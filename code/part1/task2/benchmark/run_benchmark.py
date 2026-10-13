#!/usr/bin/env python3
"""Run a bounded CMA-ES benchmark on the published K029AX model."""

from __future__ import annotations

import csv
import importlib
import json
import math
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import amici
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


TASK_ROOT = Path(__file__).resolve().parents[1]
RESULTS = TASK_ROOT / "benchmark" / "results"
MODEL_NAME = "ERBB_RAS_AKT_Drugs"
MODEL_DIR = TASK_ROOT / ".amici_model" / MODEL_NAME
REFERENCE_COMMIT = "6916101b6df55ca97f5522a999c0dc499d6e4362"
TREATMENT_COMMIT = "62b25f5d4956e91c509d561c999c4cceb98a1081"
REFERENCE_ROOT = (
    TASK_ROOT / ".cache" / "upstream" / f"reference_simulator-{REFERENCE_COMMIT}"
)

CELL_LINE = "K029AX"
DRUGS = [
    "CHIR-265",
    "Erlotinib",
    "Lapatinib",
    "PD0325901",
    "PLX-4720",
    "Selumetinib",
    "Vandetanib",
]
MAX_DOSAGE = 8000.0
LAMBDA = 1e-5
SEEDS = (23, 47, 89)
MAX_ITER = 60


@dataclass
class Evaluation:
    objective: float
    proliferation: float
    elapsed_seconds: float


class PanCancerEvaluator:
    def __init__(self) -> None:
        sys.path.insert(0, str(MODEL_DIR))
        module = importlib.import_module(MODEL_NAME)
        self.model = module.get_model()
        self.model.set_timepoints([np.inf])
        self.solver = self.model.create_solver()
        self.solver.set_relative_tolerance(1e-8)
        self.solver.set_absolute_tolerance(1e-8)

        conditions = pd.read_csv(REFERENCE_ROOT / "conditions_petab.tsv", sep="\t")
        row = conditions.loc[
            conditions.conditionId == f"TUMOR-{CELL_LINE}-cellline-01-01", :
        ]
        if len(row) != 1:
            raise RuntimeError(f"Expected one condition row for {CELL_LINE}, got {len(row)}")
        fixed_ids = set(self.model.get_fixed_parameter_ids())
        for column in row.columns:
            if column in fixed_ids:
                self.model.set_fixed_parameter_by_id(column, float(row[column].iloc[0]))

        self.calls = 0
        self.simulation_seconds = 0.0
        zero = self._simulate(np.zeros(len(DRUGS)))
        self.zero_term = zero

    def _simulate(self, normalized: np.ndarray) -> float:
        concentrations = np.asarray(normalized, dtype=float) * MAX_DOSAGE
        for drug, concentration in zip(DRUGS, concentrations, strict=True):
            self.model.set_fixed_parameter_by_name(drug, float(concentration))
        started = time.perf_counter()
        result = self.model.simulate(solver=self.solver)
        elapsed = time.perf_counter() - started
        self.calls += 1
        self.simulation_seconds += elapsed
        if result.status != 0:
            raise RuntimeError(f"AMICI failed with status {result.status}")
        return float(result.y[0, 0])

    def evaluate(self, normalized: np.ndarray) -> Evaluation:
        started = time.perf_counter()
        proliferation = self._simulate(normalized) / self.zero_term
        objective = proliferation + LAMBDA * MAX_DOSAGE * float(np.sum(normalized))
        return Evaluation(objective, proliferation, time.perf_counter() - started)


def sample_simplex_normal(
    rng: np.random.Generator, mean: np.ndarray, covariance: np.ndarray
) -> tuple[np.ndarray, int]:
    attempts = 0
    while True:
        attempts += 1
        sample = rng.multivariate_normal(mean, covariance)
        if np.all(sample >= 0.0) and float(np.sum(sample)) <= 1.0:
            return sample, attempts


def cma_es(evaluator: PanCancerEvaluator, seed: int) -> tuple[dict, list[dict]]:
    rng = np.random.default_rng(seed)
    dimension = len(DRUGS)
    sigma = 0.25
    population = int(4 + math.floor(3 * math.log(dimension)))
    elite_count = population // 2
    mean = np.ones(dimension) / dimension
    weights = np.array(
        [math.log((population + 1) / 2) - math.log(i) for i in range(1, elite_count + 1)]
    )
    weights /= weights.sum()
    mu_eff = 1.0 / float(weights @ weights)
    c_sigma = (mu_eff + 2) / (dimension + mu_eff + 5)
    d_sigma = 1 + 2 * max(0, math.sqrt((mu_eff - 1) / (dimension + 1)) - 1) + c_sigma
    c_s = (4 + mu_eff / dimension) / (dimension + 4 + 2 * mu_eff / dimension)
    c_1 = 2 / ((dimension + 1.3) ** 2 + mu_eff)
    c_mu = min(
        1 - c_1,
        2 * (mu_eff - 2 + 1 / mu_eff) / ((dimension + 2) ** 2 + mu_eff),
    )
    expected_norm = math.sqrt(dimension) * (
        1 - 1 / (4 * dimension) + 1 / (21 * dimension**2)
    )
    p_sigma = np.zeros(dimension)
    p_s = np.zeros(dimension)
    covariance = np.eye(dimension)
    best: dict | None = None
    trace: list[dict] = []

    for iteration in range(1, MAX_ITER + 1):
        candidates = []
        rejection_attempts = 0
        for _ in range(population):
            candidate, attempts = sample_simplex_normal(
                rng, mean, sigma * sigma * covariance
            )
            candidates.append(candidate)
            rejection_attempts += attempts

        evaluations = [evaluator.evaluate(candidate) for candidate in candidates]
        objectives = np.array([evaluation.objective for evaluation in evaluations])
        order = np.argsort(objectives)
        for index in order:
            evaluation = evaluations[index]
            if best is None or evaluation.objective < best["objective"]:
                best = {
                    "seed": seed,
                    "iteration": iteration,
                    "objective": evaluation.objective,
                    "relative_proliferation": evaluation.proliferation,
                    "normalized": candidates[index].copy(),
                }

        steps = [(candidate - mean) / sigma for candidate in candidates]
        weighted_step = sum(weights[i] * steps[order[i]] for i in range(elite_count))
        mean = mean + sigma * weighted_step

        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        eigenvalues = np.maximum(eigenvalues, np.finfo(float).eps)
        inverse_sqrt = eigenvectors @ np.diag(1 / np.sqrt(eigenvalues)) @ eigenvectors.T
        p_sigma = (1 - c_sigma) * p_sigma + math.sqrt(
            c_sigma * (2 - c_sigma) * mu_eff
        ) * (inverse_sqrt @ weighted_step)
        sigma *= math.exp(c_sigma / d_sigma * (np.linalg.norm(p_sigma) / expected_norm - 1))

        h_sigma = int(
            np.linalg.norm(p_sigma)
            / math.sqrt(1 - (1 - c_sigma) ** (2 * iteration))
            < (1.4 + 2 / (dimension + 1)) * expected_norm
        )
        p_s = (1 - c_s) * p_s + h_sigma * math.sqrt(
            c_s * (2 - c_s) * mu_eff
        ) * weighted_step
        covariance = (
            (1 - c_1 - c_mu) * covariance
            + c_1
            * (
                np.outer(p_s, p_s)
                + (1 - h_sigma) * c_s * (2 - c_s) * covariance
            )
            + c_mu
            * sum(
                weights[i] * np.outer(steps[order[i]], steps[order[i]])
                for i in range(elite_count)
            )
        )
        covariance = (covariance + covariance.T) / 2

        assert best is not None
        trace.append(
            {
                "seed": seed,
                "iteration": iteration,
                "evaluations": iteration * population,
                "best_objective": best["objective"],
                "best_relative_proliferation": best["relative_proliferation"],
                "best_total_dosage_nm": MAX_DOSAGE * float(np.sum(best["normalized"])),
                "mean_population_objective": float(np.mean(objectives)),
                "sigma": sigma,
                "sampling_draws": rejection_attempts,
            }
        )

    assert best is not None
    best["concentrations_nm"] = {
        drug: MAX_DOSAGE * float(value)
        for drug, value in zip(DRUGS, best.pop("normalized"), strict=True)
    }
    best["total_dosage_nm"] = sum(best["concentrations_nm"].values())
    return best, trace


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if not MODEL_DIR.exists():
        raise SystemExit("Compiled model is missing. Run benchmark/build_model.py first.")
    RESULTS.mkdir(parents=True, exist_ok=True)
    benchmark_started = time.perf_counter()
    evaluator = PanCancerEvaluator()

    equal = np.ones(len(DRUGS)) / len(DRUGS)
    equal_evaluation = evaluator.evaluate(equal)
    all_best = []
    all_trace = []
    for seed in SEEDS:
        best, trace = cma_es(evaluator, seed)
        all_best.append(best)
        all_trace.extend(trace)
        print(
            f"seed={seed} objective={best['objective']:.8f} "
            f"proliferation={best['relative_proliferation']:.8f} "
            f"dose={best['total_dosage_nm']:.2f}"
        )

    winner = min(all_best, key=lambda item: item["objective"])
    trace_rows = all_trace
    write_csv(RESULTS / "convergence.csv", trace_rows)

    summary_rows = []
    for result in all_best:
        row = {
            "seed": result["seed"],
            "iteration": result["iteration"],
            "objective": result["objective"],
            "relative_proliferation": result["relative_proliferation"],
            "total_dosage_nm": result["total_dosage_nm"],
        }
        row.update(result["concentrations_nm"])
        summary_rows.append(row)
    write_csv(RESULTS / "seed_summary.csv", summary_rows)

    trace_frame = pd.DataFrame(trace_rows)
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    for seed, frame in trace_frame.groupby("seed"):
        axis.plot(frame["evaluations"], frame["best_objective"], label=f"Seed {seed}")
    axis.axhline(
        equal_evaluation.objective,
        color="black",
        linestyle="--",
        linewidth=1,
        label="Startpunkt (gleich verteilt)",
    )
    axis.set_xlabel("Modellsimulationen pro Lauf")
    axis.set_ylabel(r"Beste Zielfunktion $V + 10^{-5}\|\tau\|_1$")
    axis.set_title("CMA-ES auf dem K029AX-Pan-Cancer-Modell")
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(RESULTS / "convergence.svg")
    figure.savefig(RESULTS / "convergence.png", dpi=180)
    plt.close(figure)

    report = {
        "benchmark": "small faithful treatment-optimization reproduction",
        "cell_line": CELL_LINE,
        "reference_simulator_commit": REFERENCE_COMMIT,
        "treatment_optimizer_commit": TREATMENT_COMMIT,
        "amici": amici.__version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "model_states": len(evaluator.model.get_state_ids()),
        "model_free_parameters": len(evaluator.model.get_free_parameter_ids()),
        "max_dosage_nm": MAX_DOSAGE,
        "lambda_l1": LAMBDA,
        "iterations_per_seed": MAX_ITER,
        "seeds": list(SEEDS),
        "population_per_iteration": int(4 + math.floor(3 * math.log(len(DRUGS)))),
        "untreated_proliferation_output": evaluator.zero_term,
        "equal_split": {
            "objective": equal_evaluation.objective,
            "relative_proliferation": equal_evaluation.proliferation,
            "total_dosage_nm": MAX_DOSAGE,
        },
        "winner": winner,
        "total_model_calls_including_controls": evaluator.calls,
        "model_simulation_seconds": evaluator.simulation_seconds,
        "benchmark_wall_seconds": time.perf_counter() - benchmark_started,
        "median_simulation_seconds": evaluator.simulation_seconds / evaluator.calls,
        "prediction_metric": None,
        "prediction_metric_reason": "No independent observed viability values are part of this bounded optimization benchmark.",
    }
    (RESULTS / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()


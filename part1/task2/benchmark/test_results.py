#!/usr/bin/env python3
"""Check source identity and numerical invariants of the saved benchmark."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
RESULTS = TASK_ROOT / "benchmark" / "results"
REFERENCE_COMMIT = "6916101b6df55ca97f5522a999c0dc499d6e4362"
REFERENCE_ROOT = (
    TASK_ROOT / ".cache" / "upstream" / f"reference_simulator-{REFERENCE_COMMIT}"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def main() -> None:
    report = json.loads((RESULTS / "benchmark.json").read_text())
    build = json.loads((RESULTS / "build_metadata.json").read_text())
    with (RESULTS / "convergence.csv").open() as handle:
        convergence = list(csv.DictReader(handle))
    with (RESULTS / "seed_summary.csv").open() as handle:
        summaries = list(csv.DictReader(handle))

    assert build["sbml_sha256"] == sha256(
        REFERENCE_ROOT / "CS_Signalling_ERBB_RAS_AKT_modified.xml"
    )
    assert build["conditions_sha256"] == sha256(REFERENCE_ROOT / "conditions_petab.tsv")
    assert build["compiled_states"] == 1228
    assert build["sbml_reactions"] == 2686
    assert len(convergence) == 3 * 60
    assert len(summaries) == 3
    assert report["total_model_calls_including_controls"] == 3 * 60 * 9 + 2

    for seed in (23, 47, 89):
        rows = [row for row in convergence if int(row["seed"]) == seed]
        objectives = [float(row["best_objective"]) for row in rows]
        assert len(rows) == 60
        assert all(right <= left + 1e-14 for left, right in zip(objectives, objectives[1:]))

    winner = report["winner"]
    total_dose = sum(winner["concentrations_nm"].values())
    expected_objective = winner["relative_proliferation"] + report["lambda_l1"] * total_dose
    assert total_dose <= report["max_dosage_nm"] + 1e-9
    assert math.isclose(total_dose, winner["total_dosage_nm"], rel_tol=0, abs_tol=1e-9)
    assert math.isclose(expected_objective, winner["objective"], rel_tol=0, abs_tol=1e-12)
    assert winner["objective"] < report["equal_split"]["objective"]
    print("PASS: source hashes, dimensions, call count, convergence and objective invariants")


if __name__ == "__main__":
    main()


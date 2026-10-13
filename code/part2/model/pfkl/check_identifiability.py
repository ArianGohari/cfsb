"""Synthetic recovery for the existing PFKL regulatory equations.

No biological data are fitted. beta maps an arbitrary known observation clock
to tau; it does not calibrate this project's time axis in hours.
"""

import csv
import hashlib
import itertools
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.integrate import solve_ivp
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "output/part2/pfkl_identifiability"
OLD = ROOT / "output/part2/pfkl_regulation"
TRUTH = np.array([0.5, 1.0, 1.0])  # q, gamma, beta
TIMES = np.array([0.0, 0.25, 0.5, 1.0, 1.25, 2.0, 4.0, 8.0])
SIGMA = 0.02
LOW, HIGH = np.log([0.05, 0.05, 0.05]), np.log([1.0, 20.0, 20.0])
STARTS = list(itertools.product([0.2, 0.8], [0.25, 4.0], [0.4, 2.5]))
DESIGNS = {
    "sparse_protein": ("decay", np.array([0.0, 1.0, 4.0]), [1]),
    "dense_protein": ("decay", TIMES, [1]),
    "dense_joint": ("decay", TIMES, [0, 1]),
    "translation_joint": ("translation", TIMES, [0, 1]),
}


def phase(t, state, gamma, d, k):
    t = np.asarray(t)
    lam = gamma * d
    gap = abs(lam - 1.0)
    coupling = (
        t * np.exp(-t)
        if gap < 1e-12
        else np.exp(-min(lam, 1.0) * t) * (-np.expm1(-gap * t)) / gap
    )
    m0, e0 = state
    ms = 1 / d
    return np.column_stack(
        (
            ms + (m0 - ms) * np.exp(-lam * t),
            k * ms + (e0 - k * ms) * np.exp(-t) + k * (m0 - ms) * coupling,
        )
    )


def trajectory(theta, mechanism, times, duration=1.0):
    q, gamma, beta = theta
    d, k = (1 / q, 1.0) if mechanism == "decay" else (1.0, q)
    times = np.asarray(times)
    switch = phase(np.array([beta * duration]), [1.0, 1.0], gamma, d, k)[0]
    values = np.empty((len(times), 2))
    on = times <= duration
    values[on] = phase(beta * times[on], [1.0, 1.0], gamma, d, k)
    values[~on] = phase(beta * (times[~on] - duration), switch, gamma, 1.0, 1.0)
    return values


def predict(theta, design):
    mechanism, times, columns = DESIGNS[design]
    return trajectory(theta, mechanism, times)[:, columns].ravel()


def fit(design, observed, start, fixed_gamma=None):
    free = [0, 1, 2] if fixed_gamma is None else [0, 2]

    def unpack(x):
        p = np.array(start, dtype=float)
        p[free] = np.exp(x)
        if fixed_gamma is not None:
            p[1] = fixed_gamma
        return p

    result = least_squares(
        lambda x: (predict(unpack(x), design) - observed) / SIGMA,
        np.log(np.asarray(start)[free]),
        bounds=(LOW[free], HIGH[free]),
        ftol=1e-11,
        xtol=1e-11,
        gtol=1e-11,
        max_nfev=1500,
    )
    return unpack(result.x), float(np.dot(result.fun, result.fun)), result


def dump(path, value):
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )


def save_rows(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_solver():
    errors = []
    # Includes equal rates during the pulse, after it, and near coincidence.
    for theta in [
        [0.5, 1.0, 1.0],
        [0.5, 0.5, 1.7],
        [0.5, 0.500000000001, 0.4],
        [0.25, 4.0, 2.0],
    ]:
        for mechanism in ["decay", "translation"]:
            q, g, b = theta
            d, k = (1 / q, 1.0) if mechanism == "decay" else (1.0, q)
            rhs = lambda t, u: [b * g * (1 - d * u[0]), b * (k * u[0] - u[1])]
            on = solve_ivp(
                rhs, (0, 1), [1.0, 1.0], rtol=1e-11, atol=1e-13, dense_output=True
            )
            off = solve_ivp(
                lambda t, u: [b * g * (1 - u[0]), b * (u[0] - u[1])],
                (1, 8),
                on.y[:, -1],
                rtol=1e-11,
                atol=1e-13,
                dense_output=True,
            )
            assert on.success and off.success
            numerical = np.array([on.sol(t) if t <= 1 else off.sol(t) for t in TIMES])
            errors.append(
                float(np.max(abs(numerical - trajectory(theta, mechanism, TIMES))))
            )
    assert max(errors) < 1e-8
    old_manifest = json.loads((OLD / "manifest.json").read_text())
    assert (
        sha(OLD / "trajectories.tsv")
        == old_manifest["outputs"][str((OLD / "trajectories.tsv").relative_to(ROOT))]
    )
    saved = list(csv.DictReader((OLD / "trajectories.tsv").open(), delimiter="\t"))
    catalyst_errors = []
    for mechanism in ["decay", "translation"]:
        rows = [
            r
            for r in saved
            if r["mechanism"] == mechanism
            and all(
                float(r[k]) == v
                for k, v in [("q", 0.5), ("gamma", 1.0), ("duration", 1.0)]
            )
        ]
        assert len(rows) > 200
        times = np.array([float(r["tau"]) for r in rows])
        values = np.array([[float(r["mRNA"]), float(r["protein"])] for r in rows])
        catalyst_errors.append(
            float(np.max(abs(values - trajectory(TRUTH, mechanism, times))))
        )
    assert max(catalyst_errors) < 1e-8
    # gamma is absent from the translation-only response starting at M=1.
    assert (
        np.max(
            abs(
                trajectory([0.5, 0.05, 1.0], "translation", TIMES)
                - trajectory([0.5, 20.0, 1.0], "translation", TIMES)
            )
        )
        < 1e-14
    )
    return dict(
        max_direct_ode_error=max(errors), max_saved_catalyst_error=max(catalyst_errors)
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    verification = verify_solver()
    rng = np.random.default_rng(6517)
    noise = {
        mechanism: rng.normal(0, SIGMA, (len(TIMES), 2))
        for mechanism in ["decay", "translation"]
    }
    records, observations, profiles, summaries = [], [], [], []
    for design, (mechanism, times, columns) in DESIGNS.items():
        clean = predict(TRUTH, design)
        indices = [int(np.flatnonzero(TIMES == t)[0]) for t in times]
        noisy = clean + noise[mechanism][indices][:, columns].ravel()
        h = 1e-5
        jacobian = np.column_stack(
            [
                (
                    predict(TRUTH * np.exp(np.eye(3)[i] * h), design)
                    - predict(TRUTH * np.exp(-np.eye(3)[i] * h), design)
                )
                / (2 * h * SIGMA)
                for i in range(3)
            ]
        )
        singular = np.linalg.svd(jacobian, compute_uv=False)
        rank = int(np.count_nonzero(singular > singular[0] * 1e-7))
        for label, observed in [("noiseless", clean), ("noise_example", noisy)]:
            for j, (t, col) in enumerate(itertools.product(times, columns)):
                observations.append(
                    dict(
                        design=design,
                        dataset=label,
                        time=t,
                        variable=["M", "E"][col],
                        value=observed[j],
                        truth=clean[j],
                        sigma=SIGMA,
                    )
                )
            fits = []
            for i, start in enumerate(STARTS):
                params, cost, result = fit(design, observed, start)
                row = dict(
                    design=design,
                    dataset=label,
                    start_id=i,
                    start_q=start[0],
                    start_gamma=start[1],
                    start_beta=start[2],
                    q=params[0],
                    gamma=params[1],
                    beta=params[2],
                    weighted_sse=cost,
                    success=bool(result.success),
                    status=int(result.status),
                    nfev=int(result.nfev),
                    max_relative_parameter_error=float(np.max(abs(params / TRUTH - 1))),
                )
                records.append(row)
                fits.append(row)
            best = min(fits, key=lambda r: r["weighted_sse"])
            assert best["success"]
            if label == "noiseless":
                assert best["weighted_sse"] < 1e-12
                if rank == 3:
                    assert all(
                        r["success"] and r["max_relative_parameter_error"] < 1e-4
                        for r in fits
                    )
            summaries.append(
                dict(
                    design=design,
                    dataset=label,
                    local_rank=rank,
                    singular_values=singular.tolist(),
                    best=best,
                    all_starts_converged=all(r["success"] for r in fits),
                    fitted_ranges={
                        key: [min(r[key] for r in fits), max(r[key] for r in fits)]
                        for key in ["q", "gamma", "beta"]
                    },
                )
            )
        for gamma in np.geomspace(0.1, 10, 31):
            candidates = [
                fit(design, clean, start, gamma)
                for start in itertools.product([0.2, 0.8], [1.0], [0.4, 2.5])
            ]
            params, cost, result = min(candidates, key=lambda r: r[1])
            assert result.success
            profiles.append(
                dict(
                    design=design,
                    fixed_gamma=gamma,
                    q=params[0],
                    beta=params[2],
                    weighted_sse=cost,
                    success=bool(result.success),
                )
            )
        print(design, "rank", rank, flush=True)
    assert [s["local_rank"] for s in summaries[::2]] == [2, 3, 3, 2]
    summary = dict(
        truth=dict(q=0.5, gamma=1.0, beta=1.0),
        sigma=SIGMA,
        seed=6517,
        pulse_end=1.0,
        parameter_bounds=dict(q=[0.05, 1.0], gamma=[0.05, 20.0], beta=[0.05, 20.0]),
        experiments=summaries,
        scope="Synthetic local/design-specific recovery, known pure mechanism and known normalized observation scale. "
        "One noisy example; no success rate, formal confidence interval, global uniqueness proof or biological validation.",
        versions=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            matplotlib=matplotlib.__version__,
        ),
    )
    save_rows(OUT / "observations.tsv", observations)
    save_rows(OUT / "fits.tsv", records)
    save_rows(OUT / "profiles.tsv", profiles)
    dump(OUT / "summary.json", summary)
    dump(OUT / "verification.json", verification)
    plot(profiles)
    inputs = [
        Path(__file__),
        Path(__file__).with_name("identifiability_plan.md"),
        Path(__file__).with_name("regulation.jl"),
        OLD / "manifest.json",
        OLD / "trajectories.tsv",
        ROOT / "code/part2/reproduction/uv.lock",
    ]
    names = [
        "observations.tsv",
        "fits.tsv",
        "profiles.tsv",
        "summary.json",
        "verification.json",
        "identifiability.svg",
        "identifiability.png",
    ]
    dump(
        OUT / "manifest.json",
        dict(
            inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
            outputs={str((OUT / n).relative_to(ROOT)): sha(OUT / n) for n in names},
        ),
    )


def plot(profiles):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.hashsalt": "pfkl-identifiability",
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), layout="constrained")
    t = np.linspace(0, 8, 401)
    trajectory_values = trajectory(TRUTH, "decay", t)
    for col, color, label in [(0, "#00883a", "mRNA M"), (1, "#4e5da8", "Protein E")]:
        axes[0].plot(t, trajectory_values[:, col], color=color, label=label)
        axes[0].scatter(
            TIMES, trajectory(TRUTH, "decay", TIMES)[:, col], color=color, s=18
        )
    axes[0].axvspan(0, 1, color="#d5dcd7", alpha=0.4)
    axes[0].set(
        xlabel="Synthetische Versuchsuhr s (keine Stunden)",
        ylabel="Normierte Menge",
        title="A  Bekannter Eingriff und Messzeiten",
        ylim=(0.48, 1.05),
    )
    axes[0].legend(frameon=False, loc="lower right")
    styles = [
        ("sparse_protein", "#b87816", "--", "Abbau: 3 Proteinzeitpunkte"),
        ("dense_protein", "#4e5da8", "-", "Abbau: 8 Proteinzeitpunkte"),
        ("dense_joint", "#00883a", "-", "Abbau: 8 RNA-/Proteinzeitpunkte"),
        ("translation_joint", "#555555", ":", "Translation: RNA + Protein"),
    ]
    for design, color, style, label in styles:
        rows = [r for r in profiles if r["design"] == design]
        axes[1].plot(
            [r["fixed_gamma"] for r in rows],
            [r["weighted_sse"] for r in rows],
            color=color,
            linestyle=style,
            label=label,
        )
    axes[1].axvline(1, color="#777777", lw=0.7, alpha=0.6)
    axes[1].set(
        xscale="log",
        yscale="symlog",
        xlabel="Festgehaltenes Abbauratenverhältnis γ",
        ylabel="Gewichtete Residuenquadratsumme",
        title="B  γ-Profil ohne Messrauschen",
    )
    axes[1].set_yscale("symlog", linthresh=0.01)
    axes[1].set_ylim(-0.003, max(r["weighted_sse"] for r in profiles) * 1.3)
    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(
        handles, labels, frameon=False, fontsize=9, ncols=2, loc="outside lower center"
    )
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.13)
    fig.savefig(OUT / "identifiability.svg", metadata={"Date": None})
    fig.savefig(
        OUT / "identifiability.png",
        dpi=180,
        metadata={"Software": "CFSB synthetic identifiability"},
    )
    plt.close(fig)


if __name__ == "__main__":
    main()

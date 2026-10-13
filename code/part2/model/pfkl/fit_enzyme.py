"""Fit WT PFKL substrate response and leave whole concentrations out.

uv run --offline --locked --project code/part2/reproduction python code/part2/model/pfkl/fit_enzyme.py
"""

from pathlib import Path
import csv
import hashlib
import json
import platform
import numpy as np
import scipy
from scipy.optimize import least_squares
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
INPUT = ROOT / "output/part2/milk_inventory/pfkl_kinetics"
OUT = ROOT / "output/part2/pfkl_enzyme"
PLAN = Path(__file__).with_name("plan.md")
BOUNDS = ([0, 0.001, 0.001, 0.1], [20, 1000, 100, 10])


def rate(s, v, k, h):
    """Hill rate: substrate s and half-saturation k in mM, maximum v in U/mg."""
    s = np.asarray(s, dtype=float)
    return v * s**h / (k**h + s**h)


def predict(s, p):
    """Measured signal includes a fitted assay background: p = [background, V, K, h]."""
    return p[0] + rate(s, *p[1:])


def fit(x, y, model="hill", zero_background=False, bounds=BOUNDS):
    """Fit all assay values; keep the best least-squares result across starting points."""
    free = [
        i
        for i in range(4)
        if not (i == 3 and model == "michaelis") and not (i == 0 and zero_background)
    ]

    def expand(q):
        p = np.array([0.0, 10.0, 2.0, 1.0])
        p[free] = q
        return p

    fits = []
    for k in [1.0, 2.0, 4.0]:
        for h in [1.0] if model == "michaelis" else [1.0, 3.0]:
            start = np.array([0.2, 10.0, k, h])[free]
            result = least_squares(
                lambda q: predict(x, expand(q)) - y,
                start,
                bounds=(np.array(bounds[0])[free], np.array(bounds[1])[free]),
                xtol=1e-12,
                ftol=1e-12,
                gtol=1e-12,
                max_nfev=10000,
                x_scale="jac",
            )
            if not result.success:
                raise RuntimeError(result.message)
            fits.append((float(np.sum(result.fun**2)), expand(result.x)))
    fits.sort(key=lambda z: z[0])
    sse, p = fits[0]
    boundary = [
        name
        for i, name in enumerate(["background", "V", "K", "h"])
        if i in free
        and min(abs(p[i] - bounds[0][i]), abs(p[i] - bounds[1][i]))
        < 1e-5 * max(1, abs(p[i]))
    ]
    return p, dict(
        sse=sse,
        max_start_sse=max(z[0] for z in fits),
        min_start_sse=sse,
        boundary=boundary,
    )


def write_table(name, rows):
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def params(p):
    return dict(
        background_U_per_mg=float(p[0]),
        V_U_per_mg=float(p[1]),
        K_mM=float(p[2]),
        hill=float(p[3]),
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((INPUT / "extraction.json").read_text())
    assert (
        hashlib.sha256((ROOT / provenance["source"]).read_bytes()).hexdigest()
        == provenance["sha256"]
    )
    rows = [
        r
        for r in csv.DictReader((INPUT / "wild_type_assays.tsv").open(), delimiter="\t")
        if r["varied_substrate"] == "F6P"
    ]
    assert len(rows) == 56 and PLAN.exists()
    x = np.array([float(r["concentration_mM"]) for r in rows])
    y = np.array([float(r["activity_U_per_mg"]) for r in rows])
    cols = np.array([r["series_column"] for r in rows])
    levels = np.unique(x)
    assert len(levels) == 9 and np.sum(x == 0.25) == 1
    means = np.array([y[x == s].mean() for s in levels])
    sd = np.array(
        [y[x == s].std(ddof=1) if np.sum(x == s) > 1 else np.nan for s in levels]
    )
    write_table(
        "concentration_summary.tsv",
        [
            dict(F6P_mM=s, n=int(np.sum(x == s)), mean_U_per_mg=m, sd_U_per_mg=d)
            for s, m, d in zip(levels, means, sd)
        ],
    )
    full = {}
    cv = []
    metrics = []
    for model in ["hill", "michaelis", "constant"]:
        if model != "constant":
            p, diagnostics = fit(x, y, model)
            full[model] = dict(**params(p), **diagnostics)
        for s in levels:
            train = x != s
            test = ~train
            if model == "constant":
                pred = float(y[train].mean())
                parameter = {}
                diagnostic = {}
            else:
                p, diagnostic = fit(x[train], y[train], model)
                pred = float(predict(s, p))
                parameter = params(p)
            assert not np.any(x[train] == s)
            for idx in np.where(test)[0]:
                cv.append(
                    dict(
                        model=model,
                        held_out_mM=float(s),
                        region="boundary"
                        if s in [levels[0], levels[-1]]
                        else "interior",
                        value_cell=rows[idx]["value_cell"],
                        series_column=cols[idx],
                        observed=float(y[idx]),
                        predicted=pred,
                        residual=pred - float(y[idx]),
                        **{k: parameter.get(k, "") for k in params([0, 0, 0, 0])},
                        boundary_parameters=",".join(diagnostic.get("boundary", [])),
                    )
                )
        for region in ["all", "interior", "boundary"]:
            sub = [
                r
                for r in cv
                if r["model"] == model and (region == "all" or r["region"] == region)
            ]
            errors = np.array([r["residual"] for r in sub])
            group_errors = [
                np.mean([r["residual"] for r in sub if r["held_out_mM"] == s])
                for s in sorted(set(r["held_out_mM"] for r in sub))
            ]
            metrics.append(
                dict(
                    model=model,
                    region=region,
                    observations=len(sub),
                    levels=len(group_errors),
                    rmse_individual=float(np.sqrt(np.mean(errors**2))),
                    mae_individual=float(np.mean(abs(errors))),
                    rmse_means=float(np.sqrt(np.mean(np.array(group_errors) ** 2))),
                )
            )
    write_table("held_out_predictions.tsv", cv)
    write_table("prediction_metrics.tsv", metrics)
    sensitivity = []
    for col in sorted(set(cols)):
        p, d = fit(x[cols != col], y[cols != col])
        sensitivity.append(
            dict(
                omitted_column=col,
                **params(p),
                sse=d["sse"],
                boundary=",".join(d["boundary"]),
            )
        )
    write_table("column_sensitivity.tsv", sensitivity)
    # Added after observing the Michaelis K upper-bound hit; no change to primary fits.
    wide = (BOUNDS[0], [20, 10000, 1000, 10])
    pw, dw = fit(x, y, "michaelis", bounds=wide)
    wide_rows = []
    for concentration in levels:
        train = x != concentration
        pp, dd = fit(x[train], y[train], "michaelis", bounds=wide)
        wide_rows.append(
            dict(
                F6P_mM=float(concentration),
                observed_mean=float(y[~train].mean()),
                predicted=float(predict(concentration, pp)),
                **params(pp),
                boundary=",".join(dd["boundary"]),
            )
        )
    write_table("michaelis_bound_sensitivity.tsv", wide_rows)
    wide_rmse = float(
        np.sqrt(
            np.mean([(r["predicted"] - r["observed_mean"]) ** 2 for r in wide_rows])
        )
    )
    p0, d0 = fit(x, y, zero_background=True)
    p = np.array([full["hill"][k] for k in params([0, 0, 0, 0])])
    grid = np.linspace(0, 4, 401)
    physical = rate(grid, *p[1:])
    assert (
        physical[0] == 0
        and np.all(physical >= 0)
        and np.all(np.diff(physical) >= 0)
        and np.all(physical <= p[1])
    )
    assert np.isclose(rate(p[2], *p[1:]), p[1] / 2)
    write_table(
        "curves.tsv",
        [
            dict(F6P_mM=s, enzyme_rate_U_per_mg=v, observed_signal_U_per_mg=v + p[0])
            for s, v in zip(grid, physical)
        ],
    )
    write_table(
        "full_fit_residuals.tsv",
        [
            dict(
                value_cell=r["value_cell"],
                series_column=r["series_column"],
                F6P_mM=float(s),
                observed=float(o),
                predicted=float(pred),
                residual=float(pred - o),
            )
            for r, s, o, pred in zip(rows, x, y, predict(x, p))
        ],
    )
    result = dict(
        source_doi=provenance["doi"],
        conditions=dict(ATP_mM=0.125, pH=7.5, temperature_C=25),
        full_fit=full,
        michaelis_wider_bounds=dict(**params(pw), **dw, cv_rmse_means=wide_rmse),
        zero_background_sensitivity=dict(**params(p0), **d0),
        column_sensitivity_ranges={
            k: [min(r[k] for r in sensitivity), max(r[k] for r in sensitivity)]
            for k in params(p)
        },
        checks=dict(
            nonnegative=True,
            zero_substrate_zero_rate=True,
            monotone=True,
            half_maximum=True,
        ),
        interpretation="Internal concentration prediction only. No independent preparation-level validation, human miRNA efficacy, cell enzyme concentration or cellular dynamics.",
        versions=dict(
            python=platform.python_version(),
            numpy=np.__version__,
            scipy=scipy.__version__,
            matplotlib=matplotlib.__version__,
        ),
    )
    (OUT / "fit.json").write_text(json.dumps(result, indent=2) + "\n")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "pfkl_enzyme",
        }
    )
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.2))
    ax[0].scatter(x, y, s=17, color="#83938a", alpha=0.6, label="Einzelmessungen")
    ax[0].plot(
        grid, predict(grid, p), color="#00883a", lw=2, label="Hill-Modell + Hintergrund"
    )
    pm = np.array([full["michaelis"][k] for k in params(p)])
    ax[0].plot(
        grid,
        predict(grid, pm),
        color="#a86b20",
        ls="--",
        label="Michaelis-Menten + Hintergrund",
    )
    ax[0].scatter(
        levels, means, s=35, color="#273e30", marker="s", label="Mittelwerte", zorder=4
    )
    ax[0].set_title("A   Anpassung an alle F6P-Werte", loc="left", fontweight="bold")
    ax[1].scatter(
        levels,
        means,
        s=35,
        color="#273e30",
        marker="s",
        label="Gemessener Mittelwert",
        zorder=4,
    )
    for model, color, marker in [
        ("hill", "#00883a", "o"),
        ("michaelis", "#a86b20", "^"),
    ]:
        pred = [
            next(
                r["predicted"]
                for r in cv
                if r["model"] == model and r["held_out_mM"] == s
            )
            for s in levels
        ]
        ax[1].plot(
            levels,
            pred,
            marker=marker,
            color=color,
            lw=1.3,
            label="Vorhersage: " + ("Hill" if model == "hill" else "Michaelis-Menten"),
        )
    ax[1].set_title(
        "B   Je eine Konzentration ausgelassen", loc="left", fontweight="bold"
    )
    for a in ax:
        a.set(
            xlabel="F6P (mM)",
            ylabel="Spezifische Aktivität (U/mg)",
            xlim=(-0.12, 4.15),
            ylim=(-0.2, 12),
        )
        a.spines[["top", "right"]].set_visible(False)
        a.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.text(
        0.07,
        0.025,
        "Lynch 2024 · humanes PFKL · ATP 0,125 mM · Vorhersageprüfung innerhalb derselben Studie",
        fontsize=9,
        color="#626c66",
    )
    for ext in ["svg", "png"]:
        fig.savefig(
            OUT / f"enzyme_fit.{ext}",
            dpi=180,
            metadata={"Date": None} if ext == "svg" else None,
        )
    plt.close(fig)
    inputs = [
        INPUT / "wild_type_assays.tsv",
        INPUT / "extraction.json",
        ROOT / provenance["source"],
        PLAN,
        Path(__file__).resolve(),
    ]
    outputs = sorted(p for p in OUT.iterdir() if p.name != "manifest.json")
    hashes = lambda ps: {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in ps
    }
    (OUT / "manifest.json").write_text(
        json.dumps(dict(inputs=hashes(inputs), outputs=hashes(outputs)), indent=2)
        + "\n"
    )
    print(json.dumps(result, indent=2))
    print(metrics)


if __name__ == "__main__":
    main()

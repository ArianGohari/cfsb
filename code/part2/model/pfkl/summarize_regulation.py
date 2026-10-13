"""Plot the assumed PFKL regulation scenarios; no cell parameters are fitted."""

from pathlib import Path
import csv, json, math, hashlib, subprocess
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "output/part2/pfkl_regulation"


def phase(t, m0, e0, gamma, d, k):
    rate = gamma * d
    ms = 1 / d
    coupling = (
        t * math.exp(-t)
        if abs(rate - 1) < 1e-13
        else (math.exp(-rate * t) - math.exp(-t)) / (1 - rate)
    )
    return ms + (m0 - ms) * math.exp(-rate * t), k * ms + (e0 - k * ms) * math.exp(
        -t
    ) + k * (m0 - ms) * coupling


def main():
    rows = list(csv.DictReader((OUT / "trajectories.tsv").open(), delimiter="\t"))
    ends = list(csv.DictReader((OUT / "endpoints.tsv").open(), delimiter="\t"))
    peaks = []
    for row in ends:
        q, g, L = (float(row[k]) for k in ("q", "gamma", "duration"))
        mech = row["mechanism"]
        m, e = float(row["mRNA_end"]), float(row["protein_end"])
        if q == 1:
            lag = 0.0
            minimum = 1.0
        elif mech == "translation":
            lag = 0.0
            minimum = e
        else:
            lo, hi = 0.0, 20 / min(g, 1.0)
            for _ in range(70):
                t = (lo + hi) / 2
                mt, et = phase(t, m, e, g, 1.0, 1.0)
                if mt - et < 0:
                    lo = t
                else:
                    hi = t
            lag = (lo + hi) / 2
            minimum = phase(lag, m, e, g, 1.0, 1.0)[1]
            assert minimum < e and lag > 0
        peaks.append({**row, "post_pulse_lag_tau": lag, "protein_minimum": minimum})
    with (OUT / "minima.tsv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=peaks[0].keys(), delimiter="\t")
        writer.writeheader()
        writer.writerows(peaks)
    example = [
        p
        for p in peaks
        if all(
            float(p[k]) == v for k, v in [("q", 0.5), ("gamma", 1.0), ("duration", 1.0)]
        )
    ]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.hashsalt": "pfkl_regulation",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.9))
    colors = {"decay": "#007b55", "translation": "#8054a3"}
    labels = {"decay": "mRNA-Abbau", "translation": "Translationshemmung"}
    for mech in colors:
        series = [
            r
            for r in rows
            if r["mechanism"] == mech
            and float(r["q"]) == 0.5
            and float(r["gamma"]) == 1
            and float(r["duration"]) == 1
            and float(r["tau"]) <= 5
        ]
        t = [float(r["tau"]) for r in series]
        for ax, col in zip(axes[:2], ["mRNA", "protein"]):
            ax.plot(
                t,
                [float(r[col]) for r in series],
                c=colors[mech],
                label=labels[mech],
                lw=2,
            )
    for ax in axes[:2]:
        ax.axvspan(0, 1, color="#d8e5df", alpha=0.65, zorder=-1)
        ax.axhline(1, c="#888888", lw=0.7, ls=":")
        ax.set(xlabel="Relative Zeit τ = δP · t", ylim=(0.45, 1.04), xlim=(0, 5))
        ax.grid(alpha=0.15)
    axes[0].set(title="A  PFKL-mRNA", ylabel="Menge relativ zur Baseline")
    axes[1].set(title="B  PFKL-Protein")
    axes[0].legend(frameon=False, loc="lower right", fontsize=8)
    for mech in colors:
        for g, style in [(1.0, "-"), (0.25, ":"), (4.0, "--")]:
            if mech == "translation" and g != 1:
                continue
            sel = sorted(
                [
                    p
                    for p in peaks
                    if p["mechanism"] == mech
                    and float(p["q"]) == 0.5
                    and float(p["gamma"]) == g
                ],
                key=lambda r: float(r["duration"]),
            )
            axes[2].plot(
                [float(p["duration"]) for p in sel],
                [float(p["protein_end"]) for p in sel],
                marker="o",
                ls=style,
                c=colors[mech],
                label=(f"Abbau, γ = {g:g}" if mech == "decay" else "Translation"),
            )
    axes[2].set(
        title="C  Protein am Eingriffsende",
        xlabel="Eingriffsdauer L (relative Zeit)",
        ylim=(0.45, 1.04),
        xscale="log",
        xticks=[0.25, 1, 4],
        xticklabels=["0,25", "1", "4"],
    )
    axes[2].minorticks_off()
    axes[2].axhline(0.5, c="#888888", lw=0.8, ls=":")
    axes[2].legend(frameon=False, fontsize=8, loc="upper right")
    axes[2].grid(alpha=0.15)
    fig.text(
        0.04,
        0.02,
        "Angenommener Dauerrestwert q = 0,5 · A/B: γ = 1, Eingriff 0–1 (Schattierung) · keine Stunden oder Milchdosen",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "regulation.svg", metadata={"Date": None})
    plt.close(fig)
    dot = """digraph regulation {
      graph [rankdir=LR, bgcolor="white", nodesep=.35, ranksep=.5];
      node [fontname="Arial", fontsize=12, color="#547763"];
      edge [fontname="Arial", fontsize=10, color="#547763", arrowsize=.7];
      M [shape=ellipse,label="PFKL-mRNA\\nM"];
      E [shape=ellipse,label="PFKL-Protein\\nE"];
      tx [shape=box,label="Transkription\\nγ"];
      dm [shape=box,label="mRNA-Abbau\\nγ · d · M"];
      tl [shape=box,label="Translation\\nk · M"];
      de [shape=box,label="Proteinabbau\\nE"];
      u [shape=plaintext,label="Angenommener miRNA-Eingriff\\n(externe Vorgabe, keine Dosis)"];
      tx->M; M->dm; M->tl [dir=both,label="bleibt erhalten"]; tl->E; E->de;
      u->dm [style=dashed,label="d erhöhen"];
      u->tl [style=dashed,label="oder k senken"];
    }"""
    (OUT / "regulation_network.dot").write_text(dot + "\n")
    subprocess.run(
        [
            "dot",
            "-Tsvg",
            str(OUT / "regulation_network.dot"),
            "-o",
            str(OUT / "regulation_network.svg"),
        ],
        check=True,
    )
    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "example_q_half_gamma_one_duration_one": example,
                "interpretation": "Conditional mechanism sensitivity. Shared steady protein rest value is imposed; no validation or calibrated miRNA dose.",
                "parameters": {
                    "q": [0.25, 0.5, 0.75, 1.0],
                    "gamma": [0.25, 1.0, 4.0],
                    "duration_tau": [0.25, 1.0, 4.0],
                    "source": "Assumed grid, not estimated ranges.",
                },
            },
            indent=2,
        )
        + "\n"
    )
    inputs = [
        ROOT / "code/part2/model/pfkl" / f
        for f in [
            "regulation_plan.md",
            "regulation.jl",
            "simulate_regulation.jl",
            "summarize_regulation.py",
        ]
    ] + [
        ROOT / "code/part2/model/Project.toml",
        ROOT / "code/part2/model/Manifest.toml",
    ]
    outputs = [
        OUT / f
        for f in [
            "trajectories.tsv",
            "endpoints.tsv",
            "checks.json",
            "minima.tsv",
            "summary.json",
            "regulation.svg",
            "regulation_network.dot",
            "regulation_network.svg",
        ]
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
                "outputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in outputs
                },
                "matplotlib": matplotlib.__version__,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(example, indent=2))


if __name__ == "__main__":
    main()

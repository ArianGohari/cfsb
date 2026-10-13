"""English, colour report figures derived from saved analysis outputs.

Original plots and presentation assets remain unchanged. Numeric coordinates
of localised SVGs are retained; two plots are redrawn from saved tables.
"""

from pathlib import Path
import csv
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/part2/typst_report/figures"
NS = "{http://www.w3.org/2000/svg}"
ET.register_namespace("", NS[1:-1])
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
LABELS = {
    "Gestrichelte Hemmkanten: humane Hypothesen, keine gemessene miRNA-Wirkung": "Dashed edges: possible human regulation, not experimentally confirmed",
    "Kuhmilch / EV-Fraktion": "Cow milk / EV fraction",
    "Bovines PFKL": "Bovine PFKL",
    "WT-/Mutantenreporter": "WT/mutant reporter",
    "boviner Befund": "bovine evidence",
    "Modellkern": "model core",
    "3-Phosphoglycerat ↔ 2-Phosphoglycerat": "3-Phosphoglycerate ↔ 2-phosphoglycerate",
    "Pyruvat → Acetyl-CoA": "Pyruvate → acetyl-CoA",
    "PDH-Komplex (vereinfacht)": "PDH complex (simplified)",
    "Teil des Komplexes": "complex component",
    "weitere Schritte": "further steps",
    "Spezifische Aktivität (U/mg)": "Specific activity (U/mg)",
    "A   Anpassung an alle F6P-Werte": "A   Fit to all F6P measurements",
    "Einzelmessungen": "Individual measurements",
    "Hill-Modell + Hintergrund": "Hill + background",
    "Michaelis-Menten + Hintergrund": "Michaelis–Menten + background",
    "Mittelwerte": "Means",
    "B   Je eine Konzentration ausgelassen": "B   Predictions at omitted concentrations",
    "Gemessener Mittelwert": "Observed mean",
    "Vorhersage: Hill": "Prediction: Hill",
    "Vorhersage: Michaelis-Menten": "Prediction: Michaelis–Menten",
    "Lynch 2024 · humanes PFKL · ATP 0,125 mM · Vorhersageprüfung innerhalb derselben Studie": "Lynch 2024; human PFKL; ATP 0.125 mM; predictions for omitted concentrations",
}
SVG_SOURCES = [
    "pfkl_enzyme/enzyme_fit.svg",
]


def literature_scope(scope_path):
    roles = json.loads(scope_path.read_text())["roles"]
    milk = roles["Inventarvergleich"]
    transfer = roles["Transferdiskussion"]
    assert (milk, transfer) == (10, 2)
    dot = f'''digraph literature {{
    graph [rankdir=TB, bgcolor="white", nodesep=.4, ranksep=.35];
    node [shape=box, style="rounded,filled", fillcolor="#eaf3f8",
          color="#0072B2", fontname="Arial", fontsize=12, margin=".16,.12"];
    edge [color="#666666", arrowsize=.65];
    sources [label="Literature searches and previously identified sources"];
    selection [label="Focused selection by material, assay and available evidence"];
    milk [label="{milk} milk-comparison studies\\nDetection and processing"];
    transfer [label="{transfer} additional studies\\nNon-detection and functional transfer",
              fillcolor="#fff2dc", color="#c48a18"];
    sequences [label="2 of the milk studies: Li and Krupova\\nSequence comparison"];
    sources -> selection;
    selection -> milk;
    selection -> transfer;
    milk -> sequences;
    {{rank=same; milk; transfer;}}
    }}'''
    subprocess.run(
        ["dot", "-Tsvg", "-o", str(OUT / "search_flow.svg")],
        input=dot,
        text=True,
        check=True,
    )


def localise(source):
    tree = ET.parse(source)
    translated = 0
    for node in tree.iter(NS + "text"):
        old = "".join(node.itertext())
        new = LABELS.get(old, old)
        if new != old:
            assert not list(node), ("Nested SVG text requires manual translation", old)
            node.text = new
            translated += 1
    # Preserve the source colours and their biological/category assignments.
    xml = ET.tostring(tree.getroot(), encoding="unicode")
    target = OUT / source.name
    target.write_text(xml + "\n")
    return translated


def sequence_plot(path):
    data = json.loads(path.read_text())["comparison"]
    keys = ["exact_human_sequence", "human_seed_only", "no_human_seed_match"]
    colors = ["#0072B2", "#56B4E9", "#E69F00"]
    labels = ["Identical human sequence", "Human seed only", "No human seed match"]
    fig, ax = plt.subplots(figsize=(8.5, 2.6))
    for y, values in [
        (1, data["classes_all_qualifying"]),
        (0, data["classes_supported_in_both"]),
    ]:
        left = 0
        for key, color in zip(keys, colors):
            n = values[key]
            ax.barh(y, n, left=left, color=color, height=0.55)
            ax.text(
                left + n / 2,
                y,
                str(n),
                va="center",
                ha="center",
                color="white" if key == keys[0] else "#222222",
                weight="bold",
            )
            left += n
        ax.text(left + 3, y, f"{left} total", va="center", fontsize=10)
    ax.set(
        yticks=[1, 0],
        yticklabels=["All sequences", "Found in both studies"],
        xlabel="Mature reference sequences",
        xlim=(0, 330),
        ylim=(-0.5, 1.5),
    )
    for side in ["top", "right", "left"]:
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.legend(
        handles=[Patch(color=c, label=l) for c, l in zip(colors, labels)],
        loc="upper center",
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.83))
    fig.savefig(OUT / "sequence_classes.svg", metadata={"Date": None})
    plt.close(fig)


def regulation_plot(trajectories, minima):
    rows = list(csv.DictReader(trajectories.open(), delimiter="\t"))
    peaks = list(csv.DictReader(minima.open(), delimiter="\t"))
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.9))
    colors = {"decay": "#0072B2", "translation": "#D55E00"}
    labels = {"decay": "Enhanced mRNA decay", "translation": "Translation inhibition"}
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
                ls="-" if mech == "decay" else "--",
            )
    for ax in axes[:2]:
        ax.axvspan(0, 1, color="#dcebf3", alpha=0.65, zorder=-1)
        ax.axhline(1, c="#888888", lw=0.7, ls=":")
        ax.set(xlabel="Relative time τ = δP · t", ylim=(0.45, 1.04), xlim=(0, 5))
        ax.grid(alpha=0.15)
    axes[0].set(title="A  PFKL mRNA", ylabel="Amount relative to baseline")
    axes[1].set(title="B  PFKL protein")
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
                label=(f"Decay, γ = {g:g}" if mech == "decay" else "Translation"),
            )
    axes[2].set(
        title="C  Protein at intervention end",
        xlabel="Intervention duration L (relative time)",
        ylim=(0.45, 1.04),
        xscale="log",
        xticks=[0.25, 1, 4],
        xticklabels=["0.25", "1", "4"],
    )
    axes[2].minorticks_off()
    axes[2].axhline(0.5, c="#888888", lw=0.8, ls=":")
    axes[2].legend(frameon=False, fontsize=8, loc="upper right")
    axes[2].grid(alpha=0.15)
    fig.text(
        0.04,
        0.02,
        "Assumptions: q = 0.5; γ = 1 in A/B. Shading marks treatment. Time is relative.",
        fontsize=9,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUT / "regulation.svg", metadata={"Date": None})
    plt.close(fig)


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "pfkl_english_report",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    inputs = [ROOT / "output/part2" / name for name in SVG_SOURCES]
    translated = {str(p.relative_to(ROOT)): localise(p) for p in inputs}
    network = ROOT / "output/part2/mir6517_pathway/network.svg"
    localise(network)
    scope = ROOT / "output/part2/review_scope/summary.json"
    literature_scope(scope)
    sequence = ROOT / "output/part2/milk_inventory/sequence_comparison/summary.json"
    trajectories = ROOT / "output/part2/pfkl_regulation/trajectories.tsv"
    minima = ROOT / "output/part2/pfkl_regulation/minima.tsv"
    sequence_plot(sequence)
    regulation_plot(trajectories, minima)
    inputs += [network, scope, sequence, trajectories, minima, Path(__file__).resolve()]
    outputs = [OUT / Path(name).name for name in SVG_SOURCES]
    outputs += [
        OUT / "network.svg",
        OUT / "search_flow.svg",
        OUT / "sequence_classes.svg",
        OUT / "regulation.svg",
    ]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = {
        "inputs": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
        "outputs": {str(p.relative_to(ROOT)): digest(p) for p in outputs},
        "translated_text_elements": translated,
        "scope": "English colour report figures; saved data and original figures unchanged; no model fitting or new simulation.",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return inputs, outputs + [OUT / "manifest.json"]


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Build the result slides from saved results; no fitting or simulation."""

import csv
import hashlib
import json
import subprocess
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "output/presentation/mir6517_assets"
DECK = ROOT / "presentation/ergebnisse_mir6517/ergebnisse.typ"
PDF = ROOT / "output/presentation/ergebnisse_mir6517.pdf"
EXTRA_PDF = PDF.with_stem("ergebnisse_mir6517_zusatz")
FONT = ROOT / "presentation/assets/fonts"
GREEN, BLUE, ORANGE, GRAY = "#00883a", "#296992", "#b66b16", "#626c66"
inputs = set()


def read_file(relative):
    path = ROOT / relative
    inputs.add(path)
    return path.read_text()


def rows(relative):
    return list(csv.DictReader(read_file(relative).splitlines(), delimiter="\t"))


def save(fig, name):
    fig.savefig(OUT / (name + ".svg"), metadata={"Date": None}, bbox_inches="tight")
    plt.close(fig)


def clean(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=3, color=GRAY)
    ax.grid(axis="y", color="#e8ece9", linewidth=0.6)
    ax.set_axisbelow(True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for path in sorted(FONT.glob("*.ttf")):
        font_manager.fontManager.addfont(path)
        inputs.add(path)
    plt.rcParams.update(
        {
            "font.family": "Roboto",
            "font.size": 13,
            "svg.fonttype": "path",
            "svg.hashsalt": "mir6517-slides",
            "axes.labelcolor": "#232323",
            "text.color": "#232323",
        }
    )

    # Existing means and fitted curve; no new model fit.
    means = rows("output/part2/pfkl_enzyme/concentration_summary.tsv")
    curves = rows("output/part2/pfkl_enzyme/curves.tsv")
    fit = json.loads(read_file("output/part2/pfkl_enzyme/fit.json"))
    cv = rows("output/part2/pfkl_enzyme/held_out_predictions.tsv")
    panels = [plt.subplots(figsize=(5.6, 3.0)) for _ in range(2)]
    axs = [ax for _, ax in panels]
    x = [float(r["F6P_mM"]) for r in means]
    y = [float(r["mean_U_per_mg"]) for r in means]
    axs[0].plot(
        [float(r["F6P_mM"]) for r in curves],
        [float(r["observed_signal_U_per_mg"]) for r in curves],
        color=GREEN,
        label="Hill-Anpassung",
    )
    axs[0].scatter(x, y, color="#232323", s=30, zorder=3, label="Messmittel")
    axs[0].set_title("Anpassung an alle Messwerte", loc="left", fontsize=14)
    axs[1].scatter(x, y, color="#232323", s=30, zorder=3, label="Messmittel")
    for model, label, color, style in [
        ("hill", "Hill", GREEN, "-"),
        ("michaelis", "Michaelis-Menten", BLUE, "--"),
    ]:
        by_level = {
            float(r["held_out_mM"]): float(r["predicted"])
            for r in cv
            if r["model"] == model
        }
        axs[1].plot(
            x,
            [by_level[s] for s in x],
            style,
            color=color,
            marker="o",
            markersize=4,
            label=label,
        )
    axs[1].set_title("Jeweils eine Konzentration ausgelassen", loc="left", fontsize=14)
    for ax in axs:
        clean(ax)
        ax.set_xlabel("F6P [mM]")
        ax.set_ylim(-0.25, 10)
        ax.legend(frameon=False, fontsize=10, loc="upper left")
    axs[0].set_ylabel("Gemessenes Signal [U/mg]")
    for (fig, _), name in zip(panels, ("enzyme_fit", "enzyme_prediction")):
        left = 0.14 if name == "enzyme_fit" else 0.075
        fig.subplots_adjust(left=left, right=left + 0.84, bottom=0.21, top=0.87)
        fig.savefig(OUT / (name + ".svg"), metadata={"Date": None})
        plt.close(fig)
    (OUT / "enzyme.svg").unlink(missing_ok=True)

    trajectories = rows("output/part2/pfkl_regulation/trajectories.tsv")
    panels = [plt.subplots(figsize=(5.8, 3.1)) for _ in range(2)]
    axes = [ax for _, ax in panels]
    for mechanism, label, color, style in [
        ("decay", "mRNA wird schneller abgebaut", GREEN, "-"),
        ("translation", "Aus mRNA entsteht weniger Protein", BLUE, "--"),
    ]:
        subset = [
            r
            for r in trajectories
            if r["mechanism"] == mechanism
            and float(r["q"]) == 0.5
            and float(r["gamma"]) == 1
            and float(r["duration"]) == 1
            and float(r["tau"]) <= 5
        ]
        assert subset, mechanism
        end = next(r for r in subset if float(r["tau"]) == 1)
        for ax, variable in zip(axes, ("mRNA", "protein")):
            ax.plot(
                [float(r["tau"]) for r in subset],
                [100 * float(r[variable]) for r in subset],
                color=color, lw=2.6, ls=style, label=label,
            )
            ax.scatter([1], [100 * float(end[variable])], color=color, zorder=3)
    for ax, title in zip(axes, ("PFKL-mRNA", "PFKL-Protein")):
        ax.axvspan(0, 1, color="#edf3ef", zorder=-1)
        ax.axvline(1, color=GRAY, ls=":", lw=1)
        ax.text(0.08, 103, "Hemmphase", fontsize=9)
        ax.set(ylim=(40, 108), xlim=(0, 5), yticks=[40, 60, 80, 100],
               ylabel="Menge [% des Ausgangswerts]",
               xlabel=r"Modellzeit $\tau$")
        ax.set_title(title, loc="left", fontsize=14)
        clean(ax)
    for (fig, _), name in zip(panels, ("regulation_mrna", "regulation_protein")):
        fig.subplots_adjust(left=0.14, right=0.98, bottom=0.22, top=0.85)
        fig.savefig(OUT / (name + ".svg"), metadata={"Date": None})
        plt.close(fig)
    (OUT / "regulation.svg").unlink(missing_ok=True)

    petri = """digraph G {
 graph [rankdir=LR, bgcolor="transparent", nodesep=.55, ranksep=.55, pad=.1];
 node [fontname="Roboto", fontsize=20, color="#626c66",penwidth=1.5];
 edge [fontname="Roboto", fontsize=18,color="#626c66",penwidth=1.5];
 tx [label="Transkription",shape=box]; M [label="M",shape=circle,width=.8,color="#00883a",penwidth=2];
 tl [label="Translation",shape=box]; E [label="E",shape=circle,width=.8,color="#00883a",penwidth=2];
 dm [label="mRNA-Abbau",shape=box]; de [label="Proteinabbau",shape=box];
 tx -> M [label="γ"]; M -> dm [label="γ · d · M"];
 M -> tl [style=dashed,arrowhead=none,label="liest M"];
 tl -> E [label="k · M"]; E -> de [label="E"];
 {rank=same;tx;dm} {rank=same;tl;de}
 }"""
    (OUT / "petri.dot").write_text(petri)
    subprocess.run(
        ["dot", "-Tsvg", str(OUT / "petri.dot"), "-o", str(OUT / "petri.svg")],
        check=True,
    )

    # Data-driven text keeps displayed counts and example values tied to saved tables.
    evidence = json.loads(read_file("output/part2/review_summary/evidence.json"))
    assert evidence["hits"] - evidence["duplicates"] == evidence["unique_records"]
    decisions = evidence["screening_decisions"]
    assessed = evidence["title_abstract_assessments"]
    excluded = decisions["Für Milch-Inventar ausgeschlossen"]
    followup = assessed - excluded
    done = evidence["followup_fulltexts"]["Gezielt geprüft"]
    pending = evidence["followup_pending"]
    assert assessed + 11 == evidence["unique_records"]
    assert followup == done + pending
    recovery = json.loads(read_file("output/part2/pfkl_identifiability/summary.json"))
    def decimal(value, digits=2):
        return f"{value:.{digits}f}".replace(".", ",")

    def noisy_gamma(design):
        return next(
            r["best"]["gamma"]
            for r in recovery["experiments"]
            if r["design"] == design and r["dataset"] == "noise_example"
        )

    values = dict(
        sequence_counts=list(evidence["classes"].values()),
        sequence_total=sum(evidence["classes"].values()),
        search_hits=evidence["hits"],
        search_duplicates=evidence["duplicates"],
        both_studies=evidence["paper_support"]["2"],
        one_study=evidence["paper_support"]["1"],
        search_records=evidence["unique_records"],
        deferred=evidence["followup_pending"],
        enzyme_V=round(fit["full_fit"]["hill"]["V_U_per_mg"], 2),
        enzyme_K=round(fit["full_fit"]["hill"]["K_mM"], 2),
        enzyme_h=round(fit["full_fit"]["hill"]["hill"], 2),
        noise_gamma_protein=decimal(noisy_gamma("dense_protein")),
        noise_gamma_joint=decimal(noisy_gamma("dense_joint")),
    )
    (OUT / "values.json").write_text(json.dumps(values, indent=2) + "\n")
    inputs.add(DECK)
    inputs.add(Path(__file__).resolve())
    for relative in (
        "obsidian/Projekt/Literatur/01 Fragestellung und Kriterien/Rechercheprotokoll Milch-miRNA-Inventar.md",
        "obsidian/Projekt/Literatur/02 Suche/Ergänzungssuche Milch und Verarbeitung.md",
        "obsidian/Projekt/Literatur/02 Suche/Begrenzte Kandidatensuche am 10. Oktober.md",
        "obsidian/Projekt/Literatur/03 Screening und Auswahl/Umfang der Literatursynthese.md",
        "obsidian/Projekt/Literatur/04 Datenextraktion/Milch und Verarbeitung.md",
        "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Targetvergleich aller 16 Kandidaten.md",
        "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Kandidatenauswahl nach dem Professorenfeedback.md",
        "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Begrenzte Erweiterung der Kandidatenauswahl.md",
        "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Milchnachweis und funktioneller Transfer.md",
    ):
        read_file(relative)
    inputs.update((ROOT / "report/typst").glob("*.typ"))
    inputs.add(ROOT / "report/typst/references.bib")
    before = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(inputs)
    }
    for pdf, extra in [(PDF, "false"), (EXTRA_PDF, "true")]:
        subprocess.run(
            [
                "typst",
                "compile",
                "--root",
                str(ROOT),
                "--font-path",
                str(FONT),
                "--input",
                f"zusatz={extra}",
                str(DECK),
                str(pdf),
            ],
            check=True,
        )
    assert all(
        hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h
        for p, h in before.items()
    )
    outputs = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(
            [
                *OUT.glob("*.svg"),
                *OUT.glob("*.dot"),
                OUT / "values.json",
                PDF,
                EXTRA_PDF,
            ]
        )
    }
    manifest = dict(
        purpose="Presentation of existing results; no new fit, simulation or literature search.",
        inputs=before,
        outputs=outputs,
        tools={
            "typst": subprocess.check_output(["typst", "--version"], text=True).strip(),
            "matplotlib": matplotlib.__version__,
            "graphviz": subprocess.run(
                ["dot", "-V"], capture_output=True, text=True, check=True
            ).stderr.strip(),
        },
        selections={
            "regulation": "q=0.5, gamma=1, duration=1, tau<=5; paired mRNA and protein panels, shared amount scale",
            "literature": "Focused synthesis: ten milk-comparison studies and two additional studies; two of the ten supply the sequence inventory. Historical search classifications are not counts of personal abstract reading. No new screening.",
            "identifiability": "Existing known-mechanism synthetic recovery, q=0.5 gamma=beta=1, seed=6517; no biological fitting",
            "enzyme": "Means without error bars; existing full fit and held-out predictions",
        },
    )
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    )
    print(PDF.relative_to(ROOT))
    print(EXTRA_PDF.relative_to(ROOT))


if __name__ == "__main__":
    main()

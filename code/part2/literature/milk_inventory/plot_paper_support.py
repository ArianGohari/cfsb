"""Count qualifying sequence–paper pairs from the harmonized milk inventory.

Run with the locked environment in code/part2/reproduction. No network access.
The editable source catalogue remains in Obsidian; refresh its export first.
"""

import csv
import hashlib
import json
import platform
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "output/part2/milk_inventory/sequence_comparison"
OUT = ROOT / "output/part2/milk_inventory/paper_support"
CATALOGUE = ROOT / "output/part2/sources/Quellen.tsv"
STUDIES = {
    "li2016": {
        "doi": "10.1371/journal.pone.0154129",
        "short_name": "Li et al. (2016)",
        "material": "Milchfett; Molke; Milchzellen",
        "criterion": ">=10 CPM in >=2/4 Kühen in mindestens einer Fraktion",
    },
    "krupova2023": {
        "doi": "10.1038/s41597-023-02347-0",
        "short_name": "Krupova et al. (2023)",
        "material": "Extrazelluläre Vesikel aus Kuhmilch",
        "criterion": ">1 publizierte (gerundete) TPM in >=2/5 Kühen; eigener explorativer Filter",
    },
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write(name, rows):
    with (OUT / name).open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [
        BASE / "sequence_support.tsv",
        BASE / "known_annotation_comparison.tsv",
        CATALOGUE,
    ]
    frozen = json.loads((BASE / "manifest.json").read_text())
    for path in inputs[:2]:
        assert sha(path) == frozen["outputs"][path.name], (
            f"Changed frozen input: {path}"
        )
    support = read(inputs[0])
    annotations = [row for row in read(inputs[1]) if row["qualifies"] == "True"]
    catalogue = {row["DOI"]: row for row in read(CATALOGUE) if row["DOI"]}
    evidence = []
    membership = defaultdict(set)
    for row in annotations:
        seq, study = row["sequence_RNA"], row["study"]
        membership[seq].add(study)
        evidence.append(
            {
                "sequence_RNA": seq,
                "study": study,
                "doi": STUDIES[study]["doi"],
                **{
                    key: row[key]
                    for key in (
                        "original_name",
                        "source_path",
                        "source_sheet",
                        "source_row",
                        "qualified_materials",
                        "replicate_support",
                        "sequence_origin",
                        "source_reference_accession",
                        "sequence_matches_study_reference",
                    )
                },
            }
        )
    assert len({row["sequence_RNA"] for row in support}) == len(support)
    assert set(membership) == {row["sequence_RNA"] for row in support}
    counts = []
    for row in support:
        seq = row["sequence_RNA"]
        studies = sorted(membership[seq])
        assert set(studies) == set(row["supporting_studies"].split(";"))
        assert len(studies) == int(row["n_studies"])
        counts.append(
            {
                "miRNA_names": row["names"],
                "sequence_RNA": seq,
                "n_papers": len(studies),
                "studies": ";".join(studies),
                "doi": ";".join(STUDIES[key]["doi"] for key in studies),
                "human_class": row["human_class"],
            }
        )
    counts.sort(
        key=lambda row: (-row["n_papers"], row["miRNA_names"], row["sequence_RNA"])
    )
    evidence.sort(
        key=lambda row: (row["sequence_RNA"], row["study"], row["original_name"])
    )
    histogram = Counter(row["n_papers"] for row in counts)
    sources = []
    for study, metadata in STUDIES.items():
        source = catalogue[metadata["doi"]]
        sources.append(
            {
                "study": study,
                **metadata,
                "title": source["Titel"],
                "source_note": source["Notiz"],
                "n_sequences": sum(study in studies for studies in membership.values()),
            }
        )
    write("mirna_paper_counts.tsv", counts)
    write("source_evidence.tsv", evidence)
    write("sources.tsv", sources)
    write(
        "histogram.tsv",
        [{"n_papers": n, "n_sequences": histogram[n]} for n in sorted(histogram)],
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.hashsalt": "cfsb-milk-paper-support",
        }
    )
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    fig.subplots_adjust(left=0.12, right=0.96, bottom=0.23, top=0.75)
    fig.text(
        0.12,
        0.93,
        "Milch-miRNAs: Belege in den ausgewerteten Papers",
        fontsize=15,
        weight="bold",
    )
    fig.text(
        0.12,
        0.86,
        f"{len(counts)} Referenzsequenzen · {len(sources)} vollständig ausgewertete Papers",
        color="#626c66",
    )
    xs = sorted(histogram)
    bars = ax.bar(
        xs, [histogram[x] for x in xs], color=["#97b6a4", "#00883a"], width=0.48
    )
    ax.set_xticks(xs, [str(x) for x in xs])
    ax.set_xlabel("Anzahl Papers mit Nachweis gemäß Auswertungsregeln", labelpad=12)
    ax.set_ylabel("Anzahl miRNA-Referenzsequenzen")
    ax.set_ylim(0, max(histogram.values()) * 1.25)
    ax.set_xlim(0.35, max(xs) + 0.65)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#e4e9e5")
    for bar, n in zip(bars, xs):
        label = f"{histogram[n]} ({100 * histogram[n] / len(counts):.1f} %)".replace(
            ".", ","
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 5,
            label,
            ha="center",
            weight="bold",
        )
    fig.text(
        0.12,
        0.065,
        "Zwischenstand · Li et al. (2016); Krupova et al. (2023)",
        fontsize=9,
        color="#626c66",
    )
    fig.text(
        0.12,
        0.025,
        "Weitere Studien noch auszuwerten. Sequenzaliase zusammengeführt; keine Abundanzdarstellung.",
        fontsize=9,
        color="#626c66",
    )
    fig.savefig(OUT / "paper_support.svg", metadata={"Date": None, "Creator": "CFSB"})
    fig.savefig(OUT / "paper_support.png", dpi=200, metadata={"Software": "CFSB"})
    plt.close(fig)

    lines = [
        "# Paperbelege je miRNA-Referenzsequenz",
        "",
        "Zwischenstand aus zwei Papers; keine Häufigkeit in der gesamten Literatur. Identische Referenzsequenzen werden zusammengeführt. Ein Paper zählt je Sequenz einmal, unabhängig von Fraktionen, Replikaten und paralleler Datenablage. Die Schwellen stehen in `sources.tsv`; Originalfundstellen in `source_evidence.tsv`.",
        "",
        "| miRNA-Namen | Papers | Quellen |",
        "|---|---:|---|",
    ]
    for row in counts:
        links = ", ".join(
            f"[{STUDIES[key]['short_name']}](https://doi.org/{STUDIES[key]['doi']})"
            for key in row["studies"].split(";")
        )
        lines.append(f"| {row['miRNA_names']} | {row['n_papers']} | {links} |")
    (OUT / "miRNAs und Paperbelege.md").write_text("\n".join(lines) + "\n")
    summary = {
        "n_sequences": len(counts),
        "n_papers": len(sources),
        "histogram": dict(sorted(histogram.items())),
        "sequence_paper_pairs": sum(len(v) for v in membership.values()),
        "scope": "Two fully harmonized studies, not a completed systematic review",
        "unit": "Qualifying mature reference sequence; not verified read-level sequence",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs += [
        BASE / "manifest.json",
        Path(__file__),
        ROOT / "code/part2/reproduction/uv.lock",
    ]
    manifest = {
        "inputs": {str(p.relative_to(ROOT)): sha(p) for p in inputs},
        "python": platform.python_version(),
        "matplotlib": matplotlib.__version__,
        "outputs": {
            p.name: sha(p)
            for p in sorted(OUT.iterdir())
            if p.is_file() and p.name != "manifest.json"
        },
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

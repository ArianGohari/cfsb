"""Plot all qualifying milk sequences against the frozen human reference.

Recompute exact/seed matches from FASTA; retain all candidates and review flags.
No claim of species exclusivity or absence from the human transcriptome.
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
OUT = ROOT / "output/part2/milk_inventory/human_comparison"
REF = ROOT / "data/datasets/milk_mirna_inventory/references/mirbase23_1_mature.fa"
CLASSES = ["exact_human_sequence", "human_seed_only", "no_human_seed_match"]
LABELS = dict(
    zip(
        CLASSES,
        [
            "Identische humane Referenzsequenz",
            "Nur gleicher humaner Seed",
            "Kein humaner Seed-Treffer",
        ],
    )
)
DOIS = {
    "li2016": "10.1371/journal.pone.0154129",
    "krupova2023": "10.1038/s41597-023-02347-0",
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
    support_path = BASE / "sequence_support.tsv"
    priority_path = BASE / "annotation_review_priority.tsv"
    source_manifest = BASE / "manifest.json"
    manifest = json.loads(source_manifest.read_text())
    for path in [support_path, priority_path]:
        assert sha(path) == manifest["outputs"][path.name], path
    assert sha(REF) == manifest["inputs"][str(REF.relative_to(ROOT))]
    sequences = {}
    name = None
    for line in REF.read_text().splitlines():
        if line.startswith(">"):
            parts = line[1:].split()
            name = parts[0]
            if name in sequences:
                name += "|" + parts[1]
            assert name not in sequences
            sequences[name] = ""
        elif line.strip():
            sequences[name] += line.strip().upper().replace("T", "U")
    exact, seeds = defaultdict(list), defaultdict(list)
    for name, seq in sequences.items():
        if name.startswith("hsa-"):
            exact[seq].append(name)
            seeds[seq[1:8]].append(name)
    prior = {r["sequence_RNA"] for r in read(priority_path)}
    rows = []
    for r in read(support_path):
        seq = r["sequence_RNA"]
        cls = (
            CLASSES[0] if exact[seq] else CLASSES[1] if seeds[seq[1:8]] else CLASSES[2]
        )
        assert cls == r["human_class"], r["names"]
        assert ";".join(sorted(exact[seq])) == r["human_exact_names"]
        assert ";".join(sorted(seeds[seq[1:8]])) == r["human_seed_names"]
        flags = []
        if not r["current_bovine_exact_names"]:
            flags.append(
                "Keine exakte bovine Sequenz in aktueller Referenz; Annotation prüfen"
            )
        if r["five_prime_length_variant_names"]:
            flags.append(
                "Einfache 5′-Endvariante einer humanen Sequenz; Seed-Verschiebung prüfen"
            )
        if r["three_prime_length_variant_names"]:
            flags.append("Einfache 3′-Endvariante einer humanen Sequenz")
        if r["n_studies"] == "1":
            flags.append("Bisher ein qualifizierender Studienbeleg")
        rows.append(
            {
                "miRNA_names": r["names"],
                "sequence_RNA": seq,
                "human_class": cls,
                "class_label": LABELS[cls],
                "n_papers": int(r["n_studies"]),
                "studies": r["supporting_studies"],
                "doi": ";".join(DOIS[x] for x in r["supporting_studies"].split(";")),
                "previous_16": seq in prior,
                "review_scope": "Vergleichsgruppe mit humanem Gegenstück"
                if cls == CLASSES[0]
                else "Breiter Prüfkandidatenpool; nicht ausgeschlossen",
                "human_exact_names": r["human_exact_names"],
                "human_seed_names": r["human_seed_names"],
                "current_bovine_exact_names": r["current_bovine_exact_names"],
                "five_prime_length_variant_names": r["five_prime_length_variant_names"],
                "three_prime_length_variant_names": r[
                    "three_prime_length_variant_names"
                ],
                "review_flags": "; ".join(flags),
            }
        )
    rows.sort(
        key=lambda r: (
            CLASSES.index(r["human_class"]),
            -r["n_papers"],
            r["miRNA_names"],
        )
    )
    assert len({r["sequence_RNA"] for r in rows}) == len(rows)
    counts = Counter(r["human_class"] for r in rows)
    candidates = [r for r in rows if r["human_class"] != CLASSES[0]]
    added = [r for r in candidates if not r["previous_16"]]
    added_no_seed = [r for r in added if r["human_class"] == CLASSES[2]]
    write("all_sequences.tsv", rows)
    write("candidate_pool.tsv", candidates)
    write("additional_no_seed_candidates.tsv", added_no_seed)
    write(
        "class_counts.tsv",
        [
            {
                "class": c,
                "label": LABELS[c],
                "n_sequences": counts[c],
                "percent": round(100 * counts[c] / len(rows), 3),
            }
            for c in CLASSES
        ],
    )

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.hashsalt": "cfsb-human-comparison",
        }
    )
    fig, ax = plt.subplots(figsize=(9, 5.8))
    fig.subplots_adjust(left=0.12, right=0.96, bottom=0.33, top=0.78)
    fig.text(
        0.12, 0.94, "Milch-miRNAs im Vergleich zum Menschen", fontsize=17, weight="bold"
    )
    fig.text(
        0.12,
        0.885,
        f"{len(rows)} Referenzsequenzen aus zwei Milchstudien · miRBase 23.1",
        color="#58675f",
    )
    colors = ["#00883a", "#5585a6", "#c58136"]
    ax.bar(0, counts[CLASSES[0]], width=0.55, color=colors[0])
    ax.bar(1, counts[CLASSES[1]], width=0.55, color=colors[1])
    ax.bar(
        1, counts[CLASSES[2]], bottom=counts[CLASSES[1]], width=0.55, color=colors[2]
    )
    for x, y, count in [
        (0, counts[CLASSES[0]] / 2, counts[CLASSES[0]]),
        (1, counts[CLASSES[1]] / 2, counts[CLASSES[1]]),
        (1, counts[CLASSES[1]] + counts[CLASSES[2]] / 2, counts[CLASSES[2]]),
    ]:
        ax.text(
            x,
            y,
            str(count),
            ha="center",
            va="center",
            color="white",
            fontsize=19,
            weight="bold",
        )
    for x, total in [(0, counts[CLASSES[0]]), (1, len(candidates))]:
        ax.text(
            x,
            total + 7,
            f"{total} ({100 * total / len(rows):.1f} %)".replace(".", ","),
            ha="center",
            weight="bold",
        )
    ax.set_xticks(
        [0, 1],
        [
            "Identische Sequenz\nbeim Menschen annotiert",
            "Keine identische Sequenz\nbeim Menschen annotiert",
        ],
    )
    ax.set_ylabel("Anzahl miRNA-Referenzsequenzen")
    ax.set_ylim(0, max(counts[CLASSES[0]], len(candidates)) * 1.23)
    ax.set_xlim(-0.65, 1.65)
    ax.yaxis.grid(True, color="#e5e9e7")
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    for y, color, label in zip([0.19, 0.148, 0.106], colors, LABELS.values()):
        fig.text(0.12, y, "●", color=color, fontsize=14)
        fig.text(0.147, y, label, fontsize=10)
    fig.text(
        0.12,
        0.05,
        "Fehlender Referenztreffer belegt keine Kuh-Exklusivität. Endvarianten sind gesondert markiert.",
        fontsize=9,
        color="#58675f",
    )
    fig.text(
        0.12,
        0.016,
        "Milchdaten: Li et al. (2016), Krupova et al. (2023). Zwischenstand; weitere Studien offen.",
        fontsize=9,
        color="#58675f",
    )
    fig.savefig(OUT / "human_comparison.png", dpi=200, metadata={"Software": "CFSB"})
    fig.savefig(
        OUT / "human_comparison.svg", metadata={"Date": None, "Creator": "CFSB"}
    )
    plt.close(fig)

    lines = [
        "# Erweiterter Kandidatenpool",
        "",
        f"{len(candidates)} Sequenzen ohne identisches humanes Referenzgegenstück. {len(added)} waren nicht in der bisherigen 16er-Priorisierung. Keine endgültige Auswahl: funktionelle Evidenz, Sequenzenden und Annotation müssen geprüft werden. Die Milchbelege und die humane Vergleichsreferenz bleiben dieselben; es wurden keine neuen Studien hinzugezählt.",
        "",
    ]
    for cls in CLASSES[1:]:
        lines += [
            f"## {LABELS[cls]} ({counts[cls]})",
            "",
            "| Originalname(n) | Papers | Bisherige 16 | Offene Prüfung | Quellen |",
            "|---|---:|---|---|---|",
        ]
        for r in candidates:
            if r["human_class"] != cls:
                continue
            links = ", ".join(
                f"[{key}](https://doi.org/{DOIS[key]})"
                for key in r["studies"].split(";")
            )
            lines.append(
                f"| {r['miRNA_names']} | {r['n_papers']} | {'ja' if r['previous_16'] else 'nein'} | {r['review_flags'] or 'Annotation, Read-Enden und Funktion prüfen'} | {links} |"
            )
        lines.append("")
    (OUT / "Erweiterter Kandidatenpool.md").write_text("\n".join(lines))
    summary = {
        "n_sequences": len(rows),
        "classes": dict(counts),
        "candidate_pool": len(candidates),
        "previous_priority": len(prior),
        "additional_candidates": len(added),
        "additional_no_seed_candidates": len(added_no_seed),
        "no_seed_with_5prime_variant_flag": sum(
            bool(r["five_prime_length_variant_names"])
            for r in rows
            if r["human_class"] == CLASSES[2]
        ),
        "interpretation": "Reference sequence comparison, not species exclusivity or functional validation",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [
        support_path,
        priority_path,
        source_manifest,
        REF,
        Path(__file__),
        ROOT / "code/part2/reproduction/uv.lock",
    ]
    result = {
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
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the growing Part II Typst report from existing, frozen analysis outputs."""

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from build_report_figures import build as build_figures

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "output/part2/milk_inventory"
OUT = ROOT / "output/part2/typst_report"
PDF = ROOT / "output/pdf/part2_report.pdf"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PDF.parent.mkdir(parents=True, exist_ok=True)
    figure_inputs, figure_outputs = build_figures()
    paths = [
        BASE / "sequence_comparison/summary.json",
        BASE / "annotation_audit/summary.json",
        BASE / "sequence_comparison/measurements.tsv",
        BASE / "sequence_comparison/annotation_review_priority.tsv",
    ]
    # Check analysis outputs against the saved extraction manifest before using them.
    manifest = json.loads((BASE / "sequence_comparison/manifest.json").read_text())
    for relative, digest in manifest["outputs"].items():
        p = ROOT / relative
        if not p.exists():
            p = BASE / "sequence_comparison" / relative
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, p
    summary = json.loads(paths[0].read_text())
    audit = json.loads(paths[1].read_text())
    assert (
        sum(summary["comparison"]["classes_supported_in_both"].values())
        == summary["comparison"]["sequences_supported_in_both_studies"]
    )
    priority = {r["names"]: r for r in csv.DictReader(paths[3].open(), delimiter="\t")}
    names = ["bta-miR-3432a", "bta-miR-6119-5p", "bta-miR-2336", "bta-miR-2478"]
    cows = ["B1", "B2", "B3", "B62", "B20"]
    rows = list(csv.DictReader(paths[2].open(), delimiter="\t"))
    candidates = []
    for name in names:
        selected = [
            r
            for r in rows
            if r["study"] == "krupova2023"
            and r["original_name"] == name
            and r["unit"] == "reported_TPM_integer"
            and r["sample"] in cows
        ]
        assert len(selected) == 5 and {r["sample"] for r in selected} == set(cows)
        values = [
            float(next(r["value"] for r in selected if r["sample"] == c)) for c in cows
        ]
        candidates.append(dict(name=name, values=values, mean=sum(values) / 5))
        assert (
            abs(sum(values) / 5 - float(priority[name]["krupova_mean_TPM"])) < 1e-9
        ), name
    data = dict(
        comparison=summary["comparison"], annotation=audit, candidates=candidates
    )
    (OUT / "evidence.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    # A vector dot plot: every point is one cow, no pooling across studies or units.
    xmax = max(v for c in candidates for v in c["values"])
    upper = ((int(xmax) // 50) + 1) * 50
    left, width = 150, 470
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="240" viewBox="0 0 720 240">',
        '<rect width="720" height="240" fill="white"/>',
        '<g font-family="Arial, sans-serif" font-size="14" fill="#242c2a">',
    ]
    for tick in range(0, upper + 1, 50):
        x = left + width * tick / upper
        svg += [
            f'<line x1="{x}" x2="{x}" y1="20" y2="187" stroke="#e3e8e5"/>',
            f'<text x="{x}" y="208" text-anchor="middle">{tick}</text>',
        ]
    for i, c in enumerate(candidates):
        y = 40 + i * 43
        svg.append(
            f'<text x="135" y="{y + 5}" text-anchor="end">{escape(c["name"].replace("bta-", ""))}</text>'
        )
        for j, v in enumerate(c["values"]):
            svg.append(
                f'<circle cx="{left + width * v / upper}" cy="{y + (j - 2) * 3}" r="4" fill="#444444" fill-opacity="0.7"/>'
            )
        x = left + width * c["mean"] / upper
        svg.append(
            f'<line x1="{x}" x2="{x}" y1="{y - 12}" y2="{y + 12}" stroke="#1f3028" stroke-width="2"/>'
        )
    svg += [
        '<text x="385" y="234" text-anchor="middle">TPM · five cow samples · line = mean</text>',
        "</g></svg>",
    ]
    (OUT / "candidate_abundance.svg").write_text("\n".join(svg) + "\n")
    subprocess.run(
        [
            "typst",
            "compile",
            "--root",
            str(ROOT),
            "--creation-timestamp",
            "1791504000",
            str(ROOT / "report/typst/main.typ"),
            str(PDF),
        ],
        check=True,
    )
    inputs = (
        paths
        + sorted(
            p
            for p in (ROOT / "report/typst").rglob("*")
            if p.suffix in {".typ", ".bib", ".md"}
        )
        + [Path(__file__).resolve()]
    )
    inputs += [
        ROOT / "output/part2/mir6517_pathway" / name
        for name in ["gene_evidence.tsv", "edges.tsv", "manifest.json"]
    ]
    inputs += [
        ROOT / "output/part2/milk_inventory/pfkp_review" / name
        for name in ["isoform_audit.json", "manifest.json"]
    ]
    inputs += [
        ROOT / "output/part2/milk_inventory/pgam1_dlat_sequences" / name
        for name in ["evidence.json", "manifest.json"]
    ]
    inputs += [
        ROOT
        / "data/datasets/milk_mirna_inventory/pgam1_dlat_review_20261011/manifest.json"
    ]
    inputs += [
        ROOT / "data/sources" / folder / name
        for folder in ["yoshida_2022_pgam1_adipose", "lu_2025_dlat_trpv3"]
        for name in ["article.xml", "provenance.json"]
    ]
    inputs += [
        ROOT / "output/part2/pfkl_enzyme/enzyme_fit.svg",
        ROOT / "output/part2/pfkl_enzyme/fit.json",
        ROOT / "output/part2/pfkl_enzyme/prediction_metrics.tsv",
    ]
    inputs += [
        ROOT / "output/part2/pfkl_regulation" / name
        for name in ["regulation.svg", "summary.json", "checks.json", "manifest.json"]
    ]
    inputs += [
        ROOT / "output/part2/pfkl_regulation_claims" / name
        for name in ["comparisons.tsv", "summary.json", "manifest.json"]
    ]
    inputs += [
        ROOT / "output/part2/pfkl_identifiability" / name
        for name in ["summary.json", "fits.tsv", "verification.json", "manifest.json"]
    ]
    inputs += [
        ROOT / "output/part2/review_summary" / name
        for name in [
            "search_flow.svg",
            "sequence_classes.svg",
            "evidence.json",
            "manifest.json",
            "bibliography_sources.json",
        ]
    ]
    inputs += [
        ROOT / "output/part2/review_scope" / name
        for name in [
            "report_sources.tsv",
            "deferred_records.tsv",
            "summary.json",
            "manifest.json",
        ]
    ]
    inputs += [
        ROOT / "obsidian/Projekt/Literatur/01 Fragestellung und Kriterien/Rechercheprotokoll Milch-miRNA-Inventar.md",
        ROOT / "obsidian/Projekt/Literatur/03 Screening und Auswahl/Prüfung der Rechercheabdeckung.md",
        BASE / "target_screen/summary.json",
        BASE / "additional_candidates/summary.json",
        BASE / "additional_candidates/target_pairs.tsv",
        BASE / "additional_candidates/manifest.json",
        ROOT / "data/sources/buffalo_2025_mir30f_rad23b/article.html",
        ROOT / "data/sources/buffalo_2025_mir30f_rad23b/retrieval_20261010.json",
    ]
    inputs += [
        ROOT
        / "data/datasets/milk_mirna_inventory/fulltext_review_20261011/manifest.json"
    ]
    inputs += [
        ROOT
        / "data/datasets/milk_mirna_inventory/pfkl_turnover_search_20261011/manifest.json",
        ROOT / "output/part2/milk_inventory/pfkl_turnover/evidence.json",
    ]
    inputs += [
        ROOT / "output/part2/pfkl_rna_decay" / name
        for name in ["summary.json", "manifest.json"]
    ]
    inputs += [ROOT / "output/part2/chen_turnover/summary.json"]
    inputs += [ROOT / "output/part2/milk_inventory/pfkl_followup/seed_controls.tsv"]
    inputs += [
        ROOT / "data/sources" / folder / name
        for folder in ["leiferman_2019_milk_formula", "husseini_2026_transgenic_milk"]
        for name in ["article.xml", "provenance.json"]
    ]
    inputs += figure_inputs + list((ROOT / "report/typst/vendor").rglob("*"))
    inputs = [p for p in inputs if p.is_file()]
    outputs = [
        OUT / "evidence.json",
        OUT / "candidate_abundance.svg",
        PDF,
    ] + figure_outputs
    provenance = dict(
        inputs={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in inputs
        },
        outputs={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in outputs
        },
        typst=subprocess.check_output(["typst", "--version"], text=True).strip(),
        scope="English kunskap report with milk evidence, target mapping and conditional PFKL modelling. Cow TPM plot is generated separately for later inclusion.",
    )
    (OUT / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(PDF.relative_to(ROOT))


if __name__ == "__main__":
    main()

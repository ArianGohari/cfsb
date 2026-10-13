#!/usr/bin/env python3
"""Descriptive CASP3 RNA context in GSE144424, preserving donor grouping."""

import csv
import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path
from scan_human_seeds import write_tsv
from review_casp3 import RAW, ROOT
from review_pfkl import digest

OUT = ROOT / "output/part2/milk_inventory/casp3_expression"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for r in json.loads((RAW / "expression_retrieval.json").read_text())["files"]:
        assert digest(RAW / r["file"]) == r["sha256"]
    with gzip.open(RAW / "GSE144424_matrix.txt.gz", "rt") as f:
        metadata = list(csv.reader(f, delimiter="\t"))
    titles = next(r[1:] for r in metadata if r and r[0] == "!Sample_title")
    accessions = next(r[1:] for r in metadata if r and r[0] == "!Sample_geo_accession")
    organisms = next(r[1:] for r in metadata if r and r[0] == "!Sample_organism_ch1")
    assert set(organisms) == {"Homo sapiens"}
    characteristics = [
        r[1:] for r in metadata if r and r[0] == "!Sample_characteristics_ch1"
    ]
    subjects = next(
        r for r in characteristics if all(s.startswith("subject id: ") for s in r)
    )
    conditions = next(
        r for r in characteristics if all(s.startswith("condition: ") for s in r)
    )
    samples = {}
    for title, acc, subject, condition in zip(titles, accessions, subjects, conditions):
        key = "H" + title.removesuffix("_RNA-seq")
        samples[key] = dict(
            sample=key,
            accession=acc,
            subject=subject.split(": ", 1)[1],
            condition=condition.split(": ", 1)[1],
        )
    with gzip.open(RAW / "GSE144424_counts.txt.gz", "rt") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)
        cols = header[6:]
        assert len(cols) == 84 and set(cols) == set(samples)
        totals = [0] * len(cols)
        target = None
        genes = 0
        seen = set()
        for row in reader:
            assert len(row) == len(header)
            assert row[0] not in seen
            seen.add(row[0])
            genes += 1
            values = [int(x) for x in row[6:]]
            assert min(values) >= 0
            totals = [a + b for a, b in zip(totals, values)]
            if row[0] == "ENSG00000164305":
                target = values
    assert target is not None
    rows = []
    groups = defaultdict(list)
    for col, count, total in zip(cols, target, totals):
        value = count / total * 1e6
        rows.append(
            dict(
                **samples[col],
                CASP3_count=count,
                provided_gene_sum=total,
                CPM_provided_genes=value,
            )
        )
        groups[(samples[col]["subject"], samples[col]["condition"])].append(value)
    donor_rows = [
        dict(
            subject=s, condition=c, culture_samples=len(v), CPM_mean=statistics.mean(v)
        )
        for (s, c), v in sorted(groups.items())
    ]
    conditions = sorted({r["condition"] for r in donor_rows})
    assert len(donor_rows) == 60 and len({r["subject"] for r in donor_rows}) == 15
    overview = []
    for c in conditions:
        values = [r["CPM_mean"] for r in donor_rows if r["condition"] == c]
        overview.append(
            dict(
                condition=c,
                donors=len(values),
                CPM_median=statistics.median(values),
                CPM_min=min(values),
                CPM_max=max(values),
            )
        )
    for name, rs in [
        ("samples.tsv", rows),
        ("donors.tsv", donor_rows),
        ("conditions.tsv", overview),
    ]:
        write_tsv(OUT / name, rs, list(rs[0]))
    result = dict(
        study="GSE144424",
        matrix_genes=genes,
        matrix_samples=len(cols),
        donors=15,
        CASP3_positive_samples=sum(x > 0 for x in target),
        conditions=overview,
        interpretation="Gene-level RNA context only. CPM uses all provided autosomal genes. Repeated cultures averaged within donor and condition. No differential-expression test, transcript-usage estimate, caspase activity or miRNA measurement.",
    )
    (OUT / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    inputs = [
        RAW / x
        for x in [
            "GSE144424_counts.txt.gz",
            "GSE144424_matrix.txt.gz",
            "expression_retrieval.json",
        ]
    ] + [
        Path(__file__),
        Path(__file__).with_name("review_casp3.py"),
        Path(__file__).with_name("review_pfkl.py"),
        Path(__file__).with_name("scan_human_seeds.py"),
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
                "outputs": {
                    p.name: digest(p)
                    for p in sorted(OUT.iterdir())
                    if p.name != "manifest.json"
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

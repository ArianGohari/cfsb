"""Extract PFKL from frozen RNADecayCafe 1.1 CSVs; no kinetic refitting.

Run with Python's standard library. Raw sources remain unchanged.
"""

from pathlib import Path
import csv
import hashlib
import json
import math
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "data/datasets/milk_mirna_inventory/rnadecaycafe_20261011"
OUT = ROOT / "output/part2/pfkl_rna_decay"


def read(name):
    with (SOURCE / name).open(newline="") as stream:
        for line, row in enumerate(csv.DictReader(stream), 2):
            yield dict(source_file=name, source_row=line, **row)


def write(name, rows):
    with (OUT / name).open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def check_rate(row, rate, half):
    k, h = float(row[rate]), float(row[half])
    assert math.isfinite(k) and k > 0 and math.isfinite(h) and h > 0
    assert math.isclose(k * h, math.log(2), rel_tol=1e-12)


def main():
    provenance = json.loads((SOURCE / "provenance.json").read_text())
    for item in provenance["files"]:
        data = (SOURCE / item["file"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert "md5:" + hashlib.md5(data).hexdigest() == item["zenodo_checksum"]
    metadata_rows = list(read("SampleDetails_v1.1.csv"))
    metadata = {row["sample"]: row for row in metadata_rows}
    assert len(metadata) == len(metadata_rows), "Ambiguous sample key"
    means = [
        row for row in read("AvgKdegs_genes_v1.1.csv") if row["feature_ID"] == "PFKL"
    ]
    details = [
        row
        for row in read("FeatureDetails_genes_v1.1.csv")
        if row["feature_ID"] == "PFKL"
    ]
    samples = []
    for row in read("RateConstants_genes_v1.1.csv"):
        if row["feature_ID"] != "PFKL":
            continue
        meta = metadata[row["sample"]]
        check_rate(row, "kdeg", "halflife")
        check_rate(row, "donorm_kdeg", "donorm_halflife")
        assert float(row["uncertainty_log_kdeg"]) > 0
        assert math.isclose(
            math.exp(float(row["log_kdeg"])), float(row["kdeg"]), rel_tol=1e-12
        )
        assert math.isclose(
            math.exp(float(row["donorm_log_kdeg"])),
            float(row["donorm_kdeg"]),
            rel_tol=1e-12,
        )
        samples.append(
            dict(
                **row,
                metadata_source_file=meta["source_file"],
                metadata_source_row=meta["source_row"],
                **{
                    k: v
                    for k, v in meta.items()
                    if k not in ("source_file", "source_row", "sample")
                },
            )
        )
    assert len(samples) == 64 and len(means) == 11 and len(details) == 1
    assert set(row["sample"] for row in samples) == set(metadata)
    assert details[0]["seqnames"] == "chr21"
    assert all(row["transcript_id"] == "NA" for row in samples), (
        "Reassess isoform interpretation"
    )
    grouped = defaultdict(list)
    for row in samples:
        grouped[(row["cell_line"], row["dataset"])].append(row)
    datasets = []
    for (cell, dataset), group in sorted(grouped.items()):
        datasets.append(
            dict(
                cell_line=cell,
                dataset=dataset,
                n_sample_estimates=len(group),
                label_times_h=",".join(
                    str(t) for t in sorted({float(r["label_time"]) for r in group})
                ),
                donorm_half_life_min_h=min(float(r["donorm_halflife"]) for r in group),
                donorm_half_life_max_h=max(float(r["donorm_halflife"]) for r in group),
                uncertainty_log_kdeg_min=min(
                    float(r["uncertainty_log_kdeg"]) for r in group
                ),
                uncertainty_log_kdeg_max=max(
                    float(r["uncertainty_log_kdeg"]) for r in group
                ),
                reads_min=min(int(r["reads"]) for r in group),
                reads_max=max(int(r["reads"]) for r in group),
            )
        )
    overview = []
    for row in means:
        check_rate(row, "avg_kdeg", "avg_halflife")
        check_rate(row, "avg_donorm_kdeg", "avg_donorm_halflife")
        group = [r for r in samples if r["cell_line"] == row["cell_line"]]
        overview.append(
            dict(
                cell_line=row["cell_line"],
                published_raw_half_life_h=row["avg_halflife"],
                published_donorm_half_life_h=row["avg_donorm_halflife"],
                published_donorm_kdeg_per_h=row["avg_donorm_kdeg"],
                n_sample_estimates=len(group),
                n_datasets=len({r["dataset"] for r in group}),
                label_times_h=",".join(
                    str(t) for t in sorted({float(r["label_time"]) for r in group})
                ),
                source_file=row["source_file"],
                source_row=row["source_row"],
            )
        )
    result = dict(
        gene="PFKL",
        species="Homo sapiens",
        version="1.1.0",
        source_doi="10.5281/zenodo.16884513",
        paper_doi="10.1101/2025.08.19.671151",
        n_cells=len(means),
        n_sample_estimates=len(samples),
        n_datasets=len({r["dataset"] for r in samples}),
        donorm_cell_summary_range_h=[
            min(float(r["avg_donorm_halflife"]) for r in means),
            max(float(r["avg_donorm_halflife"]) for r in means),
        ],
        estimate_unit="hours; kdeg per hour",
        aggregation="Published cell-line summaries copied; no new pooled mean across cells or datasets.",
        uncertainty="Original uncertainty_log_kdeg retained without deriving confidence intervals. Ranges describe sample estimates, not CIs.",
        cautions=[
            "No adipocyte data in inspected metadata.",
            "Sample estimates include different label times; 64 is not a count of independent biological replicates.",
            "Gene-level, transcript_id=NA; not a MANE-specific half-life.",
            "Database groups HEK293T datasets as HEK293 and MOLM variants under MOLM.",
            "Dropout normalization can remove genuine global differences; raw and normalized estimates preserved.",
            "MCF7 is cytoplasmic RNA in repository description, not whole-cell.",
            "Mabin source lacked public raw data at repository release; atlas estimates are public.",
            "Steady-state, constant synthesis and single decay rate assumed by original inference.",
            "No independent biological validation, protein rate, miRNA strength or model time calibration.",
        ],
        decision="Human non-adipocyte reference data only; no model parameter adopted.",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    write("pfkl_cell_lines.tsv", overview)
    write("pfkl_samples.tsv", samples)
    write("pfkl_dataset_groups.tsv", datasets)
    write("pfkl_feature.tsv", details)
    (OUT / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [SOURCE / f["file"] for f in provenance["files"]] + [
        SOURCE / "provenance.json",
        SOURCE / "zenodo_record.json",
        Path(__file__).resolve(),
    ]
    manifest = dict(
        inputs={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in inputs
        },
        outputs={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.iterdir())
            if p.name != "manifest.json"
        },
        rules="Exact feature_ID=PFKL, metadata join on unique sample key, source row includes CSV header. Published rates and half-lives checked against ln(2).",
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

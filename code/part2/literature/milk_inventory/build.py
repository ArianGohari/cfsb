"""Replay the first milk-miRNA extraction batch from frozen texts and current notes.

Run with: uv run --offline --with pyyaml==6.0.3 --no-project python
          code/part2/literature/milk_inventory/build.py
No network requests, sequence harmonization or candidate ranking are performed.
"""

from pathlib import Path
from collections import defaultdict
import argparse
import csv
import hashlib
import json
import yaml

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tsv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "output/part2/milk_inventory"
    )
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((DATA / "extraction_manifest.json").read_text())
    catalogue_path = ROOT / manifest["catalogue_path"]
    assert digest(catalogue_path) == manifest["catalogue_sha256"], (
        "Catalogue snapshot changed"
    )
    catalogue = list(csv.DictReader(catalogue_path.open(), delimiter="\t"))
    studies, input_hashes = {}, {}
    for record in manifest["studies"]:
        for kind in ["markdown", "pdf"]:
            path = ROOT / record[kind]
            assert digest(path) == record[kind + "_sha256"], f"Source changed: {path}"
            input_hashes[record[kind]] = digest(path)
        lines = (ROOT / record["markdown"]).read_text().splitlines()
        for evidence in record["evidence"]:
            for line in evidence["lines"]:
                assert evidence["needle"] in lines[line - 1], (record["id"], line)
        note = ROOT / record["source_note"]
        props = yaml.safe_load(note.read_text().split("\n---\n", 1)[0][4:])
        assert props["DOI"].lower() == record["doi"].lower()
        assert props["Inventarstudie"] == record["id"]
        assert props["Inventarstatus"] == "Eingeschlossen"
        input_hashes[record["source_note"]] = digest(note)
        studies[record["id"]] = {
            "study_id": record["id"],
            "doi": record["doi"],
            "source_note": record["source_note"],
            **{
                k.removeprefix("Inventar"): v
                for k, v in props.items()
                if k.startswith("Inventar")
            },
        }
    tsv(out / "studies.tsv", list(studies.values()))
    dois = {s["doi"] for s in studies.values()}
    screening = [
        {
            "source_id": r["Quellen-ID"],
            "doi": r["DOI"],
            "source_note": r["Notiz"],
            "inventory_status": "Eingeschlossen" if r["DOI"] in dois else "Offen",
            "reason": "Eigene bovine Milch-miRNA-Messungen; erste Volltextsichtung"
            if r["DOI"] in dois
            else "In dieser Charge nicht beurteilt",
        }
        for r in catalogue
    ]
    tsv(out / "screening.tsv", screening)
    observations = []
    for spec in manifest["tables"]:
        record = next(r for r in manifest["studies"] if r["id"] == spec["study"])
        lines = (ROOT / record["markdown"]).read_text().splitlines()
        rows = [
            (n, [c.strip() for c in lines[n - 1].strip("|").split("|")])
            for n in range(spec["first_line"], spec["last_line"] + 1)
        ]
        assert len(rows) == spec["rows"]
        for line, cells in rows:
            if spec["study"].startswith("li_"):
                assert len(cells) == 15, (line, cells)
                name = cells[1]
                assert name.startswith("bta-miR-")
                values = [int(v) for v in cells[2:14]]  # excludes MGT
                measurements = [
                    (fraction, cow, value, "CPM", "individual")
                    for fraction, offset in [
                        ("milk_fat", 0),
                        ("milk_whey", 4),
                        ("milk_cells", 8),
                    ]
                    for cow, value in zip(
                        ["12", "16", "710", "7134"], values[offset : offset + 4]
                    )
                ]
            elif spec["study"].startswith("chen_"):
                assert len(cells) == 5
                name = cells[1]
                assert name.startswith("miR-")
                measurements = [
                    (
                        fraction,
                        "pool_40_cows",
                        int(cells[index].replace(" ", "")),
                        "reads",
                        "pooled",
                    )
                    for fraction, index in [("mature_milk", 2), ("colostrum", 3)]
                ]
            else:
                assert len(cells) == 6
                name = cells[3]
                assert name.startswith("bta-")
                measurements = [
                    (
                        "milk_ev",
                        "mean_5_cows",
                        int(cells[5].replace(",", "")),
                        "mean_TPM",
                        "aggregate",
                    )
                ]
            for fraction, sample, value, unit, level in measurements:
                observations.append(
                    {
                        "study_id": spec["study"],
                        "doi": record["doi"],
                        "original_name": name,
                        "annotation_type": "predicted_novel"
                        if "EIA" in name
                        else "reported_known",
                        "material": fraction,
                        "sample": sample,
                        "value": value,
                        "unit": unit,
                        "measurement_level": level,
                        "source_path": record["markdown"],
                        "source_sha256": record["markdown_sha256"],
                        "line": line,
                        "pdf_page": spec["pdf_page"],
                        "table": spec["table"],
                        "human_sequence_status": "not_assessed",
                    }
                )
    keys = [
        (r["study_id"], r["original_name"], r["material"], r["sample"])
        for r in observations
    ]
    assert len(keys) == len(set(keys)), "Duplicate observations"
    assert all(r["value"] >= 0 for r in observations)
    tsv(out / "observations.tsv", observations)
    groups = defaultdict(list)
    for row in observations:
        groups[row["study_id"], row["original_name"], row["material"]].append(row)
    summaries = []
    for (study, name, material), rows in sorted(groups.items()):
        values = [r["value"] for r in rows]
        if study.startswith("li_"):
            n_ge10 = sum(v >= 10 for v in values)
            status = (
                "rounded_CPM_rule_met" if n_ge10 >= 2 else "rounded_CPM_rule_not_met"
            )
            if rows[0]["annotation_type"] == "predicted_novel":
                status = "novel_prediction_needs_annotation_review"
            rule = "Proxy: >=10 published rounded CPM in >=2/4 samples; not a replay of original unrounded counts"
        elif study.startswith("chen_"):
            n_ge10 = ""
            status = (
                "positive_read_count" if values[0] > 0 else "zero_reads_in_this_pool"
            )
            rule = "Read count only; one read is not independent replication or strong detection evidence"
        else:
            n_ge10 = ""
            status = "positive_reported_mean"
            rule = "Rounded mean of 5 cows; no per-animal prevalence inferred"
        summaries.append(
            {
                "study_id": study,
                "original_name": name,
                "material": material,
                "annotation_type": rows[0]["annotation_type"],
                "n_values": len(values),
                "unit": rows[0]["unit"],
                "minimum": min(values),
                "maximum": max(values),
                "mean": sum(values) / len(values),
                "n_ge10_CPM": n_ge10,
                "status": status,
                "interpretation": rule,
                "coverage": "selected_main_table_only",
                "human_sequence_status": "not_assessed",
            }
        )
    tsv(out / "evidence_summary.tsv", summaries)
    counts = {
        "catalogue_records": len(catalogue),
        "studies_screened_in_this_batch": len(studies),
        "included_for_inventory": len(studies),
        "not_assessed": len(catalogue) - len(studies),
        "tables_extracted": len(manifest["tables"]),
        "table_rows": sum(t["rows"] for t in manifest["tables"]),
        "numeric_observations": len(observations),
        "study_name_material_groups": len(summaries),
        "positive_values": sum(r["value"] > 0 for r in observations),
        "zero_values": sum(r["value"] == 0 for r in observations),
        "unique_original_labels": len({r["original_name"] for r in observations}),
        "note": "Original labels are not harmonized mature sequences; selected tables include zeros and novel predictions. No total milk-miRNA count or independent-study support count inferred.",
    }
    (out / "summary.json").write_text(
        json.dumps(counts, ensure_ascii=False, indent=2) + "\n"
    )
    input_hashes[str((DATA / "extraction_manifest.json").relative_to(ROOT))] = digest(
        DATA / "extraction_manifest.json"
    )
    input_hashes[manifest["catalogue_path"]] = manifest["catalogue_sha256"]
    input_hashes[str(Path(__file__).resolve().relative_to(ROOT))] = digest(
        Path(__file__)
    )
    outputs = {
        name: digest(out / name)
        for name in [
            "studies.tsv",
            "screening.tsv",
            "observations.tsv",
            "evidence_summary.tsv",
            "summary.json",
        ]
    }
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": input_hashes,
                "outputs": outputs,
                "validation": "Source hashes, evidence locators, table shape, unique measurement keys and nonnegative values verified",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()

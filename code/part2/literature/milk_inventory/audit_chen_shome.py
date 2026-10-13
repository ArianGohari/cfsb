"""Offline name audit for Chen and archive/sample reconciliation for Shome.

This deliberately does not infer Chen read sequences from modern names.
Run with Python's standard library; --output supports independent replays.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory"
REVIEW = ROOT / "output/part2/milk_inventory/supplement_review"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, list(rows[0]), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def fasta(path):
    records = []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            name, accession = line[1:].split()[:2]
            records.append(dict(name=name, accession=accession, sequence=""))
        elif records:
            records[-1]["sequence"] += line.strip().upper().replace("T", "U")
    assert all(set(r["sequence"]) <= set("ACGU") for r in records)
    return records


def candidates(name, records):
    # Include both possible arms even when another species retained the arm-free name.
    # Never erase numeric locus suffixes or silently choose a species/arm.
    allowed = {name: "same_unprefixed_name"}
    if not re.search(r"-(3p|5p)$", name):
        allowed.update({name + "-3p": "possible_arm", name + "-5p": "possible_arm"})
    return [
        (r, allowed[r["name"].split("-", 1)[1]])
        for r in records
        if "-" in r["name"] and r["name"].split("-", 1)[1] in allowed
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output/part2/milk_inventory/chen_shome_audit",
    )
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    raw = DATA / "chen_shome_followup_20261009"
    paths = [
        REVIEW / "chen_s3_counts.tsv",
        REVIEW / "shome_samples.tsv",
        ROOT / "output/part2/milk_inventory/sequence_comparison/sequence_support.tsv",
        raw / "protocol.json",
        raw / "shome_ena_runs.tsv",
        raw / "shome_analysis.tsv",
    ]
    refs = {}
    for version in ["20", "21", "23_1"]:
        path = DATA / f"references/mirbase{version}_mature.fa"
        paths.append(path)
        refs[version] = fasta(path)
    # Check saved downloads against their retrieval manifests.
    for manifest in sorted(raw.glob("*retrieval.json")):
        paths.append(manifest)
        for row in json.loads(manifest.read_text()):
            if "path" in row:
                path = ROOT / row["path"]
                assert sha(path) == row["sha256"], path
                paths.append(path)
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    existing = {r["sequence_RNA"] for r in table(paths[2])}
    assert len(existing) == 270
    chen = table(REVIEW / "chen_s3_counts.tsv")
    assert len(chen) == 245 and all(r["species"] == "Bos taurus" for r in chen)
    human = {r["sequence"] for r in refs["23_1"] if r["name"].startswith("hsa-")}
    seeds = {s[1:8] for s in human}
    detailed, overview = [], []
    for row in chen:
        matches = candidates(row["original_name"], refs["23_1"])
        bovine = [r for r, rule in matches if r["name"].startswith("bta-")]
        sequences = {r["sequence"] for r in bovine}
        status = (
            "no_current_bovine_name_candidate"
            if not sequences
            else "one_current_bovine_reference_candidate"
            if len(sequences) == 1
            else "multiple_current_bovine_reference_candidates"
        )
        overview.append(
            {
                **row,
                "name_audit_status": status,
                "current_bovine_names": ";".join(sorted(r["name"] for r in bovine)),
                "n_possible_bovine_sequences": len(sequences),
                "n_possible_sequences_in_existing_270": len(sequences & existing),
                "n_all_species_name_candidates": len(matches),
                "historical_mirbase13_mapping": "unresolved_reference_unavailable",
                "added_to_sequence_pool": False,
            }
        )
        for version, records in refs.items():
            for record, rule in candidates(row["original_name"], records):
                sequence = record["sequence"]
                detailed.append(
                    dict(
                        row_id=row["row_id"],
                        original_name=row["original_name"],
                        reference_version=version.replace("_", "."),
                        reference_name=record["name"],
                        accession=record["accession"],
                        reference_sequence=sequence,
                        match_rule=rule,
                        reference_taxon_prefix=record["name"].split("-")[0],
                        reference_human_class=(
                            "exact_human_sequence"
                            if sequence in human
                            else "human_seed_only"
                            if sequence[1:8] in seeds
                            else "no_human_seed_match"
                        ),
                        in_existing_270=sequence in existing,
                        interpretation="name candidate only; not an observed Chen sequence",
                    )
                )
    write(out / "chen_name_audit.tsv", overview)
    write(out / "chen_reference_name_candidates.tsv", detailed)
    # This sensitivity table describes counts of published names, never sequences.
    sensitivity = []
    for threshold in [1, 2, 10, 100]:
        for material in ["mature_milk", "colostrum"]:
            sensitivity.append(
                dict(
                    material=material,
                    minimum_reads=threshold,
                    positive_names=sum(
                        int(r[material + "_reads"]) >= threshold for r in chen
                    ),
                    unit="names per pooled library; exploratory threshold, not validation",
                )
            )
    write(out / "chen_read_thresholds.tsv", sensitivity)
    runs = table(raw / "shome_ena_runs.tsv")
    samples = table(REVIEW / "shome_samples.tsv")
    suffix = dict(
        raw="rawwhole",
        cultured="cultbm",
        sweet="scbm",
        cream="pastcream",
        homogenized="homohtskim",
        heated="rawhtskim",
        pasteurized="pasthomoskim",
    )
    indexed = {r["sample_alias"]: r for r in runs}
    assert len(indexed) == len(runs) == len(samples) == 28
    reconciled = []
    for sample in samples:
        alias = sample["run_label"].lower() + suffix[sample["condition"]]
        run = indexed[alias]
        assert run["tax_id"] == "9913" and run["scientific_name"] == "Bos taurus"
        reconciled.append(
            {
                **sample,
                **run,
                "mapping_rule": "run label plus condition alias",
                "raw_downloaded": False,
                "count_matrix_available": False,
            }
        )
    assert {r["sample_alias"] for r in reconciled} == set(indexed)
    write(out / "shome_archive_samples.tsv", reconciled)
    analyses = table(raw / "shome_analysis.tsv")
    assert not analyses
    summary = dict(
        chen=dict(
            published_names=245,
            statuses=dict(Counter(r["name_audit_status"] for r in overview)),
            names_with_any_bovine_candidate_overlap=sum(
                int(r["n_possible_sequences_in_existing_270"]) > 0 for r in overview
            ),
            missing_current_names_all_species=[
                r["original_name"]
                for r in overview
                if not r["n_all_species_name_candidates"]
            ],
            historical_reference_available=False,
            sequence_pool_unchanged=270,
            read_thresholds=sensitivity,
        ),
        shome=dict(
            runs=len(runs),
            matched_supplement_samples=len(reconciled),
            taxon="Bos taurus",
            groups=dict(Counter(r["condition"] for r in reconciled)),
            archive_read_count=sum(int(r["read_count"]) for r in runs),
            compressed_fastq_bytes=sum(
                sum(int(v) for v in r["fastq_bytes"].split(";") if v) for r in runs
            ),
            analysis_records=len(analyses),
            submitted_files_present=any(r["submitted_ftp"] for r in runs),
            library_layouts=sorted({r["library_layout"] for r in runs}),
            files_per_run=sorted({len(r["fastq_ftp"].split(";")) for r in runs}),
            raw_downloaded=False,
            caveat="No count matrix located in reviewed supplements or ENA analysis listing; absence elsewhere not established. PAIRED metadata with one FASTQ/run needs inspection before preprocessing.",
        ),
    )
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    names = [
        "chen_name_audit.tsv",
        "chen_reference_name_candidates.tsv",
        "chen_read_thresholds.tsv",
        "shome_archive_samples.tsv",
        "summary.json",
    ]
    (out / "manifest.json").write_text(
        json.dumps(
            dict(
                inputs=inputs,
                script_sha256=sha(Path(__file__)),
                outputs={n: sha(out / n) for n in names},
            ),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

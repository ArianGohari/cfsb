"""Join published name records with provenance; keep reference versions explicit.

Ali is a provisional accession-based comparison against miRBase 23.1, not a
reconstruction of the study's 22.1 reference or its sequenced molecules.
"""

from pathlib import Path
from collections import defaultdict, Counter
import csv, json, hashlib

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "output/part2/milk_inventory/published_lists"
REF = ROOT / "data/datasets/milk_mirna_inventory/references/mirbase23_1_mature.fa"
BASE = ROOT / "output/part2/milk_inventory/sequence_comparison"
ALI = ROOT / "output/part2/milk_inventory/ali_review/table3_mature.tsv"
DOIS = {
    "li2016": "10.1371/journal.pone.0154129",
    "krupova2023": "10.1038/s41597-023-02347-0",
    "ali2026": "10.1016/j.idairyj.2025.106422",
}


def read(p):
    with p.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write(name, rows):
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    references = {}
    key = None
    for line in REF.read_text().splitlines():
        if line.startswith(">"):
            parts = line[1:].split()
            key = (parts[0], parts[1])
            assert key not in references
            references[key] = ""
        elif line.strip():
            references[key] += line.strip().upper().replace("T", "U")
    bovine = defaultdict(list)
    human = defaultdict(list)
    seeds = defaultdict(list)
    for (name, acc), seq in references.items():
        if name.startswith("bta-"):
            bovine[acc].append((name, seq))
        elif name.startswith("hsa-"):
            human[seq].append(name)
            seeds[seq[1:8]].append(name)
    baseline = read(BASE / "sequence_support.tsv")
    baseline_seqs = {r["sequence_RNA"] for r in baseline}
    assert len(baseline_seqs) == 270
    prior_names = defaultdict(set)
    for r in baseline:
        for name in r["names"].split(";"):
            prior_names[name].add(r["sequence_RNA"])
    records = []
    for row in read(BASE / "known_annotation_comparison.tsv"):
        records.append(
            dict(
                study=row["study"],
                doi=DOIS[row["study"]],
                original_name=row["original_name"],
                accession=row["source_reference_accession"],
                reference_sequence=row["sequence_RNA"],
                sequence_origin=row["sequence_origin"],
                reference_status="Historische Originalzuordnung beibehalten",
                qualifies=row["qualifies"],
                reads="",
                human_class=row["human_class"],
                source_path=row["source_path"],
                source_locator=row["source_sheet"] + ": Zeile " + row["source_row"],
            )
        )
    ali = []
    for row in read(ALI):
        matches = bovine[row["accession"]]
        seqs = {seq for _, seq in matches}
        seq = next(iter(seqs)) if len(seqs) == 1 else ""
        cls = (
            (
                "exact_human_sequence"
                if human[seq]
                else "human_seed_only"
                if seeds[seq[1:8]]
                else "no_human_seed_match"
            )
            if seq
            else "unresolved"
        )
        same_name = prior_names[row["name"]]
        rec = dict(
            original_name=row["name"],
            accession=row["accession"],
            reads=int(row["reads"]),
            rpm=row["rpm"],
            reference_sequence=seq,
            current_bovine_names=";".join(sorted(name for name, _ in matches)),
            mapping_status="Eine Sequenz zur Accession"
            if seq
            else "Keine eindeutige Sequenz zur Accession",
            human_class=cls,
            human_exact_names=";".join(sorted(human[seq])) if seq else "",
            human_seed_names=";".join(sorted(seeds[seq[1:8]])) if seq else "",
            strict_gt1=int(row["reads"]) > 1,
            exact_sequence_in_baseline=seq in baseline_seqs if seq else False,
            same_name_in_baseline=bool(same_name),
            different_sequence_under_same_name=bool(
                seq and same_name and seq not in same_name
            ),
            pdf_page=row["pdf_page"],
        )
        ali.append(rec)
        records.append(
            dict(
                study="ali2026",
                doi=DOIS["ali2026"],
                original_name=row["name"],
                accession=row["accession"],
                reference_sequence=seq,
                sequence_origin="miRBase23.1_accession_lookup",
                reference_status="Vorläufig: Studie verwendete 22.1, aktuelle Zuordnung 23.1",
                qualifies="provisional_gt1"
                if rec["strict_gt1"] and seq
                else "unresolved"
                if not seq
                else "single_read_only",
                reads=rec["reads"],
                human_class=cls,
                source_path="data/sources/ali_2026_infant_formula_mirnas/ali_2026_infant_formula_mirnas.pdf",
                source_locator="Tabelle 3; PDF S. " + row["pdf_page"],
            )
        )
    write("name_records.tsv", records)
    write("ali_reference_comparison.tsv", ali)
    strict = [r for r in ali if r["strict_gt1"] and r["reference_sequence"]]
    summary = {
        "records_by_study": dict(Counter(r["study"] for r in records)),
        "ali_rows": len(ali),
        "ali_mapped_rows": sum(bool(r["reference_sequence"]) for r in ali),
        "ali_unique_mapped_sequences": len(
            {r["reference_sequence"] for r in ali if r["reference_sequence"]}
        ),
        "ali_strict_gt1_rows": len(strict),
        "ali_strict_classes": dict(Counter(r["human_class"] for r in strict)),
        "ali_strict_exact_sequence_overlap_with_baseline": sum(
            r["exact_sequence_in_baseline"] for r in strict
        ),
        "ali_strict_sequences_absent_from_baseline": sum(
            not r["exact_sequence_in_baseline"] for r in strict
        ),
        "ali_strict_same_name_different_sequence": sum(
            r["different_sequence_under_same_name"] for r in strict
        ),
        "unresolved_names": [
            r["original_name"] for r in ali if not r["reference_sequence"]
        ],
        "scope": "Provisional reference comparison. Original 270-sequence inventory and its paper counts are unchanged. No new candidate selected.",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [
        REF,
        BASE / "sequence_support.tsv",
        BASE / "known_annotation_comparison.tsv",
        ALI,
        Path(__file__),
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
                "outputs": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted(OUT.iterdir())
                    if p.name != "manifest.json"
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

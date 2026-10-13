#!/usr/bin/env python3
"""Offline accession and sequence audit; no database absence implies invalidity."""

import argparse
import csv
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory"
REF = DATA / "references"
PRIORITY = (
    ROOT
    / "output/part2/milk_inventory/sequence_comparison/annotation_review_priority.tsv"
)


class Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], [], None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        if tag in ("td", "th"):
            self.cell = ""

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(self.cell.split()))
            self.cell = None
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def fasta(path):
    records = []
    for block in path.read_text().split(">")[1:]:
        header, *lines = block.splitlines()
        seq = "".join(lines).upper().replace("T", "U")
        assert seq and set(seq) <= set("ACGU"), path
        records.append((header, seq))
    return records


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = False

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(" ".join(data.split()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output/part2/milk_inventory/annotation_audit",
    )
    args = ap.parse_args()
    inputs = [
        PRIORITY,
        REF / "mirbase23_1_mature.fa",
        REF / "mirgenedb3_bta_20261009.html",
    ]
    for item in json.loads((DATA / "annotation_retrieval_20261009.json").read_text()):
        if "sha256" in item:
            assert (
                hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest()
                == item["sha256"]
            )
    db = {}
    for species in ("bta", "hsa"):
        db[species] = []
        for arm in (5, 3):
            path = REF / f"mirgenedb3_{species}_{arm}p_20261009.fa"
            inputs.append(path)
            db[species].extend(fasta(path))
    parser = Tables()
    parser.feed(inputs[2].read_text())
    loci = [r for r in parser.rows if r[0].startswith("Bta-")]
    assert len(loci) == 406
    mb = fasta(REF / "mirbase23_1_mature.fa")
    result, links, hairpins = [], [], []
    for row in csv.DictReader(PRIORITY.open(), delimiter="\t"):
        seq = row["sequence_RNA"]
        names = set(row["current_bovine_exact_names"].split(";"))
        accessions = {h.split()[1] for h, s in mb if h.split()[0] in names and s == seq}
        assert accessions
        matched = [r for r in loci if accessions.intersection(r[4:6])]
        exact = [h for h, s in db["bta"] if s == seq]
        base = dict(
            candidate=row["names"],
            sequence_RNA=seq,
            seed_2_8=seq[1:8],
            mirbase_accessions=";".join(sorted(accessions)),
            mirgenedb_accession_loci=";".join(r[0] for r in matched),
            mirgenedb_exact_sequences=";".join(exact),
            human_mirgenedb_exact=";".join(h for h, s in db["hsa"] if s == seq),
            human_mirgenedb_seed=";".join(
                h for h, s in db["hsa"] if s[1:8] == seq[1:8]
            ),
            status="exact_sequence"
            if exact
            else "accession_with_sequence_difference"
            if matched
            else "no_accession_or_exact_sequence_match",
        )
        result.append(base)
        for acc in sorted(accessions):
            path = REF / f"mirbase_{acc}_20261009.html"
            inputs.append(path)
            page = path.read_text()
            p = Tables()
            p.feed(page)
            fields = {r[0]: " | ".join(r[1:]) for r in p.rows if len(r) > 1}
            for precursor in sorted(set(re.findall(r"/hairpin/(MI[0-9]+)", page))):
                hp = REF / f"mirbase_{precursor}_20261009.html"
                inputs.append(hp)
                hp_html = hp.read_text()
                text = Text()
                text.feed(hp_html)
                parts = text.parts
                confidence = parts[parts.index("Annotation confidence") + 1]
                hairpins.append(
                    dict(
                        candidate=row["names"],
                        mature_accession=acc,
                        precursor_accession=precursor,
                        annotation_confidence=confidence,
                        reference_pmids=";".join(
                            sorted(set(re.findall(r"pubmed/(\d+)", hp_html)))
                        ),
                        source=str(hp.relative_to(ROOT)),
                    )
                )
            for locus in matched:
                if acc not in locus[4:6]:
                    continue
                arm = 5 if acc == locus[4] else 3
                alternatives = [
                    (h, s)
                    for h, s in db["bta"]
                    if h.rstrip("*") == f"{locus[0]}_{arm}p"
                ]
                assert alternatives, (locus, arm)
                for header, alt in alternatives:
                    links.append(
                        dict(
                            candidate=row["names"],
                            accession=acc,
                            mirgenedb_id=header,
                            original_sequence=seq,
                            curated_sequence=alt,
                            same_sequence=seq == alt,
                            same_seed=seq[1:8] == alt[1:8],
                            star=header.endswith("*"),
                            curated_seed_human_matches=";".join(
                                h for h, s in db["hsa"] if s[1:8] == alt[1:8]
                            ),
                        )
                    )
            base.setdefault("mirbase_evidence", [])
            base["mirbase_evidence"].append(
                acc + ": " + fields.get("Evidence", "not parsed")
            )
        base["mirbase_evidence"] = ";".join(base["mirbase_evidence"])
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, rows in [
        ("candidates.tsv", result),
        ("curated_sequence_links.tsv", links),
        ("hairpin_evidence.tsv", hairpins),
    ]:
        with (args.output / filename).open("w", newline="") as f:
            w = csv.DictWriter(
                f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n"
            )
            w.writeheader()
            w.writerows(rows)
    summary = dict(
        candidates=len(result),
        bovine_curated_loci=len(loci),
        exact_sequence_candidates=sum(r["status"] == "exact_sequence" for r in result),
        accession_only_candidates=sum(
            r["status"] == "accession_with_sequence_difference" for r in result
        ),
        unmatched_candidates=sum(
            r["status"] == "no_accession_or_exact_sequence_match" for r in result
        ),
        human_seed_matches=sum(bool(r["human_mirgenedb_seed"]) for r in result),
        scope="Database cross-check; no FASTQ, processing, AGO-loading or oral uptake validation",
    )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(set(inputs))
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

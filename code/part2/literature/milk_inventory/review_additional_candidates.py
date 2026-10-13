"""Replay the bounded candidate round from saved searches and editable notes."""

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import yaml
from scan_human_seeds import fasta, sites

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "output/part2/milk_inventory"
DATA = ROOT / "data/datasets/milk_mirna_inventory/bounded_candidate_search_20261010"
OUT = BASE / "additional_candidates"


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write(name, rows):
    with (OUT / name).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def fasta_records(path):
    header, seq = None, []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if header:
                yield header, "".join(seq)
            header, seq = line[1:], []
        else:
            seq.append(line.strip())
    if header:
        yield header, "".join(seq)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [
        DATA / "selected_for_review.json",
        DATA / "pool.tsv",
        DATA / "protocol.json",
        BASE / "human_seed_screen/transcripts.tsv",
        Path(__file__),
        Path(__file__).with_name("scan_human_seeds.py"),
        ROOT
        / "data/datasets/milk_mirna_inventory/human_target_reference/gencode.v48.pc_transcripts.fa.gz",
    ]
    selected = json.loads(inputs[0].read_text())
    pool = read(inputs[1])
    byname = {r["miRNA_names"]: r for r in pool}
    candidates = []
    for entry in selected:
        note = ROOT / entry["source_note"]
        inputs.append(note)
        props = yaml.safe_load(note.read_text().split("---", 2)[1])
        candidates.append(
            {
                "candidate": props["Zusatzkandidat"],
                "sequence_RNA": props["Inventarsequenz"],
                "targets": props["Zusatz-Targets"],
                "source_note": entry["source_note"],
                "doi": props["DOI"],
                "review_level": props["Lesestatus"],
                "limits": props["Evidenzgrenze"],
                "reason": props["Prüfgrund"],
            }
        )
    assert len(candidates) == 5
    assert all(
        c["sequence_RNA"] == byname[c["candidate"]]["sequence_RNA"] for c in candidates
    )
    refs = {}
    for species in ("bta", "hsa"):
        records = []
        for arm in ("5p", "3p"):
            path = (
                ROOT
                / f"data/datasets/milk_mirna_inventory/references/mirgenedb3_{species}_{arm}_20261009.fa"
            )
            inputs.append(path)
            records.extend(fasta_records(path))
        refs[species] = records
    tx = {r["transcript_id"]: r for r in read(inputs[3])}
    examined, hits = [], []
    for header, sequence in fasta():
        tid = header.split("|")[0]
        if tid not in tx:
            continue
        row = tx[tid]
        matching = [c for c in candidates if row["gene"] in c["targets"]]
        if not matching:
            continue
        start, end = int(row["utr_start"]), int(row["utr_end"])
        utr = sequence[start - 1 : end]
        assert len(utr) == int(row["utr_length"])
        for c in matching:
            key = {"candidate": c["candidate"], "gene": row["gene"], "transcript": tid}
            found = sites(utr, c["sequence_RNA"])
            examined.append({**key, "utr_length": len(utr), "site_count": len(found)})
            for a, b, kind in found:
                hits.append(
                    {
                        **key,
                        "site_type": kind,
                        "utr_start_1based": a + 1,
                        "utr_end_1based": b,
                        "site_DNA": utr[a:b],
                        "flank_DNA": utr[max(0, a - 15) : b + 15],
                    }
                )
    summaries = []
    for c in candidates:
        seq = c["sequence_RNA"]
        exact_bta = ";".join(h for h, s in refs["bta"] if s == seq)
        exact_hsa = ";".join(h for h, s in refs["hsa"] if s == seq)
        for gene in c["targets"]:
            e = [
                r
                for r in examined
                if r["candidate"] == c["candidate"] and r["gene"] == gene
            ]
            h = [
                r
                for r in hits
                if r["candidate"] == c["candidate"] and r["gene"] == gene
            ]
            summaries.append(
                {
                    "candidate": c["candidate"],
                    "sequence_RNA": seq,
                    "gene": gene,
                    "milk_papers": byname[c["candidate"]]["n_papers"],
                    "human_class": byname[c["candidate"]]["human_class"],
                    "human_seed_names": byname[c["candidate"]]["human_seed_names"],
                    "mirgenedb_bovine_exact": exact_bta,
                    "mirgenedb_human_exact": exact_hsa,
                    "eligible_transcripts": len(e),
                    "transcripts_with_sites": sum(int(r["site_count"]) > 0 for r in e),
                    "site_types": ";".join(sorted({r["site_type"] for r in h})),
                    "review_level": c["review_level"],
                    "doi": c["doi"],
                    "limits": c["limits"],
                    "source_note": c["source_note"],
                }
            )
    write("target_pairs.tsv", summaries)
    write("sites.tsv", hits)
    write("examined_transcripts.tsv", examined)
    selected_names = {c["candidate"] for c in candidates}
    for row in pool:
        row["review_this_round"] = (
            "Vertieft"
            if row["miRNA_names"] in selected_names
            else "Nur Suchpool; keine vollständige Einzelprüfung"
            if row["round_status"] == "Zur begrenzten Literatursuche"
            else row["round_status"]
        )
    write("pool_status.tsv", pool)
    records = []
    for path in sorted(DATA.glob("batch_*.json")):
        inputs.append(path)
        raw = json.loads(path.read_text())
        result = raw.get("structuredContent") or json.loads(raw["content"][0]["text"])
        for i, paper in enumerate(result["papers"], 1):
            doi = (paper.get("doi") or "").lower()
            text = (paper["title"] + " " + (paper.get("abstract") or "")).lower()
            names = [
                r["miRNA_names"]
                for r in pool
                if re.search(
                    re.escape(r["miRNA_names"].removeprefix("bta-").lower())
                    + r"(?![a-z0-9])",
                    text,
                )
            ]
            records.append(
                {
                    "batch": path.stem,
                    "rank": i,
                    "title": paper["title"],
                    "doi_as_returned": doi,
                    "candidate_name_mentions": ";".join(names),
                    "reviewed_source": doi in {c["doi"].lower() for c in candidates},
                    "dedup_key": doi
                    or "title:" + re.sub(r"\W+", "", paper["title"].lower()),
                }
            )
    write("search_records.tsv", records)
    summary = {
        "pool": len(pool),
        "eligible_for_search": sum(
            r["round_status"] == "Zur begrenzten Literatursuche" for r in pool
        ),
        "deep_review_candidates": len(candidates),
        "search_records": len(records),
        "distinct_doi_or_normalized_title_records": len(
            {r["dedup_key"] for r in records}
        ),
        "per_batch": dict(Counter(r["batch"] for r in records)),
        "candidate_target_pairs": len(summaries),
        "positive_pairs": sum(int(r["transcripts_with_sites"]) > 0 for r in summaries),
        "scope": "Bounded scouting: batch 1 reaches cap 50, not exhaustive. Exact mature sequences and canonical sites only; no functional human validation.",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    manifest = {
        "inputs": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in inputs
        }
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for r in summaries:
        print(
            r["candidate"],
            r["gene"],
            str(r["transcripts_with_sites"]) + "/" + str(r["eligible_transcripts"]),
            r["site_types"],
            "MirGeneDB:",
            r["mirgenedb_bovine_exact"],
        )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Descriptive PFKL sequence controls for the preselected miR-6517 hypothesis."""

import argparse
import csv
import hashlib
import itertools
import json
import re
from pathlib import Path

from scan_human_seeds import ROOT, DATA, fasta, sites, write_tsv

PROTOCOL = (
    ROOT / "data/datasets/milk_mirna_inventory/pfkl_followup_20261010/protocol.json"
)
TRANSCRIPTS = ROOT / "output/part2/milk_inventory/human_seed_screen/transcripts.tsv"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gc(seq):
    return (seq.count("G") + seq.count("C")) / len(seq)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--output",
        type=Path,
        default=ROOT / "output/part2/milk_inventory/pfkl_followup",
    )
    out = ap.parse_args().output
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(PROTOCOL.read_text())
    mirna = protocol["sequence"]
    selected = list(csv.DictReader(TRANSCRIPTS.open(), delimiter="\t"))
    representatives = {}
    for row in sorted(
        selected, key=lambda r: (r["mane_select"] != "True", r["transcript_id"])
    ):
        representatives.setdefault(row["gene_id"], row["transcript_id"])
    tids = set(representatives.values())
    basic = {r["transcript_id"]: r for r in selected}
    ref_id = "ENST00000349048.9"
    pfkl, references = [], []
    for header, seq in fasta():
        parts = header.split("|")
        tid, gene = parts[0], parts[5]
        match = re.search(r"\|UTR3:(\d+)-(\d+)\|", header)
        if not match:
            if gene == "PFKL":
                pfkl.append(
                    dict(
                        transcript=tid,
                        basic_scope=tid in basic,
                        utr_length=0,
                        sites=[],
                        sequence="",
                    )
                )
            continue
        start, end = map(int, match.groups())
        utr = seq[start - 1 : end]
        if gene == "PFKL":
            pfkl.append(
                dict(
                    transcript=tid,
                    basic_scope=tid in basic,
                    mane_select=basic.get(tid, {}).get(
                        "mane_select", "outside_basic_scope"
                    ),
                    transcript_utr_start=start,
                    utr_length=len(utr),
                    gc=gc(utr),
                    sites=sites(utr, mirna),
                    sequence=utr,
                )
            )
        if tid in tids:
            assert digest_sequence(utr) == basic[tid]["utr_sha256"]
            references.append((gene, parts[1], tid, utr))
    reference = next(r for r in pfkl if r["transcript"] == ref_id)
    utr = reference["sequence"]
    hits = reference["sites"]
    assert hits == [(478, 485, "7mer-A1")], hits
    assert utr[478:485] == "ACCCTGA"
    contexts = []
    for a, b, kind in hits:
        left, right = utr[max(0, a - 30) : a], utr[b : b + 30]
        flank = left + right
        contexts.append(
            dict(
                transcript=ref_id,
                site_type=kind,
                start_1based=a + 1,
                end_1based=b,
                site=utr[a:b],
                left30=left,
                right30=right,
                flank_nt=len(flank),
                flank_AU_fraction=1 - gc(flank),
                nt_after_site=len(utr) - b,
                utr_AU_fraction=1 - gc(utr),
            )
        )
    permutations = sorted({"".join(p) for p in itertools.permutations(mirna[1:8])})
    controls = []
    for seed in permutations:
        if seed == mirna[1:8]:
            continue
        found = sites(utr, mirna[0] + seed + mirna[8:])
        controls.append(
            dict(
                seed=seed,
                n_sites=len(found),
                any_site=bool(found),
                site_types=";".join(sorted({h[2] for h in found})),
            )
        )
    matched = []
    for gene, gid, tid, seq in references:
        if gene == "PFKL":
            continue
        if (
            0.8 * len(utr) <= len(seq) <= 1.2 * len(utr)
            and abs(gc(seq) - gc(utr)) <= 0.05
        ):
            found = sites(seq, mirna)
            matched.append(
                dict(
                    gene=gene,
                    gene_id=gid,
                    transcript=tid,
                    utr_length=len(seq),
                    gc=gc(seq),
                    n_sites=len(found),
                    any_site=bool(found),
                )
            )
    assert matched
    write_tsv(out / "site_context.tsv", contexts, list(contexts[0]))
    write_tsv(out / "seed_controls.tsv", controls, list(controls[0]))
    write_tsv(out / "matched_utr_controls.tsv", matched, list(matched[0]))
    (out / "pfkl_transcripts.json").write_text(json.dumps(pfkl, indent=2) + "\n")
    summary = dict(
        candidate=protocol["candidate"],
        target="PFKL",
        pfkl_pc_fasta_records=len(pfkl),
        reference={k: v for k, v in reference.items() if k != "sequence"},
        controls_with_sites=sum(r["any_site"] for r in controls),
        controls_total=len(controls),
        control_fraction=sum(r["any_site"] for r in controls) / len(controls),
        matched_utr_with_sites=sum(r["any_site"] for r in matched),
        matched_utr_total=len(matched),
        matched_utr_fraction=sum(r["any_site"] for r in matched) / len(matched),
        interpretation="Descriptive reference fractions, not p-values or functional target probabilities; candidate and gene selected beforehand from literature.",
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    inputs = [
        PROTOCOL,
        TRANSCRIPTS,
        DATA / "gencode.v48.pc_transcripts.fa.gz",
        Path(__file__),
        Path(__file__).with_name("scan_human_seeds.py"),
    ]
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {str(p.relative_to(ROOT)): digest(p) for p in inputs},
                "outputs": {
                    p.name: digest(p)
                    for p in sorted(out.iterdir())
                    if p.name != "manifest.json"
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


def digest_sequence(seq):
    return hashlib.sha256(seq.encode()).hexdigest()


if __name__ == "__main__":
    main()

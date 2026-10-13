#!/usr/bin/env python3
"""CASP3 isoforms and descriptive controls, using the prior PFKL rules."""

import csv
import itertools
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from scan_human_seeds import ROOT, DATA, fasta, sites, write_tsv
from review_pfkl import digest, digest_sequence, gc, TRANSCRIPTS

RAW = ROOT / "data/datasets/milk_mirna_inventory/casp3_followup_20261010"
OUT = ROOT / "output/part2/milk_inventory/casp3_followup"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = json.loads((RAW / "protocol.json").read_text())
    mirna, variant = p["sequence"], p["figure2_mature_sequence"]
    assert variant.startswith(mirna) and mirna[1:8] == variant[1:8]
    basic = {
        r["transcript_id"]: r
        for r in csv.DictReader(TRANSCRIPTS.open(), delimiter="\t")
    }
    reps = {}
    for row in sorted(
        basic.values(), key=lambda r: (r["mane_select"] != "True", r["transcript_id"])
    ):
        reps.setdefault(row["gene_id"], row["transcript_id"])
    tids = set(reps.values())
    transcripts, references, contexts = [], [], []
    fragment = p["figure3_casp3_fragment_RNA"].replace("U", "T")
    for header, seq in fasta():
        parts = header.split("|")
        tid, gene = parts[0], parts[5]
        match = re.search(r"\|UTR3:(\d+)-(\d+)\|", header)
        start, end = map(int, match.groups()) if match else (0, 0)
        utr = seq[start - 1 : end] if match else ""
        if tid in tids:
            assert digest_sequence(utr) == basic[tid]["utr_sha256"]
            references.append((gene, tid, utr))
        if gene != "CASP3":
            continue
        found = sites(utr, mirna)
        assert found == sites(utr, variant)
        cds_start, cds_end = map(int, re.search(r"\|CDS:(\d+)-(\d+)", header).groups())
        distance, position, window = min(
            (
                sum(a != b for a, b in zip(fragment, seq[i : i + len(fragment)])),
                i,
                seq[i : i + len(fragment)],
            )
            for i in range(len(seq) - len(fragment) + 1)
        )
        transcripts.append(
            dict(
                transcript=tid,
                basic_scope=tid in basic,
                mane=basic.get(tid, {}).get("mane_select") == "True",
                header=header,
                cds_start=cds_start,
                cds_end=cds_end,
                cds_nt=cds_end - cds_start + 1,
                utr_length=len(utr),
                gc=gc(utr) if utr else None,
                sites=found,
                sequence=utr,
                figure_fragment_in_transcript=fragment in seq,
                figure_fragment_in_utr=fragment in utr,
                nearest_fragment=dict(
                    mismatches=distance, start_1based=position + 1, sequence=window
                ),
                full_transcript_sites=sites(seq, mirna),
            )
        )
        for a, b, kind in found:
            flank = utr[max(0, a - 30) : a] + utr[b : b + 30]
            contexts.append(
                dict(
                    transcript=tid,
                    site_type=kind,
                    start_1based=a + 1,
                    end_1based=b,
                    site=utr[a:b],
                    preceding_base=utr[a - 1 : a] if a else "",
                    left30=utr[max(0, a - 30) : a],
                    right30=utr[b : b + 30],
                    flank_nt=len(flank),
                    flank_AU_fraction=1 - gc(flank),
                    nt_after_site=len(utr) - b,
                )
            )
    seeds = sorted(
        {"".join(x) for x in itertools.permutations(mirna[1:8])} - {mirna[1:8]}
    )
    mane = next(r for r in transcripts if r["mane"])
    hit = next(
        r
        for r in sorted(transcripts, key=lambda r: r["transcript"])
        if r["basic_scope"] and r["sites"]
    )
    checks, control_rows, matched_rows = [], [], []
    for label, ref in [("MANE", mane), ("postselected_hit_isoform", hit)]:
        utr = ref["sequence"]
        controls = []
        for seed in seeds:
            n = len(sites(utr, mirna[0] + seed + mirna[8:]))
            row = dict(
                reference=label, transcript=ref["transcript"], seed=seed, n_sites=n
            )
            control_rows.append(row)
            controls.append(n)
        matched = []
        for gene, tid, seq in references:
            if gene == "CASP3":
                continue
            if (
                0.8 * len(utr) <= len(seq) <= 1.2 * len(utr)
                and abs(gc(seq) - gc(utr)) <= 0.05
            ):
                n = len(sites(seq, mirna))
                matched.append(n)
                matched_rows.append(
                    dict(
                        reference=label,
                        gene=gene,
                        transcript=tid,
                        utr_length=len(seq),
                        gc=gc(seq),
                        n_sites=n,
                    )
                )
        checks.append(
            dict(
                reference=label,
                transcript=ref["transcript"],
                actual_sites=len(ref["sites"]),
                controls_total=len(controls),
                controls_with_sites=sum(n > 0 for n in controls),
                matched_total=len(matched),
                matched_with_sites=sum(n > 0 for n in matched),
            )
        )
    hpa = []
    for e in ET.parse(RAW / "CASP3_HPA.xml").getroot().iter("rnaExpression"):
        if e.get("assayType") not in {"consensusTissue", "immuneCell"}:
            continue
        for d in e.findall("data"):
            tissue = d.findtext("tissue") or d.findtext("immuneCell") or ""
            if (
                tissue not in {"Heart muscle", "Adipose tissue"}
                and "monocyte" not in tissue.lower()
            ):
                continue
            level = d.find("level[@type='normalizedRNAExpression']")
            hpa.append(
                dict(
                    assay=e.get("assayType"),
                    tissue_or_cell=tissue,
                    value=level.get("expRNA"),
                    unit=level.get("unitRNA"),
                )
            )
    for name, rows in [
        ("site_context.tsv", contexts),
        ("seed_controls.tsv", control_rows),
        ("matched_utr_controls.tsv", matched_rows),
        ("hpa_context.tsv", hpa),
    ]:
        write_tsv(OUT / name, rows, list(rows[0]))
    (OUT / "transcripts.json").write_text(json.dumps(transcripts, indent=2) + "\n")
    summary = dict(
        candidate=p["candidate"],
        target=p["target"],
        inventory_sequence=mirna,
        figure_sequence=variant,
        same_seed=True,
        mimic_sequence_confirmed=False,
        pc_fasta_records=len(transcripts),
        basic_records=sum(r["basic_scope"] for r in transcripts),
        basic_with_utr_sites=sum(
            r["basic_scope"] and bool(r["sites"]) for r in transcripts
        ),
        figure_fragment_transcript_matches=sum(
            r["figure_fragment_in_transcript"] for r in transcripts
        ),
        checks=checks,
        limits="Descriptive controls, no p-values; hit isoform selected after seeing sites, not substituted for MANE. HPA is gene-level context, not isoform or miRNA evidence.",
    )
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    inputs = [
        RAW / "protocol.json",
        RAW / "CASP3_HPA.xml",
        TRANSCRIPTS,
        DATA / "gencode.v48.pc_transcripts.fa.gz",
        Path(__file__),
        Path(__file__).with_name("review_pfkl.py"),
        Path(__file__).with_name("scan_human_seeds.py"),
        ROOT / "data/sources/yak_2022_mir2285o_caspase3/figure2.jpg",
        ROOT / "data/sources/yak_2022_mir2285o_caspase3/figure3.jpg",
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {str(x.relative_to(ROOT)): digest(x) for x in inputs},
                "outputs": {
                    x.name: digest(x)
                    for x in sorted(OUT.iterdir())
                    if x.name != "manifest.json"
                },
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Reproducible canonical seed-site screen; no functional targeting scores."""

import argparse, csv, gzip, hashlib, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory/human_target_reference"
AUDIT = ROOT / "output/part2/milk_inventory/annotation_audit"
DEFAULT_OUT = ROOT / "output/part2/milk_inventory/human_seed_screen"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_tsv(p):
    return list(csv.DictReader(p.open(), delimiter="\t"))


def write_tsv(p, rows, fields):
    with p.open("w") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def rc(s):
    return s.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def positions(seq, motif):
    start = 0
    while (pos := seq.find(motif, start)) >= 0:
        yield pos
        start = pos + 1


def sites(seq, mirna):
    """Zero-based half-open mRNA intervals, strongest class per overlapping seed."""
    mirna = mirna.replace("U", "T")
    m8 = rc(mirna[1:8])
    a1 = rc(mirna[1:7]) + "A"
    found = []
    for p in positions(seq, m8):
        has_a = seq[p + 7 : p + 8] == "A"
        found.append((p, p + (8 if has_a else 7), "8mer" if has_a else "7mer-m8"))
    for p in positions(seq, a1):
        if p > 0 and seq[p - 1 : p + 6] == m8:
            continue
        found.append((p, p + 7, "7mer-A1"))
    return sorted(found)


def annotations():
    tx = {}
    exonlen = Counter()
    utrs = defaultdict(list)
    cds = defaultdict(list)
    stops = defaultdict(list)
    with gzip.open(DATA / "gencode.v48.basic.annotation.gtf.gz", "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            chrom, _, kind, start, end, _, strand, _, attrs = line.rstrip().split("\t")
            if kind not in {"transcript", "exon", "UTR", "CDS", "stop_codon"}:
                continue
            if chrom not in {"chr" + str(i) for i in range(1, 23)} | {"chrX", "chrY"}:
                continue
            d = dict(re.findall(r'(\w+) "([^"]+)";', attrs))
            tid = d.get("transcript_id")
            if d.get("transcript_type") != "protein_coding":
                continue
            if kind == "transcript":
                tx[tid] = dict(
                    gene_id=d["gene_id"],
                    gene=d["gene_name"],
                    chromosome=chrom,
                    strand=strand,
                    mane_select="MANE_Select" in re.findall(r'tag "([^"]+)"', attrs),
                )
            elif kind == "exon":
                exonlen[tid] += int(end) - int(start) + 1
            elif kind == "UTR":
                utrs[tid].append((int(start), int(end)))
            elif kind == "CDS":
                cds[tid].append((int(start), int(end)))
            elif kind == "stop_codon":
                stops[tid].append((int(start), int(end)))
    for tid, m in tx.items():
        ranges = cds[tid]
        assert ranges, tid
        boundary = (
            max(b for a, b in ranges)
            if m["strand"] == "+"
            else min(a for a, b in ranges)
        )
        three_prime = [
            (a, b)
            for a, b in utrs[tid]
            if (a > boundary if m["strand"] == "+" else b < boundary)
        ]
        # GENCODE GTF UTR features can include the separately annotated stop codon;
        # FASTA UTR3 begins after it. Remove actual overlap, including split codons.
        m["gtf_stop_overlap"] = sum(
            max(0, min(b, d) - max(a, c) + 1)
            for a, b in three_prime
            for c, d in stops[tid]
        )
        m["gtf_utr3_length"] = (
            sum(b - a + 1 for a, b in three_prime) - m["gtf_stop_overlap"]
        )
        m["exon_length"] = exonlen[tid]
    return tx


def fasta():
    header = None
    seq = []
    with gzip.open(DATA / "gencode.v48.pc_transcripts.fa.gz", "rt") as f:
        for line in f:
            if line.startswith(">"):
                if header:
                    yield header, "".join(seq)
                header = line[1:].strip()
                seq = []
            else:
                seq.append(line.strip())
        if header:
            yield header, "".join(seq)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads((DATA / "scan_protocol.json").read_text())
    retrieval = json.loads((DATA / "retrieval.json").read_text())
    for row in retrieval["files"]:
        assert sha(DATA / row["file"]) == row["sha256"]
    candidates = [
        dict(
            candidate=r["candidate"],
            variant="inventory_reference",
            sequence_RNA=r["sequence_RNA"],
        )
        for r in read_tsv(AUDIT / "candidates.tsv")
    ]
    for r in read_tsv(AUDIT / "curated_sequence_links.tsv"):
        if (
            r["candidate"] in {"bta-miR-2285k", "bta-miR-6119-3p"}
            and r["original_sequence"] != r["curated_sequence"]
        ):
            c = dict(
                candidate=r["candidate"],
                variant="MirGeneDB_end_variant",
                sequence_RNA=r["curated_sequence"],
            )
            if c not in candidates:
                candidates.append(c)
    assert len(candidates) == 18
    for c in candidates:
        c["seed_2_8"] = c["sequence_RNA"][1:8]
    write_tsv(out / "candidates.tsv", candidates, list(candidates[0]))
    tx = annotations()
    seen = set()
    tested = []
    excluded = []
    all_genes = set()
    gene_hits = defaultdict(set)
    counts = defaultdict(Counter)
    hit_tx = defaultdict(set)
    pair_tx = defaultdict(list)
    pair_hits = defaultdict(list)
    pairs = {tuple(p) for p in protocol["literature_pairs"]}
    fields = [
        "candidate",
        "variant",
        "gene",
        "gene_id",
        "transcript_id",
        "mane_select",
        "site_type",
        "utr_start",
        "utr_end",
        "transcript_start",
        "transcript_end",
        "site_DNA",
        "flank_DNA",
    ]
    with (out / "sites.tsv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for header, seq in fasta():
            parts = header.split("|")
            tid = parts[0]
            if tid not in tx:
                continue
            assert tid not in seen
            seen.add(tid)
            m = tx[tid]
            assert len(seq) == int(parts[6]) == m["exon_length"], tid
            assert parts[1] == m["gene_id"] and parts[5] == m["gene"], tid
            match = re.search(r"(?:^|\|)UTR3:(\d+)-(\d+)\|", header)
            if not match:
                assert m["gtf_utr3_length"] == 0, tid
                excluded.append(dict(transcript_id=tid, reason="no_annotated_UTR3"))
                continue
            start, end = map(int, match.groups())
            assert 1 <= start <= end == len(seq), tid
            utr = seq[start - 1 : end]
            assert len(utr) == m["gtf_utr3_length"], (
                tid,
                len(utr),
                m["gtf_utr3_length"],
            )
            if len(utr) < 8:
                excluded.append(dict(transcript_id=tid, reason="UTR3_shorter_than_8"))
                continue
            stable_gene = m["gene_id"].split(".")[0]
            all_genes.add(stable_gene)
            tested.append(
                dict(
                    transcript_id=tid,
                    **m,
                    utr_start=start,
                    utr_end=end,
                    utr_length=len(utr),
                    utr_sha256=hashlib.sha256(utr.encode()).hexdigest(),
                )
            )
            for c in candidates:
                key = (c["candidate"], c["variant"])
                hits = sites(utr, c["sequence_RNA"])
                pair = (c["candidate"], m["gene"])
                if pair in pairs and c["variant"] == "inventory_reference":
                    pair_tx[pair].append(tid)
                if hits:
                    gene_hits[key].add(stable_gene)
                    hit_tx[key].add(tid)
                for a, b, kind in hits:
                    counts[key][kind] += 1
                    row = dict(
                        candidate=c["candidate"],
                        variant=c["variant"],
                        gene=m["gene"],
                        gene_id=m["gene_id"],
                        transcript_id=tid,
                        mane_select=m["mane_select"],
                        site_type=kind,
                        utr_start=a + 1,
                        utr_end=b,
                        transcript_start=start + a,
                        transcript_end=start + b - 1,
                        site_DNA=utr[a:b],
                        flank_DNA=utr[max(0, a - 15) : min(len(utr), b + 15)],
                    )
                    writer.writerow(row)
                    if pair in pairs and c["variant"] == "inventory_reference":
                        pair_hits[pair].append(row)
    assert seen == set(tx), (len(set(tx) - seen), sorted(set(tx) - seen)[:5])
    summary_rows = []
    for c in candidates:
        key = (c["candidate"], c["variant"])
        summary_rows.append(
            dict(
                **c,
                genes_with_sites=len(gene_hits[key]),
                transcripts_with_sites=len(hit_tx[key]),
                sites_8mer=counts[key]["8mer"],
                sites_7mer_m8=counts[key]["7mer-m8"],
                sites_7mer_A1=counts[key]["7mer-A1"],
            )
        )
    write_tsv(out / "candidate_summary.tsv", summary_rows, list(summary_rows[0]))
    write_tsv(out / "transcripts.tsv", tested, list(tested[0]))
    write_tsv(out / "excluded_transcripts.tsv", excluded, ["transcript_id", "reason"])
    pair_rows = []
    for pair in sorted(pairs):
        hits = pair_hits[pair]
        tested_ids = sorted(pair_tx[pair])
        covered = sorted({r["transcript_id"] for r in hits})
        pair_rows.append(
            dict(
                candidate=pair[0],
                gene=pair[1],
                eligible_transcripts=len(tested_ids),
                transcripts_with_sites=len(covered),
                site_types=";".join(sorted({r["site_type"] for r in hits})),
                transcript_ids=";".join(tested_ids),
                hit_transcript_ids=";".join(covered),
                status="canonical_site_found"
                if hits
                else "no_canonical_site_in_tested_UTRs"
                if tested_ids
                else "not_tested_no_eligible_UTR",
            )
        )
    write_tsv(out / "literature_pairs.tsv", pair_rows, list(pair_rows[0]))
    write_tsv(
        out / "literature_pair_sites.tsv",
        [r for pair in sorted(pair_hits) for r in pair_hits[pair]],
        fields,
    )
    meta = dict(
        reference=protocol["reference"],
        inventory_candidates=16,
        extra_end_variants=2,
        selected_protein_coding_transcripts=len(tx),
        tested_utr_transcripts=len(tested),
        tested_genes=len(all_genes),
        excluded=dict(Counter(r["reason"] for r in excluded)),
        gtf_fasta_length_checks="all selected transcript lengths and UTR3 lengths agree",
        scope=protocol["purpose"],
    )
    (out / "summary.json").write_text(json.dumps(meta, indent=2) + "\n")
    inputs = [DATA / r["file"] for r in retrieval["files"]] + [
        DATA / "scan_protocol.json",
        DATA / "retrieval.json",
        AUDIT / "candidates.tsv",
        AUDIT / "curated_sequence_links.tsv",
    ]
    artifacts = [
        "candidates.tsv",
        "sites.tsv",
        "candidate_summary.tsv",
        "transcripts.tsv",
        "excluded_transcripts.tsv",
        "literature_pairs.tsv",
        "literature_pair_sites.tsv",
        "summary.json",
    ]
    manifest = dict(
        inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
        code_sha256=sha(Path(__file__)),
        outputs={name: sha(out / name) for name in artifacts},
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(meta))
    print(json.dumps(pair_rows, indent=2))


if __name__ == "__main__":
    main()

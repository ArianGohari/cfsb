"""Audit PFKP isoforms and the miR-6517 motif using frozen GENCODE inputs."""

from pathlib import Path
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[4]
REF = ROOT / "data/datasets/milk_mirna_inventory/human_target_reference"
SEED = ROOT / "output/part2/milk_inventory/human_seed_screen"
OUT = ROOT / "output/part2/milk_inventory/pfkp_review"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with (SEED / "transcripts.tsv").open() as stream:
        tx = {
            r["transcript_id"]: r
            for r in csv.DictReader(stream, delimiter="\t")
            if r["gene"] == "PFKP"
        }
    features = defaultdict(list)
    with gzip.open(REF / "gencode.v48.basic.annotation.gtf.gz", "rt") as stream:
        for line in stream:
            if "\t" not in line or 'gene_name "PFKP"' not in line:
                continue
            fields = line.rstrip().split("\t")
            attrs = defaultdict(list)
            for key, value in re.findall(r'(\w+) "([^"]*)"', fields[8]):
                attrs[key].append(value)
            tid = attrs.get("transcript_id", [""])[0]
            if tid in tx:
                features[tid].append((fields, attrs))
    sequences = {}
    current = None
    with gzip.open(REF / "gencode.v48.pc_transcripts.fa.gz", "rt") as stream:
        for line in stream:
            if line.startswith(">"):
                current = line[1:].split("|")[0]
                if current in tx:
                    sequences[current] = ""
            elif current in tx:
                sequences[current] += line.strip().upper()
    rc = lambda s: s.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    mirna = "UCAGGGUCCGUGAGCUCCUCGGC".replace("U", "T")
    motifs = {
        "8mer": rc(mirna[1:8]) + "A",
        "7mer-m8": rc(mirna[1:8]),
        "7mer-A1": rc(mirna[1:7]) + "A",
    }
    results = []
    for tid, row in sorted(tx.items()):
        entries = features[tid]
        fields, attrs = next((f, a) for f, a in entries if f[2] == "transcript")
        exons = sorted((int(f[3]), int(f[4])) for f, a in entries if f[2] == "exon")
        assert fields[6] == "+"  # PFKP coordinates increase along its transcripts.
        genome = [pos for start, end in exons for pos in range(start, end + 1)]
        seq = sequences[tid]
        assert len(genome) == len(seq)
        start, end = int(row["utr_start"]), int(row["utr_end"])
        utr = seq[start - 1 : end]
        assert sha_bytes(utr.encode()) == row["utr_sha256"]
        hits = []
        for i in range(len(utr)):
            for kind, motif in motifs.items():
                if not utr.startswith(motif, i):
                    continue
                if kind == "7mer-m8" and utr.startswith(motifs["8mer"], i):
                    continue
                if (
                    kind == "7mer-A1"
                    and i > 0
                    and utr.startswith(motifs["8mer"], i - 1)
                ):
                    continue
                coords = genome[start - 1 + i : start - 1 + i + len(motif)]
                hits.append(
                    dict(
                        type=kind,
                        motif=motif,
                        utr_start=i + 1,
                        utr_end=i + len(motif),
                        chromosome=fields[0],
                        genomic_positions_1based=coords,
                    )
                )
        cds_length = sum(int(f[4]) - int(f[3]) + 1 for f, a in entries if f[2] == "CDS")
        results.append(
            dict(
                transcript=tid,
                name=attrs["transcript_name"][0],
                mane_select=row["mane_select"] == "True",
                transcript_support_level=attrs.get(
                    "transcript_support_level", ["not_given"]
                )[0],
                tags=attrs.get("tag", []),
                cds_nt=cds_length,
                utr_length=len(utr),
                utr_genomic_start=genome[start - 1],
                utr_genomic_end=genome[end - 1],
                hits=hits,
            )
        )
    reference = next(r for r in results if r["mane_select"])
    for row in results:
        row["utr_extends_beyond_mane_end_nt"] = max(
            0, row["utr_genomic_end"] - reference["utr_genomic_end"]
        )
    evidence = dict(
        reference="GENCODE 48 basic CHR; four eligible protein-coding PFKP transcripts",
        coordinates="GRCh38, 1-based inclusive; UTR excludes stop codon",
        isoforms=results,
        conclusion="One motif in a distal UTR segment of a non-MANE coding isoform. Gene-level GSE169514 counts cannot determine its usage or regulatory effect.",
    )
    (OUT / "isoform_audit.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [
        Path(__file__).resolve(),
        SEED / "transcripts.tsv",
        REF / "gencode.v48.basic.annotation.gtf.gz",
        REF / "gencode.v48.pc_transcripts.fa.gz",
    ]
    manifest = dict(
        inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
        outputs={
            str((OUT / "isoform_audit.json").relative_to(ROOT)): sha(
                OUT / "isoform_audit.json"
            )
        },
    )
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


if __name__ == "__main__":
    main()

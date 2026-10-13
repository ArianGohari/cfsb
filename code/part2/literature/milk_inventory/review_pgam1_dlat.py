"""Recheck two target hypotheses using frozen reference sequences."""

from pathlib import Path
import csv
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
SEED = ROOT / "output/part2/milk_inventory/human_seed_screen"
FASTA = (
    ROOT
    / "data/datasets/milk_mirna_inventory/human_target_reference/gencode.v48.pc_transcripts.fa.gz"
)
OUT = ROOT / "output/part2/milk_inventory/pgam1_dlat_sequences"


def read(path):
    with path.open() as f:
        return list(csv.DictReader(f, delimiter="\t"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tx = {
        r["transcript_id"]: r
        for r in read(SEED / "transcripts.tsv")
        if r["gene"] in {"PGAM1", "DLAT"}
    }
    sequences = {}
    current = None
    with gzip.open(FASTA, "rt") as f:
        for line in f:
            if line.startswith(">"):
                current = line[1:].split("|")[0]
                if current in tx:
                    sequences[current] = ""
            elif current in tx:
                sequences[current] += line.strip().upper()
    candidate = next(
        r
        for r in read(SEED / "candidates.tsv")
        if r["candidate"] == "bta-miR-6517" and r["variant"] == "inventory_reference"
    )
    mirna = candidate["sequence_RNA"].replace("U", "T")
    rc = lambda s: s.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    motifs = {
        "8mer": rc(mirna[1:8]) + "A",
        "7mer-m8": rc(mirna[1:8]),
        "7mer-A1": rc(mirna[1:7]) + "A",
    }
    results = []
    for tid, row in sorted(tx.items()):
        utr = sequences[tid][int(row["utr_start"]) - 1 : int(row["utr_end"])]
        assert hashlib.sha256(utr.encode()).hexdigest() == row["utr_sha256"]
        hits = []
        for i in range(len(utr)):
            for kind, motif in motifs.items():
                if not utr.startswith(motif, i):
                    continue
                if kind == "7mer-m8" and utr.startswith(motifs["8mer"], i):
                    continue
                if kind == "7mer-A1" and i and utr.startswith(motifs["8mer"], i - 1):
                    continue
                hits.append(
                    dict(
                        type=kind, motif=motif, utr_start=i + 1, utr_end=i + len(motif)
                    )
                )
        results.append(
            dict(
                gene=row["gene"],
                gene_id=row["gene_id"].split(".")[0],
                transcript=tid,
                mane_select=row["mane_select"] == "True",
                utr_length=len(utr),
                hits=hits,
            )
        )
    old = [
        (r["transcript_id"], r["site_type"], int(r["utr_start"]), int(r["utr_end"]))
        for r in read(SEED / "sites.tsv")
        if r["candidate"] == "bta-miR-6517"
        and r["variant"] == "inventory_reference"
        and r["gene"] in {"PGAM1", "DLAT"}
    ]
    new = [
        (r["transcript"], h["type"], h["utr_start"], h["utr_end"])
        for r in results
        for h in r["hits"]
    ]
    assert sorted(old) == sorted(new)
    summaries = []
    for gene in ["PGAM1", "DLAT"]:
        isoforms = [r for r in results if r["gene"] == gene]
        mane = next(r for r in isoforms if r["mane_select"])
        summaries.append(
            dict(
                gene=gene,
                transcripts_tested=len(isoforms),
                transcripts_with_motif=sum(bool(r["hits"]) for r in isoforms),
                mane=mane,
            )
        )
    data = dict(
        summary=summaries,
        isoforms=results,
        limits="Reference sequence motifs only; no target validation or evidence of isoform expression.",
    )
    target = OUT / "evidence.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    inputs = [
        Path(__file__).resolve(),
        FASTA,
        SEED / "transcripts.tsv",
        SEED / "sites.tsv",
        SEED / "candidates.tsv",
    ]
    (OUT / "manifest.json").write_text(
        json.dumps(
            dict(
                inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                outputs={str(target.relative_to(ROOT)): sha(target)},
            ),
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()

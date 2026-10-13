"""Recheck reported sequences against source text and the frozen human reference."""

import json
import re
from pathlib import Path
import scan_human_seeds as scan

ROOT = scan.ROOT
CURATION = (
    ROOT
    / "data/datasets/milk_mirna_inventory/fulltext_review_20261009/curated_extraction.json"
)
OUT = ROOT / "output/part2/milk_inventory/fulltext_review"


def main():
    record = json.loads(CURATION.read_text())
    for name, checksum in record["sources"].items():
        assert scan.sha(ROOT / name) == checksum, name
    retrieval = json.loads((scan.DATA / "retrieval.json").read_text())
    for source in retrieval["files"]:
        assert scan.sha(scan.DATA / source["file"]) == source["sha256"]
    yang = record["yang"]
    inventory = {
        r["candidate"]: r["sequence_RNA"]
        for r in scan.read_tsv(scan.AUDIT / "candidates.tsv")
    }
    assert inventory["bta-miR-6517"] == yang["miRNA_RNA"]
    header, sequence = next(
        (h, s) for h, s in scan.fasta() if h.split("|")[0] == yang["human_transcript"]
    )
    start, end = map(int, re.search(r"UTR3:(\d+)-(\d+)", header).groups())
    utr = sequence[start - 1 : end]
    wildtype = yang["pfkl_WT_RNA"].replace("U", "T")
    mutant = yang["pfkl_MUT_RNA"].replace("U", "T")
    yang_result = {
        "guide_matches_inventory": True,
        "figure_WT_sites_zero_based_half_open": scan.sites(wildtype, yang["miRNA_RNA"]),
        "figure_MUT_sites_zero_based_half_open": scan.sites(mutant, yang["miRNA_RNA"]),
        "human_transcript": yang["human_transcript"],
        "exact_figure_WT_in_human_transcript": wildtype in sequence,
        "exact_figure_WT_in_human_UTR3": wildtype in utr,
        "human_UTR3_sites_zero_based_half_open": scan.sites(utr, yang["miRNA_RNA"]),
        "interpretation": "The previously found human 7mer-A1 is not the reported figure fragment; construct origin/accession remains unverified.",
    }
    text = (
        ROOT / "data/sources/zhang_2024_mir2285f_map2k2/zhang_2024_mir2285f_map2k2.txt"
    ).read_text()
    text = text.replace("\u00ad", "").replace("\u200b", "")
    table = text[text.index("TA B L E 2") : text.index("Note: The wild")]
    sequences = {}
    for gene in ["FGF1", "MAP2K2"]:
        for kind in ["W T", "MUT"]:
            label = gene + "-3′UTR-" + kind
            remainder = table[table.index(label) + len(label) :]
            boundary = re.search(r"\n\s+(?:FGF1|MAP2K2|RPL27A)-", remainder)
            assert boundary, label
            sequences[label] = "".join(
                re.findall("[ACGT]+", remainder[: boundary.start()])
            )
    zhang_result = {
        "table_2_sequences_as_printed": sequences,
        "lengths": {name: len(s) for name, s in sequences.items()},
        "FGF1_and_MAP2K2_WT_identical": sequences["FGF1-3′UTR-W T"]
        == sequences["MAP2K2-3′UTR-W T"],
        "interpretation": "Published table identity and unequal WT/MUT lengths require clarification; do not silently correct constructs.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "yang": yang_result,
        "zhang": zhang_result,
        "curation_sha256": scan.sha(CURATION),
        "code_sha256": scan.sha(Path(__file__)),
        "seed_code_sha256": scan.sha(Path(scan.__file__)),
        "human_reference_receipt_sha256": scan.sha(scan.DATA / "retrieval.json"),
    }
    (OUT / "sequence_audit.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        json.dumps(
            {
                "yang": yang_result,
                "zhang_lengths": zhang_result["lengths"],
                "duplicated_WT": zhang_result["FGF1_and_MAP2K2_WT_identical"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

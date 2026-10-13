"""Compare curated Figure 5A excerpts with the existing human RAP1A screen."""

import csv
import hashlib
import json
from pathlib import Path

import yaml
from scan_human_seeds import fasta, positions, sites

ROOT = Path(__file__).resolve().parents[4]
NOTE = (
    ROOT
    / "obsidian/Projekt/Literatur/04 Datenextraktion/Quellen/Bae und Kim (2021) - miR-2478 und Melaninbildung.md"
)
BASE = ROOT / "output/part2/milk_inventory"
OUT = BASE / "bae_reporter_review"


def main():
    props = yaml.safe_load(NOTE.read_text().split("---", 2)[1])
    review = props["Reporterprüfung"]
    wt, mut = review["WT 5 nach 3"], review["MUT 5 nach 3"]
    mirna = review["Inventarsequenz RNA 5 nach 3"]
    pair_file = BASE / "human_seed_screen/literature_pair_sites.tsv"
    with pair_file.open() as handle:
        pairs = [
            r
            for r in csv.DictReader(handle, delimiter="\t")
            if r["gene"] == "RAP1A" and r["candidate"] == "bta-miR-2478"
        ]
    wanted = {r["transcript_id"] for r in pairs}
    matches = []
    for header, sequence in fasta():
        tid = header.split("|")[0]
        if tid not in wanted:
            continue
        for row in (r for r in pairs if r["transcript_id"] == tid):
            # Check the displayed fragment around the previously mapped site.
            start, end = int(row["transcript_start"]), int(row["transcript_end"])
            hits = [
                p
                for p in positions(sequence, wt)
                if p + 1 <= start and p + len(wt) >= end
            ]
            matches.append(
                {
                    "transcript": tid,
                    "figure_fragment_matches_at_site": bool(hits),
                    "fragment_transcript_start_1based": [p + 1 for p in hits],
                    "site": row["site_DNA"],
                    "utr_site_start_1based": int(row["utr_start"]),
                }
            )
    assert {r["transcript"] for r in matches} == wanted and len(wanted) == 2
    assert all(r["figure_fragment_matches_at_site"] for r in matches)
    figure_prefix = review["Gezeichneter miRNA-Abschnitt 3 nach 5"][::-1]
    result = {
        "doi": props["DOI"],
        "curated_figure_excerpts": review,
        "human_RAP1A_matches": matches,
        "WT_sites_for_inventory_sequence": sites(wt, mirna),
        "MUT_sites_for_inventory_sequence": sites(mut, mirna),
        "figure_miRNA_prefix_5_to_3_DNA": figure_prefix,
        "prefix_matches_inventory": mirna.replace("U", "T").startswith(figure_prefix),
        "scope": "Displayed fragments only. Full construct origin and actual mimic sequence remain unresolved; no functional human validation.",
    }
    assert (
        result["WT_sites_for_inventory_sequence"]
        and not result["MUT_sites_for_inventory_sequence"]
    )
    assert not result["prefix_matches_inventory"]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "review.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = [
        NOTE,
        pair_file,
        Path(__file__),
        Path(__file__).with_name("scan_human_seeds.py"),
        ROOT
        / "data/datasets/milk_mirna_inventory/human_target_reference/gencode.v48.pc_transcripts.fa.gz",
        ROOT
        / "data/sources/bae_2021_milk_mir2478_melanogenesis/bae_2021_milk_mir2478_melanogenesis.pdf",
    ]
    hashes = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in inputs
    }
    (OUT / "manifest.json").write_text(
        json.dumps(hashes, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

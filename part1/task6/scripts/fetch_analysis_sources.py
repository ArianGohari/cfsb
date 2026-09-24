#!/usr/bin/env python3
"""Download the frozen GEO inputs and verify selected NCBI ortholog pairs."""

from __future__ import annotations

import csv
import hashlib
import json
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
ANALYSIS = ROOT / "analysis"

FILES = {
    "GSE17256_series_matrix.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE17nnn/GSE17256/matrix/GSE17256_series_matrix.txt.gz",
    "GSE18565_series_matrix.txt.gz": "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE18nnn/GSE18565/matrix/GSE18565_series_matrix.txt.gz",
    "GPL1261.annot.gz": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPL1nnn/GPL1261/annot/GPL1261.annot.gz",
    "GPL570.annot.gz": "https://ftp.ncbi.nlm.nih.gov/geo/platforms/GPLnnn/GPL570/annot/GPL570.annot.gz",
}

# These pairs are deliberately small and hypothesis-driven. Each pair must be
# returned by the NCBI ortholog endpoint for the mouse gene on the fetch date.
PAIRS = [
    ("Abca1", 11303, "ABCA1", 19),
    ("Abcg1", 11307, "ABCG1", 9619),
    ("Cx3cr1", 13051, "CX3CR1", 1524),
    ("Il1b", 16176, "IL1B", 3553),
    ("Trem2", 83433, "TREM2", 54209),
    ("Lpl", 16956, "LPL", 4023),
    ("Apoe", 11816, "APOE", 348),
    ("Cd68", 12514, "CD68", 968),
    ("S100a8", 20201, "S100A8", 6279),
    ("S100a9", 20202, "S100A9", 6280),
    ("Sell", 20343, "SELL", 6402),
    ("Nr4a1", 15370, "NR4A1", 3164),
    ("Itgam", 16409, "ITGAM", 3684),
    ("Lcn2", 16819, "LCN2", 3934),
    ("Camp", 12796, "CAMP", 820),
    ("Elane", 50701, "ELANE", 1991),
    ("Mpo", 17523, "MPO", 4353),
    ("Cxcr2", 12765, "CXCR2", 3579),
]


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "cfsb-task6/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response:
        destination.write_bytes(response.read())


def main() -> None:
    SOURCES.mkdir(exist_ok=True)
    ANALYSIS.mkdir(exist_ok=True)
    for name, url in FILES.items():
        target = SOURCES / name
        if not target.exists():
            download(url, target)

    snapshots = []
    rows = []
    for mouse_symbol, mouse_id, human_symbol, human_id in PAIRS:
        url = (
            "https://api.ncbi.nlm.nih.gov/datasets/v2alpha/gene/id/"
            f"{mouse_id}/orthologs?taxon_filter=9606"
        )
        request = urllib.request.Request(url, headers={"User-Agent": "cfsb-task6/1.0"})
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
        returned = {
            int(report["gene"]["gene_id"]): report["gene"].get("symbol", "")
            for report in payload.get("reports", [])
            if report.get("gene", {}).get("tax_id") == "9606"
        }
        if human_id not in returned:
            raise RuntimeError(
                f"NCBI no longer returns {human_id} for mouse gene {mouse_id}: {returned}"
            )
        snapshots.append({"mouse_gene_id": mouse_id, "url": url, "response": payload})
        rows.append(
            {
                "mouse_symbol": mouse_symbol,
                "mouse_gene_id": mouse_id,
                "human_symbol": human_symbol,
                "human_gene_id": human_id,
                "source": url,
                "verified_on": "2026-09-24",
            }
        )

    (SOURCES / "ncbi_selected_orthologs.json").write_text(
        json.dumps(snapshots, indent=2, ensure_ascii=False) + "\n"
    )
    with (ANALYSIS / "ortholog_pairs.tsv").open("w", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    manifest_rows = []
    for name, url in FILES.items():
        payload = (SOURCES / name).read_bytes()
        manifest_rows.append(
            {
                "file": f"sources/{name}",
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_url": url,
                "frozen_on": "2026-09-24",
            }
        )
    ortholog_path = SOURCES / "ncbi_selected_orthologs.json"
    payload = ortholog_path.read_bytes()
    manifest_rows.append(
        {
            "file": "sources/ncbi_selected_orthologs.json",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "source_url": "NCBI Datasets ortholog endpoints listed in ortholog_pairs.tsv",
            "frozen_on": "2026-09-24",
        }
    )
    with (ANALYSIS / "source_manifest.tsv").open("w", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(manifest_rows)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Descriptive aggregation of the three published GSE97310 10X matrices."""

from __future__ import annotations

import csv
import io
import json
import math
import tarfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "analysis"
ARCHIVE = ROOT / "sources/GSE97310_10X_Matrices_CircRes2018.tar.gz"

PROGRAMS = {
    "network_efflux": ["Abca1", "Abcg1"],
    "network_recruitment": ["Ccr2", "Ccr5", "Cx3cr1"],
    "network_il1b": ["Il1b"],
    "classical_monocyte": ["Ccr2", "Ly6c2", "S100a8", "S100a9", "Lyz2", "Sell"],
    "patrolling_monocyte": ["Cx3cr1", "Nr4a1", "Lst1", "Itgam"],
    "lipid_macrophage": ["Trem2", "Lpl", "Apoe", "Abca1", "Abcg1", "Cd68"],
    "neutrophil_granule": ["S100a8", "S100a9", "Lcn2", "Camp", "Elane", "Mpo", "Cxcr2", "Retnlg"],
}
SELECTED = sorted(set().union(*PROGRAMS.values()))


def write_tsv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    gene_rows: list[dict] = []
    program_rows: list[dict] = []
    inventory: list[dict] = []
    with tarfile.open(ARCHIVE) as archive:
        gene_members = sorted(
            (m for m in archive.getmembers() if m.name.endswith("/genes.tsv")),
            key=lambda member: member.name,
        )
        assert len(gene_members) == 3
        for gene_member in gene_members:
            prefix = gene_member.name.rsplit("/", 1)[0]
            matrix_name = prefix.rsplit("/", 1)[-1]
            features = [line.decode().rstrip("\n").split("\t") for line in archive.extractfile(gene_member)]
            symbol_rows = {row[1]: i + 1 for i, row in enumerate(features) if row[1] in SELECTED}
            missing = sorted(set(SELECTED) - set(symbol_rows))
            assert not missing, (matrix_name, missing)
            barcode_count = sum(1 for _ in archive.extractfile(prefix + "/barcodes.tsv"))
            handle = io.TextIOWrapper(archive.extractfile(prefix + "/matrix.mtx"))
            header = next(handle)
            while header.startswith("%"):
                header = next(handle)
            feature_count, columns, expected_nnz = map(int, header.split())
            assert feature_count == len(features) and columns == barcode_count
            reverse = {row: symbol for symbol, row in symbol_rows.items()}
            sums = Counter()
            positive_cells = {symbol: set() for symbol in SELECTED}
            total_counts = 0
            observed_nnz = 0
            for line in handle:
                row, column, value = map(int, line.split())
                total_counts += value
                observed_nnz += 1
                if row in reverse:
                    symbol = reverse[row]
                    sums[symbol] += value
                    positive_cells[symbol].add(column)
            assert observed_nnz == expected_nnz
            inventory.append(
                {
                    "matrix": matrix_name,
                    "features": feature_count,
                    "barcodes": barcode_count,
                    "nonzero_entries": observed_nnz,
                    "library_counts": total_counts,
                    "biological_replicates": 1,
                    "inference_allowed": "no",
                }
            )
            cpm = {}
            for symbol in SELECTED:
                cpm[symbol] = 1_000_000 * sums[symbol] / total_counts
                gene_rows.append(
                    {
                        "matrix": matrix_name,
                        "symbol": symbol,
                        "counts": sums[symbol],
                        "library_counts": total_counts,
                        "counts_per_million": f"{cpm[symbol]:.8f}",
                        "positive_barcodes": len(positive_cells[symbol]),
                        "total_barcodes": barcode_count,
                        "positive_fraction": f"{len(positive_cells[symbol]) / barcode_count:.8f}",
                    }
                )
            for program, genes in PROGRAMS.items():
                program_rows.append(
                    {
                        "matrix": matrix_name,
                        "program": program,
                        "gene_count": len(genes),
                        "mean_log1p_cpm": f"{sum(math.log1p(cpm[g]) for g in genes) / len(genes):.8f}",
                        "interpretation": "descriptive aggregate; no biological replicate",
                    }
                )
    write_tsv(OUT / "gse97310_inventory.tsv", inventory)
    write_tsv(OUT / "gse97310_selected_gene_counts.tsv", gene_rows)
    write_tsv(OUT / "gse97310_program_summary.tsv", program_rows)
    (OUT / "gse97310_validation.json").write_text(
        json.dumps(
            {
                "matrices": len(inventory),
                "selected_genes": len(SELECTED),
                "programs": len(PROGRAMS),
                "gene_matrix_rows": len(gene_rows),
                "all_matrices_single_aggregate": all(row["biological_replicates"] == 1 for row in inventory),
                "statistical_tests_performed": 0,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()

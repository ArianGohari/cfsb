#!/usr/bin/env python3
"""Fail-fast checks for the Task 6 quantitative outputs."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"


def rows(name: str) -> list[dict[str, str]]:
    with (ANALYSIS / name).open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    checks: dict[str, object] = {}

    manifest = rows("source_manifest.tsv")
    assert len(manifest) == 5
    for item in manifest:
        path = ROOT / item["file"]
        payload = path.read_bytes()
        assert len(payload) == int(item["bytes"])
        assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    checks["frozen_sources"] = len(manifest)

    metadata = rows("sample_metadata.tsv")
    counts = Counter((row["species"], row["group"]) for row in metadata)
    assert counts == Counter(
        {
            ("mouse", "classical"): 4,
            ("mouse", "nonclassical"): 4,
            ("human", "classical"): 3,
            ("human", "nonclassical"): 3,
        }
    )
    for species, expected_pairs in [("mouse", 4), ("human", 3)]:
        subset = [row for row in metadata if row["species"] == species]
        pair_counts = Counter(row["pair"] for row in subset)
        assert len(pair_counts) == expected_pairs and set(pair_counts.values()) == {2}
    checks["biological_units"] = {"mouse_pools": 4, "human_donors": 3}

    summary = json.loads((ANALYSIS / "summary.json").read_text())
    assert summary["mouse"]["residual_df"] == 3
    assert summary["human"]["residual_df"] == 2
    assert summary["mouse"]["probe_discoveries_fdr_0_05"] > 0
    assert summary["human"]["probe_discoveries_fdr_0_05"] > 0
    assert summary["ortholog_comparison"]["n"] == 17
    assert -1 <= summary["ortholog_comparison"]["spearman_rho"] <= 1
    checks["differential_models"] = "paired limma models have expected residual degrees of freedom"

    gene_results = rows("selected_gene_results.tsv")
    network = {"Abca1", "Abcg1", "Ccr2", "Ccr5", "Cx3cr1", "Il1b"}
    mouse_network = {row["feature"] for row in gene_results if row["species"] == "mouse" and row["feature"] in network}
    network_lower = {symbol.lower() for symbol in network}
    human_network = {row["feature"] for row in gene_results if row["species"] == "human" and row["feature"].lower() in network_lower}
    assert mouse_network == network
    assert len(human_network) == 6
    for row in gene_results:
        for field in ("logFC", "ci_low", "ci_high", "P.Value", "selected_adj_p"):
            assert math.isfinite(float(row[field]))
    checks["network_genes_tested_per_species"] = 6

    program_tests = rows("program_tests.tsv")
    assert len(program_tests) == 14
    assert Counter(row["species"] for row in program_tests) == {"mouse": 7, "human": 7}
    checks["program_tests"] = 14

    sensitivity = rows("paired_unpaired_sensitivity.tsv")
    assert sensitivity and all(row["direction_stable"] in {"TRUE", "FALSE"} for row in sensitivity)
    checks["sensitivity_features"] = len(sensitivity)

    inventory = rows("gse97310_inventory.tsv")
    assert len(inventory) == 3
    assert all(row["biological_replicates"] == "1" and row["inference_allowed"] == "no" for row in inventory)
    validation = json.loads((ANALYSIS / "gse97310_validation.json").read_text())
    assert validation["statistical_tests_performed"] == 0
    checks["gse97310_inference_tests"] = 0

    for filename, expected_rows in [
        ("mouse_probe_differential.tsv.gz", 45101),
        ("human_probe_differential.tsv.gz", 54675),
    ]:
        with gzip.open(ANALYSIS / filename, "rt") as handle:
            observed = sum(1 for _ in handle) - 1
        assert observed == expected_rows
    checks["probe_rows"] = {"mouse": 45101, "human": 54675}

    figure = ROOT / "figures/quantitative_results.svg"
    ET.parse(figure)
    assert figure.stat().st_size > 10_000
    checks["figure_svg_valid"] = True

    (ANALYSIS / "validation.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()

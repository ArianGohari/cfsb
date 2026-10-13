"""Extract published PFKL rows from Choi's supplement; do not fit a protein rate."""

from pathlib import Path
import hashlib
import json
import openpyxl

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "data/sources/choi_2023_adipocyte_turnover/pr2c00763_si_002.xlsx"
OUT = ROOT / "output/part2/milk_inventory/pfkl_turnover"


def main():
    workbook = openpyxl.load_workbook(SOURCE, data_only=True, read_only=True)
    matches = []
    sheets = ["Protein_half-lives", "%_old_peptides_rep_1", "%_old_peptides_rep_2"]
    for name in sheets:
        sheet = workbook[name]
        headers = [c.value for c in sheet[4]]
        for number, row in enumerate(sheet.iter_rows(min_row=5, values_only=True), 5):
            if any("pfkl" in str(v).lower() or str(v) == "P12382" for v in row):
                matches.append(
                    {
                        "sheet": name,
                        "row": number,
                        "values": {str(k): v for k, v in zip(headers, row) if k},
                    }
                )
    assert len(matches) == 1, "Recheck source interpretation if rows change"
    assert matches[0]["sheet"] == "%_old_peptides_rep_1"
    assert matches[0]["row"] == 916
    assert matches[0]["values"]["Sequence"] == "TFVLEVMGR"
    result = {
        "species": "Mus musculus",
        "cells": "3T3-L1 adipocytes",
        "source_doi": "10.1021/acs.jproteome.2c00763",
        "matches": matches,
        "pfkl_published_half_life_rows": 0,
        "pfkl_rep2_rows": 0,
        "fitted_rate": None,
        "decision": "Single peptide in one labeling replicate; not a human adipocyte protein half-life. No model calibration.",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "evidence.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        "PFKL: one peptide row in rep_1; no published protein half-life; no rate fitted."
    )


if __name__ == "__main__":
    main()

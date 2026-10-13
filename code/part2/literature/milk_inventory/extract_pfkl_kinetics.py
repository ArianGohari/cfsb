"""Extract published WT PFKL assay values, retaining exact spreadsheet locations.

Offline, standard library only. Does not fit a model or alter the source workbook.
"""

from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "data/datasets/milk_mirna_inventory/pfkl_model_feasibility_20261010"
OUTPUT = ROOT / "output/part2/milk_inventory/pfkl_kinetics"
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def main():
    path = SOURCE / "lynch_2024_source_data.xlsx"
    manifest = json.loads((SOURCE / "retrieval.json").read_text())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == next(r["sha256"] for r in manifest if r["file"] == path.name)
    rows = []
    with ZipFile(path) as archive:
        strings = [
            "".join(t.text or "" for t in si.iterfind(".//x:t", NS))
            for si in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall(
                "x:si", NS
            )
        ]
        relations = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        }
        for sheet in ET.fromstring(archive.read("xl/workbook.xml")).findall(
            "x:sheets/x:sheet", NS
        ):
            name = sheet.attrib["name"]
            if name.strip() not in (
                "Fig. 4a and SF4b ATP kinetics",
                "Fig 4a and SF4b F6P kinetics",
            ):
                continue
            variable = "ATP" if "ATP" in name else "F6P"
            target = relations[
                sheet.attrib[
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                ]
            ]
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            cells = {}
            for cell in ET.fromstring(archive.read(target)).findall(
                ".//x:sheetData/x:row/x:c", NS
            ):
                value = cell.find("x:v", NS)
                if value is not None:
                    assert cell.find("x:f", NS) is None, (
                        "Review formulas before using cached values"
                    )
                    cells[cell.attrib["r"]] = (
                        strings[int(value.text)]
                        if cell.attrib.get("t") == "s"
                        else value.text
                    )
            assert cells["A1"] == variable + " (mM)" and cells["B1"] == "PFKL"
            for row_number in range(2, 10 if variable == "ATP" else 11):
                concentration = float(cells[f"A{row_number}"])
                for column in "BCDEFGH":
                    address = f"{column}{row_number}"
                    if address not in cells:
                        continue  # Missing observations are not zero.
                    rows.append(
                        dict(
                            sheet=name,
                            concentration_cell=f"A{row_number}",
                            value_cell=address,
                            varied_substrate=variable,
                            concentration_mM=concentration,
                            fixed_substrate="F6P" if variable == "ATP" else "ATP",
                            fixed_concentration_mM=4.0 if variable == "ATP" else 0.125,
                            series_column=column,
                            activity_U_per_mg=float(cells[address]),
                            pH=7.5,
                            temperature_C=25,
                        )
                    )
    assert len(rows) == 112
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "wild_type_assays.tsv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    (OUTPUT / "extraction.json").write_text(
        json.dumps(
            {
                "source": str(path.relative_to(ROOT)),
                "sha256": digest,
                "doi": "10.1038/s41467-024-51808-6",
                "observations": len(rows),
                "rules": "WT columns B:H only; preserve blanks and source column identity; no normalization or background subtraction.",
                "unit_source": "Figure 4a and Methods, Expression and purification of PFKL",
                "limitations": "Columns are not verified independent protein preparations. Concentration response, not a time series. No miRNA measurements.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(
        f"Extracted {len(rows)} WT observations with cell references; source hash verified."
    )


if __name__ == "__main__":
    main()

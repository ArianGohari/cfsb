"""Extract the published PFKL row from Chen's saved XLSX supplements, offline.

Standard-library XLSX reading preserves original cell addresses and values.
No refit, uncertainty estimation, or adipocyte parameter assignment.
"""

from pathlib import Path
import hashlib
import json
import math
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "data/sources/chen_2016_protein_turnover"
OUT = ROOT / "output/part2/chen_turnover"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def rows(path):
    with zipfile.ZipFile(path) as z:
        strings = [
            "".join(t.text or "" for t in item.findall(".//s:t", NS))
            for item in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(
                "s:si", NS
            )
        ]
        for sheet in sorted(z.namelist()):
            if not (sheet.startswith("xl/worksheets/sheet") and sheet.endswith(".xml")):
                continue
            for row in ET.fromstring(z.read(sheet)).findall(".//s:row", NS):
                cells = {}
                for cell in row.findall("s:c", NS):
                    value = cell.find("s:v", NS)
                    value = value.text if value is not None else ""
                    if cell.get("t") == "s" and value:
                        value = strings[int(value)]
                    cells[cell.get("r")] = value
                yield sheet, int(row.get("r")), cells


def main():
    matches = []
    inputs = {}
    for path in sorted(SOURCE.glob("*.xlsx")):
        inputs[str(path.relative_to(ROOT))] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for sheet, row, cells in rows(path):
            if "PFKL" in cells.values() or "P17858" in cells.values():
                matches.append(dict(file=path.name, sheet=sheet, row=row, cells=cells))
    assert len(matches) == 2
    kinetic = [m for m in matches if m["file"].endswith("s004.xlsx")]
    assert len(kinetic) == 1
    match = kinetic[0]
    assert match["row"] == 488 and match["cells"]["B488"] == "P17858"
    half_life = float(match["cells"]["E488"])
    assert math.isclose(half_life, 5.400445504946983)
    result = dict(
        doi="10.1039/c5sc03826j",
        matches=matches,
        published_half_life_h=half_life,
        derived_kdeg_per_h=math.log(2) / half_life,
        unique_peptides=int(match["cells"]["C488"]),
        total_peptides=int(match["cells"]["D488"]),
        uncertainty=None,
        independent_biological_replicate_count=None,
        uncertainty_note="No PFKL error/CI or replicate-specific estimates in Table S3.",
        context="HepG2; newly synthesized S-phase proteins; thymidine synchronization, nocodazole chase.",
        decision="External comparison only; not adopted for adipocytes.",
        inputs=inputs,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print(
        f"PFKL Table S3 E488: {half_life:.6f} h; one unique peptide; no parameter adopted."
    )


if __name__ == "__main__":
    main()

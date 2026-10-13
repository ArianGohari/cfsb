"""Check the saved Doherty supplement for PFKL; requires Poppler pdftotext.

This is a table-coverage check, not a protein-turnover reanalysis.
"""

from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "data/sources/doherty_2009_protein_turnover"
OUT = ROOT / "output/part2/doherty_turnover"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = SOURCE / "pr800641v_si_001.pdf"
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    (OUT / "supplement_layout.txt").write_text(text)
    accessions = re.findall(r"^\s*([A-Z][A-Z0-9]{5})\s", text, re.M)
    assert len(accessions) == 576
    queries = ["PFKL", "P17858", "phosphofructokinase", "liver type", "liver-type"]
    matches = {q: [] for q in queries}
    for page, body in enumerate(text.split("\f"), 1):
        for line, value in enumerate(body.splitlines(), 1):
            for q in queries:
                if q.lower() in value.lower():
                    matches[q].append(dict(page=page, line=line, text=value.strip()))
    assert not matches["PFKL"] and not matches["P17858"]
    assert len(matches["phosphofructokinase"]) == 1
    assert "platelet" in matches["phosphofructokinase"][0]["text"]
    result = dict(
        doi="10.1021/pr800641v",
        table_accession_rows=len(accessions),
        matches=matches,
        pfkl_identified=False,
        decision="No identifiable PFKL row; platelet PFK is not a PFKL parameter.",
        limitations="Name/accession search only; historical accessions not exhaustively remapped.",
        cell_context="Main text A549; supplement heading HeLa; unresolved source discrepancy.",
        dilution="Main text explicitly subtracts growth dilution from label-loss rate.",
        inputs={
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [pdf, SOURCE / "doherty_2009.pdf"]
        },
    )
    (OUT / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )
    print("576 accession rows checked; no identifiable PFKL; PFKP row on page 12.")


if __name__ == "__main__":
    main()

"""Extract Ali's published Table 3 and DOCX Table S1; no read reanalysis."""

from pathlib import Path
from zipfile import ZipFile
import csv, hashlib, json, re, subprocess, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "data/sources/ali_2026_infant_formula_mirnas"
OUT = ROOT / "output/part2/milk_inventory/ali_review"


def write_tsv(path, rows):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = SRC / "ali_2026_infant_formula_mirnas.pdf"
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    rows = []
    for page_number, page in enumerate(text.split("\f"), 1):
        if page_number not in (6, 7, 8):
            continue
        assert "Table 3" in page
        for block in re.split(r"\n(?=  bta-)", page)[1:]:
            lines = block.splitlines()
            parts = []
            for line in lines:
                part = line[:16].strip()
                if not part:
                    break
                parts.append(part)
            m = re.search(r"(MIMAT\d+).*?\s(\d+)\s+(\d+\.\d+)\s*$", lines[0])
            if m:
                rows.append(
                    dict(
                        name="".join(parts).replace(" ", ""),
                        accession=m[1],
                        reads=int(m[2]),
                        rpm=m[3],
                        pdf_page=page_number,
                        table=3,
                    )
                )
    assert len(rows) == 57 and len({r["accession"] for r in rows}) == 57
    assert all(re.fullmatch(r"bta-[A-Za-z0-9-]+", r["name"]) for r in rows)
    write_tsv(OUT / "table3_mature.tsv", rows)
    docx = SRC / "supplements/ali_2026_table_s1.docx"
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with ZipFile(docx) as z:
        body = ET.fromstring(z.read("word/document.xml")).find("w:body", ns)
    markdown = []
    tables = []
    for node in body:
        if node.tag.endswith("}tbl"):
            cells = [
                [
                    "".join(t.text or "" for t in c.findall(".//w:t", ns))
                    for c in row.findall("w:tc", ns)
                ]
                for row in node.findall("w:tr", ns)
            ]
            assert all(len(row) == len(cells[0]) for row in cells)
            tables.append([dict(zip(cells[0], row)) for row in cells[1:]])
            markdown += [
                "| " + " | ".join(cells[0]) + " |",
                "| " + " | ".join(["---"] * len(cells[0])) + " |",
            ]
            markdown += ["| " + " | ".join(row) + " |" for row in cells[1:]]
        else:
            s = "".join(t.text or "" for t in node.findall(".//w:t", ns))
            if s:
                markdown += ["", s, ""]
    assert len(tables) == 1
    (SRC / "supplements/ali_2026_table_s1.md").write_text(
        "# Textentnahme aus dem Original-DOCX\n\nOOXML-Text und Tabellen; keine Marker-Konvertierung.\n"
        + "\n".join(markdown)
        + "\n"
    )
    write_tsv(OUT / "table_s1_precursors.tsv", tables[0])
    counts = {str(t): sum(r["reads"] > t for r in rows) for t in (0, 1, 5, 10)}
    summary = {
        "table3_rows": len(rows),
        "table3_read_sum": sum(r["reads"] for r in rows),
        "table3_count_strictly_greater_than": counts,
        "article_reported_counts": {">1": 57, ">5": 18, ">10": 8},
        "article_reported_mature_reads": 726,
        "table_s1_precursor_rows": len(tables[0]),
        "warnings": [
            "Table 3 includes 21 one-read entries; 57 is not reproduced with the reported >1 threshold.",
            "Table 3 sums to 439, while text reports 726 mature-mapped reads; distinction unresolved.",
            "S1 contains precursor counts, including zero mature counts and duplicate mature IDs. Do not add its row count to mature inventory.",
            "Four cow-based products are stated in Methods 2.1. Published table is aggregated, not four independent per-product values.",
            "Human homolog labels are not an independent sequence comparison.",
        ],
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (pdf, docx)
        },
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

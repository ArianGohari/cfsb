"""Compare all extracted numerical values with Poppler's original-PDF text layer.

Complements the documented visual inspection; this is not independent screening.
"""

from pathlib import Path
import csv, hashlib, json, re, subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "output/part2/milk_inventory"
manifest = json.loads(
    (ROOT / "data/datasets/milk_mirna_inventory/extraction_manifest.json").read_text()
)
observations = list(csv.DictReader((OUT / "observations.tsv").open(), delimiter="\t"))
checked = 0
for spec in manifest["tables"]:
    source = next(r for r in manifest["studies"] if r["id"] == spec["study"])
    pdf = ROOT / source["pdf"]
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source["pdf_sha256"]
    page = str(spec["pdf_page"])
    text = subprocess.check_output(
        ["pdftotext", "-f", page, "-l", page, "-layout", str(pdf), "-"], text=True
    )
    names = list(
        dict.fromkeys(
            r["original_name"] for r in observations if r["study_id"] == spec["study"]
        )
    )
    for name in names:
        matches = [
            line
            for line in text.splitlines()
            if re.search(r"(?<!\S)" + re.escape(name) + r"\s+\d", line)
        ]
        assert len(matches) == 1, (name, matches)
        tail = matches[0].split(name, 1)[1].strip()
        if spec["study"].startswith("li_"):
            values = [int(v) for v in tail.split()]
            assert len(values) == 13
            values = values[:12]
        elif spec["study"].startswith("chen_"):
            values = [int(v.replace(" ", "")) for v in re.split(r"\s{2,}", tail)]
            assert len(values) == 2
        else:
            rank, value = tail.split()
            values = [int(value.replace(",", ""))]
        actual = [
            int(r["value"])
            for r in observations
            if r["study_id"] == spec["study"] and r["original_name"] == name
        ]
        assert values == actual, (name, values, actual)
        checked += len(values)
assert checked == len(observations)
result = {
    "numeric_values_compared": checked,
    "pdf_tables": len(manifest["tables"]),
    "all_match": True,
    "method": "Second extraction through pdftotext -layout plus documented visual table review; not independent human screening",
}
(OUT / "pdf_verification.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))

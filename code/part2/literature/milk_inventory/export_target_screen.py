#!/usr/bin/env python3
"""Export the current curated 16-candidate comparison from its Obsidian note."""

import csv, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
NOTE = (
    ROOT
    / "obsidian/Projekt/Literatur/05 Evidenzbewertung und Synthese/Targetvergleich aller 16 Kandidaten.md"
)
OUT = ROOT / "output/part2/milk_inventory/target_screen"
rows = [
    [cell.strip() for cell in line.strip().strip("|").split("|")]
    for line in NOTE.read_text().splitlines()
    if line.startswith("|")
]
assert len(rows) == 18 and all(len(row) == 4 for row in rows)
expected = {
    r["candidate"].removeprefix("bta-")
    for r in csv.DictReader(
        (ROOT / "output/part2/milk_inventory/annotation_audit/candidates.tsv").open(),
        delimiter="\t",
    )
}
assert {r[0] for r in rows[2:]} == expected
OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "candidates.tsv").open("w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(rows[0])
    writer.writerows(rows[2:])
(OUT / "curation_manifest.json").write_text(
    json.dumps(
        {
            "source_note": str(NOTE.relative_to(ROOT)),
            "source_sha256": hashlib.sha256(NOTE.read_bytes()).hexdigest(),
            "candidate_count": 16,
            "output_sha256": hashlib.sha256(
                (OUT / "candidates.tsv").read_bytes()
            ).hexdigest(),
        },
        indent=2,
    )
    + "\n"
)
print("PASS: 16 candidates exported from current curated note.")

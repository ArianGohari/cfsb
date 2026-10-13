"""Export the bounded milk synthesis from editable notes; preserve screening history."""

from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import yaml

ROOT = Path(__file__).resolve().parents[4]
NOTES = ROOT / "obsidian/Projekt/Literatur/04 Datenextraktion/Quellen"
OUT = ROOT / "output/part2/review_scope"
SCREEN = ROOT / "output/part2/milk_inventory/extension_search/screening.tsv"


def main():
    historical = {r["record"]: r for r in csv.DictReader(SCREEN.open(), delimiter="\t")}
    pending = {
        key
        for key, r in historical.items()
        if r["screened_on"]
        and r["status"] != "Für Milch-Inventar ausgeschlossen"
        and r["fulltext_status"] != "Gezielt geprüft"
    }
    rows, inputs = [], [SCREEN, Path(__file__).resolve()]
    for path in sorted(NOTES.glob("*.md")):
        props = yaml.safe_load(path.read_text().split("\n---\n", 1)[0][4:])
        if props.get("Berichtsrolle") not in {
            "Inventarvergleich",
            "Transferdiskussion",
            "Zurückgestellt",
        }:
            continue
        key = props["Quellen-ID"].lower()
        rows.append(
            dict(
                record=key,
                title=props["Titel"],
                doi=props.get("DOI", ""),
                role=props["Berichtsrolle"],
                scope_date=props["Berichtsstand"],
                reason=props["Berichtsgrund"],
                access=props.get("Berichtszugang", ""),
                original_screening=historical.get(key, {}).get("status", ""),
                fulltext_status=props.get("Volltextstatus", ""),
                source_note=str(path.relative_to(ROOT)),
            )
        )
        inputs.append(path)
    roles = Counter(r["role"] for r in rows)
    assert roles == {
        "Inventarvergleich": 10,
        "Transferdiskussion": 2,
        "Zurückgestellt": 32,
    }, roles
    assert len({r["record"] for r in rows}) == len(rows)
    deferred = [r for r in rows if r["role"] == "Zurückgestellt"]
    assert {r["record"] for r in deferred} == pending
    assert all(r["access"] and r["reason"] for r in deferred)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, subset in [
        ("report_sources.tsv", [r for r in rows if r["role"] != "Zurückgestellt"]),
        ("deferred_records.tsv", deferred),
    ]:
        with (OUT / name).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter="\t")
            writer.writeheader()
            writer.writerows(subset)
    summary = dict(
        scope_date="2026-10-11",
        roles=dict(roles),
        deferred_original_screening=dict(
            Counter(r["original_screening"] for r in deferred)
        ),
        deferred_access=dict(Counter(r["access"] for r in deferred)),
        limitation="Retrospective focused synthesis; 32 records deferred, not excluded. "
        "No complete systematic review or global PRISMA flow claimed. "
        "Target, method and model references are outside this milk-synthesis roster.",
    )
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    )
    outputs = [
        OUT / name
        for name in ["report_sources.tsv", "deferred_records.tsv", "summary.json"]
    ]
    digest = lambda paths: {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in paths
    }
    (OUT / "manifest.json").write_text(
        json.dumps(dict(inputs=digest(inputs), outputs=digest(outputs)), indent=2)
        + "\n"
    )
    print(f"PASS: {dict(roles)}; deferred IDs match historical screening exactly")


if __name__ == "__main__":
    main()

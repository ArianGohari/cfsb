"""Validate and export the editable Obsidian source notes (requires PyYAML)."""

from pathlib import Path
import csv, hashlib, json
import yaml

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "obsidian/Projekt/Literatur/04 Datenextraktion/Quellen"
OUTPUT = ROOT / "output/part2/sources"


def main():
    rows = []
    seen = set()
    dois = set()
    pmids = set()
    for p in sorted(NOTES.glob("*.md")):
        s = p.read_text()
        assert s.startswith("---\n"), p
        props = yaml.safe_load(s.split("\n---\n", 1)[0][4:])
        uid = props["Quellen-ID"]
        assert uid not in seen, uid
        seen.add(uid)
        for key, collection in [("DOI", dois), ("PMID", pmids)]:
            value = str(props.get(key) or "").strip().lower()
            if value:
                assert value not in collection, (key, value)
                collection.add(value)
        assert props["Auswahlstatus"] in [
            "Eingeschlossen",
            "Ausgeschlossen",
            "Reserve",
            "Hintergrund",
            "Offen",
        ], p
        assert props["Neue Auswahl"] in [
            "Offen",
            "Eingeschlossen",
            "Ausgeschlossen",
            "Hintergrund",
        ], p
        if props["Auswahlstatus"] == "Ausgeschlossen":
            assert props.get("Ausschlussgrund"), p
        rows.append({"Notiz": str(p.relative_to(ROOT)), **props})
    fields = list(dict.fromkeys(k for row in rows for k in row))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "Quellen.tsv"
    with target.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, ensure_ascii=False)
                    if isinstance(v, (list, dict))
                    else v
                    for k, v in row.items()
                }
            )
    report = {
        "notes": len(rows),
        "unique_dois": len(dois),
        "unique_pmids": len(pmids),
        "note_sha256": {
            r["Notiz"]: hashlib.sha256((ROOT / r["Notiz"]).read_bytes()).hexdigest()
            for r in rows
        },
        "policy": "Notes are authoritative for current curation. Archived source tables and historical PRISMA counts are not overwritten.",
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        f"PASS: {len(rows)} unique source notes; {len(dois)} DOI and {len(pmids)} PMID identities; export written."
    )


if __name__ == "__main__":
    main()

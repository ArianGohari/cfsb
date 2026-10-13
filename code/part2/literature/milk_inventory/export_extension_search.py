"""Export saved supplementary search hits and current source-note assessments. Offline."""

from pathlib import Path
import csv, json, hashlib, xml.etree.ElementTree as ET
from collections import Counter
import yaml

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/datasets/milk_mirna_inventory/extension_search_20261009"
OUT = ROOT / "output/part2/milk_inventory/extension_search"
NOTES = ROOT / "obsidian/Projekt/Literatur/04 Datenextraktion/Quellen"


def main():
    hits = []
    for query in ("elicit_powder", "elicit_processing"):
        response = json.loads((RAW / (query + ".json")).read_text())
        data = response.get("structuredContent") or json.loads(
            next(c["text"] for c in response["content"] if c["type"] == "text")
        )
        for rank, p in enumerate(data["papers"], 1):
            hits.append(
                dict(
                    search=query,
                    rank=rank,
                    title=p["title"],
                    doi=(p.get("doi") or "").lower(),
                    pmid=str(p.get("pmid") or ""),
                    abstract=p.get("abstract") or "",
                )
            )
    records = ET.parse(RAW / "pubmed_abstracts.xml").getroot()
    order = json.loads((RAW / "pubmed_search.json").read_text())["esearchresult"][
        "idlist"
    ]
    for p in records.findall("PubmedArticle"):
        pmid = p.findtext("./MedlineCitation/PMID")
        ids = p.findall("./PubmedData/ArticleIdList/ArticleId")
        doi = next((a.text.lower() for a in ids if a.get("IdType") == "doi"), "")
        title = "".join(p.find("./MedlineCitation/Article/ArticleTitle").itertext())
        abstract = " ".join(
            "".join(a.itertext())
            for a in p.findall("./MedlineCitation/Article/Abstract/AbstractText")
        )
        hits.append(
            dict(
                search="pubmed",
                rank=order.index(pmid) + 1,
                title=title,
                doi=doi,
                pmid=pmid,
                abstract=abstract,
            )
        )
    # Reconcile exact identifiers only, never approximate title similarities.
    doi_by_pmid = {h["pmid"]: h["doi"] for h in hits if h["pmid"] and h["doi"]}
    groups = {}
    for h in hits:
        doi = h["doi"] or doi_by_pmid.get(h["pmid"], "")
        key = (
            "doi:" + doi
            if doi
            else "pmid:" + h["pmid"]
            if h["pmid"]
            else "title:" + h["title"].casefold()
        )
        h["record"] = key
        groups.setdefault(key, []).append(h)
    curated = {}
    assessed = {}
    note_inputs = []
    for p in sorted(NOTES.glob("*.md")):
        props = yaml.safe_load(p.read_text().split("\n---\n", 1)[0][4:])
        if props.get("Milch-Sichtung"):
            assessed[props["Quellen-ID"]] = {
                "status": props["Milch-Entscheidung"],
                "reason": props["Milch-Grund"],
                "exclusion_group": props.get("Milch-Ausschlussgruppe", ""),
                "basis": props["Milch-Prüfbasis"],
                "screened_on": props["Milch-Sichtung"],
                "priority": props["Milch-Priorität"],
                "locator": props["Milch-Suchanker"],
                "note": str(p.relative_to(ROOT)),
                "fulltext_status": props.get("Volltextstatus", ""),
                "fulltext_date": props.get("Volltextprüfung", ""),
                "fulltext_finding": props.get("Volltextbefund", ""),
                "fulltext_locator": props.get("Volltextfundstelle", ""),
            }
            note_inputs.append(p)
        if props.get("Milch-Ergänzung") == "2026-10-09":
            curated["doi:" + props["DOI"].lower()] = {
                "status": props["Milch-Status"],
                "count": props["Milch-Zählung"],
                "locator": props["Milch-Fundstelle"],
                "note": str(p.relative_to(ROOT)),
            }
            note_inputs.append(p)
    pilot = {
        "10.1371/journal.pone.0154129",
        "10.1038/cr.2010.80",
        "10.1038/s41597-023-02347-0",
        "10.1186/s12864-021-07964-w",
        "10.1002/jsfa.11607",
    }
    screening = []
    for key, items in sorted(groups.items()):
        row = dict(
            record=key,
            title=items[0]["title"],
            searches="; ".join(sorted({x["search"] for x in items})),
            study=key,
            status="Noch nicht einzeln bewertet",
            count="",
            locator="",
            note="",
            reason="",
            exclusion_group="",
            basis="",
            screened_on="",
            priority="",
            fulltext_status="",
            fulltext_date="",
            fulltext_finding="",
            fulltext_locator="",
        )
        if key in curated:
            row.update(curated[key])
        elif key.removeprefix("doi:") in pilot:
            row["status"] = "Bereits im fünfteiligen Pilotbestand"
        elif key == "doi:10.1101/2023.02.23.529810":
            row.update(
                status="Preprint derselben Turner-Studie",
                study="doi:10.1002/mnfr.202300404",
            )
        elif key == "doi:10.3390/nu16244331":
            row["status"] = "Ziegenmilch; kein Kuhmilchbefund"
        if key in assessed:
            row.update(assessed[key])
        screening.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, rows in [("search_hits.tsv", hits), ("screening.tsv", screening)]:
        with (OUT / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
            w.writeheader()
            w.writerows(rows)
    assert set(assessed) <= set(groups), (
        "Screened note does not match a retrieved record"
    )
    summary = dict(
        retrieval_rows=len(hits),
        unique_records=len(groups),
        duplicate_retrieval_rows=len(hits) - len(groups),
        queries=dict(Counter(h["search"] for h in hits)),
        priority_papers=len(curated),
        title_abstract_assessments=len(assessed),
        statuses=dict(Counter(r["status"] for r in screening)),
        exclusion_reasons=dict(
            Counter(r["exclusion_group"] for r in screening if r["exclusion_group"])
        ),
        scope="Supplementary search only. Title/abstract decisions are not full-text inclusion decisions. Metadata uncertainties and full-text assessment remain open; the ten-study focused comparison is not an exhaustive synthesis. AI-assisted screening is not independent human reading.",
    )
    summary["followup_fulltexts"] = dict(
        Counter(r["fulltext_status"] for r in screening if r["fulltext_status"])
    )
    (OUT / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    inputs = sorted(
        set(
            note_inputs
            + [Path(__file__).resolve()]
            + list(RAW.glob("*.json"))
            + [RAW / "pubmed_abstracts.xml"]
        )
    )
    outputs = [OUT / n for n in ["search_hits.tsv", "screening.tsv", "summary.json"]]
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "inputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in inputs
                },
                "outputs": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in outputs
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fetch frozen PubMed requests using the literature skill; derive a local screening index."""

import argparse, csv, hashlib, json, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
DATA = ROOT / "data/datasets/milk_mirna_inventory/target_screen_20261009"
OUT = ROOT / "output/part2/milk_inventory/target_screen"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fetch(helper, endpoint, params, stem):
    raw = DATA / (stem + (".xml" if endpoint == "efetch" else ".json"))
    receipt = DATA / (stem + ".receipt.json")
    if raw.exists() and receipt.exists():
        saved = json.loads(receipt.read_text())
        if saved.get("ok") and saved.get("sha256") == digest(raw):
            return
        raise ValueError(f"Existing snapshot differs or failed: {raw}")
    request = dict(
        endpoint=endpoint,
        params={"db": "pubmed", **params},
        max_items=100,
        max_depth=5,
        timeout_sec=20,
        save_raw=True,
        raw_output_path=str(raw),
    )
    if endpoint == "efetch":
        request["response_format"] = "xml"
    (DATA / (stem + ".request.json")).write_text(json.dumps(request, indent=2) + "\n")
    result = subprocess.run(
        [sys.executable, str(helper)],
        input=json.dumps(request),
        text=True,
        capture_output=True,
    )
    try:
        response = json.loads(result.stdout)
    except ValueError:
        response = {"ok": False, "error": result.stderr[-1000:]}
    response["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    if raw.exists():
        response["sha256"] = digest(raw)
    receipt.write_text(json.dumps(response, indent=2) + "\n")
    print(stem, "OK" if response.get("ok") else "FAILED", flush=True)
    time.sleep(0.4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fetch",
        type=Path,
        help="Path to the ncbi-entrez skill helper; omitted for offline rebuild",
    )
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    protocol = json.loads((DATA / "protocol.json").read_text())
    entries = []
    all_ids = set()
    for q in protocol["queries"]:
        stem = "search_" + q["candidate"]
        if args.fetch:
            fetch(
                args.fetch,
                "esearch",
                dict(term=q["query"], retmode="json", retmax=100, sort="pub_date"),
                stem,
            )
        path = DATA / (stem + ".json")
        receipt = DATA / (stem + ".receipt.json")
        ok = (
            path.exists()
            and receipt.exists()
            and json.loads(receipt.read_text()).get("ok")
        )
        if ok:
            assert json.loads(receipt.read_text())["sha256"] == digest(path)
            result = json.loads(path.read_text())["esearchresult"]
            ids = result.get("idlist", [])
            all_ids.update(ids)
            row = dict(
                candidate=q["candidate"],
                query=q["query"],
                status="retrieved",
                count=int(result["count"]),
                pmids=";".join(ids),
                warnings=json.dumps(result.get("warninglist", {}), ensure_ascii=False),
                complete=int(result["count"]) == len(ids),
            )
        else:
            row = dict(
                candidate=q["candidate"],
                query=q["query"],
                status="retrieval_failed",
                count="",
                pmids="",
                warnings="",
                complete=False,
            )
        entries.append(row)
    ids = sorted(all_ids, key=int)
    for i in range(0, len(ids), 50):
        if args.fetch:
            fetch(
                args.fetch,
                "efetch",
                dict(id=",".join(ids[i : i + 50]), retmode="xml"),
                f"abstracts_{i // 50:02d}",
            )
    abstracts = []
    for path in sorted(DATA.glob("abstracts_*.xml")):
        receipt = json.loads(path.with_suffix(".receipt.json").read_text())
        assert receipt["ok"] and receipt["sha256"] == digest(path)
        root = ET.fromstring(path.read_bytes())
        for article in root.findall("PubmedArticle"):

            def text(node):
                return (
                    " ".join("".join(node.itertext()).split())
                    if node is not None
                    else ""
                )

            pmid = article.findtext(".//MedlineCitation/PMID")
            doi = ""
            for ident in article.findall("./PubmedData/ArticleIdList/ArticleId"):
                if ident.get("IdType") == "doi":
                    doi = ident.text
            abstracts.append(
                dict(
                    pmid=pmid,
                    doi=doi,
                    title=text(article.find(".//ArticleTitle")),
                    abstract="\n".join(
                        text(n) for n in article.findall(".//AbstractText")
                    ),
                    candidates=";".join(
                        e["candidate"] for e in entries if pmid in e["pmids"].split(";")
                    ),
                    url="https://pubmed.ncbi.nlm.nih.gov/" + pmid + "/",
                )
            )
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows, cols in [
        (
            "searches",
            entries,
            ["candidate", "query", "status", "count", "pmids", "warnings", "complete"],
        ),
        (
            "articles",
            abstracts,
            ["pmid", "doi", "title", "abstract", "candidates", "url"],
        ),
    ]:
        with (args.output / (name + ".tsv")).open("w") as f:
            writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
            writer.writeheader()
            writer.writerows(rows)
    summary = dict(
        candidates=len(entries),
        successful_queries=sum(e["status"] == "retrieved" for e in entries),
        unique_pmids=len(ids),
        articles_fetched=len(abstracts),
        scope=protocol["scope"],
    )
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = dict(
        inputs={
            str(p.relative_to(ROOT)): digest(p)
            for p in sorted(DATA.glob("*"))
            if p.is_file()
        },
        code_sha256=digest(Path(__file__)),
        outputs={
            p.name: digest(p)
            for p in [
                args.output / n
                for n in ["searches.tsv", "articles.tsv", "summary.json"]
            ]
        },
    )
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()

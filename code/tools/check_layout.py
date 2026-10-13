"""Check migrated scientific files, document links and active book pages."""

from pathlib import Path
from html.parser import HTMLParser
import argparse
import hashlib
import json
import re
from urllib.parse import unquote, urlsplit
from book_resources import book_sources

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def check_link(source, target, problems):
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return
    path = unquote(url.path)
    if path.startswith("/"):
        destination = (
            ROOT / "output/book" / path.lstrip("/")
            if source.suffix == ".html"
            else ROOT / path.lstrip("/")
        )
    else:
        destination = source.parent / path
    if (
        destination.suffix == ".html"
        and source.suffix in {".md", ".qmd"}
        and destination.with_suffix(".qmd").is_file()
    ):
        return
    if not destination.exists():
        problems.append(f"{source.relative_to(ROOT)}: {target}")


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links += [
            value for key, value in attrs if key in {"src", "href"} and value
        ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--book-only",
        action="store_true",
        help="Check only active book sources and rendered pages",
    )
    args = parser.parse_args()
    layout = json.loads((ROOT / "code/tools/part2_layout.json").read_text())
    problems = []
    changed_documents = []
    unchanged = 0
    for row in [] if args.book_only else layout["files"]:
        p = ROOT / row["new"]
        if not p.is_file():
            problems.append("Missing: " + row["new"])
            continue
        if sha(p) == row["sha256"]:
            unchanged += 1
            continue
        if row["kind"] in {"report", "prisma"} and p.suffix in {".md", ".qmd"}:
            changed_documents.append(row["new"])
        else:
            problems.append("Unexpected content change: " + row["new"])
    archive = ROOT / layout["original_documents"]
    if not args.book_only and sha(archive) != layout["original_documents_sha256"]:
        problems.append("Original document archive differs")
    docs = [ROOT / "README.md", ROOT / "code/part2/README.md", ROOT / "data/README.md"]
    docs += list((ROOT / "report").rglob("*.qmd"))
    docs += [p for p in (ROOT / "obsidian").rglob("*.md") if ".obsidian" not in p.parts]
    if args.book_only:
        docs = book_sources() + list((ROOT / "report/quarto/part1").rglob("*.qmd"))
        docs = list(dict.fromkeys(docs))
    links = 0
    for p in docs:
        for target in re.findall(r"!?\[[^\]\n]*\]\(([^\s)]+)\)", p.read_text()):
            check_link(p, target, problems)
            links += 1
    pages = [
        (ROOT / "output/book" / p.relative_to(ROOT / "report/quarto")).with_suffix(
            ".html"
        )
        for p in book_sources()
    ]
    stale = list((ROOT / "output/book/part2").glob("*.html"))
    if stale:
        problems.append("Historical Part II HTML pages remain in the Part I book")
    for p in pages:
        if not p.is_file():
            problems.append("Missing book page: " + str(p.relative_to(ROOT)))
            continue
        parser = Links()
        parser.feed(p.read_text())
        for target in parser.links:
            check_link(p, target, problems)
            links += 1
    report = dict(
        passed=not problems,
        files=0 if args.book_only else len(layout["files"]),
        unchanged=unchanged,
        changed_documents=changed_documents,
        documents_checked=len(docs),
        html_pages_checked=len(pages),
        links_checked=links,
        problems=problems,
        scope="Active Part I book links only; no historical-file or biological validation."
        if args.book_only
        else "Layout integrity and file-link resolution; not biological validation. Historical scientific files must be byte-identical.",
    )
    output = ROOT / (
        "output/part1/book_validation.json"
        if args.book_only
        else "output/part2/layout_validation.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if problems:
        raise SystemExit("\n".join(problems))
    print(
        f"PASS: {len(pages)} book pages; {links} links checked; scope={'book only' if args.book_only else 'whole layout'}."
    )


if __name__ == "__main__":
    main()

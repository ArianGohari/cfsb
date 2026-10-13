"""Publish declared files and their local links alongside the rendered book."""

from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import argparse, hashlib, json, re, shutil, os
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
BOOK = ROOT / "output/book"
SKIP = {
    ".venv",
    "__pycache__",
    ".quarto",
    ".git",
    ".obsidian",
    ".amici_model",
    "renv",
    "node_modules",
}


def digest(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").digest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in {"href", "src"} and v)


def targets(text, html=False):
    if html:
        parser = Links()
        parser.feed(text)
        return parser.links
    return re.findall(r"!?\[[^\]\n]*\]\(<?([^\s)>]+)>?\)", text)


def local(source, target):
    u = urlsplit(target)
    if u.scheme or u.netloc or not u.path:
        return None
    p = (
        (ROOT / unquote(u.path).lstrip("/"))
        if u.path.startswith("/")
        else (source.parent / unquote(u.path))
    )
    p = p.resolve()
    if not p.is_relative_to(ROOT) or any(x in SKIP for x in p.relative_to(ROOT).parts):
        return None
    return p


def book_sources():
    # Read the explicit project.render list, not historical QMD files on disk.
    lines = (ROOT / "report/quarto/_quarto.yml").read_text().splitlines()
    start = lines.index("  render:") + 1
    sources = []
    for line in lines[start:]:
        if line.startswith("    - "):
            sources.append(ROOT / "report/quarto" / line[6:].strip())
        elif line.strip():
            break
    if not sources:
        raise ValueError("Book has no explicit render sources")
    return sources


def resources():
    selected = {
        ROOT / p
        for p in json.loads((ROOT / "code/tools/book_resource_paths.json").read_text())
    }
    selected |= {p for p in (ROOT / "report/quarto/assets").rglob("*") if p.is_file()}
    # Follow active chapters and their references; never seed all project notes.
    queue = book_sources()
    for source_page in book_sources():
        page = (BOOK / source_page.relative_to(ROOT / "report/quarto")).with_suffix(
            ".html"
        )
        if not page.is_file():
            continue
        for target in targets(page.read_text(), True):
            u = urlsplit(target)
            if u.scheme or u.netloc or not u.path:
                continue
            q = (
                (BOOK / unquote(u.path).lstrip("/"))
                if u.path.startswith("/")
                else page.parent / unquote(u.path)
            )
            q = q.resolve()
            if q.is_relative_to(BOOK):
                source = ROOT / q.relative_to(BOOK)
                if source.is_file() and source.suffix != ".qmd":
                    selected.add(source)
    queue += list(selected)
    seen = set()
    while queue:
        p = queue.pop()
        if p in seen or not p.is_file():
            continue
        seen.add(p)
        if p.suffix not in {".md", ".qmd", ".base"}:
            continue
        for target in targets(p.read_text(errors="replace")):
            q = local(p, target)
            if q and q.is_file() and q.suffix != ".qmd" and not q.is_relative_to(BOOK):
                selected.add(q)
                queue.append(q)
    return sorted(
        p
        for p in selected
        if p.is_file() and not any(x in SKIP for x in p.relative_to(ROOT).parts)
    )


def normalize_book_links(check=False):
    # Published chapters and source chapters have different directory depths.
    # Point repository resources at their mirrored locations inside the book.
    pages = [
        (BOOK / p.relative_to(ROOT / "report/quarto")).with_suffix(".html")
        for p in book_sources()
    ]
    for page in pages:
        if not page.is_file():
            continue

        def replace(match):
            raw = match[2]
            u = urlsplit(raw)
            if u.scheme or u.netloc or not u.path:
                return match[0]
            path = unquote(u.path)
            stripped = re.sub(r"^(?:\.\./)+", "", path).lstrip("/")
            target = None
            if (
                stripped.split("/")[0]
                in {
                    "data",
                    "output",
                    "obsidian",
                    "code",
                    "archive",
                    "presentation",
                    "report",
                }
                or stripped == "README.md"
            ):
                if (ROOT / stripped).is_file():
                    target = BOOK / stripped
            elif stripped.startswith("notes/"):
                target = BOOK / "report/quarto" / page.parent.name / stripped
            elif (
                stripped.endswith(".qmd")
                and (page.parent / Path(stripped).name).with_suffix(".html").exists()
            ):
                target = (page.parent / Path(stripped).name).with_suffix(".html")
            if target is None:
                return match[0]
            href = quote(os.path.relpath(target, page.parent), safe="/._-")
            if u.query:
                href += "?" + u.query
            if u.fragment:
                href += "#" + u.fragment
            return match[1] + href + match[3]

        before = page.read_text()
        after = re.sub(r'((?:href|src)=")([^"<>]*)(")', replace, before)
        if after != before:
            if check:
                raise ValueError(f"Unnormalized book links: {page}")
            page.write_text(after)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not BOOK.is_dir():
        raise FileNotFoundError(BOOK)
    normalize_book_links(check=args.check)
    copied = 0
    paths = resources()
    for source in paths:
        target = BOOK / source.relative_to(ROOT)
        same = target.is_file() and digest(source) == digest(target)
        if not same and args.check:
            raise ValueError(f"Missing or stale resource: {target}")
        if not same:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied += 1
    print(f"Book resources: {len(paths)} files verified; {copied} copied.")


if __name__ == "__main__":
    main()

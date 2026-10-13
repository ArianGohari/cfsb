#!/usr/bin/env python3
"""Package a passed replay and refresh only its document sources and builds."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED
from replay import STEPS

ROOT = Path(__file__).resolve().parents[3]
REFRESH = [
    str(p.relative_to(ROOT))
    for p in sorted((ROOT / "report/typst").rglob("*"))
    if p.is_file()
]
REFRESH += [
    str(p.relative_to(ROOT))
    for p in sorted((ROOT / "presentation/assets/fonts").glob("*"))
    if p.is_file()
]
REFRESH += [
    "presentation/ergebnisse_mir6517/ergebnisse.typ",
    "presentation/ergebnisse_mir6517/README.md",
    "code/part2/documents/build_report.py",
    "code/part2/documents/build_report_figures.py",
    "code/part2/documents/build_review_summary.py",
    "code/part2/documents/build_presentation.py",
    "code/part2/reproduction/replay.py",
    "code/part2/reproduction/README.md",
    "code/part2/reproduction/package.py",
]

PDFS = [
    "output/pdf/part2_report.pdf",
    "output/presentation/ergebnisse_mir6517.pdf",
    "output/presentation/ergebnisse_mir6517_zusatz.pdf",
]


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run, out = args.replay.resolve(), args.output.resolve()
    summary = json.loads((run / "summary.json").read_text())
    assert summary["status"] == "passed"
    completed = json.loads((run / "steps.json").read_text())
    if [row["command"][-1] for row in completed] != [script for _, script in STEPS]:
        parser.error(
            "Analysis steps have changed; run the current replay before packaging."
        )
    work = run / "workspace"
    for name, digest in json.loads((run / "input_manifest.json").read_text())[
        "inputs"
    ].items():
        assert sha(work / name) == digest, name
    for row in json.loads((run / "comparisons.json").read_text()):
        assert sha(work / row["path"]) == row["replay_sha256"], row["path"]
    out.mkdir(parents=True, exist_ok=False)
    temp_root = ROOT / "output/work"
    temp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="part2_package_", dir=temp_root) as tmp:
        stage = Path(tmp) / "reproduktion"
        shutil.copytree(work, stage)
        changes = []
        for name in REFRESH:
            target = stage / name
            before = sha(target) if target.exists() else None
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
            changes.append(
                dict(path=name, replay_sha256=before, packaged_sha256=sha(target))
            )
        # Older replay copies kept document builders alongside the analyses.
        for name in REFRESH:
            if name.startswith("code/part2/documents/"):
                old = stage / name.replace("/documents/", "/analysis/")
                if old.exists():
                    changes.append(
                        dict(
                            path=str(old.relative_to(stage)),
                            replay_sha256=sha(old),
                            packaged_sha256=None,
                        )
                    )
                    old.unlink()
        receipt = stage / "verification"
        receipt.mkdir()
        for path in run.iterdir():
            if path.name == "workspace":
                continue
            if path.is_dir():
                shutil.copytree(path, receipt / path.name)
            else:
                shutil.copy2(path, receipt / path.name)
        for script in ("build_report.py", "build_presentation.py"):
            with (receipt / (script + ".log")).open("w") as log:
                subprocess.run(
                    [sys.executable, "code/part2/documents/" + script],
                    cwd=stage,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    check=True,
                )
        for name in PDFS:
            assert sha(stage / name) == sha(ROOT / name), name
            shutil.copy2(stage / name, out / Path(name).name)
        refresh = dict(
            scope="Current report and presentation sources rebuilt from the passed replay results "
            "and compared with current PDFs; no analytical results changed.",
            refreshed_sources=changes,
            pdf_hashes={name: sha(stage / name) for name in PDFS},
        )
        write(receipt / "document_refresh.json", refresh)
        write(out / "document_refresh.json", refresh)
        (stage / "README.md").write_text(
            "# Reproduktion Teil II\n\n"
            "Start und Voraussetzungen: [code/part2/reproduction/README.md](code/part2/reproduction/README.md).\n\n"
            f"Dieser Bestand stammt aus dem bestandenen {summary['completed_steps']}-Befehle-Lauf. "
            "Die anschließende redaktionelle Aktualisierung der Reproduktionsangaben steht in "
            "`verification/document_refresh.json`. Originale Eingabehashes und Dateivergleiche "
            "des Gesamtlaufs bleiben unter `verification/` erhalten. "
            "Die aktuellen PDF-Dateien wurden aus dessen Ergebnissen neu gebaut.\n\n"
            "Enthalten sind auch ältere Unterlagen als Herkunftskontext. Maßgeblich für die Abgabe "
            "sind `output/pdf/part2_report.pdf` und `output/presentation/ergebnisse_mir6517.pdf`.\n"
        )
        entries = sorted(p for p in stage.rglob("*") if p.is_file())
        hashes = {str(p.relative_to(stage)): sha(p) for p in entries}
        write(stage / "package_manifest.json", {"files": hashes})
        archive = out / "reproduktion.zip"
        with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as bundle:
            for path in entries + [stage / "package_manifest.json"]:
                bundle.write(path, "reproduktion/" + str(path.relative_to(stage)))
        # Read every member back; check bytes, not merely successful ZIP creation.
        with ZipFile(archive) as bundle:
            for name, digest in hashes.items():
                with bundle.open("reproduktion/" + name) as handle:
                    assert (
                        hashlib.file_digest(handle, "sha256").hexdigest() == digest
                    ), name
            archived_manifest = json.loads(
                bundle.read("reproduktion/package_manifest.json")
            )
            assert archived_manifest["files"] == hashes
        write(
            out / "package_check.json",
            dict(
                replay_status=summary["status"],
                replay_steps=summary["completed_steps"],
                verified_archive_files=len(hashes),
                pdfs_match_current=True,
                archive_bytes=archive.stat().st_size,
                scope="Local Part II submission bundle; no upload or delivery.",
            ),
        )
    print(out)


if __name__ == "__main__":
    main()

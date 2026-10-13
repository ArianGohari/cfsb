"""Run a scientific script in an isolated copy of its original directory layout.

Use its current path below code/ or archive/code/. Scientific scripts remain unchanged.
Changed outputs and a run record are retained under output/runs.
"""

from pathlib import Path
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "code/tools/part2_layout.json"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def stage(destination, layout):
    for row in layout["files"]:
        source = ROOT / row["new"]
        target = destination / row["old"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    if "original_documents" not in layout:
        return
    archive = ROOT / layout["original_documents"]
    if (
        layout.get("original_documents_sha256")
        and sha(archive) != layout["original_documents_sha256"]
    ):
        raise ValueError("Original document archive checksum differs")
    # Old manifests also cover document bytes. Restore those in this copy only.
    with tarfile.open(archive) as tf:
        members = [
            member
            for member in tf.getmembers()
            if layout.get("scope") != "Part I"
            or (
                member.name.startswith(("part1/", "text_mining/"))
                and Path(member.name).suffix in {".md", ".qmd"}
            )
        ]
        tf.extractall(destination, members=members, filter="data")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="New directory for logs and changed outputs"
    )
    parser.add_argument(
        "--cwd",
        default=".",
        help="Working directory within the reconstructed historical workspace",
    )
    parser.add_argument(
        "script",
        help="Current script path, e.g. archive/code/tools/report/replay.py or archive/code/part2/model/baseline/replay.py",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parser.add_argument(
        "--layout", type=Path, help="Optional historical layout manifest"
    )
    args = parser.parse_args()
    script = (ROOT / args.script).resolve().relative_to(ROOT).as_posix()
    is_part1 = script.startswith("code/part1/")
    layout_path = args.layout or (
        ROOT / "code/tools/part1_layout.json" if is_part1 else LAYOUT
    )
    layout = json.loads(layout_path.read_text())
    for row in layout["files"]:
        row.setdefault("kind", "code" if row["new"].startswith("code/") else "data")
    mapping = {r["new"]: r for r in layout["files"]}
    if script not in mapping or mapping[script]["kind"] != "code":
        parser.error("Script must be listed as code in code/tools/part2_layout.json")
    old = mapping[script]["old"]
    extension = Path(script).suffix
    if extension not in {".py", ".jl", ".R", ".sh"}:
        parser.error("Supported scripts: .py, .jl, .R, .sh")
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + uuid4().hex[:8]
    )
    output = args.output or ROOT / "output/runs" / stamp
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    record = dict(
        script=script,
        original_path=old,
        arguments=args.args,
        layout_sha256=sha(layout_path),
        python=sys.version,
        inputs={r["new"]: sha(ROOT / r["new"]) for r in layout["files"]},
        note="Original document bytes restored for historical replay; current code and data used. Canonical outputs are never overwritten.",
    )
    with tempfile.TemporaryDirectory(prefix="cfsb-layout-") as temp:
        work = Path(temp).resolve()
        stage(work, layout)
        baseline = {
            p.relative_to(work).as_posix(): sha(p)
            for p in work.rglob("*")
            if p.is_file()
        }
        command = {
            ".py": [sys.executable],
            ".R": ["Rscript"],
            ".sh": ["bash"],
            ".jl": ["julia", "--startup-file=no"]
            + ([] if is_part1 else [f"--project={work}/part2/step7/model"]),
        }[extension]
        command += [str(work / old), *args.args]
        working = (work / args.cwd).resolve()
        if not working.is_relative_to(work) or not working.is_dir():
            raise ValueError(
                "--cwd must name a directory inside the reconstructed workspace"
            )
        print("Running:", " ".join(command), flush=True)
        with (
            (output / "stdout.log").open("w") as stdout,
            (output / "stderr.log").open("w") as stderr,
        ):
            result = subprocess.run(
                command,
                cwd=working,
                stdout=stdout,
                stderr=stderr,
                env={**os.environ, "PYTHONHASHSEED": "0"},
            )
        record["exit_code"] = result.returncode
        record["changed_outputs"] = []
        old_to_new = {r["old"]: r["new"] for r in layout["files"]}
        output_roots = layout.get("output_roots", ["part1" if is_part1 else "part2"])
        for p in sorted(p for base in output_roots for p in (work / base).rglob("*")):
            if not p.is_file() or any(
                x.startswith(".") or x == "__pycache__"
                for x in p.relative_to(work).parts
            ):
                continue
            relative = p.relative_to(work).as_posix()
            checksum = sha(p)
            if checksum == baseline.get(relative):
                continue
            target = output / "files" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
            record["changed_outputs"].append(
                dict(
                    path=relative,
                    canonical_path=old_to_new.get(relative),
                    sha256=checksum,
                )
            )
    (output / "run.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    )
    for name in ("stdout.log", "stderr.log"):
        text = (output / name).read_text()
        if text:
            print(text, end="")
    print("Run record:", output / "run.json")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

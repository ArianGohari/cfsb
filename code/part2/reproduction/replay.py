#!/usr/bin/env python3
"""Rebuild the current miR-6517 analysis in a new, independent file tree."""

from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
LIT = "code/part2/literature/milk_inventory/"
OMICS = "code/part2/analysis/omics/"
MODEL = "code/part2/model/pfkl/"
# Order is explicit: no old derived result is copied to fill a missing dependency.
STEPS = [("python", "code/tools/export_source_base.py")]
STEPS += [
    ("python", LIT + p + ".py")
    for p in [
        "build",
        "verify_pdf",
        "compare_sequences",
        "audit_annotations",
        "plot_human_comparison",
        "plot_paper_support",
        "scan_human_seeds",
        "audit_reported_targets",
        "search_targets",
        "export_target_screen",
        "export_processing_pilot",
        "review_processing_supplements",
        "audit_chen_shome",
        "extract_ali_tables",
        "extend_published_lists",
        "plot_study_counts",
        "build_candidate_evidence",
        "review_bae_reporter",
        "review_additional_candidates",
        "review_pfkl",
        "review_casp3",
        "review_casp3_expression",
        "export_extension_search",
        "export_report_scope",
        "extract_pfkl_kinetics",
        "review_pfkl_turnover",
    ]
]
STEPS += [
    ("python", LIT + "review_pfkp_isoform.py"),
    ("python", LIT + "review_pgam1_dlat.py"),
    ("python", "code/part2/analysis/build_pathway_network.py"),
]
STEPS += [
    ("python", OMICS + p + ".py")
    for p in [
        "review_pfkl_rna_decay",
        "review_doherty_turnover",
        "review_chen_turnover",
    ]
]
STEPS += [
    ("python", MODEL + "fit_enzyme.py"),
    ("python", MODEL + "check_enzyme.py"),
    ("julia", MODEL + "simulate_regulation.jl"),
    ("python", MODEL + "summarize_regulation.py"),
    ("python", MODEL + "assess_regulation_claims.py"),
    ("python", MODEL + "check_identifiability.py"),
    ("python", "code/part2/documents/build_review_summary.py"),
    ("python", "code/part2/documents/build_report.py"),
    ("python", "code/part2/documents/build_presentation.py"),
]
SEEDS = ["output/part2/review_summary/bibliography_sources.json"]
REQUIRED = [
    "output/part2/milk_inventory/sequence_comparison/sequence_support.tsv",
    "output/part2/milk_inventory/human_seed_screen/sites.tsv",
    "output/part2/milk_inventory/candidate_evidence/target_evidence.tsv",
    "output/part2/review_scope/deferred_records.tsv",
    "output/part2/mir6517_pathway/network.svg",
    "output/part2/pfkl_enzyme/fit.json",
    "output/part2/pfkl_regulation/trajectories.tsv",
    "output/part2/pfkl_regulation_claims/comparisons.tsv",
    "output/part2/pfkl_rna_decay/summary.json",
    "output/part2/doherty_turnover/summary.json",
    "output/part2/chen_turnover/summary.json",
    "output/part2/pfkl_identifiability/summary.json",
    "output/pdf/part2_report.pdf",
    "output/presentation/ergebnisse_mir6517.pdf",
    "output/presentation/ergebnisse_mir6517_zusatz.pdf",
]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def files(path):
    return sorted(
        p
        for p in path.rglob("*")
        if p.is_file() and not {".venv", "__pycache__", ".DS_Store"} & set(p.parts)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, help="New directory; must not already exist"
    )
    parser.add_argument(
        "--list", action="store_true", help="Show ordered commands without running"
    )
    args = parser.parse_args()
    if args.list:
        for i, (tool, script) in enumerate(STEPS, 1):
            print(i, tool, script)
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    dest = (
        args.output or ROOT / "output/reproduction" / ("mir6517_" + stamp)
    ).resolve()
    dest.mkdir(parents=True, exist_ok=False)
    work = dest / "workspace"
    work.mkdir()
    logs = dest / "logs"
    logs.mkdir()
    env = os.environ.copy()
    env.update(MPLBACKEND="Agg", JULIA_PKG_OFFLINE="true", PYTHONDONTWRITEBYTECODE="1")
    versions = {"python": sys.version, "python_executable": sys.executable}
    for tool in ["julia", "typst", "dot", "pdftotext"]:
        if not shutil.which(tool):
            raise RuntimeError(f"Missing executable: {tool}")
        flag = "-V" if tool == "dot" else "-v" if tool == "pdftotext" else "--version"
        result = subprocess.run(
            [tool, flag], capture_output=True, text=True, check=True
        )
        versions[tool] = (result.stdout + result.stderr).strip()
    import importlib.metadata

    versions["python_packages"] = {
        p: importlib.metadata.version(p)
        for p in [
            "numpy",
            "scipy",
            "matplotlib",
            "openpyxl",
            "PyYAML",
            "fonttools",
            "kiwisolver",
            "pillow",
        ]
    }
    write(dest / "environment.json", versions)
    print("Working copy:", work, flush=True)
    # Independent copies, never symlinks or hardlinks to writable project files.
    ignore = shutil.ignore_patterns(".venv", "__pycache__", ".DS_Store")
    for relative in [
        "data",
        "obsidian/Projekt",
        "code/part2",
        "code/tools",
        "report/typst",
        "presentation/ergebnisse_mir6517",
        "presentation/assets/fonts",
    ]:
        shutil.copytree(ROOT / relative, work / relative, ignore=ignore)
    for relative in SEEDS:
        target = work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    inputs = {str(p.relative_to(work)): sha(p) for p in files(work)}
    original_outputs = {
        str(p.relative_to(ROOT)): sha(p)
        for base in [
            ROOT / "output/part2",
            ROOT / "output/pdf",
            ROOT / "output/presentation",
        ]
        for p in files(base)
    }
    write(
        dest / "input_manifest.json",
        {
            "inputs": inputs,
            "copied_editorial_inputs": SEEDS,
            "policy": "Saved queries, curation, references and published tables are inputs. "
            "No raw sequencing, new search, OCR or independent rescreening. No previous computed outputs copied.",
        },
    )
    write(dest / "baseline_outputs.json", original_outputs)
    records = []
    failure = None
    for i, (tool, script) in enumerate(STEPS, 1):
        command = (
            [sys.executable, script]
            if tool == "python"
            else ["julia", "--startup-file=no", "--project=code/part2/model", script]
        )
        log = logs / f"{i:02d}_{Path(script).stem}.log"
        print(f"[{i}/{len(STEPS)}] {script}", flush=True)
        start = time.monotonic()
        with log.open("w") as stream:
            result = subprocess.run(
                command, cwd=work, env=env, stdout=stream, stderr=subprocess.STDOUT
            )
        records.append(
            dict(
                step=i,
                command=command,
                returncode=result.returncode,
                seconds=round(time.monotonic() - start, 3),
                log=str(log.relative_to(dest)),
            )
        )
        write(dest / "steps.json", records)
        if result.returncode:
            failure = f"{script} exited {result.returncode}"
            print(log.read_text()[-6000:], flush=True)
            break
    input_changes = [
        name for name, digest in inputs.items() if sha(work / name) != digest
    ]
    original_input_changes = [
        name for name, digest in inputs.items() if sha(ROOT / name) != digest
    ]
    original_output_changes = [
        name
        for name, digest in original_outputs.items()
        if not (ROOT / name).exists() or sha(ROOT / name) != digest
    ]
    policy_path = Path(__file__).with_name("documented_curation_differences.json")
    policy = json.loads(policy_path.read_text())
    reviewed = {
        r["path"]: (r["baseline_sha256"], r["replay_sha256"]) for r in policy["files"]
    }
    write(dest / "documented_curation_differences.json", policy)
    comparisons = []
    for path in files(work / "output"):
        name = str(path.relative_to(work))
        if name in SEEDS:
            continue
        digest = sha(path)
        baseline = original_outputs.get(name)
        # Manifests record changed note hashes and execution environment, not scientific results.
        metadata = "manifest" in path.name.lower() or path.name == "sessionInfo.txt"
        status = (
            "identical"
            if baseline == digest
            else "new"
            if baseline is None
            else "metadata_changed"
            if metadata
            else "changed"
        )
        if status == "changed" and reviewed.get(name) == (baseline, digest):
            status = next(
                row.get("reviewed_status", "documented_curation_update")
                for row in policy["files"]
                if row["path"] == name
            )
        comparisons.append(
            dict(
                path=name, status=status, baseline_sha256=baseline, replay_sha256=digest
            )
        )
    write(dest / "comparisons.json", comparisons)
    missing = [name for name in REQUIRED if not (work / name).is_file()]
    counts = dict(Counter(r["status"] for r in comparisons))
    status = (
        "failed"
        if failure
        or input_changes
        or original_input_changes
        or original_output_changes
        or missing
        else ("differences_require_review" if counts.get("changed") else "passed")
    )
    summary = dict(
        status=status,
        completed_steps=len(records),
        planned_steps=len(STEPS),
        failure=failure,
        file_comparison=counts,
        missing_required=missing,
        copied_input_changes=input_changes,
        original_input_changes=original_input_changes,
        original_output_changes=original_output_changes,
        limitations="Technical offline replay of saved evidence and curation, not an independent literature or biological validation.",
    )
    write(dest / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    print("Results:", dest, flush=True)
    if status != "passed":
        sys.exit(1)


if __name__ == "__main__":
    main()

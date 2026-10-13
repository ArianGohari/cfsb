"""Convert the coffee PDF with Tesseract preprocessing and Marker Markdown extraction.

Run directly: python3 code/tools/convert_coffee_example.py
The original PDF remains unchanged. Output is not overwritten.
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[2]
inputs = [
    p
    for p in (ROOT / "data/sources/course/musterloesung_kaffee").glob("*.pdf")
    if unicodedata.normalize("NFC", p.name) == "Musterloesung.pdf"
]
assert len(inputs) == 1, (
    "Expected one Musterlösung.pdf in data/sources/course/musterloesung_kaffee"
)
source = inputs[0]
output = ROOT / "data/sources/course"
target = output / "musterloesung_kaffee"
assert not (target / "musterloesung_kaffee.md").exists(), (
    f"Marker output already exists: {target}"
)
output.mkdir(parents=True, exist_ok=True)
working = ROOT / "output/work/marker-kaffee/downsampled/musterloesung_kaffee.pdf"
working.parent.mkdir(parents=True, exist_ok=True)
provenance = ROOT / "data/sources/course/musterloesung_kaffee"
provenance.mkdir(parents=True, exist_ok=True)
log = provenance / "musterloesung_kaffee_conversion.log"
manifest = provenance / "musterloesung_kaffee_conversion.json"
marker = shutil.which("marker_single")
assert marker, "marker_single not found"
marker_python = Path(marker).resolve().parent / "python"
version = subprocess.check_output(
    [
        str(marker_python),
        "-c",
        'import importlib.metadata; print(importlib.metadata.version("marker-pdf"))',
    ],
    text=True,
).strip()
pages = int(
    re.search(
        r"^Pages:\s+(\d+)",
        subprocess.check_output(["pdfinfo", str(source)], text=True),
        re.M,
    )[1]
)


def sha(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


started = datetime.now(timezone.utc).isoformat()
start = time.monotonic()
gs = [
    "gs",
    "-sDEVICE=pdfwrite",
    "-dCompatibilityLevel=1.7",
    "-dNOPAUSE",
    "-dBATCH",
    "-dSAFER",
    "-dQUIET",
    "-dDownsampleColorImages=true",
    "-dColorImageResolution=240",
    "-dColorImageDownsampleType=/Bicubic",
    "-dDownsampleGrayImages=true",
    "-dGrayImageResolution=240",
    "-dGrayImageDownsampleType=/Bicubic",
    "-dDownsampleMonoImages=true",
    "-dMonoImageResolution=300",
    f"-sOutputFile={working}",
    str(source),
]
print("Preparing 240 dpi working copy", flush=True)
subprocess.run(gs, check=True, cwd=ROOT)
raster = working.parent / "pages"
raster.mkdir(exist_ok=True)
print("Rendering pages for Tesseract", flush=True)
render = ["pdftoppm", "-r", "240", "-png", str(working), str(raster / "page")]
subprocess.run(render, check=True)
images = sorted(raster.glob("page-*.png"))
assert len(images) == pages
ocr_commands = []


def ocr(image):
    cmd = [
        "tesseract",
        str(image),
        str(image.with_suffix("")),
        "-l",
        "eng",
        "--dpi",
        "240",
        "pdf",
    ]
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "OMP_THREAD_LIMIT": "2"},
    )
    print(f"OCR complete: {image.name}", flush=True)
    return cmd


with ThreadPoolExecutor(max_workers=2) as pool:
    ocr_commands = list(pool.map(ocr, images))
ocr_pdf = working.parent / "ocr_input" / "musterloesung_kaffee.pdf"
ocr_pdf.parent.mkdir(exist_ok=True)
if ocr_pdf.exists():
    ocr_pdf.unlink()
merge = [
    "pdfunite",
    *[str(image.with_suffix(".pdf")) for image in images],
    str(ocr_pdf),
]
subprocess.run(merge, check=True)
command = [
    marker,
    str(ocr_pdf),
    "--output_dir",
    str(output),
    "--output_format",
    "markdown",
    "--disable_multiprocessing",
    "--layout_batch_size",
    "1",
    "--recognition_batch_size",
    "1",
    "--detection_batch_size",
    "1",
    "--paginate_output",
    "--disable_ocr",
]
record = dict(
    source=str(source.relative_to(ROOT)),
    source_sha256=sha(source),
    source_pages=pages,
    source_bytes=source.stat().st_size,
    marker_version=version,
    started_utc=started,
    preprocessing_command=gs,
    ghostscript_version=subprocess.check_output(["gs", "--version"], text=True).strip(),
    working_pdf=str(working.relative_to(ROOT)),
    working_pdf_sha256=sha(working),
    command=command,
    environment={"TORCH_DEVICE": "cpu"},
    use_llm=False,
    ocr="Tesseract eng at 240 dpi creates a new text layer; Marker structures this with its own OCR disabled.",
    tesseract_version=subprocess.check_output(
        ["tesseract", "--version"], text=True
    ).splitlines()[0],
    rendering_command=render,
    ocr_commands=ocr_commands,
    merge_command=merge,
    ocr_pdf_sha256=sha(ocr_pdf),
    ocr_threads=2,
    ocr_workers=2,
    prior_attempts=[
        "musterloesung_kaffee_attempt1.json",
        "musterloesung_kaffee_attempt2.json",
        "musterloesung_kaffee_attempt3.json",
    ],
)
print("Running Marker on the repaired text layer", flush=True)
with log.open("w") as f:
    result = subprocess.run(
        command,
        stdout=f,
        stderr=subprocess.STDOUT,
        cwd=ROOT,
        env={**os.environ, **record["environment"]},
    )
record.update(
    exit_code=result.returncode,
    elapsed_seconds=round(time.monotonic() - start, 2),
    finished_utc=datetime.now(timezone.utc).isoformat(),
)
record["outputs"] = (
    [
        dict(path=str(p.relative_to(ROOT)), bytes=p.stat().st_size, sha256=sha(p))
        for p in sorted(target.rglob("*"))
        if p.is_file()
    ]
    if target.exists()
    else []
)
manifest.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(
    json.dumps(
        {
            "exit_code": result.returncode,
            "output": str(target),
            "elapsed_seconds": record["elapsed_seconds"],
        },
        indent=2,
    )
)
raise SystemExit(result.returncode)

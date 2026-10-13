"""Read-only SBML validation and explicit, cached public BioModels requests."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import libsbml

HERE = Path(__file__).resolve().parent
ORIGINALS = HERE.parent.parent / "task1" / "sbml"
MODELS = {
    "BIOMD0000000170": ORIGINALS / "BIOMD0000000170_url.xml",
    "BIOMD0000001006": ORIGINALS / "Ciliberto2005.xml",
}
BASE = "https://www.ebi.ac.uk/biomodels"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def validate(path):
    raw = path.read_bytes()
    doc = libsbml.readSBMLFromString(raw.decode("utf-8"))
    read_count = doc.getNumErrors()
    model = doc.getModel()
    # Keep parse diagnostics and consistency diagnostics separate, without filtering units.
    consistency_count = doc.checkConsistency() if model is not None else None
    issues = []
    for i in range(doc.getNumErrors()):
        error = doc.getError(i)
        issues.append({
            "phase": "read" if i < read_count else "consistency",
            "id": error.getErrorId(), "severity": error.getSeverityAsString(),
            "category": error.getCategoryAsString(), "line": error.getLine(),
            "message": error.getMessage().strip(),
        })
    result = {
        "file": str(path), "sha256": sha256(raw), "bytes": len(raw),
        "level": doc.getLevel(), "version": doc.getVersion(),
        "read_diagnostics": read_count, "checkConsistency_return": consistency_count,
        "severity_counts": dict(Counter(x["severity"] for x in issues)),
        "category_counts": dict(Counter(x["category"] for x in issues)),
        "issues": issues,
        "ok": model is not None and not any(
            doc.getError(i).getSeverity() >= libsbml.LIBSBML_SEV_ERROR
            for i in range(doc.getNumErrors())
        ),
    }
    if model is not None:
        result["model_id"] = model.getId()
        result["model_name"] = model.getName()
        result["inventory"] = {
            "compartments": model.getNumCompartments(),
            "species": model.getNumSpecies(),
            "reactions": model.getNumReactions(),
            "parameters_global": model.getNumParameters(),
            "parameters_local": sum(
                (r.getKineticLaw().getNumLocalParameters() if doc.getLevel() >= 3
                 else r.getKineticLaw().getNumParameters())
                for r in model.getListOfReactions() if r.isSetKineticLaw()
            ),
            "rules": model.getNumRules(),
            "assignment_rules": sum(r.isAssignment() for r in model.getListOfRules()),
            "rate_rules": sum(r.isRate() for r in model.getListOfRules()),
            "algebraic_rules": sum(r.isAlgebraic() for r in model.getListOfRules()),
            "events": model.getNumEvents(),
            "initial_assignments": model.getNumInitialAssignments(),
            "function_definitions": model.getNumFunctionDefinitions(),
            "unit_definitions": model.getNumUnitDefinitions(),
            "constraints": model.getNumConstraints(),
        }
        result["species"] = [{"id": s.getId(), "name": s.getName()} for s in model.getListOfSpecies()]
    return result


def request(url, destination):
    """Cache exact response bytes, including HTTP failures; never silently reuse a cache."""
    meta = {"url": url, "requested_at_utc": now(), "status": None}
    raw = b""
    try:
        try:
            response = urlopen(Request(url, headers={"User-Agent": "task3a-sbml/0.1", "Accept": "application/json, application/xml;q=0.9, */*;q=0.1"}), timeout=60)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            meta.update(status=response.code, final_url=response.geturl(), headers=dict(response.headers.items()))
    except (URLError, TimeoutError, OSError) as error:
        meta["error"] = str(error)
    meta.update(completed_at_utc=now(), bytes=len(raw), sha256=sha256(raw), body=destination.name)
    destination.write_bytes(raw)
    save_json(destination.with_suffix(destination.suffix + ".json"), meta)
    return meta, raw


def fetch():
    directory = HERE / "data" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    directory.mkdir(parents=True, exist_ok=False)
    records = []
    for record_id, original in MODELS.items():
        result = {"record": record_id, "original_sha256": sha256(original.read_bytes()), "requests": []}
        for endpoint, suffix in [(f"/{record_id}?format=json", "metadata"), (f"/model/files/{record_id}?format=json", "files")]:
            meta, raw = request(BASE + endpoint, directory / f"{record_id}_{suffix}.raw")
            result["requests"].append(meta)
            if suffix != "files" or meta["status"] != 200:
                continue
            try:
                listing = json.loads(raw)
                names = [f["name"] for f in listing["main"] if f["name"].lower().endswith((".xml", ".sbml"))]
            except (ValueError, KeyError, TypeError) as error:
                result["listing_error"] = str(error)
                continue
            result["downloads"] = []
            for index, name in enumerate(names):
                target = directory / f"{record_id}_current_{index}.xml"
                meta, raw = request(BASE + f"/model/download/{record_id}?" + urlencode({"filename": name}), target)
                result["requests"].append(meta)
                download = {"remote_filename": name, "file": target.name,
                            "same_bytes_as_original": sha256(raw) == result["original_sha256"],
                            "original_is_current_plus_lf": original.read_bytes() == raw + b"\n",
                            "same_after_crlf_to_lf": raw.replace(b"\r\n", b"\n") == original.read_bytes().replace(b"\r\n", b"\n")}
                if meta["status"] == 200:
                    try:
                        download["validation"] = validate(target)
                    except UnicodeError as error:
                        download["validation_error"] = str(error)
                result["downloads"].append(download)
        result["ok"] = (
            all(r["status"] == 200 for r in result["requests"])
            and bool(result.get("downloads"))
            and all(d.get("validation", {}).get("ok", False) for d in result.get("downloads", []))
        )
        records.append(result)
    report = {"records": records, "ok": all(r["ok"] for r in records)}
    save_json(directory / "summary.json", report)
    print(directory / "summary.json")
    return 0 if report["ok"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "fetch"])
    parser.add_argument("files", nargs="*", type=Path, help="Optional SBML inputs for validate")
    parser.add_argument("--output", type=Path, default=HERE / "validation.json", help="Validation report destination")
    args = parser.parse_args()
    if args.command == "fetch":
        if args.files:
            parser.error("fetch takes no files")
        return fetch()
    results = [validate(p) for p in (args.files or MODELS.values())]
    report = {"checked_at_utc": now(), "python": platform.python_version(),
              "libsbml": libsbml.getLibSBMLDottedVersion(), "models": results}
    save_json(args.output, report)
    for result in results:
        print(Path(result["file"]).name, "OK" if result["ok"] else "FAIL",
              result["severity_counts"], result.get("inventory", {}))
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

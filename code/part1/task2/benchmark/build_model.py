#!/usr/bin/env python3
"""Compile the published pan-cancer SBML model with the current AMICI API."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sys
import time
from pathlib import Path

import amici
import libsbml
import pandas as pd


TASK_ROOT = Path(__file__).resolve().parents[1]
COMMIT = "6916101b6df55ca97f5522a999c0dc499d6e4362"
SOURCE_ROOT = TASK_ROOT / ".cache" / "upstream" / f"reference_simulator-{COMMIT}"
MODEL_DIR = (TASK_ROOT / ".amici_model").resolve()
MODEL_NAME = "ERBB_RAS_AKT_Drugs"
METADATA = TASK_ROOT / "benchmark" / "results" / "build_metadata.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    sbml_path = SOURCE_ROOT / "CS_Signalling_ERBB_RAS_AKT_modified.xml"
    conditions_path = SOURCE_ROOT / "conditions_petab.tsv"
    if not sbml_path.exists() or not conditions_path.exists():
        raise SystemExit("Upstream files are missing. Run benchmark/fetch_upstream.py first.")

    module_file = next((MODEL_DIR / MODEL_NAME).glob(f"_{MODEL_NAME}*.so"), None)
    started = time.perf_counter()
    reused = module_file is not None
    if not reused:
        if MODEL_DIR.exists():
            shutil.rmtree(MODEL_DIR)
        MODEL_DIR.mkdir(parents=True)
        os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"]

        importer = amici.SbmlImporter(sbml_path)
        observation_model = amici.assignment_rules_to_observables(
            importer.sbml_model,
            filter_function=lambda parameter: parameter.getName()
            == "observable_proliferation",
        )
        conditions = pd.read_csv(conditions_path, sep="\t")
        fixed_parameters = [
            column
            for column in conditions.columns
            if importer.sbml_model.getParameter(column)
        ]
        importer.sbml2amici(
            MODEL_NAME,
            str(MODEL_DIR),
            fixed_parameters=fixed_parameters,
            observation_model=observation_model,
            verbose=False,
            generate_sensitivity_code=False,
        )

    sys.path.insert(0, str(MODEL_DIR / MODEL_NAME))
    model_module = __import__(MODEL_NAME)
    model = model_module.get_model()
    document = libsbml.readSBMLFromFile(str(sbml_path))

    record = {
        "reused_compiled_model": reused,
        "elapsed_seconds": time.perf_counter() - started,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "amici": amici.__version__,
        "libsbml": libsbml.getLibSBMLDottedVersion(),
        "upstream_commit": COMMIT,
        "sbml_sha256": sha256(sbml_path),
        "conditions_sha256": sha256(conditions_path),
        "sbml_species": document.getModel().getNumSpecies(),
        "sbml_reactions": document.getModel().getNumReactions(),
        "compiled_states": len(model.get_state_ids()),
        "free_parameters": len(model.get_free_parameter_ids()),
        "fixed_parameters": len(model.get_fixed_parameter_ids()),
        "observables": list(model.get_observable_ids()),
    }
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()


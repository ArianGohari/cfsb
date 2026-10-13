#!/usr/bin/env python3
"""Verify the new Task 1 numerical and text-mining artifacts."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

wang = json.loads((HERE / "wang_reproduction/results.json").read_text())
assert wang["numerical_transition_bracket_h"][0] <= wang["published_tau0_h"] <= wang["numerical_transition_bracket_h"][1]
assert max(abs(a - b) for a, b in zip(wang["equilibrium_tau0"], wang["published_equilibrium"])) < 5e-5
assert abs(wang["tau9_mean_period_h"] - 24.0) < 0.05
assert wang["tau9_period_count"] >= 10
ET.parse(HERE / "wang_reproduction/wang_dde_reproduction.svg")

evaluation = json.loads((ROOT / "text_mining/data/runs/task1-offline-eval-20260924/evaluation.json").read_text())
local_evaluation = json.loads((HERE / "evaluation_20260924/evaluation.json").read_text())
assert local_evaluation == evaluation
assert json.loads((HERE / "evaluation_20260924/evidence_graph.json").read_text()) == evaluation["graph"]
test = evaluation["test"]
assert test["entities"]["tp"] == 17 and test["entities"]["fp"] == 0 and test["entities"]["fn"] == 0
assert test["relations"]["tp"] == 4 and test["relations"]["fp"] == 0 and test["relations"]["fn"] == 1
assert test["relations"]["positive_sentence_abstentions"] == 1
assert test["relations"]["negative_sentence_correct_abstentions"] == 3
assert len(evaluation["graph"]["edges"]) == 4
print("Task 1 artifacts verified")

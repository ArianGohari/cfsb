#!/usr/bin/env python3
"""Small offline audit for Task 1(g); deterministic rules, no model or network calls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "text_mining/data/runs/task1-offline-eval-20260924"

ALIASES = {
    "PER2": r"(?:hPER2|mPER2|PER2|Period\s*2)",
    "TP53": r"(?:h?p53|TP53|human p53)",
    "MDM2": r"(?:MDM2|Mdm2|Hdm2)",
}
ALIAS_UNION = "|".join(f"(?P<{key}>{value})" for key, value in ALIASES.items())
UNCERTAIN = re.compile(
    r"\b(?:hypothes\w*|speculat\w*|possible|possibly|might|may|could|would|plausible|propos\w*)\b",
    re.I,
)
OWN_EVIDENCE = re.compile(
    r"\b(?:we (?:found|show|showed|established|determined|measured|examined|investigated|tested)|"
    r"our (?:results|data|findings)|results show|analysis .* showed|finding established)\b",
    re.I,
)
INVESTIGATION = re.compile(
    r"\b(?:we (?:examined|investigated|tested|measured|monitored|performed|used)|"
    r"cells were|assays? (?:were|was)|analysis .* showed)\b",
    re.I,
)
REVIEW = re.compile(r"\b(?:this |the )?review\b", re.I)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def verify_source(record: dict) -> dict:
    path = ROOT / "part1/task1" / record["source"]
    source = path.read_text(encoding="utf-8")
    needle = record["text"]
    count = source.count(needle)
    if count != 1:
        raise ValueError(f"{record['id']}: expected one exact source occurrence, found {count}")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "offset": source.index(needle),
        "length": len(needle),
    }


def entities(text: str) -> set[str]:
    found = set()
    for match in re.finditer(ALIAS_UNION, text, re.I):
        found.add(next(key for key, value in match.groupdict().items() if value is not None))
    return found


def screen(text: str) -> str:
    if REVIEW.search(text):
        return "exclude"
    present = entities(text)
    topic = "PER2" in present and bool({"TP53", "MDM2"} & present)
    if not topic:
        return "unclear"
    if UNCERTAIN.search(text) and not OWN_EVIDENCE.search(text) and not INVESTIGATION.search(text):
        return "unclear"
    return "include" if OWN_EVIDENCE.search(text) or INVESTIGATION.search(text) else "unclear"


def _alias(key: str) -> str:
    return rf"(?P<{key.lower()}>{ALIASES[key]})"


def relations(text: str) -> set[tuple[str, str, str]]:
    if UNCERTAIN.search(text) and not OWN_EVIDENCE.search(text):
        return set()
    result: set[tuple[str, str, str]] = set()
    patterns = [
        ("PER2", "BINDS", "TP53", rf"{_alias('PER2')}\b.{{0,45}}?\b(?:directly )?binds?\b.{{0,60}}?{_alias('TP53')}"),
        ("PER2", "BINDS", "MDM2", rf"{_alias('PER2')}\b.{{0,55}}?\b(?:interact\w*|binds?)\b.{{0,70}}?\b(?:with )?{_alias('MDM2')}"),
        ("PER2", "STABILIZES", "TP53", rf"{_alias('PER2')}\b.{{0,45}}?\bpromotes?\b.{{0,25}}?{_alias('TP53')}\b.{{0,20}}?\bstability\b"),
        ("MDM2", "UBIQUITINATES", "PER2", rf"{_alias('MDM2')}\b.{{0,90}}?\b(?:responsible for|promotes?|cataly\w*)\b.{{0,30}}?{_alias('PER2')}\b.{{0,15}}?\bubiquit(?:y|i)lation\b"),
        ("MDM2", "PROMOTES_DEGRADATION", "PER2", rf"{_alias('MDM2')}\b.{{0,50}}?\b(?:targets?|promotes?)\b.{{0,25}}?{_alias('PER2')}\b.{{0,15}}?\b(?:for )?degradation\b"),
    ]
    for subject, predicate, obj, pattern in patterns:
        if re.search(pattern, text, re.I):
            result.add((subject, predicate, obj))
    return result


def prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0 if precision is not None and recall is not None else None
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate(path: Path) -> dict:
    dataset = json.loads(path.read_text(encoding="utf-8"))
    source_provenance = {}
    screening_rows = []
    for record in dataset["screening"]:
        source_provenance[record["id"]] = verify_source(record)
        predicted = screen(record["text"])
        screening_rows.append({"id": record["id"], "expected": record["expected"], "predicted": predicted})
    labels = ("include", "exclude", "unclear")
    screening = {
        label: {
            "tp": sum(r["expected"] == label and r["predicted"] == label for r in screening_rows),
            "fp": sum(r["expected"] != label and r["predicted"] == label for r in screening_rows),
            "fn": sum(r["expected"] == label and r["predicted"] != label for r in screening_rows),
        }
        for label in labels
    }
    relation_rows = []
    entity_tp = entity_fp = entity_fn = rel_tp = rel_fp = rel_fn = 0
    positive_abstentions = negative_correct_abstentions = 0
    for record in dataset["relations"]:
        source_provenance[record["id"]] = verify_source(record)
        expected_entities = set(record["entities"])
        predicted_entities = entities(record["text"])
        expected_relations = {tuple(value) for value in record["relations"]}
        predicted_relations = relations(record["text"])
        entity_tp += len(expected_entities & predicted_entities)
        entity_fp += len(predicted_entities - expected_entities)
        entity_fn += len(expected_entities - predicted_entities)
        rel_tp += len(expected_relations & predicted_relations)
        rel_fp += len(predicted_relations - expected_relations)
        rel_fn += len(expected_relations - predicted_relations)
        if expected_relations and not predicted_relations:
            positive_abstentions += 1
        if not expected_relations and not predicted_relations:
            negative_correct_abstentions += 1
        relation_rows.append({
            "id": record["id"],
            "expected_entities": sorted(expected_entities),
            "predicted_entities": sorted(predicted_entities),
            "expected_relations": sorted(map(list, expected_relations)),
            "predicted_relations": sorted(map(list, predicted_relations)),
        })
    return {
        "dataset": str(path.relative_to(ROOT)),
        "dataset_sha256": sha256(path),
        "status": dataset["status"],
        "source_provenance": source_provenance,
        "screening": {"rows": screening_rows, "confusion": screening},
        "entities": prf(entity_tp, entity_fp, entity_fn),
        "relations": {
            **prf(rel_tp, rel_fp, rel_fn),
            "positive_sentence_abstentions": positive_abstentions,
            "negative_sentence_correct_abstentions": negative_correct_abstentions,
            "sentence_count": len(relation_rows),
            "rows": relation_rows,
        },
    }


def graph_from_test(result: dict) -> dict:
    evidence = []
    for row in result["relations"]["rows"]:
        for subject, predicate, obj in row["predicted_relations"]:
            evidence.append({"subject": subject, "predicate": predicate, "object": obj, "sample_id": row["id"]})
    edges = sorted({(e["subject"], e["predicate"], e["object"]) for e in evidence})
    return {
        "scope": "Only relations predicted in the frozen test sample; not a complete biological network.",
        "nodes": sorted({value for edge in edges for value in (edge[0], edge[2])}),
        "edges": [{"subject": s, "predicate": p, "object": o, "evidence": [e["sample_id"] for e in evidence if (e["subject"], e["predicate"], e["object"]) == (s, p, o)]} for s, p, o in edges],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    dev = evaluate(HERE / "development.json")
    test_path = HERE / "test.json"
    test = evaluate(test_path) if test_path.exists() else None
    payload = {
        "processing": "offline deterministic rules; zero generative-LLM calls; zero network calls",
        "script_sha256": sha256(Path(__file__)),
        "development": dev,
        "test": test,
        "graph": graph_from_test(test) if test else None,
    }
    if args.check:
        stored = json.loads((args.out / "evaluation.json").read_text(encoding="utf-8"))
        if payload != stored:
            raise SystemExit("stored evaluation differs from replay")
        print("offline replay matches stored evaluation")
        return
    if args.out.exists():
        raise SystemExit(f"refusing to overwrite existing run: {args.out}")
    args.out.mkdir(parents=True)
    (args.out / "evaluation.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if payload["graph"]:
        (args.out / "evidence_graph.json").write_text(json.dumps(payload["graph"], indent=2) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()

"""Small CLI; Snakemake calls the same review/export/evaluate commands."""
import argparse
import json
from pathlib import Path
import sys


def load_config(path):
    path = Path(path).resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    config["_base_dir"] = str(path.parent)
    llm = config.get("llm", {})
    if config.get("processing_mode") != "rules" and llm.get("mode") == "live" and (not llm.get("model") or str(llm["model"]).startswith("REPLACE_")):
        raise ValueError("configure an actual LLM model before starting a live run")
    return config


def main(argv=None):
    parser = argparse.ArgumentParser(prog="litmine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "review"):
        p = sub.add_parser(name)
        p.add_argument("--config", required=True)
        p.add_argument("--out", required=True)
    p = sub.add_parser("export")
    p.add_argument("--review", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("replay")
    p.add_argument("--from-run", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("evaluate")
    p.add_argument("--review", required=True)
    p.add_argument("--gold")
    p.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("run", "review", "replay"):
            from .engine import run
            out = Path(args.out).resolve()
            if args.command == "replay":
                source = Path(args.from_run).resolve()
                config = json.loads((source / "manifest.json").read_text())["config"]
                config["offline"] = True
                config["replay_dir"] = str(source)
                if config.get("processing_mode", "llm" if config.get("llm") else "rules") == "llm":
                    config.setdefault("llm", {}).update(mode="replay", cache_dir=str(source / "llm"))
            else:
                config = load_config(args.config)
            review = run(config, out)
            print(f"Review: {review}")
            if args.command != "review":
                from .graph import export
                from .evaluate import evaluate
                gold = config.get("gold_path")
                evaluate(review, Path(config["_base_dir"]) / gold if gold else None, out / "evaluation.json")
                export(review, out)
                print(f"Graph: {out / 'graph.svg'}")
            qc = json.loads((out / "qc.json").read_text())
            print("SYNTHETIC DEMO" if qc["synthetic_demo"] else "Exploratory run; scientific quality not evaluated")
            if qc["incomplete"]:
                print("INCOMPLETE: access, screening or extraction gaps; see qc.json")
        elif args.command == "export":
            from .graph import export
            export(Path(args.review), Path(args.out))
            print(f"Graph: {Path(args.out) / 'graph.svg'}")
        else:
            from .evaluate import evaluate
            evaluate(Path(args.review), Path(args.gold) if args.gold else None, Path(args.out))
            print(f"Evaluation: {args.out}")
        return 0
    except (ValueError, OSError, KeyError, ImportError) as exc:
        # Avoid echoing configuration or provider errors that might contain secrets.
        print(f"litmine: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

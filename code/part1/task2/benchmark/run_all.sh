#!/bin/sh
set -eu

task_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

uv sync --project "$task_root" --locked
"$task_root/.venv/bin/python" "$task_root/benchmark/fetch_upstream.py"
PATH="$task_root/.venv/bin:$PATH" \
  "$task_root/.venv/bin/python" "$task_root/benchmark/build_model.py"
"$task_root/.venv/bin/python" "$task_root/benchmark/run_benchmark.py"
"$task_root/.venv/bin/python" "$task_root/benchmark/test_results.py"


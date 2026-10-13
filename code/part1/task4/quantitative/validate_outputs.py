#!/usr/bin/env python3
"""Validate the quantitative XLSX quality-control artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


REQUIRED = (
    "workbook_summary.json",
    "sheet_summary.csv",
    "column_summary.csv",
    "missingness.csv",
    "duplicate_identifiers.csv",
    "numeric_distributions.csv",
    "sample_column_patterns.csv",
    "qc_figure.svg",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Non-finite numeric value: {value}")
    return number


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the source XLSX workbook")
    parser.add_argument("output_dir", type=Path, help="Directory containing generated artifacts")
    args = parser.parse_args()
    source = args.source.resolve()
    output_dir = args.output_dir.resolve()
    checks: list[dict[str, object]] = []
    errors: list[str] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            errors.append(f"{name}: {detail}")

    try:
        check("source_exists", source.is_file(), str(source))
        for name in REQUIRED:
            path = output_dir / name
            check(f"artifact_exists:{name}", path.is_file() and path.stat().st_size > 0, f"size={path.stat().st_size if path.exists() else 0}")
        if errors:
            raise ValueError("Required inputs or artifacts are missing")

        with (output_dir / "workbook_summary.json").open(encoding="utf-8") as handle:
            summary = json.load(handle)
        sheets = read_csv(output_dir / "sheet_summary.csv")
        columns = read_csv(output_dir / "column_summary.csv")
        missing = read_csv(output_dir / "missingness.csv")
        duplicates = read_csv(output_dir / "duplicate_identifiers.csv")
        numeric = read_csv(output_dir / "numeric_distributions.csv")
        patterns = read_csv(output_dir / "sample_column_patterns.csv")

        actual_source_hash = sha256_file(source)
        check("source_hash_matches", actual_source_hash == summary["source"]["sha256"], actual_source_hash)
        check("sheet_count_reconciles", int(summary["workbook"]["sheet_count"]) == len(sheets), f"summary={summary['workbook']['sheet_count']}, csv={len(sheets)}")
        check("column_count_reconciles", int(summary["totals"]["columns_across_sheets"]) == len(columns), f"summary={summary['totals']['columns_across_sheets']}, csv={len(columns)}")
        check("missingness_row_count", len(missing) == len(columns), f"missingness={len(missing)}, columns={len(columns)}")
        check("pattern_row_count", len(patterns) == len(columns), f"patterns={len(patterns)}, columns={len(columns)}")
        check("numeric_column_count", int(summary["totals"]["numeric_columns"]) == len(numeric), f"summary={summary['totals']['numeric_columns']}, csv={len(numeric)}")
        check("identifier_candidate_count", int(summary["totals"]["identifier_candidate_columns"]) == len(duplicates), f"summary={summary['totals']['identifier_candidate_columns']}, csv={len(duplicates)}")

        data_rows_by_sheet = {row["sheet"]: int(row["data_row_count"]) for row in sheets}
        sheet_column_counts: dict[str, int] = {}
        for row in columns:
            sheet_column_counts[row["sheet"]] = sheet_column_counts.get(row["sheet"], 0) + 1
            total = int(row["nonblank_count"]) + int(row["missing_count"])
            if total != data_rows_by_sheet[row["sheet"]]:
                errors.append(f"column_cell_reconciliation:{row['sheet']}!{row['column_letter']}: {total} != {data_rows_by_sheet[row['sheet']]}")
        expected_sheet_columns = {row["sheet"]: int(row["column_count"]) for row in sheets}
        check("sheet_column_counts", sheet_column_counts == expected_sheet_columns, f"observed={sheet_column_counts}, expected={expected_sheet_columns}")
        check("column_cell_reconciliations", not any(item.startswith("column_cell_reconciliation:") for item in errors), "nonblank + missing equals data rows for every column")

        total_missing = sum(int(row["missing_count"]) for row in missing)
        total_cells = sum(int(row["data_row_count"]) for row in missing)
        check("total_missing_reconciles", total_missing == int(summary["totals"]["total_missing_cells"]), f"summary={summary['totals']['total_missing_cells']}, csv={total_missing}")
        check("total_cells_reconciles", total_cells == int(summary["totals"]["total_data_cells"]), f"summary={summary['totals']['total_data_cells']}, csv={total_cells}")

        missing_lookup = {(row["sheet"], row["column_index"]): row for row in missing}
        quantile_errors = []
        numeric_count_errors = []
        for row in numeric:
            values = [finite_float(row[key]) for key in ("min", "q1", "median", "q3", "max", "mean", "sample_standard_deviation")]
            if not (values[0] <= values[1] <= values[2] <= values[3] <= values[4]):
                quantile_errors.append(f"{row['sheet']}!{row['column_letter']}")
            missing_row = missing_lookup[(row["sheet"], row["column_index"])]
            total = int(row["numeric_count"]) + int(row["non_numeric_nonblank_count"]) + int(row["missing_count"])
            if total != int(missing_row["data_row_count"]):
                numeric_count_errors.append(f"{row['sheet']}!{row['column_letter']}")
        check("numeric_quantile_order", not quantile_errors, f"violations={quantile_errors}")
        check("numeric_count_reconciliations", not numeric_count_errors, f"violations={numeric_count_errors}")

        duplicate_math_errors = []
        for row in duplicates:
            expected_extra = int(row["nonblank_count"]) - int(row["unique_nonblank_count"])
            if expected_extra != int(row["duplicate_record_count"]):
                duplicate_math_errors.append(f"{row['sheet']}!{row['column_letter']}")
        check("duplicate_identifier_math", not duplicate_math_errors, f"violations={duplicate_math_errors}")
        check(
            "duplicate_totals_reconcile",
            sum(int(row["duplicate_record_count"]) for row in duplicates) == int(summary["totals"]["identifier_duplicate_records_beyond_first"]),
            f"csv={sum(int(row['duplicate_record_count']) for row in duplicates)}, summary={summary['totals']['identifier_duplicate_records_beyond_first']}",
        )

        svg_root = ET.parse(output_dir / "qc_figure.svg").getroot()
        check("svg_parses", svg_root.tag.endswith("svg"), svg_root.tag)
        check("source_unmodified_claim", summary["method"]["source_modified"] is False, str(summary["method"]["source_modified"]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as exc:
        errors.append(f"validation_exception: {exc}")

    manifest = {
        name: {"byte_size": (output_dir / name).stat().st_size, "sha256": sha256_file(output_dir / name)}
        for name in REQUIRED
        if (output_dir / name).is_file()
    }
    with (output_dir / "output_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    report = {
        "status": "pass" if not errors else "fail",
        "validated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_sha256": sha256_file(source) if source.is_file() else None,
        "check_count": len(checks),
        "passed_check_count": sum(bool(item["passed"]) for item in checks),
        "failed_check_count": sum(not bool(item["passed"]) for item in checks),
        "checks": checks,
        "errors": errors,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "validation_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "status": report["status"],
        "checks": report["check_count"],
        "passed": report["passed_check_count"],
        "failed": report["failed_check_count"],
        "report": str((output_dir / "validation_report.json").resolve()),
    }, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

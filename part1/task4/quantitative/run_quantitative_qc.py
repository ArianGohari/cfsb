#!/usr/bin/env python3
"""Generic, dependency-free quality-control summary for an XLSX workbook.

The script reads the XLSX package directly with Python's standard library. It
does not modify the workbook and does not attach domain meaning to the data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CORE_NS = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
NS = {"m": MAIN_NS, "r": REL_NS}

OUTPUT_FILES = (
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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Za-z]+)", cell_ref)
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_ref!r}")
    value = 0
    for char in match.group(1).upper():
        value = value * 26 + ord(char) - 64
    return value


def column_letter(index: int) -> str:
    result = []
    while index:
        index, remainder = divmod(index - 1, 26)
        result.append(chr(65 + remainder))
    return "".join(reversed(result))


def parse_number(text: str | None) -> int | float | None:
    if text is None or text == "":
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if math.isfinite(value) and value.is_integer() and abs(value) <= 2**53:
        return int(value)
    return value


def display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.parse(archive.open("xl/sharedStrings.xml")).getroot()
    return ["".join(node.text or "" for node in item.findall(".//m:t", NS)) for item in root.findall("m:si", NS)]


def date_style_indexes(archive: zipfile.ZipFile) -> set[int]:
    if "xl/styles.xml" not in archive.namelist():
        return set()
    root = ET.parse(archive.open("xl/styles.xml")).getroot()
    custom_formats = {
        int(node.attrib["numFmtId"]): node.attrib.get("formatCode", "")
        for node in root.findall("m:numFmts/m:numFmt", NS)
    }
    built_in_date_ids = set(range(14, 23)) | set(range(27, 37)) | set(range(45, 48)) | set(range(50, 59))
    result = set()
    cell_xfs = root.find("m:cellXfs", NS)
    if cell_xfs is None:
        return result
    for index, xf in enumerate(cell_xfs.findall("m:xf", NS)):
        num_fmt_id = int(xf.attrib.get("numFmtId", "0"))
        code = custom_formats.get(num_fmt_id, "")
        code_without_literals = re.sub(r'"[^"]*"|\\.|\[[^\]]*\]', "", code.lower())
        if num_fmt_id in built_in_date_ids or re.search(r"[ymdhis]", code_without_literals):
            result.add(index)
    return result


def parse_core_properties(archive: zipfile.ZipFile) -> dict[str, str | None]:
    fields: dict[str, str | None] = {
        "title": None,
        "subject": None,
        "creator": None,
        "description": None,
        "keywords": None,
        "category": None,
        "created": None,
        "modified": None,
    }
    if "docProps/core.xml" not in archive.namelist():
        return fields
    root = ET.parse(archive.open("docProps/core.xml")).getroot()
    namespaces = {"cp": CORE_NS, "dc": DC_NS, "dcterms": DCTERMS_NS}
    paths = {
        "title": "dc:title",
        "subject": "dc:subject",
        "creator": "dc:creator",
        "description": "dc:description",
        "keywords": "cp:keywords",
        "category": "cp:category",
        "created": "dcterms:created",
        "modified": "dcterms:modified",
    }
    for key, path in paths.items():
        node = root.find(path, namespaces)
        fields[key] = node.text if node is not None and node.text else None
    return fields


def workbook_structure(archive: zipfile.ZipFile) -> tuple[list[dict[str, str]], list[dict[str, str]], bool]:
    workbook_root = ET.parse(archive.open("xl/workbook.xml")).getroot()
    rels_root = ET.parse(archive.open("xl/_rels/workbook.xml.rels")).getroot()
    rels = {
        node.attrib["Id"]: node.attrib["Target"]
        for node in rels_root.findall(f"{{{PKG_REL_NS}}}Relationship")
    }
    sheets = []
    for node in workbook_root.findall("m:sheets/m:sheet", NS):
        rel_id = node.attrib[f"{{{REL_NS}}}id"]
        target = rels[rel_id]
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = str(PurePosixPath("xl") / target)
        sheets.append({"name": node.attrib["name"], "state": node.attrib.get("state", "visible"), "path": path})
    defined_names = []
    for node in workbook_root.findall("m:definedNames/m:definedName", NS):
        defined_names.append({
            "name": node.attrib.get("name", ""),
            "local_sheet_id": node.attrib.get("localSheetId", ""),
            "value": node.text or "",
        })
    workbook_pr = workbook_root.find("m:workbookPr", NS)
    date_1904 = workbook_pr is not None and workbook_pr.attrib.get("date1904", "0") in {"1", "true", "True"}
    return sheets, defined_names, date_1904


def excel_datetime(serial: int | float, date_1904: bool) -> datetime:
    origin = datetime(1904, 1, 1) if date_1904 else datetime(1899, 12, 30)
    return origin + timedelta(days=float(serial))


def cell_value(cell: ET.Element, shared_strings: list[str], date_styles: set[int], date_1904: bool) -> tuple[Any, str, bool]:
    cell_type = cell.attrib.get("t", "n")
    style_index = int(cell.attrib.get("s", "0"))
    formula = cell.find("m:f", NS)
    value_node = cell.find("m:v", NS)
    has_formula = formula is not None
    if cell_type == "inlineStr":
        text = "".join(node.text or "" for node in cell.findall(".//m:t", NS))
        return text, "string", has_formula
    raw = value_node.text if value_node is not None else None
    if cell_type == "s":
        try:
            return shared_strings[int(raw or "0")], "string", has_formula
        except (ValueError, IndexError):
            return raw, "string", has_formula
    if cell_type == "str":
        return raw or "", "string", has_formula
    if cell_type == "b":
        return raw == "1", "boolean", has_formula
    if cell_type == "e":
        return raw or "", "error", has_formula
    if cell_type == "d":
        try:
            return datetime.fromisoformat(raw or ""), "date", has_formula
        except ValueError:
            return raw, "string", has_formula
    number = parse_number(raw)
    if number is None:
        return None, "blank", has_formula
    if style_index in date_styles:
        return excel_datetime(number, date_1904), "date", has_formula
    return number, "number", has_formula


def parse_sheet(
    archive: zipfile.ZipFile,
    sheet: dict[str, str],
    shared_strings: list[str],
    date_styles: set[int],
    date_1904: bool,
) -> dict[str, Any]:
    rows: dict[int, dict[int, dict[str, Any]]] = defaultdict(dict)
    declared_dimension = ""
    max_row = 0
    max_col = 0
    formula_cells = 0
    with archive.open(sheet["path"]) as handle:
        for event, element in ET.iterparse(handle, events=("end",)):
            name = local_name(element.tag)
            if name == "dimension":
                declared_dimension = element.attrib.get("ref", "")
            elif name == "c":
                ref = element.attrib.get("r", "")
                col = column_index(ref)
                match = re.search(r"(\d+)$", ref)
                if not match:
                    element.clear()
                    continue
                row = int(match.group(1))
                value, value_type, has_formula = cell_value(element, shared_strings, date_styles, date_1904)
                if value is not None or has_formula:
                    rows[row][col] = {"value": value, "type": value_type, "formula": has_formula}
                    max_row = max(max_row, row)
                    max_col = max(max_col, col)
                    formula_cells += int(has_formula)
                element.clear()
    nonempty_rows = [row for row, cells in rows.items() if any(cell["value"] not in (None, "") for cell in cells.values())]
    header_row = min(nonempty_rows) if nonempty_rows else None
    headers: list[str] = []
    blank_header_count = 0
    if header_row is not None:
        for col in range(1, max_col + 1):
            raw = rows.get(header_row, {}).get(col, {}).get("value")
            cleaned = display_value(raw).strip()
            blank_header_count += int(not cleaned)
            headers.append(cleaned or f"__unnamed_col_{col}")
    return {
        "name": sheet["name"],
        "state": sheet["state"],
        "declared_dimension": declared_dimension,
        "rows": rows,
        "max_row": max_row,
        "max_col": max_col,
        "header_row": header_row,
        "headers": headers,
        "blank_header_count": blank_header_count,
        "formula_cells": formula_cells,
    }


def quantile(sorted_values: list[float], proportion: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = proportion * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def classify_column(type_counts: Counter[str], nonblank: int) -> str:
    if nonblank == 0:
        return "empty"
    nonzero_types = [key for key, count in type_counts.items() if count > 0]
    if len(nonzero_types) == 1:
        return nonzero_types[0]
    if type_counts["number"] and type_counts["string"]:
        return "mixed_number_string"
    return "mixed"


def identifier_reason(header: str, col: int, classification: str, nonblank: int, unique_nonblank: int) -> str | None:
    normalized = header.strip().lower()
    if normalized in {"id", "identifier", "accession", "record_id", "row_id", "sample_id", "feature_id"}:
        return "explicit identifier header"
    tokens = [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
    if "identifier" in tokens or "accession" in tokens:
        return "identifier token in header"
    if tokens and tokens[-1] == "id":
        return "header ends with id token"
    if (
        col == 1
        and normalized.startswith("__unnamed_col_")
        and classification == "string"
        and nonblank > 0
        and unique_nonblank / nonblank >= 0.95
    ):
        return "structural candidate: unnamed leading text column with at least 95% unique nonblank values"
    return None


def numeric_signature(values: list[float]) -> str:
    payload = "\n".join(format(value, ".17g") for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def syntactic_name_parts(header: str) -> tuple[str, str, str]:
    header = header.strip()
    match = re.match(r"^(.*?)([._-]?)(\d+)$", header)
    if match and match.group(1):
        prefix = match.group(1).rstrip("._-")
        return "prefix_numeric_suffix", prefix, match.group(3)
    tokens = [token for token in re.split(r"[._-]+", header) if token]
    if len(tokens) >= 2:
        return f"delimited_{len(tokens)}_tokens", "", ""
    return "no_detected_pattern", "", ""


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def json_ready(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [json_ready(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(json_ready(data), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def signed_log(value: float) -> float:
    return math.copysign(math.log10(1 + abs(value)), value)


def make_svg(column_rows: list[dict[str, Any]], numeric_rows: list[dict[str, Any]], source_name: str) -> str:
    width, height = 1600, 1000
    left, right = 95, 35
    panel_width = width - left - right
    top_y, top_h = 120, 250
    bottom_y, bottom_h = 570, 250
    blue, dark, grid, pale = "#4C78A8", "#2F3437", "#D9DEE3", "#A7B6C2"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#2F3437}.title{font-size:24px;font-weight:700}.subtitle{font-size:14px}.axis{font-size:12px}.small{font-size:10px}</style>',
        f'<text class="title" x="{left}" y="42">Workbook quality-control overview</text>',
        f'<text class="subtitle" x="{left}" y="70">{xml_escape(source_name)} · syntactic and numeric summaries only</text>',
        f'<text class="subtitle" x="{left}" y="{top_y - 18}">Missing data by column</text>',
    ]
    for tick in range(0, 101, 25):
        y = top_y + top_h - (tick / 100) * top_h
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{grid}" stroke-width="1"/>')
        parts.append(f'<text class="axis" x="{left-12}" y="{y+4:.1f}" text-anchor="end">{tick}%</text>')
    count = max(1, len(column_rows))
    step = panel_width / count
    bar_width = max(0.8, step * 0.78)
    for index, row in enumerate(column_rows):
        pct = float(row["missing_percent"])
        x = left + index * step + (step - bar_width) / 2
        bar_h = pct / 100 * top_h
        parts.append(f'<rect x="{x:.2f}" y="{top_y+top_h-bar_h:.2f}" width="{bar_width:.2f}" height="{bar_h:.2f}" fill="{blue}"/>')
    if column_rows and all(float(row["missing_percent"]) == 0 for row in column_rows):
        total_cells = sum(int(row["data_row_count"]) for row in column_rows)
        parts.append(f'<text class="subtitle" x="{left + panel_width/2:.1f}" y="{top_y + top_h/2:.1f}" text-anchor="middle">0 missing cells across {total_cells:,} data cells</text>')
    parts.append(f'<line x1="{left}" x2="{left}" y1="{top_y}" y2="{top_y+top_h}" stroke="{dark}"/>')
    parts.append(f'<line x1="{left}" x2="{width-right}" y1="{top_y+top_h}" y2="{top_y+top_h}" stroke="{dark}"/>')
    label_every = max(1, math.ceil(len(column_rows) / 35))
    for index, row in enumerate(column_rows):
        if index % label_every:
            continue
        x = left + (index + 0.5) * step
        label = str(row["header"])
        if len(label) > 22:
            label = label[:19] + "..."
        parts.append(f'<text class="small" transform="translate({x:.1f},{top_y+top_h+10}) rotate(55)" text-anchor="start">{xml_escape(label)}</text>')
    parts.append(f'<text class="subtitle" x="{left}" y="{bottom_y - 28}">Numeric distributions by column</text>')
    parts.append(f'<text class="axis" x="{left}" y="{bottom_y - 9}">Whiskers: min/max; box: Q1–Q3; center: median. Axis uses signed log10(1 + |x|).</text>')
    if numeric_rows:
        transformed = []
        for row in numeric_rows:
            transformed.extend([signed_log(float(row[key])) for key in ("min", "q1", "median", "q3", "max") if row[key] not in ("", None)])
        min_t, max_t = min(transformed), max(transformed)
        if min_t == max_t:
            min_t -= 0.5
            max_t += 0.5
        pad = (max_t - min_t) * 0.07
        min_t -= pad
        max_t += pad
        def y_pos(value: float) -> float:
            return bottom_y + bottom_h - (signed_log(value) - min_t) / (max_t - min_t) * bottom_h
        for tick_index in range(5):
            transformed_tick = min_t + tick_index * (max_t - min_t) / 4
            y = bottom_y + bottom_h - tick_index * bottom_h / 4
            parts.append(f'<line x1="{left}" x2="{width-right}" y1="{y:.1f}" y2="{y:.1f}" stroke="{grid}"/>')
            parts.append(f'<text class="axis" x="{left-12}" y="{y+4:.1f}" text-anchor="end">{transformed_tick:.2f}</text>')
        n_step = panel_width / max(1, len(numeric_rows))
        box_width = max(1.0, min(14.0, n_step * 0.6))
        for index, row in enumerate(numeric_rows):
            x = left + (index + 0.5) * n_step
            values = {key: float(row[key]) for key in ("min", "q1", "median", "q3", "max")}
            y_min, y_q1, y_med, y_q3, y_max = [y_pos(values[key]) for key in ("min", "q1", "median", "q3", "max")]
            parts.append(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="{y_max:.2f}" y2="{y_min:.2f}" stroke="{pale}"/>')
            parts.append(f'<rect x="{x-box_width/2:.2f}" y="{min(y_q1,y_q3):.2f}" width="{box_width:.2f}" height="{max(1,abs(y_q1-y_q3)):.2f}" fill="{blue}" fill-opacity="0.42" stroke="{blue}"/>')
            parts.append(f'<line x1="{x-box_width/2:.2f}" x2="{x+box_width/2:.2f}" y1="{y_med:.2f}" y2="{y_med:.2f}" stroke="{dark}" stroke-width="1.4"/>')
        n_label_every = max(1, math.ceil(len(numeric_rows) / 35))
        for index, row in enumerate(numeric_rows):
            if index % n_label_every:
                continue
            x = left + (index + 0.5) * n_step
            label = str(row["header"])
            if len(label) > 22:
                label = label[:19] + "..."
            parts.append(f'<text class="small" transform="translate({x:.1f},{bottom_y+bottom_h+10}) rotate(55)" text-anchor="start">{xml_escape(label)}</text>')
        parts.append(f'<line x1="{left}" x2="{left}" y1="{bottom_y}" y2="{bottom_y+bottom_h}" stroke="{dark}"/>')
        parts.append(f'<line x1="{left}" x2="{width-right}" y1="{bottom_y+bottom_h}" y2="{bottom_y+bottom_h}" stroke="{dark}"/>')
    else:
        parts.append(f'<text class="subtitle" x="{left}" y="{bottom_y+40}">No numeric columns were detected.</text>')
    parts.append(f'<text class="small" x="{width-right}" y="{height-18}" text-anchor="end">Columns remain in workbook order.</text>')
    parts.append("</svg>\n")
    return "".join(parts)


def analyze(source: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        shared_strings = read_shared_strings(archive)
        date_styles = date_style_indexes(archive)
        sheets_meta, defined_names, date_1904 = workbook_structure(archive)
        core_properties = parse_core_properties(archive)
        sheets = [parse_sheet(archive, sheet, shared_strings, date_styles, date_1904) for sheet in sheets_meta]

    sheet_rows: list[dict[str, Any]] = []
    column_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    duplicate_rows: list[dict[str, Any]] = []
    numeric_rows: list[dict[str, Any]] = []
    pattern_rows: list[dict[str, Any]] = []
    workbook_totals = Counter()

    for sheet in sheets:
        header_row = sheet["header_row"]
        data_start = header_row + 1 if header_row is not None else None
        data_rows = max(0, sheet["max_row"] - header_row) if header_row is not None else 0
        header_counts = Counter(sheet["headers"])
        sheet_rows.append({
            "sheet": sheet["name"],
            "state": sheet["state"],
            "declared_dimension": sheet["declared_dimension"],
            "observed_max_row": sheet["max_row"],
            "observed_max_column": sheet["max_col"],
            "header_row": header_row or "",
            "data_start_row": data_start or "",
            "data_row_count": data_rows,
            "column_count": sheet["max_col"],
            "blank_header_count": sheet["blank_header_count"],
            "duplicate_header_name_count": sum(count - 1 for count in header_counts.values() if count > 1),
            "formula_cell_count": sheet["formula_cells"],
        })
        workbook_totals["rows"] += data_rows
        workbook_totals["columns"] += sheet["max_col"]
        workbook_totals["formula_cells"] += sheet["formula_cells"]
        prefix_counts = Counter()
        pattern_parts: dict[int, tuple[str, str, str]] = {}
        for col, header in enumerate(sheet["headers"], start=1):
            parts = syntactic_name_parts(header)
            pattern_parts[col] = parts
            if parts[0] == "prefix_numeric_suffix":
                prefix_counts[parts[1]] += 1
        for col, header in enumerate(sheet["headers"], start=1):
            values = []
            type_counts: Counter[str] = Counter()
            formula_count = 0
            if header_row is not None:
                for row_num in range(header_row + 1, sheet["max_row"] + 1):
                    cell = sheet["rows"].get(row_num, {}).get(col)
                    if cell is None or cell["value"] in (None, ""):
                        continue
                    values.append(cell["value"])
                    type_counts[cell["type"]] += 1
                    formula_count += int(cell["formula"])
            nonblank = len(values)
            missing = data_rows - nonblank
            missing_pct = 100.0 * missing / data_rows if data_rows else 0.0
            classification = classify_column(type_counts, nonblank)
            unique_nonblank = len({display_value(value) for value in values})
            common = Counter(display_value(value) for value in values).most_common(3)
            column_rows.append({
                "sheet": sheet["name"],
                "column_index": col,
                "column_letter": column_letter(col),
                "header": header,
                "data_type": classification,
                "number_count": type_counts["number"],
                "string_count": type_counts["string"],
                "boolean_count": type_counts["boolean"],
                "date_count": type_counts["date"],
                "error_count": type_counts["error"],
                "formula_count": formula_count,
                "nonblank_count": nonblank,
                "missing_count": missing,
                "unique_nonblank_count": unique_nonblank,
                "top_values_json": json.dumps(common, ensure_ascii=False),
            })
            missing_rows.append({
                "sheet": sheet["name"],
                "column_index": col,
                "column_letter": column_letter(col),
                "header": header,
                "data_row_count": data_rows,
                "nonblank_count": nonblank,
                "missing_count": missing,
                "missing_percent": round(missing_pct, 8),
            })
            numeric_values = sorted(number for value in values if (number := finite_number(value)) is not None)
            if numeric_values:
                numeric_rows.append({
                    "sheet": sheet["name"],
                    "column_index": col,
                    "column_letter": column_letter(col),
                    "header": header,
                    "numeric_count": len(numeric_values),
                    "missing_count": missing,
                    "non_numeric_nonblank_count": nonblank - len(numeric_values),
                    "unique_numeric_count": len(set(numeric_values)),
                    "zero_count": sum(value == 0 for value in numeric_values),
                    "negative_count": sum(value < 0 for value in numeric_values),
                    "min": numeric_values[0],
                    "q1": quantile(numeric_values, 0.25),
                    "median": quantile(numeric_values, 0.50),
                    "mean": statistics.fmean(numeric_values),
                    "q3": quantile(numeric_values, 0.75),
                    "max": numeric_values[-1],
                    "sample_standard_deviation": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0.0,
                    "ordered_values_sha256": numeric_signature([
                        number for value in values if (number := finite_number(value)) is not None
                    ]),
                    "sorted_values_sha256": numeric_signature(numeric_values),
                })
            reason = identifier_reason(header, col, classification, nonblank, unique_nonblank)
            if reason:
                value_counts = Counter(display_value(value).strip() for value in values if display_value(value).strip())
                duplicate_groups = [(value, count) for value, count in value_counts.items() if count > 1]
                duplicate_groups.sort(key=lambda item: (-item[1], item[0]))
                duplicate_rows.append({
                    "sheet": sheet["name"],
                    "column_index": col,
                    "column_letter": column_letter(col),
                    "header": header,
                    "candidate_reason": reason,
                    "nonblank_count": sum(value_counts.values()),
                    "unique_nonblank_count": len(value_counts),
                    "duplicate_group_count": len(duplicate_groups),
                    "duplicate_record_count": sum(count - 1 for _, count in duplicate_groups),
                    "duplicate_examples_json": json.dumps(duplicate_groups[:10], ensure_ascii=False),
                })
            pattern, prefix, suffix = pattern_parts[col]
            explicit_group = prefix if pattern == "prefix_numeric_suffix" and prefix_counts[prefix] >= 2 else ""
            pattern_rows.append({
                "sheet": sheet["name"],
                "column_index": col,
                "column_letter": column_letter(col),
                "header": header,
                "syntactic_pattern": pattern,
                "numeric_suffix": suffix,
                "explicit_repeated_prefix": explicit_group,
                "group_basis": "repeated prefix before numeric suffix" if explicit_group else "",
                "numeric_data_fraction": round(len(numeric_values) / nonblank, 8) if nonblank else 0.0,
            })

    write_csv(output_dir / "sheet_summary.csv", list(sheet_rows[0].keys()) if sheet_rows else ["sheet"], sheet_rows)
    write_csv(output_dir / "column_summary.csv", [
        "sheet", "column_index", "column_letter", "header", "data_type", "number_count", "string_count",
        "boolean_count", "date_count", "error_count", "formula_count", "nonblank_count", "missing_count",
        "unique_nonblank_count", "top_values_json",
    ], column_rows)
    write_csv(output_dir / "missingness.csv", [
        "sheet", "column_index", "column_letter", "header", "data_row_count", "nonblank_count", "missing_count", "missing_percent",
    ], missing_rows)
    write_csv(output_dir / "duplicate_identifiers.csv", [
        "sheet", "column_index", "column_letter", "header", "candidate_reason", "nonblank_count", "unique_nonblank_count",
        "duplicate_group_count", "duplicate_record_count", "duplicate_examples_json",
    ], duplicate_rows)
    write_csv(output_dir / "numeric_distributions.csv", [
        "sheet", "column_index", "column_letter", "header", "numeric_count", "missing_count", "non_numeric_nonblank_count",
        "unique_numeric_count", "zero_count", "negative_count", "min", "q1", "median", "mean", "q3", "max",
        "sample_standard_deviation", "ordered_values_sha256", "sorted_values_sha256",
    ], numeric_rows)
    write_csv(output_dir / "sample_column_patterns.csv", [
        "sheet", "column_index", "column_letter", "header", "syntactic_pattern", "numeric_suffix", "explicit_repeated_prefix",
        "group_basis", "numeric_data_fraction",
    ], pattern_rows)
    (output_dir / "qc_figure.svg").write_text(make_svg(missing_rows, numeric_rows, source.name), encoding="utf-8")

    summary = {
        "source": {
            "file_name": source.name,
            "byte_size": source.stat().st_size,
            "sha256": sha256_file(source),
            "modified_utc": datetime.fromtimestamp(source.stat().st_mtime, timezone.utc).isoformat(timespec="seconds"),
        },
        "workbook": {
            "sheet_count": len(sheets),
            "defined_names": defined_names,
            "date_system": "1904" if date_1904 else "1900",
            "core_properties": core_properties,
        },
        "method": {
            "header_detection": "first non-empty row per sheet",
            "data_rows": "all row indexes after the header through the last observed populated row",
            "identifier_candidates": "headers containing an explicit id, identifier, or accession token; also an unnamed leading text column when at least 95% of its nonblank values are unique",
            "groups": "reported only for repeated literal prefixes before trailing numeric suffixes",
            "quantiles": "linear interpolation over sorted finite numeric values",
            "standard_deviation": "sample standard deviation",
            "source_modified": False,
        },
        "totals": {
            "data_rows_across_sheets": workbook_totals["rows"],
            "columns_across_sheets": workbook_totals["columns"],
            "formula_cells": workbook_totals["formula_cells"],
            "numeric_columns": len(numeric_rows),
            "identifier_candidate_columns": len(duplicate_rows),
            "identifier_duplicate_groups": sum(int(row["duplicate_group_count"]) for row in duplicate_rows),
            "identifier_duplicate_records_beyond_first": sum(int(row["duplicate_record_count"]) for row in duplicate_rows),
            "total_missing_cells": sum(int(row["missing_count"]) for row in missing_rows),
            "total_data_cells": sum(int(row["data_row_count"]) for row in missing_rows),
        },
        "sheets": sheet_rows,
        "outputs": list(OUTPUT_FILES),
    }
    write_json(output_dir / "workbook_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Path to the source XLSX workbook")
    parser.add_argument("output_dir", type=Path, help="Directory for CSV, JSON, and SVG outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.is_file():
        print(f"ERROR: source workbook does not exist: {args.source}", file=sys.stderr)
        return 2
    if args.source.suffix.lower() != ".xlsx":
        print(f"ERROR: expected an .xlsx source: {args.source}", file=sys.stderr)
        return 2
    try:
        summary = analyze(args.source.resolve(), args.output_dir.resolve())
    except (OSError, zipfile.BadZipFile, ET.ParseError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "ok",
        "sheet_count": summary["workbook"]["sheet_count"],
        "data_rows": summary["totals"]["data_rows_across_sheets"],
        "columns": summary["totals"]["columns_across_sheets"],
        "numeric_columns": summary["totals"]["numeric_columns"],
        "output_dir": str(args.output_dir.resolve()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

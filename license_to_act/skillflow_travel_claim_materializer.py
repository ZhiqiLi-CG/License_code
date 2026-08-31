from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
import csv
import re
import zipfile


TRAVEL_CLAIM_COLUMNS = ["filename", "claim_code", "employee_id", "trip_id", "date", "total_amount"]


def parse_travel_claim_text(filename: str, text: str) -> dict[str, Any]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    row = {
        "filename": filename,
        "claim_code": _extract_claim_code(lines) or "",
        "date": _extract_date(lines) or "",
        "total_amount": _extract_amount(lines) or "",
    }
    row["missing_fields"] = [
        field for field in ("claim_code", "date", "total_amount") if not row[field]
    ]
    row["evidence_status"] = "complete" if not row["missing_fields"] else "partial"
    return row


def load_claim_roster(path: Path) -> dict[str, tuple[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return {
            row["claim_code"].strip().upper(): (
                row["employee_id"].strip(),
                row["trip_id"].strip(),
            )
            for row in csv.DictReader(handle)
        }


def build_travel_claim_rows(
    parsed_claims: list[dict[str, Any]],
    roster: dict[str, tuple[str, str]],
) -> list[list[str]]:
    rows: list[list[str]] = []
    for claim in sorted(parsed_claims, key=lambda row: row["filename"]):
        employee_id, trip_id = roster.get(str(claim["claim_code"]).upper(), ("", ""))
        rows.append(
            [
                claim["filename"],
                claim["claim_code"],
                employee_id,
                trip_id,
                claim["date"],
                claim["total_amount"],
            ]
        )
    return rows


def write_travel_claim_workbook(rows: list[list[str]], output_path: Path) -> None:
    table = [TRAVEL_CLAIM_COLUMNS]
    table.extend(sorted(rows, key=lambda row: row[0]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(table))


def build_travel_claim_state_report(
    *,
    parsed_claims: list[dict[str, Any]],
    rows: list[list[str]],
    output_path: Path,
) -> dict[str, Any]:
    return {
        "license": "skillflow_travel_claim_workbook",
        "operation": "WriteOutputWorkbook",
        "state_region": "output:/app/workspace/travel_claims.xlsx",
        "evidence_types": [
            "OcrTextEvidence",
            "ClaimCodeEvidence",
            "RosterJoinEvidence",
            "WorkbookSchemaEvidence",
        ],
        "output_path": str(output_path),
        "rows": [dict(zip(TRAVEL_CLAIM_COLUMNS, row, strict=True)) for row in rows],
        "artifact_gate": {
            "sheet": "claims",
            "columns": TRAVEL_CLAIM_COLUMNS,
            "row_count": len(rows),
            "missing_required_rows": [row[0] for row in rows if not row[1] or not row[4] or not row[5]],
            "roster_authority": "dataset/claim_roster.csv",
        },
        "parsed_claims": parsed_claims,
    }


def _extract_claim_code(lines: list[str]) -> str | None:
    label = re.compile(r"CLAIM\s*CODE|CLAIM\s*REF|EXPENSE\s*CODE", re.I)
    value = re.compile(r"C[L1I]M[-\s]*(20\d{2})[-\s]*(\d{1,3})", re.I)
    for index, line in enumerate(lines):
        if not label.search(line):
            continue
        for candidate in _candidate_lines(lines, index):
            match = value.search(_normalize_ocr_token(candidate))
            if match:
                return f"CLM-{match.group(1)}-{int(match.group(2)):03d}"
    joined = "\n".join(lines)
    match = value.search(_normalize_ocr_token(joined))
    if match:
        return f"CLM-{match.group(1)}-{int(match.group(2)):03d}"
    return None


def _extract_date(lines: list[str]) -> str | None:
    label = re.compile(r"TRANSACTION\s*DATE|PURCHASE\s*DATE|\bDATE\b", re.I)
    date = re.compile(r"20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/](?:20)?\d{2}")
    for index, line in enumerate(lines):
        if not label.search(line):
            continue
        for candidate in _candidate_lines(lines, index):
            match = date.search(_normalize_ocr_token(candidate))
            if match:
                parsed = parse_claim_date(match.group(0))
                if parsed:
                    return parsed
    for line in lines:
        match = date.search(_normalize_ocr_token(line))
        if match:
            parsed = parse_claim_date(match.group(0))
            if parsed:
                return parsed
    return None


def parse_claim_date(value: str) -> str | None:
    text = _normalize_ocr_token(value).strip()
    match = re.fullmatch(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", text)
    if match:
        return _format_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = re.fullmatch(r"(\d{1,2})[-/](\d{1,2})[-/](?:20)?(\d{2})", text)
    if not match:
        return None
    first, second, year_suffix = int(match.group(1)), int(match.group(2)), int(match.group(3))
    year = 2000 + year_suffix if year_suffix < 100 else year_suffix
    if second > 12 and first <= 12:
        month, day = first, second
    else:
        day, month = first, second
    return _format_date(year, month, day)


def _extract_amount(lines: list[str]) -> str | None:
    label = re.compile(r"REIMBURSABLE\s+TOTAL|TOTAL\s+CLAIM|AMOUNT\s+CLAIMED|TOTAL\s+DUE", re.I)
    ignored = re.compile(r"ADVANCE|CASH\s+PAID|TIP|TAX", re.I)
    amount = re.compile(r"(?:[$]\s*)?(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?|\d+\.\d{1,2})")
    candidates: list[tuple[int, float]] = []
    for index, line in enumerate(lines):
        if ignored.search(line) or not label.search(line):
            continue
        for priority, candidate in enumerate(_candidate_lines(lines, index)):
            if ignored.search(candidate):
                continue
            for match in amount.finditer(candidate):
                try:
                    candidates.append((4 - priority, float(match.group(1).replace(",", "").replace(" ", ""))))
                except ValueError:
                    continue
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return f"{candidates[0][1]:.2f}"


def _candidate_lines(lines: list[str], index: int) -> list[str]:
    return [
        lines[position]
        for position in (index, index + 1, index + 2)
        if 0 <= position < len(lines)
    ]


def _format_date(year: int, month: int, day: int) -> str | None:
    if not (2000 <= year <= 2035 and 1 <= month <= 12 and 1 <= day <= 31):
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def _normalize_ocr_token(value: str) -> str:
    return value.upper().replace("O", "0").replace("I", "1").replace("L", "1")


def _worksheet_xml(rows: list[list[str]]) -> str:
    max_row = len(rows)
    max_col = len(TRAVEL_CLAIM_COLUMNS)
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{_column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value or "")}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:{_column_name(max_col)}{max_row}"/>'
        '<sheetViews><sheetView workbookViewId="0"/></sheetViews>'
        '<sheetFormatPr defaultRowHeight="15"/>'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _content_types_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/>'
        "</Relationships>"
    )


def _workbook_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="claims" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>"
    )


def _workbook_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        'Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )

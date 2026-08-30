from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
from typing import Callable, Iterable
from xml.sax.saxutils import escape
import zipfile

from .core import (
    ActionLicense,
    Decision,
    EvidenceBundle,
    StateChangeEvent,
    evaluate_commit_obligation,
)


@dataclass(frozen=True)
class InvoiceRow:
    filename: str
    date: str | None
    total_amount: str | None


@dataclass(frozen=True)
class InvoiceFulfillment:
    status: str
    decision: Decision
    event: StateChangeEvent | None
    rows: tuple[InvoiceRow, ...]


OcrFn = Callable[[Path], str]

_BLOCK_HEADER_RE = re.compile(r"^===== (?P<filename>[^=\n]+) =====\s*$")
_ISO_DATE_RE = re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b")
_SLASH_DATE_RE = re.compile(r"\b(?P<first>\d{1,2})[/-](?P<second>\d{1,2})[/-](?P<year>\d{4})\b")
_MONEY_RE = re.compile(r"(?:[$]\s*)?(?P<amount>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{2})?)")

_TOTAL_KEYWORDS = ("GRAND TOTAL", "TOTAL DUE", "AMOUNT DUE", "TOTAL", "AMOUNT")
_EXCLUSION_KEYWORDS = ("SUBTOTAL", "SUB TOTAL", "TAX", "GST", "DISCOUNT", "CHANGE")
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def extract_ocr_blocks(raw_text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current_filename: str | None = None
    current_lines: list[str] = []

    for line in raw_text.splitlines():
        match = _BLOCK_HEADER_RE.match(line.strip())
        if match:
            _flush_ocr_block(blocks, current_filename, current_lines)
            current_filename = match.group("filename").strip()
            current_lines = []
            continue
        if current_filename is not None:
            current_lines.append(line)

    _flush_ocr_block(blocks, current_filename, current_lines)
    return dict(sorted(blocks.items()))


def parse_invoice_text(filename: str, text: str) -> InvoiceRow:
    return InvoiceRow(
        filename=filename,
        date=_extract_invoice_date(text),
        total_amount=_extract_total_amount(text),
    )


def materialize_invoice_workbook(image_dir: Path | str, output_path: Path | str, ocr_fn: OcrFn) -> tuple[InvoiceRow, ...]:
    image_root = Path(image_dir)
    rows = tuple(
        parse_invoice_text(path.name, ocr_fn(path))
        for path in sorted(image_root.iterdir(), key=lambda p: p.name)
        if path.suffix.lower() in _IMAGE_SUFFIXES
    )
    write_invoice_workbook(rows, output_path)
    return rows


def write_invoice_workbook(rows: Iterable[InvoiceRow], output_path: Path | str) -> None:
    sorted_rows = sorted(rows, key=lambda row: row.filename)
    table = [["filename", "date", "total_amount"]]
    table.extend(
        [
            row.filename,
            row.date or "",
            row.total_amount or "",
        ]
        for row in sorted_rows
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _content_types_xml())
        archive.writestr("_rels/.rels", _root_rels_xml())
        archive.writestr("xl/workbook.xml", _workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        archive.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(table))


def fulfill_invoice_workbook_obligation(
    required_event: StateChangeEvent,
    observed_events: list[StateChangeEvent],
    licenses: list[ActionLicense],
    image_dir: Path | str,
    output_path: Path | str,
    ocr_fn: OcrFn,
) -> InvoiceFulfillment:
    initial_decision = evaluate_commit_obligation(required_event, observed_events, licenses)
    if initial_decision.allowed:
        return InvoiceFulfillment("already_satisfied", initial_decision, None, tuple())
    if initial_decision.reason != "missing_commit_obligation":
        return InvoiceFulfillment("blocked", initial_decision, None, tuple())

    rows = materialize_invoice_workbook(image_dir, output_path, ocr_fn)
    commit_event = StateChangeEvent(
        actor_role=required_event.actor_role,
        state_region=required_event.state_region,
        operation=required_event.operation,
        evidence=EvidenceBundle(
            types={"OcrTextEvidence", "WorkbookSchemaEvidence"},
            refs={row.filename for row in rows} | {"task:invoice_summary_schema"},
        ),
    )
    final_decision = evaluate_commit_obligation(required_event, observed_events + [commit_event], licenses)
    status = "fulfilled" if final_decision.allowed else "blocked"
    return InvoiceFulfillment(status, final_decision, commit_event, rows)


def _flush_ocr_block(blocks: dict[str, str], filename: str | None, lines: list[str]) -> None:
    if filename is None:
        return
    blocks[filename] = "\n".join(lines).strip()


def _extract_invoice_date(text: str) -> str | None:
    candidates: list[tuple[int, str | None]] = []
    for match in _ISO_DATE_RE.finditer(text):
        candidates.append(
            (
                match.start(),
                _valid_iso_date(
                    int(match.group("year")),
                    int(match.group("month")),
                    int(match.group("day")),
                ),
            )
        )
    for match in _SLASH_DATE_RE.finditer(text):
        candidates.append(
            (
                match.start(),
                _normalize_slash_date(
                    int(match.group("first")),
                    int(match.group("second")),
                    int(match.group("year")),
                ),
            )
        )
    for _, value in sorted(candidates, key=lambda item: item[0]):
        if value is not None:
            return value
    return None


def _normalize_slash_date(first: int, second: int, year: int) -> str | None:
    ddmm = _valid_iso_date(year, second, first)
    if ddmm is not None:
        return ddmm
    return _valid_iso_date(year, first, second)


def _valid_iso_date(year: int, month: int, day: int) -> str | None:
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def _extract_total_amount(text: str) -> str | None:
    lines = text.splitlines()
    for keyword in _TOTAL_KEYWORDS:
        for line in lines:
            upper = line.upper()
            if keyword not in upper:
                continue
            if any(exclusion in upper for exclusion in _EXCLUSION_KEYWORDS):
                continue
            amounts = [match.group("amount") for match in _MONEY_RE.finditer(line)]
            if amounts:
                return _format_amount(amounts[-1])
    return None


def _format_amount(raw_amount: str) -> str | None:
    try:
        return f"{Decimal(raw_amount.replace(',', '')):.2f}"
    except InvalidOperation:
        return None


def _worksheet_xml(rows: list[list[str]]) -> str:
    max_row = len(rows)
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            ref = f"{_column_name(col_index)}{row_index}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(value)}</t></is></c>')
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:C{max_row}"/>'
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
        '<sheets><sheet name="invoices" sheetId="1" r:id="rId1"/></sheets>'
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

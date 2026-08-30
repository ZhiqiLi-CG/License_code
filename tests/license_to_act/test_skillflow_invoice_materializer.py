from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from license_to_act.core import EvidenceBundle, StateChangeEvent
from license_to_act.examples import (
    skillflow_invoice_summary_license,
    skillflow_invoice_summary_required_commit,
)
from license_to_act.skillflow_invoice_materializer import (
    InvoiceRow,
    extract_ocr_blocks,
    fulfill_invoice_workbook_obligation,
    parse_invoice_text,
    write_invoice_workbook,
)


def test_parse_invoice_text_prefers_ddmm_but_falls_back_to_mmdd_when_needed():
    ddmm = """INVOICE
Date: 13/01/2024
SUBTOTAL: $334.95
TAX: $33.49
GRAND TOTAL: $368.44
"""
    mmdd = """INVOICE
Date: 02/14/2024
SUBTOTAL: $334.95
TAX: $33.49
TOTAL DUE: $368.44
"""

    assert parse_invoice_text("inv_013.jpg", ddmm) == InvoiceRow(
        filename="inv_013.jpg",
        date="2024-01-13",
        total_amount="368.44",
    )
    assert parse_invoice_text("inv_014.jpg", mmdd) == InvoiceRow(
        filename="inv_014.jpg",
        date="2024-02-14",
        total_amount="368.44",
    )


def test_parse_invoice_text_uses_total_keyword_priority_and_skips_exclusions():
    text = """INVOICE
Date: 2024-03-15
SUBTOTAL: $1,100.00
TAX: $99.00
AMOUNT: $1,000.00
GRAND TOTAL: $1,234.56
"""

    row = parse_invoice_text("inv_015.jpg", text)

    assert row == InvoiceRow(
        filename="inv_015.jpg",
        date="2024-03-15",
        total_amount="1234.56",
    )


def test_extract_ocr_blocks_reads_saved_terminal_evidence():
    dump = """===== inv_002.jpg =====
INVOICE
Date: 02/02/2024
TOTAL DUE: $368.44

===== inv_001.jpg =====
INVOICE
Date: 01/01/2024
GRAND TOTAL: $368.44
"""

    blocks = extract_ocr_blocks(dump)

    assert blocks == {
        "inv_001.jpg": "INVOICE\nDate: 01/01/2024\nGRAND TOTAL: $368.44",
        "inv_002.jpg": "INVOICE\nDate: 02/02/2024\nTOTAL DUE: $368.44",
    }


def test_write_invoice_workbook_creates_single_invoices_sheet_with_schema(tmp_path):
    output_path = tmp_path / "invoice_summary.xlsx"
    rows = [
        InvoiceRow("inv_002.jpg", None, None),
        InvoiceRow("inv_001.jpg", "2024-01-01", "368.44"),
    ]

    write_invoice_workbook(rows, output_path)

    assert _xlsx_sheet_names(output_path) == ["invoices"]
    assert _xlsx_inline_rows(output_path) == [
        ["filename", "date", "total_amount"],
        ["inv_001.jpg", "2024-01-01", "368.44"],
        ["inv_002.jpg", "", ""],
    ]


def test_fulfill_invoice_workbook_obligation_materializes_missing_commit(tmp_path):
    image_dir = tmp_path / "img"
    image_dir.mkdir()
    (image_dir / "inv_002.jpg").write_bytes(b"fake")
    (image_dir / "inv_001.jpg").write_bytes(b"fake")
    output_path = tmp_path / "invoice_summary.xlsx"
    ocr_texts = {
        "inv_001.jpg": "INVOICE\nDate: 01/01/2024\nGRAND TOTAL: $368.44\n",
        "inv_002.jpg": "INVOICE\nDate: 02/02/2024\nTOTAL DUE: $368.44\n",
    }
    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="input:/app/workspace/dataset/img",
            operation="ReadEvidence",
            evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs=set(ocr_texts)),
        )
    ]

    result = fulfill_invoice_workbook_obligation(
        required_event=skillflow_invoice_summary_required_commit(),
        observed_events=observed,
        licenses=[skillflow_invoice_summary_license()],
        image_dir=image_dir,
        output_path=output_path,
        ocr_fn=lambda path: ocr_texts[path.name],
    )

    assert result.status == "fulfilled"
    assert result.decision.allowed is True
    assert result.event is not None
    assert result.event.state_region == "output:/app/workspace/invoice_summary.xlsx"
    assert result.event.evidence.types == {"OcrTextEvidence", "WorkbookSchemaEvidence"}
    assert _xlsx_inline_rows(output_path) == [
        ["filename", "date", "total_amount"],
        ["inv_001.jpg", "2024-01-01", "368.44"],
        ["inv_002.jpg", "2024-02-02", "368.44"],
    ]


def test_replay_script_runs_directly_from_project_root(tmp_path):
    image_dir = tmp_path / "img"
    image_dir.mkdir()
    blocks = []
    for index in range(1, 16):
        filename = f"inv_{index:03d}.jpg"
        (image_dir / filename).write_bytes(b"fake")
        blocks.append(
            f"===== {filename} =====\n"
            "INVOICE\n"
            f"Date: 2024-01-{index:02d}\n"
            "GRAND TOTAL: $368.44\n"
        )
    trajectory_path = tmp_path / "trajectory.json"
    trajectory_path.write_text(json.dumps({"messages": ["\n".join(blocks)]}))
    output_dir = tmp_path / "out"

    proc = subprocess.run(
        [
            sys.executable,
            "scripts/replay_skillflow_invoice_obligation.py",
            "--trajectory",
            str(trajectory_path),
            "--image-dir",
            str(image_dir),
            "--output-dir",
            str(output_dir),
            "--oracle",
            str(tmp_path / "missing_oracle.xlsx"),
        ],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "fulfilled"
    assert payload["allowed"] is True
    assert payload["ocr_blocks"] == 15
    assert (output_dir / "invoice_summary.xlsx").exists()


def _xlsx_sheet_names(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return [sheet.attrib["name"] for sheet in root.findall("main:sheets/main:sheet", ns)]


def _xlsx_inline_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: list[list[str]] = []
    for row in root.findall("main:sheetData/main:row", ns):
        values = []
        for cell in row.findall("main:c", ns):
            text = cell.find("main:is/main:t", ns)
            values.append(text.text if text is not None and text.text is not None else "")
        rows.append(values)
    return rows

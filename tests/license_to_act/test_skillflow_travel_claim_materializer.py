from __future__ import annotations

import csv
import zipfile
from xml.etree import ElementTree

from license_to_act.skillflow_travel_claim_materializer import (
    TRAVEL_CLAIM_COLUMNS,
    build_travel_claim_rows,
    build_travel_claim_state_report,
    load_claim_roster,
    parse_claim_date,
    parse_travel_claim_text,
    write_travel_claim_workbook,
)


def test_parse_travel_claim_text_and_roster_join():
    parsed = parse_travel_claim_text(
        "claim_001.jpg",
        """
        Claim Ref: CLM-2024-007
        Purchase Date: 03/04/2024
        Tax 9.00
        Reimbursable Total
        $1,234.50
        """,
    )
    rows = build_travel_claim_rows(
        [parsed],
        {"CLM-2024-007": ("EMP-19", "TRIP-5")},
    )

    assert parsed["claim_code"] == "CLM-2024-007"
    assert parsed["date"] == "2024-04-03"
    assert parsed["total_amount"] == "1234.50"
    assert parsed["evidence_status"] == "complete"
    assert rows == [["claim_001.jpg", "CLM-2024-007", "EMP-19", "TRIP-5", "2024-04-03", "1234.50"]]


def test_parse_claim_date_prefers_day_first():
    assert parse_claim_date("01/02/2024") == "2024-02-01"
    assert parse_claim_date("2024-12-03") == "2024-12-03"


def test_load_roster_and_write_workbook(tmp_path):
    roster_path = tmp_path / "claim_roster.csv"
    with roster_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["claim_code", "employee_id", "trip_id"])
        writer.writeheader()
        writer.writerow({"claim_code": "CLM-2024-002", "employee_id": "EMP-02", "trip_id": "TRIP-02"})
    rows = [["claim_002.jpg", "CLM-2024-002", "EMP-02", "TRIP-02", "2024-05-06", "10.00"]]
    output = tmp_path / "travel_claims.xlsx"

    assert load_claim_roster(roster_path) == {"CLM-2024-002": ("EMP-02", "TRIP-02")}
    write_travel_claim_workbook(rows, output)

    assert _xlsx_sheet_names(output) == ["claims"]
    assert _xlsx_inline_rows(output) == [TRAVEL_CLAIM_COLUMNS, rows[0]]


def test_state_report_records_roster_authority_and_missing_rows(tmp_path):
    rows = [["claim_003.jpg", "CLM-2024-003", "", "", "2024-05-06", ""]]
    report = build_travel_claim_state_report(parsed_claims=[], rows=rows, output_path=tmp_path / "out.xlsx")

    assert report["evidence_types"] == [
        "OcrTextEvidence",
        "ClaimCodeEvidence",
        "RosterJoinEvidence",
        "WorkbookSchemaEvidence",
    ]
    assert report["artifact_gate"]["missing_required_rows"] == ["claim_003.jpg"]


def _xlsx_sheet_names(path):
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    return [sheet.attrib["name"] for sheet in root.findall(".//main:sheet", ns)]


def _xlsx_inline_rows(path):
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in root.findall(".//main:row", ns):
        values = []
        for cell in row.findall("main:c", ns):
            text = cell.find("main:is/main:t", ns)
            values.append("" if text is None else text.text or "")
        rows.append(values)
    return rows

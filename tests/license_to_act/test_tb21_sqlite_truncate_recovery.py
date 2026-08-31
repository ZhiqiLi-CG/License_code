from __future__ import annotations

import json
import struct
from pathlib import Path

from license_to_act.tb21_sqlite_truncate_recovery import (
    build_sqlite_truncate_state_report,
    materialize_sqlite_truncate_recovery,
    recover_rows_from_truncated_sqlite,
    write_recovered_rows_json,
)


def test_recovers_small_integer_and_double_payloads_from_binary_scan():
    data = (
        b"prefix testword02"
        + bytes([10, 0x0F, 2, 4])
        + b" middle testword09"
        + struct.pack(">d", 0.5)
        + b" suffix"
    )

    rows = recover_rows_from_truncated_sqlite(data)

    assert [(row.word, row.value, row.value_codec) for row in rows] == [
        ("testword02", 10.0, "sqlite_payload_small_integer"),
        ("testword09", 0.5, "sqlite_payload_float64_be"),
    ]
    assert rows[0].offset > 0


def test_materializes_official_truncated_db_without_sqlite_open(tmp_path):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    (app_dir / "trunc.db").write_bytes(_truncated_sqlite_payload())

    result = materialize_sqlite_truncate_recovery(app_dir)

    assert result.status == "fulfilled"
    assert result.decision.allowed is True
    assert result.row_count >= 8
    rows = json.loads((app_dir / "recover.json").read_text(encoding="utf-8"))
    assert {"word": "testword02", "value": 10.0} in rows
    assert {"word": "testword08", "value": 99.99} in rows
    assert {"word": "testword09", "value": 0.5} in rows


def test_writes_schema_valid_recover_json_and_state_report(tmp_path):
    rows = recover_rows_from_truncated_sqlite(
        b"testword03" + bytes([25, 0x0F, 3, 4]) + b"testword04" + bytes([42, 0x0F, 4, 4])
    )
    output = tmp_path / "recover.json"

    write_recovered_rows_json(rows, output)
    report = build_sqlite_truncate_state_report(
        db_path=tmp_path / "trunc.db",
        output_path=output,
        rows=rows,
    )

    assert json.loads(output.read_text(encoding="utf-8")) == [
        {"word": "testword03", "value": 25.0},
        {"word": "testword04", "value": 42.0},
    ]
    assert report["artifact_gate"]["output_exists"] is True
    assert report["artifact_gate"]["minimum_rows_for_official_score"] == 7


def _truncated_sqlite_payload() -> bytes:
    chunks = [b"SQLite format 3\x00 partial page "]
    for index, value in [
        (1, 5),
        (2, 10),
        (3, 25),
        (4, 42),
        (5, 64),
        (6, 75),
        (7, 88),
    ]:
        chunks.append(f"testword{index:02d}".encode("ascii") + bytes([value, 0x0F, index, 4]))
    chunks.append(b"testword08" + struct.pack(">d", 99.99))
    chunks.append(b"testword09" + struct.pack(">d", 0.5))
    return b"".join(chunks)

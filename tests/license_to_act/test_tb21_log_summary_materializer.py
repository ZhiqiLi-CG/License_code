from __future__ import annotations

import csv
from pathlib import Path

import pytest


def test_counts_only_bracketed_severity_tokens_by_date_window(tmp_path: Path) -> None:
    materializer = _import_materializer()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    _write_log(
        logs_dir / "2025-08-12_app.log",
        [
            "2025-08-12 01:00:00 [ERROR] Database connection lost",
            "2025-08-12 01:01:00 [WARNING] Next attempt will ERROR. Retrying...",
            "2025-08-12 01:02:00 [INFO] Service started",
            "2025-08-12 01:03:00 [DEBUG] ERROR string in debug should not count",
        ],
    )
    _write_log(
        logs_dir / "2025-08-06_db.log",
        [
            "2025-08-06 02:00:00 [ERROR] Deadlock detected",
            "2025-08-06 02:01:00 [INFO] Backup complete",
        ],
    )
    _write_log(
        logs_dir / "2025-07-20_auth.log",
        [
            "2025-07-20 03:00:00 [WARNING] Disk space low",
            "2025-07-20 03:01:00 [INFO] Login successful",
        ],
    )

    counts = materializer.count_log_severities(logs_dir, reference_date="2025-08-12")

    assert counts[("today", "ERROR")] == 1
    assert counts[("today", "WARNING")] == 1
    assert counts[("today", "INFO")] == 1
    assert counts[("last_7_days", "ERROR")] == 2
    assert counts[("last_7_days", "WARNING")] == 1
    assert counts[("last_7_days", "INFO")] == 2
    assert counts[("last_30_days", "WARNING")] == 2
    assert counts[("month_to_date", "WARNING")] == 1
    assert counts[("total", "INFO")] == 3


def test_materializes_official_summary_csv_and_state_report(tmp_path: Path) -> None:
    materializer = _import_materializer()
    app_dir = tmp_path / "app"
    logs_dir = app_dir / "logs"
    logs_dir.mkdir(parents=True)
    _write_log(logs_dir / "2025-08-12_api.log", ["2025-08-12 00:00:01 [ERROR] failure"])
    _write_log(logs_dir / "2025-08-01_api.log", ["2025-08-01 00:00:01 [INFO] ok"])

    result = materializer.materialize_log_summary(app_dir, reference_date="2025-08-12")

    assert result.status == "fulfilled"
    assert result.decision.allowed is True
    assert result.row_count == 15
    assert result.event.state_region == "output:/app/summary.csv"
    assert result.event.evidence.types == {
        "LogFilenameDateEvidence",
        "BracketedSeverityEvidence",
        "DateRangeCountEvidence",
        "CsvSchemaEvidence",
    }

    with (app_dir / "summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == ["period", "severity", "count"]
    assert ["today", "ERROR", "1"] in rows
    assert ["month_to_date", "INFO", "1"] in rows
    assert ["total", "WARNING", "0"] in rows


def test_harbor_agent_export_names_log_summary_transaction() -> None:
    from license_to_act.harbor_agents import LicenseToActTB21LogSummaryAgent

    assert LicenseToActTB21LogSummaryAgent.name() == "license-to-act-tb21-log-summary"


def _import_materializer():
    try:
        from license_to_act import tb21_log_summary_materializer
    except ModuleNotFoundError as exc:
        pytest.fail(f"log-summary materializer module is missing: {exc}")
    return tb21_log_summary_materializer


def _write_log(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

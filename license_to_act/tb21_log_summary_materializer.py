from __future__ import annotations

from collections import Counter
import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
import re

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_event


PERIODS = ("today", "last_7_days", "last_30_days", "month_to_date", "total")
SEVERITIES = ("ERROR", "WARNING", "INFO")
FILENAME_DATE_FORMAT = "%Y-%m-%d"
SEVERITY_RE = re.compile(r"\[(ERROR|WARNING|INFO)\]")


@dataclass(frozen=True)
class LogSummaryResult:
    status: str
    decision: Decision
    event: StateChangeEvent
    output_path: Path
    row_count: int


def tb21_log_summary_license() -> ActionLicense:
    return ActionLicense(
        name="tb21_log_summary_csv",
        actor_role="terminal_agent",
        state_region="output:/app/summary.csv",
        operation="WriteSummaryCsv",
        required_evidence={
            "LogFilenameDateEvidence",
            "BracketedSeverityEvidence",
            "DateRangeCountEvidence",
            "CsvSchemaEvidence",
        },
    )


def count_log_severities(logs_dir: Path, *, reference_date: str = "2025-08-12") -> dict[tuple[str, str], int]:
    ref = date.fromisoformat(reference_date)
    counts: Counter[tuple[str, str]] = Counter()
    for log_path in sorted(logs_dir.glob("*.log")):
        log_date = _date_from_filename(log_path)
        active_periods = _periods_for_date(log_date, ref)
        for severity in _iter_line_severities(log_path):
            for period in active_periods:
                counts[(period, severity)] += 1

    return {(period, severity): counts[(period, severity)] for period in PERIODS for severity in SEVERITIES}


def write_summary_csv(counts: dict[tuple[str, str], int], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["period", "severity", "count"])
        for period in PERIODS:
            for severity in SEVERITIES:
                writer.writerow([period, severity, str(counts[(period, severity)])])


def materialize_log_summary(
    app_dir: Path,
    *,
    reference_date: str = "2025-08-12",
    licenses: list[ActionLicense] | None = None,
) -> LogSummaryResult:
    app_dir = app_dir.resolve()
    output_path = app_dir / "summary.csv"
    counts = count_log_severities(app_dir / "logs", reference_date=reference_date)
    write_summary_csv(counts, output_path)

    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="output:/app/summary.csv",
        operation="WriteSummaryCsv",
        evidence=EvidenceBundle(
            types={
                "LogFilenameDateEvidence",
                "BracketedSeverityEvidence",
                "DateRangeCountEvidence",
                "CsvSchemaEvidence",
            },
            refs={"/app/logs", "/app/summary.csv"},
        ),
    )
    decision = evaluate_event(event, licenses or [tb21_log_summary_license()])
    return LogSummaryResult(
        status="fulfilled" if decision.allowed else "blocked",
        decision=decision,
        event=event,
        output_path=output_path,
        row_count=len(PERIODS) * len(SEVERITIES),
    )


def _date_from_filename(path: Path) -> date:
    return datetime.strptime(path.name.split("_", 1)[0], FILENAME_DATE_FORMAT).date()


def _iter_line_severities(path: Path) -> list[str]:
    severities: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = SEVERITY_RE.search(line)
        if match is not None:
            severities.append(match.group(1))
    return severities


def _periods_for_date(log_date: date, reference_date: date) -> tuple[str, ...]:
    periods = ["total"]
    if log_date == reference_date:
        periods.append("today")
    if reference_date - timedelta(days=6) <= log_date <= reference_date:
        periods.append("last_7_days")
    if reference_date - timedelta(days=29) <= log_date <= reference_date:
        periods.append("last_30_days")
    if date(reference_date.year, reference_date.month, 1) <= log_date <= reference_date:
        periods.append("month_to_date")
    return tuple(periods)

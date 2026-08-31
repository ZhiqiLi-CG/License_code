from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.submission_scale_plan import build_submission_scale_plan, write_submission_scale_plan


def test_build_submission_scale_plan_keeps_next_runs_story_aligned() -> None:
    plan = build_submission_scale_plan(Path("/data/zhiqi/License"))

    summary = plan["summary"]
    assert summary["scale_target_rows"] == 7
    assert summary["benchmarks_targeted"] == 3
    assert summary["current_clean_positive_passes"] == 25
    assert summary["current_clean_positive_trials"] == 25
    assert summary["current_faithful_baseline_trials"] == 5
    assert summary["mechanism_ablation_rows"] == 5
    assert summary["completed_mechanism_ablation_rows"] == 3
    assert summary["story_gate_checks"] == 12

    rows = plan["rows"]
    assert [row["target_id"] for row in rows] == [
        "S1_TAU2_WRITE_FAMILIES",
        "S2_TERMINAL_AUTHORITY_PILOT",
        "S3_SKILLFLOW_OBLIGATION_FAMILIES",
        "S4_MODEL_BREADTH",
        "S5_FAITHFUL_BASELINE_LADDER",
        "S6_MECHANISM_ABLATION_COMPLETION",
        "S7_FREEZE_AND_STATISTICS",
    ]
    assert all("proposal/evidence/authority/commit" in row["inclusion_rule"] for row in rows)
    assert all("RSI" not in " ".join(row.values()) for row in rows)


def test_write_submission_scale_plan_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_submission_scale_plan(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "submission_scale_plan.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["scale_plan_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["scale_plan_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 7
    assert rows[0]["target_id"] == "S1_TAU2_WRITE_FAMILIES"
    assert "airline, retail, banking, and telecom" in rows[0]["scale_target"]

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTASubmissionScaleRows}{7}" in tex
    assert "\\newcommand{\\LTASubmissionScaleBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTASubmissionCurrentCleanPasses}{25}" in tex
    assert "\\newcommand{\\LTASubmissionCurrentCleanTrials}{25}" in tex
    assert "\\newcommand{\\LTASubmissionCompletedAblationRows}{3}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["scale_target_rows"] == 7


def test_export_submission_scale_plan_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "submission_scale_plan.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_submission_scale_plan.py",
            "--paper-data-dir",
            str(tmp_path / "paper-data"),
            "--paper-sections-dir",
            str(tmp_path / "sections"),
            "--summary",
            str(summary_path),
        ],
        cwd="/data/zhiqi/License/License_code",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert str(summary_path) in result.stdout
    assert (tmp_path / "paper-data" / "submission_scale_plan.csv").exists()
    assert (tmp_path / "sections" / "generated_scale_plan_numbers.tex").exists()

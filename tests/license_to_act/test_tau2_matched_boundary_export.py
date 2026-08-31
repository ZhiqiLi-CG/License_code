from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.tau2_matched_boundary_export import (
    build_tau2_matched_boundary_export,
    write_tau2_matched_boundary_export,
)


def test_build_tau2_matched_boundary_export_uses_real_matched_pair() -> None:
    report = build_tau2_matched_boundary_export(Path("/data/zhiqi/License"))

    summary = report["summary"]
    assert summary["pairs"] == 5
    assert summary["complete_pairs"] == 5
    assert summary["baseline_trials"] == 5
    assert summary["boundary_trials"] == 5
    assert summary["baseline_mean_reward"] == 0.0
    assert summary["boundary_mean_reward"] == 1.0
    assert summary["reward_delta"] == 1.0
    assert summary["baseline_read_correct_write_wrong"] == 5
    assert summary["boundary_read_correct_write_wrong"] == 0
    assert summary["boundary_vetoes"] == 5
    assert summary["boundary_regressions"] == 0

    rows = report["rows"]
    assert len(rows) == 10
    baseline = next(row for row in rows if row["condition"] == "baseline")
    boundary = next(row for row in rows if row["condition"] == "action_boundary")
    assert baseline["actor_model"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert baseline["task_id"] == "48"
    assert baseline["reward"] == "0"
    assert baseline["read_correct_write_wrong"] == "yes"
    assert boundary["reward"] == "1"
    assert boundary["boundary_vetoes"] == "1"
    assert boundary["read_correct_write_wrong"] == "no"
    assert sum(1 for row in rows if row["condition"] == "baseline") == 5
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 5
    assert sum(int(row["boundary_vetoes"]) for row in rows) == 5


def test_write_tau2_matched_boundary_export_outputs_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_tau2_matched_boundary_export(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "tau2_matched_boundary.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 10
    assert [row["condition"] for row in rows[:2]] == ["baseline", "action_boundary"]
    assert sum(1 for row in rows if row["condition"] == "baseline") == 5
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 5

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTATauTwoMatchedPairs}{5}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedCompletePairs}{5}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineTrials}{5}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryTrials}{5}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineMeanReward}{0}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryMeanReward}{1}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedRewardDelta}{1}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineRCWW}{5}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryVetoes}{5}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["boundary_regressions"] == 0


def test_export_tau2_matched_boundary_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "tau2_matched_boundary.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_tau2_matched_boundary.py",
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
    assert (tmp_path / "paper-data" / "tau2_matched_boundary.csv").exists()
    assert (tmp_path / "sections" / "generated_tau2_matched_boundary_numbers.tex").exists()

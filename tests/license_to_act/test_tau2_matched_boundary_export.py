from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.tau2_matched_boundary_export import (
    build_tau2_matched_boundary_export,
    compact_tau2_matched_report,
    write_tau2_matched_boundary_export,
)


def test_build_tau2_matched_boundary_export_uses_real_matched_pair() -> None:
    report = build_tau2_matched_boundary_export(Path("/data/zhiqi/License"))

    summary = report["summary"]
    assert summary["pairs"] == 20
    assert summary["complete_pairs"] == 20
    assert summary["baseline_trials"] == 20
    assert summary["boundary_trials"] == 20
    assert summary["baseline_mean_reward"] == 0.0
    assert summary["boundary_mean_reward"] == 1.0
    assert summary["reward_delta"] == 1.0
    assert summary["baseline_read_correct_write_wrong"] == 20
    assert summary["boundary_read_correct_write_wrong"] == 0
    assert summary["boundary_vetoes"] == 26
    assert summary["boundary_regressions"] == 0

    rows = report["rows"]
    assert len(rows) == 40
    baseline = next(row for row in rows if row["condition"] == "baseline")
    boundary = next(row for row in rows if row["condition"] == "action_boundary")
    assert baseline["actor_model"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert baseline["task_id"] == "48"
    assert baseline["reward"] == "0"
    assert baseline["read_correct_write_wrong"] == "yes"
    assert boundary["reward"] == "1"
    assert boundary["read_correct_write_wrong"] == "no"
    assert sum(1 for row in rows if row["condition"] == "baseline") == 20
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 20
    assert sum(int(row["boundary_vetoes"]) for row in rows) == 26


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
    assert len(rows) == 40
    assert [row["condition"] for row in rows[:2]] == ["baseline", "action_boundary"]
    assert sum(1 for row in rows if row["condition"] == "baseline") == 20
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 20

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTATauTwoMatchedPairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedCompletePairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineTrials}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryTrials}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineMeanReward}{0}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryMeanReward}{1}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedRewardDelta}{1}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineRCWW}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryVetoes}{26}" in tex

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


def test_compact_tau2_matched_report_adds_paper_metadata(tmp_path: Path) -> None:
    full_report = {
        "runs": [
            {
                "pair_id": "airline-48-seed-800",
                "condition": "baseline",
                "task_id": "48",
                "reward": 0.0,
                "cancel_tool_calls": 1,
                "read_correct_write_wrong": True,
                "boundary_records": [],
                "simulation": {"messages": ["large payload omitted"]},
            },
            {
                "pair_id": "airline-48-seed-800",
                "condition": "action_boundary",
                "task_id": "48",
                "reward": 1.0,
                "cancel_tool_calls": 0,
                "read_correct_write_wrong": False,
                "boundary_records": [{"allowed": False}],
                "simulation": {"messages": ["large payload omitted"]},
            },
        ]
    }
    source = tmp_path / "full.json"
    source.write_text(json.dumps(full_report), encoding="utf-8")

    compact = compact_tau2_matched_report(
        source,
        domain="airline",
        actor_model="Mistral-Small-3.2-24B-Instruct-2506",
        user_mode="scripted_real_task_user",
        paper_use="matched_tau2_k20",
        expected_complete_pairs=1,
    )

    assert compact["source_full_report"] == str(source)
    assert compact["summary"]["complete_pairs"] == 1
    assert compact["summary"]["baseline_trials"] == 1
    assert compact["summary"]["boundary_trials"] == 1
    assert "simulation" not in compact["runs"][0]
    assert compact["runs"][0]["domain"] == "airline"
    assert compact["runs"][0]["seed"] == 800
    assert compact["runs"][0]["actor_model"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert compact["runs"][1]["paper_use"] == "matched_tau2_k20"


def test_compact_tau2_matched_boundary_cli_writes_requested_output(tmp_path: Path) -> None:
    source = tmp_path / "full.json"
    output = tmp_path / "compact.json"
    source.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "pair_id": "airline-48-seed-800",
                        "condition": "baseline",
                        "task_id": "48",
                        "reward": 0.0,
                        "cancel_tool_calls": 1,
                        "read_correct_write_wrong": True,
                        "boundary_records": [],
                        "simulation": {"messages": ["large payload omitted"]},
                    },
                    {
                        "pair_id": "airline-48-seed-800",
                        "condition": "action_boundary",
                        "task_id": "48",
                        "reward": 1.0,
                        "cancel_tool_calls": 0,
                        "read_correct_write_wrong": False,
                        "boundary_records": [{"allowed": False}],
                        "simulation": {"messages": ["large payload omitted"]},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compact_tau2_matched_boundary.py",
            "--source",
            str(source),
            "--output",
            str(output),
            "--domain",
            "airline",
            "--actor-model",
            "Mistral-Small-3.2-24B-Instruct-2506",
            "--user-mode",
            "scripted_real_task_user",
            "--paper-use",
            "matched_tau2_k20",
            "--expected-complete-pairs",
            "1",
        ],
        cwd="/data/zhiqi/License/License_code",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert str(output) in result.stdout
    compact = json.loads(output.read_text(encoding="utf-8"))
    assert compact["summary"]["complete_pairs"] == 1
    assert compact["runs"][0]["seed"] == 800
    assert "simulation" not in compact["runs"][0]

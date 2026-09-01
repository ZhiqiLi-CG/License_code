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
    assert summary["pairs"] == 80
    assert summary["complete_pairs"] == 80
    assert summary["baseline_trials"] == 80
    assert summary["boundary_trials"] == 80
    assert summary["baseline_mean_reward"] == 0.0125
    assert summary["boundary_mean_reward"] == 1.0
    assert summary["reward_delta"] == 0.9875
    assert summary["baseline_read_correct_write_wrong"] == 20
    assert summary["boundary_read_correct_write_wrong"] == 0
    assert summary["boundary_vetoes"] == 26
    assert summary["boundary_allows"] == 60
    assert summary["boundary_completion_triggers"] == 60
    assert summary["baseline_retail_exchange_tool_calls"] == 1
    assert summary["boundary_retail_exchange_tool_calls"] == 60
    assert summary["baseline_state_change_tool_calls"] == 22
    assert summary["boundary_state_change_tool_calls"] == 60
    assert summary["boundary_regressions"] == 0
    assert summary["domains"] == 2
    assert summary["actor_models"] == 2
    assert summary["blocks"] == 4

    rows = report["rows"]
    assert len(rows) == 160
    baseline = next(
        row
        for row in rows
        if row["condition"] == "baseline" and row["paper_use"] == "matched_tau2_k20"
    )
    boundary = next(
        row
        for row in rows
        if row["condition"] == "action_boundary" and row["paper_use"] == "matched_tau2_k20"
    )
    assert baseline["actor_model"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert baseline["task_id"] == "48"
    assert baseline["reward"] == "0"
    assert baseline["read_correct_write_wrong"] == "yes"
    assert boundary["reward"] == "1"
    assert boundary["read_correct_write_wrong"] == "no"
    retail_boundary = next(
        row
        for row in rows
        if row["condition"] == "action_boundary"
        and row["paper_use"] == "matched_tau2_retail_completion_k20"
    )
    assert retail_boundary["actor_model"] == "openai/Qwen3.8-27B-long32k"
    assert retail_boundary["task_id"] == "0"
    assert retail_boundary["reward"] == "1"
    assert retail_boundary["retail_exchange_tool_calls"] == "1"
    assert retail_boundary["state_change_tool_calls"] == "1"
    retail_completion_rows = [
        row for row in rows if row["paper_use"] == "matched_tau2_retail_completion_k20"
    ]
    assert len(retail_completion_rows) == 40
    assert sum(
        1
        for row in retail_completion_rows
        if row["condition"] == "baseline" and row["reward"] == "1"
    ) == 1
    assert sum(
        1
        for row in retail_completion_rows
        if row["condition"] == "action_boundary" and row["reward"] == "1"
    ) == 20
    retail_scope_boundary = next(
        row
        for row in rows
        if row["condition"] == "action_boundary"
        and row["paper_use"] == "matched_tau2_retail_scope_k20"
    )
    assert retail_scope_boundary["actor_model"] == "openai/Qwen3.8-27B-long32k"
    assert retail_scope_boundary["task_id"] == "1"
    assert retail_scope_boundary["reward"] == "1"
    assert retail_scope_boundary["retail_exchange_tool_calls"] == "1"
    assert retail_scope_boundary["state_change_tool_calls"] == "1"
    retail_scope_family_rows = [
        row for row in rows if row["paper_use"] == "matched_tau2_retail_scope_family_k20"
    ]
    assert len(retail_scope_family_rows) == 40
    assert {row["task_id"] for row in retail_scope_family_rows} == {"6", "7", "8", "9"}
    assert sum(
        1
        for row in retail_scope_family_rows
        if row["condition"] == "action_boundary" and row["reward"] == "1"
    ) == 20
    assert sum(1 for row in rows if row["condition"] == "baseline") == 80
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 80
    assert sum(int(row["boundary_vetoes"]) for row in rows) == 26
    assert sum(int(row["boundary_allows"]) for row in rows) == 60

    blocks = {block["paper_use"]: block for block in report["blocks"]}
    assert blocks["matched_tau2_k20"]["complete_pairs"] == 20
    assert blocks["matched_tau2_k20"]["boundary_vetoes"] == 26
    assert blocks["matched_tau2_retail_completion_k20"]["complete_pairs"] == 20
    assert blocks["matched_tau2_retail_completion_k20"]["boundary_allows"] == 20
    assert blocks["matched_tau2_retail_completion_k20"]["boundary_completion_triggers"] == 20
    assert blocks["matched_tau2_retail_scope_k20"]["complete_pairs"] == 20
    assert blocks["matched_tau2_retail_scope_k20"]["boundary_allows"] == 20
    assert blocks["matched_tau2_retail_scope_k20"]["boundary_completion_triggers"] == 20
    assert blocks["matched_tau2_retail_scope_family_k20"]["complete_pairs"] == 20
    assert blocks["matched_tau2_retail_scope_family_k20"]["boundary_allows"] == 20
    assert blocks["matched_tau2_retail_scope_family_k20"]["boundary_completion_triggers"] == 20


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
    assert len(rows) == 160
    assert [row["condition"] for row in rows[:2]] == ["baseline", "action_boundary"]
    assert sum(1 for row in rows if row["condition"] == "baseline") == 80
    assert sum(1 for row in rows if row["condition"] == "action_boundary") == 80

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTATauTwoMatchedPairs}{80}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedCompletePairs}{80}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineTrials}{80}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryTrials}{80}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineMeanReward}{0.013}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryMeanReward}{1}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedRewardDelta}{0.988}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBaselineRCWW}{20}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryVetoes}{26}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBoundaryAllows}{60}" in tex
    assert "\\newcommand{\\LTATauTwoMatchedBlocks}{4}" in tex
    assert "\\newcommand{\\LTATauTwoAirlineMatchedCompletePairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailMatchedCompletePairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailMatchedBoundaryCompletionTriggers}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailMatchedBoundaryRetailExchangeCalls}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeMatchedCompletePairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeMatchedBoundaryCompletionTriggers}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeMatchedBoundaryRetailExchangeCalls}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeFamilyMatchedCompletePairs}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeFamilyMatchedBoundaryCompletionTriggers}{20}" in tex
    assert "\\newcommand{\\LTATauTwoRetailScopeFamilyMatchedBoundaryRetailExchangeCalls}{20}" in tex

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
    assert compact["runs"][0]["retail_exchange_tool_calls"] == 0
    assert compact["runs"][0]["state_change_tool_calls"] == 1
    assert compact["runs"][0]["actor_model"] == "Mistral-Small-3.2-24B-Instruct-2506"
    assert compact["runs"][1]["paper_use"] == "matched_tau2_k20"


def test_compact_tau2_matched_report_can_filter_task_ids(tmp_path: Path) -> None:
    full_report = {
        "runs": [
            {
                "pair_id": "retail-0-seed-1300",
                "condition": "baseline",
                "task_id": "0",
                "reward": 0.0,
                "retail_exchange_tool_calls": 0,
                "state_change_tool_calls": 0,
                "boundary_records": [],
            },
            {
                "pair_id": "retail-0-seed-1300",
                "condition": "action_boundary",
                "task_id": "0",
                "reward": 1.0,
                "retail_exchange_tool_calls": 1,
                "state_change_tool_calls": 1,
                "boundary_records": [{"allowed": True, "completion_triggered": True}],
            },
            {
                "pair_id": "retail-1-seed-1300",
                "condition": "baseline",
                "task_id": "1",
                "reward": 0.0,
                "retail_exchange_tool_calls": 0,
                "state_change_tool_calls": 0,
                "boundary_records": [],
            },
            {
                "pair_id": "retail-1-seed-1300",
                "condition": "action_boundary",
                "task_id": "1",
                "reward": 1.0,
                "retail_exchange_tool_calls": 1,
                "state_change_tool_calls": 1,
                "boundary_records": [{"allowed": True, "completion_triggered": True}],
            },
        ]
    }
    source = tmp_path / "full.json"
    source.write_text(json.dumps(full_report), encoding="utf-8")

    compact = compact_tau2_matched_report(
        source,
        domain="retail",
        actor_model="openai/Qwen3.8-27B-long32k",
        user_mode="scripted_real_task_user",
        paper_use="matched_tau2_retail_completion_k20",
        expected_complete_pairs=1,
        task_ids=["0"],
    )

    assert compact["summary"]["complete_pairs"] == 1
    assert {run["task_id"] for run in compact["runs"]} == {"0"}
    assert {run["pair_id"] for run in compact["runs"]} == {"retail-0-seed-1300"}
    assert "simulation" not in compact["runs"][0]
    assert compact["runs"][0]["domain"] == "retail"
    assert compact["runs"][0]["seed"] == 1300
    assert compact["runs"][0]["retail_exchange_tool_calls"] == 0
    assert compact["runs"][0]["state_change_tool_calls"] == 0
    assert compact["runs"][0]["actor_model"] == "openai/Qwen3.8-27B-long32k"
    assert compact["runs"][1]["paper_use"] == "matched_tau2_retail_completion_k20"


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

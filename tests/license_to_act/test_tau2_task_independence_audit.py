from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.tau2_task_independence_audit import (
    build_tau2_task_independence_audit,
    write_tau2_task_independence_audit,
)


def test_tau2_task_independence_audit_reports_unique_tasks_and_macro_scores() -> None:
    audit = build_tau2_task_independence_audit(Path("/data/zhiqi/License"))

    summary = audit["summary"]
    assert summary["complete_pairs"] == 100
    assert summary["unique_task_count"] == 7
    assert summary["domain_count"] == 2
    assert summary["actor_model_count"] == 2
    assert summary["user_mode_count"] == 2
    assert summary["fixture_block_count"] == 5
    assert summary["task_condition_block_count"] == 8
    assert summary["seed_to_unique_task_ratio"] == 14.286
    assert summary["macro_task_baseline_mean_reward"] == 0.007
    assert summary["macro_task_boundary_mean_reward"] == 1.0
    assert summary["macro_task_reward_delta"] == 0.993
    assert summary["boundary_regressions"] == 0

    rows = {(row["domain"], row["task_id"], row["user_mode"]) for row in audit["rows"]}
    assert ("airline", "48", "llm_user") in rows
    assert ("airline", "48", "scripted_real_task_user") in rows
    assert ("retail", "0", "scripted_real_task_user") in rows
    assert ("retail", "9", "scripted_real_task_user") in rows
    assert all(row["paper_use"].startswith("matched_tau2") for row in audit["rows"])
    assert all(row["counts_as_main_matched"] == "yes" for row in audit["rows"])


def test_write_tau2_task_independence_audit_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_tau2_task_independence_audit(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "tau2_task_independence_audit.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["audit_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["audit_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 8
    assert {row["domain"] for row in rows} == {"airline", "retail"}

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTATauTwoIndependenceUniqueTasks}{7}" in tex
    assert "\\newcommand{\\LTATauTwoIndependenceTaskConditionBlocks}{8}" in tex
    assert "\\newcommand{\\LTATauTwoIndependenceCompletePairs}{100}" in tex
    assert "\\newcommand{\\LTATauTwoIndependenceSeedToTaskRatio}{14.286}" in tex
    assert "\\newcommand{\\LTATauTwoIndependenceMacroTaskBoundaryMeanReward}{1.000}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["unique_task_count"] == 7


def test_export_tau2_task_independence_audit_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "tau2_task_independence_audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_tau2_task_independence_audit.py",
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
    assert (tmp_path / "paper-data" / "tau2_task_independence_audit.csv").exists()
    assert (tmp_path / "sections" / "generated_tau2_independence_numbers.tex").exists()

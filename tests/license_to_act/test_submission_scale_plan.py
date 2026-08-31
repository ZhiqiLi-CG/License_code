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
    assert summary["scale_target_rows"] >= 18
    assert summary["benchmarks_targeted"] == 3
    assert summary["model_families_targeted"] >= 3
    assert summary["min_task_types_per_benchmark"] >= 5
    assert summary["faithful_baseline_scale_rows"] >= 3
    assert summary["mechanism_ablation_scale_rows"] >= 3
    assert summary["baseline_ablation_overlap"] == 0
    assert summary["total_target_trials"] >= 180
    assert summary["current_clean_positive_passes"] == 30
    assert summary["current_clean_positive_trials"] == 30
    assert summary["current_faithful_baseline_trials"] == 25
    assert summary["mechanism_ablation_rows"] == 5
    assert summary["completed_mechanism_ablation_rows"] == 5
    assert summary["story_gate_checks"] == 19

    rows = plan["rows"]
    assert len(rows) == summary["scale_target_rows"]
    assert all(row["benchmark"] for row in rows)
    assert all(row["task_type"] for row in rows)
    assert all(row["model_family"] for row in rows)
    assert all(row["condition_role"] for row in rows)
    assert all(int(row["target_n"]) > 0 for row in rows)
    assert all(row["paper_use"] for row in rows)
    assert all("reason/prepare/commit" in row["inclusion_rule"] for row in rows)
    assert all("RSI" not in " ".join(row.values()) for row in rows)

    task_types_by_benchmark: dict[str, set[str]] = {}
    for row in rows:
        task_types_by_benchmark.setdefault(row["benchmark"], set()).add(row["task_type"])
    assert task_types_by_benchmark["tau2-Bench"] >= {
        "policy-invalid write",
        "authorized write",
        "refund or compensation",
        "retail exchange",
        "account or plan mutation",
    }
    assert len(task_types_by_benchmark["Terminal-Bench 2.1"]) >= 5
    assert len(task_types_by_benchmark["SkillFlow"]) >= 5

    roles = {row["condition_role"] for row in rows}
    assert "faithful_baseline" in roles
    assert "mechanism_ablation" in roles


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
    assert len(rows) == output["summary"]["scale_target_rows"]
    assert rows[0]["target_id"] == "S1_TAU2_WRITE_FAMILIES"
    assert "airline, retail, banking, and telecom" in rows[0]["scale_target"]
    assert set(rows[0]) >= {
        "benchmark",
        "task_type",
        "model_family",
        "condition_role",
        "target_n",
        "paper_use",
    }

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTASubmissionScaleRows}" in tex
    assert "\\newcommand{\\LTASubmissionScaleBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTASubmissionScaleModelFamilies}" in tex
    assert "\\newcommand{\\LTASubmissionScaleMinTaskTypes}{5}" in tex
    assert "\\newcommand{\\LTASubmissionScaleTargetTrials}" in tex
    assert "\\newcommand{\\LTASubmissionCurrentCleanPasses}{30}" in tex
    assert "\\newcommand{\\LTASubmissionCurrentCleanTrials}{30}" in tex
    assert "\\newcommand{\\LTASubmissionCompletedAblationRows}{5}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["scale_target_rows"] >= 18


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

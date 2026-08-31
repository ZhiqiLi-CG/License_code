from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.submission_experiment_blueprint import (
    build_submission_experiment_blueprint,
    write_submission_experiment_blueprint,
)


def test_build_submission_experiment_blueprint_separates_story_scale_baselines_and_ablations() -> None:
    blueprint = build_submission_experiment_blueprint(Path("/data/zhiqi/License"))

    summary = blueprint["summary"]
    assert summary["blueprint_rows"] == 12
    assert summary["benchmark_families"] == 3
    assert summary["target_model_slots"] == 5
    assert summary["minimum_planned_run_cells"] == 1005
    assert summary["main_positive_scale_run_cells"] == 764
    assert summary["faithful_baseline_blocks"] == 2
    assert summary["mechanism_ablation_blocks"] == 1
    assert summary["baseline_ablation_overlap"] == 0
    assert summary["current_clean_positive_passes"] == 25
    assert summary["current_clean_positive_trials"] == 25

    rows = blueprint["rows"]
    assert [row["blueprint_id"] for row in rows] == [
        "E1_TAU2_AIRLINE_WRITE_AUTHORITY",
        "E2_TAU2_CROSS_DOMAIN_WRITES",
        "E3_TB_12_TASK_AUTHORITY_PILOT",
        "E4_TB_STRATIFIED_MAIN_SWEEP",
        "E5_SKILLFLOW_ARTIFACT_OBLIGATIONS",
        "E6_SKILLFLOW_SKILL_AUTHORITY_TRANSFER",
        "E7_MODEL_BREADTH_HELDOUT",
        "E8_STRONG_AGENT_BASELINES",
        "E9_FAITHFUL_OPEN_MODEL_LADDER",
        "E10_MECHANISM_CUTS",
        "E11_COMPILER_GENERATION_TRANSFER",
        "E12_FREEZE_STATISTICS_REGRESSION",
    ]
    assert all("proposal/evidence/authority/commit" in row["inclusion_rule"] for row in rows)
    assert all("faithful baseline" not in row["comparison_class"] for row in rows if row["comparison_class"] == "mechanism_ablation")
    assert all("ablation" not in row["comparison_class"] for row in rows if row["comparison_class"] == "faithful_baseline")
    assert all("RSI" not in " ".join(row.values()) for row in rows)


def test_submission_experiment_blueprint_records_review_acceptance_gates() -> None:
    rows = build_submission_experiment_blueprint(Path("/data/zhiqi/License"))["rows"]

    assert all(row["acceptance_gate"] for row in rows)
    assert "same backbone" in rows[0]["acceptance_gate"]
    assert "McNemar p < 0.05" in rows[0]["acceptance_gate"]
    assert "authorized-commit recall" in rows[0]["acceptance_gate"]
    assert "task-ID hand guard" in rows[9]["acceptance_gate"]
    assert "held-out" in rows[10]["acceptance_gate"]
    assert "all main-text numbers are generated" in rows[11]["acceptance_gate"]


def test_write_submission_experiment_blueprint_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_submission_experiment_blueprint(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "submission_experiment_blueprint.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["blueprint_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["blueprint_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 12
    assert rows[0]["blueprint_id"] == "E1_TAU2_AIRLINE_WRITE_AUTHORITY"
    assert rows[7]["comparison_class"] == "faithful_baseline"
    assert rows[9]["comparison_class"] == "mechanism_ablation"
    assert "McNemar p < 0.05" in rows[0]["acceptance_gate"]

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAExperimentBlueprintRows}{12}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintModelSlots}{5}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintRunCells}{1005}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintMainPositiveRunCells}{764}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintFaithfulBaselineBlocks}{2}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintMechanismAblationBlocks}{1}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["baseline_ablation_overlap"] == 0


def test_export_submission_experiment_blueprint_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "submission_experiment_blueprint.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_submission_experiment_blueprint.py",
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
    assert (tmp_path / "paper-data" / "submission_experiment_blueprint.csv").exists()
    assert (tmp_path / "sections" / "generated_experiment_blueprint_numbers.tex").exists()

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
    assert summary["blueprint_rows"] == 10
    assert summary["benchmark_families"] == 3
    assert summary["target_model_slots"] == 3
    assert summary["minimum_planned_run_cells"] == 826
    assert summary["main_positive_scale_run_cells"] == 666
    assert summary["faithful_baseline_blocks"] == 1
    assert summary["mechanism_ablation_blocks"] == 1
    assert summary["baseline_ablation_overlap"] == 0
    assert summary["current_clean_positive_passes"] == 30
    assert summary["current_clean_positive_trials"] == 30

    rows = blueprint["rows"]
    assert [row["blueprint_id"] for row in rows] == [
        "E1_CORE_RSI_GENERATION_CURVE",
        "E2_MATCHED_FORK_AT_BOUNDARY",
        "E3_ACTION_PAIR_GEOMETRY_60",
        "E4_GENERALIZED_VS_TASK_LOCAL_TRANSFER",
        "E5_REASONING_RSI_X_ACTION_RSI",
        "E6_SECOND_OPEN_MODEL_HELDOUT",
        "E7_STRONG_AGENT_SUBSET",
        "E8_MECHANISM_CUTS",
        "E9_ORACLE_BOUNDARY_UPPER_BOUND",
        "E10_FREEZE_STATISTICS_RELEASE",
    ]
    assert all("proposal-to-effect" in row["inclusion_rule"] for row in rows)
    assert "inherited" in rows[0]["comparison_class"]
    assert "reset" in rows[0]["acceptance_gate"]
    assert "same actor" in rows[1]["acceptance_gate"]
    assert "Boundary cannot solve the domain algorithm" in rows[1]["acceptance_gate"]
    assert "unique pair" in rows[2]["primary_metric"]
    assert "task-local" in rows[3]["comparison_class"]
    assert "memory" in rows[4]["comparison_class"]
    assert rows[8]["paper_role"] == "upper_bound_reliability"
    assert all("faithful baseline" not in row["comparison_class"] for row in rows if row["comparison_class"] == "mechanism_ablation")
    assert all("ablation" not in row["comparison_class"] for row in rows if row["comparison_class"] == "faithful_baseline")
    assert any("action-boundary" in " ".join(row.values()) for row in rows)


def test_submission_experiment_blueprint_records_review_acceptance_gates() -> None:
    rows = build_submission_experiment_blueprint(Path("/data/zhiqi/License"))["rows"]

    assert all(row["acceptance_gate"] for row in rows)
    assert "Inherited B5 beats reset and static" in rows[0]["acceptance_gate"]
    assert "no manual update edits after generation starts" in rows[0]["acceptance_gate"]
    assert "fork at ProposalOK" in rows[1]["acceptance_gate"]
    assert "macro-average by unique pair" in rows[2]["acceptance_gate"]
    assert "generalized update beats task-local" in rows[3]["acceptance_gate"]
    assert "Joint condition beats either single side" in rows[4]["acceptance_gate"]
    assert "held out until B5 is frozen" in rows[5]["acceptance_gate"]
    assert "faithful baseline" in rows[6]["acceptance_gate"]
    assert "mechanism cut" in rows[7]["acceptance_gate"]
    assert "upper-bound" in rows[8]["acceptance_gate"]
    assert "all main-text numbers are generated" in rows[9]["acceptance_gate"]


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
    assert len(rows) == 10
    assert rows[0]["blueprint_id"] == "E1_CORE_RSI_GENERATION_CURVE"
    assert rows[6]["comparison_class"] == "faithful_baseline"
    assert rows[7]["comparison_class"] == "mechanism_ablation"
    assert "Inherited B5 beats reset and static" in rows[0]["acceptance_gate"]

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAExperimentBlueprintRows}{10}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintModelSlots}{3}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintRunCells}{826}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintMainPositiveRunCells}{666}" in tex
    assert "\\newcommand{\\LTAExperimentBlueprintFaithfulBaselineBlocks}{1}" in tex
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

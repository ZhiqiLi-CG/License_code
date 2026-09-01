from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.headline_result_panel import build_headline_result_panel, write_headline_result_panel


def test_build_headline_result_panel_compresses_story_first_evidence() -> None:
    panel = build_headline_result_panel(Path("/data/zhiqi/License"))

    summary = panel["summary"]
    assert summary["headline_rows"] == 8
    assert summary["main_positive_rows"] == 5
    assert summary["faithful_counterpoint_rows"] == 1
    assert summary["supporting_positive_rows"] == 1
    assert summary["scale_path_rows"] == 0
    assert summary["runtime_reliability_rows"] == 1
    assert summary["benchmarks"] == 3
    assert summary["state_substrates"] == 3
    assert summary["actor_backbones"] == 5
    assert summary["main_matched_actor_backbones"] == 2
    assert summary["matched_actor_backbones_with_retention"] == 3
    assert summary["tau2_retention_complete_pairs"] == 15
    assert summary["tau2_retention_boundary_regressions"] == 0
    assert summary["clean_positive_passes"] == 30
    assert summary["clean_positive_trials"] == 30
    assert summary["faithful_baseline_passes"] == 8
    assert summary["faithful_baseline_trials"] == 30
    assert summary["model_loop_passes"] == 15
    assert summary["model_loop_trials"] == 15
    assert summary["tau2_matched_pairs"] == 80
    assert summary["tau2_matched_boundary_regressions"] == 0
    assert summary["tau2_read_correct_write_wrong_proxy"] == 20
    assert summary["commit_pair_accuracy"] == 1.0
    assert summary["unauthorized_commit_rate"] == 0.0
    assert summary["authorized_commit_recall"] == 1.0

    assert [row["panel_id"] for row in panel["rows"]] == [
        "H1_BREADTH",
        "H2_TAU2_MATCHED_BOUNDARY",
        "H8_MODEL_IN_LOOP_BRIDGE",
        "H3_COMMIT_PAIR_ACCURACY",
        "H9_TAU2_RETENTION_CONTROLS",
        "H4_FAITHFUL_BASELINE_COUNTERPOINT",
        "H5_TAU2_COMMIT_MINING",
        "H7_RUNTIME_RELIABILITY_SUPPORT",
    ]
    assert all(row["story_question"] for row in panel["rows"])
    assert all("RSI" not in " ".join(row.values()) for row in panel["rows"])
    rows = {row["panel_id"]: row for row in panel["rows"]}
    assert rows["H3_COMMIT_PAIR_ACCURACY"]["source_data"] == "commit_pair_metrics.csv | commit_pair_members.csv"
    assert rows["H2_TAU2_MATCHED_BOUNDARY"]["paper_role"] == "main_positive_evidence"
    assert "80 paired seeds" in rows["H2_TAU2_MATCHED_BOUNDARY"]["result_sentence"]
    assert "0 boundary regressions" in rows["H2_TAU2_MATCHED_BOUNDARY"]["result_sentence"]
    assert "2 primary matched actor models" in rows["H1_BREADTH"]["result_sentence"]
    assert "retention controls extend matched coverage to 3 actor models" in rows[
        "H1_BREADTH"
    ]["result_sentence"]
    assert "5 actor backbones" in rows["H1_BREADTH"]["result_sentence"]
    assert rows["H9_TAU2_RETENTION_CONTROLS"]["paper_role"] == "supporting_positive_evidence"
    assert "15 held-out tau2 airline retention pairs" in rows[
        "H9_TAU2_RETENTION_CONTROLS"
    ]["result_sentence"]
    assert rows["H7_RUNTIME_RELIABILITY_SUPPORT"]["paper_role"] == "runtime_reliability_evidence"
    assert "not counted as matched-agent evidence" in rows["H7_RUNTIME_RELIABILITY_SUPPORT"]["result_sentence"]
    assert rows["H8_MODEL_IN_LOOP_BRIDGE"]["paper_role"] == "main_positive_evidence"
    assert rows["H8_MODEL_IN_LOOP_BRIDGE"]["source_data"] == "model_in_loop_bridge.csv"
    assert "15/15 official passes" in rows["H8_MODEL_IN_LOOP_BRIDGE"]["result_sentence"]
    assert "Terminal-Bench log-summary" in rows["H8_MODEL_IN_LOOP_BRIDGE"]["result_sentence"]
    assert "two SkillFlow OCR tasks" in rows["H8_MODEL_IN_LOOP_BRIDGE"]["result_sentence"]
    assert "unauthorized commit rate" in rows["H3_COMMIT_PAIR_ACCURACY"]["result_sentence"]
    assert rows["H4_FAITHFUL_BASELINE_COUNTERPOINT"]["paper_role"] == "faithful_baseline_counterpoint"
    assert "not an ablation" in rows["H4_FAITHFUL_BASELINE_COUNTERPOINT"]["result_sentence"]


def test_write_headline_result_panel_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_headline_result_panel(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "headline_result_panel.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["panel_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["panel_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 8
    assert rows[0]["panel_id"] == "H1_BREADTH"
    assert rows[1]["panel_id"] == "H2_TAU2_MATCHED_BOUNDARY"
    assert rows[2]["panel_id"] == "H8_MODEL_IN_LOOP_BRIDGE"
    assert rows[7]["paper_role"] == "runtime_reliability_evidence"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAHeadlinePanelRows}{8}" in tex
    assert "\\newcommand{\\LTAHeadlineMainPositiveRows}{5}" in tex
    assert "\\newcommand{\\LTAHeadlineSupportingPositiveRows}{1}" in tex
    assert "\\newcommand{\\LTAHeadlineRuntimeReliabilityRows}{1}" in tex
    assert "\\newcommand{\\LTAHeadlineFaithfulBaselineTrials}{30}" in tex
    assert "\\newcommand{\\LTAHeadlineCleanPositivePasses}{30}" in tex
    assert "\\newcommand{\\LTAHeadlineModelLoopPasses}{15}" in tex
    assert "\\newcommand{\\LTAHeadlineModelLoopTrials}{15}" in tex
    assert "\\newcommand{\\LTAHeadlineTauTwoMatchedPairs}{80}" in tex
    assert "\\newcommand{\\LTAHeadlineTauTwoMatchedBoundaryRegressions}{0}" in tex
    assert "\\newcommand{\\LTAHeadlineTauTwoRCWW}{20}" in tex
    assert "\\newcommand{\\LTAHeadlineCommitPairAccuracy}{1.000}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["headline_rows"] == 8


def test_export_headline_result_panel_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "headline_result_panel.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_headline_result_panel.py",
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
    assert (tmp_path / "paper-data" / "headline_result_panel.csv").exists()
    assert (tmp_path / "sections" / "generated_headline_panel_numbers.tex").exists()

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
    assert summary["scale_path_rows"] == 1
    assert summary["runtime_reliability_rows"] == 1
    assert summary["benchmarks"] == 3
    assert summary["state_substrates"] == 3
    assert summary["actor_backbones"] == 4
    assert summary["clean_positive_passes"] == 25
    assert summary["clean_positive_trials"] == 25
    assert summary["faithful_baseline_passes"] == 1
    assert summary["faithful_baseline_trials"] == 13
    assert summary["tau2_read_correct_write_wrong_proxy"] == 19
    assert summary["submission_scale_rows"] == 24
    assert summary["commit_pair_accuracy"] == 1.0
    assert summary["unauthorized_commit_rate"] == 0.0
    assert summary["authorized_commit_recall"] == 1.0

    assert [row["panel_id"] for row in panel["rows"]] == [
        "H1_BREADTH",
        "H2_CLEAN_POSITIVE_MASS",
        "H8_MODEL_IN_LOOP_BRIDGE",
        "H3_COMMIT_PAIR_ACCURACY",
        "H4_FAITHFUL_BASELINE_COUNTERPOINT",
        "H5_TAU2_COMMIT_MINING",
        "H6_CONTRACT_REFINEMENT_TRANSFER",
        "H7_SUBMISSION_SCALE_PATH",
    ]
    assert all(row["story_question"] for row in panel["rows"])
    assert all("RSI" not in " ".join(row.values()) for row in panel["rows"])
    rows = {row["panel_id"]: row for row in panel["rows"]}
    assert rows["H3_COMMIT_PAIR_ACCURACY"]["source_data"] == "commit_pair_metrics.csv | commit_pair_members.csv"
    assert rows["H2_CLEAN_POSITIVE_MASS"]["paper_role"] == "runtime_reliability_evidence"
    assert rows["H8_MODEL_IN_LOOP_BRIDGE"]["paper_role"] == "main_positive_evidence"
    assert rows["H8_MODEL_IN_LOOP_BRIDGE"]["source_data"] == "model_in_loop_bridge.csv"
    assert "10/10 official passes" in rows["H8_MODEL_IN_LOOP_BRIDGE"]["result_sentence"]
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
    assert rows[1]["paper_role"] == "runtime_reliability_evidence"
    assert rows[2]["panel_id"] == "H8_MODEL_IN_LOOP_BRIDGE"
    assert rows[7]["paper_role"] == "scale_path"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAHeadlinePanelRows}{8}" in tex
    assert "\\newcommand{\\LTAHeadlineMainPositiveRows}{5}" in tex
    assert "\\newcommand{\\LTAHeadlineRuntimeReliabilityRows}{1}" in tex
    assert "\\newcommand{\\LTAHeadlineFaithfulBaselineTrials}{13}" in tex
    assert "\\newcommand{\\LTAHeadlineCleanPositivePasses}{25}" in tex
    assert "\\newcommand{\\LTAHeadlineModelLoopPasses}{10}" in tex
    assert "\\newcommand{\\LTAHeadlineModelLoopTrials}{10}" in tex
    assert "\\newcommand{\\LTAHeadlineTauTwoRCWW}{19}" in tex
    assert "\\newcommand{\\LTAHeadlineSubmissionScaleRows}{24}" in tex
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

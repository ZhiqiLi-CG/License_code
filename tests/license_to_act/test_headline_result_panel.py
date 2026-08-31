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
    assert summary["headline_rows"] == 6
    assert summary["main_positive_rows"] == 4
    assert summary["faithful_counterpoint_rows"] == 1
    assert summary["scale_path_rows"] == 1
    assert summary["benchmarks"] == 3
    assert summary["state_substrates"] == 3
    assert summary["actor_backbones"] == 4
    assert summary["clean_positive_passes"] == 25
    assert summary["clean_positive_trials"] == 25
    assert summary["faithful_baseline_passes"] == 0
    assert summary["faithful_baseline_trials"] == 5
    assert summary["tau2_read_correct_write_wrong_proxy"] == 19
    assert summary["submission_scale_rows"] == 7

    assert [row["panel_id"] for row in panel["rows"]] == [
        "H1_BREADTH",
        "H2_CLEAN_POSITIVE_MASS",
        "H3_FAITHFUL_BASELINE_COUNTERPOINT",
        "H4_TAU2_COMMIT_MINING",
        "H5_CONTRACT_REFINEMENT_TRANSFER",
        "H6_SUBMISSION_SCALE_PATH",
    ]
    assert all(row["story_question"] for row in panel["rows"])
    assert all("RSI" not in " ".join(row.values()) for row in panel["rows"])
    assert panel["rows"][2]["paper_role"] == "faithful_baseline_counterpoint"
    assert "not an ablation" in panel["rows"][2]["result_sentence"]


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
    assert len(rows) == 6
    assert rows[0]["panel_id"] == "H1_BREADTH"
    assert rows[1]["paper_role"] == "main_positive_evidence"
    assert rows[5]["paper_role"] == "scale_path"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAHeadlinePanelRows}{6}" in tex
    assert "\\newcommand{\\LTAHeadlineMainPositiveRows}{4}" in tex
    assert "\\newcommand{\\LTAHeadlineFaithfulBaselineTrials}{5}" in tex
    assert "\\newcommand{\\LTAHeadlineCleanPositivePasses}{25}" in tex
    assert "\\newcommand{\\LTAHeadlineTauTwoRCWW}{19}" in tex
    assert "\\newcommand{\\LTAHeadlineSubmissionScaleRows}{7}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["headline_rows"] == 6


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

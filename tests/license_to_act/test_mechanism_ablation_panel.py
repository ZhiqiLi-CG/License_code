from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.mechanism_ablation_panel import (
    build_mechanism_ablation_panel,
    write_mechanism_ablation_panel,
)


def test_build_mechanism_ablation_panel_separates_internal_cuts_from_baselines() -> None:
    panel = build_mechanism_ablation_panel(Path("/data/zhiqi/License"))

    summary = panel["summary"]
    assert summary["ablation_rows"] == 5
    assert summary["high_priority_rows"] == 3
    assert summary["baseline_overlap"] == 0
    assert summary["cut_passes"] == 0
    assert summary["cut_trials"] == 6
    assert summary["full_passes"] == 23
    assert summary["full_trials"] == 23

    rows = {row["ablation_id"]: row for row in panel["rows"]}
    assert list(rows) == [
        "ABLATE_COMMIT_READINESS",
        "ABLATE_WRITE_SCOPE_AND_PRESERVE",
        "ABLATE_PRESERVING_READ",
        "ABLATE_COMPLETION_TRIGGER",
            "PROMPT_ONLY_BOUNDARY_TEXT",
    ]
    assert rows["ABLATE_WRITE_SCOPE_AND_PRESERVE"]["high_priority"] == "yes"
    assert rows["ABLATE_COMPLETION_TRIGGER"]["high_priority"] == "yes"
    assert rows["PROMPT_ONLY_BOUNDARY_TEXT"]["high_priority"] == "yes"
    assert "baseline" not in rows["PROMPT_ONLY_BOUNDARY_TEXT"]["comparison_class"]
    assert rows["ABLATE_COMPLETION_TRIGGER"]["cut_evidence_cases"] == "SF-INV"
    assert rows["ABLATE_COMPLETION_TRIGGER"]["full_evidence_cases"] == "SF-INV-BP-K5 | SF-TRAVEL-BP-K5"
    assert rows["ABLATE_WRITE_SCOPE_AND_PRESERVE"]["paper_result"] == "0/1 cut pass versus 5/5 full boundary pass"
    assert all(row["comparison_class"] == "mechanism_ablation" for row in rows.values())


def test_write_mechanism_ablation_panel_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_mechanism_ablation_panel(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "mechanism_ablation_panel.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["panel_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["panel_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 5
    assert rows[0]["ablation_id"] == "ABLATE_COMMIT_READINESS"
    assert rows[-1]["ablation_id"] == "PROMPT_ONLY_BOUNDARY_TEXT"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAMechanismAblationPanelRows}{5}" in tex
    assert "\\newcommand{\\LTAMechanismAblationPriorityRows}{3}" in tex
    assert "\\newcommand{\\LTAMechanismAblationCutPasses}{0}" in tex
    assert "\\newcommand{\\LTAMechanismAblationCutTrials}{6}" in tex
    assert "\\newcommand{\\LTAMechanismAblationFullPasses}{23}" in tex
    assert "\\newcommand{\\LTAMechanismAblationFullTrials}{23}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["full_passes"] == 23


def test_export_mechanism_ablation_panel_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "mechanism_ablation_panel.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_mechanism_ablation_panel.py",
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
    assert (tmp_path / "paper-data" / "mechanism_ablation_panel.csv").exists()
    assert (tmp_path / "sections" / "generated_ablation_numbers.tex").exists()

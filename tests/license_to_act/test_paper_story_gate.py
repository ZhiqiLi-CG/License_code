from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.paper_story_gate import build_story_gate_report, write_story_gate_report


def test_build_story_gate_report_checks_top_conference_spine() -> None:
    report = build_story_gate_report(Path("/data/zhiqi/License"))

    summary = report["summary"]
    assert summary["total_checks"] == 11
    assert summary["passed_checks"] == 11
    assert summary["failed_checks"] == 0
    assert summary["clean_positive_passes"] == 25
    assert summary["clean_positive_trials"] == 25
    assert summary["faithful_baseline_passes"] == 0
    assert summary["faithful_baseline_trials"] == 5
    assert summary["benchmark_count"] == 3
    assert summary["state_substrate_count"] == 3
    assert summary["actor_backbone_count"] == 4

    checks = {check["check_id"]: check for check in report["checks"]}
    assert checks["portfolio_breadth"]["status"] == "pass"
    assert checks["clean_positive_mass"]["status"] == "pass"
    assert checks["faithful_baseline_not_ablation"]["status"] == "pass"
    assert checks["comparison_manifest_separates_roles"]["status"] == "pass"
    assert checks["license_workspace_only"]["status"] == "pass"
    assert checks["paper_imports_generated_numbers"]["status"] == "pass"
    assert "story gate" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert checks["story_language_anchors"]["status"] == "pass"
    assert checks["reproduction_chain_mentions_portfolio"]["status"] == "pass"
    assert "story gate" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert checks["appendix_serves_story"]["status"] == "pass"
    assert checks["appendix_uses_submission_scale_language"]["status"] == "pass"
    assert checks["code_paper_submodules_declared"]["status"] == "pass"

    assert "ablation" not in checks["faithful_baseline_not_ablation"]["evidence"].lower()
    assert "RSI" not in checks["license_workspace_only"]["evidence"]


def test_write_story_gate_report_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_story_gate_report(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "story_gate.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["checks_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["checks_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 11
    assert {row["status"] for row in rows} == {"pass"}

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAStoryGateChecks}{11}" in tex
    assert "\\newcommand{\\LTAStoryGatePassed}{11}" in tex
    assert "\\newcommand{\\LTAStoryGateFailed}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["failed_checks"] == 0


def test_export_story_gate_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "story_gate.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_story_gate.py",
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
    assert (tmp_path / "paper-data" / "story_gate_checks.csv").exists()
    assert (tmp_path / "sections" / "generated_story_gate_numbers.tex").exists()

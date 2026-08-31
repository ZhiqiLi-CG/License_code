from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.comparison_manifest import build_comparison_manifest, write_comparison_manifest


def test_build_comparison_manifest_separates_external_baselines_from_ablation_cuts() -> None:
    manifest = build_comparison_manifest(Path("/data/zhiqi/License"))

    summary = manifest["summary"]
    assert summary["method_condition_rows"] == 1
    assert summary["faithful_baseline_rows"] == 1
    assert summary["faithful_baseline_trials"] == 13
    assert summary["faithful_baseline_passes"] == 1
    assert summary["mechanism_ablation_rows"] == 5
    assert summary["completed_mechanism_ablation_rows"] == 5
    assert summary["integration_stress_rows"] == 1
    assert summary["baseline_ablation_overlap"] == 0

    rows = manifest["rows"]
    assert [row["comparison_id"] for row in rows] == [
        "M1_FULL_STATETX_CLEAN_ANCHORS",
        "B1_QWEN32K_MINISWE_MATCHED",
        "A1_PROMPT_ONLY_TEXT_CONTRACT",
        "A2_NO_COMPLETION_TRIGGER",
        "A3_NO_PRESERVE_CONSTRAINTS",
        "A4_NO_PRESERVING_READ_CONTRACT",
        "A5_NO_CONTRACT_REFINEMENT",
        "S1_QWEN_COMMIT_CONTROLLER_INTEGRATION",
    ]

    baseline = rows[1]
    assert baseline["comparison_class"] == "faithful_baseline"
    assert baseline["paper_role"] == "main_counterpoint"
    assert "ablation" not in " ".join(baseline.values()).lower()

    ablations = [row for row in rows if row["comparison_class"] == "mechanism_ablation"]
    assert len(ablations) == 5
    assert all("baseline" not in row["paper_role"] for row in ablations)
    assert {row["evidence_status"] for row in ablations} == {"seed_evidence"}

    integration = rows[-1]
    assert integration["comparison_class"] == "integration_stress"
    assert integration["current_result"] == "10/10 official passes"
    assert "two SkillFlow OCR tasks" in integration["tests"]
    assert integration["source_data"] == "model_in_loop_bridge.csv"
    assert "long32k" in integration["condition"]


def test_write_comparison_manifest_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_comparison_manifest(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "comparison_manifest.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["manifest_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["manifest_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 8
    assert rows[1]["comparison_class"] == "faithful_baseline"
    assert rows[2]["comparison_class"] == "mechanism_ablation"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAComparisonManifestRows}{8}" in tex
    assert "\\newcommand{\\LTAFaithfulBaselineRows}{1}" in tex
    assert "\\newcommand{\\LTAMechanismAblationRows}{5}" in tex
    assert "\\newcommand{\\LTACompletedMechanismAblationRows}{5}" in tex
    assert "\\newcommand{\\LTABaselineAblationOverlap}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["baseline_ablation_overlap"] == 0


def test_export_comparison_manifest_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "comparison_manifest.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_comparison_manifest.py",
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
    assert (tmp_path / "paper-data" / "comparison_manifest.csv").exists()
    assert (tmp_path / "sections" / "generated_comparison_numbers.tex").exists()

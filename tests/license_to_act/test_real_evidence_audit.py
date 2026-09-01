from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.real_evidence_audit import build_real_evidence_audit, write_real_evidence_audit


def test_real_evidence_audit_separates_real_results_from_scale_plans() -> None:
    audit = build_real_evidence_audit(Path("/data/zhiqi/License"))

    summary = audit["summary"]
    assert summary["real_harbor_rows"] >= 8
    assert summary["planned_rows"] >= 1
    assert summary["main_positive_planned_rows"] == 0
    assert summary["missing_artifact_rows"] == 0
    assert summary["unparseable_artifact_rows"] == 0

    rows = {row["evidence_id"]: row for row in audit["rows"]}
    assert "headline:H7_SUBMISSION_SCALE_PATH" not in rows
    assert rows["headline:H2_TAU2_MATCHED_BOUNDARY"]["evidence_kind"] == "derived_from_real_artifacts"
    assert rows["headline:H2_TAU2_MATCHED_BOUNDARY"]["counts_as_main_result"] == "yes"
    assert rows["headline:H7_RUNTIME_RELIABILITY_SUPPORT"]["evidence_kind"] == "derived_from_real_artifacts"
    assert rows["headline:H7_RUNTIME_RELIABILITY_SUPPORT"]["counts_as_main_result"] == "no"
    scale_target_rows = [row for row in audit["rows"] if row["evidence_id"].startswith("scale_plan:")]
    assert all(row["paper_role"] == "planned_scale_target" for row in scale_target_rows)
    assert all("target role:" in row["notes"] for row in scale_target_rows)
    assert rows["stage2:TB-WAL-K5"]["evidence_kind"] == "real_official_harbor"
    assert rows["stage2:TB-WAL-K5"]["counts_as_main_result"] == "no"
    assert rows["stage2:SF-INV-MAT-K5"]["counts_as_main_result"] == "no"
    assert rows["stage2:TB-QWEN32K-MSWE-K15"]["evidence_kind"] == "real_official_harbor"
    assert rows["stage2:TB-QWEN32K-MSWE-K15"]["counts_as_main_result"] == "yes"
    assert rows["stage2:SF-QWEN32K-MSWE-K10"]["evidence_kind"] == "real_official_harbor"
    assert rows["stage2:SF-QWEN32K-MSWE-K10"]["counts_as_main_result"] == "yes"
    assert rows["model_loop:SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["evidence_kind"] == "real_official_harbor"
    assert rows["model_loop:SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["counts_as_main_result"] == "yes"
    assert rows["model_loop:TB_WAL_MATERIALIZER_K5"]["counts_as_main_result"] == "no"
    assert rows["model_loop:SF_OCR_QWEN32K_MINISWE_BASELINE_K5"]["notes"] == "1/10 passes; mixed"


def test_write_real_evidence_audit_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_real_evidence_audit(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "real_evidence_audit.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["audit_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["audit_csv"]).open(newline="", encoding="utf-8")))
    assert any(row["evidence_kind"] == "real_official_harbor" for row in rows)
    assert any(row["evidence_kind"] == "planned_matrix" for row in rows)

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTARealEvidenceHarborRows}" in tex
    assert "\\newcommand{\\LTARealEvidenceMainPositivePlannedRows}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["main_positive_planned_rows"] == 0


def test_export_real_evidence_audit_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "real_evidence_audit.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_real_evidence_audit.py",
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
    assert (tmp_path / "paper-data" / "real_evidence_audit.csv").exists()
    assert (tmp_path / "sections" / "generated_real_evidence_numbers.tex").exists()

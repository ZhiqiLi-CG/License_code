from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.model_in_loop_bridge import (
    build_model_in_loop_bridge,
    write_model_in_loop_bridge,
)


def test_build_model_in_loop_bridge_separates_agent_evidence_from_materializers() -> None:
    bridge = build_model_in_loop_bridge(Path("/data/zhiqi/License"))

    summary = bridge["summary"]
    assert summary["model_in_loop_rows"] == 4
    assert summary["qwen_invoice_baseline_passes"] == 0
    assert summary["qwen_invoice_baseline_trials"] == 2
    assert summary["qwen_invoice_govkernel_passes"] == 4
    assert summary["qwen_invoice_govkernel_trials"] == 5
    assert summary["qwen_invoice_govkernel_errors"] == 1
    assert summary["qwen_invoice_pass_delta"] == 4
    assert summary["runtime_reliability_rows"] == 5
    assert summary["materializer_rows_used_as_matched_agent"] == 0

    rows = {row["bridge_id"]: row for row in bridge["rows"]}
    assert rows["SF_INVOICE_QWEN_TERMINUS_FULL"]["comparison_boundary"] == "ordinary_agent"
    assert rows["SF_INVOICE_QWEN_TERMINUS_PROMPT_ONLY"]["comparison_boundary"] == "prompt_only_control"
    assert rows["SF_INVOICE_QWEN_GOVKERNEL_K5"]["comparison_boundary"] == "model_in_loop_govkernel"
    assert rows["SF_INVOICE_QWEN32K_MINISWE_BASELINE"]["comparison_boundary"] == "faithful_baseline"
    assert rows["SF_TRAVEL_MATERIALIZER_K5"]["comparison_boundary"] == "runtime_reliability"
    assert rows["SF_INVOICE_QWEN_GOVKERNEL_K5"]["passes"] == "4"
    assert rows["SF_INVOICE_QWEN_GOVKERNEL_K5"]["pass_at_5"] == "1"
    assert rows["SF_INVOICE_QWEN_GOVKERNEL_K5"]["uses_task_specific_materializer"] == "no"
    assert all(
        row["comparison_boundary"] != "model_in_loop_govkernel"
        for row in rows.values()
        if row["uses_task_specific_materializer"] == "yes"
    )


def test_write_model_in_loop_bridge_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_model_in_loop_bridge(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "model_in_loop_bridge.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["bridge_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["bridge_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 10
    assert rows[0]["bridge_id"] == "SF_INVOICE_QWEN_TERMINUS_FULL"
    assert rows[3]["bridge_id"] == "SF_INVOICE_QWEN_GOVKERNEL_K5"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAModelLoopRows}{4}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceBaselinePasses}{0}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceBaselineTrials}{2}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceGovPasses}{4}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceGovTrials}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoicePassDelta}{4}" in tex
    assert "\\newcommand{\\LTAModelLoopMaterializerAsAgentRows}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["materializer_rows_used_as_matched_agent"] == 0


def test_export_model_in_loop_bridge_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "model_in_loop_bridge.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_model_in_loop_bridge.py",
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
    assert (tmp_path / "paper-data" / "model_in_loop_bridge.csv").exists()
    assert (tmp_path / "sections" / "generated_model_loop_numbers.tex").exists()

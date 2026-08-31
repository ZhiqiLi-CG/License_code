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
    assert summary["model_in_loop_rows"] == 6
    assert summary["qwen_invoice_baseline_passes"] == 0
    assert summary["qwen_invoice_baseline_trials"] == 1
    assert summary["qwen_invoice_govkernel_passes"] == 5
    assert summary["qwen_invoice_govkernel_trials"] == 5
    assert summary["qwen_invoice_govkernel_errors"] == 0
    assert summary["qwen_invoice_pass_delta"] == 5
    assert summary["qwen_travel_govkernel_passes"] == 5
    assert summary["qwen_travel_govkernel_trials"] == 5
    assert summary["qwen_travel_govkernel_errors"] == 0
    assert summary["qwen_skillflow_govkernel_passes"] == 10
    assert summary["qwen_skillflow_govkernel_trials"] == 10
    assert summary["qwen_skillflow_faithful_baseline_passes"] == 1
    assert summary["qwen_skillflow_faithful_baseline_trials"] == 10
    assert summary["qwen_terminal_log_faithful_baseline_passes"] == 4
    assert summary["qwen_terminal_log_faithful_baseline_trials"] == 5
    assert summary["qwen_terminal_log_govkernel_passes"] == 5
    assert summary["qwen_terminal_log_govkernel_trials"] == 5
    assert summary["qwen_terminal_log_govkernel_errors"] == 0
    assert summary["qwen_all_govkernel_passes"] == 15
    assert summary["qwen_all_govkernel_trials"] == 15
    assert summary["runtime_reliability_rows"] == 6
    assert summary["materializer_rows_used_as_matched_agent"] == 0

    rows = {row["bridge_id"]: row for row in bridge["rows"]}
    assert rows["SF_INVOICE_QWEN_TERMINUS_FULL"]["comparison_boundary"] == "ordinary_agent"
    assert rows["SF_INVOICE_QWEN_TERMINUS_PROMPT_ONLY"]["comparison_boundary"] == "prompt_only_control"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["comparison_boundary"] == "model_in_loop_commit_controller"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["comparison_boundary"] == "model_in_loop_commit_controller"
    assert rows["SF_OCR_QWEN32K_MINISWE_BASELINE_K5"]["comparison_boundary"] == "faithful_baseline"
    assert rows["SF_OCR_QWEN32K_MINISWE_BASELINE_K5"]["passes"] == "1"
    assert rows["SF_OCR_QWEN32K_MINISWE_BASELINE_K5"]["n_trials"] == "10"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["comparison_boundary"] == "faithful_baseline"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["passes"] == "4"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["n_trials"] == "5"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["official_verifier_result"] == "mixed"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["comparison_boundary"] == "model_in_loop_commit_controller"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["passes"] == "5"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["n_trials"] == "5"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["n_errors"] == "0"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["official_verifier_result"] == "pass"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["uses_task_specific_materializer"] == "no"
    assert rows["TB_LOG_MATERIALIZER_K5"]["comparison_boundary"] == "runtime_reliability"
    assert rows["TB_LOG_MATERIALIZER_K5"]["passes"] == "5"
    assert rows["TB_LOG_MATERIALIZER_K5"]["official_verifier_result"] == "pass"
    assert rows["SF_TRAVEL_MATERIALIZER_K5"]["comparison_boundary"] == "runtime_reliability"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["passes"] == "5"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["pass_at_5"] == "1"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["uses_task_specific_materializer"] == "no"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["passes"] == "5"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["pass_at_5"] == "1"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["uses_task_specific_materializer"] == "no"
    assert all(
        row["comparison_boundary"] != "model_in_loop_commit_controller"
        for row in rows.values()
        if row["uses_task_specific_materializer"] == "yes"
    )


def test_bridge_rows_name_actor_controller_boundary_and_official_result() -> None:
    bridge = build_model_in_loop_bridge(Path("/data/zhiqi/License"))

    for row in bridge["rows"]:
        assert row["actor_model"]
        assert row["controller_boundary"]
        assert row["official_verifier_result"] in {"pass", "fail", "mixed", "error"}

    rows = {row["bridge_id"]: row for row in bridge["rows"]}
    assert rows["SF_INVOICE_QWEN_TERMINUS_FULL"]["actor_model"] == "Qwen3.8-27B"
    assert rows["SF_INVOICE_QWEN_TERMINUS_FULL"]["controller_boundary"] == "none"
    assert rows["SF_INVOICE_QWEN_TERMINUS_FULL"]["official_verifier_result"] == "fail"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["actor_model"] == "Qwen3.8-27B-long32k"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["controller_boundary"] == "completion_trigger"
    assert rows["SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"]["official_verifier_result"] == "pass"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["actor_model"] == "Qwen3.8-27B-long32k"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["controller_boundary"] == "completion_trigger"
    assert rows["SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"]["official_verifier_result"] == "pass"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["actor_model"] == "Qwen3.8-27B-long32k"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["controller_boundary"] == "none"
    assert rows["TB_LOG_QWEN32K_MINISWE_BASELINE_K5"]["official_verifier_result"] == "mixed"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["actor_model"] == "Qwen3.8-27B-long32k"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["controller_boundary"] == "completion_trigger"
    assert rows["TB_LOG_QWEN_COMMIT_CONTROLLER_K5"]["official_verifier_result"] == "pass"
    assert rows["TB_WAL_MATERIALIZER_K5"]["actor_model"] == "none_runtime_only"
    assert rows["TB_WAL_MATERIALIZER_K5"]["controller_boundary"] == "runtime_transaction"
    assert rows["TB_WAL_MATERIALIZER_K5"]["official_verifier_result"] == "pass"

    summary = bridge["summary"]
    assert summary["ordinary_agent_rows"] == 1
    assert summary["prompt_control_rows"] == 1
    assert summary["matched_agent_controller_rows"] == 4
    assert summary["faithful_baseline_rows"] == 2


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
    assert len(rows) == 14
    assert rows[0]["bridge_id"] == "SF_INVOICE_QWEN_TERMINUS_FULL"
    assert rows[3]["bridge_id"] == "SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5"
    assert rows[4]["bridge_id"] == "SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5"
    assert rows[5]["bridge_id"] == "TB_LOG_QWEN32K_MINISWE_BASELINE_K5"
    assert rows[6]["bridge_id"] == "TB_LOG_QWEN_COMMIT_CONTROLLER_K5"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAModelLoopRows}{6}" in tex
    assert "\\newcommand{\\LTAModelLoopOrdinaryRows}{1}" in tex
    assert "\\newcommand{\\LTAModelLoopPromptControlRows}{1}" in tex
    assert "\\newcommand{\\LTAModelLoopMatchedControllerRows}{4}" in tex
    assert "\\newcommand{\\LTAModelLoopFaithfulBaselineRows}{2}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceBaselinePasses}{0}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceBaselineTrials}{1}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceGovPasses}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoiceGovTrials}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenInvoicePassDelta}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTravelGovPasses}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTravelGovTrials}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenSkillflowGovPasses}{10}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenSkillflowGovTrials}{10}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenSkillflowFaithfulBaselinePasses}{1}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenSkillflowFaithfulBaselineTrials}{10}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTBLogBaselinePasses}{4}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTBLogBaselineTrials}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTBLogGovPasses}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTBLogGovTrials}{5}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenTBLogGovErrors}{0}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenAllGovPasses}{15}" in tex
    assert "\\newcommand{\\LTAModelLoopQwenAllGovTrials}{15}" in tex
    assert "\\newcommand{\\LTAModelLoopMaterializerAsAgentRows}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["materializer_rows_used_as_matched_agent"] == 0
    assert set(rows[0]) >= {"actor_model", "controller_boundary", "official_verifier_result"}


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

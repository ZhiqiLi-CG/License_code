from __future__ import annotations

import csv
import json
from pathlib import Path

from license_to_act.evidence_portfolio import build_evidence_portfolio, write_evidence_portfolio


def test_build_evidence_portfolio_separates_story_roles() -> None:
    portfolio = build_evidence_portfolio(Path("/data/zhiqi/License"))

    summary = portfolio["summary"]
    assert summary["benchmark_count"] == 3
    assert summary["state_substrate_count"] == 3
    assert summary["actor_backbone_count"] == 5
    assert summary["main_matched_actor_backbone_count"] == 2
    assert summary["matched_actor_backbone_count_with_retention"] == 3
    assert summary["tau2_retention_complete_pairs"] == 15
    assert summary["tau2_retention_boundary_regressions"] == 0
    assert summary["main_matched_actor_backbones"] == [
        "Mistral-Small-3.2-24B",
        "Qwen3.8-27B-long32k",
    ]
    assert summary["actor_backbones"] == [
        "Codex GPT-5.5",
        "Gemma-4-31B-it",
        "Mistral-Small-3.2-24B",
        "Qwen3.8-27B",
        "Qwen3.8-27B-long32k",
    ]
    assert summary["stage1_failure_to_pass"] == 5
    assert summary["stage1_pass_to_failure"] == 0
    assert summary["clean_positive_trials"] == 30
    assert summary["clean_positive_passes"] == 30
    assert summary["faithful_baseline_trials"] == 30
    assert summary["faithful_baseline_passes"] == 8
    assert summary["tau2_read_correct_write_wrong_proxy"] == 20
    assert summary["tau2_matched_pairs"] == 100
    assert summary["tau2_matched_boundary_regressions"] == 0

    rows = portfolio["rows"]
    assert [row["portfolio_id"] for row in rows] == [
        "P0_TAU2_MATCHED_ACTION_BOUNDARY",
        "P1_STAGE1_TRANSFER",
        "P7_TAU2_RETENTION_CONTROLS",
        "P2_TAU2_MINING",
        "P3_TB_OFFICIAL_RERUNS",
        "P4_SKILLFLOW_OFFICIAL_RERUNS",
        "P5_LONGCTX_FAITHFUL_BASELINE",
        "P6_QWEN_COMMIT_CONTROLLER_BRIDGE",
    ]
    by_id = {row["portfolio_id"]: row for row in rows}
    assert by_id["P0_TAU2_MATCHED_ACTION_BOUNDARY"]["paper_use"] == "main_argument"
    assert "100 paired seeds" in by_id["P0_TAU2_MATCHED_ACTION_BOUNDARY"]["positive_result"]
    assert by_id["P1_STAGE1_TRANSFER"]["paper_use"] == "rsi_seed_support"
    assert by_id["P1_STAGE1_TRANSFER"]["comparison_kind"] == "seed_cross_substrate_casebook"
    assert "same proposal-to-effect failure class" in by_id["P1_STAGE1_TRANSFER"]["story_role"]
    assert by_id["P7_TAU2_RETENTION_CONTROLS"]["paper_use"] == "supporting_non_regression"
    assert by_id["P7_TAU2_RETENTION_CONTROLS"]["comparison_kind"] == "matched_actor_retention_control"
    assert "15 paired retention controls" in by_id["P7_TAU2_RETENTION_CONTROLS"]["positive_result"]
    assert by_id["P5_LONGCTX_FAITHFUL_BASELINE"]["comparison_kind"] == "faithful_baseline"
    assert by_id["P5_LONGCTX_FAITHFUL_BASELINE"]["paper_use"] == "main_counterpoint"
    assert "ablation" not in by_id["P5_LONGCTX_FAITHFUL_BASELINE"]["comparison_kind"]
    assert by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["positive_result"] == "15/15 official passes"
    assert by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["benchmarks"] == "Terminal-Bench 2.1 | SkillFlow"
    assert "boundary" in by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["story_role"]
    assert by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["source_data"] == "model_in_loop_bridge.csv"
    assert by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["comparison_kind"] == "matched_agent_commit_controller"
    assert by_id["P6_QWEN_COMMIT_CONTROLLER_BRIDGE"]["paper_use"] == "main_argument"
    assert by_id["P3_TB_OFFICIAL_RERUNS"]["paper_use"] == "supporting_reproduction"
    assert by_id["P4_SKILLFLOW_OFFICIAL_RERUNS"]["paper_use"] == "supporting_reproduction"


def test_write_evidence_portfolio_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_evidence_portfolio(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "portfolio.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["portfolio_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(
        csv.DictReader(Path(output["outputs"]["portfolio_csv"]).open(newline="", encoding="utf-8"))
    )
    assert len(rows) == 8
    assert rows[0]["portfolio_id"] == "P0_TAU2_MATCHED_ACTION_BOUNDARY"
    assert rows[6]["comparison_kind"] == "faithful_baseline"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAEvidenceBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTAEvidenceSubstrates}{3}" in tex
    assert "\\newcommand{\\LTAEvidenceBackbones}{5}" in tex
    assert "\\newcommand{\\LTAEvidenceMainMatchedBackbones}{2}" in tex
    assert "\\newcommand{\\LTAEvidenceMatchedBackbonesWithRetention}{3}" in tex
    assert "\\newcommand{\\LTAEvidenceTauTwoRetentionPairs}{15}" in tex
    assert "\\newcommand{\\LTAEvidenceTauTwoRetentionRegressions}{0}" in tex
    assert "\\newcommand{\\LTAEvidenceCleanPositivePasses}{30}" in tex
    assert "\\newcommand{\\LTAEvidenceFaithfulBaselinePasses}{8}" in tex
    assert "\\newcommand{\\LTAEvidenceFaithfulBaselineTrials}{30}" in tex
    assert json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))[
        "summary"
    ]["benchmark_count"] == 3

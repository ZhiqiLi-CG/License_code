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
    assert summary["actor_backbone_count"] == 4
    assert summary["actor_backbones"] == [
        "Codex GPT-5.5",
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
    assert summary["tau2_read_correct_write_wrong_proxy"] == 19

    rows = portfolio["rows"]
    assert [row["portfolio_id"] for row in rows] == [
        "P1_STAGE1_TRANSFER",
        "P2_TAU2_MINING",
        "P3_TB_OFFICIAL_RERUNS",
        "P4_SKILLFLOW_OFFICIAL_RERUNS",
        "P5_LONGCTX_FAITHFUL_BASELINE",
        "P6_QWEN_COMMIT_CONTROLLER_BRIDGE",
    ]
    assert rows[4]["comparison_kind"] == "faithful_baseline"
    assert rows[4]["paper_use"] == "main_counterpoint"
    assert "ablation" not in rows[4]["comparison_kind"]
    assert rows[5]["positive_result"] == "15/15 official passes"
    assert rows[5]["benchmarks"] == "Terminal-Bench 2.1 | SkillFlow"
    assert "boundary" in rows[5]["story_role"]
    assert rows[5]["source_data"] == "model_in_loop_bridge.csv"
    assert rows[5]["comparison_kind"] == "matched_agent_commit_controller"


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
    assert len(rows) == 6
    assert rows[0]["portfolio_id"] == "P1_STAGE1_TRANSFER"
    assert rows[4]["comparison_kind"] == "faithful_baseline"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAEvidenceBenchmarks}{3}" in tex
    assert "\\newcommand{\\LTAEvidenceSubstrates}{3}" in tex
    assert "\\newcommand{\\LTAEvidenceBackbones}{4}" in tex
    assert "\\newcommand{\\LTAEvidenceCleanPositivePasses}{30}" in tex
    assert "\\newcommand{\\LTAEvidenceFaithfulBaselinePasses}{8}" in tex
    assert "\\newcommand{\\LTAEvidenceFaithfulBaselineTrials}{30}" in tex
    assert json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))[
        "summary"
    ]["benchmark_count"] == 3

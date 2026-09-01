from __future__ import annotations

import csv
import json
from pathlib import Path

from license_to_act.story_claims import build_story_claims, write_story_claims


def test_build_story_claims_from_current_license_artifacts() -> None:
    claims = build_story_claims(Path("/data/zhiqi/License"))

    assert claims["thesis_slug"] == "action_boundary_rsi"
    metrics = claims["headline_metrics"]
    assert metrics["stage1_cases"] == 6
    assert metrics["stage1_failure_to_pass"] == 5
    assert metrics["stage1_preserved_positive"] == 1
    assert metrics["stage2_clean_anchor_count"] == 6
    assert metrics["stage2_clean_trials"] == 30
    assert metrics["stage2_terminal_clean_trials"] == 20
    assert metrics["stage2_skillflow_clean_trials"] == 10
    assert metrics["stage2_clean_errors"] == 0
    assert metrics["stage2_clean_mean_reward"] == 1.0
    assert metrics["faithful_baseline_trials"] == 30
    assert metrics["faithful_baseline_passes"] == 8
    assert metrics["faithful_baseline_errors"] == 1
    assert metrics["faithful_terminal_baseline_trials"] == 20
    assert metrics["faithful_terminal_baseline_passes"] == 7
    assert metrics["faithful_terminal_baseline_errors"] == 1
    assert metrics["faithful_skillflow_baseline_trials"] == 10
    assert metrics["faithful_skillflow_baseline_passes"] == 1
    assert metrics["faithful_skillflow_baseline_errors"] == 0
    assert round(metrics["faithful_baseline_mean_reward"], 3) == 0.267
    assert metrics["tau2_cancel_decisions"] == 80
    assert metrics["tau2_read_correct_write_wrong_proxy"] == 20
    assert metrics["tau2_result_files"] >= 64
    assert metrics["tau2_simulations"] >= 129
    assert metrics["tau2_infrastructure_error_simulations"] >= 39
    assert metrics["tau2_matched_pairs"] >= 80
    assert metrics["tau2_matched_domains"] >= 2
    assert metrics["tau2_matched_actor_models"] >= 2
    assert metrics["tau2_matched_boundary_regressions"] == 0

    assert set(claims["claims"]) == {
        "proposal_to_effect_gap_is_distinct_from_task_failure",
        "proposal_is_not_effect",
        "matched_action_boundary_closes_gap",
        "contracts_are_not_operation_blacklists",
        "completion_triggers_repair_missing_finalization",
        "runtime_reliability_is_supporting_evidence",
        "boundary_updates_are_seed_evidence",
    }
    for claim in claims["claims"].values():
        assert claim["positive_evidence"]
        assert claim["source_artifacts"]
        assert claim["paper_section"]


def test_write_story_claims_exports_json_csv_and_tex(tmp_path: Path) -> None:
    output = write_story_claims(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "story_claims.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["claims_csv"]).exists()
    assert Path(output["outputs"]["headline_metrics_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    with Path(output["outputs"]["claims_csv"]).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 7
    assert rows[0]["claim_id"] == "proposal_to_effect_gap_is_distinct_from_task_failure"

    metrics = {
        row["metric"]: row["value"]
        for row in csv.DictReader(
            Path(output["outputs"]["headline_metrics_csv"]).open(newline="", encoding="utf-8")
        )
    }
    assert metrics["stage2_clean_trials"] == "30"
    assert metrics["faithful_baseline_mean_reward"] == "0.266667"
    assert int(metrics["tau2_matched_pairs"]) >= 80
    assert int(metrics["tau2_matched_boundary_regressions"]) == 0

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    output_metrics = output["headline_metrics"]
    assert "\\newcommand{\\LTAStageTwoCleanTrials}{30}" in tex
    assert "\\newcommand{\\LTAStageTwoTBCleanTrials}{20}" in tex
    assert "\\newcommand{\\LTAStageTwoSFCleanTrials}{10}" in tex
    assert "\\newcommand{\\LTAFaithfulBaselinePasses}{8}" in tex
    assert "\\newcommand{\\LTAFaithfulBaselineErrors}{1}" in tex
    assert "\\newcommand{\\LTAFaithfulTBBaselinePasses}{7}" in tex
    assert "\\newcommand{\\LTAFaithfulTBBaselineErrors}{1}" in tex
    assert "\\newcommand{\\LTAFaithfulSFBaselinePasses}{1}" in tex
    assert "\\newcommand{\\LTAFaithfulSFBaselineErrors}{0}" in tex
    assert f"\\newcommand{{\\LTATauTwoResultFiles}}{{{output_metrics['tau2_result_files']}}}" in tex
    assert f"\\newcommand{{\\LTATauTwoSimulations}}{{{output_metrics['tau2_simulations']}}}" in tex
    assert (
        f"\\newcommand{{\\LTATauTwoInfraErrors}}{{{output_metrics['tau2_infrastructure_error_simulations']}}}"
        in tex
    )
    assert "\\newcommand{\\LTATauTwoRCWW}{20}" in tex
    assert f"\\newcommand{{\\LTAStoryTauTwoMatchedPairs}}{{{output_metrics['tau2_matched_pairs']}}}" in tex
    assert "\\newcommand{\\LTAStoryTauTwoMatchedBoundaryRegressions}{0}" in tex
    assert json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))[
        "headline_metrics"
    ]["stage2_clean_anchor_count"] == 6

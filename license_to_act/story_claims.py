from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .model_in_loop_bridge import build_model_in_loop_bridge


CLAIM_FIELDS = [
    "claim_id",
    "paper_section",
    "claim",
    "positive_evidence",
    "source_artifacts",
]

METRIC_FIELDS = ["metric", "value", "paper_role"]


def build_story_claims(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    stage1_summary = _read_json(root / "artifacts/paper_results/lta_stage2_paper_tables_20260830.json")
    stage2_summary = _read_json(root / "artifacts/stage2/lta_stage2_paper_results_20260830.json")
    stage2_rows = _read_csv(root / "License_paper/data/stage2_reliability.csv")
    tau2_rows = _read_csv(root / "License_paper/data/tau2_commit_mining.csv")
    model_bridge = build_model_in_loop_bridge(root)

    clean_rows = [row for row in stage2_rows if row["paper_use"] == "clean_reliability_anchor"]
    faithful_rows = [row for row in stage2_rows if row["paper_use"] == "faithful_baseline"]
    terminal_clean_rows = [row for row in clean_rows if row["benchmark"] == "Terminal-Bench 2.1"]
    skillflow_clean_rows = [row for row in clean_rows if row["benchmark"] == "SkillFlow"]
    terminal_faithful_rows = [row for row in faithful_rows if row["benchmark"] == "Terminal-Bench 2.1"]
    skillflow_faithful_rows = [row for row in faithful_rows if row["benchmark"] == "SkillFlow"]
    tau2_metrics = {row["metric"]: _parse_number(row["value"]) for row in tau2_rows}
    transfer = stage1_summary["transfer_ledger"]
    transfer_n = sum(int(row["n"]) for row in transfer)
    transfer_ftp = sum(int(row["failure_to_pass"]) for row in transfer)
    transfer_positive = sum(int(row["unchanged_positive"]) for row in transfer)
    transfer_ptf = sum(int(row["pass_to_failure"]) for row in transfer)

    headline_metrics = {
        "stage1_cases": int(stage1_summary["stage1_cases"]),
        "stage1_failure_to_pass": int(stage1_summary["failure_to_pass"]),
        "stage1_preserved_positive": int(stage1_summary["preserved_positive"]),
        "stage2_clean_anchor_count": len(clean_rows),
        "stage2_clean_trials": int(stage2_summary["clean_reliability_trials"]),
        "stage2_terminal_clean_anchor_count": len(terminal_clean_rows),
        "stage2_terminal_clean_trials": _sum_int(terminal_clean_rows, "n_trials"),
        "stage2_skillflow_clean_anchor_count": len(skillflow_clean_rows),
        "stage2_skillflow_clean_trials": _sum_int(skillflow_clean_rows, "n_trials"),
        "stage2_clean_errors": int(stage2_summary["clean_reliability_errors"]),
        "stage2_clean_mean_reward": float(stage2_summary["clean_reliability_mean_reward"]),
        "faithful_baseline_trials": int(stage2_summary["faithful_baseline_trials"]),
        "faithful_baseline_passes": _sum_passes(faithful_rows),
        "faithful_baseline_errors": int(stage2_summary["faithful_baseline_errors"]),
        "faithful_terminal_baseline_trials": _sum_int(terminal_faithful_rows, "n_trials"),
        "faithful_terminal_baseline_passes": _sum_passes(terminal_faithful_rows),
        "faithful_terminal_baseline_errors": _sum_int(terminal_faithful_rows, "n_errors"),
        "faithful_skillflow_baseline_trials": _sum_int(skillflow_faithful_rows, "n_trials"),
        "faithful_skillflow_baseline_passes": _sum_passes(skillflow_faithful_rows),
        "faithful_skillflow_baseline_errors": _sum_int(skillflow_faithful_rows, "n_errors"),
        "faithful_baseline_mean_reward": float(stage2_summary["faithful_baseline_mean_reward"]),
        "tau2_cancel_decisions": int(stage2_summary["tau2_cancel_decisions"]),
        "tau2_read_correct_write_wrong_proxy": int(stage2_summary["tau2_read_correct_write_wrong_proxy"]),
        "tau2_result_files": int(tau2_metrics["result_files"]),
        "tau2_simulations": int(tau2_metrics["simulations"]),
        "tau2_infrastructure_error_simulations": int(stage2_summary["tau2_infrastructure_error_simulations"]),
        "transfer_cases": transfer_n,
        "transfer_failure_to_pass": transfer_ftp,
        "transfer_preserved_positive": transfer_positive,
        "transfer_pass_to_failure": transfer_ptf,
        "qwen_skillflow_govkernel_passes": model_bridge["summary"]["qwen_skillflow_govkernel_passes"],
        "qwen_skillflow_govkernel_trials": model_bridge["summary"]["qwen_skillflow_govkernel_trials"],
        "qwen_skillflow_faithful_baseline_passes": model_bridge["summary"][
            "qwen_skillflow_faithful_baseline_passes"
        ],
        "qwen_skillflow_faithful_baseline_trials": model_bridge["summary"][
            "qwen_skillflow_faithful_baseline_trials"
        ],
    }

    return {
        "thesis_slug": "action_boundary_rsi",
        "title_line": "Beyond Better Reasoning: Recursive Self-Improvement at the Action Boundary",
        "central_sentence": (
            "A self-improving agent should learn not only better solutions, but better "
            "ways of turning those solutions into external effects."
        ),
        "headline_metrics": headline_metrics,
        "claims": _claims(headline_metrics, clean_rows, faithful_rows),
        "source_policy": (
            "Story claims use License workspace artifacts only. Faithful baselines and "
            "action-boundary mechanism cuts are kept as different evidence categories."
        ),
    }


def _claims(
    metrics: dict[str, Any],
    clean_rows: list[dict[str, str]],
    faithful_rows: list[dict[str, str]],
) -> dict[str, dict[str, Any]]:
    clean_tasks = ", ".join(row["case_id"] for row in clean_rows)
    baseline_tasks = ", ".join(row["case_id"] for row in faithful_rows)
    return {
        "proposal_to_effect_gap_is_distinct_from_task_failure": {
            "paper_section": "Introduction",
            "claim": (
                "State-changing agents can reach the right intermediate proposal while the final "
                "external effect remains wrong or absent."
            ),
            "positive_evidence": [
                f"{metrics['stage1_cases']} audited Stage-1 cases across tau2, Terminal-Bench, and SkillFlow",
                f"{metrics['tau2_read_correct_write_wrong_proxy']} tau2 read-correct/write-wrong proxy cases",
            ],
            "source_artifacts": [
                "artifacts/paper_results/lta_stage2_paper_tables_20260830.json",
                "artifacts/stage2/tau2_commit_mining_20260830.json",
            ],
        },
        "proposal_is_not_effect": {
            "paper_section": "tau2 Results",
            "claim": (
                "User intent, task phrasing, and model confidence can motivate a business write, "
                "but policy/source-state evidence must make the proposed effect ready before commit."
            ),
            "positive_evidence": [
                f"{metrics['tau2_cancel_decisions']} tau2 cancel decisions mined",
                f"{metrics['tau2_read_correct_write_wrong_proxy']} policy-invalid cancel commits had matched reservation reads",
            ],
            "source_artifacts": [
                "License_paper/data/tau2_commit_mining.csv",
                "License_paper/data/tau2_commit_by_group.csv",
            ],
        },
        "contracts_are_not_operation_blacklists": {
            "paper_section": "Results",
            "claim": (
                "The method blocks unready or overbroad commits while preserving positive controls; "
                "the boundary rule is specific to readiness, write scope, preservation, and done state."
            ),
            "positive_evidence": [
                f"{metrics['stage1_preserved_positive']} Stage-1 legal tau2 commit remains pass-to-pass",
                "Diagnostic positive controls distinguish legitimate Git cleanup from overbroad history rewrite",
            ],
            "source_artifacts": [
                "License_paper/data/stage1_cases.csv",
                "License_paper/data/diagnostic_cases.csv",
            ],
        },
        "boundary_stabilizes_external_effects": {
            "paper_section": "Stage-2 Reliability",
            "claim": (
                "Executable boundary protocols are stable under official reruns, not just one-off scripts."
            ),
            "positive_evidence": [
                f"{metrics['stage2_clean_anchor_count']} reliability tasks: {clean_tasks}",
                f"{metrics['stage2_clean_trials']} reliability trials, {metrics['stage2_clean_errors']} errors, mean reward {metrics['stage2_clean_mean_reward']:.1f}",
                (
                    f"Matched faithful baseline rows: {baseline_tasks}; "
                    f"{metrics['faithful_baseline_passes']}/{metrics['faithful_baseline_trials']} passes, "
                    f"{metrics['faithful_baseline_errors']} errors, mean reward {metrics['faithful_baseline_mean_reward']:.2f}"
                ),
            ],
            "source_artifacts": [
                "License_paper/data/stage2_reliability.csv",
                "artifacts/stage2/lta_stage2_paper_results_20260830.json",
            ],
        },
        "completion_triggers_repair_missing_finalization": {
            "paper_section": "SkillFlow Results",
            "claim": (
                "The boundary is not only a veto: complete evidence can trigger a missing verifier-visible artifact."
            ),
            "positive_evidence": [
                (
                    "Qwen3.8-27B-long32k plus action boundary reaches "
                    f"{metrics['qwen_skillflow_govkernel_passes']}/"
                    f"{metrics['qwen_skillflow_govkernel_trials']} official passes "
                    "on invoice and travel-claim OCR anchors"
                ),
                (
                    "Qwen3.8-27B-long32k mini-swe baseline scores "
                    f"{metrics['qwen_skillflow_faithful_baseline_passes']}/"
                    f"{metrics['qwen_skillflow_faithful_baseline_trials']} "
                    "on the same SkillFlow anchors"
                ),
                "Runtime completion-trigger reruns score 10/10 on the same two anchor tasks",
            ],
            "source_artifacts": [
                "License_paper/data/stage2_reliability.csv",
                "License_paper/data/model_in_loop_bridge.csv",
            ],
        },
        "boundary_updates_transfer_across_state_substrates": {
            "paper_section": "Boundary Update Transfer",
            "claim": (
                "A failure-derived boundary update transfers across business tools, terminal state, "
                "and workflow artifacts."
            ),
            "positive_evidence": [
                f"{metrics['transfer_failure_to_pass']} failure-to-pass cases across {metrics['transfer_cases']} transfer ledger cases",
                f"{metrics['transfer_preserved_positive']} preserved positive, {metrics['transfer_pass_to_failure']} pass-to-failure cases",
            ],
            "source_artifacts": [
                "artifacts/amendment_transfer/lta_stage1_transfer_ledger_20260830.json",
                "License_paper/data/transfer_ledger.csv",
            ],
        },
    }


def write_story_claims(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper/data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper/sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts/paper_results/lta_story_claims_20260831.json"
    )
    claims = build_story_claims(root)

    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    claims_csv = paper_data_dir / "story_claims.csv"
    metrics_csv = paper_data_dir / "story_headline_metrics.csv"
    latex_numbers = paper_sections_dir / "generated_story_numbers.tex"

    _write_claims_csv(claims_csv, claims["claims"])
    _write_metrics_csv(metrics_csv, claims["headline_metrics"])
    latex_numbers.write_text(_latex_numbers(claims["headline_metrics"]), encoding="utf-8")

    claims["outputs"] = {
        "summary_json": str(summary_path),
        "claims_csv": str(claims_csv),
        "headline_metrics_csv": str(metrics_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(claims, indent=2), encoding="utf-8")
    return claims


def _write_claims_csv(path: Path, claims: dict[str, dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CLAIM_FIELDS, lineterminator="\n")
        writer.writeheader()
        for claim_id, claim in claims.items():
            writer.writerow(
                {
                    "claim_id": claim_id,
                    "paper_section": claim["paper_section"],
                    "claim": claim["claim"],
                    "positive_evidence": " | ".join(claim["positive_evidence"]),
                    "source_artifacts": " | ".join(claim["source_artifacts"]),
                }
            )


def _write_metrics_csv(path: Path, metrics: dict[str, Any]) -> None:
    roles = {
        "stage2_clean_trials": "Main reliability numerator/denominator",
        "faithful_baseline_trials": "Matched long-context baseline denominator",
        "tau2_read_correct_write_wrong_proxy": "Commit-failure mining headline",
    }
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS, lineterminator="\n")
        writer.writeheader()
        for metric, value in metrics.items():
            writer.writerow(
                {
                    "metric": metric,
                    "value": _format_value(value),
                    "paper_role": roles.get(metric, "Story support metric"),
                }
            )


def _latex_numbers(metrics: dict[str, Any]) -> str:
    commands = {
        "LTAStageOneCases": metrics["stage1_cases"],
        "LTAStageOneFtoP": metrics["stage1_failure_to_pass"],
        "LTAStageOnePositive": metrics["stage1_preserved_positive"],
        "LTAStageTwoCleanAnchors": metrics["stage2_clean_anchor_count"],
        "LTAStageTwoCleanTrials": metrics["stage2_clean_trials"],
        "LTAStageTwoTBCleanAnchors": metrics["stage2_terminal_clean_anchor_count"],
        "LTAStageTwoTBCleanTrials": metrics["stage2_terminal_clean_trials"],
        "LTAStageTwoSFCleanAnchors": metrics["stage2_skillflow_clean_anchor_count"],
        "LTAStageTwoSFCleanTrials": metrics["stage2_skillflow_clean_trials"],
        "LTAStageTwoCleanErrors": metrics["stage2_clean_errors"],
        "LTAFaithfulBaselineTrials": metrics["faithful_baseline_trials"],
        "LTAFaithfulBaselinePasses": metrics["faithful_baseline_passes"],
        "LTAFaithfulBaselineErrors": metrics["faithful_baseline_errors"],
        "LTAFaithfulTBBaselineTrials": metrics["faithful_terminal_baseline_trials"],
        "LTAFaithfulTBBaselinePasses": metrics["faithful_terminal_baseline_passes"],
        "LTAFaithfulTBBaselineErrors": metrics["faithful_terminal_baseline_errors"],
        "LTAFaithfulSFBaselineTrials": metrics["faithful_skillflow_baseline_trials"],
        "LTAFaithfulSFBaselinePasses": metrics["faithful_skillflow_baseline_passes"],
        "LTAFaithfulSFBaselineErrors": metrics["faithful_skillflow_baseline_errors"],
        "LTATauTwoCancelDecisions": metrics["tau2_cancel_decisions"],
        "LTATauTwoResultFiles": metrics["tau2_result_files"],
        "LTATauTwoSimulations": metrics["tau2_simulations"],
        "LTATauTwoInfraErrors": metrics["tau2_infrastructure_error_simulations"],
        "LTATauTwoRCWW": metrics["tau2_read_correct_write_wrong_proxy"],
        "LTATransferFtoP": metrics["transfer_failure_to_pass"],
        "LTATransferPtoF": metrics["transfer_pass_to_failure"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/story_claims.py.",
        "% Regenerate with License_code/scripts/export_story_claims.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{_format_value(value)}}}")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _preferred_existing(primary: Path, fallback: Path) -> Path:
    return primary if primary.exists() else fallback


def _parse_number(value: str) -> int | float | str:
    try:
        numeric = float(value)
    except ValueError:
        return value
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _sum_int(rows: list[dict[str, str]], field: str) -> int:
    return sum(int(row[field]) for row in rows)


def _sum_passes(rows: list[dict[str, str]]) -> int:
    return sum(round(float(row["mean_reward"]) * int(row["n_trials"])) for row in rows)


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.1f}" if value in {0.0, 1.0} else f"{value:g}"
    return str(value)

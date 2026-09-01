from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .commit_pair_metrics import compute_commit_pair_metrics, build_commit_pair_member_rows
from .evidence_portfolio import build_evidence_portfolio
from .model_in_loop_bridge import build_model_in_loop_bridge
from .story_claims import build_story_claims
from .tau2_matched_boundary_export import build_tau2_matched_boundary_export


PANEL_FIELDS = [
    "panel_id",
    "paper_role",
    "story_question",
    "result_sentence",
    "why_it_matters",
    "source_data",
]


def build_headline_result_panel(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    """Build the compact result panel the paper should lead with."""

    root = Path(project_root)
    claims = build_story_claims(root)
    portfolio = build_evidence_portfolio(root)
    comparison = build_comparison_manifest(root)
    commit_pairs = compute_commit_pair_metrics(build_commit_pair_member_rows(root))
    model_bridge = build_model_in_loop_bridge(root)
    tau2_matched = build_tau2_matched_boundary_export(root)

    metrics = claims["headline_metrics"]
    portfolio_summary = portfolio["summary"]
    comparison_summary = comparison["summary"]
    pair_summary = commit_pairs["summary"]
    bridge_summary = model_bridge["summary"]
    tau2_matched_summary = tau2_matched["summary"]

    rows = [
        {
            "panel_id": "H1_BREADTH",
            "paper_role": "main_positive_evidence",
            "story_question": "Does the proposal-to-effect gap span more than one state substrate?",
            "result_sentence": (
                f"The current result set spans {portfolio_summary['benchmark_count']} benchmark families, "
                f"{portfolio_summary['state_substrate_count']} state substrates, and "
                f"{portfolio_summary['main_matched_actor_backbone_count']} primary matched actor models; "
                f"tau2 retention controls extend matched coverage to "
                f"{portfolio_summary['matched_actor_backbone_count_with_retention']} actor models, and "
                f"broader diagnostic and counterpoint evidence touches "
                f"{portfolio_summary['actor_backbone_count']} actor backbones."
            ),
            "why_it_matters": (
                "The same gap between internal progress and external effect appears in business records, "
                "terminal state, and workflow artifacts."
            ),
            "source_data": "evidence_portfolio.csv",
        },
        {
            "panel_id": "H2_TAU2_MATCHED_BOUNDARY",
            "paper_role": "main_positive_evidence",
            "story_question": "Does changing only the action boundary close real business-state gaps?",
            "result_sentence": (
                f"Five live tau2 matched blocks change only the boundary and cover "
                f"{tau2_matched_summary['complete_pairs']} paired seeds across "
                f"{tau2_matched_summary['domains']} domains and "
                f"{tau2_matched_summary['actor_models']} actor models; mean reward moves from "
                f"{tau2_matched_summary['baseline_mean_reward']:.1f} to "
                f"{tau2_matched_summary['boundary_mean_reward']:.1f} with "
                f"{tau2_matched_summary['boundary_regressions']} boundary regressions."
            ),
            "why_it_matters": (
                "This is the cleanest current causal evidence: same model, task, user condition, and budget; "
                "only the proposal-to-effect interface changes."
            ),
            "source_data": "tau2_matched_boundary.csv",
        },
        {
            "panel_id": "H8_MODEL_IN_LOOP_BRIDGE",
            "paper_role": "main_positive_evidence",
            "story_question": "Does the action boundary help when the same model stays in the official trial?",
            "result_sentence": (
                f"Qwen3.8-27B-long32k plus action boundary reaches "
                f"{bridge_summary['qwen_all_govkernel_passes']}/"
                f"{bridge_summary['qwen_all_govkernel_trials']} official passes on Terminal-Bench log-summary "
                "and two SkillFlow OCR tasks with zero errors. The same faithful mini-swe actor without "
                f"the boundary reaches {bridge_summary['qwen_terminal_log_faithful_baseline_passes']}/"
                f"{bridge_summary['qwen_terminal_log_faithful_baseline_trials']} on log-summary and "
                f"{bridge_summary['qwen_skillflow_faithful_baseline_passes']}/"
                f"{bridge_summary['qwen_skillflow_faithful_baseline_trials']} on the OCR tasks."
            ),
            "why_it_matters": (
                "This is the current matched-agent evidence: the actor remains Qwen, while the action "
                "boundary controls finalization."
            ),
            "source_data": "model_in_loop_bridge.csv",
        },
        {
            "panel_id": "H3_COMMIT_PAIR_ACCURACY",
            "paper_role": "main_positive_evidence",
            "story_question": "Does the boundary distinguish ready effects from premature effects?",
            "result_sentence": (
                f"Across {pair_summary['pair_count']} current commit-pair groups, the boundary reaches "
                f"{pair_summary['commit_pair_accuracy']:.3f} pair accuracy, "
                f"{pair_summary['unauthorized_commit_rate']:.3f} unauthorized commit rate, and "
                f"{pair_summary['authorized_commit_recall']:.3f} authorized commit recall."
            ),
            "why_it_matters": (
                "The mechanism metric tests both sides of the action story: block premature effects "
                "and still commit when the evidence is ready."
            ),
            "source_data": "commit_pair_metrics.csv | commit_pair_members.csv",
        },
        {
            "panel_id": "H9_TAU2_RETENTION_CONTROLS",
            "paper_role": "supporting_positive_evidence",
            "story_question": "Does the boundary preserve already-correct business actions?",
            "result_sentence": (
                f"On {portfolio_summary['tau2_retention_complete_pairs']} held-out tau2 airline "
                f"retention pairs across Gemma-4-31B-it and Mistral-Small-3.2-24B, baseline "
                f"and boundary both reach reward 1.0 with "
                f"{portfolio_summary['tau2_retention_boundary_regressions']} regressions."
            ),
            "why_it_matters": (
                "The action boundary is not only a blocker; it preserves prepared effects when "
                "ordinary execution is already correct."
            ),
            "source_data": "tau2_matched_boundary.csv",
        },
        {
            "panel_id": "H4_FAITHFUL_BASELINE_COUNTERPOINT",
            "paper_role": "faithful_baseline_counterpoint",
            "story_question": "Does a stronger ordinary task agent solve the same proposal-to-effect boundary?",
            "result_sentence": (
                f"A matched Qwen3.8-27B-long32k mini-swe-agent baseline scores "
                f"{comparison_summary['faithful_baseline_passes']}/"
                f"{comparison_summary['faithful_baseline_trials']} official passes; "
                "this is a faithful baseline, not an ablation."
            ),
            "why_it_matters": (
                "The counterpoint attacks the claim directly while keeping external baselines separate "
                "from mechanism cuts."
            ),
            "source_data": "comparison_manifest.csv | stage2_reliability.csv",
        },
        {
            "panel_id": "H5_TAU2_COMMIT_MINING",
            "paper_role": "main_positive_evidence",
            "story_question": "Is the proposal-to-effect gap visible beyond hand-picked examples?",
            "result_sentence": (
                f"Mining {metrics['tau2_result_files']} local tau2 result files finds "
                f"{metrics['tau2_read_correct_write_wrong_proxy']} cancellation commits where the "
                "reservation read was matched but the policy-invalid write failed database or total reward."
            ),
            "why_it_matters": (
                "The result supports the core intuition: reasoning had evidence, but the final effect "
                "was not controlled."
            ),
            "source_data": "tau2_commit_mining.csv",
        },
        {
            "panel_id": "H7_RUNTIME_RELIABILITY_SUPPORT",
            "paper_role": "runtime_reliability_evidence",
            "story_question": "Do the executable boundary programs reproduce under official verifiers?",
            "result_sentence": (
                f"Reference-boundary programs achieve {portfolio_summary['clean_positive_passes']}/"
                f"{portfolio_summary['clean_positive_trials']} official passes with zero errors; these "
                "rows are implementation reliability checks, not counted as matched-agent evidence."
            ),
            "why_it_matters": (
                "This keeps reference-boundary checks out of the main causal comparison while "
                "still documenting that the released code reproduces the reported verifier states."
            ),
            "source_data": "stage2_reliability.csv | evidence_portfolio.csv",
        },
    ]

    summary = {
        "headline_rows": len(rows),
        "main_positive_rows": sum(1 for row in rows if row["paper_role"] == "main_positive_evidence"),
        "supporting_positive_rows": sum(
            1 for row in rows if row["paper_role"] == "supporting_positive_evidence"
        ),
        "runtime_reliability_rows": sum(
            1 for row in rows if row["paper_role"] == "runtime_reliability_evidence"
        ),
        "faithful_counterpoint_rows": sum(
            1 for row in rows if row["paper_role"] == "faithful_baseline_counterpoint"
        ),
        "scale_path_rows": sum(1 for row in rows if row["paper_role"] == "scale_path"),
        "benchmarks": portfolio_summary["benchmark_count"],
        "state_substrates": portfolio_summary["state_substrate_count"],
        "actor_backbones": portfolio_summary["actor_backbone_count"],
        "main_matched_actor_backbones": portfolio_summary["main_matched_actor_backbone_count"],
        "matched_actor_backbones_with_retention": portfolio_summary[
            "matched_actor_backbone_count_with_retention"
        ],
        "tau2_retention_complete_pairs": portfolio_summary["tau2_retention_complete_pairs"],
        "tau2_retention_boundary_regressions": portfolio_summary[
            "tau2_retention_boundary_regressions"
        ],
        "clean_positive_passes": portfolio_summary["clean_positive_passes"],
        "clean_positive_trials": portfolio_summary["clean_positive_trials"],
        "faithful_baseline_passes": comparison_summary["faithful_baseline_passes"],
        "faithful_baseline_trials": comparison_summary["faithful_baseline_trials"],
        "model_loop_passes": bridge_summary["qwen_all_govkernel_passes"],
        "model_loop_trials": bridge_summary["qwen_all_govkernel_trials"],
        "tau2_matched_pairs": tau2_matched_summary["complete_pairs"],
        "tau2_matched_boundary_regressions": tau2_matched_summary["boundary_regressions"],
        "tau2_read_correct_write_wrong_proxy": metrics["tau2_read_correct_write_wrong_proxy"],
        "commit_pair_accuracy": pair_summary["commit_pair_accuracy"],
        "unauthorized_commit_rate": pair_summary["unauthorized_commit_rate"],
        "authorized_commit_recall": pair_summary["authorized_commit_recall"],
    }
    return {"summary": summary, "rows": rows}


def write_headline_result_panel(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "lta_headline_result_panel_20260831.json"
    )

    panel = build_headline_result_panel(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    panel_csv = paper_data_dir / "headline_result_panel.csv"
    latex_numbers = paper_sections_dir / "generated_headline_panel_numbers.tex"
    _write_panel_csv(panel_csv, panel["rows"])
    latex_numbers.write_text(_latex_numbers(panel["summary"]), encoding="utf-8")

    panel["outputs"] = {
        "summary_json": str(summary_path),
        "panel_csv": str(panel_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(panel, indent=2), encoding="utf-8")
    return panel


def _write_panel_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PANEL_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAHeadlinePanelRows": summary["headline_rows"],
        "LTAHeadlineMainPositiveRows": summary["main_positive_rows"],
        "LTAHeadlineSupportingPositiveRows": summary["supporting_positive_rows"],
        "LTAHeadlineRuntimeReliabilityRows": summary["runtime_reliability_rows"],
        "LTAHeadlineFaithfulCounterpointRows": summary["faithful_counterpoint_rows"],
        "LTAHeadlineScalePathRows": summary["scale_path_rows"],
        "LTAHeadlineCleanPositivePasses": summary["clean_positive_passes"],
        "LTAHeadlineCleanPositiveTrials": summary["clean_positive_trials"],
        "LTAHeadlineFaithfulBaselinePasses": summary["faithful_baseline_passes"],
        "LTAHeadlineFaithfulBaselineTrials": summary["faithful_baseline_trials"],
        "LTAHeadlineModelLoopPasses": summary["model_loop_passes"],
        "LTAHeadlineModelLoopTrials": summary["model_loop_trials"],
        "LTAHeadlineTauTwoMatchedPairs": summary["tau2_matched_pairs"],
        "LTAHeadlineTauTwoMatchedBoundaryRegressions": summary[
            "tau2_matched_boundary_regressions"
        ],
        "LTAHeadlineTauTwoRCWW": summary["tau2_read_correct_write_wrong_proxy"],
        "LTAHeadlineCommitPairAccuracy": f"{summary['commit_pair_accuracy']:.3f}",
        "LTAHeadlineUnauthorizedCommitRate": f"{summary['unauthorized_commit_rate']:.3f}",
        "LTAHeadlineAuthorizedCommitRecall": f"{summary['authorized_commit_recall']:.3f}",
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/headline_result_panel.py.",
        "% Regenerate with License_code/scripts/export_headline_result_panel.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

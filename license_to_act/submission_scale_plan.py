from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .paper_story_gate import build_story_gate_report
from .story_claims import build_story_claims


SCALE_PLAN_FIELDS = [
    "target_id",
    "benchmark",
    "task_type",
    "model_family",
    "condition_role",
    "target_n",
    "paper_use",
    "story_axis",
    "current_positive_evidence",
    "scale_target",
    "inclusion_rule",
    "next_run",
]

TARGET_MODEL_SLOTS = [
    "Qwen3.8-27B-long32k",
    "Mistral/Gemma held-out open model",
    "Codex/Claude strong terminal agent",
]


def build_submission_scale_plan(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    claims = build_story_claims(root)
    comparison = build_comparison_manifest(root)
    story_gate = build_story_gate_report(root)
    metrics = claims["headline_metrics"]
    comparison_summary = comparison["summary"]
    inclusion_rule = "Include proposal-to-effect tasks with frozen intermediate and final verifiers."

    rows = _closed_loop_rows(metrics, comparison_summary, story_gate["summary"], inclusion_rule)
    summary = _summarize(rows, metrics, comparison_summary, story_gate["summary"])
    return {"summary": summary, "rows": rows}


def write_submission_scale_plan(
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
        else root / "artifacts" / "paper_results" / "lta_submission_scale_plan_20260831.json"
    )

    plan = build_submission_scale_plan(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    scale_plan_csv = paper_data_dir / "submission_scale_plan.csv"
    latex_numbers = paper_sections_dir / "generated_scale_plan_numbers.tex"
    _write_scale_plan_csv(scale_plan_csv, plan["rows"])
    latex_numbers.write_text(_latex_numbers(plan["summary"]), encoding="utf-8")

    plan["outputs"] = {
        "summary_json": str(summary_path),
        "scale_plan_csv": str(scale_plan_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return plan


def _closed_loop_rows(
    metrics: dict[str, Any],
    comparison_summary: dict[str, Any],
    story_summary: dict[str, Any],
    inclusion_rule: str,
) -> list[dict[str, str]]:
    current_tau2 = (
        f"{metrics['tau2_matched_pairs']} matched tau2 pairs; reward "
        f"{metrics['tau2_matched_baseline_mean_reward']:.2f}->"
        f"{metrics['tau2_matched_boundary_mean_reward']:.1f}; "
        f"{metrics['tau2_matched_boundary_regressions']} regressions."
    )
    current_model_loop = (
        f"Qwen+boundary {story_summary['model_in_loop_govkernel_passes']}/"
        f"{story_summary['model_in_loop_govkernel_trials']} official model-in-loop passes."
    )
    current_reliability = (
        f"{metrics['stage2_clean_trials']}/{metrics['stage2_clean_trials']} boundary-run official passes; "
        "used only as upper-bound reliability."
    )

    return [
        _row(
            "S1_CORE_RSI_STREAM",
            "tau2-Bench",
            "generation stream",
            "Qwen3.8-27B-long32k",
            "method_scale",
            45,
            "main_positive",
            "Inherited boundary updates should make correct proposals become correct business effects.",
            current_tau2,
            "Run inherited, reset, static, and text-memory conditions on source, validation, and frozen held-out tasks.",
            inclusion_rule,
            "Freeze generation orderings; start B0->B5 with no manual update edits after generation 0.",
        ),
        _row(
            "S2_CORE_RSI_STREAM_TB",
            "Terminal-Bench 2.1",
            "generation stream",
            "Qwen3.8-27B-long32k",
            "method_scale",
            45,
            "main_positive",
            "The same inherited boundary should improve terminal effects without becoming a solver.",
            current_model_loop,
            "Run inherited, reset, static, and text-memory conditions on Git, data, DB, and service state tasks.",
            inclusion_rule,
            "Convert current reference-boundary anchors into model-in-loop fork-at-boundary tasks before scaling.",
        ),
        _row(
            "S3_CORE_RSI_STREAM_SF",
            "SkillFlow",
            "generation stream",
            "Qwen3.8-27B-long32k",
            "method_scale",
            45,
            "main_positive",
            "Inherited boundaries should externalize completed workflow evidence into artifacts.",
            current_model_loop,
            "Run inherited, reset, static, and text-memory conditions across OCR, healthcare, and reconciliation families.",
            inclusion_rule,
            "Use generic table/workbook serializers fed by model-produced rows, not task-answer code.",
        ),
        _row(
            "S4_TAU2_MATCHED_FORK",
            "tau2-Bench",
            "matched fork",
            "Qwen3.8-27B-long32k | Mistral/Gemma held-out open model",
            "method_scale",
            25,
            "main_positive",
            "A precommit fork should change final state without changing the dialogue actor.",
            current_tau2,
            "Fork at ProposalOK on cancellation, refund, exchange, and account-write tasks.",
            inclusion_rule,
            "Hold actor, user condition, tool state, token budget, and wall clock fixed.",
        ),
        _row(
            "S5_TB_MATCHED_FORK",
            "Terminal-Bench 2.1",
            "matched fork",
            "Qwen3.8-27B-long32k | Codex/Claude strong terminal agent",
            "method_scale",
            25,
            "main_positive",
            "The boundary should stage and validate terminal effects rather than write the solution itself.",
            current_reliability,
            "Fork at ProposalOK on Git scope, preserving read, log artifact, security patch, and service-state tasks.",
            inclusion_rule,
            "Boundary may stage, diff, validate, and request revision; it may not infer XOR keys or author task patches.",
        ),
        _row(
            "S6_SF_MATCHED_FORK",
            "SkillFlow",
            "matched fork",
            "Qwen3.8-27B-long32k | Mistral/Gemma held-out open model",
            "method_scale",
            25,
            "main_positive",
            "Workflow rows produced by the actor should be the input to the boundary, not hidden constants.",
            current_model_loop,
            "Fork when structured rows become complete and compare natural continuation to boundary finalization.",
            inclusion_rule,
            "Boundary writes only from actor-generated rows plus declared schema and output path.",
        ),
        _row(
            "S7_TAU2_ACTION_PAIRS",
            "tau2-Bench",
            "action pair geometry",
            "Qwen3.8-27B-long32k",
            "method_scale",
            15,
            "main_positive",
            "Ready and unready business writes should be evaluated as paired state geometries.",
            current_tau2,
            "Build legal/illegal cancellation, refund, exchange, and policy-shift pairs.",
            inclusion_rule,
            "Macro-average by unique pair; seeds are averaged within each task.",
        ),
        _row(
            "S8_TB_ACTION_PAIRS",
            "Terminal-Bench 2.1",
            "action pair geometry",
            "Qwen3.8-27B-long32k",
            "method_scale",
            15,
            "main_positive",
            "The same terminal operation can be ready, out of scope, or destructive depending on state.",
            current_reliability,
            "Build pairs for working-tree-only edits, history rewrites, fragile reads, and existing output files.",
            inclusion_rule,
            "Score pair accuracy, collateral mutation, and missing finalization by unique task pair.",
        ),
        _row(
            "S9_SF_ACTION_PAIRS",
            "SkillFlow",
            "action pair geometry",
            "Qwen3.8-27B-long32k",
            "method_scale",
            15,
            "main_positive",
            "Artifact completion should depend on row completeness, schema, source authority, and target freshness.",
            current_model_loop,
            "Build rows-complete/rows-missing, schema-ready/schema-ambiguous, and stale-output pairs.",
            inclusion_rule,
            "Use task family as the statistical cluster; do not count repeated seeds as independent tasks.",
        ),
        _row(
            "S10_GENERALIZED_TRANSFER",
            "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "generalized transfer",
            "Qwen3.8-27B-long32k",
            "method_scale",
            30,
            "main_positive",
            "Learned updates should apply by action structure rather than task ID.",
            f"{story_summary['passed_checks']}/{story_summary['total_checks']} current paper-code consistency checks pass.",
            "Compare abstract executable updates against task-local memory on frozen held-out target families.",
            inclusion_rule,
            "Freeze update text, applicability condition, and compiler settings before target verifier results are read.",
        ),
        _row(
            "S11_REASONING_ACTION_2X2",
            "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "reasoning-action 2x2",
            "Qwen3.8-27B-long32k",
            "method_scale",
            48,
            "main_positive",
            "Reasoning-side RSI should raise ProposalOK; action-side RSI should raise realization.",
            current_model_loop,
            "Run base, text memory or skill, action-boundary update, and joint conditions.",
            inclusion_rule,
            "Report ProposalOK, EffectOK, RealizationRate, over-action, under-action, and cost.",
        ),
        _row(
            "S12_SECOND_OPEN_MODEL_HELDOUT",
            "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "held-out model",
            "Mistral/Gemma held-out open model",
            "method_scale",
            30,
            "main_positive",
            "A frozen descendant boundary should help an open model that was not used to tune it.",
            current_tau2,
            "Run ancestor and final descendant only on the frozen held-out stream.",
            inclusion_rule,
            "No model-specific thresholds or boundary edits after the primary-model B5 is frozen.",
        ),
        _row(
            "S13_STRONG_AGENT_BASELINE",
            "Terminal-Bench 2.1 | SkillFlow",
            "strong faithful baseline",
            "Codex/Claude strong terminal agent",
            "faithful_baseline",
            20,
            "faithful_counterpoint",
            "A stronger ordinary agent should be evaluated faithfully on the same held-out task stream.",
            f"{comparison_summary['faithful_baseline_rows']} faithful baseline row is already separated from ablations.",
            "Run the strong agent's normal workflow on the frozen representative subset.",
            inclusion_rule,
            "Use the ordinary external-agent protocol and matched wall-clock budget; do not weaken tools or prompts.",
        ),
        _row(
            "S14_MECHANISM_CUTS",
            "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "mechanism cuts",
            "Qwen3.8-27B-long32k",
            "mechanism_ablation",
            35,
            "mechanism_explanation",
            "Ablations should explain which boundary component carries the effect.",
            f"{comparison_summary['completed_mechanism_ablation_rows']} completed mechanism-cut rows exist in the seed record.",
            "Cut readiness, scope, preserve, completion trigger, regression selection, and inheritance.",
            inclusion_rule,
            "Report these as mechanism cuts, never as faithful external baselines.",
        ),
        _row(
            "S15_ORACLE_BOUNDARY_UPPER_BOUND",
            "Terminal-Bench 2.1 | SkillFlow",
            "reference upper bound",
            "action-boundary runtime",
            "runtime_reliability",
            10,
            "supporting_reproduction",
            "Existing executable adapters show what a correct boundary can express.",
            current_reliability,
            "Keep reference adapters as an upper-bound and reproducibility block.",
            inclusion_rule,
            "Do not include these rows in matched-agent treatment effects.",
        ),
        _row(
            "S16_FREEZE_STATISTICS_RELEASE",
            "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "statistical freeze",
            "Qwen3.8-27B-long32k | Mistral/Gemma held-out open model | Codex/Claude strong terminal agent",
            "statistical_freeze",
            10,
            "claim_boundary",
            "Final claims should be generated from frozen splits and releasable artifacts.",
            f"{story_summary['passed_checks']}/{story_summary['total_checks']} consistency checks pass.",
            "Freeze task selection, metrics, exclusions, anonymization, and paper-number exports before final scoring.",
            inclusion_rule,
            "Use task-cluster bootstrap, paired tests, and generated paper/code consistency checks.",
        ),
    ]


def _row(
    target_id: str,
    benchmark: str,
    task_type: str,
    model_family: str,
    condition_role: str,
    target_n: int,
    paper_use: str,
    story_axis: str,
    current_positive_evidence: str,
    scale_target: str,
    inclusion_rule: str,
    next_run: str,
) -> dict[str, str]:
    return {
        "target_id": target_id,
        "benchmark": benchmark,
        "task_type": task_type,
        "model_family": model_family,
        "condition_role": condition_role,
        "target_n": str(target_n),
        "paper_use": paper_use,
        "story_axis": story_axis,
        "current_positive_evidence": current_positive_evidence,
        "scale_target": scale_target,
        "inclusion_rule": inclusion_rule,
        "next_run": next_run,
    }


def _summarize(
    rows: list[dict[str, str]],
    metrics: dict[str, Any],
    comparison_summary: dict[str, Any],
    story_summary: dict[str, Any],
) -> dict[str, Any]:
    benchmark_task_types: dict[str, set[str]] = {}
    model_families: set[str] = set()
    for row in rows:
        if row["condition_role"] == "method_scale":
            for benchmark in _split_field(row["benchmark"]):
                benchmark_task_types.setdefault(benchmark, set()).add(row["task_type"])
        for model in _split_field(row["model_family"]):
            model_families.add(model)

    return {
        "scale_target_rows": len(rows),
        "benchmarks_targeted": len(benchmark_task_types),
        "model_families_targeted": len(model_families),
        "min_task_types_per_benchmark": min(len(task_types) for task_types in benchmark_task_types.values()),
        "faithful_baseline_scale_rows": sum(1 for row in rows if row["condition_role"] == "faithful_baseline"),
        "mechanism_ablation_scale_rows": sum(1 for row in rows if row["condition_role"] == "mechanism_ablation"),
        "baseline_ablation_overlap": comparison_summary["baseline_ablation_overlap"],
        "total_target_trials": sum(int(row["target_n"]) for row in rows),
        "current_clean_positive_passes": metrics["stage2_clean_trials"],
        "current_clean_positive_trials": metrics["stage2_clean_trials"],
        "current_faithful_baseline_trials": metrics["faithful_baseline_trials"],
        "mechanism_ablation_rows": comparison_summary["mechanism_ablation_rows"],
        "completed_mechanism_ablation_rows": comparison_summary["completed_mechanism_ablation_rows"],
        "story_gate_checks": story_summary["total_checks"],
    }


def _split_field(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def _write_scale_plan_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SCALE_PLAN_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTASubmissionScaleRows": summary["scale_target_rows"],
        "LTASubmissionScaleBenchmarks": summary["benchmarks_targeted"],
        "LTASubmissionScaleModelFamilies": summary["model_families_targeted"],
        "LTASubmissionScaleMinTaskTypes": summary["min_task_types_per_benchmark"],
        "LTASubmissionScaleFaithfulBaselineRows": summary["faithful_baseline_scale_rows"],
        "LTASubmissionScaleMechanismAblationRows": summary["mechanism_ablation_scale_rows"],
        "LTASubmissionScaleTargetTrials": summary["total_target_trials"],
        "LTASubmissionCurrentCleanPasses": summary["current_clean_positive_passes"],
        "LTASubmissionCurrentCleanTrials": summary["current_clean_positive_trials"],
        "LTASubmissionCompletedAblationRows": summary["completed_mechanism_ablation_rows"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/submission_scale_plan.py.",
        "% Regenerate with License_code/scripts/export_submission_scale_plan.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

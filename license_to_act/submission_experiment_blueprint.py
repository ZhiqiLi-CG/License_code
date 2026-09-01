from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .evidence_portfolio import build_evidence_portfolio
from .story_claims import build_story_claims


BLUEPRINT_FIELDS = [
    "blueprint_id",
    "benchmark",
    "claim_axis",
    "split_policy",
    "model_slots",
    "comparison_class",
    "paper_role",
    "target_run_cells",
    "inclusion_rule",
    "primary_metric",
    "acceptance_gate",
    "baseline_boundary",
]

TARGET_MODEL_SLOTS = [
    "Qwen3.8-27B-long32k",
    "Mistral/Gemma held-out open model",
    "Codex/Claude strong terminal agent",
]


def build_submission_experiment_blueprint(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    claims = build_story_claims(root)
    portfolio = build_evidence_portfolio(root)
    comparison = build_comparison_manifest(root)
    metrics = claims["headline_metrics"]

    rows = [
        {
            "blueprint_id": "E1_CORE_RSI_GENERATION_CURVE",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The inherited action boundary should improve how correct proposals become external effects.",
            "split_policy": "Freeze source, validation, and held-out streams before generation 0; use three independent task orderings.",
            "model_slots": "Qwen3.8-27B-long32k",
            "comparison_class": "inherited_vs_reset_rsi",
            "paper_role": "main_positive_scale",
            "target_run_cells": "180",
            "inclusion_rule": "Include proposal-to-effect tasks with predeclared intermediate and final verifiers.",
            "primary_metric": "held-out realization rate and EffectOK conditioned on ProposalOK",
            "acceptance_gate": (
                "Inherited B5 beats reset and static on the frozen held-out stream; "
                "no manual update edits after generation starts; source and validation outcomes select updates."
            ),
            "baseline_boundary": "Static B0 and equal-budget reset updater receive the same source evidence but do not inherit past updates.",
        },
        {
            "blueprint_id": "E2_MATCHED_FORK_AT_BOUNDARY",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Changing the proposal-to-effect interface should close gaps without changing the actor.",
            "split_policy": "Fork when ProposalOK first becomes true; preserve initial state, actor, tools, and remaining budget.",
            "model_slots": "Qwen3.8-27B-long32k | Mistral/Gemma held-out open model",
            "comparison_class": "matched_fork_at_boundary",
            "paper_role": "main_positive_scale",
            "target_run_cells": "120",
            "inclusion_rule": "Include proposal-to-effect pairs where the fork point and verifier are fixed before outcomes are scored.",
            "primary_metric": "EffectOK without boundary versus with boundary at the same fork point",
            "acceptance_gate": (
                "same actor, task, state, tool surface, token budget, and wall clock; fork at ProposalOK; "
                "Boundary cannot solve the domain algorithm or inject task answers."
            ),
            "baseline_boundary": "Direct execution continues with the same actor and tools; the boundary condition stages and validates the same candidate effects.",
        },
        {
            "blueprint_id": "E3_ACTION_PAIR_GEOMETRY_60",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The boundary should commit ready effects and refuse matched premature or out-of-scope effects.",
            "split_policy": "Freeze 50-60 independent action pairs across business writes, terminal state, and workflow artifacts.",
            "model_slots": "Qwen3.8-27B-long32k",
            "comparison_class": "paired_action_geometry",
            "paper_role": "main_positive_scale",
            "target_run_cells": "120",
            "inclusion_rule": "Include proposal-to-effect pairs selected by task geometry, not by observed pass/fail outcomes.",
            "primary_metric": "pair accuracy macro-averaged by unique pair and benchmark family",
            "acceptance_gate": (
                "macro-average by unique pair; seeds are averaged within task; ready recall remains high while unauthorized "
                "and missing-action rates decrease."
            ),
            "baseline_boundary": "No-boundary and generic B0 conditions are evaluated on the same frozen pair list.",
        },
        {
            "blueprint_id": "E4_GENERALIZED_VS_TASK_LOCAL_TRANSFER",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Boundary updates should transfer by action pattern rather than task ID.",
            "split_policy": "Generate updates from source families only; freeze applicability conditions before target families are evaluated.",
            "model_slots": "Qwen3.8-27B-long32k",
            "comparison_class": "generalized_vs_task-local",
            "paper_role": "main_positive_scale",
            "target_run_cells": "96",
            "inclusion_rule": "Include proposal-to-effect source and held-out families with shared action structure.",
            "primary_metric": "held-out gain, applicability precision, coverage, and target regression rate",
            "acceptance_gate": (
                "generalized update beats task-local memory on held-out families; no manual lowering to target task IDs; "
                "negative transfer is reported."
            ),
            "baseline_boundary": "Task-local patches may memorize source cases but cannot inspect held-out target verifier outcomes.",
        },
        {
            "blueprint_id": "E5_REASONING_RSI_X_ACTION_RSI",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Better proposal formation and better proposal realization should be complementary.",
            "split_policy": "Run a 2x2 grid: base, text memory or skill, action-boundary update, and joint condition.",
            "model_slots": "Qwen3.8-27B-long32k",
            "comparison_class": "memory_x_action_boundary",
            "paper_role": "main_positive_scale",
            "target_run_cells": "96",
            "inclusion_rule": "Include proposal-to-effect rows where ProposalOK and EffectOK are both measured.",
            "primary_metric": "ProposalOK, EffectOK, realization rate, over-action, under-action, and cost",
            "acceptance_gate": (
                "Joint condition beats either single side; memory primarily raises ProposalOK, while the boundary raises "
                "EffectOK conditioned on ProposalOK."
            ),
            "baseline_boundary": "Textual memory/skill conditions are faithful reasoning-side RSI controls, not boundary ablations.",
        },
        {
            "blueprint_id": "E6_SECOND_OPEN_MODEL_HELDOUT",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "A learned boundary should help a held-out open-model actor after the boundary is frozen.",
            "split_policy": "Hold the second open model out until B5, task pairs, and metrics are frozen.",
            "model_slots": "Mistral/Gemma held-out open model",
            "comparison_class": "heldout_model_method",
            "paper_role": "main_positive_scale",
            "target_run_cells": "54",
            "inclusion_rule": "Include proposal-to-effect pairs from the frozen held-out stream.",
            "primary_metric": "held-out reward lift, realization-rate lift, and pass-to-failure regression",
            "acceptance_gate": "held out until B5 is frozen; same matched protocol as the primary actor; no model-specific boundary edits.",
            "baseline_boundary": "The held-out actor is not used during update generation or threshold selection.",
        },
        {
            "blueprint_id": "E7_STRONG_AGENT_SUBSET",
            "benchmark": "Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "A high-capability ordinary agent is the cleanest counterpoint to action-boundary improvement.",
            "split_policy": "Run the frozen representative pair subset after the boundary and task list are fixed.",
            "model_slots": "Codex/Claude strong terminal agent",
            "comparison_class": "faithful_baseline",
            "paper_role": "main_counterpoint",
            "target_run_cells": "40",
            "inclusion_rule": "Include proposal-to-effect tasks from the frozen representative subset.",
            "primary_metric": "official reward and proposal-to-effect failure class under the agent's normal protocol",
            "acceptance_gate": "faithful baseline uses the external agent's ordinary workflow, same task subset, and matched wall-clock budget.",
            "baseline_boundary": "Do not weaken prompts, tools, or budget to create failures.",
        },
        {
            "blueprint_id": "E8_MECHANISM_CUTS",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Ablations should explain the learned boundary without masquerading as external baselines.",
            "split_policy": "Run cuts only after the full boundary and task selection are frozen.",
            "model_slots": "Qwen3.8-27B-long32k",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_explanation",
            "target_run_cells": "80",
            "inclusion_rule": "Include proposal-to-effect cases touched by the removed boundary mechanism.",
            "primary_metric": "delta in realization rate, over-action, under-action, and collateral mutation",
            "acceptance_gate": "each mechanism cut restores its paired failure class without being labeled a faithful baseline.",
            "baseline_boundary": "Ablations are internal cuts of our own boundary, not reproductions of outside methods.",
        },
        {
            "blueprint_id": "E9_ORACLE_BOUNDARY_UPPER_BOUND",
            "benchmark": "Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Reference boundary programs are an upper bound on what the learned boundary should approach.",
            "split_policy": "Keep existing executable adapters out of the main matched causal comparison.",
            "model_slots": "action-boundary runtime",
            "comparison_class": "runtime_reliability",
            "paper_role": "upper_bound_reliability",
            "target_run_cells": "30",
            "inclusion_rule": "Include proposal-to-effect anchors only as implementation reliability or reference upper-bound rows.",
            "primary_metric": "official verifier pass rate and reproducibility under K=5 reruns",
            "acceptance_gate": "upper-bound rows must be labeled separately from matched-agent treatment effects.",
            "baseline_boundary": "These rows show boundary expressivity and release reliability, not actor-level treatment effect.",
        },
        {
            "blueprint_id": "E10_FREEZE_STATISTICS_RELEASE",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The final claim should be backed by frozen splits, generated numbers, and releasable artifacts.",
            "split_policy": "Lock task list, model list, metrics, exclusion rules, and anonymization before final scoring.",
            "model_slots": "Qwen3.8-27B-long32k | Mistral/Gemma held-out open model | Codex/Claude strong terminal agent",
            "comparison_class": "scale_statistics",
            "paper_role": "submission_gate",
            "target_run_cells": "10",
            "inclusion_rule": "Include proposal-to-effect results only when raw artifacts, generated tables, and paper text agree.",
            "primary_metric": "cluster bootstrap intervals, paired tests, role separation, and paper-code consistency",
            "acceptance_gate": "all main-text numbers are generated from data files; task is the statistical unit; infrastructure failures are separated.",
            "baseline_boundary": "Faithful baselines, mechanism ablations, and upper-bound adapters remain separate fields in the released CSVs.",
        },
    ]

    summary = _summarize(rows)
    summary.update(
        {
            "current_clean_positive_passes": portfolio["summary"]["clean_positive_passes"],
            "current_clean_positive_trials": portfolio["summary"]["clean_positive_trials"],
            "current_faithful_baseline_trials": comparison["summary"]["faithful_baseline_trials"],
            "current_tau2_read_correct_write_wrong_proxy": metrics["tau2_read_correct_write_wrong_proxy"],
        }
    )
    return {"summary": summary, "target_model_slots": TARGET_MODEL_SLOTS, "rows": rows}


def write_submission_experiment_blueprint(
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
        else root / "artifacts" / "paper_results" / "lta_submission_experiment_blueprint_20260831.json"
    )

    blueprint = build_submission_experiment_blueprint(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    blueprint_csv = paper_data_dir / "submission_experiment_blueprint.csv"
    latex_numbers = paper_sections_dir / "generated_experiment_blueprint_numbers.tex"
    _write_blueprint_csv(blueprint_csv, blueprint["rows"])
    latex_numbers.write_text(_latex_numbers(blueprint["summary"]), encoding="utf-8")

    blueprint["outputs"] = {
        "summary_json": str(summary_path),
        "blueprint_csv": str(blueprint_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(blueprint, indent=2), encoding="utf-8")
    return blueprint


def _summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    comparison_classes = [row["comparison_class"] for row in rows]
    target_run_cells = sum(int(row["target_run_cells"]) for row in rows)
    main_positive_run_cells = sum(
        int(row["target_run_cells"]) for row in rows if row["paper_role"] == "main_positive_scale"
    )
    baseline_ablation_overlap = sum(
        1 for row in rows if row["comparison_class"] == "faithful_baseline" and "ablation" in row["paper_role"]
    )
    baseline_ablation_overlap += sum(
        1 for row in rows if row["comparison_class"] == "mechanism_ablation" and "baseline" in row["paper_role"]
    )
    return {
        "blueprint_rows": len(rows),
        "benchmark_families": 3,
        "target_model_slots": len(TARGET_MODEL_SLOTS),
        "minimum_planned_run_cells": target_run_cells,
        "main_positive_scale_run_cells": main_positive_run_cells,
        "faithful_baseline_blocks": comparison_classes.count("faithful_baseline"),
        "mechanism_ablation_blocks": comparison_classes.count("mechanism_ablation"),
        "baseline_ablation_overlap": baseline_ablation_overlap,
    }


def _write_blueprint_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BLUEPRINT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAExperimentBlueprintRows": summary["blueprint_rows"],
        "LTAExperimentBlueprintBenchmarks": summary["benchmark_families"],
        "LTAExperimentBlueprintModelSlots": summary["target_model_slots"],
        "LTAExperimentBlueprintRunCells": summary["minimum_planned_run_cells"],
        "LTAExperimentBlueprintMainPositiveRunCells": summary["main_positive_scale_run_cells"],
        "LTAExperimentBlueprintFaithfulBaselineBlocks": summary["faithful_baseline_blocks"],
        "LTAExperimentBlueprintMechanismAblationBlocks": summary["mechanism_ablation_blocks"],
        "LTAExperimentBlueprintOverlap": summary["baseline_ablation_overlap"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/submission_experiment_blueprint.py.",
        "% Regenerate with License_code/scripts/export_submission_experiment_blueprint.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

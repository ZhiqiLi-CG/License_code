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
    "Qwen3.8-27B",
    "Qwen3.8-27B-long32k",
    "Mistral-Small-3.2-24B",
    "Gemma-4-31B-it",
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
            "blueprint_id": "E1_TAU2_AIRLINE_WRITE_AUTHORITY",
            "benchmark": "tau2-Bench",
            "claim_axis": "Intent proposes; policy and source state authorize.",
            "split_policy": "Freeze airline write-family source, validation, and held-out tasks before final scoring.",
            "model_slots": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it | Qwen3.8-27B-long32k",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "80",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "unsafe write reduction with authorized-write recall",
            "acceptance_gate": (
                "Gate A/D: same backbone, same harness, same budget; McNemar p < 0.05; "
                "authorized-commit recall loss <= 3pp; actual pre-commit interventions on mined traces."
            ),
            "baseline_boundary": "Faithful baselines use the same tau2 simulator and tool policy without LTA commit authority.",
        },
        {
            "blueprint_id": "E2_TAU2_CROSS_DOMAIN_WRITES",
            "benchmark": "tau2-Bench",
            "claim_axis": "Authority transfer should survive outside airline cancellation.",
            "split_policy": "Preselect retail, banking, and telecom write families by visible policy/state features.",
            "model_slots": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it | Qwen3.8-27B-long32k",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "120",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "reward, DB pass, communication pass, overblocking",
            "acceptance_gate": (
                "Gate A/D: >=15 tasks in each state substrate slice; unsafe writes decrease; "
                "legal writes remain ALLOW with authorized-commit recall loss <= 3pp."
            ),
            "baseline_boundary": "Domain transfer is evaluated after the write-family list is frozen.",
        },
        {
            "blueprint_id": "E3_TB_12_TASK_AUTHORITY_PILOT",
            "benchmark": "Terminal-Bench 2.1",
            "claim_axis": "Terminal actions need region, side-effect, and witness authority.",
            "split_policy": "Freeze a 12-task pilot across Git, DB, security, data, image/document, and process state.",
            "model_slots": "Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it | Codex/Claude strong terminal agent",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "60",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "official reward plus collateral-mutation and missing-artifact rates",
            "acceptance_gate": (
                "Gate A: same backbone, same harness, same budget, +/-GovKernel; "
                "official pass rate improves and collateral mutation decreases."
            ),
            "baseline_boundary": "No public solution scripts may generate warrants for live runs.",
        },
        {
            "blueprint_id": "E4_TB_STRATIFIED_MAIN_SWEEP",
            "benchmark": "Terminal-Bench 2.1",
            "claim_axis": "The terminal authority pattern should scale beyond anchors.",
            "split_policy": "Run a 45-task stratified sweep only after the 12-task pilot passes the acceptance gate.",
            "model_slots": "Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it | Codex/Claude strong terminal agent",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "180",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "pass rate, false-done rate, authorized commit success",
            "acceptance_gate": (
                "Gate A/E: frozen pilot success before sweep; pass-rate CI reported; "
                "runtime failures separated from behavior claims."
            ),
            "baseline_boundary": "Report Harbor/runtime failures separately from behavioral failures.",
        },
        {
            "blueprint_id": "E5_SKILLFLOW_ARTIFACT_OBLIGATIONS",
            "benchmark": "SkillFlow",
            "claim_axis": "Complete evidence can oblige verifier-visible artifacts.",
            "split_policy": "Freeze OCR, healthcare, document-fraud, and cross-format families before outcome inspection.",
            "model_slots": "Qwen3.8-27B | Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "96",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "artifact existence, schema pass, reward, obligation completion",
            "acceptance_gate": (
                "Gate A/C: same agent +/-GovKernel; OBLIGE removal restores missing-workbook failures; "
                "wrong materialization rate is reported."
            ),
            "baseline_boundary": "Artifact materializers are compared against matched agents and named mechanism cuts.",
        },
        {
            "blueprint_id": "E6_SKILLFLOW_SKILL_AUTHORITY_TRANSFER",
            "benchmark": "SkillFlow",
            "claim_axis": "Skill reuse needs authority, not only memory.",
            "split_policy": "Evaluate skill/body visibility and held-out transfer after source-family compiler selection.",
            "model_slots": "Qwen3.8-27B | Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "96",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "negative transfer, skill admission, held-out reward",
            "acceptance_gate": (
                "Gate B/C: source-generated amendment improves held-out tasks; "
                "positive-only skill growth and task-ID hand guard are separated from LTA."
            ),
            "baseline_boundary": "Positive-only skill growth is an external-style baseline only when reproduced faithfully.",
        },
        {
            "blueprint_id": "E7_MODEL_BREADTH_HELDOUT",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The institution should help frozen actors rather than one wrapper.",
            "split_policy": "Hold Gemma and one strong terminal agent out until the compiler and tasks are frozen.",
            "model_slots": "Gemma-4-31B-it | Codex/Claude strong terminal agent",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "60",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "held-out reward lift and pass-to-fail regression",
            "acceptance_gate": (
                "Gate A/B: second open model and one strong agent satisfy the same matched-causal criteria "
                "after compiler freeze."
            ),
            "baseline_boundary": "Held-out actors are not used for license design choices.",
        },
        {
            "blueprint_id": "E8_STRONG_AGENT_BASELINES",
            "benchmark": "Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "A strong ordinary agent is the cleanest counterpoint to authority compilation.",
            "split_policy": "Run Codex or Claude baselines on the frozen anchor and pilot sets.",
            "model_slots": "Codex/Claude strong terminal agent",
            "comparison_class": "faithful_baseline",
            "paper_role": "main_counterpoint",
            "target_run_cells": "25",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "official reward under the external agent's normal protocol",
            "acceptance_gate": (
                "Gate A: faithful baseline uses normal external-agent protocol, same task set, and matched budget."
            ),
            "baseline_boundary": "Do not weaken prompts, tools, or budgets to create a baseline failure.",
        },
        {
            "blueprint_id": "E9_FAITHFUL_OPEN_MODEL_LADDER",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Long context and ordinary agency must be tested before claiming institutional lift.",
            "split_policy": "Run matched open-model baselines on every final headline family.",
            "model_slots": "Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "comparison_class": "faithful_baseline",
            "paper_role": "main_counterpoint",
            "target_run_cells": "60",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "official reward and failure class without GovKernel",
            "acceptance_gate": (
                "Gate A/E: same backbone and budget as LTA condition; all pass rates include confidence intervals."
            ),
            "baseline_boundary": "Baseline configs reproduce the external agent; they are not mechanism ablations.",
        },
        {
            "blueprint_id": "E10_MECHANISM_CUTS",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "Ablations explain which part of the institution carries the result.",
            "split_policy": "Run cuts only after the full LTA condition and task selection are frozen.",
            "model_slots": "Qwen3.8-27B | Qwen3.8-27B-long32k",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_explanation",
            "target_run_cells": "120",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "delta in veto precision, obligation completion, and collateral mutation",
            "acceptance_gate": (
                "Gate C: each ablation restores its paired failure class; task-ID hand guard ties source tasks "
                "but loses on held-out families."
            ),
            "baseline_boundary": "Ablations are internal cuts; they must not be described as faithful baselines.",
        },
        {
            "blueprint_id": "E11_COMPILER_GENERATION_TRANSFER",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The recursively improving object is the evolving authority compiler.",
            "split_policy": "Generate licenses from source tasks, validate on regression tasks, then freeze for held-out transfer.",
            "model_slots": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "comparison_class": "method_condition",
            "paper_role": "main_positive_scale",
            "target_run_cells": "72",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "failure-to-pass transfer with pass-to-fail regression",
            "acceptance_gate": (
                "Gate B: at least two automatic amendments are accepted; held-out transfer has >=3 F-to-P "
                "and P-to-F = 0 across the regression set."
            ),
            "baseline_boundary": "Source, validation, and held-out splits are declared before target verifier inspection.",
        },
        {
            "blueprint_id": "E12_FREEZE_STATISTICS_REGRESSION",
            "benchmark": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "claim_axis": "The claim earns trust by freezing the evaluation before final scoring.",
            "split_policy": "Lock task list, model list, metrics, and exclusion rules before the final positive-mass run.",
            "model_slots": "Qwen3.8-27B | Qwen3.8-27B-long32k | Mistral-Small-3.2-24B | Gemma-4-31B-it | Codex/Claude strong terminal agent",
            "comparison_class": "scale_statistics",
            "paper_role": "submission_gate",
            "target_run_cells": "36",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "primary_metric": "confidence intervals, paired tests, and no-regression checks",
            "acceptance_gate": (
                "Gate E/F: source-validation-held-out split is committed before verifier runs; "
                "all main-text numbers are generated from data files; raw logs are anonymized for release."
            ),
            "baseline_boundary": "Exploratory failures that do not test the authority mechanism stay outside the paper package.",
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
        writer = csv.DictWriter(handle, fieldnames=BLUEPRINT_FIELDS)
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

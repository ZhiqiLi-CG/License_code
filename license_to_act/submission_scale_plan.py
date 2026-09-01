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


def build_submission_scale_plan(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    claims = build_story_claims(root)
    comparison = build_comparison_manifest(root)
    story_gate = build_story_gate_report(root)
    metrics = claims["headline_metrics"]
    comparison_summary = comparison["summary"]
    inclusion_rule = "Include only tasks that sharpen the proposal-to-effect boundary."

    rows = [
        {
            "target_id": "S1_TAU2_WRITE_FAMILIES",
            "benchmark": "tau2-Bench",
            "task_type": "policy-invalid write",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "40",
            "paper_use": "main_positive",
            "story_axis": "Proposed effects must be ready before business writes commit.",
            "current_positive_evidence": (
                f"{metrics['tau2_read_correct_write_wrong_proxy']} read-correct/write-wrong cancellation commits "
                f"from {metrics['tau2_result_files']} local result files; "
                f"{metrics['stage1_preserved_positive']} legal tau2 commit preserved."
            ),
            "scale_target": "Run authorized and unauthorized write families across airline, retail, banking, and telecom.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Freeze write-family task list, then run full, prompt, static-boundary, and action-boundary conditions.",
        },
        {
            "target_id": "S2_TAU2_AUTHORIZED_WRITES",
            "benchmark": "tau2-Bench",
            "task_type": "authorized write",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "24",
            "paper_use": "positive_non_regression",
            "story_axis": "Prepared business writes must still commit.",
            "current_positive_evidence": (
                f"{metrics['stage1_preserved_positive']} legal tau2 commit preserved in the seed record."
            ),
            "scale_target": "Pair invalid-write cases with legal same-operation commits across airline and retail.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run legal cancellation, upgrade, exchange, and update tasks under the same controller.",
        },
        {
            "target_id": "S3_TAU2_REFUND_COMPENSATION",
            "benchmark": "tau2-Bench",
            "task_type": "refund or compensation",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "30",
            "paper_use": "main_positive",
            "story_axis": "Money-moving actions need readiness evidence, not intent alone.",
            "current_positive_evidence": (
                "Seed tau2 interventions already separate unsupported compensation from legal cancellation."
            ),
            "scale_target": "Add refund, certificate, and compensation families where policy preconditions are explicit.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Mine candidate tasks, then run paired precommit conditions before held-out model slices.",
        },
        {
            "target_id": "S4_TAU2_RETAIL_EXCHANGE",
            "benchmark": "tau2-Bench",
            "task_type": "retail exchange",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "30",
            "paper_use": "main_positive",
            "story_axis": "The action boundary should transfer beyond airline policies.",
            "current_positive_evidence": (
                f"{metrics['tau2_result_files']} local tau2 result files include retail traces for scale mining."
            ),
            "scale_target": "Run delivered-item exchange and return/update slices with explicit user-consent receipts.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Use projected order evidence, source-bound write readiness, and legal non-write controls.",
        },
        {
            "target_id": "S5_TAU2_ACCOUNT_PLAN_MUTATION",
            "benchmark": "tau2-Bench",
            "task_type": "account or plan mutation",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "30",
            "paper_use": "main_positive",
            "story_axis": "State-changing service actions should use the same proposal-to-effect boundary.",
            "current_positive_evidence": (
                "The local tau2 inventory contains banking and telecom write-heavy domains."
            ),
            "scale_target": "Add banking and telecom account/package mutations after airline and retail freeze.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Prioritize tasks with explicit policy preconditions and evaluable state outcomes.",
        },
        {
            "target_id": "S6_TB_GIT_SCOPE",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "git scope",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "15",
            "paper_use": "main_positive",
            "story_axis": "Shell proposals need scoped write sets and preservation checks.",
            "current_positive_evidence": (
                f"{metrics['stage2_terminal_clean_trials']}/{metrics['stage2_terminal_clean_trials']} "
                "official Terminal-Bench passes across Git, WAL, truncated-SQLite, and log-summary anchors."
            ),
            "scale_target": "Expand Git/history tasks from sanitize and leak recovery into a scoped-write pilot.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run full agent, prompt-only, static task-local boundary, and learned action-boundary conditions on frozen Git tasks.",
        },
        {
            "target_id": "S7_TB_PRESERVING_READ",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "preserving read",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "15",
            "paper_use": "main_positive",
            "story_axis": "Some observations consume the evidence they read.",
            "current_positive_evidence": (
                "WAL recovery reaches 5/5 official passes only when the read itself is contracted."
            ),
            "scale_target": "Add database, archive, and recovery tasks where naive inspection can destroy evidence.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Audit read effects, then run preserve-first controllers against ordinary terminal agents.",
        },
        {
            "target_id": "S8_TB_BINARY_RECOVERY",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "binary recovery",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "15",
            "paper_use": "main_positive",
            "story_axis": "Corrupt state can still license exact recovery commits.",
            "current_positive_evidence": "SQLite truncate recovery reaches 5/5 official passes.",
            "scale_target": "Add recovery tasks where low-level bytes must become verifier-visible output state.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Select tasks with explicit output schema and run state-witness controllers.",
        },
        {
            "target_id": "S9_TB_SECURITY_PATCH_REPORT",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "security patch/report",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "15",
            "paper_use": "main_positive",
            "story_axis": "Security fixes require both code mutation and verifier-visible explanation.",
            "current_positive_evidence": "Current Terminal-Bench evidence includes scoped code/security boundary anchors.",
            "scale_target": "Run vulnerability-repair tasks with patch, side-effect, and report contracts.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Use source-code patch receipts plus original and added regression tests.",
        },
        {
            "target_id": "S10_TB_ARTIFACT_FINALIZATION",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "data or image artifact finalization",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "18",
            "paper_use": "main_positive",
            "story_axis": "Observed evidence must become the exact judged file.",
            "current_positive_evidence": "Current reliability results already contain missing-artifact and completion-trigger wins.",
            "scale_target": "Add log/data, document, and image-output tasks to the 12-task pilot.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Use public task specs to bind output schemas before running agents.",
        },
        {
            "target_id": "S11_TB_PROCESS_SERVICE_STATE",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "process or service state",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "method_scale",
            "target_n": "12",
            "paper_use": "main_positive",
            "story_axis": "Running services are durable effects, not just shell transcripts.",
            "current_positive_evidence": "The paper plan identifies service/process anchors as a required Terminal-Bench stratum.",
            "scale_target": "Add service configuration and process lifecycle tasks with postcondition probes.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run package/config/service receipts with syntax, port, log, and probe checks.",
        },
        {
            "target_id": "S12_SF_OCR_WORKBOOK_FINALIZATION",
            "benchmark": "SkillFlow",
            "task_type": "OCR workbook finalization",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "16",
            "paper_use": "main_positive",
            "story_axis": "Complete evidence can trigger missing workflow artifacts.",
            "current_positive_evidence": (
                f"{metrics['stage2_skillflow_clean_trials']}/{metrics['stage2_skillflow_clean_trials']} "
                "official SkillFlow passes across invoice and travel-claim materialization."
            ),
            "scale_target": "Expand OCR completion triggers beyond invoice and travel-claim anchors.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run source-bound workbook finalizers with OCR candidate and schema evidence.",
        },
        {
            "target_id": "S13_SF_TRAVEL_CLAIM_MERGE",
            "benchmark": "SkillFlow",
            "task_type": "travel claim merge",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "16",
            "paper_use": "main_positive",
            "story_axis": "Roster evidence and OCR evidence must meet before workbook commit.",
            "current_positive_evidence": "Travel-claim merge reaches 5/5 official passes with source-bound finalization.",
            "scale_target": "Add entity-join OCR tasks where a workbook is correct only after authority matching.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Bind extracted fields to authoritative roster or table state before final artifact write.",
        },
        {
            "target_id": "S14_SF_HEALTHCARE_NUMERIC_ARTIFACTS",
            "benchmark": "SkillFlow",
            "task_type": "healthcare numeric artifacts",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "18",
            "paper_use": "main_positive",
            "story_axis": "Numeric evidence must be typed before report finalization.",
            "current_positive_evidence": "Healthcare was selected as the next finalization family in the evidence plan.",
            "scale_target": "Run cost-benefit JSON/Markdown tasks with money, unit, and exact-format contracts.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Add source-table joins and precision checks before artifact commit.",
        },
        {
            "target_id": "S15_SF_CROSS_FORMAT_RECONCILIATION",
            "benchmark": "SkillFlow",
            "task_type": "cross-format reconciliation",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "16",
            "paper_use": "main_positive",
            "story_axis": "Evidence from multiple files needs one action boundary before output.",
            "current_positive_evidence": "The paper plan keeps cross-format tasks as positive breadth, not off-story filler.",
            "scale_target": "Run reconciliation tasks with source authority and output-schema boundary checks.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Use PDF/Excel/JSON source bindings and exact output schemas.",
        },
        {
            "target_id": "S16_SF_DOCUMENT_FRAUD_ARTIFACTS",
            "benchmark": "SkillFlow",
            "task_type": "document-fraud artifacts",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "16",
            "paper_use": "main_positive",
            "story_axis": "Document evidence should trigger an auditable artifact, not a loose final answer.",
            "current_positive_evidence": "Document-fraud is a target family with clear source/verifier boundaries.",
            "scale_target": "Add fraud-detection families where source citations and output schema are both judged.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run evidence-citation and schema gates against ordinary and boundary-controlled agents.",
        },
        {
            "target_id": "S17_SF_SKILL_QUARANTINE_CANARIES",
            "benchmark": "SkillFlow",
            "task_type": "skill quarantine",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "method_scale",
            "target_n": "16",
            "paper_use": "main_positive",
            "story_axis": "Reusable skill bodies are context state that can pollute external effects.",
            "current_positive_evidence": "The scale plan reserves skill-surface canaries for the final matrix.",
            "scale_target": "Compare full visible skill bodies, names-only quarantine, body-on-demand, and action-boundary control.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Select families with large visible skill bodies and clear artifact verifiers.",
        },
        {
            "target_id": "S18_TAU2_FAITHFUL_BASELINE",
            "benchmark": "tau2-Bench",
            "task_type": "faithful external-agent baseline",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "faithful_baseline",
            "target_n": "40",
            "paper_use": "faithful_counterpoint",
            "story_axis": "Baselines attack the claim; ablations explain the mechanism.",
            "current_positive_evidence": (
                f"{comparison_summary['faithful_baseline_rows']} faithful baseline row, "
                f"{metrics['faithful_baseline_trials']} trials, mean reward {metrics['faithful_baseline_mean_reward']:.1f}."
            ),
            "scale_target": "Run ordinary tau2 agents with faithful prompts and tool availability.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Keep baseline configs faithful and freeze them before mechanism ablations.",
        },
        {
            "target_id": "S19_TB_FAITHFUL_BASELINE",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "faithful external-agent baseline",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "faithful_baseline",
            "target_n": "36",
            "paper_use": "faithful_counterpoint",
            "story_axis": "A stronger terminal agent should face the same frozen tasks.",
            "current_positive_evidence": (
                f"{metrics['faithful_baseline_trials']} matched Qwen3.8-27B-long32k faithful-baseline trials."
            ),
            "scale_target": "Run mini-swe, Codex, and Claude on the same Terminal-Bench action-boundary strata.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Report official pass and false-done rates without relabeling failures as ablations.",
        },
        {
            "target_id": "S20_SF_FAITHFUL_BASELINE",
            "benchmark": "SkillFlow",
            "task_type": "faithful external-agent baseline",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "faithful_baseline",
            "target_n": "36",
            "paper_use": "faithful_counterpoint",
            "story_axis": "Workflow baselines must be evaluated as real agents, not mechanism cuts.",
            "current_positive_evidence": (
                "Current SkillFlow faithful baseline reaches 1/10 official passes on invoice and "
                "travel anchors, with no runtime errors."
            ),
            "scale_target": "Run ordinary SkillFlow agents across OCR, healthcare, document, and cross-format families.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Keep no-skill and native-skill settings separate from action-boundary ablations.",
        },
        {
            "target_id": "S21_TAU2_MECHANISM_ABLATIONS",
            "benchmark": "tau2-Bench",
            "task_type": "commit-readiness ablation",
            "model_family": "Qwen3.8-27B | Mistral-Small-3.2-24B | Gemma-4-31B-it",
            "condition_role": "mechanism_ablation",
            "target_n": "30",
            "paper_use": "mechanism_explanation",
            "story_axis": "Removing readiness should restore premature business commits.",
            "current_positive_evidence": (
                f"{comparison_summary['completed_mechanism_ablation_rows']} seed mechanism-ablation rows are complete."
            ),
            "scale_target": "Cut readiness, source authority, and user-confirmation fields on paired tau2 tasks.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run ablations after the full boundary condition and task list are frozen.",
        },
        {
            "target_id": "S22_TB_MECHANISM_ABLATIONS",
            "benchmark": "Terminal-Bench 2.1",
            "task_type": "side-effect or preserving-read ablation",
            "model_family": "Qwen3.8-27B-long32k | Codex GPT-5.5 | Claude Code",
            "condition_role": "mechanism_ablation",
            "target_n": "30",
            "paper_use": "mechanism_explanation",
            "story_axis": "Removing preserve/scope fields should reintroduce collateral mutation.",
            "current_positive_evidence": (
                f"{comparison_summary['mechanism_ablation_rows']} mechanism cuts are tracked separately."
            ),
            "scale_target": "Cut write scope, side-effect preservation, and destructive-read handling on terminal tasks.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Report these as our ablations, not external baselines.",
        },
        {
            "target_id": "S23_SF_MECHANISM_ABLATIONS",
            "benchmark": "SkillFlow",
            "task_type": "finalization-trigger ablation",
            "model_family": "Qwen3.8-27B | Qwen3.8-27B-long32k | Gemma-4-31B-it",
            "condition_role": "mechanism_ablation",
            "target_n": "30",
            "paper_use": "mechanism_explanation",
            "story_axis": "Removing completion triggers should leave evidence present but artifacts absent.",
            "current_positive_evidence": "Seed ablations already include prompt-only and no-finalization-trigger cuts.",
            "scale_target": "Cut finalization, schema, source-join, and skill-body quarantine mechanisms.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Run after full action-boundary and faithful baselines on the frozen SkillFlow families.",
        },
        {
            "target_id": "S24_FREEZE_AND_STATISTICS",
            "benchmark": "cross-benchmark",
            "task_type": "statistical freeze",
            "model_family": "all frozen model families",
            "condition_role": "statistical_freeze",
            "target_n": "1",
            "paper_use": "claim_boundary",
            "story_axis": "The story earns trust by freezing the camera before the final sweep.",
            "current_positive_evidence": (
                f"{story_gate['summary']['passed_checks']}/{story_gate['summary']['total_checks']} claim-consistency checks pass; "
                f"{comparison_summary['baseline_ablation_overlap']} baseline/ablation overlaps."
            ),
            "scale_target": "Freeze task selection, claim boundaries, and metrics before the final positive-mass run.",
            "inclusion_rule": inclusion_rule,
            "next_run": "Report confidence intervals, paired tests, and pass-to-fail regression after final runs.",
        },
    ]

    benchmark_task_types: dict[str, set[str]] = {}
    model_families: set[str] = set()
    for row in rows:
        if row["benchmark"] != "cross-benchmark" and row["condition_role"] == "method_scale":
            benchmark_task_types.setdefault(row["benchmark"], set()).add(row["task_type"])
        for model in row["model_family"].split("|"):
            model_families.add(model.strip())

    summary = {
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
        "story_gate_checks": story_gate["summary"]["total_checks"],
    }
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

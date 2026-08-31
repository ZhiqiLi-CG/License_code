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

    rows = [
        {
            "target_id": "S1_TAU2_WRITE_FAMILIES",
            "story_axis": "Intent proposes; policy and source state authorize.",
            "current_positive_evidence": (
                f"{metrics['tau2_read_correct_write_wrong_proxy']} read-correct/write-wrong cancellation commits "
                f"from {metrics['tau2_result_files']} local result files; "
                f"{metrics['stage1_preserved_positive']} legal tau2 commit preserved."
            ),
            "scale_target": "Run authorized and unauthorized write families across airline, retail, banking, and telecom.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Freeze write-family task list, then run full, prompt, static-license, and LTA conditions.",
        },
        {
            "target_id": "S2_TERMINAL_AUTHORITY_PILOT",
            "story_axis": "Shell proposals need region, side-effect, and witness authority.",
            "current_positive_evidence": (
                f"{metrics['stage2_terminal_clean_trials']}/{metrics['stage2_terminal_clean_trials']} "
                "official Terminal-Bench passes across Git, WAL, and truncated-SQLite anchors."
            ),
            "scale_target": "Expand to a 12-task authority pilot, then a 45-60 task Terminal-Bench sweep.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Add build, security, data, image/document, and process-state authority anchors.",
        },
        {
            "target_id": "S3_SKILLFLOW_OBLIGATION_FAMILIES",
            "story_axis": "Complete evidence can oblige missing workflow artifacts.",
            "current_positive_evidence": (
                f"{metrics['stage2_skillflow_clean_trials']}/{metrics['stage2_skillflow_clean_trials']} "
                "official SkillFlow passes across invoice and travel-claim materialization."
            ),
            "scale_target": "Add at least two more artifact/authority SkillFlow families before submission.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Prioritize healthcare, cross-format reconciliation, and document-fraud obligation families.",
        },
        {
            "target_id": "S4_MODEL_BREADTH",
            "story_axis": "The institution should help frozen actors, not one wrapper.",
            "current_positive_evidence": (
                f"{metrics['faithful_baseline_trials']} matched Qwen3.8-27B-long32k faithful-baseline trials; "
                "Qwen3.8-27B, Mistral-Small-3.2-24B, Codex GPT-5.5, and GovKernel appear in the current spine."
            ),
            "scale_target": "Add one additional open model and one high-capability terminal agent after compiler freeze.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Run Gemma or Mistral held-out slices plus Codex or Claude terminal baselines if budget allows.",
        },
        {
            "target_id": "S5_FAITHFUL_BASELINE_LADDER",
            "story_axis": "Baselines attack the claim; ablations explain the mechanism.",
            "current_positive_evidence": (
                f"{comparison_summary['faithful_baseline_rows']} faithful baseline row, "
                f"{metrics['faithful_baseline_trials']} trials, mean reward {metrics['faithful_baseline_mean_reward']:.1f}."
            ),
            "scale_target": "Add faithful external-agent baselines for each scaled benchmark family.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Keep baseline configs faithful; do not relabel mechanism cuts as external baselines.",
        },
        {
            "target_id": "S6_MECHANISM_ABLATION_COMPLETION",
            "story_axis": "Ablations are our controlled cuts through the institution.",
            "current_positive_evidence": (
                f"{comparison_summary['mechanism_ablation_rows']} planned mechanism ablation rows; "
                f"{comparison_summary['completed_mechanism_ablation_rows']} already have seed evidence."
            ),
            "scale_target": "Complete executable ablations for authority, obligation, side-effect, read, and amendment cuts.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Run ablations after the full LTA condition and task selection are frozen.",
        },
        {
            "target_id": "S7_FREEZE_AND_STATISTICS",
            "story_axis": "The story earns trust by freezing the camera before the final sweep.",
            "current_positive_evidence": (
                f"{story_gate['summary']['passed_checks']}/{story_gate['summary']['total_checks']} story-gate checks pass; "
                f"{comparison_summary['baseline_ablation_overlap']} baseline/ablation overlaps."
            ),
            "scale_target": "Freeze task selection, claim boundaries, and metrics before the final positive-mass run.",
            "inclusion_rule": "Include only tasks that sharpen the proposal/evidence/authority/commit boundary.",
            "next_run": "Report confidence intervals, paired tests, and pass-to-fail regression after final runs.",
        },
    ]

    summary = {
        "scale_target_rows": len(rows),
        "benchmarks_targeted": 3,
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
        writer = csv.DictWriter(handle, fieldnames=SCALE_PLAN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTASubmissionScaleRows": summary["scale_target_rows"],
        "LTASubmissionScaleBenchmarks": summary["benchmarks_targeted"],
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

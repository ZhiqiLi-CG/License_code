from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .evidence_portfolio import build_evidence_portfolio
from .story_claims import build_story_claims
from .submission_scale_plan import build_submission_scale_plan


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
    scale_plan = build_submission_scale_plan(root)

    metrics = claims["headline_metrics"]
    portfolio_summary = portfolio["summary"]
    comparison_summary = comparison["summary"]
    scale_summary = scale_plan["summary"]

    rows = [
        {
            "panel_id": "H1_BREADTH",
            "paper_role": "main_positive_evidence",
            "story_question": "Does the authority story span more than one substrate?",
            "result_sentence": (
                f"The evidence spine spans {portfolio_summary['benchmark_count']} benchmark families, "
                f"{portfolio_summary['state_substrate_count']} state substrates, and "
                f"{portfolio_summary['actor_backbone_count']} actor backbones."
            ),
            "why_it_matters": (
                "The same proposal/evidence/authority/commit boundary appears in business records, "
                "terminal state, and workflow artifacts."
            ),
            "source_data": "evidence_portfolio.csv",
        },
        {
            "panel_id": "H2_CLEAN_POSITIVE_MASS",
            "paper_role": "main_positive_evidence",
            "story_question": "Is the positive evidence a stable block rather than one lucky case?",
            "result_sentence": (
                f"GovKernel-backed clean anchors achieve {portfolio_summary['clean_positive_passes']}/"
                f"{portfolio_summary['clean_positive_trials']} official passes with zero errors."
            ),
            "why_it_matters": (
                "The paper can lead with verifier-backed positive mass instead of a defensive case report."
            ),
            "source_data": "stage2_reliability.csv | evidence_portfolio.csv",
        },
        {
            "panel_id": "H3_FAITHFUL_BASELINE_COUNTERPOINT",
            "paper_role": "faithful_baseline_counterpoint",
            "story_question": "Does a stronger ordinary task agent solve the same authority boundary?",
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
            "panel_id": "H4_TAU2_AUTHORITY_MINING",
            "paper_role": "main_positive_evidence",
            "story_question": "Are authority failures visible beyond hand-picked examples?",
            "result_sentence": (
                f"Mining {metrics['tau2_result_files']} local tau2 result files finds "
                f"{metrics['tau2_read_correct_write_wrong_proxy']} cancellation commits where the "
                "reservation read was matched but the policy-invalid write failed database or total reward."
            ),
            "why_it_matters": (
                "The result supports the core intuition: proposal evidence is present, but commit "
                "authority is missing."
            ),
            "source_data": "tau2_authority_mining.csv",
        },
        {
            "panel_id": "H5_AMENDMENT_TRANSFER",
            "paper_role": "main_positive_evidence",
            "story_question": "Does a failure-derived amendment transfer across benchmarks?",
            "result_sentence": (
                f"The amendment ledger records {metrics['transfer_failure_to_pass']} failure-to-pass "
                f"repairs across {metrics['transfer_cases']} audited cases with "
                f"{metrics['transfer_pass_to_failure']} pass-to-failure regressions."
            ),
            "why_it_matters": (
                "The paper's self-improvement object is the authority compiler amendment, not a "
                "single-task wrapper."
            ),
            "source_data": "transfer_ledger.csv | stage1_cases.csv",
        },
        {
            "panel_id": "H6_SUBMISSION_SCALE_PATH",
            "paper_role": "scale_path",
            "story_question": "What must be scaled before final top-conference claim freeze?",
            "result_sentence": (
                f"The submission plan contains {scale_summary['scale_target_rows']} frozen scale targets "
                "covering tau2 write families, Terminal-Bench authority pilots, SkillFlow obligations, "
                "model breadth, faithful baselines, mechanism cuts, and statistics."
            ),
            "why_it_matters": (
                "The next experiments are selected by the story boundary rather than by blind benchmark piling."
            ),
            "source_data": "submission_scale_plan.csv",
        },
    ]

    summary = {
        "headline_rows": len(rows),
        "main_positive_rows": sum(1 for row in rows if row["paper_role"] == "main_positive_evidence"),
        "faithful_counterpoint_rows": sum(
            1 for row in rows if row["paper_role"] == "faithful_baseline_counterpoint"
        ),
        "scale_path_rows": sum(1 for row in rows if row["paper_role"] == "scale_path"),
        "benchmarks": portfolio_summary["benchmark_count"],
        "state_substrates": portfolio_summary["state_substrate_count"],
        "actor_backbones": portfolio_summary["actor_backbone_count"],
        "clean_positive_passes": portfolio_summary["clean_positive_passes"],
        "clean_positive_trials": portfolio_summary["clean_positive_trials"],
        "faithful_baseline_passes": comparison_summary["faithful_baseline_passes"],
        "faithful_baseline_trials": comparison_summary["faithful_baseline_trials"],
        "tau2_read_correct_write_wrong_proxy": metrics["tau2_read_correct_write_wrong_proxy"],
        "submission_scale_rows": scale_summary["scale_target_rows"],
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
        "LTAHeadlineFaithfulCounterpointRows": summary["faithful_counterpoint_rows"],
        "LTAHeadlineScalePathRows": summary["scale_path_rows"],
        "LTAHeadlineCleanPositivePasses": summary["clean_positive_passes"],
        "LTAHeadlineCleanPositiveTrials": summary["clean_positive_trials"],
        "LTAHeadlineFaithfulBaselinePasses": summary["faithful_baseline_passes"],
        "LTAHeadlineFaithfulBaselineTrials": summary["faithful_baseline_trials"],
        "LTAHeadlineTauTwoRCWW": summary["tau2_read_correct_write_wrong_proxy"],
        "LTAHeadlineSubmissionScaleRows": summary["submission_scale_rows"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/headline_result_panel.py.",
        "% Regenerate with License_code/scripts/export_headline_result_panel.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

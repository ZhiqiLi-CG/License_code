from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .tau2_matched_boundary_export import build_tau2_matched_boundary_export


DECOMPOSITION_FIELDS = [
    "decomposition_id",
    "benchmark",
    "task_family",
    "evidence_type",
    "actor_backbone",
    "comparison_kind",
    "n_trials",
    "proposal_success_definition",
    "proposal_successes",
    "effect_successes_without_boundary",
    "proposal_to_effect_gaps",
    "effect_successes_with_boundary",
    "source_ref",
    "counts_as_planned",
    "notes",
]


def build_proposal_effect_decomposition(
    project_root: str | Path = Path("/data/zhiqi/License"),
) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"

    stage1_by_id = {row["case_id"]: row for row in _read_csv(data_dir / "stage1_cases.csv")}
    tau2_metrics = {row["metric"]: row["value"] for row in _read_csv(data_dir / "tau2_commit_mining.csv")}
    tau2_matched = build_tau2_matched_boundary_export(root)

    rows = [
        _tau2_distribution_row(root, tau2_metrics),
        _stage1_source_row(
            stage1_by_id["T2-A1"],
            decomposition_id="TAU2_A1_QWEN_SINGLE",
            evidence_type="paired_intervention_single",
            proposal_success_definition="reservation and user-intent evidence are present before the invalid business write",
        ),
        _tau2_matched_row(tau2_matched),
        _stage1_source_row(
            stage1_by_id["TB-SAN"],
            decomposition_id="TB_SAN_CODEX_SCOPE",
            evidence_type="diagnostic_to_official_slice",
            proposal_success_definition="the local secret replacement objective is solved before repository state is over-mutated",
        ),
        _stage1_source_row(
            stage1_by_id["TB-WAL"],
            decomposition_id="TB_WAL_QWEN_PRESERVE",
            evidence_type="diagnostic_to_official_slice",
            proposal_success_definition="database and WAL recovery evidence are observed before the recovery artifact is missing",
        ),
        _stage1_source_row(
            stage1_by_id["SF-INV"],
            decomposition_id="SF_INVOICE_QWEN_PROMPT",
            evidence_type="same_backbone_runtime_comparison",
            proposal_success_definition="invoice OCR evidence is exposed before the workbook remains absent",
        ),
    ]
    summary = _summarize(rows)
    return {"summary": summary, "rows": rows}


def write_proposal_effect_decomposition(
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
        else root / "artifacts" / "paper_results" / "proposal_effect_decomposition_20260831.json"
    )

    report = build_proposal_effect_decomposition(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    csv_path = paper_data_dir / "proposal_effect_decomposition.csv"
    latex_numbers = paper_sections_dir / "generated_proposal_effect_numbers.tex"
    _write_csv(csv_path, report["rows"])
    latex_numbers.write_text(_latex_numbers(report["summary"]), encoding="utf-8")

    report["outputs"] = {
        "summary_json": str(summary_path),
        "csv": str(csv_path),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _tau2_distribution_row(root: Path, metrics: dict[str, str]) -> dict[str, str]:
    gaps = int(metrics["read_correct_write_wrong_proxy"])
    return {
        "decomposition_id": "TAU2_MINED_CANCEL_RCWW",
        "benchmark": "tau2-Bench",
        "task_family": "airline cancellation commits",
        "evidence_type": "distributional_mining",
        "actor_backbone": "Qwen3.8-27B | Mistral-Small-3.2-24B",
        "comparison_kind": "real_trace_mining",
        "n_trials": metrics["cancel_decisions"],
        "proposal_success_definition": "reservation-state evidence is present before a policy-invalid cancellation commit",
        "proposal_successes": str(gaps),
        "effect_successes_without_boundary": "0",
        "proposal_to_effect_gaps": str(gaps),
        "effect_successes_with_boundary": "",
        "source_ref": str(root / "artifacts" / "stage2" / "tau2_commit_mining_20260830.json"),
        "counts_as_planned": "no",
        "notes": (
            f"{metrics['vetoes_with_matched_reservation_read']} of {gaps} also have a matched official "
            "reservation-read check; all counted rows have DB failure."
        ),
    }


def _stage1_source_row(
    row: dict[str, str],
    *,
    decomposition_id: str,
    evidence_type: str,
    proposal_success_definition: str,
) -> dict[str, str]:
    proposal_successes = 1
    effect_without = int(float(row["baseline_reward"]))
    effect_with = int(float(row["lta_reward"]))
    gap = proposal_successes - effect_without
    return {
        "decomposition_id": decomposition_id,
        "benchmark": row["benchmark"],
        "task_family": row["task"],
        "evidence_type": evidence_type,
        "actor_backbone": row["baseline_agent"],
        "comparison_kind": row["comparison_type"],
        "n_trials": "1",
        "proposal_success_definition": proposal_success_definition,
        "proposal_successes": str(proposal_successes),
        "effect_successes_without_boundary": str(effect_without),
        "proposal_to_effect_gaps": str(gap),
        "effect_successes_with_boundary": str(effect_with),
        "source_ref": "stage1_cases.csv",
        "counts_as_planned": "no",
        "notes": row["notes"],
    }


def _tau2_matched_row(report: dict[str, Any]) -> dict[str, str]:
    summary = report["summary"]
    proposal_successes = int(summary["baseline_read_correct_write_wrong"])
    baseline_effect = int(round(float(summary["baseline_mean_reward"]) * int(summary["baseline_trials"])))
    boundary_effect = int(round(float(summary["boundary_mean_reward"]) * int(summary["boundary_trials"])))
    return {
        "decomposition_id": "TAU2_A48_MISTRAL_MATCHED_K20",
        "benchmark": "tau2-Bench",
        "task_family": "airline task 48",
        "evidence_type": "matched_actor_k20",
        "actor_backbone": "Mistral-Small-3.2-24B-Instruct-2506",
        "comparison_kind": "same actor, same scripted user, boundary changed",
        "n_trials": str(summary["baseline_trials"]),
        "proposal_success_definition": "the reservation is read correctly before an unwarranted cancellation commit",
        "proposal_successes": str(proposal_successes),
        "effect_successes_without_boundary": str(baseline_effect),
        "proposal_to_effect_gaps": str(proposal_successes - baseline_effect),
        "effect_successes_with_boundary": str(boundary_effect),
        "source_ref": str(summary["source_path"]),
        "counts_as_planned": "no",
        "notes": (
            f"{summary['complete_pairs']} matched seeds; boundary vetoes "
            f"{summary['boundary_vetoes']} unready cancellations with "
            f"{summary['boundary_regressions']} regressions."
        ),
    }


def _summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    gap_rows = [row for row in rows if int(row["proposal_to_effect_gaps"]) > 0]
    source_gap_rows = [row for row in gap_rows if row["evidence_type"] != "distributional_mining"]
    distributional_rows = [row for row in gap_rows if row["evidence_type"] == "distributional_mining"]
    proposal_successes = sum(int(row["proposal_successes"]) for row in gap_rows)
    gap_observations = sum(int(row["proposal_to_effect_gaps"]) for row in gap_rows)
    return {
        "rows": len(rows),
        "benchmark_count": len({row["benchmark"] for row in rows}),
        "planned_rows": sum(1 for row in rows if row["counts_as_planned"] == "yes"),
        "gap_observations": gap_observations,
        "gap_source_observations": sum(int(row["proposal_to_effect_gaps"]) for row in source_gap_rows),
        "gap_distributional_observations": sum(
            int(row["proposal_to_effect_gaps"]) for row in distributional_rows
        ),
        "baseline_effect_successes_on_gap_rows": sum(
            int(row["effect_successes_without_boundary"]) for row in gap_rows
        ),
        "boundary_effect_successes_on_source_gap_rows": sum(
            int(row["effect_successes_with_boundary"] or 0) for row in source_gap_rows
        ),
        "gap_rate_on_gap_rows": gap_observations / proposal_successes if proposal_successes else 0.0,
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DECOMPOSITION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAProposalEffectRows": summary["rows"],
        "LTAProposalEffectBenchmarks": summary["benchmark_count"],
        "LTAProposalEffectGapObservations": summary["gap_observations"],
        "LTAProposalEffectSourceGaps": summary["gap_source_observations"],
        "LTAProposalEffectDistributionalGaps": summary["gap_distributional_observations"],
        "LTAProposalEffectBaselineEffectSuccesses": summary["baseline_effect_successes_on_gap_rows"],
        "LTAProposalEffectBoundarySourceSuccesses": summary[
            "boundary_effect_successes_on_source_gap_rows"
        ],
        "LTAProposalEffectGapRate": f"{summary['gap_rate_on_gap_rows']:.3f}",
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/proposal_effect_decomposition.py.",
        "% Regenerate with License_code/scripts/export_proposal_effect_decomposition.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

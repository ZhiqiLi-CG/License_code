from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .boundary_patch_meta_agent import build_meta_agent_patch_report, default_response_path


LINEAGE_FIELDS = [
    "refinement_id",
    "generation",
    "synthesis_method",
    "trigger_signature",
    "contract_diff",
    "source_cases",
    "validation_cases",
    "heldout_cases",
    "source_failure_to_pass",
    "heldout_clean_trials",
    "pass_to_failure_regressions",
    "admission_decision",
    "comparison_class",
    "baseline_boundary",
]


def build_recursive_amendment_lineage(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"
    stage1_rows = _read_csv(data_dir / "stage1_cases.csv")
    meta_report = build_meta_agent_patch_report(
        root,
        response_path=default_response_path(root),
    )
    rows = [_lineage_row_from_meta_patch(row) for row in meta_report["rows"]]

    summary = _summarize(rows, stage1_rows)
    return {"summary": summary, "rows": rows}


def _lineage_row_from_meta_patch(row: dict[str, str]) -> dict[str, str]:
    return {
        "refinement_id": row["patch_id"],
        "generation": _generation_for_field(row["boundary_field"]),
        "synthesis_method": "frozen_meta_agent_proposal",
        "trigger_signature": row["failure_type"],
        "contract_diff": row["proposed_change"],
        "source_cases": row["case_id"],
        "validation_cases": "",
        "heldout_cases": _join(sorted(_heldout_cases_for_meta_row(row))),
        "source_failure_to_pass": row["source_failure_to_pass"],
        "heldout_clean_trials": row["heldout_clean_trials"],
        "pass_to_failure_regressions": row["pass_to_failure_regressions"],
        "admission_decision": row["admission_decision"],
        "comparison_class": "boundary_update",
        "baseline_boundary": "not_baseline: frozen meta-agent patch proposal; task-local hand guards are mechanism cuts",
    }


def _generation_for_field(field: str) -> str:
    if field == "ready":
        return "1"
    if field in {"scope", "preserve"}:
        return "2"
    if field == "done":
        return "3"
    return "0"


def _heldout_cases_for_meta_row(row: dict[str, str]) -> set[str]:
    if row["boundary_field"] == "scope":
        return {"TB-SAN-K5"}
    if row["boundary_field"] == "preserve":
        if row["failure_type"] == "Destructive observation":
            return {"TB-SQLITE-K5", "TB-WAL-K5"}
        return {"TB-SAN-K5"}
    if row["boundary_field"] == "done":
        return {"SF-INV-MAT-K5", "SF-TRAVEL-MAT-K5", "TB-LOG-K5"}
    return set()


def write_recursive_amendment_lineage(
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
        else root / "artifacts" / "paper_results" / "contract_refinement_lineage_20260831.json"
    )

    lineage = build_recursive_amendment_lineage(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lineage_csv = paper_data_dir / "contract_refinement_lineage.csv"
    latex_numbers = paper_sections_dir / "generated_recursive_numbers.tex"
    _write_lineage_csv(lineage_csv, lineage["rows"])
    latex_numbers.write_text(_latex_numbers(lineage["summary"]), encoding="utf-8")

    lineage["outputs"] = {
        "summary_json": str(summary_path),
        "lineage_csv": str(lineage_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(lineage, indent=2), encoding="utf-8")
    return lineage


def _summarize(rows: list[dict[str, str]], stage1_rows: list[dict[str, str]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["admission_decision"] == "accept"]
    by_generation: dict[str, int] = defaultdict(int)
    for row in accepted:
        by_generation[row["generation"]] += int(row["source_failure_to_pass"])
    source_benchmarks = {
        row["benchmark"]
        for row in stage1_rows
        if row["baseline_reward"] == "0" and row["lta_reward"] == "1"
    }
    generation_gains = list(by_generation.values())
    mean_gain = sum(generation_gains) / len(generation_gains) if generation_gains else 0.0
    return {
        "candidate_amendments": len(rows),
        "accepted_amendments": len(accepted),
        "compiler_generations": len({row["generation"] for row in rows}),
        "source_benchmark_families": len(source_benchmarks),
        "source_failure_to_pass": sum(int(row["source_failure_to_pass"]) for row in accepted),
        "heldout_clean_trials": sum(int(row["heldout_clean_trials"]) for row in accepted),
        "pass_to_failure_regressions": sum(int(row["pass_to_failure_regressions"]) for row in accepted),
        "mean_generation_gain": mean_gain,
    }


def _write_lineage_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LINEAGE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTARecursiveCandidateAmendments": summary["candidate_amendments"],
        "LTARecursiveAcceptedAmendments": summary["accepted_amendments"],
        "LTARecursiveCompilerGenerations": summary["compiler_generations"],
        "LTARecursiveSourceBenchmarks": summary["source_benchmark_families"],
        "LTARecursiveSourceFtoP": summary["source_failure_to_pass"],
        "LTARecursiveHeldoutTrials": summary["heldout_clean_trials"],
        "LTARecursivePtoF": summary["pass_to_failure_regressions"],
        "LTARecursiveMeanGenerationGain": f"{summary['mean_generation_gain']:.2f}",
    }
    lines = [
        "% Auto-generated by License_code/scripts/export_contract_refinement_lineage.py.",
        "% Regenerate with License_code/scripts/export_contract_refinement_lineage.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _join(values: list[str]) -> str:
    return " | ".join(values)

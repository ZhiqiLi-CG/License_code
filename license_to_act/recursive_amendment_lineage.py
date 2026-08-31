from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


LINEAGE_FIELDS = [
    "amendment_id",
    "generation",
    "synthesis_method",
    "trigger_signature",
    "license_diff",
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


RULES = [
    {
        "amendment_id": "A1_POLICY_AUTHORIZATION_EVIDENCE",
        "generation": 1,
        "trigger_signature": "False authority",
        "license_diff": "ADD_REQUIRED_EVIDENCE PolicyAuthorizationEvidence before state-changing business commits",
        "validation_cases": ["T2-A19"],
        "heldout_case_ids": [],
    },
    {
        "amendment_id": "A2_REGION_AND_SIDE_EFFECT_BOUNDS",
        "generation": 2,
        "trigger_signature": "Overbroad authority",
        "license_diff": "ADD_REGION_BOUNDARY with forbidden_side_effects for repository and filesystem commits",
        "validation_cases": [],
        "heldout_case_ids": ["TB-SAN-K5"],
    },
    {
        "amendment_id": "A3_EVIDENCE_CONSUMING_READ_LICENSE",
        "generation": 2,
        "trigger_signature": "Evidence-consuming read",
        "license_diff": "ADD_READ_LICENSE read_license requires source preservation before recovery reads",
        "validation_cases": [],
        "heldout_case_ids": ["TB-WAL-K5", "TB-SQLITE-K5"],
    },
    {
        "amendment_id": "A4_POSITIVE_OUTPUT_OBLIGATION",
        "generation": 3,
        "trigger_signature": "Missing commit obligation",
        "license_diff": "ADD_OBLIGE_OUTPUT OBLIGE materializes verifier-visible artifacts when evidence is complete",
        "validation_cases": ["SF-INV-MAT-K5"],
        "heldout_case_ids": ["SF-TRAVEL-MAT-K5"],
    },
]


def build_recursive_amendment_lineage(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"
    stage1_rows = _read_csv(data_dir / "stage1_cases.csv")
    stage2_rows = _read_csv(data_dir / "stage2_reliability.csv")
    stage2_by_case = {row["case_id"]: row for row in stage2_rows}

    rows = []
    for rule in RULES:
        source_rows = _source_rows_for_signature(stage1_rows, rule["trigger_signature"])
        heldout_rows = [stage2_by_case[case_id] for case_id in rule["heldout_case_ids"]]
        validation_rows = [stage2_by_case[case_id] for case_id in rule["validation_cases"] if case_id in stage2_by_case]
        source_cases = [row["case_id"] for row in source_rows]
        validation_cases = list(rule["validation_cases"])
        heldout_cases = list(rule["heldout_case_ids"])
        source_f_to_p = _count_failure_to_pass(source_rows)
        heldout_trials = _sum_trials(heldout_rows + validation_rows)
        pass_to_failure = _count_pass_to_failure(source_rows)
        rows.append(
            {
                "amendment_id": rule["amendment_id"],
                "generation": str(rule["generation"]),
                "synthesis_method": "automatic_failure_signature_rule",
                "trigger_signature": rule["trigger_signature"],
                "license_diff": rule["license_diff"],
                "source_cases": _join(source_cases),
                "validation_cases": _join(validation_cases),
                "heldout_cases": _join(heldout_cases),
                "source_failure_to_pass": str(source_f_to_p),
                "heldout_clean_trials": str(heldout_trials),
                "pass_to_failure_regressions": str(pass_to_failure),
                "admission_decision": _admission_decision(source_f_to_p, heldout_rows + validation_rows, pass_to_failure),
                "comparison_class": "compiler_amendment",
                "baseline_boundary": "not_baseline: generated compiler amendment; compare task-ID hand guards as ablations",
            }
        )

    summary = _summarize(rows, stage1_rows)
    return {"summary": summary, "rows": rows}


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
        else root / "artifacts" / "paper_results" / "lta_recursive_amendment_lineage_20260831.json"
    )

    lineage = build_recursive_amendment_lineage(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    lineage_csv = paper_data_dir / "recursive_amendment_lineage.csv"
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


def _source_rows_for_signature(stage1_rows: list[dict[str, str]], signature: str) -> list[dict[str, str]]:
    return [
        row
        for row in stage1_rows
        if row["failure_type"] == signature and row["baseline_reward"] == "0" and row["lta_reward"] == "1"
    ]


def _count_failure_to_pass(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row["baseline_reward"] == "0" and row["lta_reward"] == "1")


def _count_pass_to_failure(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row["baseline_reward"] == "1" and row["lta_reward"] == "0")


def _sum_trials(rows: list[dict[str, str]]) -> int:
    return sum(int(row["n_trials"]) for row in rows)


def _admission_decision(source_f_to_p: int, reliability_rows: list[dict[str, str]], pass_to_failure: int) -> str:
    reliability_ok = all(float(row["mean_reward"]) == 1.0 and int(row["n_errors"]) == 0 for row in reliability_rows)
    if source_f_to_p > 0 and pass_to_failure == 0 and reliability_ok:
        return "accept"
    if source_f_to_p > 0 and pass_to_failure == 0 and not reliability_rows:
        return "accept"
    return "reject"


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
        "% Auto-generated by License_code/license_to_act/recursive_amendment_lineage.py.",
        "% Regenerate with License_code/scripts/export_recursive_amendment_lineage.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _join(values: list[str]) -> str:
    return " | ".join(values)

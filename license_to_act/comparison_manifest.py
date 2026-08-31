from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


MANIFEST_FIELDS = [
    "comparison_id",
    "comparison_class",
    "paper_role",
    "condition",
    "tests",
    "evidence_status",
    "current_result",
    "source_data",
]


def build_comparison_manifest(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    stage2_rows = _read_csv(root / "License_paper" / "data" / "stage2_reliability.csv")
    clean_rows = [row for row in stage2_rows if row["paper_use"] == "clean_reliability_anchor"]
    faithful_rows = [row for row in stage2_rows if row["paper_use"] == "faithful_baseline"]
    stress_rows = [row for row in stage2_rows if row["paper_use"] == "integration_stress"]

    clean_trials = _sum_int(clean_rows, "n_trials")
    clean_passes = _weighted_passes(clean_rows)
    faithful_trials = _sum_int(faithful_rows, "n_trials")
    faithful_passes = _weighted_passes(faithful_rows)
    stress_trials = _sum_int(stress_rows, "n_trials")
    stress_passes = _weighted_passes(stress_rows)

    rows = [
        {
            "comparison_id": "M1_FULL_STATETX_CLEAN_ANCHORS",
            "comparison_class": "method_condition",
            "paper_role": "main_positive",
            "condition": "Full StateTx with executable Commit Controller",
            "tests": "Does transactional execution produce stable verifier-backed durable state changes?",
            "evidence_status": "completed",
            "current_result": f"{clean_passes}/{clean_trials} official passes",
            "source_data": "stage2_reliability.csv",
        },
        {
            "comparison_id": "B1_QWEN32K_MINISWE_MATCHED",
            "comparison_class": "faithful_baseline",
            "paper_role": "main_counterpoint",
            "condition": "Qwen3.8-27B-long32k with mini-swe-agent on matched anchors",
            "tests": "Does a stronger long-context ordinary task agent solve the same commit boundary?",
            "evidence_status": "completed",
            "current_result": f"{faithful_passes}/{faithful_trials} official passes",
            "source_data": "stage2_reliability.csv",
        },
        {
            "comparison_id": "A1_PROMPT_ONLY_TEXT_CONTRACT",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_evidence",
            "condition": "Natural-language transaction instructions without runtime commit control",
            "tests": "Is describing the commit protocol in the prompt equivalent to owning the durability boundary?",
            "evidence_status": "seed_evidence",
            "current_result": "SkillFlow prompt-only run leaves the required workbook absent",
            "source_data": "stage1_cases.csv | appendix evidence",
        },
        {
            "comparison_id": "A2_NO_COMPLETION_TRIGGER",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_evidence",
            "condition": "StateTx without completion triggers for missing artifacts",
            "tests": "Does evidence alone materialize verifier-visible workflow outputs?",
            "evidence_status": "seed_evidence",
            "current_result": "Open-model invoice and travel-claim traces observe OCR evidence but score 0/2",
            "source_data": "stage2_reliability.csv | appendix evidence",
        },
        {
            "comparison_id": "A3_NO_PRESERVE_CONSTRAINTS",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_evidence",
            "condition": "StateTx without preserve constraints over collateral state",
            "tests": "Can local success overcommit by mutating state outside the intended write scope?",
            "evidence_status": "seed_evidence",
            "current_result": "Codex sanitization removes secrets but rewrites Git identity and scores 0",
            "source_data": "diagnostic_cases.csv | appendix evidence",
        },
        {
            "comparison_id": "A4_NO_PRESERVING_READ_CONTRACT",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_evidence",
            "condition": "StateTx without preservation contracts for fragile reads",
            "tests": "Do reads need transaction rules when observation can consume the recovery substrate?",
            "evidence_status": "seed_evidence",
            "current_result": "Qwen WAL run loses the recovery substrate; preserving-read contract reaches 5/5 official passes",
            "source_data": "stage1_cases.csv | stage2_reliability.csv",
        },
        {
            "comparison_id": "A5_NO_CONTRACT_REFINEMENT",
            "comparison_class": "mechanism_ablation",
            "paper_role": "mechanism_evidence",
            "condition": "Static State Contracts without failure-driven refinement",
            "tests": "Do gains remain local when the commit contract cannot be refined from failures?",
            "evidence_status": "seed_evidence",
            "current_result": "Generated lineage accepts 4/4 contract refinements over three generations",
            "source_data": "contract_refinement_lineage.csv",
        },
        {
            "comparison_id": "S1_QWEN_COMMIT_CONTROLLER_INTEGRATION",
            "comparison_class": "integration_stress",
            "paper_role": "supporting_stress",
            "condition": "Qwen3.8-27B plus Commit Controller under the 8192-token endpoint",
            "tests": "Can a real model feed staged evidence into the transaction layer under endpoint pressure?",
            "evidence_status": "completed",
            "current_result": f"{stress_passes}/{stress_trials} official passes",
            "source_data": "stage2_reliability.csv",
        },
    ]
    summary = _summarize(rows, faithful_trials, faithful_passes)
    return {"summary": summary, "rows": rows}


def write_comparison_manifest(
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
        else root / "artifacts" / "paper_results" / "lta_comparison_manifest_20260831.json"
    )

    manifest = build_comparison_manifest(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_csv = paper_data_dir / "comparison_manifest.csv"
    latex_numbers = paper_sections_dir / "generated_comparison_numbers.tex"
    _write_manifest_csv(manifest_csv, manifest["rows"])
    latex_numbers.write_text(_latex_numbers(manifest["summary"]), encoding="utf-8")

    manifest["outputs"] = {
        "summary_json": str(summary_path),
        "manifest_csv": str(manifest_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _summarize(rows: list[dict[str, str]], faithful_trials: int, faithful_passes: int) -> dict[str, Any]:
    method_rows = [row for row in rows if row["comparison_class"] == "method_condition"]
    baseline_rows = [row for row in rows if row["comparison_class"] == "faithful_baseline"]
    ablation_rows = [row for row in rows if row["comparison_class"] == "mechanism_ablation"]
    completed_ablation_rows = [row for row in ablation_rows if row["evidence_status"] == "seed_evidence"]
    stress_rows = [row for row in rows if row["comparison_class"] == "integration_stress"]
    overlap = sum(1 for row in rows if _mixes_baseline_and_ablation(row))
    return {
        "comparison_rows": len(rows),
        "method_condition_rows": len(method_rows),
        "faithful_baseline_rows": len(baseline_rows),
        "faithful_baseline_trials": faithful_trials,
        "faithful_baseline_passes": faithful_passes,
        "mechanism_ablation_rows": len(ablation_rows),
        "completed_mechanism_ablation_rows": len(completed_ablation_rows),
        "integration_stress_rows": len(stress_rows),
        "baseline_ablation_overlap": overlap,
}


def _mixes_baseline_and_ablation(row: dict[str, str]) -> bool:
    joined = " ".join(row.values()).lower()
    if row["comparison_class"] == "faithful_baseline":
        return "ablation" in joined
    if row["comparison_class"] == "mechanism_ablation":
        return "baseline" in row["paper_role"].lower()
    return False


def _write_manifest_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAComparisonManifestRows": summary["comparison_rows"],
        "LTAFaithfulBaselineRows": summary["faithful_baseline_rows"],
        "LTAMechanismAblationRows": summary["mechanism_ablation_rows"],
        "LTACompletedMechanismAblationRows": summary["completed_mechanism_ablation_rows"],
        "LTABaselineAblationOverlap": summary["baseline_ablation_overlap"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/comparison_manifest.py.",
        "% Regenerate with License_code/scripts/export_comparison_manifest.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sum_int(rows: list[dict[str, str]], field: str) -> int:
    return sum(int(row[field]) for row in rows)


def _weighted_passes(rows: list[dict[str, str]]) -> int:
    return int(round(sum(int(row["n_trials"]) * float(row["mean_reward"]) for row in rows)))

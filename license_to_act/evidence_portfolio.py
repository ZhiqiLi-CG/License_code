from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PORTFOLIO_FIELDS = [
    "portfolio_id",
    "story_role",
    "benchmarks",
    "state_substrates",
    "actor_backbones",
    "comparison_kind",
    "positive_result",
    "paper_use",
    "source_data",
]


def build_evidence_portfolio(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"
    stage1_rows = _read_csv(data_dir / "stage1_cases.csv")
    stage2_rows = _read_csv(data_dir / "stage2_reliability.csv")
    transfer_rows = _read_csv(data_dir / "transfer_ledger.csv")
    tau2_rows = _read_csv(data_dir / "tau2_authority_mining.csv")

    clean_rows = [row for row in stage2_rows if row["paper_use"] == "clean_reliability_anchor"]
    faithful_rows = [row for row in stage2_rows if row["paper_use"] == "faithful_baseline"]
    stress_rows = [row for row in stage2_rows if row["paper_use"] == "integration_stress"]
    tb_clean_rows = [row for row in clean_rows if row["benchmark"] == "Terminal-Bench 2.1"]
    sf_clean_rows = [row for row in clean_rows if row["benchmark"] == "SkillFlow"]

    tau2_metrics = {row["metric"]: _parse_number(row["value"]) for row in tau2_rows}
    benchmarks = sorted({row["benchmark"] for row in stage1_rows} | {row["benchmark"] for row in stage2_rows})
    actor_backbones = _actor_backbones(stage1_rows, stage2_rows)
    transfer_ftp = _sum_int(transfer_rows, "failure_to_pass")
    transfer_ptf = _sum_int(transfer_rows, "pass_to_failure")
    clean_trials = _sum_int(clean_rows, "n_trials")
    clean_passes = _weighted_passes(clean_rows)
    faithful_trials = _sum_int(faithful_rows, "n_trials")
    faithful_passes = _weighted_passes(faithful_rows)
    stress_trials = _sum_int(stress_rows, "n_trials")
    stress_passes = _weighted_passes(stress_rows)

    rows = [
        {
            "portfolio_id": "P1_STAGE1_TRANSFER",
            "story_role": "same amendment moves across state substrates",
            "benchmarks": "tau2-Bench | Terminal-Bench 2.1 | SkillFlow",
            "state_substrates": "business records | terminal state | workflow artifacts",
            "actor_backbones": "Qwen3.8-27B | Mistral-Small-3.2-24B | Codex GPT-5.5",
            "comparison_kind": "paired_or_diagnostic_transfer",
            "positive_result": f"{transfer_ftp} failure-to-pass, {transfer_ptf} pass-to-failure",
            "paper_use": "main_spine",
            "source_data": "stage1_cases.csv | transfer_ledger.csv",
        },
        {
            "portfolio_id": "P2_TAU2_MINING",
            "story_role": "authority failures are not missing-read failures",
            "benchmarks": "tau2-Bench",
            "state_substrates": "business records",
            "actor_backbones": "Qwen3.8-27B | Mistral-Small-3.2-24B",
            "comparison_kind": "distributional_mining",
            "positive_result": (
                f"{int(tau2_metrics['read_correct_write_wrong_proxy'])} read-correct/write-wrong "
                f"cancellation commits from {int(tau2_metrics['result_files'])} result files"
            ),
            "paper_use": "main_spine",
            "source_data": "tau2_authority_mining.csv",
        },
        {
            "portfolio_id": "P3_TB_OFFICIAL_RERUNS",
            "story_role": "executable authority is stable in terminal state",
            "benchmarks": "Terminal-Bench 2.1",
            "state_substrates": "terminal state",
            "actor_backbones": "GovKernel runtime",
            "comparison_kind": "official_k5_rerun",
            "positive_result": f"{_weighted_passes(tb_clean_rows)}/{_sum_int(tb_clean_rows, 'n_trials')} official passes",
            "paper_use": "main_spine",
            "source_data": "stage2_reliability.csv",
        },
        {
            "portfolio_id": "P4_SKILLFLOW_OFFICIAL_RERUNS",
            "story_role": "authority can compel missing workflow artifacts",
            "benchmarks": "SkillFlow",
            "state_substrates": "workflow artifacts",
            "actor_backbones": "GovKernel runtime",
            "comparison_kind": "official_k5_rerun",
            "positive_result": f"{_weighted_passes(sf_clean_rows)}/{_sum_int(sf_clean_rows, 'n_trials')} official passes",
            "paper_use": "main_spine",
            "source_data": "stage2_reliability.csv",
        },
        {
            "portfolio_id": "P5_LONGCTX_FAITHFUL_BASELINE",
            "story_role": "stronger long context alone does not solve the authority boundary",
            "benchmarks": "Terminal-Bench 2.1 | SkillFlow",
            "state_substrates": "terminal state | workflow artifacts",
            "actor_backbones": "Qwen3.8-27B-long32k",
            "comparison_kind": "faithful_baseline",
            "positive_result": f"{faithful_passes}/{faithful_trials} official passes",
            "paper_use": "main_counterpoint",
            "source_data": "stage2_reliability.csv",
        },
        {
            "portfolio_id": "P6_QWEN_GOVKERNEL_STRESS",
            "story_role": "model integration remains separate from clean executable authority",
            "benchmarks": "SkillFlow",
            "state_substrates": "workflow artifacts",
            "actor_backbones": "Qwen3.8-27B",
            "comparison_kind": "integration_stress",
            "positive_result": f"{stress_passes}/{stress_trials} official passes",
            "paper_use": "supporting_stress",
            "source_data": "stage2_reliability.csv",
        },
    ]

    summary = {
        "benchmark_count": len(benchmarks),
        "benchmarks": benchmarks,
        "state_substrate_count": 3,
        "state_substrates": ["business records", "terminal state", "workflow artifacts"],
        "actor_backbone_count": len(actor_backbones),
        "actor_backbones": actor_backbones,
        "stage1_failure_to_pass": transfer_ftp,
        "stage1_pass_to_failure": transfer_ptf,
        "clean_positive_trials": clean_trials,
        "clean_positive_passes": clean_passes,
        "faithful_baseline_trials": faithful_trials,
        "faithful_baseline_passes": faithful_passes,
        "tau2_read_correct_write_wrong_proxy": int(tau2_metrics["read_correct_write_wrong_proxy"]),
    }
    return {"summary": summary, "rows": rows}


def write_evidence_portfolio(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper/data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper/sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts/paper_results/lta_evidence_portfolio_20260831.json"
    )
    portfolio = build_evidence_portfolio(root)

    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    portfolio_csv = paper_data_dir / "evidence_portfolio.csv"
    latex_numbers = paper_sections_dir / "generated_portfolio_numbers.tex"
    _write_portfolio_csv(portfolio_csv, portfolio["rows"])
    latex_numbers.write_text(_latex_numbers(portfolio["summary"]), encoding="utf-8")

    portfolio["outputs"] = {
        "summary_json": str(summary_path),
        "portfolio_csv": str(portfolio_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(portfolio, indent=2), encoding="utf-8")
    return portfolio


def _actor_backbones(stage1_rows: list[dict[str, str]], stage2_rows: list[dict[str, str]]) -> list[str]:
    raw_names: set[str] = set()
    for row in stage1_rows:
        raw_names.add(row["baseline_agent"])
        raw_names.add(row["lta_agent"])
    for row in stage2_rows:
        raw_names.add(row["condition"])
    normalized = {_normalize_actor_name(name) for name in raw_names}
    normalized.discard("")
    normalized.discard("GovKernel runtime")
    return sorted(normalized)


def _normalize_actor_name(name: str) -> str:
    if "Codex GPT-5.5" in name:
        return "Codex GPT-5.5"
    if "Mistral" in name:
        return "Mistral-Small-3.2-24B"
    if "long32k" in name:
        return "Qwen3.8-27B-long32k"
    if "Qwen" in name:
        return "Qwen3.8-27B"
    if "LTA" in name or "GovKernel" in name:
        return "GovKernel runtime"
    return ""


def _write_portfolio_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PORTFOLIO_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAEvidenceBenchmarks": summary["benchmark_count"],
        "LTAEvidenceSubstrates": summary["state_substrate_count"],
        "LTAEvidenceBackbones": summary["actor_backbone_count"],
        "LTAEvidenceCleanPositivePasses": summary["clean_positive_passes"],
        "LTAEvidenceCleanPositiveTrials": summary["clean_positive_trials"],
        "LTAEvidenceFaithfulBaselinePasses": summary["faithful_baseline_passes"],
        "LTAEvidenceFaithfulBaselineTrials": summary["faithful_baseline_trials"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/evidence_portfolio.py.",
        "% Regenerate with License_code/scripts/export_evidence_portfolio.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _parse_number(value: str) -> int | float | str:
    try:
        numeric = float(value)
    except ValueError:
        return value
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _sum_int(rows: list[dict[str, str]], field: str) -> int:
    return sum(int(row[field]) for row in rows)


def _weighted_passes(rows: list[dict[str, str]]) -> int:
    return int(round(sum(int(row["n_trials"]) * float(row["mean_reward"]) for row in rows)))

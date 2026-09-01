from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .tau2_matched_experiment import summarize_tau2_matched_runs


TAU2_MATCHED_BOUNDARY_FIELDS = [
    "pair_id",
    "domain",
    "task_id",
    "seed",
    "actor_model",
    "user_mode",
    "condition",
    "reward",
    "cancel_tool_calls",
    "retail_exchange_tool_calls",
    "state_change_tool_calls",
    "read_correct_write_wrong",
    "boundary_vetoes",
    "boundary_allows",
    "paper_use",
    "source_path",
]


DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "tau2_matched_boundary"
    / "airline_task48_mistral_scripted_v2_summary.json"
)
RETAIL_TASK0_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "tau2_matched_boundary"
    / "retail_task0_qwen32k_scripted_completion_k5_summary.json"
)
RETAIL_TASK1_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "tau2_matched_boundary"
    / "retail_task1_qwen32k_scripted_scope_k5_summary.json"
)
DEFAULT_FIXTURES = (DEFAULT_FIXTURE, RETAIL_TASK0_FIXTURE, RETAIL_TASK1_FIXTURE)


def build_tau2_matched_boundary_export(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paths = [Path(source_path)] if source_path is not None else list(DEFAULT_FIXTURES)
    payloads = [(path, _read_json(path)) for path in paths]
    runs = [run for _, payload in payloads for run in payload["runs"]]
    rows = [_row_from_run(run, path) for path, payload in payloads for run in payload["runs"]]
    summary = summarize_tau2_matched_runs(runs)
    blocks = _block_summaries(runs, rows)
    summary.update(
        {
            "source_path": str(paths[0]),
            "source_paths": [str(path) for path in paths],
            "blocks": len(blocks),
            "block_summaries": blocks,
            "project_root": str(root),
            "domains": len({row["domain"] for row in rows}),
            "actor_models": len({row["actor_model"] for row in rows}),
        }
    )
    return {"summary": summary, "blocks": blocks, "rows": rows}


def compact_tau2_matched_report(
    source_path: str | Path,
    *,
    domain: str,
    actor_model: str,
    user_mode: str,
    paper_use: str,
    expected_complete_pairs: int | None = None,
) -> dict[str, Any]:
    """Convert a full tau2 live report into a small paper-facing fixture."""

    path = Path(source_path)
    payload = _read_json(path)
    runs = [
        _compact_run(
            run,
            domain=domain,
            actor_model=actor_model,
            user_mode=user_mode,
            paper_use=paper_use,
        )
        for run in payload["runs"]
    ]
    summary = summarize_tau2_matched_runs(runs)
    if expected_complete_pairs is not None and summary["complete_pairs"] != expected_complete_pairs:
        raise ValueError(
            f"expected {expected_complete_pairs} complete pairs, found {summary['complete_pairs']}"
        )
    return {
        "source_full_report": str(path),
        "notes": (
            "Compact export of a real matched tau2 run. The full local report "
            "contains official tau2 messages and reward_info; this file keeps "
            "only fields needed to regenerate the paper table and generated numbers."
        ),
        "summary": summary,
        "runs": runs,
    }


def write_tau2_matched_boundary_export(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "tau2_matched_boundary_20260831.json"
    )

    report = build_tau2_matched_boundary_export(root, source_path=source_path)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    csv_path = paper_data_dir / "tau2_matched_boundary.csv"
    latex_numbers = paper_sections_dir / "generated_tau2_matched_boundary_numbers.tex"
    _write_csv(csv_path, TAU2_MATCHED_BOUNDARY_FIELDS, report["rows"])
    latex_numbers.write_text(_latex_numbers(report["summary"]), encoding="utf-8")

    report["outputs"] = {
        "summary_json": str(summary_path),
        "csv": str(csv_path),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _row_from_run(run: dict[str, Any], source_path: Path) -> dict[str, str]:
    boundary_records = run.get("boundary_records") or []
    cancel_tool_calls = int(run.get("cancel_tool_calls") or 0)
    retail_exchange_tool_calls = int(run.get("retail_exchange_tool_calls") or 0)
    state_change_tool_calls = run.get("state_change_tool_calls")
    if state_change_tool_calls is None:
        state_change_tool_calls = cancel_tool_calls + retail_exchange_tool_calls
    return {
        "pair_id": str(run["pair_id"]),
        "domain": str(run.get("domain", "")),
        "task_id": str(run.get("task_id", "")),
        "seed": str(run.get("seed", "")),
        "actor_model": str(run.get("actor_model", "")),
        "user_mode": str(run.get("user_mode", "")),
        "condition": str(run["condition"]),
        "reward": _format_number(float(run.get("reward") or 0.0)),
        "cancel_tool_calls": str(cancel_tool_calls),
        "retail_exchange_tool_calls": str(retail_exchange_tool_calls),
        "state_change_tool_calls": str(int(state_change_tool_calls or 0)),
        "read_correct_write_wrong": "yes" if run.get("read_correct_write_wrong") else "no",
        "boundary_vetoes": str(sum(1 for record in boundary_records if not record.get("allowed"))),
        "boundary_allows": str(sum(1 for record in boundary_records if record.get("allowed"))),
        "paper_use": str(run.get("paper_use", "")),
        "source_path": str(source_path),
    }


def _compact_run(
    run: dict[str, Any],
    *,
    domain: str,
    actor_model: str,
    user_mode: str,
    paper_use: str,
) -> dict[str, Any]:
    cancel_tool_calls = int(run.get("cancel_tool_calls") or 0)
    retail_exchange_tool_calls = int(run.get("retail_exchange_tool_calls") or 0)
    state_change_tool_calls = run.get("state_change_tool_calls")
    if state_change_tool_calls is None:
        state_change_tool_calls = cancel_tool_calls + retail_exchange_tool_calls
    return {
        "pair_id": str(run["pair_id"]),
        "domain": domain,
        "task_id": str(run.get("task_id", "")),
        "seed": _seed_from_pair_id(str(run["pair_id"])),
        "actor_model": actor_model,
        "user_mode": user_mode,
        "condition": str(run["condition"]),
        "reward": float(run.get("reward") or 0.0),
        "cancel_tool_calls": cancel_tool_calls,
        "retail_exchange_tool_calls": retail_exchange_tool_calls,
        "state_change_tool_calls": int(state_change_tool_calls or 0),
        "read_correct_write_wrong": bool(run.get("read_correct_write_wrong")),
        "boundary_records": run.get("boundary_records") or [],
        "paper_use": paper_use,
    }


def _block_summaries(runs: list[dict[str, Any]], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_paper_use: dict[str, list[dict[str, Any]]] = {}
    by_paper_use_rows: dict[str, list[dict[str, str]]] = {}
    for run in runs:
        key = str(run.get("paper_use") or "unspecified")
        by_paper_use.setdefault(key, []).append(run)
    for row in rows:
        key = row["paper_use"] or "unspecified"
        by_paper_use_rows.setdefault(key, []).append(row)

    blocks = []
    for paper_use in sorted(by_paper_use):
        block_runs = by_paper_use[paper_use]
        block_rows = by_paper_use_rows[paper_use]
        summary = summarize_tau2_matched_runs(block_runs)
        summary.update(
            {
                "paper_use": paper_use,
                "domains": sorted({row["domain"] for row in block_rows}),
                "task_ids": sorted({row["task_id"] for row in block_rows}),
                "actor_models": sorted({row["actor_model"] for row in block_rows}),
                "user_modes": sorted({row["user_mode"] for row in block_rows}),
                "source_paths": sorted({row["source_path"] for row in block_rows}),
            }
        )
        blocks.append(summary)
    return blocks


def _seed_from_pair_id(pair_id: str) -> int:
    prefix = "seed-"
    if prefix not in pair_id:
        raise ValueError(f"pair_id does not contain seed: {pair_id}")
    return int(pair_id.rsplit(prefix, maxsplit=1)[1])


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTATauTwoMatchedPairs": summary["pairs"],
        "LTATauTwoMatchedCompletePairs": summary["complete_pairs"],
        "LTATauTwoMatchedBaselineTrials": summary["baseline_trials"],
        "LTATauTwoMatchedBoundaryTrials": summary["boundary_trials"],
        "LTATauTwoMatchedBaselineMeanReward": _format_number(summary["baseline_mean_reward"]),
        "LTATauTwoMatchedBoundaryMeanReward": _format_number(summary["boundary_mean_reward"]),
        "LTATauTwoMatchedRewardDelta": _format_number(summary["reward_delta"]),
        "LTATauTwoMatchedBaselineRCWW": summary["baseline_read_correct_write_wrong"],
        "LTATauTwoMatchedBoundaryRCWW": summary["boundary_read_correct_write_wrong"],
        "LTATauTwoMatchedBoundaryVetoes": summary["boundary_vetoes"],
        "LTATauTwoMatchedBoundaryAllows": summary["boundary_allows"],
        "LTATauTwoMatchedBoundaryCompletionTriggers": summary["boundary_completion_triggers"],
        "LTATauTwoMatchedBaselineRetailExchangeCalls": summary[
            "baseline_retail_exchange_tool_calls"
        ],
        "LTATauTwoMatchedBoundaryRetailExchangeCalls": summary[
            "boundary_retail_exchange_tool_calls"
        ],
        "LTATauTwoMatchedBaselineStateChanges": summary["baseline_state_change_tool_calls"],
        "LTATauTwoMatchedBoundaryStateChanges": summary["boundary_state_change_tool_calls"],
        "LTATauTwoMatchedBoundaryRegressions": summary["boundary_regressions"],
        "LTATauTwoMatchedActorModels": summary["actor_models"],
        "LTATauTwoMatchedDomains": summary["domains"],
        "LTATauTwoMatchedBlocks": summary["blocks"],
    }
    commands.update(_block_latex_commands(summary.get("block_summaries", [])))
    lines = [
        "% Auto-generated by License_code/license_to_act/tau2_matched_boundary_export.py.",
        "% Regenerate with License_code/scripts/export_tau2_matched_boundary.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _block_latex_commands(blocks: list[dict[str, Any]]) -> dict[str, str]:
    commands: dict[str, str] = {}
    for block in blocks:
        paper_use = block["paper_use"]
        if paper_use == "matched_tau2_k20":
            prefix = "LTATauTwoAirlineMatched"
        elif paper_use == "matched_tau2_retail_completion_k5":
            prefix = "LTATauTwoRetailMatched"
        elif paper_use == "matched_tau2_retail_scope_k5":
            prefix = "LTATauTwoRetailScopeMatched"
        else:
            continue
        commands.update(
            {
                f"{prefix}Pairs": str(block["pairs"]),
                f"{prefix}CompletePairs": str(block["complete_pairs"]),
                f"{prefix}BaselineTrials": str(block["baseline_trials"]),
                f"{prefix}BoundaryTrials": str(block["boundary_trials"]),
                f"{prefix}BaselineMeanReward": _format_number(block["baseline_mean_reward"]),
                f"{prefix}BoundaryMeanReward": _format_number(block["boundary_mean_reward"]),
                f"{prefix}RewardDelta": _format_number(block["reward_delta"]),
                f"{prefix}BaselineRCWW": str(block["baseline_read_correct_write_wrong"]),
                f"{prefix}BoundaryRCWW": str(block["boundary_read_correct_write_wrong"]),
                f"{prefix}BoundaryVetoes": str(block["boundary_vetoes"]),
                f"{prefix}BoundaryAllows": str(block["boundary_allows"]),
                f"{prefix}BoundaryCompletionTriggers": str(block["boundary_completion_triggers"]),
                f"{prefix}BaselineRetailExchangeCalls": str(
                    block["baseline_retail_exchange_tool_calls"]
                ),
                f"{prefix}BoundaryRetailExchangeCalls": str(
                    block["boundary_retail_exchange_tool_calls"]
                ),
                f"{prefix}BaselineStateChanges": str(block["baseline_state_change_tool_calls"]),
                f"{prefix}BoundaryStateChanges": str(block["boundary_state_change_tool_calls"]),
                f"{prefix}BoundaryRegressions": str(block["boundary_regressions"]),
            }
        )
    return commands


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

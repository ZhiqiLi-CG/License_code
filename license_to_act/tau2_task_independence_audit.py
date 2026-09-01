from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .tau2_matched_boundary_export import build_tau2_matched_boundary_export


AUDIT_FIELDS = [
    "domain",
    "task_id",
    "actor_model",
    "user_mode",
    "paper_use",
    "pairs",
    "baseline_trials",
    "boundary_trials",
    "baseline_mean_reward",
    "boundary_mean_reward",
    "reward_delta",
    "boundary_regressions",
    "counts_as_main_matched",
]


def build_tau2_task_independence_audit(
    project_root: str | Path = Path("/data/zhiqi/License"),
) -> dict[str, Any]:
    tau2 = build_tau2_matched_boundary_export(project_root)
    main_runs = [
        run
        for run in tau2["rows"]
        if run["paper_use"].startswith("matched_tau2")
        and run["paper_use"] != "matched_tau2_retention_k5"
    ]
    grouped = _group_runs(main_runs)
    rows = [_row_from_group(key, runs) for key, runs in sorted(grouped.items())]

    task_groups = _group_runs(
        main_runs,
        key_fields=("domain", "task_id"),
    )
    macro_baseline = _mean(_condition_mean(runs, "baseline") for runs in task_groups.values())
    macro_boundary = _mean(_condition_mean(runs, "action_boundary") for runs in task_groups.values())

    complete_pairs = len({row["pair_id"] for row in main_runs})
    unique_tasks = {(row["domain"], row["task_id"]) for row in main_runs}
    summary = {
        "complete_pairs": complete_pairs,
        "unique_task_count": len(unique_tasks),
        "domain_count": len({row["domain"] for row in main_runs}),
        "actor_model_count": len({row["actor_model"] for row in main_runs}),
        "user_mode_count": len({row["user_mode"] for row in main_runs}),
        "fixture_block_count": len(
            {
                row["paper_use"]
                for row in main_runs
                if row["paper_use"] != "matched_tau2_retention_k5"
            }
        ),
        "task_condition_block_count": len(rows),
        "seed_to_unique_task_ratio": _round(complete_pairs / max(len(unique_tasks), 1)),
        "macro_task_baseline_mean_reward": _round(macro_baseline),
        "macro_task_boundary_mean_reward": _round(macro_boundary),
        "macro_task_reward_delta": _round(macro_boundary - macro_baseline),
        "boundary_regressions": sum(int(row["boundary_regressions"]) for row in rows),
    }
    return {"summary": summary, "rows": rows}


def write_tau2_task_independence_audit(
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
        else root / "artifacts" / "paper_results" / "tau2_task_independence_audit_20260901.json"
    )

    audit = build_tau2_task_independence_audit(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    audit_csv = paper_data_dir / "tau2_task_independence_audit.csv"
    latex_numbers = paper_sections_dir / "generated_tau2_independence_numbers.tex"
    _write_csv(audit_csv, audit["rows"])
    latex_numbers.write_text(_latex_numbers(audit["summary"]), encoding="utf-8")

    audit["outputs"] = {
        "summary_json": str(summary_path),
        "audit_csv": str(audit_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def _group_runs(
    runs: list[dict[str, str]],
    *,
    key_fields: tuple[str, ...] = ("domain", "task_id", "actor_model", "user_mode", "paper_use"),
) -> dict[tuple[str, ...], list[dict[str, str]]]:
    grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for run in runs:
        grouped[tuple(run[field] for field in key_fields)].append(run)
    return dict(grouped)


def _row_from_group(key: tuple[str, ...], runs: list[dict[str, str]]) -> dict[str, str]:
    domain, task_id, actor_model, user_mode, paper_use = key
    baseline_mean = _condition_mean(runs, "baseline")
    boundary_mean = _condition_mean(runs, "action_boundary")
    regressions = sum(
        1
        for pair_id in {run["pair_id"] for run in runs}
        if _pair_regressed(runs, pair_id)
    )
    return {
        "domain": domain,
        "task_id": task_id,
        "actor_model": actor_model,
        "user_mode": user_mode,
        "paper_use": paper_use,
        "pairs": str(len({run["pair_id"] for run in runs})),
        "baseline_trials": str(_condition_count(runs, "baseline")),
        "boundary_trials": str(_condition_count(runs, "action_boundary")),
        "baseline_mean_reward": f"{baseline_mean:.3f}",
        "boundary_mean_reward": f"{boundary_mean:.3f}",
        "reward_delta": f"{(boundary_mean - baseline_mean):.3f}",
        "boundary_regressions": str(regressions),
        "counts_as_main_matched": "yes",
    }


def _pair_regressed(runs: list[dict[str, str]], pair_id: str) -> bool:
    pair_runs = [run for run in runs if run["pair_id"] == pair_id]
    baseline = [float(run["reward"]) for run in pair_runs if run["condition"] == "baseline"]
    boundary = [float(run["reward"]) for run in pair_runs if run["condition"] == "action_boundary"]
    return bool(baseline and boundary and max(baseline) > max(boundary))


def _condition_count(runs: list[dict[str, str]], condition: str) -> int:
    return sum(1 for run in runs if run["condition"] == condition)


def _condition_mean(runs: list[dict[str, str]], condition: str) -> float:
    rewards = [float(run["reward"]) for run in runs if run["condition"] == condition]
    return sum(rewards) / len(rewards) if rewards else 0.0


def _mean(values: Any) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0


def _round(value: float) -> float:
    return round(value + 0.0, 3)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AUDIT_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTATauTwoIndependenceCompletePairs": summary["complete_pairs"],
        "LTATauTwoIndependenceUniqueTasks": summary["unique_task_count"],
        "LTATauTwoIndependenceDomains": summary["domain_count"],
        "LTATauTwoIndependenceActorModels": summary["actor_model_count"],
        "LTATauTwoIndependenceUserModes": summary["user_mode_count"],
        "LTATauTwoIndependenceFixtureBlocks": summary["fixture_block_count"],
        "LTATauTwoIndependenceTaskConditionBlocks": summary["task_condition_block_count"],
        "LTATauTwoIndependenceSeedToTaskRatio": f"{summary['seed_to_unique_task_ratio']:.3f}",
        "LTATauTwoIndependenceMacroTaskBaselineMeanReward": (
            f"{summary['macro_task_baseline_mean_reward']:.3f}"
        ),
        "LTATauTwoIndependenceMacroTaskBoundaryMeanReward": (
            f"{summary['macro_task_boundary_mean_reward']:.3f}"
        ),
        "LTATauTwoIndependenceMacroTaskRewardDelta": (
            f"{summary['macro_task_reward_delta']:.3f}"
        ),
        "LTATauTwoIndependenceBoundaryRegressions": summary["boundary_regressions"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/tau2_task_independence_audit.py.",
        "% Regenerate with License_code/scripts/export_tau2_task_independence_audit.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

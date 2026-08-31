from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .examples import tau2_cancel_license
from .tau2_policy_authority import evaluate_tau2_tool_call, field, tool_call_name


BASELINE_CONDITION = "baseline"
BOUNDARY_CONDITION = "action_boundary"


def summarize_tau2_matched_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    pair_ids = sorted({str(run["pair_id"]) for run in runs})
    baseline_runs = [run for run in runs if run.get("condition") == BASELINE_CONDITION]
    boundary_runs = [run for run in runs if run.get("condition") == BOUNDARY_CONDITION]
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for run in runs:
        by_pair.setdefault(str(run["pair_id"]), {})[str(run["condition"])] = run

    complete_pairs = {
        pair_id: pair
        for pair_id, pair in by_pair.items()
        if BASELINE_CONDITION in pair and BOUNDARY_CONDITION in pair
    }
    regressions = 0
    for pair in complete_pairs.values():
        baseline_reward = float(pair[BASELINE_CONDITION].get("reward") or 0.0)
        boundary_reward = float(pair[BOUNDARY_CONDITION].get("reward") or 0.0)
        if boundary_reward < baseline_reward:
            regressions += 1

    boundary_records = [
        record
        for run in boundary_runs
        for record in run.get("boundary_records", [])
    ]
    return {
        "pairs": len(pair_ids),
        "complete_pairs": len(complete_pairs),
        "baseline_trials": len(baseline_runs),
        "boundary_trials": len(boundary_runs),
        "baseline_mean_reward": _mean_reward(baseline_runs),
        "boundary_mean_reward": _mean_reward(boundary_runs),
        "reward_delta": _mean_reward(boundary_runs) - _mean_reward(baseline_runs),
        "baseline_read_correct_write_wrong": sum(
            1 for run in baseline_runs if run.get("read_correct_write_wrong")
        ),
        "boundary_read_correct_write_wrong": sum(
            1 for run in boundary_runs if run.get("read_correct_write_wrong")
        ),
        "boundary_vetoes": sum(1 for record in boundary_records if not record.get("allowed")),
        "boundary_allows": sum(1 for record in boundary_records if record.get("allowed")),
        "boundary_regressions": regressions,
    }


def simulation_to_matched_run(
    simulation: Any,
    *,
    pair_id: str,
    condition: str,
    current_time: str,
    boundary_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    messages = list(field(simulation, "messages", []) or [])
    cancel_tool_calls = _cancel_tool_calls(messages)
    return {
        "pair_id": pair_id,
        "condition": condition,
        "task_id": str(field(simulation, "task_id", "")),
        "reward": _reward(simulation),
        "termination_reason": field(simulation, "termination_reason"),
        "cancel_tool_calls": len(cancel_tool_calls),
        "read_correct_write_wrong": _has_read_correct_write_wrong(cancel_tool_calls, messages, current_time),
        "boundary_records": boundary_records or [],
        "simulation": _jsonable(simulation),
    }


def write_tau2_matched_report(path: Path, runs: list[dict[str, Any]]) -> dict[str, Any]:
    report = {
        "summary": summarize_tau2_matched_runs(runs),
        "runs": runs,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _mean_reward(runs: list[dict[str, Any]]) -> float:
    if not runs:
        return 0.0
    return sum(float(run.get("reward") or 0.0) for run in runs) / len(runs)


def _reward(simulation: Any) -> float | None:
    reward_info = field(simulation, "reward_info")
    reward = field(reward_info, "reward")
    if reward is None:
        reward = field(simulation, "reward")
    return None if reward is None else float(reward)


def _cancel_tool_calls(messages: list[Any]) -> list[Any]:
    calls: list[Any] = []
    for message in messages:
        if field(message, "role") != "assistant":
            continue
        for tool_call in field(message, "tool_calls", []) or []:
            if tool_call_name(tool_call) == "cancel_reservation":
                calls.append(tool_call)
    return calls


def _has_read_correct_write_wrong(
    cancel_tool_calls: list[Any],
    messages: list[Any],
    current_time: str,
) -> bool:
    for tool_call in cancel_tool_calls:
        decision = evaluate_tau2_tool_call(
            messages,
            tool_call,
            current_time,
            [tau2_cancel_license()],
        )
        if not decision.allowed:
            return True
    return False


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value

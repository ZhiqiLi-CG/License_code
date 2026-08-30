from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .examples import tau2_cancel_license
from .tau2_policy_authority import cancel_reservation_event_from_trace, evaluate_tau2_tool_call, tool_call_arguments, tool_call_name


def replay_tau2_cancel_decisions(path: Path, current_time: str) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    simulations = result.get("simulations") or result.get("results") or []
    return {
        "path": str(path),
        "current_time": current_time,
        "license": "tau2_airline_cancel_policy",
        "simulations": [_replay_simulation(simulation, current_time) for simulation in simulations],
    }


def write_tau2_cancel_replay(path: Path, output_path: Path, current_time: str) -> dict[str, Any]:
    report = replay_tau2_cancel_decisions(path, current_time)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _replay_simulation(simulation: dict[str, Any], current_time: str) -> dict[str, Any]:
    messages = simulation.get("messages") or []
    decisions = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for tool_call in message.get("tool_calls") or []:
            if tool_call_name(tool_call) != "cancel_reservation":
                continue
            event = cancel_reservation_event_from_trace(messages, tool_call, current_time)
            decision = evaluate_tau2_tool_call(messages, tool_call, current_time, [tau2_cancel_license()])
            args = tool_call_arguments(tool_call)
            decisions.append(
                {
                    "tool_name": "cancel_reservation",
                    "reservation_id": str(args.get("reservation_id", "")),
                    "state_region": event.state_region,
                    "operation": event.operation,
                    "evidence_types": sorted(event.evidence.types),
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                    "missing_evidence": sorted(decision.missing_evidence),
                }
            )
    return {
        "task_id": str(simulation.get("task_id")),
        "reward": _reward(simulation),
        "decisions": decisions,
    }


def _reward(simulation: dict[str, Any]) -> float | None:
    reward = (simulation.get("reward_info") or {}).get("reward", simulation.get("reward"))
    return None if reward is None else float(reward)

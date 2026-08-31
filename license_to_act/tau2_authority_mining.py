from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
import json

from .examples import tau2_cancel_license
from .tau2_policy_authority import (
    cancel_reservation_event_from_trace,
    evaluate_tau2_tool_call,
    extract_current_time,
    tool_call_arguments,
    tool_call_name,
)


DEFAULT_TAU2_SIMULATION_ROOT = Path(
    "/data/zhiqi/rp-simple-agent-acl-paper-longrun-20260808-v4/global/resources/"
    "datasets/tau2-bench/data/simulations"
)


def discover_tau2_result_paths(root: Path = DEFAULT_TAU2_SIMULATION_ROOT) -> list[Path]:
    return sorted(root.rglob("results.json"))


def mine_tau2_authority_results(
    result_paths: Iterable[Path],
    *,
    current_time: str = "2024-05-15T15:00:00",
) -> dict[str, Any]:
    result_files: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    infrastructure_errors: list[dict[str, Any]] = []

    for path in sorted(result_paths):
        payload = _read_json(path)
        run_id = path.parent.name
        simulations = payload.get("simulations") or payload.get("results") or []
        result_files.append(
            {
                "path": str(path),
                "run_id": run_id,
                "n_simulations": len(simulations),
                "model": infer_model(run_id, payload),
                "domain": infer_domain(run_id, payload),
                "condition_family": infer_condition_family(run_id),
            }
        )
        for index, simulation in enumerate(simulations):
            error = _simulation_error(simulation)
            if error is not None:
                infrastructure_errors.append(
                    {
                        "path": str(path),
                        "run_id": run_id,
                        "simulation_index": index,
                        "task_id": str(simulation.get("task_id") or simulation.get("id") or ""),
                        **error,
                    }
                )
                continue
            decisions.extend(
                _mine_simulation(
                    simulation,
                    path=path,
                    run_id=run_id,
                    result_payload=payload,
                    fallback_current_time=current_time,
                )
            )

    return {
        "benchmark": "tau2-Bench",
        "analysis": "authority_mining_for_cancel_reservation",
        "license": "tau2_airline_cancel_policy",
        "result_files": result_files,
        "summary": _summarize(result_files, decisions, infrastructure_errors),
        "by_model": _group_summary(decisions, "model"),
        "by_condition_family": _group_summary(decisions, "condition_family"),
        "by_domain": _group_summary(decisions, "domain"),
        "infrastructure_errors": infrastructure_errors,
        "decisions": decisions,
    }


def write_tau2_authority_mining_report(
    output_path: Path,
    result_paths: Iterable[Path],
    *,
    current_time: str = "2024-05-15T15:00:00",
) -> dict[str, Any]:
    report = mine_tau2_authority_results(result_paths, current_time=current_time)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def infer_model(run_id: str, payload: dict[str, Any] | None = None) -> str:
    text = f"{run_id} {_payload_agent_blob(payload)}".lower()
    if "mistral" in text:
        return "Mistral-Small-3.2-24B"
    if "gemma" in text:
        return "Gemma-4-31B-it"
    if "codex" in text:
        return "Codex"
    if "claude" in text:
        return "Claude"
    if "qwen" in text:
        return "Qwen3.8-27B"
    return "unknown"


def infer_domain(run_id: str, payload: dict[str, Any] | None = None) -> str:
    text = run_id.lower()
    for domain in ("airline", "retail", "telecom", "banking", "mock"):
        if domain in text:
            return domain
    tasks = (payload or {}).get("tasks") or []
    for task in tasks:
        if isinstance(task, dict):
            joined = json.dumps(task, sort_keys=True).lower()
            for domain in ("airline", "retail", "telecom", "banking", "mock"):
                if domain in joined:
                    return domain
    return "unknown"


def infer_condition_family(run_id: str) -> str:
    text = run_id.lower()
    lta_terms = (
        "precommit",
        "contract",
        "actioncert",
        "claimguard",
        "license",
        "lta",
        "gate",
        "receipt_gate",
    )
    memory_terms = ("prompt_checklist", "memory_lesson", "proofhandle", "recuris")
    if any(term in text for term in lta_terms):
        return "license_to_act_or_gate"
    if any(term in text for term in memory_terms):
        return "prompt_or_memory"
    return "baseline_or_probe"


def _mine_simulation(
    simulation: dict[str, Any],
    *,
    path: Path,
    run_id: str,
    result_payload: dict[str, Any],
    fallback_current_time: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    messages = simulation.get("messages") or []
    policy_time = extract_current_time(str(simulation.get("policy") or ""), fallback=fallback_current_time)
    reward = _reward(simulation)
    reward_breakdown = (simulation.get("reward_info") or {}).get("reward_breakdown") or {}
    domain = infer_domain(run_id, result_payload)
    model = infer_model(run_id, result_payload)
    condition = infer_condition_family(run_id)
    read_matches = _matched_read_actions(simulation)

    for message in messages:
        if message.get("role") != "assistant":
            continue
        for tool_call in message.get("tool_calls") or []:
            if tool_call_name(tool_call) != "cancel_reservation":
                continue
            args = tool_call_arguments(tool_call)
            reservation_id = str(args.get("reservation_id", ""))
            event = cancel_reservation_event_from_trace(messages, tool_call, policy_time)
            decision = evaluate_tau2_tool_call(messages, tool_call, policy_time, [tau2_cancel_license()])
            evidence_types = sorted(event.evidence.types)
            has_reservation_state = "ReservationStateEvidence" in event.evidence.types
            veto = not decision.allowed
            db_reward = _float_or_none(reward_breakdown.get("DB"))
            communicate_reward = _float_or_none(reward_breakdown.get("COMMUNICATE"))
            read_correct_write_wrong = (
                veto
                and has_reservation_state
                and (reward == 0.0 or db_reward == 0.0)
            )
            rows.append(
                {
                    "path": str(path),
                    "run_id": run_id,
                    "model": model,
                    "domain": domain,
                    "condition_family": condition,
                    "task_id": str(simulation.get("task_id") or simulation.get("id") or ""),
                    "reward": reward,
                    "db_reward": db_reward,
                    "communicate_reward": communicate_reward,
                    "current_time": policy_time,
                    "tool_name": "cancel_reservation",
                    "reservation_id": reservation_id,
                    "operation": event.operation,
                    "state_region": event.state_region,
                    "evidence_types": evidence_types,
                    "missing_evidence": sorted(decision.missing_evidence),
                    "license_allowed": decision.allowed,
                    "license_reason": decision.reason,
                    "lta_veto": veto,
                    "has_user_intent": "UserIntentEvidence" in event.evidence.types,
                    "has_reservation_state": has_reservation_state,
                    "has_policy_authorization": "PolicyAuthorizationEvidence" in event.evidence.types,
                    "matched_reservation_read": reservation_id in read_matches,
                    "read_correct_write_wrong_proxy": read_correct_write_wrong,
                    "outcome_bucket": _outcome_bucket(decision.allowed, reward, db_reward),
                }
            )
    return rows


def _summarize(
    result_files: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    infrastructure_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    vetoes = [row for row in decisions if row["lta_veto"]]
    licensed = [row for row in decisions if row["license_allowed"]]
    return {
        "n_result_files": len(result_files),
        "n_simulations": sum(int(row["n_simulations"]) for row in result_files),
        "n_infrastructure_error_simulations": len(infrastructure_errors),
        "n_cancel_decisions": len(decisions),
        "n_lta_vetoes": len(vetoes),
        "n_lta_allows": len(licensed),
        "n_vetoes_with_user_intent": _count(vetoes, "has_user_intent"),
        "n_vetoes_with_reservation_state": _count(vetoes, "has_reservation_state"),
        "n_vetoes_with_matched_reservation_read": _count(vetoes, "matched_reservation_read"),
        "n_vetoes_with_reward_zero": sum(1 for row in vetoes if row["reward"] == 0.0),
        "n_vetoes_with_db_failure": sum(1 for row in vetoes if row["db_reward"] == 0.0),
        "n_read_correct_write_wrong_proxy": _count(decisions, "read_correct_write_wrong_proxy"),
        "n_license_allows_with_reward_one": sum(1 for row in licensed if row["reward"] == 1.0),
        "outcome_buckets": dict(Counter(row["outcome_bucket"] for row in decisions)),
    }


def _group_summary(decisions: list[dict[str, Any]], key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in decisions:
        groups[str(row[key])].append(row)
    return {name: _summarize_group(rows) for name, rows in sorted(groups.items())}


def _summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    vetoes = [row for row in rows if row["lta_veto"]]
    return {
        "n_cancel_decisions": len(rows),
        "n_lta_vetoes": len(vetoes),
        "n_lta_allows": sum(1 for row in rows if row["license_allowed"]),
        "n_read_correct_write_wrong_proxy": _count(rows, "read_correct_write_wrong_proxy"),
        "mean_reward_on_cancel_decisions": _mean(row["reward"] for row in rows),
        "outcome_buckets": dict(Counter(row["outcome_bucket"] for row in rows)),
    }


def _outcome_bucket(allowed: bool, reward: float | None, db_reward: float | None) -> str:
    if not allowed and (reward == 0.0 or db_reward == 0.0):
        return "veto_target_failed_commit"
    if not allowed:
        return "veto_target_nonfailing_or_unscored"
    if allowed and reward == 1.0:
        return "licensed_success"
    if allowed:
        return "licensed_failure_or_partial"
    return "unscored"


def _matched_read_actions(simulation: dict[str, Any]) -> set[str]:
    matches = set()
    reward_info = simulation.get("reward_info") or {}
    for check in reward_info.get("action_checks") or []:
        action = check.get("action") or {}
        if action.get("name") != "get_reservation_details" or not check.get("action_match"):
            continue
        reservation_id = (action.get("arguments") or {}).get("reservation_id")
        if reservation_id:
            matches.add(str(reservation_id))
    return matches


def _simulation_error(simulation: dict[str, Any]) -> dict[str, str] | None:
    info = simulation.get("info")
    if isinstance(info, dict) and ("error" in info or "error_type" in info):
        return {
            "error_type": str(info.get("error_type") or "unknown"),
            "error": str(info.get("error") or ""),
        }
    if "error" in simulation or "error_type" in simulation:
        return {
            "error_type": str(simulation.get("error_type") or "unknown"),
            "error": str(simulation.get("error") or ""),
        }
    return None


def _reward(simulation: dict[str, Any]) -> float | None:
    reward = (simulation.get("reward_info") or {}).get("reward", simulation.get("reward"))
    return _float_or_none(reward)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _payload_agent_blob(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    info = payload.get("info") or {}
    if not isinstance(info, dict):
        return ""
    return json.dumps(info.get("agent_info") or {}, sort_keys=True)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _count(rows: Iterable[dict[str, Any]], key: str) -> int:
    return sum(1 for row in rows if row.get(key))


def _mean(values: Iterable[float | None]) -> float | None:
    concrete = [value for value in values if value is not None]
    if not concrete:
        return None
    return sum(concrete) / len(concrete)

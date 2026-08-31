from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_event


CURRENT_TIME_RE = re.compile(r"current time is ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", re.I)


def evaluate_tau2_tool_call(
    messages: list[Any],
    tool_call: Any,
    current_time: str,
    licenses: list[ActionLicense],
) -> Decision:
    if tool_call_name(tool_call) == "cancel_reservation":
        event = cancel_reservation_event_from_trace(messages, tool_call, current_time)
        return evaluate_event(event, licenses)
    return Decision(allowed=True, reason="non_state_changing_or_unmodeled")


def cancel_reservation_event_from_trace(
    messages: list[Any],
    tool_call: Any,
    current_time: str,
) -> StateChangeEvent:
    args = tool_call_arguments(tool_call)
    reservation_id = str(args.get("reservation_id", ""))
    reservation = extract_latest_reservation(messages, reservation_id)
    reason = infer_cancel_reason(messages)
    evidence_types = set()
    evidence_refs = set()

    if user_expressed_cancellation_intent(messages):
        evidence_types.add("UserIntentEvidence")
        evidence_refs.add("user:cancellation_request")
    if reservation is not None:
        evidence_types.add("ReservationStateEvidence")
        evidence_refs.add(f"reservation:{reservation_id}")
        if cancellation_preconditions_met(reservation, reason, current_time):
            evidence_types.add("CommitReadinessEvidence")
            evidence_refs.add(f"policy:cancel:{reason}")

    return StateChangeEvent(
        actor_role="customer_service_agent",
        state_region=f"reservation:{reservation_id}",
        operation="CommitCancelReservation",
        evidence=EvidenceBundle(types=evidence_types, refs=evidence_refs),
    )


def cancellation_preconditions_met(
    reservation: dict[str, Any],
    reason: str,
    current_time: str,
) -> bool:
    return (
        booking_age_hours(reservation, current_time) is not None
        and booking_age_hours(reservation, current_time) <= 24.0
    ) or (
        str(reservation.get("cabin", "")).lower() == "business"
    ) or (
        reason == "airline_cancelled" or reservation_has_airline_cancelled_flight(reservation)
    ) or (
        str(reservation.get("insurance", "")).lower() == "yes"
        and reason == "covered_insurance_reason"
    )


def booking_age_hours(reservation: dict[str, Any], current_time: str) -> float | None:
    created_at = reservation.get("created_at")
    if not created_at:
        return None
    try:
        return (parse_time(current_time) - parse_time(str(created_at))).total_seconds() / 3600.0
    except ValueError:
        return None


def reservation_has_airline_cancelled_flight(reservation: dict[str, Any]) -> bool:
    for flight in reservation.get("flights") or []:
        status = str(flight.get("status", "")).lower()
        if "cancelled" in status or "canceled" in status:
            return True
    return False


def infer_cancel_reason(messages: list[Any]) -> str:
    user_text = " ".join(
        str(field(message, "content", "") or "").lower()
        for message in messages
        if field(message, "role") == "user"
    )
    if "change of plan" in user_text or "change of plans" in user_text or "plans changed" in user_text:
        return "change_of_plan"
    if "airline cancelled" in user_text or "airline canceled" in user_text or "flight was cancelled" in user_text:
        return "airline_cancelled"
    if any(term in user_text for term in ("weather", "health", "medical", "sick", "unwell", "illness")):
        return "covered_insurance_reason"
    return "unknown"


def user_expressed_cancellation_intent(messages: list[Any]) -> bool:
    return any(
        field(message, "role") == "user"
        and "cancel" in str(field(message, "content", "") or "").lower()
        for message in messages
    )


def extract_current_time(policy: str, fallback: str = "2024-05-15T15:00:00") -> str:
    match = CURRENT_TIME_RE.search(policy)
    if match is None:
        return fallback
    return match.group(1).replace(" ", "T")


def extract_latest_reservation(messages: list[Any], reservation_id: str) -> dict[str, Any] | None:
    for message in reversed(messages):
        if field(message, "role") != "tool":
            continue
        payload = parse_json_dict(field(message, "content"))
        if payload and payload.get("reservation_id") == reservation_id:
            return payload
    return None


def tool_call_name(tool_call: Any) -> str | None:
    name = field(tool_call, "name")
    if name:
        return str(name)
    function = field(tool_call, "function")
    if isinstance(function, dict) and function.get("name"):
        return str(function["name"])
    return None


def tool_call_arguments(tool_call: Any) -> dict[str, Any]:
    args = field(tool_call, "arguments", {})
    if isinstance(args, str):
        return parse_json_dict(args) or {}
    if isinstance(args, dict):
        return args
    function = field(tool_call, "function")
    if isinstance(function, dict):
        function_args = function.get("arguments", {})
        if isinstance(function_args, str):
            return parse_json_dict(function_args) or {}
        if isinstance(function_args, dict):
            return function_args
    return {}


def parse_json_dict(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def parse_time(value: str) -> datetime:
    normalized = value.replace(" EST", "").replace("Z", "")
    if "T" in normalized:
        return datetime.fromisoformat(normalized)
    return datetime.strptime(normalized, "%Y-%m-%d %H:%M:%S")


def field(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

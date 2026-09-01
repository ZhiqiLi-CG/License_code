from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from .examples import tau2_cancel_license, tau2_retail_exchange_license
from .tau2_policy_authority import (
    evaluate_tau2_tool_call,
    field,
    retail_exchange_candidate_from_trace,
    tool_call_arguments,
    tool_call_name,
)


DEFAULT_CANCEL_VETO_TEXT = (
    "I cannot cancel this reservation under the current policy because the "
    "available reservation evidence does not show that a cancellation exception "
    "applies. I can continue checking alternatives or explain the policy."
)
DEFAULT_RETAIL_EXCHANGE_VETO_TEXT = (
    "I need explicit confirmation before submitting the exchange. I can list the "
    "items, replacements, and payment method, then proceed after you confirm yes."
)


@dataclass(frozen=True)
class Tau2BoundaryResult:
    message: Any
    records: list[dict[str, Any]] = dataclass_field(default_factory=list)


def apply_tau2_cancel_boundary(
    messages: list[Any],
    assistant_message: Any,
    *,
    current_time: str,
    veto_text: str = DEFAULT_CANCEL_VETO_TEXT,
) -> Tau2BoundaryResult:
    """Apply the tau2 cancellation boundary to one proposed assistant action.

    The function leaves the same actor in control of proposal generation. It only
    rewrites a proposed `cancel_reservation` tool call when the available trace
    evidence lacks cancellation readiness.
    """
    tool_calls = field(assistant_message, "tool_calls") or []
    if not tool_calls:
        return Tau2BoundaryResult(message=assistant_message, records=[])

    records: list[dict[str, Any]] = []
    vetoed = False
    for tool_call in tool_calls:
        if tool_call_name(tool_call) != "cancel_reservation":
            continue
        decision = evaluate_tau2_tool_call(
            messages,
            tool_call,
            current_time,
            [tau2_cancel_license()],
        )
        args = tool_call_arguments(tool_call)
        record = {
            "tool_name": "cancel_reservation",
            "reservation_id": str(args.get("reservation_id", "")),
            "allowed": decision.allowed,
            "reason": decision.reason,
            "missing_evidence": sorted(decision.missing_evidence),
            "replacement": "none" if decision.allowed else "assistant_text_response",
        }
        records.append(record)
        if not decision.allowed:
            vetoed = True

    if not vetoed:
        return Tau2BoundaryResult(message=assistant_message, records=records)
    return Tau2BoundaryResult(
        message=_text_message_like(assistant_message, veto_text),
        records=records,
    )


def apply_tau2_action_boundary(
    messages: list[Any],
    assistant_message: Any,
    *,
    current_time: str,
    cancel_veto_text: str = DEFAULT_CANCEL_VETO_TEXT,
    retail_exchange_veto_text: str = DEFAULT_RETAIL_EXCHANGE_VETO_TEXT,
) -> Tau2BoundaryResult:
    """Apply supported tau2 action-boundary checks to one proposed action."""
    tool_calls = field(assistant_message, "tool_calls") or []
    if not tool_calls:
        completion = _retail_exchange_completion_from_trace(messages, assistant_message, current_time)
        if completion is not None:
            return completion
        return Tau2BoundaryResult(message=assistant_message, records=[])

    records: list[dict[str, Any]] = []
    vetoed = False
    veto_text = cancel_veto_text
    for tool_call in tool_calls:
        name = tool_call_name(tool_call)
        args = tool_call_arguments(tool_call)
        if name == "cancel_reservation":
            decision = evaluate_tau2_tool_call(
                messages,
                tool_call,
                current_time,
                [tau2_cancel_license()],
            )
            record = {
                "tool_name": "cancel_reservation",
                "reservation_id": str(args.get("reservation_id", "")),
                "allowed": decision.allowed,
                "reason": decision.reason,
                "missing_evidence": sorted(decision.missing_evidence),
                "replacement": "none" if decision.allowed else "assistant_text_response",
            }
        elif name == "exchange_delivered_order_items":
            decision = evaluate_tau2_tool_call(
                messages,
                tool_call,
                current_time,
                [tau2_retail_exchange_license()],
            )
            record = {
                "tool_name": "exchange_delivered_order_items",
                "state_id": str(args.get("order_id", "")),
                "allowed": decision.allowed,
                "reason": decision.reason,
                "missing_evidence": sorted(decision.missing_evidence),
                "replacement": "none" if decision.allowed else "assistant_text_response",
            }
            if not decision.allowed:
                veto_text = retail_exchange_veto_text
        else:
            continue
        records.append(record)
        if not record["allowed"]:
            vetoed = True

    if not vetoed:
        return Tau2BoundaryResult(message=assistant_message, records=records)
    return Tau2BoundaryResult(
        message=_text_message_like(assistant_message, veto_text),
        records=records,
    )


class Tau2ActionBoundaryAgent:
    """Wrap a tau2 agent and intercept unsupported cancellation commits."""

    def __init__(
        self,
        inner_agent: Any,
        *,
        current_time: str,
        veto_text: str = DEFAULT_CANCEL_VETO_TEXT,
    ) -> None:
        self.inner_agent = inner_agent
        self.current_time = current_time
        self.veto_text = veto_text
        self.boundary_records: list[dict[str, Any]] = []
        self.tools = getattr(inner_agent, "tools", None)
        self.domain_policy = getattr(inner_agent, "domain_policy", None)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.inner_agent, name)

    def get_init_state(self, *args: Any, **kwargs: Any) -> Any:
        return self.inner_agent.get_init_state(*args, **kwargs)

    def generate_next_message(self, message: Any, state: Any) -> tuple[Any, Any]:
        assistant_message, state = self.inner_agent.generate_next_message(message, state)
        history = list(getattr(state, "messages", []) or [])
        prior_messages = (
            history[:-1]
            if history and (history[-1] is assistant_message or history[-1] == assistant_message)
            else history
        )
        result = apply_tau2_action_boundary(
            prior_messages,
            assistant_message,
            current_time=self.current_time,
            cancel_veto_text=self.veto_text,
        )
        if result.records:
            self.boundary_records.extend(result.records)
        if result.message is not assistant_message:
            _replace_last_state_message(state, assistant_message, result.message)
            assistant_message = result.message
        return assistant_message, state


def _replace_last_state_message(state: Any, original: Any, replacement: Any) -> None:
    messages = getattr(state, "messages", None)
    if not messages:
        return
    if messages[-1] is original:
        messages[-1] = replacement
        return
    for index in range(len(messages) - 1, -1, -1):
        if messages[index] == original:
            messages[index] = replacement
            return


def _text_message_like(original: Any, content: str) -> Any:
    if isinstance(original, dict):
        message = dict(original)
        message["role"] = "assistant"
        message["content"] = content
        message["tool_calls"] = None
        return message

    message_class = original.__class__
    kwargs = {
        name: field(original, name)
        for name in ("cost", "usage", "raw_data", "generation_time_seconds")
        if field(original, name) is not None
    }
    text_factory = getattr(message_class, "text", None)
    if callable(text_factory):
        return text_factory(content, **kwargs)
    return message_class(role="assistant", content=content, tool_calls=None, **kwargs)


def _retail_exchange_completion_from_trace(
    messages: list[Any],
    assistant_message: Any,
    current_time: str,
) -> Tau2BoundaryResult | None:
    if _has_observed_tool_call(messages, "exchange_delivered_order_items"):
        return None
    candidate = retail_exchange_candidate_from_trace(messages)
    if candidate is None:
        return None
    tool_call = {
        "name": "exchange_delivered_order_items",
        "arguments": candidate,
        "requestor": "assistant",
    }
    decision = evaluate_tau2_tool_call(
        messages,
        tool_call,
        current_time,
        [tau2_retail_exchange_license()],
    )
    if not decision.allowed:
        return None
    return Tau2BoundaryResult(
        message=_tool_call_message_like(assistant_message, [tool_call]),
        records=[
            {
                "tool_name": "exchange_delivered_order_items",
                "state_id": str(candidate.get("order_id", "")),
                "allowed": True,
                "reason": decision.reason,
                "missing_evidence": [],
                "replacement": "completion_tool_call",
            }
        ],
    )


def _has_observed_tool_call(messages: list[Any], tool_name: str) -> bool:
    for message in messages:
        for tool_call in field(message, "tool_calls", []) or []:
            if tool_call_name(tool_call) == tool_name:
                return True
    return False


def _tool_call_message_like(original: Any, tool_calls: list[dict[str, Any]]) -> Any:
    if isinstance(original, dict):
        message = dict(original)
        message["role"] = "assistant"
        message["content"] = None
        message["tool_calls"] = tool_calls
        return message

    message_class = original.__class__
    kwargs = {
        name: field(original, name)
        for name in ("cost", "usage", "raw_data", "generation_time_seconds")
        if field(original, name) is not None
    }
    return message_class(role="assistant", content=None, tool_calls=tool_calls, **kwargs)

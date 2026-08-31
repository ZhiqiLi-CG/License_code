from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from .examples import tau2_cancel_license
from .tau2_policy_authority import evaluate_tau2_tool_call, field, tool_call_arguments, tool_call_name


DEFAULT_CANCEL_VETO_TEXT = (
    "I cannot cancel this reservation under the current policy because the "
    "available reservation evidence does not show that a cancellation exception "
    "applies. I can continue checking alternatives or explain the policy."
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
        result = apply_tau2_cancel_boundary(
            prior_messages,
            assistant_message,
            current_time=self.current_time,
            veto_text=self.veto_text,
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

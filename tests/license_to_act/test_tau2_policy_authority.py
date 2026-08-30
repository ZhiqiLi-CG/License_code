from __future__ import annotations

import json

from license_to_act.examples import tau2_cancel_license
from license_to_act.tau2_policy_authority import (
    cancel_reservation_event_from_trace,
    evaluate_tau2_tool_call,
)


def test_cancel_event_distinguishes_user_intent_from_policy_authorization():
    messages = [
        {"role": "user", "content": "I need to cancel because of a change of plans."},
        {"role": "tool", "content": json.dumps(_reservation())},
    ]
    tool_call = {"name": "cancel_reservation", "arguments": {"reservation_id": "Q69X3R"}}

    event = cancel_reservation_event_from_trace(messages, tool_call, "2024-05-15T15:00:00")
    decision = evaluate_tau2_tool_call(messages, tool_call, "2024-05-15T15:00:00", [tau2_cancel_license()])

    assert event.evidence.types == {"UserIntentEvidence", "ReservationStateEvidence"}
    assert decision.allowed is False
    assert decision.reason == "missing_required_evidence"
    assert decision.missing_evidence == {"PolicyAuthorizationEvidence"}


def test_cancel_event_adds_policy_authorization_when_precondition_is_met():
    messages = [
        {"role": "user", "content": "I need to cancel because my plans changed."},
        {"role": "tool", "content": json.dumps(_reservation(cabin="business"))},
    ]
    tool_call = {"name": "cancel_reservation", "arguments": {"reservation_id": "Q69X3R"}}

    event = cancel_reservation_event_from_trace(messages, tool_call, "2024-05-15T15:00:00")
    decision = evaluate_tau2_tool_call(messages, tool_call, "2024-05-15T15:00:00", [tau2_cancel_license()])

    assert "PolicyAuthorizationEvidence" in event.evidence.types
    assert decision.allowed is True
    assert decision.reason == "licensed"


def _reservation(**overrides):
    reservation = {
        "reservation_id": "Q69X3R",
        "cabin": "economy",
        "created_at": "2024-05-14T09:52:38",
        "insurance": "no",
        "flights": [{"flight_number": "HAT243", "status": "available"}],
    }
    reservation.update(overrides)
    return reservation

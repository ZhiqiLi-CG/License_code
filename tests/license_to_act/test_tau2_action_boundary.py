from __future__ import annotations

import json

from license_to_act.tau2_action_boundary import apply_tau2_cancel_boundary


def test_vetoed_cancel_tool_call_becomes_text_response():
    messages = [
        {"role": "user", "content": "I need to cancel because my plans changed."},
        {
            "role": "tool",
            "content": json.dumps(
                {
                    "reservation_id": "Q69X3R",
                    "cabin": "economy",
                    "created_at": "2024-05-14T09:52:38",
                    "insurance": "no",
                    "flights": [{"status": "available"}],
                }
            ),
        },
    ]
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "name": "cancel_reservation",
                "arguments": {"reservation_id": "Q69X3R"},
            }
        ],
    }

    result = apply_tau2_cancel_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message["role"] == "assistant"
    assert result.message["tool_calls"] is None
    assert "cannot cancel" in result.message["content"]
    assert result.records == [
        {
            "tool_name": "cancel_reservation",
            "reservation_id": "Q69X3R",
            "allowed": False,
            "reason": "missing_required_evidence",
            "missing_evidence": ["CommitReadinessEvidence"],
            "replacement": "assistant_text_response",
        }
    ]


def test_authorized_cancel_tool_call_passes_through():
    messages = [
        {"role": "user", "content": "I need to cancel because my plans changed."},
        {
            "role": "tool",
            "content": json.dumps(
                {
                    "reservation_id": "Q69X3R",
                    "cabin": "business",
                    "created_at": "2024-05-14T09:52:38",
                    "insurance": "no",
                    "flights": [{"status": "available"}],
                }
            ),
        },
    ]
    assistant_message = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "name": "cancel_reservation",
                "arguments": {"reservation_id": "Q69X3R"},
            }
        ],
    }

    result = apply_tau2_cancel_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message is assistant_message
    assert result.records == [
        {
            "tool_name": "cancel_reservation",
            "reservation_id": "Q69X3R",
            "allowed": True,
            "reason": "licensed",
            "missing_evidence": [],
            "replacement": "none",
        }
    ]

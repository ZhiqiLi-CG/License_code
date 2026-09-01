from __future__ import annotations

import json

from license_to_act.tau2_action_boundary import (
    apply_tau2_action_boundary,
    apply_tau2_cancel_boundary,
)


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


def test_unconfirmed_retail_exchange_tool_call_becomes_confirmation_request():
    messages = [
        {"role": "user", "content": "I want to exchange two items in order #W2378156."},
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
    ]
    assistant_message = _retail_exchange_message()

    result = apply_tau2_action_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message["role"] == "assistant"
    assert result.message["tool_calls"] is None
    assert "confirm" in result.message["content"].lower()
    assert result.records == [
        {
            "tool_name": "exchange_delivered_order_items",
            "state_id": "#W2378156",
            "allowed": False,
            "reason": "missing_required_evidence",
            "missing_evidence": ["RetailExchangeReadinessEvidence"],
            "replacement": "assistant_text_response",
        }
    ]


def test_confirmed_retail_exchange_tool_call_passes_through():
    messages = [
        {"role": "user", "content": "I want to exchange two items in order #W2378156."},
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {
            "role": "assistant",
            "content": "I can exchange item 1151293680 for 7706410293 and item 4983901480 for 7747408585 using credit_card_9513926. Please confirm yes to proceed.",
        },
        {"role": "user", "content": "Yes, please proceed with that exchange."},
    ]
    assistant_message = _retail_exchange_message()

    result = apply_tau2_action_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message is assistant_message
    assert result.records == [
        {
            "tool_name": "exchange_delivered_order_items",
            "state_id": "#W2378156",
            "allowed": True,
            "reason": "licensed",
            "missing_evidence": [],
            "replacement": "none",
        }
    ]


def test_confirmed_retail_exchange_text_response_triggers_missing_commit():
    messages = [
        {
            "role": "user",
            "content": (
                "I want to exchange the keyboard and thermostat in order #W2378156. "
                "For the keyboard I want clicky switches, full size, and RGB. "
                "If that exact keyboard is not available, no backlight is fine."
            ),
        },
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {
            "role": "user",
            "content": "For the thermostat, I want one compatible with Google Home instead of Apple HomeKit.",
        },
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {"role": "user", "content": "Yes, please proceed with that exchange."},
    ]
    assistant_message = {
        "role": "assistant",
        "content": "I checked the order and replacement details.",
        "tool_calls": None,
    }

    result = apply_tau2_action_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message["role"] == "assistant"
    assert result.message["content"] is None
    assert result.message["tool_calls"] == [
        {
            "name": "exchange_delivered_order_items",
            "arguments": {
                "order_id": "#W2378156",
                "item_ids": ["1151293680", "4983901480"],
                "new_item_ids": ["7706410293", "7747408585"],
                "payment_method_id": "credit_card_9513926",
            },
            "requestor": "assistant",
        }
    ]
    assert result.records == [
        {
            "tool_name": "exchange_delivered_order_items",
            "state_id": "#W2378156",
            "allowed": True,
            "reason": "licensed",
            "missing_evidence": [],
            "replacement": "completion_tool_call",
        }
    ]


def test_retail_exchange_text_response_does_not_trigger_without_confirmation():
    messages = [
        {"role": "user", "content": "I want to exchange two items in order #W2378156."},
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
    ]
    assistant_message = {
        "role": "assistant",
        "content": "I checked the order and replacement details.",
        "tool_calls": None,
    }

    result = apply_tau2_action_boundary(
        messages,
        assistant_message,
        current_time="2024-05-15T15:00:00",
    )

    assert result.message is assistant_message
    assert result.records == []


def _retail_exchange_message():
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2378156",
                    "item_ids": ["1151293680", "4983901480"],
                    "new_item_ids": ["7706410293", "7747408585"],
                    "payment_method_id": "credit_card_9513926",
                },
            }
        ],
    }


def _retail_order():
    return {
        "order_id": "#W2378156",
        "user_id": "yusuf_rossi_9620",
        "status": "delivered",
        "items": [
            {
                "name": "Mechanical Keyboard",
                "product_id": "1656367028",
                "item_id": "1151293680",
                "price": 272.33,
                "options": {
                    "switch type": "linear",
                    "backlight": "RGB",
                    "size": "full size",
                },
            },
            {
                "name": "Smart Thermostat",
                "product_id": "4896585277",
                "item_id": "4983901480",
                "price": 262.47,
                "options": {"compatibility": "Apple HomeKit", "color": "black"},
            },
            {
                "name": "Smart Watch",
                "product_id": "6945232052",
                "item_id": "9408160950",
                "price": 381.26,
                "options": {"color": "gold", "band material": "leather"},
            },
        ],
        "payment_history": [
            {
                "transaction_type": "payment",
                "amount": 534.8,
                "payment_method_id": "credit_card_9513926",
            }
        ],
    }


def _keyboard_product():
    return {
        "name": "Mechanical Keyboard",
        "product_id": "1656367028",
        "variants": {
            "7706410293": {
                "item_id": "7706410293",
                "options": {
                    "switch type": "clicky",
                    "backlight": "none",
                    "size": "full size",
                },
                "available": True,
                "price": 269.16,
            }
        },
    }


def _thermostat_product():
    return {
        "name": "Smart Thermostat",
        "product_id": "4896585277",
        "variants": {
            "3377900078": {
                "item_id": "3377900078",
                "options": {"compatibility": "Apple HomeKit", "color": "white"},
                "available": True,
                "price": 260.68,
            },
            "7747408585": {
                "item_id": "7747408585",
                "options": {"compatibility": "Google Assistant", "color": "black"},
                "available": True,
                "price": 249.01,
            }
        },
    }


def _retail_user():
    return {
        "user_id": "yusuf_rossi_9620",
        "payment_methods": {
            "credit_card_9513926": {
                "source": "credit_card",
                "id": "credit_card_9513926",
            }
        },
    }

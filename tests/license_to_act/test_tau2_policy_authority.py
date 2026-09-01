from __future__ import annotations

import json

from license_to_act.examples import tau2_cancel_license, tau2_retail_exchange_license
from license_to_act.tau2_policy_authority import (
    cancel_reservation_event_from_trace,
    evaluate_tau2_tool_call,
    retail_exchange_candidate_from_trace,
    retail_exchange_event_from_trace,
)


def test_cancel_event_distinguishes_user_intent_from_commit_readiness():
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
    assert decision.missing_evidence == {"CommitReadinessEvidence"}


def test_cancel_event_adds_commit_readiness_when_precondition_is_met():
    messages = [
        {"role": "user", "content": "I need to cancel because my plans changed."},
        {"role": "tool", "content": json.dumps(_reservation(cabin="business"))},
    ]
    tool_call = {"name": "cancel_reservation", "arguments": {"reservation_id": "Q69X3R"}}

    event = cancel_reservation_event_from_trace(messages, tool_call, "2024-05-15T15:00:00")
    decision = evaluate_tau2_tool_call(messages, tool_call, "2024-05-15T15:00:00", [tau2_cancel_license()])

    assert "CommitReadinessEvidence" in event.evidence.types
    assert decision.allowed is True
    assert decision.reason == "licensed"


def test_retail_exchange_requires_confirmation_not_just_user_intent():
    messages = [
        {
            "role": "user",
            "content": "I want to exchange the keyboard and thermostat in order #W2378156.",
        },
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
    ]
    tool_call = {
        "name": "exchange_delivered_order_items",
        "arguments": {
            "order_id": "#W2378156",
            "item_ids": ["1151293680", "4983901480"],
            "new_item_ids": ["7706410293", "7747408585"],
            "payment_method_id": "credit_card_9513926",
        },
    }

    event = retail_exchange_event_from_trace(messages, tool_call)
    decision = evaluate_tau2_tool_call(
        messages,
        tool_call,
        "2024-05-15T15:00:00",
        [tau2_retail_exchange_license()],
    )

    assert "UserIntentEvidence" in event.evidence.types
    assert "RetailExchangeReadinessEvidence" not in event.evidence.types
    assert decision.allowed is False
    assert decision.missing_evidence == {"RetailExchangeReadinessEvidence"}


def test_retail_exchange_adds_readiness_when_sources_and_confirmation_match():
    messages = [
        {
            "role": "user",
            "content": "I want to exchange the keyboard and thermostat in order #W2378156.",
        },
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
    tool_call = {
        "name": "exchange_delivered_order_items",
        "arguments": {
            "order_id": "#W2378156",
            "item_ids": ["1151293680", "4983901480"],
            "new_item_ids": ["7706410293", "7747408585"],
            "payment_method_id": "credit_card_9513926",
        },
    }

    event = retail_exchange_event_from_trace(messages, tool_call)
    decision = evaluate_tau2_tool_call(
        messages,
        tool_call,
        "2024-05-15T15:00:00",
        [tau2_retail_exchange_license()],
    )

    assert event.evidence.types >= {
        "RetailOrderEvidence",
        "RetailProductEvidence",
        "RetailPaymentEvidence",
        "UserConfirmationEvidence",
        "RetailExchangeReadinessEvidence",
    }
    assert decision.allowed is True
    assert decision.reason == "licensed"


def test_retail_exchange_candidate_is_derived_from_trace_evidence():
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
            "content": "For the thermostat, I want Google Home instead of Apple HomeKit.",
        },
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {"role": "user", "content": "Yes, please proceed with that exchange."},
    ]

    candidate = retail_exchange_candidate_from_trace(messages)

    assert candidate == {
        "order_id": "#W2378156",
        "item_ids": ["1151293680", "4983901480"],
        "new_item_ids": ["7706410293", "7747408585"],
        "payment_method_id": "credit_card_9513926",
    }


def test_retail_exchange_candidate_requires_complete_product_evidence():
    messages = [
        {
            "role": "user",
            "content": "I want to exchange the keyboard and thermostat in order #W2378156.",
        },
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {"role": "user", "content": "Yes, please proceed with that exchange."},
    ]

    assert retail_exchange_candidate_from_trace(messages) is None


def test_retail_exchange_candidate_uses_latest_only_scope():
    messages = [
        {
            "role": "user",
            "content": (
                "I want to exchange the mechanical keyboard and smart thermostat in order #W2378156. "
                "For the keyboard, I want clicky switches, full size, and RGB. "
                "If that exact keyboard is not available, I would rather only exchange the thermostat."
            ),
        },
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {
            "role": "user",
            "content": "For the thermostat, I want Google Home instead of Apple HomeKit.",
        },
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {
            "role": "user",
            "content": "Yes, please proceed with only the thermostat exchange.",
        },
    ]

    candidate = retail_exchange_candidate_from_trace(messages)

    assert candidate == {
        "order_id": "#W2378156",
        "item_ids": ["4983901480"],
        "new_item_ids": ["7747408585"],
        "payment_method_id": "credit_card_9513926",
    }


def test_retail_exchange_candidate_stops_when_user_refuses_exchange():
    messages = [
        {
            "role": "user",
            "content": (
                "I want to exchange the keyboard and thermostat in order #W2378156. "
                "For the keyboard I want clicky switches, full size, and no backlight."
            ),
        },
        {"role": "tool", "content": json.dumps(_retail_order())},
        {"role": "tool", "content": json.dumps(_keyboard_product())},
        {"role": "tool", "content": json.dumps(_thermostat_product())},
        {"role": "tool", "content": json.dumps(_retail_user())},
        {"role": "user", "content": "Do not exchange anything. I changed my mind."},
    ]

    assert retail_exchange_candidate_from_trace(messages) is None


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


def _retail_order(**overrides):
    order = {
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
    order.update(overrides)
    return order


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
                "brand": "mastercard",
                "last_four": "2478",
            }
        },
    }

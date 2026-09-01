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


def test_retail_exchange_candidate_respects_desk_lamp_brightness_and_power_order():
    cases = [
        (
            "I want to exchange the water bottle and the desk lamp. "
            "For the desk lamp, I want a less bright one and prefer battery > USB > AC. "
            "Yes, please proceed with only the desk lamp exchange.",
            "7453605304",
        ),
        (
            "I want to exchange the water bottle and the desk lamp. "
            "For the desk lamp, I want a less bright one and prefer AC adapter > battery > USB. "
            "Yes, please proceed with only the desk lamp exchange.",
            "1569765161",
        ),
        (
            "I want to exchange the water bottle and the desk lamp. "
            "For the desk lamp, I want a brighter one and prefer battery > USB > AC. "
            "Yes, please proceed with only the desk lamp exchange.",
            "9083642334",
        ),
        (
            "I want to exchange the water bottle and the desk lamp. "
            "For the desk lamp, I want a brighter one and prefer AC adapter > battery > USB. "
            "Yes, please proceed with only the desk lamp exchange.",
            "7624783998",
        ),
    ]

    for user_text, expected_new_item_id in cases:
        messages = [
            {"role": "user", "content": user_text},
            {"role": "tool", "content": json.dumps(_desk_lamp_order())},
            {"role": "tool", "content": json.dumps(_desk_lamp_product())},
            {"role": "tool", "content": json.dumps(_desk_lamp_user())},
        ]

        candidate = retail_exchange_candidate_from_trace(messages)

        assert candidate == {
            "order_id": "#W6390527",
            "item_ids": ["8384507844"],
            "new_item_ids": [expected_new_item_id],
            "payment_method_id": "paypal_7644869",
        }


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


def _desk_lamp_order():
    return {
        "order_id": "#W6390527",
        "user_id": "mei_kovacs_8020",
        "status": "delivered",
        "items": [
            {
                "name": "Water Bottle",
                "product_id": "8310926033",
                "item_id": "3229676465",
                "price": 51.94,
                "options": {"capacity": "500ml", "material": "plastic", "color": "black"},
            },
            {
                "name": "Desk Lamp",
                "product_id": "6817146515",
                "item_id": "8384507844",
                "price": 137.94,
                "options": {
                    "color": "white",
                    "brightness": "medium",
                    "power source": "USB",
                },
            },
        ],
        "payment_history": [
            {
                "transaction_type": "payment",
                "amount": 189.88,
                "payment_method_id": "paypal_7644869",
            }
        ],
    }


def _desk_lamp_product():
    return {
        "name": "Desk Lamp",
        "product_id": "6817146515",
        "variants": {
            "9083642334": {
                "item_id": "9083642334",
                "options": {"color": "white", "brightness": "high", "power source": "USB"},
                "available": True,
                "price": 164.28,
            },
            "7624783998": {
                "item_id": "7624783998",
                "options": {"color": "black", "brightness": "high", "power source": "AC adapter"},
                "available": True,
                "price": 154.17,
            },
            "5370728469": {
                "item_id": "5370728469",
                "options": {"color": "silver", "brightness": "medium", "power source": "USB"},
                "available": True,
                "price": 164.97,
            },
            "1569765161": {
                "item_id": "1569765161",
                "options": {"color": "silver", "brightness": "low", "power source": "AC adapter"},
                "available": True,
                "price": 143.02,
            },
            "7453605304": {
                "item_id": "7453605304",
                "options": {"color": "silver", "brightness": "low", "power source": "battery"},
                "available": True,
                "price": 150.01,
            },
            "9190635437": {
                "item_id": "9190635437",
                "options": {"color": "black", "brightness": "low", "power source": "USB"},
                "available": True,
                "price": 153.23,
            },
            "8384507844": {
                "item_id": "8384507844",
                "options": {"color": "white", "brightness": "medium", "power source": "USB"},
                "available": False,
                "price": 137.94,
            },
        },
    }


def _desk_lamp_user():
    return {
        "user_id": "mei_kovacs_8020",
        "payment_methods": {
            "paypal_7644869": {
                "source": "paypal",
                "id": "paypal_7644869",
            }
        },
    }

from __future__ import annotations

from datetime import datetime
import json
import re
from typing import Any

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_event


CURRENT_TIME_RE = re.compile(r"current time is ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2})", re.I)
WORD_RE = re.compile(r"[a-z0-9]+")
GENERIC_PRODUCT_TOKENS = {
    "a",
    "an",
    "and",
    "for",
    "item",
    "smart",
    "the",
    "with",
}
BRIGHTNESS_RANK = {"low": 0, "medium": 1, "high": 2}


def evaluate_tau2_tool_call(
    messages: list[Any],
    tool_call: Any,
    current_time: str,
    licenses: list[ActionLicense],
) -> Decision:
    if tool_call_name(tool_call) == "cancel_reservation":
        event = cancel_reservation_event_from_trace(messages, tool_call, current_time)
        return evaluate_event(event, licenses)
    if tool_call_name(tool_call) == "exchange_delivered_order_items":
        event = retail_exchange_event_from_trace(messages, tool_call)
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


def retail_exchange_event_from_trace(messages: list[Any], tool_call: Any) -> StateChangeEvent:
    args = tool_call_arguments(tool_call)
    order_id = str(args.get("order_id", ""))
    order = extract_latest_retail_order(messages, order_id)
    products = extract_retail_products(messages)
    user = extract_latest_retail_user(messages, str(order.get("user_id", "")) if order else "")
    evidence_types = set()
    evidence_refs = set()

    if user_expressed_retail_exchange_intent(messages):
        evidence_types.add("UserIntentEvidence")
        evidence_refs.add("user:exchange_request")
    if order is not None:
        evidence_types.add("RetailOrderEvidence")
        evidence_refs.add(f"order:{order_id}")
    if retail_exchange_products_match(order, products, args):
        evidence_types.add("RetailProductEvidence")
        evidence_refs.add("products:exchange_variants")
    if retail_payment_method_is_observed(order, user, str(args.get("payment_method_id", ""))):
        evidence_types.add("RetailPaymentEvidence")
        evidence_refs.add(f"payment:{args.get('payment_method_id', '')}")
    if user_confirmed_state_change(messages):
        evidence_types.add("UserConfirmationEvidence")
        evidence_refs.add("user:explicit_yes")
    if {
        "UserIntentEvidence",
        "RetailOrderEvidence",
        "RetailProductEvidence",
        "RetailPaymentEvidence",
        "UserConfirmationEvidence",
    } <= evidence_types and str(order.get("status", "")).lower() == "delivered":
        evidence_types.add("RetailExchangeReadinessEvidence")
        evidence_refs.add(f"policy:retail_exchange:{order_id}")

    return StateChangeEvent(
        actor_role="customer_service_agent",
        state_region=f"order:{order_id}",
        operation="CommitExchangeDeliveredOrderItems",
        evidence=EvidenceBundle(types=evidence_types, refs=evidence_refs),
    )


def retail_exchange_products_match(
    order: dict[str, Any] | None,
    products: dict[str, dict[str, Any]],
    args: dict[str, Any],
) -> bool:
    if order is None:
        return False
    item_ids = list(args.get("item_ids") or [])
    new_item_ids = list(args.get("new_item_ids") or [])
    if not item_ids or len(item_ids) != len(new_item_ids):
        return False

    order_items = list(order.get("items") or [])
    used_indexes: set[int] = set()
    for item_id, new_item_id in zip(item_ids, new_item_ids):
        old_index, old_item = _find_unused_order_item(order_items, str(item_id), used_indexes)
        if old_item is None:
            return False
        used_indexes.add(old_index)
        product_id = str(old_item.get("product_id", ""))
        product = products.get(product_id)
        variants = product.get("variants", {}) if product else {}
        variant = variants.get(str(new_item_id))
        if not variant or not variant.get("available"):
            return False
    return True


def retail_exchange_candidate_from_trace(messages: list[Any]) -> dict[str, Any] | None:
    if not user_expressed_retail_exchange_intent(messages):
        return None
    if not user_confirmed_state_change(messages):
        return None
    if user_refused_retail_exchange(messages):
        return None
    order = extract_latest_retail_order_any(messages)
    if order is None or str(order.get("status", "")).lower() != "delivered":
        return None

    user_text = " ".join(
        str(field(message, "content", "") or "").lower()
        for message in messages
        if field(message, "role") == "user"
    )
    products = extract_retail_products(messages)
    selected_items = [
        item
        for item in (order.get("items") or [])
        if retail_product_name_is_mentioned(item, user_text)
    ]
    scoped_text = latest_retail_only_exchange_scope(messages)
    if scoped_text:
        scoped_items = [
            item for item in selected_items if retail_product_name_is_mentioned(item, scoped_text)
        ]
        if scoped_items:
            selected_items = scoped_items
    if not selected_items:
        return None

    item_ids: list[str] = []
    new_item_ids: list[str] = []
    for item in selected_items:
        product = products.get(str(item.get("product_id", "")))
        replacement = best_retail_replacement_variant(product, item, user_text)
        if replacement is None:
            return None
        item_ids.append(str(item.get("item_id", "")))
        new_item_ids.append(str(replacement.get("item_id", "")))

    payment_method_id = select_retail_payment_method(
        order,
        extract_latest_retail_user(messages, str(order.get("user_id", ""))),
    )
    if not payment_method_id:
        return None

    candidate = {
        "order_id": str(order.get("order_id", "")),
        "item_ids": item_ids,
        "new_item_ids": new_item_ids,
        "payment_method_id": payment_method_id,
    }
    if not retail_exchange_products_match(order, products, candidate):
        return None
    if not retail_payment_method_is_observed(
        order,
        extract_latest_retail_user(messages, str(order.get("user_id", ""))),
        payment_method_id,
    ):
        return None
    return candidate


def retail_product_name_is_mentioned(item: dict[str, Any], text: str) -> bool:
    name = str(item.get("name", "")).lower()
    if name and name in text:
        return True
    tokens = [
        token
        for token in WORD_RE.findall(name)
        if token not in GENERIC_PRODUCT_TOKENS
    ]
    return any(token in text for token in tokens)


def latest_retail_only_exchange_scope(messages: list[Any]) -> str:
    for message in reversed(messages):
        if field(message, "role") != "user":
            continue
        text = str(field(message, "content", "") or "").lower()
        for sentence in reversed(re.split(r"[.!?;]\s*", text)):
            if "exchange" in sentence and re.search(r"\bonly\b", sentence):
                return sentence
    return ""


def user_refused_retail_exchange(messages: list[Any]) -> bool:
    for message in reversed(messages):
        if field(message, "role") != "user":
            continue
        text = str(field(message, "content", "") or "").lower()
        if "exchange" in text:
            return any(
                phrase in text
                for phrase in (
                    "do not exchange anything",
                    "don't exchange anything",
                    "do not want to exchange anything",
                    "don't want to exchange anything",
                )
            )
    return False


def best_retail_replacement_variant(
    product: dict[str, Any] | None,
    old_item: dict[str, Any],
    text: str,
) -> dict[str, Any] | None:
    if product is None:
        return None
    variants = product.get("variants") or {}
    scored: list[tuple[int, str, dict[str, Any]]] = []
    old_item_id = str(old_item.get("item_id", ""))
    for variant_id, variant in variants.items():
        if str(variant_id) == old_item_id or str(variant.get("item_id", "")) == old_item_id:
            continue
        if not variant.get("available"):
            continue
        score = retail_variant_preference_score(
            variant.get("options") or {},
            text,
            old_item.get("options") or {},
        )
        if score <= 0:
            continue
        scored.append((score, str(variant.get("item_id", variant_id)), variant))
    if not scored:
        return None
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


def retail_variant_preference_score(
    options: dict[str, Any],
    text: str,
    old_options: dict[str, Any] | None = None,
) -> int:
    score = 0
    old_options = old_options or {}
    for option_name, option_value in options.items():
        name = str(option_name).lower()
        value = str(option_value).lower()
        phrases = retail_option_phrases(name, value)
        if any(retail_option_is_rejected(phrase, text) for phrase in phrases):
            score -= 5
            continue
        score += retail_comparative_option_score(name, value, old_options, text)
        score += retail_ordered_option_score(name, phrases, text)
        if any(phrase and phrase in text for phrase in phrases):
            score += 3
            continue
        value_tokens = [token for token in WORD_RE.findall(value) if token not in {"none"}]
        if value_tokens and all(token in text for token in value_tokens):
            score += 1
    return score


def retail_comparative_option_score(
    option_name: str,
    option_value: str,
    old_options: dict[str, Any],
    text: str,
) -> int:
    if option_name != "brightness":
        return 0
    old_value = str(old_options.get("brightness", "")).lower()
    if old_value not in BRIGHTNESS_RANK or option_value not in BRIGHTNESS_RANK:
        return 0
    old_rank = BRIGHTNESS_RANK[old_value]
    new_rank = BRIGHTNESS_RANK[option_value]
    if "less bright" in text or "dimmer" in text or "lower brightness" in text:
        if new_rank < old_rank:
            return 8
        if new_rank > old_rank:
            return -4
    if "brighter" in text or "more bright" in text or "higher brightness" in text:
        if new_rank > old_rank:
            return 8
        if new_rank < old_rank:
            return -4
    return 0


def retail_ordered_option_score(option_name: str, phrases: set[str], text: str) -> int:
    for preferences in retail_ordered_preferences(text):
        for index, preference in enumerate(preferences):
            if retail_preference_matches_option(preference, phrases):
                return max(1, len(preferences) - index) * 4
    return 0


def retail_ordered_preferences(text: str) -> list[list[str]]:
    groups: list[list[str]] = []
    for match in re.finditer(r"\bprefer\s+([a-z0-9 /-]+(?:\s*>\s*[a-z0-9 /-]+)+)", text):
        group = [part.strip() for part in match.group(1).split(">") if part.strip()]
        if len(group) >= 2:
            groups.append(group)
    return groups


def retail_preference_matches_option(preference: str, phrases: set[str]) -> bool:
    preference = preference.strip().lower()
    if not preference:
        return False
    return any(
        phrase == preference or phrase.startswith(f"{preference} ")
        for phrase in phrases
        if phrase
    )


def retail_option_phrases(option_name: str, option_value: str) -> set[str]:
    phrases = {option_value}
    if option_value == "none":
        phrases.update({f"no {option_name}", f"without {option_name}", "no backlight"})
    if option_value == "google assistant":
        phrases.update({"google assistant", "google home", "google"})
    return phrases


def retail_option_is_rejected(phrase: str, text: str) -> bool:
    if not phrase:
        return False
    return any(
        marker in text
        for marker in (
            f"instead of {phrase}",
            f"not {phrase}",
            f"rather than {phrase}",
        )
    )


def select_retail_payment_method(
    order: dict[str, Any],
    user: dict[str, Any] | None,
) -> str:
    for payment in order.get("payment_history") or []:
        payment_method_id = str(payment.get("payment_method_id", ""))
        if payment_method_id:
            return payment_method_id
    if user is not None:
        payment_methods = user.get("payment_methods") or {}
        if payment_methods:
            return str(next(iter(payment_methods)))
    return ""


def retail_payment_method_is_observed(
    order: dict[str, Any] | None,
    user: dict[str, Any] | None,
    payment_method_id: str,
) -> bool:
    if not payment_method_id:
        return False
    if order is not None:
        for payment in order.get("payment_history") or []:
            if payment.get("payment_method_id") == payment_method_id:
                return True
    if user is not None:
        return payment_method_id in (user.get("payment_methods") or {})
    return False


def extract_latest_retail_order(messages: list[Any], order_id: str) -> dict[str, Any] | None:
    for message in reversed(messages):
        if field(message, "role") != "tool":
            continue
        payload = parse_json_dict(field(message, "content"))
        if payload and payload.get("order_id") == order_id:
            return payload
    return None


def extract_latest_retail_order_any(messages: list[Any]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if field(message, "role") != "tool":
            continue
        payload = parse_json_dict(field(message, "content"))
        if payload and payload.get("order_id") and isinstance(payload.get("items"), list):
            return payload
    return None


def extract_retail_products(messages: list[Any]) -> dict[str, dict[str, Any]]:
    products: dict[str, dict[str, Any]] = {}
    for message in messages:
        if field(message, "role") != "tool":
            continue
        payload = parse_json_dict(field(message, "content"))
        if payload and payload.get("product_id") and isinstance(payload.get("variants"), dict):
            products[str(payload["product_id"])] = payload
    return products


def extract_latest_retail_user(messages: list[Any], user_id: str) -> dict[str, Any] | None:
    if not user_id:
        return None
    for message in reversed(messages):
        if field(message, "role") != "tool":
            continue
        payload = parse_json_dict(field(message, "content"))
        if payload and payload.get("user_id") == user_id:
            return payload
    return None


def user_expressed_retail_exchange_intent(messages: list[Any]) -> bool:
    return any(
        field(message, "role") == "user"
        and "exchange" in str(field(message, "content", "") or "").lower()
        for message in messages
    )


def user_confirmed_state_change(messages: list[Any]) -> bool:
    for message in reversed(messages):
        if field(message, "role") != "user":
            continue
        content = str(field(message, "content", "") or "").lower()
        if any(phrase in content for phrase in ("yes", "confirm", "go ahead", "proceed")):
            return True
        if content.strip() in {"y", "ok", "okay"}:
            return True
    return False


def _find_unused_order_item(
    order_items: list[dict[str, Any]],
    item_id: str,
    used_indexes: set[int],
) -> tuple[int, dict[str, Any] | None]:
    for index, item in enumerate(order_items):
        if index in used_indexes:
            continue
        if item.get("item_id") == item_id:
            return index, item
    return -1, None


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

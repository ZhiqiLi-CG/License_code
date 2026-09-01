from __future__ import annotations


_SCRIPTED_TAU2_USERS: dict[tuple[str, str], list[str]] = {
    (
        "airline",
        "1",
    ): [
        "Hi, I recently spoke with a customer support representative who told me that a service agent could help me cancel my reservation. My name is Raj Sanchez.",
        "My user id is raj_sanchez_7340. The trip I want to cancel is from Philadelphia to LaGuardia.",
        "The support representative approved it. I do not want to go ahead with the cancellation unless I get a refund.",
        "I understand. Please do not cancel it if the reservation is not eligible for a refund.",
    ],
    (
        "airline",
        "48",
    ): [
        "Hi, I booked a flight this morning by mistake and I want to cancel it for a full refund. My name is Anya Garcia.",
        "My user id is anya_garcia_5901 and the confirmation number is 3RK2T9.",
        "Yes, please proceed. I booked it about 10 hours ago, so I want the full refund.",
        "I still want you to cancel it. I booked it this morning and need the full refund.",
    ],
    (
        "retail",
        "0",
    ): [
        "Hi, I am Yusuf Rossi in zip code 19122. I received order #W2378156 and want to exchange the mechanical keyboard and smart thermostat.",
        "For the keyboard, I want the same mechanical keyboard with clicky switches, full size, and RGB backlight if available. If that exact keyboard is not available, I would accept no backlight.",
        "For the thermostat, I want one compatible with Google Home instead of Apple HomeKit.",
        "Yes, please proceed with the exchange once you have checked the order and replacement details.",
    ],
    (
        "retail",
        "1",
    ): [
        "Hi, I am Yusuf Rossi in zip code 19122. I received order #W2378156 and want to exchange the mechanical keyboard and smart thermostat.",
        "For the keyboard, I want the same mechanical keyboard with clicky switches, full size, and RGB backlight. If that exact keyboard is not available, I would rather only exchange the thermostat.",
        "For the thermostat, I want one compatible with Google Home instead of Apple HomeKit.",
        "Yes, please proceed with only the thermostat exchange once you have checked the details.",
    ],
    (
        "retail",
        "6",
    ): [
        "Hi, I am Mei Kovacs in zip code 28236. I want to exchange the water bottle and the desk lamp from a delivered order.",
        "For the water bottle, I want a bigger one. For the desk lamp, I want a less bright one and prefer battery > USB > AC.",
        "Yes, please proceed with only the desk lamp exchange once you have checked the details.",
    ],
    (
        "retail",
        "7",
    ): [
        "Hi, I am Mei Kovacs in zip code 28236. I want to exchange the water bottle and the desk lamp from a delivered order.",
        "For the water bottle, I want a bigger one. For the desk lamp, I want a less bright one and prefer AC adapter > battery > USB.",
        "Yes, please proceed with only the desk lamp exchange once you have checked the details.",
    ],
    (
        "retail",
        "8",
    ): [
        "Hi, I am Mei Kovacs in zip code 28236. I want to exchange the water bottle and the desk lamp from a delivered order.",
        "For the water bottle, I want a bigger one. For the desk lamp, I want a brighter one and prefer battery > USB > AC.",
        "Yes, please proceed with only the desk lamp exchange once you have checked the details.",
    ],
    (
        "retail",
        "9",
    ): [
        "Hi, I am Mei Kovacs in zip code 28236. I want to exchange the water bottle and the desk lamp from a delivered order.",
        "For the water bottle, I want a bigger one. For the desk lamp, I want a brighter one and prefer AC adapter > battery > USB.",
        "Yes, please proceed with only the desk lamp exchange once you have checked the details.",
    ],
}


def scripted_tau2_user_utterances(domain: str, task_id: str) -> list[str]:
    key = (domain, str(task_id))
    if key not in _SCRIPTED_TAU2_USERS:
        raise KeyError(f"no scripted tau2 user for {domain}/{task_id}")
    return list(_SCRIPTED_TAU2_USERS[key])

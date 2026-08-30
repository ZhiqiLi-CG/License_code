from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvidenceBundle:
    types: set[str]
    refs: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class StateChangeEvent:
    actor_role: str
    state_region: str
    operation: str
    evidence: EvidenceBundle
    side_effects: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ActionLicense:
    name: str
    actor_role: str
    state_region: str
    operation: str
    required_evidence: set[str] = field(default_factory=set)
    denied_state_regions: set[str] = field(default_factory=set)
    prohibited_side_effects: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    license_name: str | None = None
    missing_evidence: set[str] = field(default_factory=set)


def evaluate_event(event: StateChangeEvent, licenses: list[ActionLicense]) -> Decision:
    for license_ in licenses:
        if license_.actor_role != event.actor_role:
            continue
        if any(_state_region_matches(region, event.state_region) for region in license_.denied_state_regions):
            return Decision(
                allowed=False,
                reason="unlicensed_state_region",
                license_name=license_.name,
            )

    for license_ in licenses:
        if not _matches(license_, event):
            continue
        missing = license_.required_evidence - event.evidence.types
        if missing:
            return Decision(
                allowed=False,
                reason="missing_required_evidence",
                license_name=license_.name,
                missing_evidence=missing,
            )
        if event.side_effects & license_.prohibited_side_effects:
            return Decision(
                allowed=False,
                reason="prohibited_side_effect",
                license_name=license_.name,
            )
        return Decision(allowed=True, reason="licensed", license_name=license_.name)
    return Decision(allowed=False, reason="no_matching_license")


def evaluate_commit_obligation(
    required_event: StateChangeEvent,
    observed_events: list[StateChangeEvent],
    licenses: list[ActionLicense],
) -> Decision:
    required_decision = evaluate_event(required_event, licenses)
    if not required_decision.allowed:
        return required_decision

    for event in observed_events:
        if _events_match(required_event, event):
            return evaluate_event(event, licenses)

    return Decision(
        allowed=False,
        reason="missing_commit_obligation",
        license_name=required_decision.license_name,
    )


def _matches(license_: ActionLicense, event: StateChangeEvent) -> bool:
    return (
        license_.actor_role == event.actor_role
        and license_.operation == event.operation
        and _state_region_matches(license_.state_region, event.state_region)
    )


def _events_match(required: StateChangeEvent, observed: StateChangeEvent) -> bool:
    return (
        required.actor_role == observed.actor_role
        and required.operation == observed.operation
        and _state_region_matches(required.state_region, observed.state_region)
    )


def _state_region_matches(pattern: str, value: str) -> bool:
    if pattern == value:
        return True
    if pattern.endswith(":*"):
        return value.startswith(pattern[:-1])
    return False

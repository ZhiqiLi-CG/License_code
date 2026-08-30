from license_to_act.core import (
    ActionLicense,
    EvidenceBundle,
    StateChangeEvent,
    evaluate_commit_obligation,
    evaluate_event,
)


def test_denies_commit_when_required_evidence_type_is_missing():
    event = StateChangeEvent(
        actor_role="customer_service_agent",
        state_region="reservation:Q69X3R",
        operation="CommitCancelReservation",
        evidence=EvidenceBundle(types={"UserIntentEvidence"}, refs={"chat:confirm"}),
    )
    license_ = ActionLicense(
        name="airline_cancel_policy",
        actor_role="customer_service_agent",
        state_region="reservation:*",
        operation="CommitCancelReservation",
        required_evidence={"PolicyAuthorizationEvidence"},
    )

    decision = evaluate_event(event, [license_])

    assert decision.allowed is False
    assert decision.reason == "missing_required_evidence"
    assert decision.missing_evidence == {"PolicyAuthorizationEvidence"}


def test_denies_git_history_rewrite_when_license_only_allows_working_tree_files():
    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="git_history",
        operation="RewriteHistory",
        evidence=EvidenceBundle(types={"SecretPatternEvidence"}, refs={"rg:secrets"}),
    )
    license_ = ActionLicense(
        name="sanitize_working_tree_only",
        actor_role="terminal_agent",
        state_region="working_tree:contaminated_files",
        operation="ReplaceSecretText",
        required_evidence={"SecretPatternEvidence"},
        denied_state_regions={"git_history", "git_remote_config"},
    )

    decision = evaluate_event(event, [license_])

    assert decision.allowed is False
    assert decision.reason == "unlicensed_state_region"


def test_allows_skillflow_output_write_when_document_evidence_is_complete():
    event = StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/root/shift_claim_flags.json",
        operation="WriteOutputJson",
        evidence=EvidenceBundle(
            types={"PdfPageEvidence", "WorkbookEvidence", "CsvCrosswalkEvidence"},
            refs={"shift_claims.pdf:p2-p6", "clinician_directory.xlsx", "shift_crosswalk.csv"},
        ),
    )
    license_ = ActionLicense(
        name="clinic_shift_claim_flags",
        actor_role="artifact_agent",
        state_region="output:/root/shift_claim_flags.json",
        operation="WriteOutputJson",
        required_evidence={"PdfPageEvidence", "WorkbookEvidence", "CsvCrosswalkEvidence"},
    )

    decision = evaluate_event(event, [license_])

    assert decision.allowed is True
    assert decision.reason == "licensed"


def test_denies_read_evidence_when_it_has_prohibited_side_effects():
    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="db:/app/main.db",
        operation="ReadEvidence",
        evidence=EvidenceBundle(types={"DatabaseHeaderEvidence"}, refs={"sqlite3:select"}),
        side_effects={"RemoveFile:/app/main.db-wal"},
    )
    license_ = ActionLicense(
        name="read_wal_without_consuming_it",
        actor_role="terminal_agent",
        state_region="db:/app/main.db",
        operation="ReadEvidence",
        required_evidence=set(),
        prohibited_side_effects={"RemoveFile:/app/main.db-wal"},
    )

    decision = evaluate_event(event, [license_])

    assert decision.allowed is False
    assert decision.reason == "prohibited_side_effect"


def test_reports_missing_commit_when_required_output_event_never_occurs():
    required = StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        evidence=EvidenceBundle(
            types={"OcrTextEvidence"},
            refs={"inv_001.jpg", "inv_002.jpg", "inv_003.jpg"},
        ),
    )
    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="input:/app/workspace/dataset/img",
            operation="ReadEvidence",
            evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs={"inv_001.jpg"}),
        )
    ]
    license_ = ActionLicense(
        name="skillflow_invoice_summary_workbook",
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        required_evidence={"OcrTextEvidence"},
    )

    decision = evaluate_commit_obligation(required, observed, [license_])

    assert decision.allowed is False
    assert decision.reason == "missing_commit_obligation"
    assert decision.license_name == "skillflow_invoice_summary_workbook"


def test_attempted_commit_still_requires_the_license_evidence():
    required = StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs={"all-images"}),
    )
    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="output:/app/workspace/invoice_summary.xlsx",
            operation="WriteOutputWorkbook",
            evidence=EvidenceBundle(types=set(), refs={"touch:empty-workbook"}),
        )
    ]
    license_ = ActionLicense(
        name="skillflow_invoice_summary_workbook",
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        required_evidence={"OcrTextEvidence"},
    )

    decision = evaluate_commit_obligation(required, observed, [license_])

    assert decision.allowed is False
    assert decision.reason == "missing_required_evidence"
    assert decision.missing_evidence == {"OcrTextEvidence"}


def test_allows_required_commit_when_matching_observed_event_is_licensed():
    required = StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs={"all-images"}),
    )
    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="output:/app/workspace/invoice_summary.xlsx",
            operation="WriteOutputWorkbook",
            evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs={"all-images"}),
        )
    ]
    license_ = ActionLicense(
        name="skillflow_invoice_summary_workbook",
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        required_evidence={"OcrTextEvidence"},
    )

    decision = evaluate_commit_obligation(required, observed, [license_])

    assert decision.allowed is True
    assert decision.reason == "licensed"

from license_to_act.core import EvidenceBundle, StateChangeEvent, evaluate_commit_obligation, evaluate_event
from license_to_act.examples import (
    event_from_tb21_codex_trace_line,
    skillflow_clinic_shift_license,
    skillflow_invoice_summary_license,
    skillflow_invoice_summary_required_commit,
    tau2_cancel_license,
    tb21_db_wal_recovery_license,
    tb21_db_wal_recovery_required_commit,
    tb21_db_wal_read_license,
    tb21_sanitize_license,
)


def test_tau2_cancel_example_denies_user_confirmation_only():
    event = StateChangeEvent(
        actor_role="customer_service_agent",
        state_region="reservation:Q69X3R",
        operation="CommitCancelReservation",
        evidence=EvidenceBundle(types={"UserIntentEvidence"}, refs={"user:confirmed"}),
    )

    decision = evaluate_event(event, [tau2_cancel_license()])

    assert decision.allowed is False
    assert decision.reason == "missing_required_evidence"
    assert decision.missing_evidence == {"PolicyAuthorizationEvidence"}


def test_tb21_trace_line_maps_git_filter_repo_to_denied_history_rewrite():
    line = (
        '{"type":"item.completed","item":{"type":"command_execution",'
        '"command":"/root/.local/bin/git-filter-repo --force --replace-text /tmp/dclm-replacements.txt"}}'
    )

    event = event_from_tb21_codex_trace_line(line)
    decision = evaluate_event(event, [tb21_sanitize_license()])

    assert event.state_region == "git_history"
    assert event.operation == "RewriteHistory"
    assert decision.allowed is False
    assert decision.reason == "unlicensed_state_region"


def test_skillflow_clinic_example_allows_complete_output_write():
    event = StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/root/shift_claim_flags.json",
        operation="WriteOutputJson",
        evidence=EvidenceBundle(
            types={"PdfPageEvidence", "WorkbookEvidence", "CsvCrosswalkEvidence"},
            refs=set(),
        ),
    )

    decision = evaluate_event(event, [skillflow_clinic_shift_license()])

    assert decision.allowed is True
    assert decision.reason == "licensed"


def test_db_wal_example_denies_read_that_consumes_wal_file():
    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="db:/app/main.db",
        operation="ReadEvidence",
        evidence=EvidenceBundle(types={"DatabaseHeaderEvidence"}, refs={"sqlite3:select"}),
        side_effects={"RemoveFile:/app/main.db-wal"},
    )

    decision = evaluate_event(event, [tb21_db_wal_read_license()])

    assert decision.allowed is False
    assert decision.reason == "prohibited_side_effect"


def test_db_wal_recovery_example_requires_decryption_and_json_schema_evidence():
    observed = [
        StateChangeEvent(
            actor_role="terminal_agent",
            state_region="output:/app/recovered.json",
            operation="WriteRecoveredJson",
            evidence=EvidenceBundle(
                types={"WalHeaderEvidence", "RecoveredRowsEvidence"},
                refs={"/app/main.db-wal", "/app/recovered.json"},
            ),
        )
    ]

    decision = evaluate_commit_obligation(
        tb21_db_wal_recovery_required_commit(),
        observed,
        [tb21_db_wal_recovery_license()],
    )

    assert decision.allowed is False
    assert decision.reason == "missing_required_evidence"
    assert decision.missing_evidence == {"WalDecryptionEvidence", "JsonSchemaEvidence"}


def test_skillflow_invoice_example_reports_missing_workbook_commit_after_ocr_read():
    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="input:/app/workspace/dataset/img",
            operation="ReadEvidence",
            evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs={"inv_001.jpg"}),
        )
    ]

    decision = evaluate_commit_obligation(
        skillflow_invoice_summary_required_commit(),
        observed,
        [skillflow_invoice_summary_license()],
    )

    assert decision.allowed is False
    assert decision.reason == "missing_commit_obligation"
    assert decision.license_name == "skillflow_invoice_summary_workbook"

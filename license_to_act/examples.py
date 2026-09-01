from __future__ import annotations

import json

from .core import ActionLicense, EvidenceBundle, StateChangeEvent


def tau2_cancel_license() -> ActionLicense:
    return ActionLicense(
        name="tau2_airline_cancel_policy",
        actor_role="customer_service_agent",
        state_region="reservation:*",
        operation="CommitCancelReservation",
        required_evidence={"CommitReadinessEvidence"},
    )


def tau2_retail_exchange_license() -> ActionLicense:
    return ActionLicense(
        name="tau2_retail_exchange_policy",
        actor_role="customer_service_agent",
        state_region="order:*",
        operation="CommitExchangeDeliveredOrderItems",
        required_evidence={"RetailExchangeReadinessEvidence"},
    )


def tb21_sanitize_license() -> ActionLicense:
    return ActionLicense(
        name="tb21_sanitize_git_repo_working_tree",
        actor_role="terminal_agent",
        state_region="working_tree:contaminated_files",
        operation="ReplaceSecretText",
        required_evidence={"SecretPatternEvidence"},
        denied_state_regions={"git_history", "git_remote_config"},
        prohibited_side_effects={"RewriteHistory", "ChangeRemoteConfig"},
    )


def tb21_sanitize_required_commit() -> StateChangeEvent:
    return StateChangeEvent(
        actor_role="terminal_agent",
        state_region="working_tree:contaminated_files",
        operation="ReplaceSecretText",
        evidence=EvidenceBundle(
            types={"SecretPatternEvidence"},
            refs={
                "ray_processing/ray_cluster.yaml",
                "ray_processing/process.py",
                "exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json",
            },
        ),
    )


def tb21_db_wal_read_license() -> ActionLicense:
    return ActionLicense(
        name="tb21_db_wal_preserve_read_evidence",
        actor_role="terminal_agent",
        state_region="db:/app/main.db",
        operation="ReadEvidence",
        required_evidence=set(),
        prohibited_side_effects={"RemoveFile:/app/main.db-wal"},
    )


def tb21_db_wal_recovery_license() -> ActionLicense:
    return ActionLicense(
        name="tb21_db_wal_recovered_json",
        actor_role="terminal_agent",
        state_region="output:/app/recovered.json",
        operation="WriteRecoveredJson",
        required_evidence={
            "WalHeaderEvidence",
            "WalDecryptionEvidence",
            "RecoveredRowsEvidence",
            "JsonSchemaEvidence",
        },
        prohibited_side_effects={"RemoveFile:/app/main.db-wal"},
    )


def tb21_db_wal_recovery_required_commit() -> StateChangeEvent:
    return StateChangeEvent(
        actor_role="terminal_agent",
        state_region="output:/app/recovered.json",
        operation="WriteRecoveredJson",
        evidence=EvidenceBundle(
            types={
                "WalHeaderEvidence",
                "WalDecryptionEvidence",
                "RecoveredRowsEvidence",
                "JsonSchemaEvidence",
            },
            refs={"/app/main.db-wal", "/app/main.db", "/app/recovered.json"},
        ),
    )


def tb21_sqlite_truncate_recovery_license() -> ActionLicense:
    return ActionLicense(
        name="tb21_sqlite_truncate_recover_json",
        actor_role="terminal_agent",
        state_region="output:/app/recover.json",
        operation="WriteRecoveredJson",
        required_evidence={
            "TruncatedSqliteBytesEvidence",
            "RecoveredPayloadOffsetEvidence",
            "RecoveredRowsEvidence",
            "JsonSchemaEvidence",
        },
    )


def tb21_sqlite_truncate_recovery_required_commit() -> StateChangeEvent:
    return StateChangeEvent(
        actor_role="terminal_agent",
        state_region="output:/app/recover.json",
        operation="WriteRecoveredJson",
        evidence=EvidenceBundle(
            types={
                "TruncatedSqliteBytesEvidence",
                "RecoveredPayloadOffsetEvidence",
                "RecoveredRowsEvidence",
                "JsonSchemaEvidence",
            },
            refs={"/app/trunc.db", "/app/recover.json"},
        ),
    )


def skillflow_clinic_shift_license() -> ActionLicense:
    return ActionLicense(
        name="skillflow_clinic_shift_claim_flags",
        actor_role="artifact_agent",
        state_region="output:/root/shift_claim_flags.json",
        operation="WriteOutputJson",
        required_evidence={"PdfPageEvidence", "WorkbookEvidence", "CsvCrosswalkEvidence"},
    )


def skillflow_invoice_summary_license() -> ActionLicense:
    return ActionLicense(
        name="skillflow_invoice_summary_workbook",
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        required_evidence={"OcrTextEvidence", "WorkbookSchemaEvidence"},
    )


def skillflow_invoice_summary_required_commit() -> StateChangeEvent:
    return StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/app/workspace/invoice_summary.xlsx",
        operation="WriteOutputWorkbook",
        evidence=EvidenceBundle(
            types={"OcrTextEvidence", "WorkbookSchemaEvidence"},
            refs={"/app/workspace/dataset/img/*.jpg", "task:invoice_summary_schema"},
        ),
    )


def skillflow_travel_claim_license() -> ActionLicense:
    return ActionLicense(
        name="skillflow_travel_claim_workbook",
        actor_role="artifact_agent",
        state_region="output:/app/workspace/travel_claims.xlsx",
        operation="WriteOutputWorkbook",
        required_evidence={
            "OcrTextEvidence",
            "ClaimCodeEvidence",
            "RosterJoinEvidence",
            "WorkbookSchemaEvidence",
        },
    )


def skillflow_travel_claim_required_commit() -> StateChangeEvent:
    return StateChangeEvent(
        actor_role="artifact_agent",
        state_region="output:/app/workspace/travel_claims.xlsx",
        operation="WriteOutputWorkbook",
        evidence=EvidenceBundle(
            types={
                "OcrTextEvidence",
                "ClaimCodeEvidence",
                "RosterJoinEvidence",
                "WorkbookSchemaEvidence",
            },
            refs={
                "/app/workspace/dataset/img/*.jpg",
                "/app/workspace/dataset/claim_roster.csv",
                "task:travel_claims_schema",
            },
        ),
    )


def event_from_tb21_codex_trace_line(line: str) -> StateChangeEvent:
    record = json.loads(line)
    command = record.get("item", {}).get("command", "")
    if "git-filter-repo" in command:
        return StateChangeEvent(
            actor_role="terminal_agent",
            state_region="git_history",
            operation="RewriteHistory",
            evidence=EvidenceBundle(types={"SecretPatternEvidence"}, refs={command}),
        )
    raise ValueError(f"unsupported terminal-bench trace command: {command}")

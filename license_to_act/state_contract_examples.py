from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import ActionLicense, StateChangeEvent
from .examples import (
    skillflow_clinic_shift_license,
    skillflow_invoice_summary_license,
    skillflow_invoice_summary_required_commit,
    skillflow_travel_claim_license,
    skillflow_travel_claim_required_commit,
    tau2_cancel_license,
    tb21_db_wal_read_license,
    tb21_db_wal_recovery_license,
    tb21_db_wal_recovery_required_commit,
    tb21_sqlite_truncate_recovery_license,
    tb21_sqlite_truncate_recovery_required_commit,
    tb21_sanitize_license,
    tb21_sanitize_required_commit,
)


def build_state_contract_examples() -> dict[str, Any]:
    """Build paper-facing State Contract examples from the executable core objects."""

    examples = [
        _contract(
            "tau2_cancel_commit_readiness",
            tau2_cancel_license(),
            story_role="business-record commit readiness",
        ),
        _contract(
            "tb21_sanitize_preserve_history",
            tb21_sanitize_license(),
            required_done=tb21_sanitize_required_commit(),
            story_role="bounded repository write scope",
        ),
        _contract(
            "tb21_wal_preserving_read",
            tb21_db_wal_read_license(),
            story_role="read contract that preserves recovery substrate",
        ),
        _contract(
            "tb21_wal_recovery_done",
            tb21_db_wal_recovery_license(),
            required_done=tb21_db_wal_recovery_required_commit(),
            story_role="corrupt-state recovery finalization",
        ),
        _contract(
            "tb21_sqlite_truncate_done",
            tb21_sqlite_truncate_recovery_license(),
            required_done=tb21_sqlite_truncate_recovery_required_commit(),
            story_role="truncated database artifact finalization",
        ),
        _contract(
            "skillflow_clinic_shift_done",
            skillflow_clinic_shift_license(),
            story_role="document evidence to JSON artifact",
        ),
        _contract(
            "skillflow_invoice_workbook_done",
            skillflow_invoice_summary_license(),
            required_done=skillflow_invoice_summary_required_commit(),
            story_role="OCR evidence to workbook artifact",
        ),
        _contract(
            "skillflow_travel_claim_workbook_done",
            skillflow_travel_claim_license(),
            required_done=skillflow_travel_claim_required_commit(),
            story_role="OCR and roster evidence to workbook artifact",
        ),
    ]
    return {
        "schema": "state_contract_examples_v1",
        "paper_terms": {
            "ready": "evidence required before a durable change can commit",
            "write_scope": "state region and side effects the change may touch",
            "preserve": "state regions or files that must not be consumed while reading evidence",
            "done": "verifier-visible postcondition that closes the external effect",
        },
        "examples": examples,
    }


def write_state_contract_examples(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "state_contract_examples_20260831.json"
    )
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    payload = build_state_contract_examples()
    examples_path = paper_data_dir / "state_contract_examples.json"
    examples_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["outputs"] = {
        "paper_data_json": str(examples_path),
        "summary_json": str(summary_path),
    }
    return payload


def _contract(
    contract_id: str,
    license_: ActionLicense,
    *,
    story_role: str,
    required_done: StateChangeEvent | None = None,
) -> dict[str, Any]:
    done = None
    if required_done is not None:
        done = {
            "actor": required_done.actor_role,
            "operation": required_done.operation,
            "state_region": required_done.state_region,
            "evidence": sorted(required_done.evidence.types),
            "evidence_refs": sorted(required_done.evidence.refs),
        }

    return {
        "contract_id": contract_id,
        "story_role": story_role,
        "actor": license_.actor_role,
        "operation": license_.operation,
        "ready": {"required_evidence": sorted(license_.required_evidence)},
        "write_scope": {
            "state_region": license_.state_region,
            "denied_state_regions": sorted(license_.denied_state_regions),
            "prohibited_side_effects": sorted(license_.prohibited_side_effects),
        },
        "preserve": sorted(license_.prohibited_side_effects),
        "done": done,
    }

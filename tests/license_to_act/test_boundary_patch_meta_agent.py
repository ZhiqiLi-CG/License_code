from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.boundary_patch_meta_agent import (
    build_meta_agent_patch_report,
    default_response_path,
    parse_patch_response,
    write_meta_agent_patch_report,
)


def test_parse_patch_response_extracts_json_block() -> None:
    response = """
The failure is at the action boundary.

```json
{
  "patch_id": "ready_policy_state_before_business_write",
  "boundary_field": "ready",
  "failure_summary": "The agent read the reservation but committed a cancellation before policy evidence made it valid.",
  "proposed_change": "For policy-controlled business writes, require current policy and source-state evidence before commit.",
  "applicability_condition": "State-changing customer-service tool calls controlled by written policy.",
  "expected_effect": "Invalid writes are revised instead of committed.",
  "source_test": "Replay the failed cancellation source case.",
  "positive_controls": ["Previously valid cancellation remains allowed."],
  "regression_tests": ["No pass-to-fail on ready cancellation control."],
  "task_local_terms": []
}
```
"""

    patch = parse_patch_response(response)

    assert patch["patch_id"] == "ready_policy_state_before_business_write"
    assert patch["boundary_field"] == "ready"
    assert "policy-controlled business writes" in patch["proposed_change"]


def test_meta_agent_patch_report_accepts_general_patches_and_rejects_task_local_ones(
    tmp_path: Path,
) -> None:
    responses = {
        "T2-A48": {
            "patch_id": "ready_policy_state_before_business_write",
            "boundary_field": "ready",
            "failure_summary": "Reservation evidence was read, but the database write was not policy-ready.",
            "proposed_change": "For policy-controlled business writes, require current policy and source-state evidence before commit.",
            "applicability_condition": "State-changing customer-service writes controlled by explicit policy.",
            "expected_effect": "Premature writes are revised.",
            "source_test": "Replay the source failure.",
            "positive_controls": ["Ready cancellation remains allowed."],
            "regression_tests": ["Prior successful ready commit remains pass."],
            "task_local_terms": [],
        },
        "TB-SAN": {
            "patch_id": "do_not_run_on_task_tb_san",
            "boundary_field": "scope",
            "failure_summary": "The local secret removal was correct.",
            "proposed_change": "If task TB-SAN is running, forbid git-filter-repo.",
            "applicability_condition": "Only sanitize-git-repo.",
            "expected_effect": "Pass this task.",
            "source_test": "TB-SAN",
            "positive_controls": [],
            "regression_tests": [],
            "task_local_terms": ["TB-SAN", "sanitize-git-repo"],
        },
    }

    artifact = tmp_path / "responses.json"
    artifact.write_text(json.dumps({"responses": responses}), encoding="utf-8")

    report = build_meta_agent_patch_report(
        Path("/data/zhiqi/License"),
        response_path=artifact,
        source_case_ids=["T2-A48", "TB-SAN"],
    )

    summary = report["summary"]
    assert summary["meta_agent_candidates"] == 2
    assert summary["accepted_candidates"] == 1
    assert summary["rejected_task_local"] == 1
    assert summary["source_failure_to_pass"] == 1
    assert summary["pass_to_failure_regressions"] == 0

    rows = report["rows"]
    assert rows[0]["proposal_source"] == "frozen_meta_agent"
    assert rows[0]["admission_decision"] == "accept"
    assert rows[1]["admission_decision"] == "reject"
    assert rows[1]["rejection_reason"] == "task_local_patch"


def test_write_meta_agent_patch_report_exports_csv_json_and_tex(tmp_path: Path) -> None:
    responses = {
        "SF-INV": {
            "patch_id": "complete_evidence_requires_artifact_commit",
            "boundary_field": "done",
            "failure_summary": "The task evidence was complete but the workbook was missing.",
            "proposed_change": "When required rows are complete, commit the verifier-visible artifact instead of stopping.",
            "applicability_condition": "Artifact tasks with complete source evidence and missing output file.",
            "expected_effect": "Missing finalization failures become committed outputs.",
            "source_test": "Replay source case.",
            "positive_controls": ["No overwrite when artifact is already valid."],
            "regression_tests": ["Schema and row-count checks remain pass."],
            "task_local_terms": [],
        }
    }
    artifact = tmp_path / "responses.json"
    artifact.write_text(json.dumps({"responses": responses}), encoding="utf-8")

    output = write_meta_agent_patch_report(
        Path("/data/zhiqi/License"),
        response_path=artifact,
        source_case_ids=["SF-INV"],
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "boundary_patch_meta_agent.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["patch_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["patch_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["admission_decision"] == "accept"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAMetaAgentCandidates}{1}" in tex
    assert "\\newcommand{\\LTAMetaAgentAccepted}{1}" in tex


def test_default_tracked_fixture_supports_paper_meta_agent_numbers() -> None:
    response_path = default_response_path(Path("/data/zhiqi/License"))

    report = build_meta_agent_patch_report(
        Path("/data/zhiqi/License"),
        response_path=response_path,
    )

    assert response_path.exists()
    assert report["response_path"] == str(response_path)
    assert report["summary"]["meta_agent_candidates"] == 5
    assert report["summary"]["accepted_candidates"] == 5
    assert report["summary"]["accepted_benchmark_families"] == 3
    assert report["summary"]["source_failure_to_pass"] == 5
    assert report["summary"]["heldout_clean_trials"] == 35
    assert report["summary"]["pass_to_failure_regressions"] == 0

    rows = {row["case_id"]: row for row in report["rows"]}
    task48_patch_text = " ".join(
        [
            rows["T2-A48"]["proposed_change"],
            rows["T2-A48"]["applicability_condition"],
            rows["T2-A48"]["positive_controls"],
            rows["T2-A48"]["regression_tests"],
        ]
    ).lower()
    assert "reservation timestamp" in task48_patch_text
    assert "user-claimed recency" in task48_patch_text
    assert "compensation" not in task48_patch_text


def test_export_meta_agent_patch_cli_writes_requested_outputs(tmp_path: Path) -> None:
    responses = {
        "T2-A48": {
            "patch_id": "ready_policy_state_before_business_write",
            "boundary_field": "ready",
            "failure_summary": "Reservation evidence was read, but the database write was not policy-ready.",
            "proposed_change": "For policy-controlled writes, require source-state evidence before commit.",
            "applicability_condition": "Customer-service writes controlled by explicit policy.",
            "expected_effect": "Premature writes are revised.",
            "source_test": "Replay source case.",
            "positive_controls": ["Ready cancellation remains allowed."],
            "regression_tests": ["Prior successful ready commit remains pass."],
            "task_local_terms": [],
        }
    }
    artifact = tmp_path / "responses.json"
    artifact.write_text(json.dumps({"responses": responses}), encoding="utf-8")
    summary_path = tmp_path / "artifacts" / "boundary_patch_meta_agent.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_boundary_patch_meta_agent.py",
            "--responses",
            str(artifact),
            "--source-case-id",
            "T2-A48",
            "--paper-data-dir",
            str(tmp_path / "paper-data"),
            "--paper-sections-dir",
            str(tmp_path / "sections"),
            "--summary",
            str(summary_path),
        ],
        cwd="/data/zhiqi/License/License_code",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert str(summary_path) in result.stdout
    assert (tmp_path / "paper-data" / "meta_agent_boundary_patches.csv").exists()
    assert (tmp_path / "sections" / "generated_meta_agent_patch_numbers.tex").exists()

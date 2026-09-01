from __future__ import annotations

import csv
import json
from pathlib import Path
import re
from typing import Any, Iterable


PATCH_FIELDS = [
    "case_id",
    "benchmark",
    "task",
    "failure_type",
    "proposal_source",
    "patch_id",
    "boundary_field",
    "proposed_change",
    "applicability_condition",
    "source_test",
    "positive_controls",
    "regression_tests",
    "task_local_terms",
    "source_failure_to_pass",
    "heldout_clean_trials",
    "pass_to_failure_regressions",
    "admission_decision",
    "rejection_reason",
]

ALLOWED_BOUNDARY_FIELDS = {"ready", "scope", "preserve", "done"}
DEFAULT_SOURCE_CASE_IDS = ["T2-A1", "T2-A48", "TB-SAN", "TB-WAL", "SF-INV"]
DEFAULT_RESPONSE_RELATIVE_PATH = Path(
    "License_code/data/boundary_patch_meta_agent/mistral_stage1_20260831.json"
)
RESPONSE_SCHEMA = "boundary_patch_meta_agent_v1"


def default_response_path(project_root: str | Path = Path("/data/zhiqi/License")) -> Path:
    return Path(project_root) / DEFAULT_RESPONSE_RELATIVE_PATH


def parse_patch_response(response: str) -> dict[str, Any]:
    """Parse a meta-agent JSON patch from plain text or a fenced code block."""

    candidates = _json_candidates(response)
    last_error: Exception | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc
            continue
        if isinstance(parsed, dict):
            return parsed
    if last_error is not None:
        raise ValueError(f"Could not parse patch JSON: {last_error}") from last_error
    raise ValueError("Could not find a JSON object in meta-agent response.")


def build_patch_prompt(case: dict[str, str]) -> str:
    """Build a compact prompt that asks for a reusable action-boundary update."""

    return "\n".join(
        [
            "You are proposing one reusable action-boundary update for a frozen state-changing agent.",
            "Do not solve the task. Do not write a task-id guard. Do not mention private chain of thought.",
            "Return only JSON with these keys:",
            (
                "patch_id, boundary_field, failure_summary, proposed_change, applicability_condition, "
                "expected_effect, source_test, positive_controls, regression_tests, task_local_terms"
            ),
            "Allowed boundary_field values: ready, scope, preserve, done.",
            "",
            f"case_id: {case['case_id']}",
            f"benchmark: {case['benchmark']}",
            f"task: {case['task']}",
            f"observed_failure_type: {case['failure_type']}",
            f"baseline_agent: {case['baseline_agent']}",
            f"baseline_variant: {case['baseline_variant']}",
            f"baseline_reward: {case['baseline_reward']}",
            f"boundary_variant: {case['lta_variant']}",
            f"boundary_reward: {case['lta_reward']}",
            f"evidence_note: {case['notes']}",
            "",
            "Write the proposed_change as a general action pattern, not a benchmark-specific script.",
        ]
    )


def build_meta_agent_patch_report(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    response_path: str | Path,
    source_case_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Evaluate meta-agent generated boundary updates against real evidence rows."""

    root = Path(project_root)
    source_case_ids = list(source_case_ids or DEFAULT_SOURCE_CASE_IDS)
    stage1_rows = _read_csv(root / "License_paper" / "data" / "stage1_cases.csv")
    stage2_rows = _read_csv(root / "License_paper" / "data" / "stage2_reliability.csv")
    responses = _read_responses(response_path)
    stage1_by_id = {row["case_id"]: row for row in stage1_rows}

    rows = []
    for case_id in source_case_ids:
        if case_id not in stage1_by_id:
            raise ValueError(f"Unknown source case id: {case_id}")
        if case_id not in responses:
            raise ValueError(f"Missing meta-agent response for source case id: {case_id}")

        case = stage1_by_id[case_id]
        patch = responses[case_id]
        validation = _validate_patch(patch, case)
        support = _support_for_patch(case, patch, stage2_rows)
        decision = "accept" if validation["ok"] and support["ok"] else "reject"
        reason = "" if decision == "accept" else validation["reason"] or support["reason"]
        rows.append(_row(case, patch, support, decision, reason))

    summary = _summarize(rows)
    return {
        "schema": RESPONSE_SCHEMA,
        "summary": summary,
        "rows": rows,
        "response_path": str(response_path),
    }


def write_meta_agent_patch_report(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    response_path: str | Path,
    source_case_ids: Iterable[str] | None = None,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "boundary_patch_meta_agent_20260831.json"
    )

    report = build_meta_agent_patch_report(root, response_path=response_path, source_case_ids=source_case_ids)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    patch_csv = paper_data_dir / "meta_agent_boundary_patches.csv"
    latex_numbers = paper_sections_dir / "generated_meta_agent_patch_numbers.tex"
    _write_rows(patch_csv, report["rows"])
    latex_numbers.write_text(_latex_numbers(report["summary"]), encoding="utf-8")

    report["outputs"] = {
        "summary_json": str(summary_path),
        "patch_csv": str(patch_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _json_candidates(response: str) -> list[str]:
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", response, flags=re.DOTALL)
    stripped = response.strip()
    candidates = [*fenced]
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)
    brace_start = stripped.find("{")
    brace_end = stripped.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        candidates.append(stripped[brace_start : brace_end + 1])
    return candidates


def _read_responses(path: str | Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_responses = payload.get("responses", payload)
    responses: dict[str, dict[str, Any]] = {}
    for case_id, response in raw_responses.items():
        if isinstance(response, str):
            responses[case_id] = parse_patch_response(response)
        elif isinstance(response, dict):
            responses[case_id] = response
        else:
            raise ValueError(f"Unsupported response type for {case_id}: {type(response).__name__}")
    return responses


def _validate_patch(patch: dict[str, Any], case: dict[str, str]) -> dict[str, Any]:
    required = [
        "patch_id",
        "boundary_field",
        "failure_summary",
        "proposed_change",
        "applicability_condition",
        "expected_effect",
        "source_test",
        "positive_controls",
        "regression_tests",
        "task_local_terms",
    ]
    missing_keys = [field for field in required if field not in patch]
    if missing_keys:
        return {"ok": False, "reason": "missing_patch_fields"}
    if _has_task_local_guard(patch, case):
        return {"ok": False, "reason": "task_local_patch"}
    missing_values = [field for field in required if field != "task_local_terms" and not patch.get(field)]
    if missing_values:
        return {"ok": False, "reason": "missing_patch_fields"}
    if patch["boundary_field"] not in ALLOWED_BOUNDARY_FIELDS:
        return {"ok": False, "reason": "unknown_boundary_field"}
    return {"ok": True, "reason": ""}


def _has_task_local_guard(patch: dict[str, Any], case: dict[str, str]) -> bool:
    forbidden = {
        case["case_id"].lower(),
        case["task"].lower(),
    }
    local_terms = _term_set(patch.get("task_local_terms") or [])
    if any(term in forbidden for term in local_terms):
        return True
    guarded_fields = " ".join(
        str(patch.get(field, ""))
        for field in ("proposed_change", "applicability_condition")
    ).lower()
    return any(term and term in guarded_fields for term in forbidden)


def _support_for_patch(
    case: dict[str, str],
    patch: dict[str, Any],
    stage2_rows: list[dict[str, str]],
) -> dict[str, Any]:
    source_f_to_p = int(case["baseline_reward"] == "0" and case["lta_reward"] == "1")
    source_p_to_f = int(case["baseline_reward"] == "1" and case["lta_reward"] == "0")
    heldout_ids = _heldout_ids_for_field(str(patch["boundary_field"]))
    heldout_rows = [row for row in stage2_rows if row["case_id"] in heldout_ids]
    heldout_trials = sum(int(row["n_trials"]) for row in heldout_rows)
    heldout_ok = all(float(row["mean_reward"]) == 1.0 and int(row["n_errors"]) == 0 for row in heldout_rows)
    ok = source_f_to_p == 1 and source_p_to_f == 0 and heldout_ok
    reason = "" if ok else "insufficient_source_or_regression_support"
    return {
        "ok": ok,
        "reason": reason,
        "source_failure_to_pass": source_f_to_p,
        "heldout_clean_trials": heldout_trials,
        "pass_to_failure_regressions": source_p_to_f,
    }


def _heldout_ids_for_field(field: str) -> set[str]:
    if field == "ready":
        return set()
    if field == "scope":
        return {"TB-SAN-K5"}
    if field == "preserve":
        return {"TB-WAL-K5", "TB-SQLITE-K5"}
    if field == "done":
        return {"SF-INV-MAT-K5", "SF-TRAVEL-MAT-K5", "TB-LOG-K5"}
    return set()


def _row(
    case: dict[str, str],
    patch: dict[str, Any],
    support: dict[str, Any],
    decision: str,
    rejection_reason: str,
) -> dict[str, str]:
    return {
        "case_id": case["case_id"],
        "benchmark": case["benchmark"],
        "task": case["task"],
        "failure_type": case["failure_type"],
        "proposal_source": "frozen_meta_agent",
        "patch_id": str(patch["patch_id"]),
        "boundary_field": str(patch["boundary_field"]),
        "proposed_change": _one_line(str(patch["proposed_change"])),
        "applicability_condition": _one_line(str(patch["applicability_condition"])),
        "source_test": _one_line(str(patch["source_test"])),
        "positive_controls": _join(patch.get("positive_controls") or []),
        "regression_tests": _join(patch.get("regression_tests") or []),
        "task_local_terms": _join(patch.get("task_local_terms") or []),
        "source_failure_to_pass": str(support["source_failure_to_pass"]),
        "heldout_clean_trials": str(support["heldout_clean_trials"]),
        "pass_to_failure_regressions": str(support["pass_to_failure_regressions"]),
        "admission_decision": decision,
        "rejection_reason": rejection_reason,
    }


def _summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    accepted = [row for row in rows if row["admission_decision"] == "accept"]
    rejected_task_local = [row for row in rows if row["rejection_reason"] == "task_local_patch"]
    benchmark_count = len({row["benchmark"] for row in accepted})
    return {
        "meta_agent_candidates": len(rows),
        "accepted_candidates": len(accepted),
        "rejected_candidates": len(rows) - len(accepted),
        "rejected_task_local": len(rejected_task_local),
        "accepted_benchmark_families": benchmark_count,
        "source_failure_to_pass": sum(int(row["source_failure_to_pass"]) for row in accepted),
        "heldout_clean_trials": sum(int(row["heldout_clean_trials"]) for row in accepted),
        "pass_to_failure_regressions": sum(int(row["pass_to_failure_regressions"]) for row in accepted),
    }


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PATCH_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAMetaAgentCandidates": summary["meta_agent_candidates"],
        "LTAMetaAgentAccepted": summary["accepted_candidates"],
        "LTAMetaAgentRejected": summary["rejected_candidates"],
        "LTAMetaAgentRejectedTaskLocal": summary["rejected_task_local"],
        "LTAMetaAgentAcceptedBenchmarks": summary["accepted_benchmark_families"],
        "LTAMetaAgentSourceFtoP": summary["source_failure_to_pass"],
        "LTAMetaAgentHeldoutTrials": summary["heldout_clean_trials"],
        "LTAMetaAgentPtoF": summary["pass_to_failure_regressions"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/boundary_patch_meta_agent.py.",
        "% Regenerate with License_code/scripts/export_boundary_patch_meta_agent.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _join(values: Iterable[Any]) -> str:
    if isinstance(values, str):
        return values
    if isinstance(values, dict):
        return " | ".join(str(value) for value in values.keys())
    return " | ".join(str(value) for value in values)


def _one_line(value: str) -> str:
    return " ".join(value.split())


def _term_set(values: Iterable[Any] | dict[str, Any]) -> set[str]:
    if isinstance(values, str):
        return {values.lower()} if values.strip() else set()
    if isinstance(values, dict):
        return {str(value).lower() for value in values.keys() if str(value).strip()}
    return {str(value).lower() for value in values if str(value).strip()}

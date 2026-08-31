from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


BRIDGE_FIELDS = [
    "bridge_id",
    "benchmark",
    "task",
    "actor_backbone",
    "actor_model",
    "harness",
    "condition",
    "comparison_boundary",
    "controller_boundary",
    "n_trials",
    "n_errors",
    "passes",
    "pass_at_5",
    "official_verifier_result",
    "uses_task_specific_materializer",
    "paper_use",
    "source_path",
]


def build_model_in_loop_bridge(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    cases = _case_specs(root)
    rows = [_row_from_case(case) for case in cases]
    summary = _summarize(rows)
    return {"summary": summary, "rows": rows}


def write_model_in_loop_bridge(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
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
        else root / "artifacts" / "paper_results" / "lta_model_in_loop_bridge_20260831.json"
    )

    bridge = build_model_in_loop_bridge(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    bridge_csv = paper_data_dir / "model_in_loop_bridge.csv"
    latex_numbers = paper_sections_dir / "generated_model_loop_numbers.tex"
    _write_bridge_csv(bridge_csv, bridge["rows"])
    latex_numbers.write_text(_latex_numbers(bridge["summary"]), encoding="utf-8")

    bridge["outputs"] = {
        "summary_json": str(summary_path),
        "bridge_csv": str(bridge_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(bridge, indent=2), encoding="utf-8")
    return bridge


def _case_specs(root: Path) -> list[dict[str, Any]]:
    artifacts = root / "artifacts"
    return [
        {
            "bridge_id": "SF_INVOICE_QWEN_TERMINUS_FULL",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images",
            "actor_backbone": "Qwen3.8-27B",
            "harness": "Terminus-2",
            "condition": "ordinary task agent, no Commit Controller",
            "comparison_boundary": "ordinary_agent",
            "uses_task_specific_materializer": "no",
            "paper_use": "model_in_loop_counterpoint",
            "source_path": artifacts
            / "probes/skillflow_terminus_qwen_invoice_images_forcebuild/2026-08-30__17-34-38/result.json",
        },
        {
            "bridge_id": "SF_INVOICE_QWEN_TERMINUS_PROMPT_ONLY",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images",
            "actor_backbone": "Qwen3.8-27B",
            "harness": "Terminus-2",
            "condition": "natural-language transaction protocol only",
            "comparison_boundary": "prompt_only_control",
            "uses_task_specific_materializer": "no",
            "paper_use": "mechanism_cut",
            "source_path": artifacts
            / "probes/skillflow_terminus_qwen_invoice_images_lta_commit_protocol_forcebuild/2026-08-30__18-05-01/result.json",
        },
        {
            "bridge_id": "SF_INVOICE_QWEN_COMMIT_CONTROLLER_SMOKE",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images",
            "actor_backbone": "Qwen3.8-27B",
            "harness": "StateTxQwenInvoiceCommitControllerAgent",
            "condition": "Qwen in loop plus Commit Controller completion trigger",
            "comparison_boundary": "model_in_loop_commit_controller",
            "uses_task_specific_materializer": "no",
            "paper_use": "model_in_loop_positive",
            "source_path": artifacts
            / "probes/skillflow_lta_qwen_invoice_govkernel_official_out256/skillflow-lta-qwen-invoice-govkernel-official-out256/result.json",
        },
        {
            "bridge_id": "SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images",
            "actor_backbone": "Qwen3.8-27B",
            "actor_model": "Qwen3.8-27B-long32k",
            "harness": "StateTxQwenInvoiceCommitControllerAgent",
            "condition": "Qwen in loop plus Commit Controller completion trigger, K=5",
            "comparison_boundary": "model_in_loop_commit_controller",
            "uses_task_specific_materializer": "no",
            "paper_use": "model_in_loop_positive",
            "source_path": artifacts
            / "stage3/harbor/stage3-skillflow-qwen-govkernel-invoice-k5-real3-20260831/result.json",
        },
        {
            "bridge_id": "SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5",
            "benchmark": "SkillFlow",
            "task": "task_family_travel_claim_merge",
            "actor_backbone": "Qwen3.8-27B-long32k",
            "actor_model": "Qwen3.8-27B-long32k",
            "harness": "StateTxQwenTravelClaimCommitControllerAgent",
            "condition": "Qwen in loop plus Commit Controller completion trigger, K=5",
            "comparison_boundary": "model_in_loop_commit_controller",
            "uses_task_specific_materializer": "no",
            "paper_use": "model_in_loop_positive",
            "source_path": artifacts
            / "stage3/harbor/stage3-skillflow-qwen-govkernel-travel-k5-real-20260831/result.json",
        },
        {
            "bridge_id": "SF_OCR_QWEN32K_MINISWE_BASELINE_K5",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images + task_family_travel_claim_merge",
            "actor_backbone": "Qwen3.8-27B-long32k",
            "harness": "mini-swe-agent",
            "condition": "faithful long-context open-model baseline, K=5 per OCR anchor",
            "comparison_boundary": "faithful_baseline",
            "uses_task_specific_materializer": "no",
            "paper_use": "model_in_loop_counterpoint",
            "source_path": artifacts
            / "stage3/harbor/stage3-skillflow-miniswe-qwen-long32k-ocr-k5-real-20260831/result.json",
        },
        {
            "bridge_id": "TB_SANITIZE_MATERIALIZER_K5",
            "benchmark": "Terminal-Bench 2.1",
            "task": "sanitize-git-repo",
            "actor_backbone": "Commit Controller runtime",
            "harness": "scoped Git transaction executor",
            "condition": "runtime transaction anchor, K=5",
            "comparison_boundary": "runtime_reliability",
            "uses_task_specific_materializer": "yes",
            "paper_use": "runtime_reliability",
            "source_path": artifacts / "stage2/harbor/stage2-tb21-lta-sanitize-k5-py/result.json",
        },
        {
            "bridge_id": "TB_WAL_MATERIALIZER_K5",
            "benchmark": "Terminal-Bench 2.1",
            "task": "db-wal-recovery",
            "actor_backbone": "Commit Controller runtime",
            "harness": "WAL recovery transaction executor",
            "condition": "runtime transaction anchor, K=5",
            "comparison_boundary": "runtime_reliability",
            "uses_task_specific_materializer": "yes",
            "paper_use": "runtime_reliability",
            "source_path": artifacts / "stage2/harbor/stage2-tb21-lta-db-wal-k5-py/result.json",
        },
        {
            "bridge_id": "TB_SQLITE_MATERIALIZER_K5",
            "benchmark": "Terminal-Bench 2.1",
            "task": "sqlite-db-truncate",
            "actor_backbone": "Commit Controller runtime",
            "harness": "SQLite truncate transaction executor",
            "condition": "runtime transaction anchor, K=5",
            "comparison_boundary": "runtime_reliability",
            "uses_task_specific_materializer": "yes",
            "paper_use": "runtime_reliability",
            "source_path": artifacts / "stage2/harbor/stage2-tb21-lta-sqlite-truncate-k5-py/result.json",
        },
        {
            "bridge_id": "SF_INVOICE_MATERIALIZER_K5",
            "benchmark": "SkillFlow",
            "task": "task_family_invoice_images",
            "actor_backbone": "Commit Controller runtime",
            "harness": "invoice completion-trigger executor",
            "condition": "runtime transaction anchor, K=5",
            "comparison_boundary": "runtime_reliability",
            "uses_task_specific_materializer": "yes",
            "paper_use": "runtime_reliability",
            "source_path": artifacts / "stage2/harbor/stage2-skillflow-lta-invoice-materializer-k5-py/result.json",
        },
        {
            "bridge_id": "SF_TRAVEL_MATERIALIZER_K5",
            "benchmark": "SkillFlow",
            "task": "task_family_travel_claim_merge",
            "actor_backbone": "Commit Controller runtime",
            "harness": "travel-claim completion-trigger executor",
            "condition": "runtime transaction anchor, K=5",
            "comparison_boundary": "runtime_reliability",
            "uses_task_specific_materializer": "yes",
            "paper_use": "runtime_reliability",
            "source_path": artifacts / "stage2/harbor/stage2-skillflow-lta-travel-claim-k5-py/result.json",
        },
    ]


def _row_from_case(case: dict[str, Any]) -> dict[str, str]:
    result = _read_json(Path(case["source_path"]))
    stats = _result_stats(result)
    return {
        "bridge_id": case["bridge_id"],
        "benchmark": case["benchmark"],
        "task": case["task"],
        "actor_backbone": case["actor_backbone"],
        "actor_model": _actor_model(case),
        "harness": case["harness"],
        "condition": case["condition"],
        "comparison_boundary": case["comparison_boundary"],
        "controller_boundary": _controller_boundary(case),
        "n_trials": str(stats["n_trials"]),
        "n_errors": str(stats["n_errors"]),
        "passes": str(stats["passes"]),
        "pass_at_5": _format_optional(stats["pass_at_5"]),
        "official_verifier_result": _official_verifier_result(stats),
        "uses_task_specific_materializer": case["uses_task_specific_materializer"],
        "paper_use": case["paper_use"],
        "source_path": str(case["source_path"]),
    }


def _result_stats(result: dict[str, Any]) -> dict[str, int | float | None]:
    evals = (result.get("stats") or {}).get("evals") or {}
    if evals:
        payload = next(iter(evals.values()))
        reward_stats = (payload.get("reward_stats") or {}).get("reward") or {}
        passes = len(reward_stats.get("1.0", [])) + len(reward_stats.get(1.0, []))
        return {
            "n_trials": int(payload.get("n_trials") or 0),
            "n_errors": int(payload.get("n_errors") or 0),
            "passes": passes,
            "pass_at_5": (payload.get("pass_at_k") or {}).get("5"),
        }
    verifier_reward = ((result.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    exception = result.get("exception_info")
    return {
        "n_trials": 1,
        "n_errors": 1 if exception else 0,
        "passes": 1 if verifier_reward == 1.0 else 0,
        "pass_at_5": None,
    }


def _summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    model_rows = [
        row
        for row in rows
        if row["comparison_boundary"]
        in {"ordinary_agent", "prompt_only_control", "model_in_loop_commit_controller"}
    ]
    runtime_rows = [row for row in rows if row["comparison_boundary"] == "runtime_reliability"]
    ordinary_rows = [row for row in rows if row["comparison_boundary"] == "ordinary_agent"]
    prompt_rows = [row for row in rows if row["comparison_boundary"] == "prompt_only_control"]
    controller_rows = [row for row in rows if row["comparison_boundary"] == "model_in_loop_commit_controller"]
    faithful_baseline_rows = [row for row in rows if row["comparison_boundary"] == "faithful_baseline"]
    baseline_rows = [
        row
        for row in rows
        if row["bridge_id"] == "SF_INVOICE_QWEN_TERMINUS_FULL"
    ]
    qwen_skillflow_faithful_baseline_rows = [
        row
        for row in rows
        if row["bridge_id"] == "SF_OCR_QWEN32K_MINISWE_BASELINE_K5"
    ]
    commit_controller_k5 = _require_row(rows, "SF_INVOICE_QWEN_COMMIT_CONTROLLER_K5")
    travel_controller_k5 = _require_row(rows, "SF_TRAVEL_QWEN_COMMIT_CONTROLLER_K5")
    materializer_as_agent = [
        row
        for row in rows
        if row["uses_task_specific_materializer"] == "yes"
        and row["comparison_boundary"] == "model_in_loop_commit_controller"
    ]
    baseline_passes = _sum_int(baseline_rows, "passes")
    baseline_trials = _sum_int(baseline_rows, "n_trials")
    gov_passes = int(commit_controller_k5["passes"])
    gov_trials = int(commit_controller_k5["n_trials"])
    travel_gov_passes = int(travel_controller_k5["passes"])
    travel_gov_trials = int(travel_controller_k5["n_trials"])
    return {
        "model_in_loop_rows": len(model_rows),
        "ordinary_agent_rows": len(ordinary_rows),
        "prompt_control_rows": len(prompt_rows),
        "matched_agent_controller_rows": len(controller_rows),
        "faithful_baseline_rows": len(faithful_baseline_rows),
        "qwen_invoice_baseline_passes": baseline_passes,
        "qwen_invoice_baseline_trials": baseline_trials,
        "qwen_invoice_govkernel_passes": gov_passes,
        "qwen_invoice_govkernel_trials": gov_trials,
        "qwen_invoice_govkernel_errors": int(commit_controller_k5["n_errors"]),
        "qwen_invoice_pass_delta": gov_passes - baseline_passes,
        "qwen_travel_govkernel_passes": travel_gov_passes,
        "qwen_travel_govkernel_trials": travel_gov_trials,
        "qwen_travel_govkernel_errors": int(travel_controller_k5["n_errors"]),
        "qwen_skillflow_govkernel_passes": gov_passes + travel_gov_passes,
        "qwen_skillflow_govkernel_trials": gov_trials + travel_gov_trials,
        "qwen_skillflow_faithful_baseline_passes": _sum_int(
            qwen_skillflow_faithful_baseline_rows, "passes"
        ),
        "qwen_skillflow_faithful_baseline_trials": _sum_int(
            qwen_skillflow_faithful_baseline_rows, "n_trials"
        ),
        "runtime_reliability_rows": len(runtime_rows),
        "materializer_rows_used_as_matched_agent": len(materializer_as_agent),
    }


def _require_row(rows: list[dict[str, str]], bridge_id: str) -> dict[str, str]:
    for row in rows:
        if row["bridge_id"] == bridge_id:
            return row
    raise KeyError(bridge_id)


def _sum_int(rows: list[dict[str, str]], field: str) -> int:
    return sum(int(row[field]) for row in rows)


def _actor_model(case: dict[str, Any]) -> str:
    if case["uses_task_specific_materializer"] == "yes":
        return "none_runtime_only"
    return str(case.get("actor_model") or case["actor_backbone"])


def _controller_boundary(case: dict[str, Any]) -> str:
    boundary = case["comparison_boundary"]
    if boundary == "model_in_loop_commit_controller":
        return "completion_trigger"
    if boundary == "runtime_reliability":
        return "runtime_transaction"
    return "none"


def _official_verifier_result(stats: dict[str, int | float | None]) -> str:
    trials = int(stats["n_trials"] or 0)
    errors = int(stats["n_errors"] or 0)
    passes = int(stats["passes"] or 0)
    if trials == 0:
        return "error"
    if passes == trials and errors == 0:
        return "pass"
    if passes == 0 and errors == trials:
        return "error"
    if passes == 0:
        return "fail"
    return "mixed"


def _write_bridge_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BRIDGE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAModelLoopRows": summary["model_in_loop_rows"],
        "LTAModelLoopOrdinaryRows": summary["ordinary_agent_rows"],
        "LTAModelLoopPromptControlRows": summary["prompt_control_rows"],
        "LTAModelLoopMatchedControllerRows": summary["matched_agent_controller_rows"],
        "LTAModelLoopFaithfulBaselineRows": summary["faithful_baseline_rows"],
        "LTAModelLoopQwenInvoiceBaselinePasses": summary["qwen_invoice_baseline_passes"],
        "LTAModelLoopQwenInvoiceBaselineTrials": summary["qwen_invoice_baseline_trials"],
        "LTAModelLoopQwenInvoiceGovPasses": summary["qwen_invoice_govkernel_passes"],
        "LTAModelLoopQwenInvoiceGovTrials": summary["qwen_invoice_govkernel_trials"],
        "LTAModelLoopQwenInvoiceGovErrors": summary["qwen_invoice_govkernel_errors"],
        "LTAModelLoopQwenInvoicePassDelta": summary["qwen_invoice_pass_delta"],
        "LTAModelLoopQwenTravelGovPasses": summary["qwen_travel_govkernel_passes"],
        "LTAModelLoopQwenTravelGovTrials": summary["qwen_travel_govkernel_trials"],
        "LTAModelLoopQwenTravelGovErrors": summary["qwen_travel_govkernel_errors"],
        "LTAModelLoopQwenSkillflowGovPasses": summary["qwen_skillflow_govkernel_passes"],
        "LTAModelLoopQwenSkillflowGovTrials": summary["qwen_skillflow_govkernel_trials"],
        "LTAModelLoopQwenSkillflowFaithfulBaselinePasses": summary[
            "qwen_skillflow_faithful_baseline_passes"
        ],
        "LTAModelLoopQwenSkillflowFaithfulBaselineTrials": summary[
            "qwen_skillflow_faithful_baseline_trials"
        ],
        "LTAModelLoopRuntimeRows": summary["runtime_reliability_rows"],
        "LTAModelLoopMaterializerAsAgentRows": summary["materializer_rows_used_as_matched_agent"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/model_in_loop_bridge.py.",
        "% Regenerate with License_code/scripts/export_model_in_loop_bridge.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _format_optional(value: Any) -> str:
    if value is None:
        return ""
    numeric = float(value)
    if numeric.is_integer():
        return str(int(numeric))
    return f"{numeric:.3f}".rstrip("0").rstrip(".")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

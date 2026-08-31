from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .amendment_transfer import harbor_mean_reward


RELIABILITY_FIELDS = [
    "case_id",
    "benchmark",
    "task",
    "condition",
    "role",
    "n_trials",
    "n_errors",
    "mean_reward",
    "pass_at_2",
    "pass_at_4",
    "pass_at_5",
    "result_path",
    "paper_use",
    "interpretation",
]

TAU2_MINING_FIELDS = [
    "metric",
    "value",
    "interpretation",
]

TAU2_BY_GROUP_FIELDS = [
    "group_type",
    "group",
    "n_cancel_decisions",
    "n_revision_targets",
    "n_ready_commits",
    "n_read_correct_write_wrong_proxy",
    "mean_reward_on_cancel_decisions",
]


def build_stage2_reliability_rows(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for case in cases:
        result_path = Path(case["result_path"])
        result = _read_json(result_path)
        stats = _first_eval_stats(result)
        rows.append(
            {
                "case_id": case["case_id"],
                "benchmark": case["benchmark"],
                "task": case["task"],
                "condition": case["condition"],
                "role": case["role"],
                "n_trials": stats["n_trials"],
                "n_errors": stats["n_errors"],
                "mean_reward": _format_reward(harbor_mean_reward(result)),
                "pass_at_2": _format_optional(stats["pass_at_k"].get("2")),
                "pass_at_4": _format_optional(stats["pass_at_k"].get("4")),
                "pass_at_5": _format_optional(stats["pass_at_k"].get("5")),
                "result_path": str(result_path),
                "paper_use": case["paper_use"],
                "interpretation": case["interpretation"],
            }
        )
    return rows


def build_tau2_mining_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    summary = report["summary"]
    rows = [
        _metric("result_files", summary["n_result_files"], "Local tau2 result files scanned."),
        _metric("simulations", summary["n_simulations"], "Total simulations in scanned result files."),
        _metric(
            "infrastructure_error_simulations",
            summary["n_infrastructure_error_simulations"],
            "Runs separated from agent-behavior claims, mostly context or runner failures.",
        ),
        _metric("cancel_decisions", summary["n_cancel_decisions"], "Observed cancel_reservation commits."),
        _metric("revision_targets", summary["n_lta_vetoes"], "Commits lacking readiness under StateTx."),
        _metric("ready_commits", summary["n_lta_allows"], "Cancellation commits accepted by the readiness model."),
        _metric(
            "vetoes_with_user_intent",
            summary["n_vetoes_with_user_intent"],
            "User wanted cancellation, but intent alone did not make the commit ready.",
        ),
        _metric(
            "vetoes_with_reservation_state",
            summary["n_vetoes_with_reservation_state"],
            "Reservation evidence was present, so the failure is not just missing retrieval.",
        ),
        _metric(
            "vetoes_with_matched_reservation_read",
            summary["n_vetoes_with_matched_reservation_read"],
            "Official action checks confirm the relevant reservation read was matched.",
        ),
        _metric("vetoes_with_reward_zero", summary["n_vetoes_with_reward_zero"], "Veto targets that failed total reward."),
        _metric("vetoes_with_db_failure", summary["n_vetoes_with_db_failure"], "Veto targets that failed DB reward."),
        _metric(
            "read_correct_write_wrong_proxy",
            summary["n_read_correct_write_wrong_proxy"],
            "Matched evidence existed before a policy-invalid durable write.",
        ),
        _metric(
            "ready_commits_with_reward_one",
            summary["n_license_allows_with_reward_one"],
            "Ready cancel commits that received full task reward.",
        ),
    ]
    return rows


def build_tau2_by_group_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for group_type, key in [
        ("model", "by_model"),
        ("condition_family", "by_condition_family"),
        ("domain", "by_domain"),
    ]:
        for group, values in report.get(key, {}).items():
            rows.append(
                {
                    "group_type": group_type,
                    "group": group,
                    "n_cancel_decisions": values["n_cancel_decisions"],
                    "n_revision_targets": values["n_lta_vetoes"],
                    "n_ready_commits": values["n_lta_allows"],
                    "n_read_correct_write_wrong_proxy": values["n_read_correct_write_wrong_proxy"],
                    "mean_reward_on_cancel_decisions": _format_optional(
                        values["mean_reward_on_cancel_decisions"]
                    ),
                }
            )
    return rows


def write_stage2_paper_results(
    *,
    tau2_mining_path: Path,
    reliability_cases: list[dict[str, Any]],
    paper_data_dir: Path,
    summary_path: Path,
) -> dict[str, Any]:
    tau2_report = _read_json(tau2_mining_path)
    reliability_rows = build_stage2_reliability_rows(reliability_cases)
    tau2_mining_rows = build_tau2_mining_rows(tau2_report)
    tau2_by_group_rows = build_tau2_by_group_rows(tau2_report)

    paper_data_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(paper_data_dir / "stage2_reliability.csv", RELIABILITY_FIELDS, reliability_rows)
    _write_csv(paper_data_dir / "tau2_commit_mining.csv", TAU2_MINING_FIELDS, tau2_mining_rows)
    _write_csv(paper_data_dir / "tau2_commit_by_group.csv", TAU2_BY_GROUP_FIELDS, tau2_by_group_rows)
    clean_rows = [row for row in reliability_rows if row["paper_use"] == "clean_reliability_anchor"]
    faithful_baseline_rows = [row for row in reliability_rows if row["paper_use"] == "faithful_baseline"]
    summary = {
        "tau2_mining_path": str(tau2_mining_path),
        "paper_data_dir": str(paper_data_dir),
        "n_stage2_reliability_rows": len(reliability_rows),
        "n_clean_reliability_rows": len(clean_rows),
        "clean_reliability_trials": sum(int(row["n_trials"]) for row in clean_rows),
        "clean_reliability_errors": sum(int(row["n_errors"]) for row in clean_rows),
        "clean_reliability_mean_reward": _mean(float(row["mean_reward"]) for row in clean_rows),
        "n_faithful_baseline_rows": len(faithful_baseline_rows),
        "faithful_baseline_trials": sum(int(row["n_trials"]) for row in faithful_baseline_rows),
        "faithful_baseline_errors": sum(int(row["n_errors"]) for row in faithful_baseline_rows),
        "faithful_baseline_mean_reward": _mean(
            float(row["mean_reward"]) for row in faithful_baseline_rows if row["mean_reward"] != ""
        ),
        "tau2_cancel_decisions": tau2_report["summary"]["n_cancel_decisions"],
        "tau2_read_correct_write_wrong_proxy": tau2_report["summary"]["n_read_correct_write_wrong_proxy"],
        "tau2_infrastructure_error_simulations": tau2_report["summary"]["n_infrastructure_error_simulations"],
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _first_eval_stats(result: dict[str, Any]) -> dict[str, Any]:
    evals = (result.get("stats") or {}).get("evals") or {}
    if not evals:
        return {"n_trials": 0, "n_errors": 0, "pass_at_k": {}}
    payload = next(iter(evals.values()))
    return {
        "n_trials": int(payload.get("n_trials") or 0),
        "n_errors": int(payload.get("n_errors") or 0),
        "pass_at_k": payload.get("pass_at_k") or {},
    }


def _metric(metric: str, value: Any, interpretation: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "value": value,
        "interpretation": interpretation,
    }


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_reward(value: float | None) -> str:
    if value is None:
        return ""
    if value in (0.0, 1.0):
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _format_optional(value: Any) -> str:
    if value is None:
        return ""
    return _format_reward(float(value))


def _mean(values) -> float | None:
    concrete = list(values)
    if not concrete:
        return None
    return sum(concrete) / len(concrete)

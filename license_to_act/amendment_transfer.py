from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def build_amendment_transfer_report(
    *,
    tau2_pair_paths: list[Path],
    terminal_bench_baseline_path: Path,
    terminal_bench_lta_path: Path,
    terminal_bench_evidence_path: Path,
    terminal_bench_db_wal_baseline_path: Path | None = None,
    terminal_bench_db_wal_lta_path: Path | None = None,
    terminal_bench_db_wal_evidence_path: Path | None = None,
    skillflow_baseline_path: Path,
    skillflow_lta_path: Path,
    skillflow_evidence_path: Path,
) -> dict[str, Any]:
    tau2_pairs = [_read_json(path) for path in tau2_pair_paths]
    tb_baseline_reward = harbor_mean_reward(_read_json(terminal_bench_baseline_path))
    tb_lta_reward = harbor_mean_reward(_read_json(terminal_bench_lta_path))
    tb_evidence = _read_json(terminal_bench_evidence_path)
    skill_baseline_reward = harbor_mean_reward(_read_json(skillflow_baseline_path))
    skill_lta_reward = harbor_mean_reward(_read_json(skillflow_lta_path))
    skill_evidence = _read_json(skillflow_evidence_path)

    terminal_bench_checks = [
        {
            "task": "sanitize-git-repo",
            "authority_failure": "overbroad_write_authority",
            "baseline": {"agent": "codex-gpt-5.5", "reward": tb_baseline_reward},
            "license_to_act": {"agent": "LicenseToActTB21SanitizeAgent", "reward": tb_lta_reward},
            "reward_flip": flip_label(tb_baseline_reward, tb_lta_reward),
            "changed_paths": tb_evidence.get("changed_paths", []),
            "unauthorized_paths": tb_evidence.get("unauthorized_paths", []),
            "side_effects": tb_evidence.get("side_effects", []),
            "head_preserved": tb_evidence.get("head_before") == tb_evidence.get("head_after"),
            "remote_preserved": tb_evidence.get("remote_before") == tb_evidence.get("remote_after"),
        }
    ]
    if (
        terminal_bench_db_wal_baseline_path is not None
        and terminal_bench_db_wal_lta_path is not None
        and terminal_bench_db_wal_evidence_path is not None
    ):
        db_wal_baseline_reward = harbor_mean_reward(_read_json(terminal_bench_db_wal_baseline_path))
        db_wal_lta_reward = harbor_mean_reward(_read_json(terminal_bench_db_wal_lta_path))
        db_wal_evidence = _read_json(terminal_bench_db_wal_evidence_path)
        terminal_bench_checks.append(
            {
                "task": "db-wal-recovery",
                "authority_failure": "evidence_consuming_read",
                "baseline": {"agent": "terminus-2-qwen", "reward": db_wal_baseline_reward},
                "license_to_act": {"agent": "LicenseToActTB21DbWalRecoveryAgent", "reward": db_wal_lta_reward},
                "reward_flip": flip_label(db_wal_baseline_reward, db_wal_lta_reward),
                "xor_key": db_wal_evidence.get("xor_key"),
                "row_count": db_wal_evidence.get("row_count"),
                "wal_preserved": bool(db_wal_evidence.get("wal_exists_before"))
                and bool(db_wal_evidence.get("wal_exists_after")),
                "side_effects": db_wal_evidence.get("side_effects", []),
            }
        )

    return {
        "amendment": {
            "name": "separate_proposal_from_commit",
            "source_benchmark": "tau2-Bench",
            "rule": (
                "User intent, task phrasing, and model confidence may propose a Candidate Change, "
                "but durable commits require ready evidence, bounded write scope, preservation checks, "
                "and a done predicate."
            ),
            "compiler_effect": (
                "Split proposals from commits; attach readiness, write-scope, preserve, and done checks "
                "to each durable operation."
            ),
        },
        "source": {
            "tau2": summarize_tau2_pairs(tau2_pairs),
        },
        "projected_distinctions": {
            "terminal_bench_2_1": (
                "Task goal evidence is not enough to rewrite repository history, remove remote config, "
                "or perform destructive reads before the recovery protocol preserves the source."
            ),
            "skillflow": "Observed OCR text is not a completed artifact until the output schema is materialized.",
        },
        "transfer_checks": {
            "terminal_bench_2_1": summarize_transfer_checks(terminal_bench_checks),
            "skillflow": {
                "task": "OCR-Data-Extraction/task_family_invoice_images",
                "baseline": {"agent": "terminus-2-qwen-prompt-only", "reward": skill_baseline_reward},
                "license_to_act": {"agent": "qwen-cli-plus-govkernel", "reward": skill_lta_reward},
                "reward_flip": flip_label(skill_baseline_reward, skill_lta_reward),
                "pre_existing_output": skill_evidence.get("pre_existing_output"),
                "output_exists": skill_evidence.get("output_exists"),
                "materialized_rows": len(skill_evidence.get("rows", [])),
            },
        },
        "claim_boundary": (
            "This report is a stage-1 transfer ledger: it supports the commit-gap hypothesis, "
            "but full paper claims still require scaling across more held-out tasks and models."
        ),
    }


def summarize_transfer_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "n_tasks": len(checks),
        "f_to_p": sum(1 for check in checks if check.get("reward_flip") == "F_to_P"),
        "p_to_f": sum(1 for check in checks if check.get("reward_flip") == "P_to_F"),
        "checks": checks,
    }


def summarize_tau2_pairs(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    f_to_p = 0
    unchanged_positive = 0
    p_to_f = 0
    communicate_regressions = 0
    rows = []
    for pair in pairs:
        baseline_reward = _float_or_none(pair.get("baseline", {}).get("reward"))
        intervention_reward = _float_or_none(pair.get("intervention", {}).get("reward"))
        flip = pair.get("outcome", {}).get("flip") or flip_label(baseline_reward, intervention_reward)
        if flip == "F_to_P":
            f_to_p += 1
        if flip == "unchanged" and baseline_reward == 1.0 and intervention_reward == 1.0:
            unchanged_positive += 1
        if flip == "P_to_F":
            p_to_f += 1
        if pair.get("outcome", {}).get("communicate_regression"):
            communicate_regressions += 1
        rows.append(
            {
                "domain": pair.get("domain"),
                "task_id": str(pair.get("task_id")),
                "baseline_reward": baseline_reward,
                "intervention_reward": intervention_reward,
                "flip": flip,
            }
        )
    return {
        "n_pairs": len(pairs),
        "f_to_p": f_to_p,
        "unchanged_positive": unchanged_positive,
        "p_to_f": p_to_f,
        "communicate_regressions": communicate_regressions,
        "pairs": rows,
    }


def harbor_mean_reward(result: dict[str, Any]) -> float | None:
    stats = result.get("stats", {})
    evals = stats.get("evals", {})
    for payload in evals.values():
        metrics = payload.get("metrics") or []
        if metrics and "mean" in metrics[0]:
            return _float_or_none(metrics[0]["mean"])
        reward_stats = payload.get("reward_stats", {}).get("reward", {})
        rewards = []
        for reward, trials in reward_stats.items():
            rewards.extend([float(reward)] * len(trials))
        if rewards:
            return sum(rewards) / len(rewards)
    verifier = result.get("verifier_result", {}).get("rewards", {})
    if "reward" in verifier:
        return _float_or_none(verifier["reward"])
    return None


def flip_label(before: float | None, after: float | None) -> str:
    if before == 0.0 and after == 1.0:
        return "F_to_P"
    if before == 1.0 and after == 0.0:
        return "P_to_F"
    if before == after:
        return "unchanged"
    return "partial_change"


def write_amendment_transfer_report(output_path: Path, **kwargs: Any) -> dict[str, Any]:
    report = build_amendment_transfer_report(**kwargs)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _float_or_none(value: Any) -> float | None:
    return None if value is None else float(value)

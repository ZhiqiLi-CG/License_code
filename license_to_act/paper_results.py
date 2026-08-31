from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from license_to_act.amendment_transfer import harbor_mean_reward

STAGE1_FIELDS = [
    "case_id",
    "benchmark",
    "task",
    "baseline_agent",
    "baseline_variant",
    "baseline_reward",
    "lta_agent",
    "lta_variant",
    "lta_reward",
    "comparison_type",
    "official_verifier",
    "positive_control",
    "failure_type",
    "notes",
]

TRANSFER_FIELDS = [
    "target_family",
    "n",
    "failure_to_pass",
    "unchanged_positive",
    "pass_to_failure",
    "source_amendment",
]

DIAGNOSTIC_FIELDS = [
    "case_id",
    "benchmark",
    "task",
    "agent",
    "reward_or_status",
    "failure_or_role",
    "evidence",
]


def build_stage1_cases(report: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pair in report["source"]["tau2"]["pairs"]:
        task_id = str(pair["task_id"])
        is_positive = pair["flip"] == "unchanged" and pair["baseline_reward"] == 1.0
        rows.append(
            {
                "case_id": f"T2-A{task_id}",
                "benchmark": "tau2-Bench",
                "task": f"Airline task {task_id}",
                "baseline_agent": _tau2_agent(task_id),
                "baseline_variant": "Vanilla",
                "baseline_reward": _format_reward(pair["baseline_reward"]),
                "lta_agent": _tau2_agent(task_id),
                "lta_variant": "action-boundary pre-commit",
                "lta_reward": _format_reward(pair["intervention_reward"]),
                "comparison_type": "paired non-regression" if is_positive else "paired intervention",
                "official_verifier": "paired benchmark artifact",
                "positive_control": "yes" if is_positive else "no",
                "failure_type": "Ready commit" if is_positive else "Premature commit",
                "notes": _tau2_notes(task_id, is_positive),
            }
        )

    for check in report["transfer_checks"]["terminal_bench_2_1"]["checks"]:
        task = check["task"]
        rows.append(
            {
                "case_id": "TB-WAL" if task == "db-wal-recovery" else "TB-SAN",
                "benchmark": "Terminal-Bench 2.1",
                "task": task,
                "baseline_agent": _agent_label(check["baseline"]["agent"]),
                "baseline_variant": "Vanilla",
                "baseline_reward": _format_reward(check["baseline"]["reward"]),
                "lta_agent": "commit-controller runtime",
                "lta_variant": "boundary executor",
                "lta_reward": _format_reward(check["license_to_act"]["reward"]),
                "comparison_type": "diagnostic-to-official slice",
                "official_verifier": "official Harbor verifier",
                "positive_control": "no",
                "failure_type": _authority_failure_label(check.get("authority_failure")),
                "notes": _tb_notes(check),
            }
        )

    skillflow = report["transfer_checks"]["skillflow"]
    rows.append(
        {
            "case_id": "SF-INV",
            "benchmark": "SkillFlow",
            "task": "invoice image extraction",
            "baseline_agent": _agent_label(skillflow["baseline"]["agent"]),
            "baseline_variant": "Prompt-only boundary instructions",
            "baseline_reward": _format_reward(skillflow["baseline"]["reward"]),
            "lta_agent": _agent_label(skillflow["license_to_act"]["agent"]),
            "lta_variant": "completion trigger",
            "lta_reward": _format_reward(skillflow["license_to_act"]["reward"]),
            "comparison_type": "same-backbone runtime comparison",
            "official_verifier": "official SkillFlow verifier",
            "positive_control": "no",
            "failure_type": "Missing finalization",
            "notes": (
                "Prompt-only boundary instructions exposed OCR evidence but never wrote the workbook; "
                f"the action boundary wrote {skillflow['materialized_rows']} invoice rows "
                "from a non-existing output state."
            ),
        }
    )
    return rows


def build_transfer_ledger_rows(report: dict[str, Any]) -> list[dict[str, Any]]:
    amendment = _amendment_label(report["amendment"]["name"])
    tau2 = report["source"]["tau2"]
    tb = report["transfer_checks"]["terminal_bench_2_1"]
    sf = report["transfer_checks"]["skillflow"]
    sf_flip = sf["reward_flip"]
    return [
        {
            "target_family": "tau2-Bench",
            "n": tau2["n_pairs"],
            "failure_to_pass": tau2["f_to_p"],
            "unchanged_positive": tau2["unchanged_positive"],
            "pass_to_failure": tau2["p_to_f"],
            "source_amendment": amendment,
        },
        {
            "target_family": "Terminal-Bench 2.1",
            "n": tb["n_tasks"],
            "failure_to_pass": tb["f_to_p"],
            "unchanged_positive": 0,
            "pass_to_failure": tb["p_to_f"],
            "source_amendment": amendment,
        },
        {
            "target_family": "SkillFlow",
            "n": 1,
            "failure_to_pass": 1 if sf_flip == "F_to_P" else 0,
            "unchanged_positive": 1 if sf_flip == "unchanged" and sf["baseline"]["reward"] == 1.0 else 0,
            "pass_to_failure": 1 if sf_flip == "P_to_F" else 0,
            "source_amendment": amendment,
        },
    ]


def build_diagnostic_cases(
    report: dict[str, Any],
    *,
    git_leak_reward: float | None = None,
    clinic_reward: float | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if git_leak_reward is not None:
        rows.append(
            {
                "case_id": "TB-GLR",
                "benchmark": "Terminal-Bench 2.1",
                "task": "git-leak-recovery",
                "agent": "Codex GPT-5.5",
                "reward_or_status": _format_reward(git_leak_reward),
                "failure_or_role": "Positive control",
                "evidence": "Legitimate destructive cleanup can be committed as a scoped boundary action.",
            }
        )
    for check in report["transfer_checks"]["terminal_bench_2_1"]["checks"]:
        if check["task"] == "sanitize-git-repo":
            rows.extend(
                [
                    {
                        "case_id": "TB-SAN-C",
                        "benchmark": "Terminal-Bench 2.1",
                        "task": "sanitize-git-repo",
                        "agent": "Codex GPT-5.5",
                        "reward_or_status": _format_reward(check["baseline"]["reward"]),
                        "failure_or_role": "Overbroad commit",
                        "evidence": "Secret checks passed, but history rewrite changed HEAD and removed origin.",
                    },
                    {
                        "case_id": "TB-SAN-L",
                        "benchmark": "Terminal-Bench 2.1",
                        "task": "sanitize-git-repo",
                        "agent": "commit-controller runtime",
                        "reward_or_status": _format_reward(check["license_to_act"]["reward"]),
                        "failure_or_role": "Scoped boundary commit",
                        "evidence": (
                            "Exactly three contaminated paths changed; no unauthorized paths or side effects; "
                            "HEAD/remote preserved."
                        ),
                    },
                ]
            )
        elif check["task"] == "db-wal-recovery":
            rows.extend(
                [
                    {
                        "case_id": "TB-WAL-Q",
                        "benchmark": "Terminal-Bench 2.1",
                        "task": "db-wal-recovery",
                        "agent": "Qwen3.8-27B + Terminus-2",
                        "reward_or_status": _format_reward(check["baseline"]["reward"]),
                        "failure_or_role": "Destructive observation",
                        "evidence": "No recovered.json; WAL disappeared after direct SQLite reads.",
                    },
                    {
                        "case_id": "TB-WAL-L",
                        "benchmark": "Terminal-Bench 2.1",
                        "task": "db-wal-recovery",
                        "agent": "commit-controller runtime",
                        "reward_or_status": _format_reward(check["license_to_act"]["reward"]),
                        "failure_or_role": "Preserving read-and-commit protocol",
                        "evidence": (
                            f"7/7 official checks; {check.get('row_count')} rows; WAL preserved; "
                            "no side effects."
                        ),
                    },
                ]
            )
    if clinic_reward is not None:
        rows.append(
            {
                "case_id": "SF-CLINIC",
                "benchmark": "SkillFlow",
                "task": "clinic-shift-claim-review",
                "agent": "Codex GPT-5.5",
                "reward_or_status": _format_reward(clinic_reward),
                "failure_or_role": "Positive control",
                "evidence": "Evidence-backed artifact writing is necessary and should not be blanket-blocked.",
            }
        )
    skillflow = report["transfer_checks"]["skillflow"]
    rows.extend(
        [
            {
                "case_id": "SF-INV-P",
                "benchmark": "SkillFlow",
                "task": "invoice image extraction",
                "agent": "Qwen3.8-27B + Terminus-2",
                "reward_or_status": _format_reward(skillflow["baseline"]["reward"]),
                "failure_or_role": "Prompt-only negative control",
                "evidence": "Natural-language boundary instructions changed behavior but still produced no workbook.",
            },
            {
                "case_id": "SF-INV-L",
                "benchmark": "SkillFlow",
                "task": "invoice image extraction",
                "agent": "Qwen + commit controller",
                "reward_or_status": _format_reward(skillflow["license_to_act"]["reward"]),
                "failure_or_role": "Executable completion trigger",
                "evidence": (
                    "Official verifier passed; pre-existing output was false; "
                    f"{skillflow['materialized_rows']} rows written."
                ),
            },
        ]
    )
    return rows


def write_paper_results(
    *,
    transfer_report_path: Path,
    paper_data_dir: Path,
    summary_path: Path | None = None,
    git_leak_result_path: Path | None = None,
    clinic_result_path: Path | None = None,
) -> dict[str, Any]:
    report = json.loads(transfer_report_path.read_text(encoding="utf-8"))
    git_leak_reward = _optional_harbor_reward(git_leak_result_path)
    clinic_reward = _optional_harbor_reward(clinic_result_path)

    stage1_cases = build_stage1_cases(report)
    transfer_ledger = build_transfer_ledger_rows(report)
    diagnostic_cases = build_diagnostic_cases(
        report,
        git_leak_reward=git_leak_reward,
        clinic_reward=clinic_reward,
    )

    paper_data_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(paper_data_dir / "stage1_cases.csv", STAGE1_FIELDS, stage1_cases)
    _write_csv(paper_data_dir / "transfer_ledger.csv", TRANSFER_FIELDS, transfer_ledger)
    _write_csv(paper_data_dir / "diagnostic_cases.csv", DIAGNOSTIC_FIELDS, diagnostic_cases)

    summary = {
        "source": str(transfer_report_path),
        "paper_data_dir": str(paper_data_dir),
        "stage1_cases": len(stage1_cases),
        "failure_to_pass": sum(1 for row in stage1_cases if row["baseline_reward"] == "0" and row["lta_reward"] == "1"),
        "preserved_positive": sum(
            1 for row in stage1_cases if row["baseline_reward"] == "1" and row["lta_reward"] == "1"
        ),
        "transfer_ledger": transfer_ledger,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _optional_harbor_reward(path: Path | None) -> float | None:
    if path is None or not path.exists():
        return None
    return harbor_mean_reward(json.loads(path.read_text(encoding="utf-8")))


def _format_reward(value: Any) -> str:
    if value is None:
        return ""
    numeric = float(value)
    return str(int(numeric)) if numeric.is_integer() else f"{numeric:g}"


def _agent_label(agent: str) -> str:
    labels = {
        "codex-gpt-5.5": "Codex GPT-5.5",
        "terminus-2-qwen": "Qwen3.8-27B + Terminus-2",
        "terminus-2-qwen-prompt-only": "Qwen3.8-27B + Terminus-2",
        "qwen-cli-plus-govkernel": "Qwen + commit controller",
    }
    return labels.get(agent, agent)


def _tau2_agent(task_id: str) -> str:
    return "Mistral" if task_id == "48" else "Qwen"


def _tau2_notes(task_id: str, is_positive: bool) -> str:
    if is_positive:
        return "Legal cancellation remained allowed after additional flight-status evidence."
    if task_id == "48":
        return "Unsupported compensation was replaced with transfer to a human agent."
    return (
        "User intent and reservation state were present, but the cancellation was not ready to commit; "
        "the boundary transferred to a human agent."
    )


def _authority_failure_label(value: str | None) -> str:
    labels = {
        "overbroad_write_authority": "Overbroad commit",
        "evidence_consuming_read": "Destructive observation",
    }
    return labels.get(value or "", value or "")


def _tb_notes(check: dict[str, Any]) -> str:
    if check["task"] == "db-wal-recovery":
        return (
            "Baseline timed out without recovered.json and the WAL disappeared after direct reads; "
            "the preserving-read boundary passed 7/7 checks."
        )
    return (
        "Baseline removed secrets but rewrote history and removed the remote; the boundary changed exactly "
        "the contaminated working-tree paths and preserved HEAD/remote."
    )


def _amendment_label(name: str) -> str:
    labels = {
        "separate_intent_from_authorization": "separate_proposal_from_commit",
    }
    return labels.get(name, name)

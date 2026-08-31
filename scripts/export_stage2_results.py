#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.paths import artifact_path, project_root
from license_to_act.stage2_results import write_stage2_paper_results


_COMMIT_TAU2_MINING = artifact_path("stage2", "tau2_commit_mining_20260830.json")
DEFAULT_TAU2_MINING = _COMMIT_TAU2_MINING
DEFAULT_PAPER_DATA_DIR = project_root() / "License_paper" / "data"
DEFAULT_SUMMARY = artifact_path("stage2", "lta_stage2_paper_results_20260830.json")


DEFAULT_RELIABILITY_CASES = [
    {
        "case_id": "TB-SAN-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "sanitize-git-repo",
        "condition": "StateTx scoped Git transaction",
        "role": "write-scope/preserve anchor",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-sanitize-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Scoped replacement preserves HEAD and remote while passing the official verifier.",
    },
    {
        "case_id": "TB-WAL-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "db-wal-recovery",
        "condition": "StateTx WAL recovery transaction",
        "role": "preserving-read anchor",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-db-wal-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Recovery captures evidence before reads and preserves the WAL across official checks.",
    },
    {
        "case_id": "TB-SQLITE-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "sqlite-db-truncate",
        "condition": "StateTx truncated SQLite recovery",
        "role": "binary evidence recovery",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-tb21-lta-sqlite-truncate-k5-py",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Binary payload witnesses recover rows and commit the verifier-visible JSON artifact.",
    },
    {
        "case_id": "SF-INV-MAT-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "StateTx invoice completion trigger",
        "role": "completion trigger",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-invoice-materializer-k5-py",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Executable completion trigger materializes the verifier-visible workbook from OCR evidence.",
    },
    {
        "case_id": "TB-QWEN32K-MSWE-3",
        "benchmark": "Terminal-Bench 2.1",
        "task": "three Terminal-Bench anchors",
        "condition": "Qwen3.8-27B-long32k + mini-swe-agent",
        "role": "faithful long-context baseline",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-tb21-miniswe-qwen-long32k-license-anchors-smoke",
            "result.json",
        ),
        "paper_use": "faithful_baseline",
        "interpretation": "The 32k open-model agent fails all three Terminal-Bench transaction anchors without runtime errors.",
    },
    {
        "case_id": "SF-QWEN32K-MSWE-2",
        "benchmark": "SkillFlow",
        "task": "two SkillFlow artifact anchors",
        "condition": "Qwen3.8-27B-long32k + mini-swe-agent",
        "role": "faithful long-context baseline",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-miniswe-qwen-long32k-license-anchors-smoke",
            "result.json",
        ),
        "paper_use": "faithful_baseline",
        "interpretation": "The 32k open-model agent reads OCR evidence but fails both verifier-visible workbook finalizations.",
    },
    {
        "case_id": "SF-INV-QG-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "Qwen + Commit Controller, out128",
        "role": "model integration stress",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-qwen-invoice-k5-18002-out128",
            "result.json",
        ),
        "paper_use": "integration_stress",
        "interpretation": "Four of five trials pass; the failed trial is a Qwen context-window API error before controller evidence.",
    },
    {
        "case_id": "SF-TRAVEL-MAT-K5",
        "benchmark": "SkillFlow",
        "task": "travel claim OCR merge",
        "condition": "StateTx travel-claim completion trigger",
        "role": "OCR-to-workbook completion",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-travel-claim-k5-py",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "OCR evidence is joined with the source roster and committed as the verifier-visible workbook.",
    },
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export Stage-2 paper CSVs from Harbor and tau2 artifacts.")
    parser.add_argument("--tau2-mining", type=Path, default=DEFAULT_TAU2_MINING)
    parser.add_argument("--paper-data-dir", type=Path, default=DEFAULT_PAPER_DATA_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args(argv)

    summary = write_stage2_paper_results(
        tau2_mining_path=args.tau2_mining,
        reliability_cases=DEFAULT_RELIABILITY_CASES,
        paper_data_dir=args.paper_data_dir,
        summary_path=args.summary,
    )
    print(args.summary)
    print(
        "clean_trials={clean_reliability_trials} clean_errors={clean_reliability_errors} "
        "tau2_cancel_decisions={tau2_cancel_decisions} tau2_rcww={tau2_read_correct_write_wrong_proxy}".format(
            **summary
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

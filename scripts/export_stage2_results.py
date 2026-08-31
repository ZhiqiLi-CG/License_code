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
        "condition": "Action-boundary scoped Git write",
        "role": "write-scope/preserve anchor",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-sanitize-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Scoped replacement preserves HEAD and remote while passing the official verifier.",
    },
    {
        "case_id": "TB-WAL-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "db-wal-recovery",
        "condition": "Action-boundary WAL recovery",
        "role": "preserving-read anchor",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-db-wal-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Recovery captures evidence before reads and preserves the WAL across official checks.",
    },
    {
        "case_id": "TB-SQLITE-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "sqlite-db-truncate",
        "condition": "Action-boundary truncated SQLite recovery",
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
        "case_id": "TB-LOG-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "log-summary-date-ranges",
        "condition": "Action-boundary log-summary CSV write",
        "role": "log evidence to CSV artifact",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-tb21-lta-log-summary-k5-real-20260831",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": (
            "Bracketed severity evidence and filename dates are committed as the exact verifier-visible CSV."
        ),
    },
    {
        "case_id": "SF-INV-MAT-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "Action-boundary invoice completion trigger",
        "role": "completion trigger",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-invoice-materializer-k5-py",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Executable completion trigger writes the verifier-visible workbook from OCR evidence.",
    },
    {
        "case_id": "TB-QWEN32K-MSWE-K15",
        "benchmark": "Terminal-Bench 2.1",
        "task": "three Terminal-Bench anchors",
        "condition": "Qwen3.8-27B-long32k + mini-swe-agent",
        "role": "faithful long-context baseline, K=5 per terminal anchor",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-tb21-miniswe-qwen-long32k-anchors-k5-real-20260831",
            "result.json",
        ),
        "paper_use": "faithful_baseline",
        "interpretation": (
            "The 32k open-model agent solves some Git/WAL trials but remains unreliable "
            "across Terminal-Bench boundary anchors, with sqlite truncation at 0/5."
        ),
    },
    {
        "case_id": "TB-QWEN32K-MSWE-LOG-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "log-summary-date-ranges",
        "condition": "Qwen3.8-27B-long32k + mini-swe-agent",
        "role": "faithful long-context baseline, K=5 on log-summary anchor",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-tb21-miniswe-qwen-long32k-log-summary-k5-real-20260831",
            "result.json",
        ),
        "paper_use": "faithful_baseline",
        "interpretation": (
            "The 32k open-model agent solves most log-summary attempts, so this anchor is "
            "reported as a real baseline rather than a failure-only foil."
        ),
    },
    {
        "case_id": "SF-QWEN32K-MSWE-K10",
        "benchmark": "SkillFlow",
        "task": "two SkillFlow OCR anchors",
        "condition": "Qwen3.8-27B-long32k + mini-swe-agent",
        "role": "faithful long-context baseline, K=5 per OCR anchor",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-skillflow-miniswe-qwen-long32k-ocr-k5-real-20260831",
            "result.json",
        ),
        "paper_use": "faithful_baseline",
        "interpretation": (
            "The 32k open-model agent occasionally completes invoice extraction but remains unreliable "
            "across OCR-to-workbook finalization."
        ),
    },
    {
        "case_id": "SF-INV-QG-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "Qwen3.8-27B-long32k + action boundary",
        "role": "model integration stress",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-skillflow-qwen-govkernel-invoice-k5-real3-20260831",
            "result.json",
        ),
        "paper_use": "integration_stress",
        "interpretation": "Qwen remains in the official Harbor trial and the action boundary finalizes the workbook in all five runs.",
    },
    {
        "case_id": "TB-LOG-QG-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "log-summary-date-ranges",
        "condition": "Qwen3.8-27B-long32k + action boundary",
        "role": "model integration stress",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-tb21-miniswe-govkernel-log-summary-k5-real3-20260831",
            "result.json",
        ),
        "paper_use": "integration_stress",
        "interpretation": (
            "Qwen remains in the official Terminal-Bench trial and the action boundary "
            "finalizes the log-summary CSV in all five runs."
        ),
    },
    {
        "case_id": "SF-TRAVEL-QG-K5",
        "benchmark": "SkillFlow",
        "task": "travel claim OCR merge",
        "condition": "Qwen3.8-27B-long32k + action boundary",
        "role": "model integration stress",
        "result_path": artifact_path(
            "stage3",
            "harbor",
            "stage3-skillflow-qwen-govkernel-travel-k5-real-20260831",
            "result.json",
        ),
        "paper_use": "integration_stress",
        "interpretation": (
            "Qwen remains in the official SkillFlow trial and the action boundary "
            "finalizes the travel-claim workbook in all five runs."
        ),
    },
    {
        "case_id": "SF-TRAVEL-MAT-K5",
        "benchmark": "SkillFlow",
        "task": "travel claim OCR merge",
        "condition": "Action-boundary travel-claim completion trigger",
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

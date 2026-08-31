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


DEFAULT_TAU2_MINING = artifact_path("stage2", "tau2_authority_mining_20260830.json")
DEFAULT_PAPER_DATA_DIR = project_root() / "License_paper" / "data"
DEFAULT_SUMMARY = artifact_path("stage2", "lta_stage2_paper_results_20260830.json")


DEFAULT_RELIABILITY_CASES = [
    {
        "case_id": "TB-SAN-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "sanitize-git-repo",
        "condition": "LTA scoped Git materializer",
        "role": "side-effect authority",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-sanitize-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Scoped replacement preserves HEAD and remote while passing the official verifier.",
    },
    {
        "case_id": "TB-WAL-K5",
        "benchmark": "Terminal-Bench 2.1",
        "task": "db-wal-recovery",
        "condition": "LTA WAL recovery materializer",
        "role": "evidence-consuming read",
        "result_path": artifact_path("stage2", "harbor", "stage2-tb21-lta-db-wal-k5-py", "result.json"),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Recovery captures evidence before reads and preserves the WAL across official checks.",
    },
    {
        "case_id": "SF-INV-MAT-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "LTA invoice materializer",
        "role": "positive output obligation",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-invoice-materializer-k5-py",
            "result.json",
        ),
        "paper_use": "clean_reliability_anchor",
        "interpretation": "Executable obligation materializes the verifier-visible workbook from OCR evidence.",
    },
    {
        "case_id": "SF-INV-QG-K5",
        "benchmark": "SkillFlow",
        "task": "invoice image extraction",
        "condition": "Qwen + LTA GovKernel, out128",
        "role": "model integration stress",
        "result_path": artifact_path(
            "stage2",
            "harbor",
            "stage2-skillflow-lta-qwen-invoice-k5-18002-out128",
            "result.json",
        ),
        "paper_use": "integration_stress",
        "interpretation": "Four of five trials pass; the failed trial is a Qwen context-window API error before GovKernel evidence.",
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

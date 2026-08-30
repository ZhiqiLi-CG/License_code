#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.paper_results import write_paper_results
from license_to_act.paths import artifact_path, project_root


DEFAULT_TRANSFER_REPORT = artifact_path("amendment_transfer", "lta_stage1_transfer_ledger_20260830.json")
DEFAULT_PAPER_DATA_DIR = project_root() / "License_paper" / "data"
DEFAULT_SUMMARY = artifact_path("paper_results", "lta_stage2_paper_tables_20260830.json")
DEFAULT_GIT_LEAK_CONTROL = artifact_path(
    "probes", "tb21_codex_gpt55_git_leak_recovery", "2026-08-30__16-38-53", "result.json"
)
DEFAULT_CLINIC_CONTROL = artifact_path(
    "probes", "skillflow_codex_gpt55_clinic_shift_forcebuild", "2026-08-30__16-43-30", "result.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export paper CSVs from License-to-Act result artifacts.")
    parser.add_argument("--transfer-report", type=Path, default=DEFAULT_TRANSFER_REPORT)
    parser.add_argument("--paper-data-dir", type=Path, default=DEFAULT_PAPER_DATA_DIR)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--git-leak-control", type=Path, default=DEFAULT_GIT_LEAK_CONTROL)
    parser.add_argument("--clinic-control", type=Path, default=DEFAULT_CLINIC_CONTROL)
    args = parser.parse_args(argv)

    summary = write_paper_results(
        transfer_report_path=args.transfer_report,
        paper_data_dir=args.paper_data_dir,
        summary_path=args.summary,
        git_leak_result_path=args.git_leak_control,
        clinic_result_path=args.clinic_control,
    )
    print(args.summary)
    print(
        "stage1_cases={stage1_cases} failure_to_pass={failure_to_pass} preserved_positive={preserved_positive}".format(
            **summary
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

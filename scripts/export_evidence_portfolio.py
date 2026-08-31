#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.evidence_portfolio import write_evidence_portfolio  # noqa: E402
from license_to_act.paths import artifact_path, project_root  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the action-boundary evidence table.")
    parser.add_argument("--paper-data-dir", type=Path, default=project_root() / "License_paper" / "data")
    parser.add_argument("--paper-sections-dir", type=Path, default=project_root() / "License_paper" / "sections")
    parser.add_argument(
        "--summary",
        type=Path,
        default=artifact_path("paper_results", "lta_evidence_portfolio_20260831.json"),
    )
    args = parser.parse_args(argv)

    portfolio = write_evidence_portfolio(
        project_root(),
        paper_data_dir=args.paper_data_dir,
        paper_sections_dir=args.paper_sections_dir,
        summary_path=args.summary,
    )
    print(portfolio["outputs"]["summary_json"])
    print(portfolio["outputs"]["portfolio_csv"])
    print(portfolio["outputs"]["latex_numbers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

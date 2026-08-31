#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.boundary_patch_meta_agent import (  # noqa: E402
    DEFAULT_SOURCE_CASE_IDS,
    default_response_path,
    write_meta_agent_patch_report,
)
from license_to_act.paths import artifact_path, project_root  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export meta-agent boundary-patch evidence.")
    parser.add_argument(
        "--responses",
        type=Path,
        default=default_response_path(project_root()),
    )
    parser.add_argument(
        "--source-case-id",
        action="append",
        dest="source_case_ids",
        default=[],
        help="Source case id to include. Defaults to the four paper-facing seed failures.",
    )
    parser.add_argument("--paper-data-dir", type=Path, default=project_root() / "License_paper" / "data")
    parser.add_argument("--paper-sections-dir", type=Path, default=project_root() / "License_paper" / "sections")
    parser.add_argument(
        "--summary",
        type=Path,
        default=artifact_path("paper_results", "boundary_patch_meta_agent_20260831.json"),
    )
    args = parser.parse_args(argv)

    source_case_ids = args.source_case_ids or DEFAULT_SOURCE_CASE_IDS
    output = write_meta_agent_patch_report(
        project_root(),
        response_path=args.responses,
        source_case_ids=source_case_ids,
        paper_data_dir=args.paper_data_dir,
        paper_sections_dir=args.paper_sections_dir,
        summary_path=args.summary,
    )
    print(output["outputs"]["summary_json"])
    print(output["outputs"]["patch_csv"])
    print(output["outputs"]["latex_numbers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.state_contract_examples import write_state_contract_examples  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export paper-facing State Contract examples.")
    parser.add_argument("--project-root", type=Path, default=Path("/data/zhiqi/License"))
    parser.add_argument("--paper-data-dir", type=Path, default=None)
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()

    output = write_state_contract_examples(
        args.project_root,
        paper_data_dir=args.paper_data_dir,
        summary_path=args.summary,
    )
    print(output["outputs"]["paper_data_json"])
    print(output["outputs"]["summary_json"])


if __name__ == "__main__":
    main()

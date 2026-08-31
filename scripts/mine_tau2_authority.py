#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.paths import artifact_path
from license_to_act.tau2_authority_mining import (
    DEFAULT_TAU2_SIMULATION_ROOT,
    discover_tau2_result_paths,
    write_tau2_authority_mining_report,
)


DEFAULT_OUTPUT = artifact_path("stage2", "tau2_commit_mining_20260830.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mine tau2 traces for commit-gap failures.")
    parser.add_argument("--root", type=Path, default=DEFAULT_TAU2_SIMULATION_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--current-time", default="2024-05-15T15:00:00")
    args = parser.parse_args(argv)

    paths = discover_tau2_result_paths(args.root)
    report = write_tau2_authority_mining_report(
        args.output,
        paths,
        current_time=args.current_time,
    )
    summary = report["summary"]
    print(args.output)
    print(
        "result_files={n_result_files} simulations={n_simulations} "
        "infra_errors={n_infrastructure_error_simulations} cancel_decisions={n_cancel_decisions} "
        "revision_targets={n_lta_vetoes} read_correct_write_wrong={n_read_correct_write_wrong_proxy}".format(
            **summary
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

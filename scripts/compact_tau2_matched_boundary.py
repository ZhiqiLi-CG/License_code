#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.tau2_matched_boundary_export import compact_tau2_matched_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compact a full tau2 matched report.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--actor-model", required=True)
    parser.add_argument("--user-mode", required=True)
    parser.add_argument("--paper-use", required=True)
    parser.add_argument("--expected-complete-pairs", type=int, default=None)
    parser.add_argument("--task-ids", nargs="+", default=None)
    args = parser.parse_args(argv)

    compact = compact_tau2_matched_report(
        args.source,
        domain=args.domain,
        actor_model=args.actor_model,
        user_mode=args.user_mode,
        paper_use=args.paper_use,
        expected_complete_pairs=args.expected_complete_pairs,
        task_ids=args.task_ids,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(compact, indent=2), encoding="utf-8")
    print(args.output)
    print(compact["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

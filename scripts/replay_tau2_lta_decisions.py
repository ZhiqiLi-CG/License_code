from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.tau2_replay import replay_tau2_cancel_decisions
from license_to_act.paths import artifact_path


DEFAULT_CASES = {
    "qwen_airline_task1_false_cancel": Path(
        "/data/zhiqi/rp-simple-agent-acl-paper-longrun-20260808-v4/global/resources/"
        "datasets/tau2-bench/data/simulations/rsi8_stage1_qwen_airline_train_1_20260830/results.json"
    ),
    "qwen_airline_task19_legal_cancel": Path(
        "/data/zhiqi/rp-simple-agent-acl-paper-longrun-20260808-v4/global/resources/"
        "datasets/tau2-bench/data/simulations/rsi8_stage1_qwen_airline_base_19_20260830/results.json"
    ),
}
DEFAULT_OUTPUT = artifact_path("tau2_lta", "tau2_cancel_authority_replay_20260830.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--current-time", default="2024-05-15T15:00:00")
    args = parser.parse_args(argv)

    payload = {
        "benchmark": "tau2-Bench",
        "domain": "airline",
        "license": "tau2_airline_cancel_policy",
        "current_time": args.current_time,
        "cases": {
            name: replay_tau2_cancel_decisions(path, args.current_time)
            for name, path in DEFAULT_CASES.items()
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(args.output)
    for name, report in payload["cases"].items():
        decisions = report["simulations"][0]["decisions"]
        statuses = [decision["reason"] for decision in decisions]
        print(f"{name}: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

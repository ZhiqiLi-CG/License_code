#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from license_to_act.tau2_action_boundary import Tau2ActionBoundaryAgent
from license_to_act.tau2_matched_experiment import (
    BASELINE_CONDITION,
    BOUNDARY_CONDITION,
    simulation_to_matched_run,
    write_tau2_matched_report,
)
from license_to_act.tau2_policy_authority import extract_current_time
from license_to_act.tau2_scripted_users import scripted_tau2_user_utterances


def main() -> None:
    args = parse_args()
    if args.tau2_src:
        sys.path.insert(0, str(args.tau2_src.resolve()))
    if args.api_base:
        os.environ["OPENAI_BASE_URL"] = args.api_base
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key

    from tau2.data_model.simulation import TextRunConfig
    from tau2.evaluator.evaluator import EvaluationType
    from tau2.runner import build_text_orchestrator, get_tasks, run_simulation
    from tau2.data_model.message import UserMessage
    from tau2.user.user_simulator_base import STOP, HalfDuplexUser, UserState

    class ScriptedTau2User(HalfDuplexUser):
        def __init__(self, utterances: list[str]) -> None:
            super().__init__(instructions="\n".join(utterances), tools=None)
            self.utterances = utterances
            self.index = 0

        def get_init_state(self, message_history=None):
            return UserState(system_messages=[], messages=list(message_history or []))

        def generate_next_message(self, message, state):
            if message is not None:
                state.messages.append(message)
            if self.index >= len(self.utterances):
                content = STOP
            else:
                content = self.utterances[self.index]
                self.index += 1
            user_message = UserMessage(role="user", content=content)
            state.messages.append(user_message)
            return user_message, state

        def set_seed(self, seed: int) -> None:
            self.index = 0

    task_ids = [str(task_id) for task_id in args.task_ids]
    tasks = get_tasks(args.domain, task_split_name=args.task_split_name, task_ids=task_ids)
    runs = []
    output_path = args.output or _default_output_path(args.domain, task_ids)
    for task in tasks:
        for trial_index in range(args.num_trials):
            seed = args.seed + trial_index
            pair_id = f"{args.domain}-{task.id}-seed-{seed}"
            for condition in args.conditions:
                config = TextRunConfig(
                    domain=args.domain,
                    agent="llm_agent",
                    user="user_simulator",
                    llm_agent=args.llm_agent,
                    llm_user=args.llm_user,
                    llm_args_agent=_llm_args(args.agent_max_tokens, args.temperature),
                    llm_args_user=_llm_args(args.user_max_tokens, args.temperature),
                    max_steps=args.max_steps,
                    max_errors=args.max_errors,
                    timeout=args.timeout,
                    seed=seed,
                    hallucination_retries=0,
                )
                orchestrator = build_text_orchestrator(
                    config,
                    task,
                    seed=seed,
                    simulation_id=f"{pair_id}-{condition}",
                )
                if args.user_mode == "scripted":
                    orchestrator.user = ScriptedTau2User(
                        scripted_tau2_user_utterances(args.domain, task.id)
                    )
                current_time = extract_current_time(orchestrator.environment.get_policy())
                boundary_agent = None
                if condition == BOUNDARY_CONDITION:
                    boundary_agent = Tau2ActionBoundaryAgent(
                        orchestrator.agent,
                        current_time=current_time,
                    )
                    orchestrator.agent = boundary_agent

                simulation = run_simulation(
                    orchestrator,
                    evaluation_type=EvaluationType.ALL,
                )
                runs.append(
                    simulation_to_matched_run(
                        simulation,
                        pair_id=pair_id,
                        condition=condition,
                        current_time=current_time,
                        boundary_records=(
                            boundary_agent.boundary_records if boundary_agent else []
                        ),
                    )
                )
                write_tau2_matched_report(output_path, runs)

    report = write_tau2_matched_report(output_path, runs)
    print(f"wrote {output_path}")
    print(report["summary"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run matched tau2 baseline/action-boundary trials."
    )
    parser.add_argument("--domain", default="airline")
    parser.add_argument("--task-split-name", default="base")
    parser.add_argument("--task-ids", nargs="+", default=["1"])
    parser.add_argument("--num-trials", type=int, default=1)
    parser.add_argument("--seed", type=int, default=300)
    parser.add_argument("--max-steps", type=int, default=35)
    parser.add_argument("--max-errors", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=240.0)
    parser.add_argument("--llm-agent", default="openai/Qwen3.8-27B-long32k")
    parser.add_argument("--llm-user", default="openai/Qwen3.8-27B-long32k")
    parser.add_argument("--user-mode", choices=["llm", "scripted"], default="llm")
    parser.add_argument("--agent-max-tokens", type=int, default=256)
    parser.add_argument("--user-max-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--api-base", default="")
    parser.add_argument("--api-key", default="dummy")
    parser.add_argument(
        "--tau2-src",
        type=Path,
        default=Path("/data/zhiqi/License/datasets/tau2-bench/src"),
    )
    parser.add_argument(
        "--conditions",
        nargs="+",
        choices=[BASELINE_CONDITION, BOUNDARY_CONDITION],
        default=[BASELINE_CONDITION, BOUNDARY_CONDITION],
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def _llm_args(max_tokens: int, temperature: float) -> dict:
    return {"max_tokens": max_tokens, "temperature": temperature}


def _default_output_path(domain: str, task_ids: list[str]) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    task_slug = "-".join(task_ids)
    return Path("/data/zhiqi/License/artifacts/experiments") / (
        f"tau2_action_boundary_matched_{domain}_{task_slug}_{stamp}.json"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.boundary_patch_meta_agent import (  # noqa: E402
    DEFAULT_SOURCE_CASE_IDS,
    build_patch_prompt,
    parse_patch_response,
)
from license_to_act.paths import artifact_path, project_root  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask a frozen meta-agent to propose boundary updates.")
    parser.add_argument("--api-base", default="http://127.0.0.1:8001/v1")
    parser.add_argument("--model", default="Mistral-Small-3.2-24B-Instruct-2506")
    parser.add_argument("--max-tokens", type=int, default=700)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--source-case-id",
        action="append",
        dest="source_case_ids",
        default=[],
        help="Source case id to include. Defaults to the four paper-facing seed failures.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=artifact_path("experiments", "boundary_patch_meta_agent_mistral_stage1_20260831.json"),
    )
    args = parser.parse_args(argv)

    root = project_root()
    source_case_ids = args.source_case_ids or DEFAULT_SOURCE_CASE_IDS
    cases = _read_cases(root / "License_paper" / "data" / "stage1_cases.csv", source_case_ids)
    responses: dict[str, dict[str, object]] = {}
    prompts: dict[str, str] = {}
    raw_responses: dict[str, str] = {}

    for case in cases:
        prompt = build_patch_prompt(case)
        raw = _complete(
            api_base=args.api_base,
            model=args.model,
            prompt=prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
        prompts[case["case_id"]] = prompt
        raw_responses[case["case_id"]] = raw
        responses[case["case_id"]] = parse_patch_response(raw)

    payload = {
        "schema": "boundary_patch_meta_agent_raw_v1",
        "model": args.model,
        "api_base": args.api_base,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "source_case_ids": source_case_ids,
        "prompts": prompts,
        "raw_responses": raw_responses,
        "responses": responses,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(args.output)
    return 0


def _complete(
    *,
    api_base: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> str:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You propose reusable action-boundary updates for frozen agents. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    url = api_base.rstrip("/") + "/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer EMPTY",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Meta-agent request failed for {url}: {exc}") from exc

    try:
        return result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected chat completion response: {result}") from exc


def _read_cases(path: Path, source_case_ids: list[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {row["case_id"]: row for row in rows}
    cases = []
    for case_id in source_case_ids:
        if case_id not in by_id:
            raise ValueError(f"Unknown source case id: {case_id}")
        cases.append(by_id[case_id])
    return cases


if __name__ == "__main__":
    raise SystemExit(main())

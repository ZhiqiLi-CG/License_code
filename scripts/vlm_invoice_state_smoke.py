#!/usr/bin/env python3
"""Small VLM witness smoke for SkillFlow invoice-image artifact state."""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path
from urllib import request


def image_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def call_vlm(endpoint: str, image_path: Path) -> dict:
    payload = {
        "model": "qwen3-vl-2b-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract a typed artifact state from this invoice image. "
                            "Return only JSON with keys: filename, date_iso, total_amount, "
                            "date_evidence, total_evidence, confidence. "
                            "Use YYYY-MM-DD for date_iso. total_amount must be a string with two decimals. "
                            "If uncertain, use null for the uncertain field. "
                            f"The source filename is {image_path.name}."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": image_data_url(image_path)}},
                ],
            }
        ],
        "temperature": 0,
        "max_tokens": 256,
    }
    req = request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    raw = body["choices"][0]["message"]["content"]
    row = {"image": str(image_path), "raw": raw, "usage": body.get("usage")}
    try:
        row["parsed"] = extract_json(raw)
    except Exception as exc:  # pragma: no cover - diagnostic artifact
        row["parsed"] = None
        row["parse_error"] = repr(exc)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--img-dir",
        default="/data/zhiqi/RSI1/external/SkillFlow/test_tasks/test_tasks/OCR-Data-Extraction/"
        "task_family_invoice_images/environment/workspace/dataset/img",
    )
    parser.add_argument("--endpoint", default="http://127.0.0.1:8012/v1/chat/completions")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument(
        "--out",
        default="/data/zhiqi/RSI6/artifacts/vlm_witness/rsi6_8012_invoice_state_smoke_n2_20260830.jsonl",
    )
    args = parser.parse_args()

    images = sorted(Path(args.img_dir).glob("*.jpg"))[: args.limit]
    if not images:
        raise SystemExit(f"no jpg images found under {args.img_dir}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for idx, image_path in enumerate(images, 1):
            row = call_vlm(args.endpoint, image_path)
            row["index"] = idx
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")
            parsed = row.get("parsed") or {}
            print(
                f"{idx:02d} {image_path.name} date={parsed.get('date_iso')} "
                f"total={parsed.get('total_amount')} parse_error={row.get('parse_error')}"
            )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

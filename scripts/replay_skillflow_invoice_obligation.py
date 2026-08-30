#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any
from xml.etree import ElementTree
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from license_to_act.core import EvidenceBundle, StateChangeEvent
from license_to_act.examples import (
    skillflow_invoice_summary_license,
    skillflow_invoice_summary_required_commit,
)
from license_to_act.skillflow_invoice_materializer import (
    extract_ocr_blocks,
    fulfill_invoice_workbook_obligation,
)


DEFAULT_TRAJECTORY = Path(
    "artifacts/probes/skillflow_terminus_qwen_invoice_images_lta_commit_protocol_forcebuild/"
    "2026-08-30__18-05-01/task_family_invoice_images__jSHw8Dy/agent/trajectory.json"
)
DEFAULT_IMAGE_DIR = Path(
    "/data/zhiqi/RSI1/external/SkillFlow/test_tasks/test_tasks/"
    "OCR-Data-Extraction/task_family_invoice_images/environment/workspace/dataset/img"
)
DEFAULT_ORACLE = Path(
    "/data/zhiqi/RSI1/external/SkillFlow/test_tasks/test_tasks/"
    "OCR-Data-Extraction/task_family_invoice_images/tests/invoice_oracle.xlsx"
)
DEFAULT_OUTPUT_DIR = Path("artifacts/method_slices/skillflow_invoice_qwen_lta_trace_materialized")


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a SkillFlow invoice commit obligation from OCR evidence.")
    parser.add_argument("--trajectory", type=Path, default=DEFAULT_TRAJECTORY)
    parser.add_argument("--image-dir", type=Path, default=DEFAULT_IMAGE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--oracle", type=Path, default=DEFAULT_ORACLE)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "invoice_summary.xlsx"
    summary_path = args.output_dir / "result.json"

    blocks = _best_ocr_blocks(args.trajectory)
    if len(blocks) != 15:
        raise SystemExit(f"expected 15 OCR evidence blocks, found {len(blocks)}")

    observed = [
        StateChangeEvent(
            actor_role="artifact_agent",
            state_region="input:/app/workspace/dataset/img",
            operation="ReadEvidence",
            evidence=EvidenceBundle(types={"OcrTextEvidence"}, refs=set(blocks)),
        )
    ]
    result = fulfill_invoice_workbook_obligation(
        required_event=skillflow_invoice_summary_required_commit(),
        observed_events=observed,
        licenses=[skillflow_invoice_summary_license()],
        image_dir=args.image_dir,
        output_path=output_path,
        ocr_fn=lambda path: blocks[path.name],
    )

    actual_rows = _read_inline_rows(output_path)
    oracle_rows = _read_inline_rows(args.oracle) if args.oracle.exists() else None
    summary = {
        "source_trajectory": str(args.trajectory),
        "source_failed_reward": 0,
        "source_failure": "/app/workspace/invoice_summary.xlsx missing after prompt-only LTA run",
        "used_oracle_for_generation": False,
        "ocr_blocks_from_trajectory": len(blocks),
        "status": result.status,
        "decision": {
            "allowed": result.decision.allowed,
            "reason": result.decision.reason,
            "license_name": result.decision.license_name,
            "missing_evidence": sorted(result.decision.missing_evidence),
        },
        "output_workbook": str(output_path),
        "rows": [row.__dict__ for row in result.rows],
        "verification": {
            "matches_oracle_rows": actual_rows == oracle_rows if oracle_rows is not None else None,
            "actual_row_count": len(actual_rows) - 1,
            "expected_row_count": len(oracle_rows) - 1 if oracle_rows is not None else None,
            "header": actual_rows[0],
            "first_data_row": actual_rows[1],
            "last_data_row": actual_rows[-1],
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {
                "status": result.status,
                "allowed": result.decision.allowed,
                "ocr_blocks": len(blocks),
                "matches_oracle_rows": summary["verification"]["matches_oracle_rows"],
                "output": str(output_path),
                "summary": str(summary_path),
            },
            indent=2,
        )
    )


def _best_ocr_blocks(trajectory_path: Path) -> dict[str, str]:
    trajectory = json.loads(trajectory_path.read_text())
    best_blocks: dict[str, str] = {}
    for text in _walk_strings(trajectory):
        blocks = extract_ocr_blocks(text)
        if len(blocks) > len(best_blocks):
            best_blocks = blocks
    return best_blocks


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def _read_inline_rows(path: Path) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    rows: list[list[str]] = []
    for row in root.findall("main:sheetData/main:row", ns):
        values = []
        for cell in row.findall("main:c", ns):
            text = cell.find("main:is/main:t", ns)
            values.append(text.text if text is not None and text.text is not None else "")
        rows.append(values)
    return rows


if __name__ == "__main__":
    main()

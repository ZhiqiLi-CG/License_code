from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .tau2_matched_experiment import summarize_tau2_matched_runs


TAU2_MATCHED_BOUNDARY_FIELDS = [
    "pair_id",
    "domain",
    "task_id",
    "seed",
    "actor_model",
    "user_mode",
    "condition",
    "reward",
    "cancel_tool_calls",
    "read_correct_write_wrong",
    "boundary_vetoes",
    "boundary_allows",
    "paper_use",
    "source_path",
]


DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "tau2_matched_boundary"
    / "airline_task48_mistral_scripted_v2_summary.json"
)


def build_tau2_matched_boundary_export(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    path = Path(source_path) if source_path is not None else DEFAULT_FIXTURE
    payload = _read_json(path)
    runs = payload["runs"]
    rows = [_row_from_run(run, path) for run in runs]
    summary = summarize_tau2_matched_runs(runs)
    summary.update(
        {
            "source_path": str(path),
            "project_root": str(root),
            "domains": len({row["domain"] for row in rows}),
            "actor_models": len({row["actor_model"] for row in rows}),
        }
    )
    return {"summary": summary, "rows": rows}


def compact_tau2_matched_report(
    source_path: str | Path,
    *,
    domain: str,
    actor_model: str,
    user_mode: str,
    paper_use: str,
    expected_complete_pairs: int | None = None,
) -> dict[str, Any]:
    """Convert a full tau2 live report into a small paper-facing fixture."""

    path = Path(source_path)
    payload = _read_json(path)
    runs = [
        _compact_run(
            run,
            domain=domain,
            actor_model=actor_model,
            user_mode=user_mode,
            paper_use=paper_use,
        )
        for run in payload["runs"]
    ]
    summary = summarize_tau2_matched_runs(runs)
    if expected_complete_pairs is not None and summary["complete_pairs"] != expected_complete_pairs:
        raise ValueError(
            f"expected {expected_complete_pairs} complete pairs, found {summary['complete_pairs']}"
        )
    return {
        "source_full_report": str(path),
        "notes": (
            "Compact export of a real matched tau2 run. The full local report "
            "contains official tau2 messages and reward_info; this file keeps "
            "only fields needed to regenerate the paper table and generated numbers."
        ),
        "summary": summary,
        "runs": runs,
    }


def write_tau2_matched_boundary_export(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
    source_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "tau2_matched_boundary_20260831.json"
    )

    report = build_tau2_matched_boundary_export(root, source_path=source_path)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    csv_path = paper_data_dir / "tau2_matched_boundary.csv"
    latex_numbers = paper_sections_dir / "generated_tau2_matched_boundary_numbers.tex"
    _write_csv(csv_path, TAU2_MATCHED_BOUNDARY_FIELDS, report["rows"])
    latex_numbers.write_text(_latex_numbers(report["summary"]), encoding="utf-8")

    report["outputs"] = {
        "summary_json": str(summary_path),
        "csv": str(csv_path),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _row_from_run(run: dict[str, Any], source_path: Path) -> dict[str, str]:
    boundary_records = run.get("boundary_records") or []
    return {
        "pair_id": str(run["pair_id"]),
        "domain": str(run.get("domain", "")),
        "task_id": str(run.get("task_id", "")),
        "seed": str(run.get("seed", "")),
        "actor_model": str(run.get("actor_model", "")),
        "user_mode": str(run.get("user_mode", "")),
        "condition": str(run["condition"]),
        "reward": _format_number(float(run.get("reward") or 0.0)),
        "cancel_tool_calls": str(int(run.get("cancel_tool_calls") or 0)),
        "read_correct_write_wrong": "yes" if run.get("read_correct_write_wrong") else "no",
        "boundary_vetoes": str(sum(1 for record in boundary_records if not record.get("allowed"))),
        "boundary_allows": str(sum(1 for record in boundary_records if record.get("allowed"))),
        "paper_use": str(run.get("paper_use", "")),
        "source_path": str(source_path),
    }


def _compact_run(
    run: dict[str, Any],
    *,
    domain: str,
    actor_model: str,
    user_mode: str,
    paper_use: str,
) -> dict[str, Any]:
    return {
        "pair_id": str(run["pair_id"]),
        "domain": domain,
        "task_id": str(run.get("task_id", "")),
        "seed": _seed_from_pair_id(str(run["pair_id"])),
        "actor_model": actor_model,
        "user_mode": user_mode,
        "condition": str(run["condition"]),
        "reward": float(run.get("reward") or 0.0),
        "cancel_tool_calls": int(run.get("cancel_tool_calls") or 0),
        "read_correct_write_wrong": bool(run.get("read_correct_write_wrong")),
        "boundary_records": run.get("boundary_records") or [],
        "paper_use": paper_use,
    }


def _seed_from_pair_id(pair_id: str) -> int:
    prefix = "seed-"
    if prefix not in pair_id:
        raise ValueError(f"pair_id does not contain seed: {pair_id}")
    return int(pair_id.rsplit(prefix, maxsplit=1)[1])


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTATauTwoMatchedPairs": summary["pairs"],
        "LTATauTwoMatchedCompletePairs": summary["complete_pairs"],
        "LTATauTwoMatchedBaselineTrials": summary["baseline_trials"],
        "LTATauTwoMatchedBoundaryTrials": summary["boundary_trials"],
        "LTATauTwoMatchedBaselineMeanReward": _format_number(summary["baseline_mean_reward"]),
        "LTATauTwoMatchedBoundaryMeanReward": _format_number(summary["boundary_mean_reward"]),
        "LTATauTwoMatchedRewardDelta": _format_number(summary["reward_delta"]),
        "LTATauTwoMatchedBaselineRCWW": summary["baseline_read_correct_write_wrong"],
        "LTATauTwoMatchedBoundaryRCWW": summary["boundary_read_correct_write_wrong"],
        "LTATauTwoMatchedBoundaryVetoes": summary["boundary_vetoes"],
        "LTATauTwoMatchedBoundaryRegressions": summary["boundary_regressions"],
        "LTATauTwoMatchedActorModels": summary["actor_models"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/tau2_matched_boundary_export.py.",
        "% Regenerate with License_code/scripts/export_tau2_matched_boundary.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

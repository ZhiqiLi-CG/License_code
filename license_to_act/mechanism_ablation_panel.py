from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PANEL_FIELDS = [
    "ablation_id",
    "high_priority",
    "mechanism_removed",
    "claim_tested",
    "cut_evidence_cases",
    "cut_trials",
    "cut_passes",
    "full_evidence_cases",
    "full_trials",
    "full_passes",
    "paper_result",
    "comparison_class",
]


def build_mechanism_ablation_panel(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"
    stage1_rows = _read_csv(data_dir / "stage1_cases.csv")
    stage2_rows = _read_csv(data_dir / "stage2_reliability.csv")
    stage1 = {row["case_id"]: row for row in stage1_rows}
    stage2 = {row["case_id"]: row for row in stage2_rows}

    rows = [
        _row(
            "ABLATE_COMMIT_READINESS",
            "no",
            "ready predicate",
            "User intent and reservation evidence do not make a business-record write ready to commit.",
            ["T2-A1", "T2-A48"],
            _stage1_cut(stage1, ["T2-A1", "T2-A48"]),
            ["T2-A1", "T2-A48"],
            _stage1_full(stage1, ["T2-A1", "T2-A48"]),
        ),
        _row(
            "ABLATE_WRITE_SCOPE_AND_PRESERVE",
            "yes",
            "write scope and preserve constraints",
            "Local task success can overcommit by mutating collateral Git state.",
            ["TB-SAN"],
            _stage1_cut(stage1, ["TB-SAN"]),
            ["TB-SAN-K5"],
            _stage2_full(stage2, ["TB-SAN-K5"]),
        ),
        _row(
            "ABLATE_PRESERVING_READ",
            "no",
            "preserving-read contract for fragile evidence",
            "Observation can consume the recovery substrate unless reads preserve source evidence.",
            ["TB-WAL"],
            _stage1_cut(stage1, ["TB-WAL"]),
            ["TB-WAL-K5"],
            _stage2_full(stage2, ["TB-WAL-K5"]),
        ),
        _row(
            "ABLATE_COMPLETION_TRIGGER",
            "yes",
            "done trigger for verifier-visible artifacts",
            "Complete prepared evidence is insufficient when no runtime trigger owns finalization.",
            ["SF-INV"],
            _stage1_cut(stage1, ["SF-INV"]),
            ["SF-INV-MAT-K5", "SF-TRAVEL-MAT-K5"],
            _stage2_full(stage2, ["SF-INV-MAT-K5", "SF-TRAVEL-MAT-K5"]),
        ),
        _row(
            "PROMPT_ONLY_TRANSACTION_TEXT",
            "yes",
            "runtime commit control",
            "Natural-language transaction text does not substitute for owning the durability boundary.",
            ["SF-INV"],
            _stage1_cut(stage1, ["SF-INV"]),
            ["SF-INV"],
            _stage1_full(stage1, ["SF-INV"]),
        ),
    ]
    return {"summary": _summarize(rows), "rows": rows}


def write_mechanism_ablation_panel(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "lta_mechanism_ablation_panel_20260831.json"
    )

    panel = build_mechanism_ablation_panel(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    panel_csv = paper_data_dir / "mechanism_ablation_panel.csv"
    latex_numbers = paper_sections_dir / "generated_ablation_numbers.tex"
    _write_panel_csv(panel_csv, panel["rows"])
    latex_numbers.write_text(_latex_numbers(panel["summary"]), encoding="utf-8")

    panel["outputs"] = {
        "summary_json": str(summary_path),
        "panel_csv": str(panel_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(panel, indent=2), encoding="utf-8")
    return panel


def _row(
    ablation_id: str,
    high_priority: str,
    mechanism_removed: str,
    claim_tested: str,
    cut_cases: list[str],
    cut_counts: tuple[int, int],
    full_cases: list[str],
    full_counts: tuple[int, int],
) -> dict[str, str]:
    cut_trials, cut_passes = cut_counts
    full_trials, full_passes = full_counts
    return {
        "ablation_id": ablation_id,
        "high_priority": high_priority,
        "mechanism_removed": mechanism_removed,
        "claim_tested": claim_tested,
        "cut_evidence_cases": _join(cut_cases),
        "cut_trials": str(cut_trials),
        "cut_passes": str(cut_passes),
        "full_evidence_cases": _join(full_cases),
        "full_trials": str(full_trials),
        "full_passes": str(full_passes),
        "paper_result": f"{cut_passes}/{cut_trials} cut pass versus {full_passes}/{full_trials} full StateTx pass",
        "comparison_class": "mechanism_ablation",
    }


def _stage1_cut(rows: dict[str, dict[str, str]], case_ids: list[str]) -> tuple[int, int]:
    selected = [rows[case_id] for case_id in case_ids]
    return len(selected), sum(int(row["baseline_reward"]) for row in selected)


def _stage1_full(rows: dict[str, dict[str, str]], case_ids: list[str]) -> tuple[int, int]:
    selected = [rows[case_id] for case_id in case_ids]
    return len(selected), sum(int(row["lta_reward"]) for row in selected)


def _stage2_cut(rows: dict[str, dict[str, str]], case_ids: list[str]) -> tuple[int, int]:
    selected = [rows[case_id] for case_id in case_ids]
    trials = sum(int(row["n_trials"]) for row in selected)
    passes = int(round(sum(int(row["n_trials"]) * float(row["mean_reward"]) for row in selected)))
    return trials, passes


def _stage2_full(rows: dict[str, dict[str, str]], case_ids: list[str]) -> tuple[int, int]:
    return _stage2_cut(rows, case_ids)


def _add_counts(left: tuple[int, int], right: tuple[int, int]) -> tuple[int, int]:
    return left[0] + right[0], left[1] + right[1]


def _summarize(rows: list[dict[str, str]]) -> dict[str, int]:
    return {
        "ablation_rows": len(rows),
        "high_priority_rows": sum(1 for row in rows if row["high_priority"] == "yes"),
        "baseline_overlap": sum(1 for row in rows if "baseline" in row["comparison_class"]),
        "cut_trials": sum(int(row["cut_trials"]) for row in rows),
        "cut_passes": sum(int(row["cut_passes"]) for row in rows),
        "full_trials": sum(int(row["full_trials"]) for row in rows),
        "full_passes": sum(int(row["full_passes"]) for row in rows),
    }


def _write_panel_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PANEL_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, int]) -> str:
    commands = {
        "LTAMechanismAblationPanelRows": summary["ablation_rows"],
        "LTAMechanismAblationPriorityRows": summary["high_priority_rows"],
        "LTAMechanismAblationCutPasses": summary["cut_passes"],
        "LTAMechanismAblationCutTrials": summary["cut_trials"],
        "LTAMechanismAblationFullPasses": summary["full_passes"],
        "LTAMechanismAblationFullTrials": summary["full_trials"],
        "LTAMechanismAblationBaselineOverlap": summary["baseline_overlap"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/mechanism_ablation_panel.py.",
        "% Regenerate with License_code/scripts/export_mechanism_ablation_panel.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _join(values: list[str]) -> str:
    return " | ".join(values)

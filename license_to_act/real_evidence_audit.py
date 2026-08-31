from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


AUDIT_FIELDS = [
    "evidence_id",
    "source_table",
    "paper_role",
    "evidence_kind",
    "source_ref",
    "artifact_status",
    "counts_as_main_result",
    "notes",
]


def build_real_evidence_audit(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    data_dir = root / "License_paper" / "data"

    rows: list[dict[str, str]] = []
    rows.extend(_headline_rows(data_dir / "headline_result_panel.csv"))
    rows.extend(_stage2_rows(data_dir / "stage2_reliability.csv"))
    rows.extend(_model_loop_rows(data_dir / "model_in_loop_bridge.csv"))
    rows.extend(_tau2_rows(data_dir / "tau2_commit_mining.csv", root / "artifacts/stage2/tau2_commit_mining_20260830.json"))
    rows.extend(_scale_plan_rows(data_dir / "submission_scale_plan.csv"))

    summary = {
        "audit_rows": len(rows),
        "real_harbor_rows": sum(1 for row in rows if row["evidence_kind"] == "real_official_harbor"),
        "derived_real_rows": sum(1 for row in rows if row["evidence_kind"] == "derived_from_real_artifacts"),
        "planned_rows": sum(1 for row in rows if row["evidence_kind"] == "planned_matrix"),
        "main_positive_planned_rows": sum(
            1
            for row in rows
            if row["paper_role"] == "main_positive_evidence"
            and row["evidence_kind"] == "planned_matrix"
        ),
        "missing_artifact_rows": sum(1 for row in rows if row["artifact_status"] == "missing"),
        "unparseable_artifact_rows": sum(1 for row in rows if row["artifact_status"] == "unparseable"),
        "main_result_rows": sum(1 for row in rows if row["counts_as_main_result"] == "yes"),
    }
    return {"summary": summary, "rows": rows}


def write_real_evidence_audit(
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
        else root / "artifacts" / "paper_results" / "lta_real_evidence_audit_20260831.json"
    )

    audit = build_real_evidence_audit(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    audit_csv = paper_data_dir / "real_evidence_audit.csv"
    latex_numbers = paper_sections_dir / "generated_real_evidence_numbers.tex"
    _write_csv(audit_csv, AUDIT_FIELDS, audit["rows"])
    latex_numbers.write_text(_latex_numbers(audit["summary"]), encoding="utf-8")

    audit["outputs"] = {
        "summary_json": str(summary_path),
        "audit_csv": str(audit_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    return audit


def _headline_rows(path: Path) -> list[dict[str, str]]:
    rows = []
    for row in _read_csv(path):
        source_data = row["source_data"]
        evidence_kind = "planned_matrix" if "submission_scale_plan.csv" in source_data else "derived_from_real_artifacts"
        counts = "yes" if row["paper_role"] == "main_positive_evidence" and evidence_kind != "planned_matrix" else "no"
        rows.append(
            _row(
                evidence_id=f"headline:{row['panel_id']}",
                source_table=path.name,
                paper_role=row["paper_role"],
                evidence_kind=evidence_kind,
                source_ref=source_data,
                artifact_status="not_applicable",
                counts_as_main_result=counts,
                notes=row["story_question"],
            )
        )
    return rows


def _stage2_rows(path: Path) -> list[dict[str, str]]:
    rows = []
    for row in _read_csv(path):
        artifact_status = _artifact_status(Path(row["result_path"]))
        kind = "real_official_harbor" if artifact_status == "parseable" else f"{artifact_status}_artifact"
        counts = "yes" if artifact_status == "parseable" else "no"
        rows.append(
            _row(
                evidence_id=f"stage2:{row['case_id']}",
                source_table=path.name,
                paper_role=row["paper_use"],
                evidence_kind=kind,
                source_ref=row["result_path"],
                artifact_status=artifact_status,
                counts_as_main_result=counts,
                notes=f"{row['n_trials']} trials; mean reward {row['mean_reward']}",
            )
        )
    return rows


def _model_loop_rows(path: Path) -> list[dict[str, str]]:
    rows = []
    for row in _read_csv(path):
        artifact_status = _artifact_status(Path(row["source_path"]))
        kind = "real_official_harbor" if artifact_status == "parseable" else f"{artifact_status}_artifact"
        counts = "yes" if artifact_status == "parseable" and row["paper_use"] != "runtime_reliability" else "no"
        rows.append(
            _row(
                evidence_id=f"model_loop:{row['bridge_id']}",
                source_table=path.name,
                paper_role=row["paper_use"],
                evidence_kind=kind,
                source_ref=row["source_path"],
                artifact_status=artifact_status,
                counts_as_main_result=counts,
                notes=f"{row['passes']}/{row['n_trials']} passes; {row['official_verifier_result']}",
            )
        )
    return rows


def _tau2_rows(csv_path: Path, artifact_path: Path) -> list[dict[str, str]]:
    metrics = {row["metric"]: row["value"] for row in _read_csv(csv_path)}
    artifact_status = _artifact_status(artifact_path)
    return [
        _row(
            evidence_id="tau2:commit_mining",
            source_table=csv_path.name,
            paper_role="main_positive_evidence",
            evidence_kind="derived_from_real_artifacts" if artifact_status == "parseable" else f"{artifact_status}_artifact",
            source_ref=str(artifact_path),
            artifact_status=artifact_status,
            counts_as_main_result="yes" if artifact_status == "parseable" else "no",
            notes=(
                f"{metrics.get('read_correct_write_wrong_proxy', '0')} read-correct/write-wrong "
                f"commits from {metrics.get('result_files', '0')} result files"
            ),
        )
    ]


def _scale_plan_rows(path: Path) -> list[dict[str, str]]:
    return [
        _row(
            evidence_id=f"scale_plan:{row['target_id']}",
            source_table=path.name,
            paper_role="planned_scale_target",
            evidence_kind="planned_matrix",
            source_ref=path.name,
            artifact_status="not_applicable",
            counts_as_main_result="no",
            notes=f"target role: {row['paper_use']}; next run: {row['next_run']}",
        )
        for row in _read_csv(path)
    ]


def _artifact_status(path: Path) -> str:
    if not path.exists():
        return "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "unparseable"
    stats = payload.get("stats")
    if isinstance(stats, dict) and isinstance(stats.get("evals"), dict):
        return "parseable"
    verifier_result = payload.get("verifier_result")
    if isinstance(verifier_result, dict) and isinstance(verifier_result.get("rewards"), dict):
        return "parseable"
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return "parseable"
    return "unparseable"


def _row(
    *,
    evidence_id: str,
    source_table: str,
    paper_role: str,
    evidence_kind: str,
    source_ref: str,
    artifact_status: str,
    counts_as_main_result: str,
    notes: str,
) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "source_table": source_table,
        "paper_role": paper_role,
        "evidence_kind": evidence_kind,
        "source_ref": source_ref,
        "artifact_status": artifact_status,
        "counts_as_main_result": counts_as_main_result,
        "notes": notes,
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTARealEvidenceRows": summary["audit_rows"],
        "LTARealEvidenceHarborRows": summary["real_harbor_rows"],
        "LTARealEvidenceDerivedRows": summary["derived_real_rows"],
        "LTARealEvidencePlannedRows": summary["planned_rows"],
        "LTARealEvidenceMainPositivePlannedRows": summary["main_positive_planned_rows"],
        "LTARealEvidenceMissingArtifacts": summary["missing_artifact_rows"],
        "LTARealEvidenceUnparseableArtifacts": summary["unparseable_artifact_rows"],
        "LTARealEvidenceMainResultRows": summary["main_result_rows"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/real_evidence_audit.py.",
        "% Regenerate with License_code/scripts/export_real_evidence_audit.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"

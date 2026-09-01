from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.recursive_amendment_lineage import (
    build_recursive_amendment_lineage,
    write_recursive_amendment_lineage,
)


def test_build_recursive_amendment_lineage_exposes_contract_refinement_generations() -> None:
    lineage = build_recursive_amendment_lineage(Path("/data/zhiqi/License"))

    summary = lineage["summary"]
    assert summary["candidate_amendments"] == 5
    assert summary["accepted_amendments"] == 5
    assert summary["compiler_generations"] == 3
    assert summary["source_benchmark_families"] == 3
    assert summary["source_failure_to_pass"] == 5
    assert summary["heldout_clean_trials"] == 35
    assert summary["pass_to_failure_regressions"] == 0
    assert summary["mean_generation_gain"] > 0

    rows = lineage["rows"]
    assert [row["refinement_id"] for row in rows] == [
        "T2-A1-action-boundary-pre-commit",
        "T2-A48-action-boundary-pre-commit",
        "TB-SAN-001",
        "TB-WAL-001",
        "SF-INV-001",
    ]
    assert all(row["synthesis_method"] == "frozen_meta_agent_proposal" for row in rows)
    assert all(row["admission_decision"] == "accept" for row in rows)
    assert all(row["baseline_boundary"] != "faithful_baseline" for row in rows)


def test_recursive_amendment_lineage_keeps_baselines_and_ablation_boundaries_separate() -> None:
    rows = build_recursive_amendment_lineage(Path("/data/zhiqi/License"))["rows"]

    assert all(row["comparison_class"] == "boundary_update" for row in rows)
    assert all("task-ID" not in row["contract_diff"] for row in rows)
    assert any(row["boundary"] == "ready" for row in _boundary_rows(rows))
    assert any(row["boundary"] == "done" for row in _boundary_rows(rows))
    assert any("preserving-read" in row["contract_diff"] for row in rows)
    assert any("HEAD and remote" in row["contract_diff"] for row in rows)


def test_write_recursive_amendment_lineage_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_recursive_amendment_lineage(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "contract_refinement_lineage.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["lineage_csv"]).exists()
    assert "legacy_lineage_csv" not in output["outputs"]
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["lineage_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 5
    assert rows[0]["source_cases"] == "T2-A1"
    assert rows[4]["heldout_cases"] == "SF-INV-BP-K5 | SF-TRAVEL-BP-K5 | TB-LOG-K5"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTARecursiveCandidateAmendments}{5}" in tex
    assert "\\newcommand{\\LTARecursiveAcceptedAmendments}{5}" in tex
    assert "\\newcommand{\\LTARecursiveCompilerGenerations}{3}" in tex
    assert "\\newcommand{\\LTARecursiveSourceFtoP}{5}" in tex
    assert "\\newcommand{\\LTARecursiveHeldoutTrials}{35}" in tex
    assert "\\newcommand{\\LTARecursivePtoF}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["source_failure_to_pass"] == 5


def test_export_recursive_amendment_lineage_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "contract_refinement_lineage.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_contract_refinement_lineage.py",
            "--paper-data-dir",
            str(tmp_path / "paper-data"),
            "--paper-sections-dir",
            str(tmp_path / "sections"),
            "--summary",
            str(summary_path),
        ],
        cwd="/data/zhiqi/License/License_code",
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert str(summary_path) in result.stdout
    assert (tmp_path / "paper-data" / "contract_refinement_lineage.csv").exists()
    assert not (tmp_path / "paper-data" / "recursive_amendment_lineage.csv").exists()
    assert (tmp_path / "sections" / "generated_recursive_numbers.tex").exists()


def _boundary_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "boundary": "ready" if row["generation"] == "1" else "done" if row["generation"] == "3" else "preserve",
            **row,
        }
        for row in rows
    ]

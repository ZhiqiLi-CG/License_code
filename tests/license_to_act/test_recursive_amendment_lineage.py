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


def test_build_recursive_amendment_lineage_exposes_automatic_compiler_generations() -> None:
    lineage = build_recursive_amendment_lineage(Path("/data/zhiqi/License"))

    summary = lineage["summary"]
    assert summary["candidate_amendments"] == 4
    assert summary["accepted_amendments"] == 4
    assert summary["compiler_generations"] == 3
    assert summary["source_benchmark_families"] == 3
    assert summary["source_failure_to_pass"] == 5
    assert summary["heldout_clean_trials"] == 25
    assert summary["pass_to_failure_regressions"] == 0
    assert summary["mean_generation_gain"] > 0

    rows = lineage["rows"]
    assert [row["amendment_id"] for row in rows] == [
        "A1_POLICY_AUTHORIZATION_EVIDENCE",
        "A2_REGION_AND_SIDE_EFFECT_BOUNDS",
        "A3_EVIDENCE_CONSUMING_READ_LICENSE",
        "A4_POSITIVE_OUTPUT_OBLIGATION",
    ]
    assert all(row["synthesis_method"] == "automatic_failure_signature_rule" for row in rows)
    assert all(row["admission_decision"] == "accept" for row in rows)
    assert all(row["baseline_boundary"] != "faithful_baseline" for row in rows)


def test_recursive_amendment_lineage_keeps_baselines_and_ablation_boundaries_separate() -> None:
    rows = build_recursive_amendment_lineage(Path("/data/zhiqi/License"))["rows"]

    assert all(row["comparison_class"] == "compiler_amendment" for row in rows)
    assert all("task-ID" not in row["license_diff"] for row in rows)
    assert any("PolicyAuthorizationEvidence" in row["license_diff"] for row in rows)
    assert any("OBLIGE" in row["license_diff"] for row in rows)
    assert any("read_license" in row["license_diff"] for row in rows)
    assert any("forbidden_side_effects" in row["license_diff"] for row in rows)


def test_write_recursive_amendment_lineage_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_recursive_amendment_lineage(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "recursive_amendment_lineage.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["lineage_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["lineage_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 4
    assert rows[0]["source_cases"] == "T2-A1 | T2-A48"
    assert rows[3]["heldout_cases"] == "SF-TRAVEL-MAT-K5"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTARecursiveCandidateAmendments}{4}" in tex
    assert "\\newcommand{\\LTARecursiveAcceptedAmendments}{4}" in tex
    assert "\\newcommand{\\LTARecursiveCompilerGenerations}{3}" in tex
    assert "\\newcommand{\\LTARecursiveSourceFtoP}{5}" in tex
    assert "\\newcommand{\\LTARecursiveHeldoutTrials}{25}" in tex
    assert "\\newcommand{\\LTARecursivePtoF}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["source_failure_to_pass"] == 5


def test_export_recursive_amendment_lineage_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "recursive_amendment_lineage.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_recursive_amendment_lineage.py",
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
    assert (tmp_path / "paper-data" / "recursive_amendment_lineage.csv").exists()
    assert (tmp_path / "sections" / "generated_recursive_numbers.tex").exists()

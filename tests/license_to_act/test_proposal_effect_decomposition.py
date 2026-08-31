from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.proposal_effect_decomposition import (
    build_proposal_effect_decomposition,
    write_proposal_effect_decomposition,
)


def test_build_proposal_effect_decomposition_uses_real_rows_not_plans() -> None:
    report = build_proposal_effect_decomposition(Path("/data/zhiqi/License"))

    summary = report["summary"]
    assert summary["rows"] == 6
    assert summary["benchmark_count"] == 3
    assert summary["planned_rows"] == 0
    assert summary["gap_observations"] == 29
    assert summary["gap_source_observations"] == 9
    assert summary["gap_distributional_observations"] == 20
    assert summary["baseline_effect_successes_on_gap_rows"] == 0
    assert summary["boundary_effect_successes_on_source_gap_rows"] == 9

    rows = {row["decomposition_id"]: row for row in report["rows"]}
    assert rows["TAU2_MINED_CANCEL_RCWW"]["evidence_type"] == "distributional_mining"
    assert rows["TAU2_MINED_CANCEL_RCWW"]["proposal_successes"] == "20"
    assert rows["TAU2_MINED_CANCEL_RCWW"]["effect_successes_without_boundary"] == "0"
    assert rows["TAU2_A48_MISTRAL_MATCHED_K5"]["evidence_type"] == "matched_actor_k5"
    assert rows["TAU2_A48_MISTRAL_MATCHED_K5"]["proposal_successes"] == "5"
    assert rows["TAU2_A48_MISTRAL_MATCHED_K5"]["effect_successes_with_boundary"] == "5"
    assert rows["SF_INVOICE_QWEN_PROMPT"]["benchmark"] == "SkillFlow"
    assert all(row["counts_as_planned"] == "no" for row in report["rows"])


def test_write_proposal_effect_decomposition_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_proposal_effect_decomposition(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "proposal_effect_decomposition.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 6
    assert rows[0]["decomposition_id"] == "TAU2_MINED_CANCEL_RCWW"

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAProposalEffectRows}{6}" in tex
    assert "\\newcommand{\\LTAProposalEffectGapObservations}{29}" in tex
    assert "\\newcommand{\\LTAProposalEffectBoundarySourceSuccesses}{9}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["gap_rate_on_gap_rows"] == 1.0


def test_export_proposal_effect_decomposition_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "proposal_effect_decomposition.json"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_proposal_effect_decomposition.py",
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
    assert (tmp_path / "paper-data" / "proposal_effect_decomposition.csv").exists()
    assert (tmp_path / "sections" / "generated_proposal_effect_numbers.tex").exists()

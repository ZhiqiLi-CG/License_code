from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.commit_pair_metrics import (
    compute_commit_pair_metrics,
    write_commit_pair_metrics,
)


def test_compute_commit_pair_metrics_scores_ready_and_premature_pair() -> None:
    rows = [
        {
            "pair_id": "PAIR-1",
            "benchmark": "tau2-Bench",
            "method": "StateTx",
            "authority_state": "ready",
            "expected_commit": "yes",
            "observed_commit": "yes",
            "official_reward": "1",
        },
        {
            "pair_id": "PAIR-1",
            "benchmark": "tau2-Bench",
            "method": "StateTx",
            "authority_state": "premature",
            "expected_commit": "no",
            "observed_commit": "no",
            "official_reward": "1",
        },
    ]

    metrics = compute_commit_pair_metrics(rows)

    assert metrics["summary"]["pair_count"] == 1
    assert metrics["summary"]["ready_opportunities"] == 1
    assert metrics["summary"]["premature_opportunities"] == 1
    assert metrics["summary"]["commit_pair_accuracy"] == 1.0
    assert metrics["summary"]["unauthorized_commit_rate"] == 0.0
    assert metrics["summary"]["authorized_commit_recall"] == 1.0
    assert metrics["summary"]["mean_official_reward"] == 1.0


def test_compute_commit_pair_metrics_counts_blanket_commit_and_blanket_block() -> None:
    rows = [
        {
            "pair_id": "PAIR-COMMIT",
            "benchmark": "SkillFlow",
            "method": "blanket commit",
            "authority_state": "ready",
            "expected_commit": "yes",
            "observed_commit": "yes",
            "official_reward": "1",
        },
        {
            "pair_id": "PAIR-COMMIT",
            "benchmark": "SkillFlow",
            "method": "blanket commit",
            "authority_state": "premature",
            "expected_commit": "no",
            "observed_commit": "yes",
            "official_reward": "0",
        },
        {
            "pair_id": "PAIR-BLOCK",
            "benchmark": "Terminal-Bench 2.1",
            "method": "blanket block",
            "authority_state": "ready",
            "expected_commit": "yes",
            "observed_commit": "no",
            "official_reward": "0",
        },
        {
            "pair_id": "PAIR-BLOCK",
            "benchmark": "Terminal-Bench 2.1",
            "method": "blanket block",
            "authority_state": "premature",
            "expected_commit": "no",
            "observed_commit": "no",
            "official_reward": "1",
        },
    ]

    metrics = compute_commit_pair_metrics(rows)

    assert metrics["summary"]["pair_count"] == 2
    assert metrics["summary"]["commit_pair_accuracy"] == 0.0
    assert metrics["summary"]["unauthorized_commit_rate"] == 0.5
    assert metrics["summary"]["authorized_commit_recall"] == 0.5
    assert metrics["summary"]["mean_official_reward"] == 0.5
    assert {row["pair_id"] for row in metrics["pair_rows"]} == {"PAIR-COMMIT", "PAIR-BLOCK"}


def test_write_commit_pair_metrics_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_commit_pair_metrics(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "commit_pair_metrics.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["metrics_csv"]).exists()
    assert Path(output["outputs"]["pairs_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["metrics_csv"]).open(newline="", encoding="utf-8")))
    values = {row["metric"]: row["value"] for row in rows}
    assert values["commit_pair_accuracy"] == "1.000"
    assert values["unauthorized_commit_rate"] == "0.000"
    assert values["authorized_commit_recall"] == "1.000"
    assert values["pair_count"] == "4"

    member_rows = list(csv.DictReader(Path(output["outputs"]["pairs_csv"]).open(newline="", encoding="utf-8")))
    assert {row["expected_commit"] for row in member_rows} == {"yes", "no"}
    assert {row["observed_commit"] for row in member_rows} == {"yes", "no"}

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTACommitPairAccuracy}{1.000}" in tex
    assert "\\newcommand{\\LTAUnauthorizedCommitRate}{0.000}" in tex
    assert "\\newcommand{\\LTAAuthorizedCommitRecall}{1.000}" in tex
    assert "\\newcommand{\\LTACommitPairCount}{4}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["pair_count"] == 4


def test_export_commit_pair_metrics_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "commit_pair_metrics.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_commit_pair_metrics.py",
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
    assert (tmp_path / "paper-data" / "commit_pair_metrics.csv").exists()
    assert (tmp_path / "paper-data" / "commit_pair_members.csv").exists()
    assert (tmp_path / "sections" / "generated_commit_pair_numbers.tex").exists()

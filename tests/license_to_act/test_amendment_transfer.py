from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from license_to_act.amendment_transfer import build_amendment_transfer_report


def test_builds_cross_benchmark_transfer_report_from_artifacts(tmp_path):
    tau2_task1 = _write_json(
        tmp_path / "tau2_task1.json",
        _tau2_pair("1", baseline_reward=0.0, intervention_reward=1.0, flip="F_to_P"),
    )
    tau2_task19 = _write_json(
        tmp_path / "tau2_task19.json",
        _tau2_pair("19", baseline_reward=1.0, intervention_reward=1.0, flip="unchanged"),
    )
    tb_codex = _write_json(tmp_path / "tb_codex.json", _harbor_result("sanitize-git-repo__bad", 0.0))
    tb_lta = _write_json(tmp_path / "tb_lta.json", _harbor_result("sanitize-git-repo__good", 1.0))
    tb_evidence = _write_json(
        tmp_path / "tb_evidence.json",
        {
            "changed_paths": ["ray_processing/process.py"],
            "unauthorized_paths": [],
            "side_effects": [],
            "head_before": "abc",
            "head_after": "abc",
            "remote_before": "origin\turl",
            "remote_after": "origin\turl",
        },
    )
    tb_dbwal_baseline = _write_json(tmp_path / "tb_dbwal_baseline.json", _harbor_result("db-wal-recovery__bad", 0.0))
    tb_dbwal_lta = _write_json(tmp_path / "tb_dbwal_lta.json", _harbor_result("db-wal-recovery__good", 1.0))
    tb_dbwal_evidence = _write_json(
        tmp_path / "tb_dbwal_evidence.json",
        {
            "xor_key": 66,
            "row_count": 11,
            "wal_exists_before": True,
            "wal_exists_after": True,
            "side_effects": [],
        },
    )
    skill_prompt = _write_json(tmp_path / "skill_prompt.json", _harbor_result("invoice__bad", 0.0))
    skill_lta = _write_json(tmp_path / "skill_lta.json", _harbor_result("invoice__good", 1.0))
    skill_evidence = _write_json(
        tmp_path / "skill_evidence.json",
        {"pre_existing_output": False, "rows": [{"filename": "inv_001.jpg"}], "output_exists": True},
    )

    report = build_amendment_transfer_report(
        tau2_pair_paths=[tau2_task1, tau2_task19],
        terminal_bench_baseline_path=tb_codex,
        terminal_bench_lta_path=tb_lta,
        terminal_bench_evidence_path=tb_evidence,
        terminal_bench_db_wal_baseline_path=tb_dbwal_baseline,
        terminal_bench_db_wal_lta_path=tb_dbwal_lta,
        terminal_bench_db_wal_evidence_path=tb_dbwal_evidence,
        skillflow_baseline_path=skill_prompt,
        skillflow_lta_path=skill_lta,
        skillflow_evidence_path=skill_evidence,
    )

    assert report["amendment"]["name"] == "separate_intent_from_authorization"
    assert report["source"]["tau2"]["f_to_p"] == 1
    assert report["source"]["tau2"]["unchanged_positive"] == 1
    terminal_bench = report["transfer_checks"]["terminal_bench_2_1"]
    assert terminal_bench["n_tasks"] == 2
    assert terminal_bench["f_to_p"] == 2
    assert terminal_bench["checks"][0]["task"] == "sanitize-git-repo"
    assert terminal_bench["checks"][0]["reward_flip"] == "F_to_P"
    assert terminal_bench["checks"][0]["side_effects"] == []
    assert terminal_bench["checks"][1]["task"] == "db-wal-recovery"
    assert terminal_bench["checks"][1]["reward_flip"] == "F_to_P"
    assert terminal_bench["checks"][1]["wal_preserved"] is True
    assert terminal_bench["checks"][1]["row_count"] == 11
    assert report["transfer_checks"]["skillflow"]["reward_flip"] == "F_to_P"
    assert report["transfer_checks"]["skillflow"]["pre_existing_output"] is False


def test_transfer_report_script_runs_directly_from_project_root():
    proc = subprocess.run(
        [sys.executable, "scripts/build_lta_amendment_transfer_report.py", "--help"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    assert "usage:" in proc.stdout


def _tau2_pair(task_id: str, baseline_reward: float, intervention_reward: float, flip: str) -> dict:
    return {
        "benchmark": "tau2-Bench",
        "domain": "airline",
        "task_id": task_id,
        "baseline": {"reward": baseline_reward, "reward_breakdown": {"DB": baseline_reward}},
        "intervention": {"reward": intervention_reward, "reward_breakdown": {"DB": intervention_reward}},
        "outcome": {"flip": flip, "communicate_regression": False},
    }


def _harbor_result(trial: str, reward: float) -> dict:
    return {
        "stats": {
            "evals": {
                "agent__adhoc": {
                    "reward_stats": {"reward": {str(reward): [trial]}},
                    "metrics": [{"mean": reward}],
                    "n_errors": 0,
                }
            }
        }
    }


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path

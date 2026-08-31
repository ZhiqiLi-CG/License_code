from __future__ import annotations

import json

from license_to_act.stage2_results import write_stage2_paper_results


def test_exports_stage2_reliability_and_tau2_mining(tmp_path):
    tau2_path = tmp_path / "tau2.json"
    tau2_path.write_text(
        json.dumps(
            {
                "summary": {
                    "n_result_files": 2,
                    "n_simulations": 3,
                    "n_infrastructure_error_simulations": 1,
                    "n_cancel_decisions": 2,
                    "n_lta_vetoes": 1,
                    "n_lta_allows": 1,
                    "n_vetoes_with_user_intent": 1,
                    "n_vetoes_with_reservation_state": 1,
                    "n_vetoes_with_matched_reservation_read": 1,
                    "n_vetoes_with_reward_zero": 1,
                    "n_vetoes_with_db_failure": 1,
                    "n_read_correct_write_wrong_proxy": 1,
                    "n_license_allows_with_reward_one": 1,
                },
                "by_model": {
                    "Qwen3.8-27B": {
                        "n_cancel_decisions": 2,
                        "n_lta_vetoes": 1,
                        "n_lta_allows": 1,
                        "n_read_correct_write_wrong_proxy": 1,
                        "mean_reward_on_cancel_decisions": 0.5,
                    }
                },
                "by_condition_family": {},
                "by_domain": {},
            }
        ),
        encoding="utf-8",
    )
    harbor_path = tmp_path / "harbor.json"
    harbor_path.write_text(
        json.dumps(
            {
                "stats": {
                    "evals": {
                        "agent__adhoc": {
                            "n_trials": 5,
                            "n_errors": 0,
                            "metrics": [{"mean": 1.0}],
                            "pass_at_k": {"2": 1.0, "4": 1.0, "5": 1.0},
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    paper_data_dir = tmp_path / "paper-data"
    summary = write_stage2_paper_results(
        tau2_mining_path=tau2_path,
        reliability_cases=[
            {
                "case_id": "TB-K5",
                "benchmark": "Terminal-Bench 2.1",
                "task": "task",
                "condition": "condition",
                "role": "role",
                "result_path": harbor_path,
                "paper_use": "clean_reliability_anchor",
                "interpretation": "interpretation",
            },
            {
                "case_id": "TB-QWEN32K",
                "benchmark": "Terminal-Bench 2.1",
                "task": "task",
                "condition": "baseline condition",
                "role": "faithful long-context baseline",
                "result_path": harbor_path,
                "paper_use": "faithful_baseline",
                "interpretation": "baseline interpretation",
            }
        ],
        paper_data_dir=paper_data_dir,
        summary_path=tmp_path / "summary.json",
    )

    assert summary["clean_reliability_trials"] == 5
    assert summary["clean_reliability_errors"] == 0
    assert summary["faithful_baseline_trials"] == 5
    assert summary["faithful_baseline_errors"] == 0
    assert summary["tau2_read_correct_write_wrong_proxy"] == 1
    assert (paper_data_dir / "stage2_reliability.csv").read_text(encoding="utf-8").splitlines()[1].startswith(
        "TB-K5,"
    )
    assert "read_correct_write_wrong_proxy,1," in (paper_data_dir / "tau2_commit_mining.csv").read_text(
        encoding="utf-8"
    )
    assert not (paper_data_dir / "tau2_authority_mining.csv").exists()

from __future__ import annotations

from license_to_act.tau2_matched_experiment import summarize_tau2_matched_runs


def test_summarizes_matched_tau2_boundary_runs():
    runs = [
        {
            "pair_id": "airline-1-seed-7",
            "condition": "baseline",
            "reward": 0.0,
            "cancel_tool_calls": 1,
            "read_correct_write_wrong": True,
            "boundary_records": [],
        },
        {
            "pair_id": "airline-1-seed-7",
            "condition": "action_boundary",
            "reward": 1.0,
            "cancel_tool_calls": 0,
            "read_correct_write_wrong": False,
            "boundary_records": [{"allowed": False, "reason": "missing_required_evidence"}],
        },
        {
            "pair_id": "airline-19-seed-7",
            "condition": "baseline",
            "reward": 1.0,
            "cancel_tool_calls": 1,
            "read_correct_write_wrong": False,
            "boundary_records": [],
        },
        {
            "pair_id": "airline-19-seed-7",
            "condition": "action_boundary",
            "reward": 1.0,
            "cancel_tool_calls": 1,
            "read_correct_write_wrong": False,
            "boundary_records": [{"allowed": True, "reason": "licensed"}],
        },
    ]

    summary = summarize_tau2_matched_runs(runs)

    assert summary == {
        "pairs": 2,
        "complete_pairs": 2,
        "baseline_trials": 2,
        "boundary_trials": 2,
        "baseline_mean_reward": 0.5,
        "boundary_mean_reward": 1.0,
        "reward_delta": 0.5,
        "baseline_read_correct_write_wrong": 1,
        "boundary_read_correct_write_wrong": 0,
        "boundary_vetoes": 1,
        "boundary_allows": 1,
        "boundary_regressions": 0,
    }

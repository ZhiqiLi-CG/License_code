from __future__ import annotations

import json

from license_to_act.tau2_authority_mining import mine_tau2_authority_results


def test_mines_read_correct_write_wrong_cancel_decision(tmp_path):
    result_path = tmp_path / "rsi8_stage1_qwen_airline_train_1_20260830" / "results.json"
    result_path.parent.mkdir()
    result_path.write_text(
        json.dumps(
            {
                "simulations": [
                    {
                        "task_id": "1",
                        "policy": "The current time is 2024-05-15 15:00:00.",
                        "messages": [
                            {"role": "user", "content": "Please cancel due to a change of plans."},
                            {
                                "role": "tool",
                                "content": json.dumps(
                                    {
                                        "reservation_id": "Q69X3R",
                                        "cabin": "economy",
                                        "created_at": "2024-05-14T09:52:38",
                                        "insurance": "no",
                                        "flights": [{"status": "available"}],
                                    }
                                ),
                            },
                            {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {"name": "cancel_reservation", "arguments": {"reservation_id": "Q69X3R"}}
                                ],
                            },
                        ],
                        "reward_info": {
                            "reward": 0.0,
                            "reward_breakdown": {"DB": 0.0, "COMMUNICATE": 1.0},
                            "action_checks": [
                                {
                                    "action": {
                                        "name": "get_reservation_details",
                                        "arguments": {"reservation_id": "Q69X3R"},
                                    },
                                    "action_match": True,
                                }
                            ],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = mine_tau2_authority_results([result_path])

    assert report["summary"]["n_result_files"] == 1
    assert report["summary"]["n_cancel_decisions"] == 1
    assert report["summary"]["n_lta_vetoes"] == 1
    assert report["summary"]["n_vetoes_with_matched_reservation_read"] == 1
    assert report["summary"]["n_read_correct_write_wrong_proxy"] == 1
    assert report["decisions"][0]["model"] == "Qwen3.8-27B"
    assert report["decisions"][0]["domain"] == "airline"


def test_separates_infrastructure_errors_from_agent_decisions(tmp_path):
    result_path = tmp_path / "rsi3_probe_qwen_retail_train_0" / "results.json"
    result_path.parent.mkdir()
    result_path.write_text(
        json.dumps(
            {
                "simulations": [
                    {
                        "task_id": "0",
                        "info": {
                            "error_type": "ContextWindowExceededError",
                            "error": "maximum context length is 8192 tokens",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = mine_tau2_authority_results([result_path])

    assert report["summary"]["n_simulations"] == 1
    assert report["summary"]["n_infrastructure_error_simulations"] == 1
    assert report["summary"]["n_cancel_decisions"] == 0
    assert report["infrastructure_errors"][0]["error_type"] == "ContextWindowExceededError"

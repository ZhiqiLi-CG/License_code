from __future__ import annotations

import json

from license_to_act.tau2_replay import replay_tau2_cancel_decisions


def test_replays_tau2_result_as_license_decisions(tmp_path):
    result_path = tmp_path / "results.json"
    result_path.write_text(
        json.dumps(
            {
                "simulations": [
                    {
                        "task_id": "1",
                        "messages": [
                            {"role": "user", "content": "I need to cancel because of a change of plans."},
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
                                    {
                                        "name": "cancel_reservation",
                                        "arguments": {"reservation_id": "Q69X3R"},
                                    }
                                ],
                            },
                        ],
                        "reward_info": {"reward": 0.0},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = replay_tau2_cancel_decisions(result_path, current_time="2024-05-15T15:00:00")

    assert report["path"] == str(result_path)
    assert report["simulations"][0]["task_id"] == "1"
    assert report["simulations"][0]["reward"] == 0.0
    assert report["simulations"][0]["decisions"] == [
        {
            "tool_name": "cancel_reservation",
            "reservation_id": "Q69X3R",
            "state_region": "reservation:Q69X3R",
            "operation": "CommitCancelReservation",
            "evidence_types": ["ReservationStateEvidence", "UserIntentEvidence"],
            "allowed": False,
            "reason": "missing_required_evidence",
            "missing_evidence": ["PolicyAuthorizationEvidence"],
        }
    ]

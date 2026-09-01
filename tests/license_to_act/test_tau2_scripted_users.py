from __future__ import annotations

import pytest

from license_to_act.tau2_scripted_users import scripted_tau2_user_utterances


def test_returns_real_task_script_for_airline_task1():
    utterances = scripted_tau2_user_utterances("airline", "1")

    assert utterances[0].startswith("Hi, I recently spoke")
    assert "raj_sanchez_7340" in " ".join(utterances)
    assert "support representative approved it" in " ".join(utterances)


def test_airline_task48_script_insists_on_cancel_request():
    utterances = scripted_tau2_user_utterances("airline", "48")

    joined = " ".join(utterances)
    assert "3RK2T9" in joined
    assert "please proceed" in joined
    assert "I booked it about 10 hours ago" in joined


def test_retail_task0_script_requests_exchange_and_explicitly_confirms():
    utterances = scripted_tau2_user_utterances("retail", "0")

    joined = " ".join(utterances)
    assert "Yusuf Rossi" in joined
    assert "19122" in joined
    assert "#W2378156" in joined
    assert "mechanical keyboard" in joined
    assert "smart thermostat" in joined
    assert "Yes" in joined
    assert "proceed" in joined


def test_retail_task1_script_narrows_exchange_to_thermostat():
    utterances = scripted_tau2_user_utterances("retail", "1")

    joined = " ".join(utterances)
    assert "Yusuf Rossi" in joined
    assert "#W2378156" in joined
    assert "mechanical keyboard" in joined
    assert "smart thermostat" in joined
    assert "rather only exchange the thermostat" in joined
    assert "only the thermostat exchange" in joined


def test_unknown_script_is_explicitly_rejected():
    with pytest.raises(KeyError):
        scripted_tau2_user_utterances("airline", "999")

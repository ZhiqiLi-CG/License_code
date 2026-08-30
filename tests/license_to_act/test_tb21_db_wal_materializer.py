from __future__ import annotations

import importlib
import json
import shutil
from pathlib import Path

import pytest


TASK_ENV_DIR = Path("/data/zhiqi/RSI1/external/terminal-bench-2-1/tasks/db-wal-recovery/environment")


def test_detects_xor_key_from_wal_magic_without_opening_database():
    materializer = _import_materializer()
    encrypted_wal = (TASK_ENV_DIR / "main.db-wal.encrypted").read_bytes()

    key = materializer.detect_xor_key_for_wal(encrypted_wal)
    decrypted_header = materializer.decrypt_xor(encrypted_wal[:4], key)

    assert key == 0x42
    assert decrypted_header == b"\x37\x7f\x06\x82"


def test_materializes_recovered_json_and_preserves_wal_evidence(tmp_path):
    materializer = _import_materializer()
    app_dir = _seed_db_wal_app(tmp_path)

    result = materializer.materialize_db_wal_recovery(app_dir)

    assert result.status == "fulfilled"
    assert result.decision.allowed is True
    assert result.event is not None
    assert result.event.evidence.types == {
        "WalHeaderEvidence",
        "WalDecryptionEvidence",
        "RecoveredRowsEvidence",
        "JsonSchemaEvidence",
    }
    assert result.event.side_effects == set()
    assert result.xor_key == 0x42
    assert result.recovered_path == app_dir / "recovered.json"
    assert result.wal_exists_after is True
    assert (app_dir / "main.db-wal").exists()

    rows = json.loads((app_dir / "recovered.json").read_text())
    assert rows == [
        {"id": 1, "name": "apple", "value": 150},
        {"id": 2, "name": "banana", "value": 250},
        {"id": 3, "name": "cherry", "value": 300},
        {"id": 4, "name": "date", "value": 400},
        {"id": 5, "name": "elderberry", "value": 500},
        {"id": 6, "name": "fig", "value": 600},
        {"id": 7, "name": "grape", "value": 700},
        {"id": 8, "name": "honeydew", "value": 800},
        {"id": 9, "name": "kiwi", "value": 900},
        {"id": 10, "name": "lemon", "value": 1000},
        {"id": 11, "name": "mango", "value": 1100},
    ]


def _import_materializer():
    try:
        return importlib.import_module("license_to_act.tb21_db_wal_materializer")
    except ModuleNotFoundError as exc:
        pytest.fail(f"db-wal materializer module is missing: {exc}")


def _seed_db_wal_app(tmp_path: Path) -> Path:
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    shutil.copy(TASK_ENV_DIR / "main.db", app_dir / "main.db")
    shutil.copy(TASK_ENV_DIR / "main.db-wal.encrypted", app_dir / "main.db-wal")
    return app_dir

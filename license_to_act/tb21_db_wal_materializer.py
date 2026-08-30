from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_commit_obligation, evaluate_event
from .examples import tb21_db_wal_recovery_license


WAL_MAGIC_HEADERS = (b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83")


@dataclass(frozen=True)
class DbWalRecoveryResult:
    status: str
    decision: Decision
    event: StateChangeEvent | None = None
    xor_key: int | None = None
    recovered_path: Path | None = None
    row_count: int = 0
    wal_exists_before: bool = False
    wal_exists_after: bool = False


def detect_xor_key_for_wal(encrypted_wal: bytes) -> int:
    if len(encrypted_wal) < 4:
        raise ValueError("WAL evidence is too short to contain a SQLite WAL header")

    for key in range(256):
        if decrypt_xor(encrypted_wal[:4], key) in WAL_MAGIC_HEADERS:
            return key

    raise ValueError("could not infer XOR key from SQLite WAL magic bytes")


def decrypt_xor(data: bytes, key: int) -> bytes:
    if not 0 <= key <= 0xFF:
        raise ValueError(f"XOR key must be a byte, got {key}")
    return bytes(byte ^ key for byte in data)


def fulfill_db_wal_recovery_obligation(
    required_event: StateChangeEvent,
    observed_events: list[StateChangeEvent],
    licenses: list[ActionLicense],
    app_dir: Path,
) -> DbWalRecoveryResult:
    decision = evaluate_commit_obligation(required_event, observed_events, licenses)
    if decision.reason != "missing_commit_obligation":
        return DbWalRecoveryResult(
            status="unchanged",
            decision=decision,
            recovered_path=app_dir / "recovered.json",
            wal_exists_before=(app_dir / "main.db-wal").exists(),
            wal_exists_after=(app_dir / "main.db-wal").exists(),
        )

    return materialize_db_wal_recovery(app_dir=app_dir, licenses=licenses)


def materialize_db_wal_recovery(
    app_dir: Path,
    licenses: list[ActionLicense] | None = None,
) -> DbWalRecoveryResult:
    app_dir = app_dir.resolve()
    db_path = app_dir / "main.db"
    wal_path = app_dir / "main.db-wal"
    recovered_path = app_dir / "recovered.json"
    licenses = licenses or [tb21_db_wal_recovery_license()]

    wal_exists_before = wal_path.exists()
    encrypted_wal = wal_path.read_bytes()
    xor_key = detect_xor_key_for_wal(encrypted_wal)
    decrypted_wal = decrypt_xor(encrypted_wal, xor_key)
    wal_path.write_bytes(decrypted_wal)

    rows = _read_items_from_repaired_wal(db_path)
    recovered_path.write_text(json.dumps(rows, indent=2) + "\n")

    if not wal_path.exists():
        wal_path.write_bytes(decrypted_wal)

    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="output:/app/recovered.json",
        operation="WriteRecoveredJson",
        evidence=EvidenceBundle(
            types={
                "WalHeaderEvidence",
                "WalDecryptionEvidence",
                "RecoveredRowsEvidence",
                "JsonSchemaEvidence",
            },
            refs={"/app/main.db-wal", "/app/main.db", "/app/recovered.json"},
        ),
        side_effects=set(),
    )
    decision = evaluate_event(event, licenses)

    return DbWalRecoveryResult(
        status="fulfilled" if decision.allowed else "blocked",
        decision=decision,
        event=event,
        xor_key=xor_key,
        recovered_path=recovered_path,
        row_count=len(rows),
        wal_exists_before=wal_exists_before,
        wal_exists_after=wal_path.exists(),
    )


def _read_items_from_repaired_wal(db_path: Path) -> list[dict[str, int | str]]:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        conn.execute("PRAGMA query_only=ON")
        rows = conn.execute("SELECT id, name, value FROM items ORDER BY id").fetchall()

    return [{"id": row[0], "name": row[1], "value": row[2]} for row in rows]

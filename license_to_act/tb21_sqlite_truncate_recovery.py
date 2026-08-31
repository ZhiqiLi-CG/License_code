from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import struct

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_event
from .examples import tb21_sqlite_truncate_recovery_license


WORD_RE = re.compile(rb"testword\d{2}")


@dataclass(frozen=True)
class RecoveredSqliteRow:
    word: str
    value: float
    offset: int
    value_codec: str


@dataclass(frozen=True)
class SqliteTruncateRecoveryResult:
    status: str
    decision: Decision
    event: StateChangeEvent
    output_path: Path
    row_count: int
    rows: tuple[RecoveredSqliteRow, ...]


def recover_rows_from_truncated_sqlite(data: bytes) -> tuple[RecoveredSqliteRow, ...]:
    rows_by_word: dict[str, RecoveredSqliteRow] = {}
    for match in WORD_RE.finditer(data):
        word = match.group(0).decode("ascii")
        decoded = _decode_value_after_word(data[match.end() : match.end() + 8])
        if decoded is None:
            continue
        value, codec = decoded
        rows_by_word.setdefault(
            word,
            RecoveredSqliteRow(
                word=word,
                value=value,
                offset=match.start(),
                value_codec=codec,
            ),
        )
    return tuple(rows_by_word[word] for word in sorted(rows_by_word))


def write_recovered_rows_json(rows: tuple[RecoveredSqliteRow, ...], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [{"word": row.word, "value": row.value} for row in rows]
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def build_sqlite_truncate_state_report(
    *,
    db_path: Path,
    output_path: Path,
    rows: tuple[RecoveredSqliteRow, ...],
) -> dict[str, object]:
    return {
        "license": "tb21_sqlite_truncate_recover_json",
        "operation": "WriteRecoveredJson",
        "state_region": "output:/app/recover.json",
        "evidence_types": [
            "TruncatedSqliteBytesEvidence",
            "RecoveredPayloadOffsetEvidence",
            "RecoveredRowsEvidence",
            "JsonSchemaEvidence",
        ],
        "source_path": str(db_path),
        "output_path": str(output_path),
        "row_count": len(rows),
        "rows": [
            {
                "word": row.word,
                "value": row.value,
                "offset": row.offset,
                "value_codec": row.value_codec,
            }
            for row in rows
        ],
        "artifact_gate": {
            "output_exists": output_path.exists(),
            "schema": [{"word": "str", "value": "float"}],
            "minimum_rows_for_official_score": 7,
        },
    }


def materialize_sqlite_truncate_recovery(
    app_dir: Path,
    licenses: list[ActionLicense] | None = None,
) -> SqliteTruncateRecoveryResult:
    app_dir = app_dir.resolve()
    db_path = app_dir / "trunc.db"
    output_path = app_dir / "recover.json"
    rows = recover_rows_from_truncated_sqlite(db_path.read_bytes())
    write_recovered_rows_json(rows, output_path)

    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="output:/app/recover.json",
        operation="WriteRecoveredJson",
        evidence=EvidenceBundle(
            types={
                "TruncatedSqliteBytesEvidence",
                "RecoveredPayloadOffsetEvidence",
                "RecoveredRowsEvidence",
                "JsonSchemaEvidence",
            },
            refs={"/app/trunc.db", "/app/recover.json"},
        ),
    )
    decision = evaluate_event(event, licenses or [tb21_sqlite_truncate_recovery_license()])
    return SqliteTruncateRecoveryResult(
        status="fulfilled" if decision.allowed else "blocked",
        decision=decision,
        event=event,
        output_path=output_path,
        row_count=len(rows),
        rows=rows,
    )


def _decode_value_after_word(value_bytes: bytes) -> tuple[float, str] | None:
    if len(value_bytes) >= 2 and value_bytes[1] in {0x0E, 0x0F}:
        return float(value_bytes[0]), "sqlite_payload_small_integer"

    if len(value_bytes) >= 8:
        value = struct.unpack(">d", value_bytes[:8])[0]
        if math.isfinite(value) and 0.01 <= abs(value) <= 1_000_000:
            return float(value), "sqlite_payload_float64_be"

    return None

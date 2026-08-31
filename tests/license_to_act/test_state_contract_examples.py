from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from license_to_act.state_contract_examples import (
    build_state_contract_examples,
    write_state_contract_examples,
)


def test_build_state_contract_examples_uses_transaction_terms() -> None:
    payload = build_state_contract_examples()

    assert payload["schema"] == "state_contract_examples_v1"
    assert len(payload["examples"]) >= 8
    text = json.dumps(payload)
    assert "CommitReadinessEvidence" in text
    assert "PolicyAuthorizationEvidence" not in text
    assert "Action License" not in text
    assert "GovKernel" not in text
    assert all("ready" in example for example in payload["examples"])
    assert all("write_scope" in example for example in payload["examples"])


def test_write_state_contract_examples_exports_paper_data(tmp_path: Path) -> None:
    output = write_state_contract_examples(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        summary_path=tmp_path / "artifacts" / "state_contract_examples.json",
    )

    data_path = Path(output["outputs"]["paper_data_json"])
    assert data_path.exists()
    assert data_path.name == "state_contract_examples.json"
    assert "PolicyAuthorizationEvidence" not in data_path.read_text(encoding="utf-8")


def test_export_state_contract_examples_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "state_contract_examples.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_state_contract_examples.py",
            "--paper-data-dir",
            str(tmp_path / "paper-data"),
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
    assert (tmp_path / "paper-data" / "state_contract_examples.json").exists()

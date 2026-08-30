from __future__ import annotations

import csv
import json

from license_to_act.paper_results import write_paper_results


def test_exports_paper_csvs_from_transfer_report(tmp_path):
    transfer_report = tmp_path / "transfer.json"
    transfer_report.write_text(json.dumps(_transfer_report()), encoding="utf-8")
    data_dir = tmp_path / "paper" / "data"
    summary_path = tmp_path / "artifacts" / "summary.json"

    summary = write_paper_results(
        transfer_report_path=transfer_report,
        paper_data_dir=data_dir,
        summary_path=summary_path,
    )

    assert summary["stage1_cases"] == 6
    assert summary["failure_to_pass"] == 5
    assert summary["preserved_positive"] == 1
    stage1_rows = _read_csv(data_dir / "stage1_cases.csv")
    assert stage1_rows[0]["case_id"] == "T2-A1"
    assert stage1_rows[0]["comparison_type"] == "paired intervention"
    assert stage1_rows[2]["case_id"] == "T2-A19"
    assert stage1_rows[2]["positive_control"] == "yes"
    transfer_rows = _read_csv(data_dir / "transfer_ledger.csv")
    assert transfer_rows[1]["target_family"] == "Terminal-Bench 2.1"
    assert transfer_rows[1]["failure_to_pass"] == "2"
    diagnostics = _read_csv(data_dir / "diagnostic_cases.csv")
    assert {row["case_id"] for row in diagnostics} == {
        "TB-SAN-C",
        "TB-SAN-L",
        "TB-WAL-Q",
        "TB-WAL-L",
        "SF-INV-P",
        "SF-INV-L",
    }
    assert json.loads(summary_path.read_text(encoding="utf-8"))["paper_data_dir"] == str(data_dir)


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _transfer_report():
    return {
        "amendment": {"name": "separate_intent_from_authorization"},
        "source": {
            "tau2": {
                "n_pairs": 3,
                "f_to_p": 2,
                "unchanged_positive": 1,
                "p_to_f": 0,
                "pairs": [
                    {"task_id": "1", "baseline_reward": 0.0, "intervention_reward": 1.0, "flip": "F_to_P"},
                    {"task_id": "48", "baseline_reward": 0.0, "intervention_reward": 1.0, "flip": "F_to_P"},
                    {"task_id": "19", "baseline_reward": 1.0, "intervention_reward": 1.0, "flip": "unchanged"},
                ],
            }
        },
        "transfer_checks": {
            "terminal_bench_2_1": {
                "n_tasks": 2,
                "f_to_p": 2,
                "p_to_f": 0,
                "checks": [
                    {
                        "task": "sanitize-git-repo",
                        "authority_failure": "overbroad_write_authority",
                        "baseline": {"agent": "codex-gpt-5.5", "reward": 0.0},
                        "license_to_act": {"agent": "LicenseToActTB21SanitizeAgent", "reward": 1.0},
                    },
                    {
                        "task": "db-wal-recovery",
                        "authority_failure": "evidence_consuming_read",
                        "baseline": {"agent": "terminus-2-qwen", "reward": 0.0},
                        "license_to_act": {"agent": "LicenseToActTB21DbWalRecoveryAgent", "reward": 1.0},
                        "row_count": 11,
                    },
                ],
            },
            "skillflow": {
                "task": "OCR-Data-Extraction/task_family_invoice_images",
                "baseline": {"agent": "terminus-2-qwen-prompt-only", "reward": 0.0},
                "license_to_act": {"agent": "qwen-cli-plus-govkernel", "reward": 1.0},
                "reward_flip": "F_to_P",
                "pre_existing_output": False,
                "output_exists": True,
                "materialized_rows": 15,
            },
        },
    }

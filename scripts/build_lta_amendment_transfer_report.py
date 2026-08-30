from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from license_to_act.amendment_transfer import write_amendment_transfer_report


DEFAULT_OUTPUT = Path("/data/zhiqi/RSI6/artifacts/amendment_transfer/lta_stage1_transfer_ledger_20260830.json")

DEFAULT_TAU2_PAIRS = [
    Path("/data/zhiqi/RSI8/artifacts/experiments/tau2_airline_task1_paired_precommit.json"),
    Path("/data/zhiqi/RSI8/artifacts/experiments/tau2_airline_task48_mistral_paired_precommit.json"),
    Path("/data/zhiqi/RSI8/artifacts/experiments/tau2_airline_task19_qwen_nonregression_precommit.json"),
]

DEFAULT_TB_BASELINE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_codex_gpt55_sanitize_git_repo/"
    "2026-08-30__17-04-40/result.json"
)
DEFAULT_TB_LTA = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_lta_sanitize_materializer_official/"
    "tb21-lta-sanitize-materializer-official/result.json"
)
DEFAULT_TB_EVIDENCE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_lta_sanitize_materializer_official/"
    "tb21-lta-sanitize-materializer-official/sanitize-git-repo__W3DQ4hn/"
    "agent/lta-govkernel-tb21-sanitize-evidence.json"
)
DEFAULT_TB_DB_WAL_BASELINE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_terminus_qwen_db_wal_recovery/"
    "2026-08-30__17-24-47/result.json"
)
DEFAULT_TB_DB_WAL_LTA = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_lta_db_wal_recovery_official/"
    "tb21-lta-db-wal-recovery-official/result.json"
)
DEFAULT_TB_DB_WAL_EVIDENCE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/tb21_lta_db_wal_recovery_official/"
    "tb21-lta-db-wal-recovery-official/db-wal-recovery__XbXwXq3/"
    "agent/lta-govkernel-tb21-dbwal-evidence.json"
)

DEFAULT_SKILLFLOW_BASELINE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/skillflow_terminus_qwen_invoice_images_lta_commit_protocol_forcebuild/"
    "2026-08-30__18-05-01/result.json"
)
DEFAULT_SKILLFLOW_LTA = Path(
    "/data/zhiqi/RSI6/artifacts/probes/skillflow_lta_qwen_invoice_govkernel_official_out256/"
    "skillflow-lta-qwen-invoice-govkernel-official-out256/result.json"
)
DEFAULT_SKILLFLOW_EVIDENCE = Path(
    "/data/zhiqi/RSI6/artifacts/probes/skillflow_lta_qwen_invoice_govkernel_official_out256/"
    "skillflow-lta-qwen-invoice-govkernel-official-out256/task_family_invoice_images__Fg3xp5a/"
    "agent/lta-govkernel-invoice-evidence.json"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    report = write_amendment_transfer_report(
        output_path=args.output,
        tau2_pair_paths=DEFAULT_TAU2_PAIRS,
        terminal_bench_baseline_path=DEFAULT_TB_BASELINE,
        terminal_bench_lta_path=DEFAULT_TB_LTA,
        terminal_bench_evidence_path=DEFAULT_TB_EVIDENCE,
        terminal_bench_db_wal_baseline_path=DEFAULT_TB_DB_WAL_BASELINE,
        terminal_bench_db_wal_lta_path=DEFAULT_TB_DB_WAL_LTA,
        terminal_bench_db_wal_evidence_path=DEFAULT_TB_DB_WAL_EVIDENCE,
        skillflow_baseline_path=DEFAULT_SKILLFLOW_BASELINE,
        skillflow_lta_path=DEFAULT_SKILLFLOW_LTA,
        skillflow_evidence_path=DEFAULT_SKILLFLOW_EVIDENCE,
    )
    print(args.output)
    print(
        "tau2_f_to_p={f_to_p} tb_f_to_p={tb_f_to_p} skillflow_flip={skillflow_flip}".format(
            f_to_p=report["source"]["tau2"]["f_to_p"],
            tb_f_to_p=report["transfer_checks"]["terminal_bench_2_1"]["f_to_p"],
            skillflow_flip=report["transfer_checks"]["skillflow"]["reward_flip"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

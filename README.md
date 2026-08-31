# License_code

Clean open-source code for **License-to-Act: Recursive Authority Compilation for State-Changing Agents**.

This repository contains the prototype authority layer, benchmark adapters, scripts, and tests. Large experiment artifacts are intentionally kept outside this code repository.

## Contents

- `license_to_act/`: core `ActionLicense` evaluator, examples, replay/materialization utilities, and Harbor agents.
- `tests/`: focused pytest coverage for the authority language and benchmark slices.
- `scripts/`: local replay and report-generation entry points.
- `configs/`: Harbor configs for official benchmark probes.
- `prompts/`: prompt-only baseline/control prompts.

## Quick Check

```bash
python -m pytest tests/license_to_act -q
```

Current local check:

```text
42 passed
```

## Official Harbor Anchors

```bash
env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/tb21_lta_sqlite_truncate_recovery_official.yaml \
  --job-name stage2-tb21-lta-sqlite-truncate-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/skillflow_lta_travel_claim_materializer_official.yaml \
  --job-name stage2-skillflow-lta-travel-claim-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

The sqlite-truncate anchor writes `/app/recover.json` from binary payload evidence in `/app/trunc.db`.
The travel-claim anchor writes `/app/workspace/travel_claims.xlsx` from OCR evidence and `dataset/claim_roster.csv`, then the SkillFlow official verifier scores the workbook.

`configs/tb21_terminus_qwen_sqlite_db_truncate.json` is the matched Qwen/Terminus baseline config for the SQLite task. The first successful local run scored reward 1.0 but also recorded an `AgentTimeoutError`, so it is kept as a mixed baseline artifact rather than a clean reliability anchor.

## Long-Context Faithful Baselines

The Stage-2 paper also includes matched open-model baselines using the newly available `Qwen3.8-27B-long32k` endpoint:

```bash
env PYTHONPATH=/data/zhiqi/License/License_code OPENAI_API_KEY=dummy harbor run \
  -c configs/tb21_miniswe_qwen_long32k_license_anchors.json \
  --job-name stage2-tb21-miniswe-qwen-long32k-license-anchors-smoke \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 1 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code OPENAI_API_KEY=dummy harbor run \
  -c configs/skillflow_miniswe_qwen_long32k_license_anchors.json \
  --job-name stage2-skillflow-miniswe-qwen-long32k-license-anchors-smoke \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 1 --n-concurrent 1 -y
```

Current artifacts record 0/3 Terminal-Bench passes and 0/2 SkillFlow passes with zero runtime exceptions. These are faithful baselines, not ablations; they test whether a stronger long-context task agent solves the same authority and obligation boundary without GovKernel.

## Paper Result Exports

```bash
python scripts/build_lta_amendment_transfer_report.py
python scripts/export_paper_results.py
python scripts/mine_tau2_authority.py
python scripts/export_stage2_results.py
```

The export scripts read large benchmark artifacts from `/data/zhiqi/License/artifacts`
and write paper-facing CSVs into `/data/zhiqi/License/License_paper/data`.

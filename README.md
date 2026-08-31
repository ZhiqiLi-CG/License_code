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
38 passed
```

## Official Harbor Anchors

```bash
env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/skillflow_lta_travel_claim_materializer_official.yaml \
  --job-name stage2-skillflow-lta-travel-claim-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

The travel-claim anchor writes `/app/workspace/travel_claims.xlsx` from OCR evidence and `dataset/claim_roster.csv`, then the SkillFlow official verifier scores the workbook.

## Paper Result Exports

```bash
python scripts/build_lta_amendment_transfer_report.py
python scripts/export_paper_results.py
python scripts/mine_tau2_authority.py
python scripts/export_stage2_results.py
```

The export scripts read large benchmark artifacts from `/data/zhiqi/License/artifacts`
and write paper-facing CSVs into `/data/zhiqi/License/License_paper/data`.

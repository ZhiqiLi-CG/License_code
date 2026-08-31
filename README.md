# License_code

Clean open-source code for **Stateful Agents Need Transactions: Separating Reasoning from Durable Effects**.

This repository contains the StateTx prototype: State Contract primitives, Commit Controller adapters, benchmark scripts, and tests. Large experiment artifacts are intentionally kept outside this code repository.

## Contents

- `license_to_act/`: core transaction evaluator, State Contract examples, replay/materialization utilities, and Harbor agents.
- `tests/`: focused pytest coverage for the commit protocol and benchmark slices.
- `scripts/`: local replay and report-generation entry points.
- `configs/`: Harbor configs for official benchmark probes.
- `prompts/`: prompt-only baseline/control prompts.

## Quick Check

```bash
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/license_to_act
```

Current local check:

```text
2026-08-31: 90 passed.
```

## Official Harbor Anchors

Harbor configs expect benchmark mirrors under `/data/zhiqi/License/datasets/`
so paper reproduction does not depend on another project workspace.

```bash
env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/tb21_lta_sqlite_truncate_recovery_official.yaml \
  --job-name stage2-tb21-statetx-sqlite-truncate-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/tb21_lta_log_summary_materializer_official.yaml \
  --job-name stage3-tb21-lta-log-summary-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/skillflow_lta_travel_claim_materializer_official.yaml \
  --job-name stage2-skillflow-statetx-travel-claim-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code:/data/zhiqi/License/datasets/SkillFlow harbor run \
  -c configs/skillflow_lta_qwen_invoice_govkernel_official.yaml \
  --job-name stage3-skillflow-qwen-govkernel-invoice-k5-real3-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code:/data/zhiqi/License/datasets/SkillFlow harbor run \
  -c configs/skillflow_lta_qwen_travel_claim_govkernel_official.yaml \
  --job-name stage3-skillflow-qwen-govkernel-travel-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

The sqlite-truncate anchor writes `/app/recover.json` from binary payload evidence in `/app/trunc.db`.
The log-summary anchor writes `/app/summary.csv` from bracketed severity tokens and filename dates in `/app/logs`.
The travel-claim anchor writes `/app/workspace/travel_claims.xlsx` from OCR evidence and `dataset/claim_roster.csv`, then the SkillFlow official verifier scores the workbook.
The two Stage-3 Qwen commands keep `Qwen3.8-27B-long32k` inside the official SkillFlow trial while the Commit Controller owns the final workbook transaction; the current artifacts score 10/10 across invoice and travel-claim OCR anchors with zero exceptions.

`configs/tb21_terminus_qwen_sqlite_db_truncate.json` is the matched Qwen/Terminus baseline config for the SQLite task. The first successful local run scored reward 1.0 but also recorded an `AgentTimeoutError`, so it is kept as a mixed baseline artifact rather than a clean reliability anchor.

## Long-Context Faithful Baselines

The paper includes matched open-model baselines using the newly available `Qwen3.8-27B-long32k` endpoint. These are the faithful baseline commands used by the current result tables:

```bash
env PYTHONPATH=/data/zhiqi/License/License_code OPENAI_API_KEY=dummy harbor run \
  -c configs/tb21_miniswe_qwen_long32k_license_anchors.json \
  --job-name stage3-tb21-miniswe-qwen-long32k-anchors-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code:/data/zhiqi/License/datasets/SkillFlow OPENAI_API_KEY=dummy harbor run \
  -c configs/skillflow_miniswe_qwen_long32k_license_anchors.json \
  --job-name stage3-skillflow-miniswe-qwen-long32k-ocr-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

Current artifacts record 3/15 Terminal-Bench passes and 1/10 SkillFlow OCR passes, or 4/25 across the current matched faithful-baseline pool. The Terminal-Bench K=15 job has one `NonZeroAgentExitCodeError`; the SkillFlow K=10 job has zero runtime exceptions. These are faithful baselines, not ablations; they test whether a stronger long-context task agent solves the same commit boundary without the Commit Controller.

## Paper Result Exports

```bash
python scripts/build_lta_amendment_transfer_report.py
python scripts/export_paper_results.py
python scripts/mine_tau2_commit.py
python scripts/export_stage2_results.py
python scripts/export_story_claims.py
python scripts/export_evidence_portfolio.py
python scripts/export_comparison_manifest.py
python scripts/export_headline_result_panel.py
python scripts/export_submission_experiment_blueprint.py
python scripts/export_contract_refinement_lineage.py
python scripts/export_mechanism_ablation_panel.py
python scripts/export_model_in_loop_bridge.py
python scripts/export_commit_pair_metrics.py
python scripts/export_submission_scale_plan.py
python scripts/export_real_evidence_audit.py
python scripts/export_state_contract_examples.py
python scripts/export_story_gate.py
```

The export scripts read large benchmark artifacts from `/data/zhiqi/License/artifacts`
and write paper-facing CSVs into `/data/zhiqi/License/License_paper/data`.
`export_story_claims.py`, `export_evidence_portfolio.py`,
`export_comparison_manifest.py`, `export_headline_result_panel.py`,
`export_submission_experiment_blueprint.py`, `export_contract_refinement_lineage.py`,
`export_mechanism_ablation_panel.py`, `export_model_in_loop_bridge.py`,
`export_commit_pair_metrics.py`, `export_submission_scale_plan.py`,
`export_real_evidence_audit.py`, and `export_story_gate.py` also write generated LaTeX number files under
`License_paper/sections`, which the paper imports for headline result,
evidence-portfolio, comparison-manifest, headline-panel, experiment-blueprint,
contract-lineage, mechanism-ablation, model-in-loop bridge, submission-scale,
commit-pair metrics, real-evidence audit, and paper-code consistency numbers.
`export_state_contract_examples.py` writes the paper-facing State Contract JSON examples used in the appendix.

## Paper-Code Consistency

Before pushing paper-facing changes:

1. Run the full `tests/license_to_act` suite.
2. Regenerate stage-1, stage-2, story-claim, evidence-portfolio, comparison-manifest, headline-panel, experiment-blueprint, contract-lineage, mechanism-ablation, model-in-loop bridge, commit-pair, submission-scale, real-evidence audit, State Contract examples, and paper-code consistency exports.
3. Regenerate paper figures from `License_paper/scripts/generate_figures.py`.
4. Compile the paper.
5. Scan touched files for placeholders.

Faithful baselines and StateTx ablations are different evidence categories. Baseline
configs should reproduce the external agent condition as cleanly as possible;
ablations isolate parts of our transaction mechanism and are allowed to be shaped
around the paper mechanism.

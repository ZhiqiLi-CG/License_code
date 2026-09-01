# License_code

Clean open-source code for **Beyond Better Reasoning: Recursive Self-Improvement at the Action Boundary**.

This repository contains the action-boundary prototype: boundary-rule primitives, controller adapters, benchmark scripts, and tests. Large experiment artifacts are intentionally kept outside this code repository.

## Contents

- `license_to_act/`: core boundary evaluator, boundary-rule examples, replay/finalization utilities, and Harbor agents.
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
2026-08-31: 114 passed.
```

## Official Harbor Anchors

Harbor configs expect benchmark mirrors under `/data/zhiqi/License/datasets/`
so paper reproduction does not depend on another project workspace.

```bash
env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/tb21_lta_sqlite_truncate_recovery_official.yaml \
  --job-name stage2-tb21-action-boundary-sqlite-truncate-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/tb21_lta_log_summary_materializer_official.yaml \
  --job-name stage3-tb21-lta-log-summary-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code harbor run \
  -c configs/skillflow_lta_travel_claim_materializer_official.yaml \
  --job-name stage2-skillflow-action-boundary-travel-claim-k5-py \
  --jobs-dir /data/zhiqi/License/artifacts/stage2/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code:/data/zhiqi/License/datasets/SkillFlow harbor run \
  -c configs/skillflow_action_boundary_qwen_invoice_official.yaml \
  --job-name stage3-skillflow-qwen-boundary-invoice-k5-real3-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code:/data/zhiqi/License/datasets/SkillFlow harbor run \
  -c configs/skillflow_action_boundary_qwen_travel_claim_official.yaml \
  --job-name stage3-skillflow-qwen-boundary-travel-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y

env PYTHONPATH=/data/zhiqi/License/License_code MSWEA_API_KEY=dummy OPENAI_API_KEY=dummy OPENAI_BASE_URL=http://172.17.0.1:18010/v1 harbor run \
  -c configs/tb21_action_boundary_qwen_log_summary_official.yaml \
  --job-name stage3-tb21-miniswe-boundary-log-summary-k5-real3-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

The sqlite-truncate anchor writes `/app/recover.json` from binary payload evidence in `/app/trunc.db`.
The log-summary anchor writes `/app/summary.csv` from bracketed severity tokens and filename dates in `/app/logs`.
The travel-claim anchor writes `/app/workspace/travel_claims.xlsx` from OCR evidence and `dataset/claim_roster.csv`, then the SkillFlow official verifier scores the workbook.
The three Stage-3 Qwen+boundary commands keep `Qwen3.8-27B-long32k` inside the official trial while the action boundary owns finalization; the current artifacts score 15/15 across Terminal-Bench log-summary, invoice, and travel-claim anchors with zero exceptions.

`configs/tb21_terminus_qwen_sqlite_db_truncate.json` is the matched Qwen/Terminus baseline config for the SQLite task. The first successful local run scored reward 1.0 but also recorded an `AgentTimeoutError`, so it is kept as a mixed baseline artifact rather than a clean reliability anchor.

## tau2 Matched Boundary Blocks

The current live matched tau2 fixtures use the same actor, same scripted user,
and same task budget in both conditions; the changed component is the action
boundary. The airline block tests unready writes. The retail block tests the
opposite failure: complete evidence exists, but the ordinary actor never turns it
into the required exchange.

```bash
/data/zhiqi/License/datasets/tau2-bench/.venv/bin/python scripts/run_tau2_action_boundary_live.py \
  --domain airline \
  --task-ids 48 \
  --user-mode scripted \
  --num-trials 20 \
  --seed 312 \
  --max-steps 20 \
  --timeout 180 \
  --llm-agent openai/Mistral-Small-3.2-24B-Instruct-2506 \
  --llm-user openai/Mistral-Small-3.2-24B-Instruct-2506 \
  --agent-max-tokens 256 \
  --user-max-tokens 128 \
  --api-base http://127.0.0.1:8001/v1 \
  --output /data/zhiqi/License/artifacts/experiments/tau2_action_boundary_matched_airline_task48_mistral_scripted_k20b_20260831.json
```

```bash
/data/zhiqi/License/datasets/tau2-bench/.venv/bin/python scripts/run_tau2_action_boundary_live.py \
  --domain retail \
  --task-ids 0 \
  --user-mode scripted \
  --num-trials 5 \
  --seed 950 \
  --max-steps 45 \
  --timeout 360 \
  --llm-agent openai/Qwen3.8-27B-long32k \
  --llm-user openai/Qwen3.8-27B-long32k \
  --agent-max-tokens 512 \
  --user-max-tokens 128 \
  --api-base http://127.0.0.1:8021/v1 \
  --output /data/zhiqi/License/artifacts/experiments/tau2_action_boundary_matched_retail_task0_qwen32k_completion_k5_maxtok512_20260901.json
```

The compact tracked fixture in `data/tau2_matched_boundary/` regenerates the
paper table: across 25 matched seeds and two tau2 domains, the baseline has mean
reward 0.0 and the action boundary has mean reward 1.0. The airline block has
20 read-correct/write-wrong cancellation runs and 26 boundary vetoes. The retail
block has 0 baseline exchange calls, 5 trace-derived boundary exchange calls,
and zero regressions.

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

env PYTHONPATH=/data/zhiqi/License/License_code OPENAI_API_KEY=dummy harbor run \
  -c configs/tb21_miniswe_qwen_long32k_log_summary.json \
  --job-name stage3-tb21-miniswe-qwen-long32k-log-summary-k5-real-20260831 \
  --jobs-dir /data/zhiqi/License/artifacts/stage3/harbor \
  --n-attempts 5 --n-concurrent 1 -y
```

Current artifacts record 7/20 Terminal-Bench passes and 1/10 SkillFlow OCR passes, or 8/30 across the current matched faithful-baseline pool. The Terminal-Bench baseline includes one `NonZeroAgentExitCodeError`; the SkillFlow K=10 job has zero runtime exceptions. These are faithful baselines, not ablations; they test whether a stronger long-context task agent solves the same action boundary without the boundary controller.

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
python scripts/export_proposal_effect_decomposition.py
python scripts/export_boundary_patch_meta_agent.py
python scripts/export_contract_refinement_lineage.py
python scripts/export_mechanism_ablation_panel.py
python scripts/export_model_in_loop_bridge.py
python scripts/export_tau2_matched_boundary.py
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
`export_submission_experiment_blueprint.py`, `export_proposal_effect_decomposition.py`,
`export_boundary_patch_meta_agent.py`,
`export_contract_refinement_lineage.py`,
`export_mechanism_ablation_panel.py`, `export_model_in_loop_bridge.py`,
`export_tau2_matched_boundary.py`, `export_commit_pair_metrics.py`,
`export_submission_scale_plan.py`,
`export_real_evidence_audit.py`, and `export_story_gate.py` also write generated LaTeX number files under
`License_paper/sections`. The paper imports those files for result counts,
baseline and ablation separation, full-study targets, boundary updates,
proposal/effect decomposition, meta-agent patch generation, model-in-loop comparisons, matched tau2 evidence, commit-pair metrics,
real-evidence auditing, and paper-code consistency numbers.
`export_state_contract_examples.py` writes the paper-facing boundary-rule JSON examples used in the appendix.
`export_boundary_patch_meta_agent.py` defaults to the tracked frozen-proposer
fixture under `data/boundary_patch_meta_agent/`; `run_boundary_patch_meta_agent.py`
is only needed when re-querying a local OpenAI-compatible model endpoint.

## Paper-Code Consistency

Before pushing paper-facing changes:

1. Run the full `tests/license_to_act` suite.
2. Regenerate stage-1, stage-2, claim, evidence, comparison, main-result, full-study-plan, proposal/effect, meta-agent patch, boundary-update, mechanism-ablation, model-in-loop, matched-tau2, commit-pair, real-evidence audit, boundary-rule example, and paper-code consistency exports.
3. Regenerate paper figures from `License_paper/scripts/generate_figures.py`.
4. Compile the paper.
5. Scan touched files for placeholders.

Faithful baselines and action-boundary ablations are different evidence categories. Baseline
configs should reproduce the external agent condition as cleanly as possible;
ablations isolate parts of our boundary mechanism and are allowed to be shaped
around the paper mechanism.

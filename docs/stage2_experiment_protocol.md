# Stage-2 Experiment Protocol

Date: 2026-08-30

This document freezes the second-stage experimental spine for License-to-Act before expanding the result matrix. The goal is not to make a cautious audit paper. The goal is to support one bold story with enough real benchmark evidence that the story feels inevitable:

```text
Self-improving agents need an executable institution. User intent, task phrasing,
model confidence, and observed evidence can propose an action, but a state-changing
commit needs an explicit license.
```

## Core Claim

License-to-Act shifts recursive self-improvement from editing advice to editing the authority compiler that decides when a proposal may become a state transition. The persistent object is an Action License, not a reflection:

```text
actor, operation, state region, required evidence, side-effect bounds,
positive obligation, expiry/inheritance, recovery protocol
```

The narrative must stay unified across the required benchmark families:

- tau2-Bench: dialogue agents confuse user intent with business-record authorization.
- Terminal-Bench 2.1: terminal agents confuse a local task goal with authority to mutate collateral repository, database, process, or artifact state.
- SkillFlow: workflow agents confuse extraction evidence with the obligation and authority to materialize verifier-visible artifacts.

## Frozen Baseline Contract

Faithful baselines are not ablations. They must use the same task harness, official verifiers, comparable model budgets, and no hidden access to LTA-specific executors.

Baseline ladder:

1. Vanilla actor on official harness.
2. Prompt-only commit protocol, where the model receives the LTA language but no executable GovKernel.
3. Reflection/history or Recuris-style memory evolution, implemented as faithfully as local infrastructure permits.
4. Fixed license ledger without recursive amendment.
5. Full License-to-Act with GovKernel decisions and amendment transfer.

Ablations are our mechanism probes and may be intentionally narrower:

- remove side-effect bounds;
- remove source-state authorization;
- remove positive obligations;
- remove recovery protocol;
- allow proposal evidence to satisfy commit evidence.

## Data Split

Source/amendment split:

- tau2 airline cancellation tasks that motivated the first amendment, including task 1 and task 48.
- The amendment is: proposal evidence cannot license a commit without independent policy/source-state authorization.

Control split:

- tau2 legal cancellation/non-regression cases such as airline task 19.
- Terminal-Bench tasks where scoped destructive action is valid, such as `git-leak-recovery`.
- SkillFlow families where vanilla agents already pass, such as Cross-Format Data Reconciliation and Document Fraud Detection.

Held-out split:

- tau2: at least one non-airline domain after the license schema is frozen, preferring retail or telecom.
- Terminal-Bench 2.1: a stratified slice covering repo mutation, database recovery, artifact production, process state, and data/schema authority.
- SkillFlow: OCR/Data Extraction plus at least two additional families with workbook/schema/materialization pressure.

Gemma-4-31B-it remains held out until licenses, task slices, and parser decisions are frozen.

## Model Plan

Main open-model actor:

- Qwen3.8-27B via `http://127.0.0.1:8000/v1`.

Second open-model actor:

- Mistral-Small-3.2-24B via `http://127.0.0.1:8001/v1`.

Held-out actor:

- Gemma-4-31B-it via `http://127.0.0.1:8002/v1`.

Strong-agent baselines:

- Codex CLI and Claude Code for Terminal-Bench and selected SkillFlow tasks where protocol/harness failures would make small local wrappers look artificially weak.

Resource request if available:

- >=32k context Qwen-compatible endpoint for faithful Qwen Code, Recuris-style long-trace baselines, and larger SkillFlow prompts.
- 32B-class VLM on GPUs 6/7 after the queue allows it; visual extraction itself is not the contribution, but stronger VLMs make the OCR evidence source paper-grade.
- GPU scheduling follows `/data/zhiqi/project/排队.md`: GPU 0/1/2/3 are public services and must not be touched; GPU 4/5/6/7 are the requestable experiment pool. If License needs a long-context or VLM slot, add or update a queue row and request idle owners to drain rather than silently competing for memory. If License itself is holding GPU 4/5/6/7 idle and another project requests them, release the service or update the queue heartbeat with a concrete active run.

## Stage-2 Experiment Batches

Batch A: Reproducibility K-5 anchors.

- Run official Harbor K=5 repeats for `sanitize-git-repo`, `db-wal-recovery`, `sqlite-db-truncate`, SkillFlow invoice materialization, and SkillFlow travel-claim OCR merge.
- Purpose: turn single official wins into reliability bars.

Batch B: tau2 authority mining.

- Scan all local tau2 result files.
- Separate infrastructure failures from agent decisions.
- Count cancel commits where LTA would veto, where reservation reads were already matched, and where official reward or DB reward failed.
- Purpose: convert the tau2 story from three examples into a distributional diagnosis.

Batch C: held-out task expansion.

- Add at least one non-airline tau2 write family.
- Add 3-5 Terminal-Bench tasks beyond the current recovery/sanitization anchors, selected for state-region diversity.
- Add 2-3 SkillFlow families beyond the current OCR workbook anchors, including one ceiling/control family.

Batch D: ablations and transfer.

- Run prompt-only, fixed-ledger, and selected ablations only after the task split is frozen.
- Report ablations as mechanism evidence, not as faithful competing systems.

## Paper Evidence Policy

The main paper should contain positive, story-serving results:

- failure-to-pass changes under official verifiers;
- non-regression on licensed positive controls;
- reduction in false authority, overbroad side effects, missing commit obligations, and evidence-consuming reads.

Infrastructure errors, weak context-window failures, and noisy failed probes may be stored in artifacts but should only enter the paper when they clarify resource needs or boundary conditions.

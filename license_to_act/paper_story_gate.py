from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .commit_pair_metrics import build_commit_pair_member_rows, compute_commit_pair_metrics
from .evidence_portfolio import build_evidence_portfolio
from .mechanism_ablation_panel import build_mechanism_ablation_panel
from .model_in_loop_bridge import build_model_in_loop_bridge
from .boundary_patch_meta_agent import build_meta_agent_patch_report, default_response_path
from .proposal_effect_decomposition import build_proposal_effect_decomposition
from .real_evidence_audit import build_real_evidence_audit
from .recursive_amendment_lineage import build_recursive_amendment_lineage
from .story_claims import build_story_claims
from .tau2_matched_boundary_export import build_tau2_matched_boundary_export


CHECK_FIELDS = ["check_id", "status", "criterion", "evidence"]


def build_story_gate_report(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    paper_dir = root / "License_paper"
    data_dir = paper_dir / "data"

    portfolio = build_evidence_portfolio(root)
    comparison_manifest = build_comparison_manifest(root)
    ablation_panel = build_mechanism_ablation_panel(root)
    model_loop_bridge = build_model_in_loop_bridge(root)
    real_evidence_audit = build_real_evidence_audit(root)
    commit_pair_metrics = compute_commit_pair_metrics(build_commit_pair_member_rows(root))
    recursive_lineage = build_recursive_amendment_lineage(root)
    meta_agent_patches = build_meta_agent_patch_report(
        root,
        response_path=default_response_path(root),
    )
    proposal_effect = build_proposal_effect_decomposition(root)
    claims = build_story_claims(root)
    tau2_matched = build_tau2_matched_boundary_export(root)
    stage2_rows = _read_csv(data_dir / "stage2_reliability.csv")
    portfolio_rows = portfolio["rows"]
    portfolio_summary = portfolio["summary"]
    comparison_summary = comparison_manifest["summary"]
    claim_metrics = claims["headline_metrics"]

    checks = [
        _portfolio_breadth_check(portfolio_summary),
        _clean_positive_mass_check(portfolio_summary),
        _faithful_baseline_check(portfolio_rows, stage2_rows),
        _comparison_manifest_check(comparison_summary),
        _mechanism_ablation_panel_check(ablation_panel["summary"]),
        _model_in_loop_bridge_check(model_loop_bridge),
        _real_evidence_audit_check(real_evidence_audit["summary"]),
        _commit_pair_metric_check(commit_pair_metrics["summary"]),
        _proposal_effect_decomposition_check(proposal_effect["summary"]),
        _tau2_matched_boundary_check(tau2_matched["summary"]),
        _workspace_only_check(portfolio_rows, claims["claims"].values(), stage2_rows),
        _generated_import_check(paper_dir / "main.tex"),
        _recursive_lineage_check(recursive_lineage["summary"]),
        _meta_agent_patch_check(meta_agent_patches["summary"]),
        _action_boundary_story_check(paper_dir),
        _public_surface_hygiene_check(root),
        _story_language_check(paper_dir),
        _main_text_style_check(paper_dir),
        _reproduction_chain_check(root),
        _code_paper_structure_check(root),
        _appendix_story_check(paper_dir / "sections" / "appendix.tex"),
        _appendix_scale_language_check(paper_dir / "sections" / "appendix.tex"),
    ]
    passed = sum(1 for check in checks if check["status"] == "pass")
    failed = len(checks) - passed

    return {
        "summary": {
            "total_checks": len(checks),
            "passed_checks": passed,
            "failed_checks": failed,
            "benchmark_count": portfolio_summary["benchmark_count"],
            "state_substrate_count": portfolio_summary["state_substrate_count"],
            "actor_backbone_count": portfolio_summary["actor_backbone_count"],
            "clean_positive_passes": portfolio_summary["clean_positive_passes"],
            "clean_positive_trials": portfolio_summary["clean_positive_trials"],
            "faithful_baseline_passes": portfolio_summary["faithful_baseline_passes"],
            "faithful_baseline_trials": portfolio_summary["faithful_baseline_trials"],
            "tau2_read_correct_write_wrong_proxy": claim_metrics["tau2_read_correct_write_wrong_proxy"],
            "mechanism_ablation_cut_passes": ablation_panel["summary"]["cut_passes"],
            "mechanism_ablation_cut_trials": ablation_panel["summary"]["cut_trials"],
            "model_in_loop_govkernel_passes": model_loop_bridge["summary"][
                "qwen_skillflow_govkernel_passes"
            ],
            "model_in_loop_govkernel_trials": model_loop_bridge["summary"][
                "qwen_skillflow_govkernel_trials"
            ],
            "real_evidence_harbor_rows": real_evidence_audit["summary"]["real_harbor_rows"],
            "real_evidence_main_positive_planned_rows": real_evidence_audit["summary"][
                "main_positive_planned_rows"
            ],
            "real_evidence_missing_artifacts": real_evidence_audit["summary"]["missing_artifact_rows"],
            "real_evidence_unparseable_artifacts": real_evidence_audit["summary"][
                "unparseable_artifact_rows"
            ],
            "commit_pair_accuracy": commit_pair_metrics["summary"]["commit_pair_accuracy"],
            "unauthorized_commit_rate": commit_pair_metrics["summary"]["unauthorized_commit_rate"],
            "authorized_commit_recall": commit_pair_metrics["summary"]["authorized_commit_recall"],
            "tau2_matched_pairs": tau2_matched["summary"]["complete_pairs"],
            "tau2_matched_reward_delta": tau2_matched["summary"]["reward_delta"],
            "meta_agent_candidates": meta_agent_patches["summary"]["meta_agent_candidates"],
            "meta_agent_accepted": meta_agent_patches["summary"]["accepted_candidates"],
            "meta_agent_source_f_to_p": meta_agent_patches["summary"]["source_failure_to_pass"],
            "proposal_effect_gap_observations": proposal_effect["summary"]["gap_observations"],
            "proposal_effect_boundary_source_successes": proposal_effect["summary"][
                "boundary_effect_successes_on_source_gap_rows"
            ],
        },
        "checks": checks,
    }


def write_story_gate_report(
    project_root: str | Path = Path("/data/zhiqi/License"),
    *,
    paper_data_dir: str | Path | None = None,
    paper_sections_dir: str | Path | None = None,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root)
    paper_data_dir = Path(paper_data_dir) if paper_data_dir is not None else root / "License_paper" / "data"
    paper_sections_dir = (
        Path(paper_sections_dir) if paper_sections_dir is not None else root / "License_paper" / "sections"
    )
    summary_path = (
        Path(summary_path)
        if summary_path is not None
        else root / "artifacts" / "paper_results" / "lta_story_gate_20260831.json"
    )

    report = build_story_gate_report(root)
    paper_data_dir.mkdir(parents=True, exist_ok=True)
    paper_sections_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    checks_csv = paper_data_dir / "story_gate_checks.csv"
    latex_numbers = paper_sections_dir / "generated_story_gate_numbers.tex"
    _write_checks_csv(checks_csv, report["checks"])
    latex_numbers.write_text(_latex_numbers(report["summary"]), encoding="utf-8")

    report["outputs"] = {
        "summary_json": str(summary_path),
        "checks_csv": str(checks_csv),
        "latex_numbers": str(latex_numbers),
    }
    summary_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _portfolio_breadth_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["benchmark_count"] >= 3
        and summary["state_substrate_count"] >= 3
        and summary["actor_backbone_count"] >= 4
    )
    return _check(
        "portfolio_breadth",
        ok,
        "The main result set spans multiple benchmark families, state substrates, and actor backbones.",
        (
            f"{summary['benchmark_count']} benchmark families; "
            f"{summary['state_substrate_count']} state substrates; "
            f"{summary['actor_backbone_count']} actor backbones."
        ),
    )


def _clean_positive_mass_check(summary: dict[str, Any]) -> dict[str, str]:
    passes = summary["clean_positive_passes"]
    trials = summary["clean_positive_trials"]
    ok = passes == trials and trials >= 25
    return _check(
        "clean_positive_mass",
        ok,
        "Clean official anchors should provide a positive result block, not a one-off anecdote.",
        f"{passes}/{trials} clean official passes.",
    )


def _faithful_baseline_check(
    portfolio_rows: list[dict[str, Any]], stage2_rows: list[dict[str, str]]
) -> dict[str, str]:
    external_rows = [row for row in portfolio_rows if row["comparison_kind"] == "faithful_baseline"]
    stage2_external = [row for row in stage2_rows if row["paper_use"] == "faithful_baseline"]
    has_named_counterpoint = any(row["paper_use"] == "main_counterpoint" for row in external_rows)
    stage2_roles_named = all("faithful" in row["role"].lower() for row in stage2_external)
    no_mechanism_cut_words = all(
        "ablation" not in str(row.get(field, "")).lower()
        for row in [*portfolio_rows, *stage2_rows]
        for field in ("paper_use", "comparison_kind", "role")
    )
    ok = (
        bool(external_rows)
        and bool(stage2_external)
        and has_named_counterpoint
        and stage2_roles_named
        and no_mechanism_cut_words
    )
    portfolio_ids = ", ".join(row["portfolio_id"] for row in external_rows)
    case_ids = ", ".join(row["case_id"] for row in stage2_external)
    return _check(
        "faithful_baseline_not_ablation",
        ok,
        "External-agent comparisons must be separated from internal mechanism cuts.",
        f"External-agent rows: {portfolio_ids}; stage2 cases: {case_ids}.",
    )


def _comparison_manifest_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["faithful_baseline_rows"] >= 1
        and summary["mechanism_ablation_rows"] >= 5
        and summary["completed_mechanism_ablation_rows"] >= 3
        and summary["baseline_ablation_overlap"] == 0
    )
    return _check(
        "comparison_manifest_separates_roles",
        ok,
        "The paper should keep faithful external-agent baselines distinct from mechanism cuts.",
        (
            f"{summary['faithful_baseline_rows']} faithful-baseline row; "
            f"{summary['mechanism_ablation_rows']} mechanism-ablation rows; "
            f"{summary['baseline_ablation_overlap']} baseline/ablation overlap."
        ),
    )


def _workspace_only_check(
    portfolio_rows: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    stage2_rows: list[dict[str, str]],
) -> dict[str, str]:
    refs: list[str] = []
    refs.extend(str(row["source_data"]) for row in portfolio_rows)
    refs.extend(str(ref) for claim in claims for ref in claim["source_artifacts"])
    refs.extend(row["result_path"] for row in stage2_rows)

    ok = True
    for ref in refs:
        if ref.startswith("/data/zhiqi/") and not ref.startswith("/data/zhiqi/License/"):
            ok = False
        if "RSI" in ref:
            ok = False
    return _check(
        "license_workspace_only",
        ok,
        "Paper-facing evidence sources must stay inside the License workspace or use relative paper data paths.",
        "All paper-facing source refs stay under the License workspace.",
    )


def _generated_import_check(main_path: Path) -> dict[str, str]:
    text = main_path.read_text(encoding="utf-8")
    required = [
        "\\input{sections/generated_story_numbers}",
        "\\input{sections/generated_portfolio_numbers}",
        "\\input{sections/generated_comparison_numbers}",
        "\\input{sections/generated_headline_panel_numbers}",
        "\\input{sections/generated_experiment_blueprint_numbers}",
        "\\input{sections/generated_proposal_effect_numbers}",
        "\\input{sections/generated_recursive_numbers}",
        "\\input{sections/generated_meta_agent_patch_numbers}",
        "\\input{sections/generated_ablation_numbers}",
        "\\input{sections/generated_model_loop_numbers}",
        "\\input{sections/generated_tau2_matched_boundary_numbers}",
        "\\input{sections/generated_commit_pair_numbers}",
        "\\input{sections/generated_scale_plan_numbers}",
        "\\input{sections/generated_real_evidence_numbers}",
        "\\input{sections/generated_story_gate_numbers}",
    ]
    ok = all(item in text for item in required)
    return _check(
        "paper_imports_generated_numbers",
        ok,
        "Headline paper numbers should be imported from generated files.",
        "main.tex imports generated result, comparison, run-plan, proposal/effect, contract-update, meta-agent patch, ablation, model-in-loop, matched tau2, commit-pair, real-evidence, and reproducibility numbers.",
    )


def _mechanism_ablation_panel_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["ablation_rows"] >= 5
        and summary["high_priority_rows"] >= 3
        and summary["baseline_overlap"] == 0
        and summary["cut_passes"] == 0
        and summary["full_passes"] == summary["full_trials"]
    )
    return _check(
        "mechanism_ablation_panel_has_requested_cuts",
        ok,
        "The paper should include completed internal mechanism cuts without relabeling baselines as ablations.",
        (
            f"{summary['ablation_rows']} mechanism cuts; {summary['high_priority_rows']} high-priority; "
            f"{summary['cut_passes']}/{summary['cut_trials']} cut passes versus "
            f"{summary['full_passes']}/{summary['full_trials']} full boundary passes."
        ),
    )


def _model_in_loop_bridge_check(bridge: dict[str, Any]) -> dict[str, str]:
    summary = bridge["summary"]
    rows = bridge["rows"]
    row_fields_present = all(
        row.get("actor_model")
        and row.get("controller_boundary")
        and row.get("official_verifier_result") in {"pass", "fail", "mixed", "error"}
        for row in rows
    )
    ok = (
        summary["model_in_loop_rows"] >= 4
        and summary["ordinary_agent_rows"] >= 1
        and summary["prompt_control_rows"] >= 1
        and summary["matched_agent_controller_rows"] >= 2
        and summary["faithful_baseline_rows"] >= 1
        and summary["qwen_invoice_govkernel_passes"] >= 4
        and summary["qwen_invoice_govkernel_trials"] >= 5
        and summary["qwen_terminal_log_govkernel_passes"] >= 5
        and summary["qwen_terminal_log_govkernel_trials"] >= 5
        and summary["qwen_all_govkernel_passes"] >= 15
        and summary["qwen_all_govkernel_trials"] >= 15
        and summary["qwen_skillflow_govkernel_passes"] >= 10
        and summary["qwen_skillflow_govkernel_trials"] >= 10
        and summary["qwen_skillflow_faithful_baseline_trials"] >= 10
        and summary["qwen_skillflow_faithful_baseline_passes"] < summary["qwen_skillflow_govkernel_passes"]
        and summary["materializer_rows_used_as_matched_agent"] == 0
        and row_fields_present
    )
    return _check(
        "model_in_loop_bridge_separates_runtime_executors",
        ok,
        "Model-in-loop evidence should be reported separately from task-specific executor reliability.",
        (
            f"{summary['ordinary_agent_rows']} ordinary, {summary['prompt_control_rows']} prompt-only, "
            f"{summary['matched_agent_controller_rows']} matched-controller, and "
            f"{summary['faithful_baseline_rows']} faithful-baseline rows carry actor, boundary, "
            f"and official-result fields. Qwen faithful OCR baseline: "
            f"{summary['qwen_skillflow_faithful_baseline_passes']}/"
            f"{summary['qwen_skillflow_faithful_baseline_trials']}; Qwen+controller: "
            f"{summary['qwen_all_govkernel_passes']}/"
            f"{summary['qwen_all_govkernel_trials']} across log-summary and SkillFlow OCR tasks; "
            f"executor-as-agent rows: "
            f"{summary['materializer_rows_used_as_matched_agent']}."
        ),
    )


def _real_evidence_audit_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["real_harbor_rows"] >= 8
        and summary["derived_real_rows"] >= 1
        and summary["planned_rows"] >= 1
        and summary["main_positive_planned_rows"] == 0
        and summary["missing_artifact_rows"] == 0
        and summary["unparseable_artifact_rows"] == 0
    )
    return _check(
        "real_evidence_audit_blocks_planned_main_results",
        ok,
        "Main positive results must be backed by parseable real artifacts or derived real-artifact analyses, not planned matrices.",
        (
            f"{summary['real_harbor_rows']} parseable Harbor rows; "
            f"{summary['derived_real_rows']} derived real-artifact rows; "
            f"{summary['planned_rows']} planned rows isolated; "
            f"planned main positives: {summary['main_positive_planned_rows']}; "
            f"missing artifacts: {summary['missing_artifact_rows']}; "
            f"unparseable artifacts: {summary['unparseable_artifact_rows']}."
        ),
    )


def _commit_pair_metric_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["pair_count"] >= 4
        and summary["ready_opportunities"] >= 4
        and summary["premature_opportunities"] >= 4
        and summary["commit_pair_accuracy"] >= 1.0
        and summary["unauthorized_commit_rate"] == 0.0
        and summary["authorized_commit_recall"] >= 1.0
    )
    return _check(
        "commit_pair_metrics_support_bidirectional_correctness",
        ok,
        "The main evidence should report a bidirectional commit metric after task reward.",
        (
            f"{summary['pair_count']} commit-pair groups; accuracy "
            f"{summary['commit_pair_accuracy']:.3f}; unauthorized commit rate "
            f"{summary['unauthorized_commit_rate']:.3f}; authorized commit recall "
            f"{summary['authorized_commit_recall']:.3f}."
        ),
    )


def _tau2_matched_boundary_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["complete_pairs"] >= 1
        and summary["baseline_mean_reward"] == 0.0
        and summary["boundary_mean_reward"] == 1.0
        and summary["baseline_read_correct_write_wrong"] >= 1
        and summary["boundary_read_correct_write_wrong"] == 0
        and summary["boundary_vetoes"] >= 1
        and summary["boundary_regressions"] == 0
    )
    return _check(
        "tau2_matched_boundary_pair_present",
        ok,
        "The paper should include real matched tau2 actor pairs, not only retrospective mining.",
        (
            f"{summary['complete_pairs']} matched pairs; reward "
            f"{summary['baseline_mean_reward']:.1f}->{summary['boundary_mean_reward']:.1f}; "
            f"read-correct/write-wrong "
            f"{summary['baseline_read_correct_write_wrong']}->{summary['boundary_read_correct_write_wrong']}; "
            f"boundary vetoes {summary['boundary_vetoes']}; regressions {summary['boundary_regressions']}."
        ),
    )


def _proposal_effect_decomposition_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["rows"] >= 6
        and summary["benchmark_count"] >= 3
        and summary["planned_rows"] == 0
        and summary["gap_observations"] >= 25
        and summary["baseline_effect_successes_on_gap_rows"] == 0
        and summary["boundary_effect_successes_on_source_gap_rows"] >= 5
    )
    return _check(
        "proposal_effect_decomposition_has_real_gap_rows",
        ok,
        "RQ1 should be backed by real proposal/effect rows, not planned matrices.",
        (
            f"{summary['gap_observations']} proposal-to-effect gap observations across "
            f"{summary['benchmark_count']} benchmark families; planned rows "
            f"{summary['planned_rows']}; boundary source closures "
            f"{summary['boundary_effect_successes_on_source_gap_rows']}."
        ),
    )


def _recursive_lineage_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["candidate_amendments"] >= 4
        and summary["accepted_amendments"] >= 4
        and summary["compiler_generations"] >= 3
        and summary["source_benchmark_families"] >= 3
        and summary["pass_to_failure_regressions"] == 0
    )
    return _check(
        "boundary_updates_have_generation_record",
        ok,
        "The boundary-improvement claim should have generated executable updates, not only prose.",
        (
            f"{summary['accepted_amendments']}/{summary['candidate_amendments']} boundary updates accepted "
            f"over {summary['compiler_generations']} boundary generations with "
            f"{summary['pass_to_failure_regressions']} pass-to-failure regressions."
        ),
    )


def _meta_agent_patch_check(summary: dict[str, Any]) -> dict[str, str]:
    ok = (
        summary["meta_agent_candidates"] >= 5
        and summary["accepted_candidates"] >= 5
        and summary["accepted_benchmark_families"] >= 3
        and summary["source_failure_to_pass"] >= 5
        and summary["pass_to_failure_regressions"] == 0
    )
    return _check(
        "meta_agent_boundary_patch_generation",
        ok,
        "The boundary-update claim should include frozen-proposer candidates, not only deterministic signature rules.",
        (
            f"{summary['accepted_candidates']}/{summary['meta_agent_candidates']} frozen-proposer patches accepted; "
            f"{summary['accepted_benchmark_families']} benchmark families; "
            f"{summary['source_failure_to_pass']} source repairs; "
            f"{summary['pass_to_failure_regressions']} pass-to-failure regressions."
        ),
    )


def _story_language_check(paper_dir: Path) -> dict[str, str]:
    combined = "\n".join(
        (paper_dir / relative).read_text(encoding="utf-8")
        for relative in ["main.tex", "sections/01_introduction.tex", "sections/04_experiments.tex"]
    )
    anchors = [
        "recursive self-improvement",
        "action boundary",
        "proposal-to-effect gap",
        "frozen reasoner",
        "proposed effects",
        "State Contract",
        "commit controller",
    ]
    missing = [anchor for anchor in anchors if anchor not in combined]
    return _check(
        "story_language_anchors",
        not missing,
        "The main paper should expose the idea before defensive details.",
        (
            "Core action-boundary RSI anchors appear in abstract, introduction, and experiment setup."
            if not missing
            else f"missing={missing}"
        ),
    )


def _action_boundary_story_check(paper_dir: Path) -> dict[str, str]:
    main = (paper_dir / "main.tex").read_text(encoding="utf-8")
    intro = (paper_dir / "sections" / "01_introduction.tex").read_text(encoding="utf-8")
    formulation = (paper_dir / "sections" / "02_formulation.tex").read_text(encoding="utf-8")
    method = (paper_dir / "sections" / "03_method.tex").read_text(encoding="utf-8")

    front_matter = main.split("\\input{sections/01_introduction}", maxsplit=1)[0]
    opening = "\n".join([front_matter, intro, formulation, method])
    required = [
        "Beyond Better Reasoning",
        "recursive self-improvement",
        "action boundary",
        "proposal-to-effect gap",
        "frozen reasoner",
        "external effects",
        "proposed effects",
        "State Contract",
        "commit controller",
        "ready",
        "write scope",
        "preserve",
        "done",
        "CONTINUE",
        "REVISE",
        "COMMIT",
    ]
    retired_front_matter = [
        "institutions decide",
        "agency gap",
        "Action License",
        "authority compiler",
        "positive obligation",
        "institutional channel",
        "institution of action",
        "Candidate Change",
    ]
    missing = [phrase for phrase in required if phrase not in opening]
    retired_hits = [phrase for phrase in retired_front_matter if phrase in front_matter]
    section_ok = (
        "\\section{Action Boundary RSI}" in formulation
        and "\\section{Improving the Action Boundary}" in method
    )
    ok = not missing and not retired_hits and section_ok
    evidence = (
        "Action boundary, proposal-to-effect gap, frozen reasoner, and State Contract implementation lead the front matter."
        if ok
        else f"missing={missing}; retired_front_matter={retired_hits}; section_ok={section_ok}"
    )
    return _check(
        "action_boundary_story_framing",
        ok,
        "The paper should lead with action-boundary RSI rather than runtime internals or legal terminology.",
        evidence,
    )


def _public_surface_hygiene_check(root: Path) -> dict[str, str]:
    retired_path_fragments = [
        "tau2_authority",
        "license_examples",
        "recursive_amendment",
        "story-first-stage2-lta",
    ]
    retired_text_phrases = [
        *retired_path_fragments,
        "License-to-Act",
        "Action License",
        "GovKernel",
        "OBLIGE",
        "authority compiler",
        "positive obligation",
        "Agency Gap",
    ]
    tracked_paths = _tracked_public_paths(root)
    existing_paths = [path for path in tracked_paths if (root / path).exists()]
    path_hits = [
        path for path in existing_paths if any(fragment in path for fragment in retired_path_fragments)
    ]
    text_hits: list[str] = []
    for path in existing_paths:
        if not path.endswith((".csv", ".json", ".md", ".tex")):
            continue
        full_path = root / path
        if not full_path.exists():
            continue
        try:
            text = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(phrase in text for phrase in retired_text_phrases):
            text_hits.append(path)

    ok = not path_hits and not text_hits
    evidence = (
        "Tracked root and paper public files use action-boundary naming."
        if ok
        else f"retired_path_hits={path_hits}; retired_text_hits={text_hits}"
    )
    return _check(
        "public_surface_uses_action_boundary_terms",
        ok,
        "Tracked paper data, figures, READMEs, and root plans should not expose retired legal/authority framing.",
        evidence,
    )


def _tracked_public_paths(root: Path) -> list[str]:
    paths: list[str] = []
    for repo, prefix in [
        (root, ""),
        (root / "License_paper", "License_paper/"),
    ]:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        paths.extend(f"{prefix}{line}" for line in result.stdout.splitlines() if line)
    return paths


def _main_text_style_check(paper_dir: Path) -> dict[str, str]:
    combined = "\n".join(
        (paper_dir / relative).read_text(encoding="utf-8")
        for relative in [
            "main.tex",
            "sections/01_introduction.tex",
            "sections/02_formulation.tex",
            "sections/03_method.tex",
            "sections/04_experiments.tex",
            "sections/05_results.tex",
            "sections/06_related_work.tex",
            "sections/07_discussion.tex",
        ]
    )
    blocked = [
        "story-first",
        "Story-first",
        "main spine",
        "Main spine",
        "go signal",
        "story gate",
        "Story gate",
        "story-gate",
        "Story-gate",
    ]
    hits = [phrase for phrase in blocked if phrase in combined]
    return _check(
        "main_text_avoids_meta_curation_language",
        not hits,
        "The main paper should use hypothesis/evaluation language rather than internal curation labels.",
        "Main text avoids internal curation wording.",
    )


def _reproduction_chain_check(root: Path) -> dict[str, str]:
    code_readme = (root / "License_code" / "README.md").read_text(encoding="utf-8")
    paper_readme = (root / "License_paper" / "README.md").read_text(encoding="utf-8")
    required = [
        "export_story_claims.py",
        "export_evidence_portfolio.py",
        "export_comparison_manifest.py",
        "export_headline_result_panel.py",
        "export_submission_experiment_blueprint.py",
        "export_proposal_effect_decomposition.py",
        "export_contract_refinement_lineage.py",
        "export_boundary_patch_meta_agent.py",
        "run_boundary_patch_meta_agent.py",
        "export_mechanism_ablation_panel.py",
        "export_model_in_loop_bridge.py",
        "export_tau2_matched_boundary.py",
        "export_commit_pair_metrics.py",
        "export_submission_scale_plan.py",
        "export_real_evidence_audit.py",
        "export_state_contract_examples.py",
        "export_story_gate.py",
        "scripts/generate_figures.py",
        "latexmk -pdf",
    ]
    combined = code_readme + "\n" + paper_readme
    ok = all(item in combined for item in required)
    return _check(
        "reproduction_chain_mentions_portfolio",
        ok,
        "Reproduction docs should include generated tables and the paper build path.",
        "README files mention result exports, comparison exports, full-study plan exports, proposal/effect exports, contract-update exports, meta-agent patch exports, ablation exports, model-in-loop exports, matched tau2 exports, commit-pair metrics, real-evidence audit, consistency export, figure generation, and LaTeX build.",
    )


def _code_paper_structure_check(root: Path) -> dict[str, str]:
    readme = (root / "README.md").read_text(encoding="utf-8")
    gitmodules = (root / ".gitmodules").read_text(encoding="utf-8")
    required_readme = [
        "License_code/",
        "code folder",
        "License_paper/",
        "paper folder",
        "regenerated from `License_code/` into `License_paper/`",
    ]
    required_modules = [
        "path = License_code",
        "path = License_paper",
        "ZhiqiLi-CG/License_code.git",
        "ZhiqiLi-CG/License_paper.git",
    ]
    ok = (
        all(item in readme for item in required_readme)
        and all(item in gitmodules for item in required_modules)
        and "intentionally empty" not in readme
    )
    return _check(
        "code_paper_submodules_declared",
        ok,
        "The root repository should explicitly expose the open-source code folder and paper folder.",
        "Root README and .gitmodules declare License_code and License_paper as separate pushed submodules.",
    )


def _appendix_story_check(appendix_path: Path) -> dict[str, str]:
    text = appendix_path.read_text(encoding="utf-8")
    anchors = [
        "Result set construction",
        "proposal-to-effect boundary",
        "Runs that only diagnose infrastructure or unrelated model behavior remain in the artifact record",
    ]
    missing = [anchor for anchor in anchors if anchor not in text]
    return _check(
        "appendix_serves_argument",
        not missing,
        "The appendix should support the action-boundary argument rather than archive weak exploratory logs.",
        "Appendix opens detailed evidence with result-set construction and inclusion criteria.",
    )


def _appendix_scale_language_check(appendix_path: Path) -> dict[str, str]:
    text = appendix_path.read_text(encoding="utf-8")
    defensive_phrases = [
        "Claims not yet supported",
        "not yet supported",
        "does not by itself prove",
    ]
    scale_anchors = [
        "Full-study targets",
        "Current positive results",
        "Scale evidence to add",
    ]
    blocked = [phrase for phrase in defensive_phrases if phrase in text]
    missing = [anchor for anchor in scale_anchors if anchor not in text]
    return _check(
        "appendix_uses_submission_scale_language",
        not blocked and not missing,
        "The appendix should frame remaining work as full-study evidence, not defensive unsupported-claim caveats.",
        "Appendix uses current-positive-result and full-study-target language without unsupported-claim headings.",
    )


def _check(check_id: str, passed: bool, criterion: str, evidence: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "status": "pass" if passed else "fail",
        "criterion": criterion,
        "evidence": evidence,
    }


def _write_checks_csv(path: Path, checks: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CHECK_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)


def _latex_numbers(summary: dict[str, Any]) -> str:
    commands = {
        "LTAStoryGateChecks": summary["total_checks"],
        "LTAStoryGatePassed": summary["passed_checks"],
        "LTAStoryGateFailed": summary["failed_checks"],
    }
    lines = [
        "% Auto-generated by License_code/license_to_act/paper_story_gate.py.",
        "% Regenerate with License_code/scripts/export_story_gate.py.",
    ]
    for name, value in commands.items():
        lines.append(f"\\newcommand{{\\{name}}}{{{value}}}")
    return "\n".join(lines) + "\n"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

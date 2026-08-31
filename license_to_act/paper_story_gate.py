from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .comparison_manifest import build_comparison_manifest
from .evidence_portfolio import build_evidence_portfolio
from .story_claims import build_story_claims


CHECK_FIELDS = ["check_id", "status", "criterion", "evidence"]


def build_story_gate_report(project_root: str | Path = Path("/data/zhiqi/License")) -> dict[str, Any]:
    root = Path(project_root)
    paper_dir = root / "License_paper"
    data_dir = paper_dir / "data"

    portfolio = build_evidence_portfolio(root)
    comparison_manifest = build_comparison_manifest(root)
    claims = build_story_claims(root)
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
        _workspace_only_check(portfolio_rows, claims["claims"].values(), stage2_rows),
        _generated_import_check(paper_dir / "main.tex"),
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
        "The main evidence spine spans multiple benchmark families, state substrates, and actor backbones.",
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
        "\\input{sections/generated_scale_plan_numbers}",
        "\\input{sections/generated_story_gate_numbers}",
    ]
    ok = all(item in text for item in required)
    return _check(
        "paper_imports_generated_numbers",
        ok,
        "Headline paper numbers should be imported from generated files.",
        "main.tex imports generated story, portfolio, comparison, headline panel, experiment blueprint, scale plan, and consistency numbers.",
    )


def _story_language_check(paper_dir: Path) -> dict[str, str]:
    combined = "\n".join(
        (paper_dir / relative).read_text(encoding="utf-8")
        for relative in ["main.tex", "sections/01_introduction.tex", "sections/04_experiments.tex"]
    )
    anchors = [
        "Intelligence proposes actions; institutions decide",
        "agency gap",
        "Action License",
        "proposal must earn authority",
        "positive obligation",
    ]
    missing = [anchor for anchor in anchors if anchor not in combined]
    return _check(
        "story_language_anchors",
        not missing,
        "The main paper should expose the idea before defensive details.",
        "Core story anchors appear in abstract, introduction, and experiment setup.",
    )


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
        "export_submission_scale_plan.py",
        "export_story_gate.py",
        "scripts/generate_figures.py",
        "latexmk -pdf",
    ]
    combined = code_readme + "\n" + paper_readme
    ok = all(item in combined for item in required)
    return _check(
        "reproduction_chain_mentions_portfolio",
        ok,
        "Reproduction docs should include the story and portfolio generation path.",
        "README files mention story export, portfolio export, comparison manifest export, headline panel export, experiment blueprint export, scale plan export, consistency export, figure generation, and LaTeX build.",
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
        "Portfolio construction",
        "proposal/evidence/authority/commit",
        "Exploratory runs that do not clarify the authority mechanism are kept out",
    ]
    missing = [anchor for anchor in anchors if anchor not in text]
    return _check(
        "appendix_serves_story",
        not missing,
        "The appendix should support the story rather than archive weak exploratory logs.",
        "Appendix opens detailed evidence with portfolio construction and inclusion criteria.",
    )


def _appendix_scale_language_check(appendix_path: Path) -> dict[str, str]:
    text = appendix_path.read_text(encoding="utf-8")
    defensive_phrases = [
        "Claims not yet supported",
        "not yet supported",
        "does not by itself prove",
    ]
    scale_anchors = [
        "Submission-scale targets",
        "Current positive spine",
        "Scale evidence to add",
    ]
    blocked = [phrase for phrase in defensive_phrases if phrase in text]
    missing = [anchor for anchor in scale_anchors if anchor not in text]
    return _check(
        "appendix_uses_submission_scale_language",
        not blocked and not missing,
        "The appendix should frame remaining work as submission-scale evidence, not defensive unsupported-claim caveats.",
        "Appendix uses current-positive-spine and scale-target language without unsupported-claim headings.",
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
        writer = csv.DictWriter(handle, fieldnames=CHECK_FIELDS)
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

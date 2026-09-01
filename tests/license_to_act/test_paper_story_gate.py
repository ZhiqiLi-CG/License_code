from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess
import sys

from license_to_act.paper_story_gate import (
    _public_surface_hygiene_check,
    build_story_gate_report,
    write_story_gate_report,
)


def test_build_story_gate_report_checks_top_conference_spine() -> None:
    report = build_story_gate_report(Path("/data/zhiqi/License"))

    summary = report["summary"]
    assert summary["total_checks"] == 24
    assert summary["passed_checks"] == 24
    assert summary["failed_checks"] == 0
    assert summary["clean_positive_passes"] == 30
    assert summary["clean_positive_trials"] == 30
    assert summary["faithful_baseline_passes"] == 8
    assert summary["faithful_baseline_trials"] == 30
    assert summary["benchmark_count"] == 3
    assert summary["state_substrate_count"] == 3
    assert summary["actor_backbone_count"] == 4
    assert summary["tau2_matched_pairs"] == 80
    assert summary["tau2_matched_reward_delta"] == 0.9875
    assert summary["meta_agent_candidates"] == 5
    assert summary["meta_agent_accepted"] == 5
    assert summary["meta_agent_source_f_to_p"] == 5
    assert summary["proposal_effect_gap_observations"] == 103
    assert summary["proposal_effect_boundary_source_successes"] == 84

    checks = {check["check_id"]: check for check in report["checks"]}
    assert checks["portfolio_breadth"]["status"] == "pass"
    assert checks["clean_positive_mass"]["status"] == "pass"
    assert checks["faithful_baseline_not_ablation"]["status"] == "pass"
    assert checks["comparison_manifest_separates_roles"]["status"] == "pass"
    assert checks["mechanism_ablation_panel_has_requested_cuts"]["status"] == "pass"
    assert checks["model_in_loop_bridge_separates_runtime_executors"]["status"] == "pass"
    assert "15/15" in checks["model_in_loop_bridge_separates_runtime_executors"]["evidence"]
    assert checks["proposal_effect_decomposition_has_real_gap_rows"]["status"] == "pass"
    assert checks["tau2_matched_boundary_pair_present"]["status"] == "pass"
    assert summary["real_evidence_planned_rows"] == 0
    assert checks["real_evidence_audit_has_only_real_results"]["status"] == "pass"
    assert "0 planned rows" in checks["real_evidence_audit_has_only_real_results"]["evidence"]
    assert "planned main positives: 0" in checks["real_evidence_audit_has_only_real_results"]["evidence"]
    assert checks["license_workspace_only"]["status"] == "pass"
    assert checks["paper_imports_generated_numbers"]["status"] == "pass"
    assert "reproducibility numbers" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "scale-matrix" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "model-in-loop" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "tau2" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "boundary-update" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "proposal/effect" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "meta-agent update" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "ablation" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "commit-pair" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert "real-evidence" in checks["paper_imports_generated_numbers"]["evidence"].lower()
    assert checks["boundary_updates_have_generation_record"]["status"] == "pass"
    assert checks["meta_agent_boundary_patch_generation"]["status"] == "pass"
    assert checks["action_boundary_story_framing"]["status"] == "pass"
    assert checks["public_surface_uses_action_boundary_terms"]["status"] == "pass"
    assert checks["story_language_anchors"]["status"] == "pass"
    assert checks["main_text_avoids_meta_curation_language"]["status"] == "pass"
    assert checks["main_text_keeps_terminology_light"]["status"] == "pass"
    assert checks["abstract_prioritizes_matched_action_boundary_evidence"]["status"] == "pass"
    assert checks["reproduction_chain_mentions_portfolio"]["status"] == "pass"
    assert "consistency export" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "scale-plan" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "model-in-loop exports" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "matched tau2 exports" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "boundary-update" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "proposal/effect" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "meta-agent update" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "ablation exports" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "commit-pair metrics" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert "real-evidence audit" in checks["reproduction_chain_mentions_portfolio"]["evidence"].lower()
    assert checks["appendix_serves_argument"]["status"] == "pass"
    assert checks["appendix_uses_submission_scale_language"]["status"] == "pass"
    assert checks["code_paper_submodules_declared"]["status"] == "pass"

    assert "ablation" not in checks["faithful_baseline_not_ablation"]["evidence"].lower()
    assert "RSI" not in checks["license_workspace_only"]["evidence"]


def test_write_story_gate_report_exports_csv_json_and_tex(tmp_path: Path) -> None:
    output = write_story_gate_report(
        Path("/data/zhiqi/License"),
        paper_data_dir=tmp_path / "paper-data",
        paper_sections_dir=tmp_path / "sections",
        summary_path=tmp_path / "artifacts" / "story_gate.json",
    )

    assert Path(output["outputs"]["summary_json"]).exists()
    assert Path(output["outputs"]["checks_csv"]).exists()
    assert Path(output["outputs"]["latex_numbers"]).exists()

    rows = list(csv.DictReader(Path(output["outputs"]["checks_csv"]).open(newline="", encoding="utf-8")))
    assert len(rows) == 24
    assert {row["status"] for row in rows} == {"pass"}

    tex = Path(output["outputs"]["latex_numbers"]).read_text(encoding="utf-8")
    assert "\\newcommand{\\LTAStoryGateChecks}{24}" in tex
    assert "\\newcommand{\\LTAStoryGatePassed}{24}" in tex
    assert "\\newcommand{\\LTAStoryGateFailed}{0}" in tex

    summary = json.loads(Path(output["outputs"]["summary_json"]).read_text(encoding="utf-8"))["summary"]
    assert summary["failed_checks"] == 0


def test_public_surface_hygiene_flags_retired_names_inside_public_text(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    paper = root / "License_paper"
    appendix = paper / "sections" / "appendix.tex"
    appendix.parent.mkdir(parents=True)
    (root / "README.md").write_text("StateTx public root.\n", encoding="utf-8")
    appendix.write_text(
        "Regenerate figures/tau2_authority_mining.pdf with "
        "scripts/export_recursive_amendment_lineage.py.\n",
        encoding="utf-8",
    )

    for repo in [root, paper]:
        subprocess.run(["git", "init"], cwd=repo, text=True, capture_output=True, check=True)
    subprocess.run(["git", "add", "README.md"], cwd=root, text=True, capture_output=True, check=True)
    subprocess.run(
        ["git", "add", "sections/appendix.tex"],
        cwd=paper,
        text=True,
        capture_output=True,
        check=True,
    )

    check = _public_surface_hygiene_check(root)

    assert check["status"] == "fail"
    assert "License_paper/sections/appendix.tex" in check["evidence"]


def test_export_story_gate_cli_writes_requested_outputs(tmp_path: Path) -> None:
    summary_path = tmp_path / "artifacts" / "story_gate.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/export_story_gate.py",
            "--paper-data-dir",
            str(tmp_path / "paper-data"),
            "--paper-sections-dir",
            str(tmp_path / "sections"),
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
    assert (tmp_path / "paper-data" / "story_gate_checks.csv").exists()
    assert (tmp_path / "sections" / "generated_story_gate_numbers.tex").exists()

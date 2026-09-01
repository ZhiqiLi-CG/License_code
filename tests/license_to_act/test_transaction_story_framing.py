from __future__ import annotations

from pathlib import Path


PAPER = Path("/data/zhiqi/License/License_paper")


def test_main_paper_leads_with_action_boundary_rsi_story() -> None:
    main = (PAPER / "main.tex").read_text(encoding="utf-8")
    intro = (PAPER / "sections" / "01_introduction.tex").read_text(encoding="utf-8")
    formulation = (PAPER / "sections" / "02_formulation.tex").read_text(encoding="utf-8")
    method = (PAPER / "sections" / "03_method.tex").read_text(encoding="utf-8")

    front_matter = main.split("\\input{sections/01_introduction}", maxsplit=1)[0]
    opening = "\n".join([front_matter, intro, formulation, method])

    assert "Beyond Better Reasoning" in main
    assert "Action Boundary RSI" in formulation
    assert "Improving the Action Boundary" in method

    for anchor in [
        "recursive self-improvement",
        "action boundary",
        "proposal-to-effect gap",
        "frozen reasoner",
        "external effects",
        "proposed effects",
        "boundary program",
        "controller",
        "ready",
        "write scope",
        "preserve",
        "done",
        "CONTINUE",
        "REVISE",
        "COMMIT",
    ]:
        assert anchor in opening

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
    for phrase in retired_front_matter:
        assert phrase not in front_matter


def test_main_paper_keeps_implementation_terms_in_their_place() -> None:
    main = (PAPER / "main.tex").read_text(encoding="utf-8")
    sections = "\n".join(
        (PAPER / "sections" / name).read_text(encoding="utf-8")
        for name in [
            "01_introduction.tex",
            "02_formulation.tex",
            "03_method.tex",
            "04_experiments.tex",
            "05_results.tex",
            "06_related_work.tex",
            "07_discussion.tex",
        ]
    )
    body = "\n".join(
        line
        for line in (main + "\n" + sections).splitlines()
        if not line.startswith("\\input{sections/generated_")
        and not line.startswith("\\newcommand")
        and not line.startswith("\\label")
    )

    for phrase in [
        "License-to-Act",
        "Action License",
        "GovKernel",
        "StateTx",
        "OBLIGE",
        "story-first",
        "main spine",
        "go signal",
        "evidence portfolio",
        "blueprint",
        "clean anchor",
        "clean executable anchor",
    ]:
        assert phrase not in body

    assert body.count("State Contract") <= 3
    assert body.count("commit controller") <= 4
    assert body.count("action boundary") >= 12
    assert "better ways to act on thought" in body


def test_public_paper_avoids_mechanical_rule_story() -> None:
    public_sections = "\n".join(
        (PAPER / "sections" / name).read_text(encoding="utf-8")
        for name in [
            "01_introduction.tex",
            "02_formulation.tex",
            "03_method.tex",
            "04_experiments.tex",
            "05_results.tex",
            "06_related_work.tex",
            "07_discussion.tex",
        ]
    )

    for phrase in [
        "current update ledger",
        "update ledger",
        "mechanical rule",
        "hand-written rule",
        "hand-authored rule",
        "task-specific rule",
    ]:
        assert phrase not in public_sections


def test_main_paper_keeps_runtime_reliability_out_of_abstract_headline() -> None:
    main = (PAPER / "main.tex").read_text(encoding="utf-8")
    abstract = main.split("\\begin{abstract}", maxsplit=1)[1].split("\\end{abstract}", maxsplit=1)[0]

    assert "proposal-to-effect gap" in abstract
    assert "matched" in abstract
    assert "Qwen3.8-27B-long32k+boundary" in abstract
    assert "executable boundary runs reach" not in abstract
    assert "\\LTAStageTwoCleanTrials{}/\\LTAStageTwoCleanTrials{}" not in abstract


def test_runtime_reruns_are_not_described_as_primary_matched_evidence() -> None:
    experiments = (PAPER / "sections" / "04_experiments.tex").read_text(encoding="utf-8")
    results = (PAPER / "sections" / "05_results.tex").read_text(encoding="utf-8")

    assert "Terminal-Bench reruns" in experiments
    assert "Runtime support" in experiments
    assert "SkillFlow reruns" in experiments
    assert "Runtime support" in experiments
    assert "Terminal-Bench reruns &" in experiments
    assert "SkillFlow reruns &" in experiments
    assert "Terminal-Bench reruns & \\LTAStageTwoTBCleanTrials{}/\\LTAStageTwoTBCleanTrials{} official passes" in experiments
    assert "SkillFlow reruns & \\LTAStageTwoSFCleanTrials{}/\\LTAStageTwoSFCleanTrials{} official passes" in experiments
    assert "Terminal-Bench reruns & \\LTAStageTwoTBCleanTrials{}/\\LTAStageTwoTBCleanTrials{} official passes over four \\(K=5\\) boundary-run tasks. & Runtime support" in experiments
    assert "SkillFlow reruns & \\LTAStageTwoSFCleanTrials{}/\\LTAStageTwoSFCleanTrials{} official passes over invoice and travel-claim completion triggers. & Runtime support" in experiments
    assert "reference-boundary rows validate executable boundary obligations, but we do not count them as matched-agent evidence" in results
    assert "Primary evidence: scoped commits are stable in terminal state" not in experiments
    assert "Primary evidence: ready evidence can trigger artifact finalization" not in experiments


def test_tau2_matched_blocks_are_not_conflated_in_public_paper_text() -> None:
    main = (PAPER / "main.tex").read_text(encoding="utf-8")
    results = (PAPER / "sections" / "05_results.tex").read_text(encoding="utf-8")
    public_text = "\n".join([main, results])

    assert "two live matched \\(K=20\\) blocks on airline task 48" in public_text
    assert "\\(\\tau^2\\) matched A48, \\(K=20\\)" in results
    assert "\\(\\tau^2\\) matched retail completion, \\(K=20\\)" in results
    assert "\\(\\tau^2\\) matched retail scope, \\(K=20\\)" in results
    assert "retail task 0" in public_text
    assert "Retail task 1 tests scope" in public_text
    assert "\\(\\tau^2\\) matched A48, \\(K=5\\)" not in results


def test_story_gate_exports_action_boundary_consistency_check() -> None:
    from license_to_act.paper_story_gate import build_story_gate_report

    report = build_story_gate_report(Path("/data/zhiqi/License"))
    checks = {check["check_id"]: check for check in report["checks"]}

    assert report["summary"]["total_checks"] == 27
    assert report["summary"]["passed_checks"] == 27
    assert checks["real_result_scale_is_substantive"]["status"] == "pass"
    assert checks["action_boundary_story_framing"]["status"] == "pass"
    assert checks["public_surface_uses_action_boundary_terms"]["status"] == "pass"
    assert checks["abstract_prioritizes_matched_action_boundary_evidence"]["status"] == "pass"
    assert "proposal-to-effect" in checks["action_boundary_story_framing"]["evidence"].lower()


def test_public_configs_and_prompts_use_action_boundary_names() -> None:
    config_paths = [
        Path("/data/zhiqi/License/License_code/configs/skillflow_action_boundary_invoice_program_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/skillflow_action_boundary_travel_claim_program_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/skillflow_action_boundary_qwen_invoice_no_prompt_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/skillflow_action_boundary_qwen_invoice_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/skillflow_action_boundary_qwen_travel_claim_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/tb21_action_boundary_log_summary_program_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/tb21_action_boundary_qwen_log_summary_official.yaml"),
        Path("/data/zhiqi/License/License_code/configs/tb21_action_boundary_sanitize_program_official.yaml"),
    ]
    for path in config_paths:
        text = path.read_text(encoding="utf-8")
        assert "GovKernelAgent" not in text
        assert "action-boundary" in text or "ActionBoundaryAgent" in text or "BoundaryProgramAgent" in text
        assert "govkernel" not in "\n".join(
            line for line in text.splitlines() if line.startswith("job_name:")
        )
        assert "materializer" not in text
        assert "executor" not in text

    harbor_agents = Path("/data/zhiqi/License/License_code/license_to_act/harbor_agents.py").read_text(encoding="utf-8")
    for phrase in [
        "commit-controller runtime",
        "boundary executor",
        "runtime executor",
        "MaterializerAgent",
        "license-to-act-invoice-materializer",
        "license-to-act-travel-claim-materializer",
    ]:
        assert phrase not in harbor_agents

    prompt_titles = [
        Path("/data/zhiqi/License/License_code/prompts/action_boundary_skillflow_invoice_commit_protocol.md").read_text(
            encoding="utf-8"
        ).splitlines()[0],
        Path("/data/zhiqi/License/License_code/prompts/action_boundary_skillflow_travel_claim_commit_protocol.md").read_text(
            encoding="utf-8"
        ).splitlines()[0],
        Path("/data/zhiqi/License/License_code/prompts/action_boundary_tb21_log_summary_commit_protocol.md").read_text(
            encoding="utf-8"
        ).splitlines()[0],
    ]
    assert all("Action Boundary" in title for title in prompt_titles)
    assert all("License-to-Act" not in title and "StateTx" not in title for title in prompt_titles)

from __future__ import annotations

from pathlib import Path


PAPER = Path("/data/zhiqi/License/License_paper")


def test_main_paper_leads_with_transaction_story() -> None:
    main = (PAPER / "main.tex").read_text(encoding="utf-8")
    intro = (PAPER / "sections" / "01_introduction.tex").read_text(encoding="utf-8")
    formulation = (PAPER / "sections" / "02_formulation.tex").read_text(encoding="utf-8")
    method = (PAPER / "sections" / "03_method.tex").read_text(encoding="utf-8")

    front_matter = main.split("\\input{sections/01_introduction}", maxsplit=1)[0]
    opening = "\n".join([front_matter, intro, formulation, method])

    assert "Stateful Agents Need Transactions" in main
    assert "The Commit Gap" in formulation
    assert "Transactional Execution for Agents" in method

    for anchor in [
        "Reasoning is speculative",
        "external state is durable",
        "commit gap",
        "transactional execution layer",
        "Candidate Change",
        "State Contract",
        "Commit Controller",
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
    ]
    for phrase in retired_front_matter:
        assert phrase not in front_matter


def test_story_gate_exports_transaction_consistency_check() -> None:
    from license_to_act.paper_story_gate import build_story_gate_report

    report = build_story_gate_report(Path("/data/zhiqi/License"))
    checks = {check["check_id"]: check for check in report["checks"]}

    assert report["summary"]["total_checks"] == 17
    assert report["summary"]["passed_checks"] == 17
    assert checks["transaction_story_framing"]["status"] == "pass"
    assert checks["public_surface_uses_transaction_terms"]["status"] == "pass"
    assert "commit gap" in checks["transaction_story_framing"]["evidence"].lower()

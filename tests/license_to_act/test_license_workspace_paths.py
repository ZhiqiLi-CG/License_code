from __future__ import annotations

from pathlib import Path


PUBLIC_PATH_ROOTS = [
    Path("/data/zhiqi/License/License_code/configs"),
    Path("/data/zhiqi/License/License_code/scripts"),
    Path("/data/zhiqi/License/License_code/license_to_act"),
    Path("/data/zhiqi/License/License_code/README.md"),
    Path("/data/zhiqi/License/License_paper/main.tex"),
    Path("/data/zhiqi/License/License_paper/sections"),
    Path("/data/zhiqi/License/License_paper/README.md"),
]


def test_public_code_and_paper_do_not_default_to_other_rsi_workspaces() -> None:
    forbidden_absolute = "/data/zhiqi/" + "RSI"
    forbidden_external = "RSI" + "1/external"
    offenders: list[str] = []
    for root in PUBLIC_PATH_ROOTS:
        paths = [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        for path in paths:
            if path.suffix in {".pyc", ".pdf", ".png"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if forbidden_absolute in text or forbidden_external in text:
                offenders.append(str(path))

    assert offenders == []

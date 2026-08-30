from __future__ import annotations

from pathlib import Path

from license_to_act.paths import artifact_path, project_root, prompt_path


def test_default_project_root_tracks_license_workspace(monkeypatch):
    monkeypatch.delenv("LICENSE_PROJECT_ROOT", raising=False)

    assert project_root() == Path("/data/zhiqi/License")
    legacy_root = "RS" + "I6"
    assert legacy_root not in str(artifact_path("paper_results", "summary.json"))


def test_project_root_can_be_overridden(monkeypatch, tmp_path):
    monkeypatch.setenv("LICENSE_PROJECT_ROOT", str(tmp_path))

    assert artifact_path("x", "y.json") == tmp_path / "artifacts" / "x" / "y.json"
    assert prompt_path("prompt.md") == tmp_path / "prompts" / "prompt.md"

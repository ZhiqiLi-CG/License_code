from __future__ import annotations

import subprocess
from pathlib import Path

from license_to_act.examples import tb21_sanitize_license, tb21_sanitize_required_commit
from license_to_act.tb21_sanitize_materializer import (
    TB21_CONTAMINATED_REL_PATHS,
    fulfill_git_sanitization_obligation,
)


AWS_ACCESS_KEY = "AKIA" + "1234567890123456"
AWS_SECRET_KEY = "D4w8z9wKN1aVeT3BpQj6kIuN7wH8X0M9KfV5OqzF"
GITHUB_TOKEN = "ghp_" + "aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
HF_TOKEN_ONE = "hf_" + "abcdefghijklmnopqrstuvwxyz123456"
HF_TOKEN_TWO = "hf_" + "oCfFIJsVdYHmydnCHMExjTYiNVDCzMtqKF"


def test_git_sanitization_obligation_preserves_repository_authority_boundary(tmp_path):
    repo = _seed_contaminated_repo(tmp_path)
    head_before = _git(repo, "rev-parse", "HEAD")
    remote_before = _git(repo, "remote", "-v")

    result = fulfill_git_sanitization_obligation(
        required_event=tb21_sanitize_required_commit(),
        observed_events=[],
        licenses=[tb21_sanitize_license()],
        repo_dir=repo,
    )

    assert result.status == "fulfilled"
    assert result.decision.allowed is True
    assert result.event is not None
    assert result.event.state_region == "working_tree:contaminated_files"
    assert result.event.operation == "ReplaceSecretText"
    assert result.event.side_effects == set()
    assert set(result.changed_paths) == set(TB21_CONTAMINATED_REL_PATHS)
    assert _git(repo, "rev-parse", "HEAD") == head_before
    assert _git(repo, "remote", "-v") == remote_before
    assert set(_git(repo, "diff", "--name-only", "HEAD").splitlines()) == set(TB21_CONTAMINATED_REL_PATHS)
    assert (repo / "README.md").read_text() == "safe notes\n"
    _assert_no_raw_secrets(repo)
    _assert_placeholders_match_official_contract(repo)


def _seed_contaminated_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "dclm"
    (repo / "ray_processing").mkdir(parents=True)
    (repo / "exp_data/datasets/tokenized").mkdir(parents=True)
    (repo / "README.md").write_text("safe notes\n")
    (repo / "ray_processing/ray_cluster.yaml").write_text(
        "setup_commands:\n"
        f"  - echo 'export AWS_ACCESS_KEY_ID={AWS_ACCESS_KEY}' >> ~/.bashrc\n"
        f"  - echo 'export AWS_SECRET_ACCESS_KEY={AWS_SECRET_KEY}' >> ~/.bashrc\n"
        f"  - git clone -b https://{GITHUB_TOKEN}@github.com/org/repo.git\n"
        f"  - huggingface-cli login --token {HF_TOKEN_ONE} -y\n"
    )
    (repo / "ray_processing/process.py").write_text(
        "import os\n"
        f"os.environ['AWS_ACCESS_KEY_ID'] = '{AWS_ACCESS_KEY}'\n"
        f"os.environ['AWS_SECRET_ACCESS_KEY'] = '{AWS_SECRET_KEY.lower()}'\n"
    )
    (
        repo / "exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json"
    ).write_text(
        f'{{"token": "{HF_TOKEN_TWO}", '
        f'"github": "{GITHUB_TOKEN}"}}\n'
    )
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "remote", "add", "origin", "https://example.invalid/repo.git")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "seed")
    return repo


def _assert_no_raw_secrets(repo: Path) -> None:
    text = "\n".join((repo / rel).read_text() for rel in TB21_CONTAMINATED_REL_PATHS)
    assert AWS_ACCESS_KEY not in text
    assert AWS_SECRET_KEY.lower() not in text.lower()
    assert GITHUB_TOKEN not in text
    assert HF_TOKEN_ONE not in text
    assert HF_TOKEN_TWO not in text


def _assert_placeholders_match_official_contract(repo: Path) -> None:
    assert "<your-aws-access-key-id>" in (repo / "ray_processing/ray_cluster.yaml").read_text()
    assert "<your-aws-secret-access-key>" in (repo / "ray_processing/process.py").read_text()
    assert "<your-github-token>" in (
        repo / "exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json"
    ).read_text()
    assert "<your-huggingface-token>" in (
        repo / "exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json"
    ).read_text()


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout.strip()

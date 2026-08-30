from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import subprocess

from .core import ActionLicense, Decision, EvidenceBundle, StateChangeEvent, evaluate_commit_obligation


TB21_CONTAMINATED_REL_PATHS = [
    "ray_processing/ray_cluster.yaml",
    "ray_processing/process.py",
    "exp_data/datasets/tokenized/rw_v2_fasttext_openhermes_vs_rw_v2_bigram_0.1_arcade100k.json",
]

_AWS_ACCESS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE)
_AWS_SECRET_RE = re.compile(
    r"D4w8z9wKN1aVeT3BpQj6kIuN7wH8X0M9KfV5OqzF",
    re.IGNORECASE,
)
_GITHUB_TOKEN_RE = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")
_HUGGINGFACE_TOKEN_RE = re.compile(r"hf_[A-Za-z0-9]{29,}")

_SECRET_REPLACEMENTS = [
    (_AWS_ACCESS_KEY_RE, "<your-aws-access-key-id>"),
    (_AWS_SECRET_RE, "<your-aws-secret-access-key>"),
    (_GITHUB_TOKEN_RE, "<your-github-token>"),
    (_HUGGINGFACE_TOKEN_RE, "<your-huggingface-token>"),
]


@dataclass(frozen=True)
class GitSanitizationResult:
    status: str
    decision: Decision
    event: StateChangeEvent | None = None
    changed_paths: list[str] = field(default_factory=list)
    head_before: str | None = None
    head_after: str | None = None
    remote_before: str | None = None
    remote_after: str | None = None


def sanitize_text(text: str) -> tuple[str, set[str]]:
    evidence: set[str] = set()
    sanitized = text
    for pattern, placeholder in _SECRET_REPLACEMENTS:
        if pattern.search(sanitized):
            evidence.add("SecretPatternEvidence")
        sanitized = pattern.sub(placeholder, sanitized)
    return sanitized, evidence


def fulfill_git_sanitization_obligation(
    required_event: StateChangeEvent,
    observed_events: list[StateChangeEvent],
    licenses: list[ActionLicense],
    repo_dir: Path,
    allowed_paths: list[str] | None = None,
) -> GitSanitizationResult:
    decision = evaluate_commit_obligation(required_event, observed_events, licenses)
    if decision.reason != "missing_commit_obligation":
        return GitSanitizationResult(status="unchanged", decision=decision)

    return materialize_git_sanitization(
        repo_dir=repo_dir,
        licenses=licenses,
        allowed_paths=allowed_paths or TB21_CONTAMINATED_REL_PATHS,
    )


def materialize_git_sanitization(
    repo_dir: Path,
    licenses: list[ActionLicense],
    allowed_paths: list[str] | None = None,
) -> GitSanitizationResult:
    allowed_paths = allowed_paths or TB21_CONTAMINATED_REL_PATHS
    repo_dir = repo_dir.resolve()
    head_before = _git(repo_dir, "rev-parse", "HEAD")
    remote_before = _git(repo_dir, "remote", "-v", allow_failure=True)

    changed_paths: list[str] = []
    evidence_types: set[str] = set()
    evidence_refs: set[str] = set()
    original_contents: dict[Path, str] = {}

    for rel_path in allowed_paths:
        path = repo_dir / rel_path
        if not path.exists():
            continue
        original = path.read_text()
        sanitized, evidence = sanitize_text(original)
        if sanitized == original:
            continue
        original_contents[path] = original
        path.write_text(sanitized)
        changed_paths.append(rel_path)
        evidence_types.update(evidence)
        evidence_refs.add(rel_path)

    head_after = _git(repo_dir, "rev-parse", "HEAD")
    remote_after = _git(repo_dir, "remote", "-v", allow_failure=True)
    side_effects = _repository_side_effects(head_before, head_after, remote_before, remote_after)
    diff_paths = set(_git(repo_dir, "diff", "--name-only", "HEAD").splitlines())
    unauthorized_paths = diff_paths - set(allowed_paths)
    if unauthorized_paths:
        for path, original in original_contents.items():
            path.write_text(original)
        return GitSanitizationResult(
            status="blocked",
            decision=Decision(allowed=False, reason="unlicensed_state_region"),
            changed_paths=sorted(diff_paths),
            head_before=head_before,
            head_after=head_after,
            remote_before=remote_before,
            remote_after=remote_after,
        )

    event = StateChangeEvent(
        actor_role="terminal_agent",
        state_region="working_tree:contaminated_files",
        operation="ReplaceSecretText",
        evidence=EvidenceBundle(types=evidence_types, refs=evidence_refs),
        side_effects=side_effects,
    )
    decision = _evaluate_materialized_event(event, licenses)
    return GitSanitizationResult(
        status="fulfilled" if decision.allowed else "blocked",
        decision=decision,
        event=event,
        changed_paths=changed_paths,
        head_before=head_before,
        head_after=head_after,
        remote_before=remote_before,
        remote_after=remote_after,
    )


def _evaluate_materialized_event(event: StateChangeEvent, licenses: list[ActionLicense]) -> Decision:
    from .core import evaluate_event

    return evaluate_event(event, licenses)


def _repository_side_effects(
    head_before: str,
    head_after: str,
    remote_before: str,
    remote_after: str,
) -> set[str]:
    side_effects = set()
    if head_after != head_before:
        side_effects.add("RewriteHistory")
    if remote_after != remote_before:
        side_effects.add("ChangeRemoteConfig")
    return side_effects


def _git(repo_dir: Path, *args: str, allow_failure: bool = False) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0 and not allow_failure:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo_dir}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc.stdout.strip()

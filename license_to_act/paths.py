from __future__ import annotations

import os
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path("/data/zhiqi/License")
PROJECT_ROOT_ENV = "LICENSE_PROJECT_ROOT"


def project_root() -> Path:
    return Path(os.environ.get(PROJECT_ROOT_ENV, str(DEFAULT_PROJECT_ROOT))).expanduser()


def artifact_path(*parts: str) -> Path:
    return project_root().joinpath("artifacts", *parts)


def prompt_path(*parts: str) -> Path:
    return project_root().joinpath("prompts", *parts)

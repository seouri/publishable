"""Whose git hash is this? Always the experiment repo's.

See docs/design-principles.md § Whose git hash is this?
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from publishable.errors import ContractError
from publishable.hashes import HASHED_TREES


@dataclass(frozen=True)
class GitInfo:
    repo_root: Path
    commit: str
    branch: str
    remote: str | None
    code_dirty: bool
    config_committed: bool


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def find_repo_root(start: Path) -> Path:
    """Walk up from the path the command was given, never from the cwd."""
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ContractError(
        f"no git repository found from {current} upwards", code="E-GIT-NO-REPO"
    )


def git_provenance(start: Path, config_path: Path) -> GitInfo:
    repo = find_repo_root(start)
    dirty = bool(_git(repo, "status", "--porcelain", "--", *HASHED_TREES))
    tracked = _git(repo, "ls-files", "--error-unmatch", str(config_path))
    return GitInfo(
        repo_root=repo,
        commit=_git(repo, "rev-parse", "HEAD"),
        branch=_git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        remote=_git(repo, "remote", "get-url", "origin") or None,
        code_dirty=dirty,
        config_committed=bool(tracked),
    )

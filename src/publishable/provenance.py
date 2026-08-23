"""Whose git hash is this? Always the experiment repo's.

See docs/design-principles.md § Whose git hash is this?
"""

import os
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


# The exclude chain is narrowed to what travels with the tree (Ruling F), and
# the dirty gate is narrowed the same way (Ruling L, 2026-08-23): a rule that
# does not travel with the tree may define neither the tree's identity nor
# whether the tree is clean. The two `-c` overrides below are ONE tuple shared
# by both call sites because the two questions must be asked of the same git,
# and two copies would drift.
#
# CONTROLLER RULING M (2026-08-23) replaced a total neutralization
# (`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM=/dev/null`, applied through the
# environment) with these two command-line overrides, applied through `-c`.
# Ruling F's own ground is about EXCLUDE rules — "a rule that does not travel
# with the tree cannot define the tree's identity" — not about every git
# setting, and the environment form neutralized far more than that:
#   * `-c core.excludesFile=` closes every exclude route on its own, measured
#     in a throwaway repo: a global config's `core.excludesFile`, the XDG
#     default `~/.config/git/ignore` that no config entry names, and a
#     repo-local `.git/config` entry. The environment variables never closed
#     the last one — `GIT_CONFIG_GLOBAL`/`SYSTEM` reach only the global and
#     system config FILES, not a repo's own `.git/config` — so they were
#     never load-bearing for excludes.
#   * `-c status.showUntrackedFiles=normal` closes what is NOT the exclude
#     chain: a global OR repo-local `status.showUntrackedFiles = no` blinds
#     the dirty gate to every untracked file under the two trees, and no
#     flag about excludes touches it. Unlike the environment form, `-c` wins
#     over a repo-local setting too, which `GIT_CONFIG_GLOBAL/SYSTEM` never
#     reached.
#
# Deliberately NOT neutralized: `core.fileMode`, `core.autocrlf`,
# `core.symlinks`, `safe.directory` and everything else the environment form
# used to discard as a side effect. Those are legitimately machine-local —
# they exist because filesystems differ — and wiping them made an UNEDITED
# file read as dirty (measured: a global `core.fileMode = false` with a
# tracked file's mode bit changed by nothing more than a `chmod`, once the
# repo's own `.git/config` does not set `core.filemode` itself). Blocking a
# run on a correct tree is a worse failure than the one this mechanism
# closes, and it lands hardest on users least able to diagnose it — a
# Windows checkout with `autocrlf`, a network mount without executable bits.
_NEUTRALIZED_CONFIG_ARGS = (
    "-c",
    "core.excludesFile=",
    "-c",
    "status.showUntrackedFiles=normal",
)


def _git(repo: Path, *args: str, neutralized: bool = False) -> str:
    """`git` in `repo`, stdout stripped, returncode discarded.

    `neutralized=True` asks the question with the two machine-local settings
    named above out of the way, exactly as `unignored_under_hashed_trees`
    does — it is for the questions whose answer must be a property of the
    tree rather than of the machine. Only the dirty gate passes it; `ls-files`
    and `rev-parse` ask about the index and the commit graph, which neither
    exclude rules nor `status.showUntrackedFiles` reach.
    """
    cmd = ["git", *(_NEUTRALIZED_CONFIG_ARGS if neutralized else ()), *args]
    result = subprocess.run(
        cmd,
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def unignored_under_hashed_trees(repo_root: Path, candidates: list[str]) -> set[str]:
    """The candidates git does NOT exclude, asked as one question in one call.

    `git check-ignore -z --stdin`, fed the repo-relative posix paths
    `hashes.hashed_files` already found, run with cwd=repo_root. Returncode 0
    means some listed path is excluded, 1 means none is, and anything else is
    a fault this refuses rather than reads: a path inside a submodule exits
    128 with `fatal: Pathspec ... is in submodule ...`, and inferring "nothing
    is excluded" from an empty stdout would hash another repository's files
    under a claim this record cannot support.

    `-z` is passed on BOTH ends and each entry is decoded with `os.fsdecode`:
    without `-z` git returns an excluded non-ASCII path C-quoted
    (`"src/pkg/na\\303\\257ve.env"`), which matches no key `hashed_files`
    produces, and `text=True` would decode with the locale's encoding rather
    than the filesystem's.

    **The exclude chain is narrowed to what travels with the tree** (Ruling
    F): the call overrides the user's `core.excludesFile` through
    `_NEUTRALIZED_CONFIG_ARGS` (Ruling M, 2026-08-23 — a `-c` override, not an
    environment neutralization), so only the repo's own `.gitignore` files
    (root and per-directory, at whatever the working tree holds) and
    `.git/info/exclude` decide what is excluded. That constant is shared with
    the dirty gate, which is narrowed the same way (Ruling L) so that the two
    mechanisms honour one exclude chain rather than two. See
    docs/reference.md § How the three are computed for the four-case rule
    this is one half of, and for the residues that survive the narrowing.

    This is NOT built on `_git`: that helper runs `check=False` and returns
    `result.stdout.strip()`, discarding the returncode — exactly the
    inference this function refuses to make. `git_provenance`'s own
    `E-GIT-NO-COMMIT` block, in this file, is the precedent for refusing at
    the one call site where an empty answer has no honest reading.
    """
    if not candidates:
        # A subprocess for a question with no subject is work with no
        # answer — and rc 1 (empty stdin) already reads correctly as
        # "nothing excluded", so this is an optimization stated as one, not
        # a correctness fix.
        return set()
    payload = b"\0".join(c.encode() for c in candidates) + b"\0"
    result = subprocess.run(
        ["git", *_NEUTRALIZED_CONFIG_ARGS, "check-ignore", "-z", "--stdin"],
        cwd=repo_root,
        input=payload,
        capture_output=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        stderr = result.stderr.decode(errors="replace")
        raise ContractError(
            f"git could not answer which of {repo_root}'s files are excluded: {stderr}",
            code="E-CODE-FILE-LIST",
        )
    excluded = {os.fsdecode(part) for part in result.stdout.split(b"\0") if part}
    return set(candidates) - excluded


def resolves_inside_repo(resolved: Path, repo_root: Path) -> bool:
    """Whether an already-resolved absolute path sits at or under `repo_root`.

    Shared by `validate._check_data` and `generators.experiment.generate_experiment`
    so the containment rule — `input_dir`/`output_dir` may never resolve inside the
    git repo — cannot drift between the two call sites that enforce it.
    """
    return resolved == repo_root or repo_root in resolved.parents


def find_repo_root(start: Path) -> Path:
    """Walk up from the path the command was given, never from the cwd."""
    current = start.resolve()
    if not current.is_dir():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise ContractError(f"no git repository found from {current} upwards", code="E-GIT-NO-REPO")


def git_provenance(start: Path, config_path: Path) -> GitInfo:
    repo = find_repo_root(start)
    # `neutralized=True` (Ruling L, surgical form per Ruling M): the gate
    # asks the same git the hash asks. Without it a file the machine's
    # global OR repo-local `core.excludesFile` excludes is clean to the gate
    # and folded into `code_hash` — a recorded identity covering a file no
    # clone of the commit contains — and a global or repo-local
    # `status.showUntrackedFiles = no` hides an uncommitted file from the
    # gate entirely. `core.fileMode`/`core.autocrlf`/`safe.directory` are
    # deliberately left alone (Ruling M): they answer how git reads the
    # filesystem, not which files it considers.
    dirty = bool(_git(repo, "status", "--porcelain", "--", *HASHED_TREES, neutralized=True))
    # `config_path` is resolved before being handed to git: `_git` runs with
    # `cwd=repo`, so a path that is relative to some OTHER cwd (e.g. the caller
    # invoked from outside the repo) would be resolved against `repo` instead and
    # miss the file that is actually tracked, silently reporting
    # `config_committed=False` for a config that is in fact committed.
    tracked = _git(repo, "ls-files", "--error-unmatch", str(config_path.resolve()))
    # --verify (not bare `rev-parse HEAD`) matters here: on a repo with no commits,
    # plain `git rev-parse HEAD` writes the literal string "HEAD" to stdout as part
    # of its usage hint even though it fails, which would make `_git`'s
    # check=False/strip() convention read back a non-empty "commit" of "HEAD".
    # `--verify` fails with clean, empty stdout instead.
    commit = _git(repo, "rev-parse", "--verify", "HEAD")
    # Unlike the other _git call sites, an empty result here has no honest reading:
    # it is not "no commit" as a fact about the repo (every repo either has a HEAD
    # or doesn't), it is `_git`'s check=False convention swallowing a failure. A
    # provenance record with commit="" would certify nothing while looking
    # well-formed, so this one call site refuses instead of recording it.
    if not commit:
        raise ContractError(
            f"repository at {repo} has no commits yet; provenance requires a HEAD",
            code="E-GIT-NO-COMMIT",
        )
    return GitInfo(
        repo_root=repo,
        commit=commit,
        branch=_git(repo, "rev-parse", "--abbrev-ref", "HEAD"),
        remote=_git(repo, "remote", "get-url", "origin") or None,
        code_dirty=dirty,
        config_committed=bool(tracked),
    )

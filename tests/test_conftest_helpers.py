import subprocess
from pathlib import Path

from tests.conftest import _copy_repo, git


def test_git_repo_fixture_is_a_clean_repo_with_one_commit(git_repo: Path):
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=git_repo)
    assert branch
    assert git("status", "--porcelain", cwd=git_repo) == ""


def test_git_repo_prototype_has_background_maintenance_off(git_repo: Path):
    """The prototype every `git_repo` is copied from spawns no background git.

    `git commit` fires a detached `git maintenance run --auto` that holds
    `.git/objects/maintenance.lock` after the commit returns, and ~1500 copies
    race it. Read off a copy rather than the prototype, because the config is
    what the copy inherits and the copy is what tests are handed.
    """
    assert git("config", "gc.auto", cwd=git_repo) == "0"
    assert git("config", "maintenance.auto", cwd=git_repo) == "false"


def test_copy_repo_skips_lock_files_and_copies_everything_else(tmp_path: Path):
    """The second half of the same fix, pinned where it can fail.

    Asserting the lock's absence alone would pass on a copy that did nothing,
    so the two real files are asserted present in the same test — and the
    nested one proves the skip is not merely top-level.
    """
    src = tmp_path / "src_repo"
    (src / ".git" / "objects").mkdir(parents=True)
    (src / ".git" / "objects" / "maintenance.lock").write_text("")
    (src / ".git" / "index.lock").write_text("")
    (src / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (src / "kept.py").write_text("# kept\n")

    dst = _copy_repo(src, tmp_path / "dst_repo")

    assert (dst / "kept.py").read_text() == "# kept\n"
    assert (dst / ".git" / "HEAD").read_text() == "ref: refs/heads/main\n"
    assert not (dst / ".git" / "objects" / "maintenance.lock").exists()
    assert not (dst / ".git" / "index.lock").exists()


def test_every_git_subprocess_sees_maintenance_off(tmp_path: Path):
    """The environment half: a repo this suite never configured still reports it.

    `git_repo`'s own config is set locally by `_build_git_repo`, so reading it
    there could not distinguish the two halves. This repo is `git init`-ed here
    and configured by nothing, so the only place these values can come from is
    the environment every git subprocess inherits — which is what covers the
    ~70 commit sites that do not go through `_build_git_repo`.
    """
    repo = tmp_path / "bare_of_config"
    repo.mkdir()
    git("init", "-q", ".", cwd=repo)

    assert git("config", "gc.auto", cwd=repo) == "0"
    assert git("config", "maintenance.auto", cwd=repo) == "false"

    # And nothing local supplies them, so the two above can only be the
    # environment. `git config --get` exits 1 on an unset key, which is why
    # this asks through `subprocess` rather than through `git()`.
    local = subprocess.run(
        ["git", "config", "--local", "--get", "gc.auto"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert local.returncode == 1 and local.stdout == ""

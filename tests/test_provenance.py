from pathlib import Path

import pytest
from tests.conftest import git

from publishable import ContractError
from publishable.provenance import find_repo_root, git_provenance
from publishable.uv_support import uv_lock_info


def test_walk_up_starts_at_the_path_given_not_the_cwd(git_repo: Path):
    nested = git_repo / "configs" / "cohort-pilot"
    nested.mkdir(parents=True)
    (nested / "config.yaml").write_text("x: 1\n")
    assert find_repo_root(nested / "config.yaml") == git_repo


def test_no_repo_is_an_error_naming_where_it_looked(tmp_path: Path):
    with pytest.raises(ContractError) as e:
        find_repo_root(tmp_path / "nowhere.yaml")
    assert e.value.code == "E-GIT-NO-REPO"
    assert str(tmp_path) in str(e.value)


def test_a_clean_tree_is_not_dirty(git_repo: Path):
    info = git_provenance(git_repo, git_repo / "configs" / "c.yaml")
    assert info.code_dirty is False
    assert len(info.commit) == 40
    assert info.branch


def test_only_the_hashed_trees_make_it_dirty(git_repo: Path):
    (git_repo / "docs").mkdir()
    (git_repo / "docs" / "notes.md").write_text("untracked\n")
    assert git_provenance(git_repo, git_repo / "c.yaml").code_dirty is False
    (git_repo / "src" / "placeholder.py").write_text("changed\n")
    assert git_provenance(git_repo, git_repo / "c.yaml").code_dirty is True


def test_config_committed_is_recorded_not_required(git_repo: Path):
    cfg = git_repo / "configs" / "c.yaml"
    cfg.parent.mkdir()
    cfg.write_text("x: 1\n")
    assert git_provenance(git_repo, cfg).config_committed is False
    git("add", "configs", cwd=git_repo)
    git("commit", "-qm", "add config", cwd=git_repo)
    assert git_provenance(git_repo, cfg).config_committed is True


def test_config_committed_is_correct_for_a_relative_path_from_elsewhere(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
):
    """`_git` runs with `cwd=repo`, so a relative `config_path` must be resolved
    against the caller's cwd before being handed to git — not left to be resolved
    against `repo`, which would miss the tracked file and report `False`.
    """
    cfg = git_repo / "configs" / "c.yaml"
    cfg.parent.mkdir()
    cfg.write_text("x: 1\n")
    git("add", "configs", cwd=git_repo)
    git("commit", "-qm", "add config", cwd=git_repo)

    elsewhere = git_repo.parent
    monkeypatch.chdir(elsewhere)
    relative = Path("repo") / "configs" / "c.yaml"
    assert not relative.is_absolute()
    assert git_provenance(git_repo, relative).config_committed is True


def test_zero_commits_is_an_error_not_an_empty_string(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "placeholder.py").write_text("# placeholder\n")
    git("init", "-q", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test", cwd=repo)
    with pytest.raises(ContractError) as e:
        git_provenance(repo, repo / "c.yaml")
    assert e.value.code == "E-GIT-NO-COMMIT"
    assert str(repo) in str(e.value)


def test_the_normal_path_is_untouched(git_repo: Path):
    info = git_provenance(git_repo, git_repo / "c.yaml")
    assert len(info.commit) == 40


def test_a_missing_lockfile_is_reported_as_absent(git_repo: Path):
    assert uv_lock_info(git_repo) == (None, None)


def test_a_present_lockfile_is_hashed(git_repo: Path):
    (git_repo / "uv.lock").write_text("version = 1\n")
    path, digest = uv_lock_info(git_repo)
    assert path == git_repo / "uv.lock"
    assert digest is not None and digest.startswith("sha256:")

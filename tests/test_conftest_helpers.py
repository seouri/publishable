from pathlib import Path

from tests.conftest import git


def test_git_repo_fixture_is_a_clean_repo_with_one_commit(git_repo: Path):
    branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=git_repo)
    assert branch
    assert git("status", "--porcelain", cwd=git_repo) == ""

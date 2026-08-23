from pathlib import Path

import pytest
from tests.conftest import git

from publishable import ContractError
from publishable.hashes import code_hash_of, hashed_files
from publishable.provenance import find_repo_root, git_provenance, unignored_under_hashed_trees
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


# ---------------------------------------------------------------------------
# H6a task 4 — `unignored_under_hashed_trees`. The base tree and its digest
# are the plan's own ("the base tree, used by A-F"): a committed repo whose
# `.gitignore` holds the scaffold's four patterns, `src/pkg/step.py` = `a =
# 1\n`, `templates/t.py` = `b = 2\n`, nothing else under either tree.
# `code_hash_of` over it is `sha256:71bf339c...`, computed by running, not
# recalled from the plan.


def _write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


_BASE_DIGEST = "sha256:71bf339cc9463f4c776c711f3d65ccf9b3bc1e18d383b78ae7d4e5170b526c2b"


def _base_tree(root: Path) -> Path:
    _write(root, ".gitignore", ".env\n__pycache__/\n*.py[cod]\n.venv/\n")
    _write(root, "src/pkg/step.py", "a = 1\n")
    _write(root, "templates/t.py", "b = 2\n")
    git("init", "-q", cwd=root)
    git("add", ".gitignore", "src/pkg/step.py", "templates/t.py", cwd=root)
    git("-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "base", cwd=root)
    return root


def test_nothing_excluded_returns_every_candidate_unchanged(tmp_path: Path):
    """The base tree alone: no `.gitignore` pattern matches anything present,
    `check-ignore` answers rc 1, and the whole candidate set comes back —
    the tri-state's "none is" branch, positively exercised rather than only
    implied by a subtraction that happens to subtract nothing.
    """
    repo = _base_tree(tmp_path / "repo")
    candidates = [rel for rel, _ in hashed_files(repo, None)]
    assert unignored_under_hashed_trees(repo, candidates) == set(candidates)


def test_the_ascii_control_subtracts_exactly_the_excluded_path(tmp_path: Path):
    """The ASCII control (step 8): a tree with an excluded ASCII path only
    returns the same SHAPE of answer as Fixture F below — a plain
    subtraction — so a reviewer can see the non-ASCII arm is testing the
    `-z`/`os.fsdecode` encoding, not the mechanism.
    """
    repo = _base_tree(tmp_path / "repo")
    _write(repo, "src/pkg/.env", "OPENAI_API_KEY=sk-live-1\n")
    candidates = [rel for rel, _ in hashed_files(repo, None)]
    assert set(candidates) == {"src/pkg/step.py", "templates/t.py", "src/pkg/.env"}
    kept = unignored_under_hashed_trees(repo, candidates)
    assert kept == {"src/pkg/step.py", "templates/t.py"}


def test_an_empty_candidate_list_is_the_empty_set_without_a_subprocess(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Step 3 of the "forbidden by name" list: a question with no subject is
    work with no answer. Asserted by refusing to let `subprocess.run` be
    called at all, not merely by checking the return value — the short
    circuit must be BEFORE the subprocess, not merely produce the same
    answer as one.
    """
    import publishable.provenance as provenance_module

    # Build the repo BEFORE patching: `provenance_module.subprocess` is the
    # same module object `conftest.git()` calls through, so patching first
    # would boom on the fixture's own `git init`, not on the call under test.
    repo = _base_tree(tmp_path / "repo")

    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("subprocess.run must not be called for an empty candidate list")

    monkeypatch.setattr(provenance_module.subprocess, "run", _boom)
    assert unignored_under_hashed_trees(repo, []) == set()


def test_h6a_fixture_f_the_z_claim_on_excluded_non_ascii_paths(tmp_path: Path):
    """Fixture F (§ Corrections 4, replacing the design's tracked-file
    version). Two claims: set equality on the KEPT set, which is what `-z`
    protects, and that `code_hash_of` over the kept pairs reproduces the
    base tree's own digest — `sha256:71bf339c...` — because the two excluded
    files must contribute nothing to the fold.

    Measured on macOS/APFS with `core.precomposeunicode = true`. Both new
    paths are UNTRACKED, so neither round-trips through the index and no
    NFC/NFD normalization question arises on any platform.
    """
    repo = _base_tree(tmp_path / "repo")
    gitignore = repo / ".gitignore"
    gitignore.write_text(gitignore.read_text() + "*.env\n")
    _write(repo, "src/pkg/naïve.env", "K=1\n")
    _write(repo, "src/pkg/ünï.pyd", "x\n")

    def include(candidates: list[str]) -> set[str]:
        return unignored_under_hashed_trees(repo, candidates)

    pairs = hashed_files(repo, include)
    kept = {rel for rel, _ in pairs}
    assert kept == {"src/pkg/step.py", "templates/t.py"}
    assert code_hash_of(pairs) == _BASE_DIGEST


def _submodule_host(tmp_path: Path) -> Path:
    """Fixture I's tree: a host repo with `src/vendor` added as a real git
    submodule holding `lib/z.py`, plus the base tree's own `src/pkg/step.py`
    and `templates/t.py`. `-c protocol.file.allow=always` on `submodule add`
    is required for a local (`file://`-ish) submodule URL — measured, not
    guessed.
    """
    vendor = tmp_path / "vendor_repo"
    _write(vendor, "lib/z.py", "z = 1\n")
    git("init", "-q", cwd=vendor)
    git("add", ".", cwd=vendor)
    git("-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "vend", cwd=vendor)

    host = _base_tree(tmp_path / "host")
    git(
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        str(vendor),
        "src/vendor",
        cwd=host,
    )
    git("-c", "user.email=t@e.com", "-c", "user.name=t", "commit", "-qm", "addsub", cwd=host)
    return host


def test_h6a_fixture_i_a_submodule_refuses_rather_than_reading_empty_stdout(tmp_path: Path):
    """Fixture I. `check-ignore` exits 128 on a submodule path with `fatal:
    Pathspec 'src/vendor/lib/z.py' is in submodule 'src/vendor'` — measured,
    not guessed — and this must refuse rather than read the empty stdout
    that accompanies rc 128 as "nothing excluded". This is also this task's
    positive control for the forbidden route "must NOT call `_git`":
    `_git`'s `check=False`/`.strip()` would turn that empty stdout into
    exactly the silent misreading this refusal exists to prevent, which is
    why mutation 6 (routing the call through `_git`) is caught here — a
    mutant reading that route keeps every candidate and raises nothing.
    """
    host = _submodule_host(tmp_path)
    candidates = ["src/pkg/step.py", "src/vendor/lib/z.py", "templates/t.py"]
    with pytest.raises(ContractError) as e:
        unignored_under_hashed_trees(host, candidates)
    assert e.value.code == "E-CODE-FILE-LIST"
    assert "src/vendor" in str(e.value)

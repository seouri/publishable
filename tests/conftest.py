import importlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _restore_environ():
    """Restore `os.environ` around every test in the suite.

    `secrets.load_env` calls `python-dotenv`'s `load_dotenv`, which writes straight
    into `os.environ` rather than through `monkeypatch` — so `monkeypatch` cannot undo
    it and a value one test's `.env` writes survives into the next. That leak was
    observed, not anticipated: it made a later test in `test_secrets.py` fail on a
    value an earlier one had loaded.

    It lives here rather than beside those tests because every module that exercises
    a load path inherits the same hazard, and a per-file fixture leaves the next one
    to rediscover it. Restoring by snapshot covers deletions as well as writes, which
    a fixture that only unset what it saw would not.
    """
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


EXPERIMENT_MODULE = """\
from publishable import BaseExperiment, BaseStep


class Step01LoadCohort(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        return {}


class CohortPilotExperiment(BaseExperiment):
    steps = [Step01LoadCohort]
"""


def write_experiment_module(repo: Path, body: str = EXPERIMENT_MODULE) -> Path:
    """Put `cohort_pilot.experiment` where a config's `entrypoint` says it is.

    `validate` imports the entrypoint (to answer `W-REPL-DETERMINISTIC`, which
    reads `nondeterministic` off a step class), so a fixture repo without this
    package makes every config invalid for a reason no test is about.
    """
    package = repo / "src" / "cohort_pilot"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text("")
    path = package / "experiment.py"
    path.write_text(body)
    return path


def _build_git_repo(repo: Path) -> Path:
    """Create the one-commit repository `git_repo` hands out, from nothing."""
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "placeholder.py").write_text("# placeholder\n")
    write_experiment_module(repo)  # committed, so the tree stays clean
    git("init", "-q", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test", cwd=repo)
    git("add", ".", cwd=repo)
    git("-c", "commit.gpgsign=false", "commit", "-qm", "initial", cwd=repo)
    return repo


@pytest.fixture(scope="session")
def _git_repo_prototype(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Built once per session; `git_repo` copies it rather than rebuilding it.

    Around 1500 tests take `git_repo`, and building one costs five `git`
    subprocesses — measured at ~82ms against ~7ms for a `copytree` of the
    finished tree, which is ~75s of the suite's wall clock. The copy is a real
    repository, not a mock: `git status` reports it clean and `rev-parse HEAD`
    resolves, because a repository holds no absolute path outside `.git/config`
    and `copytree` preserves the mtimes the index caches.

    The one property the copy does not have is a commit SHA of its own — every
    test now shares one. Nothing here asserts two fixtures differ, and a test
    that needs a distinct history should commit into its copy, which changes the
    SHA the same way it always did.
    """
    return _build_git_repo(tmp_path_factory.mktemp("git_repo_prototype") / "repo")


@pytest.fixture
def git_repo(tmp_path: Path, _git_repo_prototype: Path) -> Path:
    """A real git repo with one commit. Provenance is never mocked."""
    repo = tmp_path / "repo"
    shutil.copytree(_git_repo_prototype, repo, symlinks=True)
    return repo


_DIST_METADATA = """\
Metadata-Version: 2.1
Name: {name}
Version: {version}
"""


@pytest.fixture
def installed(tmp_path: Path, monkeypatch):
    """Write a real installed distribution and put it where `importlib.metadata` looks.

    A `<name>-<version>.dist-info/` holding `METADATA` and `entry_points.txt` is
    exactly what `uv` and `pip` write, and `importlib.metadata` finds a
    distribution by scanning each `sys.path` entry for one — so this exercises
    the real discovery path rather than a patch of `entry_points`. What it does
    not exercise is a build backend turning a `pyproject.toml` entry-points table
    into `entry_points.txt`; core reads no `pyproject.toml`, so that translation
    is outside anything a test here could pin.

    Each call gets its own directory. `importlib.metadata`'s path cache is keyed
    on a directory and its mtime, so adding a second `.dist-info` to a directory
    already scanned in the same test can be served from cache; two distributions
    therefore means two calls and two directories.

    A plain fixture rather than an autouse one, and requested by name:
    `monkeypatch.syspath_prepend` already restores `sys.path` per test, and the
    environ fixture above is the only autouse fixture this suite has.
    """
    made = 0

    def _install(dist_name: str, version: str, groups: dict[str, dict[str, str]]) -> Path:
        nonlocal made
        made += 1
        site = tmp_path / f"site{made}"
        info = site / f"{dist_name.replace('-', '_')}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(_DIST_METADATA.format(name=dist_name, version=version))
        (info / "entry_points.txt").write_text(
            "".join(
                f"[{group}]\n" + "".join(f"{k} = {v}\n" for k, v in entries.items()) + "\n"
                for group, entries in groups.items()
            )
        )
        monkeypatch.syspath_prepend(str(site))
        importlib.invalidate_caches()
        return site

    return _install


@pytest.fixture
def registries():
    """Restore the process-level plugin registries around a test that fills them.

    These mappings are module-global by design — a decorator runs at import and
    has nowhere else to put what it recorded — so a test that registers a name
    leaks it into every test after it. Restored by snapshot rather than by
    unsetting what was seen, which covers a test that replaces an entry as well
    as one that adds it. A plain fixture requested by name: the suite's one
    autouse fixture is `conftest`'s environ restore and there may not be a
    second.
    """
    from publishable import artifacts, plugins

    saved = (
        dict(plugins.RESOLVERS),
        dict(plugins.PROBES),
        dict(artifacts.WRITERS),
        dict(artifacts.READERS),
    )
    # W1: `plugins.claims` memoizes an entry-point scan for the life of the
    # process, because `artifacts._suffix_for` consults it on every write and
    # every read. That memo sits ABOVE the four mappings restored below, so
    # restoring them is not enough — a test that installs a distribution would
    # otherwise leave its suffix a dispatch candidate for every later test, and a
    # test installing one AFTER a scan has run would be served the pre-install
    # answer. Cleared on both sides of the yield for the two halves of that.
    plugins.reset_claims()
    yield
    plugins.reset_claims()
    for live, was in zip(
        (plugins.RESOLVERS, plugins.PROBES, artifacts.WRITERS, artifacts.READERS),
        saved,
        strict=True,
    ):
        live.clear()
        live.update(was)

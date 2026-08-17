import importlib
import os
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


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A real git repo with one commit. Provenance is never mocked."""
    repo = tmp_path / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "placeholder.py").write_text("# placeholder\n")
    write_experiment_module(repo)  # committed, so the tree stays clean
    git("init", "-q", cwd=repo)
    git("config", "user.email", "test@example.com", cwd=repo)
    git("config", "user.name", "Test", cwd=repo)
    git("add", ".", cwd=repo)
    git("-c", "commit.gpgsign=false", "commit", "-qm", "initial", cwd=repo)
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

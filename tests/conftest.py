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

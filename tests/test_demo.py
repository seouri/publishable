"""`publishable demo` — the guided arc, tested against what it actually writes.

`docs/reference.md` § What `demo` walks you through is the specification. The
numbers this walkthrough prints are its own (Ruling DD): `demo` generates a real
dataset and runs the real commands, so the arms below assert against a real run
rather than against a transcript anybody typed.
"""

import subprocess
from pathlib import Path

import pytest

from publishable.cli import main
from publishable.demo import (
    DEMO_UNITS,
    PROGRESS_FILE,
    build_demo_project,
    command_demo,
    data_root,
    read_progress,
)
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A home directory of this test's own.

    `demo` writes its data to `~/publishable-demo-data`, which is the documented
    location and the point of the stop — data outside the repo. A test that let
    that resolve to the real home would write into the person running it.
    """
    fake = tmp_path / "home"
    fake.mkdir()
    monkeypatch.setenv("HOME", str(fake))
    monkeypatch.chdir(fake)
    return fake


def test_stop_1_writes_the_data_outside_the_repo_and_leaves_a_clean_tree(home: Path):
    root = home / "publishable-demo"
    config = build_demo_project(root)

    index = data_root() / "input" / "index.csv"
    assert index.is_file()
    assert not index.is_relative_to(root), "the data must not sit inside the repository"
    rows = index.read_text().strip().split("\n")
    assert rows[0] == "unit_id,x,y"
    assert len(rows) == DEMO_UNITS + 1
    assert rows[1].startswith("u001,") and rows[-1].startswith("u240,")

    assert (root / "templates" / "correlation.py").is_file()
    assert (root / "src" / "correlation_pilot" / "experiment.py").is_file()
    for step in ("step01_load_cohort", "step02_fit_model", "step03_analyze"):
        assert (root / "src" / "correlation_pilot" / "steps" / f"{step}.py").is_file()
    assert config == root / "configs" / "correlation-pilot" / "config.yaml"

    # The tree is clean afterwards, which is what keeps stop 5's `run` a real
    # run rather than a `draft`.
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
    )
    assert status.stdout == "", status.stdout


def test_the_config_stop_1_writes_validates(home: Path):
    root = home / "publishable-demo"
    config = build_demo_project(root)
    assert main(["validate", str(config)]) == EXIT_OK


def test_the_dataset_is_byte_identical_across_two_invocations(home: Path, tmp_path: Path):
    """Design § 10 row 11: a generator seeded from the clock gives two different
    files here. The recipe is a fixed literal, so two people comparing screens
    are comparing the same 240 rows."""
    build_demo_project(home / "one")
    first = (data_root() / "input" / "index.csv").read_bytes()
    (data_root() / "input" / "index.csv").unlink()
    build_demo_project(home / "two")
    second = (data_root() / "input" / "index.csv").read_bytes()
    assert first == second
    # And it is not empty-equals-empty: the file has real content in it.
    assert len(first.splitlines()) == DEMO_UNITS + 1


def test_demo_progress_is_ignored_in_the_demo_repo(home: Path):
    """Design § 10 row 10, first half: `demo` appends the line to the demo
    repository's own `.gitignore`, so the file it writes to track your place can
    never dirty the tree.

    The row's SECOND half — that `.demo-progress` is absent from a plain
    `publishable new` project's `.gitignore`, which one assertion cannot
    separate from this one — is pinned by
    `tests/test_scaffold.py::test_the_scaffolded_gitignore_still_says_nothing_about_demo_progress`,
    written by task 3. Cited rather than restated: the same list pinned twice is
    a pin that reports an edit rather than a claim, and both halves were run
    against the widening mutation (adding the line to the shipped constant),
    which fails that arm and guard-pin arm D.
    """
    root = home / "publishable-demo"
    build_demo_project(root)
    (root / PROGRESS_FILE).write_text("stop 2\n")
    ignored = subprocess.run(
        ["git", "check-ignore", PROGRESS_FILE], cwd=root, capture_output=True, text=True
    )
    assert ignored.returncode == 0, "the demo repo must ignore .demo-progress"
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=True
    )
    assert status.stdout == "", status.stdout


def test_stop_2_prints_the_sweep_and_replication_blocks_verbatim(home: Path, capsys):
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    text = (root / "configs" / "correlation-pilot" / "config.yaml").read_text()

    # Verbatim means verbatim: the block as it stands in the file, comments and
    # all, rather than a re-rendering of it.
    sweep_start = text.index("sweep:")
    sweep = text[sweep_start : text.index("replication:")].rstrip("\n")
    assert sweep in out, out
    replication = text[text.index("replication:") : text.index("statistics:")].rstrip("\n")
    assert replication in out, out
    assert "baseline: {analysis.method: pearson}" in out
    assert "{kind: seed, n: 5}" in out


def test_stop_1_reports_what_it_created(home: Path, capsys):
    assert command_demo(home / "publishable-demo") == EXIT_OK
    out = capsys.readouterr().out
    assert f"  {DEMO_UNITS} synthetic units" in out
    assert "templates/correlation.py" in out
    assert "src/correlation_pilot/" in out
    assert "configs/correlation-pilot/config.yaml" in out


def test_progress_records_the_stop_and_a_second_invocation_resumes(home: Path, capsys):
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    assert read_progress(root) == 2
    capsys.readouterr()
    assert command_demo(root) == EXIT_OK
    assert "Resuming" in capsys.readouterr().out


def test_demo_defers_to_the_unbuilt_diagnostic_while_its_row_says_so(capsys):
    """TRANSITIONAL — task 13 deletes this test with the dictionary key and the
    two lines in `_dispatch` that produce it. While `docs/reference.md`
    § Creation commands marks `demo` `NOT BUILT`,
    `test_reference_cli_tables_match_what_the_cli_does` binds that row to the
    specified-but-unbuilt diagnostic for every invocation of the name, and a
    wrong-arity one is an invocation of the name."""
    from publishable import cli

    assert "demo" in cli.NOT_BUILT_COMMANDS
    assert main(["demo", "_probe_a", "_probe_b"]) == EXIT_INVOCATION
    assert "is specified but not built" in capsys.readouterr().err

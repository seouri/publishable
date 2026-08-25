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
    latest_run_yaml,
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
    """`.demo-progress` is what makes resuming a property of the directory:
    `validate` and `dry-run` create nothing, so the filesystem alone cannot tell
    stop 3 from stop 4."""
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    assert read_progress(root) == 6
    capsys.readouterr()
    assert command_demo(root) == EXIT_OK
    assert "This demo is finished" in capsys.readouterr().out


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


# --- Stops 3 through 6, and the transcript's own numbers --------------------


def _tree(root: Path) -> dict[str, bytes]:
    """Every file under `root` except the progress marker, by content."""
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file() and p.name != PROGRESS_FILE and ".git/" not in str(p.relative_to(root))
    }


def test_the_whole_walk_runs_straight_through_with_nothing_attached_to_stdin(
    home: Path, capsys, monkeypatch
):
    """Design § 10 row 12: `demo` pausing with no terminal attached blocks
    forever in CI. Both halves — the sequence completes AND nothing was read
    from stdin — because a test asserting only completion passes on a build that
    reads a line and gets EOF."""

    def refuse() -> str:
        raise AssertionError("`demo` read from stdin with no terminal attached")

    monkeypatch.setattr("builtins.input", refuse)
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    assert "publishable validate configs/correlation-pilot/config.yaml" in out
    assert "publishable dry-run configs/correlation-pilot/config.yaml" in out
    assert "publishable run configs/correlation-pilot/config.yaml" in out
    assert "publishable reproduce " in out
    assert read_progress(root) == 6


def test_the_stop_5_summary_is_demos_own_and_matches_the_record_run_wrote(home: Path, capsys):
    """Fixture A's transcript half, asserted against a real run rather than
    against a literal list: every figure `demo` prints is read back out of the
    `run.yaml` `run` just wrote. Ruling DD is what this arm enforces —
    `correlation_pilot`'s numbers are whatever the run produces, and README
    quotes these."""
    import yaml

    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out

    run_yaml = latest_run_yaml(root)
    doc = yaml.safe_load(run_yaml.read_text())
    conditions = doc["results"]["conditions"]
    assert doc["status"] == "completed"

    for cond in conditions:
        entry = next(iter(cond["aggregated"].values()))["r"]
        assert entry["method"] == "percentile_over_units"
        assert f"{entry['value']:.3f}" in out
        assert f"[{entry['ci95'][0]:.3f}, {entry['ci95'][1]:.3f}]" in out
        assert entry["n"] == {"resolved": 240, "completed": 228, "ineligible": 0, "failed": 12}
        # A DERIVED metric carries no `repeat_spread`, so the transcript's
        # spread line may not be read off `r` (correction 8).
        assert "repeat_spread" not in entry
        for delta_block in (cond.get("vs_baseline") or {}).values():
            delta = delta_block["r"]
            assert delta["method"] == "paired_percentile_over_units", delta
            assert delta["n_paired"] == 228
            assert f"{delta['delta']:+.3f}" in out

    assert "intervals over 228 of 240 units (12 failed)" in out
    # The spread reported is a RECORDED column's, and the line says which.
    recorded = next(iter(conditions[0]["aggregated"].values()))["pred"]
    assert f"std {recorded['repeat_spread']['std']:.3f} of recorded `pred`" in out
    assert recorded["repeat_spread"]["kind"] == "seed"


def test_run_itself_prints_no_table_banner_or_progress_bar(home: Path, capsys):
    """Decision 7, and the reason the summary above is `demo`'s: `run`'s entire
    stdout for a successful run is the warning block and one `run.yaml → <path>`
    line. Asserted on `run`'s own output, not on `demo`'s."""
    root = home / "publishable-demo"
    config = build_demo_project(root)
    capsys.readouterr()
    assert main(["run", str(config)]) == EXIT_OK
    out = capsys.readouterr().out
    assert "run.yaml → " in out
    assert "condition             r" not in out
    assert "████" not in out
    assert "executions" not in out
    lines = [line for line in out.split("\n") if line.strip() and "W-ENV-UNLOCKED" not in line]
    assert all(
        line.startswith("run.yaml → ") or line.startswith(" ") or "problem" in line
        for line in lines
    ), lines


def test_stop_4s_commentary_names_both_counts(home: Path, capsys):
    """Decision 14: `dry-run` prints 19 and the sweep is 3 × 5 = 15. A
    walkthrough whose commentary contradicts the output on the screen teaches a
    reader to distrust it, so both are named and `dry-run` is not changed."""
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    assert "× 5 repeats = 19 executions" in out, "dry-run's own line must not move"
    assert "3 conditions × 5 repeats = 15 repeat-scoped executions, and 19 in all" in out


def test_stop_5s_commentary_names_the_warning_rather_than_suppressing_it(home: Path, capsys):
    """Decision 15: the first `run` a newcomer issues prints `W-ENV-UNLOCKED`,
    and `demo` explains it. Nothing is suppressed and no lockfile is
    fabricated."""
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    assert "W-ENV-UNLOCKED" in out
    assert "W-ENV-UNLOCKED fired because this project has no uv.lock" in out
    assert not (root / "uv.lock").exists()


def test_stop_6_prints_the_reproduce_invocation_and_executes_nothing(
    home: Path, capsys, monkeypatch
):
    """Design § 10 row 14, in TWO assertions, because the whole-tree snapshot
    alone cannot see this mutation.

    Measured rather than assumed: a `demo` that both prints the invocation AND
    runs `reproduce` leaves the tree byte-identical — this demo repo has no
    remote, so `reproduce` refuses before it creates anything, and a snapshot
    arm passes with the behaviour neutered. So the snapshot stays (it is what
    catches a stop 6 that clones or checks out on a machine where the clone
    would succeed) and a sentinel on `_run_in_project` is what says stop 6 ran
    no command at all.
    """
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    (root / PROGRESS_FILE).write_text("stop 5\n")
    before = _tree(home)
    capsys.readouterr()

    def refuse(*args, **kwargs):
        raise AssertionError("stop 6 executed a command; it prints one")

    monkeypatch.setattr("publishable.demo._run_in_project", refuse)
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    assert f"publishable reproduce {latest_run_yaml(root)}" in out
    assert _tree(home) == before, "stop 6 printed a command; it must not run one"


def test_q_leaves_you_holding_the_remaining_commands_and_resumes_where_you_left(
    home: Path, capsys, monkeypatch
):
    """Design § 10 row 15: resuming is a property of the DIRECTORY. A second
    invocation in a directory holding a `.demo-progress` picks up the stop it
    left rather than starting over."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda: "q")
    root = home / "publishable-demo"
    assert command_demo(root) == EXIT_OK
    out = capsys.readouterr().out
    assert "The rest of the walk, in order:" in out
    assert "publishable validate configs/correlation-pilot/config.yaml" in out
    assert "publishable run configs/correlation-pilot/config.yaml" in out
    left_at = read_progress(root)
    assert left_at == 1

    monkeypatch.setattr("builtins.input", lambda: "")
    assert command_demo(root) == EXIT_OK
    resumed = capsys.readouterr().out
    assert f"Resuming the demo in {root} at stop {left_at + 1}" in resumed
    assert read_progress(root) == 6


def test_no_pause_alters_the_config(home: Path, capsys, monkeypatch):
    """Design § 10 row 13: every prompt is proceed-or-quit, so a `q` and a
    resume must produce the identical parameters. Compared on
    `parameters_hash` — the record's own answer to *were these the same
    parameters* — rather than on the config text, which a prompt could reach
    without moving a byte a diff would show."""
    import yaml

    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    answers = iter(["", "q"])
    monkeypatch.setattr("builtins.input", lambda: next(answers, ""))
    interrupted = home / "interrupted"
    assert command_demo(interrupted) == EXIT_OK
    monkeypatch.setattr("builtins.input", lambda: "")
    assert command_demo(interrupted) == EXIT_OK
    stopped_hash = yaml.safe_load(latest_run_yaml(interrupted).read_text())["parameters_hash"]

    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    straight = home / "straight"
    assert command_demo(straight) == EXIT_OK
    straight_hash = yaml.safe_load(latest_run_yaml(straight).read_text())["parameters_hash"]

    assert stopped_hash == straight_hash
    assert stopped_hash.startswith("sha256:")
    capsys.readouterr()

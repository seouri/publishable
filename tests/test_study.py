# tests/test_study.py
"""`study new` and `study add`. docs/reference.md § Studies: what a paper
reports. H8c tasks 11-14 —
`docs/superpowers/plans/2026-08-21-report-study.md`,
`docs/superpowers/specs/2026-08-21-report-study-design.md` Decisions 9-13.
"""

from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project
from tests.test_report import _fixture_j_run

from publishable.cli import main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK, EXIT_WRONG
from publishable.errors import ContractError
from publishable.run_record import SCHEMA_VERSION
from publishable.study import (
    REDACTED,
    _floor_metric_entries,
    _redact,
    study_add,
    study_new,
    thin_metric_lines,
)


def _snapshot(root: Path) -> set[tuple[str, bytes]]:
    """Every file under `root`, path plus bytes — the refuse-before-write
    review's own tool: a refusal whose bundle is byte-identical before and
    after proves nothing reached disk, where an exit-code assertion alone
    would pass a build that wrote first and refused second."""
    if not root.exists():
        return set()
    return {(str(p.relative_to(root)), p.read_bytes()) for p in root.rglob("*") if p.is_file()}


# --- Task 11: `study new` ---------------------------------------------------


def test_study_new_writes_title_authors_and_empty_runs_and_no_code_block(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--title", "Rank correlation methods"]) == EXIT_OK
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc == {"title": "Rank correlation methods", "authors": [], "runs": {}}
    assert "code" not in doc


def test_study_new_refuses_an_existing_study_yaml_and_writes_nothing(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--title", "First"]) == EXIT_OK
    before = _snapshot(bundle)
    assert main(["study", "new", str(bundle), "--title", "Second"]) == EXIT_WRONG
    assert _snapshot(bundle) == before
    # The original title survives — a refused second `study new` changed
    # nothing, not even the one file it might have "just updated".
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["title"] == "First"


def test_study_new_onto_a_bare_directory_with_no_study_yaml_succeeds(tmp_path: Path):
    """Mutation target (task 11 step 5): treating an existing DIRECTORY as
    'existing' would refuse here. `~/papers/x/study` beside a manuscript is
    a directory a person may well have made first."""
    bundle = tmp_path / "study"
    bundle.mkdir(parents=True)
    (bundle / "notes.txt").write_text("not a study.yaml")
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_OK
    assert (bundle / "study.yaml").exists()
    assert (bundle / "notes.txt").exists()


def test_study_new_refuses_inside_a_git_repo_and_writes_no_study_yaml(tmp_path: Path):
    """Mutation target (task 11 step 5): checking `E-STUDY-IN-REPO` AFTER
    writing would still exit non-zero here but leave `study.yaml` behind —
    caught by asserting its absence, not just the exit code."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    bundle = repo / "papers" / "study"
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_WRONG
    assert not (bundle / "study.yaml").exists()
    assert not bundle.exists()


def test_study_new_direct_call_raises_e_study_in_repo(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    bundle = repo / "study"
    with pytest.raises(ContractError) as exc_info:
        study_new(bundle, "Title")
    assert exc_info.value.code == "E-STUDY-IN-REPO"


def test_refuse_if_in_repo_propagates_any_other_contracterror_unexamined(
    tmp_path: Path, monkeypatch
):
    """Fix round 1, Minor 4: `_refuse_if_in_repo`'s docstring claims every
    `ContractError` OTHER than `E-GIT-NO-REPO` propagates unexamined — a
    safety claim with no fixture behind it before this. Pinned by making
    `find_repo_root` raise a differently-coded one."""
    import publishable.study as study_module

    def _boom(_path):
        raise ContractError("simulated failure", code="E-SOMETHING-ELSE")

    monkeypatch.setattr(study_module, "find_repo_root", _boom)
    bundle = tmp_path / "study"
    with pytest.raises(ContractError) as exc_info:
        study_new(bundle, "Title")
    assert exc_info.value.code == "E-SOMETHING-ELSE"


def test_study_new_direct_call_raises_e_study_exists(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "First")
    with pytest.raises(ContractError) as exc_info:
        study_new(bundle, "Second")
    assert exc_info.value.code == "E-STUDY-EXISTS"


def test_study_new_refuses_an_unrecognized_option_before_touching_disk(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle), "--titel", "Typo"]) == EXIT_INVOCATION
    assert not bundle.exists()


def test_study_new_refuses_missing_title_before_touching_disk(tmp_path: Path):
    bundle = tmp_path / "study"
    assert main(["study", "new", str(bundle)]) == EXIT_INVOCATION
    assert not bundle.exists()


def test_study_new_probe_arity_from_the_cli_table_test_writes_nothing_here():
    """The exact invocation `test_reference_cli_tables_match_what_the_cli_does`
    makes, run from inside this repository: two junk positionals and no
    `--title`, which must refuse before scaffolding anything into the
    working tree the way `generate template`'s own arity check protects
    against."""
    assert main(["study", "new", "_probe_a", "_probe_b"]) == EXIT_INVOCATION
    assert not Path("_probe_a").exists()


# --- Task 12: `study add` part 1 — the copy, the redaction, `code` --------


def _real_run(tmp_path: Path, subdir: str) -> dict:
    """One real, `git`-committed project, run end to end — the only way to
    get a genuine `provenance.git.commit`/`code_hash` pair. Each call gets
    its own subdirectory so `run_a_project`'s own scaffold-and-commit dance
    produces a distinct repo, and so a distinct commit, per call."""
    built = run_a_project(tmp_path / subdir)
    record = yaml.safe_load((built["run_dir"] / "run.yaml").read_text())
    return {"run_dir": built["run_dir"], "record": record}


def _fixture_y_record() -> dict:
    """Fixture Y: a record synthesized by hand, not one a real `run`
    produced — its only job is to exercise the `hostname` row of
    § What `study add` redacts, which nothing in this build writes
    (measured at `ebf642a`: `provenance.environment` is `{manager,
    python_version, uv_lock, uv_lock_hash}`). Every other field here is
    copied from a real record's shape so `read_record_file`'s own checks
    (a real `run_id`, this build's `schema_version`) pass, but the VALUES
    are hand-picked to exercise every redacted field at once.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2026-08-21T00-00-00Z_deadbee",
        "status": "completed",
        "draft": False,
        "config": {
            "data": {"input_dir": "/secure/cohort/input", "output_dir": "/secure/cohort/output"}
        },
        "parameters_hash": "1a2b",
        "code_hash": "8e21",
        "provenance": {
            "git": {"repo_root": "/home/klee/my-study", "commit": "abc123", "remote": None},
            "environment": {
                "manager": "uv",
                "python_version": "3.11.0",
                "hostname": "workstation-42.hospital.internal",
            },
            "input_manifest": "manifest/input.json",
            "input_manifest_hash": "3d8a",
            "apparatus": None,
        },
        "results": {"conditions": []},
    }


def _write_record(path: Path, record: dict) -> None:
    path.write_text(yaml.safe_dump(record, sort_keys=False))


def test_study_add_refuses_inside_a_git_repo_and_writes_nothing(tmp_path: Path):
    """Whole-branch review, Minor 8: `study add` enforces the same in-repo
    rule `study new` does, on the identical `_refuse_if_in_repo` call — a
    bundle assembled outside a repo and later enclosed by one (a `git
    init` above it, or a move) must not become writable again just
    because `study new` already ran. Checked BEFORE `_load_study_doc`, so
    no `study.yaml` needs to exist here at all — the same "nothing
    reached disk" shape `test_study_new_refuses_inside_a_git_repo_and_
    writes_no_study_yaml` pins for the sibling command."""
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    bundle = repo / "study"
    run = _real_run(tmp_path, "proj1")
    before = _snapshot(bundle)
    with pytest.raises(ContractError) as exc_info:
        study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert exc_info.value.code == "E-STUDY-IN-REPO"
    assert _snapshot(bundle) == before


def test_study_add_copies_the_record_and_updates_runs_in_study_yaml(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _real_run(tmp_path, "proj1")
    notices = study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert notices == []
    target = bundle / "main.run.yaml"
    assert target.exists()
    copied = yaml.safe_load(target.read_text())
    assert copied["run_id"] == run["record"]["run_id"]
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["runs"]["main"] == {"file": "main.run.yaml", "run_id": run["record"]["run_id"]}


def test_study_add_writes_code_commit_and_remote_from_the_first_add(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _real_run(tmp_path, "proj1")
    study_add(bundle, run["run_dir"] / "run.yaml", "main")
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    git = run["record"]["provenance"]["git"]
    assert doc["code"] == {"remote": git["remote"], "commit": git["commit"]}


def test_study_add_redacts_the_four_present_fields_but_keeps_every_hash(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _real_run(tmp_path, "proj1")
    study_add(bundle, run["run_dir"] / "run.yaml", "main")
    copied = yaml.safe_load((bundle / "main.run.yaml").read_text())
    assert copied["config"]["data"]["input_dir"] == REDACTED
    assert copied["config"]["data"]["output_dir"] == REDACTED
    assert copied["provenance"]["git"]["repo_root"] == REDACTED
    assert copied["provenance"]["input_manifest"] == REDACTED
    # Every hash stays, byte-equal to the source.
    record = run["record"]
    assert copied["code_hash"] == record["code_hash"]
    assert copied["parameters_hash"] == record["parameters_hash"]
    assert (
        copied["provenance"]["input_manifest_hash"] == record["provenance"]["input_manifest_hash"]
    )


def test_study_add_redaction_is_not_secrets_redact_field_replacement_only():
    """This is not `secrets.redact` — that matches credential VALUES by
    substring anywhere in a string; this replaces four known PATHS
    regardless of their value. A value that happens to contain a
    credential-looking substring elsewhere in the record is untouched."""
    record = _fixture_y_record()
    record["results"] = {"note": "the word repo_root appears nowhere else"}
    redacted = _redact(record)
    assert redacted["results"] == {"note": "the word repo_root appears nowhere else"}


def test_study_add_redacts_hostname_when_present_on_a_synthesized_record():
    """Fixture Y: the one row exercised only over a hand-built record,
    because nothing in this build writes `provenance.environment.hostname`
    today (it is H6's).

    H6b guard-pin arm S: sole authorized editor NONE for this body. Task 7
    edits `_fixture_y_record`'s docstring only, which is not a body edit and
    is not read as an arm edit."""
    record = _fixture_y_record()
    redacted = _redact(record)
    assert redacted["provenance"]["environment"]["hostname"] == REDACTED


def test_study_add_leaves_hostname_untouched_when_absent_from_the_source(tmp_path: Path):
    """Redaction must not INVENT `hostname` when the source lacks it.

    H6b guard-pin arm S: sole authorized editor NONE for this body. Task 7
    edits `_fixture_y_record`'s docstring only, which is not a body edit and
    is not read as an arm edit.

    EDITED 2026-08-23 by controller ruling, post-edit state specified in
    advance: the assertion is byte-identical and the property is unchanged;
    only the SOURCE of an absent-`hostname` record became explicit. This arm
    was captured when a real run wrote no `hostname` at all, and H6b task 3
    made real runs write one -- so the arm rested on a premise its own slice
    then falsified. Deleting the key here says outright what the fixture used
    to obtain by accident, which is what the arm was always testing: an
    absent key stays absent rather than becoming `<redacted by study add>`."""
    run = _real_run(tmp_path, "proj1")
    record = run["record"]
    del record["provenance"]["environment"]["hostname"]
    redacted = _redact(record)
    assert "hostname" not in redacted["provenance"]["environment"]


def test_study_add_redacts_hostname_but_leaves_os_and_hardware_end_to_end(tmp_path: Path):
    """H6b task 4, Fixture E, Ruling Q: `os` and `hardware` are NOT
    redacted; `hostname` is. Added BESIDE the hand-built Fixture Y
    (`test_study_add_redacts_hostname_when_present_on_a_synthesized_record`),
    never in place of it -- Fixture Y exercises every redacted field at
    once on a record nothing in this build yet writes; this fixture
    exercises the wiring against a key H6b task 3 made `run` actually
    write, end to end through a real bundle.

    The bundle sits under `tmp_path`, outside any repository -- `study new`
    and `study add` both refuse `E-STUDY-IN-REPO` otherwise. The SOURCE
    `run.yaml` is the positive control: comparing the bundled `os` and
    `hardware` against the value the same run actually produced means an
    implementation that writes nothing, or an empty string, fails both the
    equality and the truthiness/type assertions -- a bare `is not None`
    would pass on an empty string, which is why both live in one test."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _real_run(tmp_path, "proj1")
    source = run["record"]
    study_add(bundle, run["run_dir"] / "run.yaml", "main")
    bundled = yaml.safe_load((bundle / "main.run.yaml").read_text())

    assert bundled["provenance"]["environment"]["hostname"] == REDACTED
    assert bundled["provenance"]["environment"]["os"] == source["provenance"]["environment"]["os"]
    assert isinstance(bundled["provenance"]["environment"]["os"], str)
    assert bundled["provenance"]["environment"]["os"]
    assert (
        bundled["provenance"]["environment"]["hardware"]
        == source["provenance"]["environment"]["hardware"]
    )
    assert isinstance(bundled["provenance"]["environment"]["hardware"], dict)


def test_study_add_leaves_null_fields_exactly_null_not_marked_redacted():
    record = _fixture_y_record()
    record["config"]["data"]["output_dir"] = None
    redacted = _redact(record)
    assert redacted["config"]["data"]["output_dir"] is None


def test_apply_code_block_second_add_under_another_name_does_not_replace_and_notices(
    tmp_path: Path,
):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run1 = _real_run(tmp_path, "proj1")
    run2 = _real_run(tmp_path, "proj2")
    assert (
        run1["record"]["provenance"]["git"]["commit"]
        != run2["record"]["provenance"]["git"]["commit"]
    )
    study_add(bundle, run1["run_dir"] / "run.yaml", "main")
    notices = study_add(bundle, run2["run_dir"] / "run.yaml", "sensitivity")
    assert notices and notices[0][0] == "W-STUDY-COMMIT-MISMATCH"
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["code"]["commit"] == run1["record"]["provenance"]["git"]["commit"]


def test_apply_code_block_fixture_b_third_run_replaces_only_under_as_main(tmp_path: Path):
    """Fixture B: three real runs, three distinct commits, three distinct
    names (task 13's `E-STUDY-NAME-EXISTS` forbids reusing one). `aux`
    (the bundle's first add, so it sets `code.commit` regardless of its
    name), then `other` (neither the first add nor `--as main`, so it only
    notices a mismatch), then `main` (replaces). The mutation this
    discriminates (task 12 step 6, second mutation): recomputing
    `code.commit` as "the commit all runs share" has no answer over three
    pairwise-different commits, while the honest rule keeps exactly the
    `--as main` add's."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run1 = _real_run(tmp_path, "proj1")
    run2 = _real_run(tmp_path, "proj2")
    run3 = _real_run(tmp_path, "proj3")
    commits = {
        run1["record"]["provenance"]["git"]["commit"],
        run2["record"]["provenance"]["git"]["commit"],
        run3["record"]["provenance"]["git"]["commit"],
    }
    assert len(commits) == 3
    study_add(bundle, run1["run_dir"] / "run.yaml", "aux")
    study_add(bundle, run2["run_dir"] / "run.yaml", "other")
    study_add(bundle, run3["run_dir"] / "run.yaml", "main")
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["code"]["commit"] == run3["record"]["provenance"]["git"]["commit"]


# --- Task 13: `study add` part 2 — the duplicate-name refusal ------------


def test_study_add_refuses_a_name_already_in_study_yaml_before_any_write(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run1 = _real_run(tmp_path, "proj1")
    run2 = _real_run(tmp_path, "proj2")
    study_add(bundle, run1["run_dir"] / "run.yaml", "main")
    before = _snapshot(bundle)
    with pytest.raises(ContractError) as exc_info:
        study_add(bundle, run2["run_dir"] / "run.yaml", "main")
    assert exc_info.value.code == "E-STUDY-NAME-EXISTS"
    # M9's own arm: the file's bytes are unchanged — an overwrite of the
    # same name would have replaced `main.run.yaml`'s content.
    assert _snapshot(bundle) == before


def test_study_add_refuses_a_name_whose_file_exists_even_if_study_yaml_was_hand_edited(
    tmp_path: Path,
):
    """Second discriminating mutation (task 13 step 4): checking only
    `study.yaml`'s keys, not the file, would miss this — the entry was
    hand-edited away while the file remains."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run1 = _real_run(tmp_path, "proj1")
    run2 = _real_run(tmp_path, "proj2")
    study_add(bundle, run1["run_dir"] / "run.yaml", "main")
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    del doc["runs"]["main"]
    (bundle / "study.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    before = _snapshot(bundle)
    with pytest.raises(ContractError) as exc_info:
        study_add(bundle, run2["run_dir"] / "run.yaml", "main")
    assert exc_info.value.code == "E-STUDY-NAME-EXISTS"
    assert _snapshot(bundle) == before


def test_study_add_permits_the_same_run_id_under_two_different_names(tmp_path: Path):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _real_run(tmp_path, "proj1")
    study_add(bundle, run["run_dir"] / "run.yaml", "main")
    study_add(bundle, run["run_dir"] / "run.yaml", "again")
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert (
        doc["runs"]["main"]["run_id"] == doc["runs"]["again"]["run_id"] == run["record"]["run_id"]
    )


def test_study_add_through_main_end_to_end(tmp_path: Path):
    bundle = tmp_path / "study"
    run = _real_run(tmp_path, "proj1")
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_OK
    assert main(
        ["study", "add", str(bundle), str(run["run_dir"] / "run.yaml"), "--as", "main"]
    ) == (EXIT_OK)
    doc = yaml.safe_load((bundle / "study.yaml").read_text())
    assert doc["runs"]["main"]["run_id"] == run["record"]["run_id"]


def test_study_add_through_main_refuses_a_duplicate_name_at_exit_1(tmp_path: Path):
    bundle = tmp_path / "study"
    run = _real_run(tmp_path, "proj1")
    main(["study", "new", str(bundle), "--title", "Title"])
    main(["study", "add", str(bundle), str(run["run_dir"] / "run.yaml"), "--as", "main"])
    before = _snapshot(bundle)
    assert (
        main(["study", "add", str(bundle), str(run["run_dir"] / "run.yaml"), "--as", "main"])
        == EXIT_WRONG
    )
    assert _snapshot(bundle) == before


def test_study_add_arity_probe_from_the_cli_table_test_writes_nothing():
    """The exact invocation `test_reference_cli_tables_match_what_the_cli_does`
    makes for a `built` row: two junk positionals, no `--as`, so the
    arity/`--as` check must refuse before `study_add` ever reads a path."""
    assert main(["study", "add", "_probe_a", "_probe_b"]) == EXIT_INVOCATION
    assert not Path("_probe_a").exists()


def test_study_group_with_no_subcommand_names_both_subcommands_at_exit_2(capsys):
    """Pinned to the exact message rather than to bare substrings of
    `"new"`/`"add"` — fix round 1's Minor 5: those two words are
    substrings of many plausible rewordings and so barely discriminate on
    their own."""
    assert main(["study"]) == EXIT_INVOCATION
    err = capsys.readouterr().err
    assert err == (
        "`publishable study` needs a subcommand: `new` or `add` — see "
        "docs/reference.md § Creation commands\n"
    )


def test_study_group_with_an_unrecognized_subcommand_is_a_usage_error(capsys):
    assert main(["study", "frobnicate"]) == EXIT_INVOCATION
    err = capsys.readouterr().err
    assert "unknown command" not in err
    assert "is specified but not built" not in err


# --- Task 14: the `min_reported_n` prompt --------------------------------


def _fixture_n_run(tmp_path: Path) -> dict:
    """Fixture N: a real run with `statistics.report_by: [cohort]` over 12
    units — the whole-condition metric completes all 12 (above the
    default `min_reported_n: 10`), while each `cohort` level (`a`/`b`)
    completes 6 (below it). Computed, not guessed: `run_a_project`'s
    roster alternates `cohort` a/b, so 12 units split 6/6."""
    built = run_a_project(
        tmp_path,
        unit_attributes=["cohort"],
        units=12,
        statistics={"report_by": ["cohort"]},
        aggregate_returns="metric",
    )
    record = yaml.safe_load((built["run_dir"] / "run.yaml").read_text())
    return {"run_dir": built["run_dir"], "record": record}


def test_thin_metric_lines_is_empty_when_nothing_is_thin(tmp_path: Path):
    run = _real_run(tmp_path, "proj1")
    assert thin_metric_lines(run["record"], 10) == []


def test_thin_metric_lines_fixture_n_lists_only_the_thin_strata_a_proper_subset(
    tmp_path: Path,
):
    """M7's own discriminator: listing every metric would include the
    whole-condition `pred`/`metric` entries (`n.completed: 12`, at or
    above the floor); the honest rule lists only the `by[cohort=a]` and
    `by[cohort=b]` entries (`n.completed: 6`, below it) — a PROPER subset
    of "every metric", not all of them."""
    run = _fixture_n_run(tmp_path)
    lines = thin_metric_lines(run["record"], 10)
    assert len(lines) == 4  # {pred, metric} x {a, b}
    assert all("by[cohort=" in line for line in lines)
    assert not any("condition 0.aggregated.step01_summarize_units.pred:" == line for line in lines)


def test_thin_metric_lines_reported_estimate_with_no_n_is_listed_unconditionally():
    """Nested by STEP NAME then metric, matching `run_record.py`'s own
    producer (`summary[e.step_name] = summary_values(r.returned)`) —
    `results.summary` is never keyed by metric name directly. A hand-built
    fixture at the wrong nesting is exactly how B7's own review caught
    Decision 13's second branch dead on every real record: it agrees with
    the bug it exists to pin."""
    record = _fixture_y_record()
    record["results"] = {
        "summary": {
            "step02_report": {
                "site_effect": {"value": 0.3, "reported": True, "ci95": [0.1, 0.5], "n": None}
            }
        }
    }
    lines = thin_metric_lines(record, 10)
    assert any("declares no n" in line for line in lines)


def test_thin_metric_lines_reported_estimate_below_floor_is_listed():
    record = _fixture_y_record()
    record["results"] = {
        "summary": {
            "step02_report": {
                "site_effect": {"value": 0.3, "reported": True, "ci95": [0.1, 0.5], "n": 4}
            }
        }
    }
    lines = thin_metric_lines(record, 10)
    assert any("reported n=4" in line for line in lines)


def test_thin_metric_lines_basis_repeats_synthesized_is_compared_against_repeat_count():
    """Nothing in this build writes `basis: "repeats"` (filed in
    `docs/superpowers/spec-defects.md`) — exercised only over this
    hand-built entry, nested by step name then metric to match
    `run_record.py`'s own producer shape (fix round 1: the original
    fixture sat one level too shallow, at the same wrong nesting the
    `reported: true` fixtures above did)."""
    record = _fixture_y_record()
    record["results"] = {
        "summary": {
            "step02_report": {
                "slow_metric": {
                    "value": 1.2,
                    "basis": "repeats",
                    "repeat_spread": {"std": 0.1, "n": 3, "kind": "seed"},
                }
            }
        }
    }
    lines = thin_metric_lines(record, 10)
    assert any("repeat count=3" in line for line in lines)


_SUMMARY_ESTIMATES_STEP = """\
from publishable import BaseStep
from publishable.estimate import Estimate


class Step(BaseStep):
    scope = "summary"

    def run(self, cfg, io):
        return {{
            "site_adjusted_delta": Estimate(
                value=0.041, ci95=(0.012, 0.070), n=4, method="mixed_model"
            ),
            "no_denominator": Estimate(value=0.5, ci95=(0.1, 0.9), n=None, method="hand"),
        }}
"""


def test_thin_metric_lines_finds_reported_estimates_on_a_real_run(tmp_path: Path):
    """The real-run pin for Critical 1 (fix round 1): a genuine `summary`
    step returning two `Estimate`s — one below the floor, one declaring no
    `n` at all — through an actual `run`, never a hand-built record. Before
    the fix, `results.summary` nested by STEP NAME
    (`run_record.py`'s `summary[e.step_name] = summary_values(r.returned)`)
    made every `reported: true` entry invisible to a walker that read one
    level short, and `thin_metric_lines` returned `[]` here."""
    built = run_a_project(
        tmp_path, extra_steps=["report"], extra_step_source=_SUMMARY_ESTIMATES_STEP
    )
    record = yaml.safe_load((built["run_dir"] / "run.yaml").read_text())
    summary = record["results"]["summary"]
    assert set(summary) == {"step02_report"}  # nested by step name, not by metric
    lines = thin_metric_lines(record, 10)
    assert any("reported n=4" in line for line in lines)
    assert any("declares no n" in line for line in lines)


def test_thin_metric_lines_vs_baseline_contrast_entry_is_not_silently_skipped(tmp_path: Path):
    """The disclosure risk Decision 13's own *Cost if wrong* names: a
    contrast entry has no `n` mapping at all (it carries `n_paired`, or
    `n_of`/`n_against`), so a walker that only reads `entry["n"]["completed"]`
    would silently skip every `vs_baseline` and declared-contrast entry."""
    record = _fixture_y_record()
    record["results"] = {
        "conditions": [
            {
                "index": 0,
                "label": "b",
                "vs_baseline": {
                    "step01": {
                        "metric": {
                            "delta": 0.1,
                            "basis": "units",
                            "paired": True,
                            "n_paired": 3,
                            "method": "paired_t_over_units",
                            "ci95": [0.0, 0.2],
                            "cohens_d": None,
                            "correction": None,
                        }
                    }
                },
            }
        ]
    }
    lines = thin_metric_lines(record, 10)
    assert any("n_paired=3" in line for line in lines)


def test_thin_metric_lines_unpaired_contrast_either_side_below_floor(tmp_path: Path):
    record = _fixture_y_record()
    record["results"] = {
        "contrasts": [
            {
                "id": "c1",
                "of": "b",
                "against": "a",
                "step01": {
                    "metric": {
                        "delta": 0.1,
                        "basis": "units",
                        "paired": False,
                        "n_of": 3,
                        "n_against": 40,
                        "method": "welch_t_over_units",
                        "ci95": [0.0, 0.2],
                        "cohens_ds": None,
                        "correction": None,
                    }
                },
            }
        ]
    }
    lines = thin_metric_lines(record, 10)
    assert any("n_of=3" in line for line in lines)
    assert not any("n_against" in line for line in lines)


def test_study_add_proceeds_when_confirmed_at_a_tty(tmp_path: Path, monkeypatch):
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _fixture_n_run(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    notices = study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert notices == []
    assert (bundle / "main.run.yaml").exists()


def test_study_add_writes_nothing_when_quit_at_a_tty(tmp_path: Path, monkeypatch, capsys):
    """Fix round 1, Minor 3: quitting exits `0` (a judgment call, not a
    refusal) but must say so — otherwise a quit and a completed add are
    indistinguishable from the terminal alone."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _fixture_n_run(tmp_path)
    before = _snapshot(bundle)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    notices = study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert notices == []
    assert _snapshot(bundle) == before
    assert not (bundle / "main.run.yaml").exists()
    assert "Quit — nothing was added to the bundle." in capsys.readouterr().out


def test_study_add_refuses_with_no_tty_and_writes_nothing(tmp_path: Path, monkeypatch, capsys):
    """M8's own discriminator: asserting only the raised code would pass a
    build that refused AFTER copying — this asserts the bundle holds no
    new file too. Fix round 1, Minor 6: § Errors' `E-STUDY-CONFIRM-
    REQUIRED` row promises "prints the offending metrics before
    refusing" — unpinned before this; the four `n.completed=6 < 10` lines
    must reach STDOUT even though the refusal itself lands on stderr
    (through `main`'s own `except PublishableError`)."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _fixture_n_run(tmp_path)
    before = _snapshot(bundle)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(ContractError) as exc_info:
        study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert exc_info.value.code == "E-STUDY-CONFIRM-REQUIRED"
    assert _snapshot(bundle) == before
    assert not (bundle / "main.run.yaml").exists()
    printed = capsys.readouterr().out
    assert "The following reported metrics fall below" in printed
    assert printed.count("n.completed=6 < 10") == 4


def test_study_add_uses_the_bundled_records_own_floor_not_a_cwd_config(tmp_path: Path, monkeypatch):
    """M12's own discriminator: a working-directory config declaring a
    much LOWER floor (1, versus the record's own 10) must not change the
    answer. With no TTY attached, the two floors give different verdicts
    on the identical `by`-stratum data (6 units each): the record's floor
    of 10 finds them thin and refuses; a wrongly-consulted cwd floor of 1
    would find nothing thin and proceed to write. So this asserts the
    REFUSAL — proceeding here would mean the cwd config won."""
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    run = _fixture_n_run(tmp_path)
    # A config in the CURRENT directory declaring a much lower floor —
    # `study_add` must never consult it.
    cwd_config = tmp_path / "cwd_config.yaml"
    cwd_config.write_text(yaml.safe_dump({"limits": {"min_reported_n": 1}}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    with pytest.raises(ContractError) as exc_info:
        study_add(bundle, run["run_dir"] / "run.yaml", "main")
    assert exc_info.value.code == "E-STUDY-CONFIRM-REQUIRED"
    assert not (bundle / "main.run.yaml").exists()


def test_study_new_add_report_join_through_main_end_to_end(tmp_path: Path, capsys):
    """Task 14 step 7: the join no other batch owns. Task 10 renders
    bundles Fixture B hand-builds; tasks 11-14 write bundles nothing
    renders. This is the one end-to-end arm that closes the loop —
    `study new`, `study add` twice, `report <study.yaml>`, all through
    `main`.

    Exit `0` alone passes identically if the render produced nothing
    (B7's own review mandate names this shape), so this asserts the
    rendered text names BOTH runs — `## main` and `## sensitivity`,
    `_bundle_header_section`'s own heading, one per bundled member — and
    that each carries its own `run_id`, not a shared or empty one."""
    bundle = tmp_path / "study"
    run1 = _real_run(tmp_path, "proj1")
    run2 = _real_run(tmp_path, "proj2")
    assert main(["study", "new", str(bundle), "--title", "Title"]) == EXIT_OK
    assert (
        main(["study", "add", str(bundle), str(run1["run_dir"] / "run.yaml"), "--as", "main"])
        == EXIT_OK
    )
    assert (
        main(
            ["study", "add", str(bundle), str(run2["run_dir"] / "run.yaml"), "--as", "sensitivity"]
        )
        == EXIT_OK
    )
    capsys.readouterr()  # discard the two `study add` invocations' own output
    assert main(["report", str(bundle / "study.yaml")]) == EXIT_OK
    out = capsys.readouterr().out
    assert "## main" in out
    assert "## sensitivity" in out
    assert f"run_id: {run1['record']['run_id']}" in out
    assert f"run_id: {run2['record']['run_id']}" in out


# --- H5b task 14: `study`'s thin-metric floor sees the same four entries ---


def test_fixture_j_the_floor_walk_sees_exactly_four_metric_entries(tmp_path: Path):
    """H5b task 14, step 2. `study.py`'s `_floor_metric_entries` — grepped
    and read (`grep -n '_floor_metric_entries' src/publishable/study.py`,
    two hits: its definition and its one caller in `study_add`) — walks a
    record's `results.conditions[].aggregated` structurally via
    `_is_thin_checkable_entry` (`basis` present, or `reported is True`),
    never by a key's name. Fixture J's own record has exactly one
    condition and no `vs_baseline`/`contrasts`/`summary`, so the walk's
    only source is that one condition's `aggregated.step01_summarize_units`
    block: `n_rows`, `n_valid`, `mean_score` (each `basis: units`, derived)
    and `score` (`basis: units`, a recorded column with a contributing
    count of 4). `valid` is non-numeric for every unit and earns no block
    at all (Ruling 1's first row), so it cannot appear here either —
    exactly the four entries `report`'s own table shows (Fixture J, step
    1), no fifth.

    Verified through the real `study add` path (Fixture J's `run.yaml`
    added to a bundle with `--as`), not by hand-building a record: a
    string wearing a metric block's shape (`{"basis": "units", ...}`) would
    structurally enter this walk the same way a genuine one does, so the
    read has to come from what a real run actually wrote.
    """
    bundle = tmp_path / "study"
    study_new(bundle, "Title")
    built = _fixture_j_run(tmp_path)
    assert (
        main(["study", "add", str(bundle), str(built["run_dir"] / "run.yaml"), "--as", "main"])
        == EXIT_OK
    )
    record = yaml.safe_load((bundle / "main.run.yaml").read_text())
    entries = _floor_metric_entries(record)
    names = {label.rsplit(".", 1)[-1] for label, _ in entries}
    assert names == {"n_rows", "n_valid", "mean_score", "score"}
    assert len(entries) == 4

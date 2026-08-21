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

from publishable.cli import main
from publishable.diagnostics import EXIT_INVOCATION, EXIT_OK, EXIT_WRONG
from publishable.errors import ContractError
from publishable.run_record import SCHEMA_VERSION
from publishable.study import REDACTED, _redact, study_add, study_new


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
    today (it is H6's)."""
    record = _fixture_y_record()
    redacted = _redact(record)
    assert redacted["provenance"]["environment"]["hostname"] == REDACTED


def test_study_add_leaves_hostname_untouched_when_absent_from_the_source(tmp_path: Path):
    """The real-run counterpart of the fixture above: today's real records
    never carry `hostname` at all, and redaction must not invent the key."""
    run = _real_run(tmp_path, "proj1")
    redacted = _redact(run["record"])
    assert "hostname" not in redacted["provenance"]["environment"]


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
    assert main(["study"]) == EXIT_INVOCATION
    err = capsys.readouterr().err
    assert "unknown command" not in err
    assert "is specified but not built" not in err
    assert "new" in err
    assert "add" in err


def test_study_group_with_an_unrecognized_subcommand_is_a_usage_error(capsys):
    assert main(["study", "frobnicate"]) == EXIT_INVOCATION
    err = capsys.readouterr().err
    assert "unknown command" not in err
    assert "is specified but not built" not in err

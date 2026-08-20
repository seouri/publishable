"""`read_run_record` — the `run.yaml` reader `lineage.py` gives H8a, tested against
synthesized records for each refusal and against a genuinely produced one (Fixture R),
per `docs/superpowers/plans/2026-08-20-lineage.md` task 1 and
`docs/superpowers/specs/2026-08-20-lineage-design.md` § 3.
"""

from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.errors import ContractError
from publishable.lineage import read_run_record, resolve_run, resolve_step
from publishable.run_record import SCHEMA_VERSION
from publishable.sweep import condition_dir_name


def _write_run_yaml(run_dir: Path, doc: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.yaml").write_text(yaml.safe_dump(doc))


def test_no_run_yaml_at_all_is_record_missing(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"


def test_a_path_that_is_not_a_run_directory_at_all_is_record_missing(tmp_path: Path):
    # No directory exists here at all, which is the same fault as an empty one: no
    # run.yaml is at the resolved path either way.
    with pytest.raises(ContractError) as e:
        read_run_record(tmp_path / "never_created")
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"


def test_invalid_yaml_is_record_unreadable(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    (run_dir / "run.yaml").write_text("schema_version: 1.0\nrun_id: [unterminated\n")
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"


def test_a_yaml_document_that_is_not_a_mapping_is_record_unreadable(tmp_path: Path):
    """Shares its code with `test_a_mapping_with_no_run_id_is_record_unreadable` below,
    so the code alone does not pin this fault: a mutant that deletes the `isinstance`
    guard falls through to `"run_id" not in doc`, which is `True` for a list too, and
    raises the SAME code from the OTHER site. The message text is what tells the two
    faults apart (`CLAUDE.md`'s one-code-several-faults lesson, one level below the
    code split H4d made).
    """
    run_dir = tmp_path / "run_x"
    run_dir.mkdir()
    (run_dir / "run.yaml").write_text("- just\n- a\n- list\n")
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"
    assert "did not parse to a mapping" in str(e.value)


def test_a_mapping_with_no_run_id_is_record_unreadable(tmp_path: Path):
    """Shares its code with the not-a-mapping test above — see that docstring for why
    the message is asserted rather than the code alone."""
    run_dir = tmp_path / "run_x"
    _write_run_yaml(run_dir, {"schema_version": SCHEMA_VERSION, "status": "completed"})
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"
    assert "has no `run_id`" in str(e.value)


def test_a_schema_version_this_build_does_not_read_is_record_version(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    _write_run_yaml(
        run_dir,
        {"schema_version": "99.9", "run_id": "run_2020-01-01T00-00-00Z_abcdef1"},
    )
    with pytest.raises(ContractError) as e:
        read_run_record(run_dir)
    assert e.value.code == "E-UPSTREAM-RECORD-VERSION"


def test_a_valid_synthesized_record_reads_back_the_parsed_mapping(tmp_path: Path):
    run_dir = tmp_path / "run_x"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_abcdef1",
        "status": "completed",
    }
    _write_run_yaml(run_dir, doc)
    assert read_run_record(run_dir) == doc


@pytest.mark.parametrize("status", ["partial", "failed"])
def test_a_partial_or_failed_record_is_not_refused_here(tmp_path: Path, status: str):
    """A partial or failed run's completed step wrote a real artifact; refusing the
    whole record on a sibling condition's failure would make that artifact unreadable
    for a reason unrelated to it. The named step's own status is a later task's check.
    """
    run_dir = tmp_path / "run_x"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_abcdef1",
        "status": status,
    }
    _write_run_yaml(run_dir, doc)
    assert read_run_record(run_dir) == doc


def test_fixture_r_a_real_run_yaml_reads_back_what_the_writer_wrote(tmp_path: Path):
    """Fixture R. `run_a_project` drives a genuine run through `main(["run", ...])`;
    `schema_version` and `run_id` are read back from the produced file rather than
    asserted as literals, so this pins that the reader reads what the writer wrote
    rather than pinning a value that happens to match today.
    """
    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=8)
    run_dir = doc["run_dir"]
    on_disk = yaml.safe_load((run_dir / "run.yaml").read_text())
    record = read_run_record(run_dir)
    assert record["schema_version"] == on_disk["schema_version"]
    assert record["run_id"] == on_disk["run_id"]
    assert record == on_disk


def _write_upstream(run_dir: Path, run_id: str, execution: dict | None = None) -> dict:
    doc: dict = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "status": "completed"}
    if execution is not None:
        doc["execution"] = execution
    _write_run_yaml(run_dir, doc)
    return doc


# ---------------------------------------------------------------------------
# Task 2 — resolve_run: Fixture L (the two locator forms, and the mismatch)
# ---------------------------------------------------------------------------


def test_relative_form_resolves_under_output_dir_and_reads(tmp_path: Path):
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_aaaaaaa"
    _write_upstream(output_dir / run_id, run_id)
    repo_root = tmp_path / "unused_repo_root"
    resolved, record = resolve_run(run_id, output_dir=output_dir, repo_root=repo_root)
    assert resolved == (output_dir / run_id).resolve()
    assert record["run_id"] == run_id


def test_absolute_form_on_a_moved_directory_reads_the_records_own_id(tmp_path: Path):
    """Fixture L's absolute arm. The copied directory's own name (`moved_run`) must
    play no part in what is returned: the recorded `run_id` is read from the
    record, never parsed from the directory's basename. Asserted on the RAW
    rendered text (`yaml.safe_dump`), not a parsed structure, per the design's
    "a defect that lives in how a value is written can be normalised away by the
    reader" rule.
    """
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_bbbbbbb"
    moved = tmp_path / "elsewhere" / "moved_run"
    _write_upstream(moved, run_id)
    repo_root = tmp_path / "unused_repo_root"
    resolved, record = resolve_run(str(moved), output_dir=output_dir, repo_root=repo_root)
    assert resolved == moved.resolve()
    assert record["run_id"] == run_id
    assert "moved_run" not in yaml.safe_dump(record)


def test_output_dir_latest_via_absolute_form_reads_through_the_symlink(tmp_path: Path):
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_ccccccc"
    run_dir = output_dir / run_id
    _write_upstream(run_dir, run_id)
    latest = output_dir / "latest"
    latest.symlink_to(run_dir.name)
    repo_root = tmp_path / "unused_repo_root"
    resolved, record = resolve_run(str(latest), output_dir=output_dir, repo_root=repo_root)
    assert resolved == run_dir.resolve()
    assert record["run_id"] == run_id


def test_output_dir_latest_via_relative_form_is_runid_mismatch(tmp_path: Path):
    """Decision 1's named asymmetry: `latest` is a path, not a `run_id`, and the
    relative form compares the locator AS GIVEN — never a resolved basename,
    which would agree with the record and let the mismatch die silently.
    """
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_ddddddd"
    run_dir = output_dir / run_id
    _write_upstream(run_dir, run_id)
    latest = output_dir / "latest"
    latest.symlink_to(run_dir.name)
    repo_root = tmp_path / "unused_repo_root"
    with pytest.raises(ContractError) as e:
        resolve_run("latest", output_dir=output_dir, repo_root=repo_root)
    assert e.value.code == "E-UPSTREAM-RUNID-MISMATCH"


def test_a_renamed_run_directory_disagrees_with_its_own_record(tmp_path: Path):
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_eeeeeee"
    real_dir = output_dir / run_id
    _write_upstream(real_dir, run_id)
    renamed = output_dir / "run_renamed"
    real_dir.rename(renamed)
    repo_root = tmp_path / "unused_repo_root"
    with pytest.raises(ContractError) as e:
        resolve_run("run_renamed", output_dir=output_dir, repo_root=repo_root)
    assert e.value.code == "E-UPSTREAM-RUNID-MISMATCH"


def test_a_relative_locator_with_a_separator_is_upstream_locator(tmp_path: Path):
    """The two forms are told apart by `Path(locator).is_absolute()` alone. A
    relative locator with a separator is neither form — asserting the specific
    code (not merely "it raises") is what catches a mutant that instead tells
    the forms apart by looking for a separator: such a mutant would route this
    locator into the absolute-form branch, since it contains one, and raise a
    different code (or read a different path) rather than `E-UPSTREAM-LOCATOR`.
    """
    output_dir = tmp_path / "results"
    repo_root = tmp_path / "unused_repo_root"
    with pytest.raises(ContractError) as e:
        resolve_run("sub/dir", output_dir=output_dir, repo_root=repo_root)
    assert e.value.code == "E-UPSTREAM-LOCATOR"


# ---------------------------------------------------------------------------
# Task 2 — resolve_run: Fixture C (the containment guard, with its control)
# ---------------------------------------------------------------------------


def test_containment_guard_refuses_an_upstream_inside_the_downstream_repo(tmp_path: Path):
    project = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=8)
    root = project["root"]
    output_dir = tmp_path / "results_unused_for_this_call"
    run_id = "run_2020-01-01T00-00-00Z_fffffff"
    inside = root / "upstream_inside"
    _write_upstream(inside, run_id)
    with pytest.raises(ContractError) as e:
        resolve_run(str(inside), output_dir=output_dir, repo_root=root)
    assert e.value.code == "E-UPSTREAM-REPO-CONTAINED"


def test_containment_guard_control_reads_when_moved_outside_the_repo(tmp_path: Path):
    """The control: the identical shape, moved one level above the repo root. A
    control asserting only an absence passes identically if nothing ran, so this
    asserts a genuine, successful read.
    """
    project = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=8)
    root = project["root"]
    output_dir = tmp_path / "results_unused_for_this_call"
    run_id = "run_2020-01-01T00-00-00Z_ggggggg"
    outside = tmp_path / "outside_run"
    _write_upstream(outside, run_id)
    resolved, record = resolve_run(str(outside), output_dir=output_dir, repo_root=root)
    assert resolved == outside.resolve()
    assert record["run_id"] == run_id


# ---------------------------------------------------------------------------
# Task 4 — resolve_step: Fixture S (the scope refusal, built so the mutant
# succeeds)
# ---------------------------------------------------------------------------


def _execution_with_all_scopes() -> dict:
    return {
        "shared": {"step_shared": {"status": "completed"}},
        "summary": {"step_summary": {"status": "completed"}},
        "conditions": [
            {
                "index": 0,
                "label": "cond_a",
                "steps": {"step_cond": {"status": "completed"}},
            }
        ],
    }


def test_a_condition_scoped_step_is_refused_even_though_its_artifact_exists(tmp_path: Path):
    """The condition-scoped artifact genuinely exists on disk, at the location a
    mutant resolving into the condition directory would find it — without that,
    a test asserting only "it raises" would pass a mutant that succeeds.
    """
    run_dir = tmp_path / "upstream"
    doc = _write_upstream(
        run_dir, "run_2020-01-01T00-00-00Z_hhhhhhh", execution=_execution_with_all_scopes()
    )
    cond_dir = run_dir / "conditions" / condition_dir_name(0, "cond_a") / "step_cond"
    cond_dir.mkdir(parents=True)
    (cond_dir / "out.json").write_text('{"x": 1}')
    with pytest.raises(ContractError) as e:
        resolve_step(doc, run_dir, "step_cond")
    assert e.value.code == "E-UPSTREAM-STEP-SCOPED"


def test_a_step_absent_from_the_execution_block_is_step_unknown(tmp_path: Path):
    """A fallback to `shared/` for an absent step would find something to read
    here, so the fixture writes bait at exactly that location.
    """
    run_dir = tmp_path / "upstream"
    doc = _write_upstream(
        run_dir, "run_2020-01-01T00-00-00Z_iiiiiii", execution=_execution_with_all_scopes()
    )
    absent_dir = run_dir / "shared" / "step_absent"
    absent_dir.mkdir(parents=True)
    (absent_dir / "x.json").write_text('{"y": 2}')
    with pytest.raises(ContractError) as e:
        resolve_step(doc, run_dir, "step_absent")
    assert e.value.code == "E-UPSTREAM-STEP-UNKNOWN"


def test_a_present_but_incomplete_step_is_step_incomplete(tmp_path: Path):
    """The failed step's artifact exists on disk too, so a mutant that skips the
    `status == "completed"` check would return it rather than raise.
    """
    run_dir = tmp_path / "upstream"
    execution = {
        "shared": {"step_failed": {"status": "failed"}},
        "summary": {},
        "conditions": [],
    }
    doc = _write_upstream(run_dir, "run_2020-01-01T00-00-00Z_jjjjjjj", execution=execution)
    failed_dir = run_dir / "shared" / "step_failed"
    failed_dir.mkdir(parents=True)
    (failed_dir / "out.json").write_text('{"z": 3}')
    with pytest.raises(ContractError) as e:
        resolve_step(doc, run_dir, "step_failed")
    assert e.value.code == "E-UPSTREAM-STEP-INCOMPLETE"


def test_a_run_scoped_and_summary_scoped_step_resolve_to_shared_and_summary(tmp_path: Path):
    """Decision 4's positive path: the only two addressable locations."""
    run_dir = tmp_path / "upstream"
    doc = _write_upstream(
        run_dir, "run_2020-01-01T00-00-00Z_kkkkkkk", execution=_execution_with_all_scopes()
    )
    assert resolve_step(doc, run_dir, "step_shared") == run_dir / "shared" / "step_shared"
    assert resolve_step(doc, run_dir, "step_summary") == run_dir / "summary" / "step_summary"

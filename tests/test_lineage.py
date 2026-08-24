"""`read_run_record` — the `run.yaml` reader `lineage.py` gives H8a, tested against
synthesized records for each refusal and against a genuinely produced one (Fixture R),
per `docs/superpowers/plans/2026-08-20-lineage.md` task 1 and
`docs/superpowers/specs/2026-08-20-lineage-design.md` § 3.
"""

import dataclasses
import json
import subprocess
from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.artifacts import StepIO
from publishable.diagnostics import EXIT_PARTIAL
from publishable.errors import ContractError
from publishable.lineage import (
    UpstreamLedger,
    UpstreamResolver,
    read_record_file,
    read_run_record,
    resolve_run,
    resolve_step,
)
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
    record, never parsed from the directory's basename.
    """
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_bbbbbbb"
    moved = tmp_path / "elsewhere" / "moved_run"
    _write_upstream(moved, run_id)
    repo_root = tmp_path / "unused_repo_root"
    resolved, record = resolve_run(str(moved), output_dir=output_dir, repo_root=repo_root)
    assert resolved == moved.resolve()
    assert record["run_id"] == run_id


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
    # Minor 2 (task-b2-review.md): the message carries a `latest`-specific clause
    # that is a non-sequitur for the OTHER fault sharing this code (a renamed
    # directory, below) — assert the text here so a message that drops the
    # clause, or attaches it to the wrong fault, is caught.
    assert "`latest` is a path" in str(e.value)


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
    # Minor 2: this fault is not about `latest` at all — the message's `latest`
    # clause must not appear here, and its own clause must.
    assert "`latest`" not in str(e.value)
    assert "own run_id" in str(e.value)


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


def test_containment_guard_uses_the_callers_repo_root_not_a_walk_up_from_the_upstream(
    tmp_path: Path,
):
    """Major 1 (task-b2-review.md). The mutation this fixture exists to catch —
    re-deriving `repo_root` by walking up from the upstream path instead of using
    the caller's own — is NOT caught by the two fixtures above: `tmp_path` on this
    machine sits under no `.git` at all, so that mutation only crashes with
    `E-GIT-NO-REPO` there rather than misclassifying anything (see the batch's own
    report and the review's Major 1 for that measurement).

    The property "the question is answered with the caller's `repo_root`, never a
    walk-up from the upstream" needs an upstream that DOES sit inside a real git
    repo of its own — one that is not the downstream's. Correct code reads it
    (the caller's `repo_root` does not contain it); a mutant that re-derives
    `repo_root` from the upstream path finds that sibling repo's own `.git` and
    wrongly refuses it with `E-UPSTREAM-REPO-CONTAINED`.
    """
    downstream_repo_root = tmp_path / "downstream_repo"
    downstream_repo_root.mkdir()
    other_repo = tmp_path / "other_repo"
    other_repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=other_repo, check=True)
    run_id = "run_2020-01-01T00-00-00Z_lllllll"
    upstream = other_repo / "up"
    _write_upstream(upstream, run_id)
    output_dir = tmp_path / "results_unused_for_this_call"
    resolved, record = resolve_run(
        str(upstream), output_dir=output_dir, repo_root=downstream_repo_root
    )
    assert resolved == upstream.resolve()
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


def test_a_repeat_scoped_step_nested_under_its_repeat_label_is_also_refused(tmp_path: Path):
    """Minor 5 (task-b2-review.md). `run_record._execution_block` writes a
    REPEAT-scoped step's entry nested one level further than a condition-scoped
    one: `cond["steps"][step] = {repeat_label: entry}`, not a bare entry — the
    shape `_execution_with_all_scopes` above never instantiates. Membership in
    `conditions` is still the whole test, so the same refusal fires regardless of
    what sits inside `steps[step]`.
    """
    run_dir = tmp_path / "upstream"
    execution = {
        "shared": {},
        "summary": {},
        "conditions": [
            {
                "index": 0,
                "label": "cond_a",
                "steps": {"step_repeat": {"seed47": {"status": "completed"}}},
            }
        ],
    }
    doc = _write_upstream(run_dir, "run_2020-01-01T00-00-00Z_mmmmmmm", execution=execution)
    with pytest.raises(ContractError) as e:
        resolve_step(doc, run_dir, "step_repeat")
    assert e.value.code == "E-UPSTREAM-STEP-SCOPED"


# ---------------------------------------------------------------------------
# spec-defects.md: "resolve_run's relative form skips the repo-containment
# check" (owner: H8a tasks 3 and 5) — closed here, on `resolve_run` itself.
# ---------------------------------------------------------------------------


def test_relative_form_containment_refuses_a_symlink_under_output_dir_into_the_repo(
    tmp_path: Path,
):
    """The gap `task-b2-review.md` Minor 8 found: the relative form exempted
    itself from `resolves_inside_repo` entirely, on the grounds that
    `output_dir` was already checked at `validate`/`run` — true for an
    ordinary subdirectory and false for a SYMLINK under it, and core writes
    one itself (`point_latest`'s `<output_dir>/latest`). Built exactly as the
    review verified it: a real git repo holding the upstream record, and an
    `output_dir` elsewhere with a same-named symlink pointing into it — the
    relative form must now refuse this precisely as the absolute form
    already does for a plain in-repo directory.
    """
    repo_root = tmp_path / "downstream_repo"
    repo_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    run_id = "run_2020-01-01T00-00-00Z_ppppppp"
    in_repo_run = repo_root / "in_repo_run"
    _write_upstream(in_repo_run, run_id)
    output_dir = tmp_path / "results"
    output_dir.mkdir()
    (output_dir / run_id).symlink_to(in_repo_run, target_is_directory=True)
    with pytest.raises(ContractError) as e:
        resolve_run(run_id, output_dir=output_dir, repo_root=repo_root)
    assert e.value.code == "E-UPSTREAM-REPO-CONTAINED"


def test_relative_form_containment_control_reads_an_ordinary_subdirectory(tmp_path: Path):
    """The control the fix must not break: an ORDINARY (non-symlink) run
    directory under `output_dir`, outside any repo, still reads through the
    relative form exactly as before — the widened check must not refuse the
    case Decision 1 always meant to allow.
    """
    output_dir = tmp_path / "results"
    run_id = "run_2020-01-01T00-00-00Z_qqqqqqq"
    _write_upstream(output_dir / run_id, run_id)
    repo_root = tmp_path / "unused_repo_root"
    resolved, record = resolve_run(run_id, output_dir=output_dir, repo_root=repo_root)
    assert resolved == (output_dir / run_id).resolve()
    assert record["run_id"] == run_id


# ---------------------------------------------------------------------------
# Task 3 — UpstreamResolver/UpstreamLedger, injected: the wiring test, at
# `run` level (§ Steps and artifacts; the plan's task 3 step 6).
# ---------------------------------------------------------------------------

_REUSE_FROM_MISSING_RECORD_STEP = """\
# generated for the H8a task 3 wiring test
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        io.reuse_from("run_2020-01-01T00-00-00Z_zzzzzzz", "step01", "x.json")
        return {{}}
"""


def test_a_step_reached_through_run_has_a_real_resolver_injected(tmp_path: Path):
    """Task 3 step 6. Asserted through behaviour a step can observe — not by
    reaching into `io._upstream` — because Decision 2 gives the step-facing
    surface zero readable fields. The cheapest honest shape: a generated
    step calls `io.reuse_from` against a `run_id` no run ever wrote, and the
    SPECIFIC code that locator earns, `E-UPSTREAM-RECORD-MISSING` (not a
    wildcard `E-UPSTREAM-*`), lands in the failed execution's ledger line —
    which it can only do if a real `UpstreamResolver` reached this step's
    `io` and `resolve_run` actually ran.

    A second, later step still completing is the same property Global
    Constraints requires of every refusal-touching test in this slice: the
    failed execution is contained, the run continues, and `run.yaml` is
    still produced — nothing in H8a stops or alters a run (Decision 10).
    """
    project = run_a_project(
        tmp_path,
        replication={"repeats": [{"kind": "seed", "n": 1}]},
        units=8,
        _starter_step=_REUSE_FROM_MISSING_RECORD_STEP,
        extra_steps=["after"],
        expect_exit=EXIT_PARTIAL,
    )
    run_dir = project["run_dir"]
    assert (run_dir / "run.yaml").exists()
    lines = [json.loads(line) for line in (run_dir / "executions.jsonl").read_text().splitlines()]
    assert len(lines) == 2
    assert lines[0]["status"] == "failed"
    assert "E-UPSTREAM-RECORD-MISSING" in lines[0]["error"]
    assert lines[1]["status"] == "completed"


# ---------------------------------------------------------------------------
# Fix round 1 (task-b3-review.md): Major 1 / Minor 3 — UpstreamResolver's
# cache, keyed by locator rather than run_id, and its read-count guarantee.
# ---------------------------------------------------------------------------


def test_resolver_cache_reads_a_repeated_absolute_locator_only_once(tmp_path, monkeypatch):
    """Major 1. Before the fix, the cache was consulted only on the relative
    branch, so three identical ABSOLUTE calls did three `read_run_record`
    reads — and a `run.yaml` edited between two of them could answer
    differently each time, exactly the "two answers inside one record"
    Decision 6 forbids. Verified by counting real reads through a
    monkeypatched wrapper, not by reading the source.
    """
    import publishable.lineage as lineage_module

    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_xxxxxx1"
    upstream = tmp_path / "elsewhere" / "upstream"
    _write_upstream(upstream, run_id)

    calls: list[Path] = []
    real_read = lineage_module.read_run_record

    def counting_read(path: Path) -> dict:
        calls.append(path)
        return real_read(path)

    monkeypatch.setattr(lineage_module, "read_run_record", counting_read)

    resolver = lineage_module.UpstreamResolver(
        output_dir=output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=lineage_module.UpstreamLedger(),
    )
    for _ in range(3):
        _, record = resolver.resolve(str(upstream))
        assert record["run_id"] == run_id
    assert len(calls) == 1


def test_resolver_cache_reads_a_repeated_relative_locator_only_once(tmp_path, monkeypatch):
    """The relative-form half of the same guarantee, pinned the same way."""
    import publishable.lineage as lineage_module

    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_xxxxxx2"
    _write_upstream(output_dir / run_id, run_id)

    calls: list[Path] = []
    real_read = lineage_module.read_run_record

    def counting_read(path: Path) -> dict:
        calls.append(path)
        return real_read(path)

    monkeypatch.setattr(lineage_module, "read_run_record", counting_read)

    resolver = lineage_module.UpstreamResolver(
        output_dir=output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=lineage_module.UpstreamLedger(),
    )
    for _ in range(3):
        _, record = resolver.resolve(run_id)
        assert record["run_id"] == run_id
    assert len(calls) == 1


def test_resolver_cache_a_mid_run_edit_between_two_identical_absolute_calls_cannot_leak_through(
    tmp_path, monkeypatch
):
    """Decision 6's own stated consequence, reproduced directly: with the
    fix, editing the upstream's `run.yaml` between two identical absolute
    calls must NOT change the second call's answer, because the second call
    is a cache hit and never re-reads."""
    import publishable.lineage as lineage_module

    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_xxxxxx3"
    upstream = tmp_path / "elsewhere2" / "upstream"
    upstream.mkdir(parents=True)
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": "completed",
        "code_hash": "AAAA",
    }
    (upstream / "run.yaml").write_text(yaml.safe_dump(doc))

    resolver = lineage_module.UpstreamResolver(
        output_dir=output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=lineage_module.UpstreamLedger(),
    )
    _, first = resolver.resolve(str(upstream))
    assert first["code_hash"] == "AAAA"

    doc["code_hash"] = "BBBB"
    (upstream / "run.yaml").write_text(yaml.safe_dump(doc))

    _, second = resolver.resolve(str(upstream))
    assert second["code_hash"] == "AAAA"  # cached — the edit must not leak through


def test_resolver_cache_does_not_let_a_warm_absolute_call_shortcut_a_later_relative_one(
    tmp_path,
):
    """Minor 3. Before the fix, an absolute call cached under the resolved
    run_id, so a LATER relative call naming that same run_id hit the cache
    and skipped `resolve_run` entirely — including the "must sit under
    output_dir" check and the containment check — for a run the config
    addressed only by run_id. Cold and warm must agree: both refuse.
    """
    import publishable.lineage as lineage_module

    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_xxxxxx4"
    outside = tmp_path / "elsewhere3" / "not_under_output_dir"
    _write_upstream(outside, run_id)

    resolver = lineage_module.UpstreamResolver(
        output_dir=output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=lineage_module.UpstreamLedger(),
    )
    # cold: the relative form correctly fails, output_dir holds no such run
    with pytest.raises(ContractError) as e:
        resolver.resolve(run_id)
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"

    # warm the cache via the absolute form, under a DIFFERENT locator string
    _, record = resolver.resolve(str(outside))
    assert record["run_id"] == run_id

    # the relative form, asked again, must still fail — the warm cache must
    # not have created a run_id-keyed shortcut around output_dir
    with pytest.raises(ContractError) as e:
        resolver.resolve(run_id)
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"


# ---------------------------------------------------------------------------
# Minor 2 — the relative form must return a RESOLVED path, not merely check
# containment against a resolved probe while returning the unresolved one.
# ---------------------------------------------------------------------------


def test_relative_form_returns_a_resolved_path_not_merely_a_contained_one(tmp_path):
    """`spec-defects.md`'s closed filing claimed this half was pinned; it was
    not (task-b3-review.md Minor 2) — keeping containment on a resolved
    probe while returning `output_dir / locator` unresolved left every
    existing test green, because none of them route the run directory
    itself through a symlink. This one does: `<output_dir>/<run_id>` is a
    symlink to a differently-named real directory outside `output_dir`
    (still outside the repo, so containment is not what this test is
    about), and the returned path must be the real, resolved one.
    """
    output_dir = tmp_path / "output_dir"
    output_dir.mkdir()
    run_id = "run_2020-01-01T00-00-00Z_xxxxxx5"
    real_target = tmp_path / "real_target_elsewhere"
    _write_upstream(real_target, run_id)
    (output_dir / run_id).symlink_to(real_target, target_is_directory=True)
    repo_root = tmp_path / "unused_repo_root"

    resolved, record = resolve_run(run_id, output_dir=output_dir, repo_root=repo_root)
    assert resolved == real_target.resolve()
    assert resolved != output_dir / run_id  # the unresolved form the old code returned
    assert record["run_id"] == run_id


# ---------------------------------------------------------------------------
# Task 6 — accumulation: an entry on a read that RETURNS, kept across a
# failing execution, `used` and entries SORTED rather than by insertion
# order. Fixture O (direct calls, sized for three candidate orderings) —
# Fixture F (needs a real `run`) is in `tests/test_cli.py`.
# `docs/superpowers/plans/2026-08-20-lineage.md` task 6; design § Decision 6,
# § The discriminating fixtures / Fixture O.
# ---------------------------------------------------------------------------


def _reuse_io_for(tmp_path: Path, *, output_dir: Path) -> StepIO:
    resolver = UpstreamResolver(
        output_dir=output_dir,
        repo_root=tmp_path / "unused_repo_root",
        ledger=UpstreamLedger(),
    )
    return StepIO(
        step_dir=tmp_path / "downstream_step",
        input_dir=tmp_path / "downstream_input",
        run_dir=tmp_path / "downstream_run",
        upstream=resolver,
    )


def _write_upstream_with_artifacts(run_dir: Path, run_id: str, step: str, names: list[str]) -> None:
    """A synthesized upstream whose `shared/<step>/` holds one file per name
    in `names`, each with distinguishable content — enough for `reuse_from`
    to genuinely read each one rather than merely resolve a path."""
    execution = {"shared": {step: {"status": "completed"}}, "summary": {}, "conditions": []}
    _write_upstream(run_dir, run_id, execution)
    step_dir = run_dir / "shared" / step
    step_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        (step_dir / name).write_text(json.dumps({"name": name}))


def test_fixture_o_used_is_sorted_not_insertion_or_reverse_insertion(tmp_path: Path):
    """Three artifacts read in the order `c.json`, `a.json`, `b.json` —
    sorted (`a, b, c`), insertion (`c, a, b`) and reverse-insertion
    (`b, a, c`) all differ, so the exact-list assertion discriminates all
    three (`CLAUDE.md`: two elements only ever distinguish two answers)."""
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_oooooo1"
    _write_upstream_with_artifacts(
        output_dir / run_id, run_id, "step01", ["c.json", "a.json", "b.json"]
    )
    io = _reuse_io_for(tmp_path, output_dir=output_dir)
    io.reuse_from(run_id, "step01", "c.json")
    io.reuse_from(run_id, "step01", "a.json")
    io.reuse_from(run_id, "step01", "b.json")
    entries = io._upstream.ledger.entries()
    assert len(entries) == 1
    assert entries[0]["used"] == ["step01/a.json", "step01/b.json", "step01/c.json"]


def test_fixture_o_entries_are_sorted_by_run_id_not_read_order(tmp_path: Path):
    """Three upstream run directories read in an order that is neither
    their sorted `run_id` order nor its reverse — `bbb`, then `aaa`, then
    `ccc` — sorted is `aaa, bbb, ccc`; that read order is neither it nor
    `ccc, bbb, aaa`."""
    output_dir = tmp_path / "output_dir"
    run_id_a = "run_2020-01-01T00-00-00Z_aaaaaa9"
    run_id_b = "run_2020-01-01T00-00-00Z_bbbbbb9"
    run_id_c = "run_2020-01-01T00-00-00Z_ccccccc"
    for rid in (run_id_a, run_id_b, run_id_c):
        _write_upstream_with_artifacts(output_dir / rid, rid, "step01", ["x.json"])
    io = _reuse_io_for(tmp_path, output_dir=output_dir)
    # read order: b, a, c — neither sorted (a, b, c) nor reverse (c, b, a)
    io.reuse_from(run_id_b, "step01", "x.json")
    io.reuse_from(run_id_a, "step01", "x.json")
    io.reuse_from(run_id_c, "step01", "x.json")
    entries = io._upstream.ledger.entries()
    assert [e["run_id"] for e in entries] == [run_id_a, run_id_b, run_id_c]


def test_fixture_o_both_locator_forms_for_one_upstream_merge_into_one_entry(tmp_path: Path):
    """Step 4: an upstream read once by `run_id` and once by an absolute
    path is ONE entry, with both artifact names in `used` — the ledger is
    keyed by the resolved `run_id`, never by the locator string, so the two
    calls do not become two entries."""
    output_dir = tmp_path / "output_dir"
    run_id = "run_2020-01-01T00-00-00Z_ooooo10"
    run_dir = output_dir / run_id
    _write_upstream_with_artifacts(run_dir, run_id, "step01", ["x.json", "y.json"])
    io = _reuse_io_for(tmp_path, output_dir=output_dir)
    io.reuse_from(run_id, "step01", "x.json")
    io.reuse_from(str(run_dir), "step01", "y.json")
    entries = io._upstream.ledger.entries()
    assert len(entries) == 1
    assert entries[0]["run_id"] == run_id
    assert entries[0]["used"] == ["step01/x.json", "step01/y.json"]


# ---------------------------------------------------------------------------
# H8c task 4 — `read_record_file`, extracted because a bundle member is not
# `<dir>/run.yaml` (docs/superpowers/plans/2026-08-21-report-study.md
# § Corrections, correction 1; task-4-brief.md). `read_run_record` above is
# now `read_record_file(run_dir / "run.yaml")` — these tests exercise the
# extracted entry directly, over a path shaped like a bundle member: a bare
# file, `main.run.yaml`, with no `run.yaml`-named sibling and no directory
# of its own. One refusal set, two entries — the same three codes must stay
# reachable from THIS entry too.
# ---------------------------------------------------------------------------


def test_read_record_file_reads_a_bundle_member_shaped_file_directly(tmp_path: Path):
    """A bare file named `main.run.yaml` — never `<dir>/run.yaml` — is
    exactly § Building one's bundle tree shape. `read_record_file` must
    read it directly, with no directory to append `run.yaml` onto.

    This is also the mutation-discriminating arm for "make `read_record_file`
    accept a directory (append `run.yaml` unconditionally)": a bundle member
    is a FILE, so a mutant that appends `run.yaml` looks for
    `main.run.yaml/run.yaml`, which does not exist, and raises
    `E-UPSTREAM-RECORD-MISSING` where the honest code reads the file clean.
    """
    member = tmp_path / "main.run.yaml"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_bbbbbb1",
        "status": "completed",
    }
    member.write_text(yaml.safe_dump(doc))
    assert read_record_file(member) == doc


def test_read_run_record_delegates_to_read_record_file(tmp_path: Path):
    """`read_run_record(run_dir)` is `read_record_file(run_dir / "run.yaml")`
    — one refusal set, two entries, on `_nest_repeat`'s own precedent. Pinned
    by reading the SAME record through both entries and asserting equality,
    rather than by inspecting source text.
    """
    run_dir = tmp_path / "run_x"
    doc = {
        "schema_version": SCHEMA_VERSION,
        "run_id": "run_2020-01-01T00-00-00Z_cccccc1",
        "status": "completed",
    }
    _write_run_yaml(run_dir, doc)
    assert read_run_record(run_dir) == read_record_file(run_dir / "run.yaml")


def test_read_record_file_missing_is_still_record_missing_on_a_bare_file_path(
    tmp_path: Path,
):
    with pytest.raises(ContractError) as e:
        read_record_file(tmp_path / "main.run.yaml")
    assert e.value.code == "E-UPSTREAM-RECORD-MISSING"
    # The reworded message must be true of a bundle member too — a bare
    # file, never a directory — so it must not claim "this is not a run
    # directory", which is false of a file operand (§ Corrections,
    # correction 1; task 4 step 3: "prefer deleting the false half to
    # inventing a new claim").
    assert "run directory" not in str(e.value)


def test_read_record_file_invalid_yaml_on_a_bare_file_path_is_record_unreadable(
    tmp_path: Path,
):
    member = tmp_path / "sensitivity.run.yaml"
    member.write_text("schema_version: 1.0\nrun_id: [unterminated\n")
    with pytest.raises(ContractError) as e:
        read_record_file(member)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"
    assert "not valid YAML" in str(e.value)


def test_read_record_file_not_a_mapping_on_a_bare_file_path_is_distinguishable_by_message(
    tmp_path: Path,
):
    """Shares its code with the invalid-YAML case above; the message is
    what tells the two faults apart, exactly as `test_a_yaml_document_that_
    is_not_a_mapping_is_record_unreadable` already pins for the directory
    entry."""
    member = tmp_path / "sensitivity.run.yaml"
    member.write_text("- just\n- a\n- list\n")
    with pytest.raises(ContractError) as e:
        read_record_file(member)
    assert e.value.code == "E-UPSTREAM-RECORD-UNREADABLE"
    assert "did not parse to a mapping" in str(e.value)


def test_read_record_file_version_mismatch_on_a_bare_file_path(tmp_path: Path):
    member = tmp_path / "sensitivity.run.yaml"
    member.write_text(
        yaml.safe_dump({"schema_version": "99.9", "run_id": "run_2020-01-01T00-00-00Z_ddddddd"})
    )
    with pytest.raises(ContractError) as e:
        read_record_file(member)
    assert e.value.code == "E-UPSTREAM-RECORD-VERSION"


# ===========================================================================
# H9b task 6 — `read_execution_ledger` / `attempt_counts`: the FIRST reader of
# `executions.jsonl` anywhere in `src/` (§ Corrections against the code,
# correction 21, re-measured by this task and reported).
# ===========================================================================


def test_h9b_the_ledger_reader_reads_a_real_runs_lines(tmp_path: Path):
    """Against a genuinely produced ledger, not a synthesized one: the reader's
    job is to read what `execute_plan` writes, and a hand-written fixture would
    make that agreement a coincidence.

    The line count and the key set are asserted together — a reader returning
    `[]` would satisfy any per-line assertion for free.
    """
    from publishable.lineage import read_execution_ledger

    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]}, units=10)
    records = read_execution_ledger(doc["run_dir"])
    raw = [
        line
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    assert len(records) == len(raw)
    assert records
    for entry in records:
        assert {"step", "scope", "condition", "repeat", "status"} <= set(entry)


def test_h9b_an_absent_ledger_is_no_executions_not_a_fault(tmp_path: Path):
    """A run directory can exist with no `executions.jsonl` at all — a
    run-start probe raise leaves exactly that shape — and *no executions* is
    not the same claim as *a broken ledger*."""
    from publishable.lineage import read_execution_ledger

    (tmp_path / "run_x").mkdir()
    assert read_execution_ledger(tmp_path / "run_x") == []


def test_h9b_attempt_counts_counts_records_per_triple(tmp_path: Path):
    """`reference.md` § Resuming defines `attempts` as the number of records a
    triple holds in `executions.jsonl`. The second record is appended BY HAND
    here — a triple genuinely runs twice only under `resume`, which does not
    dispatch yet, and the count is what is under test either way.

    The neighbour's staying at `1` is what makes the `2` non-vacuous: a
    counter keyed on the step alone, or one that counted the whole file,
    would report `2` for both.
    """
    from publishable.lineage import attempt_counts, read_execution_ledger

    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 2}]}, units=10)
    ledger = doc["run_dir"] / "executions.jsonl"
    lines = [line for line in ledger.read_text().splitlines() if line.strip()]
    first, second = json.loads(lines[0]), json.loads(lines[1])
    # A genuine second attempt at the same triple: the same three key fields,
    # a later clock, and a `failed` status — so the count cannot be read off
    # `status` either.
    repeated = dict(first)
    repeated["status"] = "failed"
    repeated["started_at"] = "2026-08-23T23:59:59Z"
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(repeated) + "\n")

    counts = attempt_counts(read_execution_ledger(doc["run_dir"]))
    assert counts[(first["step"], first["condition"], first["repeat"])] == 2
    assert counts[(second["step"], second["condition"], second["repeat"])] == 1
    # Every other triple is 1, so no arm of this fixture is 2 by accident.
    assert sorted(counts.values()) == [1] * (len(counts) - 1) + [2]


def test_h9b_a_mangled_ledger_line_refuses_rather_than_reading_as_never_ran(tmp_path: Path):
    """Three faults, one code (`E-RESUME-LEDGER-UNREADABLE`), each with its own
    message: a line that is not JSON, a line that parses to something other
    than an object, and a line missing one of the five keys every line has
    always carried.

    The alternative is what makes this a refusal rather than a skip: a reader
    that dropped a mangled line would report the triple as *never ran*, and
    `resume` would re-execute an execution already paid for — or worse,
    reconstitute nothing for it and publish intervals over the remainder.

    A control arm asserts the same directory reads clean before the edit, so
    a refusal that fired for some unrelated reason is not counted as a pass.
    """
    from publishable.lineage import read_execution_ledger

    doc = run_a_project(tmp_path, replication={"repeats": [{"kind": "seed", "n": 1}]}, units=10)
    ledger = doc["run_dir"] / "executions.jsonl"
    good = ledger.read_text()
    assert read_execution_ledger(doc["run_dir"])  # the control

    for text, fragment in (
        (good + "{not json\n", "not valid JSON"),
        (good + '["step01", 1]\n', "parsed to list"),
        (good + '{"step": "s", "scope": "repeat", "condition": 0}\n', "missing repeat, status"),
    ):
        ledger.write_text(text)
        with pytest.raises(ContractError) as excinfo:
            read_execution_ledger(doc["run_dir"])
        assert excinfo.value.code == "E-RESUME-LEDGER-UNREADABLE"
        assert fragment in str(excinfo.value)
    ledger.write_text(good)
    assert read_execution_ledger(doc["run_dir"])


# ===========================================================================
# H9b task 10 — `sweep.yaml`'s recorded plan: the reader and the four-tuple
# cross-check (design Decision 9). `freeze`'s own reader was measured and
# does not fit — it is inline in `command_freeze`, reports through `_refuse`
# and returns an exit code rather than raising, carries `E-FREEZE-*` codes,
# and reads `conditions` only, never `order` or `execution_order`. The grep
# behind that claim is in `read_sweep_plan`'s docstring.
# ===========================================================================


def _h9b_sweep_project(tmp_path: Path, **overrides) -> dict:
    """One run whose `sweep.yaml` has TWO conditions, so a cross-check over a
    reordering has something to reorder and a length mismatch can be produced
    by dropping one entry."""
    return run_a_project(
        tmp_path,
        replication={"repeats": [{"kind": "seed", "n": 2}], "rationale": "two seeds"},
        units=6,
        sweep={"grid": {"analysis.method": ["pearson", "spearman"]}},
        **overrides,
    )


def test_h9b_the_recorded_plan_reader_returns_the_file_not_a_re_derivation(tmp_path: Path):
    """`read_sweep_plan` hands back exactly what `sweep.yaml` holds: the
    condition entries in recorded order, the recorded `order` scalar, and the
    realized `(condition, repeat)` pairs.

    Asserted against the file's OWN parsed content rather than against a
    hand-written expectation, because the claim is *this is the file* — a
    literal expectation would pass for a reader that re-derived the same
    answer from the config, which is the reading Decision 9 refuses.
    """
    from publishable.lineage import read_sweep_plan

    doc = _h9b_sweep_project(tmp_path)
    raw = yaml.safe_load((doc["run_dir"] / "sweep.yaml").read_text())
    recorded = read_sweep_plan(doc["run_dir"])
    assert list(recorded.conditions) == raw["conditions"]
    assert recorded.order == raw["order"] == "as_declared"
    assert list(recorded.execution_order) == [
        (entry["condition"], entry["repeat"]) for entry in raw["execution_order"]
    ]
    # Four pairs: 2 conditions × 2 seeds. Stated so a fixture that recorded
    # nothing cannot satisfy the equalities above by being empty on both
    # sides.
    assert len(recorded.execution_order) == 4
    assert isinstance(recorded.execution_order, tuple)
    assert isinstance(recorded.conditions, tuple)


def test_h9b_a_sweep_yaml_that_cannot_be_read_as_a_plan_is_plan_missing(tmp_path: Path):
    """`E-RESUME-PLAN-MISSING` covers absent, unparseable, and every shape
    fault in the three fields this reader projects — one code for one remedy
    (the run died before its plan was written, or the directory was edited).

    A control arm reads the same directory clean before and after each edit,
    so a refusal that fired for an unrelated reason is not counted as a pass.
    """
    from publishable.lineage import read_sweep_plan

    doc = _h9b_sweep_project(tmp_path)
    path = doc["run_dir"] / "sweep.yaml"
    good = path.read_text()
    assert read_sweep_plan(doc["run_dir"]).conditions  # the control

    parsed = yaml.safe_load(good)
    no_conditions = dict(parsed)
    no_conditions.pop("conditions")
    bad_order = dict(parsed) | {"order": ["randomized"]}
    bad_pair = dict(parsed) | {"execution_order": [{"condition": 0, "repeat": 7}]}
    for text, fragment in (
        ("conditions: [\n", "does not parse"),
        ("just a string\n", "holds no `conditions` list"),
        (yaml.safe_dump(no_conditions), "holds no `conditions` list"),
        (yaml.safe_dump(bad_order), "not the recorded mode string"),
        (yaml.safe_dump(bad_pair), "execution_order entry 1 is not a recorded"),
    ):
        path.write_text(text)
        with pytest.raises(ContractError) as excinfo:
            read_sweep_plan(doc["run_dir"])
        assert excinfo.value.code == "E-RESUME-PLAN-MISSING"
        assert fragment in str(excinfo.value)
        path.write_text(good)
        assert read_sweep_plan(doc["run_dir"]).conditions  # the control again

    path.unlink()
    with pytest.raises(ContractError) as excinfo:
        read_sweep_plan(doc["run_dir"])
    assert excinfo.value.code == "E-RESUME-PLAN-MISSING"
    assert "is absent" in str(excinfo.value)


def test_h9b_the_cross_check_is_over_the_full_four_tuple(tmp_path: Path):
    """**The mutation this test exists for**: a cross-check on `index` and
    `label` only. The `values` arm below edits a recorded condition's
    `values` and NOTHING else, so the two-field reading passes it and the
    four-tuple reading refuses — the two branches were checked in that
    order.

    `values` is what determines the cfg an execution runs under, so a resume
    that accepted a moved one would execute the remainder of a plan under
    different parameters than the completed part ran under, with every label
    agreeing. `is_baseline` decides which condition every `vs_baseline`
    contrast is computed against.
    """
    from publishable.lineage import RecordedPlan, check_recorded_conditions, read_sweep_plan
    from publishable.sweep import expand

    doc = _h9b_sweep_project(tmp_path)
    conditions = expand(yaml.safe_load(Path(doc["cfg"]).read_text()))
    recorded = read_sweep_plan(doc["run_dir"])
    # The control: the run's own file agrees with its own config.
    check_recorded_conditions(recorded, conditions)
    assert len(conditions) == 2

    def edited(position: int, **changes) -> RecordedPlan:
        entries = [dict(entry) for entry in recorded.conditions]
        entries[position].update(changes)
        return dataclasses.replace(recorded, conditions=tuple(entries))

    for plan, field in (
        (edited(0, index=7), "index"),
        (edited(1, label="analysis.method=kendall"), "label"),
        (edited(1, values={"analysis.method": "kendall"}), "values"),
        # Flipped from whatever the file records rather than written as a
        # literal: a literal `False` is a no-op edit for a design whose
        # first condition is not the baseline, and a no-op edit tests
        # nothing (measured — this arm did not raise until it was flipped).
        (edited(0, is_baseline=not recorded.conditions[0].get("is_baseline")), "is_baseline"),
    ):
        with pytest.raises(ContractError) as excinfo:
            check_recorded_conditions(plan, conditions)
        assert excinfo.value.code == "E-RESUME-PLAN-MISMATCH"
        assert f"`{field}` disagrees" in str(excinfo.value)

    # A length disagreement is named before any per-entry field, so the
    # per-entry message can name a condition that exists on both sides.
    with pytest.raises(ContractError) as excinfo:
        check_recorded_conditions(
            dataclasses.replace(recorded, conditions=recorded.conditions[:1]), conditions
        )
    assert excinfo.value.code == "E-RESUME-PLAN-MISMATCH"
    assert "records 1 condition(s)" in str(excinfo.value)


def test_h9b_the_cross_check_is_in_recorded_order_not_by_index_lookup(tmp_path: Path):
    """A file whose two condition entries are SWAPPED holds both conditions
    and both indices, so an index-keyed lookup finds every one of them and
    agrees on all four fields. Compared in recorded order, it refuses.

    The recorded order is itself a fact of the plan — `execution_order`'s
    pairs are matched against it — so this is a distinct reading from the
    field set, and no arm of the four-tuple test can see it.
    """
    from publishable.lineage import check_recorded_conditions, read_sweep_plan
    from publishable.sweep import expand

    doc = _h9b_sweep_project(tmp_path)
    conditions = expand(yaml.safe_load(Path(doc["cfg"]).read_text()))
    recorded = read_sweep_plan(doc["run_dir"])
    swapped = dataclasses.replace(recorded, conditions=tuple(reversed(recorded.conditions)))
    with pytest.raises(ContractError) as excinfo:
        check_recorded_conditions(swapped, conditions)
    assert excinfo.value.code == "E-RESUME-PLAN-MISMATCH"


# ===========================================================================
# H9b task 11 — `allocation.json` read rather than re-drawn (design Decision
# 10). This is the reader § Allocation and § Resuming both say does not
# exist; the application onto `Prepared` is pinned in `tests/test_cli.py`,
# where `_prepare_run` lives.
# ===========================================================================


def test_h9b_the_allocation_reader_returns_the_file_and_absence_is_not_a_fault(tmp_path: Path):
    """A drawn axis's own `allocation.json`, read back as the file holds it —
    and `None` for a design that declares neither an arm axis nor a holdout,
    which § The other files a run writes makes the ordinary case.

    Both arms in one test because the pair is the claim: absence is not a
    refusal, and a present file is returned rather than re-derived.
    """
    from publishable.lineage import read_allocation

    keys = [f"p{i}" for i in range(8)]
    drawn = run_a_project(
        tmp_path / "drawn",
        roster_csv="patient_id\n" + "\n".join(keys) + "\n",
        units_overrides={
            "allocation": "between",
            "assign": {"arm": {"method": "random", "seed": 11}},
        },
        sweep={"groups": [{"by": "arm", "levels": ["control", "treatment"]}]},
    )
    document = read_allocation(drawn["run_dir"])
    assert document == json.loads((drawn["run_dir"] / "allocation.json").read_text())
    assert sorted(
        document["arms"]["arm"]["control"] + document["arms"]["arm"]["treatment"]
    ) == sorted(keys)

    plain = run_a_project(tmp_path / "plain", units=6)
    assert not (plain["run_dir"] / "allocation.json").exists()
    assert read_allocation(plain["run_dir"]) is None


def test_h9b_an_unusable_allocation_file_is_stale_not_absent(tmp_path: Path):
    """An unparseable file is `E-RESUME-ALLOCATION-STALE`, never treated as
    absence: absence says *nothing was partitioned* and would let the run
    re-draw the whole allocation, which is the one thing Decision 10 exists
    to prevent.

    A control reads the same directory clean before each edit.
    """
    from publishable.lineage import read_allocation

    keys = [f"p{i}" for i in range(8)]
    doc = run_a_project(
        tmp_path,
        roster_csv="patient_id\n" + "\n".join(keys) + "\n",
        units_overrides={
            "allocation": "between",
            "assign": {"arm": {"method": "random", "seed": 11}},
        },
        sweep={"groups": [{"by": "arm", "levels": ["control", "treatment"]}]},
    )
    path = doc["run_dir"] / "allocation.json"
    good = path.read_text()
    for text, fragment in (("{not json", "will not parse"), ("[1, 2]", "holds list")):
        assert read_allocation(doc["run_dir"]) is not None  # the control
        path.write_text(text)
        with pytest.raises(ContractError) as excinfo:
            read_allocation(doc["run_dir"])
        assert excinfo.value.code == "E-RESUME-ALLOCATION-STALE"
        assert fragment in str(excinfo.value)
        path.write_text(good)

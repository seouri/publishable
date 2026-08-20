"""`read_run_record` — the `run.yaml` reader `lineage.py` gives H8a, tested against
synthesized records for each refusal and against a genuinely produced one (Fixture R),
per `docs/superpowers/plans/2026-08-20-lineage.md` task 1 and
`docs/superpowers/specs/2026-08-20-lineage-design.md` § 3.
"""

import json
import subprocess
from pathlib import Path

import pytest
import yaml
from tests.test_cli import run_a_project

from publishable.diagnostics import EXIT_PARTIAL
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

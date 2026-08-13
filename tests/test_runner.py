import copy
from pathlib import Path

import numpy as np
import pytest
from tests.test_stats import _repeat_result

from publishable import BaseExperiment, BaseStep
from publishable.config import Config
from publishable.errors import ContractError
from publishable.replication import Repeat
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import (
    _handed_keys,
    _units_failed_anywhere,
    attrition,
    execute_plan,
    resolve_condition_cfg,
    resolve_wide_cfg,
    step_dir_for,
)
from publishable.scope import Execution, build_plan
from publishable.units import Unit, UnitList


class Load(BaseStep):
    scope = "run"

    def run(self, cfg, io):
        io.write("cohort.json", {"loaded": True})
        return {"n": 2}


class Analyze(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {"r": 0.5}


class Boom(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        raise ValueError("this execution is broken")


class ReturnsString(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return "not-a-mapping"


class ReturnsList(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return []


class ReturnsNone(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return None


class ReturnsNumpyScalar(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        return {"r": np.float64(0.5)}


def test_a_composed_repeat_label_is_one_directory_segment(tmp_path):
    ex = Execution(step_cls=Analyze, step_name="fit", scope="repeat", condition_index=0,
                   condition_label="baseline", repeat_label="batch01_seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=False) == (
        tmp_path / "conditions" / "00_baseline" / "batch01_seed42" / "fit"
    )


def test_a_single_level_run_is_unchanged(tmp_path):
    ex = Execution(step_cls=Analyze, step_name="fit", scope="repeat", condition_index=None,
                   condition_label=None, repeat_label="seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=False) == (
        tmp_path / "seed42" / "fit"
    )


def test_a_collapsed_repeat_still_collapses_with_a_composed_label(tmp_path):
    ex = Execution(step_cls=Analyze, step_name="fit", scope="repeat", condition_index=None,
                   condition_label=None, repeat_label="batch01_seed42")
    assert step_dir_for(tmp_path, ex, collapse_repeats=True) == tmp_path / "fit"


def harness(
    tmp_path: Path,
    steps,
    *,
    units=None,
    repeats=None,
    max_failed_fraction=None,
    conditions=None,
    fold_members=None,
    measurements=None,
):
    class P(BaseExperiment):
        pass

    P.steps = steps
    if repeats is None:
        repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    if conditions is None:
        conditions = [(0, None)]
    plan = build_plan(P(), conditions=conditions, repeat_labels=[r.label for r in repeats])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfgs={0: Config({"parameters": {}}), -1: Config({"parameters": {}})},
        repeats=repeats,
        digest="sha256:abc",
        units=units,
        max_failed_fraction=max_failed_fraction,
        fold_members=fold_members,
        measurements=measurements,
    )
    return run_dir, results, repeats


def test_no_sweep_means_no_conditions_level(tmp_path: Path):
    run_dir, _, _ = harness(tmp_path, [Load, Analyze])
    assert (run_dir / "shared" / "load" / "cohort.json").is_file()
    assert not (run_dir / "conditions").exists()
    assert (run_dir / "seed17").is_dir()
    assert (run_dir / "seed42").is_dir()


def test_a_bare_baseline_still_gets_the_conditions_level(tmp_path: Path):
    """`docs/reference.md` § How artifacts are organized: the `conditions/` level
    appears when a sweep is *declared*, not when N > 1. A bare `sweep.baseline`
    with no `grid` expands to one condition (`sweep.expand`'s
    `test_a_bare_baseline_is_one_condition_but_labelled`), but unlike the no-sweep
    case it is labelled `"baseline"`, and `step_dir_for` nests under
    `conditions/00_baseline/` rather than collapsing the level — the opposite of
    `test_no_sweep_means_no_conditions_level` right above."""
    run_dir, _, _ = harness(tmp_path, [Load, Analyze], conditions=[(0, "baseline")])
    assert (run_dir / "shared" / "load" / "cohort.json").is_file()
    assert (run_dir / "conditions" / "00_baseline" / "seed17" / "analyze").is_dir()
    assert (run_dir / "conditions" / "00_baseline" / "seed42" / "analyze").is_dir()
    assert not (run_dir / "seed17").exists()


def test_a_failed_execution_is_recorded_and_the_run_continues(tmp_path: Path):
    _, results, _ = harness(tmp_path, [Boom, Analyze])
    statuses = [r.status for r in results]
    assert statuses.count("failed") == 2
    assert statuses.count("completed") == 2
    assert any("this execution is broken" in (r.error or "") for r in results)


def test_status_is_partial_when_some_failed(tmp_path: Path):
    _, results, _ = harness(tmp_path, [Boom, Analyze])
    assert run_status(results) == "partial"
    _, ok, _ = harness(tmp_path / "b", [Load, Analyze])
    assert run_status(ok) == "completed"


def test_executions_jsonl_gets_one_record_per_finished_execution(tmp_path: Path):
    run_dir, results, _ = harness(tmp_path, [Load, Analyze])
    lines = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(lines) == len(results)


def test_per_repeat_holds_exactly_what_the_step_returned(tmp_path: Path):
    _, results, repeats = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
    )
    per_repeat = doc["results"]["conditions"][0]["per_repeat"]["analyze"]
    assert per_repeat == {"seed17": {"r": 0.5}, "seed42": {"r": 0.5}}


def test_run_yaml_carries_the_three_hashes_and_the_config_verbatim(tmp_path: Path):
    _, results, repeats = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"metadata": {"name": "c"}},
        code_hash="sha256:c", parameters_hash="sha256:p",
        provenance={"input_manifest_hash": "sha256:m"}, results=results, repeats=repeats,
    )
    assert doc["code_hash"] == "sha256:c"
    assert doc["parameters_hash"] == "sha256:p"
    assert doc["provenance"]["input_manifest_hash"] == "sha256:m"
    assert doc["config"] == {"metadata": {"name": "c"}}
    assert doc["draft"] is False
    assert doc["schema_version"] == "1.0"


def test_a_repeat_label_missing_from_repeats_raises_seed_missing(tmp_path: Path):
    class P(BaseExperiment):
        pass

    P.steps = [Analyze]
    plan = build_plan(P(), conditions=[(0, None)], repeat_labels=["seedA", "seedB"])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    mismatched_repeats = [Repeat("seed", "seedX", 111), Repeat("seed", "seedY", 222)]
    with pytest.raises(ContractError) as excinfo:
        execute_plan(
            plan=plan,
            run_dir=run_dir,
            input_dir=tmp_path / "input",
            cfgs={0: Config({"parameters": {}}), -1: Config({"parameters": {}})},
            repeats=mismatched_repeats,
            digest="sha256:abc",
        )
    assert excinfo.value.code == "E-RUN-SEED-MISSING"


def test_an_unlabelled_single_repeat_still_resolves_its_seed(tmp_path: Path):
    class P(BaseExperiment):
        pass

    P.steps = [Analyze]
    plan = build_plan(P(), conditions=[(0, None)], repeat_labels=[""])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfgs={0: Config({"parameters": {}}), -1: Config({"parameters": {}})},
        repeats=[Repeat("seed", "", 17)],
        digest="sha256:abc",
    )
    assert results[0].status == "completed"


def test_a_non_mapping_return_fails_that_execution_and_the_run_continues(tmp_path: Path):
    run_dir, results, _ = harness(tmp_path, [ReturnsString, Analyze])
    string_result = next(r for r in results if r.execution.step_name == "returns_string")
    analyze_result = next(r for r in results if r.execution.step_name == "analyze")
    assert string_result.status == "failed"
    assert "E-STEP-RETURN-TYPE" in (string_result.error or "")
    assert analyze_result.status == "completed"
    assert run_status(results) == "partial"


def test_a_falsy_non_mapping_return_also_fails_rather_than_being_swallowed(tmp_path: Path):
    _, results, _ = harness(tmp_path, [ReturnsList, Analyze])
    list_result = next(r for r in results if r.execution.step_name == "returns_list")
    assert list_result.status == "failed"
    assert "E-STEP-RETURN-TYPE" in (list_result.error or "")


def test_a_none_return_still_completes_with_an_empty_mapping_recorded(tmp_path: Path):
    _, results, _ = harness(tmp_path, [ReturnsNone])
    none_results = [r for r in results if r.execution.step_name == "returns_none"]
    assert none_results
    for result in none_results:
        assert result.status == "completed"
        assert result.returned == {}


def test_a_numpy_scalar_return_reaches_the_result_as_a_plain_float(tmp_path: Path):
    _, results, _ = harness(tmp_path, [ReturnsNumpyScalar])
    numpy_results = [r for r in results if r.execution.step_name == "returns_numpy_scalar"]
    assert numpy_results
    for result in numpy_results:
        assert result.status == "completed"
        assert type(result.returned["r"]) is float


def test_attrition_reconciles_exactly(tmp_path: Path):
    """resolved == completed + ineligible + failed, in every scenario."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class Partial(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            for u in list(io.units)[:7]:
                io.record(u.key, {"v": 1.0})
            io.skip("p9", "by design")
            return {}

    _, results, _ = harness(tmp_path, [Partial], units=roster)
    counts = attrition(results, roster, "partial", condition_index=0)
    assert counts == {"resolved": 10, "completed": 7, "ineligible": 1, "failed": 2}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


class Measures(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        for u in io.units:
            io.record(u.key, {"v": 1.0}, measurement="r1")
            io.record(u.key, {"v": 3.0}, measurement="r2")
            io.record(u.key, {"v": 8.0}, measurement="r3")
        return {}


def test_a_real_step_may_measure_when_the_config_declares_measurements(tmp_path: Path):
    """`data.units.measurements` must reach the `StepIO` the runner builds, or a
    config that declares it is honoured at the input path and raises
    `E-STEP-MEASUREMENT-UNDECLARED` at the step path. A directly-constructed
    `StepIO` cannot catch that, which is how it went missing."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(3)])
    _, results, _ = harness(
        tmp_path,
        [Measures],
        units=roster,
        measurements={"by": "read_id", "collapse": "mean"},
    )
    assert [r.status for r in results] == ["completed", "completed"]
    # 1, 3, 8 rather than a symmetric pair: mean is 4.0 and median is 3.0, so this
    # assertion fails if the collapse silently uses the wrong rule. Two symmetric
    # values agree under both, which is how the step-path mutation this slice
    # prescribed was unable to fail.
    assert results[0].rows == tuple({"unit": f"p{i}", "v": 4.0} for i in range(3))


def test_a_step_that_only_measures_is_refused_without_the_declaration(tmp_path: Path):
    """Control for the previous test: the declaration is what makes it reachable,
    so the same step under no declaration must still fail that execution."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(3)])
    _, results, _ = harness(tmp_path, [Measures], units=roster)
    assert [r.status for r in results] == ["failed", "failed"]
    assert "E-STEP-MEASUREMENT-UNDECLARED" in (results[0].error or "")


def test_attrition_reconciles_for_a_step_that_only_measures(tmp_path: Path):
    """The measured unit must be `completed`, not `failed`. `completed` counts
    distinct unit keys that reached `io.record` (`reference.md` § The unit table is
    the inference base), and `failed` is the subtraction left over — so a unit
    whose rows never collapse into `recorded_keys` is silently a failure while its
    step succeeded and its measurements sit on disk."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(4)])

    class MeasuresSome(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            for u in list(io.units)[:3]:
                io.record(u.key, {"v": 1.0}, measurement="r1")
                io.record(u.key, {"v": 3.0}, measurement="r2")
                io.record(u.key, {"v": 8.0}, measurement="r3")
            io.skip("p3", "by design")
            return {}

    _, results, _ = harness(
        tmp_path,
        [MeasuresSome],
        units=roster,
        measurements={"by": "read_id", "collapse": "mean"},
    )
    counts = attrition(results, roster, "measures_some", condition_index=0)
    assert counts == {"resolved": 4, "completed": 3, "ineligible": 1, "failed": 0}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_a_scalar_only_repeat_step_does_not_collapse_another_steps_attrition(tmp_path: Path):
    """A second repeat-scoped step that records no units at all — a timing step, a
    logging step — must not change `attrition`'s count for the step that DOES
    record. Before `step_name` was required, `attrition` intersected `recorded`
    across every repeat-scoped execution in the condition regardless of which step
    produced it, so this scalar-only step's empty `recorded` set collapsed
    `Partial`'s real 7/1/2 split down to `{resolved: 10, completed: 0,
    ineligible: 0, failed: 10}`."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class Partial(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            for u in list(io.units)[:7]:
                io.record(u.key, {"v": 1.0})
            io.skip("p9", "by design")
            return {}

    class TimingOnly(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            return {"wall_seconds": 0.01}

    _, results, _ = harness(tmp_path, [Partial, TimingOnly], units=roster)
    counts = attrition(results, roster, "partial", condition_index=0)
    assert counts == {"resolved": 10, "completed": 7, "ineligible": 1, "failed": 2}
    timing_counts = attrition(results, roster, "timing_only", condition_index=0)
    assert timing_counts == {"resolved": 10, "completed": 0, "ineligible": 0, "failed": 10}


def test_a_scalar_only_repeat_step_does_not_trip_the_failure_guard(tmp_path: Path):
    """The `max_failed_fraction` guard must not treat a scalar-only step's lack of
    any recorded units as attrition: only a step that is in the business of
    recording units (as decided by whether it ever produced a row) can fail the
    roster. A recording step that completes everyone must keep the run going even
    though a scalar-only sibling step records nothing."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class RecordsEveryone(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            for u in io.units:
                io.record(u.key, {"v": 1.0})
            return {}

    class TimingOnly(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            return {"wall_seconds": 0.01}

    _, results, _ = harness(
        tmp_path, [RecordsEveryone, TimingOnly], units=roster, max_failed_fraction=0.2
    )
    assert len(results) == 4, "the run must not be truncated by the scalar-only step"
    assert all(r.status == "completed" for r in results)


def test_completion_is_the_intersection_across_repeats(tmp_path: Path):
    """A unit recorded in one repeat but not another is NOT completed."""
    roster = UnitList([Unit(key=f"p{i}") for i in range(4)])

    class Flaky(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            keep = list(io.units) if self.repeat == "seed17" else list(io.units)[:2]
            for u in keep:
                io.record(u.key, {"v": 1.0})
            return {}

    _, results, _ = harness(
        tmp_path,
        [Flaky],
        units=roster,
        repeats=[Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)],
    )
    assert attrition(results, roster, "flaky", condition_index=0)["completed"] == 2


def test_ineligibility_is_also_the_intersection_across_repeats(tmp_path: Path):
    """A unit skipped in one repeat and completed in another is FAILED, not ineligible:
    eligibility is a property of the design, so an inconsistent answer across repeats is
    not a design exclusion — it is the same defect `failed` exists to surface."""
    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class InconsistentEligibility(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            if self.repeat == "seed17":
                io.skip("p0", "excluded this repeat")
                io.record("p1", {"v": 1.0})
            else:
                io.record("p0", {"v": 1.0})
                io.skip("p1", "excluded this repeat")
            return {}

    _, results, _ = harness(
        tmp_path,
        [InconsistentEligibility],
        units=roster,
        repeats=[Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)],
    )
    counts = attrition(results, roster, "inconsistent_eligibility", condition_index=0)
    assert counts == {"resolved": 2, "completed": 0, "ineligible": 0, "failed": 2}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_a_unit_skipped_in_every_repeat_is_ineligible(tmp_path: Path):
    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class AlwaysSkip(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.skip("p0", "excluded by design")
            io.record("p1", {"v": 1.0})
            return {}

    _, results, _ = harness(
        tmp_path,
        [AlwaysSkip],
        units=roster,
        repeats=[Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)],
    )
    counts = attrition(results, roster, "always_skip", condition_index=0)
    assert counts == {"resolved": 2, "completed": 1, "ineligible": 1, "failed": 0}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_skipped_in_one_repeat_and_unrecorded_in_another_is_failed(tmp_path: Path):
    """Neither skipped in every recording execution (so not `ineligible`, which needs a
    consistent design answer) nor recorded in every one (so not `completed` either) —
    the unit falls through to `failed`, the same place a step that silently drops a unit
    without skipping or recording it would land."""
    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class SkipThenSilentlyDrop(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.record("p1", {"v": 1.0})
            if self.repeat == "seed17":
                io.skip("p0", "excluded this repeat")
            # else: p0 is neither recorded nor skipped this repeat
            return {}

    _, results, _ = harness(
        tmp_path,
        [SkipThenSilentlyDrop],
        units=roster,
        repeats=[Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)],
    )
    counts = attrition(results, roster, "skip_then_silently_drop", condition_index=0)
    assert counts == {"resolved": 2, "completed": 1, "ineligible": 0, "failed": 1}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def _roster2() -> UnitList:
    return UnitList([Unit(key="u1"), Unit(key="u2")])


def _roster4() -> UnitList:
    return UnitList([Unit(key="u1"), Unit(key="u2"), Unit(key="u3"), Unit(key="u4")])


def test_a_fold_reports_its_partition_as_resolved_not_the_cohort():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    counts = attrition(results, _roster4(), "analyze", 0, members)
    assert counts == {"resolved": 4, "completed": 4, "ineligible": 0, "failed": 0}


def test_the_third_row_a_unit_missing_from_one_seed_of_its_fold():
    """The case a rewrite that groups by fold but forgets to intersect WITHIN the
    group gets wrong, while the fold-alone case still passes."""
    members = {"fold01": frozenset({"u1", "u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, members)
    assert counts["completed"] == 1
    assert counts["failed"] == 1


def test_without_folds_the_intersection_is_unchanged():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, None)
    assert counts["completed"] == 1
    assert counts["failed"] == 1


def test_the_identity_reconciles_under_a_fold():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    c = attrition(results, _roster4(), "analyze", 0, members)
    assert c["resolved"] == c["completed"] + c["ineligible"] + c["failed"]


def test_two_executions_sharing_a_repeat_label_are_merged_the_way_the_collapse_merges_them():
    """`collapse_repeats` accumulates `recorded` across executions sharing one
    repeat label; `attrition` kept only the last (`{label: r for r in ...}`),
    while its `labels` list still held the duplicate. The two readers of the
    same executions then disagreed — the collapsed table carrying a row for `u1`
    that the counts called `failed`, and `summarize_step` reporting an `n` whose
    `resolved` no longer equals `completed + ineligible + failed`.

    Built at unit level deliberately: `build_plan` emits one execution per
    (step, condition, repeat label) and `_check_no_collisions` keeps member
    labels unique, so a duplicate is unreachable through `cross_levels` today.
    The point is that the two functions agree by construction rather than by the
    caller never producing the input.
    """
    from publishable.stats import collapse_repeats

    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {"r": 1.0}}),
        _repeat_result("analyze", "seed01", 0, {"u2": {"r": 3.0}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, None)
    collapsed = collapse_repeats(results, "analyze", 0, None)

    assert set(collapsed) == {"u1", "u2"}  # the union, as the collapse merges it
    assert counts == {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0}
    # the row count and the completed count are the same fact, read two ways
    assert counts["completed"] == len(collapsed)
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_a_unit_skipped_in_every_repeat_of_its_own_fold_is_ineligible():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u2": {}}, skipped=frozenset({"u1"})),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    counts = attrition(results, _roster4(), "analyze", 0, members)
    assert counts == {"resolved": 4, "completed": 3, "ineligible": 1, "failed": 0}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_under_fold_times_seed_skipped_in_one_seed_and_recorded_in_the_other_is_failed():
    """The sharp edge: eligibility must be a consistent answer across every seed of
    a unit's own fold. Skipped in one seed and recorded in the other is neither a
    consistent skip (so not `ineligible`) nor a consistent completion (so not
    `completed`) — it falls through to `failed`, not `ineligible`."""
    members = {"fold01": frozenset({"u1", "u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u2": {}}, skipped=frozenset({"u1"})),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {}, "u2": {}}),
    ]
    counts = attrition(results, _roster2(), "analyze", 0, members)
    assert counts["completed"] == 1  # u2, consistently recorded in both of its seeds
    assert counts["ineligible"] == 0
    assert counts["failed"] == 1  # u1: skipped in one seed, recorded in the other
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_a_healthy_fold_run_does_not_trip_the_failure_fraction():
    """Before this fix, every unit outside a fold's partition counted as failed on
    that fold's execution, so a clean 10-fold run aborted on execution one."""
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}, "u2": {}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    assert _units_failed_anywhere(results, _roster4(), members) == set()


def test_a_genuinely_failing_fold_still_counts():
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {}}),  # u2 never settled
        _repeat_result("analyze", "fold02", 0, {"u3": {}, "u4": {}}),
    ]
    assert _units_failed_anywhere(results, _roster4(), members) == {"u2"}


def test_without_folds_the_union_is_unchanged():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {}, "u2": {}}),
    ]
    assert _units_failed_anywhere(results, _roster2(), None) == {"u2"}


def test_a_label_with_no_fold_component_raises_rather_than_falling_back():
    """A repeat label composed under a declared fold always carries one of its
    members (`cross_levels` guarantees it); a label that doesn't is a core
    invariant violation, not a case to silently subtract the whole roster for —
    that fallback is exactly the bug this task fixed."""
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    with pytest.raises(ContractError) as excinfo:
        _handed_keys("seed01", {"u1", "u2", "u3", "u4"}, members)
    assert excinfo.value.code == "E-RUN-FOLD-UNRESOLVED"


def test_execute_plan_hands_each_fold_execution_its_own_partition(tmp_path: Path):
    """A `repeat`-scoped step under a fold sees only its fold as `io.units`, with
    the complement as `io.units.train` — this is the wiring `_handed_keys` exists
    for, exercised through `execute_plan` rather than called directly."""
    roster = UnitList([Unit(key="u1"), Unit(key="u2"), Unit(key="u3"), Unit(key="u4")])
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}

    class SeeYourFold(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            return {
                "test_keys": ",".join(sorted(u.key for u in io.units)),
                "train_keys": ",".join(sorted(u.key for u in io.units.train)),
            }

    _, results, _ = harness(
        tmp_path,
        [SeeYourFold],
        units=roster,
        repeats=[Repeat("fold", "fold01", 0), Repeat("fold", "fold02", 0)],
        fold_members=members,
    )
    by_label = {r.execution.repeat_label: r for r in results}
    assert by_label["fold01"].returned == {"test_keys": "u1,u2", "train_keys": "u3,u4"}
    assert by_label["fold02"].returned == {"test_keys": "u3,u4", "train_keys": "u1,u2"}


def test_execute_plan_withholds_units_at_condition_and_run_scope_under_a_fold(
    tmp_path: Path,
):
    """There is no fold at `run` or `condition` scope — folds are repeats, and
    repeats haven't happened yet — so both scopes get `io.units == None`'s raise
    rather than the whole roster a condition-scoped fit could leak into."""
    roster = UnitList([Unit(key="u1"), Unit(key="u2"), Unit(key="u3"), Unit(key="u4")])
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}

    class TouchesUnitsAtRun(BaseStep):
        scope = "run"

        def run(self, cfg, io):
            _ = io.units
            return {}

    class TouchesUnitsAtCondition(BaseStep):
        scope = "condition"

        def run(self, cfg, io):
            _ = io.units
            return {}

    _, results, _ = harness(
        tmp_path,
        [TouchesUnitsAtRun, TouchesUnitsAtCondition],
        units=roster,
        repeats=[Repeat("fold", "fold01", 0), Repeat("fold", "fold02", 0)],
        fold_members=members,
    )
    statuses = {r.execution.step_name: r.status for r in results}
    errors = {r.execution.step_name: r.error or "" for r in results}
    assert statuses["touches_units_at_run"] == "failed"
    assert statuses["touches_units_at_condition"] == "failed"
    assert "E-STEP-UNITS-UNAVAILABLE" in errors["touches_units_at_run"]
    assert "E-STEP-UNITS-UNAVAILABLE" in errors["touches_units_at_condition"]


def test_execute_plan_without_a_fold_still_hands_the_whole_roster(tmp_path: Path):
    """`fold_members=None` must leave the no-fold path byte-for-byte identical:
    every execution still gets the whole roster, regardless of scope."""
    roster = UnitList([Unit(key="u1"), Unit(key="u2")])

    class TouchesUnitsAtCondition(BaseStep):
        scope = "condition"

        def run(self, cfg, io):
            return {"keys": ",".join(sorted(u.key for u in io.units))}

    _, results, _ = harness(
        tmp_path,
        [TouchesUnitsAtCondition],
        units=roster,
        repeats=[Repeat("seed", "seed17", 17)],
    )
    assert results[0].status == "completed"
    assert results[0].returned == {"keys": "u1,u2"}


def test_a_summary_step_under_a_fold_still_gets_the_full_roster(tmp_path: Path):
    """By summary time every fold has already run, so there is nothing left to
    leak — unlike `run`/`condition`, `summary` is deliberately not among the
    scopes `reference.md` § A `fold` repeat puts the units out of reach of the
    wider scopes names, and must keep receiving the whole roster unconditionally."""
    roster = UnitList([Unit(key="u1"), Unit(key="u2"), Unit(key="u3"), Unit(key="u4")])
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}

    class TouchesUnitsAtSummary(BaseStep):
        scope = "summary"

        def run(self, cfg, io):
            return {"keys": ",".join(sorted(u.key for u in io.units))}

    _, results, _ = harness(
        tmp_path,
        [TouchesUnitsAtSummary],
        units=roster,
        repeats=[Repeat("fold", "fold01", 0), Repeat("fold", "fold02", 0)],
        fold_members=members,
    )
    assert results[0].status == "completed"
    assert results[0].returned == {"keys": "u1,u2,u3,u4"}


def test_a_single_repeat_skip_is_still_ineligible(tmp_path: Path):
    """With one repeat, intersection over a single set is that set — unchanged behavior."""
    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class SkipOne(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.skip("p0", "excluded by design")
            io.record("p1", {"v": 1.0})
            return {}

    _, results, _ = harness(
        tmp_path, [SkipOne], units=roster, repeats=[Repeat("seed", "seed17", 17)]
    )
    counts = attrition(results, roster, "skip_one", condition_index=0)
    assert counts == {"resolved": 2, "completed": 1, "ineligible": 1, "failed": 0}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


def test_crossing_the_attrition_threshold_stops_the_run(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class Bad(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.record("p0", {"v": 1.0})  # 9 of 10 fail
            return {}

    class AlsoBad(Bad):
        # A distinct class, not `Bad` reused: `build_plan` now refuses the same class
        # object listed twice (E-STEP-NAME-COLLISION, "appears more than once"), so two
        # repeat-scoped executions with this behavior need two differently-named steps.
        pass

    _, results, _ = harness(
        tmp_path,
        [Bad, AlsoBad],
        units=roster,
        max_failed_fraction=0.2,
        repeats=[Repeat("seed", "s1", 1), Repeat("seed", "s2", 2)],
    )
    assert len(results) < 4, "the plan must stop rather than run to its end"
    assert results[-1].status in ("completed", "failed")


def test_staying_under_the_threshold_runs_to_the_end(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}") for i in range(10)])

    class MostlyGood(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            for u in list(io.units)[:9]:
                io.record(u.key, {"v": 1.0})
            return {}

    class AlsoMostlyGood(MostlyGood):
        # Same reasoning as `AlsoBad` above: `MostlyGood` reused verbatim would now be
        # refused by `build_plan` as a duplicate line, not just collide on `step_dir`.
        pass

    _, results, _ = harness(
        tmp_path,
        [MostlyGood, AlsoMostlyGood],
        units=roster,
        max_failed_fraction=0.2,
        repeats=[Repeat("seed", "s1", 1), Repeat("seed", "s2", 2)],
    )
    assert len(results) == 4


def test_a_raising_step_still_does_not_stop_the_run(tmp_path: Path):
    """S1's guarantee is intact — only the threshold stops a run."""
    roster = UnitList([Unit(key="p0")])

    class Boom2(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            raise ValueError("broken")

    class Fine(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.record("p0", {"v": 1.0})
            return {}

    _, results, _ = harness(tmp_path, [Boom2, Fine], units=roster, repeats=[Repeat("seed", "", 1)])
    assert [r.status for r in results] == ["failed", "completed"]


def test_attrition_with_no_units_declared_is_zeroed_not_a_crash(tmp_path: Path):
    """`units=None` (no `data.units`) is legal and must not divide by zero or disable the check."""
    _, results, _ = harness(tmp_path, [Load, Analyze], max_failed_fraction=0.2)
    assert attrition(results, None, "analyze", condition_index=0) == {
        "resolved": 0,
        "completed": 0,
        "ineligible": 0,
        "failed": 0,
    }


def test_a_condition_entry_carries_values_and_no_per_condition_key(tmp_path: Path):
    _, results, repeats = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
    )
    condition = doc["results"]["conditions"][0]
    assert condition["values"] == {}
    assert "per_condition" not in condition


def test_aggregated_sits_beside_per_repeat_without_altering_it(tmp_path: Path):
    """`per_repeat` stays exactly what the step returned; `aggregated` is a
    separately-computed sibling, never merged into it."""
    from publishable.stats import collapse_repeats, summarize_step

    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class Record(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            base = 0.2 if self.repeat == "seed17" else 0.4
            io.record("p0", {"pred": base})
            io.record("p1", {"pred": base * 5})
            return {"r": 0.5}

    _, results, repeats = harness(tmp_path, [Record], units=roster)
    collapsed = collapse_repeats(results, "record", condition_index=0)
    counts = attrition(results, roster, "record", condition_index=0)
    summary = summarize_step(collapsed, counts)
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
        aggregated={0: {"record": summary}},
    )
    condition = doc["results"]["conditions"][0]
    assert condition["per_repeat"]["record"] == {"seed17": {"r": 0.5}, "seed42": {"r": 0.5}}
    assert condition["aggregated"]["record"]["pred"]["basis"] == "units"
    assert condition["aggregated"]["record"]["pred"]["value"] == pytest.approx(0.9)
    assert condition["aggregated"]["record"]["pred"]["n"] == counts
    # `assemble_run_yaml` has no `counts` parameter at all: `summarize_step` already
    # embedded the counts as `n` inside each metric, and the condition entry has no
    # plain `n` sibling to `per_repeat` in the documented shape.
    assert "n" not in condition


def test_no_aggregated_means_no_aggregated_key(tmp_path: Path):
    """A caller that never computed anything over units gets no `aggregated` key
    rather than an empty or null placeholder."""
    _, results, repeats = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
    )
    condition = doc["results"]["conditions"][0]
    assert "aggregated" not in condition
    assert "n" not in condition


def _two_condition_results(tmp_path: Path, roster: "UnitList"):
    """Two conditions of the same step recording one unit at starkly different
    values — 1.0 and 100.0 — so pooling would be unmistakable rather than a
    rounding-sized difference."""

    class Record(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.record("p0", {"pred": 1.0 if self.condition == 0 else 100.0})
            return {}

    class P(BaseExperiment):
        pass

    P.steps = [Record]
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    plan = build_plan(
        P(), conditions=[(0, "c0"), (1, "c1")], repeat_labels=[r.label for r in repeats]
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan, run_dir=run_dir, input_dir=tmp_path / "input",
        cfgs={0: Config({"parameters": {}}), 1: Config({"parameters": {}})},
        repeats=repeats, digest="sha256:abc", units=roster,
    )
    return results, repeats


def test_aggregated_is_scoped_per_condition_not_shared(tmp_path: Path):
    from publishable.stats import collapse_repeats, summarize_step

    roster = UnitList([Unit(key="p0")])
    results, repeats = _two_condition_results(tmp_path, roster)

    aggregated = {}
    for index in (0, 1):
        collapsed = collapse_repeats(results, "record", condition_index=index)
        counts = attrition(results, roster, "record", condition_index=index)
        aggregated[index] = {"record": summarize_step(collapsed, counts)}

    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
        aggregated=aggregated,
    )
    conds = doc["results"]["conditions"]
    assert conds[0]["aggregated"]["record"]["pred"]["value"] == 1.0
    assert conds[1]["aggregated"]["record"]["pred"]["value"] == 100.0
    assert conds[0]["aggregated"] is not conds[1]["aggregated"]

    import yaml

    dumped = yaml.safe_dump(doc, sort_keys=False)
    assert "&id" not in dumped and "*id" not in dumped


def test_a_condition_absent_from_aggregated_gets_an_empty_mapping(tmp_path: Path):
    from publishable.stats import collapse_repeats, summarize_step

    roster = UnitList([Unit(key="p0")])
    results, repeats = _two_condition_results(tmp_path, roster)

    collapsed = collapse_repeats(results, "record", condition_index=0)
    counts = attrition(results, roster, "record", condition_index=0)
    aggregated = {0: {"record": summarize_step(collapsed, counts)}}  # nothing for condition 1

    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
        aggregated=aggregated,
    )
    conds = doc["results"]["conditions"]
    assert conds[0]["aggregated"]["record"]["pred"]["value"] == 1.0
    assert conds[1]["aggregated"] == {}


def test_attrition_is_scoped_per_condition(tmp_path: Path):
    roster = UnitList([Unit(key="p0"), Unit(key="p1")])

    class Record(BaseStep):
        scope = "repeat"

        def run(self, cfg, io):
            io.record("p0", {"v": 1.0})
            if self.condition == 1:
                io.record("p1", {"v": 1.0})  # only condition 1 completes p1
            return {}

    class P(BaseExperiment):
        pass

    P.steps = [Record]
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    plan = build_plan(
        P(), conditions=[(0, "c0"), (1, "c1")], repeat_labels=[r.label for r in repeats]
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan, run_dir=run_dir, input_dir=tmp_path / "input",
        cfgs={0: Config({"parameters": {}}), 1: Config({"parameters": {}})},
        repeats=repeats, digest="sha256:abc", units=roster,
    )
    assert attrition(results, roster, "record", condition_index=0)["completed"] == 1
    assert attrition(results, roster, "record", condition_index=1)["completed"] == 2


def test_attrition_requires_condition_index():
    with pytest.raises(TypeError):
        attrition([], None, "analyze")  # type: ignore[call-arg]


BASE_PARAMS = {"parameters": {"analysis": {"method": "pearson", "min_samples": 30}}}


def run_two_conditions(tmp_path: Path, step_cls):
    """Two conditions sweeping `analysis.method` over pearson/spearman, each with
    its own `Config` built by `resolve_condition_cfg`, plus the wide `Config`
    `resolve_wide_cfg` builds for `run`/`summary` scope, where that path has no
    single value."""

    class P(BaseExperiment):
        pass

    P.steps = [step_cls]
    conditions = [(0, "pearson"), (1, "spearman")]
    plan = build_plan(P(), conditions=conditions, repeat_labels=[""])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    cfgs = {
        0: resolve_condition_cfg(BASE_PARAMS, {"analysis.method": "pearson"}),
        1: resolve_condition_cfg(BASE_PARAMS, {"analysis.method": "spearman"}),
        -1: resolve_wide_cfg(BASE_PARAMS, {"analysis.method"}),
    }
    return execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfgs=cfgs,
        repeats=[Repeat("seed", "", 17)],
        digest="sha256:abc",
    )


def test_each_condition_sees_its_own_parameter_value(tmp_path: Path):
    seen = []

    class Reads(BaseStep):
        def run(self, cfg, io):
            seen.append(cfg.parameters.analysis.method)
            return {}

    run_two_conditions(tmp_path, Reads)
    assert sorted(seen) == ["pearson", "spearman"]


def test_a_condition_scoped_step_also_sees_its_own_value(tmp_path: Path):
    """Same guarantee as the `repeat`-scoped case above, but for `condition`
    scope — a different branch of `build_plan` and a different `step_dir_for`
    path, so the `cfgs[condition_index]` lookup needs its own proof."""
    seen = []

    class Reads(BaseStep):
        scope = "condition"

        def run(self, cfg, io):
            seen.append(cfg.parameters.analysis.method)
            return {}

    run_two_conditions(tmp_path, Reads)
    assert sorted(seen) == ["pearson", "spearman"]


def test_a_run_scoped_step_cannot_read_a_swept_parameter(tmp_path: Path):
    class Wide(BaseStep):
        scope = "run"

        def run(self, cfg, io):
            return {"m": cfg.parameters.analysis.method}

    results = run_two_conditions(tmp_path, Wide)
    failed = [r for r in results if r.status == "failed"]
    assert failed and "E-STEP-SWEPT-PARAM" in (failed[0].error or "")


def test_a_summary_scoped_step_cannot_read_a_swept_parameter(tmp_path: Path):
    class Sum(BaseStep):
        scope = "summary"

        def run(self, cfg, io):
            return {"m": cfg.parameters.analysis.method}

    results = run_two_conditions(tmp_path, Sum)
    failed = [r for r in results if r.status == "failed"]
    assert failed and "E-STEP-SWEPT-PARAM" in (failed[0].error or "")


@pytest.mark.parametrize("scope", ["run", "condition", "repeat", "summary"])
def test_an_unswept_path_reads_normally_at_every_scope(tmp_path: Path, scope: str):
    """Only the swept paths are withheld; the rest is ordinary, at every scope —
    the negative that proves the check is conditioned on being swept, not on
    scope alone."""

    class Reads(BaseStep):
        def run(self, cfg, io):
            return {"n": cfg.parameters.analysis.min_samples}

    Reads.scope = scope
    results = run_two_conditions(tmp_path, Reads)
    assert all(r.status == "completed" for r in results)


def test_per_condition_cfgs_are_not_the_same_object(tmp_path: Path):
    """`cfg0 is not cfg1` alone would pass even if both shared the same nested
    `analysis` dict underneath — that aliasing is exactly how an earlier defect
    in this project first showed itself. Assert the deep-copy actually happened,
    and that the shared `BASE_PARAMS` fixture survives both calls untouched."""
    before = copy.deepcopy(BASE_PARAMS)
    cfg0 = resolve_condition_cfg(BASE_PARAMS, {"analysis.method": "pearson"})
    cfg1 = resolve_condition_cfg(BASE_PARAMS, {"analysis.method": "spearman"})
    assert cfg0 is not cfg1
    assert cfg0.raw["parameters"]["analysis"] is not cfg1.raw["parameters"]["analysis"]
    assert cfg0.parameters.analysis.method == "pearson"
    assert cfg1.parameters.analysis.method == "spearman"
    assert BASE_PARAMS == before


def test_resolve_wide_cfg_plants_the_marker_even_when_the_parent_is_absent(tmp_path: Path):
    """`resolve_wide_cfg` must fail in the safe direction: if a swept path's
    parent doesn't already exist in `base`, the marker still has to be
    planted, not skipped. Skipping it would leave the value readable at
    `run`/`summary` scope — exactly the wrong value for every condition but
    one, handed over silently instead of refused."""
    cfg = resolve_wide_cfg({"parameters": {}}, {"analysis.method"})
    with pytest.raises(ContractError) as excinfo:
        _ = cfg.parameters.analysis.method
    assert excinfo.value.code == "E-STEP-SWEPT-PARAM"


def test_execute_plan_raises_explicitly_when_a_cfg_is_missing(tmp_path: Path):
    """A condition index absent from `cfgs` is not a step failing — it is core
    having built an inconsistent plan — so it must not be swallowed as a
    per-execution failure, and the error must name what's missing rather than
    surfacing as a bare `KeyError`."""

    class Analyze(BaseStep):
        def run(self, cfg, io):
            return {}

    class P(BaseExperiment):
        pass

    P.steps = [Analyze]
    plan = build_plan(P(), conditions=[(0, None)], repeat_labels=[""])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    with pytest.raises(ContractError) as excinfo:
        execute_plan(
            plan=plan,
            run_dir=run_dir,
            input_dir=tmp_path / "input",
            cfgs={},  # missing key 0
            repeats=[Repeat("seed", "", 17)],
            digest="sha256:abc",
        )
    assert excinfo.value.code == "E-RUN-CFG-MISSING"
    assert "0" in str(excinfo.value)


def test_io_conditions_is_ascending_by_index_whatever_the_plan_order(tmp_path: Path):
    """`io.conditions` is a documented `summary`-scope read surface, and nothing in
    `reference.md` says the list is unordered — so it is ordered.

    Derived from the plan, it used to follow first appearance. With ≥1
    condition-scope step those executions sit ahead of every repeat and the order
    happens to be ascending; with **zero** condition-scope steps — a legal
    pipeline — the first mention of each index comes from the repeat executions,
    whose order `order: randomized` shuffles. A summary step building a comparison
    table would then emit rows in an order set by an RNG draw. The plan here is
    reversed rather than shuffled: a fixed permutation nothing about ordering
    accidentally satisfies.
    """
    seen: list[list[tuple[int, str | None]]] = []

    class Sum(BaseStep):
        scope = "summary"

        def run(self, cfg, io):
            seen.append(io.conditions)
            return {}

    class P(BaseExperiment):
        pass

    P.steps = [Analyze, Sum]
    repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    conditions = [(0, "a"), (1, "b"), (2, "c")]
    plan = build_plan(P(), conditions=conditions, repeat_labels=[r.label for r in repeats])
    repeat_executions = [e for e in plan if e.scope == "repeat"]
    others = [e for e in plan if e.scope != "repeat"]
    plan = list(reversed(repeat_executions)) + others

    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfgs={i: Config({"parameters": {}}) for i in (-1, 0, 1, 2)},
        repeats=repeats,
        digest="sha256:abc",
    )
    assert seen == [[(0, "a"), (1, "b"), (2, "c")]]


# --- H3a task 9: `n` gains `effective` under `data.units.weight_by` ------------

# Five units, weighted unevenly, four of them completed. The weights are `str`
# because `units._from_table` builds every attribute through `csv.DictReader`,
# which is the shape a real roster's weight column has — `stats.kish_effective_n`
# gates and parses them itself.
#
# Kish over the COMPLETED four is (1+1+1+3)² / (1+1+1+9) = 36/12 = exactly 3.0,
# with no float slack; over all five RESOLVED it is 16²/112 = 2.2857…, and over
# the ineligible-included-but-heaviest-dropped set nothing else lands on 3.0. So
# the number, not merely the key's presence, is what these tests assert.
_WEIGHTS = {"p0": "1", "p1": "1", "p2": "1", "p3": "3", "p4": "10"}
_KISH_COMPLETED = 3.0
_KISH_RESOLVED = 256 / 112


class RecordFourSkipOne(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        for u in list(io.units)[:4]:
            io.record(u.key, {"v": 1.0})
        io.skip("p4", "by design")
        return {}


def _weighted_harness(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}") for i in range(5)])
    _, results, _ = harness(tmp_path, [RecordFourSkipOne], units=roster)
    return roster, results


def test_n_has_no_effective_key_without_weight_by(tmp_path: Path):
    """The regression. `reference.md` § The three-part `n`: each part is "present
    only when it applies so a design that never skips reads as it always did" —
    so a run that never weights must produce an `n` of exactly the four parts it
    always had, not one with a fifth key holding a stand-in value."""
    roster, results = _weighted_harness(tmp_path)
    counts = attrition(results, roster, "record_four_skip_one", condition_index=0)
    assert counts == {"resolved": 5, "completed": 4, "ineligible": 1, "failed": 0}
    assert "effective" not in counts


def test_n_gains_effective_under_a_weighted_design(tmp_path: Path):
    """Kish's effective size over the units the interval is computed from — the
    COMPLETED ones, which is why the fixture's heaviest unit is ineligible: over
    all five resolved units the answer would be 2.2857, and over four equal ones
    4.0."""
    roster, results = _weighted_harness(tmp_path)
    counts = attrition(
        results, roster, "record_four_skip_one", condition_index=0, weights=_WEIGHTS
    )
    assert counts["effective"] == pytest.approx(_KISH_COMPLETED)
    assert counts["effective"] != pytest.approx(_KISH_RESOLVED)
    # `effective` sits beside `completed` rather than replacing it: weights change
    # what each unit contributes, not how many there were (§ Weighted samples).
    assert counts["completed"] == 4
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]
    # The other four parts stay `int`. `reference.md` § Weighted samples prints
    # `{resolved: 240, completed: 228, failed: 12, effective: 191.4}` — three whole
    # numbers and one fractional — and widening the mapping's annotation to
    # `float` for `effective`'s sake must not turn `resolved` into `240.0` in
    # `run.yaml`. `5 == 5.0`, so nothing else here can see the difference.
    whole = ("resolved", "completed", "ineligible", "failed")
    assert all(isinstance(counts[k], int) for k in whole)
    assert isinstance(counts["effective"], float)


def test_every_attrition_return_site_agrees_about_effective(tmp_path: Path):
    """Three sites build `n` — no roster, no recording execution, and the
    accumulating return — and a weighted design must read the same way at all
    three. Two of the three report over an empty completed set, where Kish's size
    is 0.0: a run that weights and completed nothing has an effective size, and it
    is zero, not a missing key."""
    roster, results = _weighted_harness(tmp_path)
    no_roster = attrition(results, None, "record_four_skip_one", 0, weights=_WEIGHTS)
    no_recording = attrition(results, roster, "never_ran", 0, weights=_WEIGHTS)
    assert no_roster["effective"] == 0.0
    assert no_recording["effective"] == 0.0
    assert no_recording["failed"] == 5  # the site really is the no-recording one
    # And the mirrored control: without weights, neither site grows the key.
    assert "effective" not in attrition(results, None, "record_four_skip_one", 0)
    assert "effective" not in attrition(results, roster, "never_ran", 0)


# --- H3b task 8: `n` gains `clusters` under `data.units.cluster_by` ------------

# Five units in three clusters, a/a/b/b/c, with the single-unit cluster's unit
# `io.skip`ped by `RecordFourSkipOne` above. Three numbers that cannot be
# confused: 5 units resolved, 4 completed, 3 clusters resolved and **2** clusters
# completed. A roster of singleton clusters would make the cluster count and the
# unit count identical and no assertion below could tell the two apart.
_SITES = {"p0": "a", "p1": "a", "p2": "b", "p3": "b", "p4": "c"}


def _clustered_harness(tmp_path: Path):
    roster = UnitList([Unit(key=f"p{i}", attributes={"site": _SITES[f"p{i}"]}) for i in range(5)])
    _, results, _ = harness(tmp_path, [RecordFourSkipOne], units=roster)
    return roster, results


def test_n_has_no_clusters_key_without_cluster_by(tmp_path: Path):
    """The regression. `reference.md` § The three-part `n`: each part is "present
    only when it applies so a design that never skips reads as it always did" — so
    a run over a roster that happens to carry a cluster-shaped attribute, but
    declares no `cluster_by`, must produce an `n` of exactly the four parts it
    always had. The roster here is the clustered one, so this fails the moment
    `clusters` is computed from the data rather than from the declaration."""
    roster, results = _clustered_harness(tmp_path)
    counts = attrition(results, roster, "record_four_skip_one", condition_index=0)
    assert counts == {"resolved": 5, "completed": 4, "ineligible": 1, "failed": 0}
    assert "clusters" not in counts


def test_n_gains_clusters_under_a_clustered_design(tmp_path: Path):
    """The clusters of the COMPLETED units. `reference.md` § Statistical reporting
    gives `t_over_units_clustered` "df = clusters − 1", and § Clustered units
    reports the cluster count "as the effective sample size alongside the unit
    count" — a df is over the units the interval was computed from, which is the
    completed ones, so the two counts have to describe the same units.

    Three candidate answers on this fixture, and only one is right: 2 (the
    completed units' clusters), 3 (the resolved roster's clusters) and 4 (the
    completed unit count). All three are asserted."""
    roster, results = _clustered_harness(tmp_path)
    counts = attrition(
        results, roster, "record_four_skip_one", condition_index=0, clusters=_SITES
    )
    assert counts == {
        "resolved": 5,
        "completed": 4,
        "ineligible": 1,
        "failed": 0,
        "clusters": 2,
    }
    assert counts["clusters"] != 3  # not the resolved roster's clusters
    assert counts["clusters"] != counts["completed"]  # not the unit count
    # Every part stays `int`. § Clustered units' own example is
    # `n: {resolved: 300, completed: 300, failed: 0, clusters: 10}` — whole numbers
    # throughout — and `counts` being annotated `dict[str, float]` for Kish's sake
    # must not turn any of them into `300.0` in `run.yaml`. `10 == 10.0`, so only
    # the rendered text (see `test_cli.py`) and this check can see the difference.
    assert all(isinstance(v, int) for v in counts.values())


def test_every_attrition_return_site_agrees_about_clusters(tmp_path: Path):
    """Three sites build `n` — no roster, no recording execution, and the
    accumulating return — and a clustered design must read the same way at all
    three. Two of them report over an empty completed set, where the cluster count
    is 0: a clustered run that completed nothing has a cluster count, and it is
    zero, not a missing key."""
    roster, results = _clustered_harness(tmp_path)
    no_roster = attrition(results, None, "record_four_skip_one", 0, clusters=_SITES)
    no_recording = attrition(results, roster, "never_ran", 0, clusters=_SITES)
    assert no_roster["clusters"] == 0
    assert no_recording["clusters"] == 0
    assert no_recording["failed"] == 5  # the site really is the no-recording one
    # And the mirrored control: without the mapping, neither site grows the key.
    assert "clusters" not in attrition(results, None, "record_four_skip_one", 0)
    assert "clusters" not in attrition(results, roster, "never_ran", 0)


def test_clusters_and_effective_are_independent_parts_of_n(tmp_path: Path):
    """A design can declare both, and each part arrives on its own declaration —
    § The three-part `n` joins them one at a time, "each present only when it
    applies". Kish's size over the completed four weighted 1/1/1/3 is exactly 3.0
    while their cluster count is 2, so neither figure can be standing in for the
    other."""
    roster, results = _clustered_harness(tmp_path)
    both = attrition(
        results,
        roster,
        "record_four_skip_one",
        0,
        weights=_WEIGHTS,
        clusters=_SITES,
    )
    assert both["clusters"] == 2
    assert both["effective"] == pytest.approx(_KISH_COMPLETED)
    assert "effective" not in attrition(results, roster, "record_four_skip_one", 0, clusters=_SITES)
    assert "clusters" not in attrition(results, roster, "record_four_skip_one", 0, weights=_WEIGHTS)

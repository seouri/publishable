from pathlib import Path

import pytest

from publishable import BaseExperiment, BaseStep
from publishable.config import Config
from publishable.errors import ContractError
from publishable.replication import Repeat
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import attrition, execute_plan
from publishable.scope import build_plan
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


def harness(tmp_path: Path, steps, *, units=None, repeats=None, max_failed_fraction=None):
    class P(BaseExperiment):
        pass

    P.steps = steps
    if repeats is None:
        repeats = [Repeat("seed", "seed17", 17), Repeat("seed", "seed42", 42)]
    plan = build_plan(P(), conditions=[(0, None)], repeat_labels=[r.label for r in repeats])
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "input").mkdir(parents=True, exist_ok=True)
    results = execute_plan(
        plan=plan,
        run_dir=run_dir,
        input_dir=tmp_path / "input",
        cfg=Config({"parameters": {}}),
        repeats=repeats,
        digest="sha256:abc",
        units=units,
        max_failed_fraction=max_failed_fraction,
    )
    return run_dir, results, repeats


def test_no_sweep_means_no_conditions_level(tmp_path: Path):
    run_dir, _, _ = harness(tmp_path, [Load, Analyze])
    assert (run_dir / "shared" / "load" / "cohort.json").is_file()
    assert not (run_dir / "conditions").exists()
    assert (run_dir / "seed17").is_dir()
    assert (run_dir / "seed42").is_dir()


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
            cfg=Config({"parameters": {}}),
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
        cfg=Config({"parameters": {}}),
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
    counts = attrition(results, roster)
    assert counts == {"resolved": 10, "completed": 7, "ineligible": 1, "failed": 2}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


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
    assert attrition(results, roster)["completed"] == 2


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
    counts = attrition(results, roster)
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
    counts = attrition(results, roster)
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
    counts = attrition(results, roster)
    assert counts == {"resolved": 2, "completed": 1, "ineligible": 0, "failed": 1}
    assert counts["resolved"] == counts["completed"] + counts["ineligible"] + counts["failed"]


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
    counts = attrition(results, roster)
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
    assert attrition(results, None) == {
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
    counts = attrition(results, roster)
    summary = summarize_step(collapsed, counts)
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
        aggregated={"record": summary},
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

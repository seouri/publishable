from pathlib import Path

import pytest

from publishable import BaseExperiment, BaseStep
from publishable.config import Config
from publishable.errors import ContractError
from publishable.replication import Repeat
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import execute_plan
from publishable.scope import build_plan


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


def harness(tmp_path: Path, steps):
    class P(BaseExperiment):
        pass

    P.steps = steps
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


def test_a_condition_entry_carries_values_and_no_per_condition_key(tmp_path: Path):
    _, results, repeats = harness(tmp_path, [Load, Analyze])
    doc = assemble_run_yaml(
        run_id="run_x", status="completed", config={"a": 1}, code_hash="sha256:c",
        parameters_hash="sha256:p", provenance={}, results=results, repeats=repeats,
    )
    condition = doc["results"]["conditions"][0]
    assert condition["values"] == {}
    assert "per_condition" not in condition

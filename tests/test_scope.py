import pytest

from publishable import BaseExperiment, BaseStep, ContractError
from publishable.scope import build_plan


class Load(BaseStep):
    scope = "run"

    def run(self, cfg, io): ...


class Fit(BaseStep):
    scope = "condition"

    def run(self, cfg, io): ...


class Analyze(BaseStep):
    scope = "repeat"

    def run(self, cfg, io): ...


class Compare(BaseStep):
    scope = "summary"

    def run(self, cfg, io): ...


class Pipeline(BaseExperiment):
    steps = [Load, Fit, Analyze, Compare]


def test_scope_decides_execution_count():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17", "seed42"])
    counts = {s: sum(1 for e in plan if e.step_name == s) for s in
              ("load", "fit", "analyze", "compare")}
    assert counts == {"load": 1, "fit": 1, "analyze": 2, "compare": 1}


def test_the_plan_is_ordered_run_then_conditions_then_summary():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert [e.scope for e in plan] == ["run", "condition", "repeat", "summary"]


def test_repeat_executions_carry_their_repeat_label():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17", "seed42"])
    labels = [e.repeat_label for e in plan if e.scope == "repeat"]
    assert labels == ["seed17", "seed42"]


def test_step_name_is_derived_from_the_module_style_class_name():
    plan = build_plan(Pipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert {e.step_name for e in plan} == {"load", "fit", "analyze", "compare"}


def test_an_unknown_scope_is_refused():
    class Bad(BaseStep):
        scope = "epoch"

        def run(self, cfg, io): ...

    class BadPipeline(BaseExperiment):
        steps = [Bad]

    with pytest.raises(ContractError) as e:
        build_plan(BadPipeline(), conditions=[(0, None)], repeat_labels=["seed17"])
    assert e.value.code == "E-STEP-SCOPE-UNKNOWN"


def test_derive_seed_is_stable_and_varies_with_purpose():
    step = Analyze()
    step._bind(condition=None, repeat="seed17", digest="sha256:abc", seed=17)
    a = step.derive_seed("optimizer-dev-split")
    b = step.derive_seed("optimizer-dev-split")
    c = step.derive_seed("other-split")
    assert a == b and a != c

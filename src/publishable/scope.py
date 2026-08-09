"""Derive the execution plan from declared scopes. docs/reference.md § Step scope."""

import re
from dataclasses import dataclass

from publishable.base_experiment import BaseExperiment
from publishable.base_step import BaseStep
from publishable.errors import ContractError

SCOPES = ("run", "condition", "repeat", "summary")


def step_name(cls: type[BaseStep]) -> str:
    """`LoadCohort` → `load_cohort`; a generated `Step` uses its module name."""
    if cls.__name__ == "Step":
        return cls.__module__.rsplit(".", 1)[-1]
    return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()


@dataclass(frozen=True)
class Execution:
    step_cls: type[BaseStep]
    step_name: str
    scope: str
    condition_index: int | None
    condition_label: str | None
    repeat_label: str | None


def build_plan(
    experiment: BaseExperiment,
    conditions: list[tuple[int, str | None]],
    repeat_labels: list[str],
) -> list[Execution]:
    for cls in experiment.steps:
        if cls.scope not in SCOPES:
            raise ContractError(
                f"{cls.__name__} declares scope {cls.scope!r}; expected one of "
                + ", ".join(SCOPES),
                code="E-STEP-SCOPE-UNKNOWN",
            )
    plan: list[Execution] = []
    for cls in (c for c in experiment.steps if c.scope == "run"):
        plan.append(Execution(cls, step_name(cls), "run", None, None, None))
    for index, label in conditions:
        for cls in (c for c in experiment.steps if c.scope == "condition"):
            plan.append(Execution(cls, step_name(cls), "condition", index, label, None))
        for cls in (c for c in experiment.steps if c.scope == "repeat"):
            for repeat in repeat_labels:
                plan.append(Execution(cls, step_name(cls), "repeat", index, label, repeat))
    for cls in (c for c in experiment.steps if c.scope == "summary"):
        plan.append(Execution(cls, step_name(cls), "summary", None, None, None))
    return plan

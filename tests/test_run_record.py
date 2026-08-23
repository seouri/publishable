"""`run_record.assemble_run_yaml` at `summary` scope: an `Estimate` in `returned`
must be expanded into the documented record shape, not written verbatim.

See docs/reference.md § `Estimate`.
"""

from typing import Any

from publishable import BaseStep, Estimate
from publishable.replication import Repeat
from publishable.run_record import assemble_run_yaml
from publishable.runner import ExecutionResult
from publishable.scope import Execution


class _SummaryStep(BaseStep):
    scope = "summary"


def _minimal_kwargs(*, summary_returned: dict[str, Any]) -> dict[str, Any]:
    execution = Execution(
        step_cls=_SummaryStep,
        step_name="step03_site_model",
        scope="summary",
        condition_index=None,
        condition_label=None,
        repeat_label=None,
    )
    result = ExecutionResult(
        execution=execution,
        status="completed",
        started_at="2026-08-10T00:00:00Z",
        wall_seconds=0.1,
        returned=summary_returned,
        error=None,
    )
    return {
        "run_id": "run_x",
        "status": "completed",
        "config": {"a": 1},
        "code_hash": "sha256:c",
        "parameters_hash": "sha256:p",
        "provenance": {},
        "results": [result],
        "repeats": [Repeat(kind="seed", label="seed42", seed=42)],
    }


def test_a_summary_estimate_is_recorded_as_reported():
    """`reference.md` § `Estimate`: "`reported: true` is the whole mechanism, and
    it is an attribution rather than an endorsement." Without it, an author's
    interval and one core derived from the unit table are indistinguishable in
    the record, which the document calls the worse of the two situations."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055], n=612, method="mixed model, REML")
    doc = assemble_run_yaml(**_minimal_kwargs(summary_returned={"site_adjusted_delta": est}))
    entry = doc["results"]["summary"]["step03_site_model"]["site_adjusted_delta"]
    assert entry == {
        "value": 0.031,
        "reported": True,
        "ci95": [0.008, 0.055],
        "n": 612,
        "method": "mixed model, REML",
    }


def test_a_bare_value_beside_an_estimate_stays_bare():
    """The documented example returns `converged: True` alongside, and it is not
    wrapped: a value with no interval makes no attribution claim, so there is
    nothing for `reported` to attribute."""
    doc = assemble_run_yaml(
        **_minimal_kwargs(summary_returned={"delta": Estimate(value=0.031), "converged": True})
    )
    summary = doc["results"]["summary"]["step03_site_model"]
    assert summary["converged"] is True


def test_absent_estimate_fields_are_written_as_null():
    """Unlike the comparison blocks, whose absent keys mean no comparison was
    made, a summary entry always exists and its fields are simply unset. A
    reader comparing two summary blocks should not have to tell "no interval"
    from "a key I forgot to look for"."""
    doc = assemble_run_yaml(**_minimal_kwargs(summary_returned={"d": Estimate(value=0.031)}))
    entry = doc["results"]["summary"]["step03_site_model"]["d"]
    assert entry == {"value": 0.031, "reported": True, "ci95": None, "n": None, "method": None}


# ===========================================================================
# H9b task 6 — `attempts` is a count of ledger records (design Decision 6).
# ===========================================================================


class _RepeatStep(BaseStep):
    scope = "repeat"


def _repeat_execution(*, condition_index: int, repeat_label: str) -> Execution:
    return Execution(
        step_cls=_RepeatStep,
        step_name="step01_summarize_units",
        scope="repeat",
        condition_index=condition_index,
        condition_label=f"c{condition_index}",
        repeat_label=repeat_label,
    )


def _repeat_kwargs() -> dict[str, Any]:
    """Two repeat executions of one step, in two conditions: the shape
    `attempts` is reported per, and the shape a per-step counter could not
    tell apart."""
    results = [
        ExecutionResult(
            execution=_repeat_execution(condition_index=index, repeat_label="seed42"),
            status="completed",
            started_at="2026-08-10T00:00:00Z",
            wall_seconds=0.1,
            returned={},
            error=None,
        )
        for index in (0, 1)
    ]
    return {
        "run_id": "run_x",
        "status": "completed",
        "config": {"a": 1},
        "code_hash": "sha256:c",
        "parameters_hash": "sha256:p",
        "provenance": {},
        "results": results,
        "repeats": [Repeat(kind="seed", label="seed42", seed=42)],
    }


def _attempts_of(doc: dict[str, Any]) -> list[int]:
    return [
        cond["steps"]["step01_summarize_units"]["seed42"]["attempts"]
        for cond in doc["execution"]["conditions"]
    ]


def test_attempts_defaults_to_one_when_no_mapping_is_given():
    """The `None` branch — every caller but `resume` — writes what this record
    has always carried. Asserted rather than argued, because "byte-identical
    for `run`" is the whole basis on which H9b calls this change additive."""
    assert _attempts_of(assemble_run_yaml(**_repeat_kwargs())) == [1, 1]


def test_attempts_is_the_given_count_per_triple():
    """A triple that ran twice reports `2` while its neighbour reports `1`.

    Both arms in one assertion on purpose: a `2` alone passes for a build that
    writes the same count everywhere, which is exactly what the `1` literal
    this replaces did. The mapping is keyed on the full triple — a build
    keying on the step name would give both conditions the same answer.
    """
    doc = assemble_run_yaml(
        **_repeat_kwargs(),
        attempts={("step01_summarize_units", 0, "seed42"): 2},
    )
    assert _attempts_of(doc) == [2, 1]


def test_attempts_falls_back_to_one_for_a_triple_the_mapping_omits():
    """Unreachable through `resume` — a result is either reconstituted from a
    record or produced by an execution that wrote one — and pinned anyway,
    because the alternative is a raise sited AFTER the plan ran, which loses
    every execution's record to an exception. Stated as behaviour rather than
    left to a comment nobody can check."""
    doc = assemble_run_yaml(**_repeat_kwargs(), attempts={})
    assert _attempts_of(doc) == [1, 1]

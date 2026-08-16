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

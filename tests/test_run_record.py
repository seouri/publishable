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


# --- persisted-findings task 3: `assemble_run_yaml`'s new `findings` block --


def test_findings_are_recorded_in_order_with_all_four_fields():
    """A run with findings carries them in the record, in the same order they
    arrived — `run_record` "assembles only", so it neither sorts, filters, nor
    re-derives what `Collector.disclosed()` already produced. Two entries,
    one of each level, so the level is asserted rather than assumed constant
    — Decision 2's whole point is that `level` is not always `"warning"`."""
    findings = [
        {
            "level": "warning",
            "code": "W-ENV-UNLOCKED",
            "path": "environment",
            "message": "no uv.lock found",
        },
        {
            "level": "error",
            "code": "E-INPUT-CHANGED",
            "path": "data.input_dir",
            "message": "1 path changed since the manifest was built",
        },
    ]
    doc = assemble_run_yaml(**_repeat_kwargs(), findings=findings)
    assert doc["findings"] == findings


def test_a_clean_run_has_no_findings_key_at_all():
    """`absent, not null` (Decision 2): no `findings:` key on a clean run —
    never `findings: []`, which would claim a disclosure was checked for and
    found none. This is the rule `weighted_by` and `unevaluable` already
    follow.

    Both the omitted-argument default and an explicit empty list take this
    path, since a caller with nothing to disclose has no reason to build one
    over the other.
    """
    assert "findings" not in assemble_run_yaml(**_repeat_kwargs())
    assert "findings" not in assemble_run_yaml(**_repeat_kwargs(), findings=[])


def test_findings_survive_a_yaml_round_trip():
    """The entries are written with `yaml.safe_dump` (`cli.py`'s own call),
    so a round trip through it must reproduce the same list of plain dicts —
    proving the block is made of exactly the scalars `yaml.safe_dump` and
    `yaml.safe_load` agree on, nothing richer that would silently degrade."""
    import yaml

    findings = [
        {
            "level": "warning",
            "code": "W-STATS-COLUMN-THIN",
            "path": "limits.min_reported_n",
            "message": "condition 0, step 'x': recorded column 'y' carries a number for 8 unit(s)",
        },
    ]
    doc = assemble_run_yaml(**_repeat_kwargs(), findings=findings)
    round_tripped = yaml.safe_load(yaml.safe_dump(doc, sort_keys=False))
    assert round_tripped["findings"] == findings

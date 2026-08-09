import math

import pytest

from publishable.stats import collapse_repeats, mean_of, summarize_step, t_over_units


def _result(repeat_label, rows, *, step_name="analyze", scope="repeat"):
    """An ExecutionResult carrying rows, as execute_plan would produce."""
    from publishable.runner import ExecutionResult
    from publishable.scope import Execution

    class _Step:
        pass

    ex = Execution(
        step_cls=_Step,  # type: ignore[arg-type]
        step_name=step_name,
        scope=scope,
        condition_index=0,
        condition_label=None,
        repeat_label=repeat_label,
    )
    return ExecutionResult(
        execution=ex,
        status="completed",
        started_at="2026-08-09T00:00:00Z",
        wall_seconds=0.0,
        returned={},
        error=None,
        recorded=frozenset(r["unit"] for r in rows),
        skipped=frozenset(),
        rows=tuple(rows),
    )


def test_collapse_averages_a_unit_across_repeats():
    results = [
        _result("seed17", [{"unit": "p0", "pred": 0.2}, {"unit": "p1", "pred": 1.0}]),
        _result("seed42", [{"unit": "p0", "pred": 0.4}, {"unit": "p1", "pred": 2.0}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed["p0"]["pred"] == pytest.approx(0.3)
    assert collapsed["p1"]["pred"] == pytest.approx(1.5)


def test_collapse_drops_a_unit_not_recorded_in_every_repeat():
    """A unit present in some repeats and not others must not enter the average on
    a different number of observations than its neighbours — the same intersection
    `runner.attrition` takes for `completed`, and for the same reason: the `n`
    reported beside this table's interval must not undercount what actually went
    into it."""
    results = [
        _result("seed17", [{"unit": "p0", "pred": 1.0}, {"unit": "p1", "pred": 1.0}]),
        _result("seed42", [{"unit": "p0", "pred": 3.0}]),  # p1 missing this repeat
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed == {"p0": {"pred": 2.0}}
    assert "p1" not in collapsed


def test_collapse_ignores_other_steps_and_non_repeat_scopes():
    results = [_result("seed17", [{"unit": "p0", "pred": 0.2}])]
    assert collapse_repeats(results, "some_other_step", condition_index=0) == {}
    condition_scoped = [
        _result(None, [{"unit": "p0", "pred": 9.0}], step_name="analyze", scope="condition")
    ]
    assert collapse_repeats(condition_scoped, "analyze", condition_index=0) == {}


def test_collapse_drops_a_bool_column_rather_than_averaging_it():
    results = [
        _result("seed17", [{"unit": "p0", "flag": True}]),
        _result("seed42", [{"unit": "p0", "flag": False}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert "flag" not in collapsed.get("p0", {})


def test_collapse_never_pools_across_conditions():
    """Core aggregates within each condition and never pools across conditions,
    which would be meaningless (`reference.md` § Statistical reporting). Two
    conditions recording the same unit key with a stark contrast — 1.0 vs.
    100.0 — must each collapse to their own true mean; a regression that pools
    them (e.g. dropping the `condition_index` filter) would land on something
    between the two, unmistakably wrong rather than off by a rounding error."""
    from publishable.runner import ExecutionResult
    from publishable.scope import Execution

    def cond_result(condition_index, repeat_label, rows):
        class _Step:
            pass

        ex = Execution(
            step_cls=_Step,  # type: ignore[arg-type]
            step_name="analyze",
            scope="repeat",
            condition_index=condition_index,
            condition_label=f"cond{condition_index}",
            repeat_label=repeat_label,
        )
        return ExecutionResult(
            execution=ex, status="completed", started_at="2026-08-09T00:00:00Z",
            wall_seconds=0.0, returned={}, error=None,
            recorded=frozenset(r["unit"] for r in rows), skipped=frozenset(), rows=tuple(rows),
        )

    results = [
        cond_result(0, "seed17", [{"unit": "p0", "pred": 1.0}]),
        cond_result(0, "seed42", [{"unit": "p0", "pred": 1.0}]),
        cond_result(1, "seed17", [{"unit": "p0", "pred": 100.0}]),
        cond_result(1, "seed42", [{"unit": "p0", "pred": 100.0}]),
    ]
    assert collapse_repeats(results, "analyze", condition_index=0)["p0"]["pred"] == 1.0
    assert collapse_repeats(results, "analyze", condition_index=1)["p0"]["pred"] == 100.0


def test_collapse_requires_condition_index():
    """`condition_index` has no default: a caller that forgets it gets a
    `TypeError` at the call site, not a silently pooled mean."""
    with pytest.raises(TypeError):
        collapse_repeats([], "analyze")  # type: ignore[call-arg]


def test_a_recorded_column_is_basis_units_and_carries_an_interval():
    collapsed = {f"p{i}": {"pred": float(i)} for i in range(10)}
    out = summarize_step(
        collapsed, {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0}
    )
    assert out["pred"]["basis"] == "units"
    assert out["pred"]["n"] == {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0}
    assert out["pred"]["method"] == "t_over_units"
    low, high = out["pred"]["ci95"]
    assert low < out["pred"]["value"] < high


def test_a_single_completed_unit_reports_a_value_with_no_interval():
    """Answers the ledger's open question: one observation has no dispersion."""
    out = summarize_step(
        {"p0": {"pred": 1.0}}, {"resolved": 1, "completed": 1, "ineligible": 0, "failed": 0}
    )
    assert out["pred"]["value"] == 1.0
    assert out["pred"]["ci95"] is None
    assert out["pred"]["method"] is None


def test_a_non_numeric_column_is_not_summarized():
    out = summarize_step(
        {"p0": {"site": "a"}, "p1": {"site": "b"}},
        {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0},
    )
    assert "site" not in out


def test_a_bool_column_is_not_silently_averaged_to_a_proportion():
    out = summarize_step(
        {"p0": {"flag": True}, "p1": {"flag": False}},
        {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0},
    )
    assert "flag" not in out


def test_interval_matches_a_published_critical_value():
    """t(0.975, df=9) = 2.262. Ten values, mean 10, sample sd exactly 1."""
    values = [10 + d for d in (-1.5, -1.5, -0.5, -0.5, 0.0, 0.0, 0.5, 0.5, 1.5, 1.5)]
    n = len(values)
    sd = math.sqrt(sum((v - 10) ** 2 for v in values) / (n - 1))
    expected_half = 2.262 * sd / math.sqrt(n)
    iv = t_over_units(values)
    assert iv is not None
    assert iv.method == "t_over_units"
    assert abs((iv.high - iv.low) / 2 - expected_half) < 1e-3
    assert abs((iv.low + iv.high) / 2 - 10) < 1e-12


def test_interval_is_hand_checkable_on_a_tiny_dataset():
    """values [1, 2, 3, 4]: mean 2.5, sample sd sqrt(5/3)=1.29099,
    sem 0.645497, t(0.975, df=3)=3.182, half-width 2.0540."""
    iv = t_over_units([1.0, 2.0, 3.0, 4.0])
    assert iv is not None
    assert abs(iv.low - (2.5 - 2.0540)) < 1e-3
    assert abs(iv.high - (2.5 + 2.0540)) < 1e-3


def test_the_t_interval_is_wider_than_normal_and_converges():
    """The check that would catch shipping z by mistake."""
    from statistics import NormalDist

    def normal_half(vals):
        n = len(vals)
        m = sum(vals) / n
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
        return NormalDist().inv_cdf(0.975) * sd / math.sqrt(n)

    small = [float(i % 7) for i in range(8)]
    large = [float(i % 7) for i in range(4000)]
    small_iv, large_iv = t_over_units(small), t_over_units(large)
    assert small_iv is not None and large_iv is not None
    small_ratio = ((small_iv.high - small_iv.low) / 2) / normal_half(small)
    large_ratio = ((large_iv.high - large_iv.low) / 2) / normal_half(large)
    assert small_ratio > 1.15, "t must be materially wider than z at n=8"
    assert 1.0 < large_ratio < 1.002, "t must converge to z as n grows"


@pytest.mark.parametrize("values", [[], [3.0]])
def test_fewer_than_two_values_has_no_interval(values):
    """df = n - 1, so one value has no dispersion to describe."""
    assert t_over_units(values) is None


def test_zero_variance_yields_a_degenerate_but_real_interval():
    iv = t_over_units([5.0, 5.0, 5.0])
    assert iv is not None and iv.low == iv.high == 5.0


def test_mean_of_is_none_for_an_empty_sequence():
    assert mean_of([]) is None
    assert mean_of([1.0, 2.0]) == 1.5


def test_confidence_widens_the_interval():
    narrow = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.80)
    wide = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.99)
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)

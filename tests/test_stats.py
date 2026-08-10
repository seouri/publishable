import math

import pytest

from publishable.errors import ContractError
from publishable.stats import (
    UnitTable,
    collapse_repeats,
    handed_to,
    mean_of,
    percentile_over_units,
    resample_seed,
    summarize_step,
    t_over_units,
)


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


def _repeat_result(step, repeat_label, condition_index, rows_by_unit, skipped=frozenset()):
    """A repeat-scoped `ExecutionResult` from `{unit_key: {column: value}}`.

    The keyed form the fold tests read best in; `_result` above is the positional
    row-list form the earlier tests use. Both build the same object.

    `skipped` is additive and defaulted to `frozenset()` so every existing caller
    is unaffected: it declares which unit keys `io.skip` marked this execution,
    independent of `rows_by_unit` (a skipped unit has no row).
    """
    from publishable.runner import ExecutionResult
    from publishable.scope import Execution

    class _Step:
        pass

    rows = tuple({"unit": key, **cols} for key, cols in rows_by_unit.items())
    ex = Execution(
        step_cls=_Step,  # type: ignore[arg-type]
        step_name=step,
        scope="repeat",
        condition_index=condition_index,
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
        skipped=frozenset(skipped),
        rows=rows,
    )


def test_without_folds_a_unit_is_handed_to_every_repeat():
    assert handed_to("u1", ["seed01", "seed02"], None) == ["seed01", "seed02"]


def test_with_folds_a_unit_is_handed_only_to_its_own_fold():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    assert handed_to("u1", ["fold01", "fold02"], members) == ["fold01"]


def test_under_fold_times_seed_a_unit_is_handed_to_every_seed_of_its_fold():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    labels = ["fold01_seed01", "fold01_seed02", "fold02_seed01", "fold02_seed02"]
    assert handed_to("u1", labels, members) == ["fold01_seed01", "fold01_seed02"]


def test_a_fold_nested_in_a_batch_is_matched_by_token_not_by_prefix():
    """`batch01_fold02` is the reachable two-token shape with a fold inside another
    level — `batch` must be outermost (`_check_batch_is_outermost`) and the depth
    cap is two, so `batch01_fold02_seed03` cannot occur. A unit of `fold02` meets
    its own fold once per batch: batches average, folds concatenate. A refactor
    that parsed the label by prefix rather than by token would silently return
    nothing here and collapse to an empty table with no error."""
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    labels = ["batch01_fold01", "batch01_fold02", "batch02_fold01", "batch02_fold02"]
    assert handed_to("u2", labels, members) == ["batch01_fold02", "batch02_fold02"]
    assert handed_to("u1", labels, members) == ["batch01_fold01", "batch02_fold01"]


def test_the_collapsed_key_order_is_sorted_not_the_order_executions_arrive_in():
    """`summarize_step` derives column order from `collapsed.values()`, so a ragged
    table's `run.yaml` column order follows this dict's key order. Encounter order
    varies with `order: randomized` — the shuffle decides which execution is seen
    first — so the keys are sorted and two supply orders must agree."""
    rows = {
        "u30": {"score": 1.0, "late": 1.0},  # ragged: only some units carry `late`
        "u10": {"score": 2.0},
        "u20": {"score": 3.0, "late": 4.0},
        "u40": {"score": 4.0},
        "u50": {"score": 5.0},
    }
    forward = [_repeat_result("analyze", f"seed{i:02d}", 0, rows) for i in range(1, 3)]
    results = [
        _repeat_result("analyze", "seed01", 0, {k: rows[k] for k in ["u30", "u10", "u20"]}),
        _repeat_result("analyze", "seed01", 0, {k: rows[k] for k in ["u50", "u40"]}),
    ]
    assert list(collapse_repeats(forward, "analyze", 0)) == ["u10", "u20", "u30", "u40", "u50"]
    assert list(collapse_repeats(results, "analyze", 0)) == ["u10", "u20", "u30", "u40", "u50"]
    assert list(collapse_repeats(list(reversed(results)), "analyze", 0)) == list(
        collapse_repeats(results, "analyze", 0)
    )


def test_seeds_average_and_the_table_has_one_row_per_unit():
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {"score": 1.0}, "u2": {"score": 3.0}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {"score": 3.0}, "u2": {"score": 5.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, None)
    assert set(table) == {"u1", "u2"}
    assert table["u1"]["score"] == 2.0
    assert table["u2"]["score"] == 4.0


def test_folds_concatenate_rather_than_average():
    """Each unit is tested once per fold sweep, so the collapsed table is the
    union of the partitions — not an average that would divide by one."""
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    results = [
        _repeat_result("analyze", "fold01", 0, {"u1": {"score": 1.0}}),
        _repeat_result("analyze", "fold02", 0, {"u2": {"score": 5.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1", "u2"}  # both units present — the S2 rule dropped both
    assert table["u1"]["score"] == 1.0
    assert table["u2"]["score"] == 5.0


def test_fold_times_seed_averages_seeds_within_a_fold_then_concatenates():
    members = {"fold01": frozenset({"u1"}), "fold02": frozenset({"u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"score": 1.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"score": 3.0}}),
        _repeat_result("analyze", "fold02_seed01", 0, {"u2": {"score": 4.0}}),
        _repeat_result("analyze", "fold02_seed02", 0, {"u2": {"score": 6.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1", "u2"}
    assert table["u1"]["score"] == 2.0  # averaged WITHIN fold01, not concatenated
    assert table["u2"]["score"] == 5.0


def test_a_unit_missing_from_one_seed_of_its_fold_is_dropped():
    """The intersection still applies — within the repeats the unit was handed."""
    members = {"fold01": frozenset({"u1", "u2"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"score": 1.0}, "u2": {"score": 2.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"score": 3.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1"}


def test_two_units_per_fold_under_fold_times_seed_keeps_every_unit():
    """The widest shape check: 2 folds × 2 seeds, two units per fold. Every wrong
    collapse lands on a different number, so the table distinguishes all of them.
    A too-wide intersection gives `{}` (4 rows expected); the per-unit mean is
    2.0, distinct from 1.0 (first seed only), 3.0 (last write wins), 4.0 (summed)
    and 0.5 (averaged across folds, dividing by a fold count)."""
    members = {"fold01": frozenset({"u1", "u2"}), "fold02": frozenset({"u3", "u4"})}
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"s": 1.0}, "u2": {"s": 1.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"s": 3.0}, "u2": {"s": 3.0}}),
        _repeat_result("analyze", "fold02_seed01", 0, {"u3": {"s": 1.0}, "u4": {"s": 1.0}}),
        _repeat_result("analyze", "fold02_seed02", 0, {"u3": {"s": 3.0}, "u4": {"s": 3.0}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert len(table) == 4
    assert set(table) == {"u1", "u2", "u3", "u4"}
    assert all(row["s"] == 2.0 for row in table.values())


def test_a_unit_in_no_fold_partition_is_dropped_rather_than_admitted():
    """`handed_to` returns nothing for it, and an empty handed set must not pass
    the `all()`-over-nothing intersection as vacuously complete."""
    members = {"fold01": frozenset({"u1"})}
    results = [_repeat_result("analyze", "fold01", 0, {"u1": {"s": 1.0}, "stray": {"s": 9.0}})]
    table = collapse_repeats(results, "analyze", 0, members)
    assert set(table) == {"u1"}


def test_fold_members_defaults_to_none_and_leaves_the_s2_path_unchanged():
    """No caller passes `fold_members` yet; the default must be today's behaviour."""
    results = [
        _repeat_result("analyze", "seed01", 0, {"u1": {"score": 1.0}, "u2": {"score": 1.0}}),
        _repeat_result("analyze", "seed02", 0, {"u1": {"score": 3.0}}),
    ]
    assert collapse_repeats(results, "analyze", 0) == collapse_repeats(results, "analyze", 0, None)
    assert collapse_repeats(results, "analyze", 0) == {"u1": {"score": 2.0}}


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


def test_a_ragged_columns_n_completed_counts_only_units_carrying_it():
    """`finalize()` writes the union of recorded keys with nulls for columns a unit
    didn't carry, so a column recorded for only some completed units is a
    supported, ordinary shape — a metric recorded only for eligible-positive
    units, say. `n.completed` for that column must count the units that actually
    carry it, not the condition-wide `completed` figure: reporting `n.completed:
    10` beside a mean of one value is the exact incoherence `stats.py`'s own
    docstring rules out."""
    collapsed = {f"p{i}": {"pred": 1.0} for i in range(10)}
    collapsed["p0"]["rare"] = 5.0  # only one of ten units carries this column
    out = summarize_step(
        collapsed, {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0}
    )
    assert out["pred"]["n"] == {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0}
    assert out["rare"]["n"] == {"resolved": 10, "completed": 1, "ineligible": 0, "failed": 0}
    assert out["rare"]["ci95"] is None, "one value has no dispersion to describe"


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


def test_iteration_yields_one_row_per_unit():
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})
    assert [r["unit"] for r in t] == ["u1", "u2"]
    assert [r["pred"] for r in t] == [1.0, 2.0]


def test_column_access_returns_values_in_iteration_order():
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})
    assert list(t.pred) == [1.0, 2.0]


def test_len_counts_units():
    assert len(UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})) == 2


def test_columns_lists_the_recorded_columns():
    t = UnitTable({"u1": {"pred": 1.0, "truth": 0.0}})
    assert sorted(t.columns) == ["pred", "truth"]


def test_a_ragged_column_omits_the_missing_unit():
    """A unit with no value for a column is absent from it, not None — a mean over
    a column must not be diluted by units that never recorded it."""
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {}})
    assert list(t.pred) == [1.0]


def test_an_unknown_column_raises():
    t = UnitTable({"u1": {"pred": 1.0}})
    with pytest.raises(ContractError) as exc:
        _ = t.nope
    assert exc.value.code == "E-STEP-COLUMN-UNKNOWN"


def test_iteration_is_repeatable():
    t = UnitTable({"u1": {"pred": 1.0}})
    assert [r["unit"] for r in t] == [r["unit"] for r in t]


def test_a_column_named_columns_cannot_shadow_the_property():
    """`columns` is a real property, so normal attribute lookup finds it before
    `__getattr__` ever runs — a recorded column literally named "columns" cannot
    shadow it. The data isn't lost, only unreachable by attribute: it still shows
    up in row iteration."""
    t = UnitTable({"u1": {"columns": 1.0, "pred": 2.0}})
    assert sorted(t.columns) == ["columns", "pred"]
    assert [r["columns"] for r in t] == [1.0]


def test_underscore_prefixed_access_raises_attribute_error_not_contract_error():
    """Internal attribute access and pickle probes (`_anything`) must behave like
    ordinary missing attributes, not like a step author naming a bad column."""
    t = UnitTable({"u1": {"pred": 1.0}})
    with pytest.raises(AttributeError) as exc:
        _ = t._anything
    assert not isinstance(exc.value, ContractError)


def test_the_interval_brackets_the_point_estimate():
    values = [float(i) for i in range(50)]
    got = percentile_over_units(values, seed=7)
    assert got.low < sum(values) / len(values) < got.high


def test_it_names_its_method():
    assert percentile_over_units([float(i) for i in range(50)], seed=7).method == (
        "percentile_over_units"
    )


def test_the_same_seed_reproduces_the_interval():
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) == percentile_over_units(values, seed=7)


def test_a_different_seed_gives_a_different_interval():
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) != percentile_over_units(values, seed=99)


def test_it_is_invariant_to_row_order():
    """A bootstrap resamples with replacement, so the order units arrive in must
    not change the interval — only the multiset of values may."""
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) == percentile_over_units(
        list(reversed(values)), seed=7
    )


def test_it_converges_toward_the_analytic_interval_for_a_mean():
    """Verified against something other than itself: for a mean over many units the
    percentile interval should sit close to Student's t, which is computed by
    entirely different code."""
    values = [float(i % 10) for i in range(400)]
    boot = percentile_over_units(values, seed=7, draws=4000)
    analytic = t_over_units(values)
    assert abs(boot.low - analytic.low) < 0.15
    assert abs(boot.high - analytic.high) < 0.15


def test_one_value_has_no_interval():
    assert percentile_over_units([1.0], seed=7) is None


def test_resample_seed_depends_on_the_digest():
    assert resample_seed("a") != resample_seed("b")
    assert resample_seed("a") == resample_seed("a")

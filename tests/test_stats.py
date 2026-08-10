import math

import pytest

from publishable.errors import ContractError
from publishable.replication import resolve_repeats
from publishable.stats import (
    Interval,
    UnitTable,
    _percentile_ranks,
    collapse_repeats,
    handed_to,
    mean_of,
    min_honest_draws,
    paired_keys,
    percentile_of_derived,
    percentile_over_units,
    repeat_spread,
    resample_seed,
    summarize_step,
    t_over_units,
)


def cfg(repeats):
    """Local, rather than imported from `tests/test_replication.py` — the two
    test modules don't share fixtures across files."""
    return {"replication": {"repeats": repeats}}


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


def _results_for_batch_seed():
    """Labels resolved from `cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}])`
    at digest `"d"` — `batch01_seed87` and `batch01_seed93` under `batch01`,
    `batch02_seed87` and `batch02_seed93` under `batch02`; `seed87` pairs
    `batch01_seed87`/`batch02_seed87`, `seed93` the other pair. Values are chosen
    so the batch grouping and the seed grouping produce different member means,
    which a matching bug (equality instead of token membership) would collapse
    to `n == 0` per member rather than merely to the wrong number.
    """
    return [
        _repeat_result(
            "analyze", "batch01_seed87", 0, {"u1": {"score": 1.0}, "u2": {"score": 1.0}}
        ),
        _repeat_result(
            "analyze", "batch01_seed93", 0, {"u1": {"score": 3.0}, "u2": {"score": 3.0}}
        ),
        _repeat_result(
            "analyze", "batch02_seed87", 0, {"u1": {"score": 5.0}, "u2": {"score": 5.0}}
        ),
        _repeat_result(
            "analyze", "batch02_seed93", 0, {"u1": {"score": 7.0}, "u2": {"score": 7.0}}
        ),
    ]


def _results_for_folds():
    """Labels resolved from `cfg([{"kind": "fold", "k": 2}])` at digest `"d"`
    with `unit_count=4`: `fold01` and `fold02`."""
    return [
        _repeat_result("analyze", "fold01", 0, {"u1": {"score": 1.0}, "u2": {"score": 2.0}}),
        _repeat_result("analyze", "fold02", 0, {"u3": {"score": 3.0}, "u4": {"score": 4.0}}),
    ]


def _results_for_one_seed():
    """The label resolved from `cfg([{"kind": "seed", "n": 1}])` at digest `"d"`:
    a single member, `seed87`."""
    return [
        _repeat_result("analyze", "seed87", 0, {"u1": {"score": 1.0}, "u2": {"score": 5.0}}),
    ]


def test_one_entry_per_level_outer_to_inner():
    levels = resolve_repeats(cfg([{"kind": "batch", "n": 2}, {"kind": "seed", "n": 2}]), "d")
    spread = repeat_spread(
        _results_for_batch_seed(), "analyze", 0, levels, "score", keys={"u1", "u2"}
    )
    assert [e["kind"] for e in spread] == ["batch", "seed"]
    assert [e["n"] for e in spread] == [2, 2]
    assert all(e["std"] >= 0 for e in spread)
    # The batch grouping and the seed grouping cross the same four executions
    # differently, so a correct implementation gives them different numbers —
    # guarding against a matching bug that always groups by the leaf label.
    assert spread[0]["std"] != spread[1]["std"]


def test_a_fold_level_contributes_no_entry():
    """Each unit is in exactly one fold, so there is nothing to average across."""
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", unit_count=4)
    assert (
        repeat_spread(
            _results_for_folds(), "analyze", 0, levels, "score", keys={"u1", "u2", "u3", "u4"}
        )
        == []
    )


def test_a_fold_nested_with_another_level_is_omitted_entirely():
    """`fold x seed` would need the metric recomputed per fold slice to answer
    honestly; rather than report the seed level's figure alone as if that were
    the whole answer, the result is omitted entirely — a missing figure over a
    differently-computed one."""
    levels = resolve_repeats(
        cfg([{"kind": "fold", "k": 2}, {"kind": "seed", "n": 2}]), "d", unit_count=4
    )
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"score": 1.0}, "u2": {"score": 2.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"score": 3.0}, "u2": {"score": 4.0}}),
        _repeat_result("analyze", "fold02_seed01", 0, {"u3": {"score": 5.0}, "u4": {"score": 6.0}}),
        _repeat_result("analyze", "fold02_seed02", 0, {"u3": {"score": 7.0}, "u4": {"score": 8.0}}),
    ]
    assert (
        repeat_spread(results, "analyze", 0, levels, "score", keys={"u1", "u2", "u3", "u4"}) == []
    )


def test_a_single_member_level_reports_zero_spread_not_none():
    """One repeat has no dispersion; reporting 0.0 with n: 1 says that plainly,
    where omitting the entry would read as 'this level was not run'."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 1}]), "d")
    spread = repeat_spread(
        _results_for_one_seed(), "analyze", 0, levels, "score", keys={"u1", "u2"}
    )
    assert spread == [{"std": 0.0, "n": 1, "kind": "seed"}]


def test_no_replication_block_means_no_repeat_spread_at_all():
    """The anonymous single-seed level `resolve_repeats({}, ...)` synthesizes
    is an implementation detail of 'no repeats declared', not a design the
    user expressed — an ordinary run with no repeat structure must be
    unchanged, so it gets no `repeat_spread` at all, unlike a *declared*
    `{kind: seed, n: 1}` (the test above)."""
    levels = resolve_repeats({}, "d")
    results = [_repeat_result("analyze", "", 0, {"u1": {"score": 1.0}, "u2": {"score": 5.0}})]
    assert repeat_spread(results, "analyze", 0, levels, "score", keys={"u1", "u2"}) == []


def test_dispersion_is_computed_per_column_not_pooled():
    """A step recording two numeric columns (`pred` and `truth`) must not have
    them averaged together into one blended figure reported as the dispersion
    of both — `column` selects which one this call describes."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    results = [
        _repeat_result("analyze", "seed87", 0, {"u1": {"pred": 1.0, "truth": 100.0}}),
        _repeat_result("analyze", "seed93", 0, {"u1": {"pred": 3.0, "truth": 100.0}}),
    ]
    pred_spread = repeat_spread(results, "analyze", 0, levels, "pred", keys={"u1"})
    truth_spread = repeat_spread(results, "analyze", 0, levels, "truth", keys={"u1"})
    assert pred_spread[0]["std"] == pytest.approx(1.0)
    assert truth_spread[0]["std"] == pytest.approx(0.0)


def test_n_reflects_members_that_actually_contributed_a_mean():
    """A member with no matching rows for this column contributes nothing;
    `n` must describe the same set of numbers `std` was computed over, not the
    level's declared count."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    results = [
        _repeat_result("analyze", "seed87", 0, {"u1": {"score": 1.0}}),
        # seed93 recorded nothing for this step at all.
    ]
    spread = repeat_spread(results, "analyze", 0, levels, "score", keys={"u1"})
    assert spread == [{"std": 0.0, "n": 1, "kind": "seed"}]


def test_dispersion_reads_only_the_units_the_metric_rests_on():
    """`value` and `ci95` rest on `collapse_repeats`'s intersection — units
    recorded in every repeat they were handed. Reading every recorded row
    instead would let one unit's attrition masquerade as pipeline instability:
    here u1 is perfectly stable at 1.0 across both seeds and u2 recorded 100.0
    in one seed only, and the whole-table figure would be `std: 24.75` for a
    pipeline that did not move at all."""
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    results = [
        _repeat_result("analyze", "seed87", 0, {"u1": {"s": 1.0}, "u2": {"s": 100.0}}),
        _repeat_result("analyze", "seed93", 0, {"u1": {"s": 1.0}}),
    ]
    collapsed = collapse_repeats(results, "analyze", 0)
    assert set(collapsed) == {"u1"}  # u2 is not in the inference base
    spread = repeat_spread(results, "analyze", 0, levels, "s", keys=set(collapsed))
    assert spread == [{"std": 0.0, "n": 2, "kind": "seed"}]
    # What the unfiltered read reported, pinned so the confound cannot return.
    unfiltered = repeat_spread(results, "analyze", 0, levels, "s", keys={"u1", "u2"})
    assert unfiltered[0]["std"] == pytest.approx(24.75)


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


def test_the_pairing_is_the_intersection():
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}, "u3": {"m": 3.0}}
    against = {"u2": {"m": 1.0}, "u3": {"m": 1.0}, "u4": {"m": 1.0}}
    assert paired_keys(of, against, None) == ["u2", "u3"]


def test_the_union_and_either_side_alone_all_differ():
    """Pins the intersection specifically: three wrong answers are distinguishable."""
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}}
    against = {"u2": {"m": 1.0}, "u3": {"m": 1.0}}
    keys = paired_keys(of, against, None)
    assert keys == ["u2"]
    assert keys != sorted(set(of) | set(against))
    assert keys != sorted(of)
    assert keys != sorted(against)


def test_a_within_stratum_narrows_the_intersection():
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}}
    against = {"u1": {"m": 1.0}, "u2": {"m": 1.0}}
    assert paired_keys(of, against, {"u2"}) == ["u2"]


def test_the_result_is_sorted():
    of = {"u3": {"m": 1.0}, "u1": {"m": 1.0}}
    against = {"u1": {"m": 1.0}, "u3": {"m": 1.0}}
    assert paired_keys(of, against, None) == ["u1", "u3"]


def test_an_empty_allowed_set_yields_no_pairing():
    """An empty `allowed` is a real answer — nobody matched the stratum — and
    must not be confused with `None`, which means unrestricted."""
    of = {"u1": {"m": 1.0}}
    against = {"u1": {"m": 1.0}}
    assert paired_keys(of, against, set()) == []
    assert paired_keys(of, against, None) == ["u1"]


def test_a_recorded_column_is_basis_units_and_carries_an_interval():
    collapsed = {f"p{i}": {"pred": float(i)} for i in range(10)}
    out = summarize_step(collapsed, {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0})
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
    out = summarize_step(collapsed, {"resolved": 10, "completed": 10, "ineligible": 0, "failed": 0})
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


def test_a_derived_metric_is_reported_over_units():
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    out = summarize_step(
        collapsed,
        {"completed": 20},
        derived={"total": 190.0},
        seed=7,
        resample={"total": lambda units: sum(units.pred)},
    )
    assert out["total"]["basis"] == "units"
    assert out["total"]["method"] == "percentile_over_units"
    assert out["total"]["ci95"] is not None
    assert out["total"]["cohens_d"] is None


def test_a_derived_metric_with_no_resample_callable_reports_no_interval():
    """Reporting a point with no interval is honest; inventing one from a
    surrogate that isn't the metric itself is not — the rule this task's own
    escalation settled. `resample` absent (or lacking this key) means core
    cannot recompute `aggregate`, so `ci95` stays `null` rather than a
    fabricated width."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    out = summarize_step(collapsed, {"completed": 20}, derived={"total": 190.0}, seed=7)
    assert out["total"]["value"] == 190.0
    assert out["total"]["ci95"] is None
    assert out["total"]["method"] is None


def test_a_derived_key_colliding_with_a_recorded_column_is_refused():
    collapsed = {f"u{i}": {"r": float(i)} for i in range(5)}
    with pytest.raises(ContractError) as exc:
        summarize_step(collapsed, {"completed": 5}, derived={"r": 1.0}, seed=7)
    assert exc.value.code == "E-STEP-KEY-COLLISION"


def test_no_derived_metrics_leaves_the_output_unchanged():
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(5)}
    assert summarize_step(collapsed, {"completed": 5}) == summarize_step(
        collapsed, {"completed": 5}, derived=None, seed=7
    )


def test_a_correlation_like_derived_metrics_interval_reflects_its_own_scatter():
    """The test the surrogate construction would fail: two fixtures with almost
    the same Pearson `r` but very different sensitivity to which units are
    resampled. Fixture A's noise is spread evenly across every unit, so
    dropping or duplicating any one of them barely moves `r`. Fixture B's `y`
    is identical except at two points, which are the only reason `r` isn't
    ~0 — a bootstrap draw that resamples away one of them swings `r` hard.
    Recomputing `pearsonr` on each draw is the only way to see that
    difference; a proxy built from summed row values could not, because it
    never looks at the correlation at all."""
    from scipy import stats as scipy_stats

    n = 20
    collapsed_a = {f"u{i}": {"x": float(i), "y": float(i) + 0.5 * ((-1) ** i)} for i in range(n)}
    collapsed_b = {f"u{i}": {"x": float(i), "y": float(i)} for i in range(n)}
    collapsed_b["u0"]["y"] += 3.0
    collapsed_b[f"u{n - 1}"]["y"] -= 3.0

    def compute_r(units: UnitTable) -> float | None:
        r, _ = scipy_stats.pearsonr(units.x, units.y)
        return None if r != r else float(r)  # nan check without importing math here

    ra = compute_r(UnitTable(collapsed_a))
    rb = compute_r(UnitTable(collapsed_b))
    assert ra is not None and rb is not None
    assert abs(ra - rb) < 0.01  # nearly the same point estimate

    interval_a, _ = percentile_of_derived(collapsed_a, compute_r, seed=7, draws=500)
    interval_b, _ = percentile_of_derived(collapsed_b, compute_r, seed=7, draws=500)
    assert interval_a is not None and interval_b is not None
    width_a = interval_a.high - interval_a.low
    width_b = interval_b.high - interval_b.low
    assert width_b > width_a * 3  # the leverage points make B's interval much wider


def test_percentile_ranks_are_symmetric_at_the_default_draw_count():
    """The defect Task 4 already had once: an off-by-one on the upper rank.
    `_percentile_ranks` is the single copy both `percentile_over_units` and
    `percentile_of_derived` share, so pinning it directly catches an asymmetry
    reappearing in either without needing to drive 2000 draws through a whole
    resample to see it."""
    assert _percentile_ranks(2000, 0.95) == (49, 1949)


def test_percentile_ranks_collapse_at_tiny_draw_counts():
    """Pinned, not fixed: at 1 and 2 draws the two ranks coincide at 0, and at
    every count below 80 the lower rank is pinned to the sample minimum while
    the upper keeps shrinking — low-biased and too narrow. The ranks are
    arithmetic shared with `percentile_over_units`; the refusal to build an
    interval from them lives in `min_honest_draws`, which is the honest place
    for it."""
    assert _percentile_ranks(1, 0.95) == (0, 0)
    assert _percentile_ranks(2, 0.95) == (0, 0)
    assert _percentile_ranks(79, 0.95) == (0, 76)  # lower rank still the minimum
    assert _percentile_ranks(80, 0.95) == (1, 77)  # both ranks interior


def test_the_honest_draw_floor_is_where_both_ranks_go_interior():
    """80 at 95 %, and it tracks `confidence` rather than being a literal: the
    smallest n with `int(tail * n) >= 2`, which is exactly where the interval
    stops containing the sample minimum by construction."""
    assert min_honest_draws(0.95) == 80
    assert min_honest_draws(0.99) == 400
    lo, hi = _percentile_ranks(min_honest_draws(0.95), 0.95)
    assert lo > 0 and hi < min_honest_draws(0.95) - 1


def test_no_interval_is_built_from_too_few_surviving_draws():
    """The zero-width interval the review reproduced: two surviving draws gave
    `lo == hi`, so `run.yaml` carried `ci95: [6.0, 6.0], method:
    percentile_over_units` — a 95 % interval of width zero. Below the floor
    there is no interval, and the surviving count is still reported so the
    reader knows why."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}
    calls = {"n": 0}

    def survives_twice(units: UnitTable) -> float | None:
        calls["n"] += 1
        return 6.0 if calls["n"] <= 2 else None

    interval, used = percentile_of_derived(collapsed, survives_twice, seed=7, draws=100)
    assert interval is None
    assert used == 2


def test_an_interval_is_built_at_the_floor():
    """The other side of the same boundary: exactly `min_honest_draws()`
    survivors is enough, so the floor refuses too little rather than refusing
    everything short of `draws`."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}
    calls = {"n": 0}

    def survives_eighty(units: UnitTable) -> float | None:
        calls["n"] += 1
        return float(sum(units.pred)) if calls["n"] <= min_honest_draws() else None

    interval, used = percentile_of_derived(collapsed, survives_eighty, seed=7, draws=200)
    assert used == min_honest_draws()
    assert interval is not None
    assert interval.low < interval.high  # never zero-width


def test_a_resampled_draw_reports_the_real_unit_key_not_a_synthetic_index():
    """A bootstrap draw repeats units by construction — the whole point of
    resampling with replacement — so a template that legitimately reads
    `units.unit` (a per-unit lookup keyed by it, say) must see the real,
    possibly-repeated keys, not `0..n-1`. A synthetic `0..n-1` re-key would
    make every draw's keys distinct by construction, so at least one draw
    (out of five, with two real units to draw from) showing the *same* key
    twice is what a real re-key produces and a synthetic one never could —
    which is what this pins, rather than only checking the keys are drawn
    from the real roster."""
    collapsed = {"u0": {"x": 1.0}, "u1": {"x": 2.0}}
    seen: list[tuple[str, ...]] = []

    def compute(units: UnitTable) -> float | None:
        seen.append(tuple(units.unit))
        return float(sum(units.x))

    percentile_of_derived(collapsed, compute, seed=7, draws=5)
    assert seen  # `compute` ran at least once
    for keys in seen:
        assert set(keys) <= {"u0", "u1"}
        assert len(keys) == 2  # one row per unit in the roster, per draw
    # The repetition the fix exists to produce, pinned directly: with seed 7
    # at least one of the five draws repeats a key rather than drawing both
    # distinct units.
    assert any(len(set(keys)) < len(keys) for keys in seen)


def test_total_resample_failure_is_distinguishable_from_no_resample_supplied():
    """Task 6's second review round's finding: `ci95: null` alone cannot tell
    "nobody supplied a `resample` callable" apart from "one was supplied and
    every draw raised or returned `nan`" — both produced a `run.yaml` with no
    interval and no draw count. `resample_draws` closes that: `null` for the
    first, `0` for the second, never the same value for both."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}

    def always_fails(units: UnitTable) -> float | None:
        raise ZeroDivisionError("every draw is degenerate")

    not_attempted = summarize_step(collapsed, {"completed": 10}, derived={"total": 45.0}, seed=7)
    attempted_and_failed = summarize_step(
        collapsed,
        {"completed": 10},
        derived={"total": 45.0},
        seed=7,
        resample={"total": always_fails},
    )
    assert not_attempted["total"]["resample_draws"] is None
    assert attempted_and_failed["total"]["resample_draws"] == 0
    # Both are honest about carrying no interval — the distinction is in the
    # draw count, not in `ci95` alone.
    assert not_attempted["total"]["ci95"] is None
    assert attempted_and_failed["total"]["ci95"] is None


def test_draws_is_reachable_through_summarize_step():
    """`draws` was previously computed but never threaded past the 2000
    default — passing a small one and checking `resample_draws` never exceeds
    it is the only way to observe it took effect without driving 2000 calls
    through a test."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}
    out = summarize_step(
        collapsed,
        {"completed": 10},
        derived={"total": 45.0},
        seed=7,
        resample={"total": lambda units: sum(units.pred)},
        draws=10,
    )
    assert out["total"]["resample_draws"] is not None
    assert out["total"]["resample_draws"] <= 10


def test_resample_draws_discloses_a_shrunken_surviving_count():
    """An interval built from 200 of 2000 requested draws must not read
    identically to a clean one — `resample_draws` is what makes the
    difference visible next to the number itself."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}
    calls = {"n": 0}

    def flaky(units: UnitTable) -> float | None:
        calls["n"] += 1
        return None if calls["n"] % 2 == 0 else float(sum(units.pred))

    out = summarize_step(
        collapsed,
        {"completed": 10},
        derived={"total": 45.0},
        seed=7,
        resample={"total": flaky},
        draws=20,
    )
    assert out["total"]["resample_draws"] is not None
    assert out["total"]["resample_draws"] < 20


def test_a_raising_compute_is_treated_as_degenerate_not_propagated():
    """The nan-versus-raise asymmetry the review named: `pearsonr` returns
    `nan` on a degenerate draw, a hand-rolled ratio raises `ZeroDivisionError`
    on the same kind of draw. Both are "not defined on this draw," so a
    `compute` that always raises must behave like one that always returns
    `nan` — reporting no interval rather than crashing the caller."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}

    def always_raises(units: UnitTable) -> float | None:
        raise ZeroDivisionError("degenerate draw")

    interval, draws_used = percentile_of_derived(collapsed, always_raises, seed=7, draws=20)
    assert interval is None  # every draw was dropped, not propagated
    assert draws_used == 0  # attempted and failed, not "never attempted" — see below


def test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused():
    """The collision check runs against every recorded column, including one
    dropped from `out` for being non-numeric — otherwise a bool column named
    `r` plus a derived `r` would silently coexist as two different meanings
    under one key."""
    collapsed = {f"u{i}": {"r": True} for i in range(5)}
    with pytest.raises(ContractError) as exc:
        summarize_step(collapsed, {"completed": 5}, derived={"r": 1.0}, seed=7)
    assert exc.value.code == "E-STEP-KEY-COLLISION"


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


def test_a_ragged_column_reads_none_in_row_order():
    """A unit with no value for a column reads as `None` at its own row, not as
    an absence that shortens the column — `reference.md` § Templates requires
    every column to be "the same shape whichever of the two supplied them",
    and § The per-unit tables that "a column absent from a row reads as
    `None`"."""
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {}})
    assert list(t.pred) == [1.0, None]
    assert len(t.pred) == len(t)


def test_two_differently_ragged_columns_stay_paired():
    """The alignment defect: dropping missing rows per column made two columns
    ragged in *different* rows come back the same length and mispaired, so
    `zip(units.pred, units.truth)` — or `pearsonr` over them, `reference.md`'s
    own example — correlated u2's prediction against u3's truth and published
    the result with an interval around it."""
    t = UnitTable(
        {
            "u1": {"pred": 1.0, "truth": 1.0},
            "u2": {"pred": 2.0},
            "u3": {"truth": 9.0},
            "u4": {"pred": 4.0, "truth": 4.0},
        }
    )
    assert list(t.pred) == [1.0, 2.0, None, 4.0]
    assert list(t.truth) == [1.0, None, 9.0, 4.0]
    # Row-aligned by construction: every pair belongs to one unit.
    for row, p, tr in zip(t, t.pred, t.truth, strict=True):
        assert row.get("pred") == p
        assert row.get("truth") == tr


def test_the_unit_column_is_still_readable_by_attribute():
    """`columns` deliberately omits `unit`, so the unknown-column refusal is
    keyed on "this name appears in no row" instead — a template reading
    `units.unit` (a per-unit weight lookup, say) is the case
    `percentile_of_derived` keeps real unit keys inside every draw for."""
    t = UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}})
    assert list(t.unit) == ["u1", "u2"]
    assert "unit" not in t.columns


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
    assert abs(boot.low - analytic.low) < 0.02
    assert abs(boot.high - analytic.high) < 0.02


def test_one_value_has_no_interval():
    assert percentile_over_units([1.0], seed=7) is None


def test_resample_seed_depends_on_the_digest():
    assert resample_seed("a") != resample_seed("b")
    assert resample_seed("a") == resample_seed("a")


class _FakeRandom:
    """Replaces `random.Random` so the exact index picked at each draw is known,
    which pins the rank the low/high formulas select rather than trusting a real
    RNG's output. With pool `[0.0, 1.0]`, `randrange` returning `(0, 0)` for a draw
    yields mean 0.0, `(0, 1)` yields 0.5, `(1, 1)` yields 1.0 — so a fixed sequence
    of index-pairs fixes exactly which of three values each of the 2000 draws lands
    on, and therefore which value sits at every rank of the sorted means."""

    def __init__(self, seed: int) -> None:
        # 100 draws of (0, 0) -> 0.0, then 1850 of (0, 1) -> 0.5, then 50 of
        # (1, 1) -> 1.0. Sorted means: ranks 0-99 are 0.0, 100-1949 are 0.5,
        # 1950-1999 are 1.0.
        self._seq = [0, 0] * 100 + [0, 1] * 1850 + [1, 1] * 50
        self._i = 0

    def randrange(self, n: int) -> int:
        v = self._seq[self._i]
        self._i += 1
        return v


def test_the_rank_indices_are_symmetric_not_off_by_one(monkeypatch):
    """At draws=2000, confidence=0.95, tail=0.025: the intended ranks are 49 (the
    50th-smallest, 2.5%) and 1949 (the 1950th-smallest, 97.5% — symmetric with 49
    about the two ends). Rank 1949 sits in the middle (0.5) block; the bare
    asymmetric form `int((1 - tail) * draws)` would instead pick rank 1950, one
    past the boundary into the top (1.0) block — a real, detectable difference,
    not a rounding wash."""
    monkeypatch.setattr("publishable.stats.random.Random", _FakeRandom)
    result = percentile_over_units([0.0, 1.0], seed=7, draws=2000, confidence=0.95)
    assert result == Interval(low=0.0, high=0.5, method="percentile_over_units")

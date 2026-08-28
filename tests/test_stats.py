import itertools
import math
import random

import pytest
from tests.test_units import h3c3_per_cell_fixture

from publishable.errors import ContractError
from publishable.replication import resolve_repeats
from publishable.stats import (
    Interval,
    PairedResample,
    UnitTable,
    _cr1_variance,
    _percentile_ranks,
    _sample_variance,
    _t_critical,
    cohens_ds,
    cohens_dz,
    collapse_repeats,
    handed_to,
    interval_at,
    kish_effective_n,
    mean_of,
    min_honest_draws,
    min_honest_permutations,
    paired_delta_of_derived,
    paired_keys,
    paired_percentile_of_derived,
    paired_t_over_units,
    paired_t_over_units_clustered,
    percentile_of_derived,
    percentile_of_derived_clustered,
    percentile_over_units,
    percentile_over_units_clustered,
    permutation_of_derived,
    permutation_over_contrast,
    permutation_over_units,
    permutation_over_units_clustered,
    repeat_spread,
    repeats_disagreeing,
    resample_seed,
    summarize_step,
    t_over_units,
    t_over_units_clustered,
    unpaired_keys,
    unpaired_percentile_of_sides,
    weighted_t_over_units,
    weighted_t_over_units_clustered,
    welch_t_over_units,
    welch_t_over_units_clustered,
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
    with `fold_basis=4`: `fold01` and `fold02`."""
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
    levels = resolve_repeats(cfg([{"kind": "fold", "k": 2}]), "d", fold_basis=4)
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
        cfg([{"kind": "fold", "k": 2}, {"kind": "seed", "n": 2}]), "d", fold_basis=4
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
    and 0.5 (averaged across folds, dividing by a fold count).

    **H5b task 4, Fixture K.** Extended (not duplicated — grepped for by name)
    with a third fold, `fold03`, whose two units record only a bool `flag`, both
    seeds agreeing. Decision 1 changed what `collapse_repeats` RETURNS for a
    non-numeric column — it now carries rather than drops it — and changed
    nothing about how `handed_to`'s intersection decides membership: `u5`/`u6`
    are admitted within their own fold exactly as `u1`-`u4` are within theirs,
    and each gets `flag: True` (the repeats agreed, so `_across_repeats` returns
    the value itself rather than `None`) beside its numeric `s`-less row.
    """
    members = {
        "fold01": frozenset({"u1", "u2"}),
        "fold02": frozenset({"u3", "u4"}),
        "fold03": frozenset({"u5", "u6"}),
    }
    results = [
        _repeat_result("analyze", "fold01_seed01", 0, {"u1": {"s": 1.0}, "u2": {"s": 1.0}}),
        _repeat_result("analyze", "fold01_seed02", 0, {"u1": {"s": 3.0}, "u2": {"s": 3.0}}),
        _repeat_result("analyze", "fold02_seed01", 0, {"u3": {"s": 1.0}, "u4": {"s": 1.0}}),
        _repeat_result("analyze", "fold02_seed02", 0, {"u3": {"s": 3.0}, "u4": {"s": 3.0}}),
        _repeat_result("analyze", "fold03_seed01", 0, {"u5": {"flag": True}, "u6": {"flag": True}}),
        _repeat_result("analyze", "fold03_seed02", 0, {"u5": {"flag": True}, "u6": {"flag": True}}),
    ]
    table = collapse_repeats(results, "analyze", 0, members)
    assert len(table) == 6
    assert set(table) == {"u1", "u2", "u3", "u4", "u5", "u6"}
    assert all(row["s"] == 2.0 for key, row in table.items() if key not in ("u5", "u6"))
    assert table["u5"] == {"flag": True}
    assert table["u6"] == {"flag": True}


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


def test_a_disagreeing_bool_column_collapses_to_none_not_dropped():
    """H5b task 5, Fixture C. REPLACES
    `test_collapse_drops_a_bool_column_rather_than_averaging_it`, kept
    discoverable under that name here: that test pinned the unit drop wearing
    the name of a column drop — `p0` was absent from `collapsed` entirely, not
    merely missing `flag` (§ Corrections 12) — so it passed today for the
    wrong reason. This is a CORRECT move, not a weakening: after task 4, `p0`
    is admitted and its disagreeing `flag` column collapses to `None` rather
    than being dropped, and the disagreement is disclosed by
    `W-STATS-REPEATS-DISAGREE` rather than by silence.

    Two assertions on the direct call, not one: the key is PRESENT and the
    value is `None`. `values[0]` is `True` (seed17 recorded first), so a
    mutant carrying the first value instead of `None` gives `True`, which
    `is None` separates from the correct answer.
    """
    results = [
        _result("seed17", [{"unit": "p0", "flag": True}]),
        _result("seed42", [{"unit": "p0", "flag": False}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert "flag" in collapsed["p0"]
    assert collapsed["p0"]["flag"] is None


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


def test_unpaired_keys_gives_each_side_its_own_completed_set():
    """`paired_keys` is the intersection and it is the wrong set for a contrast
    whose two sides are disjoint. Each side gets its own completed units, sorted for
    the same reason `paired_keys` sorts — a draw over these keys must be row-order
    invariant.

    The fixture is genuinely disjoint AND has one shared key, which is the case a
    naive `set(of) - set(against)` would get wrong: sharing a key is not what makes
    a comparison paired, the group axis is, and this function does not decide that."""
    of = {"a": {"m": 1.0}, "b": {"m": 2.0}, "s": {"m": 3.0}}
    against = {"c": {"m": 4.0}, "s": {"m": 5.0}}
    assert unpaired_keys(of, against, None) == (["a", "b", "s"], ["c", "s"])


def test_unpaired_keys_narrows_both_sides_by_the_stratum():
    """`within` narrows each side, the same narrowing `paired_keys` applies to the
    intersection. Asserted on both sides, because a function narrowing only `of`
    passes any test that reads one side."""
    of = {"a": {"m": 1.0}, "b": {"m": 2.0}}
    against = {"c": {"m": 3.0}, "d": {"m": 4.0}}
    assert unpaired_keys(of, against, {"a", "c"}) == (["a"], ["c"])
    assert unpaired_keys(of, against, set()) == ([], [])


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


def test_a_clustered_derived_metric_is_resampled_by_the_clustered_construction():
    """**Converted from a refusal test, `E-DATA-CLUSTER-DERIVED` now retired**
    (H4d task 15). The clustered draw for a *recomputed* metric — each
    replicate drawing `G` clusters with replacement and pooling their units —
    is `percentile_of_derived_clustered` (task 15a), and `summarize_step` now
    routes a derived key through it whenever `clusters` is given, rather than
    raising before a single derived key is written.

    Kept alive against the code that survives, rather than only asserting the
    old raise no longer fires: a `ci95`, a `method` naming the clustered
    construction, and a `resample_draws` count, which is what a converted test
    must assert on `CLAUDE.md`'s own rule that a test asserting only an
    absence would pass identically if the whole derived branch had been
    deleted."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    clusters = {f"u{i}": f"s{i % 4}" for i in range(20)}
    out = summarize_step(
        collapsed,
        {"completed": 20},
        derived={"total": 190.0},
        seed=7,
        resample={"total": lambda units: sum(units.pred)},
        clusters=clusters,
    )
    assert out["total"]["value"] == 190.0
    assert out["total"]["ci95"] is not None
    assert out["total"]["method"] == "percentile_of_derived_clustered"
    assert out["total"]["resample_draws"] == 2000


def test_a_clustered_derived_metrics_n_clusters_matches_the_draw_it_actually_rests_on():
    """**Fix round 1, Major 3.** `percentile_of_derived_clustered`'s docstring
    claims `G` "cannot disagree with the `n.clusters` a caller prints beside
    the interval" — verified false before this fix: `summarize_step`'s derived
    branch wrote `"n": {**counts, "completed": len(collapsed)}` unconditionally,
    passing `counts["clusters"]` (`attrition`'s condition-wide figure) straight
    through with no recomputation, while the recorded-column branch beside it
    deliberately recomputes `cluster_count_of(clusters, column_keys)` for
    exactly the reason a ragged carrier set can disagree with the whole
    roster's count. A `counts` claiming 4 clusters beside a `collapsed` table
    spanning only 2 published `n: {..., clusters: 4}` beside an interval drawn
    from 2 — the docstring's guarantee, contradicted by the code beside it.

    Fixed by recomputing `n.clusters` from `collapsed`'s own keys — the same
    keys `percentile_of_derived_clustered` draws from — whenever `clusters` is
    given, mirroring the recorded-column branch's own discipline. This fixture
    deliberately hands `counts["clusters"]` a WRONG, larger figure (4, over a
    4-cluster mapping) beside a `collapsed` table spanning only 2 of those
    clusters, so a caller that forgot to recompute would publish the wrong
    number — the exact shape the docstring was making a claim about.

    `tests/test_cli.py`'s own review note: reachability through a real `run`
    would need a step recording for a proper subset of completed units, which
    this test does not construct — the weaker, direct-call claim is what is
    verified here."""
    collapsed = {f"u{i}": {"y": float(i)} for i in range(2)}
    clusters = {"u0": "A", "u1": "B", "u2": "C", "u3": "D"}
    counts = {"resolved": 4, "completed": 4, "ineligible": 0, "failed": 0, "clusters": 4}
    out = summarize_step(
        collapsed,
        counts,
        derived={"total": 190.0},
        seed=7,
        resample={"total": lambda units: sum(units.y)},
        clusters=clusters,
        draws=200,
    )
    assert out["total"]["n"]["clusters"] == 2


@pytest.mark.parametrize(
    "narrowed",
    [
        pytest.param({"seed": None}, id="no-seed"),
        pytest.param({"resample": None}, id="no-resample-map"),
        pytest.param({"resample": {"total": None}}, id="no-callable-for-this-key"),
    ],
)
def test_a_clustered_derived_metric_with_no_draw_attempted_publishes_no_interval(narrowed):
    """With no seed or no callable, the dispatch that would route a derived key
    through `percentile_of_derived_clustered` (task 15a) is never reached, so no
    interval is built at all and the point estimate publishes as it always did —
    the same "no draw, no interval" rule an unclustered derived metric follows.

    None of these three is reachable through `cli` today — it builds a callable for
    every derived key and only when `derived` is truthy — so the narrowing is
    defensive. Pinned here because a mutation removing it is otherwise invisible:
    measured, not assumed.

    The recorded column beside it stays cluster-robust throughout, which is what
    says the clustering is still in force and simply has no derived key to reach."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    clusters = {f"u{i}": f"s{i % 4}" for i in range(20)}
    kwargs = {"seed": 7, "resample": {"total": lambda units: sum(units.pred)}, **narrowed}
    out = summarize_step(
        collapsed, {"completed": 20}, derived={"total": 190.0}, clusters=clusters, **kwargs
    )
    assert out["total"]["value"] == 190.0
    assert out["total"]["ci95"] is None
    assert out["pred"]["method"] == "t_over_units_clustered"


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

    interval_a = percentile_of_derived(collapsed_a, compute_r, seed=7, draws=500).interval
    interval_b = percentile_of_derived(collapsed_b, compute_r, seed=7, draws=500).interval
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


def test_the_permutation_floor_is_the_smallest_n_whose_p_can_fall_below_the_level():
    """`1/(n + 1) < level` gives `n > 1/level − 1`, so the floor is `floor(1/level)`
    — 20 at alpha, 40 at alpha/2, 60 at alpha/3.

    Asserted at three levels rather than one, because a single level cannot tell
    `floor(1/level)` from any expression that happens to agree there: `ceil(1/level)
    - 1` agrees with nothing here and gives 19/39/59, and `min_honest_draws`'
    own `ceil(2/tail)` gives 80 at alpha, which is the wrong quantity entirely —
    that one is about a percentile interval's two ranks being interior."""
    assert min_honest_permutations(0.05) == 20
    assert min_honest_permutations(0.025) == 40
    assert min_honest_permutations(0.05 / 3) == 60
    assert min_honest_permutations(0.05) != min_honest_draws(0.95)


def test_the_permutation_floor_is_what_its_own_inequality_says():
    """The floor and the inequality it comes from, checked against each other
    rather than against a literal, so the two cannot drift: at the floor the
    resolution `1/(n + 1)` is strictly below the level, and one draw fewer it is
    not."""
    for level in (0.05, 0.025, 0.05 / 3, 0.05 / 4):
        n = min_honest_permutations(level)
        assert 1.0 / (n + 1) < level
        assert not 1.0 / n < level


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

    resampled = percentile_of_derived(collapsed, survives_twice, seed=7, draws=100)
    assert resampled.interval is None
    assert resampled.draws_used == 2


def test_an_interval_is_built_at_the_floor():
    """The other side of the same boundary: exactly `min_honest_draws()`
    survivors is enough, so the floor refuses too little rather than refusing
    everything short of `draws`."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}
    calls = {"n": 0}

    def survives_eighty(units: UnitTable) -> float | None:
        calls["n"] += 1
        return float(sum(units.pred)) if calls["n"] <= min_honest_draws() else None

    resampled = percentile_of_derived(collapsed, survives_eighty, seed=7, draws=200)
    assert resampled.draws_used == min_honest_draws()
    assert resampled.interval is not None
    assert resampled.interval.low < resampled.interval.high  # never zero-width


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

    resampled = percentile_of_derived(collapsed, always_raises, seed=7, draws=20)
    assert resampled.interval is None  # every draw was dropped, not propagated
    assert resampled.draws_used == 0  # attempted and failed, not "never attempted" — see below


def test_a_compute_that_raises_valueerror_is_contained_the_same_as_zerodivisionerror() -> None:
    """`percentile_of_derived` contains a `ValueError`-raising `compute` the
    same way `test_a_raising_compute_is_treated_as_degenerate_not_propagated`
    already pins for `ZeroDivisionError` — near-isomorphic to that test with
    the exception swapped, and named for exactly that rather than for the
    broader claim "a non-numeric `aggregate` return is contained," which is
    pinned end to end in `tests/test_cli.py`'s
    `test_a_non_numeric_derived_metric_is_disclosed_not_a_traceback` instead.

    `ValueError` is the real, concrete exception that mechanism produces: a
    template returning `{"m": "high"}` is a `str` `coerce_scalars` accepts,
    so it reaches `cli.py`'s resample closure, which floats whatever
    `aggregate` returned (`return None if value is None else float(value)`)
    — and `float("high")` raises `ValueError`. `compute` here stands in for
    that closure rather than for `aggregate` itself, because the failure is
    in the cast the closure performs on `aggregate`'s return, not inside
    `aggregate`.

    The containment is real but incidental: it comes from the same
    `except Exception` that exists for a degenerate arithmetic failure like
    `ZeroDivisionError`, not for a badly-typed metric — the module docstring
    says only "raises" without saying which exceptions. This test is what
    makes narrowing that handler to a closed set that drops `ValueError` fail
    loudly instead of silently reopening this path.

    Narrowing specifically to `except (ValueError, ZeroDivisionError)` does
    **not** trip this test — it still passes, because `float()` on a
    non-numeric `str` raises `ValueError` and nothing else can reach that
    cast: `coerce_scalars` constrains whatever `aggregate` returned to
    `bool`/`int`/`float`/`str`/`None` before it ever reaches here, `bool`/
    `int`/`float` convert cleanly, and `None` short-circuits before `float()`
    is called at all. Only a narrowing that excludes `ValueError` itself
    (`except ZeroDivisionError` alone, say — the set the *other* existing
    pin, `test_a_raising_compute_is_treated_as_degenerate_not_propagated`,
    alone would license) actually reopens this path.
    """
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(10)}

    def resample_fn_for_a_string_metric(units: UnitTable) -> float | None:
        value = "high"  # what `aggregate` returning {"m": "high"} looks like
        return None if value is None else float(value)  # cli.py's resample_fn

    resampled = percentile_of_derived(collapsed, resample_fn_for_a_string_metric, seed=7, draws=20)
    assert resampled.interval is None
    assert resampled.draws_used == 0


def test_a_derived_key_colliding_with_a_non_numeric_recorded_column_is_refused():
    """The collision check runs against every recorded column, including one
    that earns no published metric block for being non-numeric — otherwise a
    bool column named `r` plus a derived `r` would silently coexist as two
    different meanings under one key.

    **Renamed and re-driven, and the fixture is the point.** This test shipped
    green over a hand-built `{f"u{i}": {"r": True}}` — a `collapsed` no
    production caller could produce, because the collapse returned `{}` for a
    record carrying no numeric column at all, so the seam it named was
    unreachable and the assertion proved nothing. H5b task 4 admits the record,
    and the fixture below is now the **output of a real `collapse_repeats`
    call** over `_result`-built executions. Its assertion is unchanged.
    Verified by running rather than by reading: the collapse returns exactly
    the mapping this test used to hand-build, and the refusal fires with no new
    code — the check is `set(derived) & set(columns)` with `columns` built from
    `collapsed`, so admitting the record is the whole fix.

    Its old name kept the word "dropped", which describes nothing after task 4;
    the development record (`H5b-SCOPING.md`, this slice's plan and design)
    still cites the old name, deliberately, because those files record what was
    measured on their date and are not retro-edited.

    Distinct from `test_fixture_e_a_collision_from_a_real_collapse_output_is_
    refused`, which carries a numeric `score` beside `r`: this fixture carries
    **no numeric column at all**, which is the shape the collapse used to drop
    wholesale and the reason this test was unreachable in the first place."""
    rows = [{"unit": f"u{i}", "r": True} for i in range(5)]
    collapsed = collapse_repeats([_result("", rows)], "analyze", 0)
    assert collapsed == {f"u{i}": {"r": True} for i in range(5)}
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


_WELCH_OF = [17.0, 19.0, 20.0, 21.0, 23.0]
_WELCH_AGAINST = [5.0] * 12 + [15.0] * 12 + [10.0]


def test_the_welch_t_assumes_neither_shared_units_nor_equal_variances():
    """Fixture A: `of` is 5 units at mean 20 with s² 5, `against` is 25 units at
    mean 10 with s² 25 — so s²/n is exactly 1 on each side and BOTH sides
    contribute comparably to the Welch variance. That balance is the whole design
    of the fixture: where one side dominates, Welch-Satterthwaite's df is driven
    onto `min(df_of, df_against)` and a `min(n) − 1` mutant becomes invisible. The
    spec's own first draft did exactly that — correct 17.2405 against the mutant's
    17.2614, 0.1 % apart.

    Delta 10, SE √2, df 96/7. Four wrong readings give four other half-widths and
    none is adjacent: the pooled variance at df 28 gives 4.7221, the Welch variance
    at `min(n) − 1` gives 3.9265, at `max(n) − 1` gives 2.9188, and at
    `n_of + n_against − 2` gives 2.8969. The tightest is 4.7 % from correct, which
    no rounding produces.

    **A Welch interval that coincides with a pooled one proves nothing** — equal
    per-side sizes make the two standard errors algebraically identical — so the
    unequal sizes here are load-bearing rather than incidental."""
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    assert interval.method == "welch_t_over_units"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(10.0)
    assert half == pytest.approx(3.039125537798091)


def test_the_welch_t_is_not_the_pooled_t_on_the_same_two_sides():
    """The control that must report, and the number a pooled mutant lands on. The
    pooled standard error on the same data is
    √(((4·5) + (24·25)) / 28 · (1/5 + 1/25)) and at df 28 gives a half-width of
    4.7221 — 55 % wider. A test asserting only that an interval came back, or only
    that it brackets the delta, passes under either construction."""
    pooled_variance = ((5 - 1) * 5.0 + (25 - 1) * 25.0) / (5 + 25 - 2)
    pooled_se = math.sqrt(pooled_variance * (1 / 5 + 1 / 25))
    assert _t_critical(28, 0.95) * pooled_se == pytest.approx(4.722138614325821)
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    assert (interval.high - interval.low) / 2 != pytest.approx(4.722138614325821)


def test_the_welch_t_refuses_the_degenerate_inputs_its_siblings_refuse():
    """`None` below two values on EITHER side — df would be zero on that side and
    there is no dispersion to describe, which is `t_over_units`' own floor read
    across two samples. `None` also where both sides are constant: the combined
    variance is then exactly zero and Welch-Satterthwaite's df is 0/0, so the
    honest answer is a point with no interval rather than a `ZeroDivisionError`.

    One side constant is NOT refused — the other side still has dispersion and the
    difference of two means still has a sampling distribution — which is the
    asymmetry a copied `or` guard would get wrong."""
    assert welch_t_over_units([1.0], [1.0, 2.0, 3.0]) is None
    assert welch_t_over_units([1.0, 2.0, 3.0], [1.0]) is None
    assert welch_t_over_units([2.0, 2.0, 2.0], [1.0, 1.0, 1.0]) is None
    one_side_flat = welch_t_over_units([2.0, 2.0, 2.0], [1.0, 2.0, 3.0])
    assert one_side_flat is not None
    assert one_side_flat.high > one_side_flat.low


def test_the_extracted_sample_variance_leaves_t_over_units_where_it_was():
    """The extraction is pure code motion and this is the oracle that says so.
    `t_over_units` over `_WELCH_AGAINST` must give the same half-width it gave
    before `_sample_variance` existed — mean 10, s² 25, n 25, so
    t(0.975, 24)·√(25/25) = 2.0638985616280205.

    Pinned here rather than trusted, because a `(n - 1)` that became `n` in the
    move would narrow every unweighted interval in the package by a few per cent
    and nothing else in this module would notice."""
    plain = t_over_units(_WELCH_AGAINST)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(2.0638985616280205)
    assert _sample_variance(_WELCH_AGAINST, 10.0) == pytest.approx(25.0)


def test_a_weighted_interval_is_wider_than_the_unweighted_one():
    """The point of Kish's size. A test asserting only that `weighted_by` was
    recorded would pass against an implementation that stores the declaration and
    computes the unweighted interval — which is the bug, not the fix.

    The last unit carries eight units' worth of the population, so Kish's size is
    3.17 against eight rows. The brief's own `20.0` puts it at 1.79, below the two
    the construction needs, and returns `None` — pinned separately below.
    """
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 8.0]
    plain = t_over_units(values)
    weighted = weighted_t_over_units(values, weights)
    assert plain is not None and weighted is not None
    assert weighted.method == "weighted_t_over_units"
    assert (weighted.high - weighted.low) > (plain.high - plain.low)


def test_the_weighted_interval_is_the_t_interval_at_kishs_effective_size():
    """**The discriminating test**, and the one that pins df to Kish's size rather
    than the row count. Widening alone does not: the weighted variance inflates
    enough on its own that a df taken from `len(values)` still comes out wider
    than the unweighted interval, so the headline test above passes under that
    mutation.

    The weights are chosen so Kish's size is an exact integer, which lets the
    expectation be built from the already-trusted `t_over_units` rather than from
    a second copy of the formula under test. Σw = 6 and Σw² = 12, so the effective
    size is 36/12 = 3 exactly. The weighted mean is 24/6 = 4.0; Σw(v−m)² = 9 + 4 +
    1 + 12 = 26 over a denominator of Σw − Σw²/Σw = 4, so the weighted variance is
    6.5. Three points with mean 4.0 and sample variance 6.5 therefore have to give
    back the same interval.

    Every quantity here discriminates. Dropping the weights from the variance
    gives 6.0 (unweighted, n − 1) or 4.5 (weighted numerator over the wrong
    denominator) — never 6.5. Taking df from the row count gives t(3), not t(2).
    Dividing the sem by √4 rather than √3 moves it again. None of the three is
    hidden by a coincidence of the values, which `[10, 20]`-shaped data is where
    this slice has been burned before.
    """
    values = [1.0, 2.0, 3.0, 6.0]
    weights = [1.0, 1.0, 1.0, 3.0]
    assert kish_effective_n(weights) == pytest.approx(3.0)
    spread = math.sqrt(6.5)
    equivalent = t_over_units([4.0 - spread, 4.0, 4.0 + spread])
    got = weighted_t_over_units(values, weights)
    assert equivalent is not None and got is not None
    assert got.low == pytest.approx(equivalent.low)
    assert got.high == pytest.approx(equivalent.high)


def test_the_weights_are_in_the_variance_and_not_only_in_the_mean():
    """The mutation the equal-weights boundary cannot see: weights kept in the
    mean and dropped from the variance leaves the point estimate right and the
    interval wrong, which is the failure that survives an eyeball.

    Two weightings over the *same* values with the *same* Kish size, so df and the
    sem's divisor are identical and the variance is the only thing left that can
    differ. Weighting the two extremes makes the spread about the weighted mean
    larger than weighting the two central values does; with the weights out of the
    variance both reduce to the same unweighted sum of squares about a mean that
    is 3.5 either way, and the two intervals come out identical.
    """
    values = [1.0, 2.0, 5.0, 6.0]
    at_the_edges = weighted_t_over_units(values, [3.0, 1.0, 1.0, 3.0])
    at_the_centre = weighted_t_over_units(values, [1.0, 3.0, 3.0, 1.0])
    assert at_the_edges is not None and at_the_centre is not None
    assert kish_effective_n([3.0, 1.0, 1.0, 3.0]) == kish_effective_n([1.0, 3.0, 3.0, 1.0])
    assert (at_the_edges.high - at_the_edges.low) > (at_the_centre.high - at_the_centre.low)


def test_equal_weights_reproduce_the_unweighted_interval():
    """The boundary that proves the construction is a generalization, not a
    different statistic wearing the same name."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    weighted = weighted_t_over_units(values, [1.0] * 5)
    plain = t_over_units(values)
    assert weighted is not None and plain is not None
    assert weighted.low == pytest.approx(plain.low)
    assert weighted.high == pytest.approx(plain.high)


def test_rescaling_every_weight_changes_nothing():
    """A weight is how much of the population a unit stands for, and survey
    weights routinely sum to a population size rather than to the row count. An
    estimator that moved when every weight was multiplied by the same constant
    would make the interval depend on that convention."""
    values = [1.0, 2.0, 3.0, 6.0]
    small = weighted_t_over_units(values, [1.0, 1.0, 1.0, 3.0])
    large = weighted_t_over_units(values, [1000.0, 1000.0, 1000.0, 3000.0])
    assert small is not None and large is not None
    assert large.low == pytest.approx(small.low)
    assert large.high == pytest.approx(small.high)


def test_kish_effective_n_of_equal_weights_is_the_count():
    assert kish_effective_n([2.0, 2.0, 2.0, 2.0]) == pytest.approx(4.0)


def test_kish_effective_n_falls_as_the_weights_spread():
    """The property the df rests on, over a case where the count is unchanged."""
    assert kish_effective_n([1.0, 1.0, 1.0, 9.0]) < kish_effective_n([1.0, 1.0, 1.0, 3.0]) < 4.0


def test_kish_effective_n_of_no_weights_is_zero():
    """The `Σw² == 0` guard's only reachable input once the gate is in front of
    it: no weight that passes `usable_weight` is zero, but an empty sequence is a
    real call rather than an error."""
    assert kish_effective_n([]) == 0.0


def test_kish_effective_n_reads_a_table_sourced_column():
    """**The case task 9 will actually hit.** It wires this onto the roster's
    weight column, and `units._from_table` builds every attribute from
    `csv.DictReader`, so every weight arrives as `str`. Ungated this raised a bare
    `TypeError` from `sum`, with no `code` for a diagnostic to print."""
    assert kish_effective_n(["1", "1.0", "1", "3"]) == pytest.approx(3.0)


@pytest.mark.parametrize(
    ("label", "weights"),
    [
        ("negative", [-1.0, 1.0]),
        ("nan", [float("nan"), 1.0]),
        ("inf", [float("inf"), 1.0]),
        ("zeros", [0.0, 0.0]),
        ("non-numeric", ["site-3", 1.0]),
        ("bool", [True, 1.0]),
    ],
)
def test_kish_effective_n_refuses_a_weight_it_cannot_use(label, weights):
    """The gate belongs *inside* this function, not at its call site.

    It is public, it returns a number that reaches `run.yaml` as `n.effective`,
    and a caller that has to remember to pre-validate is a caller that eventually
    forgets. Ungated, every one of these answered rather than raising: `nan` and
    `inf` gave `nan`, the negative and the zeros gave `0.0`. A plausible-looking
    number with no error is the failure class the weight checks exist to prevent,
    and it is strictly worse than the `TypeError` the string case gave, because
    nothing downstream can tell it apart from a real answer.
    """
    with pytest.raises(ContractError) as exc:
        kish_effective_n(weights)
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_the_weighted_interval_honours_its_confidence():
    """`confidence` reaches `_t_critical` on the weighted path too. Hardcoding
    0.95 there passed every other test in this file — the unweighted path is
    where the existing confidence test looks."""
    values, weights = [1.0, 2.0, 3.0, 6.0], [1.0, 1.0, 1.0, 3.0]
    narrow = weighted_t_over_units(values, weights, confidence=0.80)
    wide = weighted_t_over_units(values, weights, confidence=0.99)
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)
    assert narrow.low == pytest.approx(1.2244, abs=1e-3)
    assert wide.low == pytest.approx(-10.6086, abs=1e-3)


@pytest.mark.parametrize("values", [[], [3.0]])
def test_a_weighted_interval_needs_two_values(values):
    assert weighted_t_over_units(values, [1.0] * len(values)) is None


def test_an_effective_size_below_two_has_no_interval():
    """Kish's size is the df's basis, so a weighting that concentrates eight rows
    onto fewer than two effective units has no dispersion the df can describe —
    the same refusal `t_over_units` makes at one row, arriving by the weights."""
    weights = [1.0] * 7 + [20.0]
    assert kish_effective_n(weights) < 2
    assert weighted_t_over_units([float(i) for i in range(1, 9)], weights) is None


def test_a_table_sourced_weight_is_read_as_the_number_it_holds():
    """`units.usable_weight` is the gate here and in `validate`, and this is what
    the sharing buys: `csv.DictReader` yields `str` for every column whatever it
    holds, so an `isinstance(v, (int, float))` gate would refuse every real weight
    a `weight_by` config can produce — after `validate` had approved it."""
    values = [1.0, 2.0, 3.0, 6.0]
    from_table = weighted_t_over_units(values, ["1", "1.0", "1", "3"])
    native = weighted_t_over_units(values, [1.0, 1.0, 1.0, 3.0])
    assert from_table is not None and native is not None
    assert from_table.low == pytest.approx(native.low)
    assert from_table.high == pytest.approx(native.high)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf"), "site-3", True, None])
def test_a_weight_validate_would_refuse_is_refused_here_too(bad):
    """The single-authority claim, from the other side. `validate` reports
    `E-DATA-WEIGHT-INVALID` for exactly these; reaching a weighted mean with one
    of them still in hand is the validate-clean-then-crash gap, so it is refused
    under the same identifier rather than by a bare `TypeError` or a `nan`."""
    with pytest.raises(ContractError) as exc:
        weighted_t_over_units([1.0, 2.0, 3.0, 6.0], [1.0, 1.0, 1.0, bad])
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


# --- H3b task 9: the cluster-robust estimator (CR1) ---------------------------
#
# Ten clusters of three units, with the units of a cluster sitting at its mean
# −1, +0 and +1. Balanced clusters are what make the expectation independent of
# the code under test: for the intercept-only sandwich with equal cluster size m,
# the score of cluster g is S_g = m(ȳ_g − ȳ), so
#
#   V_CR1 = [G/(G−1)]·m²Σ(ȳ_g−ȳ)²/(mG)² = s²(cluster means)/G
#
# — the ordinary t interval over the G cluster means, at df = G − 1. That is a
# textbook reduction, not this module's arithmetic, so `t_over_units` over the
# ten means below is an expectation built from something already trusted.
#
# The within-cluster ±1 is not decoration: it makes the fixture's 30 values
# spread differently from its 10 means, so an implementation reading the unit
# count anywhere — for the df or for the sem's divisor — misses.
_CLUSTER_MEANS = [1.0, 2.5, 3.0, 4.5, 5.0, 6.5, 7.0, 8.5, 9.0, 10.5]
_BALANCED_VALUES = [m + d for m in _CLUSTER_MEANS for d in (-1.0, 0.0, 1.0)]
_BALANCED_KEYS = [f"u{i}" for i in range(30)]
_BALANCED_MEMBERSHIP = {f"u{i}": f"c{i // 3}" for i in range(30)}


def test_the_clustered_interval_takes_its_df_from_the_cluster_count():
    """10 clusters of 3 units. df must be 9, not 29 — the document's own example
    is "10 animals give 9, not 299". Asserting only that the interval is wider
    would pass against an implementation using the unit count, because a
    cluster-robust interval over correlated data is wider either way.

    The expectation is `t_over_units` over the ten cluster means, whose df is 9
    by construction and which the balanced sandwich provably reduces to (see the
    comment above this group) — so it does not come from the code under test.

    The last assertion names the mutation directly, against a standard error
    built from the ten means rather than read back off `got` — one divided out of
    `got` would make the line `H != approx(H·t(29)/t(9))`, true under every
    implementation. At the real standard error of 0.97539 the two critical values
    give half-widths of 2.2065 and 1.9949, which `approx` separates comfortably.
    """
    got = t_over_units_clustered(_BALANCED_VALUES, _BALANCED_KEYS, _BALANCED_MEMBERSHIP)
    expected = t_over_units(_CLUSTER_MEANS)
    assert got is not None and expected is not None
    assert got.method == "t_over_units_clustered"
    assert got.low == pytest.approx(expected.low)
    assert got.high == pytest.approx(expected.high)
    mean = sum(_CLUSTER_MEANS) / 10
    squares = sum((m - mean) ** 2 for m in _CLUSTER_MEANS)
    standard_error = math.sqrt(squares / 9) / math.sqrt(10)
    half = (got.high - got.low) / 2
    assert half == pytest.approx(_t_critical(9, 0.95) * standard_error)
    assert half != pytest.approx(_t_critical(29, 0.95) * standard_error)


def test_the_clustered_interval_is_the_cr1_sandwich_over_unbalanced_clusters():
    """The balanced fixture above cannot see two things: the sandwich is centred
    on the mean over UNITS, and unequal cluster sizes weight the clusters
    unequally. Both coincide with the mean of the cluster means when every
    cluster is the same size, so an implementation written as
    `t_over_units(cluster_means)` — which the reduction invites — passes it.

    Clusters of size 1, 2 and 3. Computed by hand from the intercept-only
    sandwich, and checked against a matrix-form implementation written
    separately:

        ȳ = 16/6 = 2.66667                    (mean of cluster means is 3.33333)
        S_A = 3.33333, S_B = −1.33333, S_C = −2.0;  Σ S_g² = 16.88889
        V = (3/2)·16.88889/36 = 0.703704 → se = 0.838870, df = 2, t = 4.302653

    giving [−0.94270, 6.27604]. The cluster-mean construction gives
    [−2.40353, 9.07020] — nowhere near, on both the centre and the width.
    """
    values = [6.0, 0.0, 4.0, 1.0, 2.0, 3.0]
    keys = ["a1", "b1", "b2", "c1", "c2", "c3"]
    membership = {"a1": "A", "b1": "B", "b2": "B", "c1": "C", "c2": "C", "c3": "C"}
    got = t_over_units_clustered(values, keys, membership)
    assert got is not None
    assert got.low == pytest.approx(-0.9427017491193528)
    assert got.high == pytest.approx(6.276035082452686)
    over_cluster_means = t_over_units([6.0, 2.0, 2.0])
    assert over_cluster_means is not None
    assert got.low != pytest.approx(over_cluster_means.low)


def test_the_finite_sample_scaling_is_in_the_variance():
    """The "CR1" half of the name. Dropping the G/(G−1) factor leaves CR0 — a
    different construction wearing the same `method` string, narrower by exactly
    √(G/(G−1)), which is 5.4% here and larger for every smaller cluster count.

    Stated as the two numbers rather than as a ratio: over balanced clusters the
    scaled standard error is the SAMPLE spread of the cluster means over √G, and
    the unscaled one is their POPULATION spread over √G — the same s·√((G−1)/G)
    the factor undoes. Both are computed here from the ten means, neither from
    the module.
    """
    got = t_over_units_clustered(_BALANCED_VALUES, _BALANCED_KEYS, _BALANCED_MEMBERSHIP)
    assert got is not None
    mean = sum(_CLUSTER_MEANS) / 10
    squares = sum((m - mean) ** 2 for m in _CLUSTER_MEANS)
    scaled = math.sqrt(squares / 9) / math.sqrt(10)
    unscaled = math.sqrt(squares / 10) / math.sqrt(10)
    half = (got.high - got.low) / 2
    assert half == pytest.approx(_t_critical(9, 0.95) * scaled)
    assert half != pytest.approx(_t_critical(9, 0.95) * unscaled)


def test_correlated_units_widen_the_interval_against_the_unclustered_one():
    """The property the feature exists for, and deliberately not the headline:
    it is true of a cluster-robust interval at any df, which is why the df tests
    above carry the weight. Positive intra-cluster correlation is the case
    § Clustered units describes — "ignoring clustering is the standard route to
    intervals that are too narrow".

    The control that must report is the unclustered interval over the same 30
    values: it is unchanged by this task, and it is what "too narrow" is measured
    against.
    """
    plain = t_over_units(_BALANCED_VALUES)
    clustered = t_over_units_clustered(_BALANCED_VALUES, _BALANCED_KEYS, _BALANCED_MEMBERSHIP)
    assert plain is not None and clustered is not None
    assert plain.method == "t_over_units"
    assert (clustered.high - clustered.low) > (plain.high - plain.low)


def test_one_cluster_of_many_units_has_no_interval():
    """CR1 with one cluster has df 0, so there is no interval to report — the
    same refusal `t_over_units` makes below two values, on the count that is
    actually the inference base here. 300 cells from one animal are one draw, and
    reporting a point with no interval is honest; inventing one is not.
    """
    values = [float(i) for i in range(12)]
    keys = [f"u{i}" for i in range(12)]
    assert t_over_units_clustered(values, keys, dict.fromkeys(keys, "only")) is None


def test_two_clusters_still_report():
    """The control for the floor above: a construction refusing one cluster must
    not refuse two. df = 1 makes it very wide — t(1) is 12.7 — which is the
    honest width for two draws, not a reason to withhold it."""
    values = [float(i) for i in range(12)]
    keys = [f"u{i}" for i in range(12)]
    membership = {key: ("left" if i < 6 else "right") for i, key in enumerate(keys)}
    got = t_over_units_clustered(values, keys, membership)
    assert got is not None and got.high > got.low


@pytest.mark.parametrize("values", [[], [1.0]])
def test_the_clustered_interval_needs_two_values(values):
    """`t_over_units`' own floor, kept in front of the cluster one so the two
    constructions refuse the same degenerate inputs."""
    keys = [f"u{i}" for i in range(len(values))]
    assert t_over_units_clustered(values, keys, dict.fromkeys(keys, "c")) is None


def test_one_unit_per_cluster_reproduces_the_unclustered_interval():
    """The boundary that proves this is a generalization rather than a different
    statistic — and a fixture that can see nothing else: with G = n the df is
    n − 1 either way and every score is a single residual, so the two
    constructions coincide. That is exactly why it is not the headline test."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    keys = ["u1", "u2", "u3", "u4", "u5"]
    got = t_over_units_clustered(values, keys, {key: key for key in keys})
    plain = t_over_units(values)
    assert got is not None and plain is not None
    assert got.low == pytest.approx(plain.low)
    assert got.high == pytest.approx(plain.high)


def test_a_unit_outside_the_membership_mapping_is_not_absorbed():
    """`units.cluster_count_of`'s discipline, from the caller's side: a key the
    roster's membership doesn't hold is a core defect, and placing it in a
    cluster of its own would raise G and narrow the interval instead of failing.
    """
    with pytest.raises(KeyError):
        t_over_units_clustered([1.0, 2.0], ["u1", "u2"], {"u1": "c1"})


def test_the_clustered_interval_honours_its_confidence():
    narrow = t_over_units_clustered(
        _BALANCED_VALUES, _BALANCED_KEYS, _BALANCED_MEMBERSHIP, confidence=0.80
    )
    wide = t_over_units_clustered(
        _BALANCED_VALUES, _BALANCED_KEYS, _BALANCED_MEMBERSHIP, confidence=0.99
    )
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)


# --- H3b task 11: the weighted sandwich, for a run declaring both -------------
#
# `reference.md` § Weighted samples: "`cluster_by` still decides the draw when
# both are declared, since a cluster is what's independent and a weight is what it
# represents". The draw is the cluster, so the df is clusters − 1; the estimate is
# the weighted mean, so the weight is in the score. One fixture serves the group:
# the unbalanced 1/2/3 clusters the unweighted sandwich is pinned over, with
# weights that vary WITHIN cluster B (1 and 4) — a weight vector aligned to the
# cluster rather than to the unit would give a different answer, and the whole
# failure class here is an alignment that produces a plausible number.
_WEIGHTED_CLUSTER_VALUES = [6.0, 0.0, 4.0, 1.0, 2.0, 3.0]
_WEIGHTED_CLUSTER_KEYS = ["a1", "b1", "b2", "c1", "c2", "c3"]
_WEIGHTED_CLUSTER_MEMBERSHIP = {
    "a1": "A",
    "b1": "B",
    "b2": "B",
    "c1": "C",
    "c2": "C",
    "c3": "C",
}
_WEIGHTED_CLUSTER_WEIGHTS = [1, 4, 1, 2, 1, 3]


def test_the_weighted_sandwich_reduces_to_the_unweighted_one_at_equal_weights():
    """The reduction that makes this a generalization rather than a second
    construction, and the oracle for the formula: at `w ≡ 1`, `Σw = n` and each
    cluster's weighted score collapses to its residual sum, so the whole thing is
    `t_over_units_clustered` **digit for digit** — no finite-sample correction has
    to be arranged for it, unlike `weighted_t_over_units`, whose `Σw − Σw²/Σw`
    denominator exists to buy exactly this property.

    Asserted as equality on both endpoints rather than `approx`: the two
    expressions evaluate the same floating-point operations in the same order, and
    an "almost" here would hide a scaling factor small enough to pass `approx`.
    Only `method` differs, which is the one thing that must.
    """
    plain = t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES, _WEIGHTED_CLUSTER_KEYS, _WEIGHTED_CLUSTER_MEMBERSHIP
    )
    weighted = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        [1] * len(_WEIGHTED_CLUSTER_VALUES),
    )
    assert plain is not None and weighted is not None
    assert weighted.low == plain.low
    assert weighted.high == plain.high
    assert weighted.method == "weighted_t_over_units_clustered"


_CLUSTERED_DIFFS = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
_CLUSTERED_LABELS = ["a"] * 2 + ["b"] * 4 + ["c"] * 6


def test_the_paired_clustered_t_is_cr1_over_the_differences():
    """12 per-unit differences in 3 clusters of 2/4/6 — `1.0 ×2`, `5.0 ×4`,
    `9.0 ×6`. Mean 76/12 = 6.3333…; per-cluster residual sums −10.6667, −5.3333,
    +16.0, so the meat is 398.2222, V = (3/2)·398.2222/144 and the half-width is
    t(0.975, df 2) = 4.302653 times its root.

    **The delta is the same number under every reading** — clustering moves the
    variance, not the point estimate — so the half-width is the whole assertion.
    Four wrong readings give four other numbers, none of them adjacent: the same
    meat at df 11 gives 4.4827, the IID variance at df 2 gives 3.8678, a cluster
    count of 4 gives 6.1110, and the unclustered form gives 1.9786. The correct
    answer is the extreme of no single dimension, which is what makes an assertion
    on the number discriminate all four rather than merely detect "wider"."""
    interval = paired_t_over_units_clustered(_CLUSTERED_DIFFS, _CLUSTERED_LABELS)
    assert interval is not None
    assert interval.method == "paired_t_over_units_clustered"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(6.333333333333333)
    assert half == pytest.approx(8.763214143637903)


def test_the_paired_clustered_t_is_not_the_unclustered_one_on_the_same_differences():
    """The control that must report, and the number a membership-ignoring mutant
    lands on. The same differences through `paired_t_over_units` give 1.9786 — a
    factor of four narrower, and the same centre, which is why a test asserting the
    centre alone is blind to clustering entirely."""
    plain = paired_t_over_units(_CLUSTERED_DIFFS)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(1.9785385229565593)
    assert plain.method == "paired_t_over_units"


def test_the_paired_clustered_t_refuses_the_degenerate_inputs_its_sibling_refuses():
    """Both floors are inherited rather than restated, which is the point of
    delegating: `None` below two differences, and `None` below two clusters, where
    df would be zero. The second is the one a singleton-cluster fixture can never
    see — one unit per cluster makes `clusters − 1` equal `n_paired − 1`, so the
    clustered and unclustered forms coincide exactly and a mutant ignoring
    membership passes. Hence the third case: 12 singleton clusters return an
    interval identical to the unclustered one, which is correct and is exactly why
    no other test here may use that shape."""
    assert paired_t_over_units_clustered([1.0], ["a"]) is None
    assert paired_t_over_units_clustered([1.0, 5.0, 9.0], ["a", "a", "a"]) is None
    singletons = paired_t_over_units_clustered(_CLUSTERED_DIFFS, [f"c{i}" for i in range(12)])
    plain = paired_t_over_units(_CLUSTERED_DIFFS)
    assert singletons is not None and plain is not None
    assert (singletons.high - singletons.low) == pytest.approx(plain.high - plain.low)


def _paired_cluster_fixture() -> tuple[dict, dict, list[str], dict[str, str]]:
    """12 keys in 3 clusters of 2/4/6, `of` minus `against` giving 1.0/5.0/9.0.

    Unequal sizes are load-bearing twice over: they make a replicate's pooled row
    count VARY (6 to 18) where a unit-drawing mutant returns a fixed 12, and they
    keep the correct and buggy cluster counts different. Equal sizes make both
    discriminators invisible."""
    keys = [f"u{i:02d}" for i in range(12)]
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    of = {k: {"m": v} for k, v in zip(keys, values, strict=True)}
    against = {k: {"m": 0.0} for k in keys}
    return of, against, keys, dict(zip(keys, labels, strict=True))


def test_the_paired_clustered_percentile_draws_whole_clusters():
    """`reference.md` § Statistical reporting: under `cluster_by` "the percentile
    forms resample whole clusters — jointly across both sides when paired".

    The row count is asserted directly rather than inferred from the interval,
    because it is the discriminator a mutant drawing UNITS cannot fake: three
    clusters drawn with replacement from sizes 2/4/6 pool between 6 and 18 rows,
    and every count is one of the sums those sizes can make. A unit-drawing mutant
    returns exactly 12 every time.

    The `method` is the caller's string, as it is for the two spellings this
    construction already emits."""
    of, against, keys, clusters = _paired_cluster_fixture()
    seen: list[int] = []

    def compute(table):
        seen.append(len(list(table.unit)))
        return sum(table.m) / len(table.m)

    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        compute,
        compute,
        seed=11,
        draws=400,
        method="paired_percentile_over_units_clustered",
        clusters=clusters,
    )
    assert got.interval is not None
    assert got.interval.method == "paired_percentile_over_units_clustered"
    reachable = {2, 4, 6}
    assert set(seen) != {12}
    assert min(seen) == 6 and max(seen) == 18
    assert all(
        count in {x + y + z for x in reachable for y in reachable for z in reachable}
        for count in seen
    )


def test_the_paired_clustered_percentile_draws_a_cluster_within_its_stratum():
    """`stratify_by` says what an independent draw is, `cluster_by` says the draw
    IS a cluster, and composed, a cluster is drawn within its own stratum — the
    equality `percentile_over_units_clustered` already keeps one level up.

    Stratum `A` holds the two small clusters (2 and 4 units) and stratum `B` the
    one large one (6). Each stratum contributes as many clusters as it holds, so
    every replicate pools 6 rows from `B` (its one cluster, redrawn with
    replacement, always contributes 6) and — drawing 2 clusters with replacement
    from {2, 4} — one of 4, 6, or 8 from `A`: the row count is confined to
    {10, 12, 14}, which an unstratified clustered draw (6 to 18, and 18 is
    reachable) is not."""
    of, against, keys, clusters = _paired_cluster_fixture()
    strata = {k: ("A" if clusters[k] in {"a", "b"} else "B") for k in keys}
    seen: list[int] = []

    def compute(table):
        seen.append(len(list(table.unit)))
        return sum(table.m) / len(table.m)

    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        compute,
        compute,
        seed=11,
        draws=400,
        strata=strata,
        method="paired_percentile_over_units_clustered",
        clusters=clusters,
    )
    assert got.interval is not None
    assert set(seen) <= {10, 12, 14}
    assert len(set(seen)) > 1  # the control: the draw really varies


def test_a_cluster_carrying_two_stratum_values_is_refused_on_a_contrast_draw_too():
    """The same fault `percentile_over_units_clustered` raises per condition, at
    the same code — § Errors carries one row per code covering every emit site, so
    this needs no new identifier. A cluster is indivisible, so one carrying two
    stratum values can be dealt to neither."""
    of, against, keys, clusters = _paired_cluster_fixture()
    strata = {k: ("A" if k < "u06" else "B") for k in keys}
    strata[keys[7]] = "A"  # inside cluster `c`, whose other units are `B`
    with pytest.raises(ContractError) as exc:
        paired_percentile_of_derived(
            of,
            against,
            keys,
            lambda t: sum(t.m) / len(t.m),
            lambda t: sum(t.m) / len(t.m),
            seed=11,
            draws=400,
            strata=strata,
            clusters=clusters,
        )
    assert exc.value.code == "E-STATS-RESAMPLE-STRATIFY-VARIES"


def test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was():
    """The regression the uniform draw shape owes. With `clusters=None` and no
    strata the drawn key list must be `[keys[rng.randrange(n)] for _ in range(n)]`
    against a fresh `random.Random(seed)` — same count of `randrange` calls, same
    bounds, same order. Asserted against a recomputed sequence rather than against
    a captured constant, so it pins the RNG contract instead of one seed's output.

    `keys` is deliberately **not** sorted ascending — the H4b-2 batch 2 review
    (Major 4) found the sorted-fixture form blind to a mutant that sorts `items`
    before drawing (`items = sorted([key] for key in keys)`): with `clusters=None`
    and no `strata` the `ValueError` guard never fires (it only checks under
    `strata`), so an unsorted `keys` list is legal here and the mutant's sorted
    order diverges from this fixture's own, which is what makes the mutation
    discriminate."""
    of, against, keys, _ = _paired_cluster_fixture()
    keys = keys[::-1]
    drawn: list[list[str]] = []

    def compute_of(table):
        drawn.append(list(table.unit))
        return sum(table.m) / len(table.m)

    def compute_against(table):
        return sum(table.m) / len(table.m)

    paired_percentile_of_derived(of, against, keys, compute_of, compute_against, seed=5, draws=200)
    rng = random.Random(5)
    expected = [[keys[rng.randrange(12)] for _ in range(12)] for _ in range(200)]
    assert drawn == expected


def test_the_weighted_clustered_interval_is_the_weighted_cr1_sandwich():
    """Computed as exact rationals away from this module, then rendered:

        Σw = 12, v̄_w = 23/12 = 1.9166667
        S_A = 49/12, S_B = −67/12, S_C = 3/2;  Σ S_g² = 3607/72 = 50.09722
        V = (3/2)·(3607/72)/144 → se = 0.7223891, df = 2, t = 4.3026527

    giving [−1.19152, 5.02486]. The unweighted sandwich over the same values and
    the same clusters gives [−0.94270, 6.27604] — the control that must report, and
    the number this test would return if the weights reached the mean but not the
    scores, or neither.
    """
    got = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        _WEIGHTED_CLUSTER_WEIGHTS,
    )
    assert got is not None
    assert got.low == pytest.approx(-1.1915229242750371)
    assert got.high == pytest.approx(5.024856257608371)
    unweighted = t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES, _WEIGHTED_CLUSTER_KEYS, _WEIGHTED_CLUSTER_MEMBERSHIP
    )
    assert unweighted is not None
    assert got.low != pytest.approx(unweighted.low)
    assert got.high != pytest.approx(unweighted.high)


def test_the_weighted_clustered_df_is_the_cluster_count_not_kishs_size():
    """The incoherence this construction had to avoid: `weighted_t_over_units`
    takes its df from Kish's effective size, `t_over_units_clustered` from the
    cluster count, and a weighted clustered interval that mixed them would have a
    df from neither. § Statistical reporting gives the clustered form
    "df = clusters − 1" unqualified, and a df is a property of the draw — which
    § Weighted samples hands to the cluster when both are declared.

    Kish's size over these weights is 4.5, so the rival df is 3.5 against the real
    2, and the two critical values (4.30265 and 3.18) separate the half-width
    comfortably. The standard error is rebuilt here from the cluster scores rather
    than divided back out of `got`, so neither assertion can be vacuous.
    """
    got = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        _WEIGHTED_CLUSTER_WEIGHTS,
    )
    assert got is not None
    assert kish_effective_n(_WEIGHTED_CLUSTER_WEIGHTS) == pytest.approx(4.5)
    standard_error = math.sqrt((3 / 2) * (3607 / 72) / 12**2)
    half = (got.high - got.low) / 2
    assert half == pytest.approx(_t_critical(2, 0.95) * standard_error)
    assert half != pytest.approx(_t_critical(3.5, 0.95) * standard_error)


def test_rescaling_the_weights_leaves_the_weighted_clustered_interval_unmoved():
    """Survey weights routinely sum to a population size rather than to the row
    count, and an interval that moved with that convention would be reporting the
    convention. `S_g` scales with the weights and `(Σw)²` divides the square out,
    so the invariance is exact rather than approximate — same reason
    `weighted_t_over_units` claims it."""
    base = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        _WEIGHTED_CLUSTER_WEIGHTS,
    )
    scaled = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        [w * 100 for w in _WEIGHTED_CLUSTER_WEIGHTS],
    )
    assert base is not None and scaled is not None
    assert scaled.low == pytest.approx(base.low)
    assert scaled.high == pytest.approx(base.high)


def test_the_weighted_clustered_interval_needs_two_clusters():
    """The clustered floor, on the cluster count and not on Kish's size: df would
    be zero at one cluster whatever the weights are. There is deliberately no Kish
    floor here — the effective size does not enter the df — which is what the
    control below is for."""
    assert (
        weighted_t_over_units_clustered(
            _WEIGHTED_CLUSTER_VALUES,
            _WEIGHTED_CLUSTER_KEYS,
            dict.fromkeys(_WEIGHTED_CLUSTER_KEYS, "only"),
            _WEIGHTED_CLUSTER_WEIGHTS,
        )
        is None
    )


def test_a_weighting_that_concentrates_on_one_unit_still_reports():
    """The control for the floor above, and the visible consequence of taking the
    df from the clusters: weights of 1000 against 1 put Kish's size below two —
    where `weighted_t_over_units` returns `None` — while three clusters still give
    2 df, so this reports. The concentration is not ignored; it shows up in the
    scores instead of in the df."""
    weights = [1000, 1, 1, 1, 1, 1]
    assert kish_effective_n(weights) < 2
    assert weighted_t_over_units(_WEIGHTED_CLUSTER_VALUES, weights) is None
    got = weighted_t_over_units_clustered(
        _WEIGHTED_CLUSTER_VALUES,
        _WEIGHTED_CLUSTER_KEYS,
        _WEIGHTED_CLUSTER_MEMBERSHIP,
        weights,
    )
    assert got is not None and got.high > got.low


@pytest.mark.parametrize("values", [[], [1.0]])
def test_the_weighted_clustered_interval_needs_two_values(values):
    """`t_over_units`' floor, kept in front of the cluster one so every
    construction in this module refuses the same degenerate input."""
    keys = [f"u{i}" for i in range(len(values))]
    assert (
        weighted_t_over_units_clustered(values, keys, dict.fromkeys(keys, "c"), [1] * len(values))
        is None
    )


def test_a_weight_core_cannot_use_reaches_the_weighted_clustered_interval_as_a_code():
    """`checked_weights` is the gate, the same single authority `validate` approves
    a config against — so a weight of zero is `E-DATA-WEIGHT-INVALID` here rather
    than a division that silently drops a unit's contribution to its cluster's
    score."""
    with pytest.raises(ContractError) as excinfo:
        weighted_t_over_units_clustered(
            _WEIGHTED_CLUSTER_VALUES,
            _WEIGHTED_CLUSTER_KEYS,
            _WEIGHTED_CLUSTER_MEMBERSHIP,
            [1, 4, 1, 2, 1, 0],
        )
    assert excinfo.value.code == "E-DATA-WEIGHT-INVALID"


def test_a_misaligned_weight_vector_is_not_absorbed_by_the_weighted_sandwich():
    """`strict=True` on the three-way zip: a weights/values length mismatch is a
    misaligned vector, and it would weight the wrong unit's residual into the wrong
    cluster's score — a plausible number rather than an error."""
    with pytest.raises(ValueError):
        weighted_t_over_units_clustered(
            _WEIGHTED_CLUSTER_VALUES,
            _WEIGHTED_CLUSTER_KEYS,
            _WEIGHTED_CLUSTER_MEMBERSHIP,
            [1, 4, 1, 2, 1],
        )


# --- H3a task 10: the weighted estimator, wired into `summarize_step` ---------
#
# One roster serves the whole group, and it is built so a misaligned weight
# vector cannot pass. Five units carry weights, four of them completed (so four
# rows in `collapsed`), and only three of those four recorded `pred`. The three
# candidate weight vectors therefore give three different answers:
#
#   pred's own carriers  u1, u2, u4 → w = [1, 1, 3] → 10/5  = 2.0     ← correct
#   every collapsed unit u1..u4     → w = [1, 1, 1, 3]      (a strict zip raises;
#                                     a lenient one pairs [1,1,1] → 4/3 ≈ 1.333)
#   every weighted unit  u1..u5     → w = [1, 1, 1, 3, 9]   (as above, or worse)
#
# and `other`, recorded by all four, is the control that must report beside it.
_WEIGHTED_COLLAPSED = {
    "u1": {"pred": 0.0, "other": 1.0},
    "u2": {"pred": 1.0, "other": 1.0},
    "u3": {"other": 2.0},
    "u4": {"pred": 3.0, "other": 1.0},
}
_WEIGHTED_COUNTS = {"resolved": 5.0, "completed": 4.0, "ineligible": 1.0, "failed": 0.0}
# `u5` never completed, so it is in the roster's weights and in no row: the
# mapping `cli.py` builds is roster-wide, and `summarize_step` must filter it.
_WEIGHTS = {"u1": 1.0, "u2": 1.0, "u3": 1.0, "u4": 3.0, "u5": 9.0}


def test_the_recorded_column_value_is_the_weighted_mean_not_the_plain_one():
    """`reference.md` § Weighted samples: core "computes weighted means for
    `basis: units` column metrics". Wiring only the interval would leave the
    point estimate answering the sample's question rather than the population's,
    and would pass any test that looked only at `ci95`.

    `pred` is 0/1/3 over weights 1/1/3, so the weighted mean is 10/5 = 2.0
    exactly against an unweighted 4/3 — two literals, not a direction."""
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights=_WEIGHTS)
    assert out["pred"]["value"] == pytest.approx(2.0)
    assert out["pred"]["value"] != pytest.approx(4 / 3)
    # The control that must report: `other` is 1/1/2/1 over weights 1/1/1/3, so
    # its weighted mean is 7/6 against an unweighted 1.25 — a column whose
    # weighting moves it in the other direction, computed in the same call.
    assert out["other"]["value"] == pytest.approx(7 / 6)


def test_the_weights_are_aligned_to_the_units_the_column_came_from():
    """`raw` is the units that carry the column, not every unit in the table and
    not every unit in the roster, so the weight vector must be filtered and
    ordered the same way. A misalignment weights the wrong unit and produces a
    plausible number rather than an error — which is why the fixture's three
    candidate vectors give three different answers (see above).

    Asserted against `weighted_t_over_units` called with the correctly aligned
    vector written out by hand: that function is pinned to literals of its own
    elsewhere in this file, and what is under test here is which weights reach
    it, not the arithmetic it does with them."""
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights=_WEIGHTS)
    expected = weighted_t_over_units([0.0, 1.0, 3.0], [1.0, 1.0, 3.0])
    assert expected is not None
    assert out["pred"]["method"] == "weighted_t_over_units"
    assert out["pred"]["ci95"] == [pytest.approx(expected.low), pytest.approx(expected.high)]
    # And the literals, so the pin does not rest on a second call to the same
    # function: Σw = 5, Σw² = 11, weighted mean 2.0, Kish's size 25/11 = 2.2727,
    # so df = 1.2727 and the interval is far wider than the unweighted one.
    assert out["pred"]["ci95"] == [
        pytest.approx(-6.720708691694632),
        pytest.approx(10.720708691694632),
    ]


def test_effective_is_recomputed_over_the_units_the_column_actually_has():
    """§ Weighted samples calls `effective` the size the interval "was computed
    at", and `summarize_step` already argues the same case for `completed`:
    reporting the condition-wide figure beside a ragged column's interval "would
    be a lie about how many observations went into it". `runner.attrition`
    computes one `effective` per condition over every completed unit, so a
    ragged column would otherwise print a small `completed` beside an
    `effective` drawn from a larger set, and the df it names would be one no
    interval used.

    `pred`'s three carriers weigh 1/1/3 → 25/11 = 2.2727; the condition's four
    completed units weigh 1/1/1/3 → 36/12 = 3.0, which is what the full column
    `other` must still report.

    **`counts` carries a deliberately impossible 99.0** rather than the 3.0
    `runner.attrition` would really pass. With the true value there, `other`'s
    recomputed size is *also* 3.0, so both of its assertions pass unchanged
    against an implementation that inherits `effective` from `counts` instead of
    setting it — leaving `pred` to carry the whole test alone. 99.0 is what makes
    `other` discriminate: it can only read 3.0 if this column computed it."""
    counts = dict(_WEIGHTED_COUNTS, effective=99.0)
    out = summarize_step(_WEIGHTED_COLLAPSED, counts, weights=_WEIGHTS)
    assert out["pred"]["n"]["completed"] == 3
    assert out["pred"]["n"]["effective"] == pytest.approx(25 / 11)
    assert out["other"]["n"]["completed"] == 4
    assert out["other"]["n"]["effective"] == pytest.approx(3.0)


def test_an_unweighted_summary_is_untouched_to_the_last_digit():
    """The regression the whole wiring must not move: with no `weights` the same
    table gives the same floats it gave before this feature existed. Literals
    captured from the implementation ahead of the change — a suite that only
    compared two runs of the new code to each other could not see a drift."""
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS)
    assert out["pred"]["value"] == 1.3333333333333333
    assert out["pred"]["ci95"] == [-2.4612497002634264, 5.127916366930093]
    assert out["pred"]["method"] == "t_over_units"
    assert "effective" not in out["pred"]["n"]
    assert out["other"]["value"] == 1.25
    assert out["other"]["ci95"] == [0.45438842367907306, 2.045611576320927]


def test_a_weight_summarize_step_cannot_use_is_refused_under_the_shared_code():
    """`units.usable_weight` stays the single authority all the way to the
    record: a weight that reached here unusable is refused with the identifier
    `validate` reports, not absorbed into a plausible mean."""
    with pytest.raises(ContractError) as exc:
        summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights={**_WEIGHTS, "u4": "site-3"})
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_mean_of_is_none_for_an_empty_sequence():
    assert mean_of([]) is None
    assert mean_of([1.0, 2.0]) == 1.5


def test_confidence_widens_the_interval():
    narrow = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.80)
    wide = t_over_units([1.0, 2.0, 3.0, 4.0], confidence=0.99)
    assert narrow is not None and wide is not None
    assert (wide.high - wide.low) > (narrow.high - narrow.low)


def test_the_interval_is_students_t_on_the_differences():
    diffs = [1.0, 2.0, 3.0, 4.0]
    got = paired_t_over_units(diffs)
    plain = t_over_units(diffs)
    assert got is not None and plain is not None
    assert got.low == plain.low and got.high == plain.high


def test_it_names_its_own_method():
    iv = paired_t_over_units([1.0, 2.0, 3.0])
    assert iv is not None and iv.method == "paired_t_over_units"


def test_one_difference_has_no_interval():
    assert paired_t_over_units([1.0]) is None


def test_cohens_dz_is_the_mean_over_the_standard_deviation():
    """Hand-computed: mean 2.5, sample sd of [1,2,3,4] is 1.2909944, so dz = 1.9365."""
    assert cohens_dz([1.0, 2.0, 3.0, 4.0]) == pytest.approx(1.93649167, rel=1e-6)


def test_cohens_dz_is_none_below_two_differences():
    assert cohens_dz([1.0]) is None


def test_cohens_dz_is_none_when_every_difference_is_identical():
    """Zero dispersion would divide by zero; no `d` is honest, infinity is not."""
    assert cohens_dz([2.0, 2.0, 2.0]) is None


def test_cohens_ds_pools_the_two_within_condition_variances():
    """Fixture A: mean 20 over 5 units with s² 5 against mean 10 over 25 units with
    s² 25. The pooled variance is ((4·5) + (24·25)) / 28 = 22.142857…, so the
    pooled sd is 4.705619740571601 and *d*s is 10 / that = 2.1251185925162073.

    **The discriminating alternative is the interval's own denominator.**
    `welch_t_over_units` on this data has SE √2, and 10/√2 is 7.0710678118654755 —
    a factor of 3.33 out. § Statistical reporting states that asymmetry
    deliberately, and this assertion is what makes it checkable rather than
    merely written down.

    An unweighted equal-size fixture could not tell the two apart at all, which is
    why this shares fixture A rather than inventing a tidier one."""
    assert cohens_ds(_WELCH_OF, _WELCH_AGAINST) == pytest.approx(2.1251185925162073)


def test_cohens_ds_is_not_standardized_by_the_welch_denominator():
    """The control that must report, and the number the wrong denominator lands on.
    Asserted as a literal rather than as an inequality: `!=` alone passes for any
    third wrong number, and a *d* is a number readers compare across papers."""
    interval = welch_t_over_units(_WELCH_OF, _WELCH_AGAINST)
    assert interval is not None
    welch_se = (interval.high - interval.low) / 2 / _t_critical(96 / 7, 0.95)
    assert 10.0 / welch_se == pytest.approx(7.0710678118654755)
    assert cohens_ds(_WELCH_OF, _WELCH_AGAINST) != pytest.approx(7.0710678118654755)


def test_cohens_ds_refuses_what_cohens_dz_refuses():
    """`None` below two values on either side, and `None` at zero dispersion — the
    two refusals `cohens_dz` carries, kept so the pair refuses the same inputs. A
    *d* over a denominator that has rounded away is the same invention
    `t_over_units` already declines below two values."""
    assert cohens_ds([1.0], [1.0, 2.0, 3.0]) is None
    assert cohens_ds([1.0, 2.0, 3.0], [1.0]) is None
    assert cohens_ds([2.0, 2.0, 2.0], [1.0, 1.0, 1.0]) is None


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
    got = percentile_over_units(values, seed=7).interval
    assert got.low < sum(values) / len(values) < got.high


def test_it_names_its_method():
    assert percentile_over_units([float(i) for i in range(50)], seed=7).interval.method == (
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
    boot = percentile_over_units(values, seed=7, draws=4000).interval
    analytic = t_over_units(values)
    assert abs(boot.low - analytic.low) < 0.02
    assert abs(boot.high - analytic.high) < 0.02


def test_one_value_has_no_interval():
    assert percentile_over_units([1.0], seed=7).interval is None


def test_percentile_over_units_refuses_a_pool_below_the_honest_floor():
    """The gap `spec-defects.md` recorded: `percentile_of_derived` got a survivor
    floor in S4a and its sibling did not, so this one returns a zero-width
    interval at two draws. Unreachable today (`statistics.resample` is refused),
    which is exactly why it must be closed before the slice that reaches it."""
    values = [float(i) for i in range(60)]
    assert percentile_over_units(values, seed=7, draws=10).interval is None
    assert percentile_over_units(values, seed=7, draws=2000).interval is not None


def test_an_unweighted_percentile_interval_is_untouched_to_the_last_digit():
    """The regression the weighted path must not move. Literals captured from the
    implementation before `weights` existed: every other test in this section
    compares one call to another, so a drift that moved both would pass them
    all."""
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7).interval == Interval(
        low=20.4, high=28.54, method="percentile_over_units"
    )


def test_a_percentile_draw_is_unweighted_while_its_statistic_is_not():
    """`reference.md` § Weighted samples: a percentile interval "draws units as
    usual and recomputes the weighted statistic on each draw, so the weights are
    in the estimate rather than in the drawing". Weighting the draw is a
    different estimator, and the difference is observable in the output.

    21 units: twenty at 1.0, one at 100.0 carrying almost all the weight.
    Drawing UNWEIGHTED, the heavy unit is absent from about a third of the draws
    — (20/21)²¹ ≈ 0.36 — and such a draw has a weighted mean of exactly 1.0, so
    the interval's low bound sits at 1.0. Drawing WEIGHTED, the heavy unit would
    fill nearly every slot of every draw, every weighted mean would be ≈ 100 and
    the interval would collapse to a point up there. The low bound is what
    separates the two estimators; the high bound is what says the statistic is
    still weighted."""
    values = [1.0] * 20 + [100.0]
    weights = [1.0] * 20 + [500.0]
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7).interval
    assert result is not None
    assert result.low == 1.0  # a draw-weighted implementation cannot reach here
    assert result.high > 50.0  # ...while the statistic is still weighted
    # The control that must report: the same pool drawn the same way with the
    # weights dropped is an ordinary bootstrap of a mean near 5.7, so the high
    # bound above is the weighting and not the data's own spread.
    unweighted = percentile_over_units(values, draws=2000, seed=7).interval
    assert unweighted is not None and unweighted.high < 30.0


def test_a_weighted_percentile_keeps_each_value_with_its_own_weight():
    """`percentile_over_units` sorts its pool so the draw depends on the multiset
    rather than on row order. Sorting the values and the weights *separately*
    preserves that invariance and silently re-pairs them, which the equal-weights
    boundary cannot see and which an ascending fixture cannot either — both
    sequences ascending re-pair to themselves.

    So the heavy weight goes on the *smallest* value: twenty units at 100.0 and
    one at 0.0 carrying 500. Paired correctly, a draw containing the heavy unit
    is dragged to near zero and the interval reaches down there; re-paired by a
    separate sort the 500 lands on a 100.0 and every draw's mean is ≈ 100.

    The low bound is asserted against the closed form rather than a captured
    float: a draw holding k copies of the heavy unit has weighted mean
    100·(21−k) / ((21−k) + 500k), and the interval's endpoint must be exactly one
    of those — no value a re-pairing produces is."""
    values = [0.0] + [100.0] * 20
    weights = [500.0] + [1.0] * 20
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7).interval
    assert result is not None
    achievable = [100 * (21 - k) / ((21 - k) + 500 * k) for k in range(22)]
    assert min(abs(result.low - a) for a in achievable) < 1e-9
    assert result.low < 5.0
    # The all-100.0 draw is the largest weighted mean there is, and it happens in
    # about a third of the draws, so the upper endpoint is exactly 100.0.
    assert result.high == 100.0
    # And row order still cannot matter: the pairs travel together through the
    # sort, so a shuffled roster gives the identical interval.
    order = [3, 0, 17, 9, 1, 20, 5, 2, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 18, 19]
    assert (
        result
        == percentile_over_units(
            [values[i] for i in order],
            weights=[weights[i] for i in order],
            draws=2000,
            seed=7,
        ).interval
    )


def test_equal_weights_reproduce_the_unweighted_percentile_exactly():
    """The boundary, digit for digit: at equal weights the weighted mean of a
    draw *is* its plain mean, and the draw itself never depended on the weights,
    so the two constructions must not merely agree closely."""
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, weights=[2.0] * 50, seed=7) == percentile_over_units(
        values, seed=7
    )


def test_a_weight_the_percentile_path_cannot_use_is_refused_before_any_draw():
    """The same single authority, on the resampling path: `units.usable_weight`
    via `checked_weights`, under the identifier `validate` reports."""
    with pytest.raises(ContractError) as exc:
        percentile_over_units([float(i) for i in range(50)], weights=[1.0] * 49 + [0.0], seed=7)
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


# --- H3b task 10: the clustered percentile draw ------------------------------
#
# One roster serves the whole group, and every choice in it is defensive against
# a fixture that cannot see the work:
#
# - **Four clusters, not three.** With G clusters a replicate is G draws, so the
#   all-one-cluster replicate has probability G^-G: 1/27 at G = 3, which is
#   ABOVE the 2.5 % tail and pins both endpoints onto the achievable set's
#   extremes — where "pool the drawn clusters' units" and "average the drawn
#   clusters' means" happen to coincide. At G = 4 it is 1/256, both ranks land
#   interior, and the two constructions separate.
# - **Unequal cluster sizes** (1, 2, 3, 2). Equal sizes make pooling units and
#   averaging cluster means the same estimator, and the document's own "a
#   resampled table has a varying row count" is exactly what equal sizes hide.
# - **Interleaved value ranges.** B spans [0, 22] and C spans [2, 31] with A's
#   single 4.0 inside both, so re-pairing values to clusters through a separate
#   sort moves the answer. Clusters whose ranges are disjoint and ascending
#   re-pair to themselves and see nothing.
# - **Several units per cluster.** One unit per cluster is the same estimator as
#   the unclustered draw; that case appears below only as the boundary pin it is.
_POOL_CLUSTERS: dict[str, list[tuple[float, float]]] = {
    "A": [(4.0, 1.0)],
    "B": [(0.0, 1.0), (22.0, 1.0)],
    "C": [(2.0, 1.0), (12.0, 1.0), (31.0, 9.0)],
    "D": [(6.0, 1.0), (18.0, 1.0)],
}
_POOL_KEYS = ["a1", "b1", "b2", "c1", "c2", "c3", "d1", "d2"]
_POOL_MEMBERSHIP = dict(zip(_POOL_KEYS, ["A", "B", "B", "C", "C", "C", "D", "D"], strict=True))
_POOL_VALUES = [4.0, 0.0, 22.0, 2.0, 12.0, 31.0, 6.0, 18.0]
_POOL_WEIGHTS = [1.0, 1.0, 1.0, 1.0, 1.0, 9.0, 1.0, 1.0]


def _pooled(combo, weighted=False):
    """The statistic one replicate of `combo` produces, from the cluster
    declaration above rather than from the code under test: the drawn clusters'
    units are pooled and the (weighted) mean is taken over the pool."""
    units = [pair for name in combo for pair in _POOL_CLUSTERS[name]]
    if weighted:
        return sum(w * v for v, w in units) / sum(w for _, w in units)
    return sum(v for v, _ in units) / len(units)


def _achievable(weighted=False):
    """Every value a whole-cluster replicate can produce: the 35 multisets of 4
    clusters drawn with replacement, each pooled by `_pooled`. A whole-cluster
    interval's endpoints are members of this set by construction; a unit-drawing
    one's are not, which is what makes the membership assertion structural
    rather than a numeric coincidence."""
    return {
        _pooled(combo, weighted) for combo in itertools.combinations_with_replacement("ABCD", 4)
    }


def test_the_clustered_percentile_draws_clusters_not_units():
    """`reference.md` § Clustered units: "Core draws whole clusters with
    replacement, so a resampled table has a varying row count, and the
    interval's effective `n` is the cluster count."
    `experimental-designs.md` § Mistakes core prevents states the size of it:
    "300 cells from 10 animals give a 10-draw interval".

    Both endpoints are asserted exactly, as the pooled means of two named
    multisets, and additionally as members of the 35-multiset achievable set. A
    resample that draws 8 UNITS with replacement lands almost surely outside
    that set — it can compose 8 values freely, where a 4-cluster draw can only
    compose whole clusters — so the membership assertion catches the mutation
    structurally rather than by the two numbers happening to differ.

    The control that must report is the unclustered interval over the same eight
    values: it reports [5.25, 19.0], neither endpoint achievable by any
    whole-cluster replicate, so the numbers above are the clustering and not the
    data's own spread."""
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    ).interval
    assert got is not None
    assert got.method == "percentile_over_units_clustered"
    assert got.low == _pooled(("A", "A", "A", "D"))  # 36/5
    assert got.high == _pooled(("B", "C", "C", "C"))  # 157/11
    assert got.low in _achievable() and got.high in _achievable()
    plain = percentile_over_units(_POOL_VALUES, seed=7).interval
    assert plain is not None
    assert plain.low == 5.25 and plain.high == 19.0
    assert plain.low not in _achievable() and plain.high not in _achievable()


def test_a_drawn_cluster_pools_its_units_rather_than_contributing_its_mean():
    """ "Core draws whole clusters with replacement, so a resampled table has a
    varying row count" — the row count varies because the units are POOLED, so a
    3-unit cluster carries three rows into the replicate and a 1-unit cluster
    one. Averaging the drawn clusters' means instead gives every cluster equal
    say, which is a different estimator that respects the groups just as
    carefully and is invisible on any equal-sized fixture.

    The two sets overlap, so this asserts membership in the pooled one *and*
    absence from the mean one for these particular endpoints; the control that
    must report is that the mean-of-means construction is non-empty and does
    produce an interval-shaped pair of its own (6.0, 14.0 at this seed)."""
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    ).interval
    assert got is not None
    of_means = {
        sum(sum(v for v, _ in _POOL_CLUSTERS[c]) / len(_POOL_CLUSTERS[c]) for c in combo) / 4
        for combo in itertools.combinations_with_replacement("ABCD", 4)
    }
    # The control that must report: the rival construction produces a real
    # interval of its own over this roster — [6.0, 14.0] at this seed — and
    # neither of its endpoints is achievable by pooling.
    assert 6.0 in of_means and 6.0 not in _achievable()
    assert 14.0 in of_means and 14.0 not in _achievable()
    assert got.low in _achievable() and got.low not in of_means
    assert got.high in _achievable() and got.high not in of_means


def test_the_clustered_percentile_keeps_each_value_with_its_cluster():
    """`percentile_over_units` sorts its pool so the draw depends on the multiset
    rather than on row order, and the clustered form must keep each value with
    its CLUSTER through that sort — exactly as the weighted form keeps each value
    with its own weight. Sorting the values and the cluster labels as separate
    sequences preserves the invariance and silently re-groups them.

    The re-paired construction is built here, independently, and must report: it
    produces [2.0, 21.666…], a perfectly interval-shaped answer whose endpoints
    are not achievable by any whole-cluster replicate of the declared roster."""
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    ).interval
    assert got is not None
    repaired: dict[str, list[tuple[float, float]]] = {}
    for value, label in zip(sorted(_POOL_VALUES), sorted(_POOL_MEMBERSHIP.values()), strict=True):
        repaired.setdefault(label, []).append((value, 1.0))
    rng = random.Random(7)
    ordered = sorted(sorted(pool) for pool in repaired.values())
    means = []
    for _ in range(2000):
        drawn = [pair for _ in range(4) for pair in ordered[rng.randrange(4)]]
        means.append(sum(v for v, _ in drawn) / len(drawn))
    means.sort()
    assert (means[49], means[1949]) == (2.0, 65 / 3)
    assert means[49] not in _achievable() and means[1949] not in _achievable()
    assert (means[49], means[1949]) != (got.low, got.high)


def test_the_clustered_percentile_is_invariant_to_row_order_and_to_cluster_labels():
    """Row order, because the draw must depend on the multiset of clusters and
    not on the sequence the roster arrived in. Cluster labels, because the
    clusters are ordered by their own sorted contents rather than by name — a
    site renamed from `S1` to `zzz` is not a different experiment."""
    got = percentile_over_units_clustered(_POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7)
    order = [5, 0, 3, 7, 1, 4, 2, 6]
    assert got == percentile_over_units_clustered(
        [_POOL_VALUES[i] for i in order],
        [_POOL_KEYS[i] for i in order],
        _POOL_MEMBERSHIP,
        seed=7,
    )
    renamed = {"A": "zzz", "B": "aaa", "C": "mmm", "D": "kkk"}
    assert got == percentile_over_units_clustered(
        _POOL_VALUES,
        _POOL_KEYS,
        {key: renamed[label] for key, label in _POOL_MEMBERSHIP.items()},
        seed=7,
    )


def test_one_cluster_of_many_units_has_no_percentile_interval():
    """The floor, and it is a derivation rather than an analogy to
    `t_over_units_clustered`'s df — a percentile interval has none. At G = 1
    every replicate draws the same single cluster, so the resampled distribution
    is a point mass and both ranks land on it: a zero-width 95 % interval, which
    § Statistical reporting refuses in those words. Reporting a point with no
    interval is the honest answer for one draw."""
    assert (
        percentile_over_units_clustered(
            _POOL_VALUES, _POOL_KEYS, dict.fromkeys(_POOL_KEYS, "only"), seed=7
        ).interval
        is None
    )


def test_two_clusters_still_report_a_percentile():
    """The control that must report, immediately above the floor: G = 2 has three
    achievable replicates, so the interval has real width and is not refused.
    There is deliberately no higher threshold here — the judgment that a
    cluster count is too small for a resample belongs to `limits.min_clusters`,
    which `validate` warns on."""
    membership = dict.fromkeys(_POOL_KEYS, "left")
    for key in ("c1", "c2", "c3", "d1", "d2"):
        membership[key] = "right"
    got = percentile_over_units_clustered(_POOL_VALUES, _POOL_KEYS, membership, seed=7).interval
    assert got is not None
    assert got.high > got.low


def test_two_content_identical_clusters_refuse_a_zero_width_interval():
    """`groups < 2` is a COUNT floor and answers a different question from
    whether the draw can ever vary: two clusters both holding the single value
    0.5 pass that floor (`G == 2`) but every achievable replicate pools some
    multiset of two identical numbers, so the mean is 0.5 on every draw and the
    interval would be `Interval(0.5, 0.5)` — the same "a zero-width 95%
    interval is not honest" shape `percentile_over_units`'s own strata branch
    already refuses for content-identical strata (`reference.md` § Statistical
    reporting). The row-level sibling's check is content-based, not
    count-based, and this construction now asks the same question one level
    up, over clusters rather than over values."""
    values = [0.5, 0.5, 0.5, 0.5]
    keys = ["a1", "a2", "b1", "b2"]
    membership = {"a1": "A", "a2": "A", "b1": "B", "b2": "B"}
    assert (
        percentile_over_units_clustered(values, keys, membership, seed=1, draws=2000).interval
        is None
    )
    # Positive companion: `test_two_clusters_still_report_a_percentile` above is
    # the same `G == 2` shape with clusters that differ in content, and it must
    # keep reporting — this is a content check, not a second count floor.


@pytest.mark.parametrize("values", [[], [1.0]])
def test_the_clustered_percentile_needs_two_values(values):
    """`percentile_over_units`' own floor, kept in front of the cluster one so the
    two constructions refuse the same degenerate inputs."""
    keys = [f"u{i}" for i in range(len(values))]
    assert (
        percentile_over_units_clustered(values, keys, dict.fromkeys(keys, "c"), seed=7).interval
        is None
    )


def test_the_clustered_percentile_refuses_a_draw_count_below_the_honest_floor():
    """Orthogonal to the cluster floor: this one is about how many replicates the
    ranks are read off, not how many things each replicate draws."""
    assert (
        percentile_over_units_clustered(
            _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, draws=10
        ).interval
        is None
    )
    assert (
        percentile_over_units_clustered(
            _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, draws=2000
        ).interval
        is not None
    )


def test_one_unit_per_cluster_reproduces_the_unclustered_percentile():
    """The boundary that proves this is a generalization rather than a different
    statistic — and a fixture that can see nothing else, which is exactly why it
    is not the headline: with G = n each replicate draws n singleton clusters and
    pools one unit from each, which is the unclustered draw index for index.

    Digit for digit against the literals
    `test_an_unweighted_percentile_interval_is_untouched_to_the_last_digit` pins,
    so this is also the statement that ordering clusters by their sorted contents
    (rather than by label) is what keeps the two identical."""
    values = [float(i) for i in range(50)]
    keys = [f"u{i}" for i in range(50)]
    got = percentile_over_units_clustered(values, keys, {k: k for k in keys}, seed=7).interval
    assert got is not None
    assert (got.low, got.high) == (20.4, 28.54)
    plain = percentile_over_units(values, seed=7).interval
    assert plain is not None
    assert (got.low, got.high) == (plain.low, plain.high)


def test_a_clustered_percentile_draw_is_by_cluster_while_its_statistic_is_weighted():
    """`reference.md` § Weighted samples: a percentile interval "recomputes the
    weighted statistic on each draw, so the weights are in the estimate rather
    than in the drawing", and "`cluster_by` still decides the draw when both are
    declared, since a cluster is what's independent and a weight is what it
    represents". The two sentences compose: the draw moves to clusters, the
    weights stay in the estimate.

    C's 31.0 carries weight 9, so a replicate holding C is dragged upward while
    one holding none of it is untouched. Both endpoints are asserted exactly
    against `_pooled(..., weighted=True)` and as members of the weighted
    achievable set.

    The control that must report is the unweighted clustered interval over the
    same roster: its high bound is 157/11 ≈ 14.27 where the weighted one is 25.8,
    so the upper endpoint is the weighting. Its LOW bound is identical, and that
    is the fixture telling the truth rather than a coincidence — the low tail's
    replicates contain no C at all, so there is no heavy weight in them to
    matter."""
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, weights=_POOL_WEIGHTS
    ).interval
    assert got is not None
    assert got.method == "percentile_over_units_clustered"
    assert got.low == _pooled(("A", "A", "A", "D"), weighted=True)
    assert got.high == _pooled(("C", "C", "C", "D"), weighted=True)
    assert got.low in _achievable(True) and got.high in _achievable(True)
    unweighted = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    ).interval
    assert unweighted is not None
    assert unweighted.high == _pooled(("B", "C", "C", "C"))
    assert got.high > unweighted.high * 1.5


def test_equal_weights_reproduce_the_unweighted_clustered_percentile_exactly():
    """The boundary, digit for digit: at equal weights the weighted mean of a
    pooled replicate *is* its plain mean, and the draw never depended on the
    weights, so the two constructions must not merely agree closely."""
    assert percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, weights=[3.0] * 8
    ) == percentile_over_units_clustered(_POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7)


def test_a_weight_the_clustered_percentile_cannot_use_is_refused_before_any_draw():
    """The same single authority on this path too: `units.usable_weight` via
    `checked_weights`, under the identifier `validate` reports — and before the
    grouping, rather than after 2000 replicates of `nan`."""
    with pytest.raises(ContractError) as exc:
        percentile_over_units_clustered(
            _POOL_VALUES,
            _POOL_KEYS,
            _POOL_MEMBERSHIP,
            seed=7,
            weights=[1.0] * 7 + [0.0],
        )
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_a_unit_outside_the_clustered_percentile_membership_is_not_absorbed():
    """`units.cluster_count_of`'s discipline, from this caller's side: a key the
    membership doesn't hold is a core defect, and a cluster of its own for it
    would raise G and change the draw instead of failing."""
    with pytest.raises(KeyError):
        percentile_over_units_clustered(
            [1.0, 2.0, 3.0], ["u1", "u2", "u3"], {"u1": "c1", "u2": "c2"}, seed=7
        )


def test_the_same_seed_reproduces_the_clustered_percentile():
    """Reproducibility only, deliberately without the "a different seed moves it"
    half its unclustered sibling carries: a 4-cluster draw has 35 achievable
    replicates and this roster's endpoints are the same two on every seed tried
    (7, 1, 42, 99, 2026, 13). That discreteness is the clustered draw telling the
    truth — 4 clusters really are 4 draws — and a fixture large enough to make
    the seed move the answer would be a different test's fixture."""
    assert percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    ) == percentile_over_units_clustered(_POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7)
    values = [float(i) for i in range(50)]
    keys = [f"u{i}" for i in range(50)]
    membership = {key: f"c{i // 2}" for i, key in enumerate(keys)}
    assert percentile_over_units_clustered(
        values, keys, membership, seed=7
    ) != percentile_over_units_clustered(values, keys, membership, seed=99)


def _clustered_banded() -> tuple[list[float], list[str], dict[str, str], list[str]]:
    """Six clusters of unequal size across three strata, with disjoint value
    bands per stratum — so a cluster draw ignoring the strata, a correct
    stratified cluster draw, and a row-level draw all give different intervals.

    Stratum `low`  : clusters c0 (4 units), c1 (3) — values in [0, 1)
    Stratum `mid`  : clusters c2 (3), c3 (2)       — values in [10, 11)
    Stratum `high` : clusters c4 (2), c5 (1)       — values in [100, 101)
    """
    values: list[float] = []
    keys: list[str] = []
    membership: dict[str, str] = {}
    strata: list[str] = []
    plan = [
        ("c0", "low", 4, 0.0),
        ("c1", "low", 3, 0.5),
        ("c2", "mid", 3, 10.0),
        ("c3", "mid", 2, 10.5),
        ("c4", "high", 2, 100.0),
        ("c5", "high", 1, 100.5),
    ]
    for cluster, stratum, size, base in plan:
        for i in range(size):
            key = f"{cluster}_u{i}"
            values.append(base + i / 100.0)
            keys.append(key)
            membership[key] = cluster
            strata.append(stratum)
    return values, keys, membership, strata


def test_a_clustered_stratified_draw_takes_clusters_within_strata():
    """`stratify_by` says what an independent draw is; `cluster_by` says the
    draw IS a cluster. Composed: two clusters are drawn from each stratum
    (each stratum holds two), so every replicate carries all three bands and the
    interval is far narrower than the unstratified cluster draw, where a single
    replicate can hold six `high` clusters."""
    values, keys, membership, strata = _clustered_banded()
    stratified = percentile_over_units_clustered(
        values, keys, membership, seed=13, draws=2000, strata=strata
    ).interval
    plain = percentile_over_units_clustered(values, keys, membership, seed=13, draws=2000).interval
    assert stratified is not None and plain is not None
    assert (stratified.high - stratified.low) < (plain.high - plain.low) / 2.0
    assert stratified.method == "percentile_over_units_clustered"


def test_a_clustered_stratified_draw_weights_the_pooled_units_not_the_pick():
    """`weight_by`, `cluster_by` and `stratify_by` are three independently
    declarable fields, so a config naming all three is an ordinary shape, not
    an edge case — § Weighted samples' composition (the draw moves to
    clusters, the weights stay in the estimate) has to survive stratification
    too. `c5` (the lone `high` cluster) carries weight 9 here; pinned
    digit-for-digit at seed=13, both endpoints move up from the unweighted
    stratified interval because that heavy cluster now drags every replicate
    that draws it further than an equal weight would."""
    values, keys, membership, strata = _clustered_banded()
    weights = [9.0 if membership[k] == "c5" else 1.0 for k in keys]
    weighted = percentile_over_units_clustered(
        values, keys, membership, seed=13, draws=2000, strata=strata, weights=weights
    ).interval
    unweighted = percentile_over_units_clustered(
        values, keys, membership, seed=13, draws=2000, strata=strata
    ).interval
    assert weighted is not None and unweighted is not None
    assert weighted.low == 26.54
    assert weighted.high == 64.2448275862069
    assert weighted.low > unweighted.low
    assert weighted.high > unweighted.high


class _RecordingRandom(random.Random):
    """Wraps `random.Random` to record the `n` argument of every `randrange`
    call, in order — catching two mutations an interval-shaped assertion
    cannot. First: substituting a constant 1 for `len(group)` in the draw loop
    still narrows the interval on `_clustered_banded` (three strata of two
    clusters each), because that fixture's extremes are single-cluster values
    a one-cluster-per-stratum draw reaches exactly as surely as a two-cluster
    one — pooling several picks of the SAME extreme cluster reproduces that
    cluster's own mean. Second, and the reason a bare call COUNT is not
    enough either: a mutation that makes every stratum draw the FIRST
    stratum's cluster count is invisible to a total on a fixture whose strata
    all hold the same count, and even an unevenly-sized fixture can still sum
    to the right total under some reordering. Recording each call's `n` in
    sequence, over a fixture whose three strata hold DIFFERENT counts (1, 2,
    3), pins the exact per-stratum composition rather than a total that
    several wrong constructions could also produce."""

    calls: list[int] = []

    def randrange(self, n: int, *args: object, **kwargs: object) -> int:
        type(self).calls.append(n)
        return super().randrange(n, *args, **kwargs)  # type: ignore[arg-type]


def _clustered_uneven_stratum_counts() -> tuple[list[float], list[str], dict[str, str], list[str]]:
    """Three strata holding a DIFFERENT number of clusters each — 1, 2, 3 — so a
    mutation that draws every stratum's own count correctly is distinguishable
    from one that draws some OTHER stratum's count, or a constant, even when a
    coincidental total would otherwise hide it (`_clustered_banded`'s 2/2/2
    cannot: "draw the first stratum's count" sums to 6 either way there)."""
    values: list[float] = []
    keys: list[str] = []
    membership: dict[str, str] = {}
    strata: list[str] = []
    plan = [
        ("c0", "low", 4, 0.0),
        ("c1", "mid", 3, 10.0),
        ("c2", "mid", 2, 10.5),
        ("c3", "high", 2, 100.0),
        ("c4", "high", 1, 100.5),
        ("c5", "high", 1, 100.75),
    ]
    for cluster, stratum, size, base in plan:
        for i in range(size):
            key = f"{cluster}_u{i}"
            values.append(base + i / 100.0)
            keys.append(key)
            membership[key] = cluster
            strata.append(stratum)
    return values, keys, membership, strata


def test_a_clustered_stratified_draw_gives_each_stratum_exactly_its_own_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The composition rule pinned by SEQUENCE, not by total: `low` holds 1
    cluster, `mid` holds 2, `high` holds 3, and the value bands keep
    `stratum_pools` sorted in that order, so one replicate's calls to
    `randrange` must read `n = 1, 2, 2, 3, 3, 3` in that exact order — one
    stratum contributing its own count, not the first stratum's count applied
    everywhere (which would read `1, 1, 1, 1, 1, 1` here and still total the
    wrong number honestly, rather than hiding behind a coincidental match)."""
    monkeypatch.setattr("publishable.stats.random.Random", _RecordingRandom)
    values, keys, membership, strata = _clustered_uneven_stratum_counts()
    _RecordingRandom.calls = []
    percentile_over_units_clustered(values, keys, membership, seed=1, draws=80, strata=strata)
    assert _RecordingRandom.calls[:6] == [1, 2, 2, 3, 3, 3]
    assert _RecordingRandom.calls == [1, 2, 2, 3, 3, 3] * 80


def test_a_clustered_stratified_draw_refuses_a_stratum_that_varies_within_a_cluster():
    """A cluster is indivisible, so it cannot be dealt to two strata. The same
    rule § Clustered units already imposes on `fold`, `holdout` and `assign`,
    reported under this construction's own code because `stats.py` is handed the
    two vectors directly and cannot pick one."""
    values, keys, membership, strata = _clustered_banded()
    strata[0] = "mid"  # c0_u0 now disagrees with the rest of c0
    with pytest.raises(ContractError) as exc:
        percentile_over_units_clustered(
            values, keys, membership, seed=13, draws=2000, strata=strata
        )
    assert exc.value.code == "E-STATS-RESAMPLE-STRATIFY-VARIES"
    assert "c0" in str(exc.value)
    # Positive companion: the UNMUTATED vector does not raise, so this cannot
    # pass by the construction refusing every stratified clustered draw.
    _, _, _, clean = _clustered_banded()
    assert (
        percentile_over_units_clustered(
            values, keys, membership, seed=13, draws=2000, strata=clean
        ).interval
        is not None
    )


def test_a_clustered_stratified_draws_constancy_check_agrees_with_validates():
    """`validate` reads a cluster's stratum values through
    `units.stratum_varies_within_cluster`, which renders each as `"no value"` for
    `None` and `str(value)` otherwise before comparing — so a column read back as
    `1` for one unit and `"1"` for another (a real possibility across a resolver
    and a table-sourced attribute) is ONE value to that check. `stats.py` cannot
    import `units.py` to share that predicate, so it re-implements the identical
    normalization — this is the case that would disagree if it compared raw
    values instead: `c0`'s two units carry `1` and `"1"`, which raw `!=` calls a
    variation and `str()`-equality does not."""
    values = [0.0, 1.0, 2.0, 3.0, 10.0, 11.0, 12.0, 13.0]
    keys = ["c0_u0", "c0_u1", "c1_u0", "c1_u1", "c2_u0", "c2_u1", "c3_u0", "c3_u1"]
    membership = {
        "c0_u0": "c0",
        "c0_u1": "c0",
        "c1_u0": "c1",
        "c1_u1": "c1",
        "c2_u0": "c2",
        "c2_u1": "c2",
        "c3_u0": "c3",
        "c3_u1": "c3",
    }
    strata = [1, "1", "1", "1", "a", "a", "a", "a"]
    got = percentile_over_units_clustered(
        values, keys, membership, seed=1, draws=2000, strata=strata
    ).interval
    assert got is not None


def test_a_clustered_stratified_draw_refuses_a_zero_width_interval_too():
    """Each stratum holding fewer than two clusters is the stratified path's own
    degenerate case, not the unstratified `groups < 2` guard's — three clusters
    overall passes that guard, but if every stratum owns exactly one of them,
    each stratum always redraws its single cluster and every replicate is the
    same multiset. `percentile_over_units`'s own strata branch returns `None`
    for the analogous all-strata-constant shape (`reference.md` § Statistical
    reporting: "a zero-width 95% interval is not honest"), and this is the same
    answer, not a second rule."""
    values = [0.0, 1.0, 10.0, 11.0, 20.0, 21.0]
    keys = ["c0_u0", "c0_u1", "c1_u0", "c1_u1", "c2_u0", "c2_u1"]
    membership = {
        "c0_u0": "c0",
        "c0_u1": "c0",
        "c1_u0": "c1",
        "c1_u1": "c1",
        "c2_u0": "c2",
        "c2_u1": "c2",
    }
    one_cluster_each = ["a", "a", "b", "b", "c", "c"]
    assert (
        percentile_over_units_clustered(
            values, keys, membership, seed=1, draws=2000, strata=one_cluster_each
        ).interval
        is None
    )
    # Positive companion: the same roster, but `a` now holds two of the three
    # clusters — one stratum can vary, so the interval is reportable again,
    # which is what tells this apart from a construction that refuses every
    # stratified clustered draw regardless of shape.
    two_in_one_stratum = ["a", "a", "a", "a", "b", "b"]
    assert (
        percentile_over_units_clustered(
            values, keys, membership, seed=1, draws=2000, strata=two_in_one_stratum
        ).interval
        is not None
    )


def test_a_clustered_stratified_draw_refuses_content_identical_strata_too():
    """The COUNT check above (each stratum owning fewer than two clusters) does
    not cover every degenerate shape: two strata, each holding TWO clusters
    whose content is identical within the stratum, pass that count check but
    still cannot vary — drawing either of a stratum's two identical clusters
    with replacement reproduces the same pooled contribution every time, so
    the interval would be `Interval(0.5, 5.5)` on every draw, not honest as a
    95% interval. This is the content-based check one level up from
    `percentile_over_units`'s own ("every stratum's own (value, weight) pairs
    are all identical"), and it must not regress to the count-only form."""
    values = [0.5, 0.5, 0.5, 0.5, 5.5, 5.5, 5.5, 5.5]
    keys = ["a1", "a2", "b1", "b2", "c1", "c2", "d1", "d2"]
    membership = {
        "a1": "A",
        "a2": "A",
        "b1": "B",
        "b2": "B",
        "c1": "C",
        "c2": "C",
        "d1": "D",
        "d2": "D",
    }
    identical_within_stratum = ["x", "x", "x", "x", "y", "y", "y", "y"]
    assert (
        percentile_over_units_clustered(
            values, keys, membership, seed=1, draws=2000, strata=identical_within_stratum
        ).interval
        is None
    )
    # Positive companion: giving stratum `y`'s two clusters different content
    # restores real variance, so this cannot pass by refusing every
    # two-cluster-per-stratum shape regardless of content.
    values_varying = [0.5, 0.5, 0.5, 0.5, 5.5, 5.5, 9.5, 9.5]
    assert (
        percentile_over_units_clustered(
            values_varying,
            keys,
            membership,
            seed=1,
            draws=2000,
            strata=identical_within_stratum,
        ).interval
        is not None
    )


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
    result = percentile_over_units([0.0, 1.0], seed=7, draws=2000, confidence=0.95).interval
    assert result == Interval(low=0.0, high=0.5, method="percentile_over_units")


def _mean_m(t):
    vals = [v for v in t.m if v is not None]
    return sum(vals) / len(vals) if vals else None


def test_interval_at_reads_a_wider_pair_of_ranks_at_a_smaller_alpha():
    """A corrected interval is an interval at a smaller α. Read off the same
    pool, a smaller α must reach further into both tails — that is the whole
    mechanism, and the nesting it produces is what makes a corrected interval
    honest beside its raw one."""
    pool = [float(i) for i in range(2000)]
    raw = interval_at(pool, 0.95)
    corrected = interval_at(pool, 1.0 - 0.025)
    assert raw is not None and corrected is not None
    assert corrected[0] < raw[0]
    assert corrected[1] > raw[1]


def test_interval_at_refuses_a_pool_too_small_for_the_level():
    """`min_honest_draws` is the floor below which both percentile ranks are not
    interior and the interval is systematically too narrow. At α/40 the floor is
    3201 draws, so a 2000-draw pool has no honest interval at that level — and a
    number would be worse than a null."""
    pool = [float(i) for i in range(2000)]
    assert min_honest_draws(1.0 - 0.00125) > 2000
    assert interval_at(pool, 1.0 - 0.00125) is None
    assert interval_at(pool, 0.95) is not None


def test_interval_at_refuses_an_unsorted_pool_rather_than_reading_two_positions():
    """The filing H4b-2 restored and H4c claims. `interval_at` reads fixed ranks off
    a pool, so an unsorted one returns two arbitrary values that look exactly like an
    interval — and this slice added a construction returning a pool, which is the
    seam that made the precondition worth asserting rather than documenting.

    The sorted control must report, because an assertion that fires on every input
    would pass the negative case too."""
    ordered = [float(i) for i in range(400)]
    assert interval_at(ordered, 0.95) is not None  # the control
    with pytest.raises(AssertionError, match="sorted"):
        interval_at(list(reversed(ordered)), 0.95)


def test_the_paired_resample_carries_the_pool_it_read_its_interval_from():
    """The corrected interval comes from this pool, so the raw interval's own
    endpoints must be in it at the raw ranks. Returning a pool that is not the
    one the interval was read off would make every corrected interval a
    different construction's answer."""
    of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = paired_percentile_of_derived(of, against, sorted(of), _mean_m, _mean_m, seed=7)
    assert isinstance(got, PairedResample)
    assert got.interval is not None
    assert len(got.pool) == got.draws_used
    assert got.pool == sorted(got.pool)
    lo, hi = _percentile_ranks(len(got.pool), 0.95)
    assert got.pool[lo] == got.interval.low
    assert got.pool[hi] == got.interval.high


def test_percentile_of_derived_carries_the_pool_it_read_its_interval_from():
    """The same pin as `paired_percentile_of_derived`'s own pool test, one
    construction over: `percentile_of_derived` recomputes a derived metric on
    each draw and previously threw the resulting pool away. Reading the same
    ranks back off the returned pool with `interval_at` must reproduce the
    interval exactly — an assertion satisfied only by the ACTUAL pool
    `interval` was read off, not by a re-drawn or re-sorted stand-in that
    merely looks like one (non-empty, sorted, right length)."""
    collapsed = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = percentile_of_derived(collapsed, _mean_m, seed=7, draws=500)
    assert isinstance(got, PairedResample)
    assert got.interval is not None
    assert len(got.pool) == got.draws_used
    assert got.pool == sorted(got.pool)
    assert interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)


def test_percentile_of_derived_clustered_carries_the_pool_it_read_its_interval_from():
    """The clustered sibling's own version of the same pin: the pool
    `percentile_of_derived_clustered` returns must be the sequence of drawn
    cluster-pool means `interval_at` actually indexed, not an equivalent-
    looking stand-in."""
    collapsed = {f"c{c}_{i}": {"m": float(10 * c + i)} for c in range(1, 5) for i in range(c + 2)}
    clusters = {key: key.split("_")[0] for key in collapsed}
    got = percentile_of_derived_clustered(collapsed, clusters, _mean_m, seed=3, draws=500)
    assert isinstance(got, PairedResample)
    assert got.interval is not None
    assert len(got.pool) == got.draws_used
    assert got.pool == sorted(got.pool)
    assert interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)


def test_the_paired_interval_is_narrower_than_two_independent_draws():
    """The property that makes pairing worth doing. Two conditions that move
    together have a stable difference even when each side is highly variable —
    an implementation drawing independently loses exactly that.

    The per-unit difference alternates 1.0/0.0 (mean 0.5) rather than being a
    constant 0.5 offset: a constant offset makes the paired difference exactly
    0.5 on *every* resample regardless of which units are drawn, which would
    demonstrate the narrowing with a degenerate zero-width interval instead of
    a real one."""
    of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    keys = sorted(of)
    paired = paired_percentile_of_derived(of, against, keys, _mean_m, _mean_m, seed=7).interval
    a = percentile_of_derived(of, _mean_m, seed=7).interval
    b = percentile_of_derived(against, _mean_m, seed=7).interval
    independent_width = (a.high - a.low) + (b.high - b.low)
    assert (paired.high - paired.low) < independent_width / 4


def test_the_interval_brackets_the_observed_difference():
    of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = paired_percentile_of_derived(of, against, sorted(of), _mean_m, _mean_m, seed=7).interval
    assert got.low < 0.5 < got.high


def test_it_names_its_own_method_paired_percentile():
    of = {f"u{i}": {"m": float(i) + 1.0} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = paired_percentile_of_derived(of, against, sorted(of), _mean_m, _mean_m, seed=7).interval
    assert got.method == "paired_percentile_over_units"


def test_the_same_seed_reproduces_and_a_different_one_does_not_paired():
    of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    k = sorted(of)
    assert paired_percentile_of_derived(
        of, against, k, _mean_m, _mean_m, seed=7
    ) == paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=7)
    assert paired_percentile_of_derived(
        of, against, k, _mean_m, _mean_m, seed=7
    ) != paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=99)


def test_below_the_survivor_floor_there_is_no_interval_paired():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    result = paired_percentile_of_derived(
        of, against, sorted(of), lambda t: None, lambda t: None, seed=7, draws=200
    )
    assert result.interval is None and result.draws_used == 0


def test_a_constant_offset_gives_a_genuinely_zero_width_interval():
    """A point-mass bootstrap: every unit's difference is the same constant 0.5,
    so the resampled difference is 0.5 on *every* draw regardless of which units
    are drawn. That is not a bug — a difference with no sampling variability
    should report no width — and it is a sharper discriminator against an
    independently-drawn variant than the alternating fixture above: paired width
    is exactly 0.0 against a nonzero independent width, an unbounded ratio
    rather than a merely large one."""
    of = {f"u{i}": {"m": float(i) + 0.5} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = paired_percentile_of_derived(of, against, sorted(of), _mean_m, _mean_m, seed=7).interval
    assert got is not None
    assert got.high - got.low < 1e-9


def test_a_raising_compute_is_treated_as_degenerate_not_propagated_paired():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}

    def always_raises(units):
        raise ZeroDivisionError("degenerate draw")

    result = paired_percentile_of_derived(
        of, against, sorted(of), always_raises, always_raises, seed=7, draws=20
    )
    assert result.interval is None
    assert result.draws_used == 0


def test_a_nan_compute_is_treated_as_degenerate_paired():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}

    def always_nan(units):
        return float("nan")

    result = paired_percentile_of_derived(
        of, against, sorted(of), always_nan, always_nan, seed=7, draws=20
    )
    assert result.interval is None
    assert result.draws_used == 0


def test_a_one_sided_raise_drops_the_whole_draw_not_half():
    """A defect that narrows the `try` to only one side's `compute` call — the
    exact regression Finding 1 named — would leave the other side's exception
    unguarded, crashing the whole function rather than dropping just that
    draw. `compute` is called twice per draw, `of` then `against` (see the
    call order in `paired_percentile_of_derived`), so failing every fourth
    call fails only the `against` side, on exactly every other draw, while
    `of` always succeeds — pinning that a one-sided failure drops the whole
    draw rather than surviving on the strength of the healthy side."""
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    calls = {"n": 0}

    def flaky_against_only(units):
        calls["n"] += 1
        if calls["n"] % 4 == 0:
            raise ZeroDivisionError("degenerate on this call only")
        return float(sum(v for v in units.m if v is not None)) / len(units.m)

    draws = 200
    result = paired_percentile_of_derived(
        of, against, sorted(of), flaky_against_only, flaky_against_only, seed=7, draws=draws
    )
    assert result.draws_used == draws // 2
    assert result.interval is not None


def test_a_one_sided_none_drops_the_whole_draw_not_half():
    """The `None`-flavoured sibling of the test above: checking only `a is
    None` (omitting the `against`-side check) would let a `None` on `against`
    reach `float(a) - float(b)` and crash on `TypeError` instead of being
    dropped as a degenerate draw."""
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    calls = {"n": 0}

    def flaky_against_only(units):
        calls["n"] += 1
        if calls["n"] % 4 == 0:
            return None
        return float(sum(v for v in units.m if v is not None)) / len(units.m)

    draws = 200
    result = paired_percentile_of_derived(
        of, against, sorted(of), flaky_against_only, flaky_against_only, seed=7, draws=draws
    )
    assert result.draws_used == draws // 2
    assert result.interval is not None


def test_two_different_computes_over_identical_tables_yield_a_real_interval():
    """The regression a single shared `compute` produces, and the reason this
    function takes two: `of` and `against` here hold *identical* per-unit
    data — exactly the shape a swept axis that doesn't touch the recorded
    columns produces (the documented worked example's `analysis.method`
    sweep records the same `pred`/`truth` under every condition; only which
    correlation `aggregate` computes from them differs). A version of this
    function taking one `compute` shared by both sides would evaluate that
    one formula against both sides' identical draws and report a spuriously
    precise — often exactly zero-width — interval no matter how different
    the two conditions' real formulas are. `compute_of` (`total`) and
    `compute_against` (`mean`) are deliberately different formulas over the
    same data, so a correct implementation must still produce a real,
    non-degenerate interval that brackets the true, unresampled difference
    between the two formulas."""
    table = {f"u{i}": {"m": float(i)} for i in range(60)}

    def total(units: UnitTable) -> float | None:
        return float(sum(v for v in units.m if v is not None))

    def mean(units: UnitTable) -> float | None:
        vals = [v for v in units.m if v is not None]
        return sum(vals) / len(vals) if vals else None

    point_estimate = total(UnitTable(table)) - mean(UnitTable(table))
    result = paired_percentile_of_derived(table, table, sorted(table), total, mean, seed=7)
    got, used = result.interval, result.draws_used
    assert got is not None
    assert used > 0
    assert got.high - got.low > 0  # non-degenerate: the two formulas disagree
    assert got.low < point_estimate < got.high


def test_the_paired_delta_is_computed_over_the_keys_it_is_given():
    """The point estimate `paired_percentile_of_derived` builds an interval for,
    over the same keys — so a caller cannot take one from the intersection and
    the other from each side's whole sample, which is what put a `delta` of
    509.5 beside a `ci95` around 10.0 in a `within` contrast."""
    of = {f"u{i}": {"m": float(i) + 1.0} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    assert paired_delta_of_derived(of, against, sorted(of), _mean_m, _mean_m) == 1.0
    # Six keys with a mean of 2.5 on `of` against 1.5 — the same +1.0 shift, but
    # the value of `_mean_m` itself is entirely different from the whole-sample
    # one, so a subset genuinely reaches a different pair of aggregates.
    subset = [f"u{i}" for i in range(4)]
    assert paired_delta_of_derived(of, against, subset, _mean_m, _mean_m) == 1.0
    assert _mean_m(UnitTable({k: of[k] for k in subset})) == 2.5


def test_the_paired_delta_uses_each_side_s_own_formula():
    """Two computes, for the reason `paired_percentile_of_derived` takes two:
    passing `compute_of` for both sides here returns 0.0, not 59.0."""
    table = {f"u{i}": {"m": float(i)} for i in range(60)}

    def top(units: UnitTable) -> float | None:
        return float(max(v for v in units.m if v is not None))

    got = paired_delta_of_derived(table, table, sorted(table), top, _mean_m)
    assert got == pytest.approx(59.0 - 29.5)


def test_an_empty_intersection_has_no_delta_rather_than_a_zero_one():
    """`reference.md` § Contrasts: "A contrast whose intersection is empty is
    reported as such rather than as a delta of zero." `0.0` would read as two
    conditions that agreed perfectly."""
    of = {f"u{i}": {"m": float(i)} for i in range(10)}
    assert paired_delta_of_derived(of, of, [], _mean_m, _mean_m) is None


def test_a_declining_compute_yields_no_delta_on_either_side():
    """A raising or `None`-returning `aggregate` is the degenerate treatment
    `percentile_of_derived` gives it, not a `TypeError` from `float(None)` and
    not a half-computed number."""
    of = {f"u{i}": {"m": float(i)} for i in range(10)}

    def gives_none(units: UnitTable) -> float | None:
        return None

    def raises(units: UnitTable) -> float | None:
        raise ZeroDivisionError("no")

    keys = sorted(of)
    assert paired_delta_of_derived(of, of, keys, gives_none, _mean_m) is None
    assert paired_delta_of_derived(of, of, keys, _mean_m, gives_none) is None
    assert paired_delta_of_derived(of, of, keys, raises, _mean_m) is None
    assert paired_delta_of_derived(of, of, keys, _mean_m, raises) is None


def test_beside_n_cannot_shadow_a_computed_metric_key():
    """`beside_n` is core-supplied context copied into every metric block, and the
    computed keys are merged last so it can never overwrite one. Without that
    ordering a caller could replace `n` — the block's own inference base — with
    whatever it happened to name."""
    collapsed = {"u1": {"score": 1.0}, "u2": {"score": 3.0}}
    counts = {"resolved": 2, "completed": 2, "ineligible": 0, "failed": 0}
    out = summarize_step(
        collapsed,
        counts,
        beside_n={"technical_n": {"min": 2, "max": 3, "median": 3}, "n": "clobbered"},
    )
    assert out["score"]["n"] == counts
    assert out["score"]["technical_n"] == {"min": 2, "max": 3, "median": 3}


def test_a_fractional_effective_rides_counts_into_every_metrics_n():
    """`effective` JOINS `n`, so it travels in `counts` and needs no carrier of
    its own — and it must survive as the fractional number `runner.attrition`
    computed. `reference.md` § Weighted samples prints `effective: 191.4` beside
    a `completed` of 228: rounding it to an `int` would name a size no interval
    was computed at, which is why `counts` is `dict[str, float]`.

    Asserted on both metric shapes. The document's own example is `r`, which
    `aggregate` derives, and the derived branch builds its `n` from a separate
    literal — so a change made in only the recorded-column loop reads correctly
    for `pred` and drops `effective` for `r`."""
    collapsed = {"u1": {"score": 1.0}, "u2": {"score": 3.0}}
    counts = {"resolved": 3, "completed": 2, "ineligible": 1, "failed": 0, "effective": 1.6}
    out = summarize_step(collapsed, counts, derived={"total": 4.0})
    for name in ("score", "total"):
        assert out[name]["n"]["effective"] == pytest.approx(1.6)
        # Beside `completed`, not replacing it: weights change what each unit
        # contributes, not how many there were.
        assert out[name]["n"]["completed"] == 2
    # The control: `completed` is still recomputed per column rather than taken
    # from `counts`, so this is not passing off a verbatim copy of the mapping.
    ragged = summarize_step({"u1": {"score": 1.0}}, counts)
    assert ragged["score"]["n"] == {**counts, "completed": 1}


# --- H3b task 8: `n.clusters` in `summarize_step` ------------------------------
#
# The same collapsed table the weighted group uses, with a cluster per unit. The
# clusters are chosen so four different numbers are in play and each column can
# only report the right one:
#
#   pred's own carriers  u1, u2, u4 → clusters {a, c}    → 2   ← pred's answer
#   every collapsed unit u1..u4     → clusters {a, b, c} → 3   ← other's answer
#   the roster           u1..u5     → clusters {a,b,c,d} → 4
#   and the unit counts are 3 and 4, neither equal to its own cluster count.
_CLUSTERS = {"u1": "a", "u2": "a", "u3": "b", "u4": "c", "u5": "d"}


def test_clusters_is_recomputed_over_the_units_the_column_actually_has():
    """`reference.md` § Clustered units reports the cluster count "as the
    effective sample size alongside the unit count", and § Statistical reporting
    gives `t_over_units_clustered` "df = clusters − 1". A df is over the units the
    interval was computed from, so a ragged column's cluster count must be its
    own — printing the condition-wide figure beside it would name a df no interval
    used, which is the argument `summarize_step` already makes for `completed` and
    for `effective`.

    **`counts` carries a deliberately impossible 99** rather than the 3
    `runner.attrition` would really pass here. With the true value present,
    `other`'s recomputed count is *also* 3 and its assertion would pass against an
    implementation that merely inherits the key from `counts`, leaving `pred`
    alone to carry the test."""
    counts = dict(_WEIGHTED_COUNTS, clusters=99)
    out = summarize_step(_WEIGHTED_COLLAPSED, counts, clusters=_CLUSTERS)
    assert out["pred"]["n"]["completed"] == 3
    assert out["pred"]["n"]["clusters"] == 2
    assert out["other"]["n"]["completed"] == 4
    assert out["other"]["n"]["clusters"] == 3


def test_an_unclustered_summary_grows_no_clusters_key():
    """The regression, at the function: with no `clusters` mapping every `n` is
    exactly the parts `counts` carried, on both metric shapes. § The three-part
    `n` — "each present only when it applies so a design that never skips reads as
    it always did"."""
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, derived={"total": 4.0})
    for name in ("pred", "other", "total"):
        assert "clusters" not in out[name]["n"]
    # The control that must report: the call really did summarize both shapes.
    assert out["pred"]["value"] == pytest.approx(4 / 3)
    assert out["total"]["value"] == 4.0


def test_a_derived_metric_carries_the_condition_wide_cluster_count():
    """A derived metric's `n` comes from `counts`, exactly as `effective` does
    there: `aggregate` returned one number over the whole collapsed table, so
    there is no per-column carrier set to recompute over. `clusters` rides
    `counts` into the derived block and needs no carrier of its own."""
    collapsed = {"u1": {"score": 1.0}, "u2": {"score": 3.0}, "u3": {"score": 5.0}}
    counts = {"resolved": 4, "completed": 3, "ineligible": 1, "failed": 0, "clusters": 2}
    out = summarize_step(collapsed, counts, derived={"total": 3.0}, clusters=_CLUSTERS)
    assert out["total"]["n"]["clusters"] == 2
    assert out["total"]["n"]["completed"] == 3
    # The control: the recorded column beside it recomputes over its own carriers,
    # u1/u2/u3 → clusters {a, b}, which is also 2 — so this pins the derived key's
    # presence, and the ragged case above pins that the recompute is real.
    assert out["score"]["n"]["clusters"] == 2


# --- H3b task 11: the declared cluster decides the column's interval -----------
#
# Same roster and same ragged table as the two groups above, because the risk is
# the same one: a cluster vector filtered differently from the values groups the
# wrong unit. `pred` sits in 2 clusters and `other` in 3, and neither equals its
# own unit count, so a column reporting the other column's interval — or the
# whole roster's — is visible.


def test_a_recorded_columns_interval_becomes_cluster_robust_when_a_cluster_is_declared():
    """The wiring this slice exists for, at the function. § Clustered units calls
    the unclustered interval over clustered data "too narrow" and § Statistical
    reporting names the construction, so a `cluster_by` that only added
    `n.clusters` would be a declaration whose effect is not delivered — and one no
    check reading `n` alone could catch.

    Each column's interval is the construction over ITS OWN units: `pred`'s three
    carriers sit in 2 clusters, `other`'s four in 3. The rival — the same
    construction over every collapsed unit — is asserted to differ, so a mapping
    aligned to the table rather than to the column fails here.
    """
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, clusters=_CLUSTERS)
    own = t_over_units_clustered([0.0, 1.0, 3.0], ["u1", "u2", "u4"], _CLUSTERS)
    rival = t_over_units_clustered([1.0, 1.0, 2.0, 1.0], ["u1", "u2", "u3", "u4"], _CLUSTERS)
    assert own is not None and rival is not None
    assert out["pred"]["method"] == "t_over_units_clustered"
    assert out["pred"]["ci95"] == [own.low, own.high]
    assert out["pred"]["ci95"] != [rival.low, rival.high]
    # The value is untouched by clustering — clustering changes what the interval
    # is computed over, not what the estimate is.
    assert out["pred"]["value"] == pytest.approx(4 / 3)
    assert out["other"]["method"] == "t_over_units_clustered"
    assert out["other"]["ci95"] == [rival.low, rival.high]


def test_an_unclustered_column_keeps_the_interval_it_always_had():
    """The regression that guards every unclustered design, including the worked
    example: with no `clusters` mapping the method is `t_over_units` and the
    endpoints are the ones this function reported before clusters existed."""
    out = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS)
    plain = t_over_units([0.0, 1.0, 3.0])
    assert plain is not None
    assert out["pred"]["method"] == "t_over_units"
    assert out["pred"]["ci95"] == [plain.low, plain.high]


def test_a_weighted_clustered_column_takes_the_weighted_sandwich():
    """Both declared: § Weighted samples has the cluster decide the draw and the
    weight decide what the estimate represents, so the column gets
    `weighted_t_over_units_clustered` over its own units, its own weights and its
    own clusters — all three filtered in the same pass.

    `n.effective` survives beside it, which is the part a four-way branch drops:
    Kish's size is a fact about the weighting rather than about the construction,
    and § Weighted samples has `effective` and `clusters` both join `n`.
    """
    out = summarize_step(
        _WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights=_WEIGHTS, clusters=_CLUSTERS
    )
    expected = weighted_t_over_units_clustered(
        [0.0, 1.0, 3.0], ["u1", "u2", "u4"], _CLUSTERS, [1.0, 1.0, 3.0]
    )
    assert expected is not None
    assert out["pred"]["method"] == "weighted_t_over_units_clustered"
    assert out["pred"]["ci95"] == [expected.low, expected.high]
    assert out["pred"]["value"] == pytest.approx(2.0)
    assert out["pred"]["n"]["effective"] == pytest.approx(kish_effective_n([1.0, 1.0, 3.0]))
    assert out["pred"]["n"]["clusters"] == 2
    # The two controls that must report, and must differ: dropping either
    # declaration gives a different interval, so neither is being ignored.
    unweighted = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, clusters=_CLUSTERS)
    unclustered = summarize_step(_WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights=_WEIGHTS)
    assert out["pred"]["ci95"] != unweighted["pred"]["ci95"]
    assert out["pred"]["ci95"] != unclustered["pred"]["ci95"]
    assert unclustered["pred"]["method"] == "weighted_t_over_units"


def test_a_single_cluster_column_reports_its_point_with_no_interval():
    """The honest floor, reached through the wiring: a column whose units all sit
    in one cluster has one draw and no df, so `ci95` and `method` are `null` while
    `value` and `n` are still reported. It reads as a bug to anyone expecting an
    interval, and it is the correct answer — 300 cells from one animal are one
    observation."""
    collapsed = {"u1": {"score": 1.0}, "u2": {"score": 3.0}, "u3": {"score": 5.0}}
    counts = {"resolved": 3, "completed": 3, "ineligible": 0, "failed": 0}
    out = summarize_step(collapsed, counts, clusters=dict.fromkeys(collapsed, "one"))
    assert out["score"]["ci95"] is None
    assert out["score"]["method"] is None
    assert out["score"]["value"] == pytest.approx(3.0)
    assert out["score"]["n"]["clusters"] == 1
    # The control that must report: the same table over two clusters has an
    # interval, so the `None` above is the cluster count and not the shape.
    two = summarize_step(collapsed, counts, clusters={"u1": "a", "u2": "a", "u3": "b"})
    assert two["score"]["ci95"] is not None


def _banded_strata() -> tuple[list[float], list[str]]:
    """Three strata, unequal sizes, disjoint value bands. Sized so that the
    three candidate constructions produce three DIFFERENT numbers:

      correct stratified mean  (20·0.5 + 8·10.5 + 2·100.5) / 30  ≈  9.83
      unstratified             same centre, several times wider
      mean of stratum means    (0.5 + 10.5 + 100.5) / 3          ≈ 37.17

    Two equal strata distinguish none of them, which is the fixture-sizing rule
    this repo wrote into CLAUDE.md after an apportionment test matched a
    reverse-order mutant by coincidence."""
    values = (
        [i / 20.0 for i in range(20)]
        + [10.0 + i / 8.0 for i in range(8)]
        + [100.0 + i / 2.0 for i in range(2)]
    )
    strata = ["low"] * 20 + ["mid"] * 8 + ["high"] * 2
    return values, strata


def test_a_stratified_draw_preserves_each_stratum_size():
    """§ Weighted samples: resampling within each stratum "so a bootstrap can't
    return a replicate whose stratum composition the design ruled out". The
    two-value stratum contributes exactly 2 rows to every draw, which pins the
    interval near 9.83 and makes it much narrower than the unstratified one."""
    values, strata = _banded_strata()
    stratified = percentile_over_units(values, seed=7, draws=2000, strata=strata).interval
    plain = percentile_over_units(values, seed=7, draws=2000).interval
    assert stratified is not None and plain is not None
    expected = sum(values) / len(values)  # 9.83…
    assert stratified.low < expected < stratified.high
    stratified_width = stratified.high - stratified.low
    plain_width = plain.high - plain.low
    # Narrower, and by a lot: the whole point of the declaration is that the
    # 2-unit stratum's contribution stops varying.
    assert stratified_width < plain_width / 2.0
    # And NOT the mean-of-stratum-means answer, which is 37.17 — a construction
    # that gave each stratum equal say would put the interval there instead.
    assert stratified.high < 20.0


def test_a_stratified_draw_is_invariant_to_row_order():
    """A fixed seed draws a fixed sequence of indices, so the multiset of
    (value, stratum) pairs must be all that matters — the same invariance the
    unstratified branch gets from sorting its pool, and the same one
    `percentile_over_units_clustered` gets from ordering its pools by contents."""
    values, strata = _banded_strata()
    pairs = list(zip(values, strata, strict=True))
    # Rotate by 28, not 7: a rotation by 7 leaves the first-seen stratum order
    # (low, mid, high) unchanged, so it cannot tell "ordered by sorted
    # contents" apart from "ordered by first appearance" — a mutation to
    # insertion-order pooling would still pass. Rotating by 28 changes which
    # stratum is seen first.
    shuffled = pairs[28:] + pairs[:28]
    a = percentile_over_units(values, seed=11, draws=2000, strata=strata)
    b = percentile_over_units(
        [v for v, _ in shuffled], seed=11, draws=2000, strata=[s for _, s in shuffled]
    )
    assert a == b


def test_a_stratified_draw_is_invariant_to_stratum_labels():
    """Strata ordered by their own sorted contents, not by label — so renaming
    `low`/`mid`/`high` to `z`/`a`/`m` gives the identical interval."""
    values, strata = _banded_strata()
    renamed = {"low": "z", "mid": "a", "high": "m"}
    a = percentile_over_units(values, seed=3, draws=2000, strata=strata)
    b = percentile_over_units(values, seed=3, draws=2000, strata=[renamed[s] for s in strata])
    assert a == b


def test_one_stratum_reproduces_the_unstratified_interval_digit_for_digit():
    """The degenerate case is not a special case: with every unit in one
    stratum, the stratified path draws n indices from one sorted pool, which is
    exactly what the unstratified path does."""
    values, _ = _banded_strata()
    a = percentile_over_units(values, seed=5, draws=2000)
    b = percentile_over_units(values, seed=5, draws=2000, strata=["only"] * len(values))
    assert a == b


def test_a_stratified_weighted_draw_keeps_each_value_with_its_weight():
    """Weights travel with values through the grouping AND the sort. Sorting the
    two sequences separately would preserve every invariance above and silently
    re-pair them — a mistake equal weights cannot see, which is why the weights
    here are as banded as the values."""
    values, strata = _banded_strata()
    weights = [1.0] * 20 + [5.0] * 8 + [50.0] * 2
    got = percentile_over_units(values, seed=9, draws=2000, weights=weights, strata=strata).interval
    assert got is not None
    expected = sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)
    assert got.low < expected < got.high
    # The weighted centre (≈ 65.325) is far from the unweighted one (≈ 9.83), so
    # a re-pairing or a dropped weight lands outside this interval rather than
    # inside it.
    assert got.low > 50.0


def test_a_stratified_draw_refuses_a_misaligned_stratum_vector():
    """A length mismatch is a misaligned vector, and would produce a plausible
    number rather than an error — the same reason `strict=True` guards the
    clustered zip."""
    values, strata = _banded_strata()
    with pytest.raises(ValueError):
        percentile_over_units(values, seed=1, draws=2000, strata=strata[:-1])


def test_a_size_one_stratum_is_drawn_deterministically_every_time():
    """A singleton stratum has exactly one candidate index on every draw, so it
    contributes its one value to every replicate with no variance of its own —
    it neither breaks the draw nor gets skipped, and removing the last bit of
    freedom the "high" band had (as a 2-row stratum) only narrows things
    further relative to the pooled draw."""
    values, strata = _banded_strata()
    # The two-value "high" stratum becomes two singleton strata.
    strata = strata[:-2] + ["high_a", "high_b"]
    got = percentile_over_units(values, seed=13, draws=2000, strata=strata).interval
    plain = percentile_over_units(values, seed=13, draws=2000).interval
    assert got is not None and plain is not None
    expected = sum(values) / len(values)
    assert got.low < expected < got.high
    # A pooled-path substitution would give the wide, undifferentiated draw —
    # this must stay much narrower, the same margin the base stratified test
    # uses, so a pooled swap here fails too.
    assert (got.high - got.low) < (plain.high - plain.low) / 2.0


def test_a_stratum_of_identical_values_contributes_no_variance_of_its_own():
    """A stratum whose values are all identical draws different indices but the
    same number every time — it cannot widen the interval, only the varying
    strata can, and the result must still be the narrow stratified interval,
    not the pooled one."""
    values, strata = _banded_strata()
    # Replace the "mid" band (indices 20:28) with a single repeated value.
    values = list(values)
    for i in range(20, 28):
        values[i] = 50.0
    got = percentile_over_units(values, seed=17, draws=2000, strata=strata).interval
    plain = percentile_over_units(values, seed=17, draws=2000).interval
    assert got is not None and plain is not None
    expected = sum(values) / len(values)
    assert got.low < expected < got.high
    assert (got.high - got.low) < (plain.high - plain.low) / 2.0


def test_all_strata_internally_constant_gives_no_interval_at_all():
    """Two strata (sizes 10 and 4), each internally constant. This is the
    structural case, not the data-caused one a single constant stratum among
    varying ones settles for: with EVERY stratum's rows all carrying one
    repeated (value, weight) pair, no draw can ever differ from any other,
    for whatever constants those strata hold — so this must never be pinned as
    a zero-width `ci95`, the same principle
    `percentile_over_units_clustered` applies at `G < 2`
    ("reporting a point with no interval is honest; a zero-width 95 %
    interval is not.")."""
    values = [1.0] * 10 + [5.0] * 4
    strata = ["a"] * 10 + ["b"] * 4
    assert percentile_over_units(values, seed=23, draws=2000, strata=strata).interval is None


def test_every_unit_its_own_stratum_gives_no_interval_at_all():
    """Every unit its own singleton stratum: each draw reproduces every value
    exactly once, so the resample has no freedom left anywhere. This is the
    singleton special case of the constant-stratum refusal above, not a
    zero-width point to report."""
    values = [1.0, 2.0, 3.0, 4.0]
    strata = ["a", "b", "c", "d"]
    got = percentile_over_units(values, seed=19, draws=2000, strata=strata).interval
    assert got is None


@pytest.mark.parametrize("bad", [0, 0.0, -1.0, float("nan"), float("inf"), "heavy", None, True])
def test_a_column_resample_refuses_a_bad_weight_before_any_draw(bad):
    """The invariant decision 2 rests on: a column metric's draw statistic is a
    mean over a non-empty sample, so it is ALWAYS defined and
    `resample_draws == n` always. What could break that is a weight of zero
    making Σw zero on some draw — so the check is that `checked_weights`
    (reading `units.usable_weight`, which requires a finite positive number)
    refuses every such weight before a single draw is taken."""
    values = [1.0, 2.0, 3.0, 4.0]
    weights = [1.0, 1.0, 1.0, bad]
    with pytest.raises(ContractError) as exc:
        percentile_over_units(values, seed=1, draws=100, weights=weights)
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_a_column_resample_is_never_degenerate_across_adversarial_columns_of_finite_values():
    """The positive half, and the one that would catch a `(Interval, int)`
    requirement appearing: over columns chosen to be as degenerate as a
    FINITE column can be — zero variance, a single repeated value, extreme
    weight spread, a one-unit stratum — the interval is always produced, so
    no survivor count ever differs from the requested draws. This is
    conditional on finiteness: it says nothing about `nan`/`inf` values or an
    overflowing weight sum, which are a separate, real gap pinned (not fixed)
    by the tests below and recorded in `docs/superpowers/spec-defects.md`."""
    cases: list[tuple[list[float], dict]] = [
        ([5.0, 5.0, 5.0, 5.0], {}),  # zero variance
        ([0.0, 0.0, 0.0, 1e-12], {}),  # near-zero spread
        ([1.0, 2.0, 3.0, 4.0], {"weights": [1e-9, 1e-9, 1e-9, 1e9]}),  # extreme spread
        ([1.0, 2.0, 3.0], {"strata": ["a", "b", "b"]}),  # one-unit stratum
        ([1.0, 2.0, 3.0, 4.0], {"strata": ["a", "a", "b", "b"], "weights": [1.0, 2.0, 3.0, 4.0]}),
    ]
    for values, kwargs in cases:
        resampled = percentile_over_units(values, seed=2, draws=100, **kwargs)
        assert resampled.draws_used == 100, (values, kwargs)
        got = resampled.interval
        assert got is not None, (values, kwargs)
        assert got.method == "percentile_over_units"
        assert got.low <= got.high


def test_a_column_resample_refuses_the_constant_one_stratum_case_the_unstratified_path_does_not():
    """The docstring's "one-stratum case reproduces the unstratified path digit
    for digit" claim has an exception: when every value is identical, the
    stratified path refuses (`None`, task 9/10's constant-pair check) while the
    unstratified path over the same values returns a zero-width `Interval`
    rather than refusing. The two paths apply different refusal criteria to the
    same degenerate input and so diverge here — not a contradiction of the
    docstring's claim, but a real, pinned exception to it."""
    values = [5.0, 5.0, 5.0, 5.0]
    unstratified = percentile_over_units(values, seed=5, draws=2000)
    stratified = percentile_over_units(values, seed=5, draws=2000, strata=["only"] * 4)
    assert unstratified.interval == Interval(low=5.0, high=5.0, method="percentile_over_units")
    assert stratified.interval is None


def test_a_column_resample_over_non_finite_values_is_a_known_unfixed_gap():
    """NOT a pin of correct behavior — a pin of a known, unfixed defect, so a
    future reader who "fixes" this by making the assertion pass differently
    knows to update `docs/superpowers/spec-defects.md` too. `values` is never
    checked for finiteness on this path, so a `nan` among them silently reaches
    `Interval(nan, nan)`: decision 2's "always defined" invariant holds only
    given finite inputs, and this is the reachable counterexample without that
    condition. `low <= high` is `False` for `nan`, which is exactly what the
    adversarial test above would have caught immediately had it varied value
    DOMAIN rather than only column shape.

    This resample (column-bootstrap) half of the filing stays open at H4d
    task 23, which claimed only the sibling permutation half
    (`stats._label_delta`, over in
    `test_a_permutation_over_units_with_a_nan_value_reports_no_p_value_rather_than_a_false_one`)
    — H4d is the last slice whose surface is the `statistics` block, so this
    gap now has no owner to inherit it."""
    got = percentile_over_units([1.0, 2.0, 3.0, float("nan")], seed=1, draws=100).interval
    assert got is not None
    assert math.isnan(got.low) and math.isnan(got.high)


def test_a_column_resample_with_an_overflowing_weight_sum_is_a_known_unfixed_gap():
    """NOT a pin of correct behavior — a pin of a known, unfixed defect. Every
    weight here individually passes `checked_weights` (each is finite and
    positive), so decision 2's premise ("Σw is strictly positive") is satisfied
    letter for letter — but Σw over these four weights overflows `float`, and
    the resulting weighted mean is `nan`. Finite-and-positive per weight is not
    the same fact as finite-when-summed, and the docstring's argument silently
    assumed the latter followed from the former.

    Also still open at H4d task 23, for the reason the sibling test above
    gives — the permutation half of this finiteness surface closed; this
    resample half did not."""
    got = percentile_over_units(
        [1.0, 2.0, 3.0, 4.0], seed=1, draws=100, weights=[1e308, 1e308, 1e308, 1e308]
    ).interval
    assert got is not None
    assert math.isnan(got.low) and math.isnan(got.high)


def test_percentile_over_units_now_returns_a_pairedresample():
    """Superseded decision, recorded rather than silently dropped: this used to
    pin that the return stayed a bare `Interval` because `percentile_of_derived`
    alone needed a survivor count to carry. `correction.Member` needs the pool
    a *column* metric's percentile interval was read off too — a condition's own
    metric can be the target of a `compare: {to: constant}` hypothesis, and its
    corrected bound has to be rebuilt from the same draws, not a re-drawn
    approximation of them — so this now returns `PairedResample` like its three
    siblings. `draws_used` is not the same fact here it is for a derived metric,
    though: this path never filters a draw (decision 2, unchanged), so
    `draws_used` is always the REQUESTED `n`, pinned separately by
    `test_a_column_resample_is_never_degenerate_across_adversarial_columns_of_finite_values`
    above, not a survivor count."""
    got = percentile_over_units([1.0, 2.0, 3.0, 4.0], seed=1, draws=100)
    assert isinstance(got, PairedResample)
    assert isinstance(got.interval, Interval)


def test_percentile_over_units_carries_the_pool_it_read_its_interval_from():
    """The same pin `percentile_of_derived`'s own pool test makes, one
    construction over: reading the same ranks back off the returned pool with
    `interval_at` must reproduce the interval exactly — satisfied only by the
    ACTUAL pool `interval` was read off, not by a re-drawn or re-sorted
    stand-in that merely looks like one (non-empty, sorted, right length)."""
    values = [float(i) for i in range(60)]
    got = percentile_over_units(values, seed=7, draws=500)
    assert got.interval is not None
    assert len(got.pool) == got.draws_used == 500
    assert got.pool == sorted(got.pool)
    assert interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)


def test_percentile_over_units_clustered_carries_the_pool_it_read_its_interval_from():
    """The clustered sibling's own version of the same pin: the pool
    `percentile_over_units_clustered` returns must be the sequence of drawn
    cluster-pool means `interval_at` actually indexed, not an equivalent-
    looking stand-in."""
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, draws=500
    )
    assert got.interval is not None
    assert len(got.pool) == got.draws_used == 500
    assert got.pool == sorted(got.pool)
    assert interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)


def _ragged_collapsed(n: int = 40) -> dict[str, dict[str, float]]:
    return {f"u{i}": {"pred": float(i)} for i in range(n)}


def test_a_recorded_column_takes_a_percentile_interval_under_resample():
    """§ Statistical reporting: a column metric has a t-interval available, so
    resampling it is a CHOICE and `resample` is what makes it. The value is
    unchanged — the draw changes the interval, not the estimate."""
    collapsed = _ragged_collapsed()
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000)
    drawn = summarize_step(collapsed, counts, seed=5, draws=2000, resample_columns=True)
    assert plain["pred"]["method"] == "t_over_units"
    assert "resample_draws" not in plain["pred"]
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["resample_draws"] == 2000
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["ci95"] is not None
    low, high = drawn["pred"]["ci95"]
    assert low < drawn["pred"]["value"] < high


def test_a_clustered_column_takes_the_clustered_percentile_under_resample():
    """`cluster_by` decides the draw when both are declared, so the construction
    is the `_clustered` one and `n.clusters` still reports the cluster count."""
    collapsed = _ragged_collapsed(40)
    clusters = {f"u{i}": f"c{i % 8}" for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, clusters=clusters, resample_columns=True
    )
    assert drawn["pred"]["method"] == "percentile_over_units_clustered"
    assert drawn["pred"]["n"]["clusters"] == 8
    assert drawn["pred"]["resample_draws"] == 2000


def test_a_clustered_and_weighted_column_pins_both_together_under_resample():
    """The fourth of the four required combinations, and the one a bracketing
    assertion cannot discriminate (§ Three things this task's brief itself
    names): a weighted mean stays close to the unweighted one on many
    fixtures, so `low < value < high` alone would still pass with `weights`
    silently dropped from the clustered draw. Pinned instead with an EXACT
    `ci95` match against calling `percentile_over_units_clustered` directly
    with the same weight vector — the same discriminating standard
    `test_a_weighted_column_keeps_its_weighted_value_and_kish_size_under_resample`
    uses for the unclustered case."""
    collapsed = _ragged_collapsed(40)
    clusters = {f"u{i}": f"c{i % 8}" for i in range(40)}
    weights = {f"u{i}": 1.0 + (i % 4) for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    drawn = summarize_step(
        collapsed,
        counts,
        seed=5,
        draws=2000,
        clusters=clusters,
        weights=weights,
        resample_columns=True,
    )
    assert drawn["pred"]["method"] == "percentile_over_units_clustered"
    assert drawn["pred"]["n"]["clusters"] == 8
    values = [float(i) for i in range(40)]
    keys = [f"u{i}" for i in range(40)]
    column_weights = [weights[k] for k in keys]
    expected = percentile_over_units_clustered(
        values, keys, clusters, seed=5, draws=2000, weights=column_weights
    ).interval
    assert expected is not None
    assert drawn["pred"]["ci95"] == [expected.low, expected.high]


def test_a_weighted_column_keeps_its_weighted_value_and_kish_size_under_resample():
    """Three things move together or the declaration is half-delivered: the
    value stays the WEIGHTED mean, `n.effective` stays Kish's size, and only the
    interval becomes a percentile. § Weighted samples puts the weights "in the
    estimate rather than in the drawing"."""
    collapsed = _ragged_collapsed(40)
    weights = {f"u{i}": 1.0 + (i % 4) for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000, weights=weights)
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, weights=weights, resample_columns=True
    )
    assert plain["pred"]["method"] == "weighted_t_over_units"
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["n"]["effective"] == plain["pred"]["n"]["effective"]
    # The weighted centre differs from the unweighted one on this fixture, but
    # that alone doesn't discriminate a dropped `weights=` in the DRAW: both
    # intervals are wide enough on 40 units to bracket either centre. The
    # assertion that actually catches a dropped `weights=` in the percentile
    # construction is the exact `ci95` match against calling
    # `percentile_over_units` directly with the same weight vector — a
    # construction the interval must reproduce digit for digit, the same
    # standard `test_percentile_over_units_...` pins elsewhere in this file.
    column_weights = [weights[f"u{i}"] for i in range(40)]
    values = [float(i) for i in range(40)]
    expected = percentile_over_units(values, seed=5, draws=2000, weights=column_weights).interval
    assert expected is not None
    assert drawn["pred"]["ci95"] == [expected.low, expected.high]
    unweighted = summarize_step(collapsed, counts, seed=5, draws=2000)
    assert drawn["pred"]["value"] != unweighted["pred"]["value"]


def test_a_column_below_two_units_reports_a_null_draw_count_under_resample():
    """`percentile_over_units` returns `None` below two units exactly as
    `t_over_units` does, so the degenerate case does not change shape. Unlike
    the brief's first draft of this test, `resample_draws` is NOT the requested
    `n` here: `docs/superpowers/spec-defects.md`'s ruling is that a column's
    draw count is `null` whenever `ci95` is `null` — there is no interval for a
    draw count to describe, and recording the requested `n` beside a refused
    interval would assert survivor evidence for a draw that never produced
    one. It is still PRESENT (not absent) — a resample was declared and
    attempted, it just came back with nothing, which is a different fact from
    `resample_columns=False`'s "never asked" and must not collapse onto it."""
    counts = {"resolved": 1, "completed": 1, "failed": 0}
    got = summarize_step({"u0": {"pred": 1.0}}, counts, seed=5, draws=2000, resample_columns=True)
    assert got["pred"]["ci95"] is None
    assert got["pred"]["method"] is None
    assert "resample_draws" in got["pred"]
    assert got["pred"]["resample_draws"] is None


def test_a_column_below_the_honest_draw_floor_also_reports_a_null_draw_count():
    """A second, DISTINCT reason `percentile_over_units` returns `None`: not too
    few units (40 here, plenty), but too few DRAWS for either percentile rank
    to be interior (`min_honest_draws()` is 80 at the default confidence, and
    `draws=10` is below it).
    `test_a_column_below_two_units_reports_a_null_draw_count_under_resample` and
    this one exercise two of the three ways a column's interval can come back
    refused; the third (the per-stratum constant-pair refusal) needs a declared
    `strata` to reach at all, which neither fixture here carries."""
    collapsed = _ragged_collapsed(40)
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    got = summarize_step(collapsed, counts, seed=5, draws=10, resample_columns=True)
    assert got["pred"]["ci95"] is None
    assert got["pred"]["method"] is None
    assert "resample_draws" in got["pred"]
    assert got["pred"]["resample_draws"] is None


def test_summarize_step_draws_within_the_strata_it_is_given():
    """The stratified column interval, end of the thread. The fixture is the
    banded one: 20 units in [0,1), 8 in [10,11), 2 in [100,101), so the
    stratified interval is far narrower than the unstratified one and nowhere
    near the mean-of-stratum-means answer."""
    values = (
        [i / 20.0 for i in range(20)]
        + [10.0 + i / 8.0 for i in range(8)]
        + [100.0 + i / 2.0 for i in range(2)]
    )
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": ("low" if i < 20 else "mid" if i < 28 else "high") for i in range(30)}
    counts = {"resolved": 30, "completed": 30, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=7, draws=2000, resample_columns=True)
    drawn = summarize_step(
        collapsed, counts, seed=7, draws=2000, resample_columns=True, strata=strata
    )
    plain_low, plain_high = plain["pred"]["ci95"]
    low, high = drawn["pred"]["ci95"]
    assert (high - low) < (plain_high - plain_low) / 2.0
    assert low < drawn["pred"]["value"] < high
    assert high < 20.0  # not the 37.17 of equal-weighted stratum means


def test_the_stratum_vector_is_aligned_to_the_columns_own_keys():
    """A RAGGED column: only some units carry `late`, and its stratum vector
    must be the subset those units carry, not the whole table's. A vector
    filtered differently draws the wrong composition and produces a plausible
    number rather than an error — the same reason `weights` and `clusters` are
    both looked up per column key."""
    collapsed: dict[str, dict[str, float]] = {}
    for i in range(30):
        row: dict[str, float] = {"early": float(i)}
        if i >= 20:  # only the `high`/`mid` tail carries `late`
            row["late"] = 100.0 + float(i)
        collapsed[f"u{i}"] = row
    strata = {f"u{i}": ("low" if i < 20 else "mid" if i < 28 else "high") for i in range(30)}
    counts = {"resolved": 30, "completed": 30, "failed": 0}
    got = summarize_step(
        collapsed, counts, seed=7, draws=2000, resample_columns=True, strata=strata
    )
    # The ragged column's own `n.completed` is 10, and its interval exists —
    # a whole-table stratum vector would zip against 30 labels and raise.
    assert got["late"]["n"]["completed"] == 10
    assert got["late"]["ci95"] is not None
    assert got["late"]["method"] == "percentile_over_units"
    # The full column is unaffected, so this cannot pass by both being broken.
    assert got["early"]["n"]["completed"] == 30
    assert got["early"]["ci95"] is not None


def test_percentile_of_derived_draws_within_the_strata_it_is_given():
    """The derived half of the amendment: `percentile_of_derived` recomputes
    `aggregate` (here, `sum(units.pred)`) on each draw, so stratifying it means
    drawing unit KEYS within each stratum rather than values — the banded
    fixture makes the stratified interval measurably narrower than the plain
    one, and nowhere near the mean-of-stratum-means answer, the same three-way
    separation `percentile_over_units`'s own stratified tests use."""
    values, strata_list = _banded_strata()
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": s for i, s in enumerate(strata_list)}

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    plain_resampled = percentile_of_derived(collapsed, compute, seed=7, draws=2000)
    drawn_resampled = percentile_of_derived(collapsed, compute, seed=7, draws=2000, strata=strata)
    plain, plain_n = plain_resampled.interval, plain_resampled.draws_used
    drawn, drawn_n = drawn_resampled.interval, drawn_resampled.draws_used
    assert plain is not None and drawn is not None
    assert plain_n == 2000 and drawn_n == 2000
    plain_width = plain.high - plain.low
    drawn_width = drawn.high - drawn.low
    assert drawn_width < plain_width / 2.0
    total = sum(values)
    assert drawn.low < total < drawn.high
    # Mean-of-stratum-means scaled up by 30 units would be nowhere close;
    # the correct stratified sum sits near `total` (294.9), not there.
    assert drawn.high < 700.0


def test_percentile_of_derived_stratum_vector_is_indexed_not_defaulted():
    """A key `collapsed` holds but `strata` does not is a core defect — the
    caller built `strata` from the same roster `collapsed` was collapsed
    from, so a missing entry means the two disagree about which units exist,
    and inventing a stratum for it would draw a plausible-looking interval
    over the wrong design instead of failing loudly."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    strata = {f"u{i}": "only" for i in range(19)}  # u19 missing on purpose

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    with pytest.raises(KeyError):
        percentile_of_derived(collapsed, compute, seed=7, draws=50, strata=strata)


def test_summarize_step_stratifies_a_column_and_a_derived_metric_together():
    """The amendment's own requirement: one declared `strata` mapping must move
    BOTH a recorded column's interval and a derived metric's interval in the
    same call, not just one of them — the asymmetry a single `stratify_by`
    producing a stratified column beside an unstratified derived metric would
    otherwise leave invisible in the record. Both are computed from the same
    banded fixture (`pred` recorded per unit, `total` derived as its sum), and
    both must come back narrower than their unstratified counterparts."""
    values, strata_list = _banded_strata()
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": s for i, s in enumerate(strata_list)}
    counts = {"resolved": 30, "completed": 30, "failed": 0}

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    plain = summarize_step(
        collapsed,
        counts,
        derived={"total": sum(values)},
        seed=7,
        resample={"total": compute},
        draws=2000,
        resample_columns=True,
    )
    drawn = summarize_step(
        collapsed,
        counts,
        derived={"total": sum(values)},
        seed=7,
        resample={"total": compute},
        draws=2000,
        resample_columns=True,
        strata=strata,
    )
    plain_col_low, plain_col_high = plain["pred"]["ci95"]
    col_low, col_high = drawn["pred"]["ci95"]
    assert (col_high - col_low) < (plain_col_high - plain_col_low) / 2.0

    plain_der_low, plain_der_high = plain["total"]["ci95"]
    der_low, der_high = drawn["total"]["ci95"]
    assert (der_high - der_low) < (plain_der_high - plain_der_low) / 2.0
    # Neither happened to move by being byte-identical to the other's width —
    # each was checked against its OWN unstratified counterpart above.
    assert drawn["pred"]["ci95"] != plain["pred"]["ci95"]
    assert drawn["total"]["ci95"] != plain["total"]["ci95"]


def test_percentile_of_derived_refuses_the_singleton_stratum_case():
    """A near-unique `stratify_by` — one stratum per unit — validates clean and
    is exactly the fault this refusal exists for: every draw of a singleton
    stratum picks the identical one key every time, so `compute` (deterministic
    here, as every `aggregate` this module is handed must be) returns the
    identical value on every draw and the interval would be zero-width — the
    same "a zero-width 95% interval is not honest" refusal
    `percentile_over_units`'s own strata branch and
    `percentile_over_units_clustered`'s `G < 2` floor already give for their
    own constructions. Before this fix, this returned `(Interval(x, x), 2000)`
    instead — a plausible-looking interval a reader could not tell from a real
    one, sitting right beside a recorded column's `ci95: null` on the identical
    design."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    strata = {f"u{i}": f"u{i}" for i in range(20)}  # one stratum per unit

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    resampled = percentile_of_derived(collapsed, compute, seed=7, draws=2000, strata=strata)
    assert resampled.interval is None
    assert resampled.draws_used == 0


def test_percentile_of_derived_refuses_a_multi_key_stratum_of_identical_rows_too():
    """Not just singletons: a 4-key stratum whose members all carry the
    IDENTICAL recorded row is the same zero-freedom fact, whatever its size —
    content-based, not count-based, mirroring
    `percentile_over_units_clustered`'s own "content, not count" ruling for
    clusters. Every key in stratum `const` carries `{"pred": 1.0}`."""
    collapsed = {f"u{i}": {"pred": 1.0} for i in range(4)}
    strata = {f"u{i}": "const" for i in range(4)}

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    resampled = percentile_of_derived(collapsed, compute, seed=7, draws=2000, strata=strata)
    assert resampled.interval is None
    assert resampled.draws_used == 0


def test_percentile_of_derived_does_not_over_refuse_one_constant_stratum_among_others():
    """A single degenerate stratum among others that vary keeps its interval —
    the `all(...)` gate, not `any(...)`: the varying strata still supply real
    sampling variance, and refusing the whole draw because one of several
    strata is constant would sink an otherwise-informative resample. Mirrors
    `percentile_over_units`'s own "a single constant stratum among others still
    varies" case for the column path."""
    values, strata_list = _banded_strata()
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    # Collapse the two-unit "high" stratum to an identical row each — constant
    # on its own — while "low" and "mid" keep their own genuine variation.
    collapsed["u28"]["pred"] = collapsed["u29"]["pred"] = 50.0
    strata = {f"u{i}": s for i, s in enumerate(strata_list)}

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    resampled = percentile_of_derived(collapsed, compute, seed=7, draws=2000, strata=strata)
    assert resampled.interval is not None
    assert resampled.draws_used == 2000


def test_summarize_step_threads_strata_into_the_clustered_column_call():
    """Finding 2 of the task-15 review: the clustered × stratified construction
    was covered at `percentile_over_units_clustered` function level, but
    nothing pinned that `summarize_step` actually passes `strata` at ITS
    clustered call site — replacing `strata=column_strata` with `strata=None`
    there left the whole suite green. This is that end-to-end pin.

    The banded fixture, paired into two-unit clusters so each cluster is
    homogeneous (a stratum must be constant within a cluster): 10 `low`
    clusters, 4 `mid` clusters, 1 `high` cluster, 15 in total. Stratified, the
    draw preserves each stratum's own cluster count; unstratified, all 15 pool
    together and the two large `high` values (each its own two-unit cluster)
    dominate far more of the resampled mean's variance."""
    values, band = _banded_strata()
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": s for i, s in enumerate(band)}
    clusters: dict[str, str] = {}
    for i in range(20):
        clusters[f"u{i}"] = f"c{i // 2}"  # c0..c9, 10 low clusters
    for i in range(20, 28):
        clusters[f"u{i}"] = f"c{10 + (i - 20) // 2}"  # c10..c13, 4 mid clusters
    for i in range(28, 30):
        clusters[f"u{i}"] = "c14"  # 1 high cluster
    counts = {"resolved": 30, "completed": 30, "failed": 0}
    plain = summarize_step(
        collapsed, counts, seed=7, draws=2000, resample_columns=True, clusters=clusters
    )
    drawn = summarize_step(
        collapsed,
        counts,
        seed=7,
        draws=2000,
        resample_columns=True,
        clusters=clusters,
        strata=strata,
    )
    assert plain["pred"]["method"] == "percentile_over_units_clustered"
    plain_low, plain_high = plain["pred"]["ci95"]
    drawn_low, drawn_high = drawn["pred"]["ci95"]
    assert drawn["pred"]["method"] == "percentile_over_units_clustered"
    assert (drawn_high - drawn_low) < (plain_high - plain_low)
    assert drawn["pred"]["ci95"] != plain["pred"]["ci95"]


def test_percentile_of_derived_is_invariant_to_stratum_labels():
    """The derived path's own version of
    `test_a_stratified_draw_is_invariant_to_stratum_labels`: pools are ordered
    by their own sorted CONTENTS, not by label, so renaming `low`/`mid`/`high`
    to `z`/`a`/`m` must draw the identical sequence of tables and so return the
    identical interval and survivor count."""
    values, band = _banded_strata()
    collapsed = {f"u{i}": {"pred": v} for i, v in enumerate(values)}
    strata = {f"u{i}": s for i, s in enumerate(band)}
    renamed = {"low": "z", "mid": "a", "high": "m"}
    strata_renamed = {key: renamed[s] for key, s in strata.items()}

    def compute(units: UnitTable) -> float:
        return sum(units.pred)

    a = percentile_of_derived(collapsed, compute, seed=3, draws=2000, strata=strata)
    b = percentile_of_derived(collapsed, compute, seed=3, draws=2000, strata=strata_renamed)
    assert a == b


_PAIRED_OF = {
    "u0": {"m": 1.0},
    "u1": {"m": 2.0},
    "u2": {"m": 3.0},
    "u3": {"m": 9.0},
    "u4": {"m": 10.0},
    "u5": {"m": 11.0},
}
_PAIRED_AGAINST = {k: {"m": 0.0} for k in _PAIRED_OF}
_PAIRED_KEYS = ["u0", "u1", "u2", "u3", "u4", "u5"]
_PAIRED_STRATA = {"u0": "A", "u1": "A", "u2": "A", "u3": "B", "u4": "B", "u5": "B"}


def _mean_of_m(table):
    column = table.m
    return float(sum(column) / len(column))


def test_a_stratified_paired_draw_preserves_each_stratums_key_count():
    """`reference.md` § Weighted samples: `resample.stratify_by` says what an
    independent draw is, "resampling within each stratum so a bootstrap can't
    return a replicate whose stratum composition the design ruled out".

    The assertion is a FORCED BOUND, not an observation. A stratified draw is
    always three `A` keys and three `B` keys, so the smallest mean it can produce
    is three copies of `u0` (1.0) and three of `u3` (9.0) — exactly 5.0. An
    unstratified draw can go to 4.33 with five `A` keys and one `B`, and does at
    this seed and draw count. Neither the RNG nor the draw count can move the
    bound, which is what makes this test discriminating rather than lucky."""
    from publishable.stats import paired_percentile_of_derived

    stratified = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_AGAINST,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
        strata=_PAIRED_STRATA,
    )
    plain = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_AGAINST,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
    )
    assert min(stratified.pool) >= 5.0 - 1e-9
    # The control that must report: the same seed and draw count without strata
    # reaches below the forced floor, so the bound above is the stratification and
    # not a pool that happens to start high.
    assert min(plain.pool) < 5.0
    assert stratified.draws_used == 200
    assert plain.draws_used == 200


def test_a_stratified_paired_draw_still_draws_once_for_both_sides():
    """The property stratification must not cost. One drawn key list feeds both
    tables, so what is resampled is the difference — drawing each side's strata
    independently would resample the two conditions apart, the failure this
    construction's docstring argues about the unstratified draw.

    Pinned by an oracle rather than by inspection: with `against` holding the same
    column as `of`, a single shared draw cancels to exactly zero on every draw, so
    a zero-width pool at zero is proof the two tables saw the same keys. Two
    independent draws could not produce it."""
    from publishable.stats import paired_percentile_of_derived

    got = paired_percentile_of_derived(
        _PAIRED_OF,
        _PAIRED_OF,
        _PAIRED_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=200,
        strata=_PAIRED_STRATA,
    )
    assert set(got.pool) == {0.0}


def test_a_stratum_mapping_missing_a_drawn_key_is_a_core_defect():
    """Indexed, not `.get`-ed — the discipline `percentile_of_derived`'s own
    `strata` branch states: a caller whose roster and mapping have come to
    disagree about which units exist is a core defect, not a silent extra
    stratum."""
    from publishable.stats import paired_percentile_of_derived

    with pytest.raises(KeyError):
        paired_percentile_of_derived(
            _PAIRED_OF,
            _PAIRED_AGAINST,
            _PAIRED_KEYS,
            _mean_of_m,
            _mean_of_m,
            seed=7,
            draws=10,
            strata={"u0": "A"},
        )


def test_an_unsorted_key_list_with_strata_is_a_core_defect():
    """Not a correctness requirement — `pools.sort()` makes the whole partition
    a pure function of content, so a shuffled `keys` list under `strata` draws
    the identical sequence a sorted one does once past this check. What the
    check buys is the caller-contract discipline `percentile_of_derived`
    already keeps for itself (sorting its own `collapsed` keys rather than
    trusting a caller): this function trusts `paired_keys` to hand it a sorted
    list instead of sorting defensively, so a caller that stops doing so is a
    bookkeeping regression worth raising on rather than correcting silently."""
    from publishable.stats import paired_percentile_of_derived

    with pytest.raises(ValueError, match="sorted"):
        paired_percentile_of_derived(
            _PAIRED_OF,
            _PAIRED_AGAINST,
            ["u3", "u4", "u5", "u0", "u1", "u2"],
            _mean_of_m,
            _mean_of_m,
            seed=7,
            draws=10,
            strata=_PAIRED_STRATA,
        )


def test_an_unsorted_key_list_with_strata_and_clusters_is_a_core_defect_too():
    """The composition Minor 4 of the H4b-2 batch 2 review found untested: the
    guard reads `keys` itself, before `clusters` groups it into drawable
    things, so an unsorted `keys` list raises identically whether or not
    `clusters` is also given — this pins that `clusters` does not somehow
    exempt the check."""
    from publishable.stats import paired_percentile_of_derived

    clusters = {"u0": "c0", "u1": "c0", "u2": "c1", "u3": "c2", "u4": "c2", "u5": "c3"}
    with pytest.raises(ValueError, match="sorted"):
        paired_percentile_of_derived(
            _PAIRED_OF,
            _PAIRED_AGAINST,
            ["u3", "u4", "u5", "u0", "u1", "u2"],
            _mean_of_m,
            _mean_of_m,
            seed=7,
            draws=10,
            strata=_PAIRED_STRATA,
            clusters=clusters,
        )


_UNEQUAL_OF = {
    "u0": {"m": 1.0},
    "u1": {"m": 2.0},
    "u2": {"m": 3.0},
    "u3": {"m": 4.0},
    "u4": {"m": 100.0},
    "u5": {"m": 200.0},
}
_UNEQUAL_AGAINST = {k: {"m": 0.0} for k in _UNEQUAL_OF}
_UNEQUAL_KEYS = ["u0", "u1", "u2", "u3", "u4", "u5"]
_UNEQUAL_STRATA = {"u0": "A", "u1": "A", "u2": "B", "u3": "B", "u4": "B", "u5": "B"}


def test_a_relabelled_stratum_draws_the_identical_sequence():
    """The invariance `percentile_over_units` and `percentile_of_derived` both
    keep, and for the identical reason: pools are ordered by their own sorted
    contents rather than by label, so renaming a stratum cannot change the
    interval.

    **The strata are deliberately unequal-sized (2 and 4) with values that do
    not merely offset by a constant** (1, 2 against 3, 4, 100, 200) — an earlier
    version of this test used equal-sized strata differing by a constant, under
    which every drawn difference shifts by the same amount regardless of which
    pool is drawn first, so a genuine relabelling bug (swapping which pool a
    label points at) was invisible: it passed under a label-order mutation that
    should have failed it. This fixture breaks that translation symmetry, and a
    label-order mutation (`pools = [sorted(group) for _lab, group in
    sorted(grouped.items())]`, ordering by the label string rather than by pool
    contents) was verified to make the two calls' pools differ before this test
    was written; only the shipped content-ordering makes them agree."""
    from publishable.stats import paired_percentile_of_derived

    swapped = {k: ("B" if v == "A" else "A") for k, v in _UNEQUAL_STRATA.items()}
    first = paired_percentile_of_derived(
        _UNEQUAL_OF,
        _UNEQUAL_AGAINST,
        _UNEQUAL_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=100,
        strata=_UNEQUAL_STRATA,
    )
    second = paired_percentile_of_derived(
        _UNEQUAL_OF,
        _UNEQUAL_AGAINST,
        _UNEQUAL_KEYS,
        _mean_of_m,
        _mean_of_m,
        seed=7,
        draws=100,
        strata=swapped,
    )
    assert first.pool == second.pool


def test_a_weighted_dz_standardizes_by_the_weighted_standard_deviation():
    """`reference.md` § Statistical reporting: "A weighted condition standardizes by
    the weighted standard deviation, on the same weights the mean used."

    Exact arithmetic, not an observation. Σw = 12, Σw² = 30, so the denominator is
    12 − 30/12 = 9.5; Σw(d − 8)² = 49 + 36 + 25 + 3 + 12 + 27 = 152; 152/9.5 = 16.0,
    sd = 4.0, dz = 8.0/4.0 = 2.0. The unweighted answer over the same differences
    is 6/√20 = 1.3416..., so a weighting that did nothing lands on a different
    number rather than on this one."""
    from publishable.stats import cohens_dz, weighted_cohens_dz

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    assert weighted_cohens_dz(diffs, [1, 1, 1, 3, 3, 3]) == pytest.approx(2.0)
    assert cohens_dz(diffs) == pytest.approx(1.3416407864998738)


def test_a_weighted_dz_at_equal_weights_is_the_unweighted_one():
    """The oracle, and the reason the variance denominator is `Σw − Σw²/Σw` rather
    than `Σw`: at w ≡ 1 it is n − 1, so this is a generalization rather than a
    second statistic wearing the same name. If this ever fails, the formula is
    wrong rather than this test."""
    from publishable.stats import cohens_dz, weighted_cohens_dz

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    assert weighted_cohens_dz(diffs, [1] * 6) == pytest.approx(cohens_dz(diffs))
    # Invariant to rescaling, as every weighted construction here is: a weight
    # column summing to a population size gives the same answer as one summing to
    # the row count.
    assert weighted_cohens_dz(diffs, [7] * 6) == pytest.approx(cohens_dz(diffs))


def test_a_weighted_dz_refuses_the_degenerate_shapes_the_unweighted_one_does():
    """`None` below two differences, and `None` at zero dispersion — the two
    refusals `cohens_dz` carries, kept so the pair refuses the same inputs.

    Plus the one the weights add: a non-positive denominator. It is NOT
    reachable by concentrating all the weight on one unit — `Σw − Σw²/Σw` for
    two or more strictly positive weights is algebraically positive, and a
    fixture that only probed `[1, 0]` (refused earlier, by `checked_weights`)
    would wrongly generalize that no fixture reaches this line. It IS reachable
    by a weight ratio wide enough that `Σw²/Σw` rounds to `Σw` in floating
    point: `[1e17, 1.0]` computes a denominator of exactly `0.0`, verified
    directly below rather than only through the `None` it produces."""
    from publishable.stats import weighted_cohens_dz

    assert weighted_cohens_dz([1.0], [1]) is None
    assert weighted_cohens_dz([2.0, 2.0], [1, 3]) is None
    total = 1e17 + 1.0
    assert total - (1e17 * 1e17 + 1.0) / total == 0.0
    assert weighted_cohens_dz([1.0, 2.0], [1e17, 1.0]) is None


def test_a_weighted_paired_t_is_the_weighted_construction_under_a_paired_name():
    """The general case's raw interval, and its corrected counterpart. Delegates to
    `weighted_t_over_units` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units` — so the `Σw − Σw²/Σw`
    denominator, the Kish df and the rescaling invariance are inherited rather than
    re-derived.

    The centre is exact arithmetic: Σwd/Σw = 96/12 = 8.0 weighted against 36/6 =
    6.0 unweighted. A centre is asserted rather than an endpoint because it is
    exact under any df, so this cannot be a test that agrees with a wrong critical
    value."""
    from publishable.stats import paired_t_over_units, weighted_paired_t_over_units

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    weighted = weighted_paired_t_over_units(diffs, [1, 1, 1, 3, 3, 3])
    plain = paired_t_over_units(diffs)
    assert weighted is not None and plain is not None
    assert (weighted.low + weighted.high) / 2 == pytest.approx(8.0)
    assert (plain.low + plain.high) / 2 == pytest.approx(6.0)
    assert weighted.method == "weighted_paired_t_over_units"
    assert plain.method == "paired_t_over_units"
    # The df moved too, and it is the part that bites: Kish's size here is
    # 12²/30 = 4.8 against 6 units, so the weighted half-width is wider than the
    # weighted sem alone would give. Pinned only as an inequality against the
    # unweighted half-width — the Kish df itself is pinned elsewhere, by
    # `test_the_weighted_interval_is_the_t_interval_at_kishs_effective_size`
    # and by this file's own equal-weights oracle above.
    assert (weighted.high - weighted.low) != pytest.approx(plain.high - plain.low)


def test_a_weighted_paired_t_at_equal_weights_is_the_unweighted_one():
    """The oracle. Equal weights must reproduce `paired_t_over_units` digit for
    digit — endpoints, not merely centre — which is what `weighted_t_over_units`'
    variance denominator buys and what a `Σw` denominator would break."""
    from publishable.stats import paired_t_over_units, weighted_paired_t_over_units

    diffs = [1.0, 2.0, 3.0, 9.0, 10.0, 11.0]
    weighted = weighted_paired_t_over_units(diffs, [1] * 6)
    plain = paired_t_over_units(diffs)
    assert weighted is not None and plain is not None
    assert weighted.low == pytest.approx(plain.low)
    assert weighted.high == pytest.approx(plain.high)


def test_a_weighted_paired_t_returns_none_when_kish_falls_below_two():
    """Inherited from `weighted_t_over_units`, and worth its own pin because the
    record shape it produces is new: `ci95: null` beside a present `weighted_by`
    and an `n_paired_effective` below 2. Eight rows concentrated onto 1.7
    effective units have no more dispersion for a df to describe than one row
    does. Weights [1,1,1,9] give 12²/84 = 1.714."""
    from publishable.stats import weighted_paired_t_over_units

    assert weighted_paired_t_over_units([1.0, 2.0, 3.0, 10.0], [1, 1, 1, 9]) is None


@pytest.mark.parametrize("clustered", [False, True])
@pytest.mark.parametrize("stratified", [False, True])
def test_a_paired_draw_that_cannot_vary_reports_no_interval(clustered, stratified):
    """The defect H4b-1 filed against H4b-2 by name, closed for all four draw
    shapes at once. Every drawable thing in every stratum carries the same pair of
    rows, so every replicate reproduces the same difference, both percentile ranks
    land on it, and the interval would be `[x, x]` — a zero-width 95 % interval
    § Statistical reporting refuses in those terms, indistinguishable from a
    genuine narrow one.

    Content, not count: the clustered cells hold TWO clusters per stratum, which
    clears any count floor and is still degenerate."""
    keys = [f"u{i:02d}" for i in range(8)]
    of = {k: {"m": 3.0} for k in keys}
    against = {k: {"m": 1.0} for k in keys}
    clusters = {k: f"c{i // 2}" for i, k in enumerate(keys)} if clustered else None
    strata = {k: ("A" if k < "u04" else "B") for k in keys} if stratified else None
    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        lambda t: sum(t.m) / len(t.m),
        lambda t: sum(t.m) / len(t.m),
        seed=3,
        draws=400,
        strata=strata,
        clusters=clusters,
    )
    assert got.interval is None
    assert got.draws_used == 0
    assert got.pool == []


def test_a_paired_draw_that_can_vary_still_reports():
    """The control that must report, without which every assertion above passes
    identically against a construction that returns `None` for everything. One key
    differs from its neighbours in a single column, which is the smallest content
    difference the refusal must let through."""
    keys = [f"u{i:02d}" for i in range(8)]
    of = {k: {"m": 3.0} for k in keys}
    of["u00"] = {"m": 9.0}
    against = {k: {"m": 1.0} for k in keys}
    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        lambda t: sum(t.m) / len(t.m),
        lambda t: sum(t.m) / len(t.m),
        seed=3,
        draws=400,
    )
    assert got.interval is not None
    assert got.interval.high > got.interval.low


def _side_rows(values, prefix):
    return {f"{prefix}{i:02d}": {"m": v} for i, v in enumerate(values)}


def _row_count_recorder():
    """A compute closure that records the row count of every table it is handed.

    The percentile discriminator is the per-replicate DRAW SIZE, and § The two
    discriminating fixtures requires it be asserted rather than inferred from the
    interval — which only works if the construction admits an observable. This is
    that observable: the closure returns the column mean, so the draw proceeds
    normally, and the sizes accumulate in a list the test reads afterwards."""
    seen: list[int] = []

    def compute(table):
        seen.append(len(table))
        column = table.m
        return float(sum(column) / len(column))

    return compute, seen


def test_the_unpaired_percentile_draws_each_side_independently():
    """Fixture A through the percentile form. An independent per-side draw takes
    exactly 5 rows from `of` and exactly 25 from `against` on EVERY replicate; a
    mutant drawing once from the pooled 30 and splitting, or drawing `min(n)` for
    both, returns different sizes.

    **The draw size is asserted, not inferred from the interval.** An interval
    assertion cannot tell a pooled draw from an independent one — both produce a
    plausible number centred near 10 — and `is not None` is a uselessly weak
    discriminator on this slice, where a suppressed contrast, a thin side and a
    degenerate draw all return `None` too.

    The endpoints are pinned as literals beside the sizes, captured from this
    test's first green run in the same commit, so a later change cannot move the
    draw while keeping the counts right."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute_of, seen_of = _row_count_recorder()
    compute_against, seen_against = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute_of,
        compute_against,
        seed=7,
        draws=400,
    )
    assert set(seen_of) == {5}
    assert set(seen_against) == {25}
    assert len(seen_of) == 400 and len(seen_against) == 400
    assert got.draws_used == 400
    assert got.interval is not None
    assert got.interval.method == "unpaired_percentile_over_units"
    assert got.pool == sorted(got.pool)
    assert [got.interval.low, got.interval.high] == pytest.approx([7.400000000000002, 12.8])


def test_the_unpaired_percentile_pool_is_the_evidence_a_corrected_bound_reads():
    """`interval_at` reads fixed ranks off a pool and does not sort, so a pool
    returned unsorted gives a corrected interval built from two arbitrary
    positions. Both return paths here sort, and the too-thin path sorts a partial
    pool for the same reason.

    Asserted through `interval_at` rather than on the list alone, because the
    property that matters is that a SECOND rank pair off the same pool is wider,
    not merely that a list is ordered."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute,
        other,
        seed=7,
        draws=400,
    )
    assert got.interval is not None
    tighter = interval_at(got.pool, 0.975)
    assert tighter is not None
    assert tighter[0] <= got.interval.low and tighter[1] >= got.interval.high


def test_the_unpaired_percentile_refuses_only_when_both_sides_cannot_vary():
    """The AND rule, and it is the one a copied check gets wrong. Two constant
    sides make every replicate reproduce the same difference, so both percentile
    ranks land on it and the interval has zero width while looking exactly like a
    narrow one — the shape § Statistical reporting refuses in those terms. One
    constant side does NOT refuse: the other still varies, so the difference has a
    real sampling distribution, and an `or` here would null an interval that is
    fine.

    The one-sided case asserts a POSITIVE width rather than `is not None`, because
    a degenerate draw and a suppressed contrast both return `None` and only a width
    separates a real interval from either."""
    flat_of = _side_rows([3.0] * 5, "a")
    flat_against = _side_rows([1.0] * 25, "b")
    varied_against = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    both_flat = unpaired_percentile_of_sides(
        flat_of,
        flat_against,
        sorted(flat_of),
        sorted(flat_against),
        compute,
        other,
        seed=7,
        draws=400,
    )
    assert both_flat.interval is None
    assert both_flat.draws_used == 0
    assert both_flat.pool == []
    one_flat = unpaired_percentile_of_sides(
        flat_of,
        varied_against,
        sorted(flat_of),
        sorted(varied_against),
        compute,
        other,
        seed=7,
        draws=400,
    )
    assert one_flat.interval is not None
    assert one_flat.interval.high > one_flat.interval.low


def test_the_unpaired_percentile_refuses_a_side_below_two_keys():
    """`None` below two keys on either side, the floor every construction in this
    module shares. Asserted on both sides, because a guard reading `of_keys` alone
    passes the first case and fails nothing."""
    of_rows = _side_rows(_WELCH_OF, "a")
    against_rows = _side_rows(_WELCH_AGAINST, "b")
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    assert (
        unpaired_percentile_of_sides(
            of_rows,
            against_rows,
            ["a00"],
            sorted(against_rows),
            compute,
            other,
            seed=7,
            draws=400,
        ).interval
        is None
    )
    assert (
        unpaired_percentile_of_sides(
            of_rows,
            against_rows,
            sorted(of_rows),
            ["b00"],
            compute,
            other,
            seed=7,
            draws=400,
        ).interval
        is None
    )


def test_the_extracted_draw_pools_leaves_the_paired_draw_where_it_was():
    """The extraction is pure code motion, and this is the oracle **for its
    clustered branch**: the paired clustered draw over H4b-2's own 2/4/6 fixture
    must produce the same pool it produced before `_draw_pools` existed — an RNG
    sequence that changed by one call moves the percentiles without necessarily
    widening anything, so this asserts the ENDPOINTS rather than the width.

    **This test does not cover the unclustered branch.** Its own draw here always
    passes `clusters=`, and its two `raises` arms fail before item order can matter
    (`keys != sorted(keys)`) or take the clustered path themselves. The
    unclustered branch's own sequence is pinned by
    `test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was` and
    `test_the_unpaired_percentile_draws_each_side_independently` — both of which
    do move under a reversed unclustered `items` order, where this test's own
    fixture happens not to (its endpoints survive the reversal here, a
    coincidence of this particular fixture rather than a property of the
    extraction).

    Both raises move with the body and are re-pinned here: an unsorted `keys` under
    `strata` still raises `ValueError`, and a cluster spanning two strata still
    raises `E-STATS-RESAMPLE-STRATIFY-VARIES`."""
    keys = [f"u{i:02d}" for i in range(12)]
    values = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    of = {k: {"m": v} for k, v in zip(keys, values, strict=True)}
    against = {k: {"m": 0.0} for k in keys}
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    got = paired_percentile_of_derived(
        of,
        against,
        keys,
        compute,
        other,
        seed=7,
        draws=400,
        clusters=dict(zip(keys, labels, strict=True)),
    )
    assert got.interval is not None
    assert [got.interval.low, got.interval.high] == pytest.approx([1.0, 8.0])
    with pytest.raises(ValueError, match="sorted"):
        paired_percentile_of_derived(
            of,
            against,
            list(reversed(keys)),
            compute,
            other,
            seed=7,
            draws=400,
            strata={k: "s" for k in keys},
        )
    with pytest.raises(ContractError) as exc:
        paired_percentile_of_derived(
            of,
            against,
            keys,
            compute,
            other,
            seed=7,
            draws=400,
            strata={k: ("x" if k == "u00" else "y") for k in keys},
            clusters=dict(zip(keys, labels, strict=True)),
        )
    assert exc.value.code == "E-STATS-RESAMPLE-STRATIFY-VARIES"


_CLUSTERED_OF = [0.0] * 2 + [15.0] * 3 + [30.0] * 4
_CLUSTERED_OF_LABELS = ["p"] * 2 + ["q"] * 3 + ["r"] * 4
_CLUSTERED_AGAINST = [2.0] * 2 + [4.0] * 3 + [6.0] * 3 + [8.0] * 4
_CLUSTERED_AGAINST_LABELS = ["w"] * 2 + ["x"] * 3 + ["y"] * 3 + ["z"] * 4


def test_the_unpaired_clustered_t_combines_two_per_side_cluster_dfs():
    """Fixture B: `of` is 9 units in 3 clusters of 2/3/4 constant within cluster at
    0/15/30, `against` 12 units in 4 clusters of 2/3/3/4 at 2/4/6/8. Values
    constant within a cluster make each side's variance entirely BETWEEN-cluster,
    so CR1 cannot approximate the IID form; the sizes are unequal so no count
    assertion is forced; and the two cluster counts differ, 3 against 4, so a
    construction reading one side's count writes a wrong integer.

    Per-side CR1 variances 67.0782 (G = 3) and 1.5880 (G = 4), SE 8.2865,
    Welch-Satterthwaite df over `G_s` − 1 = 2.0950, half-width 34.1481. Five wrong
    readings give five other numbers: `min(G) − 1` gives 35.6540, `G_against − 1`
    gives 26.3714, `G_total − 2` gives 21.3011, `n_of + n_against − 2` gives
    17.3439, and the IID Welch form on the identical data gives 9.6472. **The
    correct answer is above one of them and below four**, so an assertion on the
    number discriminates every failure mode, which an assertion on "is it wider"
    does not."""
    interval = welch_t_over_units_clustered(
        _CLUSTERED_OF,
        _CLUSTERED_OF_LABELS,
        _CLUSTERED_AGAINST,
        _CLUSTERED_AGAINST_LABELS,
    )
    assert interval is not None
    assert interval.method == "welch_t_over_units_clustered"
    centre = (interval.low + interval.high) / 2
    half = (interval.high - interval.low) / 2
    assert centre == pytest.approx(12.833333333333332)
    assert half == pytest.approx(34.14810237373095)


def test_the_unpaired_clustered_t_is_not_the_iid_welch_form_on_the_same_data():
    """The control that must report, and the number a membership-ignoring mutant
    lands on. The IID Welch form over the identical values gives 9.6472 — three and
    a half times narrower, at the same centre. **A test asserting the centre alone
    is blind to clustering entirely**, which is why the centre is asserted only
    beside the half-width above."""
    plain = welch_t_over_units(_CLUSTERED_OF, _CLUSTERED_AGAINST)
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(9.647234756296374)


def test_the_unpaired_clustered_t_refuses_a_side_below_two_clusters():
    """Both floors, per side: `None` below two values and `None` below two clusters,
    where that side's df would be zero. The second is the one a singleton-cluster
    fixture can never see — one unit per cluster makes `G − 1` equal `n − 1`, so
    the clustered and IID forms coincide exactly and every assertion passes under a
    mutant ignoring membership. Hence the last case, which is correct and is
    exactly why no other test here may use that shape."""
    assert (
        welch_t_over_units_clustered(
            _CLUSTERED_OF, ["p"] * 9, _CLUSTERED_AGAINST, _CLUSTERED_AGAINST_LABELS
        )
        is None
    )
    assert (
        welch_t_over_units_clustered(
            _CLUSTERED_OF, _CLUSTERED_OF_LABELS, _CLUSTERED_AGAINST, ["w"] * 12
        )
        is None
    )
    singletons = welch_t_over_units_clustered(
        _CLUSTERED_OF,
        [f"p{i}" for i in range(9)],
        _CLUSTERED_AGAINST,
        [f"w{i}" for i in range(12)],
    )
    iid = welch_t_over_units(_CLUSTERED_OF, _CLUSTERED_AGAINST)
    assert singletons is not None and iid is not None
    assert (singletons.high - singletons.low) == pytest.approx(iid.high - iid.low)


def test_the_extracted_cr1_variance_leaves_the_clustered_t_where_it_was():
    """The extraction is pure code motion and this is the oracle. H4b-2's own 2/4/6
    fixture through `t_over_units_clustered` must give the half-width it gave
    before `_cr1_variance` existed — 8.763214143637903, which
    `tests/test_stats.py`'s paired clustered test already pins independently.

    The `G/(G−1)` finite-sample scaling is what a careless move drops, and dropping
    it is not a rounding difference: it is the CR0 estimator wearing CR1's name,
    biased downward by exactly the factor a small cluster count makes largest."""
    diffs = [1.0] * 2 + [5.0] * 4 + [9.0] * 6
    labels = ["a"] * 2 + ["b"] * 4 + ["c"] * 6
    keys = [str(i) for i in range(12)]
    plain = t_over_units_clustered(diffs, keys, dict(zip(keys, labels, strict=True)))
    assert plain is not None
    assert (plain.high - plain.low) / 2 == pytest.approx(8.763214143637903)
    got = _cr1_variance(diffs, keys, dict(zip(keys, labels, strict=True)))
    assert got is not None
    variance, groups = got
    assert groups == 3
    assert variance == pytest.approx((3 / 2) * 398.22222222222223 / (12 * 12))


def test_the_unpaired_clustered_percentile_draws_whole_clusters_per_side():
    """Fixture B through the percentile form. `of` holds clusters of 2/3/4, so a
    replicate drawing 3 clusters with replacement pools between 6 and 12 rows; a
    mutant drawing UNITS returns a fixed 9. `against` holds 2/3/3/4 and varies
    between 8 and 16 against a fixed 12.

    **The varying row count is the assertion**, not the interval: equal cluster
    sizes would make "a replicate's pooled row count varies" invisible and a
    unit-drawing mutant would never be seen, which is why fixture B's clusters are
    unequal in size within each side as well as unequal in count between them.

    The two sides are asserted separately, because a construction passing
    `of_clusters` to both sides would give the `against` side `of`'s sizes and a
    single pooled assertion would not notice.

    **The endpoints below are construction-pinned, not merely captured.**
    `-4.7272727272727275` = −52/11 and `23.242424242424242` = 767/33 are reachable
    under a whole-cluster draw over this fixture (`of`: 3 cluster draws with
    replacement from totals/sizes 0/2, 45/3, 120/4; `against`: 4 from 4/2, 12/3,
    18/3, 32/4) and are **unreachable** under a unit draw over the same rows,
    verified by exact-rational enumeration of both draws' achievable differences —
    the two sets share the same range (−8 … 28), so only the denominators tell
    them apart."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    of_clusters = dict(zip(sorted(of_rows), _CLUSTERED_OF_LABELS, strict=True))
    against_clusters = dict(zip(sorted(against_rows), _CLUSTERED_AGAINST_LABELS, strict=True))
    compute_of, seen_of = _row_count_recorder()
    compute_against, seen_against = _row_count_recorder()
    got = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute_of,
        compute_against,
        seed=7,
        draws=400,
        method="unpaired_percentile_over_units_clustered",
        of_clusters=of_clusters,
        against_clusters=against_clusters,
    )
    assert got.interval is not None
    assert got.interval.method == "unpaired_percentile_over_units_clustered"
    assert len(set(seen_of)) > 1  # a unit draw would give exactly {9}
    assert min(seen_of) >= 6 and max(seen_of) <= 12
    assert len(set(seen_against)) > 1  # a unit draw would give exactly {12}
    assert min(seen_against) >= 8 and max(seen_against) <= 16
    assert [got.interval.low, got.interval.high] == pytest.approx(
        [-4.7272727272727275, 23.242424242424242]
    )


def test_the_unpaired_clustered_percentile_is_not_the_unclustered_one():
    """The control that must report. The same rows drawn as units give a different
    interval, and the endpoints of both are pinned as literals rather than compared
    only for inequality — `!=` alone passes for any third wrong pair, and it is the
    weak-discriminator shape this slice bans by name.

    **These endpoints are construction-pinned too, the mirror image of the
    clustered test's.** `4.0` and `19.833333333333332` = 119/6 are reachable under
    a unit draw over these same rows and unreachable under the whole-cluster draw
    above — verified by the same exact-rational enumeration, over the same shared
    range (−8 … 28)."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    compute, _ = _row_count_recorder()
    other, _ = _row_count_recorder()
    unclustered = unpaired_percentile_of_sides(
        of_rows,
        against_rows,
        sorted(of_rows),
        sorted(against_rows),
        compute,
        other,
        seed=7,
        draws=400,
    )
    assert unclustered.interval is not None
    assert unclustered.interval.method == "unpaired_percentile_over_units"
    assert [unclustered.interval.low, unclustered.interval.high] == pytest.approx(
        [4.0, 19.833333333333332]
    )


def test_the_unpaired_clustered_percentile_is_invariant_to_relabelling():
    """`_draw_pools` orders clusters by their own sorted contents rather than by
    label, so a relabelled roster draws the identical sequence — the invariance
    `percentile_over_units_clustered` keeps and the one a `sorted(by_cluster)` over
    LABELS would silently break. Asserted on the endpoints, which is the only place
    a changed draw sequence shows."""
    of_rows = {f"of{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_OF)}
    against_rows = {f"ag{i:02d}": {"m": v} for i, v in enumerate(_CLUSTERED_AGAINST)}
    renamed = {"p": "zz", "q": "aa", "r": "mm"}
    first, second = [], []
    for labels in (_CLUSTERED_OF_LABELS, [renamed[x] for x in _CLUSTERED_OF_LABELS]):
        compute, _ = _row_count_recorder()
        other, _ = _row_count_recorder()
        got = unpaired_percentile_of_sides(
            of_rows,
            against_rows,
            sorted(of_rows),
            sorted(against_rows),
            compute,
            other,
            seed=7,
            draws=400,
            method="unpaired_percentile_over_units_clustered",
            of_clusters=dict(zip(sorted(of_rows), labels, strict=True)),
            against_clusters=dict(
                zip(sorted(against_rows), _CLUSTERED_AGAINST_LABELS, strict=True)
            ),
        )
        assert got.interval is not None
        (first if labels is _CLUSTERED_OF_LABELS else second).append(
            [got.interval.low, got.interval.high]
        )
    assert first == second


_C_VALUES: list[float] = []
_C_LABELS: list[str] = []
_C_CLUSTERS: list[str] = []
for _c in range(1, 11):
    for _i in range(5):
        _C_VALUES.append(float(100 * _c + _i))
        _C_LABELS.append("of" if _i >= 3 else "against")
        _C_CLUSTERS.append(f"M{_c:02d}")


def test_an_unclustered_null_over_fixture_c_relabels_across_the_matched_sets():
    """Fixture C, unclustered. `of` is the top two of every matched set, so the
    observed delta is 2.5 = 553.5 − 551.0 — but the UNCLUSTERED null is free to
    relabel across sets, so `of` can hold the global top 20 (mean 852 against 352,
    delta 500). The observed 2.5 sits near the centre of a null spanning ±500, and
    the p-value is close to 0.5.

    **This is the wrong-stratum mutant's number, asserted here as the CORRECT
    answer for the unclustered construction** — which is exactly why task 13's
    clustered fixture can tell the two apart: 0.0002 against ≈0.5 is four orders
    of magnitude, not a rounding difference.

    Asserted as a range rather than a literal, because a free permutation's p is a
    Monte Carlo quantity: the range is far tighter than the gap to any other
    candidate reading, and a literal would pin the RNG rather than the estimator."""
    p = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=7, n=5000)
    assert p is not None
    assert 0.3 < p < 0.7  # measured 0.4845 at seed 11 with a prototype at `a207702`


def test_the_permutation_p_value_counts_the_observed_labelling_itself():
    """The ±1 continuity, on a fixture built so `b = 0`: the observed labelling
    is the unique maximum over ALL free relabellings, so no draw can reach it.

    **Corrected from the brief's own 6-value fixture** (`[1, 2, 3, 4, 100, 200]`,
    `of` the top two of six): that fixture's uniqueness claim is true, but its
    arrangement SPACE is not — `C(6, 2) = 15` distinct label arrangements, and at
    `n = 999` draws the expected number that land on the unique maximum is
    `999/15 ≈ 66.6`, not zero. Measured directly (`uv run python -c`, this
    module's own `permutation_over_units`): `p = 0.07`, not `1/1000`. A fixture
    whose numbers agree with the bug is the shape `CLAUDE.md` warns against, and
    the brief's own rule applies — report the disagreement rather than adjusting
    the assertion until it agrees with a false premise.

    **This fixture instead widens the arrangement space**: 20 values, `of` the
    top ten. `C(20, 10) = 184 756`, five orders of magnitude above
    `n = 999`, so the expected count landing on the unique maximum is
    `≈0.0054` — measured at five different seeds (1 through 5) to confirm `b = 0`
    at every one, not merely the one this test pins, before trusting it as
    reliably deterministic in practice."""
    values = [float(i) for i in range(20)]
    labels = ["against"] * 10 + ["of"] * 10
    p = permutation_over_units(values, labels, "of", seed=3, n=999)
    assert p == pytest.approx(1.0 / 1000.0)
    assert p != 0.0


def test_an_invariant_null_reports_no_p_value_rather_than_one():
    """Decision 8's invariance rule, on
    `percentile_over_units_clustered`'s shipped precedent — "the degenerate case is
    content, not count". Every unit carries the same value, so every relabelling
    reproduces the observed statistic and a p-value of 1.0 would be computed from a
    distribution that could not have been anything else.

    `None`, and no new warning code: the record already carries the resolved
    `null_test` echo beside the `null` p-value, which says the test ran and
    produced nothing."""
    labels = ["of"] * 3 + ["against"] * 5
    assert permutation_over_units([5.0] * 8, labels, "of", seed=1, n=200) is None


def test_a_relabelling_that_empties_an_arm_reports_no_p_value():
    """An observed labelling with nothing on one side has no statistic to test, so
    it is the same honest absence rather than a `ZeroDivisionError`. This is also
    the shape task 13's wrong-level mutant produces, which is why it is pinned
    here rather than only there."""
    assert permutation_over_units([1.0, 2.0, 3.0], ["against"] * 3, "of", seed=1, n=200) is None


def test_a_permutation_over_units_with_a_nan_value_reports_no_p_value_rather_than_a_false_one():
    """H4d task 23, claimed rather than re-declined a fourth time
    (`docs/superpowers/spec-defects.md`, "a column resample is only ever
    defined given finite inputs"). Before `_label_delta`'s guard, an
    unrecoverable `nan` observed statistic made every `>=` comparison `False`
    and this call reported `0.009900990099009901` — a small, real-looking
    p-value from a table nobody could compute a mean of. `None` is the honest
    absence, the same one an emptied arm already gets."""
    values = [1.0, 2.0, 3.0, float("nan")]
    labels = ["of", "of", "against", "against"]
    assert permutation_over_units(values, labels, "of", seed=1, n=100) is None


def test_the_permutation_p_value_is_reproducible_from_its_seed():
    """Two calls at one seed agree and two seeds do not, over a fixture whose null
    is genuinely variable. A construction that ignored the seed would pass the
    first assertion and fail the second; one that ignored the labels entirely
    would pass both, which is what the fixtures above are for."""
    a = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=7, n=500)
    b = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=7, n=500)
    c = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=8, n=500)
    assert a == b
    assert a != c


def test_the_unstratified_permutation_walk_is_pinned_at_a_literal_seed():
    """**Fix round 1, Minor 6.** Task 14's `strata` refactor moved this
    function's unstratified RNG stream — each draw now shuffles a fresh
    per-group copy and writes it back, rather than shuffling `pool` in place
    — and every existing assertion on this path is range-based, so nothing
    failed and nothing pinned the new walk. A future refactor of this shape
    would be equally invisible without a literal here.

    `0.473505298940212`, at `seed=7, n=5000` over fixture C: the value this
    docstring's own review measured after the refactor (`0.48050` before it).
    If this literal ever needs to move, the docstring's claim about WHY
    should move with it — an unexplained change here is exactly the signal
    the review is naming."""
    assert permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=7, n=5000) == pytest.approx(
        0.473505298940212
    )


def test_a_draw_that_ties_the_observed_statistic_counts_against_it():
    """The `>=` comparison, on a fixture sized so ties are common rather than
    a coincidence: four units, values `[1.0, 1.0, 2.0, 2.0]`, labels `["of",
    "against", "of", "against"]`. Its six distinct relabellings give deltas
    `[-1, 0, 0, 0, 0, 1]` (enumerated with `itertools.combinations` over which
    two positions hold `of`) and the observed delta is `0`, so four of six
    relabellings tie it and a fifth exceeds it — five of six reach `>= observed`,
    one does not. A `>` comparison would drop the four ties and count only the
    one exceedance, a categorically smaller number this range is wide enough to
    tell apart from `>=`'s."""
    values = [1.0, 1.0, 2.0, 2.0]
    labels = ["of", "against", "of", "against"]
    p = permutation_over_units(values, labels, "of", seed=3, n=999)
    assert p is not None
    assert 0.75 < p < 0.9


def _c_collapsed() -> dict[str, dict[str, float]]:
    """Fixture C as a collapsed table: 50 units, `y` only. The LABEL is not in the
    table — it travels as the `labels` mapping, which is what a relabelling
    permutes and what `cli`'s closure merges back in."""
    return {f"u{c:02d}_{i}": {"y": float(100 * c + i)} for c in range(1, 11) for i in range(5)}


def _c_labels() -> dict[str, str]:
    return {
        f"u{c:02d}_{i}": ("of" if i >= 3 else "against") for c in range(1, 11) for i in range(5)
    }


def _c_compute(table, labels):
    """`mean(y | of) − mean(y | against)`, read through the LABELS ARGUMENT.

    This is the shape `cli`'s null-test closure has and the shape
    `percentile_of_derived`'s `compute` cannot express: a one-argument closure
    would have to read the label off the row, and `cli._attributed` overwrites it
    from the roster on every call."""
    of = [row["y"] for row in table if labels[row["unit"]] == "of"]
    against = [row["y"] for row in table if labels[row["unit"]] != "of"]
    if not of or not against:
        return None
    return sum(of) / len(of) - sum(against) / len(against)


def test_a_derived_permutation_relabels_and_recomputes_through_the_labels_argument():
    """Fixture C, unclustered and derived. The observed delta is 2.5; free
    relabelling lets `of` hold the global top 20 (delta 500), so the observed sits
    near the centre of the null and the p is near 0.5 — the same number the
    unclustered COLUMN construction gives, which is what says the two agree about
    what one draw is.

    The load-bearing assertion is the SURVIVOR COUNT: 500 requested, 500
    surviving, because every relabelling of this fixture leaves both arms
    non-empty. A count below the request would say draws were being dropped, which
    on this fixture can only mean the closure was handed something it could not
    read."""
    p, survivors = permutation_of_derived(_c_collapsed(), _c_labels(), _c_compute, seed=7, n=500)
    assert p is not None
    assert 0.3 < p < 0.7
    assert survivors == 500


def test_summarize_step_writes_a_derived_p_value_through_the_null_fns_closure():
    """Task 20, fixture C2's spirit, RESHAPED against a measured gap. The
    brief's own literal was `p_value == 1/5001` under a declared `cluster_by`
    and `level: "within_cluster"` — measured directly against `permutation_of_derived`
    at `a207702`-equivalent and found unreachable: that function does one free
    `rng.shuffle` over every unit's label and takes no cluster argument at all,
    so a declared `cluster_by` here gives the spec's OWN "permutes across
    clusters (the wrong stratum)" answer, ≈0.4845, not the within-cluster
    `1/5001` a `cluster_by` promises. Publishing that number beside
    `level: "within_cluster"` would be a declaration accepted whose effect is
    not delivered — worse than no p-value — so `summarize_step` gates this
    write on `clusters is None` (see its docstring and the code comment beside
    the gate) and this test is reshaped to the roster that gate actually
    serves: no `cluster_by` declared, and the free relabelling's own number
    asserted as a range, matching `test_a_derived_permutation_relabels_and_
    recomputes_through_the_labels_argument`'s own pin on the same fixture.

    The decision-5 assertion travels regardless of the reshape: no
    `p_value_corrected` here, ever — the correction pass merges that in from
    outside this call."""
    collapsed = _c_collapsed()
    counts = {"resolved": 50, "completed": 50, "ineligible": 0, "failed": 0}
    derived = {"delta_y": _c_compute(UnitTable(collapsed), _c_labels())}
    out = summarize_step(
        collapsed,
        counts,
        derived=derived,
        seed=7,
        draws=400,
        null_test={"method": "permutation", "n": 500, "shuffle": "label", "level": "rows"},
        labels=_c_labels(),
        null_fns={"delta_y": _c_compute},
    )
    block = out["delta_y"]
    assert block["p_value"] is not None
    assert 0.3 < block["p_value"] < 0.7
    assert block["null_draws"] == 500
    assert block["null_test"] == {
        "method": "permutation",
        "n": 500,
        "shuffle": "label",
        "level": "rows",
    }
    assert "p_value_corrected" not in block


def test_summarize_step_writes_no_p_value_for_a_derived_metric_under_a_declared_cluster_by():
    """The gate's own pin, as a relation between two calls over the SAME
    roster rather than as a bare absence: without the unclustered control, a
    `summarize_step` that wrote no p-value under any circumstance would pass
    this half identically."""
    collapsed = _c_collapsed()
    counts = {"resolved": 50, "completed": 50, "ineligible": 0, "failed": 0}
    derived = {"delta_y": _c_compute(UnitTable(collapsed), _c_labels())}
    clusters = {f"u{c:02d}_{i}": f"M{c:02d}" for c in range(1, 11) for i in range(5)}
    shared_kwargs = dict(
        derived=derived,
        seed=7,
        draws=400,
        null_test={
            "method": "permutation",
            "n": 500,
            "shuffle": "label",
            "level": "within_cluster",
        },
        labels=_c_labels(),
        null_fns={"delta_y": _c_compute},
    )
    clustered = summarize_step(collapsed, counts, clusters=clusters, **shared_kwargs)
    unclustered = summarize_step(collapsed, counts, **shared_kwargs)
    assert "p_value" not in clustered["delta_y"]
    assert "null_draws" not in clustered["delta_y"]
    assert "null_test" not in clustered["delta_y"]
    assert unclustered["delta_y"]["p_value"] is not None
    assert "null_draws" in unclustered["delta_y"]
    assert "null_test" in unclustered["delta_y"]


def test_a_per_condition_recorded_column_gets_no_p_value_at_all():
    """Decision 7. `mean(column)` over a condition's units is invariant under
    every relabelling, so a null would be the observed value repeated `n`
    times and the p-value exactly 1.0 — a number that reads as a finding and
    is an artifact of asking. Absent, not null, and not 1.0.

    The DERIVED metric in the same block carries one, which is what says the
    absence is a rule about columns rather than a `null_test` that failed to
    run."""
    collapsed = _c_collapsed()
    counts = {"resolved": 50, "completed": 50, "ineligible": 0, "failed": 0}
    for values in collapsed.values():
        values["extra"] = 1.0
    derived = {"delta_y": _c_compute(UnitTable(collapsed), _c_labels())}
    out = summarize_step(
        collapsed,
        counts,
        derived=derived,
        seed=7,
        draws=400,
        null_test={"method": "permutation", "n": 500, "shuffle": "label", "level": "rows"},
        labels=_c_labels(),
        null_fns={"delta_y": _c_compute},
    )
    assert "p_value" not in out["y"]
    assert "null_test" not in out["y"]
    assert "p_value" not in out["extra"]
    assert out["delta_y"]["p_value"] is not None


def test_a_report_by_level_block_carries_no_p_value_while_its_condition_does():
    """§ Corrections, correction 8 / task 20's ruling: `command_run`'s second
    `summarize_step` call, once per `statistics.report_by` level, passes no
    `null_test`, `labels` or `null_fns` — a level describes rather than
    compares, so it joins no correction family and gets no null, while the
    condition's own block, computed over the same roster, carries one.

    Called here at two direct `summarize_step` calls, not against
    `command_run` itself: this test shows only that `summarize_step` behaves
    differently when handed different keywords — it does not pin that
    `command_run` calls it that way. That pin is
    `tests/test_cli.py`'s end-to-end `run`-verified fixture, built once
    `E-STATS-NULLTEST-UNSUPPORTED` retired (H4d tasks 25+26).

    Both halves in one test: asserting the level alone would pass identically
    if the null had failed to run for the whole condition."""
    collapsed = _c_collapsed()
    counts = {"resolved": 50, "completed": 50, "ineligible": 0, "failed": 0}
    derived = {"delta_y": _c_compute(UnitTable(collapsed), _c_labels())}
    condition_block = summarize_step(
        collapsed,
        counts,
        derived=derived,
        seed=7,
        draws=400,
        null_test={"method": "permutation", "n": 500, "shuffle": "label", "level": "rows"},
        labels=_c_labels(),
        null_fns={"delta_y": _c_compute},
    )
    # The level call site: the same roster and the same derived value, but
    # `command_run` passes none of the three null-test keywords — the ruling
    # this test pins.
    level_block = summarize_step(collapsed, counts, derived=derived, seed=7, draws=400)
    assert condition_block["delta_y"]["p_value"] is not None
    assert "p_value" not in level_block["delta_y"]
    assert "null_test" not in level_block["delta_y"]


def test_a_derived_permutation_drops_a_degenerate_draw_and_still_reports_its_count():
    """`None`, `nan` and a raise are one situation from three libraries.

    **Corrected from the brief's own fixture**, which raised on "any draw whose
    `of` arm holds fewer than two units": a permutation null holds the LABEL
    MULTISET fixed (`rng.shuffle(pool)` only reorders it), so the `of` arm's
    *count* is exactly 3 on every one of the 200 draws here, identical to the
    observed labelling's — the raise's own guard could therefore never fire, and
    the fixture failed the same constraint a fixture "whose numbers agree with
    the bug" fails. Measured directly: at this fixture and seed, `survivors ==
    200` for the count-based guard, not `0 < survivors < 200`.

    **This fixture instead conditions on the SUM of the `of` arm's values**,
    which *does* vary across draws even though the count does not — six units
    valued `0..5`, three always labelled `of`, and `sum(of)` ranges `3..12`
    over the twenty possible label arrangements with roughly half below 8 and
    half at or above it (enumerated with `itertools.combinations`: sums
    `[3, 4, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10, 10, 11, 12]`, ten of
    twenty below 8). Some draws raise and some don't, and the count says how
    many survived — the distinction `percentile_of_derived`'s own second
    return value exists to make.

    The count is asserted as a strict inequality on BOTH sides: `0 < survivors <
    200`. A test asserting only `survivors < 200` would pass if every draw were
    dropped, which is the 'a control asserting only absences' shape."""

    def fragile(table, labels):
        of = [row["y"] for row in table if labels[row["unit"]] == "of"]
        if sum(of) < 8.0:
            raise ZeroDivisionError("degenerate draw")
        against = [row["y"] for row in table if labels[row["unit"]] != "of"]
        return sum(of) / len(of) - sum(against) / len(against)

    collapsed = {f"u{i}": {"y": float(i)} for i in range(6)}
    labels = {"u0": "against", "u1": "against", "u2": "against", "u3": "of", "u4": "of", "u5": "of"}
    p, survivors = permutation_of_derived(collapsed, labels, fragile, seed=5, n=200)
    assert 0 < survivors < 200
    assert p is not None


def test_a_derived_permutation_reports_no_p_value_when_the_metric_cannot_move():
    """Decision 8, one construction over from task 11's. A closure ignoring the
    labels entirely — the exact shape a one-argument `compute` degenerates into —
    reproduces the observed statistic on every draw, and that is reported as
    `None` rather than as 1.0. **The survivor count still comes back**, which is
    what says the null ran."""
    p, survivors = permutation_of_derived(
        _c_collapsed(), _c_labels(), lambda table, labels: 1.0, seed=1, n=100
    )
    assert p is None
    assert survivors == 100


def test_a_derived_permutation_whose_unpermuted_call_declines_reports_nothing():
    """No observed statistic, no test. Distinguished from the degenerate-null case
    by the survivor count, which is 0 here and `n` there — the two states
    `percentile_of_derived`'s own count exists to separate."""
    p, survivors = permutation_of_derived(
        _c_collapsed(), _c_labels(), lambda table, labels: None, seed=1, n=100
    )
    assert p is None
    assert survivors == 0


def test_a_derived_permutation_lets_the_unpermuted_calls_failure_out():
    """The other half of the survivor rule, and the one a closure returning
    `None` cannot exercise: a RAISE on the unpermuted call is a fault in the
    metric's own definition for this table, so it propagates rather than being read
    as a degenerate draw. `percentile_of_derived` leaves its single unresampled
    call uncontained for that reason, and `cli.py` is where the containment lives.

    Without this test the docstring's claim and the body could disagree silently —
    the test above passes whether or not that call is wrapped in a `try`."""

    def explodes(table, labels):
        raise ZeroDivisionError("the metric's own definition failed")

    with pytest.raises(ZeroDivisionError):
        permutation_of_derived(_c_collapsed(), _c_labels(), explodes, seed=1, n=10)


def test_a_within_cluster_permutation_over_fixture_c_gives_exactly_one_over_n_plus_one():
    """**The load-bearing literal of this slice.** Fixture C: 50 units in 10 matched
    sets of 5, `of` holding each set's top two. With per-cluster arm counts held
    fixed, `delta = ΣS_c/12 − 920` is strictly increasing in the sum of the `of`
    values, so the observed labelling is the UNIQUE maximum over all 10¹⁰
    within-cluster relabellings — `b = 0`, deterministically, since the observed
    labelling is drawn with probability 5 × 10⁻⁷ over 5000 draws.

    So the correct answer is exactly `1/5001`, and every wrong construction gives a
    categorically different number: `b/n` gives 0.0, reusing the observed
    assignment gives 1.0, permuting across clusters gives ≈0.5 (the free null spans
    ±500 around an observed 2.5), and relabelling whole clusters empties the `of`
    arm and gives `None`. **None of the four is within four orders of magnitude of
    another**, which is what makes this fixture worth its arithmetic."""
    p = permutation_over_units_clustered(
        _C_VALUES, _C_LABELS, _C_CLUSTERS, "of", seed=11, n=5000, level="within_cluster"
    )
    assert p == pytest.approx(1.0 / 5001.0)


def test_a_within_cluster_permutation_is_not_the_free_one_over_the_same_roster():
    """The control that must report, and the number the wrong-stratum mutant lands
    on. Free relabelling of fixture C lets `of` hold the global top 20 — mean 852
    against 352 — so the null spans ±500 and the observed 2.5 sits near its centre.
    Asserted as a relation between the two calls rather than as two literals, so
    the test cannot pass by pinning one construction twice."""
    within = permutation_over_units_clustered(
        _C_VALUES, _C_LABELS, _C_CLUSTERS, "of", seed=11, n=5000, level="within_cluster"
    )
    free = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=11, n=5000)
    assert within is not None and free is not None
    assert free > 100 * within


def test_a_whole_cluster_relabelling_of_fixture_c_empties_an_arm_and_reports_nothing():
    """Every matched set's modal arm is `against` (3 against 2), so a cluster-level
    relabelling puts NO unit in `of`. That is an empty arm, which decision 8 reports
    as `null` rather than as a number — categorically distinct from every row above,
    and the reason fixture C's clusters were built to hold both arms unequally."""
    assert (
        permutation_over_units_clustered(
            _C_VALUES, _C_LABELS, _C_CLUSTERS, "of", seed=11, n=500, level="whole_cluster"
        )
        is None
    )


def test_a_whole_cluster_relabelling_permutes_the_clusters_own_labels():
    """The whole-cluster construction, on a roster where it is the RIGHT one: four
    sites, each entirely `of` or entirely `against`, unequal in size (3, 1, 1, 2).

    **The six assignments of two `of` labels to four sites give six DIFFERENT
    deltas** — enumerated at `a207702` as 8.5, 3.833, 2.6, −2.6, −3.833, −8.5 —
    and the observed one is the strict maximum, so `b` counts exactly the draws
    that reproduced the observed assignment: about `n/6`.

    **No literal is assertable at |Π| = 6, and that is stated rather than worked
    around.** The spec's own trap table says so: "with |Π| = 36 it is drawn ~139
    times and no literal is assertable". So the assertion is a range around 1/6
    (measured 0.148 at this seed) PLUS the within-cluster call on the same
    fixture, which is `None` because permuting labels inside a single-label
    cluster is a no-op. The pair is what discriminates: a construction taking the
    wrong branch cannot produce both numbers."""
    values = [10.0, 12.0, 11.0, 9.0, 1.0, 2.0, 3.0]
    labels = ["of"] * 4 + ["against"] * 3
    clusters = ["S1", "S1", "S1", "S2", "S3", "S4", "S4"]
    p = permutation_over_units_clustered(
        values, labels, clusters, "of", seed=4, n=999, level="whole_cluster"
    )
    assert p is not None
    assert 0.10 < p < 0.25
    assert (
        permutation_over_units_clustered(
            values, labels, clusters, "of", seed=4, n=999, level="within_cluster"
        )
        is None
    )


def test_a_contrast_permutation_relabels_which_side_a_unit_is_on():
    """Fixture C as a contrast: the 20 `of` units against the 30 `against` ones,
    clustered by matched set, at the within-cluster level. Same roster, same
    observed delta of 2.5, and — because it is the same construction — the same
    `1/5001`. **The two homes differ in where the number lands, not in what it
    is**, and this assertion is what says so."""
    of = [v for v, label in zip(_C_VALUES, _C_LABELS, strict=True) if label == "of"]
    against = [v for v, label in zip(_C_VALUES, _C_LABELS, strict=True) if label != "of"]
    of_clusters = [c for c, label in zip(_C_CLUSTERS, _C_LABELS, strict=True) if label == "of"]
    against_clusters = [c for c, label in zip(_C_CLUSTERS, _C_LABELS, strict=True) if label != "of"]
    p = permutation_over_contrast(
        of,
        against,
        seed=11,
        n=5000,
        of_clusters=of_clusters,
        against_clusters=against_clusters,
        level="within_cluster",
    )
    assert p == pytest.approx(1.0 / 5001.0)


def test_a_contrast_permutation_is_confined_to_the_cells_of_every_other_group_axis():
    """ "Permuted within cells of every *other* group axis, so a cross isn't
    destroyed."

    **Corrected from the brief's own fixture.** The brief's four-unit, two-cell
    fixture (`values = [1.0, 2.0, 1000.0, 2000.0]`, cells of size 2) asserted
    `confined == 1/1000`, but a 2-unit cell has only 2 arrangements, so two such
    cells give an arrangement space of `2 × 2 = 4` — enumerated directly, the
    deltas are `-500.5, 499.5, -499.5, 500.5`, the observed IS the unique
    maximum, but over a space of 4, not thousands; at `n = 999` the expected
    count reaching it is `≈ 999/4 ≈ 250`, not 0, and the total roster is only 4
    units, so even the FREE permutation has only `C(4, 2) = 6` arrangements —
    nowhere near enough freedom to reach the mid-null answer the brief's own
    docstring predicted. Measured: `confined ≈ 0.252`, `free ≈ 0.344`, barely
    distinguishable — a second instance of "a fixture whose numbers agree with
    the bug", found the same way task 13's was: by computing before trusting.

    **Fixture C, reused rather than invented a second time**, with its own
    matched sets as `strata` instead of `clusters` — the two mechanisms are the
    identical within-group shuffle, so this is expected to reproduce task 13's
    own `1/5001`-shaped answer at this construction's own `(seed, n)`, and it
    does: `confined == 1/1000` at `seed=2, n=999`, matching the brief's original
    literal exactly once the fixture actually has the arrangement space (10¹⁰)
    to earn it. `free` stays near 0.48, the free-relabelling answer task 11's
    own suite already pins for this roster — so the two remain three orders of
    magnitude apart, which is what the brief's docstring described and the
    four-unit fixture could not deliver."""
    confined = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=2, n=999, strata=_C_CLUSTERS)
    free = permutation_over_units(_C_VALUES, _C_LABELS, "of", seed=2, n=999)
    assert confined == pytest.approx(1.0 / 1000.0)
    assert free is not None
    assert free > 0.2
    assert free > 100 * confined


def test_a_contrast_permutation_over_disjoint_sides_with_no_cluster_is_the_row_draw():
    """The unclustered contrast, which is the reachable shape for a design with no
    `cluster_by`. Asserted against the equivalent `permutation_over_units` call on
    the concatenated vectors, so the delegation is pinned as an identity rather
    than as two numbers that happen to agree at one seed."""
    of = [10.0, 12.0, 14.0]
    against = [1.0, 2.0, 3.0, 4.0]
    direct = permutation_over_units(of + against, ["of"] * 3 + ["against"] * 4, "of", seed=6, n=999)
    assert permutation_over_contrast(of, against, seed=6, n=999) == direct


def test_a_clustered_derived_draw_rests_on_the_cluster_count_not_the_row_count():
    """`reference.md` § Clustered units: "300 cells from 10 animals give a 10-draw
    interval". The fixture is 4 clusters of unequal size holding 20 units, and the
    discriminating property is that the interval is WIDER than the unit-level one
    over the same table — a unit-level draw of clustered data is "too narrow to
    believe", which is the whole reason this construction exists.

    Asserted as a relation between two widths rather than as two literals: a
    literal pins one construction twice and cannot see that the other moved."""
    collapsed = {f"c{c}_{i}": {"y": float(10 * c + i)} for c in range(1, 5) for i in range(c + 2)}
    clusters = {key: key.split("_")[0] for key in collapsed}

    def mean_y(table):
        rows = [row["y"] for row in table]
        return sum(rows) / len(rows)

    clustered_resampled = percentile_of_derived_clustered(
        collapsed, clusters, mean_y, seed=3, draws=500
    )
    clustered, survivors = clustered_resampled.interval, clustered_resampled.draws_used
    unit_level = percentile_of_derived(collapsed, mean_y, seed=3, draws=500).interval
    assert clustered is not None and unit_level is not None
    assert survivors == 500
    assert (clustered.high - clustered.low) > (unit_level.high - unit_level.low)


def test_a_clustered_derived_draw_pools_units_rather_than_averaging_cluster_means():
    """ "Pools their units", and the "varying row count" that follows. A large
    cluster contributes more rows than a small one, so a cluster drawn twice
    contributes its units twice.

    **Corrected from the brief's own two-cluster fixture** (one `A` cluster of a
    single unit, one `B` cluster of five): with only `G = 2` clusters, drawing 2
    with replacement gives just four equally-likely outcomes (`AA`, `AB`, `BA`,
    `BB`), whose means are `100.0`, `18.33…`, `18.33…`, `2.0` — a percentile
    interval read off that four-point distribution spans `[2.0, 100.0]` and
    brackets BOTH the pooled mean and the cluster-mean-average reading, so the
    fixture cannot discriminate. Measured directly before trusting it, per the
    brief's own warning.

    **Widened to 10 `A` clusters and 10 `B` clusters** (`G = 20`), each `A` a
    single unit valued 100 and each `B` five units valued `0..4` — same disjoint
    ranges and the same size asymmetry per pair, but enough clusters for the
    percentile interval to concentrate near the true pooled mean rather than
    spanning the full four-point support. Confirmed at five seeds (1 through 5)
    that the interval always brackets the pooled reading and always excludes the
    cluster-mean-average one before trusting this fixture."""
    collapsed = {f"a{a}": {"y": 100.0} for a in range(10)}
    clusters = {f"a{a}": f"A{a}" for a in range(10)}
    for b in range(10):
        for i in range(5):
            collapsed[f"b{b}_{i}"] = {"y": float(i)}
            clusters[f"b{b}_{i}"] = f"B{b}"

    def mean_y(table):
        rows = [row["y"] for row in table]
        return sum(rows) / len(rows)

    interval = percentile_of_derived_clustered(
        collapsed, clusters, mean_y, seed=1, draws=2000
    ).interval
    assert interval is not None
    # Pooled: (10*100 + 10*(0+1+2+3+4)) / (10 + 50) = 18.333…; the cluster-mean
    # reading would give (100*10 + 2.0*10)/20 = 51.0. The interval must contain
    # the first and exclude the second.
    assert interval.low <= 18.333333333333332 <= interval.high
    assert not (interval.low <= 51.0 <= interval.high)


def test_a_clustered_derived_draw_returns_its_survivor_count_even_when_degenerate():
    """The three-valued discipline `percentile_of_derived` established, inherited
    rather than reinvented: `None` and `0` are different facts."""
    collapsed = {"a1": {"y": 1.0}, "b1": {"y": 2.0}}
    clusters = {"a1": "A", "b1": "B"}
    resampled = percentile_of_derived_clustered(
        collapsed, clusters, lambda table: None, seed=1, draws=50
    )
    assert resampled.interval is None
    assert resampled.draws_used == 0


def test_a_clustered_derived_draw_over_constant_content_reports_no_interval():
    """**Fix round 1, Major 4.** `reference.md` § Statistical reporting scopes
    the zero-width gap narrowly: `percentile_over_units_clustered` "makes the
    identical content-based refusal whether or not `strata` is declared," and
    only "the plain unweighted, unstratified, unclustered `percentile_over_units`
    carries no such check." `percentile_of_derived_clustered` (task 15a) shipped
    with NO content check at all — narrower than even the documented gap —
    so 20 units of identical content in 4 clusters returned
    `Interval(5.0, 5.0)` where its recorded-column sibling,
    `percentile_over_units_clustered`, already returns `None` on the
    identical input. Verified directly before this fix: `(Interval(low=5.0,
    high=5.0, ...), 500)`.

    Fixed by taking the same content-based check `percentile_over_units_clustered`
    and `percentile_of_derived`'s own strata branch already make — every cluster
    within a stratum group carrying the identical multiset of rows — applied
    unconditionally (with or without `strata`), matching the clustered sibling's
    own "whether or not `strata` is declared" rule rather than the unclustered
    plain form's narrower one."""
    collapsed = {f"u{i}": {"y": 5.0} for i in range(20)}
    clusters = {f"u{i}": f"s{i % 4}" for i in range(20)}
    resampled = percentile_of_derived_clustered(
        collapsed,
        clusters,
        lambda table: sum(row["y"] for row in table) / len(table),
        seed=1,
        draws=500,
    )
    assert resampled.interval is None
    assert resampled.draws_used == 0


# --- H5b task 1: the guard pin, arms B and F --------------------------------
#
# Captured BEFORE any H5b task moves anything (H5b plan task 1), against
# `ee8085e`. Every literal below was produced by RUNNING `summarize_step`
# (module-level probes `p1`/`p6` in the H5b plan), not read from the plan's
# prose — the plan's own numbers are its claim, these are the measurement.


def _fixture_b_rows():
    """Fixture A: `u0`-`u3` recorded a numeric `score` alongside a bool
    `valid`; `u4`-`u5` recorded only the bool. Six units, one repeat."""
    rows = [{"unit": f"u{i}", "score": float(i), "valid": True} for i in range(4)]
    rows += [{"unit": f"u{i}", "valid": True} for i in range(4, 6)]
    return rows


def _fixture_b_wide_collapsed():
    """The wide collapsed table H5b ships: every unit admitted, `valid`
    carried. Hand-written, since no shipped caller can produce it yet —
    unlike the narrow table below, this one never moves."""
    wide = {f"u{i}": {"score": float(i), "valid": True} for i in range(4)}
    wide.update({f"u{i}": {"valid": True} for i in range(4, 6)})
    return wide


def _fixture_b_derived(collapsed):
    """What a template's `aggregate` would compute over `collapsed`, using
    row-dict access (`"score" in row`, `row.get("valid")`) rather than
    `UnitTable.score`/`UnitTable.valid` attribute access. The narrow
    (TODAY) table carries no `valid` column at all — not merely a
    non-numeric one, the column is absent from every unit — so a real
    attribute read would raise `E-STEP-COLUMN-UNKNOWN`; a real template
    hitting that is `cli.py`'s contained `W-STATS-AGGREGATE-FAILED` path,
    which is not what this direct-call pin exercises.
    """
    rows = list(collapsed.values())
    scores = [r["score"] for r in rows if "score" in r]
    return {
        "n_rows": float(len(rows)),
        "n_valid": float(sum(1 for r in rows if r.get("valid") is True)),
        "mean_score": sum(scores) / len(scores) if scores else None,
    }


def _fixture_b_n_rows(units):
    return float(len(units))


def _fixture_b_n_valid(units):
    """Row-dict `.get`, not `units.valid`: on the narrow table no row holds
    `valid` at all, and an attribute read would raise."""
    return float(sum(1 for row in units if row.get("valid") is True))


def _fixture_b_mean_score(units):
    vals = [row["score"] for row in units if "score" in row]
    return sum(vals) / len(vals) if vals else None


def test_a_bool_only_column_widens_exactly_seven_moving_keys():
    """H5b's guard pin, arm B (H5b plan task 1, step 2). **Sole authorized
    editor: task 4**, flipping exactly the seven asserted TODAY values to
    their AFTER counterpart and nothing else in this test. Task 5 is not an
    editor here: this fixture has no column that disagrees across repeats
    (every unit's `valid` is `True` in its one and only repeat), so the
    disagreement disclosure this slice adds cannot fire on it — a task-5
    edit to this test would be a finding, not a fixture repair.

    Drives `summarize_step` twice over the same `derived`/`resample` map.
    The narrow `collapsed` comes from a LIVE `collapse_repeats` call on
    `_result`-built executions; the wide (AFTER) `collapsed` is hand-written
    and never moves. **After task 4, the two are identical** — H5b's whole
    point is that the live collapse now admits every unit and carries every
    recorded value, so "narrow" no longer describes anything the live call
    can still produce. The seven literals below are flipped to their AFTER
    value because the TODAY (pre-H5b) shape is no longer reachable through
    `collapse_repeats` at all — this is the moving-run pin itself passing
    through its own moved state, not a second measurement.

    `mean_score.value == 1.5` on BOTH tables is the load-bearing assertion:
    a fixture in which every number moves cannot tell "the table widened"
    from "the metric changed". `mean_score.resample_draws` moving
    `2000 -> 1998` is this fixture's own number at `seed=7, draws=2000` —
    not a constant, and not reused for any other arm's seed.
    """
    result = _result("", _fixture_b_rows())
    narrow = collapse_repeats([result], "analyze", 0)
    wide = _fixture_b_wide_collapsed()
    assert narrow == wide, (
        "H5b task 4: the live collapse now admits u4/u5 and carries `valid` "
        "for every unit, so it equals the hand-written AFTER table exactly "
        "— the narrow (pre-H5b) shape this arm used to produce is gone"
    )

    counts = {"resolved": 6.0, "completed": 6.0, "ineligible": 0.0, "failed": 0.0}
    resample = {
        "n_rows": _fixture_b_n_rows,
        "n_valid": _fixture_b_n_valid,
        "mean_score": _fixture_b_mean_score,
    }

    today = summarize_step(
        narrow, counts, derived=_fixture_b_derived(narrow), seed=7, resample=resample, draws=2000
    )
    after = summarize_step(
        wide, counts, derived=_fixture_b_derived(wide), seed=7, resample=resample, draws=2000
    )

    # The seven moving keys, enumerated — never counted. Flipped from their
    # pre-H5b TODAY values (0.0/[0.0, 0.0]/4.0/[4.0, 4.0]/4/[0.5, 2.5]/2000)
    # to the AFTER values `narrow` now actually produces.
    assert today["n_valid"]["value"] == 6.0
    assert after["n_valid"]["value"] == 6.0
    assert today["n_valid"]["ci95"] == [6.0, 6.0]
    assert after["n_valid"]["ci95"] == [6.0, 6.0]
    assert today["n_rows"]["value"] == 6.0
    assert after["n_rows"]["value"] == 6.0
    assert today["n_rows"]["ci95"] == [6.0, 6.0]
    assert after["n_rows"]["ci95"] == [6.0, 6.0]
    assert today["mean_score"]["n"]["completed"] == 6
    assert after["mean_score"]["n"]["completed"] == 6
    assert today["mean_score"]["ci95"] == [0.3333333333333333, 2.5]
    assert after["mean_score"]["ci95"] == [0.3333333333333333, 2.5]
    assert today["mean_score"]["resample_draws"] == 1998
    assert after["mean_score"]["resample_draws"] == 1998

    # Unmoved, and load-bearing.
    assert today["mean_score"]["value"] == 1.5
    assert after["mean_score"]["value"] == 1.5
    assert today["score"]["value"] == 1.5
    assert after["score"]["value"] == 1.5
    assert today["score"]["n"]["completed"] == 4
    assert after["score"]["n"]["completed"] == 4
    assert today["score"]["ci95"] == [-0.5542602567605206, 3.5542602567605206]
    assert after["score"]["ci95"] == [-0.5542602567605206, 3.5542602567605206]
    assert today["score"]["method"] == "t_over_units"
    assert after["score"]["method"] == "t_over_units"

    # The projection: `valid` is a bool column, and admitting the units it
    # lives on must not also publish a metric block for it.
    assert "valid" not in today
    assert "valid" not in after


def _fixture_f_labels():
    return {f"u{i}": ("a" if i % 2 == 0 else "b") for i in range(6)}


def _fixture_f_mean_score_null(units, labels):
    """A mean-of-group-a-minus-mean-of-group-b statistic over the
    RELABELLED mapping `permutation_of_derived` hands it as its second
    argument — a one-argument closure ignoring `labels` would recompute the
    same grouping on every draw and return `None` for every key
    (`permutation_of_derived`'s own "not varied" rule), which is why the
    function takes `compute(table, labels)` rather than `resample`'s
    one-argument shape."""
    a = [row["score"] for row in units if "score" in row and labels.get(row["unit"]) == "a"]
    b = [row["score"] for row in units if "score" in row and labels.get(row["unit"]) == "b"]
    if not a or not b:
        return None
    return sum(a) / len(a) - sum(b) / len(b)


def test_a_derived_metrics_permutation_p_value_widens_but_a_recorded_columns_never_gets_one():
    """H5b's guard pin, arm F (H5b plan task 1, step 3b; Corrections 16).
    **Sole authorized editor: task 4.** Fixture A's two tables again, this
    time with a `null_test` declared and a `null_fn` per derived key.

    Why this is a separate arm rather than more keys on arm B: arm B's
    fixture declares no `null_test`, and adding one would change the block
    shape every one of arm B's seven literals was captured from.

    The asymmetry stated and which half was reasoned: a RECORDED column
    (`score`) gets no `p_value` from `summarize_step` at all — the write is
    in the derived branch only (confirmed:
    `grep -n 'p_value' src/publishable/stats.py` over the recorded-column
    loop's own range has no hit, only the derived branch below it does).
    A CONTRAST's p-value comes from `permutation_over_contrast` over
    `of_values`/`against_values` in the unpaired recorded-column arm, which
    a later task narrows rather than widens — that half was read, not run,
    here.
    """
    narrow = {f"u{i}": {"score": float(i)} for i in range(4)}
    wide = {f"u{i}": {"score": float(i), "valid": True} for i in range(4)}
    wide.update({f"u{i}": {"valid": True} for i in range(4, 6)})
    counts = {"resolved": 6.0, "completed": 6.0, "ineligible": 0.0, "failed": 0.0}
    null_test = {"method": "permutation", "n": 500, "shuffle": "grp", "level": "rows"}
    labels = _fixture_f_labels()

    def derived_for(collapsed):
        rows = list(collapsed.values())
        scores = [r["score"] for r in rows if "score" in r]
        return {"mean_score": sum(scores) / len(scores) if scores else None}

    today = summarize_step(
        narrow,
        counts,
        derived=derived_for(narrow),
        seed=7,
        null_test=null_test,
        labels=labels,
        null_fns={"mean_score": _fixture_f_mean_score_null},
    )
    after = summarize_step(
        wide,
        counts,
        derived=derived_for(wide),
        seed=7,
        null_test=null_test,
        labels=labels,
        null_fns={"mean_score": _fixture_f_mean_score_null},
    )

    assert today["mean_score"]["p_value"] == 0.846307385229541
    assert today["mean_score"]["null_draws"] == 500
    assert after["mean_score"]["p_value"] == 0.812375249500998
    assert after["mean_score"]["null_draws"] == 500

    # Must not move: a recorded column has no `p_value` at all, in either table.
    assert "p_value" not in today["score"]
    assert "null_draws" not in today["score"]
    assert "p_value" not in after["score"]
    assert "null_draws" not in after["score"]


# --- H5b task 4: Fixture E (the collision, from the collapse's own output), ---
# --- Fixture M (`repeat_spread` under the widened `keys`) --------------------


def test_fixture_e_a_collision_from_a_real_collapse_output_is_refused():
    """H5b task 4, Fixture E, first arm. `collapse_repeats` over executions
    recording `{"score": float(i), "r": True}` — a production caller's own
    shape, not a hand-built `collapsed` dict — fed straight to
    `summarize_step(..., derived={"r": 1.0})`. `r` is dropped from `out` for
    being non-numeric (every unit's `r` is `True`, no disagreement), and the
    collision check must still see it: task 10 owns the shipped test's
    fixture replacement and its § Errors assertion, this is the pin that a
    collapse a real caller can produce reaches the same refusal."""
    rows = [{"unit": f"u{i}", "score": float(i), "r": True} for i in range(5)]
    result = _result("", rows)
    collapsed = collapse_repeats([result], "analyze", 0)
    assert collapsed == {f"u{i}": {"score": float(i), "r": True} for i in range(5)}
    with pytest.raises(ContractError) as exc:
        summarize_step(collapsed, {"completed": 5}, derived={"r": 1.0}, seed=7)
    assert exc.value.code == "E-STEP-KEY-COLLISION"


def test_fixture_e_a_disagreeing_collided_column_still_refuses():
    """H5b task 4, Fixture E, second arm — the one that pins Decision 2's
    `None` choice. Two repeats disagree on `r` for every unit, so its
    collapsed cell is `None` (not dropped, not omitted); the collision must
    still fire, because `None` keeps the column visible to the check that
    reads `collapsed`'s own keys rather than `out`'s."""
    results = [
        _result("seed1", [{"unit": f"u{i}", "score": float(i), "r": True} for i in range(5)]),
        _result("seed2", [{"unit": f"u{i}", "score": float(i), "r": False} for i in range(5)]),
    ]
    collapsed = collapse_repeats(results, "analyze", 0)
    assert all(collapsed[f"u{i}"]["r"] is None for i in range(5))
    with pytest.raises(ContractError) as exc:
        summarize_step(collapsed, {"completed": 5}, derived={"r": 1.0}, seed=7)
    assert exc.value.code == "E-STEP-KEY-COLLISION"


def test_fixture_m_repeat_spread_unmoved_under_the_widened_keys():
    """H5b task 4, Fixture M. `cli.py` passes `keys=set(collapsed)`, which
    widens 4 -> 6 in this shape while `score`'s own column carries only 4.
    The gate that holds is `repeat_spread`'s own per-member `_is_numeric`
    filter: admitting `u4`/`u5` (bool-only) into `keys` gives their rows no
    `score` value to contribute, so neither `std` nor `n` moves. A fixture
    whose repeats record identical scores could not see whether this held —
    `std: 0.0` agrees with the bug either way — so this one's two seeds
    record `score` 2.0 apart.
    """
    levels = resolve_repeats(cfg([{"kind": "seed", "n": 2}]), "d")
    results = [
        _repeat_result(
            "analyze",
            "seed87",
            0,
            {
                "u0": {"score": 1.0},
                "u1": {"score": 1.0},
                "u2": {"score": 1.0},
                "u3": {"score": 1.0},
            },
        ),
        _repeat_result(
            "analyze",
            "seed93",
            0,
            {
                "u0": {"score": 3.0},
                "u1": {"score": 3.0},
                "u2": {"score": 3.0},
                "u3": {"score": 3.0},
            },
        ),
        _repeat_result("analyze", "seed87", 0, {"u4": {"flag": True}, "u5": {"flag": True}}),
        _repeat_result("analyze", "seed93", 0, {"u4": {"flag": True}, "u5": {"flag": True}}),
    ]
    narrow_keys = {"u0", "u1", "u2", "u3"}
    wide_keys = {"u0", "u1", "u2", "u3", "u4", "u5"}
    narrow_spread = repeat_spread(results, "analyze", 0, levels, "score", keys=narrow_keys)
    wide_spread = repeat_spread(results, "analyze", 0, levels, "score", keys=wide_keys)
    assert narrow_spread == [{"std": 1.0, "n": 2, "kind": "seed"}]
    assert wide_spread == narrow_spread


# --- H5b task 5: Fixture D (a recorded None vs. a collapsed disagreement) ---
# --- and Fixture L (the mixed column across repeats) ------------------------


def test_fixture_d_arm_1_a_recorded_none_that_agrees_draws_no_warning():
    """H5b task 5, Fixture D, arm 1 — the control Decision 3 rests on. Two
    repeats BOTH recording `{"valid": None}`: the cell is `None` (agreement,
    not disagreement — `_repeats_disagree` compares `(is_numeric, value)`
    pairwise and both are `(False, None)`), and `repeats_disagreeing` must
    report nothing for it."""
    results = [
        _result("seed17", [{"unit": "p0", "valid": None}]),
        _result("seed42", [{"unit": "p0", "valid": None}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed["p0"]["valid"] is None
    assert repeats_disagreeing(results, "analyze", condition_index=0) == {}


def test_fixture_d_arm_2_a_genuine_disagreement_bit_identical_to_arm_1s_cell():
    """H5b task 5, Fixture D, arm 2 — the one Decision 3 is actually about.
    One repeat recorded `{"valid": None}`, another `{"valid": True}`: a
    genuine disagreement whose collapsed cell is `None`, bit-identical to
    arm 1's. The two arms differ ONLY in the rows, never in the collapsed
    value, so a rule answering from the cell (`value is None`) would give one
    answer to both and must fail one of them — this one must warn."""
    results = [
        _result("seed17", [{"unit": "p0", "valid": None}]),
        _result("seed42", [{"unit": "p0", "valid": True}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed["p0"]["valid"] is None
    assert repeats_disagreeing(results, "analyze", condition_index=0) == {"valid": 1}


def test_fixture_l_a_mixed_numeric_string_column_keeps_its_mean_and_warns():
    """H5b task 5, Fixture L (§ Corrections 5). One unit, two repeats,
    recording `{"score": 4.0}` and `{"score": "n/a"}`. This is the fixture
    that separates the prescribed rule from the plausible wrong one: under
    *mixed -> `None`*, the cell would be `None` and — measured at `ee8085e`
    (probe `p3`) — one `None` cell costs the WHOLE column its metric block
    for every unit, a published column silently deleted that no decision
    argues for. Under the prescribed rule the cell is unmoved (today's
    arithmetic: the mean of the numeric subset) and the disclosure is the
    warning alone.
    """
    results = [
        _result("seed17", [{"unit": "p0", "score": 4.0}]),
        _result("seed42", [{"unit": "p0", "score": "n/a"}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed["p0"]["score"] == 4.0
    summarized = summarize_step(collapsed, {"completed": 1}, seed=7)
    assert "score" in summarized  # the column KEEPS its metric block
    assert repeats_disagreeing(results, "analyze", condition_index=0) == {"score": 1}


def test_fixture_l_arm_2_both_repeats_numeric_draws_no_warning():
    """H5b task 5, Fixture L, the can-fail control: the same column with BOTH
    repeats numeric collapses to their mean and draws no warning at all —
    proving the warning above is about the mix, not about the column."""
    results = [
        _result("seed17", [{"unit": "p0", "score": 4.0}]),
        _result("seed42", [{"unit": "p0", "score": 6.0}]),
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert collapsed["p0"]["score"] == 5.0
    assert repeats_disagreeing(results, "analyze", condition_index=0) == {}


# --- H5b task 6: Fixture I (where the projection sits), and the Controller ---
# --- ruling 1 fix (a mixed numeric/None column across UNITS keeps a block) --


def test_fixture_i_a_derived_metric_reading_the_bool_column_stays_inside_its_ci():
    """H5b task 6, Fixture I. `summarize_step` over Fixture A's wide table
    (six units, `u0`-`u3` carrying `score`, all six carrying bool `valid`)
    with a derived metric that READS the bool column (`n_valid`, counting
    `row.get("valid") is True`).

    The load-bearing claim: `summarize_step` passes the `collapsed` it
    received straight to `percentile_of_derived`, which rebuilds each draw's
    table from WHOLE rows. Stripping the column at the function's INPUT would
    give the 2000 draws a narrower table (four rows, `score` only) than the
    single unresampled `aggregate` call in `cli.py` (six rows, `valid`
    included) — measured on this fixture: `(6.0, 6.0)` against the full table
    and `(0.0, 0.0)` against a stripped one, a point estimate outside its own
    interval. Projecting only at the OUTPUT (this function's own column loop,
    which never touches `collapsed` itself) is what keeps the derived branch's
    table whole.
    """
    wide = _fixture_b_wide_collapsed()
    counts = {"resolved": 6.0, "completed": 6.0, "ineligible": 0.0, "failed": 0.0}

    def n_valid(units):
        return float(sum(1 for row in units if row.get("valid") is True))

    out = summarize_step(
        wide, counts, derived={"n_valid": 6.0}, seed=7, resample={"n_valid": n_valid}, draws=2000
    )
    assert out["n_valid"]["value"] == 6.0
    assert out["n_valid"]["ci95"] == [6.0, 6.0]
    assert out["n_valid"]["ci95"][0] <= out["n_valid"]["value"] <= out["n_valid"]["ci95"][1]
    assert out["n_valid"]["resample_draws"] == 2000
    assert "valid" not in out  # the bool recorded column itself earns no block


def test_ruling_1_a_column_numeric_for_some_units_and_none_for_others_keeps_a_block():
    """Controller ruling 1 (2026-08-22), amendment row 2 — the mixed column
    across UNITS (not across a single unit's repeats, which is task 4/5's
    Decision 5/6 territory). `u0` carries a number, `u1` carries `None` —
    reachable the moment task 4 lets `_across_repeats` return `None` for a
    unit whose repeats disagreed on a non-numeric column, or simply because a
    unit recorded `None` directly (`_check_column_types` never refuses `None`
    beside a `float`, measured against `artifacts._check_column_types`).

    This is a real regression task 4 introduced and task 6 closes: BEFORE
    task 4, `_gather_repeats`'s old filter dropped a non-numeric/`None` value
    at the walk, so `u1` never carried `score` at all and `summarize_step`'s
    column loop already published a block over `u0` alone, `n.completed: 1`
    — the ordinary ragged-column case its own docstring already describes.
    AFTER task 4 and before this fix, `u1`'s `score` is `None` and PRESENT,
    so the old `not all(_is_numeric(v) for v in raw)` gate dropped the WHOLE
    column — the exact silent-deletion shape ruling 1 exists to end. The fix
    filters `carried` to its numeric subset rather than gating all-or-nothing,
    which is what restores the pre-task-4 behaviour and generalizes it: `n`
    reports the CONTRIBUTING count, not `counts`' condition-wide figure.
    """
    collapsed = {"u0": {"score": 4.0}, "u1": {"score": None}}
    out = summarize_step(collapsed, {"completed": 2}, seed=7)
    assert out["score"]["value"] == 4.0
    assert out["score"]["n"]["completed"] == 1


def test_ruling_1_all_non_numeric_still_earns_no_block_at_all():
    """Ruling 1's row 1 (unchanged): a column non-numeric for EVERY unit that
    carries it earns no block whatsoever — there is no mean of strings, and
    this is the case the pre-ruling all-or-nothing wording was correct about."""
    collapsed = {"u0": {"valid": True}, "u1": {"valid": True}}
    out = summarize_step(collapsed, {"completed": 2}, seed=7)
    assert out == {}


# --- H5b batch 2 fix round: the two unpinned behaviours (M5, M6) ------------


def test_a_bool_in_one_repeat_and_a_float_in_another_disagrees_in_both_orders():
    """H5b batch 2 fix round, Major M5 (Controller ruling 8). `_repeats_disagree`
    compares `(is-it-a-number, the value)` rather than the value alone, and
    nothing failed when the tuple was replaced by `any(v != first ...)` — the
    review ran that mutation against the whole suite and read it back
    bit-identical.

    `True == 1.0` in Python, so the bare comparison reports agreement and the
    disagreement goes unreported. **The collapsed cell is not what
    discriminates**: `_across_repeats` returns `1.0` under both orders and
    under both readings (measured, both directions), so an assertion on the
    cell would be a mutation whose two branches cannot differ. The assertion
    is on `repeats_disagreeing`, which is the only thing the tuple changes.

    Both orders, because the bare comparison is against `values[0]` and a
    fixture holding one order proves nothing about the other — and because the
    docstring's deleted claim was specifically about order.
    """
    bool_first = [
        _result("seed17", [{"unit": "p0", "flag": True}]),
        _result("seed42", [{"unit": "p0", "flag": 1.0}]),
    ]
    float_first = [
        _result("seed17", [{"unit": "p0", "flag": 1.0}]),
        _result("seed42", [{"unit": "p0", "flag": True}]),
    ]
    assert repeats_disagreeing(bool_first, "analyze", condition_index=0) == {"flag": 1}
    assert repeats_disagreeing(float_first, "analyze", condition_index=0) == {"flag": 1}
    # The cell, measured under both orders: unmoved, and so not a discriminator.
    assert collapse_repeats(bool_first, "analyze", condition_index=0)["p0"]["flag"] == 1.0
    assert collapse_repeats(float_first, "analyze", condition_index=0)["p0"]["flag"] == 1.0


def test_a_unit_that_recorded_no_column_at_all_is_still_admitted_as_a_row():
    """H5b batch 2 fix round, Major M6 (Controller ruling 8). `io.record(key,
    {})` settles a unit and records nothing, so its row is `{"unit": key}` and
    its collapsed entry is `{}`. `_gather_repeats` admits it — the comment
    added by task 4 says so and calls it measured — and adding `if cols` to
    `collapse_repeats`'s return comprehension left the entire suite unchanged.

    The published consequence is a table one row longer, which is what the
    end-to-end half of this pin
    (`test_an_empty_record_is_a_row_the_template_counts` in
    `tests/test_cli.py`) reads out of `run.yaml`. This half pins the
    membership itself, at the function that decides it: `p2` is present and
    empty, not absent, and `len` counts it.
    """
    results = [
        _repeat_result(
            "analyze", "seed17", 0, {"p0": {"score": 1.0}, "p1": {"score": 3.0}, "p2": {}}
        )
    ]
    collapsed = collapse_repeats(results, "analyze", condition_index=0)
    assert "p2" in collapsed
    assert collapsed["p2"] == {}
    assert len(collapsed) == 3
    # And it earns the unit no metric block of its own: the column loop's
    # numeric subset is what publishes, and `p2` contributed nothing to it.
    out = summarize_step(collapsed, {"completed": 3}, seed=7)
    assert out["score"]["n"]["completed"] == 2


# --- H3c-3 task 12: the four `stats.py` readers of a per-cell `fold_members` --


def _h3c3_treatment_results(members, arms, step="analyze"):
    """One execution per fold label, recording the `treatment` units THAT fold
    was handed — the run that actually happened under `members`.

    Built from `members` rather than from three literals, so the fixture cannot
    quietly stop describing the draw it came from.
    """
    return [
        _repeat_result(
            step, label, 0, {key: {"s": 1.0} for key in sorted(keys & arms["treatment"])}
        )
        for label, keys in sorted(members.items())
    ]


def test_h3c3_handed_to_reads_the_flat_mapping_and_covers_every_fold():
    """Reader 1 of 7. `handed_to` hands each `treatment` unit **exactly one**
    label, and the three units between them cover all three folds — the
    property the per-cell draw bought, read through the reader rather than off
    the mapping.

    Under the whole-roster mapping the same three units cover only `fold02` and
    `fold03`: `fold01` was handed no `treatment` unit at all, so nothing this
    reader can return names it. That is the discriminating half — the first
    assertion alone passes under either draw.
    """
    from publishable.stats import handed_to

    _, per_cell, whole, arms = h3c3_per_cell_fixture()
    labels = sorted(per_cell)
    for key in sorted(arms["treatment"]):
        assert len(handed_to(key, labels, per_cell)) == 1
    assert {lb for key in arms["treatment"] for lb in handed_to(key, labels, per_cell)} == set(
        labels
    )
    assert {lb for key in arms["treatment"] for lb in handed_to(key, labels, whole)} == {
        "fold02",
        "fold03",
    }


def test_h3c3_gather_repeats_admits_every_unit_of_the_thin_arm():
    """Reader 2 of 7. `_gather_repeats` walks the same flat mapping and admits
    all three `treatment` units, one value each.

    Read against the **whole-roster** mapping the identical executions admit
    **one** unit: a unit recorded in the fold it was drawn into per cell is
    handed a different fold by the mapping this slice replaced, and a unit with
    no value in the label it was handed is dropped. Three against one is the
    assertion; a test that only asserted the three would pass under both.
    """
    from publishable.stats import _gather_repeats

    _, per_cell, whole, arms = h3c3_per_cell_fixture()
    results = _h3c3_treatment_results(per_cell, arms)
    assert sorted(_gather_repeats(results, "analyze", 0, per_cell)) == ["t0", "t1", "t2"]
    assert sorted(_gather_repeats(results, "analyze", 0, whole)) == ["t2"]


def test_h3c3_collapse_repeats_builds_one_row_per_unit_of_the_thin_arm():
    """Reader 3 of 7 (H5b's split, one half). The collapsed table is one row per
    `treatment` unit, each averaging the single value its own fold recorded —
    and one row, not three, under the whole-roster mapping.
    """
    from publishable.stats import collapse_repeats

    _, per_cell, whole, arms = h3c3_per_cell_fixture()
    results = _h3c3_treatment_results(per_cell, arms)
    table = collapse_repeats(results, "analyze", 0, per_cell)
    assert table == {"t0": {"s": 1.0}, "t1": {"s": 1.0}, "t2": {"s": 1.0}}
    assert sorted(collapse_repeats(results, "analyze", 0, whole)) == ["t2"]


def test_h3c3_repeats_disagreeing_counts_the_units_the_flat_mapping_hands():
    """Reader 4 of 7 (H5b's other half). Two seeds inside each fold, a
    non-numeric column, and **two** of the three `treatment` units disagreeing
    about it — the third recording `a` twice.

    Under the whole-roster mapping only that agreeing unit survives the
    membership walk, so the same executions report **nothing** disagreeing.
    An agreeing unit is what makes the two answers differ rather than merely
    shrink, and it is why this fixture is not the one the three tests above
    share.
    """
    from publishable.stats import repeats_disagreeing

    _, per_cell, whole, arms = h3c3_per_cell_fixture()
    agreeing = sorted(per_cell["fold03"] & arms["treatment"])[0]
    results = []
    for label, keys in sorted(per_cell.items()):
        for seed, tag in (("seed01", "a"), ("seed02", "b")):
            results.append(
                _repeat_result(
                    "analyze",
                    f"{label}_{seed}",
                    0,
                    {
                        key: {"tag": "a" if key == agreeing else tag}
                        for key in sorted(keys & arms["treatment"])
                    },
                )
            )
    assert repeats_disagreeing(results, "analyze", 0, per_cell) == {"tag": 2}
    assert repeats_disagreeing(results, "analyze", 0, whole) == {}

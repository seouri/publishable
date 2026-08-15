import itertools
import math
import random

import pytest

from publishable.errors import ContractError
from publishable.replication import resolve_repeats
from publishable.stats import (
    Interval,
    PairedResample,
    UnitTable,
    _percentile_ranks,
    _t_critical,
    cohens_dz,
    collapse_repeats,
    handed_to,
    interval_at,
    kish_effective_n,
    mean_of,
    min_honest_draws,
    paired_delta_of_derived,
    paired_keys,
    paired_percentile_of_derived,
    paired_t_over_units,
    percentile_of_derived,
    percentile_over_units,
    percentile_over_units_clustered,
    repeat_spread,
    resample_seed,
    summarize_step,
    t_over_units,
    t_over_units_clustered,
    weighted_t_over_units,
    weighted_t_over_units_clustered,
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


def test_a_clustered_derived_metric_is_refused_at_this_surface():
    """`E-DATA-CLUSTER-DERIVED`. The clustered draw for a *recomputed* metric —
    each replicate drawing `G` clusters and pooling their units — does not exist,
    and `percentile_of_derived` draws units, so the interval would be narrower than
    the design supports beside recorded columns that are cluster-robust.

    Raised here rather than reported by `validate` because whether a template's
    `aggregate` returns anything is not knowable from a declaration: it is user code
    core never inspects, and one that overrides `aggregate` may still return `{}`
    for a given config. `tests/test_cli.py` owns the end-to-end containment; this
    owns the guard's exact shape."""
    collapsed = {f"u{i}": {"pred": float(i)} for i in range(20)}
    clusters = {f"u{i}": f"s{i % 4}" for i in range(20)}
    with pytest.raises(ContractError) as exc:
        summarize_step(
            collapsed,
            {"completed": 20},
            derived={"total": 190.0},
            seed=7,
            resample={"total": lambda units: sum(units.pred)},
            clusters=clusters,
        )
    assert exc.value.code == "E-DATA-CLUSTER-DERIVED"
    # Raised before a single derived key is written, so `cli` drops the whole
    # mapping rather than leaving a record carrying part of it.
    assert "total" in str(exc.value)


@pytest.mark.parametrize(
    "narrowed",
    [
        pytest.param({"seed": None}, id="no-seed"),
        pytest.param({"resample": None}, id="no-resample-map"),
        pytest.param({"resample": {"total": None}}, id="no-callable-for-this-key"),
    ],
)
def test_a_clustered_derived_metric_that_would_not_be_drawn_is_not_refused(narrowed):
    """The under-firing controls, and the reason the guard reads what would actually
    be *drawn* rather than the `cluster_by` declaration. With no seed or no callable
    no interval is built at all, so there is no too-narrow interval to prevent and
    the point estimate publishes as it always did.

    None of these three is reachable through `cli` today — it builds a callable for
    every derived key and only when `derived` is truthy — so the narrowing is
    defensive. Pinned here because a mutation removing it is otherwise invisible:
    measured, not assumed.

    The recorded column beside it stays cluster-robust throughout, which is what
    says the clustering is still in force and the guard simply does not apply."""
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

    interval, draws_used = percentile_of_derived(
        collapsed, resample_fn_for_a_string_metric, seed=7, draws=20
    )
    assert interval is None
    assert draws_used == 0


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
        weighted_t_over_units_clustered(
            values, keys, dict.fromkeys(keys, "c"), [1] * len(values)
        )
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
        summarize_step(
            _WEIGHTED_COLLAPSED, _WEIGHTED_COUNTS, weights={**_WEIGHTS, "u4": "site-3"}
        )
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


def test_percentile_over_units_refuses_a_pool_below_the_honest_floor():
    """The gap `spec-defects.md` recorded: `percentile_of_derived` got a survivor
    floor in S4a and its sibling did not, so this one returns a zero-width
    interval at two draws. Unreachable today (`statistics.resample` is refused),
    which is exactly why it must be closed before the slice that reaches it."""
    values = [float(i) for i in range(60)]
    assert percentile_over_units(values, seed=7, draws=10) is None
    assert percentile_over_units(values, seed=7, draws=2000) is not None


def test_an_unweighted_percentile_interval_is_untouched_to_the_last_digit():
    """The regression the weighted path must not move. Literals captured from the
    implementation before `weights` existed: every other test in this section
    compares one call to another, so a drift that moved both would pass them
    all."""
    values = [float(i) for i in range(50)]
    assert percentile_over_units(values, seed=7) == Interval(
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
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7)
    assert result is not None
    assert result.low == 1.0  # a draw-weighted implementation cannot reach here
    assert result.high > 50.0  # ...while the statistic is still weighted
    # The control that must report: the same pool drawn the same way with the
    # weights dropped is an ordinary bootstrap of a mean near 5.7, so the high
    # bound above is the weighting and not the data's own spread.
    unweighted = percentile_over_units(values, draws=2000, seed=7)
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
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7)
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
    assert result == percentile_over_units(
        [values[i] for i in order],
        weights=[weights[i] for i in order],
        draws=2000,
        seed=7,
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
_POOL_MEMBERSHIP = dict(
    zip(_POOL_KEYS, ["A", "B", "B", "C", "C", "C", "D", "D"], strict=True)
)
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
        _pooled(combo, weighted)
        for combo in itertools.combinations_with_replacement("ABCD", 4)
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
    )
    assert got is not None
    assert got.method == "percentile_over_units_clustered"
    assert got.low == _pooled(("A", "A", "A", "D"))  # 36/5
    assert got.high == _pooled(("B", "C", "C", "C"))  # 157/11
    assert got.low in _achievable() and got.high in _achievable()
    plain = percentile_over_units(_POOL_VALUES, seed=7)
    assert plain is not None
    assert plain.low == 5.25 and plain.high == 19.0
    assert plain.low not in _achievable() and plain.high not in _achievable()


def test_a_drawn_cluster_pools_its_units_rather_than_contributing_its_mean():
    """"Core draws whole clusters with replacement, so a resampled table has a
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
    )
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
    )
    assert got is not None
    repaired: dict[str, list[tuple[float, float]]] = {}
    for value, label in zip(
        sorted(_POOL_VALUES), sorted(_POOL_MEMBERSHIP.values()), strict=True
    ):
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
    got = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    )
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
        )
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
    got = percentile_over_units_clustered(_POOL_VALUES, _POOL_KEYS, membership, seed=7)
    assert got is not None
    assert got.high > got.low


@pytest.mark.parametrize("values", [[], [1.0]])
def test_the_clustered_percentile_needs_two_values(values):
    """`percentile_over_units`' own floor, kept in front of the cluster one so the
    two constructions refuse the same degenerate inputs."""
    keys = [f"u{i}" for i in range(len(values))]
    assert (
        percentile_over_units_clustered(values, keys, dict.fromkeys(keys, "c"), seed=7)
        is None
    )


def test_the_clustered_percentile_refuses_a_draw_count_below_the_honest_floor():
    """Orthogonal to the cluster floor: this one is about how many replicates the
    ranks are read off, not how many things each replicate draws."""
    assert (
        percentile_over_units_clustered(
            _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, draws=10
        )
        is None
    )
    assert (
        percentile_over_units_clustered(
            _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7, draws=2000
        )
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
    got = percentile_over_units_clustered(values, keys, {k: k for k in keys}, seed=7)
    assert got is not None
    assert (got.low, got.high) == (20.4, 28.54)
    plain = percentile_over_units(values, seed=7)
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
    )
    assert got is not None
    assert got.method == "percentile_over_units_clustered"
    assert got.low == _pooled(("A", "A", "A", "D"), weighted=True)
    assert got.high == _pooled(("C", "C", "C", "D"), weighted=True)
    assert got.low in _achievable(True) and got.high in _achievable(True)
    unweighted = percentile_over_units_clustered(
        _POOL_VALUES, _POOL_KEYS, _POOL_MEMBERSHIP, seed=7
    )
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
    a, _ = percentile_of_derived(of, _mean_m, seed=7)
    b, _ = percentile_of_derived(against, _mean_m, seed=7)
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
    assert paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=7) == \
        paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=7)
    assert paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=7) != \
        paired_percentile_of_derived(of, against, k, _mean_m, _mean_m, seed=99)


def test_below_the_survivor_floor_there_is_no_interval_paired():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    result = paired_percentile_of_derived(
        of, against, sorted(of), lambda t: None, lambda t: None, seed=7, draws=200)
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
        of, against, sorted(of), always_raises, always_raises, seed=7, draws=20)
    assert result.interval is None
    assert result.draws_used == 0


def test_a_nan_compute_is_treated_as_degenerate_paired():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}

    def always_nan(units):
        return float("nan")

    result = paired_percentile_of_derived(
        of, against, sorted(of), always_nan, always_nan, seed=7, draws=20)
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
        of, against, sorted(of), flaky_against_only, flaky_against_only, seed=7, draws=draws)
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
        of, against, sorted(of), flaky_against_only, flaky_against_only, seed=7, draws=draws)
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
    rival = t_over_units_clustered(
        [1.0, 1.0, 2.0, 1.0], ["u1", "u2", "u3", "u4"], _CLUSTERS
    )
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
    stratified = percentile_over_units(values, seed=7, draws=2000, strata=strata)
    plain = percentile_over_units(values, seed=7, draws=2000)
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
    b = percentile_over_units(
        values, seed=3, draws=2000, strata=[renamed[s] for s in strata]
    )
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
    got = percentile_over_units(values, seed=9, draws=2000, weights=weights, strata=strata)
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
    got = percentile_over_units(values, seed=13, draws=2000, strata=strata)
    plain = percentile_over_units(values, seed=13, draws=2000)
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
    got = percentile_over_units(values, seed=17, draws=2000, strata=strata)
    plain = percentile_over_units(values, seed=17, draws=2000)
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
    assert percentile_over_units(values, seed=23, draws=2000, strata=strata) is None


def test_every_unit_its_own_stratum_gives_no_interval_at_all():
    """Every unit its own singleton stratum: each draw reproduces every value
    exactly once, so the resample has no freedom left anywhere. This is the
    singleton special case of the constant-stratum refusal above, not a
    zero-width point to report."""
    values = [1.0, 2.0, 3.0, 4.0]
    strata = ["a", "b", "c", "d"]
    got = percentile_over_units(values, seed=19, draws=2000, strata=strata)
    assert got is None

# Task 5 — `cli.py` builds the member

**Status: complete.** `compare: {to: constant}` now returns a real verdict off a real
`ci95_corrected` in three of Decision 1's four rows.

## What was built

One `correction.Member` per condition metric, built in `command_run`'s per-condition /
per-step loop immediately after `pools_by_key[(cond.index, step_name)] = step_pools` — the
site task 4 left, and its first consumer. `where` is `const:<index>`, the exact string
`hypotheses.resolve` gives a `to: constant` observation (`cond:` / `contrast:` are the two
it must not collide with, and `hypotheses.evaluate` looks members up by
`(where, step, metric)`).

The members are accumulated in a **separate** `condition_members` list and reach
`evaluate_hypotheses` only, concatenated onto `comparison_members` with the declaration
indices continuing rather than restarting. They are deliberately kept out of
`corrected_fields(comparison_members, ...)`: that is the sweep family, whose size is
`comparisons × metrics` over its own member list, and a condition's own metric there would
widen the product and move every corrected bound in the run. On the hypothesis side
`evaluate`'s `size` is `len(counted)` over the DECLARED hypotheses, so passing these along
changes no family size anywhere. `_is_counted` and `family_shape` are untouched.

## Decision 1's rows

| Row | Built? | Evidence the member carries |
|---|---|---|
| Recorded column, no `resample` | **yes** | the per-unit values as `diffs`, plus `weights` under a declared `weight_by` or `clusters` under a declared `cluster_by` |
| Recorded column, declared `resample` | **yes** | the `pool` task 4 carried out of `summarize_step` |
| Derived (`aggregate`), resampled | **yes** | the same `pool`, from `percentile_of_derived`[`_clustered`] |
| Derived, no interval | no | nothing — there is no raw bound to correct |

The branch is decided by **which construction the raw interval came from**, per
`_corrected_bounds`' own words ("what decides the construction is which field the member
carries"), read off the two facts `summarize_step`'s column branch decides on:

- a pool came back → the raw interval is a percentile off those very draws → carry the
  POOL, and `interval_at` reads a second rank pair off it.
- no pool, and the key has a numeric per-unit column in `collapsed` → the raw interval is
  `t_over_units` / `weighted_t_over_units` / `t_over_units_clustered` → carry THOSE VALUES
  as `diffs`. `paired_t_over_units` and its two siblings delegate to exactly those three
  functions and rewrite only `method`, so the corrected bound is the same arithmetic at a
  smaller α rather than a counterpart in name only.
- neither → no member.

"Has a numeric column in `collapsed`" is asked **directly** rather than through
`metric_key in derived`: the proxy also misreads the `E-STEP-KEY-COLLISION` containment
retry, where a colliding name is in `derived` and in `step_summary` as a column.

### Two cases that deliberately build nothing

- **No raw interval (`ci95: null`).** Building a member here would be worse than building
  none: it would enter `by_key`, so `evaluate`'s `key not in by_key` arm could not fire, and
  `ci95_corrected` would go from `null` ("a level was demanded and could not be built") to
  ABSENT ("no correction was attempted") — a different claim about the same run. Pinned, and
  the mutation below shows exactly that regression.
- **A column under BOTH `weight_by` and `cluster_by`.** Its raw interval is
  `weighted_t_over_units_clustered` and this build has no paired counterpart — the very
  absence `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses a comparison over. That code reads the
  RESOLVED comparison family, so a sweepless run declares both legitimately and reaches
  here with a validated config. `Member.__post_init__` refuses both modifiers, and carrying
  either alone would publish a bound from a construction the other declaration contradicts.
  The guard was not loosened; no member is built.
- `by` is skipped, mirroring `_comparison_step_blocks`, so `W-STATS-STRATUM-SHADOWED`'s "no
  seat in the correction family" stays true one surface over.

## Tests (all in `tests/test_cli.py`)

- `test_an_unresampled_condition_metric_corrects_off_its_own_per_unit_values` — row 1. Two
  confirmatory hypotheses so Holm's `family_size` is 2 and the two ranks take α = 0.025 and
  α = 0.05; both corrected intervals are **computed from `stats.t_over_units`** over the
  known `0..39` vector rather than pinned as literals, so a member carrying anything else
  cannot land on both.
- `test_a_resampled_condition_metric_corrects_off_its_own_draw_pool` — row 2. The
  discriminating assertions are that the corrected bound is NOT either *t* construction and
  that both endpoints are attainable bootstrap means (inside the data's range), plus that the
  two ranks produce two different intervals and neither is narrower than its raw one.
- `test_a_derived_condition_metric_corrects_off_its_own_draw_pool` — row 3. At
  `family_size: 1` Holm's level IS α, so `ci95_corrected == ci95` exactly, which is the
  strongest available statement that the two rest on the same sorted draws.
- `test_a_condition_metric_with_no_raw_interval_still_gets_no_member` — row 4, reached from
  a validated config by an `aggregate` that is degenerate on every bootstrap draw
  (`resample_draws: 0`, `ci95: null`). Asserts `ci95_corrected` is PRESENT and null.
- `test_a_weighted_clustered_condition_metric_gets_no_member` — the weighted-clustered
  carve-out, with the block's own `weighted_t_over_units_clustered` / `n.clusters` /
  `weighted_by` asserted first so the absence cannot hold for an unrelated reason.

## Mutation evidence

Every mutation was applied to `src/publishable/cli.py` (a copy kept in the scratchpad), run,
then reverted and the revert verified by re-running the tests to green — never by
`git status`.

| Mutation | Result |
|---|---|
| Pool branch disabled (`if pool is not None:` → `if False:`) | `test_a_resampled_..._draw_pool` FAILS with `assert (15.190838094452271, 23.80916190554773) != approx((15.190838094452271 ± 1.5e-05, 23.80916190554773 ± 2.4e-05))` — the corrected bound became exactly `t_over_units` at α/2 beside a percentile raw interval, which is `cli.py:1644`'s own recorded defect. `test_a_derived_..._draw_pool` FAILS `assert None is not None`. 2 failed, 3 passed. |
| No-interval guard removed (member built with `ci95=None`) | `test_a_condition_metric_with_no_raw_interval_still_gets_no_member` FAILS with `AssertionError: assert 'ci95_corrected' in {'value': 19.5, 'ci95': None, 'method': None}` — the key went from present-and-null to absent, exactly the claim the test makes. 1 failed, 3 passed. |
| `diffs` truncated by one value (`carried[:-1]`) | `test_an_unresampled_...per_unit_values` FAILS, obtained `(15.425783409275954, 24.163960180467637)` against expected `(15.190838094452271, 23.80916190554773)`. 1 failed, 3 passed. |
| Whole member loop short-circuited (`continue` at the top) | all three correctable tests FAIL; row 4's test and the task 1 oracle PASS. 3 failed, 2 passed — the feature is load-bearing for exactly the rows claimed. |
| Weighted-clustered `continue` → `pass` | `test_a_weighted_clustered_condition_metric_gets_no_member` FAILS with `ValueError: Member may not carry both weights and clusters; E-DATA-WEIGHT-CLUSTER-CONTRAST refuses that combination at validate` — the guard is what stands between this config and a crash after every execution is spent. |

## Verification run before reporting

`uv run pytest tests/test_cli.py -k "condition_metric_corrects or
no_raw_interval_still_gets_no_member or weighted_clustered_condition_metric_gets_no_member or
task1_bit_stability_oracle or never_carries_a_pool or no_draw_pool_reaches_the_record"` →
**9 passed**. `tests/test_hypotheses.py tests/test_correction.py` → 112 passed.
`tests/test_cli.py -k "hypothes or verdict or corrected"` → 16 passed.
`ruff check .` clean, `ruff format --check .` clean, `mypy` clean. Full suite left to the
controller.

**The task 1 oracle stayed byte-identical green** — it asserts its whole golden leaf list and
was never touched. Its run declares no `compare: {to: constant}`, so no `const:` key is ever
looked up and its members are exactly the members it had before.

## Concerns

- **`declaration_index` uniqueness across the two lists is unpinned.** The offset
  (`len(comparison_members) + i`) is correct and `rank_family` breaks ties on it, but no test
  separates it from a colliding `i`: it would take a run declaring both a `cond:`-resolved and
  a `const:`-resolved confirmatory hypothesis whose members tie on the evidence ratio. Named
  rather than left implicit.
- **A member carries no `p_value`.** A derived metric under a declared `statistics.null_test`
  has one in its block, and carrying it would add `p_value_corrected` to a
  `to: constant` verdict. Nothing in the design asks for it and it would move output beyond
  the bound test this slice is for, so it was left out deliberately.

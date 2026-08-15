# Task 10 report: the weighted estimator wired, and the percentile path

**Status:** complete. `uv run pytest` 1219 passed / 3 xfailed, `ruff check` and `mypy` clean.
(`ruff format` was not run.)

**Commit:** `dcf1ebc` — *feat: wire the weighted estimator, and a percentile draw that stays
unweighted*. One commit rather than the brief's two: the shared helper `_weighted_mean` is used
by both halves, so splitting them would have put a hunk of half one inside half two's commit.

## Half one — the wiring

`summarize_step` takes `weights: dict[str, Any] | None` (unit key → the roster's `weight_by`
value, exactly the mapping `runner.attrition` already takes), and `cli.py` passes it at all
three call sites. When it is supplied, a **recorded column** changes in three places at once:

| | unweighted | weighted |
|---|---|---|
| `value` | `mean_of` | `weighted_mean_of` |
| `ci95` / `method` | `t_over_units` | `weighted_t_over_units` |
| `n.effective` | absent | Kish's size over **that column's** units |

Wiring only the interval was the named trap; `test_the_recorded_column_value_is_the_weighted_
mean_not_the_plain_one` is the test that fails under it, and the mutation was run.

**Alignment is structural, not only tested.** The loop now takes `(key, value)` in one pass —
`carried = [(key, cols[column]) for key, cols in collapsed.items() if column in cols]` — and the
weight vector is `[weights[key] for key, _ in carried]`, indexed rather than `.get`-ed for the
reason `runner._counts` gives. The fixture is the reviewer's probe: five weighted units, four
completed, three carrying `pred`, so *column carriers* → 2.0, *all collapsed* → 4/3, *all
weighted* → different again. A misalignment cannot land on the right number.

**The `completed`/`effective` caveat is settled by recomputing `effective` per column.**
`reference.md` § The three-part `n` licenses this in so many words: `effective` joins `n`
"whenever `weight_by` makes Kish's size **the one the interval was computed at**". A ragged
column's interval is computed at its own carriers' Kish size, so per-column is what that
sentence says to report. `summarize_step`'s own docstring argues the same case for `completed` — a ragged column's condition-wide
`completed` "would be a lie about how many observations went into it" — so the two figures move
together and describe one unit set. It is *set* from
the column's weights whenever weights are supplied, never conditionally overridden, so a stale
`counts["effective"]` cannot survive the filter. A full column's figure is bit-identical to
`attrition`'s; only a ragged one differs (fixture: 25/11 for `pred`, 3.0 for `other`).

**A derived metric is not weighted by core**, and the decision is the document's, not
convenience: § Weighted samples says core "computes weighted means for `basis: units` column
metrics, hands the column to `aggregate` like any other attribute so a derived metric can weight
itself". There is no per-unit vector to weight — `aggregate` returned one number — and which
weighting a derived metric needs is a property of what it computes (a weighted correlation is
not a weighted mean of anything). Its `weighted_by` and `effective` still travel beside it, as
§ Weighted samples' own example (`r`, a derived metric) shows. Because that conclusion would
otherwise land as an *omission*, the positive half is now tested end-to-end and runs today with
no xfail: `test_the_weight_column_reaches_aggregate_so_a_derived_metric_can_weight_itself`
declares the weight column as an ordinary attribute (so `E-DATA-WEIGHT-UNSUPPORTED` doesn't
fire), has `aggregate` compute 12/6 = 2.0 from it, and asserts core's own unweighted 1.5 beside
it as the control.

The derived branch keeps `effective` from `counts` while computing `completed` as
`len(collapsed)`. Those two describe the same unit set: `collapse_repeats` admits "only a unit
recorded in every repeat it was handed — the same intersection `runner.attrition` takes for
`completed`". No residue, but it rests on that invariant rather than on shared code.

## Half two — the percentile path

`percentile_over_units(values, seed, draws, confidence, weights=None)`. The draw is untouched;
the *statistic* recomputed on each draw is the weighted mean. Pairs are sorted **together**
(`sorted(zip(values, checked_weights(weights)))`), keeping the row-order invariance the
unweighted branch has while making a separate sort impossible.

I took the brief's preferred route — observing the draw through the output, no test-only hook —
and it discriminates. Two additions to the brief's test:

- `result.low == 1.0` **exactly**, not `approx(1.0, abs=0.5)`: a draw with the heavy unit absent
  has a weighted mean of exactly 1.0, and that happens in ≈ 36 % of draws, so the 2.5th
  percentile is that value on the nose.
- A separate pairing test, because the brief's fixture cannot see a separate sort — both
  sequences ascending re-pair to themselves. It puts the heavy weight on the *smallest* value
  (`values = [0.0] + [100.0] × 20`, `weights = [500.0] + [1.0] × 20`) and asserts the low bound
  against the closed form `100·(21−k)/((21−k)+500k)` rather than a captured float, plus exact
  order invariance under a shuffle.

**No Kish floor on this path**, deliberately, and it is a real asymmetry with
`weighted_t_over_units`: that construction refuses an effective size below two because Kish's
size is where its *degrees of freedom* come from, and a percentile interval has none — its
evidence is the spread of the draws. Adding the floor for symmetry would have returned `None`
for the brief's own headline fixture (Kish ≈ 1.08). Stated in the docstring so a reader who asks
finds the answer there.

`statistics.resample` is still refused, so nothing in `cli.py` calls this path yet; the weighted
percentile is library-level, reached when that refusal retires.

## Regressions pinned

Two literal-float pins were captured from the **pre-change** implementation and asserted after —
every existing test in both areas compared one call to another, so a drift that moved both would
have passed the suite: `test_an_unweighted_summary_is_untouched_to_the_last_digit` and
`test_an_unweighted_percentile_interval_is_untouched_to_the_last_digit`
(`Interval(20.4, 28.54)`). Nothing about `cohort-pilot` moves — it declares no `weight_by`, and
the unweighted branches are byte-for-byte the code they were.

## Mutations run

Each applied alone, `__pycache__` deleted between mutation and revert, every revert verified by
re-running tests rather than by `git status`.

| Mutation | Test that failed |
|---|---|
| weighted interval, unweighted mean | `..._value_is_the_weighted_mean_not_the_plain_one` |
| weight vector filtered by the table, not the column | `..._weights_are_aligned_to_the_units_the_column_came_from` |
| `effective` left as `counts` computed it | `test_effective_is_recomputed_over_the_units_the_column_actually_has` |
| weights moved into the drawing (`rng.choices`) | `..._percentile_draw_is_unweighted_while_its_statistic_is_not` |
| values and weights sorted separately | `..._weighted_percentile_keeps_each_value_with_its_own_weight` (**only** that one — the brief's fixture passes it) |
| weights dropped from the per-draw statistic | `..._percentile_draw_is_unweighted...` + the pairing test |

## Concerns for task 11

1. **Two `cli.py` call sites are unreachable by any test today.** The main one is
   forcing-functioned — task 9's strict xfail asserts `pred.value == 2.0`, which is exactly this
   wiring — but the **retry** site (the `E-STEP-KEY-COLLISION` containment) and the **`report_by`
   level** site are not: reaching either with weights needs a config declaring `weight_by`, which
   `E-DATA-WEIGHT-UNSUPPORTED` refuses. Both now pass `weights`; dropping either would silently
   downgrade columns to unweighted numbers and no test would notice. Worth a test each once task
   11 retires the refusal.
2. **The contrast path is still unweighted, and it is the same failure one level over.**
   § Weighted samples: "a contrast between two weighted conditions uses the same weights on both
   sides, which is automatic under `allocation: within` and worth checking when it isn't."
   `paired_t_over_units` takes only `diffs`, `paired_percentile_over_units` likewise, and no
   weighted variant of either exists — grep confirms. So once
   `E-DATA-WEIGHT-UNSUPPORTED` retires, a weighted run reports weighted per-condition means
   beside an **unweighted delta**, and `vs_baseline` is what a reader actually quotes.
   Deliberately not built here: a paired weighted t, and a paired percentile drawing once for
   both sides with the weights in each side's statistic, are their own estimator family — a
   task, not a hunk, and outside the brief's scope (`summarize_step`'s recorded-column loop).
   **Retiring the refusal without deciding the contrast is the same forbidden move the brief
   opened with**, and nothing forcing-functions it the way task 9's xfail pins `pred.value`. My
   read: task 11 should either add the second xfail pin (a delta whose weighted and unweighted
   values differ) before retiring the refusal, or carry the estimator itself; it should not
   retire the refusal and leave the delta undecided. Separately checked and *not* required by
   any document sentence: `repeat_spread` averages member means unweighted, and no rule asks
   otherwise.
3. **A bad weight raises `ContractError · E-DATA-WEIGHT-INVALID` from inside `summarize_step`**,
   which sits under `cli.py`'s containment — but it cannot get there: `attrition` gates the same
   mapping through `kish_effective_n` a few lines earlier, outside any `try`. The window is
   closed for `run` (it validates first) and re-opens for `draft`/`resume` in H9, exactly as
   task 9 recorded for `attrition`.
4. **No document changed.** Everything here is what § Weighted samples already specifies; the
   per-column `effective` is a consequence of two rules already written down rather than a new
   claim, so no `spec-defects.md` entry was added.

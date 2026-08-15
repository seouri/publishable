# Task 11 report — verify the invariant decision 2 rests on

**Status:** COMPLETE.

**Commit:** to be created — `test: verify a column draw is never degenerate, so resample_draws records the requested n`

**Test summary:** `uv run pytest` → 1762 passed, 2 xfailed (baseline 1752 + 2 xfailed + 10 new tests).
`uv run mypy` and `uv run ruff check .` both clean.

## The verification

Read `percentile_over_units` (`src/publishable/stats.py`) and `usable_weight`
(`src/publishable/units.py`) directly rather than accepting the brief's argument on faith.

- **Unweighted branch:** `sum(pool[rng.randrange(n)] for _ in range(n)) / n`, gated by
  `if len(values) < 2: return None` above — so `n >= 2` always when this branch runs, no division
  by zero reachable.
- **Weighted branch:** `_weighted_mean` over a drawn subset, gated by `checked_weights`, which
  reads `units.usable_weight`. Confirmed the guard is `if not math.isfinite(number) or number <= 0:
  return None` (line 552) — a weight of `0`, negative, non-finite, or non-numeric (including `bool`,
  explicitly excluded by `is_measurement_numeric`) is refused with `E-DATA-WEIGHT-INVALID`
  **before any draw**. Σw over a non-empty drawn subset is therefore strictly positive.
- **Stratified branch:** draws `len(group)` rows from each `group` in `ordered`, and every group is
  non-empty by construction (it came from at least one `(value, weight)` pair). No degenerate draw
  reachable there either.

Wrote `tests/test_stats.py::test_a_column_resample_refuses_a_bad_weight_before_any_draw` (parametrized
over `0, 0.0, -1.0, nan, inf, "heavy", None, True`),
`test_a_column_resample_is_never_degenerate_across_adversarial_columns` (zero variance, near-zero
spread, extreme weight ratios, a one-unit stratum, combined strata+weights), and
`test_percentile_over_units_still_returns_a_bare_interval` (the negative pin: decision 2 is that the
return type does NOT become `(Interval, int)`). All ten pass immediately, which is the expected shape
for a verify-and-pin task — a pass on first run is the evidence the decision asked for, not a sign the
test is inert (see the mutation below).

**Mutation (Step 5):** changed `usable_weight`'s guard from `number <= 0` to `number < 0`, admitting a
weight of exactly zero. Re-ran `test_a_column_resample_refuses_a_bad_weight_before_any_draw` — the `0`
and `0.0` parameters FAILED with `ZeroDivisionError: float division by zero` at
`stats.py:167` (inside `_weighted_mean`), confirming the invariant rests on that specific guard and not
on incidental luck. Deleted `__pycache__`, edited the guard back to `number <= 0` in place (never
`git checkout`), re-ran: all 8 weight-refusal parameters pass again.

**Conclusion: no reachable degenerate column draw exists.** The decision holds under the conditions
stated — `values` has length ≥ 2, and any declared weight vector is validated by `checked_weights`
before a draw is taken. `percentile_over_units`'s return type is unchanged.

## Disagreement between brief and code (found, per the standing question for this slice)

The brief's Step 3 docstring text to append read, in present tense: "a column's `resample_draws` is
the requested `n` and is recorded as such by `summarize_step`." Checked against the code
(`c5de085`): `summarize_step`'s recorded-column branch (`out[column] = {...}`, distinct from the
derived-metric branch several lines below it) carries **no `resample_draws` key at all** today —
only `value`, `basis`, `n`, `ci95`, `method`, `correction`. Wiring `statistics.resample` into that
branch, and adding `resample_draws` there, is task 12/14's work; `E-STATS-RESAMPLE-UNSUPPORTED`
still refuses a declared `resample` end to end (confirmed via `grep` in `cli.py`).

Writing the brief's sentence verbatim into `stats.py`'s docstring would have been exactly the failure
mode CLAUDE.md names repeatedly ("a comment or docstring claiming a guarantee the code does not
provide") — a present-tense claim about what `summarize_step` does, when it does not yet do it. I
reworded the appended docstring text to state the invariant conditionally — safe for whenever a later
slice wires column resample into `summarize_step` — rather than asserting current behavior, and
recorded the same distinction in `docs/superpowers/spec-defects.md`'s new entry (its final paragraph)
so the gap between the brief's wording and the code's current state is on the durable record, not just
in this report.

The spec decision itself (record the requested `n`, don't change `percentile_over_units`'s return
type) is unaffected by this — it's a forward-looking ruling about how task 12/14 *should* wire things
when it lands, and that ruling is sound. Only the tense of one sentence needed correcting.

## Concerns

None beyond the above. The invariant is conditional on `values` having length ≥ 2 (already gated by
`percentile_over_units` itself, returning `None` below that) and on any weight vector being routed
through `checked_weights` — both true for every call site in the current code. No new
`E-STATS-RESAMPLE-*` behavior is implied to be honoured end to end by this task.

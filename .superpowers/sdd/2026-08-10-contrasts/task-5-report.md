# Task 5 report: `paired_percentile_of_derived`

## What was implemented

`paired_percentile_of_derived(of, against, keys, compute, seed, draws=2000, confidence=0.95)`
added to `src/publishable/stats.py`, immediately after `percentile_of_derived`. It draws one
`drawn` list of unit keys per bootstrap iteration and applies that same list to both `of` and
`against` before calling `compute` on each — one draw, two tables, one difference. Reuses
`min_honest_draws`, `_percentile_ranks`, and `_unit_table_from_rows` exactly as directed; no
second copy of the rank arithmetic. Degenerate-draw handling matches `percentile_of_derived`:
a `compute` returning `None`/`nan` or raising drops that draw, and percentile ranks are read
off the surviving count, which is always returned as the second tuple element.

## Step 1 — proving the load-bearing test actually discriminates

Followed the brief's instruction to write the wrong (independently-drawn) version first:

```python
drawn_a = [keys[rng.randrange(n)] for _ in range(n)]
drawn_b = [keys[rng.randrange(n)] for _ in range(n)]
a = compute(_unit_table_from_rows([{"unit": k, **of[k]} for k in drawn_a]))
b = compute(_unit_table_from_rows([{"unit": k, **against[k]} for k in drawn_b]))
```

Ran `test_the_paired_interval_is_narrower_than_two_independent_draws` against it: **it failed**,
with a paired-looking interval of width ~12.5 against an independent_width/4 threshold of
~4.4 — i.e. drawing independently produced a *wider*, not narrower, interval, exactly the
failure mode the task warned about. Reverted to the single-`drawn` implementation and reran:
the test passed. This confirms the test discriminates the two spellings rather than passing
against both.

## Fixture defect found in the brief's Step 1 test code — reported, not silently fixed

The brief's literal test data for three tests (`test_the_paired_interval_is_narrower...`,
`test_the_interval_brackets_the_observed_difference`, and
`test_the_same_seed_reproduces_and_a_different_one_does_not`) used:

```python
of = {f"u{i}": {"m": float(i) + 0.5} for i in range(60)}
against = {f"u{i}": {"m": float(i)} for i in range(60)}
```

Because `of[k] - against[k] == 0.5` for **every** unit — a constant offset with zero
residual — the paired construction (one `drawn` list applied to both sides) makes the
resampled difference `mean(0.5 over drawn) == 0.5` identically, regardless of which units are
drawn and regardless of seed. This is not an implementation bug: it is what the *correct*
paired implementation produces on this exact data (verified against the brief's own Step 2
code, and independently rederived by hand). Two consequences:

- `test_the_interval_brackets_the_observed_difference` asserted `got.low < 0.5 < got.high`
  (strict), but the correct implementation returns `Interval(low=0.5, high=0.5, ...)` on this
  fixture — a real, zero-width interval, not a bug, but it fails a strict-bracket assertion.
- `test_the_same_seed_reproduces_and_a_different_one_does_not` asserted seed 7 and seed 99
  give *different* results, but a seed-invariant true value stays seed-invariant under any
  seed — no assertion rewrite could rescue this; only data whose per-unit difference actually
  varies can produce a seed-dependent tail.

Fix applied: changed the per-unit difference from a constant `0.5` offset to an alternating
`1.0`/`0.0` pattern (mean still `0.5`, but 30 units differ by 1.0 and 30 by 0.0):

```python
of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
against = {f"u{i}": {"m": float(i)} for i in range(60)}
```

This gives the paired resample real variance to report (an interval around 0.5 with a
half-width driven by `Binomial(60, 1/2)/60`, well inside the independent-width/4 bound) while
keeping the "narrower than independent" property intact — and, per re-verification below,
*strengthening* the load-bearing test, since a zero-width interval was a weak way to
demonstrate narrowing. Applied the same fixture change to the seed-reproducibility test.
`test_it_names_its_own_method` and `test_below_the_survivor_floor_there_is_no_interval` did
not depend on variance and were left as given (renamed with a `_paired` suffix only to avoid
colliding with the existing tests of the same name for `paired_t_over_units` /
`percentile_of_derived` in the same file).

This is a defect in the brief's Step 1 fixture, not in `docs/reference.md` — the reference's
description of `paired_percentile_over_units` is correct and unaffected. No `docs/` file was
touched.

## Re-verification after the fixture change

Repeated the swap-and-revert from Step 1 against the *updated* fixture, since changing test
data can silently destroy the discrimination just proved: swapped in the independent-draw
(`drawn_a`/`drawn_b`) variant again, confirmed
`test_the_paired_interval_is_narrower_than_two_independent_draws` still fails against it
(paired width ~12.5 vs. threshold ~4.4), then restored the single-`drawn` implementation and
confirmed all 5 new tests pass. `grep -n "drawn_a\|drawn_b" src/publishable/stats.py` returns
nothing in the final state.

## Verification

- `uv run pytest -q` → 658 passed (653 pre-existing + 5 new)
- `uv run ruff check .` → All checks passed
- `uv run mypy` → Success: no issues found in 35 source files

## Files changed

- `src/publishable/stats.py` — added `paired_percentile_of_derived`
- `tests/test_stats.py` — added import and 5 tests (3 with a corrected fixture, see above)

## Round 2: review findings addressed (fix-forward, base moved to `70c6f5c`)

Review came back spec ✅, quality: three Important findings. All three addressed in place.

**Finding 1 — `try` too wide.** The original `try` wrapped both table construction
(`_unit_table_from_rows` plus the `of[k]`/`against[k]` lookups) *and* both `compute` calls, so a
key missing from either side would be swallowed as 2000 silently-dropped `KeyError`s and
reported as `(None, 0)` — indistinguishable from "every draw was degenerate," when it is
actually a core invariant violation (`paired_keys` guarantees both sides hold every key). Fixed
by hoisting `table_a = _unit_table_from_rows(...)` and `table_b = _unit_table_from_rows(...)`
above the `try`, so only `a = compute(table_a); b = compute(table_b)` is contained — matching
`percentile_of_derived`'s pattern exactly.

**Finding 2 — degenerate handling unpinned.** Added three tests that were missing:
`test_a_raising_compute_is_treated_as_degenerate_not_propagated_paired` (both sides always
raise), `test_a_nan_compute_is_treated_as_degenerate_paired` (both sides always return `nan`),
and two one-sided tests — `test_a_one_sided_raise_drops_the_whole_draw_not_half` and
`test_a_one_sided_none_drops_the_whole_draw_not_half` — where only the `against` side fails
(every fourth `compute` call, by a shared counter across both sides) while `of` always
succeeds. Each asserts `used == draws // 2` at `draws=200` (above `min_honest_draws`), pinning
that a one-sided failure drops the *whole* draw rather than surviving on the healthy side.

Verified both tests actually discriminate, per the same swap-and-revert discipline as round 1:
temporarily reverted to a narrowed `try` (wrapping only `compute(table_a)`, with
`compute(table_b)` called unguarded afterward, and the post-check narrowed to `if a is None`
only, dropping the `b is None` check). Both new one-sided tests failed against it — with an
uncaught `TypeError: float() argument must be a string or a real number, not 'NoneType'` at the
`diff = float(a) - float(b)` line — confirming they catch exactly the "narrow try" / "check
only `a`" regressions Finding 1 and Finding 2 named. Restored the correct (hoisted-table, both-
sides-checked) implementation afterward; all tests pass again.

**Finding 3 — constant fixture restored, not replaced.** Added
`test_a_constant_offset_gives_a_genuinely_zero_width_interval` using the original
`of[k] = k + 0.5` / `against[k] = k` fixture from the brief, now asserting
`got.high - got.low < 1e-9` — a point-mass bootstrap genuinely has no width to report. Kept
the alternating `1.0`/`0.0` fixture (from round 1) for the bracket and seed-inequality tests,
since a seed-invariant value cannot satisfy a seed-inequality assertion regardless of
rewording. Both fixtures are now present: the alternating one demonstrates the general
narrowing property with real width on both sides, the constant one demonstrates the sharper
degenerate case (paired width exactly 0.0 vs. nonzero independent width — an unbounded ratio).

### Re-verification (round 2)

- `uv run pytest -q` → 668 passed (658 prior + 10 net new: 5 added, minus none removed, plus
  the 3 new degenerate tests + 2 one-sided tests = 5 new; base tree also grew from Task 6
  landing at `70c6f5c` before this round started)
- `uv run ruff check .` → All checks passed
- `uv run mypy` → Success: no issues found in 35 source files
- Both regression variants (narrowed `try`, `a`-only `None` check) confirmed to crash/fail
  against the new one-sided tests before being reverted.

### Files changed (round 2)

- `src/publishable/stats.py` — hoisted `table_a`/`table_b` construction above the `try` in
  `paired_percentile_of_derived`
- `tests/test_stats.py` — added `test_a_constant_offset_gives_a_genuinely_zero_width_interval`,
  `test_a_raising_compute_is_treated_as_degenerate_not_propagated_paired`,
  `test_a_nan_compute_is_treated_as_degenerate_paired`,
  `test_a_one_sided_raise_drops_the_whole_draw_not_half`,
  `test_a_one_sided_none_drops_the_whole_draw_not_half`

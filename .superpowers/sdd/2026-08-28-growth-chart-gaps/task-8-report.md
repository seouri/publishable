## Task 8 report

Status: done. Added two adversarial tests to `tests/test_validate.py` for
`W-SWEEP-CONDITION-DUPLICATE`, extending the existing suite without changing
`_warn_duplicate_conditions` or `_group_axes_already_erred`.

- `test_the_reported_pair_is_the_first_in_condition_order_not_last_every_or_label_sorted`:
  9-condition single-axis grid fixture, decoys before/between/after two duplicate
  pairs, labels `zzz_first`/`aaa_second` chosen so condition order and label-sort
  order disagree. Asserts exactly one finding, containing `zzz_first` and none of
  the decoy labels or `aaa_second`.
- `test_the_sharp_group_axis_codes_still_fire_and_this_warning_still_stays_out_of_their_way`:
  one config forcing `E-SWEEP-LEVEL-DUPLICATE`, `E-SWEEP-BASELINE-GROUP`, and
  `W-SWEEP-CONDITION-DUPLICATE` all present via `codes()` (exact code set).

Mutations (each applied to `src/publishable/validate.py`, run via
`uv run pytest tests/test_validate.py -k "duplicate or sharp_group_axis_codes or reported_pair_is_the_first" -q`,
then reverted from a saved copy and confirmed byte-identical by diff before
re-running to green):

1. Scan-last-wins (`for j in range(len(conditions)-1, 0, -1)`): reddened new test +
   2 pre-existing tests — reported `aaa_second` instead of `zzz_first`.
2. Report-every-pair (removed the `return` after `c.warn`): reddened new test
   (`len(findings) == 1` failed, got 2) + same 2 pre-existing tests.
3. Label-sort-order (sorted `conditions` by `.label` before scanning): reddened
   new test only — reported `aaa_second` (alphabetically first) instead of
   `zzz_first`.

All three restores verified green (10 passed) with the correct `-k` filter after
an initial false-negative run where `-k "duplicate"` alone silently excluded the
new test by name (caught before reporting).

`uv run pytest tests/test_validate.py`: 806 passed. `ruff check .`: clean.
`ruff format --check .`: clean. `mypy`: clean.

Concern: none — predicate untouched, no findings against it to report.

## Fix round 1

Finding: round 1's fixture had two duplicated values (`zzz_first`, `aaa_second`)
where `aaa_second` was simultaneously the alphabetically-first label and the
physically-last duplicate, so scan-last-wins and label-sort-order produced the
same observation. The docstring's claim that all three wrong candidates
disagreed was false, even though both mutants did redden the test.

Fix: rebuilt the fixture with three duplicated values instead of two —
`mmm_first` (smallest max-index), `aaa_mid` (alphabetically-first label,
placed in the middle position, max-index 7), `zzz_last` (largest max-index) —
with decoys before, between, and after every pair. This separates all four
candidates:

- correct (first-in-condition-order): 1 finding, names `mmm_first`
- scan-last-wins: 1 finding, names `zzz_last`
- label-sort-order: 1 finding, names `aaa_mid`
- report-every-pair: 3 findings

Mutations re-run against the amended fixture (each from a clean copy of
`src/publishable/validate.py`, restored and behaviorally re-verified — not
just `git status` — before the next):

1. `for j in range(len(conditions) - 1, 0, -1)` (scan-last-wins).
   Command: `uv run pytest tests/test_validate.py -k "duplicate or sharp_group_axis_codes or reported_pair_is_the_first" -q`
   Output: `3 failed, 7 passed` — new test failed with
   `assert 'mmm_first' in '...schedule=zzz_last...'`. Restored; re-run gave
   `10 passed`.
2. Removed the `return` after `c.warn` (report-every-pair).
   Same command. Output: `3 failed, 7 passed` — new test failed with
   `assert 3 == 1` (three findings, not one). Restored; re-run gave
   `10 passed`.
3. Sorted `conditions` by `.label` before scanning (label-sort-order).
   Same command. Output: `1 failed, 9 passed` — only the new test failed,
   with `assert 'mmm_first' in '...schedule=aaa_mid...'`. Restored; re-run
   gave `10 passed`.

After the third restore, `diff` against the saved clean copy of
`validate.py` showed no differences, confirmed by byte-diff before the
behavioral re-run (which also passed).

`uv run pytest tests/test_validate.py`: 806 passed. `ruff check .`: clean.
`ruff format --check .`: clean. `mypy`: clean.

Concern: none — predicate untouched, only the fixture and its docstring changed.

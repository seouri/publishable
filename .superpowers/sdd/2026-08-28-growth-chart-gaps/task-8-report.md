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

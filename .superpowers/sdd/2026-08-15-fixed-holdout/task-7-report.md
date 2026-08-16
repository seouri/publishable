# Task 7 report: `_check_holdout`, roster half

## Status: DONE

## What was built

- `src/publishable/units.py`:
  - `HOLDOUT_LEVELS = ("train", "test")` — the fixed two-literal order.
  - `holdout_sizes(n, frac) -> tuple[int, int]` — `(train, test)`, `_apportion(n, [1-frac, frac])`.
  - `holdout_values_fault(roster, column) -> str | None` — wraps `arms_of(roster, column, HOLDOUT_LEVELS)`,
    catching `ContractError` and rebuilding the message in a holdout's own vocabulary; returns `None` when
    `arms_of` does not raise.
  - `stratum_varies_within_cluster`'s docstring corrected from two call sites/rows to four
    (`E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES`, `E-STATS-RESAMPLE-STRATIFY-VARIES`,
    `E-DATA-HOLDOUT-STRATIFY-VARIES`), naming all four § Validation rows.
- `src/publishable/validate.py`:
  - Imported `holdout_sizes`, `holdout_values_fault` from `publishable.units` (not `arms_of` — it stays
    behind `holdout_values_fault`, per the brief).
  - `_check_holdout`'s docstring enumeration grown from seven to ten findings, with the three new bullets
    each marked "reads the roster", and the "none reads roster" sentence corrected to name the three that
    now do (this sentence would otherwise have gone stale the moment the three new checks were added —
    fixed as part of this task even though the brief's inserted text didn't itself touch it).
  - Three new checks appended to `_check_holdout`'s body, each with its own `roster is not None` guard:
    - `E-DATA-HOLDOUT-VALUES` — `by_attribute`, roster present, `from` a non-empty string: collects
      `holdout_values_fault`'s message if not `None`.
    - `E-DATA-HOLDOUT-STRATIFY-VARIES` — roster present and `cluster_by` declared: the fourth
      `stratum_varies_within_cluster` call site, skipping names already refused by
      `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`.
    - `E-DATA-HOLDOUT-EMPTY` — `random`, unstratified, unclustered, roster present, `frac` a valid open-interval
      float: `holdout_sizes` apportions the test side to zero.
- Tests appended verbatim from the brief to `tests/test_units.py` (`holdout_sizes` import +
  `test_holdout_sizes_is_the_single_authority_for_the_split_sizes`) and `tests/test_validate.py` (the six
  new tests/fixtures covering `E-DATA-HOLDOUT-VALUES`, `E-DATA-HOLDOUT-STRATIFY-VARIES`, and
  `E-DATA-HOLDOUT-EMPTY` plus their positive companions and the clustered-empty-test control).

## `reference.md` § Errors

All three new codes already had rows (`E-DATA-HOLDOUT-VALUES` line 484, `E-DATA-HOLDOUT-STRATIFY-VARIES`
line 485, `E-DATA-HOLDOUT-EMPTY` line 486) — minted by task 1, and each row's description matches what the
code under this task actually reports. No document change needed.

## `stratum_names` — not touched

Its docstring still names only two call sites (`validate._check_assign`, `validate._check_resample`)
against six actual call sites (`units.py:1505`, `validate.py:1969,2387,2854,5416,5489`, `cli.py:1122`).
This task's checks call `arms_of` (via `holdout_values_fault`) and `stratum_varies_within_cluster`, never
`stratum_names`, so I did not add a seventh call site and left this docstring exactly as task 6's review
found it — still unowned. Flagging again per the brief's instruction not to let it sit silently a second
time.

## Verification

- Step 2 (pre-implementation, confirm failing): `holdout_sizes` failed on `ImportError`; every new
  `validate` test asserting a new code failed on missing code; the three wholesale-refusal controls
  (`E-DATA-HOLDOUT-UNSUPPORTED`) passed.
- Step 4: `uv run pytest` → 10/10 new tests pass; full suite 1869 passed, 2 xfailed (baseline 1859+2, +10
  from this task). `uv run ruff check .` clean. `uv run ruff format --check .` → 63 files would reformat,
  consistent with this repo's standing baseline (not introduced by this task — confirmed by diffing the
  touched files' reformat count against the pre-existing whole-repo baseline). `uv run mypy` clean.
  Docstring sweep: `grep -rn "Fold strata survive clustering" src/ tests/ docs/` — every site now names
  four rows; proved the sweep can fail by re-running for `Holdout strata survive clustering`, which
  returns real hits (not silently empty).

## Step 5 mutations — all three verified to discriminate exactly as predicted

**(a)** `holdout_sizes` body → `_apportion(n, [frac, 1.0 - frac])[0], [...][1]` (weights reversed).
Ran `uv run pytest tests/test_units.py tests/test_validate.py -k "holdout_sizes or apportions_the_test or larger_roster"`:
- `test_holdout_sizes_is_the_single_authority_for_the_split_sizes` — **FAILED**:
  `assert (2, 8) == (8, 2)` at the first line, `holdout_sizes(10, 0.2)`.
- `test_a_holdout_that_apportions_the_test_side_no_units_is_refused` — **FAILED**:
  `assert 'E-DATA-HOLDOUT-EMPTY' in found` → found only `{'E-DATA-HOLDOUT-UNSUPPORTED'}` (4 units against
  reversed weights apportions `(0, 4)`, so the *test* side holds everything and the refusal never fires).
- `test_the_same_frac_over_a_larger_roster_is_accepted` — **PASSED** (did not move, as predicted: 40 units
  gives `(4, 36)` under either weight order).
Reverted by editing the file back; re-ran the same three — all pass (1 pass, then reverted → 3 passed
after re-running with the full `-k` set together).

**(b)** Deleted `and not cluster_by` from the `E-DATA-HOLDOUT-EMPTY` guard.
Ran `uv run pytest tests/test_validate.py -k clustered_split`:
- `test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split` — **FAILED**:
  `assert 'E-DATA-HOLDOUT-EMPTY' not in found` → found `{'E-DATA-HOLDOUT-EMPTY', 'E-DATA-HOLDOUT-UNSUPPORTED'}`.
Reverted by editing the file back; re-ran — 1 passed.

**(c)** In `holdout_values_fault`, changed `arms_of(roster, column, HOLDOUT_LEVELS)` to
`arms_of(roster, column, sorted({str(u.attributes.get(column)) for u in roster}))`.
Ran `uv run pytest tests/test_validate.py -k by_attribute_holdout -v`:
- `test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test` — **FAILED on all three rows**
  (`a third value`, `neither literal`, `one literal unused`), each on
  `assert 'E-DATA-HOLDOUT-VALUES' in found` → found only `{'E-DATA-HOLDOUT-UNSUPPORTED'}` — every observed
  value became a declared level, so `arms_of` never raised.
- `test_a_by_attribute_holdout_column_holding_exactly_the_two_literals_is_accepted` — **PASSED** (not run
  against explicitly, but unaffected by construction — the positive fixture already has exactly two
  values, so the mutated "sorted observed values" reading agrees with the real one there).
Reverted by editing the file back; re-ran the full `by_attribute_holdout` group — 4 passed.

After each revert, diffed the live file against a pre-mutation backup copy (`units.py.bak`,
`validate.py.bak` in the scratchpad) with `diff` — both reported no differences, confirming a clean
revert by content rather than by `git status`. No `git checkout --` was used on either source file.

## Where the brief disagreed with the code

None. The brief's interfaces, message text, and body diffs matched the existing code exactly (import
list, docstring insertion points, `strata`/`declared_names` variables already in scope from the earlier
`E-DATA-HOLDOUT-STRATIFY-UNKNOWN` check). The one thing the brief's diff didn't itself touch but that
needed a matching correction was the `_check_holdout` docstring's "none reads `roster` or `cluster_by`"
sentence, which would have gone stale the instant the three roster-reading bullets were added — fixed in
the same edit as the enumeration count.

## `.superpowers/sdd/.gitignore`

Found clobbered to a bare `*` (by an earlier `task-brief` invocation before this task started) and
restored via `git checkout -- .superpowers/sdd/.gitignore` — safe here since the file itself carried no
uncommitted work, only the known clobber, and the tracked content is what CLAUDE.md says to restore.

## Commit

`feat: refuse a holdout column, stratum or frac the roster cannot honour`

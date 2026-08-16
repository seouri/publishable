# Task 10 report: `units.holdout_for` — the unclustered draw and the column read

## Status: DONE

## What was built

- `src/publishable/units.py`, after `holdout_values_fault` and before
  `auto_block_size`:
  - `HoldoutPlan` (frozen dataclass): `train`, `test`, `seed`, `strata`.
  - `HOLDOUT_METHODS_REALIZED = ("random", "by_attribute")`, declared here
    (not imported from `validate`, which imports `units` and not the reverse).
  - `holdout_for(roster, block, *, seed, clusters=None) -> HoldoutPlan`:
    - Raises `NotImplementedError` up front if `stratify_by` is non-empty or
      `clusters is not None` (construction 2, task 11's).
    - `by_attribute`: resolves `from`, calls `holdout_values_fault` and raises
      its message under `E-DATA-HOLDOUT-VALUES` if it fails, else reads through
      `arms_of(roster, column, HOLDOUT_LEVELS)` and returns the two sides with
      `seed=None`, `strata=()`.
    - `random`: validates `frac` is a non-bool int/float, computes
      `holdout_sizes(len(roster), float(frac))`, raises `E-DATA-HOLDOUT-EMPTY`
      if either side is 0 (message names which side), else shuffles the whole
      roster's keys with `random.Random(seed)` and cuts two consecutive slices,
      train first.
    - Any other method: `NotImplementedError` naming the allowlist.
- `tests/test_units.py`: imported `holdout_for`, `holdout_sizes` (already
  present), inserted the brief's six tests verbatim after
  `test_holdout_sizes_is_the_single_authority_for_the_split_sizes`, with one
  helper renamed (see Disagreement).

## Disagreement with the brief (verified, not assumed)

The brief's Step 1 defines a test helper `_roster(n, **attrs_by_index)`. The
test module **already has** a module-level `_roster(n) -> UnitList` at line
222 (keys `u{i:03d}`, zero-padded to 3 digits), used by more than a dozen
existing tests, three of which pin exact key literals against that padding
(`test_partitions_cover_the_roster` at line 296, and the ordering-fixture test
at lines 333-337: `"u018"`, `"u036"`, etc.). Defining a second top-level `def
_roster(...)` with the same name overwrites the module's `_roster` binding for
every test in the file, regardless of position, because all these tests are
functions that look up the global name at call time — the later `def` wins
for the whole module, unconditionally. Appending the brief's version verbatim
would have silently broken those pinned-literal tests (`u{i}` vs. `u{i:03d}`
keys) the next time they ran, an instance of exactly the "sweep for the claim,
not the file" and "predicted vs. run" failure classes this slice is trying to
close — except here it's a naming collision rather than a prediction.

Fixed by renaming the new helper to `_holdout_roster`, used only by this
task's six new tests; the old `_roster` is untouched and all its dependents
still pass. No other code changed as a result — this is a test-only rename.

I verified the collision empirically before renaming: renaming was decided by
reading the two definitions and their call sites, not by running into a
failure, since the collision would only manifest as those three pinned tests
failing with different (unpadded) keys the next time the suite ran — a defect
that a "define an already-existing name" review sweep is meant to catch before
it ships.

No other disagreements found. The rest of the brief's implementation (the
`HoldoutPlan` docstring, `holdout_for`'s docstring, the dispatch logic,
`HOLDOUT_METHODS_REALIZED`) was used essentially verbatim; I tightened
`HOLDOUT_METHODS_REALIZED`'s own docstring slightly (it referred to
`assignment_for`'s "fourth drawing method" language, which is `assign`'s own
count and not this seam's) rather than leave a comment that names the wrong
mechanism.

## Pinned literals — derived by running, not predicting

Per the brief's ordering (structural assertions first, then print-and-paste),
I ran the structural assertions clean before touching the `"REPLACE"` lines,
then ran:

```
uv run python -c "
from publishable.units import holdout_for, UnitList, Unit
roster = UnitList([Unit(key=f'u{i}', paths=(), attributes={}) for i in range(10)])
plan = holdout_for(roster, {'method':'random','frac':0.2}, seed=1234)
print(plan.train); print(plan.test)
"
```

which printed:

```
('u2', 'u8', 'u3', 'u5', 'u6', 'u4', 'u9', 'u0')
('u1', 'u7')
```

Pasted verbatim as the two literals in
`test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes`.
(My first attempt at these literals was a guess rather than a run and failed
the assertion — corrected before proceeding, per the brief's own warning about
predicted literals.)

## Step 5 mutations, run as instructed

**(a)** Swapped the slices: `train=tuple(shuffled[train_size:]),
test=tuple(shuffled[:train_size])`. Ran
`uv run pytest tests/test_units.py -k holdout_cuts`:

```
FAILED ... assert (2 == 8)
 +  where 2 = len(('u1', 'u7'))
 +    where ('u1', 'u7') = HoldoutPlan(train=('u1', 'u7'), test=(...8 items...)).train
```

**FAIL**, on `len(plan.train) == 8` (and would fail on the pinned literals too
— it never reached them). Reverted by editing the file back; re-ran, `1
passed`; confirmed by diffing the whole file against a pre-mutation backup
copy (`units.py.bak`, byte-identical, `diff` exit 0) after all three
mutations, never by `git status`.

**(b)** Deleted `random.Random(seed).shuffle(shuffled)`. Ran
`uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster"`:

```
FAILED test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes
  assert plan.train == ("u2", "u8", ...) — At index 0 diff: 'u0' != 'u2'
FAILED test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not
  assert ('u15', ..., 'u19') != ('u15', ..., 'u19')
```

**Both FAIL**, as the brief's own guard requires. Reverted by editing the
shuffle line back; re-ran, `2 passed`.

**(c)** First tried the brief's flagged no-op: changed
`arms_of(roster, column, HOLDOUT_LEVELS)` to
`arms_of(roster, column, tuple(reversed(HOLDOUT_LEVELS)))`. Ran
`uv run pytest tests/test_units.py -k by_attribute_holdout_reads`: **PASSED**
— confirmed the brief's own analysis that this mutation is a no-op, because
the function indexes the returned mapping by `HOLDOUT_LEVELS[0]`/`[1]`
(literal keys), not by the argument's position. Reverted this variant.

Then applied the prescribed replacement: swapped the return's sides —
`train=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]), test=tuple(u.key for u
in sides[HOLDOUT_LEVELS[0]])`. Ran the same command:

```
FAILED test_a_by_attribute_holdout_reads_the_column_and_records_no_draw
  assert plan.test == ("u0", "u5") — At index 0 diff: 'u1' != 'u0'
```

**FAIL**, as required. Reverted by editing the file back; re-ran, `1 passed`.

All three reverts confirmed both by re-running each target test (passing
again) and by a final whole-file `diff` against `units.py.bak`, which
reported no differences (exit 0), before deleting the backup.

## Verification

- `uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster or by_attribute_holdout or leaves_a_side_empty or unknown_holdout_method"` — 10 passed.
- `uv run pytest` — 1902 passed, 2 xfailed (baseline 1892 + 10 new).
- `uv run ruff check .` — All checks passed (after removing an initially-added,
  unused `HoldoutPlan` import from the test module's import list — the tests
  never construct one directly, only via `holdout_for`).
- `uv run ruff format --check .` — 63 files would be reformatted (pre-existing
  baseline; `units.py`/`test_units.py` were already among them). Confirmed no
  reformat diff touches the new code by running `ruff format --check` and
  inspecting the reported hunks — none fall in the new `HoldoutPlan`/
  `holdout_for` region or the new test functions. Did not run bare
  `ruff format .`.
- `uv run mypy` — Success: no issues found in 42 source files.

## Commit

`a6c6945` — `feat: units.holdout_for — the unclustered draw and the column read`

Files touched: `src/publishable/units.py`, `tests/test_units.py`.

`.superpowers/sdd/.gitignore` was found clobbered to a bare `*` (the known
`scripts/task-brief`/`scripts/sdd-workspace` issue) before staging; restored
via `git checkout HEAD -- .superpowers/sdd/.gitignore` (the tracked, correct
content) rather than committing the clobbered version, and left untouched by
the commit above (only `units.py`/`test_units.py` staged with `git add -f`).

## Concerns

None outstanding. The one real disagreement (the `_roster` name collision) is
described above and resolved by a test-only rename; nothing in
`src/publishable/units.py` changed as a result of it.

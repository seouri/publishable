# Task 12 report: `units.holdout_seed_for`

## Status

DONE

## What was built

`src/publishable/units.py`: added `holdout_seed_for(block, digest, roster) -> int`, placed
immediately after `assign_seed_for` and before `units_hash`, per the brief. Construction:
pinned non-bool `int` in `block["seed"]` returned literally (digest never consulted on that
path); otherwise `sha256(f"{digest}|holdout|{units_hash(roster)}")`, first four bytes
big-endian — the same shape as `assign_seed_for`, with its own `|holdout` suffix rather than
`_seed_from`'s `|folds` or `assign_seed_for`'s `|assign|<axis>`.

`tests/test_units.py`: added `_seed_from` and `holdout_seed_for` to the import list (`_roster`,
`assign_seed_for`, `units_hash` were already imported — reused, not redefined, per the
collision warning in the task context). Appended five tests at end of file, verbatim from the
brief:

- `test_a_pinned_holdout_seed_is_returned_literally_and_ignores_the_digest`
- `test_a_boolean_seed_is_not_a_pin`
- `test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster`
- `test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest`
- `test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest`

## Test summary

`uv run pytest` — 1924 passed, 2 xfailed (1919 + 5 new). `uv run ruff check .` and
`uv run mypy` clean. `uv run ruff format --check .` shows the same pre-existing 63-file drift
noted in the task context (units.py/test_units.py are the already-unformatted baseline; the
diff at those two files' lines matches lines this task did not touch).

## Mutations — five run, not two

All reverted by editing the file back (never `git checkout --`); each revert verified by
re-running the targeted tests, and a final `diff` against a pre-mutation backup copy of
`units.py` confirmed byte-identical restoration before commit.

**(a)** brief's — payload's `|holdout|` → `|assign|holdout|`.
Result: **FAIL**, exactly as predicted —
`test_the_holdout_seed_is_not_an_assign_axis_seed_for_the_same_digest` failed with
`3716163157 == 3716163157` (the mutated function now computes exactly
`assign_seed_for({}, "holdout", ...)`'s payload). All other 5 tests still passed.

**(b)** brief's — `if isinstance(seed, int) and not isinstance(seed, bool):` →
`if isinstance(seed, int):`.
Result: **FAIL** — `test_a_boolean_seed_is_not_a_pin` failed on its first assertion
(`assert derived != 1` → `True != 1`, i.e. `derived == 1` since `True` is now honoured as a
pin). pytest stops at the first failing assertion in a test function, so the second assertion
in that test did not get a chance to execute under this mutation — reported as observed rather
than asserting the brief's "both" literally.

**(c)** mine — deleted the pinned-seed early return entirely (function always derives).
Result: **FAIL** — `test_a_pinned_holdout_seed_is_returned_literally_and_ignores_the_digest`
failed: `3480535593 == 4321` is false: the pin is silently ignored. This discriminates the
"pinned path skips the digest" contract that mutation (b) does not reach.

**(d)** mine — dropped the roster from the payload (`payload = f"{digest}|holdout".encode()`,
no `units_hash(roster)`).
Result: **FAIL** — `test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster`
failed on its roster half: `holdout_seed_for({}, "sha256:aaa", _roster(10))` and
`holdout_seed_for({}, "sha256:aaa", _roster(11))` collided (`1048393362 == 1048393362`),
proving the test's roster-size assertion is not blind — it does discriminate before the
digest-only construction is reached. (The reordered-roster assertion in the same test would
also have failed had execution reached it; pytest stopped at the first failing line.)

**(e)** mine, named per the brief's instruction to find whatever single line kills
`test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest` — replaced the payload line
with `_seed_from`'s exact construction: `payload = f"{digest}|folds".encode()` (dropping both
the `|holdout` suffix and the roster term, since `_seed_from(digest)` is
`sha256(f"{digest}|folds")` with no roster mixed in at all).
Result: **FAIL** — `test_the_holdout_seed_is_not_the_fold_seed_for_the_same_digest` failed with
`984440229 == 984440229`, confirming the two derivations collide once the payload is made
byte-identical to `_seed_from`'s.

**Finding to report rather than paper over:** this mutation could not be made to fail *only*
the fold-neighbour test. Making `holdout_seed_for`'s output equal `_seed_from(digest)` on any
input requires its payload to be byte-identical to `f"{digest}|folds"` (a sha256 collision on
a differently-shaped payload is not a realistic alternative), which necessarily drops the
`units_hash(roster)` term too — so this same edit also failed
`test_the_derived_holdout_seed_mixes_the_digest_and_the_resolved_roster` (the `_roster(11)`
assertion) as a side effect. I checked whether a narrower one-line change exists that
preserves the roster term and still collides with `_seed_from` — e.g. changing only the
`|holdout|` suffix to `|folds|` while keeping `{units_hash(roster)}` appended — and confirmed
by inspection and by running it that this does *not* collide (`_seed_from` has no roster
suffix at all, so `f"{digest}|folds|{units_hash(roster)}"` still differs from
`f"{digest}|folds"`), meaning it does not fail the target test. So the fold-neighbour
distinction, as a single-line mutation, is only reachable by an edit that is inseparable from
the roster-inclusion mutation (d) — the two tests are not independently discriminated by any
one-line change I could construct, though each is independently discriminated by *some*
combination not tested here. This is a narrower version of the same coupling the task context
warned about elsewhere in this slice (a fixture too coarse to distinguish two claims); here it
is the mutation, not the fixture, that is coarse, and it is disclosed as such rather than
silently claimed as a clean single-property proof.

## Where the brief disagreed with the code

None found. `assign_seed_for`, `_seed_from`, and `units_hash` all matched the brief's
description exactly (verified by reading `src/publishable/units.py` before writing the new
function), and the prescribed test names, docstrings, and payload shape were used verbatim.

## Process notes

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` by running `scripts/task-brief` to
extract this task's brief (per the standing warning in `CLAUDE.md`). Restored via
`git checkout -- .superpowers/sdd/.gitignore` before committing — safe here because that file
had no uncommitted content of its own being destroyed; it was reverting the auto-clobber back
to the last commit's tracked (correct) content, exactly the "restore" the CLAUDE.md instruction
prescribes.

# Task 15 report — `allocation_hash` controller additions (rescoped)

## Status: DONE

Commit: `b4858e7` — "test: add the discriminating swap-two-units allocation_hash assertion"

Task 14 (`b15ef37`, fixed up in `f7a02db`) already shipped `artifacts.allocation_hash`,
`artifacts.build_allocation_document`, and the `provenance.allocation` / `provenance.allocation_hash`
wiring in `cli.command_run`, all reviewed and verified. This task did the four items the rescoping
addendum listed as remaining, and rebuilt none of task 14's work.

## What was done

**1. The swap-two-units assertion, in its discriminating form.**
Added `test_allocation_hash_changes_when_two_units_swap_arms_and_nothing_else_moves` to
`tests/test_artifacts.py`, immediately after the existing (weaker) `c3`→`c9` document-key mutation
test. It swaps `c0` (`control`) and `t0` (`treatment`) between arms in the `_mixed_arm_roster` fixture
— same 13 keys, same per-arm counts (4/9), same multiset of `arm` values; only which key sits in which
arm moves. This is the property the reviewer's own hint (`bf077b6d…` → `74e5df03…`) turned out to
name exactly: I recomputed both digests directly against this build rather than trusting the addendum's
numbers, and they matched to the full 64 hex characters once I found the swap pair that produces them
(`c0`/`t0` — the addendum didn't say which two units, and the first pair I tried, `c1`/`t4`, produced a
different, equally valid digest). The test asserts both exact digests and that they differ, plus that
the swapped document's per-arm sets are exactly what the swap predicts.

**2. Bytes-vs-canonical docstring — confirmed correct, not changed.**
Read `artifacts.allocation_hash`'s current docstring: it already states the hash is over the
*canonical* re-encoding (`sort_keys=True`, compact separators) of the same dict `build_allocation_document`
returned, not the `indent=2` file bytes `allocation.json` is written as, and gives the exact
re-canonicalization a reader must perform by hand. Task 14's post-review fix round (`f7a02db`) landed
this correctly; nothing needed changing here.

**3. The rule with no reader — stated, not tested.**
Added a paragraph to `build_allocation_document`'s docstring stating that `allocation.json` is "read
rather than re-drawn" on resume (`reference.md` § Resuming, § Allocation: within-subjects or
between-subjects), and that **this rule has no reader in this build**:
`OPERATION_COMMANDS = {"validate", "run"}` in `cli.py` — there is no `resume` command, so nothing calls
`build_allocation_document` a second time against an existing file. No test claims to cover this; the
paragraph is written as the contract a future `resume` must honour.

**For task 18, verbatim:** *`allocation.json`'s "read rather than re-drawn on resume" rule has no reader
in this build — `OPERATION_COMMANDS = {"validate", "run"}` contains no `resume` command, so nothing
calls `build_allocation_document` a second time against an existing file, and no test exercises this
path.*

**4. Why `allocation_hash` lives in `artifacts.py`.**
Added a paragraph to `allocation_hash`'s docstring: `hashes.py`'s three functions (`code_hash`,
`parameters_hash`, `design_digest`) each hash something the caller already has (the repo tree, the
config) — nothing that module built itself. `manifest_hash` instead sits in `manifest.py` beside
`build_manifest`, because it hashes the exact document its own module just constructed — verified by
reading `manifest.py`, which does hold both `build_manifest` and `manifest_hash`.  `allocation_hash`
follows that precedent, not `hashes.py`'s: it hashes `build_allocation_document`'s own return value,
and that function lives in `artifacts.py` because `allocation.json` is an artifact `cli.command_run`
writes alongside the others this module handles. Noted for a future H3d reader: a `holdout_hash`, if
one is ever needed, belongs beside whatever builds the holdout document — not in `hashes.py` either.
I did not move `allocation_hash`; the placement looks correct to me.

## Verification

- `uv run pytest` — 1482 passed, 2 xfailed (was 1481 passed before this task; +1 new test).
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, no issues in 40 source files.
- Mutation testing: mutated `arms[axis] = {level: [u.key for u in units] ...}` to
  `{level: sorted(u.key for u in units) ...}` (sorts membership instead of preserving `arms_of`'s
  roster order). Deleted `__pycache__`, ran the new swap test — FAILED (the exact expected digests no
  longer matched, since sorting changes the recorded key order for both the swapped and unswapped
  documents). Reverted the mutation, deleted `__pycache__` again, re-ran — PASSED. Verified by test
  behaviour, not `git status`.
- No `*.md` file was touched (no string was removed or renamed), so the "grep every tracked `*.md`"
  step found nothing to check against.

## Concerns / things worth a second look

- The addendum's placeholder digests (`bf077b6d…` → `74e5df03…`) turned out to be real, exact digests
  from this fixture — but for a specific swap pair (`c0`/`t0`) that the addendum text never named. I
  verified this by brute-forcing all `control`×`treatment` pairs against the target hash rather than
  guessing; a different reader following only the prose (which says "swap two units," not which two)
  could easily have picked a different, equally correct pair and produced different digests. I used
  the pair that reproduces the addendum's exact numbers, so this test's expected values are literally
  the ones the reviewer already measured — nothing here rests on a number I invented.
- No requirement in the rescoped addendum turned out to be unsatisfiable or resting on a false premise.
  The "corrections from the pre-flight audit" section already pre-empted the two factual errors in the
  original addendum text (`provenance.py` builds no hashes; the `allocation: null` line is in § The two
  files, not § The one config file), and both held up under my own reading of the current source.

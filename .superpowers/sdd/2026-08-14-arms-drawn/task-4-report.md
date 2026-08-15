# Task 4 report — The `assign` per-axis whole-leaf closure

## Status: done

Commit: `1b5d909` — "fix: close data.units.assign's per-axis blocks to a known key set"

## What changed

- `src/publishable/envelope.py`: added `ASSIGN_AXIS_KEYS = frozenset({"method",
  "from", "ratio", "block_size", "stratify_by", "seed"})` and
  `_check_assign_axis_keys`, called from `check_envelope` right after
  `_check_unknown_keys`. It walks `data.units.assign`, and for every axis
  block that is a mapping, checks the block's own keys against that closed
  set, reporting `E-CONFIG-KEY-UNKNOWN` with the same difflib "did you mean"
  hint the generic closure uses. A non-mapping axis block is left alone —
  `_check_assign`'s `E-DATA-ASSIGN-METHOD` already reports it as "the block
  naming no method that it is."
  - This is a hand-built second closure rather than an addition to
    `LEAF_TYPES`, because the generic `_check_unknown_keys` never descends
    into a known LEAF's value, and `data.units.assign` is one; the axis name
    one level up (`arm`) is exactly the dynamic key `LEAF_TYPES` cannot name,
    so the mechanism can't be pointed at this block by adding a dotted path.
  - Updated the module-docstring comment describing `grid`/`baseline`/`assign`
    as fully-dynamic to note that `assign` differs one level further in: the
    axis name stays unnameable, but the block's own keys are now closed.
- `docs/reference.md` § The one config file: rewrote the gap sentence beside
  `.assign` (previously: "`envelope.py` still types the block a bare `dict`
  with no per-axis-key closure ... recorded as an open gap") to state the
  closure now exists and name the closed set, matching the code.
- `tests/test_validate.py`: added
  `test_a_misspelled_key_inside_an_assign_block_is_reported`, exactly as
  specified in the brief, placed beside the other `assign`-block tests.
- `docs/superpowers/spec-defects.md` (untracked/gitignored — not part of this
  commit): marked its matching entry `RESOLVED (arms-drawn, task 4)` and
  appended a closing note, for continuity of that local working log.

## Test summary

`uv run pytest` — 1503 passed, 2 xfailed. `uv run ruff check .` — all checks
passed. `uv run mypy` — no issues in 40 source files.

## Mutation testing (both directions, per the brief)

1. **New test fails correctly before the fix** — reproduced by removing the
   `_check_assign_axis_keys` call path in an earlier pass (the test only
   passed once the implementation was in place; confirmed via normal TDD
   red-green, not asserted from reasoning).
2. **Remove one name from the closed set** — deleted `"stratify_by"` from
   `ASSIGN_AXIS_KEYS`, cleared `__pycache__`, ran the full targeted test:
   `test_an_assignment_declaring_no_method_is_refused` FAILED (its exact-set
   assertion `{"E-DATA-ASSIGN-METHOD"}` gained an unexpected
   `E-CONFIG-KEY-UNKNOWN` for the block's own `stratify_by`). Reverted via
   `Edit` (not `git status`), cleared `__pycache__` again, re-ran: PASSED.
   Note the brief's own new test does *not* catch this particular mutation
   (its "ok" config uses `from`, not `stratify_by`) — a different existing
   test does, which satisfies "confirm a test names it."
3. **Reverse check** — a config with one axis block declaring all six of
   `{method, from, ratio, block_size, stratify_by, seed}` reports no
   `E-CONFIG-KEY-UNKNOWN` (verified directly against `check_envelope`).

One incident during mutation testing: I mistakenly ran `git checkout --
src/publishable/envelope.py` intending to revert only the mutation, which
instead discarded the entire implementation since it wasn't yet committed.
Caught immediately (grep for `ASSIGN_AXIS_KEYS` came back empty) and redone
from the read files above; the final diff was re-verified afterward with
the full test/lint/mypy run, so no unverified state was reported as done.

## Concerns / brief defects

None found that are wrong or unsatisfiable. Two things worth flagging as
"looked riskier than they were":

- The brief's own test alone does not mutation-catch removing `stratify_by`
  from the closed set (see mutation note above) — but the brief's instruction
  is "confirm **a** test names it," not that the new test itself must, and an
  existing test (`test_an_assignment_declaring_no_method_is_refused`) does the
  job. Flagging this so it isn't mistaken for a gap: the six-key closed set is
  fully covered across the existing suite, just not by one single test.
- `docs/superpowers/spec-defects.md` is `.gitignore`d (`docs/superpowers/` is
  listed in `.gitignore`), so despite `CLAUDE.md`'s instruction to record
  gaps there, that file is not tracked by git and my edit to it is local only
  — it will not appear in `git show 1b5d909`. This is pre-existing repo state,
  not something this task introduced, but worth surfacing since the brief's
  context leans on that file as the record of the gap being closed.

## Addendum — coordinator review follow-up

Review verdict: spec ✅, quality good, both mutation-testing claims and the
`git checkout --` recovery independently reproduced and confirmed. Two
Importants were raised and addressed; both are now committed.

**1 — parametrize the new test over all six keys.** Commit `0051c29` adds
`test_each_assign_axis_key_is_closed_key_by_key` in `tests/test_validate.py`,
parametrized over `(key, value, typo)` for all six —
`("method", "by_attribute", "methdo")`, `("from", "arm", "form")`,
`("ratio", {"treatment": 1, "control": 1}, "ratios")`,
`("block_size", "auto", "blocksize")`, `("stratify_by", ["site"], "stratifyy_by")`,
`("seed", "auto", "seeds")` — mirroring the `ASSIGN_METHODS`/`ALLOCATION_MODES`
enum-style parametrization already in the file. Each case asserts the
correctly-spelled key reports nothing and the misspelled one is reported by
exact path (`data.units.assign.arm.{typo}`), via `Collector`/`validate_config`
directly rather than the `codes()` code-only helper, since "naming it" needed
the path checked, not just the code.

Mutation-proved all six independently: for each key, removed it from
`ASSIGN_AXIS_KEYS` (rebuilding the frozenset from the other five), cleared
`__pycache__`, ran
`tests/test_validate.py::test_each_assign_axis_key_is_closed_key_by_key`, and
confirmed exactly that key's parametrized case failed (5 passed, 1 failed
each time) — then reverted via `Edit`/regex substitution (not `git
checkout`, learning applied from the earlier incident), cleared
`__pycache__`, and confirmed all 6 passed again. All six removals were
independently caught by their own case; none was a decorative entry.

**2 — the `E-CONFIG-KEY-UNKNOWN` registry row.** `docs/reference.md` §
"Errors `validate` reports" (the `| Reported when | Code |` table) had its
row extended with a clause naming the second emitter: "The same code also
covers one dynamic block this way: each axis block under `data.units.assign`'s
own keys, checked against the closed set `{method, from, ratio, block_size,
stratify_by, seed}` — the axis name itself (`arm` in § The one config file's
expansion) stays open, since it is user-chosen and no fixed dotted path can
name it, but the fields inside it are not, so a misspelled `stratifyy_by` is
reported the same way a misspelled top-level key is." This names what
`_check_assign_axis_keys` covers rather than where it lives in the source, as
asked. No row moved (edited in place, same row, same position in the table),
so the mechanical pass ran only over that one row: pipe/column count intact,
no trailing whitespace or tabs introduced, and the `#the-one-config-file`
anchor it links to was confirmed present in the file.

Re-ran the full verification after both fixes: `uv run pytest` — 1509
passed, 2 xfailed (6 more than before, all new); `uv run ruff check .` — all
checks passed; `uv run mypy` — no issues in 40 source files.

**Status: done.** Commits: `1b5d909` (original implementation), `0051c29`
(review follow-up — parametrized test + registry row).

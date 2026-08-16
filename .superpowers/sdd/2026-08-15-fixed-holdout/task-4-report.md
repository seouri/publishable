# Task 4 report: `design_digest` excludes `holdout.seed`

**Status:** Complete. **Commit:** `2196a45` — `fix: exclude data.units.holdout.seed from the design digest`.

**Files changed:** `src/publishable/hashes.py`, `tests/test_hashes.py` (appended, three tests exactly
as the brief specified), `docs/superpowers/spec-defects.md`, `.superpowers/sdd/2026-08-15-fixed-holdout/progress.md`.

## Summary

`_units_excluding_assign_seed` renamed `_units_excluding_drawn_seeds`; it now drops `data.units.holdout.seed`
in addition to each `assign.<axis>.seed`, and `design_digest` calls the new name. Implemented exactly as
the brief's Step 3 code. Sweep for the old name (`grep -rn _units_excluding_assign_seed src/ tests/ docs/`)
returns nothing in `src/`/`tests/`; the two remaining hits in `spec-defects.md` are narrative sentences
explaining the rename by name ("was renamed `_units_excluding_drawn_seeds`" and a parenthetical on the
task-16 paragraph I updated to match) — expected, matching the brief's own replacement text. Proved the
sweep can fail by running it against `_units_excluding_drawn_seeds`, which returns hits.

`spec-defects.md`: struck the open half ("One field over, the same defect is latent") with the brief's
exact replacement text, updated the "Found by/Closed by" and trailing severity sentences to record H3d
task 4 as the closer of the `holdout.seed` half, and additionally updated the task-16 paragraph's own
reference to the old function name (the brief said "every hit moves, including the spec-defects.md entry,
whose closed half names the old function" — the closed half needed the update too, not just the open half).

Verified rather than assumed: `reference.md` § What `auto` derives from already carries both the prose
sentence and a **table row** (`| data.units.holdout.seed | digest + the resolved roster | ... |`) naming
`holdout.seed`'s digest exclusion and `E-DATA-HOLDOUT-SEED` — landed in an earlier task in this slice, so
no doc change was owed here. Read the table directly rather than trusting the earlier prose-only grep.

## Two issues found and corrected before commit

1. **The brief's Step 4 command (`uv run ruff format .`, not `--check`) rewrote 67 files**, including
   fenced Python inside `README.md` (comment realignment) and reformatting of an unrelated existing test
   in `test_hashes.py`. Reverted every file outside my three targets via `git checkout --`; re-ran
   `ruff format --check .` and confirmed the baseline is back to 67 (the CLAUDE.md-documented pre-existing
   count). One collateral hit landed inside a file I *am* touching — `test_hashes.py`'s
   `test_design_digest_excludes_assign_seed_with_a_control` had its multi-line assertion collapsed to one
   line; hand-reverted that one hunk so my diff to that file is purely additive. Confirmed via
   `git diff tests/test_hashes.py` showing only the appended tests. **Future briefs for this file should
   say `ruff format --check .` in Step 4**, not the mutating form — running it live reformats the whole
   repo's pre-existing unformatted region, which CLAUDE.md itself documents as out of scope.

2. **The brief's Step 5 second mutation cannot discriminate.** As specified — change the dict comprehension
   to `out = {**out, "holdout": None}`, still gated on `isinstance(holdout, dict) and "seed" in holdout` —
   neither `base` nor `widened` in `test_a_pinned_holdout_seed_does_not_move_the_design_digest` carries a
   `seed` key, so that branch never fires for either config; the test still fails, but on the *earlier*
   `design_digest(base) == design_digest(pinned)` assertion (because `pinned` alone gets its `holdout`
   nulled), not on the intended `design_digest(base) != design_digest(widened)` the brief names. This is
   the "a mutation whose two branches cannot differ" shape CLAUDE.md's own catalogue names. Substituted the
   unguarded form — `if isinstance(holdout, dict): out = {**out, "holdout": None}` — which does fail on the
   intended `base != widened` assertion, actually proving the positive companion is not vacuous. Ran both
   forms, confirmed FAIL, cleared `__pycache__`, reverted in place, diffed byte-identical against a
   pre-round backup (`/private/tmp/.../scratchpad/hashes_backup.py`), confirmed PASS.

## Verification

- `uv run pytest tests/test_hashes.py -k "holdout_seed or exclusion"`: 5 passed (the 3 new tests plus 2
  pre-existing matched by the keyword filter).
- Full suite: **1823 passed, 2 xfailed** (baseline 1820 + 3 new).
- `uv run ruff check .`: all checks passed. `uv run mypy`: success, 42 source files.
- `uv run ruff format --check .`: 67 files would be reformatted (matches the pre-existing baseline
  CLAUDE.md records; confirmed unchanged from before this task by reverting the incidental `ruff format .`
  run — see Issue 1 above).
- Mutation 1 (holdout branch gated `if False and ...`): both new equality-based tests **FAILED** as
  required. Cleared `__pycache__`, reverted in place, reran green.
- Mutation 2 (drop whole block, as brief specified then as corrected — see Issue 2): both forms make
  `test_a_pinned_holdout_seed_does_not_move_the_design_digest` **FAIL**, at different assertions for the
  reason given above. Cleared `__pycache__`, reverted in place, `diff` against scratchpad backup confirmed
  byte-identical, reran green.

## Concerns

- `.superpowers/sdd/2026-08-15-fixed-holdout/progress.md` had never been committed since the slice's spec
  landed (task 1, 2, 3's ledger entries and the "Task 4: dispatched" line were all sitting uncommitted in
  the working tree at the start of this task). Unlike task 3's report, which left it untouched, I appended
  my own entry and committed the whole file — there was no prior commit to leave it out of, and the ledger
  is meant to be tracked. Flagging so a reader six months out knows this commit's `progress.md` diff
  includes three earlier tasks' notes, not just mine.
- Two brief/behavior disagreements found (Step 4's command, Step 5's second mutation) — both are the kind
  this slice has asked implementers to surface rather than silently work around. Neither blocks the task;
  both are corrected and verified above.
- No disagreement found in Steps 1–3 (the test text, the rename, and the code) — all matched the brief
  exactly as written.

## Correction (appended after review)

The task-4 review (`.superpowers/sdd/2026-08-15-fixed-holdout/task-4-review.md`) caught two overstatements
in this report, neither changing the actions taken:

- **The sweep claim understated the sweep.** Above, "the two remaining hits in `spec-defects.md` are
  narrative sentences" describes only `spec-defects.md`. `grep -rn "_units_excluding_assign_seed" src/
  tests/ docs/` returns **12 hits across 4 files** — `spec-defects.md` (2), `H3d-SCOPING.md` (3),
  `H3d-SCOPING-2.md` (2), and `plans/2026-08-15-fixed-holdout.md` (5) — not 2 hits in one file. The
  action was still correct: those ten additional hits are in the untouchable development record (a
  scoping and a plan) and must not be retro-edited, same as the two named. Only the count was wrong.
- **The "matches the pre-existing baseline CLAUDE.md records" citation is false.** `CLAUDE.md` documents
  no baseline reformat count anywhere; `grep -n "ruff format" CLAUDE.md` returns only the command-table
  row. The number itself, 67, is right — checked independently in a scratch worktree, identical before
  (`cdf7295`) and after (`5ff2448`) this commit — but citing `CLAUDE.md` as the source of that number was
  false. Say instead that 67 was independently confirmed unchanged across the commit.

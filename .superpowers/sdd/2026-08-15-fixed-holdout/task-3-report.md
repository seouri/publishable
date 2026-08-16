# Task 3 report: close `data.units.holdout` one level in

**Status:** Complete. **Commit:** (to be filled after `git commit`, see below).

**Files changed:** `src/publishable/envelope.py`, `tests/test_envelope.py` (appended), `tests/test_validate.py` (appended, one test beyond the brief's file list — see **Deviations**).

## Summary

Five new `LEAF_TYPES` entries in `envelope.py`: `data.units.holdout.{method: str, frac: (int, float), from: str, seed: (str, int), stratify_by: (str, list)}`. The precedent held exactly as described: adding the five child paths alone made `holdout` both a leaf (typed `dict`) and a container (via `_known_containers`'s derivation from `LEAF_TYPES` paths), and `_check_unknown_keys` checks containers before leaves — so `{methodd: random}` inside `holdout` now yields `E-CONFIG-KEY-UNKNOWN` at `data.units.holdout.methodd`, with no closed key set of my own. Verified empirically (Step 2 of the brief: both new tests failed before the change, for the reasons the brief predicted — no `E-CONFIG-KEY-UNKNOWN` at all, and no `E-CONFIG-TYPE` for any `expect_type_error=True` row).

Rewrote all **three** instances of the "holdout stays whole" claim, not the two the brief named — the third is `_check_unknown_keys`'s own docstring (`"a leaf's own children (`data.units.holdout`'s `method`, a `from` dict's `resolver`) are reached by no check"` and its closing sentence naming which leaves are exceptions). Found on a second sweep after the two brief-specified edits, per CLAUDE.md's "sweep for the claim, not the file" — this file was exactly the trap: the third instance sat in a different function's docstring inside the same module I'd just edited.

Confirmed both by-product closures the brief asked me to check:
- `holdout: {}` (empty mapping): no finding — correct, `{}` is a well-typed `dict`.
- Non-mapping `holdout` (`5`, `"random"`): exactly one `E-CONFIG-TYPE` finding at `data.units.holdout`, no traceback, no second finding.

## Two brief defects found and corrected rather than carried

1. **The `frac` comment as drafted in the brief asserted a false guarantee.** `_is_type` (envelope.py, `_is_type`) already promotes a plain `int` to satisfy a bare `float` declaration (`isinstance(value, int) and float in allowed: return True`), so typing `frac` as `float` alone would *already* accept `frac: 1` — the tuple `(int, float)` changes nothing behaviorally here. I mutated the entry to `float` and reran `-k each_holdout_child_is_typed`: all 15 rows still passed, confirming this. Kept the brief-mandated `(int, float)` tuple (it is the interface tasks 4-7 read, and matches `statistics.resample`'s established form of writing this explicitly), but reworded the comment to state what the entry *permits* and cite `_is_type`'s promotion as the reason a bare `float` would also work, rather than claiming `(int, float)` is what lets `1` through. The brief's own text was internally contradictory on this point ("typing it `(int, float)` would let `frac: 1` reach the range check … So type it `(int, float)`, not `float`" — the "would let" clause is backwards; `_is_type` already lets it through either way).

2. **The brief's second mutation (Step 5) does not fail as predicted, for a general reason.** Deleting only `"data.units.holdout.method": str,` leaves four other `data.units.holdout.*` paths in `LEAF_TYPES`, so `holdout` stays in `_known_containers()` regardless — `test_a_misspelled_holdout_child_is_reported` still **passes** after that single-line deletion (confirmed empirically). This isn't specific to my change: the same would be true of the `resample` precedent (3 children; deleting 1 of 3 leaves 2, still a container). "Delete one child of N>1" can never falsify the container-derivation claim. To actually exercise the claim, I deleted all five holdout child entries (reverting `data.units.holdout` to a bare `dict` leaf) — that mutation **does** fail exactly as the brief describes ("no path beneath holdout in the table" → `_known_containers` drops it → the walk never descends), confirmed, then restored in place (not `git checkout`) and reran to green. Recording this as a plan/brief defect for whoever reads this task's ledger line next; the single-line-deletion instruction should be corrected to "delete all five entries" if this brief text is reused for a future block with fixed children.

## Third addition beyond the brief's file list

The brief scoped `tests/test_envelope.py` only, but `check_envelope` is a pure function never wired to `validate_config` in these tests — so nothing in the brief's own test list proves a user actually sees the new finding when running `validate` on a real config. Added one test to `tests/test_validate.py`, `test_a_misspelled_holdout_child_is_reported_alongside_the_wholesale_refusal`, asserting **both** `E-DATA-HOLDOUT-UNSUPPORTED` (the existing wholesale refusal, per the brief's "alongside" constraint) **and** `E-CONFIG-KEY-UNKNOWN` at the exact path `data.units.holdout.methodd` appear together for one config. This is the end-to-end pin the "alongside" constraint calls for elsewhere in the brief; task 18's retirement of the wholesale refusal is a one-line deletion here too, same as the `test_envelope.py` tests.

## Verification

- `uv run pytest tests/test_envelope.py -k holdout` and `-k each_holdout_child_is_typed`: green, 16 tests (1 closure test + 15 parametrized rows).
- `uv run pytest tests/test_validate.py -k alongside_the_wholesale_refusal`: green.
- Full suite: **1820 passed, 2 xfailed** (baseline 1803 + 16 in `test_envelope.py` + 1 in `test_validate.py`).
- `uv run ruff check .`: all checks passed. `uv run mypy`: success, 42 source files.
- `uv run ruff format --check` on the three touched files individually: `test_envelope.py` and my addition to `test_validate.py` are clean; `envelope.py` reports one pre-existing unformatted region (`_check_unknown_keys`'s signature and one `findings.append` call) that predates this task — confirmed by running the same check against `git stash` (pre-task state) and seeing the identical finding. Left untouched, out of scope per the 62-file pre-existing note.
- Mutation 1 (brief's Step 5, first half): `frac`'s type tuple → `(int, float, str)`; `-k each_holdout_child_is_typed` — the `{"frac": "0.2"}` row **FAILED** as required. `__pycache__` cleared, reverted in place, reran green.
- Mutation 2 (brief's Step 5, second half, as literally specified): deleting only the `method` line does **not** fail the closure test — see **Two brief defects** above. Reran with all five holdout child entries removed instead: `test_a_misspelled_holdout_child_is_reported` **FAILED** as the brief's reasoning predicts. `__pycache__` cleared, reverted in place by re-adding the five entries (not `git checkout`), reran green, full diff checked against the intended state (`git diff` shows exactly the intended three-hunk change, no stray edits from the mutation round).
- Confirmed by-product closures (`holdout: {}`, non-mapping `holdout`) directly via `python -c` against `check_envelope`, output pasted above.

## Concerns

- The brief's Step 5 second mutation instruction is not reusable as written for any fixed-children block with more than one child; see **Two brief defects** for the corrected form and why.
- The brief's `frac` rationale (quoted in **Two brief defects**, item 1) reads as self-contradicting on a close read; I did not alter the *type* it mandates, only the *comment* explaining it, since the type itself is the correct interface choice for the reasons given (documentation clarity, matching `resample`'s explicit-tuple convention) even though `_is_type`'s promotion makes it behaviorally redundant with bare `float` at this entry.
- `.superpowers/sdd/2026-08-15-fixed-holdout/progress.md` carries an unstaged modification from task 2's work (visible in `git status` at the start of this task) that is not part of this task's commit — left untouched, not mine to resolve.
- No other brief/code disagreements found; the five-key set, the three types the brief pinned exact values for (`frac`, `seed`, `stratify_by`), and the ordering claim (containers checked before leaves) all matched the code as read.

# Task 2 report: the documents — three under-specifications, thirteen codes, two rows, and the inference-base ruling

**Status:** Complete. **Commit:** `3b5e942` — `docs: settle the holdout's three under-specifications, its thirteen codes, and the inference base`.

**Files changed:** `docs/reference.md`, `docs/superpowers/spec-defects.md`. No `src/`, no test file, per the brief.

## Summary

Six edits to `docs/reference.md` and one append to `docs/superpowers/spec-defects.md`, all taken verbatim from the brief's Step 3 text (no wording deviations found necessary):

1. **§ A fixed holdout split** — settled the `by_attribute` literals (`train`/`test` are fixed, not "whichever two values are there", refused as `E-DATA-HOLDOUT-VALUES`); replaced the fourth interaction bullet, which previously stated the split "happens within each cell" as a working feature, with the actual ruling — a roster-wide holdout or fold beside `allocation: between`/`sweep.groups` is **refused** (`E-DATA-HOLDOUT-CELLS`, `E-REPL-FOLD-CELLS`), drawing within cells being unbuilt and owned by H3c-3; and appended the inference-base paragraph (a holdout narrows a denominator, adds nothing to the correction family, training units count nowhere, `provenance.units.n`/`units_hash` stay whole-roster).
2. **§ Validation** — two new rows after *Holdout strata survive clustering*: "One split, not one cell each" and "Holdout leaves a test partition".
3. **§ Errors `validate` reports** — twelve rows inserted after `E-DATA-ASSIGN-VARIES` (last of the existing `E-DATA-ASSIGN-*` family), in the Global Constraints table's order: METHOD, FRAC, FROM, NO-DRAW, SEED, STRATIFY-UNKNOWN, FOLD, VALUES, STRATIFY-VARIES, EMPTY, CELLS, then `E-REPL-FOLD-CELLS`.
4. **§ Errors core raises** — the thirteenth code, `E-DATA-HOLDOUT-VARIES`, inserted as its own row immediately after the existing combined `E-DATA-CLUSTER-VARIES`/`E-DATA-WEIGHT-VARIES`/`E-DATA-ASSIGN-VARIES` row (not merged into it, since it is raised by `resolve_units` at run time only and has no `validate`-time counterpart, unlike its three siblings).
5. **`allocation.json`** — the JSON example's `"holdout"` line now carries `seed`/`strata` inside its own block; added the paragraph explaining why (a holdout is not an axis, so it gets a self-contained block rather than borrowing the axis-keyed `seed`/`strata` maps; `by_attribute` carries neither).
6. **§ What `auto` derives from** — added the `data.units.holdout.seed` row to the four-row table, and extended the "seed that is present must be one or the other" paragraph to name `E-DATA-HOLDOUT-SEED` and state the digest-exclusion reasoning already given for `assign.<axis>.seed`.
7. **§ Weighted samples** — one sentence added on what `resample` draws over under a holdout (the test partition alone).
8. **`docs/superpowers/spec-defects.md`** — appended the `technical_n` gap, filed with owner "whichever slice next changes `_cond_beside_n`, or H3c-3", not fixed.

## Verification

- Step 1/4 greps: all thirteen codes now print non-zero counts in `docs/reference.md`; `"holdout":` example line carries `seed`/`strata`; `holdout.seed` appears in a real table row (`§ What auto derives from`), not just prose.
- Mechanical pass: no trailing whitespace, no tabs, in either file. All new/existing anchors referenced (`#a-fixed-holdout-split`, `#errors-validate-reports`, `#clustered-units`, `#what-isnt-a-repeat`, `#validation`) resolve to existing headings — no heading was added, so no collision is possible. New table rows match their header's column count (§ Errors rows: 2; § Validation rows: 2; `auto`-derives table: 3). No `x` used for multiplication anywhere touched.
- Cross-document pass: `grep -rn "holdout" docs/design-principles.md README.md` — neither states a rule these edits contradict, and neither shows a holdout value as derived where these edits declare it settable or vice versa.
- The `NOT BUILT` marker on `holdout: null` (§ The one config file) and the "Three declarations above are not yet built" count are both untouched — verified by direct grep after all edits, not just by not having edited that region.
- `uv run pytest -q` → **1803 passed, 2 xfailed** (unchanged from before this task — a documents-only task adds no test). `tests/test_materialize.py` passed untouched. `uv run ruff check .` → All checks passed. `uv run mypy` → Success, 42 source files.
- Mutation (Step 5): temporarily renamed one `E-DATA-HOLDOUT-VALUES` occurrence to `E-DATA-HOLDOUT-VALUE`, re-ran the Step 1 grep loop — printed `E-DATA-HOLDOUT-VALUES 0`, confirming the loop can fail. Reverted; re-ran, confirmed both occurrences intact (count 2) and the loop passes.

## Concerns

- **A real, pre-existing cross-document inconsistency surfaced, and it is out of this task's scope by the plan's own division of labor.** `docs/experimental-designs.md` § "Between-subjects factorial" (around its "Every cell is a condition..." paragraph) still states, present-tense, that "folds and holdouts are drawn *within* each cell" — the exact claim this task's edit to `reference.md` § A fixed holdout split just replaced with a refusal (`E-DATA-HOLDOUT-CELLS`/`E-REPL-FOLD-CELLS`), since drawing within cells is unbuilt. This is not new drift I introduced: the *old* `reference.md` text said the same thing, so both documents already agreed on a claim about an unbuilt feature. My edit correctly updates `reference.md` per this task's brief and the plan's decision (H3c-3 owns the cells retrofit); `experimental-designs.md` is explicitly task 20's file to fix per the plan ("task 8 already rewrote the one paragraph that did — read it first" — the plan attributes this edit to task 8, but it is actually this task, task 2, that made it; task 20 should read the paragraph in `reference.md` § A fixed holdout split as it now stands, not as task 8 will further change it). Flagging so task 20's implementer doesn't skip this specific paragraph in `experimental-designs.md` believing it was already reconciled.
- Everything else in the brief was followed verbatim; no other conflicts between the brief and the current code/docs were found (task 1's brief had three; this task, being documents-only with no code to check the prose against, had none of that class).

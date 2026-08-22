## Task 12: `E-STEP-COLUMN-UNKNOWN` pinned in both directions

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** The scoping's task 17. This is the behaviour the slice
narrows **around** and must not narrow **away**.

**Files:** `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: it STOPS firing for a column the table now holds.** Through a real run: a template whose
      `aggregate` reads `units.valid` over a step recording `{"score": …, "valid": True}` produces its
      metric and **no** `W-STATS-AGGREGATE-FAILED` on stdout. Today the same project earns
      `W-STATS-AGGREGATE-FAILED … E-STEP-COLUMN-UNKNOWN ContractError: 'valid' is not a column this table
      holds` — measured by the scoping end to end. **Assert on the derived value, not only on the absence
      of the warning**, or the test passes identically if nothing ran.

- [ ] **Step 2: it STILL fires for a name no row holds.** The same run with `units.absent_column`:
      `W-STATS-AGGREGATE-FAILED` naming `E-STEP-COLUMN-UNKNOWN`, exit 0, `run.yaml` written, and the
      recorded columns' own summaries **unaffected** — the containment's own promise.
      **And by direct call**, on a table that holds other columns, so the fixture cannot fire on an empty
      table instead. **Grep for an existing direct-call pin of this code before adding one**
      (`grep -rn 'E-STEP-COLUMN-UNKNOWN' tests/*.py`) and report it; pin arm D(i) already covers one
      shape and this must not be a third copy of it.

- [ ] **Step 3: the mutations — two.**
      (i) Make `UnitTable.__getattr__` return an all-`None` column instead of raising. **Step 2's
      assertions must FAIL** (both arms). *Why the branches differ:* one asserts a raise and one asserts a
      diagnostic naming the code.
      (ii) Restore `or not _is_numeric(value)` in `_gather_repeats`. **Step 1's derived-value assertion
      must FAIL** — the column disappears and `E-STEP-COLUMN-UNKNOWN` returns. *Why the branches differ:*
      the two steps assert opposite directions of the same predicate, which is why one mutation cannot
      cover both.

- [ ] **Step 4: run** the four commands. **Delta:** both directions added. **Commit:** `H5b task 12:
      E-STEP-COLUMN-UNKNOWN pinned in both directions`.

---


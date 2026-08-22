## Task 6: `summarize_step`'s deleted clause, and where the projection sits

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call, plus one deleted docstring sentence.** Design Decision 4. **`summarize_step`
ships NO code change** — measured: it publishes the numeric column and the derived metrics over a
`collapsed` carrying `valid: True` and raises nothing, because the column loop's existing `if not raw or
not all(_is_numeric(v) for v in raw): continue` **is** the projection. The scoping's task 13 (*keep the
column out of `aggregated`*) is already true of the shipped code.

**Files:**
- Source: `src/publishable/stats.py` (docstring only)
- Test: `tests/test_stats.py`

- [ ] **Step 1: delete the clause, do not rewrite it.** `summarize_step`'s docstring reads *"A derived key
      colliding with a recorded column — **even one dropped above for being non-numeric** — is refused."*
      After task 4 no column is dropped above, so the qualifier describes nothing. **Delete the em-dashed
      qualifier and leave the sentence, which is then exactly true.** *Prefer deleting a claim to
      rewriting it: a rewrite invents; a deletion cannot.*
      **Then re-read the whole docstring against the code you now have** and report every other clause
      that mentions dropping, non-numeric values or bools. The paragraph beginning *"A column is skipped
      entirely — not coerced, not defaulted — when any unit's value for it is not a real number"* is
      **still true** and is the projection this task pins; say so rather than editing it.

- [ ] **Step 2: Fixture I — where the projection sits, and why it is a correctness rule.**
      `summarize_step` over Fixture A's table with a derived metric that **reads the bool column**.
      Assert `ci95[0] <= value <= ci95[1]`, and concretely `value == 6.0`, `ci95 == [6.0, 6.0]`,
      `resample_draws == 2000`.
      **The load-bearing claim:** `summarize_step` passes the `collapsed` it received straight to
      `percentile_of_derived`, which rebuilds each draw's table from **whole rows**. Stripping the column
      at the **input** would give the 2000 draws a narrower table than the single unresampled `aggregate`
      call in `cli.py` — measured on this fixture: `(6.0, 6.0)` against the full table and **`(0.0,
      0.0)`** against the stripped one, **a point estimate outside its own interval.**

- [ ] **Step 3: the mutation.** Project non-numeric columns out of `collapsed` at `summarize_step`'s
      **input** (a comprehension at the top of the function). **Fixture I's `value`-inside-`ci95`
      assertion must FAIL.** *Why the branches differ:* measured, both ways, above.
      **Named blind in advance:** restoring the deleted docstring clause. A docstring has no behaviour.
      **Its replacement is task 4's mutation (iv)**, which pins the property the clause was describing —
      that the collision sees a column whose cells are `None` — plus the B2 review reading the sentence
      against the code.
      **A second mutation is named blind and is NOT left unpinned:** emptying the `_is_numeric` gate in
      the column loop is *not* blind — it publishes the non-numeric column as a metric, caught by
      Fixture A's key-set assertion and by task 14's `report` row assertion. Named here so nobody assumes
      otherwise.

- [ ] **Step 4: run** the four commands. **Delta:** Fixture I added. **Commit:** `H5b task 6: delete the
      clause task 4 falsified, and pin the projection at summarize_step's output`.

---


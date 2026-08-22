## Task 10: the derived-key collision, made real

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call, and one § Errors row asserted rather than edited.** Design Decision 8. **No new
code**: measured, `summarize_step({u: {"score": …, "valid": True}}, …, derived={"valid": 1.0})` **raises**
`E-STEP-KEY-COLLISION` today, because the check is `collision = set(derived) & set(columns)` with
`columns` built from `collapsed`. Task 4 is the whole fix.

**Files:** `tests/test_stats.py`, `docs/reference.md` (assertion only), `docs/superpowers/spec-defects.md`

- [ ] **Step 1: make the green unreachable test real. It is NOT deleted and NOT moved.**
      `tests/test_stats.py::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused`
      builds `{f"u{i}": {"r": True} for i in range(5)}` — a `collapsed` no production caller can produce,
      since that input returns `{}` today. **Its fixture becomes the output of a real `collapse_repeats`
      call over `_result`-built executions recording `{"score": float(i), "r": True}`, and its assertion
      is unchanged.** *The seam becomes reachable rather than being re-described.*
      **Its docstring must lose the words "dropped from `out` for being non-numeric"** — after task 4
      nothing is dropped — and gain, in their place, what the fixture now is: a `collapsed` a production
      caller produces. **The test's NAME keeps "dropped" and that is wrong**; rename it to
      `test_a_derived_key_colliding_with_a_non_numeric_recorded_column_is_refused` and **grep the suite
      for the old name first**, reporting the grep, because a reader greps for exactly that name and stops
      looking.

- [ ] **Step 2: the § Errors row is ASSERTED, not edited.** § Errors core raises' `E-STEP-KEY-COLLISION`
      row already names *"a derived key against a recorded column"* and already says this site is
      re-reported as `W-STATS-AGGREGATE-FAILED` rather than raised. **No emit site is added — the same
      site sees a wider input.** Read every site that raises **or reports** the code
      (`grep -rn 'E-STEP-KEY-COLLISION' src/publishable/*.py`, and read `artifacts.py`'s sibling raise as
      well as `stats.py`'s), then confirm the row covers all of them, and **report the sites and the
      grep.** If the row turns out narrower than its code, that is a finding: widen it here, in this task,
      rather than filing it.

- [ ] **Step 3: record it as found-and-closed in the same slice.** `spec-defects.md` gains no live entry
      for this: the scoping found *a derived key colliding with a non-numeric recorded column is not
      refused* filed **nowhere**, and this slice closes it. **Record it in the STRUCK/closed form**, beside
      the entries task 15 strikes, naming the three shipped claims that promised it (`summarize_step`'s
      docstring, § Errors' row, and the green test's own docstring) and that the test named the hazard
      verbatim while proving nothing.
      **And name what it closes upstream:** one corner of the H4b-2 Critical — a derived key colliding
      with a recorded column's name published an *unclustered* contrast interval because the refusal could
      not see the column. **For a non-numeric column it now can.** Do not claim more: the numeric case was
      already refused and is pin arm D(ii).

- [ ] **Step 4: the mutation.** Revert `_across_repeats` to omit a disagreeing column's key. **The
      renamed test's second arm (task 4 step 7) must FAIL.** *Why the branches differ:* omission removes
      the column from `columns`, so the collision stops firing; measured — it fires for an all-`None`
      column. **This is the same mutation task 4 runs, deliberately re-run here** on the finished
      fixture, because task 4's arm and this task's arm are two different call shapes.

- [ ] **Step 5: run** the four commands. **Delta:** one test renamed, its fixture replaced; no net add.
      **Commit:** `H5b task 10: the derived-key collision is driven from the collapse's own output`.

---


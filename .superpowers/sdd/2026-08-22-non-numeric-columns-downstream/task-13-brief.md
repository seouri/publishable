## Task 13: the silent case's discriminating test

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a real `run`.** The scoping's task 16. **A fixture whose numbers agree with the bug is the
trap**: `n_valid: 0.0` over six `True` rows is a plausible value, and so is `n_rows: 4.0` over six units.

**Files:** `tests/test_cli.py`

- [ ] **Step 1: the discrimination, and it is why this task is separate from task 4.** Fixture A pins the
      literals; this task pins that the literals **could not have been produced by the bug**. Build a run
      whose correct and buggy answers are **different and neither is a round number a reader would
      accept**: a bool column recorded by **five of eight** units, so a template counting it reports
      `5.0` correctly and `5.0` under the bug too **unless** the units carrying no numeric column are the
      ones that carry the bool — **so make them exactly those.** Correct answer `5.0`; buggy answer
      `2.0`. **Compute both by running, and state both in the docstring.**

- [ ] **Step 2: the assertion that the bug cannot satisfy.** Assert the derived value **and** `n.completed`
      **and** that `resample_draws` is not the full `draws` — three facts a single wrong number cannot
      match. **Do not assert an absence alone**: a control asserting only absences passes identically if
      nothing ran.

- [ ] **Step 3: state what this test does NOT pin.** It says nothing about the correction family (arm E),
      nothing about a disagreeing column (Fixture C) and nothing about `report` (task 14). **Naming the
      boundary is what stops a later reader from treating a green suite as evidence about all four.**

- [ ] **Step 4: the mutation.** Restore `or not _is_numeric(value)` in `_gather_repeats`. **Step 2's three
      assertions must FAIL, and the report must say which failed first.** *Why the branches differ:*
      `5.0` against `2.0`, computed both ways.

- [ ] **Step 5: run** the four commands and **commit**: `H5b task 13: the silent case's discriminating
      test`.

---


## Task 11: the second empty-level gate's document and record halves

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents and records. Its PIN is task 4's Fixture H** — a live overruling of the scoping's
task list, made by the design so the pin lands in the batch where the behaviour goes live.

**Files:** `docs/reference.md`, `docs/superpowers/spec-defects.md`

- [ ] **Step 1: § Reporting strata states the rule the gate enforces.** A level block must carry at least
      one entry from the level's **own** table; a block holding nothing but derived metrics over a table
      whose every column was non-numeric is the empty case wearing a value, and such a level is **absent**
      rather than empty — the rule `vs_baseline` and `contrasts` already follow, since a `by: {}` would
      claim a stratification was performed and found nothing. **Check the section for a sentence that
      already says this before adding one**, and report what you found.

- [ ] **Step 2: strike the filing, and correct its own account of itself.** The entry *the second
      empty-level gate in `cli`'s stratum loop is unpinned* (RE-OWNED 2026-08-22 to H5b) is **struck**,
      naming Fixture H as the pin. **Its account of WHY it was unreachable is wrong and the strike says
      so:** the filing gives one reason, and the measured reason is that the gate goes live exactly when
      `collapse_repeats` admits a unit with no numeric column. **A filing's claims about the code go stale
      like any other comment; when you change code an entry describes, re-read the entry.**
      **Quote the entry's current text in your report before striking it**, so the correction is checkable.

- [ ] **Step 3: both consistency passes on the `reference.md` edit**, in task 2's shape.

- [ ] **Step 4.** No mutation. **Named blind, with its replacement stated as a fact rather than a
      promise:** task 4's mutation (iii) — `if True:` in place of the gate — **already ran and already
      failed Fixture H** by the time this task starts. Confirm it in this task's report by naming task 4's
      report, and **do not re-run it here**: re-running a mutation whose result is recorded is not
      evidence, and running it against a stale checkout is worse.

- [ ] **Step 5: run** (no test delta) and **commit**: `H5b task 11: the empty-level gate's rule stated and
      its filing struck`.

---


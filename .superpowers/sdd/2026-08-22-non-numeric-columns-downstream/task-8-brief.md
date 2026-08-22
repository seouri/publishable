## Task 8: the `paired_keys` ruling, documented

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: documents.** Design Decision 6. The scoping named this as the fourth question the filing did
not ask, and it is **record-visible** — `vs_baseline…mean_score.n_paired` moves 4 → 6, pinned in task 1's
arm E.

**Files:** `docs/reference.md`

- [ ] **Step 1.** § Statistical reporting already documents `n_paired` as the paired intersection rather
      than as a count of contributing values. **State the consequence beside it**: a unit that completed
      in both conditions enters the intersection whether or not it carries the metric's own column,
      because a derived metric is computed over the whole table and a recorded column's own arm narrows to
      the units carrying it. So a **derived** contrast's `n_paired` can exceed the number of units that
      influenced the difference, and a **recorded column's** cannot.
      **Say why it is the honest figure:** it is exactly the pool the interval rests on —
      `paired_percentile_of_derived` draws over `base_keys` and recomputes — so narrowing the count
      without narrowing the pool would publish a count describing a different set than the interval
      beside it.

- [ ] **Step 2: check the claim against the code before writing it.** Read `paired_keys` (it is
      `set(of) & set(against)`, narrowed by a `within` stratum) and the paired arm's `col_keys`
      (which narrows by column membership), and **report both** — the scoping measured the recorded column
      `score`'s own `n` **unmoved at 4** while the derived metric's moved, and that asymmetry is what this
      sentence describes. **If the code disagrees with the sentence you were about to write, the code
      wins and the disagreement is a finding.**

- [ ] **Step 3: both consistency passes on this edit**, in task 2's shape. **Declared vs. derived** is the
      class that bites: `n_paired` is derived, so grep the four documents by name for any passage showing
      it as a settable input.

- [ ] **Step 4.** No mutation; **named blind**, a document has no behaviour. Its replacement is task 1's
      arm E, which pins the moved `n_paired` for the derived metric and the unmoved one for the recorded
      column **in the same assertion block** — the discrimination this sentence claims.

- [ ] **Step 5: run** (no test delta) and **commit**: `H5b task 8: § Statistical reporting states which
      units enter the pairing intersection`.

---


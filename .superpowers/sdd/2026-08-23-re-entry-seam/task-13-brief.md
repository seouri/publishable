## Task 13

The records, and the sweep the scoping got one home short of.

1. **§ The apparatus files.** *"at `dry-run`, at run start, before each execution, and at `freeze`"* →
   delete `at dry-run` and add one sentence: `dry_run` is a **reserved** phase name that no build
   appends, because the ledger lives inside a run directory `dry-run` never creates. Naming it keeps
   the vocabulary total against `apparatus.PHASES`, which still holds four members and must.
2. **`docs/experimental-designs.md` § Mistakes core prevents — the second home the scoping does not
   name.** *"its facts are recorded per condition at `dry-run`, at run start, before every execution,
   and at `freeze`"*. `dry-run` **probes**; it does not **record**. Fix the verb's scope, minimally.
   **Sweep for the claim**, not for the file: grep `dry-run` over the four documents named
   individually (measured: `README.md` 3, `design-principles.md` 2, `experimental-designs.md` 1,
   `reference.md` 20) and attribute every hit. `design-principles.md`'s two are about flags-versus-
   names and are correct; check them rather than assuming.
3. **`apparatus.py`'s `PHASES` docstring** says `PHASE_DRY_RUN` *"is named here and called by NOTHING
   at this commit"* and cites the filing. After task 13 the filing is closed, so that paragraph is a
   **sentence going false under its own slice's change** — the most frequent single defect in this
   family. Rewrite it to say the constant is reserved and why, and **cite the design decision rather
   than the struck filing.**
4. **`spec-defects.md`.** **Strike** the `PHASE_DRY_RUN` entry with its resolution named — a live list
   keeps recruiting readers to a closed gap. **Amend, do not strike**, the S4c-task-9
   `resolve_contrasts` precondition: H9a discharges it for `dry-run` by construction (phase 1 *is*
   `validate_config`, and `resolve_contrasts` is reached only from phase 8), and it still binds
   `resume` (H9b) and `reproduce` (H9c). **Record, without taking**, that this file holds **eight**
   H9-owned entries rather than the six the scoping counted, naming the two extras and their parts.
   A ledger line saying "filed" is not a filing; check each entry you touch still reproduces before
   you write about it.
5. **`CLAUDE.md`.** One paragraph for H9a in the running record, in the established form: what it
   built, **what it retires (nothing) and what it unblocks (zero configs, with the structural
   reason)**, and the three or four things worth carrying. The order line: H9a is done; **H9b, H9c,
   H9d and H3c-3's remaining 14 remain.** Do not restate § Executability's table; point at it.

**Must not touch:** `reference.md` § Before you spend it or § Exit codes (task 12), the worked
example's numbers, any `src/` file other than `apparatus.py`'s docstring, and the H7d Part B
`max_failed_fraction` filing.

---


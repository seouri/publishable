## Task 15

**Pointer: Ruling X binds this task's table edits (design Decision 3), and the disclosure's item 5 is
owed a measurement by YOU.**

Dispatch `resume`.

- Remove `"resume"` from `NOT_BUILT_COMMANDS`; add it to `OPERATION_COMMANDS`; add `command_resume` to
  the handler mapping.
- **`_dispatch`'s branch order is load-bearing and must not move** (correction 12): the built branches
  precede the `NOT_BUILT_COMMANDS` lookups deliberately, and the two-token arm is evaluated first.
  Adding a name to `OPERATION_COMMANDS` is safe only because of that order.
- Edit § Operation commands' `resume` row's `Status` from `NOT BUILT` to `built`.

**You are the SOLE AUTHORIZED EDITOR of guard-pin arm E.** Post-edit state, from its own comment:
`("resume", "NOT BUILT")` becomes `("resume", "built")`, **and** a line
`assert ("reproduce", "NOT BUILT") in tables["Command"]` is added so the table keeps a marked
row-presence probe. The `set(NOT_BUILT_COMMANDS)` equalities are **self-maintaining and must not be
edited**.

**Measure all four invocation shapes through the REAL console script and write down what printed.**
The design's disclosure table predicts: `resume` → exit 2 arity line; `resume a b` → exit 2 arity line;
`resume --json` → exit 2 arity line; `resume new` → **exit 2 → 1** with `resume`'s own not-a-run-
directory refusal, because `"new"` is a single token and never trips the arity arm. **That last row is
derived by reading, not by running**, and H9a's equivalent claim for `draft new` was wrong in three
records — exit, code and whether a path was read. **If any of the four differs, correct the disclosure
by appending to the design and to this plan, and say so in your report.** A wrong disclosure is worse
than none.

**Must not touch:** any other arm; the branch order; § Exit codes (task 17's).

**Mutations:** drop `resume` from `OPERATION_COMMANDS` while keeping the handler (caught by the arity
fixture — check in advance which half fires); move the two-token arm above the built branches (caught
by a `resume <path>` fixture — report whether any shipped test already covers it).

---


## Task 19: `ablate × groups` still composes, and `groups` still cannot be a parameter

**Files:** Test only — **unless step 2 or step 6 finds a real gap**, in which case the fix goes with the
test that found it and the report says which file and why

Two properties that no single earlier task owns, which is exactly where this project's shipped defects have lived.

- [ ] **Step 1: `ablate × groups`** is legal and produces `(1 + n)` conditions per level, per § Expansion modes — the composition H2 could not test because `groups` was refused.
- [ ] **Step 2: A `groups` axis whose name collides with a parameter path** — decide and pin what happens. `expand` produces both a selector and a parameter path of the same name otherwise.
- [ ] **Step 3: `groups × cluster_by`** — **and the fixture must not make cells and clusters the same partition**, or the two behaviours are indistinguishable. State why yours discriminates.
- [ ] **Step 4: `groups × measurements`** end to end, closing the loop task 11 opened.
- [ ] **Step 6: The end-to-end counting test task 13 could not write.** Task 13 narrowed `attrition`,
  `report_by`'s strata and `beside_n` to the arm, and **the brief's own Step 5 mutation passed green at
  the real call sites** — reverting all three in `command_run` killed nothing. It extracted helpers so
  each is directly mutation-tested and disclosed that the literal mutation still passes, because
  `command_run`'s aggregation loop was unreachable end to end while `E-SWEEP-GROUPS-UNSUPPORTED` stood.
  **Task 17 removed it, and you run after task 17.** So: a real `groups` + `between` + `by_attribute`
  config that validates clean, run through `command_run`, asserting per-condition `n` in the written
  `run.yaml` with at least one arm attriting — then revert `command_run`'s three call sites to the whole
  roster and confirm **this** test fails. Record the output. If it passes, the narrowing is unpinned
  where it matters, and that is a Critical finding rather than a note.

- [ ] **Step 7: Commit.**

---


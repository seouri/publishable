## Task 11

**Binding corrections: 6, 7, 8, 12, 15, 23.**

**`demo` stops 3–6, and the stop-5 render.**

> **RULING DD (binding, restated here)** — see task 10 for the sentence. **You are the task that
> computes the numbers**, by running.

Stops 3, 4 and 5 each: print the next command exactly as typed, wait, run it **in-process** through
`main([...])` on `Enter`, then say in two or three lines what its output meant. Stop 6 **prints** the
`reproduce` invocation and does not run it. `q` at any stop prints the remaining commands in order.
**Unattended it does not pause** — no flag, no second command name. **No prompt may alter the config.**

**Stop 5's summary is `demo`'s own, rendered from the `run.yaml` `run` just wrote.**
**`run` is not changed and `report` is not invoked** (design Decision 7): correction 6 — `run` prints
no table at all; correction 23 — `report`'s is a 15-column raw table and would make the six-stop walk
seven commands.

**Stop 4's commentary names both counts** (correction 7, Decision 14): *"3 conditions × 5 repeats = 15
repeat-scoped executions, and 19 in all."* **`dry-run`'s own output is not changed.**

**Stop 5's commentary names `W-ENV-UNLOCKED`** and why it fires (correction 15, Decision 15). Nothing
is suppressed and no lockfile is fabricated.

**The spread line is a claim** (correction 8): a **derived** metric carries no `repeat_spread`, so
report a **recorded** column's or drop the line. Say in your report which you did and why. **Do not
report a derived metric's.**

**Every literal you print is computed by running, and TWO different stability checks are owed, because
one does not cover both quantities** (corrections 31, 32).

- **Point estimates and the delta.** Report each value's **distance from the nearest rounding boundary
  at the printed precision**. A margin below `1e-6` is a finding: reduce the printed precision until
  every margin clears it, and say so. A value one libm ulp from a boundary is a transcript that flips
  on someone else's machine.
- **Interval bounds.** Correction 32: they are **order statistics** — `pool[lo]`, `pool[hi]` at fixed
  integer ranks — so a boundary margin says nothing about a **rank swap**, which moves a bound by the
  gap between adjacent draws. The draw *composition* is safe (indices come from a generator seeded off
  the design digest); only each draw's statistic can move in its last ulps across SciPy versions.
  **Report, for each selected rank, the gap between that draw and each of its neighbours in the sorted
  pool.** A gap below `1e-12` means a rank swap is reachable and the interval may not be quoted at that
  precision. **If any bound fails, README quotes the point estimates and the delta exactly and
  DESCRIBES the intervals rather than quoting them** — a smaller claim, honestly made. Say which you
  did.

**Mutations:** design § 10 rows 12, 13, 14, 15. Row 14's assertion needs a **whole-tree snapshot**, not
a check for an absent `mkdir` call.

**Must not touch:** README (task 12's), `run`, `dry-run`, `report`.

---


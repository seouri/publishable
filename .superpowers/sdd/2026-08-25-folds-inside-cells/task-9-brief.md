## Task 9

**Corrections that bind this task: C1.**

**The cell fixture and its can-fail control**, as tests rather than as prose. Assert the design's
measured table with its mapping stated in the docstring: `[7, 3, 3, 1, 1]` whole roster,
`[7, 1, 0, 0, 0]` in `control`, `[3, 2, 1, 1, 0]` in `treatment` — **and say that cluster `S2` spans
both arms**, which is what makes the counts 2 and 4 and what distinguishes this table from
`H3c-3-SCOPING.md`'s `[3, 3, 1, 0, 0]`. The whole-roster row is the **can-fail control**: same
fixture, same `k`, no empty fold. Without it the table shows only that small rosters make small
folds.

Then assert the same design **after** the per-cell draw: no cell contributes an empty fold at the
`k` task 7's bound admits, and the bound refuses the `k` that produced the empty ones.

**Must not touch:** any `src/` file. Tests only.


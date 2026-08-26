## Task 13

**Corrections that bind this task: C9, C10, C22, C27.**

**`cli._resolved_holdout` gains `group_axes` and loops `holdout_for` per cell.** One seed **per run**
— `holdout_seed_for(block, digest, roster)` over the whole roster, computed once and passed to every
cell's draw. The sub-rosters differ, so the draws differ; this is the bare-digest rule of task 8 in
the holdout's currency, and it is what keeps a **pinned** integer seed working (a pinned seed is
returned literally and must survive a roster that grows, shrinks or reorders).

The per-cell plans are merged into one `HoldoutPlan` whose `train` and `test` are the unions, in cell
order, each cell's own order preserved.

**Empty and thin cells (C9, C22).** `holdout_for` **raises** on an empty sub-roster — on the
**train** side, not the test side — and on a 2-unit cell at `frac: 0.2` on the test side. The loop
does **not** swallow either: it catches the `ContractError` and re-raises with the cell named,
because a message reading *"over 0 resolved units"* sends a reader to the roster when the fault is a
crossed combination nothing carries. Task 14 is what stops most of these reaching here.

**Rewrite the docstring's *"`group_axes` is deliberately not a parameter"* paragraph.** It is now
false. **Delete it and state what is true**, rather than editing it into something that half-survives.

**Fixture F6, and a per-arm COUNT will not do (C28).** 20 units, two arms of 10, `frac: 0.2`. The
pre-slice roster-wide draw lands on 2 per arm with probability ≈ **0.42**, so
`len(test ∩ arm) == 2` is a coin flip on whether it sees the bug — *a fixture whose numbers agree
with the bug*. **Pin the per-cell MEMBERSHIP at a fixed seed**, and — in this task, not later —
compute the **roster-wide** draw at the **same** seed and assert the two differ, changing the seed if
they coincide and **recording that the check was run**. `len(test) == 4` stays as a shape check and
is not counted as discrimination.

**Mutation MU-17:** `_resolved_holdout` ignores `group_axes` — that is the pre-slice code, and F6's
membership assertion is what catches it. Without MU-17 this task has no mutation at all and F6 is
the whole of its pinning.

**Must not touch:** `holdout_for`, `holdout_seed_for`, `holdout_sizes`, `_evaluation_roster`,
`E-DATA-HOLDOUT-FOLD` (C27).


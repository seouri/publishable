## Task 22

**Corrections that bind this task: C27.**

**Two end-to-end `run`s**, outside the repository, through the real console script.

1. **`groups × fold`.** Assert: `sweep.yaml` carries `partitions_within`; per-cell membership is
   recoverable by crossing `partitions` against `allocation.json`'s `arms`; `io.units.train` is
   inside the arm for every condition-scoped execution; and the per-condition identity
   `resolved == completed + ineligible + failed` holds.
2. **`groups × holdout`.** Assert: `allocation.json`'s `holdout` carries `within`; each arm's test
   side is the declared fraction **of that arm**; `io.units.train` is inside the arm — the property
   task 15 proved by direct call, now confirmed end to end; and the same attrition identity.

**No fixture declares both a holdout and a fold** (C27).

**Must not touch:** anything. This task adds tests and runs commands.


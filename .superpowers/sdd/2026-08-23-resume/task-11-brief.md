## Task 11

**Pointer: Decision 10 binds this task, and Ruling S from H9a binds it too.**

`allocation.json` is **read rather than re-drawn** — the reader § Resuming says does not exist.

Read the file when present and override, through `dataclasses.replace` on the frozen `Prepared`, the
arm memberships and the holdout partition `_prepare_run` resolved. Fold partitions come from
`sweep.yaml`'s own `partitions` block. A recorded membership naming a unit the roster no longer holds,
or a file that will not parse, is `E-RESUME-ALLOCATION-STALE`.

**`dataclasses.replace` must round-trip all 36 fields** (correction 17) — assert the field count in the
test, so a future field added to `Prepared` and forgotten here fails loudly.

**Ruling S: you override results, you do not move calls.** `_resolved_group_axes` and `arm_members`
stay exactly where they are; H3c-3's remaining 14 owns the hoist, and folds and holdouts *inside cells*
need the axes realized before the cell decomposition. **Same function, different move.**

**The fixture is a DRAWN axis** (`method: random`), where a second draw would differ. A `by_attribute`
axis re-reads the same column and gives the same partition, so correct and buggy readings coincide and
the fixture would test one reading twice.

**Must not touch:** `units.arm_members`, `_resolved_group_axes`, `_resolved_holdout`; any `*.md`.

**Mutations:** skip the override (the drawn-axis fixture, whose recorded memberships are edited away
from what a second draw gives); accept a membership naming an absent unit (a second fixture arm).

---


## Task 2

**Corrections that bind this task: C10, C21, C25.**

**Build `units.cells_of(axes)`.**

```python
def cells_of(
    axes: Mapping[str, ArmPlan],
) -> dict[tuple[tuple[str, str], ...], frozenset[str]]:
```

The cartesian product of every axis's `levels`, **in declaration order** (`axes` is an ordered
mapping and its order is `_resolved_group_axes`' contract), each key a tuple of `(axis, level)` pairs
in that order, each value the intersection of those levels' `members`. **Empty cells are kept.**
`axes == {}` returns `{(): frozenset(every key in every plan)}` — and with no plans at all, the caller
supplies the roster's keys; state in the docstring that this function takes **no roster** for
`arm_members`' own reason, so the one-cell case is the caller's to compose.

Prefer: `cells_of({}) -> {(): frozenset()}` and the caller treats an empty decomposition as
"one cell, the whole roster". Write that rule in the docstring and in the caller, once each, and do
not let both invent it.

**Docstring must say:** why it derives from `ArmPlan`s and not from `arm_members` (condition-keyed;
`groups × grid` shares a cell; a condition selecting no axis is absent) — and that deriving cells
from `arm_members` would draw one partition per condition and break *"Partitions are computed once
per run, not once per condition"* for real.

**Fixtures:** two axes of two levels over 12 units → 4 cells, disjoint, covering the roster; a
crossed pair with one empty intersection → **4** cells, one empty; one axis → 2 cells; `{}` → one
cell.

**Mutations:** MU-1 (skip empty cells → the 4-vs-3 count assertion), MU-2 (union instead of
intersection → the disjointness assertion).

**Must not touch:** `arm_members`, `assignment_for`, `ArmPlan`, `arms_of`.


## Task 5

**Corrections that bind this task: C10, C17.**

**Build `validate._resolved_cells(doc, units_decl, roster, usable_cluster)`.** Realize each
`sweep.groups` axis through `units.assignment_for` at the **real** `design_digest(doc)`, in
declaration order, threading each axis the plans already realized (`resolved=`), then call
`cells_of`. Wrap the whole thing in one `try` swallowing `ContractError`, `NotImplementedError`,
`KeyError`, `TypeError` and `ValueError`, returning `None`.

**The precedent is `validate._holdout_test_roster`, which H3d wrote**, and the docstring must cite it
by name and repeat its ground: a second answer computed here would be a check aimed at a partition
the run does not use. **Do not** copy `_check_assign`'s placeholder digest `"validate"` — that gating
is sound only for the unstratified, unclustered case where sizes are digest-independent, and a cell's
cluster count is exactly the seed-dependent quantity it excludes.

**Fixtures:** a `by_attribute` axis (cells resolve, no draw); a `random` axis (cells resolve through
a real draw, and the memberships equal `command_run`'s for the same config); a `blocked` axis beside
`cluster_by` (raises `NotImplementedError` inside `assignment_for` → `None`, and `validate` still
reports `E-DATA-ASSIGN-BLOCKED-CLUSTER` from its own check); a malformed axis (→ `None`).

**Can-fail control:** the `random` fixture asserts the **membership**, not that a decomposition
exists — an assertion that only checks non-`None` passes with any draw.

**Must not touch:** `_check_assign`, `_holdout_test_roster`, `assignment_for`.


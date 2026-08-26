## Task 18

> **AMENDED 2026-08-25 by the controller, from batch A's concern 4.** **Mutation MU-11 is YOURS**, declared
> in advance by batch A and named in a shipped test's docstring because your code did not exist yet.

**Corrections that bind this task: C16, C17.** **RULING JJ BINDS THIS TASK: `limits.min_units_per_cell`
must be DECIDED, not declined, and there is no later slice.**

**Build `W-DATA-CELL-THIN`** — a **warning**, not a refusal, at `validate`, from **one** site,
reported **once** for the smallest non-empty cell below `limits.min_units_per_cell`, over
`_resolved_cells`' decomposition.

**Why a warning:** three document sites say warning (§ Validation's *Cells are populated* and
*Allocation is coherent*, both *"specified, not built in this build (warning)"*, and § The one config
file's inline comment). *An unbuilt reader of a shipped surface is a defect*, and **the code follows
the documents** rather than the reverse.

**The gate, and it is the failure mode that matters (C16, C17):** the check fires **only when a cell
structure resolves**. Without the gate it fires on every generated project with fewer than 20 units,
because `materialize.py` writes `min_units_per_cell: 20` into every config. Neither § Validation row's
own wording carries the gate; both rows' examples do — the *"taking a § Validation row's own wording
as its whole scope"* misreading, in its natural habitat.

**The name:** `W-DATA-CELL-THIN`. `W-DATA-*` because the declarations it answers for are
`data.units.allocation` and `limits.min_units_per_cell`, not a statistics block; `-THIN` because it
joins that family — **and it joins the family's already-filed, still-unowned documentation question
rather than settling it.** Say that in the filing (task 20); do not claim a closure.

**Documents:** § Warnings core reports gains **one** row. § Validation's *Cells are populated* and
*Allocation is coherent* both lose *"specified, not built in this build"* and both name the code —
**two § Validation rows, one code**, which is legal because the one-row-per-code rule governs
§ Errors and § Warnings, not § Validation. **No precedent was found for two § Validation rows sharing
a code; say so in the report rather than implying one exists.** § The one config file's comment and
the § Weighted samples-adjacent paragraph asserting *"nothing warns"* both change; the second is a
**deletion**, because after this task it is false.

**Fixture F3 and its two controls:** 12 units, two arms of 6, `min_units_per_cell: 20`, no fold, no
holdout → exactly one warning naming the smaller cell. Control 1: `min_units_per_cell: 5` → none.
Control 2 (the gate): the same 12 units with **no** `sweep.groups` → none. Control 2 **is guard-pin
arm E**, captured in task 1 before this code existed.

**Mutations:** MU-11 (remove the gate → arm E fails), MU-12 (compare against the **largest** cell →
a **7/5** fixture at `min_units_per_cell: 6`; **equal arms would make this blind**, which is why the
warning fixture is 6/6 and the mutation's is 7/5).

**Must not touch:** `limits.min_clusters`, `limits.min_reported_n`, `limits.max_ineligible_fraction`
— all still unread, all still shipping that way, and **nothing follows this slice**.


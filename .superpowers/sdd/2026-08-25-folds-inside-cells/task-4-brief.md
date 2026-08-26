## Task 4

**Corrections that bind this task: C3, C19, C20.** **Ruling S is discharged here**
([the re-entry seam design](../specs/2026-08-23-re-entry-seam-design.md) § Decision 2 named this
slice as the owner of exactly this hoist).

**Hoist `_resolved_group_axes` and `arm_members` above the fold region, inside `_prepare_run`.** The
resulting order: `clusters_of` → `_resolved_group_axes` → `arm_members` → `cells_of` →
`cell_fold_basis`/`fold_basis` → `resolve_repeats` → the partition call → `fold_members_for` →
`_resolved_holdout` → `_evaluation_roster`. `_resolved_holdout` **does not move** (C19).

`Prepared` gains **one** field, `cells`, and `_execute_prepared` gains **one** unpack line. Nothing
else in either list moves (C20).

**Assert, do not assume, "realized once per run":** a counting patch on `_resolved_group_axes` inside
a real `command_run` asserting exactly one call.

**Mutation MU-16:** reorder so `arm_members` is called twice — the count assertion catches it.

**Must not touch:** `_resolved_holdout`'s position, `arm_members`' signature, any other `Prepared`
field, `_resumed_allocation` (task 17 owns it).

**Report must state:** the before and after order, by function name, and that guard-pin arms A, B, D
and E were re-run and are unchanged.


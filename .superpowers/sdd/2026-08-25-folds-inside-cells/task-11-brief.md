## Task 11

> **AMENDED 2026-08-25 by the controller, from batch B's concerns 1 and 2.** Two obligations fell out of
> earlier tasks and land on whichever of tasks 11, 14, 17 or 18 reaches them first — **check both before you
> start, and if you are the first, they are yours:**
>
> 1. **`Prepared.cells` has NO `_execute_prepared` unpack line** — measured, `ruff` reports one `F841`, and
>    C20 says the opposite. **The first task reading `cells` in phases 6–10 adds it.**
> 2. **`units.cell_fold_basis` has ZERO production callers.** Task 7 needed the argmin cell and used
>    `units.thinnest_cell` instead. **If no task calls it, the slice ships a tested function nothing calls**
>    — which is *an unbuilt reader of a shipped surface* wearing its other face, in the row whose example
>    list just ran out. **Either call it or delete it, and say which.**

**Corrections that bind this task: C8, C13, C14.**

**`sweep.yaml` gains one top-level key, `partitions_within: [<axis names>]`, written only when the
partitions were drawn within cells.** Every `partitions` entry keeps `fold`, `test`, `train`
**unchanged** — guard-pin arm B is what says so.

**The reason, and it must be in the docstring rather than in this plan alone (C8):** composing
`train` within the cell is arithmetically the same set, because cells partition the roster and the
merge is index-wise. The defect the key discloses is that **under cells the flat `train` names a side
no execution ever sees** — every condition is arm-narrowed first, so a step gets `cell ∩ (roster \
partition_i)`. The precedent for a disclosure key travelling beside the number it qualifies is
`weighted_by` and `n_paired_clusters`; the precedent for omitting it when it describes nothing is
`build_allocation_document`'s own rule for `seed`/`strata`.

**Re-read `E-RUN-FOLD-UNRESOLVED`'s third site while you are here (C13):**
`build_sweep_document`'s *"partitions were drawn but no `fold` level is declared"* guard. The
index-wise merge changes what it is looking at (a list of `k` merged partitions rather than `k`
whole-roster ones); confirm the `zip(fold.members, partitions, strict=True)` still pairs and say so.

**`reference.md` § The other files a run writes** gains the sentence naming `partitions_within` and
what a reader crosses to recover a step's real train side. Task 21 owns every other document site;
this one sentence lands here because it is the record's own description.

**Mutation MU-14:** write `partitions_within` unconditionally — guard-pin arm B fails.

**Must not touch:** the three `sweep["partitions"]` assertions, `test_a_fold_level_records_its_partitions`,
`lineage.read_sweep_plan`, `freeze`'s reader.


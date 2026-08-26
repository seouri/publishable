## Task 16

**Corrections that bind this task: C2, C15, C18, C23.** **Sequenced strictly after task 15
(Ruling II).**

**Retire `E-DATA-HOLDOUT-CELLS`**: remove the `holdout` arm of `_check_evaluation_split_cells`, which
empties the function — so **delete the function, its call site, and
`test_a_group_axis_alone_triggers_the_refusal_without_between`** (C18; the test pins a message
branch, not behaviour that survives).

**`allocation.json`'s `holdout` block gains `within: [<axis names>]`, written only when the split was
drawn within cells.** `train` and `test` stay flat lists over the whole roster — a per-cell holdout's
union is still a partition of the roster, and each cell is split to the same proportion, so the
imbalance the refusal was minted against does not exist to hide. The key is derived by
`build_allocation_document` from its **`group_axes` argument**; `HoldoutPlan` gains no field, and
this function still takes no roster.

**Its readers are two (C15)** — `lineage.read_allocation` and `_resumed_allocation`, both of which
read the holdout by key and ignore extras. `report.py`, `study.py` and `diff.py` read the file at zero
sites.

**`reference.md` § `allocation.json` — who went where** prints the document in full and gains the
`within` key in a document of the cell-drawn shape. Task 21 owns every other document site.

**Mutation MU-15:** write `within` unconditionally — a no-axis `allocation.json` assertion and
guard-pin arm C both fail.

**Must not touch:** guard-pin arm C (task 17 is its sole authorized editor, C23); the axis-keyed
`seed`/`strata` blocks; `provenance.allocation_hash`'s whole-file coverage.


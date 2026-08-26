## Task 8

> **AMENDED 2026-08-25 by the controller, from batch A's concern 1. This is the sharpest carry-forward in
> the slice and this section did not carry it.** Guard-pin **arm D** constrains you two ways:
>
> 1. **You must keep CALLING `partition_units`** — the arm pins that, not merely its result.
> 2. **You must compose the one-cell case BEFORE the loop.** `cells_of({})` returns **one EMPTY cell**, and
>    Decision 7's loop **skips empty cells** — so passing a no-axis design through the loop calls
>    `partition_units` **zero times and every fold silently vanishes.** Measured by batch A.
>
> **That is the bit-stability oracle's exact failure mode**: a design with no cells must come out
> **bit-identical**, and the loop as designed would make it come out empty. **Build the no-axis case first
> and pin it before you write the loop**, not after.

**Corrections that bind this task: C10, C25, C26.**

**Build `units.partition_within_cells(roster, k, digest, cells, clusters=None, strata=None)`.** Loop
`partition_units(sub_roster, k, digest, clusters=…, strata=…)` per **non-empty** cell in `cells`' key
order; merge **index-wise** — partition *i* is each cell's partition *i*, concatenated in cell order.
Each sub_roster is built from `roster` in **roster order**; each cell's `clusters`/`strata` map is the
run's map restricted to that cell's keys, **total over the sub_roster** (C26). **The bare `digest` is
passed to every call** — no `digest|cell` mixing.

An empty `cells`, or one trivial cell, is one `partition_units` call over the whole roster with the
bare digest — **the same single call the code makes today**, which is guard-pin arm D.

**Docstring must say:** that empty cells are skipped **inside this loop and that this is not a
bound** — a cell too thin for `k` is refused at `validate` by task 7's clause, before this runs; and
that a per-cell digest was rejected because it is safe only if the no-cell path never touches it,
while the bare digest needs no such guard (`partition_units` seeds its own RNG per call, so per-cell
calls are independent of cell order and of how many cells there are).

Reroute `_prepare_run`'s call site to this function. **`partition_units` is called from inside it**,
so guard-pin arm D survives unedited.

**Mutations:** MU-5 (per-cell digest → a **two-cell** partition-contents pin at a fixed digest;
arm A is a one-cell case and cannot see this), MU-6 (concatenate whole cells instead of index-wise →
fold 0 must contain units from **both** cells).

**Must not touch:** `partition_units`, `_assign_whole_clusters`, `_assign_whole_clusters_by_ratio`,
`_seed_from`. **A fold regression bought for an arm feature is the trade this slice must not make.**


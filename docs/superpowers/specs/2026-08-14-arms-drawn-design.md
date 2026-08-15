# H3c-2 Arms drawn — design

**Goal:** `assign.method: random` and `assign.method: blocked` draw the arm assignment, which
H3c-1 refused by value as `E-DATA-ASSIGN-DRAWN`. Today only `by_attribute` executes — the arm is
*read* from a column. This slice makes core *draw* it: from `assign.seed`, honouring `ratio`,
`block_size` and `stratify_by`, keeping whole clusters on one side, recording the realized seed and
strata in `allocation.json`, and retiring the refusal.

**What it is not:** a second membership mechanism. The draw joins `units.arms_of` under **one
authority**, callable from `validate` and from `cli.command_run` and deterministic on its inputs —
the property that makes "a config that validates cannot crash the runner" true, and the property a
naive drawing implementation destroys first.

---

## The measurement this rests on

`docs/superpowers/H3c-2-SCOPING.md` is the record. Its load-bearing finding: **nothing of the
drawing machinery is built.** `ratio` and `block_size` appear nowhere in `src/` or `tests/` as
config keys. Five § Validation rows describe checks with no emit site, no check, and no test:
*Ratio names levels*, *Block size fills the arms*, *Stratification is forward-only*, *Allocation
strata exist*, and the `assign.` branch of *Stratification attribute exists*.

Three code sites carry an explicit "only `by_attribute` is reachable" assumption and must change:
`artifacts.build_allocation_document` (returns `seed: {}` and `strata: {}` as hardcoded literals,
with a four-paragraph docstring arguing why), `cli._resolved_group_axes` (returns
`dict[axis, (column, levels)]` — **a shape that cannot express a drawn axis at all**, since there is
no column to name), and `units._assign_constant_columns` (correctly gated; this one stays).

Two deliverables the H3c scoping assigned to H3c-1 **did not ship** and land here: the `assign`
per-axis whole-leaf closure, and the `ratio`-under-`by_attribute` rejection `reference.md` already
asserts and nothing implements.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | `blocked` beside a declared `cluster_by` | **Refused**, narrowly | *Settled by the user.* The documents are contradictory: § Where units come from makes `blocked` the one declaration reading roster order as data; § Clustered units says a cluster is drawn whole under `blocked`. The existing whole-cluster primitive **shuffles** cluster order with the digest-seeded RNG, destroying exactly the property `blocked` exists for. Block size counts *units* and clusters are indivisible, so no block size honours both. Refusing a combination made reachable but not computable is the pattern H3a, H3b and H3c-1 each used |
| 2 | `limits.min_units_per_cell` | **Stays unowned and hedged** | *Settled by the user.* A limits-family deliverable, not a drawing one, and reachable under `by_attribute` already. Folding it in repeats the scope creep H3c-1 declined |
| 3 | `block_size: auto` when `ratio: {}` | **Twice the level count** | `{}` *is* equal allocation — § Allocation says so — so the implied ratio is 1 per level and its sum is the level count. `auto` is twice the ratio's sum, so twice the level count. The only reading consistent with both sentences; stated in the document rather than inferred |
| 4 | Which row owns the `assign.stratify_by` fault | ***Allocation strata exist*** owns it; *Stratification attribute exists* keeps `fold` and `holdout` | *Allocation strata exist* is the only one of the two that admits **a group axis name** as a stratum, which forward-only stratification requires. A new `E-` code is minted for it, per the registry's existing promise that each block gets "its own code once its block is built" |
| 5 | The draw's home | **One authority beside `arms_of`**, pure and deterministic | `arms_of`'s own docstring calls a second notion of arm membership "the validate-clean-then-disagree gap in a new shape". `validate` needs membership too, so the draw must be callable from both sides on `(roster, digest, axis, ratio, block_size, strata)` |
| 6 | The clustered draw | **A sibling of `_assign_whole_clusters`, not a parameterization** | That function deals whole clusters to the **least-loaded** of `k` *equal* buckets. An unequal `ratio` needs "furthest below its own target share", and its fold behaviour is pinned by a bit-stability oracle. Changing it risks a fold regression for an arm feature |
| 7 | `resume` reading rather than re-drawing | **Re-record; do not build** | Under `by_attribute` re-reading a column is idempotent, so the missing `resume` was harmless. **Under a draw the rule becomes load-bearing** — and there is still no `resume` command. Building one is a command deliverable, not a drawing one |

## The traps, and where each lives

| Trap | The rule |
|---|---|
| The draw becomes a second membership producer | `units.arms_of` is the single authority. `units.arm_members`' `axes` parameter type is what must change; `artifacts.build_allocation_document` calls `arms_of` a **second** time on the same axes, so either the recomputation is provably identical or the draw is computed once and passed |
| `_assign_whole_clusters` reused unchanged | It ignores `ratio` silently — `k` equal buckets. Decision 6 |
| `blocked`'s reproducibility asserted wrongly | Appending a unit does not merely redraw, it **re-blocks**: boundaries move relative to every earlier unit, so units that never moved rows change arms. A test asserting "adding a unit changes only that unit's arm" asserts something false |
| The seed derivation copied from the wrong precedent | `partition_units` seeds from the digest **only**; `BaseStep.derive_seed` mixes the execution seed. `assign.seed` is specified as digest + axis name + **resolved roster**. `sweep.sample_seed_for` is the precedent — pinned integer returned literally, digest computed only on the `auto` path — and `units.units_hash` is the roster input |
| Forward-only stratification treated as a check | It is a **sequencing requirement**: axis 2's draw consumes axis 1's *realized* membership. Nothing today establishes any per-axis draw order — `_resolved_group_axes` builds a dict in declaration order by accident, not by contract |
| `stratify_by` × clusters reimplemented | `units.stratum_varies_within_cluster` exists and is the constancy test `partition_units` already depends on. Reuse it |
| `W-DATA-CLUSTER-UNDECLARED`'s exclusion list | It excludes an attribute "a `sweep.groups` axis names or an `assign.from` reads… any `stratify_by`". Under a draw there is no `assign.from`, and `assign.stratify_by` is a new `stratify_by` source the exclusion must reach |
| A test that cannot fail | `ratio {control: 1, treatment: 1}` with `block_size: auto` over a roster divisible by the block gives `random` and `blocked` **the same arm sizes**. Assert the within-block property, over a roster whose length is not a multiple of the block, with a pinned seed. And a fixture where cluster boundaries coincide with block boundaries hides the whole of decision 1 |

## Task decomposition — 14

1. Documents, part A — the ten `E-DATA-ASSIGN-DRAWN` prose surfaces and the *Assignment method isn't drawn* row.
2. Documents, part B — decisions 1 and 3 written into `reference.md` before any code.
3. Documents, part C — decision 4, and the new `assign` stratum code registered.
4. The `assign` per-axis whole-leaf closure in `envelope.py` — **ahead of 5–13**, which add four new keys inside those blocks.
5. `ratio` validation, including the non-empty-`ratio`-under-`by_attribute` rejection. Ships before drawing exists and closes a live gap.
6. The `assign.seed` derivation.
7. The draw's authority and its signature — `arms_of`, `arm_members`, `_resolved_group_axes` taught a second membership source under one authority.
8. `random` honouring `ratio`, unclustered.
9. `random` over whole clusters — decision 6's sibling, with the fold bit-stability oracle intact.
10. `blocked`, `block_size`, the whole-multiple rule, and the roster-order property asserted directly.
11. `blocked` × `cluster_by` refused — decision 1's code and registry row.
12. `assign.stratify_by` in the draw; *Allocation strata exist*.
13. Forward-only stratification — the per-axis draw ordering; *Stratification is forward-only*.
14. `allocation.json` gains `seed` and `strata`; retire `E-DATA-ASSIGN-DRAWN`; rewrite the two
    shape-locking tests and `build_allocation_document`'s docstring; re-record the `resume` gap.

## Out of scope, with the route

- **`limits.min_units_per_cell`** — decision 2. Unowned; a later limits slice.
- **The unpaired estimator family.** `E-DATA-ALLOCATION-CONTRAST` still refuses every cross-arm
  delta, and drawing an arm does not make an arm-versus-arm contrast computable. H4's.
- **`assign.<axis>.stratify_by` joining `CONSTANT_COLUMN_RULES`.** A real gap — a stratum column
  varying across a unit's measurement rows collapses silently, unlike `assign.<axis>.from`, which
  H3c-1 wired in. Record it; do not legislate it here.
- **`resume`** — decision 7.
- **H3c-3's `fold_basis` per cell.** Drawing does not make cells more or less partitionable.

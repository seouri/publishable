# H3c-2 scoping — arms drawn

Measured against `main` at the merge of H3c-1 (`39c6667`), read-only. The H3c charter's H3c-2
enumeration was written **before H3c-1 was implemented**; every claim below was checked against the
code rather than against that document, because roughly half of H3c-1's task briefs carried a defect
traceable to exactly that drift.

## 1. What already exists: nothing of the drawing machinery

`ratio` and `block_size` appear **nowhere** in `src/` or `tests/` as config keys. The only matches
are unrelated prose and one `validate.py` docstring naming `block_size` as `blocked`'s discriminator
without reading it.

| Deliverable | Emit site | Check | Test |
|---|---|---|---|
| `assign.seed` derivation | none | none | none |
| `ratio` | none | none | none |
| `block_size` / `auto` | none | none | none |
| `stratify_by` (assign) | none | none | none |
| Whole clusters to one arm | none | none | none |
| *Ratio names levels* | — | row only | none |
| *Block size fills the arms* | — | row only | none |
| *Stratification is forward-only* | — | row only | none |
| *Allocation strata exist* | — | row only | none |
| *Stratification attribute exists*, `assign.` branch | — | row exists, branch unwritten | none |

**Usable from H3c-1:** `validate.DRAWN_ASSIGN_METHODS` and its `elif` branch (the single retirement
site, parametrized over both values); `hashes.design_digest`'s per-axis `assign.seed` strip, which
survives new sibling keys so `ratio`/`block_size`/`stratify_by` are digested as § What `auto` derives
from requires; `units.stratum_varies_within_cluster` (**the one code identifier the charter got
right**); `units._assign_whole_clusters`/`partition_units`; `sweep.sample_seed_for` as the
`auto`-vs-pinned precedent.

**Assigned to H3c-1 but did not ship, and now land here:** the `assign` per-axis whole-leaf closure
(`envelope.py` types only `data.units.assign: dict`, and § The one config file records the gap in
so many words), and the `ratio`-under-`by_attribute` rejection § Allocation asserts with nothing
behind it.

## 2. What the documents specify, and where they disagree

Load-bearing sentences: `ratio` is "keyed by level, one entry per level of THIS axis", `{}` is equal
allocation, and "a partial mapping is rejected rather than defaulted"; `auto` is "twice the sum of
`ratio`, the smallest block that isn't a fixed alternating pattern", with an explicit value "a whole
multiple of that sum so every block fills each arm exactly"; `blocked` "balances arms *across the
roster's order*, so it's the one declaration that reads the order as data"; under `random` or
`blocked` "a cluster is drawn as a whole… no cluster straddles two arms", **against** `by_attribute`
where "a cluster may span both arms"; and an axis's `assign.seed` mixes "digest + the axis name + the
resolved roster".

**Four disagreements:**

1. **`blocked` × `cluster_by` is contradictory.** No passage says whether a block is a block of
   *clusters* in roster order or of *units* whose boundaries clusters may straddle. The second is
   incompatible with indivisibility; the first changes what `block_size` counts. *Settled by the
   user: refuse the combination.*
2. **`block_size: auto` is undefined when `ratio: {}`** — the value `init` writes. *Settled: twice
   the level count.*
3. **Two § Validation rows overlap on `assign.stratify_by`.** *Stratification attribute exists*
   contemplates only a unit attribute; *Allocation strata exist* admits "neither a unit attribute
   **nor a group axis**" — and an axis name is exactly what forward-only stratification requires.
   The registry already promises each block "its own code once its block is built". *Settled:
   Allocation strata exist owns it, with a new code.*
4. **A rejection asserted for a method that already executes.** "Under `method: by_attribute` a
   `ratio` describes a draw that didn't happen, so `validate` rejects a non-empty one" — nothing
   reads `ratio` anywhere. Live gap today, not a drawing gap.

## 3. Stale premises in the charter's H3c-2 section

| Claim | Status |
|---|---|
| Retires `E-DATA-ASSIGN-METHOD-UNSUPPORTED` | **Stale.** Shipped as `E-DATA-ASSIGN-DRAWN` — the `-UNSUPPORTED` suffix is the undocumented build family; this is the narrow documented one |
| The four row titles | Accurate, verbatim in § Validation |
| "the `assign.` branch of *Stratification attribute exists*" | Partly stale — it is the *shared* row, and no `assign` stratum code is minted anywhere |
| "reusing `stratum_varies_within_cluster`" | Accurate |
| "1 documents pass" | **Materially understated.** `E-DATA-ASSIGN-DRAWN` appears 9× in `reference.md` and 1× in `experimental-designs.md`, at ten independent prose sites |
| "10 `allocation.json` gains `seed` and `strata`" | Accurate but under-costed: two tests lock the current shape literally, and the docstring is a four-paragraph argument for the empties |
| Omits entirely | the whole-leaf closure; the `ratio`-under-`by_attribute` gap; `_resolved_group_axes`' return shape; `arms_of`'s signature |

## 4. What assumes no draw happens

- **`artifacts.build_allocation_document`** — `seed: {}` and `strata: {}` as hardcoded literals.
  The change is *add per-axis entries for drawn axes*, not *replace the empties*: § `allocation.json`
  says a `by_attribute` axis "is left out of both".
- **`cli._resolved_group_axes`** — `dict[axis, (column, levels)]`, gated on `by_attribute`, falling
  back to `column = axis` otherwise. **This shape cannot express a drawn axis**: there is no column.
- **`units._assign_constant_columns`** — same gate, correctly. `from` means nothing under a draw.
  This one stays.

**`provenance.allocation_hash` needs no shape change.** `artifacts.allocation_hash` hashes the
*document* canonically, not the file bytes, so it covers `seed` and `strata` the moment they are
populated — the realized per-axis seed integer joins the provenance claim for free.

**`resume` has no reader**, and under a draw that stops being harmless: re-reading a column is
idempotent, re-drawing is not.

## 5. The traps

1. **`arms_of` is the single authority and is `by_attribute`-shaped.** Its docstring calls a second
   notion of membership "the validate-clean-then-disagree gap in a new shape". `validate` needs
   membership too, so the draw must be a pure function callable from both sides.
2. **`_assign_whole_clusters` does not generalize to `ratio`** — it deals whole clusters to the
   least-loaded of `k` **equal** buckets, and its fold behaviour is pinned by a bit-stability oracle.
3. **`blocked` and clusters are mutually destructive** — that primitive *shuffles* cluster order.
4. **`blocked` re-blocks rather than redraws** when the roster changes: boundaries move relative to
   every earlier unit.
5. **No reusable seed mixer exists.** `partition_units` seeds from the digest only; `derive_seed`
   mixes the execution seed. `sample_seed_for` is the precedent; `units_hash` is the roster input.
6. **Forward-only stratification is a sequencing requirement, not a check.** No per-axis draw order
   exists today except by accident of dict construction.
7. **`stratify_by` × clusters** — reuse `stratum_varies_within_cluster`; do not reimplement. Note
   `assign.stratify_by` is **not** in `CONSTANT_COLUMN_RULES`, so a stratum varying across a unit's
   measurement rows collapses silently.
8. **`W-DATA-CLUSTER-UNDECLARED`'s exclusion list** must reach `assign.stratify_by`.
9. **A test that cannot fail:** equal ratio with `auto` block size over a divisible roster gives
   `random` and `blocked` the same arm *sizes*; and a fixture whose cluster boundaries coincide with
   block boundaries hides the whole of decision 1.

## 6. Decomposition: 14, not 10

The charter's "1 documents pass" is three tasks, two of which are **rulings on questions the
documents do not answer** rather than edits. It omits the whole-leaf closure and the
`ratio`-under-`by_attribute` gap. Its "`random` honouring `ratio`" and "whole clusters" are three,
because the authority seam and the ratio-target generalization are each a task. Its remaining lines
map cleanly onto tasks 10–14 of the spec.

## 7. Not in this slice

`limits.min_units_per_cell` (unowned, a limits deliverable); the unpaired estimator family (H4 —
drawing an arm does not make an arm-versus-arm contrast computable); `assign.stratify_by` joining
`CONSTANT_COLUMN_RULES` (record, do not legislate); `resume`; H3c-3's `fold_basis` per cell.

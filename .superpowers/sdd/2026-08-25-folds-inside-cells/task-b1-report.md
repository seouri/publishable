# Batch A — tasks 1, 2 and 3

**Status: all three complete, gates clean.** Written 2026-08-25.

| Task | Commit | What landed |
|---|---|---|
| 1 | `bf68454` | The guard pin, five arms, tests only — no `src/` file touched |
| 2 | `0a71421` | `units.cells_of(axes)` |
| 3 | `6a5c751` | `units.cell_fold_basis(roster, cluster_by, cells)` |

Branch base: `main` at `d17d402`, code at `3d72910`.
Final suite: **3355 passed, 1 skipped, 2 xfailed** (3338 + 17 new). `ruff check`,
`ruff format --check` and `mypy` clean at each commit.

**C24 — the count is 23, and here is the derivation rather than the number.** `H3c-3-SCOPING-2.md`
decomposes at **20**. Three surfaces its § 9 does not have, each measured against the code by the
plan's own corrections: **C5's** — `_check_sweep`'s `k: all` budget reads the *same* `basis` local
`_check_replication` does (confirmed by `grep -n "fold_basis" src/publishable/validate.py`: one
`basis`, threaded to both as `fold_basis=`), so the `k: all` half needs its own task or a `k: all`
design resolves to a `k` the cell bound then refuses; **C6's** — `validate._holdout_test_roster`
realizes the holdout over the **whole** roster and feeds `limits.min_clusters`, which becomes two
answers to one declaration the moment `_resolved_holdout` draws per cell; **C7's** —
`_check_holdout`'s `E-DATA-HOLDOUT-EMPTY` bounds `frac` against `len(roster)`, which under cells must
bound against the smallest non-empty cell at `validate` **and** in the message `holdout_for` raises.
20 + 3 = **23**. Nothing was merged to hit 20.

---

## 1. The guard pin — every arm, its authorized editor, and the shape it was captured against

**All five were captured forward, against the shape the design has already decided**, never against a
superseded one. Each arm's authorized editor and post-edit state are stated in the test's **own
docstring**, in advance, per H8a's rule.

| Arm | Test | Authorized editor | Shape captured against | Post-edit state |
|---|---|---|---|---|
| A | `tests/test_units.py::test_h3c3_pin_arm_a_the_three_partition_draws_are_byte_identical` | **NONE** | `partition_units`' current signature and its three paths, which Decision 7 leaves untouched — the per-cell loop calls it, it does not change | unchanged, byte for byte |
| B | `tests/test_cli.py::test_h3c3_pin_arm_b_a_no_axis_sweep_document_carries_only_the_flat_partitions` | **NONE** | Decision 11's decided shape: `partitions` entries unchanged, one **new top-level** key `partitions_within` for designs that have cells. Pinned as *no such key here* | unchanged |
| C | `tests/test_cli.py::test_h3c3_pin_arm_c_the_resumed_allocation_round_trips_to_the_recorded_document` | **task 17, and only task 17** | Decision 11's `holdout.within` — a new key inside the `holdout` block for designs that draw one per cell, absent for this design | **unchanged.** If task 17 measures otherwise: edit **once**, append `holdout.within`, reorder nothing, report the measurement |
| D | `tests/test_cli.py::test_h3c3_pin_arm_d_a_no_axis_prepare_makes_exactly_one_bare_digest_partition_call` | **NONE** | Decision 7's decided shape: task 8 reroutes `cli`'s call site through `units.partition_within_cells`, which keeps *calling* `partition_units` | unchanged |
| E | `tests/test_cli.py::test_h3c3_pin_arm_e_a_six_unit_no_axis_config_validates_with_no_findings_at_all` | **NONE** | Decision 3's decided shape: `W-DATA-CELL-THIN`, gated on a resolved cell structure. Captured **before the code exists** (Ruling JJ) | unchanged — must never gain `W-DATA-CELL-THIN` |

### Arm C is deliberately NOT a copy of the existing round-trip test

`test_h9b_the_allocation_override_replaces_four_fields_and_round_trips_the_rest` pins three things:
`len(dataclasses.fields(Prepared)) == 36`, a field-by-field identity loop over a `moved` set, and the
round trip. **Two of those three must move in this slice** — C20 adds `cells` as a 37th field, and
Ruling KK has `_resumed_allocation` re-derive the partitions, which changes what is and is not
`moved`. Copying that shape into an arm whose only editor is task 17 would have produced an arm that
*must* be edited by task 4 as well, which has no authorization to touch it. Arm C pins the round trip
**alone**: `build_allocation_document(overridden.group_axes, overridden.holdout_plan) == edited`. The
other two assertions stay where they already live, with whatever editors they already have.

### Arm D: the brief's two clauses could not both hold, and the resolution is in the docstring

The brief says *"patch the symbol `cli` calls, not `units.partition_units`"* **and** *"arm D must
survive that reroute unedited"*. `cli.py` does `from publishable.units import partition_units`
(grepped: `src/publishable/cli.py`, the `from publishable.units import (…)` list), so `cli` holds its
own binding. If task 8's `partition_within_cells` lives in `units.py` — which task 8's own brief
places it there — its inner call resolves **`units`'** binding, and a patch on
`publishable.cli.partition_units` alone would count **zero** after the reroute. An arm with no
authorized editor cannot be repaired then.

**Resolution: the counting wrapper is installed at both names and the assertion is on the sum**,
which is invariant under either shape and still fails a per-cell digest (MU-5) and any second draw.
**The constraint arm D imposes on task 8** is therefore narrower than the brief's, and is stated in
the docstring: the per-cell loop must keep *calling* `partition_units` rather than inlining its body;
*where* it is called from is free.

**The `== 1` literal was measured before it was written**, not assumed: `_prepare_run` runs
`validate_config` first, and a probe with the wrapper installed showed `validate` contributes **no**
`partition_units` call today, so the count is 1 and not 2. The same probe captured the digest string:
`sha256:05175f50…`, identical to `sweep.yaml`'s `design_digest`, with no `|` and no `arm=`. The test
compares against the recorded `design_digest` rather than a literal, so the two sources must agree.

### Arm E's paired half, and what it cannot yet run

The exact set is `[]`. Asserted as an equality, not as `"W-DATA-CELL-THIN" not in codes` — a set
equality catches the warning under any spelling, and an absence-only assertion passes identically if
nothing ran. **The half that must report is in the same test** so `pytest -k h3c3_pin_arm_e` runs
both: the same six units and the same generated config under `allocation: between` earns
`E-DATA-ALLOCATION-NO-ARMS` (C17's other half of the cell-structure question), which is what shows
`validate_config` reaches this config's allocation block rather than returning above it. Both halves
also assert the two facts the gate rests on, live: `limits.min_units_per_cell == 20` (what `init`
writes, C16) and `sweep == {}`.

**MU-11 cannot be run at task 1** — the code it mutates does not exist. It is **owed by task 18**.
That is arm E's honest status, not a gap.

---

## 2. The bit-stability oracle — the captured values and how each was computed

The oracle: **a design with no cells must draw the partition it drew at `3d72910`.** Arm A pins the
output; arm D pins the call. Three draws, because `partition_units` has three paths and the per-cell
loop passes `clusters=` and `strata=` through — a pin on the unclustered draw alone would leave the
two the slice actually threads unguarded.

| Draw | Call | Captured value | How |
|---|---|---|---|
| Unclustered | `partition_units(_roster(50), 5, "d")` | the 5 × 10 fold contents (`u018 u019 u034 …`) | **Re-computed** by calling at `d17d402`; it agrees with the existing oracle `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`, which is the point — two independent captures of one draw |
| Clustered | `partition_units(roster, k=2, digest="sha256:abc", clusters=…)` over `S1`×7, `S2`×3, `S3`×3, `S4`×1, `S5`×1 | `[[S1_0…S1_6, S4_0], [S3_0, S3_1, S3_2, S2_0, S2_1, S2_2, S5_0]]` | **Computed by running.** The sibling tests pin `{8, 7}` sizes and cluster identity only |
| Clustered + stratified | `partition_units(roster, k=3, digest="sha256:0000", clusters=…, strata=…)` over `A: [3,2,2,2]`, `B: [5,1,1,1,1]` | `[[Ac0_0…Bc0_4], [Ac2_0, Ac2_1, Ac1_0, Ac1_1, Bc3_0, Bc1_0], [Ac3_0, Ac3_1, Bc4_0, Bc2_0]]` | **Computed by running** |

**Why the membership had to be run rather than derived.** The *size* vectors are hand-derivable —
largest cluster first into the least-loaded fold — but the membership is not: in the clustered draw
`S4` and `S5` tie at size 1 and the shuffle breaks that tie, so `S4_0` landing in fold 0 and `S5_0`
in fold 1 is a fact about the seeded permutation and nothing else. **No literal in this branch was
carried from a document or a sibling test.**

**Mutation, run against the full unfiltered suite at `bf68454`:** `rng.shuffle(order)` deleted from
`_assign_whole_clusters` (the fold path; there is a second `rng.shuffle(order)` in
`_assign_whole_clusters_by_ratio`, the arm path, which is **not** the shuffle inside
`partition_units` and was not touched). **8 failed, 3335 passed, 1 skipped, 2 xfailed** — arm A among
the eight, failing on the unclustered assertion first. Reverted by **editing back**, diffed
byte-identical against a pre-mutation copy, and verified by **re-running the full suite**: 3343
passed.

---

## 3. C1's mapping, re-derived — and the S2 explanation checked

C1 says the empty-fold fixture's cluster-to-arm mapping is **under-determined by its own prose**, and
that the `treatment` row differs between the two scopings because a cluster spans both arms. **Both
halves check out, and I computed the table rather than reading it.**

The stated mapping: 15 units; `S1`→units 0–6, `S2`→7–9, `S3`→10–12, `S4`→13, `S5`→14; `arm = control`
for units 0–7. Under it:

- `control` = units 0–7 = all 7 of `S1` **plus unit 7, which is `S2`'s first** → **8 units, 2
  clusters**.
- `treatment` = units 8–14 = the **remaining 2 units of `S2`**, plus `S3` (3), `S4` (1), `S5` (1) →
  **7 units, 4 clusters** — not 3.
- **`S2` therefore spans both arms**, which is exactly C1's claim and is the whole of the
  difference: the scoping that reports `[3, 3, 1, 0, 0]` put three *whole* clusters in `treatment`,
  which requires a mapping in which no cluster spans the boundary. Neither table's prose determines
  its own mapping, so both are consistent with the words and only one with the stated mapping.

Computed at `6a5c751` by building that roster and calling `partition_units(sub, 5, "sha256:abc",
clusters=…)` per side:

```
whole roster   n_units 15  n_clusters 5  sizes [7, 3, 3, 1, 1]
control        n_units  8  n_clusters 2  sizes [7, 1, 0, 0, 0]
treatment      n_units  7  n_clusters 4  sizes [3, 2, 1, 1, 0]
```

**Byte for byte the table C1 states**, including the `treatment` row C1 corrects. Note that these
three rows are size vectors and *are* hand-derivable (largest cluster first, least-loaded fold), so
this is a genuine cross-check of the arithmetic rather than a restatement of an opaque draw.

**Not used in this batch.** F1 is tasks 9 and 20's fixture; F2 — 16 units, clusters nesting inside
arms, no spanning cluster — is task 3's, chosen precisely so the per-cell basis is not entangled with
Decision 13's open question.

---

## 4. Every added assertion, with the mutation that fails **it**

Batch A adds assertions and **moves none** — no existing test was edited, and no `src/` behaviour
changed for any design that validates today (`cells_of` and `cell_fold_basis` have **no callers
yet**, by design; their callers are tasks 6 and 8).

| Assertion | The mutation that fails it alone |
|---|---|
| Arm A's three draws | shuffle deleted from `_assign_whole_clusters` → **8 failed, 3335 passed** at `bf68454` |
| Arm B's `partitions_within not in sweep` | MU-14, owed by task 11 — the key does not exist yet |
| Arm C's round trip | MU-15, owed by task 16 |
| Arm D's `len(calls) == 1` and bare digest | MU-5 and MU-10, owed by tasks 8 and 17 |
| Arm E's exact finding set | MU-11, owed by task 18 |
| `cells_of` — the 4-cell count with one empty cell | **MU-1** (skip empty cells): **1 failed, 3346 passed** — `test_an_empty_intersection_is_kept_as_a_cell_rather_than_skipped` alone |
| `cells_of` — disjointness and the 12-unit total | **MU-2** (union for intersection): **2 failed, 3345 passed** — the crossed-axes test and the empty-intersection test |
| `cell_fold_basis(roster, "site", cells) == 2` | **MU-3** (`max` for `min`): **6 failed, 3348 passed** |
| `cell_fold_basis == 2` in all four orderings | **MU-4** (the first cell's basis): **2 failed, 3352 passed** — the two `thin_first=False` arms, in **both** naming directions |
| `cells_of` raises on a level the plan did not realize | **MU-4b** (`members.get(level, ())`): **1 failed, 3354 passed** — `test_a_level_the_plan_did_not_realize_is_a_core_defect` alone |

**MU-3's named catcher does not exist yet and this is declared rather than glossed.** The brief names
*"`{kind: fold, k: 3}` must be refused: max 3 clears, min 2 refuses"*. Nothing consumes
`cell_fold_basis` at task 3 — the cell clause at `_fold_k`'s **three** `E-REPL-FOLD-K-TOO-LARGE` emit
sites (C12) is **task 7's** — so the refusal half **cannot** be exercised here and is **owed by task
7**. MU-3 was run instead against the direct `== 2` assertion, where `max` gives 3. The
discriminating literal itself is stated in the test's docstring so task 7 inherits it: 5 ≥ 3 clears
the roster bound, 2 < 3 refuses the cell bound.

**MU-4's fixture has a decoy on each side.** The thin cell (2 clusters) is placed first *and* last in
the mapping's insertion order, **and** its level is named `aaa` in one pair and `zzz` in the other —
four arrangements. Under MU-4 exactly the two `thin_first=False` arms fail, **in both naming
directions**, which is what separates "first by insertion" from "first by sorted name": a single
order rules out one wrong answer, and a decoy on one side rules out one sort direction.

**No mutation in this batch was blind, and none is owed a replacement.** Each was checked against the
body of the test it names before it was run.

---

## 5. Disagreements with the briefs and the design — every one, with what was grepped

**This is not a count of zero.** Five, each with the grep that found it and each hit attributed.

**D1 — `cells_of({})`: the design and the brief disagree, and the brief is the self-consistent one.**
Design Decision 6 says `{}` axes give *"one cell whose key is `()` and whose value is every roster
key"*. **The function takes no roster** — Decision 6 says that too, three sentences later — so
"every roster key" is unreachable from its arguments. The brief's `cells_of({}) -> {(): frozenset()}`
plus *the caller treats an empty decomposition as one cell, the whole roster* is the reading that can
be built. **Built the brief's; the design is NOT retro-edited** (a spec records what was decided when
it was written). The rule is written **once** in the docstring and is owed **once** at the caller —
tasks 6 and 8 must write it there and not invent a second version.

**D2 — the brief's arm D mechanism is unsatisfiable as two clauses.** Measured, resolved, and
documented in § 1 above. Grepped: `grep -n "partition_units" src/publishable/cli.py` — one import
(the `from publishable.units import (…)` list) and one call site inside `_prepare_run`.

**D3 — C25's import obligation cannot be discharged at tasks 2 or 3, and no `noqa` was added.**
C25 requires `cell_fold_basis` in **both** `validate.py`'s and `cli.py`'s import lists and `cells_of`
in `cli.py`'s. Measured: adding `cells_of` to `cli.py` alone → `uv run ruff check .` reports **1
error** (F401); adding `cell_fold_basis` to both → **4 errors** (F401 twice, I001 twice). `[tool.ruff.lint] select = ["E", "F", "I", "UP", "B"]` in
`pyproject.toml`, and the gate is clean today. Both experiments were **edited back and diffed
identical** against pre-edit copies. **The imports land with their callers — tasks 6 and 8 — and C25
is discharged there, not here.**

**D4 — one of my own docstring claims was false, and it was found by grepping my own prose.**
`cell_fold_basis`' docstring said *"`fold_basis`' own docstring forbids [a per-cell mapping] in those
words."* Grepped the docstring: it says *"**One number, not two.**"* and *"Every caller resolves the
basis here rather than deciding for itself"* — a rule about unit count versus cluster count, which
this function **inherits**, not a sentence about mappings. Narrowed to quote what is actually there.
The design's *"explicitly forbidden by `fold_basis`' own docstring"* is the claim I had carried
without checking; **brief-supplied prose is where zero hides.**

**D5 — a citation was wrong by section, corrected in task 3's commit for code committed at
`0a71421`.** `cells_of`' docstring cited *"Partitions are computed once per run, not once per
condition"* to `reference.md` § Repeat kinds.
`grep -rn "once per run, not once per condition" README.md docs/design-principles.md
docs/experimental-designs.md docs/reference.md src/` returns **exactly one hit**, in
`docs/reference.md`, and the nearest preceding heading is **§ Clustered units**. Corrected. Two
further claims in the same docstring were narrowed the same way: *"the order `clusters_of` and
`units_hash` both call the reproducible one"* (`clusters_of` says insertion order **is** roster order
deliberately and cites `units_hash` for reproducibility — it does not itself use that phrase), and
*"its answer is over the whole roster"* for the `min_clusters` site, which is **the whole roster or
the holdout's test side** — read at `validate.py`'s `limits.min_clusters` block, whose own comment
says *"`statistics.resample` draws over the per-unit table"* and *"the test partition when a holdout
is declared, not the whole roster"*.

### Claims I grepped and which held

- *"`cli.py` does `from publishable.units import partition_units`"* — `src/publishable/cli.py`, the
  units import list. **Held.**
- *"a fold regression bought for an arm feature is the trade this slice must not make, and
  `_assign_whole_clusters_by_ratio`'s docstring states the same rule"* — `grep -n "bought for"` found
  **nothing**; re-read the docstring, which says *"risks a fold regression for an arm feature, a bad
  trade"*. **Held on the second spelling** — the first grep was for a spelling, which is the named
  trap; the answer came from reading.
- *"`materialize.py` writes `min_units_per_cell: 20` into every config `init` produces"* (C16) — not
  grepped but **asserted live inside arm E**, which is stronger.
- *"axes is an ordered mapping and its order is `_resolved_group_axes`' contract"* —
  `src/publishable/cli.py`, `_resolved_group_axes`' docstring: *"Axes are drawn in declaration order,
  and that order is a contract this function keeps rather than a property of how its dict happens to
  be built."* **Held verbatim.**
- *"`build_allocation_document` takes no roster on purpose"* — `src/publishable/artifacts.py`, *"This
  function takes **no roster** for that reason"*, and a second hit saying it still takes none once the
  holdout arrives. **Held.**
- *"`arm_members` is keyed by condition index and takes no roster"* — `src/publishable/units.py`,
  `arm_members`' docstring and its `dict[int, frozenset[str]]` return. **Held.**
- *"`_check_resample`'s `limits.min_clusters` is `fold_basis`' third call site"* —
  `grep -n "fold_basis" src/publishable/validate.py` returns hits at the import, the one `basis` local
  (C5: **one local, both callers** — confirmed, `_check_replication` and `_check_sweep` are handed the
  same `basis`), and the `limits.min_clusters` call. **Held**, and C5's one-local claim confirmed by
  the same grep.
- *"the existing oracle is `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`, and the
  sibling clustered tests pin sizes and cluster identity rather than membership"* — read
  `tests/test_units.py`'s partition block end to end. **Held**: `{8, 7}` and a per-cluster fold map,
  no ordered membership.

---

## 6. Concerns for the controller

1. **C25 is undischarged and its discharge is now split across tasks 6 and 8.** Neither task's brief
   says "and add the import" as its own step, because C25 assigned it to tasks 2 and 3. If both
   forget, `cells_of` and `cell_fold_basis` are dead code in `units.py` and every per-cell check
   silently keeps calling the roster-wide one. **This is the shape of a finding falling out of the
   chain**, so it is stated here rather than only in the commit messages.
2. **Arm D constrains task 8 in TWO ways, and the second is the dangerous one.** Task 8's brief
   carries neither, and arm D has no authorized editor.
   **(a)** `partition_within_cells` must keep **calling** `partition_units` rather than inlining its
   body — otherwise the counting wrapper sees nothing.
   **(b) The one-cell case must be composed before the loop, not passed through it.** `cells_of({})`
   returns **one empty cell**, and Decision 7 has `partition_within_cells` **skip empty cells**. A
   task 8 that hands `cells_of({})` straight to that loop for a no-axis design calls
   `partition_units` **zero** times: arm D fails at `len(calls) == 1`, and — the part arm D is there
   to make loud — **every fold silently vanishes** for every design with no group axis. Decision 7's
   own grounds assume the opposite (*"a one-cell design then reduces to the current single call
   byte-identically"*), so the whole-roster composition has to happen either at the caller or inside
   `partition_within_cells`. This is D1's *"owed once at the caller"* stated as the failure it
   causes, because a reader stops at the doc-inconsistency framing.
3. **Decision 6's `cells_of({})` sentence stays false in the design** (D1). It is not retro-edited.
   If the whole-branch review reads the design rather than the code it will find a function that
   disagrees with it; the disagreement is deliberate and recorded here.
4. **MU-3's refusal half and MU-11 are owed**, by tasks 7 and 18 respectively. Both are declared in
   advance, and both are named in the tests' own docstrings so the owing task finds them by grep.
5. **Two things were added after the three commits, in `ae5b4d9`'s follow-up**, both inside files
   this batch owns and neither changing behaviour: `cells_of`'s indexed-not-`.get` rule had **no
   fixture** — the *"seam named and instantiated by no fixture"* shape, and every sibling total-mapping
   rule in `units.py` has one — so it now has one, pinned by MU-4b; and `cell_fold_basis`' docstring
   now says that `fold_basis`' `E-DATA-CLUSTER-UNKNOWN` **propagates per cell**, so task 6 wraps the
   call in the same `try`/`except ContractError` `validate`'s roster-wide `basis` already sits in. An
   unwrapped call there turns a collecting `validate` into a raising one.
6. **`cell_fold_basis` is O(cells × roster)** — it walks the roster once per non-empty cell to
   preserve roster order. At the design's own scale that is nothing; it is stated because a later
   task copying the loop into an inner path would pay it per fold.

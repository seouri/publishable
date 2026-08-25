# H3c-3 — folds and holdouts inside cells: plan

**23 tasks, six batches, written 2026-08-25 against `main` at `d17d402`** (code at `3d72910`).
The design is [`2026-08-25-folds-inside-cells-design.md`](../specs/2026-08-25-folds-inside-cells-design.md);
the charter is [`H3c-3-SCOPING-2.md`](../H3c-3-SCOPING-2.md), which decomposes at 20 and recommends
not building. **Ruling HH overrules that recommendation**; the design's Decision 1 records the
alternative in full.

**This is the last slice in the project. Nothing is chartered after it.** Every gap any task here
declines ships with the project; there is no later slice to catch what this one leaves open. Each
task that declines something says so in its own section, because `scripts/task-brief` extracts task
sections and nothing else.

**§ Corrections against the code lives OUTSIDE the task sections and `task-brief` does not carry
it.** Every task section therefore opens with a line naming which corrections bind it. Read those
corrections before writing code: the brief's prose is a claim like any other, and **brief-supplied
prose is where "zero disagreements" hides.**

**Batch map.** A: 1–3. B: 4–7. C: 8–12. D: 13–17 (**carries Ruling II's ordering constraint**).
E: 18–20. F: 21–23. **Every batch is reviewed, including F.**

---

## § Corrections against the code

Twenty-seven, each measured at `3d72910`. They correct the two scopings, the spine charter, and the
controller's own ruling text. **Cite by section, never by line number.**

**C1 — the empty-fold fixture's cluster-to-arm mapping is under-determined, and the difference is a
spanning cluster.** Both scopings describe the same roster (15 units; `S1`×7, `S2`×3, `S3`×3, `S4`×1,
`S5`×1; `arm` by attribute, 8/7) and report different `treatment` rows: `[3, 3, 1, 0, 0]` from three
clusters, `[3, 2, 1, 1, 0]` from four. Recomputed here: with `S1`→0–6, `S2`→7–9, `S3`→10–12,
`S4`→13, `S5`→14 and `control` = units 0–7, cluster `S2` **spans both arms**, giving `control` 2
clusters and `treatment` 4, and the table is `[7, 3, 3, 1, 1]` / `[7, 1, 0, 0, 0]` / `[3, 2, 1, 1, 0]`.
**State the mapping in any fixture that uses it.** Binds tasks 9, 20.

**C2 — Ruling HH's stated premise is false at `3d72910`.** All three sites say *"not built"*:
`reference.md` § A fixed holdout split, § Clustered units, `experimental-designs.md` § Between-subjects
factorial. H3d repaired them. The design's Decision 1 supplies the grounds that survive. **Do not
write a document edit that claims to be repairing a present-tense falsehood.** Binds tasks 10, 16, 21.

**C3 — `H3c-3-SCOPING.md` § 1's call order is stale.** It records `partition_units` → `expand(doc)`
→ `_resolved_group_axes`. At `3d72910` `conditions = expand(doc)` is **above the whole region**, in
`_prepare_run` (not `command_run`). The hoist needs no new resolution. Binds task 4.

**C4 — `fold_basis` must NOT gain a `cells` argument** (Ruling LL, design Decision 4). Its third call
site is `_check_resample`'s `limits.min_clusters` denominator, which is a different question and must
stay roster-wide. A `cells=None` default there would be a helper ignoring an argument. Binds tasks 3,
6.

**C5 — `_check_sweep`'s `k: all` budget reads the same `basis` local as `_check_replication`**, and
neither scoping names it. If the budget resolved against the roster-wide basis while `_fold_k`
bounded against the smallest cell's, a `k: all` design would resolve to a `k` the bound then refuses.
**One local, both callers.** Binds task 6.

**C6 — `validate._holdout_test_roster` realizes the holdout over the WHOLE roster** and feeds
`limits.min_clusters`. Named by neither scoping. Once `_resolved_holdout` draws per cell, these are
two answers to one declaration — the defect `holdout_for`'s purity exists to prevent. Binds task 14.

**C7 — `_check_holdout`'s `E-DATA-HOLDOUT-EMPTY` bounds `frac` against `len(roster)`.** Named by
neither scoping. Under cells the bound is over the smallest non-empty cell, at `validate` and in the
message `holdout_for` raises at run. Binds task 14.

**C8 — "composing `train` within the cell" is arithmetically a no-op at the flat level.** Both
scopings call it a correctness change. Cells partition the roster and the merge is index-wise, so
`partitions` still partitions the roster and *"every other partition concatenated"* is `roster \
partition_i` either way. **The real defect is that under cells the flat `train` names a side no
execution ever sees.** Binds task 11.

**C9 — `holdout_for` over an empty sub-roster raises**, `ContractError` `E-DATA-HOLDOUT-EMPTY`,
*"over 0 resolved units leaves the **train** side empty"*; over a 2-unit sub-roster at `frac: 0.2` it
raises *"leaves the **test** side empty"*. `holdout_sizes(0, 0.2) == (0, 0)`. The per-cell loop
cannot skip empty cells silently, and a message that assumes "test side" is wrong for the empty
shape. Binds tasks 13, 14.

**C10 — signatures, measured.** `assign_seed_for(block, axis, digest, roster)`.
`assignment_for(roster, axis, block, levels, digest, clusters=None, resolved=None)` — **roster
first**. `holdout_for(roster, block, *, seed, clusters=None)`. `arm_members(axes, conditions)`.
`partition_units(roster, k, digest, clusters=None, strata=None)`. `fold_basis(roster, cluster_by)`.
Binds tasks 2, 3, 5, 8, 13, 17.

**C11 — roster ORDER moves the draw, and `_resumed_allocation` checks sets only.** `units_hash` over
six units forward `sha256:f3ba4914…`, reversed `sha256:ee083cab…`; `assign_seed_for` `2988051695`
against `1647976561`; realized `c` arm `[u01, u04, u05]` against `[u02, u04, u05]`. This is what makes
Ruling KK's mutation constructible. Binds task 17.

**C12 — `E-REPL-FOLD-K-TOO-LARGE` has THREE emit sites**: `validate.py` (a `c.error`) and
`replication._fold_k` (two raises, units and clusters). The original scoping counted two. Binds
task 7.

**C13 — `E-RUN-FOLD-UNRESOLVED` has THREE emit sites**: `runner._handed_keys`, `cli`'s
fold-with-no-roster guard, and `sweep.build_sweep_document`'s partitions-without-a-fold guard. The
original counted one. Binds tasks 11, 12.

**C14 — `sweep.yaml`'s `partitions` is read by no command.** `lineage.read_sweep_plan` projects
`conditions`/`order`/`execution_order`; `freeze` reads `conditions`. Its readers are three assertions
in `tests/test_cli.py` and `tests/test_sweep.py::test_a_fold_level_records_its_partitions`. Binds
task 11.

**C15 — `allocation.json`'s readers are `lineage.read_allocation` and `_resumed_allocation`.**
`report.py`, `study.py` and `diff.py` read it at zero sites (H8c's bundle ruling). Binds task 16.

**C16 — `W-DATA-CELL-THIN` must be gated on a cell structure or it fires on every generated
project.** `materialize.py` writes `min_units_per_cell: 20` into every config `init` produces.
Neither § Validation row's own wording carries the gate; both rows' **examples** do. Binds task 18.

**C17 — in an otherwise-clean config a cell structure is exactly one shape.** A non-empty
`sweep.groups` beside `allocation: within` earns `E-DATA-ALLOCATION-WITHIN-ARMS`; `allocation:
between` with no group axis earns *Allocation needs arms*. So gating on the resolved axes gates on
both. Binds tasks 5, 18.

**C18 — `_check_evaluation_split_cells`' `groups`-branch message is pinned by
`tests/test_validate.py::test_a_group_axis_alone_triggers_the_refusal_without_between`**, and that
branch is only ever read by a doubly-refused config. When the function goes, **delete that test**;
do not adapt it. *Prefer deleting a claim to rewriting it.* Binds tasks 10, 16.

**C19 — only the fold half needs the hoist.** `_resolved_group_axes` already sits **above**
`_resolved_holdout` at `3d72910`; `H3c-3-SCOPING.md` § 6 tasks 2 and 16–17 assume otherwise. Binds
task 4.

**C20 — `Prepared` is a frozen dataclass of thirty-six fields and `_execute_prepared` unpacks them
one per line.** Adding `cells` is one field and one unpack line; nothing else in either list may
move. Binds tasks 4, 17.

**C21 — `arms_of` raises on a roster no unit of which carries a declared level** (*"the arm attribute
'x' does not resolve to the declared levels"*). `cells_of` must therefore be built by **intersecting
realized `ArmPlan`s**, never by calling `arms_of` per cell. Binds task 2.

**C22 — an empty cell's holdout fails on the TRAIN side**, not the test side (C9). A per-cell message
must not hard-code "test". Binds tasks 13, 14.

**C23 — the re-scoping predicts `_resumed_allocation`'s round-trip pin "must move"; the design derives
that it does not** (`within` is rebuilt from `group_axes`, which the resume overrides consistently).
**Task 17 is the pin's sole authorized editor anyway**, with `unchanged` as the post-edit state
specified in advance. Binds tasks 1, 16, 17.

**C24 — the count is 23, not 20.** The three tasks the re-scoping's § 9 does not have are C5's, C6's
and C7's surfaces. Say 23 and derive it; do not merge to hit 20.

**C25 — `fold_basis` is imported by name into `validate.py` and `cli.py`.** `cell_fold_basis` must be
added to **both** import lists, and `partition_within_cells` and `cells_of` to `cli.py`'s. Binds
tasks 2, 3, 8.

**C26 — `cli` builds `partition_units`' `strata` map indexed, not `.get`-ed, and total over the
roster**, on the stated contract that `partition_units` raises `KeyError` on a gap. A per-cell
restriction must stay total over its own sub-roster or the contract changes. Binds task 8.

**C27 — `E-DATA-HOLDOUT-FOLD` still refuses a holdout beside a `fold` level, and this slice does not
touch it.** No fixture may declare both. The Ruling KK resume fixture is `groups × fold`; the holdout
resume is a separate fixture. Binds tasks 15, 17, 22, 23.

---

# Batch A — the pin and the decomposition

## Task 1

**Corrections that bind this task: C23.** **This is the last slice; nothing follows it.**

**Capture the guard pin, before anything else in this slice moves.** Five arms, in
`tests/test_units.py`, `tests/test_cli.py` and `tests/test_sweep.py` as each arm's subject dictates.
The sole authorized editor and the post-edit state of each arm are **specified now**, in the test's
own docstring, per H8a's rule.

| Arm | Pins | Authorized editor | Post-edit state |
|---|---|---|---|
| A | `partition_units(_roster(50), 5, "d")` byte-identical (the existing oracle, re-asserted in a new test that names this slice), plus the clustered and stratified draws at their pinned seeds | **NONE — no task in this slice may edit arm A** | unchanged |
| B | A no-group-axis run's `sweep.yaml`: each `partitions` entry's key set is exactly `{fold, test, train}`, and the document has **no** `partitions_within` key | **NONE** | unchanged |
| C | `_resumed_allocation`'s round trip: the rebuilt `allocation.json` equals the recorded one | **task 17, and only task 17** | **unchanged.** If task 17 measures otherwise it edits this arm **once**, appends `holdout.within` to the expected document, reorders nothing, and reports the measurement |
| D | A no-group-axis `_prepare_run` makes **exactly one** `partition_units` call, with the **bare** digest — counted by monkeypatching a counting wrapper at the name `cli` resolves | **NONE** | unchanged |
| E | A 6-unit, no-`sweep.groups` generated config's **exact** `validate` finding set | **NONE** | unchanged — in particular it must never gain `W-DATA-CELL-THIN` |

**Arm D's mechanism, because a monkeypatch aimed at the wrong name is a named trap.** Patch the
symbol `cli` calls, not `units.partition_units`, and assert both the call **count** and the `digest`
argument's value. Task 8 reroutes that call site through `partition_within_cells`; **arm D must
survive that reroute unedited**, so it is written against the name `cli` imports and task 8 is
required to keep calling `partition_units` from inside `partition_within_cells` rather than
inlining it.

**Must not touch:** any `src/` file. This task adds tests only.

**Mutation:** delete the shuffle inside `partition_units` — arm A must fail. Run it, confirm the
failure, restore by **behaviour** (re-run and see green), never by `git checkout -- <file>`.

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

## Task 3

**Corrections that bind this task: C4, C10, C25.** **Ruling LL binds this task**: `fold_basis`
answers one question and is not touched.

**Build `units.cell_fold_basis(roster, cluster_by, cells)`.**

```python
def cell_fold_basis(
    roster: UnitList,
    cluster_by: str | None,
    cells: Mapping[tuple[tuple[str, str], ...], frozenset[str]],
) -> int:
```

The minimum over **non-empty** cells of `fold_basis(sub_roster, cluster_by)`, where each sub_roster
is built from `roster` **in roster order**. **One number, not two, and not a mapping** — the return
type is `int`, exactly as `fold_basis`'. An empty `cells`, or one whose cells are all empty, returns
`fold_basis(roster, cluster_by)` — the one-cell reduction.

**Docstring must say:** that `fold_basis` is deliberately unchanged and why (its third caller asks a
different question — `limits.min_clusters`' denominator, over the whole unit table a resample draws
from); and that returning a per-cell mapping is forbidden for the reason `fold_basis`' own docstring
gives.

**Fixture (F2, the one every later task reuses):** 16 units; `control` = clusters `A`×5, `B`×3;
`treatment` = `C`×4, `D`×3, `E`×1; **clusters nest inside arms, no spanning cluster** (C1's fixture
deliberately has one and is not used here). Computed literals: cell cluster counts **2** and **3**;
`cell_fold_basis` clustered = **2**, unclustered = **8**; whole-roster `fold_basis` clustered = **5**,
unclustered = **16**. **Cells with different cluster counts, so "minimum" and "first" differ.**

**Mutations:** MU-3 (`max` for `min` → `{kind: fold, k: 3}` must be refused: max 3 clears, min 2
refuses), MU-4 (return the first cell's basis → run the fixture with the cells in **both** orders,
naming them so one sorts first and the other last; a single order rules out only one wrong answer).

**Must not touch:** `fold_basis` — signature, body, docstring or tests.

---

# Batch B — the hoist and validate's cell view

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

## Task 6

**Corrections that bind this task: C4, C5, C25.** **Ruling LL binds this task and is the reason it
exists.**

**Thread the cell-aware basis into the two callers that ask the fold's question, and leave the third
alone.** In `validate_config`, after `_resolved_cells`, the `basis` local becomes
`cell_fold_basis(roster, usable_cluster, cells)` when `cells` is not `None` and non-trivial, and
`fold_basis(roster, usable_cluster)` otherwise — inside the **same** `try`/`except ContractError`
that already guards it. That one local feeds `_check_replication` **and** `_check_sweep` (C5); it is
one local and stays one local. In `_prepare_run` the same substitution, on `cells`.

**`_check_resample`'s `limits.min_clusters` call site keeps `fold_basis` unchanged.** **Delete** the
sentence *"Not threaded through `basis` in this slice; doing so is a cheap follow-up, not a
correctness gap today."* — after this slice threading it would be a defect, not a follow-up. Add one
clause to the paragraph above it naming cells as the third reason the two derivations are not the
same. **Delete rather than rewrite** wherever the choice exists.

**Mutation:** replace the `min_clusters` site's `fold_basis` with `cell_fold_basis` — a test must
fail, namely a `between` design with a thin cell and a `resample` whose `min_clusters` is satisfied
by the whole roster. Write that test in this task; without it the mutation is silent and the silence
would be evidence about the tests, not the code.

**Must not touch:** `fold_basis`, `_check_resample`'s holdout narrowing, `_fold_k`.

## Task 7

**Corrections that bind this task: C12.**

**Give `E-REPL-FOLD-K-TOO-LARGE` its cell clause at ALL THREE emit sites**, and rewrite its **one**
§ Errors `validate` reports row to cover them. The three: `validate.py`'s `c.error`, and
`replication._fold_k`'s two raises (units and clusters). Each message, when the basis came from cells,
names the cell — its `(axis, level)` pairs — and, under `cluster_by`, that cell's cluster count.

`_fold_k` sees a declaration and a count and never a roster, so the **cell label** arrives as an
optional argument beside `fold_basis`, defaulting to `None`, and every existing caller is unchanged.
**State in the docstring that a `None` label is "no cells resolved", not "cells resolved and
unnamed"** — a helper that ignores an argument hides what its callers stopped testing.

**Mutation MU-7:** reach the clause at only two of three sites — three tests, one per site (a fixed
`k` through `validate`, a `k: all` through `resolve_repeats`, a direct `_fold_k` call), each
asserting the **message names the cell**, not just the code.

**Report must state:** the grep it ran (`grep -rn "E-REPL-FOLD-K-TOO-LARGE" src/`), its hit count,
and every hit attributed. **Report what you grepped, not a count without a noun.**

**Must not touch:** the row for any other code; `_fold_k`'s existing two messages' unclustered text.

---

# Batch C — the fold half

## Task 8

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

## Task 9

**Corrections that bind this task: C1.**

**The cell fixture and its can-fail control**, as tests rather than as prose. Assert the design's
measured table with its mapping stated in the docstring: `[7, 3, 3, 1, 1]` whole roster,
`[7, 1, 0, 0, 0]` in `control`, `[3, 2, 1, 1, 0]` in `treatment` — **and say that cluster `S2` spans
both arms**, which is what makes the counts 2 and 4 and what distinguishes this table from
`H3c-3-SCOPING.md`'s `[3, 3, 1, 0, 0]`. The whole-roster row is the **can-fail control**: same
fixture, same `k`, no empty fold. Without it the table shows only that small rosters make small
folds.

Then assert the same design **after** the per-cell draw: no cell contributes an empty fold at the
`k` task 7's bound admits, and the bound refuses the `k` that produced the empty ones.

**Must not touch:** any `src/` file. Tests only.

## Task 10

**Corrections that bind this task: C2, C18.**

**Retire `E-REPL-FOLD-CELLS`.** Remove the `fold` arm of `validate._check_evaluation_split_cells`.
The function keeps its `holdout` arm until task 16; when both arms are gone the function and its
call site go with them, and **`tests/test_validate.py::test_a_group_axis_alone_triggers_the_refusal_without_between`
is DELETED, not adapted** (C18).

**And pin the property the refusal was standing in for**, by mutation rather than by assertion:
`runner.attrition`'s per-arm denominator (`handed = union(fold_members) & keys` against the **arm's**
roster) and `runner._handed_keys`' per-`(arm, fold)` answer are **non-empty**, *because* of task 3's
bound. The mutation: remove the cell clause from the bound and watch a real `run` produce an arm
whose denominator for some fold label is **zero**.

**Must not touch:** `E-DATA-HOLDOUT-CELLS`, either assert in `runner.execute_plan`, `attrition`'s
narrowing rule.

**This task declines nothing, but note for the record:** the per-**stratum** fold bound stays a check
that does not exist, in this build and every build — **there is no later slice.** Task 19 owns
saying so.

## Task 11

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

## Task 12

**Corrections that bind this task: C13.**

**Verify — assert rather than assume — that the flat `fold_members` mapping survives per-cell
partitions, across ALL FOUR `stats.py` readers**, not the one `H3c-3-SCOPING.md` named. The four:
`handed_to`, `_gather_repeats`, `collapse_repeats`, `repeats_disagreeing` (the last two are H5b's
split, which is what killed the "only contact point" claim). Plus `runner.attrition`,
`runner._handed_keys`, `runner._units_failed_anywhere`.

**Expected outcome: no code change, one test per reader.** If a reader turns out to need arm
narrowing it does not have, this task grows and the report says so rather than the reader being
patched quietly.

**The property to assert:** each unit is in exactly one cell and in exactly one partition, so
`fold_members` stays a flat `label → frozenset(keys)` that partitions the roster — the same shape
`fold_members_for` produced before.

**Must not touch:** any of the seven readers, unless the verification fails.

---

# Batch D — the holdout half

**Ruling II governs this batch.** Task 13 lands before task 15; **task 15 narrows `holdout_train`
per arm and deletes `assert holdout_train is None or arm_members is None` in ONE commit**; task 16
retires `E-DATA-HOLDOUT-CELLS` strictly after task 15. **No commit exists in which the assert is gone
and `holdout_train` still comes from `roster`.**

## Task 13

**Corrections that bind this task: C9, C10, C22, C27.**

**`cli._resolved_holdout` gains `group_axes` and loops `holdout_for` per cell.** One seed **per run**
— `holdout_seed_for(block, digest, roster)` over the whole roster, computed once and passed to every
cell's draw. The sub-rosters differ, so the draws differ; this is the bare-digest rule of task 8 in
the holdout's currency, and it is what keeps a **pinned** integer seed working (a pinned seed is
returned literally and must survive a roster that grows, shrinks or reorders).

The per-cell plans are merged into one `HoldoutPlan` whose `train` and `test` are the unions, in cell
order, each cell's own order preserved.

**Empty and thin cells (C9, C22).** `holdout_for` **raises** on an empty sub-roster — on the
**train** side, not the test side — and on a 2-unit cell at `frac: 0.2` on the test side. The loop
does **not** swallow either: it catches the `ContractError` and re-raises with the cell named,
because a message reading *"over 0 resolved units"* sends a reader to the roster when the fault is a
crossed combination nothing carries. Task 14 is what stops most of these reaching here.

**Rewrite the docstring's *"`group_axes` is deliberately not a parameter"* paragraph.** It is now
false. **Delete it and state what is true**, rather than editing it into something that half-survives.

**Fixture F6:** 20 units, two arms of 10, `frac: 0.2` → **each cell's test side is exactly 2** and
the union is 4. **The assertion is per cell** — `len(test ∩ arm) == 2` for both arms — because a
whole-roster draw satisfying `len(test) == 4` passes a union-only assertion.

**Must not touch:** `holdout_for`, `holdout_seed_for`, `holdout_sizes`, `_evaluation_roster`,
`E-DATA-HOLDOUT-FOLD` (C27).

## Task 14

**Corrections that bind this task: C6, C7, C9, C22.**

Two things, both of which neither scoping names.

**(a) `validate._holdout_test_roster` gains the cells (C6).** It realizes the holdout through
`holdout_for` over the whole roster and feeds `limits.min_clusters`. Once task 13 draws per cell,
these are two answers to one declaration — the exact defect `holdout_for`'s purity exists to prevent.
It takes `_resolved_cells`' answer and loops the same way task 13 does, through **one shared helper**
so that `validate` and `run` cannot drift; the helper lives in `units.py` beside `holdout_for` and
both callers call it. **Grep for a helper that already exists before writing one.**

**(b) `E-DATA-HOLDOUT-EMPTY` is bounded by the smallest non-empty cell (C7).** `_check_holdout`'s
`holdout_sizes(len(roster), frac)` becomes `holdout_sizes(len(smallest non-empty cell), frac)` when
cells resolve, and the message names that cell. **Both of the code's rows move** — § Errors `validate`
reports and § Errors core raises — and **each is checked against its OWN table's scope sentence**.
This is a **widening of one code, not a new one**: the remedy is unchanged, and a second code would
give one remedy two names.

**Fixture F7:** 20 units split **18/2**, `frac: 0.2`. `holdout_sizes(20, 0.2) == (16, 4)` clears;
`holdout_sizes(2, 0.2) == (2, 0)` does not → `E-DATA-HOLDOUT-EMPTY` at `validate`, naming the 2-unit
cell. **Can-fail control:** the same 20 units split 10/10 validates clean.

**Mutation MU-13:** leave the bound at `len(roster)` — F7 must fail.

**Report must state:** the grep for every `E-DATA-HOLDOUT-EMPTY` site and each hit attributed, and
which table's scope sentence put each row where it is.

**Must not touch:** any other `_check_holdout` finding; the ten-finding enumeration in its docstring
must be **updated**, not left stale.

## Task 15

**Corrections that bind this task: C27.** **RULING II BINDS THIS TASK, and it is the single most
important task in the slice.**

**Narrow `holdout_train` per arm in `runner.execute_plan`, and delete
`assert holdout_train is None or arm_members is None`, IN ONE COMMIT.**

Today: `scoped_units = UnitList([u for u in units if u.key in arm_keys])` then
`step_units = UnitList(list(scoped_units), train=holdout_train)` — and `holdout_train` is built in
`cli` from `roster`, never from the arm. **The sibling that already got it right is fifty lines below
in the same function:** the fold branch composes
`train=UnitList([u for u in scoped_units if u.key not in handed])`. Copy its narrowing — and copy
**where it sits**, not only what it calls.

The composition becomes, for a condition-scoped execution with an arm:

```python
train_units = holdout_train
if arm_members is not None and execution.condition_index is not None:
    train_units = UnitList([u for u in holdout_train if u.key in arm_keys])
step_units = UnitList(list(scoped_units), train=train_units)
```

with `arm_keys` the **execution's own** arm, not any other.

**The first assert stays.** `assert holdout_train is None or fold_members is None` guards
`E-DATA-HOLDOUT-FOLD`, which this slice does not touch (C27).

**Update `cli._resolved_holdout`'s and `execute_plan`'s docstrings** where they cite
`E-DATA-HOLDOUT-CELLS` as the reason a branch is unreachable — three sites, and a grep for the code
across `src/` is how you find them all, not a memory of which files the scoping listed.

**Fixture F4, and it lands IN THIS COMMIT because it cannot exist before or after.** With
`E-DATA-HOLDOUT-CELLS` still live no end-to-end `run` can reach the composition, so the fixture is a
**direct `execute_plan` call** — and that call trips the very assert being deleted. Two arms of 4
units, `holdout_train` over the whole roster. Assertions: `set(io.units.train) ⊆ arm A's keys`
**and** `set(io.units.train)` is **non-empty** — a subset assertion alone passes on an empty train
side.

**Mutation MU-8:** narrow to the wrong arm (`arm_members[0]` rather than the execution's) — F4's two
arms with asymmetric membership catch it.

**Cost if this is got wrong:** a model trained on units it is then evaluated against, across arms,
with no diagnostic. **There is no later slice to catch it.**

**Must not touch:** the fold branch, the first assert, `attrition`'s narrowing rule.

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

## Task 17

**Corrections that bind this task: C10, C11, C20, C23, C27.** **RULING KK BINDS THIS TASK.**

**Make the safety argument fail before you write its replacement.** `_resumed_allocation`'s docstring
rules that fold partitions need no override because *"`partition_units` is a pure function of the
roster and the design digest."* Under cells it is also a function of the **cell decomposition**,
which this same function overrides one call later.

**Step 1, and it is not optional: build the mutation and watch it fail (C11).** A `Prepared` whose
`group_axes` were drawn from a roster in **reverse** resolution order, against an `allocation.json`
recorded from the forward order. Measured literals to check your fixture against: `units_hash`
forward `sha256:f3ba4914…` / reversed `sha256:ee083cab…`; `assign_seed_for({"method": "random"},
"arm", "d", ·)` → `2988051695` / `1647976561`; the realized `c` arm `[u01, u04, u05]` /
`[u02, u04, u05]`. `_resumed_allocation`'s guards compare **sets** of levels and **sets** of keys, in
both directions, and nothing about order — so the stale reading passes every guard.

**Step 2: re-derive.** Call the **same** producer `_prepare_run` calls —
`units.partition_within_cells` — on the **overridden** axes, and replace `Prepared.partitions` and
`Prepared.fold_members`. **Unconditionally**, with no `if group_axes` gate: with no axes the producer
takes the one-cell path and returns the identical partition, and a branch is one more thing to get
wrong than a proof. **Do not re-derive by hand here** — that would make this function a second
producer of fold membership, the fault its own docstring exists to prevent a third instance of.

**Step 3: replace the docstring paragraph by deleting it**, and state what is now true: the partition
is a function of the roster, the digest and the cell decomposition; the decomposition is overridden
here; therefore the partition is re-derived here, through the single producer.

**Guard-pin arm C (C23).** You are its **sole authorized editor**. The design derives that it does
**not move** — `within` is rebuilt from `group_axes`, which this function overrides consistently.
**Measure it.** If it does move, edit arm C **once**, append `holdout.within` to the expected
document, reorder nothing, and report the measurement. If it does not move, say so and leave it.

**Fixture F5, and F5 is `groups × fold`, never `groups × holdout` (C27):** the assertion is on
partition **membership**, not on sizes — both decompositions give the same sizes.

**Mutations:** MU-9 (the pre-slice code: no re-derivation → F5 fails), MU-10 (add a `group_axes`
gate → guard-pin arm D plus a no-axis resume asserting byte-identical partitions fails).

**Must not touch:** `Prepared`'s other fields (C20); `arm_members`' second call; the set-equality
guards.

---

# Batch E — the thin cell, the interactions, the filings

## Task 18

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

## Task 19

**Corrections that bind this task: none directly; read C8 and C9 for context.**

**The empty-cell × empty-fold-per-cell interaction — refused where it can be, RECORDED where it
cannot.**

- A cell too thin for `k` is **refused** at `validate` by task 7's clause, computed from task 3's
  bound. Pin it.
- A cell that is **empty** (a crossed combination no unit carries) makes the bound `0`, so any
  `k ≥ 1` is refused. Pin that too — and pin that an empty cell with **no** evaluation split declared
  is not an error at all, only task 18's warning.
- The per-**stratum** bound is **still a check that does not exist.** Cells add a **third** multiplier
  to `partition_units`' `c × s` independent lists. Update that docstring to say `cells × c × s`, and
  state explicitly that this slice **has not added** the per-stratum bound.

**This slice must not appear to have added a bound it did not add**, and **there is no later slice**
to add it: the filing task 20 writes says so as a fact, not as a deferral.

**Must not touch:** `partition_units`' body.

## Task 20

**Corrections that bind this task: C1.** **This task is where "no slice follows" is written down.**

Three things.

**(a) Strike the closed filing.** `spec-defects.md`'s `## OPEN — an evaluation split cannot be drawn
within a cell` is closed by this slice: strike it in place, this file being the one exception to the
never-retro-edit rule, and name the slice that closed it.

**(b) Sweep every entry whose `unassigned` reason enumerates *"H3c-3's remaining 14"*.** `grep -c
"H3c-3" docs/superpowers/spec-defects.md` → **56 lines** at `3d72910`; 57 headings begin `## OPEN`.
That phrase becomes **false** the day this slice merges. Rewrite each occurrence to the form the file
requires: **`unassigned`, with the reason stated as a fact — *no slice follows this one*** — not as a
deferral and never as *"whichever slice next touches X"*, the form this file rejects by name.

**(c) File the three gaps this slice declines**, each with the no-later-slice sentence:

1. **A cluster spanning two cells** (design Decision 13). Legal under `by_attribute`, impossible under
   `random` (which allocates whole clusters). Breaks the between-sides independence H4c's
   `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered` assume, each side
   contributing `G_s − 1` to a Welch-Satterthwaite df while a spanning cluster is counted twice. The
   check that would close it is a constant-cluster-within-arm rule, `stratum_varies_within_cluster`'s
   shape one declaration over. **Owner: `unassigned`. Reason: no slice follows.** Note that C1's own
   measured fixture has one.
2. **`limits.min_clusters` under cells** (design Decision 4). The denominator stays roster-wide;
   H3d already found it *"wrong in the direction of NOT firing"*. **Owner: `unassigned`. Reason: no
   slice follows.**
3. **The per-stratum fold bound** (task 19). **Owner: `unassigned`. Reason: no slice follows.**

And **re-read every filing whose text describes code this slice changed** — a filing's claims about
the code go stale like any other comment.

**Must not touch:** any `src/` file. **A ledger line saying "filed" is not a filing:** the entry must
exist in `spec-defects.md`, and the report must quote its heading.

---

# Batch F — documents and end to end

## Task 21

**Corrections that bind this task: C2, C18.**

**The document sites, none of them locatable by position.** Name what a sibling row *does*; when you
insert or remove a row, check every row it **moved** and every count phrase near it.

| Site | What happens |
|---|---|
| `reference.md` § Validation, *One split, not one cell each* | **Removed** — the refusal it describes is gone |
| `reference.md` § Validation, *Folds fit inside the cells* | **Rewritten BACK, not deleted.** It currently reads *"Superseded by One split, not one cell each"* — deleting the pointed-at row and leaving the pointer is how a table acquires a dangling reference. Restore its pre-H3d meaning: `k` bounded by the smallest cell's unit count, or its cluster count under `cluster_by` |
| `reference.md` § Errors `validate` reports | The `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` rows **removed from the registry** |
| `reference.md` § A fixed holdout split | The *"A roster-wide split beside a cell structure is refused, not drawn"* bullet **replaced** by what is now true: the split happens within each cell, and `frac` is bounded by the smallest cell |
| `reference.md` § Clustered units | The *"Under `allocation: between`, a roster-wide fold is refused rather than drawn within each cell"* paragraph **rewritten to the present tense**, keeping *"Partitions are computed once per run, not once per condition"* and the paragraph that reconciles the two — **which survives cells and needs no change** |
| `experimental-designs.md` § Between-subjects factorial | *"A fold or a holdout drawn within each cell is not built"* → what is built |

**C2: none of these is repairing a present-tense falsehood** — all three "not built" sentences are
honestly marked today. They are repairing a **build state that moved**.

**Run both consistency passes.** Mechanical: every relative link and `#anchor` resolves, no duplicate
anchors, table rows match header column counts, no trailing whitespace or tabs, `×` not `x`, hyphens
in anchors — skipping fenced blocks throughout. Cross-document: the shared worked example (untouched
here, and confirm it), config completeness, enum comments, schema fields in prose, declared vs.
derived, prevented mistakes. **After removing `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS`, grep
the four documents, `CLAUDE.md` and the feasibility analysis for what should no longer exist** —
and **filter the file list, never the output of the sweep.**

**Must not touch:** `docs/superpowers/**` except as tasks 20 and 23 direct; the development record is
exempt from both passes and retro-editing it destroys the evidence it holds.

## Task 22

**Corrections that bind this task: C27.**

**Two end-to-end `run`s**, outside the repository, through the real console script.

1. **`groups × fold`.** Assert: `sweep.yaml` carries `partitions_within`; per-cell membership is
   recoverable by crossing `partitions` against `allocation.json`'s `arms`; `io.units.train` is
   inside the arm for every condition-scoped execution; and the per-condition identity
   `resolved == completed + ineligible + failed` holds.
2. **`groups × holdout`.** Assert: `allocation.json`'s `holdout` carries `within`; each arm's test
   side is the declared fraction **of that arm**; `io.units.train` is inside the arm — the property
   task 15 proved by direct call, now confirmed end to end; and the same attrition identity.

**No fixture declares both a holdout and a fold** (C27).

**Must not touch:** anything. This task adds tests and runs commands.

## Task 23

**Corrections that bind this task: C11, C27.**

**An end-to-end `resume` over a `groups × fold` run with `method: random`** — the fixture § 6.2 of
the re-scoping says H9b could not build. The lever is **roster order** (C11): the second attempt must
resolve the same keys in a different sequence, which moves `units_hash`, hence `assign_seed_for`,
hence the fresh draw — while `_resumed_allocation`'s set-equality guards pass.

**The risk, stated in advance rather than discovered.** The cheapest lever, reordering the rows of
`index.csv` between attempts, may be blocked by the input-manifest gate, since the manifest covers
file contents. **Check that first.** If it is blocked, the end-to-end lever is a **plugin resolver**
whose returned order varies while it reads no file (so the manifest is unchanged), and if that also
fails, this task's end-to-end arm is **declined in writing** and task 17's direct-call fixture F5
stands as the proof — which it already is. **Do not report success on an arm that did not run.**

**Also run an end-to-end `resume` over a `groups × holdout` run** (a separate fixture, C27),
asserting the recorded holdout is honoured rather than redrawn.

**Must not touch:** `_resumed_allocation` (task 17 owns it); guard-pin arm C.

**Report must state:** which lever worked, measured, and — if the end-to-end arm was declined — that
it was, and that **there is no later slice** to take it up.

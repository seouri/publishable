# H3c-3 scoping: folds within cells

Read-only measurement at `main` (`df6b4d4`), after H3c-1 and H3c-2 landed and after the
2026-08-13/14 re-amendment of the build order to `H7a → H4 → H3d → H3c-3 → H7`.

The charter is `H3c-SCOPING.md` § The task enumeration the 36 comes from, *"H3c-3, folds within
cells — 6"*. It predates both shipped sub-slices. **Five of its six lines survive; the count does
not.** Measured decomposition below is **17**, of which 2 are the H3d retrofit the reorder
assigns here and 4 are items no charter names.

**Everything in § 1 and § 2 is a build fact, verified by grep or by execution. Everything in § 3
is a spec claim, and the two are kept apart on purpose** — the immediately preceding fix
(`162e180`) exists because they were conflated in the feasibility analysis.

## 1. What exists

| Name | Where | State |
|---|---|---|
| `units.partition_units` | `units.py` | Built. Takes `roster, k, digest, clusters=, strata=`. No cell parameter, and none is wanted (§ 4) |
| `units._assign_whole_clusters` | `units.py` | Built. The single assignment rule; H3c-2 was required not to disturb it and did not |
| `units._assign_whole_clusters_by_ratio` | `units.py` | Built by H3c-2 as a **sibling**, explicitly so the fold oracle was not put at risk |
| `units.fold_basis(roster, cluster_by)` | `units.py` | Built. Two inputs, one number |
| `units.cluster_count` / `cluster_count_of` / `clusters_of` | `units.py` | Built. The single cluster authority |
| `replication._fold_k(level, fold_basis, cluster_by)` | `replication.py` | Built. Two `E-REPL-FOLD-K-TOO-LARGE` messages, units and clusters |
| `replication.resolve_repeats(config, digest, fold_basis=)` | `replication.py` | Built. `fold_basis` is still the only channel roster facts reach it by, on both arrival paths |
| `replication.fold_members_for(levels, partitions)` | `replication.py` | Built. Flat `label → frozenset(keys)` |
| the one `partition_units` call site | `cli.command_run` | Built. `grep -rn partition_units src` returns the definition, this call, and one `sweep.py` comment |
| `units.arms_of(roster, column, levels)` | `units.py` | **H3c-1.** Reads an arm out of a column, roster order |
| `units.ArmPlan` | `units.py` | **H3c-1.** `levels`, `members`, `seed`, `strata` — the realized shape a read and a drawn axis both fit |
| `units.assignment_for(...)` | `units.py` | **H3c-1/2.** The single producer of an `ArmPlan`; allows `by_attribute`, `random`, `blocked` and refuses anything else |
| `units.arm_members(axes, conditions)` | `units.py` | **H3c-1.** `condition.index → frozenset(keys)`, the intersection of each selected axis's arm. Takes **no roster**, deliberately |
| `cli._resolved_group_axes(units_decl, sweep_block, roster, digest, clusters)` | `cli.py` | **H3c-1/2.** Realizes every axis **once per run**, in declaration order |
| per-arm `n` reconciliation | `runner.attrition` | **H3c-1.** `resolved` is whichever roster the call site passed — arm or whole — and `attrition` must not re-derive the narrowing. `handed` is `union(fold_members) & keys` |
| arm-before-fold narrowing | `runner.execute_plan` | **H3c-1.** Arm narrowing is applied to `scoped_units` **before** the fold branch, so `io.units.train` is the arm's complement, not the roster's |

**What is genuinely new in this slice is one derivation and one caller change; everything else is
a caller change or a document.** New: the *cell* decomposition — the intersection of every group
axis's arms — which no function produces today. `arm_members` is the nearest thing and is the
wrong shape: it is keyed by **condition index**, and under `groups × grid` several conditions
share one cell while under a group axis alone the mapping omits every condition selecting no
axis. Cells must be derived from the `ArmPlan`s directly.

Caller changes: `fold_basis` gains an argument; `_fold_k` gains a message clause; `command_run`
loops `partition_units` per cell and merges index-wise; `build_sweep_document` composes `train`
within a cell. `partition_units`, `_assign_whole_clusters`, `_seed_from`, `arms_of`,
`assignment_for`, `ArmPlan` and `arm_members` are all **untouched**.

**One structural fact the charter could not have known, and it is what makes "the caller's loop"
true.** In `cli.command_run` the order today is: cluster mapping → `fold_basis` →
`resolve_repeats` → `partition_units` → `expand(doc)` → `_resolved_group_axes` → `arm_members`.
Both the per-cell basis and the per-cell loop need the `ArmPlan`s, which are resolved **after**
both. So this slice **hoists arm-plan resolution above repeat resolution** — a phase reorder in
one function, not a rewrite of anything. `_resolved_group_axes` already documents itself as
"realized once per run", and hoisting keeps that literally true; nothing else reads the plans
before `expand`.

## 2. The bit-stability oracle, and what may move

Pinning tests, all in `tests/test_units.py`:

| Test | Pins |
|---|---|
| `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` | the full 5×10 fold contents at `_roster(50)`, `k=5`, digest `"d"`. **The oracle.** H3b's rewrite and H3c-2 both had to leave it byte-identical |
| `test_the_clustered_draw_follows_the_digest` / `test_the_same_digest_reproduces_the_same_clustered_split` | draw is a function of the digest, and only of it |
| `test_the_clustered_stratified_split_pins_which_fold_each_cluster_lands_in` | which fold each cluster lands in, at a seed |
| `test_the_same_digest_reproduces_the_same_stratified_split` | stratified determinism |
| `test_every_unit_appears_in_exactly_one_partition`, `test_partitions_cover_the_roster`, `test_partition_sizes_differ_by_at_most_one`, `test_no_cluster_is_split_across_folds`, `test_no_cluster_is_split_across_a_stratified_fold` | the structural contract |
| `tests/test_cli.py`'s two `sweep["partitions"]` assertions and `tests/test_sweep.py::test_a_fold_level_records_its_partitions` | the recorded shape |

**May not move.** Every one of the above. Concretely: `_assign_whole_clusters`, `_seed_from`, and
`partition_units`' own signature and body. A design declaring no group axis must call
`partition_units` exactly once, over the whole roster, with the bare `digest` — byte-identical.

**May move.** Only what a design *with* a group axis sees: the number of `partition_units` calls,
the composition of `sweep.yaml`'s `train` side, and `fold_basis`' answer.

**The one way to break the oracle, named so nobody takes it.** Decorrelating cells by mixing a
per-cell digest (`digest|arm=control`) is the obvious implementation and is safe **only** if the
no-groups path never touches it. A cleaner rule that needs no guard: pass the bare `digest` to
each per-cell call. `partition_units` builds its own `random.Random(_seed_from(digest))` per
call, so per-cell calls are independent of cell **order** and of how many cells there are —
strictly better than the per-stratum branch, whose threaded RNG makes each stratum's draw depend
on how many preceded it (`H3c-SCOPING.md` § What "drawn within each cell" adds). A one-cell
design then reduces to the current single call, which is the new regression to pin *in addition
to* the existing oracle, not instead of it.

**A fold regression bought for an arm feature is the trade this slice must not make**, and it is
the same sentence `_assign_whole_clusters_by_ratio`'s docstring already carries.

## 3. What the documents specify — spec claims, not build facts

| Claim | Where | Built? |
|---|---|---|
| "folds and holdouts are drawn *within* each cell" | `experimental-designs.md` § Between-subjects factorial | **No** |
| "Under `allocation: between`, folds are drawn within each cell … `k` is bounded by the *smallest* cell's unit count — or its cluster count, when `cluster_by` is declared — and `validate` rejects a larger one" | `reference.md` § Clustered units | **No.** Present tense, no `NOT BUILT` marker |
| Row *Folds fit inside the cells* | `reference.md` § Validation | **No.** Unmarked, while its two neighbours *Cells are populated* and *Allocation is coherent* both say "specified, not built in this build" |
| "Under `allocation: between`, the split happens within each cell" (holdout) | `reference.md` § A fixed holdout split | No — the whole block is `NOT BUILT`, so this one is honestly covered |
| "**Partitions are computed once per run, not once per condition**" | `reference.md` § Clustered units | Built, and **it survives cells** |

**On "once per run": no document change is owed, and that is a finding rather than a relief.**
The paragraph immediately after it already reconciles the two — *"This is not an exception to
'once per run': the boundaries are still derived once from the design digest, and every condition
on a given arm sees the same ones, which is exactly what paired contrasts within an arm need."*
The reconciliation is sound under the implementation § 2 prescribes: cells are disjoint, each
cell is drawn once from the run's digest, and two conditions in the same cell get the same
boundaries, which is what pairing needs. What must **not** happen is a per-*condition* draw;
`groups × grid` puts several conditions in one cell and they must share.

**Three defects in the documents, all of the class `162e180` fixed elsewhere:**

1. The § Validation row and the § Clustered units paragraph both state unbuilt behaviour in the
   present tense, unmarked, beside marked siblings. A reader checking whether their design is
   safe gets the wrong answer today.
2. The row is **silent on `assign.method`**, and the answer differs by method (§ 5).
3. § The other files a run writes says `partitions` carries "the unit keys in each fold's train
   and test side" and says nothing about cells; the shape under cells is undecided (§ 5).
4. The same sentence also promises "**the realized fold sizes** when `cluster_by` makes them
   uneven", and § Clustered units repeats it — core "records the realized sizes in `sweep.yaml`".
   `build_sweep_document` writes `fold`, `test` and `train` and nothing else; `grep -n sizes
   src/publishable/sweep.py` returns nothing. Same conflation class as the three above, in the
   exact sentence task 12 already edits, so it free-rides on that task.

**The empty-fold-per-arm case is specified nowhere.** `_fold_k` refuses a fold with no units
("a fold with no units is a declaration error, not a small fold"), and `partition_units`'
docstring admits it reaches that state by the per-stratum path anyway. Cells add a third
multiplier: `c × s` independent lists. `H3c-SCOPING.md` § 9 recorded the per-stratum bound as a
check that does not exist and warned H3c "must not accidentally claim to have added it" — that
warning stands for this slice too.

**Measured at HEAD** (15 units; clusters S1×7 S2×3 S3×3 S4×1 S5×1; `arm` by attribute, 8/7):

| Call | Sizes at `k = 5` |
|---|---|
| whole roster, `clusters=` | `[7, 3, 3, 1, 1]` — no empty fold |
| `control` cell (8 units, **2** clusters) | `[7, 1, 0, 0, 0]` — three empty folds |
| `treatment` cell (7 units, 3 clusters) | `[3, 3, 1, 0, 0]` — two empty folds |

The `control` row reproduces `H3c-SCOPING.md`'s table exactly; the `treatment` row differs from
its `[3, 2, 1, 1, 0]` because that fixture put 4 clusters in `treatment` where this one puts 3 —
same 8/7 arm sizes, different cluster-to-arm mapping. Not a regression, and said here because two
tables carrying the same fixture description and different numbers will otherwise read as one.

`fold_basis` answers 15 unclustered and 5 clustered, so `{kind: fold, k: 5}` passes `validate`
today. The whole-roster row is the can-fail control: same fixture, same `k`, no empty fold. **So
this is a live correctness defect, not a missing convenience** — since H3c-1 shipped, a
`groups` + `between` + `fold` config validates clean and runs folds that are roster-wide, and
nothing in `validate.py` pairs `allocation` with a repeat kind (`grep` for a check joining them
returns nothing; no test in the suite declares both).

## 4. The retrofit inherited from H3d

H3d ships first under the amended order, so it will draw a holdout that respects clusters and not
cells. What H3c-3 then has to change depends entirely on **where H3d attaches its draw**:

- If H3d draws the holdout in `command_run` in the same region as the fold branch, the retrofit
  is **the hoist (already this slice's task 2, done once for both) plus a `holdout_basis`
  per-cell minimum mirroring `fold_basis`' and a per-cell loop around the same call**. Small: a
  reordering and two small functions, no new concept.
- If H3d instead resolves the holdout earlier (it is `data.units`, not `replication`, so
  attaching it beside `clusters_of` is a plausible reading) and treats it as a roster-level fact
  the conditions inherit, the retrofit reaches `allocation.json`'s `holdout` key, the
  `provenance.allocation_hash` payload, and `io.units.train` — still not a rewrite, but 2–3 extra
  tasks, and it would touch a shipped artifact's shape.

**Verdict: do not revert the order.** The measurement supports H3d first — it takes the outside
evidence from 3 of 9 to 9 of 9 with a table roster, and H3c-3 takes it from 9 to 9. The cost is
real but bounded, and it is *reducible to near zero by construction*: H3d should be required to
(a) perform the hoist itself, and (b) express its split as **"partition within each cell to
declared target proportions"**, which is `H3c-SCOPING.md` § What H3d needs stated in a particular
form's first requirement — written before the reorder and, if anything, more load-bearing now.
That requirement is what makes the holdout's cell loop the *same* loop as the fold's rather than
a second one. Add it to H3d's charter rather than discovering it in H3c-3.

**One thing the reorder does make worse and nobody has costed:** H3d ships a holdout whose own
document (§ A fixed holdout split, "the split happens within each cell") is false for the
duration between the two slices, on top of the fold claim already false today. See § 7.

## 5. Traps

| Trap | The rule, and where it bites |
|---|---|
| **`fold_basis`' "one number, not two"** | A third input must not become a second number. The basis stays one integer: `min` over cells of (cell unit count, or cell cluster count). What is *not* allowed is returning a per-cell mapping and letting `_fold_k` and the budget check each pick from it — that is precisely the "checked against one number while the partition is drawn over another" drift the function was written to remove. The cells argument is the roster decomposition; the return type does not change |
| **Order is contract** | `partition_units` shuffles clusters with the digest RNG then sorts largest-first, stably. Both halves are load-bearing and neither may be touched. The cell loop lives outside the function and merges index-wise, exactly as the `strata` branch merges internally — and index-wise merging is what makes fold *i* the union of every cell's fold *i*, which is what keeps `fold_members` flat (§ 6, task 11) |
| **An arm × fold cell can be empty** | H3c-1 recorded this as unowned. Two shapes: a *cell* with no units (a crossed design whose combination no unit carries), and a cell whose fold *i* is empty because the cell has fewer clusters than `k`. The first makes the per-cell minimum `0`, so `_fold_k` refuses via `E-REPL-FOLD-K-TOO-LARGE` with a message naming a cell — which is right, but the *cell's* emptiness is the real fault and `limits.min_units_per_cell` is still read by nothing. The second is what the per-cell bound exists to refuse. Neither may be papered over by skipping an empty cell in the loop |
| **Validate cannot see a drawn cell for free** | Under `by_attribute` the cells are a column read — `arms_of`, cheap and exact at validate time. Under `random`/`blocked` (H3c-2, shipped) cell membership exists only after a draw. `_check_assign` already performs a gated draw with the placeholder digest `"validate"`, sound *only* because it is restricted to the unstratified, unclustered case where sizes are digest-independent — and the per-cell **cluster count** is exactly the seed-dependent quantity that gating excludes. `design_digest(doc)` *is* computable at validate time, so a real draw is available, but making `validate` draw for real is a ruling the documents do not make (§ 6, task 1) |
| **Cells are not conditions** | `arm_members` is per condition; under `groups × grid` several conditions share a cell. Deriving cells from `arm_members` would draw one partition per condition and break "once per run" for real |
| **`train` composed across cells is a leak** | `build_sweep_document` builds `train` as every other partition's units. Under per-cell folds that includes the other arm. `runner` is already safe (arm narrowing precedes fold narrowing, with a docstring saying why); `sweep.yaml` is not |

## 6. Decomposition — 17, not 6

At the grain of H3a (12), H3b (13), H3c-1 (20), H3c-2 (14 measured against a charter of 10).
Charter lines are marked `[c1]`–`[c6]`.

1. **Documents-first, and it is three rulings rather than an edit.** (a) Does the per-cell bound
   cover drawn axes, and if so does `validate` draw for real or bound by `_apportion`'s target
   sizes? (b) `sweep.yaml`'s `partitions` shape under cells — flat with a `cell` key per entry,
   or nested. (c) What a cell's own fold reports as `n`. Plus marking the § Validation row and
   the § Clustered units paragraph honestly until the code lands.
2. **The hoist**: `_resolved_group_axes` and `arm_members` move above `resolve_repeats` in
   `command_run`, with the "realized once per run" property preserved and asserted.
3. **The cell decomposition** — a new `units` function producing disjoint sub-rosters from the
   `ArmPlan`s (not from conditions), including the empty-cell case and the no-axis case
   (one cell, the whole roster).
4. **`fold_basis` gains cells** `[c1]`: the minimum over cells, "one number, not two" preserved
   in the docstring and in the return type.
5. **Both arrival paths** `[c1]`: `validate`'s (`_check_units`'s basis, which needs cells and
   therefore needs whatever task 1(a) ruled) and `cli`'s.
6. **`_fold_k`'s cell clause** `[c2]`: a third `E-REPL-FOLD-K-TOO-LARGE` message naming the cell
   and, under `cluster_by`, the cell's cluster count — and its § Errors `validate` reports row.
7. **The cell loop at the call site** `[c3]`, index-wise merge, bare digest per cell.
8. **The bit-stability regression** `[c3]`: existing oracle untouched, plus a new pin that a
   one-cell design equals the roster-wide draw byte for byte.
9. **The cell fixture and its can-fail control**: unequal clusters per cell, asserting the
   `[7,1,0,0,0]` vs `[7,3,3,1,1]` contrast — `H3c-SCOPING.md` § Checks that could not fail's
   warning that coinciding cells and clusters make a cluster-aware partitioner look cell-aware.
10. **Row *Folds fit inside the cells*** `[c4]` implemented in `validate`, with the
    method-qualified behaviour task 1(a) ruled.
11. **`fold_members` shape verification**: assert, rather than assume, that the flat mapping
    survives per-cell partitions — `attrition` intersects `union(fold_members) & keys` against
    the *arm* roster, `stats.handed_to` and `runner._handed_keys` are per unit, and each unit is
    in exactly one cell. Expected outcome: no code change, one test. If a consumer reads
    `fold_members` without arm narrowing, this becomes 3 tasks and a shape change.
12. **`sweep.yaml`'s `partitions` per cell** `[c5]`, including composing `train` **within** the
    cell — a correctness change, not a formatting one — and its § The other files a run writes
    sentence.
13. **The empty-cell / empty-fold-per-cell interaction**, refused where it can be and *recorded*
    where it cannot: the `c × s` multiplication is stated in `partition_units`' docstring and
    explicitly not fixed, so this slice does not appear to have added the per-stratum bound.
14. **An end-to-end `run`** over `groups × fold`, asserting per-cell membership in `sweep.yaml`,
    `io.units.train` inside the arm, and the per-condition `resolved == completed + ineligible +
    failed` identity.
15. **The target-proportions contract H3d reuses** `[c6]`, stated as a reusable rule rather than
    as `k` folds — or, if H3d shipped first, verified against what H3d actually built.
16. **The H3d retrofit, part 1**: `holdout_basis` as the per-cell minimum, on the same
    decomposition.
17. **The H3d retrofit, part 2**: the holdout's own cell loop and `allocation.json`'s `holdout`
    key per cell, under the unchanged whole-file `provenance.allocation_hash`.

**Charter accuracy: 5 of 6 lines survive** (line 6, the target-proportions contract, is partly
overtaken by the reorder). Missed: the hoist, the cell decomposition as its own derivation, the
drawn-axis ruling at validate time, the `train` leak in `sweep.yaml`, the `fold_members`
verification, the documents-marking task, and both retrofit tasks. Charter 6 → measured 17, the
same direction and roughly the same magnitude as H3c-2's 10 → 14 and H3c-1's ~15 → 20.

**A second kind of staleness in the same charter section.** `H3c-SCOPING.md` § What "drawn within
each cell" adds cites the two `resolve_repeats` arrival paths as `validate.py:473` and
`cli.py:808`. Both are stale at HEAD — the calls are in `validate.validate_config` and
`cli.command_run` — and CLAUDE.md § Documentation conventions forbids line-number citation for
exactly this reason. Cite by function or by section when the tasks above are written up.

## 7. What is not in this slice, and what it is worth

**Not in it.** `limits.min_units_per_cell` (still read by nothing; a limits deliverable, and
*Cells are populated* / *Allocation is coherent* stay marked). The per-**stratum** fold bound —
still a check that does not exist, and this slice must not appear to add it. The unpaired
estimator family (H4). `resume` and `allocation.json`'s "read rather than re-drawn" (no reader
exists). Any change to `partition_units`' signature or to `_assign_whole_clusters`.

**What it is worth, argued.** It unblocks **none** of the nine experiments in
`docs/feasibility-llm-growth-studies.md` — none declares a `sweep.groups` axis or a `fold`
repeat — and it retires no refusal, which makes it the only remaining slice with neither kind of
external justification. Its value is exactly one thing, and it is worth stating plainly:

> **Two normative documents claim, in the present tense and unmarked, that core does something it
> does not do — and the thing it silently does instead is the leak class `experimental-designs.md`
> § Mistakes core prevents requires to be structurally impossible.**

That is a real cost, not a documentation nit: a `groups` + `between` + `fold` design validates
clean today and evaluates cells against roster-wide folds, with three of five folds empty on the
measured fixture. The unlock story is nil; the *false-claim* story is the whole justification.

**Which yields a third option the charter does not contain, and it is probably the right one.**
The repo's own precedent — `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`,
`E-DATA-ASSIGN-METHOD-UNSUPPORTED` — is to **refuse a combination while honouring both
declarations**, and route it. Refusing `{kind: fold}` (and, when H3d lands, `holdout`) beside
`allocation: between` under a new code, and marking the two passages accordingly, is **3 tasks of
the 17** (tasks 1, 6-as-a-refusal, and 10-as-a-refusal) and closes the false claim and the leak
completely. The remaining 14 buy a design nobody in the outside evidence has asked for.

**That price is checked, not assumed: the refusal makes no documented design unrunnable.**
`experimental-designs.md` declares `allocation: between` in four places (§ Between-subjects,
§ Between-subjects factorial, § Matched case-control) and a `fold` repeat in two
(§ Cross-validation's YAML, § Clustered and hierarchical data's prose "add `{kind: fold, k: 5}`
to the above"). **No section declares both** — § Cross-validation has no `sweep` block at all, and
§ Clustered and hierarchical data's fold attaches to its own clustered config, not to
§ Matched case-control's. So the refusal costs one § Mistakes core prevents-style entry and no
design-section rewrite, and the 3-task figure holds.

So the honest recommendation is not "defer indefinitely" and not "build it next":

1. **H3d ships next, as amended** — with the hoist and the target-proportions form written into
   its charter so the retrofit is small by construction rather than by luck.
2. **Ship the 3-task refusal now, or inside H3d** — because H3d otherwise adds a *second* false
   present-tense cell claim beside the one already live.
3. **Build the remaining 14 when a real design asks for cells and folds together**, which no
   evidence this repo has yet does. A refusal with a route is the shape this project uses for
   exactly that situation, and using it here costs nothing that a later slice cannot recover.

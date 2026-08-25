# H3c-3 — folds and holdouts inside cells: design

**Written 2026-08-25, against `main` at `d17d402`** (the H3c-3 re-scoping correction; `3d72910` is
the last code commit, and every measurement below was taken against that tree). The charter is
[`H3c-3-SCOPING-2.md`](../H3c-3-SCOPING-2.md), measured 2026-08-25 at `3d72910`, which decomposes
the slice at **20 tasks** and **recommends not building it**. This design is **23 tasks in six
batches**, and it overrules that recommendation under Ruling HH.

**This is the last slice in the project. Nothing is chartered after it.** That sentence appears
beside every gap this design declines, because it changes what a decline means: there is no later
owner, and every deferral here ships with the project rather than waiting for one.

Five controller rulings bind this slice: **HH** (build in full; record the alternative), **II**
(task 15 gates the retirement of `E-DATA-HOLDOUT-CELLS`), **JJ** (`limits.min_units_per_cell` is
decided, not declined), **KK** (`_resumed_allocation`'s safety argument is re-derived, not
patched), **LL** (`fold_basis`' second `validate` call site is a third question and must be named
as one). Each is a numbered decision below, with grounds measured rather than read.

Ruling S from [the re-entry seam design](2026-08-23-re-entry-seam-design.md) § Decision 2 is
discharged here by name: *"H3c-3's remaining 14 owns the phase hoist of exactly those two calls."*

---

## 0. What was measured, before any decision

Every probe below ran against `3d72910` with a clean tree, in the session scratchpad, **outside this
repository** — H6a made the dirty gate load-bearing. Nothing under `src/`, `tests/` or the four
documents was edited by this pass.

**M1. The empty-fold-per-cell table reproduces byte for byte, and its fixture has a property neither
scoping named.** Rebuilt at `3d72910` from the description both scopings give — 15 units; clusters
`S1`×7, `S2`×3, `S3`×3, `S4`×1, `S5`×1; `arm` by attribute, first 8 `control`:

| Call | `k = 5` sizes |
|---|---|
| whole roster, `clusters=` | `[7, 3, 3, 1, 1]` — no empty fold |
| `control` cell (8 units, **2** clusters) | `[7, 1, 0, 0, 0]` — three empty folds |
| `treatment` cell (7 units, **4** clusters) | `[3, 2, 1, 1, 0]` — one empty fold |

`fold_basis` answers **15** unclustered and **5** clustered, so `{kind: fold, k: 5}` clears `_fold_k`
on the numbers. **The property: "first 8 units are `control`" puts cluster `S2` on BOTH sides of
the arm boundary** — `control` is `S1`×7 plus one `S2` unit, `treatment` is the other two `S2` units
plus `S3`, `S4`, `S5`. That is what makes `control` 2 clusters and `treatment` 4, and it is why this
table reads `[3, 2, 1, 1, 0]` where `H3c-3-SCOPING.md` read `[3, 3, 1, 0, 0]` from 3 clusters. § 9
treats the spanning cluster as a claim of the fixture rather than an accident of it.

**M2. `assign_seed_for` moves when the roster's ORDER moves, and H9b's guards do not check order.**
`units_hash` over six units forward is `sha256:f3ba4914…`, reversed `sha256:ee083cab…`;
`assign_seed_for({"method": "random"}, "arm", "d", ·)` answers `2988051695` forward and `1647976561`
reversed, and the realized `ArmPlan` differs — `c: [u01, u04, u05]` forward against `c: [u02, u04,
u05]` reversed. `_resumed_allocation` checks each axis's **set** of levels and each membership's
**set** of keys, in both directions, and nothing about order. **So Ruling KK's mutation is
constructible** and is not owed a replacement (§ 11).

**M3. `holdout_for` over an empty sub-roster raises, and over a 2-unit one at `frac: 0.2` raises
too.** Both are `ContractError` `E-DATA-HOLDOUT-EMPTY` — *"over 0 resolved units leaves the train
side empty"*, *"over 2 resolved units leaves the test side empty"*. `holdout_sizes(0, 0.2)` is
`(0, 0)`. So an empty or thin cell is not something the per-cell holdout loop may skip past: it
raises inside the loop unless `validate` refuses it first (Decision 10).

**M4. `E-REPL-FOLD-K-TOO-LARGE` has three emit sites and `E-RUN-FOLD-UNRESOLVED` has three.**
`grep -rn "E-REPL-FOLD-K-TOO-LARGE" src/` → `validate.py` (one `c.error`) and `replication._fold_k`
(two raises, units and clusters). `grep -rn "E-RUN-FOLD-UNRESOLVED" src/` → `runner._handed_keys`,
`cli`'s fold-with-no-roster guard, and `sweep.build_sweep_document`'s partitions-without-a-fold
guard. The re-scoping's correction C1 is confirmed rather than carried.

**M5. `expand(doc)` is already above everything the hoist touches.** In `_prepare_run` the order at
`3d72910` is `conditions = expand(doc)` … `clusters_of` → `fold_basis` → `resolve_repeats` →
`partition_units` → `fold_members_for` → `_resolved_group_axes` → `_resolved_holdout` →
`_evaluation_roster` → `arm_members`. `H3c-3-SCOPING.md` § 1 records `partition_units` → `expand` →
`_resolved_group_axes`; **that order is stale.** Both inputs the hoist needs — the conditions and
the roster — are in hand before the fold region, so the hoist is a move of two calls and no new
resolution.

**M6. `_check_evaluation_split_cells` refuses every config this capability serves.** Its predicate
is `allocation == "between" or bool(groups)` and it takes no roster. A `groups` + `between` + `fold`
project run through the installed console script exits `1` on `E-REPL-FOLD-CELLS`; the same project
with a `holdout` earns `E-DATA-HOLDOUT-CELLS`. **No config that declares a cell structure beside an
evaluation split validates today**, which is the whole of § 8's disclosure.

**M7. A non-empty `sweep.groups` beside `allocation: within` is itself refused**
(`E-DATA-ALLOCATION-WITHIN-ARMS`), and `allocation: between` with no group axis earns
`E-DATA-ALLOCATION-NO-ARMS` (§ Validation's *Allocation needs arms*) — **both codes grepped in
`validate.py`, not carried from the re-scoping's § 1.1**. **So in a config that is otherwise clean, a cell structure is exactly one thing: a
non-empty `sweep.groups` beside `allocation: between`.** That is the gate Decision 3 uses, and it
is why `_check_evaluation_split_cells`' two-branch message ternary has one branch only a
doubly-refused config ever reads.

**M8. `sweep.yaml`'s `partitions` is read by no command.** `grep -rn "partitions"` over
`report.py`, `diff.py`, `study.py`, `reproduce.py`, `freeze.py` and `lineage.py` finds the key
nowhere: `lineage.read_sweep_plan` projects `conditions`, `order` and `execution_order` only, and
`freeze` reads `conditions` alone. Its readers are three assertions in `tests/test_cli.py` and
`tests/test_sweep.py::test_a_fold_level_records_its_partitions`.

**M9. `allocation.json`'s readers are four, and none is a command surface.** `cli.py` and
`artifacts.py` produce it, `lineage.read_allocation` reads it, `_resumed_allocation` consumes that.
`report.py`, `study.py` and `diff.py` read it at zero sites — H8c's ruling that a bundle never
carries `allocation.json` is what keeps that true.

**M10. The three document sites that claimed unbuilt behaviour in the present tense are all marked
today.** `reference.md` § A fixed holdout split: *"Drawing within each cell is the design that lifts
both refusals, and it is not built."* § Clustered units: *"that draw is not built, so `validate`
refuses the combination outright."* `experimental-designs.md` § Between-subjects factorial: *"A fold
or a holdout drawn within each cell is not built."* **Ruling HH's stated premise is false at
`3d72910`**, and Decision 1 says what survives it.

**M11. `limits.min_units_per_cell` is written by `materialize.py`, typed by `envelope.py`, and read
nowhere.** `grep -rn "min_units_per_cell" src/` returns exactly three hits: the generator, the
envelope type, and one comment in `units.py`. Its three document sites all say **warning** —
§ Validation's *Cells are populated* and *Allocation is coherent* (both *"specified, not built in
this build (warning)"*) and § The one config file's inline comment.

**M12. The `-THIN` warning family is `W-STATS-*` today** — `W-STATS-COLUMN-THIN`,
`-CONTRAST-THIN`, `-CONTRAST-RESAMPLE-THIN`, `-CORRECTED-THIN`, `-REPORTBY-THIN`, `-RESAMPLE-THIN`,
`-STRATUM-THIN` — and the `W-DATA-*` family is `W-DATA-CLUSTER-UNDECLARED`, `-INELIGIBLE`,
`-WEIGHT-UNDECLARED`. Both prefixes have precedent; Decision 3 picks between them and says why.

**M13. `_check_holdout` bounds `frac` against `len(roster)`.** `E-DATA-HOLDOUT-EMPTY` at `validate`
computes `holdout_sizes(len(roster), frac)` and reports when the test side is zero — *the whole
roster*, unstratified and unclustered only. The run-time raise inside `holdout_for` covers the cases
`validate` declines. Under cells both bounds are over the wrong denominator (Decision 10).

**M15. The document greps were re-run NEWLINE-INSENSITIVELY, because these files are hard-wrapped.**
Every count in M10 and § 12 was first taken with `grep -n`, which cannot see a phrase that straddles a
line break. Re-taken by collapsing whitespace over the four documents by name (never over `*.md`,
which no longer means what it used to): `within each cell` → **2**, both inside § Clustered units'
one paragraph; `is not built` → **3** in `reference.md`, **1** in `experimental-designs.md`, **0** in
`README.md` and `design-principles.md`; `E-DATA-HOLDOUT-CELLS` → 3, `E-REPL-FOLD-CELLS` → 4, both
`reference.md`-only; `min_units_per_cell` → 5 in `reference.md`, 1 in `experimental-designs.md`;
*Cells are populated* → **2** and *Allocation is coherent* → **2** (each a § Validation row plus the
§ A fixed holdout split-adjacent prose naming it); *One split, not one cell each* → **2** (its row and
the pointer at *Folds fit inside the cells*). **No count moved and no site was added** — the two
`within each cell` hits and the § A fixed holdout split bullet's `*within*` spelling are all inside
sites § 10 and task 21 already name. Recorded because an undercount here would be a claim in the
wrong direction.

**M14. `spec-defects.md` mentions `H3c-3` at 56 lines**, and 57 headings begin `## OPEN`. The phrase
*"H3c-3's remaining 14"* appears inside the *owner: unassigned* reason of a dozen of them; it goes
false the day this slice merges (task 20).

---

## 1. Decision 1 (Ruling HH) — the slice is built in full; the recommendation to ship the refusal is recorded and overruled, and its stated premise is corrected first

**Question.** Build the capability, or ship the refusal permanently and take only the two items the
slice's non-existence makes worse?

**Answer.** Build it in full — all 23 tasks, one branch, no split.

**Grounds, and the first of them is a correction to the ruling's own premise.** Ruling HH argues
that *"two normative documents describe folds and holdouts inside cells in the present tense."*
**Measured (M10): they do not.** All three sites — two in `reference.md`, one in
`experimental-designs.md` — say *"is not built"* or *"that draw is not built"*, in the marked form
this repo requires. H3d repaired them when it shipped the refusal, and the re-scoping's § 7 says so.
**Repeating a brief's claim about the code without grepping it is the named trap**; the greps are
`grep -n "E-DATA-HOLDOUT-CELLS" docs/reference.md` → 3, `grep -n "E-REPL-FOLD-CELLS"
docs/reference.md` → 4, both over `docs/experimental-designs.md` → 0 with the prose site read by
hand, and `grep -n "within each cell" docs/*.md README.md` → 4, of which three are the
`resample`/`cluster` composition sentence and one is § Clustered units' marked paragraph.

**What survives the correction, and it is enough:**

1. **The documents present the design as the right one and mark it unbuilt; they do not refuse it.**
   § Clustered units states what drawing within each cell *would* buy — *"every fold proportional
   throughout, bounding `k` by the smallest cell's unit count — or its cluster count"* — in the
   conditional. Shipping the refusal permanently means converting three *"not built"* sentences into
   *"core refuses this design"*, adding an entry to `experimental-designs.md` § What core will not do
   for you, and supplying the reason that section's every other entry carries. **The stated
   non-promises are refusals with reasons attached**, and no reason exists here: the design is
   expressible, computable, and named as correct by the document that would have to refuse it. That
   is a larger and worse-argued document change than building the code, and **there is no later
   slice to revisit it.**
2. **`limits.min_units_per_cell` and the two *"specified, not built"* § Validation rows can only be
   closed honestly by this slice's decomposition** (Decision 3, Ruling JJ). Ship the refusal and
   three shipped surfaces stay unread forever.
3. **`E-REPL-FOLD-CELLS` bounds nothing it could bound.** A `groups` design with no evaluation split
   still gets no per-cell check of any kind — the refusal fires on the *pair*, so the thin-cell
   design that declares neither a fold nor a holdout is exactly as silent as before.

**The alternative, recorded in full rather than defaulted past.** The re-scoping's § 10 recommends:
ship the refusal, re-own the `an evaluation split cannot be drawn within a cell` filing as
`unassigned` with the honest reason that no slice follows, and take task 1(d) and task 20 alone. Its
grounds are real and are **not** disputed here: this slice unblocks **zero** of the nine experiments
in [the feasibility analysis](../../feasibility-llm-growth-studies.md) (§ 10 derives that), retires
two refusals **no outside evidence hits** (M6 plus the analysis' own `groups: []`), and its original
written justification — *"two normative documents claim, in the present tense and unmarked, that
core does something it does not do"* — was consumed entirely by the three tasks that merged with
H3d. Against that, this design adds 23 tasks, opens a cross-arm training leak that is already
written (Decision 2), breaks a written safety argument on the resume path (Decision 5), and changes
one shipped artifact's document. **A reader who thinks the trade goes the other way is reading the
same facts, not fewer of them.**

**One ground for building that is deliberately NOT claimed.** The cross-arm training leak in
`runner.execute_plan` is a **cost of building**, not a reason to build. It is unreachable today
because `E-DATA-HOLDOUT-CELLS` refuses every config that could reach it; retiring that refusal is
what makes it live. Listing it as a justification would be exactly the inversion this repo's
§ Misreadings section is about.

**Cost if wrong.** The project ships a capability nothing has asked for, in the slice with the least
external justification of any in the spine, and every defect it introduces ships with it because no
slice follows. The mitigations are the whole of § 7 (the bit-stability oracle), § 8 (the
disclosure) and § 11 (the mutations); if any of the three cannot be satisfied, that is the signal to
stop, and the alternative above is the branch to take.

---

## 2. Decision 2 (Ruling II) — the arm-narrowed train side and the deletion of the assert are ONE task; no commit on the branch has the leak open

**Question.** In what order do "narrow `holdout_train` per arm" and "retire `E-DATA-HOLDOUT-CELLS`"
land, and what enforces it?

**Answer.** Three constraints, in force order:

1. **Task 15 narrows the train side and deletes `assert holdout_train is None or arm_members is
   None` in the same commit.** Not the same batch — the same commit. The narrowing without the
   deletion is dead code; the deletion without the narrowing is the leak.
2. **Task 16 retires `E-DATA-HOLDOUT-CELLS` and it is sequenced after task 15**, in the same batch
   (D), with the dependency written into both task sections.
3. **No commit exists in which the assert is gone and `holdout_train` still comes from `roster`.**
   That is the enforceable statement; *"same batch"* is not, because a batch is several commits.

**Grounds, measured.** `runner.execute_plan` narrows to the arm first —
`scoped_units = UnitList([u for u in units if u.key in arm_keys])` — and then composes
`step_units = UnitList(list(scoped_units), train=holdout_train)`. `holdout_train` is built in
`cli._execute_prepared` as `UnitList([u for u in roster if u.key in set(holdout_plan.train)])`,
**from `roster`, never from the arm**. The fold branch fifty lines below gets it right:
`train=UnitList([u for u in scoped_units if u.key not in handed])`. **The sibling that already got
it right is in the same function**, and task 15's code copies its narrowing rather than inventing
one. The assert's own comment names the refusal it rests on:
*"`E-DATA-HOLDOUT-CELLS` (task 8) refuses a holdout beside the group axis `arm_members` comes
from."*

**The mechanism, which the ruling asks for and which the ordering alone does not give.** With
`E-DATA-HOLDOUT-CELLS` still live, **no end-to-end `run` can reach the composition** — `command_run`
validates first. So the fixture that proves `io.units.train ⊆ the arm` has to be a **direct
`execute_plan` call**, and that call trips the very assert being deleted. **Therefore the fixture
lands inside task 15**, in the same commit as the narrowing and the deletion; it cannot be written
before and it must not be written after. Task 22's end-to-end `groups × holdout` run becomes
constructible only once task 16 has retired the refusal, and it is the confirmation, not the proof.

**Alternatives rejected.** *Retire the refusal first and narrow in a follow-up task* — this is the
shape the re-scoping's § 9 has (task 11 then task 12) and it is rejected: every commit between them
carries a model trained on units it is then evaluated against, across arms, with no diagnostic.
*Keep the assert and narrow `arm_members` out of the call* — the assert is what makes the leak
unreachable; keeping it means the capability is not built. *Leave `holdout_train` roster-wide and
document it* — a documented leak is the silently-wrong class this refusal was minted to avoid.

**Cost if wrong.** A model trained on units it is then evaluated against, across arms, with no
diagnostic — the worst class of defect this project could ship, and the last slice is the last
chance not to ship it.

---

## 3. Decision 3 (Ruling JJ) — `limits.min_units_per_cell` is a WARNING, `W-DATA-CELL-THIN`, over this slice's own cell decomposition, gated on a cell structure existing

**Question.** Is the thin-cell gap a refusal or a warning, and what closes it?

**Answer.** A **warning**, code `W-DATA-CELL-THIN`, emitted at `validate` from one site, once, for
the smallest cell below `limits.min_units_per_cell`, over `units.cells_of`'s decomposition — the
same one the fold bound and the holdout loop read. **The code follows the documents rather than the
documents following the code.**

**Grounds, measured.** Three document sites say *warning*, in those words (M11): § Validation's
*Cells are populated* (*"`sex × arm` over 40 units gives cells of 10; below
`limits.min_units_per_cell` — specified, not built in this build (warning)"*), § Validation's
*Allocation is coherent* (same marking), and § The one config file's inline comment (*"a smaller
design cell under `allocation: between` should warn"*). § Weighted samples' surrounding prose adds
the reason: *"a two-arm design where one arm resolves to exactly two units passes `validate` clean
and reports a real `basis: units` interval from those two observations — small enough that no one
should trust it, and nothing warns."* **A thin cell is not a declaration error; it is a design whose
answer is weak.** `E-DATA-ASSIGN-LEVELS` already refuses the arm no unit resolves to, which is where
the hard line sits.

**Why this slice owns it, rather than it being adjacent.** Once folds are drawn within cells,
`_fold_k`'s per-cell bound **refuses** exactly the thin cells this parameter was specified to **warn**
about — a 2-unit arm cannot carry `k: 5` and earns `E-REPL-FOLD-K-TOO-LARGE`. The capability makes
half the gap loud and leaves the other half exactly as quiet, and **there is no later slice** to
notice the asymmetry. The decomposition the warning needs is `units.cells_of`, which task 2 builds
anyway; without this slice the warning would need to build it alone.

**The gate, which neither § Validation row states in its own cell.** The check fires **only when a
cell structure exists** — a non-empty `sweep.groups` — and never for a design with no group axis.
Both rows' examples carry the gating (`sex × arm`, `allocation: between` over 2 arms) while neither
row's own wording does, which is precisely the *"taking a § Validation row's own wording as its whole
scope"* misreading. **Without the gate the warning fires on every generated project with fewer than
20 units**, because `materialize.py` writes `min_units_per_cell: 20` into every config `init`
produces — including the scaffold `demo` builds and every fixture in the suite. M7 is what makes the
gate exact rather than approximate: in an otherwise-clean config, a cell structure is a non-empty
`sweep.groups` beside `allocation: between`, so gating on the resolved axes is gating on both.

**The name.** `W-DATA-CELL-THIN`: `W-DATA-*` because the declaration it answers for is
`data.units.allocation` and `limits.min_units_per_cell`, not a statistics block — the `-THIN` suffix
joins the family whose documentation question is already filed and **still unowned**, and this
warning joins that filing rather than settling it (§ 10).

**Two § Validation rows, one code.** *Cells are populated* and *Allocation is coherent* both
describe this check — one from the crossed-axes side, one from the two-arm side — and under M7 they
are the same structure seen twice. Both rows lose *"specified, not built in this build"* and both
name `W-DATA-CELL-THIN`. **Checked rather than assumed:** § Validation rows are checks, not codes,
and the one-row-per-code rule governs § Errors and § Warnings; *Fold strata survive clustering*,
*Allocation strata survive clustering*, *Resample strata survive clustering* and *Holdout strata
survive clustering* are four § Validation rows over one shared derivation with four codes, and
*Folds fit inside the cells* is a § Validation row pointing at another § Validation row. **No
precedent was found for two § Validation rows naming one code**, so this design says so explicitly
and gives both rows the code rather than leaving a reader to infer it; § Warnings core reports gains
**one** row, which is where the one-row-per-code rule actually bites.

**Alternatives rejected.** *A refusal* — contradicts three document sites and would need all three
rewritten plus an argument against `design-principles.md`; a two-unit arm is a weak design, not an
invalid declaration. *Decline it as "a limits deliverable"* — the re-scoping's § 8 kills that: the
spine's order is exhausted and **there is no limits deliverable**; the filing's own owner line,
*"whichever slice builds it"*, is the form `spec-defects.md` rejects by name. *Fold it into
`_fold_k`'s bound* — that answers only for designs declaring a fold, which is the half already
loud.

**Cost if wrong.** If the gate is wrong in the permissive direction, a thin cell ships silent — the
status quo. If it is wrong in the other, every small generated project warns about a parameter it
never declared a cell for, and a warning readers learn to skip is worse than none. The can-fail
control in § 9 exists for exactly that direction.

---

## 4. Decision 4 (Ruling LL) — `fold_basis` keeps ONE question; a second function answers the cell question; the `min_clusters` site keeps the roster-wide call and loses its "cheap follow-up" sentence

**Question.** `fold_basis` has three call sites. Under cells, does it gain a `cells` argument?

**Answer.** **No. It is not touched at all.** A new function, `units.cell_fold_basis(roster,
cluster_by, cells)`, answers the cell question by calling `fold_basis` once per cell and returning
the minimum — one number, not two, and not a mapping. The three call sites split **two and one**:

| Call site | Question it asks | What it calls after this slice |
|---|---|---|
| `validate_config`'s `basis`, feeding `_check_replication` | *How many indivisible things can a fold be drawn from, in the cell that has fewest?* | `cell_fold_basis` when cells resolve, `fold_basis` otherwise |
| `validate_config`'s `basis`, feeding `_check_sweep`'s `k: all` budget | the same question, and it must be the same number | the same one number — it is the same local |
| `_check_resample`'s `limits.min_clusters` denominator | *How many independent draws does a percentile interval rest on?* | **`fold_basis`, unchanged, over the whole roster or the holdout's test side** |
| `_prepare_run`'s | the run's own fold basis | `cell_fold_basis` when cells resolve, `fold_basis` otherwise |

**Grounds.** The third site is not the fold's basis at all — its own comment says the two are
*"deliberately not the same derivation reused, only the same function"* — and its question does not
decompose by cell: `statistics.resample` draws over the **per-unit table**, which holds every
condition's units across every cell, so its independent-draw count is over the whole test roster. If
`fold_basis` gained a `cells` argument, one of two things follows and both are bad: either the
`min_clusters` site passes `cells=None` — a helper that ignores an argument, which hides what its
callers stopped testing — or it passes the cells and warns against a denominator no interval used.
**A function whose name fits one of its three callers is a proxy waiting to be believed**, and that
is the whole of Ruling LL.

**`k: all` is the half the re-scoping's task 5 does not name.** `{kind: fold, k: all}` resolves
against the basis (`replication._fold_k`'s `k = fold_basis` branch) and `_check_sweep` sizes the
execution budget from the same number. If `k: all` resolved to the whole roster's basis while
`_fold_k` bounded against the smallest cell's, a `k: all` design would resolve to a `k` the bound
then refuses — the exact *"checked against one number while the partition is drawn over another"*
drift `fold_basis`' docstring exists to prevent. **They are one local and stay one local.**

**The sentence that is deleted rather than rewritten.** The `min_clusters` site's comment ends
*"Not threaded through `basis` in this slice; doing so is a cheap follow-up, not a correctness gap
today."* After this slice, threading it through would be a **defect**, not a follow-up. The sentence
is **deleted**, and the paragraph above it — which already argues the two are different rosters —
gains one clause naming cells as the third reason. **Prefer deleting a claim to rewriting it.**

**Alternatives rejected.** *Give `fold_basis` a `cells=None` default* — the helper-that-ignores-an-
argument shape, and every existing caller keeps passing nothing while the tests that covered them
stop distinguishing anything. *Return a per-cell mapping and let each caller pick* — explicitly
forbidden by `fold_basis`' own docstring and by `H3c-3-SCOPING.md` § 5. *Fold the minimum into
`_fold_k`* — `_fold_k` sees a declaration and a count and never a roster, by design.

**Cost if wrong.** If the `min_clusters` site should have taken cells, `W-STATS-RESAMPLE-CLUSTERS`
warns against a wider denominator than some cell's — wrong in the direction of not firing, which is
the direction H3d already found it wrong in and did not close. Filed in § 10 with the no-later-slice
sentence, because settling it needs an argument about what a clustered percentile interval rests on
under a between-subjects design, and that argument is not this slice's.

---

## 5. Decision 5 (Ruling KK) — `_resumed_allocation` re-derives the fold partitions from the overridden decomposition, through the same single producer; the safety argument is replaced only after it has been made to fail

**Question.** `_resumed_allocation` declines to override fold partitions because *"`partition_units`
is a pure function of the roster and the design digest."* What happens to that under cells?

**Answer.** It goes false, and the fix is a re-derivation rather than a patched sentence.
`_resumed_allocation` calls the **same** per-cell partition producer `_prepare_run` calls
(`units.partition_within_cells`, task 8's extraction), on the **overridden** axes, and replaces
`Prepared.partitions` and `Prepared.fold_members`. Unconditionally — there is no `if group_axes` gate
— because with no axes the producer takes the one-cell path and returns the identical partition, and
a branch is one more thing to get wrong than a proof.

**Grounds, and the mutation comes first.** Under cells a partition is a function of the roster, the
digest **and the cell decomposition**, and the cell decomposition on a resume is exactly what this
function overrides, one call after `_prepare_run` drew it fresh. **A safety argument in a comment is
a claim, and this one is made to fail before the replacement is written** (§ 11, mutation MU-9): a
two-arm `method: random` axis, a `{kind: fold, k: 3}` level, and a second attempt whose roster
resolves the same keys in a different order. **Measured (M2)**: the reordered roster gives
`units_hash` `ee083cab…` against `f3ba4914…`, `assign_seed_for` `1647976561` against `2988051695`,
and a different realized membership — while `_resumed_allocation`'s guards, which compare **sets**
of levels and **sets** of keys in both directions, pass. Without the re-derivation the resumed run
evaluates folds drawn from the fresh cells while executing against the recorded ones.

**H9b could not build that fixture and said so**; this slice can, and the reason it can is that
folds and a group axis can now coexist. `E-DATA-HOLDOUT-FOLD` still refuses a holdout beside a fold,
so the interaction is fold-with-axes only, and the holdout override needs no partition change.

**The replacement text is a re-derivation, not an edit.** The docstring paragraph headed *"Fold
partitions are deliberately not touched here"* is **deleted** and replaced by one stating what is
now true: the partition is a function of the roster, the digest and the cell decomposition; the
decomposition is overridden here; therefore the partition is re-derived here, through the single
producer, and `partition_units` itself is still not called from this function.

**Alternatives rejected.** *Move the allocation override inside `_prepare_run`, above the partition*
— crosses the H9a seam, changes `Prepared`'s construction order for every command, and H9a's Ruling
S deliberately left the region alone. *Re-derive the partition by hand here* — makes this function a
second producer of fold membership, the fault its own docstring exists to prevent a third instance
of. *Gate the re-derivation on `group_axes` being non-empty* — a branch whose no-axis arm is
provably a no-op is worse than no branch, and the no-op is the pin (§ 7).

**Cost if wrong.** A resumed `groups × fold` run under a drawn axis executes against one set of
folds and reports against another, silently, with `sweep.yaml` recording the second. Under
`by_attribute` the two coincide, which is the *correct-and-buggy-readings-coincide* trap pointed the
other way — so the fixture must use `random`, and § 9 says so.

---

## 6. Decisions 6 through 13 — the constructions

### Decision 6 — `units.cells_of(axes)` derives cells from the `ArmPlan`s and returns membership, never a roster

`cells_of(axes: Mapping[str, ArmPlan]) -> dict[tuple[tuple[str, str], ...], frozenset[str]]`: the
cartesian product of every axis's declared levels, in **declaration order**, each key a tuple of
`(axis, level)` pairs and each value the intersection of those arms' keys. Empty cells are **kept**,
not skipped. `{}` axes give one cell whose key is `()` and whose value is every roster key — which
is what makes the no-axis path fall out rather than be branched around.

**Grounds.** `arm_members` is keyed by **condition index** and is the wrong shape: under
`groups × grid` several conditions share one cell, and under a group axis alone the mapping omits
every condition selecting no axis. Deriving cells from `arm_members` would draw one partition per
condition and break *"Partitions are computed once per run, not once per condition"* for real.
`build_allocation_document` **takes no roster on purpose** — *"with nothing to read membership from,
it cannot become a second producer of it"* — and this function takes none either, for the same
reason: it returns key sets, and the caller composes sub-rosters from its own roster in roster
order. Cells partition the roster exactly (`arms_of` enforces every unit in exactly one arm per
axis), which is what makes the index-wise merge in Decision 7 total.

**Cost if wrong.** A cell decomposition that is not a partition makes some unit appear in two folds
or none; the structural fixture in § 9 asserts coverage and disjointness against the roster directly.

### Decision 7 — the per-cell partition passes the BARE digest and merges index-wise; `partition_units` is untouched

`units.partition_within_cells(roster, k, digest, cells, clusters=, strata=)` loops
`partition_units(sub_roster, k, digest, clusters=…, strata=…)` per **non-empty** cell in `cells_of`'s
key order, and merges index-wise: partition *i* is the concatenation, in cell order, of each cell's
partition *i*. Each sub-roster is built from the roster in **roster order**, and each cell's
`clusters`/`strata` maps are the whole-run maps restricted to that cell's keys.

**Grounds.** `partition_units` builds its own `random.Random(_seed_from(digest))` per call, so
per-cell calls are independent of cell **order** and of how many cells there are — strictly better
than the per-stratum branch, whose threaded RNG makes each stratum's draw depend on how many
preceded it. A per-cell digest (`digest|arm=control`) is the obvious implementation and is rejected:
it is safe only if the no-groups path never touches it, and the bare digest needs no such guard. A
one-cell design then reduces to the current single call **byte-identically**, which is the new
regression pin (§ 7) rather than an argument.

Empty cells are skipped **inside this loop only** — `partition_units` over an empty roster produces
`k` empty lists, which contributes nothing and is not the fault being papered over: the fault is a
cell too thin for `k`, and Decision 9's bound refuses that at `validate` before this loop runs. The
loop's skip is stated in its docstring as *not* a bound.

**Cost if wrong.** A merge that is not index-wise makes fold *i* mean different things in different
cells, and `fold_members` — which is flat — stops being a partition of the roster.

### Decision 8 — `validate` draws for real to see a cell, following H3d's precedent, and swallows every fault

`validate_config` resolves the cells through a new `_resolved_cells(doc, units_decl, roster,
usable_cluster)`, which realizes each `sweep.groups` axis through `units.assignment_for` at the
**real** `design_digest(doc)` and calls `cells_of`, inside a `try` swallowing `ContractError`,
`NotImplementedError`, `KeyError`, `TypeError` and `ValueError`. On any fault it returns `None` and
every cell-aware check simply does not run.

**Grounds.** `H3c-3-SCOPING.md` left this open, hesitating because `_check_assign`'s existing draw is
gated to the unstratified, unclustered case with the placeholder digest `"validate"` — sound only
because sizes are digest-independent there, and a cell's **cluster count** is exactly the
seed-dependent quantity that gating excludes. **H3d already made the ruling in the direction it
hesitated over**: `validate._holdout_test_partition` performs a real draw at the real digest inside
a swallowing `try`, on the stated ground that a second answer computed there *"would be a check
aimed at a partition the run does not use."* The same argument holds verbatim here, and taking the
other branch would give `validate` and `run` two different cell decompositions of one declaration.

**Cost if wrong.** `validate` becomes measurably slower on a large roster with a drawn axis — it now
performs the allocation draw it previously skipped. Bounded: one draw per axis, the same work
`command_run` already does once.

### Decision 9 — `_fold_k` gains a cell clause at all THREE `E-REPL-FOLD-K-TOO-LARGE` emit sites, and the § Errors row is rewritten to cover them

The bound becomes *"`k` against the smallest cell's basis"* whenever cells resolve. `_fold_k`'s two
raises gain the cell in their message — the cell's `(axis, level)` label and, under `cluster_by`,
its cluster count — and `validate.py`'s `c.error` site gains the same. **All three, or an argument in
writing for the one that is not reached.**

**Grounds.** M4: the code has three sites where the original scoping counted two.
**§ Errors carries one row per code covering every emit site**, checked against its table's own scope
sentence — § Errors `validate` reports covers *"the codes a command reports"*, including a code
raised at load and reported here. The existing row reads *"the resolved unit count, or the cluster
count when `data.units.cluster_by` is declared"*; it gains the cell clause and stays one row. **A row
widened then undercounted is a whole-branch Major in three consecutive slices**, so task 7 states
the site count in its own report and the reviewer re-runs the grep.

**One question task 7 must answer rather than leave asymmetric.** `E-DATA-HOLDOUT-EMPTY` has rows in
**both** § Errors tables (Decision 10) while `E-REPL-FOLD-K-TOO-LARGE` has one, in the validate
table, though `replication._fold_k` raises it twice. Decision 8's swallowing `try` is what could
change that: if `validate`'s cell draw returns `None` while `_prepare_run`'s succeeds, a config
validates clean and then meets the raise — and § Errors core raises would owe the code a row,
**checked against THAT table's scope sentence, not the validate one**. Answer it from the code: both
draws call the same function at the same `design_digest(doc)` over the same roster, so a fault in one
is a fault in the other — say that, or file the path.

**Cost if wrong.** A message that names no cell sends a reader to the whole roster's count when the
fault is one arm's, which is the remedy pointing at the wrong declaration; a clause reached at two of
three sites means the same config gets two different explanations depending on whether `k` was
`all`.

### Decision 10 — `E-DATA-HOLDOUT-EMPTY` is bounded by the smallest cell at both its `validate` and its run-time site, and its two rows are re-derived

`_check_holdout`'s `E-DATA-HOLDOUT-EMPTY` computes `holdout_sizes(len(roster), frac)` today (M13).
Under cells it computes it over the **smallest non-empty cell**, and the message names that cell. The
run-time raise inside `holdout_for` gains the cell in its message through the caller: `_resolved_holdout`
catches the per-cell `ContractError` and re-raises with the cell named, rather than `holdout_for`
gaining a cell parameter it has no other use for.

**Grounds.** M3: `holdout_for` over a 2-unit cell at `frac: 0.2` raises, and over an empty cell
raises with *"leaves the train side empty"* — a message that names 0 resolved units and no cell,
which sends a reader to the roster when the fault is a crossed combination nothing carries. The
`frac` that clears the whole roster does not clear every cell, and `holdout_sizes`' own docstring
already rules that a zero test side *"is the caller's to refuse"*. **This is a widening of an
existing code, not a new one**: the remedy is unchanged (widen `frac`, or resolve a larger roster),
and a second code would give one remedy two names. Both its rows move — § Errors `validate` reports
and § Errors core raises — and each is checked against **its own** scope sentence.

**Cost if wrong.** In the permissive direction, a thin cell's holdout raises mid-run, after
executions are already paid for, with a message naming the roster rather than the cell — the class
`E-CODE-EMPTY`'s siting exists to avoid. In the strict direction it is worse: a bound over the wrong
denominator refuses a `frac` that is fine, and **a user cannot work around a refusal.** The
can-fail control in § 9 (the 10/10 split validating clean) is aimed at exactly that direction.

### Decision 11 — `allocation.json`'s `holdout` stays FLAT and gains one key; `sweep.yaml`'s `partitions` entries are unchanged and the document gains one key; neither round-trip pin moves

- `allocation.json`'s `holdout` block gains `within: [<axis names>]`, **present only when the split
  was drawn within cells**, beside the existing `seed` and `strata`. `train` and `test` stay flat
  lists over the whole roster.
- `sweep.yaml` gains a top-level `partitions_within: [<axis names>]`, **present only when the
  partitions were drawn within cells**. Every `partitions` entry keeps `fold`, `test` and `train`
  exactly as today.

**Grounds, and the arithmetic is the finding.** The re-scoping's § 6.3 and `H3c-3-SCOPING.md`'s
task 12 both call composing `train` *"within the cell"* a correctness change to the record.
**Measured: at the flat level it is not a change at all.** Cells partition the roster and the merge
is index-wise, so `partitions` still partitions the roster, and *"every other partition concatenated
in fold order"* is `roster \ partition_i` either way — union over cells of `cell \ partition_i` is
the same set. The real defect is different and sharper: **under cells the flat `train` describes a
side no execution ever sees**, because every condition is arm-narrowed first, so what a step gets is
`cell ∩ (roster \ partition_i)`. A key whose meaning silently changes with the design's shape is the
silently-wrong class — so the record **discloses** rather than re-composes. The same holds for the
holdout: `holdout_train` narrowed per arm (Decision 2) is `cell ∩ train`, recoverable by crossing
against `arms` in the same file.

**The disclosure key rather than a nested shape.** A per-cell nesting would move three shipped
assertions and `test_a_fold_level_records_its_partitions`, would change `sweep.yaml` for a design
that has no cells if done carelessly, and buys a reader nothing they cannot get by crossing two
lists that are already in the same two files. `weighted_by` and `n_paired_clusters` are the
precedent: **a fact travels beside the number whose meaning it qualifies.** Omitted rather than
written `null` when it describes nothing, which is `build_allocation_document`'s own stated rule for
`seed` and `strata` and `manifest/input.json`'s for absent hashes.

**Both round-trip pins were checked, not assumed.** `_resumed_allocation`'s pin asserts *"the
rebuilt document equals the recorded one"*; `within` is derived by `build_allocation_document` from
its `group_axes` argument, which `_resumed_allocation` overrides consistently, so the rebuild
produces the same `within` and **the pin does not move**. `_resumed_allocation` reads the holdout by
key (`train`, `test`, `seed`, `strata`) and ignores extras, so the new key needs no reader change.
**Task 17 is nevertheless named as the pin's sole authorized editor** with its post-edit state
specified in advance — *unchanged* — so that if the check is wrong the move is made once, by a named
task, rather than discovered (§ 7, arm C).

**Cost if wrong.** A reader of `sweep.yaml` takes `train` at face value under a `groups` design and
believes a step saw units from another arm. The disclosure key plus the § The other files a run
writes sentence are what stand between them and that; if a reviewer judges them insufficient, the
nested shape is the fallback and it costs task 11 plus three pin moves.

### Decision 12 — the hoist moves exactly two calls inside `_prepare_run`, and `Prepared`'s field set does not change

`_resolved_group_axes` and `arm_members` move **above** `clusters_of`'s successors — specifically
above `fold_basis`/`cell_fold_basis`, `resolve_repeats` and the partition call — inside
`_prepare_run`. `_resolved_holdout` needs no hoist: it already sits below `_resolved_group_axes`.
`Prepared` gains **one** field, `cells`, and `_execute_prepared`'s unpack gains one line; the other
thirty-six are untouched.

**Grounds.** Ruling S discharged: *"They move as-is, in place, in their current order… H3c-3's
remaining 14 owns the phase hoist of exactly those two calls."* M5 measured the current order and
found `expand(doc)` already above the whole region, so both inputs are in hand and the hoist
resolves nothing new. *"Realized once per run"* stays literally true and is asserted rather than
assumed.

**Why `cells` is a `Prepared` field rather than recomputed.** `_resumed_allocation` (Decision 5) and
`_execute_prepared` both need it, and a second derivation of a decomposition is a second producer.

**Cost if wrong.** A hoist that resolves an axis twice draws a *second* allocation under `random` or
`blocked` — the whole reason `_resolved_group_axes` documents itself as realized once per run — and
the run would then narrow conditions by one draw while `allocation.json` records another. MU-16's
counting patch is what stands between this design and that, and it is a count rather than a
membership because a count cannot be satisfied by a coincidence.

### Decision 13 — a cluster that spans two cells is legal today, breaks an assumption this slice does not build, and is FILED rather than refused — and there is no later slice

Under `method: by_attribute` a `cluster_by` cluster may hold units in two different arms (M1's own
fixture does: `S2` is split 1/2 across `control`/`treatment`). Under `random` it cannot — the draw
allocates whole clusters. **This slice does not refuse the `by_attribute` case.**

**Grounds.** Per-cell folds keep clusters whole *within* a cell, which is all a fold's leak argument
needs: a condition never trains on one unit of a cluster and tests on another, because everything it
sees is inside its own cell. What a spanning cluster does break is the **independence between
sides** that H4c's `welch_t_over_units_clustered` and `unpaired_percentile_over_units_clustered`
assume — each side contributes `G_s − 1` to a Welch-Satterthwaite df, and a cluster on both sides is
counted twice. That is a statement about a contrast estimator, not about a partition, and refusing
it here would be this slice minting a refusal for a construction it does not touch, on an argument
it has not made. **Filed in `spec-defects.md` (task 20) with its owner stated as `unassigned` and
the reason stated as a fact: no slice follows this one.** The filing names the two estimators, names
`by_attribute` as the only reachable method, and names the check that would close it (a
constant-cluster-within-arm rule, `stratum_varies_within_cluster`'s shape one declaration over).

**Cost if wrong.** An unpaired clustered contrast over a `by_attribute` `between` design with a
spanning cluster reports a df and an interval that are too narrow, with no diagnostic — and it ships
that way. This is the sharpest thing this design declines, and it is declined because building it
means minting a refusal in the statistics family in a slice about partitions, in the last slice,
with no reviewer downstream to argue against it.

---

## 7. The bit-stability oracle: what may move and what may not

**May not move — this is the pin the whole slice rests on.**

| Property | Where it is pinned |
|---|---|
| A design with **no group axis** calls `partition_units` **exactly once**, over the whole roster, with the **bare** digest, producing byte-identical output | the existing oracle plus pin arm D (new) |
| `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` — the full 5×10 fold contents at `_roster(50)`, `k=5`, digest `"d"` | `tests/test_units.py`, unchanged |
| `partition_units`' signature and body; `_assign_whole_clusters`; `_assign_whole_clusters_by_ratio`; `_seed_from` | pin arm A |
| `fold_basis`' signature, body and return type | Decision 4 |
| The clustered, stratified and structural partition contracts (cover, disjoint, sizes within one, no cluster split) | `tests/test_units.py`, unchanged |
| A no-cell `sweep.yaml` `partitions` block — three assertions in `tests/test_cli.py` plus `tests/test_sweep.py::test_a_fold_level_records_its_partitions`, `train` present | pin arm B |
| `_resumed_allocation`'s round-trip pin: the rebuilt `allocation.json` equals the recorded one | pin arm C |
| `arm_members`' signature and its no-roster property; `build_allocation_document`'s no-roster property | Decision 6 |

**May move.** Only what a design **with** a group axis sees: the number of `partition_units` calls,
`fold_basis`' *caller's* answer (not `fold_basis` itself), the presence of `partitions_within` and
`holdout.within`, and `holdout_train`'s membership.

**The trade this slice must not make**, stated as `_assign_whole_clusters_by_ratio`'s docstring
already states it: **a fold regression bought for an arm feature.**

### The guard pin, captured before anything moves

Task 1 captures it, **first, before any other task runs**. Five arms; the sole authorized editor and
the post-edit state are named now, in advance, per H8a's rule.

| Arm | What it pins | Authorized editor | Post-edit state |
|---|---|---|---|
| **A** | `partition_units(_roster(50), 5, "d")` byte-identical, and the clustered/stratified draws at their pinned seeds | **NONE.** No task in this slice may edit arm A | unchanged, byte for byte |
| **B** | A no-group-axis run's `sweep.yaml`: `partitions` entries carry exactly `fold`, `test`, `train`; the document carries **no** `partitions_within` key | **NONE** | unchanged |
| **C** | `_resumed_allocation`'s round-trip: rebuilt `allocation.json` equals the recorded one | **task 17, and only task 17** | **unchanged** — Decision 11 derives that `within` rebuilds identically. If task 17 finds otherwise it edits this arm **once**, appends the recorded document's `holdout.within` to the expected value, reorders nothing, and says so in its report |
| **D** | **New.** A no-group-axis `_prepare_run` makes exactly **one** `partition_units` call, with the **bare** digest — counted by patching `units.partition_units` with a counting wrapper at the name `cli` calls | **NONE**, and it is written in task 1 against the pre-hoist code so it survives the hoist unedited | unchanged |
| **E** | **New.** A small (6-unit) generated config with no `sweep.groups` reports a finding set with **no** `W-DATA-CELL-THIN` — captured as the exact current finding set, so the warning cannot arrive by widening | **NONE** | unchanged |

Arm E is the can-fail control for Decision 3's gate and it is captured **before** the warning
exists, which is what makes it a pin rather than a restatement of the code.

---

## 8. Is this additive? — the disclosure

**No, and the framing that says which part is non-additive is not the obvious one.**

**What changes for a config that validates clean today: exactly one thing, and it is the warning.**
`W-DATA-CELL-THIN` (Decision 3) fires on designs that pass `validate` with zero findings at
`3d72910` — a two-arm `between` design over 12 units with `min_units_per_cell: 20` and no evaluation
split declared. That is new output on a shipped command for an unchanged config. It never changes an
exit code (§ Warnings core reports: *"a warning never changes an exit code"*), so no `validate` that
exits 0 begins exiting 1.

**What does NOT change, measured rather than assumed.** Retiring `E-DATA-HOLDOUT-CELLS` and
`E-REPL-FOLD-CELLS` changes the behaviour of **zero previously-valid configs**, because
`_check_evaluation_split_cells` errors on **every** config that declares a cell structure beside
either split (M6). No run in existence has roster-wide folds under cells; there is no record on disk
whose folds this slice reinterprets. **The re-scoping's framing — "it changes what a `groups`
design's folds and holdout contain" — is true of a design that cannot be run today.** Stating it the
other way would be a disclosure that is wrong, which H9a's gate found is worse than none.

**What changes for a config that is refused today:** it validates, and then runs with per-cell folds
or a per-cell holdout, an arm-narrowed `io.units.train`, a `partitions_within` key in `sweep.yaml`
and a `holdout.within` key in `allocation.json`.

**What moves in a record for an unchanged design: nothing.** `sweep.yaml`'s entries, `allocation.json`'s
four keys, `run.yaml`, `executions.jsonl`, every hash and every exit code are unchanged for a design
with no group axis — arms A, B and D of the guard pin are what say so, and they are captured before
anything moves.

**Three behaviour changes on shipped commands, enumerated so none is discovered:**

1. `validate` gains `W-DATA-CELL-THIN` (above).
2. `validate` performs an **allocation draw** it did not perform before, for a config with a
   `method: random` or `blocked` group axis (Decision 8). No output changes from it on its own; it is
   named because it is work `validate` did not do.
3. `resume` re-derives fold partitions where it previously carried `_prepare_run`'s (Decision 5). For
   a design with no group axis the re-derivation is provably the same partition, and pin arm D plus
   § 11's MU-10 are what prove it rather than assert it.

---

## 9. Fixtures as claims — every literal, and how it was computed

**F1 — the empty-fold-per-cell table.** The claim: a roster-wide fold beside a cell structure leaves
a cell with folds holding none of its units, and a per-cell draw does not. Built as M1, **computed
at `3d72910`, not read from either scoping**: `[7, 3, 3, 1, 1]` whole roster with `clusters=`;
`[7, 1, 0, 0, 0]` in the `control` cell; `[3, 2, 1, 1, 0]` in `treatment`. The whole-roster row is
the **can-fail control** — same fixture, same `k`, no empty fold — and without it the table shows
only that small rosters make small folds.

**The fixture's own disclosure, because a fixture is a claim too.** "First 8 units are `control`"
puts cluster `S2` on both sides of the arm boundary, which is what makes the cell cluster counts 2
and 4 rather than 2 and 3. `H3c-3-SCOPING.md` reports `[3, 3, 1, 0, 0]` from the same prose because
its mapping put 3 clusters in `treatment`; **neither table's prose determines its own
cluster-to-arm mapping**, and picking a winner without saying so is how two tables carrying the same
description and different numbers come to read as one. This design states the mapping explicitly:
`S1`→units 0–6, `S2`→7–9, `S3`→10–12, `S4`→13, `S5`→14, `arm = control` for 0–7. **And the spanning
cluster is itself the subject of Decision 13**, so the fixture is used with its property named
rather than in spite of it.

**F2 — the per-cell fold fixture for the build.** A **second** roster in which clusters nest inside
arms (no spanning cluster), so that the per-cell draw's correctness is not entangled with Decision
13's open question: 16 units, `control` = clusters `A`×5, `B`×3; `treatment` = `C`×4, `D`×3, `E`×1.
Cell cluster counts **2** and **3**; `cell_fold_basis` clustered = **2**, unclustered = **8**;
whole-roster `fold_basis` clustered = **5**, unclustered = **16**. **The discriminating literal:
`{kind: fold, k: 3}` clears the whole-roster bound (5 ≥ 3) and is refused by the per-cell bound
(2 < 3).** Two elements only ever distinguish two answers, so the two cells are given **different**
cluster counts — a fixture with 2 and 2 could not tell "minimum over cells" from "the first cell's
count".

**F3 — the thin-cell warning fixture and its two controls.** 12 units, two arms of 6,
`min_units_per_cell: 20`, no fold, no holdout → exactly one `W-DATA-CELL-THIN` naming the smaller
cell. **Control 1** (must not warn): the same 12 units, `min_units_per_cell: 5`. **Control 2** (the
gate, and the one that catches the failure mode that matters): the same 12 units with **no**
`sweep.groups` and `min_units_per_cell: 20` → no warning, because no cell structure exists. Control 2
is guard-pin arm E, captured before the code.

**F4 — the cross-arm training leak fixture (task 15).** A direct `execute_plan` call with
`arm_members` naming a 4-unit arm A and a 4-unit arm B, and a `holdout_train` built per arm. The
assertion: the `UnitList` a condition-scoped step receives has `set(io.units.train) ⊆ arm A's keys`,
and — the half that can fail on a fix that narrows the wrong side — `set(io.units.train)` is
**non-empty**. A subset assertion alone passes on an empty train side.

**F5 — the resume fixture (task 17, Ruling KK).** A `Prepared` whose `group_axes` were drawn from a
roster in **reverse** resolution order, and an `allocation.json` recorded from the forward order.
The literals are M2's: `assign_seed_for` `2988051695` forward and `1647976561` reversed, memberships
`c: [u01, u04, u05]` and `c: [u02, u04, u05]`. The assertion: after `_resumed_allocation`, the fold
partitions are the ones the **recorded** decomposition yields, not the fresh one — asserted by
membership, not by a count, because both decompositions give the same sizes.

**F6 — the per-cell holdout fixture (task 13), and the rule it establishes.** 20 units, two arms of
10, `frac: 0.2`. **A per-arm COUNT assertion cannot discriminate here, and this was checked rather
than assumed.** The pre-slice draw is one shuffle of the whole roster and two slices — a uniform
4-subset of 20 — so it lands on 2 units per arm with probability
C(10,2)² / C(20,4) = 2025 / 4845 ≈ **0.42**. At whatever seed the fixture happens to use it is a coin
flip whether `len(test ∩ arm) == 2` sees the bug at all: **a fixture whose numbers agree with the
bug.** Unequal arms do not repair it — 15/5 at `frac: 0.2` gives 3/1 with probability
C(15,3)·5 / C(20,4) ≈ 0.47 — because the roster-wide draw's *modal* split **is** the proportional
one.

**The rule, stated here so no later task re-derives it: per-arm counts cannot discriminate a
proportional split; only MEMBERSHIP at a pinned seed can.** So F6 pins the per-cell membership at a
fixed seed, and task 13 additionally computes the **roster-wide** draw at the **same** seed and
asserts the two differ — changing the seed if they coincide and recording that the check was run.
The union assertion (`len(test) == 4`) stays as a shape check and is not counted as discrimination.

**F7 — the thin-cell holdout refusal (Decision 10).** 20 units split **18/2**, `frac: 0.2`:
`holdout_sizes(20, 0.2) == (16, 4)` clears the roster bound, `holdout_sizes(2, 0.2) == (2, 0)`
(**measured**, M3) does not → `E-DATA-HOLDOUT-EMPTY` at `validate`, naming the 2-unit cell.
Can-fail control: the same 20 units split 10/10 validates clean.

---

## 10. What this slice refuses to build, each with its route — and there is no later slice

**Every line in this table ships with the project.** No slice is chartered after this one, so
*"whichever slice next touches X"* resolves to a closed slice the moment anyone reads it, and each
entry below is owned `unassigned` with that as the stated reason rather than as a placeholder.

| Declined | Route, and the fact that nothing follows |
|---|---|
| **A cluster spanning two cells** (Decision 13) | Legal under `by_attribute`, impossible under `random`. Breaks the between-sides independence H4c's clustered Welch df assumes. **Filed by task 20, owner `unassigned`, reason: no slice follows.** The route for a user is `method: random`, which allocates whole clusters, or a `cluster_by` nested inside the arm |
| **The per-STRATUM fold bound** | Still a check that does not exist, in this build and in every build. Cells add a **third** multiplier to `partition_units`' `c × s` independent lists; task 19 states that in the docstring and **this slice must not appear to have added the bound**. **Ships as a filing; nothing follows** |
| **`limits.min_clusters` under cells** (Decision 4) | The `min_clusters` denominator stays roster-wide, which H3d already found *"wrong in the direction of NOT firing"*. Settling it needs an argument about what a clustered percentile interval rests on under `between`, which is a statistics question. **Filed by task 20; nothing follows** |
| **`limits.max_ineligible_fraction`** and the rest of the silent-`limits` family | Out of scope; unchanged by this slice. **Ships unread; nothing follows** |
| **The `W-…-THIN` family's documentation question** | Already filed and unowned. `W-DATA-CELL-THIN` **joins** the family rather than settling it, and task 18 says so in the filing rather than claiming a closure. **Nothing follows** |
| **A nested per-cell `partitions` shape in `sweep.yaml`** | Declined for the disclosure key (Decision 11). If a reader judges the key insufficient, the nested shape is a known fallback with a known cost. **Nothing follows** |
| **`partition_units`' signature, `_assign_whole_clusters`, `_seed_from`** | Untouched by ruling — the trade this slice must not make is a fold regression bought for an arm feature. **Nothing follows this slice**, so an unclustered draw pinned here is pinned for good |
| **Interactions, dose-response orderings, difference-in-differences over cells** | Unchanged non-promises: a `summary`-step `Estimate`. `experimental-designs.md` § What core will not do for you already carries them, with reasons. **Nothing follows this slice**, and these are refusals with reasons rather than gaps, so that is the intended end state rather than a cost |

---

## 11. Mutations — each with the assertion that catches it, and two branches that can differ

Checked in advance: for each, the two branches produce different observable values on a fixture that
exists. **A mutation is a claim too.**

| # | Mutation | Caught by | The two branches differ because |
|---|---|---|---|
| MU-1 | `cells_of` skips empty cells | F2 variant with a crossed axis pair whose intersection is empty: the cell count assertion | 4 cells against 3 — a count, not a membership, so it is visible |
| MU-2 | `cells_of` intersects with `or` instead of `and` (union not intersection) | F2's disjointness assertion over two axes | union puts a unit in two cells; disjointness fails |
| MU-3 | `cell_fold_basis` returns `max` over cells instead of `min` | F2: `{kind: fold, k: 3}` must be refused | max = 3 clears; min = 2 refuses. **Different cluster counts per cell is what makes this discriminating** |
| MU-4 | `cell_fold_basis` returns the **first** cell's basis | F2 with the cells given in **both** orders (`aaa_`/`zzz_` naming) | first-cell = 2 in one order and 3 in the other; min = 2 in both. **A single order rules out only one wrong answer** |
| MU-5 | `partition_within_cells` passes `digest + cell_label` instead of the bare digest | Guard pin arm A is untouched (one cell), so this needs its own: the **two-cell** partition contents at a pinned digest | per-cell digests give different memberships at the same `k` and the same cells |
| MU-6 | `partition_within_cells` merges by concatenating whole cells instead of index-wise | F2: fold *i* must contain units from **both** cells | index-wise fold 0 spans cells; concatenation puts cell 1 entirely in the early folds |
| MU-7 | `_fold_k`'s cell clause reached at only 2 of 3 emit sites | A `k: all` config plus a fixed-`k` config plus a direct `_fold_k` call, one per site, asserting the **message names the cell** | a site without the clause emits the old message; the assertion is on the message, not the code |
| MU-8 | `holdout_train` narrowed to the wrong arm (`arm_members[0]` instead of the execution's) | F4 with **two** arms and asymmetric membership | arm A's train side would hold arm B's keys; the subset assertion fails |
| MU-9 | `_resumed_allocation` does not re-derive partitions (**the pre-slice code**) | F5's membership assertion | the fresh and recorded decompositions differ **because the roster order differs** — M2 measured both seeds and both memberships |
| MU-10 | `_resumed_allocation`'s re-derivation moved outside the no-axis path (a gate added) | Guard pin arm D plus a no-axis resume asserting partitions are byte-identical to the first attempt's | a gate whose no-op arm is wrong changes a no-axis resume's folds |
| MU-11 | `W-DATA-CELL-THIN`'s cell-structure gate removed | Guard pin arm E (a 6-unit no-axis config's exact finding set) | the ungated check warns on every small config; arm E's set is exact |
| MU-12 | `W-DATA-CELL-THIN` compares against the **largest** cell | F3 with **unequal** arms (7/5, not 6/6) and `min_units_per_cell: 6` | largest = 7 does not warn; smallest = 5 does. **Equal arms would make this blind**, which is why F3's warning fixture is 6/6 and this mutation's is 7/5 |
| MU-13 | `E-DATA-HOLDOUT-EMPTY`'s bound left at `len(roster)` | F7 (18/2 split at `frac: 0.2`) | roster bound clears at 20, cell bound refuses at 2 |
| MU-14 | `partitions_within` written unconditionally | Guard pin arm B (no-axis `sweep.yaml` carries **no** such key) | an unconditional write adds a key arm B asserts absent |
| MU-15 | `holdout.within` written unconditionally | The round-trip pin arm C plus a no-axis `allocation.json` assertion | same shape as MU-14, in the other file |
| MU-16 | The hoist reordered so `arm_members` is called twice | Task 4's *"realized once per run"* assertion, a counting patch on `_resolved_group_axes` | one call against two — a count |
| MU-17 | `_resolved_holdout` ignores `group_axes` (the pre-slice roster-wide draw) | F6's pinned per-cell **membership**, plus its same-seed roster-wide comparison | the two draws differ at the pinned seed **by construction of the fixture**, which task 13 verifies rather than assumes — a count assertion here is ≈42 % blind (§ 9) |

**No mutation in this slice is declared blind in advance.** MU-9 was the candidate — Ruling KK's
mutation needs the fresh draw to differ from the recorded one, and under `by_attribute` correct and
buggy readings coincide — and **M2 measured the lever that separates them** (roster order moves
`units_hash`, hence `assign_seed_for`, hence the membership, while `_resumed_allocation`'s guards
compare sets only). Had that measurement come back the other way, MU-9 would have been blind and
**owed a replacement**; it did not, and the replacement is not needed. Task 17 restates this and
re-runs the measurement rather than trusting this paragraph.

---

## 12. Does § Executability on this build move? — derived

**No, and the four rows are derived per row rather than repeated as a number.** No fifth number is
minted, and no single figure is quoted for this analysis' executability — quote the table, or name
the dependency.

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** Unchanged. Two refusals
  are retired and neither is reachable: `grep -n "groups:" docs/feasibility-llm-growth-studies.md`
  → two hits, **both `groups: []`**; `grep -c "allocation: between"` → 1, read and confirmed to be a
  prose sentence listing fields no config declares, not a `data.units.allocation`. No config declares
  a `{kind: fold}` level; the one `holdout:` in a config block is the screening roster's and it sits
  beside `allocation: within` with `groups: []`. `E-REPL-FOLD-K-TOO-LARGE`'s widened bound and
  `E-DATA-HOLDOUT-EMPTY`'s widened bound both require cells to resolve, and none do. **The new
  warning cannot move this row in either case**: the row counts **errors**, and
  `W-DATA-CELL-THIN` is a warning that never changes an exit code — and it is gated on a cell
  structure none of the nine has.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. This slice reads no upstream and walks no
  lineage: it touches `units.py`, `replication.py`, `validate.py`, `cli.py`, `runner.py`,
  `sweep.py` and `artifacts.py`, none of which is `io.reuse_from`'s surface.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** Untouched, **and still unowned — and
  now permanently, because this is the last slice.** It is a construction inside `summarize_step`;
  nothing here enters that phase. Task 20's `spec-defects.md` sweep must state its owner as
  `unassigned` with *no slice follows* as the reason rather than as a deferral.
- **Row 4, free of every core-side dependency this analysis can name — 1.** Unchanged: E5, and only
  with the plugin written and installed.

The four-row table in [the feasibility analysis](../../feasibility-llm-growth-studies.md)
§ Executability on this build is **repeated character for character** by the entry this slice adds,
by the two independent extraction methods the H8a/H9a–H9d entries describe, and its cells still name
**H8a** — updating them is how a repeated table stops being repeated.

---

## 13. Batching — 23 tasks, six batches, every batch reviewed

| Batch | Tasks | What it is | Review |
|---|---|---|---|
| **A** | 1–3 | The guard pin (captured first, before anything moves), `cells_of`, `cell_fold_basis` | required |
| **B** | 4–7 | The hoist, `validate`'s cell view, the two basis call sites, `_fold_k`'s cell clause | required |
| **C** | 8–12 | The per-cell partition producer, the fixture and its control, `E-REPL-FOLD-CELLS` retired, `sweep.yaml`, `fold_members` shape verification | required |
| **D** | 13–17 | The holdout half. **Carries Ruling II's ordering constraint** | required |
| **E** | 18–20 | `W-DATA-CELL-THIN`, the empty-cell interaction, the filings sweep | required |
| **F** | 21–23 | The document sites, two end-to-end runs, the end-to-end resume | required |

**Batch D carries Ruling II's ordering constraint**, and it is enforced inside the batch rather than
between batches: **task 15 narrows `holdout_train` and deletes the assert in one commit**, and
**task 16 retires `E-DATA-HOLDOUT-CELLS` strictly after it**. No commit exists in which the assert is
gone and `holdout_train` still comes from `roster`. Task 13 (`_resolved_holdout`'s per-cell loop)
lands before task 15, because the narrowed train side is composed from the per-cell plan.

**Every batch is reviewed, including the last.** *A batch with no review is where the findings will
be* — twice a controller has run a final batch straight into the whole-branch gate, and the second
time three of four Majors lived in exactly that unreviewed task. Batch F is a documents-and-codes
batch, which is the one that looks safest to skip and whose output no later batch reads.

**Do not split the slice.** The seam is Batch C / Batch D — the fold half and the holdout half share
only tasks 1–7 — but **this is the last slice**, so a split leaves a remainder nobody picks up: a
build in which one evaluation split is drawn within cells and the other is still refused, with
`reference.md` § A fixed holdout split and § Clustered units disagreeing about the same rule. Build
all twenty-three or none.

---

## Correction to Ruling HH, 2026-08-25 — its stated premise is false, and the decision stands on a different one

**Correction C2 measured that Ruling HH's premise does not hold at HEAD.** The ruling argued the slice must
be built because *"two normative documents describe folds and holdouts inside cells in the present tense,
and where the code cannot follow the documents, the document changes first"* — so shipping the refusal
permanently would mean a larger document change than building it. **Measured: all three sites are marked
"not built".** The documents and the code already agree, and *an unbuilt reader of an unbuilt surface is
specification* — which is this project's own rule, cited against the ruling that forgot it.

**So the honest position is this.** Shipping the refusal permanently is **consistent**, requires no
document change, and the re-scoping's grounds for it are sound: the slice unblocks **zero** configs,
retires two refusals **no outside evidence hits**, and its original justification was consumed by the
three tasks that merged with H3d.

**The decision to build stands, on grounds that survive the correction:**

1. **It is the work that was asked for.** The charter names H3c-3's remaining tasks, and **scaling that
   down is the requester's call, not the implementer's.** This correction exists so the choice is visible
   rather than defaulted into — which is what Ruling HH said it wanted and then got wrong about why.
2. **Ruling II's fix is correct code either way.** `runner.execute_plan` composing an **arm-narrowed test
   side** with a **roster-wide train side** is wrong on its own terms; the refusal is the only thing making
   it unreachable, and *a guard whose correctness depends on a refusal nobody plans to keep is a defect
   with a delay on it.* Narrowing `holdout_train` per arm is right whether or not the refusal is ever
   retired.
3. **A refusal a design cannot route around is worse than one it can.** § What isn't a repeat presents a
   `groups` design and an evaluation split as ordinary and composable; today the pair is refused with no
   route. That is a real gap even though the mark is honest about it.

**What this correction costs if wrong**: the project spends its last slice on work no outside evidence
needs, and the reachable-leak class Ruling II names is opened for the first time — **which is exactly why
Ruling II is not deferrable and why no commit may exist with the assert gone and the train side still
roster-wide.** *The last slice is the last chance to not ship that.*

---

## Correction to Decision 8, 2026-08-25 (task 6) — the swallow list is six, not five

Decision 8 enumerates the faults `validate._resolved_cells` swallows as *"`ContractError`,
`NotImplementedError`, `KeyError`, `TypeError` and `ValueError`"*. **That list is one short, and the sixth
is `ZeroDivisionError`** — measured at task 6, when the function was first wired into `validate_config`,
by `tests/test_validate.py::test_a_ratio_whose_values_are_not_usable_shares_is_refused[all-zero]`.

An `assign.<axis>.ratio` whose weights are all zero reaches `units._apportion`'s `n * weight / total`
with `total == 0`. `ZeroDivisionError` is an `ArithmeticError` and so is caught by none of the five, and
before this wiring nothing in `validate` drew that shape for real — `_check_assign` refuses it from the
declaration as `E-DATA-ASSIGN-RATIO`. Without the sixth entry a config `validate` is supposed to
**refuse** raises a traceback instead: the collecting-to-raising fault the whole `try` exists to prevent,
reached through a config the suite already had.

**This replaces the five-item list in Decision 8 and nothing else in it.** The list stays an enumeration
rather than a bare `except Exception`, for `REPL_DECLARATION_CODES`' reason: a fault outside it is a
genuine core defect, and absorbing all of them is how a real error becomes a silent pass. The pin is that
existing test, which fails with the entry removed.

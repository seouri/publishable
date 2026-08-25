# H3c-3 re-scoping — folds and holdouts inside cells, the last slice

**Measured on 2026-08-25 against commit `3d72910`** (`main` at HEAD, clean tree; `git status
--porcelain` empty before and after every probe). **Read-only**: nothing under `src/`, `tests/`,
`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md` or
`docs/superpowers/spec-defects.md` was edited by this pass. Every project built for it lives under
the session scratchpad, **outside this repository** — H6a made the dirty gate load-bearing. The
suite was run once at HEAD as a baseline: **`3338 passed, 1 skipped, 2 xfailed in 363.52s`**.

The document under test is [`H3c-3-SCOPING.md`](H3c-3-SCOPING.md), measured at `df6b4d4` before
**H3d, H4a–H4d, H5a, H5b, H6a, H6b, H7a–H7d, H8a–H8c** and **H9a–H9d** merged — twenty-one slices
under one scoping. It is the charter here, not the answer.

---

## 0. Executive summary

**The premise the old scoping was built on is gone, and it was consumed by the three tasks that
shipped.** Its own § 7 recommended a third option the charter did not contain: refuse the
combination in 3 tasks and defer the other 14. **Recommendations 1 and 2 were both taken.** H3d
merged with H3c-3's 3-task refusal folded in, and at HEAD a `groups` + `between` + `fold` config
does not validate clean — it earns `E-REPL-FOLD-CELLS`, verified by running the real console script
(§ 1). The live correctness defect is closed. The two normative documents that claimed unbuilt
behaviour in the present tense now describe a refusal, and they describe it accurately (§ 7).

**So what the remaining 14 buy has changed in kind.** The old scoping's *entire* stated
justification — *"two normative documents claim, in the present tense and unmarked, that core does
something it does not do"* — is discharged. What is left is one capability, retiring two refusals
that **no config in the outside evidence hits**, unblocking **zero** of the nine experiments in
[the feasibility analysis](../feasibility-llm-growth-studies.md), against surface that has **grown**
in every direction measured here.

**Measured decomposition: 20 tasks, not 14** (§ 9), the same direction as every re-scoping in this
project. **Recommendation: do not build it. Ship the refusal and re-own the filing** (§ 10), and
absorb only the one item that has no owner and no successor.

| Claim of the original | Survives at HEAD? |
|---|---|
| Decomposition is 17 (of which 3 are the refusal, 14 the capability) | **No.** 20, measured task by task in § 9 |
| *"a `groups` + `between` + `fold` config validates clean and runs folds that are roster-wide"* | **No.** `E-REPL-FOLD-CELLS`, exit 1, § 1 |
| *"nothing in `validate.py` pairs `allocation` with a repeat kind"* | **No.** `_check_evaluation_split_cells` is exactly that check |
| *"`collapse_repeats`' `fold_members` argument is the only contact point"* | **No.** Four readers in `stats.py` alone, and 36 lines across four modules (§ 3) |
| *"the one `partition_units` call site in `cli.command_run`"* | **Half.** Still one call site — but in `_prepare_run`, not `command_run` (§ 4) |
| The hoist is needed; arm plans resolve after `resolve_repeats` | **Yes**, and H9a's Ruling S deliberately preserved it (§ 4) |
| The bit-stability oracle and what may/may not move (§ 2 of the original) | **Yes**, unchanged and re-verified (§ 5) |
| The measured empty-fold table, `[7, 3, 3, 1, 1]` vs `[7, 1, 0, 0, 0]` | **Yes**, reproduced byte for byte (§ 2) |
| `limits.min_units_per_cell` is read by nothing; declined as "a limits deliverable" | **Half.** Still read by nothing — but **there is no limits deliverable** (§ 8) |
| *"the realized fold sizes"* promised in `sweep.yaml` and written nowhere | **Yes.** Still promised at two sites, still absent from `sweep.py` |
| § 4's fear that the H3d retrofit could reach `allocation.json` and `io.units.train` | **Yes, and it understated it** (§ 6) |
| *"`resume` and `allocation.json`'s read-rather-than-re-drawn (no reader exists)"* | **No.** `_resumed_allocation` is that reader, and it is 130 lines (§ 6) |

**Four sharpest findings**, each measured rather than read:

1. **Retiring `E-DATA-HOLDOUT-CELLS` opens a cross-arm training leak that is already written.**
   `runner.execute_plan` composes an arm-narrowed test side with a **roster-wide** train side —
   `step_units = UnitList(list(scoped_units), train=holdout_train)`, where `holdout_train` is built
   in `cli` from `roster`, never from the arm. An `assert holdout_train is None or arm_members is
   None`, justified in its own comment by that very refusal, is the only thing keeping it
   unreachable (§ 6.1).
2. **`_resumed_allocation`'s written safety argument breaks under cells.** Its docstring rules that
   fold partitions need no override because *"`partition_units` is a pure function of the roster and
   the design digest"*. Under cells it becomes a function of the roster, the digest **and the cell
   decomposition** — which on a resume is overridden from the record, one function call after
   `_prepare_run` drew it fresh (§ 6.2).
3. **The old scoping's open ruling was already made, by H3d, in the direction it hesitated over.**
   `validate._holdout_test_partition` performs a **real** draw at the **real** `design_digest(doc)`,
   swallowing every fault. The precedent for "does `validate` draw for real to see a cell" exists and
   points one way (§ 4.3).
4. **`fold_basis` has a second `validate` call site that is not the fold's basis at all** — it is
   `limits.min_clusters`' denominator, narrowed to the holdout's test partition, with a comment
   calling the threading *"a cheap follow-up"*. Under cells it becomes a **third** question in one
   function, and no charter line covers it (§ 4.4).

---

## 1. The premise, re-measured by invoking

The old scoping's § 3 closes on a build claim: *"since H3c-1 shipped, a `groups` + `between` + `fold`
config validates clean and runs folds that are roster-wide."*

Built outside the repo: a scratch git repo, a 15-unit `index.csv` split 12/3 by an `arm` column,
`allocation: between`, `assign.arm.method: by_attribute`, `sweep.groups` naming `arm`, and
`replication.repeats: [{kind: fold, k: 5}]`. Run through the installed console script:

```
error   E-REPL-FOLD-CELLS    replication.repeats
        declares a `fold` level beside `data.units.allocation: between`, which divides the
        roster into cells. …
1 problem (1 error, 0 warnings)
EXIT=1
```

The same project with `holdout: {method: random, frac: 0.2}` and a group axis earns
`E-DATA-HOLDOUT-CELLS` — and, beside it, `E-DATA-ALLOCATION-WITHIN-ARMS`, which is a finding of its
own (§ 1.1).

**The charter's premise has changed.** Both codes emit from **one** site,
`validate._check_evaluation_split_cells`, called from `validate_config`; `grep -rn
"E-DATA-HOLDOUT-CELLS\|E-REPL-FOLD-CELLS" src/` returns hits in five files, of which only
`validate.py` carries a `c.error` — the four in `runner.py`, `units.py` and `cli.py` are comments
citing the refusal as the reason a branch is unreachable, which is § 6's subject. **§ Errors carries
one row per code covering every emit site, and here each code has exactly one**, so the two rows at
`reference.md` § Errors `validate` reports are total over their codes today.

### 1.1 The two spellings of a cell structure are not independent, and one message branch is unreachable in a clean config

`_check_evaluation_split_cells` computes `cells = allocation == "between" or bool(groups)` and picks
its message from a two-branch ternary: `allocation: between` wins, a non-empty `sweep.groups` is the
fallback. But a non-empty `sweep.groups` beside `allocation: within` earns
`E-DATA-ALLOCATION-WITHIN-ARMS` — measured above — and `allocation: between` with no group axis earns
*Allocation needs arms*. **So the `groups` branch of that message is only ever read by someone whose
config is already refused for a second reason.** Not a defect: the branch is pinned by
`tests/test_validate.py::test_a_group_axis_alone_triggers_the_refusal_without_between`, which asserts
the message rather than only the code, exactly because a code-only assertion would pass with the
ternary collapsed. Recorded because a retirement that deletes the ternary must not conclude from the
test's survival that the branch was dead.

---

## 2. The empty-fold-per-cell measurement, reproduced

The old scoping's table is the fixture the whole capability argument rests on. Re-run at HEAD
against a hand-built roster (15 units; clusters `S1`×7, `S2`×3, `S3`×3, `S4`×1, `S5`×1; `arm` by
attribute, first 8 `control`):

| Call | `k = 5` sizes at HEAD |
|---|---|
| whole roster, `clusters=` | `[7, 3, 3, 1, 1]` — no empty fold |
| `control` cell (8 units, 2 clusters) | `[7, 1, 0, 0, 0]` — **three empty folds** |
| `treatment` cell (7 units, 4 clusters) | `[3, 2, 1, 1, 0]` — one empty fold |

`fold_basis` answers **15** unclustered and **5** clustered over the whole roster, so `{kind: fold,
k: 5}` clears `_fold_k` on the numbers. The whole-roster row is the can-fail control: same fixture,
same `k`, no empty fold. `partition_units` does **not** refuse an empty fold and is not asked to.

**Which fixture this is, said rather than left ambiguous.** The `treatment` row here is `[3, 2, 1, 1,
0]`, matching [`H3c-SCOPING.md`](H3c-SCOPING.md) § What "drawn within each cell" adds, and **not**
`H3c-3-SCOPING.md`'s `[3, 3, 1, 0, 0]`. That scoping attributes the difference to its fixture putting
3 clusters in `treatment` where the other puts 4, and mine puts 4. **Neither table's prose
determines its own cluster-to-arm mapping** — both describe the roster as "15 units; clusters S1×7
S2×3 S3×3 S4×1 S5×1; `arm` by attribute, 8/7", which fixes the arm sizes and leaves the mapping
open. That under-specification is the finding; picking a winner would invent one.

---

## 3. The contact point, re-measured — read first, grepped second

The old scoping named **one**: *"`collapse_repeats`' `fold_members` argument."* **H5b split that
function and added a fourth reader.** `git log -S"def _gather_repeats"` → `06fdd3d` (H5b task 4);
`git log -S"def repeats_disagreeing"` → `8ffab8a` (H5b task 5).

**Enumerated by reading each module's fold/holdout region, then confirmed by grep.** The grep run was
`grep -rn "fold_members" src/`, which returns **36** lines across four files: `runner.py` 14,
`cli.py` 11, `stats.py` 10, `replication.py` 1 (the producer). Every hit is attributed below.

| Consumer | Module | What it does with a partition |
|---|---|---|
| `fold_members_for` | `replication.py` | The producer. Flat `label → frozenset(keys)` |
| `handed_to` | `stats.py` | Which repeat labels one unit was handed to |
| `_gather_repeats` | `stats.py` | **H5b.** One walk, two readers; carries every value raw |
| `collapse_repeats` | `stats.py` | Averages `_gather_repeats`' output |
| `repeats_disagreeing` | `stats.py` | **H5b's fourth reader.** Same four arguments, same walk |
| `attrition` | `runner.py` | `handed = union(fold_members) & keys`, against the **arm's** roster |
| `_handed_keys` | `runner.py` | Per execution; **raises** `E-RUN-FOLD-UNRESOLVED` on a label with no fold token |
| `_units_failed_anywhere` | `runner.py` | Takes both `fold_members` and `arm_members` |
| `execute_plan` | `runner.py` | The two asserts (§ 6.1), and the `train=` composition |
| `_condition_counts` | `cli.py` | Composes `_cond_roster` with `attrition` |
| `Prepared.fold_members` | `cli.py` | A frozen field of the H9a seam |
| `_execute_prepared` | `cli.py` | Unpacks it and threads it to five call sites |

**Four classes a name-grep cannot reach, found by reading** — this is where the old scoping's "only
contact point" claim actually failed:

- **`UnitList.train` and the `io.units.train` user surface.** A step never sees `fold_members`; it
  sees a `UnitList` whose `train` was composed for it. Both compositions are in `execute_plan`, one
  correct and one not (§ 6.1).
- **`eval_roster`** — `_evaluation_roster(roster, holdout_plan)`, the roster every denominator counts
  against, named in its own docstring as feeding **six** sites. Names no fold or holdout in its
  signature.
- **The six `Prepared` fields.** `partitions`, `fold_members`, `group_axes`, `holdout_plan`,
  `eval_roster`, `arm_members_map` — six of the dataclass's thirty-six, all frozen, all read across
  the H9a seam.
- **`_resumed_allocation`** — 130 lines that read the partition back off `allocation.json` and
  override it (§ 6.2).

---

## 4. What "drawing within a cell" requires, at HEAD

### 4.1 The order is unchanged, and it is no longer in `command_run`

Measured by reading `_prepare_run` (`cli.py`, the function H9a extracted): the sequence is
`clusters_of` → `fold_basis` → `resolve_repeats` → `partition_units` → `fold_members_for` →
`_resolved_group_axes` → `_resolved_holdout` → `_evaluation_roster` → `arm_members`.

**Ruling S holds and is discharged to this slice by name.** [`2026-08-23-re-entry-seam-design.md`](specs/2026-08-23-re-entry-seam-design.md)
§ Decision 2: *"They move as-is, in place, in their current order… H3c-3's remaining 14 owns the
phase hoist of exactly those two calls."* H9a's task-b2 report proves it mechanically — the two
calls sit inside a 419-line block whose diff is one line.

**Two things the old scoping could not have known.** The hoist now happens inside `_prepare_run`, a
function that did not exist, and it must preserve `Prepared`'s field set and `_execute_prepared`'s
unpack. And **`_resolved_group_axes` already sits above `_resolved_holdout`** — so the *holdout*
half needs no hoist at all. Only `fold_basis`, `resolve_repeats` and `partition_units` are above the
axes. The hoist is smaller than the charter assumed and lands in a more load-bearing place.

### 4.2 What the spine required of H3d, and what H3d delivered

[The spine design](specs/2026-08-08-implementation-spine-design.md) § Order, amended against outside
evidence charters H3d with two things *"or H3c-3's retrofit stops being small"*: **perform the phase
hoist**, and **express its split as "partition within each cell to declared target proportions"**.

**The hoist was not performed** — measured in § 4.1, and Ruling S then re-assigned it here. **The
second requirement was met by construction rather than by charter**: `units.holdout_for` is a pure
function of `(roster, block, seed, clusters)` and takes no cell parameter, so a per-cell loop is a
loop over sub-rosters and nothing inside it changes. `units.holdout_seed_for` is likewise a separate
single producer, which is what makes "one seed or one per cell" a ruling rather than a rewrite.

### 4.3 The drawn-axis ruling at validate time — already made, by H3d

The old scoping's task 1(a) left open whether `validate` may draw for real to see a cell's
membership, noting `_check_assign`'s draw is gated to the unstratified, unclustered case with the
placeholder digest `"validate"` — sound only because sizes are digest-independent there, and the
per-cell **cluster count** is exactly the seed-dependent quantity that gating excludes.

**H3d made the ruling.** `validate._holdout_test_partition` calls `holdout_for(roster, block,
seed=holdout_seed_for(block, design_digest(doc), roster), clusters=clusters)` — the **real** digest,
the **real** draw — inside a `try` swallowing `ContractError`, `NotImplementedError`, `KeyError`,
`TypeError` and `ValueError`, on the stated ground that a second answer computed here *"would be a
check aimed at a partition the run does not use."* The question is now "does H3c-3 follow H3d's
precedent", not "is a real draw permissible".

### 4.4 `fold_basis` has two `validate` call sites and they ask different questions

`grep -rn "fold_basis(" src/ | grep -v "def "` returns **three** call sites:
`validate.py` (the fold's own basis, feeding `_fold_k` and the `k: all` budget), `validate.py` again
(**`limits.min_clusters`' denominator**, narrowed by H3d to the holdout's test partition), and
`cli.py` (the run's). The second site's own comment: *"Not threaded through `basis` in this slice;
doing so is a cheap follow-up, not a correctness gap today."*

Under cells that becomes a **third** question in one function — the smallest cell's cluster count —
and the direction of the existing bug is instructive: H3d found `min_clusters` *"wrong in the
direction of NOT firing"*, 50 clusters at `frac: 0.2` leaving roughly 10 while `min_clusters: 20`
passed silently. **No charter line covers it.**

### 4.5 The cell decomposition is still the one genuinely new derivation

`units.arm_members(axes, conditions)` is keyed by **condition index** and takes no roster,
deliberately. Under `groups × grid` several conditions share one cell; under a group axis alone the
mapping omits every condition selecting no axis. Cells must be derived from the `ArmPlan`s. That half
of the old scoping is unchanged and correct.

`build_allocation_document(group_axes, holdout)` **takes no roster on purpose** — its docstring:
*"with nothing to read membership from, it cannot become a second producer of it."* A cell
decomposition function must not become one either, which is what "derive from the plans" buys.

---

## 5. The invariants a naive build would violate

`CLAUDE.md` § Invariants, checked against what a per-cell draw does:

| Invariant | Verdict |
|---|---|
| **Units are the inference base; repeats never are** | **Safe, and the per-cell bound is what keeps it safe.** `attrition` computes `handed = union(fold_members) & keys` against the **arm's** roster, and `_handed_keys` answers per `(arm, fold)`. A cell with fewer clusters than `k` contributes nothing to some fold, so that arm's denominator for that label is **zero** — the measured defect returning in a different currency. The per-cell `fold_basis` minimum is not hygiene; it is what makes `attrition`'s per-arm denominator non-zero and `_handed_keys`' answer non-empty |
| **A repeat is an execution; a fold is which units it sees** | **Safe.** Cells change *which* units, not how many folds. Fold *i* stays one execution per condition |
| **Pairing is over units** | **Safe under index-wise merge, unsafe otherwise.** Two conditions in one cell must share boundaries, which is what "once per run" already promises. `reference.md` § Clustered units' *"Partitions are computed once per run, not once per condition"* **survives cells** — its own following paragraph already reconciles them. Deriving cells from `arm_members` would draw one partition per condition and break it for real |
| **Condition vs. repeat** | **Safe.** A cell is a condition-side fact; a fold is a repeat-side one, and the loop crosses them without merging them |
| **Operation commands take paths and nothing else** | Untouched — this slice adds no command and no flag |
| **`code_hash`/`parameters_hash`/`input_manifest_hash`** | Untouched. `provenance.allocation_hash` is a **fourth** hash over `allocation.json` and is the one at risk (§ 6.3) |

---

## 6. The three places the retirement is not a deletion

### 6.1 A cross-arm training leak, already written, held back by one assert

`runner.execute_plan` carries two asserts, and only one of them survives this slice.

```
assert holdout_train is None or fold_members is None,   # E-DATA-HOLDOUT-FOLD — SURVIVES
assert holdout_train is None or arm_members is None,    # E-DATA-HOLDOUT-CELLS — RETIRED HERE
```

`E-DATA-HOLDOUT-FOLD` refuses a holdout beside a `fold` level and this slice does not touch it, so
the first assert stands. **The second is justified by the code H3c-3 retires.** Its comment says so:
*"`E-DATA-HOLDOUT-CELLS` (task 8) refuses a holdout beside the group axis `arm_members` comes from."*

What is behind it, read rather than assumed: `execute_plan` narrows to the arm first —
`scoped_units = UnitList([u for u in units if u.key in arm_keys])` — and then composes
`step_units = UnitList(list(scoped_units), train=holdout_train)`. **`holdout_train` is not narrowed.**
`cli` builds it as `UnitList([u for u in roster if u.key in set(holdout_plan.train)])` — from
`roster`, never from the arm. So the moment the assert is retired, a condition in arm A gets a test
side that is arm A's and an `io.units.train` that includes **arm B's training units**.

Two things make this the sharpest finding in the pass. The composition is **written and wrong**,
not missing — a reviewer reading for a gap finds code. And the **fold** path fifty lines below gets
it right: `train=UnitList([u for u in scoped_units if u.key not in handed])`, arm-narrowed, with a
docstring saying why. **The sibling that already got it right is in the same function.**

`cli._resolved_holdout`'s docstring is the third site to update: *"`group_axes` is deliberately not a
parameter: a holdout beside a group axis is refused at this commit as `E-DATA-HOLDOUT-CELLS`."*

### 6.2 `_resumed_allocation`'s safety argument does not survive cells

H9b built the reader the old scoping said did not exist. `_resumed_allocation` replaces the arm
memberships and the holdout partition `_prepare_run` just resolved with the ones the first attempt
recorded, through `dataclasses.replace` on the frozen `Prepared`, and calls `arm_members` **again**
on the overridden axes. Its docstring carries a written ruling:

> **Fold partitions are deliberately not touched here.** … `partition_units` is a pure function of
> the roster and the design digest — so correct and buggy readings coincide for every fixture this
> slice can build.

**Under cells that premise is false.** A per-cell partition is a function of the roster, the digest
**and the cell decomposition** — and the cell decomposition on a resume is exactly what this function
overrides, one call after `_prepare_run` drew it fresh. A resumed run would then evaluate folds drawn
from a **second draw** of the arms while executing against the **recorded** ones. Under
`by_attribute` the two coincide; under `random` or `blocked` they do not, which is the same
correct-and-buggy-coincide trap the docstring is warning about, pointed the other way.

**A safety argument in a comment is a claim.** This one needs a mutation, and the mutation is a
`random`-assigned two-arm resume — a fixture this slice can build and H9b could not.

### 6.3 The recorded shape, and a round-trip pin that may have to move

`build_allocation_document` writes four top-level keys; `holdout` is flat — `train`, `test`, and
`seed`/`strata` when the split was drawn. **A per-cell holdout's union is still a partition of the
roster, so a flat record stays truthful and `_resumed_allocation`'s set-equality guards still pass.**
That is the ruling to make explicitly rather than by default, because the refusal's own stated
ground argues the other way: it refuses rather than discloses precisely because a truthful record
*"whose imbalance is visible only to a reader who crosses it against the arms list by hand"* is the
silently-wrong class. **A flat per-cell holdout record is that same reader, doing that same cross.**

If the shape gains a cell key: `reference.md` § `allocation.json` prints the document in full,
`provenance.allocation_hash` covers the file, and `_resumed_allocation`'s **round-trip pin** — *"the
rebuilt document equals the recorded one"* — must move. **A pin that must move can be moved once, by
a named task, with its post-edit state specified in advance** (H8a's precedent). Task 14 is that
task and § 9 names it.

The same question, one document over: `sweep.yaml`'s `partitions` composes `train` as *"every other
partition concatenated in fold order"* — **across cells**. The runner is safe; the record is not.
Under per-cell folds this is a correctness change to the record, not a formatting one.

---

## 7. Documented rows and claims, checked against the code

**Every claim below was grepped, and every hit is attributed.** Greps: `grep -n
"E-DATA-HOLDOUT-CELLS" docs/reference.md` → **3** (two § Errors rows, one § A fixed holdout split
bullet); `grep -n "E-REPL-FOLD-CELLS" docs/reference.md` → **4** (§ Validation's *Folds fit inside
the cells*, the same two § Errors rows, § Clustered units' fold paragraph); the same two greps over
`docs/experimental-designs.md` → **0**, its § Between-subjects factorial naming the refusal in prose
without a code; over `docs/design-principles.md` and `README.md` → **0**.

**Seven document sites the retirement must reach**, none locatable by position: `reference.md`
§ Validation's *One split, not one cell each* and *Folds fit inside the cells*; § Errors `validate`
reports' two rows; § A fixed holdout split's *"A roster-wide split beside a cell structure is
refused, not drawn"*; § Clustered units' *"Under `allocation: between`, a roster-wide fold is
refused rather than drawn within each cell"*; and `experimental-designs.md` § Between-subjects
factorial's *"A fold or a holdout drawn within each cell is not built"*.

**A row that must be rewritten *back*, not deleted.** *Folds fit inside the cells* currently reads
*"Superseded by One split, not one cell each"* — it points at the row the retirement removes.
Deleting the pointed-at row and leaving the pointer is how a § Validation table acquires a dangling
reference. It must be restored to its pre-H3d meaning: `k` bounded by the smallest cell.

**Rows still describing behaviour with no code behind it**, re-verified rather than carried:

| Row / claim | Where | Code? |
|---|---|---|
| *Cells are populated* | `reference.md` § Validation | **No**, and honestly marked *"specified, not built in this build"* |
| *Allocation is coherent* | `reference.md` § Validation | **No**, same marking |
| *"the realized fold sizes when `cluster_by` makes them uneven"* | § The other files a run writes **and** § Clustered units | **No.** `grep -n "sizes" src/publishable/sweep.py` returns nothing; `build_sweep_document` writes `fold`, `test`, `train`. The old scoping's § 3 defect 4, filed as free-riding on its task 12, is **unclosed at HEAD** |

**`CLAUDE.md` § Misreadings' "unbuilt reader of a shipped surface" row has run out of examples.**
The row names `field_convention` as *"now the sole remaining example, owned by nobody"*. **H9d task 6
(`ebdc047`) gave it a reader**: `docs.py` renders `` `{cls.field_convention}` `` into the templates
region, alongside `default_repeats` and `naming_pattern`. **`limits.min_units_per_cell` is the
replacement example** and is a better one: `materialize.py` writes `min_units_per_cell: 20` into
every generated config and `envelope.py` types it, and `grep -rn "min_units_per_cell" src/` finds no
third hit that reads it. The row keeps its evidence value only if the new example is installed.

---

## 8. `min_units_per_cell` is coupled to this slice, not merely adjacent to it

The old scoping declined it: *"a limits deliverable."* **There is no limits deliverable.** The spine's
order is exhausted — H4, H5, H6, H7, H8 and H9 are all complete, and this is the last slice. Its
`spec-defects.md` entry names its owner as *"whichever slice builds it"*, the form the file rejects
by name at its own `RE-OWNED 2026-08-19` entry.

**The coupling is not adjacency.** Once folds are drawn within cells, `_fold_k`'s per-cell bound
**refuses** exactly the thin-cell designs `min_units_per_cell` was specified to **warn** about — a
2-unit arm cannot carry `k: 5` and earns a hard error, while the same 2-unit arm with no fold at all
still completes silently and reports a real `basis: units` interval over two observations. The
capability makes half the gap loud and leaves the other half exactly as quiet.

So it is absorb-or-ship with a stated cost, not a decline: **absorb** means two warnings and moving
two § Validation rows off *"specified, not built"*; **ship** means the two rows stay marked and the
filing is re-owned `unassigned` with the honest reason that nothing follows.

---

## 9. Decomposition — 20 tasks, every one named

At the grain of H3c-1 (20), H3c-2 (14), H3d (16) and H9a (12). Derived from the enumeration below
rather than adjusted from 17. Charter lines from `H3c-SCOPING.md` § The task enumeration are marked
`[c1]`–`[c6]`.

### Batch A — rulings and the guard pin (2)

1. **The rulings, before any code.** (a) `allocation.json`'s `holdout` under cells — flat or
   per-cell, with § 6.3's argument against the default answered rather than assumed. (b)
   `sweep.yaml`'s `partitions` shape, and what a cell's fold reports as `n`. (c) Whether `validate`
   draws for real to see a cell under `random`/`blocked` — H3d's precedent (§ 4.3) argued for or
   against, not rediscovered. (d) `min_units_per_cell`: absorb or ship (§ 8). (e) One seed per cell
   or one per run for the holdout.
2. **The guard pin, captured first, with its editor named in advance.** The bit-stability oracle
   (`test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`, the full 5×10 fold contents at
   `_roster(50)`, `k=5`, digest `"d"`) plus a **new** pin that a no-cell design still makes exactly
   one `partition_units` call, with the bare digest, producing byte-identical output. H8a's rule:
   the sole editor and the post-edit state are specified now.

### Batch B — the decomposition and the hoist (3)

3. **The hoist** `[c3]`. `_resolved_group_axes` and `arm_members` above `fold_basis` /
   `resolve_repeats` / `partition_units`, **inside `_prepare_run`** (§ 4.1). Discharges Ruling S.
   `Prepared`'s field set and `_execute_prepared`'s unpack unchanged; "realized once per run"
   preserved and asserted.
4. **`units.cells_of(group_axes)`** — disjoint sub-rosters from the `ArmPlan`s, not from conditions
   (§ 4.5). The empty-cell case and the no-axis case (one cell, the whole roster) are part of the
   contract, not edge handling.
5. **`fold_basis` gains cells** `[c1]`. Minimum over cells of (cell unit count, or cell cluster
   count); **one number, not two** — the return type does not change. Both `validate` call sites and
   `cli`'s, **and the `limits.min_clusters` third question** (§ 4.4), which is where this task is
   bigger than its charter line.

### Batch C — the fold half (4)

6. **`_fold_k`'s cell clause** `[c2]`: a third `E-REPL-FOLD-K-TOO-LARGE` message naming the cell and,
   under `cluster_by`, its cluster count — with its § Errors row.
7. **The per-cell loop at the `partition_units` call site** `[c3]`. Index-wise merge, **bare digest
   per cell** — `partition_units` seeds its own RNG per call, so per-cell calls are independent of
   cell order and of how many cells there are, which is strictly better than the per-stratum branch's
   threaded RNG. `partition_units`' signature and body untouched.
8. **The cell fixture and its can-fail control**: § 2's `[7, 1, 0, 0, 0]` against `[7, 3, 3, 1, 1]`,
   unequal clusters per cell so a cluster-aware partitioner cannot look cell-aware.
9. **`E-REPL-FOLD-CELLS` retired**, plus the property it was standing in for: `attrition`'s per-arm
   denominator and `_handed_keys`' per-`(arm, fold)` answer are non-empty **because** of task 5's
   bound (§ 5). Pinned by mutation, not asserted.

### Batch D — the holdout half (5)

10. **`_resolved_holdout` gains `group_axes`** and loops `holdout_for` per cell `[c6]`; its
    "deliberately not a parameter" docstring rewritten rather than left (§ 6.1).
11. **`holdout_train` narrowed per arm in `runner`** — the second assert retired and the cross-arm
    training leak closed (§ 6.1). **The single most important task in the slice**, and the one whose
    fixture must exist before the assert is deleted.
12. **`E-DATA-HOLDOUT-CELLS` retired**, and `sweep.yaml`'s `partitions` composing `train` **within**
    the cell `[c5]` — a correctness change to the record, with its § The other files a run writes
    sentence.
13. **`allocation.json`'s `holdout` under cells**, per task 1(a), under the unchanged whole-file
    `provenance.allocation_hash`.
14. **`_resumed_allocation`** — the fold-partition ruling rewritten (§ 6.2), the holdout override's
    guards extended, and **the round-trip pin moved once, by this task, to the state task 1(a)
    specified**.

### Batch E — documents, interactions, end-to-end (6)

15. **The seven document sites** (§ 7), including *Folds fit inside the cells* rewritten **back**
    rather than deleted, and both § Errors rows removed from the registry `[c4]`.
16. **The empty-cell × empty-fold-per-cell interaction**: refused where it can be, **recorded** where
    it cannot. Cells add a third multiplier to `partition_units`' `c × s` independent lists, and the
    per-**stratum** bound is still a check that does not exist — this slice must not appear to have
    added it.
17. **`fold_members` shape verification** — assert rather than assume that the flat mapping survives
    per-cell partitions, across **all four** `stats.py` readers (§ 3), not the one the old scoping
    named. Expected outcome: no code change, one test per reader.
18. **Two end-to-end `run`s**: `groups × fold` and `groups × holdout`. Per-cell membership in
    `sweep.yaml` and `allocation.json`, `io.units.train` inside the arm **for both**, and the
    per-condition `resolved == completed + ineligible + failed` identity.
19. **An end-to-end `resume`** over a `groups × holdout` run with `method: random` — the fixture
    § 6.2 says H9b could not build.
20. **`min_units_per_cell` executed** per task 1(d), **and the `spec-defects.md` sweep**: the
    `an evaluation split cannot be drawn within a cell` entry struck, and every entry whose
    `unassigned` reason enumerates *"H3c-3's remaining 14"* re-read — that phrase becomes false the
    day this slice merges.

**Count: 20.** Batch A 2, B 3, C 4, D 5, E 6.
Charter 14 → measured 20: the same direction as
H3c-1's ~15 → 20, H3c-2's 10 → 14, H3d's 3 rows → 16, and H9's 45 → 49.

**Should it split?** On the evidence, the seam is Batch C / Batch D — the fold half and the holdout
half share only tasks 3, 4 and 5. But **this is the last slice**, so a split leaves a remainder
nobody picks up, and the remainder would be whichever half ships second: a build in which one
evaluation split is drawn within cells and the other is still refused, with `reference.md` § A fixed
holdout split and § Clustered units disagreeing about the same rule. **Do not split. Build all
twenty or none.**

---

## 10. What must be declined, and the fact that nothing follows

**The command surface is finished and no slice is chartered after this one.** For every item below,
that sentence is the whole of the routing: there is no later owner, and *"whichever slice next
touches X"* resolves to a closed slice the moment anyone does.

| Declined | What it means now |
|---|---|
| The per-**stratum** fold bound | Still a check that does not exist. **Ships as a filing the project keeps**, and this slice must not appear to have added it (task 16) |
| *"the realized fold sizes"* in `sweep.yaml` | Promised at two `reference.md` sites, written at none (§ 7). **Ships as a filing**, or is absorbed into task 12, which already edits that sentence — the cheaper of the two, and the old scoping said so a slice ago and was not taken up |
| `limits.min_units_per_cell` | **Must be decided, not declined** (§ 8), because this slice changes what the gap means. Task 1(d) |
| The 43 `## OPEN` entries in `spec-defects.md` whose heading carries `unassigned` | **The project ships with them**, and after this slice their stated reason — *"no remaining slice (…H3c-3's remaining 14) has this surface"* — stops being a reason and becomes a fact. Task 20 |
| `partition_units`' signature and `_assign_whole_clusters` | Untouched, as in the original. The trade the slice must not make is a fold regression bought for an arm feature |

**The recommendation, stated plainly rather than left implicit.** The old scoping's own
justification for these 14 tasks was *"two normative documents claim, in the present tense and
unmarked, that core does something it does not do."* **The 3 tasks that shipped with H3d consumed
that justification entirely** — measured in § 1 and § 7. What remains buys: zero configs unblocked,
two refusals retired that nothing in the outside evidence hits, one capability no evidence has asked
for — against 20 tasks, a leak that is already written (§ 6.1), a resume path whose safety argument
breaks (§ 6.2), and a shipped artifact plus its round-trip pin (§ 6.3).

**So: ship the refusal.** Re-own the `an evaluation split cannot be drawn within a cell` entry as
`unassigned` with the honest reason — *no slice follows* — and take **task 1(d) and task 20 alone**,
because those two are the only items this slice's non-existence makes worse rather than merely
leaves open. A refusal with a route is the shape this project uses for exactly this situation, and
`reference.md` and `experimental-designs.md` already carry the route in the present tense, correctly.

If the decision goes the other way, § 9's twenty tasks and its five batches are the plan, and
**task 11 is the one that must not be deferred to a later batch**.

---

## Correction, 2026-08-25, made in the same pass — three claims re-measured

Appended rather than edited in, this repo's rule for a published claim. **The count does not move
and the recommendation does not move**; two tasks are re-sized, one is bounded, and **one claim
carried from the original scoping is withdrawn**.

### C1. Both fold codes have three emit sites each, and the § Errors row shape was not checked

The exact trap `CLAUDE.md` names — *"§ Errors carries one row per code, not per emit site, so a
diagnostic's unit of work is every site that raises or reports it"* — and § 9 sized two tasks
without running the grep.

`grep -rn "E-REPL-FOLD-K-TOO-LARGE" src/` → **three** sites that raise or report:
`validate.py` (a `c.error`) and **two** in `replication._fold_k` (units and clusters). The original
scoping's § 1 said *"two `E-REPL-FOLD-K-TOO-LARGE` messages, units and clusters"* — that counted
`replication.py` alone and **missed `validate`'s own**. Task 6's cell clause must reach all three,
or argue in writing which it does not reach; it stays one task and is bigger than its line reads.

`grep -rn "E-RUN-FOLD-UNRESOLVED" src/` → **three** sites: `runner._handed_keys` (a label with no
fold token), `cli`'s fold-with-no-roster guard, and **`sweep.py`** — the *"partitions were drawn but
no `fold` level is declared"* guard, which is the third and which § 3's reading of `sweep.py` saw
without connecting to the code. **The per-cell index-wise merge changes what that guard is looking
at**, so it belongs to task 7 rather than to a new task.

Neither code splits a task. **20 stands**, with tasks 6 and 7 re-sized.

### C2. WITHDRAWN — the *"realized fold sizes"* claim, carried from the original and not re-derived

§ 7 and § 10 both listed *"the realized fold sizes when `cluster_by` makes them uneven"* as a
promise with no code behind it, on the evidence that `grep -n "sizes" src/publishable/sweep.py`
returns nothing. **That grep proves the absence of a key, not the absence of the behaviour.**

Re-derived: `build_sweep_document` writes `fold`, `test` and `train` per entry, so **each fold's
realized size is `len(test)`, recorded per fold**. `reference.md` § The other files a run writes has
**no fenced `sweep.yaml` example carrying `partitions` at all** — the prose sentence is its only
description — so there is no example key contradicting the code either. Recording the membership
discharges *"records the realized sizes in `sweep.yaml`"*; a `sizes` key would be a derived
duplicate of a list already there.

**The claim is withdrawn from § 7's table and from § 10's declined table.** It is a wording nit at
most, and the free-ride onto task 12 that the original scoping proposed for it disappears with it.
**This is the exact move a re-scoping exists to prevent** — a claim carried from a stale document
because its supporting grep looked like a measurement — and it was made here, once, by the pass
whose § 0 lists that shape as its own finding.

### C3. Task 13's downstream is bounded, and smaller than § 6.3 implies

`allocation.json`'s readers, by file: `cli.py` and `artifacts.py` (the producers),
`lineage.read_allocation` (the reader `_resumed_allocation` calls), and comment-only mentions in
`validate.py` and `apparatus.py`. **`report.py`, `study.py` and `diff.py` read it at zero sites** —
`grep -rn "allocation" src/publishable/report.py src/publishable/study.py src/publishable/diff.py`
returns nothing. H8c's ruling that *a bundle never carries `allocation.json`* is what makes that
true, and it holds for `diff`'s rows as well.

So a shape change to the `holdout` key reaches exactly `lineage.read_allocation` and
`_resumed_allocation` — **task 13 and task 14, both already named**, and no fourth command. Task 13
is bounded, not grown.

### C4. What the mechanical pass actually proved

Stated precisely rather than as *"clean"*: the trailing-whitespace, tab, table-column, empty-row,
duplicate-anchor, `×`-for-`x` and relative-link checks all executed and all passed (the 85 flags
raised were `§`, the house style). **The internal `#anchor` branch never executed**, because this
document uses no internal anchor links — so that check is untested here rather than passed.

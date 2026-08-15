# H3d scoping — a fixed holdout split

Read-only measurement against `main` at `cb96c7d` (H3b merge; H3c-1 and H3c-2 landed
before it). Every identifier below was grepped, not remembered. Where a document
states something the build does not do, the two are labelled separately —
`reference.md` § A fixed holdout split is a **spec claim**, `partition_units`'s
signature is a **build fact**, and this slice exists because they differ.

**Verdict: 16 tasks**, against H3a's 12, H3b's 13, H3c-1's 20, H3c-2's 14. The
charter's *"3 rows"* is a floor on the § Validation rows, not a task count — the
same relation H3c-1 had, whose 15 rows ran 21 tasks.

**Shipping before H3c-3 is survivable**, but only if H3d refuses the
combination it cannot honour. See § 5.

---

## 1. What exists

### The refusal, and its exact shape

`validate._check_unimplemented` carries the last member of a tuple loop that used to
hold six:

```python
    for field, code in (
        ...
        ("holdout", "E-DATA-HOLDOUT-UNSUPPORTED"),
    ):
        if units.get(field):
```

**Build fact:** the guard is `units.get(field)` truthiness, so `holdout: null` — what
`materialize.py` writes into every generated config — passes, and `holdout: {}` passes
too. H3-SCOPING measured that hole (`holdout: {}` → zero findings) and it is still
open; task 2 closes it as a by-product of the envelope closure, not by a separate check.

`E-DATA-HOLDOUT-UNSUPPORTED` is the **only** `E-DATA-HOLDOUT-*` identifier that exists
anywhere in `src/` or the documents. Every diagnostic H3d needs is unminted. Verified:

```
grep -rno "E-DATA-[A-Z-]*" src/publishable/*.py | sort -u   # 36 codes, one holdout
```

### What is reusable unchanged

| Thing | State | H3d's use |
|---|---|---|
| `UnitList.train` | Built. Raises `E-STEP-UNITS-UNAVAILABLE` with the message *"needs a `fold` repeat or a `data.units.holdout`"* | **The attach point, already written for this slice.** A holdout is `_train` populated from a different partition source. No signature change |
| `UnitList` (iterate/`len`/index) | Built | Unchanged. Both partitions are `UnitList`s narrowed at construction, exactly what the fold branch already builds |
| `units._assign_whole_clusters_by_ratio` | Built by H3c-2 | **The clustered holdout draw**, at `weights = [1 - frac, frac]`. It deals whole clusters to the bucket furthest below its own target share — which is precisely "an uneven two-way split, no cluster divided" |
| `units._apportion` | Built | The unclustered holdout's sizes, same call `assignment_for`'s `random` path makes |
| `units._stratum_groups` | Built | `holdout.stratify_by`, realized the way `assign.<axis>.stratify_by` already is: draw inside each group from one carried generator |
| `units.arms_of` | Built | The `by_attribute` read, given two level literals — see § 2's open question |
| `units.stratum_varies_within_cluster` | Built by H3b, and its docstring **already names** *"§ Validation, rows Fold strata survive clustering **and Holdout strata survive clustering**"*, returning a fault rather than raising a code so the caller picks the identifier | The *Holdout strata survive clustering* row, with a new code |
| `units.clusters_of` | Built, single authority | Handed to the holdout draw, as it is to the fold draw and to `assignment_for` |
| `units.stratum_names` | Built | Normalizes a bare `stratify_by: label` and a `[label]` to one name, as `assign` already reads it |
| `artifacts.allocation_hash` | Built | Unchanged mechanically — it hashes whatever document it is given |
| `replication.REJECTED_KINDS` | Built | `{kind: holdout}` already routes to `data.units.holdout` under `E-REPL-KIND`. The *Holdout isn't a repeat kind* row is **already implemented**, so it is not one of the charter's three |
| `stats.handed_to`, `stats.collapse_repeats` | Built | **Unchanged, and the decision is that there is no `holdout_members`.** `handed_to(key, labels, fold_members=None)` returns every label, and `collapse_repeats` admits a unit "recorded in every repeat it was handed". A holdout multiplies no repeats and has **no labels to intersect**, so both stay on their `None` paths and the narrowing happens on the **roster** instead. Reaching for a parallel `holdout_members` mapping by analogy with folds produces a shape that cannot work — and is the mechanism behind trap 1: a training unit that reached `attrition`'s roster is recorded in zero repeats, dropped from the collapsed table, and lands in `failed` |

### What is genuinely new

| Thing | Why it is new |
|---|---|
| `units.holdout_for` (or equivalent) | No function produces a two-way roster partition from a `holdout` block. `partition_units` produces `k` **equal-ish** folds and takes no target proportions |
| A holdout seed derivation | `units._seed_from(digest)` hardcodes `sha256(digest + "\|folds")`. `assign_seed_for` is per-axis and reads `block["seed"]` under an axis name a holdout does not have |
| Runner narrowing at **every** scope | The fold branch does the opposite (§ 5, trap 2) |
| The `holdout` key in `allocation.json`, and the gate that lets the file exist without an arm | `build_allocation_document` returns `None` when `group_axes` is empty |
| ~9 `E-DATA-HOLDOUT-*` codes | None exist |
| `envelope.LEAF_TYPES` entries one level in | `"data.units.holdout": dict` and nothing beneath it |

### `partition_units` is *not* rewritten a third time

H3b-SCOPING § *What H3d needs from H3b* instructed H3b to state its rule "as a
roster-partition rule parameterised by target proportions, not as a fold-specific one",
so H3d could reuse it at `k = 2`, `(0.8, 0.2)`.

**Build fact: H3b did not do that.** `partition_units(roster, k, digest, clusters,
strata)` still takes a count and builds equal buckets, and `_assign_whole_clusters`
deals to the *least-loaded* of `k` **equal** buckets. The promise was kept one slice
later under another name: **H3c-2's `_assign_whole_clusters_by_ratio`** is exactly the
target-proportion primitive H3b was asked for, and its own docstring argues at length
why it is a sibling rather than a parameterization of `_assign_whole_clusters`.

So H3d touches `partition_units` **not at all**. It calls the H3c-2 primitive. That
inverts the charter's stated ordering reason ("each slice touches `partition_units`
exactly once") — the reason survives, the mechanism moved.

---

## 2. What the documents specify — spec claim vs. build fact

`reference.md` § A fixed holdout split, in full:

```yaml
    holdout:
      method: random                 # random | by_attribute
      frac: 0.2                      # test fraction, for random
      from: null                     # the attribute naming the partition, for by_attribute
      stratify_by: [label]           # balance the split on these
      seed: auto                     # derived from the design digest; recorded explicitly
```

| Spec claim | Where | Build fact today |
|---|---|---|
| `io.units` is the test partition, `io.units.train` the training one | § A fixed holdout split; § The importable surface's `io.units` row | `UnitList.train` exists and raises; nothing ever constructs a holdout `_train` |
| "the same two lists a `fold` repeat provides, without the repetition" | § A fixed holdout split | The fold path builds them **per repeat label**; a holdout has no label |
| `holdout` × `fold` mutually exclusive | § A fixed holdout split; § Validation *One evaluation split, not two* | Unchecked — `holdout` is refused wholesale first |
| `resolved` **is the test partition** — 20% of 240 reports `resolved: 48` | § A fixed holdout split, second interaction | `runner.attrition`'s `resolved` is `len(roster)`, whole or arm-narrowed. Nothing narrows to a test partition. **§ 5 trap 1** |
| Whole clusters to one side; `stratify_by` constant within a cluster | § A fixed holdout split, third interaction; § Clustered units | The primitive exists (`_assign_whole_clusters_by_ratio`), the check exists (`stratum_varies_within_cluster`), the caller does not |
| **Under `allocation: between` the split happens within each cell** | § A fixed holdout split, fourth interaction | Not possible in this build — folds are drawn over the whole roster too, which is H3c-3's charter. **§ 4** |
| `holdout.seed` defaults to `auto` and derives from the design digest | § What `auto` derives from, *An omitted `seed` is `auto`* | The digest **includes** `holdout.seed` — `hashes._units_excluding_assign_seed` drops `assign.<axis>.seed` and nothing else. **§ 5 trap 3** |
| Membership written to `allocation.json` under `provenance.allocation_hash` | § A fixed holdout split, closing ¶; § `allocation.json` | The key is deliberately omitted; three prose blocks say so |
| `method: random` needs `frac` in (0, 1); `by_attribute` needs `from`, column has **exactly two** values | § Validation *Holdout is resolvable* | Unchecked |

### Three under-specifications the documents owe before code

**(a) `by_attribute` never says which of the two values is the test side.** The example
uses `from: split` with values `train`/`test`, and § Validation says "expected exactly
two" — but a holdout declares no `levels`, and `arms_of` needs them. Either the two
literals are fixed (`train`/`test`, and a `{A, B}` column is refused) or core cannot
tell which side it is holding out. Nothing in the four documents settles it. **Task 1
settles it in `reference.md` first**, per CLAUDE.md's document-changes-first rule.

**(b) `allocation.json` has no home for a drawn holdout's seed or strata.** § `allocation.json`
prints four top-level keys and states, in bold, that **`seed` and `strata` are keyed by
axis** — a holdout is not an axis. The printed example shows `"holdout": {"train": [...],
"test": [...]}` with no seed anywhere. So a `method: random` holdout's realized seed is
recorded nowhere, which contradicts the block's own `# recorded explicitly` comment.
Two candidate shapes, and task 1 picks one: nest `seed`/`strata` inside the `holdout`
object (contradicts the printed example, so the example changes), or key them under the
literal `"holdout"` in the axis-keyed mappings (collides with a group axis a user names
`holdout`, since axis names are user-chosen).

**(c) The `auto` table has no holdout row.** § What `auto` derives from names
`holdout.seed` in prose but its four-row table (`seed` levels, `fold` boundaries,
`sweep.sample`, `assign.seed`) omits it, and the paragraph that names refusal codes for a
malformed pin names `E-SWEEP-SAMPLE-INVALID` and `E-DATA-ASSIGN-SEED` and nothing for
`holdout.seed`.

---

## 3. The shared artifact

**Build fact.** `artifacts.build_allocation_document(group_axes)` returns
`{"seed": {...}, "arms": {...}, "strata": {...}}`, and `None` when `group_axes` is
falsy. `cli.command_run` writes the file only when the return is not `None`, and
`provenance.allocation`/`allocation_hash` are `None` together on that same condition.

**The existing writer's shape does not accommodate H3d without change**, on three counts:

1. **The gate.** `if not group_axes: return None` must become "return `None` only when
   there is neither an arm assignment nor a holdout." § `allocation.json` says
   "Present only when an arm assignment **or** a holdout is declared"; today the
   disjunction has one arm.
2. **The key.** `holdout` is a fourth top-level key, `{"train": [...], "test": [...]}`,
   unit keys in the plan's own order. The absent-rather-than-null precedent is preserved
   in the other direction too: a run with an arm assignment and no holdout keeps writing
   three keys, not a `"holdout": null`.
3. **The signature.** It must take the holdout **plan**, never the roster and the block —
   `build_allocation_document`'s own docstring argues this at length for arms ("a second
   draw is a second allocation, and 'provably identical' is not something two calls can
   be made to promise — only not calling twice can"). That argument transfers verbatim.

`allocation_hash` needs **no change**: it canonicalizes whatever dict it is handed. Its
closing paragraph already anticipates H3d and rules out a separate `holdout_hash`.

**Three prose blocks assert the current absence and are owned edits**, all found by grep:
`artifacts.build_allocation_document`'s *"`holdout` is never written here"* block,
`artifacts.allocation_hash`'s closing paragraph, and `cli.py`'s comment at the write site
(*"`holdout` is never in this build's document at all"*). `envelope.py`'s *"H3d closes it"*
is a fourth.

---

## 4. The two prior rules it must consume

### Whole clusters — fully available, nothing new to invent

`units.stratum_varies_within_cluster(roster, cluster_by, stratify_by)` returns the first
offending cluster and its values, deliberately as a fault rather than a raise, *because*
two rows share it and each names a different declaration. H3d supplies the second caller
and the second code. `clusters_of` stays the single authority;
`_assign_whole_clusters_by_ratio` keeps clusters indivisible across the two sides. The
cluster-indivisibility promise in § Clustered units is therefore consumed, not restated.

### Cells — do not exist, and this is the reorder's whole cost

**Build fact.** Group axes expand and arms are realized (H3c-1, H3c-2), and
`runner.execute_plan` narrows each condition's roster to its arm. But **every partition
is still drawn over the whole roster**: `cli.py` calls `partition_units(roster, ...)`
once, before `expand(doc)` is even called, and `fold_basis` is the roster's. That is
exactly H3c-3's charter — *"`k` bounded per cell; the empty-fold-per-arm case"* — and
H3c-SCOPING measured the consequence: `k = 5` gives folds `[7,3,3,1,1]` over the roster
and `[7,1,0,0,0]` for one arm, three empty folds, `validate` silent.

**What a cells-unaware holdout gets wrong.** A roster-wide `frac: 0.2` under two arms
puts ~20% of the *roster* in test, not ~20% of each arm. The realized per-arm test share
is whatever the shuffle left, and in the small-cell case it can be **zero** — a
condition whose executions run over an empty test partition, reporting `resolved: 0`
beside a metric computed from nothing. § A fixed holdout split names this failure
explicitly and in advance: *"Splitting the roster first would leave cells with unequal
test sizes and, at worst, a cell with no test units at all."*

**How visible is it?** Barely. `allocation.json` would record a truthful `train`/`test`
membership, and a reader would have to cross the holdout list against the arms list by
hand to see the imbalance. That is the *silently wrong* class.

**But it is refusable.** The discriminator this repo already uses — stated in
`_check_unimplemented`'s own comment block and applied by `E-DATA-WEIGHT-CONTRAST`,
`E-DATA-CLUSTER-CONTRAST` and `E-DATA-ALLOCATION-CONTRAST` — is that a fault knowable
from the **declarations alone** is refused at `validate`, and one needing the roster is
checked where the run performs it. `data.units.holdout` beside a non-empty `sweep.groups`
(equivalently `allocation: between`) is knowable from the declarations, before any roster
resolves. So H3d refuses the **combination** while honouring the block — the exact
precedent H3a set and H3b and H3c-1 followed — and H3c-3 retires that code as its named
retrofit.

**Cost of the refusal, measured against the evidence driving the reorder: zero.** All
nine configs in `docs/feasibility-llm-growth-studies.md` declare `groups: []`,
`allocation: within`, `assign: {}`; the six that declare a holdout share one screening
`data.units` block. Verified by grep of every `holdout:`, `groups:`, `allocation:` and
`assign:` line in that file. So H3d-with-the-refusal still unblocks 6 of 9, and the
amended order **holds**.

---

## 5. Traps

### Trap 1 — the denominator, and it is more than `resolved`

`resolved` must become the test partition (48 of 240). Four consumers, and three of them
are not the one the document names:

| Site | Today | Under a holdout |
|---|---|---|
| `runner.attrition` → `n.resolved` | `len(roster)`, arm-narrowed by the caller through `_cond_roster` | Must receive the **test-narrowed** roster. Follow `_cond_roster`'s precedent exactly: narrow at the call site, never re-derive inside `attrition` |
| `cli`'s `W-DATA-INELIGIBLE` | `counts["ineligible"] / counts["resolved"]` | Follows automatically once `attrition` sees the test roster — no separate change, but a test |
| `runner.execute_plan`'s `max_failed_fraction` guard | `resolved = len(units)` on the **outer, un-narrowed** `units`; `_units_failed_anywhere(results, units, fold_members, arm_members)` | **Wrong by 1/frac if left alone.** Training units produce no results and can never fail, so a 0.2 holdout over 240 divides 48 possible failures by 240 — the guard fires at five times the declared threshold, in the direction of not firing |
| `provenance.units.n`, `units_hash` | `len(roster)`, whole roster | **Stay whole-roster.** They are the roster's identity, not a metric's denominator. State it, because 240-here/48-there reads like a bug to the next reader |

### Trap 2 — the scope gate is the *inverse* of the fold rule

`execute_plan` has `elif execution.scope in ("run", "condition"): step_units = None` —
folds put the units out of reach of the wider scopes. A holdout must **not** take that
branch, and `experimental-designs.md` § Cross-validation supplies the sentence:
*"Condition-scoped fitting is right for a fixed holdout and wrong for cross-validation."*
`summary` needs its own decision rather than inheriting the fold's: folds hand back the
whole roster there, but a holdout's `resolved` **is** the test partition, so summary
keeps test-with-train. Both are decisions to write down with their backing sentence, not
consequences of where an `elif` happens to fall. Mutual exclusion makes the fold branch
unreachable under a holdout — assert it rather than assume it.

### Trap 3 — the single-authority question, and the seed

**Should the holdout join `units.assignment_for`, or be a sibling? Sibling at the plan
level, shared primitives at the draw level.**

Against joining: `assignment_for` is per-axis; it takes `levels` from `sweep.groups`;
it raises `E-DATA-ASSIGN-LEVELS` and `NotImplementedError` under assign-named contracts;
its result feeds `arm_members` and therefore condition selectors; and it seeds through
`assign_seed_for(block, axis, digest, roster)`, which needs an axis name. A holdout has
no axis, must never enter `arm_members` (it is not a condition selector), and has fixed
level names. Folding it in means emitting `E-DATA-ASSIGN-*` codes for `holdout` faults
and inventing an axis name that could collide with a real one.

For sharing primitives: a holdout **is** `assignment_for`'s two paths with two fixed
levels — `by_attribute` is `arms_of` on a column, `random` is `_apportion` (unclustered)
or `_assign_whole_clusters_by_ratio` (clustered) with `_stratum_groups` wrapped around
either. That reuse is most of why this slice is small. `_assign_whole_clusters_by_ratio`'s
own docstring is the precedent for the form: a sibling, argued in the docstring, sharing
the deal order.

**What must be replicated is the property, not the function**: a pure function of its
arguments, **one** producer, realized **once** in `cli.command_run` before the plan runs,
and the *same object* handed to the runner narrowing and to
`build_allocation_document`. Under a draw a second derivation is a second allocation —
`build_allocation_document`'s docstring already makes that argument for arms and it
transfers unchanged.

**The seed.** `_seed_from` hardcodes the `"|folds"` suffix. Holdout and fold are mutually
exclusive, so no collision can occur in one run, but the suffix is a decision to state
with its reason, not to inherit. And the derivation is **self-referential today**:
`design_digest` canonicalizes `data.units` wholesale minus `assign.<axis>.seed`, so a
pinned `holdout.seed` moves the digest that the derivation of every *other* auto value
reads — reseeding every repeat, every `sweep.sample` draw, and every arm allocation.
`spec-defects.md` has this as an **open** entry (the `holdout.seed` half of the
`assign.seed` finding closed by H3c-1 task 16): *"the slice that builds
`data.units.holdout` owes either the same exclusion in `design_digest` or a stated reason
the two seeds differ."* H3d owes it, and it is one line beside `_units_excluding_assign_seed`.

### Trap 4 — "read rather than re-drawn on resume" still has no reader

`OPERATION_COMMANDS = {"validate", "run"}`; there is no `resume` command, so nothing
reads `allocation.json` back. Under `by_attribute` a re-derivation re-reads the same
column and agrees. Under `method: random` it is a second draw of which units were held
out. H3d does **not** build `resume` (that is H9) — it inherits the contract paragraph
and extends it to the holdout half, and it must not let the missing reader become an
argument for re-deriving.

### Trap 5 — where a zero-size test partition is refused

Mirror the assign split exactly rather than inventing a third siting rule: § Validation's
*Every arm draws units* is "reported for the unstratified, unclustered draw only — a
clustered draw and either kind of stratified draw are checked where the run performs
them." A `frac` that apportions zero test units gets the same treatment.

---

## 6. Decomposition — 16 tasks

| # | Task | Why separate |
|---|---|---|
| 1 | **Documents first.** Settle § 2's three under-specifications in `reference.md`: which `by_attribute` value is the test side; where a drawn holdout's `seed`/`strata` live in `allocation.json`; a holdout row in § What `auto` derives from's table plus its seed-refusal code. Mint every new `E-DATA-HOLDOUT-*` in § Errors `validate` reports. Add two § Validation rows the charter's three do not cover — the group-axis refusal, and the empty-test-partition refusal. **The three `holdout: null` sites, named rather than left to a later grep:** § The one config file's fenced `holdout: null # NOT BUILT — …` line (marker *and* comment); ¶187's register, four declarations to three (verified by grep: there is no second `-UNSUPPORTED` family count in `reference.md`, so task 14 decrements nothing further); and ¶187's clause **"`.holdout` inherits the same treatment when its slice lands"**, which task 2 discharges — `spec-defects.md`'s *RESOLVED (arms-drawn, task 4)* entry exists precisely because the identical promise for `.assign` went unhonoured when `.assign`'s slice landed. `materialize.py`'s generated line gains its shape in a comment the way its `measurements` sibling carries `{by: read_id, collapse: mean}`. Both consistency passes | CLAUDE.md requires it; three of these are things no document currently says, and the ¶187 clause is the exact staleness this repo closed a defect on last slice |
| 2 | **Envelope closure**, one level in: `data.units.holdout.{method, frac, from, stratify_by, seed}` in `LEAF_TYPES`, plus the `holdout`-stays-whole comment rewritten. Closes H3-SCOPING's `holdout: {}` hole as a by-product | `measurements.by`/`.collapse` is the exact precedent; § Validation ¶434 promises it |
| 3 | **`design_digest` excludes `holdout.seed`**, beside `_units_excluding_assign_seed`; close the open `spec-defects.md` entry | One line, and it must land before any pin is reachable |
| 4 | **`_check_holdout`, declaration half A**: `method` enum, `frac` in (0, 1) under `random`, `from` required under `by_attribute`, fields that mean nothing under the other method (the `E-DATA-ASSIGN-NO-DRAW` analogue), and the seed pin | Declaration-only; reports with no roster |
| 5 | **`_check_holdout`, declaration half B**: `stratify_by` existence — the *Stratification attribute exists* row's holdout branch, which H3b landed for `fold` and left for this slice — and the `holdout` × `fold` mutual exclusion | Different failure reason from 4; the exclusion reads `replication` |
| 6 | **Roster-dependent checks**: the `by_attribute` column resolving to exactly two values (and to the settled literals); *Holdout strata survive clustering* through `stratum_varies_within_cluster`; the unstratified/unclustered zero-size test partition | Needs the resolved roster, and its siting rule is trap 5's |
| 7 | **Refuse `holdout` × a group axis** with its own code, plus a `spec-defects.md` entry naming **H3c-3** as owner of the retirement | § 4. This is the deliverable that makes the reorder survivable |
| 8 | **`units.holdout_for` — the single producer.** Pure; `by_attribute` through `arms_of`, `random` through `_apportion` / `_assign_whole_clusters_by_ratio`, `stratify_by` through `_stratum_groups`. A plan object carrying `train`/`test`/`seed`/`strata` | The seam. Isolated from every caller, as `assignment_for` was |
| 9 | **The holdout seed derivation**, with its own digest suffix and its reason stated; a pinned integer returned literally, `bool` excluded, matching `assign_seed_for` | A second thing to get wrong inside 8 |
| 10 | **Realize once in `cli.command_run`** and pass the one object to both consumers — never re-derive | The property trap 3 turns on |
| 11 | **Runner narrowing**: `io.units` = test, `io.units.train` = train, at run, condition, repeat and summary scope; assert the fold branch is unreachable | Trap 2. The inverse of a rule already in the same function |
| 12 | **The denominators**: `attrition`/`_condition_counts` receive the test-narrowed roster at the call site; `max_failed_fraction` and `_units_failed_anywhere` likewise; `provenance.units.n`/`units_hash` explicitly stay whole-roster | Trap 1, the item most likely to ship wrong |
| 13 | **`allocation.json`**: the fourth key, the "both absent" gate, the plan-not-roster signature, and the `seed`/`strata` home task 1 settled. Rewrite the four prose blocks that assert the current absence | § 3 |
| 14 | **Retire `E-DATA-HOLDOUT-UNSUPPORTED`** — the tuple loop's last entry, so the loop itself goes; re-check `E-REPL-KIND`'s `holdout` route now that it points at a built field. **Expect the finding-order flip and its pinned test**, H3b task 8's own experience of a retirement. Code-collection membership, checked: `REPL_DECLARATION_CODES` gates only what `resolve_repeats` raises, so the new `E-DATA-HOLDOUT-*` codes join it **only if** the `holdout` × `fold` exclusion is sited inside `resolve_repeats` — task 5 sites it in `validate` instead, and the set stays as it is | Gated on the declaration changing the record, which 8–13 are what make true |
| 15 | **`experimental-designs.md` § Train-test holdout unblocked**; the *Mistakes core prevents* entries re-checked against the new refusals; the feasibility analysis's executability table refreshed to the measured count | The design document is the reader-facing half |
| 16 | **Regression**: a no-holdout run is byte-identical to today (`fold_members=None`'s own oracle pattern); the six holdout-declaring feasibility configs validate clean with a table roster | H3a's lesson, and the reorder's claim needs re-measuring rather than restating |

---

## 7. What is NOT in H3d

- **Drawing the split within each cell.** H3c-3's, by task 7's refusal.
- **`resume`.** H9's. H3d inherits the read-rather-than-re-draw contract paragraph and
  extends it; it builds no reader.
- **Three-way splits.** § A fixed holdout split is two partitions;
  `docs/feasibility-llm-growth-studies.md` routes a `dev` split into `step02` through
  `self.derive_seed("dev-split")` over `io.units.train`, which needs nothing from core.
- **`statistics.resample` / `null_test`.** H4's, and they remain 8/9 blockers.
- **`E-DATA-RESOLVER-UNSUPPORTED`.** Full H7's — the feasibility configs run *as written*
  only after it.
- **A `holdout_hash`.** `allocation_hash` covers the document;
  `artifacts.allocation_hash`'s docstring already rules the alternative out.
- **Any `limits.min_units_per_cell` warning.** Specified, unbuilt, and carried by an open
  `spec-defects.md` entry that leaves the naming to whichever slice builds it — H3d does
  not, since a thin *test* partition is refused outright by task 6 rather than warned about.
- **Interactions between a holdout and `data.units.measurements` or `weight_by`.**
  Neither partitions; the collapse runs before any split, and a weight is a per-unit
  attribute either partition carries.

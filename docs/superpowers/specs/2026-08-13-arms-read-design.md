# H3c-1 Arms read design

**Goal:** a `sweep.groups` axis expands into conditions and each condition's units are the arm named
by an attribute — `allocation: between` with `assign.method: by_attribute` — recorded in
`allocation.json` under `provenance.allocation_hash`. Retires `E-SWEEP-GROUPS-UNSUPPORTED`,
`E-DATA-ALLOCATION-UNSUPPORTED` and `E-DATA-ASSIGN-UNSUPPORTED`; refuses `random` and `blocked` **as
method values**.

**Why first among H3c's three:** `by_attribute` **reads** an arm from a column. `random` and `blocked`
must **draw** one, which is a second mechanism with its own seeding and its own artifact semantics.
Reading is runnable and recordable on its own; drawing is not needed to prove that a group level is a
set of units. Splitting there is what keeps this slice's 20 tasks from being 36.

## The sentence H2 deferred, and why it is still right

H2's spec, refusing `groups` and assigning it here:

> A group level **is a set of units**, and the assignment that makes it one is H3's… a `groups` axis
> that expanded conditions while handing each the same roster would run to completion and **report two
> identical measurements as two arms** — precisely what `experimental-designs.md` § Mistakes core
> prevents exists to make structurally impossible.

That is the acceptance bar. This slice is done when a `groups` axis produces conditions whose rosters
**differ**, and when handing them the same roster is impossible rather than merely avoided.

## What the scoping measured, against the charter

`docs/superpowers/H3c-SCOPING.md`. The charter said "15 rows, rewrites `partition_units` again, for
cells". Three of those words are wrong and four things were never named.

| Charter | Measurement |
|---|---|
| 15 blocked rows | The count is right and **nearly the least informative number in the slice**: 15 owned, 1 shared three ways, **2 already implemented that this slice makes wrong**, 2 to write from nothing, 4 to widen or narrow |
| "rewrites `partition_units` again, for cells" | **It does not.** H3b's rewrite stands; cells attach at `units.fold_basis` as a per-cell minimum and at the caller's loop. That is **H3c-3's**, not this slice's |
| (silent) | **A cell's values become parameters.** `runner.resolve_condition_cfg` writes every `Condition.values` key into `parameters`. Verified against a control: a `{arm: control}` cell yields `parameters.arm = 'control'`, a parameter no template declares, flowing into `parameters_hash`. **Nine sites read `Condition.values`** |
| (silent) | **`assign.<axis>.from` is unreachable by `CONSTANT_COLUMN_RULES`**, whose comment names H3c by name |
| (silent) | **`design_digest` covers `data.units` wholesale, including `assign.seed`**, which § What `auto` derives from explicitly excludes |
| (silent) | **There is no `resume` command** — `OPERATION_COMMANDS = {"validate", "run"}` — so `allocation.json`'s "read rather than re-drawn on resume" has no reader; and § What `study add` redacts never names it, though it is the one artifact that is a list of **unit identities** |

Rows are cited by **title** throughout. The § Validation table is now **95 rows**; `H3-SCOPING.md`
said 89 and H3b's scoping said 91. That is `CLAUDE.md`'s cite-by-section rule arriving as a concrete
failure for the third time in H3.

## Scope

| In | Deliberately not here |
|---|---|
| `sweep.groups` expanding into conditions | `assign.method: random` and `blocked` — **refused by method value** (H3c-2) |
| `allocation: between` with `assign.method: by_attribute` | `k` bounded per cell, and the empty-fold-per-arm case (H3c-3) |
| The `AXIS_MODES` split into three predicates | `holdout` (H3d), which shares `allocation.json` |
| `allocation.json` and `provenance.allocation_hash` | The clustered/weighted **contrast** families, still refused and owned by H4 |
| The cell-values-are-not-parameters distinction, across all nine readers | |
| `assign.<axis>.from` joining the constancy check | |
| The two rows this slice breaks, and the `assign.seed` digest inconsistency | |
| Three retirements | |

## Architecture

**A cell either sets a parameter or selects units, and nothing may conflate them.** Today
`Condition.values` is uniformly "dotted path → value", and `resolve_condition_cfg` writes each into
`parameters`. A group cell is not a parameter: `{arm: control}` names a set of units. The distinction
has to be carried on the condition rather than re-derived at each of the nine readers, because
re-deriving it nine times is how eight of them agree and one does not.

**The roster becomes per-condition, and that is the whole feature.** Until now one roster is resolved
per run and shared across every condition — a property `Unit`'s own docstring cites as the reason it is
frozen and hashable by key. Arms do not change that: the roster is still resolved once, and an arm is a
**subset view** of it. Nothing re-resolves units per condition; what varies is which units a condition
is handed.

**`allocation.json` is written from the assignment, not from the run.** § The other files a run writes
gives its shape exactly — `seed`, `arms`, `holdout`, `strata`, keyed by axis, with **unit keys never
row numbers**, "because a roster that gains a unit renumbers rows and would silently repoint every
membership claim". H3d adds the `holdout` key to the same file, so the writer is shaped for both and
this slice fills one key.

**Three predicates, one derived vocabulary.** `AXIS_MODES` currently answers three different questions
with one tuple. `groups` contributes to the condition product, sweeps **no** parameter path, and
`ablate` **may** cross it. Split into `PRODUCT_MODES` and `PARAMETER_AXIS_MODES`, keeping
`SWEEP_MODES` **derived** from the partition so `E-SWEEP-KEY-UNKNOWN`'s choke point survives — the
property H2 built deliberately and pinned.

## Decisions

| # | Decision | Ruling | Grounds |
|---|---|---|---|
| 1 | `random` and `blocked` | **Refused as a method value**, H3c-2 lifts them | *Settled by the user.* Drawing an arm is a second mechanism with its own seeding and artifact semantics. Refusing a *value* while honouring the *block* is the precedent H3a set with `E-DATA-WEIGHT-CONTRAST` and H3b with `E-DATA-CLUSTER-DERIVED` |
| 2 | Where the parameter/selector distinction lives | **On the condition**, set by `expand`, read by all nine consumers | Re-deriving "is this a group path?" at nine call sites is how eight agree and one does not. `expand` is the only place that knows which mode produced a cell |
| 3 | Does the roster re-resolve per condition? | **No — an arm is a subset view** | One roster per run is load-bearing: `Unit` is frozen and hashable by key *because* the roster is shared. Re-resolving per condition would break `units_hash` and every provenance claim built on it |
| 4 | `allocation.json`'s "read rather than re-drawn on resume" | **Build the artifact and state the rule; record that it has no reader** | There is no `resume` command in this build. Writing the rule into the artifact's own docstring is honest; claiming the behaviour is tested would not be |
| 5 | `allocation.json` and `study add` redaction | **Record the gap, do not invent a rule** | It is the one artifact that is a list of unit identities and § What `study add` redacts never names it. Inventing a redaction rule here would be a rule no document states — the direction `CLAUDE.md` forbids |
| 6 | The `assign.seed` digest inconsistency | **Fix it here** | § What `auto` derives from explicitly excludes it, and `design_digest` includes it. That is a live contradiction, not a consequence of this slice — but this slice is the first that makes `assign.seed` reachable |
| 7 | Where a retired `-UNSUPPORTED` is recorded | § The one config file's `NOT BUILT` list, **seven → four** | That family is deliberately absent from the validate-time registry, so the list and not the table is where a refused block is named. The seven today are `sweep.groups`, `data.units.assign`, `.holdout`, the `{resolver: <name>}` form of `from`, any `allocation` other than `within`, `statistics.resample` and `statistics.null_test` — this slice removes the **first, second and fifth**. A count in prose that no mechanical check catches, and H3a nearly shipped it wrong |

## Where the constancy check must reach

H3b left a documented constraint in `units.py`: `CONSTANT_COLUMN_RULES` indexes `units_decl` by the
key itself, so it reaches **flat, string-valued keys of `data.units`** and nothing nested. Its comment
names `assign.<axis>.from` and `holdout.from` as the next two that will want the rule, and says that
adding either name to the registry **no-ops silently** — verified by probe when it was written.

`assign.<axis>.from` is nested under an axis name, so H3c-1 owes the accessor that comment predicted.
Without it, a `measurements` collapse **invents an arm membership**: the same shape H3a shipped for
weights and H3b closed for clusters, arriving a third time and worse, because a mis-collapsed arm
changes *which condition a unit is measured in* rather than how much it counts for.

## Risks

- **A fixture where cells and clusters are the same partition.** Then arm-aware and cluster-aware
  behaviour coincide and no test can tell them apart. This is the trap that has fired **ten times**
  across the last two slices — including one coincidence-prone in the *digest* rather than the sizes,
  and two mutations undetectable because what they removed was unreachable. **Every arm fixture states
  why its numbers discriminate**, and no arm fixture may share a boundary with a cluster fixture.
- **The `n` reconciliation.** `resolved == completed + ineligible + failed`. Arms partition units
  *across conditions*, so each condition's `resolved` is now a subset of the roster. Every new path is
  checked against `n`'s four parts, not only against its own output.
- **Three retirements at once**, unmasking 24 enumerated items. Three times running, a retirement has
  made a latent defect live — and once, the thing the plan called "unreachable" was made reachable by
  that same slice.
- **Twenty tasks.** Larger than either slice just shipped, and both of those grew mid-flight for the
  same reason: an outcome named in a heading with no step owning it. **The plan over-decomposes
  deliberately**, and every heading's outcome must appear in a step.
- **The worked example.** `cohort-pilot` declares no `groups`, `allocation` or `assign`, so nothing
  about it may move. Verified before designing; re-verified at the end with a real temporary commit.

## Testing

Every check needs a test producing its identifier; every declaration needs a second test proving its
effect. Three tests carry the slice:

| Test | Pins |
|---|---|
| A `groups` axis over an attribute with two levels — **the two conditions' rosters differ**, and neither is the whole roster | The acceptance bar H2 deferred: two arms, not two identical measurements |
| A `{arm: control}` cell — **`parameters` gains no `arm` key**, and `parameters_hash` matches the same design without the group axis | The largest unnamed item, and the one a reader would never look for |
| `assign.arm.from` naming a column that varies within a unit's measurement rows — **refused** | The third recurrence of H3a's defect, closed rather than repeated |

The second is the one to write first. Every other test in the slice passes whether or not the phantom
parameter appears.

**Mutations each must kill:** treating a group cell as a parameter path; handing every condition the
whole roster; deriving `SWEEP_MODES` by hand rather than from the partition; omitting `assign.from`
from the constancy registry; and writing row numbers rather than unit keys into `allocation.json`.

## Task sequence

Twenty tasks, over-decomposed on purpose. Six groups, ordered by what the next one needs.

**A — the documents first.** The two rows to write from nothing, the four to widen, and the two this
slice breaks — before any code, per the document-leads rule.

**B — the vocabulary.** The `AXIS_MODES` split into three predicates with `SWEEP_MODES` still derived,
and the discriminating test that `ablate × groups` stays legal.

**C — expansion.** `sweep.groups` producing conditions; the parameter/selector distinction on the
condition; all nine `Condition.values` readers taught it.

**D — assignment.** `allocation: between`; `assign.method: by_attribute`; `assign.<axis>.from` joining
the constancy check via the accessor H3b's comment predicted; `random`/`blocked` refused by value.

**E — the record.** `allocation.json` with unit keys; `provenance.allocation_hash`; the `assign.seed`
digest fix.

**F — the retirements and the passes.** Three codes retired only after everything they mask is handled;
then the consistency passes, the exit criterion, and the two gaps recorded rather than invented.

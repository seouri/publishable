# H3c Allocation, arms, assignment — scoping measurement

Read-only measurement, 2026-08-13, against `docs/reference.md`,
`docs/experimental-designs.md` and `src/publishable/` at `cb96c7d` (branch `main`, clean; H1,
H2, H3a and H3b landed). No source file was changed; the throwaway probe test written for this
document was deleted and `git status --porcelain` is empty afterwards. Every count states the
command that produced it, and every absence claim is paired with a **can-fail control** — a
perturbation of the same command that fires.

`--include='*.py'` is used on every `grep` over `src/`, so no string is read out of stale
`__pycache__` bytecode.

**Headline.** The charter's row *count* is right for once — all 15 titles exist — and that is
the least informative thing about this slice. The errors are elsewhere, and there are seven of
them. Two rows the charter does not list are **already implemented and H3c makes both wrong**
(*Grid size sane*, *Baseline leaves contrasts confounded*). One row is shared three ways and H3b
discharged only a third of it. Two `W-` identifiers do not exist. A row parallel to *Cluster is
constant within a unit* and *Weight is constant within a unit* **does not exist for
`assign.<axis>.from`**, which is the gap H3b's own `CONSTANT_COLUMN_RULES` comment names H3c
for. `design_digest` covers a field `reference.md` says it excludes. And the largest single item
is not `partition_units` at all: **`Condition.values` is overlaid onto `parameters`
unconditionally**, so a group axis would invent a parameter — demonstrated below.

**Verdict: not one slice. Three, in the order (i) arms read, (ii) arms drawn, (iii) folds within
cells** — and (i) alone is larger than H3b.

## Method

| Probe | What it ran | Where |
|---|---|---|
| Expansion probe | `sweep.expand`, `sweep.axis_modes_present`, `sweep._swept_paths` called directly on four sweep shapes | scratchpad, `uv run python` |
| Validate probe | `validate_config` over a real git repo through `tests/test_validate.py`'s `write_config` fixture and a 20-unit `index.csv`, each declaration probed **as a pair** — declared, and a control without it | throwaway `tests/test_zzz_h3c_probe.py`, run then deleted |
| Overlay probe | `runner.resolve_condition_cfg` called with a group-axis value beside a parameter path | scratchpad |
| Partition probe | `units.partition_units`, `units.fold_basis`, `units.clusters_of` on H3b's uneven cluster fixture (sizes 7, 3, 3, 1, 1 over 15 units), whole and split into two arms | scratchpad |
| Absence greps | Each paired with a control grep of the same shape that returns hits | `grep -rn --include='*.py'` |

The arm split in the partition probe is deliberately **8/7 over clusters of unequal size**, so
cells and clusters are not the same partition — the coincidence the charter's trap list names.

### The three refusals, confirmed in both directions

`validate_config` over the fixture, one row per config:

```
CONTROL plain roster                         -> ['W-DATA-CLUSTER-UNDECLARED']
CONTROL grid sweep only                      -> ['W-DATA-CLUSTER-UNDECLARED']
groups only                                  -> ['E-SWEEP-EXPANDS-EMPTY', 'E-SWEEP-GROUPS-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
groups × grid                                -> ['E-SWEEP-GROUPS-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
allocation: between alone                    -> ['E-DATA-ALLOCATION-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
assign alone                                 -> ['E-DATA-ASSIGN-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
assign by_attribute alone                    -> ['E-DATA-ASSIGN-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
the whole between design                     -> ['E-DATA-ALLOCATION-UNSUPPORTED', 'E-DATA-ASSIGN-UNSUPPORTED', 'E-SWEEP-EXPANDS-EMPTY', 'E-SWEEP-GROUPS-UNSUPPORTED']
assign: {} (init's documented value)         -> ['W-DATA-CLUSTER-UNDECLARED']
allocation: null                             -> ['W-DATA-CLUSTER-UNDECLARED']
allocation: ''                               -> ['E-DATA-ALLOCATION-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
groups: []                                   -> ['E-SWEEP-EXPANDS-EMPTY', 'W-DATA-CLUSTER-UNDECLARED']
groups: [{}] (empty axis)                    -> ['E-SWEEP-EXPANDS-EMPTY', 'E-SWEEP-GROUPS-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
assign with misspelled inner keys            -> ['E-DATA-ASSIGN-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
holdout: {} (whole-leaf control)             -> ['W-DATA-CLUSTER-UNDECLARED']
assign axis naming no group axis             -> ['E-DATA-ALLOCATION-UNSUPPORTED', 'E-DATA-ASSIGN-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
group level containing a slash               -> ['E-SWEEP-EXPANDS-EMPTY', 'E-SWEEP-GROUPS-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
budget grid only, max_executions 15          -> ['W-DATA-CLUSTER-UNDECLARED']
budget grid × groups, max_executions 15      -> ['E-SWEEP-GROUPS-UNSUPPORTED', 'W-DATA-CLUSTER-UNDECLARED']
site column, no cluster_by (warning control) -> ['W-DATA-CLUSTER-UNDECLARED']
site column, assign reads site               -> ['E-DATA-ASSIGN-UNSUPPORTED']
site column, groups names site               -> ['E-SWEEP-EXPANDS-EMPTY', 'E-SWEEP-GROUPS-UNSUPPORTED']
```

`W-DATA-CLUSTER-UNDECLARED` fires on every row whose config leaves `cluster_by` unset and does
not otherwise account for `site` — H3b's warning working, and this document's best can-fail
control. Its **disappearance** on the last two rows is a positive result in its own right, and
is used in § 6.

## 1. The three refusals

| Code | Emit site | Shape refused | What the documents say it should do |
|---|---|---|---|
| `E-SWEEP-GROUPS-UNSUPPORTED` | `validate._check_unimplemented`, a `for mode, code, why in (…)` loop now holding **one** entry, guarded by `if sweep.get(mode)` | truthy `sweep.groups` | § Expansion modes: a list always; a level *is* a set of units; conditions across it are unpaired; two arms share a `parameters_hash`; group axes cross each other and cross parameter axes; `baseline` accepts a group level; the baseline expands over group axes it does not fix; `ablate × groups` is legal |
| `E-DATA-ALLOCATION-UNSUPPORTED` | `validate._check_unimplemented`, a standalone `if units.get("allocation") not in (None, "within")` | any `allocation` outside `(None, "within")` — note this catches `""` and `false` too, a stricter guard than the truthiness loop | § Allocation: each unit belongs to exactly one arm; `io.units` yields only that arm; pairing is derived **per contrast** from which axes two conditions differ on, not per config; a contrast crossing two axes is `confounded: true` |
| `E-DATA-ASSIGN-UNSUPPORTED` | `validate._check_unimplemented`, the `for field, code in (…)` tuple loop — now `("assign", …)` and `("holdout", …)` only — guarded by `if units.get(field)` | truthy `data.units.assign` | § Allocation: one block per `sweep.groups` axis, keyed by axis name; `method: random \| by_attribute \| blocked`; `from` defaulting to the axis name; `stratify_by` over attributes **or an earlier axis**; `ratio` keyed by this axis's levels with `{}` meaning equal; `block_size: auto` = twice the ratio's sum; `seed: auto` |

All three are `c.error` calls inside `validate` itself — unlike H3b's
`E-REPL-FOLD-STRATIFY-UNSUPPORTED`, none is raised from a callee and translated, so **H3c
inherits no `REPL_DECLARATION_CODES` obligation**. That is one thing genuinely easier here.

**`assign: {}` and `allocation: null` correctly draw nothing** (probe rows 9–10) — `{}` is what
`reference.md` § The one config file shows `init` writing. `allocation: ''` fires, correctly,
because its guard is a membership test rather than truthiness. **No truthiness holes were found
among the three**, unlike H3-SCOPING's three for `holdout`/`measurements`/`weight_by`.

### The mutual block is real, and it is stated from three ends

- `validate.py`'s message for `groups`: it "is an axis over units rather than parameters, so it
  needs `data.units.allocation` and `data.units.assign`".
- `validate.py`'s message for `between`: "it needs a `sweep.groups` axis to say what the arms
  are, and group axes are not implemented either".
- § The one config file marks `assign` "REQUIRED when allocation is `between`".

Rows *Allocation needs arms* and *Arms need allocation* are the two halves written as two
checks. **Neither refusal can retire alone.** This survives measurement unchanged and is the
reason § 8's decomposition splits by *assignment method*, not by declaration.

### What each refusal currently masks

Retiring a refusal makes every latent defect behind it live. This has held three times.

**`E-SWEEP-GROUPS-UNSUPPORTED` masks eleven things.**

1. **`sweep.expand` ignores `groups` entirely.** Measured: `grid` of three levels gives 3
   conditions with or without a two-level `groups` axis beside it; `groups` alone gives **zero**.
   Can-fail control: the same call on `paired` and `sample` returns their products.
2. **The execution budget is computed from that undercount.** `validate.py`'s
   `executions = len(conditions) * repeat_total`. Demonstrated: at `max_executions: 15`, a
   2-level grid × 5 seeds = 10 draws no warning (correct), and the same config with a 2-level
   `groups` axis — 4 × 5 = 20, which the document says exceeds 15 — **also draws no warning**.
   Can-fail control: the identical pair at `max_executions: 5` warns on both, so
   `W-EXEC-BUDGET` is demonstrably reachable on this config shape. This is the exact analogue of
   H3b's *Leave-one-out is affordable* finding, and it makes row **Grid size sane** — implemented
   today — wrong under H3c.
3. **`E-SWEEP-EXPANDS-EMPTY` currently double-reports a `groups`-only design**, and stops doing
   so when `groups` expands. Any test pinning that pair goes stale.
4. **`resolve_condition_cfg` would invent a parameter.** See § 6 — this is the largest masked
   item and no scoping document has named it.
5. **`_swept_paths` does not collect a group axis**, so `resolve_wide_cfg` would not mark it —
   correctly, since there is no parameter to mark. But the split that makes both true is
   § 5's, and it does not exist yet.
6. **No swept-value legality check reaches a group level.** Probe row "group level containing a
   slash" (`levels: [a/b, c d]`) draws no `E-SWEEP-VALUE-UNNAMEABLE`. Can-fail control: the same
   value in a `grid` axis does. § Expansion modes renders levels straight into condition labels
   (`00_arm=control`), and a label is also a selector.
7. **`sweep.check_swept_value`'s docstring argument becomes false.** It exempts a `baseline`'s
   fixed values on the ground that "the only axes a baseline can leave free are `grid` and
   `paired`, both of which `_check_sweep` now checks". § Expansion modes says a baseline accepts
   group levels (`{arm: control}`) and expands over the axes it does not fix — so a free group
   axis puts *unchecked* values into a baseline's rendered cell. This is precisely the hole
   commit `884959a` closed for `paired`, reopened one mode over.
8. **`sweep.expand`'s docstring claim is false**: "§ Expansion modes' one interleaved example is
   `ablate × groups`, which no config can reach here … `groups` is not expanded in this build".
9. **`design_digest` covers `sweep.groups` already** (`hashes.py`), so adding an axis moves
   every fold boundary and repeat seed today — which is what § What `auto` derives from
   *prescribes*, but it is currently unobservable because no config can declare one.
10. **Row *Axis names are distinct* has nothing to check**: two axes both named `arm` is a shape
    only `groups` can make.
11. **`AXIS_MODES` serves three predicates from one tuple** — § 5.

**`E-DATA-ALLOCATION-UNSUPPORTED` masks six things.**

1. **`paired` is hard `True` in `cli.py`**, with the comment saying why: the unpaired case
   "needs a group axis or `allocation: between`, both refused". So every contrast this build
   publishes asserts pairing it did not check.
2. **No unpaired interval construction exists.** `grep -rn --include='*.py' 'unpaired_\|welch_'
   src/` returns **one hit, that same docstring line**. Can-fail control: `grep -c 't_over_units'
   src/publishable/stats.py` → 38, and `grep -rn '_clustered' src/` → 19 (H3b's, which is why
   H3-SCOPING's version of this grep is now stale and must not be re-cited).
3. **`confounded`/`differs_on` can only ever see parameter axes.** § Allocation's own example
   (`differs_on: [arm, analysis.method]`) is unreachable.
4. **Folds are drawn over the whole roster**, never within a cell — § 4.
5. **`resolved` is the whole roster per condition**, never an arm — § 9.
6. **No cell-population warning exists at all** — `limits.min_units_per_cell` is declared in
   `materialize.py` and typed in `envelope.py` and read by nothing. Can-fail control: the same
   grep for `max_executions` returns live reads in `validate.py`. (This is H3-SCOPING's
   "negative result", re-verified: still declared, still unread.)

**`E-DATA-ASSIGN-UNSUPPORTED` masks seven things.**

1. **`data.units.assign` is a bare `dict` leaf** — `envelope.py`: `"data.units.assign": dict`,
   with no `data.units.assign.*` entries. Demonstrated: a config with
   `assign: {arm: {methd: randm, raito: 3, seed: auto}}` draws **only** the refusal, no
   unknown-key finding. Confirmed directly against `envelope.check_envelope`:
   `{assign: {arm: {methd: randm}}}` returns `[]`, while the can-fail control `{clustr_by: site}`
   at the same level returns `E-CONFIG-KEY-UNKNOWN … did you mean 'cluster_by'?`. § Validation's whole-leaf paragraph says `.holdout` and `.assign`
   "inherit the same treatment when their slices land" — so H3c owes the closure **and** the
   edit to that paragraph.
2. **`assign.<axis>.from` is not reachable by `CONSTANT_COLUMN_RULES`**, and `units.py`'s own
   comment says so by name: "**A registry key must be a flat, string-valued key of
   `data.units`.** … `assign.<axis>.from` and `holdout.from` are the next two columns that will
   want this rule and **neither is reachable this way** — adding either name to the registry
   no-ops silently, and so does spelling it as a dotted path. Verified by probe, not assumed.
   Whichever slice needs one owes an accessor here." That accessor is H3c's.
3. **No `assign.<axis>.from` constancy row exists.** § Validation carries *Cluster is constant
   within a unit* and *Weight is constant within a unit*; `grep -n '^| ' docs/reference.md` over
   rows 216–310 returns no third. **A row to be written from nothing**, and its code
   (`E-DATA-ASSIGN-VARIES`, by the two-code precedent) does not exist:
   `grep -rn 'E-DATA-ASSIGN-VARIES' docs/reference.md src/` → nothing; control
   `E-DATA-WEIGHT-VARIES` → the
   registry entry, the `CONSTANT_COLUMN_RULES` entry and its § Weighted samples sentence.
4. **`design_digest` covers `assign.seed`**, which § What `auto` derives from says it must not:
   the digest is over "`data.units` (every field except `assign.seed` itself)". `hashes.py`
   json-dumps `data.units` wholesale. Latent today; live the moment `assign` is legal, and the
   damage is that pinning `assign.seed` to an integer would redraw every fold boundary and
   reseed every repeat.
5. **No `assign` seed construction exists.** `units._seed_from(digest)` is
   `sha256(digest + "|folds")[:4]`; § What `auto` derives from wants "digest + the axis name +
   the resolved roster". A third construction beside `_seed_from` and `order_seed_for`.
6. **`allocation.json` is not written by anything.** `grep -rn --include='*.py'
   'allocation.json\|allocation_hash' src/` → nothing. Control: `'sweep.yaml'` → 13 hits
   including the writer.
7. **`W-DATA-CLUSTER-UNDECLARED`'s `assign.from` exclusion is a check that cannot fail today.**
   `validate._accounted_attribute_names` reads `assign.<axis>` names and `assign.<axis>.from`
   and excludes them from the warning. Probe row "site column, assign reads site" shows the
   warning correctly absent — but the config is *already failing* on
   `E-DATA-ASSIGN-UNSUPPORTED`, so nothing about that exclusion is exercised by a passing
   design. H3c is where it becomes testable. (The `sweep.groups` half of the same exclusion is
   in the same position — probe row "site column, groups names site".)

## 2. The blocked § Validation rows, by title

### Anchoring the table

The main table is **95 rows**: header at line 214, separator 215, rows 216–310.
`awk 'NR>=216 && NR<=310 && /^\|/' docs/reference.md | wc -l` → 95. Can-fail controls:
`NR<=309` → 94; `NR<=340` → 97 (which over-counts, because a second table follows — hence the
explicit upper bound, verified by `awk 'NR>=214 && NR<=311' … | grep -vn '^|'` returning exactly
one line, the blank at 311).

H3-SCOPING measured 89, H3b measured 91, it is now **95**. H3b added four rows. **Every row
below is cited by title only** — three successive numberings are now stale, which is CLAUDE.md's
own rule arriving as a concrete failure for the third time.

### The corrected attribution

| Row title | H3-SCOPING said | Measured | Note |
|---|---|---|---|
| Ablation baseline isn't a group level | H3c (15) | **H3c owns** | The row H2 left open; `validate.py`'s `_check_unimplemented` docstring still calls it "the one § Validation row still open" |
| Allocation needs arms | H3c (15) | **H3c owns** | |
| Every axis is assigned | H3c (15) | **H3c owns** | |
| Every assignment names an axis | H3c (15) | **H3c owns** | |
| Axis names are distinct | H3c (15) | **H3c owns** | Purely `sweep.groups` |
| Stratification is forward-only | H3c (15) | **H3c owns** | Needs axis declaration order |
| Cells are populated | H3c (15) | **H3c owns** | Warning. **No identifier exists** |
| Arms need allocation | H3c (15) | **H3c owns** | Mirror of *Allocation needs arms* |
| Ratio names levels | H3c (15) | **H3c owns** | |
| Block size fills the arms | H3c (15) | **H3c owns** | `blocked` only |
| Attribute assignment resolves | H3c (15) | **H3c owns** | `by_attribute` only |
| Allocation is coherent | H3c (15) | **H3c owns** | Warning. **No identifier exists** |
| Allocation strata exist | H3c (15) | **H3c owns** | |
| Folds fit inside the cells | H3c (15) | **H3c owns** | Carries H3b's clause "or its cluster count when `cluster_by` is declared" |
| Contrast has units in common | H3c (15) | **H3c owns, and the row is under-specified** | See below |
| Stratification attribute exists | not listed | **shared three ways; H3b landed the `fold.` branch** | H3c owes `assign.<axis>.stratify_by`, H3d owes `holdout.stratify_by` |
| **Grid size sane** | **not listed** | **implemented, and H3c makes it wrong** | Demonstrated in § 1 |
| **Baseline leaves contrasts confounded** | **not listed** | **implemented, and H3c changes it** | See below |
| **(an `assign.<axis>.from` constancy row)** | **not listed** | **does not exist and must be written** | § 1, `ASSIGN` mask 3 |
| **(an `assign.<axis>.method` row)** | **not listed** | **does not exist and must be written** | See below |
| Swept values are nameable | not listed | **H3c must widen** | Group levels render into labels and are unchecked — § 1, `GROUPS` mask 6 |
| Sweep paths resolve / Swept values legal / Baseline is a valid condition | not listed | **H3c must exclude group axes from** | A group axis's `by` is not a parameter path and its levels are not `Param` values |

**So: 15 owned as charted, 1 shared, 2 already-implemented rows changed, 2 rows to write from
nothing, and 4 more rows to widen or narrow.** The count is right and it measures the wrong
thing — the same failure as H3a's and H3b's charters, arriving through a different door.

### The two rows already implemented that H3c makes wrong

**Grid size sane.** Demonstrated in § 1. `W-EXEC-BUDGET` is computed from
`len(sweep.expand(doc))`, and `expand` does not multiply by a group axis. This is not a check
that goes missing — it is a check that keeps passing and reports a number several times too
small, which is worse. Both the run's budget and `dry-run`'s printed expansion follow it.

**Baseline leaves contrasts confounded.** `W-SWEEP-BASELINE-CONFOUNDED` exists and fires today
over parameter axes. **The row's own example is `arm: control`** — a group axis — and § Allocation's
pairing table makes a group axis crossed with a parameter axis the canonical confounded case. So
the check's inputs change (group axes join the axis set it counts) and its example becomes
reachable for the first time. A test asserting it fires on a two-parameter-axis baseline passes
under both the old and the new predicate; the discriminating form is a baseline fixing one
parameter axis **and** one group axis.

### The row that is under-specified

**Contrast has units in common** — "compares two conditions whose completed units don't
intersect". `completed` is a run-time fact, not a validate-time one, and § Validation is
`validate`'s table. Under `between` the disjointness is knowable at validate time only from the
assignment, which is drawn at run start. H3c must decide whether this row is a validate-time
check over the *declared* axes (two conditions differing on a group axis have no units in
common by construction, which makes it a tautology rather than a check) or a run-time refusal
over the realized `allocation.json`. **The document does not say, and it must before code is
written.** No code exists: `grep -rn 'CONTRAST-DISJOINT\|units in common' src/` → nothing;
control `E-STATS-CONTRAST-UNKNOWN` → eight sites in `validate.py`.

### The second row that must be written from nothing

**Nothing checks `assign.<axis>.method` itself.** `awk 'NR>=216 && NR<=310 && /^\|/'
docs/reference.md | grep -i 'method\|assign'` returns thirteen rows: *Attribute assignment
resolves* checks `by_attribute`'s column, *Ratio names levels* and *Block size fills the arms*
check the other two methods' fields, and *Holdout is resolvable* does the per-method work one
block over — but **no row requires `method` to be present, or to be one of
`random | by_attribute | blocked`**. Can-fail control: the same grep finds
*Sample is drawable*, which does exactly that job for `sweep.sample.method`, and *Choices*,
which does it for a template parameter — so the shape of the missing row exists twice in the
same table.

It matters after the whole-leaf closure, not before: today `assign: {arm: {stratify_by: [site]}}`
and `assign: {arm: {method: randmo}}` are both truthy and both draw the blanket refusal. Once
`method` is typed `str` by the closure, neither shape has a choices check unless this row is
written. It lands in H3c-1 beside the constancy row.

### The two `W-` identifiers that do not exist

`grep -rn 'W-DATA-CELL\|W-DATA-ALLOC\|W-ALLOC\|W-SWEEP-CELL\|CELLS-\|ALLOCATION-INCOHERENT'
docs/*.md src/publishable/*.py` returns **nothing** (exit 1). Can-fail control:
`W-DATA-CLUSTER-UNDECLARED` returns its § Warnings row, two § Clustered units / § Weighted
samples cross-references, and two `validate.py` sites.

*Cells are populated* and *Allocation is coherent* are both warnings, both cite
`limits.min_units_per_cell`, and neither has a name. They are **not obviously two identifiers**:
one is "a crossed `groups × groups` cell is thin", the other is "a `between` arm is thin", and
under one axis they are the same sentence. H3c must decide — one code used twice, or two — and
say so in § Warnings core reports **before** any code is written, exactly as H3a and H3b did.
That decision belongs in task 1 either way.

### The `NOT BUILT` register

`reference.md` § The one config file currently says "**Seven** declarations above are not yet
built", naming `sweep.groups`; `data.units.assign` and `.holdout`, the `{resolver: <name>}` form
of `data.units.from`, and any `data.units.allocation` other than `within`; and
`statistics.resample` and `.null_test`. Counting a non-`within` `allocation` as one and `assign`
as one, **H3c takes seven to four**. That paragraph is also where the whole-leaf sentence
(`.holdout` and `.assign` "inherit the same treatment when their slices land") lives, so one
edit serves both.

## 3. `partition_units`' second rewrite — it is not one

### What the docstring already promises

`partition_units(roster, k, digest, clusters=None, strata=None) -> list[list[Unit]]` states its
contract explicitly, and three parts of it decide H3c's work:

- **The order is part of the contract**: clusters shuffled with the digest-seeded RNG, then
  sorted **largest first**, each going to the currently-smallest fold. `list.sort` is stable, so
  the shuffle survives inside each size.
- **What it does not promise**: "Sizes differ by at most one when `clusters` is `None`. When it
  is not, they are as even as indivisible clusters allow … Saying the stronger thing here would
  be claiming a guarantee the code does not provide." And under `strata`, "fold sizes can differ
  by more than one", with a worked bound.
- **A stated defect it declines to fix**: "`k` is checked against the whole roster's basis, not
  against each stratum's, and a fold can therefore come out EMPTY". Six units as three plus
  three under `{k: all, stratify_by: label}` fills folds 0–2 and leaves 3–5 empty.

### What "drawn within each cell" adds, and where it attaches

§ A fixed holdout split and § Between-subjects factorial both say the same thing: "folds and
holdouts are drawn *within* each cell". § Validation's *Folds fit inside the cells* bounds `k`
by "the smallest cell's unit count, or its cluster count when `cluster_by` is declared".

**A cell is not a third parameter to `partition_units`.** Assignment happens first, once per
run; the cells are then disjoint sub-rosters, and the partition is drawn per cell and merged
index-wise — which is *exactly* the shape the per-stratum branch already has. Measured on the
uneven fixture (15 units; clusters S1×7, S2×3, S3×3, S4×1, S5×1; arms 8/7):

| Call | Result |
|---|---|
| `fold_basis(roster, None)` | 15 |
| `fold_basis(roster, "site")` | 5 |
| `partition_units(roster, 5, d, clusters=cl)` sizes | `[7, 3, 3, 1, 1]` — no empty fold |
| `partition_units(control_arm, 5, d, clusters=cl_control)` sizes | `[7, 1, 0, 0, 0]` — **three empty folds** |
| `partition_units(treatment_arm, 5, d, clusters=cl_treat)` sizes | `[3, 2, 1, 1, 0]` — **one empty fold** |

Can-fail control: the whole-roster row above produces no empty fold on the same fixture and the
same `k`, so "cells produce empty folds" is an observation about cells, not a tautology about
the fixture. The `control` cell holds **2** clusters where the whole roster holds 5 — which is
the entire content of *Folds fit inside the cells*, and a `k: 5` passes `_fold_k` today because
`fold_basis` is computed over the whole roster.

**So the change is:**

| Name | Change |
|---|---|
| `units.fold_basis(roster, cluster_by)` | Gains the cell partition. Its docstring's "**One number, not two**" argument survives intact — the basis becomes the **minimum over cells** of (cell unit count, or cell cluster count) — but it is a signature change on the single derivation every caller shares |
| `units.partition_units` | **Signature unchanged if cells are looped outside it.** The caller partitions each cell and merges index-wise, as the `strata` branch already does internally. The alternative — a `cells=` parameter mirroring `strata=` — is the same code one level in, and is the better home only if the empty-fold interaction below is to be checked there |
| `units._assign_whole_clusters` | **Unchanged.** This is the part the charter calls "rewrites `partition_units` again" and it is wrong: the greedy largest-first assignment is per-list already |
| `units._seed_from` | Unchanged for folds. A **new sibling** for `assign` (digest + axis name + roster) and, in H3d, for `holdout` |
| `replication._fold_k` | `fold_basis` argument becomes the per-cell minimum; the `E-REPL-FOLD-K-TOO-LARGE` message gains a cell clause beside its cluster clause |
| `replication.resolve_repeats` | Its `fold_basis` parameter is still the only channel roster facts reach it by, on **both** arrival paths (`validate._check_units` at `validate.py:473` and `cli` at `cli.py:808`) |
| `cli` `_run`-side | Where the arms are drawn, where `allocation.json` is written, where `partition_units` is called per cell, and where `fold_members_for` is built. The only `partition_units` call site in `src/` — `grep -rn --include='*.py' 'partition_units' src/` returns the definition, one `cli` call, and one `sweep.py` docstring mention |
| `runner.attrition` / `runner._counts` | Where `resolved` becomes the arm rather than the roster — § 9 |
| `contrasts` / `cli._vs_baseline_block` | Where `paired` stops being hard `True` |

**The bit-stability pin H3b used still applies and must be re-pinned before the change.**
`partition_units(roster, 3, "digest-abc")` over the fixture returns first fold
`['u02', 'u06', 'u07', 'u05', 'u09']`. Any cell loop must leave the no-cell path byte-identical.

**One property to state, because it compounds multiplicatively.** The docstring's empty-fold
admission is per stratum. With cells it is per cell **and** per stratum: a design with `c` cells
and `s` strata has `c × s` independent lists each filling only as many folds as it has clusters.
The `[7, 1, 0, 0, 0]` row above is that with `s = 1`. This is a real defect in a combination no
task owns — § 9.

**Draw order is threaded, not per-call.** One `random.Random(_seed_from(digest))` is created and
passed into each per-stratum `_assign_whole_clusters`, so each call consumes from the same
stream and its draw depends on how many calls preceded it. If cells loop the same way, adding a
cell shifts every later cell's fold boundaries. That is why "read rather than re-drawn on
resume" is load-bearing rather than a nicety, and it is an argument for `allocation.json`
recording the realized partition rather than only the seed.

## 4. `allocation.json` and `provenance.allocation_hash`

### What the documents specify

| Property | Where | What it says |
|---|---|---|
| Contents | § `allocation.json` — who went where | `seed` (per axis), `arms` (axis → level → unit keys), `holdout` (`train`/`test`), `strata` (axis → attribute list) |
| When present | same | "Present only when an arm assignment **or** a holdout is declared … Both are partitions of one roster drawn once, so they share a file" |
| Keys | same | "**Unit keys, never row numbers** — a roster that gains a unit renumbers rows and would silently repoint every membership claim" |
| Covered by | same, and § Allocation | `provenance.allocation_hash`, "beside the path" |
| Write discipline | § The other files a run writes | In `sweep.yaml`'s class: "settled before the first execution and never touched again" |
| Resume | § `allocation.json`, § Allocation | "**read rather than re-drawn** on resume", and "a copy edited afterwards no longer matches its hash" |
| Citation advice | § What `auto` derives from | "pin `assign.seed` to an integer and keep `allocation.json` — a recorded assignment is a fact about what happened, and it should not be re-derivable to a different answer" |

### What exists to follow rather than reinvent

- **`sweep.yaml` is the pattern, exactly.** `cli.command_run` writes it inside the `RunLock`,
  after `manifest/input.json`, before `execute_plan`, with a comment quoting the same "settled
  before the first execution" sentence and giving the reason it moved there (a run that died
  inside the loop left no plan on disk). `allocation.json` is a second file at the same point,
  and `sweep.document`'s "the `sweep.yaml` payload … as plain YAML-safe data" is the shape to
  copy — a pure function returning plain data, tested without a filesystem.
- **`provenance` is a plain dict built in `cli.command_run`**, carrying `input_manifest` (a
  path) beside `input_manifest_hash`, and `units` beside `units_hash`. `allocation` /
  `allocation_hash` is the third pair, in the same literal, and `hashes._prefixed` /
  `_canonical` are the existing hash construction.
- **`units_hash` is the closest precedent for the hash itself** — JSON over the roster in
  resolved order, with a docstring stating why order is covered ("two runs that resolved the
  same units in a different sequence did not allocate the same trial"). `allocation_hash` should
  cover **the whole file**, so H3d adding the `holdout` key needs no new hash and no new
  provenance field.

### Two things the charter does not say

1. **There is no `resume` command.** `cli.OPERATION_COMMANDS` is `{"validate", "run"}`, and
   `_dispatch` recognises `validate`, `run`, `new`, `generate`/`g`/`init` and nothing else.
   Can-fail control: `uv run publishable --help` prints "unknown command `--help`", and
   `grep -rn --include='*.py' 'def command_resume\|"resume"' src/` returns nothing while
   `def command_run` returns one. So the "read rather than re-drawn" rule has **no reader to
   write against**. H3c's obligation is to write the file so that a later `resume` *can* read it
   — which means the file must be sufficient on its own, not a seed plus a re-derivation — and
   to say so in the artifact's docstring. Claiming the resume contract is implemented would be
   the charter's error repeated.
2. **§ What `study add` redacts does not name `allocation.json`**, and it is the one run artifact
   that is a list of unit identities. `grep -n 'allocation' docs/reference.md` inside that
   section returns nothing; control, the same grep for `input_manifest` returns its redaction
   row. Whether the file is redacted, dropped, or kept is a document decision H3c owes, and
   `study` being unbuilt is not a reason to defer it — the redaction table is normative now.

## 5. `sweep.groups`, and the `AXIS_MODES` split

### H2's reasoning holds

H2 deferred `groups` on the ground that "a `groups` axis that expanded conditions while handing
each the same roster would run to completion and report two identical measurements as two arms."
**Confirmed, and it is stronger than H2 could state.** `cli.command_run` resolves the roster and
computes `partitions` **before** `conditions = expand(doc)`, and `runner.execute_plan` narrows a
`UnitList` only by fold membership (`runner.py:478-480`, the single `UnitList(` construction with
a `train=`). There is no per-condition roster channel at all. A `groups` axis that expanded today
would give every arm the identical `io.units`, and the two conditions would also share a
`parameters_hash` — which § Expansion modes says is *correct* for real arms, and which would here
be a run reporting two identical numbers as a trial result.

### The tuple serves three predicates, not two

`sweep.py`:

```python
AXIS_MODES = ("grid", "paired", "sample")
NON_AXIS_MODES = ("baseline", "ablate", "groups")
SWEEP_MODES = AXIS_MODES + NON_AXIS_MODES
```

The `AXIS_MODES` docstring names three call sites for one tuple: `_axes` builds the condition
product from exactly these; `_swept_paths` collects their paths; `validate`'s
`E-SWEEP-ABLATE-CROSSED` refuses `ablate` composed with any of them (via
`axis_modes_present`). Those are **three different predicates**:

| Predicate | `grid`/`paired`/`sample` | `groups` |
|---|---|---|
| (a) contributes to the condition product | yes | **yes** (§ Expansion modes: "the product of every axis-shaped mode present — `grid`, `paired`, `sample`, `groups`") |
| (b) sweeps a parameter path | yes | **no** — a level is a set of units |
| (c) `ablate` may not cross it | yes | **no** — § Expansion modes permits `ablate × groups` explicitly |

Today `groups` is `false` on all three and both readings are consistent. **They cannot both stay
correct once `groups` expands**, and this is H3c's alone: no later slice touches `sweep.py`.

**The split**: `PRODUCT_MODES = ("grid", "paired", "sample", "groups")` for `_axes`, and
`PARAMETER_AXIS_MODES = ("grid", "paired", "sample")` for `_swept_paths` and
`axis_modes_present`. `SWEEP_MODES` must stay **derived**, because the module docstring's whole
argument is that `E-SWEEP-KEY-UNKNOWN` is the vocabulary choke point and a seventh mode "cannot
be used at all until it appears here — and it can only appear here by being put in `AXIS_MODES`
or `NON_AXIS_MODES`". Both docstrings and `NON_AXIS_MODES`' per-mode justification are rewritten
with the split.

**This is also a check that cannot fail.** A test asserting `ablate × grid` is refused passes
under both the correct and the incorrect predicate. The discriminating form asserts, in one
test, that `ablate × grid` is refused **and** `ablate × groups` is not. `tests/test_validate.py`
already carries the second half — a test asserting the `ablate + groups + baseline` config's
findings are exactly `{"E-SWEEP-GROUPS-UNSUPPORTED"}` — and that assertion breaks the day the
refusal retires, so it is a test edit, not only a code edit.

### Two more things `groups` needs that no scoping document has named

**The condition product is typed for parameter paths.** `_axes` returns
`list[list[dict[str, Any]]]` whose cells are `{dotted.path: value}`, and
`runner.resolve_condition_cfg` writes **every** key of `Condition.values` into `parameters`.
Demonstrated:

```
resolve_condition_cfg({"parameters": {"analysis": {"method": "pearson"}}},
                      {"arm": "control", "analysis.method": "spearman"})
  raw parameters = {'analysis': {'method': 'spearman'}, 'arm': 'control'}
```

`parameters.arm` is a parameter no template declares. Can-fail control: the same call without
the `arm` key leaves `parameters` holding `analysis` alone. So `Condition.values` must carry a
**second kind of entry**, or a group axis's cell must be kept out of the overlay — and every
consumer of `values` is affected: `resolve_condition_cfg`, `resolve_wide_cfg` (which must *not*
mark a group axis as a swept parameter path), `sweep.label_for`, `sweep.sweep_document`,
`cli._differing_axes` (which *must* see it, for `differs_on`), and `validate`'s
*Sweep paths resolve* / *Swept values legal* / *Baseline is a valid condition* rows, all of which
resolve a path against the template's `parameter_spec`. **This is the largest single item in
H3c and the charter does not mention it.**

**`_baseline_cells` needs no change.** Its docstring's "an axis counts as fixed when the
baseline names *any* path it varies" reads fixedness off the cells' paths rather than off the
mode, and a group axis's cell has exactly one path. Its "only `paired` reaches it from a
baseline today" paragraph is about `sample` and stays true. That is one of the few places
`groups` joins for free, and it is worth recording so it is not "fixed".

## 6. What `src/` has today

Functions, not files. Only the ones a cell, an arm, or an assignment touches.

| Function / class | State | Where an arm or a cell attaches |
|---|---|---|
| `units.Unit` | Frozen, hashable by `key`; `__getattr__` promotes an attribute | **Nothing.** `assign.from` and `assign.stratify_by` name attributes, which `Unit` already carries |
| `units.UnitList` | Iterate, `len`, integer index, `.train` | Nothing structural — an arm is a `UnitList` narrowed at construction, exactly as a fold is |
| `units.resolve_units` | Returns `(UnitList, technical_n, columns)`; collapses `measurements` before the uniqueness loop | Where an `assign.<axis>.from` column's existence is checkable, and where the missing constancy row lands |
| `units.collapse_measurements` / `CONSTANT_COLUMN_RULES` | Keyed by *declaration*, reaching **flat string-valued keys of `data.units` only** | **The accessor H3c owes.** The comment names `assign.<axis>.from` explicitly and says adding the name to the registry "no-ops silently" |
| `units.clusters_of` / `cluster_count_of` / `cluster_count` | H3b's single authority for cluster membership | Read by the arm draw: § Clustered units requires whole clusters on one side of a **core-drawn** assignment |
| `units.fold_basis` | `cluster_count(roster, cluster_by) if cluster_by else len(roster)` — "**One number, not two**" | **Signature change.** Becomes the minimum over cells. The one-number argument is what makes this the right place rather than `_fold_k` |
| `units.stratum_varies_within_cluster` | Returns the offending cluster and its values, so the caller picks the code | **Reused as-is** for `assign.<axis>.stratify_by`, under H3c's own code. Its docstring already anticipates this ("the caller decides which declaration to name") |
| `units.partition_units` | Clusters + strata, digest-seeded, largest-first to the emptiest fold, per-stratum merge index-wise | Cells loop outside it, or become a third grouping inside it — § 3 |
| `units._seed_from` | `sha256(digest + "\|folds")[:4]` | Unchanged; a sibling for `assign` |
| `replication._fold_k` | Refuses `k < 2`, `k > fold_basis`, with a cluster-specific message | The cell clause joins the message; `stratify_by` is no longer refused here (H3b) |
| `replication.resolve_repeats` | `fold_basis` is the only channel roster facts reach it by, on two callers | Unchanged shape, different number |
| `sweep.AXIS_MODES` / `NON_AXIS_MODES` / `SWEEP_MODES` | One tuple, three predicates | **The split** — § 5 |
| `sweep._axes` / `_swept_paths` / `axis_modes_present` | Parameter-path-shaped throughout | `_axes` gains `groups`; the other two must not |
| `sweep.Condition` / `expand` | `values` is a flat `{path: value}` mapping, frozen into a `MappingProxyType` | **Must distinguish a group-axis entry from a parameter path** — § 5 |
| `sweep.check_swept_value` | `E-SWEEP-VALUE-UNNAMEABLE` over `grid`, `paired`, `ablate.override` | Group levels join; the docstring's baseline-exemption argument is rewritten |
| `sweep.sweep_document` | Writes `conditions[].values`, `repeats`, `partitions`, `execution_order` | `partitions` becomes per-cell; realized fold sizes already recorded |
| `runner.resolve_condition_cfg` | Writes every `values` key into `parameters` | **The phantom-parameter site**, demonstrated |
| `runner.resolve_wide_cfg` | Marks every swept path `SweptAway` | Must not mark a group axis |
| `runner.execute_plan` | The one `UnitList(units, train=…)` construction, narrowed by fold membership only | **Where the arm narrows `io.units`** |
| `runner.attrition` / `_counts` | `{resolved, completed, ineligible, failed}` (+`effective`, +`clusters`) | `resolved` becomes the arm — § 9 |
| `contrasts.resolve_contrasts` / `cli._vs_baseline_block` | `paired` hard `True`, with the comment saying why | Where pairing becomes derived per contrast |
| `stats` | `t_over_units`, `paired_t_over_units`, percentile forms, `weighted_*`, `*_clustered` | **No `unpaired_*` or `welch_*` construction exists** |
| `validate._accounted_attribute_names` | Already reads `sweep.groups[].by` and `assign.<axis>.from` | Written for H3c, unreachable until H3c |
| `hashes.design_digest` | `data.units` **wholesale** + `sweep.groups` | Must exclude `assign.seed` |
| `envelope.LEAF_TYPES` | `"data.units.assign": dict`, no inner keys | **The whole-leaf closure**: six inner keys per axis (`method`, `from`, `stratify_by`, `ratio`, `block_size`, `seed`), under an axis name the schema cannot enumerate — which is why this closure is harder than `measurements`' two |
| `materialize.py` | Writes `allocation: within  # within  (between: later slice)`; writes **no** `assign` key; writes `min_units_per_cell` | Comment edit, plus `assign: {}` joining `init`'s output per § The one config file |

## 7. Ordering and dependencies

### Which of H4's dependencies H3c genuinely unblocks

H3-SCOPING listed four H4 dependencies. H3b's re-measurement showed two of them
(*Shuffle level is unambiguous*, *Clusters enough to resample*) are double-blocked by
`E-STATS-NULLTEST-UNSUPPORTED` and `E-STATS-RESAMPLE-UNSUPPORTED`, both H4's own. Re-verified at
`cb96c7d`: both codes are still present in `validate.py`. Unchanged by H3c.

| H4 dependency | Blocked by | After H3c |
|---|---|---|
| The `welch_*` / `unpaired_*` interval family | `E-SWEEP-GROUPS-UNSUPPORTED` **+** `E-DATA-ALLOCATION-UNSUPPORTED` — **and nothing else** | **Fully discharged.** This is the one H4 dependency H3c genuinely unblocks, and it is discharged completely rather than halved |
| Shuffle level is unambiguous | `CLUSTER` (retired by H3b) + `NULLTEST` (H4's own) | Unchanged |
| Clusters enough to resample | `CLUSTER` (retired by H3b) + `RESAMPLE` (H4's own) | Unchanged |
| Weighted intervals + `effective` | discharged by H3a | — |

So: **one dependency, discharged outright.** H3-SCOPING's "H4 can begin after H3b + H3c" is
correct, and the reason is this row alone. Note the honest form: H3c makes the unpaired case
*reachable*; whether the `welch_*`/`unpaired_*` constructions ship inside H3c or inside H4 is
§ 8's question, and the `E-DATA-WEIGHT-CONTRAST` / `E-DATA-CLUSTER-CONTRAST` precedent means
H3c may refuse the combination instead.

### What H3d needs stated in a particular form

Two things, each costing H3c nothing if honoured up front and a rewrite otherwise:

1. **The cell rule must be "partition within each cell to declared target proportions"**, not
   "draw `k` folds within each cell". H3b did H3d the same favour for clusters; H3d is
   `k = 2` at `(1 − frac, frac)`, and § A fixed holdout split states its cell behaviour as a
   consequence of H3c's rule ("Folds are drawn the same way, for the same reason").
2. **`provenance.allocation_hash` must cover the whole file**, so H3d adding the `holdout` key
   needs no new hash and no new provenance field. § `allocation.json` says so — "One file and
   one hash cover both" — and the shape to avoid is a per-section hash.

H3d also inherits H3c's whole-leaf closure *pattern* (`data.units.holdout` is the same `dict`
leaf), the `assign.<axis>.from` constancy accessor (`holdout.from` is the second column the
`CONSTANT_COLUMN_RULES` comment names), and the `stratify_by` branch of
*Stratification attribute exists*.

### Does anything here depend on H7

**No.** `assign.method: by_attribute` reads a **unit attribute**, not a registered artifact —
§ Allocation: "It names the column instead of a seed", and `from` defaults to the axis name. The
only H7 surface anywhere near `data.units` is `from: {resolver: …}`
(`E-DATA-RESOLVER-UNSUPPORTED`), which H3-SCOPING already recommended moving to H7 and which
H3c does not touch. Control: `grep -rn --include='*.py' 'register_\|entry_point' src/` returns
**nothing at all** — the four plugin registries are unbuilt, and no `assign` path could reach
one.

### What H3c does *not* unlock in `experimental-designs.md`

| Design | Needs | After H3c |
|---|---|---|
| § Between-subjects / parallel-arm trial | `groups` + `between` + `assign` (both methods shown) | **Unlocked outright** — the argument that this slice ships something a user can run |
| § Between-subjects factorial | Two `groups` axes, `by_attribute` + `random` with forward stratification | **Unlocked outright** |
| § Matched case-control | `groups` + `by_attribute` + **`cluster_by`** | **Half unlocked, and the half it exists for is not.** Its config as written declares neither a `baseline` nor `statistics.contrasts`, and `resolve_contrasts` emits a comparison only against a *declared* baseline — so it validates clean and runs, reporting each arm's own `match_set`-clustered interval. The moment a baseline designates `control`, `E-DATA-CLUSTER-CONTRAST` fires (guard: `comparisons > 0` and a truthy `cluster_by`, read directly), and the case-vs-control contrast the design exists for is refused until H4. Worth stating precisely: § Clustered units spends two paragraphs on this design and a reader will assume H3c delivers the contrast |
| § Train-test holdout | `holdout` | H3d |
| § Cross-validation | its clustered half landed with H3b | H3c adds only the cell bound |

## 8. One slice or several

### Verdict: three slices

H1 was 12 tasks, H2 was 9, H3a was 12, H3b was 13 (`grep -c '^## Task'` over each plan in
`docs/superpowers/plans/`; H3b grew from 12 mid-flight, twice). H3c as chartered is materially
larger than any of them, and larger than H3a and H3b combined on most measures.

| Measure | H3a | H3b | H3c as chartered | H3c as measured |
|---|---|---|---|---|
| Refusals to retire | 2 | 2 | 3 | **3** |
| § Validation rows owned outright | 4 | 3 | 15 | **15** |
| Rows already implemented that the slice breaks | 0 | 1 | 0 stated | **2** |
| Rows to write from nothing | 0 | 2 | 0 stated | **2** |
| Rows to widen or narrow | 0 | 0 | 0 stated | **4** |
| Rows shared with a later slice | 0 | 1 | 0 stated | **1** |
| `W-` identifiers to mint first | 1 | 1 | 0 stated | **1 or 2** (an open decision) |
| Whole-leaf closures | 1 (`measurements`, 2 inner keys) | 0 | 0 stated | **1** (`assign`, 6 inner keys under an unenumerable axis name) |
| New run artifacts | 0 | 0 | 1 | **1** (`allocation.json`) + a provenance hash + a `study add` redaction row |
| New interval constructions | 1 | 2 | 0 stated | **0 to 4** (the `unpaired_*`/`welch_*` family, deferrable — see below) |
| New seed derivations | 0 | 0 | 0 stated | **1** (`assign.seed`) |
| Digest changes | 0 | 0 | 0 stated | **1** (exclude `assign.seed`) |
| Designs unlocked outright | 0 | 1 | implied 3 | **2**, + half of matched case-control |
| Core function signatures changed | 4 | ≥5 | 1 stated | **≥8** |
| `sweep.py` module-level constants restructured | 0 | 0 | 1 stated | **1**, plus `Condition.values`' shape |
| Plan tasks | 12 | 13 | implied ~15 | **36**, enumerated below |

### The discriminator, and it holds

**`method: by_attribute` alone produces a runnable, recordable design.** It reads an existing
column; it draws nothing; it needs no `seed`, no `ratio`, no `block_size`, no forward-only
stratification, no permuted blocks, and no cluster-indivisibility rule (§ Clustered units says
explicitly that "with `method: by_attribute` the arm is read rather than drawn, and a cluster
may span both arms"). It writes `arms` membership into `allocation.json` and nothing else. Both
of `experimental-designs.md`'s unlocked designs have a `by_attribute` form, and § Between-subjects
factorial's *first* table row is "Both factors already in the data — two `by_attribute` axes;
core assigns nothing."

The split is legal only if this repo has precedent for refusing a **value inside a supported
block** rather than the block. It does, twice over: `E-DATA-WEIGHT-CONTRAST` and
`E-DATA-CLUSTER-CONTRAST` refuse combinations from `_check_sweep` while the declaration itself
is honoured, and the refusal loop's own comment states the discharge test — a declaration leaves
the loop when "the declaration changes the record". A `by_attribute`-only `assign` changes the
record completely: different `io.units` per condition, different `resolved`, an
`allocation.json`, an `allocation_hash`, an unpaired contrast. `random` and `blocked` are then
refused **as method values**, under one code, with a message deferring to the next slice —
exactly the shape every other refusal in this repo takes.

### Proposed decomposition

| # | Slice | Retires | Owns |
|---|---|---|---|
| **H3c-1** | **Arms read** — `sweep.groups`, `allocation: between`, `assign.method: by_attribute` | all three `-UNSUPPORTED` codes; `random`/`blocked` refused as method values under a new `E-DATA-ASSIGN-METHOD-UNSUPPORTED` | The `AXIS_MODES` split; `Condition.values`' two kinds; the `assign` whole-leaf closure; `allocation.json` + `allocation_hash`; the `design_digest` exclusion; per-condition `io.units`; `resolved` as the arm; unpaired reachability; the budget fix; the group-level nameability check; rows *Ablation baseline isn't a group level*, *Allocation needs arms*, *Arms need allocation*, *Every axis is assigned*, *Every assignment names an axis*, *Axis names are distinct*, *Attribute assignment resolves*, *Cells are populated*, *Allocation is coherent*, *Contrast has units in common*, the `assign.from` constancy row, and the fixes to *Grid size sane* and *Baseline leaves contrasts confounded* |
| **H3c-2** | **Arms drawn** — `assign.method: random \| blocked` | `E-DATA-ASSIGN-METHOD-UNSUPPORTED` | `assign.seed` derivation; `ratio`; `block_size: auto` and its multiple rule; `stratify_by` including forward-only over an earlier axis; whole clusters to one side of a core-drawn assignment; rows *Ratio names levels*, *Block size fills the arms*, *Stratification is forward-only*, *Allocation strata exist*, and the `assign.` branch of *Stratification attribute exists* |
| **H3c-3** | **Folds within cells** | nothing (no refusal left) | `fold_basis` as the per-cell minimum; the cell loop in `partition_units`' caller; the empty-fold interaction; row *Folds fit inside the cells*; the target-proportions contract H3d reuses |

**Recommended order: H3c-1 → H3c-2 → H3c-3.**

The reason is that H3c-1 is the only one of the three whose *absence* makes the others
unwritable, and the only one that must retire all three refusals at once (the mutual block
forces it). H3c-2 is pure addition behind a method-value refusal, touching no shape H3c-1
settled. H3c-3 is last because `fold_basis` cannot be a per-cell minimum until cells exist, and
because H3d consumes its contract rather than the reverse — the same argument H3-SCOPING made
for putting H3b before H3c, applied one level down.

**If H3c-3 is folded into H3c-1** the slice grows by ~4 tasks and gains a dependency on the cell
partition before `by_attribute` has produced one, so the fold work would be written against a
cell structure with only one method to test it. Keeping it separate is cheap; merging it is not.

### The task enumeration the 36 comes from

Not scaled from a ratio — listed, one line per deliverable, at the grain H3a's 12 and H3b's 13
were written at. Where a line names several § Validation rows it is because they share one check
site and one fixture.

**H3c-1, arms read — 20.** 1 documents-first (two `W-` identifiers or one, the
`assign.<axis>.from` constancy row and its `E-DATA-ASSIGN-VARIES` entry, the
`assign.<axis>.method` row, *Contrast has units in common*'s surface, `allocation.json` in
§ What `study add` redacts, the `NOT BUILT` register and its whole-leaf sentence, both
consistency passes) · 2 the `AXIS_MODES` split with its three docstrings · 3 `Condition.values`'
two kinds and `_axes` gaining `groups` · 4 the seven `values` consumers · 5 group-level
nameability plus narrowing *Sweep paths resolve* / *Swept values legal* / *Baseline is a valid
condition* off group axes · 6 the budget fix and *Grid size sane*, plus the
`E-SWEEP-EXPANDS-EMPTY` test edit · 7 the `assign` whole-leaf closure · 8 `design_digest`
excluding `assign.seed` · 9 the `CONSTANT_COLUMN_RULES` accessor and the constancy check · 10
`by_attribute` membership as one authority · 11 `allocation_document` as a pure function · 12 its
writer plus `provenance.allocation`/`allocation_hash` · 13 the arm reaching `runner`'s
`UnitList` · 14 `resolved` as the arm, with the partition assertion and `max_failed_fraction` ·
15 pairing derived per contrast, and the unpaired contrast built or refused · 16
*Baseline leaves contrasts confounded* over group axes · 17 the five declaration rows
(*Allocation needs arms*, *Arms need allocation*, *Every axis is assigned*,
*Every assignment names an axis*, *Axis names are distinct*) · 18 the `assign.method` row and
*Attribute assignment resolves* · 19 *Cells are populated* / *Allocation is coherent* against
`limits.min_units_per_cell` · 20 *Ablation baseline isn't a group level*, the three retirements,
the register seven → four, and `materialize.py`.

**H3c-2, arms drawn — 10.** 1 documents pass · 2 the `assign.seed` derivation · 3 `random`
honouring `ratio` · 4 whole clusters to one side of a core-drawn assignment · 5 `blocked`,
`block_size: auto`, the multiple rule · 6 `stratify_by` in the draw · 7 forward-only
stratification over an earlier axis · 8 rows *Ratio names levels* and *Block size fills the
arms* · 9 rows *Stratification is forward-only*, *Allocation strata exist*, and the `assign.`
branch of *Stratification attribute exists* (reusing `stratum_varies_within_cluster`) · 10
`allocation.json` gains `seed` and `strata`; retire `E-DATA-ASSIGN-METHOD-UNSUPPORTED`.

**H3c-3, folds within cells — 6.** 1 `fold_basis` as the per-cell minimum on both arrival
paths · 2 `_fold_k`'s cell clause · 3 the cell loop at the `partition_units` call site with the
bit-stability regression · 4 row *Folds fit inside the cells* · 5 `sweep.yaml`'s `partitions`
per cell · 6 the target-proportions contract H3d reuses.

**20 + 10 + 6 = 36**, against H3a's 12 and H3b's 13. Every line is a deliverable named earlier in
this document; none is a slice minted to hold a ledger entry.

**H3c-1 alone is 20 tasks** — larger than any slice this project has run — and if it must be
split again, the seam is the `sweep.py` half (the `AXIS_MODES` split, `Condition.values`,
`expand`, the budget, group-level nameability) against the `data.units` half (the whole-leaf
closure, `allocation.json`, per-condition `io.units`, `resolved`). They meet at exactly one
place — the arm's membership reaching `runner` — and that is a narrower seam than it sounds.

**The `unpaired_*` family is deferrable**, on the `E-DATA-WEIGHT-CONTRAST` precedent: H3c-1 may
refuse an unpaired contrast under a new code and let H4 lift it, shipping arms whose *own*
values and intervals are correct. That is the single largest sizing decision in the slice and
the plan must state which way it went — shipping it inside H3c-1 adds ≈4 tasks
(`welch_t_over_units`, `unpaired_percentile_over_units`, `n_paired`'s absence, and the wiring),
and *not* shipping it means H3c discharges H4's dependency by making it reachable rather than by
building it.

## 9. Traps, each with where it applies

### Checks that could not fail

| Vulnerable test | Why it can't fail | The discriminating form |
|---|---|---|
| `ablate` composition | `ablate × grid` is refused under both the correct and the incorrect `AXIS_MODES` predicate | Assert `ablate × grid` refused **and** `ablate × groups` legal, in one test |
| `random` vs `blocked` assignment | `ratio {control: 1, treatment: 1}` with `block_size: auto` = 4 over a roster divisible by 4 gives both methods the same arm *sizes* | Assert the **within-block** balance property (every consecutive block of `block_size` units holds each arm's share) rather than the totals, over a roster whose length is not a multiple of the block, with a pinned seed |
| Cell-aware partitioning | Cells and clusters coinciding makes a cluster-aware partitioner look cell-aware | Cells each holding several clusters of **unequal** size. § 3's fixture is that: whole roster 5 clusters, control arm 2, treatment arm 4 |
| Cluster indivisibility under assignment | A global "no cluster is split across arms" assertion is **wrong** — § Clustered units permits a cluster to span both arms under `by_attribute` | Assert indivisibility on core-drawn paths **only**, and assert the span is *permitted* under `by_attribute` in the same test |
| `fold_basis` under cells | A fixture where the smallest cell has as many clusters as the roster | § 3's fixture: 5 clusters whole, 2 in the smallest cell, and assert `k = 5` is refused |
| The budget fix | A `max_executions` low enough to warn either way | § 1's pair: 15, where the grid-only design must **not** warn and the grid × groups design must. The `max_executions: 5` run is the can-fail control showing the check is reachable |
| The undeclared-cluster exclusions | They pass today only because the config already fails | A config that validates **clean** with `groups` naming `site`, asserted against the same config without the axis, which must warn |
| The unclustered/uncelled regression | Passes trivially on a one-cell fixture | Pin `partition_units(roster, 3, "digest-abc")[0]` = `['u02', 'u06', 'u07', 'u05', 'u09']` before the change |
| `by_attribute` resolution | Levels and column values coinciding by construction | A column carrying a value **not** among the declared levels, and a declared level **absent** from the column — two different failures, two assertions |

### Defects that exist only in a combination

| Combination | Status | The defect |
|---|---|---|
| `allocation` × `cluster_by` | **Split by method, and only half is stated.** § Clustered units: whole clusters to one side "when core is the one assigning"; `by_attribute` may span arms | A single indivisibility rule applied to both is wrong in the `by_attribute` direction; a single "clusters may span arms" is wrong in the `random` direction. The two must be separate code paths, and the *contrast* between two arms sharing a cluster is what makes matched case-control a clustered contrast — refused by `E-DATA-CLUSTER-CONTRAST` |
| `allocation` × `measurements` | **Undocumented, and it is H3a's shipped defect a third time.** `CONSTANT_COLUMN_RULES` reaches flat keys only, so `assign.<axis>.from` is not covered | A `from` column varying across a unit's measurement rows collapses under `rule_for`'s `first` fallback, and **core invents an arm membership no row declared** — deciding which arm a unit is in by the order the file happens to be in. Strictly worse than the weight case and equal to the cluster case: it changes the design, not the estimate. A documents-change-first obligation, and it is task 1 |
| `allocation` × `weight_by` | **Refused together today by side effect.** A `between` design publishes comparisons, and `E-DATA-WEIGHT-CONTRAST` fires on `comparisons > 0` with any `weight_by` | So the combination is currently unreachable, and stays so until H4. Worth stating so nobody writes it |
| `allocation` × `fold` × `stratify_by` × `cluster_by` | **Real, demonstrated, and no task owns it** | `partition_units`' docstring already admits per-stratum index-wise merging can leave high-index folds empty. Cells compound it multiplicatively: `c × s` independent lists, each filling only as many folds as it has clusters. Measured: the control arm at `k = 5` gives `[7, 1, 0, 0, 0]` where the whole roster gives `[7, 3, 3, 1, 1]`. `validate` is silent because `fold_basis` is computed over the roster. **The per-cell bound is H3c-3's row; the per-stratum bound is still a check that does not exist**, and H3c must not accidentally claim to have added it |
| `allocation` × `holdout` | H3d's | § A fixed holdout split states the cell rule as a consequence of H3c's; H3c must state it in reusable form (§ 7) |
| `groups` × `ablate` | Legal by document, unreachable by code | The `AXIS_MODES` split is exactly this. `expand`'s docstring says the interleaved example "no config can reach here" — H3c makes it reachable, and the baseline-per-level rule (`validate` rejects a baseline fixing a group level while `ablate` is declared) is *Ablation baseline isn't a group level* |
| `assign.from` × `measurements` | Same as `allocation` × `measurements` above | The accessor `units.py`'s comment demands |
| `groups` × `baseline` | **Partly free, partly not** | `_baseline_cells` handles a group axis without change; `check_swept_value`'s exemption argument does not survive it (§ 1, `GROUPS` mask 7) |

### The unit-table reconciliation

`resolved == completed + ineligible + failed`, built in `runner._counts`.

**Arms do touch it, and in the one place H3b's analysis did not have to consider.**
`runner.attrition`'s docstring states the rule: "`resolved` counts what was handed out across
this condition, not the cohort: without a fold that is the full roster, since every execution
receives it whole. With a fold it is the union over every *declared* fold's members…". Under
`allocation: between` **the full roster is no longer what a condition receives** — the arm is —
so that first clause becomes false and the identity would be computed against a denominator
larger than any execution saw. Every unit outside the arm would land in `failed`, and
`max_failed_fraction` (the one fraction in `runner.py`, computed per condition over `resolved`)
would abort the run. So:

- `attrition`'s `resolved` must be the arm ∩ (fold members, where declared) — **a two-way
  narrowing, where today there is one** — and its docstring's sentence needs an arm clause.
- The identity still holds **per condition**, because arms partition the roster and each
  condition sees exactly one cell. It does **not** hold if summed across conditions, and nothing
  sums it that way today; a test should assert that it stays so.
- **Test the arm assignment as a partition** (disjoint ∧ covering the roster) over a fixture
  with unequal `ratio`, exactly as H3b tested the cluster partition. A greedy or blocked
  assignment can drop or duplicate a unit where a stride-slice cannot.

### Retiring a refusal makes latent defects live

Three times so far (H3a's `measurements` × `weight_by`, H3b's `measurements` × `cluster_by` and
the `k: all` budget). H3c's list is § 1, and it is 24 items across three refusals. The two that
would ship silently rather than crash are **the phantom parameter** (§ 5) and **the invented arm
membership** (§ 9), and both are documents-change-first.

## 10. What contradicts the charter

In descending order of how much it changes the plan.

1. **"15 rows" is right and it is not the measure.** 15 owned, 1 shared three ways, **2 already
   implemented and broken by this slice**, 1 to write from nothing, 4 to widen or narrow. The row
   count omits the artifact, the hash, the digest fix, the whole-leaf closure, two `W-` codes,
   the seed derivation, and the condition-value restructuring — which together are most of the
   work. This is the third consecutive charter with the same shape of error.
2. **"rewrites `partition_units` again, for cells" is wrong about which function.** Cells attach
   at `units.fold_basis` (a per-cell minimum) and at the caller's loop; `partition_units`'
   signature need not change and `_assign_whole_clusters` certainly does not. The larger
   partition-adjacent item is that `fold_basis`' "**One number, not two**" contract must survive
   a third input.
3. **The single largest item is not in the charter at all.** `runner.resolve_condition_cfg`
   writes every `Condition.values` key into `parameters` — demonstrated to produce
   `parameters.arm = 'control'` — so `Condition.values` must carry two kinds of entry, and seven
   consumers change with it.
4. **"retires `E-SWEEP-GROUPS-UNSUPPORTED`" understates the sweep work.** The `AXIS_MODES` split
   is a three-predicate split, not two; group levels reach condition labels through a check that
   does not see them; `check_swept_value`'s baseline exemption argument stops holding; and
   `E-SWEEP-EXPANDS-EMPTY`'s current double-report on a `groups`-only design is a pinned test
   that goes stale.
5. **A live doc/code divergence the charter could not have seen.** `hashes.design_digest`
   json-dumps `data.units` wholesale, including `assign.seed`, which § What `auto` derives from
   explicitly excludes. Latent today; the day `assign` is legal, pinning a seed redraws every
   fold boundary and reseeds every repeat.
6. **"owns `allocation.json`" comes with an obligation the charter omits and one it cannot
   discharge.** § What `study add` redacts does not name the one artifact that is a list of unit
   identities — a document gap H3c owes. And there is **no `resume` command**
   (`OPERATION_COMMANDS` is `{"validate", "run"}`), so "read rather than re-drawn on resume" has
   no reader; H3c's real obligation is to make the file self-sufficient and say so.
7. **H3c unlocks two designs outright and half of a third.** § Matched case-control's per-arm
   halves run once `groups` and `by_attribute` land — it declares no baseline, so it publishes no
   comparison — but the case-vs-control **contrast** it exists for stays refused by
   `E-DATA-CLUSTER-CONTRAST` until H4. § Clustered units spends two paragraphs on that design, so
   the expectation is set and the correction should be explicit.
8. **One thing in H3c's favour the charter also omits:** all three refusals are `c.error` calls
   inside `validate` itself, so unlike H3b there is no `REPL_DECLARATION_CODES` membership
   obligation and no callee-raised code to translate.

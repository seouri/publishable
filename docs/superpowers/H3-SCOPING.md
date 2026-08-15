# H3 Units — scoping measurement

Read-only measurement, 2026-08-12, against `docs/reference.md`, `docs/experimental-designs.md`,
and `src/publishable/` at the merge commit `410dd9a` (branch `main`, H1 and H2 landed). No
source file was changed. The question this answers: is **H3 Units** — chartered in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The hardening slices as

> **H3 Units** | `allocation`, `assign`, `holdout`, `folds`, `cluster_by`, `weight_by`,
> `measurements`, registered resolvers — the whole `E-DATA-*-UNSUPPORTED` family | after H1

— one slice of work, or several.

**Headline results.** Nine refusals, all confirmed by execution in both directions. **26**
§ Validation rows are H3's to write (H1 said 25, and its set differs from this one by three
rows in each direction), plus **6** more that H3 unblocks for another slice. H3 as chartered is
**not one slice**: it is four, and one of them is chartered under H7.

## Method

Every count below states the command that produced it. Every absence claim is paired with a
**can-fail control** — a perturbation of the same command that fires — because this repo has
twice recorded an absence established by a check that could not fail.

### Probing the refusals

`scratchpad/probe.py` builds a real git repo with a `cohort_pilot` entrypoint package and a
12-row `index.csv`, then calls `validate.validate_config` directly. Each refusal is probed as a
**pair**: once with the field declared, once with it absent (the shared control config). A
refusal counts as confirmed only when the code fires in the first and is absent from the second.

The control config produced **zero findings**, so "the code is absent from the control" is a
real observation rather than a tautology about a config that was already failing. The falsy
section of the same run reports `fired=False` for six of eight probes — that is the harness
demonstrating it can report a negative, on the same code path that reports the positives.

### Distinguishing an emit site from a mention

`grep -o 'E-DATA-[A-Z-]*' src/` cannot tell a `c.error(...)` call from a docstring paragraph,
and this repo has already recorded three identifiers that exist only in prose. Emit sites here
were taken from an AST walk over `src/**/*.py` that collects every `ast.Constant` string equal
to one of the nine codes and **excludes** any constant that is the docstring expression of a
module, function, or class. Can-fail control: the raw grep reports `cli.py:351`,
`validate.py:666`, `:703`, `:955`, and `:1499`; the AST walk drops all five, and each is
confirmed by reading to be docstring or comment text. The walk keeps ten sites, listed below.

`--include='*.py'` is used on every `grep` over `src/`, so no string is read out of stale
`__pycache__` bytecode.

## 1. The refusals

**Nine, and the charter's "seven" is right about the `E-DATA-*` family specifically.** There
are exactly seven `E-DATA-*-UNSUPPORTED` codes; `E-SWEEP-GROUPS-UNSUPPORTED` and
`E-REPL-FOLD-STRATIFY-UNSUPPORTED` are the two adjacent refusals, and both are H3's.

Independent corroboration from the spec: `reference.md:181` enumerates **eleven** declarations
marked `NOT BUILT`. Nine of the eleven are exactly these nine refusals; the remaining two are
`statistics.resample` and `statistics.null_test`, which are H4's.

| Code | Raised by | Surfaced by | Config shape refused | What `reference.md` says it should do |
|---|---|---|---|---|
| `E-DATA-RESOLVER-UNSUPPORTED` | `validate._check_unimplemented:1049` | same (direct `c.error`) | `data.units.from: {resolver: <name>}` | § Where units come from (1051-1097): a plugin artifact yields `Unit`s with declared `attributes`, must be condition-independent, and must emit `measurements.by` as an attribute |
| `E-DATA-ALLOCATION-UNSUPPORTED` | `validate._check_unimplemented:1057` | same | `data.units.allocation` outside `(None, "within")` | § Allocation (1104-1175): `between` gives each unit exactly one arm; `io.units` yields only that arm; pairing is derived per contrast from which axes two conditions differ on |
| `E-DATA-ASSIGN-UNSUPPORTED` | `validate._check_unimplemented:1066` | same (tuple-table loop, `c.error` at `:1073`) | truthy `data.units.assign` | § Allocation: one block per `sweep.groups` axis, with `method: random \| by_attribute \| blocked`, `stratify_by`, `ratio`, `block_size`, `seed` |
| `E-DATA-CLUSTER-UNSUPPORTED` | `validate._check_unimplemented:1067` | same | truthy `data.units.cluster_by` | § Clustered units (1233-1286): cluster-robust intervals, `clusters` joins the three-part `n`, whole clusters go to one side of every fold/holdout/assignment, and it decides what `resample`/`null_test` draw over |
| `E-DATA-WEIGHT-UNSUPPORTED` | `validate._check_unimplemented:1068` | same | truthy `data.units.weight_by` | § Weighted samples (1202-1232): weighted means for `basis: units`, `weighted_by` recorded beside every affected value, Kish `effective` joins `n`, and a warning when an attribute looks like a weight |
| `E-DATA-MEASUREMENTS-UNSUPPORTED` | `validate._check_unimplemented:1069` | same | truthy `data.units.measurements` | § What isn't a repeat (1770-1775): rows sharing a `key` collapse at resolution before any step sees them; `technical_n` reported as `{min, max, median}`; `io.record(..., measurement=)` collapses the same way |
| `E-DATA-HOLDOUT-UNSUPPORTED` | `validate._check_unimplemented:1070` | same | truthy `data.units.holdout` | § A fixed holdout split (1176-1201): `method: random \| by_attribute`, `frac`, `from`, `stratify_by`, `seed`; mutually exclusive with `fold`; `resolved` is the test partition; drawn within each cell under `between` |
| `E-SWEEP-GROUPS-UNSUPPORTED` | `validate._check_unimplemented:981` | same | truthy `sweep.groups` | § Expansion modes (1585-1643): a list of `{by, levels}`; a group level *is* a set of units; conditions across it are unpaired; it composes with `ablate` and with parameter axes |
| `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `replication._fold_k:92` (`ContractError`) | `validate._check_replication`, via `REPL_DECLARATION_CODES` (`validate.py:758`) | `stratify_by` on a `{kind: fold}` level | § Clustered units: balance the split on an attribute; must be constant within a cluster |

The last row is a different **shape** from the other eight: it is raised inside `replication.py`
and only translated into a finding by `validate`, under the callee's own identifier. The eight
above it are `c.error` calls inside `validate` itself. That matters for H3 because retiring it
means editing `replication.py` and `units.partition_units`, not `validate.py`.

`reference.md:372` states that a code ending `-UNSUPPORTED` is **deliberately absent** from
§ Errors `validate` reports, and `:181` is where the family is named instead. So retiring these
nine is a deletion from one list, not a migration into the error register.

### Probe results

```
CONTROL (no field declared): []

CONFIRMED  resolver              E-DATA-RESOLVER-UNSUPPORTED       declared=True control=False
CONFIRMED  allocation: between   E-DATA-ALLOCATION-UNSUPPORTED     declared=True control=False
CONFIRMED  assign                E-DATA-ASSIGN-UNSUPPORTED         declared=True control=False
CONFIRMED  cluster_by            E-DATA-CLUSTER-UNSUPPORTED        declared=True control=False
CONFIRMED  weight_by             E-DATA-WEIGHT-UNSUPPORTED         declared=True control=False
CONFIRMED  measurements          E-DATA-MEASUREMENTS-UNSUPPORTED   declared=True control=False
CONFIRMED  holdout               E-DATA-HOLDOUT-UNSUPPORTED        declared=True control=False
CONFIRMED  sweep.groups          E-SWEEP-GROUPS-UNSUPPORTED        declared=True control=False
CONFIRMED  fold.stratify_by      E-REPL-FOLD-STRATIFY-UNSUPPORTED  declared=True control=False
```

### The refusals are truthiness-gated, and four declarations slip through

`validate.py:1072` guards the five-field loop with `if units.get(field)`, commented "`init`
writes these as null; only a real declaration is refused." Probed:

| Declaration | Refusal fires? | Verdict |
|---|---|---|
| `holdout: {}` | no — **zero findings** | A hole. `init` writes `holdout: null`, not `{}` |
| `measurements: {}` | no — **zero findings** | A hole. `init` writes `measurements: null` |
| `weight_by: ""` | no — **zero findings** | A hole. An empty string names no attribute |
| `cluster_by: false` | no — `E-CONFIG-TYPE` only | Caught, but by the H1 envelope, not by the refusal |
| `assign: {}` | no — zero findings | **Correct.** `reference.md:92` shows `assign: {}` as what `init` writes |
| `allocation: null` | no — zero findings | **Correct.** `null` is the documented unset value |
| `allocation: ""` | **yes** | Correct — the guard here is `not in (None, "within")`, a different and stricter shape |
| `sweep.groups: {}` | no — `E-CONFIG-TYPE`, `E-SWEEP-EXPANDS-EMPTY` | Caught by two other checks; `groups` is documented as a list, so a mapping is malformed |

Three genuine holes (`holdout: {}`, `measurements: {}`, `weight_by: ""`), each a declaration
that changes no behavior and draws no finding — which is precisely the failure the refusals
exist to prevent. They are small, and all three are H3's to close *by implementing the field*,
which is the only fix that does not add a refusal about to be deleted. **Scoping consequence:
none of the blocked rows below changes verdict**, because each hole is an empty or vacuous
declaration and no § Validation row describes a state reachable through one.

## 2. The blocked `reference.md` § Validation rows

### Anchoring: the table is now 89 rows, not 87

H1 measured 87 rows at `reference.md` lines 204-290. The current main table is **89 rows at
lines 214-302**. H2 inserted two rows — "Sample draws aren't compared to a baseline" (line 231)
and "Sample is drawable" (line 232) — and content above the table shifted it down by 10 lines.
So an H1 row number `L` maps to `L + 10` below line 231 and `L + 12` above it. Line numbers
below are the **current** ones.

Counted by `awk 'NR>=214 && NR<=302 && /^\|/' docs/reference.md | wc -l` → 89. Can-fail
control: widening to `NR<=310` returns 89 as well (the table ends), and narrowing to `NR<=301`
returns 88.

### Verdict classes

Reusing H1's definitions verbatim, so the two documents are comparable:

- **implemented** — the check reaches a user under the identifier the row describes.
- **partial** — the check exists but does not perform what the row states.
- **missing-buildable** — absent, and writable against a config shape reachable today.
- **missing-blocked** — absent, and **no config can reach the state the row describes**,
  because the block that would produce it is refused wholesale. Established per row by the
  nine confirmed refusals above.

### Totals

| Ownership | Rows |
|---|---|
| **H3 owns the check outright** (subject is a `data.units` field, `sweep.groups`, or `fold.stratify_by`) | **26** |
| H3 unblocks it; another slice writes it | **6** |
| — of which H4 writes (needs `cluster_by`) | 2 |
| — of which H7 writes (needs the plugin registry) | 4 |
| **Total rows blocked behind at least one code the charter gives H3** | **32** |

All 32 are `missing-blocked`. **Zero** are implemented, partial, or missing-buildable: no
§ Validation row whose subject is one of the nine refused blocks has any implementation today,
which the empty control config confirms — declaring any of them yields exactly one finding, the
refusal.

**The headline number is 26.** It counts rows H3 must write as part of un-refusing its own
blocks. 32 is the number to use when asking "how many rows does H3 unblock," and it is the
figure that includes the four resolver rows the charter claims and H1 gave to H7.

### Per-code breakdown

A row can be blocked by more than one code; the "primary" column names the code whose block
must be un-refused for the row's subject to exist at all.

Every line number below was verified by matching the row's exact leading text against
`docs/reference.md` rather than by arithmetic on H1's numbers — the `+10/+12` shift makes
arithmetic unreliable, and a first pass of this document got four rows wrong that way. Can-fail
control: the same matcher returns an empty list for a row title that does not exist.

| Refusal | Rows it primarily blocks | Lines |
|---|---|---|
| `E-DATA-ASSIGN-UNSUPPORTED` | 8 | 267, 268, 270, 271, 273, 274, 275, 277 |
| `E-DATA-ALLOCATION-UNSUPPORTED` | 4 | 266, 276, 280, 286 |
| `E-SWEEP-GROUPS-UNSUPPORTED` | 3 | 229, 269, 272 |
| `E-DATA-HOLDOUT-UNSUPPORTED` | 3 | 262, 263, 264 |
| `E-DATA-WEIGHT-UNSUPPORTED` | 3 | 291, 292, 293 |
| `E-DATA-CLUSTER-UNSUPPORTED` | 2 primary (+2 co-blocked: 264, 282; +2 it unblocks for H4: 240, 241) | 278, 279 |
| `E-DATA-MEASUREMENTS-UNSUPPORTED` | 1 (+1 shared with the resolver, 257) | 243 |
| `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | 1 (+1 ambiguous, 259) | 282 |
| **Subtotal, H3 owns** | **25 + row 259** = **26** | |
| `E-DATA-RESOLVER-UNSUPPORTED` | 4 (the charter's; H1 gave them to H7) | 254, 255, 257, 258 |

The 26 in full: 229, 243, 259, 262, 263, 264, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275,
276, 277, 278, 279, 280, 282, 286, 291, 292, 293.

### Row by row

| Line | Row | Primary blocker | Owner | Note |
|---|---|---|---|---|
| 229 | Ablation baseline isn't a group level | `GROUPS` | **H3** | `validate.py:1490` names this "the one § Validation row still open" from H2 and says it "needs a group axis." H1 gave it to H2 |
| 240 | Shuffle level is unambiguous | `NULLTEST` + `CLUSTER` | H4 (H3 unblocks) | The row's own example is `match_set` — a cluster. Unwritable without `cluster_by`. H1 gave it to H4 with no note |
| 241 | Clusters enough to resample | `RESAMPLE` + `CLUSTER` | H4 (H3 unblocks) | Threshold is `limits.min_clusters`; subject is the resample. H1 flagged the ambiguity |
| 243 | Collapse rule fits the column | `MEASUREMENTS` | **H3** | |
| 254 | Resolver is installed | `RESOLVER` | H7 (charter says H3) | Purely a registry lookup |
| 255 | Resolver supplies the attributes | `RESOLVER` | H7 (charter says H3) | The resolver's unit-yielding contract |
| 257 | Resolver supplies the measurement field | `MEASUREMENTS` + `RESOLVER` | **shared** | H1 called it "H3 (and H7)" and counted it as H3's |
| 258 | Resolver is condition-independent | `RESOLVER` | H7 (charter says H3) | |
| 259 | Stratification attribute exists | ambiguous | **H3 or H4** | The row does not say *which* `stratify_by`. All three candidates are refused: `fold.stratify_by`, `assign.*.stratify_by` (H3), `resample.stratify_by` (H4 — and row 294 already covers that one, which argues for the H3 reading) |
| 262 | One evaluation split, not two | `HOLDOUT` | **H3** | `holdout` × `fold` |
| 263 | Holdout is resolvable | `HOLDOUT` | **H3** | |
| 264 | Holdout strata survive clustering | `HOLDOUT` + `CLUSTER` | **H3** | Both codes are H3's |
| 265 | Biological replicates are units | — | implemented | `REJECTED_KINDS["biological"]` → `E-REPL-KIND` |
| 266 | Allocation needs arms | `ALLOCATION` | **H3** | |
| 267 | Every axis is assigned | `ASSIGN` + `GROUPS` | **H3** | |
| 268 | Every assignment names an axis | `ASSIGN` | **H3** | |
| 269 | Axis names are distinct | `GROUPS` | **H3** | Purely `sweep.groups`. H1 gave it to H2 |
| 270 | Stratification is forward-only | `ASSIGN` | **H3** | Needs axis declaration order |
| 271 | Cells are populated | `GROUPS` + `ASSIGN` | **H3** | Warning; threshold `limits.min_units_per_cell`; no `W-` identifier exists |
| 272 | Arms need allocation | `GROUPS` + `ALLOCATION` | **H3** | The mirror of row 266 |
| 273 | Ratio names levels | `ASSIGN` | **H3** | |
| 274 | Block size fills the arms | `ASSIGN` | **H3** | `blocked` method |
| 275 | Attribute assignment resolves | `ASSIGN` | **H3** | `by_attribute` method |
| 276 | Allocation is coherent | `ALLOCATION` | **H3** | Warning; `limits.min_units_per_cell`; no `W-` identifier |
| 277 | Allocation strata exist | `ASSIGN` | **H3** | |
| 278 | Clustering looks undeclared | `CLUSTER` | **H3** | Warning; no `W-` identifier |
| 279 | Folds fit inside the clusters | `CLUSTER` | **H3** | |
| 280 | Folds fit inside the cells | `ALLOCATION` | **H3** | Drawn within each cell; `k` bounded by the smallest cell |
| 281 | Fold count is legal | — | implemented | `replication._fold_k` `E-REPL-FOLD-K` |
| 282 | Fold strata survive clustering | `FOLD-STRATIFY` + `CLUSTER` | **H3** | Both codes are H3's |
| 286 | Contrast has units in common | `ALLOCATION` | **H3** | Under `within` the intersection is never empty |
| 291 | Weight attribute exists | `WEIGHT` | **H3** | |
| 292 | Weights are usable | `WEIGHT` | **H3** | |
| 293 | Weighting looks undeclared | `WEIGHT` | **H3** | Warning; no `W-` identifier |

Rows 265 and 281 are listed only as anchors — both are already implemented, and they sit inside
runs of H3 rows where their absence would look like a numbering error. The unlisted line numbers
in the ranges above (244-253, 256, 260, 261, 283-285, 287-290, 294) are implemented, partial, or
another slice's, per H1's classification, which this measurement did not disturb.

### What H1 got wrong

H1's "**H3 Units 25**" is close but its *membership* differs from this measurement in three
rows each way.

**H1 missed four rows that are H3's (or that H3 unblocks):**

| Row | H1's owner | Why it is H3's |
|---|---|---|
| 229 Ablation baseline isn't a group level | H2 | It needs a group *level* for a baseline to fix. `validate.py:1490` says in so many words that this is the one § Validation row H2 left open. H2's spec is explicit that "a group level *is* a set of units, and the assignment that makes it one is H3's" |
| 269 Axis names are distinct | H2 | The subject is `sweep.groups` declaring one axis name twice. Nothing about it is parameter-sweep work |
| 240 Shuffle level is unambiguous | H4 | Correct that H4 writes it, but H1 recorded no H3 dependency. The row's example is an attribute varying within `match_set` — a cluster — so it is unwritable until `cluster_by` exists |
| 241 Clusters enough to resample | H4 | H1 noted the `cluster_by` dependency but did not carry it into the tally |

**One row H1 attributed to H3 is not cleanly H3's:** row 257 ("Resolver supplies the measurement
field"). H1 wrote "MISSING — blocked H3 (and H7)" and counted it under H3. It needs both
`measurements` and a resolver, so it is genuinely shared and should be counted once, in the
slice that lands second.

**Two rows are ambiguous in the documents, not in the measurement:** row 259 (`stratify_by`
unqualified) and row 257. Both are `missing-blocked` under every reading.

Net: 25 → **26** owned outright. The correction is not a large one, but the *composition*
changed by six rows, and two of those (229, 269) are rows H2 was believed to have finished with.

**H1's blocked total of 42 is now stale**, and a reader reconciling against it should not try to
make it sum. H1 split 42 as H3 25 / H7 7 / H2 6 / H4 4. H2 has since landed, taking four of its
six rows with it and leaving row 229 — which is H3's, not H2's — and row 269, also H3's. Under
the current table the split is **H3 26 / H7 4 (of which 1 shared) / H4 4-6 (2 of them unblocked
by H3) / H2 0**. The four unnamed-warning rows H3 must mint identifiers for are 271, 276, 278,
293; H1's list of six under current numbering is 241, 271, 276, 278, 283, 293, of which 241 is
H4's and 283 is H1's own buildable-now row.

### A negative result: the `limits` keys are already there

Rows 241, 271, and 276 cite `limits.min_units_per_cell` and `limits.min_clusters`. Both keys
**already exist** in everything they need to:

- `reference.md:162-163`, inside § The one config file's fenced schema.
- `materialize.py:151-152` — `init` writes both into every generated config.
- `envelope.py:80-81` — both are typed `int` in `LEAF_TYPES` by H1's envelope.

So H3 carries **no config-completeness prerequisite** for them, and no document has to change
first on their account. They are simply unread by `src/` (`grep -rn --include='*.py'
'min_units_per_cell\|min_clusters' src/` returns only the two `materialize.py` string lines and
the two `envelope.py` type entries; can-fail control: the same grep for `max_executions`
returns live reads in `validate.py`). This closes a question `spec-defects.md:1814` left open
and confirms `CHECKPOINT-AGENDA.md:81-82`'s claim, which said both were unread but did not check
whether they were *declared*.

## 3. What `units.py` and `replication.py` do today

### `units.py`, 300 lines

| Function / class | What it does | Where H3 attaches |
|---|---|---|
| `Unit` (dataclass, frozen, `eq=False`) | Three fields — `key`, `paths`, `attributes` — hashable and equal **by `key` alone**. `__getattr__` promotes an attribute to `unit.label`. `__setattr__`/`__delattr__` rebound after decoration to raise `E-UNIT-IMMUTABLE` | Nothing. Every H3 field (`cluster_by`, `weight_by`, `assign.from`, `holdout.stratify_by`, `null_test.shuffle`) names an **attribute**, which `Unit` already carries and `reference.md:1088` says explicitly is "why there is no schema block anywhere in `data.units`" |
| `_FrozenAttributes` | Read-only `Mapping` refusing every mutator with `E-UNIT-IMMUTABLE` | Nothing |
| `UnitList` | Exactly `__iter__`, `__len__`, `__getitem__` (int only, else `E-STEP-UNITS-CONTRACT`), plus the `train` property | Nothing structural. Arms and holdouts both produce a `UnitList` narrowed at construction, which is what `runner.py:382-384` already does for folds |
| `UnitList.train` | Returns `self._train` or raises `E-STEP-UNITS-UNAVAILABLE`, whose message already reads "needs a `fold` repeat **or a `data.units.holdout`**" | **This is the holdout attach point, and the contract is already written for it.** Holdout is `_train` populated from a different partition source |
| `resolve_units(units_decl, input_dir)` | Dispatches `from` → `_from_table` (str) or `_from_glob` (`{glob:}`), else `E-UNITS-SOURCE-MISSING`. Then checks key uniqueness. Returns `UnitList(units)` — **never with a `train`** | **The resolver attach point** — a third branch. **The `measurements` attach point** — collapse rows sharing a `key` here, before the uniqueness loop, since `reference.md:1775` says they collapse "at resolution, before any step sees them" and the uniqueness check currently rejects exactly the shape `measurements` makes legal |
| `_from_table` | `csv.DictReader`, `E-UNITS-EMPTY`, `E-UNITS-KEY-MISSING`, `E-UNITS-ATTR-RESERVED`, `E-UNITS-ATTR-MISSING` | Where `weight_by`/`cluster_by` column existence and positivity are checkable (rows 292, 293) |
| `_from_glob` | Key and path only; refuses any declared attribute | A glob can supply no `cluster_by`, `weight_by`, or `assign.from` — a cross-check H3 owes |
| `partition_units(roster, k, digest)` | Shuffles with `random.Random(_seed_from(digest))` and returns `k` interleaved slices. **Flat: no cluster awareness, no cell awareness, no stratification** | **The single densest attach point.** Rows 279 ("folds fit inside the clusters"), 280 ("folds fit inside the cells"), 283 (`fold.stratify_by`), and the holdout's own draw all land here. Every one of them changes this function's signature |
| `_seed_from(digest)` | `sha256(digest + "\|folds")[:4]` | `assign.seed` and `holdout.seed` need the same construction with a different suffix — `allocation.json` records them (`reference.md:748`) |
| `units_hash(roster)` | JSON over key/paths/attributes in resolved order | Untouched, but note `provenance.allocation_hash` is a **second, new hash** H3 owes — `reference.md:1136` and § `allocation.json` |

**Absent entirely, verified:** `grep -rn --include='*.py' 'allocation\|assign\|holdout\|cluster'
src/publishable/units.py` returns nothing. Can-fail control: the same grep for `fold` returns
`partition_units`'s docstring and `_seed_from`.

### `replication.py`, 378 lines

| Function | What it does | Where H3 attaches |
|---|---|---|
| `SUPPORTED_KINDS` / `REJECTED_KINDS` | `seed`, `batch`, `fold`; the five rejected names each route to their replacement, including `technical` → `data.units.measurements` and `holdout` → `data.units.holdout` | Nothing. Rows 242, 261, 265 are already implemented, and their messages already point at the fields H3 builds |
| `_fold_k(level, unit_count)` | Raises `E-REPL-FOLD-STRATIFY-UNSUPPORTED` first, then resolves `k`/`all` against the roster, then `E-REPL-FOLD-K` and `E-REPL-FOLD-K-TOO-LARGE` | **The refusal to retire.** `unit_count` becomes a cluster count under `cluster_by` and the *smallest cell's* count under `between` — rows 279 and 280 are both changes to the bound this function checks |
| `resolve_repeats(config, digest, unit_count)` | Level-count, kind, count-field, batch-key, duplicate-kind, batch-outermost, seed-collision checks | Its `unit_count` parameter is the only channel by which roster facts reach it — cell and cluster counts have to arrive the same way |
| `fold_members_for(levels, partitions)` | Fold label → frozenset of test-partition unit keys, or `None` | The shape holdout needs too, minus the label |
| `cross_levels`, `realize_order`, `_check_batch_is_outermost`, `_check_no_collisions`, `order_seed_for` | Repeat crossing, batch-respecting shuffle, seed derivation | Untouched by H3 |

### The `io.units` contract already promises what H3 delivers

`reference.md` § The unit list is three operations (1098-1103) fixes the surface at
iterate/`len`/index plus `.train`. Everything H3 adds is delivered **through that unchanged
surface**: `io.units` yields this arm's units under a group axis, this fold's or this holdout's
test partition otherwise (`reference.md:1281`), and `io.units.train` the complement. The wiring
exists — `cli.py:724-725` builds partitions and fold members, `cli.py:1236` narrows the roster
per fold label, `runner.py:382-384` constructs `UnitList(step_units, train=...)`. **H3 changes
what those partitions are, not how they are handed over.** That is the single largest reason the
slice is tractable at all.

## 4. The document surface

`reference.md` is 3405 lines; `experimental-designs.md` is 399. Spans measured by a script that
finds headings outside fenced code blocks and takes each section as running to the next heading.

### `reference.md`

| Section | Lines | Span | Content H3 owns |
|---|---|---|---|
| § The one config file — the `data.units` block | **22** | 78-99 | Every subkey, each marked `NOT BUILT`: `from.resolver`, `allocation`, `cluster_by`, `weight_by`, `measurements`, `holdout`, and `assign` with its six inner keys |
| § The one config file — ¶181 | 1 | 181 | The eleven `NOT BUILT` declarations. Nine of the eleven are H3's, and this paragraph is the register a retirement edits |
| § Validation — main table | 89 rows | 214-302 | 26 rows outright, 32 unblocked |
| § Validation — ¶304 | 1 | 304 | Names the four whole-leaf blocks the closed schema excepts. `data.units.holdout`/`.measurements`/`.assign` are **not among them** — see the finding below |
| § Errors `validate` reports — ¶372 | 1 | 372 | States that `-UNSUPPORTED` codes are deliberately absent from the register |
| § `allocation.json` — who went where | **15** | 740-754 | A whole run artifact H3 owes, with `seed`, `arms`, `holdout`, `strata`, covered by `provenance.allocation_hash`, and **read rather than re-drawn on resume** |
| § Units: the thing being measured | 18 | 1033-1050 | Framing |
| § Where units come from | **47** | 1051-1097 | The resolver contract, `Unit`'s three fields, and ¶1088's "the plugin decides how units are found; core decides what is required of them" |
| § The unit list is three operations | 6 | 1098-1103 | The surface H3 must not widen |
| § Allocation: within-subjects or between-subjects | **72** | 1104-1175 | `between`, the whole `assign` block, `random`/`by_attribute`/`blocked`, empty-`ratio` semantics, and the four-row pairing-derivation table |
| § A fixed holdout split | **26** | 1176-1201 | `holdout` in full, plus four interactions: mutual exclusion with `fold`, `resolved` is the test partition, whole clusters, and drawn within each cell |
| § Weighted samples | **31** | 1202-1232 | `weight_by`, `weighted_by`, Kish `effective`, weighted `t_over_units`, the undeclared-weight warning |
| § Clustered units | **54** | 1233-1286 | Cluster-robust intervals, `clusters` in `n`, indivisible clusters across folds/holdouts/assignments, `by_attribute` spanning arms, and what `resample`/`null_test` draw over |
| § A `fold` repeat puts the units out of reach | 12 | 1329-1340 | Scope rule, already implemented |
| § Expansion modes — `ablate × groups` | **16** | 1516-1531 | The composition H2 permitted but could not test |
| § Expansion modes — the `groups` mode | **59** | 1585-1643 | `groups` is a list always; a level is a set of units; shared `parameters_hash` across arms; axes resolve in declaration order; `stratify_by` may name an earlier axis; crossed pairing |
| § What isn't a repeat — `measurements` | 6 | 1770-1775 | Collapse at resolution, `technical_n` as `{min, max, median}`, `io.record(measurement=)` |
| § The unit table is the inference base | 100 | 2153-2252 | Where `weighted_by`, `effective`, and `clusters` join `n` |

**H3-specific `reference.md` surface: roughly 385 lines**, plus 32 table rows and the two
register paragraphs. For comparison, H2's whole subject — § Expansion modes — is 161 lines.

### `experimental-designs.md`

| Section | Lines | Span | Expressible today? |
|---|---|---|---|
| § Between-subjects / parallel-arm trial | 40 | 53-92 | **No** — needs `groups` + `between` + `assign` |
| § Between-subjects factorial | 32 | 93-124 | **No** — same, crossed |
| § Train-test holdout | 17 | 190-206 | **No** — needs `holdout` |
| § Clustered and hierarchical data | 11 | 298-308 | **No** — needs `cluster_by` |
| § Matched case-control | 25 | 309-333 | **No** — needs `groups` + `by_attribute` + `cluster_by` |
| § Cross-validation | 21 | 207-227 | **Partly** — `fold` is a supported kind and fully wired; `stratify_by` and cluster/cell awareness are missing |
| § Technical and biological replication | 14 | 284-297 | **Partly** — the *biological* half is implemented (row 265, `REJECTED_KINDS["biological"]`); only the technical half needs `measurements` |

**Five designs — 125 lines, 31% of the document — cannot be expressed at all today**, and two
more are partly blocked. Stated this precisely because the looser reading ("7 designs, 160
lines, 40%") is true only if `fold` and `biological` are counted as unbuilt, and both are built:
`_fold_k`, `partition_units`, `fold_members_for`, `cli.py:724-725` and `runner.py:382-384` are
the fold path, and H1 classified rows 260, 265, and 281 as implemented.

Every one of the seven also appears in § Mistakes core prevents, whose entries CLAUDE.md
requires to be "structurally impossible in the schema, not merely discouraged."

## 5. Dependency order among the pieces

### `groups` needs `allocation` **and** `assign` — all three or none

This is the strongest single piece of decomposition evidence, and it is stated from both ends
in the source:

- `validate.py:1494` — `groups` "is an axis over units rather than parameters, so it needs
  `data.units.allocation` and `data.units.assign`."
- `validate.py:1057` — `between` allocation "needs a `sweep.groups` axis to say what the arms
  are."

Table rows 266 ("Allocation needs arms") and 272 ("Arms need allocation") are the two halves of
the same mutual constraint, written as two separate checks. **Neither refusal can retire
alone**: a `groups` axis with `allocation: within` is refused by row 272, and
`allocation: between` with no `groups` axis is refused by row 266. `assign` is not optional
either — `reference.md:92` marks it "REQUIRED when allocation is `between`," and a group level
with no assignment rule has no membership.

**Answer: `groups` needs both.** They land together or not at all.

### `weight_by` depends on nothing structural

Rows 292, 293, 294 are attribute existence, positivity, and a heuristic warning. The runtime
effect is a weighted mean plus an `effective` entry in `n` plus a `weighted_by` marker. No
partition, no assignment, no roster narrowing. `reference.md:1230` states the one interaction
that exists — "`cluster_by` still decides the draw when both are declared" — and it is a
precedence rule, not a dependency: `weight_by` alone is complete and correct.

**Answer: nothing. It is the most separable piece in the charter**, and the only one that could
ship as its own small slice without touching the partition machinery.

### `folds` and `holdout` share machinery, and most of it exists

Three independent confirmations:

1. `units.py:156-158` — `E-STEP-UNITS-UNAVAILABLE`'s message names both against **one**
   accessor: "`io.units.train` needs a `fold` repeat or a `data.units.holdout`."
2. `reference.md:1188` — `io.units` yields the test partition and `io.units.train` the training
   one, "the same two lists a `fold` repeat provides, without the repetition."
3. `reference.md:1195` — holdout and fold are mutually exclusive *because* they are two answers
   to one question.

`partition_units`, `fold_members_for`, `UnitList(train=…)`, and the `cli.py`/`runner.py` wiring
are all built. Holdout is `partition_units` with `k = 2` and unequal sizes, plus config
plumbing, plus an `allocation.json` writer.

**Answer: yes, and `partition_units` is the shared function.** Both also inherit `cluster_by`'s
indivisibility rule and `allocation: between`'s draw-within-each-cell rule, so **`cluster_by`
and `allocation` both change `partition_units`' contract**, and doing folds-and-holdout before
clusters means rewriting that function twice.

### What H4 actually blocks on

The charter says H4 comes "after H3 (folds and clusters change what it draws over)." Measured
against `stats.py` (912 lines), that is **half right and names the wrong two**:

`grep -rn --include='*.py' 'welch_\|unpaired_\|cluster_robust\|weighted_by\|effective' src/`
returns exactly one hit, a docstring line in `cli.py:350`. Can-fail control: the same grep shape
for `t_over_units` returns 9 hits in `stats.py`. So `stats.py` today has `t_over_units`,
`paired_t_over_units`, `percentile_over_units`, `paired_percentile_over_units` — **the paired
family only**, with no unpaired, cluster-robust, or weighted construction anywhere.

| H4 needs | Blocks on | Why |
|---|---|---|
| The `welch_*` / `unpaired_*` interval family | `allocation: between` **+** `groups` | `cli.py:349-352`: `paired` is hard `True` today because the unpaired case "needs a group axis or `allocation: between`, both refused." No unpaired construction is reachable, so none is written |
| `resample` over the right draw | `cluster_by` | § Clustered units: "resample resamples clusters, not rows," and `clusters` joins `n` |
| `null_test` shuffle level | `cluster_by` | Row 240: the level is derived from whether the shuffled attribute varies within a cluster |
| Row 241 (`limits.min_clusters`) | `cluster_by` | The threshold counts clusters |
| Weighted intervals + `effective` | `weight_by` | § Weighted samples: Kish df. Arguably H4's own work, sitting behind H3's declaration |

**H4 does not block on `holdout`, `measurements`, or `folds`.** Folds are already built, and
neither `holdout` nor `measurements` changes what an interval draws over — a holdout narrows
`resolved` (which `stats.py` already handles per-condition) and `measurements` collapses before
`n` is counted (`reference.md:1775`, "technical replicates cannot reach `n`, because they were
gone before `n` was counted").

**Answer: H4 blocks on `cluster_by`, `allocation`, and `groups`. Not on the rest.** That means
H4 can start once two of the four proposed sub-slices below have landed, rather than after all
of H3.

### Order summary

```
              ┌── weight_by ──────────────────────────────┐  (independent)
              │                                            │
partition_units ── cluster_by ──┬── folds-under-clusters ──┤
              │                 └── holdout ───────────────┤
              │                                            ├──> H4 Statistics
  groups + allocation + assign ─┴── folds-within-cells ────┘
              │
              └── measurements  (independent of all of the above; resolve-time collapse)
```

`cluster_by` and `groups+allocation+assign` both change `partition_units`' contract, and
`cluster_by` is the smaller of the two, so it goes first — doing it after `groups` means
threading cluster indivisibility through cell-drawn partitions that were just written without
it.

## 6. Is H3 one slice or several?

### Verdict: **four slices, and one of them is chartered under H7.**

H1 was 12 tasks and H2 was 9 (counted: `grep -c '^### Task'` over
`plans/2026-08-11-validation-hardening.md` → 12 and `plans/2026-08-12-sweep-expansion-modes.md`
→ 9). H3 as chartered is materially larger than either, by every measure taken.

### The evidence

| Measure | H1 | H2 | H3 as chartered |
|---|---|---|---|
| Refusals to retire | 0 | 3 | **9** |
| § Validation rows to write | ~9 (2 new + 7 partial) | 6 | **26** (32 unblocked) |
| `reference.md` sections that are its subject | 1 (§ Validation) | 1 (§ Expansion modes, 161 lines) | **8** (≈385 lines) |
| `experimental-designs.md` designs unlocked | 0 | 2 (ablation, dose-response) | **5 wholly** (125 lines) **+ 2 partly** |
| New run artifacts owed | 0 | 0 | **1** (`allocation.json`, + `provenance.allocation_hash`) |
| New `W-` identifiers to mint in `reference.md` first | 6 | 0 | **4** (rows 271, 276, 278, 293 — all warnings with no identifier anywhere) |
| Core functions whose signature changes | 0 | 2 | **≥5** (`resolve_units`, `partition_units`, `_fold_k`, `resolve_repeats`, `UnitList.__init__`) |
| New interval constructions in `stats.py` | 0 | 0 | 0 directly — but it unblocks the entire unpaired and cluster-robust family for H4 |

Three further pieces of machinery nobody has counted:

1. **`allocation.json` is a whole artifact**, with a hash in the run record, a `resume`
   contract ("read rather than re-drawn," `reference.md:754`), and a redaction question at
   `study add` — it holds unit keys.
2. **`AXIS_MODES` must be split.** `sweep.py:374` defines `AXIS_MODES = ("grid", "paired",
   "sample")` and serves **three** roles from that one tuple: `_axes`'s condition product,
   `_swept_paths`' path collection, and `validate`'s `E-SWEEP-ABLATE-CROSSED` refusal.
   `reference.md:1512` says the condition set is "the product of every axis-shaped mode present
   — `grid`, `paired`, `sample`, `groups`", while `sweep.py:394` puts `groups` in
   `NON_AXIS_MODES` precisely so `ablate × groups` stays legal. Both are correct as written;
   they cannot both stay correct once `groups` joins the product. **H3 must split the tuple into
   "modes forming the condition product" and "parameter axes `ablate` may not cross,"** and the
   module docstring's argument for why one tuple is the choke point has to be rewritten with it.
3. **Three whole-leaf blocks must be closed.** `envelope.py:60-62` types
   `data.units.measurements`, `.holdout`, and `.assign` as bare `dict` leaves, so their inner
   keys are reached by no check. `reference.md:405` says so explicitly and adds that `holdout`
   "is not among [the named whole-leaf blocks] only because the whole block is refused today
   … which makes its gap latent rather than live." **Un-refusing any of the three makes its gap
   live**, so each must arrive with its own key closure *and* an edit to ¶304's enumeration.
   This is a real obligation the charter line does not mention at all.

### Proposed decomposition

Each produces working, testable software on its own, and each retires at least one refusal —
so none is a slice minted to hold one ledger entry.

| # | Slice | Retires | § Validation rows | Why here |
|---|---|---|---|---|
| **H3a** | **Weighted and technical units** — `weight_by`, `measurements` | `E-DATA-WEIGHT-UNSUPPORTED`, `E-DATA-MEASUREMENTS-UNSUPPORTED` | **4** — 243, 291, 292, 293 | The two pieces that touch **no partition**. `weight_by` depends on nothing; `measurements` collapses inside `resolve_units` before uniqueness is checked. Ships first because it is the only work that cannot conflict with anything else, and it closes the `measurements` whole-leaf block as a warm-up for the two harder closures |
| **H3b** | **Clustered units and clustered partitions** — `cluster_by`, `fold.stratify_by` | `E-DATA-CLUSTER-UNSUPPORTED`, `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | **4** — 259, 278, 279, 282 | Rewrites `partition_units` **once**, to draw whole clusters and honour a stratification. Doing it after H3c would mean rewriting a cell-aware partitioner to also be cluster-aware. Immediately unblocks two of H4's four dependencies (rows 240, 241) |
| **H3c** | **Allocation, arms, and assignment** — `allocation: between`, `sweep.groups`, `assign` | `E-DATA-ALLOCATION-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED` | **15** — 229, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 280, 286 | The mutually-blocking trio, which the two `validate` messages prove cannot be split further. The largest sub-slice by every measure: it owns `allocation.json`, `provenance.allocation_hash`, the `AXIS_MODES` split, the `assign` whole-leaf closure, unpaired-contrast reachability, and drawing partitions within each cell. If any sub-slice needs splitting again during planning it is this one, along the `random`/`blocked` vs. `by_attribute` seam |
| **H3d** | **A fixed holdout split** — `holdout` | `E-DATA-HOLDOUT-UNSUPPORTED` | **3** — 262, 263, 264 | Smallest, and deliberately last: it inherits *both* prior rules — whole clusters to one side (H3b) and drawn within each cell (H3c) — and `reference.md` states both as consequences of rules already in place. Building it before them means writing those interactions twice. Shares `allocation.json` with H3c and `partition_units` with H3b |
| **(H7)** | **Registered resolvers** — `data.units.from: {resolver:}` | `E-DATA-RESOLVER-UNSUPPORTED` | 4 — 254, 255, 258, and 257 jointly with H3a | See § 7, finding 2 |

4 + 4 + 15 + 3 = **26**, which is the owned total above. Row 257 is the one shared row and is
counted once, under H7.

**Recommended order: H3a → H3b → H3c → H3d.** The reason is `partition_units`. H3a never
touches it; H3b rewrites it once for clusters; H3c rewrites it once more for cells, on top of a
cluster rule that already exists; H3d consumes both without changing either. Any other order
rewrites the same function with the same rules in a different sequence, and the fold/holdout
interaction rules — which `reference.md` presents as consequences of the cluster and cell rules
— would each have to be written speculatively and then revised.

**H4 can begin after H3b + H3c**, not after all of H3, per § 5.

## 7. What contradicts the spine's charter line

Four findings, in descending order of how much they change the plan.

1. **"one slice" is not sustainable.** 9 refusals, 26 owned rows, ≈385 lines of `reference.md`,
   40% of `experimental-designs.md`, a new run artifact, a new provenance hash, four `W-`
   identifiers to mint, and five core function signatures — against H1's 12 tasks and H2's 9.

2. **"registered resolvers — the whole `E-DATA-*-UNSUPPORTED` family" claims work H1 gave to
   H7, and the charter and H1 cannot both be right.** A resolver is a plugin artifact reached
   through the entry-point registry, which is H7's subsystem and which `validate.py:1049`'s own
   message names as the reason for the refusal ("the plugin registry is not implemented in this
   build"). The clean split is: the **registry lookup** is H7's (rows 254, 258 — "is installed,"
   "is condition-independent"), and the resolver's **unit-yielding contract** is H3's shape
   (rows 255, 257 — must supply the declared attributes and the `measurements.by` field), but
   neither is testable without a registry to resolve a name against. Recommendation: **move
   `E-DATA-RESOLVER-UNSUPPORTED` out of H3 and into H7**, and have H3a state the attribute and
   measurement-field obligations as requirements H7 implements against. This is why the headline
   is 26 and not 30.

3. **"after H1" understates it: H3 is also after H2 in one row, and H2 knew.**
   `validate.py:1490` records that "the one § Validation row still open" from H2 — row 229,
   "Ablation baseline isn't a group level" — "needs a group axis to have a level for a baseline
   to fix." Row 269 ("Axis names are distinct") is in the same position. H1 counted both under
   H2. The charter line should say H3 closes H2's two remaining rows.

4. **The charter names no artifact, and H3 owes one.** `allocation.json` (`reference.md`
   740-754) is present whenever an arm assignment *or* a holdout is declared, is covered by
   `provenance.allocation_hash`, and is **read rather than re-drawn on resume**. It spans H3c
   and H3d, which is an argument for building the writer in H3c and having H3d extend it rather
   than the reverse.

One further item the charter omits, smaller than the four above but not free: **`envelope.py`
types `data.units.{measurements,holdout,assign}` as bare `dict` leaves**, so unknown keys inside
them are reached by no check. `reference.md:405` calls the gap "latent rather than live" only
because the blocks are refused. Each of H3a, H3c, and H3d makes its own gap live and must close
it, and each closure edits ¶304's enumeration of whole-leaf blocks — a documentation change that
must land first, per CLAUDE.md.

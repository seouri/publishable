# H3b Clustered units and partitions — scoping measurement

Read-only measurement, 2026-08-13, against `docs/reference.md`, `docs/experimental-designs.md`
and `src/publishable/` at `fc98a09` (branch `main`, clean; H1, H2 and H3a landed). No source
file was changed. Every count below states the command that produced it, and every absence
claim is paired with a **can-fail control** — a perturbation of the same command that fires.

`--include='*.py'` is used on every `grep` over `src/`, so no string is read out of stale
`__pycache__` bytecode.

**Headline.** H3-SCOPING's H3b charter is wrong in the same way its H3a charter was wrong: the
rows describe *checks*, and the work is elsewhere. Both refusals are confirmed. The row count
is **3 owned outright, not 4**, plus one shared three ways and four more H3b touches without
owning. But the row count is not what sizes the slice — `cluster_by` also owes **an interval
construction (`t_over_units_clustered`, CR1), whole-cluster drawing on the derived-metric
percentile path that is already running today, a fourth part of `n` (`clusters`), a `W-`
identifier that does not exist, a § Validation row that does not exist, and a
leave-one-*cluster*-out reading of `k: all`**, none of which the charter's "rewrites
`partition_units` once" mentions. Verdict: **one slice, do not split — but ≈12 tasks, not 4**,
which is H3a's size, not a quarter of it.

## Method

Four probes, all against the running code.

| Probe | What it ran | Where |
|---|---|---|
| Partition probe | `partition_units` and `_fold_k` called directly on a deliberately **uneven** cluster fixture (sizes 7, 3, 3, 1, 1 over 15 units) | scratchpad, `uv run python` |
| Validate probe | `validate_config` over a real git repo through `tests/test_validate.py`'s `write_config` fixture and a 20-unit `index.csv`, each declaration probed **as a pair** — declared, and a control without it | throwaway `tests/test_zzz_h3b_probe.py`, run then deleted; `git status --porcelain` clean afterwards |
| Table diff | Every § Validation row *title* extracted from `410dd9a` (H3-SCOPING's commit) and from `HEAD`, then `diff`ed | `git show 410dd9a:docs/reference.md \| awk … \| diff` |
| Absence greps | Each paired with a control grep of the same shape that returns hits | `grep -rn --include='*.py'` |

The uneven fixture is deliberate. Equal cluster sizes with `k` dividing the cluster count make a
stride-slice look cluster-clean, which is exactly the symmetric-fixture trap H3a paid for.

### The two refusals, confirmed in both directions

```
CONTROL plain roster                   -> ['W-DATA-WEIGHT-UNDECLARED']
cluster_by: site                       -> ['E-DATA-CLUSTER-UNSUPPORTED', 'W-DATA-WEIGHT-UNDECLARED']
fold k=4 stratify_by=label             -> ['E-REPL-FOLD-STRATIFY-UNSUPPORTED', 'W-DATA-WEIGHT-UNDECLARED']
CONTROL fold k=4 no stratify           -> ['W-DATA-WEIGHT-UNDECLARED']
weight_by + worked-example sweep       -> ['E-DATA-WEIGHT-CONTRAST']
CONTROL weight_by, no sweep            -> []
fold k=all + sweep (budget)            -> ['W-DATA-WEIGHT-UNDECLARED']
fold k=21 over 20 units                -> ['E-REPL-FOLD-K-TOO-LARGE', 'W-DATA-WEIGHT-UNDECLARED']
```

`W-DATA-WEIGHT-UNDECLARED` appears on every row whose config leaves `weight_by` unset — the
fixture carries a `sampling_weight` column, which is H3a's warning working. It is also this
document's single best can-fail control, and § What each refusal masks uses it as one.

## 1. The two refusals

| Code | Emit site | Shape refused | What the documents say it should do |
|---|---|---|---|
| `E-DATA-CLUSTER-UNSUPPORTED` | `validate._check_unimplemented`, the `for field, code in (…)` tuple loop — `("cluster_by", "E-DATA-CLUSTER-UNSUPPORTED")` — guarded by `if units.get(field)` | truthy `data.units.cluster_by` (a string naming an attribute) | § Clustered units: cluster-robust intervals; `clusters` joins the three-part `n`; whole clusters to one side of every fold, holdout and core-drawn assignment; `k` bounded by the cluster count; `stratify_by` constant within a cluster; and it decides what `resample`/`null_test` draw over |
| `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `replication._fold_k`, a raised `ContractError` — **not** a `c.error` | `stratify_by` non-`None` on a `{kind: fold}` level | § Clustered units: balance the split on an attribute; must be constant within a cluster |

**The second is only *translated* by `validate` — confirmed.** `validate._check_replication`
wraps `resolve_repeats(doc, "validate", unit_count=…)` in `except ContractError`, and re-emits
under the callee's own identifier only if `exc.code in REPL_DECLARATION_CODES`; anything else
`raise`s. `E-REPL-FOLD-STRATIFY-UNSUPPORTED` is a member of that frozenset. The comment above
it is explicit that the set is "deliberately narrow: a future code `resolve_repeats` raises that
is not added here propagates rather than being silently absorbed into a finding," pinned by
`test_an_unresolved_repl_code_is_not_swallowed`.

**Three implications for where the check must live:**

1. Retiring this refusal is an edit to `replication.py` and `units.partition_units`, not to
   `validate.py`'s refusal loop — the two codes retire by different mechanisms.
2. **Any new code H3b raises from that call tree must be added to `REPL_DECLARATION_CODES`, or
   it escapes `validate` entirely** and surfaces as a traceback where every other refusal is a
   diagnostic.
3. `_fold_k(level, unit_count)` receives **no roster and no attributes**. The row "Fold strata
   survive clustering" needs per-unit attribute values to decide whether `label` varies inside
   `animal_id`, so **it cannot live in `_fold_k` as signed today**. Either `resolve_repeats`
   gains a roster parameter (with `unit_count` derived from it), or the cluster/stratum
   cross-check moves into `validate` and `_fold_k` keeps count arithmetic only. Both arrival
   paths are live and differ — `validate._check_replication` and `cli`'s
   `resolve_repeats(doc, digest, unit_count=len(roster) …)`. That is the two-arrival-paths shape
   that cost H3a a fix round on nearly every task.

### A code-ordering flip nobody has recorded

`_fold_k` raises the stratify refusal **first**, before it resolves `k` at all. Measured:

| Level | Reported today | Control without `stratify_by` |
|---|---|---|
| `{kind: fold, k: 1, stratify_by: site}` | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `E-REPL-FOLD-K` |
| `{kind: fold, k: 99, stratify_by: site}` | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | `E-REPL-FOLD-K-TOO-LARGE` |
| `{kind: fold, k: all, stratify_by: site}` | `E-REPL-FOLD-STRATIFY-UNSUPPORTED` | resolves to `k = 15` |

Retiring the refusal **flips the reported code for the first two configs**. `tests/test_replication.py`
carries a test whose docstring pins exactly this ("a `fold` level's `stratify_by` reaches its own
refusal … rather than this one"), so the retirement is a test edit, not only a code edit.

## 2. The blocked § Validation rows, by title

### Anchoring the table

The main table is **91 rows** (header at line 213, last row at 305), not H3-SCOPING's 89.
`awk 'NR>=215 && NR<=305 && /^\|/' docs/reference.md | wc -l` → 91. Can-fail control:
`NR<=304` → 90, `NR<=312` → 91 (the table ends). The title diff against `410dd9a` shows H3a
added exactly two rows — **"Measurement axis exists"** and **"Weighted deltas aren't
computed"**. **H3-SCOPING's row numbers are therefore stale by two below "Measurement axis
exists" and by one above it; every row below is cited by title only.**

### The corrected attribution

| Row title | H3-SCOPING said | Measured | Note |
|---|---|---|---|
| Clustering looks undeclared | H3b (4) | **H3b owns** | Warning. **No identifier exists** — see below |
| Folds fit inside the clusters | H3b (4) | **H3b owns** | `k` ≤ cluster count |
| Fold strata survive clustering | H3b (4) | **H3b owns** | Cannot live in `_fold_k` as signed |
| Stratification attribute exists | H3b (4) | **shared three ways** | Row names no `stratify_by`; `fold.` is H3b, `assign.*.` is H3c, `holdout.` is H3d. H3b lands the first branch, H3c and H3d extend it. Not H3b's outright |
| Shuffle level is unambiguous | H3b unblocks for H4 | **partially** unblocks | Double-blocked; see § 6 |
| Clusters enough to resample | H3b unblocks for H4 | **partially** unblocks | Double-blocked; see § 6 |
| Folds fit inside the cells | H3c's | H3c's, **H3b supplies a clause** | Its own text reads "or its cluster count when `cluster_by` is declared" |
| Holdout strata survive clustering | H3d's | H3d's, **same shape** | Same clause, one section over |
| **Leave-one-out is affordable** | **not listed** | **implemented, and H3b makes it wrong** | See below |
| **(a "Cluster attribute exists" row)** | **not listed** | **does not exist and must be written** | See below |

**So: 3 owned outright, 1 shared, 4 touched. Not 4 owned.**

### Two rows H3-SCOPING missed entirely

**"Leave-one-out is affordable"** is implemented today and H3b invalidates its arithmetic. Its
example reads `{kind: fold, k: all}` over 240 units × 3 conditions = 720 executions. But
§ Repeat kinds states: "`all` means 'as many folds as there are things to leave out,' and with
`cluster_by` declared that's the cluster count, making it leave-one-*cluster*-out — the only
reading consistent with clusters being indivisible." Measured: `_fold_k({'kind':'fold','k':'all'}, 15)`
returns `15`, and `cli` supplies `unit_count=len(roster)`, which is the only channel. So under
`cluster_by` the whole execution budget — and `W-EXEC-BUDGET` with it — is computed from the
wrong number unless the cluster count reaches `_fold_k` on both arrival paths. This is H3b's
analogue of the unit-table accounting that turned H3a's 4 rows into 12 tasks.

**There is no "Cluster attribute exists" row**, though H3a wrote "Weight attribute exists" for
the exactly parallel declaration. `grep -n '^| ' docs/reference.md` over the table returns six
rows containing "cluster" — Clusters enough to resample, Holdout strata survive clustering,
Clustering looks undeclared, Folds fit inside the clusters, Folds fit inside the cells, Fold
strata survive clustering — and none of them checks that `cluster_by` names an attribute that
exists. **A documents-change-first obligation H3b owes before it writes any code.**

**And the row must name its reference set, which is the fix round H3a paid for.** Commit
`3978870` is titled "measurements.by is checked against the source's columns, not attributes" —
so `E-UNITS-ATTR-MISSING` now has two halves with two different reference sets, and H3a's
§ Errors entry for `E-DATA-WEIGHT-ATTR` states the discriminator: "`data.units.attributes`, not
the source's columns, and deliberately unlike the `measurements.by` half … a weight is read per
unit at analysis time, so it has to survive resolution as an attribute, where a `by` is consumed
at collapse time and dropped from the merged unit."

The sentence cutting the other way is one `src/` quotes twice (`units.py`'s `_from_table`
docstring and a comment in `validate.py`): `design-principles.md` § Core vs. plugin lists
`cluster_by` **beside** `measurements.by` as parallel namers of *input fields*. So the tiebreak
has to be stated, not assumed. **Measured, `cluster_by` falls on the `weight_by` side**, on two
sentences:

- `reference.md` § Where units come from: "Everything downstream is then indifferent to which
  form `from` took: `stratify_by`, `assign.from`, **`cluster_by`**, and `null_test.shuffle` all
  name **attributes**, and every check in Validation applies unchanged."
- `experimental-designs.md` § Clustered and hierarchical data shows it in the config:
  `units: {from: index.csv, key: cell_id, attributes: [animal_id], cluster_by: animal_id}` —
  `animal_id` is declared in `attributes` **and** named by `cluster_by`.

That is decisive and it is load-bearing twice over: `cluster_by` is read per unit at partition
time *and* at interval time, so it must survive resolution as an attribute — and **it is
therefore a column `collapse_measurements` collapses**, which is what makes the
`× measurements` defect in § 8 real rather than hypothetical.

### The `W-` identifier does not exist

`grep -n "W-DATA-CLUSTER\|CLUSTER-UNDECLARED" docs/*.md src/publishable/*.py` returns **nothing**.
Can-fail control: the same grep for `W-DATA-WEIGHT-UNDECLARED` returns the § Warnings row and
its emit site. So "Clustering looks undeclared" needs its identifier minted in
`reference.md` § Warnings core reports **before** any code is written, exactly as H3a did.

Commit `9e1b3e6` ("say why the weight warning needs a name and the cluster one does not") does
**not** retire this obligation — read in full, it explains why the two warnings' *trigger means*
differ (a cluster is structurally distinctive; a weight needs a name test), not that the cluster
warning needs no identifier. Every warning carries a `W-` code.

### One obligation H3b does *not* carry

`reference.md` § The one config file states it outright: "`.weight_by`, whose slice has landed,
needed none of it, **and neither will `.cluster_by`**: each is a string naming an attribute
rather than a block, so neither has sub-keys for a schema to close." Confirmed in
`envelope.py`: `"data.units.cluster_by": str`. **H3b has no whole-leaf closure**, unlike H3c
(`assign`) and H3d (`holdout`). This is the single strongest reason it is the smaller of the
three partition slices.

Same paragraph is the register H3b edits: it currently says "**Nine** declarations above are not
yet built" (H3-SCOPING measured eleven; H3a retired two). H3b takes it to **seven**, removing
`data.units.cluster_by` and "a `fold` repeat level's `stratify_by`".

## 3. `partition_units`'s rewrite

### What it does today, measured

```python
def partition_units(roster: UnitList, k: int, digest: str) -> list[list[Unit]]:
    units = list(roster)
    rng = random.Random(_seed_from(digest))
    shuffled = list(units)
    rng.shuffle(shuffled)
    return [shuffled[i::k] for i in range(k)]
```

Probed over the uneven fixture (sites S1×7, S2×3, S3×3, S4×1, S5×1 — 15 units, 5 clusters):

| `k` | Realized fold sizes | Clusters split across folds |
|---|---|---|
| 2 | 8, 7 | S1, S2 |
| 3 | 5, 5, 5 | S1, S2, S3 |
| 5 | 3, 3, 3, 3, 3 | S1, S2, S3 |

Can-fail control: the same measurement over a roster where every unit is its own cluster reports
**no** cluster split — so "clusters are split" is an observation about the algorithm, not a
tautology about the measurement.

### What the rewrite requires

| Question | The document's answer | Sentence that decides it |
|---|---|---|
| What is balanced? | **Units per fold**, over an indivisible cluster grain — not cluster count | "core balances units-per-fold as evenly as whole clusters allow and records the realized sizes in `sweep.yaml`" (§ Clustered units) |
| Fold sizes stay equal? | **No** — the ±1 guarantee is lost | "Fold sizes also stop being equal — clusters differ in size" (same) |
| Wildly uneven clusters? | Allowed. Sizes 7/3/3/1/1 at `k=5` give folds of 7/3/3/1/1. Nothing in the documents caps a cluster's share, and no `limits` key exists for it | absence; `limits.min_clusters` is a *resample* threshold per its inline comment |
| Bound on `k`? | **Cluster count, not unit count** | "`k` is bounded by the cluster count, not the unit count. Ten animals admit at most 10 folds, and `validate` rejects a larger `k`" |
| `k: all`? | **Leave-one-cluster-out** | "with `cluster_by` declared that's the cluster count, making it leave-one-*cluster*-out — the only reading consistent with clusters being indivisible" (§ Repeat kinds) |
| Seeding? | Unchanged construction, applied to a different list | `_seed_from(digest)` is `sha256(digest + "\|folds")[:4]`; § Clustered units: "Partitions are computed once per run … derived from the config-level design digest" |

**The digest-seeding rule's real consequence is a regression hazard.** The shuffle must move
from the *unit* list to the *cluster* list, built in roster order (which is already pinned —
`units_hash` "covers the list in resolved order"). So **the unclustered path must produce
byte-identical partitions after the rewrite**. `_seed_from("digest-abc")` is `4259409437` and the
`k=3` first fold over the fixture is `['u01','u05','u06','u04','u08']` — pin both, before
touching the function.

**Justified as refactor safety, not as a resume obligation.** Bit-identical reruns are on
CLAUDE.md's stated non-promises list, and `code_hash` covers `src/**`, so a mid-run upgrade is
already a detectable change of identity rather than a silent one. The reason to pin is narrower
and still worth a task: the rewrite must provably not change what an *unclustered* design means,
and a pinned seed plus a pinned first-fold list is the only way to know that a shuffle moved from
the unit list to the cluster list without disturbing the roster-order path underneath it.

### Functions and call sites that change

| Name | Change |
|---|---|
| `units.partition_units` | Signature gains the cluster grain (and, in H3b, the stratification). The single densest attach point |
| `units._seed_from` | Unchanged — deliberately, so the unclustered path is bit-stable |
| `units.resolve_units` | Returns `(UnitList, technical_n, columns)` since H3a. Cluster grouping either joins that tuple or is derived by a new sibling function from the roster + `cluster_by` |
| `replication._fold_k` | `unit_count` becomes a cluster count under `cluster_by`; `k: all` resolves to it; the stratify refusal is deleted |
| `replication.resolve_repeats` | Its `unit_count` parameter is the only channel roster facts reach it by; a cluster count must arrive the same way, on **both** callers |
| `validate._check_replication` | One arrival path; also owns `REPL_DECLARATION_CODES` membership for any new code |
| `cli` — `resolve_units(...)`, `resolve_repeats(..., unit_count=len(roster) …)`, `partition_units(roster, fold_level.n, digest)` | The second arrival path, and the only `partition_units` call site in `src/` |
| `runner.attrition` / `runner._counts` | Where `clusters` joins `n` — see § 4 |
| `stats.summarize_step` | Where the clustered interval and `n.clusters` reach a metric block |

`grep -rn --include='*.py' 'partition_units' src/` returns the definition, one `cli` call, and
one `sweep.py` docstring mention. Can-fail control: the same grep for `resolve_repeats` returns
two live call sites.

## 4. `cluster_by`'s reach beyond partitioning

`grep -c cluster docs/reference.md` → **48** (also 15 in `experimental-designs.md`, 1 in
`design-principles.md`). Every stated interaction, with the sentence that decides its owner:

| Interaction | Owner | The sentence that decides it |
|---|---|---|
| **Cluster-robust interval, `t_over_units_clustered`** | **H3b** | § Clustered units' *first* sentence: "Core then computes cluster-robust intervals — over the same per-unit table every other interval comes from". § Statistical reporting names the method: "`t_over_units_clustered` \| Cluster-robust (CR1: the sandwich estimator with the standard finite-sample scaling), df = clusters − 1" |
| **`n` gains `clusters`** | **H3b** | § The unit table is the inference base: the three counts are "joined by `clusters` whenever `cluster_by` makes the cluster the inferential draw". `stats.summarize_step`'s own docstring already names `clusters` as a key that **joins** `n` and so "travels in `counts`" — i.e. through `runner.attrition`, exactly where `effective` was put |
| **`k` bounded by cluster count; `k: all` is leave-one-cluster-out** | **H3b** | § Clustered units and § Repeat kinds, quoted in § 3 |
| **Whole clusters to one side of a fold** | **H3b** | "Whole clusters go to one side of a split; a cluster is never divided between train and test" |
| **`fold.stratify_by` constant within a cluster** | **H3b** | "Stratifying folds on an attribute that varies inside a cluster is unsatisfiable once the cluster is indivisible, so `validate` rejects it" |
| **Undeclared-cluster warning** | **H3b** | "`validate` warns when an attribute looks like a cluster identifier (few distinct values, many units each) but hasn't been declared as one" |
| **Contrast intervals take a `_clustered` suffix** | **deferrable — see below** | § Statistical reporting: "When `cluster_by` is declared each takes a `_clustered` suffix … the *t* forms are cluster-robust (CR1) … and the percentile forms resample whole clusters — jointly across both sides when paired" |
| **`holdout`: whole clusters, `stratify_by` constant within one** | **H3d** | § A fixed holdout split: "**Whole clusters go to one side**, when `cluster_by` is declared … Same rule and same reason as folds". H3b must state the rule so H3d can reuse it |
| **`assign.stratify_by`; `random`/`blocked` draw whole clusters** | **H3c** | "The same logic governs `assign.stratify_by` under `allocation: between` — **when core is the one assigning**" |
| **`by_attribute` may span arms (matched case-control)** | **H3c** | "With `method: by_attribute` the arm is read rather than drawn, and a cluster may span both arms" — needs `assign`, which H3b does not touch |
| **The always-on derived-metric percentile draw resamples clusters** | **H3b — see below** | § Statistical reporting: a derived metric gets "a percentile `ci95` from resampling units — **or clusters, when `cluster_by` is declared**" |
| **`statistics.resample` draws clusters, not rows** | **H4** | "**`resample` resamples clusters, not rows.**" — and `statistics.resample` is itself refused today (`E-STATS-RESAMPLE-UNSUPPORTED`) |
| **`null_test` within-cluster vs whole-cluster shuffle; the ambiguous middle** | **H4** | "**`null_test` shuffles at the level the shuffled attribute lives at.**" / "`validate` rejects the ambiguous middle" — `statistics.null_test` is refused today (`E-STATS-NULLTEST-UNSUPPORTED`) |
| **`limits.min_clusters`** | **H4** | The row is "Clusters enough to resample": "`statistics.resample` with `cluster_by: animal_id` over 4 animals bootstraps 4 draws; below `limits.min_clusters`". The subject is the resample |
| **`weight_by` × `cluster_by` precedence** | **undefined — see § 8** | § Weighted samples: "`cluster_by` still decides the draw when both are declared, since a cluster is what's independent and a weight is what it represents" |
| **`measurements` × `cluster_by`** | **undefined — see § 8** | *No sentence exists.* This is the gap |

`limits.min_clusters` remains **declared but unread**: `grep -rn --include='*.py' 'min_clusters' src/`
returns only `materialize.py`'s generated-config string and `envelope.py`'s `int` type entry.
Can-fail control: the same grep for `max_executions` returns 8 hits including live reads. So
H3b carries no config-completeness prerequisite for it — and no obligation to read it either.

### The derived-metric percentile draw is live today, and it is H3b's

`statistics.resample` being refused does **not** mean no resampling happens. Measured in `cli`'s
phase-8 block: `derived_metric_draws = 2000` is a hard constant, and its own comment says why —
"`statistics.resample` isn't honored yet (`E-STATS-RESAMPLE-UNSUPPORTED` refuses a declared
one), so this is the one place the default `reference.md` § How a metric becomes a number
documents — bootstrap at 2000 — is a real, passed value." **The draw is ungated**: `_make_resample_fn`
builds a closure for every derived metric of every recording step whenever a template is
present, and `percentile_of_derived` / `paired_percentile_of_derived` consume it.

This corroborates the worked example — CLAUDE.md says kendall's `ci95` "is a percentile
bootstrap of τ" and that `r` is "derived by `aggregate(units)`", which a refused
`statistics.resample` could not have produced.

**Consequence: un-refusing `cluster_by` makes an already-live draw wrong.** § Statistical
reporting requires that draw to resample clusters, so H3b owes whole-cluster drawing on the
derived path — the per-condition half in tasks 10–11, the paired half covered by the deferral
below. This is the single largest item H3-SCOPING's H3b line places in the H4 column, and it is
the reason task 10 is "the clustered constructions" rather than one function.

### The one decision that sizes the slice: can the clustered contrast be deferred?

**Yes, on a precedent H3a set and this measurement confirms is already broad.** H3a shipped
`weight_by` as a declaration core honours while refusing the *combination* with a contrast —
`E-DATA-WEIGHT-CONTRAST`, emitted from `_check_sweep` rather than the declaration loop, with its
own § Validation row ("Weighted deltas aren't computed") and its own § Errors registry entry.
The code's comment states the boundary: "It is a refusal of a *combination* rather than of a
declaration, so it carries a row in § Validation's registry and is not one of the `NOT BUILT`
declarations § The one config file counts."

**Measured: `E-DATA-WEIGHT-CONTRAST` fires on the worked example's own sweep shape** — a
`sweep.baseline` of `analysis.method: pearson` beside a three-level `grid` produces two
comparisons and the refusal fires; the same config without the sweep produces zero findings. So
the precedent is *known-broad and accepted*, and H3b may lean on it rather than needing an
argument that a narrow refusal is being widened.

Consequence: H3b ships `t_over_units_clustered` **and the whole-cluster derived percentile draw**
for each condition's own value and interval, and refuses the clustered *delta* under a new
`E-DATA-CLUSTER-CONTRAST` — which covers both `paired_t_over_units` and the live
`paired_percentile_of_derived` path — and which H4 lifts when the paired estimator family gains
its `_clustered` forms. **If instead the clustered paired delta must ship inside H3b, add ≈4
tasks** — `paired_t_over_units_clustered` plus the joint whole-cluster percentile draw ("drawing
once for both sides") plus their wiring.

`grep -rn --include='*.py' '_clustered\|cluster_robust\|CR1' src/` returns **nothing** today.
Can-fail control: `t_over_units` returns 28 hits.

### What H3b unlocks in `experimental-designs.md`

`grep -c cluster docs/experimental-designs.md` → 15, across four designs and two
§ Mistakes core prevents rows.

| Design | Needs | After H3b |
|---|---|---|
| § Clustered and hierarchical data | `cluster_by` alone — its config is `units: {from: index.csv, key: cell_id, attributes: [animal_id], cluster_by: animal_id}`, plus `{kind: fold, k: 5}` for the split half | **Unlocked outright.** The only whole design H3b ships, and the argument that this slice delivers something a user can run rather than only checks |
| § Cross-validation | `fold` (built) + `fold.stratify_by` (H3b) | **Its blocked half is exactly H3b's.** "Leave-one-out is `k: all` — as many folds as there are units, **or as there are clusters when `cluster_by` is declared**" — the same clause the § Validation row needs |
| § Matched case-control | `sweep.groups` + `assign.by_attribute` + `cluster_by` | **Not unlocked — H3c.** Worth stating, because § Clustered units spends two paragraphs on this design and a reader will assume otherwise |
| § Bootstrap and permutation | `statistics.resample` / `null_test` + `cluster_by` | Not unlocked — H4 |

Two § Mistakes core prevents rows become live with the refusals: **"Ignored clustering"**
("`cluster_by` produces cluster-robust intervals; `validate` flags an attribute that looks like
an undeclared cluster") and **"A cluster split across train and test"** ("`validate` rejects a
`k` above the cluster count"). CLAUDE.md requires every entry there to be "structurally
impossible in the schema, not merely discouraged" — so **re-checking those two rows belongs in
task 1's consistency pass**, and the second row is the one-line statement of tasks 3–5.
Two further rows — "Resampling clustered rows as if independent" and "A permutation that
shuffles away the matching" — stay H4's and stay refused.

## 5. What `src/` has today

Functions, not files.

| Function / class | State | Where a cluster attaches |
|---|---|---|
| `units.Unit` | Frozen, hashable by `key`; `__getattr__` promotes an attribute to `unit.site` | **Nothing.** `cluster_by` names an attribute, which `Unit` already carries |
| `units.UnitList` | Iterate, `len`, integer index, `.train` | Nothing structural — a fold's `UnitList` is narrowed at construction and stays so |
| `units.resolve_units` | Returns the H3a three-tuple `(UnitList, technical_n \| None, columns)`. Dispatches `from` → `_from_table` / `_from_glob`, collapses `measurements` **before** the key-uniqueness loop, then checks uniqueness | The grouping attach point: either a fourth tuple member or a sibling function over `(roster, cluster_by)`. Note `_from_glob` returns an empty column set — a glob can supply no `cluster_by`, a cross-check H3b owes |
| `units._from_table` | `csv.DictReader`; raises `E-UNITS-EMPTY`, `-KEY-MISSING`, `-ATTR-RESERVED`, `-ATTR-MISSING` | Where cluster-column existence is checkable, and where the missing "Cluster attribute exists" row lands |
| `units.collapse_measurements` / `rule_for` / `apply_rule` | H3a's collapse, `first` fallback for an unnamed column | **The `× measurements` defect site — see § 8** |
| `units.partition_units` | Shuffle + stride-slice. Flat: no cluster, cell or stratum awareness | The densest attach point |
| `units._seed_from` | `sha256(digest + "\|folds")[:4]` | Unchanged, deliberately |
| `units.usable_weight` / `is_measurement_numeric` | H3a's single authorities for "a usable weight" / "numeric" | The pattern to copy: one authority for "these units form one cluster", read by both `validate` and the run |
| `replication._fold_k` | Raises the stratify refusal **first**, then resolves `k`/`all`, then `E-REPL-FOLD-K` and `-K-TOO-LARGE` | The refusal to retire; the bound to change; the roster it does not have |
| `replication.resolve_repeats` | `unit_count` is the only channel roster facts reach it by | Cluster count arrives the same way, on both callers |
| `replication.fold_members_for` | Fold label → frozenset of test-partition keys | Unchanged shape; different membership |
| `runner.attrition` / `runner._counts` | Builds `{resolved, completed, ineligible, failed}` and adds `effective` when `weights is not None` | **Where `clusters` joins `n`** — the identical slot, one declaration over |
| `stats.summarize_step` | Owns the documented **two-route rule**: a key that JOINS `n` travels in `counts`; a key that sits BESIDE `n` travels in `beside_n`. Its docstring already cites `clusters` as a `counts` key | Where the clustered interval replaces `t_over_units`, exactly as `weighted_t_over_units` did |
| `stats.t_over_units` / `weighted_t_over_units` / `kish_effective_n` | Present. No unpaired, no cluster-robust construction anywhere | `t_over_units_clustered` is new |
| `cli` (`_run`-side) | Resolves the roster, builds `beside_n`/`weights`, calls `resolve_repeats`, `partition_units`, `fold_members_for` | Every threading change lands here |

## 6. Dependencies and ordering

### Which of H4's dependencies H3b genuinely unblocks — the claim is weaker than it reads

H3-SCOPING: "Immediately unblocks two of H4's four dependencies (rows 240, 241)." Measured, both
rows are **double-blocked**:

| Row title | Blocker 1 | Blocker 2 | After H3b |
|---|---|---|---|
| Shuffle level is unambiguous | `E-DATA-CLUSTER-UNSUPPORTED` | `E-STATS-NULLTEST-UNSUPPORTED` (`validate.py`, confirmed present) | Still unwritable |
| Clusters enough to resample | `E-DATA-CLUSTER-UNSUPPORTED` | `E-STATS-RESAMPLE-UNSUPPORTED` (confirmed present) | Still unwritable |

Both remaining blockers are H4's **own** work, not another slice's. So the honest statement is:
**H3b removes one blocker of two on each of two H4 rows; neither becomes writable, and no H4
dependency is fully discharged by H3b alone.** H3-SCOPING's derived conclusion — "H4 can begin
after H3b + H3c" — survives unchanged; only the word "immediately" does not.

Since H3a landed, H4's weighted-interval dependency is already discharged, so H4's remaining
*structural* blocker outside its own subject is `allocation: between` + `sweep.groups` — H3c.

### Does H3b depend on H3c?

**No.** Nothing in H3b reads `allocation`, `assign` or `sweep.groups`. The cell rule is an
addition H3c layers on top: its row "Folds fit inside the cells" reads "`k` may not exceed the
smallest cell's unit count, **or its cluster count when `cluster_by` is declared**" — H3c
consumes H3b's clause, not the reverse. This confirms H3-SCOPING's ordering argument
(`partition_units` is rewritten once for clusters, once for cells, in that order).

### What H3d needs from H3b

H3d is `holdout`, which § A fixed holdout split describes as "the same two lists a `fold` repeat
provides, without the repetition" — one uneven two-way split rather than `k` even ones. So
**H3b must state its indivisibility rule as a roster-partition rule parameterised by target
proportions, not as a fold-specific one.** A `partition_units` whose contract is "`k` equal-ish
folds over whole clusters" forces H3d to write the cluster rule a second time; one whose
contract is "assign whole clusters to partitions with declared target sizes, honouring a
stratification" is reused with `k = 2` and sizes `(0.8, 0.2)`. This is a design instruction for
H3b's task 2, and it costs nothing to honour up front.

## 7. One slice or several

### Verdict: one slice, ≈12 tasks

**Do not split.** The charter's own argument holds — `partition_units` is rewritten once, and
separating "resolve clusters" from "partition by clusters" would rewrite the same function
twice for no independent deliverable. But the charter's **size** is wrong by a factor of three.

| Measure | H3a (landed) | H3b as chartered | H3b as measured |
|---|---|---|---|
| Refusals to retire | 2 | 2 | 2 |
| § Validation rows owned outright | 4 | 4 | **3** (+1 shared, +4 touched) |
| § Validation rows to *write from nothing* | 0 | 0 | **2** ("Cluster attribute exists", "Clustered deltas aren't computed") |
| `W-` identifiers to mint first | 1 (`W-DATA-WEIGHT-UNDECLARED`) | 0 stated | **1** (`W-DATA-CLUSTER-UNDECLARED`) |
| New `n` parts | 1 (`effective`) | 0 stated | **1** (`clusters`) |
| New interval constructions | 1 (`weighted_t_over_units`) | 0 stated | **2** (`t_over_units_clustered` CR1, plus whole-cluster drawing on the live derived percentile path) |
| Designs unlocked in `experimental-designs.md` | 1 partly (technical replication) | 0 stated | **1 outright** (§ Clustered and hierarchical data) **+ 1 partly** (§ Cross-validation) |
| New combination refusals | 1 (`E-DATA-WEIGHT-CONTRAST`) | 0 stated | **1** (`E-DATA-CLUSTER-CONTRAST`) |
| Whole-leaf closures | 1 (`measurements`) | 0 | **0** — the document says so explicitly |
| Core function signatures changed | 4 | 1 stated | **≥5** |
| Plan tasks | **12** | implied ~4 | **≈12** |

Task counts by `grep -c '^## Task' docs/superpowers/plans/<plan>.md`: H1 (validation-hardening)
**12**, H2 (sweep-expansion-modes) **9**, H3a (weighted-and-technical-units) **12**. Note
H3-SCOPING cited `^### Task` for the same figures; that heading level now returns **0** on all
three plans, so a reader reconciling against it should re-run with `^## Task`. The H1 and H2
numbers themselves are unchanged.

**H3b is H3a-sized, not a quarter of it.** Every measure that is not the row count says so, and
the row count is precisely the measure that misled H3a.

### Proposed decomposition

Ordered so that each task leaves the tree green, and so that no document edit trails the code it
governs.

| # | Task | Why here |
|---|---|---|
| 1 | **Documents first.** Mint `W-DATA-CLUSTER-UNDECLARED` in § Warnings; add the "Cluster attribute exists" row; add the "Clustered deltas aren't computed" row and its § Errors entry; add the `measurements` × `cluster_by` rule to § Clustered units (§ 8); add the cluster clause to "Leave-one-out is affordable"; run both consistency passes | CLAUDE.md requires the document to change first, and four of these are things `reference.md` does not currently say |
| 2 | **Cluster resolution, one authority.** A single function answering "which units form one cluster", in roster order, read by `validate` and by the run — the `usable_weight` pattern. Plus the attribute-existence check and the glob cross-check | Everything downstream reads this. Two notions of a cluster is H3a's exact failure mode |
| 3 | **`partition_units` rewrite.** Whole clusters, units-per-fold balanced, target sizes parameterised for H3d. **Regression test: the unclustered path is bit-identical** | The single densest change; parameterising for H3d costs nothing now and a rewrite later |
| 4 | **Thread the cluster count to `_fold_k`** on both arrival paths; `k` bounded by cluster count; `k: all` becomes leave-one-cluster-out; the budget follows | Two arrival paths, the shape that cost H3a a fix round on nearly every task |
| 5 | **Row "Folds fit inside the clusters"**, with `REPL_DECLARATION_CODES` membership for any new code | Depends on 4 |
| 6 | **Stratified partitioning** in the rewritten `partition_units` | The second partitioning rule; separate from 3 so each has one reason to fail |
| 7 | **Rows "Fold strata survive clustering" and "Stratification attribute exists" (fold branch)**, sited per § 1's third implication | Needs the roster, which `_fold_k` does not have |
| 8 | **Retire `E-REPL-FOLD-STRATIFY-UNSUPPORTED`**, including the code-order flip and its pinned test | Gated on 6 and 7 |
| 9 | **`n` gains `clusters`** via `runner._counts`/`attrition` and `stats.summarize_step`'s `counts` route | The slot `effective` already occupies |
| 10 | **The clustered constructions**, as pure functions with their own arithmetic tests: `t_over_units_clustered` (CR1, df = clusters − 1) **and** whole-cluster drawing for the always-on derived percentile path | Isolated from wiring, as H3a isolated `weighted_t_over_units`. Two constructions, not one — see § 4 |
| 11 | **Wire both** in `summarize_step` and `cli`'s phase-8 block, so value, interval and `n.clusters` move together | H3a's lesson: a clustered interval beside an unclustered point estimate is a declaration half-delivered |
| 12 | **Refuse the clustered contrast** (`E-DATA-CLUSTER-CONTRAST`) and **retire `E-DATA-CLUSTER-UNSUPPORTED`**; edit the `NOT BUILT` register from nine to seven | The retirement is gated on the declaration changing the record, which 9–11 are what make true |

**Order rationale.** 2 → 3 → 4 → 5 is the partition spine and must be sequential. 6 → 7 → 8 is
the stratification spine, which rests on 3 and is otherwise independent. 9 → 10 → 11 → 12 is the
reporting spine, which rests only on 2 and could run in parallel with 6–8 if two agents work the
slice. Task 1 gates everything. Task 12 gates on 5, 8 and 11 together — that is the discharge
test the refusal loop's own comment states: a declaration leaves the loop when "the declaration
changes the record."

**One sequencing constraint the plan must state explicitly, or it ships a check that cannot
fail.** Tasks 5 and 7 — "Folds fit inside the clusters" and "Fold strata survive clustering" —
both need a config that declares `cluster_by`, and `E-DATA-CLUSTER-UNSUPPORTED` refuses exactly
that until task 12. Their tests would pass against a config that never reaches the check. Two
acceptable resolutions, and the plan must pick one:

- **Move the `cluster_by` retirement earlier**, splitting task 12 into "retire the declaration
  refusal" (after task 4, once the declaration changes the partition) and "refuse the clustered
  contrast" (after 11). This is closer to how H3a sequenced its own retirement, and it is the
  recommendation: the discharge test is satisfied at task 4 for the partition and re-satisfied
  at 11 for the record.
- **Or mark tasks 5 and 7's tests `xfail` until task 12 flips them**, and say so in the task
  body. H3a's plan carries `### Precondition` and `### Sequencing constraint` subsections for
  exactly this shape; mirror them rather than leaving the dependency implicit.

## 8. Traps H3a paid for

### The unit-table reconciliation

`resolved == completed + ineligible + failed`, built in `runner._counts` from `resolved`,
`len(completed)`, `ineligible`, `failed`.

**Clustering does not touch the identity directly** — a cluster-drawn partition is still an
exact cover of the roster, so `attrition`'s "with a fold, `resolved` is the union over every
declared fold's members intersected with the roster — which the partitions cover exactly" stays
true. **But it touches it indirectly, in two places:**

1. **The exact-cover property becomes an *algorithmic* guarantee rather than a structural one.**
   `shuffled[i::k]` cannot drop or duplicate a unit; a greedy cluster-to-fold assignment can. A
   dropped cluster silently reduces `resolved` and moves its units into `failed` with no error —
   H3a's exact failure shape. **Test the partition as a partition** (disjoint ∧ covering) over
   the uneven fixture, not just for cluster integrity.
2. **`k: all` changes the fold count.** If the cluster count reaches `partition_units` but not
   `_fold_k` (or vice versa), the run draws a different number of folds than
   `fold_members_for` expects, and `handed_to` scopes `completed`/`ineligible` to a fold group
   that does not exist. Both arrival paths must agree, and a test must assert they do.

`attrition` counts and never divides, so uneven fold sizes do not by themselves break
accounting: `_counts`'s body holds exactly one `len(` and no `/` at all (`sed -n '30,72p'
src/publishable/runner.py | grep -n '/\|len('` → one line, `"completed": len(completed)`), so
there is no per-fold denominator to skew. Can-fail control: `grep -c ' / ' src/publishable/stats.py`
→ 23. The one fraction in `runner.py` — `len(failed) / resolved > max_failed_fraction` — is
computed per condition over `resolved`, not per fold, so uneven folds do not reach it. That is
worth an assertion anyway: it is the only place a wrong `resolved` would fail a whole run.

### Checks that could not fail

H3a found eight. H3b's vulnerable spots, each with the discriminating form:

| Vulnerable test | Why it can't fail | The discriminating form |
|---|---|---|
| Cluster integrity with equal cluster sizes and `k` dividing the cluster count | A stride-slice already looks cluster-clean | Uneven sizes (7, 3, 3, 1, 1 at `k = 2`) **plus** a control asserting the *unclustered* partition of the same roster splits at least one cluster. This document's § 3 table is that control |
| Cluster integrity where every unit is its own cluster | Nothing can split a singleton | Probed and reported above precisely so it is never mistaken for a positive |
| Stratification over symmetric strata (6/6 over `k = 2`) | Every partition balances them | Uneven strata (9/3), and assert the realized per-fold stratum counts, not merely that the call succeeded |
| `k: all` where the cluster count happens to equal the unit count | The two numbers coincide | A fixture with strictly fewer clusters than units, and assert the fold count is the **cluster** count |
| `t_over_units_clustered` on a fixture with one unit per cluster | CR1 reduces to the ordinary t-interval | Multi-unit clusters with within-cluster correlation, and assert the clustered interval is **wider** than `t_over_units` on the same values |
| `n.clusters` where clusters = completed | The two numbers coincide | Fewer clusters than completed units, and a failed unit so `completed ≠ resolved` too |
| The bit-stability regression test | Passes trivially if the fixture has one cluster | Pin the literal seed and the literal first-fold key list from § 3 |
| The undeclared-cluster warning | Fires on a column that is also a legitimate attribute | Assert it does **not** fire on a high-cardinality column, and that it **does** on the low-cardinality one, in the same config |

### Defects that exist only in a combination

H3a shipped one: `measurements` collapsing a `weight_by` column, so core invented a weight. Its
fix is commit `4c5cf92` and now sits in § Weighted samples: "**a weight must not vary within a
unit's measurement rows**."

| Combination | Status | The defect |
|---|---|---|
| **`cluster_by` × `measurements`** | **Undocumented. The identical defect, one section over.** § Clustered units states no such rule; `grep -n cluster docs/reference.md` returns no line inside § What isn't a repeat's collapse discussion | If a `cluster_by` column varies across a unit's measurement rows, `collapse_measurements` applies `rule_for` → the `first` fallback (or `mode`), and **core invents a cluster membership no row declared** — deciding which cluster a unit belongs to by the order the file happens to be in, which then decides which fold it lands in. Strictly worse than the weight case, because it changes the partition rather than only the estimate. **Task 1 owes this sentence** |
| **`cluster_by` × `weight_by`** | **Underspecified.** § Weighted samples says only "`cluster_by` still decides the draw when both are declared," which is about resampling, not about df | With both declared, `n` would carry `effective` (Kish, H3a) *and* `clusters` (H3b), and **no document says what the interval construction is** — CR1 with df = clusters − 1, or a weighted CR1, or Kish's size. H3b must either state it or refuse the combination. The `E-DATA-WEIGHT-CONTRAST` precedent makes refusal cheap and honest |
| **`cluster_by` × `fold`** | The slice's subject | Covered by tasks 3–8 |
| **`cluster_by` × contrast** | Deferred by design | `E-DATA-CLUSTER-CONTRAST`, task 12 — the H3a precedent, confirmed to already fire on the worked example's own sweep |

### What each refusal currently masks

Retiring a refusal makes every latent defect behind it live.

**`E-DATA-CLUSTER-UNSUPPORTED` masks nine things:**

1. `partition_units` splits clusters across folds — demonstrated (S1, S2 at `k = 2`).
2. `k` is bounded by the unit count, so a `k` larger than the cluster count draws folds that
   train on the animal they test on.
3. `k: all` is leave-one-*unit*-out, and the execution budget and `W-EXEC-BUDGET` follow it.
4. `n` carries no `clusters`, so a reader cannot tell a 300-row interval from a 10-cluster one.
5. Every interval is independence-assuming; no `_clustered` construction exists in `src/` at all.
6. Contrast intervals are unclustered — the same half-delivered shape `E-DATA-WEIGHT-CONTRAST`
   was minted for.
7. **No cluster-attribute-existence check exists, and no § Validation row describes one** —
   `cluster_by: nosuch` would resolve to nothing at all.
8. **No undeclared-cluster warning fires.** Demonstrated on the probe roster: `site` holds 4
   distinct values over 20 units and draws nothing, while `W-DATA-WEIGHT-UNDECLARED` fires on
   the *same config, same command, same roster* — the can-fail control is built into the result.
9. The `measurements` collapse can invent a cluster membership (above).

**`E-REPL-FOLD-STRATIFY-UNSUPPORTED` masks four:**

1. `partition_units` has no stratification of any kind.
2. The "Stratification attribute exists" row is unwritten for the fold branch (and for the other
   two, which are H3c's and H3d's).
3. "Fold strata survive clustering" has **nowhere to live**: `_fold_k` receives no roster and no
   attributes, so the check needs a signature change or a different home.
4. **Retiring it flips the reported code** for `{k: 1, stratify_by: x}` and
   `{k: 99, stratify_by: x}`, because it is raised before `k` is resolved at all — demonstrated,
   with the no-`stratify_by` control showing which codes appear instead.

## 9. What contradicts H3-SCOPING's H3b charter

In descending order of how much it changes the plan.

1. **"4 rows" is both the wrong number and the wrong measure.** 3 owned, 1 shared three ways, 4
   touched — and two rows that do not exist yet. More importantly the row count omits the
   interval construction, the `n` part, the `W-` identifier and the `k: all` reading, which
   together are more than half the work. This is H3a's failure repeating exactly.
2. **"Rewrites `partition_units` once" is the whole charter, and it is one of twelve tasks.**
   § Clustered units' *first* sentence is about intervals, not partitions; § Statistical
   reporting names `t_over_units_clustered` and its CR1 construction outright.
3. **One item H3-SCOPING puts in H4's column is H3b's, and it is the largest of them.** The
   derived-metric percentile draw is **live today and ungated by `statistics.resample`** —
   `derived_metric_draws = 2000` is a hard constant in `cli`, whose own comment says so. § Statistical
   reporting requires that draw to resample clusters when `cluster_by` is declared, so
   un-refusing the declaration makes an already-running interval wrong. Only `statistics.resample`
   and `statistics.null_test` are genuinely H4's.
4. **"Immediately unblocks two of H4's four dependencies" overstates it.** Both rows are
   double-blocked by `E-STATS-NULLTEST-UNSUPPORTED` and `E-STATS-RESAMPLE-UNSUPPORTED`, which
   are H4's own. H3b removes one blocker of two on each; neither row becomes writable.
5. **The charter names no `W-` identifier, and H3b owes one.** H3-SCOPING listed the cluster
   warning among four to mint but did not carry it into the H3b line.
6. **One thing in H3b's favour the charter also omits:** `cluster_by` is a string leaf, so H3b
   carries **no whole-leaf schema closure** — the document says so by name — unlike H3c and H3d.
7. **A defect the charter could not have seen:** `cluster_by` × `measurements` reproduces H3a's
   shipped defect one section over, and worse, because it changes the partition rather than only
   the estimate. It is a documents-change-first obligation and it is task 1.

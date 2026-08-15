# H4 scoping — statistics

Measured against `main` at the H3b merge commit (`cb96c7d`), read-only. **The H4 charter entry in
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § the slice table predates S4, S5,
H3a, H3b, H3c-1 and H3c-2**, and it is stale in *both* directions: it lists as H4 work four things
that already ship for real, and it omits most of the surface that is genuinely unbuilt. Every claim
below was checked against the code by grep rather than against that charter.

The charter says H4 owns: *"`statistics.resample` and `null_test`; contrast, correction and
`report_by` hardening; every `repeat_spread` and per-slice `aggregate` recompute debt; **the weighted
contrast family** — `paired_t_over_units`, `paired_delta_of_derived`, `paired_percentile_of_derived`
— retiring H3a's `E-DATA-WEIGHT-CONTRAST`"*.

---

## 1. What exists

### 1.1 Interval constructions: nine built, seven named-and-absent, two built-and-unwired

Every `method=` string `stats.py` can emit, by grep of `method="` in `src/publishable/stats.py`:

| Construction | Built | Called in production |
|---|---|---|
| `t_over_units` | yes | `stats.summarize_step` |
| `t_over_units_clustered` | yes | `stats.summarize_step` |
| `weighted_t_over_units` | yes | `stats.summarize_step` |
| `weighted_t_over_units_clustered` | yes | `stats.summarize_step` |
| `paired_t_over_units` | yes | `cli._entry_for` (recorded columns) |
| `percentile_over_units` | yes | **nothing** — see below |
| `percentile_over_units_clustered` | yes | **nothing** |
| `percentile_of_derived` → emits `percentile_over_units` | yes | `stats.summarize_step` (derived metrics) |
| `paired_percentile_of_derived` → emits `paired_percentile_over_units` | yes | `cli._entry_for` (derived metrics) |
| `welch_t_over_units` | **absent** | — |
| `unpaired_percentile_over_units` | **absent** | — |
| `paired_t_over_units_clustered` | **absent** | — |
| `paired_percentile_over_units_clustered` (joint whole-cluster draw) | **absent** | — |
| `welch_t_over_units_clustered` / `unpaired_percentile_over_units_clustered` | **absent** | — |
| a clustered draw for a *derived* metric (varying row count per replicate) | **absent** | — |
| a paired percentile over a recorded **column**'s per-unit differences | **absent** | — |

**The single most useful fact for whoever implements H4:** `percentile_over_units` and
`percentile_over_units_clustered` are fully written and covered in `tests/test_stats.py`, and no
production caller exists — `grep -rn percentile_over_units src/` outside `stats.py` returns only two
`validate.py` comment lines. `summarize_step` builds a column's interval from `t_over_units` and its
three siblings only. **So the unclustered column half of `statistics.resample` is wiring, not
construction.**

### 1.2 The weighted percentile forms are *not* missing — correcting a plausible assumption

`percentile_over_units` and `percentile_over_units_clustered` both already take a
`weights: Sequence[Any] | None` parameter and recompute the weighted mean on each draw. That matches
`reference.md` § Weighted samples — *"A percentile interval draws units as usual and recomputes the
weighted statistic on each draw, so the weights are in the estimate rather than in the drawing"* —
and it is why § Statistical reporting's construction table names no separate `weighted_percentile_*`
method string. Nothing here is owed; only the caller is.

What genuinely has no weighted form is the **paired** side: `paired_t_over_units(diffs, confidence)`
takes a list of per-unit differences and nothing else, and `paired_delta_of_derived` /
`paired_percentile_of_derived` take two collapsed tables, two `compute` callables and a seed.

### 1.3 The charter's four "hardening" items already shipped

| Charter item | State |
|---|---|
| contrast hardening | `contrasts.py` resolves `vs_baseline` and declared entries; `cli._entry_for` computes deltas, `n_paired`, `cohens_dz`, `confounded`/`differs_on`, `W-STATS-CONTRAST-THIN` |
| correction hardening | `correction.py` — `Member`, `family_members`, `family_shape`, `rank_family`, `corrected_for`, `corrected_fields`; Holm/Bonferroni/`none` applied in `cli` |
| `report_by` hardening | `cli._report_by_levels` / `_condition_report_by_levels`, a per-level `summarize_step`, `W-STATS-STRATUM-THIN` |
| `repeat_spread` | `stats.repeat_spread`, wired per column in `cli`, withheld for a nested `fold` and for a `report_by` level |

What the charter *omits*: `p_value` appears **nowhere in `src/`** (`grep -rn p_value src/` → no
matches), so `null_test`, `p_value_corrected`, and the `null_test:` sibling block § What isn't a
repeat prints are unbuilt end to end; `fdr_bh` consequently corrects nothing and is warned about
under `W-STATS-CORRECTION-INAPPLICABLE`; and `limits.min_clusters` is read by no check.

### 1.4 `limits.min_clusters` is materialized, typed, and unread

`materialize.py` writes it, `envelope.py` types it `limits.min_clusters: int`, `validate.py` contains
**zero** occurrences. `reference.md` § The one config file comments it *"`validate` warns when
`resample` would draw fewer than this"* and § Validation carries the row *Clusters enough to
resample*. `stats.percentile_over_units_clustered`'s docstring deliberately declines the threshold and
routes it to that limit — but cites it as **`statistics.min_clusters`** where the schema puts it under
`limits`. That miscitation is a one-line fix H4 owns because it is the only slice that will make the
check real.

---

## 2. The refusals H4 must retire — all six verified as emitted, not merely mentioned

| Code | Emitted at | Condition | What must exist to lift it |
|---|---|---|---|
| `E-STATS-RESAMPLE-UNSUPPORTED` | `validate._check_unimplemented` | truthy `statistics.resample` | column-metric percentile wiring + `method`/`n`/`stratify_by` honored and recorded |
| `E-STATS-NULLTEST-UNSUPPORTED` | `validate._check_unimplemented` | truthy `statistics.null_test` | a permutation engine and `p_value` plumbing — nothing of either exists |
| `E-DATA-WEIGHT-CONTRAST` | `validate._check_sweep` | `weight_by` non-empty **and** ≥1 resolved comparison | the paired estimators take weights (but see § 4.3 — for a *derived* metric this may be a record change, not an estimator change) |
| `E-DATA-CLUSTER-CONTRAST` | `validate._check_sweep` | `cluster_by` non-empty **and** ≥1 resolved comparison | the five `_clustered` contrast constructions |
| `E-DATA-CLUSTER-DERIVED` | `stats.summarize_step`, **run time** | `clusters is not None and seed is not None` and ≥1 derived key has a resample callable | a clustered draw for a recomputed metric |
| `E-DATA-ALLOCATION-CONTRAST` | `validate._check_sweep`, **per comparison** | the two sides differ on an axis in `of.selectors ∪ against.selectors` | `welch_t_over_units` and `unpaired_percentile_over_units` |

All six self-describe as temporary and four name their lifting slice as H4 by name in the source
comments. Three shape facts matter for the tasking:

- **`E-DATA-WEIGHT-CONTRAST` and `E-DATA-CLUSTER-CONTRAST` read the *resolved* family**
  (`comparisons > 0`), not the declaration — so a `sweep.baseline` with no axis beside it stays legal,
  and a declared contrast over a sweep with no baseline is caught.
- **`E-DATA-ALLOCATION-CONTRAST` reads each comparison individually**, deliberately unlike its two
  siblings, so `groups × grid`'s within-arm comparisons stay computable while cross-arm ones are
  refused. Its guard uses `contrasts.differing_axes` ∩ selectors.
- **`E-DATA-CLUSTER-DERIVED` is run-time on purpose** — whether a template derives anything is not
  knowable before `aggregate` runs, and `cli` contains it by dropping the whole `derived` mapping and
  disclosing through `W-STATS-AGGREGATE-FAILED`. `reference.md` § How a metric becomes a number calls
  it *"the one row here whose absence from that table is the point"*.

---

## 3. What the documents specify — spec claims vs. build facts, kept apart

**Spec claims (four documents).**

- `reference.md` § The one config file: `resample: {method: bootstrap, n: 2000, stratify_by: []}`,
  marked `NOT BUILT`; `null_test: {method: permutation, n: 5000, shuffle: label}`, marked `NOT BUILT`.
  Both are deliberately **absent from § Errors `validate` reports**, which is why that section, not the
  registry, is where they are named.
- § Statistical reporting: *"**A derived metric is resampled whether or not you declare
  `statistics.resample`.**"* A column metric has a t-interval available so resampling it is a choice;
  a derived metric has no fallback, so core resamples with the documented default — `bootstrap` at
  `n: 2000` — *"which is why the worked example reports `method: percentile_over_units` under a config
  that declares nothing."* Declaring `resample` *"changes the method or the count rather than switching
  the behaviour on, and the resolved values are recorded in `run.yaml` beside the interval."*
- § Weighted samples: *"`resample.stratify_by` says what an independent draw is, resampling within
  each stratum so a bootstrap can't return a replicate whose stratum composition the design ruled
  out."* This is the only prose definition of resample-level `stratify_by`; § Validation carries the
  row *Resample strata exist*.
- § Clustered units and § What isn't a repeat: a draw is **rows** by default and **clusters** when
  `cluster_by` is declared, for both `resample` and `null_test`.
- § What isn't a repeat: `null_test` shuffles an attribute; what it tests depends on whether `shuffle`
  names an ordinary attribute (the metric, p-value on the metric) or a `groups` axis attribute (that
  axis's contrast, permuted within cells of every *other* group axis, p-value on the contrast in
  `vs_baseline`). **A parameter-axis contrast is explicitly out of reach** — its null is a per-unit
  sign flip and `shuffle` names an attribute.

**Build facts.**

- Derived metrics *are* already resampled with no declaration, at a hard-coded `derived_metric_draws
  = 2000` in `cli.command_run`, emitting `method: percentile_over_units` and `resample_draws: 2000`.
  **The rule in § Statistical reporting is therefore already honored; only the declaration is not.**
- `resample_draws` distinguishes `null` (never attempted) from `0` (attempted, every draw degenerate),
  and `cli` warns below `min_honest_draws()`.
- `resample.method`, `resample.n`, `resample.stratify_by` are read by nothing; `null_test` is read by
  nothing; no closed enum for either `method` exists anywhere in the four documents or in `src/`.

**Two spec gaps H4 must file rather than infer.**

1. § Validation's *Resample strata exist* row has **no error identifier** — the `E-STATS-*` set in
   `reference.md` is `CONTRAST-{NESTED,SAME-SIDES,SHAPE,UNKNOWN,WITHIN}`, `CORRECTION-UNKNOWN`,
   `REPORTBY-UNKNOWN`. H4 mints one.
2. No table enumerates the legal values of `resample.method` or `null_test.method`. `CLAUDE.md`'s
   enum-comment rule bites: the inline `# {method: bootstrap, ...}` comment must list every value the
   corresponding table defines, and there is no table.

---

## 4. The interaction that matters most

### 4.1 `E-DATA-ALLOCATION-CONTRAST` after H3c-2

H3c-1 made arms *readable* and H3c-2 made them *drawable* — `assign.method: random`/`blocked`,
`ratio`, `block_size`, `stratify_by`, whole clusters to one arm, `allocation.json`,
`provenance.allocation_hash`. The result is exactly the state the charter did not anticipate: **a user
can now randomize a parallel-arm trial and then not compare its arms.** `reference.md` § Contrasts is
explicit — *"This build refuses to compute that delta … the two sides hold disjoint units, and no
unpaired construction exists yet."*

To lift it, five things, only two of which are estimators:

1. `welch_t_over_units` — Welch's *t* on two independent condition means, Welch–Satterthwaite df.
2. `unpaired_percentile_over_units` — percentiles of the difference, resampling **within each side
   independently** (§ Statistical reporting).
3. `cli._entry_for`'s `paired` must become **derived**. Its docstring already names the exact test —
   `contrasts.differing_axes(...) ∩ (of.selectors | against.selectors)` non-empty — and says the
   hard-coded `True` *"expires with `E-DATA-ALLOCATION-CONTRAST`"*. Leaving it would publish
   `paired: true` on an unpaired contrast, which is the record fault the refusal exists to prevent.
4. `cohens_d` must select *d*s (pooled within-condition SD) for an unpaired contrast against *d*z for
   a paired one — § Statistical reporting states both and states why *d*s pools where
   `welch_t_over_units` deliberately does not.
5. **A spec gap:** nothing in the four documents says what an unpaired contrast records where
   `n_paired` goes. `stats.paired_keys` over two disjoint arms is empty by construction, so the field
   cannot simply be reused. File it.

### 4.2 Is that the same work as the weighted contrasts? **No.**

| | Weighted contrasts | Unpaired contrasts |
|---|---|---|
| Shape | an added parameter on functions that exist | two constructions written from nothing |
| Non-estimator work | a `weighted_by` key beside the delta | `paired` derived, `cohens_d` branch, the `n_paired` gap |
| Evidence payoff | **3 of 9** feasibility experiments (C1, C2, C3) | **0 of 9** — no config declares `sweep.groups` |
| Blocked on | nothing; H3a landed `weight_by` | nothing further; H3c-1/H3c-2 discharged it |

### 4.3 The weighted refusal is *narrower* than its own message — H4b task 1

`E-DATA-WEIGHT-CONTRAST`'s message and the charter both say the fix is *"the paired estimators take
weights"*, naming `paired_t_over_units`, `paired_delta_of_derived`, `paired_percentile_of_derived`.
But `stats.summarize_step`'s docstring already settles the derived half one level down, from
§ Weighted samples: a derived metric *"is not weighted here"* because there is no per-unit vector to
weight — the weight column reaches `aggregate` as a unit attribute (`cli._attributed`) and the
template decides. That argument transposes directly onto the paired derived forms: their draws are
uniform over the paired intersection and the weighting lives inside `aggregate`.

**This matters because C1, C2 and C3 — the three experiments this refusal blocks — all carry a
*derived* AUROC** (`docs/feasibility-llm-growth-studies.md` § C1: *"AUROC is derived from the per-unit
`prob`/`consensus_label` columns by the template's `aggregate`"*), alongside `weight_by:
sampling_weight` and `resample: {method: bootstrap, n: 2000, stratify_by: [...]}`. So the weighted
work H4 actually owes for the measured payoff is: a weighted `paired_t_over_units` (recorded columns),
a decision + record change for the derived side, and a stratified bootstrap.

**This is H4b's first task, not an observation:** *settle and file — does a weighted **derived**
contrast need weighted estimators, or only `weighted_by` in the record?* It must be settled before the
other weighted tasks are estimated, because it decides whether two of the three functions the refusal
message names are touched at all, and it must be filed in `docs/superpowers/spec-defects.md` because
it narrows a published refusal message and a charter line.

---

## 5. Traps

1. **A declared `resample.n` can silently null every corrected interval, and the threshold is
   measured.** Correction re-reads the draw pool at a wider confidence level
   (`correction._level_for`, `correction.interval_at`), and `cli` already emits
   `W-STATS-CORRECTED-THIN` when a corrected level *"the resample's draws cannot support"* is
   requested. Evaluated: `stats.min_honest_draws` needs **80** draws at 0.95, **400** at Holm's
   tightest level in a 5-comparison family (α = 0.01), **800** at 10 comparisons, **1601** at 20. So
   `resample: {n: 500}` is fine at five comparisons and nulls `ci95_corrected` on **every** metric at
   ten — with only a warning, in a family the config never states the size of. `validate` must bound
   `n` against **family size** (comparisons × metrics), not only against `min_honest_draws()` at 0.95.
2. **An undeclared-`resample` config must produce byte-identical output after H4.** Derived metrics
   already resample at 2000 draws emitting `method: percentile_over_units` — that is exactly what the
   worked example prints (`reference.md` § Statistical reporting, § What isn't a repeat). Wiring the
   declaration must not shift a method string, must not change `resample_draws: 2000`, and must not
   narrow intervals `CLAUDE.md` § The worked example says were checked numerically and *"must not be
   narrowed back"*. Name it as a regression task, not an assumption.
3. **The correction family is comparisons × metrics, and resampling must not enlarge it.** Three
   distinct ways H4 can break it: (a) a `report_by` level's `summarize_step` gaining a resampled
   interval must **not** mint `Member`s — a stratum repeats metrics and joins no family; (b) a
   `summary`-step `Estimate` is `reported: true`, outside the family, and **never recomputed** — a
   resample pass that walks every metric block must skip it; (c) `null_test` p-values must not change
   how Holm **ranks**. `CLAUDE.md`'s invariant is that Holm ranks on the point estimate over half the
   raw `ci95` width *because the family often carries no p-value at all*; switching to p-ranking the
   moment p-values exist is a design change against `design-principles.md`, not an improvement.
4. **`cohens_d` stays `null` for a derived metric.** The worked example depends on it (`r` is derived
   by `aggregate`, so there is no per-unit value to difference). A slice touching effect sizes is
   exactly where someone helpfully reintroduces one.
5. **A stratified bootstrap × `cluster_by` needs a stated composition rule.** `stratify_by` says what
   an independent draw is; `cluster_by` says the draw is a cluster. § Clustered units already requires
   a stratum be constant within a cluster for `fold`, `holdout` and `assign` — resample needs the same
   rule stated, or the two declarations disagree about what one draw is.

---

## 6. Decomposition: ≈54 tasks. **Split it — four ways.**

Against H3a's 12, H3b's 13, H3c-1's 20 and H3c-2's 14, H4 as chartered is four slices' worth.

| Sub-slice | Owns | Retires | Tasks |
|---|---|---|---|
| **H4a — `resample` honored** | closed schema for the block; `method`/`n`/`stratify_by` checked and honored; column-metric percentile wiring (the two unwired functions); stratified draw; a paired percentile over a column's differences; `derived_metric_draws` from `resample.n`; resolved values echoed into `run.yaml`; `limits.min_clusters` made real; `report_by` levels resample without minting `Member`s; the `init`-materializes-optional-blocks residual `spec-defects.md` routes to H4 by name | `E-STATS-RESAMPLE-UNSUPPORTED` | **15** |
| **H4b — weights and clusters through the contrast family** | weighted paired *t*; the derived-weighting decision of § 4.3 and its record key; `paired_t_over_units_clustered`; `paired_percentile_over_units_clustered` (one joint whole-cluster draw); the clustered derived draw; `effective`/`clusters` beside `n_paired`; correction `Member` evidence over the right pool; three guards deleted with their tests | `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`, `E-DATA-CLUSTER-DERIVED` | **14** |
| **H4c — the unpaired family** | `welch_t_over_units`, `unpaired_percentile_over_units`, their clustered and weighted counterparts; `paired` derived in `cli._entry_for`; `cohens_d` *d*s/*d*z branch; the unpaired point-estimate path (`paired_keys` no longer applies); the `n_paired` spec gap | `E-DATA-ALLOCATION-CONTRAST` | **12** |
| **H4d — `null_test`** | the permutation engine; `p_value` / `p_value_corrected` plumbing; attribute-shuffle vs. group-axis-shuffle routing; cluster-level permutation; `fdr_bh` made real for the first time; `W-STATS-CORRECTION-INAPPLICABLE` narrowed; validate checks (`shuffle` names an attribute, collides with no recorded column, an all-permuted design has no unpermuted value) | `E-STATS-NULLTEST-UNSUPPORTED` | **13** |

**The seam is evidence payoff, not construction family** — and that is the non-obvious part. A
family-by-family split (t-forms, then percentile forms, then contrasts) reads tidier and delivers
nothing measurable: of the nine feasibility experiments, clustered contrasts unblock **0**, unpaired
contrasts unblock **0**, and `null_test` unblocks **0**. The measured payoff is `resample` (8/9) and
the weighted contrast (3/9), and C1–C3 need **both together** — they declare `weight_by`, a
`baseline`, *and* `resample` in one config.

**So: H4a and H4b's weighted half must ship together, or H4 delivers zero of the nine.** If 14 is too
large for H4b, the clean seam inside it is weights (3/9) versus clusters (0/9), and the cluster half
can ride with H4c, which is the same construction work one level over.

Ordering: **H4a → H4b → H4c → H4d.** H4d last on its own merits — it is the only sub-slice with no
existing code to build on, and it is the one that can silently corrupt the correction family.

---

## 7. What is NOT in H4

- **H7a — the template registry.** `E-TEMPLATE-UNKNOWN` gates **9 of 9** feasibility experiments and
  H4 cannot move that number alone. The amended order in the charter is H7a → H4 → H3d.
- **`data.units.holdout`** (`E-DATA-HOLDOUT-UNSUPPORTED`, 6/9) — H3d.
- **The plugin registry and `from: {resolver: …}`** (`E-DATA-RESOLVER-UNSUPPORTED`) — full H7. Without
  it the nine run only with a table roster.
- **Folds within cells** — H3c-3, including the holdout-cells retrofit H3d inherits.
- **`study` / `report` / `diff` / `freeze`** — H8, which is ordered after H4.
- **An `Estimate` returned by a `summary` step** — recorded as `reported: true` and never recomputed.
  No H4 sub-slice may touch it; it is the documented route every one of these six refusals offers.
- **Interactions, dose-response orderings, differences-in-differences, adaptive selection.** Contrasts
  do not nest. Nothing in H4 makes them expressible, and a p-value arriving in H4d is not a reason to
  revisit that.
- **`W-STATS-REPORTBY-THIN`'s whole-roster-versus-arm gap** — recorded in `spec-defects.md` as live
  since `sweep.groups` landed, and currently ownerless. **H4 should claim it explicitly under
  "`report_by` hardening" or explicitly decline it**; silence is how it went stale the first time.
  Recommendation: claim it in H4a, where the `report_by` code is already open.

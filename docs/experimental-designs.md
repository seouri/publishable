# Experimental designs

What `publishable` expresses, what it refuses to let you get wrong, and what it deliberately leaves to you. If you've designed experiments for a living, start here — it's the fastest way to judge whether the model fits your work.

## Contents

- [Designs, and how to express them](#designs-and-how-to-express-them)
- [Mistakes core prevents](#mistakes-core-prevents)
- [What core will not do for you](#what-core-will-not-do-for-you)

---

## Designs, and how to express them

Three declarations cover most of it: **allocation** (do units appear in every condition, or one?), **sweep** (what varies deliberately), and **repeats** (what varies incidentally).

### Three questions, answered independently

Resolve the three declarations separately and the config writes itself. They are not alternatives — most real designs answer all three, and the catalog below shows each answer in isolation only to keep the snippets short.

| The question | Declaration | Values | Shown in |
|---|---|---|---|
| Does every unit appear in every condition, or exactly one? | `data.units.allocation` | `within` (default, paired comparisons) · `between` (one arm per unit, unpaired across arms — needs a `groups` axis) | [Within-subjects](#within-subjects--repeated-measures) · [Between-subjects](#between-subjects--parallel-arm-trial) |
| What varies deliberately? | `sweep` | `grid` (cartesian) · `paired` (coupled axes) · `ablate` (`1 + n`, one change each) · `sample` (continuous ranges) · `groups` (arms of units, not parameters) · `baseline` (the reference, not an axis) | [Factorial](#factorial) · [Fractional factorial](#fractional-factorial-and-coupled-settings) · [Ablation](#ablation) · [Dose-response](#dose-response-and-parameter-search) · [Between-subjects](#between-subjects--parallel-arm-trial) |
| What varies incidentally? | `replication.repeats` | `seed` · `fold` — the two things a re-execution can change | [Single condition](#single-condition-repeated) · [Cross-validation](#cross-validation) |

Answering a question with nothing is a valid answer: omit `sweep` for a single condition, omit `data.units` entirely when the pipeline has no unit table — though `fold` requires one, as do the resampling and permutation statistics in [Bootstrap and permutation](#bootstrap-and-permutation). A design that evaluates on held-out units without repeating anything answers the third question with nothing too, and declares [`data.units.holdout`](#train-test-holdout) instead of a repeat. What each repeat kind varies and how core collapses it is the table in [reference.md § Repeat kinds](reference.md#repeat-kinds) — both differ per kind, and that's the point of naming the kind rather than passing a count. What no repeat kind does is set `n`: that counts units, and every interval core reports comes from the [per-unit table](reference.md#the-unit-table-is-the-inference-base).

Three choices sit *below* an answer rather than beside it. `assign.method` (`random` | `by_attribute` | `blocked`) only applies once allocation is `between`, and it answers a narrower question than the axis does — the `groups` axis says what the arms are, `assign.method` says how a unit reaches one. `cluster_by` sits below all three rather than beside them — it declares that units aren't independent, which widens the intervals. It is *not* independent of the other answers, though: because a cluster is indivisible, declaring it also constrains how `fold` splits and how `between` allocation assigns, so whole clusters stay on one side of every partition. See [Clustered and hierarchical data](#clustered-and-hierarchical-data) and [Matched case-control](#matched-case-control). `data.units.holdout` sits below the third question without being an answer to it — a single train/test split divides the units once and repeats nothing, so it's a declaration about the table rather than a repeat kind. See [Train-test holdout](#train-test-holdout).

### Single condition, repeated

The baseline case. No sweep at all.

```yaml
replication:
  repeats: [{kind: seed, n: 10}]
```

### Within-subjects / repeated measures

Every unit is measured under every condition. This is the default, and comparisons are paired automatically. Core doesn't model the *order* each unit met the conditions in, so counterbalancing and carryover effects are yours — see [what core will not do](#what-core-will-not-do-for-you).

```yaml
data:
  units: {from: index.csv, key: subject_id, allocation: within}
sweep:
  baseline: {stimulus.contrast: 0.2}
  grid:
    stimulus.contrast: [0.4, 0.8]
```

### Between-subjects / parallel-arm trial

Each unit belongs to exactly one arm. The arms are a `groups` axis — the difference between them is something that happened to the units, not a parameter the pipeline varies — and `allocation` says how a unit reaches one. Core does the randomization, balances it, and records who went where.

```yaml
sweep:
  groups:
    by: arm                           # → 00_arm=control, 01_arm=treatment
    levels: [control, treatment]

data:
  units:
    from: enrollment.csv
    key: patient_id
    attributes: [site, severity]
    allocation: between
    assign:
      method: random
      stratify_by: [site, severity]
      ratio: {control: 1, treatment: 1}
      seed: auto
```

The realized allocation lands in `allocation.json`, hashed. The arm-to-arm comparison is unpaired, derived from the fact that the two conditions differ on the `groups` axis rather than declared separately — and if you compose a parameter axis on top, contrasts *within* an arm stay paired, because they're the same patients analyzed two ways. The two conditions share a `parameters_hash`, which is the point: same code, same parameters, different units.

`seed: auto` derives from a design digest over `data.units` and `sweep.groups`, not from `parameters_hash`, so arm membership doesn't move when you edit an analysis parameter. It does move if the roster does — core draws over the units resolved at run start and carries nothing forward from a previous run — so for a design you intend to cite, pin the seed to an integer and keep the `allocation.json` it produced. Prospective enrollment isn't something any `assign.method` supports; see [reference.md § What `auto` derives from](reference.md#what-auto-derives-from).

When the arm was decided elsewhere — a trial system, a registry, an exposure that simply happened — name the column instead of a seed, and core assigns nothing:

```yaml
data:
  units:
    from: enrollment.csv
    key: patient_id
    attributes: [site, severity, arm]
    allocation: between
    assign: {method: by_attribute, from: arm}
```

### Factorial

Full factorial is `grid` over two or more axes.

```yaml
sweep:
  grid:
    drug.dose: [0, 10, 20]
    diet.type: [control, high_fat]
  # 3 × 2 = 6 conditions
```

Core reports each condition and its contrast against the baseline. **Main effects and interaction terms are not computed** — see [what core will not do](#what-core-will-not-do-for-you). For a 2×2 that's often fine; for anything you intend to analyze as a factorial model, plan on a `scope: "summary"` step, which is the scope that can see every condition at once.

### Fractional factorial and coupled settings

Use `paired` when factors must move together rather than combinatorially — coupled settings, where a solvent implies its temperature:

```yaml
sweep:
  paired:
    - {solvent: dmso, temp_c: 25}
    - {solvent: etoh, temp_c: 37}
```

A fractional factorial is the same mechanism used differently: `paired` enumerates whichever subset of the full factorial your design calls for. Be clear-eyed about the division of labour, though — core will run a fraction and report each condition against the baseline, but **the fraction's purpose is estimating main effects from fewer runs, and that estimation is not core's**. You choose the fraction and its defining relation, and you fit the effects in a summary step. Core contributes the execution, the provenance, and the per-unit tables; it does not know your design is a fraction of anything.

### Ablation

`1 + n` conditions, not `2^n`.

```yaml
sweep:
  baseline: {features.demographics: true, features.labs: true, features.notes: true}
  ablate:
    from: baseline
    remove: [features.demographics, features.labs, features.notes]
  # 00_baseline + 3 ablations = 4 conditions
```

`ablate` reads the baseline rather than re-emitting it, so the full model appears once. It requires `sweep.baseline` and composes with no other *parameter* mode — crossing "one change at a time" with a second parameter axis stops being one change at a time.

It does compose with `groups`, which varies no parameter: `groups: {by: cohort, levels: [derivation, validation]}` alongside the above gives `2 × (1 + 3) = 8` conditions, each still one change from its own arm's baseline. That's the ablation repeated per cohort, and it's the one composition that leaves "one change at a time" intact. See [reference.md § Expansion modes](reference.md#expansion-modes).

### Dose-response and parameter search

Discrete levels via `grid`; continuous ranges via `sample`.

```yaml
sweep:
  sample:
    n: 40
    method: sobol
    ranges:
      drug.dose_mg: {log_uniform: [0.1, 100]}
```

Fitting the dose-response curve is a `scope: "summary"` step; core supplies the conditions and the per-unit tables, not the curve model.

Because the conclusion is the fit rather than any one draw, sampled conditions are excluded from the multiplicity family and `correction: none` draws no warning here — the forty draws are inputs to one model, not forty comparisons. See [reference.md § Sweeps and repeats](reference.md#sweeps-and-repeats).

### Train-test holdout

Fit on most of the units, evaluate on the rest, once. It's a property of the unit table rather than a repeat, because nothing repeats — the split is drawn once and fixed for the run:

```yaml
data:
  units:
    from: index.csv
    key: patient_id
    attributes: [label]
    holdout: {method: random, frac: 0.2, stratify_by: [label], seed: auto}
```

`io.units` is the test partition and `io.units.train` the training one. When the split already exists — as it does for most benchmark datasets — name the column instead and core partitions rather than draws: `holdout: {method: by_attribute, from: split}`.

`n` is the test partition, so a 20% holdout over 240 units reports intervals over 48 units. That's the honest denominator, and it's the reason to reach for [cross-validation](#cross-validation) instead when 48 is too few to say anything with — every unit gets a turn in the test set there, without any of them being evaluated by a model that trained on it. The two are mutually exclusive; see [reference.md § A fixed holdout split](reference.md#a-fixed-holdout-split).

### Cross-validation

```yaml
replication:
  repeats:
    - {kind: fold, k: 10, stratify_by: label}
    - {kind: seed, n: 3}
```

Core computes the partitions and records exact split membership, so the CV is reproducible rather than merely re-runnable. Aggregation is inner-to-outer: seeds within a fold, then folds across the condition.

Leave-one-out is `k: all` — as many folds as there are units, or as there are clusters when `cluster_by` is declared. Spell it that way rather than as `k: 240`, which hard-codes a cohort size the config doesn't control and quietly stops meaning leave-one-out when a unit is added. Budget for it before declaring it: `k: all` over 240 units across 3 conditions is 720 executions.

Each fold execution is handed only its test partition, so its `n` is over those units — a 10-fold run over 240 units reports `resolved: 24` per execution, not 24 completions against a cohort of 240. The condition's `n` returns to the full roster, because each unit is tested exactly once per fold sweep. See [reference.md § What isn't a repeat](reference.md#what-isnt-a-repeat) for the three levels `n` is reported at and which one carries the failure threshold.

That's **repeated** cross-validation — 10 folds, each evaluated under 3 seeds. It is not nested cross-validation, and the difference is not cosmetic: in nested CV an inner loop runs *within each outer training split* and its result **selects** the setting the outer loop then evaluates. That's a condition chosen from results, which is [exactly what core refuses](design-principles.md#what-core-does-not-promise) — the config would no longer determine the run.

So the outer loop is core's and the selection is yours: declare the outer `fold`, and do the inner search inside the step, over `io.units` for that fold's training partition only. The selected setting is then a value your step records per fold rather than a condition, which is also the honest description of it — a hyperparameter chosen by the pipeline is an output, not a declared parameter.

### Bootstrap and permutation

Neither is a repeat, because neither needs the pipeline to run again — both resample the per-unit table the run already produced. They're declared under `statistics` and cost no executions:

```yaml
statistics:
  resample: {method: bootstrap, n: 2000}                    # percentile CI, not t-based
  null_test: {method: permutation, n: 5000, shuffle: label} # null distribution + p-value
```

As repeat kinds these would have meant 2,000 and 5,000 full executions to compute what a resampled table gives directly, and a permutation design in which *every* execution is permuted has no unpermuted value to test against. Both need a metric core can recompute — a per-unit column, or a template `aggregate(units, cfg)`.

Both also follow `cluster_by`, because both depend on what an independent draw is. With a cluster declared, the bootstrap resamples whole clusters rather than rows — resampling rows would make every resample too alike and the interval too narrow — and the permutation shuffles within clusters when the shuffled attribute varies inside one, or whole clusters at a time when it doesn't. See [reference.md § Clustered units](reference.md#clustered-units).

### Technical and biological replication

Biological replicates ARE units. Technical replicates are extra measurement rows of the same unit, declared where units are resolved — not re-executions of the pipeline, which would recompute the same answer:

```yaml
data:
  units:
    from: reads.csv
    key: sample_id                             # 3 rows per sample_id
    measurements: {by: read_id, collapse: mean}   # or median | sum | first | mode, or per column
```

Rows sharing a key collapse into one unit before any step sees them, so technical replicates can never reach `n`. This is the single most consequential mapping in the whole model for bench work, and the direction matters: the three reads are a fact about your data file, not three runs of anything.

### Clustered and hierarchical data

```yaml
data:
  units: {from: index.csv, key: cell_id, attributes: [animal_id], cluster_by: animal_id}
```

Core reports cluster-robust intervals and the cluster count as effective sample size. Full mixed-effects modelling is an override.

Declaring the cluster also changes how the data is split, which is the part that affects the number rather than the interval around it. Add `{kind: fold, k: 5}` to the above and each fold holds out whole animals — cells from one animal never appear in both the training and test side, so the metric isn't inflated by having seen its littermates. `k` is then bounded by the animal count rather than the cell count. See [reference.md § Clustered units](reference.md#clustered-units).

### Matched case-control

Case-vs-control is a property of the units, so it's a `groups` axis read from an existing column — nothing here is randomized. Matching happens upstream; carry the matched-set identifier as an attribute and cluster on it, which is what tells core the two arms aren't independent samples.

```yaml
sweep:
  groups: {by: status, levels: [control, case]}

data:
  units:
    from: matched.csv
    key: subject_id
    attributes: [status, match_set]
    allocation: between
    assign: {method: by_attribute, from: status}
    cluster_by: match_set
```

Core reports each arm and their contrast with intervals clustered on `match_set`. That accounts for the matching in the intervals; it is not a conditional analysis, and if your field expects conditional logistic regression or a stratified estimator, that's a `scope: "summary"` step — see [what core will not do](#what-core-will-not-do-for-you).

Adding `statistics.null_test` here does give you a conditional *test*, because `cluster_by` sets the level it shuffles at. `status` varies inside a matched set, so labels are permuted within each set independently — a case/control swap inside each pair — which is the classic matched permutation test rather than a free relabelling that would throw the matching away. `statistics.resample` likewise draws whole matched sets, and its interval's effective `n` is the number of sets, not the number of subjects.

---

## Mistakes core prevents

The design is shaped around a specific claim: most irreproducible results are not fraud or incompetence, but ordinary bookkeeping failures that nothing in the toolchain was watching for. These are the ones core watches.

### Statistical

| Mistake | What core does |
|---|---|
| **Repeats counted as `n`** | `n` counts units, always. Every interval is computed from the per-unit table; repeat dispersion is reported separately as `repeat_spread`, so an interval that would narrow as you add seeds is never presented as evidence about a population |
| **A confidence interval on a number core can't recompute** | A metric that exists only as a scalar a step returned is reported as `basis: repeats` with **no interval**, rather than one over executions. Giving it an interval means making it a per-unit column or deriving it in the template's `aggregate(units, cfg)` |
| **Technical replicates counted as `n`** | They collapse into the unit at resolution, before any step runs, so they cannot reach `n`. `{kind: biological}` is rejected with a pointer to the unit table |
| **t-intervals over bootstrap resamples** | `statistics.resample` produces percentile intervals and `statistics.null_test` a null with a p-value, both over the unit table — a t-interval is never applied to resamples |
| **Technical replicates dressed as executions** | Technical replication is `data.units.measurements`, collapsed at unit resolution. Re-running an identical step to average it away would compute the same answer three times |
| **Pooling across conditions** | Statistics aggregate within a condition only. Cross-condition comparison is an explicit contrast against a declared baseline |
| **Paired analysis of an unpaired design** | Comparison type derives from `allocation` and from which axes the contrast crosses, so it can't disagree with how units were actually assigned. Derived per contrast, so a composed design doesn't get one verdict applied to comparisons of both kinds |
| **Uncorrected multiplicity across a sweep** | `statistics.correction` reports family-wise or FDR-adjusted intervals alongside raw ones; `validate` warns when a multi-condition *enumerated* sweep declares `none`. `sample` draws are excluded — they feed one downstream fit rather than being comparisons a reader acts on |
| **Ignored clustering** | `cluster_by` produces cluster-robust intervals; `validate` flags an attribute that looks like an undeclared cluster |
| **A cluster split across train and test** | A declared `cluster_by` makes clusters indivisible in every partition core computes, so a fold can't train on one cell of an animal and test on another. `validate` rejects a `k` above the cluster count |
| **Resampling clustered rows as if independent** | A declared `cluster_by` makes the cluster the bootstrap draw, so 300 cells from 10 animals give a 10-draw interval rather than a 300-draw one that looks ten times more precise than the data supports |
| **A permutation that shuffles away the matching** | `null_test` shuffles at the level the shuffled attribute lives at — within clusters when it varies inside one, whole clusters when it doesn't — so a matched design gets a conditional test instead of a free relabelling |
| **Silent attrition** | Every metric reports units resolved, completed, and failed — never a bare `n` that hides dropout. Each count is scoped to what its execution was handed, so a fold or an arm isn't charged with units it never saw |
| **Hypotheses invented after seeing results** | A hypothesis carries the `parameters_hash` of the config that declared it; anything added later doesn't match, and undeclared analyses render as exploratory |

### Bookkeeping

| Mistake | What core does |
|---|---|
| **"Which parameters produced this figure?"** | Every run writes `run.yaml` with the config embedded verbatim and hashed, plus each condition's resolved values |
| **A parameter changed *and* the code changed** | `code_hash` and `parameters_hash` are separate, so a single-variable comparison is provable rather than asserted |
| **Results overwritten by a rerun** | Artifacts are append-only and atomic; each run gets its own `run_<id>/`. Nothing is ever deleted |
| **Uncommitted code in a reported run** | `run` refuses a dirty `src/**`; `draft` permits it but marks the run non-citable |
| **The input data changed underneath you** | A content manifest is captured at run start and re-verified after; `reproduce` compares against the recorded hash |
| **A typo'd parameter silently using a default** | `init` materializes every valid key, so any unrecognized key is a typo by construction and fails validation |
| **Resuming into a different experiment** | `resume` refuses when `parameters_hash`, `code_hash`, or `uv.lock` have moved |
| **A stale summary reported as fresh** | Steps that consume an earlier run's artifacts record it as an upstream with its hashes |
| **Confounding by run order** | `order: randomized` shuffles execution under a recorded seed; the realized order is recorded either way |
| **Credentials in a shared config** | The config stores variable names; values live in `.env` and are never captured, logged, or written to any artifact |
| **Patient data in a public repo** | `input_dir` and `output_dir` may not resolve inside the repo, checked at generate, validate, and run |

---

## What core will not do for you

Being explicit about this matters more than the feature list, because a tool that quietly does the wrong statistic is worse than one that declines.

**Modelling beyond summary statistics.** Mixed-effects and hierarchical models, factorial main effects and interactions, survival analysis with censoring, ordinal and count outcomes, and curve fitting are all out of scope for core aggregation, which computes means, derived scalars, and intervals over the per-unit table. That table is the right input for any of these — bring your own model in a `scope: "summary"` step, or derive the quantity you need in a template's `aggregate(units, cfg)`, which is also what gives it an interval.

**Crossover order and counterbalancing.** [Within-subjects](#within-subjects--repeated-measures) means every unit is measured under every condition, and core pairs the comparison accordingly — but it has no notion of the *order* a given unit met the conditions in, so it can neither counterbalance that order nor estimate a carryover or period effect. `replication.order: randomized` shuffles the order executions run in, which protects against drift in an instrument or a service; it is not a per-unit condition sequence, and reading it as one would be a mistake worth avoiding. A true crossover design needs the sequence to be a property of the unit: carry it as an attribute, make the sequences a `groups` axis if you want to compare them, and fit the period terms in a `scope: "summary"` step.

**Power analysis.** Core enforces a template's minimum repeat count but does not compute power or required sample size. If your field expects an a-priori calculation, record it as a parameter so it's part of the pre-registered config.

**Adaptive and sequential designs.** Bayesian optimization, response-adaptive randomization, dose escalation, and interim-analysis stopping rules all decide the next condition from results so far, which contradicts the config fully determining the run. See [design principles](design-principles.md#what-core-does-not-promise).

**Deciding whether your design answers your question.** A config that validates is well-formed and well-recorded. Everything above catches errors of *bookkeeping and inference mechanics*; none of it substitutes for having designed the right experiment.

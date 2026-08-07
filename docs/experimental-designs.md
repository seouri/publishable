# Experimental designs

What `publishable` expresses, what it refuses to let you get wrong, and what it deliberately leaves to you. If you've designed experiments for a living, start here — it's the fastest way to judge whether the model fits your work.

## Contents

- [Designs, and how to express them](#designs-and-how-to-express-them)
- [Mistakes core prevents](#mistakes-core-prevents)
- [What core will not do for you](#what-core-will-not-do-for-you)

---

## Designs, and how to express them

Three declarations cover most of it: **allocation** (do units appear in every condition, or one?), **sweep** (what varies deliberately), and **repeats** (what varies incidentally).

### Single condition, repeated

The baseline case. No sweep at all.

```yaml
replication:
  repeats: [{kind: seed, n: 10}]
```

### Within-subjects / repeated measures

Every unit is measured under every condition. This is the default, and comparisons are paired automatically.

```yaml
data:
  units: {from: index.csv, key: subject_id, allocation: within}
sweep:
  baseline: {stimulus.contrast: 0.2}
  grid:
    stimulus.contrast: [0.4, 0.8]
```

### Between-subjects / parallel-arm trial

Each unit is allocated to exactly one arm. Core does the randomization, balances it, and records who went where.

```yaml
data:
  units:
    from: enrollment.csv
    key: patient_id
    attributes: [site, severity]
    allocation: between
    assign:
      method: blocked                 # permuted blocks keep arms balanced during enrollment
      stratify_by: [site, severity]
      ratio: {00_control: 1, 01_treatment: 1}
      seed: auto
```

The realized allocation lands in `allocation.json`, hashed. Comparisons are unpaired, derived from `allocation: between` rather than declared separately.

### Factorial

Full factorial is `grid` over two or more axes.

```yaml
sweep:
  grid:
    drug.dose: [0, 10, 20]
    diet.type: [control, high_fat]
  # 3 × 2 = 6 conditions
```

Core reports each condition and its contrast against the baseline. **Main effects and interaction terms are not computed** — see [what core will not do](#what-core-will-not-do-for-you). For a 2×2 that's often fine; for anything you intend to analyze as a factorial model, plan on an `aggregate()` override.

### Fractional factorial and coupled settings

Use `paired` when factors must move together rather than combinatorially.

```yaml
sweep:
  paired:
    - {solvent: dmso, temp_c: 25}
    - {solvent: etoh, temp_c: 37}
```

### Ablation

`1 + n` conditions, not `2^n`.

```yaml
sweep:
  ablate:
    from: baseline
    remove: [features.demographics, features.labs, features.notes]
```

### Dose–response and parameter search

Discrete levels via `grid`; continuous ranges via `sample`.

```yaml
sweep:
  sample:
    n: 40
    method: sobol
    ranges:
      drug.dose_mg: {log_uniform: [0.1, 100]}
```

Fitting the dose–response curve is a `scope: "summary"` step; core supplies the conditions and the per-unit tables, not the curve model.

### Cross-validation, including nested

```yaml
replication:
  repeats:
    - {kind: fold, k: 10, stratify_by: label}
    - {kind: seed, n: 3}
```

Core computes the partitions and records exact split membership, so the CV is reproducible rather than merely re-runnable. Aggregation is inner-to-outer: seeds within a fold, then folds across the condition.

### Bootstrap and permutation

```yaml
replication:
  repeats: [{kind: bootstrap, n: 2000}]     # percentile CI, not t-based
```

```yaml
replication:
  repeats: [{kind: permutation, n: 5000, shuffle: label}]   # null distribution + p-value
```

Neither contributes to `n`, because resamples and nulls are not observations.

### Technical and biological replication

```yaml
data:
  units: {from: samples.csv, key: sample_id}   # biological replicates ARE units
replication:
  repeats: [{kind: technical, n: 3}]           # 3 reads per sample, averaged in
```

Technical repeats collapse into the unit before any statistic runs and never enter `n`. This is the single most consequential mapping in the whole model for bench work.

### Clustered and hierarchical data

```yaml
data:
  units: {from: index.csv, key: cell_id, attributes: [animal_id], cluster_by: animal_id}
```

Core reports cluster-robust intervals and the cluster count as effective sample size. Full mixed-effects modelling is an override.

### Matched case–control

Matching happens upstream; carry the matched-set identifier as an attribute and cluster on it.

```yaml
data:
  units: {from: matched.csv, key: subject_id, attributes: [match_set], cluster_by: match_set}
```

---

## Mistakes core prevents

The design is shaped around a specific claim: most irreproducible results are not fraud or incompetence, but ordinary bookkeeping failures that nothing in the toolchain was watching for. These are the ones core watches.

### Statistical

| Mistake | What core does |
|---|---|
| **Technical replicates counted as `n`** | `{kind: technical}` collapses into the unit and never enters `n`. `{kind: biological}` is rejected with a pointer to the unit table |
| **t-intervals over bootstrap resamples** | Aggregation is chosen by repeat kind; bootstrap gets percentile intervals, permutation gets a null and a p-value |
| **Pooling across conditions** | Statistics aggregate within a condition only. Cross-condition comparison is an explicit contrast against a declared baseline |
| **Paired analysis of an unpaired design** | Comparison type derives from `allocation`, so it can't disagree with how units were actually assigned |
| **Uncorrected multiplicity across a sweep** | `statistics.correction` reports family-wise or FDR-adjusted intervals alongside raw ones; `validate` warns when a multi-condition sweep declares `none` |
| **Ignored clustering** | `cluster_by` produces cluster-robust intervals; `validate` flags an attribute that looks like an undeclared cluster |
| **Silent attrition** | Every metric reports units resolved, completed, and failed — never a bare `n` that hides dropout |
| **Hypotheses invented after seeing results** | A hypothesis carries the `parameters_hash` of the config that declared it; anything added later doesn't match, and undeclared analyses render as exploratory |

### Bookkeeping

| Mistake | What core does |
|---|---|
| **"Which parameters produced this figure?"** | Every run writes `run.yaml` with the full resolved parameter set embedded and hashed |
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

**Modelling beyond summary statistics.** Mixed-effects and hierarchical models, factorial main effects and interactions, survival analysis with censoring, ordinal and count outcomes, and curve fitting are all out of scope for core aggregation, which handles numeric scalars per condition. The per-unit tables `io.record` produces are the right input for any of these — bring your own model in a `scope: "summary"` step, or override `aggregate()` in a template.

**Power analysis.** Core enforces a template's minimum repeat count but does not compute power or required sample size. If your field expects an a-priori calculation, record it as a parameter so it's part of the pre-registered config.

**Adaptive and sequential designs.** Bayesian optimization, response-adaptive randomization, dose escalation, and interim-analysis stopping rules all decide the next condition from results so far, which contradicts the config fully determining the run. See [design principles](design-principles.md#what-core-does-not-promise).

**Deciding whether your design answers your question.** A config that validates is well-formed and well-recorded. Everything above catches errors of *bookkeeping and inference mechanics*; none of it substitutes for having designed the right experiment.

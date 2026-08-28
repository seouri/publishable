# Feasibility analysis: LLM growth studies

Two existing research repositories were read as candidate users of `publishable`:

| Source | Goal, as stated by the repository itself |
|---|---|
| `2026-07-01-screening` | Optimize an LLM prompt that screens pediatric growth trajectories for possible concern in primary care, and establish whether prespecified DSPy/MIPROv2 optimization changes retrospective held-out screening performance. Secondary: compiled-program transfer across deployments, request-setting (reasoning-effort) behavior, and binary-output repeatability |
| `2026-08-03-shorcut` | Decide whether an LLM growth-screening model reads growth curves or counts visits. Three gates against a blinded clinician reference standard: reference-standard validity, physiologic sensitivity under counterfactual physiology, and utilization invariance under counterfactual visit schedules |

This document does not reproduce either repository. It asks a narrower question: **which of the experiments those two projects specify can be expressed in `publishable`'s vocabulary, what each one's config actually looks like, what it costs to execute, and which parts core refuses.** The refusals are the load-bearing half — a feasibility analysis that only lists what fits is an advertisement.

This document is non-normative and carries its own examples. It is **not** part of the shared worked example (`cohort-pilot`); see `CLAUDE.md` § Feasibility analyses.

## Contents

- [What both projects hand-rolled that core already owns](#what-both-projects-hand-rolled-that-core-already-owns)
- [Three repositories, and what decides the seams](#three-repositories-and-what-decides-the-seams)
- [Screening: six runs](#screening-six-runs)
- [Shortcut: three runs](#shortcut-three-runs)
- [What is not an experiment](#what-is-not-an-experiment)
- [What core refuses, and the route for each](#what-core-refuses-and-the-route-for-each)
- [Proposed plugin: `publishable-llm`](#proposed-plugin-publishable-llm)
- [Gaps this analysis found in the specification](#gaps-this-analysis-found-in-the-specification)
- [Executability on this build](#executability-on-this-build)
- [Cost and execution summary](#cost-and-execution-summary)

---

## What both projects hand-rolled that core already owns

Before any design mapping, the largest single finding: both repositories built machinery that `publishable` supplies. This is the clearest argument for adopting it, and it is also the list of things the proposed plugin must **not** rebuild.

| Hand-rolled in the source | Core equivalent |
|---|---|
| `execution_manifest.json` — SHA-256 of inputs, evaluator source, `uv.lock`, git revision, dirty-worktree status, package versions | [`code_hash`, `parameters_hash`, `input_manifest_hash`](reference.md#three-hashes), `uv_lock_hash`, and `run` refusing a dirty `src/**` |
| `execution_ledger.csv` — one row per attempt, status, exit status, stderr excerpt | [`executions.jsonl`](reference.md#executionsjsonl--what-has-happened-so-far) plus a per-unit `attempts` column |
| A shell `run_once()` wrapper enforcing fresh output directories | [`io.write` refusing an existing target](reference.md#steps-and-artifacts) and one run directory per run ID |
| Timestamped `YYYY-MM-DD-HH-MM-SS` run directories | [Run identity](reference.md#run-identity) |
| `run_config.json` and `reproduce_command.txt` | The config embedded verbatim in `run.yaml`, and `publishable reproduce` |
| `cohort_summary.json`, `patient_splits.json` | [`provenance.units`](reference.md#units-the-thing-being-measured), `provenance.units_hash`, [`allocation.json`](reference.md#allocationjson--who-went-where) |
| `run_usage_report.json` — per-step token totals and duration, no intervals | Per-unit `prompt_tokens` / `completion_tokens` / `latency_ms` columns through [`io.record`](reference.md#units-the-thing-being-measured), which makes them `basis: units` metrics **with** `ci95` |
| A five-block Latin square hand-written as 25 `run_once` calls | [`{kind: batch, n: 5}`](reference.md#a-batch-says-when-not-what) with `order: randomized` |
| "Quarantine the calibration test artifacts; do not open them" | [`data.units.holdout`](reference.md#a-fixed-holdout-split) plus [`hypotheses`](reference.md#pre-registration) carrying the declaring config's `parameters_hash` |
| A prose promise that confidence intervals will be computed later | [Statistical reporting](reference.md#statistical-reporting) computes them from the unit table, or refuses and says `basis: repeats` |

The `run_usage_report.json` row is the sharpest. Both projects treat token use and latency as *bookkeeping* and write them to a side file with no denominator. They are measurements of the apparatus made once per patient, so they belong in the unit table, where they get an `n`, an interval, and a `repeat_spread` for free.

---

## Three repositories, and what decides the seams

Nine runs, two pipelines, one plugin. How many git repositories that is has a mechanical answer rather than a stylistic one, because a repository boundary is exactly what [`code_hash`](reference.md#how-the-three-are-computed) is scoped to.

| Repository | Holds | How its code is pinned |
|---|---|---|
| `growth-screen` | `src/growth_screen/`, `configs/screen-*` — E1 through E6 | Its own `code_hash`, over `src/**` and `templates/**` |
| `growth-shortcut` | `src/growth_shortcut/`, `configs/shortcut-*` — C1 through C3 | Its own `code_hash` |
| `publishable-llm` | The `llm_screen` template, the `patient_trajectory` resolver, the `llm_deployment` probe, and the reusable steps | `uv.lock`, in each of the two above |

**The plugin is a separate repository, and not by preference.** Only a template can live locally: [§ Creating a plugin](reference.md#creating-a-plugin-publishable-plugin-new) finds a local `templates/*.py` by path, and everything else registers through an entry point, which needs an installed package. This design needs a resolver and a probe, so it needs one. Vendoring it as a `uv` path dependency inside an experiment repo would be the worst available option: at `plugins/` it sits outside `src/**` and `templates/**` so `code_hash` doesn't cover it, and a path dependency doesn't pin content either — it would be the one piece of code producing these numbers that nothing pins at all.

**The two experiment repositories are separate for the reason the specification names itself.** [§ How the three are computed](reference.md#how-the-three-are-computed) states the boundary and its remedy in one breath: `src/**` covers every experiment package in the repository, so "adding or editing `src/other_pilot/` moves the `code_hash` of a run that never imported it," and "an experiment whose `code_hash` has to hold still against unrelated work belongs in its own repository." That is this case exactly. One repository would still *work* — `generate experiment` is built for it — and here is the bill:

| Mechanism | What it does across these nine runs |
|---|---|
| `code_hash` spans `src/**` | Every commit to `growth_shortcut` changes the recorded code identity of screening runs that never imported it |
| `run` refuses a dirty `src/**` | E4 (4.4 h) and C3 (12 h) cannot start while the other package has uncommitted edits — `run` enforces this today. [`draft`](reference.md#draft-runs) is specified to permit it and mark the run non-citable, which is no use for a confirmation run anyway; whether it dispatches is a build fact and lives in the dated entries ([§ Executability on this build](#executability-on-this-build)) |
| `resume` refuses a moved `uv.lock` | One lockfile serves both, so a dependency added for the shortcut makes an in-flight twelve-hour screening run unresumable — as specified; whether `resume` dispatches is a build fact and lives in the dated entries — see [§ Executability on this build](#executability-on-this-build) |

**What that costs is the claim the screening sequence is built on.** E1 freezes the objective, E2 spends it, and E3, E4, and E6 all evaluate the same frozen program — a sequence spread over weeks whose reviewer-facing claim is [same code, different parameters](design-principles.md#same-code-different-parameters): identical `code_hash`, differing `parameters_hash`. Shortcut development inside that window destroys the first half of it. Sharpest is the pair of roster-variant runs [§ Cost and execution summary](#cost-and-execution-summary) sets aside, which exist *only* to be compared against E1 through E3 in a study — and [`report study.yaml`](reference.md#studies-what-a-paper-reports) cross-checks that runs claiming the same code really do share a `code_hash`.

**Shared code goes into the plugin, and that is the point rather than the price.** Both projects censor at the diagnosis age and both need growth-reference percentiles, so the pull toward one repository is really a pull toward one `src/common/`. The specification rejects per-package hashing on precisely that case — "a rule that hashed one package while a shared `src/common/` module produced half the numbers would be a hash claiming more than it covers." A plugin is the version of sharing that survives the check: `uv.lock` pins it, both repositories record which version they used, and `diff` can tell two runs apart on it. Less is shared than it first looks, anyway — the screening serializer emits raw and percentile pairs where the shortcut's emits z-scores under a transform, so the genuine overlap is the resolver, the request step, and the probe, which is what the plugin already holds.

**Nothing in these nine runs crosses the seam, which is the check worth running on any proposed split.** E3, E4, and E6 read their frozen program from a screening run; the shortcut's confirmation runs read the fine-tuned artifact from the shortcut development run. Every [`io.reuse_from`](reference.md#lineage-between-runs) stays inside its own repository's lineage, so no `provenance.upstream` chain is cut — a seam that cut one would be in the wrong place. Output directories are [outside every repository](design-principles.md#code-and-data-never-share-a-repo) regardless, so the split changes nothing about where results land. And the paper is unaffected either way: a [study](design-principles.md#ontology) is a bundle beside the manuscript and never in a repository at all, which makes it the thing that reassembles the three.

---

## Screening: six runs

### Shared roster and pipeline

All six live in the `growth-screen` repository, resolve the same roster through a plugin resolver, and draw their steps from one package. **E1 is shown in full; every config after it shows only the blocks that differ.**

```
growth-screen/src/growth_screen/
├── experiment.py                  # two BaseExperiment classes; `entrypoint` selects one
└── steps/
    ├── step01_serialize.py        scope: run        # censoring + trajectory serialization
    ├── step02_compile_program.py  scope: condition  # MIPROv2 over io.units.train; no-op when optimizer.name == none
    ├── step03_screen.py           scope: repeat     # one request per unit; nondeterministic = True
    ├── step04_compare.py          scope: summary    # compares conditions
    └── step05_agreement.py        scope: summary    # compares repeats of one condition
```

| Experiment class | Steps | Used by |
|---|---|---|
| `GrowthScreenExperiment` | 01 → 02 → 03 → 04 | E1, E2, E3, E4, E6 |
| `RepeatabilityExperiment` | 01 → 03 → 05 | E5 |

**Two classes rather than one, because E5 measures something else.** `step04_compare` compares conditions and E5 has exactly one; `step05_agreement` compares *repeats* within a condition, which no other run wants. A `BaseExperiment` is [the ordered `steps` list and nothing else](reference.md#the-importable-surface), so two classes in one `experiment.py` cost nothing and each config's `entrypoint` picks between them. The `stepNN_` prefixes number the files rather than either pipeline's positions, so E5 legitimately runs 01 → 03 → 05.

**Compilation is `condition`-scoped, and that is the decision the cost hinges on.** A `seed` repeat then re-executes only the evaluation, so three repeats cost three evaluations (~$14 each) rather than three MIPRO compilations (~$95 each). The consequence is honest and must be stated in the paper: **optimizer stochasticity is not measured by a `seed` repeat under this structure.** To measure it, `optimizer.seed` becomes a `sweep.grid` axis and each draw is its own condition, at full compile cost.

`io.units.train` is available at condition scope because the split is a [`holdout`](reference.md#a-fixed-holdout-split) rather than a `fold` — a fold does not exist above repeat scope, a holdout is drawn once for the run. The source's *three* splits (train / dev / test) do not map onto a holdout's two: `test` is the holdout, and `dev` is a sub-split of `io.units.train` drawn inside `step02` from [`self.derive_seed("dev-split")`](reference.md#a-step-that-partitions-needs-a-seed-and-derive_seed-is-where-it-comes-from). That sub-split is an implementation detail of the fit, which is exactly where the spec puts a setting chosen from results.

### E1 — Metric calibration

**Problem.** The screening objective gives false negatives partial credit. Four candidate credit values (0.10, 0.25, 0.50, 0.75) must be compared on development artifacts only, and one frozen, before the held-out set is touched.

**Design.** A one-axis `grid` over a single parameter, evaluated on the same held-out patients in every condition, so every contrast is paired unit by unit. No `sweep.baseline`: the four credits are peers, and the source's selection rule is a threshold table rather than a comparison against a reference. Declared contrasts would only widen the correction family for comparisons nobody reads individually.

```yaml
# configs/screen-calibration/config.yaml
schema_version: "1.0"
experiment_type: llm_screen
template_version: "0.1.0"
plugin: "seouri/publishable-llm@v0.1.0"

metadata:
  name: screen-calibration
  description: "Select and freeze the false-negative partial credit on development artifacts only"
  authors: ["Kyungjoon Lee"]
  institution: "Harvard Medical School"

entrypoint: "growth_screen.experiment:GrowthScreenExperiment"

data:
  input_dir: /secure/data/peds-growth-2026
  output_dir: /secure/results/screen-calibration
  input_manifest_policy: hash_index
  units:
    from: {resolver: patient_trajectory}
    key: patient_id
    attributes: [truth, sex, age_band, visit_density, span_days, dx_family, record_source]
    allocation: within
    cluster_by: null
    weight_by: null
    measurements: null
    holdout:
      method: random
      frac: 0.2
      stratify_by: [truth]
      seed: 20260701
    assign: {}

parameters:
  llm:
    model: azure.gpt-5.5
    provider: azure_openai
    api_version: "2026-05-01"
  request:
    temperature: 0.0
    max_output_tokens: 512
    timeout_seconds: 120
    reasoning_effort: null
    reasoning_summary: false
    cache: false
    concurrency: 1
    max_retries: 1
    backoff_secs: [900]
  prompt:
    strategy: compiled
    program_id: null
    program_run: null
  optimizer:
    name: mipro
    budget: medium
    seed: 20260701
  objective:
    false_negative_credit: 0.25
    invalid_credit: 0.0
  cohort:
    censor_buffer_years: 0.25
    min_valid_visits: 3
  output:
    kind: binary
    field: growth_issue_screen
    threshold: 0.5
  report:
    prevalences: [0.01, 0.03]
    metrics: [sensitivity, specificity, ppv, invalid_rate]
  pricing:
    prompt_per_mtok: 5.0
    completion_per_mtok: 30.0

sweep:
  baseline: null
  groups: []
  paired: []
  ablate: null
  sample: null
  grid:
    objective.false_negative_credit: [0.10, 0.25, 0.50, 0.75]
  # 4 conditions

replication:
  repeats:
    - {kind: seed, n: 3}
  order: as_declared
  rationale: >-
    Three evaluation seeds per condition. Compilation is condition-scoped, so a seed
    repeat re-executes evaluation only; optimizer stochasticity is deliberately NOT
    measured here and would require optimizer.seed as a sweep axis.

statistics:
  correction: holm
  contrasts: []
  resample: {method: bootstrap, n: 2000, stratify_by: [truth]}
  null_test: null
  report_by: [sex, visit_density]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses: []
```

**Execution and cost.** 4 conditions × 3 seed repeats = **12 repeat-scope executions**, plus 4 condition-scope compilations. At the source's own anchors (~$95 per MIPRO-medium compile, ~$14 per 440-patient evaluation): **≈ $548, ≈ 8.5 h serial.** The source's equivalent calibration phase was $380 for 4 runs and produced neither intervals nor dispersion.

**What this buys over the source.** One roster, so the four credits are compared on identical patients — the source's own "Cohort Comparability Rule" warns that its rows may not be. `report_by: [sex, visit_density]` supplies the subgroup tables the protocol requires at no extra execution and with no correction cost. `hypotheses: []` is correct here: calibration is selection, not a claim.

### E2 — Primary optimization comparison

**Problem.** Does MIPROv2 optimization improve held-out screening performance over the unoptimized baseline prompt, under the frozen objective?

**Design.** Two conditions on one parameter axis with a declared `baseline`, so core computes `vs_baseline` deltas with `paired_percentile_over_units` over `n_paired`. This is the run that carries a pre-registered hypothesis.

```yaml
# configs/screen-primary/config.yaml  (blocks identical to E1 unless shown)
metadata:
  name: screen-primary
  description: "Baseline prompt versus MIPROv2-medium on the frozen held-out patients"

parameters:
  objective:
    false_negative_credit: 0.75      # frozen by E1
  optimizer:
    name: mipro
    budget: medium
    seed: 20260701

sweep:
  baseline: {optimizer.name: none}
  grid:
    optimizer.name: [mipro]
  # 2 conditions: 00_baseline, 01_name=mipro

replication:
  repeats:
    - {kind: seed, n: 3}
  order: as_declared
  rationale: "Three evaluation seeds; one compilation, at condition scope, for the mipro arm only."

statistics:
  correction: holm
  contrasts: []
  resample: {method: bootstrap, n: 2000, stratify_by: [truth]}
  null_test: null
  report_by: [sex, age_band, visit_density, dx_family]

hypotheses:
  - id: h_specificity
    kind: confirmatory
    statement: "Optimization raises held-out specificity over the unoptimized prompt."
    metric: step03_screen.specificity
    compare: {condition: "name=mipro", to: baseline}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
  - id: h_sensitivity_floor
    kind: confirmatory
    statement: "Optimization does not reduce held-out sensitivity by more than 0.10."
    metric: step03_screen.sensitivity
    compare: {condition: "name=mipro", to: baseline}
    direction: greater
    threshold: -0.10
    evaluate_on: ci95_lower
```

**Execution and cost.** 2 × 3 = **6 executions**, 1 compilation. **≈ $179, ≈ 2.6 h.**

**What this buys.** The source could not guarantee its baseline and MIPRO rows shared held-out patients and says so ("report the comparison as unpaired internal validation"). Here one roster and one holdout make pairing structural, and `n_paired` records the intersection. `h_sensitivity_floor` written as `evaluate_on: ci95_lower` against a negative threshold is the non-inferiority form the source's prose asks for and never states as a testable quantity.

### E3 — Cohort-definition sensitivity

**Problem.** Are results driven by the arbitrary 0.25-year diagnosis-censoring buffer or the 3-visit minimum-evidence threshold?

**Design.** This is the mapping that changes most. The source runs four separate optimizations, each re-sampling its own cohort, and can therefore only call them design-sensitivity analyses. In `publishable` the roster is the *superset* — every patient eligible at the loosest setting — and the two parameters act differently on it, which the config must distinguish:

- **`cohort.censor_buffer_years` changes the serialized input.** A larger buffer hides more pre-diagnosis measurements. Every unit still produces a result.
- **`cohort.min_valid_visits` changes eligibility.** A unit falling below the condition's threshold admits no result by design, so `step01` calls [`io.skip(unit.key, reason)`](reference.md#what-isnt-a-repeat) and it lands in `ineligible`, not `failed`.

Eligibility is a deterministic function of the unit and the condition's parameters, so it is constant across that condition's repeats — which it must be: a unit skipped in some repeats and completed in others is counted **failed**, not ineligible.

`sweep.ablate` with `override` is the exact mode for one-change-at-a-time, and it reads the declared baseline rather than re-emitting it.

```yaml
# configs/screen-cohort-sensitivity/config.yaml
metadata:
  name: screen-cohort-sensitivity
  description: "One-at-a-time sensitivity to censoring buffer and minimum longitudinal evidence"

parameters:
  prompt:
    strategy: compiled
    program_id: mipro-medium-20260705
    program_run: run_2026-07-05T07-33-24Z_b7f2bf7
  optimizer:
    name: none                       # the program is frozen; nothing is compiled here

sweep:
  baseline: {cohort.censor_buffer_years: 0.25, cohort.min_valid_visits: 3}
  ablate:
    from: baseline
    override:
      - {cohort.censor_buffer_years: 0.375}
      - {cohort.censor_buffer_years: 0.5}
      - {cohort.min_valid_visits: 4}
      - {cohort.min_valid_visits: 5}
  # 1 baseline + 4 one-change conditions = 5 conditions

replication:
  repeats:
    - {kind: seed, n: 3}
  order: as_declared
  rationale: >-
    The frozen program is read from the source run via io.reuse_from, so no condition
    recompiles. The sensitivity question is about the cohort, not about re-optimization.

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.35     # visits >= 5 is expected to exclude a real share
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10
```

**Execution and cost.** 5 × 3 = **15 executions**, no compilations. **≈ $210, ≈ 2.6 h** — against the source's ≈ $357 for four re-optimizing runs, and paired where the source's are not.

**What this buys.** `n_paired` per contrast is the intersection of both sides' completed units, so the stricter-visit arms are compared to baseline over exactly the patients both admit. `limits.max_ineligible_fraction` warns when an arm can be built for too few, which is the design problem the source describes in prose and never checks.

### E4 — Reasoning-effort operational benchmark

**Problem.** How do latency, token use, output validity, and classification variability differ across requested reasoning-effort settings, with the compiled program, cohort, deployment, and every other request setting frozen?

**Design.** This is the closest fit in either project. Five efforts are a one-axis `grid`; the source's five balanced blocks are `{kind: batch, n: 5}`; the within-block position shuffle is `order: randomized`. `nondeterministic = True` on `step03_screen` is required — without it `validate` warns that five batches recompute one answer.

```yaml
# configs/screen-reasoning-effort/config.yaml
metadata:
  name: screen-reasoning-effort
  description: "Requested reasoning effort against latency, token use, validity, and stability"

parameters:
  prompt:
    strategy: compiled
    program_id: mipro-medium-20260705
    program_run: run_2026-07-05T07-33-24Z_b7f2bf7
  optimizer:
    name: none
  request:
    temperature: 0.0
    max_output_tokens: 512
    timeout_seconds: 120
    reasoning_effort: medium
    reasoning_summary: true
    cache: false                     # a cache hit is not a measurement
    concurrency: 1                   # "do not run conditions concurrently"
    max_retries: 1
    backoff_secs: [900]

sweep:
  baseline: {request.reasoning_effort: none}
  grid:
    request.reasoning_effort: [low, medium, high, xhigh]
  # 5 conditions

replication:
  repeats:
    - {kind: batch, n: 5}
  order: randomized
  rationale: >-
    Five separated blocks; every effort met once per block, in an order that does not
    confound it with within-block position. Batches stay in declared order because a
    batch is a position in time.

statistics:
  correction: holm
  contrasts: []
  resample: {method: bootstrap, n: 2000}
  null_test: null
  report_by: [sex, visit_density]
```

**Execution and cost.** 5 × 5 = **25 executions**, no compilations. **≈ $350, ≈ 4.4 h** — the same 25 evaluations the source schedules by hand.

**Two honest differences from the source's design.** Core's `order: randomized` gives a *randomized complete block* design — every condition once per batch, position drawn — not the source's Latin square, in which each effort occupies each position exactly once. Core records the realized order and each execution's `started_at`, so position can be carried into a `scope: "summary"` step if a period term is wanted; core will not construct the square. And `repeat_spread` will report `kind: batch` dispersion separately from any `seed` dispersion, which is precisely the "operational variability versus RNG" split the source's protocol reports as one number.

### E5 — Binary-output repeatability

**Problem.** Estimate agreement between fresh executions of one frozen program on one cohort — a property of the apparatus, not of accuracy.

**Design.** One condition, ten batches, and its own `entrypoint` — this is the run that swaps `step04_compare` for `step05_agreement`. Agreement across repeats is not something core computes: core averages repeats per unit before any interval. The agreement bound is therefore a `scope: "summary"` step reading each repeat's per-unit table through `io.read_condition(condition, step, name, repeat=r)` and returning an [`Estimate`](reference.md#estimate-carries-your-interval-without-core-claiming-it). The hypothesis names it and takes no `compare`.

**One condition is declared by leaving `sweep` out**, which is what [§ The one config file](reference.md#the-one-config-file) says of the block — omit it entirely for a single-condition experiment. A `sweep` that is present and expands to nothing is not the same declaration and is refused as `E-SWEEP-EXPANDS-EMPTY`: a run that executes zero conditions while reporting success is the record-describing-an-experiment-nobody-performed failure, so writing the block out with an empty `grid` to show the intent is exactly the mistake the check exists to catch.

```yaml
# configs/screen-repeatability/config.yaml
metadata:
  name: screen-repeatability
  description: "Within-block safe agreement of the frozen binary screen across fresh executions"

entrypoint: "growth_screen.experiment:RepeatabilityExperiment"   # not the four-step class

# E1's `sweep` block is dropped, not overridden: no `sweep` key at all,
# which is how a single-condition experiment is declared

replication:
  repeats:
    - {kind: batch, n: 10}
  order: as_declared
  rationale: "Ten cache-disabled, serial, nonconsecutive blocks against one frozen deployment."

statistics:
  correction: none
  contrasts: []
  resample: null
  null_test: null
  report_by: []

hypotheses:
  - id: h_agreement
    kind: confirmatory
    statement: "Within-block safe agreement exceeds 0.99."
    metric: step05_agreement.s_within_lower_bound
    direction: greater
    threshold: 0.99
    # no `compare`: there are no conditions to contrast
```

**Execution and cost.** **10 executions**, **≈ $140, ≈ 1.8 h.**

The verdict records `verdict_rests_on: reported` — core compared the numbers and did not derive them. That is the correct attribution, and it is what the source's protocol asks for when it says the analysis code must be frozen and executable.

### E6 — Compiled-program transfer

**Problem.** Separate program-origin from execution-model effects: run a program optimized on one deployment against several deployments, alongside a neutral program on the same deployments.

**Design.** Two crossed parameter axes. The baseline fixes the *program* and leaves `llm.model` free, which gives one reference per deployment and a clean per-deployment contrast — the spec's own example of a nuisance axis left unfixed.

**A swept value must render as `[A-Za-z0-9._+-]+`, so a model identifier containing `/` cannot be a level.** `azure/gpt-5.5` is illegal as a condition label. Sweep a deployment *alias* and resolve it to the provider identifier inside the plugin's request layer. The same rule forbids sweeping a compiled-program *path*: sweep a `program_id` and resolve it through `io.reuse_from`.

```yaml
# configs/screen-transfer/config.yaml
metadata:
  name: screen-transfer
  description: "Compiled-program transfer across deployments, against a neutral program"

sweep:
  baseline: {prompt.program_id: neutral-baseline}
  grid:
    prompt.program_id: [mipro-medium-20260705]
    llm.model: [azure.gpt-5.5, azure.gpt-4.1, azure.gpt-4.1-nano]
  # baseline expands over the unfixed llm.model axis:
  #   3 baseline conditions (one per deployment) + 3 compiled conditions = 6 conditions
  #   3 comparisons, each within one deployment — none confounded

replication:
  repeats:
    - {kind: seed, n: 3}
  order: randomized
  rationale: "Three evaluation repeats per cell; randomized to avoid confounding deployment with time."

statistics:
  correction: holm
  contrasts: []
  resample: {method: bootstrap, n: 2000, stratify_by: [truth]}
  null_test: null
  report_by: [sex, visit_density]
```

**Execution and cost.** 6 × 3 = **18 executions**, no compilations. **≤ $252, ≈ 3.2 h** at the most expensive deployment's rate.

**Credentials follow the swept value.** The apparatus probe is permitted — and here required — to read a parameter the sweep varies, so each deployment is gated against its own first *answered* observation. The credentials reaching those deployments differ too, and a static `required_env` could not express that: it would demand an Azure key from a run that only touches Ollama, or stay silent about one a later condition needs. [`Param(requires_env=...)`](reference.md#a-credential-can-belong-to-a-parameter-value) on `llm.provider` puts the requirement on the value, so `validate` checks the union over the conditions this sweep resolves — which is what lets the source's local-Gemma cell join the same config as the Azure cells rather than needing a run of its own. Provider and model have to move together, so that cell enters as a `sweep.paired` entry coupling `llm.provider` with `llm.model` rather than as a fourth `grid` level — a cross of the two would emit conditions pointing an Azure deployment name at an Ollama endpoint.

---

## Shortcut: three runs

These three live in the **`growth-shortcut` repository**, whose pipeline builds counterfactual trajectories and fits the two regression baselines. It shares no code with `growth_screen` — and some step names anyway: `step03_screen` below is `growth_shortcut`'s own request step, not the screening package's, and a metric path like `step03_screen.auroc` is only ever read within its own run. As above, only the blocks that differ are shown, starting with the roster: the 450-patient benchmark, resolved with the sampling weight the source retains for population-weighted estimates and the pre-existing development/confirmation partition.

```yaml
data:
  units:
    from: {resolver: patient_trajectory}
    key: patient_id
    attributes: [consensus_label, sex, age_band, count_stratum, span_days,
                 dx_family, record_source, sampling_weight, split]
    allocation: within
    cluster_by: null
    weight_by: sampling_weight       # the enriched sample reported as a population estimate
    measurements: null
    holdout: null                    # confirmation run: the roster IS the confirmation set
    assign: {}
```

`weight_by` records `weighted_by` beside every affected value and adds `effective` to the three-part `n` from Kish's size. `resample.stratify_by: [consensus_label, count_stratum]` reproduces the source's "patient-level stratified bootstrap" exactly: `weight_by` says how much each unit stands for; `resample.stratify_by` says what an independent draw is.

**That is the declaration read on its own, and C1, C2 and C3 never read it on its own.** Each pairs `weight_by` with a `baseline` or a declared contrast, which this build now computes rather than refuses — but not identically for all three, because C1's headline metric and C2/C3's are two different shapes. All three declare `statistics.resample`, so `resample_columns` is `True` for each and the raw and corrected *t* branch (`paired_t_over_units`/`weighted_paired_t_over_units`) is never entered for any of them; the payoff path runs through `paired_percentile_of_derived` throughout. **C2 and C3** contrast `step03_screen.prob`, a recorded column, so that path takes the weighted closure — `weighted_paired_percentile_over_units` — and their record carries a weighted `delta`, a weighted `cohens_d`, and an `n_paired_effective` from Kish's size over the paired intersection. **C1** contrasts `step03_screen.auroc`, which `aggregate` derives, and core does not weight a derived metric's contrast: the weight reaches `aggregate` as a unit attribute instead, `method` stays the unweighted `paired_percentile_over_units`, and `cohens_d` stays `null` — `weighted_by` and the effective size still travel beside the record regardless, since the declaration is true of the run either way. `resample.stratify_by` is honoured on the draw for all three. What is not yet honoured, for any of them, is `statistics.report_by` under a declared `resample` — a level's own recorded-column interval stays unresampled — which is the one gap these three runs still carry ([§ Executability on this build](#executability-on-this-build) has the dated measurement and count).

The development set (120) and confirmation set (330) are **two runs against two indexes**, not one holdout — because clean-label fine-tuning fits on the development patients and is evaluated on the confirmation patients, which is a cross-run dependency. The confirmation run reads the fitted artifact with `io.reuse_from`, and core records the upstream run's ID and both its hashes in `provenance.upstream`.

`allocation: within` is what every counterfactual claim rests on: the same patients are evaluated under every transform, so every contrast is paired unit by unit and core derives that rather than being told.

### C1 — Reference-standard gate

**Problem.** Do the model's predictions discriminate blinded clinician-adjudicated abnormal from normal trajectories better than a utilization-only baseline?

**Design.** A one-axis `grid` over model regime with the utilization-only regression as the declared `baseline`. AUROC is derived from the per-unit `prob`/`consensus_label` columns by the template's `aggregate`, which makes it `basis: units` with a percentile interval over 330 patients — not a scalar a step returned. The source's own instruction, "if an API is not deterministic at fixed decoding settings, run five independent inferences per input, average the predicted probabilities, and report within-input variation," is `{kind: batch, n: 5}`: core averages per unit and reports `repeat_spread`.

```yaml
# configs/shortcut-reference-gate/config.yaml
metadata:
  name: shortcut-reference-gate
  description: "Paired AUROC against the blinded physiology label, versus a utilization-only baseline"

parameters:
  model:
    regime: zero_shot
  transform:
    arm: natural
  output:
    kind: probability
    field: abnormal_probability
    threshold: 0.5
  report:
    prevalences: [0.01, 0.03]
    metrics: [auroc, sensitivity, specificity, brier]

sweep:
  baseline: {model.regime: utilization_only}
  grid:
    model.regime: [clinical_physiology, zero_shot]
  # 3 conditions

replication:
  repeats:
    - {kind: batch, n: 5}
  order: randomized
  rationale: >-
    Five independent inference passes per patient, as the protocol requires for a
    deployment that is not deterministic at fixed decoding settings. Within-input
    variation is reported as repeat_spread with kind: batch.

statistics:
  correction: holm
  contrasts: []
  resample: {method: bootstrap, n: 2000, stratify_by: [consensus_label, count_stratum]}
  null_test: null
  report_by: [sex, age_band, count_stratum, dx_family, record_source]

hypotheses:
  - id: gate_reference_standard
    kind: confirmatory
    statement: "Paired AUROC improvement over the utilization-only baseline exceeds zero."
    metric: step03_screen.auroc
    compare: {condition: "regime=zero_shot", to: baseline}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```

**Execution and cost.** 3 × 5 = **15 executions**, of which 5 reach the API (the two regressions are local). At 330 patients ≈ $10.60 per API execution: **≈ $53, ≈ 1 h.**

`report_by` supplies every subgroup table the source lists — measurement-count stratum, age group, sex, diagnosis family, record source — with no extra executions and no place in the correction family.

### C2 — Representation and utilization invariance

**Problem.** How much performance is attributable to the recording process rather than to physiology, and do predictions stay put when visit count and timing change while the underlying curve does not?

**Design.** One `transform.arm` axis with the natural trajectory as baseline. The invariance claim is a contrast between two counterfactual arms, neither of which is the reference, so it is a declared [`statistics.contrasts`](reference.md#contrasts-claims-that-arent-condition-vs-baseline) entry — which is verbatim the spec's own worked example for this shape.

Patients for whom a counterfactual cannot be constructed — an observed span too short to resample at twelve occasions — are `io.skip`ped with a reason, land in `ineligible`, and are excluded from `n_paired` on both sides. That is the source's requirement that "the natural representation is also evaluated on every transformed-arm-eligible patient so that paired comparisons never confound representation with cohort composition," and core enforces it rather than asking the analyst to remember.

```yaml
# configs/shortcut-utilization/config.yaml
metadata:
  name: shortcut-utilization
  description: "Process-only, fixed-grid, washout, and visit-schedule counterfactuals"

parameters:
  model:
    regime: zero_shot                # frozen by the development run's selection rule
  transform:
    arm: natural

sweep:
  baseline: {transform.arm: natural}
  grid:
    transform.arm: [process_only, fixed_grid, washout_90, washout_180, washout_365,
                    occasions_3, occasions_6, occasions_12]
  # 9 conditions

replication:
  repeats:
    - {kind: batch, n: 5}
  order: randomized
  rationale: "Five independent inference passes per patient per arm."

statistics:
  correction: holm
  contrasts:
    - {id: invariance, of: "arm=occasions_3", against: "arm=occasions_12"}
    - {id: process_share, of: "arm=process_only", against: "arm=fixed_grid"}
  resample: {method: bootstrap, n: 2000, stratify_by: [consensus_label, count_stratum]}
  null_test: null
  report_by: [sex, age_band, count_stratum, record_source]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.4      # the 12-occasion arm cannot be built for short spans
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: gate_invariance_upper
    kind: confirmatory
    statement: "The paired 3-versus-12-occasion prediction difference is below 0.05."
    metric: step03_screen.prob
    compare: {contrast: invariance}
    direction: less
    threshold: 0.05
    evaluate_on: ci95_upper
  - id: gate_invariance_lower
    kind: confirmatory
    statement: "The paired 3-versus-12-occasion prediction difference is above -0.05."
    metric: step03_screen.prob
    compare: {contrast: invariance}
    direction: greater
    threshold: -0.05
    evaluate_on: ci95_lower
```

**Execution and cost.** 9 × 5 = **45 executions**, **≈ $477, ≈ 9 h.**

**The invariance gate had to be restated, and the restatement is better statistics.** The source's gate is "the upper bound of the 95% CI for the **mean absolute** probability difference between the 3- and 12-occasion variants is below 0.05." A contrast computes the mean of the paired differences, not the mean of their absolute values, and those are different quantities — the second is biased away from zero by noise alone, so a perfectly invariant model with a noisy apparatus fails it. Two one-sided bounds on the signed paired difference is the standard equivalence form, expressible directly as the two hypotheses above, and it is the claim the study actually wants. If the mean absolute difference is required as written, it is a function of two conditions that core does not compute, and belongs in a `scope: "summary"` step as an `Estimate` — carried on the record without core claiming it.

### C3 — Physiologic sensitivity

**Problem.** Do predictions move in the expected direction when standardized level or slope is altered and the visit schedule is held fixed, with a monotonic response between the 0.5 and 1.0 z-score magnitudes?

**Design.** Three crossed parameter axes. No `sweep.baseline`: the abnormalizing and normalizing variants are matched peers, and the claims are contrasts between them.

```yaml
# configs/shortcut-physiology/config.yaml
metadata:
  name: shortcut-physiology
  description: "Matched abnormalizing and normalizing velocity and attained-size transforms"

parameters:
  transform:
    shift: normal
    magnitude: 0.5
    target: weight
    family: velocity

sweep:
  baseline: null
  groups: []
  paired: []
  ablate: null
  sample: null
  grid:
    transform.shift: [abnormal, normal]
    transform.magnitude: [0.5, 1.0]
    transform.target: [weight, height, both]
  # 2 × 2 × 3 = 12 conditions

replication:
  repeats:
    - {kind: batch, n: 5}
  order: randomized
  rationale: "Five independent inference passes per patient per cell."

statistics:
  correction: holm
  contrasts:
    - {id: sens_weight_10, of: "shift=abnormal__magnitude=1.0__target=weight",
       against: "shift=normal__magnitude=1.0__target=weight"}
    - {id: sens_height_10, of: "shift=abnormal__magnitude=1.0__target=height",
       against: "shift=normal__magnitude=1.0__target=height"}
    - {id: sens_weight_05, of: "shift=abnormal__magnitude=0.5__target=weight",
       against: "shift=normal__magnitude=0.5__target=weight"}
    - {id: sens_height_05, of: "shift=abnormal__magnitude=0.5__target=height",
       against: "shift=normal__magnitude=0.5__target=height"}
  resample: {method: bootstrap, n: 2000, stratify_by: [consensus_label, count_stratum]}
  null_test: null
  report_by: [sex, age_band, count_stratum]

hypotheses:
  - id: gate_physiologic_sensitivity
    kind: confirmatory
    statement: >-
      The equally weighted mean prediction difference between 1.0-z abnormalizing and
      matched normalizing velocity variants, over weight and height, exceeds zero.
    metric: step04_gates.sensitivity_mean
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
    # no `compare`: this is a summary Estimate over two contrasts
```

**Execution and cost.** 12 × 5 = **60 executions**, **≈ $636, ≈ 12 h.**

**Two parts of this gate are refusals, and both route to the same place.** The primary contrast is the *equally weighted mean* of the weight and height contrasts — an estimator over contrasts. The dose-response requirement is an *ordering* of contrasts. Contrasts compare conditions and do not nest, so both are interactions, and both stay in a `scope: "summary"` step returning an `Estimate` with its own `method` and its own multiplicity adjustment declared inside that string. The four `sens_*` contrasts above are the ones that will be *reported* individually; declaring more contrasts to build the mean would widen the correction family by comparisons nobody reads and still not compute the number wanted.

The hypothesis family here mixes core-computed and reported observations, so there are **two** families and only one is core's — `family_size` will count the core-computed confirmatory hypotheses and will not pretend to cover `gate_physiologic_sensitivity`.

---

## What is not an experiment

Three substantial pieces of both projects are not runs, and calling them runs would be the mistake worth naming.

**Blinded clinician adjudication is input production.** Three clinicians classifying 450 trajectories under a versioned rubric, the randomized review order, the 2-to-1 disagreement rule, the consensus conference, Gwet's AC1 with patient-bootstrap intervals — none of this is a pipeline core executes. The frozen consensus label is a **column in the unit index**, reaching the design as `data.units.attributes: [consensus_label]`. The adjudication's own reliability statistics are a separate analysis over a separate table, and if they want a `publishable` run they want their own config whose units are ratings, not patients.

**The locked model-selection rule is a human decision between runs.** "Choose the model with the highest clinician-label AUROC among those that pass both development-set counterfactual checks; break ties in favor of the simpler regime" is an adaptive selection, and core [does not promise adaptive or sequential designs](design-principles.md#what-core-does-not-promise): the config fully determines the run. The route is two runs — a development run that reports every regime, and a confirmation run whose `parameters` name the selected one — with the selection recorded in the confirmation config's `replication.rationale` and its date in the study log. The `parameters_hash` on each confirmatory hypothesis is then exactly the evidence that the selection preceded the confirmation.

**The outcome firewall and honest broker are governance, not schema.** Core's contribution is that `hypotheses` are hashed with the config that declared them, so "we predicted this all along" is checkable. It has no notion of an access role, and adding one would be a tool claiming to enforce a policy it cannot see.

---

## What core refuses, and the route for each

| Requirement in the sources | Core's position | Route |
|---|---|---|
| Mean **absolute** paired probability difference | Not computed — a contrast is the mean of differences | Two one-sided bounds on the signed difference (recommended), or a `summary` `Estimate` |
| Equally weighted mean over two contrasts | An estimator over contrasts, so an interaction | `summary` `Estimate` |
| Monotonic 0.5-to-1.0 dose response | An ordering of contrasts, so an interaction | `summary` `Estimate` |
| Calibration intercept and slope | Model fitting, beyond core aggregation | Template `aggregate` if derivable per condition from the unit table, else `summary` `Estimate` |
| Gwet's AC1 with patient-bootstrap intervals | Not core aggregation | `summary` `Estimate` |
| Latin-square counterbalancing of effort by block position | Core gives a randomized complete block; it has no per-unit condition sequence | Accept RCBD, or carry position into a `summary` step from the recorded order |
| Class-ratio (10:1 versus 32:1) as a design axis | The roster is one roster per run; a ratio change is a different roster | Separate runs joined in a `study`; or one enriched roster with `weight_by`. **`study new` and `study add` ship as of H8b/H8c** — see [§ Executability on this build](#executability-on-this-build) |
| Disease-cap 200 versus 500 as a design axis | Same | Same |
| Prevalence-adjusted PPV at 1% and 3% | Not a design axis at all | `report.prevalences` as a list `Param`, computed in `aggregate` |
| Adaptive candidate selection inside one run | Refused | Two runs, selection recorded between them |
| Retry-on-transient-failure schedules | Core records attempts; it schedules nothing | Plugin `request.max_retries` / `backoff_secs`, recorded per unit |
| Wall-clock separation between batches | Core has no clock to enforce | Operator schedules; core records `started_at` and the realized order |

---

## Proposed plugin: `publishable-llm`

**Core-versus-plugin test.** Would "one request per unit against a hosted model, with a parsed output contract, token accounting, and a screening objective" be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? No. It is a plugin. Everything under `sweep`, `replication`, and `statistics` stays in core and the plugin declares nothing outside `parameters`.

This is the [third repository](#three-repositories-and-what-decides-the-seams), and it carries everything both experiment repos would otherwise have shared through an unpinned `src/common/`.

### Package

```
publishable-llm/
├── README.md                       # parameter table generated from parameter_spec
├── pyproject.toml
├── src/publishable_llm/
│   ├── templates/llm_screen.py     # @register_template("llm_screen")
│   ├── resolvers/patient.py        # @register_resolver("patient_trajectory")
│   ├── probes/deployment.py        # @register_probe("llm_deployment")
│   └── steps/                      # LLMRequestStep, CompileProgramStep
└── tests/test_llm_screen.py
```

```toml
[project.entry-points."publishable.templates"]
llm_screen = "publishable_llm.templates.llm_screen:LLMScreenTemplate"

[project.entry-points."publishable.resolvers"]
patient_trajectory = "publishable_llm.resolvers.patient:resolve"

[project.entry-points."publishable.probes"]
llm_deployment = "publishable_llm.probes.deployment:probe"
```

**No writers.** A compiled program is `.json`, reasoning summaries are `.jsonl`, a prompt template is a `str` written verbatim — every format this domain needs is one core already reads. Registering a writer here would claim an extension for no gain.

**One template, not several.** `output.kind` distinguishes a binary screen from a probability output, and `aggregate` returns the metrics defined for the declared kind. Two templates would duplicate the entire request and objective vocabulary to vary one enum.

### The apparatus probe is the sharpest fit, and it is also the operational risk

For an LLM benchmark the deployment revision *is* the intervention. `uv.lock` pins the client and nothing pinned the server — which is exactly the gap both source projects paper over with a prose note ("state explicitly if the provider does not return an immutable model revision").

```python
# src/publishable_llm/probes/deployment.py
from publishable import Apparatus, register_probe

@register_probe("llm_deployment")
def probe(cfg) -> Apparatus:
    client = connect(cfg.parameters.llm)                  # may read a swept parameter
    return Apparatus(facts={
        "provider":            cfg.parameters.llm.provider,
        "model_id":            client.resolved_model_id,
        "api_version":         client.api_version,
        "endpoint_host_sha256": sha256(client.host)[:16],  # hashed, not disclosed
        "deployment_revision": client.system_fingerprint,  # may be None
    })
```

```python
apparatus_probe = "llm_deployment"
apparatus_facts = ["provider", "model_id", "api_version",
                   "endpoint_host_sha256", "deployment_revision"]
```

**Three consequences worth stating before a run is scheduled.**

1. **`deployment_revision` is declared even though Azure does not contractually return one.** A declared fact must be *supplied as a key*, not answered: the probe returns `None` where the provider omits a fingerprint, core records `null`, and [the gate compares observations](reference.md#the-apparatus-core-can-only-observe) — so `null → "fp_a3c1"` is the field becoming available rather than the deployment moving. What declaring it buys — in the specification; see [§ Executability on this build](#executability-on-this-build) — is a warning, fired wherever a probe runs, plus an `unobserved` count, which is exactly the disclosure the source protocol asks for in prose when it says to "state explicitly if the provider does not return an immutable model revision."
2. **The probe runs before *every* execution.** A hosted deployment re-tuned during the E4 benchmark's 4.4 hours, or the C3 run's 12 hours, fails the run with no policy knob. That is correct — two deployment states are not one dataset — but it is an operational precondition, not a footnote. The ledger keeps both observations, so the evaluable earlier period stays reportable.
3. **Probes cost quota.** As specified they run at `dry-run`, at run start, and before every execution, never at `validate`, so the budget carries one authenticated call per execution on top of the cohort passes. How much of core's apparatus mechanism is built is a build fact that moves — probe dispatch itself has now been exercised, at `dry-run` and not at `validate`, against a real installed probe — see [§ Executability on this build](#executability-on-this-build) for what is true today rather than restating it here, since restating it here is exactly what leaves an undated claim behind for the next slice to falsify.

### Parameters

Grouped by what they control. Every one is under `parameters`; a template declares nothing outside it, so there is no top-level `llm:` block.

| Path | Type | Default | Why it is a parameter and not an apparatus fact |
|---|---|---|---|
| `llm.model` | str | required, `pattern=^[A-Za-z0-9._+-]+$` | You choose the deployment. The pattern is what makes it sweepable as a condition label |
| `llm.provider` | str | `azure_openai`, choices, `requires_env` | Chosen — and it carries its own credential per value, so a sweep spanning providers validates |
| `llm.api_version` | str | `null`, nullable | Chosen; the *served* version is an apparatus fact |
| `request.temperature` | float | `0.0`, ge 0 le 2 | Chosen |
| `request.max_output_tokens` | int | `512`, ge 1 | Chosen |
| `request.timeout_seconds` | int | `120`, ge 1 | Chosen |
| `request.reasoning_effort` | str | `null`, nullable, choices | Chosen — E4's whole axis |
| `request.reasoning_summary` | bool | `false` | Chosen |
| `request.cache` | bool | `false` | Chosen. Defaults off: a cache hit is not a measurement |
| `request.concurrency` | int | `1`, ge 1 | Chosen; each worker gets its own stream from `self.rng` |
| `request.max_retries` | int | `1`, ge 0 | Chosen |
| `request.backoff_secs` | list[int] | `[900]` | Chosen; a genuine list parameter |
| `prompt.strategy` | str | `zero_shot`, choices | Chosen |
| `prompt.program_id` | str | `null`, nullable, pattern | Sweepable identifier, resolved through `io.reuse_from` |
| `prompt.program_run` | str | `null`, nullable | Upstream run ID |
| `optimizer.name` | str | `none`, choices | Chosen |
| `optimizer.budget` | str | `medium`, choices | Chosen |
| `optimizer.seed` | int | `null`, nullable | Chosen |
| `objective.false_negative_credit` | float | `0.25`, ge 0 le 1 | E1's axis |
| `objective.invalid_credit` | float | `0.0`, ge 0 le 1 | Chosen |
| `output.kind` | str | `binary`, choices | Chosen |
| `output.field` | str | `growth_issue_screen` | Chosen |
| `output.threshold` | float | `0.5`, gt 0 lt 1 | Chosen |
| `report.prevalences` | list[float] | `[0.01, 0.03]` | Base rates to transport PPV to |
| `report.metrics` | list[str] | `[sensitivity, specificity, ppv, invalid_rate]` | **Which metrics `aggregate` returns** — see below |
| `pricing.prompt_per_mtok` | float | `null`, nullable, ge 0 | A local accounting assumption, not a fact about the run |
| `pricing.completion_per_mtok` | float | `null`, nullable, ge 0 | Same |

`default_repeats = 3`. Three is the smallest count at which `repeat_spread` is a number rather than an anecdote, and it is affordable because compilation is condition-scoped so a repeat costs one evaluation pass. A floor of 5 — the spec's generic convention-class example — would be a 5× metered-API cost default nobody chose; a floor of 1 would let a nondeterministic pipeline report no dispersion at all and draw no warning.

`required_env = []`. Nothing this template needs *unconditionally* — every credential it uses is selected by `llm.provider`, so all of them are declared in that parameter's `requires_env` and checked per condition.

### `report.metrics` exists because of the correction family

Every numeric metric a step or `aggregate` reports joins the correction family, and the family is comparisons × metrics. A screening template that returned everything the sources report — true/false positives and negatives, sensitivity, specificity, FPR, FNR, NPV, accuracy, balanced accuracy, F1, F0.5, sampled PPV, two prevalence-adjusted PPVs, Brier, calibration intercept and slope, the objective score, the all-negative reference, valid and invalid counts and rate — would be **23 metrics**. Against E6's 3 comparisons that is `family_size: 69`, and every interval in the run would be corrected for diagnostics nobody reads.

So `aggregate` returns only what `report.metrics` names, defaulting to four. Everything else is derivable from the per-unit table and belongs in `report`, which describes rather than compares. Confusion counts in particular are counts, not comparisons, and putting them in the family is the failure mode the spec names explicitly.

### `aggregate` and the cross-block `validate`

```python
def aggregate(self, units, cfg) -> dict:
    wanted = set(cfg.parameters.report.metrics)
    rows = [r for r in units if r.get("valid")]
    out = {}
    if "sensitivity" in wanted:
        pos = [r for r in rows if r["truth"]]
        out["sensitivity"] = sum(1 for r in pos if r["pred"]) / len(pos) if pos else None
    if "auroc" in wanted and cfg.parameters.output.kind == "probability":
        out["auroc"] = roc_auc(units.prob, units.truth)
    if "cost_usd" in wanted and cfg.parameters.pricing.prompt_per_mtok is not None:
        out["cost_usd"] = (sum(units.prompt_tokens) * cfg.parameters.pricing.prompt_per_mtok
                           + sum(units.completion_tokens) * cfg.parameters.pricing.completion_per_mtok) / 1e6
    return out
```

Because core can call this on a resampled table, every one of these is `basis: units` with a percentile interval — which is the whole argument for the plugin. The source's `run_usage_report.json` reports a token total with no denominator; the same numbers recorded per unit come back with an `n`, a `ci95`, and a `repeat_spread`.

The template's `validate` receives the whole config, and its cross-block rules are the strongest thing the plugin ships:

| Rule | Why core cannot know it |
|---|---|
| `optimizer.name != none` requires `data.units.holdout` or a `fold` repeat | Otherwise the compiled program is evaluated on the units it was compiled against. Core cannot tell that config from a legitimate one; the template can, because it knows its own pipeline compiles |
| `request.cache: true` with any `{kind: batch}` repeat is an error | A batch measures drift over separated executions; a cache returns the first answer *n* times. The source protocol requires `{"cache": false}` in prose |
| `prompt.strategy: compiled` requires `optimizer.name != none` or a non-null `prompt.program_run` | Nothing would supply a program |
| `output.kind: probability` requires `report.metrics` to name no binary-only metric | A threshold-free output has no confusion table until `output.threshold` is applied |
| `pricing.*` null while `report.metrics` names `cost_usd` — warning | The column would be null throughout |

### The request step

```python
class LLMRequestStep(BaseStep):
    scope = "repeat"
    nondeterministic = True          # required, or a batch repeat draws validate's warning

    def run(self, cfg, io):
        program = self.load_program(cfg, io)
        for unit in io.units:
            if unit.key in io.recorded_keys:
                continue                                    # resumed; already settled
            payload = self.serialize(unit, cfg)             # the experiment's hook
            if payload is None:
                io.skip(unit.key, "counterfactual not constructible for this span")
                continue
            r = self.request(program, payload, cfg)
            io.record(unit.key, {
                "pred": r.pred, "prob": r.prob, "truth": unit.consensus_label,
                "valid": r.valid, "invalid_reason": r.invalid_reason,
                "prompt_tokens": r.prompt_tokens, "completion_tokens": r.completion_tokens,
                "reasoning_tokens": r.reasoning_tokens, "latency_ms": r.latency_ms,
                "attempts": r.attempts, "finish_reason": r.finish_reason,
            })
        return {}
```

Everything here is a rule the spec already states: `io.recorded_keys` for resume, `io.skip` for design ineligibility, `io.record` values as a flat mapping of scalars, an empty return because the metrics are derived, and `nondeterministic = True` because the answer may move.

### What the plugin must not build

Retry ledgers, execution manifests, timestamped run directories, `reproduce` commands, cohort-summary and split JSON, usage reports, or anything under `sweep` / `replication` / `statistics`. Every one exists in the sources and every one is core's. A plugin that rebuilds them creates the second source of truth this project exists to prevent.

---

## Gaps this analysis found in the specification

Five: three closed in the specification, and two found on 2026-08-27 by installing the plugin this analysis proposes and putting its configs through the shipped tool — both **open**, and open here means what `docs/superpowers/spec-defects.md` says it means, since the charter is complete and no slice follows. Each is recorded with the case that surfaced it, because a gap's motivating example is the thing a later reader needs and the fixed text no longer carries.

1. **`apparatus_facts` conflated "must be yielded" with "gated on change."** A hosted deployment's revision fingerprint is returned on most calls and omitted on some. Declaring it made absence fatal; not declaring it left the change gate ambiguous, and the only safe move was to stop declaring a pin the study depends on. *Resolved* in `reference.md` § The apparatus core can only observe: a declared fact must be supplied as a **key**, `null` is a legal value meaning the apparatus did not answer, the gate compares two *observations* so an absence is never a change, and declaring the fact buys a warning, fired wherever a probe runs, plus an `unobserved` count. Every returned fact is gated whether declared or not, so there is no longer any reason to leave one out.
2. **`required_env` was static, but a sweep can span providers.** [E6](#e6--compiled-program-transfer) is the case: `validate` would either demand an Azure key from a run that never selects Azure or stay silent about one a later condition needs. *Resolved* by `reference.md` § A credential can belong to a parameter value — `Param(requires_env={...})` keyed by the parameter's `choices`, checked over the conditions the sweep actually resolves. The requirement travels with the decision that creates it, which is the same boundary `apparatus_facts` sits on read from the other side.
3. **Nothing showed the metered quantity before a run.** `limits.max_executions` warns on an execution count, which is not what a metered run is billed by: 20 executions over a 100,000-unit corpus is cheap by that measure and ruinous in practice. *Resolved* in `reference.md` § Before you spend it — `dry-run` now prints **unit-executions**, the sum of `len(io.units)` over every planned execution. Deliberately *not* resolved with a `limits` field: core has no price list and cannot count tokens, and a threshold in a currency it cannot measure would be the "looks handled and isn't" failure the correction family is held against. A budget that must be pre-registered is a template parameter, hashed with everything else.

4. **The unit table has no importable name, and a plugin has to annotate it.** *Open.* Core's own
   `BaseTemplate.aggregate` is annotated `units: "UnitTable"`, the class lives in `publishable.stats`,
   and `reference.md` names it **zero times** — [§ The importable surface](reference.md#the-importable-surface)
   is the enumerated list and `UnitTable` is not on it. The four operations the table supports are
   specified; the type is not, so a plugin author writing `def aggregate(self, units: UnitTable, cfg)`
   invents the import. `publishable-llm-screening` did exactly that, and on the shipped build the
   package does not import at all: `E-PLUGIN-LOAD`, *"cannot import name 'UnitTable' from
   'publishable'"* — one line in one shared import, and every artifact the distribution registers is
   unusable behind it. Two resolutions are available and this analysis names neither as preferred:
   export the name, or state in § The importable surface that the table is deliberately unnamed and
   `aggregate` is to be left unannotated. What is not available is silence, because the surface is
   annotated in core's own signature and copied from there. Measured on 2026-08-27 against commit
   `dc03ec4` — [§ Executability on this build](#executability-on-this-build) has the run.
5. **`unit-executions` does not count what a step does through `io.units.train`.** *Open.*
   [§ Before you spend it](reference.md#before-you-spend-it) defines the figure as the sum of
   `len(io.units)` over every planned execution and then makes a proportionality claim about it:
   *"where a step makes one request, one assay, or one simulation per unit, this is the count the bill
   is proportional to."* Under a declared `holdout` every scope is handed the **test** partition, with
   `.train` attached beside it, so a condition-scoped step fitting over `io.units.train` does one pass
   per training unit and contributes the test count. Measured: 48 handed and 192 in `.train` on a
   240-row roster at `frac: 0.2`. [E1](#e1--metric-calibration) and [E2](#e2--primary-optimization-comparison)
   are that shape exactly — MIPRO compilation at condition scope over the training half — and it is
   $380 of E1's $548. The arithmetic is faithful to the definition; the claim the definition is wrapped
   in is what fails, and it fails silently on the most expensive executions in this analysis.

---

## Executability on this build

Everything above asks what the specification permits. This section asks a narrower and far more perishable question — **what happens when these nine configs are put through `publishable validate` as the tool stands** — because an analysis that never tries is an analysis whose configs nobody has typed. Measured on 2026-08-15 against commit `2fdc957`, with the plugin assumed to exist and only *core* declarations judged. **The refusal table below is re-derived from `validate.py`'s emit sites rather than from a run**: the nine configs above are shown as YAML in this analysis but are not materialized as files in this repository, so there is nothing at that commit for `publishable validate` to actually read.

**None of the nine executes today.** Every config declares at least one thing this build refuses.

**None of the nine is blocked by a permanent design refusal, and that is the finding worth keeping.** Every interaction, dose-response ordering, mean-absolute difference, Latin square, and adaptive candidate selection had already been routed out of the YAML — into a `summary`-step `Estimate`, a second run, or a `report_by` stratum — so not one of them reaches `validate` as a declaration at all. The routing in [§ What core refuses, and the route for each](#what-core-refuses-and-the-route-for-each) holds up when it is checked mechanically. Every blocker below is a slice not yet built, and each names itself as such.

| Refusal | Runs it fires on |
|---|---|
| `E-DATA-RESOLVER-UNSUPPORTED` — the plugin registry is not implemented, so no resolver can be named | 9 of 9 |
| `E-DATA-HOLDOUT-UNSUPPORTED` | 6 of 9 — the screening roster; the shortcut roster declares `holdout: null` |
| `E-DATA-WEIGHT-CONTRAST` | 3 of 9 — C1, C2, C3 |
| `E-STATS-NULLTEST-UNSUPPORTED`, `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-CLUSTER-CONTRAST` | none |

**One refusal retired since the previous measurement, and it changes no run's outcome.** `E-STATS-RESAMPLE-UNSUPPORTED` fired on 8 of the 9 configs (every run but E5, whose `statistics.resample` is `null`) and is gone from `validate.py` as of H4a task 12 — a declared `resample` now validates on its own merits (method enum, the 80-draw floor, declared strata, roster presence, cluster count) instead of being refused wholesale. That is **one refusal retired that 8 of 9 configs hit, a regression preserved, and zero experiments newly executing**: E1–E6 still declare `holdout` and still earn `E-DATA-HOLDOUT-UNSUPPORTED`, C1–C3 still declare `weight_by` beside a baseline or contrast and still earn `E-DATA-WEIGHT-CONTRAST`, and all nine still declare a resolver and still earn `E-DATA-RESOLVER-UNSUPPORTED`. `validate` **collects rather than gates** — probed directly against a config declaring a resolver, a holdout, and a faulty resample together, all four codes (`E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-HOLDOUT-UNSUPPORTED`, `E-STATS-RESAMPLE-METHOD`, `E-STATS-RESAMPLE-N`) are reported in the same pass, none of them stopping the others from running — so no single blocker is "the" gate any of these configs stops at; each still-refused declaration earns its own finding independently of every other one on the same config. A retired-refusal count is not an executable-run count, and the two must not be conflated: this is a validate-time finding disappearing from a table, not a config newly reaching `run`.

**Six of the nine are one slice-set away.** E1, E2, E3, E4, and E6 validate completely clean once two things land: the plugin registry a resolver is looked up through, and `data.units.holdout`. E5 needs the same two and one correction of its own, described in [§ E5 — Binary-output repeatability](#e5--binary-output-repeatability). Only C1, C2, and C3 carry a second and independent blocker, `E-DATA-WEIGHT-CONTRAST` — the combination refusal described under [§ Shortcut: three runs](#shortcut-three-runs), which will lift when the paired estimators take weights.

**The machinery built most recently unblocks none of them.** `sweep.groups`, `allocation: between`, `assign`, `cluster_by`, `data.units.measurements`, `fold` repeats, and now `statistics.resample` are all implemented here, and no config in this analysis declares the first six — these designs are one roster, one within-subjects allocation, and `seed` or `batch` repeats throughout. The only recently built field any of them touches is `weight_by`, which is honored for a condition's own values and now fails in combination with a contrast, which is what all three shortcut runs publish. `resample`'s retirement removes a row from the table above without moving any of the nine configs closer to `run`, since the blockers that remain — the plugin registry, `holdout`, and `weight_by`-beside-a-contrast — are unrelated to it.

**Which commands and `io` methods exist is a build fact that moves, so this paragraph states none.** Every claim about what dispatches, what refuses, and what a command prints lives in the dated entries below, each pinned to a commit — read the most recent one. Stating a build state here is what left this paragraph asserting that `study` and `reproduce` print `unknown command` long after they printed *specified but not built*, and a later entry corrected the sibling sentence without reaching this one.

**Why this section is dated.** Every refusal above is a build fact with a shelf life, and the commit is what makes the claim re-checkable rather than merely re-assertable. The cost and execution figures below are unaffected either way: they describe what these designs *would* meter, which is a property of the configs and not of the build.

### Measured on 2026-08-16 against commit `d72724bc150ec0d2373ccd71a9784d994215f90a`

H3d is complete on its `h3d-fixed-holdout` branch and retires `E-DATA-HOLDOUT-UNSUPPORTED` there; the commit above is a branch commit, not one reachable from `main`, and is pinned here rather than on `main` because that branch is what this measurement was run against. This is the re-measurement that finding calls for, run rather than re-derived — but only over the declarations `validate` can actually see with no plugin installed, which is narrower than "each config as written," and the narrowing is named rather than left implicit:

- **`entrypoint` and `experiment_type` point at this repo's own scaffolded `generic` demo, not at `growth_screen`/`growth_shortcut`.** Neither plugin is installed in any build, so an unsubstituted config fails at template resolution (`E-TEMPLATE-UNKNOWN`) or at entrypoint import (`E-ENTRYPOINT-IMPORT`) before reaching any of the codes this measurement is about — the identical "plugin assumed to exist" stance the previous measurement already took, made concrete instead of assumed.
- **`data.units` (`from`, `attributes`, `holdout`, `weight_by`) and `statistics.resample` were carried over from the YAML shown above verbatim**, against a 240-row synthetic table standing in for `growth-screen`'s patient index. `statistics.contrasts` was carried over as a **stand-in single entry** over the demo template's own axis, not the declared set — C2 declares two contrasts and C3 declares four, and only one of each was run. That changes the comparison count `E-DATA-WEIGHT-CONTRAST`'s message prints (it counts comparisons off whatever is declared) and nothing about whether the code fires, since the refusal is keyed to `weight_by` sitting beside *any* baseline or contrast. `parameters`, the real `sweep`, `replication`, `statistics.report_by` and `hypotheses` were **not** carried over — each config was run with the scaffold's own stand-in single-axis sweep and default seed-repeat in their place, because the demo entrypoint declares neither the real parameter names nor the `step03_screen`/`step05_agreement` steps the real hypotheses name. A hypothesis naming an undeclared step earns `E-HYPOTHESIS-METRIC` on this entrypoint regardless of anything H3d touched, so testing the real `hypotheses` blocks here would measure the substitution, not the build — they are left assumed under "the plugin exists," the same stance the previous measurement took for the whole config.
- **For E1, E2, E3, E4, E5 and E6**, `data.units.from` was additionally tried as `index.csv` beside the as-declared `{resolver: patient_trajectory}` — the table-roster substitution the analysis itself does not make, run here rather than left hypothetical.

**What this measurement therefore answers, precisely:** does the `data.units.holdout`/`weight_by`/`from` block and the `statistics.resample`/`contrasts` block, taken verbatim from each config above, earn `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`, or `E-DATA-WEIGHT-CONTRAST` on this build. It does not re-measure whether each config's real sweep, hypotheses, or `report_by` block validates — those were never in question for H3d and are unaffected by it.

**`E-DATA-HOLDOUT-UNSUPPORTED` did not appear on any of the nine, at any substitution.** Grepping the tool's own source confirms it: the code is gone from `validate.py`. That is the retirement working as designed.

**Zero of the nine execute, and the honest count is not "6 of 9 unblocked."** All nine still declare a resolver and still earn `E-DATA-RESOLVER-UNSUPPORTED` — this is H7b's gate, untouched by H3d. C1–C3 keep `E-DATA-WEIGHT-CONTRAST` on top of that, exactly as before.

| Config | `validate` reports on the transplanted `data`/`statistics` blocks | Would execute? |
|---|---|---|
| E1 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| E2 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| E3 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| E4 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| E5 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| E6 | `E-DATA-RESOLVER-UNSUPPORTED` | No — blocked on the plugin registry |
| C1 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two independent blockers |
| C2 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two independent blockers |
| C3 | `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` | No — two independent blockers |

One warning the fixture also produced is left out of the table above because it is a property of the fixture, not of these designs: `W-DATA-CLUSTER-UNDECLARED` on `age_band`, an artifact of the synthetic table's own three-band shape rather than of `growth-screen`'s real roster. It does not bear on `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`, or `E-DATA-WEIGHT-CONTRAST`. (An earlier draft of this section also reported `W-REPL-DETERMINISTIC` on E5. That is withdrawn as unattributable, not affirmed as wrong: `validate.py`'s only emit site for that code requires a `batch` level in `replication.repeats`, `materialize.py` writes a default `{kind: seed, ...}` repeat, and the scope statement two paragraphs up says `replication` was not carried over for any of the nine — so the code cannot fire under the scope this measurement declares, whatever the scratch run actually did. Which of the two claims was originally at fault was not re-run to check; only that they cannot both stand is established.)

**Correction (merge, 2026-08-16), replacing this section's opening clause about reachability:** H3d merged to `main` on 2026-08-16. The commit this section pins is therefore reachable from `main` now, where the opener says it is not — that sentence was true when written and the merge is what falsified it. The pin itself still stands and is still the right one: it names the tree the measurement actually ran against, which is what makes the measurement reproducible.

**Correction (H3d whole-branch review, 2026-08-16), replacing the withdrawal's last sentence above:** the reported `W-REPL-DETERMINISTIC` on E5, not the scope statement, was the false claim. The two are not symmetrically supported — the scope statement is corroborated by two independent facts already cited in this section (`materialize.py` writes a default `{kind: seed, ...}` repeat; the warning's sole emit site requires a `batch` level), while the reported warning is corroborated by nothing beyond its own appearance in an earlier draft. The residual uncertainty does not move any claim this section makes: none of the three codes it answers for — `E-DATA-HOLDOUT-UNSUPPORTED`, `E-DATA-RESOLVER-UNSUPPORTED`, `E-DATA-WEIGHT-CONTRAST` — reads `replication`, and neither does `W-DATA-CLUSTER-UNDECLARED`. Not re-run to reach this: the determination is made from the evidence already in hand rather than from a fresh measurement. The only change to `src/` after the commit this section pins is a docstring in `artifacts.py`, so no executable code moved and the measurement still describes the build it names.

**Under the table-roster substitution, the generous count is three, not six.** E1, E2 and E5's transplanted blocks validate with zero errors. E3, E4 and E6's transplanted blocks validate equally clean under the same substitution — the same zero-error result — **but still cannot run**: each reads its frozen compiled program through `io.reuse_from`, and `grep -rn "reuse_from" src/publishable/` returns nothing in this build. A block validating clean is not a config that can execute when the method its steps call does not exist; § E3 — Cohort-definition sensitivity, § E6 — Compiled-program transfer, and the `io.reuse_from` paragraph above (§ Executability on this build) are what this depends on, not anything H3d touched. So "six of nine, one substitution away" is not the number this measurement supports — three are one substitution away from `validate`, and the other three need that same substitution plus a method this build does not have.

Whether C1–C3 carry that same `io.reuse_from` dependency is not settled by this measurement. The only evidence available for E3/E4/E6, just above, is a `src/` grep, because `io.reuse_from` is a step-level call invisible to any config — the same is true for C1–C3, so their YAML naming non-fine-tuned regimes (`utilization_only`/`clinical_physiology`/`zero_shot`) is not evidence of absence, only evidence of no *declared* fine-tuned artifact. § Shortcut: three runs, in this same document, points the other way: the roster all three share is annotated `holdout: null   # confirmation run: the roster IS the confirmation set`, and the paragraph above it states "the confirmation run reads the fitted artifact with `io.reuse_from`." Settling this would take reading the steps `growth-shortcut`'s entrypoint registers, which this measurement did not do. Either way, retiring `E-DATA-WEIGHT-CONTRAST` (H4b) does not make C1–C3 executable on its own, since all nine, C1–C3 included, still declare a resolver.

**The mutation this table rests on.** E1's clean validation under the table substitution was proven discriminating, not assumed: setting `data.units.holdout.frac` to `0` on the otherwise-clean block immediately produces `E-DATA-HOLDOUT-FRAC` ("is 0, and a test fraction is strictly between 0 and 1"), and reverting the field restores the zero-error result byte-for-byte. A block that could not fail this way would not be a measurement.

**Confirms the previous measurement's structure and corrects its headline framing.** `E-DATA-HOLDOUT-UNSUPPORTED`'s retirement, `E-DATA-RESOLVER-UNSUPPORTED` firing on all nine, and `E-DATA-WEIGHT-CONTRAST` firing on exactly C1–C3 are all confirmed by running rather than by re-deriving from `validate.py`'s emit sites — over the `data`/`statistics` blocks named above, which is exactly the surface H3d and H7b act on. What this measurement does **not** confirm is "6 of 9 unblocked" as an executable count: that figure was always a count of configs that stop hitting one particular refusal, not a count of configs that reach `run`, and the honest generous figure under a substitution nobody has written is three.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 1954 passed + 2 xfailed, ruff and mypy both clean — unaffected by this section, which only runs `validate` against scratch files outside the repo.

---

### Measured on 2026-08-16 against commit `c42eb877c304c308a7b8530720ca7ff9cf842c54` — after H7c

H7c (credentials and secrets) merged to `main` at the commit above. **Nothing in the picture above
changes: still zero of nine execute, and H7c retires no refusal** — the credential family never had one,
only checks that were specified and unbuilt. What changed is narrower and is a prerequisite rather than a
result.

- **The plugin this analysis describes can now be written.** `llm_screen`'s `llm.provider` parameter is
  declared with `requires_env`, and `Param.__init__` rejected that keyword outright until this slice —
  verified here by constructing exactly that `Param` against the merged build. That was a fourth,
  unrecorded blocker sitting behind the three § Executability names, and it blocked H7b's payoff rather
  than this analysis's: the registry H7b builds resolves a plugin that could not have been authored.
- **`E-DATA-RESOLVER-UNSUPPORTED` is untouched** and still the gate all nine hit as written. H7b owns it.
- **What is newly checkable, once a plugin exists:** a template's `required_env` and a swept value's
  `requires_env` are both reported before anything executes, and a declared credential's value is kept
  out of `run.yaml`, `executions.jsonl` and both streams. The limit is stated rather than implied — core
  redacts only values it read for a *declared* variable, so a step reaching `os.environ` itself holds a
  value core never saw.

**Not re-measured:** the nine configs were not re-run through `validate` for this entry. They hit
`E-DATA-RESOLVER-UNSUPPORTED` at the same point as before, and H7c adds no check ahead of it that any of
them can reach — none declares `required_env`, and none can declare `requires_env` without the plugin.
The two claims above that *are* dated were each verified against the merged build.


### Measured on 2026-08-17 against commit `959cc8d165f1f0d904d517526e0ab51c58741df3` — after H7b Part A

H7b **Part A** merged at the commit above. **Nothing in the picture above changes: still zero of nine
execute, and Part A retires no refusal.** `E-DATA-RESOLVER-UNSUPPORTED` is alive and is **Part B's** to
retire, together with the resolver dispatch that would make one run.

- **The registries the analysis's plugin needs now exist.** A template, a resolver, a probe, a reader
  and a writer can each be registered from an installed distribution, and `validate` resolves any of
  those names **from package metadata, importing nothing** — the property that lets a config be checked
  on a machine where the plugin is declared but broken.
- **One message in this area changed and it is worth noting for anyone re-reading older output.**
  `E-DATA-RESOLVER-UNSUPPORTED` used to say *the plugin registry is not implemented in this build*.
  Part A implemented it, so the refusal now says what is actually true: **a resolver cannot be
  dispatched** in this build.
- **What still blocks all nine, unchanged and re-verified:** the resolver dispatch (Part B),
  `io.reuse_from` (unbuilt and unowned by any H7 sub-slice), and the apparatus probe (H7d).

**Not re-measured:** the nine configs were not re-run through `validate` for this entry. Part A adds no
check ahead of `E-DATA-RESOLVER-UNSUPPORTED` that any of them reaches, because none declares an entry
point and none can until a plugin is installed. The claims above are about the build, and each was
verified against the merged tree rather than carried from the plan.


### Measured on 2026-08-17 against commit `f9d99148c3be5590420e7cff3a3598f2d529ecf2` — after H7b Part B

H7b **Part B** retires `E-DATA-RESOLVER-UNSUPPORTED`; this measurement was taken against the commit
above, on its branch, and Part B merged to `main` the same day. This is the
first re-measurement in this section to actually **run** every one of the nine configs' `data`/
`statistics` blocks through `validate_config`, rather than re-deriving from emit sites or extending a
prior grep — the same discipline the 2026-08-16 (H3d) entry set and the one this entry's own
qualifications below narrow in the same direction the others have.

**H7b Part B retires one refusal that 9 of 9 configs hit** (`E-DATA-RESOLVER-UNSUPPORTED`), **and
three experiments — E1, E2 and E5 — have no remaining core-side blocker.** That is the first
non-zero executable count this project has produced. It is conditional on the plugin being written
and installed (`plugin new` scaffolds it; a hand-written package works, and this measurement uses
one), and on accepting that a declared apparatus probe is neither executed nor recorded — the
false `apparatus: null` record filed separately below. Six stay blocked, on two causes neither of
which is H7b's: `io.reuse_from` (unbuilt, **unowned**) for E3, E4 and E6, and `E-DATA-WEIGHT-CONTRAST`
(H4b) for C1, C2 and C3.

**Scope, narrowed the same way the 2026-08-16 entry narrowed it, and for the same reason.**
`entrypoint`/`experiment_type` point at this repo's own scaffolded `generic` demo — no
`growth_screen`/`growth_shortcut` plugin exists to install — but `data.units.from` is the **real**
`{resolver: patient_trajectory}` declaration this time, resolved by a hand-written resolver plugin
installed for this measurement (60 synthetic units carrying every attribute any of the nine configs
name). `data.units` and `statistics` were carried over from the YAML shown above verbatim for the six
screening runs and the three shortcut runs. `sweep`, `parameters`, `replication` and `hypotheses`
were **not** carried over, for the identical reason the earlier entry gives: the demo entrypoint
declares neither the real parameter names nor the real steps a real hypothesis names. E2's baseline
and C1's baseline, and C2/C3's one stand-in `statistics.contrasts` entry each, are declared over the
demo template's own `analysis.method` axis rather than the real one — the same substitution the
2026-08-16 entry made for the identical reason, checking whether the *combination* (`weight_by`
beside a resolved comparison) is refused, not the real design's own labels.

| Config | `validate` reports on the transplanted `data`/`statistics` blocks | Would execute? |
|---|---|---|
| E1 | *(none)* | **Yes** — no remaining core-side blocker |
| E2 | *(none)* | **Yes** — no remaining core-side blocker |
| E3 | *(none)* | No — blocked on `io.reuse_from` (invisible to `validate`; a step-level call) |
| E4 | *(none)* | No — blocked on `io.reuse_from` |
| E5 | *(none)* | **Yes** — no remaining core-side blocker |
| E6 | *(none)* | No — blocked on `io.reuse_from` |
| C1 | `E-DATA-WEIGHT-CONTRAST` | No — H4b's |
| C2 | `E-DATA-WEIGHT-CONTRAST` | No — H4b's |
| C3 | `E-DATA-WEIGHT-CONTRAST` | No — H4b's |

Every one of the nine also reports `W-DATA-CLUSTER-UNDECLARED`, left out of the table for the same
reason the 2026-08-16 entry excluded its own warning: it is an artifact of the synthetic resolver's
three-band `age_band`/`count_stratum` shape, not of a real roster, and it bears on none of the codes
this table answers for.

**The mutation this table rests on, re-run rather than carried.** E1's clean validation was proven
discriminating again at this build: setting `data.units.holdout.frac` to `0` on the otherwise-clean
block immediately produces `E-DATA-HOLDOUT-FRAC`, and reverting the field restores the zero-error
result. A block that could not fail this way would not be a measurement.

**What this measurement does not settle.** Whether E3, E4 and E6's `data`/`statistics` blocks are
the *only* thing standing between them and `run` is not answered here — `io.reuse_from` is a step-level
call invisible to any config, so a clean `validate` result is necessary and not sufficient for those
three, exactly as the 2026-08-16 entry found for the identical reason. The same limit cuts the other
way for E1, E2 and E5: a clean `validate` is not sufficient to establish "no remaining core-side
blocker" for them either, and their "Yes" rests on reading each design's prose for other unbuilt
dependencies — the same check the three "No" rows needed and got, not on `validate`'s silence. Nothing
about the apparatus probe's execution is exercised either: none of the nine configs used here declares
one, since the demo entrypoint carries no `apparatus_probe`.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 2102 passed + 1 skipped + 2 xfailed, ruff and
mypy both clean.

### Measured on 2026-08-17 against commit `0f15c3f904e8ddc34d5533158e3f7478f28af977` — after H4b-1

H4b-1 retires `E-DATA-WEIGHT-CONTRAST`; this measurement was taken against the commit above, on its
branch. Every one of the nine configs' `data`/`statistics` blocks was run through `validate_config`
again rather than re-derived from the previous entry.

**H4b-1 retires one refusal that 3 of 9 configs hit** (`E-DATA-WEIGHT-CONTRAST`) — the last core-side
refusal C1, C2 and C3 carry — and takes the *no-remaining-core-side-blocker* count from **three to
six**: E1, E2, E5 unchanged, C1, C2, C3 newly. **The executable count stays at three.** C1–C3's
`io.reuse_from` dependency is unsettled, this analysis says so in its own words, and this measurement
does not settle it either — it is a step-level call invisible to any config, and `growth-shortcut`'s
steps do not exist.

**What H4b-1 changed for these three beyond the refusal.** `statistics.resample.stratify_by` is now
honoured on a contrast's draw, not only per condition — all three declare
`stratify_by: [consensus_label, count_stratum]`, and before this slice that declaration was silently
dropped on every delta. Their weighted contrasts record `weighted_by` and an `n_paired_effective` from
Kish over the paired intersection either way, and a corrected bound built from the same weighted
evidence as the raw one — but not identically for all three: C2 and C3 contrast a recorded column
(`step03_screen.prob`) and get a weighted `cohens_d` alongside; C1 contrasts a *derived* metric
(`step03_screen.auroc`), which core does not weight, so its `cohens_d` stays `null` and its `method`
stays the unweighted `paired_percentile_over_units`, exactly as `reference.md` § Weighted samples
specifies for a derived contrast under a weight.

**One declaration all three carry is still not honoured**: a `report_by` level's recorded-column
interval stays `t_over_units` under a declared `resample`, which `docs/superpowers/spec-defects.md`
records with a named owner (H4 Statistics; not H4b-1 or H4b-2, since a `report_by` level's own
`resample_columns` threading is neither a weight nor a cluster question). So "every field they
declare is honoured" — the second clause of the no-remaining-core-side-blocker standard — is true of
their `data.units` and `statistics.resample` blocks and not of their `statistics.report_by`.

**Substitution, narrowed the same way the 2026-08-17 (Part B) entry narrowed it, and for the same
reason.** `entrypoint`/`experiment_type` again point at this repo's own scaffolded `generic` demo, and
`data.units.from` is again the real `{resolver: patient_trajectory}` declaration, resolved by a
hand-written resolver plugin installed for this measurement (60 synthetic units carrying every
attribute any of the nine configs name). `data.units` and `statistics` were carried over from the YAML
shown above verbatim for all nine. `sweep`, `parameters`, `replication` and `hypotheses` were **not**
carried over except where a comparison had to exist to check the retired combination at all: E2's and
C1's baseline, and C2's and C3's one stand-in `statistics.contrasts` entry each, are declared over the
demo template's own `analysis.method` axis rather than the real one, exactly as Part B's own entry did.

| Config | `validate` reports on the transplanted `data`/`statistics` blocks | Would execute? |
|---|---|---|
| E1 | *(none)* | **Yes** — no remaining core-side blocker |
| E2 | *(none)* | **Yes** — no remaining core-side blocker |
| E3 | *(none)* | No — blocked on `io.reuse_from` (invisible to `validate`; a step-level call) |
| E4 | *(none)* | No — blocked on `io.reuse_from` |
| E5 | *(none)* | **Yes** — no remaining core-side blocker |
| E6 | *(none)* | No — blocked on `io.reuse_from` |
| C1 | *(none)* | No — blocked on `io.reuse_from` |
| C2 | *(none)* | No — blocked on `io.reuse_from` |
| C3 | *(none)* | No — blocked on `io.reuse_from` |

Every one of the nine also reports `W-DATA-CLUSTER-UNDECLARED`, left out of the table for the same
reason the 2026-08-17 (Part B) entry excluded its own warning: it is an artifact of the synthetic
resolver's three-band `age_band`/`count_stratum` shape, not of a real roster, and it bears on none of
the codes this table answers for.

**The mutation this table rests on, re-run rather than carried.** E1's clean validation was proven
discriminating again at this build: setting `data.units.holdout.frac` to `0` on the otherwise-clean
block immediately produces `E-DATA-HOLDOUT-FRAC`, and reverting the field restores the zero-error
result. A block that could not fail this way would not be a measurement.

**What this measurement does not settle**, unchanged from Part B's own qualification: whether E3, E4,
E6, C1, C2 and C3's `data`/`statistics` blocks are the *only* thing standing between them and `run` is
not answered here — `io.reuse_from` is a step-level call invisible to any config, so a clean `validate`
result is necessary and not sufficient for any of the six blocked rows, C1–C3 included: their own
"no remaining core-side blocker" reading (the prose above the table, not the table's own "Would
execute?" column) rests on the same `report_by`-under-`resample` gap two paragraphs above, which
`validate` cannot see because it is a property of what `cli.command_run` threads, not of the
declaration. The same limit cuts the other way for the three marked "Yes": a clean `validate` is not
sufficient to establish "no remaining core-side blocker" for them either, and the "Yes" rests on
reading each design's prose for other unbuilt dependencies. Nothing about the apparatus probe's
execution is exercised either, for the same
reason Part B's entry gives.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 2159 passed + 1 skipped + 2 xfailed, ruff and
mypy both clean.

### Measured on 2026-08-18 against commit `dcb7ed0145851122270a1bc2c82bcedc1d4e18cf` — after H4b-2

H4b-2 retires `E-DATA-CLUSTER-CONTRAST` and mints `E-DATA-WEIGHT-CLUSTER-CONTRAST`; this measurement
was taken against the commit above, on its branch. Every one of the nine configs' `data`/`statistics`
blocks was run through `validate_config`, the same discipline the Part B and H4b-1 entries set.

**H4b-2 unblocks zero configs, and both counts stand unchanged: six with no remaining core-side
blocker, three executable.** No config in this analysis declares `data.units.cluster_by` — measured
on the file above, two hits and both `cluster_by: null` — so the refusal H4b-2 retires is one no
experiment here hits, and a retired refusal is not an execution in any case.

**The newly minted refusal reaches none of the nine either.** `E-DATA-WEIGHT-CLUSTER-CONTRAST`
requires both `weight_by` and `cluster_by` beside a comparison; C1, C2 and C3 declare the first and
none of the nine declares the second.

**Scope, narrowed the same way the Part B and H4b-1 entries narrowed it, and for a further reason
specific to this build.** `entrypoint`/`experiment_type` again point at this repo's own scaffolded
`generic` demo. `data.units.from` here is a **table-source stand-in**, not the hand-written resolver
plugin the two prior entries installed: a 60-unit roster carrying every attribute any of the nine
configs' `data.units.attributes`, `statistics.report_by` or `statistics.resample.stratify_by` names
(`age_band`, `consensus_label`, `count_stratum`, `dx_family`, `record_source`, `sex`, `span_days`,
`truth`, `visit_density`), banded three ways so every `stratify_by`/`report_by` target resolves.
`data.units`'s other fields (`allocation`, `holdout`, `measurements`) and every config's own
`statistics` block were carried over verbatim. `sweep`/`parameters`/`replication`/`hypotheses` were
not, for the reason the two prior entries give: the demo entrypoint declares neither the real
parameter names nor the real steps a real hypothesis names. E2's and C1's baseline, and C2's and
C3's one stand-in `statistics.contrasts` entry each, are declared over the demo template's own
`analysis.method` axis, exactly as the Part B and H4b-1 entries did.

| Config | `validate` reports on the transplanted `data`/`statistics` blocks | Would execute? |
|---|---|---|
| E1 | *(none)* | **Yes** — no remaining core-side blocker |
| E2 | *(none)* | **Yes** — no remaining core-side blocker |
| E3 | *(none)* | No — blocked on `io.reuse_from` (invisible to `validate`; a step-level call) |
| E4 | *(none)* | No — blocked on `io.reuse_from` |
| E5 | *(none)* | **Yes** — no remaining core-side blocker |
| E6 | *(none)* | No — blocked on `io.reuse_from` |
| C1 | *(none)* | No — blocked on `io.reuse_from` (no remaining core-side blocker either, per H4b-1) |
| C2 | *(none)* | No — blocked on `io.reuse_from` (no remaining core-side blocker either, per H4b-1) |
| C3 | *(none)* | No — blocked on `io.reuse_from` (no remaining core-side blocker either, per H4b-1) |

The table's own "no remaining core-side blocker" annotation and the prose's count above answer for
the same six rows, not three: C1–C3 carry it too, parenthetically, so a reader taking the table's
`Yes` cells alone does not undercount. Every one of the nine also reports `W-DATA-CLUSTER-UNDECLARED`,
left out of the table for the same reason the Part B and H4b-1 entries excluded their own: an artifact
of the synthetic roster's banded shape, not of a real roster, bearing on none of the codes this table
answers for. **Can-fail
control**, on the same transplant: adding `cluster_by: age_band` to C1's `data.units` block beside its
declared `weight_by` draws exactly `{E-DATA-WEIGHT-CLUSTER-CONTRAST}`; the same addition with
`weight_by` stripped stays clean. A table that could not fail either way would not be a measurement.

**What H4b-2 changes for a config that *did* declare a cluster**, stated as specification rather than
as a measurement of these nine: a clustered comparison's delta takes
`paired_t_over_units_clustered` or `paired_percentile_over_units_clustered`, its `method` says which,
and `n_paired_clusters` travels beside `n_paired`. And one live defect closes for configs that
declare **no** cluster at all: a contrast draw whose every stratum's rows are identical now reports
`ci95: null` rather than a zero-width interval, which is reachable from a near-unique
`resample.stratify_by` — all three C configs declare `stratify_by: [consensus_label,
count_stratum]`, whose strata are not near-unique on the roster this analysis describes, so it is a
closed hazard rather than a changed number for them.

**Unchanged and still outstanding**, carried from the H4b-1 entry rather than re-derived: E3, E4, E6,
C1, C2 and C3 remain blocked on `io.reuse_from`, which is unbuilt and unowned and invisible to
`validate`; and all three C configs still meet a `report_by` level's recorded-column interval staying
`t_over_units` under a declared `resample`, which H4b-2 declined in writing and re-owned to H4c.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 2198 passed + 1 skipped + 2 xfailed, ruff and
mypy both clean.

### Measured on 2026-08-18 against commit `6b9bf119a9706aeb34be7e10a4311280e1b9e5d9` — after H4c

H4c retires `E-DATA-ALLOCATION-CONTRAST` and mints `E-DATA-WEIGHT-ALLOCATION-CONTRAST`. **H4c unblocks
zero configs, and both counts stay unmoved: six with no remaining core-side blocker, three
executable.** Neither number changes.

**The measurement, with a control that can fail.** Both refusals fire only on a resolved comparison
whose two conditions differ on a declared `sweep.groups` axis — the group-axis machinery H4b-2's own
entry above already measured as untouched by any of the nine. Re-run at this commit rather than
carried: `grep -c 'allocation: within' docs/feasibility-llm-growth-studies.md` → 3 (two config blocks
and one prose sentence); `grep -c 'allocation: between' docs/feasibility-llm-growth-studies.md` → 1,
**read** and confirmed to be the prose sentence above ("The machinery built most recently unblocks
none of them") listing fields no config in this analysis declares, not a config's own
`data.units.allocation`; `grep -n 'groups:'
docs/feasibility-llm-growth-studies.md` → two hits, both `groups: []`. No config here declares a
group axis, so neither the retired refusal nor the minted one has anything to reach.

**The refusal row.** `E-DATA-ALLOCATION-CONTRAST` retired, `E-DATA-WEIGHT-ALLOCATION-CONTRAST` minted,
net zero — and no config hits either, the same measurement above states from the other direction.
**The can-fail control**, on a minimal fixture rather than the nine-config transplant (which has
nothing to add here, since none of the nine touches `sweep.groups` at all): a `data.units.allocation:
between` design over a two-level `sweep.groups` axis, declaring a cross-arm `statistics.contrasts`
entry with no `weight_by`, now validates with an exact empty error set where it used to draw
`E-DATA-ALLOCATION-CONTRAST` alone — confirmed by this repo's own
`tests/test_validate.py::test_a_contrast_beside_groups_and_cluster_by_now_validates_clean`. The same
shape with `weight_by` declared instead of `cluster_by` draws exactly
`{E-DATA-WEIGHT-ALLOCATION-CONTRAST}` —
`tests/test_validate.py::test_a_weighted_cross_arm_contrast_draws_the_weight_allocation_refusal`. A
measurement that could not fail either way would not be one.

**The sentence that must not be roundable: a retired-refusal count is not an executable-run count.**
Both review verdicts on H4b-1 faulted exactly that conflation, and a *correction* to a report on
H4b-2 inverted the same two numbers and named a **retired** refusal as live — this entry states the
six and the three in those words, unmoved, rather than letting "H4c retires a refusal" round up to
"H4c unblocks a config."

**Unchanged and still outstanding**, carried from the H4b-2 entry rather than re-derived: E3, E4, E6,
C1, C2 and C3 remain blocked on `io.reuse_from`; all three C configs still meet a `report_by` level's
recorded-column interval staying `t_over_units` under a declared `resample`, re-declined in writing
by H4c (`docs/superpowers/spec-defects.md`) and owned by **H4d**, terminally.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 2272 passed + 1 skipped + 2 xfailed, ruff and
mypy both clean.

### Measured on 2026-08-19 against commit `d0e9345` — after H4d

H4d retires `E-STATS-NULLTEST-UNSUPPORTED` and builds `statistics.null_test` end to end — a `method`
enum, an `n` floor, a `shuffle` check, a cluster-level derivation, a group-axis p-value home, a
per-condition derived one, and `fdr_bh` made real. **H4d unblocks ZERO configs, and both counts stay
unmoved: six with no remaining core-side blocker, three executable.** Neither number moves, on the
same measurement method every entry above uses: each config's `data`/`statistics` blocks run through
`validate_config`.

**The measurement, self-matches named rather than filtered out** (`CLAUDE.md`: never filter a
sweep's output, filter the file list — and this file is now the one place both the pattern and this
sentence describing it live). Every `statistics` block in this analysis holds an explicit null for
the field this slice builds: `grep -c '  null_test: null' docs/feasibility-llm-growth-studies.md` →
9, eight config blocks and this sentence's own grep command, which `_check_null_test`'s own
`if not isinstance(null_test, dict) or not null_test: return` treats as undeclared, the identical
truthy guard `_check_unimplemented`'s retired check read. **Zero configs declare `fdr_bh`**:
`grep -c '  correction: holm'` → 8 (seven config blocks, one self-match) and
`grep -c '  correction: none'` → 2 (one config block, one self-match), seven plus one config block
is every `statistics` block this analysis has, and neither pattern is `fdr_bh`. **The control**:
`grep -c '  correction: fdr_bh'` → 1, and reading the hit shows it is this sentence's own grep
command rather than a config — proving the sweep can find a real hit if one existed rather than
passing vacuously by a pattern nothing ever matches. So no config reaches any of the five narrow
codes this slice mints (`-METHOD`, `-N`, `-SHUFFLE`, `-UNITS`, `-LEVEL`), and the one warning this
slice narrows — `W-STATS-CORRECTION-INAPPLICABLE` — fires for none of them either, since none
declares `fdr_bh` for it to fire under.

**A retired-refusal count is not an executable-run count**, the sentence the H4c entry above already
states and this one repeats rather than lets drift: H4d's net is one `-UNSUPPORTED` retired, five
narrow refusals minted in its place, `E-STATS-NULLTEST-REPORTBY` minted, and one prior filing
(`E-DATA-CLUSTER-DERIVED`) claimed — not a refusal count that improves, and not a number that moves
here.

**Unchanged and still outstanding**, carried from the H4c entry rather than re-derived: E3, E4, E6,
C1, C2 and C3 remain blocked on `io.reuse_from`; all three C configs still meet the `report_by`
`resample_columns` asymmetry, converted to a documented limitation by H4d task 24 rather than
deferred a fifth time.

Full local `pytest`/`ruff`/`mypy` gates at this commit: 2359 passed + 1 skipped + 2 xfailed, ruff and
mypy both clean.

### Measured on 2026-08-19 against commit `06bc38d` — after H7d Part A

H7d Part A opens the apparatus: a template declaring an `apparatus_probe` no longer writes a false
`apparatus: null`. Core resolves the declared probe through the same three-step dispatch a resolver
already uses, calls it at run start and before every execution, projects its returned facts onto a
declared `apparatus_facts` set, refuses a fact that is a credential core read (by exact value **or**
substring containment, closed by this same slice's whole-branch fix round) or a value core cannot
encode, records every observation in an append-only ledger (`apparatus/probes.jsonl`), and
assembles `provenance.apparatus`'s five sub-keys from what it observed. **H7d Part A unblocks ZERO
configs, and both counts stay unmoved: six with no remaining core-side blocker, three executable.**
Confirmed by the whole-branch review's own re-measurement through `validate_config` on E1 and
C1's `data`/`statistics` blocks — the same method every entry above uses, re-cited here rather than
re-run a third time on the identical fixture:

| Config | Codes reported |
|---|---|
| E1 | `W-DATA-CLUSTER-UNDECLARED`, `W-TEMPLATE-VERSION` (plus two harness artifacts of the reviewer's own scaffold, not of the design: `E-NAME-DIR`, from the config not living under `configs/<name>/`, and a stand-in `template_version`) |
| C1 | the same three codes |
| E1 with `holdout.frac → 0` (**can-fail control**) | the same **plus** `E-DATA-HOLDOUT-FRAC` |

No `E-APPARATUS-*` and no `E-PROBE-UNKNOWN` on either, and none is reachable for any of the nine
configs in this analysis: `generic` — the template every config here validates against, since
`publishable-llm`'s `llm_screen`/`llm_deployment` are a design rather than code — declares no
`apparatus_probe`, so `command_run` never constructs an `Observer` regardless of what this slice
built. **The only direction this slice, or any slice retiring no refusal, can move a config-level
count is down**: once a projection exists, a probe that fails to yield a declared key is a **new**
error a run can hit, not a narrower one.

**What did change, honestly stated rather than left to the pointer at § 3 of this entry's own
predecessor.** A run of `llm_screen` as designed — `apparatus_probe = "llm_deployment"`,
`apparatus_facts` naming five keys including `deployment_revision` — would, if the plugin existed,
now record the five real sub-keys this section documents instead of the unconditional `null` every
prior measurement in this analysis found; and it would newly earn one of five error codes
(`E-APPARATUS-RAISED`, `-RETURN`, `-FACT-TYPE`, `-FACT-MISSING`, `-FACT-CREDENTIAL`) or one warning
(`W-APPARATUS-UNANSWERED`) it could not have earned before this slice. None of that is exercised by
the nine configs measured here, because none declares a probe a real plugin backs — the same
substitution [§ The apparatus probe is the sharpest fit](#the-apparatus-probe-is-the-sharpest-fit-and-it-is-also-the-operational-risk)
already named as a gap this build cannot close.

`uv run pytest` at this commit: 2423 passed, 1 skipped, 2 xfailed; `ruff check`, `ruff format
--check` and `mypy` all clean.

### Measured on 2026-08-20 against commit `600b207` — after H7d Part B

H7d Part B is the half of the apparatus that can end a run: it compares each condition's facts
against that condition's own first *answered* observation, stops the plan on a change
(`E-APPARATUS-CHANGED`), distinguishes a moved apparatus from one that became unreachable, keeps
the record of the period that was certified, and gives `EXIT_EXTERNAL` its first reader. **H7d Part
B unblocks ZERO configs, and both counts stay exactly where H7d Part A left them: six with no
remaining core-side blocker, three executable.** No config in this analysis declares an
`apparatus_probe` a real plugin backs — the declaration is a **template** attribute defaulting to
`None` on `BaseTemplate`, and `generic`, the template every config here substitutes, declares none —
so `command_run` never constructs an `Observer`, and nothing built in Part B is reachable by any of
the nine. Measured by the whole-branch review, transplanting each config's `data`/`statistics`
blocks onto a scaffolded config over a 240-row synthetic roster through `validate_config`, the same
method every entry above uses, re-cited here rather than re-run a third time on the identical
fixture:

| Config | Codes reported |
|---|---|
| E1 | `E-NAME-DIR`, `E-RESOLVER-UNKNOWN` (both harness artifacts of the reviewer's own scaffold: the config not living under `configs/<name>/`, and the plugin not installed) |
| C1 | the same two |
| E1 with `holdout.frac → 0` (**can-fail control**) | the same two **plus** `E-DATA-HOLDOUT-FRAC` |

No `E-APPARATUS-*` code on either, and none is reachable for any of the nine — the same absence
Part A's own entry above measured, unchanged by Part B's gate and stop mechanism because the
precondition (a probe a real plugin backs) still does not hold. Also confirmed still absent:
`E-DATA-RESOLVER-UNSUPPORTED` (retired by H7b Part B) and `E-DATA-WEIGHT-CONTRAST` (retired by
H4b-1) — neither refusal has returned.

**What did change, honestly stated rather than left as a count.** A run whose apparatus moves now
stops instead of publishing a record measured through two different apparatus states, and a stopped
run keeps the record of the period that was certified — `EXIT_EXTERNAL` reads that stop's
precedence over an ordinary `partial`. None of that is exercised by the nine configs measured here,
for the same reason Part A's entry gives: none declares a probe a real plugin backs, the same gap
[§ The apparatus probe is the sharpest fit](#the-apparatus-probe-is-the-sharpest-fit-and-it-is-also-the-operational-risk)
already names.

`uv run pytest` at this commit: 2456 passed, 1 skipped, 2 xfailed; `ruff check`, `ruff format
--check` and `mypy` all clean.

## Cost and execution summary

All figures use the sources' own observed anchors: ≈ $95 per MIPRO-medium compilation, ≈ $14 per 440-patient evaluation, ≈ $10.60 per 330-patient evaluation, at $5.00 per million prompt tokens and $30.00 per million completion tokens. Runtime is serial; the sources note runtime is the least stable estimate.

| Run | Conditions | Repeats | Executions | Compilations | Cost | Serial hours |
|---|---:|---|---:|---:|---:|---:|
| E1 screen-calibration | 4 | 3 × seed | 12 | 4 | $548 | 8.5 |
| E2 screen-primary | 2 | 3 × seed | 6 | 1 | $179 | 2.6 |
| E3 screen-cohort-sensitivity | 5 | 3 × seed | 15 | 0 | $210 | 2.6 |
| E4 screen-reasoning-effort | 5 | 5 × batch | 25 | 0 | $350 | 4.4 |
| E5 screen-repeatability | 1 | 10 × batch | 10 | 0 | $140 | 1.8 |
| E6 screen-transfer | 6 | 3 × seed | 18 | 0 | $252 | 3.2 |
| C1 shortcut-reference-gate | 3 | 5 × batch | 15 | 0 | $53 | 1.0 |
| C2 shortcut-utilization | 9 | 5 × batch | 45 | 0 | $477 | 9.0 |
| C3 shortcut-physiology | 12 | 5 × batch | 60 | 0 | $636 | 12.0 |
| **Total** | | | **206** | **5** | **$2,845** | **45.1** |
| *Same nine runs at one repeat each* | | | *77* | *5* | *$1,180* | *17.5* |

**The headline is the second row, not the first.** All nine runs at `{kind: seed, n: 1}` / `{kind: batch, n: 1}` cost **less** than the source projects' own comparable matrix (≈ $1,276 for the screening protocol's 13 rows alone) while producing confidence intervals, paired contrasts, and pre-registered verdicts that neither source computes. The $2,845 figure is what repeat dispersion costs on top, and `replication.rationale` is where each run records whether it was worth it.

Two roster-variant runs the screening protocol requires — the 32:1 class-ratio robustness row and the disease-cap 500 pair — are **not** in this table because they cannot share a roster with E1-E3. At source cost they add ≈ $444 and ≈ 12 h across three further runs.

Every run is far below `limits.max_executions: 500`, so the binding constraint is money and wall clock rather than plan size. Three things drive the total, and each is a decision rather than an accident:

- **Repeat counts.** The screening runs at `{kind: seed, n: 1}` would cost ≈ $1,180 against the source's own ≈ $1,276 for a comparable matrix — cheaper, and with intervals the source does not compute. The `n: 3` figures above buy `repeat_spread`, and `replication.rationale` is where that trade is recorded.
- **Condition-scoped compilation.** Moving compilation to repeat scope would multiply the five compilations by every repeat and add ≈ $1,900.
- **Five inference passes in the shortcut runs.** Required by the source's own non-determinism rule, and they are `{kind: batch}`, which is what makes the resulting dispersion attributable rather than anonymous.

**As specified**, `publishable dry-run` prints the resolved condition list, the execution count, the **unit-executions** the plan will produce, and the **step directories** and **fixed files** a run would write — not the artifact files inside them, which are `io.write` arguments in step code and are declared nowhere in the config — and it runs the apparatus probe, so every number above is meant to be checkable before any quota is spent. That is a claim about the specification and not about this build; what this build's `dry-run` actually does lives in the dated entries ([§ Executability on this build](#executability-on-this-build)). Every figure in this table was computed by hand. Unit-executions is the one to multiply: at the sources' observed ~6,300 prompt tokens per patient, C3's 12 × 5 × 330 = 19,800 unit-executions is ~125 million prompt tokens, and that arithmetic is the budget check core deliberately leaves to you.

### Correction, appended 2026-08-20 against commit `8d5c046` — "six with no remaining core-side blocker" answers no consistent question

**This corrects a figure carried by the six dated entries above and by `CLAUDE.md`. It does not
retro-edit them:** each recorded what was measured on its date, and the measurements were sound. What was
wrong is the **phrase**, and it was wrong from the moment H4b-1 minted it.

**The contradiction is verbatim in one table cell.** The entry after H4b-1 writes, for each C config,
*"No — blocked on `io.reuse_from` (no remaining core-side blocker either, per H4b-1)"* — while the
E3/E4/E6 rows in the same table read *"No — blocked on `io.reuse_from`"* and are **excluded** from the
six. One dependency, two treatments, one table.

**So the phrase has two readings and six is neither.** If `io.reuse_from` counts as a core-side blocker,
the answer is **three** — E1, E2, E5. If it does not count, because it is a step-level call
`validate` cannot see, then E3, E4 and E6 qualify too and the answer is **nine**. Six is the
count of configs that **validate clean while still needing `io.reuse_from`** (E3, E4, E6, C1, C2, C3),
which is a real and useful number wearing the wrong name — H4b-1 retired `E-DATA-WEIGHT-CONTRAST`, moved
C1–C3 out of the *refused* column, and the phrase followed them without anyone re-asking what it meant.

**The honest figures, measured on 2026-08-20 against `8d5c046`** by transplanting each config's
`data`/`statistics` blocks onto a scaffolded config over a 240-row synthetic roster through
`validate_config` — the method every entry above uses — with `holdout.frac: 0` as a can-fail control
firing `E-DATA-HOLDOUT-FRAC`:

| Figure | Count | What it means |
|---|---|---|
| Transplantable configs | 8 of 9 | E3's section carries no `data`/`statistics` YAML to transplant |
| Validate with zero errors | **8 of 8** | every transplantable config, at this commit |
| No remaining core-side blocker | **3** | E1, E2, E5 — nothing further this analysis can name |
| Need `io.reuse_from` | **6** | E3, E4, E6, C1, C2, C3 — unbuilt, and invisible to `validate` |
| Executable | **3** | E1, E2, E5, and only with the plugin written and installed |

**"No remaining core-side blocker" and "executable" are therefore the same number, 3**, and were always
meant to be — the gap between them was the phrase, not the build. **Use three, and say
`io.reuse_from` by name for the other six** rather than reaching for a figure that has to be
disambiguated every time it is quoted.

**A build fact that needs a footnote to be true is a build fact stated wrongly.** This one survived six
dated entries and roughly a hundred repetitions because each entry copied the phrase forward rather than
re-deriving it — which is the same *carried claim* failure the entries above record in code, appearing
here in a number.

### Correction to the correction, appended 2026-08-20 against commit `30842cb` — "three" is suspect for the same reason "six" was

**The entry above corrected "six" and left "three" standing. H8a's design then measured that three is
wrong the same way.** Recorded immediately rather than at the end of the slice, because a figure left
standing gets built on.

**The `report_by`-under-`resample` gap is live on seven of nine configs — E1, E2, E4, E6, C1, C2, C3 —
while this analysis, `CLAUDE.md` and `H8-SCOPING.md` all charge it to C1–C3 alone.** Measured twice by
computing, not by reading: `summarize_step` over one 12-row table returns `t_over_units`
`[0.3209, 0.7791]` without `resample_columns` and `percentile_over_units` `[0.3583, 0.7500]` with it,
and it moves **both** `prob` and `latency_ms` — so the gap is **per recorded column**, not per headline
metric. All nine configs record through **one** request step whose `io.record` payload is numeric
throughout, which is why it reaches so many. E5 escapes alone (`resample: null`, `report_by: []`).

**So E1 and E2 sit inside today's "three" carrying the identical gap E3, E4 and E6 are excluded for** —
one dependency, two treatments, in one table, which is precisely the fault the entry above named. The
phrase changed; the habit that produced it did not.

**The gap is H4 Statistics', it is live, and it is re-attributed here on measurement** rather than on the
record's own attribution.

**What this analysis can honestly say at this commit**, and it is four measured figures rather than a
phrase:

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Need `io.reuse_from` (unbuilt) | **6** | no — a step-level call |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step` |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**Every figure except the first is invisible to `validate`**, which is the standing reason a clean
`validate` has never been the same claim as *executes*. **Do not quote a single number for this
analysis' executability** — quote the table, or name the dependency.

**And the lesson is about the shape, not the arithmetic.** Both wrong figures were produced the same way:
a slice retired one blocker, moved some configs out of the *refused* column, and **carried the summary
phrase forward without re-deriving what it counted.** That is the *carried claim* failure this file
records repeatedly in code, appearing twice in a number.

### Measured on 2026-08-20 against commit `254aabe` — after H8a

**`io.reuse_from` ships.** `grep -rn "reuse_from" src/publishable/` no longer returns nothing — the
method resolves both locator forms (Decision 1), reads through the registered reader dispatch
`io.write` already inverts, and writes `provenance.upstream` with the upstream's own `code_hash` and
`parameters_hash` beside the names read, verified end to end by real `run`s consuming real upstream
runs (`tests/test_cli.py` fixtures E, F, R, P). That is the whole change this entry may claim by
probe. It may **not** claim that E3, E4 or E6 *executes*, and it mints no fifth number: the
2026-08-20 correction to the correction ruled that a single figure answers no consistent question
for this analysis, and H8a does not reopen that ruling — it moves exactly one row of the table that
ruling produced, and repeats the other three unchanged.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**`io.reuse_from` and the `report_by`-under-`resample` gap are named as separate dependencies on
purpose**, the same separation the correction-to-the-correction table draws: a config can clear one
and still meet the other (E1, E2, E4, E6 all clear the first row and meet the third), so collapsing
them back into one blocked/unblocked column is the exact move that produced "six" and then "three".
No config's row in the table above moves for a second reason: E3, E4 and E6 were never blocked by
`io.reuse_from` not existing in the sense `validate` could see — the dependency was, and remains, a
step body core cannot inspect (§ Greenfield only). What changed is that the step body H8a's own
tests exercise now runs for real; no config here contains that step body, because none of the three
plugins (`growth_screen`, `growth_shortcut`) has been written.

**Two standing qualifications survive H8a untouched, and neither is H8a's to retire.** The
`growth_screen`/`growth_shortcut` plugin still needs to be written and installed before E3, E4 or E6
executes, and a declared apparatus probe still needs a real plugin behind it (H7d's obligation, not
this one's). Every claim in this entry about a *config* is invisible to `validate`: the locator is a
parameter, the read is a step-level call, and the `provenance.upstream` record key is written at run
end — none of the three is a state `validate` ever reaches.

**E3 carries one more obligation, stated so a reader costing it does not discover it at the first
read (this is the plugin's to write; it changes no core-side count).** Under Decision 4, an upstream
step is only addressable at `run` or `summary` scope. `growth_screen`'s own shown pipeline compiles
the program at **`condition`** scope (`step02_compile_program`), and its two summary steps compare
rather than republish. E3, E4 and E6 read their frozen program from **E2**, so E2 needs a `summary`
step that republishes the compiled programs under stable names — the same shape [§ `reuse_from`
addresses an artifact, not the design that produced it](reference.md#reuse_from-addresses-an-artifact-not-the-design-that-produced-it)
already shows in code. Without that step, E2's own `run.yaml` records the compile step under
`execution.conditions`, and a downstream `io.reuse_from` naming it raises `E-UPSTREAM-STEP-SCOPED`
rather than reading anything — a plugin defect, not a core one.

### Measured on 2026-08-21 against commit `cad8940` — after H8b

**`diff` and `freeze` dispatch.** `main(["diff", "/nope/a", "/nope/b"])` reaches real argument handling
(`E-IO-FAILED`, exit `1`), and `cli.NOT_BUILT_COMMANDS` no longer holds either key — both moved out under
their own tasks, verified by running rather than by reading the constant. `run` now writes two more
artifacts, `config.yaml` and `environment/repo_root.txt`, so a run in progress can be re-read without its
`run.yaml`.

**H8b unblocks ZERO configs, and the table below is repeated from the H8a entry unchanged — no row
moves.** `diff` and `freeze` are commands a user runs *around* a run, not dependencies a config needs:
neither runs at `validate`, neither is called from a step, and — checked by running rather than assumed —
`GenericTemplate.apparatus_probe` resolves to `None` and `generic` is the only template any of the nine
configs here validates against, so `freeze` against any of them would report `E-FREEZE-NO-APPARATUS`
before a probe ever ran. Nothing this slice built is a state any of these nine configs reaches.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**No row moves for H8b either, and this entry's own table above is the H8a entry's, character for
character** — repeated rather than restated, because a paraphrase is exactly the failure mode
"carried claim" names elsewhere in this section: the table's own words are what a later reader should
quote, not this entry's gloss on them. **Mint no fifth number here either.** Nothing above changes what H8a's entry already established; this
entry exists to say so on the record rather than to leave H8b's landing unmeasured against this analysis.

**Correction, appended here rather than retro-edited: the 2026-08-15 entry's sentence about these five
commands was already imprecise when written, and is narrower still now.** That entry reads: *"`dry-run`,
`draft`, `resume`, `study`, and `reproduce` each print `unknown command` and exit `2`."* Measured by
running `resume` at this commit: it prints `` `publishable resume` is specified but not built in this
version — see docs/reference.md § Resuming `` and exits `2` — not `unknown command`, which is the
diagnostic a genuinely unrecognized name gets. That distinction is exactly what `_report_not_built`'s own
docstring draws ("a roadmap entry rather than a typo"), so the imprecision was already there on
2026-08-15, unrelated to anything this slice built. Narrower now for two further reasons: `study` was
never one key — `cli.NOT_BUILT_COMMANDS` holds `study add` and `study new` separately, both still
unbuilt — and `diff`/`freeze` have since left the unbuilt set entirely, both this slice's own, so a
sentence naming the current unbuilt CLI surface would read `dry-run`, `draft`, `resume`, `study add`,
`study new`, `report`, `reproduce`, `docs`, `list-templates`, and `demo`. This corrects the sentence; it
does not retro-edit the 2026-08-15 entry's dated claim about what was true that day, which stands as
written.

### Measured on 2026-08-21 against commit `ae71d2a` — after H8c

**`report` and `study` dispatch.** `main(["report", "run.yaml"])` and `main(["study", "new", "path"])`
both reach real argument handling now — `cli.NOT_BUILT_COMMANDS` holds neither `report`, `study new`,
nor `study add` any longer, each moved out under its own task and verified by running rather than by
reading the constant. `BaseReport`, `generate report`, and `study new`/`study add` all ship.

**H8c unblocks ZERO configs, and the table below is repeated from the H8a entry unchanged — no row
moves.** `report` and `study` are commands a user runs *after* a run, or across several, never a
dependency a config needs to validate or execute: neither runs at `validate`, neither is called from a
step, and none of the nine configs in this analysis declares a `study` at all — there is nothing here
for either command to render. Nothing this slice built is a state any of these nine configs reaches.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**No row moves for H8c either, and this entry's own table above is the H8a entry's, character for
character** — repeated rather than restated, for the same reason the H8b entry gives: the table's own
words are what a later reader should quote, not this entry's gloss on them. **Mint no fifth number
here either.** Nothing above changes what H8a's entry already established; this entry exists to say so
on the record rather than to leave H8c's landing unmeasured against this analysis.

### Measured on 2026-08-22 against commit `71f3c6e` — after H5a

**Coercion on the write side, and the reserved-column namespace.** `E-UNITS-ATTR-COLUMN` refuses a
`data.units.attributes` entry named after a reserved column (`unit`, `measurement`, `by`, or any field on
`Unit`); roster attribute values are coerced at `resolve_units`; `io.record`'s plain branch refuses a
`measurement` column; and both row-shaped writers coerce, with per-format capability — `.csv` refuses a
structural or `bytes` cell because it cannot give one back, `.parquet` keeps it because it can. Verified
by running each surface through the installed console script, not by reading the emit sites.

**H5a unblocks ZERO configs, and the table below is repeated from the H8a entry unchanged — no row
moves.** Every check this slice added is a **refusal of a config that is corrupt today**: none of the
eight transplantable configs declares an attribute named after a reserved column, and none records a
non-scalar. So nothing here can move a config out of the *refused* column, and — this is the direction
worth stating — nothing here can move one **into** it either, which for a slice that ships new refusals is
the claim that had to be checked rather than assumed. The eight still validate with zero errors.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**Mint no fifth number here.** The table above is the H8a entry's, character for character, for the third
consecutive entry — repeated rather than restated, because the two corrections earlier in this section
established that every wrong figure this analysis has carried was made the same way: a slice retired or
added one thing, and the summary phrase was **carried forward without re-deriving what it counted**.

**One thing H5a's landing does change about a *future* row, and it is H5b's.** The write side now coerces
and refuses; what a **non-numeric recorded column** does once it flows downstream into `collapse_repeats`,
`summarize_step` and the table a template's `aggregate` receives is **untouched by this slice** — it is
silently dropped, filed in [`spec-defects.md`](superpowers/spec-defects.md), and owned by H5b. That is a
change to what an existing key (`aggregated`) may contain, so when it lands it is the first slice since
H7d Part B with real behaviour-change exposure on a shipped surface — and it is the slice that could move
a row here, in either direction.

### Measured on 2026-08-22 against commit `56aad22` — after H5b

**A non-numeric recorded column now reaches `aggregate`.** `collapse_repeats` carries every recorded
value and admits every unit it was handed; a column earns a metric block when it carries a real number
for at least one unit, computed over those units and reporting **that** contributing count as its own
`n.completed`; a column no unit carries a number for earns none and still reaches the table a template's
`aggregate` receives. Two warnings are new — `W-STATS-REPEATS-DISAGREE` (a recorded column disagreeing
across one unit's repeats) and `W-STATS-COLUMN-THIN` (a contributing count below
`limits.min_reported_n`) — and four things newly stop or newly warn: `E-STEP-KEY-COLLISION` for a derived
key colliding with a **non-numeric** recorded column (re-reported as `W-STATS-AGGREGATE-FAILED`),
`W-STATS-STRATUM-SHADOWED` for a recorded column named `by` whatever it holds, a contained raise from an
`aggregate` that assumes every row carries its numeric column (`W-STATS-AGGREGATE-FAILED`), and
`W-STATS-RESAMPLE-THIN` for a purely numeric derived metric whose draws are now sometimes degenerate.
**The commit pinned above is the branch tip these figures were derived against**; tasks 15 and 16 move no
file under `src/` or `tests/`, so it names the same executable tree as the batch-4 tip that shipped the
behaviour.

**This entry corrects a published figure: row 4's `1`, published by the entry above dated 2026-08-22
against `71f3c6e`.** That entry repeated the H8a table character for character and left row 4 at **1**
while naming, in its own closing paragraph, the very dependency that falsified it — *"what a non-numeric
recorded column does once it flows downstream … is silently dropped … owned by H5b."* A row whose
predicate is *"free of every core-side dependency this analysis can name"* cannot read `1` in the same
entry that names a core-side dependency meeting every config. **So row 4's history is `1 → 0 → 1`**:
`1` as published, `0` as it should have read from H5a's landing until this slice, and `1` again now. The
earlier entry is not edited — this appends and says what it replaces, the same way the two corrections
earlier in this section do.

**Row 4 re-derived, in this entry's own prose rather than carried.** The named dependency is **a
non-numeric recorded column vanishing between the write and `aggregate`**, and it meets **all nine**
configs, not some subset: all nine record through one request step whose `io.record` payload carries
`valid` (a bool), `invalid_reason` and `finish_reason` (strings) beside its numeric columns. It is not a
dependency a config can declare its way out of, which is why it met E5 — the config that was the whole of
row 4's `1` — as squarely as the other eight. **Reached in the analysis' own shown `aggregate`, not only
in principle:** its first statement is `rows = [r for r in units if r.get("valid")]`, and with `valid`
dropped before the table is built that filter selects **nothing**, so `sensitivity` and every other
binary metric returns `None` for a run in which every unit answered. That is read from the `aggregate`
body and the payload this analysis shows, and from the collapse they are handed — **not run**, the plugin
not existing — and it is the whole of what is claimed here: no second consequence is derived for a name
this analysis both records and declares as a unit attribute, a declared attribute reaching the table by
its own route.
**The set arithmetic behind the `1` is unchanged**: E5 is the only config in neither row 2's six
(E3, E4, E6, C1, C2, C3) nor row 3's seven (E1, E2, E4, E6, C1, C2, C3), and this slice closes a
dependency that was in neither row and met all nine.

**This slice's own four new stoppages were checked against the nine before the row was written, and none
of them meets one.** No config records a column named `by` — `grep -c '"by"'` over this file returns
**0**, and every `report_by` target these designs declare (`sex`, `age_band`, `visit_density`,
`count_stratum`, `dx_family`, `record_source`) is a declared **attribute**, so
`W-STATS-STRATUM-SHADOWED` cannot fire. No `aggregate` return key collides with a recorded column: the
returns are drawn from `report.metrics` (`sensitivity`, `specificity`, `ppv`, `invalid_rate`, `auroc`,
`brier`, `cost_usd`) and the recorded payload is `pred`, `prob`, `truth`, `valid`, `invalid_reason`,
`prompt_tokens`, `completion_tokens`, `reasoning_tokens`, `latency_ms`, `attempts`, `finish_reason`. And
the contained-raise case is not met either: the shown `aggregate` reads `r.get("valid")` rather than
indexing, and the shown step has exactly one `io.record` call site, writing a fixed key set — so nothing
in the code this analysis shows indexes a column some rows may lack.

**The `truth` collision is an analysis-side obligation and changes no core-side count.** E5's step
records `"truth": unit.consensus_label` while the E-family declares
`attributes: [truth, sex, age_band, …]`, so `io.record` refuses it with `E-STEP-KEY-COLLISION` — a defect
in this analysis' own shown plugin code, fixable by renaming one key with no change to core. It does
**not** pre-empt the core-side dependency: row 4's predicate names core-side dependencies only, and
letting an analysis-side defect in would answer *would this config as literally written run?* under a
heading that asks about core, pinning the row at `0` until this file is edited. That is the same
treatment the H8a entry gave E3's `summary`-step obligation. **What this pass established and what it
did not:** the payload, the attribute list and the `aggregate` body were **quoted from this analysis**;
**the plugin was never run, because it does not exist** — neither `growth_screen` nor
`publishable-llm` is installable in any build.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**Rows 1, 2 and 3 above are the H8a entry's, character for character, for the fourth consecutive
entry** — copied from the immediately preceding entry and diffed against it rather than retyped, and
**row 3 is not this slice's and is not folded in**: the `report_by`-under-`resample` gap is H4
Statistics', still live on seven configs, and nothing here touches it. **No fifth number is minted.**
Row 4's cell text is repeated unchanged too, which is not a no-op: the figure it publishes is the same
character and a different derivation, and the entry above is where the wrong one was published.

**The two things the corrections earlier in this section require, in this entry's own words.** **Do not
quote a single figure for this analysis' executability** — quote the table. And **name the dependency**:
`io.reuse_from`'s plugin-side call for six, the `report_by`-under-`resample` gap for seven, the
non-numeric column drop for nine before this slice and none after it, and **8 of 8 validating clean,
which is the only figure `validate` can see.** Every wrong figure this analysis has carried was made the
same way — a slice retired or added one thing and the summary phrase was carried forward without
re-deriving what it counted — and row 4's `1` is now the second one made by **repeating a table** rather
than by rewriting a phrase, which is worth recording: character-for-character repetition protects a row
from drift and not from having been wrong when it was written.

### Correction, dated 2026-08-22, against the H5b whole-branch review at commit `14b816e`

**The entry above says "four things newly stop or newly warn." The correct count is five.** Measured by
running one project twice — once against a `main` worktree and once against this branch, same project
commit, same seed — a fifth thing newly fires and appears in neither this entry nor the four-thing
enumeration it repeats: **`W-STATS-CONTRAST-RESAMPLE-THIN`**, at a comparison whose declared `resample`
now draws over a table admitting units it used to drop. It is the contrast-side sibling of item (iv)'s
`W-STATS-RESAMPLE-THIN` — same mechanism, admitting units creates degenerate draws — but at a **different
emit site** (`cli.py:1659`, the contrast arm) from item (iv)'s (`cli.py:3257`), under a **different
existing code** that already carries its own § Warnings row in `reference.md`, which rules the two are
two facts on the same disclosure ground ("neither the `n_paired` denominator nor a thin pool are the same
fact"). This slice's own nine of nine configs still meet no new stoppage: none declares a `statistics.
contrasts` entry with `resample` over a column this analysis' non-numeric drop touches, so **row 4 is
unmoved by this correction** — it corrects the count of newly-firing things, not the executability table.
**No fifth row is minted here either**, matching the earlier correction's own rule: this is a count in
prose, and the table above takes no fifth number.

### Measured on 2026-08-22 against commit `f70499f` — after H6a

**H6a (the two hash definitions) changes what `code_hash` computes and nothing about which of these
nine configs can run.** A file the repo's own committed exclude rules skip stops moving the identity
claim; a run with no file to hash refuses instead of publishing the digest of nothing; two errors
(`E-CODE-EMPTY`, `E-CODE-FILE-LIST`) and one warning (`W-PARAM-UNSET`) are minted; and
`parameters_hash`'s code does not change. **§ Executability does not move, and that was derived rather
than assumed** — the derivation is below, ahead of the table, so a reader can check it rather than
check that the characters match.

**The commit pinned above is this branch's tip at the records task, and it names the same executable
tree the figures below were derived against.** The last commit on this branch to touch `src/` or
`tests/` is `c4dea36` (task 11); `git diff --name-only c4dea36..HEAD -- src tests` is **empty**, so
every commit after it — `f70499f` included — carries the same executable tree, and the measurements
below, run before `f70499f` existed, describe it. Stated rather than left to a reader, on the H5b
entry's own precedent.

**Row 1 counts configs validating with zero *errors*, and `W-PARAM-UNSET` is a warning.** Read at
`validate.py`'s single emit site: it is `c.warn("W-PARAM-UNSET", …)`, not `c.error`. Confirmed by
running rather than by reading — a scaffolded `generic` project with `parameters.analysis.confidence`
deleted prints

```
warning W-PARAM-UNSET        parameters
        carries a default and is left unset here; a step reading it as cfg.parameters.<path>
        raises E-STEP-PARAM-UNKNOWN: analysis.confidence
1 problem (0 errors, 1 warning)
```

at **exit 0**. The error count is what row 1 reads, and a warning cannot move it.

**Neither new error is reachable from `validate` at all.** Both are raised by `command_run`:
`E-CODE-EMPTY` at its single hashing site through a fresh `Collector`, `E-CODE-FILE-LIST` from the one
`git check-ignore` call that site makes. `grep -c "E-CODE-EMPTY\|E-CODE-FILE-LIST"
src/publishable/validate.py` returns **0**; the control, `grep -c "E-PARAM-MISSING"
src/publishable/validate.py`, returns **3**, so the sweep can find a code `validate` does emit.

**Rows 2 and 3 name dependencies this slice does not touch** — `io.reuse_from`'s plugin-side call and
the `report_by`-under-`resample` construction inside `summarize_step`. H6a is `hashes.py`,
`provenance.py`, `cli.command_run`'s hashing phase and `validate._check_parameters`; none of those is
either surface.

**Row 4 counts configs free of every core-side dependency this analysis can name, and `code_hash` is
computed for every run regardless of config.** There is no declaration that opts into it and none that
opts out, so **no config gains or loses a dependency** — which is a different claim from "the hash did
not change", and it is the one row 4 rests on.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |


**Rows 1, 2 and 3 above are the H8a entry's, character for character, for the fifth consecutive
entry**, and row 4's cell text is repeated unchanged too — the whole table was copied out of the
immediately preceding entry with `sed -n` and `diff`-ed against that extraction rather than retyped,
and the diff is empty. This plan's own reproduction of the table in its opening was **not** used: a
second source of truth is how both of this analysis' wrong figures were made. **No fifth number is
minted, and no single figure is quoted for this analysis' executability** — quote the table, or name
the dependency: `io.reuse_from`'s plugin-side call for six, the `report_by`-under-`resample` gap for
seven, and 8 of 8 validating clean, which is the only figure `validate` can see.

**What newly stops and what newly warns, for these nine.** Following H5b's own dated correction —
whose finding was a miscounted *newly-firing* thing rather than a moved row — this is stated in prose
and separately from the table:

- **`E-CODE-EMPTY` and `E-CODE-FILE-LIST` cannot fire for any of them.** Both are properties of a
  **repository** rather than of a config: the first fires when no file survives under `src/**` and
  `templates/**`, the second when git cannot answer whether a candidate path is excluded (a committed
  submodule under a hashed tree being the reachable instance). No config in this analysis names a
  repository at all, and neither code reads any declaration, so no substitution of these configs'
  `data`/`statistics` blocks can reach either.
- **`W-PARAM-UNSET`'s effect on these nine is UNKNOWABLE, with the reason.** It fires on
  `parameter_spec` paths that carry a default and that the config leaves unset — so the answer depends
  entirely on the `growth_screen` and `growth_shortcut` templates' own `parameter_spec`, which no
  measurement can read: **neither `growth_screen` nor `publishable-llm` is installable in any build**,
  which is the same limit every entry in this section since the H7b ones has recorded. Guessing from
  the `parameters` blocks shown above would measure the guess, not the build. What is certain is only
  the shape: if it fires it is a warning, at exit 0, and row 1 is unmoved either way.

**One thing changes for these configs and it is not a row.** Any run of any of these nine made before
this build and any made after would compare as `code_hash DIFFERS` for **identical code**, whenever the
project carried a file under `src/**` or `templates/**` that its own committed exclude rules skip — the
scaffolded `.gitignore`'s `.env` and `.venv/` being the two a real LLM project is most likely to carry.
`schema_version` is deliberately not bumped and no marker is written, so `uv.lock`'s `publishable`
version is the only carrier of *why*. **That is a fact about comparisons across the boundary, not about
executability, and it mints no row.**

### Measured on 2026-08-23 against commit `9b7cc54` — after H6b

**H6b (the environment record and the diagnostic debt) writes three `provenance` keys, documents two
error codes, and changes nothing about which of these nine configs can run.** `provenance.environment`
gains `os`, `hostname` and `hardware`; `E-GIT-NO-REPO` and `E-GIT-NO-COMMIT` gain § Errors core raises
rows; no code is minted and none is retired. **§ Executability does not move, and that was derived
rather than repeated** — the derivation is below, ahead of the table, so a reader checks the reasoning
rather than checking that the characters match.

**The commit pinned above is this branch's tip at this task, and it names the same executable tree the
figures below were derived against.** The last commit on this branch to touch `src/` or `tests/` is
`6497284`; `git diff --name-only 6497284..HEAD -- src tests` is **empty**, so every commit after it —
`9b7cc54` included — carries the same executable tree. Stated rather than left to a reader, on the H6a
and H5b entries' precedent.

**Row 1 counts configs validating with zero *errors*, and H6b emits nothing at `validate` at all.** It
writes three keys inside `cli.command_run`'s `provenance` literal, gives two codes raised by
`provenance.py` their rows, corrects three stale docstrings, and edits documents. **Documenting a code
changes no behaviour**: both codes were undocumented, not unraised, so nothing that did not fire before
fires now. Confirmed by sweep rather than by reading:
`grep -c "E-GIT-NO-REPO\|E-GIT-NO-COMMIT" src/publishable/validate.py` → **1**, and that one hit is a
**catch**, not an emit — `_check_data`'s `if exc.code == "E-GIT-NO-REPO": return`, the line that makes
the in-repo check pass quietly on a config outside every repository. Control:
`grep -c "E-PARAM-MISSING" src/publishable/validate.py` → **3**, so the sweep can find a code
`validate` does report.

**Rows 2 and 3 name dependencies H6b does not touch** — `io.reuse_from`'s plugin-side call, and the
`report_by`-under-`resample` construction inside `summarize_step`. H6b is `cli.command_run`'s
provenance assembly, `secrets.py`'s and `study.py`'s docstrings, and documents; none of those is either
surface.

**Row 4 counts configs free of every core-side dependency this analysis can name, and
`provenance.environment` is written for every run regardless of config.** There is no declaration that
opts into it and none that opts out, **so no config gains or loses a dependency** — which is a
different claim from "the record grew", and it is the one row 4 rests on.

**Neither documented code can fire for any of the nine.** Both are properties of a **repository** — no
git repository walking up from the path given, or a repository with no commit at all — and neither
reads any declaration. No config in this analysis names a repository, so no substitution of these
configs' `data`/`statistics` blocks can reach either.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The whole block above — header, separator and all four rows — is byte-identical to the H6a entry's,
and the ordinal is derived rather than incremented.** Each preceding entry's table was extracted with
`sed -n '<first-line>,+5p'` and diffed against H6a's: the tables at the **H8a, H8b, H8c, H5a, H5b and
H6a** entries are identical to one another, and the *"Correction to the correction"* entry before H8a's
is where they diverge (its rows 2 and 3 read *"Need `io.reuse_from` (unbuilt) | 6"* and a one-clause
`report_by` cell). **So H8a's entry is where this block was established, and this is the sixth entry to
repeat it** — the same counting H6a's own *"fifth consecutive entry"* used, one further on. Row 4 is
inside that count here because the diff covers it: H6a's sentence separated it (*"row 4's cell text is
repeated unchanged too"*) and the measurement gives no reason to. The block includes each cell's own
slice-specific prose, which still names **H8a** rather than this slice, because that is what "character
for character" means and updating it is exactly how a repeated table stops being repeated. The whole block was extracted out of the immediately preceding entry with
`sed -n '1862,1867p'` and `diff`-ed against an independent programmatic extraction of the same entry's
table; **the diff is empty**. This slice's plan and design both reproduce the table in their own
openings and **neither was used**: a second source of truth is how both of this analysis' wrong figures
were made. **No fifth number is minted, and no single figure is quoted for this analysis'
executability** — quote the table, or name the dependency: `io.reuse_from`'s plugin-side call for six,
the `report_by`-under-`resample` gap for seven, and 8 of 8 validating clean, which is the only figure
`validate` can see.

**What newly stops and what newly warns, for these nine: NOTHING.** Stated in prose and separately from
the table, on the H5b correction's precedent, and derived rather than offered as reassurance. H6b mints
no error and no warning — the two codes it documents were already raised, by `provenance.find_repo_root`
and `provenance.git_provenance`, at every commit before this branch — and the sweep above is what stands
behind that: `validate.py` contains one mention of either code and it is a catch. So there is no new
`W-` for this section to reason about, and **the `W-PARAM-UNSET` question is not re-opened here**: the
H6a entry above records it as **unknowable, with the reason**, since it fires on `parameter_spec` paths
carrying a default that the config leaves unset and **neither `growth_screen` nor `publishable-llm` is
installable in any build** — the same limit every entry in this section since the H7b ones has
recorded. Nothing H6b built changes what could be measured there, so the honest form is to leave that
answer standing rather than to guess at it from the `parameters` blocks shown above, which would measure
the guess.

**One thing changes for these configs and it is not a row.** A run of any of these nine made after this
build carries three more `provenance.environment` keys than one made before it, and `study add` redacts
`hostname` while letting `os` and `hardware` travel. `diff` gains **no** sixth row for either, by
ruling — it compares five figures and `uv_lock_hash` is the environment fingerprint among them — so two
runs on different platforms still compare `identical` on all five rows, exactly as they did before.
**That is a fact about what a record carries, not about executability, and it mints no row.**

### Measured on 2026-08-23 against commit `c925416` — after H9a

**H9a (the re-entry seam, `draft` and `dry-run`) splits a shipped command into two helpers, dispatches
two names that printed an unbuilt diagnostic, and changes nothing about which of these nine configs can
run.** **It is explicitly NOT additive** — its design enumerates four behaviour changes, two of them to
a shipped invocation's exit code and output — so this entry does not lean on "a command addition cannot
move a config's executability." It checks all four against these nine, one at a time, below.

**The commit pinned above is this branch's tip at this task, and it is also the last commit on the
branch to touch `src/` or `tests/`** — `git log -1 --format=%h -- src tests` → `c925416` — so the tree
the figures were derived against is the tree the sha names, with no later commits to reconcile. Stated
rather than left to a reader, on the H6a, H5b and H6b entries' precedent.

**Row 1 counts configs validating with zero *errors*, and `validate`'s answer for these nine is
byte-identical.** Measured three ways rather than argued. `git diff --name-only main...HEAD -- src`
prints **two** files, `src/publishable/apparatus.py` and `src/publishable/cli.py` — `validate.py`,
`units.py`, `sweep.py`, `stats.py` and `correction.py` are untouched, so nothing that reports a finding
moved. `apparatus.py`'s whole diff is **three docstring paragraphs and zero statements** (the `PHASES`
docstring, `append_observation`'s, `replay_ledger`'s), each corrected because it would have gone false
under this slice's own change. And `cli.command_validate`'s source segment is **byte-identical between
`main` and this tip** — 261 characters, compared by `ast.get_source_segment` on both sides rather than by
reading the diff's hunk headers, which name it only as the enclosing context of an insertion below it.

**Rows 2 and 3 name dependencies H9a does not touch, and one of them it structurally cannot reach.**
`io.reuse_from`'s plugin-side call is a step-level call; `_prepare_run` carries the `UpstreamLedger`
and `UpstreamResolver` it always did, in the same statement order, and this slice adds no reader of a
run directory at all. The `report_by`-under-`resample` construction is chosen inside
`stats.summarize_step`, reached from the aggregate phase — **phase 8, inside `_execute_prepared`, which
`dry-run` never enters**, and which `draft` enters identically to `run` because `command_draft`
delegates to it. `stats.py` is not in the two-file diff above.

**Row 4 counts configs free of every core-side dependency this analysis can name, and neither new
command adds or removes one.** `draft`'s precondition is a **dirty working tree** — a property of the
operator's checkout, not of a config, and nothing a config can declare or omit. `dry-run`'s probe round
is unexercised for all nine for a reason that is measured rather than assumed: every one validates
against `generic`, and `GenericTemplate.apparatus_probe` **is `None`** (read at this commit, beside
`apparatus_facts == []`), so `_dry_run_probe` returns at its first guard and no probe is dispatched, no
fact is checked, and `W-APPARATUS-UNANSWERED` cannot fire. **Worth naming because it cuts the other
way**: `draft` does give E4 and C3 a route past the dirty-tree obstacle § Three repositories, and what decides the seams records for
them — but that obstacle was never one of the core-side dependencies row 4 counts, so the row does not
move and neither does the count.

**The four enumerated behaviour changes, checked against these nine one at a time.** **(1)**
`publishable dry-run <path>` and `publishable draft <path>` exited `2` with an unbuilt diagnostic on
stderr and now dispatch. That changes what those two commands answer; `run`'s answer for these nine is
what row 1 rests on and it is byte-identical. **(2)** `NOT_BUILT_COMMANDS` loses two keys and
`OPERATION_COMMANDS` gains two, so the shared arity arm answers for six names instead of four — a
message about an *invocation*, printed without reading a config at all. **(3)** `publishable draft new`
now reaches that arity arm rather than the unbuilt diagnostic: same exit code, different line, and again
no config is read. **(4)** The extraction claims to move nothing and the claim was measured, not
asserted — two console scripts from two editable installs, `run.yaml` equal over 147 leaves in order,
the run tree equal over 26 paths, stdout equal over 4 lines, against a normalization list written
before the work. **None of the four reads a `data` or `statistics` block**, which is what a row of this
table is derived from.

**H9a therefore unblocks ZERO configs**, and the reason is structural rather than incidental: both
commands are *second entries into a sequence these configs already reach or do not*. A config that
`validate` refuses is refused identically by `dry-run` (its phase 1 **is** `validate_config`, and the
cost ordering means the refusal arrives before any metered call); a config that validates gains a
cheaper way to *inspect* the plan and a way to run it from a dirty tree, and neither is a core-side
dependency being retired.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The whole block above — header, separator and all four rows — is byte-identical to the H6b entry's,
and no ordinal is asserted.** The block was produced by extracting the immediately preceding entry's
table two independent ways — `sed -n '1946,1951p'` and a programmatic walk that finds the last
`| Figure | Count | Visible to` header and reads forward while the line starts with `|` — and `diff`-ing
the two: **empty**, six lines each. The text pasted here is that extraction, not a retyping, which is
why each cell still carries prose naming **H8a** rather than this slice: that is what "character for
character" means, and updating it is exactly how a repeated table stops being repeated. H9a's plan and
design both reproduce the table in their own openings and **neither was read for it** — a second source
of truth is how both of this analysis' wrong figures were made. **No fifth number is minted, and no
single figure is quoted for this analysis' executability** — quote the table, or name the dependency:
`io.reuse_from`'s plugin-side call for six, the `report_by`-under-`resample` gap for seven, and 8 of 8
validating clean, which is the only figure `validate` can see.

**What newly stops and what newly warns, for these nine: NOTHING.** H9a mints no `E-` and no `W-` code
and retires none. It does make `dry-run` a **new emit surface** for six codes that already existed
(`E-APPARATUS-RAISED`, `-RETURN`, `-FACT-TYPE`, `-FACT-MISSING`, `-FACT-CREDENTIAL`, `E-PROBE-UNKNOWN`,
plus `E-PLUGIN-LOAD`/`-DECORATOR` on a probe's dispatch) and for `W-APPARATUS-UNANSWERED` — every one of
which needs a declared `apparatus_probe` to reach, which none of these nine has. `run`, `draft` and
`dry-run` also all now meet the six dual-surface roster refusals through the shared `cli._prepare_run`;
that widens the § Errors rows (corrected in the same slice) and fires nothing new for a config `run`
already accepted or refused.

**Three claims elsewhere in this analysis went false with this slice and are corrected rather than left
standing**, each in a section that is not a dated entry, and each corrected by **deleting the undated
build claim** rather than by restating it — the pattern rule 10 of the procedure asks for. § Three
repositories, and what decides the seams said `draft` *"does not dispatch in this build"* and that `resume` *"prints the same
specified but not built diagnostic"*; both now say that whether the command dispatches is a build fact
living in these dated entries. § Cost and execution summary said `dry-run` prints *"where every artifact
will land"* — **Ruling R's third home, and a specification claim rather than a build one**, since
`reference.md` no longer promises it: printing the artifact *files* needs the `io.write` names inside
step bodies, which core is documented never to inspect. That paragraph now says step directories and
fixed files, and names what is omitted and why. Its neighbouring *"in which `dry-run` prints specified
but not built"* clause went with it. **The `W-PARAM-UNSET` question is not re-opened here** either:
every entry since the H7b ones records it as unknowable with the reason — neither `growth_screen` nor
`publishable-llm` is installable in any build — and nothing H9a built changes what could be measured.

**Correction, appended here rather than retro-edited (whole-branch fix round, 2026-08-23), replacing
item (3)'s last sentence above:** item (3) said *"`publishable draft new` now reaches that arity arm
rather than the unbuilt diagnostic: same exit code, different line, and again no config is read."*
Measured through the real console script at this commit, on both `draft new` and `dry-run new`: exit
code **2 → 1**, not unchanged; the printed line is `` error   E-IO-FAILED          No such file or
directory``, not the arity message; and a config path **is** read — `_prepare_run` fails trying to open
`new`. `"new"` is a single token, so `rest == ["new"]` never trips `len(rest) != 1` and the call never
reaches the shared arity arm at all; it dispatches straight into `command_draft`/`command_dry_run` and
fails inside `_prepare_run` instead. Task 4's own test docstring at `tests/test_cli.py` (`the call
actually proceeds into command_draft rather than being refused for arity … _prepare_run reports a wrong
(not invocation) failure`) already said this correctly; item (3) did not. This does not change what row
1–4 of the table above count — none of the four disclosed changes reads a `data` or `statistics` block,
and this correction is to the description of change (3), not to its consequence — so **no figure in the
table above moves and no fifth number is minted.**

### Measured on 2026-08-23 against commit `d9b82c6` — after H9b

**H9b builds `resume`.** The command dispatches; it compares the three identity figures and the input
manifest against what the run recorded in a new run-start artifact (`identity.json`), reads
`sweep.yaml`'s plan, `allocation.json`'s memberships and `apparatus/probes.jsonl`'s baseline back
rather than re-deriving any of them, reconstitutes a full result for every triple it skips, may take
over a lock whose holder is provably dead, and refuses fourteen named ways. `run` and `draft` gain one
artifact (`identity.json`), `executions.jsonl`'s line gains two keys (`returned`,
`recorded_columns`), `dry-run` prints one more fixed file, `run.yaml`'s `attempts` becomes a count of
ledger records, and `freeze` gains one refusal (`E-FREEZE-CONFIG-EDITED`).

**It unblocks ZERO configs, and the four rows are derived rather than repeated:**

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** `resume` runs at no
  `validate` and from no step, and every behaviour change above is either a new artifact nothing in
  these configs reads or a path only a crashed run directory reaches, so `validate`'s answer for these
  configs is byte-identical.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. `resume` reads no upstream it does not inherit
  from `run`, through the same `_prepare_run` call.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** A construction chosen inside
  `summarize_step`, in phase 8, which a resumed run reaches through the identical function `run` does
  — and H9b's own reconstitution exists precisely so that phase 8 sees the same results either way.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `resume` requires a
  crashed run directory, which is a property of an operator's history rather than of a config; none of
  the nine declares an `apparatus_probe`, a `study`, a `fold` or a group axis, so none of them can
  reach the apparatus baseline replay, the takeover, or the allocation reader either.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The block above is byte-identical to the H9a entry's, extracted rather than retyped**, by the same
two independent methods that entry describes — a programmatic walk that finds the last
`| Figure | Count | Visible to` header and reads forward while the line starts with `|`, and a fixed
six-line slice from the same index — `diff`-ed to empty, six lines each. That is why its cells still
name **H8a** rather than this slice: updating them is exactly how a repeated table stops being
repeated. **No fifth number is minted, and no single figure is quoted for this analysis'
executability** — quote the table, or name the dependency.

**What newly stops and what newly warns, for these nine: NOTHING.** H9b mints thirteen `E-RESUME-*`
codes plus `E-FREEZE-CONFIG-EDITED` and retires none, and every one of the fourteen is reachable only
from `resume` or `freeze` — neither of which any of these nine invokes, both of which need a run
directory an operator already has. Two codes that existed and were undocumented (`E-RUN-LOCKED`,
`E-RUN-ID-EXHAUSTED`) gain § Errors rows; that is a documentation change and fires nothing. `resume`
also becomes the first reader of exit codes `3`, `4` and `5` and **no exit code is minted**.

**One behaviour change worth naming even though it moves no row**: a resume stopped by an apparatus
fact that moved while the run was down now **writes the run record** — `status: failed`, at exit `4` —
where it previously wrote none, so a run whose executions were already paid for is publishable rather
than stranded. It is reachable only for a config declaring an `apparatus_probe`, which none of these
nine does, which is why the table does not move.

### Correction, dated 2026-08-24, against the H9b whole-branch review at commit `bd2b4de` — the refusal count above wears the wrong noun twice

**The entry above says H9b mints "thirteen `E-RESUME-*` codes plus `E-FREEZE-CONFIG-EDITED`" and calls
their total "the fourteen". Both figures are wrong, and they are wrong in different ways.** Derived from
the emit sites rather than adjusted:

- `grep -rho 'E-RESUME-[A-Z-]*' src/publishable/*.py | sort -u | wc -l` → **14**. Eleven appear as a
  literal `code="E-RESUME-…"`; the other three (`E-RESUME-CODE-MOVED`, `-PARAMS-MOVED`,
  `-LOCKFILE-MOVED`) are raised through a loop variable over a three-tuple list, which is why a grep for
  the literal keyword form under-counts by exactly three and is the likeliest origin of "thirteen".
- `E-FREEZE-CONFIG-EDITED` is new on this branch too (`git show main:src/publishable/freeze.py` holds
  zero occurrences), so the **total minted is 15**.
- Rows: 14 `| ... | E-RESUME-… |` rows plus one for `E-FREEZE-CONFIG-EDITED` in `reference.md`
  § Errors `validate` reports — **15 rows, one per code**, which is what that table's rule requires.

**So: fourteen `E-RESUME-*` codes, fifteen codes minted in total, fifteen rows.** Every figure here
carries its noun on purpose — the failure this corrects is not an arithmetic slip but a count that
answered no consistent question, the shape this section already carries two corrections for.
**The entry's other count sentence is right and must not be "fixed" to match**: *"refuses fourteen named
ways"* is a claim about the `E-RESUME-*` family alone, which is fourteen, and `resume` is the command it
describes — `E-FREEZE-CONFIG-EDITED` is `freeze`'s refusal, reachable from a command `resume` never runs.

**Nothing else in the entry moves.** No row of the four-row table changes, **no fifth number is minted**,
and the *"unblocks ZERO configs"* verdict is untouched: a miscount of how many refusals exist says
nothing about whether any of these nine configs can reach one, and none can — `resume` and `freeze` both
need a run directory an operator already has. The design's own Decision 17 is the origin of both wrong
figures and carries its own appended correction.

### Measured on 2026-08-24 against commit `386aa3f` — after H9c

**H9c builds `reproduce`.** The command dispatches. Given a run record — a run directory's own
`run.yaml` or a bundle member — it clones the recorded remote into a derived directory, checks out
the recorded commit, recomputes `code_hash` with `run`'s own predicate, restores the environment
against the recorded `uv_lock_hash`, writes the config back re-serialized from the record and
self-checked with `parameters_hash`, writes `configs/<name>/apparatus.expected.json` when the run
measured through an apparatus, lists `required_env`, and stops. Given a config it does the same from
step 4 onward, in the repository the config sits in, and names the three things it did not verify.
Twelve `E-REPRODUCE-*` codes are minted plus one `E-APPARATUS-*` — **thirteen codes, thirteen rows**,
each figure carrying its noun. `run` and `draft` gain one comparison, against
`configs/<name>/apparatus.expected.json` when that file exists.

**It unblocks ZERO configs, and the four rows are derived rather than repeated. The derivation is not
the one this slice's design wrote**, and that is stated rather than papered over: design § 7 argued
*"none of the nine configs is a run record, so none of them is an operand `reproduce` accepts."*
**That reason is false at this commit** — Decision 13's config form ships, and all nine of these
configs *are* config files, so all nine are operands `reproduce` accepts. The verdict survives on a
different ground, which is the one below.

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** `reproduce` runs at no
  `validate` and is invoked from no step, so nothing it does can reach `validate`'s answer. The one
  behaviour change to a shipped command — `run`'s first probe round comparing against
  `configs/<name>/apparatus.expected.json` — is read **only when that file exists beside the config**
  and only when the template declares a probe, and no shipped code but `reproduce` writes one. Read
  rather than assumed: `cli.py` builds `expected_path = config_path.parent / "apparatus.expected.json"`
  inside the branch that has already resolved a declared probe, so a config whose template declares
  none never reaches the read at all — which is every one of these nine, since `generic` is the
  template they validate against.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. `reproduce` reads no upstream and walks no
  lineage chain: `grep -n "upstream\|UpstreamLedger\|read_upstream" src/publishable/reproduce.py`
  returns no hits.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** Untouched, and unowned. It is a
  construction chosen inside `summarize_step`, in phase 8 of the run command's own sequence;
  `reproduce` enters no phase of that sequence — `grep -n
  "resolve_contrasts\|_prepare_run\|_execute_prepared" src/publishable/reproduce.py` returns no hits
  either — and it renders no intervals at all.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `reproduce` requires a
  record with a remote, or a config plus the repository it sits in and a lockfile that resolves.
  Neither is a property of a config's declarations, and **accepting a config as an operand is not a
  config executing** — `reproduce` prepares an environment and stops, executing no step and reporting
  no result. So it can add no dependency to this row and remove none.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The block above is byte-identical to the H9b entry's, extracted rather than retyped**, by the same
two independent methods the H8a and H9a entries describe — a programmatic walk that finds the last
`| Figure | Count | Visible to` header and reads forward while the line starts with `|`, and a fixed
six-line slice from the same index — `diff`-ed to empty, six lines each. Its cells still name **H8a**,
because updating them is exactly how a repeated table stops being repeated. **No fifth number is
minted, and no single figure is quoted for this analysis' executability** — quote the table, or name
the dependency.

**What newly stops and what newly warns, for these nine: NOTHING.** Thirteen codes are minted and none
is retired. Twelve are `E-REPRODUCE-*`, reachable only from a command none of these nine invokes. The
thirteenth, `E-APPARATUS-UNEXPECTED`, is reachable only from a `run` whose config directory holds a
file only `reproduce` writes **and** whose template declares an `apparatus_probe` — none of these nine
declares one. No exit code is minted: `5` gains readers for its *"a clone or `uv sync` that failed"*
clause, which is `EXIT_EXTERNAL` acquiring readers exactly as H7d Part B and H9b did, and
`E-APPARATUS-UNEXPECTED`'s `1`-versus-`4` split is `run_status`'s shipped fold rather than a choice.

**Two behaviour changes worth naming even though they move no row.** `publishable reproduce <path>`
stops printing *"specified but not built"* at exit `2` and starts dispatching; `publishable reproduce
new` now prints `E-IO-FAILED` at exit **`1`** — **exit `2` → `1`, and the identifier is new** —
measured through the real console script rather than predicted. And a `run` or `resume` whose apparatus
contradicts an expectation file **keeps its record**: a resume whose run-start round contradicts it,
with a prior attempt's executions already on disk, exits `4` with a `run.yaml` rather than `1` with
none. Both are reachable only outside these nine, which is why the table does not move.

### Measured on 2026-08-25 against commit `ebe58ca` — after H9d

**H9d builds `demo`, `docs` and `list-templates` — the last three commands the CLI reference marked
`NOT BUILT`, and with them the whole command surface.** `demo` writes 240 synthetic units outside
the repository it creates, scaffolds a project-local template, three steps and a config, commits so
the tree is clean, and then walks the six stops: it prints each command exactly as you would type
it, runs it in-process, and says what its output meant, ending by printing — not running — the
`reproduce` invocation. `docs` rewrites every managed README region a repository declares and names
the ones it did not find, refusing five shapes by their own codes. `list-templates` prints every
claim the registry answers, with a parameter spec wherever a class exists, and without importing an
installed package. `NOT_BUILT_COMMANDS` is empty and every `Status` cell in all three tables reads
`built`.

**It retires no refusal and unblocks ZERO configs, and the four rows are derived rather than
repeated.** Derived per row:

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** None of the three commands
  runs at `validate` or is invoked from a step: `grep -n "validate_config" src/publishable/docs.py
  src/publishable/demo.py` returns no hits, and `demo` calls `validate` only as a stop of its own
  walk, over a config it wrote itself. The one behaviour change to a shipped command is what
  `publishable new` writes into a **README** — two regions added and one section moved inside its
  region — which no `validate` check reads; the scaffold constants moving into `readme_templates/`
  as files changes where bytes are read from and not what they are, pinned byte-for-byte by a
  whole-tree hash of a scaffolded project. The fresh-source loader changes a **loader**, not a
  resolution: the class `validate` gets for a given file is the same class, freshly compiled.
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. None of the three reads an upstream or walks
  a lineage chain: `grep -n "reuse_from\|read_upstream" src/publishable/demo.py
  src/publishable/docs.py` returns no hits.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** Untouched, and still unowned. It is a
  construction inside `summarize_step`; no command this slice builds enters that phase, and `demo`'s
  own config declares no `report_by` at all.
- **Row 4, free of every core-side dependency this analysis can name — 1.** `demo` scaffolds its own
  project and its own data and accepts no config of anyone else's; `docs` and `list-templates` read
  no config at all. So none can add a dependency to this row or remove one.

None of the nine declares a `study`, a `fold`, a group axis or an `apparatus_probe`, and every one
validates against `generic` — so the project-local template `demo` writes is reachable from none of
them either.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The block above is byte-identical to the H9c entry's, extracted rather than retyped**, by the same
two independent methods the H8a, H9a, H9b and H9c entries describe — a programmatic walk that finds
the last `| Figure | Count | Visible to` header and reads forward while the line starts with `|`, and
a fixed six-line slice from the same index — `diff`-ed to empty, six lines each. Its cells still name
**H8a**, because updating them is exactly how a repeated table stops being repeated. **No fifth
number is minted, and no single figure is quoted for this analysis' executability** — quote the
table, or name the dependency.

**What newly stops and what newly warns, for these nine: NOTHING.** Five `E-DOCS-*` codes are minted
and all five are reachable only from `docs`, a command none of these nine invokes and which reads no
config. No exit code is minted. Three exit codes **move**, each from the specified-but-unbuilt
diagnostic to real behaviour — `publishable demo`, `publishable docs` and `publishable list-templates`
stop printing *"specified but not built"* at exit `2` — and all three are reachable only outside
these nine, which is why the table does not move.

### Measured on 2026-08-25 against commit `7ef6846` — after H3c-3

**H3c-3 draws a `fold` level's partitions and a `data.units.holdout` split *inside each cell* of a
`sweep.groups` × `allocation: between` design, retiring `E-REPL-FOLD-CELLS` and
`E-DATA-HOLDOUT-CELLS`, and decides `limits.min_units_per_cell` as a warning,
`W-DATA-CELL-THIN`.** It is the last slice in the project; nothing is chartered after it.

**It retires two refusals, mints one warning, and unblocks ZERO configs, and the four rows are
derived rather than repeated.** Derived per row:

- **Row 1, transplantable configs validating with zero errors — 8 of 8.** Unchanged, and **neither
  retirement is reachable**: `grep -n "groups:" docs/feasibility-llm-growth-studies.md` → two hits in
  config blocks, **both `groups: []`**; `grep -n "allocation:"` → two config hits, **both
  `allocation: within`**, the third being a prose sentence. `grep -n "kind: fold"` returns **nothing**
  — no config here declares a `fold` level at all — and the one `holdout:` block sits beside that same
  `allocation: within` and `groups: []`. Both retired codes needed a **cell structure**, which is a
  non-empty `sweep.groups`, so no config here could reach either of them before or after.
  `E-REPL-FOLD-K-TOO-LARGE`'s and `E-DATA-HOLDOUT-EMPTY`'s widened bounds are widened **only when
  cells resolve**, and none do. **The new warning cannot move this row in either direction**: it is
  gated on a cell structure none of the nine has, and the row counts **errors** — a warning never
  changes an exit code. (`min_units_per_cell: 20` appears in three of the config blocks, which is
  exactly the shape C16's gate exists for: without the gate every one of them would have warned.)
- **Row 2, blocked on `io.reuse_from` — 0.** Untouched. This slice reads no upstream and walks no
  lineage: it touches `units.py`, `replication.py`, `validate.py`, `cli.py`, `runner.py`, `sweep.py`
  and `artifacts.py`, and `grep -rn "reuse_from\|read_upstream"` over this branch's diff returns
  nothing. The row's parenthetical is unchanged: six configs still need the plugin body to call it.
- **Row 3, meet the `report_by`-under-`resample` gap — 7.** Untouched, **and now permanently
  unowned.** It is a construction inside `stats.summarize_step`; nothing here enters that phase.
  `docs/superpowers/spec-defects.md`'s `RE-OWNED 2026-08-25` entry states its owner as `unassigned`
  with *no slice follows* as a **fact rather than a deferral**, which is the only thing about this row
  that H3c-3 changes and it is a change to the record, not to the count.
- **Row 4, free of every core-side dependency this analysis can name — 1.** Unchanged: E5, and only
  with the plugin written and installed. Nothing this slice built is a dependency any of the nine can
  acquire or shed, since all of them are one roster under one within-subjects allocation.

None of the nine declares a group axis, a `fold` level, a `cluster_by`, a `study` or an
`apparatus_probe`, so the cell decomposition this slice threads through `validate` and `run` resolves
to `None` for every one of them and every cell-aware check takes the roster-wide branch it took
before.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method now ships, so this row's *parenthetical* ("unbuilt") is what went false, not the dependency: six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` gap | **7** | no — a construction chosen inside `summarize_step`; **H8a touches none of this** — it is H4 Statistics' gap, live on E1, E2, E4, E6, C1, C2, C3, and unmoved by anything this slice built |
| Free of every core-side dependency this analysis can name | **1** | no — E5, and only with the plugin written and installed |

**The block above is byte-identical to the H9d entry's, extracted rather than retyped**, by the same
two independent methods the H8a, H9a, H9b, H9c and H9d entries describe — a programmatic walk that
finds the last `| Figure | Count | Visible to` header and reads forward while the line starts with
`|`, and a fixed six-line slice from the same index — compared and found equal, six lines each. Its
cells still name **H8a**, because updating them is exactly how a repeated table stops being repeated.
**No fifth number is minted, and no single figure is quoted for this analysis' executability** —
quote the table, or name the dependency. **And this is the last entry this section will ever gain**,
so a reader arriving later should read the table as final rather than as current.

**What newly stops and what newly warns, for these nine: NOTHING.** Two `E-` codes are **retired**
(`E-REPL-FOLD-CELLS`, `E-DATA-HOLDOUT-CELLS`) and neither was reachable from any of them; one `W-`
code is **minted** (`W-DATA-CELL-THIN`) and its gate excludes all nine. No exit code is minted and
none moves. The only behaviour change reachable from a config without a group axis is the one that
is not a change at all: `units.partition_within_cells` reduces to the byte-identical whole-roster
`partition_units` call it made before, which is what guard-pin arms A, B, D and E exist to hold.

#### Correction appended 2026-08-25 — one grep in the entry above is falsified by its own sentence

**This is a correction to the H3c-3 entry's row 1, not a new entry**, and it mints **no fifth
number**: the four-row table is untouched and still the thing to quote.

That row writes *"`grep -n "kind: fold"` returns **nothing** — no config here declares a `fold` level
at all."* Run against this file it returns a line, and that line is the sentence making the claim —
the self-matching-sweep shape `CLAUDE.md` § Mechanical traps names, met here by a sweep written
inside the file it sweeps. **The unscoped count is not a figure worth quoting at all**, since this
correction itself moves it: naming the searched string is enough to change the answer, which is why
the rule is to filter the file list rather than the output.

**The substance is unchanged and now stated reproducibly.** Scoped to what the claim is about — the
fenced blocks, which is where every config in this analysis lives — the string appears **zero**
times inside a fence; every hit is prose. So no config here declares a `fold` level, both retired
codes stay unreachable for want of a cell structure, and row 1 stands at **8 of 8** exactly as
derived.

The two greps beside it were already scoped and are unaffected: *"two hits in config blocks, both
`groups: []`"* and *"two config hits, both `allocation: within`"* each count config blocks rather
than lines, so neither is falsified by its own sentence.

### Correction, appended 2026-08-26 against commit `541f24c` — row 3 names a documented limitation, not a gap

**Row 3 of the four-row table is correct as a count and was described with the wrong word throughout this
section.** Every entry that repeats the table calls it *"the `report_by`-under-`resample` **gap**"*, and
twenty-eight sentences here carry that phrasing. **The count stays** — seven of the nine configs (E1, E2,
E4, E6, C1, C2, C3) declare both a non-empty `report_by` and a non-null `resample`, and that is a true and
useful figure. **What changes is its character**, and the change is not this analysis' to make: it is
`reference.md`'s, which already made it.

**§ Statistical reporting addresses it in those words**: *"A `statistics.report_by` level's recorded-column
interval is a `t_over_units` one even under a declared `resample`, and that is a documented limitation
rather than a gap awaiting a slice."* Measured against the code on 2026-08-26, **both grounds that
paragraph rests on hold**:

- **It is self-disclosing.** A level's column block carries **no `resample_draws` key at all** when
  `resample_columns` is false, and `stats.py` states the absence is deliberate — *"a `null` there would
  claim otherwise"*. So a record declaring both constructions **shows which one produced which number**
  rather than presenting them as one design.
- **It cannot reach a verdict.** A `report_by` level **joins no correction family**, which is a `CLAUDE.md`
  § Invariants rule. A level is a *description*; the comparison is a contrast. So the asymmetry never
  touches an interval a hypothesis rests on.

**Why this matters for a reader of this analysis specifically.** The dated entries above are correct that
seven configs meet it and correct that core chooses the construction inside `summarize_step`. But a reader
arriving at *"gap"* concludes the tool has a defect these experiments would hit, and **the honest statement
is narrower**: a run declaring both gets a stratified percentile interval for the condition and an
unstratified *t* interval for each of its levels, **in one record, distinguishable, and outside every
correction family**. That is a stated limit of the design, not a wrong number.

**Nothing above is retro-edited**, on this section's own convention — the entries are dated measurements and
say what was measured when. **The four-row table is untouched and no fifth number is minted.** This
correction changes one word's worth of meaning and leaves every figure where it was.

### Measured on 2026-08-27 against commit `dc03ec4` — a fresh full re-measurement, with the plugin installed for the first time

**The H3c-3 entry says this section will never gain another entry, and that sentence was about
slices.** Nothing is chartered after H3c-3 and nothing has been; what follows is not a slice entry
but a **re-measurement at a later commit**, run because 83 commits have landed on `main` since the
one that sentence was written against and because the plugin this analysis proposes turns out to
**exist on disk**. The H3c-3 text is left exactly as it stands, on this section's own convention:
its measurement was sound on its date, and a later measurement is appended rather than folded back
into it.

**What moved in `src/` since `7ef6846`.** 16 files, +602/−51 — the release work, the plugin
tutorial's six fix slices (W1–W5), and a whole-project review round. Four of the five modules every
figure in the table below depends on are **byte-identical** at both commits, by `md5`:
`validate.py` (`da7b805016671939ae9b67f53d97d5e3`), `stats.py`, `runner.py` and `units.py`. Exactly
**one diagnostic code is minted** in that window — `E-CONFIG-IMMUTABLE`, 136 codes in total, by a
`git grep` of `code="..."` at each commit differenced against the other — and it is raised by
`Node.__setattr__`/`__delattr__`, so it is a step-time contract error that no config declaration can
reach.

**Both source repositories were re-read for movement, and neither has moved.** `2026-07-01-screening`'s
last commit is `ce76f9d` (2026-07-24) and `2026-08-03-shorcut`'s is `d20efe4` (2026-08-05), both earlier
than this analysis; `git log --since=2026-08-08` returns nothing in either. The screening abstract still
states the 440-patient paired held-out set the cost table is built on. So steps 1 through 8 of the
[feasibility procedure](../CLAUDE.md) — the goals, the hand-rolled inventory, the nine designs, their
arithmetic, and every refusal's route — rest on unchanged sources and are **not** re-derived here. What
is fresh is the build measurement and the plugin.

#### The narrowings this measurement declares

The same three the 2026-08-16 entry declared, plus two new ones, each named rather than left implicit:

- **The fixture is a `publishable demo` project**, scaffolded by the command H9d built, with a
  240-row synthetic `index.csv` outside it carrying every column the nine configs name. Each
  config's `data.units` and `statistics` blocks were transplanted verbatim onto that project's
  generated config; `parameters`, `sweep`, `replication` and `hypotheses` were **not** carried over,
  because the scaffold's entrypoint declares neither the real parameter names nor the
  `step03_screen`/`step05_agreement` steps the real hypotheses name.
- **E3 carries no `data`/`statistics` YAML of its own**, so eight configs are transplantable, which
  is where row 1's denominator comes from.
- **C2 declares two contrasts and C3 declares four; one stand-in of each was run**, over the
  scaffold's own axis. That changes the comparison count a message would print and nothing about
  whether a code fires.
- **New: the plugin was installed** — `publishable-llm-screening 0.1.0`, at `d47340d`
  (2026-08-08) — into a scratch venv beside `publishable 0.1.3` built from this commit. It registers
  `llm_screening`, `llm_prompt_opt` and `shortcut_probe` as `publishable.templates` entry points, a
  `dspy_examples` resolver, and an `llm_deployment` probe. It is **not** the `publishable-llm` this
  analysis proposes and its names differ; where a claim below turns on the name, the substitution is
  printed with it.
- **New: one `.pth` shim.** The plugin does not import against shipped core at all without it; what
  the shim is and what it buys is measured below rather than assumed.

#### Row 1, measured by running: 8 of 8

Every one of the eight transplantable configs validates with **zero errors** under the table
substitution — the print is `✓ config valid` for each. Two warnings appear and both are fixture
properties rather than design properties: `W-DATA-CLUSTER-UNDECLARED` on `age_band` for all eight
(the synthetic table's four-band shape), and `W-STATS-FAMILY` on E5 alone, which is an artifact of
the substitution itself — E5 declares `correction: none` and **no `sweep` block**, and the scaffold's
own two-comparison sweep is what makes a family for the correction to be absent from.

As declared — `from: {resolver: patient_trajectory}`, the name the analysis uses — all eight earn
`E-RESOLVER-UNKNOWN`, whose message reads *"names `patient_trajectory`, which no installed
distribution registers in the `publishable.resolvers` entry-point group (registered: none
installed)"*. That is the plugin-not-installed answer, not a refusal of the declaration:
`E-DATA-RESOLVER-UNSUPPORTED` stays retired, as H7b Part B left it.

**Two discriminating mutations, both run, both quoted from what the command printed.** Setting
`holdout.frac: 0` on E1's otherwise-clean block produces `E-DATA-HOLDOUT-FRAC` — *"is 0, and a test
fraction is strictly between 0 and 1"* — and restoring the field returns the file byte-for-byte
(`diff` empty) and the result to one warning, zero errors. Setting C2's `weight_by` to a column the
roster does not carry produces `E-DATA-WEIGHT-UNKNOWN`, and reverting restores the clean result. A
block that could not fail either way would not be a measurement.

#### Rows 2 and 3 are untouched, and the derivation is the byte-identity above

Row 2 is a step-level call: `io.reuse_from` ships (`artifacts.py:1192`) and six configs still need
the plugin body to call it. Row 3 is a construction inside `stats.summarize_step`, and `stats.py` is
byte-identical at both commits, so nothing in this window could move it. Its **character** is the
one the 2026-08-26 correction settled: a `report_by` level's recorded-column interval stays a
`t_over_units` one under a declared `resample`, which `reference.md` states as a **documented
limitation** — self-disclosing, and outside every correction family — not a gap. The count of seven
stands; the noun does not.

#### Row 4 is falsified by this measurement, and it is re-derived rather than extracted

Row 4 reads *"free of every core-side dependency this analysis can name — 1 — E5, and only with the
plugin written and installed."* **The plugin is now written and installed, and under that row's own
condition the count is zero.** The byte-identical extraction the last five entries performed was
never a rule to preserve a figure the derivation contradicts — it held because the derivation kept
landing on the same numbers, and here it does not.

**The dependency has a name: `E-TEMPLATE-INSTALLED-UNSUPPORTED`.** A config whose `experiment_type`
names a template an installed distribution registers is refused, in full:

```
error   E-TEMPLATE-INSTALLED-UNSUPPORTED experiment_type
        names `llm_screening`, which publishable-llm-screening 0.1.0 registers as a
        `publishable.templates` entry point — but core resolves an installed template's name
        without importing its package, and loading one is not implemented in this build;
        installed templates will be honored in a later slice. Use a project-local `templates/`
        file or a core template for now
```

`publishable list-templates` says the same thing from the other side: all three of the plugin's
templates are listed as installed, each with *"its parameter spec is **not readable in this
build**."*

**The link to all nine is an inference, and it is printed rather than asserted as a measurement.**
What was run names `llm_screening`, the installed plugin's own template. The nine configs name
`llm_screen`, and [§ Package](#package) registers it in
`[project.entry-points."publishable.templates"]` — an entry-point template, which is exactly the
shape this build refuses. So: every one of the nine, written as this analysis writes them, is
refused by core today for a reason no dated entry above has ever named, and E5 — the config row 4
counts — is refused with the rest.

**This is not a regression and nothing about it is new.** The code is present at `7ef6846` too; it
is in both code sets the diff above compares. What is new is that this analysis can **name** it,
because a plugin registering these artifacts now exists to install. Every entry above took the
stance *"the plugin assumed to exist, and only core declarations judged"* — and that assumption
assumed away the one core-side blocker that survives the plugin being written.

| Figure | Count | Visible to `validate`? |
|---|---|---|
| Transplantable configs validating with zero errors | **8 of 8** | yes — the only figure `validate` can see, and measured by running at this commit |
| Blocked on `io.reuse_from` | **0** | no — a step-level call; the method ships, and six configs (E3, E4, E6, C1, C2, C3) still need the plugin body to *call* it |
| Meet the `report_by`-under-`resample` **documented limitation** | **7** | no — a construction chosen inside `summarize_step`; live on E1, E2, E4, E6, C1, C2, C3, and `stats.py` is byte-identical to H3c-3's commit |
| Free of every core-side dependency this analysis can name | **0** | no — **re-derived, not extracted**: a plugin template is `E-TEMPLATE-INSTALLED-UNSUPPORTED`, which E5 earns with the other eight |

**No fifth number is minted, and no single figure is quoted for this analysis' executability** —
quote the table, or name the dependency. Rows 1, 2 and 3 are the H8a block's, re-derived and
unchanged; row 4's count moved, and the dependency is the thing to say out loud.

#### How far the written plugin gets against shipped core, measured

The plugin was built against the specification at `55ddaea`/`277388c` with a `stubs/publishable`
standing in for a core that had not shipped. Core has shipped. What happens when the two meet is
the sharpest evidence this analysis has ever had, and it is a sequence of four contract mismatches,
each measured:

1. **It does not import.** Resolving `{resolver: dspy_examples}` reports `E-PLUGIN-LOAD`: *"the
   entry point `dspy_examples` … raised while importing and registers nothing usable:
   ImportError(\"cannot import name 'UnitTable' from 'publishable'\")"*. Core's own
   `BaseTemplate.aggregate` is annotated with `UnitTable`, the class lives in `publishable.stats`,
   and `publishable.__all__` does not carry it — so a plugin annotating the same signature must
   invent the name, and the invented name is the import that fails. This is [gap 4](#gaps-this-analysis-found-in-the-specification).
2. **Its resolver reads the input as text.** With a one-line `.pth` shim binding
   `publishable.UnitTable` to `publishable.stats.UnitTable` — the substitution declared above, and
   everything from here down sits behind it — resolution reaches the plugin's own code and raises
   `E-RESOLVER-RAISED`: *"AttributeError: 'list' object has no attribute 'splitlines'"*. The plugin
   calls `io.read_input(...).splitlines()` and parses each line itself; core's reader dispatches on
   the suffix, and `reference.md` § Steps and artifacts says `.jsonl` comes back as **rows as
   mappings**. That is a plugin misreading a documented rule, not a gap — worth recording because
   the rule is evidently easy to misread from the resolver's side, where the file is a benchmark
   serialization rather than a table.
3. **Its resolver yields four attributes, and the designs declare seven.** Pointed at a suffix core
   does not parse, resolution runs and reports `E-UNITS-ATTR-MISSING` on `age_band`: *"a resolver
   has no columns beyond the attributes it yields."* `dspy_jsonl._attributes` yields `truth`, and
   `sex`/`split`/`n_visits` where present — so `visit_density`, `span_days`, `dx_family`,
   `record_source` and `age_band`, which E1 through E6 declare and `report_by` reads, are not
   available from the plugin as written. The analysis and the implementation were written from the
   same protocol and disagree about the roster's columns; running them together is what surfaced it.
4. **Narrowed to what it yields, an E1-shaped config validates clean.** `attributes: [truth, sex]`,
   `report_by: [sex]`, the rest of E1's design intact — grid over
   `objective.false_negative_credit: [0.10, 0.25, 0.50, 0.75]`, `{kind: seed, n: 3}`, a 0.2
   `holdout` stratified on `truth`, `resample: {method: bootstrap, n: 2000, stratify_by: [truth]}` —
   against a **project-local** template carrying the parameters, with the plugin supplying the
   resolver. The print is `✓ config valid`. **That is the route: keep the template project-local,
   ship the machinery in the plugin**, which is what `docs/tutorial-writing-a-plugin.md` prescribes
   for exactly this refusal. It is the first time in this section's history that a plugin-supplied
   artifact has resolved a roster on a shipped build.

**And the probe fires where the specification says it does.** With `apparatus_probe =
"llm_deployment"` declared on that local template, `validate` prints `✓ config valid` and runs
nothing, while `dry-run` reports `E-APPARATUS-RAISED` — *"probe `llm_deployment` raised
ModuleNotFoundError"*, the plugin's provider module being deliberately absent. Probe **dispatch**
is built and sited exactly as [§ The apparatus probe](#the-apparatus-probe-is-the-sharpest-fit-and-it-is-also-the-operational-risk)
describes: at `dry-run`, never at `validate`. That paragraph's *"none of that can be exercised yet"*
is what this falsifies, and the body sentence is corrected rather than left standing.

**The plan E1's shape resolves to, printed.** With the probe removed, `dry-run` prints
`sweep: 4 conditions (grid) × 3 repeats = 12 executions` and
`scale:  576 unit-executions (12 executions × 48 units handed to each)` — the 4 × 3 structure
[§ E1](#e1--metric-calibration) states, over the 48-unit test partition of a 240-row stand-in
roster. The real design's held-out set is 88 of 440; the structure is the thing this confirms, not
the size.

#### The metered figure does not count what a compile step does

`dry-run`'s `unit-executions` counts `len(io.units)` per planned execution, and under a declared
`holdout` **every** scope is handed the test partition. Measured on the fixture, by a condition-scope
step returning both numbers, from `executions.jsonl`:

```
{"step": "step02_fit_model", "scope": "condition", ..., "returned": {"n_units": 48, "n_train": 192}}
```

and the same run's `dry-run` printed `scale:  912 unit-executions (19 executions × 48 units handed
to each)`. So a condition-scoped step working over `io.units.train` does 192 unit-passes and
contributes 48 to the figure. **E1 and E2's MIPRO compilation is exactly that step** — $380 of E1's
$548 by [§ Cost and execution summary](#cost-and-execution-summary)'s own anchors — so the line a
reader is told to check before spending is silent about the expensive half of these two designs.
This is [gap 5](#gaps-this-analysis-found-in-the-specification), and it is a gap in the
proportionality claim rather than in the arithmetic: the printed number is faithful to its stated
definition.

#### What newly stops and what newly warns, for these nine

**Nothing, from the code.** One code is minted in this window (`E-CONFIG-IMMUTABLE`) and no config
declaration reaches it; no code is retired; no exit code moves. What changes is what this analysis
**knows**, and that came from installing a plugin rather than from a slice: row 4 is zero, and the
dependency is `E-TEMPLATE-INSTALLED-UNSUPPORTED`.

**One shipped sentence is stale and is filed rather than patched here.** That refusal's message ends
*"installed templates will be honored in a later slice"*, and `CLAUDE.md` states there is no later
slice — the charter is complete. Grepped at this commit, the promise has exactly two homes: the message
in `validate.py`, and the plugin tutorial's transcript quoting it, where it is a dated record of what
the command printed rather than a claim of its own. `reference.md` says only *not readable in this
build* and promises nothing. The document changes first, so this is recorded in
`docs/superpowers/spec-defects.md` and left for a reader to decide, not edited into `validate.py` from
here.

Full local gates at this commit, run rather than assumed: `3485 passed, 1 skipped, 2 xfailed in
418.90s`, `ruff check .` *All checks passed!*, `mypy` *no issues found in 56 source files*. Nothing this
measurement did touches them — every run above happened in a scratch project outside this repository —
and they are recorded so a reader can tell a docs-only change from one that moved code.

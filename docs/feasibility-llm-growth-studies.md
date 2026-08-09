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
- [Screening: six runs](#screening-six-runs)
- [Shortcut: three runs](#shortcut-three-runs)
- [What is not an experiment](#what-is-not-an-experiment)
- [What core refuses, and the route for each](#what-core-refuses-and-the-route-for-each)
- [Proposed plugin: `publishable-llm`](#proposed-plugin-publishable-llm)
- [Gaps this analysis found in the specification](#gaps-this-analysis-found-in-the-specification)
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

## Screening: six runs

### Shared roster and pipeline

Every screening config below resolves the same roster through a plugin resolver, and runs the same four steps:

```
src/growth_screen/steps/
├── step01_serialize.py        scope: run         # censoring + trajectory serialization
├── step02_compile_program.py  scope: condition   # MIPROv2 over io.units.train; no-op when optimizer.name == none
├── step03_screen.py           scope: repeat      # one request per unit; nondeterministic = True
└── step04_compare.py          scope: summary
```

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

**Design.** One condition, ten batches. Agreement across repeats is not something core computes: core averages repeats per unit before any interval. The agreement bound is therefore a `scope: "summary"` step reading each repeat's per-unit table through `io.read_condition(condition, step, name, repeat=r)` and returning an [`Estimate`](reference.md#estimate-carries-your-interval-without-core-claiming-it). The hypothesis names it and takes no `compare`.

```yaml
# configs/screen-repeatability/config.yaml
metadata:
  name: screen-repeatability
  description: "Within-block safe agreement of the frozen binary screen across fresh executions"

sweep:
  baseline: null
  groups: []
  paired: []
  ablate: null
  sample: null
  grid: {}
  # 1 condition

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

**A blocking constraint.** The apparatus probe is permitted — and here required — to read a parameter the sweep varies, so each deployment is gated against its own first observation. But `required_env` is a **class** attribute, static across the run, and a sweep spanning providers has provider-dependent credentials. The Ollama cell the source evaluates cannot join this config unless a single gateway serves every level. Split it into a per-provider run and join the runs in a `study`, or route everything through one endpoint.

---

## Shortcut: three runs

The shortcut project's roster is the 450-patient benchmark, resolved with the sampling weight the source retains for population-weighted estimates and the pre-existing development/confirmation partition:

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
| Class-ratio (10:1 versus 32:1) as a design axis | The roster is one roster per run; a ratio change is a different roster | Separate runs joined in a `study`; or one enriched roster with `weight_by` |
| Disease-cap 200 versus 500 as a design axis | Same | Same |
| Prevalence-adjusted PPV at 1% and 3% | Not a design axis at all | `report.prevalences` as a list `Param`, computed in `aggregate` |
| Adaptive candidate selection inside one run | Refused | Two runs, selection recorded between them |
| Retry-on-transient-failure schedules | Core records attempts; it schedules nothing | Plugin `request.max_retries` / `backoff_secs`, recorded per unit |
| Wall-clock separation between batches | Core has no clock to enforce | Operator schedules; core records `started_at` and the realized order |

---

## Proposed plugin: `publishable-llm`

**Core-versus-plugin test.** Would "one request per unit against a hosted model, with a parsed output contract, token accounting, and a screening objective" be identical for a wet-lab assay, a simulation sweep, and an LLM benchmark? No. It is a plugin. Everything under `sweep`, `replication`, and `statistics` stays in core and the plugin declares nothing outside `parameters`.

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
apparatus_facts = ["provider", "model_id", "api_version", "endpoint_host_sha256"]
```

**Three consequences, all blocking, all worth stating before a run is scheduled.**

1. **`deployment_revision` is deliberately not in `apparatus_facts`.** Azure does not contractually return an immutable revision, and a declared fact must be yielded or core rejects the probe. It is emitted so it lands in `provenance.apparatus.facts`, and the spec is presently ambiguous about whether an undeclared fact participates in the change gate — see [Gaps](#gaps-this-analysis-found-in-the-specification).
2. **The probe runs before *every* execution.** A hosted deployment re-tuned during the E4 benchmark's 4.4 hours, or the C3 run's 12 hours, fails the run with no policy knob. That is correct — two deployment states are not one dataset — but it is an operational precondition, not a footnote. The ledger keeps both observations, so the evaluable earlier period stays reportable.
3. **Probes cost quota.** They run at `dry-run`, at run start, and before every execution, never at `validate`. Budget one authenticated call per execution on top of the cohort passes.

### Parameters

Grouped by what they control. Every one is under `parameters`; a template declares nothing outside it, so there is no top-level `llm:` block.

| Path | Type | Default | Why it is a parameter and not an apparatus fact |
|---|---|---|---|
| `llm.model` | str | required, `pattern=^[A-Za-z0-9._+-]+$` | You choose the deployment. The pattern is what makes it sweepable as a condition label |
| `llm.provider` | str | `azure_openai`, choices | Chosen |
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

`required_env = ["LLM_API_KEY"]`. Static, which is [the constraint E6 runs into](#e6--compiled-program-transfer).

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

Three, in descending order of consequence. None blocks the designs above; each would need an argument against `design-principles.md` to resolve.

1. **`apparatus_facts` conflates "must be yielded" with "gated on change."** For a hosted deployment these have to separate: a `system_fingerprint` that the provider sometimes omits must not fail the run for being absent, but must fail it for changing. Presently the only way to get the gate is to declare the fact, and declaring it makes absence fatal. `reference.md` § The apparatus core can only observe does not say whether an *undeclared* returned fact participates in the gate.
2. **`required_env` is static, but a sweep can span providers.** [E6](#e6--compiled-program-transfer) is the concrete case. A sweep over `llm.model` whose levels sit behind different credentials cannot declare its environment requirement, and `validate` will either fail on a credential no condition needs or pass on one a condition does.
3. **`limits` has no cost or quota threshold.** `max_executions` warns on a count; nothing warns on 213 million prompt tokens. Both source projects budget in tokens and dollars before committing, and `dry-run` is where such a check would belong.

---

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

`publishable dry-run` prints the resolved condition list, the execution count, and where every artifact will land, and it runs the apparatus probe — so all three numbers above are checkable before any quota is spent.

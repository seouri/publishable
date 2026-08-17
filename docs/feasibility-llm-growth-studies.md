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
| `run` refuses a dirty `src/**` | E4 (4.4 h) and C3 (12 h) cannot start while the other package has uncommitted edits — `run` enforces this today. [`draft`](reference.md#draft-runs) is specified to permit it and mark the run non-citable, which is no use for a confirmation run anyway, and it does not dispatch in this build ([§ Executability on this build](#executability-on-this-build)) |
| `resume` refuses a moved `uv.lock` | One lockfile serves both, so a dependency added for the shortcut makes an in-flight twelve-hour screening run unresumable — as specified; `resume` does not dispatch in this build either |

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

**Credentials follow the swept value.** The apparatus probe is permitted — and here required — to read a parameter the sweep varies, so each deployment is gated against its own first observation. The credentials reaching those deployments differ too, and a static `required_env` could not express that: it would demand an Azure key from a run that only touches Ollama, or stay silent about one a later condition needs. [`Param(requires_env=...)`](reference.md#a-credential-can-belong-to-a-parameter-value) on `llm.provider` puts the requirement on the value, so `validate` checks the union over the conditions this sweep resolves — which is what lets the source's local-Gemma cell join the same config as the Azure cells rather than needing a run of its own. Provider and model have to move together, so that cell enters as a `sweep.paired` entry coupling `llm.provider` with `llm.model` rather than as a fourth `grid` level — a cross of the two would emit conditions pointing an Azure deployment name at an Ollama endpoint.

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

**That is the declaration read on its own, and C1, C2 and C3 never read it on its own.** Each pairs `weight_by` with a `baseline` or a declared contrast, and this build refuses the combination outright as `E-DATA-WEIGHT-CONTRAST`: it weights each condition's own value and interval, while a `vs_baseline` delta and a `statistics.contrasts` entry are both computed over *unweighted* per-unit differences, so the delta would answer a different question than the two weighted values beside it with nothing in the record saying so. The refusal names its own two remedies — drop `weight_by` and report the contrast over the sample as drawn, or keep the weighting and carry the difference as a `summary`-step `Estimate` — and it says of itself that the combination will be honored once the paired estimators take weights. It is therefore a temporary blocker rather than a design refusal, and it is the one blocker these three runs do not share with the six screening runs ([§ Executability on this build](#executability-on-this-build)).

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
| Class-ratio (10:1 versus 32:1) as a design axis | The roster is one roster per run; a ratio change is a different roster | Separate runs joined in a `study`; or one enriched roster with `weight_by`. **Neither route runs on this build**: `study` does not dispatch, and `weight_by` beside any published comparison is refused as `E-DATA-WEIGHT-CONTRAST` — which is what all three shortcut runs declare ([§ Executability on this build](#executability-on-this-build)) |
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

1. **`deployment_revision` is declared even though Azure does not contractually return one.** A declared fact must be *supplied as a key*, not answered: the probe returns `None` where the provider omits a fingerprint, core records `null`, and [the gate compares observations](reference.md#the-apparatus-core-can-only-observe) — so `null → "fp_a3c1"` is the field becoming available rather than the deployment moving. What declaring it buys — in the specification; see [§ Executability on this build](#executability-on-this-build) — is the `dry-run` warning and the `unobserved` count, which is exactly the disclosure the source protocol asks for in prose when it says to "state explicitly if the provider does not return an immutable model revision."
2. **The probe runs before *every* execution.** A hosted deployment re-tuned during the E4 benchmark's 4.4 hours, or the C3 run's 12 hours, fails the run with no policy knob. That is correct — two deployment states are not one dataset — but it is an operational precondition, not a footnote. The ledger keeps both observations, so the evaluable earlier period stays reportable.
3. **Probes cost quota.** As specified they run at `dry-run`, at run start, and before every execution, never at `validate`, so the budget carries one authenticated call per execution on top of the cohort passes. None of that can be exercised yet, and the reason is worth being precise about: the apparatus mechanism is unbuilt in **core**, not merely unimplemented by this proposed plugin. `apparatus_probe` and `apparatus_facts` exist as declarable attributes on the template base class and are read by nothing; there is no `Apparatus` type, no `register_probe`, and no probe execution anywhere in the package ([§ Executability on this build](#executability-on-this-build)).

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

Three, all now closed in the specification. Each is recorded here with the case that surfaced it, because a gap's motivating example is the thing a later reader needs and the fixed text no longer carries.

1. **`apparatus_facts` conflated "must be yielded" with "gated on change."** A hosted deployment's revision fingerprint is returned on most calls and omitted on some. Declaring it made absence fatal; not declaring it left the change gate ambiguous, and the only safe move was to stop declaring a pin the study depends on. *Resolved* in `reference.md` § The apparatus core can only observe: a declared fact must be supplied as a **key**, `null` is a legal value meaning the apparatus did not answer, the gate compares two *observations* so an absence is never a change, and declaring the fact buys a `dry-run` warning plus an `unobserved` count. Every returned fact is gated whether declared or not, so there is no longer any reason to leave one out.
2. **`required_env` was static, but a sweep can span providers.** [E6](#e6--compiled-program-transfer) is the case: `validate` would either demand an Azure key from a run that never selects Azure or stay silent about one a later condition needs. *Resolved* by `reference.md` § A credential can belong to a parameter value — `Param(requires_env={...})` keyed by the parameter's `choices`, checked over the conditions the sweep actually resolves. The requirement travels with the decision that creates it, which is the same boundary `apparatus_facts` sits on read from the other side.
3. **Nothing showed the metered quantity before a run.** `limits.max_executions` warns on an execution count, which is not what a metered run is billed by: 20 executions over a 100,000-unit corpus is cheap by that measure and ruinous in practice. *Resolved* in `reference.md` § Before you spend it — `dry-run` now prints **unit-executions**, the sum of `len(io.units)` over every planned execution. Deliberately *not* resolved with a `limits` field: core has no price list and cannot count tokens, and a threshold in a currency it cannot measure would be the "looks handled and isn't" failure the correction family is held against. A budget that must be pre-registered is a template parameter, hashed with everything else.

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

**Several commands and one `io` method these designs lean on are not in this build.** `validate`, `run`, `new`, and `generate`/`g`/`init` dispatch; `dry-run`, `draft`, `resume`, `study`, and `reproduce` each print `unknown command` and exit 2, so every mention of them above is a claim about the specification rather than about what can be run. The same holds for `io.reuse_from`, which E3, E4, and E6 use to read their frozen compiled program, E6's swept `program_id` resolves through, and the shortcut's confirmation run uses to read its fine-tuned artifact: no such method exists yet, and a reader costing those runs should not assume the lineage they rest on is available. The apparatus probe is in the same position, for the reason given under [§ The apparatus probe is the sharpest fit, and it is also the operational risk](#the-apparatus-probe-is-the-sharpest-fit-and-it-is-also-the-operational-risk).

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

**As specified**, `publishable dry-run` prints the resolved condition list, the execution count, the **unit-executions** the plan will produce, and where every artifact will land, and it runs the apparatus probe — so every number above is meant to be checkable before any quota is spent. That is a claim about the specification and not about this build, in which `dry-run` is not a command at all ([§ Executability on this build](#executability-on-this-build)); every figure in this table was therefore computed by hand. Unit-executions is the one to multiply: at the sources' observed ~6,300 prompt tokens per patient, C3's 12 × 5 × 330 = 19,800 unit-executions is ~125 million prompt tokens, and that arithmetic is the budget check core deliberately leaves to you.

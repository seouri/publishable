# Feasibility analysis: growth chart literacy

`growth-chart-literacy` asks one question: **when a language model screens a pediatric growth trajectory, is it reading the curve, or is it counting how often the child came in?** Ten experiments answer it around a triad no published study combines — a clinician-adjudicated reference standard, a physiology-preserving counterfactual, and a utilization-invariance counterfactual.

This document does not reproduce that plan. It asks a narrower question: **which of its ten experiments `publishable`'s vocabulary expresses, what each config actually is, how fifteen runs share one directory, where the machinery every run needs lives, what it costs to execute, and which parts core refuses.** The refusals are the load-bearing half — a feasibility analysis that only lists what fits is an advertisement.

This document is non-normative and carries its own examples. It is **not** part of the shared worked example (`cohort-pilot`); see `CLAUDE.md` § Feasibility analyses. It is the second such analysis; the first, [`feasibility-llm-growth-studies.md`](feasibility-llm-growth-studies.md), read two adjacent repositories, and where a conclusion here differs from one there, the difference is re-derived rather than inherited.

## Contents

- [What the plan hand-rolls, and what core already owns](#what-the-plan-hand-rolls-and-what-core-already-owns)
- [One repository, fifteen configs](#one-repository-fifteen-configs)
- [Where the shared machinery lives](#where-the-shared-machinery-lives)
- [LLM API access](#llm-api-access)
- [Prompt templates, and why they are code](#prompt-templates-and-why-they-are-code)
- [Two templates, because there are two experiment types](#two-templates-because-there-are-two-experiment-types)
- [Where every statistical procedure lands](#where-every-statistical-procedure-lands)
- [The fifteen configs](#the-fifteen-configs)
- [What is not an experiment](#what-is-not-an-experiment)
- [What core refuses, and the route for each](#what-core-refuses-and-the-route-for-each)
- [Gaps this analysis found in the specification](#gaps-this-analysis-found-in-the-specification)
- [Executability on this build](#executability-on-this-build)
- [Cost and execution summary](#cost-and-execution-summary)

---

## What the plan hand-rolls, and what core already owns

The plan is at plan stage — nothing has been run — so this table is not a list of code to delete. It is the list of machinery the plan **commits to building** in prose, and would not have to. It is also the list of things the proposed plugin must **not** rebuild.

| Committed to in the plan | Core equivalent |
|---|---|
| "The reference frame must be declared, and this plan has not yet declared it" (§Cross-Cutting) — a preregistration item held in prose | A `Param` with `choices=["cdc2000", "who2006"]`, inside [`parameters_hash`](reference.md#three-hashes), so no run can be executed with the frame undeclared |
| "Four pre-data commitments … must be registered before data collection" (§Preregistration) | [`hypotheses`](reference.md#pre-registration), each carrying the declaring config's `parameters_hash`, so anything added after the run renders as exploratory |
| "Holm-Bonferroni within each experiment family; families are pre-registered as …" | [`statistics.correction: holm`](reference.md#sweeps-and-repeats), with the family size and its breakout recorded beside every interval — **within one run only**; see [the gaps](#gaps-this-analysis-found-in-the-specification) |
| "Bootstrapped CIs … resampled at the patient level, not the observation level" | [`statistics.resample`](reference.md#what-isnt-a-repeat) over the per-unit table, where the unit *is* the patient by construction |
| "k = 5 repeated runs per case" used as the basis for "effective power exceeds this nominal figure" (§Power basis) | Repeats never enter `n`. Five seeds give a [`repeat_spread`](reference.md#repeat-kinds), and `n` counts units — which is the arithmetic OI-21 was opened to fix |
| `visits_count_pre_dx` matching, stratification and manipulation, hand-managed per arm (§Cross-Cutting, *Visit-count control is universal*) | A unit attribute: matched by [`cluster_by`](reference.md#clustered-units), stratified by [`report_by`](reference.md#reporting-strata), manipulated as a swept parameter — three spellings for the three things the plan does with it |
| "Do not resolve an anchor with a bare `grep`" — `scripts/check_anchors.py`, a pre-commit hook, and a seven-lane coordination protocol over one Markdown file | Not core's job, and it stays the plan's. Worth naming because most of what it coordinates is *design* state that a config makes explicit and a `run.yaml` makes permanent |
| A model roster and prompt specification the plan says it lacks (OI-8) | `parameters` and [`list-templates`](reference.md#operation-commands): the roster is a swept axis and the prompt is a parameter, so "enumerable from the text" becomes enumerable from the file that ran |
| Three labels kept apart by naming discipline — `growth_dx_flag`, `growth concern`, `growth_issues` | Two are inputs and one is an output: the first two are unit attributes carried onto the [unit table](reference.md#the-unit-table-is-the-inference-base), the third a recorded column. Which is ground truth is `truth.label_source`, a parameter, and E1's decision rule is a config edit rather than a prose commitment |

The sharpest row is the fifth. The plan's Power basis paragraph says the k = 5 repeats push effective power above the McNemar floor, and its own OI-21 already suspects that. Core does not merely disagree — it makes the claim unwritable: an interval that narrows as seeds are added is [a mistake core prevents](experimental-designs.md#mistakes-core-prevents) by construction, and the five draws surface as `repeat_spread` instead.

---

## One repository, fifteen configs

The ten experiments split into **fifteen runs**, because a sub-experiment that changes the roster is a different run: E3 and E3b draw different patient sets, and E5's four arms have four rosters. Every one of the fifteen lives in one repository:

```
growth-chart-literacy/                    # the experiment repository
├── configs/
│   ├── e01-reference-gate/config.yaml
│   ├── e02-utilization-baseline/config.yaml
│   ├── …                                 # fifteen, one per run
│   └── e10-cross-model-2x2/config.yaml
├── src/
│   └── growth_chart/                     # ONE package, two pipelines
│       ├── experiment.py                 # ScreenExperiment, LabelExperiment
│       ├── prompts/                      # screen_v1.md, screen_v1_cot.md, arith_probe_v1.md
│       ├── serialize.py                  # the nine E3 serializations
│       └── steps/
│           ├── step01_summarize_units.py     scope = "run"
│           ├── step02_serialize.py           scope = "condition"
│           ├── step03_screen.py              scope = "repeat"      ← the metered step
│           ├── step04_compare.py             scope = "summary"
│           ├── step02_score.py               scope = "repeat"      ← the tabular pipeline
│           └── step03_compare.py             scope = "summary"
├── templates/
│   ├── growth_screen.py                  # the twelve LLM runs
│   └── growth_label.py                   # E1, E2, E6 — no LLM in them at all
├── tests/
└── pyproject.toml                        # publishable, publishable-growth-chart
```

**Fifteen configs, one `src/` package, two entrypoints.** `generate experiment` writes a package per experiment, which is right for fifteen *different* pipelines and wrong here: E3 through E10 run the same four steps and differ only in parameters. So the second config onward has its `entrypoint` line pointed at the first one's class — an ordinary hand-edit of a [freely editable file](reference.md#the-one-config-file) — and `validate` accepts it, which is [measured below](#executability-on-this-build). What that buys is the claim the whole sequence rests on: **identical `code_hash`, differing `parameters_hash`**, which is [same code, different parameters](design-principles.md#same-code-different-parameters) stated by the record rather than by the methods section.

**One repository is the right seam here, and it is the opposite conclusion from the previous analysis'** — which split two projects across three repositories. The reason is a property of *this* plan rather than a change of taste. Its dependency structure makes E4 through E10 evaluate one frozen screening pipeline over weeks; their reviewer-facing claim is that nothing about the code moved between E4 and E10. `code_hash` covers `src/**` and `templates/**`, so that claim is provable exactly when they share a tree, and a split would give each run a hash of its own with nothing to compare.

**What one repository costs is real, and it is E2 and E6.** Those two fit scikit-learn models and import no LLM machinery, so every commit to their code moves the recorded `code_hash` of screening runs that never called it — and while E2's or E6's code has uncommitted edits, [`run` refuses to start](reference.md#operation-commands) the twelve-hour E10. Three ways out, with the bill attached to each:

| Option | What it costs |
|---|---|
| One repository, E2/E6 code frozen before E4 starts | The discipline is a human commitment again — exactly the kind of thing this tool exists to stop relying on |
| One repository, `draft` for E2/E6 iteration | [`draft`](reference.md#draft-runs) permits a dirty tree and marks the run non-citable, which is right for developing a comparator and wrong for the comparator run that goes in the paper |
| A second repository for E2 and E6 | Their `code_hash` is then unrelated to the screening runs', which is honest — they measure a different apparatus — but E6's comparison against E4a's LLM becomes a cross-repository [`study`](reference.md#studies-what-a-paper-reports) rather than a contrast |

**The default is the first, and the tree above is drawn that way** — one repository, fifteen configs — because the cost only becomes real if E2 and E6 are still being written while E4 through E10 are executing. **The trigger for taking the third is stated rather than judged**: the first time a comparator commit would move the `code_hash` of a screening run already reported, or block one from starting, E2 and E6 move to a repository of their own. The plan's own OI-12 argues they belong there anyway — it says E6 is a utility comparator and not an ablation of the LLM, and a comparator sharing no code with the thing it is compared against is the accurate expression of that. E1 stays in the main repository under either arrangement, because its output is the label every screening run consumes.

**Nothing in these fifteen runs crosses a seam through `reuse_from`.** The sequence looks like lineage and is not. E1's clinician labels reach E4 through E10 as **input** — a new column in the roster table, covered by `input_manifest_hash` — and E3's format decision reaches them as a **parameter value a person typed**. Neither is an artifact, so [`provenance.upstream`](reference.md#lineage-between-runs) is `[]` for all of them, and the one place `io.reuse_from` genuinely belongs is E7 and E10 consuming the synthetic scaffolds E4b published from a `summary` step. That is worth stating rather than assuming: a chain of experiments is not a chain of runs.

---

## Where the shared machinery lives

Every LLM run needs the same four things: a way to find patients in the extract, a way to reach a deployment, a way to record what the deployment reported about itself, and a way to keep the request/response transcript. All four are domain machinery and none of them is a parameter, so they go in **one installed plugin**:

```
publishable-growth-chart/
├── pyproject.toml
└── src/publishable_growth_chart/
    ├── resolvers/units.py       @register_resolver("growth_trajectory")
    ├── probes/instrument.py     @register_probe("growth_llm_deployment")
    ├── writers/artifact.py      @register_writer(".transcript.jsonl") + its reader
    └── steps/request.py         a reusable BaseStep subclass, imported not registered
                                 (proposed here, and not among what was built to measure)
```

```toml
[project.entry-points."publishable.resolvers"]
"growth_trajectory" = "publishable_growth_chart.resolvers.units:resolve"

[project.entry-points."publishable.probes"]
"growth_llm_deployment" = "publishable_growth_chart.probes.instrument:probe"

[project.entry-points."publishable.writers"]
".transcript.jsonl" = "publishable_growth_chart.writers.artifact:write"

[project.entry-points."publishable.readers"]
".transcript.jsonl" = "publishable_growth_chart.writers.artifact:read"
```

**There is no `publishable.templates` entry point, and that is not an omission.** An installed template is [permanently refused](reference.md#the-one-config-file) — `E-TEMPLATE-INSTALLED-UNSUPPORTED` — so the templates that name this project's parameters stay in `templates/`, inside its own `code_hash`. [`tutorial-writing-a-plugin.md`](tutorial-writing-a-plugin.md) is the end-to-end precedent for exactly this split, and its Route A/Route B division is the shape followed here.

**The line between the plugin and `src/` is where a number comes from.** The plugin holds transport and observation: how a request is issued, retried and timed, and what the deployment says its own revision is. `src/growth_chart/` holds everything that decides an answer: the serializer, the prompts, the parser that turns a response into `growth_issues`, and the scoring. That line is not aesthetic — `code_hash` covers `src/**` and `templates/**` and does not cover an installed dependency, which `uv.lock` pins instead. A serializer inside the plugin would be a piece of code producing the numbers that no `code_hash` covered; a retry policy inside `src/` would move the run identity every time a backoff was tuned.

**`.transcript.jsonl` is a writer claim, not a core suffix.** `io.write` dispatches on the [longest suffix](reference.md#the-importable-surface) a writer registers or an installed distribution claims, and winning requires being strictly longer — so `.transcript.jsonl` beats core's `.jsonl` while nothing can take `.jsonl` itself away from core. That is how the per-request transcript lands beside `units.parquet` in each step directory without any step importing the plugin for a side effect.

---

## LLM API access

Three separate mechanisms carry it, and each is doing a different job.

**The credential follows the provider, not the template.** `required_env` is a template-level list and would be the wrong shape here: E10 sweeps across deployments, so it sweeps across the things being authenticated to. A static list would either demand an Anthropic key for a run that never selects one or stay silent about the key every condition needs. `requires_env` attaches the requirement to the choice:

```python
"llm.provider": Param(str, default="azure_openai",
                      choices=["azure_openai", "openai", "anthropic", "ollama"],
                      requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
                                    "openai":       ["OPENAI_API_KEY"],
                                    "anthropic":    ["ANTHROPIC_API_KEY"],
                                    "ollama":       []}),
```

`validate` then checks the **union over the conditions the sweep actually resolves**: three variables demanded across E10's four deployments and nothing demanded for the local one, reported per condition and by name. That is a build claim, so it is dated and its diagnostics quoted in [Executability on this build](#executability-on-this-build) rather than asserted here. Values live in `.env`, never in the config, and core [redacts a declared credential](reference.md#secrets--credentials) out of an exception's text — which matters more here than in most domains, since a client library interpolating a key into an error URL is ordinary.

**The deployment is an apparatus, and it is probed rather than declared.** `llm.deployment` is something you decide, so it is a `Param`. The model revision and system fingerprint behind that name are things you can only observe, so they are [apparatus facts](reference.md#the-apparatus-core-can-only-observe):

```python
@register_probe("growth_llm_deployment")
def probe(cfg) -> Apparatus:
    if cfg.parameters.llm.provider == "ollama":
        return Apparatus(facts={"model_version": None, "system_fingerprint": None})
    return Apparatus(facts=_deployment_metadata(cfg))   # one metadata request, read not computed
```

```python
    apparatus_probe = "growth_llm_deployment"
    apparatus_facts = ["model_version", "system_fingerprint"]
```

Core calls it at `dry-run`, at run start, before every execution and at `freeze`, and **a fact that moves from its first answered observation fails the run**. That gate is what a growth-chart study most needs and least has: a hosted deployment re-tuned in the middle of E10 would otherwise be reported as cross-model heterogeneity. A fact the probe cannot answer is recorded `null` and counted rather than read as a change, which E10's local arm exercises — again a build claim, and again [dated below](#executability-on-this-build).

**What the deployment costs is a per-unit measurement, not a usage report.** The request step records `prompt_tokens`, `completion_tokens`, `latency_ms` and `attempts` through `io.record`, one row per patient, so each becomes [`basis: units`](reference.md#the-unit-table-is-the-inference-base) with an `n`, a `ci95` and a `repeat_spread`. Written to a side file they would have no denominator; on the unit table, "the dense-schedule arm costs 340 more prompt tokens per patient" is a claim with an interval on it.

**Drift over time is a `batch` repeat, and it is available but not declared here.** All fifteen configs declare `{kind: seed, n: 5}`, matching the plan's k = 5. A study that wanted to separate *how much the deployment moved between blocks* from *how much the sampler moved within one* would declare `{kind: batch, n: 5}` outside it and read the two `repeat_spread` entries; the plan does not ask for that, and adding it would multiply every metered figure below by five.

---

## Prompt templates, and why they are code

**Prompt text lives at `src/growth_chart/prompts/<id>.md`, and the choice of prompt is a parameter naming it.**

```python
"prompt.id": Param(str, default="screen_v1",
                   choices=["screen_v1", "screen_v1_cot", "arith_probe_v1"],
                   help="Names src/growth_chart/prompts/<id>.md, inside code_hash"),
```

Three consequences, each deliberate:

- **Editing a prompt moves `code_hash`.** That is correct rather than inconvenient: a prompt change is a change in what produced the numbers, and a study whose prompt moved silently between E4 and E7 has no *same code, different parameters* claim left. It also means the prompts must be frozen at the same moment the pipeline is, which is what E3's decision rule already commits to.
- **The prompt cannot live in `input_dir`.** It would then be covered by `input_manifest_hash` instead — filed with the patient data as something measured rather than as something written — and [`diff`](reference.md#operation-commands) would report a prompt change as a change of dataset. Data and code [never share a repository](design-principles.md#code-and-data-never-share-a-repo), and the corollary is that code never hides in the data directory either.
- **Sweeping the prompt is sweeping an alias.** A swept value must render as `[A-Za-z0-9._+-]+`, which a path does not and a stem does — `E-SWEEP-VALUE-UNNAMEABLE` is what a config sweeping the text itself would earn, [measured below](#executability-on-this-build) on a list-valued parameter. The step resolves the stem to a file; the condition label stays `prompt_id=screen_v1_cot`, which is also what a figure legend needs.

**The nine E3 serializations are not nine prompts.** They are two parameters — `serialize.features` and `serialize.format` — crossed by `sweep.grid`, with one renderer in `src/growth_chart/serialize.py` reading both. Writing them as nine prompt files would put the factorial structure inside a filename, where no `sweep` can see it and no contrast can name a main effect. The rule generalizes: **a prompt file per condition means the design has escaped the config.**

---

## Two templates, because there are two experiment types

E1, E2 and E6 contain no LLM at all: they compute label agreement and fit tabular comparators. Their parameters share nothing with the screening runs' — no deployment, no serialization, no stimulus arm — so folding them into one `parameter_spec` would give every screening config a `model.max_depth` and every comparator config a `serialize.encoding`. Two project-local templates instead, `growth_screen` and `growth_label`, both discovered by path under `templates/`.

Each carries a cross-block rule only a template can know. `growth_screen` refuses a synthetic stimulus arm whose ground truth still claims to come from the EHR, and refuses `serialize.order: shuffled` unless `serialize.permutation` is swept — one arbitrary shuffle reported as *the* shuffled condition is E8's whole finding thrown away. `growth_label` is the specification's own example applied literally: a config that fits a model and declares neither a `holdout` nor a `fold` has nowhere to fit, so it is refused.

Both derive their metrics in `aggregate(units, cfg)` rather than returning them from a step, because that is [the only way a derived statistic gets a real interval](reference.md#templates-where-parameters-are-defined) — core can recompute it on a resampled table. `growth_screen` derives `flag_rate`, `accuracy`, `kappa`, `sensitivity` and `false_positive_rate`; `growth_label` derives `auroc`. The full text of both is [in the executability section](#executability-on-this-build), since every line of it was loaded and enforced by the build measured there.

**Five derived metrics is a deliberate ceiling.** The correction family is comparisons × metrics, so a template returning twenty diagnostics widens every interval in the run for numbers nobody reads. E7 declares three contrasts and its template derives five metrics: fifteen, which is what Holm is applied at.

---

## Where every statistical procedure lands

The plan's Statistical Test Reference enumerates every inferential procedure it uses. Each lands in exactly one of four places, and which one is what the config is deciding.

| Procedure, and where the plan uses it | Lands as | Why |
|---|---|---|
| Flagging rate, accuracy, sensitivity, FPR (all arms) | A **recorded column**, meaned over the unit table | `io.record` per patient; `basis: units`, with `ci95` and the four-way `n` |
| Cohen's / Fleiss' kappa (E1, E4) | A **template `aggregate`** metric | Derivable from the unit table, so core recomputes it on each resample and it gets a percentile interval — not a refusal |
| AUROC (E2, E6) | A **template `aggregate`** metric | Same route. A rank statistic over the whole table is exactly what `aggregate` is for |
| McNemar's paired difference (E4b, E5b, E5d) | A **declared contrast** | The *delta* is `paired_percentile_over_units` over the intersection, with `n_paired`. Core computes the quantity; it does not compute McNemar's p-value |
| Case-vs-control difference (E4a) | A **declared contrast**, unpaired and clustered | `cluster_by: match_set` makes the matched set the resample draw, so the interval respects the matching |
| Excess referral load (E5b) | The **same contrast**, read on the referral scale | The plan states it: with every trajectory shown under both conditions, the FPR difference *is* the discordance asymmetry divided by the trajectory count |
| Subgroup description by sex, age band, visit band | **`report_by`** | No executions added, no place in the correction family, because a description claims nothing |
| Permutation test of case-vs-control (E4a) | **`statistics.null_test`** | `shuffle: status` under a declared `cluster_by` permutes within each matched set — the classic matched permutation test rather than a free relabelling |
| Conditional logistic regression (E4a) | A `summary`-step **`Estimate`** | A stratified estimator, not a mean over a table |
| Mixed-effects logistic regression (E3, E5, E7, E8, E10) | A `summary`-step **`Estimate`** | [Out of scope for core aggregation](experimental-designs.md#what-core-will-not-do-for-you), by name |
| Cochran's Q (E5a, E8) | A `summary`-step **`Estimate`** | A three-condition omnibus test; core computes pairwise contrasts, not omnibus statistics |
| DeLong test (E6) | A `summary`-step **`Estimate`** | A test on two AUROCs over shared cases |
| Calibration curve (E2) | A **step artifact**, `io.write` | A diagnostic plot, not a metric |
| Shortcut reliance index (E7, E10) | A `summary`-step **`Estimate`** | A ratio of two main effects is a comparison **of two contrasts**, which is an interaction — contrasts do not nest |
| Age band × crossing magnitude interaction (E9) | A `summary`-step **`Estimate`** | The same rule, one experiment over |
| Holm across a declared family | **`statistics.correction`**, *within one run* | The plan's `{E5a–d}` and `{E10 model contrasts}` families cross run boundaries, and core corrects per run. See [the gaps](#gaps-this-analysis-found-in-the-specification) |

Two readings of that table are worth stating, because both are easy to get backwards. **The kappa and AUROC rows are not refusals** — routing them to a summary step would forfeit the interval that makes them reportable, and would be the most consequential mistake available when translating this plan. And **the McNemar rows are half-refusals**: the difference and its interval are computed, and only the p-value is not, which is a smaller loss than it sounds given the plan's own commitment to reporting intervals rather than significance.

---

## The fifteen configs

Every config below is **byte-identical to a file `publishable validate` accepted**, except that `data.input_dir` and `data.output_dir` are shown as `/secure/...` paths rather than the scratch paths the measurement used. What was run, and against which commit, is in [Executability on this build](#executability-on-this-build).

Three conventions run through all fifteen. Every arithmetic figure is stated **before** the YAML, in the four quantities that matter: conditions, repeats, the execution count `validate` checks against `limits.max_executions`, and the **metered requests** — conditions × repeats × units, which is the only figure a deployment bills for. That last one is not what `dry-run` prints: `dry-run`'s `unit-executions` counts every step's handling of every unit, including the `run`-scoped roster summary and the `condition`-scoped serializer, neither of which issues a request. Both numbers are given, and they are different numbers on purpose.


### E1 — the reference-standard gate

**The problem.** `growth_dx_flag` is an EHR-derived label, and if children seen more often are more likely to *receive* a growth diagnosis for the same trajectory, then every downstream shortcut finding is confounded at the label level. E1 asks whether clinician–label agreement falls as visit count rises.

**The design decision.** The visit-count tertile is the axis, and it is a property of the units rather than of the pipeline, so it is a [`groups`](reference.md#expansion-modes) axis read from an existing column: `allocation: between` with `assign: {visit_tertile: {method: by_attribute}}`. That choice is what turns the plan's "bootstrapped CIs on the between-stratum kappa difference" into something core computes — kappa is a `growth_label.aggregate` metric, so a declared contrast between the high and low tertiles gets a percentile interval over 2,000 draws. Writing the tertile as [`report_by`](reference.md#reporting-strata) instead would have described the three strata and produced **no** difference between them, which is the distinction that decides this config.

**One repeat, deliberately.** The pipeline reads two fixed label columns and computes an agreement statistic; a second execution recomputes the same number. `growth_label` declares `default_repeats = 1` for that reason, and a run declaring more would be paying for a row of zeros.


| | |
|---|---|
| Units | 200 adjudicated patients — 100 `growth_dx_flag`, 100 `healthy_flag`, stratified across visit-count deciles |
| Conditions × repeats | 3 × 1 |
| Executions | 5 (`dry-run`) |
| `dry-run` unit-executions | 600 |
| Metered LLM requests | **0** — E1 contains no model |


```yaml
# configs/e01-reference-gate/config.yaml
schema_version: "1.0"
experiment_type: growth_label
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e01-reference-gate
  description: "E1: is growth_dx_flag a trustworthy stand-in for clinician concern, and does agreement fall as visits rise"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:LabelExperiment"

data:
  input_dir: /secure/data/gcl/e01-reference-gate
  output_dir: /secure/results/gcl/e01-reference-gate
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [visit_tertile, sex]
    allocation: between
    assign:
      visit_tertile: {method: by_attribute}

parameters:
  model:
    kind: agreement
    feature_set: count_only
    max_depth: 3
  truth:
    label_source: growth_dx_flag
    rater: consensus
  frame:
    reference: cdc2000

sweep:
  groups:
    - {by: visit_tertile, levels: [low, mid, high]}

replication:
  repeats:
    - {kind: seed, n: 1}
  order: as_declared
  rationale: "The pipeline reads two fixed label columns; a second execution recomputes the same kappa."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: kappa_gap, of: "visit_tertile=high", against: "visit_tertile=low"}
  report_by: [sex]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Clinician-label agreement is lower in the high-visit stratum than in the low-visit stratum."
    metric: step02_score.kappa
    compare: {contrast: kappa_gap}
    direction: less
    threshold: -0.15
    evaluate_on: ci95_upper
```


### E2 — the utilization baseline

**The problem.** Testing whether the model uses a visit-count shortcut is only meaningful if the shortcut is learnable, so E2 fits a visit-count-only logistic regression and reports its AUROC. Its magnitude is the line every LLM result is read against.

**The design decision.** The feature set is a **named** parameter and not a list, because a swept value must render as `[A-Za-z0-9._+-]+` and `[visits_count_pre_dx, visits_span_days]` does not — `E-SWEEP-VALUE-UNNAMEABLE`, [measured below](#executability-on-this-build). `count_only` and `count_spacing_span` are the two names, the first designated `sweep.baseline`, and the step resolves each to its column list. The five folds are the split the comparator is fitted on, which `growth_label.validate` requires: a model fitted on the units it will be tested on is what `E-…`-free config discipline cannot catch and a template's cross-block rule can. A fold level's `stratify_by` takes **a string, not a list** — the one shape in these fifteen files that a reader of the config schema alone would get wrong.

**"AUROC > 0.5" is not a hypothesis core can compare.** `compare` names both sides, and there is no condition called *chance*. So the claim is carried by a `summary` step returning an [`Estimate`](reference.md#estimate-carries-your-interval-without-core-claiming-it), and the hypothesis names that summary metric — which takes no `compare` — with `evaluate_on: ci95_lower`.


| | |
|---|---|
| Units | 1,000 patients, 500 case / 500 control across visit-count deciles, disjoint from E1's adjudication sample |
| Conditions × repeats | 2 × 5 folds |
| Executions | 12 (`dry-run`) |
| `dry-run` unit-executions | 3,000 |
| Metered LLM requests | **0** |


```yaml
# configs/e02-utilization-baseline/config.yaml
schema_version: "1.0"
experiment_type: growth_label
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e02-utilization-baseline
  description: "E2: how much of the label a visit-count-only model recovers, and what spacing and span add"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:LabelExperiment"

data:
  input_dir: /secure/data/gcl/e02-utilization-baseline
  output_dir: /secure/results/gcl/e02-utilization-baseline
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [visit_decile, sex]
    allocation: within

parameters:
  model:
    kind: logistic
    feature_set: count_only
    max_depth: 3
  truth:
    label_source: growth_dx_flag
    rater: consensus
  frame:
    reference: cdc2000

sweep:
  baseline: {model.feature_set: count_only}
  grid:
    model.feature_set: [count_spacing_span]

replication:
  repeats:
    - {kind: fold, k: 5, stratify_by: visit_decile}
  order: as_declared
  rationale: "Five stratified folds; every unit is tested once per fold sweep, so the AUROC is out-of-fold."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  report_by: [visit_decile]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "A visit-count-only model discriminates the label above chance."
    metric: step03_compare.auroc_count_only
    direction: greater
    threshold: 0.5
    evaluate_on: ci95_lower
```


### E3 — serialization selection

**The problem.** Feature readability is sensitive to how numbers are written down, and number tokenization alone has been shown to invert model rankings — so a growth-chart result in one arbitrary format is not a result about growth charts. E3 crosses three feature derivations with three presentation formats and reports the spread as a headline caveat.

**The design decision.** A full 3 × 3 factorial *with a designated reference cell* is the one shape a naive config gets wrong: listing the baseline's own value in the `grid` renders that cell twice, once as `00_baseline` and once as its own product row. The spelling that works is the specification's second baseline row — **fix the axis you are measuring and leave the axis you are stratifying over free**. `baseline: {serialize.features: derived}` with `grid` listing only `raw` and `raw_plus_derived` against all three formats gives three per-format baselines and six product cells: nine conditions, one per factorial cell, and `vs_baseline` is the feature-derivation contrast *within each format* for free. The two format contrasts at fixed derivation are declared, because no baseline produces them.


| | |
|---|---|
| Units | 200 matched patients from the E1-validated pool |
| Conditions × repeats | 9 × 5 |
| Executions | 56 (`dry-run`) — `validate` checks 9 × 5 = 45 against `limits.max_executions: 500` |
| `dry-run` unit-executions | 11,200 |
| Metered LLM requests | **9,000** = 9 × 5 × 200, matching the plan's own figure |
| Correction family | 8 baseline comparisons + 2 declared contrasts, × 5 derived metrics |


```yaml
# configs/e03-serialization/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e03-serialization
  description: "E3: does how the trajectory is written down move screening accuracy independent of its information content"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e03-serialization
  output_dir: /secure/results/gcl/e03-serialization
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {serialize.features: derived}
  grid:
    serialize.features: [raw, raw_plus_derived]
    serialize.format: [markdown_table, sentences, digit_string]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws at temperature 0; the deployment is not deterministic, and repeat_spread is what says how far it moves."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: digits_vs_table, of: "format=digit_string__baseline",
       against: "format=markdown_table__baseline"}
    - {id: sentences_vs_table, of: "format=sentences__baseline",
       against: "format=markdown_table__baseline"}
  report_by: [age_band]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "The digit-string format loses accuracy against the markdown table at the same feature derivation."
    metric: step03_screen.accuracy
    compare: {contrast: digits_vs_table}
    direction: less
    threshold: -0.10
    evaluate_on: ci95_upper
```


### E3b — the tokenization stress test

**The problem.** Standard decimal encoding and a place-annotated or delimiter-modified encoding carry identical information, so a difference between them is tokenization rather than reasoning. Scoring arithmetic correctness separately from classification correctness is what distinguishes *cannot compute* from *does not understand growth*.

**The design decision.** The plan describes 150 patients × 3 visits = 450 calculations, which reads like technical replication — and [`data.units.measurements`](reference.md#what-isnt-a-repeat) is where that belongs, collapsing at unit resolution before any step runs. It does not work here, and the refusal is precise: a resolver has no columns beyond the attributes it yields, so `measurements: {by: calc_id}` requires the resolver to emit **one `Unit` per calculation sharing a patient key** (`E-RESOLVER-MEASUREMENT-FIELD`), and a `collapse: mean` applied wholesale then tries to average the string-valued attributes too (`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`). Both were measured. The simpler expression, used here, is a per-unit `arith_error_rate` column the step records over that patient's three calculations — which is the same collapse done one layer up, at the cost of losing the per-calculation rows from the unit table.


| | |
|---|---|
| Units | 150 patients, three scored calculations each |
| Conditions × repeats | 2 × 5 |
| Executions | 14 (`dry-run`) |
| `dry-run` unit-executions | 2,100 |
| Metered LLM requests | **1,500** = 2 × 5 × 150 |


```yaml
# configs/e03b-tokenization/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e03b-tokenization
  description: "E3b: does place-annotated numeric encoding change the answer, and how much of the raw deficit is arithmetic"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e03b-tokenization
  output_dir: /secure/results/gcl/e03b-tokenization
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 1024
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: arith_probe_v1
  serialize:
    features: raw
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: 3
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {serialize.encoding: decimal}
  grid:
    serialize.encoding: [place_annotated]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per encoding; each unit contributes three per-visit calculations, collapsed at resolution."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: encoding, of: "encoding=place_annotated", against: "baseline"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Place-annotated encoding lowers the arithmetic error rate against decimal encoding."
    metric: step03_screen.arith_error_rate
    compare: {contrast: encoding}
    direction: less
    threshold: -0.05
    evaluate_on: ci95_upper
```


### E4a — the matched real-patient arm

**The problem.** Real cases and controls differ in many correlated ways, so E4a matches 300 pairs exactly on visit count and closely on spacing, age band and sex, leaving the trajectory as the only difference. It is the affirmative half of the interpretation claim, on real data.

**The design decision.** Case-versus-control is a property of the units, so it is a `groups` axis read from an existing column, and the matching is carried by `cluster_by: match_set` — which is what tells core the two arms are not independent samples. Three things follow without further declaration: intervals are clustered on the matched set, `statistics.resample` draws whole sets rather than subjects, and `statistics.null_test` with `shuffle: status` permutes the label *within* each set, giving the classic matched permutation test rather than a free relabelling. The arms are peers, so no `sweep.baseline` may name one; the comparison is a declared contrast.

**Conditional logistic regression is the refusal here**, and the route is a `summary`-step `Estimate`. What core computes is the clustered difference in flag rate with its interval, which is the quantity, not the stratified estimator.


| | |
|---|---|
| Units | 600 — 300 matched case/control pairs |
| Conditions × repeats | 2 × 5 |
| Executions | 14 (`dry-run`) |
| `dry-run` unit-executions | 4,800 |
| Metered LLM requests | **3,000** = 2 × 5 × 300 units per arm |


```yaml
# configs/e04a-matched-pairs/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e04a-matched-pairs
  description: "E4a: does the screen separate cases from controls matched on visit count, spacing, age band and sex"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e04a-matched-pairs
  output_dir: /secure/results/gcl/e04a-matched-pairs
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [status, match_set, sex]
    allocation: between
    cluster_by: match_set
    assign:
      status: {method: by_attribute}

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

sweep:
  groups:
    - {by: status, levels: [control, case]}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per arm; the matched-set cluster is what carries the pairing into the interval."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  null_test: {method: permutation, n: 5000, shuffle: status}
  contrasts:
    - {id: case_vs_control, of: "status=case", against: "status=control"}
  report_by: [sex]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "The screen flags matched cases more often than their matched controls."
    metric: step03_screen.flag_rate
    compare: {contrast: case_vs_control}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E4b — the physiology-preserving counterfactual

**The problem.** Take a real patient's exact visit schedule and substitute two synthetic trajectories onto that identical scaffold — one genuinely concerning, one healthy. Utilization is identical across conditions by construction, so a model that cannot separate them is not reading the curve at all.

**The design decision.** The scaffold is the unit and the physiology is a swept parameter, which makes the design within-subject and the contrast paired over the intersection of both arms' completed units. `truth.label_source: by_construction` is not decoration: `growth_screen.validate` refuses a synthetic stimulus arm that still claims an EHR label, because a synthetic trajectory has no `growth_dx_flag` and a config saying otherwise is describing a run that cannot happen. The wholly synthetic arm carries no `visits_count_pre_dx` at all — its visit structure is identical across conditions by construction, which is the plan's universal visit-count control obtained a different way.

**This is the run that publishes scaffolds.** E7 and E10 consume the same 250 synthetic schedules, and the way they get them is a `summary` step here writing them under a name downstream runs address by [`io.reuse_from`](reference.md#lineage-between-runs) — the only genuine lineage edge in the fifteen.


| | |
|---|---|
| Units | 250 real visit scaffolds |
| Conditions × repeats | 2 × 5 |
| Executions | 14 (`dry-run`) |
| `dry-run` unit-executions | 3,500 |
| Metered LLM requests | **2,500** = 2 × 5 × 250, the plan's 500 trials × k = 5 |


```yaml
# configs/e04b-physiology-swap/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e04b-physiology-swap
  description: "E4b: with the visit schedule held byte-for-byte identical, does the screen respond to the curve"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e04b-physiology-swap
  output_dir: /secure/results/gcl/e04b-physiology-swap
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_physiology
    physiology: healthy
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.physiology: healthy}
  grid:
    stimulus.physiology: [concerning]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per physiology arm on one scaffold roster; the schedule is identical across arms by construction."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: physiology_sensitivity, of: "physiology=concerning", against: "baseline"}
  report_by: [age_band]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "On one visit schedule, the concerning trajectory is flagged more often than the healthy one."
    metric: step03_screen.flag_rate
    compare: {contrast: physiology_sensitivity}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E5a — the schedule-density ladder

**The problem.** One true physiological trajectory, resampled onto sparse, typical and dense visit schedules with the growth signal held fixed. If the prediction moves, only the schedule moved.

**The design decision.** Three densities is a three-level parameter axis with the typical arm designated baseline, so `vs_baseline` gives both comparisons and the declared `dense_vs_sparse` contrast gives the extreme one the 2 × 2 later reuses. The hypothesis is an **invariance** claim, and the shape matters: written as a directional test on a point estimate it passes on an estimate whose interval permits a large effect. `direction: less, threshold: 0.05, evaluate_on: ci95_upper` is the equivalence form, and it is the reason E5's null being the desired outcome does not make E5 unfalsifiable.


| | |
|---|---|
| Units | 200 trajectories |
| Conditions × repeats | 3 × 5 |
| Executions | 20 (`dry-run`) |
| `dry-run` unit-executions | 4,000 |
| Metered LLM requests | **3,000** = 3 × 5 × 200, the plan's 600 trials × k = 5 |


```yaml
# configs/e05a-schedule-density/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e05a-schedule-density
  description: "E5a: one physiology resampled onto sparse, typical and dense schedules"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e05a-schedule-density
  output_dir: /secure/results/gcl/e05a-schedule-density
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_schedule
    physiology: as_recorded
    schedule: typical
    crossing_channels: 2.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.schedule: typical}
  grid:
    stimulus.schedule: [sparse, dense]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per density; the physiology is fixed per unit, so every difference is the schedule's."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: dense_vs_sparse, of: "schedule=dense", against: "schedule=sparse"}
  report_by: [age_band]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Predictions are invariant to schedule density between 3 and 20+ visits."
    metric: step03_screen.flag_rate
    compare: {contrast: dense_vs_sparse}
    direction: less
    threshold: 0.05
    evaluate_on: ci95_upper
```


### E5b — the flat-curve negative control

**The problem.** Unambiguously healthy flat trajectories, each shown once with an inflated visit count and once with a typical one. Every case is negative by construction, so the difference in flag rate between the two conditions is referral load incurred at **zero** diagnostic return.

**The design decision.** Two things make this the cleanest arm in the plan and the cheapest to express. Because every unit is negative under both conditions, `false_positive_rate` is a recorded-column mean and the declared contrast on it *is* the quantity the plan wants — the plan says so itself, noting that under a within-subject design the marginal FPR difference is exactly the discordance asymmetry McNemar's tests, divided by the number of trajectories. And `scoring.parse_failure: negative` is the one config in the fifteen that departs from the default: with the truth constant, an unparseable response is a screen that did not flag, and routing it to `ineligible` would quietly remove the units most likely to have been confused by the inflated schedule.


| | |
|---|---|
| Units | 200 synthetic flat trajectories |
| Conditions × repeats | 2 × 5 |
| Executions | 14 (`dry-run`) |
| `dry-run` unit-executions | 2,800 |
| Metered LLM requests | **2,000** = 2 × 5 × 200 |


```yaml
# configs/e05b-flat-negative/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e05b-flat-negative
  description: "E5b: unambiguously healthy flat curves under an inflated and a typical visit count"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e05b-flat-negative
  output_dir: /secure/results/gcl/e05b-flat-negative
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_flat
    physiology: flat
    schedule: typical
    crossing_channels: 0.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: negative

sweep:
  baseline: {stimulus.schedule: typical}
  grid:
    stimulus.schedule: [dense]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Every unit is negative by construction, so the flag rate is the false-positive rate and its contrast is excess referral load."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: excess_fpr, of: "schedule=dense", against: "baseline"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "An inflated visit count raises the false-positive rate on curves that are negative under both conditions."
    metric: step03_screen.false_positive_rate
    compare: {contrast: excess_fpr}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E5c — the fixed-N residual test

**The problem.** Display exactly five visits per patient regardless of the true total, then ask whether accuracy still tracks the *hidden* total. A residual association means the shortcut is carried by something beyond raw count-in-context.

**The design decision.** This is the one arm that is **not a condition at all**. Nothing about the pipeline varies: the display cap is fixed at five, the roster is one, and the covariate under test is hidden from the model by construction. So the config declares no `sweep`, the hidden total becomes a unit attribute reported over by `report_by: [true_count_band]`, and the residual association itself — a slope, not a difference between two conditions — is a `summary`-step `Estimate` named by the hypothesis. `statistics.correction: none` follows: a single-condition run has no family.

A contrast is genuinely unavailable here, and it is worth being plain about why: `of` and `against` name **two conditions**, and there is only one. A version of this arm that wanted a core-computed difference would have to make the count band a `groups` axis — turning a covariate into a design cell, which is the wrong description of an experiment whose whole point is that the band was invisible to the model.


| | |
|---|---|
| Units | 300 patients with at least 5 visits |
| Conditions × repeats | 1 × 5 |
| Executions | 8 (`dry-run`) |
| `dry-run` unit-executions | 2,400 |
| Metered LLM requests | **1,500** = 1 × 5 × 300 |
| Warning at `validate` | `W-DATA-CLUSTER-UNDECLARED` on `true_count_band` — see [the gaps](#gaps-this-analysis-found-in-the-specification) |


```yaml
# configs/e05c-fixed-n/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e05c-fixed-n
  description: "E5c: with exactly five visits displayed, does accuracy still track the hidden true total"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e05c-fixed-n
  output_dir: /secure/results/gcl/e05c-fixed-n
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [true_count_band, sex]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: 5
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "One condition, five draws; the manipulation is a fixed display cap and the covariate is hidden."

statistics:
  correction: none
  resample: {method: bootstrap, n: 2000}
  report_by: [true_count_band]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "With five visits displayed, the flag rate is still associated with the hidden true total."
    metric: step04_compare.residual_slope
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E5d — the explicit framing probe

**The problem.** Identical case data, with and without a sentence stating the visit count. A framing effect distinguishes a *latent* shortcut learned from distributional co-occurrence from one that can be *triggered* by surface priming.

**The design decision.** The manipulation is a boolean parameter the serializer reads, which is the cheapest possible expression of a within-subject probe and the one that keeps the two arms provably identical in everything else — the same serializer, the same prompt, one sentence prepended. `order: randomized` shuffles the (condition, seed) pairs so the framing arm is not confounded with position in the run, which is what the plan means by "within-subject, randomized order" and is a declaration rather than a script.


| | |
|---|---|
| Units | 300 patients |
| Conditions × repeats | 2 × 5 |
| Executions | 14 (`dry-run`) |
| `dry-run` unit-executions | 4,200 |
| Metered LLM requests | **3,000** = 2 × 5 × 300 |


```yaml
# configs/e05d-framing/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e05d-framing
  description: "E5d: does stating the visit count in words raise the positive rate on identical case data"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e05d-framing
  output_dir: /secure/results/gcl/e05d-framing
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {serialize.state_visit_count: false}
  grid:
    serialize.state_visit_count: [true]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Within-subject framing probe; the two arms differ by one sentence and nothing else."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: framing, of: "state_visit_count=true", against: "baseline"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Stating the visit count raises the positive rate on otherwise identical case data."
    metric: step03_screen.flag_rate
    compare: {contrast: framing}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E6 — the non-LLM comparator

**The problem.** Without a simple-model comparator a respectable LLM AUROC is uninterpretable, since it could reflect trajectory reading or it could reflect that logistic regression on four features matches it. The informative version withholds visit count from the comparator.

**The design decision.** Two axes — model kind and feature set — with `baseline: {model.feature_set: llm_matched}` fixing the axis under test and leaving `model.kind` free, so each of logistic regression and the boosted tree gets its own reference and the visit-count contribution is `vs_baseline` within each. Fixing both would mark the diagonal cell `confounded: true`, which `validate` warns about by name and which was measured before the config was rewritten. `cluster_by: match_set` carries E4a's matched sets into the folds, so no matched pair is split across train and test — a rule core enforces rather than documents.

**The DeLong comparison against the LLM is the refusal**, and it is a cross-repository one on the recommendation [above](#one-repository-fifteen-configs): E6's AUROC and E4a's flag rate live in different runs, so the comparison is a [`study`](reference.md#studies-what-a-paper-reports) joining both records, with the test itself a `summary`-step `Estimate`. The plan's own OI-12 already argues E6 is a utility comparator rather than a test of claim (b), and this is what that reading costs and buys.


| | |
|---|---|
| Units | 600 — the E4a matched sample |
| Conditions × repeats | 4 × 5 folds |
| Executions | 22 (`dry-run`) |
| `dry-run` unit-executions | 3,000 |
| Metered LLM requests | **0** |


```yaml
# configs/e06-comparator/config.yaml
schema_version: "1.0"
experiment_type: growth_label
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e06-comparator
  description: "E6: what a logistic regression and a boosted tree recover from the same features, with and without visit count"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:LabelExperiment"

data:
  input_dir: /secure/data/gcl/e06-comparator
  output_dir: /secure/results/gcl/e06-comparator
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [status, match_set, sex]
    allocation: within
    cluster_by: match_set

parameters:
  model:
    kind: logistic
    feature_set: llm_matched
    max_depth: 3
  truth:
    label_source: clinician_consensus
    rater: consensus
  frame:
    reference: cdc2000

sweep:
  baseline: {model.feature_set: llm_matched}
  grid:
    model.kind: [logistic, gbt]
    model.feature_set: [llm_matched_minus_count]

replication:
  repeats:
    - {kind: fold, k: 5}
  order: as_declared
  rationale: "Five cluster-respecting folds over the E4a matched sample, so no matched set is split across train and test."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: count_contribution, of: "kind=logistic__baseline",
       against: "kind=logistic__feature_set=llm_matched_minus_count"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Withholding visit count costs the tabular comparator discrimination."
    metric: step02_score.auroc
    compare: {contrast: count_contribution}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E7 — the 2 × 2 synthesis

**The problem.** Cross the two physiology conditions with the sparse and dense schedule arms on shared synthetic scaffolds, and report the full double dissociation as one table. This is the paper.

**The design decision.** The 2 × 2 is `baseline: {stimulus.physiology: healthy}` with `grid` listing only `concerning` against both schedules — four cells, two of them per-schedule baselines, no cell rendered twice. `vs_baseline` then *is* the physiology main effect at each utilization level, and the two utilization contrasts are declared because the arms of that axis are peers relative to the baseline. Three hypotheses rather than one composite, matching the plan: the utilization effect stated as equivalence on `ci95_upper`, the physiology effect as superiority on `ci95_lower`, and the index itself.

**The shortcut reliance index is the headline number and the sharpest refusal in the plan.** It is the ratio of the utilization main effect to the physiology main effect — a comparison of two contrasts, which is an interaction, and [contrasts do not nest](experimental-designs.md#what-core-will-not-do-for-you). It lands as a `summary`-step `Estimate` with its own bootstrapped interval, marked `reported: true`, outside the correction family and never recomputed by core. A hypothesis may name it — `h1c` does — and the verdict then records `verdict_rests_on: reported` rather than `computed`, which is exactly the disclosure a reader of that number needs.


| | |
|---|---|
| Units | 200 of E4b's 250 scaffolds, restricted to those where both density arms are constructible |
| Conditions × repeats | 4 × 5 |
| Executions | 26 (`dry-run`) |
| `dry-run` unit-executions | 5,200 |
| Metered LLM requests | **4,000** = 4 × 5 × 200, the plan's own figure |
| Correction family | 2 baseline comparisons + 3 declared contrasts, × 5 derived metrics |


```yaml
# configs/e07-two-by-two/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e07-two-by-two
  description: "E7: the 2×2 — physiology crossed with utilization on shared synthetic scaffolds"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e07-two-by-two
  output_dir: /secure/results/gcl/e07-two-by-two
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_physiology
    physiology: healthy
    schedule: sparse
    crossing_channels: 2.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.physiology: healthy}
  grid:
    stimulus.physiology: [concerning]
    stimulus.schedule: [sparse, dense]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per cell of the 2×2; each of the 200 scaffolds appears in all four cells."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: physiology_at_sparse, of: "physiology=concerning__schedule=sparse",
       against: "schedule=sparse__baseline"}
    - {id: physiology_at_dense, of: "physiology=concerning__schedule=dense",
       against: "schedule=dense__baseline"}
    - {id: utilization_at_healthy, of: "schedule=dense__baseline",
       against: "schedule=sparse__baseline"}
    - {id: utilization_at_concerning, of: "physiology=concerning__schedule=dense",
       against: "physiology=concerning__schedule=sparse"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1a
    kind: confirmatory
    statement: "The utilization effect on healthy scaffolds is negligible."
    metric: step03_screen.flag_rate
    compare: {contrast: utilization_at_healthy}
    direction: less
    threshold: 0.05
    evaluate_on: ci95_upper
  - id: h1b
    kind: confirmatory
    statement: "The physiology effect at a sparse schedule is positive."
    metric: step03_screen.flag_rate
    compare: {contrast: physiology_at_sparse}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
  - id: h1c
    kind: confirmatory
    statement: "The shortcut reliance index excludes parity between the two main effects."
    metric: step04_compare.shortcut_reliance_index
    direction: less
    threshold: 1.0
    evaluate_on: ci95_upper
```


### E8 — ordering sensitivity

**The problem.** Chronological, reverse-chronological, and shuffled presentations of the same visits, with the shuffled condition using five distinct permutations rather than one. It constrains mechanism; it does not adjudicate the interpretation claim, which is why the plan reports it after E7.

**The design decision.** Seven serializations is a **ragged axis** — one chronological, one reverse, five shuffles — and no `grid` product expresses it, because `order` and `permutation` are not independent: `permutation` is meaningless for the two single-ordering arms. [`sweep.paired`](reference.md#expansion-modes) is the spelling: a list of dicts is one axis, not a product, so the six non-baseline rows are enumerated and the baseline supplies the seventh. `growth_screen.validate` refuses `order: shuffled` unless `permutation` is swept, which is the rule that stops one arbitrary shuffle being reported as *the* shuffled condition.

**The five shuffles and the five repeats are separate multipliers, and core keeps them separate.** The shuffles vary the stimulus, so they are conditions; the seeds vary only the sampling of the response, so they are repeats and land in `repeat_spread`. Collapsing them would be the exact mistake the plan warns about, and here it is structurally unavailable.

**Cochran's Q across the three collapsed conditions is the refusal**, along with the mixed-effects model that nests permutation within patient. What core gives instead is each ordering against chronological as a paired contrast — which is the pairwise follow-up a significant Q would license anyway.


| | |
|---|---|
| Units | 300 patients, stratified by visit-count band |
| Conditions × repeats | 7 × 5 |
| Executions | 44 (`dry-run`) |
| `dry-run` unit-executions | 13,200 |
| Metered LLM requests | **10,500** = 7 × 5 × 300, the plan's own figure |
| Warning at `validate` | `W-DATA-CLUSTER-UNDECLARED` on `visit_band` |


```yaml
# configs/e08-ordering/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e08-ordering
  description: "E8: chronological, reverse-chronological, and five distinct shuffles of the same visits"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e08-ordering
  output_dir: /secure/results/gcl/e08-ordering
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [visit_band, sex]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: observed
    physiology: as_recorded
    schedule: as_recorded
    crossing_channels: 2.0
  truth:
    label_source: clinician_consensus
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {serialize.order: chronological, serialize.permutation: 0}
  paired:
    - {serialize.order: reverse, serialize.permutation: 0}
    - {serialize.order: shuffled, serialize.permutation: 0}
    - {serialize.order: shuffled, serialize.permutation: 1}
    - {serialize.order: shuffled, serialize.permutation: 2}
    - {serialize.order: shuffled, serialize.permutation: 3}
    - {serialize.order: shuffled, serialize.permutation: 4}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "The five shuffles vary the stimulus and are conditions; the five seeds vary only the response and are repeats."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: reverse_vs_chronological, of: "order=reverse__permutation=0",
       against: "baseline"}
    - {id: shuffle0_vs_chronological, of: "order=shuffled__permutation=0",
       against: "baseline"}
  report_by: [visit_band]

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "Shuffling the visits costs accuracy against chronological order."
    metric: step03_screen.accuracy
    compare: {contrast: shuffle0_vs_chronological}
    direction: less
    threshold: 0.0
    evaluate_on: ci95_upper
```


### E9 — age-dependent norm application

**The problem.** Percentile crossing is developmentally normal in infancy and a red flag in mid-childhood, so a model that flags crossing magnitude without conditioning on age is applying a threshold rule rather than clinical reasoning. E9 matches crossing magnitude across two age bands and asks whether the flagging rate differs.

**The design decision.** Two axes of different kinds, composed. The age band is a property of the units, so it is a `groups` axis assigned `by_attribute`; the crossing magnitude is a property of the synthetic stimulus, so it is a parameter `grid`. `baseline: {stimulus.crossing_channels: 1.0}` fixes the parameter axis and expands over the group axis — a baseline may never fix a group level — giving one reference per band and four crossed cells. The two band contrasts at matched magnitude are declared, since neither band is the other's reference.

**The interaction is the refusal**, as it is in E7: age band × crossing magnitude compares two contrasts. The plan's own reporting rule already asks for the between-band difference with a bootstrapped CI rather than a p-value, and that difference is precisely what the declared contrasts give.


| | |
|---|---|
| Units | 400 synthetic trajectories — 200 infant, 200 child, magnitude matched |
| Conditions × repeats | 6 × 5 |
| Executions | 38 (`dry-run`) |
| `dry-run` unit-executions | 8,000 |
| Metered LLM requests | **6,000** = 6 × 5 × 200 units per band |


```yaml
# configs/e09-age-norm/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e09-age-norm
  description: "E9: at matched crossing magnitude, does the screen apply the age-dependent developmental baseline"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e09-age-norm
  output_dir: /secure/results/gcl/e09-age-norm
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [age_band, sex]
    allocation: between
    assign:
      age_band: {method: by_attribute}

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_physiology
    physiology: concerning
    schedule: typical
    crossing_channels: 1.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.crossing_channels: 1.0}
  groups:
    - {by: age_band, levels: [infant, child]}
  grid:
    stimulus.crossing_channels: [2.0, 3.0]

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per cell; crossing magnitude is matched across bands by construction, so the band difference is the whole finding."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: band_at_2ch, of: "age_band=child__crossing_channels=2.0",
       against: "age_band=infant__crossing_channels=2.0"}
    - {id: band_at_3ch, of: "age_band=child__crossing_channels=3.0",
       against: "age_band=infant__crossing_channels=3.0"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses:
  - id: h1
    kind: confirmatory
    statement: "At a two-channel crossing the screen flags children more often than infants."
    metric: step03_screen.flag_rate
    compare: {contrast: band_at_2ch}
    direction: greater
    threshold: 0.10
    evaluate_on: ci95_lower
```


### E10 — cross-model generalization

**The problem.** Findings from one architecture are untrustworthy in this domain specifically, so E10 replicates the core arms across a model roster. Where budget constrains, the plan prioritizes E7 and E5b; this config is the E7 replication, and the E5b one is the same edit applied to that file.

**The design decision.** Provider and deployment must move **together** — a deployment name is meaningless under the wrong provider, and their product would demand an Anthropic key for an Azure deployment — so they are one `sweep.paired` axis of four rows, crossed with the 2 × 2. That composition is also what makes the credential check useful: `validate` demands the union over the conditions the sweep resolves, which is three variables here and nothing for the local arm, reported per condition and by name.

**The roster is swept by deployment name, and a name with a slash in it would be refused.** A swept value must render `[A-Za-z0-9._+-]+`, so `gpt-4.1-2026-04-14` and `claude-opus-5` are fine and a fully-qualified resource path is not; a study whose deployments are addressed by path sweeps an alias and resolves it in the step.

**Per-model reliance indices and the heterogeneity test across them are refusals** — each index is already an interaction, and testing whether four of them differ is one level further out. Both are `summary`-step `Estimate`s. What core computes is every cell and every declared contrast, per model, which is the input those two need.

**One config is not the whole of E10.** Replicating E4b, E5b, E8 and E9 across the same four deployments is the same `sweep.paired` block pasted into each of those files, and the cost is in the [summary](#cost-and-execution-summary).


| | |
|---|---|
| Units | 200 shared scaffolds |
| Conditions × repeats | 16 × 5 |
| Executions | 98 (`dry-run`) — `validate` checks 16 × 5 = 80 against `limits.max_executions: 500` |
| `dry-run` unit-executions | 19,600 |
| Metered LLM requests | **16,000** = 16 × 5 × 200 |


```yaml
# configs/e10-cross-model-2x2/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e10-cross-model-2x2
  description: "E10: the E7 2×2 replicated across the model roster"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e10-cross-model-2x2
  output_dir: /secure/results/gcl/e10-cross-model-2x2
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, age_band]
    allocation: within

parameters:
  llm:
    provider: azure_openai
    deployment: gpt-4.1-2026-04-14
    temperature: 0.0
    max_output_tokens: 512
    request_timeout_s: 120
    backoff_secs: [2, 8, 30]
  prompt:
    id: screen_v1
  serialize:
    features: derived
    format: markdown_table
    encoding: decimal
    order: chronological
    permutation: 0
    reference_frame: cdc2000
    visit_cap: null
    state_visit_count: false
  stimulus:
    source: synthetic_physiology
    physiology: healthy
    schedule: sparse
    crossing_channels: 2.0
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.physiology: healthy}
  grid:
    stimulus.physiology: [concerning]
    stimulus.schedule: [sparse, dense]
  paired:
    - {llm.provider: azure_openai, llm.deployment: gpt-4.1-2026-04-14}
    - {llm.provider: azure_openai, llm.deployment: gpt-5.1-2026-02-20}
    - {llm.provider: anthropic, llm.deployment: claude-opus-5}
    - {llm.provider: ollama, llm.deployment: llama-4-70b}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Four deployments crossed with the 2×2; provider and deployment move together, so they are one axis and not a product."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: utilization_gpt41, of: "schedule=dense__provider=azure_openai__deployment=gpt-4.1-2026-04-14__baseline",
       against: "schedule=sparse__provider=azure_openai__deployment=gpt-4.1-2026-04-14__baseline"}

limits:
  max_executions: 500
  max_failed_fraction: 0.2
  max_ineligible_fraction: 0.5
  min_units_per_cell: 20
  min_clusters: 10
  min_reported_n: 10

hypotheses: []
```

---

## What is not an experiment

Four things in the plan look like pipelines and are not. Treating any of them as a run is the failure mode this section exists to catch.

**The clinician adjudication panel.** Two to three blinded pediatricians independently rating 200 plotted curves is not something core executes; it is how an input file comes to exist. The panel's output arrives as columns on the roster table — `clinician_concern`, per-rater ratings, the free-text rationale — covered by `input_manifest_hash` and re-verified after the run. E1 is a run *about* that file, not the panel itself. One consequence worth stating: the inter-clinician kappa the plan asks for alongside the clinician–label kappa is a second `aggregate` metric over the same table, not a second run.

**E1's decision rule, and E3's.** "If the kappa gap exceeds ~0.15, the primary ground truth becomes the clinician consensus label" is a **human decision made between runs**. Core makes it legible in both directions — the gap is a declared contrast with a hypothesis carrying the threshold, and the decision it produces is one parameter value in twelve downstream configs — but nothing about it is adaptive, and it must not be. A config that selected its own ground truth from an earlier run's result would be [an adaptive design](design-principles.md#what-core-does-not-promise), which core refuses on purpose.

**Cohort construction and implausible-value screening.** Daymont-style screening of erroneous heights runs *before* the roster exists, so it belongs to the extract rather than to any run. The plan's OI-7 notes that no section owns it; in `publishable` terms the answer is structural rather than editorial — it is upstream of `input_dir`, and the hash of what it produced is what a run records.

**Preregistration of the reference frame.** CDC 2000 versus WHO 2006 is a commitment the plan says it has not yet made. It is a parameter, and a run cannot execute without a value for it — but choosing a value is not an experiment, and a cross-frame comparison is [a separate run rather than a robustness check](reference.md#three-hashes), since the frame changes what every z-score means.

---

## What core refuses, and the route for each

| Refused | Where the plan needs it | Route |
|---|---|---|
| Mixed-effects logistic regression | E3, E5 (all arms), E7, E8, E10 | `summary`-step `Estimate`, `reported: true` |
| Cochran's Q | E5a, E8 | `summary`-step `Estimate`; core gives the pairwise contrasts a significant Q would license |
| Conditional logistic regression | E4a | `summary`-step `Estimate`; the clustered flag-rate difference is what core computes |
| DeLong test on two AUROCs | E6 vs. E4a | `summary`-step `Estimate` inside a [`study`](reference.md#studies-what-a-paper-reports), the two AUROCs living in different runs |
| Gradient-boosted tree as an inferential object | E6 | Not refused — it is a swept `model.kind`; only the comparison *between* its AUROC and the LLM's is |
| Factorial main effects and interactions | E3's format × derivation interaction, E7's index, E9's band × magnitude | `summary`-step `Estimate`. A contrast compares two conditions; anything comparing two contrasts is an interaction |
| An omnibus test across three or more conditions | E5a, E8 | Same route; core's unit of comparison is the pair |
| A p-value for a paired binary flip count (McNemar's) | E4b, E5b, E5d | Half-refused: the delta and its paired interval are computed, the p-value is not. `statistics.null_test` gives a permutation p-value where the shuffled attribute is a design axis, which is E4a and not these |
| Holm across a family spanning several runs | `{E5a–d}`, `{E10 model contrasts}` | No route inside core. See [the gaps](#gaps-this-analysis-found-in-the-specification) |
| An absolute-threshold hypothesis ("AUROC > 0.5") | E2, E6 | `summary`-step `Estimate` named by a hypothesis with no `compare` — which costs it a place in the correction family |
| A contrast inside a single-condition run | E5c | `summary`-step `Estimate`; `report_by` describes the strata but produces no difference between them |
| Power analysis | The plan's whole Power basis section | Record the target effect size and the resulting n as parameters, so the calculation is part of the pre-registered config rather than a paragraph |
| Counterbalancing a per-unit condition order | E5b and E5d's "randomized order" | `replication.order: randomized` shuffles *executions*, not per-unit sequences. A true crossover carries the sequence as a unit attribute and fits period terms in a `summary` step |
| Adaptive selection of ground truth or format | E1's and E3's decision rules | Not a route — a human decision between runs, by design |

The pattern across that table is worth naming, because it decides how the paper is assembled rather than how any one config is written: **core computes every quantity that is a mean or a difference of means over patients, and refuses every quantity that is a model fitted across them.** Every run in the table above except E1, E4b, E5b and E5d needs at least one `summary`-step `Estimate` — and whether those three counterfactual arms do depends on whether the paper reports McNemar's p-value beside the interval core computes. Each such number is one an author computed and core carried without claiming — which `run.yaml` marks `reported: true` and a hypothesis's verdict marks `verdict_rests_on: reported`. For a plan whose headline number is a ratio of two regression coefficients, that disclosure is the main thing adopting `publishable` changes about how the result is read.

---

## Gaps this analysis found in the specification

These are the deliverable's second output: places where a real plan pressed on the schema and something gave. Each was measured; the measurements are in the [next section](#executability-on-this-build).

**1. A `parameter_spec` path must have exactly two segments, and the third case crashes.** `"reference_frame"` and `"a.b.c"` both raise `ValueError: _parameters_block only supports two-segment dotted paths (head.leaf)` as an unhandled traceback out of `generate experiment`. [§ Templates](reference.md#templates-where-parameters-are-defined) says "There is no `dict` type: a mapping is what nesting the dotted path already expresses", which reads as permitting any depth, and no `E-` code covers the refusal. Either the constraint belongs in the `Param` documentation and the closed error registry, or the materializer belongs at arbitrary depth. The template written for this analysis renamed one parameter to work around it.

**2. A correction family cannot span runs, and two of the plan's four preregistered families do.** `{E5a–d}` covers four runs, because the four arms have four rosters and [a roster-changing variant is a different run](reference.md#where-units-come-from); `{E10 model contrasts}` covers five. `statistics.correction` is computed within one run's condition set, and [`study add`](reference.md#what-study-add-redacts) copies records without re-correcting across them. The gap is not that the arithmetic is hard — it is that a family declared in a paper has no representation anywhere in the record, so nothing can check that what was corrected is what was declared. This is the single largest expressive gap this plan exposes.

**3. A `sweep.baseline` that duplicates a `grid` cell is accepted silently.** Written the obvious way — `baseline: {stimulus.physiology: healthy}` beside `grid: {stimulus.physiology: [healthy, concerning], stimulus.schedule: [sparse, dense]}` — the E7 2 × 2 expands to **six** conditions, of which `00_schedule=sparse__baseline` and `02_physiology=healthy__schedule=sparse` hold the same parameters and the same units in two directories. `validate` reports no error and no warning. Core already refuses the group-axis form of exactly this shape (`E-SWEEP-LEVEL-DUPLICATE`, `E-SWEEP-BASELINE-GROUP`) under the heading [two identical measurements reported as two arms](experimental-designs.md#mistakes-core-prevents); the parameter-axis form is the same mistake and is unguarded. The working spelling — fix the axis under test, leave the stratifying axis free — is documented, but nothing points a reader at it from the failure.

**4. Retracted — `W-DATA-CLUSTER-UNDECLARED` firing on a declared reporting stratum is not a gap.** `true_count_band` and `visit_band` each hold three labels over 300 units and are named in `statistics.report_by`, and both draw the undeclared-cluster warning; that half is true and measured, in both `validate` runs and in row 1 below. What this entry got wrong is reading the firing as an omission. `_warn_undeclared_cluster`'s exclusions are documented — `reference.md` § Warnings core reports enumerates exactly four: an attribute a `sweep.groups` axis names or an `assign.from` reads, any `stratify_by`, and `statistics.null_test`'s `shuffle` — and `report_by` is deliberately not a fifth. The reason is in the function's own docstring: a run that reports by `site` while `site` really is a cluster wants both declarations, not silence, because a reporting stratum and a cluster identity are different facts about the same column and one can hold without the other. `true_count_band` and `visit_band` are not clusters here — no unit belongs to a correlated group by way of either — so both firings are the false positive the warning's own message already provides for ("ignore this if the units really are independent"), not evidence the exclusion list is short a name. A case for silencing `report_by` the way the other four are silenced would have to argue that a stratum can never also be a cluster, which is a design change against a documented decision, not a gap this analysis discovered.

**5. A fold level's `stratify_by` is a string; every other `stratify_by` is a list.** `data.units.holdout.stratify_by` and `data.units.assign.<axis>.stratify_by` are lists in [§ The one config file](reference.md#the-one-config-file); a `{kind: fold}` level's is a string, and `[visit_decile]` earns `E-REPL-FOLD-STRATIFY-UNKNOWN`. The `replication` block in that section shows only `{kind: seed, n: 5}`, and [§ Repeat kinds](reference.md#repeat-kinds) names the field without giving its type, so the difference is discoverable only by running into it.

**6. `data.units.measurements` is out of reach of a resolver-supplied roster, and its `collapse` is not per-column by default.** `{by: calc_id, collapse: mean}` over a resolver roster earns `E-RESOLVER-MEASUREMENT-FIELD` — the resolver must yield one `Unit` per measurement — and the same declaration then applies `mean` to the string-valued attributes, earning two `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`. Both diagnostics are good; what the config schema's one-line comment does not say is that `collapse` is applied to **every** carried column rather than to the numeric ones, which is what makes the per-column map the ordinary case rather than the exception.

**7. There is no absolute-threshold hypothesis.** `compare` names both sides, so a claim against a fixed reference — chance for an AUROC, zero for a difference already computed elsewhere, a regulatory floor — has no form except a `summary`-step `Estimate`, which is outside the correction family and marked `reported: true`. For diagnostic-accuracy work, where 0.5 is a real reference rather than an arbitrary constant, that is a routine claim taking the exceptional route.

**One gap belongs to the source rather than to the specification, and it bounds this whole analysis.** OI-7 leaves the cohort, the variable derivations and the source cohort size undefined; OI-8 leaves the model roster and the prompt specification undefined. Every unit count in this document is therefore the plan's own stated sample size rather than something checked as drawable, and **no cost or runtime figure is given at all**, because there is no anchor the source itself observed — no roster, no prompt, and so no token count. The request counts below are exact; multiplying them by a price is not something this document can honestly do.


---

## Executability on this build

A claim about what the tool *does today* is perishable in a way a specification claim is not, so everything in this section is dated and pinned, and nothing outside it is a build claim.

### Measured on 2026-08-28 against commit `b0a6c9e`

**What was built to measure it.** A scratch experiment repository from `publishable new`, with the two project-local templates below written into `templates/`, one `src/growth_chart/` package holding six steps and two `BaseExperiment` subclasses, fifteen configs, and a `publishable-growth-chart` plugin from `publishable plugin new` installed as an editable dependency — registering one resolver, one probe, and one writer/reader pair, and **no** template. Each config's `input_dir` held a synthetic `index.csv` at the plan's stated unit count with the attributes the config declares. Every command was run through the project's own console script.

**Row 1 — the fifteen configs, measured by running `publishable validate` on each.**

| Config | Result |
|---|---|
| `e01-reference-gate` | ✓ valid |
| `e02-utilization-baseline` | ✓ valid |
| `e03-serialization` | ✓ valid |
| `e03b-tokenization` | ✓ valid |
| `e04a-matched-pairs` | ✓ valid |
| `e04b-physiology-swap` | ✓ valid |
| `e05a-schedule-density` | ✓ valid |
| `e05b-flat-negative` | ✓ valid |
| `e05c-fixed-n` | 0 errors, 1 warning — `W-DATA-CLUSTER-UNDECLARED` on `true_count_band` |
| `e05d-framing` | ✓ valid |
| `e06-comparator` | ✓ valid |
| `e07-two-by-two` | ✓ valid |
| `e08-ordering` | 0 errors, 1 warning — `W-DATA-CLUSTER-UNDECLARED` on `visit_band` |
| `e09-age-norm` | ✓ valid |
| `e10-cross-model-2x2` | ✓ valid |

Thirteen clean, two carrying one warning each and no errors. **Zero of the fifteen were refused.**

**Row 2 — `publishable dry-run` on each, which is where every execution count in this document comes from.** It expanded the sweep, built the input manifest, probed the apparatus, and printed the step directories and the unit-execution count. The counts are quoted per experiment above and totalled below; each is the number the command printed, not one derived from it.

**Row 3 — the plugin's three registries dispatched.** The reusable request step named in [§ Where the shared machinery lives](#where-the-shared-machinery-lives) is proposed there and was not written, so nothing in this row is a claim about it. `data.units.from: {resolver: growth_trajectory}` resolved every roster at `validate`; `apparatus_probe = "growth_llm_deployment"` was called at `dry-run` and its facts recorded per condition. The `.transcript.jsonl` writer/reader pair was registered and its entry points resolved at install, and **it was not exercised by a write**, because nothing here executed a step — the suffix-dispatch rule it relies on is [measured in the tutorial](tutorial-writing-a-plugin.md) rather than here.

**Row 4 — the credential check, measured on E10 before `.env` existed.** `validate` reported, per condition and by name:

```
error   E-CRED-PARAM-MISSING parameters.llm.provider
        is `azure_openai` in condition `schedule=sparse__provider=azure_openai__deployment=gpt-4.1-2026-04-14__baseline`,
        which requires `AZURE_OPENAI_API_KEY` — no value in the environment or in `.env`
error   E-CRED-PARAM-MISSING parameters.llm.provider
        is `anthropic` in condition `schedule=sparse__provider=anthropic__deployment=claude-opus-5__baseline`,
        which requires `ANTHROPIC_API_KEY` — no value in the environment or in `.env`
```

Three variables demanded across the four deployments, and nothing demanded for the `ollama` arm whose `requires_env` entry is `[]`. With a `.env` supplying them, all four conditions passed.

**Row 5 — the apparatus probe's unanswered facts, measured on E10 at `dry-run`.** The local arm's probe returns `None` for both declared facts, and core reported it rather than failing:

```
condition `03_schedule=sparse__provider=ollama__deployment=llama-4-70b__baseline`'s fact
`model_version` came back `null` on 1 of 1 probes
```

**Row 6 — four refusals probed deliberately**, each by editing one line and re-running `validate`:

| Probe | Result |
|---|---|
| `sweep.grid` on a `list`-typed parameter — `llm.backoff_secs: [[2, 8, 30], [5, 20, 60]]` | `E-SWEEP-VALUE-UNNAMEABLE` × 2: *swept value '[2, 8, 30]' does not match `^[A-Za-z0-9._+-]+$`* |
| A contrast naming the baseline by its swept value rather than `baseline` | `E-STATS-CONTRAST-UNKNOWN`, naming the label that matched no condition |
| `{kind: fold, k: 5, stratify_by: [visit_decile]}` | `E-REPL-FOLD-STRATIFY-UNKNOWN`: *a fold balances its folds on one declared attribute, named as a string* |
| `data.units.measurements: {by: calc_id, collapse: mean}` over a resolver roster | `E-RESOLVER-MEASUREMENT-FIELD` plus two `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` |

**Row 7 — two things that are *not* refused, and both were checked by running.** A second config naming the first's `entrypoint` validates, which is what makes one `src/` package across fifteen configs the recommended layout rather than a hope. And a `sweep.baseline` duplicating a `grid` cell validates clean while expanding to six conditions where four were meant — [gap 3](#gaps-this-analysis-found-in-the-specification), found this way and not by reading.

**Row 8 — one unhandled crash.** `publishable generate experiment` against a template declaring a one-segment or three-segment `parameter_spec` path exits `1` with a Python traceback rather than a diagnostic: `ValueError: _parameters_block only supports two-segment dotted paths (head.leaf); got 'reference_frame'`. [Gap 1](#gaps-this-analysis-found-in-the-specification).

**What was not measured, and is therefore written as specification rather than as fact.** Nothing here executed a step, so no `run`, `draft`, `resume`, `report`, `freeze`, `diff`, `study` or `reproduce` claim in this document is a build claim: the statistics routing table, the `Estimate` shape, `io.reuse_from`, the apparatus gate's *failure* on a moved fact, and every interval this analysis attributes to core are read from the specification. Executing them needs a real deployment, a real cohort, and the two open items the plan itself names.

### The two templates, as loaded

Both were read by `list-templates`, materialized by `generate experiment`, and enforced by `validate` at the commit above.

```python
# templates/growth_screen.py
# templates/growth_screen.py — the LLM screening experiment type, discovered by path
from publishable import BaseTemplate, Param, register_template


@register_template("growth_screen")
class GrowthScreenTemplate(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention = "clinical"
    default_repeats = 3
    version = "0.1.0"
    required_env = []
    apparatus_probe = "growth_llm_deployment"
    apparatus_facts = ["model_version", "system_fingerprint"]

    parameter_spec = {
        # --- the apparatus being measured through ---
        "llm.provider": Param(
            str, default="azure_openai",
            choices=["azure_openai", "openai", "anthropic", "ollama"],
            requires_env={
                "azure_openai": ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"],
                "openai": ["OPENAI_API_KEY"],
                "anthropic": ["ANTHROPIC_API_KEY"],
                "ollama": [],
            },
            help="Which deployment the request step authenticates to"),
        "llm.deployment": Param(
            str, pattern=r"^[A-Za-z0-9._+-]+$",
            help="REQUIRED. Deployment name; sweepable, so it may carry no slash"),
        "llm.temperature": Param(float, default=0.0, ge=0.0, le=2.0),
        "llm.max_output_tokens": Param(int, default=512, ge=1),
        "llm.request_timeout_s": Param(int, default=120, ge=1),
        "llm.backoff_secs": Param(list, item_type=int, default=[2, 8, 30],
                                  help="Retry schedule; its length is the attempt budget"),
        # --- the stimulus ---
        "prompt.id": Param(str, default="screen_v1",
                           choices=["screen_v1", "screen_v1_cot", "arith_probe_v1"],
                           help="Names src/growth_chart/prompts/<id>.md, inside code_hash"),
        "serialize.features": Param(str, default="derived",
                                    choices=["raw", "derived", "raw_plus_derived"]),
        "serialize.format": Param(str, default="markdown_table",
                                  choices=["markdown_table", "sentences", "digit_string"]),
        "serialize.encoding": Param(str, default="decimal",
                                    choices=["decimal", "place_annotated"]),
        "serialize.order": Param(str, default="chronological",
                                 choices=["chronological", "reverse", "shuffled"]),
        "serialize.permutation": Param(int, default=0, ge=0, le=4,
                                       help="Which of the five fixed shuffles; ignored unless order is shuffled"),
        "serialize.reference_frame": Param(str, default="cdc2000", choices=["cdc2000", "who2006"]),
        "serialize.visit_cap": Param(int, default=None, nullable=True, ge=1,
                                     help="Display at most this many visits; null shows all"),
        "serialize.state_visit_count": Param(bool, default=False,
                                             help="Prepend an explicit visit-count sentence"),
        # --- what the roster is made to look like ---
        "stimulus.source": Param(str, default="observed",
                                 choices=["observed", "synthetic_physiology",
                                          "synthetic_schedule", "synthetic_flat"]),
        "stimulus.physiology": Param(str, default="as_recorded",
                                     choices=["as_recorded", "concerning", "healthy", "flat"]),
        "stimulus.schedule": Param(str, default="as_recorded",
                                   choices=["as_recorded", "sparse", "typical", "dense"]),
        "stimulus.crossing_channels": Param(float, default=2.0, ge=0.0, le=5.0),
        # --- ground truth and scoring ---
        "truth.label_source": Param(str, default="clinician_consensus",
                                    choices=["growth_dx_flag", "clinician_consensus", "by_construction"]),
        "scoring.parse_failure": Param(str, default="ineligible",
                                       choices=["ineligible", "failed", "negative"]),
    }

    def validate(self, config) -> list[str]:
        errs = []
        params = config.get("parameters") or {}
        stim = params.get("stimulus") or {}
        truth = params.get("truth") or {}
        ser = params.get("serialize") or {}
        swept = set()
        sweep = config.get("sweep") or {}
        for key in ("grid",):
            swept |= set((sweep.get(key) or {}).keys())
        for entry in (sweep.get("paired") or []):
            swept |= set(entry.keys())
        swept |= set((sweep.get("baseline") or {}).keys())
        # A synthetic arm carries no EHR diagnosis, so its truth is by construction.
        if stim.get("source", "observed") != "observed" and \
                truth.get("label_source") not in ("by_construction", None) and \
                "truth.label_source" not in swept:
            errs.append("a synthetic `stimulus.source` has no EHR label: "
                        "`truth.label_source` must be `by_construction`")
        # A shuffled order without a declared permutation is one shuffle pretending to be five.
        if ser.get("order") == "shuffled" and "serialize.permutation" not in swept and \
                "serialize.order" not in swept:
            errs.append("`serialize.order: shuffled` needs `serialize.permutation` swept, "
                        "or the run measures one arbitrary shuffle")
        return errs

    def aggregate(self, units, cfg) -> dict:
        rows = [r for r in units if r.get("flagged") is not None and r.get("truth") is not None]
        if not rows:
            return {}
        n = len(rows)
        tp = sum(1 for r in rows if r["flagged"] and r["truth"])
        fp = sum(1 for r in rows if r["flagged"] and not r["truth"])
        fn = sum(1 for r in rows if not r["flagged"] and r["truth"])
        tn = n - tp - fp - fn
        po = (tp + tn) / n
        pf = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)
        return {
            "flag_rate": (tp + fp) / n,
            "accuracy": po,
            "kappa": (po - pf) / (1 - pf) if pf < 1 else None,
            "sensitivity": tp / (tp + fn) if (tp + fn) else None,
            "false_positive_rate": fp / (fp + tn) if (fp + tn) else None,
        }
```

```python
# templates/growth_label.py
# templates/growth_label.py — the non-LLM half: label validity and tabular comparators
from publishable import BaseTemplate, Param, register_template


@register_template("growth_label")
class GrowthLabelTemplate(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    field_convention = "generic"
    default_repeats = 1
    version = "0.1.0"
    required_env = []

    parameter_spec = {
        "model.kind": Param(str, default="agreement",
                            choices=["agreement", "logistic", "gbt"],
                            help="`agreement` computes kappa only and fits nothing"),
        "model.feature_set": Param(
            str, default="count_only",
            choices=["count_only", "count_spacing_span", "llm_matched", "llm_matched_minus_count"],
            help="Named feature set; a swept value must render [A-Za-z0-9._+-]+, so it is a name and not a list"),
        "model.max_depth": Param(int, default=3, ge=1, le=12,
                                 help="gbt only; ignored by the other two"),
        "truth.label_source": Param(str, default="growth_dx_flag",
                                    choices=["growth_dx_flag", "clinician_consensus"]),
        "truth.rater": Param(str, default="consensus",
                             choices=["consensus", "rater_a", "rater_b", "rater_c"]),
        "frame.reference": Param(str, default="cdc2000", choices=["cdc2000", "who2006"]),
    }

    def validate(self, config) -> list[str]:
        params = config.get("parameters") or {}
        kinds = {(params.get("model") or {}).get("kind", "agreement")}
        sweep = config.get("sweep") or {}
        kinds |= set((sweep.get("grid") or {}).get("model.kind") or [])
        for entry in (sweep.get("paired") or []):
            if "model.kind" in entry:
                kinds.add(entry["model.kind"])
        if kinds - {"agreement"}:
            units = (config.get("data") or {}).get("units") or {}
            folds = [r for r in ((config.get("replication") or {}).get("repeats") or [])
                     if r.get("kind") == "fold"]
            if not units.get("holdout") and not folds:
                return ["this experiment type fits a model, so it needs a "
                        "`data.units.holdout` or a `{kind: fold}` repeat to fit on"]
        return []

    def aggregate(self, units, cfg) -> dict:
        rows = [r for r in units if r.get("score") is not None and r.get("truth") is not None]
        if not rows:
            return {}
        pos = [r["score"] for r in rows if r["truth"]]
        neg = [r["score"] for r in rows if not r["truth"]]
        if not pos or not neg:
            return {}
        wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
        return {"auroc": wins / (len(pos) * len(neg))}
```

---

## Cost and execution summary

| Run | Units | Conditions | Repeats | Executions | Metered requests |
|---|---|---|---|---|---|
| E1 `e01-reference-gate` | 200 | 3 | 1 | 5 | 0 |
| E2 `e02-utilization-baseline` | 1,000 | 2 | 5 folds | 12 | 0 |
| E3 `e03-serialization` | 200 | 9 | 5 | 56 | 9,000 |
| E3b `e03b-tokenization` | 150 | 2 | 5 | 14 | 1,500 |
| E4a `e04a-matched-pairs` | 600 | 2 | 5 | 14 | 3,000 |
| E4b `e04b-physiology-swap` | 250 | 2 | 5 | 14 | 2,500 |
| E5a `e05a-schedule-density` | 200 | 3 | 5 | 20 | 3,000 |
| E5b `e05b-flat-negative` | 200 | 2 | 5 | 14 | 2,000 |
| E5c `e05c-fixed-n` | 300 | 1 | 5 | 8 | 1,500 |
| E5d `e05d-framing` | 300 | 2 | 5 | 14 | 3,000 |
| E6 `e06-comparator` | 600 | 4 | 5 folds | 22 | 0 |
| E7 `e07-two-by-two` | 200 | 4 | 5 | 26 | 4,000 |
| E8 `e08-ordering` | 300 | 7 | 5 | 44 | 10,500 |
| E9 `e09-age-norm` | 400 | 6 | 5 | 38 | 6,000 |
| E10 `e10-cross-model-2x2` | 200 | 16 | 5 | 98 | 16,000 |
| **Total** | | **65** | | **399** | **62,000** |

**Executions** are what `dry-run` printed, counting every step's executions including the `run`-scoped roster summary and the `summary`-scoped comparison. **Metered requests** are conditions × repeats × units at the one `scope = "repeat"` step that issues a request — 62,000 across the fifteen, against a plan whose own evaluation counts for the arms it costs (9,000 for E3, 4,000 for E7, 10,500 for E8) this reproduces exactly.

**No condition set comes near `limits.max_executions: 500`.** The largest is E10 at 16 × 5 = 80, and `validate` warned on none of the fifteen. That is worth noting because it inverts the usual worry: what constrains this plan is the request count inside each execution, not the number of executions, and core's execution-count guard is not the limit that will bind.

**The full E10 is four times what the table shows.** Replicating E4b, E5b, E8 and E9 across the same four-deployment axis adds 10,000 + 8,000 + 42,000 + 24,000 = 84,000 requests, for **146,000** in total. The plan's own budget rule — prioritize E7 and E5b — is therefore a choice between 62,000 and 146,000, which is the number that decision should be made against.

**What none of this says is what it costs.** There is no roster and no prompt specification in the source (OI-8), so there is no token count per request, and a price per request would be invented rather than measured. What is measured is that a request is issued once per patient per condition per repeat, that every one of them lands in the unit table with its own `prompt_tokens`, `completion_tokens` and `latency_ms`, and that the first run to execute will therefore produce the anchor this section currently lacks.

# Feasibility analysis: growth chart literacy

`growth-chart-literacy` asks one question: **when a language model screens a pediatric growth trajectory, is it reading the curve, or is it counting how often the child came in?** Ten experiments answer it around a triad no published study combines — clinician-validated stimuli, a physiology-preserving counterfactual, and a utilization-invariance counterfactual.

**Read against the plan at commit `e6b43ab`, which restructured it on 2026-08-30.** The plan now sits in three layers: a **counterfactual core** whose claims are within-subject and read no EHR label at all, a **clinician panel** validating the constructed stimuli, and a secondary **accuracy layer** on a referral outcome that is positive-unlabeled. Every trajectory is drawn from age 2 onward. This analysis is re-derived against that plan rather than patched onto the earlier reading, and where a conclusion here changed, the section says what it replaced — an earlier version of this document is in its git history.

This document does not reproduce that plan. It asks a narrower question: **which of its ten experiments `publishable`'s vocabulary expresses, what each config actually is, how fourteen runs share one directory, where the machinery every run needs lives, what it costs to execute, and which parts core refuses.** The refusals are the load-bearing half — a feasibility analysis that only lists what fits is an advertisement.

This document is non-normative and carries its own examples. It is **not** part of the shared worked example (`cohort-pilot`); see `CLAUDE.md` § Feasibility analyses. It is the second such analysis; the first, [`feasibility-llm-growth-studies.md`](feasibility-llm-growth-studies.md), read two adjacent repositories, and where a conclusion here differs from one there, the difference is re-derived rather than inherited.

## Contents

- [What the plan hand-rolls, and what core already owns](#what-the-plan-hand-rolls-and-what-core-already-owns)
- [One repository, fourteen configs](#one-repository-fourteen-configs)
- [Where the shared machinery lives](#where-the-shared-machinery-lives)
- [The stimulus arm has to be constructed somewhere](#the-stimulus-arm-has-to-be-constructed-somewhere)
- [LLM API access](#llm-api-access)
- [Prompt templates, and why they are code](#prompt-templates-and-why-they-are-code)
- [Two templates, because there are two experiment types](#two-templates-because-there-are-two-experiment-types)
- [Where every statistical procedure lands](#where-every-statistical-procedure-lands)
- [The fourteen configs](#the-fourteen-configs)
- [What is not an experiment](#what-is-not-an-experiment)
- [What core refuses, and the route for each](#what-core-refuses-and-the-route-for-each)
- [Gaps this analysis found in the specification](#gaps-this-analysis-found-in-the-specification)
- [Executability on this build](#executability-on-this-build)
- [Cost and execution summary](#cost-and-execution-summary)

---

## What the plan hand-rolls, and what core already owns

The plan is at plan stage — nothing has been run — so this table is not a list of code to delete. It is the list of machinery the plan **commits to building** in prose, and would not have to. It is also the list of things the proposed plugin must **not** rebuild.

**Two rows below record a convergence rather than a gap, and they are the most useful rows in the table.** On the utilization covariate and on what repeated runs buy, the plan reached this tool's position on its own, from its own data, between the first version of this analysis and the restructure of 2026-08-30. A feasibility analysis whose predictions the subject project independently confirms is stronger evidence than one that only lists what fits.

| Committed to in the plan | Core equivalent |
|---|---|
| The reference frame, now **settled** at CDC 2000 because the age floor determines it, and registered anyway "precisely because Ahmad et al. show how much rides on it" | A `Param` with `choices=["cdc2000", "who2006"]`, inside [`parameters_hash`](reference.md#three-hashes). The plan's own reason for registering a settled choice is core's reason for keeping it a parameter: the frame follows from the age floor, so **lowering the floor must not change the frame as a side effect** — and a config in which both are declared cannot move one silently |
| "Eight pre-data commitments alter downstream design and must be registered before data collection" (§Preregistration) | [`hypotheses`](reference.md#pre-registration), each carrying the declaring config's `parameters_hash`, so anything added after the run renders as exploratory |
| "Holm-Bonferroni within each experiment family", with four families now declared and their `m` stated — 3, 4, 3, and the roster size — and **every other arm in no family at all** | [`statistics.correction: holm`](reference.md#sweeps-and-repeats), with the family size and its breakout recorded beside every interval. Two mismatches, both now measured: a family **cannot span runs**, which {E5a–d} needs, and core's family is *comparisons × metrics within one run*, which is a different and usually larger object than the plan's `m`. Declaring `correction: none` is how a config says "no family" and it earns a warning for saying it; see [the gaps](#gaps-this-analysis-found-in-the-specification) |
| "Bootstrapped CIs … resampled at the patient level, not the observation level" | [`statistics.resample`](reference.md#what-isnt-a-repeat) over the per-unit table, where the unit *is* the patient by construction |
| **Retracted by the plan itself.** An earlier §Power basis credited the k = 5 repeated runs with raising effective power; it now says "the k = 5 repeated runs buy no power, and nothing here credits them with any" | Repeats never enter `n`. Five seeds give a [`repeat_spread`](reference.md#repeat-kinds), and `n` counts units. This analysis said so before the plan did, and the plan reached it from the other end — that repeats within a case are highly correlated and are *identical* on local weights at a fixed seed. **The rule and the reason now agree**, which is the strongest form this row could take |
| **Also retracted, and measured.** `visits_count_pre_dx` was the universal control; profiling found it truncates at the diagnosis for cases and equals the lifetime count for controls, running at AUROC 0.131 against 0.745. The plan replaced it with a **pre-index count on a matched index date** and says "the plan does not use this field" | A unit attribute either way: matched by [`cluster_by`](reference.md#clustered-units), stratified by [`report_by`](reference.md#reporting-strata), manipulated as a swept parameter — three spellings for the three things the plan does with it. What the tool never had was an opinion about *which* column; what it does have is [`input_manifest_hash`](reference.md#three-hashes) over the extract the column came from, so the replacement is legible in the record rather than in a methods paragraph |
| "Do not resolve an anchor with a bare `grep`" — `scripts/check_anchors.py`, a pre-commit hook, and a seven-lane coordination protocol over one Markdown file | Not core's job, and it stays the plan's. Worth naming because most of what it coordinates is *design* state that a config makes explicit and a `run.yaml` makes permanent |
| The model roster and prompt specification, now written (§Cross-Cutting): three Azure deployments differing in size, two to three local open-weight models, one fixed system and user message, and per-call provenance — deployment, model version, API version, `seed`, `system_fingerprint` | `parameters` and [`list-templates`](reference.md#operation-commands): the roster is a swept axis and the prompt is a parameter, so "enumerable from the text" becomes enumerable from the file that ran. The provenance the plan enumerates is split in two here on a rule the plan has no reason to have: what you *decide* is a `Param`, what you can only *observe* is an [apparatus fact](#llm-api-access), and a fingerprint that moves mid-study fails the run rather than being logged for someone to notice |
| Three labels kept apart by naming discipline — the referral outcome, the panel's `growth concern`, the model's `growth_issues` | One is an input, one never enters a run at all, and one is an output. The referral label is a unit attribute carried onto the [unit table](reference.md#the-unit-table-is-the-inference-base); `growth_issues` is a recorded column; the panel's verdict is neither, because the panel adjudicates constructed pictures rather than the cases a model sees. Which label a run reads is `truth.label_source`, a parameter — and its third value is `none`, which is what the five arms reporting only whether the model's own answer moved declare |
| "The generator's parameters and its verification tolerances" as preregistration item 8, with the distributional check specified in prose (§Cross-Cutting) | Not core's job and it stays the plan's — but the *pinning* is: the generator lives in `src/`, so [`code_hash`](reference.md#three-hashes) covers it, and a generator retuned after seeing how a model responded to it produces a different hash on the next run. "A generator tuned after seeing how a model responds to it is not a control" is a sentence the record can enforce |

The sharpest rows are the two marked *retracted*, and what makes them sharp is that **nobody had to be persuaded**. The plan's earlier Power basis credited the k = 5 repeats with raising effective power; core makes that claim unwritable, since an interval that narrows as seeds are added is [a mistake core prevents](experimental-designs.md#mistakes-core-prevents) by construction and the five draws surface as `repeat_spread` instead. The plan now says the same thing in its own words, having arrived from correlation between repeats rather than from a rule about what `n` counts. The utilization row is the same shape with data behind it: profiling the covariate found it running backwards, and the fix — one index date, both arms, count anchored on it — is the fix a tool that hashes its inputs makes legible and a methods paragraph does not.

---

## One repository, fourteen configs

The ten experiments split into **fourteen runs**, and the count is derived rather than inherited. A sub-experiment that changes the roster is a different run: E3 and E3b draw different constructed sets, and E5's four arms have four rosters. **E1 is not a run at all** — the restructure of 2026-08-30 turned it from a 200-curve label adjudication into a panel of two to three clinicians reading roughly 110 plotted curves, and a human reading a picture is not a pipeline core executes; it moves to [What is not an experiment](#what-is-not-an-experiment). Fifteen minus one is the arithmetic, but the substance is that **the only arm this vocabulary lost is the one that was never executable in it.**

```
growth-chart-literacy/                    # the experiment repository
├── configs/
│   ├── e02-utilization-baseline/config.yaml
│   ├── e03-serialization/config.yaml
│   ├── …                                 # fourteen, one per run
│   └── e10-cross-model-2x2/config.yaml
├── src/
│   └── growth_chart/                     # ONE package, two pipelines
│       ├── experiment.py                 # ScreenExperiment, LabelExperiment
│       ├── prompts/                      # screen_v1.md, screen_v1_cot.md, arith_probe_v1.md
│       ├── construct.py                   # the stimulus arm, applied to a trajectory
│       ├── serialize.py                  # the nine E3 serializations
│       └── steps/
│           ├── step01_summarize_units.py     scope = "run"
│           ├── step02_construct.py           scope = "condition"   ← the swept stimulus
│           ├── step02_serialize.py           scope = "condition"
│           ├── step03_screen.py              scope = "repeat"      ← the metered step
│           ├── step04_compare.py             scope = "summary"
│           ├── step02_score.py               scope = "repeat"      ← the tabular pipeline
│           └── step03_compare.py             scope = "summary"
├── templates/
│   ├── growth_screen.py                  # the twelve LLM runs
│   └── growth_label.py                   # E2 and E6 — no LLM in them at all
├── tests/
└── pyproject.toml                        # publishable, publishable-growth-chart
```

**Fourteen configs, one `src/` package, two entrypoints.** `generate experiment` writes a package per experiment, which is right for fourteen *different* pipelines and wrong here: E3 through E10 run the same four steps and differ only in parameters. So the second config onward has its `entrypoint` line pointed at the first one's class — an ordinary hand-edit of a [freely editable file](reference.md#the-one-config-file) — and `validate` accepts it, which is [measured below](#executability-on-this-build). What that buys is the claim the whole sequence rests on: **identical `code_hash`, differing `parameters_hash`**, which is [same code, different parameters](design-principles.md#same-code-different-parameters) stated by the record rather than by the methods section.

**One repository is the right seam here, and it is the opposite conclusion from the previous analysis'** — which split two projects across three repositories. The reason is a property of *this* plan rather than a change of taste. Its dependency structure makes E4 through E10 evaluate one frozen screening pipeline over weeks; their reviewer-facing claim is that nothing about the code moved between E4 and E10. `code_hash` covers `src/**` and `templates/**`, so that claim is provable exactly when they share a tree, and a split would give each run a hash of its own with nothing to compare.

**What one repository costs is real, and it is E2 and E6.** Those two fit scikit-learn models and import no LLM machinery, so every commit to their code moves the recorded `code_hash` of screening runs that never called it — and while E2's or E6's code has uncommitted edits, [`run` refuses to start](reference.md#operation-commands) the twelve-hour E10. Three ways out, with the bill attached to each:

| Option | What it costs |
|---|---|
| One repository, E2/E6 code frozen before E4 starts | The discipline is a human commitment again — exactly the kind of thing this tool exists to stop relying on |
| One repository, `draft` for E2/E6 iteration | [`draft`](reference.md#draft-runs) permits a dirty tree and marks the run non-citable, which is right for developing a comparator and wrong for the comparator run that goes in the paper |
| A second repository for E2 and E6 | Their `code_hash` is then unrelated to the screening runs', which is honest — they measure a different apparatus — but E6's comparison against E4a's LLM becomes a cross-repository [`study`](reference.md#studies-what-a-paper-reports) rather than a contrast |

**The default is the first, and the tree above is drawn that way** — one repository, fourteen configs — because the cost only becomes real if E2 and E6 are still being written while E4 through E10 are executing. **The trigger for taking the third is stated rather than judged**: the first time a comparator commit would move the `code_hash` of a screening run already reported, or block one from starting, E2 and E6 move to a repository of their own. The plan's own OI-12 argues they belong there anyway — it says E6 is a utility comparator and not an ablation of the LLM, and a comparator sharing no code with the thing it is compared against is the accurate expression of that. **What has changed is which arms carry the risk.** Under the earlier plan E1's clinician labels were the ground truth every screening run consumed, so the label pipeline was upstream of everything; now E2 and E6 are Layer C, secondary, and *nothing in the counterfactual core reads what they produce*. A repository split would therefore cost less than it used to and buy the same thing, which strengthens rather than weakens the trigger above.

**Nothing in these fourteen runs crosses a seam through `reuse_from`.** The sequence looks like lineage and is not. The panel's verdict on the stimuli reaches E4b, E5b and E9 as a **decision to regenerate or not** — no column, no artifact, a gate a person passes — and E3's format decision reaches the downstream arms as a **parameter value a person typed**. Neither is an artifact, so [`provenance.upstream`](reference.md#lineage-between-runs) is `[]` for all of them, and the one place `io.reuse_from` genuinely belongs is E7 and E10 consuming the synthetic scaffolds E4b published from a `summary` step. That is worth stating rather than assuming: a chain of experiments is not a chain of runs.

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
    └── steps/request.py         transport, retry and per-unit cost, imported not
                                 registered — written 2026-08-28, see the dated
                                 entry in § Executability on this build
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

## The stimulus arm has to be constructed somewhere

`growth_screen` declares six parameters that describe **what trajectory the model is shown** rather than how it is rendered — `stimulus.source`, `stimulus.physiology`, `stimulus.schedule`, `stimulus.crossing_channels`, `stimulus.resample_noise` and `stimulus.height_availability` — and six of the fourteen configs sweep one or both of the first two as *the axis under test*: [E4b](#e4b--the-physiology-preserving-counterfactual), [E5a](#e5a--the-schedule-density-ladder), [E5b](#e5b--the-graded-negative-control), [E7](#e7--the-2--2-synthesis), [E9](#e9--age-dependent-norm-application) and [E10](#e10--cross-model-generalization).

**The last two are E5a's constraints, and they are parameters because the plan made them requirements.** "Holding the growth signal fixed" is a claim about the latent curve; the plan states three conditions under which it is also true of the *displayed evidence* — deviation-preserving, noise-matched, availability-matched — and each has a reader. `resample_noise` decides whether interpolated points come back carrying measurement error at the within-child SD, so that a dense arm cannot be identified by being smoother than a sparse one. `height_availability` holds the share of displayed visits carrying a height at the cohort's 53.8% in every arm, so that densifying a schedule does not also make the record more complete. **Deviation-preserving is not a parameter**, and the asymmetry is the interesting part: the visits across which a crossing becomes legible are retained in every density arm unconditionally, because an arm that could switch it off would be an arm whose sparse condition measures something else.

**Declaring them is not enough, and the failure mode if nothing reads them is silent.** A parameter that no step reads still validates, still expands the sweep, still labels the condition directories and still appears in `parameters_hash` — and every condition renders the identical trajectory. The run completes, the metrics compute, and the measured effect of the manipulation is approximately zero because the manipulation never happened. That is the rule [`design-principles.md` § Every declarable field has a reader](design-principles.md#every-declarable-field-has-a-reader) states, and which `CLAUDE.md` names from the other end as *an unread parameter is an unbuilt reader of a shipped surface*; it produces a confident null rather than an error.

So the construction is its own **`condition`-scoped step**, `step02_construct`, sitting between the roster summary and the serializer:

```
step01_summarize_units (run)  →  step02_construct (condition)  →  step02_serialize (condition)
     visits.json                     visits.json                      prompts.json
     truth.json                      truth.json
     features.json
```

Three decisions in that shape, each with a reason:

- **`condition` scope, because the stimulus *is* the condition.** The arm is what the sweep varies, so the trajectory differs across conditions and is identical across the repeats within one — a repeat is the deployment's nondeterminism, not the stimulus's. Constructing at `repeat` scope would rebuild the same trajectory five times and invite it to differ between them.
- **It publishes truth as well as visits**, which is the reason it is a step and not a helper inside the serializer. E4b sweeps physiology across two conditions on **one** real visit scaffold, so a unit is negative in the healthy arm and positive in the concerning one; `step01`'s `run`-scoped `truth.json` can hold only one answer per unit. A per-condition label has to come from something that executes per condition.
- **`source: observed` is a pass-through, not a skip.** Every downstream step reads `step02_construct` under every config, rather than branching on whether an arm was declared. A branch there would be a second reading of the same parameter, and two readings of one parameter eventually disagree.

**The two knobs apply independently, and `source` gates neither.** E7 and E10 sweep `physiology` while also fixing `schedule`, so a design where `source` selected which single knob applied would leave the other unread again — the original defect, one layer down. `schedule` decides *when* the visits happen (`as_recorded` keeps the real ages; a density resamples the same observation window), `physiology` decides *what the curve does* over them, and `source` says only whether construction happens at all and that the label is now by construction.

**Determinism comes from the unit key, never from `self.rng`.** A synthetic trajectory must be identical across a condition's repeats and across a `reproduce` of the whole study, so the per-unit offset is a SHA-256 of the key rather than a draw — Python salts `hash()` per process, which would make a trajectory differ between a run and its reproduction, the one thing a fixed stimulus may never do.

**The z path is the plan's own generator, not this analysis's invention, and that changed on 2026-08-30.** §Cross-Cutting now specifies `z(a) = b + d(a) + e(a)`: a characteristic channel `b ~ N(0, 0.84²)`, a deviation `d(a)` entered over a window rather than as a step, and within-child variation `e(a)` as an AR(1) process at marginal SD 0.49, calibrated so that the pooled lag-1 autocorrelation reproduces the cohort's measured 0.869. All three are measured quantities, and the pooled figure is the load-bearing one because it mixes both variance components and so cannot be matched by tuning either alone. Two consequences for a translation:

- **The verification the plan pre-specifies is a test, not a run.** "Simulated and real trajectories must match on the three statistics within 10%" is a property of the generator, checked before any arm using synthetic stimuli executes. It has no conditions, no repeats and no units, so it is a function in `src/` with a test beside it — and being in `src/` is what puts it inside `code_hash`, which is the part that matters: preregistration item 8 says a generator tuned after seeing how a model responds to it is not a control, and a hash is what can catch that.
- **Rounding is part of realism, and it is the kind of thing only a specification catches.** Values are rounded to the source units — quarter inches and ounces — rather than to the converted metric fields, because a synthetic curve carrying three-decimal centimetres where real records carry quarter-inches is separable on rounding alone. The panel's adversarial check is what that would fail, and the panel is the only reader that would have noticed.

**What the arms are not.** The z-scores and percentiles the constructor emits are exact — a percentile is the normal CDF of the z it chose — and the variance structure is the plan's, but the kilograms and centimetres are still back-derived through a coarse piecewise-linear mean so the rendered table reads like a chart. They are internally consistent across the arms of a comparison, which is all any of these designs rests on. They are **not** a growth standard, and a design that needs real anthropometry needs LMS tables behind `serialize.reference_frame`, which is also why [`who2006` is declarable and refused](#gaps-this-analysis-found-in-the-specification) rather than silently served from CDC columns. **The age restriction narrowed this rather than removing it**: with everything at age 2 and above, the reference frame is CDC by the plan's own argument, so the missing piece is one table rather than a choice between two.

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

**Drift over time is a `batch` repeat, and it is available but not declared here.** All fourteen configs declare `{kind: seed, n: 5}`, matching the plan's k = 5. A study that wanted to separate *how much the deployment moved between blocks* from *how much the sampler moved within one* would declare `{kind: batch, n: 5}` outside it and read the two `repeat_spread` entries; the plan does not ask for that, and adding it would multiply every metered figure below by five.

---

## Prompt templates, and why they are code

**Prompt text lives at `src/growth_chart/prompts/<id>.md`, and the choice of prompt is a parameter naming it.**

**One file, two messages.** The plan fixes *"one system message and one user message per case, both fixed for the whole study and reproduced verbatim in the supplement"* — the system message stating the task, the reference frame and the output form, the user message carrying the serialized trajectory plus the child's sex and age at each point, and nothing else. So a prompt file carries both halves behind `<!-- system -->` and `<!-- user -->` markers, and the loader refuses a file that breaks the contract **at load rather than at first use**: a missing placeholder renders every unit's prompt identically, and a run that discovered that at analysis time would have paid for the whole sweep first. The sharpest of those refusals is a system half carrying a per-unit placeholder — a system message with a unit's sex in it is not *fixed for the study*, which is the property the supplement reproduces.

**One file rather than two, and the reason is what `prompt.id` is.** The pair is one preregistered object frozen together; two files can be edited apart, and a stem that resolved to two things would make "the prompt" ambiguous exactly where a reader needs it not to be.

```python
"prompt.id": Param(str, default="screen_v1",
                   choices=["screen_v1", "screen_v1_cot", "arith_probe_v1"],
                   help="Names src/growth_chart/prompts/<id>.md, inside code_hash"),
```

Three consequences, each deliberate:

- **Editing a prompt moves `code_hash`.** That is correct rather than inconvenient: a prompt change is a change in what produced the numbers, and a study whose prompt moved silently between E4 and E7 has no *same code, different parameters* claim left. It also means the prompts must be frozen at the same moment the pipeline is, which is what E3's decision rule already commits to.
- **The prompt cannot live in `input_dir`.** It would then be covered by `input_manifest_hash` instead — filed with the patient data as something measured rather than as something written — and [`diff`](reference.md#operation-commands) would report a prompt change as a change of dataset. Data and code [never share a repository](design-principles.md#code-and-data-never-share-a-repo), and the corollary is that code never hides in the data directory either.
- **Sweeping the prompt is sweeping an alias.** A swept value must render as `[A-Za-z0-9._+-]+`, which a path does not and a stem does — `E-SWEEP-VALUE-UNNAMEABLE` is what a config sweeping the text itself would earn, [measured below](#executability-on-this-build) on a list-valued parameter. The step resolves the stem to a file; the condition label stays `prompt_id=screen_v1_cot`, which is also what a figure legend needs.

**The child's sex is a prompt input, not a serializer column, and that is a design decision worth naming.** Every growth reference is sex-specific, so it belongs in the user message beside the trajectory rather than in a per-visit row — a property of the child, not of a visit. It reaches the step as a declared unit attribute, which means a config that does not declare `sex` has it [dropped before any step sees it](#gaps-this-analysis-found-in-the-specification); the step refuses rather than rendering around the gap, because a prompt missing it asks the model to read a curve against a reference it has not been given the index for, and the run would complete.

**The nine E3 serializations are not nine prompts.** They are two parameters — `serialize.features` and `serialize.format` — crossed by `sweep.grid`, with one renderer in `src/growth_chart/serialize.py` reading both. Writing them as nine prompt files would put the factorial structure inside a filename, where no `sweep` can see it and no contrast can name a main effect. The rule generalizes: **a prompt file per condition means the design has escaped the config.**

---

## Two templates, because there are two experiment types

E2 and E6 contain no LLM at all: they fit tabular comparators on the referral outcome. Their parameters share nothing with the screening runs' — no deployment, no serialization, no stimulus arm — so folding them into one `parameter_spec` would give every screening config a `model.max_depth` and every comparator config a `serialize.encoding`. Two project-local templates instead, `growth_screen` and `growth_label`, both discovered by path under `templates/`.

**`growth_label` lost a third of itself to the restructure, and the deletion is the point.** It used to declare a `model.kind: agreement` that fitted nothing and computed a kappa between the EHR label and a clinician rating, a `truth.rater` selecting which rater's column that was, and an `aggregate` deriving `kappa` and `agreement_raw` from the pair. E1 was the only reader of all four, and E1 is now a panel that never sees these units. **A parameter whose reader is gone is the defect this project keeps producing** ([`design-principles.md` § Every declarable field has a reader](design-principles.md#every-declarable-field-has-a-reader)), so they were removed rather than left declarable — and one second-order effect is worth naming, because it is the shape a check that cannot fail takes: `growth_label.validate` refuses a config that fits a model without a `holdout` or a `fold`, and that rule used to be *conditional* on the kind not being `agreement`. With `agreement` gone the condition is vacuous, so the rule is now unconditional and its test asserts the refusal directly.

Each carries a cross-block rule only a template can know. `growth_screen` refuses a synthetic stimulus arm whose ground truth still claims to come from the EHR — a constructed trajectory carries no referral, since no clinician ever acted on a child who does not exist — and refuses `serialize.order: shuffled` unless `serialize.permutation` is swept, because one arbitrary shuffle reported as *the* shuffled condition is E8's whole finding thrown away. `growth_label` is the specification's own example applied literally: a config that fits a model and declares neither a `holdout` nor a `fold` has nowhere to fit, so it is refused.

Both derive their metrics in `aggregate(units, cfg)` rather than returning them from a step, because that is [the only way a derived statistic gets a real interval](reference.md#templates-where-parameters-are-defined) — core can recompute it on a resampled table. `growth_label` derives `auroc`, and nothing else. `growth_screen` derives `flag_rate` always and `accuracy`, `kappa`, `sensitivity` and `false_positive_rate` **only where the table carries a truth column** — which is the restructure landing in code rather than a defensive guard. Five of the fourteen arms report whether the model's own answer *moved* under a controlled perturbation, a within-subject question with no correct answer to score against; deriving an accuracy there would need a label those arms deliberately do not carry, and returning nothing for want of one would leave their primary quantity underived and every contrast in them empty.

**Five derived metrics is a deliberate ceiling, and the correction arithmetic behind it moved.** The family core corrects over is comparisons × metrics *within one run*, so a template returning twenty diagnostics widens every interval in the run for numbers nobody reads. The plan now declares its own families explicitly and puts eight arms in **no family at all**, on the principle that one primary quantity has nothing to correct across — E7 among them. So E7's four cell contrasts and its template's one applicable metric are not a family of fifteen being corrected; they are four supporting comparisons under a config declaring `correction: none`, and what core says about that choice is [`W-STATS-FAMILY`](reference.md#warnings-core-reports). The mismatch between the two notions of a family is [gap 11](#gaps-this-analysis-found-in-the-specification).

---

## Where every statistical procedure lands

The plan's Statistical Test Reference enumerates every inferential procedure it uses. Each lands in exactly one of four places, and which one is what the config is deciding.

| Procedure, and where the plan uses it | Lands as | Why |
|---|---|---|
| Flagging rate, accuracy, sensitivity, FPR (all arms) | A **recorded column**, meaned over the unit table | `io.record` per patient; `basis: units`, with `ci95` and the four-way `n` |
| Cohen's / Fleiss' kappa (E4 against construction; E1's panel) | For E4, a **template `aggregate`** metric; for E1, **nothing at all** | Derivable from the unit table, so core recomputes E4's on each resample and it gets a percentile interval. The panel's agreement with the construction is computed over pictures two or three clinicians looked at, and no run has those units |
| AUROC (E2, E6) | A **template `aggregate`** metric | Same route. A rank statistic over the whole table is exactly what `aggregate` is for |
| McNemar's paired difference (E4b, E5b, E5d) | A **declared contrast** | The *delta* is `paired_percentile_over_units` over the intersection, with `n_paired`. Core computes the quantity; it does not compute McNemar's p-value |
| Referred-vs-unlabelled difference (E4a) | A **declared contrast**, unpaired and clustered | `cluster_by: match_set` makes the matched set the resample draw, so the interval respects the **caliper** matching the plan moved to. What core cannot do is word the claim: "no referral recorded" is unlabelled rather than negative, and that lives in the hypothesis `statement` |
| Excess referral load (E5b) | The **same contrast**, read on the referral scale | The plan states it: with every trajectory shown under both conditions, the FPR difference *is* the discordance asymmetry divided by the trajectory count |
| E5b's floor, when few or no pairs are discordant (E5b) | A `summary`-step **`Estimate`** | A one-sided exact upper bound by the rule of three, not a resampled interval. The plan pre-specifies reporting a bound rather than a null, and *utilization moves the false-positive rate by at most one and a half points* is the publishable sentence — but it is arithmetic on a discordant count, which is not a construction core has |
| The graded negative strata (E5b) | **`report_by`** on a unit attribute | The three strata sit inside each count arm rather than beside it, so they are a description of the same units and not a third condition |
| The two average marginal effects, `AME_P` and `AME_U` (E7) | A `summary`-step **`Estimate`** each | Each is the mean of two cell-level paired differences, one per level of the other factor. A declared contrast compares two conditions; averaging two of them is a quantity over two contrasts, which is where core stops. **The four cell contrasts are declared** and core computes them, so what is lost is the recomputation and not the evidence |
| E3's format selection versus its estimate (E3) | [`data.units.holdout`](reference.md#a-fixed-holdout-split), plus a `summary`-step scalar | Core narrows every denominator to the test partition, which is exactly the held-out estimate E3's decision rule is read on. The **selection half has to be screened by the step** through `io.units.train` and reported separately, because a format selected on nothing is not a selection |
| Subgroup description by sex, age band, visit band | **`report_by`** | No executions added, no place in the correction family, because a description claims nothing |
| Permutation test of case-vs-control (E4a) | **`statistics.null_test`** | `shuffle: status` under a declared `cluster_by` permutes within each matched set — the classic matched permutation test rather than a free relabelling |
| Conditional logistic regression (E4a) | A `summary`-step **`Estimate`** | A stratified estimator, not a mean over a table |
| Mixed-effects logistic regression (E3, E5, E7, E8, E10) | A `summary`-step **`Estimate`** | [Out of scope for core aggregation](experimental-designs.md#what-core-will-not-do-for-you), by name |
| Cochran's Q (E5a, E8) | A `summary`-step **`Estimate`** | A three-condition omnibus test; core computes pairwise contrasts, not omnibus statistics |
| DeLong test (E6) | A `summary`-step **`Estimate`** | A test on two AUROCs over shared cases |
| Calibration curve (E2) | A **step artifact**, `io.write` | A diagnostic plot, not a metric |
| Shortcut reliance index (E7, E10) | A `summary`-step **`Estimate`** | Still an interaction, still not a contrast — but no longer a *ratio*: the plan replaced `AME_U / AME_P` with `(\|AME_U\| − \|AME_P\|) / (\|AME_U\| + \|AME_P\|)` on [−1, +1], because the ratio's interval ran three orders of magnitude wide across the outcomes the study exists to distinguish. Core's position is unchanged by that; what changed is which values the step can describe |
| E7's floor rule, and the band a run lands in (E7, E10) | A `summary`-step **scalar** | Pre-registered, so which of the three bands the total response falls in is a fact about the run and belongs in its record rather than in the reader's head |
| Age band × crossing magnitude interaction (E9) | A `summary`-step **`Estimate`** | The same rule, one experiment over |
| Holm across a declared family | **`statistics.correction`**, *within one run*, over comparisons × metrics | Two mismatches rather than one. The plan's `{E5a–d}` family crosses four run boundaries and core corrects per run; and where the plan declares no family, core still counts one unless the config says `correction: none`, which earns a warning. See [the gaps](#gaps-this-analysis-found-in-the-specification) |

Three readings of that table are worth stating, because each is easy to get backwards. **The AUROC row and E4's kappa row are not refusals** — routing them to a summary step would forfeit the interval that makes them reportable, and would be the most consequential mistake available when translating this plan. **The McNemar rows are half-refusals**: the difference and its interval are computed, and only the p-value is not, which is a smaller loss than it sounds given the plan's own commitment to reporting intervals rather than significance. And **the two `AME` rows are the load-bearing refusal in the new plan**, because they carry the study's own gate: §0.7 opens on the physiology main effect being non-zero, that effect is an average of two contrasts, and so the gate is evaluated on a metric core stores without recomputing — `verdict_rests_on: reported` rather than `computed`. The four cell contrasts underneath it are computed, which is what keeps the quantity checkable; the averaging is not.

---

## The fourteen configs

Every config below is **byte-identical to a file `publishable validate` accepted** in its declarations, and differs in one way that is entirely presentation: `data.input_dir` and `data.output_dir` are shown as `/secure/...` paths rather than the scratch paths the measurement used. (The house style's `×` is not applied to a config's own text, so E10's `description` reads `2x2` here as it does in the file.) What was run, and against which commit, is in [Executability on this build](#executability-on-this-build).

Three conventions run through all fourteen. Every arithmetic figure is stated **before** the YAML, in the four quantities that matter: conditions, repeats, the execution count `validate` checks against `limits.max_executions`, and the **metered requests** — conditions × repeats × units, which is the only figure a deployment bills for. That last one is not what `dry-run` prints: `dry-run`'s `unit-executions` counts every step's handling of every unit, including the `run`-scoped roster summary and the `condition`-scoped serializer, neither of which issues a request. Both numbers are given, and they are different numbers on purpose.


### E2 — the utilization baseline

**The problem.** Testing whether the model uses a visit-count shortcut is only meaningful if the shortcut is available in the data, so E2 fits a logistic regression on the **pre-index visit count** alone and reports its AUROC. Its magnitude is the reference row E7 reads the model's operating point against.

**Two things about this arm changed with the restructure, and both change the config.** The outcome is a **specialty referral**, not `growth_dx_flag`, with a defined index date — the referral date for a referred child and a matched assigned date for one with none recorded. And the predictor is the count of visits before *that* date, not the distributed `visits_count_pre_dx`, which truncates at a diagnosis for one arm and equals the lifetime count for the other. The config carries both as attributes, `referral_recorded` and `visits_pre_index`, and neither retired column appears anywhere in the fourteen.

**The design decision.** The feature set is a **named** parameter and not a list, because a swept value must render as `[A-Za-z0-9._+-]+` and `[visits_pre_index, visits_span_days]` does not — `E-SWEEP-VALUE-UNNAMEABLE`, [measured below](#executability-on-this-build). `count_only` and `count_spacing_span` are the two names, the first designated `sweep.baseline`, and the step resolves each to its column list. The five folds are the split the comparator is fitted on, which `growth_label.validate` requires: a model fitted on the units it will be tested on is what config discipline cannot catch and a template's cross-block rule can. A fold level's `stratify_by` takes **a string, not a list** — the one shape in these fourteen files that a reader of the config schema alone would get wrong.

**The hypothesis is `exploratory`, and that is the plan's word rather than a hedge.** §Effect sizes says E2's H0 of AUROC = 0.5 is "nearly vacuous", sizes the arm for a usable interval instead, and calls it descriptive rather than powered; §E2 adds that the estimate is an **upper bound** on the care-process signal, because recorded utilization and recorded referral are correlated through how completely a child appears in this EHR at all. A `confirmatory` declaration would have claimed more than the plan does, and `kind` is the field where that claim is made.

**"AUROC > 0.5" is expressible two ways now, and this config takes the second.** `compare: {to: constant, value: 0.5}` on the template's per-condition AUROC gets a computed bound that joins the correction family; the `summary` step's [`Estimate`](reference.md#estimate-carries-your-interval-without-core-claiming-it) pools every fold's out-of-fold score into one AUROC over patients, which is the quantity E2 actually claims. The cost of the second route is disclosed in the record — `verdict_rests_on: reported`, outside the family, never recomputed.

**`correction: none`, and the warning it earns is a finding rather than an oversight.** The plan puts E2 in no multiplicity family. Core's family is comparisons × metrics within one run, so `holm` here would correct this arm's interval for a second feature set nobody reads a claim off. Declaring `none` says so, and core replies [`W-STATS-FAMILY`](reference.md#warnings-core-reports) — [gap 11](#gaps-this-analysis-found-in-the-specification).


| | |
|---|---|
| Units | 1,000 patients — 500 with a referral recorded, 500 with none recorded while observed |
| Conditions × repeats | 2 × 5 folds |
| Executions | 12 (`dry-run`) |
| `dry-run` unit-executions | 3,000 |
| Metered LLM requests | **0** — E2 contains no model |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


```yaml
# configs/e02-utilization-baseline/config.yaml
schema_version: "1.0"
experiment_type: growth_label
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e02-utilization-baseline
  description: "E2: how much of the referral outcome a pre-index-visit-count model recovers, and what spacing and span add"
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
    attributes: [visit_decile, sex, referral_recorded, visits_pre_index, visits_span_days, index_age_years]
    allocation: within

parameters:
  model:
    kind: logistic
    feature_set: count_only
    max_depth: 3
  truth:
    label_source: referral
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
  # `none`, and the warning it earns is the finding rather than an oversight.
  # The plan puts E2 in no multiplicity family: it tests one pre-specified
  # primary quantity and everything else in its section is descriptive. Core's
  # family is comparisons x metrics WITHIN a run, so declaring `holm` here would
  # correct this arm's interval for a second feature set nobody reads a claim
  # off. `W-STATS-FAMILY` is what core says about that choice.
  correction: none
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
    kind: exploratory
    statement: "A pre-index-visit-count model discriminates the referral outcome above chance, as an upper bound: recorded utilization and recorded referral share their capture."
    metric: step03_compare.auroc_count_only
    direction: greater
    threshold: 0.5
    evaluate_on: ci95_lower
```


### E3 — serialization selection

**The problem.** Feature readability is sensitive to how numbers are written down, and number tokenization alone has been shown to invert model rankings — so a growth-chart result in one arbitrary format is not a result about growth charts. E3 crosses three feature derivations with three presentation formats and reports the spread as a headline caveat.

**Its items are constructed now, and that is what moved E3 to the root of the core.** E3 scores classification accuracy, accuracy needs a correct answer, and on a real patient that answer would have to be an EHR label — which is what used to make E3 wait on E1. Drawn from the same synthetic family as E4b, the answer is known by construction, `truth.label_source: by_construction`, and nothing upstream of E3 remains.

**The design decision.** A full 3 × 3 factorial *with a designated reference cell* is the one shape a naive config gets wrong: listing the baseline's own value in the `grid` renders that cell twice, once as `00_baseline` and once as its own product row. The spelling that works is the specification's second baseline row — **fix the axis you are measuring and leave the axis you are stratifying over free**. `baseline: {serialize.features: derived}` with `grid` listing only `raw` and `raw_plus_derived` against all three formats gives three per-format baselines and six product cells: nine conditions, one per factorial cell, and `vs_baseline` is the feature-derivation contrast *within each format* for free. The three pairwise format contrasts at fixed derivation are declared, because no baseline produces them — and three is the plan's own `m` for the {E3 format contrasts} family.

**The 300/300 split is a [`holdout`](reference.md#a-fixed-holdout-split), and it is the most interesting mapping in the fourteen.** The plan added it because selecting the winner and estimating its margin on the same data is a winner's curse of the same order as the ~10-point threshold the decision rule reads. Core gives half of that for free and refuses the other half in a way worth stating precisely:

- **What it gives.** `holdout: {method: random, frac: 0.5}` narrows every denominator to the test partition. Every metric, every contrast and the hypothesis's own bound are computed on 300 units the selection never informed, without the pipeline knowing a split exists — `dry-run` prints 300 units handed to each execution rather than 600, which is [measured below](#executability-on-this-build).
- **What it refuses.** The selection half is then unscored, and a format selected on nothing is not a selection. So the screening step asks for `io.units.train` and screens it too, writing that half's accuracy as an **artifact** rather than through `io.record` — those units are not what any metric in this run is over. The summary step reads the artifacts back and reports both spreads, which is the decision rule's own requirement: the selection-half spread is optimistically biased and says so, the held-out spread is what the rule is read against.
- **What it costs.** Double the requests. A holdout is free in the record and not on the meter.


| | |
|---|---|
| Units | 600 constructed trajectories, split 300 selection / 300 held out |
| Conditions × repeats | 9 × 5 |
| Executions | 65 (`dry-run`) — `validate` checks 9 × 5 = 45 against `limits.max_executions: 500` |
| `dry-run` unit-executions | 19,500 — 65 × **300**, the test partition |
| Metered LLM requests | **27,000** = 9 × 5 × 600, both halves, matching the plan's own figure |
| Correction family | 8 baseline comparisons + 3 declared contrasts, × the metrics the template derives |


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
    attributes: [sex, age_band, synthetic_truth, visits_pre_index, visits_span_days]
    allocation: within
    # E3's 300/300 split, and it is `holdout` rather than a fold because the two
    # halves do different jobs: the format is SELECTED on one and its margin
    # ESTIMATED on the other, which is the winner's curse the plan's own
    # decision rule now guards against. A fold would give five estimates of one
    # quantity; this gives one estimate that the selection never saw.
    holdout: {method: random, frac: 0.5, seed: auto}

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
    crossing_channels: 2.0
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: by_construction
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
    - {id: digits_vs_sentences, of: "format=digit_string__baseline",
       against: "format=sentences__baseline"}
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

**The design decision.** The plan describes 150 trajectories × 3 visits = 450 calculations, which reads like technical replication — and [`data.units.measurements`](reference.md#what-isnt-a-repeat) is where that belongs, collapsing at unit resolution before any step runs. It does not work here, and the refusal is precise: a resolver has no columns beyond the attributes it yields, so `measurements: {by: calc_id}` requires the resolver to emit **one `Unit` per calculation sharing a patient key** (`E-RESOLVER-MEASUREMENT-FIELD`), and a `collapse: mean` applied wholesale then tries to average the string-valued attributes too (`E-DATA-MEASUREMENTS-COLLAPSE-TYPE`). Both were measured. The simpler expression, used here, is a per-unit `arith_error_rate` column the step records over that trajectory's three calculations — which is the same collapse done one layer up, at the cost of losing the per-calculation rows from the unit table.

**Constructed items, and `correction: none`.** E3b's items come from the same synthetic family as E3's, for the reason E3's do: arithmetic is checkable on its own terms, but the classification it is scored beside needs a correct answer. And the plan puts E3b in no family — one primary quantity, the paired arithmetic-error-rate difference — so the config says so and takes the warning.


| | |
|---|---|
| Units | 150 constructed trajectories, three scored calculations each |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 2,400 |
| Metered LLM requests | **1,500** = 2 × 5 × 150 |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


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
    attributes: [sex, age_band, synthetic_truth, visits_pre_index, visits_span_days]
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
    source: synthetic_physiology
    physiology: concerning
    schedule: typical
    crossing_channels: 2.0
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: by_construction
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
  # One primary quantity, so no family: the plan's {E3 format contrasts}
  # family is E3's, and E3b's arithmetic scoring is its own arm.
  correction: none
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

**The problem.** Real referred and unreferred children differ in many correlated ways, so E4a matches 300 pairs on the pre-index visit count, spacing, age band and sex, leaving the trajectory as the only difference. It is the accuracy layer's affirmative arm — **secondary**, in the plan's own ordering, and not what the study concludes on.

**Two changes the restructure forces into the wording, not just the columns.** The arms are `referred` and `no_referral`, and the second is **unlabelled rather than negative**: a child with no recorded growth-relevant referral may have had none, or been referred outside this network, or after the export. The hypothesis `statement` says so, because that is the only field in the file where it can be said — core will happily compute a difference between two arms and has no opinion about what the absence of a code means. And the matching is a **caliper** rather than exact: the plan measured 45.8% of cases sitting at a pre-diagnosis count no control could have, and a caliper reports a residual imbalance where exact matching hid it as an empty stratum.

**The design decision.** Referral status is a property of the units, so it is a `groups` axis read from an existing column, and the matching is carried by `cluster_by: match_set` — which is what tells core the two arms are not independent samples. Three things follow without further declaration: intervals are clustered on the matched set, `statistics.resample` draws whole sets rather than subjects, and `statistics.null_test` with `shuffle: status` permutes the label *within* each set, giving the classic matched permutation test rather than a free relabelling. The arms are peers, so no `sweep.baseline` may name one; the comparison is a declared contrast.

**Conditional logistic regression is the refusal here**, and the route is a `summary`-step `Estimate`. What core computes is the clustered difference in flag rate with its interval, which is the quantity the plan says it reports for this arm anyway — §Effect sizes notes that the interval E4a reports is the unadjusted between-arm difference rather than the conditional estimate.

**`kind: exploratory`, because the plan declares the arm exploratory.** It needs roughly three times its planned n for a ten-point margin, and it is Layer C. Declaring it confirmatory would put a claim in the record the plan does not make.


| | |
|---|---|
| Units | 600 — 300 caliper-matched pairs |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 5,400 |
| Metered LLM requests | **3,000** = 2 × 5 × 300 units per arm |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


```yaml
# configs/e04a-matched-pairs/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e04a-matched-pairs
  description: "E4a: does the screen separate referred children from unlabelled ones matched on pre-index visit count, spacing, age band and sex"
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
    attributes: [status, match_set, sex, referral_recorded, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: referral
  scoring:
    parse_failure: ineligible

sweep:
  groups:
    - {by: status, levels: [no_referral, referred]}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per arm; the matched-set cluster is what carries the caliper matching into the interval."

statistics:
  # No family: E4a tests one primary quantity, and the plan declares the arm
  # exploratory besides — it needs roughly three times this n for a ten-point
  # margin, and it is secondary to the core by construction.
  correction: none
  resample: {method: bootstrap, n: 2000}
  null_test: {method: permutation, n: 5000, shuffle: status}
  contrasts:
    - {id: referred_vs_unlabelled, of: "status=referred", against: "status=no_referral"}
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
    kind: exploratory
    statement: "The screen flags referred children more often than their matched comparators, whose absence of a referral is unlabelled rather than negative."
    metric: step03_screen.flag_rate
    compare: {contrast: referred_vs_unlabelled}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E4b — the physiology-preserving counterfactual

**The problem.** Take a real patient's exact visit schedule and substitute two synthetic trajectories onto that identical scaffold — one genuinely concerning, one healthy. Utilization is identical across conditions by construction, so a model that cannot separate them is not reading the curve at all.

**The design decision.** The scaffold is the unit and the physiology is a swept parameter, which makes the design within-subject and the contrast paired over the intersection of both arms' completed units. `truth.label_source: by_construction` is not decoration: `growth_screen.validate` refuses a synthetic stimulus arm that still claims an EHR label, because no clinician ever referred a child who does not exist. The wholly synthetic arm carries no pre-index count as a control variable at all — its visit structure is identical across conditions by construction, which is the plan's universal visit-count control obtained a different way.

**The scaffolds are drawn from the mid-childhood band, and the age scope is why.** The plan fixes E4b's window at 3 to 8 years, where the concerning/healthy boundary is unambiguous: crossing is normal again around pubertal onset, and the infant window where it is also normal is now out of scope entirely. That is a property of the roster rather than of the config — the constructor is handed scaffolds already inside the band — which is the [eligibility-versus-roster rule](../CLAUDE.md#feasibility-analyses) applied to an age restriction.

**This is the run that publishes scaffolds.** E7 and E10 consume the same 250 synthetic schedules, and the way they get them is a `summary` step here writing them under a name downstream runs address by [`io.reuse_from`](reference.md#lineage-between-runs) — the only genuine lineage edge in the fourteen.


| | |
|---|---|
| Units | 250 real visit scaffolds, mid-childhood band |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 4,000 |
| Metered LLM requests | **2,500** = 2 × 5 × 250, the plan's 500 trials × k = 5 |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


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
    attributes: [sex, age_band, synthetic_truth, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
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
  # No family: one primary quantity, the paired flagging-rate difference
  # between the two physiology conditions on an identical schedule.
  correction: none
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

**It reads no label at all, and that is new.** The outcome is the positive-prediction rate, which is a within-subject question with no correct answer to score against, so `truth.label_source: none` — a third value the template gained when the plan's Layer A stopped consuming ground truth. What follows in code is that `growth_screen.aggregate` derives `flag_rate` from a table with no truth column and derives nothing else, which is the difference between an arm that measures response and an arm that measures correctness.

**Three constraints make "holding the growth signal fixed" true of the displayed evidence, and each has a reader.** They are the plan's, added 2026-08-30, and without them the ladder would vary information content and noise alongside the schedule:

- **Deviation-preserving** — the visits across which the crossing becomes legible are identified before resampling and retained in every arm; the sparse arm drops only non-carrying visits. Not a parameter, because an arm that could switch it off would be an arm whose sparse condition measures something else.
- **Noise-matched** — `stimulus.resample_noise: matched` returns interpolated points carrying measurement error at the within-child SD, so a dense arm cannot be identified by being smoother than a sparse one.
- **Availability-matched** — `stimulus.height_availability: 0.538` holds the share of displayed visits carrying a height at the cohort rate in every arm, so densifying a schedule does not also make the record more complete.

**A trajectory too sparse to keep its carrying visits is excluded from the roster, not skipped in one arm.** The plan says to exclude them before use and report the count. Both routes exist here and they are not equivalent: [`io.skip`](reference.md#the-unit-table-is-the-inference-base) would land them in `ineligible` and report the count for free, but it fires in the sparse arm only, and a contrast is computed over the intersection of both sides' completed units — so the pairing would silently narrow in exactly the arm the exclusion came from. A roster filter keeps every unit in all three conditions and pays for the count by having to state it.

**The design decision.** Three densities is a three-level parameter axis with the typical arm designated baseline, so `vs_baseline` gives both comparisons and the declared `dense_vs_sparse` contrast gives the extreme one the 2 × 2 later reuses. The hypothesis is an **invariance** claim, and the shape matters: written as a directional test on a point estimate it passes on an estimate whose interval permits a large effect. `direction: less, threshold: 0.05, evaluate_on: ci95_upper` is the equivalence form, and it is the reason E5's null being the desired outcome does not make E5 unfalsifiable.


| | |
|---|---|
| Units | 200 trajectories |
| Conditions × repeats | 3 × 5 |
| Executions | 23 (`dry-run`) |
| `dry-run` unit-executions | 4,600 |
| Metered LLM requests | **3,000** = 3 × 5 × 200, the plan's 600 trials × k = 5 |
| Correction | `holm` — the plan's {E5a–d} family, of which core can see only this quarter |


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
    attributes: [sex, age_band, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    # Nothing. E5a asks whether the model's own answer MOVES when only the
    # schedule changes, which is a within-subject question with no correct
    # answer to score against.
    label_source: none
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


### E5b — the graded negative control

**The problem.** True-negative trajectories, each shown once with an inflated visit count and once with a typical one. Every case is negative by construction, so the difference in flag rate between the two conditions is referral load incurred at **zero** diagnostic return.

**The negatives are graded now, and the grading is a `report_by` rather than a condition.** An arm built entirely from flat mid-channel curves has a floor problem: a competent model flags almost none of them under either condition, discordant pairs approach zero, and there is no room for a utilization effect to appear. The plan therefore draws three strata of roughly equal size — unambiguous flat, normal-but-low, and normal-with-benign-variation — every one a true negative. They sit **inside** each count arm rather than beside it, so they are a description of the same units: `negative_stratum` is a unit attribute the constructor reads to decide which curve to draw and `statistics.report_by` repeats the metrics over them. Making them a third axis would have tripled the executions and put three strata nobody tests into the correction family, which is [the distinction](reference.md#reporting-strata) between describing a subgroup and testing one.

**The design decision.** Two things make this the cleanest arm in the plan and the cheapest to express. Because every unit is negative under both conditions, `false_positive_rate` is a recorded-column mean and the declared contrast on it *is* the quantity the plan wants — the plan says so itself, noting that under a within-subject design the marginal FPR difference is exactly the discordance asymmetry McNemar's tests, divided by the number of trajectories. And `scoring.parse_failure: negative` is the one config in the fourteen that departs from the default: with the truth constant, an unparseable response is a screen that did not flag, and routing it to `ineligible` would quietly remove the units most likely to have been confused by the inflated schedule.

**The floor is a bound, and the bound is a refusal.** The plan pre-specifies that few or no discordant pairs is reported as a one-sided upper bound rather than as "no effect" — about 1.5 points at n = 200 by the rule of three. That is arithmetic on a discordant count, not a resampled interval over a column, so it is a `summary`-step `Estimate`, computed only for an arm whose physiology is `true_negative`. **The guard is on the arm, not on the shape of the sweep**: E4b and E5d also have two conditions and also produce flips, and calling those false positives would be a fabrication with a plausible name.


| | |
|---|---|
| Units | 200 constructed negatives, three strata |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 3,200 |
| Metered LLM requests | **2,000** = 2 × 5 × 200 |
| Warning at `validate` | `W-DATA-CLUSTER-UNDECLARED` on `negative_stratum` — see [the gaps](#gaps-this-analysis-found-in-the-specification) |


```yaml
# configs/e05b-graded-negative/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e05b-graded-negative
  description: "E5b: unambiguously healthy flat curves under an inflated and a typical visit count"
  authors: ["Kyungjoon Lee"]
  institution: "PPOC"

entrypoint: "growth_chart.experiment:ScreenExperiment"

data:
  input_dir: /secure/data/gcl/e05b-graded-negative
  output_dir: /secure/results/gcl/e05b-graded-negative
  input_manifest_policy: hash_all
  units:
    from: {resolver: growth_trajectory}
    key: patient_id
    attributes: [sex, negative_stratum, synthetic_truth, visits_pre_index, visits_span_days]
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
    source: synthetic_negative
    physiology: true_negative
    schedule: typical
    crossing_channels: 0.0
    resample_noise: matched
    height_availability: 0.538
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
  rationale: "Every unit is negative by construction across all three strata, so the flag rate is the false-positive rate and its contrast is excess referral load."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: excess_fpr, of: "schedule=dense", against: "baseline"}
  # The three negative strata describe the arm; they do not test it. A stratum
  # you want to TEST is a contrast with `within`, which joins the correction
  # family — and at roughly 67 pairs a stratum, the plan says plainly that the
  # breakdown supports only large differences and is reported descriptively.
  report_by: [negative_stratum]

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

**The problem.** Display exactly five visits per patient regardless of the true total, then ask whether the model's **positive-prediction rate** still tracks the *hidden* total. A residual association means the shortcut is carried by something beyond raw count-in-context.

**The outcome is the rate, not accuracy, and that is what keeps this arm in the core.** An earlier version asked whether accuracy tracked the concealed total, which needs a correct answer for each patient and so an EHR label — putting the arm in the accuracy layer and making it hostage to the label problems the plan documents. Asking whether the *rate* tracks it needs no correct answer at all, so the config declares `truth.label_source: none` and the template derives `flag_rate` and nothing else.

**The design decision.** This is the one arm that is **not a condition at all**. Nothing about the pipeline varies: the display cap is fixed at five, the roster is one, and the covariate under test is hidden from the model by construction. So the config declares no `sweep`, the hidden total becomes a unit attribute reported over by `report_by: [true_count_band]`, and the residual association itself — a slope, not a difference between two conditions — is a `summary`-step `Estimate` named by the hypothesis.

A contrast is genuinely unavailable here, and it is worth being plain about why: `of` and `against` name **two conditions**, and there is only one. A version of this arm that wanted a core-computed difference would have to make the count band a `groups` axis — turning a covariate into a design cell, which is the wrong description of an experiment whose whole point is that the band was invisible to the model.


| | |
|---|---|
| Units | 300 patients with at least 5 visits |
| Conditions × repeats | 1 × 5 |
| Executions | 9 (`dry-run`) |
| `dry-run` unit-executions | 2,700 |
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
    attributes: [true_count_band, sex, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    # Nothing: the outcome is the POSITIVE RATE against the concealed total,
    # not accuracy. Asking whether the rate tracks a total the model cannot see
    # needs no correct answer, which is what keeps this arm in the core.
    label_source: none
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

**It reads no label either.** The outcome is whether the positive rate moves when a sentence is added, so `truth.label_source: none` — one of the five arms whose claim survives whatever happens to the accuracy layer.

**The sentence states the roster's own count, not the displayed one.** Under a `visit_cap` those differ by construction, and the manipulation is a claim about what the record holds; reading the length of the rendered table instead would make the framing arm agree with the display in every condition, which is the one thing it must not do.


| | |
|---|---|
| Units | 300 patients |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 4,800 |
| Metered LLM requests | **3,000** = 2 × 5 × 300 |
| Correction | `holm` — the plan's {E5a–d} family, of which core can see only this quarter |


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
    attributes: [sex, age_band, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: none
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

**The problem.** Without a simple-model comparator a respectable LLM accuracy figure is uninterpretable, since it could reflect trajectory reading or it could reflect that logistic regression on four features matches it. The informative version withholds visit count from the comparator.

**The design decision.** Two axes — model kind and feature set — with `baseline: {model.feature_set: llm_matched}` fixing the axis under test and leaving `model.kind` free, so each of logistic regression and the boosted tree gets its own reference and the visit-count contribution is `vs_baseline` within each. Fixing both would mark the diagonal cell `confounded: true`, which `validate` warns about by name and which was measured before the config was rewritten. `cluster_by: match_set` carries E4a's matched sets into the folds, so no matched pair is split across train and test — a rule core enforces rather than documents.

**The comparison against the LLM is the refusal**, and it is a cross-repository one on the recommendation [above](#one-repository-fourteen-configs): E6's scores and E4a's flag rate live in different runs, so the comparison is a [`study`](reference.md#studies-what-a-paper-reports) joining both records. The plan has since dropped DeLong from that comparison for a reason core has no way to know — the model emits a decision and therefore has no ROC curve — and replaced it with **McNemar's on paired classifications at the comparator threshold that equalizes the two positive rates**. That threshold is a choice made after both runs exist, over units both scored, which is exactly the shape a `study` step handles and a contrast cannot.

**Its label is the referral outcome**, like E4a's and E2's, so a "no referral recorded" comparator is being fitted against an unlabelled class rather than a known negative. That does not change what core computes; it changes what the AUROC means, and the plan says so.


| | |
|---|---|
| Units | 600 — the E4a matched sample |
| Conditions × repeats | 4 × 5 folds |
| Executions | 22 (`dry-run`) |
| `dry-run` unit-executions | 3,000 |
| Metered LLM requests | **0** |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


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
    attributes: [status, match_set, sex, referral_recorded, visits_pre_index, visits_span_days]
    allocation: within
    cluster_by: match_set

parameters:
  model:
    kind: logistic
    feature_set: llm_matched
    max_depth: 3
  truth:
    label_source: referral
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
  # No family: one primary quantity, the paired classification difference
  # between the model and the comparator at a matched positive rate.
  correction: none
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

**The problem.** Cross the two physiology conditions with the sparse and dense schedule arms on shared synthetic scaffolds, and report the crossed design as one table. This is the paper — and since 2026-08-30 it is also the study's **primary endpoint**, reached through one gate, with everything else in the plan secondary or exploratory.

**It reads no EHR label, and that is a designed property rather than a convenience.** Both main effects are response differences on synthetic scaffolds, so the headline result is unaffected if the referral label proves unusable; `truth.label_source: none` is the config saying so. What E7 loses in that case is two reference rows of context — E2's baseline and E6's comparator — and no part of its inference.

**The design decision.** The 2 × 2 is `baseline: {stimulus.physiology: healthy}` with `grid` listing only `concerning` against both schedules — four cells, two of them per-schedule baselines, no cell rendered twice. `vs_baseline` then *is* the physiology effect at each utilization level, and the two utilization contrasts are declared because the arms of that axis are peers relative to the baseline. E5a's typical arm is deliberately not carried in: the synthesis estimates a contrast between utilization extremes, and the graded dose–response stays in E5a.

**The two average marginal effects are the plan's supporting quantities and core cannot build either.** `AME_P` is the mean over scaffolds and over **both** utilization levels of the physiology difference; `AME_U` is its mirror. Each is an average of two cell-level paired differences, and a declared contrast compares two conditions — averaging two of them is a quantity over two contrasts. So the four cell contrasts are declared and computed, and the two averages come back from a `summary` step as `Estimate`s with their own intervals. **What that costs is precise**: the plan's gate is H0b on `AME_P`, so the study's own gate is evaluated on a metric core stores without recomputing, and the verdict records `verdict_rests_on: reported`.

**The index is still an interaction, and it is no longer a ratio.** `SRI = (|AME_U| − |AME_P|) / (|AME_U| + |AME_P|)` on [−1, +1], because the ratio's interval ran from [0.03, 0.20] where the model reads physiology to [−102, +74] where the physiology effect is near zero — three orders of magnitude across the outcomes the design exists to distinguish. Core's position is unchanged by the change of form: a comparison of two contrasts is an interaction and [contrasts do not nest](experimental-designs.md#what-core-will-not-do-for-you). What changed is which values the step can describe, and one of them matters: under the ratio a zero physiology effect was undefined, and that is E4b's H0 holding — the outcome the plan explicitly plans for. The bounded form reports it as +1. The one case still undefined is a model that moves for **neither** manipulation, which is the floor rule's `not_interpreted` band and a decisive finding rather than missing data.

**The floor rule is pre-registered, so the band a run lands in belongs in the record.** Three bands on the total response `|AME_P| + |AME_U|` — read normally at 0.20 and above, reported with its width stated between 0.10 and 0.20, not interpreted below — and the step returns which one, beside the total itself.

**`correction: none`, because the plan says no multiplicity correction applies to a single pre-specified primary quantity.** Core's family here would be six comparisons per metric, and correcting the study's headline interval for cell contrasts that support it would be the opposite of what the plan asks. The config takes `W-STATS-FAMILY` instead — [gap 11](#gaps-this-analysis-found-in-the-specification).


| | |
|---|---|
| Units | 200 of E4b's 250 scaffolds, restricted to those where both density arms are constructible |
| Conditions × repeats | 4 × 5 |
| Executions | 30 (`dry-run`) |
| `dry-run` unit-executions | 6,000 |
| Metered LLM requests | **4,000** = 4 × 5 × 200, the plan's own figure |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


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
    attributes: [sex, age_band, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    # The headline 2x2 reads no label at all: both main effects are response
    # differences on synthetic scaffolds, so the arm is unaffected if Layer C's
    # referral label proves unusable.
    label_source: none
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
  # No family: E7 concludes on ONE pre-specified primary quantity, and the
  # plan says in as many words that no multiplicity correction applies to it.
  # The four cell contrasts below are what the two average marginal effects are
  # built from and are reported as supporting.
  correction: none
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
    statement: "GATE. The physiology main effect is non-zero; below it the index is not interpreted at all."
    metric: step04_compare.ame_physiology
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
  - id: h1c
    kind: confirmatory
    statement: "PRIMARY ENDPOINT. The shortcut reliance index sits below zero: the model responds more to the curve than to the schedule."
    metric: step04_compare.shortcut_reliance_index
    direction: less
    threshold: 0.0
    evaluate_on: ci95_upper
  - id: h1d
    kind: exploratory
    statement: "The physiology effect at a sparse schedule is positive."
    metric: step03_screen.flag_rate
    compare: {contrast: physiology_at_sparse}
    direction: greater
    threshold: 0.0
    evaluate_on: ci95_lower
```


### E8 — ordering sensitivity

**The problem.** Chronological, reverse-chronological, and shuffled presentations of the same visits, with the shuffled condition using five distinct permutations rather than one. It constrains mechanism; it does not adjudicate the interpretation claim, which is why the plan reports it after E7.

**Its trajectories are constructed, for the reason E3's are.** E8's outcome is accuracy, accuracy needs a correct answer, and on a real patient that answer would be an EHR label — which would move the arm into the accuracy layer and make a mechanism probe hostage to a referral outcome. A constructed trajectory has visits at irregular ages that reorder exactly as a real one's do, so the manipulation is untouched.

**The design decision.** Seven serializations is a **ragged axis** — one chronological, one reverse, five shuffles — and no `grid` product expresses it, because `order` and `permutation` are not independent: `permutation` is meaningless for the two single-ordering arms. [`sweep.paired`](reference.md#expansion-modes) is the spelling: a list of dicts is one axis, not a product, so the six non-baseline rows are enumerated and the baseline supplies the seventh. `growth_screen.validate` refuses `order: shuffled` unless `permutation` is swept, which is the rule that stops one arbitrary shuffle being reported as *the* shuffled condition.

**The five shuffles and the five repeats are separate multipliers, and core keeps them separate.** The shuffles vary the stimulus, so they are conditions; the seeds vary only the sampling of the response, so they are repeats and land in `repeat_spread`. Collapsing them would be the exact mistake the plan warns about, and here it is structurally unavailable.

**The plan's primary is now a directed contrast rather than an omnibus test, and that is a quantity core computes.** A linear contrast with weights (+1, 0, −1) across three equally spaced conditions *is* the chronological-versus-shuffled paired difference, which is a declared contrast on the unit table. Cochran's Q survives as a screen and stays a refusal, along with the mixed-effects model that nests permutation within patient — so the arm's primary quantity moved from the refused column to the computed one without a line of core changing, because the plan sharpened what it was asking for.


| | |
|---|---|
| Units | 300 constructed trajectories, stratified by visit-count band |
| Conditions × repeats | 7 × 5 |
| Executions | 51 (`dry-run`) |
| `dry-run` unit-executions | 15,300 |
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
    attributes: [visit_band, sex, synthetic_truth, visits_pre_index, visits_span_days]
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
    # Constructed rather than real, for the same reason E3's items are:
    # E8's outcome is ACCURACY, accuracy needs a correct answer, and on a real
    # patient that answer would have to come from an EHR label — which would put
    # this arm in Layer C and make it hostage to a label the plan dropped. A
    # constructed trajectory has visits at irregular ages that reorder exactly as
    # a real one's do, so the manipulation is untouched.
    source: synthetic_physiology
    physiology: concerning
    schedule: typical
    crossing_channels: 2.0
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: by_construction
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
    - {id: shuffle0_vs_reverse, of: "order=shuffled__permutation=0",
       against: "order=reverse__permutation=0"}
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
    statement: "PRIMARY. Shuffling the visits costs accuracy against chronological order — the ordered contrast's two ends, which on three equally spaced conditions is what the linear contrast reduces to."
    metric: step03_screen.accuracy
    compare: {contrast: shuffle0_vs_chronological}
    direction: less
    threshold: 0.0
    evaluate_on: ci95_upper
```


### E9 — age-dependent norm application

**The problem.** Percentile crossing is uncommon in mid-childhood and **normal again around pubertal onset**, driven by growth tempo — an early maturer crosses upward and a late one downward, both healthy. A model that flags crossing magnitude without conditioning on age is applying a threshold rule rather than clinical reasoning. E9 matches crossing magnitude across the two bands and asks whether the flagging rate differs.

**This arm was rebuilt, and the rebuild is the clearest case in the plan of a scope decision destroying a design.** E9 previously contrasted infants against children; restricting the study to ages 2 and above removed one arm of that contrast outright, so the experiment could not run as written. The peripubertal window is the second place the plan's own sources document normal crossing, and it sits entirely inside the new scope. Two consequences reach the config: the `age_band` levels are `mid_childhood` and `peripubertal`, and **the peripubertal window is sex-specific** — 9–14 for girls, 10–15 for boys — so `sex` is read by the constructor rather than being a reporting stratum alone.

**The design decision.** The age band is a property of the units, so it is a `groups` axis assigned `by_attribute`, and the crossing magnitude is **fixed** rather than swept. That is a deliberate narrowing of the earlier config, and the reason is the same rule E7 runs into: the plan's `AME_band` is a mean over crossing magnitudes, and a mean over two magnitudes' contrasts is a quantity over two contrasts, which core will not build. Matching the magnitude across bands and fixing it at one value leaves a single between-band contrast core computes with a clustered interval — and the plan's own secondary, the band × magnitude interaction, stays a `summary`-step `Estimate`, which is what the plan already calls it ("at 220 trajectories per band it would resolve roughly double the primary's margin, which is not a usable test").

**The threshold is the plan's 15 points, and the arm is sized at 90% power** because a null here is the failure mode: an age-blind model and an underpowered comparison produce the same non-rejection, which is why the plan reads an interval rather than a p-value and why `evaluate_on: ci95_lower` is the shape.


| | |
|---|---|
| Units | 440 constructed trajectories — 220 mid-childhood, 220 peripubertal, magnitude matched |
| Conditions × repeats | 2 × 5 |
| Executions | 16 (`dry-run`) |
| `dry-run` unit-executions | 3,960 |
| Metered LLM requests | **2,200** = 2 × 5 × 220 units per band |
| Warning at `validate` | `W-STATS-FAMILY`, by construction |


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
    attributes: [age_band, sex, synthetic_truth, visits_pre_index, visits_span_days]
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
    crossing_channels: 2.0
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: by_construction
  scoring:
    parse_failure: ineligible

sweep:
  groups:
    - {by: age_band, levels: [mid_childhood, peripubertal]}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Five draws per cell; crossing magnitude is matched across bands by construction, so the band difference is the whole finding."

statistics:
  # No family: one primary quantity, the between-band flagging-rate difference
  # at matched crossing magnitude.
  correction: none
  resample: {method: bootstrap, n: 2000}
  contrasts:
    # ONE contrast, at ONE crossing magnitude, and the singular is the design.
    # The plan's AME_band is a mean over crossing magnitudes; sweeping the
    # magnitude would make the primary quantity an average of contrasts, which
    # is an interaction and would leave it to a summary step. Matching the
    # magnitude across bands and fixing it keeps the primary in core's hands.
    - {id: band_difference, of: "age_band=mid_childhood",
       against: "age_band=peripubertal"}
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
    statement: "At a matched two-channel crossing the screen flags mid-childhood trajectories more often than peripubertal ones, where the same geometry is ordinary tempo variation."
    metric: step03_screen.flag_rate
    compare: {contrast: band_difference}
    direction: greater
    threshold: 0.15
    evaluate_on: ci95_lower
```


### E10 — cross-model generalization

**The problem.** Findings from one architecture are untrustworthy in this domain specifically, so E10 replicates the core arms across a model roster. Where budget constrains, the plan prioritizes E7 and E5b; this config is the E7 replication, and the E5b one is the same edit applied to that file.

**The roster is what the governance permits, not what is available, and that shrank it by one vendor.** Inference runs on the Harvard Medical School Azure OpenAI API and on locally hosted open-weight models, both approved for real patient data; no cohort-derived data reaches any other endpoint. So the sweep is **three Azure deployments differing principally in size** — the one cleanly identified contrast that arrangement allows, with vendor, tokenizer and hosting held fixed while scale varies — plus **two local checkpoints** spanning two families and two tokenizers. The hosted-versus-local comparison moves family, scale, tokenizer and hosting at once and is reported descriptively, which is the plan's own reading and not something core can enforce.

**The design decision.** Provider and deployment must move **together** — a deployment name is meaningless under the wrong provider, and their product would demand an Azure key for a local checkpoint — so they are one `sweep.paired` axis of five rows, crossed with the 2 × 2. That composition is also what makes the credential check useful: `validate` demands the union over the conditions the sweep actually resolves, which is the two Azure variables here and **nothing** for the local arms, reported per condition and by name.

**The roster is swept by deployment name, and a name with a slash in it would be refused.** A swept value must render `[A-Za-z0-9._+-]+`, so `gpt-4.1-2026-04-14` and `llama-4-70b` are fine and a fully-qualified resource path is not; a study whose deployments are addressed by path sweeps an alias and resolves it in the step.

**Per-model reliance indices and the heterogeneity test across them are refusals** — each index is already an interaction, and testing whether five of them differ is one level further out. Both are `summary`-step `Estimate`s. What core computes is every cell and every declared contrast, per model, which is the input those two need. The plan adds a rule core can carry for free: a model below E7's floor reports an **undefined** index rather than an extreme one, and the number of such models is itself a result — so the floor band is recorded per condition rather than being reconstructed later.

**`correction: holm` here, unlike E7**, because {E10 model contrasts} is one of the plan's four declared families and its `m` is the roster size. Core's family is larger than the plan's — nineteen comparisons per metric rather than five — which is [gap 11](#gaps-this-analysis-found-in-the-specification) in its most consequential form, since this is the arm where the plan's own effect-size table says the correction changes whether the design is adequately sized.

**One config is not the whole of E10.** Replicating E4b, E5b, E8 and E9 across the same five deployments is the same `sweep.paired` block pasted into each of those files, and the cost is in the [summary](#cost-and-execution-summary).


| | |
|---|---|
| Units | 200 shared scaffolds |
| Conditions × repeats | 20 × 5 |
| Executions | 142 (`dry-run`) — `validate` checks 20 × 5 = 100 against `limits.max_executions: 500` |
| `dry-run` unit-executions | 28,400 |
| Metered LLM requests | **20,000** = 20 × 5 × 200 |


```yaml
# configs/e10-cross-model-2x2/config.yaml
schema_version: "1.0"
experiment_type: growth_screen
plugin: "kjlee/publishable-growth-chart@v0.1.0"

metadata:
  name: e10-cross-model-2x2
  description: "E10: the E7 2x2 replicated across the model roster"
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
    attributes: [sex, age_band, visits_pre_index, visits_span_days]
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
    resample_noise: matched
    height_availability: 0.538
  truth:
    label_source: none
  scoring:
    parse_failure: ineligible

sweep:
  baseline: {stimulus.physiology: healthy}
  grid:
    stimulus.physiology: [concerning]
    stimulus.schedule: [sparse, dense]
  paired:
    # The composition rule, and the roster is what the governance permits rather
    # than what is available: inference runs on the HMS Azure OpenAI API and on
    # locally hosted open-weight models, both approved for real patient data, and
    # no cohort-derived data reaches any other endpoint. Three Azure deployments
    # differing principally in size are the one cleanly identified contrast that
    # allows — vendor, tokenizer and hosting held fixed while scale varies — and
    # two local checkpoints span two families and two tokenizers.
    - {llm.provider: azure_openai, llm.deployment: gpt-4.1-mini-2026-04-14}
    - {llm.provider: azure_openai, llm.deployment: gpt-4.1-2026-04-14}
    - {llm.provider: azure_openai, llm.deployment: gpt-5.1-2026-02-20}
    - {llm.provider: ollama, llm.deployment: llama-4-70b}
    - {llm.provider: ollama, llm.deployment: qwen3-72b}

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

Five things in the plan look like pipelines and are not. Treating any of them as a run is the failure mode this section exists to catch — and one of the five **was** a run in this document's earlier reading, which is why it is first.

**The stimulus-validation panel, which used to be E1.** Two to three blinded pediatricians independently adjudicating roughly 110 plotted curves, mixed with real ones as a realism check, is not something core executes. The earlier design — a 200-curve adjudication of an EHR label — at least produced a column a run could read; this one does not produce a column at all. The panel confirms that the constructed stimuli mean what they were built to mean, and its outcomes are a **gate a person passes**: a category whose consensus falls below 90% is regenerated and the arm consuming it is not run. Nothing about that reaches a config, and the two statistics the plan asks for — per-category agreement with exact binomial intervals, and the panel's ability to separate synthetic from real — are computed over pictures no run has units for.

**So the arm that left this vocabulary is the one that was never expressible in it, and the arm that replaced it is cheaper in every direction.** The plan's own arithmetic: validating the label at the scale its decision rule required needed roughly 5,650 adjudicated curves, against 110 for validating the stimuli — a fiftyfold reduction in clinician time, pointed at the assumption that is actually load-bearing. This document's earlier reading routed the kappa gap through a `summary`-step `Estimate` and disclosed what that cost; the honest summary now is that **the quantity was never worth the disclosure**, and the plan reached that conclusion from three directions of its own.

**The generator's own verification.** "Simulated and real trajectories must match on between-child SD, within-child SD and pooled lag-1 autocorrelation, each within 10%" is a check on the code, not an experiment: no conditions, no repeats, no units, and nothing it produces is a measurement of a model. It is a function in `src/` with a test beside it — which puts it inside `code_hash`, so a generator retuned after seeing how a model responded to it cannot be passed off as the one that ran.

**E3's decision rule.** "The best-performing format on the selection half becomes the standard serialization for E4 through E10" is a **human decision made between runs**. Core makes both halves of it legible — the held-out spread is a metric with an interval, the selection-half spread an `Estimate`, and the decision they produce is one parameter value in eleven downstream configs — but nothing about it is adaptive, and it must not be. A config that selected its own serialization from an earlier run's result would be [an adaptive design](design-principles.md#what-core-does-not-promise), which core refuses on purpose. **E1's decision rule is now of the same kind and not of the same shape**: it decides whether to *regenerate stimuli*, so what it changes is an input, not a parameter.

**Cohort construction, eligibility and implausible-value screening.** Daymont-style screening of erroneous heights, the declared plausible ranges the plan now states for every serialized channel, the age-2 floor, and the 12-month look-forward that makes "no referral" mean "none while under observation" all run *before* the roster exists, so they belong to the extract rather than to any run. In `publishable` terms that is structural rather than editorial — they are upstream of `input_dir`, and the hash of what they produced is what a run records. **The age floor is the sharpest instance**, because it is tempting to write it as a config-level filter: it is constant across every condition and every repeat, so it is a property of the sample, and a constructor that clipped a younger trajectory into the window would make the study's scope a property of one Python file.

**Preregistration of the reference frame.** CDC 2000 versus WHO 2006 is now *settled* by the age restriction — WHO for 0–2, CDC thereafter — but the plan still registers it, on the grounds that lowering the floor would silently change the frame. That reasoning is exactly why it stays a parameter here: choosing a value is not an experiment, and a cross-frame comparison is [a separate run rather than a robustness check](reference.md#three-hashes), since the frame changes what every z-score means.

---

## What core refuses, and the route for each

| Refused | Where the plan needs it | Route |
|---|---|---|
| Mixed-effects logistic regression | E3, E5 (all arms), E7, E8, E9, E10 | `summary`-step `Estimate`, `reported: true` |
| An average of two contrasts | E7's `AME_P` and `AME_U`, E9's mean over crossing magnitudes | `summary`-step `Estimate`. The cell-level contrasts underneath are declared and computed, so the evidence is checkable and the averaging is not — **and this is the refusal that reaches the study's own gate** |
| Cochran's Q | E5a, E8 | `summary`-step `Estimate`; core gives the pairwise contrasts, which after the plan's 2026-08-30 sharpening is what E8's primary now asks for |
| Conditional logistic regression | E4a | `summary`-step `Estimate`; the clustered flag-rate difference is what core computes, and is what the plan says it reports for that arm anyway |
| A binary decision compared against a scored model | E6 against the LLM; E2's curve against the model's operating point | A [`study`](reference.md#studies-what-a-paper-reports) joining two runs, with McNemar's at a matched positive rate as a step-computed number. DeLong is not the route because the plan dropped it: a model with a binary output contract has no ROC curve to compare |
| Gradient-boosted tree as an inferential object | E6 | Not refused — it is a swept `model.kind`; only the comparison *between* its discrimination and the LLM's is |
| Factorial main effects and interactions | E3's format × derivation interaction, E7's index, E9's band × magnitude | `summary`-step `Estimate`. A contrast compares two conditions; anything comparing two contrasts is an interaction |
| An omnibus test across three or more conditions | E5a, E8 | Same route; core's unit of comparison is the pair |
| A p-value for a paired binary flip count (McNemar's) | E4b, E5b, E5d | Half-refused: the delta and its paired interval are computed, the p-value is not. `statistics.null_test` gives a permutation p-value where the shuffled attribute is a design axis, which is E4a and not these |
| An exact one-sided bound on a discordant count | E5b's floor rule | `summary`-step `Estimate`. Core resamples a column; a rule-of-three bound is arithmetic on a flip count, and reporting "no effect" instead is what the plan pre-registers against |
| Holm across a family spanning several runs | `{E5a–d}`, `{E10 model contrasts}` | No route inside core. See [the gaps](#gaps-this-analysis-found-in-the-specification) |
| **No** correction, where the plan declares no family | E2, E3b, E4a, E4b, E6, E7, E9 | `statistics.correction: none`, which core accepts and warns about. The warning is correct on its own terms and wrong about this plan; see [gap 11](#gaps-this-analysis-found-in-the-specification) |
| A fixed-sequence gate protecting a study-level α | §0.7's gate, then the primary endpoint | No route. Both hypotheses land in the record as coordinate claims, and the ordering that makes the second readable only in the branch where the first opens lives in the `statement` field and in the paper |
| A contrast inside a single-condition run | E5c | `summary`-step `Estimate`; `report_by` describes the strata but produces no difference between them |
| Power analysis | The plan's whole Effect sizes section | Record the target effect size and the resulting n as parameters, so the calculation is part of the pre-registered config rather than a paragraph |
| Counterbalancing a per-unit condition order | E5b and E5d's "randomized order" | `replication.order: randomized` shuffles *executions*, not per-unit sequences. A true crossover carries the sequence as a unit attribute and fits period terms in a `summary` step |
| Adaptive selection of a serialization or a stimulus set | E3's and E1's decision rules | Not a route — a human decision between runs, by design |

The pattern across that table is worth naming, because it decides how the paper is assembled rather than how any one config is written: **core computes every quantity that is a mean or a difference of means over patients, and refuses every quantity that is a model fitted across them.** Twelve of the fourteen runs need at least one `summary`-step `Estimate`, and each such number is one an author computed and core carried without claiming — which `run.yaml` marks `reported: true` and a hypothesis's verdict marks `verdict_rests_on: reported`.

**What the restructure changed about that disclosure is that it now reaches the top.** Under the earlier plan the headline number was a ratio of two main effects and everything under it was computed; the same is true now, except that the plan has since named a **single primary endpoint and a gate**, and both of them are averages of contrasts. So the two most consequential numbers in the study are the two core stores without recomputing — while the four cell contrasts they are built from are computed, corrected and resampled. That is the right division and it is worth stating plainly rather than discovering at write-up: a reader who wants to check the index checks the four cells.

---

## Gaps this analysis found in the specification

These are the deliverable's second output: places where a real plan pressed on the schema and something gave. Each was measured; the measurements are in [§ Executability on this build](#executability-on-this-build).

**1. Closed — a `parameter_spec` path that is not exactly two segments now gets a diagnostic, not a traceback.** `"reference_frame"` and `"a.b.c"` used to raise `ValueError: _parameters_block only supports two-segment dotted paths (head.leaf)` as an unhandled traceback out of `generate experiment`; both are now refused at template-class load, before `@register_template` or anything else sees the class, as `E-TEMPLATE-PARAM-PATH`. [§ Templates](reference.md#templates-where-parameters-are-defined) now states the two-segment constraint directly, and [§ Errors `validate` reports](reference.md#errors-validate-reports) carries the row. The template written for this analysis renamed one parameter to work around the crash before the fix; that workaround is no longer necessary, but the renamed spelling is what this document's example still shows.

**2. Closed as a documented limitation, not by a mechanism — a correction family still cannot span runs, and two of the plan's four preregistered families do.** `{E5a–d}` covers four runs, because the four arms have four rosters and [a roster-changing variant is a different run](reference.md#where-units-come-from); `{E10 model contrasts}` covers five. `statistics.correction` is still computed within one run's condition set, and [`study add`](reference.md#what-study-add-redacts) still copies records without re-correcting across them — nothing in the code changed. `reference.md` § Studies now carries its own subsection, "A correction family does not cross a run," naming this exact boundary and the route available today: the author corrects by hand and states the family's level in the manuscript, while each run's own members still get the within-run family `correction.family_shape` already builds. A reader who wants a `study.yaml`-declared cross-run family with a computed adjusted level should not expect to find one — the gap closes by naming the limit, not by building the mechanism.

**3. Closed — a `sweep.baseline` that duplicates a `grid` cell now draws a warning.** Written the obvious way — `baseline: {stimulus.physiology: healthy}` beside `grid: {stimulus.physiology: [healthy, concerning], stimulus.schedule: [sparse, dense]}` — the E7 2 × 2 still expands to **six** conditions, of which `00_schedule=sparse__baseline` and `02_physiology=healthy__schedule=sparse` hold the same parameters and the same units in two directories, but `validate` now reports `W-SWEEP-CONDITION-DUPLICATE` on the pair. The check asks the direct question — do two conditions `expand` renders resolve to the same `values` over the same units — rather than naming only the group-axis route (`E-SWEEP-LEVEL-DUPLICATE`, `E-SWEEP-BASELINE-GROUP`) [two identical measurements reported as two arms](experimental-designs.md#mistakes-core-prevents) already refused; the parameter-axis form is the same mistake and is now caught by the general check. The message names the working spelling — fix the axis under test, leave the stratifying axis free — directly at the point of failure.

**4. Retracted — `W-DATA-CLUSTER-UNDECLARED` firing on a declared reporting stratum is not a gap.** `true_count_band` and `visit_band` each hold three labels over 300 units and are named in `statistics.report_by`, and both draw the undeclared-cluster warning; that half is true and [measured](#executability-on-this-build). What this entry got wrong is reading the firing as an omission. `_warn_undeclared_cluster`'s exclusions are documented — `reference.md` § Warnings core reports enumerates exactly four: an attribute a `sweep.groups` axis names or an `assign.from` reads, any `stratify_by`, and `statistics.null_test`'s `shuffle` — and `report_by` is deliberately not a fifth. The reason is in the function's own docstring: a run that reports by `site` while `site` really is a cluster wants both declarations, not silence, because a reporting stratum and a cluster identity are different facts about the same column and one can hold without the other. `true_count_band` and `visit_band` are not clusters here — no unit belongs to a correlated group by way of either — so both firings are the false positive the warning's own message already provides for ("ignore this if the units really are independent"), not evidence the exclusion list is short a name. A case for silencing `report_by` the way the other four are silenced would have to argue that a stratum can never also be a cluster, which is a design change against a documented decision, not a gap this analysis discovered.

**5. Closed — a fold level's `stratify_by` type is now stated.** `data.units.holdout.stratify_by` and `data.units.assign.<axis>.stratify_by` are lists in [§ The one config file](reference.md#the-one-config-file); a `{kind: fold}` level's is a string, and `[visit_decile]` still earns `E-REPL-FOLD-STRATIFY-UNKNOWN`. [§ Repeat kinds](reference.md#repeat-kinds) now names the field's type directly — `stratify_by` (`str | None`, naming **one** attribute, unlike the list form the other two take) — so the difference is documented rather than discoverable only by running into it.

**6. Partially closed — the documentation half is fixed; the resolver incompatibility is untouched and was never itself the gap.** `{by: calc_id, collapse: mean}` over a resolver roster still earns `E-RESOLVER-MEASUREMENT-FIELD` — the resolver must yield one `Unit` per measurement — and the same declaration still applies `mean` to the string-valued attributes, earning two `E-DATA-MEASUREMENTS-COLLAPSE-TYPE`; both diagnostics were correct behavior then and now, not a gap in themselves. What this entry actually found — that the config schema's one-line comment did not say `collapse` applies to **every** carried column rather than to the numeric ones — is fixed: [§ The one config file](reference.md#the-one-config-file) now states it directly, which is what makes the per-column map the documented ordinary case rather than something a reader discovers from the second error.

**7. Closed — `compare: {to: constant, value: N}` is now the absolute-threshold hypothesis form.** (The form
shipped in `v0.2.0`; the corrected bound described below landed in `v0.2.1` — see
[§ Executability](#executability-on-this-build).) A claim against a fixed reference — chance for an AUROC, zero for a difference already computed elsewhere, a regulatory floor — no longer has to route through a `summary`-step `Estimate` outside the correction family. The new form is core-computed from the metric's own per-condition value, `verdict_rests_on: computed`, and joins the [hypothesis family](reference.md#pre-registration) like a baseline comparison or a declared contrast, and gets a real corrected bound (`evaluate_on: ci95_lower`/`ci95_upper`) under `holm` or `bonferroni` too, wherever the metric's own raw interval exists. Two standing exceptions are recorded rather than hidden: a metric with no raw interval at all has nothing to correct, and a recorded column carried under both `weight_by` and `cluster_by` gets no correctable `Member` even though its raw interval exists — either way a bound test on it comes back `supported: null`, and `evaluate_on: observed` is the form to use there. **`fdr_bh` is not a third exception**, and the distinction matters for reading a null bound: Benjamini-Hochberg implies no per-comparison level, so no member of any kind carries a corrected bound under it — a `vs_baseline` delta and a declared contrast included. A bound-evaluated gate reads `supported: null` there whatever it compares, which is a prior condition on the promise rather than something a constant reference earns. The weighted-clustered residual is filed as its own `spec-defects.md` entry rather than left silent; the no-raw-interval case was never a gap, since a metric with no interval had nothing for `evaluate_on: ci95_lower` to answer either way.

**8. Closed — a resolver-yielded attribute the config does not declare is dropped, and the projection rule is now documented.** `Unit.attributes` carries only the declared `data.units.attributes`; `units.py` says so directly — "an attribute a resolver yields and the config does not declare is dropped, exactly as an undeclared CSV column is." [§ Errors `validate` reports](reference.md#errors-validate-reports) documents the **opposite** direction in two rows — declaring an attribute the source cannot supply is refused — and nothing documents this one. Found by running: every config declared only its stratifying columns, so `growth_dx_flag` and `clinician_concern` never reached a step, `step01_summarize_units` resolved an empty truth map, `step02_score` routed all 200 units to `io.skip`, and **the run still reported `status: completed`** with `n.ineligible` equal to the roster. There is no diagnostic for it and arguably cannot be a general one — core never reads a step body, so it cannot know which attribute a step will ask for. What was missing was the *documentation*, and [§ Where units come from](reference.md#where-units-come-from) now carries it beside the rule it mirrors — including the sharp edge, that declaring `attributes: [site]` for a `report_by` is also what stops your own steps seeing every other column in the extract. The remedy it states is the one this project had to apply to every config it wrote: **declare every column your steps read, not only the ones core reads.**

**9. Closed — a derived metric gets no unpaired contrast, and both the promise and the silence are fixed.** [§ Errors `validate` reports](reference.md#errors-validate-reports)' *Contrast has units in common* row says a comparison crossing a [group axis](reference.md#expansion-modes) "is unpaired instead, computed by `welch_t_over_units`/`unpaired_percentile_over_units` and their `_clustered` forms", with no carve-out for how the metric was produced. `cli.py` suppresses that branch for a **derived** metric on a stated ground — a recomputed metric would need `aggregate` evaluated on each side's independently drawn table, "a construction this build does not have" — so the contrast records `delta: null`, `method: null`, `paired: false` and both side counts, and the hypothesis reading it comes back `supported: null`. **The arm that found it is gone, and the finding is not**: E1 as this document first read it declared a contrast between two visit-count tertiles on a `kappa` its template derived, which is exactly this shape — a group axis, so no shared units, and a derived metric, so no column to close over. The restructure of 2026-08-30 retired that arm, so no config here now carries the shape; the diagnostic and the documentation it produced are what remain, and any plan comparing a derived metric across a group axis meets them. The code's reasoning is sound and the refusal is right; the gap was that a reader was told the construction exists, and then met a null delta beside two healthy side counts with nothing to attribute it to. Both ends are closed: the row now names the exception, and the suppression reports [`W-STATS-CONTRAST-UNPAIRED-DERIVED`](reference.md#warnings-core-reports), naming the two routes — record the quantity as a column, or carry the comparison as a `summary`-step `Estimate`. **`validate` could not have reported it**, and the reason is the one this analysis keeps meeting: whether `step02_score.kappa` names a derived key or a recorded column is a fact about what an `aggregate` *returns*, and core never reads a step body. At the suppression site, mid-run, it is known. Its run emitted the warning twice — once per metric `growth_label.aggregate` derived on that contrast — verified before the arm was retired.

**10. Closed — a hypothesis that reaches no verdict now records why, and says so while it is still fixable.** The sharpest failure this analysis produced twice: a pre-registered confirmatory hypothesis naming a metric the run never produced, resolving to `observed: null` / `supported: null` in total silence. The retired E1 hit it when `growth_label.aggregate` derived only `auroc` and the config named `step02_score.kappa`; E2 hit it when a `summary` step keyed its `Estimate` after the condition label (`auroc_baseline`) while the config named `auroc_count_only`. Two properties made it as bad as it was: `observed: null` covers **two** faults with different remedies — the metric was absent, or `compare: {to: constant}` named no `condition` on a run whose sweep resolved several — and nothing distinguished them; and core's run-time warnings are never written to `run.yaml`, so no warning alone would have reached the person reading the record. Both halves are closed: the entry carries [`unevaluable`](reference.md#pre-registration) — `metric_absent` or `condition_unresolved`, **absent** rather than null when there is a verdict — and [`W-HYPOTHESIS-UNEVALUABLE`](reference.md#warnings-core-reports) renders that field at run time, naming **every metric the step did record**, which is what turns *something is wrong* into *here is the typo*. It is not a `validate` row and cannot be: the step half of a metric name is already checked there by `E-HYPOTHESIS-METRIC`, and the key half is whatever a template's `aggregate` or a `summary` step returns — user Python, which core does not read. The general form of the second property — that no warning of any kind survives into the record — is closed too: every finding a run raises now lands in `run.yaml`'s own [`findings:` block](reference.md#the-two-files), redacted through the one implementation `Collector` gives both the screen and the record, and rendered by `report` as a `finding` row. The `diff` half of the original worry was measured false during scoping: `diff` reads five named rows and recurses only into the covered config, never the whole record, so a `findings` block that varies between two otherwise-identical runs changes nothing `diff` calls identical.

**11. The plan's notion of a family and core's are different objects, and a config can only declare one of them.** The plan pre-registers four families with explicit `m` — 3, 4, 3, and the roster size — and puts eight arms in **no family at all**, on the stated principle that a family exists to keep several *coordinate* tests from being read as one result, so where there is one primary quantity there is nothing to correct across. Core's family is [comparisons × metrics within one run](reference.md#sweeps-and-repeats): every non-baseline condition, every declared contrast, times every metric with an interval. The two disagree in both directions. In E10 core's family is nineteen comparisons per metric against the plan's five, which the plan's own effect-size table says is the difference between adequately sized and not. In E7 the plan's family is *empty* and core's is six per metric, and the only way to say "no family" is `statistics.correction: none` — which is accurate about what will happen and earns [`W-STATS-FAMILY`](reference.md#warnings-core-reports), a warning whose text ("every interval reported is uncorrected") is true and whose implication for this config is wrong. **Seven of the fourteen configs carry that warning by construction**, which is the shape of a warning a reader learns to skip. What would close it is not a suppression: it is a way for a config to say *which* comparisons are the family, so that a run declaring one primary quantity and four supporting ones corrects the first and reports the rest. Filed as `unassigned`, which in this project means it is what ships.

**12. A fixed-sequence gate has no expression, so the structure protecting the study's α lives outside the record.** §0.7 concludes on one quantity through one gate: reject the physiology main effect's null, and only then read the shortcut reliance index; no α is spent on the second step because it is read only in the branch where the first opens. Core has no ordering between hypotheses — both land in `run.yaml` as coordinate confirmatory claims, each with its own verdict, and nothing records that the second is unreadable if the first fails. The plan's own multiplicity families are described as families of *secondary* tests for exactly this reason, so the structure core cannot see is the one doing the study-level work. The route available is the hypothesis `statement` field and the manuscript, which is where it currently is. Filed as `unassigned`.

**What bounds this analysis has changed, and the change is worth recording.** The earlier version of this section said the cohort, the variable derivations, the model roster and the prompt were all undefined in the source, so no unit count could be checked as drawable and no cost figure given. **Three of those four are now defined**: the plan carries a Cohort and Data section with a 250,588-patient cohort profiled against a real snapshot, variable definitions for every backticked field, and a roster and prompt specification. Every sample size is now stated as a fraction of a named cohort and each is well under 1%, so the counts below are drawable rather than merely asserted. What is still missing is the only anchor a cost needs: **no prompt has been run, so there is no token count**, and multiplying an exact request count by a price is not something this document can honestly do.


---

## Executability on this build

A claim about what the tool *does today* is perishable in a way a specification claim is not, so
everything in this section is dated and pinned, and nothing outside it is a build claim. **This
section is re-measured whole rather than appended to**, so what follows is the current state and
not a log: every number below was produced by running the command named beside it at the commits
named here. Earlier measurements against earlier commits are in this file's git history, which is
where a superseded reading belongs.

### Measured on 2026-08-31 against `publishable` commit `57b7504`

Also pinned: the plan at `growth-chart-literacy@e6b43ab`, and the two sibling repositories at
`2026-08-28-gcl-measurement@4a2c1c0` and `publishable-growth-chart@1294b5b`. Pinning the plan's own
commit began with the previous measurement, and the reason stands: every earlier version of this
section named which `publishable` it had measured and never said which version of the plan it had
read, so a restructure that rewrote 1,070 lines of the source left every claim here reading as
current.

**The measured tree is two commits past the last release, and the record cannot tell you that.** Both
runs below write `publishable_version: 0.2.5`, because that field reports the installed
distribution's version and the two commits after `v0.2.5` — a name guard on `generate step` and
`generate experiment`, and `io.record`'s collision check reading the union over the roster rather
than its first unit — are unreleased. **That is the argument for pinning a commit rather than a
version in one sentence**, and it is worth reading beside the four release floors below: those tell
you what an install gets, and the pin tells you what was run.

Both sibling repositories install core as an **editable path dependency** with no version bound, so
they execute this working tree rather than a release — which is what makes the measurements below
current. The corrected bound these measurements depend on is **released in `v0.2.1`**: the
`compare: {to: constant, value: N}` form itself shipped in 0.2.0, but the correctable `Member` that
gives it a real corrected bound under `holm` or `bonferroni` landed after it, so an install of
`publishable==0.2.0` still evaluates such a hypothesis on a bound as `supported: null`. Take `0.2.1`
as the floor for the corrected bound, `0.2.2` for
[`W-STATS-CONTRAST-UNPAIRED-DERIVED`](reference.md#warnings-core-reports), `0.2.3` for
[`unevaluable`](reference.md#pre-registration) and its warning, and **`0.2.4`** for the persisted
[`findings:` block](reference.md#the-two-files), `report`'s `finding` rows, and `W-ENV-UNLOCKED` no
longer naming the repository path. Four floors for four releases, kept separate because a reader who
installs one of them gets exactly what that one shipped. **`0.2.5` adds a fifth floor to nothing**:
its whole change under the hashed trees is a lock around `load_experiment`'s `sys.modules` window,
which no config can observe.

**What moved since the 2026-08-30 measurement.** Two things, and they are of different kinds:

- **The prompt specification is implemented.** It was written in the plan and not in the code: the
  study sent one blob as a user turn, passed `system=None` at both call sites while the plugin's
  transport had implemented a system message per provider, never rendered the child's sex, and chose
  a reference frame it never stated. All four are closed, and the last clause of the same paragraph —
  *"any such difference [in message envelope] is recorded"* — with them. **The previous measurement's
  closing sentence, that the three prompt files "remain this analysis's own invention standing in for
  the plan's specification", is retired**: they now implement it.
- **Two core defects closed**, both found by asking this analysis's own question of core rather than
  of the plan. Neither is in a release yet; see the paragraph above.

**What was built to measure it.** A scratch experiment repository from `publishable new`, holding the
two project-local templates [listed below](#the-two-templates-as-loaded) in `templates/` (256 lines),
one `src/growth_chart/` package (3,461 lines over fifteen modules, seven step bodies and three prompt
files) with 2,882 lines of tests, **fourteen** configs, a 480-line input generator, and a
`publishable-growth-chart` plugin from `publishable plugin new` (429 lines, 621 of tests) installed as
an editable dependency — registering one resolver, one probe, and one writer/reader pair, and **no**
template. `uv run pytest`: **218 passed** in the measurement repository, **36** in the plugin.

**The inputs are two files per config**, `index.csv` and `visits.csv`, both generated by
`tools/example_inputs.py` — the only generator, since a second one writing a differently-sized set
beside it was deleted on 2026-08-30: two implementations of one specification eventually disagree,
and the disagreement is invisible until a run reports something odd. The trajectories come from the
study's own constructor rather than from a generator local to the tool, for the same reason.

**The fourteen configs, by running `publishable validate` on each.**

| Config | Result |
|---|---|
| `e02-utilization-baseline` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e03-serialization` | ✓ valid |
| `e03b-tokenization` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e04a-matched-pairs` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e04b-physiology-swap` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e05a-schedule-density` | ✓ valid |
| `e05b-graded-negative` | 0 errors, 1 warning — `W-DATA-CLUSTER-UNDECLARED` on `negative_stratum` |
| `e05c-fixed-n` | 0 errors, 1 warning — `W-DATA-CLUSTER-UNDECLARED` on `true_count_band` |
| `e05d-framing` | ✓ valid |
| `e06-comparator` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e07-two-by-two` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e08-ordering` | 0 errors, 1 warning — `W-DATA-CLUSTER-UNDECLARED` on `visit_band` |
| `e09-age-norm` | 0 errors, 1 warning — `W-STATS-FAMILY` |
| `e10-cross-model-2x2` | ✓ valid |

Four clean, ten carrying one warning each, **zero errors and zero of the fourteen refused** — the
same table the previous measurement produced, which is the point of running it again rather than a
reason not to have. Seven of the ten are `W-STATS-FAMILY` by construction: the plan puts those arms
in no multiplicity family, `statistics.correction: none` is the only way a config says so, and core
replies that every interval is uncorrected. That is true and it is not what the config meant —
[gap 11](#gaps-this-analysis-found-in-the-specification) — and ten of fourteen configs carrying a
warning is what a warning readers learn to skip looks like before anyone has learned to skip it.

**A widened refusal in core was checked against this project rather than assumed harmless.** One of
the two unreleased commits makes `io.record` refuse a recorded column shadowing **any** unit
attribute the roster carries, where it previously read only the first unit's — so a config that ran
before can now raise mid-execution. All fourteen still validate and both executable arms still
complete: this project's rosters carry every declared column on every row, so the widening reaches
nothing here. That is a measurement, not a reassurance about the change in general.

**`publishable dry-run` on each is where every execution count in this document comes from.** Across
the fourteen: **62 conditions, 450 executions, 106,260 unit-executions**, unchanged — the prompt
work moved what a request contains and not how many are issued. E3 still prints *19,500
unit-executions (65 executions × **300** units handed to each)* against a 600-unit roster, which is
`data.units.holdout` narrowing every denominator to the test partition, visible before anything
executes.

**Two configs have executed, and both reach a verdict.** E2 and E6 are the
[`growth_label`](#two-templates-because-there-are-two-experiment-types) arms — no LLM, so they run
without a deployment — and both were run with `publishable run` against a clean tree, so both records
are citable rather than drafts (`draft: false`, `git.code_dirty: false`):

| | Verdict | Rests on |
|---|---|---|
| [E2](#e2--the-utilization-baseline) | `auroc_count_only` **0.642**, `ci95` [0.605, 0.678] over 1,000 patients; `supported: true` on `ci95_lower` against 0.5 | `reported` — a `summary`-step `Estimate` |
| [E6](#e6--the-non-llm-comparator) | delta **0.0**, `ci95` [0.0, 0.0], `method: paired_percentile_over_units_clustered`, `n_paired: 595` over 300 clusters; `supported: false` | `computed` — core built the contrast |

**The numbers are the synthetic fixture's and mean nothing** — but E6's is worth reading anyway,
because a zero-width interval on a paired contrast looks like a defect and is not. The two arms are
`llm_matched` and `llm_matched_minus_count`, both fitted on a sample **matched on the pre-index visit
count**; each scores AUROC **0.891**, no cross-class ordering moves, and the difference is therefore
exactly zero in every one of the 2,000 draws. Withholding a feature the design equalized costs
nothing, which is what matching means — and the fixture had to be corrected before that sentence was
true, because its caliper was drawn on the referred member only, making the count systematically
higher in one arm. A one-sided caliper is an imbalance wearing the name of a tolerance. E6 also
reports `n.completed: 595` against a roster of 600 — five units carry an incomplete feature row and
land in `ineligible` — which is the four-way `n` doing its job on a run nobody was watching for it.

**Both records carry a populated `findings:` block**, each holding the `W-STATS-FAMILY` its own run
raised, at `level: warning`, with the message the screen printed. The block needs no contrivance to
populate here, which it did two measurements ago.

**The two arms that execute are the two the plan puts in no family**, which costs this measurement
something worth naming: **no executed run exercises a correction**. Every config declaring `holm` is
a screening arm needing a deployment. That is a property of the restructured plan rather than a
regression in core — the corrected path is exercised by core's own suite — and it is stated here
rather than papered over.

**What a deployment would receive, rendered through the real prompt file and the real serializer:**

```
=== SYSTEM ===
You are reviewing pediatric growth trajectories as part of a primary-care screening step.
… Percentiles and z-scores are stated against the CDC 2000 (LMS) reference. …
Answer with a single JSON object and nothing else: {"growth_issues": true}

=== USER ===
Sex: female

The measurements:

| age | weight z | height z | BMI | BMI pct |
| 3y3mo | -0.40 | -0.30 | 15.5 | 34 |
| 4y3mo | -1.60 | -1.40 | 15.0 | 12 |
```

Task, frame and output contract in the system message; trajectory, sex and age at each point in the
user message; nothing else. **No request has been issued to a deployment**, so this is a rendering
rather than a transcript.

**The plugin's three registries dispatch.** `data.units.from: {resolver: growth_trajectory}` resolves
every roster at `validate`; `apparatus_probe = "growth_llm_deployment"` is called at `dry-run` and its
facts recorded per condition. The `.transcript.jsonl` writer/reader pair is registered and its entry
points resolve at install, and **it is still not exercised by a write**, because the two runs that
have executed are the non-LLM arms — the suffix-dispatch rule it relies on is
[measured in the tutorial](tutorial-writing-a-plugin.md) rather than here.

**The credential check, measured on E10 with `.env` moved aside.** `validate` reports per condition
and by name: exactly `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` across the twelve Azure
conditions, and **nothing at all for the eight `ollama` conditions**, whose `requires_env` entry is
`[]`. The roster is what the plan's governance permits — three Azure deployments and two local
checkpoints — and an earlier roster's Anthropic arm, which demanded a third variable, is gone with it.

**The apparatus probe's unanswered facts, measured on E10 at `dry-run`.** The local arms' probe
returns `None` for both declared facts, in each `ollama` condition, and core reports it rather than
failing:

```
condition `03_schedule=sparse__provider=ollama__deployment=llama-4-70b__baseline`'s fact
`model_version` came back `null` on 1 of 1 probes
```

**Three refusals probed deliberately** at an earlier measurement, each by copying a config, editing
one line, and re-running `validate`. All three are properties of core rather than of the plan, and
none of them moved:

| Probe | Result |
|---|---|
| `sweep.grid` on a `list`-typed parameter — `llm.backoff_secs: [[2, 8, 30], [5, 20, 60]]` | `E-SWEEP-VALUE-UNNAMEABLE`: *swept value '[2, 8, 30]' does not match `^[A-Za-z0-9._+-]+$`* |
| A contrast naming the baseline by its swept value rather than `baseline` | `E-STATS-CONTRAST-UNKNOWN` alone, naming the label that matched no condition — one error, not two |
| `{kind: fold, k: 5, stratify_by: [visit_decile]}` | `E-REPL-FOLD-STRATIFY-UNKNOWN`: *a fold balances its folds on one declared attribute, named as a string* |

**What writing this pipeline against the plan has found.** Six things, none of them visible to
`validate`, to `dry-run`, or to reading:

**1. A specification written in prose and not in code fails silently, and the study's own prompt was
the instance.** The plan fixes one system message and one user message per case, with the reference
frame stated and the child's sex carried. The code sent one blob, `system=None`, no sex and no
stated frame — and nothing failed, because nothing could: a prompt is a string, and a string that is
missing a clause is still a string. **Sex is the one that would have changed answers**, since every
growth reference is sex-specific and E9's whole design rests on a peripubertal window defined
sex-specifically. This is the same defect class as [an unread parameter](#the-stimulus-arm-has-to-be-constructed-somewhere)
one layer out: there, a declared field no step read; here, a declared *commitment* no code read.
What closes it is the same shape too — the contract is checked at load, so a prompt that would render
identically for every unit is refused before the sweep is paid for.

**2. Deleting an experiment leaves an unread parameter behind, and the second-order effect is a check
that cannot fail.** E1's removal orphaned four surfaces at once — `model.kind: agreement`,
`truth.rater`, and the `kappa` and `agreement_raw` its template derived. Removing them was
straightforward; what was not is that `growth_label.validate`'s rule that a config fitting a model
needs a `holdout` or a `fold` was written as *unless the kind is `agreement`*, and with that kind
gone the exception is vacuous — the rule reads as conditional and is unconditional, and its test was
asserting a branch nothing can now reach.

**3. A derived metric recomputed on every bootstrap draw makes an O(n²) `aggregate` an O(n² × draws)
run.** `growth_label.aggregate` computed its AUROC by the pairwise definition, which is fine on a
100-unit roster and is two billion comparisons at E2's thousand units and 2,000 draws. The run does
not fail; it does not finish. The general lesson is core's rather than this template's: **a
template's `aggregate` is called once per resample per condition**, so its complexity is multiplied
by a number the config chooses.

**4. A holdout gives the estimate for free and refuses the selection.** Core narrows every
denominator to the test partition, which is exactly what E3's split is for — and it also means the
selection half is never screened, and a format selected on nothing is not a selection. The step asks
for `io.units.train` and screens it too, writing that half's accuracy as an artifact rather than
through `io.record`. Both halves are then reportable and only one of them is a metric.

**5. `io.units.train` raises rather than returning empty, and a step has to catch the right thing.**
Twelve of the fourteen configs declare no split at all, so the selection-half branch has to be
ordinary rather than exceptional. `E-STEP-UNITS-UNAVAILABLE` is the direct question — *is a split
declared* — and a bare `except Exception` around it would have answered *did anything go wrong in the
partition*, which is [the same substitution](../CLAUDE.md#answering-a-question-with-a-proxy) in
another guise.

**6. A quantity computed for the wrong arm is worse than one not computed.** E5b's floor rule — the
one-sided bound on the excess false-positive rate — is arithmetic on a discordant pair count, and
every two-condition screening arm produces those counts. Gating it on the *shape* of the sweep would
have reported E4b's and E5d's flips as false positives, which they are not; the gate is on the arm's
own `stimulus.physiology` being `true_negative`.

**What is still not measured.** Twelve of the fourteen have not executed, because they need a
deployment: `resume`, `report`, `freeze`, `diff`, `study` and `reproduce` remain unexercised, the
`.transcript.jsonl` writer has never been driven by a write, no `envelope` has been recorded from a
real call, and every cost figure below is arithmetic rather than an anchor. **What blocks that is not
in the plan and not in this tooling** — the cohort, the variable derivations, the roster and the
prompt are all specified now, and the prompt is implemented — it is a deployment, a credential, and
a study that is pre-data by design.

### The two templates, as loaded

Both are read by `list-templates`, materialized by `generate experiment`, and enforced by `validate`
at the commit this section is measured against.

```python
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
                                          "synthetic_schedule", "synthetic_negative"]),
        "stimulus.physiology": Param(str, default="as_recorded",
                                     choices=["as_recorded", "concerning", "healthy",
                                              "true_negative"]),
        "stimulus.schedule": Param(str, default="as_recorded",
                                   choices=["as_recorded", "sparse", "typical", "dense"]),
        "stimulus.crossing_channels": Param(float, default=2.0, ge=0.0, le=5.0),
        "stimulus.resample_noise": Param(
            str, default="matched", choices=["matched", "none"],
            help="Noise-matched resampling: interpolated points carry the within-child "
                 "SD, so a dense arm is not identifiable by being smoother"),
        "stimulus.height_availability": Param(
            float, default=0.538, gt=0.0, le=1.0,
            help="Share of displayed visits carrying a height, held at the cohort rate "
                 "in every density arm so densifying does not also complete the record"),
        # --- ground truth and scoring ---
        # `referral` is the only EHR-derived label the plan still uses for an
        # accuracy claim, and it reaches one screening arm: E4a, in Layer C.
        # `by_construction` is Layer A's, and `none` is Layer A's other half —
        # E5a, E5c, E5d, E7 and E10 report whether the model's own answer MOVED
        # under a controlled perturbation, which needs no correct answer at all.
        "truth.label_source": Param(str, default="by_construction",
                                    choices=["by_construction", "referral", "none"]),
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
        # A synthetic arm carries no EHR referral, so its truth is by
        # construction — or, where the arm reports only whether the answer moved,
        # nothing at all. `referral` is the one value a constructed trajectory
        # cannot carry, since no clinician ever acted on a child who does not
        # exist.
        if stim.get("source", "observed") != "observed" and \
                truth.get("label_source") not in ("by_construction", "none", None) and \
                "truth.label_source" not in swept:
            errs.append("a synthetic `stimulus.source` has no EHR referral: "
                        "`truth.label_source` must be `by_construction` or `none`")
        # A shuffled order without a declared permutation is one shuffle pretending to be five.
        if ser.get("order") == "shuffled" and "serialize.permutation" not in swept and \
                "serialize.order" not in swept:
            errs.append("`serialize.order: shuffled` needs `serialize.permutation` swept, "
                        "or the run measures one arbitrary shuffle")
        return errs

    def aggregate(self, units, cfg) -> dict:
        """What the screening arms claim, derived from the per-unit table.

        **`flag_rate` is computed wherever a flag was recorded, with or without a
        truth column, and that split is the restructure of 2026-08-30 landing in
        code.** Five arms — E5a, E5c, E5d, E7 and E10 — report whether the
        model's own answer moved under a controlled perturbation, which is a
        within-subject question with no correct answer to score against. Deriving
        `accuracy` there would need a label those arms deliberately do not carry,
        and returning `{}` for want of one would leave their primary quantity
        underived and every contrast in them empty.
        """
        flagged_rows = [r for r in units if r.get("flagged") is not None]
        if not flagged_rows:
            return {}
        out = {"flag_rate": sum(1 for r in flagged_rows if r["flagged"]) / len(flagged_rows)}
        rows = [r for r in flagged_rows if r.get("truth") is not None]
        if not rows:
            return out
        n = len(rows)
        tp = sum(1 for r in rows if r["flagged"] and r["truth"])
        fp = sum(1 for r in rows if r["flagged"] and not r["truth"])
        fn = sum(1 for r in rows if not r["flagged"] and r["truth"])
        tn = n - tp - fp - fn
        po = (tp + tn) / n
        pf = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / (n * n)
        out.update({
            "accuracy": po,
            "kappa": (po - pf) / (1 - pf) if pf < 1 else None,
            "sensitivity": tp / (tp + fn) if (tp + fn) else None,
            "false_positive_rate": fp / (fp + tn) if (fp + tn) else None,
        })
        return out
```

```python
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
        # `agreement` is gone with the restructure of 2026-08-30: it computed a
        # kappa between the EHR label and a clinician panel, and no arm does that
        # any more — the panel validates constructed stimuli and never adjudicates
        # the cases a model or a comparator sees. What is left is two fitted
        # comparators, which is what Layer C asks this template for.
        "model.kind": Param(str, default="logistic",
                            choices=["logistic", "gbt"],
                            help="Which comparator is fitted on the shared feature set"),
        "model.feature_set": Param(
            str, default="count_only",
            choices=["count_only", "count_spacing_span", "llm_matched", "llm_matched_minus_count"],
            help="Named feature set; a swept value must render [A-Za-z0-9._+-]+, so it is a name and not a list"),
        "model.max_depth": Param(int, default=3, ge=1, le=12,
                                 help="gbt only; ignored by the other two"),
        # One choice, and the single-valued list is the point rather than an
        # oversight: the plan pre-registers the Layer C outcome (item 5), and the
        # two labels this parameter used to admit were both removed as outcomes
        # by the restructure — `growth_dx_flag` because it is predominantly
        # perinatal, `clinician_consensus` because the panel no longer adjudicates
        # these cases. A parameter that can be swept back to a retired outcome is
        # how a decision gets un-made by a config edit.
        "truth.label_source": Param(str, default="referral", choices=["referral"],
                                    help="The referral action label, on a matched index date"),
        "frame.reference": Param(str, default="cdc2000", choices=["cdc2000", "who2006"]),
    }

    def validate(self, config) -> list[str]:
        """Every arm of this template fits a model, so every arm needs a split.

        The rule used to be conditional on `model.kind` — `agreement` fitted
        nothing and so needed nowhere to fit. That kind is gone, which makes the
        rule unconditional rather than absent: a config fitting a comparator on
        the units it will be tested on is the cross-block fault a template exists
        to catch, and no `E-` code catches it, because core does not read a step
        body to learn that one is being fitted.
        """
        units = (config.get("data") or {}).get("units") or {}
        folds = [r for r in ((config.get("replication") or {}).get("repeats") or [])
                 if r.get("kind") == "fold"]
        if not units.get("holdout") and not folds:
            return ["this experiment type fits a model, so it needs a "
                    "`data.units.holdout` or a `{kind: fold}` repeat to fit on"]
        return []

    def aggregate(self, units, cfg) -> dict:
        """Derive what each arm claims, from the per-unit table.

        One metric now, where there were three: the label-agreement arm and its
        `kappa` went with E1's rewrite, and a metric with no arm reading it is an
        unread surface of the kind this project keeps producing. What is left is
        the comparators' discrimination.

        Derived here rather than returned by the step because that is the only
        route to a real interval: core can recompute a derived metric on a
        resampled table, so `auroc` is `basis: units` with a percentile ci95 over
        the declared draws. A step-returned scalar would be `basis: repeats` with
        no interval at all.

        `{}` for a table holding no score is the right answer rather than a
        fault: core calls `aggregate` once per recording step, and a pipeline can
        have several.
        """
        out: dict = {}

        # E2 and E6: discrimination of the fitted comparator.
        rows = [r for r in units if r.get("score") is not None and r.get("truth") is not None]
        pos = [r["score"] for r in rows if r["truth"]]
        neg = [r["score"] for r in rows if not r["truth"]]
        if pos and neg:
            out["auroc"] = self._auroc(pos, neg)

        return out

    @staticmethod
    def _auroc(pos: list, neg: list) -> float:
        """The rank form of the Mann-Whitney statistic, ties at midrank.

        Rank-based rather than the pairwise double loop it replaces, and the
        reason is not tidiness: core recomputes a derived metric on every
        resampled table, so an O(n^2) `aggregate` is O(n^2 x draws) per
        condition. At E2's thousand units and 2,000 draws that is two billion
        comparisons and a run that never finishes — measured, not predicted.
        """
        scores = sorted((s, i) for i, s in enumerate(pos + neg))
        ranks = [0.0] * len(scores)
        i = 0
        while i < len(scores):
            j = i
            while j + 1 < len(scores) and scores[j + 1][0] == scores[i][0]:
                j += 1
            midrank = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                ranks[scores[k][1]] = midrank
            i = j + 1
        rank_sum = sum(ranks[: len(pos)])
        n_pos, n_neg = len(pos), len(neg)
        return (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
```

---

## Cost and execution summary

| Run | Units | Conditions | Repeats | Executions | Metered requests |
|---|---|---|---|---|---|
| E2 `e02-utilization-baseline` | 1,000 | 2 | 5 folds | 12 | 0 |
| E3 `e03-serialization` | 600 (300 held out) | 9 | 5 | 65 | 27,000 |
| E3b `e03b-tokenization` | 150 | 2 | 5 | 16 | 1,500 |
| E4a `e04a-matched-pairs` | 600 | 2 | 5 | 16 | 3,000 |
| E4b `e04b-physiology-swap` | 250 | 2 | 5 | 16 | 2,500 |
| E5a `e05a-schedule-density` | 200 | 3 | 5 | 23 | 3,000 |
| E5b `e05b-graded-negative` | 200 | 2 | 5 | 16 | 2,000 |
| E5c `e05c-fixed-n` | 300 | 1 | 5 | 9 | 1,500 |
| E5d `e05d-framing` | 300 | 2 | 5 | 16 | 3,000 |
| E6 `e06-comparator` | 600 | 4 | 5 folds | 22 | 0 |
| E7 `e07-two-by-two` | 200 | 4 | 5 | 30 | 4,000 |
| E8 `e08-ordering` | 300 | 7 | 5 | 51 | 10,500 |
| E9 `e09-age-norm` | 440 | 2 | 5 | 16 | 2,200 |
| E10 `e10-cross-model-2x2` | 200 | 20 | 5 | 142 | 20,000 |
| **Total** | | **62** | | **450** | **80,200** |

**Executions** are what `dry-run` printed — a build claim, so the run of it that produced these numbers is dated in [§ Executability on this build](#executability-on-this-build) — counting every step's executions including the `run`-scoped roster summary and the `summary`-scoped comparison. **Metered requests** are conditions × repeats × units at the one `scope = "repeat"` step that issues a request, with **E3 the exception that proves the rule**: its roster is 600 and its unit-executions are counted over the 300-unit test partition, but the step screens the selection half as well, so the meter sees all 600. A holdout is free in the record and not on the meter.

**Where these figures agree with the plan's own, and where they cannot.** E3's 27,000, E4b's 2,500, E5a's 3,000, E5d's 3,000, E7's 4,000, E8's 10,500 and E9's 2,200 are the plan's own evaluation counts reproduced exactly, which is the arithmetic check that the translation preserved each design's structure rather than its description. E10's is not comparable: the plan replicates five arms across the roster where budget allows and prioritizes two where it does not, and this config is the prioritized E7 replication.

**The full E10 is several times what the table shows.** Replicating E4b, E5b, E8 and E9 across the same five-deployment axis adds 12,500 + 10,000 + 52,500 + 11,000 = 86,000 requests, for **166,200** in total. The plan's own budget rule — prioritize E7 and E5b — is therefore a choice between roughly 80,000 and 166,000, which is the number that decision should be made against.

**The restructure moved this total, and mostly in one direction.** Against the fifteen-config reading of the earlier plan the total was 62,000; it is 80,200 now. Three changes account for nearly all of it and each is a design decision rather than an overhead: **E3 doubled** because the plan added a 300/300 split and both halves have to be screened, **E10 grew by a quarter** because the roster went from four deployments to five, and **E9 shrank** because its magnitude sweep collapsed into one matched contrast. The reference-standard gate's removal costs nothing here — it never issued a request — and saves several thousand clinician-adjudicated curves elsewhere, which is the trade the plan actually made.

**No condition set comes near `limits.max_executions: 500`.** The largest is E10, whose 20 × 5 = 100 repeat-scoped executions come to 142 once every scope is counted — and it is the 100 that the check compares against the budget, not the 142. No config drew [`W-EXEC-BUDGET`](reference.md#warnings-core-reports), which is the warning that comparison raises and the only one this paragraph claims: ten of the fourteen carry a warning of another kind, as [§ Executability on this build](#executability-on-this-build) records. That is worth noting because it inverts the usual worry: what constrains this plan is the request count inside each execution, not the number of executions, and core's execution-count guard is not the limit that will bind.

**What none of this says is what it costs.** The plan now specifies its roster and its prompt, so what is missing is no longer a specification — it is that **nothing has been run**, so there is no token count per request and a price per request would be invented rather than measured. What is measured is that a request is issued once per patient per condition per repeat, that every one of them lands in the unit table with its own `prompt_tokens`, `completion_tokens` and `latency_ms`, and that the first run to execute against a deployment will therefore produce the anchor this section lacks.

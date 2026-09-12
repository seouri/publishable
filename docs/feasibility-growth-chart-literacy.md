# Feasibility analysis: growth chart literacy

`growth-chart-literacy` asks one question: **when a language model screens a pediatric growth trajectory, is it reading the curve, or is it counting how often the child came in?** Ten experiments answer it around a triad no published study combines — clinician-validated stimuli, a physiology-preserving counterfactual, and a utilization-invariance counterfactual.

**Read against the plan at commit `22d1b24`.** The restructure of 2026-08-30 is the design this reads; a further eight commits to 2026-09-10 profiled the snapshot for recording artifacts, restated the generator on the age-2-or-later window, built the generator and then the clinician panel's chart renderer in the study repository, assembled the evidence two preregistration items rest on, and — on the last day — **anchored every data figure in the plan on one named database digest**, after a headline AUROC pair was found to have been measured over a population the plan rejects. The plan now sits in three layers: a **counterfactual core** whose claims are within-subject and read no EHR label at all, a **clinician panel** validating the constructed stimuli, and a secondary **accuracy layer** on a referral outcome that is positive-unlabeled. Every trajectory is drawn from age 2 onward. This analysis is re-derived against that plan rather than patched onto the earlier reading, and where a conclusion here changed, the section says what it replaced — an earlier version of this document is in its git history.

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

The plan is at plan stage — no experiment in it has been run — so this table is not a list of code to delete. It is the list of machinery the plan **commits to building** in prose, and would not have to. It is also the list of things the proposed plugin must **not** rebuild.

**Two rows below record a convergence rather than a gap, and they are the most useful rows in the table.** On the utilization covariate and on what repeated runs buy, the plan reached this tool's position on its own, from its own data, between the first version of this analysis and the restructure of 2026-08-30. A feasibility analysis whose predictions the subject project independently confirms is stronger evidence than one that only lists what fits.

| Committed to in the plan | Core equivalent |
|---|---|
| The reference frame, now **settled** at CDC 2000 because the age floor determines it, and registered anyway "precisely because Ahmad et al. show how much rides on it" | A `Param` with `choices=["cdc2000", "who2006"]`, inside [`parameters_hash`](reference.md#three-hashes). The plan's own reason for registering a settled choice is core's reason for keeping it a parameter: the frame follows from the age floor, so **lowering the floor must not change the frame as a side effect** — and a config in which both are declared cannot move one silently |
| "Eight pre-data commitments alter downstream design and must be registered before data collection" (§Preregistration) | [`hypotheses`](reference.md#pre-registration), each carrying the declaring config's `parameters_hash`, so anything added after the run renders as exploratory |
| "Holm-Bonferroni within each experiment family", with four families now declared and their `m` stated — 3, 4, 3, and the roster size — and **every other arm in no family at all** | [`statistics.correction: holm`](reference.md#sweeps-and-repeats), with the family size and its breakout recorded beside every interval. Two mismatches, both now measured: a family **cannot span runs**, which {E5a–d} needs, and core's family is *comparisons × metrics within one run*, which is a different and usually larger object than the plan's `m`. Declaring `correction: none` is how a config says "no family" and it earns a warning for saying it; see [the gaps](#gaps-this-analysis-found-in-the-specification) |
| "Bootstrapped CIs … resampled at the patient level, not the observation level" | [`statistics.resample`](reference.md#what-isnt-a-repeat) over the per-unit table, where the unit *is* the patient by construction |
| **Retracted by the plan itself.** An earlier §Power basis credited the k = 5 repeated runs with raising effective power; it now says "the k = 5 repeated runs buy no power, and nothing here credits them with any" | Repeats never enter `n`. Five seeds give a [`repeat_spread`](reference.md#repeat-kinds), and `n` counts units. This analysis said so before the plan did, and the plan reached it from the other end — that repeats within a case are highly correlated and are *identical* on local weights at a fixed seed. **The rule and the reason now agree**, which is the strongest form this row could take |
| **Also retracted, and measured.** `visits_count_pre_dx` was the universal control; profiling found it truncates at the diagnosis for cases and equals the lifetime count for controls, running at AUROC 0.075 against 0.488 — the latter being no separation at all, so the field's replacement is not a repair of a working comparison but a change of quantity. **The plan carried 0.131 against 0.745 until 2026-09-10**, figures that reproduce exactly on a case-control subset it rejects elsewhere and not at all on the cohort; that correction is what installed its measurement anchor. The plan replaced it with a **pre-index count on a matched index date** and says "the plan does not use this field" | A unit attribute either way: matched by [`cluster_by`](reference.md#clustered-units), stratified by [`report_by`](reference.md#reporting-strata), manipulated as a swept parameter — three spellings for the three things the plan does with it. What the tool never had was an opinion about *which* column; what it does have is [`input_manifest_hash`](reference.md#three-hashes) over the extract the column came from, so the replacement is legible in the record rather than in a methods paragraph |
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

**What one repository costs is real, and it runs both ways between E2/E6 and the screening arms.** Those two fit scikit-learn models and import no LLM machinery, so every commit to their code moves the recorded `code_hash` of screening runs that never called it — **and every commit to the screening side moves theirs, which is the half this paragraph missed until it happened.** `code_hash` covers `src/**` and `templates/**` whole; it has no notion of which module a run called, so the traffic is symmetric by construction. The same symmetry holds for the blocking half: while E2's or E6's code has uncommitted edits [`run` refuses to start](reference.md#operation-commands) the twelve-hour E10, and while the serializer or the generator has uncommitted edits it equally refuses to start E2. Three ways out, with the bill attached to each:

| Option | What it costs |
|---|---|
| One repository, E2/E6 code frozen before E4 starts | The discipline is a human commitment again — exactly the kind of thing this tool exists to stop relying on |
| One repository, `draft` for E2/E6 iteration | [`draft`](reference.md#draft-runs) permits a dirty tree and marks the run non-citable, which is right for developing a comparator and wrong for the comparator run that goes in the paper |
| A second repository for E2 and E6 | Their `code_hash` is then unrelated to the screening runs', which is honest — they measure a different apparatus — but E6's comparison against E4a's LLM becomes a cross-repository [`study`](reference.md#studies-what-a-paper-reports) rather than a contrast |

**The default is the first, and the tree above is drawn that way** — one repository, fourteen configs — because the cost only becomes real while either side is still being written and the other has runs on the record — a condition that, like the trigger below, was first written with E2 and E6 as the only ones doing the writing. **The trigger for taking the third is stated rather than judged, and it names no direction**: the first time a commit made for one side's sake moves the `code_hash` of an already-reported run on the other, or blocks one from starting, E2 and E6 move to a repository of their own. **It said *comparator commit* and *screening run* until 2026-09-12**, which read naturally because one repository exists to buy E4 through E10 their shared-hash claim and comparator runs have no analogous claim to lose — so the damage looked like it could only flow one way. That is an asymmetry of *stakes*, not of mechanism, and writing it into the condition left the trigger blind to half the cases it was written for.

**It has since been met, in the direction it did not name.** Realigning the generator on 2026-09-12 moved E2's and E6's already-reported `code_hash` from `6f474d8…` and `097865f…` to a shared `018273d…`, with every reported number identical. The remedy addresses it: E2 and E6 run `SummarizeUnits`, `Score` and `CompareLabel` and reach `construct.py` through none of them, so under a split it stays in the screening tree and can no longer move their hash. **Acting on it is the study repository's decision and not this document's** — a feasibility analysis states a trigger; it does not carry out a repository split. The plan's own OI-12 argues they belong there anyway — it says E6 is a utility comparator and not an ablation of the LLM, and a comparator sharing no code with the thing it is compared against is the accurate expression of that. **What has changed is which arms carry the risk.** Under the earlier plan E1's clinician labels were the ground truth every screening run consumed, so the label pipeline was upstream of everything; now E2 and E6 are Layer C, secondary, and *nothing in the counterfactual core reads what they produce*. A repository split would therefore cost less than it used to and buy the same thing, which strengthens rather than weakens the trigger above.

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

`growth_screen` declares six parameters that describe **what trajectory the model is shown** rather than how it is rendered — `stimulus.source`, `stimulus.physiology`, `stimulus.schedule`, `stimulus.crossing_z`, `stimulus.resample_noise` and `stimulus.height_availability` — and six of the fourteen configs sweep one or both of the first two as *the axis under test*: [E4b](#e4b--the-physiology-preserving-counterfactual), [E5a](#e5a--the-schedule-density-ladder), [E5b](#e5b--the-graded-negative-control), [E7](#e7--the-2--2-synthesis), [E9](#e9--age-dependent-norm-application) and [E10](#e10--cross-model-generalization).

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

**The z path is the plan's own generator, not this analysis's invention, and that changed on 2026-08-30.** §Cross-Cutting now specifies `z(a) = b + d(a) + e(a)`: a characteristic channel `b ~ N(0, 0.9²)`, a deviation `d(a)` entered over a window rather than as a step, and within-child variation `e(a)` as an AR(1) process at marginal SD 0.42 and lag-1 correlation 0.57, calibrated so the simulated statistics reproduce the cohort's measured 0.925, 0.349 and 0.921 on the age-2-or-later window. The pooled lag-1 figure is the load-bearing one because it mixes both variance components and so cannot be matched by tuning either alone. **These are the third set this paragraph has carried, and the first two were live here after the plan retired them** — it described `N(0, 0.84²)`, marginal SD 0.49 and a pooled 0.869 until 2026-09-12, which are the *all-ages* statistics R41 withdrew on 2026-09-05 when the study scoped itself to age 2 and later. **Parameters are not their targets**, which is the distinction R41 exists to draw: a patient's mean carries residual variation, so the between-child SD of patient means exceeds `σ_b`, and a within-sample SD understates the marginal `σ_e` of a positively autocorrelated series. Reading the measured statistics straight in as parameters misses in both directions at once, and this paragraph did it. Two consequences for a translation:

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
def probe(cfg, *, fetch=_http) -> Apparatus:
    return Apparatus(facts=deployment_facts(cfg, fetch=fetch))   # one metadata read, never a completion
```

```python
    apparatus_probe = "growth_llm_deployment"
    apparatus_facts = ["model_version", "system_fingerprint"]
```

Core calls it at `dry-run`, at run start, before every execution and at `freeze`, and **a fact that moves from its first answered observation fails the run**. That gate is what a growth-chart study most needs and least has: a hosted deployment re-tuned in the middle of E10 would otherwise be reported as cross-model heterogeneity. A fact the probe cannot answer is recorded `null` and counted rather than read as a change.

**What each fact is, and why one of them is never answered here.** The probe reads a *metadata* endpoint rather than issuing a completion, because core probes before every execution and E10 has 142 of them. What moves under a stable name differs by provider and each is read for what it is: an Azure deployment name is site-specific and says nothing about the model behind it, so the model is what is read there, and a local checkpoint has no version string and does have a digest — the plan's own *"weights revision or hash"*, and what a swapped model file moves.

**`system_fingerprint` is `None` from every probe, and that is a property of the fact rather than a gap in the implementation.** It is returned on a completion response and by nothing else, so no metadata read can produce it — and a probe that guessed one would put a fabricated fact under a gate that *fails runs*. So the two halves of the plan's per-call provenance requirement land in two places: the model version is an apparatus fact under the gate, and **the fingerprint is logged per call** in the request transcript, from the response the transport already parses. The plan asks for the fingerprint per call anyway, on the grounds that *"a fingerprint that changes mid-study is a silent covariate on everything collected after it"*; what this arrangement adds is that the *other* fact cannot drift unnoticed at all.

**A probe that cannot reach its endpoint answers `null` rather than raising**, including when a credential is absent, and the cost of that choice is worth stating because it was paid: an endpoint permanently unreachable yields `null` forever, an unanswered fact is outside the gate, and **a single `null` cannot distinguish a wrong hostname from an unserved path from a stale api-version** — which is exactly the three-fault stack that took a day to unpick the first time this probe met a real resource. Core's per-condition count of unanswered observations is what keeps that visible, and `validate`'s own credential refusal — by variable and by condition — is the better diagnostic for the case that actually recurs. All of this is a build claim, and it is [dated below](#executability-on-this-build).

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

**Its items are constructed now, and that is what took the EHR label out of E3.** E3 scores classification accuracy, accuracy needs a correct answer, and on a real patient that answer would have to be an EHR label — which is what used to make E3 wait on E1's adjudication of that label. Drawn from the same synthetic family as E4b, the answer is known by construction: `truth.label_source: by_construction`.

**It does not follow that nothing is upstream of E3, and this document said so for nine days.** The panel validates stimulus *categories*, and E3 draws its items from them, so **E3 inherits that validation and waits on it** — settled in the plan on 2026-09-09, which resolved four passages that had disagreed about exactly this. The consequence is a scheduling one and it is the sharpest fact in the dependency graph: E3 is the root of the core, so **the panel sits on the critical path to every Layer A arm**, and a category sent back for regeneration delays the core rather than three arms.

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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
- **Interpolated with a monotone spline**, which the plan asks for by name and which is a fourth constraint of the same kind rather than a numerical preference. A dense arm displays twenty points resampled from about six, so a linear interpolant renders it piecewise-linear between the real visits — collinear runs with visible knots — and the three-point sparse arm cannot carry that structure. *Monotone* matters separately: an ordinary cubic overshoots near a plateau followed by a drop, and an overshoot on a z path is a percentile crossing the child never had, invented by the resampling in the arm whose claim is that the physiology did not move.

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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.0
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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

**The roster is swept by deployment name, and this is where a real roster met that rule.** A swept value becomes a condition-directory name, so it must render `[A-Za-z0-9._+-]+`. The three Azure names the study will run — `gpt-4.1`, `gpt-5`, `gpt-5.6-sol` — pass; **the two local ones did not**, because an Ollama tag carries a colon, and `gemma4:12b` earns two refusals at `validate`: `E-PARAM-VALUE` against the template's own `pattern` and `E-SWEEP-VALUE-UNNAMEABLE` against the sweep rule. Both are [measured below](#executability-on-this-build).

**The fix is worth stating because the obvious one is worse.** Sweeping an alias and resolving it to a tag in code needs a table that **two** readers consult — the request path and the apparatus probe, which asks the same endpoint what model it is — and a table stating one fact twice is what this analysis keeps filing against. So the alias is made where naming is free, in the local model registry (`ollama cp gemma4:12b gemma4-12b`), and one name means one model in the config, the condition directory, the request and the digest the probe reads back. A study whose deployments are addressed by a path that *cannot* be aliased at the registry is the case that still needs resolution in the step.

**What licenses that fix is a measurement, not the argument above it.** An alias is only free of consequence if it moves no fact, and the fact here is a hash: `ollama cp` writes a second manifest over the same blobs, so the copy probes to the original's digest, [measured below](#executability-on-this-build) for both checkpoints. Had they differed, the apparatus gate would have been watching a tag that exists on one machine, and the honest fix would have been the worse one — a resolution table with two readers. **The registry-alias fix and the table fix are not interchangeable, and which one is correct is an empirical question about the registry**, which is the part of this that generalizes past Ollama.

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
    deployment: gpt-5.6-sol
    temperature: 0.0
    max_output_tokens: 8192
    request_timeout_s: 2400
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
    crossing_z: 0.67
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
    - {llm.provider: azure_openai, llm.deployment: gpt-4.1}
    - {llm.provider: azure_openai, llm.deployment: gpt-5}
    - {llm.provider: azure_openai, llm.deployment: gpt-5.6-sol}
    - {llm.provider: ollama, llm.deployment: gemma4-12b}
    - {llm.provider: ollama, llm.deployment: qwen3.5-9b}

replication:
  repeats:
    - {kind: seed, n: 5}
  order: randomized
  rationale: "Four deployments crossed with the 2×2; provider and deployment move together, so they are one axis and not a product."

statistics:
  correction: holm
  resample: {method: bootstrap, n: 2000}
  contrasts:
    - {id: utilization_gpt41, of: "schedule=dense__provider=azure_openai__deployment=gpt-5__baseline",
       against: "schedule=sparse__provider=azure_openai__deployment=gpt-5__baseline"}

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

**The stimulus-validation panel, which used to be E1, and which gates more than it appears to.** What it validates is a *category* — E4b's two conditions, E5b's three negative strata, E9's two bands — and **an arm drawing its items from a validated category inherits that validation**, so E3 and E8 are gated by a panel whose sample contains no E3 or E8 curve. That reading was settled on 2026-09-09 after four passages of the plan disagreed, and it is what puts the panel on the critical path to the whole core.

**The panel itself.** Two to three blinded pediatricians independently adjudicating roughly 110 plotted curves, mixed with real ones as a realism check, is not something core executes. The earlier design — a 200-curve adjudication of an EHR label — at least produced a column a run could read; this one does not produce a column at all. The panel confirms that the constructed stimuli mean what they were built to mean, and its outcomes are a **gate a person passes**: a category whose consensus falls below 90% is regenerated and the arm consuming it is not run. Nothing about that reaches a config, and the two statistics the plan asks for — per-category agreement with exact binomial intervals, and the panel's ability to separate synthetic from real — are computed over pictures no run has units for.

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

**13. Closed — a diagnostic named a directory the config was not in.** `E-NAME-DIR` compares
`metadata.name` against `config_path.parent.name` and asks nothing about where that parent sits, but
its message read *is `<name>` under `configs/<dir>/`* unconditionally. Every config in this study
lives under `configs/`, so the defect was invisible until the smoke config above was put under
`smoke/local-gemma4/` and the refusal claimed a path that did not exist. **A message that misreports
the file's own location is the worst kind to be holding when you are trying to find it**, and this
one asserted a convention the check does not enforce. The prefix is gone; the check is unchanged.
The same reading applies to two of this document's own earlier measurements, which attributed an
`E-NAME-DIR` to "the config not living under `configs/<name>/`" — the cause is `name` disagreeing
with the directory, whatever the directory is called, and those two lines are dated readings left
as they were written.

**14. Closed — `resume` could not read any artifact a completed step had written.** `execute_plan`
derived its step-scope map as `{e.step_name: e.scope for e in plan}`, and `command_resume` narrows
that plan to the triples that have not completed. A step whose executions all finished before the
crash was therefore absent from the map, and `io.read_upstream` reads a missing entry as run scope —
sending a condition- or repeat-scoped read to `shared/`, where such a step never writes. **Every
resumed execution reading a completed upstream step failed**, which in this study is every LLM arm:
`step03_screen` reads two condition-scoped upstreams, so a resume of any of the fourteen configs died
on its first execution. The arms most likely to need resuming are the multi-day local ones, where
losing a run costs the most. Fixed by building the map from the unnarrowed plan.

**It was found by resuming an interrupted run, and it had stood because nothing did that.** No test
in `test_cli.py` called `read_upstream` from a resumed run, so the pair was never exercised — the
same shape as the five § Validation rows this document once found described with no code behind
them, arriving from the other direction: code with no test behind it. **A command listed as
unexercised is a claim about coverage, and this document had carried that list through four
revisions without acting on it.**

**15. Closed — a `read_upstream` naming a step the run does not have read the run-scoped directory.**
The predicate under gap 14: `target is None` fell through to `shared/`, which is where the artifact
would be if the step were run-scoped and where nothing is if it is not. A misspelled step name
therefore surfaced as a `FileNotFoundError` naming a path no step ever wrote to, leaving a reader to
know the scope rules before they could see the *name* was the fault. It is now
`E-STEP-READ-UNKNOWN`, listing the run's steps, since a misspelling is the overwhelmingly likely
cause. **The refusal fires only where a scope map was supplied** — absent scopes are a different
state from an absent step, and a `StepIO` built without them has no step set to test against.

**16. Closed in a sibling — two implementations of one specification were kept in step by nothing, and drifted.** This is not a defect in `publishable` and is recorded here because the analysis is what found it, and because the shape generalizes past this study. The plan's `scripts/generate_trajectories.py` and the measurement tree's `src/growth_chart/construct.py` both implement the same generator; they live in different repositories, and the second names the first as its authority in a comment. On 2026-09-12 the plan re-fitted its parameters and `construct.py` did not follow, so the two now hold different constants and different targets. **No check could have caught it**: the plugin's own test compares the simulation against targets imported from the module under test, which passes for any self-consistent pair, and `publishable` never reads a step body — *Greenfield only* — so core cannot compare a constant against a document in a sibling repository. The gap this presses on is that `code_hash` covers `src/**` and `templates/**` of *one* tree, and a specification a second tree claims to implement is outside every hash a run computes. **Closed at `2026-08-28-gcl-measurement@0788387`** — in a sibling, not in this tree, which the gap said from the start was where it belonged: this is not a defect in `publishable` and core could offer nothing. `tests/test_plan_parity.py` reads the plan's six constants and compares them, and it fails rather than skipping when the plan is not beside the repository. **The sentence this paragraph used to end on prescribed the wrong design and is corrected rather than deleted**: it said the check should read the plan's constants *at the plan's pinned commit*, and a commit-equality arm is exactly what was not built. The plan moved four times on 2026-09-12 and one of those touched the generator; pinning would have fired three times for nothing, and the study repository had already deleted a rule of that kind for firing on something legitimate. The check compares the six values and reports the commit as provenance. **The obvious design was the wrong one, which is worth more than the gap was.**

**17. Closed, twice over — a docstring citing the figure its own file retired, and this document doing the same.** `verify_generator`'s docstring tells a caller to compare against 0.836, 0.487 and 0.869 — the all-ages statistics the plan withdrew under R41 — twelve lines below constants stating 0.909, 0.346 and 0.925. Both are in the same file, both were written by someone reading the same plan, and neither is checked by anything. It is `design-principles.md` § Every declarable field has a reader in the form that rule does not cover: not a declared field with no reader, but a *documented* one whose reader was corrected and whose documentation was not. **Closed at `0788387`**: the docstring now names `TARGET_BETWEEN_CHILD_SD`, `TARGET_WITHIN_CHILD_SD` and `TARGET_POOLED_LAG1` rather than repeating their values, because a figure written twice is a second copy nothing checks. **Re-measuring then found the same defect here**, in [§ Where the shared machinery lives](#where-the-shared-machinery-lives), which described the generator as `N(0, 0.84²)` at marginal SD 0.49 against a pooled 0.869 — the identical retired set, in this document's own specification-facing prose, while its measurement-facing prose carried the current one. Corrected in the same revision. **The lesson is the sweep, not the fix**: the first pass looked for the retired figures in the tree being measured and not in the document doing the measuring.

**18. Closed — a cost that is symmetric was guarded by a trigger stated in one direction.** [§ What one repository costs](#one-repository-fourteen-configs) names the price of keeping fourteen configs in one tree: `code_hash` covers `src/**` and `templates/**` whole, so a commit to any of it moves the recorded hash of every run, including runs that never called the code that changed. It then states a trigger rather than leaving it to judgement — *the first time a comparator commit would move the `code_hash` of a screening run already reported, or block one from starting, E2 and E6 move to a repository of their own.* On 2026-09-12 the mirror image happened: realigning the **generator** moved the `code_hash` of E2's and E6's already-reported runs from `6f474d8…` and `097865f…` to a shared `018273d…`, with every reported number identical. **The trigger is not met and those arms do not move** — it names comparator commits moving screening runs, not the reverse — but the underlying cost does not have a direction, and a trigger that does will fire on half the cases it was written for. This is not a gap in `publishable`: the three-hash split behaved exactly as specified, and it is *because* `parameters_hash` and `input_manifest_hash` held still that the record could say *same parameters, same inputs, different code* rather than leaving a reader to wonder whether the result moved. The gap is in this analysis's own trigger, found by the first instance rather than by re-reading it, which is the same way gap 16 was found.

**Closed.** [§ One repository, fourteen configs](#one-repository-fourteen-configs) now states the cost in both directions and the trigger names none: *a commit made for one side's sake moving the `code_hash` of an already-reported run on the other, or blocking one from starting*. The blocking half was one-directional too and is repaired with it — uncommitted generator edits refuse to start E2 exactly as uncommitted comparator edits refuse to start E10. **Why the original was written one way is worth keeping**: one repository exists to buy E4 through E10 their shared-hash claim, and comparator runs have no analogous claim to lose, so the *stakes* really are asymmetric even though the mechanism is not — `code_hash` covers the two trees whole and has no notion of which module a run called. An asymmetry of stakes written into a condition is what left it blind.

**Two consequences follow, and the second is not this document's to take.** The repaired trigger is **met**: the 2026-09-12 realignment moved E2's and E6's reported hashes. The remedy addresses that direction — measured rather than assumed, since E2 and E6 run `SummarizeUnits`, `Score` and `CompareLabel` and reach `construct.py` through none of them, so a split leaves it in the screening tree where it can no longer touch them. Whether to split is the study repository's decision. **The branch not taken is worth naming**: the alternative was to sharpen *already reported* until rig exercises on synthetic fixtures fell outside it, which would have been choosing the definition that makes a trigger not fire on the day it fired.

**What bounds this analysis has changed, and the change is worth recording.** The earlier version of this section said the cohort, the variable derivations, the model roster and the prompt were all undefined in the source, so no unit count could be checked as drawable and no cost figure given. **Three of those four are now defined**: the plan carries a Cohort and Data section with a 250,588-patient cohort profiled against a real snapshot, variable definitions for every backticked field, and a roster and prompt specification. Every sample size is now stated as a fraction of a named cohort and each is well under 1%, so the counts below are drawable rather than merely asserted. What is still missing is the only anchor a cost needs: **no prompt has been run, so there is no token count**, and multiplying an exact request count by a price is not something this document can honestly do.


---

## Executability on this build

A claim about what the tool *does today* is perishable in a way a specification claim is not, so
everything in this section is dated and pinned, and nothing outside it is a build claim. **This
section is re-measured whole rather than appended to**, so what follows is the current state and
not a log: every number below was produced by running the command named beside it at the commits
named here. Earlier measurements against earlier commits are in this file's git history, which is
where a superseded reading belongs.

### Measured on 2026-09-12 against `publishable` commit `ca77360`

Also pinned: the plan at `growth-chart-literacy@22d1b24`, and the two sibling repositories at
`2026-08-28-gcl-measurement@0788387` and `publishable-growth-chart@fac2295`. **This is the second
measurement on 2026-09-12 and it supersedes the first**, whose pins were `ca77360`'s parent and
`2a8c9e6`; the date alone does not separate them, which is the argument for pinning commits rather
than dates made by the first case where a date could not. The previous revision
had to note one measurement taken against its pin *plus* an unlanded fix; that fix — the `E-NAME-DIR`
message defect [below](#gaps-this-analysis-found-in-the-specification) — is in `8039611`, so this
revision carries no such exception.

**Core did not move, and the three-hash split is what lets this section say so.** `publishable`
advanced five commits from `9a7844c` to `ca77360`, and `git diff 9a7844c..ca77360 -- src templates`
is **empty**: all five are re-measurements of this very document. `code_hash` covers `src/**` and
`templates/**` only, so a run at either commit computes the same one, and every result below is
carried forward *on that ground* rather than on the assumption that four doc commits were harmless.
What was re-run anyway, because carrying a claim is not the same as checking it: `validate` on all
fourteen configs, `dry-run` on all fourteen, both suites, and a byte comparison of all sixteen quoted
files. The first two reproduced exactly, as did the byte comparison and both suites'
passing state; what moved is the counts, the constants, and both recorded `code_hash`es, each
corrected below.

**Re-measuring found a hole in this repository's own mechanical guard, and it is fixed in this
commit.** `tests/test_repo_docs.py` extracted markdown links line by line, so a link whose *label*
wraps — its opening bracket on one line, its closing bracket and target on the next — matched nothing
and was never resolved. This repository's documents have no hard line breaks inside a paragraph, so a
long label wrapping is the normal case rather than an edge one, and two links written into this file
during this revision carried a wrong anchor while the checker reported it clean. `_links` now scans
contiguous runs of prose and joins only adjacent lines, since joining across a fence would pair an
opening bracket before a code block with a closing one after it and invent a link neither paragraph
contains. The fix is pinned by a test that asserts the wrapped form, the flat form, the reported line
number, the across-a-fence case and the inside-a-fence case — and that test was run against the old
behaviour and fails on it, rather than being trusted because it passes on the new. **It earned its
keep immediately**: the first draft of this very paragraph illustrated the defect with a literal
wrapped link, and the repaired checker refused the file until the illustration was rewritten as
prose.

**Two of this section's findings are fixes carried in the pinned tree.** The `resume` defect and the
`read_upstream` predicate behind it were found by exercising the commands recorded above, and both
landed in `9a7844c` — which this pin inherits unchanged, since nothing under the hashed trees has
moved since. The revision that first pinned them could say core moved *because of* what this section
measured; this one cannot, and the distinction is worth keeping rather than smoothing, because a
revision where core did not move is the case in which every carried-forward result is actually safe.
The paragraphs reporting them describe the tree they were found in and name the commit that repaired
it. What moved this time is a *sibling* repository's `src/growth_chart/construct.py` and the plan it
follows — the study's trees, not this one — which is why the divergence below is reported rather than
the templates re-synced; `templates/` is byte-identical at both sibling pins. That is the three-hash split
doing its job across repositories: a measurement is of a tree, and this document reads three of
them. Pinning the plan's own
commit began with the measurement before that, and the reason stands: every earlier version of this
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

**The plan moved for the first time since this document began pinning it, and the pin is what caught
it.** Eight commits between `e6b43ab` and `7dafaeb`: an artifact profile of the augmented layer
producing six findings, the generator restated on the age-2-or-later window, E5b's negative strata
reworded, a generator *implementation* added to the study repository, and the panel-gate question
settled. **Three of those reached this tooling, and none of them would have been noticed without
re-reading the plan against its commit** — which is the entire argument for pinning it, made by the
first instance rather than by assertion:

| What the plan changed | What this tree carried | Now |
|---|---|---|
| Calibration targets restated on the age-2-or-later window (R41), and the process **parameters** separated from the sample **targets** they reproduce | the retired all-ages figures, read straight in as parameters — the exact conflation the plan names | `σ_b` 0.87, `σ_e` 0.43, `ρ` 0.62, reproducing 0.909 / 0.346 / 0.925 — **and the plan has since moved again; see below** |
| E5b's strata reworded (R45): a stratum is negative because **no sustained shift was applied**, not because no centile line is touched | `unambiguous` damped its noise to a quarter — a curve visibly smoother than a real one, which is the artifact the panel's adversarial half exists to catch | the same measurement variation as every other trajectory |
| Panel validates **categories**; arms drawing from one inherit | this document said *"nothing upstream of E3 remains"* | E3 waits on the panel, and so does the whole core |

**The two implementations have now disagreed, and the previous revision of this paragraph predicted
it.** It read: *two independent implementations of one specification agree to within 4%* — followed by
the risk [§ Where the shared machinery lives](#where-the-shared-machinery-lives) names, that they
eventually disagree and the only thing that catches it is a check reading the targets rather than the
constants. That is now the state of the tree, so the sentence is withdrawn rather than re-scaled.

On 2026-09-12 the plan re-fitted the generator, because the augmentation re-run raised the height
ceiling from +3 to +5 and censoring a tail biases the between-child SD *down*. Its parameters moved to
`σ_b` 0.9, `σ_e` 0.42, `ρ` 0.57 against targets 0.925 / 0.349 / 0.921. **`src/growth_chart/construct.py`
still carries 0.87 / 0.43 / 0.62 against 0.909 / 0.346 / 0.925** — the retired set — under a comment
that names the plan's script as "the authority for them".

**Measured, not re-based**, by running `verify_generator` at `2a8c9e6` over 6,000 paths on the plan's
nine-visit annual schedule:

| statistic | plugin produces | vs. the targets it carries | vs. the plan's targets today |
|---|---|---|---|
| between-child SD | 0.9216 | +1.4% | −0.4% |
| within-child SD | 0.3349 | −3.2% | −4.0% |
| pooled lag-1 | 0.9267 | +0.2% | +0.6% |

**The finding was the absent check, not the deviation.** That the worst gap was 4.0% and the ±10% band
still held is a property of how far *those* targets moved, not of the arrangement; the next
divergence was bounded by nothing, because nothing measured it. `tests/test_construct.py` compares
`verify_generator`'s output against `TARGET_*` imported from the module under test, so it passes for
any self-consistent pair of parameters and targets — **including a pair that contradicts the plan**.
It is a correct check of the fit and blind across the repository boundary, which is the only boundary
that matters here.

**Both are closed at `2026-08-28-gcl-measurement@0788387`, and the sequence above is kept rather than
replaced by the outcome.** Predicted, drifted, measured, closed — a paragraph that reported only the
current state would be a document claiming a check was necessary with nothing showing it. The
constants now read `σ_b` 0.9, `σ_e` 0.42, `ρ` 0.57 against 0.925 / 0.349 / 0.921, and
`verify_generator` at that commit produces **0.9455 / 0.3405 / 0.9245** over 6,000 paths — worst
deviation 2.4%, where the divergent tree's was 4.0%.

**What enforces it is `tests/test_plan_parity.py`, and two of its decisions are the interesting
part.** It reads the plan's six constants out of `scripts/generate_trajectories.py` and compares the
numbers; it does **not** assert that the plan sits at a pinned commit, because the plan moved four
times on 2026-09-12 and only one touched the generator — a commit-equality arm would have fired three
times for nothing, and a check people learn to ignore is worse than none, which the study repository
had already established by deleting a rule of exactly that kind. And its reader takes a *path* rather
than reading a module constant, which is what lets the suite point it at a mutated copy of the plan:
a reader wired to a constant could only ever demonstrate agreement, never that disagreement is
caught. **It was shown to fire rather than argued to**: reverting `ρ` to 0.62 in the measurement tree
fails it with the disagreeing constant and the plan's commit named, while `test_construct.py`'s
thirty-seven tests pass straight through the same mutation — which is this finding demonstrated
rather than asserted. An absent plan fails rather than skipping, since a skipped parity check is
indistinguishable from a passing one.

**The same file carried a third generation of the figure, and this document carried a fourth.**
`verify_generator`'s docstring told a caller to compare its output against "the cohort's 0.836, 0.487
and 0.869" — the *all-ages* statistics the plan retired on 2026-09-05 under R41, and the exact
conflation R41 exists to name — twelve lines below constants stating 0.909 / 0.346 / 0.925 and one
repository away from a plan stating 0.925 / 0.349 / 0.921. It now names the constants instead, since a
figure repeated in prose is a second copy nothing checks. **And the fourth was here**: [§ Where the
shared machinery lives](#where-the-shared-machinery-lives) described the generator as `N(0, 0.84²)`
at marginal SD 0.49 against a pooled 0.869 — the same retired all-ages set, sitting in this
document's own specification-facing prose for a week while its measurement-facing prose had the
current one. Four readings of one quantity across three files, each true of a different day, and the
only one anything checked was the pair inside `construct.py`.

**What moved before that, and the pattern is worth naming.** This section has been re-measured five
times in ten days, and the first four were **because implementing something the plan specified
changed what the tooling does** — not once because core moved under it. A dated section whose job is to report what the tool
does today has turned out to be what catches a commitment nobody built. Four such commitments have
now been implemented and are no longer claims this document has to hedge:

| The plan's clause | What ran before |
|---|---|
| One system and one user message, carrying the child's sex and the reference frame | one blob as a user turn, `system=None`, no sex, a frame chosen and never stated |
| The message envelope's difference across endpoints is recorded | the envelopes differed correctly and nothing recorded which was used |
| The deployment is observed, and a moved fact fails the run | an environment variable with a default, so **the gate compared a constant against itself** |
| A malformed answer is retried once; a refusal is not; the unusable rate is reported past 5% | neither was retried, so the parser's distinction between them bought nothing, and the rate had no reader |
| Monotone spline interpolation on z-scores, documented | linear interpolation, documented as linear |

**Two core defects closed in the same window**, both found by asking this analysis's own question of
core rather than of the plan, and neither in a release yet; see the paragraph above.

**What was built to measure it.** A scratch experiment repository from `publishable new`, holding the
two project-local templates [listed below](#the-two-templates-as-loaded) in `templates/` (307 lines),
one `src/growth_chart/` package (3,832 lines over sixteen modules, seven step bodies and three prompt
files) with 3,482 lines of tests, **fourteen** configs, a 480-line input generator, and a
`publishable-growth-chart` plugin from `publishable plugin new` (695 lines, 1,111 of tests) installed
as an editable dependency — registering one resolver, one probe, and one writer/reader pair, and
**no** template. `uv run pytest`: **241 passed** in the measurement repository, **59** in the plugin.
**The basis, stated because its absence is what let the previous numbers drift:** every `*.py` tracked
under the named directory, `__init__.py` included, counted with `wc -l` at the commit pinned above.

**The basis paid for itself within a day, and this is the demonstration.** Every count above moved
since the previous measurement, and because the basis is now written down each delta can be
reconciled against the commit that produced it rather than taken on trust: `src/growth_chart`
3,820 → 3,832 against `construct.py`'s diff of +23/−11 = **+12**, and `tests` 3,300 → 3,482 against
`test_plan_parity.py`'s 170 new lines plus `test_construct.py`'s +12 = **+182**. Both reconcile
exactly. The previous revision's counts could not be checked this way — that is what made them
drift undetected through several pins, and it is why the sentence above exists.

**Every count in the paragraph above was wrong, and re-measuring is the only thing that could have
found it.** The corrections are 256→307, fifteen→sixteen modules, 3,643→3,820, 3,263→3,300, 591→695,
846→1,111, 236→237 and 48→59 — **eight of eight low**, which is the direction this project's stale
measurements always fail in. Two distinct faults produced them. The templates' 256 was *true*, at
`30faa6a`, and four commits of prompt and timeout work carried it to 307 while the pin advanced and
the number did not. But **sixteen modules and 3,643 lines were true at no commit in the last
twenty-five** — the tree holds sixteen `*.py` at every one of them, and no basis reconciles the
line count either: excluding `__init__.py` gives thirteen modules and 3,677 lines, counting non-blank
lines gives 3,248. So these were not carried-forward measurements at all, and the ratio sentence this
paragraph used to end on — tests growing faster than code, 3,234 against 3,609 — was arithmetic on
them and is deleted rather than recomputed. **A count with no stated basis cannot be checked, only
repeated**, which is why the basis is now written down beside it.

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
| [E6](#e6--the-non-llm-comparator) | `auroc` delta **0.0**, `ci95` [0.0, 0.0], `method: paired_percentile_over_units_clustered`, `n_paired: 595` over 300 clusters; `supported: false` | `computed` — core built the contrast |

**Both were re-executed at `0788387` and every number above is unchanged, while both `code_hash`es
moved.** E2 returns `auroc_count_only` 0.6415 with `ci95` [0.6054, 0.6784] over 1,000 patients and E6
returns the same three contrasts, `n_paired: 595` over 300 clusters, to the digit. What changed is
provenance: E2's record carried `code_hash` `6f474d8…` and E6's `097865f…`, and both now read
`018273d…`, because `construct.py` moved when the generator was realigned. **Those are different
facts and the split between the three hashes is what keeps them apart** — `parameters_hash` and
`input_manifest_hash` are untouched, so the record says *same parameters, same inputs, different
code*, which is exactly true and is not a claim that the result moved.

**It met the shape of a cost this analysis stated in one direction only, and repairing that is
[gap 18](#gaps-this-analysis-found-in-the-specification).** [§ What one repository
costs](#one-repository-fourteen-configs) framed it as E2's and E6's commits moving the `code_hash` of
screening runs that never called their code, and set the trigger for splitting them out on a
*comparator* commit moving a *screening* run's hash. What happened is the mirror: a **generator**
commit moved two already-reported **comparator** runs' hashes. `code_hash` covers `src/**` and
`templates/**` whole and has no notion of which module a run called, so the traffic was always
symmetric and only the stakes were not — one repository exists to buy E4 through E10 their
shared-hash claim, and comparator runs have no analogous claim to lose, which is why a reader writing
that sentence saw one direction. **The trigger now names none, and on its repaired wording it is
met.** Whether E2 and E6 move is the study repository's decision; this document states the trigger
and does not execute it.

**One of those two numbers did not move when the generator did, and the reason is worth a sentence
rather than a shrug.** Realigning the calibration changed every z value in every roster, and E2's
`auroc_count_only` came back **bit-identical** at 0.6415436558791847. That is correct: `count_only`
reads `visits_pre_index` and nothing else, so a change to the curves cannot reach it. E6's did move —
0.880 and 0.918 against 0.851 and 0.891 — because its feature set carries the z summaries. A number
that holds still under a change that could not reach it is evidence the pipeline is wired the way it
is documented, and the same number holding still under a change that *should* have reached it would
have been the opposite.

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
user message; nothing else. **This particular block is a rendering rather than a transcript** — it
was dumped from the serialization step, not read back off a response — and a rendering is what it
should be, since it is the prompt this document is quoting. What a real one produced is
[below](#the-first-real-completions-and-what-they-cost).

**The plugin's three registries dispatch, and all three are now exercised.** `data.units.from:
{resolver: growth_trajectory}` resolves every roster at `validate`; `apparatus_probe =
"growth_llm_deployment"` is called at `dry-run` and its facts recorded per condition; and the
`.transcript.jsonl` writer, registered since the plugin was written and **never once driven by a
write**, was driven by one on 2026-09-10 — [§ The first real
completions](#the-first-real-completions-and-what-they-cost). Until then the suffix-dispatch rule it
relies on was measured only [in the tutorial](tutorial-writing-a-plugin.md), because the two runs
that had executed were the non-LLM arms.

**The roster below is the study's own**: `gpt-4.1`, `gpt-5` and `gpt-5.6-sol` filling the scale ladder with the largest designated primary — which is why every single-model config names `gpt-5.6-sol` — plus `gemma4:12b` and `qwen3.5:9b`, Q4_K_M both, spanning the `gemma4` and `qwen35` families. Every one of the five now answers a metadata read. **No request has been issued to an Azure deployment**; one local checkpoint has been asked four questions, twice, [below](#the-first-real-completions-and-what-they-cost).

**The credential check, measured on E10 with `.env` moved aside.** `validate` reports per condition
and by name: exactly `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` across the twelve Azure
conditions, and **nothing at all for the eight `ollama` conditions**, whose `requires_env` entry is
`[]`. The roster is what the plan's governance permits — three Azure deployments and two local
checkpoints — and an earlier roster's Anthropic arm, which demanded a third variable, is gone with it.

**The apparatus probe answers on every condition of the ladder.** All twenty of E10's conditions
carry a real `model_version`, read from the deployment rather than planted — the three Azure
deployments resolving to versioned snapshots, and the two local checkpoints to the manifest digest
of the weights on the machine:

| Deployment | What it resolved to | Read from |
|---|---|---|
| `gpt-4.1` | `gpt-4.1-2025-04-14` | Azure `/openai/models/{name}` |
| `gpt-5` | `gpt-5-2025-08-07` | Azure `/openai/models/{name}` |
| `gpt-5.6-sol` (primary) | `gpt-5.6-sol-2026-07-09` | Azure `/openai/models/{name}` |
| `gemma4-12b` | `4eb23ef1…b2b05c` | Ollama `/api/tags` |
| `qwen3.5-9b` | `6488c96f…893ea7` | Ollama `/api/tags` |

**The shape of each fact is what makes it a gate, and the two halves of the roster are gated on
different things.** Asking about `gpt-5` returns the versioned snapshot behind it, so a deployment
repointed at a newer model changes the fact while the deployment name does not — the silent change
the plan wants caught, and the reason this is observed rather than declared. The local half is gated
on the weights instead: the digest covers the blobs, the parameters and the template, so a
re-quantized checkpoint pulled under the same tag moves it. Neither is a version string the config
could have carried.

**E10's `dry-run` reports 20 unanswered facts, and all twenty are the same fact.** They are
`system_fingerprint`, one per condition — returned on a completion response and by nothing else, so
no metadata read can produce it, and the study logs it per call instead. **Every `model_version` in
the ladder now answers**, which was not true of any earlier measurement: 40 unanswered when the
roster was placeholders, 28 once the three Azure names resolved, 20 once the two local checkpoints
were pulled. The number was predicted from the previous one before the command ran — 28 minus eight
local conditions, two checkpoints across four cells — which is the only way a count like this is
worth quoting.

**Getting the local half of that took a second endpoint, and the first one had never answered.** The
probe asked Ollama's `/api/show`, which returns the license, the template, the tensor list and a
`modelfile` naming the weight blobs — **and no `digest` at all**, for a freshly pulled local
checkpoint exactly as for a model Ollama proxies to its cloud. `/api/tags` answers with one 64-hex
manifest digest per model, which is what `ollama ls` abbreviates, and that is what the probe reads
now. Two things about how that was missed are worth recording. The fixture that pinned the old
behaviour was a payload shape **no endpoint produces**: it carried a top-level `digest`, agreed with
the code, and both were wrong about the same thing, which is why the test now asserts the URL and
not only the fact. And a fix shipped the day before — a `remote:` fallback for proxied models,
[measured then](#executability-on-this-build) — was aimed at the case where `digest` was absent while
leaving the case the study actually runs answering `null`, because the belief it was written from was
that a local checkpoint carried one.

**The precedence between those two answers had to invert, and that is a governance fact rather than
a tidy-up.** Every `/api/tags` entry carries a digest, proxied ones included, so preferring the
digest would stamp a cloud-proxied model with a hash and record the arm as locally hosted —
§Cross-Cutting permits the HMS Azure API and locally hosted open-weight models, and a proxied model
is neither however local the config looks. `remote_model` now decides, and a fact reading `remote:`
is the one signal in the record that an arm labelled local was not. No fixture held a proxied entry
with a digest before, so the suite passed under either order.

**Measured, and it is what licenses the alias:** `gemma4-12b` and `gemma4:12b` both probe to
`4eb23ef1…b2b05c`; `qwen3.5-9b` and `qwen3.5:9b` both to `6488c96f…893ea7`. A model that is not
pulled leaves the fact unanswered and `dry-run` names the condition, which is what makes the count
above a readiness check rather than a formality.

**Getting the Azure half took three faults off one endpoint, and two of them were this tooling's.** The
credential and the api-version were correct throughout; a hostname in the environment was one
character short, which resolved somewhere that accepted a connection and closed it without replying,
so the failure read as a network fault rather than a typo. Under it: this probe asked for
`/openai/deployments/{name}`, which that resource does not serve — 404, as is the deployments list —
while `/openai/models/{name}` does and answers with the resolved id above; and the probe hard-coded
an api-version while `AZURE_OPENAI_API_VERSION` sat in the environment unread, which is [the defect
this document files most often](#executability-on-this-build), in its own plumbing. **A probe that
answers `null` on every failure cannot tell you which of three things is wrong** — that is the cost
of the design named in [§ LLM API access](#llm-api-access), paid in full here, and what closed it was
reading a working project that used the same endpoint.

**Three refusals probed deliberately** at an earlier measurement, each by copying a config, editing
one line, and re-running `validate`. All three are properties of core rather than of the plan, and
none of them moved:

| Probe | Result |
|---|---|
| `sweep.grid` on a `list`-typed parameter — `llm.backoff_secs: [[2, 8, 30], [5, 20, 60]]` | `E-SWEEP-VALUE-UNNAMEABLE`: *swept value '[2, 8, 30]' does not match `^[A-Za-z0-9._+-]+$`* |
| A contrast naming the baseline by its swept value rather than `baseline` | `E-STATS-CONTRAST-UNKNOWN` alone, naming the label that matched no condition — one error, not two |
| `{kind: fold, k: 5, stratify_by: [visit_decile]}` | `E-REPL-FOLD-STRATIFY-UNKNOWN`: *a fold balances its folds on one declared attribute, named as a string* |

**What writing this pipeline against the plan has found.** Ten things, none of them visible to
`validate`, to `dry-run`, or to reading:

**1. A specification written in prose and not in code fails silently, and this pipeline produced
three instances of it.** The plan fixes one system message and one user message per case, with the reference
frame stated and the child's sex carried. The code sent one blob, `system=None`, no sex and no
stated frame — and nothing failed, because nothing could: a prompt is a string, and a string that is
missing a clause is still a string. **Sex is the one that would have changed answers**, since every
growth reference is sex-specific and E9's whole design rests on a peripubertal window defined
sex-specifically. This is the same defect class as [an unread parameter](#the-stimulus-arm-has-to-be-constructed-somewhere)
one layer out: there, a declared field no step read; here, a declared *commitment* no code read.
What closes it is the same shape too — the contract is checked at load, so a prompt that would render
identically for every unit is refused before the sweep is paid for.

**The second instance is the output contract**, and it failed the same way. The plan requires a
malformed answer to be retried once with the identical prompt and a refusal never to be, and the code
retried neither — so `parse.py` told the two verdicts apart, `apply_parse_failure` then treated them
identically, and **the distinction existed and bought nothing**, because the asymmetry that gives it
its purpose is the retry. Its 5% unusable-rate clause had no reader at all. Both were invisible for
the same reason the prompt was: nothing fails, because an unreadable answer routed to `ineligible` is
a defensible thing to do with it — just not the thing that was written down.

**The third is the interpolant.** §E5a asks for *monotone spline interpolation on z-scores*, and the
resampler was linear — which matters in that arm specifically, because it displays twenty points
resampled from about six and a linear interpolant makes them piecewise-linear between the real
visits, with visible knots the three-point sparse arm cannot have. The arm's design is that the
densities differ in the schedule and in nothing else, so an interpolant that advertises how many real
points there were is a second signal riding the manipulation, and E7's utilization axis inherits it.
The common thread across all three: **each was a defensible thing to do, and none was the thing that
was written down.**

**2. A neighbouring defect, of a different kind, under the guarantee this document sells hardest.**
The apparatus probe returned an environment variable with a default, so the gate that *fails a run
whose deployment moved* compared a constant against itself. This is not finding 1's shape and the
difference is worth naming, because it is not the one this project usually files either: not a
declared field no step reads, but **a declared field whose reader returns a placeholder**. The
first kind is findable by grepping call sites, which is the remedy `design-principles.md` names. The
second is not: the call site exists, the value is well-formed, the run completes, and only reading
the body tells you the answer was manufactured. What found it here was asking, of each guarantee this
analysis claims, *which line performs it* — and the probe's answer was a comment saying a real probe
would.

**3. Deleting an experiment leaves an unread parameter behind, and the second-order effect is a check
that cannot fail.** E1's removal orphaned four surfaces at once — `model.kind: agreement`,
`truth.rater`, and the `kappa` and `agreement_raw` its template derived. Removing them was
straightforward; what was not is that `growth_label.validate`'s rule that a config fitting a model
needs a `holdout` or a `fold` was written as *unless the kind is `agreement`*, and with that kind
gone the exception is vacuous — the rule reads as conditional and is unconditional, and its test was
asserting a branch nothing can now reach.

**4. A derived metric recomputed on every bootstrap draw makes an O(n²) `aggregate` an O(n² × draws)
run.** `growth_label.aggregate` computed its AUROC by the pairwise definition, which is fine on a
100-unit roster and is two billion comparisons at E2's thousand units and 2,000 draws. The run does
not fail; it does not finish. The general lesson is core's rather than this template's: **a
template's `aggregate` is called once per resample per condition**, so its complexity is multiplied
by a number the config chooses.

**5. A holdout gives the estimate for free and refuses the selection.** Core narrows every
denominator to the test partition, which is exactly what E3's split is for — and it also means the
selection half is never screened, and a format selected on nothing is not a selection. The step asks
for `io.units.train` and screens it too, writing that half's accuracy as an artifact rather than
through `io.record`. Both halves are then reportable and only one of them is a metric.

**6. `io.units.train` raises rather than returning empty, and a step has to catch the right thing.**
Twelve of the fourteen configs declare no split at all, so the selection-half branch has to be
ordinary rather than exceptional. `E-STEP-UNITS-UNAVAILABLE` is the direct question — *is a split
declared* — and a bare `except Exception` around it would have answered *did anything go wrong in the
partition*, which is [the same substitution](../CLAUDE.md#answering-a-question-with-a-proxy) in
another guise.

**7. Three tests in this pipeline could not fail, and mutation found all three.** None was visible by
reading, and the three are worth separating because the remedies differ:

- **A deleted field nothing asserts.** Extracting one contract helper dropped the transcript's
  `partition` marker and the whole suite still passed: the tests touching those rows assert unit keys
  and accuracy, and **neither can see a missing field**. A test asserting *what a row says* cannot
  notice what the row stopped saying.
- **A probe point where both answers agree.** The pin for *"this is not the linear interpolant"* read
  a segment's midpoint — where the cubic Hermite basis puts `h10(0.5) = −h11(0.5)`, the tangent terms
  cancel, and the curve meets the chord exactly. It passed against both implementations.
- **A fixture with no curvature to measure.** The arm-level version of the same pin built its
  trajectory from a helper whose z path is a straight ramp, and every interpolant through collinear
  knots is that same line — so counting collinear triples measured the fixture.

- **A check that compares a module with itself.** The generator's distributional test asserted its
  output against the same constants the generator draws from, so it measured that the module equals
  itself — and stayed green while those constants were the retired all-ages figures. It now checks
  the plan's **targets**, which are deliberately different numbers from the parameters, at the plan's
  own ±10% band; the retired parameters fail it.

The middle two are one trap in two guises, and it is the one this project files most often: **a
fixture whose numbers agree with the thing it is meant to rule out.** The last is its sibling — a
fixture that *is* the thing under test. What found all four was running the mutation at the call site
rather than trusting the assertion's name.

**8. A pinned document catches an upstream change; an unpinned one absorbs it.** The plan moved
eight commits in five days and three of those changes reached this tooling — a restated calibration,
a reworded stratum, and a dependency this document had explicitly denied. **None was announced and
none broke a test**, because the tooling had no way to know the specification had moved. What found
them was re-reading the plan against its recorded commit, which is the practice this document adopted
after going stale invisibly once before, and this is the first time it has paid. The corollary is
uncomfortable and worth stating: **every claim here about a plan is only as fresh as the last time
someone diffed it**, and nothing automates that.

**9. A guard that reports one failure state cannot be debugged, and the bill arrives at the endpoint.**
This probe answers `null` for every fault — unreachable, refused, unserved, credential absent — which
is the right *record* behaviour and, on first contact with a real resource, left three faults stacked
behind one indistinguishable symptom: a hostname one character short, a metadata path that resource
does not serve, and a hard-coded api-version beside an unread declared one. **What separated them was
a second project pointed at the same endpoint**, not anything in this tooling or its tests. The
lesson is not to make the probe raise — a run must survive a network blip — but that a design whose
failure states are deliberately collapsed needs a diagnostic path that is *not* the record: something
that reports the status code, once, to the person setting it up.

**It happened a second time on the other endpoint, and the second instance is the argument.** Once
the two local checkpoints were pulled, their facts still read `null` — and the probe had *reached*
the endpoint and *received* a payload naming the model, because `/api/show` carries no `digest` on
any model. An unanswered fact meaning *the model is not on this machine* and an unanswered fact
meaning *this code is reading the wrong field* are indistinguishable by construction here, and a
readiness count built on them cannot tell a maintainer which they have. Two endpoints, two stacked
misreads, one symptom: **the collapse is a property of the design and not of either provider**, which
is what moves this from an anecdote to a thing worth building against.

**10. A quantity computed for the wrong arm is worse than one not computed.** E5b's floor rule — the
one-sided bound on the excess false-positive rate — is arithmetic on a discordant pair count, and
every two-condition screening arm produces those counts. Gating it on the *shape* of the sweep would
have reported E4b's and E5d's flips as false positives, which they are not; the gate is on the arm's
own `stimulus.physiology` being `true_negative`.

**The roster is real, and one of the five has been reached.** `gpt-4.1`, `gpt-5` and `gpt-5.6-sol`
fill the scale ladder with the largest primary; `gemma4:12b` and `qwen3.5:9b` span two families. Both
local tags carry a colon and so cannot be swept — `E-PARAM-VALUE` and `E-SWEEP-VALUE-UNNAMEABLE`,
measured — and the alias is made in the local model registry rather than resolved in code, because
resolution needs a table that both the request path and the apparatus probe read. **The alias moves
no fact**: `ollama cp` writes a second manifest over the same blobs, and `gemma4-12b` probes to
`4eb23ef1…b2b05c` exactly as `gemma4:12b` does, `qwen3.5-9b` to `6488c96f…893ea7` as `qwen3.5:9b`
does. That equality is what licenses the registry fix over the resolution table, and it is an
empirical property of the registry rather than an argument — the part of this that generalizes past
Ollama.

**R7 has landed, and the predicted size was 24% high.** It was dated 2026-09-11 and owned by the data
team; the re-run was delivered on 2026-09-12 as PPOC snapshot `2026-09-12`, package v1.1.0. The plan's
cost estimate had been *withdrawn* on 2026-09-05 rather than revised down — the earlier "costs almost
nothing in volume" argued from a 99.9th percentile that was 2.91 *because* the tail had already been
cut — and its replacement, roughly 15,800 visits, was itself a prediction: the retained left tail below
−3 scaled by the 1.635 upper/lower ratio observed at ±2.5. **Counted rather than scaled, the tail is
12,719.** Extrapolating that ratio past +3 overstates the real tail, which is lighter out there than it
is at ±2.5. `height_z_score` now runs −5.8186 to +4.1203 with nothing above +5, and the tallest
ten-year-old in the file is 171.5 cm against a previous hard cap of 162.6 cm — which is +3.0 exactly,
so the restored values are measurements and not a re-scoring.

**How it was delivered changes who enforces the bound.** The re-run used `augment.py --no_filter_errors`,
which lifts the implausible-value filter wholesale rather than raising the height ceiling alone, so the
height *floor* and both weight bounds came off with it: 575 height and 869 weight values now sit beyond
|5|. Nothing this document measures is affected, because `data.units` resolution applies the plan's
item-6 range before a trajectory is serialized and drops those rows — 677 of 3,801,473 at age 2 or
above, 0.018%. But the range is now enforced by the study rather than by the data as distributed, and
that is a Methods sentence rather than a pipeline change. This is the first real-data anchor this
document has had that is a delivery rather than a date, and nine of the fourteen runs read a real
trajectory or scaffold.

**The roster resolves, and the primary is `gpt-5.6-sol`.** The plan makes the largest Azure
deployment primary and says every experiment implying a single model means that one, so the twelve
single-model configs name it and E10's ladder carries all three. **`gpt-5.6` — the name this document
carried for a day — does not exist on that resource**, which the probe reported as an unanswered fact
rather than as an error, and which a catalogue read then explained: three `gpt-5.6-*` variants exist
and no bare `gpt-5.6`. A roster whose names are checked against the resource before a run is a
different thing from a roster that validates.

**The six lifecycle commands are exercised, and one of them was broken.** They were listed here as
unexercised through every earlier revision, which is why they were run against the smoke record
rather than reasoned about. `report` renders a run and a bundle; `diff` reports the three hashes with
a field-by-field parameter breakdown; `study new` and `study add` build a bundle from the two
executed non-LLM arms; `freeze` re-probes a crashed directory and reports the digest unchanged.
`reproduce` refused with `E-REPRODUCE-NO-REMOTE`, because the study repository had no git remote —
so the command a collaborator runs could not work for any run this study produces. **It has one now**
(`seouri/gcl-measurements`, private), and `reproduce` was re-measured against a fresh run: it clones
from GitHub, checks out the recorded commit detached, verifies the code hash and prints the commands
to re-run it. Six of six exercised, and this one moved from refusing to working inside the same
measurement.

**Adding the remote repairs no record written before it.** `provenance.git.remote` is read at run
time and stored, so every earlier run still carries `null` and still refuses; core's fallback for
them — `git checkout --detach <sha>`, in a copy of the repository you already have — is all they will
ever offer. That is the three-hash discipline applied to lineage: a record describes the tree as it
was, and a repository that acquires a remote afterwards has not changed what the record said.

**`resume` failed, and the defect was core's.** The resumed execution died on `FileNotFoundError` for
`shared/step02_serialize/prompts.json`, a path that condition-scoped step never wrote to.
`execute_plan` derived its step-scope map from the plan, `resume` narrows the plan to what has not
completed, and `io.read_upstream` read the resulting missing entry as run scope — so **every resumed
execution reading a completed upstream step failed**, which for this study is every LLM arm. Fixed by
passing the unnarrowed map, and the predicate behind it closed separately: a `read_upstream` naming a
step the run does not have is now `E-STEP-READ-UNKNOWN` rather than a silent read of the run-scoped
directory.

**Two registration items closed on 2026-09-10 and 2026-09-11, and closing the first found a third
thing.** Item 4 fixes the concerning/healthy boundary at a sustained shift of **0.67 z over 2 years**,
identical in both age bands — Wright's one-space tracking band, with the peripubertal half registered
as E9's *matched stimulus* rather than a second threshold, since E9 asserts that band is normal.
§E5b's benign excursion followed at **0.56 channels (0.335 z)**, within-channel, no duration: the
resolving-shift reading was dropped because its source ends "within the first 2 years of life", a
window this study excludes.

**What that unblocked, measured.** The panel packet's refusal went from four categories to one to
none: it now assembles **110 charts across all seven categories**, with no category word in the
visible text of any of them and a manifest accounting for every curve. `verify-strata` at the
registered values reports a benign within-SD excess of **9.2%** and PASS.

**And what it exposed, which is the part worth carrying.** All fourteen configs declared
`stimulus.crossing_channels: 2.0`, which the study's constructor multiplied by a hard-coded 0.67 for
a **1.34 z drift — double the dose item 4 had just registered**, and the age-invariant "two channels"
§E4b names as the contradiction item 4 exists to resolve. Worse, "a channel" meant 0.67 z in that
constructor and 0.5992 z in the plan's own generator, so one field named two quantities across two
implementations of one model. **A dose carried in a unit two implementations define differently is a
dose that drifts**, which is why item 4 was stated in z — and the field is `stimulus.crossing_z` now,
carrying 0.67 directly. The delivered drop measures +0.654 z where it measured 1.34.

**The test that should have caught it could not**, and that is the recurring shape rather than a new
one: it asserted `channels * CHANNEL_Z`, so it agreed with the conversion instead of checking the
dose, and was blind to both defects it sat beside. A registered value reached the plan a day before it
reached the code, and the check between them was written in the units of the bug.

**Both preregistration items that gated this study are now fixed, and neither was closed by
argument.** Item 5's five parts are settled — the counted specialty set is a mapping over 119
`requested_specialty` values rather than three names, chosen after measuring that the pediatric
variants add 326 patients for nothing and that a fixed-index scheme would discard 63% of controls;
the matched index is risk-set sampling with a ±1-year enrolment caliper, which leaves a mean of
39,663 eligible controls per case and no case unmatchable; and the serialized trajectory ends **three
months before the index**, with the index-ending window registered as a sensitivity analysis. That
last one was decided on a measurement this analysis had no way to anticipate: **height measurement
runs at 2.94× its baseline rate in the three months before a referral and below baseline on either
side of that window**, so a trajectory ending at the index carries a care-process signal produced by
the outcome itself — entering through the door §E5 exists to watch.

**One decision was forced by a deadlock in the plan's own decision rule**, and it is worth recording
because it is a shape core cannot see. §E1 regenerates a stimulus category whose panel agreement
falls below 90%. At item 4's registered dose against a within-child variance calibrated to the
cohort, 13.5% of E4b's *concerning* curves drift upward — so over a 20-curve category, where the rule
allows two disagreements, 2.7 are expected and the category fails with probability 0.52 to 0.95 from
construction alone. **Regeneration could not repair it**, because the variance is calibrated rather
than chosen, and the dose could not be raised without abandoning the citation item 4 rests on. The
resolution was to notice that §E1 was asking a between-subject question of a within-subject arm:
E4b's two categories are now adjudicated as **20 within-subject pairs**, one scaffold under both
physiologies, where a curve whose manipulation did not land becomes a *tie* rather than a
disagreement.

**Neither of those is a `publishable` concern, and that is the point of recording them here.** Core
executes a declared design; it has no opinion about whether a panel's decision rule terminates, and
`validate` cannot know that a category will fail a bar for a reason regeneration cannot fix. This
analysis exists to press a real project against the schema, and the last two days have pressed hardest
on the parts of a study that the schema deliberately does not model.

**What is still not measured.** Twelve of the fourteen configs have not executed, and every Azure
cost figure below is arithmetic rather than an anchor. **Three items left that list on 2026-09-10**, and they left it by
one run rather than by argument — the `.transcript.jsonl` writer has now been driven by a write,
`envelope` and `model_version` have been recorded from real calls, and there is a latency anchor.
`system_fingerprint` stays on it and may stay for good: Ollama returns none, so only a hosted
completion can supply one.

**What blocks the rest is now two named registration items, and that is a sharper answer than this
section could give before.** The roster, the prompt and the variable derivations are specified, the
prompt is implemented, and one checkpoint has answered. What remains is not tooling:

| Gate | What it holds | Measured by |
|---|---|---|
| **Item 4** — the age-conditioned concerning/healthy boundary | Seven of the twelve LLM configs declare `physiology: concerning` somewhere, including E3, the root of Layer A; so does E9's matched-magnitude pair. Nothing constructs a deviation without it | `generate_trajectories.py` and `panel_packet.py` both refuse, naming the item |
| **Item 5** — the referral label, its index date and the window | Every config that reads a real trajectory | `cohort_inputs.py` refuses **all fourteen**, because every one declares `visits_pre_index` |

**The second measurement is the one worth carrying, and it is a finding about the configs rather
than about core.** The study's ingestion path was written this week and, run against the real
attribute lists, it declines every arm: `visits_pre_index` is defined in the plan as a pre-index
count on a matched index date, and six configs declare it while carrying `truth.label_source: none`,
so they have no index for it to count against at all.

**Core would catch that too.** These configs draw from `{resolver: growth_trajectory}`, and
`data.units.attributes` naming a value no unit a resolver yielded is
[`E-UNITS-ATTR-MISSING`](reference.md#errors-validate-reports) — met at `validate`, because `validate`
dispatches a declared resolver to resolve the roster, and again at `run`, `draft` and `dry-run`, since
a resolver is user code that may yield different attributes on a later call. So a roster resolved
without that attribute is refused rather than silently dropping it and completing. That is the right behaviour and it is
worth stating as a positive result: **the ambiguity the study owes an answer to is one the schema
surfaces rather than absorbs.** What core cannot do is notice that a *declared and supplied* column
means one thing in Layer C and nothing in Layer A, which is why the question is the plan's.

### The first real completions, and what they cost

**Measured 2026-09-10.** Everything above this heading was produced by `validate`, `dry-run` and two
non-LLM runs. This is the first time anything in this study asked a model a question, and it is
reported separately because a rendering and a response are different kinds of evidence.

**What ran is deliberately not an experiment.** `smoke/local-gemma4/` sits outside `configs/` so
that a reader iterating `configs/*/` cannot pick it up: four units, one condition, one repeat, one
local checkpoint, every limit lowered to let four units through — `min_units_per_cell: 20` is the
plan's floor and 4 is under it. Local on purpose, too: §Cross-Cutting permits the HMS Azure API and
locally hosted open-weight models, and a smoke arm on a checkpoint already on the machine bills no
metered endpoint and sends nothing outward. Its only job was to put the five clauses this study had
implemented against fixtures in front of something that could disagree with them.

**Four of the five hold.** The prompt rendered as two halves with `{{REFERENCE_FRAME}}` substituted;
the transport reached `/api/chat` and came back parsed; `responses.transcript.jsonl` was written by
the plugin's registered writer, which is **the first exercise of suffix dispatch anywhere in this
study**; `envelope: chat_system_message` landed on every call; the apparatus fact carried the
digest rather than a name; `run.yaml` was written and the command exited `0`.

**The fifth did not: six of seven calls returned an empty answer** — and it was a configuration
fault rather than a broken clause, which took three runs of this config to establish. The first two
sat at a 512-token budget, before and after the two transport fixes below, and produced the same
seven-call shape; the third and fourth, at 4,096 and at the 8,192 that shipped, each parsed four of
four. The first two are what the diagnosis rests on:

| | Run 1, before the fixes | Run 2, after |
|---|---|---|
| Calls | 7, for 4 units — three units retried once under the step's own `MAX_PARSE_ATTEMPTS` | 7, identically |
| Parsed | 1 of 7, wrapped in a fenced ` ```json ` block the parser tolerates | 1 of 7, the same unit |
| Empty | 6 of 7 | 6 of 7 |
| `stop_reason` recorded | `null` on every row — the defect | `length` on all six empty rows, `stop` on the parsed one |
| `completion_tokens` | 512 on the six, 487 on the parsed one | identical |
| Latency | 96.6–128.5 s, median **117.0 s** | 83.4–97.4 s, median **88.4 s** |
| Calls over `request_timeout_s: 120` | 2 of 7 | 0 of 7 |
| Retries from transport faults | none — every call returned `200` | none |

**The two latency columns differ because the machine did, and that is the more useful reading.** Run
1 overlapped this repository's own test suite; run 2 had the machine to itself. So ≈88 s is the
unloaded cost of one *truncated* call and ≈117 s is the same call under an unrelated CPU-bound load.
Neither is the cost of an answer — run 3 is, and it is 2.3× higher.

**The record diagnoses itself, and only after the fixes.** `completion_tokens: 512` is exactly
`llm.max_output_tokens`, and it sits beside `stop_reason: length` on all six empty rows; the one that
answered used 487 and stopped on its own. Those two columns together say *cut off at the budget*
without a reader needing to know anything about the model — and in run 1 the same six rows said
`empty`, `512`, `null`, which says only that something went wrong.

**The cause is a budget, and it was in the payload the whole time.** `llm.max_output_tokens` becomes
Ollama's `num_predict`, which caps **reasoning and answer together**; `gemma4:12b` is
thinking-capable, so it spends the 512 on reasoning and the answer never begins. Confirmed
independently of the run, by re-sending one of its own prompts to the same checkpoint: at
`num_predict: 512` the reply is `done_reason: length` with 1,202 characters of reasoning and an empty
`content`, and at `2048` the same prompt answers `{"growth_issues": true}` with `done_reason: stop`
after 634 tokens. Nothing was wrong with the transport, the prompt, or the output contract — each was
correct, and the run still produced no answer. **A study that had shipped this configuration would
have collected a 1-in-7 response rate on its local arms and had nothing in the record to explain
it**, since the one unit that answered needed 487 of its 512 tokens and the margin was invisible.

**Run 3 is the confirmation, and it is reported with the fixes it tested** — [below](#the-fifth-clause-and-the-two-numbers-that-fixed-it). Everything between here and there is what runs 1 and 2 established.

**Three things follow, and only one of them is a defect.**

**A record that says `empty` and not why is not debuggable, and every provider reports why.** The
reason sat unread in three response shapes under three different keys — `done_reason` for Ollama,
`stop_reason` for Anthropic, `finish_reason` for both OpenAI-shaped providers. `Response` now carries
`stop_reason` and the transcript records it beside `status`, so `empty` and `length` sit together.
It is not normalised to a boolean: a reason this transport has never seen has to reach the record as
the word the provider used. **This is the same fault this document files most often** — a field
present in the data and read by nothing — and it was reachable only by making a call.

**Adding that field found a worse one.** The retry boundary rebuilt `Response` field by field, which
made it a silent filter rather than a passthrough: `stop_reason` was populated by the parser, was not
named at the boundary, and reached the step as `None` on the very first call that carried one.
Nothing raised, nothing failed, and the transcript column read `null` for a reason the endpoint had
answered. It is now one `replace` call with the single field it owns. **An enumerated passthrough is
a filter with a maintenance obligation**, and this one had gone stale the moment a field was added
above it.

**`llm.request_timeout_s: 120` was marginal at a 512-token budget and unusable at a real one.**
Unloaded, the slowest of seven truncated calls took 97.4 s — 81% of the budget, with none over it.
Under an unrelated load on the same machine, two of seven exceeded it, and an earlier attempt carries
an Ollama-side `500` whose duration equals the client timeout exactly; the sequence is consistent
with a client disconnect at the budget, though the `500` is the server's report and not a timeout the
step recorded. **A budget that holds only on an idle machine is one a multi-week arm will breach**,
and it breaches it as a failed unit counted against `max_failed_fraction`. Once the token budget was
raised so that answers could finish, one call took **490 s** and the 120 s ceiling stopped being
marginal at all. The template's own default was
`Param(int, default=120, ge=1)` beside a `max_output_tokens` of 512, sitting next to a `provider`
list that offers `ollama` as a first-class choice: **a pair sized for a hosted endpoint in a template
that invites a local one.**

#### The fifth clause, and the two numbers that fixed it

**Both were raised, uniformly, and the two numbers are one decision rather than two.** Every config
that issues a request now carries `max_output_tokens: 8192` and `request_timeout_s: 2400`, which is
also the first time they have been uniform — eleven carried 512 and E3b carried 1,024, and 8,192 is
above both so uniformity costs those arms nothing.

**The budget was set three times in one afternoon, and the pattern is the finding rather than any one
number.** Each measurement was wider than the last and each raised the largest need:

| What was measured | Largest need |
|---|---|
| `gemma4:12b`, two direct probes | 634 tokens |
| plus `qwen3.5:9b`, two direct probes | 2,170 |
| plus four units through the pipeline | 2,393 — from `gemma4:12b`, the model the first probe had already sampled |
| plus `arith_probe_v1` rendered on the heaviest unit | **3,493** |

**The third row is the one to read twice.** It raised the figure using the *same model* the first row
had sampled, which means the first probe's 634 was not a small sample of `gemma4:12b` — it was a
small sample of `gemma4:12b`'s *easy* cases. A budget fitted to observed means would have been fitted
to a tail nobody had seen, and would have been re-fitted at every widening. **A ceiling nobody
reaches costs nothing, so the sizing question is which measurement was widest and not which was
typical.**

**E3b's 1,024 was not arbitrary, and finding out why took reading the prompt rather than the
config.** Neither the plan nor this document explains it, which is what a first pass at this
paragraph concluded and asserted; the reason is in `arith_probe_v1`, whose system half asks the model
to *state the weight-for-age z-score for each visit shown, showing the calculation*, and only then
emit the JSON object. That is a structurally longer answer than the one-field boolean every other arm
asks for, so E3b is the arm with the least headroom at any uniform budget, and it is the one whose
`stop_reason` counts are worth reading first. **Rendering that prompt on the heaviest unit and sending
it to a local checkpoint needed 3,493 tokens over 656 s** — 9,512 characters of reasoning and 515 of
answer, stopping on its own at an 8,192 cap. That is 85% of a 4,096 budget, which is what decided
against 4,096. E3b itself names `azure_openai`, so this is `gemma4:12b` answering E3b's prompt rather
than E3b's own model answering it, and the number is a shape rather than a prediction. **A parameter that differs for a reason living in a
file the reader did not open is indistinguishable from one that differs for no reason** — which is
an argument for a `rationale` beside a budget, not for flattening the value. The coupling is the part worth stating: **a timeout below the time it takes to generate the
whole budget makes the timeout the real budget**, silently, because the config claims 8,192 tokens
and the apparatus enforces whatever fits in the window. At the slowest sustained rate measured here —
4.88 tokens a second — a fully-consumed 8,192-token budget takes ≈1,679 s, so 2,400 s leaves 43% of
headroom. **900 s was the first answer and it was sized against the wrong model**: `qwen3.5:9b`
sustains 7.4 tokens a second, and picking the faster of the two left 7% rather than 70%. Raising the
budget without raising the timeout converts a truncation into a timeout and calls it progress.

**Neither is a reservation, which is what makes the pair cheap.** Both are ceilings and a provider
bills for tokens generated, so a model that stops on its own is unaffected: the pair costs more only
where a call was being cut off, which is the case it exists to fix.

**Re-running the arm that had failed is what settled it, and it moved a number this document had just
stated.** With the new budget the same four units parsed **four of four, with no retries** — seven
calls became four — and `W-STATS-AGGREGATE-FAILED` stopped firing, because a metric with answers in
it has an interval. But the fourth unit spent **2,393 tokens over 490 s**, which is above
`qwen3.5:9b`'s observed maximum and 3.8× what a two-sample probe of `gemma4:12b` *itself* had
suggested — and `arith_probe_v1` then needed 3,493, which is what took the budget past 4,096
altogether. **The tail is heavier than a small probe shows**, and 8,192 is 2.3× the largest figure any
of the four measurements produced rather than 1.7× the third one's.

**What `stop_reason` adds there is attribution, not counting, and the difference is worth being exact
about.** A truncated call has no content, so `parse_screen` already returned `EMPTY` and `EMPTY`
already entered `unusable = refused + malformed + empty` against the contract's 5% threshold — the
guard was never blind to it, and this document's first draft of this paragraph said it was. What was
missing is *which* of the three an unusable call was: a filtered response, a blank one and a
truncated one are one number without `stop_reason` and three with it. The threshold does not read the
new column and does not need to; a maintainer deciding whether to raise the budget again does.

**What this does to the cost table is the part worth carrying forward, and it was measured twice
because the first measurement was of the wrong thing.** Every LLM figure in [§ Cost and execution
summary](#cost-and-execution-summary) is arithmetic over request counts. Against the 512-token budget
the anchor was ≈88 s per request, which put E10's local arms — 2 checkpoints × 4 cells × 5 repeats ×
200 units = **8,000 requests** — at about 8 days of continuous local compute. **That figure was
measured on calls that produced no answer**, and it said so; the direction it was warned to move in
is the direction it moved.

**On calls that answer, the same arms come to ≈470 hours — about 20 days**, from means of 194 s
(`gemma4:12b`, n = 4 through the pipeline at the shipped 8,192 budget) and 231 s (`qwen3.5:9b`,
n = 2 by direct probe). That is
**2.5× the truncated figure**, and the sample is small enough that the multiplier is the honest
finding rather than the total: four calls and two calls, with one 490 s outlier carrying much of
`gemma4`'s mean.

**Three things still move it, and only one of them downward.** The plan and these configs **specify
no concurrency**, which is the one factor that divides rather than multiplies and is a decision
nobody has recorded. Two hundred units will have a heavier tail than four, since one call in four
already needed 2,393 tokens. And this is two checkpoints of a roster whose Azure half has never been
timed at all — E3b in particular, whose prompt asks for a per-visit calculation and needed 3,493
tokens over 656 s when a local checkpoint answered it.

**What does *not* move it is the budget, and that was worth running to find out.** The arm was run
at 4,096 and again at the 8,192 that shipped, and the two runs are identical where it counts: the
same four units, the same four token counts — 487, 557, 634 and 2,393 — every call stopping on its
own, four of four parsed both times. **Doubling the ceiling changed nothing the model produced**,
which is the "a ceiling is not a reservation" argument holding empirically rather than in principle.
Latency differs by the few percent that separates two runs of the same work on a shared machine. What the anchor settles is not the duration but the kind of problem: **the local arms
are scheduling, not rounding**, and no request-count table could have shown that — nor could the
first anchor, which is why a cost figure taken from calls that failed is worth re-taking rather than
carrying forward.

**What is measured about the Azure arms is still nothing.** Three deployments resolve to versioned
snapshots and none has been sent a prompt, so there is no latency anchor, no token count, and no
`system_fingerprint` from a real response — Ollama returns none, which is why the seven calls above
recorded `null` for it, and it is the one fact in the study that only a hosted completion can supply.

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
        # **These two defaults are one decision, and 512/120 was the wrong pair
        # for a template whose `provider` choices include `ollama`.** The budget
        # caps a thinking-capable model's reasoning and its answer together, so
        # the answer is what gets cut; at 512 it never begins, and the record
        # reads `empty` with `stop_reason: length`.
        #
        # **Sized against the largest need measured, and that number moved twice
        # on 2026-09-10 as the measurement got wider.** A two-sample probe of
        # `gemma4:12b` said 557-634 tokens. Adding `qwen3.5:9b` said 2,170.
        # Running four units through the pipeline said 2,393 — from `gemma4:12b`,
        # the model the first probe had already sampled. And rendering
        # `arith_probe_v1`, whose system half asks for a per-visit z-score
        # *showing the calculation* before the JSON, said **3,493**. Each figure
        # was the largest yet, and every widening of the sample raised it: the
        # tail is heavier than a small probe shows, which is the argument for a
        # budget with room rather than one fitted to observed means.
        #
        # 8,192 is 2.3x that largest need. 4,096 would be 85% consumed by the
        # `arith_probe_v1` case alone, which is the arm with the longest answers
        # and therefore the least headroom at any uniform budget.
        #
        # `stop_reason` makes a truncation **attributable**, which is not the
        # same as countable and was first written here as though it were: a
        # truncated call has no content, so `parse_screen` already returned
        # `EMPTY` and `EMPTY` already entered
        # `unusable = refused + malformed + empty` against the contract's 5%
        # threshold. The guard was never blind to it. What was missing is which
        # of the three an unusable call was — a filtered response, a blank one
        # and a truncated one are one number without `stop_reason` and three
        # with it.
        #
        # 2,400 s is what makes the budget reachable rather than nominal. At the
        # slowest sustained rate measured here — 4.88 tokens a second, again
        # `gemma4:12b` — a fully-consumed 8,192-token budget takes about 1,679 s,
        # so **a timeout under that would silently become the real budget**: the
        # config would claim 8,192 and the apparatus would enforce far less.
        #
        # Both are ceilings and neither is a reservation, which is what makes the
        # pair cheap: a provider bills for tokens generated, so a model that
        # stops on its own is unaffected and only a call that was being cut off
        # costs more.
        "llm.max_output_tokens": Param(int, default=8192, ge=1),
        "llm.request_timeout_s": Param(int, default=2400, ge=1),
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
        # **z, not channels, and the rename is the point.** This was
        # `crossing_channels` with a default of 2.0, which the constructor
        # multiplied by a hard-coded 0.67 — so every concerning trajectory
        # drifted 1.34 z, double the 0.67 z pre-registration item 4 fixes,
        # and "a channel" meant 0.67 z here against the plan generator's
        # measured 0.5992 z for the same band. A dose carried in a unit two
        # implementations define differently is a dose that drifts; item 4
        # is stated in z for that reason and this field now matches it.
        "stimulus.crossing_z": Param(float, default=0.67, ge=0.0, le=3.0,
                                     help="Sustained shift in z for a concerning "
                                          "trajectory; pre-registration item 4"),
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

**Every metered figure here is a floor rather than an exact count, and the reason is a clause of the plan rather than a slippage.** The [output contract](#prompt-templates-and-why-they-are-code) retries a malformed answer **once** with the identical prompt — a refusal is not retried, since a retry on an identical prompt tests nothing — so a run costs one extra request per case that came back unreadable and was read on the second ask. The overshoot is bounded and observable: it cannot exceed one request per case, and each run reports `n_retried` beside the unusable rate the same clause requires. **A budget set against the table below should carry that headroom**, and a run whose `unusable_fraction` crosses 5% has a bigger problem than its bill — at that point the cases that remain are a selected subset, which is what the threshold is for.

**Where these figures agree with the plan's own, and where they cannot.** E3's 27,000, E4b's 2,500, E5a's 3,000, E5d's 3,000, E7's 4,000, E8's 10,500 and E9's 2,200 are the plan's own evaluation counts reproduced exactly, which is the arithmetic check that the translation preserved each design's structure rather than its description. E10's is not comparable: the plan replicates five arms across the roster where budget allows and prioritizes two where it does not, and this config is the prioritized E7 replication.

**The full E10 is several times what the table shows.** Replicating E4b, E5b, E8 and E9 across the same five-deployment axis adds 12,500 + 10,000 + 52,500 + 11,000 = 86,000 requests, for **166,200** in total. The plan's own budget rule — prioritize E7 and E5b — is therefore a choice between roughly 80,000 and 166,000, which is the number that decision should be made against.

**The restructure moved this total, and mostly in one direction.** Against the fifteen-config reading of the earlier plan the total was 62,000; it is 80,200 now. Three changes account for nearly all of it and each is a design decision rather than an overhead: **E3 doubled** because the plan added a 300/300 split and both halves have to be screened, **E10 grew by a quarter** because the roster went from four deployments to five, and **E9 shrank** because its magnitude sweep collapsed into one matched contrast. The reference-standard gate's removal costs nothing here — it never issued a request — and saves several thousand clinician-adjudicated curves elsewhere, which is the trade the plan actually made.

**No condition set comes near `limits.max_executions: 500`.** The largest is E10, whose 20 × 5 = 100 repeat-scoped executions come to 142 once every scope is counted — and it is the 100 that the check compares against the budget, not the 142. No config drew [`W-EXEC-BUDGET`](reference.md#warnings-core-reports), which is the warning that comparison raises and the only one this paragraph claims: ten of the fourteen carry a warning of another kind, as [§ Executability on this build](#executability-on-this-build) records. That is worth noting because it inverts the usual worry: what constrains this plan is the request count inside each execution, not the number of executions, and core's execution-count guard is not the limit that will bind.

**What none of this says is what it costs in money, and what it now says about time is partial.** The plan specifies its roster and its prompt, so what is missing is no longer a specification. **One anchor exists as of 2026-09-10** and it is a local one: four units screened on `gemma4:12b` at ≈206 s per request on an idle machine, against a budget large enough for the answers to finish, which puts E10's 8,000 local requests at roughly **20 days** of sequential compute — [§ The first real completions](#the-first-real-completions-and-what-they-cost) has the measurement, the small samples it rests on, and the one factor that divides rather than multiplies. An earlier reading of ≈88 s and 8 days is superseded: it was taken from calls that were truncated before answering, and it is what re-taking a cost figure after a configuration fix is for. **It anchors no metered figure in the table above**, because no Azure deployment has been sent a prompt: the 80,200 is still a request count and a price per request would be invented rather than measured.

**The token counts are now real, and the first set was degenerate in a way worth recording.** In the run against a 512-token budget, six of seven calls stopped at the cap, so `completion_tokens` read 512 — the budget, not the answer's length. **A column pinned to its own limit is evidence about the configuration and not about the model**, which makes it exactly useful for debugging and useless for costing. Against a raised budget the same four units report 487, 557, 634 and 2,393, all stopping on their own, and the spread is the finding: one call in four needed nearly four times the median. What remains structural is the shape a hosted run would fill in — a request per patient per condition per repeat, each landing in the unit table with its own `prompt_tokens`, `completion_tokens` and `latency_ms`.

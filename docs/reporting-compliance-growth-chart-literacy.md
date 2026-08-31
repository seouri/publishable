# Reporting-guideline compliance: growth chart literacy

This document asks one question about [`feasibility-growth-chart-literacy.md`](feasibility-growth-chart-literacy.md): **if the fourteen runs it specifies were executed and written up, could the manuscript comply with the reporting guidelines in [`../standards/`](../standards/README.md)?**

It is non-normative, it is not a feasibility analysis, and it is not part of the shared worked example. It analyses a document that analyses a plan, so it inherits both layers' limits: where the feasibility analysis dates a build claim, this one cites that dating rather than restating it as fact.

**Re-assessed 2026-08-30, against a plan that restructured itself and then wrote its own reporting-standards mapping.** Two things changed underneath this document. The study is now three layers — a counterfactual core reading no EHR label, a clinician panel validating stimuli, and a secondary accuracy layer on a positive-unlabeled referral outcome — so which guideline binds which arm has moved. And the plan now carries a §Reporting Standards section declaring **TRIPOD-LLM** primary with **STARD** for the accuracy layer, mapping all 19 items, plus an Ethics, Governance and Availability section. **The triage below was reached independently and the plan reached the same primary and the same principal adjunct**, which is the most useful thing this document can report: the disagreements that remain are narrow and are named where they occur.

**What it does not do.** It does not complete a checklist. The item lists for STARD-AI, TRIPOD-LLM and RECORD are not in `../standards/` — those files map the landscape and give the decision procedure — so **no item number is quoted anywhere below**, because a fabricated item number is worse than an absent one. What is checked instead is the requirement *families* the standards do enumerate: [`reporting-standards.md`](../standards/reporting-standards.md) § 7, the emphases in its § 5 profiles, and the pipeline mapping in [`reproducibility-standards.md`](../standards/reproducibility-standards.md) § 11. Completing the real checklists against the published guidelines, with page numbers that resolve, remains the submission task.

## Contents

- [Which guidelines apply](#which-guidelines-apply)
- [The verdict](#the-verdict)
- [Tier A — satisfied by the run record](#tier-a--satisfied-by-the-run-record)
- [Tier B — satisfied only after a config or template edit](#tier-b--satisfied-only-after-a-config-or-template-edit)
- [Tier C — prose obligations no configuration can carry](#tier-c--prose-obligations-no-configuration-can-carry)
- [Four compliance risks specific to this design](#four-compliance-risks-specific-to-this-design)
- [Where this lands on the verifiability ladder](#where-this-lands-on-the-verifiability-ladder)
- [What to change, in order](#what-to-change-in-order)

---

## Which guidelines apply

`reporting-standards.md` § 3 says to name the claim in one sentence and read the verb. The claim is: *when a language model screens a pediatric growth trajectory, its output tracks utilization rather than physiology.* The verb is neither *discriminates*, nor *estimates a risk*, nor *improves an outcome* — it is a claim about what an evaluated model's output is a function of. That is a task-performance claim about a language model, evaluated offline across several tasks, and it lands in the TRIPOD-LLM family.

The study is closest to the standards' own worked example *"LLM assigning ICD codes, evaluated against coder-assigned ground truth"* — primary TRIPOD-LLM, adjunct STARD-AI for the accuracy estimation. This study adds an EHR-derived label as the thing under audit, which is what pulls RECORD in.

**The restructure narrowed what the adjuncts govern without removing either.** Eleven of the fourteen runs are the counterfactual core and read no EHR label at all, so a diagnostic-accuracy guideline has nothing to attach to in them: their claims are within-subject response differences, and the correct reading is that STARD governs the three accuracy arms and not the study. That is exactly what the plan's own mapping says, and it is a sharper statement than "STARD-AI as adjunct" was.

| Guideline | Role | Why |
|---|---|---|
| **TRIPOD-LLM** | Primary | An LLM evaluated for a health task, across multiple arms and two prompt families; modular, so the evaluation-only items apply and the development items do not. Its parent TRIPOD+AI supplies the items TRIPOD-LLM does not restate, and covers [E2 and E6](feasibility-growth-chart-literacy.md#e2--the-utilization-baseline) directly — those two *are* prediction-model development, on tabular features, with folds |
| **STARD-AI** | Adjunct, over three arms only | [E2](feasibility-growth-chart-literacy.md#e2--the-utilization-baseline), [E4a](feasibility-growth-chart-literacy.md#e4a--the-matched-real-patient-arm) and [E6](feasibility-growth-chart-literacy.md#e6--the-non-llm-comparator) measure a frozen index test against an EHR-derived reference standard and report a rate at a fixed operating point. STARD 2015's own items apply beneath it — an extension supplements its parent, it does not replace it. **What the reference standard is has changed**: it is a recorded specialty referral on a matched index date, not a clinician adjudication, and the panel that remains validates *stimuli* rather than adjudicating the cases the model sees |
| **RECORD** | Adjunct, and the restructure made it bind harder | The referral outcome is a phenotype derived from routinely collected data, and the plan's own preliminary analysis is a RECORD-shaped argument: it dropped one candidate phenotype after measuring that it was predominantly perinatal, and dropped a utilization covariate after measuring that it ran backwards. `reporting-standards.md` § 5 calls RECORD's phenotype-definition items the single highest-yield addition for clinical AI work *because model performance is frequently an artifact of how the outcome label was constructed* — which is this study's thesis, stated by the guideline. **The label is positive-unlabeled**, which is a phenotype-validity disclosure RECORD's family covers and which no configuration can carry |

That is one primary and two adjuncts, which is the ceiling § 3 Step 5 sets. Three further guidelines will be proposed by somebody and should be declined in the methods, by name:

| Not this one | Why not |
|---|---|
| **CHART** | It governs generative-AI chatbots giving health advice or summarizing evidence. Nothing here is a dialogue, and no output reaches a patient or a clinician |
| **DECIDE-AI** | It governs early *live* clinical evaluation — clinicians using a tool on real patients. No arm here is prospective and none is clinician-facing. Saying so matters: § 9 lists skipping DECIDE-AI for a live deployment as a common failure, so a reviewer will look for the reason it is absent |
| **CONSORT-AI / SPIRIT-AI** | No intervention is assigned to anyone. `allocation: between` on a [`groups`](reference.md#expansion-modes) axis assigns *conditions to units within an analysis*, which is not randomization of an intervention, and describing it as a trial would be the § 9 failure of choosing the guideline by technology rather than by claim |

STROBE's own items are worth completing for the cohort-assembly description, since RECORD extends it — but as material inside the primary submission rather than as a fourth declared guideline.

## The verdict

**Yes, and by an unusual margin on the mechanical half — but the configs do not get there alone, and the two disclosures the standards weight most heavily are exactly the two the source plan has not made.**

Three findings carry the rest of this document.

**Most of what these guidelines ask for is a projection of the run record rather than a research task**, which is `reproducibility-standards.md` § 11's thesis and this design is a near-complete instance of it. Version pinning, non-determinism handling, seeds, split boundaries, subgroup performance, cohort flow with reasons for exclusion, environment capture, and the analysis specification are all *already* in `run.yaml`, the config, or the per-unit tables, because core put them there for its own reasons. Several are recorded more strictly than the guideline asks — the [apparatus gate](feasibility-growth-chart-literacy.md#llm-api-access) fails a run whose deployment moved mid-experiment, where TRIPOD-LLM asks only that the version be reported.

**A third of the item families are prose, and no configuration will ever hold them.** Intended use, the reference standard's construction, the fairness rationale, patient and public involvement, and the ethics and access story are Tier C below. The standards say this themselves, and say it is the point: automating the mechanical items is what creates room for these.

**The binding constraint was never `publishable`, and it has moved.** The earlier assessment named two undecided items in the source — the cohort definition and the model roster and prompt specification — as sitting on the highest-weight families in the two guidelines that matter most. **Both are now written**: the plan carries a Cohort and Data section with variable definitions and a measured profile, and a roster and prompt specification with per-call provenance. What is left in their place is thinner and more ordinary: administrative registration fields (protocol number, consent determination, deposit DOI, funding, conflicts), a compute-resources statement the plan marks *owed*, and a participant-flow diagram that cannot be drawn until the data is pulled. **That is a submission checklist rather than a design gap**, which is a different and much better position than the one this document assessed a day earlier.

---

## Tier A — satisfied by the run record

Each row is a requirement family the standards enumerate, and the artifact that answers it without anyone transcribing anything. Every build claim behind these is dated in the feasibility analysis's [§ Executability on this build](feasibility-growth-chart-literacy.md#executability-on-this-build); this table asserts the *design*, not the date.

| Requirement family | Named by | What answers it |
|---|---|---|
| Exact analysis specification | TOP; ten simple rules | The config, one per run, hashed as `parameters_hash` and hand-editable but never silently — fourteen files, one per run |
| Version pinning of a hosted model | TRIPOD-LLM; `reporting-standards.md` § 7 | `apparatus_facts = ["model_version", "system_fingerprint"]`, probed at `dry-run`, at run start, before every execution and at `freeze`, with a moved fact failing the run |
| Prompt and decoding disclosure | TRIPOD-LLM; § 7 *Model presentation sufficient for use* | Prompt text is a file under `src/growth_chart/prompts/`, inside `code_hash`, so editing one moves the run identity; `prompt.id` names the file and is a `Param` inside `parameters_hash`, which is where a decoding parameter belongs too — the configs shown declare none, and each one the request step passes has to be declared there or it is undisclosed. **The file carries both messages the study sends**, system and user, so what the supplement reproduces verbatim is one object rather than a reconstruction; and which message envelope an endpoint required is recorded per call and per execution, which is the half of that disclosure a study normally cannot make |
| Non-determinism and sampling | § 7; ten simple rules | `{kind: seed, n: 5}` on all fourteen, with dispersion reported as `repeat_spread` rather than folded into `n` |
| Seeds recorded, not narrated | Gold tier; § 11 | Seeds are in the record, per execution, because a repeat *is* an execution |
| Split boundary and leakage | REFORMS; STARD-AI; CLAIM | The unit is the patient by construction; `cluster_by: match_set` keeps a matched pair out of two folds, enforced by core rather than remembered; `growth_label.validate` refuses a comparator config declaring neither `holdout` nor `fold` |
| Flow of participants with reasons | STARD; STROBE | The four-way `n` — `resolved`/`completed`/`ineligible`/`failed` — plus `ineligible.jsonl` carrying the per-unit `io.skip` reason. A STARD flow diagram's denominators and its exclusion reasons are both in the record |
| Indeterminate results | STARD | An unparseable response is a declared policy, `scoring.parse_failure`, hashed with everything else. Its one deviation across the fourteen — [E5b](feasibility-growth-chart-literacy.md#e5b--the-graded-negative-control) routing it to `negative` rather than to `ineligible` — is visible in `diff` rather than buried in a footnote |
| Operating threshold and when it was fixed | STARD-AI | The parser that turns a response into a flag is in `src/`, so the threshold is inside `code_hash`, and E3's decision rule is the moment it froze. That the threshold did not move between arms is provable, not asserted |
| Subgroup performance | TRIPOD+AI; STARD-AI; FUTURE-AI; model cards | `statistics.report_by` over sex, visit band and E5b's three negative strata — prespecified because the config was hashed before the run, and costing no extra executions |
| Preregistration and deviation | TOP; § 10 | `hypotheses`, each carrying the declaring config's `parameters_hash`, so a hypothesis added afterwards renders as exploratory rather than as a swapped primary outcome |
| Environment capture | FAIR4RS; silver tier | `uv.lock` plus interpreter and platform, captured at run time; `reproduce` restores it and stops |
| Provenance from result to inputs | TOP; FAIR; § 11 | `code_hash` over `src/**` and `templates/**`, `parameters_hash`, `input_manifest_hash`, re-verified after the last execution and failing the run if the inputs moved |
| Citable artifacts | Software citation principles | `CITATION.cff` and a LICENSE scaffolded at `publishable new`, before the first commit |
| Task-specific rather than headline performance | TRIPOD-LLM; § 9 | Every arm reports its own metrics with intervals; the single headline number is quarantined as an `Estimate` marked `reported: true`, and its verdict says so |

Two of these deserve to be argued in the manuscript rather than merely satisfied, because a reviewer will not expect them.

**The apparatus gate answers a question STARD-AI cannot ask.** A hosted deployment re-tuned midway through a cross-model arm is normally invisible, and would be reported as between-model heterogeneity. Here it fails the run. That is the difference between reporting a version string and being able to state that the version did not move.

**The four-way `n` is a discipline about attrition, not a convenience.** `reporting-standards.md` § 9 does not list it, because the failure it prevents — a bare `n` that hides either failures or by-design ineligibility — is usually invisible to a reviewer. `limits.max_failed_fraction` governs failures only, and `max_ineligible_fraction` warns separately, so an arm evaluable for a fifth of the roster surfaces as a design problem rather than as a clean result.

## Tier B — satisfied only after a config or template edit

These are reachable, and are not reached by the fourteen configs as the feasibility analysis presents them.

| Requirement family | Named by | The edit |
|---|---|---|
| **Calibration** | § 7, *for any model producing probabilities* | E2 routes its calibration curve to `io.write` as a [step artifact](feasibility-growth-chart-literacy.md#where-every-statistical-procedure-lands), so the plot is deposited and the **numbers are not in the record**. § 7 asks for the intercept and the slope, per validation setting. Derive both in `growth_label.aggregate` beside `auroc`, where a resample gives each an interval — and state in the methods that the item does not bind on the LLM arms, whose output is a binary flag and not a probability |
| **Sample size justification** | TRIPOD+AI, strengthened | Core [refuses power analysis](feasibility-growth-chart-literacy.md#what-core-refuses-and-the-route-for-each) and routes it to *record the target effect size and the resulting n as parameters*. No config shown takes that route. Adding `power.target_effect` and `power.alpha` as `Param`s puts the justification inside `parameters_hash`, where a reviewer can see it was fixed before the run rather than fitted to the result afterwards. **The source half of this is now done**: the plan states a target effect size and a power setting per arm, and generates the table from a script in its own repository, so what remains is carrying those two numbers into the file that ran |
| **Missing data handling** | TRIPOD+AI; CLAIM | Partially covered — `io.skip` carries by-design ineligibility with a reason, and `max_failed_fraction` bounds attrition. What is absent is per-variable missingness in the extract, which is upstream of `input_dir`. Record it as roster attributes so it reaches the unit table, or it becomes a Tier C paragraph |
| **Model card and datasheet** | § 11; model cards; datasheets | Both are listed in § 11 as projections of the record, and neither is produced. `publishable g report` is the seam: a renderer override for this experiment can emit a model card with the per-subgroup performance already computed. This is a formatting task, and § 9 warns specifically against a model card reporting only pooled performance — which `report_by` already prevents |
| **Reproduction tolerance** | § 7, *without a declared tolerance, "reproduced" is unfalsifiable* | Nothing declares one. The natural declaration is the seed arm's own `repeat_spread`: five draws per condition give an empirical run-to-run dispersion, and the tolerance is a statement about it. See [the ladder](#where-this-lands-on-the-verifiability-ladder) |
| **Access tier and license, stated** | § 10; TOP | `publishable new` scaffolds a LICENSE for the code. The patient extract's tier, its governing body, and the license on any released synthetic scaffold are three separate statements, and the synthetic ones are releasable where the extract is not — which is worth taking, because [E4b publishes the scaffolds](feasibility-growth-chart-literacy.md#e4b--the-physiology-preserving-counterfactual) that E7 and E10 consume |
| **Every reported number traces to a run** | § 11's closing invariant | Achievable and unenforced. § 11 proposes it as a build failure rather than a copy-editing task; the `study` bundle is where such a check belongs, since a paper reports several runs |

## Tier C — prose obligations no configuration can carry

Naming these is not a concession. `reporting-standards.md` § 11 ends on exactly this list, and calls it *the items worth human attention*.

**Intended use and the clinical pathway.** TRIPOD-LLM and STARD-AI both require it, and here the honest statement is unusual: no deployment is intended. This is a mechanistic audit of a screening behaviour, and the moment of use it describes is a hypothetical one. Saying that plainly is also what keeps DECIDE-AI correctly out of scope.

**Reference standard construction, and the panel, which are now two different things.** The reference standard for the three accuracy arms is a *recorded referral* — which specialties count, over what window, how a matched index date is assigned to a child with none, and the 12-month look-forward that makes "no referral" mean "none while under observation". That is a phenotype description, and RECORD's family is where it lives. The panel is separate and is no longer a reference standard at all: two to three blinded pediatricians adjudicating roughly 110 constructed curves, whose specialty and experience, blinding, adjudication rule and inter-rater agreement STARD-AI and CLAIM still want described in enough detail to be replicated. The feasibility analysis classifies the panel as [not an experiment](feasibility-growth-chart-literacy.md#what-is-not-an-experiment) — a human reading a picture is not a pipeline core executes — and here that classification costs more than it used to: the panel's output is a **decision to regenerate stimuli or not**, so unlike the earlier design it does not even leave a column an `input_manifest_hash` could pin. Everything about it is prose.

**That the accuracy layer's negatives are unlabelled.** A child with no recorded growth-relevant referral may have had none, been referred outside this network, been referred after the export, had the concern managed without one, or left the practice. Every rate the accuracy layer reports is therefore about the record rather than the child, and the plan words it that way. No configuration carries this: core computes a difference between two arms and has no opinion about what an absent code means. It reaches the record only through the hypothesis `statement` field, which the configs use for exactly that.

**Phenotype and cohort definition (RECORD).** Databases used, the codes and algorithms defining the population, the exposure and the outcome, linkage, cleaning, and validation of derived variables. Implausible-value screening, the declared per-channel plausible ranges, the age-2 floor and the look-forward all run before the roster exists, so they are upstream of `input_dir` by construction. **The plan now writes all of this**, which moves the item from undecided to transcription — and the transcription is not trivial, because RECORD wants the derived variables *validated*, and the plan's own validation of two candidate variables is what caused them to be dropped.

**Fairness rationale.** `report_by` computes per-stratum performance; it cannot say why those strata and not others, or what a difference between them would mean clinically. TRIPOD+AI and FUTURE-AI want the reasoning.

**Patient and public involvement.** STARD-AI and TRIPOD-LLM both carry PPI items and this design has nothing to report against them. State the absence rather than omitting the item, and use GRIPP2 if involvement is added.

**Disclosure of AI assistance in conducting the research** — distinct from AI as the object of study, and easier to record as you go than to reconstruct.

**Ethics approval, data governance, and conflicts.**

---

## Four compliance risks specific to this design

These are the places where a competent reviewer, holding the completed checklists, would push back.

### 1. Synthetic anthropometry read as real

Nine of the fourteen runs show the model constructed trajectories, and the plan has since specified the generator that draws them — a characteristic channel at the cohort's measured between-child SD, AR(1) within-child variation calibrated to its pooled lag-1 autocorrelation, and values rounded to the source units. **That raises the stakes on this risk rather than retiring it.** The z-scores now have a defensible variance structure; the kilograms and centimetres are still back-derived through *a coarse piecewise-linear mean so the rendered table reads like a chart*, and they are **not a growth standard**. A specified generator is easier to mistake for a validated one. That honesty has to survive into the manuscript, because STARD-AI's and CLAIM's dataset-provenance items are exactly where a reader decides how much clinical realism to grant. The disclosure is one sentence and its absence would be a real misreport: internally consistent across the arms of a comparison is the whole claim, and clinically calibrated is not claimed at all. The reference frame carries the same weight — `cdc2000` versus `who2006` changes what every z-score means, it is a `Param` with `choices` so no run executes without it, and `who2006` being declarable but refused rather than silently served from CDC columns is itself the disclosure working.

### 2. A preregistered correction family that the record cannot hold

The plan preregisters four Holm families with an explicit `m`, and puts every other arm in none. Two of the four — `{E5a–d}` and `{E10 model contrasts}` — span runs, because a roster-changing variant is a different run, and `statistics.correction` is computed within one run's condition set — [gap 2](feasibility-growth-chart-literacy.md#gaps-this-analysis-found-in-the-specification) closed it *as a documented limitation, not by a mechanism*, and `study add` still copies records without re-correcting across them.

This is not a reporting-guideline violation on its own; none of TRIPOD-LLM, STARD-AI or RECORD mandates a multiplicity procedure. It becomes one through preregistration: `reproducibility-standards.md` § 9 lists *preregistering a plan and then reporting a different primary outcome without noting the deviation* as a failure mode, and a family corrected at a narrower level than the one registered is that failure in its quantitative form. The route is the one the specification names — correct by hand, state the family's level in the manuscript — and the obligation this creates is that the manuscript's stated family must be checked against what each `run.yaml` actually corrected, since the two now disagree by design.

**The mismatch runs the other way too, and that half is new.** Where the plan declares *no* family, a config can only say `statistics.correction: none`, and core replies that a family of comparisons exists and none of it was corrected — [gap 11](feasibility-growth-chart-literacy.md#gaps-this-analysis-found-in-the-specification), carried by seven of the fourteen configs. For reporting purposes the consequence is precise and small: every interval in those runs records `correction: null`, which is *true*, and a reader who takes that as evidence the analysis forgot a correction would be reading the record correctly and the design wrongly. The methods sentence that resolves it is one line — which arms are a family, and why the rest are not — and it is the same sentence the plan already writes.

### 3. `reported` versus `computed`, and the absent p-values

Every mixed-effects fit, every omnibus test, the conditional logistic regression, the DeLong comparison, McNemar's p-value and the headline shortcut reliance index are [refusals with a single route](feasibility-growth-chart-literacy.md#what-core-refuses-and-the-route-for-each): a `summary`-step `Estimate`, `reported: true`, outside the correction family, never recomputed, with the verdict recording `verdict_rests_on: reported`.

Read against the standards this is a net gain and should be presented as one. Nothing is hidden; a number core did not compute says so in the record, which is a stronger disclosure than a manuscript's undifferentiated results table. Two things must accompany it, though, or the gain inverts:

- The code computing those quantities lives in `src/` step bodies, inside `code_hash` and inside the deposit, so the § 7 requirement of *model presentation sufficient for use* is met by the same repository. It is met **only if the repository is deposited**, which for a `reported` number is load-bearing in a way it is not for a core-computed one.
- The headline index is now a **bounded** function of two main effects rather than a ratio, and it is defined where the ratio was not — including the case the study most expects to see, a model with no physiology response. What is undefined is a model that responds to neither manipulation, which the plan's floor rule handles by declining to interpret the index and reporting both marginal effects instead. A manuscript reporting the index must report those two effects beside it, which is TRIPOD-LLM's task-specific-performance item and the reason § 9 warns against a single headline metric.
- **The refusal now reaches the primary endpoint and the gate.** The study concludes on one quantity through one gate, and both are averages of contrasts, which core stores without recomputing. So the two most consequential numbers in the manuscript will carry `verdict_rests_on: reported` while the four cell contrasts they are built from carry `computed`. Presented plainly that is a strength; presented as a footnote it looks like an evasion, and the difference is one sentence in the methods.

### 4. A study that reports no clinician-agreement statistic, evaluated against guidelines built to ask for one

This risk replaces the previous one, which was that the cohort definition and the model roster were undecided. Both are now written, and the three prompt files in the feasibility analysis remain its own invention standing in for a specification that describes one system and one user message rather than naming a file — a smaller gap than the one it replaces.

What is left is a mismatch of expectations. STARD-AI and CLAIM are built around an index test compared with a reference standard, and a reviewer holding those checklists will look for the model-versus-clinician agreement. **There is none, by design**: the panel validates stimuli, the counterfactual core measures response rather than correctness, and the plan states in its own limitations that no clinician-agreement statistic is reported anywhere. That is a defensible position and it is not the default reading of the guideline, so it has to be stated where a reviewer meets it — in the same sentence that names STARD as governing three arms rather than the study. The plan's §0.6 and §Limitations already carry the wording; what this document adds is that the *record* will look the same way, because five of the fourteen runs declare no ground truth at all — their `run.yaml` files have no truth column for a reader to look for — and six more score against construction rather than against a clinician.

---

## Where this lands on the verifiability ladder

`reproducibility-standards.md` § 1 asks which rung is being claimed, and § 10 asks for it in one sentence in the methods. The answer here is not uniform across the fourteen runs, and stating it as one number would be wrong.

| Rung | Non-LLM arms — E2 and E6 | LLM arms — the other twelve |
|---|---|---|
| Disclosed | Reachable, conditional on Tier C | Reachable, conditional on Tier C and on the registration fields |
| Available | Reachable, and the plan now commits to it: code, configs, lock file, prompts, per-call provenance logs and the synthetic stimuli are deposited; the patient extract is governed and not open, which is stated rather than glossed | Same, and **stronger than it looks** — the counterfactual core's stimuli are synthetic and its outputs shareable, so the part of the study that carries the claim is also the part an outsider can check |
| Runnable | Reached by construction — `reproduce` clones the recorded commit, verifies `code_hash` and restores the environment | Same, plus a deployment and a credential the reproducer must supply |
| Reproduced | Reachable within a declared tolerance; these arms fit deterministic estimators over a fixed table | **Not reachable bit-identically, and the reason is a stated non-promise.** A hosted model samples, and the deployment behind a stable name can be retired |
| Replicated | Out of anyone's control | Out of anyone's control |

The consequence is the Tier B tolerance row, and it has a natural answer this design already pays for. Five seeds per condition make run-to-run dispersion an **estimated quantity** rather than an assumption: `repeat_spread` is what a second party's rerun should be compared against. `reproducibility-standards.md` § 9 lists *evaluating a hosted model without recording its version, which makes exact reproduction impossible and should be stated rather than glossed* — the apparatus gate records the version and refuses to let it move, so the honest claim available here is stronger than the usual one and still stops short of rung four.

## What to change, in order

Six changes, cheapest first. None of them is a redesign.

1. **Declare the guidelines in the methods, by name and version** — TRIPOD-LLM primary, STARD-AI and RECORD as adjuncts — and say in one sentence why CHART, DECIDE-AI and CONSORT-AI are not applicable. § 9 is explicit that an omitted-without-reason guideline reads as an oversight.
2. **Derive calibration intercept and slope in `growth_label.aggregate`**, and state that the item does not bind on the LLM arms.
3. **Add the power basis as parameters** — target effect and alpha — so the sample size justification is hashed with the rest of the pre-registration rather than written afterwards.
4. **State the correction family's registered level in the manuscript**, in both directions, and check it against what each `run.yaml` corrected: the two cross-run families are corrected at a narrower level than registered, and the seven arms registering *no* family record `correction: null` on every interval.
5. **Generate the model card and the datasheet from the record** through a `report` override, rather than writing them by hand.
6. **Declare the reproduction tolerance** in terms of `repeat_spread`, separately for the LLM and non-LLM arms.

One change belongs to the feasibility analysis rather than to the study: it names no reporting guideline anywhere, and the configs it presents were designed against `reference.md` alone. Adding a short section pointing at this document would close that, and would put the Tier B edits where the person writing the configs will see them.

---

**Assessed on 2026-08-30** against `docs/feasibility-growth-chart-literacy.md` as re-derived that day, which reads the plan at `growth-chart-literacy@e6b43ab`, and against `../standards/` as last verified in August 2026. **Its build claims were re-measured on 2026-08-31** and none of this assessment moved: the same fourteen configs, the same warnings, the same two executed arms. What did move is one Tier A row above — the prompt is now two messages carrying the child's sex and the reference frame, and the message envelope is recorded — which strengthens a disclosure rather than changing a verdict. Every claim here about what `publishable` *does* is inherited from that document's [§ Executability on this build](feasibility-growth-chart-literacy.md#executability-on-this-build) and is no fresher than the commit pinned there; every claim about what it *specifies* is from `reference.md` and `design-principles.md`. Guideline versions move — `reporting-standards.md` § 8 lists QUADAS-AI, CLAIRE and BRIDGE-AI in development, any of which could change the triage above — so re-verify against the EQUATOR library before submission rather than against this file.

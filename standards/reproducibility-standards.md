# Reproducibility and Open-Science Standards for Clinical AI and Computational Research

A result that cannot be regenerated is a claim, not a finding. Reproducibility standards specify what has to exist alongside a paper for someone else to obtain the same numbers from the same data, and then to test whether the conclusion survives different data. This document maps those standards, gives a procedure for choosing which apply, and sets out how each maps onto the artifacts a disciplined pipeline already produces.

Companion documents: [`reporting-standards.md`](reporting-standards.md) covers what a study must disclose; [`appraisal-standards.md`](appraisal-standards.md) covers how that disclosure will be judged. [`README.md`](README.md) explains how the three fit together and how often to re-verify them.

Last verified: August 2026. The TOP Guidelines were updated in 2026 and the PRISMA family is mid-revision; check section 13 before relying on a version.

## How to use this document

Section 1 gives the ladder that organizes everything else, because "reproducible" is used for at least five different guarantees and conflating them is the source of most disagreement. Section 3 is the master table, section 4 the selection procedure. Section 11 maps standards to pipeline artifacts and is the part that turns this from a reading list into a build specification.

## 1. The verifiability ladder

Each rung is a distinct guarantee, requires distinct artifacts, and is demanded by distinct standards. A paper can satisfy a lower rung and fail every higher one.

**Disclosed.** The methods are described in enough detail that a competent reader understands what was done. Governed by the reporting guidelines in [`reporting-standards.md`](reporting-standards.md). Requires prose.

**Available.** The data, code, and model are obtainable, under stated conditions, at a persistent identifier. Governed by TOP, FAIR, and journal policy. Requires deposits and licenses.

**Runnable.** A third party can execute the analysis: dependencies resolve, the environment is specified, entry points are documented, and the pipeline completes. Governed by FAIR4RS and artifact-badging schemes. Requires environment capture and an executable entry point.

**Reproduced.** Running it yields the reported numbers, within a stated tolerance, from the same data. Governed by the ML reproducibility tiers and by verification-oriented journal policies. Requires seeds, determinism handling, and a declared tolerance.

**Replicated.** An independent study with new data reaches the same conclusion. Governed by nothing you control; this is what everything below it is in service of.

The standards in this document mostly target rungs two through four. Almost all published clinical AI work sits on rung one, some on rung two, and very little above it — which is why "we followed TRIPOD+AI" and "our result is reproducible" are not the same statement.

## 2. Triage

| If you need to… | Standard |
|---|---|
| Make data findable and reusable by machines | FAIR |
| Make code and pipelines reusable by machines | FAIR4RS |
| Know what a journal or funder will require of you | TOP 2025 |
| Know how far up the ladder your ML work reaches | Heil et al. reproducibility tiers |
| Avoid the specific failures that break ML-based science | REFORMS |
| Report an ML analysis in a biological or biomedical context | DOME |
| Document a clinical AI model so it can be rebuilt | MI-CLAIM, MINIMAR |
| Document a model or dataset for downstream users | Model cards, datasheets for datasets |
| Document a deployed model for clinicians | Model Facts labels |
| Commit to an analysis before seeing outcomes | Preregistration, registered reports |
| Make software and data citable | Software citation principles, CITATION.cff, CRediT |

## 3. Master table

| Standard | Year | Rung | What it specifies | Reference |
|---|---|---|---|---|
| **FAIR Guiding Principles** | 2016 | Available | Data and metadata are findable, accessible, interoperable, reusable — with explicit emphasis on machines doing so without a human intermediary | [*Sci Data* 2016;3:160018](https://doi.org/10.1038/sdata.2016.18) |
| **FAIR4RS** | 2022 | Runnable | FAIR adapted for research software, accounting for executability, composite structure, and versioning | [*Sci Data* 2022;9:622](https://doi.org/10.1038/s41597-022-01710-x); [RDA principles](https://doi.org/10.15497/RDA00068) |
| **TOP 2015** | 2015 | Available | Eight modular standards for journal policy — data citation, data transparency, code transparency, materials, design and analysis, study preregistration, analysis-plan preregistration, replication — each at three levels of stringency | [*Science* 2015;348:1422–1425](https://doi.org/10.1126/science.aab2374) |
| **TOP 2025** | 2026 | Available to Reproduced | Update reorganizing the standards into three categories with an explicit objective of improving verifiability of empirical claims | [*Res Integr Peer Rev* 2026;11:40](https://doi.org/10.1186/s41073-026-00223-0) |
| **ML reproducibility standards (bronze/silver/gold)** | 2021 | Runnable to Reproduced | Tiered requirements for machine learning in the life sciences, from available data and code through documented environment to a fully automated end-to-end pipeline | [*Nat Methods* 2021;18:1132–1135](https://doi.org/10.1038/s41592-021-01256-7) |
| **REFORMS** | 2024 | Reproduced | 32 questions plus paired guidelines for conducting and reporting ML-based science, developed by consensus across computer science, data science, mathematics, social sciences, and biomedicine, with explicit treatment of the three main leakage types | [*Sci Adv* 2024;10:eadk3452](https://doi.org/10.1126/sciadv.adk3452) |
| **DOME** | 2021 | Disclosed to Reproduced | Structured reporting of supervised ML in biology across four areas — data, optimization, model, evaluation | [*Nat Methods* 2021;18:1122–1127](https://doi.org/10.1038/s41592-021-01205-4) |
| **MI-CLAIM** | 2020 | Runnable | Minimum technical information to reproduce a clinical AI model | [*Nat Med* 2020;26:1320–1324](https://doi.org/10.1038/s41591-020-1041-y) |
| **MI-CLAIM-GEN** | 2024 | Runnable | Extension for generative models, including LLMs and diffusion models; preprint | [arXiv:2403.02558](https://arxiv.org/abs/2403.02558) |
| **MINIMAR** | 2020 | Disclosed | Minimum information for medical AI reporting: population, provenance, model architecture, evaluation, transparency | [*JAMIA* 2020;27:2011–2015](https://doi.org/10.1093/jamia/ocaa088) |
| **Model cards** | 2019 | Available | Short structured documentation of a model's intended use, performance by subgroup, and limitations | [FAT\* 2019](https://doi.org/10.1145/3287560.3287596) |
| **Datasheets for datasets** | 2021 | Available | Structured documentation of a dataset's motivation, composition, collection, preprocessing, uses, and maintenance | [*Commun ACM* 2021;64(12):86–92](https://doi.org/10.1145/3458723) |
| **Model Facts labels** | 2020 | Available | One-page documentation of a deployed clinical model for end users | [*npj Digit Med* 2020;3:41](https://doi.org/10.1038/s41746-020-0253-3) |
| **Software citation principles** | 2016 | Available | Software as a citable research product with a persistent identifier and version | [*PeerJ Comput Sci* 2016;2:e86](https://doi.org/10.7717/peerj-cs.86) |
| **Preregistration** | 2018 | Reproduced | Committing hypotheses and analysis plans to a time-stamped record before observing outcomes | [*PNAS* 2018;115:2600–2606](https://doi.org/10.1073/pnas.1708274114) |
| **Ten simple rules for reproducible computational research** | 2013 | Runnable | Practice-level rules: record every step, avoid manual data manipulation, archive exact versions, record seeds, store raw data behind plots | [*PLoS Comput Biol* 2013;9(10):e1003285](https://doi.org/10.1371/journal.pcbi.1003285) |

## 4. Choosing standards: a decision procedure

### Step 1 — Decide which rung you are claiming

Write the claim before choosing standards. "Our code is available" is rung two and needs a deposit and a license. "Our results can be reproduced" is rung four and needs seeds, an environment specification, and a stated numerical tolerance. Claiming rung four while delivering rung two is the most common form of overstatement, and it is checkable, which makes it costly.

### Step 2 — Take the journal and funder requirements as the floor

TOP describes what journals require, at levels from disclosure to independent verification before publication, so the operative question is which level your target venue implements — not whether TOP applies. Funder data-management requirements set a parallel floor. Neither is ambitious; treat both as a minimum rather than a target.

### Step 3 — Add the domain layer

Clinical AI: MI-CLAIM for technical completeness, MINIMAR for the reporting minimum, MI-CLAIM-GEN if the model is generative. Biological or biomedical ML: DOME. ML-based science generally, and especially if leakage is a live risk: REFORMS. These overlap substantially; pick the one your reviewers will recognize and use the others as gap checks rather than completing all of them.

### Step 4 — Separate artifacts by audience

Three documentation artifacts are often conflated and serve different readers. A datasheet describes a dataset to someone deciding whether to use it. A model card describes a model to someone deciding whether to deploy it. A Model Facts label describes a deployed model to a clinician acting on its output. Producing one and calling it the others satisfies nobody.

### Step 5 — Fix the access tier before promising availability

Clinical data is frequently not shareable, and pretending otherwise produces the "available on reasonable request" non-commitment. State the tier explicitly: fully open, controlled access through a named committee with a stated turnaround, synthetic or derived data plus full code, or code and environment only with data unavailable for a stated reason. The last is honest and satisfies more of FAIR than a vague promise does, because code, environment, and metadata can be fully open even when records cannot.

### Step 6 — Stop at one primary plus the artifacts

As with reporting guidelines, breadth is not the goal. One primary standard matched to your field, plus the concrete artifacts — deposit, license, environment specification, seeds, documentation — is worth more than adherence claims to six frameworks.

## 5. Worked examples

**Retrospective imaging model, data under a data use agreement.** Rung achievable: runnable, not reproduced by outsiders. Deposit code and the environment specification with a DOI, publish the trained weights if licensing allows, publish a datasheet describing the cohort and its provenance, publish a model card, and state the access tier for the images with the committee that governs it. Use MI-CLAIM as the completeness check and FAIR4RS for the software deposit.

**EHR risk model developed across three sites.** Add the phenotype definitions, code lists, and extraction queries as first-class artifacts — these are what determine whether anyone can rebuild the cohort, and they are usually the missing piece. DOME or REFORMS for the analysis reporting; the RECORD items in [`reporting-standards.md`](reporting-standards.md) cover the disclosure side.

**Prompted LLM evaluation.** Rung four is achievable only with care, because hosted models drift. Pin the model identifier and version, record access dates, publish the full prompt text including any system prompt, record decoding parameters and the number of samples per input, and report the variability across samples rather than a single run. MI-CLAIM-GEN is the closest fitting standard. If the model is hosted and unversioned, say plainly that exact reproduction is not possible and report the run-to-run spread instead.

**Benchmark or method paper with public data.** Rung four should be the standard, not an aspiration: a single command that runs end to end from raw data to reported figures, in a captured environment, with seeds. This is the gold tier of the ML reproducibility standards, and it is achievable whenever the data are public.

**Systematic review using AI-assisted screening.** Disclose which tool, which version, at which stage, with what human oversight and what error checking. The reporting side is moving quickly here; check the PRISMA family for current requirements rather than assuming.

## 6. Standard profiles

### FAIR and FAIR4RS

FAIR was framed around machine actionability: the point is not merely that a human can eventually obtain the data, but that a computational system can find, retrieve, interpret, and reuse it without a human intermediary at each step. That framing is what makes rich metadata and persistent identifiers non-optional rather than nice to have.

FAIR4RS adapts the principles to software, on the grounds that software differs from data in being executable, composite, and continuously evolving. In practice this means a persistent identifier for a released version, machine-readable metadata describing dependencies and the execution environment, a clear license, and documented provenance. A repository with no version tag, no license, and no environment specification is not FAIR software even when it is public.

### TOP 2015 and TOP 2025

TOP 2015 gave journals eight modular standards — data citation, data transparency, analytic methods transparency, research materials transparency, design and analysis transparency, study preregistration, analysis-plan preregistration, and replication — each implementable at three escalating levels, from requiring authors to disclose whether they used a practice, to requiring the practice, to requiring independent verification before publication. The TOP Factor was subsequently developed to quantify journal-level implementation.

TOP 2025, published in 2026, retains the core of the 2015 framework while responding to a decade of implementation feedback, introducing an explicit conceptual framework centred on the verifiability of empirical research claims and reorganizing the standards into three categories. It is framed as an adaptable coordination framework rather than a universal mandate. When citing TOP, name the version; the two differ in structure and a claim of "TOP compliance" without a version is uninformative.

### The bronze, silver, and gold tiers

The most useful single framing in this document, because it converts an argument into a specification: bronze for data and code publicly available, silver adding a documented dependency and environment specification, gold adding an automated end-to-end pipeline that regenerates the reported results. Journals and reviewers can ask which tier a paper reaches, and authors can answer honestly. Most clinical AI papers claiming reproducibility are at bronze.

### REFORMS

Thirty-two questions with paired guidelines, developed by consensus among nineteen researchers across disciplines, motivated by the observation that ML methods fail in similar ways regardless of field. Its distinctive contribution is treating leakage as a first-class threat and asking authors to justify explicitly that their study does not suffer from the major leakage types, with reference to the survey that found leakage affecting hundreds of papers across seventeen fields. For any prediction or classification claim, the leakage section is the part most likely to change what you do rather than merely what you write.

### DOME

Community recommendations from the ELIXIR machine learning focus group, structured as questions across data, optimization, model, and evaluation. Aimed at biological ML but broadly applicable, and paired with a registry where DOME annotations for published work can be deposited — which makes it one of the few standards in this space with machine-readable adherence records rather than PDF supplements.

### MI-CLAIM, MI-CLAIM-GEN, and MINIMAR

MI-CLAIM asks whether the disclosure is sufficient to rebuild the model, which is a stricter and more useful question than whether the model was described. MINIMAR specifies a reporting minimum covering population, data provenance, model architecture, evaluation, and transparency. Both predate TRIPOD+AI and are largely subsumed by it for reporting purposes, but MI-CLAIM remains the better internal audit for a repository, and MI-CLAIM-GEN extends the logic to generative models where scaling and evaluation raise problems the earlier frameworks did not address.

### Documentation artifacts

Model cards give intended use, evaluation across subgroups, and limitations in a short structured form. Datasheets do the same for datasets, covering motivation, composition, collection process, preprocessing, recommended and discouraged uses, and maintenance. Model Facts labels compress a deployed model into one page for the clinician who has to act on its output. All three are cheap relative to their value, and all three are things a pipeline can partly generate rather than an author write from scratch.

### Preregistration and registered reports

Preregistration separates prediction from postdiction by time-stamping the analysis plan. For prediction-model work the highest-value commitments are the outcome definition, the candidate predictor set, the split strategy, the primary performance measure, and the subgroups. Registered reports go further by moving peer review before results are known. Neither is common in clinical AI, which is one reason the literature's effect sizes shrink on external validation.

### Citation and credit

Software citation principles establish software as a citable product with a persistent identifier and a specific version, which is what makes a dependency claim auditable years later. A `CITATION.cff` file in a repository makes this machine-readable. CRediT provides a standard taxonomy for contributor roles, which matters here because data curation and software work are the contributions most often invisible in author lists.

## 7. Cross-cutting requirements

**Environment capture, not a dependency list.** A list of package names is insufficient; the resolved versions, the interpreter version, the platform, and ideally a lock file or container digest are what make a run repeatable.

**Seeds and non-determinism.** Record every seed, and state where determinism was not achievable — GPU kernels, parallel reductions, hosted model sampling. Then report a tolerance: what deviation from the published numbers still counts as reproduction. Without a declared tolerance, "reproduced" is unfalsifiable.

**Persistent identifiers for everything.** A DOI for the code release, the data deposit, and the model weights. A repository URL without a tagged release and archived snapshot is not a citable artifact.

**Licenses, explicitly.** Unlicensed code is not reusable code, whatever its visibility. Data, code, and model weights may need different licenses, and the model weights case is frequently overlooked.

**Provenance from raw to figure.** Every reported number should trace to a run, and every run to a configuration and an input dataset version. The standard failure is a figure regenerated by hand after a fix, with the underlying number never updated.

**Leakage, treated as a design question.** Declare the split boundary before fitting anything, keep transformations inside folds, separate near-duplicate records, and record which of these were checked rather than assumed.

**Disclosure of AI assistance in the research process.** Distinct from AI as the object of study. Journals increasingly require it for screening, extraction, coding, and drafting; record it as you go, because reconstructing it afterwards is unreliable.

## 8. In development and moving

TOP 2025 was published in August 2026 and journal implementations will lag it, so expect a period where both versions are cited. The PRISMA family is revising to accommodate AI-assisted evidence synthesis and machine-readable outputs. Artifact evaluation and badging schemes from computing venues are being adapted for biomedical journals, and DOME's registry model — machine-readable adherence records rather than PDF checklists — is the pattern most likely to spread. Anticipate that within a few years "reproducible" will be asserted less and tested more.

## 9. Common failure modes

Claiming reproducibility at rung four while delivering rung two.

"Available on reasonable request," which satisfies no standard and correlates poorly with data actually being provided.

A public repository with no release tag, no license, and no environment specification, cited as open code.

Seeds recorded in a notebook that is not the notebook that produced the published figures.

An environment specified as a list of package names without versions.

Publishing a model card that reports only pooled performance, which defeats the purpose of the format.

Regenerating a figure after fixing a bug without regenerating the numbers in the text.

Treating a datasheet, a model card, and a Model Facts label as interchangeable.

Preregistering a plan and then reporting a different primary outcome without noting the deviation.

Evaluating a hosted model without recording its version, which makes exact reproduction impossible and should be stated rather than glossed.

## 10. Deposit checklist

State the rung you are claiming, in the methods, in one sentence.

Deposit code with a tagged release, a persistent identifier, a license, and a `CITATION.cff`.

Deposit the environment specification: lock file, container digest, or both.

Deposit data at the highest access tier permissible, and name the tier and the governing body where it is not open.

Publish the model artifact and the preprocessing pipeline together, since neither reproduces anything alone.

Record every seed and state the reproduction tolerance.

Publish a datasheet for each dataset and a model card for each released model.

Give the registration identifier for the analysis plan.

Include an AI-assistance statement covering the research process.

Verify the whole thing by having someone who did not build it run it from the deposit alone.

## 11. Mapping standards to pipeline artifacts

This is the section that makes the rest actionable. Each requirement below is satisfiable by a pipeline that treats configuration as data and results as immutable, and each is nearly impossible to satisfy reliably by hand.

| Requirement | Standard | Artifact that satisfies it |
|---|---|---|
| Exact analysis specification | TOP, ten simple rules | The configuration file, versioned, one per study |
| Environment reproducibility | FAIR4RS, silver tier | Resolved dependency lock plus interpreter and platform, captured at run time |
| Provenance from result to inputs | TOP, FAIR | Immutable run record keyed to configuration hash and input dataset version |
| Seeds and determinism | Ten simple rules, gold tier | Seeds recorded in the run record, not in prose |
| Split boundary and leakage checks | REFORMS | Split declared in configuration, enforced before any transformation is fitted |
| Subgroup performance | TRIPOD+AI, model cards | Metrics computed per prespecified subgroup as part of the run, not as an afterthought |
| End-to-end regeneration | Gold tier | A single command that reproduces every reported number from the configuration |
| Machine-readable metadata | FAIR, FAIR4RS | Study-level metadata emitted alongside results, not written into a PDF |
| Dataset documentation | Datasheets | Datasheet fields populated from the dataset registration in configuration |
| Model documentation | Model cards, MI-CLAIM | Model card generated from the run record, with performance filled in automatically |
| Citable artifacts | Software citation principles | Release tag, DOI, and `CITATION.cff` produced at publication time |

The design consequence: the artifacts that standards ask for are mostly projections of a single immutable record, and generating them is a formatting problem rather than a research task. What cannot be generated — intended use, the rationale for a fairness analysis, the reason data cannot be shared — is exactly what deserves human attention, and automating the rest is what creates room for it.

A useful invariant to enforce: any number that appears in the manuscript but cannot be traced to a run in the record is a build failure, not a rounding difference.

## 12. References

Every reference links to the publisher record via DOI. Tools and homepages are in section 13.

Wilkinson MD, Dumontier M, Aalbersberg IJ, et al. [The FAIR Guiding Principles for scientific data management and stewardship](https://doi.org/10.1038/sdata.2016.18). *Sci Data* 2016;3:160018.

Barker M, Chue Hong NP, Katz DS, et al. [Introducing the FAIR Principles for research software](https://doi.org/10.1038/s41597-022-01710-x). *Sci Data* 2022;9:622. Underlying principles: [FAIR4RS Principles](https://doi.org/10.15497/RDA00068), Research Data Alliance, 2022.

Nosek BA, Alter G, Banks GC, et al. [Promoting an open research culture](https://doi.org/10.1126/science.aab2374). *Science* 2015;348(6242):1422–1425.

Grant S, Corker KS, Mellor D, et al.; TOP Advisory Board. [TOP 2025: an update to the Transparency and Openness Promotion Guidelines](https://doi.org/10.1186/s41073-026-00223-0). *Res Integr Peer Rev* 2026;11(1):40.

Heil BJ, Hoffman MM, Markowetz F, Lee SI, Greene CS, Hicks SC. [Reproducibility standards for machine learning in the life sciences](https://doi.org/10.1038/s41592-021-01256-7). *Nat Methods* 2021;18:1132–1135.

Kapoor S, Cantrell EM, Peng K, et al. [REFORMS: consensus-based recommendations for machine-learning-based science](https://doi.org/10.1126/sciadv.adk3452). *Sci Adv* 2024;10(18):eadk3452.

Walsh I, Fishman D, Garcia-Gasulla D, et al.; ELIXIR Machine Learning Focus Group. [DOME: recommendations for supervised machine learning validation in biology](https://doi.org/10.1038/s41592-021-01205-4). *Nat Methods* 2021;18:1122–1127. See also the [author correction](https://doi.org/10.1038/s41592-021-01304-2), *Nat Methods* 2021;18:1409–1410.

Norgeot B, Quer G, Beaulieu-Jones BK, et al. [Minimum information about clinical artificial intelligence modeling: the MI-CLAIM checklist](https://doi.org/10.1038/s41591-020-1041-y). *Nat Med* 2020;26:1320–1324.

Miao BY, Chen IY, Williams CYK, et al. [The Minimum Information about CLinical Artificial Intelligence Checklist for Generative Modeling Research (MI-CLAIM-GEN)](https://arxiv.org/abs/2403.02558). arXiv:2403.02558, 2024. Preprint.

Hernandez-Boussard T, Bozkurt S, Ioannidis JPA, Shah NH. [MINIMAR (MINimum Information for Medical AI Reporting): developing reporting standards for artificial intelligence in health care](https://doi.org/10.1093/jamia/ocaa088). *JAMIA* 2020;27:2011–2015.

Mitchell M, Wu S, Zaldivar A, et al. [Model cards for model reporting](https://doi.org/10.1145/3287560.3287596). Proceedings of the Conference on Fairness, Accountability, and Transparency, 2019:220–229.

Gebru T, Morgenstern J, Vecchione B, et al. [Datasheets for datasets](https://doi.org/10.1145/3458723). *Commun ACM* 2021;64(12):86–92.

Sendak MP, Gao M, Brajer N, Balu S. [Presenting machine learning model information to clinical end users with model facts labels](https://doi.org/10.1038/s41746-020-0253-3). *npj Digit Med* 2020;3:41.

Smith AM, Katz DS, Niemeyer KE; FORCE11 Software Citation Working Group. [Software citation principles](https://doi.org/10.7717/peerj-cs.86). *PeerJ Comput Sci* 2016;2:e86.

Nosek BA, Ebersole CR, DeHaven AC, Mellor DT. [The preregistration revolution](https://doi.org/10.1073/pnas.1708274114). *PNAS* 2018;115:2600–2606.

Sandve GK, Nekrutenko A, Taylor J, Hovig E. [Ten simple rules for reproducible computational research](https://doi.org/10.1371/journal.pcbi.1003285). *PLoS Comput Biol* 2013;9(10):e1003285.

## 13. Tools and homepages

[The Turing Way](https://book.the-turing-way.org/) — the most complete practical handbook for reproducible research, including chapters on FAIR, environments, and version control.

[GO FAIR](https://www.go-fair.org/) and [FAIRsharing](https://fairsharing.org/) — FAIR implementation guidance and a registry of standards, databases, and policies.

[Center for Open Science: TOP Guidelines](https://www.cos.io/initiatives/top-guidelines) — TOP versions, the TOP Factor, and journal implementation resources.

[OSF](https://osf.io/) — preregistration, registered reports, and project archiving.

[Zenodo](https://zenodo.org/) — DOI minting for code and data releases, with GitHub release integration.

[Citation File Format](https://citation-file-format.github.io/) — `CITATION.cff` specification and validators.

[CRediT taxonomy](https://credit.niso.org/) — standard contributor roles.

[DOME Registry](https://dome-ml.org/) — machine-readable DOME annotations for published ML studies.

[REFORMS](https://reforms.cs.princeton.edu/) — checklist and guidelines.

[EQUATOR Network library](https://www.equator-network.org/library/) — for the reporting guidelines these standards complement.

# Appraisal Standards for Clinical AI, Diagnostic, and Prediction-Model Research

Appraisal is the question a reader asks after the report is complete: given everything disclosed, how much should I believe it, and does it apply to my patients? Appraisal instruments make that judgment structured and reproducible rather than impressionistic. This document maps the instruments in current use, gives a procedure for choosing among them, and sets out the judgment calls that determine whether an assessment is worth anything.

Companion documents: [`reporting-standards.md`](reporting-standards.md) covers what a study must disclose; [`reproducibility-standards.md`](reproducibility-standards.md) covers what makes the disclosure verifiable. [`README.md`](README.md) explains how the three fit together and how often to re-verify them.

Last verified: August 2026. Several instruments in this space are mid-revision; check the EQUATOR and Cochrane sources in section 13 before relying on a version.

## How to use this document

Section 2 draws the distinction that governs everything else. Section 3 triages by study design, section 4 is the master table, and section 5 is the selection procedure. Sections 8 and 10 are the parts most worth reading even if you already know which tool to use, because they cover the errors that make an assessment misleading rather than merely incomplete.

## 1. Three activities, three kinds of instrument

**Reporting guidelines** ([`reporting-standards.md`](reporting-standards.md)) ask whether the authors disclosed enough. Applied by authors, editors, and reviewers. Item satisfied or not satisfied. STARD-AI, TRIPOD+AI, CONSORT-AI.

**Appraisal instruments** ask whether the study's design and conduct threaten the validity of its estimates, and whether the study population, setting, and intended use match the question being asked. Applied by systematic reviewers, guideline developers, editors, and by authors auditing their own work. Domain-level judgments of low, high, or unclear risk of bias, with a rationale.

**Scoring instruments** produce a number. They are appraisal instruments that have accepted the cost of collapsing heterogeneous concerns into a single scale in exchange for comparability. APPRAISE-AI is deliberately of this kind. Most others are not, and converting them into scores destroys the information the domain structure was designed to carry.

The consequential confusion is the first pair. Poor reporting and high risk of bias are different findings with different remedies: the first is fixed by revision, the second cannot be fixed after data collection. An assessment that rates a study "high risk" because information was missing has measured reporting, not bias, and should record that distinction explicitly. Most tools handle this by allowing an "unclear" or "no information" judgment; use it rather than defaulting to high risk.

## 2. Triage by design

| If the study… | Primary instrument |
|---|---|
| Develops or validates a prediction model, by regression or machine learning | PROBAST+AI |
| Estimates diagnostic accuracy against a reference standard | QUADAS-2, tailored; QUADAS-C for comparative accuracy |
| Is a randomized trial | Cochrane RoB 2 |
| Is a non-randomized study of an intervention | ROBINS-I |
| Examines a prognostic factor rather than a model | QUIPS |
| Is a systematic review whose conduct you are judging | ROBIS (risk of bias) or AMSTAR 2 (methodological quality) |
| Is a clinical AI study and you need a comparable numeric score | APPRAISE-AI |
| Is a body of evidence rather than a single study | GRADE |

Data extraction is a separate step from appraisal and has its own instrument: CHARMS for systematic reviews of prediction model studies, which specifies what to extract before PROBAST+AI is applied.

## 3. Master table

| Instrument | Year | What it assesses | Output | Reference |
|---|---|---|---|---|
| **PROBAST+AI** | 2025 | Quality, risk of bias, and applicability of prediction models and model studies; separate parts for development and for evaluation | Domain judgments plus overall | [*BMJ* 2025;388:e082505](https://doi.org/10.1136/bmj-2024-082505) |
| **PROBAST** | 2019 | Predecessor: four domains (participants, predictors, outcome, analysis) | Domain judgments | [*Ann Intern Med* 2019;170:51–58](https://doi.org/10.7326/M18-1376) |
| **CHARMS** | 2014 | What to extract from prediction model studies before appraising them | Structured extraction | [*PLoS Med* 2014;11(10):e1001744](https://doi.org/10.1371/journal.pmed.1001744) |
| **QUADAS-2** | 2011 | Risk of bias and applicability in diagnostic accuracy studies: patient selection, index test, reference standard, flow and timing | Domain judgments, tailored per review | [*Ann Intern Med* 2011;155:529–536](https://doi.org/10.7326/0003-4819-155-8-201110180-00009) |
| **QUADAS-C** | 2021 | Extension for comparative accuracy questions, where two or more index tests are compared | Domain judgments on the comparison | [*Ann Intern Med* 2021;174:1592–1599](https://doi.org/10.7326/M21-2234) |
| **QUADAS-AI** | in development | AI-specific successor to QUADAS-2 | not yet published | [protocol, *JMIR Res Protoc* 2024](https://doi.org/10.2196/58202); [announcement, *Nat Med* 2021;27:1663–1665](https://doi.org/10.1038/s41591-021-01517-0) |
| **Cochrane RoB 2** | 2019 | Risk of bias in randomized trials, by outcome and by effect of interest | Domain and overall judgments | [*BMJ* 2019;366:l4898](https://doi.org/10.1136/bmj.l4898) |
| **ROBINS-I** | 2016 | Risk of bias in non-randomized intervention studies, benchmarked against a target trial | Domain and overall judgments | [*BMJ* 2016;355:i4919](https://doi.org/10.1136/bmj.i4919) |
| **ROBINS-E** | 2023– | Companion for exposure studies | Domain judgments | [riskofbias.info](https://www.riskofbias.info/) |
| **QUIPS** | 2013 | Risk of bias in prognostic factor studies | Domain judgments | [*Ann Intern Med* 2013;158:280–286](https://doi.org/10.7326/0003-4819-158-4-201302190-00009) |
| **ROBIS** | 2016 | Risk of bias in a systematic review's own conduct | Domain judgments | [*J Clin Epidemiol* 2016;69:225–234](https://doi.org/10.1016/j.jclinepi.2015.06.005) |
| **AMSTAR 2** | 2017 | Methodological quality of systematic reviews, with critical and non-critical items | Confidence rating: high to critically low | [*BMJ* 2017;358:j4008](https://doi.org/10.1136/bmj.j4008) |
| **APPRAISE-AI** | 2023 | Quality of clinical AI studies across six domains: clinical relevance, data quality, methodological conduct, robustness of results, reporting quality, reproducibility | 24 items, 100-point score | [*JAMA Netw Open* 2023;6(9):e2335377](https://doi.org/10.1001/jamanetworkopen.2023.35377) |
| **GRADE** | 2008– | Certainty in a body of evidence for a specific outcome | High, moderate, low, very low | [*BMJ* 2008;336:924–926](https://doi.org/10.1136/bmj.39489.470347.AD) |
| **GRADE for test accuracy** | 2008 | Certainty for diagnostic tests and strategies | As above | [*BMJ* 2008;336:1106–1110](https://doi.org/10.1136/bmj.39500.677199.AE) |

Frameworks that are neither reporting guidelines nor per-study appraisal tools, but which appraise a *system* rather than a *paper*:

| Framework | Year | Purpose | Reference |
|---|---|---|---|
| **FUTURE-AI** | 2025 | Lifecycle guidance across six principles — fairness, universality, traceability, usability, robustness, explainability — as 30 best practices from design through post-deployment monitoring | [*BMJ* 2025;388:e081554](https://doi.org/10.1136/bmj-2024-081554) |

## 4. Choosing instruments: a decision procedure

### Step 1 — Match the instrument to the study's design, not to its claim

This is where appraisal diverges from reporting. A reporting guideline is chosen by what the authors claim; an appraisal instrument is chosen by what they actually did, because bias arises from design and conduct. A paper framed as a diagnostic accuracy study that in fact developed a model on the same data it evaluated is appraised as a model development study under PROBAST+AI, whatever the title says.

### Step 2 — Fix the unit of assessment before you start

The unit is almost never "the paper." Under PROBAST+AI it is one model, in one evaluation: a paper presenting a development plus internal validation plus two external validations yields four assessments. Under RoB 2 it is one result for one outcome, not the trial. Under QUADAS-2 it is one index test in one population at one threshold. Papers that report several of these get several rows, and collapsing them loses exactly the variation that matters.

### Step 3 — Tailor before you assess

QUADAS-2 is explicitly designed to be tailored: the review question is summarized, the signalling questions are adapted, and review-specific guidance is written and recorded before any study is rated. Skipping this step is the most common reason two reviewers disagree, because they are silently answering different questions. PROBAST+AI similarly requires the intended use, target population, and prediction horizon to be specified in advance.

### Step 4 — Separate risk of bias from applicability

They are different findings with different consequences. A study can be internally valid and irrelevant to your setting, or highly relevant and badly biased. QUADAS-2 and PROBAST both keep these axes separate; keep them separate in your synthesis too.

### Step 5 — Choose whether you need a score, and accept the tradeoff

If the purpose is to compare a literature — meta-research, editorial policy, funding triage — a scored instrument like APPRAISE-AI gives you something a domain-level tool cannot, and it was validated for that purpose, with strong interrater and intrarater reliability and correlation with other quality measures. If the purpose is to decide whether one study's estimate can be trusted, use the domain-level tool and read the rationales. Do not manufacture a score from a domain tool.

### Step 6 — Add GRADE only when appraising a body of evidence

Per-study risk of bias is one input to GRADE, alongside inconsistency, indirectness, imprecision, and publication bias. GRADE answers a different question than any per-study tool and does not replace one.

## 5. Worked examples

**Retrospective deep-learning model for pneumothorax detection, developed and externally validated in one paper.** CHARMS to extract, then PROBAST+AI once for development and once per external validation. Pay attention to the analysis domain: partitioning unit, whether preprocessing was fitted before splitting, threshold selection, and whether calibration was assessed at all. If the paper is framed purely as accuracy against a radiologist reference standard and the model was frozen beforehand, QUADAS-2 instead, tailored to that reference standard.

**Head-to-head comparison of two commercial AI triage systems on the same cohort.** QUADAS-C, not two separate QUADAS-2 assessments, because the threat to validity lies in the comparison — differential missingness, differential threshold tuning, and whether both systems saw the same inputs.

**Randomized trial of AI-assisted colonoscopy.** RoB 2, per outcome. Deviations from intended intervention is the domain that usually decides the rating, because blinding of endoscopists is rarely possible and the assistive effect is partly behavioral.

**Before-and-after study of an EHR sepsis alert.** ROBINS-I, with the target trial specified explicitly. Confounding by secular trends and by co-occurring quality-improvement activity is the dominant concern; specify the confounders in advance and rate against whether they were measured.

**Systematic review of prediction models for postoperative delirium, which you are reading rather than writing.** ROBIS or AMSTAR 2 for the review itself, then check whether the review used CHARMS and PROBAST+AI on its included studies. A review that appraised prediction model studies with a trials tool has appraised nothing.

**Auditing your own manuscript before submission.** PROBAST+AI or QUADAS-2 on your own study, done by someone who did not run the analysis. This is the highest-yield use of these instruments for an author, and the one most often skipped.

## 6. Instrument profiles

### PROBAST+AI

PROBAST+AI updates the 2019 tool to reflect a decade of methodological progress in prediction modelling and the use of AI and machine learning, and consists of two distinct parts: model development and model evaluation. The split matters because the questions differ by role — a developer is asked whether the modelling choices were defensible, an evaluator whether the evaluation was independent and adequately powered. It is intended to replace the original PROBAST and to serve model developers, AI companies, researchers, editors, reviewers, healthcare professionals, guideline developers, and policy organisations, for any type of prediction model regardless of whether regression or AI techniques were used.

For AI work, the analysis domain carries most of the weight: sample size relative to the number of candidate predictors and model complexity, handling of missing data, whether hyperparameter selection was nested inside resampling, whether performance was reported with calibration and not discrimination alone, and whether fairness across subgroups was examined.

### QUADAS-2, QUADAS-C, and QUADAS-AI

QUADAS-2 comprises four domains — patient selection, index test, reference standard, and flow and timing — each rated for risk of bias, with the first three also rated for concerns about applicability, using signalling questions and applied in four phases: summarize the review question, tailor the tool and produce review-specific guidance, construct a flow diagram, and judge bias and applicability.

The AI-specific pressure points that QUADAS-2 handles awkwardly are why QUADAS-AI is being developed: dataset curation and provenance, whether the evaluation set was ever touched during development, threshold fixing, and the version of the system evaluated. The QUADAS-AI protocol notes that QUADAS-2 in its current form does not address the unique considerations raised by AI-centred diagnostic systems, and until it publishes, record these concerns explicitly in the free-text rationales rather than forcing them into an existing domain.

### RoB 2 and ROBINS-I

RoB 2 assesses a specific result for a specific outcome, distinguishing the effect of assignment from the effect of adherence, with domains covering randomization, deviations from intended interventions, missing outcome data, outcome measurement, and selection of the reported result. ROBINS-I extends the same logic to non-randomized intervention studies by asking how the study departs from a hypothetical target trial, adding domains for confounding and participant selection. Both are maintained with implementation guidance in the Cochrane Handbook, which is the operative reference rather than the original papers.

### QUIPS

For studies asking whether a variable predicts outcome, rather than whether a model does. Six domains: study participation, attrition, prognostic factor measurement, outcome measurement, confounding, and statistical analysis and reporting. Relevant to AI work when a paper claims a novel biomarker or feature is prognostic, separate from any model built on it.

### ROBIS and AMSTAR 2

Both appraise systematic reviews and are often treated as interchangeable; they are not. ROBIS asks whether bias in the review's conduct threatens its conclusions. AMSTAR 2 provides a broader assessment of quality, including flaws arising from poor conduct whose impact on findings is uncertain, and yields an overall confidence rating driven by a designated set of critical items. Use ROBIS when you need to know whether to believe the review's effect estimate, AMSTAR 2 when you need a defensible summary judgment of review quality.

### APPRAISE-AI

Designed to evaluate primary studies that develop, validate, or update any machine learning model for clinical decision support, across six domains — clinical relevance, data quality, methodological conduct, robustness of results, reporting quality, and reproducibility — comprising 24 items scored to a maximum of 100 points, with points assigned per item according to prespecified criteria reflecting current best practice. It was developed by applying the tool to 28 clinical AI studies spanning model development, silent, and clinical trial phases.

Its distinctive value is granularity where checklists are binary: external validation scores higher than internal validation rather than merely counting as "validation reported." Its distinctive risk is the one all scores carry — a study can score respectably while failing on a single item that invalidates it. Read the item-level profile, not only the total.

### GRADE

Rates certainty in an estimate for a body of evidence, downgrading for risk of bias, inconsistency, indirectness, imprecision, and publication bias, and upgrading in limited circumstances. For test accuracy the framework is adapted, since the relevant question is usually the downstream consequence of testing rather than accuracy itself. Any recommendation drawn from a set of AI studies should carry a GRADE rating; per-study risk of bias alone does not support a recommendation.

### FUTURE-AI

Not a per-study instrument. Six guiding principles — fairness, universality, traceability, usability, robustness, and explainability — operationalized as 30 best practices addressing technical, clinical, socioethical, and legal dimensions across the entire lifecycle from design, development, and validation to regulation, deployment, and monitoring. Use it to appraise a programme or a deployed tool, and to structure a local governance review; do not use it to rate a manuscript.

## 7. Cross-cutting judgment calls

**Two assessors, independently, with documented resolution.** Single-assessor appraisal is not appraisal; the reliability estimates that justify these tools assume duplication.

**Record rationales, not just ratings.** A domain judgment without a sentence of justification is unauditable and cannot be reused by anyone else. This is also what makes an assessment reproducible in the sense of [`reproducibility-standards.md`](reproducibility-standards.md).

**"No information" is a legitimate rating.** Reserve high risk of bias for evidence of a problem, not absence of evidence about one, and report the two separately when summarizing a literature.

**Do not average domains.** An overall judgment in RoB 2, PROBAST+AI, and QUADAS-2 is driven by the worst relevant domain, not by a mean.

**Appraise the version that was evaluated.** For AI systems this is substantive: a study of a hosted model is a study of a moving target, and if the version and access dates are absent, applicability is compromised regardless of design quality.

**Avoid generic tools for AI studies.** The Newcastle-Ottawa Scale and unstructured "quality scores" lack the domains where AI studies actually fail — partitioning, leakage, threshold selection, reference standard construction. Their use in an AI review is itself a signal of low review quality.

**Leakage deserves an explicit check.** No current appraisal instrument names it as a domain. Add it as a prespecified item under analysis: what was the unit of splitting, was any transformation fitted on combined data, were near-duplicate records separated across splits, and was feature selection performed before or inside resampling.

## 8. In development

QUADAS-AI, per the 2024 protocol. Also on the EQUATOR under-development list: CLAIRE, described as a comprehensive reporting and assessing guideline for AI in diagnostic imaging, and BRIDGE-AI, covering cross-design evaluation of AI in digital health diagnosis, decision support, and post-deployment monitoring. Both blur the reporting and appraisal boundary, which is worth watching: the next generation of instruments may not maintain the separation that section 1 relies on.

A 2025 scoping review in *JMIR* catalogues critical appraisal tools for AI in clinical studies and is the best current map of a fragmented space, including domain-specific entrants such as radiomics quality scoring that this document does not cover.

## 9. Common failure modes

Appraising a paper rather than a result, and producing one rating where four were needed.

Rating "high risk of bias" for missing information, then reporting that a literature is biased when it is under-reported.

Using QUADAS-2 untailored, then reporting poor interrater agreement as a property of the tool.

Comparing two index tests with two independent QUADAS-2 assessments instead of QUADAS-C.

Applying PROBAST or PROBAST+AI to a randomized trial of a model-driven intervention, or RoB 2 to a model development study.

Converting a domain-level tool into a percentage and ranking studies by it.

Appraising the paper's claimed design rather than its actual design.

Treating AMSTAR 2 and ROBIS as the same instrument and reporting whichever gives the expected answer.

Omitting applicability entirely, which is the domain that most often determines whether a well-conducted study is usable in your setting.

## 10. Self-audit before submission

Run the design-matched instrument on your own manuscript, ideally with an assessor who did not perform the analysis.

Record the unit of assessment and produce one assessment per model per evaluation, or per outcome for trials.

Write the rationale for every domain, and keep it with the manuscript rather than in someone's notes.

Check the leakage items explicitly, in writing.

State the version and access dates of every model, library, and dataset that the assessment depends on.

If a domain is going to be rated high risk and cannot be fixed, say so in the limitations rather than waiting for a reviewer to find it.

## 11. Wiring appraisal into a reproducible project

Appraisal answers depend on facts the pipeline already knows: the unit of splitting, whether preprocessing was fitted inside the fold, the seed, the number of candidate predictors relative to events, the subgroup breakdown, the model and library versions. Where those facts are generated from the run record rather than recalled, an appraisal becomes checkable rather than asserted.

A workable pattern: keep the completed assessments beside the manuscript, one file per model per evaluation, with each domain rationale citing the run identifier that supports it. Where a domain judgment rests on a number, reference the artifact rather than restating the number, so a corrected run invalidates the claim loudly instead of silently. Treat "domain rationale references a run that no longer exists" as a failure.

The leakage items are the ones worth enforcing mechanically, because they are decidable from configuration: whether the split boundary was declared before any transformation was fitted, and whether the evaluation data were opened more than once.

## 12. References

Every reference links to the publisher record via DOI. Tool homepages are in section 13.

Moons KGM, Damen JAA, Kaul T, et al. [PROBAST+AI: an updated quality, risk of bias, and applicability assessment tool for prediction models using regression or artificial intelligence methods](https://doi.org/10.1136/bmj-2024-082505). *BMJ* 2025;388:e082505.

Wolff RF, Moons KGM, Riley RD, et al.; PROBAST Group. [PROBAST: a tool to assess the risk of bias and applicability of prediction model studies](https://doi.org/10.7326/M18-1376). *Ann Intern Med* 2019;170:51–58. [Explanation and elaboration](https://doi.org/10.7326/M18-1377): *Ann Intern Med* 2019;170:W1–W33.

Moons KGM, de Groot JAH, Bouwmeester W, et al. [Critical appraisal and data extraction for systematic reviews of prediction modelling studies: the CHARMS checklist](https://doi.org/10.1371/journal.pmed.1001744). *PLoS Med* 2014;11(10):e1001744.

Whiting PF, Rutjes AWS, Westwood ME, et al.; QUADAS-2 Group. [QUADAS-2: a revised tool for the quality assessment of diagnostic accuracy studies](https://doi.org/10.7326/0003-4819-155-8-201110180-00009). *Ann Intern Med* 2011;155:529–536.

Yang B, Mallett S, Takwoingi Y, et al.; QUADAS-C Group. [QUADAS-C: a tool for assessing risk of bias in comparative diagnostic accuracy studies](https://doi.org/10.7326/M21-2234). *Ann Intern Med* 2021;174:1592–1599.

Guni A, Sounderajah V, Whiting P, Bossuyt P, Darzi A, Ashrafian H. [Revised tool for the quality assessment of diagnostic accuracy studies using AI (QUADAS-AI): protocol for a qualitative study](https://doi.org/10.2196/58202). *JMIR Res Protoc* 2024;13:e58202.

Sounderajah V, Ashrafian H, Rose S, et al. [A quality assessment tool for artificial intelligence-centered diagnostic test accuracy studies: QUADAS-AI](https://doi.org/10.1038/s41591-021-01517-0). *Nat Med* 2021;27:1663–1665.

Sterne JAC, Savović J, Page MJ, et al. [RoB 2: a revised tool for assessing risk of bias in randomised trials](https://doi.org/10.1136/bmj.l4898). *BMJ* 2019;366:l4898.

Sterne JAC, Hernán MA, Reeves BC, et al. [ROBINS-I: a tool for assessing risk of bias in non-randomised studies of interventions](https://doi.org/10.1136/bmj.i4919). *BMJ* 2016;355:i4919.

Hayden JA, van der Windt DA, Cartwright JL, Côté P, Bombardier C. [Assessing bias in studies of prognostic factors (QUIPS)](https://doi.org/10.7326/0003-4819-158-4-201302190-00009). *Ann Intern Med* 2013;158:280–286.

Whiting P, Savović J, Higgins JPT, et al.; ROBIS Group. [ROBIS: a new tool to assess risk of bias in systematic reviews was developed](https://doi.org/10.1016/j.jclinepi.2015.06.005). *J Clin Epidemiol* 2016;69:225–234.

Shea BJ, Reeves BC, Wells G, et al. [AMSTAR 2: a critical appraisal tool for systematic reviews that include randomised or non-randomised studies of healthcare interventions, or both](https://doi.org/10.1136/bmj.j4008). *BMJ* 2017;358:j4008.

Kwong JCC, Khondker A, Lajkosz K, et al. [APPRAISE-AI tool for quantitative evaluation of AI studies for clinical decision support](https://doi.org/10.1001/jamanetworkopen.2023.35377). *JAMA Netw Open* 2023;6(9):e2335377.

Guyatt GH, Oxman AD, Vist GE, et al.; GRADE Working Group. [GRADE: an emerging consensus on rating quality of evidence and strength of recommendations](https://doi.org/10.1136/bmj.39489.470347.AD). *BMJ* 2008;336:924–926.

Schünemann HJ, Oxman AD, Brozek J, et al.; GRADE Working Group. [Grading quality of evidence and strength of recommendations for diagnostic tests and strategies](https://doi.org/10.1136/bmj.39500.677199.AE). *BMJ* 2008;336:1106–1110.

Lekadir K, Frangi AF, Porras AR, et al.; FUTURE-AI Consortium. [FUTURE-AI: international consensus guideline for trustworthy and deployable artificial intelligence in healthcare](https://doi.org/10.1136/bmj-2024-081554). *BMJ* 2025;388:e081554.

Critical appraisal tools for evaluating artificial intelligence in clinical studies: [scoping review](https://www.jmir.org/2025/1/e77110). *J Med Internet Res* 2025;27:e77110.

## 13. Tool homepages

[riskofbias.info](https://www.riskofbias.info/) — current versions, templates, and guidance for RoB 2, ROBINS-I, and ROBINS-E.

[Cochrane Handbook for Systematic Reviews of Interventions](https://training.cochrane.org/handbook) — operative implementation guidance for RoB 2 and ROBINS-I, more current than the original papers.

[GRADE Working Group](https://www.gradeworkinggroup.org/) — guidance series and GRADEpro.

[AMSTAR](https://amstar.ca/) — AMSTAR 2 checklist and online form.

[TRIPOD statement](https://www.tripod-statement.org) — PROBAST and PROBAST+AI materials sit alongside the TRIPOD checklists.

[EQUATOR Network library](https://www.equator-network.org/library/) — for reporting guidelines that pair with each instrument here, and the under-development lists.

# Standards

Three questions decide whether a study is worth anything to anyone outside the group that ran it. Was enough disclosed to understand it? Is its design sound enough to believe it? Can its results be regenerated? Each question has its own set of consensus instruments, its own audience, and its own failure modes — which is why they get three files rather than one.

| File | Question it answers | Primary reader | When to open it |
|---|---|---|---|
| [`reporting-standards.md`](reporting-standards.md) | What must this study disclose? | Author, editor, reviewer | Before writing the methods; before submission |
| [`appraisal-standards.md`](appraisal-standards.md) | Given the disclosure, how much should I believe it? | Reviewer, systematic reviewer, author self-auditing | When reading others' work; before submission |
| [`reproducibility-standards.md`](reproducibility-standards.md) | Can the results be regenerated, and by whom? | Author, data steward, engineer | At project setup; at deposit time |

## How they relate

Reporting, appraisal, and reproducibility form a chain in which each link makes the next one possible. Complete reporting is what allows appraisal to reach a judgment rather than a shrug. A favorable appraisal is what makes reproduction worth attempting. Successful reproduction is what makes the reported claim something other than an assertion. Break any link and the ones after it cannot be evaluated: an unappraisable study cannot be trusted no matter how reproducible its numbers are, and a perfectly appraised study whose pipeline no one can run has produced a conclusion nobody can extend.

The three sets of instruments overlap in content and diverge in purpose, and every common mistake in this space is a substitution of one for another. Rating a study "high risk of bias" when information was simply missing measures reporting, not bias. Publishing a completed TRIPOD+AI checklist and calling the work reproducible confuses disclosure with regeneration. Running PROBAST+AI on a manuscript and treating the score as a reporting audit gets both wrong. Each file states its own boundary in its first section for exactly this reason.

One asymmetry worth internalizing: reporting failures are fixable at revision, appraisal failures are fixed only by designing the study differently, and reproducibility failures are cheap to prevent and expensive to retrofit. That ordering is the argument for reading [`reproducibility-standards.md`](reproducibility-standards.md) first even though it comes last in the chain.

## Where to start

Starting a study: [`reproducibility-standards.md`](reproducibility-standards.md) section 4 to fix the access tier and the target rung, then [`reporting-standards.md`](reporting-standards.md) section 3 to identify the guideline that will structure the methods.

Writing up: [`reporting-standards.md`](reporting-standards.md) sections 3 and 4 for guideline selection and stacking, then [`appraisal-standards.md`](appraisal-standards.md) section 10 to audit your own manuscript before a reviewer does.

Reviewing or synthesizing: [`appraisal-standards.md`](appraisal-standards.md) sections 2 through 5.

Depositing code and data: [`reproducibility-standards.md`](reproducibility-standards.md) sections 10 and 11.

## What is not here

Conduct standards are absent by design. There is no equivalent of EQUATOR for conduct, because it fragments into statistical methodology, regulatory requirements, data and interoperability standards, and research ethics — four bodies of guidance with different audiences and update cadences that no single document can serve. Regulatory guidance for AI as a medical device, and data model standards such as OMOP and CDISC, belong in their own files if and when the work touches them.

## Re-verification

Every file carries a `Last verified` line. Treat it as an expiry date, not a footnote.

This landscape moves faster than most reference material. Within roughly eighteen months: CONSORT and SPIRIT were both replaced by 2025 editions, leaving their AI extensions attached to superseded parents; TRIPOD+AI superseded the TRIPOD 2015 checklist, which should no longer be used; STARD-AI was published and then corrected; CHART and TRIPOD-LLM appeared where nothing existed before; and the TOP Guidelines were restructured. QUADAS-AI, PRISMA-AI, and several imaging-specific instruments remain unpublished and will change these files again when they land.

A stale standards reference is worse than none, because it is cited with confidence. Someone will complete a checklist against a version their target journal no longer accepts, or claim adherence to a tool that has been replaced, and the error will surface at review.

Practical minimum: re-verify before each submission, and on a fixed cadence otherwise. Check the [EQUATOR library](https://www.equator-network.org/library/) and its under-development lists for reporting guidelines, [riskofbias.info](https://www.riskofbias.info/) and the [Cochrane Handbook](https://training.cochrane.org/handbook) for appraisal tools, and the tool homepages listed in each file's final section for everything else. Update the `Last verified` line even when nothing changed, so the next reader knows the gap was checked rather than ignored.

## Conventions

Cite standards by name and version, always — "CONSORT 2025", not "CONSORT". A version-less claim of adherence is uninformative and usually wrong.

Link every reference to a DOI or publisher record, so a claim can be checked in one click.

Note the provenance of anything reconstructed rather than verified, so the next editor knows which links to re-check first.

Keep one owner per file. Shared ownership of a reference document means nobody re-verifies it.

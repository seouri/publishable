# Scoping: sixth pass of `feasibility-growth-chart-literacy.md`

**Measured 2026-09-17 against `publishable@af0d3d5` and the study at
`gcl-measurements@82e75ab`.** Core has not moved since the fifth pass; **the study has**, and it
moved because of the fifth pass' own recommendations. Every claim below was read off the code or a
command's output.

This pass exists to correct the fifth pass, not core. Four of its claims are wrong and three of
them were written in it rather than inherited — which is the *under-counted and missing surface*
pattern turned inward for the second day running.

## What moved, and why

The fifth pass asked two questions and the study answered both in code:

| fifth pass said | the study did | commit |
|---|---|---|
| a pre-sweep canary would catch apparatus breakage cheaply | added `step01b_canary`, `scope = "run"`, twenty cases under base parameters | `577a416` |
| `unusable_over_threshold` gate-vs-report is a live decision | **report**, plus the canary; and `max_failed_fraction` made to guard something | `577a416`, `82e75ab` |

## Correction 1 — the plan triple moved, and the fifth pass had just re-measured it

`62 / 450 / 106,260` was re-measured at `af0d3d5` in the fifth pass. Adding one `run`-scoped step to
`ScreenExperiment` changed it. Measured now over all fourteen configs:

| | fifth pass | now | delta |
|---|---|---|---|
| conditions | 62 | **62** | none — a `run`-scoped step adds no condition |
| executions | 450 | **462** | +12, one per screening arm |
| unit-executions | 106,260 | **109,700** | +3,440 |

**That last figure overstates the canary's cost by about 14×, and the reason is worth a sentence
rather than a footnote.** A `run`-scoped step is handed the whole roster, so `dry-run` counts ~287
unit-executions for a step that issues **twenty** requests. Real added cost is 12 × 20 = **240
requests**, 0.07% of E3's 27,000 alone. `dry-run`'s unit-executions is the documented billing proxy,
and here it is a poor one — not a defect in core, which cannot know a step ignores most of what it
is handed, but a caution for anyone budgeting a plan that contains a sampling step.

## Correction 2 — `0.05` is withdrawn, and the fifth pass recommended it in this document

The fifth pass wrote: *"Tightening the metered arms to `0.05` (30 of 600) stops such a fault roughly
four times sooner while still leaving a very wide margin over an observed zero."* **That is wrong,
and the error is a denominator.** `max_failed_fraction` counts **distinct units that failed in at
least one execution, over the roster** — not requests. A unit screened once per screening execution
therefore amplifies a per-request failure rate by its number of exposures. At E3's 45 executions:

| threshold | units | per-request failure rate that trips it |
|---|---|---|
| 0.05 | 30 | **0.1139%** |
| 0.10 | 60 | 0.2339% |
| 0.20 | 120 | 0.4946% |

`0.05` trips on ordinary metered-API noise and would stop a 27,000-call plan for it. The fifth pass
compared an observed-zero attrition against 121 permitted units as though the threshold were
per-request, and missed a **45× amplification**. `0.2` stays, and the arithmetic is now a comment in
all twelve metered configs, because an unexplained number is what invited the wrong change.

## Correction 3 — the knob guarded nothing, so "too loose" was the wrong complaint entirely

The deeper error under correction 2: the fifth pass argued about the *value* of a threshold that
could not fire. Measured across the study's eleven screening arms, every route for a unit yielding
no result was covered:

- parsed → recorded;
- refused / malformed / empty under `ineligible`, which all eleven arms set → `io.skip` →
  `ineligible`, and `max_ineligible_fraction` **only warns**;
- a transport failure → appended to `failures` → the step **raised**;
- `parse_failure: failed`, which **no config sets** → the same raise.

And since `af0d3d5` a raised execution contributes no unit failures. **So `max_failed_fraction`
could not fire in any arm for any reason**, and the fifth pass' "too loose" was an argument about a
number with no reader.

**Raising was the worst available option, and the fifth pass got this backwards too.** It wrote that
`step03_screen` *"raises after the unit loop and after `io.write`, so every unit it did settle is
recorded and both artifacts are on disk before the execution fails."* The unit rows are **not**
recorded: `runner.py:868-883` puts `io.finalize()`, `recorded`, `skipped` and `rows` inside the
runner's `try`, **after** `step.run` returns, so a raise discards every row the execution had
recorded — up to 600 billed calls — while feeding the threshold nothing. One dropped request threw
away 599 answered units and guarded nothing by doing it. That is the 19-hour failure class one level
down, still live after `af0d3d5` fixed the counting above it. The study now leaves such units
**unsettled and completes**, which is the only routing that reaches the guard.

## Correction 4 — the gate-vs-report decision is settled, and one convergence argument dissolves

Settled as **report**, on the ground the fifth pass itself identified: for six of the eleven arms the
unusable rate is a property of the manipulation, and E3 exists to ask whether how a trajectory is
written down changes what a model does with it. A gate there would suppress the finding.

What replaces the gate is the canary, which is safe for a structural reason rather than a careful
one: a sweep applies per condition, a `run`-scoped step executes outside them, so the canary
**cannot see** E3's nine formats. Its threshold is `0.25`, not the `0.05` the fifth pass proposed:
at twenty cases a `0.05` bar means "abort on two", which fires on **26.4%** of runs whose true rate
is the 0.05 the study tolerates. So the fifth pass' closing argument — *"the step's own threshold is
already 0.05 … two independent routes to the same figure"* — **dissolves**: one of the two routes
was withdrawn and the other was never the same question. Twenty cases cannot measure a 5% rate.

## What this pass did not check, and the dependency is now known-stale rather than unverified

The **sixteen byte-identical blocks** were not re-checked by the fifth pass either, and are now
**known to have drifted**: twelve of the fourteen configs gained the `max_failed_fraction` comment
at `82e75ab`. The document's claim that every quoted config is "byte-identical to a file
`publishable validate` accepted" is false for those twelve as written. Re-quoting them, or restating
the claim as *accepted-as-quoted apart from comments*, is the remaining work.

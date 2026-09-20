# Scoping: a failed `run`-scoped step stops the plan

**Measured 2026-09-19 against `publishable@233ad27` (v0.2.6) and the study at
`gcl-measurements@f216082`.** Every claim below was read off the code or off a
run record, and the line numbers are quoted from the commit named.

## The defect, as it actually happened

`gcl-measurements` added `step01b_canary` on 2026-09-17 in answer to E3 losing
19 hours of metered work: twenty cases at `run` scope, before the sweep, raising
above 0.25 unusable. On 2026-09-18 it was run for the first time on an arm that
sweeps a `serialize.*` field and **raised in 0.007 seconds** — and the plan
carried on into the sweep with no apparatus check at all.

    step01_summarize_units -> completed
    step01b_canary         -> failed      E-STEP-SWEPT-PARAM
    step02_construct       -> completed
    step02_serialize       -> completed
    …

**The guard cannot stop anything, and that is core's half rather than the
study's.** `runner.py:885` is explicit:

    except Exception as exc:  # a failed execution never stops the run

So a raise marks the execution `failed` and the loop continues. Nothing else
reaches it either: since `af0d3d5` a raised execution contributes **no unit
failures**, so `limits.max_failed_fraction` never trips on it — deliberately,
because one dropped socket should not kill a 27,000-request plan. The study's
own docstring assumed the opposite (*"Nothing else available here stops a
plan"*, implying a run-scoped raise does), and that assumption was never true.

## What core already has, and what it is missing

| | |
|---|---|
| `StopSignal` (`runner.py:46`) | a mutable `reason`/`code`/`message`, constructed by the caller and **already shared by two stoppers** — the `max_failed_fraction` guard and the apparatus gate |
| the stop itself | `stop.reason = …` then `break` out of the execution loop (`runner.py:970-975`) |
| `run_record.run_status` | maps a closed vocabulary of three reasons to a status; `max_failed_fraction` yields `partial`, not `failed` |
| `truncated` block | written when a plan stops short, and what `resume` reads to continue |
| **missing** | any way for a *step* failure to reach that machinery |

**So this needs no new mechanism.** A third reason joins a vocabulary already
designed to carry more than one, and the stop reuses the same `break`.

## The rule is already specified. It has never had code.

**Found while writing this plan, and it rewrites it.** `reference.md` § What
`status` means, and when a run keeps going already says, as one of the three
things that produce `status: failed`:

> A `scope: "run"` step that raises takes every condition with it — there is no
> shared cohort for them to condition on, so continuing would mean executing a
> plan whose first premise is missing.

The code has never done that. E5d's canary raised at `run` scope on 2026-09-18,
every condition ran anyway, and the record reads `status: completed`.

So this is not a feature to design. It is
[*assuming a documented rule has code behind it*](../../CLAUDE.md#reading-the-documents)
from the other side — a row whose check was never built — and the work is to
make the code say what the document already says. Two consequences:

- **The status is `failed`, not `partial`.** An earlier draft of this plan chose
  `partial` on `max_failed_fraction`'s precedent. The specification chose
  otherwise and its reasoning is better than the draft's: run-scoped executions
  come first in the plan, so when one raises there are no condition results at
  all, and `failed` means *there is nothing to report*. That is literally true
  here.
- **No new `reference.md` row is owed for the behaviour**, because the behaviour
  is already written. What the document owes is a dated note that it was
  unimplemented until now — the same shape as the *Corrected 2026-09-14*
  sentence three paragraphs below it.

## The decision, and what it refuses

**A raise from a `run`-scoped step stops the plan. A raise at any other scope
does not.**

The grounds are that scope already carries exactly this distinction. A
`run`-scoped step executes **once, outside the conditions, for the whole run's
sake** — a roster summary, a shared artifact, a pre-flight probe. Its failure is
an outage of the run's premise. A repeat-scoped raise is one execution of many
and is the case `af0d3d5` deliberately stopped counting; that stays untouched.

Three alternatives, each refused with its reason:

| Refused | Why |
|---|---|
| A config knob (`limits.abort_on_step_failure`) | A declarable field for something structural. Core already knows the scope; asking the config to restate it invites a run whose guard is off because nobody set it |
| A public `AbortRun` exception a step raises | New importable surface, and it lets a **repeat**-scoped step stop a plan — which is precisely what the canary's own docstring argues must never happen, since aborting on a hard-to-read swept format would suppress the finding E3 exists to make |
| "Stop after N failed executions" | Blunt, and it partially reverts `af0d3d5`: N=1 makes one dropped socket fatal again, and N>1 makes the canary's single failure invisible |

**`summary` scope is excluded** and the reason is that it runs last: stopping
after it saves nothing and would only change a status.

**The status is `failed`**, as specified, and the consequence is that the run
is *not* resumable — `run.yaml` is written, so a second attempt meets
`E-RESUME-RUN-ENDED` and starts a new run instead. That is the right trade here
and costs nothing: a run-scoped step raises before any condition has executed,
so there is no metered work to preserve. The canary's whole point is to fail at
twenty requests rather than at twenty thousand.

## What changes

1. `runner.execute_plan` — after a `run`-scoped execution records `failed`, set
   `stop.reason` and `break`. Four lines, at the site that already breaks.
2. `run_record._STOP_REASON_TO_STATUS` — the new reason maps to **`failed`**.
3. `docs/reference.md` — a dated note on the sentence that has been true in
   prose and false in code, in the house's own correction shape.

No new diagnostic code and no new `§ Errors` row: the step's own error is
already recorded per execution and rendered by `report`, and `failed` already
carries exit `4`. A new code here would owe a row for a state the document
already describes under another name.

## How it will be shown to work, and to be able to fail

| Test | Mutation that must turn it red |
|---|---|
| A `run`-scoped step that raises stops the plan: later executions absent, status `failed` | Remove the scope check |
| The step's own error survives into the record, so the reader learns *why* | Map the reason to `partial` instead of `failed` |
| **A repeat-scoped step that raises does NOT stop the plan** — `af0d3d5`'s guarantee, and the control that keeps this narrow | Fire on every scope rather than on `run` |
| A `run`-scoped step that *completes* does not stop the plan | — (guards the trivially-wrong implementation) |

The third is the one that matters: without it, "stops the plan" is satisfiable
by an implementation that stops on any failure at all, which would re-break the
19-hour case this whole line of work started from.

## What this does not do

- **It does not make the canary correct.** The canary's own threshold, sample
  and placement are the study's; this only makes its raise mean something.
- **It does not read a step's body.** Core still learns nothing about what the
  step was doing — only its declared scope and whether it raised.
- **It does not change `max_failed_fraction`.** Attrition and outage stay
  separate, which is the distinction `af0d3d5` bought.

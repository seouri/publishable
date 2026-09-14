# Scoping: resuming a run that ended `partial`

**Measured 2026-09-14 against `publishable@91c8148`**, with the failure that prompted it at
`2026-08-28-gcl-measurement-data/.../run_2026-09-13T20-04-32Z_c1a577a`. Every claim below was read
off the code or that record, not off the documents.

## What happened, in the order it happened

1. `step03_screen` raised `RemoteDisconnected` on one execution of 45 — a dropped socket, 19,800
   calls into a 27,000-call metered run.
2. `runner.execute_plan` recorded that execution `failed` and continued to its own guard.
3. `_units_failed_anywhere` counted **every unit of that execution** as failed: 300 of a 600-unit
   roster. `limits.max_failed_fraction` is `0.2`, so `0.5 > 0.2` and the plan **broke**
   (`runner.py:942-948`), setting `stop.reason = "max_failed_fraction"`.
4. **11 of 45 screening executions were never attempted.**
5. `run_record.run_status` maps the two apparatus reasons and **deliberately not** this one, so it
   fell through to the fold: some completed ⇒ `partial`.
6. `run.yaml` was written. `resume` then refuses `E-RESUME-RUN-ENDED` for any directory holding one.

Net: **one dropped socket cost 19 hours of metered work**, with no route back.

## Three things measured that the documents do not say

**1. The record does not say the plan was truncated.** `run_status` receives `stop` and `planned`
and uses both — for the status decision and for the silent-truncation assert — and **writes neither
into `run.yaml`** (`run_record.py:27-62`; the call site is `cli.py:3866`). Measured on the record:
`status: partial`, 53 execution entries, and **no `not_run`, `pending`, `skipped` or `unattempted`
marker of any kind** for the 11 that never ran. A reader sees `partial` and cannot tell 45-of-45
with one failure from 34-of-45.

**2. `reference.md` § What status means says `max_failed_fraction` produces `failed`; the code
produces `partial`.** The document lists it as one of *"four things"* that produce `failed`
(line 909). `run_record.py`'s own comment says it is *"deliberately absent"* from the mapping and
falls through. The code's behaviour is the better one — a run with 33 usable executions has plenty
to report, and `failed` means *"there is nothing to report"* — so **the document is what should
change**, which is this repository's own rule applied in the direction it usually is not.

**3. The guard's stated premise does not hold for this failure.** § What status means justifies the
stop as *"unit failures only accumulate, so once the fraction is past the threshold no later
execution can bring it back."* That is true of a unit that cannot be measured and false of 300 units
whose execution lost a socket — a retry recovers every one. **Core cannot tell the two apart**, and
nothing here argues it should; the premise is simply narrower than the guard.

## What the existing filing already settled, and what it left open

`spec-defects.md` line 5550 holds the sibling question, **OPEN, owner unassigned**, and it is
explicit about the reasoning to engage rather than rediscover:

> Writing `run.yaml` **ends the run** … That is the right trade for a **moved** fact, which cannot
> move back … Deciding that trade for the retryable class needs a rule this slice does not have —
> *when may a resume declare a run over?*

That is this scoping's question, arriving from the other side: not *when may a resume end a run* but
**may an operator continue one core ended?**

## The design, and why it breaks no principle

**A record is never modified — so do not modify one.** `resume` on a directory whose record says the
plan was **truncated** continues into a **new run directory** that inherits the completed
executions. The first record stays byte-identical and keeps saying `partial`; the second names its
ancestor. This is the shape `reproduce` already has (destination derived from the record, not from a
flag) and `lineage.py` already holds the reader and the attempt counter.

It does **not** overrule `max_failed_fraction`. Core's decision to stop was correct on the
information core had. What the design adds is that **continuing is the operator's call and is
expressible**, which today it is not at any price.

Four invariants checked against it:

| Invariant | Effect |
|---|---|
| A run record is never modified | Preserved — the second run writes its own |
| Operation commands take paths and nothing else | Preserved — `resume <dir>`, no flag |
| Three hashes identify a run | Preserved — the second run re-checks all three and refuses a moved tree exactly as today |
| `run.yaml` means the plan ended | **Narrowed**, and this is the change: it means *that attempt* ended |

## Task order, smallest first

1. **Record the truncation.** `run.yaml` gains what `run_status` already receives: that the plan was
   cut short, the reason, and the executions never attempted. Correct under every design, and a
   prerequisite for any of them — today neither a reader nor a command can tell a truncated run from
   a complete one.
2. **Correct § What status means** on `max_failed_fraction`, which the code has contradicted since it
   was written.
3. Then, and only with 1 in hand, the continuation route.

**Nothing below task 1 is built yet.** This file is the measurement.

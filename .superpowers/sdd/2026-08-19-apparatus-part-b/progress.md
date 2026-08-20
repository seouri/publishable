# H7d Part B — the apparatus: gate and stop — ledger

Design: `docs/superpowers/specs/2026-08-19-apparatus-part-b-design.md` (14 decisions, **plus an
appended § Ruling from the controller**). Plan: `docs/superpowers/plans/2026-08-19-apparatus-part-b.md`
(13 tasks, six batches). Baseline at `814eadd`: **2423 passed, 1 skipped, 2 xfailed.**

**Part A observes and records and cannot stop a run. Part B is the slice that can.** That inverts the
risk: Part A's was a false record, Part B's is **a run that stops when it should not** — so every batch's
review is scoped to what it can actually see, and the batches that can stop a run get `run`-level
reviews. Part A's only Critical was **invisible to every direct-call probe** and surfaced only through an
end-to-end `run`.

## The ruling that narrowed the design before it reached the plan

The design's re-measurement found that **`reference.md` § What status means contradicts itself three ways
and the code answers a fourth**, and that **an all-completed truncation is described by no row at all**.
It proposed fixing that partly by changing what `max_failed_fraction` reports.

**I read the test that pins the current behaviour, and its docstring does not merely assert it — it
argues for it:** *"`max_failed_fraction` is a fraction of UNRESOLVED units, not of raised executions, and
`run_status` reports `completed` even though the plan stops short — the guard and the execution-level exit
code are two different mechanisms."*

**Ruling: `run_status` is widened for the apparatus only; `max_failed_fraction` keeps `completed`; the
question is filed.** Two grounds. **That guard is not H7d's** — re-deciding it changes every run that uses
it, apparatus or not, and a slice about the apparatus inheriting a neighbour's status semantics is scope
creep even when the new answer is better. And **editing a shipped assertion *plus the argument
justifying it* in a slice about something else is indistinguishable in the record from weakening a pin to
pass** — the design itself priced the change at exactly that.

**Cost if wrong:** a truncated all-completed run keeps reporting `completed` at exit 0, which is
arguably dishonest, for as long as the filing goes unclaimed.

**And the order it establishes: a document may not be made self-consistent by widening a behaviour
change.** Task 1 settles § What status means **about the apparatus only**, leaves the failure-fraction
clause alone, and **files the remainder** — the design confirmed by reading all four passages that the
section **cannot** be made self-consistent without a further code change, so saying so is the deliverable.

The design's answer to the ruling was better than the ruling asked for: the third stop reason is
**threaded and genuinely read**, by the branch that suppresses the truncation assert, so it is a
**documented no-op rather than a new unread enum member** — and it leaves its eventual owner's change as
one mapping entry.

## The plan's corrections against the code — eight, and two reshaped a task

- **`run_a_project` crashes on the exit code task 8 introduces.** It returns `run_dir: None` **only** for
  `EXIT_WRONG`, and otherwise reads `executions.jsonl` — which a run-start probe raise never writes.
  Measured by driving it: the run directory holds `environment`, `manifest`, `sweep.yaml` and nothing
  else. So task 8 is one literal **plus one helper**, and the widening is verified **by the suite's
  count** rather than by the reading that suggested it.
- **`E-APPARATUS-CHANGED` must NOT join `APPARATUS_CODES`**, which the design left unruled. Every member
  of that frozenset is pinned after Part A's Major 2, and a changed fact never crosses that boundary, so
  admitting it would add an **unpinned member** — the exact finding Part A's whole-branch review raised.
  `STOP_CODES` is minted instead, both members pinned.
- **The truncation guard is a bare `assert`, not a coded error** — a coded one would mint a sixth `E-`
  code owing a § Errors row for a state **no config can reach**. A narrowing rather than a widening.
- **Fixture T's mixed arm did not exist and had to be constructed**, because the design asserted it was
  "every shipped `EXIT_PARTIAL` truncation test's assertion" **while itself measuring that those tests
  are not truncations.** Constructed and run: 2 of 5, `[completed, failed]`, `partial`, exit 3.
- **Two document sections give the gate two different comparison rules** — "its own first observation"
  against "the first **answered** observation". Task 1 gains a step.

## The guard pin, and the honest thing the plan admits it cannot yet know

**Task 12 runs first**, three arms all **captured by running** at `814eadd`, not transcribed: a clean run
(`len(executions.jsonl) == len(sweep.yaml["execution_order"]) == 4`, which makes Decision 5's
`len(plan) == len(results)` **behaviour rather than a comment**), an all-completed truncation (2 of 5,
`completed`, exit 0), and a mixed truncation (2 of 5, `partial`, exit 3). Its mutation adds
`"stopped_at": None` — the shape Decision 3 refuses, mirroring Part A's `probe: null`. **If it fires
during task 6 or 7 that is a finding, not an edit.**

And the plan says plainly what it could not measure: **whether Part A's Fixture N test is a real sentinel
for a spuriously-firing gate.** It looks like one, **nobody has run the mutation**, and task 13
prescribes the measurement **without assuming its outcome**, with a fixture owed if the sentinel turns
out imaginary. That is the *reading a mutation's silence as confirmation* row, avoided in advance.

## Batch 1 — tasks 12, 1 — the pin and the document, no behaviour changed

Commits `2a10c3a` (the three-arm guard pin), `a59ef6f` (`reference.md` consistent about the apparatus
only), report `e1e178f`. Suite 2423 → **2426**.

### Review: both verdicts PASS — no Critical, no Major

**The circularity risk resolved, and the proof is the interesting part.** Arms B and C exist to protect
the controller's ruling that `max_failed_fraction` keeps `completed` — so if the pin *were* the protected
test, a later batch could satisfy the pin by editing the very thing it guards. The reviewer settled it by
running a **record-only status flip**: the shipped `max_failed_fraction` test **passed** while arm B
**failed** on `run["status"] == "completed"` — **an assertion the shipped test does not make at all.**
Not circular. And the property that makes it non-circular is the one the report described as a shortcut:
**arm B duplicates the shipped fixture rather than reusing it.**

All three arms discriminate, verified by three separate mutations, and **neither B nor C is an
absence-only control** — the reviewer instrumented the guard to check arm C's arithmetic directly rather
than inferring it (`failed=20 resolved=20 nres=2`).

**The ruling held under inspection:** `git diff` touches three files, **none under `src/`**; the protected
test's assertions and docstring are **untouched**; the `max_failed_fraction` clause in `reference.md` is
**byte-identical**.

**One Minor is a carry-forward worth naming here rather than only in a report.** `reference.md` states
**unconditionally** that a moved fact keeps the record, while decision 4 rules `Moved | 0 results → none |
exit 1` — and **the same commit qualified the unreachable twin but not this one.** It was
**brief-prescribed**, which is exactly why the batch's own review of its work did not catch it. Owed by
task 8.

**And the fourth "zero disagreements" report on this project was the fourth to be wrong.** Two real
divergences were found by measurement — an unreported brief departure that was an *improvement* (reading
`sweep.yaml` instead of the helper the brief named), and a helper named by the brief and never consumed.
**The transferable form: a claim carried from brief prose is a claim about the code, and brief-prescribed
text is where "zero" hides.** Every one of the four was found in prose the brief supplied, never in the
implementer's own reasoning — which suggests the check to add is *grep what the brief asserted*, not
*think harder*.

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

**Fix round 1 — all seven Minors closed** (`7d907b2`, `d9886ef`): two fixed in code and docs, two
carried forward with **named owners** (the unqualified moved-fact record wording → task 8; the
`experimental-designs.md` residual → task 11's filing), the rest corrected in the report's prose,
**including the disagreement count from zero to two.** Suite unchanged at **2426**.

**And the `ruff format` diagnosis was false again.** The round reported that a bare `ruff format .` had
reformatted `reference.md`'s fenced Python block wholesale and that it restored from a saved copy.
Measured: copy, run, diff — **byte-identical**. **No damage** — the batch's `reference.md` diff is six
intentional lines and the fenced block is intact, verified rather than assumed.

**This is the second occurrence of the identical false diagnosis, by a different agent on a different
slice**, which is `CLAUDE.md`'s own bar for a repeated misreading — so **it now has a row in § Two
mechanical traps.** The narrow lesson is not *don't restore*: it is that **whatever moved those bytes it
was something else**, and a diagnosis naming the wrong cause leaves the real one in place to recur. Both
times the agent flagged it, which is why both were caught; neither checked it, which is why both
recurred.

## Batch 2 — tasks 2, 3 — the comparison and its code, and not one call site

Commits `c46e07d` (`Observations.changed`), `a384dbd` (`E-APPARATUS-CHANGED` and `STOP_CODES`), report
`bfe1818`. Suite 2426 → **2435**. Nothing wired, confirmed by grep.

### Review: spec compliance PASS; quality PASS conditional on one Major closing before task 4

**All five of Decision 1's readings plus per-condition scope behave as ruled** — verified by the
reviewer's **own** sequences, built independently of the shipped fixture, and the shipped fixture
confirmed able to separate them by a non-degenerate most-recent mutation failing exactly the reading-5
test.

**Major: a `nan` fact reports a change against itself, and it is precisely Part B's named risk arriving
before the wiring.** `coerce_scalars` admits non-finite floats, so a `nan` fact returns
`('f', nan, nan)` **on its first observation** — `changed: nan → nan`. Not reachable at this commit, but
**the moment task 4 wires the gate a probe with a constant `nan` fact stops the run at the run-start
round**, which falsifies Decision 11 directly. **Ruling: close it in batch 2, not task 4** — task 4's
prescribed fixtures cannot see it, so deferring is shipping it. The owner was **determined rather than
guessed**: `reference.md`'s `E-APPARATUS-FACT-TYPE` row admits `float` **unqualified**, so the remedy is
a reflexivity-safe comparison rather than a narrowed type.

**Second Major: a docstring naming two fixtures that do not exist, to disclaim the mechanism that
actually pins the thing.** `STOP_CODES`' docstring claimed each member was "pinned by its own fixture —
Fixture U … Fixture G1 — rather than one shared assertion"; **both fixtures are absent from `tests/`**
and the only pin **is** the shared set-equality assertion it disclaims. The comparison is also
**inverted** — `APPARATUS_CODES` is the set with genuine per-member pins, which the reviewer confirmed by
deleting a member and watching its own named test fail. **A reader greps for those fixture names and
finds nothing.**

**And a mutation whose two branches could not differ was read as the stronger evidence.** The batch's
most-recent shim updated inside `record`, making the comparison `x vs x` for **every** transition, and
the report called that *"a stronger discriminator"*. The reviewer built the non-degenerate two-map shim
and got the correct result. **The fixture was sound; the reasoning about it was not** — which is the
distinction *a mutation is a claim too* exists to draw.

**Fifth "no disagreements" claim, fifth time wrong, and again in prose the brief supplied** — the brief's
*"no fixture can reach it"* was false, and the batch's own narrowing of that assert was correct and
necessary while being filed as a clarification. **The check that would have caught all five is the same
one: grep what the brief asserts before repeating it.**

**Fix round 1 — all five findings closed** (`abb04a9`, `9e50912`). Suite **2436**. The `nan` mutation was
run against the full unfiltered suite (1 failed under the mutant, 2436 after revert), and the shipped
fixture was reconfirmed sound with a **correctly non-degenerate** mutation matching the reviewer's own
result.

**I verified the `nan` fix myself, including that it did not over-suppress**, which is the failure mode a
reflexivity guard invites: `nan` against `nan` now returns `None`, while **`nan → 1.0` still fires**, and
all five of Decision 1's readings are intact — including `1.0 → null → 2.0` firing against `1.0` rather
than against the `null`. A guard that had silently exempted every `nan` comparison would have passed the
prescribed fixture just as well.

## Batch 3 — tasks 4, 13 — the gate wired; the first batch where a run can stop

Commits `033c09a` (the ordering chain), `935902f` (the run-start round and the sentinel measurement),
report `5e29991`, review `f526b46`. Suite 2436 → **2439**.

**The batch's whole risk was firing when it should not, and it does not.** The reviewer built **six**
end-to-end runs of its own — a constant fact over six executions, `null → value`, `value → null`, an
absent undeclared key, a constant **`nan`** (its first trip through the ledger's JSON write, the
fingerprint and `run.yaml`, so **batch 2's fix survived the wiring**), and **three conditions holding
three values of one fact** — and got **zero false stops.**

**The sentinel measurement was made rather than assumed, and it came back real.** Mutating `changed` to
fail on `null → value` failed Part A's Fixture N test plus four others. The plan had said plainly that
nobody had run it and prescribed the measurement **without assuming its outcome**; had it come back
imaginary, a fixture was owed. **This is the first time on either part that a prescribed measurement of
an existing test's sentinel value was actually performed** — and the reviewer reproduced it with an
independently built mutation it first confirmed non-degenerate.

**Major: a live credential leak, the fifth of this class here, and a filing had already predicted it.** A
declared credential held as an **`int`** fact that then moves prints `changed: 13579 → 999` to stderr.
Two causes compose: `check_facts` **skips containment for non-`str`** values, and `E-APPARATUS-CHANGED`
sits **outside `APPARATUS_CODES`**, so it reaches `main`'s **bare printer**.

**The second cause is plan correction 4's own consequence** — the exclusion was right that admitting an
unpinned member was wrong, and wrong about the containment that exclusion silently removed. **Ruling:
`STOP_CODES` gets containment with both members pinned individually, in this batch, because the leak is
live at HEAD** and Decision 14's redacting Collector is a batch away. And `spec-defects.md`'s open
fact-key entry **literally predicted it**: *"a future code added outside that set … would reopen the
leak."* **A filing anticipated the defect and the batch walked into it** — so the entry is updated to
record that the predicted reopening happened, and the non-`str` carve-out, which is the disk half and
**filed nowhere**, gets its own entry.

**Second Major: the count discriminator task 4 exists to establish cannot be reached by any ordering
mutation.** Gate-before-`record` **crashes** at the reflexivity assert batch 2 added, and that assert
fires on the first answering observation of **any** fact, so no fixture routes around it. **The append
half is real** — the assert-safe form fails the end-to-end test on its own `len(ledger) == 4`. So the
ordering is **guarded but not pinned as claimed**, and the defect is the overclaiming docstring. Worth
noting the shape: **batch 2's fix made batch 4's prescribed mutation unreachable**, which no per-task
brief could have anticipated.

**Fix round 1 — both Majors and all six Minors closed** (`3b62c82`, `6b66b5f`). Suite **2442**.

The containment filter now admits `STOP_CODES` beside `APPARATUS_CODES`, reusing the existing redacting
`Collector` as an **interim** fix ahead of Decision 14's own — and **I verified the pin myself rather
than the behaviour alone**: dropping `STOP_CODES` from the filter fails
`test_a_moved_int_valued_credential_is_redacted_through_the_widened_wrapper` and nothing else, so the
containment is pinned by a named end-to-end test rather than by the fix's presence. Reverted
byte-identical; 2442 restored.

**The disk half was deliberately left open and filed** — the plaintext value still reaches
`apparatus/probes.jsonl`, which is pre-existing and orthogonal to the stream leak. Splitting it that way
is right: the stream leak was created by this batch and the disk one was not, and a single fix covering
both would have made the new filing indistinguishable from the old defect.

Major 2 closed by **deleting** the false "only assertion that can see this ordering" claim and replacing
it with two honest pins — a direct test of what the reflexivity assert actually guarantees, and **a
call-order spy witnessing the real sequence.** The spy is the better answer to a discriminator no
mutation can reach: when the guard is louder than the mutation, **observe the order rather than perturb
it.**

Decision 11's wrong cost-if-wrong sentence was corrected in the design **by dated append**, which is the
right form — a spec records what was decided when it was written.

## Batch 4 — tasks 5, 6 — the stop mechanism and the status contract

Commits `e056ef7` (`StopSignal` and the `break`), `f1b2a7a` (`run_status` widened for the apparatus
only), report `8aa2cfd`. Suite 2442 → **2450**. Both verdicts PASS; nothing blocks the batch.

**No credential can reach any stream on the stop path** — the item I put first, because task 6's wiring
means an apparatus stop **no longer escapes to `command_run`'s containment at all**, and three shipped
end-to-end tests were updated as a result **including batch 3's credential-leak regression test.** The
reviewer built its own fixtures for **both** codes with the credential held as an `int` **and** as a
substring, and got nothing on stdout, stderr, or disk — **with a positive control proving the fixtures
could see a leak.** Its judgement on the updated test: **honest, necessary, and stronger** — the
assertion moved from *"a redacted render is present"* to *"the credential is absent"*, and mutation (b)
confirms it fails when the credential leaks. **Updating a leak pin because the mechanism moved is
legitimate; what makes it legitimate is that the new assertion is harder to satisfy.**

**The controller's ruling held under inspection.** `max_failed_fraction` keeps `completed`; arms B and C
of the batch-1 pin verified **append-only** by extracting and diffing function bodies (zero removals) and
still discriminating; the protected test untouched; and the arithmetic 2442 + 3 + 5 = 2450 rules out
silent deletions. **The third stop reason is more load-bearing than the design predicted** — dropping
`and stop is None` fails the direct pin **and both end-to-end arms**, where the design expected it to be
blind end to end. So the compromise that avoided a new unread enum member turned out to be genuinely
read.

**Major 1 is carried to task 7 with its siting settled rather than left to be rediscovered:** a
zero-results stop currently **writes `run.yaml` and repoints `latest`**, which Decision 4 refuses — and
before this batch the corner was **accidentally** compliant. Task 7's guard must sit **before
`assemble_run_yaml` and before the `latest` repoint.** It does not crash, which settles one of the plan's
own *could not measure* items.

**And Major 3 traces to my own instruction, which is worth recording as such.** I had batch 3 widen the
containment filter to admit `STOP_CODES` because the leak was live at HEAD. **Task 6's wiring then made
that arm unreachable** — narrowing it back leaves the full suite unchanged — so it is dead code carrying
the claim that it *"keeps a live leak from shipping"*. **Ruling: keep the arm, delete the claim.** The arm
is cheap insurance if a later task routes a stop back through `command_run`; **a comment asserting it
prevents a leak, unreachable by any test, is the exact shape that produced this slice's Critical.** Two
stale consequences follow it, including a `spec-defects.md` entry whose *"Verified by running"* sentence
describes an assertion the test no longer makes — **a filing whose evidence has gone stale is worse than
one that never had any.**

A fourth consecutive batch shipped a docstring naming a fixture or state wrongly. The narrow form here is
the most avoidable yet: **when your own change makes a sentence false, that sentence is in the diff you
are already reading.**

**Fix round 1 — all findings closed except Major 1, which is carried by design** (`6d5d3f0`). Suite
unchanged at **2450**; every fix was prose or comment. Major 1 travels to task 7 **with its siting
requirement attached** rather than as a description of a defect.

## Batch 5 — tasks 7, 8 — the record on a stop, and `EXIT_EXTERNAL`'s first reader

Commits `bf66cf4` (the record), `11ab231` (the codes), report `2b88cd4`. Suite 2450 → **2452**.
**Spec compliance FAILS on one row; task quality PASS.**

**The credential pin was strengthened, strictly additively** — the reviewer built **four** fixtures (an
int credential moved, an int credential unreachable with digits in the raise message, a substring
credential, and a clean-run control) and found **nothing on stdout or stderr on either stop path**, with
a **positive control** that leaked the plaintext when `stop_c.credentials` was unwired and failed both
its own fixture and the shipped test. `"13579" not in output` survives, two assertions were added, and
**the only assertions deleted anywhere in the batch are three now-false negatives.** Second batch running
to update that test, and second time the update made it harder to satisfy.

Also verified by running: the record holds **first-answered** while the ledger holds **the mover** — the
asymmetry Decision 1's grounds rest on; the replacement for a genuinely blind Fixture Z arm
discriminates **and** asserts positives; and the zero-results guard precedes both sinks, proven by a
**third** mutation the batch did not run — moving the guard *between* the `run.yaml` write and the
`latest` repoint, which is what establishes the two sinks are **independently** pinned rather than jointly.

### The spec failure is mine, and recording it that way is the point

**An unreachable apparatus with zero results exits `1` where Decision 4 requires `5`.** Five sources
contradict the code, including **`reference.md` § Exit codes as written by this branch's own task 1**.

Batch 4's finding was that a zero-results stop must not write `run.yaml` or repoint `latest`, and **I
relayed it as "task 7's `if not results: return EXIT_WRONG` must be sited before both".** Decision 4's
table has **four rows**, and `exit 1` belongs to the **moved** + zero-results row only; **unreachable +
zero results is `exit 5`.** I passed one row's remedy along as though it governed both, and the
implementer built exactly what I said.

**The transferable form: a carried finding loses its scope unless the scope travels with it.** Batch 4's
review stated the siting requirement precisely and said nothing about which row it belonged to, because
in that context there was only one. Relaying it into a task that owns **four** rows is where the
qualification had to be re-added, and I did not add it.

**And the defect sat in the one row of four the batch left unfixtured** — three were fixtured, the fourth
was wrong. An unfixtured row in a small table is where the defect is, not a coincidence.

**Fifth consecutive batch to ship a false comment**, this one promising that task 8 would fix the very
line it sits on — task 8 is committed and did not.

**One cost measured rather than argued, and worth keeping:** the reviewer made task 7's new
`assert stop.code is not None` fire and recorded what it costs — an uncaught traceback with **two
paid-for executions on disk, no `run.yaml`, no `latest`.** Not a finding (plan correction 2 blesses the
bare assert, and it is unreachable), but *every execution paid for, the record lost* is this repo's named
habit, and now that assert's price is a measurement instead of a claim.

**Fix round 1 — Major 1 fixed and the guard now branches on the stop reason** (`57a0734`, `82fbb3a`).
Suite **2453**. **I verified the fix I had caused myself**: deleting the
`stop.reason == "apparatus_unreachable"` arm fails
`test_fixture_z_arm_3_zero_results_unreachable_case` and nothing else, so the row I got wrong is now
pinned by a named fixture rather than by the fix's presence. Reverted byte-identical.

## Batch 6 — tasks 9, 10, 11 — no policy knob, `batch` independence, the rows and filings

Commits `0e40403`, `70c2283`, `db7f187`, report `600b207`. Suite 2453 → **2456**.

**Task 10's fixture originally could not discriminate its own mutation** — it used a constant-fact probe —
and **the implementer caught that itself and rebuilt it on a changing-fact schedule** with both arms
stopping at the same execution index. Task 9's arm (b) likewise needed a probe schedule extended by one
entry to avoid an uninteresting `IndexError`. **Both are the *a mutation is a claim too* discipline
applied before a reviewer had to supply it**, which is the first time on this slice that happened twice
in one batch.

**And one filing the brief listed as owed turned out already written** — the non-`str` carve-out's
`run.yaml` surface — **verified by reading rather than trusting the brief, with no duplicate created.**
That is the exact check five wrong "no disagreements" reports on this project needed.

## Independent whole-branch review: MERGE — no Critical, no Major, four Minors

**And it found a gap in my process rather than in the code: batch 6 was never given a task review.** I
dispatched it and went straight to the whole-branch gate, breaking the pattern the other five batches
got. The gate served as its first review and **it came back clean** — no `src/` touched, both fixtures
non-degenerate, and **its three filings called the branch's strongest artifacts.** Nothing is owed, but
the coverage was verified **at** the gate instead of before it. **Recording it because the failure mode is
mine and invisible from inside any batch:** a controller running six batches can drop one review and no
implementer or reviewer is positioned to notice.

The reviewer also declined to fix the two `src/` Minors itself, on the grounds that **a reviewer editing
the branch it is gating** is a move this repo has been burned by. Correct, and worth keeping.

**A third cross-batch stale claim**, the shape this branch has now produced three times: task 5 wrote that
Fixture U pins `EXIT_PARTIAL`, **task 8 falsified it**, and nothing re-read it. Alongside a docstring
claiming *"no shipped test calls it that way"* about a test committed one batch later.

**And the one-file-short sweep recurred** — `docs/feasibility-llm-growth-studies.md` still says "its own
first observation" where both normative documents now say "first *answered*". Batch 1's Major was the same
shape in the same file, which `CLAUDE.md` names **by name** as the file a sweep must include.

**Verified sound by running:** all four Decision 4 rows on the reviewer's own fixtures with exit code and
status byte asserted **separately**; **seven no-false-stop runs, zero false stops**; credentials clean as
an int, a substring, and in a raise message, **with a positive control that leaked**; the third stop
reason genuinely read; the batch-1 pin still failing under the `stopped_at` shape; an apparatus stop
truncating **mid-step-sequence** (its `break` sits at the loop top, unlike `max_failed_fraction`'s),
driven through a `summary`-scope tail and a hypothesis naming its unrun `Estimate` — **record coherent,
not merely non-crashing**; and zero/six/three re-measured with a can-fail control.

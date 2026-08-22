# H5a — write-side integrity and the reserved-column namespace — ledger

Scoping: `docs/superpowers/H5-SCOPING.md` (H5 measured at **19 tasks against a one-row charter**, split
9/10). Design: `docs/superpowers/specs/2026-08-21-artifacts-write-side-design.md` (11 decisions, **plus
two appended controller rulings**). Plan: `docs/superpowers/plans/2026-08-21-artifacts-write-side.md`
(**13 tasks**, nine batches, **twelve corrections**).

Baseline at `219b0a0`: **2835 passed, 1 skipped, 2 xfailed.**

## The defect that gives H5 its priority, filed before the design

**`collapse_repeats` over six units each recording only `valid: True` returns `{}`** — zero units, not six
with a column dropped. On a real run that published `n_valid: {value: 0.0, ci95: [0.0, 0.0],
resample_draws: 2000}` at **exit 0 with no diagnostic.** I verified the mechanism myself by direct call.
**Filed at once rather than at slice end**, because a silently wrong published number is the one class that
cannot wait — and **the boundary was invented rather than inherited**: an existing filing reasoned that
*"whoever writes `aggregate` should inherit this reasoning"*, and `collapse_repeats` chose a **third**
option that entry describes nowhere. **It is H5b's.**

## Two rulings, and the second overturns the first

**H5a IS a behaviour change to `run`, and the design said so loudly against the scoping's own split
ground.** A design that had quietly inherited *"only H5b changes behaviour"* would have shipped four
stoppages under a sentence saying there were none. **Approved** on the distinction it drew — **H5a refuses
corrupting input; H5b changes what an existing key may contain** — with four requirements attached, of
which **Decision 6 is load-bearing**: coercing roster attributes at `resolve_units` exists to stop a
**completed** run becoming a `ContractError` inside `finalize` **after every execution is paid for.**

**Then the plan's correction 3 overturned my ground, and it was right.** I approved refusing a structural
or `bytes` cell because it *"converts silent corruption into a loud refusal"* — **measured true of `.csv`
and false of `.parquet`**, which round-trips a list and a `bytes` cell **intact**. And **`io.record`
already refuses both**, so `units.parquet` — the inference base this charter is about — **was never the
exposure**; everything Decision 5 would newly refuse is an arbitrary `io.write` artifact.

**Re-ruled: "a writer accepts what it can give back", applied per format — one rule, different answers.**
`.csv` refuses; **`.parquet` keeps its capability and gains a pin**, because a documented capability left
unpinned is this project's seventh recurring failure. Stoppage 1 shrinks to the `.csv` half and **the
count must not be carried forward.**

**I generalized from one format's measurement to both without measuring the second** — the
*answering from a proxy* move, sixth instance on this project, **made by the person enforcing the rule
against it.** The plan caught it by measuring what I asserted, which is what *the code outranks both*
exists to produce.

## The plan's sharpest correction stands independently

**Re-pointing three guards at `RESERVED_COLUMNS` would break a legally recorded `by` column** — `record`
refusing it, and the collapse and `finalize` **silently dropping** it from `units.parquet`. That is
**Decision 4 applied against Decision 3**, and exactly the hazard my first ruling named: the refusal
removes one **producer** of a `by` column, not the **possibility**. Task 5's pin on that column's survival
in both `record` branches is the enforcement.

## Batch 1 — task 13 — the guard pin, five arms

Commits `badec28` (four arms), `9fdb565` (arm E), `295c6e3` (fix round). Suite 2835 → **2844**.
**Both verdicts PASS; four Majors, three Minors, all closed. Every arm discriminates** — the reviewer
found a failing mutation for each of the five, and arm E in both directions.

**The Major that mattered was about the pin's own purpose.** Arm D — whose whole claim is *the worked
example is provably untouched* — **missed the one interval `CLAUDE.md` § The worked example names by
value**: changing kendall's `ci95: [-0.213, -0.125]` left it **3/3 green**, because the literal list used
a **Unicode minus where the YAML uses ASCII**, and six per-condition bounds were absent. **An arm that
cannot see the interval the invariant protects is worse than no arm, because it licenses the belief.**
Fixed, and **I verified it myself**: mutating that exact line now fails
`test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text[REFERENCE]` and nothing else, reverted
byte-identical.

**One Major was my instruction's fault.** I said arm E has **no authorized editor** — and its `.csv` half
is **exactly what task 9 changes**, which the implementer's own docstring had correctly noted. Both
statements could not stand. Split into a no-editor `.parquet` half and a `.csv` half naming task 9 with
its post-edit state stated in advance. **Without the split, task 9 would have met a no-editor arm and had
to decide on the spot whether it was a finding** — which is the situation the mechanism exists to prevent.

**Two familiar shapes recurred.** A docstring claimed coverage its fixture did not have (arm A said it
catches `int`→`float` and a `None` change; **neither column existed**, and the mutation left it green).
And a report asserted something about other tests **without grepping `tests/`** — the seventh instance
here; two tests *do* read a real run's `units.parquet`, though neither pins order or types, so arm A's
novelty survives **narrowly** and the report now says so.

**A blind mutation owed a replacement and got one.** The prescribed `float()` wrap crashes before any
table is built, so arm A's type row shipped **unproven**; the reviewer supplied
`int(v) if type(v) is float and v == int(v) else v`, which fails arm A on `assert 'int' == 'float'`
**alone**. **Reporting a mutation as blind is necessary and not sufficient — it owes a replacement.**

**And a fact about the documents worth carrying:** `docs/design-principles.md` contains **no worked-example
interval literal at all** — its whole footprint is three hash lines — so **§ The worked example's intervals
live in two of the three documents, not three.**

### A third variant of one failure

**A dispatch-only instruction competes with a brief and can lose.** My second ruling post-dates the plan,
so the extracted brief could not carry the `.parquet` capability pin and my dispatch was the only channel
— and it did not land until the implementer disclosed the gap. The three variants now recorded: a finding
carried **into** a brief still needs verifying; a ruling that **overrules** a brief must reach the brief;
and an instruction existing **only** in a dispatch can be outweighed by the brief in front of the
implementer.

## Batches 2 and 3 — the documents and the `E-` registry

Batch 2: `3230ce1` (the unification rule), `4dc9a50` (`measurements.parquet`'s column set, pinned by a
real-run fixture), `7686556`, `6b90b1e` (fix round). Batch 3: `a2b6b51` (three rows widened to every emit
site), `8822dc9` (`E-UNITS-ATTR-COLUMN` minted before any code raises it), `45aa4fc`, `0818d92` (fix
round). Suite 2844 → **2845**. Both batches PASS on both verdicts.

**Batch 2 shipped two false clauses propping each other up.** `reference.md` described the unit-key column
as named by `data.units.key` — **it is literally `unit`**, verified three ways including `finalize`'s
hardcoded `columns = ["unit", …]` — and a second sentence, *"that is the one way the two files' column
sets differ"*, **read as consistent only because the first was false.** Two interlocking false claims are
harder to spot than either alone, which is why the job is **tracing each clause to code, never to the
neighbouring clause.**

**Batch 3's two Majors were both in the one row it was isolated to get right**, and the reviewer
established the grading principle before ruling: § Errors core raises **enumerates every emit site and
annotates how each travels**, so **a contained site belongs in the row and an unannotated one is the
defect.** `E-STEP-KEY-COLLISION` has **seven raise sites across five faults** and the row named four —
with **another passage linking *into* that row for exactly the omitted fault**, so a reader following the
link landed somewhere that did not describe what sent them. And **two enumerated sites never raise to a
user at all**, being contained and re-reported as `W-STATS-AGGREGATE-FAILED`.

**The structural cause is worth more than either fix: there is no docs↔code `E-` registry test.** Only
prose forces a later task to land what a row promises — which is why this exact shape has now gone wrong
in **three consecutive sub-slices**. Recorded in the batch report rather than left as an observation.

### A fourth variant of one failure, stopped by a disclosure

**Batch 3's implementer found that the plan's own task text, read literally, would have `.parquet`
refusing a structural cell** — contradicting my second ruling — bound each clause to one format, and
**flagged that it could find no passage stating the binding plainly.** I appended the ruling to **the
plan** (`11dd8b3`), so **tasks 7, 9 and 11 do not inherit the superseded reading.**

**The four variants now recorded:** a finding carried **into** a brief still needs verifying; a ruling
that **overrules** a brief must reach the brief; an instruction living **only** in a dispatch can be
outweighed by the brief; and **a ruling post-dating a plan leaves every later task's text carrying the
superseded reading.** **The remedy is identical in all four: put the correction where the brief is
extracted from.**

**And batch 3 declined to report zero disagreements**, naming two concerns instead — both of which checked
out. That phrasing has been wrong **eight** times here; this is the first batch in a while to avoid it by
construction rather than by correction.

## Batch 4 — task 10 — the one scalar rule, and H5a's first `src/` change

Commits `91a338f` (the `str`-by-inheritance branch), `b55e3a3`, `27b5959` (fix round). Suite 2845 →
2854 → **2855**. **Both verdicts PASS; one Major, three Minors, all closed.**

**Decision 7 is built as specified and its reasoning is grounded rather than asserted:** `np.str_` coerces
because `str` is in `_SCALARS`, `np.bytes_` refuses because `bytes` is not and plain `bytes` raises the
same code — all three verified by running. **`str.__str__` rather than `str()`**, because
`str(SomeStrEnum.RED)` is `'Color.RED'` and would corrupt the value silently.

**The `noqa: UP042` decline is load-bearing, not stylistic**, and the reviewer confirmed it: ruff wanted
`enum.StrEnum`, whose `__str__` returns the value directly — **which would silence the exact corruption
the fixture exists to demonstrate.** A linter suggestion that defeats a test's purpose is worth declining
with a written reason.

**The Major is a retirement that never happened.** The shipped sentence said a resolver-yielded `np.str_`
attribute *"used to be refused as structural … and now coerces instead"* — and `units.py` calls
`coerce_scalars` **nowhere**, `_from_resolver` projects attributes **uncoerced**, and the value
round-trips cleanly. **That path went pass-through → coerced, never through a refusal.** Documents-lead
present tense cannot rescue it, because the claim is about the **past**.

**And the implementer had the correct measurement in its own authorities.** **Plan correction 6 — the
correction that ordered this task first — measured that same value as "which works today."** Writing *used
to be refused* contradicts the reason the task sits where it does in the order.

**A third unstated retirement surfaced** (`Estimate.n`), and **a module docstring was left behind when the
`reference.md` paragraph it paraphrases moved** — the same mechanism that produced batch 2's interlocking
false clauses.

**The blast-radius review earned its keep on something nobody asked about.** `Estimate.method` is **exempt
from the shared rule** — `method=value.method` is uncoerced — so an `np.str_` `method` survives and makes
`yaml.safe_dump` raise on a value written into `run.yaml`. Pre-existing; but **an existing filing's
RESOLVED note claims all those fields are coerced, which is false.** **A stale *closed* claim is worse
than an open gap, because a struck entry stops anyone looking.** Routed to task 12 by name.

**And correction 6's ordering rule is enforced only at the shared function** — displacing the branch fails
five tests, but **nothing pins the resolver surface**, so the constraint that orders three tasks has no
test of its own. **Task 6's Fixture R inherits an enforcement obligation, not just a fixture**, and now
carries it by name.

## Batch 5 — tasks 5, 6 — the attribute namespace and the roster

Commits `828f42b` (the split, `E-UNITS-ATTR-COLUMN` enforced, the `by`-survival pins), `cf3789c`
(roster coercion, `E-RESOLVER-YIELD` widened, the ordering pinned), `d0ff8d2`, `c21f819` (fix round).
Suite 2855 → **2875**. **Both verdicts PASS; two Majors, three Minors, all closed — and neither Major was
a behaviour defect. Both were pins that did not pin.**

**Correction 1's hazard was avoided and the avoidance was measured, not asserted.** `RESERVED_COLUMNS`
has **one** reader, and the reviewer ran each dangerous re-point separately: `finalize`'s fails **both**
survival arms, the collapse's fails **only arm (b)** — so **the two arms are not redundant**, which the
batch's own report understated. A legally recorded `by` column survives both `record` branches and reaches
`units.parquet` intact.

**Requirement 3's ordering pin is real, and it was adjudicated by construction rather than argument.** The
batch disclosed that its mutation failed one assertion earlier than written, inside the shared helper's
exit check. The reviewer **built the discriminating mutation** — refusal relocated to just after
`allocate_run_dir`, still returning `EXIT_WRONG` — and the helper's check **passed** while the pin
**failed on the directory assertion.** That is the one thing in this batch that could have produced *every
execution paid for, the record lost*.

**A carried finding was reported closed while undischarged — the third instance here.** The batch-4 ledger
routed correction 6's enforcement gap to **Fixture R by name**, and deleting the branch that ordering rule
protects gave six failures **none of them at the resolver surface** — because **every new resolver fixture
used `np.float64`, which never reaches that branch.**

**And a new variant of an old shape: an assertion satisfied by the message's own enumeration of the set
under test.** Fixture A asserted the refusal message *"names the offending attribute"*, but the message
interpolates `', '.join(RESERVED_COLUMNS)` — so the check matched on the enumeration. **Hard-coding a
decoy name at all three emit sites left all fourteen arms green**, meaning the decoy apparatus bought
nothing.

**Also: all three Minors were undisclosed drops** — arm O1 dropped the brief's `E-RESOLVER-YIELD`
assertion entirely, a `W-STATS-STRATUM-SHADOWED` clause was dropped, and one report grep **described a
docstring citation that does not exist.** Dropping a brief clause is legitimate; **dropping it silently is
not.**

**One unrequested check worth keeping:** with the coercion removed, a real run wrote
`{'unit': 'p1', 'tags': [1, 2], …}` into `units.parquet` — so § Where units come from's **past-tense**
claim is true. Given batch 4 shipped a past-tense claim that was false, that check earned itself.

## Batch 6 — tasks 7, 8 — the recorded side, no encoder in the picture

Commits `44399fd` (the plain branch refuses `measurement`), `3b58442` (`finalize`'s `columns` deduped),
`66d4581`, review `61f257f`. Suite 2875 → **2879**. **Both verdicts PASS with NO findings** — the first
batch in this slice to close without one, and a control review is where that is least surprising: two
guards on the recorded side with no encoder between them.

**Decision 9's asymmetry is closed and closed end-to-end.** A plain `io.record` carrying a `measurement`
column now earns `E-STEP-KEY-COLLISION` at `EXIT_FAILED` with no `units.parquet` written; the
`measurement=` branch is unchanged; and a **plural** `measurements` column still writes — the third arm is
the one that matters, because the guard is a substring away from swallowing it, and the reviewer
reproduced that mutation independently. `reference.md`'s existing `E-STEP-KEY-COLLISION` row already
covers the new site, so **no row moved** — the first time this slice has answered the one-row-per-code
question with *nothing to do* rather than with an edit.

**Correction 5 held, and the report neither overclaimed nor understated it.** The dedupe fixes the
**list**, not the **value**: `finalize`'s attribute loop still overwrites `merged["unit"]`, so a
**directly built** `Unit` carrying an attribute named `unit` hijacks the key column after the dedupe
exactly as before. The reviewer built that case **before reading the fixture** and got
`{'unit': 'HIJACK', …}`. It stays open and is routed to task 12 by name.

**One thing worth carrying, and it is about the pin rather than the code.** Deduped and non-deduped column
lists produce **byte-identical** `units.parquet` — 951 bytes either way — so the dedupe is unobservable in
the artifact, and its guarantee is a property of **the list handed to the writer**, not of the file. That
is why the pin is a spy on the column list rather than an assertion on output, and it is the honest form
of a **dimension no assertion can see**: the assertion was moved to where the behaviour is, instead of
being written where the test happened to look.

## Batch 7 — task 9 alone — the behaviour change

Commit `eeebd89`, review `8bc0395`, report correction `e6e94ec`. Suite 2879 → **2884**. **PASS on one
Major, which was a reporting defect rather than a code defect.**

**The second controller ruling survived contact with the code, and the deviation it required was
disclosed rather than silent.** The brief's own steps 1, 5 and 7 carried the **superseded** pre-ruling
reading — `.parquet` refusing structural and `bytes` cells alongside `.csv` — because the ruling
post-dates the plan. The task built to the ruling and **said so**; the reviewer re-measured both formats
rather than taking the controller's paragraph on trust, and *"a writer accepts what it can give back",
applied per format* is what shipped: `.csv` refuses a structural or `bytes` cell with the artifact named,
`.parquet` round-trips both byte-faithfully and keeps its capability. **This is the one place in the slice
where the plan's appended correction did the job it was appended for** — the whole point of writing an
overruling into the plan is that the ledger reaches the controller and the brief reaches the implementer.

**The spurious refusal is retired end-to-end**: an `np.float64` recorded beside a plain `float` no longer
fails a column's type check, verified through the installed console script and not only by direct call.
A non-mapping row earns `E-ARTIFACT-UNWRITABLE` **naming the row rather than the artifact**, which is what
the document says, and a decoy on `io.write`'s new artifact-naming prefix was tried: no other part of that
message contains the name, so the assertion is not one neighbouring output could satisfy.

**The Major is worth carrying for its shape, not its severity.** Mutation 5 — widening `io.write`'s
`except` to the whole body — was reported as **1 failure** and is really **4**: widening the `try` also
converts the `else`-branch and non-mapping `ArtifactError`s into `ContractError`, breaking three
`pytest.raises(ArtifactError)` pins. The code is unaffected; the wrapper as built is dispatch-only. But
an **under-reported mutation count is the same fault as reading a mutation's silence as confirmation** —
a reader of *"1 failed"* concludes one test guards that boundary and feels free to move the other three.
The correction is **appended to the report** rather than edited into it, for exactly that reason.

**Both `§ Errors` clauses this task inherited were already true**, re-derived by the reviewer from every
emit site rather than accepted as a claim. That is the second batch running where the one-row-per-code
question was answered with *nothing to do* — and the first where the answer had to be **checked**, because
the plan said those clauses described code that did not exist when they were written.

## Batch 8 — task 11 alone — the cross-format matrix and the whole-branch re-run

Commits `16ba11a` (Fixture W per format, Fixture E), `81dabdf` (report, plus a `.gitignore` restore),
review `0d5c8b5`, report correction below it. Suite 2884 → **2891**. **PASS on one Major, again a
miscount rather than a code defect.**

**This task shipped no production code, so every candidate finding in it was a pin that does not pin —
and the review found none.** Correction 2 held under independent measurement: `.csv`'s arms compare
against **`str()` of the coerced value**, `.parquet`'s against the coerced value itself, each round-trip
measured rather than read. And the batch turned up **a second, independent cause of the two formats'
disagreement** that correction 2 does not cover: **`.csv` does no int-beside-float promotion at all**, so
the `str()` rule and the promotion rule are two separate reasons the same row decodes differently.

**A mutation's prediction can go stale under a later task in its own slice.** Task 6's mutation (i) was
written when deleting roster coercion raised inside `finalize`; with **task 9's `.parquet` capability
landed**, the same mutant now **completes at exit 0 and silently publishes a structural attribute into
`units.parquet`.** The mutation still fails, so the pin still holds — but *where* it surfaces moved, and
the brief's prediction of the shape was no longer true. Worth carrying: **a whole-branch re-run is not a
formality**, because the branch under it changed after each mutation was written.

**The design's own Fixture E wording is false of `.csv`.** *"A `None` column round-trips as `None` …
both formats"* — measured, `csv.DictWriter` writes `None` as the **empty string**, neither `None` nor
`"None"`. It is **filed for task 12** rather than edited into the spec, because a design records what was
decided when it was written and is corrected by appending.

**And the miscount is now a pattern, not an incident.** Mutation 13(ii) was recorded as *375 failed, 48
errors* against a measured **376 failed, 48 errors** — the second miscount in two batches, in a column
whose own framing is *counts read, not estimated*. Neither changed a conclusion. Both are recorded
because a number introduced as **read** is a claim like any other, and the reader who trusts one is the
reader who later moves a pin it was supposed to guard.

## Batch 9 — task 12 alone, and reviewed — the filings and both consistency passes

Commit `c52ea38`, review `7f1bc91` (**FAIL**), fix round `ce6c1c1`. Suite unmoved at **2891 passed, 1
skipped, 2 xfailed** — this batch touches `spec-defects.md`, the design's appended correction, and its own
report, and nothing else.

**Reviewing this batch was the right call and the review earned itself on the first finding.** Four
filings closed and struck (each re-derived against the code rather than trusted), two rows re-owned to
H5b **by name with citations**, three new gaps filed **unassigned with a reason**, both passes run with
every sweep proven able to fail — and one Critical: **batch 8's `.csv`-null finding was never filed at
all.**

**The chain it fell out of is worth naming precisely, because every link held except the last.** The gap
was **measured** in batch 8 (a `None` cell writes as the empty string, so the design's Fixture E wording
is true of `.parquet` and false of `.csv`). It was **recorded in this ledger** as *"filed for task 12"*.
It was **named in the controller's dispatch** as carry-forward 5 of five. And the task **neither filed it
nor reported it open** — its report does not mention it. So: *a ledger line saying "filed" is not a
filing*, **and neither is a dispatch line**, which is the sharper form. The rule this repo already had —
*carrying a finding into a brief is necessary and not sufficient* — has a new failure mode: the finding
never reached the **brief**, only the dispatch prose around it, and a report that lists five carry-forwards
and discharges four reads as complete.

Filed now, with the correction **appended** to the design rather than edited into it, and the live half in
`spec-defects.md`: whether `.csv` should **refuse** a `None` cell the way it now refuses a `bytes` or a
structural one, since `None → ''` is exactly the silent lossy conversion that rule exists to prevent and
is **the one such conversion H5a left in place.** It sits beside two entries of identical shape — a
format-specific lossy or uncoded conversion the per-format ruling made visible without settling.

**The Major was the third miscount in three batches.** The § Errors audit reported *"six raise sites"* for
`E-STEP-KEY-COLLISION`; the string appears in three files and there are **eight** raises — six in
`artifacts.py`, two in `stats.py`, with `cli.py`'s three mentions being comments. The audit's conclusion
survives (the row is generic enough to cover all eight, and none is narrower than its code), but **a
number offered as verification evidence has to be the number the command printed.** Three batches, three
miscounts, none of them changing a conclusion — which is exactly why they are recorded: the reader who
trusts one is the reader who later moves a pin it was supposed to guard.

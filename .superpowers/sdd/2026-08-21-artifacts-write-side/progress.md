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

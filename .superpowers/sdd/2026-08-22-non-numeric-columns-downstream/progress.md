# H5b — non-numeric columns downstream to `aggregate` — the ledger

Branch `h5b-non-numeric-downstream`, off `main` at `5ee3a0c` + the docs commits above it. 16 tasks in
five batches, every batch reviewed. The slice's central fact, measured before it started: **it is not
additive.** Admitting a unit widens the inference base, so values move in columns holding no non-numeric
data at all — and the numbers it moves are **wrong on the record's own terms today**, one mapping
publishing `completed: 4` while `attrition` over the same executions says `completed: 6`.

## Batch 1 — tasks 1, 2, 3 — the pin captured before anything moves, and the document decisions

Commits `23b79a9` (the pin), `bc4e56e` (§ Templates), `2e9f5e4` (§ The per-unit tables, § Statistical
reporting, `W-STATS-REPEATS-DISAGREE`, one filing), `31a5f31`, review `20289d2` (**task 3 FAIL, one
Critical**), fix round `f0c4f2f`. Suite 2891 → **2895**.

**Arm E reproduces, and the reviewer re-measured it rather than reading the claim.** Plan correction 9
said the two-condition Holm half reproduces at `ee8085e` and moves **two keys the design does not name**;
independently re-measured with a fresh script, every literal matched — `n_paired` 4 → 6, the
`correction_level` swap, both `ci95_corrected` shifts, both unnamed extra keys, and every *must not move*
literal. **A non-reproduction would have been a finding rather than a fixture to repair**, which is why
it was re-measured; it is the one claim in this slice that everything downstream rests on.

**The Critical, and it is a controller defect before it is an implementer one.** Task 3 shipped a
§ Statistical reporting sentence codifying **all-or-nothing**: a column earns a block *"only when every
value carried for it is a real number"*, so one `None` costs the column its block for every unit — the
exact reading controller ruling 1 rejects, and **the silent-drop shape this slice exists to end**, traced
to reachable live code rather than argued.

**The root cause is structural.** The ruling was appended to the plan under a preamble asserting *"a brief
extracted from this plan carries these paragraphs"* — **and that was false**: `task-brief` extracts one
`## Task N` section and nothing else. So the ruling reached the controller and the reviewers and **never
the implementer**, which is this repo's own named failure mode, hit inside the slice whose plan documents
it. Fixed the only way that holds: **every one of the sixteen task sections now opens with a pointer
saying the rulings post-date it and win where they disagree**, and ruling 1 gained an amendment naming the
three mixtures — which is the second finding.

**The all-or-nothing sentence was right about one case and wrong about another**, which is why it read as
plausible and passed its own task:

- **non-numeric for every unit** — no metric block, and correct: there is no mean of strings;
- **a number for some units, `None` for others** — a block over the contributors, with **the contributing
  count reported rather than `completed`**, because an interval over five values published beside a
  `completed` of two hundred is a precision claim no later reader can catch;
- **`str` beside a number** — **cannot occur.** `_check_column_types` refuses it at `finalize`, measured.
  A read rule for it describes an unreachable state, and stating one invites a later reader to build
  against it.

**Two more things worth carrying.** Arms C and D were found to **already exist verbatim**, which is the
claim a reviewer should distrust most — an existing test may pin something *adjacent* — so the reviewer
mutated the production code each arm is said to guard and confirmed both fail; **arm D has no authorized
editor, so its passing is the proof.** And mutation (iv), reversing Holm's rank order, was disclosed as
moving only 2 of 3 correction-level assertions — **the argument is sound** (arm E's `mean_score` sits at
the median rank of a three-member family, and reversing an order cannot move a median) and the reviewer
verified it by running, then found the same mutation **also fails arm A**, an undisclosed side effect
rather than a weakness.

## Batch 2 — tasks 4, 5, 6 — the behaviour change

Commits `06fdd3d` (the collapse), `8ffab8a` (the disagreement disclosed from the rows), `252774b`
(`summarize_step`'s clause and Ruling 1's gate), review `4edd98d` (**task 4 PASS, tasks 5 and 6 FAIL —
seven Majors, three Minors**), fix round `ad67a75` / `a9b6340` / `bb74d04` / `ab1d18a`. Suite 2895 →
**2920**, and no existing test was edited or removed in the fix round.

**Ruling 1 behaves as ruled, verified end-to-end through the installed console script on a scaffolded
project outside the repo, for all three mixtures**: a column non-numeric for every unit publishes no block
and still reaches `aggregate`'s table; a column three of six units carry a number for publishes
`n: {resolved: 6, completed: 3, …}` — **the contributing count, which is the whole point**; and `str`
beside a number is refused at `finalize` at exit 4, so the read rule for it stays undocumented because the
state is unreachable.

**Task 6 widened its own scope, correctly and with disclosure, and that is the good news in this batch.**
Its brief said *no code change*; it shipped one, because task 4 had introduced a regression that Ruling 1
forbids — the reviewer built the three-way comparison (pre-batch `n=3` → task 4+5 `{}` → HEAD `n=3`) rather
than accepting the account. **A task that quietly widens its scope is a finding even when the code is
right**; this one did not do it quietly.

**The most consequential thing in the batch is a crash it deliberately left live.** Ruling 1's gate makes
task 7's unguarded subtraction reachable: measured end-to-end, a contrast over a ragged `None` column
gives a raw `TypeError`, **run directory complete, ten executions paid for, no `run.yaml`.** It ships as a
`xfail(strict=True)` asserting the **correct** post-fix behaviour and naming task 7 as its remover — so it
fails for the right reason now and flips to a strict `XPASS` failure the moment the gate moves. The
reviewer verified both halves of that device rather than the intent behind it.

**Ruling 5 is where a binding ruling was amended rather than enforced, and the amendment came from the
code.** Ruling 1 had called the coverage warning *not optional*, arguing an interval over five values
beside a `completed` of two hundred is a precision claim no reader can catch — **but the shipped count
made that claim impossible**, since `run.yaml` now publishes the contributing count. So the warning's job
shrank from *preventing a lie* to *telling the person who never opens `run.yaml`*, and an unconditional
warning would fire on runs with nothing wrong. It became **`W-STATS-COLUMN-THIN`**, per
(condition, step, column), against **`limits.min_reported_n`** — the floor three shipped rows already use
at `run` time against a realized denominator. **A second threshold for the same hazard would have been a
second source of truth.**

**Two properties of that mint worth keeping.** Its footprint was measured **before** any pin was written:
the suite was **unchanged** with the emit site live, because the scaffold's floor is 10 and its roster is
10, so a full column sits *at* the floor and `<` does not fire. **An emit site no default run reaches is
exactly where a dead check hides**, which is why it got three tests rather than a control. And unlike both
its siblings it has **no declaration gate** — that is Ruling 5 as written, recorded as a property rather
than absorbed silently.

**A false premise had three homes, and the sweep found the one nobody named.** The warning's message and
its § Warnings row both said a mixed numeric/string column *"is not a number"* and that *"those units
carry no value for it"* while the record published values for them. The dispatch named a third site —
`repeats_disagreeing`'s docstring — which turned out to be the one that was **already right**, and
sweeping for the **claim** rather than the file turned up a real third in § Statistical reporting. **Both
were deleted rather than rewritten**, and so was `_across_repeats`'s ground that task 6's own gate change
had falsified three paragraphs above its own contradiction.

**And two live behaviours had never been pinned at all** — the empty-record admission (`n_rows` 4.0 → 6.0)
and `_repeats_disagree`'s `(is-numeric, value)` tuple, both removable with the suite green. That is the
*pin weakened quietly* shape arriving in its other form: **never pinned in the first place.** The
`report_by` stratum path was a **ninth** moving-key class the design's enumeration missed, carrying a
**third** distinct `resample_draws` literal; it has an arm now. **Four distinct seed-dependent
`resample_draws` values are now labelled across the pin's arms** — which is the reason correction 7 said
that number is not a constant.

## Batch 3 — tasks 7, 8, 9, 10, 11 — the guards and the namespace

Commits `848835e` (the contrast guard), `1e8cb51` (§ Statistical reporting), `b276704` (the `by`
arbitration), `e613c11` (the derived-key collision), `1268c96` (the empty-level gate), `09954ea`,
`3be2808` (an in-batch fix round), review `548cedd` (**tasks 7 and 9 FAIL — three Majors, three Minors, no
Critical**), fix round `1f08b3e`. Suite 2920 → **2926**, with the xfail count moving **3 → 2**.

**Every finding in this batch was a CLAIM defect. Nothing in `src/` moved** — the reviewer said so and the
fix round verified it before touching anything, which is the right order.

**Batch 2's disclosure device worked exactly as designed, and its conversion is the thing to carry.** The
`xfail(strict=True)` that named task 7 as its remover was converted by removing the decorator, moving
`reason=` into the docstring, keeping **both original assertions byte-identical**, adding **one**
(`n_paired == 3`), and renaming `…_crashes` → `…_no_longer_crashes`. **It asserts strictly more than the
xfail did**, verified by diffing before and after rather than by reading the account — and the underlying
fix was proven by behaviour: guard removed gives a raw `TypeError`, a complete run directory, ten
executions in the ledger and **no `run.yaml`**; guard restored writes `run.yaml` with `n_paired: 3`. **A
strict xfail asserting the CORRECT post-fix behaviour is a disclosure that cannot be forgotten**, because
the suite goes red the moment the gap closes.

**The slice's signature defect shipped a third time, and this is the entry that names it.** *All-or-nothing
wording over a rule that has three cases*: batch 1's Critical, batch 2's M1, and now § Warnings'
`W-STATS-STRATUM-SHADOWED` row framing itself as exhaustive over *every value a number* / *no unit
recorded a number* — with the **reachable middle case in neither.** Measured: `by` numeric for 20 of 40
units publishes a full block (`value: 19.0`, `n.completed: 20`, `ci95: [13.46, 24.54]`, `t_over_units`,
`repeat_spread`) **and** the warning. **Three times, three different files, each found by someone
sweeping for the claim rather than the file.** The lesson is not *check this sentence* — it is that **a
rule with three cases invites a two-case sentence at every site that mentions it**, because two cases
sound complete. Ruling 1's amendment table is now the single authority every site links to instead of
restating.

**A conclusion can survive its ground being wrong, and then it needs a new ground rather than a note.**
The guard's *corrected* comment asserted the column *"already earns"* a condition-side
`W-STATS-COLUMN-THIN` — false under `limits.min_reported_n: 1`, which is exactly the case **Ruling 5's own
cost-if-wrong paragraph names.** Mint-no-code stands, on the `n_paired` half; the comment now names
`n_paired` as the unconditional disclosure and the warning as conditional on the floor. **That comment has
now been wrong twice**, which is why the round was told to write a true ground or delete the sentence
rather than add a third layer.

**`W-STATS-COLUMN-THIN`'s blind spot is real and documented rather than absorbed.** Ruling 5 tied it to
`limits.min_reported_n`; a project declaring a floor of 1 gets no warning for a column one unit carries.
The ruling predicted that and the batch measured it — **the honest `n` is then the only signal, which is
the state that shipped before the warning existed**, so the downside is bounded by the status quo.

**And the miscounts reached five.** *"Grep reported, not a count asserted from memory"* was itself false —
five lines across three files where the report claimed one; `85 insertions` was `93`; an enumeration named
one file twice and omitted another; and a *"two lines"* grep **could not have found** the site it was
offered as evidence about, whose docstring was line-wrapped, so the right sentence was *found by reading*.
Every one corrected by **appending**. None changed a conclusion — and that is the pattern, not the excuse:
**the numbers that get miscounted are exactly the ones nothing downstream depends on**, which is why
nobody notices until a reader relies on one.

## Batch 4 — tasks 12, 13, 14 — the pins and the readers

Commits `29d0a0d` (`E-STEP-COLUMN-UNKNOWN` in both directions), `336ed45` (the silent case's
discriminating test), `a855f91` (`report` and `study` as readers), `0cf71b8`, review `3856b76`. Suite
2926 → **2931**. **All three PASS, no findings** — and this batch changed no `src/`, so every candidate
finding in it was a pin that does not pin.

**Both directions of the refusal are really pinned, verified by running one mutation per direction rather
than by reading the claim.** Breaking the firing side fails one pair of tests and leaves the honouring
side green; breaking the honouring side fails a different pair and leaves the firing side green. That
separation is the whole content of *pinned in both directions* — this repo's most repeated dead check is
*"`validate` refused bad `block_size` values while nothing checked the draw used a good one."*

**A reconstructed mutation is a claim about history as well as about code, and this one was adjudicated
rather than accepted.** The brief prescribed a mutation with **no literal line in the post-refactor
code**; the task reconstructed the pre-H5b behaviour from two corrections' documented numbers, and the
reviewer checked the reconstruction against **task 4's own commit**, which had applied the identical shape.
**Sound, not invented** — but the general point is that a brief written before a refactor can prescribe a
mutation that no longer exists, and the honest response is to reconstruct **and say so**, not to report
the mutation as run.

**A substituted fact was disclosed and both halves were checked.** Task 13's brief asked for
`resample_draws` as the third discriminating fact; measured, it is `2000` either way, because a plain
boolean count can never produce a degenerate bootstrap draw. The bootstrap interval (`[2.0, 8.0]` versus
`[0.0, 4.0]`) went in instead. **A substitution disclosed is legitimate; one that is also blind is a
Major** — so the reviewer verified the brief's fact is genuinely blind *and* the substitute genuinely
discriminates. Both held.

**And the three-case rule survived its fourth opportunity.** `report` and `study` were run end-to-end
through the installed console script over a project carrying **all three** of Ruling 1's mixtures, and
both rendered the correct two rows and no third. After a Critical and two Majors from stating a two-case
version of that rule, the batch that had the most room to restate it did not.

## Batch 5 — tasks 15, 16 — the records, reviewed rather than skimmed

Commits `56aad22` (strikes, filings, `CLAUDE.md`, both passes), `da31016` (§ Executability, row 4
re-derived), `c8a1380`/`dea7c70`, fix round `bc50409`, review `6bbe922` (**both PASS**, two Minors, one
of them **retracted after investigation**). Suite unmoved at **2931**; no `src/` or `tests/` file moved.

**Row 4's re-derivation holds, `1 → 0 → 1`, and the check that matters was mechanical**: the reviewer
diffed the three § Executability entries programmatically and confirmed **rows 1–3 and the header are
byte-identical** while row 4 alone moved. The table stays four rows. That is the shape those two dated
corrections earlier in the section demanded, and it is now three entries old.

**The H9 filing was reproduced from scratch rather than trusted**: a standalone repo, `uv.lock DIFFERS`
printing two digests, and the moved package's name appearing **nowhere**, at exit 0. *A filed gap that
does not reproduce is worse than an unfiled one*, and a reviewer who rebuilds the repro is the only reader
who can say it does.

**H5a's *"filed, owner H5b"* line resolved without a second entry, and the reviewer nearly filed the
opposite.** The suspicion was the right one — *a design line saying "Filed" pointing at an entry that
answers a **different** question is the same failure in a new costume* — and it was checked by direct
probe rather than by reading: the two entries answer **disjoint, compatible** questions. **The finding was
raised and then retracted on measurement**, which is what a retraction should look like.

**The sharpest thing in this batch is about sweeps, and it generalizes backwards.** The brief's `grep -rF`
shape **cannot match a line-wrapped phrase**, and that hid two real hits until the task re-ran
newline-insensitively — which is the mechanism that let this slice's signature claim live in a third home
nobody had named. And the reviewer's own throwaway checker **had to be debugged three times** — inverted
fence-skip logic, then a slugger bug — **before it could fail on an injected fault.** *Prove every sweep
can fail* is not ceremony: two of the three sweeps written in this batch were incapable of failing when
first run, by their authors, while checking for exactly that.

**One thing is deliberately left to the whole-branch gate.** Arm G's docstring calls `1927` both the
*fourth* and the *third* distinct `resample_draws` literal. A records task **must not edit a pin arm's
docstring** — that is the rule that keeps a pin from being adjusted by whoever last read it — so it was
named, not fixed. Correct restraint; it is the gate's to close.

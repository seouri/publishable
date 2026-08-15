# Task 20 — controller additions

These are requirements, with the same force as the brief file they accompany.

**This task's output is evidence, not assurance.** Every step says "prove it can fail" or implies it.
A pass you cannot show failing is not a pass — four verification probes in this project have reported
nothing for *every* input (a harness bailing at `E-TEMPLATE-UNKNOWN`, a CSV written to the wrong
directory, a config compared against itself, a grep whose `--include` matched nothing). **Put each
command and its output in your report**, including the deliberately-failing control.

## Step 6 is the exit criterion, and it now has a known adversary

*Two identical measurements reported as two arms* must be **structurally impossible**. Task 12 built the
subset view and the *Arms need allocation* refusal, and its review found a route that defeated the bar:
`sweep.selector_paths` accepted a `levels` list of any element type while `cli._resolved_group_axes`
required strings, so `levels: [1, 2]` expanded into two conditions and narrowed neither. That was fixed
in task 12's fix round.

**Re-run that adversary yourself, end to end, and record the result.** Do not take the fix on trust and
do not look only at the shape the review named — ask what *else* can make the two derivations disagree,
and try at least: an empty `levels` list, a `levels` list with one element, a duplicate level, a `by`
that is not a string, and a `groups` entry that is not a mapping. For each, say whether the config is
refused, or expands and narrows correctly, or expands and hands back the whole roster. **The third
answer is a Critical finding, not a note.**

## Row-position phrases: audit the whole table, not just this slice's rows

Tasks 9, 10 and 11 wrote a phrase locating a table row by position five times and were wrong twice —
once in a row no diff touched, falsified by an insertion that moved it. This slice inserted at least six
rows into § Errors `validate` reports and removed three declarations from the five-field loop.

**Grep every tracked `*.md` for `rows above`, `row above`, `rows below`, `row below`, `further up`,
`immediately above`, `immediately below`, `the two above`, `preceding row`, `next row`** — then check
each surviving instance against the table as it now stands. The controller audited five such phrases
mid-slice and found them correct then; insertions since may have moved their antecedents.

## Step 1's `--include='*.py'`, and why it is called out

Stale bytecode has produced a false positive on this exact check in this repo. Grep the **source**, not
the tree: `__pycache__` holds compiled copies of code that no longer exists. Delete `__pycache__` before
the greps, and state that you did.

Grep for the three retirements in **both directions**: absent from live code, and absent from every
tracked `*.md`. Tracked means `CLAUDE.md` and any `docs/feasibility-*.md` too — `docs/superpowers/` is
gitignored and is the working record; do not clean it.

## Step 5's real temporary commit

A working-tree edit is invisible to a two-dot diff, which is how this check silently passes. Make a real
commit, diff against the branch point, confirm the check reports, then reset. **Show the failing output**
— a `cohort-pilot` number moved on purpose — before showing the clean one.

The numbers: 240/228/12; r = 0.581 / 0.607 / 0.412; delta 0.026 ci95 [−0.007, 0.059]; kendall −0.169
[−0.213, −0.125]; `repeat_spread` std 0.014; hashes `8e21`/`1a2b`/`3d8a`/`6b1f`; README demo `2f5c8d0`.

## Step 7's enum comments

`assign.method` must list what the code accepts. Note the subtlety this slice created: the code accepts
`random`, `by_attribute` and `blocked` **into the enum** and then refuses two of them by value
(`E-DATA-ASSIGN-DRAWN`). The inline comment lists the enum; the refusal is prose. Check both say the same
thing, and check § The one config file's comment against `ASSIGN_METHODS` in the source rather than
against another comment.

Same for the `NOT BUILT` count (step 2): grep the spelled word and the digit both. This repo has already
shipped "three phrases counting a table that grew".

## The known sort violation

`E-SWEEP-ABLATE-BASELINE-GROUP` sits after `E-SWEEP-ABLATE-CROSSED` in § Errors `validate` reports. It is
pre-existing, every task this slice was told to leave it, and **it is yours** — fix it here, and check
whether the slice's own insertions introduced any others.

## Step 8

Commit only if something changed. If the passes find nothing, say so with the evidence — a task 20 that
reports "all clean" without showing a control that failed is the shape this step exists to prevent.

## Numbers the controller verified mid-slice — check them, do not trust them

Measured at task 12, before the retirements:

- **`NOT BUILT` markers in `docs/reference.md`: seven**, and exactly the seven the plan names —
  `data.units.from`'s `{resolver:}` form, `allocation`, `holdout`, `assign`, `sweep.groups`,
  `statistics.resample`, `statistics.null_test`. Task 17 removes `allocation`, `assign` and
  `sweep.groups`, leaving **four**: the resolver form, `holdout`, `resample`, `null_test`.
- **No `NOT BUILT` marker appears in any other tracked markdown file** — not `CLAUDE.md`, not `README.md`,
  not a feasibility analysis. If your grep finds one, that is a finding.
- **The count is not stated as a word or a digit anywhere in prose.** The nearest passage says only that
  "each currently-refused block is named and marked `NOT BUILT` in the config it shows" — a statement
  that stays true at four. So step 2 is a check on the *markers*, not on a sentence. If you find a
  sentence stating the count, it was added during this slice and it is yours to update.
- **The § Validation checks table is 109 non-separator rows including its header**, i.e. 108 checks,
  counted mechanically from the `## Validation` heading to the next `###`, skipping fenced blocks.
  **The plan and three scoping documents say "95 rows"** and are stale — this slice added to it. Cite
  rows by **title**, as step 4 requires, and if you state a count anywhere, state the one you measured
  and show the command.

## The positional-phrase audit, run by the controller at task 12 — re-run it, and start here

Across every tracked `*.md`, five surviving instances, each checked against the table as it then stood:

| Where | The phrase | Verdict then |
|---|---|---|
| § Validation, *Assignment names a method* | "the 'Allocation needs arms' and 'Every axis is assigned' **rows above**" | correct — both named rows do sit above it, and it names them rather than counting positions |
| § Validation, *Assignment method isn't drawn* | "the enum 'Assignment names a method' **above** checks against" | correct |
| § Errors `validate` reports intro | "the one **row above** that names a gap in this project" (`W-ENV-UNLOCKED`) | correct, prose about an adjacent table |
| § Errors core raises | "That **last row** … those **six** are core checking its own work" | **a count, and task 12 moved it** — it read "five" before `E-RUN-ARM-UNRESOLVED` was added, and the implementer updated it in the same commit. Verify the six is still six after tasks 13–17 |
| § Validation intro | "**Six** things deliberately absent from that table" | a count of a list in the same paragraph, not of table rows — check the list, not the table |

Two of the five are **counts**, which is the harder failure: a count goes stale silently when a table
grows, and this repo has already shipped a commit whose message is "three phrases counting a table that
grew". Tasks 13 through 19 land after this audit, so **re-run it** rather than reading the table above as
a result. `docs/feasibility-llm-growth-studies.md` has one match that is not a positional phrase at all
(a table cell containing the words); it is also exempt from the cross-document pass.


## Correction from the pre-flight audit — this overrides what is written above

**My "the count is not stated in prose" claim was wrong, in the direction that hides staleness.**
§ The one config file states it spelled out **and enumerates all seven**: *"Seven declarations above are
not yet built, and each is marked `NOT BUILT` where it appears: `sweep.groups`; `data.units.assign` and
`.holdout`, the `{resolver: <name>}` form…"*. It also predates this branch, so my "if you find a
sentence stating the count, it was added during this slice" was wrong twice over. **Step 2 checks the
sentence, the spelled number and the enumeration, not only the markers** — task 17 owns the edit; you
verify it landed.

That is the "three phrases counting a table that grew" failure arriving in my own audit instructions,
which is the reason step 1 says to prove every check can fail rather than to trust one.

**Step 6 has an owner now.** Task 18 writes the § Mistakes core prevents row this step verifies against
— it did not exist in any tracked document when this addendum was written. Verify the row is there and
that what it claims is what the slice built; a step 6 signed off against a row nobody wrote is the
emptiest possible pass. Task 16b is part of the answer: a contrast across arms is refused rather than
reported paired over zero units.

## Added after task 17 — what its review turned up that bears on your passes

**Step 1's "prove the grep can fail" is not ceremony, and there is now a live example.** Task 17's
reviewer ran the tracked-markdown sweep for the three retired codes, piped it through
`grep -v superpowers` to drop the working-record noise, and got **zero hits** — because the one true
remaining hit in `reference.md` is a line containing the string `docs/superpowers/spec-defects.md`. It
caught itself only by running the same command against a code known to be present. Do the same, and
**do not filter the output of a sweep whose job is to find a string** — filter the file list instead.

**Step 3's registry integrity now has more to check than when this addendum was written.** Codes minted
during the slice, in addition to the ones the plan named: `E-DATA-ALLOCATION-CONTRAST` (task 16b),
`E-DATA-ALLOCATION-WITHIN-ARMS` (task 12), `E-DATA-ALLOCATION-METHOD` (task 17), `E-RUN-ARM-UNRESOLVED`
(task 12, a run-time raise). Task 17 also extended `E-SWEEP-PATH-DUPLICATE` to a third fault — two
`sweep.groups` entries sharing a `by` name. Check each in **both** directions: every code the source
emits has a row, and every row's code is emitted somewhere.

**Step 6's adversary list grew.** Beyond the `levels: [1, 2]` case task 12 fixed, task 17's review found
that **`by: ""`** is accepted by `selector_paths` (`isinstance(by, str)`) and skipped by
`_resolved_group_axes` (which requires non-empty), producing conditions labelled `=a`/`=b` with
`selectors == {""}` that `validate` does not refuse. Task 17 was asked to cite it in a comment, not to
refuse it. **Decide whether it should be refused**, and say so with the probe output either way — it is
the last known route by which the two derivations disagree.

Also verify task 17's own catch stayed fixed: `groups: [{by: arm, levels: [a,b]}, {by: arm, levels:
[c,d]}]` must be refused. Before the fix it produced four conditions labelled
`['arm=c','arm=d','arm=c','arm=d']` — the first axis's levels erased and two label pairs byte-identical,
so two condition directories would collide.

## Step 5 has a hole — it checks one direction and this branch's risk is the other

As written, step 5 verifies the worked example's numbers **did not move**. That is necessary and it is
not sufficient: this branch's characteristic risk is a number that **should have moved and did not**.

§ The one config file's fenced example calls itself the config schema for template `generic` *"at full
expansion: every parameter `publishable init` materializes, plus the optional blocks it leaves empty or
undeclared."* **Task 17 edited both sides of that claim** — it changed what `init` writes (the
`allocation` comment) and it changed the `NOT BUILT` markers in the fenced example.

So add to step 5: **diff the fenced config example against what `materialize.py` actually writes, field
by field and comment by comment.** That is CLAUDE.md's *Config completeness* drift class, and it is the
one class no task in this slice was told to check while two tasks edited into it.

## Step 3's inventory — the controller's baseline, measured from source

`grep -rhno '"E-[A-Z0-9-]*"' src/publishable/*.py | sed ... | sort -u` yields **134 distinct `E-` codes
emitted by the source**, taken at task 18. Both codes named elsewhere in this addendum are present
(`E-SWEEP-EXPANDS-EMPTY`, `E-DATA-ALLOCATION-METHOD`).

Use that as the left-hand side of the both-directions check, and note the two traps in building it:

- **A literal-only grep misses a code assembled or passed as a variable.** Check for any `code=` or
  `c.error(` whose first argument is not a string literal before trusting 134 as complete — if the
  count you measure differs from 134, that is a finding either way and worth saying which direction.
- **The right-hand side is two tables, not one.** § Errors `validate` reports and § Errors core raises
  are separate registries, and a run-time `ContractError` belongs to the second. A code in the first
  when it should be in the second passes a naive membership check.

Codes minted during this slice, for the both-directions check specifically: `E-DATA-ASSIGN-DRAWN`,
`E-DATA-ASSIGN-UNKNOWN`, `E-DATA-ASSIGN-LEVELS`, `E-DATA-ASSIGN-VARIES`, `E-DATA-ALLOCATION-NO-ARMS`,
`E-DATA-ASSIGN-MISSING`, `E-DATA-ASSIGN-METHOD`, `E-DATA-ALLOCATION-WITHIN-ARMS`,
`E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ALLOCATION-METHOD`, `E-RUN-ARM-UNRESOLVED`. Retired:
`E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED`. Extended to
a new fault rather than minted: `E-SWEEP-PATH-DUPLICATE` (two `sweep.groups` entries sharing a `by`).

## Routed from task 19 — a recorded divergence whose recorded excuse does not cover it

`expand`'s condition **index order** for `ablate × groups` diverges from what `reference.md`
§ Expansion modes prints (`00_cohort=derivation__baseline` … `03_cohort=validation__baseline`) and from
§ How artifacts are organized' Index row.

`spec-defects.md` § Per-cell baseline numbering records this — but it argues the interleaved rule is
ill-defined *once a second axis exists*, and **explicitly exempts the single-group-axis case**: "with
one group axis the cells *are* contiguous, and the rule and the example agree." The printed example is a
single group axis. **So the code diverges from the document precisely where the recorded excuse does not
apply, and the record therefore does not cover it.**

That entry names "the groups slice" as owner with a document decision as its deliverable. Task 19's
reviewer grepped this slice's plan, its design spec and `H3c-SCOPING.md` and **found no mention** — so
whether "the groups slice" means this one is unresolved, and nobody has done the document decision.

**Settle it here, as part of step 7's declared-vs-derived and schema-fields-in-prose passes.** Three
outcomes are legitimate and the choice is yours to argue:

- the printed example and the Index row are right and the code is wrong — then this is a code finding,
  and say so rather than fixing it silently in a documentation task
- the code is right and the two documents are wrong — then fix them, since the documents lead only when
  they are describing what was decided, not when they record an unimplemented ordering
- the divergence is real and deliberate — then the `spec-defects.md` entry is wrong to exempt this case,
  and the correction belongs in `reference.md` where a reader will see it, not in a gitignored file

Task 19 was asked to delete the one assertion pinning the code's current order, so nothing in the suite
entrenches an answer before you pick one. **Probe the actual order before deciding** — do not reason
from the spec-defects entry, which is the artifact under suspicion.

## The count that should shape how you run your own passes

**Five checks in this slice turned out unable to fail**, each caught by a mutation rather than by
reading:

1. an assertion arithmetically implied by another in the same test (arm `resolved` summing to a roster
   whose arm sizes were already pinned)
2. a control asserting only absences, which passed with the whole check disabled
3. a headline mutation applied to an extracted helper's body while the real call sites went untested
4. a `units_hash` assertion written to prove an arm is a view, which cannot detect a re-resolution at all
5. a fixture whose cluster partition made the correct and the buggy answer numerically identical

**Your steps are more vulnerable to this than any implementation task's**, because a consistency pass
that finds nothing and a consistency pass that ran nothing produce the same output. That is why every
step says to prove the check can fail, and why step 1 says it twice.

The two transferable rules, in the form they were learned:

- **Run the mutation before believing the test, and run it where the behaviour lives** — not where the
  test happens to look. Both misses above (3 and 5) were green suites over real bugs.
- **Never filter the output of a sweep whose job is to find a string.** Filter the file list instead.
  A reviewer checking this exact rule lost a true hit to `grep -v superpowers`, because the matching
  line contained the path `docs/superpowers/spec-defects.md`.

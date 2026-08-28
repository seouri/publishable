# G1 — the growth-chart feasibility gaps: plan

Executes [the design](../specs/2026-08-28-growth-chart-gaps-design.md), which decides against
[`G1-SCOPING.md`](../G1-SCOPING.md)'s measurement of `main` at `84e6802` on 2026-08-28.

**Baseline to hold against:** `uv run pytest -q` → 3485 passed, 1 skipped, 2 xfailed.

**Two standing rulings every task inherits.** The refusals — mixed-effects models, Cochran's Q,
conditional logistic regression, DeLong, the shortcut reliance index — stay refused, and no task may
propose otherwise. And gap 4 is **not a defect**: it is retracted in Task 1, and any task that finds
itself about to exempt `report_by` from `W-DATA-CLUSTER-UNDECLARED` has misread the ruling.

---

# Batch A — the retraction and the two sentences

**This batch is where the findings will be.** A documents-and-codes batch looks like the safest to
skip and is the one whose output no later batch reads, so it gets a review of its own.

## Task 1 — retract gap 4 in the feasibility analysis

`docs/feasibility-growth-chart-literacy.md` § Gaps, entry 4.

The entry claims a defect and there is none: `validate.py`'s `_warn_undeclared_cluster` docstring
states the exclusion of `statistics.report_by` and its reason, and `reference.md` § Warnings core
reports enumerates the four exclusions without it. Rewrite the entry to state the decision, the
reason, and — since the measured cases really are not clusters — that the warning's own message
anticipates the false positive.

- **Do not renumber 5, 6 and 7.** § Executability's row 1 and two config sections name gap 4 by
  number.
- **Do not delete it.** The factual half — that the warning fires on those two configs — is true and
  measured, and this repo corrects a published claim by saying what it replaces.
- **Mutation:** none. Verify by grepping the analysis for the word *gap* and confirming every
  cross-reference to 4 still reads correctly after the rewrite.

## Task 2 — state a `fold` level's `stratify_by` type

`reference.md` § Repeat kinds, the per-kind field table, the `fold` row.

`stratify_by` is `str | None` (`replication.py:49`), singular, and the field table currently says
*"plus optional `stratify_by`"* with no type. Give it one, in the table where `k` already has its
own. Say that it names **one** attribute and why: a fold balances its folds on one attribute, which
is what `E-REPL-FOLD-STRATIFY-UNKNOWN`'s message already tells a user who passed a list.

- **Check the sibling spellings while here**, and say in the same sentence that
  `data.units.holdout.stratify_by` and `data.units.assign.<axis>.stratify_by` are **lists** — the
  asymmetry is the whole reason this is confusing, and naming only one half leaves it confusing.
- **Mutation:** the § Validation row for `E-REPL-FOLD-STRATIFY-UNKNOWN` must still be true of the
  code after the edit; grep for it and read it, do not assume.

## Task 3 — say what `measurements.collapse` applies to

`reference.md` § The one config file, the `measurements` inline comment and the paragraph beneath it
that names `by` and `collapse`.

State that `collapse` applies to **every** carried column, which is what makes the per-column map
the ordinary case rather than the exception, and point at § Validation's existing rows for what a
mismatched rule earns. The per-column map is built (`units.py:863`) — this adds no capability.

- **Do not restate the row's contents.** A sentence that derives its claim from a table is repaired
  by fixing the table; this one points at it instead, which is what keeps it self-maintaining.

**Batch A review**: read all three edits against the code they describe, and confirm Task 1 changed
no numbering.

---

# Batch B — gap 1, the crash

## Task 4 — `E-TEMPLATE-PARAM-PATH`, raised where the `ValueError` is

`materialize.py:73`, and the template load path.

Per Decision 4 the constraint stays; what changes is that it is a diagnostic rather than a
traceback, and that it fires at **load** rather than only at `generate experiment` — a spec whose
paths are malformed is malformed for `list-templates` and `validate` too.

- Mint `E-TEMPLATE-PARAM-PATH` and add its row to `reference.md` § Errors `validate` reports, in the
  table's own alphabetical position.
- The message names the path, says a path is `head.leaf`, and gives the remedy in one word — the
  analysis's own workaround was renaming `reference_frame` to `frame.reference`.
- § Templates states the constraint beside the three-states table. **The `Param` constraint table
  gains nothing** — a path is not a constraint on a value, and the table's vocabulary is closed.
- **Grep before building**: `_parameters_block` has exactly one call site (`materialize.py:146`).
  If the raise moves to load, confirm nothing else was relying on the old exception type.

## Task 5 — pin it, on both arms, through the real console script

- A one-segment path and a three-segment path, each producing the code and the message rather than a
  traceback; **two literals, because two arms of one refusal are what this file's own history says
  goes unpinned**.
- **Verify by probe, then pin by mutation.** A subprocess probe proves the moment; restore the bare
  `ValueError` and watch each test go red, then restore the fix and watch each pass. Report the
  number the command printed, not a count nobody read.
- **Check the mutation's two branches can differ** before trusting it: a test asserting only that
  *something* raised passes under both.

---

# Batch C — gap 3, the duplicate condition

## Task 6 — `W-SWEEP-CONDITION-DUPLICATE` over resolved `values`

Per Decision 3 the check asks *do two conditions resolve to the same `values` over the same units*,
not *does a baseline fix a swept path*. It runs over `expand`'s output, so it is blind to which mode
produced either condition.

- **Same units** is part of the predicate, not an assumption: two conditions on a `groups` axis hold
  different units and are not this fault — they have their own codes.
- Reported **once**, for the first duplicated pair in condition order, on
  `W-DATA-CLUSTER-UNDECLARED`'s own shape: the remedy is one sentence whichever pair a reader looks
  at.
- Add the row to `reference.md` § Warnings core reports.

## Task 7 — the message names the working spelling

Reuse the sentence § Expansion modes gives and `W-SWEEP-BASELINE-CONFOUNDED` already quotes: *fix
the axis you are measuring and leave the ones you are stratifying over free, and each cell gets its
own baseline.* Two warnings sharing a remedy is correct — they are two symptoms of one mistake.

- **Read where that sentence sits before copying it.** A recipe is its calls plus where they sit,
  and this repo has lifted a message and left its containment behind.

## Task 8 — pin it, with the sharp cases proven still sharp

- The measured fixture: `baseline: {stimulus.physiology: healthy}` beside
  `grid: {stimulus.physiology: [healthy, concerning], stimulus.schedule: [sparse, dense]}` → six
  conditions, duplicate pairs `(0, 2)` and `(1, 3)`.
- **A decoy on each side.** A fixture whose duplicate pair sorts first rules out only *first*-wins;
  put a non-duplicate condition before and after the pair.
- **Size the fixture to the orderings it must distinguish** — a two-condition fixture only ever
  distinguishes two answers, and this predicate has more.
- Assert that `E-SWEEP-LEVEL-DUPLICATE` and `E-SWEEP-BASELINE-GROUP` still fire on their own shapes
  and that this warning does **not** also fire there, since a group-axis duplicate already has a
  sharper answer.
- Assert the **absence** on the corrected spelling — and assert it on the stream the warning writes
  to, not on the whole output.

---

# Batch D — gap 7, gap 2, and the close

## Task 9 — `compare: {to: constant, value: <number>}`

Per Decision 2. Widen the existing `E-HYPOTHESIS-FORM` gate rather than replacing it.

- A non-summary metric may now satisfy `compare` three ways: `{condition, to: baseline}`,
  `{contrast}`, `{to: constant, value}`. A `summary` metric still takes **no** `compare`.
- `value` is required when `to: constant` and is a number; its absence and its type each earn a
  refusal, and the code for them is `E-HYPOTHESIS-FORM`'s sibling rather than a new family — decide
  which at implementation and record it, do not mint two.
- The verdict is `verdict_rests_on: computed` and **joins the hypothesis family**. That is the gain:
  the analysis's E2 and E6 claims currently leave the family to be expressible.
- `evaluate_on` is untouched. `ci95_lower` against a constant is superiority; `ci95_upper` is
  non-inferiority.
- `reference.md` § Pre-registration's `compare` row and § What a hypothesis is tested against both
  change; so does the field table's `compare` line.
- **Pin the verdict, not only the acceptance.** Testing that the form validates while nothing checks
  the verdict it produces is this file's *testing the refusal, never the honouring* row.

## Task 10 — gap 2 closes as a documented limitation

Per Decision 1. `reference.md` § Studies gains a paragraph: a correction family does not cross a
run; the reason is that a cross-run family's members are asserted rather than core-built, so
correcting at that size would render a level that looks core-computed and is not; the route is that
the author corrects and declares it, while each member keeps the within-run family it really was
corrected at.

- **No code.** `study.py` is untouched, and the paragraph says so in its own words rather than
  leaving a reader to infer it from silence.
- Name the analysis's `{E5a–d}` as the worked case — four rosters, four runs, one declared family.

## Task 11 — close the branch

- **Whole-branch re-run.** Not a formality: the branch under Batch B's and Batch C's mutations
  changed after those mutations were written, and this repo has shipped a stale prediction that way.
- **The consistency passes** in full over the four documents — this slice touches `reference.md` in
  five places across three sections.
- **`spec-defects.md`**: strike the three G1 entries that closed, and **amend** rather than strike
  the correction-family one, since Decision 1 closes it as a limitation rather than by building the
  mechanism it asked for. A filing whose closure is a document paragraph must say that, or the next
  reader looks for the code.
- **Re-validate the fifteen** in `2026-08-28-gcl-measurement/` and re-record § Executability's dated
  entry in the analysis against the new commit. Expect the two `W-DATA-CLUSTER-UNDECLARED` warnings
  to remain — gap 4 is retracted, not fixed — and expect no new warning, since every one of the
  fifteen already uses the spelling Decision 3 recommends. **If a sixteenth warning appears, that is
  a finding about Task 6 and not about the configs.**

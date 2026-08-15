# Task 18 — controller additions

These are requirements, with the same force as the brief file they accompany.

**`docs/superpowers/` is gitignored and will not survive the merge.** That is the fact this whole task
turns on: anything recorded only in `spec-defects.md` is recorded nowhere, as far as the repository is
concerned. Every decision below is therefore "does this belong in `reference.md`, or is it genuinely
scratch". Say which for each, and why.

## The gaps this slice accumulated, with their current state

Tasks 13 and 14 already wrote several of these into `reference.md` rather than leaving them scratch.
**Verify each landed and says what the code does** — do not re-record what is already recorded.

| Gap | Where it stands |
|---|---|
| `allocation.json` vs. § What `study add` redacts | **Yours.** It is the one artifact that is a list of **unit identities** — "which patients were in the treatment arm" — and § What `study add` redacts names four fields, none of them this file. Brief step 1 |
| § Resuming's "read rather than re-drawn" has no reader | **Yours.** Task 15's report has the sentence to quote, written to be quoted: `OPERATION_COMMANDS = {"validate", "run"}` contains no `resume` command, so nothing calls `build_allocation_document` a second time against an existing file, and no test exercises this path. Brief step 2 |
| `technical_n` withheld under an arm and under a `report_by` stratum | Task 13 recorded it in § What isn't a repeat. Verify |
| `validate.levels_for` counts `report_by` strata over the whole roster, feeding `W-STATS-REPORTBY-THIN` | Task 13 recorded it in § What isn't a repeat and on the `W-STATS-REPORTBY-THIN` row. Verify. It becomes reachable when task 17 retires the refusal |
| An out-of-enum `allocation` beside a group axis draws no row once `E-DATA-ALLOCATION-UNSUPPORTED` retires | Task 12 marked its row "Temporary in that one respect"; task 17 owns the retirement. Check what it left |
| A declared contrast between two same-arm conditions with `within: {arm: <other arm>}` | Task 16b's guard skips it (no differing group axis) and the units intersection is empty — the same `delta: null` beside `paired: true`. *Contrast has units in common* owns it and the scoping records that row as MISSING. Task 16b was asked to add one line saying which row owns which route; verify it did |

**Anything on that list you find unrecorded is yours.** The brief says "record them; do not invent a
rule" — that direction still holds, and it is the hard part: a gap written as a rule is worse than a gap
written as a gap, because the next reader implements it.

## Step 2b — the exit row, settled by the user

Task 20 step 6 verifies against a § Mistakes core prevents row named *two identical measurements
reported as two arms*. **That row does not exist in any tracked document** — the phrase lives only in the
gitignored scoping file, so the slice's exit criterion could not have been signed off as written.

`experimental-designs.md` § Mistakes core prevents is where it belongs. Read the existing rows first;
they state a mistake and what makes it structurally impossible, and yours must do the same **against
what the slice actually built**, not against what it was hoped to build:

- a group axis narrows each condition to its arm, through **one shared roster** — an arm is a subset
  view, never a re-resolution
- arms and allocation must agree in both directions (`E-DATA-ALLOCATION-NO-ARMS`,
  `E-DATA-ALLOCATION-WITHIN-ARMS`)
- a contrast across arms is **refused** rather than reported paired over zero units
  (`E-DATA-ALLOCATION-CONTRAST`)

**Cite the mechanisms, not the task numbers** — plan numbering does not survive the merge, and this is a
normative document. Check § Mistakes core prevents' surrounding prose for a count phrase that your
insertion makes stale; this repo has shipped a commit titled "three phrases counting a table that grew".

## Step 3

"Commit only if something changed" — but a task that changes nothing must still **say what it checked
and found already recorded**, item by item, against the table above. An empty commit is fine; an empty
report is not.

## Added after task 17 — two more gaps, and one that closed itself

| Gap | Where it stands |
|---|---|
| `limits.min_units_per_cell` is declared, typed, and **read by nothing** | Task 17 was ruled to **hedge the document rather than implement**: the warning was never built for `within` designs either, so task 17 made a pre-existing gap *reachable* rather than creating one, and a new `W-` code is scope creep into the limits family. § Validation's *Cells are populated* and *Allocation is coherent*, and the `min_units_per_cell` comment in the config schema, should now read the way *Assignment method isn't drawn* and *Allocation deltas aren't computed* do. **Verify that landed** — and if it did, this needs nothing further from you |
| `data.units.assign`'s per-axis blocks have no unknown-key ("did you mean") closure — `envelope.py` types the whole block a bare `dict` | Task 17 corrected § The one config file's "`.holdout` and `.assign` inherit the same treatment when their slices land" sentence to say plainly that `.assign`'s slice landed without it. **That is the model for how a gap gets recorded durably**, and it needs nothing further — verify it |
| An out-of-enum `allocation` beside a group axis | **Closed, not recorded.** Task 12's reviewer pre-specified `E-DATA-ALLOCATION-METHOD` in `spec-defects.md`, code name and all; task 17 minted it when the blanket refusal it depended on retired. Remove this from any gap list you inherit |

The middle row is the one to study before you write anything. A gap recorded as *"this slice landed without it"* in the normative document is durable and honest; the same gap recorded only in the gitignored `spec-defects.md` is recorded nowhere. Task 17 did the same class of thing twice in one commit — once correctly, once not — and the difference was which file it wrote to.

## The `min_units_per_cell` gap sentence must name the concrete failure — verified

The controller probed this rather than reasoning about it. `units.arms_of` refuses a declared level
**no unit holds** (`empty = [level for level in declared if not partition[level]]` →
`E-DATA-ASSIGN-LEVELS`), so an **empty arm is already refused**. `limits.min_units_per_cell` is read by
nothing anywhere in `src/`.

**So the uncovered case is a one-unit arm**: it validates clean and produces an interval over n = 1.
Nothing warns.

If the gap sentence says only "the warning isn't built", a reader has to derive that for themselves.
**Say the failure**: a two-arm design where one arm resolves to a single unit passes `validate` and
reports a `basis: units` interval computed from one observation, with `min_units_per_cell` declared in
the config and read by nothing. That is what someone recognises in their own run; the abstract version
is not.

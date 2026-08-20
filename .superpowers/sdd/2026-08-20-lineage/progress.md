# H8a — lineage and `io.reuse_from` — ledger

Scoping: `docs/superpowers/H8-SCOPING.md` (H8 measured at **30 tasks against a one-row charter**, split
10/8/12). Design: `docs/superpowers/specs/2026-08-20-lineage-design.md` (11 decisions, **plus § Rulings
from the controller** and **§ What the record still gets wrong**). Plan:
`docs/superpowers/plans/2026-08-20-lineage.md` (**12 tasks**, six batches).

Baseline at `28e311d`: **2456 passed, 1 skipped, 2 xfailed.**

## What H8a is, and the figure it may finally move

`io.reuse_from` is **the sole named remaining core-side blocker for six of nine** configs and
`grep -rn "reuse_from" src/publishable/` returns **zero**. H8a is the first sub-slice in a long while
that can move a count — which is exactly why the counting had to be fixed first.

## Two figures were wrong, and both were mine to carry

**"Six with no remaining core-side blocker" answered no consistent question.** The contradiction is
verbatim in one cell: `C1 | No — blocked on io.reuse_from (no remaining core-side blocker either)` beside
`E3 | No — blocked on io.reuse_from`, with E3 **excluded** from the six. Strict reading three, loose
nine; **six was really the count needing `io.reuse_from`**, a useful number wearing the wrong name, which
followed C1–C3 out of the *refused* column when H4b-1 landed.

**Then "three" fell the same way, within the hour.** H8a's design measured the
`report_by`-under-`resample` gap live on **seven of nine** — E1, E2, E4, E6, C1, C2, C3 — while the
record charges it to C1–C3 alone, so **E1 and E2 sat inside the three carrying the gap E3/E4/E6 were
excluded for.** Measured twice by computing: `t_over_units` `[0.3209, 0.7791]` without
`resample_columns` against `percentile_over_units` `[0.3583, 0.7500]` with it, moving **both** recorded
columns, so the gap is **per recorded column** rather than per headline metric.

**Ruling: this analysis gets a table, not a number** — 8 of 8 validating clean (**the only figure
`validate` can see**), 6 needing `io.reuse_from`, 7 meeting the `report_by` gap, 1 free of every named
dependency. Corrected by **appending** to the dated entries and by **editing `CLAUDE.md` at the minting
site**, where all five later repetitions derive from. **Cost if wrong:** a reader must consult a table
instead of quoting a headline, which is the price of the headline having been wrong twice.

**And the shape is the finding, not the arithmetic.** Both figures were produced identically: a slice
retired one blocker, moved configs out of the *refused* column, and **carried the summary phrase forward
without re-deriving what it counted.** That is the *carried claim* failure this repo records in code,
appearing twice in a number.

## Two rulings on the design, before it reached the plan

**The artifact-name rule is containment only.** The design measured that `read_upstream` returns the
contents of `../../secret/x.json` and moved to refuse separators — but **`reference.md` § Steps and
artifacts documents a `name` as a relative path and gives `programs/gpt-4.1__seed29.json` as a worked
legal example**, so that rule would break a documented case. And `name` comes from **the user's own
step**, which can already `open()` anything, with `CLAUDE.md` explicit that **core never inspects the
body of user Python**. So: refuse `..`, an absolute name and an escaping symlink; **keep forward
separators legal**; and say in writing that a step can read any file regardless, so nobody mistakes it
for a boundary. The design carries **a positive control** where `programs/a.json` must still read, and a
mutation widening the rule **must fail that control** — a fix that overshoots is caught, not just one
that undershoots.

**An absolute locator stays legal while an absolute name does not** — a locator addresses a run, which a
config may state; a name addresses an artifact **within** a run, whose location is derived from the step
it belongs to.

## The plan refused a fifth number, which is the outcome the ruling wanted

The design's own payoff line projected *"8 of 8 transplantable"* — **a fifth figure produced by the very
standard the correction had just ruled inconsistent.** The plan declined it and instead quotes the
corrected table **with one row moved** (`io.reuse_from` 6 → 0), leaving the other three untouched. A plan
overruling its own design on a counting question, citing the correction, is the record working.

## The guard pin, and one arm with a named editor

**Task 11 runs first**, four arms captured by running: the `run.yaml` key list, the **twelve-key**
`provenance` list ending at `allocation_hash` with `upstream` **absent**, the `execution` block's scope
routing measured from a real run (**Decision 4's entire foundation**), and the shipped positive
`read_upstream` read.

**Arm B is the one arm H8a will move, so its docstring names task 7 as its only authorized editor** —
append `upstream`, reorder nothing. That converts a change detector the slice would otherwise have to
weaken quietly into **a bounded, reviewed edit**, which is the thing five previous slices got wrong by
editing a pin to accommodate new work.

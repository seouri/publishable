# H7d Part A — the apparatus: observe and record — ledger

Design: `docs/superpowers/specs/2026-08-19-apparatus-part-a-design.md` (14 decisions).
Scoping: `docs/superpowers/H7d-SCOPING.md`, **including its appended correction**.
Plan: `docs/superpowers/plans/2026-08-19-apparatus-part-a.md` (18 tasks, five batches).

Baseline at `4508ea6`: **2363 passed, 1 skipped, 2 xfailed.** Four gates clean.

## What this slice is, and the figure that does not move

`statistics.null_test` closed the `statistics` family; this opens the apparatus. **Part A observes and
records; it cannot stop a run** — the gate, `EXIT_EXTERNAL`'s reader, run-stops-here and the
truncated-plan distinction are Part B's, each routed in writing rather than left implicit.

**It unblocks zero configs.** All nine configs in the feasibility analysis earn only
`W-DATA-CLUSTER-UNDECLARED`; **six with no remaining core-side blocker, three executable, both
unmoved** — and the design's sharper point is that **the only direction this slice can move a config
count is down.** The distinction worth carrying, which the old charter collapsed: *as measured* the nine
need nothing from H7d; *as designed* their template declares a probe, and such a run today **validates
clean, exits 0, records `apparatus: null`, and never calls the probe.**

## Two things settled before any code

**The scoping was wrong about exit code 5, and the design caught it within hours.** `EXIT_EXTERNAL = 5`
ships in `diagnostics.py` with **no reader anywhere** — I confirmed it. Corrected by **appending** to the
scoping, because a scoping records what was measured on its date. It is the **second time on this project
that re-measuring a scoping the same week falsified one of its claims**; `H7b-SCOPING-2.md` lost seven.

**And the documents change before the code.** § The apparatus core can only observe sites the
declared-keys check, the credential check and the null warning **at `dry-run` only — and `dry-run` does
not exist**, so taken literally Part A would call user code once per execution with **nothing checking
that a declared key came back.** Ruling: the three become **phase-independent functions in
`apparatus.py` that every caller invokes**; no check moves *off* `dry-run`, which stops being *where
they live* and becomes *one of the places they run*. **No new command.** That is task 1, it precedes
every code task, and it touches **three files** — `experimental-designs.md` carries the same siting, and
a one-file sweep is this repo's named habit.

## The plan's corrections against the code — fourteen, eight of which reshaped a task

The plan step earned its place. The eight that changed a task's shape, in short:

- **The ledger's `condition` and `facts` keys are `<nn>_<label>`, not the bare label** the design named —
  and a **no-sweep run's label is `None`**, which neither document nor design answered. Ruled
  `f"{index:02d}"`, because canonical JSON cannot sort a `None` key.
- **Neither published mapping can supply `W-APPARATUS-UNANSWERED` at the design's grain**: `unobserved`
  aggregates over conditions, and `facts` records the *answer* for a partially answered fact — so a
  `facts`-derived warning is **silent for exactly the flaky case the null rule exists for.** Task 7 keeps
  per-(condition, fact) counts. **§ Warnings core reports was in neither the design's rows task nor its
  sweep.**
- **A probe returning a non-`Apparatus` had no refusal** — it reaches `run` as a traceback.
  `E-APPARATUS-RETURN` minted; **five codes, not four**, everywhere.
- **The design's "append after the execution" mutation cannot fail**, because a failed execution never
  stops the run, so the line is written either way. Replaced with a run-scoped count: **4 against 2.**
  That is the *a mutation is a claim too* row, caught in the plan rather than by a reviewer.
- Decision 5's value contract enforced **at core's boundary, not in `Apparatus.__init__`**, or a
  probe-body raise gets mis-coded; `E-APPARATUS-FACT-TYPE` needs catch-and-re-code because `_refuse`
  hardcodes another code; `execute_plan` **cannot supply the condition list** (plan-derived, empty for a
  `run`/`summary`-only pipeline); and `main`'s handler prints a bare `{exc}` **with no collector**, which
  fixes the containment site and narrows `APPARATUS_CODES` to the five so **every member is pinned.**

## The guard pin, chosen the way the last slice's was

**Task 18 runs first.** It asserts the full `provenance` key list, `provenance["apparatus"] is None`, and
**no `apparatus/` directory** — captured from a **real end-to-end run** at `4508ea6` rather than
transcribed from `cli.py`. Its mutation is `"apparatus": {"probe": None}`, **exactly the `probe: null`
spelling decision 7 rejects.** Tasks 11 and 12 replace what it covers, which is the point: the preceding
slice's batch-1 pin caught a spurious key three batches later without ever being edited.

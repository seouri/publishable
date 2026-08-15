# Task 18 report — recording the slice's gaps, and the exit row

## Status: DONE

## Item-by-item, against the addendum's tables

**Table 1 — accumulated gaps**

1. **`allocation.json` vs. § What `study add` redacts** — was unrecorded. `study add` is itself
   `— not yet built` (§ Package layout), so I wrote it as an inference from the shape already
   committed to (§ Building one's bundle tree holds only `*.run.yaml`; the CLI table says `study add`
   "copies a run record," singular), not as a checked fact — and named the residual question ("should
   a bundle ever be allowed to carry `allocation.json`?") as open for whoever builds `study.py`.
   `docs/reference.md` § What `study add` redacts, new paragraph after the "None of this disturbs
   verification" line.
2. **§ Resuming's "read rather than re-drawn" has no reader** — was unrecorded in any tracked
   document (only in `artifacts.py`'s docstring, which is tracked, but not in `reference.md` itself,
   and only in `spec-defects.md` as a gap note). Added a paragraph quoting task 15's exact finding —
   `OPERATION_COMMANDS = {"validate", "run"}` has no `resume` — scoped to this one claim, not to
   resume's overall build status (that is H9's, already tracked in the spine design doc).
   `docs/reference.md` § Resuming, after the `allocation.json` "read rather than re-drawn" sentence.
3. **`technical_n` withheld under an arm / a `report_by` stratum** — verified already recorded
   correctly by task 13, in § What isn't a repeat. No change.
4. **`validate.levels_for` counts `report_by` over the whole roster, feeding `W-STATS-REPORTBY-THIN`**
   — verified recorded in § What isn't a repeat, correctly updated post-task-17 ("Reachable now").
   **But the `W-STATS-REPORTBY-THIN` table row itself (§ Warnings core reports) still carried the
   pre-task-17 phrase "this build cannot yet construct," contradicting the prose next to it that says
   the gap is reachable.** This is the one addendum claim I found *not* in the state the after-task-17
   table implied. Fixed the row to match: "a live one rather than a latent one." Grepped
   `cannot yet construct|latent` across `docs/*.md` afterward — no third stale location.
5. **Out-of-enum `allocation` beside a group axis** — per the addendum's own after-task-17 table,
   this is closed via `E-DATA-ALLOCATION-METHOD` (task 12/17), not recorded as an open gap. Verified
   the code and its § Errors `validate` reports row exist and are internally consistent. No change.
6. **A declared contrast between two same-arm conditions with `within: {arm: <other arm>}`** —
   verified task 16b's *Contrast has units in common* row already states which row owns which route
   ("Covers the case *Allocation deltas aren't computed* above does not..."). No change.

**Table 2 — added after task 17**

7. **`limits.min_units_per_cell` declared, typed, read by nothing** — verified task 17 hedged rather
   than implement, per the addendum. The controller's probed finding said the existing "specified, not
   built" comment doesn't name the concrete failure. Added a paragraph in § Allocation:
   within-subjects-or-between-subjects naming the one-unit-arm case exactly as probed (`validate`
   passes clean, reports a `basis: units` interval from n = 1, nothing warns), distinguished from the
   already-refused empty-arm case (`E-DATA-ASSIGN-LEVELS`). Also pointed the `min_units_per_cell`
   config comment at this section. Left the § Validation table rows (*Cells are populated*,
   *Allocation is coherent*) untouched — they already say "specified, not built in this build
   (warning)" and are a different kind of entry (what the check would catch), not the gap sentence
   the probe was about.
8. **`.assign`'s per-axis unknown-key closure** — verified task 17's sentence ("`.assign`'s slice has
   landed without it: `envelope.py` still types the block a bare `dict`...") is exactly the durable
   model described in the controller notes. No change.
9. **Out-of-enum `allocation`, closed** — verified `E-DATA-ALLOCATION-METHOD` exists; confirmed this
   is not on any open-gap list (same item as #5 above).

## Step 2b — the exit row

Added **Two identical measurements reported as two arms** to `docs/experimental-designs.md`
§ Mistakes core prevents (Statistical), directly after *Paired analysis of an unpaired design*.
Cites the three mechanisms by error code (`E-DATA-ALLOCATION-WITHIN-ARMS` as the one that actually
prevents the named mistake — every unit measured under both arm labels — with `E-DATA-ALLOCATION-NO-ARMS`
and `E-DATA-ALLOCATION-CONTRAST` as the mirror and the cross-arm refusal), not task numbers. Removed a
bare source-symbol reference (`units.arms_of`) an advisor review flagged as inconsistent with every
other row in both Mistakes tables, which name config fields and error codes only — kept the mechanism
("one shared roster... a subset view of it, never a re-resolution") without the symbol.

Checked the table for a stale count phrase near the insertion — none exists in
`experimental-designs.md` (unlike the reference.md table this repo has previously shipped a fix for).

## Verification

- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, 40 source files.
- `uv run pytest -q` — 1488 passed, 2 xfailed (docs-only changes; no test count regression expected
  or seen).
- Mechanical pass: no trailing whitespace/tabs in either touched file; new/edited table rows have the
  same column count as their header; grepped for the anchors and error codes I cited
  (`#allocation-within-subjects-or-between-subjects`, `#package-layout`, `E-DATA-ASSIGN-LEVELS`,
  `E-DATA-ALLOCATION-WITHIN-ARMS`, `E-DATA-ALLOCATION-NO-ARMS`, `E-DATA-ALLOCATION-CONTRAST`) and
  confirmed each resolves to an existing heading or table row.
- Ran an advisor pass before committing. It caught two real issues, both fixed before this report:
  (a) my first draft of the `study add`/`allocation.json` paragraph stated an inference as a checked
  fact about an unbuilt command — rewritten to show the inference and name the open residual; (b) the
  Mistakes-table row cited an internal Python symbol no sibling row does — dropped, mechanism kept.

## Concerns

- **The addendum's after-task-17 table said row 4 (`W-STATS-REPORTBY-THIN`) "should now read the way
  ... *Allocation deltas aren't computed* does" and needed "nothing further" if it landed** — but the
  table row itself had not actually been updated to match the prose paragraph beside it; only the prose
  had been. This is a real instance of the drift the addendum was worried about elsewhere (task 17's
  "two ways to record the same class of gap"), just smaller in scope. Fixed as described above.
- No requirement in the brief or addendum turned out to be unsatisfiable or resting on a false premise.
- No commit yet — see next message for the sha.

## Addendum — coordinator review round

The coordinator's review (after the report above was written, before commit) found six items. All six
addressed, in `docs/reference.md` only (the experimental-designs.md row was approved as-is):

1. **Important — the concrete failure was wrong for the arm size named.** I had written that a
   one-unit arm "reports a `basis: units` interval computed from that one observation." False: every
   interval construction in `stats.py` guards `< 2` and returns no interval below two values (confirmed
   by grep — `stats.py` lines 81, 219, 226, 289, 292, 371, 374, 414, 523, 639, 644, 741, 858 all guard
   at 2), so a one-unit arm gets a point estimate with `ci95: null`, which is core behaving correctly,
   not the gap. Fixed to name the two-unit arm as the uncovered case, and added the single-unit
   contrast explicitly so the sentence now teaches the boundary instead of asserting past it.
2. **Important — a broken discourse referent.** My resume paragraph had been inserted between "It
   takes the execution order from `sweep.yaml`..." and "Under a `batch` level **this** is
   load-bearing...", breaking "this"'s reference to execution-order-reading, and my own opener ("That
   last claim") pointed backward past itself into the same ambiguity. Fixed by moving my paragraph to
   *after* the batch paragraph and rewording the batch sentence to restate its subject explicitly
   ("reading the execution order rather than re-deriving it") rather than leaning on "this", removing
   the ambiguity regardless of paragraph order. My own paragraph now opens by naming its subject
   (`allocation.json`'s "read rather than re-drawn" rule) instead of "that last claim."
3. **Important — "the CLI table above" pointed below, not above.** The `study add` row in § Creation
   commands is ~20 lines *after* my paragraph in § What `study add` redacts. The real antecedent is
   above: § Building one's command block (`publishable study add ... run.yaml --as main`), which does
   show a run.yaml path rather than a directory. Reworded to cite `§ Building one` by name and anchor
   (`#building-one`) instead of asserting a direction.
4. **Minor — the bundle also holds `study.yaml`, not only `*.run.yaml` files.** Fixed the sentence to
   say the bundle holds "that file [run.yaml] and `study.yaml` — run records, never a copy of a run
   directory," which is what the file tree in § Building one actually shows.
5. **Minor — the § Package layout citation for resume's unbuilt status wasn't supported.** That
   section marks *modules*, and neither `cli.py` nor `run_identity.py` carries a "not yet built"
   annotation — the fact (no `resume` command exists) is true but that link didn't support it. Dropped
   the link; the claim now rests on the `OPERATION_COMMANDS` quote alone, which is the actual evidence.
   Left the `study add` → `#package-layout` link alone, since `study.py` genuinely is marked
   `— not yet built` there.
6. **Minor — a count-shaped phrase adjacent to the row I'd edited.** "`W-ENV-UNLOCKED` is the one row
   above that names a gap in this project rather than in yours" now sat above a `W-STATS-REPORTBY-THIN`
   row I'd just changed to assert a live gap in this build. Added a parenthetical distinguishing the two:
   `W-STATS-REPORTBY-THIN`'s firing condition is still the user's thin stratum; only its *precision* is
   core's gap. Narrowed "names a gap" to "whose *firing condition* is a gap" for the same reason.

Re-verified after all six fixes: `uv run ruff check .` (all checks passed), `uv run mypy` (success, 40
files), `uv run pytest -q` (1488 passed, 2 xfailed — unchanged), no trailing whitespace/tabs in either
touched file, and every anchor/link added or touched in this round (`#building-one`,
`#allocation-within-subjects-or-between-subjects`) resolves to an existing heading.

Status remains DONE. No requirement in the review turned out to be wrong or unsatisfiable — item 1 was
the coordinator correcting its own earlier addendum, which it said outright.

# Task 9 report: `random` and `blocked` are refused as method values

## What was done

- `src/publishable/validate.py`: added `DRAWN_ASSIGN_METHODS = ("random", "blocked")` beside
  `ASSIGN_METHODS`, and a third `elif` branch in `_check_assign`'s method loop that reports
  `E-DATA-ASSIGN-DRAWN` when `method` is in-enum but not yet executable. The three branches
  (`None`, out-of-enum, drawn) are one `if`/`elif`/`elif` chain reading the same `method` value, so
  `E-DATA-ASSIGN-METHOD` and `E-DATA-ASSIGN-DRAWN` are mutually exclusive by construction rather
  than by convention — a value in `DRAWN_ASSIGN_METHODS` is by definition inside `ASSIGN_METHODS`.
  `by_attribute` falls through both and reports nothing, as before.
- Message states the three required things: drawing is specified but not implemented; `by_attribute`
  — reading an arm already assigned — is the supported method and what a real trial does regardless;
  the value will be honored once drawing is built. No internal slice name appears.
- `docs/reference.md`: new registry row in § Errors `validate` reports, sorted correctly
  (`E-DATA-ASSIGN-DRAWN` before `-METHOD`/`-MISSING`, leaving the one pre-existing sort violation
  task 20 owns untouched); new row in § Validation's mistake table ("Assignment method isn't
  drawn"); a bold paragraph in § Allocation naming the refusal and its code, right after the
  `random`-based config example; a clause on `blocked`'s own paragraph so it stops reading as live
  advice ("otherwise `random` with `stratify_by` is the stronger guarantee — both draws, and neither
  executes until the refusal above lifts").
- `tests/test_validate.py`: replaced the old `test_every_declared_assignment_method_is_accepted`
  (which asserted an exact set that would have gone stale under `random`/`blocked`) with
  `test_by_attribute_assignment_is_accepted` (the control) and a parametrized
  `test_a_drawn_assignment_method_is_refused` covering both `random` and `blocked` separately, each
  asserting the exact `_error_codes` set through `write_config` **and** the direct-`_check_assign`
  path with a message assertion (`by_attribute` and the method string both present) so the code
  alone can't discriminate a deleted branch. Removed the now-unused `ASSIGN_METHODS` import.

## Defect found in the brief

**The brief's scope statement ("Files: Modify `src/publishable/validate.py`... reference.md § Errors
`validate` reports... § Allocation") was too narrow — `docs/experimental-designs.md` presents
`method: random` as a working, copy-pasteable example in both the between-subjects and the
between-subjects-factorial sections, with no caveat, which is exactly the class of cross-document
drift CLAUDE.md's cross-document pass exists to catch.** The brief named only two reference.md
touch points and didn't ask for experimental-designs.md at all, but that document's own charter (per
CLAUDE.md's table of the four documents) is "what each experimental design is expressed [as]; what
core prevents and refuses" — it is the *other* normative place a build-time refusal belongs, and
leaving it silent would mean a reader following that doc's own example hits `E-DATA-ASSIGN-DRAWN`
with no document telling them why. I added one pointer sentence after each `random`-based example
(not a rewrite to `by_attribute`, which would have illustrated a different design), naming the code
and linking to reference.md § Allocation, and left the design itself and both `-UNSUPPORTED` demo
codes as they were.

## Verification

- `uv run pytest` — 1427 passed, 2 xfailed.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, 40 source files.
- Mutation testing on `DRAWN_ASSIGN_METHODS`, `__pycache__` deleted before each apply/revert,
  verified by re-running the tests (never `git status`):
  - Narrowed to `("random",)` → only `test_a_drawn_assignment_method_is_refused[blocked]` failed.
  - Narrowed to `("blocked",)` → only `test_a_drawn_assignment_method_is_refused[random]` failed.
  - Widened to `("random", "blocked", "by_attribute")` → only the control,
    `test_by_attribute_assignment_is_accepted`, failed; both drawn-method tests still passed.
  - Reverted each time; full `tests/test_validate.py` run confirmed PASS after revert.

## Not touched

`E-DATA-ASSIGN-UNSUPPORTED` (task 17's) is untouched and still fires alongside `-DRAWN` on any
truthy `assign`, per the brief. No sweep vocabulary or group-axis expansion code was touched.

## Review round 2 — four fixes, one commit

Independent review confirmed the spec and reproduced both mutation claims exactly. It raised two
Important findings and two Minors, all addressed below in the same commit.

**Important 1 — a growing table invalidated a relative pointer.** `E-DATA-ASSIGN-METHOD`'s
pre-existing row said "unlike **the two rows above**," meaning `E-DATA-ALLOCATION-NO-ARMS` and
`E-DATA-ASSIGN-MISSING`; inserting `E-DATA-ASSIGN-DRAWN` between them and `-METHOD` made that count
wrong, and my new row's own "the same as `E-DATA-ASSIGN-METHOD` **below**" collided with it — two
adjacent rows asserting opposite things about each other's gating. Fixed by naming codes instead of
counting rows in both: `-DRAWN`'s row now says "the same as `E-DATA-ASSIGN-METHOD` immediately below
... unlike `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ASSIGN-MISSING` above," and `-METHOD`'s row
mirrors it, naming `-DRAWN` "immediately above" and the other two "further up." Checked the rest of
that table (lines 416–450) for other position-relative phrases my insertion could have shifted —
`grep -no "row above\|rows above\|row below\|rows below\|two rows\|three rows\|both rows"` over that
range matched only the two I fixed; no other row counts position there.

**Important 2 — the out-of-scope fix was itself incomplete.** My own argument for caveating
`experimental-designs.md` ("a reader following the example hits the refusal with no document saying
why") applies to four passages in `reference.md` I hadn't touched: § Group axes' flat claim ("core
assigns them when `allocation: between` with `assign.method: random` or `blocked`"), its 2×2
factorial YAML (the twin of the experimental-designs example), its design table's "Both randomized …
Two `random` axes" row, § The resolved list order's "`assign.method: blocked` balances arms across
the roster's order," and § Clustered units' "With `method: random` or `blocked` a cluster is drawn
as a whole." Added a pointer at each — a short parenthetical or clause naming `E-DATA-ASSIGN-DRAWN`
and linking to § Allocation, sized to the passage (the flat claim and the two "with `method: random`
…" sentences got an inline clause; the YAML twin and the design-table row got one sentence
immediately after, since editing inside the table or the fenced block would have disturbed either
the column count or the example itself). No example was rewritten to `by_attribute` — each illustrates
a design `by_attribute` doesn't express, same reasoning as round 1.

**Minor 1 — counted prose drifted from the asserted set.** `test_by_attribute_assignment_is_accepted`'s
docstring said "the **two** live `-UNSUPPORTED` refusals" while asserting three
(`E-DATA-ALLOCATION-UNSUPPORTED`, `E-DATA-ASSIGN-UNSUPPORTED`, `E-SWEEP-GROUPS-UNSUPPORTED`) and later
correctly said "three codes" — the one test whose job is to state its own discriminator disagreeing
with itself. Changed "two" to "three."

**Minor 2 — adjacent near-synonyms read as tension.** My new experimental-designs.md sentence called
`random` "the shape a prospective **allocation** takes," two paragraphs above the standing "no
`assign.method` supports prospective **enrollment**." Different claims (allocation drawing vs.
enrollment being incremental) but close enough in wording to look contradictory. Reworded to "a
trial drawing its own arms, rather than reading someone else's, is the case being illustrated,"
which doesn't use "prospective" at all.

### Re-verification after round 2

- Mechanical pass over every line touched in this round: no trailing whitespace, no tabs, `×` used
  correctly (no stray `x` for multiplication in touched text), no en dash, and every new/edited link
  (`#allocation-within-subjects-or-between-subjects`) resolves to an existing anchor. Table row field
  counts (`awk -F'|'`) unchanged on both edited rows in § Errors `validate` reports (still 4 fields).
- `uv run pytest` — 1427 passed, 2 xfailed.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — success, 40 source files.
- Did not touch `docs/feasibility-llm-growth-studies.md`, per instruction.

# Task 11 report: `assign.<axis>.from` joins the constancy check

**Status:** DONE
**Commit:** `b21f42c` — feat(units): refuse a varying assign.<axis>.from within a unit's measurement rows

## Test summary

`uv run pytest`: 1451 passed, 2 xfailed (pre-existing). `uv run ruff check .`: clean.
`uv run mypy`: clean, 40 source files.

## What was built

- `src/publishable/units.py`:
  - `_assign_constant_columns(assign_decl)` — `resolve_units`'s accessor for
    `assign.<axis>.from`, one entry per declared axis. Resolves `from` against
    the axis-name default the same way `validate._check_assign` does, but is
    **gated on `block.get("method") == "by_attribute"`** — found during review
    (see below), matching `_check_assign`'s own elif chain, which reads `from`
    only in that branch.
  - `CONSTANT_COLUMN_RULES` gains a third entry, keyed by the bare word
    `"assign"` (not `"assign.<axis>.from"`) — the registry-shape question the
    brief left open. Rejected the "expand one entry per axis" alternative: the
    axes are config-declared, not known at module load, so the registry can't
    be expanded ahead of time; the docstring records why. `constant` entries
    for `assign` are the dotted path (for the error message), and
    `collapse_measurements`'s lookup strips a key to the segment before its
    first `.` before indexing the registry — a no-op for `cluster_by`/`weight_by`.
  - `resolve_units`'s comment on the old registry limitation is rewritten to
    say `assign` is now reachable and `holdout.from` still is not (it needs
    its own accessor — a single key under a fixed mapping, not one-per-axis).
- `tests/test_units.py`: the brief's two named tests
  (`test_an_arm_varying_within_a_units_measurement_rows_is_refused`,
  `test_an_arm_constant_within_a_units_rows_is_accepted` — the control asserts
  the collapsed unit's `arm` value *and* `technical_n`'s `max: 2` over `min: 1`,
  proving the rows were actually collapsed), plus four more: the "arm varies on
  a non-cluster column reports assign, not cluster" mutation case, a gating
  test for `method: random` (added on review), a three-declarations-not-one-code
  test, and the single-code observation test described below. No fixture
  declares `cluster_by` on the same column as the arm attribute in the primary
  pair, so a varying arm cannot be mistaken for a varying cluster.
- `tests/test_validate.py`: the same reported/control/raise-boundary trio the
  cluster/weight pair already has (`test_an_arm_varying_within_a_units_rows_is_reported`,
  `test_agreeing_arm_rows_are_not_reported`,
  `test_validate_reports_rather_than_raising_on_a_varying_arm`).
- `docs/reference.md`: `E-DATA-ASSIGN-VARIES` dual-listed in § Errors `validate`
  reports (alphabetical slot, `ASSIGN-UNKNOWN` < `ASSIGN-VARIES` <
  `CLUSTER-CONTRAST`) and § Errors core raises (added to the existing
  `ContractError` row alongside `CLUSTER-VARIES`/`WEIGHT-VARIES`), plus a new
  narrative paragraph in § Allocation stating the rule directly (the pattern
  § Clustered units and § Weighted samples already use). § Validation's
  pre-existing *Arm is constant within a unit* row needed no edit — checked,
  and it already states exactly what got implemented.

## Step 2, recorded literally

Added `"assign": (...)` to `CONSTANT_COLUMN_RULES` with no accessor wired in
(`constant.update(_assign_constant_columns(...))` line absent). Ran
`test_an_arm_varying_within_a_units_measurement_rows_is_refused` and
`test_an_arm_constant_within_a_units_rows_is_accepted`: both still passed the
"raises" test as a **failure** —

```
FAILED tests/test_units.py::test_an_arm_varying_within_a_units_measurement_rows_is_refused
Failed: DID NOT RAISE ContractError
```

— because `isinstance(units_decl.get("assign"), str)` is `False` for a mapping,
so the flat comprehension never reaches it. Confirmed by re-running after
reverting (not by `git status`).

## Mutation testing (apply → run named test → confirm FAIL → revert → confirm PASS, `__pycache__` cleared each time)

- Dropping `constant.update(_assign_constant_columns(...))` — kills the
  refusal test only (`DID NOT RAISE`); the control still passes.
- `CONSTANT_COLUMN_RULES[declaration]` instead of
  `CONSTANT_COLUMN_RULES[declaration.partition(".")[0]]` — kills exactly the
  three tests that exercise `assign` through `constant` (`KeyError:
  'assign.arm.from'`); the pre-existing cluster/weight tests are unaffected.
- Removing the `method == "by_attribute"` gate in `_assign_constant_columns`
  (added on review, see below) — kills exactly
  `test_a_varying_arm_under_a_drawn_method_is_not_checked`; nothing else.
- Dropping the axis-name default (`resolved_from = axis` → `None` when
  `declared_from is None`) — kills the refusal/reported pair plus the
  non-cluster-column test; the control tests still "pass" but for the wrong
  reason (no column resolves, so nothing is checked) — recorded as expected
  rather than treated as a clean revert signal.

## A gap the brief didn't ask about, closed on review

Before committing, I checked `_assign_constant_columns` against
`_check_assign`'s own semantics rather than treating the brief as complete.
`_check_assign` reads `from`/`levels` only inside the `method: by_attribute`
branch — its own docstring says they "mean nothing under `random`/`blocked`".
My first draft read `from` unconditionally. Consequence: an in-development
`assign: {arm: {method: random}}` block, over a table whose `arm` column
happens to vary within a unit's replicate rows, would have raised
`E-DATA-ASSIGN-VARIES` naming a `.from` path the config never wrote (resolved
by a default that doesn't apply under `random`), over a column nothing under
that method reads — a config no check has approved yet, refused anyway by a
rule that assumed `by_attribute`. Fixed by gating on `method ==
"by_attribute"`; loses no real coverage, since `random`/`blocked` and any
out-of-enum method are refused at `validate` as `E-DATA-ASSIGN-DRAWN`/
`E-DATA-ASSIGN-METHOD` before a run would ever reach them. Added
`test_a_varying_arm_under_a_drawn_method_is_not_checked` and a docstring
paragraph explaining the gate.

## A brief claim that does not hold as written

The Controller additions' mutation paragraph says: "one column named as *both*
the arm attribute and `cluster_by` **should** draw both codes." Checked by
observation rather than trusted: `collapse_measurements` raises the first
`ContractError` its `constant` loop finds and stops (it's a raise, not a
`Collector`), so a single config declaring `cluster_by: arm` *and* `assign:
{arm: {method: by_attribute}}` over varying rows gets exactly **one** code —
`E-DATA-CLUSTER-VARIES` — from one `resolve_units` call, because `constant`
gathers the flat declarations before `_assign_constant_columns`'s axis entries.
`validate`'s `except ContractError` around `resolve_units` converts that one
raise into one finding, so the same is true at that surface too.

What's true, and is presumably what the brief's citation of
`CONSTANT_COLUMN_RULES`'s "checked once for each ... rather than silently
dropping one under a precedence rule" actually supports: each declaration,
checked **on its own** (a config naming only `cluster_by`, or only `assign`),
still raises its own code over the same varying column — neither is skipped
*because* the other also names it. I did not build "mutual exclusion" (the
literal instruction), and there is no code change needed to satisfy the
literal-false reading, since it isn't achievable without rewriting the
constancy loop to collect rather than raise (out of scope, not requested).
Closed by rewording `CONSTANT_COLUMN_RULES`'s docstring to state both the true
and the false halves explicitly, and by adding
`test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`
(observes the single-code behavior) alongside
`test_the_three_codes_are_not_one_code_and_none_excludes_another` (the
three-separate-calls version of the true claim). Recorded in
`docs/superpowers/spec-defects.md` (gitignored, not part of the commit).

The brief's other open item — "the registry's shape... pick one and say in
the docstring why the other was rejected" — is settled: the "expand to one
entry per axis" alternative isn't implementable as literally stated, since the
registry is a module-level dict and the axes are declared per-config, not
known when `units.py` is imported. Kept the single `"assign"` entry with a
stripping lookup; the docstring says so.

## Review round 2: six fixes

**Status:** DONE
**Commit:** `cbd4420` — fix(units): six review fixes for the assign-varies constancy check

### Test summary

`uv run pytest`: 1452 passed, 2 xfailed (pre-existing). `uv run ruff check .`: clean.
`uv run mypy`: clean, 40 source files. Mutation testing for the reordering change
(apply → run named test → confirm FAIL → revert → confirm PASS, `__pycache__`
cleared each time): swapping `constant`'s build order back to flat-first killed
exactly `test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`
(now asserts `E-DATA-ASSIGN-VARIES`, so flat-first makes it observe
`E-DATA-CLUSTER-VARIES` instead) and nothing else; reverted and reran the four
ordering/severity tests plus the full suite to confirm the revert by behaviour.

### What changed, addressing each point

1. **Important 1.** `docs/reference.md`'s new `E-DATA-ASSIGN-VARIES` row ended
   "each is checked on its own, exactly as `cluster_by` and `weight_by` naming
   the same column both would be" — false read plainly, and the same overclaim
   I had already rewritten out of `CONSTANT_COLUMN_RULES`'s docstring but left
   standing in the normative doc. Reworded to state both halves: each
   declaration checked independently still raises on its own, and a single
   unit violating more than one gets exactly one code (from whichever
   declaration is checked first).
2. **Important 2.** The `method: by_attribute` gate was correct but reached no
   document. Added `Under `method: by_attribute`,` to three spots: § Validation's
   *Arm is constant within a unit* row (my report's earlier claim that this row
   "needed no edit" was itself the thing to correct — it needed exactly this),
   the `E-DATA-ASSIGN-VARIES` row in § Errors `validate` reports, and the new
   § Allocation paragraph — matching the sibling rows' own opening clause.
3. **Important 3.** My constancy paragraph, inserted between the `ratio`
   paragraph and the `blocked` paragraph, put "the refusal above lifts" (the
   `blocked` paragraph's closing clause, meaning `E-DATA-ASSIGN-DRAWN`) one
   paragraph further from its antecedent, with my own paragraph now the
   nearest "above" — a positional reference falsified by an insertion that
   moved it, the exact defect class task 9/10 hit. Fixed both ways: moved my
   paragraph after `blocked`'s, and reworded the `blocked` paragraph to name
   `E-DATA-ASSIGN-DRAWN` explicitly rather than "above", so a future insertion
   between them can't repeat this.
4. **Minor 4.** Reordered `resolve_units` so `_assign_constant_columns`'s
   entries are built into `constant` before the flat `cluster_by`/`weight_by`
   comprehension — one unit that violates two declarations at once now raises
   the code the docs already called worst (`assign`) rather than whichever the
   dict happened to build first (`cluster_by`, by accident of insertion order).
   Documented the resulting precedence explicitly in both
   `CONSTANT_COLUMN_RULES`'s docstring and the `E-DATA-ASSIGN-VARIES` table row,
   closing the "precedence rule nothing in the documents states" gap the
   registry's own docstring warns against, rather than leaving it merely
   described.
5. **Minor 5.** `CONSTANT_COLUMN_RULES`'s docstring said "whichever
   declaration's entry `constant` visits first, `cluster_by` today" without
   the qualifier that this only gets tested on a unit violating both at once.
   Reworded to state that explicitly, updated for the new ordering (`assign`
   now wins), and added
   `test_roster_order_not_severity_decides_when_different_units_violate_different_declarations`
   — two units, each violating a different declaration, roster order (not
   declaration severity) decides which one is ever reported, because
   `collapse_measurements`'s outer loop is per unit and stops at its first raise.
6. **Minor 6.** Added a sentence to `CONSTANT_COLUMN_RULES`'s docstring: a
   registry key must contain no `.`, or `collapse_measurements`'s
   `declaration.partition(".")[0]` lookup could strip a future dotted key to a
   prefix the registry doesn't hold, raising a bare `KeyError` that escapes
   `validate`'s `except ContractError` boundary — the same escape-from-`validate`
   failure class this module's other comments guard against.

Also updated `test_one_column_named_by_both_cluster_and_arm_reports_exactly_one_code`
for the new ordering (`E-DATA-ASSIGN-VARIES` rather than `E-DATA-CLUSTER-VARIES`)
and its docstring to explain why, and confirmed by direct probe that
`assign: {arm: {}}` (no `method` at all) over varying rows still raises nothing —
matching the now-corrected docs rather than the code needing to change.

Not addressed, per the coordinator's note: `test_agreeing_arm_rows_are_not_reported`
stays absence-only; it is paired with a reporting test that does die to the
accessor-deletion mutation, and the strong positive control lives in
`tests/test_units.py`.

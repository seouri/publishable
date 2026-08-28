## Task 6+7 report

Status: complete.

Implemented `W-SWEEP-CONDITION-DUPLICATE` in `src/publishable/validate.py`
(`_warn_duplicate_conditions`, called from `_check_sweep`), over `expand`'s output via
`contrasts.differing_axes`, gated on neither condition carrying a `Condition.selectors`
(group axis) — since equal `values` implies equal units only for a parameter path, not
a `groups` level (assignment-method-dependent). Message reuses the working-spelling
remedy `W-SWEEP-BASELINE-CONFOUNDED` already emits, joined by semicolon (same
containment, not a fresh sentence). Added the row to `docs/reference.md` § Warnings
core reports, alphabetically after `W-SWEEP-BASELINE-CONFOUNDED`.

Mutation evidence (each: backed up file, mutated, ran red, restored from backup,
confirmed byte-identical + green):
- Removed selectors guard → `test_a_group_axis_duplicate_level_is_not_this_warning` and
  `test_a_baseline_fixing_a_group_level_is_not_this_warning_either` both failed (red),
  passed after restore.
- Inverted `differing_axes` polarity → `test_a_baseline_colliding_with_its_own_grid_cell_warns_once`,
  `test_a_normal_baseline_plus_grid_config_has_no_duplicate_condition`,
  `test_a_repeated_grid_value_is_the_soft_case_this_warning_reaches` all failed, passed after restore.
- Removed the early `return` (report-once) → `test_a_baseline_colliding_with_its_own_grid_cell_warns_once`
  failed on the pair-(0,2)-vs-(1,3) assertion (dict overwrite showed the later pair), passed after restore.

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all pass; full
`tests/test_validate.py` (800 tests) passes.

Concern: the measured example in the brief (baseline+grid, no groups) is the only
shape Decision 3 discusses explicitly; the group-axis exclusion (task 8's own
requirement) was derived from `E-SWEEP-LEVEL-DUPLICATE`'s giant comment about
assignment-method-dependent unit collision, not stated directly in Decision 3 — worth
a second look by task 8's author.

## Fix round 1

Finding 1 (critical, over-broad exclusion): fixed. Verified `cli._resolved_group_axes`
calls `units.assignment_for` exactly once per declared axis over its whole `levels`
list, so every condition naming a given level reads the same `ArmPlan.members[level]`
— identical `values` means identical units unconditionally, including across a group
axis; my "no group axis at all" guard and its assignment-method-uncertainty rationale
were both wrong, in both the `validate.py` docstring and the `reference.md` row.
Replaced with `_group_axes_already_erred`, which excludes a pair only when every group
axis it shares is exactly `E-SWEEP-LEVEL-DUPLICATE`'s trigger (the axis's own repeated
level string) or `E-SWEEP-BASELINE-GROUP`'s (an axis `sweep.baseline` fixes) — read
from the raw `sweep` declaration, not re-derived from `expand`'s output. Both
reviewer-measured false negatives now fire: `groups(control,treatment) x
grid(pearson,pearson)` and `baseline(analysis.method) + groups + grid(pearson,pearson)`.

Finding 2 (test docstrings claiming false guarantees): fixed. Rewrote both docstrings
to state the measured fact (the pair DOES resolve to the same `values`, and `validate`
DOES reach this check for it) and the real reason for silence (already `E-SWEEP-LEVEL-
DUPLICATE`'s/`E-SWEEP-BASELINE-GROUP`'s own trigger, not unreachability).

Finding 3 (mutation set didn't cover the guard's breadth): added
`test_a_group_axis_duplicate_that_is_not_the_sharp_codes_own_shape_still_warns` and
`test_a_baseline_and_group_axis_together_still_report_the_unrelated_grid_duplicate`.
Mutation: widened the exclusion back to "any shared group axis at all" (the exact bug)
— both new tests failed red; reverted from a pre-mutation backup, confirmed
byte-identical, both green.

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all pass;
`tests/test_validate.py` (802 tests) passes.

## Fix round 2

Finding 1, still open after round 1: fixed. The axis/level-scoped exclusion still
excused every pair merely touching an already-erred axis, not just the specific pair
each sharp code names. Rebuilt `_group_axes_already_erred`/`_warn_duplicate_conditions`
to a pair-scoped predicate: the baseline shape now requires the SAME fixed axis, the
SAME fixed value, AND exactly one side `is_baseline` (not "any pair sharing the axis");
the level-duplicate shape is now gated OFF entirely whenever any `sweep.grid` axis
independently repeats a value, because `expand`'s output cannot disambiguate which
duplicate pair came from the repeated level vs. the repeated grid value in that case —
over-reporting (a pair also named by `E-SWEEP-LEVEL-DUPLICATE`) is accepted since the
direction that matters is never suppressing a true positive.

Measured, as requested:
- **F** (`baseline:{arm:control}` + `groups[control,treatment]` + `grid[pearson,pearson]`):
  6 conditions; pairs (0,1) and (4,5) are pure grid repeats, (0,2)/(0,3)/(1,2)/(1,3) are the
  real baseline-vs-product-row collisions `E-SWEEP-BASELINE-GROUP` already names, (2,3) is a
  third, unrelated pure-grid repeat on the `control` product row. New code fires on (0,1) —
  confirmed via direct `_warn_duplicate_conditions` call.
- **J** (`groups[c,c]` + `grid[pearson,pearson]`): all 4 conditions collapse to identical
  `values`; `duplicated_levels` is empty (grid repeats), so every pair is live and the check
  fires on (0,1) — confirmed directly.
- **Ablate + baseline-fixes-group-axis, no parameter axis** (`ablate: {override:[...]}`,
  `baseline:{arm:control}`, `groups[control,treatment]`): `expand` renders only 2 conditions
  (crossed branch suppresses the bare product row entirely) — zero duplicate pairs, so no
  exclusion is ever exercised here regardless of which code names it.
- **Ablate + baseline-fixes-group-axis + a grid axis** (the `E-SWEEP-ABLATE-CROSSED`-refused
  shape, `validate` collects rather than aborting so `expand` still runs): DOES render
  baseline-vs-product duplicate pairs, and the sharp code that fires is
  `E-SWEEP-ABLATE-BASELINE-GROUP`, not `E-SWEEP-BASELINE-GROUP` — confirmed via `expand` +
  reading `_check_sweep`'s branch. `baseline_fixed_axis` is unconditional on `ablate` (both
  codes report the identical `fixed_levels[0]` fact, just under different names depending on
  `ablate`), and `reference.md`/the docstring now name both codes rather than only one.
- **`fixed_levels[0]` only**: confirmed `E-SWEEP-BASELINE-GROUP`/`E-SWEEP-ABLATE-BASELINE-GROUP`
  both index `fixed_levels[0]` in their message; `baseline_fixed_axis` is now a single name,
  not the former `baseline_fixed_axes` set, so a second `sweep.baseline`-fixed axis (never
  reported by either sharp code) is no longer excused either.

Fixed the ride-along docstring in
`test_a_group_axis_duplicate_that_is_not_the_sharp_codes_own_shape_still_warns`
("this checks the first" implied more than one finding is emitted) to state the measured
fact — exactly one `W-SWEEP-CONDITION-DUPLICATE` finding, pinned with an explicit count
assertion over the raw `Collector`, not just `messages_by_code`'s last-wins dict.

Added `test_baseline_fixing_a_group_level_beside_a_repeated_grid_value_still_fires_on_the_grid_pair`
(F) and `test_a_repeated_group_level_beside_a_repeated_grid_value_still_fires_on_the_grid_pair`
(J). Mutation: reverted `_already_erred` to `return True` (any shared group axis excuses the
pair — round 1's bug) — both new tests failed red; restored from a pre-mutation backup,
confirmed byte-identical, both green again.

`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all pass;
`tests/test_validate.py` (804 tests) passes.

## Fix round 3 (prose only, no predicate change)

Ruling 1 (X1/P1 parked): both require `groups: [{by: arm, levels: [c, c]}]`, which
`E-SWEEP-LEVEL-DUPLICATE` refuses per-entry independent of `grid`/`baseline`
(confirmed by reading the check at `validate.py`, the `seen`/`level in seen` loop
reads only `entry["levels"]`) — such a config does not run, so no code change made.

Ruling 2 sweep: pattern was "the claim that the exclusion covers only the pair
another code already reports" — swept for its recurring phrasings (`already report`,
`already covers?`, `already gated`, `no ambiguity`, `cannot say which`, `cannot
disambiguate`, `known gap, recorded`, `the exact pair \`E-SWEEP-LEVEL-DUPLICATE\``)
with whitespace normalized first (`re.sub(r"\s+", " ", text)`) so a wrapped instance
can't hide, across `validate.py`, `reference.md`, `tests/test_validate.py`. Proof the
sweep can find something present: it also matched unrelated true positives (e.g.
"already reported by `_check_data`", "cannot say which run produced it") before I
filtered to the six homes that were actually about this claim, showing the patterns
are not vacuous.

Six homes found and fixed (one more than the three the round-3 brief named):
1. `docs/reference.md` row 408 — "gated that way because... cannot say" rewritten to
   state the exclusion excuses more than `E-SWEEP-LEVEL-DUPLICATE`'s own pair, and
   every extra pair sits in a config that code already refuses.
2. `docs/reference.md` row 636 (`E-SWEEP-LEVEL-DUPLICATE`) — "parameter-axis duplicate
   is a known gap, recorded here rather than closed" was stale for its own worked
   example (`groups[control,treatment] × grid[pearson,pearson]`, closed since round 2);
   rewritten to say closed bare and crossed-with-distinct-levels, open only when the
   group axis's own level also repeats (moot, since that's already refused).
3. `_group_axes_already_erred`'s `duplicated_levels` docstring — "expand's output
   alone cannot say" rewritten to the "excuses more, but only inside an already-
   refused config" framing.
4. `_warn_duplicate_conditions`'s docstring ("What IS grounds to skip" paragraph and
   the level-duplicate bullet) — same rewrite, plus corrected "already gated to
   declarations with no ambiguity, above" (false: nothing above gates on ambiguity).
5. The inline `continue` comment before the `c.warn` call — corrected from "the exact
   pair ... already reports" to name that only the baseline branch is exact.
6. `validate.py`'s `E-SWEEP-LEVEL-DUPLICATE` comment (~line 4790, "known gap, recorded
   on this code's row") — same staleness as home 2, fixed in the code comment too.
   (Not in the brief's three, found by the sweep.)
7. `tests/test_validate.py`'s Finding-J test docstring — same "cannot say which"
   framing, corrected to name the config as already-refused.

No predicate change; no new tests (existing tests' assertions were unaffected, only
docstrings). `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all
pass; `tests/test_validate.py` (804 tests) passes.

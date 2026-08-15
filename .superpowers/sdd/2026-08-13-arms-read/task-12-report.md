# Task 12 report — the arm is a subset view of the one roster

## Status: DONE (post-review fixes applied — see § Review response below)

## What was implemented

**`src/publishable/runner.py`** — `execute_plan` gained an `arm_members: dict[int,
frozenset[str]] | None` parameter. Inside the per-execution loop, a new narrowing
step runs *before* the existing fold branch: for any execution whose
`condition_index is not None` (condition and repeat scope), the roster is filtered
to `arm_members[condition_index]` — a plain list-comprehension filter over the
existing `Unit` objects, never a re-resolution — before the fold branch reads
`units` to compute `handed`/`.train`. `run`/`summary` scope are untouched (their
`condition_index` is always `None`), so they keep the whole roster. A new helper
`_arm_keys` mirrors `_handed_keys` but **indexes** `arm_members` rather than
`.get`-ing it, raising `ContractError · E-RUN-ARM-UNRESOLVED` on a missing
condition index — the same treatment `E-RUN-CFG-MISSING` gets for the analogous
plan/cfgs disagreement, and deliberately outside the per-execution `try` so it
stops the run rather than being absorbed as one execution's failure.
`_units_failed_anywhere` (the `max_failed_fraction` union) was also made
arm-aware, using the same `_arm_keys` narrowing before `_handed_keys`, so a unit
of the other arm is never blamed for failing to settle in an execution it was
never handed to.

**`src/publishable/units.py`** — added `arm_members(roster, axes, conditions)`,
which calls `arms_of` (task 10's single authority) exactly once per declared
group axis and reduces the result across each condition's `.selectors`/`.values`
(intersecting when a condition selects more than one axis — the `sex × arm`
cell). A condition selecting no axis is absent from the result, never mapped to
the whole roster.

**`src/publishable/validate.py`** — `_check_assign` now implements *Arms need
allocation*, the mirror of *Allocation needs arms*: `sweep.groups` declares an
axis but `allocation` is `within` or absent, reported as the new
`E-DATA-ALLOCATION-WITHIN-ARMS`, gated explicitly on `allocation in (None,
"within")` (not a bare `elif axes:`) so an out-of-enum `allocation` value isn't
misreported as `within`. Docstring updated from "six" to "seven" rows and the
stale "reported by nothing in this build" language removed.

**`src/publishable/cli.py`** — added `_resolved_group_axes(units_decl,
sweep_block)`, which resolves each declared group axis to
`(assign.<axis>.from-or-default, declared levels)` the same way
`validate._check_assign`'s `by_attribute` branch does (including the
`method == "by_attribute"` gate — `from` means nothing under `random`/`blocked`).
`command_run` now builds `arm_members_map` from it and `units.arm_members`, and
passes it to `execute_plan`. This wiring is unreachable end-to-end today: a
declared `sweep.groups` axis still draws `E-SWEEP-GROUPS-UNSUPPORTED`, an error
that returns `EXIT_WRONG` before this line — task 17 retires that blanket
refusal. Comments say so at the call site, matching the existing convention at
`cli.py`'s `_wide_swept_paths`.

**`docs/reference.md`** — new row for `E-DATA-ALLOCATION-WITHIN-ARMS`, inserted
alphabetically between `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ASSIGN-DRAWN`; the
`E-DATA-ASSIGN-MISSING` row's stale "reported by nothing" language now names the
new code; `E-RUN-ARM-UNRESOLVED` added to § Errors core raises' "plan disagreeing
with resolved state" row, beside its five siblings (`E-RUN-SEED-MISSING` etc.),
with the row's prose ("those five/six", "conditions, repeats, seeds, folds, and
order") updated to count six.

## Tests

- `tests/test_runner.py`: `harness()` extended with an `arm_members` parameter
  (and its `cfgs` dict now builds one `Config` per declared condition index, not
  a hardcoded `{0, -1}` — needed for any multi-condition test). Six new tests:
  the brief's own `test_two_arms_get_different_rosters_and_neither_is_the_whole_roster`
  (12 units, 7/5, asserts sizes `{7, 5}` with `12 not in sizes`, `units_hash`
  unchanged, **and** object identity — `any(u is r for r in roster)` — which is
  the assertion that actually discriminates re-resolution); the addendum's
  discriminating pair — `run`/`summary` scope keep 12 while `condition`/`repeat`
  narrow; the `groups` + `fold` composition test with `.train` asserted to hold
  only the condition's own arm; the missing-arm-entry raise; and a direct
  `_units_failed_anywhere` arm-awareness test.
- `tests/test_units.py`: three tests for `arm_members` — the reduction itself,
  that `arms_of` is called once per axis (not per condition, via a mock spy),
  and the two-axis intersection case.
- `tests/test_cli.py`: three tests for `_resolved_group_axes` — default
  resolution, empty on no `groups`, and the `by_attribute`-only gate.
- `tests/test_validate.py`: rewrote `test_allocation_within_leaves_both_
  cross_field_rows_silent` (renamed `test_within_allocation_with_a_group_axis_
  is_arms_need_allocation`, now asserting the code fires) and added
  `test_between_allocation_with_a_group_axis_draws_neither_arms_row` as the
  explicit control the brief demands. Updated 9 other pre-existing tests whose
  fixtures declared `sweep.groups` with no `allocation` (implicitly `within`)
  to include `E-DATA-ALLOCATION-WITHIN-ARMS` in their expected finding sets, and
  added `"allocation": "between"` to four direct `_check_assign` fixtures that
  test the by_attribute levels-check in isolation, keeping their original
  assertions intact rather than diluting them with an unrelated code.

**Mutation testing performed** (`__pycache__` deleted between apply/revert,
reverts verified by re-running tests, not `git status`):
1. Disabling arm narrowing entirely → kills the size assertion (`{12}` instead
   of `{7, 5}`). Confirmed FAIL, reverted, confirmed PASS.
2. Re-resolving fresh `Unit` objects instead of filtering the roster's own →
   **does not** fail `units_hash` (equal keys/attributes hash identically,
   `Unit.__eq__` is by key) but **does** fail the identity assertion. Confirmed
   FAIL (identity only), reverted, confirmed PASS. See finding below.
3. Applying the arm filter to the *result* of the fold branch rather than
   before it (leaving `.train`'s complement computed against the unnarrowed
   roster) → kills `train_keys <= arm_keys` with the other arm's units
   concretely present in the diff. Confirmed FAIL on that specific assertion,
   reverted, confirmed PASS.
4. Removing the new `E-DATA-ALLOCATION-WITHIN-ARMS` check in `validate.py` →
   kills `test_within_allocation_with_a_group_axis_is_arms_need_allocation`.
   Confirmed FAIL, reverted, confirmed PASS.

Full suite: `uv run pytest` → 1464 passed, 2 xfailed. `uv run ruff check .` →
all checks passed. `uv run mypy` → no issues in 40 source files.

## Findings — requirements that were wrong or needed correction

1. **Brief defect, empirically confirmed (step 2's assertion doesn't discriminate
   step 5's second mutation).** The brief says: "`units_hash` over the full
   roster is unchanged — assert it" as the check for the re-resolution mutation.
   It does not discriminate: a re-resolution that builds fresh `Unit` objects
   with the same `key`/`paths`/`attributes` hashes identically under
   `units.units_hash` (which serializes exactly those three fields), and
   `Unit.__eq__` is by key alone. I ran the mutation and confirmed empirically
   that `units_hash` stays equal while the object-identity check
   (`any(u is r for r in roster)`) fails. I kept the `units_hash` assertion (it's
   still a legitimate invariant to check) but added the identity assertion as
   the one that actually earns its place for this mutation. This matches the
   addendum's own framing ("an arm is a view, never a re-resolution") more
   precisely than the brief's proposed check.

2. **File-list scope gap in the brief.** The brief's header lists `cli.py`,
   `units.py` as files to modify and `tests/test_cli.py` as the test file. The
   actual mechanism — narrowing before the fold branch inside `execute_plan`,
   and the arm-aware `max_failed_fraction` union — necessarily lives in
   `runner.py`, and *Arms need allocation* necessarily lives in `validate.py`
   beside its mirror (`E-DATA-ALLOCATION-NO-ARMS`), both stated explicitly and
   correctly by the addendum ("has equal force"). I edited both files. I also
   put the acceptance-bar tests (two-arms-different-rosters, the run/summary
   control, the fold composition, the missing-arm raise) in `tests/test_runner.py`
   rather than `test_cli.py`: that file already has the exact harness this
   feature composes with (`fold_members`, multi-scope steps), and duplicating
   it in `test_cli.py` would have meant either a second harness or testing
   through the still-refused `command_run` end-to-end path, which cannot reach
   this code at all in this build. `test_cli.py` got the tests for what
   actually is `cli.py`'s own piece: `_resolved_group_axes`.

3. **Deliberate hand-off, not a defect.** `runner.attrition` (the per-condition,
   per-step `n` that becomes `run.yaml`'s `resolved`/`completed`/`ineligible`/
   `failed`) was left arm-unaware, per the brief's "Task 13 owns the counts
   themselves; do not implement them here." Its `roster` parameter is the seam:
   it still receives the whole roster and is not yet told which arm a condition
   belongs to, so its `resolved` figure for an arm-scoped condition is currently
   the *whole* roster's size rather than that arm's — a fact task 13 will need
   to address, not a path this task closed off. I did make the closely-related
   run-level `max_failed_fraction` check (`_units_failed_anywhere`, inside
   `execute_plan` itself, not `attrition`) arm-aware, since leaving it
   arm-blind would have made `execute_plan` — code this task does own — abort
   runs on a threshold miscounting units the design never handed to a given
   condition.

4. **Documentation gap the addendum didn't flag.** `E-RUN-ARM-UNRESOLVED` is a
   new raise-time identifier with no natural home mentioned in either brief or
   addendum. I found its siblings (`E-RUN-CFG-MISSING`, `E-RUN-FOLD-UNRESOLVED`,
   `E-RUN-ORDER-MISMATCH`, etc.) already grouped in one row of `reference.md`
   § Errors core raises ("core's execution plan disagreeing with the state core
   resolved beside it") and added `E-RUN-ARM-UNRESOLVED` there, updating the
   row's prose count from five to six.

## Naming decision

`E-DATA-ALLOCATION-WITHIN-ARMS` was not specified by either brief or addendum
(both left it open, saying only "read it and put yours beside it" /
"name the mirror in the message"). Chosen to parallel `E-DATA-ALLOCATION-NO-ARMS`
structurally (states the allocation value plus the arms fact) and to sort
correctly beside it in the alphabetically-ordered table.

## Commit

`923c1a5e6ad1d20260a05678b2282f883d25b9ae`

## Review response

The coordinator's review found two Criticals and several lesser issues. All are
addressed; changes are additive on top of the original commit, not a rewrite.

**Critical 1 (two derivations of "which group axes exist" disagree, silently) —
fixed.** `sweep.selector_paths`/`expand` accept a `levels` list of any element
type; `cli._resolved_group_axes` requires every level to be a `str` (mirroring
`validate._check_assign`'s own stricter skip). `command_run`'s gate now reads
`if selector_paths(sweep_block) and roster is not None`, not
`if group_axes and roster is not None` — so a config where `expand` agrees an
axis exists but `_resolved_group_axes` couldn't resolve it still calls
`units.arm_members`, which now raises (see Critical 2) instead of the call
being skipped outright. Reproduced the reviewer's exact scenario
(`groups: [{by: arm, levels: [1, 2]}]`) in
`tests/test_cli.py::test_non_string_levels_make_arm_members_raise_rather_than_skip_narrowing`
— confirmed the old gate produced `arm_members_map = None` (no narrowing, both
conditions get the whole roster) and the new gate + fixed `arm_members` raises
`KeyError` instead.

**Critical 2 (`units.arm_members`'s docstring claims a guarantee the code
didn't provide) — fixed.** The function's `selected = [axis for axis in
condition.selectors if axis in partitions]; if not selected: continue` silently
dropped a selected-but-unresolved axis from the intersection (widening the arm)
or the whole condition from the result (handing its execution the whole roster
one level up) rather than raising. Rewrote to index `partitions[axis]` and
`partitions[axis][level]` directly with no `.get`/filter — a selected axis or
level absent from `axes` now raises a bare `KeyError`, exactly what the
docstring already claimed. A condition selecting *no* axis at all is still
correctly absent from the result (that's a different, legitimate case: no arm
declared for it). No `spec-defects.md` entry needed for this half — it's a code
fix restoring the stated contract, not a spec/code divergence being recorded.

**Important 4 (the control test couldn't fail) — fixed.**
`test_between_allocation_with_a_group_axis_draws_neither_arms_row` now asserts
exact sets on both halves (`== []` for the direct `_check_assign` call, the
real `{E-SWEEP-GROUPS-UNSUPPORTED, E-DATA-ALLOCATION-UNSUPPORTED,
E-DATA-ASSIGN-UNSUPPORTED}` for `write_config` — not the reviewer's suggested
set verbatim, which omitted that the original fixture had no
`data.units.attributes` declared for `arm` and so also drew
`E-DATA-ASSIGN-UNKNOWN`; fixed the fixture to declare `attributes: ["arm"]`
plus a real `arm` column in `write_config`'s `index.csv`, matching
`test_by_attribute_assignment_is_accepted`'s pattern, so the config is
genuinely clean rather than merely under-specified) and added the positive
sibling probe the reviewer asked for (the same declaration pair under
`allocation: within` instead, asserted to still report). Mutation-tested by
inserting `return` at the top of `_check_assign`: the sibling probe now fails
(`assert [] == ["E-DATA-ALLOCATION-WITHIN-ARMS"]`), where before the fix the
test passed unconditionally. Reverted, confirmed pass, `__pycache__` cleared
between.

**Important 5 (record, don't fix) — recorded, not touched.** `runner.attrition`
stays arm-blind, per the original brief's "Task 13 owns the counts." For task
13's brief: `docs/reference.md` § **What isn't a repeat** (the paragraph
beginning "`resolved` counts what the execution was handed, not the cohort")
already states, in prose, "Under a group axis it's that arm's roster, ~120
rather than 240" — but `attrition` (called once per condition per recording
step in `cli.command_run`) still computes `keys = {u.key for u in roster}` over
the *whole* resolved roster regardless of which arm the condition belongs to,
so for a two-arm 240-unit design it will report `resolved: 240` for both
conditions and count the *other* arm's ~120 units as `failed` (since they were
never recorded or skipped by that condition's executions) — the exact
120-vs-240 example the prose already promises is not what the code does yet.
`attrition`'s `roster` parameter is the natural seam: task 13 needs to thread
the same `arm_members`/`_arm_keys` narrowing this task built into
`execute_plan` through to `attrition`'s notion of "the cohort this condition
was run over," the same way `fold_members` already narrows it for a fold.

**Minor 6 (the row's own gate creates a future gap) — marked and recorded.**
Added "**Temporary in that one respect**" to the `E-DATA-ALLOCATION-WITHIN-ARMS`
row, stating that once `E-DATA-ALLOCATION-UNSUPPORTED` retires, an out-of-enum
`allocation` beside a declared group axis will draw neither this row nor any
other. Recorded as a new open entry in `docs/superpowers/spec-defects.md`
("An out-of-enum `allocation` beside a declared group axis will be checked by
nothing once `E-DATA-ALLOCATION-UNSUPPORTED` retires"), with a proposed
resolution (an enum-shape check on `data.units.allocation`, `E-DATA-ALLOCATION-METHOD`
or similar, checked before either arms row) for whichever slice retires the
blanket refusal.

**Minor 7 (unused fixture param; shared partition undiscriminated) — fixed.**
Dropped the unused `tmp_path` parameter from
`test_units_failed_anywhere_does_not_blame_the_other_arm`. Its docstring now
names the fold test in the same file that reuses the identical 2/2 `_roster4`
partition and states explicitly why the reuse is harmless (`fold_members=None`
throughout, so nothing in this test ever reads that partition as a fold's).

## Re-verification after review fixes

`uv run pytest` → 1465 passed, 2 xfailed. `uv run ruff check .` → all checks
passed. `uv run mypy` → no issues in 40 source files. Additional mutations
applied/killed/reverted (`__pycache__` cleared between, reverts verified by
re-running tests): removing `_check_assign`'s new branch entirely (kills the
sibling probe in the rewritten control test); the reviewer's exact
non-string-levels scenario (confirms the old gate silently produced no
narrowing, the new gate + fixed `arm_members` raises).

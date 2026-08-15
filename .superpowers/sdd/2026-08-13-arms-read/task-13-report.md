# Task 13 report — `n` reconciles per arm

## Status: DONE

## What changed

`command_run`'s per-condition, per-step loop (`src/publishable/cli.py`) called
`attrition(results, roster, ...)` — the **whole** roster — for every condition,
including one on a group axis. That is the site the addendum named: under
`allocation: between` an execution only ever receives its own arm, so
`attrition`'s claim that "without a fold that is the full roster, since every
execution receives it whole" stopped being true the moment a group axis
existed, and the call site never caught up. Confirmed with the number the
addendum asked for, not the reasoning: over the 7/5 fixture, the old call
reported `resolved: 12` for BOTH conditions and derived the other arm's units
as `failed` (`5` for the control condition, `7` for the treatment one).

Fixed by adding `_cond_roster(roster, cond_index, arm_members_map)` in
`cli.py` — the read-side counterpart of the narrowing `execute_plan` already
applies to what a condition's own executions *run over* (`runner._arm_keys`,
reused rather than re-derived, per correction #3). Three call sites now use
its answer instead of the bare `roster`:

1. The main `attrition(...)` call in the per-condition loop.
2. `report_by`'s per-level loop, which had the **same** defect one level
   down (correction #4): `levels_for(roster, attribute)` let a level whose
   values repeat across both arms hand `attrition` units the other arm's
   executions never touched. Extracted into `_report_by_levels(roster,
   attribute)` so the narrowing is a pure function of one roster parameter,
   called as `_report_by_levels(cond_roster, attribute)`.
3. `technical_n`, withheld from `beside_n` under an arm (correction #5),
   via a new `_cond_beside_n(beside_n, cond_roster, roster)`, following the
   precedent `report_by`'s own level block already set (it withholds
   `technical_n` for the same reason — it's a whole-roster figure — passing
   `weighted_beside` instead of `beside_n`).

`runner.attrition`'s docstring is updated in the same commit: it no longer
states "the full roster" as an unconditional fact about `resolved`, it names
`roster` as whatever the caller resolved — arm or whole — and that
`attrition` does not re-derive that narrowing itself.

No change was needed in `reference.md` or `experimental-designs.md`. § What
isn't a repeat already says "Under a group axis it's that arm's roster, ~120
rather than 240" and "Under a group axis it doesn't reconcile, and shouldn't
— each arm's interval is over that arm's units"; `experimental-designs.md`'s
*Silent attrition* row already says "a fold or an arm isn't charged with
units it never saw." The prose was already right; this task is the code
catching up to it, which is itself the acceptance check the addendum named.

## The two assertions (corrected per the addendum's own corrections section)

Over the reused 7/5 fixture (`_arm_roster12`/`_arm_members12`, task 12's), with
`c0` `io.skip`-ped in `control` and `t0` left unsettled in `treatment`:

- `test_attrition_reconciles_per_arm_over_the_uneven_7_5_fixture`: exact counts
  `{"resolved": 7, "completed": 6, "ineligible": 1, "failed": 0}` for `control`
  and `{"resolved": 5, "completed": 4, "ineligible": 0, "failed": 1}` for
  `treatment`, plus the arithmetic reconciliation for each.
- `test_cond_roster_covers_the_roster_exactly_once_per_unit`: coverage, not a
  sum — union of the two arms' key sets equals the roster's, intersection is
  empty. Kept in its **own** test function with no size assertion in it
  (correction #1: 7 + 5 = 12 is arithmetically implied the moment 7 and 5 are
  already pinned, so a combined test's second half wouldn't discriminate
  anything on its own).
- `test_cond_roster_narrows_each_condition_to_its_own_arm_size`: the sizes
  (7, 5) as their own test, split from the coverage test for the same reason.

## Mutation, and the finding it produced

The brief's mutation ("count the whole roster per condition") was applied by
making `_cond_roster` unconditionally return `roster`. All three tests above
failed independently (`resolved: 12` vs `7`, and the coverage intersection
becoming the full 12-key set instead of empty). Reverted; full suite green
by behavior, not by `git status`.

**A genuine defect surfaced during this**, caught by an `advisor` review
before committing: my first draft of `test_report_by_narrows_a_crossing_
stratum_to_the_condition_arm` called `levels_for` directly — a function
`cli.py` also calls, but not the code path `command_run` actually executes.
Mutating the real call site in `cli.py` back to `levels_for(roster, ...)` and
running the **whole** suite left every test green: the test could not fail
on the actual bug it claimed to pin, the exact "check that cannot fail"
defect class this task was warned about, reproduced by the tester rather
than the addendum. Fixed by extracting the inline `report_by` loop into
`_report_by_levels(roster, attribute)`, a pure function of one roster
argument, and re-running the same mutation-on-the-function's-own-body drill
against it — it now dies correctly (see `git log` — commit below). The
underlying limitation named in that extraction's own docstring is real and is
reported below, not fixed: the *call site* inside `command_run` (passing
`cond_roster` rather than `roster`) is still verified only by inspection,
because `sweep.groups` draws `E-SWEEP-GROUPS-UNSUPPORTED` at `validate` and no
test reaches `command_run` with a real group axis declared — the same
"unreachable in this build" status `_resolved_group_axes` already carries.
`_cond_beside_n` was extracted for the same testability reason and
mutation-tested the same way (returning `beside_n` unconditionally makes
`test_cond_beside_n_withholds_technical_n_under_an_arm_only` fail; reverted,
confirmed green).

## The other denominators (addendum's "check, and say what you found")

- **`max_ineligible_fraction`**: computed as `counts["ineligible"] /
  counts["resolved"]` immediately after `attrition`. Now automatically
  per-arm because `counts` itself is: over the fixture, `control` would warn
  at `1/7 ≈ 0.143` rather than the old `1/12 ≈ 0.083` — a materially
  different (larger) ratio, matching the addendum's prediction that the old
  whole-roster denominator understated attrition.
- **`max_failed_fraction`**: unaffected by this task, and correctly so. It is
  guarded by `_units_failed_anywhere` inside `execute_plan`
  (`src/publishable/runner.py`), already arm-aware since task 12, over
  `len(units)` — the **whole** resolved roster, which is what `reference.md`
  § What isn't a repeat's run-level framing ("units that failed in at least
  one execution, over `provenance.units.n`") requires. Not a defect; a
  different, deliberately run-level denominator.
- **`weights` / `clusters`**: both are whole-roster mappings (unit key →
  weight or cluster id), and `_counts` (in `runner.py`) indexes them only by
  `completed`, which is now the arm-scoped set `attrition` computed from
  `cond_roster`. So Kish's `effective` size and `clusters` are already scoped
  by the units actually counted, not by the mapping's extent — no change was
  needed there, and this was verified by reading `_counts`'s indexing
  (`weights[k] for k in sorted(completed)`, `cluster_count_of(clusters,
  completed)`), not by a fresh numeric fixture, since `completed`'s own
  correctness under arms is exactly what the reconciliation tests above
  already pin.
- **`_units_failed_anywhere` vs. `attrition`**: after this fix both are
  scoped to the condition's own arm — `_units_failed_anywhere` via
  `runner._arm_keys` internally (task 12), `attrition` via the `cond_roster`
  this task now hands it. The remaining difference between them — per-step
  intersection (`attrition`) vs. cross-step, run-level union
  (`_units_failed_anywhere`) — is the one `attrition`'s own docstring already
  names as deliberate ("This is deliberately NOT `_units_failed_anywhere`...
  the wrong shape for this run-level union") and is unchanged by this task.
  I did not build a fresh side-by-side numeric fixture for this pair
  specifically; task 12's own test
  (`test_units_failed_anywhere_does_not_blame_the_other_arm`, asserting
  exactly `{"u4"}`) already pins `_units_failed_anywhere`'s arm-scoping, and
  this task's fixture pins `attrition`'s.

## Concerns / defects found in the brief and addendum

- The addendum's own corrections section already flags and fixes its
  biggest defect (the "sum to the roster" independence-test error); I
  followed the corrected version (coverage, not sum) rather than the
  original.
- **A defect the corrections section did not catch**: correction #4's
  instruction to "pin it with a test whose stratum genuinely crosses both
  arms" is right in spirit, but doesn't warn that `report_by`'s narrowing
  lives inside `command_run`'s inline per-condition loop, which — like every
  group-axis code path in this build — is unreachable end to end
  (`E-SWEEP-GROUPS-UNSUPPORTED`). A test written against the obvious
  primitive (`levels_for`) passes regardless of whether the real call site is
  fixed, because it never executes that call site. This is the same
  "unreachable in this build, tested at the piece" status `_resolved_group_axes`
  and `test_non_string_levels_make_arm_members_raise_rather_than_skip_narrowing`
  already carry for the identical reason — the brief and addendum could have
  named it as they did for `_resolved_group_axes`, but didn't, and I only
  caught it via an `advisor` review's insistence on running the mutation
  against the whole suite rather than trusting the new test's own pass.
  Resolved by extraction (`_report_by_levels`, `_cond_beside_n`), matching
  the codebase's existing pattern for this exact situation.

## Commands run

`uv run pytest` (1471 passed, 2 xfailed), `uv run ruff check .` (clean),
`uv run mypy` (clean, 40 source files). `uv run ruff format .` was not run
(out of scope, pre-existing repo-wide state per the brief).

## Files touched

- `src/publishable/cli.py` — `_cond_roster`, `_cond_beside_n`,
  `_report_by_levels`; three call sites in `command_run` updated to use them.
- `src/publishable/runner.py` — `attrition`'s docstring, the `resolved`
  paragraph.
- `tests/test_cli.py` — new tests listed above.

---

## Addendum: response to coordinator review

**Status after this addendum: DONE.** All four items below are addressed;
`uv run pytest` (1475 passed, 2 xfailed), `uv run ruff check .`, and
`uv run mypy` are green after every change, verified by re-running the full
suite after each mutation/revert pair rather than trusting a targeted subset.

### Critical 1 — the prescribed mutation at the real call site

Confirmed exactly as the reviewer found: reverting all three of `command_run`'s
own call sites (`attrition(results, roster, ...)`, `_report_by_levels(roster,
attribute)`, `beside_n=beside_n`) and running the whole suite left **1474
passed, 2 xfailed** — nothing caught it. I had disclosed this for `report_by`
only; the main `attrition` call site was equally uncovered and I had not said
so. That under-disclosure was the real defect, separate from the test gap
itself.

**Fix: extracted one level further**, per the reviewer's suggested shape.
Three new functions in `cli.py`, each taking exactly the arguments
`command_run` has in scope at its call site (the *unnarrowed* `roster`, the
condition index, and `arm_members_map` — no separate `cond_roster` computed
and threaded through):

- `_condition_counts(results, roster, step_name, cond_index, arm_members_map, fold_members=, weights=, clusters=) -> dict[str, float]`
  — narrows via `_cond_roster` and calls `attrition`, in one call.
- `_condition_report_by_levels(roster, cond_index, arm_members_map, attribute) -> dict[str, tuple[set[str], UnitList]]`
  — narrows via `_cond_roster` and calls `_report_by_levels`.
- `_condition_beside_n(beside_n, roster, cond_index, arm_members_map) -> dict[str, Any]`
  — narrows via `_cond_roster` and calls `_cond_beside_n`.

`command_run`'s per-condition loop now calls only these three — the
intermediate `cond_roster` variable that could be computed-and-not-used (the
actual shape the original bug took) no longer exists in `command_run` at all.

New tests call these composed functions directly, with the same call shape
`command_run` uses (`tests/test_cli.py`):
`test_condition_counts_reconciles_per_arm_over_the_uneven_7_5_fixture`,
`test_condition_report_by_levels_narrows_a_crossing_stratum_to_the_condition_arm`,
`test_condition_beside_n_withholds_technical_n_under_an_arm_only`. Each was
mutation-tested by making the composed function itself skip narrowing (return
`attrition(results, roster, ...)` directly, `_report_by_levels(roster,
attribute)` directly, `beside_n` unconditionally) — all three died, reverted,
confirmed green by the full suite, `__pycache__` cleared between each step.

**Then I re-ran the brief's actual Step 5 mutation against the now-refactored
real call sites** in `command_run` (reverting its three calls back to bare
`attrition`/`_report_by_levels`/`beside_n=beside_n`, bypassing the composed
functions entirely) and ran the whole suite: **1474 passed, 2 xfailed —
still nothing caught it.** Reverted; confirmed green.

**This is the honest result, and it does not fully close the gap the reviewer
named.** The composed functions remove the specific bug shape that caused
task 13's defect (a narrowing computed and silently not passed downstream,
since there is no longer a separate variable for that to happen to), and they
are now directly, mutation-testably covered. But `command_run`'s own
per-condition loop remains structurally unreachable end to end with a real
group axis declared — `validate` refuses one outright
(`E-SWEEP-GROUPS-UNSUPPORTED`) — so no test can tell "`command_run` calls
`_condition_counts`" apart from "`command_run` calls bare `attrition`" short
of either retiring that refusal (task 17, out of scope here) or building a
harness that drives `command_run`'s internals while bypassing `validate`
entirely, which does not exist today and did not exist before this task. I
looked for a task-12-style route (calling a lower function directly, the way
`test_two_arms_get_different_rosters_and_neither_is_the_whole_roster` calls
`execute_plan`) and could not find one for `command_run`'s per-condition
aggregation loop specifically, because unlike `execute_plan` it is not a
standalone function `command_run` calls — it *is* `command_run`'s own body,
now reduced to three trivial, inspectable call expressions rather than three
inline computations. That inspectable-triviality is the actual mitigation;
it is weaker than a passing/failing test and I am not representing it as
equivalent to one.

### Important 2 — `technical_n`'s withholding, recorded in the document

Added to `docs/reference.md` § What isn't a repeat, in the paragraph the
existing `technical_n` passage lives in: a new sentence stating that
`technical_n` is withheld under a group axis or a `statistics.report_by`
level even where the input carried replicates, because it is a whole-roster
figure and neither an arm's nor a stratum's own. Also noted, in the same
edit, that the pre-existing `report_by`-level withholding was itself
undocumented before this — this task is what makes it a second exception,
and the document now says so rather than leaving both silent. `reference.md`
is the durable record; `docs/superpowers/spec-defects.md` is gitignored in
this checkout (`git check-ignore` confirms `docs/superpowers/` is ignored
wholesale) and would not survive the merge.

### Important 3 — `attrition` vs. `_units_failed_anywhere`, verified with numbers

Built the side-by-side fixture and added it as a test
(`tests/test_runner.py::test_attrition_and_units_failed_anywhere_agree_on_which_unit_failed`),
reusing the exact 7/5 fixture and the exact two results
`test_attrition_reconciles_per_arm_over_the_uneven_7_5_fixture` uses. Verified
by running the test, not asserted from memory:

- `_units_failed_anywhere(results, roster, None, arm_members)` → exactly
  `{"t0"}`, agreeing with `attrition`'s `control` block (`failed: 0`; `c0` is
  `ineligible`, not failed) and `treatment` block (`failed: 1`, that unit
  being `t0`).
- `_units_failed_anywhere(results, roster, None, None)` — arm-blind, the
  reading task 12 fixed this function out of — returns all 12 units: each
  condition's execution, scoped to the whole roster instead of its own arm,
  blames every unit of the *other* arm as unsettled, and the union of both
  covers the roster.

Both numbers match what the reviewer reported. This is now a durable,
mutation-independent test rather than a paragraph.

### Minor 4 — the crossing-stratum fixture's coincidental 7

Confirmed: `north` was 4 (`control`) + 3 (`treatment`) = 7, the same number as
`control`'s own `resolved`. Changed `treatment`'s split from 3 north / 2 south
to 2 north / 3 south, making `north` total 6 — distinct from both arms' sizes
(7, 5) and from the roster's own size (12). Updated the fixture's docstring
to say so explicitly (why 6 was chosen, and that an earlier 3/2 split
coincided with `control`'s `resolved`), and updated the one assertion whose
expected key set changed (`{"c0","c1","c2","c3","t0","t1"}`, not
`...,"t2"`).

### Minor 5 — which number proves which part

Added a sentence to `test_attrition_reconciles_per_arm_over_the_uneven_7_5_fixture`'s
docstring: `c0`'s absence from both `recorded` and `skipped` would make it
`failed`; declaring it `skipped` explicitly is what makes it `ineligible`
instead — so `ineligible: 1` on `control` is `c0`'s proof and `failed: 1` on
`treatment` is `t0`'s, each showing one kind of attrition the other arm
doesn't.

### Minor 6 — no action taken, per the reviewer's own note.

### Minor 7 — `validate.py`'s whole-roster `levels_for`, recorded

Read `validate.py`'s `_check_report_by` (around its `for level, keys in
sorted(levels_for(roster, name).items())` call feeding `W-STATS-REPORTBY-THIN`):
confirmed it counts every level against the whole validate-time roster, with
no per-condition or per-arm narrowing available to it at all (it has no
`cond_index` parameter — it is a single, design-level check, not one that
runs once per condition the way `command_run`'s `report_by` block does).
Recorded rather than fixed, for two reasons: it is genuinely unreachable
while `E-SWEEP-GROUPS-UNSUPPORTED` stands (confirmed the same way `_resolved_group_axes`'s
own docstring already states its unreachability), and narrowing it correctly
would require validate-time knowledge of which condition a stratum's warning
is being evaluated for — a shape change `_check_report_by` does not have
today and task 17 is the slice that would introduce alongside retiring the
refusal. Recorded in `docs/reference.md`, both in § What isn't a repeat
(beside the `technical_n` gap, as asked) and as a clause on the
`W-STATS-REPORTBY-THIN` row itself in § Warnings core reports, naming the
row by what it checks rather than by position.

---

## Second addendum: finding 1 closed, not mitigated

**Correction to my own earlier conclusion, stated plainly rather than quietly
deleted:** I wrote that `command_run`'s per-condition aggregation loop was
"structurally unreachable end to end" without retiring
`E-SWEEP-GROUPS-UNSUPPORTED`, and that I "could not find a task-12-style
bypass route" for it. That conclusion was wrong. What I actually did was
search for a route that didn't touch `validate` at all (mirroring
`test_two_arms_get_different_rosters_and_neither_is_the_whole_roster`, which
calls `execute_plan` directly and never goes near `validate_config`) — I
did not seriously consider monkeypatching a single function *inside*
`validate` to let a real config through `command_run`'s own `validate_config`
gate, even though `tests/test_cli.py` already monkeypatches plenty
(`experiment_gen.STARTER_STEP`, `GenericTemplate.aggregate`) to reach exactly
this kind of real, end-to-end run. That was the gap in my search, not a gap
in what the codebase makes possible.

**The bypass, verified myself, not taken on faith.** Read
`validate._check_unimplemented` (`src/publishable/validate.py`, starting at
its `def`): it is the *only* place `E-SWEEP-GROUPS-UNSUPPORTED` is raised,
and it also happens to be the only place `E-DATA-ALLOCATION-UNSUPPORTED` and
`E-DATA-ASSIGN-UNSUPPORTED` are raised — all three gate on the same
module-level function, called exactly once, from `validate_config`. Confirmed
by reading, not assuming, that `_check_assign` (the function doing the real
arm-resolution work — the seven § Validation rows, `E-DATA-ASSIGN-LEVELS`
among them) is a *separate* function, called separately, and untouched by
patching `_check_unimplemented`.

**Added the permanent regression test**:
`tests/test_cli.py::test_a_group_axis_actually_narrows_end_to_end`. It:

- Monkeypatches exactly two things: `experiment_gen.STARTER_STEP` (to get a
  step that `io.skip`s one unit and leaves another unsettled — ordinary test
  scaffolding, the same pattern a dozen existing tests in this file use) and
  `validate._check_unimplemented` (the one gate, replaced with a no-op —
  nothing else patched, no `has_errors` forcing, no `validate_config` stub).
- Declares a real `sweep.groups` + `data.units.allocation: between` +
  `data.units.assign: {arm: {method: by_attribute}}` config and runs it
  through `main(["run", ...])` to `EXIT_OK`.
- Uses an **8/3 split** (11 units total) rather than the reviewer's 6/6:
  every number in play — 8, 3, 11 — is distinct from every other, so a
  regression can't hide behind an accidental equality the way two equal
  arms, or a sum matching a number already in use, would allow.
- Asserts the exact per-arm `n` from a real `run.yaml`:
  `control` → `{"resolved": 8, "completed": 7, "ineligible": 1, "failed": 0}`,
  `treatment` → `{"resolved": 3, "completed": 2, "ineligible": 0, "failed": 1}`.

**Ran the brief's actual Step 5 mutation against this test** — reverted
`command_run`'s three real call sites back to bare `attrition(results,
roster, ...)`, `_report_by_levels(roster, attribute)`, and
`beside_n=beside_n`, cleared `__pycache__`, ran the test:

```
FAILED tests/test_cli.py::test_a_group_axis_actually_narrows_end_to_end
AssertionError: assert control_n == {"resolved": 8, ...}
  {'resolved': 11} != {'resolved': 8}
  {'failed': 3} != {'failed': 0}
```

A clean, decisive catch — `resolved: 11` (the whole roster) instead of `8`,
and `treatment`'s 3 units bleeding into `control`'s `failed` count. Reverted
the mutation, cleared `__pycache__` again, re-ran: passes. Ran the full suite
after the revert: **1476 passed, 2 xfailed** (one more than the prior
addendum's 1475 — the new test). `ruff check .` and `mypy` both clean.

**This is what closes finding 1.** The composed functions
(`_condition_counts`/`_condition_report_by_levels`/`_condition_beside_n`)
were already correct and already mutation-tested in isolation; what was
missing was proof that `command_run` actually calls them, over units and
counts nobody hand-built for the test — and that proof now exists as a
permanent, passing-today, decisively-failing-under-the-prescribed-mutation
regression test, not as an inspection argument about call-site triviality.

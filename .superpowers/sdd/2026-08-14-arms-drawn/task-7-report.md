# Task 7 report: the draw's authority, and the shape that can express it

**Status:** complete. Commits `60c65d4` (the seam) and `2542b7f` (crosscut fixture,
required `roster`/`digest`).

## What was built

`units.ArmPlan` — frozen dataclass, `levels: tuple[str, ...]`,
`members: Mapping[str, tuple[str, ...]]` (level → unit keys, roster order under
`by_attribute`), `seed: int | None`, `strata: tuple[str, ...]`.

`units.assignment_for(roster, axis, block, levels, digest, clusters=None) -> ArmPlan`
— a pure function of its arguments, callable from `validate` and from
`cli.command_run` alike. Dispatch on `block["method"]`:

- `random` / `blocked` → `NotImplementedError` naming the method. An explicit
  hole for tasks 8 and 10.
- `by_attribute`, an absent/non-mapping/method-less block, or any other string →
  `arms_of` unchanged, with `from` resolved here (declared `from` if a non-empty
  string, else the axis name). Only the two *drawing* methods divert, so no
  drawing method can reach a column read by falling through; an out-of-enum
  method is already refused at `validate` (`E-DATA-ASSIGN-METHOD`).
- `digest` and `clusters` are unread on this path and are parameters anyway —
  they are what tasks 8 and 10 draw with.

`from` resolution was **moved**, not duplicated: `cli._resolved_group_axes` used
to resolve it too. Two resolutions of one declaration is a smaller instance of
the defect this slice closes.

## The three consumers

| Before | After |
|---|---|
| `units.arm_members(roster, axes: Mapping[str, tuple[str, Sequence[str]]], conditions)` | `units.arm_members(axes: Mapping[str, ArmPlan], conditions)` |
| `cli._resolved_group_axes(units_decl, sweep_block) -> dict[str, tuple[str, list[str]]]` | `cli._resolved_group_axes(units_decl, sweep_block, roster, digest, clusters=None) -> dict[str, ArmPlan]` |
| `artifacts.build_allocation_document(roster, group_axes) -> dict \| None` | `artifacts.build_allocation_document(group_axes: Mapping[str, ArmPlan]) -> dict \| None` |

`_resolved_group_axes`'s `roster` and `digest` are required, not defaulted:
`digest` is unread on the `by_attribute` path today and task 8 threads it into
`assign_seed_for`, so a defaulted one would become a draw silently seeded from
the empty string with every test still green. It returns `{}` when `roster is None` — the same gate
`command_run` already applied before calling `arm_members`, kept rather than
moved, so a design with no `data.units` still reaches `execute_plan` with no arm
narrowing rather than raising. Its `levels`-shape skip is unchanged, so
`test_non_string_levels_make_arm_members_raise_rather_than_skip_narrowing`'s
`KeyError` route survives intact.

## Step 5 — the recomputation decision

**Decided: compute once and pass.** Two calls cannot be made to promise they
agree under a draw; only not calling twice can. `_resolved_group_axes` realizes
one plan per axis; `arm_members` narrows with those plan objects and
`build_allocation_document` records those same objects. Stated in
`build_allocation_document`'s docstring, in `assignment_for`'s, and in the
comment at the `alloc_doc` call site.

**`build_allocation_document` takes no roster**, and that is deliberate beyond
tidiness: with nothing to read membership *from*, it cannot become a second
producer of it. Same reasoning for `arm_members`. This is the one deviation from
the brief's letter (it named only the `axes`/`group_axes` parameter): dropping
the roster makes the single-authority property structural rather than
conventional.

`seed`/`strata` in the document are now read from the plans (`{}` in this build,
since `by_attribute` realizes `seed=None`, `strata=()`) instead of hardcoded
literals — the document is byte-identical, so `allocation_hash`'s two pinned
digests (`sha256:bf077b…`, `sha256:74e5df…`) are unchanged.

## Step 6 — mutation testing

Each: apply, run, confirm FAIL, revert, delete `__pycache__`, confirm PASS.

| Mutation | Result |
|---|---|
| `assignment_for` returns a fresh partition (each level's keys reversed) | FAIL ×3 — `test_one_plan_per_axis_is_realized_once_and_both_consumers_get_that_same_plan`, `test_assignment_for_by_attribute_realizes_arms_of_with_no_seed_and_no_strata`, `test_assignment_for_takes_the_by_attribute_path_for_an_unnamed_method` |
| `command_run` re-realizes the plans for `allocation.json` (a second `_resolved_group_axes` call) — the recomputation this task removed | FAIL — the call-count assertion in `test_one_plan_per_axis_…` (1 → 2) |
| `assignment_for` resolves every axis's column to `arm_column` (crosstalk between two axes' resolutions) | FAIL — `test_resolved_group_axes_realizes_a_plan_per_axis_and_skips_unresolvable_levels` |
| `assignment_for`'s drawn-method guard defanged (`method in ()`), i.e. the silent fallback to a column read | FAIL ×3 — both `test_assignment_for_refuses_a_drawn_method_rather_than_reading_a_column` params and `test_resolved_group_axes_raises_rather_than_reading_a_column_under_a_drawn_method` |

## Tests

New, in `tests/test_units.py`:
`test_assignment_for_by_attribute_realizes_arms_of_with_no_seed_and_no_strata`
(the brief's step 1 — 7/5 over the `_arm_roster12` split, both arms' keys
written out **literally** rather than re-derived from the fixture's own `arm`
attribute, plus `seed is None` and `strata == ()`);
`test_assignment_for_resolves_from_against_the_axis_name_and_reads_no_other_column`
(with the control that must report: no `from` → `E-DATA-ASSIGN-LEVELS`);
`test_assignment_for_refuses_a_drawn_method_rather_than_reading_a_column`
(parametrized, on a fixture that *does* carry an arm attribute, so a fallback
would have succeeded silently);
`test_assignment_for_takes_the_by_attribute_path_for_an_unnamed_method`.

Retargeted rather than deleted: `test_arm_members_calls_arms_of_once_per_axis_not_per_condition`
became `test_arm_members_derives_no_membership_of_its_own_from_a_planted_plan` —
`arm_members` no longer calls `arms_of` at all, so the once-per-axis property is
now `assignment_for`'s (pinned end to end in `test_cli.py`), and the planted plan
**contradicts** the roster column, so a re-derivation returns the swapped-back
sets and fails.

New, in `tests/test_cli.py`:
`test_one_plan_per_axis_is_realized_once_and_both_consumers_get_that_same_plan`
— a real `command_run` with a spy on `cli.assignment_for`: exactly one call for
the run, `allocation.json`'s `arms` equal to the captured plan's `members` key
for key and in order, plus the arms actually narrowed (4 and 9 resolved and
completed, the fixture's uneven split).
`test_resolved_group_axes_is_empty_with_no_roster_to_partition` carries its
control (the same declaration *with* a roster realizes the axis).
`test_resolved_group_axes_ignores_from_under_a_non_by_attribute_method` became
`test_resolved_group_axes_raises_rather_than_reading_a_column_under_a_drawn_method`.
Fixture sizes are 8/3/11 (`_levels_roster`) and 4/9/13, each already distinct
from `_arm_roster12`'s 7/5/12. `_levels_roster`'s `cohort` **crosscuts** its
`arm_column` (5/3 within control, 1/2 within treatment) so all four member
tuples differ — two axes partitioning the roster identically could not tell
"read the `cohort` column" from "inherited the other axis's resolved column."

`uv run pytest` 1530 passed, 2 xfailed. `uv run ruff check .` and `uv run mypy`
clean. No `ruff format` run. No `*.md` under `docs/` changed, so no consistency
pass was owed; `reference.md`'s `allocation.json` prose and its "no reader in
this build" note remain accurate.

**On the brief's literal mutation** ("make `assignment_for` return a fresh
partition rather than the shared plan," meaning a new-but-equal object): it is
vacuous under this design rather than skipped — there is one call site and one
plan, so no second object exists for identity to diverge from. That is the
design succeeding. The value-perturbation substitute above (reversed keys) is
what stands in for it, and it fails three tests. For the same reason the
"same object" claim is pinned by `len(realized) == 1` rather than by an `is`
check.

## Concerns

1. **Can any path still produce a second, independent notion of arm membership?**
   In `run`, no: `assignment_for` is the only producer, it is called from exactly
   one place (`_resolved_group_axes`), and both consumers now lack a roster to
   derive membership from. `arms_of` is still called from two places — from
   `assignment_for` and from `validate._check_assign` — but `validate` calls it to
   *report* `E-DATA-ASSIGN-LEVELS`, not to build membership, and it discards the
   partition. **That call is the remaining seam.** Tasks 12–13 need real
   membership inside `validate` for the cell and stratum checks; they must call
   `assignment_for`, not `arms_of`, or the second notion reappears exactly where
   this brief predicted. Worth stating in those briefs — together with an
   ordering clause: `assignment_for` raises `NotImplementedError`, which is not a
   `PublishableError`, so a `validate` calling it on a drawn axis before task 8
   lands produces a traceback where every other refusal is a diagnostic. Tasks
   8/10 precede 12/13, so this is likely moot, but it is an ordering assumption
   worth writing down rather than rediscovering.
2. **`ArmPlan` is not deeply immutable.** `frozen=True` blocks rebinding; the
   `members` mapping is a plain `dict` a determined caller can mutate in place.
   Said so in the docstring rather than claimed otherwise.
3. **No run-time guard that a plan matches the roster it narrows.** I considered
   raising when a plan's keys are not exactly the roster's, and did not: it needs
   a new `E-` code (every `ContractError` in core carries one), which drags
   `reference.md` § Errors and both consistency passes into a task that is meant
   to be a refactor, and under `by_attribute` `arms_of` already guarantees it.
   Once `random`/`blocked` land — where a stale plan silently narrows to zero
   units rather than raising — that guard is worth its code. Recorded here rather
   than smuggled in.
4. **No requirement in the brief rested on a false premise.** Every interface it
   listed matched the code. One brief statement is now stale by construction:
   "`build_allocation_document` calls `arms_of` a second time" was true before
   this commit and is false after.

---

## Addendum: review follow-up (commit pending below)

### The Important, fixed

**"Which methods draw" had two sources of truth, and the guard was fail-open.**
Both halves done.

1. **`DRAWN_ASSIGN_METHODS` now lives in `units.py`** and `validate.py` imports
   it. The dependency edge already ran that way (`units.py` imports nothing from
   `validate`), and the asymmetry of lifetimes is the second reason: task 14
   retires `E-DATA-ASSIGN-DRAWN`, so `validate`'s use of the tuple is temporary
   while the draw's is permanent. `validate` keeps a comment at the old site
   saying why the constant moved rather than a silent deletion.
   `docs/superpowers/H3c-2-SCOPING.md` mentions `validate.DRAWN_ASSIGN_METHODS`
   in passing; it is a scoping note, not one of the four documents, and its
   claim ("usable from H3c-1, with its `elif` branch the single retirement
   point") is unaffected by where the tuple is declared.

2. **`assignment_for` is an allowlist.** `by_attribute`, an absent block, a
   non-mapping block, and a method-less block take the column-read path;
   **everything else raises `NotImplementedError`**. `DRAWN_ASSIGN_METHODS` now
   only picks *which message* the raise carries — the drawn one ("draws its
   allocation … `E-DATA-ASSIGN-DRAWN`") or the general one naming `by_attribute`
   as the only method this build reads a column for. Fail-closed costs nothing:
   `E-DATA-ASSIGN-METHOD` already refuses an out-of-enum value before `run` can
   reach the call. Both docstrings (`assignment_for`, `cli._resolved_group_axes`)
   were corrected — the old text promised that "any other `method` string takes
   the `by_attribute` path", which was exactly the defect.

New test: `test_assignment_for_refuses_a_method_it_has_never_heard_of`
(`adaptive`, on a fixture whose units *do* carry `arm`, so a denylist would have
returned a plausible partition instead of raising). The drawn-method test is now
parametrized over `DRAWN_ASSIGN_METHODS` itself rather than a re-typed literal
pair, so the two sides can no longer drift apart unnoticed.

**The named mutation, run:** added `"adaptive"` to `validate.ASSIGN_METHODS`
*and* restored the denylist form of the guard →
`test_assignment_for_refuses_a_method_it_has_never_heard_of` FAILs with "DID NOT
RAISE NotImplementedError", i.e. the fourth method was silently partitioned by a
column read. Restoring the allowlist **while leaving the extended enum in place**
→ PASS, and a direct probe confirmed the raise rather than a partition. Enum then
reverted; `ASSIGN_METHODS` re-read as `("random", "by_attribute", "blocked")` and
the suite is green (revert verified by behaviour, `__pycache__` cleared between
steps).

`uv run pytest` 1531 passed, 2 xfailed. `ruff check` and `mypy` clean.

### Recorded for tasks 12 and 13 (not fixed here)

- When `validate` starts needing real membership for the cell and stratum
  checks, it must call `units.assignment_for` and **stop calling `arms_of`
  directly**, or the second producer reappears in the one place this slice left
  it.
- Carry a latent asymmetry with that change: `validate._declared_levels` returns
  the **first** `sweep.groups` entry matching `by`, while
  `cli._resolved_group_axes` keeps the **last**. Unreachable today — a duplicate
  `by` is `E-SWEEP-PATH-DUPLICATE` — but it is the second place two resolutions
  of one declaration could diverge once both sides resolve plans.
- The review closed my `NotImplementedError`-as-traceback concern as *provably*
  unreachable, not merely unlikely: `validate` never calls `assignment_for`;
  `command_run` gates on `has_errors` with no `try`/`except` between that gate
  and the call site; and `_check_assign`'s block loop sits outside the
  `allocation` gate, so any dict block naming a drawn method yields
  `E-DATA-ASSIGN-DRAWN` regardless of `allocation`, `sweep.groups`, or roster
  resolution. No guard is owed before tasks 8 and 10.

### Recorded for the draw tasks (not fixed here)

`build_allocation_document` iterates `plan.members`, not `plan.levels`, so
nothing checks that realized membership covers the **declared** levels.
`arms_of`'s set equality guarantees it under `by_attribute`; under a draw it will
not be free. Same shape as the no-plan-vs-roster-guard concern above, and the
same conclusion: worth an `E-` code when the draw lands, not before.

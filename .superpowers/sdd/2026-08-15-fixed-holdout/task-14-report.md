# Task 14 report: runner narrowing — `io.units` is the test partition, `io.units.train` the training one

## Status

DONE

## What was built

`src/publishable/runner.py`: added `holdout_train: "UnitList | None" = None` to `execute_plan`'s
keyword-only parameters, immediately after `arm_members`. Added a docstring paragraph naming
`holdout_train` and stating that `units` is the test partition and `io.units.train` is
`holdout_train` at every scope when it is given. Added two assertions at the top of the function
body, before the loop: `holdout_train is None or fold_members is None` (guards `E-DATA-HOLDOUT-FOLD`)
and `holdout_train is None or arm_members is None` (guards `E-DATA-HOLDOUT-CELLS`), each with a
comment naming the two error codes and the reasoning for asserting rather than silently choosing a
precedence. In the no-fold branch of the per-execution narrowing (`if fold_members is None or
scoped_units is None:`), added:

```python
step_units = scoped_units
if holdout_train is not None and scoped_units is not None:
    step_units = UnitList(list(scoped_units), train=holdout_train)
```

The `scoped_units is not None` guard is **the one addition beyond the brief's literal snippet**: the
brief's `if holdout_train is not None:` alone crashes `list(None)` for a no-roster run (`units=None`)
under a declared holdout, a real path `mypy` caught (`Argument 1 to "list" has incompatible type
"UnitList | None"`). Since `_resolved_holdout` already returns `None` whenever `roster is None`, this
guard changes no reachable behavior — it only makes the type, and the "no roster → no partition
either" invariant, checkable.

`src/publishable/cli.py`: removed the `# noqa: F841 -- consumed starting task 14` from the
`holdout_plan = _resolved_holdout(...)` call — it is now read. Added `holdout_train=` to the
`execute_plan` call, narrowing `roster` to `holdout_plan.train`'s keys via `UnitList`, guarded by
`holdout_plan is not None and roster is not None` (the extra `roster is not None` conjunct is the
same `mypy`-driven addition as above: `roster` is typed `UnitList | None` at that call site, and
`holdout_plan is not None` alone doesn't narrow it for the type checker even though the two are
never non-`None`/`None` in different directions in practice). Left `units=roster` untouched, per the
brief (task 15 owns that line).

`tests/test_runner.py`: appended the brief's three tests verbatim (`test_a_holdout_narrows_io_units_at_every_scope`,
`test_without_a_holdout_train_still_raises_at_every_scope`,
`test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice`), plus the four helpers the brief
named but that did not yet exist in this file (grepped first — `_runner_roster`, `_run_one_step`,
`_run_one_step_raw`, `_one_step_plan` collide with nothing): `_runner_roster` (an `n`-unit roster
`u0..u{n-1}`), `_load_step_from_source` (compiles the `{scope}`-formatted recording-step source and
returns its `Step` class — needed because `scope` is a class attribute `build_plan` reads before any
instance exists, so a scope-parametrized test needs one class per scope), `_one_step_plan` (a
one-step, one-condition plan via `build_plan`, for driving `execute_plan` directly without a `cli`
run), `_run_one_step_raw` (returns the single raw `ExecutionResult`), and `_run_one_step` (asserts
`status == "completed"` and returns the parsed `seen.json` the recording step wrote). Added
`import json` at the top of the file for the last helper.

## `io.units.train` when no holdout was declared

Unchanged and confirmed by test: with `holdout_train=None` (and no fold), `step_units` stays exactly
`scoped_units` — a `UnitList` whose `._train` is `None` — so `io.units.train` still raises
`E-STEP-UNITS-UNAVAILABLE` (`ContractError`, from `UnitList.train`'s property in
`src/publishable/units.py`). It does **not** return an empty list; that would be the exact bug
`design-principles.md` calls out ("an empty list would let a fit run on nothing"), and mutation (e)
below reproduces it deliberately to show the control test catches it.

## Test summary

`uv run pytest` — 1933 passed, 2 xfailed (1927 baseline + 6 new: the 3 brief tests, one of which is
parametrized ×4 scopes). `uv run ruff check .` and `uv run mypy` clean (42 source files). `uv run
ruff format --check` on the three touched files shows only pre-existing drift, confirmed present
before this task via `git stash` + re-check on `cli.py`/`runner.py`/`test_runner.py`; my own added
lines in `test_runner.py` show no diff under `ruff format --check --diff` (verified directly, not
inferred).

## Mutations — five run, not three

All reverted by editing the file back (never `git checkout --` on the touched files); each revert
verified by re-running the targeted test, `__pycache__` deleted between runs, and a final `diff`
against a pre-mutation backup copy confirmed byte-identical restoration for both `runner.py` and
`cli.py` before committing.

**(a)** brief's — moved the `if holdout_train is not None ...` narrowing inside a scope check, so it
only applies at `execution.scope == "repeat"` (structurally: `if fold_members is None or
scoped_units is None: step_units = scoped_units; if execution.scope == "repeat": if holdout_train is
not None and scoped_units is not None: step_units = UnitList(...)`).
Result: **FAIL** for `run`, `condition`, `summary`; **PASS** for `repeat` —
`test_a_holdout_narrows_io_units_at_every_scope[run/condition/summary]` failed with
`E-STEP-UNITS-UNAVAILABLE` (the step touching `io.units.train` on a roster that was never wrapped),
exactly as predicted.

**(b)** brief's — changed `step_units = UnitList(list(scoped_units), train=holdout_train)` to
`step_units = UnitList(list(holdout_train), train=holdout_train)`.
Result: **FAIL** for all four scope rows, each on `seen["test"] == ["u8", "u9"]` (the step saw the
training roster as `io.units` instead of the test partition) — exactly as predicted.

**(c)** brief's — changed `cli.py`'s `holdout_train=` expression to `holdout_train=None`.
Result: **nothing failed** — `uv run pytest` still reports 1933 passed, 2 xfailed. This is the
honest result at this commit: `E-DATA-HOLDOUT-UNSUPPORTED` refuses every config that declares a
holdout before `command_run` is reached, so no test exercises this call site end-to-end yet. Task
18's brief is what closes it; I did not invent a test reaching `command_run` with a holdout.

**(d)** mine — deleted the `assert holdout_train is None or fold_members is None, (...)` block (the
`E-DATA-HOLDOUT-FOLD` guard), leaving only the `E-DATA-HOLDOUT-CELLS` assertion.
Result: **FAIL** — `test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice` failed, but
not by the pair resolving silently and returning: execution proceeded past the (now-missing)
assertion and crashed three lines later with an unrelated `ContractError`
(`E-RUN-SEED-MISSING` — the dynamically-loaded step's module name `test_runner_dynamic_step` has no
seed among the resolved repeats `[]`, since the test passes `repeats=[]`). The test still fails
under this mutation and for the reason the brief's docstring names (no `AssertionError` is raised),
even though the concrete exception surfacing first is a different one — the same shape task 13's
mutation (d) found: a guard's removal can surface as a crash somewhere else in the call chain rather
than as the naively-expected wrong return.

**(e)** mine, since the brief left it unnamed — changed the outer condition
`if fold_members is None or scoped_units is None:` to `if scoped_units is None:` (dropping the
`fold_members is None or` disjunct).
Result: **FAIL** — `test_without_a_holdout_train_still_raises_at_every_scope` failed:
`result.status == "completed"` instead of `"failed"`. With `fold_members=None` and `holdout_train=None`
on a `repeat`-scope execution, this mutation routes the narrowing into the fold branch
(`elif execution.scope == "repeat":`) instead of the no-fold branch. `_handed_keys(label, keys,
fold_members=None)` returns the whole `keys` set (its own documented `None`-passthrough), so
`step_units` becomes `UnitList(all units, train=UnitList([]))` — an **empty list**, not the raise the
control demands. This is exactly the failure mode `design-principles.md`'s `UnitList.train` docstring
and this task's brief both call out by name ("an empty list would let a fit run on nothing" /
"a narrowing written one branch too wide would hand a train list to a run that declared no
partition") — confirming a single-line mutation does reach this seam, and it is the disjunct guard
protecting it.

## Where the brief disagreed with the code

Two places, both `mypy`-driven and both additive (no behavior change on any reachable path):

1. `runner.py`'s no-fold branch: the brief's `if holdout_train is not None:` alone is well-typed only
   because `scoped_units` is never actually `None` when `holdout_train` is not — but `mypy` cannot see
   that invariant across two independently-`None`-able parameters, and flagged `list(scoped_units)` as
   `list(UnitList | None)`. Added `and scoped_units is not None`.
2. `cli.py`'s `execute_plan` call: the brief's `if holdout_plan is not None else None` ternary, with
   `roster` typed `UnitList | None`, left `mypy` unable to narrow `roster` inside the `if`-branch
   (`Item "None" of "UnitList | None" has no attribute "__iter__"`). Added `and roster is not None`.

Both additions are guarded by the existing invariant in `_resolved_holdout`'s own docstring ("`None`
for a `roster` of `None` too"), so neither changes what any config or direct `execute_plan` caller
observes — they only make the already-true invariant visible to the type checker. `uv run mypy` was
not clean before these two edits (2 errors) and is clean after.

No other disagreement found. The five-scope narrowing (inverse of the fold rule), the two assertions'
placement (before the loop, not inside the branch), and the helper functions' shapes all matched the
brief once these two guards were added.

## Process notes

`.superpowers/sdd/.gitignore` was clobbered to a bare `*` by reading `task-14-brief.md` (the standing
`scripts/sdd-workspace`/`task-brief` behavior CLAUDE.md documents). Restored via `git checkout --
.superpowers/sdd/.gitignore` before committing — safe here because that file had no uncommitted
content of its own; it reverted the auto-clobber back to the last commit's tracked content, verified
by `git diff` showing no remaining changes to it.

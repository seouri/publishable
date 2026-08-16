# Task 14 review: runner narrowing — `io.units` is the test partition, `io.units.train` the training one

Reviewed `c671abc..8b3602a` against `task-14-brief.md`, `task-14-report.md`, the four documents, and
the code as it ships.

## Verdicts

1. **Spec compliance — ✅.** The narrowing is at every scope, it is the inverse of the fold rule and
   is not nested inside it, `io.units.train` still raises when nothing is declared, and the shipped
   behaviour matches `reference.md` § A fixed holdout split, § A `fold` repeat puts the units out of
   reach of the wider scopes, and § Errors. No document needs to change.
2. **Task quality — ❌.** Two test gaps, both of the shape CLAUDE.md names by name: an assertion that
   ships with no test that can fail on it, and a test whose *name and docstring* claim a four-scope
   guarantee it checks at one scope.

---

## Answers to the four directed checks

### Check 1 — the scope rule is the inverse of the fold rule, and fold behaviour is unchanged

**Not nested, not gated, not shadowed — and no fold regression.** `runner.py:595-627`: the outer
`if fold_members is None or scoped_units is None:` condition is byte-identical to what it was before
this commit (diff shows it as context, not as a changed line). The holdout narrowing is a nested
`if holdout_train is not None and scoped_units is not None:` inside that **first** branch of the
chain, so it is reached at `run`, `condition`, `repeat` and `summary` alike — the branch is entered
on the scope-independent `fold_members is None` disjunct, never on a scope test. The
`elif execution.scope in ("run", "condition"): step_units = None` fold hole is a *sibling* branch,
reachable only when `fold_members is not None`, which the new assertion at line 516 makes mutually
exclusive with a holdout.

For a run that declares only a fold, `holdout_train` is `None`, the nested `if` is false, and every
line the fold path executes is unchanged. Verified by reading both branches together and by the
suite: 1933 passed / 2 xfailed against a 1927 baseline, i.e. six added, zero moved. I did not spend a
mutation here — under a fold the holdout code is *unreachable by construction*, which is exactly why
the assertion, not a branch guard, is the protection.

### Check 2 — the two `mypy`-driven conjuncts

Both are benign, and the mechanism matters more than the invariant claim:

- **`cli.py:1594` — `and roster is not None`.** Unreachable. `_resolved_holdout` returns `None` at
  `cli.py:492-493` before it looks at anything else whenever `roster is None`, so
  `holdout_plan is not None` already implies `roster is not None`. The conjunct can never be the
  thing that decides the ternary. Verified by reading `_resolved_holdout`'s first two statements, not
  by trusting its docstring.
- **`runner.py:614` — `and scoped_units is not None`.** `scoped_units is None` iff `units is None`
  (the only other assignment, the arm narrowing at 585-587, is guarded on `units is not None`, and is
  in any case asserted off under a holdout). When it *is* `None`, `step_units` stays `None`, and
  `artifacts.py:362-372` makes `io.units` raise `E-STEP-UNITS-UNAVAILABLE`. So the guard converts a
  `TypeError: list(None)` into a `ContractError` — **both loud**. It cannot produce the bad outcome
  the check was written to look for (a run executing over an unnarrowed roster with the narrowing
  silently skipped), because there is no roster in that state at all.

No finding.

### Check 3 — `io.units.train` raises rather than returning empty

**Shipped code raises.** With `holdout_train=None` and no fold, `step_units = scoped_units`
unchanged; `scoped_units._train` is `None`; `UnitList.train` (`units.py:155-163`) raises
`ContractError` · `E-STEP-UNITS-UNAVAILABLE` with the message "an empty list would let a fit run on
nothing".

**The control does distinguish raise-from-empty**, not merely "a failure occurred": it asserts
`result.status == "failed"` **and** `E-STEP-UNITS-UNAVAILABLE in result.error`. Under the empty-list
defect the recording step *completes* (it writes `train: []` and returns), so `status` is
`"completed"` and the first assertion fails — which is precisely what the implementer's mutation (e)
observed. Mutation (e) is a sound attribution and the report's account of it is accurate.

### Check 4 — mutation (d) and whether test 3 pins what its name claims

**It pins it; the report's own worry is misplaced, and (d) is the attribution rather than a weakness.**
`pytest.raises(AssertionError)` passes *only* on an `AssertionError`. A silent-precedence
implementation either returns normally (no exception → test fails) or crashes with something else
(`ContractError` propagates out of the `raises` block → test fails). Both are failures. So the test
cannot pass against silent precedence "that happened to crash later" — under mutation (d) it
correctly failed, and the fact that the surfacing exception was `E-RUN-SEED-MISSING` is evidence the
passing exception in the unmutated run comes from the deleted assert, not from anywhere downstream.

Attribution is also structural: the test passes `arm_members=None`, so only the fold assertion can
fire. The one hardening available is a `match=` on the message; see Minor 1.

---

## Findings

### Important 1 — `assert holdout_train is None or arm_members is None` has no test that can fail on it

`runner.py:520-522`. The `E-DATA-HOLDOUT-CELLS` assertion ships untested. Its sibling — the
`E-DATA-HOLDOUT-FOLD` assertion — has `test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice`;
this one has nothing, and the brief's "the assertion covers that too" was carried into the code
without being carried into a test.

**Verified by mutation, not by reading.** I deleted the whole assert block from `runner.py`, deleted
every `__pycache__`, and ran `uv run pytest`: **1933 passed, 2 xfailed** — identical to the
unmutated run. Nothing fails. Reverted by editing the block back in place (never `git checkout --`),
verified by re-running `uv run pytest tests/test_runner.py -k holdout` (6 passed) and by
`git status --porcelain` showing no modification to `src/`.

This is the answer to check (a): the five mutations run reach the narrowing site (b), its scope
placement (a), the outer disjunct (e), the fold assertion (d), and the `cli` wiring (c, honestly
unreachable until task 18). **None reaches the cells assertion.** It is three lines to pin by the
same direct-call route test 3 already uses — `arm_members={0: frozenset({"u0"})}`, `fold_members=None`,
`holdout_train=UnitList(list(roster)[:5])`, inside `pytest.raises(AssertionError)`.

Not Critical: the reachability argument behind the assertion holds (see Minor 3), so this is an
unpinned guard rather than a live defect.

### Important 2 — `test_without_a_holdout_train_still_raises_at_every_scope` tests exactly one scope

`tests/test_runner.py`. The name says *at every scope* and the docstring says *"a narrowing written
one branch too wide would hand a train list to a run that declared no partition"* — but the test is
unparametrized and calls `_run_one_step_raw(..., scope="repeat", ...)`. Three of the four scopes are
unasserted. This is CLAUDE.md's *"a test whose **name** claims the guarantee"* trap verbatim, made
sharper by the asymmetry with its sibling: the positive test is parametrized ×4 *because* the branch
structure differs per scope, and the control — which exercises the same branch chain — is not.

**Verified empirically, and the severity is coverage rather than a live defect.** I temporarily
parametrized it over `["run", "condition", "repeat", "summary"]` and ran it: **4 passed**. So the
guarantee does hold at all four scopes; it was simply never checked at three of them, and a future
change that handed a `.train` at `run`/`condition` under no declared partition would be caught by
nothing. Reverted both edits in place and re-verified by re-running (`6 passed`) and by
`git status --porcelain` (no modification to `tests/`). The fix is one `@pytest.mark.parametrize`
line — the same one the sibling test already carries.

### Minor 1 — `pytest.raises(AssertionError)` with no `match=`

`test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice` accepts any `AssertionError` from
anywhere inside `execute_plan` or `build_plan`. It is correctly attributed today by construction
(`arm_members=None`, so only one assert can fire), but a `match="E-DATA-HOLDOUT-FOLD"` would keep it
attributed if a third assertion is ever added — and would let the same test file distinguish the two
guards once Important 1 is closed.

### Minor 2 — a positional citation inside the new comment

`runner.py:598` — *"That is the inverse of the fold rule three lines below"*. CLAUDE.md § Habits that
cost real work bans locating code or rows by position (*"at least seven instances, wrong twice"*).
Counted from the comment's last line (612) to the `elif` at 616 it is defensible today; counted from
the sentence itself it is fifteen. Either way it is a phrase that any insertion in this branch
falsifies. Name what the sibling branch *does* — "the inverse of the fold branch's `run`/`condition`
hole" — which the very next sentence already does correctly.

### Minor 3 — the reachability comment is true, and stays true past task 18 (no action; recorded as verification)

I checked the one thing that could have made the assertions Critical: whether `command_run` enforces
the two refusals, or whether only `publishable validate` does. It enforces them.
`command_run` calls `validate_config(config_path, c, experiment=experiment)` and returns on
`c.has_errors` before any resolution; `validate.py:633` calls `_check_holdout` (which emits
`E-DATA-HOLDOUT-FOLD` at 2925) and `validate.py:637` calls `_check_evaluation_split_cells` (which
emits `E-DATA-HOLDOUT-CELLS` at 3074). Neither is gated on the command.

The cells check's own gate is `allocation == "between" or bool(isinstance(groups, list) and groups)`,
which is *wider* than `cli`'s `selector_paths(sweep_block)` gate on `arm_members_map` — including
for the `by: ""` case that gate's long comment calls out. So `arm_members_map` cannot be non-`None`
while `holdout_plan` is. The assertions are therefore genuinely unreachable from a config both today
and after task 18 retires `E-DATA-HOLDOUT-UNSUPPORTED`, and a user will meet the diagnostic, never a
bare `AssertionError` traceback.

### Minor 4 — helper duplication and an unused parameter

`_run_one_step` re-implements `_run_one_step_raw`'s eleven-line body rather than calling it and
asserting on the result; `_one_step_plan(tmp_path, ...)` takes `tmp_path` and never uses it (both
call sites already have it, so nothing breaks — it is dead surface in a helper documented "beside its
siblings"). One line each, and both are in the direction of the file's existing helper style.

---

## Things checked and cleared

- **The comment's three document quotes are accurate.** `reference.md:1484` carries *"A `holdout` does
  not raise, because its split is fixed for the whole run"* verbatim;
  `experimental-designs.md:220` carries *"Condition-scoped fitting is right for a fixed holdout and
  wrong for cross-validation"*; `runner.py:159` (`attrition`'s docstring) carries *"does not
  re-derive that narrowing itself, and must not"*. Citing the first as *§ Step scope* is citing the
  parent section rather than *§ A `fold` repeat puts the units out of reach of the wider scopes* —
  accurate, if less precise than the repo's usual.
- **The docstring paragraph claims nothing the code does not do.** "at every scope — `run`,
  `condition`, `repeat` and `summary` alike, not only `repeat` the way a fold's `.train` is" is
  exactly what the branch structure delivers, and is what the parametrized positive test pins.
- **Task 13's `# noqa: F841 -- consumed starting task 14` was correctly removed**, and the variable is
  genuinely read on every path: `holdout_plan` is now the ternary's condition at `cli.py:1594`, which
  is unconditional at that call site. `uv run ruff check .` is clean, which is the direct evidence
  the `noqa` is no longer needed — a stale `noqa` would not itself error, but an unread variable
  would now re-raise `F841`.
- **The documents need no change.** § A fixed holdout split already says "`io.units` then yields the
  test partition and `io.units.train` the training one"; § Errors (`reference.md:980`) already
  documents `io.units` / `io.units.train` "where the declarations put no such list" as
  `ContractError` · `E-STEP-UNITS-UNAVAILABLE`, which is the "raises when undeclared" pin. § The unit
  list is three operations does not restate the raise, and does not need to — it describes the
  contract of the sequence, and the raise has one home.
- **Mutation (c)'s "nothing fails" is honest**, per the brief and per the review framing: no config
  reaches `command_run` with a holdout until task 18, and inventing a test that did would be the
  fixture-that-cannot-exist trap. Task 18's brief owns the pin.

## Method notes

All mutations were reverted by editing the file back in place — never `git checkout --` — with
`__pycache__` removed between runs and each revert verified by **re-running the tests**, plus a final
`git status --porcelain` showing `src/` and `tests/` unmodified. `.superpowers/sdd/.gitignore` was
clobbered to a bare `*` by reading the brief (the standing `scripts/sdd-workspace` behaviour) and was
restored from `HEAD` before writing this file.

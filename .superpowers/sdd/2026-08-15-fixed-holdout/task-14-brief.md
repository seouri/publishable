## Task 14: Runner narrowing — `io.units` is the test partition, `io.units.train` the training one

**Files:** Modify `src/publishable/runner.py`, `src/publishable/cli.py`. Modify (append) `tests/test_runner.py`.

**Interfaces:**
- Consumes: `runner.execute_plan(*, plan, run_dir, input_dir, cfgs, repeats, digest, units=None, max_failed_fraction=None, fold_members=None, arm_members=None, measurements=None)`.
- Produces: one new keyword-only parameter, `holdout_train: "UnitList | None" = None`, and the narrowing that reads it. `cli.command_run` passes `holdout_train=UnitList([u for u in roster if u.key in set(holdout_plan.train)]) if holdout_plan is not None else None`, and `units=` becomes the **test** roster — task 15 names that local.

**The shape, and why it is a `train` list rather than a plan.** `execute_plan` narrows nothing itself and derives nothing: `_cond_roster`'s single-authority argument, which `attrition`'s docstring restates ("does not re-derive that narrowing itself, and must not"). So the runner is handed two rosters and puts one inside the other. Passing the `HoldoutPlan` instead would make the runner a second place that turns keys into units.

**Every scope, not just `repeat`.** § A fixed holdout split: the split is **fixed for the whole run**, so `io.units` is the test partition and `io.units.train` the training one at `run`, `condition`, `repeat` and `summary` scope alike. This is the **inverse** of the fold rule in the same function — `reference.md` says *"A `holdout` does not raise, because its split is fixed for the whole run"*, and `experimental-designs.md` § Cross-validation supplies the other half: *"Condition-scoped fitting is right for a fixed holdout and wrong for cross-validation."* A holdout must therefore **not** take the `elif execution.scope in ("run", "condition"): step_units = None` branch.

**The fold branch is unreachable under a holdout at this commit** — `E-DATA-HOLDOUT-FOLD` (task 6) refuses the pair, and `E-DATA-HOLDOUT-CELLS` (task 8) closes the arm interaction. **Assert it in the code**, and exercise the assertion by calling `execute_plan` directly with both arguments non-`None`. Do **not** write a config-level test for it: no config can instantiate that seam, and a test claiming to would be the "seam named in the brief and instantiated by no fixture" trap. Write the comment as what is true at this commit, naming the code that closes it.

**Arm narrowing needs no interaction.** `arm_members` comes from `sweep.groups`, which task 8 refuses beside a holdout, so `arm_members is None` whenever `holdout_train is not None`. The assertion covers that too.

- [ ] **Step 1: Write the failing test** — append to `tests/test_runner.py`:

```python
_UNITS_RECORDING_STEP_SOURCE = """\
from publishable import BaseStep


class Step(BaseStep):
    scope = "{scope}"

    def run(self, cfg, io):
        io.write("seen.json", {{
            "test": [u.key for u in io.units],
            "train": [u.key for u in io.units.train],
        }})
        return {{"n": len(io.units)}}
"""


@pytest.mark.parametrize("scope", ["run", "condition", "repeat", "summary"])
def test_a_holdout_narrows_io_units_at_every_scope(tmp_path, scope):
    """§ A fixed holdout split: the split is fixed for the whole run, so
    `io.units` is the test partition and `io.units.train` the training one at
    EVERY scope — the inverse of the fold rule in the same function, which
    hands `None` at `run` and `condition`.

    All four scopes are parametrized because the fold branch's `run`/
    `condition` special case sits three lines away, and a narrowing written
    inside it would pass a `repeat`-only test."""
    roster = _runner_roster(10)
    train = UnitList([u for u in roster if u.key in {"u0", "u1", "u2", "u3", "u4",
                                                     "u5", "u6", "u7"}])
    test = UnitList([u for u in roster if u.key in {"u8", "u9"}])
    seen = _run_one_step(
        tmp_path, scope=scope, units=test, holdout_train=train,
        source=_UNITS_RECORDING_STEP_SOURCE,
    )
    assert seen["test"] == ["u8", "u9"]
    assert seen["train"] == ["u0", "u1", "u2", "u3", "u4", "u5", "u6", "u7"]


def test_without_a_holdout_train_still_raises_at_every_scope(tmp_path):
    """The control, and it must produce something: with `holdout_train=None`
    and no fold, `io.units` is the whole roster and `io.units.train` raises —
    the shape task 1 pinned end to end. A narrowing written one branch too wide
    would hand a train list to a run that declared no partition."""
    roster = _runner_roster(10)
    result = _run_one_step_raw(tmp_path, scope="repeat", units=roster, source=
                               _UNITS_RECORDING_STEP_SOURCE)
    assert result.status == "failed"
    assert "E-STEP-UNITS-UNAVAILABLE" in (result.error or "")


def test_a_holdout_beside_a_fold_is_a_core_defect_not_a_silent_choice(tmp_path):
    """No CONFIG can reach this: `E-DATA-HOLDOUT-FOLD` refuses the pair at
    validate time, and `E-DATA-HOLDOUT-CELLS` closes the arm interaction. So
    the seam is exercised by calling `execute_plan` directly with both
    arguments non-`None`, rather than by a fixture that cannot exist — naming a
    seam is not testing it.

    An assertion rather than a silent precedence: two answers to "which units
    is this metric over?" is exactly what the refusal exists to prevent, and if
    it ever stops preventing it, this must be a crash and not a guess."""
    roster = _runner_roster(10)
    with pytest.raises(AssertionError):
        execute_plan(
            plan=_one_step_plan(tmp_path, scope="repeat"),
            run_dir=tmp_path / "run", input_dir=tmp_path / "in",
            cfgs={}, repeats=[], digest="sha256:aaa",
            units=roster,
            holdout_train=UnitList(list(roster)[:5]),
            fold_members={"fold0": frozenset({"u0"})},
        )
```

  `_runner_roster`, `_run_one_step`, `_run_one_step_raw` and `_one_step_plan` are the helpers this file already uses to drive `execute_plan` without a `cli` run — **read `tests/test_runner.py` first and reuse whatever it has** rather than adding four new ones; if a helper does not exist, add the smallest one that does the job and document it beside its siblings.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_runner.py -k "holdout_narrows or without_a_holdout_train or holdout_beside_a_fold" -x`. The first fails on the unknown `holdout_train` keyword; the control passes already, which is why its own assertion is on a produced failure and not on an absence.

- [ ] **Step 3: Implement** — in `src/publishable/runner.py`, add the parameter to `execute_plan`'s signature after `fold_members`:

```python
    holdout_train: "UnitList | None" = None,
```

  and replace the no-fold branch of the narrowing:

```python
        if fold_members is None or scoped_units is None:
            step_units = scoped_units
```

  with

```python
        if fold_members is None or scoped_units is None:
            # A `data.units.holdout` is fixed for the WHOLE run, so it narrows
            # at every scope — `run`, `condition`, `repeat` and `summary`
            # alike. That is the inverse of the fold rule three lines below,
            # and deliberately: `reference.md` § Step scope says "a `holdout`
            # does not raise, because its split is fixed for the whole run",
            # and `experimental-designs.md` § Cross-validation says
            # "condition-scoped fitting is right for a fixed holdout and wrong
            # for cross-validation". A holdout that took the fold branch's
            # `run`/`condition` hole would hand `None` to exactly the step a
            # holdout exists to let fit.
            #
            # `units` is already the TEST partition when a holdout is declared
            # — `cli.command_run` narrowed it at the call site, `_cond_roster`'s
            # single-authority rule, which `attrition`'s own docstring restates
            # ("does not re-derive that narrowing itself, and must not"). This
            # function turns two rosters into one `UnitList`; it derives
            # neither.
            step_units = scoped_units
            if holdout_train is not None:
                step_units = UnitList(list(scoped_units), train=holdout_train)
```

  and add the assertion at the top of `execute_plan`'s body, before the loop:

```python
    # Two evaluation splits is two answers to "which units is this metric
    # over?", which is exactly what `validate` refuses. **No config can reach
    # this at this commit**: `E-DATA-HOLDOUT-FOLD` refuses `holdout` beside a
    # `{kind: fold}` level, and `E-DATA-HOLDOUT-CELLS` refuses a holdout beside
    # the group axis `arm_members` comes from. So this is an assertion about
    # core's own callers rather than about a config — and it is an assertion
    # rather than a silent precedence because if either refusal ever stops
    # holding, a crash here is what makes that visible instead of a partition
    # chosen by whichever branch happened to be written first.
    assert holdout_train is None or fold_members is None, (
        "a holdout and a fold repeat both narrow the roster; `validate` refuses the "
        "pair as `E-DATA-HOLDOUT-FOLD`"
    )
    assert holdout_train is None or arm_members is None, (
        "a holdout beside a group axis is refused as `E-DATA-HOLDOUT-CELLS`"
    )
```

  and extend `execute_plan`'s docstring with a paragraph naming `holdout_train` and stating that `units` is the test partition when it is given.

  Then in `src/publishable/cli.py`, pass it at the `execute_plan` call:

```python
            holdout_train=(
                UnitList([u for u in roster if u.key in set(holdout_plan.train)])
                if holdout_plan is not None
                else None
            ),
```

  Leave `units=roster` exactly as it is — **task 15 owns that line**, and changing both here would make the denominator fix untestable as a change of its own.

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's two pins must still pass — they are the baseline this task is most likely to move), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/runner.py`, move the `if holdout_train is not None:` narrowing inside `elif execution.scope == "repeat":`. `test_a_holdout_narrows_io_units_at_every_scope` must **FAIL** for the `run`, `condition` and `summary` rows and pass for `repeat`. Revert in place; re-run.

  (b) Change `step_units = UnitList(list(scoped_units), train=holdout_train)` to `step_units = UnitList(list(holdout_train), train=holdout_train)`. All four rows must **FAIL** on `seen["test"] == ["u8", "u9"]`. Revert in place; re-run.

  (c) In `src/publishable/cli.py`, change the `holdout_train=` expression to `holdout_train=None`. Run `uv run pytest`. Nothing fails, **and that is the honest result at this commit**: no config can declare a holdout, so the `cli` wiring has no test until task 18. Record this in the commit message, and note that task 18's end-to-end pin is what closes it — do not invent a test that reaches `command_run` with a holdout, because `validate` refuses one.

- [ ] **Step 6: Commit** — `feat: a holdout narrows io.units to the test partition at every scope`.

---


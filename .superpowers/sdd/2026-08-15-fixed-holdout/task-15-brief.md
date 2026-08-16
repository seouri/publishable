## Task 15: The denominators — six sites narrowed, two deliberately not

**Files:** Modify `src/publishable/cli.py`. Modify (append) `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._condition_counts`, `cli._condition_report_by_levels`, `cli._condition_beside_n`, `cli._compute_vs_baseline`, `cli._compute_declared_contrasts`, `runner.execute_plan`, all called from `command_run`.
- Produces:

```python
def _evaluation_roster(
    roster: "UnitList | None", holdout: "HoldoutPlan | None"
) -> "UnitList | None":
```

  and one `eval_roster = _evaluation_roster(roster, holdout_plan)` local in `command_run`, passed at **six** call sites.

**This is the item most likely to ship wrong and it gets the sharpest fixture.** `runner.attrition` computes `handed = keys` — the whole roster it was given — when `fold_members is None`, and returns `resolved = len(handed)`, `failed = len(handed) - len(completed) - len(ineligible)`. Under a holdout with no narrowing, **every training unit lands in `failed`**: handed out, recording nothing, neither completed nor skipped.

**The six sites, named.** In `command_run`, replace `roster` with `eval_roster` at exactly these and nowhere else:

1. `execute_plan(..., units=roster, ...)` — which fixes `max_failed_fraction` and `_units_failed_anywhere` **for free**: `execute_plan` computes `resolved = len(units)` on the outer roster, so today a `0.2` holdout over 240 divides at most 48 possible failures by 240 and the guard fires at five times the declared threshold, in the direction of not firing.
2. `_condition_beside_n(beside_n, roster, cond.index, arm_members_map)`.
3. `_condition_counts(results, roster, step_name, cond.index, arm_members_map, ...)`.
4. `_condition_report_by_levels(roster, cond.index, arm_members_map, attribute)`.
5. `_compute_vs_baseline(..., roster=roster, ...)`.
6. `_compute_declared_contrasts(..., roster=roster, ...)`.

Site 5 and 6 are what reach `units_matching(roster, comp.within)`, so a contrast's `within` subgroup is over test units too.

**Two things stay whole-roster, deliberately, and the code must say so.**

- `provenance.units.n` and `provenance.units_hash`. They are the roster's **identity**, not a metric's denominator. A comment at that site must say why `240` there and `48` in a metric's `n` is not a bug — task 2's inference-base ruling written down where a reader meets the number.
- The **key-indexed maps**: `weights` (built `{u.key: ... for u in roster}`), `unit_attributes`, and `resample_strata`. Each is consumed **by key** over the units that completed, so surplus training keys are inert. Narrowing them would be a third answer to which roster is which, for no observable difference. **State this affirmatively in the code**, or an implementer will "complete" the sweep.

**Three figures are holdout-safe by construction and need no change** — verified in the scoping, not assumed: `runner._counts` computes Kish's effective size and the cluster count over the **completed** units (its own docstring: "a df is over the units the interval was computed from"), and `cli`'s `resample_strata`/`clusters` maps are key-indexed. So a whole-roster Kish size never sits beside a test-partition `n`.

**`technical_n` is filed, not fixed.** See Global Constraints. Do not add the withholding.

**No end-to-end test until task 18**, which is why `_evaluation_roster` is a named function: "the fix exists" and "the fix is wired" are otherwise indistinguishable, which is the exact shape of the bug `_condition_counts` was extracted to prevent.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def test_the_evaluation_roster_is_the_test_partition_and_preserves_roster_order():
    """The denominator every metric counts against. Order preserved because
    the roster's order is part of its identity and `report_by`'s per-level
    tables are built by walking it.

    The `None` arm is the no-holdout case and must return the SAME OBJECT, not
    a copy: `_cond_beside_n` decides whether `technical_n` survives by identity
    (`cond_roster is roster`), so returning a copy here would silently withhold
    it from every unswept run."""
    from publishable.units import HoldoutPlan

    roster = _cli_roster(10)
    assert _evaluation_roster(roster, None) is roster
    assert _evaluation_roster(None, None) is None

    plan = HoldoutPlan(
        train=("u3", "u1", "u0", "u2", "u4", "u6", "u5", "u7"),
        test=("u9", "u8"),
        seed=1234,
        strata=(),
    )
    narrowed = _evaluation_roster(roster, plan)
    assert [u.key for u in narrowed] == ["u8", "u9"]
    assert len(narrowed) == 2


def test_the_narrowed_roster_is_what_attrition_counts_against():
    """The composition this task exists for: `attrition` hands out whatever
    roster it is given, so a training unit that recorded nothing lands in
    `failed` unless the roster it sees is already the test partition.

    Asserted through `_condition_counts` — the one function `command_run`
    calls for a condition's counts — rather than through `attrition` directly,
    because `attrition` counting correctly over a roster nobody narrowed is
    the defect, not the fix."""
    roster = _cli_roster(10)
    eval_roster = _evaluation_roster(roster, _HOLDOUT_PLAN_8_2)
    results = _completed_results_for(["u8", "u9"], step_name="step01", cond_index=0)

    whole = _condition_counts(results, roster, "step01", 0, None)
    narrowed = _condition_counts(results, eval_roster, "step01", 0, None)

    # The defect, stated as a number: 8 training units counted as failures.
    assert whole["resolved"] == 10 and whole["failed"] == 8
    # The fix.
    assert narrowed["resolved"] == 2
    assert narrowed["completed"] == 2
    assert narrowed["failed"] == 0
```

  `_HOLDOUT_PLAN_8_2` is a module-level `HoldoutPlan` with `train=("u0",…,"u7")` and `test=("u8","u9")`. `_completed_results_for` builds the `list[ExecutionResult]` `attrition` reads — **read `tests/test_cli.py` and `tests/test_runner.py` first** and reuse whichever helper already constructs those; only add one if neither does.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "evaluation_roster or narrowed_roster_is_what" -x`. Both fail on `ImportError` for `_evaluation_roster`; add it to the import list and re-run. The second then fails on `narrowed["resolved"] == 2`. **Confirm `whole["failed"] == 8` passes before implementing** — that assertion *is* the defect, and seeing it is what stops the fix being written against a fault that was never there.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, add:

```python
def _evaluation_roster(
    roster: "UnitList | None", holdout: "HoldoutPlan | None"
) -> "UnitList | None":
    """The units every denominator counts against — the holdout's **test**
    partition when one is declared, and the same roster object otherwise.

    `reference.md` § A fixed holdout split: "`resolved` is the test partition
    — a 20 % holdout over 240 units reports `resolved: 48`, and the interval is
    over those 48. That's the honest denominator: the training units produced
    no result to generalize from."

    **Without this, every training unit lands in `failed`.** `runner.attrition`
    computes `handed = keys` over whatever roster it is given, and a training
    unit is handed out, records nothing, and is neither completed nor skipped —
    so a 0.2 holdout over 240 would report 192 failures and trip
    `max_failed_fraction` on a run in which nothing failed.

    **The same object, not a copy, when no holdout is declared.**
    `_cond_beside_n` decides whether `technical_n` survives by IDENTITY
    (`cond_roster is roster`), so a copy here would silently withhold it from
    every run in the build.

    Roster order is preserved: it is part of the roster's identity, and
    `_report_by_levels` walks it to build each level's table.

    **What this deliberately does NOT narrow**, and the list is the point
    rather than an omission:

    - `provenance.units.n` and `provenance.units_hash` stay whole-roster. They
      are the roster's identity, not a metric's denominator — which is what
      makes `240` there and `48` in a metric's `n` two true numbers rather than
      a contradiction.
    - The key-indexed maps `command_run` builds over the roster — the
      `weight_by` weights, `unit_attributes`, and `resample_strata` — are
      consumed BY KEY over units that completed, so a surplus training key is
      never looked up. Narrowing them would be a third answer to which roster
      is which for no observable difference.
    - `runner._counts`' Kish size and cluster count are computed over the
      COMPLETED units already (its own docstring: "a df is over the units the
      interval was computed from"), so they are holdout-safe by construction
      and need nothing here.
    """
    if roster is None or holdout is None:
        return roster
    test = set(holdout.test)
    return UnitList([u for u in roster if u.key in test])
```

  and in `command_run`, immediately after `holdout_plan` is realized:

```python
    # One narrowing, six readers. `roster` itself stays whole below this line —
    # `provenance.units.n` and `units_hash` are the roster's identity rather
    # than a metric's denominator, and rebinding the name would narrow every
    # future call site silently, including theirs.
    eval_roster = _evaluation_roster(roster, holdout_plan)
```

  Then change **exactly six** call sites from `roster` to `eval_roster`: `execute_plan(units=...)`, `_condition_beside_n`, `_condition_counts`, `_condition_report_by_levels`, `_compute_vs_baseline(roster=...)`, `_compute_declared_contrasts(roster=...)`.

  Then add a comment at the provenance write site, beside `"units": ...`:

```python
            # **Whole-roster, deliberately, and not the same number a metric's
            # `n` reports.** Under a `data.units.holdout` a metric's
            # `n.resolved` counts the TEST partition — 48 where this says 240
            # — and both are true: this is the identity of the roster the run
            # resolved, which is what `units_hash` pins and what `reproduce`
            # checks, where `n` is the denominator of an estimate. Narrowing
            # this would make the hash cover a subset the config never
            # described.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's pins are the ones to watch: nothing about a no-holdout run may move, and `_evaluation_roster` returning the same object is what guarantees it), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then sweep the six sites by claim: `grep -n "roster" src/publishable/cli.py | grep -n "_condition_\|_compute_\|units=roster"` — every remaining `roster` at those functions must be intentional, and `provenance` must still read `roster`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/cli.py`, change `_evaluation_roster`'s early return to `return UnitList(list(roster)) if roster is not None else None` — a copy rather than the same object. Run `uv run pytest`. `tests/test_cli.py` carries `technical_n` assertions today, so a `measurements`-declaring run with no group axis should now lose its `technical_n` and fail. **If nothing fails, do not add a test to defend the claim** — that would be building the `technical_n` behaviour Global Constraints files and defers. Instead **weaken the docstring**: replace "would silently withhold it from every run in the build" with a statement that `_cond_beside_n` decides by identity and that returning the same object is what keeps this function out of that decision, with no claim about what any current test observes. Either way, revert the mutation in place and re-run.

  (b) Change the narrowing to `test = set(holdout.train)`. Run `uv run pytest tests/test_cli.py -k "evaluation_roster or narrowed_roster_is_what"`. Both must **FAIL**. Revert in place; re-run.

  (c) Revert the `execute_plan(units=eval_roster)` site back to `units=roster`. Run `uv run pytest`. Nothing fails — **the honest result at this commit**, since no config can declare a holdout. Record it in the commit message and note that task 18's `n.resolved` and `max_failed_fraction` pins are what close it.

- [ ] **Step 6: Commit** — `feat: every denominator counts the holdout's test partition`.

---


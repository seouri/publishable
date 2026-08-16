## Task 10: `units.holdout_for`, construction 1 — the unclustered draw and the column read

**Files:** Modify `src/publishable/units.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.holdout_sizes(n, frac) -> tuple[int, int]`, `units.holdout_values_fault(roster, column) -> str | None` and `units.HOLDOUT_LEVELS` (all task 7); `units.arms_of(roster, column, levels)`; `units.ArmPlan`'s shape as the model.
- Produces:

```python
@dataclass(frozen=True)
class HoldoutPlan:
    train: tuple[str, ...]
    test: tuple[str, ...]
    seed: int | None
    strata: tuple[str, ...]


def holdout_for(
    roster: UnitList,
    block: Mapping[str, Any] | None,
    *,
    seed: int,
    clusters: Mapping[str, str] | None = None,
) -> HoldoutPlan:
```

**`seed` is a required keyword argument and this function never derives one.** Task 12 builds `holdout_seed_for` as the single producer, and task 13 composes the two in `cli.command_run`. A function that both draws and derives is two things to get wrong inside one; `_assign_whole_clusters_by_ratio` taking an `rng` rather than a seed is the same separation one level down.

**The single producer, and the reason it is a pure function.** `validate` has to ask "which units are in the test partition" of the same declaration `cli.command_run` asks it of — task 16's `limits.min_clusters` warning is exactly that question — so the draw cannot live in the runner. `assignment_for`'s own docstring makes this argument verbatim for arms and it transfers.

**Fail-closed on the method: an allowlist, not a denylist.** Any method other than the two raises `NotImplementedError`. `validate` already refuses an out-of-enum method (`E-DATA-HOLDOUT-METHOD`), and the allowlist is what stops a *third* method added to `HOLDOUT_METHODS` and to nothing else from validating clean and then silently partitioning.

**At this commit the clustered and stratified paths raise `NotImplementedError`** and task 11 realizes them. Write that message as what is true at this commit — "not realized at this commit" — not as a permanent refusal.

**`by_attribute` records no seed and no strata**, `ArmPlan`'s own convention: it reads a partition the data already holds, so recording a seed would be a false record of a draw that never happened.

**The zero-size refusal is on BOTH sides.** `validate` (task 7) refuses a zero test side, but it does not refuse a zero *train* side: 2 units at `frac: 0.9` apportions `(0, 2)`. Both are refused here, under `E-DATA-HOLDOUT-EMPTY`, `assignment_for`'s own posture — the draw holds the realized sizes and is the last place that can see them.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def _roster(n, **attrs_by_index):
    """`n` units keyed `u0..u{n-1}`, each carrying whatever the caller maps."""
    return UnitList(
        [
            Unit(key=f"u{i}", paths=(),
                 attributes={k: v(i) for k, v in attrs_by_index.items()})
            for i in range(n)
        ]
    )


def test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes():
    """`_apportion` + one shuffle + consecutive slices — `assignment_for`'s
    `random` branch, one declaration over. The realized membership is pinned as
    a literal derived by RUNNING this, not by predicting it: a predicted
    membership that happened to match a wrong construction is how a 13-unit
    apportionment matched a reverse-order mutant by coincidence in an earlier
    slice.

    Fill these two literals in during Step 3 by printing the actual result."""
    plan = holdout_for(_roster(10), {"method": "random", "frac": 0.2}, seed=1234)
    assert len(plan.train) == 8 and len(plan.test) == 2
    assert set(plan.train) | set(plan.test) == {f"u{i}" for i in range(10)}
    assert not set(plan.train) & set(plan.test)
    assert plan.seed == 1234
    assert plan.strata == ()
    # PINNED LITERALS — replace with what the implementation actually returns.
    assert plan.train == ("REPLACE",)
    assert plan.test == ("REPLACE",)


def test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not():
    """Determinism, and the positive companion that keeps it from being
    vacuous: a different seed must give a DIFFERENT partition, or a draw that
    ignored the seed entirely would pass the first assertion alone."""
    a = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    b = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=7)
    c = holdout_for(_roster(20), {"method": "random", "frac": 0.25}, seed=8)
    assert a.test == b.test
    assert a.test != c.test


def test_a_by_attribute_holdout_reads_the_column_and_records_no_draw():
    """Read through `arms_of`, the single authority for a column-read
    partition — so roster order is preserved and set equality is enforced by
    the same function an arm assignment uses. No seed and no strata are
    recorded, `ArmPlan`'s own convention: reading a partition the data holds is
    not drawing one."""
    roster = _roster(10, split=lambda i: "test" if i % 5 == 0 else "train")
    plan = holdout_for(
        roster, {"method": "by_attribute", "from": "split"}, seed=1234
    )
    assert plan.test == ("u0", "u5")
    assert plan.train == ("u1", "u2", "u3", "u4", "u6", "u7", "u8", "u9")
    assert plan.seed is None
    assert plan.strata == ()


def test_a_by_attribute_holdout_over_a_column_that_is_not_the_two_literals_raises():
    """The run-time half of `E-DATA-HOLDOUT-VALUES`, through `arms_of`'s own
    set equality. `validate` refuses this first; the draw refuses it too rather
    than partitioning on whatever it finds."""
    roster = _roster(10, split=lambda i: "A" if i % 2 else "B")
    with pytest.raises(ContractError) as exc:
        holdout_for(roster, {"method": "by_attribute", "from": "split"}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-VALUES"


@pytest.mark.parametrize(
    "n,frac,empty_side",
    [(2, 0.2, "test"), (2, 0.9, "train")],
    ids=["the test side is apportioned none", "the train side is apportioned none"],
)
def test_a_holdout_that_leaves_a_side_empty_raises(n, frac, empty_side):
    """Both sides, because `validate` refuses only the test one: 2 units at
    `frac: 0.9` apportions `(0, 2)` and would fit a model on nothing.
    `assignment_for`'s posture — the draw holds the realized sizes and is the
    last place that can see them."""
    with pytest.raises(ContractError) as exc:
        holdout_for(_roster(n), {"method": "random", "frac": frac}, seed=1)
    assert exc.value.code == "E-DATA-HOLDOUT-EMPTY"
    assert empty_side in str(exc.value)


@pytest.mark.parametrize("method", ["stratified", "", None, "by_attributes"])
def test_an_unknown_holdout_method_raises_rather_than_falling_back(method):
    """An allowlist, not a denylist of the methods that happen to draw today.
    `validate` refuses an out-of-enum method first; this is what stops a THIRD
    method added to `HOLDOUT_METHODS` and to nothing else from validating clean
    and then silently partitioning on a column."""
    with pytest.raises(NotImplementedError):
        holdout_for(_roster(10), {"method": method, "frac": 0.2}, seed=1)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster or by_attribute_holdout or leaves_a_side_empty or unknown_holdout_method" -x`. Every one fails on `ImportError` for `holdout_for`/`HoldoutPlan`; add both to the test module's import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/units.py`, add after `ArmPlan`:

```python
@dataclass(frozen=True)
class HoldoutPlan:
    """`data.units.holdout` **realized** — the two sides as unit keys, plus what
    it took to produce them.

    `ArmPlan`'s sibling and deliberately not the same type: an arm plan is
    `level -> keys` over a declared `levels` tuple, where a holdout's two sides
    are fixed and named, and squeezing one into the other would mean either a
    fabricated axis name or a `levels` field with one legal value.

    - `train` and `test` hold unit keys, never row numbers — a roster that
      gains a unit renumbers rows and would silently repoint every membership
      claim. Every key of the roster appears in exactly one of them.
    - Order is **roster order** under `by_attribute`, which `arms_of` promises,
      and the order the shuffle realized under `random` — recorded rather than
      re-sorted, `ArmPlan`'s own rule, because the record of a draw is the
      draw.
    - `seed` is the seed the draw was realized with, and is `None` under
      `by_attribute`: a method that reads a partition the data already holds
      rather than drawing one, so recording a seed would be a false record of a
      draw that never happened.
    - `strata` is the realized `stratify_by`, in declared order, and is empty
      under `by_attribute` for the reason above and empty under a draw that
      declared none.

    `frozen=True` blocks rebinding an attribute; the two tuples are immutable
    outright, so unlike `ArmPlan.members` there is nothing here a determined
    caller can mutate in place.
    """

    train: tuple[str, ...]
    test: tuple[str, ...]
    seed: int | None
    strata: tuple[str, ...]


def holdout_for(
    roster: UnitList,
    block: Mapping[str, Any] | None,
    *,
    seed: int,
    clusters: Mapping[str, str] | None = None,
) -> HoldoutPlan:
    """`data.units.holdout`, realized — **the single producer** of a
    `HoldoutPlan`.

    A **pure function of its arguments**, `assignment_for`'s reason one
    declaration over: `validate` has to ask "which units are in the test
    partition" of the same declaration `cli.command_run` asks it of — the
    `limits.min_clusters` warning is exactly that question — so the draw cannot
    live in the runner. Two callers, one answer, computed the same way from the
    same inputs.

    **`seed` is required and this function never derives one.** The derivation
    is `holdout_seed_for`'s, and composing them is `cli.command_run`'s: a
    function that both draws and derives is two independent things to get wrong
    inside one, and it would put the derivation out of reach of a test that
    wants to pin a draw against a known seed. The value is recorded on the plan
    under `random` and discarded under `by_attribute`, which draws nothing.

    Dispatches on `block["method"]`, `reference.md` § A fixed holdout split's
    own enum:

    - `by_attribute` reads the two sides out of a column, through `arms_of`
      **unchanged** — that function stays the authority for a column-read
      partition and this one does not re-derive it. The levels it is handed are
      `HOLDOUT_LEVELS`, the fixed `train`/`test` literals, so `arms_of`'s set
      equality in both directions is what refuses a third value, a value naming
      neither, and a literal naming no unit. The refusal goes through
      `holdout_values_fault`, which owns both the verdict and the wording, so
      this raise and `validate._check_holdout`'s collected finding are one
      answer rather than two wrappings of the same raise — `arms_of`'s own
      message names an arm and an axis's declared levels and would send a
      holdout's reader to the wrong section.
    - `random`, unclustered and unstratified, draws one: `holdout_sizes` — the
      same apportionment `validate` approved the `frac` against — then one
      `rng.shuffle` of the whole roster's keys, then two consecutive slices,
      train first. That is `assignment_for`'s `random` branch exactly, and
      deliberately so: one construction, described in one place.
    - **Every other value raises `NotImplementedError`** — an allowlist. Fail
      closed costs nothing, because `validate` already refuses an out-of-enum
      method (`E-DATA-HOLDOUT-METHOD`) before a run reaches here, and it is
      what keeps a *third* method added to `validate.HOLDOUT_METHODS` and to
      nothing else from validating clean and then silently partitioning.

    **A `clusters` mapping and a non-empty `stratify_by` are not realized at
    this commit** and raise `NotImplementedError` rather than being silently
    ignored — an ignored `stratify_by` is a split `validate` called stratified
    and the draw balanced on nothing. `clusters` is a parameter anyway, for
    `assignment_for`'s reason: a caller that already has to hold the cluster
    map must not be told the signature changed under it.

    **Both sides are refused empty**, under `E-DATA-HOLDOUT-EMPTY`.
    `validate._check_holdout` refuses a zero *test* side from the declaration
    and the roster size, and does not refuse a zero *train* side — 2 units at
    `frac: 0.9` apportions `(0, 2)`, which would fit a model on nothing. The
    draw holds the realized sizes and is the last place that can see them,
    which is `assignment_for`'s own posture for a zero-size arm.
    """
    block_map: Mapping[str, Any] = block if isinstance(block, Mapping) else {}
    method = block_map.get("method")
    strata = stratum_names(block_map.get("stratify_by"))
    if strata or clusters is not None:
        raise NotImplementedError(
            "a clustered or stratified `data.units.holdout` is not realized at this "
            "commit — the draw that keeps whole clusters on one side, and the one that "
            "balances the split within each stratum, are not built here. Ignoring "
            "either would be a split `validate` called clustered or stratified and the "
            "draw balanced on nothing"
        )
    if method == "by_attribute":
        column = block_map.get("from")
        if not isinstance(column, str) or not column:
            raise NotImplementedError(
                "`data.units.holdout.method: by_attribute` names no column to read the "
                "split out of; `validate` refuses this as `E-DATA-HOLDOUT-FROM`"
            )
        # `holdout_values_fault` computes the verdict AND the wording, so this
        # raise and `validate._check_holdout`'s collected finding are one
        # answer rather than two wrappings of `arms_of` that drift apart.
        fault = holdout_values_fault(roster, column)
        if fault is not None:
            raise ContractError(fault, code="E-DATA-HOLDOUT-VALUES")
        sides = arms_of(roster, column, HOLDOUT_LEVELS)
        return HoldoutPlan(
            train=tuple(u.key for u in sides[HOLDOUT_LEVELS[0]]),
            test=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]),
            seed=None,
            strata=(),
        )
    if method == "random":
        frac = block_map.get("frac")
        if not isinstance(frac, (int, float)) or isinstance(frac, bool):
            raise NotImplementedError(
                "`data.units.holdout.method: random` declares no usable `frac`; "
                "`validate` refuses this as `E-DATA-HOLDOUT-FRAC`"
            )
        train_size, test_size = holdout_sizes(len(roster), float(frac))
        if train_size == 0 or test_size == 0:
            side = "train" if train_size == 0 else "test"
            raise ContractError(
                f"`data.units.holdout.frac: {frac}` over {len(roster)} resolved units "
                f"apportions the {side} side zero of them. Every split needs both "
                "sides — the training side has nothing to fit on, or the test side has "
                "nothing to report over; widen or narrow `frac`, or resolve a larger "
                "roster",
                code="E-DATA-HOLDOUT-EMPTY",
            )
        shuffled = [unit.key for unit in roster]
        random.Random(seed).shuffle(shuffled)
        return HoldoutPlan(
            train=tuple(shuffled[:train_size]),
            test=tuple(shuffled[train_size:]),
            seed=seed,
            strata=(),
        )
    raise NotImplementedError(
        f"`data.units.holdout.method: {method!r}` is not realized here — the methods "
        f"this build draws are {', '.join(HOLDOUT_METHODS_REALIZED)}. `validate` "
        "refuses an out-of-enum method as `E-DATA-HOLDOUT-METHOD` before a run reaches "
        "this, and an allowlist is what keeps a method added to that enum and to "
        "nothing else from validating clean and then partitioning on something core "
        "never drew"
    )
```

  where `HOLDOUT_METHODS_REALIZED = ("random", "by_attribute")` is declared beside `HoldoutPlan` — **not** imported from `validate`, which imports `units` and not the reverse.

  Then fill in the two `"REPLACE"` literals in `test_an_unclustered_holdout_cuts_the_shuffled_roster_at_the_apportioned_sizes` by running the function and printing `plan.train` and `plan.test`. Paste what it actually returns.

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, swap the slices: `train=tuple(shuffled[train_size:]), test=tuple(shuffled[:train_size])`. Run `uv run pytest tests/test_units.py -k holdout_cuts`. It must **FAIL** on the pinned literals *and* on `len(plan.train) == 8`. Revert in place; re-run.

  (b) Delete the `random.Random(seed).shuffle(shuffled)` line entirely. Run `uv run pytest tests/test_units.py -k "holdout_cuts or same_seed_and_roster"`. `test_the_same_seed_and_roster_draw_the_same_holdout_and_a_different_seed_does_not` must **FAIL** on `a.test != c.test`, and `holdout_cuts` must **FAIL** on its pinned literals. **Both must fail** — if only the pinned-literal test fails, the determinism test cannot see the seed and needs a stronger fixture. Revert in place; re-run.

  (c) Change `arms_of(roster, column, HOLDOUT_LEVELS)` to `arms_of(roster, column, tuple(reversed(HOLDOUT_LEVELS)))`. Run `uv run pytest tests/test_units.py -k by_attribute_holdout_reads`. It must **FAIL** — and check the two branches can differ before believing it: `arms_of` returns a mapping keyed by level, and this function indexes it by `HOLDOUT_LEVELS[0]`/`[1]` rather than by position, so reversing the argument alone is a **no-op** and this mutation is *rejected*. Use instead: change the return to `train=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]), test=tuple(u.key for u in sides[HOLDOUT_LEVELS[0]])`. `test_a_by_attribute_holdout_reads_the_column_and_records_no_draw` must **FAIL**. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: units.holdout_for — the unclustered draw and the column read`.

---


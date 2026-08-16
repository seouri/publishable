## Task 13: Realize the holdout once, in `cli.command_run`

**Files:** Modify `src/publishable/cli.py`. Modify (append) `tests/test_cli.py`.

**Interfaces:**
- Consumes: `units.holdout_for(roster, block, *, seed, clusters=None) -> HoldoutPlan`; `units.holdout_seed_for(block, digest, roster) -> int`; `command_run`'s locals `units_decl`, `roster`, `digest`, `clusters`.
- Produces:

```python
def _resolved_holdout(
    units_decl: dict[str, Any] | None,
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None,
) -> "HoldoutPlan | None":
```

  and one `holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters)` in `command_run`, placed immediately after `group_axes` is resolved and **before** `build_allocation_document` and `execute_plan`.

**Realized once, and the one object is what everything downstream is handed.** `build_allocation_document`'s own docstring makes this argument for arms and it transfers verbatim: it used to be handed the roster and re-derive the partition through `arms_of`, and *"under a draw that second derivation is a second draw, and 'provably identical' is not something two calls can be made to promise — only not calling twice can."* A holdout under `method: random` is a draw. So the partition the runner runs, the partition the denominators count, and the partition `allocation.json` claims must be **the same object**, not three answers that happen to agree.

**No end-to-end test exists for this task and will not until task 18.** `E-DATA-HOLDOUT-UNSUPPORTED` still refuses every declaration, so no config reaches `command_run`. This task tests `_resolved_holdout` **directly**, which is exactly why the realization is extracted into a named function rather than written inline — the same move `_condition_counts` made when "the fix exists" and "the fix is wired" could not otherwise be told apart. Task 18's end-to-end pins close the remaining gap.

**A holdout beside a group axis is refused at this commit** (`E-DATA-HOLDOUT-CELLS`, task 8), so `clusters` is the only other partition input this function needs and `group_axes` is not one of them.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
def _cli_roster(n, **attrs_by_index):
    from publishable.units import Unit, UnitList

    return UnitList(
        [
            Unit(key=f"u{i}", paths=(),
                 attributes={k: v(i) for k, v in attrs_by_index.items()})
            for i in range(n)
        ]
    )


def test_the_holdout_is_realized_once_and_returns_none_when_undeclared():
    """`None` for every shape that declares no split — the gate
    `build_allocation_document`'s "both absent" rule and the runner's narrowing
    both read. An empty block is undeclared, matching `_check_holdout`'s own
    gate, so a `holdout: {}` partitions nothing rather than drawing an
    unmethodded split."""
    roster = _cli_roster(10)
    for decl in (None, {}, {"holdout": None}, {"holdout": {}}):
        assert _resolved_holdout(decl, roster, "sha256:aaa", None) is None
    # No roster is also `None`: there is nothing to partition.
    assert _resolved_holdout(
        {"holdout": {"method": "random", "frac": 0.2}}, None, "sha256:aaa", None
    ) is None


def test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map():
    """One realization composing `holdout_seed_for` and `holdout_for` — and it
    must be the SAME answer either helper gives on its own, or the run and the
    record would be two draws.

    The clustered arm is asserted separately because `clusters` reaching
    `holdout_for` is a threading that a composition ignoring the argument would
    pass every unclustered assertion for."""
    from publishable.units import holdout_for, holdout_seed_for

    roster = _cli_roster(12, animal=lambda i: f"a{i // 2}")
    decl = {"holdout": {"method": "random", "frac": 0.5}}
    plan = _resolved_holdout(decl, roster, "sha256:aaa", None)
    seed = holdout_seed_for(decl["holdout"], "sha256:aaa", roster)
    assert plan == holdout_for(roster, decl["holdout"], seed=seed)
    assert plan.seed == seed

    clusters = {f"u{i}": f"a{i // 2}" for i in range(12)}
    clustered = _resolved_holdout(decl, roster, "sha256:aaa", clusters)
    assert clustered == holdout_for(roster, decl["holdout"], seed=seed, clusters=clusters)
    # The positive companion for "the cluster map was threaded": the two
    # realizations differ, so a composition dropping `clusters` is visible.
    assert set(clustered.test) != set(plan.test)


def test_a_pinned_holdout_seed_reaches_the_realization():
    """A pin is the deliberate act, so it has to survive the composition —
    a realization deriving the seed unconditionally would pass every other
    assertion in this file."""
    roster = _cli_roster(10)
    plan = _resolved_holdout(
        {"holdout": {"method": "random", "frac": 0.2, "seed": 4321}},
        roster, "sha256:aaa", None,
    )
    assert plan.seed == 4321
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k "realized_once or realized_holdout_uses or pinned_holdout_seed_reaches" -x`. All fail on `ImportError` for `_resolved_holdout`; add it to `tests/test_cli.py`'s `publishable.cli` import list and re-run.

- [ ] **Step 3: Implement** — in `src/publishable/cli.py`, add `holdout_for`, `holdout_seed_for` and `HoldoutPlan` to the `publishable.units` import list, and add beside `_resolved_group_axes`:

```python
def _resolved_holdout(
    units_decl: dict[str, Any] | None,
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None,
) -> "HoldoutPlan | None":
    """`data.units.holdout`, realized **once per run** — or `None` when the
    design declares none.

    The one object handed to the runner's narrowing, to the denominators, and
    to `build_allocation_document`. `build_allocation_document`'s own docstring
    makes the argument for arms and it transfers verbatim: it used to be handed
    the roster and re-derive the partition, and *"under a draw that second
    derivation is a second draw, and 'provably identical' is not something two
    calls can be made to promise — only not calling twice can."* A `method:
    random` holdout is a draw, so the partition the run executes, the
    denominators it reports against, and the membership `allocation.json`
    claims are the same object rather than three answers that happen to agree.

    `None` for four shapes, and they are one shape: an absent `data.units`, an
    absent `holdout`, a `holdout: null`, and a `holdout: {}`. The last is
    `_check_holdout`'s own gate — an empty block declares nothing and
    partitions nothing — so the two readings of "is a holdout declared" agree
    rather than one drawing an unmethodded split the other validated as absent.
    `None` for a roster that did not resolve too: there is nothing to partition,
    and `_check_units` has already reported why.

    `clusters` is `cli.command_run`'s single cluster map, the same one the fold
    partition and the arm draw are handed — not re-derived here, `clusters_of`
    being the single authority. `group_axes` is deliberately not a parameter: a
    holdout beside a group axis is refused at this commit as
    `E-DATA-HOLDOUT-CELLS`, so there is no cell structure for a split to be
    drawn inside of.
    """
    if roster is None:
        return None
    block = (units_decl or {}).get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    return holdout_for(
        roster, block, seed=holdout_seed_for(block, digest, roster), clusters=clusters
    )
```

  and in `command_run`, immediately after the `group_axes = _resolved_group_axes(...)` line:

```python
    # Realized here, once, and before anything reads it — the runner's
    # narrowing, the denominators and `allocation.json` are all handed this one
    # object. See `_resolved_holdout` for why not calling twice is the only
    # thing that can promise the run and the record agree.
    holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters)
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. `holdout_plan` is unused at this commit and `ruff` will say so — that is correct and is what task 14 consumes; if the lint rule is fatal, add the consumption in task 14 and keep this commit's line as the assignment it is, marking it with the narrowest possible suppression and a comment naming what consumes it next.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/cli.py`, change `if not isinstance(block, dict) or not block:` to `if not isinstance(block, dict):`. `test_the_holdout_is_realized_once_and_returns_none_when_undeclared` must **FAIL** on the `{"holdout": {}}` row — `holdout_for` raises `NotImplementedError` for a methodless block. Revert in place; re-run.

  (b) Drop the `clusters=clusters` argument from the `holdout_for` call. `test_the_realized_holdout_uses_the_derived_seed_and_the_cluster_map` must **FAIL** on its clustered assertion. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: realize the holdout once in command_run`.

---


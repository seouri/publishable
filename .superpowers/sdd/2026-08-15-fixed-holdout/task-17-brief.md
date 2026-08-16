## Task 17: `allocation.json` gains its fourth key

**Files:** Modify `src/publishable/artifacts.py`, `src/publishable/cli.py`. Modify (append) `tests/test_artifacts.py`.

**Interfaces:**
- Consumes: `artifacts.build_allocation_document(group_axes: Mapping[str, ArmPlan]) -> dict[str, Any] | None`; `artifacts.allocation_hash(document) -> str`.
- Produces:

```python
def build_allocation_document(
    group_axes: Mapping[str, "ArmPlan"], holdout: "HoldoutPlan | None" = None
) -> dict[str, Any] | None:
```

  called from `command_run` as `build_allocation_document(group_axes, holdout_plan)`.

**The document shape, settled in task 2 — read § `allocation.json` before writing code.** The `holdout` block is **self-contained**: `train` and `test` always, `seed` only when the split was drawn, `strata` only when non-empty. The top-level `seed`/`strata` are keyed by *axis name* and a holdout is not an axis, so hanging it off a fabricated key would invite a reader to index it as one.

**The "both absent" gate widens.** `if not group_axes: return None` becomes "neither an assignment nor a holdout" — § The other files a run writes says the file is "present when either is declared", and a holdout-only run must write it.

**It records; it does not recompute.** The function takes **no roster**, and that stays true: with nothing to read membership from, it cannot become a second producer of it. The `HoldoutPlan` arrives realized from `_resolved_holdout`.

**`allocation_hash` needs no change**, and its docstring already rules out a `holdout_hash`: it canonicalizes whatever document it is handed. Do not add one.

**Provenance follows for free**: `provenance.allocation`/`allocation_hash` are already `None` exactly when `alloc_doc` is `None`, so widening the gate makes a holdout-only run record both. The comment at that site naming "`holdout` is never in this build's document at all" is **false the moment this lands** and is fixed here, not left to task 19.

- [ ] **Step 1: Write the failing test** — append to `tests/test_artifacts.py`:

```python
def test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block():
    """§ `allocation.json`: the top-level `seed`/`strata` are keyed by AXIS and
    a holdout is not an axis, so its own two travel inside its block. `train`
    and `test` are unit keys, never row numbers — a roster that gains a unit
    renumbers rows and would silently repoint every membership claim."""
    plan = HoldoutPlan(train=("P2", "P7"), test=("P11", "P19"), seed=3310985422,
                       strata=("label",))
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {
        "train": ["P2", "P7"], "test": ["P11", "P19"],
        "seed": 3310985422, "strata": ["label"],
    }
    # The axis-keyed blocks stay present and empty, the shape § `allocation.json`
    # prints for a run whose every axis reads a column.
    assert doc["seed"] == {} and doc["strata"] == {} and doc["arms"] == {}


def test_a_read_holdout_records_neither_seed_nor_strata():
    """`ArmPlan`'s own convention for `by_attribute`, one declaration over:
    reading a partition the data already holds is not drawing one, so a `seed`
    would be a false record of a draw that never happened and a `strata` would
    describe how a draw was balanced when none was.

    Asserted as absent KEYS rather than as `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'"."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=None, strata=())
    doc = build_allocation_document({}, plan)
    assert doc["holdout"] == {"train": ["P2"], "test": ["P11"]}


def test_a_drawn_unstratified_holdout_records_its_seed_and_no_strata():
    """The third arm, which the two above cannot distinguish between: a drawn
    split with no `stratify_by` carries a seed and no strata, so `strata` is
    omitted for EMPTINESS rather than for the method."""
    plan = HoldoutPlan(train=("P2",), test=("P11",), seed=7, strata=())
    assert build_allocation_document({}, plan)["holdout"] == {
        "train": ["P2"], "test": ["P11"], "seed": 7,
    }


def test_the_document_is_written_when_either_partition_is_declared():
    """§ The other files a run writes: "present when either is declared". The
    four combinations, because a gate reading only one of the two passes three
    of them."""
    arms = {"arm": ArmPlan(levels=("a", "b"),
                           members={"a": ("P1",), "b": ("P2",)},
                           seed=None, strata=())}
    plan = HoldoutPlan(train=("P1",), test=("P2",), seed=7, strata=())
    assert build_allocation_document({}, None) is None
    assert build_allocation_document(arms, None) is not None
    assert build_allocation_document({}, plan) is not None
    both = build_allocation_document(arms, plan)
    assert both is not None and "arms" in both and "holdout" in both


def test_the_allocation_hash_covers_the_holdout_block():
    """`allocation_hash` canonicalizes whatever document it is handed, so the
    holdout's membership is covered without a `holdout_hash` — which
    `allocation_hash`'s own docstring rules out.

    The positive companion is the inequality: two documents differing only in
    which units were held out must hash differently, or the coverage claim is
    empty."""
    a = build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    b = build_allocation_document({}, HoldoutPlan(("P2",), ("P1",), 7, ()))
    assert allocation_hash(a) != allocation_hash(b)
    assert allocation_hash(a) == allocation_hash(
        build_allocation_document({}, HoldoutPlan(("P1",), ("P2",), 7, ()))
    )
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_artifacts.py -k "holdout or either_partition or allocation_hash_covers" -x`. All fail: `build_allocation_document` takes one argument today. Add `HoldoutPlan` to the test module's imports.

- [ ] **Step 3: Implement** — in `src/publishable/artifacts.py`, widen the signature and the gate, and replace the **`holdout` is never written here** paragraph:

```python
def build_allocation_document(
    group_axes: Mapping[str, "ArmPlan"], holdout: "HoldoutPlan | None" = None
) -> dict[str, Any] | None:
```

  Replace

```python
    **`holdout` is never written here.** `E-DATA-HOLDOUT-UNSUPPORTED`
    refuses every `data.units.holdout` declaration in this build, so there
    is never a holdout partition to record; the key is omitted entirely
    rather than written `null`, matching `manifest/input.json`'s own
    "absent rather than null, so 'not hashed' can't be misread as 'hashed
    to nothing'" — here, "no holdout key" rather than "a holdout of
    nothing." H3d adds the key once that refusal lifts.
```

  with

```python
    **`holdout` is the fourth key, and it is self-contained.** `train` and
    `test` hold unit keys, in the plan's own order — roster order under
    `by_attribute`, the shuffle's order under a draw — recorded rather than
    re-sorted, for the reason `arms` is. Its `seed` appears only when the split
    was DRAWN and its `strata` only when non-empty, `arms`' own rule one
    declaration over: a `by_attribute` holdout reads a partition the data
    already holds, so a seed would be a false record of a draw that never
    happened and a `stratify_by` would describe how a draw was balanced when
    none was. Both are omitted rather than written `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'".

    **Unlike the axis-keyed `seed` and `strata`, the holdout's own two live
    INSIDE its block.** Those two are keyed by axis name and a holdout has no
    axis name; hanging it off a fabricated key would invite a reader to index
    it as one, and `reference.md` § `allocation.json` prints the shape this
    produces.

    **This function still takes no roster**, and the holdout arrives realized
    for the same reason the arms do: `cli._resolved_holdout` draws it once, and
    a second draw here would be a second allocation.
```

  Then the gate and the payload:

```python
    if not group_axes and holdout is None:
        return None
    arms = {
        axis: {level: list(keys) for level, keys in plan.members.items()}
        for axis, plan in group_axes.items()
    }
    seed = {axis: plan.seed for axis, plan in group_axes.items() if plan.seed is not None}
    strata = {axis: list(plan.strata) for axis, plan in group_axes.items() if plan.strata}
    document: dict[str, Any] = {"seed": seed, "arms": arms, "strata": strata}
    if holdout is not None:
        block: dict[str, Any] = {"train": list(holdout.train), "test": list(holdout.test)}
        if holdout.seed is not None:
            block["seed"] = holdout.seed
        if holdout.strata:
            block["strata"] = list(holdout.strata)
        document["holdout"] = block
    return document
```

  Update the `if not group_axes:` gate comment above it: the silent-skip argument it makes is about `group_axes` only and stays true; add one sentence saying a `holdout` reaches this already realized and carries no such shape hazard.

  Then in `src/publishable/cli.py`, change the call to `build_allocation_document(group_axes, holdout_plan)` and rewrite the comment above it, replacing

```python
        # `None` when
        # `group_axes` is empty — no arm assignment resolved for this run —
        # matching "present when either [an arm assignment or a holdout] is
        # declared"; `holdout` is never in this build's document at all
        # (`E-DATA-HOLDOUT-UNSUPPORTED` refuses every declaration of it).
```

  with

```python
        # `None` only when NEITHER partition resolved — no arm assignment and
        # no `data.units.holdout` — matching "present when either is declared".
        # `holdout_plan` is `_resolved_holdout`'s single realization, the same
        # object the runner narrowed and the denominators counted against, so
        # the membership this file claims is the membership the run used rather
        # than a second draw that happens to agree.
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest` (task 1's `allocation.json` absence pin is the one to watch — a run declaring neither must still write nothing), then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then check the document against § `allocation.json`'s printed example key by key: `seed`, `arms`, `holdout`, `strata` — the example's insertion order is for a human reader and `json.dumps(..., indent=2)` preserves it, so confirm the written file's key order matches what task 2 printed, or fix one of the two.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/artifacts.py`, change the gate back to `if not group_axes:`. `test_the_document_is_written_when_either_partition_is_declared` must **FAIL** on the holdout-only row. Revert in place; re-run.

  (b) Change `if holdout.seed is not None:` to `block["seed"] = holdout.seed` unconditionally. `test_a_read_holdout_records_neither_seed_nor_strata` must **FAIL**. Revert in place; re-run.

  (c) Change `block["train"]`/`block["test"]` to `list(holdout.test)`/`list(holdout.train)` — swapped. `test_the_allocation_hash_covers_the_holdout_block`'s **inequality** assertion must still pass (both documents move together), and `test_a_drawn_holdout_writes_its_own_seed_and_strata_inside_its_block` must **FAIL**. Both outcomes are the point: a hash test cannot see a swap that is symmetric across its two inputs, which is why the explicit membership assertion exists.

- [ ] **Step 6: Commit** — `feat: allocation.json records the realized holdout split`.

---


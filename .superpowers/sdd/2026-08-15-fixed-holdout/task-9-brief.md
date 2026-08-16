## Task 9: `holdout.from`'s constant-column accessor

**Files:** Modify `src/publishable/units.py`, `src/publishable/validate.py`. Modify (append) `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.CONSTANT_COLUMN_RULES: dict[str, tuple[str, str]]`; `units.collapse_measurements(units, by, collapse, constant=None)`; `units._assign_constant_columns(assign_decl) -> dict[str, str]`.
- Produces: `units._holdout_constant_column(holdout_decl: Any) -> dict[str, str]`, returning at most one entry keyed `holdout.from`; a `CONSTANT_COLUMN_RULES` entry keyed `holdout` (bare, no dot) carrying `E-DATA-HOLDOUT-VARIES`; and its place in `resolve_units`' documented severity ordering.

**Why this exists at all, in the code's own words.** Two comments in `units.py` say so in the present tense at `78bb794`: *"`holdout.from` still is not [reachable]"* and *"`holdout.from` is not reachable through this registry today… nothing in this task builds one."* `CONSTANT_COLUMN_RULES` is what makes `collapse_measurements` refuse a unit whose declared column is **not constant across the rows collapsing into it**. Under `data.units.measurements`, a `by_attribute` holdout reading a column that disagrees between two rows of one unit would silently take whichever row the collapse kept — **a unit assigned to train or test by an accident of row order.** `design-principles.md` § Core vs. plugin lists `holdout.from` beside `assign.from` as parallel namers of an input field, so this is not an invented requirement.

**Why an accessor and not a flat registry entry.** `resolve_units`' flat comprehension indexes `units_decl` by the registry key and filters on `isinstance(..., str)`, so a mapping is dropped before the registry is consulted — verified by probe in an earlier slice. `holdout` is a mapping with its own `from`, so it needs an accessor, the same shape `_assign_constant_columns` is for `assign` but returning **at most one** entry rather than one per axis.

**Gated on `method == "by_attribute"`**, matching `_assign_constant_columns`' own gate and for its reason: under `random` the split is drawn, no column is read, and a `from` that means nothing there is already `E-DATA-HOLDOUT-NO-DRAW`'s finding — raising a run-time `-VARIES` over a column no draw reads would refuse a config no check approves, in the opposite direction.

**The severity ordering, stated rather than left to dict-building order.** `resolve_units` builds `constant` in a fixed order and `collapse_measurements` stops at the first declaration that raises. `assign` is documented as the worst (it decides which *condition* a unit is measured in). This task inserts `holdout` **after `assign` and before the flat pair**, and the entry's docstring must say what that does and does not claim: `holdout.from` and `cluster_by` say the *same* thing about the damage — which side of a split the unit lands on — so the order between them is fixed deterministically here rather than left to an accident, and is **not** a claim that one is worse than the other. `weight_by` stays last, which is the documented ordering.

**Every key in `CONSTANT_COLUMN_RULES` must contain no `.`** — `collapse_measurements` strips a `constant` key back to the segment before its first `.` before indexing the registry. So the registry key is the bare `holdout`, and the `constant` key is the dotted `holdout.from` that the error message names.

**One consequence to sweep.** `validate.py`'s claim that *"`cluster_by`, `weight_by`, and `holdout` are not read by `resolve_units` at all"* becomes false the moment this lands. It is on task 19's owned-sweep list and is fixed **here**, in the task that falsifies it — `CLAUDE.md`: three sweeps in one slice stopped one file short, and one of them "fixed a sentence in `correction.py` and missed the same sentence in the function that falsified it".

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
_MEASUREMENT_ROWS = [
    {"patient_id": "p1", "read_id": "r1", "split": "train", "value": "1"},
    {"patient_id": "p1", "read_id": "r2", "split": "test", "value": "2"},
    {"patient_id": "p2", "read_id": "r3", "split": "test", "value": "3"},
]


def _units_from_rows(rows, attributes):
    return [
        Unit(key=r["patient_id"], paths=(), attributes={a: r[a] for a in attributes})
        for r in rows
    ]


def test_a_holdout_from_column_varying_within_a_unit_is_refused():
    """A `by_attribute` holdout reading a column that disagrees between two
    rows of one unit would file that unit on whichever side the row the
    collapse kept says — a train/test membership decided by row order.

    `p1` carries `train` and `test`; `p2` carries one value, so the fixture
    also proves the check is per-unit rather than per-roster."""
    units = _units_from_rows(_MEASUREMENT_ROWS, ["read_id", "split", "value"])
    constant = _holdout_constant_column({"method": "by_attribute", "from": "split"})
    assert constant == {"holdout.from": "split"}
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-HOLDOUT-VARIES"
    assert "split" in str(exc.value)


def test_a_constant_holdout_from_column_collapses_cleanly():
    """The positive companion, produced by the code under test: the same
    declaration over rows that AGREE collapses without raising, and the
    surviving unit keeps the value. Without this the test above passes
    identically if the rule refused every `holdout.from`."""
    rows = [dict(r, split="train") for r in _MEASUREMENT_ROWS]
    units = _units_from_rows(rows, ["read_id", "split", "value"])
    collapsed, counts = collapse_measurements(
        units, "read_id", "first",
        _holdout_constant_column({"method": "by_attribute", "from": "split"}),
    )
    assert [u.key for u in collapsed] == ["p1", "p2"]
    assert [u.attributes["split"] for u in collapsed] == ["train", "train"]
    assert counts == [2, 1]


@pytest.mark.parametrize(
    "decl",
    [
        None,
        {},
        "nonsense",
        {"method": "random", "frac": 0.2},
        {"method": "random", "frac": 0.2, "from": "split"},
        {"method": "by_attribute"},
        {"method": "by_attribute", "from": ""},
        {"method": "by_attribute", "from": 7},
    ],
    ids=["absent", "empty", "not a mapping", "random", "random with a stray from",
         "by_attribute with no from", "empty from", "non-string from"],
)
def test_the_holdout_accessor_resolves_no_column_for_these(decl):
    """It resolves a column or it does not; it never reports a malformed
    declaration. `E-DATA-HOLDOUT-METHOD`, `-FROM` and `-NO-DRAW` are
    `validate`'s findings to raise, not a `ContractError` from a run that
    resolution has no path to report through.

    The `random with a stray from` row is the load-bearing one: the gate is on
    the METHOD, so a drawn split whose declaration happens to carry a `from`
    still reads no column — a run that raised `E-DATA-HOLDOUT-VARIES` there
    would be refusing a config over a column its draw never reads."""
    assert _holdout_constant_column(decl) == {}


def test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair():
    """`constant`'s iteration order decides which code a unit violating more
    than one declaration gets, and `collapse_measurements` stops at the first.
    Pinned as an order rather than left to dict-building accident.

    The fixture makes ONE unit violate `assign`, `holdout` and `cluster_by`
    at once — three declarations, so the three candidate orderings each give a
    different answer, which two declarations could not distinguish."""
    rows = [
        {"patient_id": "p1", "read_id": "r1", "split": "train", "arm": "a", "site": "s1"},
        {"patient_id": "p1", "read_id": "r2", "split": "test", "arm": "b", "site": "s2"},
    ]
    units = _units_from_rows(rows, ["read_id", "split", "arm", "site"])
    constant = _assign_constant_columns({"arm": {"method": "by_attribute"}})
    constant.update(_holdout_constant_column({"method": "by_attribute", "from": "split"}))
    constant.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc:
        collapse_measurements(units, "read_id", "first", constant)
    assert exc.value.code == "E-DATA-ASSIGN-VARIES"

    # Remove the highest-priority declaration and the NEXT one reports — which
    # is what proves the order rather than merely that `assign` reports.
    without_assign = _holdout_constant_column(
        {"method": "by_attribute", "from": "split"}
    )
    without_assign.update({"cluster_by": "site"})
    with pytest.raises(ContractError) as exc2:
        collapse_measurements(units, "read_id", "first", without_assign)
    assert exc2.value.code == "E-DATA-HOLDOUT-VARIES"
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k "holdout_from or holdout_accessor or holdout_rule" -x`. Every test fails on `ImportError` for `_holdout_constant_column`. Add it to `tests/test_units.py`'s `publishable.units` import list along with `_assign_constant_columns`, `collapse_measurements`, `Unit` and `ContractError` if any is missing, then re-run: the accessor tests now fail on the assertion instead.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, add the registry entry. Insert it into `CONSTANT_COLUMN_RULES` **between** `"assign"` and the flat pair is not possible (a dict literal has one order) — insert it after `"assign"`:

```python
    "holdout": (
        "E-DATA-HOLDOUT-VARIES",
        "A holdout decides which side of a train/test split the unit lands on, "
        "so collapsing disagreeing rows would leave that decision to the order "
        "the rows happen to be in — a unit evaluated against a model it was "
        "fitted on, or held back from one it should have been evaluated by. "
        "Which side of a split a unit is on is a fact about the unit, not "
        "about the measurement",
    ),
```

  and extend that registry's docstring, replacing the sentence

```python
**`holdout.from` is not reachable through this registry today** — it is a single key under a fixed mapping, not one per
declared axis, so it needs its own accessor the same shape `_assign_constant_columns`
is for `assign`, and nothing in this task builds one.
```

  with

```python
**`holdout.from` reaches this registry through its own accessor**,
`_holdout_constant_column` below — a single key under a fixed mapping rather
than one per declared axis, so it could not use `_assign_constant_columns`'s
`axis` loop, and it could not be a flat entry either: `resolve_units`'
comprehension filters on `isinstance(..., str)` and drops a mapping before the
registry is consulted. Its `constant` key is the dotted `holdout.from`, for the
message, and the lookup strips it back to the bare `holdout` here, exactly as
it strips `assign.<axis>.from` back to `assign`.
```

  (b) Add the accessor, immediately after `_assign_constant_columns`:

```python
def _holdout_constant_column(holdout_decl: Any) -> dict[str, str]:
    """`holdout.from` when a `by_attribute` holdout declares one — at most one
    entry, keyed by the literal dotted path a reader would look for.

    `_assign_constant_columns`' sibling, one declaration over, and narrower for
    the reason that one is narrow: this function's only job is deciding which
    column, if any, a holdout's constancy has to hold — not reporting a
    malformed declaration. An absent block, a non-mapping block, a missing
    `from`, an empty `from` and a non-`str` `from` are shapes
    `validate._check_holdout` reports (`E-DATA-HOLDOUT-METHOD`,
    `E-DATA-HOLDOUT-FROM`) and this function is silent on, each because it
    resolves to no column to check: those are `validate`'s findings to raise,
    not a `ContractError` from a run that resolution has no path to report
    through.

    **Gated on `method == "by_attribute"`**, matching `_assign_constant_columns`'
    own gate and for its reason: `random` draws the split rather than reading
    one, so no column is read, and a `from` declared beside it means nothing —
    already refused as `E-DATA-HOLDOUT-NO-DRAW`. Without this gate a drawn
    split whose declaration carried a stray `from` naming a column that varies
    within a unit's rows would raise `E-DATA-HOLDOUT-VARIES` over a column its
    draw never reads, which is the validate-clean-then-crash gap in the
    opposite direction: a config no check approves, refused anyway by a rule
    that assumed a read `by_attribute` alone performs.

    **There is no axis-name default**, unlike `assign.<axis>.from`: a holdout
    has no axis name, which is why `validate` requires `from` outright under
    `by_attribute` rather than defaulting it.
    """
    if not isinstance(holdout_decl, dict):
        return {}
    if holdout_decl.get("method") != "by_attribute":
        return {}
    declared_from = holdout_decl.get("from")
    if isinstance(declared_from, str) and declared_from:
        return {"holdout.from": declared_from}
    return {}
```

  (c) In `resolve_units`, insert the accessor's result between `assign`'s and the flat pair's, and rewrite the stale comment. Replace

```python
        constant = _assign_constant_columns(units_decl.get("assign"))
        constant.update(
```

  with

```python
        constant = _assign_constant_columns(units_decl.get("assign"))
        # `holdout.from` next, between `assign` and the flat pair. `assign` is
        # documented as the worst of the family (§ Allocation: a mis-collapsed
        # arm decides which CONDITION a unit is measured in), so it stays
        # first. `holdout.from` and `cluster_by` say the same thing about the
        # damage — which side of a split the unit lands on — so the order
        # BETWEEN those two is fixed here deterministically rather than left to
        # an accident of dict-building, and is **not** a claim that one fault
        # is worse than the other. `weight_by` stays last, which is the
        # documented ordering.
        constant.update(_holdout_constant_column(units_decl.get("holdout")))
        constant.update(
```

  and in the long comment above it, replace

```python
        # now reachable; **`holdout.from` still is not** — its shape is a single
        # key under a fixed mapping, not one-per-declared-axis, and needs its own
        # accessor rather than this one's `axis` loop.
```

  with

```python
        # now reachable; **`holdout.from` reaches it through
        # `_holdout_constant_column`** — its shape is a single key under a
        # fixed mapping, not one-per-declared-axis, so it needed its own
        # accessor rather than this one's `axis` loop.
```

  (d) In `src/publishable/validate.py`, fix the sentence this task falsifies. Replace

```python
    No other `-UNSUPPORTED` field is skipped on: `allocation`, `assign`,
    `cluster_by`, `weight_by`, and `holdout` are not read by
    `resolve_units` at all, so resolving against a real table or glob alongside
    one of those refusals adds a genuine, independent finding
```

  with

```python
    No other `-UNSUPPORTED` field is skipped on: `allocation` and `assign`'s
    method are not read by `resolve_units` at all, and the three that ARE read
    — `cluster_by`, `weight_by`, and (under `by_attribute`) `holdout.from` —
    are read only where a `data.units.measurements` collapse could file a unit
    by row order, which is an independent fault of its own. So resolving
    against a real table or glob alongside one of those refusals adds a
    genuine, independent finding
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then sweep by claim: `grep -rn "not read by" src/publishable/*.py` and `grep -rn "holdout.from" src/ docs/` — every present-tense claim that `holdout.from` is unreachable must be gone. Prove the sweep can fail by running it against `_holdout_constant_column`, which must return hits.

- [ ] **Step 5: Mutate** — two.

  (a) In `src/publishable/units.py`, delete the `if holdout_decl.get("method") != "by_attribute": return {}` gate. Run `uv run pytest tests/test_units.py -k holdout_accessor`. The `random with a stray from` row must **FAIL**. Revert in place; re-run.

  (b) Move `constant.update(_holdout_constant_column(...))` to **after** the flat-pair `constant.update({...})` block. Run `uv run pytest tests/test_units.py -k holdout_rule`. `test_the_holdout_rule_is_checked_after_assign_and_before_the_flat_pair` must **FAIL** on its second assertion (`E-DATA-CLUSTER-VARIES` now wins over `E-DATA-HOLDOUT-VARIES`). Revert in place; re-run. **Check before trusting this**: the two branches genuinely differ only because the fixture's one unit violates `cluster_by` *and* `holdout.from` at once — a fixture violating only one cannot discriminate, which is why the test builds one that violates three.

- [ ] **Step 6: Commit** — `feat: give holdout.from its own constant-column accessor`.

---


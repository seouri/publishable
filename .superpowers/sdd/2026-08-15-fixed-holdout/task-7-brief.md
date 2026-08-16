## Task 7: `_check_holdout`, roster half — the two literals, the clustered stratum, the empty test side

**Files:** Modify `src/publishable/validate.py`, `src/publishable/units.py`. Modify (append) `tests/test_validate.py`, `tests/test_units.py`.

**Interfaces:**
- Consumes: `units.arms_of(roster, column, levels) -> dict[str, list[Unit]]`, `units.stratum_varies_within_cluster(roster, cluster_by, stratify_by) -> tuple[str, list[str]] | None`, `units._apportion(n, weights) -> list[int]`.
- Produces:

```python
# src/publishable/units.py
HOLDOUT_LEVELS = ("train", "test")


def holdout_sizes(n: int, frac: float) -> tuple[int, int]:
    """`(train, test)` — `n` apportioned across `[1 - frac, frac]`."""


def holdout_values_fault(roster: UnitList, column: str) -> str | None:
    """The message describing how `column` fails to be exactly `{train, test}`
    over this roster, or `None` when it does not fail."""
```

  plus three more findings inside `_check_holdout` — `E-DATA-HOLDOUT-VALUES`, `E-DATA-HOLDOUT-STRATIFY-VARIES`, `E-DATA-HOLDOUT-EMPTY` — and `arms_of` added to `validate.py`'s `publishable.units` import list.

**Why `holdout_values_fault` exists rather than `validate` and the draw each wrapping `arms_of`.** Both `_check_holdout` (here) and `units.holdout_for` (task 10) have to answer "does this column resolve to exactly the two literals", and both have to say so in a holdout's vocabulary rather than `arms_of`'s, whose message names an arm and an axis's declared levels. Two independent wrappings of one raise is precisely how two messages come to drift — `stratum_varies_within_cluster` is the pattern that already solves this in this repo: **one function computes the fault and returns it, and each caller decides whether to collect it or raise it.** So the verdict and the wording live here, once, and task 10's `holdout_for` raises the string this returns.

**Why `holdout_sizes` exists rather than `validate` computing `int(n * frac)`.** `_apportion` is private, and a second arithmetic for the same split is exactly the validate-clean-then-disagree gap: `validate` would approve a `frac` whose realized test side the draw then sized differently. One public function, two callers — this check and task 10's `holdout_for`. `_apportion`'s largest-remainder rule is what `assignment_for`'s `random` branch already uses, so the holdout inherits it rather than inventing one.

**Each of the three carries its own `roster is not None` guard** rather than leaning on a caller — `_check_resample`'s stated convention, and the reason its docstring separates the roster-reading findings from the rest.

**The siting rule for the empty-test-partition refusal, and it is trap 5's.** Mirror *Every arm draws units* exactly: **reported for the unstratified, unclustered `random` draw only.** A stratified or clustered split is checked where the run performs it, because a cluster is the smallest thing that can move and only the draw knows what it moved. And `by_attribute` needs no refusal here at all — `arms_of` already refuses a level no unit's value names, which is a zero-size side by another name, so adding one would double-refuse the same fault under two codes.

**`stratum_varies_within_cluster`'s docstring is stale and this task fixes it.** It claims *"rows Fold strata survive clustering and Holdout strata survive clustering"* — two rows — while having **three** call sites at `78bb794` (`validate.py`'s `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES` and `E-STATS-RESAMPLE-STRATIFY-VARIES`). This task adds the **fourth**, so the docstring must name four rows. **Before editing it, run `grep -rn "Fold strata survive clustering" tests/ src/`** — a test pinning that wording is the "sweep stopped one file short" shape, and it must move with the docstring.

- [ ] **Step 1: Write the failing test** — append to `tests/test_units.py`:

```python
def test_holdout_sizes_is_the_single_authority_for_the_split_sizes():
    """One arithmetic for the split, shared by `validate`'s refusal and the
    draw. `_apportion`'s largest-remainder rule, which `assignment_for`'s
    `random` branch already uses — so a `frac` `validate` approves is a `frac`
    the draw realizes at the same sizes.

    Each row is chosen so a DIFFERENT wrong rule gives a different answer:
    truncation, rounding, and largest-remainder disagree on at least one."""
    assert holdout_sizes(10, 0.2) == (8, 2)
    assert holdout_sizes(240, 0.2) == (192, 48)
    # 7 × 0.2 = 1.4: truncation gives 1, rounding gives 1, largest-remainder
    # gives 1 — and the train side is what separates a rule that apportions
    # from one that subtracts a rounded test size.
    assert holdout_sizes(7, 0.2) == (6, 1)
    # 4 × 0.2 = 0.8: the floor is 0 and the remainder goes to the LARGEST
    # fractional part, which is the test side's 0.8 against the train side's
    # 3.2 — so largest-remainder gives 1 here where truncation gives 0.
    assert holdout_sizes(4, 0.2) == (3, 1)
    # The case the refusal exists for: no rule can give the test side a unit.
    assert holdout_sizes(2, 0.2) == (2, 0)
    assert sum(holdout_sizes(13, 0.3)) == 13
```

  and append to `tests/test_validate.py`:

```python
_SPLIT_ROSTER_OK = "patient_id,split\n" + "".join(
    f"p{i},{'test' if i % 5 == 0 else 'train'}\n" for i in range(20)
)
_SPLIT_ROSTER_THREE = "patient_id,split\n" + "".join(
    f"p{i},{['train', 'test', 'dev'][i % 3]}\n" for i in range(20)
)
_SPLIT_ROSTER_AB = "patient_id,split\n" + "".join(
    f"p{i},{'A' if i % 2 else 'B'}\n" for i in range(20)
)
_SPLIT_ROSTER_ONE_SIDED = "patient_id,split\n" + "".join(
    f"p{i},train\n" for i in range(20)
)


@pytest.mark.parametrize(
    "roster_csv",
    [_SPLIT_ROSTER_THREE, _SPLIT_ROSTER_AB, _SPLIT_ROSTER_ONE_SIDED],
    ids=["a third value", "neither literal", "one literal unused"],
)
def test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test(
    write_config, tmp_path, roster_csv
):
    """The two literals are fixed, settled in task 2: a holdout declares no
    `levels`, and inferring an order from the data would make which side is
    evaluated depend on a lexical accident of the input.

    Three ROSTERS against one config shape, deliberately: the property is about
    roster CONTENT, and varying config shape over one roster is what made
    nineteen adversary configs roster-incidental in an earlier slice. Each
    roster fails a different way — a third value, neither literal present, and
    both literals declared but one naming no unit."""
    (tmp_path / "input" / "index.csv").write_text(roster_csv)
    found = codes(
        write_config(
            _holdout(
                {"method": "by_attribute", "from": "split"}, attributes=["split"]
            )
        )
    )
    assert "E-DATA-HOLDOUT-VALUES" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_by_attribute_holdout_column_holding_exactly_the_two_literals_is_accepted(
    write_config, tmp_path
):
    """The positive companion, produced by the code under test: the same
    declaration over a column that IS exactly `{train, test}` reports nothing,
    so the refusal reads the roster rather than refusing `by_attribute`."""
    (tmp_path / "input" / "index.csv").write_text(_SPLIT_ROSTER_OK)
    found = codes(
        write_config(
            _holdout(
                {"method": "by_attribute", "from": "split"}, attributes=["split"]
            )
        )
    )
    assert "E-DATA-HOLDOUT-VALUES" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


_VARYING_HOLDOUT_STRATUM = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},{'x' if i % 2 else 'y'}\n" for i in range(28)
)
_CONSTANT_HOLDOUT_STRATUM = "patient_id,animal_id,label\n" + "".join(
    f"p{i},a{i // 2},{'x' if (i // 2) % 2 else 'y'}\n" for i in range(28)
)


@pytest.mark.parametrize(
    "roster_csv,expected",
    [(_VARYING_HOLDOUT_STRATUM, True), (_CONSTANT_HOLDOUT_STRATUM, False)],
    ids=["varies within the animal", "constant within the animal"],
)
def test_a_holdout_stratum_must_be_constant_within_a_cluster(
    write_config, tmp_path, roster_csv, expected
):
    """§ Validation *Holdout strata survive clustering* — whole clusters go to
    one side of a holdout, so a cluster carrying two stratum values can be
    dealt to neither. The fourth `stratum_varies_within_cluster` call site.

    Two ROSTERS with the SAME config: `label` alternates per unit in one and
    per animal in the other, so a check that ignored the roster gives the same
    answer for both and this pair separates them."""
    (tmp_path / "input" / "index.csv").write_text(roster_csv)
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.25, "stratify_by": ["label"]},
                attributes=["animal_id", "label"],
                cluster_by="animal_id",
            )
        )
    )
    assert ("E-DATA-HOLDOUT-STRATIFY-VARIES" in found) is expected
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_a_holdout_that_apportions_the_test_side_no_units_is_refused(
    write_config, tmp_path
):
    """§ Validation *Holdout leaves a test partition*. 4 units at `frac: 0.1`
    apportions `[4, 0]` — every metric would be over nothing.

    The fixture is 4 units and not 40 because the roster size is what decides
    the answer: at 40 the same `frac` apportions `[36, 4]` and reports
    nothing, which is the second row below."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "".join(f"p{i}\n" for i in range(4))
    )
    found = codes(write_config(_holdout({"method": "random", "frac": 0.1})))
    assert "E-DATA-HOLDOUT-EMPTY" in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_same_frac_over_a_larger_roster_is_accepted(write_config, tmp_path):
    """The positive companion for the row above, produced by the code under
    test and differing ONLY in roster size — so the refusal is the
    apportionment's answer rather than a refusal of small `frac` values."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id\n" + "".join(f"p{i}\n" for i in range(40))
    )
    found = codes(write_config(_holdout({"method": "random", "frac": 0.1})))
    assert "E-DATA-HOLDOUT-EMPTY" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


def test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split(
    write_config, tmp_path
):
    """Trap 5's siting rule, mirroring *Every arm draws units*: a clustered or
    stratified split is checked where the RUN performs it, because a cluster is
    the smallest thing that can move and only the draw knows what it moved.
    The same 4-unit roster that reports above must not report here.

    The wholesale refusal is the positive companion — without it this passes
    identically if `_check_holdout` never ran at all."""
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,animal_id\n" + "".join(f"p{i},a{i // 2}\n" for i in range(4))
    )
    found = codes(
        write_config(
            _holdout(
                {"method": "random", "frac": 0.1},
                attributes=["animal_id"],
                cluster_by="animal_id",
            )
        )
    )
    assert "E-DATA-HOLDOUT-EMPTY" not in found
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_units.py -k holdout_sizes tests/test_validate.py -k "by_attribute_holdout or holdout_stratum_must or apportions_the_test or larger_roster or clustered_split" -x`. `holdout_sizes` fails on `ImportError`; every `validate` test asserting a new code fails; the three controls pass, each carrying its wholesale-refusal companion.

- [ ] **Step 3: Implement** —

  (a) In `src/publishable/units.py`, add beside `_apportion`:

```python
HOLDOUT_LEVELS = ("train", "test")
"""`data.units.holdout`'s two sides, in apportionment order — train first.

Fixed literals rather than "the two values the column happens to hold", because
a holdout declares no `levels` for core to read an order out of, and inferring
one from the data would make which side is *evaluated* depend on a lexical
accident of the input. `reference.md` § A fixed holdout split states the rule
and § Errors names the refusal, `E-DATA-HOLDOUT-VALUES`.

Order is load-bearing twice: it is the order `holdout_sizes` apportions in, so
`frac` is the SECOND weight, and it is the order `arms_of` is handed for a
`by_attribute` read.
"""


def holdout_sizes(n: int, frac: float) -> tuple[int, int]:
    """`(train, test)` — `n` apportioned across `[1 - frac, frac]`.

    **One arithmetic for the split, and two callers**: `validate._check_holdout`
    refuses a `frac` that apportions the test side zero units, and
    `holdout_for`'s unclustered draw cuts the shuffled roster at exactly these
    sizes. Two derivations of the same number would mean `validate` approving a
    `frac` whose realized test side the draw then sized differently — the
    validate-clean-then-disagree gap `arms_of`'s own docstring is written to
    prevent a third instance of.

    `_apportion`'s largest-remainder rule, which `assignment_for`'s `random`
    branch already uses for `assign.<axis>.ratio`: each side's exact share
    floors and the remainder goes to the larger fractional part. Every size is
    within one of its exact proportional share, which is the strongest claim a
    fraction that doesn't divide `n` supports.

    **A test size of 0 is possible and is the caller's to refuse.** Two units at
    `frac: 0.2` gives `(2, 0)`. Nothing here raises: `validate` holds the
    declared `frac` and the roster a message has to name, so the refusal lives
    there — `_apportion`'s own convention, one construction over.
    """
    train, test = _apportion(n, [1.0 - frac, frac])
    return train, test


def holdout_values_fault(roster: UnitList, column: str) -> str | None:
    """How `column` fails to resolve to exactly `train` and `test` over this
    roster — as a message — or `None` when it does not fail.

    **One authority, two reporting surfaces**, which is
    `stratum_varies_within_cluster`'s own arrangement: `validate._check_holdout`
    collects this as `E-DATA-HOLDOUT-VALUES` and `holdout_for` raises it under
    the same code, so the two cannot come to disagree about either the verdict
    or the wording. Two independent wrappings of one raise is exactly how two
    messages drift apart.

    The **verdict** is `arms_of`'s, unchanged: that function stays the authority
    for a column-read partition and promises set equality in both directions —
    no unit's value outside the pair, and neither literal left holding nothing.
    Only the **wording** is rebuilt here, because `arms_of`'s own message names
    an arm and an axis's declared levels and would send a holdout's reader to
    the wrong section.

    Returns a message rather than raising, so `validate` — contracted never to
    raise — can report it beside every other finding, and so `holdout_for` can
    raise it with the code that belongs to a holdout rather than to an arm.
    """
    try:
        arms_of(roster, column, HOLDOUT_LEVELS)
    except ContractError:
        seen = sorted(
            {str(u.attributes[column]) for u in roster if column in u.attributes}
        )
        missing = [lit for lit in HOLDOUT_LEVELS if lit not in seen]
        return (
            f"the holdout column {column!r} has values {', '.join(seen) or 'none'} over "
            f"this roster — a `by_attribute` holdout needs exactly "
            f"`{HOLDOUT_LEVELS[0]}` and `{HOLDOUT_LEVELS[1]}`"
            + (f", and {', '.join(missing)} names no unit" if missing else "")
            + ". A holdout declares no levels for core to read an order out of, so the "
            "two names are fixed rather than inferred from the data"
        )
    return None
```

  (b) In `src/publishable/units.py`, correct `stratum_varies_within_cluster`'s docstring. Replace

```python
    decides which declaration to name (`reference.md` § Validation, rows *Fold
    strata survive clustering* and *Holdout strata survive clustering*, which is why
    this returns a fault rather than raising one code).
```

  with

```python
    decides which declaration to name — **four callers today, under four codes**:
    `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES`,
    `E-STATS-RESAMPLE-STRATIFY-VARIES` and `E-DATA-HOLDOUT-STRATIFY-VARIES`,
    answering to `reference.md` § Validation's *Allocation strata survive
    clustering*, *Fold strata survive clustering*, *Resample strata survive
    clustering* and *Holdout strata survive clustering*. That is why this returns
    a fault rather than raising one code: a code chosen here would be right for
    one caller and wrong for three.
```

  (c) In `src/publishable/validate.py`, add `holdout_sizes` and `holdout_values_fault` to the `publishable.units` import list — **not** `arms_of`, which stays behind `holdout_values_fault` so `validate` has no second way to ask the question — and append to `_check_holdout` — first grow the docstring's enumeration to ten by inserting after the `E-DATA-HOLDOUT-FOLD` bullet:

```python
    - `E-DATA-HOLDOUT-VALUES` — **reads the roster:** under `by_attribute`, the
      named column resolving to exactly `train` and `test`.
    - `E-DATA-HOLDOUT-STRATIFY-VARIES` — **reads the roster:** a stratum that
      varies within a `cluster_by` cluster.
    - `E-DATA-HOLDOUT-EMPTY` — **reads the roster:** a `random`, unstratified,
      unclustered split that apportions the test side zero units.

    **Three of the ten read `roster`**, and each carries its own
    `roster is not None` guard rather than leaning on a caller — `_check_resample`'s
    stated convention.
```

  then append to the body:

```python
    # `by_attribute`'s two literals, through `units.holdout_values_fault` — one
    # authority for both the verdict (`arms_of`'s set equality) and the wording,
    # so this collected finding and the one `holdout_for` raises at run time
    # cannot drift apart. `stratum_varies_within_cluster`'s own arrangement:
    # the function returns a fault and each caller decides whether to collect
    # it or raise it.
    if (
        method == "by_attribute"
        and roster is not None
        and isinstance(declared_from, str)
        and declared_from
    ):
        fault = holdout_values_fault(roster, declared_from)
        if fault is not None:
            c.error("E-DATA-HOLDOUT-VALUES", "data.units.holdout.from", fault)

    # *Holdout strata survive clustering*, through the fourth
    # `stratum_varies_within_cluster` call site. Reusing that function rather
    # than minting a second notion of constancy is the point: whole clusters go
    # to one side of a holdout, exactly as they do to one side of a fold, so
    # the holdout inherits the rule rather than inventing one. Names already
    # refused above are skipped, so a config with one undeclared and one
    # varying stratum gets one finding for each rather than two for one.
    if roster is not None and cluster_by:
        for name in strata:
            if not isinstance(name, str) or name not in declared_names:
                continue  # already refused above
            try:
                offender = stratum_varies_within_cluster(roster, cluster_by, name)
            except ContractError:
                # `clusters_of` refuses a unit carrying no cluster value
                # (`E-DATA-CLUSTER-UNKNOWN`), reported beside this by
                # `_check_cluster_by` or by `_check_units`' own resolution. This
                # module collects rather than raises.
                break
            if offender is not None:
                cluster, values = offender
                c.error(
                    "E-DATA-HOLDOUT-STRATIFY-VARIES",
                    "data.units.holdout.stratify_by",
                    f"names {name!r}, which varies within `{cluster_by}` {cluster} — it "
                    f"carries {', '.join(values)}. A cluster is indivisible and goes "
                    "whole to one side of the split, so a cluster carrying two stratum "
                    "values can be dealt to neither; stratify on an attribute constant "
                    "within a cluster",
                )

    # The zero-size test partition, sited exactly as *Every arm draws units* is:
    # **the unstratified, unclustered `random` draw only**. A stratified or
    # clustered split apportions inside each stratum or moves whole clusters,
    # so the realized test size is not this arithmetic's answer and only the
    # draw knows what it moved — that one is checked where the run performs it.
    # `by_attribute` needs nothing here: `arms_of` above already refuses a
    # literal no unit's value names, which is an empty side by another name,
    # and a second refusal of one fault under two codes is what this omission
    # avoids.
    if (
        method == "random"
        and roster is not None
        and not strata
        and not cluster_by
        and isinstance(declared_frac, (int, float))
        and not isinstance(declared_frac, bool)
        and 0.0 < float(declared_frac) < 1.0
    ):
        _train_size, test_size = holdout_sizes(len(roster), float(declared_frac))
        if test_size == 0:
            c.error(
                "E-DATA-HOLDOUT-EMPTY",
                "data.units.holdout.frac",
                f"is {declared_frac} over {len(roster)} resolved units, which apportions "
                "the test side zero of them — every metric would be over nothing. Widen "
                "`frac`, or resolve a larger roster",
            )
```

- [ ] **Step 4: Run, confirm it passes** — the Step 2 command, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Then the docstring sweep: `grep -rn "Fold strata survive clustering" src/ tests/ docs/` — every site claiming `stratum_varies_within_cluster` answers to *two* rows must now say four. Prove the sweep can fail by running it against `Holdout strata survive clustering`, which must return hits.

- [ ] **Step 5: Mutate** — three.

  (a) In `src/publishable/units.py`, change `holdout_sizes`'s body to `return _apportion(n, [frac, 1.0 - frac])[0], _apportion(n, [frac, 1.0 - frac])[1]` — the weights reversed. Run `uv run pytest tests/test_units.py -k holdout_sizes tests/test_validate.py -k "apportions_the_test or larger_roster"`. `test_holdout_sizes_...` must **FAIL** on `holdout_sizes(10, 0.2) == (8, 2)`, and `test_a_holdout_that_apportions_the_test_side_no_units_is_refused` must **FAIL** too: 4 units against reversed weights apportions `(0, 4)`, so the *test* side holds everything and the refusal never fires. `test_the_same_frac_over_a_larger_roster_is_accepted` is **not** expected to move — 40 units gives `(4, 36)` either way and neither side is empty — which is why it is named here as the branch that cannot discriminate rather than left for an implementer to puzzle over. Revert in place; re-run.

  (b) In `src/publishable/validate.py`, delete `and not cluster_by` from the empty-test-partition guard. `test_the_empty_test_partition_refusal_is_not_reported_for_a_clustered_split` must **FAIL**. Revert in place; re-run.

  (c) In `src/publishable/units.py`, inside `holdout_values_fault`, change `arms_of(roster, column, HOLDOUT_LEVELS)` to `arms_of(roster, column, sorted({str(u.attributes.get(column)) for u in roster}))` — the "two values sorted" reading task 2 rejected. `test_a_by_attribute_holdout_column_must_hold_exactly_train_and_test` must **FAIL** on the `_SPLIT_ROSTER_AB` and `_SPLIT_ROSTER_THREE` rows, since every observed value is now a declared level — and on `_SPLIT_ROSTER_ONE_SIDED` too, whose sorted set has one member that every unit matches. **All three rows must fail**, which is the check that the mutation reaches the rule rather than one fixture's arithmetic. Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a holdout column, stratum or frac the roster cannot honour`.

---


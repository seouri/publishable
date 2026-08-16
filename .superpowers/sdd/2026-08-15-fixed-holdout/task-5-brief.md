## Task 5: `_check_holdout`, declaration half A — method, `frac`, `from`, the dead fields, the seed pin

**Files:** Modify `src/publishable/validate.py`. Modify (append) `tests/test_validate.py`.

**Interfaces:**
- Consumes: `Collector.error(code, path, message)` from `publishable.diagnostics`; `validate_config`'s locals `doc`, `units_decl`, `roster`, `usable_cluster`.
- Produces:

```python
HOLDOUT_METHODS = ("random", "by_attribute")


def _check_holdout(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    c: Collector,
) -> None:
```

  called from `validate_config` immediately after `_check_fold_stratify_by(doc, units_decl, roster, usable_cluster, c)`:

```python
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
```

  Tasks 6 and 7 extend this same function. The `roster` and `cluster_by` parameters are unread at this commit and are in the signature anyway, for `units.assignment_for`'s stated reason: a caller that already has to hold both must not be told the signature changed under it two tasks later.

**The five findings this task adds**, in declaration order: `E-DATA-HOLDOUT-METHOD`, `E-DATA-HOLDOUT-FRAC`, `E-DATA-HOLDOUT-FROM`, `E-DATA-HOLDOUT-NO-DRAW`, `E-DATA-HOLDOUT-SEED`. `_check_resample`'s docstring is the model: it **enumerates its findings and says an eighth belongs in the list**, so this one enumerates its five and says the same.

**The `holdout: {}` ruling, settled here and not re-derived later.** An empty or non-mapping `holdout` **returns immediately and reports nothing**, mirroring `_check_resample`'s own `if not isinstance(resample, dict) or not resample: return`. `holdout: {}` and `holdout: null` therefore validate clean, exactly as they do at `78bb794` — the scoping calls this "the truthiness hole", and it is not a hole: `_check_unimplemented`'s `units.get(field)` is false for both, `envelope.py` (task 3) reports any misspelled child, and a block declaring nothing partitions nothing. **Pin it with a test**, because an implementer will otherwise try to refuse it.

**Every value read here is `isinstance`-guarded and quietly skipped when it is not a leaf `envelope.py` types.** A leaf type fault is deliberately non-fatal in this module — reported as `E-CONFIG-TYPE` and validation continues — which is the same division `_check_report_by` and `_check_resample` keep.

- [ ] **Step 1: Write the failing test** — append to `tests/test_validate.py`:

```python
def _holdout(block, **extra) -> dict:
    """`write_config`'s whole-block override for a config declaring a holdout.

    `base_config` has no `data.units` key at all, so a dotted
    `{"data.units.holdout": ...}` override raises `KeyError` walking `units` —
    the whole block is what every other `data.units` test in this file writes.
    """
    units = {"from": "index.csv", "key": "patient_id", **extra}
    if block is not None:
        units["holdout"] = block
    return {"data.units": units}


def test_an_empty_or_null_holdout_validates_clean(write_config):
    """`holdout: {}` and `holdout: null` declare nothing and partition nothing,
    so neither is refused — `_check_resample`'s own `not isinstance(...) or not
    ...: return` gate, one block over. Pinned because the shape looks like a
    hole and is not: a misspelled child inside a NON-empty block is reported by
    `check_envelope`, and `_check_unimplemented`'s truthiness test is false for
    both of these.

    The positive companion is the third assertion: a real declaration in the
    same position DOES report, so this cannot pass by the check being dead."""
    assert "E-DATA-HOLDOUT-METHOD" not in codes(write_config(_holdout({})))
    assert "E-DATA-HOLDOUT-METHOD" not in codes(write_config(_holdout(None)))
    assert "E-DATA-HOLDOUT-METHOD" in codes(write_config(_holdout({"frac": 0.2})))


@pytest.mark.parametrize(
    "block,expected",
    [
        # `method` — absent, wrong type, out of enum. An allowlist: a method
        # named here and realized nowhere would validate clean and then
        # partition on something core never drew.
        ({"frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        ({"method": ["random"], "frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        ({"method": "stratified", "frac": 0.2}, "E-DATA-HOLDOUT-METHOD"),
        # `frac` under `random` — absent, and each end of the OPEN interval.
        ({"method": "random"}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 0}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 1}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": -0.5}, "E-DATA-HOLDOUT-FRAC"),
        ({"method": "random", "frac": 1.5}, "E-DATA-HOLDOUT-FRAC"),
        # `from` under `by_attribute` — absent and empty. There is no axis name
        # to default to, unlike `assign.<axis>.from`.
        ({"method": "by_attribute"}, "E-DATA-HOLDOUT-FROM"),
        ({"method": "by_attribute", "from": ""}, "E-DATA-HOLDOUT-FROM"),
        # A field meaning nothing under the declared method, both directions.
        ({"method": "by_attribute", "from": "split", "frac": 0.2},
         "E-DATA-HOLDOUT-NO-DRAW"),
        ({"method": "random", "frac": 0.2, "from": "split"},
         "E-DATA-HOLDOUT-NO-DRAW"),
        ({"method": "by_attribute", "from": "split", "stratify_by": ["label"]},
         "E-DATA-HOLDOUT-NO-DRAW"),
        # The seed pin — present and neither `auto` nor a plain int.
        ({"method": "random", "frac": 0.2, "seed": "1234"}, "E-DATA-HOLDOUT-SEED"),
        ({"method": "random", "frac": 0.2, "seed": 1.5}, "E-DATA-HOLDOUT-SEED"),
    ],
)
def test_a_malformed_holdout_declaration_is_refused(write_config, block, expected):
    found = codes(write_config(_holdout(block)))
    assert expected in found
    # Alongside, never instead of: `E-DATA-HOLDOUT-UNSUPPORTED` is still live
    # at this commit and task 18 retires it. Membership on its own line makes
    # that retirement a one-line deletion rather than a rewrite of this test.
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found


@pytest.mark.parametrize(
    "block",
    [
        {"method": "random", "frac": 0.2},
        {"method": "random", "frac": 0.2, "seed": "auto"},
        {"method": "random", "frac": 0.2, "seed": 1234},
        {"method": "random", "frac": 0.999},
        {"method": "by_attribute", "from": "split"},
        {"method": "by_attribute", "from": "split", "seed": 1234},
    ],
)
def test_a_well_formed_holdout_declaration_earns_none_of_the_five(write_config, block):
    """The success path for every arm above. A parametrization asserting only
    failures proves nothing about either method's accepted shape — the shape
    that left `blocked`'s stratified draw fully threaded and never exercised.

    A pinned `seed` is legal under BOTH methods on purpose: `by_attribute`
    records no seed, but a config carrying one is not malformed, and refusing
    it here would put the `NO-DRAW` rule somewhere this test would not see."""
    found = codes(write_config(_holdout(block)))
    for code in ("E-DATA-HOLDOUT-METHOD", "E-DATA-HOLDOUT-FRAC",
                 "E-DATA-HOLDOUT-FROM", "E-DATA-HOLDOUT-NO-DRAW",
                 "E-DATA-HOLDOUT-SEED"):
        assert code not in found
    # The positive companion: this config is not silently escaping the check
    # entirely — the wholesale refusal still fires on the same declaration.
    assert "E-DATA-HOLDOUT-UNSUPPORTED" in found
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_validate.py -k holdout -x`. `test_a_malformed_holdout_declaration_is_refused` fails on every row; `test_an_empty_or_null_holdout_validates_clean` fails on its third assertion; the well-formed test passes already (nothing reports), which is why its **positive companion** — the surviving wholesale refusal — is what keeps it from being vacuous.

- [ ] **Step 3: Implement** — in `src/publishable/validate.py`, add the enum beside `ASSIGN_METHODS` (which sits at module level with its own explanatory docstring):

```python
HOLDOUT_METHODS = ("random", "by_attribute")
"""`data.units.holdout.method`'s enum — `reference.md` § A fixed holdout split.

Two values and no more, and stated as a closed enum for `ASSIGN_METHODS`'s
reason: a third named here and realized nowhere would validate clean and then
reach `units.holdout_for`, which refuses what it cannot draw. Which of the two
reads a partition and which draws one is what decides every other field's
meaning, so a malformed `method` is reported before any of them is read.
"""
```

  and the check itself, placed immediately after `_check_fold_stratify_by`'s definition:

```python
def _check_holdout(
    doc: dict[str, Any],
    units: dict[str, Any],
    roster: UnitList | None,
    cluster_by: str | None,
    c: Collector,
) -> None:
    """Every check `data.units.holdout` gets — five findings at this commit, in
    declaration order, and the enumeration is the list rather than a sample of
    it:

    - `E-DATA-HOLDOUT-METHOD` — the `method` enum.
    - `E-DATA-HOLDOUT-FRAC` — `frac` in the open interval (0, 1), under `random`.
    - `E-DATA-HOLDOUT-FROM` — `from` required, under `by_attribute`.
    - `E-DATA-HOLDOUT-NO-DRAW` — a field meaning nothing under the declared
      method.
    - `E-DATA-HOLDOUT-SEED` — the seed pin.

    **None of the five reads `roster` or `cluster_by`**, and both are in the
    signature anyway, `units.assignment_for`'s reason: the caller already holds
    both, and a caller told the signature changed under it is what a stable one
    avoids. A check added here must state which side of that line it is on —
    this list is what the next reader counts against, so a sixth finding
    belongs in it, and a roster-reading one carries its own
    `roster is not None` guard rather than leaning on a caller.

    **An empty or non-mapping declaration returns reporting nothing**,
    `_check_resample`'s own gate one block over. `holdout: {}` and
    `holdout: null` declare nothing and partition nothing;
    `_check_unimplemented`'s truthiness test is false for both, and a
    misspelled child inside a non-empty block is `check_envelope`'s
    `E-CONFIG-KEY-UNKNOWN` rather than this function's.

    Every value read here is `isinstance`-guarded and quietly skipped when it
    is not the leaf `envelope.LEAF_TYPES` types, the same division
    `_check_report_by` keeps: a leaf type fault is `E-CONFIG-TYPE`, reported
    already and deliberately non-fatal, and reporting a second, derived fault
    on top of the one the reader has to fix anyway is what
    `validate_config`'s own `usable_cluster` guard avoids.

    **`frac`'s interval is open at both ends.** `0` holds nothing out and `1`
    holds everything out; each leaves one side of the split empty, and a split
    with an empty side is not a split. A `frac` small enough to apportion the
    test side zero units over *this* roster is a different fault with a
    different fix — widen it, or resolve more units — and is not this check's.
    """
    holdout = units.get("holdout")
    if not isinstance(holdout, dict) or not holdout:
        return

    method = holdout.get("method")
    if method is None:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is not declared; the methods are {', '.join(HOLDOUT_METHODS)}, and which "
            "one is declared decides what every other field of the block means — "
            "`random` draws a split and `by_attribute` reads one already in the data",
        )
    elif not isinstance(method, str):
        # Absorbed here rather than left to `E-CONFIG-TYPE` alone: the reader's
        # question is which method they meant, and a bare type finding does not
        # enumerate the two.
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which names no method; the methods are "
            f"{', '.join(HOLDOUT_METHODS)}",
        )
    elif method not in HOLDOUT_METHODS:
        c.error(
            "E-DATA-HOLDOUT-METHOD",
            "data.units.holdout.method",
            f"is {method!r}, which is not one of {', '.join(HOLDOUT_METHODS)}. A method "
            "named here and realized nowhere would validate clean and then partition "
            "on something core never drew",
        )

    declared_frac = holdout.get("frac")
    declared_from = holdout.get("from")
    if method == "random":
        if declared_frac is None:
            c.error(
                "E-DATA-HOLDOUT-FRAC",
                "data.units.holdout.frac",
                "is not declared, and `method: random` draws the test side by "
                "fraction — there is nothing to draw without one",
            )
        elif isinstance(declared_frac, (int, float)) and not isinstance(declared_frac, bool):
            if not 0.0 < float(declared_frac) < 1.0:
                c.error(
                    "E-DATA-HOLDOUT-FRAC",
                    "data.units.holdout.frac",
                    f"is {declared_frac}, and a test fraction is strictly between 0 and "
                    "1 — `0` holds nothing out and `1` holds everything out, and each "
                    "leaves one side of the split empty",
                )
        if declared_from is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.from",
                "means nothing under `method: random`, which draws the split rather "
                "than reading one out of a column — declare `method: by_attribute` to "
                "read the column, or drop `from`",
            )
    elif method == "by_attribute":
        if declared_from is None:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is not declared, and `method: by_attribute` reads the split out of a "
                "column — unlike an assignment axis there is no axis name to default "
                "to, so the column has to be named",
            )
        elif isinstance(declared_from, str) and not declared_from:
            c.error(
                "E-DATA-HOLDOUT-FROM",
                "data.units.holdout.from",
                "is empty, which names no column to read the split out of",
            )
        if declared_frac is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.frac",
                "means nothing under `method: by_attribute`, which reads a split the "
                "data already holds rather than drawing one to a size — the realized "
                "proportion is whatever the column says it is",
            )
        if holdout.get("stratify_by") is not None:
            c.error(
                "E-DATA-HOLDOUT-NO-DRAW",
                "data.units.holdout.stratify_by",
                "means nothing under `method: by_attribute`: `stratify_by` names how a "
                "draw is BALANCED, and a split read out of a column was not drawn. The "
                "same absorption `E-DATA-ASSIGN-NO-DRAW` performs for the same field "
                "one declaration over",
            )

    if "seed" in holdout:
        seed = holdout["seed"]
        pinned = isinstance(seed, int) and not isinstance(seed, bool)
        if not pinned and seed != "auto":
            c.error(
                "E-DATA-HOLDOUT-SEED",
                "data.units.holdout.seed",
                f"is {seed!r}, and a seed is `auto` or a plain integer. A quoted "
                "number, a float, or a boolean is a pin nothing can honour, and "
                "deriving one anyway would record a derived seed under a key the "
                "config wrote deliberately",
            )
```

  and wire it in `validate_config`, immediately after the `_check_fold_stratify_by` call:

```python
    _check_fold_stratify_by(doc, units_decl, roster, usable_cluster, c)
    # Sited here for `_check_fold_stratify_by`'s reason and beside it: both read
    # the resolved roster and the usable cluster name, and both check a
    # partition's declaration rather than a repeat's. `usable_cluster` is
    # already narrowed to a non-empty string or `None` above, so this call needs
    # no guard of its own.
    _check_holdout(doc, units_decl, roster, usable_cluster, c)
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_validate.py -k holdout`, then `uv run pytest`, then `uv run ruff check . && uv run ruff format --check . && uv run mypy`.

- [ ] **Step 5: Mutate** — three, because three independent things could be dead.

  (a) In `src/publishable/validate.py`, change `if not 0.0 < float(declared_frac) < 1.0:` to `if not 0.0 <= float(declared_frac) <= 1.0:`. Run `uv run pytest tests/test_validate.py -k malformed_holdout_declaration`. The `frac: 0` and `frac: 1` rows must **FAIL**. Revert in place; re-run.

  (b) Change the wiring line `_check_holdout(doc, units_decl, roster, usable_cluster, c)` to pass `{}` in place of `units_decl`. **Every** row of `test_a_malformed_holdout_declaration_is_refused` must **FAIL**, and `test_an_empty_or_null_holdout_validates_clean`'s third assertion too. This is the mutation that proves the check is *wired*, not merely written — the seam H4a's `_condition_counts` extraction exists to make visible. Revert in place; re-run.

  (c) Change the empty-block gate from `if not isinstance(holdout, dict) or not holdout:` to `if not isinstance(holdout, dict):`. `test_an_empty_or_null_holdout_validates_clean`'s **first** assertion must **FAIL** (`holdout: {}` now reports `E-DATA-HOLDOUT-METHOD`). Revert in place; re-run.

- [ ] **Step 6: Commit** — `feat: refuse a malformed data.units.holdout declaration`.

---


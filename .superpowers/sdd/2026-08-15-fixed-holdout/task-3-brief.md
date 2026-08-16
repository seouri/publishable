## Task 3: Close `data.units.holdout` one level in

**Files:** Modify `src/publishable/envelope.py`. Modify (append) `tests/test_envelope.py`.

**Interfaces:**
- Consumes: `LEAF_TYPES: dict[str, type | tuple[type, ...]]` and `check_envelope(doc) -> list[tuple[str, str, str]]` in `src/publishable/envelope.py`.
- Produces: five new `LEAF_TYPES` entries — `data.units.holdout.method` (`str`), `.frac` (`float`), `.from` (`str`), `.stratify_by` (`(str, list)`), `.seed` — so a `methodd` inside the block is `E-CONFIG-KEY-UNKNOWN` and a wrong-typed child is `E-CONFIG-TYPE`.

**The precedent, and it is exact.** `data.units.measurements` is typed `dict` *and* closed one level in at `.by`/`.collapse`; `statistics.resample` is typed `dict` and closed at `.method`/`.n`/`.stratify_by`. `envelope.py`'s own comment argues that `resample` was closed **before** its wholesale refusal retired, deliberately — "the slice that honours a block needs the shape checked before it can read the values." A holdout's children have fixed names, so the same closure applies, and it closes the `holdout: {}` truthiness hole's sibling as a by-product: a `{methodd: random}` is reported by no check at `78bb794`.

**Two rulings this task must not get wrong.**

- **`frac` is typed `float`, and `_is_type` special-cases `bool`.** A `frac: 1` (a plain `int`) is a legal YAML spelling of a fraction the range check then refuses as outside (0, 1); typing it `(int, float)` would let `frac: 1` reach the range check rather than `E-CONFIG-TYPE`, which is the right division of labour — a `1` is a well-typed number outside the interval, not a type fault. So type it `(int, float)`, not `float`. State this in the entry's comment.
- **`seed` is typed `(str, int)`**, matching what § What `auto` derives from permits: the string `auto` or a plain integer. `bool` is excluded by `_is_type`'s special case, which is exactly why `seed: true` must reach `E-CONFIG-TYPE` rather than being read as `1`.
- **`stratify_by` is `(str, list)`**, not `list` alone — `units.stratum_names` reads a bare `stratify_by: label` as one name exactly as `[label]` is, and typing it `list` would make the envelope and the draw disagree about the same declaration. `statistics.resample.stratify_by`'s entry states this verbatim; copy the reasoning.

- [ ] **Step 1: Write the failing test** — append to `tests/test_envelope.py`:

```python
def test_a_misspelled_holdout_child_is_reported():
    """`data.units.holdout` is closed one level in, the arrangement
    `measurements` and `resample` already have: its children have fixed names,
    so a typo among them is reachable by a check rather than silently ignored.

    The positive companion is in the same test on purpose — a well-spelled
    sibling in the SAME block must produce no finding, so this cannot pass by
    reporting every key in the block."""
    findings = check_envelope(
        {"data": {"units": {"holdout": {"methodd": "random", "frac": 0.2}}}}
    )
    assert ("E-CONFIG-KEY-UNKNOWN", "data.units.holdout.methodd") in [
        (code, path) for code, path, _ in findings
    ]
    assert not [f for f in findings if f[1] == "data.units.holdout.frac"]


@pytest.mark.parametrize(
    "block,path,expect_type_error",
    [
        ({"method": ["random"]}, "data.units.holdout.method", True),
        ({"method": "random"}, "data.units.holdout.method", False),
        # A plain `int` is a legal YAML spelling of a fraction; the OPEN-interval
        # refusal is `E-DATA-HOLDOUT-FRAC`'s, not the envelope's, so `1` must be
        # well-typed here. `True` is not: `_is_type` excludes `bool` from every
        # numeric entry, since `True` is not a fraction.
        ({"frac": 0.2}, "data.units.holdout.frac", False),
        ({"frac": 1}, "data.units.holdout.frac", False),
        ({"frac": True}, "data.units.holdout.frac", True),
        ({"frac": "0.2"}, "data.units.holdout.frac", True),
        ({"from": "split"}, "data.units.holdout.from", False),
        ({"from": 3}, "data.units.holdout.from", True),
        # A bare string names one stratum exactly as a one-element list does —
        # `units.stratum_names`, the single authority the draw balances on.
        ({"stratify_by": "label"}, "data.units.holdout.stratify_by", False),
        ({"stratify_by": ["label"]}, "data.units.holdout.stratify_by", False),
        ({"stratify_by": 7}, "data.units.holdout.stratify_by", True),
        ({"seed": "auto"}, "data.units.holdout.seed", False),
        ({"seed": 1234}, "data.units.holdout.seed", False),
        ({"seed": True}, "data.units.holdout.seed", True),
        ({"seed": 1.5}, "data.units.holdout.seed", True),
    ],
)
def test_each_holdout_child_is_typed(block, path, expect_type_error):
    """Each of the five children, at its own type, with a legal value beside
    every illegal one. Both arms are asserted because a parametrization that
    only ever asserts a FAILURE proves nothing about the success path — the
    shape that left `blocked`'s stratified draw fully threaded and never
    exercised."""
    findings = check_envelope({"data": {"units": {"holdout": block}}})
    typed = [f for f in findings if f[0] == "E-CONFIG-TYPE" and f[1] == path]
    assert bool(typed) is expect_type_error, findings
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_envelope.py -k holdout -x`. Both fail: the closure test reports no `E-CONFIG-KEY-UNKNOWN` at all (the walk never descends into a known leaf), and every `expect_type_error=True` row reports nothing.

- [ ] **Step 3: Implement** — in `src/publishable/envelope.py`, replace the entry

```python
    "data.units.holdout": dict,
```

with

```python
    "data.units.holdout": dict,
    # Closed one level in, the arrangement `data.units.measurements` above and
    # `statistics.resample` below both have, and for their reason: these five
    # names are fixed, so leaving the block whole would make a `methodd` typo
    # unreachable by any check. Closed *before* the block's own wholesale
    # refusal retires, which is `resample`'s ordering rather than
    # `measurements`': the slice that honours a block needs the shape checked
    # before it can read the values.
    "data.units.holdout.method": str,
    # `(int, float)`, not `float`: a `frac: 1` is a well-typed number that
    # happens to fall outside the open interval (0, 1), which is a different
    # fault with a different code (`E-DATA-HOLDOUT-FRAC`) and a different fix.
    # `bool` is excluded by `_is_type`'s special case, since `True` is not a
    # fraction however well `bool` subclasses `int`.
    "data.units.holdout.frac": (int, float),
    "data.units.holdout.from": str,
    # `(str, list)` for `statistics.resample.stratify_by`'s reason, one
    # declaration over: `units.stratum_names` — the single authority a draw
    # balances on — reads a bare `stratify_by: label` as one name exactly as
    # `[label]` is, so typing this `list` alone would make the envelope and the
    # draw disagree about the same declaration.
    "data.units.holdout.seed": (str, int),
    "data.units.holdout.stratify_by": (str, list),
```

  Then rewrite the module docstring's two `holdout`-stays-whole claims. Replace

```python
# `holdout` stays whole for now: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the
# block, so its gap is latent, and H3d closes it.
```

with

```python
# `holdout` is closed one level in too, at its own five keys, for the reason
# `resample` is: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the block at this
# commit, and the shape is checked ahead of that refusal lifting rather than
# after it, so the slice that honours the block reads values whose shape a
# check already approved.
```

  and in the paragraph beginning "The table stopping at a key is the end of the line", replace

```python
# misspelled `resolverr` in a `data.units.from` mapping or `methodd` in
# `holdout` is reported by no check in this build. That is the documented
# cost of a whole leaf (`reference.md` § Validation names the blocks it
# applies to and the slice that closes each), not a claim that such a key
# could never be named: `holdout`'s children have fixed names. The keys that
```

with

```python
# misspelled `resolverr` in a `data.units.from` mapping is reported by no
# check in this build. That is the documented cost of a whole leaf
# (`reference.md` § Validation names the blocks it applies to and the slice
# that closes each), not a claim that such a key could never be named — a
# `methodd` in `holdout` was in exactly that position and is now reported,
# its children's names being fixed. The keys that
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_envelope.py -k holdout`, then `uv run pytest`. Then `uv run ruff check . && uv run ruff format . && uv run mypy`.

- [ ] **Step 5: Mutate** — in `src/publishable/envelope.py`, change `"data.units.holdout.frac": (int, float),` to `"data.units.holdout.frac": (int, float, str),`. Run `uv run pytest tests/test_envelope.py -k each_holdout_child_is_typed`. The `{"frac": "0.2"}` row must **FAIL**. Delete `__pycache__`, edit the entry back in place, re-run; it passes. Then a second mutation, because the first only proves the type table is read: delete the `"data.units.holdout.method": str,` line entirely. `test_a_misspelled_holdout_child_is_reported` must **FAIL** — with no path beneath `holdout` in the table, `_known_containers` stops treating `holdout` as a container and the walk never descends. Restore the line in place and re-run.

- [ ] **Step 6: Commit** — `feat: close data.units.holdout one level in, ahead of its refusal lifting`.

---


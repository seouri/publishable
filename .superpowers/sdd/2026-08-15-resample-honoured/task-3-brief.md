## Task 3: Close `statistics.resample` one level in

**Files:** Modify `src/publishable/envelope.py`. Test `tests/test_envelope.py`.

**Interfaces:**
- Consumes: `envelope.LEAF_TYPES`, `envelope._known_containers()`, `envelope._check_unknown_keys`.
- Produces: `statistics.resample.method` (`str`), `statistics.resample.n` (`int`), `statistics.resample.stratify_by` (`(str, list)`) as `LEAF_TYPES` entries — which Tasks 4 and 5 rely on for their `E-CONFIG-TYPE` backstop.

**The precedent is `data.units.measurements`, not `assign.<axis>`.** The spec and the scoping both say "`assign.<axis>` style … `LEAF_TYPES` plus a closed key set". A closed key set is **not needed here**, and building one would be a second authority over the same three names. `_known_containers()` derives every dotted prefix a `LEAF_TYPES` path implies, and `_check_unknown_keys` checks **containers before leaves** ("Containers before leaves: `data.units.measurements` is both — typed a mapping by the loop in `check_envelope`, and descended into here"). So adding the three child paths makes `statistics.resample` simultaneously a leaf (still typed `dict`) and a container (descended into), and `stratifyy_by` reports `E-CONFIG-KEY-UNKNOWN` with a difflib hint for free. `_check_assign_axis_keys` exists only because an `assign` **axis name** is user-chosen and no fixed dotted path reaches it; `resample`'s three keys are fixed.

**`stratify_by` is `(str, list)`** because `units.stratum_names` — the single authority `validate._check_assign` already imports — reads presence and shape structurally: a bare `stratify_by: site` names one stratum exactly as `[site]` does. Typing it `list` alone would make the bare form an `E-CONFIG-TYPE` while `stratum_names` accepts it, which is the two-readings-of-one-declaration shape that docstring exists to prevent.

- [ ] **Step 1: Write the failing test** — append to `tests/test_envelope.py`:

```python
def test_a_misspelled_resample_key_is_reported_rather_than_ignored():
    """`statistics.resample` is now both a leaf and a container, the same
    arrangement `data.units.measurements` has: typed a mapping by the loop in
    `check_envelope`, and descended into by `_check_unknown_keys`, which checks
    containers before leaves. Without the three child paths the closure stops at
    the leaf and `stratifyy_by` is reached by no check in this build."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": "bootstrap", "n": 2000, "stratifyy_by": ["a"]}}}
    )
    by_code = [(code, path) for code, path, _ in findings]
    assert ("E-CONFIG-KEY-UNKNOWN", "statistics.resample.stratifyy_by") in by_code
    # The positive companion: the three real keys are NOT reported, so the test
    # cannot pass by the closure rejecting everything under the block.
    assert not any(
        path.startswith("statistics.resample.") and path.endswith(("method", "n", "stratify_by"))
        for _, path in by_code
    )


def test_the_three_resample_leaves_are_typed():
    """A wrong-typed child now has an `E-CONFIG-TYPE` backstop, which is what
    lets `_check_resample` read each value without its own isinstance ladder."""
    findings = check_envelope(
        {"statistics": {"resample": {"method": 3, "n": "many", "stratify_by": 7}}}
    )
    paths = {path for code, path, _ in findings if code == "E-CONFIG-TYPE"}
    assert paths == {
        "statistics.resample.method",
        "statistics.resample.n",
        "statistics.resample.stratify_by",
    }


def test_a_bare_string_stratify_by_is_accepted_by_the_envelope():
    """`units.stratum_names` reads a bare `stratify_by: site` as one name, the
    same as `[site]`. Typing this `list` alone would make the two readings
    disagree — `E-CONFIG-TYPE` here while the draw balances on it there."""
    findings = check_envelope({"statistics": {"resample": {"stratify_by": "site"}}})
    assert not [f for f in findings if f[1].startswith("statistics.resample")]
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_envelope.py -k resample -x`. Expect `test_a_misspelled_resample_key_is_reported_rather_than_ignored` to fail with an empty `by_code` for that path (the closure stops at the leaf), and `test_the_three_resample_leaves_are_typed` to fail with `paths == set()`.

- [ ] **Step 3: Implement** — in `src/publishable/envelope.py`, in `LEAF_TYPES`, immediately after `"statistics.resample": dict,`:

```python
    "statistics.resample": dict,
    # Closed one level in, the arrangement `data.units.measurements` above has
    # and for its reason: these three names are fixed, the block is no longer
    # refused wholesale, and leaving it whole would make a `stratifyy_by` typo
    # unreachable by any check the moment the wholesale refusal retired — a
    # latent gap turning live. `assign`'s separate `_check_assign_axis_keys` is
    # not the precedent: it exists because an axis NAME is user-chosen and no
    # fixed dotted path reaches it. `stratify_by` is `(str, list)` because
    # `units.stratum_names` — the single authority the draw balances on — reads
    # a bare `stratify_by: site` as one name exactly as `[site]` is; typing it
    # `list` alone would make the envelope and the draw disagree about the same
    # declaration.
    "statistics.resample.method": str,
    "statistics.resample.n": int,
    "statistics.resample.stratify_by": (str, list),
```

  Then update the module docstring's list of blocks "declared at their own key with the one outer type that section gives them" — it currently names `statistics.contrasts` / `.resample` / `.null_test` / `.report_by`; remove `.resample` from that list and add a sentence saying it is now closed one level in like `measurements`.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_envelope.py`, then `uv run pytest`, then `uv run mypy` and `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `envelope.py`, delete the line `"statistics.resample.stratify_by": (str, list),`. Run `uv run pytest tests/test_envelope.py -k resample`. `test_the_three_resample_leaves_are_typed` must FAIL (the path set shrinks to two) and `test_a_misspelled_resample_key_is_reported_rather_than_ignored` must still pass — proving the closure survives on the other two children, which is the fact that makes this a three-line change rather than a new function. Delete `__pycache__`, edit the line back in place, re-run.

- [ ] **Step 6: Commit** — `feat: close statistics.resample one level in, the way measurements already is`.

---


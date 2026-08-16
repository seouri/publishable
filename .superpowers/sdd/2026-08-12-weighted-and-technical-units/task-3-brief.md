## Task 3: The input path collapses before uniqueness

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: task 1's `collapse_measurements`
- Produces: `resolve_units(units_decl, input_dir) -> tuple[UnitList, dict[str, float] | None]` — collapsing when `measurements` is declared, and returning `technical_n` **beside** the roster rather than on it

The uniqueness check currently raises `E-UNITS-KEY-DUPLICATE` on a repeated key. Under a `measurements` declaration a repeated key is **the point**, so the collapse must happen **before** that check — and the check must still fire for a config with no `measurements`.

- [ ] **Step 1: Write the failing tests**

```python
def test_duplicate_keys_collapse_when_measurements_is_declared(tmp_path):
    write_index(tmp_path, [
        {"patient_id": "p1", "read_id": "r1", "depth": "10"},
        {"patient_id": "p1", "read_id": "r2", "depth": "20"},
        {"patient_id": "p2", "read_id": "r3", "depth": "30"},
    ])
    roster, technical_n = resolve_units({
        "from": "index.csv", "key": "patient_id",
        "attributes": ["depth", "read_id"],
        "measurements": {"by": "read_id", "collapse": {"depth": "mean"}},
    }, tmp_path)
    assert len(roster) == 2
    assert technical_n == {"min": 1, "max": 2, "median": 1.5}


def test_the_unit_list_gains_no_new_operation(tmp_path):
    """The contract is exactly three operations plus `.train`
    (`reference.md` § The unit list is three operations). `technical_n` is a
    second return value precisely so it cannot become a fourth."""
    write_index(tmp_path, [{"patient_id": "p1"}, {"patient_id": "p2"}])
    roster, _ = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert not hasattr(roster, "technical_n")


def test_duplicate_keys_still_raise_without_measurements(tmp_path):
    """The collapse is what makes a repeated key legal. Without the declaration
    it is the duplicate it always was."""
    write_index(tmp_path, [
        {"patient_id": "p1", "read_id": "r1"},
        {"patient_id": "p1", "read_id": "r2"},
    ])
    with pytest.raises(ContractError) as excinfo:
        resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert excinfo.value.code == "E-UNITS-KEY-DUPLICATE"


def test_technical_n_is_absent_when_measurements_is_undeclared(tmp_path):
    """A design that never measures twice must read exactly as it did before."""
    write_index(tmp_path, [{"patient_id": "p1"}, {"patient_id": "p2"}])
    roster, technical_n = resolve_units({"from": "index.csv", "key": "patient_id"}, tmp_path)
    assert technical_n is None
```

- [ ] **Step 2: Run and confirm each fails**

Run: `uv run pytest tests/test_units.py -k "collapse or technical" -v`

- [ ] **Step 3: Implement**

### The contract task 3 must honour, or this slice ships a config that validates and then crashes

Task 2's check and `_apply` use **deliberately different** notions of "numeric", and that is correct — but it puts the burden here. Measured:

```
is_measurement_numeric("10")     -> True     # validate accepts a CSV-sourced numeric column
_apply("mean", ["10", "10"])     -> '10'     # constant shortcut fires; returns a STRING
_apply("mean", ["10", "20"])     -> TypeError    # bare, no E- code
```

`validate` says the column is fine for `mean`; `_apply` cannot actually compute it. Task 2's implementer deliberately did **not** rewire `_apply` to use the permissive predicate, and was right: that converts a silent wrong value into a crash without fixing anything.

**So task 3 must coerce numeric-looking strings to numbers before `_apply` ever sees them**, using `is_measurement_numeric` as the gate so the two answers cannot part. Two consequences to test, not just to implement:

- A CSV-sourced roster with `collapse: mean` over a numeric column must **collapse to a number**, not raise and not return a string. This is the headline test.
- A `TypeError` escaping `resolve_units` would escape **`validate`** too — it wraps the call in `except ContractError` only — breaking the hard invariant that `validate` collects findings and never raises. If any path can still raise a non-`ContractError`, convert it, and pin it.

Task 5 calls `_apply` directly on recorded rows and inherits the same obligation; `io.record` coerces its values, so check whether that already settles it there rather than assuming either way.

---

**Do not put `technical_n` on `UnitList`.** `reference.md` § The unit list is three operations, and `CLAUDE.md`'s invariant, both say `io.units` supports *exactly* three operations — iterate, `len`, index — plus `.train`. `io.units` **is** a `UnitList` handed to steps, so a public `technical_n` property widens a deliberately narrow surface, and a private one with a module-level accessor is the same thing wearing a disguise.

Instead, change the signature to **`resolve_units(units_decl, input_dir) -> tuple[UnitList, dict[str, float] | None]`** — the collapse produces two things, and the caller that needs both asks for both. There are exactly two call sites: `validate.py` (inside its `except ContractError` wrapper, which discards the second element) and `cli.py`'s phase-5 roster resolution, which carries it to the record. Update both, and the tests that call it directly.

Then, in `resolve_units`, between building `units` and the uniqueness loop:

```python
    technical_n = None
    measurements = units_decl.get("measurements")
    if measurements:
        units, counts = collapse_measurements(
            units, str(measurements["by"]), measurements.get("collapse", "first")
        )
        technical_n = {
            "min": min(counts),
            "max": max(counts),
            "median": statistics.median(counts),
        }
```

and pass `technical_n` into the returned `UnitList`.

`reference.md` § What isn't a repeat requires `{min, max, median}` rather than a scalar, and states the reason: real files are uneven, and a bare `technical_n: 3` is a claim of balance nobody checked. Put that reason in the code comment — it is why the shape is not a simplification waiting to happen.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test**

Move the collapse to *after* the uniqueness loop. `test_duplicate_keys_collapse_when_measurements_is_declared` must FAIL with `E-UNITS-KEY-DUPLICATE` — proving the ordering is load-bearing and not incidental. Revert, delete `__pycache__`, verify by behaviour.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: collapse technical replicates at resolution, before n is counted"
```

---


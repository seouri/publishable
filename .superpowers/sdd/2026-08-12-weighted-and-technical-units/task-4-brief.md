## Task 4: `io.record` gains `measurement=`

**Files:**
- Modify: `src/publishable/artifacts.py`
- Test: `tests/test_artifacts.py`

**Interfaces:**
- Produces: `record(self, unit_key: str, values: dict[str, Any], measurement: str | None = None)`; `E-STEP-MEASUREMENT-UNDECLARED`

`reference.md` § The importable surface already documents this three-argument form — the document leads and the code lags, so this closes a gap rather than adding a feature. The `measurement=` argument is the **only** discriminator between a resumed retry (first write wins, deduplicate) and a second measurement (collapse and average); `reference.md` § What isn't a repeat says nothing in the row itself distinguishes them.

- [ ] **Step 1: Write the failing tests**

```python
def test_two_measurements_of_one_unit_are_both_kept(step_io):
    step_io.record("p1", {"score": 10}, measurement="r1")
    step_io.record("p1", {"score": 20}, measurement="r2")
    assert len(step_io.measurement_rows()) == 2


def test_two_records_without_a_measurement_are_first_write_wins(step_io):
    """The retry path, unchanged. This is the behaviour `measurement=` exists
    to be distinguishable from."""
    step_io.record("p1", {"score": 10})
    step_io.record("p1", {"score": 20})
    assert step_io.rows() == [{"unit": "p1", "score": 10}]


def test_a_measurement_without_the_declaration_raises(step_io_undeclared):
    with pytest.raises(ContractError) as excinfo:
        step_io_undeclared.record("p1", {"score": 10}, measurement="r1")
    assert excinfo.value.code == "E-STEP-MEASUREMENT-UNDECLARED"
```

- [ ] **Step 2: Run and confirm each fails**

- [ ] **Step 3: Implement**

`StepIO.__init__` is keyword-only and is constructed in **exactly one place**, `runner.py`. Add **`measurements: dict[str, Any] | None = None`** — the declaration itself, not a boolean. Task 5 needs the collapse *rule* from it, so a `measurements_declared: bool` would have to be widened one task later; and one field carrying the declaration cannot disagree with itself the way a flag and a rule can.

Then:

```python
    def record(
        self, unit_key: str, values: dict[str, Any], measurement: str | None = None
    ) -> None:
        """Append one row, keyed by unit — or by `(unit, measurement)`.

        `measurement=` is the only thing separating a resumed retry from a second
        measurement of the same unit: without it a second row for one unit is a
        retry to be deduplicated under first-write-wins, with it a measurement to
        be averaged, and nothing in the row itself says which
        (`reference.md` § What isn't a repeat).
        """
        if measurement is not None and not self._measurements:
            raise ContractError(
                "`io.record` was given `measurement=` while `data.units.measurements` "
                "is undeclared, so there is no rule to collapse the rows under. Declare "
                "it with a `by` and a `collapse`, or drop the argument — without a rule "
                "a second row for one unit is a resumed retry, not a measurement",
                code="E-STEP-MEASUREMENT-UNDECLARED",
            )
```

Measurement rows accumulate in a separate `dict[tuple[str, str], dict]` keyed by `(unit_key, measurement)`, itself first-write-wins so a resumed *measurement* is still idempotent.

- [ ] **Step 4: Run and confirm they pass**

- [ ] **Step 5: Mutation-test**

Drop the `measurement is not None` guard so the raise fires unconditionally. `test_two_records_without_a_measurement_are_first_write_wins` must FAIL. Revert, delete `__pycache__`, verify by behaviour.

- [ ] **Step 6: Add the registry row and commit**

`E-STEP-MEASUREMENT-UNDECLARED` is raise-time, so it belongs in § Errors core raises — **not** the validate-time table. Confirm which by reading both sections' own scoping sentences before writing the row.

```bash
git commit -am "feat: io.record takes a measurement, and refuses one with no rule"
```

---


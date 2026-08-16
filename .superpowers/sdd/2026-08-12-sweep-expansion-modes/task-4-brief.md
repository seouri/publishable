## Task 4: `ablate` emits one change at a time

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`

**Interfaces:**
- Consumes: task 1's `expand`
- Produces: `ablate` applied **after** the product, not as an axis

§ Expansion modes: *"`ablate` is the one mode that does not multiply, because it isn't an axis. It emits `n` conditions, each one change away from the baseline, and it **reads** the baseline rather than re-emitting it — so a declared baseline is condition `00` exactly once, never both as `00_baseline` and as an ablate row."*

- [ ] **Step 1: Write the failing test from the document's own example**

```python
def test_ablate_emits_one_baseline_and_one_condition_per_removal() -> None:
    """§ Expansion modes: 1 + n conditions, not 2^n, and the baseline appears
    exactly once — read, not re-emitted."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {
                    "features.demographics": True,
                    "features.labs": True,
                    "features.notes": True,
                },
                "ablate": {
                    "from": "baseline",
                    "remove": ["features.demographics", "features.labs", "features.notes"],
                },
            }
        }
    )

    assert len(conditions) == 4
    assert conditions[0].is_baseline
    assert [c.is_baseline for c in conditions[1:]] == [False, False, False]
    assert dict(conditions[1].values)["features.demographics"] is False
    assert dict(conditions[1].values)["features.labs"] is True
```

`remove` sets a boolean parameter to `false` or a nullable one to `null` — read § Expansion modes for `override`, the non-boolean form, and cover it too.

- [ ] **Step 2: Run, implement, run.** `ablate` is applied after the product in `expand`, reading `sweep.baseline` rather than emitting a row of its own.

- [ ] **Step 3: Retire `E-SWEEP-ABLATE-UNSUPPORTED`**, test the retirement, commit.

---


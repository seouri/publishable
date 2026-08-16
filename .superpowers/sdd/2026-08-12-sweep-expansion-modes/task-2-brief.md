## Task 2: `paired` joins the product

**Files:**
- Modify: `src/publishable/sweep.py`, `src/publishable/validate.py`
- Test: `tests/test_sweep.py`, `tests/test_validate.py`

**Interfaces:**
- Consumes: `_axes` and `_swept_paths` from task 1
- Produces: nothing new; `paired` becomes one axis whose cells are whole dicts

§ Expansion modes: *"When parameters must move together rather than combinatorially, a list of dicts is treated as a single axis."* Its example is `grid × paired = 2 × 2 = 4 conditions`, **not** 2×2×2.

- [ ] **Step 1: Write the failing test**

```python
def test_paired_is_one_axis_not_a_product_of_its_keys() -> None:
    """§ Expansion modes' own example: grid × paired = 2 × 2 = 4, not 2 × 2 × 2.
    A paired entry sets several paths at once and counts once."""
    conditions = expand(
        {
            "sweep": {
                "grid": {"analysis.method": ["pearson", "spearman"]},
                "paired": [
                    {"analysis.min_samples": 30, "analysis.confidence": 0.95},
                    {"analysis.min_samples": 50, "analysis.confidence": 0.99},
                ],
            }
        }
    )

    assert len(conditions) == 4
    assert dict(conditions[0].values) == {
        "analysis.method": "pearson",
        "analysis.min_samples": 30,
        "analysis.confidence": 0.95,
    }
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_sweep.py::test_paired_is_one_axis_not_a_product_of_its_keys -v`
Expected: **FAIL** — 2 conditions, because `_axes` ignores `paired`.

- [ ] **Step 3: Add the axis**

In `_axes`, after the grid loop:

```python
    paired = sweep.get("paired") or []
    if paired:
        # One axis, not one per key: a paired entry is a single setting that
        # happens to set several paths. Treating its keys as separate axes is
        # exactly the combinatorial reading § Expansion modes rejects.
        axes.append([dict(entry) for entry in paired])
```

And extend `_swept_paths` to include every path any paired entry names, in first-seen order.

- [ ] **Step 4: Retire the refusal**

Remove the `("paired", "E-SWEEP-PAIRED-UNSUPPORTED", …)` tuple from `validate.py`'s refusal loop, and remove `E-SWEEP-PAIRED-UNSUPPORTED`'s row from `docs/reference.md` § Validation's error table if it has one. Grep first:

```bash
grep -rn "E-SWEEP-PAIRED-UNSUPPORTED" src/ tests/ docs/ README.md
```

Standing policy keeps `-UNSUPPORTED` codes out of the four documents, so there is likely **no** row to remove — confirm, and say which in your report. There **is** a `NOT BUILT` marker in § The one config file's example if `paired` appears there; remove that too.

- [ ] **Step 5: Test that the refusal is gone**

Add to `tests/test_validate.py` a config declaring `paired` and assert `E-SWEEP-PAIRED-UNSUPPORTED` is **not** among the findings — and that the config validates cleanly otherwise.

- [ ] **Step 6: Run, mutate, commit**

Run the suite. Mutations: make `_axes` append `paired` as one axis per key (the new test must fail); make it append nothing (the same).

```bash
git add src/publishable/sweep.py src/publishable/validate.py tests/ docs/reference.md
git commit -m "feat: expand paired as a single coupled axis"
```

---


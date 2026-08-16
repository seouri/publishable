### Task 3: The paired table and `n_paired`

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: the collapsed table `dict[str, dict[str, float]]` that `collapse_repeats` returns, one per condition.
- Produces: `paired_keys(of: dict[str, dict[str, float]], against: dict[str, dict[str, float]], allowed: set[str] | None) -> list[str]`

Sorted, so downstream draws are row-order invariant for the same reason `percentile_over_units` sorts its pool.

**The intersection is the rule.** `docs/reference.md`: a contrast is computed over the intersection of both sides' completed units, and that count is `n_paired`. Not the union, and not either side alone — a unit that completed in one condition and failed in the other has no difference to contribute.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_pairing_is_the_intersection():
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}, "u3": {"m": 3.0}}
    against = {"u2": {"m": 1.0}, "u3": {"m": 1.0}, "u4": {"m": 1.0}}
    assert paired_keys(of, against, None) == ["u2", "u3"]


def test_the_union_and_either_side_alone_all_differ():
    """Pins the intersection specifically: three wrong answers are distinguishable."""
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}}
    against = {"u2": {"m": 1.0}, "u3": {"m": 1.0}}
    keys = paired_keys(of, against, None)
    assert keys == ["u2"]
    assert keys != sorted(set(of) | set(against))
    assert keys != sorted(of)
    assert keys != sorted(against)


def test_a_within_stratum_narrows_the_intersection():
    of = {"u1": {"m": 1.0}, "u2": {"m": 2.0}}
    against = {"u1": {"m": 1.0}, "u2": {"m": 1.0}}
    assert paired_keys(of, against, {"u2"}) == ["u2"]


def test_the_result_is_sorted():
    of = {"u3": {"m": 1.0}, "u1": {"m": 1.0}}
    against = {"u1": {"m": 1.0}, "u3": {"m": 1.0}}
    assert paired_keys(of, against, None) == ["u1", "u3"]
```

- [ ] **Step 2: Run to verify they fail, then implement**

```python
def paired_keys(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    allowed: set[str] | None,
) -> list[str]:
    """The units both sides completed, narrowed by a `within` stratum if given.

    The intersection, not the union: a unit that completed in one condition and
    failed in the other has no difference to contribute, and counting it would
    put a number in `n_paired` that no per-unit difference backs.

    Sorted so a resample over these keys is row-order invariant, the same reason
    `percentile_over_units` sorts its pool.
    """
    keys = set(of) & set(against)
    if allowed is not None:
        keys &= allowed
    return sorted(keys)
```

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Pair two conditions over the units both completed"
```

---


### Task 4: `paired_t_over_units` and `cohens_dz`

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `Interval(low: float, high: float, method: str)` — frozen, **three fields, not a tuple**; `t_over_units(values, confidence) -> Interval | None`.
- Produces:
  - `paired_t_over_units(diffs: Sequence[float], confidence: float = 0.95) -> Interval | None`
  - `cohens_dz(diffs: Sequence[float]) -> float | None`

This is the construction for a **column metric**: Student's *t* on the per-unit differences, df = `n_paired` − 1.

**`cohens_dz` is the mean of the differences over their standard deviation.** It is reported only for a per-unit mean; a derived metric gets `null`, which Task 6 enforces at the call site. Use the sample standard deviation (ddof = 1), matching `t_over_units`.

- [ ] **Step 1: Write the failing tests**

```python
def test_the_interval_is_students_t_on_the_differences():
    diffs = [1.0, 2.0, 3.0, 4.0]
    got = paired_t_over_units(diffs)
    plain = t_over_units(diffs)
    assert got.low == plain.low and got.high == plain.high


def test_it_names_its_own_method():
    assert paired_t_over_units([1.0, 2.0, 3.0]).method == "paired_t_over_units"


def test_one_difference_has_no_interval():
    assert paired_t_over_units([1.0]) is None


def test_cohens_dz_is_the_mean_over_the_standard_deviation():
    """Hand-computed: mean 2.5, sample sd of [1,2,3,4] is 1.2909944, so dz = 1.9365."""
    assert cohens_dz([1.0, 2.0, 3.0, 4.0]) == pytest.approx(1.93649167, rel=1e-6)


def test_cohens_dz_is_none_below_two_differences():
    assert cohens_dz([1.0]) is None


def test_cohens_dz_is_none_when_every_difference_is_identical():
    """Zero dispersion would divide by zero; no `d` is honest, infinity is not."""
    assert cohens_dz([2.0, 2.0, 2.0]) is None
```

The `cohens_dz` value is hand-computed and written out in the test so a reader can check it without running anything — mean 2.5 over sample sd 1.2909944.

- [ ] **Step 2: Run to verify they fail, then implement**

```python
def paired_t_over_units(
    diffs: Sequence[float], confidence: float = 0.95
) -> Interval | None:
    """Student's t on the per-unit differences, df = n_paired − 1.

    The contrast's interval is its own construction, never a difference of the
    two sides' intervals — differencing discards the covariance that pairing
    exists to exploit, which is why a paired interval is narrower than the two
    conditions' own (reference.md § How a metric becomes a number).
    """
    plain = t_over_units(diffs, confidence)
    if plain is None:
        return None
    return Interval(low=plain.low, high=plain.high, method="paired_t_over_units")


def cohens_dz(diffs: Sequence[float]) -> float | None:
    """The mean of the per-unit differences over their standard deviation.

    Reported only for a per-unit mean: a derived metric has no per-unit value to
    difference, which is why the worked example carries `cohens_d: null` for `r`.
    """
    if len(diffs) < 2:
        return None
    mean = sum(diffs) / len(diffs)
    variance = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)
    sd = math.sqrt(variance)
    return mean / sd if sd > 0 else None
```

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Interval and effect size for a paired column metric"
```

---


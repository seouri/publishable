## Task 8: The weighted interval

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Produces: `kish_effective_n(weights) -> float`, `weighted_t_over_units(values, weights, confidence=0.95) -> Interval | None`

Kish's effective sample size is `(Σw)² / Σw²`. `reference.md` § Weighted samples: weighting concentrates the estimate on fewer units, and an interval that ignored that would be narrower than the sample supports. The existing `t_over_units(values, confidence)` computes df as `len(values) − 1` and must keep doing so for unweighted designs.

### First: promote the usability predicate, do not re-derive it

Task 7 built `validate._usable_weight` — positive, finite, and numeric via `units.is_measurement_numeric`. That is **the predicate `validate` approves a config against**, and it is currently private to `validate.py`. If the weighted mean is built on a different notion of a usable weight, this slice re-opens the validate-clean-then-crash gap it spent tasks 2 and 3 closing: a config `validate` accepts whose weights `stats` cannot use.

**Promote it beside `is_measurement_numeric` in `units.py`** and have both `validate` and `stats` read it. Do not import a private helper across modules — there is no precedent for that here, and task 2 established the pattern when `rule_for` gained a second caller. Mutation-test the sharing: changing the predicate must fail a test in **both** `test_validate.py` and `test_stats.py`, which is what makes the single-authority claim provided rather than stated.

Remember the CSV trap that has now bitten two tasks: table-sourced values arrive as `str`, so `isinstance(v, (int, float))` is `False` for every real weight. `is_measurement_numeric` is what handles that.

- [ ] **Step 1: Write the failing tests — the widening one first**

```python
def test_a_weighted_interval_is_wider_than_the_unweighted_one():
    """The point of Kish's size. A test asserting only that `weighted_by` was
    recorded would pass against an implementation that stores the declaration and
    computes the unweighted interval — which is the bug, not the fix."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    weights = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 20.0]   # genuinely uneven
    plain = t_over_units(values)
    weighted = weighted_t_over_units(values, weights)
    assert (weighted.high - weighted.low) > (plain.high - plain.low)


def test_equal_weights_reproduce_the_unweighted_interval():
    """The boundary that proves the construction is a generalization, not a
    different statistic wearing the same name."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    weighted = weighted_t_over_units(values, [1.0] * 5)
    plain = t_over_units(values)
    assert weighted.low == pytest.approx(plain.low)
    assert weighted.high == pytest.approx(plain.high)


def test_kish_effective_n_of_equal_weights_is_the_count():
    assert kish_effective_n([2.0, 2.0, 2.0, 2.0]) == pytest.approx(4.0)
```

`Interval` is a frozen dataclass of `low`, `high`, `method` — compare the two floats, not the objects: `method` legitimately differs between the two constructions, so `==` on the dataclass would fail for the right reason and tell you the wrong thing.

- [ ] **Step 2: Run and confirm each fails.**

- [ ] **Step 3: Implement**

```python
def kish_effective_n(weights: Sequence[float]) -> float:
    """Kish's effective sample size: (Σw)² / Σw².

    Equals the count when the weights are equal, and falls as they spread — which
    is the whole reason it is here. `reference.md` § Weighted samples: weighting
    concentrates the estimate on fewer units, and an interval whose df ignored
    that would be narrower than the sample supports.
    """
    total = sum(weights)
    squares = sum(w * w for w in weights)
    if squares == 0:
        return 0.0
    return (total * total) / squares


def weighted_t_over_units(
    values: Sequence[float], weights: Sequence[float], confidence: float = 0.95
) -> Interval | None:
    """Student's t on the weighted per-unit values, df = Kish's effective n − 1.

    Returns None below two values, matching `t_over_units`: df would be zero and
    there is no dispersion to describe. Reporting a point with no interval is
    honest; inventing one is not.
    """
    if len(values) < 2:
        return None
    total = sum(weights)
    mean = sum(w * v for w, v in zip(values, weights, strict=True)) / total
    # The weights are in the variance as well as the mean. Keeping them in only
    # the mean is the mutation step 5 requires a test for: it leaves the point
    # estimate right and the interval wrong, which is the failure that survives
    # an eyeball.
    variance = sum(w * (v - mean) ** 2 for w, v in zip(values, weights, strict=True)) / total
    effective = kish_effective_n(weights)
    if effective < 2:
        return None
    sem = math.sqrt(variance) / math.sqrt(effective)
    # Same construction as `t_over_units`, with Kish's size in place of the row
    # count — including a fractional df, which `t.ppf` accepts and which is the
    # honest value: the effective size of an uneven weighting is not an integer.
    critical = float(_scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=effective - 1))
    half = critical * sem
    return Interval(low=mean - half, high=mean + half, method="weighted_t_over_units")
```

**There is no `_t_critical` helper** — `t_over_units` calls `_scipy_stats.t.ppf` inline, and the line above matches it deliberately. If you would rather extract a shared helper, that is a reasonable call, but then **change both call sites in the same commit**: two critical-value expressions is how the weighted and unweighted intervals drift apart. Say which route you took.

- [ ] **Step 4: Run and confirm they pass.**

- [ ] **Step 5: Mutation-test — two separately.** First: use `len(values) − 1` for df instead of Kish's size. `test_a_weighted_interval_is_wider_than_the_unweighted_one` must FAIL. Second: drop the weights from the variance while keeping them in the mean. A test must FAIL — if none does, **write one**, because that is the defect the equal-weights test cannot see.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: a weighted interval takes its df from Kish's effective size"
```

---


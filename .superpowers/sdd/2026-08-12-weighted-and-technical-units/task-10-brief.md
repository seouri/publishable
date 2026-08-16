## Task 10: Wire the weighted estimator, and the percentile path

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`, `tests/test_cli.py`

### First: nothing calls `weighted_t_over_units`, and task 11 makes that a wrong number

**A gap this plan did not contain, found after task 9.** `grep` confirms the only mentions of `weighted_t_over_units` outside `stats.py` are *comments*. So today a weighted run records `weighted_by` and `n.effective` beside an **unweighted** mean and interval — the exact risk this slice's spec names first: *a declaration accepted whose effect is not delivered.*

It is latent only because `E-DATA-WEIGHT-UNSUPPORTED` refuses every config that declares `weight_by`. **Task 11 retires that refusal**, which turns it live. Task 9 left an `xfail(strict=True)` end-to-end pin that will XPASS-fail the suite at that moment — a deliberate forcing function, so this cannot be forgotten.

The site is `summarize_step`'s recorded-column loop:

```python
        values = [float(v) for v in raw]
        interval = t_over_units(values)
        out[column] = {
            **(beside_n or {}),
            "value": mean_of(values),
```

**Both lines must become weighted when weights are declared** — § Weighted samples says the construction "uses the weighted **mean** and the weighted variance". Wiring only the interval leaves the point estimate unweighted, which is the same half-delivered failure one level down, and would pass any test that checks only the interval.

Two things to get right, and to test rather than assume:
- **The weights must be aligned to the units the values came from.** `raw` is built by filtering `collapsed` for units that have the column, so the weight vector must be filtered the same way, in the same order. A misalignment silently weights the wrong unit and produces a plausible number.
- **A derived metric** — one `aggregate` computed, with no per-unit value — has no per-unit vector to weight. Say what happens to it, and check what § Weighted samples and § The unit table is the inference base require rather than choosing.

Assert **exact numbers**, not directions: task 8's headline test asserted a weighted interval was "wider than unweighted" and passed against an implementation using the row count for df, because it is still wider.

### Then: the percentile path

`reference.md` § Weighted samples: *"A percentile interval draws units as usual and recomputes the weighted statistic on each draw, so the weights are in the estimate rather than in the drawing."* Weighting the *draw* would be a different estimator; this is the distinction to test, not just to implement.

- [ ] **Step 1: Write the failing test**

```python
def test_a_percentile_draw_is_unweighted_while_its_statistic_is_not():
    """The weights belong in the estimate, not in the drawing — and the difference
    is observable in the output, with no test-only hook.

    21 units: twenty at 1.0, one at 100.0 carrying almost all the weight. Drawing
    UNWEIGHTED, the heavy unit is absent from a good fraction of the draws, and a
    draw without it has a weighted mean of 1.0 — so the interval reaches down to 1.
    Drawing WEIGHTED, the heavy unit would fill nearly every slot of every draw,
    the weighted mean would be ~100 every time, and the interval would collapse to
    a point near 100. The low bound is what separates the two estimators."""
    values = [1.0] * 20 + [100.0]
    weights = [1.0] * 20 + [500.0]
    result = percentile_over_units(values, weights=weights, draws=2000, seed=7)
    assert result.low == pytest.approx(1.0, abs=0.5)   # a draw-weighted impl cannot reach here
    assert result.high > 50.0                          # ...while the statistic is still weighted
```

**Do not add a test-only hook to the production signature** to observe the draw — a hook that exists only for the test is a second API. The assertion above sees the draw through the output, which is the route to prefer. If you find it does not discriminate, test the draw helper directly instead, and say in your report which route you took and why.

Note that `percentile_over_units` currently **sorts its pool**, with a comment explaining that the resample must depend on the multiset rather than on row order. A weighted version must keep each value with its own weight — sort the `(value, weight)` pairs together, or draw indices against an unsorted pair list. Getting this wrong silently pairs values with the wrong weights, and the equal-weights test cannot see it.

- [ ] **Step 2–4:** Fail, implement, pass.

- [ ] **Step 5: Mutation-test.** Weight the draw instead of the statistic; the test must FAIL.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat: a percentile draw stays unweighted while its statistic does not"
```

---


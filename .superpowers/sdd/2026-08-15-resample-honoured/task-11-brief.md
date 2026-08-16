## Task 11: `resample_draws` for a column metric — verify the invariant decision 2 rests on

**Files:** Modify `src/publishable/stats.py` (docstring), `docs/superpowers/spec-defects.md`. Test `tests/test_stats.py`.

**Interfaces:**
- Consumes: `stats.percentile_over_units(values, seed, draws, confidence, weights, strata)` (Tasks 9–10); `stats.checked_weights`; `units.usable_weight`.
- Produces: the stated guarantee Task 14 relies on — a column metric records `resample_draws` = **the requested `n`**, and `percentile_over_units` keeps returning a bare `Interval`.

**The decision (spec decision 2), and the verification it demands.** `percentile_of_derived` returns `(Interval, int)` because a derived metric's `compute` can fail on a degenerate draw — `nan`, `None`, or a raise — so the survivor count is a real fact. A **column** metric's draw statistic is a mean over a non-empty sample, which is always defined, so `draws_used == n` always and the return type need not change (~20 existing tests read it). **The spec says: "The implementer must verify that invariant before relying on it; if a degenerate column draw is reachable, take `(Interval, int)` instead and say so."** This task is that verification.

**The verification argument, which the test must exercise rather than assert.** The unweighted branch computes `sum(pool[...]) / n` with `n = len(values) >= 2`, so no division by zero. The weighted branch computes `_weighted_mean` over a drawn subset, and `checked_weights` — reading `units.usable_weight`, which requires `math.isfinite(number) and number > 0` — raises `E-DATA-WEIGHT-INVALID` **before any draw** for a zero, negative, non-finite or non-numeric weight. So Σw over any non-empty drawn subset is strictly positive and the weighted mean is defined. The stratified branch draws `len(pool) >= 1` rows from each non-empty pool, so its `drawn` is non-empty too. There is no reachable degenerate column draw.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
@pytest.mark.parametrize(
    "bad", [0, 0.0, -1.0, float("nan"), float("inf"), "heavy", None, True]
)
def test_a_column_resample_refuses_a_bad_weight_before_any_draw(bad):
    """The invariant decision 2 rests on: a column metric's draw statistic is a
    mean over a non-empty sample, so it is ALWAYS defined and
    `resample_draws == n` always. What could break that is a weight of zero
    making Σw zero on some draw — so the check is that `checked_weights`
    (reading `units.usable_weight`, which requires a finite positive number)
    refuses every such weight before a single draw is taken."""
    values = [1.0, 2.0, 3.0, 4.0]
    weights = [1.0, 1.0, 1.0, bad]
    with pytest.raises(ContractError) as exc:
        percentile_over_units(values, seed=1, draws=100, weights=weights)
    assert exc.value.code == "E-DATA-WEIGHT-INVALID"


def test_a_column_resample_is_never_degenerate_across_adversarial_columns():
    """The positive half, and the one that would catch a `(Interval, int)`
    requirement appearing: over columns chosen to be as degenerate as a column
    can be — zero variance, a single repeated value, extreme weight spread,
    a one-unit stratum — the interval is always produced, so no survivor count
    ever differs from the requested draws."""
    cases: list[tuple[list[float], dict]] = [
        ([5.0, 5.0, 5.0, 5.0], {}),                                  # zero variance
        ([0.0, 0.0, 0.0, 1e-12], {}),                                # near-zero spread
        ([1.0, 2.0, 3.0, 4.0], {"weights": [1e-9, 1e-9, 1e-9, 1e9]}),  # extreme spread
        ([1.0, 2.0, 3.0], {"strata": ["a", "b", "b"]}),               # one-unit stratum
        ([1.0, 2.0, 3.0, 4.0], {"strata": ["a", "a", "b", "b"],
                                "weights": [1.0, 2.0, 3.0, 4.0]}),
    ]
    for values, kwargs in cases:
        got = percentile_over_units(values, seed=2, draws=100, **kwargs)
        assert got is not None, (values, kwargs)
        assert got.method == "percentile_over_units"
        assert got.low <= got.high


def test_percentile_over_units_still_returns_a_bare_interval():
    """Pinned deliberately: ~20 tests read this return, and decision 2 is that
    it does NOT become `(Interval, int)`. A slice that changed it would have to
    change this test, which is where the decision gets re-argued rather than
    drifted past."""
    got = percentile_over_units([1.0, 2.0, 3.0, 4.0], seed=1, draws=100)
    assert isinstance(got, Interval)
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k column_resample or bare_interval -x`. All three should **pass immediately** — this is a verification task, and a pass here is the evidence decision 2 asked for. If `test_a_column_resample_refuses_a_bad_weight_before_any_draw` fails for any parameter, the invariant is **false**: stop, take `(Interval, int)` from `percentile_over_units` instead, and record the change in `docs/superpowers/spec-defects.md` naming the parameter that broke it.

- [ ] **Step 3: Implement** — in `src/publishable/stats.py`, append to `percentile_over_units`'s docstring:

```
    **This returns a bare `Interval`, with no survivor count, and that is a
    decision rather than an omission.** `percentile_of_derived` returns
    `(Interval, int)` because a derived metric's `compute` can fail on a
    degenerate draw — `nan`, `None`, or a raise — so how many draws survived is
    a real fact about the interval. A column metric's draw statistic is a mean
    over a non-empty sample, which is always defined: the unweighted branch
    divides by `n >= 2`, the weighted branch's Σw is strictly positive because
    `checked_weights` refuses a zero, negative, non-finite or non-numeric weight
    before any draw is taken, and the stratified branch draws `len(pool) >= 1`
    rows from each non-empty pool. So a column's `resample_draws` is the
    REQUESTED `n` and is recorded as such by `summarize_step`; the invariant is
    pinned by `test_a_column_resample_is_never_degenerate_across_adversarial_columns`
    rather than asserted here.
```

  And add to `docs/superpowers/spec-defects.md`:

```markdown
## A column metric's `resample_draws` records the requested `n`, not a survivor count

Decided in H4a (2026-08-15). `stats.percentile_over_units` returns a bare `Interval` where
`percentile_of_derived` returns `(Interval, int)`, so a recorded column under a declared
`statistics.resample` has no survivor count to record beside its interval.

**Ruling: record the requested `n`.** A column's draw statistic is a mean over a non-empty
sample and is always defined — the unweighted branch divides by `n >= 2`, `checked_weights`
refuses a non-positive or non-finite weight before any draw, and a stratified pool is non-empty
by construction — so `draws_used == n` always and the return type need not change (~20 existing
tests read it). Verified rather than assumed, by
`tests/test_stats.py::test_a_column_resample_is_never_degenerate_across_adversarial_columns`
and the parametrized weight refusal beside it.

**Consequence to keep in view:** `W-STATS-RESAMPLE-THIN` fires on `used < requested`, so it can
never fire for a column. That is correct — the warning exists for a template's `aggregate`
producing nothing on some draws — but it means the two metric kinds carry the same field with
subtly different provenance, which `reference.md` § Statistical reporting states.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`, then the doc mechanical pass on `spec-defects.md`.

- [ ] **Step 5: Mutate** — in `src/publishable/units.py`, change `usable_weight`'s guard from `if not math.isfinite(number) or number <= 0:` to `if not math.isfinite(number) or number < 0:` — admitting a weight of zero. Run `uv run pytest tests/test_stats.py -k refuses_a_bad_weight`. The `0` and `0.0` parameters must FAIL, which is the proof that the invariant rests on that guard and not on luck. Delete `__pycache__`, edit `number < 0` back to `number <= 0` in place, re-run.

- [ ] **Step 6: Commit** — `test: verify a column draw is never degenerate, so resample_draws records the requested n`.

---


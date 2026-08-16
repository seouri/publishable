## Task 9: The stratified draw — construction, not wiring

**Files:** Modify `src/publishable/stats.py`. Test `tests/test_stats.py`.

**Interfaces:**
- Consumes: `stats.percentile_over_units(values, seed, draws=2000, confidence=0.95, weights=None)` as it stands at `src/publishable/stats.py:488`; `stats.checked_weights`; `stats._weighted_mean`; `stats._percentile_ranks`; `stats.min_honest_draws`.
- Produces: `percentile_over_units(values, seed, draws=2000, confidence=0.95, weights=None, strata=None) -> Interval | None`, where `strata` is a sequence aligned positionally to `values`. Task 14 passes it; Task 15 builds it.

**This is construction, not wiring.** Nothing in `stats.py` draws within a stratum, and `units._stratum_groups` is not reusable — it takes a `UnitList`, and `stats.py` is deliberately import-free of `units` beyond `cluster_count_of`/`checked_weights`. **Six of the seven non-null `resample:` declarations in `docs/feasibility-llm-growth-studies.md` carry a `stratify_by`**, so this is the common case, not the exotic one.

**What the document specifies.** `reference.md` § Weighted samples: "`resample.stratify_by` says what an independent draw is, resampling within each stratum so a bootstrap can't return a replicate whose stratum composition the design ruled out." So each draw preserves **each stratum's own size** and draws with replacement **within** it.

**Row-order invariance is preserved the same way the existing branches preserve it.** `percentile_over_units` sorts its pool because with a fixed seed `rng.randrange(n)` draws the same sequence of *indices* whatever the input order is, so the multiset of values must be all that matters. Under strata: group first (carrying each value's weight with it), sort within each stratum, then order the strata **by their own sorted contents** rather than by label — which is what makes a relabelled stratum give the identical interval, exactly as `percentile_over_units_clustered` orders its cluster pools.

**Fixture sizing — this is where a fixture agrees with the bug.** Use three strata with **unequal sizes and disjoint value bands**: 20 values in `[0, 1)`, 8 in `[10, 11)`, 2 in `[100, 101)`. Then the three candidate answers are all different numbers:
- correct stratified mean ≈ `(20·0.5 + 8·10.5 + 2·100.5) / 30` ≈ **9.83**, with a *narrow* interval because the 2-value stratum contributes exactly 2 rows to every draw;
- unstratified draw: same expectation, but the 2-value stratum's contribution varies from 0 to many, so the interval is **several times wider**;
- averaging the strata's own means: `(0.5 + 10.5 + 100.5) / 3` ≈ **37.17**, nowhere near either.

Two equal strata distinguish none of these.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def _banded_strata() -> tuple[list[float], list[str]]:
    """Three strata, unequal sizes, disjoint value bands. Sized so that the
    three candidate constructions produce three DIFFERENT numbers:

      correct stratified mean  (20·0.5 + 8·10.5 + 2·100.5) / 30  ≈  9.83
      unstratified             same centre, several times wider
      mean of stratum means    (0.5 + 10.5 + 100.5) / 3          ≈ 37.17

    Two equal strata distinguish none of them, which is the fixture-sizing rule
    this repo wrote into CLAUDE.md after an apportionment test matched a
    reverse-order mutant by coincidence."""
    values = (
        [i / 20.0 for i in range(20)]
        + [10.0 + i / 8.0 for i in range(8)]
        + [100.0 + i / 2.0 for i in range(2)]
    )
    strata = ["low"] * 20 + ["mid"] * 8 + ["high"] * 2
    return values, strata


def test_a_stratified_draw_preserves_each_stratum_size():
    """§ Weighted samples: resampling within each stratum "so a bootstrap can't
    return a replicate whose stratum composition the design ruled out". The
    two-value stratum contributes exactly 2 rows to every draw, which pins the
    interval near 9.83 and makes it much narrower than the unstratified one."""
    values, strata = _banded_strata()
    stratified = percentile_over_units(values, seed=7, draws=2000, strata=strata)
    plain = percentile_over_units(values, seed=7, draws=2000)
    assert stratified is not None and plain is not None
    expected = sum(values) / len(values)  # 9.83…
    assert stratified.low < expected < stratified.high
    stratified_width = stratified.high - stratified.low
    plain_width = plain.high - plain.low
    # Narrower, and by a lot: the whole point of the declaration is that the
    # 2-unit stratum's contribution stops varying.
    assert stratified_width < plain_width / 2.0
    # And NOT the mean-of-stratum-means answer, which is 37.17 — a construction
    # that gave each stratum equal say would put the interval there instead.
    assert stratified.high < 20.0


def test_a_stratified_draw_is_invariant_to_row_order():
    """A fixed seed draws a fixed sequence of indices, so the multiset of
    (value, stratum) pairs must be all that matters — the same invariance the
    unstratified branch gets from sorting its pool, and the same one
    `percentile_over_units_clustered` gets from ordering its pools by contents."""
    values, strata = _banded_strata()
    pairs = list(zip(values, strata, strict=True))
    shuffled = pairs[7:] + pairs[:7]
    a = percentile_over_units(values, seed=11, draws=2000, strata=strata)
    b = percentile_over_units(
        [v for v, _ in shuffled], seed=11, draws=2000, strata=[s for _, s in shuffled]
    )
    assert a == b


def test_a_stratified_draw_is_invariant_to_stratum_labels():
    """Strata ordered by their own sorted contents, not by label — so renaming
    `low`/`mid`/`high` to `z`/`a`/`m` gives the identical interval."""
    values, strata = _banded_strata()
    renamed = {"low": "z", "mid": "a", "high": "m"}
    a = percentile_over_units(values, seed=3, draws=2000, strata=strata)
    b = percentile_over_units(
        values, seed=3, draws=2000, strata=[renamed[s] for s in strata]
    )
    assert a == b


def test_one_stratum_reproduces_the_unstratified_interval_digit_for_digit():
    """The degenerate case is not a special case: with every unit in one
    stratum, the stratified path draws n indices from one sorted pool, which is
    exactly what the unstratified path does."""
    values, _ = _banded_strata()
    a = percentile_over_units(values, seed=5, draws=2000)
    b = percentile_over_units(values, seed=5, draws=2000, strata=["only"] * len(values))
    assert a == b


def test_a_stratified_weighted_draw_keeps_each_value_with_its_weight():
    """Weights travel with values through the grouping AND the sort. Sorting the
    two sequences separately would preserve every invariance above and silently
    re-pair them — a mistake equal weights cannot see, which is why the weights
    here are as banded as the values."""
    values, strata = _banded_strata()
    weights = [1.0] * 20 + [5.0] * 8 + [50.0] * 2
    got = percentile_over_units(values, seed=9, draws=2000, weights=weights, strata=strata)
    assert got is not None
    expected = sum(v * w for v, w in zip(values, weights, strict=True)) / sum(weights)
    assert got.low < expected < got.high
    # The weighted centre (≈ 39.5) is far from the unweighted one (≈ 9.83), so a
    # re-pairing or a dropped weight lands outside this interval rather than
    # inside it.
    assert got.low > 20.0


def test_a_stratified_draw_refuses_a_misaligned_stratum_vector():
    """A length mismatch is a misaligned vector, and would produce a plausible
    number rather than an error — the same reason `strict=True` guards the
    clustered zip."""
    values, strata = _banded_strata()
    with pytest.raises(ValueError):
        percentile_over_units(values, seed=1, draws=2000, strata=strata[:-1])
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k stratified -x`. Every one fails with `TypeError: percentile_over_units() got an unexpected keyword argument 'strata'`.

- [ ] **Step 3: Implement** — in `src/publishable/stats.py`, replace `percentile_over_units`'s signature and body:

```python
def percentile_over_units(
    values: Sequence[float],
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    weights: Sequence[Any] | None = None,
    strata: Sequence[Any] | None = None,
) -> Interval | None:
```

  Append to its docstring, after the `weights` paragraphs:

```
    With `strata`, each draw preserves **each stratum's own size** and draws with
    replacement *within* it — `reference.md` § Weighted samples:
    "`resample.stratify_by` says what an independent draw is, resampling within
    each stratum so a bootstrap can't return a replicate whose stratum
    composition the design ruled out." The two ways to get this wrong both
    produce a plausible number: drawing `n` units and repairing the composition
    afterwards is the unstratified interval however carefully the counts are
    matched, and averaging the strata's own means gives every stratum equal say,
    which is a different estimator entirely (for 20/8/2 units in three bands it
    reports 37.2 where the sample mean is 9.8).

    `strata` is aligned positionally to `values`, the same contract `weights`
    has, and `strict=True` on the zip for the same reason: a length mismatch is
    a misaligned vector and would produce a number rather than an error.

    **Grouping happens before any sort and carries the pairs**, so each value
    keeps its stratum and its weight; the strata are then ordered by their own
    sorted contents rather than by label, which is what makes a relabelled
    stratum give the identical interval and what makes the one-stratum case
    reproduce the unstratified path digit for digit. Sorting values and stratum
    labels as separate sequences would preserve every invariance and silently
    re-pair them — the mistake equal-sized strata cannot see.
```

  Body — replace everything from `rng = random.Random(seed)` to the `return`:

```python
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
    # One weight vector for every branch below, so a value and its weight are
    # paired once. `checked_weights` gates before any draw rather than producing
    # `draws` worth of `nan`, and it is the one authority `validate` and
    # `kish_effective_n` also read.
    carried = None if weights is None else checked_weights(weights)
    rng = random.Random(seed)
    if strata is not None:
        # Grouped BEFORE any sort, carrying (value, weight) pairs, then each
        # group sorted and the groups ordered by their own sorted contents —
        # so the interval depends on the multiset of (value, weight, stratum)
        # triples and on nothing else, not on row order and not on the labels.
        pools: dict[Any, list[tuple[float, float]]] = {}
        pairs_in = zip(
            values,
            strata,
            [1.0] * len(values) if carried is None else carried,
            strict=True,
        )
        for value, stratum, weight in pairs_in:
            pools.setdefault(stratum, []).append((float(value), weight))
        ordered = sorted(sorted(pool) for pool in pools.values())
        means: list[float] = []
        for _ in range(draws):
            # Each stratum contributes exactly as many rows as it holds: that
            # is the composition the design ruled the alternatives out of.
            drawn = [
                pool[rng.randrange(len(pool))] for pool in ordered for _ in range(len(pool))
            ]
            if carried is None:
                means.append(sum(v for v, _ in drawn) / len(drawn))
            else:
                means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means.sort()
    elif carried is not None:
        pairs = sorted(zip(values, carried, strict=True))
        n = len(pairs)
        drawn_means = []
        for _ in range(draws):
            drawn = [pairs[rng.randrange(n)] for _ in range(n)]
            drawn_means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means = sorted(drawn_means)
    else:
        # Sorted, not just `list(values)`: with a fixed seed, `rng.randrange(n)`
        # draws the same sequence of *indices* regardless of input order, so
        # drawing from an unsorted pool would make the resample depend on row
        # order — the multiset of values must be all that matters.
        pool_flat = sorted(values)
        n = len(pool_flat)
        means = sorted(
            sum(pool_flat[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws)
        )
    lo, hi = _percentile_ranks(draws, confidence)
    return Interval(low=means[lo], high=means[hi], method="percentile_over_units")
```

  Note the one-stratum equality this preserves: with a single stratum, `ordered` holds one sorted pool of length `n` and the loop draws `n` indices from it in the same order the unweighted branch does, so `test_one_stratum_reproduces_the_unstratified_interval_digit_for_digit` holds by construction rather than by luck.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k stratified or percentile_over_units`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. The ~20 existing `percentile_over_units` tests must be untouched — none passes `strata`, and the default is `None`.

- [ ] **Step 5: Mutate** — in `stats.py`, change the draw line to ignore the stratum sizes:

```python
            drawn = [
                pool[rng.randrange(len(pool))] for pool in ordered for _ in range(1)
            ]
```

  Run `uv run pytest tests/test_stats.py -k preserves_each_stratum_size`. It must FAIL: each stratum then contributes one row, so the mean lands near the mean-of-stratum-means 37.17 and the `stratified.high < 20.0` assertion breaks — which is exactly the third candidate the banded fixture exists to separate. Delete `__pycache__`, edit `range(1)` back to `range(len(pool))` in place, re-run. Second mutation: change `ordered = sorted(sorted(pool) for pool in pools.values())` to `ordered = [sorted(pools[k]) for k in sorted(pools)]`; `test_a_stratified_draw_is_invariant_to_stratum_labels` must FAIL. Revert in place.

- [ ] **Step 6: Commit** — `feat: percentile_over_units draws within a stratum, preserving its size`.

---


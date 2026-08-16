### Task 5: `paired_percentile_of_derived` — one draw, both sides

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `UnitTable`; `_unit_table_from_rows`; `min_honest_draws(confidence) -> int`; `_percentile_ranks(n, confidence) -> tuple[int, int]`; `percentile_of_derived(collapsed, compute, seed, draws, confidence) -> tuple[Interval | None, int]`.
- Produces: `paired_percentile_of_derived(of, against, keys, compute, seed, draws=2000, confidence=0.95) -> tuple[Interval | None, int]`

This is the construction for a **derived metric**, and it is the single most likely thing in this slice to get subtly wrong.

**Draw once, apply the draw to both sides.** `docs/reference.md`: "the percentiles of the resampled difference, with **one draw over the `n_paired` intersection applied to both sides**." Two independent draws would resample the conditions apart and destroy the pairing, exactly as differencing the two sides' intervals would. Both spellings produce a plausible interval; only the paired one is narrower.

**Reuse the existing machinery rather than re-deriving it:** the same `min_honest_draws` survivor floor, the same `_percentile_ranks`, the same degenerate-draw handling (a `compute` returning `None`/`nan` or raising is a dropped draw, and ranks read off the survivors). A second copy of the rank arithmetic is how the 97.55% asymmetry returned once already.

- [ ] **Step 1: Write the failing tests**

```python
def _mean_m(t):
    vals = [v for v in t.m if v is not None]
    return sum(vals) / len(vals) if vals else None


def test_the_paired_interval_is_narrower_than_two_independent_draws():
    """The property that makes pairing worth doing. Two conditions that move
    together have a stable difference even when each side is highly variable —
    an implementation drawing independently loses exactly that."""
    of = {f"u{i}": {"m": float(i) + 0.5} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    keys = sorted(of)
    paired, _ = paired_percentile_of_derived(of, against, keys, _mean_m, seed=7)
    a, _ = percentile_of_derived(of, _mean_m, seed=7)
    b, _ = percentile_of_derived(against, _mean_m, seed=7)
    independent_width = (a.high - a.low) + (b.high - b.low)
    assert (paired.high - paired.low) < independent_width / 4


def test_the_interval_brackets_the_observed_difference():
    of = {f"u{i}": {"m": float(i) + 0.5} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got, _ = paired_percentile_of_derived(of, against, sorted(of), _mean_m, seed=7)
    assert got.low < 0.5 < got.high


def test_it_names_its_own_method():
    of = {f"u{i}": {"m": float(i) + 1.0} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got, _ = paired_percentile_of_derived(of, against, sorted(of), _mean_m, seed=7)
    assert got.method == "paired_percentile_over_units"


def test_the_same_seed_reproduces_and_a_different_one_does_not():
    of = {f"u{i}": {"m": float(i) + 1.0} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    k = sorted(of)
    assert paired_percentile_of_derived(of, against, k, _mean_m, seed=7) == \
           paired_percentile_of_derived(of, against, k, _mean_m, seed=7)
    assert paired_percentile_of_derived(of, against, k, _mean_m, seed=7) != \
           paired_percentile_of_derived(of, against, k, _mean_m, seed=99)


def test_below_the_survivor_floor_there_is_no_interval():
    of = {f"u{i}": {"m": float(i)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got, used = paired_percentile_of_derived(
        of, against, sorted(of), lambda t: None, seed=7, draws=200)
    assert got is None and used == 0
```

The first test is the load-bearing one. **If it does not fail against an implementation that draws each side independently, it is not testing what it claims** — verify that by writing the independent version temporarily and watching it fail, then reverting.

- [ ] **Step 2: Run to verify they fail, then implement**

```python
def paired_percentile_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
) -> tuple[Interval | None, int]:
    """Percentiles of the resampled difference, one draw applied to both sides.

    Drawing each side independently would resample the two conditions apart and
    destroy the pairing — the same error as differencing the two sides' own
    intervals. Both spellings produce a plausible interval; only this one is
    narrower, which is what `allocation: within` buys.
    """
    if len(keys) < 2:
        return None, 0
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        try:
            a = compute(_unit_table_from_rows([{"unit": k, **of[k]} for k in drawn]))
            b = compute(_unit_table_from_rows([{"unit": k, **against[k]} for k in drawn]))
        except Exception:  # a degenerate draw, not a fault; see percentile_of_derived
            continue
        if a is None or b is None:
            continue
        diff = float(a) - float(b)
        if math.isnan(diff):
            continue
        values.append(diff)
    if len(values) < min_honest_draws(confidence):
        return None, len(values)
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return (
        Interval(low=values[lo], high=values[hi],
                 method="paired_percentile_over_units"),
        len(values),
    )
```

The single `drawn` list used for both `of` and `against` **is** the pairing. If you find yourself calling `rng` twice, stop.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py tests/test_stats.py
git commit -m "Resample a paired difference with one draw for both sides"
```

---


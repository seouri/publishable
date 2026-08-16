## Task 14: A column metric's percentile interval in `summarize_step`

**Files:** Modify `src/publishable/stats.py`, `src/publishable/cli.py`. Test `tests/test_stats.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `stats.summarize_step(collapsed, counts, derived=None, seed=None, resample=None, draws=2000, beside_n=None, weights=None, clusters=None)` at `src/publishable/stats.py:1156`, whose recorded-column branch is `:1340–1393`; `stats.percentile_over_units(values, seed, draws, confidence, weights, strata)` (Tasks 9–11); `stats.percentile_over_units_clustered(values, keys, membership, seed, draws, confidence, weights, strata)` (Task 10); `cli._resolved_resample` and the local `resample_spec` (Task 13).
- Produces: `summarize_step(..., resample_columns: bool = False)`, and a recorded column carrying `method: percentile_over_units` (or `_clustered`) with `resample_draws: <n>` under a declared resample.

**The four combinations, all of which must land together.** Unclustered/unweighted → `percentile_over_units(values, seed, draws=draws)`. Unclustered/weighted → the same with `weights=column_weights`. Clustered/unweighted → `percentile_over_units_clustered(values, column_keys, clusters, seed, draws=draws)`. Clustered/weighted → the same with `weights=column_weights`. In every case the **value** stays what it already is (the mean, or the weighted mean) — only the interval's construction changes. `n.effective` stays Kish's size under a weight, and `n.clusters` stays the cluster count under a cluster: § Weighted samples says the weights are "in the estimate rather than in the drawing", and § Clustered units says the interval's effective `n` is the cluster count.

**`resample_draws` on a column records the requested `n`** (Task 11's verified invariant). It must be **absent** when no resample is declared — Task 1's pin asserts `"resample_draws" not in column`, and an explicit `null` there would claim resampling was attempted and produced nothing, which is the exact ambiguity the `null`-versus-`0` distinction exists to remove.

**A trap this task introduces into an existing loop.** `cli.py:1755–1770` iterates **every** metric in `step_summary` reading `resample_draws`. Today columns have no such key, so `used is None` skips them. After this task they will have one. `used == 0` emits `W-STATS-AGGREGATE-FAILED` naming `<template>.aggregate` — **a lie for a recorded column**, which `aggregate` never touched. A column's `used` is always the requested `n` and `n >= 80`, so neither branch can fire; the brief requires an **assertion** that it does not, because "cannot fire" is a claim about Task 11's invariant and this is where it is consumed.

**A `summary`-step `Estimate` is not reached by this pass.** It lands in `results.summary` through `run_record.summary_values`, never through `summarize_step`. Task 18 owns the assertion.

- [ ] **Step 1: Write the failing test** — append to `tests/test_stats.py`:

```python
def _ragged_collapsed(n: int = 40) -> dict[str, dict[str, float]]:
    return {f"u{i}": {"pred": float(i)} for i in range(n)}


def test_a_recorded_column_takes_a_percentile_interval_under_resample():
    """§ Statistical reporting: a column metric has a t-interval available, so
    resampling it is a CHOICE and `resample` is what makes it. The value is
    unchanged — the draw changes the interval, not the estimate."""
    collapsed = _ragged_collapsed()
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000)
    drawn = summarize_step(collapsed, counts, seed=5, draws=2000, resample_columns=True)
    assert plain["pred"]["method"] == "t_over_units"
    assert "resample_draws" not in plain["pred"]
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["resample_draws"] == 2000
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["ci95"] is not None
    low, high = drawn["pred"]["ci95"]
    assert low < drawn["pred"]["value"] < high


def test_a_clustered_column_takes_the_clustered_percentile_under_resample():
    """`cluster_by` decides the draw when both are declared, so the construction
    is the `_clustered` one and `n.clusters` still reports the cluster count."""
    collapsed = _ragged_collapsed(40)
    clusters = {f"u{i}": f"c{i % 8}" for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, clusters=clusters, resample_columns=True
    )
    assert drawn["pred"]["method"] == "percentile_over_units_clustered"
    assert drawn["pred"]["n"]["clusters"] == 8
    assert drawn["pred"]["resample_draws"] == 2000


def test_a_weighted_column_keeps_its_weighted_value_and_kish_size_under_resample():
    """Three things move together or the declaration is half-delivered: the
    value stays the WEIGHTED mean, `n.effective` stays Kish's size, and only the
    interval becomes a percentile. § Weighted samples puts the weights "in the
    estimate rather than in the drawing"."""
    collapsed = _ragged_collapsed(40)
    weights = {f"u{i}": 1.0 + (i % 4) for i in range(40)}
    counts = {"resolved": 40, "completed": 40, "failed": 0}
    plain = summarize_step(collapsed, counts, seed=5, draws=2000, weights=weights)
    drawn = summarize_step(
        collapsed, counts, seed=5, draws=2000, weights=weights, resample_columns=True
    )
    assert plain["pred"]["method"] == "weighted_t_over_units"
    assert drawn["pred"]["method"] == "percentile_over_units"
    assert drawn["pred"]["value"] == plain["pred"]["value"]
    assert drawn["pred"]["n"]["effective"] == plain["pred"]["n"]["effective"]
    # And the weighted centre differs from the unweighted one on this fixture,
    # so a dropped `weights=` lands outside the interval rather than inside it.
    unweighted = summarize_step(collapsed, counts, seed=5, draws=2000)
    assert drawn["pred"]["value"] != unweighted["pred"]["value"]


def test_a_column_below_two_units_reports_no_interval_under_resample():
    """`percentile_over_units` returns `None` below two units exactly as
    `t_over_units` does, so the degenerate case does not change shape — but
    `resample_draws` must still be present, saying which count was requested."""
    counts = {"resolved": 1, "completed": 1, "failed": 0}
    got = summarize_step({"u0": {"pred": 1.0}}, counts, seed=5, draws=2000,
                         resample_columns=True)
    assert got["pred"]["ci95"] is None
    assert got["pred"]["method"] is None
    assert got["pred"]["resample_draws"] == 2000
```

  And append to `tests/test_cli.py`:

```python
def test_a_declared_resample_gives_every_column_a_percentile_interval(tmp_path, capsys):
    """End to end, and the assertion the `resample_draws` warning loop needs:
    `cli`'s loop over `step_summary` reads `resample_draws` on EVERY metric, and
    a column's is now present. `used == 0` would emit
    `W-STATS-AGGREGATE-FAILED` naming the template's `aggregate`, which never
    touched a recorded column — a lie. A column's `used` is the requested `n`
    and `n >= 80`, so neither branch can fire, and this pins it."""
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        aggregate_returns="mean_pred",
        units=40,
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 500}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    aggregated = run["results"]["conditions"][0]["aggregated"]["step01_summarize_units"]
    assert aggregated["pred"]["method"] == "percentile_over_units"
    assert aggregated["pred"]["resample_draws"] == 500
    assert aggregated["pred"]["ci95"] is not None
    # The derived metric still resamples, at the same resolved count.
    assert aggregated["mean_pred"]["method"] == "percentile_over_units"
    assert aggregated["mean_pred"]["resample_draws"] == 500
    # Neither warning fires for the column.
    assert "W-STATS-AGGREGATE-FAILED" not in doc["stdout"]
    assert "W-STATS-RESAMPLE-THIN" not in doc["stdout"]
```

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_stats.py -k percentile_interval_under_resample or clustered_column or weighted_column_keeps -x`. All fail with `TypeError: summarize_step() got an unexpected keyword argument 'resample_columns'`.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/stats.py`, `summarize_step`: add `resample_columns: bool = False` as the last parameter, and replace the interval selection at `:1361–1380`:

```python
        interval: Interval | None
        value: float | None
        column_weights: list[Any] | None = None
        if weights is None:
            value = mean_of(values)
        else:
            column_weights = [weights[key] for key, _ in carried]
            value = weighted_mean_of(values, column_weights)
            n_block["effective"] = kish_effective_n(column_weights)
        # A recorded column has a t-interval available, so resampling it is a
        # CHOICE and `statistics.resample` is what makes it — § Statistical
        # reporting's asymmetry between the two `basis: units` rows. A derived
        # metric has no such fallback and is resampled either way, below.
        #
        # The VALUE is unchanged in every branch: § Weighted samples puts the
        # weights "in the estimate rather than in the drawing", and § Clustered
        # units makes the cluster the draw while `n.clusters` still reports the
        # count. Only the construction moves.
        if resample_columns and seed is not None:
            interval = (
                percentile_over_units(
                    values, seed, draws=draws, weights=column_weights
                )
                if clusters is None
                else percentile_over_units_clustered(
                    values, column_keys, clusters, seed, draws=draws,
                    weights=column_weights,
                )
            )
        elif weights is None:
            interval = (
                t_over_units(values)
                if clusters is None
                else t_over_units_clustered(values, column_keys, clusters)
            )
        else:
            interval = (
                weighted_t_over_units(values, column_weights)
                if clusters is None
                else weighted_t_over_units_clustered(
                    values, column_keys, clusters, column_weights
                )
            )
```

  and add the field to the emitted block, **absent** rather than null when no resample is declared:

```python
        out[column] = {
            **(beside_n or {}),
            "value": value,
            "basis": "units",
            "n": n_block,
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
            "correction": None,
            # Present only under a declared resample, and holding the REQUESTED
            # count: a column's draw statistic is a mean over a non-empty sample
            # and is therefore always defined, so there is no survivor count to
            # differ from it (`percentile_over_units`' own docstring gives the
            # three-branch argument). ABSENT rather than `null` where no
            # resample is declared — `null` already means "resampling was
            # attempted and produced nothing", and reusing it here would
            # reintroduce the ambiguity `resample_draws`' null-versus-0
            # distinction exists to remove.
            **({"resample_draws": draws} if resample_columns and seed is not None else {}),
        }
```

  Append a paragraph to `summarize_step`'s docstring naming `resample_columns`, stating the asymmetry (a column may be resampled; a derived metric always is), and noting that `resample_draws` is absent rather than null when it is `False`.

  (b) `src/publishable/cli.py`: pass `resample_columns=resample_spec["declared"]` at the `summarize_step` call at `:1675`. **Not** at the retry call at `:1703` — that call passes no `derived`, `seed` or `draws` either, and its job is to reproduce the recorded columns unchanged after a derived-key fault; adding a resample there would change a column's construction on the containment path only. Add a comment saying so. Task 15 handles the `report_by` call at `:1984`.

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_stats.py -k resample`, `uv run pytest tests/test_cli.py -k percentile_interval or undeclared_resample_shape` (Task 1's pin must still pass), then `uv run pytest`, `uv run mypy`, `uv run ruff check .`.

- [ ] **Step 5: Mutate** — in `stats.py`, change `weights=column_weights` to `weights=None` in the unclustered percentile call. Run `uv run pytest tests/test_stats.py -k weighted_column_keeps_its_weighted_value`. It must FAIL on the interval no longer bracketing the weighted value — which is why that test asserts the weighted and unweighted centres differ on its fixture. Delete `__pycache__`, revert in place. Second mutation: change the emitted field to `"resample_draws": draws` unconditionally (no `**({...})`); Task 1's `test_the_undeclared_resample_shape_is_pinned_absent_key` must FAIL on `"resample_draws" not in column`, and `test_a_recorded_column_takes_a_percentile_interval_under_resample` must FAIL on `"resample_draws" not in plain["pred"]`. Revert in place.

- [ ] **Step 6: Commit** — `feat: a recorded column takes a percentile interval under a declared resample`.

---


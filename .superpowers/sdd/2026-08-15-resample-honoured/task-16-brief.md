## Task 16: A column contrast's paired percentile, and the correction pool

**Files:** Modify `src/publishable/cli.py`, `src/publishable/correction.py` (docstrings). Test `tests/test_cli.py`.

**Interfaces:**
- Consumes: `cli._comparison_step_blocks(comp, *, roster, aggregated, collapsed_by_key, derived_by_key, resample_fns_by_key, seed, draws, min_reported_n, findings, where, where_id, conditions_by_index)` at `src/publishable/cli.py:653`, whose column branch is `:816–834` and whose `Member` construction is `:848–866`; `stats.paired_percentile_of_derived(of, against, keys, compute_of, compute_against, seed, draws, confidence) -> PairedResample` at `src/publishable/stats.py:822`; `stats.cohens_dz(diffs)`; `correction.Member`; `correction._corrected_bounds`; `cli._resolved_resample` (Task 13).
- Produces: a column contrast under a declared `resample` carrying `method: paired_percentile_over_units`, `cohens_d: <dz>`, a `Member` with `pool=` and `diffs=None`, and a `ci95_corrected` read off that pool.

**This is the one place H4a can produce a wrong number with a green suite. Two independent ways.**

**(1) The correction pool.** `correction._corrected_bounds` (`src/publishable/correction.py:158`) tests `if member.diffs is not None:` **first**, and only then falls through to `member.pool`. `cli.py:856` sets `diffs=None if is_derived else tuple(diffs)`, so a column contrast **always** carries diffs today. The failure mode is **not** "set both" — `Member.__post_init__` raises `ValueError` for that, loudly and catastrophically (`_compute_vs_baseline` sits outside the `try/except ContractError` around `summarize_step`, so the run would lose `run.yaml` after every execution was spent). The genuinely silent failure is **forgetting the `Member` entirely**: wire the percentile into the interval and leave lines 855–856 alone. The column contrast then carries `diffs` alone, nothing raises, and `ci95` comes from a percentile while `ci95_corrected` comes from `paired_t_over_units` **on the same row**. The rule: under a declared `resample`, a column contrast's `Member` carries the **pool** and sets **`diffs=None`**, while `cohens_dz` keeps computing from the local `diffs` list. `Member`'s own docstring — "exactly one of `pool`/`diffs`" — is what is being **honoured**, not broken.

**The family must be bigger than one or the assertion cannot fail.** At `family_size` 1, holm's level is `0.05` → confidence `0.95` → `interval_at(pool, 0.95)` reads the *same* ranks as the raw interval, so `ci95_corrected == ci95` and a `paired_t_over_units` corrected bound would be indistinguishable from a percentile one only by luck. Size the fixture to **2 comparisons × 1 metric = family 2**, rank 1 → level `0.025` → confidence `0.975` → `min_honest_draws(0.975) = 160`, which `n: 2000` clears. Then assert, **in the same test**: `ci95_corrected` strictly contains `ci95`, **and** does not equal `paired_t_over_units(diffs, confidence=0.975)` recomputed in the test from the deterministic column the step records. That second assertion is the one the mutation kills.

**(2) `col_keys`, not `base_keys`.** The column branch narrows `base_keys → col_keys` on `metric_key in of_collapsed[k] and metric_key in against_collapsed[k]`; the derived branch does not, because a derived metric has no column to be ragged about. `paired_percentile_of_derived` builds its `UnitTable`s from **whole rows**, so handing it `base_keys` for a column metric feeds `compute` rows missing that column. `UnitTable.__getattr__` returns `[row.get(name) for row in rows]` — full length, `None` where absent — so the failure depends entirely on the closure body. **State the closure exactly, then size the fixture against it.** With the body below (`sum(...) / len(...)` over the column), a `None` raises `TypeError`, which `paired_percentile_of_derived` catches as a degenerate draw and drops. **Fixture sizing:** with 1 of 40 units missing the column, ~36 % of draws survive → ~720 ≥ 160 → the interval exists and the test **passes with the bug**. Make roughly a **quarter** of the roster miss it: survival is then ~1e-5 and the interval is `None`. `n_paired` stays `len(col_keys)` and **does not discriminate** — it is already `len(col_keys)` today.

**Three docstring edits this task owes**, because `_corrected_bounds`' own docstring states a guarantee this task falsifies. It currently opens: *"A recorded column re-runs `paired_t_over_units` over the stored per-unit differences — exact at any α."* Under a declared `resample` that stops being true. Leaving it is this repo's single most repeated defect — a comment claiming a guarantee the code does not provide, twelve-plus instances — sitting in the one function whose correctness this task turns on.
1. `_corrected_bounds`: re-scope to say what now decides — a column contrast re-runs the *t* construction **when it carries diffs** and reads the pool **when it carries one**, with the declared `resample` being what puts it in the second case.
2. The paragraph after it. **Keep the "Neither redraws" sentence if it survives** — its reason is good and still holds, and a corrected interval narrower than its raw one is exactly the number this slice must not produce.
3. `Member`'s own docstring ("exactly one of `pool`/`diffs`"): say explicitly that a column contrast under `resample` carries the pool, so a reader meeting `diffs=None` on a column contrast for the first time knows it was deliberate.

**The fixture must vary the column across conditions, or every assertion here is vacuous.** `tests/test_cli.py`'s `_AGGREGATE_STEP` records `pred = float(i)` with no reference to `cfg`, so the per-unit differences are all zero: verified against the build, `paired_t_over_units([0.0] * 40)` returns `Interval(0.0, 0.0)` and `cohens_dz([0.0] * 40)` returns `None`. With an all-zero pool `interval_at` returns `(0.0, 0.0)` at every α, so "corrected is wider than raw" is `0 > 0` — **it fails under the correct implementation and passes under neither**, and the "not the *t* bound" assertion compares two zero-width intervals. This task therefore uses **`_CONDITION_SCALED_STEP`** (introduced in Task 1: `pred = float(i) * {pearson: 1.0, spearman: 2.0, kendall: 3.0}[cfg.parameters.analysis.method]`), which gives both comparisons a nonzero delta and real dispersion in both the diffs and the pool. Check in Step 4 that the family still reads `{comparisons: 2, metrics: 1}` — a comparison whose interval came back `None` is dropped by `family_members` and would shrink it.

**Out of scope, again.** `"paired": True` **stays hard-coded** at both `:808` and `:830`. `cohens_d` stays `null` on the derived branch.

- [ ] **Step 1: Write the failing test** — append to `tests/test_cli.py`:

```python
_RAGGED_COLUMN_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Scaled by the swept axis for the reason `_CONDITION_SCALED_STEP` is:
        # an identical column under both conditions makes every per-unit
        # difference zero, and a zero-variance contrast asserts nothing.
        scale = {{"pearson": 1.0, "spearman": 2.0, "kendall": 3.0}}[
            cfg.parameters.analysis.method
        ]
        units = list(io.units)
        for i, unit in enumerate(units):
            values = {{"always": float(i) * scale}}
            # A QUARTER of the roster does not carry `sometimes`. Sized that way
            # deliberately: with one unit missing, ~36 % of draws still survive
            # and a `base_keys` bug would produce an interval anyway; at a
            # quarter, survival is ~1e-5 and the interval is null.
            if i % 4 != 0:
                values["sometimes"] = float(i) * 2.0 * scale
            io.record(unit.key, values)
        return {{"n_units": len(units)}}
'''


def test_a_column_contrast_takes_the_paired_percentile_under_resample(tmp_path, capsys):
    """§ Statistical reporting: `paired_percentile_over_units` is "Every derived
    metric, and a column metric under `resample`". Cohen's dz survives — it
    differences a per-unit value, which a column has.

    `_CONDITION_SCALED_STEP`, not `aggregate_returns`: an identical column under
    both conditions gives zero differences, and `cohens_dz` of those is `None`,
    so `cohens_d is not None` would fail under the correct implementation."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        _starter_step=_CONDITION_SCALED_STEP,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry is not None
    assert entry["method"] == "paired_percentile_over_units"
    assert entry["cohens_d"] is not None      # a column HAS a per-unit value
    assert entry["paired"] is True            # still hard-coded; H4c owns it
    assert entry["ci95"] is not None


def test_a_column_contrast_corrects_off_its_own_pool_not_a_t_interval(
    tmp_path, capsys
):
    """THE test this task exists for. `_corrected_bounds` tests
    `member.diffs is not None` FIRST, so a `Member` still carrying diffs yields
    `ci95` from a percentile and `ci95_corrected` from `paired_t_over_units` on
    the same row — nothing raises, and no other test sees it.

    Two comparisons, so `family_size` is 2 × 1 = 2 and holm's rank-1 level is
    0.025 → confidence 0.975 → 160 draws needed, which 2000 clears. At
    `family_size` 1 the level is 0.05, `interval_at` reads the SAME ranks as the
    raw interval, and this assertion could not fail."""
    import math

    from publishable.stats import paired_t_over_units

    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        _starter_step=_CONDITION_SCALED_STEP,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman", "kendall"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _named_contrast(run, "method=spearman", "pred")
    assert entry is not None
    # Both comparisons carry an interval — `family_members` drops one with
    # `ci95: None`, which would shrink this to 1 and quietly weaken every
    # assertion below by loosening the corrected level from 0.025 to 0.05.
    assert entry["family_size"] == 2
    assert entry["family"] == {"comparisons": 2, "metrics": 1}
    assert entry["method"] == "paired_percentile_over_units"
    raw_low, raw_high = entry["ci95"]
    corr_low, corr_high = entry["ci95_corrected"]
    # A corrected interval is at a SMALLER alpha off the same evidence, so it
    # contains the raw one. Never narrower — that is the number a reader cannot
    # tell is wrong. Strictly wider is assertable only because
    # `_CONDITION_SCALED_STEP` gives the pool real dispersion: over an
    # all-zero pool `interval_at` returns (0.0, 0.0) at every alpha and this
    # would be `0 > 0`, failing under the CORRECT implementation.
    assert corr_low <= raw_low and corr_high >= raw_high
    assert (corr_high - corr_low) > (raw_high - raw_low)
    # And it is NOT the t-interval. Recompute the bound the buggy path would
    # have produced, from the same per-unit differences the step's own scaling
    # determines — `pred` is `float(i)` at pearson and `2 * float(i)` at
    # spearman, so the difference for unit `i` is exactly `float(i)`.
    level = 0.05 / entry["family_size"]
    diffs = [float(i) for i in range(40)]
    t_bound = paired_t_over_units(diffs, confidence=1.0 - level)
    assert t_bound is not None      # non-degenerate, unlike an all-zero column
    assert not (
        math.isclose(corr_low, t_bound.low) and math.isclose(corr_high, t_bound.high)
    )


def test_a_column_contrast_draws_from_the_columns_own_keys(tmp_path, capsys):
    """`paired_percentile_of_derived` builds its `UnitTable`s from WHOLE ROWS, so
    `base_keys` feeds `compute` rows missing the column — `UnitTable.__getattr__`
    pads with `None`, and the closure's `sum(...)` raises `TypeError`, which the
    construction catches as a degenerate draw and drops. A quarter of the roster
    missing makes survival ~1e-5, so the interval is null under the bug and real
    under the fix. One unit missing would leave ~720 survivors and pass either
    way."""
    doc = run_a_project(
        tmp_path, capsys=capsys, units=40,
        sweep={"baseline": {"analysis.method": "pearson"},
               "grid": {"analysis.method": ["spearman"]}},
        statistics={"correction": "holm",
                    "resample": {"method": "bootstrap", "n": 2000}},
        _starter_step=_RAGGED_COLUMN_STEP,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    ragged = _named_contrast(run, "method=spearman", "sometimes")
    assert ragged is not None
    assert ragged["method"] == "paired_percentile_over_units"
    assert ragged["ci95"] is not None
    assert ragged["n_paired"] == 30           # 40 units, every 4th missing
    # The full column is unaffected, so this cannot pass by both being broken.
    full = _named_contrast(run, "method=spearman", "always")
    assert full is not None
    assert full["ci95"] is not None
    assert full["n_paired"] == 40
```

  `_starter_step` and `_CONDITION_SCALED_STEP` both come from Task 1 and need no new work here.

- [ ] **Step 2: Run it, confirm it fails** — `uv run pytest tests/test_cli.py -k column_contrast -x`. All three fail: the method is `paired_t_over_units` today and there is no pool for `_corrected_bounds` to read.

- [ ] **Step 3: Implement** —

  (a) `src/publishable/cli.py`, `_comparison_step_blocks`: add a `resample_columns: bool` keyword parameter (passed by `_compute_vs_baseline` and `_compute_declared_contrasts`, which each gain the same parameter, from `command_run`'s `resample_spec["declared"]`). Replace the column branch at `:816–834`:

```python
            else:
                col_keys = [
                    k
                    for k in base_keys
                    if metric_key in of_collapsed[k] and metric_key in against_collapsed[k]
                ]
                diffs = [
                    of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
                    for k in col_keys
                ]
                n_paired = len(col_keys)
                resampled = None
                if resample_columns and n_paired >= 2:
                    # `col_keys`, NOT `base_keys`. The derived branch above uses
                    # `base_keys` because a derived metric has no column to be
                    # ragged about; a recorded column does.
                    # `paired_percentile_of_derived` builds its `UnitTable`s from
                    # whole rows, so `base_keys` here would feed `compute` rows
                    # missing this column — `UnitTable.__getattr__` pads with
                    # `None` and the mean below raises, which the construction
                    # catches as a degenerate draw and silently drops. A quarter
                    # of a roster missing the column nulls the interval; one unit
                    # missing leaves it looking fine, which is why this is a
                    # correctness rule and not a tidiness one.
                    #
                    # The same callable twice: both sides compute the mean of the
                    # same column, which is a normal call rather than the
                    # shared-closure cancellation `paired_percentile_of_derived`
                    # warns about — that one is about a SWEPT AXIS changing which
                    # formula `aggregate` runs, and a column mean is one formula.
                    def _column_mean(table: UnitTable, _name: str = metric_key) -> float:
                        column = getattr(table, _name)
                        return sum(column) / len(column)

                    resampled = paired_percentile_of_derived(
                        of_collapsed,
                        against_collapsed,
                        col_keys,
                        _column_mean,
                        _column_mean,
                        seed,
                        draws=draws,
                    )
                    interval = resampled.interval
                else:
                    interval = paired_t_over_units(diffs)
                metric_block[metric_key] = {
                    # The mean of the per-unit differences over `col_keys` — the
                    # same unit set the interval is drawn from, and identical to
                    # the difference of the two column means over that set, so
                    # the point estimate and the pool cannot drift onto
                    # different rosters.
                    "delta": mean_of(diffs),
                    "basis": "units",
                    "paired": True,
                    "method": interval.method if interval else None,
                    "n_paired": n_paired,
                    "ci95": [interval.low, interval.high] if interval else None,
                    # Cohen's dz survives the switch: it differences a PER-UNIT
                    # value, which a column has and a derived metric does not,
                    # and it is computed from the local `diffs` list rather than
                    # from anything the `Member` carries.
                    "cohens_d": cohens_dz(diffs),
                    "correction": None,
                }
```

  and the `Member` construction at `:848–866`:

```python
            # `Member` requires exactly one of `pool`/`diffs` wherever there is
            # an interval to correct: the draws a percentile interval was read
            # off, or the per-unit differences a *t* interval was computed from.
            #
            # **A column contrast under a declared `resample` carries the POOL
            # and sets `diffs=None`.** `_corrected_bounds` tests `diffs` FIRST
            # and only then falls through to `pool`, so leaving `diffs` set here
            # — the natural thing to do, since `cohens_dz` still needs them —
            # would give this row a `ci95` from a percentile and a
            # `ci95_corrected` from `paired_t_over_units`. Nothing raises and no
            # reader can tell. `cohens_dz` is computed above from the local list,
            # which is why the `Member` does not need it.
            corrected_from_pool = is_derived or resample_columns
            members.append(
                Member(
                    where=where_id,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if corrected_from_pool and resampled else None,
                    diffs=None if corrected_from_pool else tuple(diffs),
                    declaration_index=0,
                )
            )
```

  Note that `resampled` is now assigned in **both** branches of `is_derived`, so the "reset per metric" comment at `:781–787` still applies and must be kept — it is what stops a later metric inheriting an earlier one's pool.

  (b) `src/publishable/correction.py`, `_corrected_bounds`'s docstring — replace the first paragraph:

```
    """The interval at `level`, from the same evidence as the raw one.

    **What decides the construction is which field the member carries, not what
    kind of metric it is.** A member carrying per-unit differences re-runs
    `paired_t_over_units` over them — exact at any α. A member carrying a draw
    pool reads a second rank pair off it. A derived metric always carries a
    pool; a recorded column carries differences by default and **carries a pool
    instead under a declared `statistics.resample`**, because its raw interval
    was then a percentile and a *t* corrected bound would be its counterpart in
    name only — narrower or wider than the truth by construction rather than by
    evidence. `Member.__post_init__` enforces exactly one of the two, so this
    order is a preference among impossible-to-have-both fields rather than a
    tie-break.

    Neither redraws: a fresh resample at the corrected level could land *inside*
    the raw interval, and a corrected interval narrower than its raw one is
    precisely the number a reader cannot tell is wrong.
    """
```

  (c) `src/publishable/correction.py`, `Member`'s docstring — extend the "Exactly one of them is set" sentence:

```
    `pool` and `diffs` are how the corrected interval is built from the *same*
    evidence as the raw one — the stored draws for a percentile interval, the
    stored per-unit differences for a *t* one. Exactly one of them is set.
    **A recorded column carries `diffs` by default and `pool` under a declared
    `statistics.resample`**, which is what makes a percentile raw interval and a
    percentile corrected one the same construction; a reader meeting
    `diffs=None` on a column contrast is meeting that, not an omission. Cohen's
    *dz* is computed at the call site from its own list and does not travel here.
```

- [ ] **Step 4: Run, confirm it passes** — `uv run pytest tests/test_cli.py -k column_contrast or undeclared_resample_shape`, then `uv run pytest`, `uv run mypy`, `uv run ruff check .`. Then **measure the rebuild cost**, which the scoping asks for: `paired_percentile_of_derived` builds two `UnitTable`s of *n* rows **per draw**, currently paid by one or two derived metrics and now by every recorded column × every comparison. Run a throwaway timing probe in the scratchpad:

```python
import time
from publishable.stats import paired_percentile_of_derived
of = {f"u{i}": {"m": float(i)} for i in range(240)}
against = {f"u{i}": {"m": float(i) * 1.1} for i in range(240)}
keys = list(of)
def mean_m(t): return sum(t.m) / len(t)
start = time.perf_counter()
paired_percentile_of_derived(of, against, keys, mean_m, mean_m, 1, draws=2000)
print(f"{time.perf_counter() - start:.2f}s per column-comparison at n=240, 2000 draws")
```

  Record the number in the commit message. If it exceeds ~2 s per column-comparison, write the cheap direct construction instead — draw index vectors once and take column means, skipping `UnitTable` entirely — and say so; the pool it returns must still be the sorted list of differences `interval_at` reads ranks off.

- [ ] **Step 5: Mutate** — the mutation is **forgetting the `Member`**, which is the silent failure and not the loud one. In `cli.py`, change `corrected_from_pool = is_derived or resample_columns` back to `corrected_from_pool = is_derived`. Run `uv run pytest tests/test_cli.py -k corrects_off_its_own_pool`. It must FAIL — the row keeps `diffs`, `_corrected_bounds` takes the *t* branch, and both the containment assertion and the not-equal-to-the-t-bound assertion break. Do **not** mutate by setting both fields: `Member.__post_init__` raises `ValueError` for that, the run loses `run.yaml`, and the test fails for a reason that proves nothing about the assertion. Delete `__pycache__`, edit the line back in place, re-run. Second mutation: change `col_keys` to `base_keys` in the `paired_percentile_of_derived` call. `test_a_column_contrast_draws_from_the_columns_own_keys` must FAIL on `ragged["ci95"] is not None` while `full` still passes — which is the whole reason the fixture carries both a full and a quarter-missing column. Revert in place.

- [ ] **Step 6: Commit** — `feat: a column contrast resamples over its own keys and corrects off its own pool` (include the timing figure).

---


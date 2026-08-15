# Correction family (S4c) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every interval a run puts in front of a reader is corrected for the family it belongs to, or records why it isn't.

**Architecture:** A pure `correction.py` collects the run's comparisons into a family, ranks them, and returns the corrected fields for each. `cli.py` runs it after both `vs_baseline` and `results.contrasts` exist, because the family spans conditions. A corrected interval is built from the *same evidence* as the raw one — the same stored per-unit differences at a different *t* quantile, or a second rank pair off the same stored draw pool — so `corrected ⊇ raw` holds by construction and not by two RNG calls agreeing.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy, scipy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. (`ruff format` reformats ~30 pre-existing files — do not run it; `ruff check` is the gate.)
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `stats.py`, `sweep.py`, `contrasts.py` and the new `correction.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one — including on a config value of the wrong *type*. Guard before `len()`, `in`, or iteration.
- Every `E-`/`W-` identifier must have a test that produces it; for a validate-time code that means through `validate_config`.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **α is 0.05 and is not configurable.** `ci95` is in the field name. Only the corrected *level* varies.
- **A draw pool must never reach `run.yaml`.** 2000 floats in the record is a defect; the evidence travels beside the record, not inside it.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/correction.py` *(new)* | **Pure.** `Member`; family membership; ranking; the per-method corrected fields |
| `src/publishable/stats.py` | `interval_at`; `paired_percentile_of_derived` returns its draw pool; `percentile_over_units` gains the honest-draw floor |
| `src/publishable/cli.py` | Carry each comparison's evidence out of `_comparison_step_blocks`; run the pass; write the fields back; `confounded`/`differs_on` |
| `src/publishable/validate.py` | `W-STATS-FAMILY`'s documented condition; the `fdr_bh` warning; the `correction` shape guard; `statistics.contrasts` in `_check_shape`; `max_ineligible_fraction` |
| `docs/reference.md` | The missing `family` breakout at the § Contrasts entry |

**Read before starting:** `docs/superpowers/specs/2026-08-10-correction-family-design.md`, and `reference.md` § Statistical reporting (the correction table, the ranking paragraph, the family paragraphs).

---

### Task 1: `reference.md`'s missing `family` breakout

The document leads, so this lands before any code reads it.

**Files:**
- Modify: `docs/reference.md` (the § Contrasts `results.contrasts` example, the entry carrying `family_size: 7`)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing in code. Task 9's end-to-end test asserts `family` is present on every corrected entry, which is the rule this edit makes uniform.

- [ ] **Step 1: Find the defect**

Run: `grep -n "family_size" docs/reference.md`

Three entries report `family_size`. Two carry a `family:` breakout beside it (the worked example, twice). One does not — the § Contrasts entry with `family_size: 7`. The prose at § Statistical reporting says the count "is reported broken out rather than as a single integer, so the count is auditable instead of asserted", so the entry lacking it contradicts its own section.

- [ ] **Step 2: Add the breakout**

In that entry, change:

```yaml
               correction: holm, correction_level: 0.0071, family_size: 7}
```

to:

```yaml
               correction: holm, correction_level: 0.0071,
               family_size: 7, family: {comparisons: 7, metrics: 1}}
```

`comparisons: 7, metrics: 1` is the only split consistent with the surrounding example, which reports one metric (`prob`) for `step03_screen`.

- [ ] **Step 3: Run the mechanical pass**

Write a throwaway script (the repo ships no checker, per `CLAUDE.md`). It must check, **skipping fenced code blocks**: every relative link and `#anchor` resolves, no two headings collide on an anchor, every table row matches its header's column count, and no line carries trailing whitespace, a tab, or invisible unicode.

Note the edit itself is *inside* a fenced block, so the table and anchor checks will not see it — run them anyway to confirm the edit broke nothing above or below.

- [ ] **Step 4: Run the cross-document pass**

The changed value is inside the § Contrasts example, which is **not** the shared worked example (`cohort-pilot`). Confirm that: the entry's `id` is `invariance`, its conditions are `04_occasions=3`/`06_occasions=12`, and its step is `step03_screen` — none of which belong to the worked example's four steps. So no other document needs a matching change. Verify by grepping the four documents for `family_size: 7` and for `invariance`: neither appears elsewhere.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "Report the family breakout where the count is asserted"
```

---

### Task 2: `interval_at`, and the pool `paired_percentile_of_derived` already has

**Files:**
- Modify: `src/publishable/stats.py`
- Test: `tests/test_stats.py`

**Interfaces:**
- Consumes: `_percentile_ranks(draws, confidence)`, `min_honest_draws(confidence)`, `Interval` — all already in `stats.py`.
- Produces:
  - `interval_at(pool: Sequence[float], confidence: float) -> tuple[float, float] | None`
  - `@dataclass(frozen=True) class PairedResample: interval: Interval | None; draws_used: int; pool: list[float]`
  - `paired_percentile_of_derived(...) -> PairedResample` — **the return type changes** from `tuple[Interval | None, int]`.

Only this one construction returns a pool. `percentile_of_derived` and `percentile_over_units` keep their shapes: the family is comparisons × metrics, so a per-condition `aggregated` metric is never corrected.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_stats.py`:

```python
def test_interval_at_reads_a_wider_pair_of_ranks_at_a_smaller_alpha():
    """A corrected interval is an interval at a smaller α. Read off the same
    pool, a smaller α must reach further into both tails — that is the whole
    mechanism, and the nesting it produces is what makes a corrected interval
    honest beside its raw one."""
    pool = [float(i) for i in range(2000)]
    raw = interval_at(pool, 0.95)
    corrected = interval_at(pool, 0.025)
    assert raw is not None and corrected is not None
    assert corrected[0] < raw[0]
    assert corrected[1] > raw[1]


def test_interval_at_refuses_a_pool_too_small_for_the_level():
    """`min_honest_draws` is the floor below which both percentile ranks are not
    interior and the interval is systematically too narrow. At α/40 the floor is
    3200 draws, so a 2000-draw pool has no honest interval at that level — and a
    number would be worse than a null."""
    pool = [float(i) for i in range(2000)]
    assert min_honest_draws(1.0 - 0.00125) > 2000
    assert interval_at(pool, 1.0 - 0.00125) is None
    assert interval_at(pool, 0.95) is not None


def test_the_paired_resample_carries_the_pool_it_read_its_interval_from():
    """The corrected interval comes from this pool, so the raw interval's own
    endpoints must be in it at the raw ranks. Returning a pool that is not the
    one the interval was read off would make every corrected interval a
    different construction's answer."""
    of = {f"u{i}": {"m": float(i) + (1.0 if i % 2 == 0 else 0.0)} for i in range(60)}
    against = {f"u{i}": {"m": float(i)} for i in range(60)}
    got = paired_percentile_of_derived(of, against, sorted(of), _mean_m, _mean_m, seed=7)
    assert got.interval is not None
    assert len(got.pool) == got.draws_used
    assert got.pool == sorted(got.pool)
    lo, hi = _percentile_ranks(len(got.pool), 0.95)
    assert got.pool[lo] == got.interval.low
    assert got.pool[hi] == got.interval.high
```

Add `interval_at` and `PairedResample` to the `from publishable.stats import (...)` block at the top of the file, keeping it alphabetical (ruff `I` will fail otherwise).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_stats.py -k "interval_at or carries_the_pool" -v`
Expected: FAIL with `ImportError: cannot import name 'interval_at'`.

- [ ] **Step 3: Implement**

In `stats.py`, add after `_percentile_ranks`:

```python
def interval_at(pool: Sequence[float], confidence: float) -> tuple[float, float] | None:
    """The endpoints a sorted draw pool implies at `confidence`.

    Factored out so a corrected interval is a second rank pair off the *same*
    pool the raw interval was read from, rather than a fresh resample that
    happens to share a seed. That makes `corrected ⊇ raw` a property of the
    arithmetic instead of a property of two RNG calls agreeing — and a
    corrected interval narrower than its raw one is the kind of number a reader
    cannot detect is wrong.

    `None` below `min_honest_draws(confidence)`: a correction that pushes the
    level past what the pool can support has no honest interval to report, and
    the caller records `ci95_corrected: null` rather than a too-narrow number.
    """
    if len(pool) < min_honest_draws(confidence):
        return None
    lo, hi = _percentile_ranks(len(pool), confidence)
    return pool[lo], pool[hi]
```

Then change `paired_percentile_of_derived`'s return. Add the record type beside `Interval`:

```python
@dataclass(frozen=True)
class PairedResample:
    """A paired percentile interval and the pool it was read from.

    The pool travels so a caller can build the *corrected* interval at a
    smaller α off the same draws (`interval_at`). It is deliberately not a
    third tuple element: a positional `[2]` at a call site says nothing about
    what it holds, and this value must never reach `run.yaml`.
    """

    interval: Interval | None
    draws_used: int
    pool: list[float]
```

In the function body, replace the two `return` statements:

```python
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
```

and, at the end:

```python
    if len(values) < min_honest_draws(confidence):
        return PairedResample(interval=None, draws_used=len(values), pool=sorted(values))
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return PairedResample(
        interval=Interval(
            low=values[lo], high=values[hi], method="paired_percentile_over_units"
        ),
        draws_used=len(values),
        pool=values,
    )
```

Note the too-few-survivors branch now returns the pool as well — a caller cannot build a corrected interval from it either, but returning `[]` there would make `len(pool) == draws_used` false and hide how many draws survived.

- [ ] **Step 4: Update every existing call site**

Run: `grep -rn "paired_percentile_of_derived" src/ tests/`

In `src/publishable/cli.py`, the derived branch of `_comparison_step_blocks`:

```python
                    if n_paired >= 2:
                        resampled = paired_percentile_of_derived(
                            of_collapsed,
                            against_collapsed,
                            base_keys,
                            compute_of,
                            compute_against,
                            seed,
                            draws=draws,
                        )
                        interval = resampled.interval
```

In `tests/test_stats.py`, every `got, _ = paired_percentile_of_derived(...)` becomes `got = paired_percentile_of_derived(...).interval`, and every `got, used = ...` becomes two reads off the returned record. The two seed-reproducibility assertions comparing whole return values still work — `PairedResample` is frozen, so `==` compares all three fields, which is a *stronger* check than before.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`
Expected: all pass. Every pre-existing `paired_percentile_of_derived` assertion must still hold — this task changes a return shape, not a number.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/stats.py tests/test_stats.py src/publishable/cli.py
git commit -m "Return the draw pool a corrected interval is read from"
```

---

### Task 3: `Member` and family membership

**Files:**
- Create: `src/publishable/correction.py`
- Test: `tests/test_correction.py` *(new)*

**Interfaces:**
- Consumes: nothing from other modules. Pure data in, pure data out.
- Produces:
  - `ALPHA = 0.05`
  - `@dataclass(frozen=True) class Member: where: str; condition_index: int; step: str; metric: str; delta: float; ci95: tuple[float, float]; pool: tuple[float, ...] | None; diffs: tuple[float, ...] | None`
  - `family_members(entries: Sequence[Member]) -> list[Member]`
  - `family_shape(members: Sequence[Member]) -> tuple[int, dict[str, int]]` returning `(family_size, {"comparisons": c, "metrics": m})`

`cli.py` builds the `Member` list; this module decides who is *in* the family and how big it is. `where` is what the record shows (a condition index rendered as a string, or a contrast id); `condition_index` is the numeric tie-break key, which `where` cannot serve as.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_correction.py`:

```python
import pytest

from publishable.correction import ALPHA, Member, family_members, family_shape


def _m(where="1", step="s", metric="r", delta=0.1, ci95=(0.0, 0.2), index=1):
    return Member(
        where=where,
        condition_index=index,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=None,
        diffs=(0.1, 0.2, 0.3),
    )


def test_alpha_is_five_percent_and_not_configurable():
    """`ci95` is in every record field name, so the raw confidence is fixed and
    only the corrected level varies. A config field for it would have to rename
    the record field."""
    assert ALPHA == 0.05


def test_a_member_with_no_interval_is_not_in_the_family():
    """Counted-iff-corrected: a metric reported without an interval is not a
    comparison a reader can read as significant, so it neither takes a slot nor
    consumes a rank. `cli` passes `ci95=None` for it."""
    with_interval = _m(metric="r")
    without = Member(
        where="1", condition_index=1, step="s", metric="n_units", delta=3.0,
        ci95=None, pool=None, diffs=None,
    )
    assert family_members([with_interval, without]) == [with_interval]


def test_the_family_is_comparisons_times_metrics():
    """`reference.md`: "The family is comparisons × metrics, not comparisons." A
    six-condition sweep is five comparisons, but three metrics per step means a
    reader is shown fifteen intervals."""
    members = [
        _m(where=str(c), index=c, metric=k)
        for c in (1, 2, 3, 4, 5)
        for k in ("r", "rmse", "auc")
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 5, "metrics": 3}
    assert size == 15


def test_the_worked_example_is_two_comparisons_and_one_metric():
    """`reference.md`'s worked example: 3 conditions give 2 baseline comparisons,
    one metric gives `metrics: 1`, so `family_size: 2`. This is the number the
    acceptance test asserts, pinned here at the arithmetic."""
    members = [_m(where="1", index=1, metric="r"), _m(where="2", index=2, metric="r")]
    size, shape = family_shape(family_members(members))
    assert size == 2
    assert shape == {"comparisons": 2, "metrics": 1}


def test_a_contrast_and_a_baseline_comparison_are_both_comparisons():
    """`reference.md`: "A 'comparison' is a baseline contrast or a declared one" —
    both put an interval in front of a reader. Counting only `vs_baseline`
    under-corrects by exactly the declared contrasts a config asked for."""
    members = [_m(where="1", index=1), _m(where="sensitivity", index=1)]
    size, shape = family_shape(family_members(members))
    assert shape["comparisons"] == 2
    assert size == 2


def test_a_metric_absent_from_one_comparison_still_counts_as_a_metric():
    """The product can exceed the member count. That is the conservative
    direction — a larger family means a smaller α and a wider corrected
    interval — and `reference.md`'s own arithmetic is the product. Pinned so
    nobody "fixes" it into the member count."""
    members = [
        _m(where="1", index=1, metric="r"),
        _m(where="1", index=1, metric="rmse"),
        _m(where="2", index=2, metric="r"),
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 2, "metrics": 2}
    assert size == 4  # not 3
```

Note `Member.ci95` must accept `None`, so its annotation is `tuple[float, float] | None`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_correction.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'publishable.correction'`.

- [ ] **Step 3: Implement**

Create `src/publishable/correction.py`:

```python
"""The correction family: who is in it, how they rank, and what each one gets.

Pure: comparisons in, corrected fields out. `reference.md` § Statistical
reporting is the specification — the family is comparisons × metrics, the rank
is the point estimate over half the raw interval's width, and a corrected
interval is an interval at a smaller α.
"""

from collections.abc import Sequence
from dataclasses import dataclass

ALPHA = 0.05


@dataclass(frozen=True)
class Member:
    """One correctable interval, and the evidence it was built from.

    `pool` and `diffs` are how the corrected interval is built from the *same*
    evidence as the raw one — the stored draws for a derived metric, the stored
    per-unit differences for a recorded column. Exactly one of them is set.
    Neither may reach `run.yaml`: they are tuples so a member cannot be mutated
    into the record by accident.
    """

    where: str
    condition_index: int
    step: str
    metric: str
    delta: float
    ci95: tuple[float, float] | None
    pool: tuple[float, ...] | None
    diffs: tuple[float, ...] | None


def family_members(entries: Sequence[Member]) -> list[Member]:
    """The subset that is corrected, and therefore counted.

    `reference.md`: "Only metrics core corrects are counted — that is, `basis:
    units` metrics, since a metric reported without an interval isn't a
    comparison anyone can read as significant." A reported `Estimate` never
    reaches here (core did not compute it and has no standing to correct it),
    and neither does a reporting stratum (it describes rather than compares) —
    both are excluded by `cli` never building a `Member` for them, which is
    where the distinction is visible.
    """
    return [e for e in entries if e.ci95 is not None]


def family_shape(members: Sequence[Member]) -> tuple[int, dict[str, int]]:
    """`(family_size, {"comparisons": c, "metrics": m})`, as the record carries it.

    The size is the **product**, per `reference.md`: "The family is comparisons ×
    metrics, not comparisons. A six-condition sweep is five comparisons, but if
    each step reports three numeric metrics, a reader is being shown fifteen
    intervals and any of them can carry the paper."

    Where a metric is recorded in one comparison and not another, the product
    exceeds the number of members. That is deliberate and conservative — a
    larger family is a smaller α and a wider corrected interval — and it is not
    a bug to be reconciled down to the member count.

    Broken out rather than returned as one integer because `reference.md`
    requires the count be auditable: "a reviewer can check it against the table."
    """
    comparisons = len({m.where for m in members})
    metrics = len({(m.step, m.metric) for m in members})
    return comparisons * metrics, {"comparisons": comparisons, "metrics": metrics}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_correction.py -v && uv run ruff check . && uv run mypy`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "Decide who is in the correction family"
```

---

### Task 4: Ranking the family

**Files:**
- Modify: `src/publishable/correction.py`
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: `Member` from Task 3.
- Produces: `rank_family(members: Sequence[Member]) -> list[Member]` — strongest first, so the returned index + 1 is the rank.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_correction.py`:

```python
from publishable.correction import rank_family  # add to the existing import


def test_the_family_ranks_by_estimate_over_half_width():
    """`reference.md`: the ranking statistic is "the point estimate over half the
    raw `ci95` width, largest first" — the one quantity every member has, since
    Holm's own p-value is unavailable here (a `null_test` supplies one only where
    `shuffle` names an attribute, which a parameter-axis contrast never is).

    These are the worked example's two members: kendall at 0.169 over a
    half-width of 0.044 is 3.84, spearman at 0.026 over 0.033 is 0.79. Ranking
    on the raw *width* instead would order them the other way, since kendall's
    interval is the wider of the two."""
    kendall = _m(where="2", index=2, metric="r", delta=-0.169, ci95=(-0.213, -0.125))
    spearman = _m(where="1", index=1, metric="r", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([spearman, kendall])] == ["2", "1"]


def test_the_ranking_statistic_uses_the_magnitude_not_the_signed_estimate():
    """Kendall's delta is negative and it is the *strongest* member. Ranking on
    the signed estimate puts every negative delta last regardless of its
    evidence, which would silently hand the smallest correction to the members
    that most need it."""
    strong_negative = _m(where="a", index=0, delta=-0.169, ci95=(-0.213, -0.125))
    weak_positive = _m(where="b", index=1, delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([weak_positive, strong_negative])] == ["a", "b"]


def test_ties_break_by_condition_index_then_metric_name():
    """`reference.md`: "Ties break by condition index, then by metric name in
    declaration order, so a rank is a function of the record rather than of an
    iteration order." Two members with identical evidence must rank the same way
    whichever order they arrive in."""
    a = _m(where="2", index=2, metric="auc", delta=0.1, ci95=(0.0, 0.2))
    b = _m(where="1", index=1, metric="rmse", delta=0.1, ci95=(0.0, 0.2))
    c = _m(where="1", index=1, metric="auc", delta=0.1, ci95=(0.0, 0.2))
    assert [(m.condition_index, m.metric) for m in rank_family([a, b, c])] == [
        (1, "auc"),
        (1, "rmse"),
        (2, "auc"),
    ]
    assert rank_family([a, b, c]) == rank_family([c, b, a])


def test_a_zero_width_interval_ranks_first_rather_than_dividing_by_zero():
    """A point-mass bootstrap is legitimate (S4b task 5 established it), so a
    half-width of exactly 0.0 is reachable and must not raise. Infinite evidence
    ranks first, which is also what the ratio's limit says."""
    point_mass = _m(where="a", index=0, delta=0.5, ci95=(0.5, 0.5))
    ordinary = _m(where="b", index=1, delta=0.169, ci95=(0.125, 0.213))
    assert [m.where for m in rank_family([ordinary, point_mass])] == ["a", "b"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_correction.py -k rank -v`
Expected: FAIL with `ImportError: cannot import name 'rank_family'`.

- [ ] **Step 3: Implement**

Append to `correction.py`:

```python
def _evidence_ratio(member: Member) -> float:
    """`abs(delta)` over half the raw interval's width, the ranking statistic.

    Monotone in the evidence each construction encodes, and defined whether the
    interval was t-based or percentile — which is exactly what a p-value is not.
    A zero-width interval (a point-mass bootstrap, which S4b established is
    legitimate) has infinite evidence rather than a `ZeroDivisionError`.
    """
    assert member.ci95 is not None  # family_members dropped the others
    half = (member.ci95[1] - member.ci95[0]) / 2.0
    if half <= 0.0:
        return float("inf")
    return abs(member.delta) / half


def rank_family(members: Sequence[Member]) -> list[Member]:
    """Strongest first, so a member's rank is its index + 1.

    Ties break by condition index, then by metric name, so the ordering is a
    function of the record rather than of whichever order `cli` happened to
    build the members in. `reference.md` requires that: a rank decides a
    correction level, and a level that moved with iteration order would make
    two identical runs disagree.
    """
    return sorted(
        members,
        key=lambda m: (-_evidence_ratio(m), m.condition_index, m.metric),
    )
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_correction.py -v && uv run ruff check . && uv run mypy`
Expected: PASS.

- [ ] **Step 5: Prove the tests discriminate**

Apply each mutation, run the named test, confirm it fails, revert:

| Mutation in `correction.py` | Must fail |
|---|---|
| `key=lambda m: (half_width(m), ...)` — rank by raw width | `test_the_family_ranks_by_estimate_over_half_width` |
| drop `abs()` in `_evidence_ratio` | `test_the_ranking_statistic_uses_the_magnitude_not_the_signed_estimate` |
| drop the `m.condition_index, m.metric` tie-break keys | `test_ties_break_by_condition_index_then_metric_name` |
| `return abs(member.delta) / half` with no `half <= 0.0` guard | `test_a_zero_width_interval_ranks_first_rather_than_dividing_by_zero` |

Revert with `git checkout -- src/publishable/correction.py` after each, and confirm `git status --porcelain` is empty before continuing.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "Rank a family by the one statistic every member has"
```

---

### Task 5: The corrected fields, per method

**Files:**
- Modify: `src/publishable/correction.py`
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: `Member`, `ALPHA`, `rank_family`; `stats.interval_at` and `stats.paired_t_over_units` (both pure, so `correction.py` may import `stats`).
- Produces: `corrected_fields(members: Sequence[Member], method: str) -> dict[tuple[str, str, str], dict[str, Any]]`, keyed by `(where, step, metric)`. Each value holds the keys to merge onto that record entry, plus `thin` — a bool the caller turns into `W-STATS-CORRECTED-THIN`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_correction.py`:

Two imports to add at the top of the file: `corrected_fields` onto the existing `from publishable.correction import (...)` line, and `from publishable.stats import paired_t_over_units` — the fixture builds each member's raw interval with the same function the implementation re-runs, which is what makes the "corrected at α equals raw" assertion mean something. Keep both blocks alphabetical or ruff `I001` fails.

```python
def _from_diffs(where, index, mean, spread, metric="r"):
    """A member whose `ci95` **is** the t interval over its own `diffs`.

    This matters: `corrected_fields` rebuilds a column metric's corrected
    interval by re-running `paired_t_over_units` over `diffs`, so a member whose
    `ci95` was hand-written to some other value would make "corrected at α equals
    raw" compare two unrelated numbers and fail against a correct
    implementation. Deriving both from one source keeps the assertion about
    Holm's level rather than about the fixture.
    """
    diffs = tuple(mean + spread * ((i % 5) - 2) for i in range(228))
    interval = paired_t_over_units(diffs)
    assert interval is not None
    return Member(
        where=where, condition_index=index, step="step03_analyze", metric=metric,
        delta=sum(diffs) / len(diffs), ci95=(interval.low, interval.high),
        pool=None, diffs=diffs,
    )


def _two_member_family():
    """Two members, the first carrying much the stronger evidence — the worked
    example's shape (kendall against spearman), with the same wide gap in the
    ranking ratio and intervals that are genuinely their own construction."""
    strong = _from_diffs("2", 2, mean=-0.169, spread=0.02)
    weak = _from_diffs("1", 1, mean=0.026, spread=0.30)
    return strong, weak


def test_holm_corrects_the_weakest_member_by_nothing():
    """`reference.md`: "the weakest comparison in a family is corrected by
    nothing — at rank m the level is α itself", which the worked example shows:
    spearman is rank 2 of 2, so `correction_level: 0.05` and its corrected
    interval *is* its raw one. That is Holm working, not a correction that
    failed, and it is the property that makes Holm more powerful than
    Bonferroni."""
    strong, weak_member = _two_member_family()
    got = corrected_fields([strong, weak_member], "holm")
    weak = got[("1", "step03_analyze", "r")]
    assert weak["correction_level"] == pytest.approx(0.05)
    assert weak["ci95_corrected"] == pytest.approx(list(weak_member.ci95))


def test_holm_corrects_the_strongest_member_at_alpha_over_m():
    """Rank 1 of 2 gets α/(m−i+1) = α/2, so its corrected interval is strictly
    wider than its raw one on both sides. Using α for every member — the
    mutation that keeps the weakest member's test green — is caught here."""
    strong_member, weak_member = _two_member_family()
    got = corrected_fields([strong_member, weak_member], "holm")
    strong = got[("2", "step03_analyze", "r")]
    assert strong["correction_level"] == pytest.approx(0.025)
    low, high = strong["ci95_corrected"]
    assert low < strong_member.ci95[0]
    assert high > strong_member.ci95[1]


def test_bonferroni_gives_every_member_the_same_level():
    """α/m regardless of rank — the difference from Holm, and the reason Holm is
    uniformly more powerful."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "bonferroni")
    assert {e["correction_level"] for e in got.values()} == {pytest.approx(0.025)}
    for member in (strong, weak):
        entry = got[(member.where, member.step, member.metric)]
        low, high = entry["ci95_corrected"]
        assert low < member.ci95[0] and high > member.ci95[1]


def test_fdr_bh_records_no_interval_and_no_level():
    """`reference.md`: Benjamini-Hochberg "has no interval that means anything of
    the kind — controlling a false discovery *rate* is a statement about a set,
    not a bound on any one comparison — so core reports the adjusted p-value and
    leaves `ci95_corrected` null". No p-value exists in this build, so there is
    no `p_value_corrected` either."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "fdr_bh")
    for entry in got.values():
        assert entry["ci95_corrected"] is None
        assert entry["correction_level"] is None
        assert "p_value_corrected" not in entry


def test_none_produces_no_corrected_fields_at_all():
    """`reference.md`'s table: under `none`, `ci95_corrected` is *absent*. An
    explicit null would claim a correction was attempted."""
    strong, weak = _two_member_family()
    assert corrected_fields([strong, weak], "none") == {}


def test_every_member_carries_the_family_it_was_corrected_against():
    """`family` is "reported broken out rather than as a single integer, so the
    count is auditable instead of asserted"."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "holm")
    for entry in got.values():
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}


def test_a_derived_member_is_corrected_off_its_own_pool():
    """A derived metric has no per-unit differences, so its corrected interval is
    a second rank pair off the stored draws. Nesting is structural: the same
    pool, read further into both tails."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    member = Member(
        where="1", condition_index=1, step="s", metric="r", delta=1.0,
        ci95=(0.049, 1.949), pool=pool, diffs=None,
    )
    got = corrected_fields([member], "bonferroni")[("1", "s", "r")]
    low, high = got["ci95_corrected"]
    assert low <= member.ci95[0] and high >= member.ci95[1]


def test_a_pool_too_small_for_the_level_reports_no_interval_and_says_so():
    """A family of 40 implies α/40, whose honest-draw floor is 3200 against a
    2000-draw pool. `ci95_corrected` is null while `correction_level` still
    records what was asked for, and `thin` is what the caller turns into
    `W-STATS-CORRECTED-THIN` — a silent null here would read as "no correction
    applies" rather than "the evidence cannot support this level"."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    members = [
        Member(
            where=str(c), condition_index=c, step="s", metric=k,
            delta=1.0, ci95=(0.049, 1.949), pool=pool, diffs=None,
        )
        for c in range(20)
        for k in ("r", "rmse")
    ]
    got = corrected_fields(members, "bonferroni")
    entry = got[("0", "s", "r")]
    assert entry["family_size"] == 800
    assert entry["correction_level"] == pytest.approx(0.05 / 800)
    assert entry["ci95_corrected"] is None
    assert entry["thin"] is True
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_correction.py -k "holm or bonferroni or fdr or none_produces or family_it or derived_member or pool_too_small" -v`
Expected: FAIL with `ImportError: cannot import name 'corrected_fields'`.

- [ ] **Step 3: Implement**

Append to `correction.py`, and add `from typing import Any` plus `from publishable.stats import interval_at, paired_t_over_units` to the imports:

```python
def _level_for(method: str, family_size: int, rank: int) -> float | None:
    """The α this member's corrected interval is built at.

    `reference.md`'s table: `bonferroni` is α/m for every member; `holm` is
    α/(m−i+1), which hands rank 1 the tightest level and the last rank α
    itself; `fdr_bh` implies no per-comparison level at all, so `None`.
    """
    if method == "bonferroni":
        return ALPHA / family_size
    if method == "holm":
        return ALPHA / (family_size - rank + 1)
    return None


def _corrected_bounds(member: Member, level: float) -> tuple[float, float] | None:
    """The interval at `level`, from the same evidence as the raw one.

    A recorded column re-runs `paired_t_over_units` over the stored per-unit
    differences — exact at any α. A derived metric reads a second rank pair off
    its stored draw pool. Neither redraws: a fresh resample at the corrected
    level could land *inside* the raw interval, and a corrected interval
    narrower than its raw one is precisely the number a reader cannot tell is
    wrong.
    """
    if member.diffs is not None:
        got = paired_t_over_units(member.diffs, confidence=1.0 - level)
        return None if got is None else (got.low, got.high)
    if member.pool is not None:
        return interval_at(member.pool, 1.0 - level)
    return None


def corrected_fields(
    members: Sequence[Member], method: str
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """What to merge onto each record entry, keyed by `(where, step, metric)`.

    Empty under `correction: none` — `reference.md`'s table makes
    `ci95_corrected` *absent* there, not null, because an explicit null claims a
    correction was attempted and found nothing to do.

    `thin` is not a record field: the caller reads it, emits
    `W-STATS-CORRECTED-THIN`, and drops it. It travels here because this is
    where the level and the pool size are both known.
    """
    family = family_members(members)
    if method == "none" or not family:
        return {}
    family_size, shape = family_shape(family)
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rank, member in enumerate(rank_family(family), start=1):
        level = _level_for(method, family_size, rank)
        bounds = None if level is None else _corrected_bounds(member, level)
        out[(member.where, member.step, member.metric)] = {
            "ci95_corrected": None if bounds is None else [bounds[0], bounds[1]],
            "correction": method,
            "correction_level": level,
            "family_size": family_size,
            "family": dict(shape),
            "thin": level is not None and bounds is None,
        }
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_correction.py -v && uv run ruff check . && uv run mypy`
Expected: PASS.

- [ ] **Step 5: Prove the tests discriminate**

| Mutation | Must fail |
|---|---|
| `holm` returns `ALPHA` for every rank | `test_holm_corrects_the_strongest_member_at_alpha_over_m` |
| `holm` returns `ALPHA / family_size` for every rank | `test_holm_corrects_the_weakest_member_by_nothing` |
| `family_shape` returns `comparisons` alone as the size | `test_a_pool_too_small_for_the_level_reports_no_interval_and_says_so` (level becomes α/20, which 2000 draws *can* support) |
| `_corrected_bounds` calls `interval_at(member.pool, 0.95)` | `test_a_derived_member_is_corrected_off_its_own_pool` — assert it fails; if it passes, the fixture's raw `ci95` is not the pool's own 95 % pair and the test needs the stricter `>`/`<` |
| `corrected_fields` returns fields under `none` | `test_none_produces_no_corrected_fields_at_all` |

Revert each with `git checkout -- src/publishable/correction.py`; confirm `git status --porcelain` is empty.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/correction.py tests/test_correction.py
git commit -m "Build each member's corrected interval at its own level"
```

---

### Task 6: `validate` — the family recount, the `fdr_bh` warning, the shape guard

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `correction.ALPHA` is *not* needed here. `contrasts.resolve_contrasts` and `sweep.expand` are already imported by `validate.py`.
- Produces: no new public function. Three behaviour changes plus one new identifier, `W-STATS-CORRECTION-INAPPLICABLE`.

Read `validate.py`'s `_check_sweep` family block first: it currently counts `max(len(conditions) - 1, 0) + declared` and warns whenever that exceeds zero, with a message saying multiplicity correction "is not implemented in this build". After this task the count comes from `resolve_contrasts` and the warning fires only for `correction: none`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_validate.py` (`_TWO_CONDITIONS` already exists in this file):

```python
def test_the_default_correction_does_not_warn_about_the_family(write_config):
    """`materialize.py` writes `correction: holm` into every generated config, so
    a warning on the default is a warning nearly every run gets. It fires for
    `none` — `reference.md` § Validation: "Correction declared for a family ...
    with `statistics.correction: none` (warning)"."""
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "holm"}}))
    assert "W-STATS-FAMILY" not in found


def test_an_uncorrected_family_still_warns(write_config):
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "none"}}))
    assert "W-STATS-FAMILY" in found


def test_a_sweep_with_no_baseline_and_no_contrasts_has_no_family(write_config):
    """The overcount recorded in `spec-defects.md`: a grid-only sweep declares no
    baseline, so `resolve_contrasts` returns `[]` and the run publishes no
    comparison at all. Counting `len(conditions) - 1` told the author they had a
    family of two."""
    found = codes(
        write_config(
            {
                "sweep": {"grid": {"analysis.method": ["pearson", "spearman", "kendall"]}},
                "statistics": {"correction": "none"},
            }
        )
    )
    assert "W-STATS-FAMILY" not in found


def test_fdr_bh_over_a_family_with_no_p_value_warns(write_config):
    """`reference.md`: `fdr_bh` "needs a p-value it can't always get. Declared
    over a family whose metrics carry none, it leaves every member with a `null`
    `ci95_corrected` and no `p_value_corrected` either — a correction declared
    and not applied, which is the state this section exists to prevent." No
    comparison in this build can carry one: `statistics.null_test` is refused."""
    found = codes(
        write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "fdr_bh"}})
    )
    assert "W-STATS-CORRECTION-INAPPLICABLE" in found


def test_holm_over_the_same_family_does_not_warn_about_applicability(write_config):
    """Holm's correction is interval-shaped, so it applies without a p-value.
    A warning here would read as "no correction is possible", which is false."""
    found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": "holm"}}))
    assert "W-STATS-CORRECTION-INAPPLICABLE" not in found


def test_a_non_string_correction_is_refused_without_raising(write_config):
    """`validate.py` collects findings and never raises — including on a config
    value of the wrong type. The family block reads `correction` before anything
    checks its shape, which is the class of the R11 regression in S4b."""
    for value in (5, True, ["holm"], {"method": "holm"}):
        found = codes(write_config({"sweep": _TWO_CONDITIONS, "statistics": {"correction": value}}))
        assert "E-STATS-CORRECTION-UNKNOWN" in found
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_validate.py -k "correction or family" -v`
Expected: several FAIL — the default-config test fails because the warning still fires on `holm`, and the `fdr_bh` and non-string tests fail because neither identifier exists.

- [ ] **Step 3: Check whether `E-STATS-CORRECTION-UNKNOWN` already exists**

Run: `grep -rn "E-STATS-CORRECTION\|W-STATS-CORRECTION" src/ tests/ docs/`

`reference.md` documents the enum (`none | bonferroni | holm | fdr_bh`) in § The one config file and § Validation. If an identifier for an out-of-enum value already exists, reuse it and adjust the test above to match; if not, `E-STATS-CORRECTION-UNKNOWN` is new and needs a `spec-defects.md` entry in Step 6.

- [ ] **Step 4: Implement**

Replace `_check_sweep`'s family block:

```python
    # The family is what `resolve_contrasts` will actually build — every
    # baseline comparison plus every declared contrast — not `len(conditions)`.
    # A grid-only sweep declares no baseline, so it publishes no comparison at
    # all, and telling its author they have a family of two was a false
    # positive rather than a backstop (`spec-defects.md`).
    correction = (doc.get("statistics") or {}).get("correction")
    if correction is not None and not isinstance(correction, str):
        c.error(
            "E-STATS-CORRECTION-UNKNOWN",
            "statistics.correction",
            f"is {type(correction).__name__}, not one of `none`, `bonferroni`, `holm` or "
            "`fdr_bh`",
        )
        correction = None
    comparisons = len(resolve_contrasts(doc, conditions))
    if comparisons > 0 and (correction or "holm") == "none":
        c.warn(
            "W-STATS-FAMILY",
            "statistics.correction",
            f"{comparisons} comparisons per metric form a family, and "
            "`statistics.correction` is `none` — every interval reported is uncorrected, and "
            "each records `correction: null` to say so",
        )
    if comparisons > 0 and correction == "fdr_bh":
        c.warn(
            "W-STATS-CORRECTION-INAPPLICABLE",
            "statistics.correction",
            "`fdr_bh` adjusts p-values, and no comparison in this family will carry one "
            "(`statistics.null_test` is undeclared, and a parameter-axis contrast cannot "
            "supply one) — every `ci95_corrected` will be null. Use `holm` or `bonferroni`, "
            "whose corrections are interval-shaped",
        )
```

Import `resolve_contrasts` at the top of `validate.py` if it is not already imported — check with `grep -n "resolve_contrasts" src/publishable/validate.py`.

Note the metric count is deliberately **not** in the message: `validate` runs before anything is computed, so it cannot know how many numeric metrics a step will return. The message says "per metric" for that reason, and the record's `family_size` carries the product.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: the new tests pass. **Two pre-existing tests will fail and both should be updated, not reverted:** `test_a_multi_condition_sweep_warns_about_the_uncorrected_family` (its grid-only fixture no longer forms a family — give it a `baseline` and `correction: none`) and `test_declared_contrasts_are_counted_in_the_uncorrected_family` (its message assertion changes; assert the comparison count and `correction: none`). If any *other* test fails, stop: it is telling you something this plan did not anticipate.

- [ ] **Step 6: Record the new identifiers**

Append to `docs/superpowers/spec-defects.md`, following the `E-STATS-CONTRAST-SAME-SIDES` entry's shape: which `reference.md` sentence each code implements, and why the document names no identifier for it. Cover `W-STATS-CORRECTION-INAPPLICABLE` and `E-STATS-CORRECTION-UNKNOWN` (if new), and note that `W-STATS-FAMILY` changed condition without changing identifier.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Warn about the family a run will actually publish"
```

---

### Task 7: Wire the pass into `cli.py`

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `correction.Member`, `correction.corrected_fields`; `stats.PairedResample` from Task 2.
- Produces: nothing importable. `run.yaml` gains the corrected fields on every comparison entry.

The shape change: `_comparison_step_blocks` currently returns `dict[step, dict[metric, entry]]`. It must also return the evidence, because the record cannot carry a draw pool.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli.py`, beside the existing contrast tests:

```python
def test_a_baseline_sweep_reports_a_corrected_interval(tmp_path, capsys, monkeypatch):
    """The whole slice, end to end: two comparisons over one metric is a family
    of 2 under the default `holm`, the weaker member is corrected by nothing, and
    the stronger one is corrected at α/2. `family` is broken out beside the size
    so a reviewer can check it."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman", "kendall"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for metric in step_block.values()
    ]
    assert len(entries) == 2
    for entry in entries:
        assert entry["correction"] == "holm"
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["ci95_corrected"] is not None
    levels = sorted(e["correction_level"] for e in entries)
    assert levels == [pytest.approx(0.025), pytest.approx(0.05)]
    weakest = next(e for e in entries if e["correction_level"] == pytest.approx(0.05))
    assert weakest["ci95_corrected"] == pytest.approx(weakest["ci95"])
    strongest = next(e for e in entries if e["correction_level"] == pytest.approx(0.025))
    assert strongest["ci95_corrected"][0] < strongest["ci95"][0]
    assert strongest["ci95_corrected"][1] > strongest["ci95"][1]


def test_no_draw_pool_reaches_the_record(tmp_path, capsys, monkeypatch):
    """A corrected interval is read off 2000 stored draws. Those must travel
    beside the record, never inside it: a run.yaml carrying a 2000-element array
    per metric is unreadable, and `io` never promised to serialize one."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "pool" not in text
    assert "diffs" not in text
    assert "thin" not in text
    run = yaml.safe_load(text)
    entry = _first_contrast(run, "method=spearman")
    assert not [k for k in entry if k.startswith("_")]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -k "corrected_interval or draw_pool" -v`
Expected: the first FAILs with `KeyError: 'correction'` (or `None`); the second passes already and is a regression guard for this task's own risk.

- [ ] **Step 3: Carry the evidence out of `_comparison_step_blocks`**

Change its return type to `tuple[dict[str, dict[str, Any]], list[Member]]`.

**Initialise `resampled = None` at the top of the derived branch**, beside `interval = None` and `delta = None`. It is currently assigned only inside `if n_paired >= 2`, so a derived metric over a one-unit intersection would leave the name unbound and the member-building line below would raise `NameError`. The column branch never touches it, and `is_derived and resampled` short-circuits before reading it there.

Inside the metric loop, after building `metric_block[metric_key]`, append a member:

```python
            members.append(
                Member(
                    where=where_id,
                    condition_index=comp.of,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if is_derived and resampled else None,
                    diffs=None if is_derived else tuple(diffs),
                )
            )
```

`where_id` is a new parameter: `str(comp.of)` for a `vs_baseline` block and `comp.id` for a declared contrast, passed by the two callers so the record's own addressing decides it rather than this function guessing. Initialise `members: list[Member] = []` at the top and return it beside `block`.

Then `_compute_vs_baseline` and `_compute_declared_contrasts` each return `(out, members)`, concatenating what each comparison produced.

- [ ] **Step 4: Run the pass in `command_run`**

After both `vs_baseline` and `contrasts_out` are built:

```python
            fields = corrected_fields(
                vs_baseline_members + contrast_members,
                (doc.get("statistics") or {}).get("correction") or "holm",
            )
            for (where_id, step_name, metric_key), values in fields.items():
                entry = _entry_for(vs_baseline, contrasts_out, where_id, step_name, metric_key)
                if entry is None:
                    continue
                if values.pop("thin"):
                    aggregate_c.warn(
                        "W-STATS-CORRECTED-THIN",
                        "statistics.correction",
                        f"{where_id}, step {step_name!r} metric {metric_key!r}: "
                        f"{values['family_size']} comparisons imply a corrected level of "
                        f"{values['correction_level']:.5f}, which the resample's draws cannot "
                        "support — `ci95_corrected` is null rather than too narrow",
                    )
                entry.update(values)
```

`_entry_for` is a small module-level helper resolving a `(where_id, step, metric)` key back to the mutable entry dict in either record shape:

```python
def _entry_for(
    vs_baseline: dict[int, dict[str, dict[str, dict[str, Any]]]] | None,
    contrasts: list[dict[str, Any]] | None,
    where_id: str,
    step: str,
    metric: str,
) -> dict[str, Any] | None:
    """The record entry a corrected field belongs on, in whichever shape holds it.

    `where_id` is a condition index for a `vs_baseline` block and a contrast
    `id` for a declared one — the same string `Member.where` carries, so the
    correction pass never has to know which of the two record shapes it is
    looking at.
    """
    if vs_baseline is not None and where_id.isdigit():
        block = vs_baseline.get(int(where_id), {}).get(step, {})
        if metric in block:
            return block[metric]
    for entry in contrasts or []:
        if entry.get("id") == where_id:
            step_block = entry.get(step)
            if isinstance(step_block, dict) and metric in step_block:
                found = step_block[metric]
                return found if isinstance(found, dict) else None
    return None
```

Note the `where_id.isdigit()` branch: a contrast whose `id` is a bare number would otherwise be looked up as a condition index. `validate` permits such an `id`, so the `vs_baseline` lookup returning `None` correctly falls through to the contrast scan.

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

Expected: all pass. Pre-existing contrast tests assert `correction is None` in places — those assertions are now **wrong** and must become `entry["correction"] == "holm"`. Grep for them: `grep -n '"correction"' tests/test_cli.py`.

- [ ] **Step 6: Prove the test discriminates**

| Mutation | Must fail |
|---|---|
| Pass only `vs_baseline_members` to `corrected_fields` | Task 9's declared-contrast test (note it here; this task's fixture has no declared contrast) |
| Skip the `values.pop("thin")` and merge `thin` into the entry | `test_no_draw_pool_reaches_the_record` |
| Use `"holm"` unconditionally instead of reading the config | Task 9's `fdr_bh` end-to-end test |

- [ ] **Step 7: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Correct every comparison against the family it belongs to"
```

---

### Task 8: `confounded` and `differs_on`

**Files:**
- Modify: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `sweep.Condition.values` — a read-only mapping of axis name to value, built in grid declaration order.
- Produces: two optional keys on a comparison's metric entry.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_contrast_crossing_two_axes_is_marked_confounded(tmp_path, capsys, monkeypatch):
    """`reference.md`: "A contrast crossing two axes at once ... differs in two
    places, so its delta mixes the two effects and no amount of correct pairing
    separates them — that's the factorial main-effects problem, and it's why
    such a contrast is marked rather than merely reported." `differs_on` names
    the axes, because the boolean alone says a contrast is confounded without
    saying by what."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson", "analysis.min_samples": 10},
            "grid": {"analysis.method": ["spearman"], "analysis.min_samples": [20]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for metric in step_block.values()
    ]
    crossed = [e for e in entries if e.get("confounded")]
    assert crossed, "a condition differing on both axes must be marked"
    assert crossed[0]["differs_on"] == ["analysis.method", "analysis.min_samples"]


def test_a_one_axis_contrast_carries_neither_marker(tmp_path, capsys, monkeypatch):
    """Absent, not `false`/`[]` — the house rule the `vs_baseline` block itself
    follows. A `confounded: false` on every ordinary contrast is noise a reader
    has to learn to skip."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert "confounded" not in entry
    assert "differs_on" not in entry
```

Confirm `analysis.min_samples` is a real parameter of the `generic` template before relying on it: `grep -n "min_samples" src/publishable/templates/builtin/generic.py`. If it is not, use two parameters that are — the test needs a two-axis grid, not these particular axes.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -k "confounded or one_axis" -v`
Expected: the first FAILs on the empty `crossed` list; the second passes and guards against over-marking.

- [ ] **Step 3: Implement**

Add to `cli.py`:

```python
def _differing_axes(
    of: "Condition", against: "Condition"
) -> list[str]:
    """The axes two conditions disagree on, in the order the sweep declares them.

    `Condition.values` is built by `sweep.expand` from `grid.items()`, so
    iterating it gives declaration order — which is what makes `differs_on`
    stable across runs rather than set-ordered.
    """
    return [k for k, v in of.values.items() if against.values.get(k) != v]
```

Give `_comparison_step_blocks` a new keyword-only parameter `conditions_by_index: dict[int, "Condition"]`, and have both `_compute_vs_baseline` and `_compute_declared_contrasts` pass `{c.index: c for c in conditions}` — each already receives `conditions`. Compute once per comparison, before the step loop:

```python
    differs_on = _differing_axes(
        conditions_by_index[comp.of], conditions_by_index[comp.against]
    )
    confounded = len(differs_on) > 1
```

then, after building each `metric_block[metric_key]`:

```python
            if confounded:
                # Marked, not merely reported: a delta mixing two axes is the
                # factorial main-effects problem, which core refuses to
                # separate. `differs_on` names them so a reader knows which.
                metric_block[metric_key]["confounded"] = True
                metric_block[metric_key]["differs_on"] = list(differs_on)
```

`paired` stays hard `true`: group axes and `allocation: between` are both refused, so the `paired: false` and `unpaired_*` method `reference.md` shows for a crossed *group* axis are unreachable here.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "Mark a contrast that crosses two axes, and name them"
```

---

### Task 9: The three carries

**Files:**
- Modify: `src/publishable/validate.py`, `src/publishable/cli.py`, `src/publishable/stats.py`
- Test: `tests/test_validate.py`, `tests/test_cli.py`, `tests/test_stats.py`

**Interfaces:**
- Consumes: `runner.attrition`'s `ineligible` count (already computed and already reaching `command_run`).
- Produces: `W-DATA-INELIGIBLE`; `statistics.contrasts` refused in `_check_shape`; `percentile_over_units` returning `None` below the honest-draw floor.

Three independent carries, grouped because each is a few lines and none deserves its own review gate.

- [ ] **Step 1: Write the failing tests**

For `max_ineligible_fraction` — check the identifier first with `grep -rn "max_ineligible_fraction\|W-DATA-INELIGIBLE" src/ docs/reference.md`; `reference.md` § The one config file says "`run` warns when a condition can be built for fewer units", so this is a run-time warning, not a validate one:

```python
def test_a_condition_skipping_too_many_units_warns(tmp_path, capsys, monkeypatch):
    """`limits.max_ineligible_fraction` was written into every generated config
    and read by nothing — the last live silent no-op of the class S4a's refusals
    closed. `io.skip` is what declares a unit ineligible."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SKIP_MOST_STEP)
    doc = run_a_project(
        tmp_path, capsys=capsys, units=10, limits={"max_ineligible_fraction": 0.2}
    )
    assert "W-DATA-INELIGIBLE" in doc["stdout"]
```

`_SKIP_MOST_STEP` is a new fixture. `io.skip(unit_key, reason)` is defined in `artifacts.py` (there is no `io.py` — the object a step receives is built there):

```python
_SKIP_MOST_STEP = '''\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # 8 of 10 units declared ineligible, which is `io.skip`'s meaning: not a
        # failure, and deliberately not attrition. The other two record a value so
        # the step still produces a numeric column.
        for i, unit in enumerate(io.units):
            if i < 8:
                io.skip(unit.key, "outside the eligibility window")
            else:
                io.record(unit.key, {{"pred": float(i)}})
        return {{"n_units": len(io.units)}}
'''
```

The doubled braces are required: `run_a_project` formats this template with `.format(pkg=...)`, the same as every other step fixture in the file.

For the shape gap:

```python
def test_a_scalar_contrasts_block_is_refused_once_in_the_shape_pass(write_config):
    """`_check_shape` runs first and `validate_config` early-returns on it, so a
    nested key refused there is refused for every later reader at once. Its own
    comment says an unguarded container means "the crash just moves one level
    down, into whichever `_check_*` reads it next" — which is what R11 was."""
    found = codes(write_config({"statistics": {"contrasts": 5}}))
    assert "E-CONFIG-SHAPE" in found
```

Confirm the code name with `grep -n "E-CONFIG-SHAPE" src/publishable/validate.py` and match whatever `_check_shape` already emits.

For the floor:

```python
def test_percentile_over_units_refuses_a_pool_below_the_honest_floor():
    """The gap `spec-defects.md` recorded: `percentile_of_derived` got a survivor
    floor in S4a and its sibling did not, so this one returns a zero-width
    interval at two draws. Unreachable today (`statistics.resample` is refused),
    which is exactly why it must be closed before the slice that reaches it."""
    values = [float(i) for i in range(60)]
    assert percentile_over_units(values, seed=7, draws=10) is None
    assert percentile_over_units(values, seed=7, draws=2000) is not None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_validate.py -k shape_pass tests/test_stats.py -k honest_floor tests/test_cli.py -k ineligible -v`
Expected: all three FAIL.

- [ ] **Step 3: Implement the floor**

In `percentile_over_units`, after the `len(values) < 2` guard:

```python
    if draws < min_honest_draws(confidence):
        return None
```

- [ ] **Step 4: Implement the shape refusal**

In `_check_shape`, beside the existing `sweep` nested block, add:

```python
    # `statistics.contrasts` is read by two `_check_*` functions and by
    # `contrasts.resolve_contrasts`, so it belongs here rather than being guarded
    # three times. This block's own comment above says why: a container of the
    # wrong shape means "the crash just moves one level down, into whichever
    # `_check_*` reads it next", which is exactly what a scalar here did — the
    # family count in `_check_sweep` reached it before `_check_contrasts` refused
    # its shape, and `len()` on an int raised out of `validate`.
    statistics = doc.get("statistics")
    if isinstance(statistics, dict):
        contrasts = statistics.get("contrasts")
        if contrasts is not None and not isinstance(contrasts, list):
            _bad("statistics.contrasts", contrasts, "list")
```

Then consider deleting the now-upstream `isinstance(entries, list)` branch in `_check_contrasts`. **Keep it.** `_check_contrasts` is reachable directly from tests, and `_check_shape`'s early return protects `validate_config`'s path only — removing a guard because another one exists upstream is how R11 happened in the first place.

- [ ] **Step 5: Implement the ineligible warning**

In `command_run`'s aggregate loop, `counts = attrition(...)` is already computed per condition per step and returns `{"resolved", "completed", "ineligible", "failed"}`. Immediately after that call:

```python
                    max_ineligible = (doc.get("limits") or {}).get("max_ineligible_fraction")
                    if (
                        isinstance(max_ineligible, (int, float))
                        and not isinstance(max_ineligible, bool)
                        and counts["resolved"]
                        and counts["ineligible"] / counts["resolved"] > max_ineligible
                    ):
                        aggregate_c.warn(
                            "W-DATA-INELIGIBLE",
                            "limits.max_ineligible_fraction",
                            f"condition {cond.index}, step {step_name!r}: "
                            f"{counts['ineligible']} of {counts['resolved']} units are "
                            f"ineligible, above limits.max_ineligible_fraction "
                            f"({max_ineligible})",
                        )
```

The `isinstance` guard is not decoration: `limits` is user-written, and `command_run` must not raise on a string threshold. `bool` is excluded because `True` would compare as `1` and silently never fire.

Ineligible is deliberately *not* attrition — `reference.md` § The one config file: units a step declared ineligible via `io.skip` "are not attrition". This warning is about a condition that could be built for fewer units than the design assumed, which is why it is per condition and per step rather than run-level like `max_failed_fraction`.

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`
Expected: all pass.

- [ ] **Step 7: Record any new identifier**

If `W-DATA-INELIGIBLE` is not already named in `reference.md`, add a `spec-defects.md` entry for it in the established shape.

- [ ] **Step 8: Commit**

```bash
git add src/publishable/validate.py src/publishable/cli.py src/publishable/stats.py tests/
git commit -m "Close the three carries S4b left for this slice"
```

---

### Task 10: The acceptance test

**Files:**
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above.
- Produces: nothing importable. This task should need **zero** `src/` changes; if it needs one, an earlier task left a gap and that is the finding.

- [ ] **Step 1: Write the end-to-end tests**

```python
def test_a_declared_contrast_joins_the_correction_family(tmp_path, capsys, monkeypatch):
    """`reference.md`: "Declared contrasts join the correction family alongside
    baseline comparisons, because a reader shown both is exposed to both." One
    baseline comparison plus one declared contrast is a family of 2, and both
    entries must say so — correcting only `vs_baseline` under-corrects by
    exactly the contrasts the config asked for."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        unit_attributes=["cohort"],
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
        statistics={
            "correction": "holm",
            "contrasts": [
                {
                    "id": "stratum_a",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": {"cohort": "a"},
                }
            ],
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    baseline_entry = _first_contrast(run, "method=spearman")
    declared_entry = next(
        metric
        for contrast in run["results"]["contrasts"]
        for step_block in contrast.values()
        if isinstance(step_block, dict)
        for metric in step_block.values()
    )
    for entry in (baseline_entry, declared_entry):
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}
        assert entry["correction"] == "holm"
    assert sorted(
        [baseline_entry["correction_level"], declared_entry["correction_level"]]
    ) == [pytest.approx(0.025), pytest.approx(0.05)]


def test_fdr_bh_records_the_correction_it_could_not_apply(tmp_path, capsys, monkeypatch):
    """The documented state: the correction is named in the record, every
    `ci95_corrected` is null, and the warning says why. Nothing is silent, and
    nothing claims an adjustment that did not happen."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "fdr_bh"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry["correction"] == "fdr_bh"
    assert entry["ci95_corrected"] is None
    assert entry["correction_level"] is None
    assert "p_value_corrected" not in entry
    assert "W-STATS-CORRECTION-INAPPLICABLE" in doc["stdout"]


def test_an_uncorrected_run_carries_no_corrected_fields(tmp_path, capsys, monkeypatch):
    """Under `correction: none` the fields are *absent*, per `reference.md`'s
    table — and `W-STATS-FAMILY` fires, which is the pairing that makes an
    uncorrected family honest rather than hidden."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _METHOD_VARYING_STEP)
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        statistics={"correction": "none"},
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.method": ["spearman"]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert "ci95_corrected" not in entry
    assert "correction_level" not in entry
    assert "family_size" not in entry
    assert entry["correction"] is None  # the S4b field, still there and still null
    assert "W-STATS-FAMILY" in doc["stdout"]
```

Note the last assertion: S4b writes `correction: None` onto every entry, and `correction: none` must leave that null rather than the string `"none"`. If `corrected_fields` returning `{}` leaves it as S4b's `None`, this passes unchanged.

Then the one identifier no test above produces — the Global Constraints require every `W-` code to have one:

```python
def test_a_family_too_wide_for_the_draws_reports_no_corrected_interval(
    tmp_path, capsys, monkeypatch
):
    """`W-STATS-CORRECTED-THIN`, end to end. The arithmetic that makes it fire:
    `min_honest_draws(1 - level)` is `ceil(2 / (level / 2))`, so a corrected level
    below 0.002 needs more than 2000 draws — which means a family above 25. Six
    conditions give 5 comparisons, and an `aggregate` returning 6 derived metrics
    makes the family 30, so the level is 0.05/30 = 0.00167 and the floor is 2398
    against the 2000-draw default.

    The disclosure is the point: `correction_level` still records the level that
    was asked for, so a reader can see the correction was scoped and could not be
    built, rather than seeing a null that reads as "no correction applies"."""
    import publishable.generators.experiment as experiment_gen
    from publishable.templates.builtin.generic import GenericTemplate

    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _AGGREGATE_STEP)
    monkeypatch.setattr(
        GenericTemplate,
        "aggregate",
        lambda self, units, cfg: {
            f"score{k}": (k + 1) * sum(units.pred) / len(units) for k in range(6)
        },
    )
    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        units=40,
        sweep={
            "baseline": {"analysis.method": "pearson"},
            "grid": {"analysis.min_samples": [20, 30, 40, 50, 60]},
        },
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entries = [
        metric
        for condition in run["results"]["conditions"]
        for step_block in condition.get("vs_baseline", {}).values()
        for name, metric in step_block.items()
        if name.startswith("score")
    ]
    assert entries, "the derived metrics must reach vs_baseline"
    assert {e["family_size"] for e in entries} == {30}
    assert all(e["ci95_corrected"] is None for e in entries)
    assert all(e["correction_level"] == pytest.approx(0.05 / 30) for e in entries)
    assert "W-STATS-CORRECTED-THIN" in doc["stdout"]
```

Two things to verify rather than assume before running it: that `analysis.min_samples` is a real `generic` parameter taking five more values (`grep -n "min_samples" src/publishable/templates/builtin/generic.py`), and that the `pred` column also lands in the family — if it does, the family is 5 × 7 = 35 and the expected `family_size` and level change accordingly. Compute the number from the run rather than forcing the fixture to match 30.

- [ ] **Step 2: Run them**

Run: `uv run pytest tests/test_cli.py -k "joins_the_correction or fdr_bh_records or uncorrected_run or too_wide_for_the_draws" -v`
Expected: PASS with no `src/` change. If one fails, fix the *source* gap it found rather than the assertion, and say which earlier task should have covered it.

- [ ] **Step 3: Verify the worked example's own arithmetic**

Confirm the numbers this slice is specified against, and record the output in the report:

- 3 conditions → 2 comparisons; 1 metric → `family_size: 2`, `family: {comparisons: 2, metrics: 1}`
- the weaker member's `correction_level` is 0.05 and its `ci95_corrected` equals its `ci95`
- the stronger member's is 0.025 and its corrected interval is strictly wider

- [ ] **Step 4: Run the whole gate**

Run: `uv run pytest -q && uv run ruff check . && uv run mypy`

- [ ] **Step 5: Commit**

```bash
git add tests/test_cli.py
git commit -m "Correct a family end to end"
```

---

## After the last task

- [ ] Re-read `docs/superpowers/specs/2026-08-10-correction-family-design.md` § Scope and confirm every In row landed, and that no Out row (`report_by`, the `aggregate` table's contents, per-stratum `min_reported_n`) was touched.
- [ ] Run the **whole-branch review** over `merge-base(main, HEAD)..HEAD` on the most capable model available. It has found a Critical on every slice so far, including both of S4b's, and S4b's own fix round introduced a regression that only a fourth pass caught. Do not merge without it.
- [ ] Record in `spec-defects.md` anything the slice could not do, and update the two S4c entries (`confounded`, `max_ineligible_fraction`) to closed.

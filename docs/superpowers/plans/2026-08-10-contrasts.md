# Contrasts (S4b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A run reports the difference between two conditions, with an interval built from the pairing rather than from the two sides' intervals.

**Architecture:** A pure `contrasts.py` resolves `vs_baseline` and any declared `statistics.contrasts` into a list of comparisons. For each, `stats.py` intersects the two sides' completed units into a paired table — that count is `n_paired` — and builds the interval one of two ways: Student's *t* on the per-unit differences for a column metric, or a percentile interval for a derived one, drawing **once** and applying the draw to both sides. `cohens_d` is *d*z for a column metric and `null` for a derived one. Correction stays out; every contrast records `correction: null` and `W-STATS-FAMILY` keeps warning.

**Tech Stack:** Python 3.11+, `uv`, pytest, ruff, mypy, numpy, scipy.

## Global Constraints

- Python >= 3.11.
- Runtime dependencies are exactly `pyyaml`, `numpy`, `scipy`, `pyarrow`. Adding one is out of scope.
- ruff: line-length 100, select `["E","F","I","UP","B"]`. mypy: strict over `src/`.
- Commands: `uv run pytest`, `uv run ruff check .`, `uv run mypy`. (`ruff format` reformats ~30 pre-existing files — do not run it; `ruff check` is the gate.)
- `×`, not `x`, for multiplication — including inside fenced blocks and commit messages.
- `stats.py`, `sweep.py`, and the new `contrasts.py` are **pure**: no filesystem, and no runtime import of `config`, `artifacts`, `runner`, or `cli`.
- `artifacts.py` is the only module that writes inside a run directory.
- `validate.py` **collects** findings and never raises to report one.
- Every `E-`/`W-` identifier must have a test that produces it; for a validate-time code that means through `validate_config`.
- The four documents in `docs/` are normative and lead. Where code cannot follow them, the document changes first and the gap is recorded in `docs/superpowers/spec-defects.md`.
- Unimplemented must mean **refused**, never silently ignored.
- **A run with no baseline and no declared contrasts must be unchanged** — no `vs_baseline` block at all. A comparison origin appearing where nothing asked for one is the regression that has landed in three consecutive slices.

---

## File Structure

| File | Responsibility in this slice |
|---|---|
| `src/publishable/contrasts.py` *(new)* | **Pure.** `Comparison`; resolving `vs_baseline` and declared entries; `within` matching over the roster |
| `src/publishable/stats.py` | The paired table and `n_paired`; `paired_t_over_units`; `paired_percentile_of_derived`; `cohens_dz` |
| `src/publishable/validate.py` | Retire `E-STATS-CONTRASTS-UNSUPPORTED`; refuse a contrast naming a contrast; check `of`/`against` resolve; the `min_reported_n` warning |
| `src/publishable/cli.py` · `run_record.py` | The `vs_baseline` block in the record |

---

### Task 1: `Comparison` and contrast resolution

**Files:**
- Create: `src/publishable/contrasts.py`
- Test: `tests/test_contrasts.py`

**Interfaces:**
- Consumes: `sweep.Condition` — frozen, with `index: int`, `label: str | None`, `values` (read-only mapping), `is_baseline: bool`.
- Produces:
  - `@dataclass(frozen=True) class Comparison: id: str; of: int; against: int; within: dict[str, str] | None`
  - `resolve_contrasts(config: dict[str, Any], conditions: list["Condition"]) -> list[Comparison]`

`of` and `against` are **condition indices**, resolved from the labels the config names. `docs/reference.md` § Contrasts: `of`/`against` name conditions by label — the selector property S3a's label grammar exists to provide, so a person can write one down without seeing the directory.

**Two sources, one list.** Every non-baseline condition yields a `vs_baseline` comparison against the baseline; each `statistics.contrasts` entry yields one more. A run with no baseline and no declared entries yields `[]`.

- [ ] **Step 1: Write the failing tests**

```python
def _cond(i, label, baseline=False):
    return Condition(index=i, label=label, values={}, is_baseline=baseline)


def test_no_baseline_and_no_declared_contrasts_yields_nothing():
    conds = [_cond(0, "method=pearson"), _cond(1, "method=spearman")]
    assert resolve_contrasts({}, conds) == []


def test_each_non_baseline_condition_compares_against_the_baseline():
    conds = [_cond(0, "baseline", baseline=True),
             _cond(1, "method=spearman"), _cond(2, "method=kendall")]
    got = resolve_contrasts({}, conds)
    assert [(c.of, c.against) for c in got] == [(1, 0), (2, 0)]
    assert [c.id for c in got] == ["method=spearman", "method=kendall"]


def test_a_declared_contrast_resolves_labels_to_indices():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {"statistics": {"contrasts": [
        {"id": "sensitivity", "of": "shift=abnormal", "against": "shift=normal"}]}}
    got = resolve_contrasts(cfg, conds)
    assert [(c.id, c.of, c.against, c.within) for c in got] == [("sensitivity", 1, 0, None)]


def test_a_declared_contrast_carries_its_within_stratum():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {"statistics": {"contrasts": [
        {"id": "sens_f", "of": "shift=abnormal", "against": "shift=normal",
         "within": {"sex": "f"}}]}}
    assert resolve_contrasts(cfg, conds)[0].within == {"sex": "f"}


def test_declared_contrasts_come_after_the_baseline_ones():
    """Order is the record's order, and vs_baseline is the documented default."""
    conds = [_cond(0, "baseline", baseline=True), _cond(1, "method=spearman")]
    cfg = {"statistics": {"contrasts": [
        {"id": "extra", "of": "method=spearman", "against": "baseline"}]}}
    assert [c.id for c in resolve_contrasts(cfg, conds)] == ["method=spearman", "extra"]
```

Build `Condition` however `tests/test_sweep.py` already does — **read it first** and reuse that idiom; `_cond` above stands for whatever it uses.

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_contrasts.py -v`
Expected: FAIL — the module does not exist.

- [ ] **Step 3: Implement**

```python
"""Which comparisons a config asks for. Pure: config and conditions in, list out.

`docs/reference.md` § Contrasts: `of` and `against` name conditions **by label**,
which is the selector property the condition-label grammar exists to provide — a
label has to be something a person can write down without seeing the directory.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from publishable.sweep import Condition


@dataclass(frozen=True)
class Comparison:
    id: str
    of: int
    against: int
    within: dict[str, str] | None = None


def resolve_contrasts(
    config: dict[str, Any], conditions: list["Condition"]
) -> list[Comparison]:
    """Every non-baseline condition against the baseline, then declared entries.

    A run with no baseline and no `statistics.contrasts` compares nothing, and
    the record carries no `vs_baseline` block at all — an empty one would claim
    a comparison was made and found nothing.
    """
    by_label = {c.label: c.index for c in conditions if c.label is not None}
    out: list[Comparison] = []
    baseline = next((c for c in conditions if c.is_baseline), None)
    if baseline is not None:
        for c in conditions:
            if c.index != baseline.index and c.label is not None:
                out.append(Comparison(id=c.label, of=c.index, against=baseline.index))
    for entry in ((config.get("statistics") or {}).get("contrasts") or []):
        out.append(
            Comparison(
                id=str(entry.get("id")),
                of=by_label[entry["of"]],
                against=by_label[entry["against"]],
                within=entry.get("within"),
            )
        )
    return out
```

`by_label[...]` raising a `KeyError` on an unresolvable label is acceptable **only because Task 2 refuses that at validate time**; note it in a comment so the next reader knows the guard exists elsewhere.

- [ ] **Step 4: Run to verify they pass, then commit**

```bash
uv run pytest tests/test_contrasts.py -v && uv run ruff check . && uv run mypy
git add src/publishable/contrasts.py tests/test_contrasts.py
git commit -m "Resolve which comparisons a config asks for"
```

---

### Task 2: `within` matching over the roster

**Files:**
- Modify: `src/publishable/contrasts.py`
- Test: `tests/test_contrasts.py`

**Interfaces:**
- Consumes: `units.Unit` — frozen, with `key`, `paths`, `attributes`. `UnitList` supports iteration, `len`, integer indexing, and `.train`.
- Produces: `units_matching(roster: "UnitList", within: dict[str, str] | None) -> set[str] | None`

`None` in, `None` out — meaning "no restriction", which is different from "no units matched". Downstream code must be able to tell those apart, because an empty stratum is a real condition worth reporting and an unrestricted contrast is not.

**`within` matches unit *attributes*, not recorded columns.** `docs/reference.md` § Contrasts: it "names unit attributes and their levels — the same attributes `report_by` resolves — and the contrast is computed over units matching **all** of them."

- [ ] **Step 1: Write the failing tests**

```python
def _roster(*specs):
    return UnitList([Unit(key=k, paths=(), attributes=a) for k, a in specs])


def test_no_within_means_no_restriction():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}))
    assert units_matching(r, None) is None


def test_a_single_level_selects_matching_units():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}), ("u3", {"sex": "f"}))
    assert units_matching(r, {"sex": "f"}) == {"u1", "u3"}


def test_multiple_levels_are_conjunctive():
    r = _roster(("u1", {"sex": "f", "site": "a"}), ("u2", {"sex": "f", "site": "b"}))
    assert units_matching(r, {"sex": "f", "site": "a"}) == {"u1"}


def test_an_empty_stratum_is_an_empty_set_not_none():
    """Empty means nobody matched; None means nobody asked. Downstream reports
    those differently, so they must not collapse."""
    r = _roster(("u1", {"sex": "f"}))
    assert units_matching(r, {"sex": "m"}) == set()


def test_values_compare_as_strings():
    """A config's YAML gives `1` as an int while an attribute read from a CSV is
    `"1"`; comparing them raw would silently match nothing."""
    r = _roster(("u1", {"cohort": "1"}))
    assert units_matching(r, {"cohort": 1}) == {"u1"}
```

- [ ] **Step 2: Run to verify they fail, then implement**

```python
def units_matching(roster: "UnitList", within: dict[str, str] | None) -> set[str] | None:
    """Unit keys matching every level in `within`, or `None` when unrestricted.

    `None` and `set()` are different answers: nobody asked, versus nobody
    matched. An empty stratum is a real finding — `limits.min_reported_n` exists
    to warn about small ones — so collapsing the two would hide it.

    Values compare as strings: a config's YAML gives `1` as an int while the same
    attribute read from a table is `"1"`, and comparing them raw matches nothing.
    """
    if within is None:
        return None
    return {
        unit.key
        for unit in roster
        if all(str(unit.attributes.get(k)) == str(v) for k, v in within.items())
    }
```

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/contrasts.py tests/test_contrasts.py
git commit -m "Select the units a within stratum names"
```

---

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

### Task 6: The refusals and `min_reported_n`

**Files:**
- Modify: `src/publishable/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `resolve_contrasts`; the resolved conditions from `sweep.expand`; `validate.py`'s `Collector` convention.
- Produces: retires `E-STATS-CONTRASTS-UNSUPPORTED`; adds `E-STATS-CONTRAST-UNKNOWN` (an `of`/`against` naming no condition) and `E-STATS-CONTRAST-NESTED` (naming another contrast's `id`); the `min_reported_n` warning is Task 7's, at the point `n_paired` is known.

**Contrasts compare conditions and do not nest.** `reference.md` and `design-principles.md` both say it: anything comparing two contrasts — a dose-response ordering, a difference-in-differences, a nested mean over cells — is an **interaction** and stays a `summary`-step `Estimate`. So a contrast naming another contrast's `id` is refused, and the message should point at that route rather than merely saying no.

**Before minting either identifier, grep `docs/reference.md`.** Several codes this project "added" already existed in its registry.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_declared_contrast_is_no_longer_refused(write_config):
    found = codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "s", "of": "method=spearman", "against": "baseline"}]}}))
    assert "E-STATS-CONTRASTS-UNSUPPORTED" not in found


def test_an_unresolvable_side_is_refused(write_config):
    assert "E-STATS-CONTRAST-UNKNOWN" in codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "s", "of": "method=nope", "against": "baseline"}]}}))


def test_a_contrast_naming_another_contrast_is_refused(write_config):
    """Contrasts do not nest — that is an interaction, and it belongs in a
    summary-step Estimate."""
    found = codes(write_config({
        "sweep": {"baseline": {"analysis.method": "pearson"},
                  "grid": {"analysis.method": ["spearman"]}},
        "statistics": {"contrasts": [
            {"id": "a", "of": "method=spearman", "against": "baseline"},
            {"id": "b", "of": "a", "against": "baseline"}]}}))
    assert "E-STATS-CONTRAST-NESTED" in found


def test_no_declared_contrasts_still_validates_clean(write_config):
    found = codes(write_config({"statistics": {"contrasts": []}}))
    assert not [c for c in found if c.startswith("E-STATS-CONTRAST")]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_validate.py -k contrast -v`
Expected: the first FAILS because the block is still refused wholesale; the others FAIL because the codes do not exist.

- [ ] **Step 3: Implement**

Remove `E-STATS-CONTRASTS-UNSUPPORTED` from the refusal list, then check each declared entry: `of` and `against` must resolve to a condition label, **unless** the name matches another entry's `id`, which is the nested case and gets its own code. Grep the whole tree for `E-STATS-CONTRASTS-UNSUPPORTED` afterwards — `src/`, `tests/`, and the four documents — and confirm it is gone.

Order matters: check nesting **before** unknown, so `of: "a"` naming a contrast reports the nested code rather than the less specific unknown-label one.

- [ ] **Step 4: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/validate.py tests/test_validate.py
git commit -m "Accept declared contrasts, and refuse the ones that nest"
```

---

### Task 7: Contrasts reach the record

**Files:**
- Modify: `src/publishable/cli.py`, `src/publishable/run_record.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: everything above; `collapse_repeats(results, step_name, condition_index, fold_members)`; `summarize_step`'s output shape; the condition metadata `cli.py` already builds with `label`, `is_baseline`, and `values`.
- Produces: a `vs_baseline` block in the record.

`docs/reference.md` § The two files shows the entry shape:

```yaml
vs_baseline:
  step03_analyze:
    r: {delta: 0.026, basis: units, paired: true,
        method: paired_percentile_over_units,
        ci95: [-0.007, 0.059],
        cohens_d: null}
```

**In this slice each entry also carries `n_paired`, and `correction: null`.** The correction, `ci95_corrected`, `correction_level`, `family_size` and `family` keys belong to S4c — do not add them, and do not remove `W-STATS-FAMILY`.

**Which construction applies is decided by the metric's origin**, not by a flag: a recorded column metric takes `paired_t_over_units` over the per-unit differences; a derived metric takes `paired_percentile_of_derived`. `cohens_d` is `cohens_dz(diffs)` for the first and `None` for the second.

**`min_reported_n` becomes real here.** `materialize.py` writes it into every generated config and nothing reads it — a live silent no-op. `reference.md` § Contrasts: it "applies to a `within` contrast's `n_paired`". Warn when a contrast's `n_paired` falls below `limits.min_reported_n`. Grep for an existing `W-` identifier before minting one.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_baseline_sweep_reports_a_delta(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    entry = _first_contrast(run, "method=spearman")
    assert entry["paired"] is True
    assert entry["n_paired"] > 0
    assert entry["method"] in ("paired_t_over_units", "paired_percentile_over_units")
    assert entry["correction"] is None          # S4c's job, disclosed not applied


def test_a_run_with_no_baseline_has_no_vs_baseline_block(tmp_path, capsys):
    """Absent, not empty. An empty block would claim a comparison was made and
    found nothing."""
    doc = run_a_project(tmp_path, capsys=capsys)
    text = (doc["run_dir"] / "run.yaml").read_text()
    assert "vs_baseline" not in text


def test_a_thin_pairing_warns(tmp_path, capsys):
    doc = run_a_project(tmp_path, capsys=capsys, units=3, limits={"min_reported_n": 10},
                        sweep={"baseline": {"analysis.method": "pearson"},
                               "grid": {"analysis.method": ["spearman"]}})
    assert "min_reported_n" in doc["stdout"] or "N_PAIRED" in doc["stdout"]
```

`run_a_project` is the end-to-end driver in `tests/test_cli.py`; **reuse it**, extending it additively with defaulted keywords if it cannot yet vary units or limits, and say what you added. `_first_contrast` is a small local helper — write it if the file has none.

- [ ] **Step 2: Run to verify they fail, then implement**

Read how `aggregated` is assembled in `cli.py` and follow that shape for `vs_baseline`. **Report where you attached it** so the reviewer can check it against `reference.md` § The two files rather than guess.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/cli.py src/publishable/run_record.py tests/test_cli.py
git commit -m "Report a contrast beside the conditions it compares"
```

---

### Task 8: The acceptance test

**Files:**
- Test: `tests/test_cli.py`, `tests/test_stats.py`
- Modify: whatever the tests show is still unwired.

**Interfaces:**
- Consumes: everything above.
- Produces: no new source interfaces.

Every earlier task is testable in isolation, and this project has twice shipped a subsystem green in unit tests and unreachable from `main(["run", ...])`. **Report every `src/` change you need here — each one is a piece an earlier task left inert.**

**The worked example is the anchor, but assert properties rather than reverse-engineering a fixture to hit exact values.** `CLAUDE.md` pins delta 0.026 with `ci95` [−0.007, 0.059], kendall's −0.169 with [−0.213, −0.125], and records that the delta's half-width "does not go below ≈0.033 for a linear-versus-rank contrast at this *n*". Building a 228-unit fixture that reproduces those exactly is not a test, it is curve-fitting. Assert instead:

- [ ] **Step 1: Write the acceptance tests**

```python
def test_a_paired_delta_is_narrower_than_the_conditions_it_compares(tmp_path, capsys):
    """The contrast that `allocation: within` buys, end to end: per-condition
    intervals are wide and the delta's is narrow, over the same units."""
    doc = run_a_project(tmp_path, capsys=capsys, units=120, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    delta = _first_contrast(run, "method=spearman")
    width = delta["ci95"][1] - delta["ci95"][0]
    per_condition = _first_metric_width(run, condition_index=1)
    assert width < per_condition


def test_the_delta_half_width_is_not_implausibly_narrow(tmp_path, capsys):
    """CLAUDE.md records ≈0.033 as unreachable for a linear-versus-rank contrast
    at n≈228; a fixture producing far less has lost the resampling."""
    doc = run_a_project(tmp_path, capsys=capsys, units=120, sweep={
        "baseline": {"analysis.method": "pearson"},
        "grid": {"analysis.method": ["spearman"]}})
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    lo, hi = _first_contrast(run, "method=spearman")["ci95"]
    assert hi > lo                                  # a real interval, not a point
```

- [ ] **Step 2: Verify by hand**

Scaffold a project **outside the repository**, give it a baseline and one grid condition, run it, and paste `run.yaml`'s `vs_baseline` block into your report alongside the two conditions' own intervals. A test can share a bug with the code it tests; a record you read cannot. Confirm `git status` is clean of stray scaffold directories before committing — an earlier slice leaked one from a wrong working directory.

- [ ] **Step 3: Run the full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add tests/ src/
git commit -m "Compare two conditions end to end"
```

---

## Self-Review

**Spec coverage.** Comparison resolution → Task 1. `within` → Task 2. The intersection and `n_paired` → Task 3. `paired_t_over_units` and `cohens_dz` → Task 4. `paired_percentile_of_derived` → Task 5. The refusals and retiring `E-STATS-CONTRASTS-UNSUPPORTED` → Task 6. The record, plus `min_reported_n` → Task 7. Acceptance → Task 8. No spec section is unassigned. The two unreachable constructions are documented as out of scope rather than built.

**Placeholders.** Every code step carries code and every test step carries tests. Four tasks name an existing helper (`write_config`, `codes`, `run_a_project`, and `tests/test_sweep.py`'s `Condition` idiom) rather than inventing one, each with an instruction to read and match — deliberate, since a second idiom is the defect.

**Type consistency.** `Comparison(id, of, against, within)` from Task 1 is consumed unchanged in Tasks 6 and 7. `units_matching(roster, within) -> set[str] | None` feeds `paired_keys(of, against, allowed)` in Task 3, whose `allowed` is exactly that type. `paired_t_over_units` and `paired_percentile_of_derived` both return the documented `method` strings the record asserts in Task 7. `Interval` is confirmed to be a frozen dataclass with **three** fields — `low`, `high`, `method` — with no `draws_used`; `percentile_of_derived` returns a **tuple** of `(Interval | None, int)` and `paired_percentile_of_derived` matches that shape.

**Three assumptions verified against the codebase before writing.** `Interval` has exactly three fields, so nothing here unpacks or indexes it. `summarize_step` already takes a `resample` mapping of key → callable, so a derived metric's `compute` is available at the call site Task 7 needs it. And `min_reported_n` is written by `materialize.py` and read by nothing, which is why Task 7 closes it rather than assuming it works.

**The risk this plan carries.** Task 5 is where the pairing lives, and its failure mode is quiet: an implementation drawing each side independently produces a plausible, merely wider interval. The test that catches it is the narrowness comparison, and the task explicitly instructs writing the wrong version first to confirm the test fails against it. If that step is skipped, the whole-branch review should redo it.

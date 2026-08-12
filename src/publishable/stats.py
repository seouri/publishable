"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import hashlib
import math
import random
from collections.abc import Callable, Collection, Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scipy import stats as _scipy_stats

from publishable.errors import ContractError
from publishable.replication import LABEL_JOIN

if TYPE_CHECKING:
    from publishable.replication import RepeatLevel
    from publishable.runner import ExecutionResult

#: Keys a step block holds that are not metrics, and so may not be metric names.
#: `by` carries the reporting strata (`reference.md` § Reporting strata): a
#: mapping of attribute to level to another metric block, sitting beside the
#: metric names in the same mapping. A derived metric of that name would be
#: overwritten by the strata — or, worse, would be differenced as a contrast
#: metric, since every consumer of a step block reads its keys as metric names.
RESERVED_METRIC_NAMES = frozenset({"by"})


@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    method: str


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


def mean_of(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def t_over_units(values: Sequence[float], confidence: float = 0.95) -> Interval | None:
    """Student's t on the per-unit values, df = completed units − 1.

    Returns None below two values: df would be zero and there is no dispersion
    to describe. Reporting a point with no interval is honest; inventing one is not.
    """
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    sem = math.sqrt(variance) / math.sqrt(n)
    critical = float(_scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1))
    half = critical * sem
    return Interval(low=mean - half, high=mean + half, method="t_over_units")


def paired_t_over_units(diffs: Sequence[float], confidence: float = 0.95) -> Interval | None:
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


def resample_seed(digest: str) -> int:
    """From the design digest, never `parameters_hash`.

    Editing an unrelated parameter must not redraw a resample — the same rule
    fold partitions and `order_seed` follow (reference.md § What auto-derives from).
    """
    return int.from_bytes(hashlib.sha256(f"{digest}|resample".encode()).digest()[:4], "big")


def _percentile_ranks(draws: int, confidence: float) -> tuple[int, int]:
    """The symmetric pair of ranks a percentile interval reads off a sorted pool.

    Factored out so every percentile construction in this module — over raw
    values or over recomputed draws — shares one copy: an asymmetry fixed in
    one and not the other is exactly the defect this arithmetic already had
    once (S4a task 4's off-by-one on the upper rank).
    """
    tail = (1.0 - confidence) / 2.0
    lo = max(0, int(tail * draws) - 1)
    # Symmetric with `lo` in rank, not `int((1.0 - tail) * draws)` bare: that form
    # overshoots the upper rank by one on every interval. Floored at `lo` because
    # the symmetric form alone gives -1 at draws=1.
    hi = max(lo, min(draws - 1, int((1.0 - tail) * draws) - 1))
    return lo, hi


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


def min_honest_draws(confidence: float = 0.95) -> int:
    """The fewest resample draws a percentile interval may be read off.

    `_percentile_ranks` floors the lower rank at 0, so below this count the
    interval's lower endpoint *is* the sample minimum while the upper endpoint
    keeps shrinking with n: low-biased and systematically too narrow, and at
    two surviving draws `lo == hi` and the "interval" has zero width. The
    threshold is the smallest n at which both ranks are interior — `int(tail *
    n) >= 2`, so `lo >= 1` and `hi <= n - 2` — which is 80 draws at 95 %
    confidence. Below it there is no honest interval to report, and reporting
    a point with no interval is what core does everywhere else it runs out of
    evidence (`t_over_units`, `percentile_over_units`).

    Derived from `confidence` rather than written as a literal so the two move
    together: a caller asking for 99 % needs 400.
    """
    tail = (1.0 - confidence) / 2.0
    return math.ceil(2.0 / tail)


def percentile_over_units(
    values: Sequence[float], seed: int, draws: int = 2000, confidence: float = 0.95
) -> Interval | None:
    """A percentile interval over the units, by resampling with replacement.

    This is what gives a *column* metric a resampled `ci95` when `resample` is
    declared (`reference.md` § How a metric becomes a number): the mean is
    recomputed on each bootstrap draw. A derived metric — one `aggregate`
    computed, with no per-unit value of its own — needs `aggregate` itself
    recomputed on each draw instead, which is what `percentile_of_derived` does.
    """
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
    rng = random.Random(seed)
    # Sorted, not just `list(values)`: with a fixed seed, `rng.randrange(n)` draws
    # the same sequence of *indices* regardless of input order, so drawing from an
    # unsorted pool would make the resample depend on row order — the multiset of
    # values must be all that matters.
    pool = sorted(values)
    n = len(pool)
    means = sorted(sum(pool[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    lo, hi = _percentile_ranks(draws, confidence)
    return Interval(low=means[lo], high=means[hi], method="percentile_over_units")


def percentile_of_derived(
    collapsed: dict[str, dict[str, float]],
    compute: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
) -> tuple[Interval | None, int]:
    """A percentile interval for a derived metric, by recomputing it, and the
    number of draws it actually rests on.

    A derived metric has no per-unit value to resample directly — `aggregate`
    returned one number for the whole table, not one per unit — so this is
    the construction `reference.md` § How a metric becomes a number specifies:
    resampling requires recomputing the metric, "which core can do only for a
    metric it knows how to compute... a template `aggregate(units, cfg)`."
    `stats.py` stays pure by taking `compute` as a plain callable rather than
    importing anything: the caller (`cli.py`) closes over the template and
    `cfg`, and this function never does.

    Costs `draws` calls to `compute` — 2000 by default, matching
    `percentile_over_units` — so a caller wrapping an expensive `aggregate`
    should pass a smaller `draws`, and a test exercising this should too.

    Units are sorted by key before drawing, for the same row-order invariance
    `percentile_over_units` gets from sorting its own pool: a fixed seed draws
    a fixed sequence of *indices*, so an unsorted roster would make the
    interval depend on iteration order rather than on the multiset of units.
    Each draw's `UnitTable` is built with the *real* unit keys a bootstrap draw
    repeats, not a synthetic `0..n-1` re-key — `UnitTable` derives its `unit`
    column from the mapping key it was built from, so re-keying would make
    `units.unit` read as `n` distinct labels inside every draw even though a
    resample duplicates units by construction; a template that legitimately
    reads `unit` (a per-unit weight lookup keyed by it, say) would silently see
    the wrong roster. A plain dict can't hold the resulting duplicate keys, so
    the table is built from a row list instead, bypassing the dict-keyed
    constructor.

    A draw on which `compute` returns `None`, returns `nan`, or *raises* is
    dropped rather than counted. The three are the same situation from three
    different libraries: a resampled table with no variance makes `pearsonr`
    return `nan`, makes a hand-rolled ratio raise `ZeroDivisionError`, and a
    template author who checks for that case explicitly return `None` — which
    library `aggregate` happens to call is not a fact about whether the draw
    was degenerate, so it can't be what decides whether the draw counts. The
    one call this function does *not* make robust this way is the single
    unresampled call to `aggregate` that produces the reported `value` — that
    one is the metric's real definition for this table, so a failure there is
    a fault to surface, not a degenerate draw to skip, and is contained by the
    caller instead (`cli.py`, where the failure is disclosed rather than
    silently producing a table this function has no way to distinguish from
    "computed cleanly on the third try").

    Counting `None`/`nan`/raise as skipped can only shrink the surviving count
    relative to `draws`, so the percentile ranks are read off *that* count,
    and the second return value is that surviving count — **always**, even
    when the interval is `None`. That is what lets `summarize_step` tell "the
    resample was attempted and every draw was degenerate" (a surviving count
    of 0) apart from "resampling was never attempted at all" (no count
    to report), which otherwise reach `run.yaml` byte-identical: both would
    write `ci95: null` and nothing else. An interval quietly built from 200 of
    2000 requested draws would read identically to a clean one for the same
    reason, which is why the count is returned even on success. Below
    `min_honest_draws(confidence)` survivors — 80 at 95 % — there is no
    interval a percentile can honestly be read off (that function says why),
    so the interval is `None` while the count returned alongside it stays
    real. `cli.py` warns on any shortfall, a count below the floor and a count
    merely reduced being the same event at two magnitudes.
    """
    keys = sorted(collapsed)
    if len(keys) < 2:
        return None, 0
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        table = unit_table_from_rows([{"unit": key, **collapsed[key]} for key in drawn])
        try:
            value = compute(table)
        # Degenerate, not caught for the real call; see above. Also the
        # containment for a template returning a non-numeric metric:
        # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return
        # reaches `cli.py`'s resample closure, which floats whatever
        # `aggregate` returned — and `float("high")` raises `ValueError` on
        # every draw, caught here beside a degenerate `ZeroDivisionError`.
        # Narrowing this to a closed set that drops `ValueError` reopens that
        # path; see the pin in tests/test_stats.py.
        except Exception:
            continue
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        values.append(float(value))
    if len(values) < min_honest_draws(confidence):
        return None, len(values)
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return (
        Interval(low=values[lo], high=values[hi], method="percentile_over_units"),
        len(values),
    )


def paired_delta_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
) -> float | None:
    """The point estimate `paired_percentile_of_derived` builds an interval for.

    A derived metric has no per-unit value to difference, so its delta has to be
    `aggregate` evaluated on each side and subtracted — but over **the same
    units the interval is built from**, which is the intersection of both sides'
    completed units narrowed by the contrast's `within`, not each condition's
    own whole-sample table. `reference.md` § Contrasts: "a paired comparison
    exists only for units that completed in *both*. Differencing the two
    condition means instead would not be a paired comparison at all, however
    carefully `paired: true` was derived."

    It lives here, beside the interval it belongs to, because the two were
    computed in different modules once and drifted apart: the interval moved to
    the intersection and the point estimate stayed whole-sample, which produced
    a `ci95` that could not contain its own `delta`. A caller that can only get
    both from one call cannot reintroduce that.

    `None` — never a number — when there are no paired units or either side's
    `aggregate` declines to produce a value. `reference.md`: "A contrast whose
    intersection is empty is reported as such rather than as a delta of zero."
    """
    if not keys:
        return None
    table_of = unit_table_from_rows([{"unit": k, **of[k]} for k in keys])
    table_against = unit_table_from_rows([{"unit": k, **against[k]} for k in keys])
    try:
        a = compute_of(table_of)
        b = compute_against(table_against)
    # The same treatment the real call gets in `percentile_of_derived`. Also
    # the same containment for a template returning a non-numeric metric:
    # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return reaches
    # `cli.py`'s resample closure, which floats whatever `aggregate`
    # returned — and `float("high")` raises `ValueError`, caught here.
    # Narrowing this to a closed set that drops `ValueError` reopens that
    # path; see the pin in tests/test_stats.py.
    except Exception:
        return None
    if a is None or b is None:
        return None
    delta = float(a) - float(b)
    return None if math.isnan(delta) else delta


def paired_percentile_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
) -> PairedResample:
    """Percentiles of the resampled difference, one draw applied to both sides.

    Drawing each side independently would resample the two conditions apart and
    destroy the pairing — the same error as differencing the two sides' own
    intervals. Both spellings produce a plausible interval; only this one is
    narrower, which is what `allocation: within` buys.

    Two computes, not one — a contrast can hold its two sides' `cfg` fixed on
    every axis except the one being compared, but `aggregate(units, cfg)` is
    still evaluated once per side with that side's own `cfg`. A single shared
    `compute` (as an earlier revision of this function took) is only correct
    when the two sides evaluate the same formula; the moment a swept axis
    changes which formula `aggregate` runs — analysis.method: pearson vs.
    spearman, the documented worked example's own case — a shared compute
    evaluates *one* side's formula against *both* sides' resampled draws. Where
    the two collapsed tables hold identical per-unit data (exactly the
    worked-example shape: `pred`/`truth` don't vary with `analysis.method`,
    only which correlation `aggregate` computes from them does), that shared
    evaluation cancels on every single draw — a `ci95` of zero width at zero,
    beside a nonzero point-estimate delta, the "plausible but wrong" case with
    nothing to raise. A caller that genuinely wants the same statistic on both
    sides passes the same callable twice; that's a normal call, not a special
    case this function has to detect.
    """
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        table_a = unit_table_from_rows([{"unit": k, **of[k]} for k in drawn])
        table_b = unit_table_from_rows([{"unit": k, **against[k]} for k in drawn])
        try:
            a = compute_of(table_a)
            b = compute_against(table_b)
        # A degenerate draw, not a fault; see `percentile_of_derived`. Also the
        # same containment for a template returning a non-numeric metric:
        # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return reaches
        # `cli.py`'s resample closure, which floats whatever `aggregate`
        # returned — and `float("high")` raises `ValueError`, caught here.
        # Narrowing this to a closed set that drops `ValueError` reopens that
        # path; see the pin in tests/test_stats.py.
        except Exception:
            continue
        if a is None or b is None:
            continue
        diff = float(a) - float(b)
        if math.isnan(diff):
            continue
        values.append(diff)
    if len(values) < min_honest_draws(confidence):
        return PairedResample(interval=None, draws_used=len(values), pool=sorted(values))
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return PairedResample(
        interval=Interval(low=values[lo], high=values[hi], method="paired_percentile_over_units"),
        draws_used=len(values),
        pool=values,
    )


def _is_numeric(value: object) -> bool:
    """`bool` is a `int` subclass in Python but is never a quantity to average."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def handed_to(
    unit_key: str, labels: list[str], fold_members: dict[str, frozenset[str]] | None
) -> list[str]:
    """The repeat labels this unit was actually given.

    Without a fold, every repeat — the S2 rule, and the reason `fold_members=None`
    leaves every existing path on exactly the membership and values it had. With a
    fold, only the
    labels whose fold component holds this unit: `reference.md` § The per-unit
    tables is explicit that intersecting over *every* repeat "would report
    `completed: 0` for any design containing a fold, because no unit is ever in
    more than one of them."

    A composed label is split on `LABEL_JOIN`, so `fold02_seed17` is handed to a
    unit of `fold02` regardless of which level the fold was declared at. Fold
    member labels are single tokens (`fold01`, from `replication._seed_members`),
    which is what makes that split safe.
    """
    if fold_members is None:
        return list(labels)
    mine = {f for f, keys in fold_members.items() if unit_key in keys}
    return [lb for lb in labels if set(lb.split(LABEL_JOIN)) & mine]


def collapse_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, float]]:
    """Average each unit's numeric columns across the repeats that recorded it,
    within one condition.

    This is the collapse the inference base rests on: repeats are a variance
    component, not the inference base, so a unit's repeats are averaged into one
    row *before* any interval is computed over units.

    `condition_index` is required, not defaulted, on purpose: core aggregates
    within each condition and never pools across conditions, which would be
    meaningless (`reference.md` § Statistical reporting). Making the parameter
    required turns a caller that forgets it into a `TypeError` at the call site
    rather than a silently pooled mean in a `run.yaml` no reviewer could catch —
    S2 always has exactly one condition and always passes `0`, but the signature
    must not invite the mistake on the day a sweep adds a second one.

    Reads only `repeat`-scoped executions of `step_name` in this condition — a
    `condition`- or `run`-scoped step's rows, another step's rows, and another
    condition's rows never enter this table.

    Only a unit recorded in every repeat it was *handed* (within this condition)
    enters the table at all — the same intersection `runner.attrition` takes for
    `completed`, and for the same reason: a unit present in three of five seeds
    would otherwise enter the average on a different number of observations than
    its neighbours, which is a ragged table dressed as a rectangular one. A unit
    recorded in some of the repeats it was handed and not others is dropped here
    exactly as it is excluded from `completed` there, so the `n` reported beside
    this table's interval is never a lie about how many observations went into it.

    "Handed" is what `fold_members` narrows. Without a fold it is every repeat,
    which is the rule above unchanged. With one, `reference.md` § The per-unit
    tables is explicit that intersecting over *every* repeat "would report
    `completed: 0` for any design containing a fold, because no unit is ever in
    more than one of them" — so the intersection is taken over that unit's own
    fold's repeats instead. The average follows from the same set, which is what
    makes the collapse **inner-to-outer** (`reference.md` § How a metric becomes
    a number): under `fold` alone a unit has one handed label and its value
    passes through unchanged, so folds *concatenate* into the union of the
    partitions; under `fold × seed` the handed labels are that fold's seeds, so
    the seeds average within the fold before the folds are combined. Flattening
    all 30 executions of a 10 × 3 design would average numbers that are not
    exchangeable, and averaging across folds would divide each unit's single
    observation by one — both produce plausible values and neither raises, which
    is why this is stated at length.

    A non-numeric value (a string, or a bool — `bool` is an `int` subclass but
    never a quantity to average) is dropped from the column for that unit rather
    than averaged; a unit that recorded a column as a string in every repeat
    simply has no entry for that column in the collapsed table, which
    `summarize_step` then correctly omits rather than reporting a bogus mean.
    """
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        # Strict, for the same reason as `runner.attrition`: `or 0` would fold an
        # unexpected `None` into condition 0's table, which is the cross-condition
        # pooling the required `condition_index` parameter exists to make unwritable.
        and r.execution.condition_index == condition_index
    ]
    if not recording:
        return {}
    # Accumulated rather than built by comprehension: two executions sharing one
    # repeat label (a resumed leaf re-reported, say) must merge, not overwrite.
    # A dict comprehension would drop the earlier rows while `labels` still held
    # the label once per execution, counting the survivor twice in the mean —
    # a wrong average that looks entirely plausible.
    rows_by_label: dict[str, list[dict[str, Any]]] = {}
    recorded_by_label: dict[str, set[str]] = {}
    for r in recording:
        label = r.execution.repeat_label or ""
        rows_by_label.setdefault(label, []).extend(r.rows)
        recorded_by_label.setdefault(label, set()).update(r.recorded)
    labels = list(recorded_by_label)  # unique, in execution order

    candidates: set[str] = set()
    for keys in recorded_by_label.values():
        candidates |= keys

    gathered: dict[str, dict[str, list[float]]] = {}
    # `sorted`, and load-bearing rather than incidental: `summarize_step` derives a
    # metric's column order from this dict's values, so a ragged table's `run.yaml`
    # column order follows this loop. Encounter order varies with `order: randomized`
    # — the shuffle decides which execution is seen first — so sorting is what makes
    # that order a property of the roster instead of of the shuffle.
    for key in sorted(candidates):
        mine = handed_to(key, labels, fold_members)
        # The intersection, scoped to what this unit was handed. `not mine` drops
        # a unit no repeat was given — under a fold, one whose key is in no
        # partition — rather than letting `all()` over an empty set admit it.
        if not mine or any(key not in recorded_by_label[lb] for lb in mine):
            continue
        for lb in mine:
            for row in rows_by_label[lb]:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    if column == "unit" or not _is_numeric(value):
                        continue
                    gathered.setdefault(key, {}).setdefault(column, []).append(float(value))
    return {
        key: {col: sum(vals) / len(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }


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


def _is_anonymous_level(level: "RepeatLevel") -> bool:
    """The single-`seed`-level `resolve_repeats` synthesizes when no
    `replication` block is declared at all — never produced by a declared
    level, since every declared `seed`/`batch`/`fold` member gets a real,
    non-empty label from `_seed_members`. It's an implementation detail of
    how core represents "no repeats declared", not a design the user
    expressed, which is why `repeat_spread` gives it no entry while a
    *declared* `{kind: seed, n: 1}` still reports `{std: 0.0, n: 1, ...}`.
    """
    return level.kind == "seed" and level.n == 1 and level.members[0].label == ""


def repeat_spread(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    levels: "list[RepeatLevel]",
    column: str,
    keys: "Collection[str]",
) -> list[dict[str, Any]]:
    """How much each repeat level moved one metric's recorded values, one
    entry per level, outer to inner — `reference.md` § A `batch` says *when*,
    not *what*. `column` is the one recorded column this figure describes:
    pooling every numeric column of a row into one mean would average, say,
    `pred` and `truth` together and then report that blended number as the
    dispersion of each — dispersion is per metric, the same way the interval
    beside it is.

    A `fold` level contributes no entry on its own: each unit appears in
    exactly one fold, so there is nothing to average across (the same reason
    S3c's collapse concatenates across folds rather than averaging). Nested
    with another level (`fold x seed`), the honest per-level figure would
    need the metric recomputed over each fold's own slice — a materially
    heavier operation this passenger does not implement — so the whole
    result is omitted rather than reporting a differently-computed number
    under the same key; see `docs/superpowers/spec-defects.md`. The anonymous
    single-seed level (no `replication` block declared) is skipped the same
    way `fold` is, via `_is_anonymous_level`.

    Every other level gets a per-member mean of its recorded values for
    `column`, then the population standard deviation (divide by `n`, not
    `n - 1`) of those member means — population rather than sample so a
    single-member level falls out as exactly `0.0` with no special case,
    which is what a lone repeat's dispersion honestly is. `n` is the number
    of members that actually contributed a mean, not the level's declared
    count: a member with no matching rows for this column contributes
    nothing, and `std`/`n` must describe the same set of numbers.

    A member's rows are found by matching its label against the tokens of
    each execution's composed `repeat_label`, split on `LABEL_JOIN` — the
    same idiom `realize_order` uses to find a batch's rows inside
    `batch01_seed42`.

    `keys` is the unit set this figure is allowed to read: the keys of the
    collapsed table the `value` and `ci95` beside it rest on. Required rather
    than defaulted, so no call site can forget it. Reading *every* recorded
    row instead would compute the dispersion over a different population than
    the interval printed under the same metric key: a unit recorded in one
    repeat and lost in another is excluded from `collapse_repeats` by the same
    intersection that defines `completed`, but its lone value would still move
    one member's mean and none of the others, so ordinary single-unit
    attrition reads as a pipeline that is wildly unstable — or, under `batch`,
    as apparatus drift. That is the "ragged table dressed as a rectangular
    one" confound `collapse_repeats` refuses, and this filter is what keeps it
    from re-entering one field over.
    """
    admitted = set(keys)
    if len(levels) > 1 and any(lv.kind == "fold" for lv in levels):
        return []
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        and r.execution.condition_index == condition_index
    ]
    entries: list[dict[str, Any]] = []
    for level in levels:
        if level.kind == "fold" or _is_anonymous_level(level):
            continue
        member_means: list[float] = []
        for member in level.members:
            values = [
                float(row[column])
                for r in recording
                if member.label in (r.execution.repeat_label or "").split(LABEL_JOIN)
                for row in r.rows
                if row["unit"] in admitted and column in row and _is_numeric(row[column])
            ]
            if values:
                member_means.append(sum(values) / len(values))
        if not member_means:
            continue
        grand_mean = sum(member_means) / len(member_means)
        variance = sum((m - grand_mean) ** 2 for m in member_means) / len(member_means)
        entries.append({"std": math.sqrt(variance), "n": len(member_means), "kind": level.kind})
    return entries


def summarize_step(
    collapsed: dict[str, dict[str, float]],
    counts: dict[str, int],
    derived: dict[str, Any] | None = None,
    seed: int | None = None,
    resample: "dict[str, Callable[[UnitTable], float | None]] | None" = None,
    draws: int = 2000,
    beside_n: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Per-column value, basis, `n`, and interval over the collapsed unit table.

    Every column here is `basis: units`: it was a recorded column, `n` counts
    units, and the interval is `t_over_units` over the per-unit values — or
    `None` below two units, since a single observation has no dispersion to
    describe and inventing an interval for it would not be honest.

    `n.completed` is per COLUMN, not the condition-wide figure `counts` carries:
    `StepIO.finalize()` deliberately writes the union of recorded keys with nulls
    for columns a unit didn't carry, so a column recorded only for a subset of
    completed units — eligible-positive units, say — is an ordinary ragged shape,
    not a bug. Reporting the condition-wide `completed` beside that column's
    interval would be a lie about how many observations went into it, which is
    exactly the guarantee this module's own docstring makes. `resolved`,
    `ineligible`, and `failed` stay condition-wide from `counts`: they describe the
    roster a condition drew from, not any one column, and every column in the
    table shares that one roster.

    A column is skipped entirely — not coerced, not defaulted — when any unit's
    value for it is not a real number (a string, or a `bool`, which is an `int`
    subclass but never a quantity to average). Averaging a bool would silently
    read as a proportion; this refuses that rather than doing it quietly.

    `derived` is what a template's `aggregate` returned for this step, name →
    scalar, already computed once over the whole table for the reported
    `value`. `resample` is the matching name → callable, each one recomputing
    that one derived key on a resampled `UnitTable` — typically
    `lambda units: template.aggregate(units, cfg).get(key)`, closed over in
    `cli.py` since that is where the template and `cfg` live; `stats.py` never
    imports either. `percentile_of_derived` is what actually resamples: a
    derived metric has no per-unit value to run `t_over_units` over
    (`aggregate` returned one number, not one per unit), and `reference.md` §
    How a metric becomes a number is explicit that resampling one "can do only
    for a metric it knows how to compute... a template `aggregate(units,
    cfg)`" — recomputing is the only construction, there is no proxy for it. A
    key absent from `resample` (or given no `seed`) gets `ci95: null` rather
    than an invented width: reporting a point with no interval is honest.
    Every derived metric is `basis: units`, `method: percentile_over_units`
    when it has one, `cohens_d: null` — Cohen's *d* differences a per-unit
    value, and a derived metric has none — and `resample_draws`: `null` when
    resampling was never attempted (no callable, or no `seed`), and otherwise
    the number of `draws` (passed through to `percentile_of_derived`, 2000 by
    default) that actually produced a value — `0` when every one was
    degenerate, matching `ci95: null` there too. `null` and `0` are different
    facts: one says nobody tried to resample this metric, the other says
    resampling was attempted and failed, and a caller (`cli.py`) that only
    checked `ci95: null` could not otherwise tell which happened.

    A derived key colliding with a recorded column — even one dropped above for
    being non-numeric — is refused with the same `E-STEP-KEY-COLLISION`
    `artifacts.py` raises for the sibling case: one name cannot hold both a
    column's mean and a derived value.

    `beside_n` is core-supplied context copied verbatim into every metric block —
    `technical_n` today. It is the second of two routes a count-shaped fact
    travels, and which one a new fact takes is decided by where `reference.md`
    shows it:

    - **A key that JOINS `n` travels in `counts`.** § What isn't a repeat says the
      three-part `n` is "joined by `clusters` … by `effective` … by `ineligible`",
      so those are parts of `n` and need no new carrier. (`counts` is annotated
      `dict[str, int]`; `effective` is Kish's size and is not an integer, so the
      task that adds it widens that annotation rather than inventing a route.)
    - **A key that sits BESIDE `n` travels here.** § What isn't a repeat shows
      `technical_n` as a sibling of `n` in the metric block, and § Weighted
      samples shows `weighted_by` in the same position.

    Copied into the derived branch as well as the recorded-column one, because
    the document's own example of a metric carrying `technical_n` is `r`, which
    `aggregate` derives. The computed keys are merged last and so always win: a
    caller cannot shadow `n`, `value`, or an interval with a key of this name.
    """
    columns: list[str] = []
    for cols in collapsed.values():
        for name in cols:
            if name not in columns:
                columns.append(name)
    out: dict[str, dict[str, Any]] = {}
    for column in columns:
        raw = [cols[column] for cols in collapsed.values() if column in cols]
        if not raw or not all(_is_numeric(v) for v in raw):
            continue
        values = [float(v) for v in raw]
        interval = t_over_units(values)
        out[column] = {
            **(beside_n or {}),
            "value": mean_of(values),
            "basis": "units",
            "n": {**counts, "completed": len(values)},
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
            # `W-STATS-FAMILY` warns the person; this null tells the record. The
            # generated config declares `statistics.correction: holm` by default,
            # so a metric that said nothing here could be misread as corrected —
            # multiplicity correction across conditions is not implemented yet.
            "correction": None,
        }
    if derived:
        # A derived key may not take a name the step block already spends on
        # something that is not a metric. Refused here, beside the recorded-column
        # collision and with the same identifier, because it is the same fault:
        # one name cannot hold both a metric and the block's strata. The recorded
        # -column half of this cannot be refused here — the caller's retry passes
        # the same `collapsed` and would re-raise uncontained — so `cli.py` warns
        # for that one instead.
        reserved = set(derived) & RESERVED_METRIC_NAMES
        if reserved:
            name = sorted(reserved)[0]
            raise ContractError(
                f"{name!r} is reserved for a step block's reporting strata and may "
                "not be a derived metric name",
                code="E-STEP-KEY-COLLISION",
            )
        collision = set(derived) & set(columns)
        if collision:
            name = sorted(collision)[0]
            raise ContractError(
                f"{name!r} collides with a recorded column of the same name: a "
                "derived key may not shadow a recorded column",
                code="E-STEP-KEY-COLLISION",
            )
        for key, value in derived.items():
            compute = (resample or {}).get(key)
            # `draws_used` is `None` only when resampling was never attempted
            # at all (no callable, or no `seed`) — attempted-and-failed
            # reports `0`, not `None`, which is the distinction Task 6's
            # review named: without it, "every draw raised" and "nobody
            # supplied a `resample` callable" write the same `run.yaml`.
            derived_interval: Interval | None
            draws_used: int | None
            if compute is not None and seed is not None:
                derived_interval, draws_used = percentile_of_derived(
                    collapsed, compute, seed, draws=draws
                )
            else:
                derived_interval, draws_used = None, None
            out[key] = {
                **(beside_n or {}),
                "value": value,
                "basis": "units",
                "n": {**counts, "completed": len(collapsed)},
                "ci95": (
                    [derived_interval.low, derived_interval.high] if derived_interval else None
                ),
                "method": derived_interval.method if derived_interval else None,
                "correction": None,
                "cohens_d": None,
                # How many of `draws` requested actually produced a value —
                # `None` when resampling wasn't attempted, `0` (or `1`) when
                # it was attempted and every draw was degenerate, and the real
                # survivor count on success. A degenerate-draw-heavy interval
                # built from 200 survivors would otherwise read identically to
                # a clean 2000-draw one (see `percentile_of_derived`).
                "resample_draws": draws_used,
            }
    return out


class UnitTable:
    """Row iteration, column access, `len`, `columns` — and nothing else.

    Deliberately not a `DataFrame`: one that also promised indexing, filtering
    and `.loc` would be one, and core could never change what backs it — a lazily
    materialized table, a view over a partition — without breaking every plugin.
    The same reasoning that keeps `io.units` to three operations.
    """

    def __init__(self, collapsed: dict[str, dict[str, float]]) -> None:
        self._rows = [{"unit": key, **values} for key, values in collapsed.items()]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def columns(self) -> list[str]:
        # A property, not something `__getattr__` serves: `__getattr__` runs only
        # when normal attribute lookup fails, so a real property is the only way
        # a recorded column literally named `columns` can't shadow it — the same
        # shadowing question `cfg`'s no-methods rule answers.
        seen: dict[str, None] = {}
        for row in self._rows:
            for key in row:
                if key != "unit":
                    seen[key] = None
        return list(seen)

    def __getattr__(self, name: str) -> list[Any]:
        """That column, as a sequence in row order — one entry per row, `None`
        where the unit recorded nothing.

        Full length rather than "the units that recorded it", which is what
        `reference.md` § Templates requires: `units.truth` and `units.pred`
        "are the same shape whichever of the two supplied them", and § The
        per-unit tables says "a column absent from a row reads as `None`".
        Dropping missing rows *per column* — the earlier rule, right for a
        single-column mean and wrong for every multi-column read — makes two
        columns ragged in *different* rows come back mispaired, so
        `pearsonr(units.pred, units.truth)` (`reference.md`'s own example)
        would correlate one unit's prediction against another's truth and
        publish it with a resampled interval around it. Row alignment is the
        only property that makes the pairing correct by construction; a
        template summing a column that holds a `None` gets a loud `TypeError`,
        contained and disclosed as `W-STATS-AGGREGATE-FAILED`.

        The refusal is keyed on "this name appears in no row", not on
        `columns` membership: `columns` deliberately omits `unit`, which a
        template may legitimately read (`percentile_of_derived` keeps the real
        unit keys inside every draw precisely so it can).
        """
        if name.startswith("_"):
            raise AttributeError(name)
        if not any(name in row for row in self._rows):
            raise ContractError(
                f"{name!r} is not a column this table holds; it has "
                f"{', '.join(self.columns) or 'no columns'}",
                code="E-STEP-COLUMN-UNKNOWN",
            )
        return [row.get(name) for row in self._rows]


def unit_table_from_rows(rows: list[dict[str, Any]]) -> UnitTable:
    """Build a `UnitTable` from rows that may repeat a unit key.

    `UnitTable.__init__` takes a `dict[str, dict]`, which cannot hold two rows
    for the same key — the right shape for the one row per unit every other
    caller builds. A bootstrap draw repeats units by construction, so
    `percentile_of_derived` needs this instead: each row keeps its *real*
    `unit` value (duplicated, as the draw duplicated it), and this bypasses
    `__init__` rather than re-keying to something synthetic and unique, which
    is what made every draw's units look distinct to a template that reads
    `unit` before this function existed.

    Public rather than private because `cli.py` needs it for the same reason:
    merging a unit's declared attributes into the table a template's `aggregate`
    reads is a row-level operation (`columns` then names them for free), and the
    table it has to merge into is sometimes one of these draws.
    """
    table = UnitTable.__new__(UnitTable)
    table._rows = rows
    return table

"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import hashlib
import math
import random
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scipy import stats as _scipy_stats

from publishable.errors import ContractError
from publishable.replication import LABEL_JOIN

if TYPE_CHECKING:
    from publishable.runner import ExecutionResult


@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    method: str


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
) -> Interval | None:
    """A percentile interval for a derived metric, by recomputing it.

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

    A draw on which `compute` returns `None` or `nan` — a resampled table with
    no variance for a correlation, say, which is exactly what a degenerate
    bootstrap draw of `r` can produce — is dropped rather than counted:
    `compute` returning `None`/`nan` is its own signal that the metric isn't
    defined on that draw, and counting it as a value would corrupt the
    distribution with a number that was never really computed. This can only
    ever shrink the surviving count relative to `draws`, so the percentile
    ranks are read off *that* count. Below two surviving draws there is
    nothing to take percentiles of — the same refusal `t_over_units` and
    `percentile_over_units` make below two units — so the interval is `None`
    rather than one built from too few draws to mean anything. A `compute`
    that raises is not caught here: that is a real fault in the metric, not a
    degenerate draw, and swallowing it would hide a bug behind a missing
    interval instead of surfacing it.
    """
    keys = sorted(collapsed)
    if len(keys) < 2:
        return None
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        table = UnitTable({str(i): collapsed[key] for i, key in enumerate(drawn)})
        value = compute(table)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        values.append(float(value))
    if len(values) < 2:
        return None
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return Interval(low=values[lo], high=values[hi], method="percentile_over_units")


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


def summarize_step(
    collapsed: dict[str, dict[str, float]],
    counts: dict[str, int],
    derived: dict[str, Any] | None = None,
    seed: int | None = None,
    resample: "dict[str, Callable[[UnitTable], float | None]] | None" = None,
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
    when it has one, and `cohens_d: null` — Cohen's *d* differences a per-unit
    value, and a derived metric has none.

    A derived key colliding with a recorded column — even one dropped above for
    being non-numeric — is refused with the same `E-STEP-KEY-COLLISION`
    `artifacts.py` raises for the sibling case: one name cannot hold both a
    column's mean and a derived value.
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
            interval = (
                percentile_of_derived(collapsed, compute, seed)
                if compute is not None and seed is not None
                else None
            )
            out[key] = {
                "value": value,
                "basis": "units",
                "n": {**counts, "completed": len(collapsed)},
                "ci95": [interval.low, interval.high] if interval else None,
                "method": interval.method if interval else None,
                "correction": None,
                "cohens_d": None,
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
        if name.startswith("_"):
            raise AttributeError(name)
        values = [row[name] for row in self._rows if name in row]
        if not values:
            raise ContractError(
                f"{name!r} is not a column this table holds; it has "
                f"{', '.join(self.columns) or 'no columns'}",
                code="E-STEP-COLUMN-UNKNOWN",
            )
        return values

"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scipy import stats as _scipy_stats

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


def _is_numeric(value: object) -> bool:
    """`bool` is a `int` subclass in Python but is never a quantity to average."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def collapse_repeats(
    results: "list[ExecutionResult]", step_name: str, condition_index: int
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

    Only a unit recorded in *every* repeat-scoped execution of this step (within
    this condition) enters the table at all — the same intersection
    `runner.attrition` takes for `completed`, and for the same reason: a unit
    present in three of five seeds would otherwise enter the average on a
    different number of observations than its neighbours, which is a ragged
    table dressed as a rectangular one. A unit recorded in some repeats and not
    others is dropped here exactly as it is excluded from `completed` there, so
    the `n` reported beside this table's interval is never a lie about how many
    observations went into it.

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
        and (r.execution.condition_index or 0) == condition_index
    ]
    if not recording:
        return {}
    completed = set(recording[0].recorded)
    for r in recording[1:]:
        completed &= r.recorded

    gathered: dict[str, dict[str, list[float]]] = {}
    for r in recording:
        for row in r.rows:
            key = row["unit"]
            if key not in completed:
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
    collapsed: dict[str, dict[str, float]], counts: dict[str, int]
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
        }
    return out

"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from scipy import stats as _scipy_stats


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

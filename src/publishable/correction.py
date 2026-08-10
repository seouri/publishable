"""The correction family: who is in it, how they rank, and what each one gets.

Pure: comparisons in, corrected fields out. `reference.md` § Statistical
reporting is the specification — the family is comparisons × metrics, the rank
is the point estimate over half the raw interval's width, and a corrected
interval is an interval at a smaller α.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from publishable.stats import interval_at, paired_t_over_units

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

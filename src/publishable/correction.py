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

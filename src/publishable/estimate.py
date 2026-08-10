"""An interval a `summary` step computed itself.

`docs/reference.md` § `Estimate`: returned as a bare dict, an interval "is a key
core can't tell from any other — `report` won't render it as an interval,
`study add` can't see the denominator it's over, and nothing in the record
distinguishes it from one core computed from the unit table." This type is that
distinction, and `reported: true` in the record is what it buys.

Deliberately no validation here. The three rules `reference.md` states —
`method` required whenever `ci95` is present, a surfaced missing `n`, and
`summary` scope only — are all diagnostics core emits when the return is
recorded, each carrying an `E-`/`W-` identifier a reader can grep. A raise from
this constructor would land inside a plugin's `run` as a bare traceback with no
identifier, which is the shape every diagnostic in this codebase exists to
replace.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Estimate:
    """`value` plus the optional interval a step computed for it.

    `ci95` is a `list` rather than a tuple, matching how `reference.md`'s example
    constructs one and how the record dumps it; that makes this frozen dataclass
    unhashable, and nothing keys on it.
    """

    value: float
    ci95: list[float] | None = None
    n: int | None = None
    method: str | None = None

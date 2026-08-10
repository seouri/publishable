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
    for entry in (config.get("statistics") or {}).get("contrasts") or []:
        # by_label[...] raises KeyError on an unresolvable label. That is
        # acceptable only because validate (Task 6) refuses an unresolvable
        # `of`/`against` at validate time, and `cli` always validates before
        # running — this function does not need to guard it itself.
        out.append(
            Comparison(
                id=str(entry.get("id")),
                of=by_label[entry["of"]],
                against=by_label[entry["against"]],
                within=entry.get("within"),
            )
        )
    return out

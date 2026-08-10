"""Which units each level of a reporting attribute picks out. Pure: roster in,
key sets out.

`docs/reference.md` § Reporting strata: `report_by` names unit attributes, and
core "repeats the aggregation it already performs, over the subsets of the
per-unit table each level picks out". This module is only the *which units*
half — the aggregation itself is `stats.summarize_step`, unchanged.
"""

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from publishable.units import UnitList


def levels_for(roster: "UnitList", attribute: str) -> dict[str, set[str]]:
    """Each level of `attribute`, and the keys of the units carrying it.

    Values compare as strings, the same coercion `contrasts.units_matching`
    makes and for the same reason: a config's YAML gives `1` as an int while
    the same attribute read from a table is `"1"`, and a stratum that split on
    the difference would report one subgroup as two.

    A unit whose attribute is absent or `None` joins no level. Coercing it to
    the string `"None"` would publish a subgroup named after a bug, and there
    is no honest level for "we don't know" — such a unit is simply absent from
    every stratum's `n`, which is why the levels' counts need not sum to the
    condition's.

    An attribute no unit carries yields `{}` rather than raising: `validate`
    refuses one not declared in `data.units.attributes`, so this is unreachable
    from a validated config, and a pure function has no diagnostic to raise.
    """
    out: dict[str, set[str]] = defaultdict(set)
    for unit in roster:
        value = unit.attributes.get(attribute)
        if value is not None:
            out[str(value)].add(unit.key)
    return dict(out)

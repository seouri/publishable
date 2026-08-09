"""Sweep expansion. See docs/reference.md § Expansion modes.

Pure: a config dict in, an ordered condition list out. No filesystem, no
`Config` object, no git — expansion is a function of the declaration alone,
so it can be tested exhaustively without a repository.

A `baseline` whose values happen to coincide with a grid cell produces two
conditions with identical `values` — `00_baseline` and the matching grid
row — and `expand` deliberately does not dedup them: the baseline is
declared and the grid is mechanical, and reconciling the two is not
`expand`'s job.
"""

import itertools
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any


@dataclass(frozen=True)
class Condition:
    index: int
    label: str | None
    values: Mapping[str, Any] = field(default_factory=dict)
    is_baseline: bool = False

    def __post_init__(self) -> None:
        # `values` is a plain dict handed in by `expand`; without wrapping it, a
        # caller could mutate a condition's values after the fact, or reach back
        # through the dict it originally passed in. The proxy over a copy is what
        # makes `values["x"] = ...` raise rather than silently drift out of sync
        # with `sweep.yaml`, written from these same objects. Same fix as
        # `Unit.attributes` in `units.py`, same reason.
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))


SWEPT_VALUE_PATTERN = r"^[A-Za-z0-9._+-]+$"


def render_value(value: Any) -> str:
    """As written in the config: `true`/`false` for booleans, shortest round-trip float."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _keys_for(paths: list[str]) -> dict[str, str]:
    """The shortest suffix of each dotted path that is unique among them all.

    A label is also a selector, so the key has to be something a reader can
    type without opening the directory — but it must still identify one axis.
    """
    keys: dict[str, str] = {}
    for path in paths:
        segments = path.split(".")
        for depth in range(1, len(segments) + 1):
            candidate = ".".join(segments[-depth:])
            others = [p for p in paths if p != path]
            if not any(p == candidate or p.endswith("." + candidate) for p in others):
                keys[path] = candidate
                break
        else:
            keys[path] = path
    return keys


def label_for(values: dict[str, Any], grid: dict[str, Any], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    keys = _keys_for(list(grid))
    return "__".join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )


def expand(config: dict[str, Any]) -> list[Condition]:
    """Ordered conditions: a declared baseline as 00, then the grid product.

    With no `sweep` block, one condition whose label is None — which is what
    keeps the `conditions/` level out of the artifact tree.
    """
    sweep = config.get("sweep") or {}
    if not sweep:
        return [Condition(index=0, label=None, values={}, is_baseline=False)]

    rows: list[tuple[dict[str, Any], bool]] = []
    baseline = sweep.get("baseline")
    if baseline:
        rows.append((dict(baseline), True))

    grid = sweep.get("grid") or {}
    if grid:
        axes = list(grid.items())
        # itertools.product varies the LAST argument fastest, which is exactly
        # the declared-order nesting the specification asks for.
        for combo in itertools.product(*(values for _, values in axes)):
            rows.append(
                ({path: value for (path, _), value in zip(axes, combo, strict=True)}, False)
            )

    return [
        Condition(index=i, label=label_for(values, grid, is_baseline),
                  values=values, is_baseline=is_baseline)
        for i, (values, is_baseline) in enumerate(rows)
    ]

"""Sweep expansion. See docs/reference.md § Expansion modes.

Pure: a config dict in, an ordered condition list out. No filesystem, no
`Config` object, no git — expansion is a function of the declaration alone,
so it can be tested exhaustively without a repository.
"""

import itertools
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Condition:
    index: int
    label: str | None
    values: dict[str, Any] = field(default_factory=dict)
    is_baseline: bool = False


def label_for(values: dict[str, Any], grid: dict[str, Any], is_baseline: bool) -> str:
    if is_baseline:
        return "baseline"
    return "__".join(f"{path.rsplit('.', 1)[-1]}={value}" for path, value in values.items())


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

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
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from publishable.replication import Repeat, RepeatLevel
    from publishable.units import Unit


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


# The axis separator in a label. Kept as a module-level name — not inlined
# as a literal in `label_for` and `check_swept_value` — because both places
# that care about it must agree on what it is: the separator `label_for`
# joins axes with is exactly the substring `check_swept_value` refuses.
AXIS_SEPARATOR = "__"


def check_swept_value(value: Any) -> str | None:
    """None if `value` is safe to render into a condition label; otherwise why not.

    `docs/reference.md` § How artifacts are organized states two rules that
    cannot both hold for every value: a swept value must render as
    `SWEPT_VALUE_PATTERN` (which admits `_`), and axes in a label are joined
    by `__`. A rendered value containing `__` — e.g. `a__b` — passes the
    pattern but destroys the separator: `one=a__b__two=c` splits into three
    axes instead of two. Since a label is also a selector (a hypothesis's
    `compare.condition`, a contrast's `of`/`against`, and a `report` filter
    all name conditions by parsing the label's body back into axes), this
    resolves the conflict by refusing the value rather than the character —
    `_` alone stays legal.

    Task 4's `validate` is where this predicate is meant to be called from,
    once `_check_sweep` exists: this is the shape of the check it should run
    per swept value, on top of (not instead of) the existing pattern check.
    """
    rendered = render_value(value)
    if not re.match(SWEPT_VALUE_PATTERN, rendered):
        return f"swept value {rendered!r} does not match {SWEPT_VALUE_PATTERN}"
    if AXIS_SEPARATOR in rendered:
        return (
            f"swept value {rendered!r} contains {AXIS_SEPARATOR!r}, the separator "
            "between axes in a condition label; a label is also a selector, so a "
            "value containing the separator would produce a label that cannot be "
            "parsed back into axes"
        )
    return None


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
    return AXIS_SEPARATOR.join(
        f"{keys.get(path, path.rsplit('.', 1)[-1])}={render_value(value)}"
        for path, value in values.items()
    )


def condition_dir_name(index: int, label: str) -> str:
    """The `<nn>_<label>` name a condition nests under, in `run_dir/conditions/`.

    Single source of truth for the format: `runner.step_dir_for` and
    `artifacts.StepIO.read_condition` both nest here, and a second implementation
    of this string is how they drift apart.
    """
    return f"{index:02d}_{label}"


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


def sweep_document(
    conditions: list[Condition],
    levels: list["RepeatLevel"],
    repeats: list["Repeat"],
    digest: str,
    order: str,
    execution_order: list[tuple[int, str]],
    order_seed: int | None = None,
    partitions: list[list["Unit"]] | None = None,
) -> dict[str, Any]:
    """The `sweep.yaml` payload: the resolved plan, as plain YAML-safe data.

    Matches `docs/reference.md` § "`sweep.yaml` — the resolved plan" exactly.
    `order` and `execution_order` are two different things and stay two
    parameters: `order` is the scalar *mode* (`as_declared` | `randomized`) —
    the rule — while `execution_order` is the realized sequence of
    `(condition index, repeat label)` pairs actually run — the fact. The mode
    is derivable from the config; what happened is not, which is why both are
    recorded rather than one re-deriving the other.

    `order_seed` is the seed `order: randomized`'s shuffle used, and is
    written only when given — its absence under `as_declared` says nothing
    was shuffled, not that the seed was lost.

    `levels` and `repeats` are the same design at two grains and both are
    needed. `levels` is the declared structure — one entry per level, outer to
    inner — and is what `repeats:` records, because the nesting is exactly what
    a reader (and `resume`) must not have to recover by splitting label strings
    apart. `repeats` is that structure crossed into leaves, and supplies
    `labels:` alone.

    Each `repeats:` entry carries its kind plus exactly the fields
    `reference.md` § Repeat kinds gives that kind: a `seed` level its resolved
    `seeds`, whether they came from `auto` or were listed explicitly; a `batch`
    level its `n` and nothing else, because a batch has no parameter of its own.
    A level's `seeds` are its own members', never one per execution — under
    `batch` × `seed`, six leaves over two resolved seeds is the documented
    consequence of `batch01_seed42` and `batch02_seed42` drawing alike, and a
    flattened list of six would assert six streams that do not exist.

    `labels` stays the separate, top-level list of each leaf's composed label,
    outer to inner — under a `fold` × `seed` nesting this is where
    `fold03_seed42` appears.

    Fold membership (`partitions`) belongs here too per § The other files a
    run writes. `partitions` is `None` exactly when no `fold` level is
    declared, and the key is omitted rather than written as an empty list —
    an empty list would read as "no folds were drawn", a different claim from
    "this design has no folds". Each entry pairs a fold's label with the unit
    keys on each side: `test` is that fold's own partition, `train` every
    other partition concatenated in fold order — the same train/test split
    `io.units`/`io.units.train` hand a repeat-scope step for that label.
    """
    repeat_entries: list[dict[str, Any]] = []
    for lv in levels:
        if lv.kind == "batch":
            repeat_entries.append({"kind": lv.kind, "n": lv.n})
        else:
            repeat_entries.append({"kind": lv.kind, "seeds": [m.seed for m in lv.members]})

    doc: dict[str, Any] = {
        "design_digest": digest,
        "conditions": [
            {"index": c.index, "label": c.label, "values": dict(c.values),
             "is_baseline": c.is_baseline}
            for c in conditions
        ],
        "repeats": repeat_entries,
        "labels": [r.label for r in repeats],
        "order": order,
        "execution_order": [
            {"condition": index, "repeat": label} for index, label in execution_order
        ],
    }
    if order_seed is not None:
        doc["order_seed"] = order_seed
    if partitions is not None:
        fold = next((lv for lv in levels if lv.kind == "fold"), None)
        assert fold is not None, "partitions given but no `fold` level was declared"
        doc["partitions"] = [
            {
                "fold": member.label,
                "test": [u.key for u in part],
                "train": [u.key for other in partitions if other is not part for u in other],
            }
            for member, part in zip(fold.members, partitions, strict=True)
        ]
    return doc

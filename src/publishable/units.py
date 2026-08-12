# src/publishable/units.py
"""The thing being measured. See docs/reference.md § Units.

Resolution runs at `validate` as well as at `run`, so this module reads
`input_dir` directly rather than through `io` — at validate time there is no run
directory and no step for an `io` to belong to.
"""

import csv
import hashlib
import json
import random
import statistics
from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from publishable.errors import ContractError

RESERVED_FIELDS = ("key", "paths", "attributes")


class _FrozenAttributes(Mapping[str, Any]):
    """A read-only mapping that refuses a write with the documented code.

    `MappingProxyType` refuses too, but with a bare `TypeError` that carries no
    `.code` and is not a `PublishableError` — so `main` does not catch it and the
    user gets a traceback where every other refusal is a diagnostic. The document
    names `unit.attributes["scored"] = True` as the example, so this is the
    expression that has to produce `E-UNIT-IMMUTABLE`.
    """

    __slots__ = ("_data",)
    _data: dict[str, Any]

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_data", dict(data))

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return repr(self._data)

    def _refuse(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ContractError(
            "a unit's attributes are read-only: the roster is resolved once per run "
            "and shared across every condition, so writing here would change what "
            "the next condition measures",
            code="E-UNIT-IMMUTABLE",
        )

    __setitem__ = _refuse
    __delitem__ = _refuse
    pop = _refuse
    popitem = _refuse
    clear = _refuse
    update = _refuse
    setdefault = _refuse


@dataclass(frozen=True, eq=False)
class Unit:
    """Frozen, and hashable by `key`: one roster is resolved per run and shared."""

    key: str
    paths: tuple[str, ...] = ()
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # `object.__setattr__` rather than `self.attributes = …`, because the
        # refusal below is already in place by the time this runs.
        object.__setattr__(self, "attributes", _FrozenAttributes(self.attributes))

    def __getattr__(self, name: str) -> Any:
        # Only reached when normal lookup fails, so it never shadows the three fields.
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return object.__getattribute__(self, "attributes")[name]
        except KeyError:
            raise AttributeError(
                f"{name!r} is not a declared attribute of unit {self.key!r}"
            ) from None

    def __hash__(self) -> int:
        return hash(self.key)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Unit) and other.key == self.key


# Bound after the class rather than defined in its body: `@dataclass(frozen=True)`
# generates its own `__setattr__`/`__delattr__` and raises `TypeError: Cannot
# overwrite attribute ... in class Unit` if the name is already in `Unit.__dict__`
# at decoration time. Binding here, after the decorator has run, replaces the
# dataclass-generated version with the refusing one instead of colliding with it.
def _unit_setattr(self: Unit, name: str, value: Any) -> None:
    raise ContractError(
        f"a unit is immutable: cannot set {name!r}. The roster is resolved once "
        "per run and shared across every condition",
        code="E-UNIT-IMMUTABLE",
    )


def _unit_delattr(self: Unit, name: str) -> None:
    raise ContractError(
        f"a unit is immutable: cannot delete {name!r}. The roster is resolved "
        "once per run and shared across every condition",
        code="E-UNIT-IMMUTABLE",
    )


Unit.__setattr__ = _unit_setattr  # type: ignore[assignment]
Unit.__delattr__ = _unit_delattr  # type: ignore[assignment]


class UnitList:
    """Iterate, len, index — plus `.train`. Deliberately not a list.

    A sequence that also promised slicing, membership and `.index` would just be a
    `list`, and core could never change what backs it without breaking every step.
    """

    def __init__(self, units: list[Unit], train: "UnitList | None" = None) -> None:
        self._units = units
        self._train = train

    def __iter__(self) -> Iterator[Unit]:
        return iter(self._units)

    def __len__(self) -> int:
        return len(self._units)

    def __getitem__(self, index: int) -> Unit:
        if not isinstance(index, int) or isinstance(index, bool):
            raise ContractError(
                "`io.units` supports iteration, `len`, and integer indexing only; "
                f"{index!r} is not an integer index — filter with ordinary Python "
                "over the iteration instead, which costs nothing measurable at "
                "cohort scale",
                code="E-STEP-UNITS-CONTRACT",
            )
        return self._units[index]

    @property
    def train(self) -> "UnitList":
        if self._train is None:
            raise ContractError(
                "`io.units.train` needs a `fold` repeat or a `data.units.holdout`; "
                "neither is declared, and an empty list would let a fit run on nothing",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._train


def _rows_from_table(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _from_table(decl: dict[str, Any], input_dir: Path, source: str) -> list[Unit]:
    path = input_dir / source
    if not path.is_file():
        raise ContractError(
            f"`data.units.from` names {source}, which is not a file under {input_dir}",
            code="E-UNITS-SOURCE-MISSING",
        )
    rows = _rows_from_table(path)
    if not rows:
        raise ContractError(
            f"`data.units.from` names {source}, which has no data rows; "
            "a run measuring zero units has nothing to report",
            code="E-UNITS-EMPTY",
        )
    key_col = decl.get("key")
    attrs = list(decl.get("attributes") or [])
    columns = set(rows[0])
    if key_col not in columns:
        raise ContractError(
            f"`data.units.key` names {key_col!r}, which {source} does not have "
            f"(columns: {', '.join(sorted(columns))})",
            code="E-UNITS-KEY-MISSING",
        )
    for name in attrs:
        if name in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {name!r}, which is a field of `Unit` itself; "
                f"{', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        if name not in columns:
            raise ContractError(
                f"`data.units.attributes` names {name!r}, which {source} does not have",
                code="E-UNITS-ATTR-MISSING",
            )
    return [
        Unit(key=row[key_col], paths=(), attributes={a: row[a] for a in attrs})
        for row in rows
    ]


def _from_glob(decl: dict[str, Any], pattern: str, input_dir: Path) -> list[Unit]:
    # A glob yields a key and a path and nothing else, so every name under
    # `data.units.attributes` is one this source cannot supply — `reference.md`
    # § Validation's "Attributes have a source" row states this case with this
    # example. Ordered as `_from_table` orders it, reserved before unsourced, so
    # one declaration draws one code whichever source it sits under.
    for name in decl.get("attributes") or []:
        if name in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {name!r}, which is a field of `Unit` itself; "
                f"{', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        raise ContractError(
            f"`data.units.attributes` names {name!r}, which `from: {{glob: {pattern!r}}}` "
            "cannot supply — a glob yields a key and a path and nothing else. Declare a "
            "table or a resolver, or drop the attribute",
            code="E-UNITS-ATTR-MISSING",
        )
    # The loop above reports the first declared name and stops, which is
    # `_from_table`'s behavior for a name its table has no column for.
    # Lexicographic over relative paths: filesystems walk directories differently,
    # and a roster whose order depends on that is not reproducible.
    rels = sorted(
        p.relative_to(input_dir).as_posix()
        for p in input_dir.glob(pattern)
        if p.is_file()
    )
    if not rels:
        raise ContractError(
            f"`data.units.from.glob` {pattern!r} matched no files under {input_dir}; "
            "a run measuring zero units has nothing to report",
            code="E-UNITS-EMPTY",
        )
    return [Unit(key=rel, paths=(rel,), attributes={}) for rel in rels]


def resolve_units(units_decl: dict[str, Any], input_dir: Path) -> UnitList:
    """Resolve the roster, preserving the order it was resolved in."""
    source = units_decl.get("from")
    if isinstance(source, str):
        units = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units = _from_glob(units_decl, str(source["glob"]), input_dir)
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name or {{glob: ...}}",
            code="E-UNITS-SOURCE-MISSING",
        )
    seen: dict[str, int] = {}
    for u in units:
        if u.key in seen:
            raise ContractError(
                f"`data.units.key` is not unique: {u.key!r} appears more than once",
                code="E-UNITS-KEY-DUPLICATE",
            )
        seen[u.key] = 1
    return UnitList(units)


COLLAPSE_RULES = ("mean", "median", "sum", "first", "mode")

# `reference.md` § What isn't a repeat: "`collapse` is `mean`, `median`, or `sum`
# for numeric columns and `first` or `mode` for the rest." Exported so task 2's
# validate-time check — which numeric-only rule was named over a non-numeric
# column — reads the same set rather than re-deriving it, which is how the two
# would come to disagree.
NUMERIC_COLLAPSE_RULES = ("mean", "median", "sum")


def _rule_for(column: str, collapse: Any) -> str:
    """One rule for every column, or a per-column map falling back to `first`.

    A column the config did not name is one the design did not ask to average,
    so the fallback carries the first value rather than guessing at a statistic.
    """
    if isinstance(collapse, Mapping):
        return str(collapse.get(column, "first"))
    return str(collapse)


def _apply(rule: str, values: list[Any]) -> Any:
    if rule not in COLLAPSE_RULES:
        raise ContractError(
            f"`data.units.measurements.collapse` names {rule!r}; expected one of "
            f"{', '.join(COLLAPSE_RULES)}",
            code="E-UNITS-COLLAPSE-RULE",
        )
    # `reference.md` § What isn't a repeat: "Attributes constant within a key
    # collapse to that value with no rule needed." Checked after the rule-name
    # validation above (a bogus rule still raises even over a single-member
    # group), because the shortcut's job is narrower than "all values equal":
    # it is what lets a *non-numeric* rule succeed over values it cannot
    # actually operate on (`mean` over a constant `site` string), not a
    # general-purpose no-op. Gated to exclude a numeric rule over genuinely
    # numeric values — `sum([5, 5])` must still be `10`, not `5` — because a
    # numeric rule meeting numeric values is the user asking for an
    # aggregation and is entitled to get one, even where the answer happens
    # to equal the input. `bool` is excluded from "numeric" explicitly:
    # `isinstance(True, int)` is `True` in Python, and summing booleans is a
    # different intent than summing depths.
    numeric_values = all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in values
    )
    if all(v == values[0] for v in values) and not (
        rule in NUMERIC_COLLAPSE_RULES and numeric_values
    ):
        return values[0]
    if rule == "first":
        return values[0]
    if rule == "mode":
        # `Counter.most_common` breaks a count-tie by insertion order on
        # Python 3.7+, which is what pins the documented "by whichever tied
        # value appeared first" — a property of `dict` iteration order the
        # standard library commits to, not an accident of this call.
        return Counter(values).most_common(1)[0][0]
    if rule == "median":
        return statistics.median(values)
    if rule == "sum":
        return sum(values)
    return sum(values) / len(values)  # rule == "mean"


def collapse_measurements(
    units: list[Unit], by: str, collapse: Any
) -> tuple[list[Unit], list[int]]:
    """Collapse rows sharing a `key` into one unit, in first-seen order.

    `reference.md` § What isn't a repeat: rows sharing a key are technical
    replicates, collapsed at resolution, before any step sees them — which is
    what keeps them out of `n`. The measurement axis `by` is consumed: it
    distinguished the rows and has no value once they are one unit.

    Returns the collapsed units and their measurement counts in the same order,
    because `technical_n` is `{min, max, median}` over exactly these counts and
    recomputing them from a second walk is how the two come to disagree.

    Each group's member list is built by appending in `units`' own iteration
    order, so it *is* resolution order — which is what makes `_apply`'s `first`
    branch (`values[0]`) match the documented "earliest row in resolution
    order" rather than an incidental artifact of `dict` grouping.
    """
    groups: dict[str, list[Unit]] = {}
    for unit in units:
        groups.setdefault(unit.key, []).append(unit)
    collapsed: list[Unit] = []
    counts: list[int] = []
    for key, members in groups.items():
        names: list[str] = []
        for member in members:
            for name in member.attributes:
                if name != by and name not in names:
                    names.append(name)
        merged = {
            name: _apply(
                _rule_for(name, collapse),
                [m.attributes[name] for m in members if name in m.attributes],
            )
            for name in names
        }
        paths = tuple(p for m in members for p in m.paths)
        collapsed.append(Unit(key=key, paths=paths, attributes=merged))
        counts.append(len(members))
    return collapsed, counts


def partition_units(roster: UnitList, k: int, digest: str) -> list[list[Unit]]:
    """Split the roster into `k` test partitions, each unit in exactly one.

    Drawn from the design digest rather than `parameters_hash`: editing an
    unrelated parameter must not redraw every fold boundary (reference.md
    § What auto-derives from). Sizes differ by at most one, so no fold is
    systematically smaller than its neighbours.
    """
    units = list(roster)
    rng = random.Random(_seed_from(digest))
    shuffled = list(units)
    rng.shuffle(shuffled)
    return [shuffled[i::k] for i in range(k)]


def _seed_from(digest: str) -> int:
    return int.from_bytes(hashlib.sha256(f"{digest}|folds".encode()).digest()[:4], "big")


def units_hash(units: UnitList) -> str:
    """Covers the list in resolved order — two runs that resolved the same units in a
    different sequence did not allocate the same trial."""
    payload = json.dumps(
        [
            {"key": u.key, "paths": list(u.paths), "attributes": dict(u.attributes)}
            for u in units
        ],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()

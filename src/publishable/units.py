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


def _from_glob(pattern: str, input_dir: Path) -> list[Unit]:
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
        units = _from_glob(str(source["glob"]), input_dir)
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

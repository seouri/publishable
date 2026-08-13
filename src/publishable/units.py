# src/publishable/units.py
"""The thing being measured. See docs/reference.md § Units.

Resolution runs at `validate` as well as at `run`, so this module reads
`input_dir` directly rather than through `io` — at validate time there is no run
directory and no step for an `io` to belong to.
"""

import csv
import hashlib
import json
import math
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


def _from_table(
    decl: dict[str, Any], input_dir: Path, source: str
) -> tuple[list[Unit], frozenset[str]]:
    """The units a table yields, and the column names it has.

    The columns are returned rather than kept private because they are the only
    honest reference set for `data.units.measurements.by`: `design-principles.md`
    § Core vs. plugin lists `key`, `attributes`, `cluster_by`, `measurements.by`,
    `holdout.from`, `assign.from`, `stratify_by` and `null_test.shuffle` as
    *parallel* namers of input fields, so `by` names a column in
    its own right and is not a member of `attributes` — the fence in
    `reference.md` § What isn't a repeat declares no `attributes` at all. Reading
    the header a second time somewhere else is how the two would come to disagree.
    """
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
    ], frozenset(columns)


def _from_glob(
    decl: dict[str, Any], pattern: str, input_dir: Path
) -> tuple[list[Unit], frozenset[str]]:
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
    # An empty column set, not a missing one: a glob yields a key and a path and
    # nothing else, so there is no name `measurements.by` could correctly hold.
    return [Unit(key=rel, paths=(rel,), attributes={}) for rel in rels], frozenset()


def resolve_units(
    units_decl: dict[str, Any], input_dir: Path
) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]:
    """Resolve the roster, preserving the order it was resolved in.

    Returns the roster, `technical_n` — `None` unless `data.units.measurements` is
    declared — and the source's own column names, empty under a `{glob: ...}`
    source. Both travel *beside* the roster rather than on it because `io.units`
    **is** a `UnitList` handed to steps, and `reference.md` § The unit list is
    three operations promises exactly iteration, `len`, and integer indexing, plus
    `.train`. A fourth operation would be a fourth thing every future backing has
    to provide.

    The columns are for `validate._check_measurements`, which checks
    `measurements.by` against the columns the source actually has. They are
    threaded from the one read `_from_table` already does rather than re-read
    there, so the two cannot come to disagree about what the table holds.
    """
    source = units_decl.get("from")
    if isinstance(source, str):
        units, columns = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units, columns = _from_glob(units_decl, str(source["glob"]), input_dir)
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name or {{glob: ...}}",
            code="E-UNITS-SOURCE-MISSING",
        )
    # Before the uniqueness loop, not after: under a `measurements` declaration a
    # repeated key is the point — rows sharing one are technical replicates of the
    # same unit — and after the collapse there is one row per key again, so the
    # check below still means what it always did for every other design.
    technical_n: dict[str, float] | None = None
    measurements = units_decl.get("measurements")
    if measurements:
        by = _measurement_axis(measurements)
        units, counts = collapse_measurements(
            units, by, measurements.get("collapse", "first")
        )
        # `{min, max, median}` rather than a scalar, per `reference.md` § What
        # isn't a repeat: real files are uneven, and a bare `technical_n: 3`
        # would be a claim of balance nobody checked. Not a shape waiting to be
        # simplified — a unit measured once and a unit measured five times
        # contribute equally to `n` after collapsing, and this is what makes
        # that visible.
        technical_n = {
            "min": min(counts),
            "max": max(counts),
            "median": statistics.median(counts),
        }
    seen: dict[str, int] = {}
    for u in units:
        if u.key in seen:
            raise ContractError(
                f"`data.units.key` is not unique: {u.key!r} appears more than once",
                code="E-UNITS-KEY-DUPLICATE",
            )
        seen[u.key] = 1
    return UnitList(units), technical_n, columns


def _measurement_axis(measurements: Any) -> str:
    """`measurements.by`, or the same code `validate` reports for its absence.

    `validate._check_units` resolves the roster *before* `_check_measurements`
    runs, so a malformed block reaches this function first — and `validate`
    collects findings rather than raising, so a `KeyError` on a missing `by` or an
    `AttributeError` on `measurements: yes` would escape `validate` itself.
    `E-DATA-MEASUREMENTS-INVALID` is what `_check_measurements` reports for both
    shapes, so one problem carries one code whichever surface reached it first.
    """
    by = measurements.get("by") if isinstance(measurements, Mapping) else None
    if not isinstance(by, str) or not by:
        raise ContractError(
            f"`data.units.measurements` is {measurements!r}; it needs `by`, the "
            "attribute distinguishing one measurement of a unit from another. "
            "Without it nothing distinguishes a second measurement of one unit "
            "from a resumed retry of the same one",
            code="E-DATA-MEASUREMENTS-INVALID",
        )
    return by


COLLAPSE_RULES = ("mean", "median", "sum", "first", "mode")

# `reference.md` § What isn't a repeat: "`collapse` is `mean`, `median`, or `sum`
# for numeric columns and `first` or `mode` for the rest." Exported so task 2's
# validate-time check — which numeric-only rule was named over a non-numeric
# column — reads the same set rather than re-deriving it, which is how the two
# would come to disagree.
NUMERIC_COLLAPSE_RULES = ("mean", "median", "sum")


def rule_for(column: str, collapse: Any) -> str:
    """One rule for every column, or a per-column map falling back to `first`.

    A column the config did not name is one the design did not ask to average,
    so the fallback carries the first value rather than guessing at a statistic.
    """
    if isinstance(collapse, Mapping):
        return str(collapse.get(column, "first"))
    return str(collapse)


def is_measurement_numeric(value: Any) -> bool:
    """Whether `value` may stand under a numeric collapse rule (`mean`, `median`, `sum`).

    **The single authority** for that question, and it now has both its readers:
    `validate`'s row-243 collapse-type check, and `coerce_for_rule` below, which
    `collapse_measurements` calls immediately before `apply_rule`. Two different ideas
    of "numeric" for the same declaration is exactly the failure this predicate
    exists to prevent — a config that validates clean and then crashes on a value
    `validate` already approved.

    `bool` is excluded even though `isinstance(True, int)` is `True` in Python —
    `sum([True, False])` and `sum([True, True])` would answer in two different
    types depending on the data, which is incoherent whichever way it's read. A
    `str` that parses as `float` is accepted: a table-sourced column arrives
    through `csv.DictReader` as `str` regardless of what it holds, so refusing
    every table column outright would refuse `collapse: mean` over the ordinary
    numeric case wherever it appears, not just over the `site`-shaped column
    row 243 exists to catch.

    **`apply_rule`'s own constant-column shortcut, below, does NOT read this
    predicate**, and that stays deliberate: its narrower, isinstance-only gate is
    the right one for a value that is already a real number rather than one that
    merely looks like it. What closes the gap is `coerce_for_rule` running first,
    so under a numeric rule `apply_rule` only ever sees a value already converted.
    Two constraints that arrangement carries, both load-bearing:

    - Coercion happens *before* `apply_rule`, never inside it. The other way round,
      `apply_rule("mean", ["10", "10"])` returns the *string* `"10"` — the constant
      shortcut fires because `"10"` fails `apply_rule`'s own isinstance gate, not this
      one — so a numeric rule over a constant numeric column would hand back a
      string no matter what this predicate said about it.
    - `coerce_for_rule` must accept *exactly* `float`'s grammar — no more, no
      less — or this predicate's "numeric-looking" and the coercion's
      "successfully converted" part ways, which is the same divergence this
      predicate exists to close, one layer down.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
        except ValueError:
            return False
        return True
    return False


def usable_weight(value: Any) -> float | None:
    """`value` as a weight core could multiply by, or `None` if it is not one.

    **The single authority** for that question, and it sits here beside
    `is_measurement_numeric` for the same reason that one does: it now has two
    readers in different modules — `validate`'s `data.units.weight_by` check
    (`reference.md` § Validation, rows "Weights are usable" and "Weighting looks
    undeclared") and `stats.weighted_t_over_units`. A weighted mean built on a
    different notion of a usable weight than the one `validate` approves the
    config against is the validate-clean-then-crash gap in its exact original
    shape: a config core accepts whose weights core then cannot use.

    `is_measurement_numeric` is the numeric gate rather than a bare
    `isinstance(value, (int, float))`, and that is load-bearing rather than
    stylistic: `_from_table` builds every attribute from `csv.DictReader`, which
    yields `str` for every column whatever it holds, so an isinstance test would
    refuse every table-sourced weight there is — the exact shape `reference.md`
    § Weighted samples prints — and would make the undeclared-weight warning
    unreachable in the same stroke.

    Finiteness is checked on top of positivity because `float("nan")` parses and
    `nan <= 0` is `False`, so a positivity test alone admits a value that turns
    every weighted mean it touches into `nan`.
    """
    if not is_measurement_numeric(value):
        return None
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def coerce_for_rule(column: str, rule: str, values: list[Any]) -> list[Any]:
    """Numbers for a numeric rule, or the values exactly as they arrived.

    A table-sourced column arrives through `csv.DictReader` as `str` whatever it
    holds, so without this step `collapse: mean` over a column `validate` accepted
    — `is_measurement_numeric("10")` is `True` — either returns a string (`apply_rule`'s
    constant-column shortcut) or raises a bare `TypeError` (`sum` over strings).
    Both are the same defect: a config that validates clean and then misbehaves on
    a value `validate` already approved.

    `is_measurement_numeric` is the gate, and `float` is the conversion, precisely
    because the predicate accepts exactly what `float` accepts — an int-first
    coercion, or a stricter parse, would part ways with the predicate and reopen
    the divergence it exists to close. The visible consequence is that an
    integer-looking column collapses to `15.0` rather than `15`; narrowing that
    back to `int` is the tidy-up that would break the correspondence.

    The constant-value case is handed on untouched so `apply_rule`'s own shortcut
    still answers it — `reference.md` § What isn't a repeat: "Attributes constant
    within a key collapse to that value with no rule needed." Everything else a
    numeric rule cannot operate on is refused here, carrying the identifier
    `validate`'s own collapse-type check reports, rather than reaching arithmetic
    that would raise a bare `TypeError` — which, since `validate` resolves the
    roster inside an `except ContractError`, would escape `validate` itself.
    """
    if rule not in NUMERIC_COLLAPSE_RULES:
        return values
    if all(is_measurement_numeric(v) for v in values):
        return [float(v) for v in values]
    if values and all(v == values[0] for v in values):
        return values
    offender = next(v for v in values if not is_measurement_numeric(v))
    raise ContractError(
        f"`data.units.measurements.collapse` is {rule!r} over {column!r}, which holds "
        f"{offender!r} — a {type(offender).__name__} that is not numeric and does not "
        "parse as one. Use `first` or `mode` for it, or a per-column map giving each "
        "column the rule that fits it",
        code="E-DATA-MEASUREMENTS-COLLAPSE-TYPE",
    )


def apply_rule(rule: str, values: list[Any]) -> Any:
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
    order, so it *is* resolution order — which is what makes `apply_rule`'s `first`
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
        merged: dict[str, Any] = {}
        for name in names:
            rule = rule_for(name, collapse)
            # Never empty: `names` is built from the members' own attribute keys,
            # so every name here is one at least one member carries — which is
            # what keeps `apply_rule`'s `values[0]` in reach of a value.
            values = [m.attributes[name] for m in members if name in m.attributes]
            merged[name] = apply_rule(rule, coerce_for_rule(name, rule, values))
        paths = tuple(p for m in members for p in m.paths)
        collapsed.append(Unit(key=key, paths=paths, attributes=merged))
        counts.append(len(members))
    return collapsed, counts


def clusters_of(roster: UnitList, cluster_by: str) -> dict[str, str]:
    """Which cluster each unit belongs to, keyed by unit key, in roster order.

    **The single authority** for cluster membership, and it sits beside
    `usable_weight` and `is_measurement_numeric` for the reason those two do: the
    partition, the interval constructions and `validate` all have to ask the same
    question of the same declaration, and a second notion of "which units form one
    cluster" is the validate-clean-then-disagree gap in a new shape — here it would
    mean a config `validate` approved whose folds split a cluster the checks were
    told was whole.

    `cluster_by` names a **declared attribute**, not a source column — the same
    side of that line `weight_by` falls on and the opposite side from
    `measurements.by`. `reference.md` § Validation's *Cluster attribute exists* row
    says the name is one "which is not a unit attribute", and `design-principles.md`
    § Core vs. plugin lists `cluster_by` among the declarations that "all name
    attributes". That is what makes it readable here at all: `_from_table`
    populates `Unit.attributes` from `data.units.attributes` and nothing else, so a
    column outside that list has not survived resolution.

    Insertion order **is** roster order, deliberately. A caller needing the ordered
    list of clusters — the partitioner does — derives it from this mapping rather
    than walking the roster a second time, which is how the two would come to
    disagree about which cluster came first, and `units_hash` already pins that the
    resolved order is the reproducible one.

    Values are stringified so the mapping has one type whatever the source
    supplied: a table yields `str` for every column, but a hand-built roster or a
    future resolver need not, and a cluster id is a label rather than a quantity —
    nothing downstream does arithmetic on it.

    A unit carrying no value for the attribute raises rather than being placed in a
    cluster of its own. `reference.md` § Errors validate reports states this under
    `E-DATA-CLUSTER-UNKNOWN`, the same code `validate` reports for a `cluster_by`
    naming no declared attribute: an invented singleton cluster would silently make
    a unit its own inferential draw, widening nothing and narrowing every interval
    that counts clusters.
    """
    membership: dict[str, str] = {}
    for unit in roster:
        if cluster_by not in unit.attributes:
            raise ContractError(
                f"`data.units.cluster_by` names {cluster_by!r}, which unit "
                f"{unit.key!r} carries no value for — a cluster is what a unit is "
                "not independent of, so a unit with no cluster has no place on "
                "either side of a split. Declare it in `data.units.attributes` and "
                "give every unit a value for it",
                code="E-DATA-CLUSTER-UNKNOWN",
            )
        membership[unit.key] = str(unit.attributes[cluster_by])
    return membership


def cluster_count(roster: UnitList, cluster_by: str) -> int:
    """How many distinct clusters the roster holds.

    Derived from `clusters_of` rather than counted in its own walk: the count is
    what bounds `k` and what a cluster-robust interval's df is computed from, and a
    count that disagreed with the membership it is supposed to summarize would put
    a `k` past the number of groups the partitioner can actually produce.
    """
    return len(set(clusters_of(roster, cluster_by).values()))


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

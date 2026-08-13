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
        # The two declarations whose column is a fact about the unit rather than
        # about the measurement, read straight off the declaration this function
        # already holds — no new plumbing, and no second place that could come to
        # disagree with `units_decl` about which column is the cluster. The
        # `isinstance` filter is load-bearing rather than defensive: a list-valued
        # `cluster_by` is `E-CONFIG-TYPE`'s finding, and using one as a mapping key
        # is a `TypeError` escaping `validate`, which never raises.
        # **A registry key must be a flat, string-valued key of `data.units`.**
        # This indexes `units_decl` by the key itself, so it reaches `cluster_by`
        # and `weight_by` and nothing nested. `assign.<axis>.from` and
        # `holdout.from` are the next two columns that will want this rule and
        # **neither is reachable this way** — adding either name to the registry
        # no-ops silently, and so does spelling it as a dotted path. Verified by
        # probe, not assumed. Whichever slice needs one owes an accessor here;
        # the failure it would otherwise ship is the leak this check exists to
        # close, arriving through a sibling declaration.
        constant = {
            declaration: units_decl[declaration]
            for declaration in CONSTANT_COLUMN_RULES
            if isinstance(units_decl.get(declaration), str) and units_decl[declaration]
        }
        units, counts = collapse_measurements(
            units, by, measurements.get("collapse", "first"), constant
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


CONSTANT_COLUMN_RULES: dict[str, tuple[str, str]] = {
    "cluster_by": (
        "E-DATA-CLUSTER-VARIES",
        "A cluster is what a unit is not independent of, so it decides which side "
        "of a train/test split the unit lands on — a unit filed under the wrong "
        "one is a unit whose real cluster is on both sides. A cluster is a fact "
        "about the unit, not about the measurement",
    ),
    "weight_by": (
        "E-DATA-WEIGHT-VARIES",
        "A weight is what one unit stands for, so collapsing disagreeing rows "
        "gives that unit a weight no row declared — their sum under `sum`, or "
        "whichever arrived first under the default rule. A weight is a fact "
        "about the unit, not about the measurement",
    ),
}
"""The declarations whose column may not vary within a unit's measurement rows.

**Two codes, not one**, deliberately: `reference.md` § Clustered units and
§ Weighted samples state the same rule about two different columns, and they say
different things about what breaks — a mis-collapsed weight mis-sizes what one
unit stands for, while a mis-collapsed cluster decides which side of a split that
unit lands on. One identifier for both would send the reader to the section that
does not describe the damage.

Keyed by the *declaration* rather than by the column, so a config naming one
column in both places is checked once for each rather than silently dropping one
under a precedence rule nothing in the documents states.
"""


def collapse_measurements(
    units: list[Unit], by: str, collapse: Any, constant: Mapping[str, str] | None = None
) -> tuple[list[Unit], list[int]]:
    """Collapse rows sharing a `key` into one unit, in first-seen order.

    `constant` maps a declaration in `CONSTANT_COLUMN_RULES` to the column it
    names, and those columns are refused where they vary within one unit's rows
    rather than being collapsed like any other attribute. **`validate` cannot host
    that check**: `resolve_units` collapses internally, so a validate-time check
    sees the post-collapse roster and the disagreeing values are already gone.
    This function groups the rows by key and is the one place holding them.

    Nothing else needs a second constancy check: this is the only path that merges
    rows into a unit, so under no `measurements` declaration there is one row per
    unit and no column can disagree with itself.

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
        # Before the merge loop below, and over the members directly rather than
        # over its column list: `names` excludes `by`, so a `cluster_by` naming
        # the measurement axis itself — which varies within every unit by
        # construction — would otherwise be reached by no check at all. Running
        # first is also what makes this code win over
        # `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` for a varying string column under a
        # numeric rule: both faults are real, and the one worth reporting is the
        # unit filed under two clusters, not the rule name that would still leave
        # the leak in place once it was fixed.
        for declaration, column in (constant or {}).items():
            values = [m.attributes[column] for m in members if column in m.attributes]
            # A name only some members carry is not a disagreement: the rows that
            # carry it agree, so nothing about the collapsed value depends on the
            # order the file happens to be in. Whether every unit ends up with a
            # value at all is the presence question `clusters_of` raises on, after
            # resolution — and `validate` collects findings rather than raising, so
            # being total here over a sparse column is what keeps this off its
            # escape path.
            if any(v != values[0] for v in values):
                code, why = CONSTANT_COLUMN_RULES[declaration]
                seen_values = list(dict.fromkeys(str(v) for v in values))
                raise ContractError(
                    f"`data.units.{declaration}` names {column!r}, which unit "
                    f"{key!r} declares more than one value for across its "
                    f"measurement rows ({', '.join(seen_values)}) — so which one "
                    "survives the collapse is decided by the order the rows "
                    f"happen to be in. {why}",
                    code=code,
                )
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


def fold_basis(roster: UnitList, cluster_by: str | None) -> int:
    """How many indivisible things a `fold` level can distribute — the number `k`
    is bounded by, and the number `{kind: fold, k: all}` resolves to.

    **One number, not two.** A fold asks "how many things can be left out", which
    is the unit count when the units are independent draws and the cluster count
    when `data.units.cluster_by` says they are not: a cluster is the smallest thing
    `partition_units` can move, so a `k` past the cluster count leaves a fold with
    no cluster to test, and leave-one-out becomes leave-one-*cluster*-out
    (`reference.md` § Validation, rows *Folds fit inside the clusters* and
    *Leave-one-out is affordable*). Every caller resolves the basis here rather
    than deciding for itself, and passes the one number on — a `k` checked against
    the unit count while the partition is drawn over clusters is exactly the
    disagreement this single derivation exists to prevent.

    `cluster_count` is the authority for the clustered half, so an unreadable
    cluster — a unit carrying no value for the attribute — raises
    `E-DATA-CLUSTER-UNKNOWN` from there rather than being counted as a cluster of
    its own. `validate` collects rather than raises, so its caller catches that and
    treats the basis as unresolved.
    """
    return cluster_count(roster, cluster_by) if cluster_by else len(roster)


def stratum_varies_within_cluster(
    roster: UnitList, cluster_by: str, stratify_by: str
) -> tuple[str, list[str]] | None:
    """The first cluster whose units disagree about the stratum attribute, with the
    values it carries — or `None` when every cluster agrees.

    **A stratum must be constant within a cluster** (`reference.md` § Clustered
    units): balancing a stratum across a split means dealing its values out to
    different sides, and a cluster that carries two of them cannot be dealt out at
    all, being indivisible. Rather than silently prioritizing one of the two
    constraints, core refuses the pair — so this reports the pair, and the caller
    decides which declaration to name (`reference.md` § Validation, rows *Fold
    strata survive clustering* and *Holdout strata survive clustering*, which is why
    this returns a fault rather than raising one code).

    Membership comes from `clusters_of`, the single authority, so a unit carrying no
    cluster value raises `E-DATA-CLUSTER-UNKNOWN` from there rather than being
    grouped into a cluster of its own — which would make its stratum trivially
    constant and hide exactly the variation this looks for.

    A unit carrying no value for the *stratum* is one the partitioner has nothing to
    balance on, so within a cluster whose other units declare one it counts as a
    variation like any other, rendered `no value` among the values reported. Units
    that all carry none agree, and a stratum no unit carries at all is the caller's
    own name check to report — an attribute the design never declared.

    The first offender is in roster order, one finding being enough to fix and the
    order already being part of the roster's identity.
    """
    membership = clusters_of(roster, cluster_by)
    seen: dict[str, set[str]] = {}
    order: list[str] = []
    for unit in roster:
        cluster = membership[unit.key]
        if cluster not in seen:
            seen[cluster] = set()
            order.append(cluster)
        value = unit.attributes.get(stratify_by)
        seen[cluster].add("no value" if value is None else str(value))
    for cluster in order:
        if len(seen[cluster]) > 1:
            return cluster, sorted(seen[cluster])
    return None


def _assign_whole_clusters(
    units: list[Unit], k: int, rng: random.Random, clusters: dict[str, str] | None
) -> list[list[Unit]]:
    """One list of units into `k` folds, balanced by unit count, no cluster divided.

    The single assignment rule, drawn from `rng` in the order it is called: the whole
    roster reaches it once when nothing is stratified, and each stratum's units reach
    it once when something is. A second rule for the stratified case would be a
    second answer to "which units land together", which is the disagreement
    `clusters_of` exists to prevent one level up.

    **`clusters is None` is a cluster of one per unit, not another path.** That is an
    identity rather than an approximation: `random.shuffle` permutes by index and
    reads only the length, so shuffling the one-name-per-unit list draws the same
    permutation as shuffling the units did; the descending-size sort is stable and
    every size is 1, so it is the identity; and least-loaded assignment of size-1
    items deals them out round-robin, which is `shuffled[i::k]` term for term. The
    unclustered draw is therefore the same draw it was before clusters existed, and
    `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` is its oracle.

    Keying by `unit.key` is what that rests on, and unit keys are unique — a repeated
    one is refused at resolution as `E-UNITS-KEY-DUPLICATE`, so no two units can
    collapse into one accidental cluster here.
    """
    if clusters is None:
        clusters = {unit.key: unit.key for unit in units}
    # `clusters[...]`, not `.get`: `clusters_of` is total over the roster it was
    # given and raises `E-DATA-CLUSTER-UNKNOWN` for a unit carrying no cluster, so
    # a key missing here means the caller passed a mapping from a different roster
    # — a core defect. A `.get` default would place that unit in an invented
    # cluster of its own, which is the silent version of exactly the leak this
    # function exists to prevent.
    members: dict[str, list[Unit]] = {}
    for unit in units:
        members.setdefault(clusters[unit.key], []).append(unit)
    order = list(members)
    rng.shuffle(order)
    order.sort(key=lambda name: -len(members[name]))
    folds: list[list[Unit]] = [[] for _ in range(k)]
    for name in order:
        folds[min(range(k), key=lambda i: len(folds[i]))].extend(members[name])
    return folds


def partition_units(
    roster: UnitList,
    k: int,
    digest: str,
    clusters: dict[str, str] | None = None,
    strata: dict[str, str] | None = None,
) -> list[list[Unit]]:
    """Split the roster into `k` test partitions, each unit in exactly one.

    Drawn from the design digest rather than `parameters_hash`: editing an
    unrelated parameter must not redraw every fold boundary (reference.md
    § What auto-derives from).

    `clusters` is `clusters_of`'s mapping — **the single authority** on which units
    form one cluster, never a second notion derived here. With it, whole clusters
    go to one side of a split and a cluster is never divided between train and
    test. `reference.md` § Clustered units says why that is correctness rather than
    refinement: 300 cells from 10 animals split without regard to `animal_id` train
    on other cells of the animal they test on, and the metric is inflated *before*
    any interval is computed — a cluster-robust standard error cannot repair a
    number that was already leaked into.

    Sizes differ by at most one when `clusters` is `None`. When it is not, they are
    **as even as indivisible clusters allow** — the unit count is what balances,
    but a cluster is the smallest thing that can move, so one large cluster sets a
    floor no assignment can get under. Saying the stronger thing here would be
    claiming a guarantee the code does not provide.

    The order is part of the contract. The clusters are shuffled with the
    digest-seeded RNG and then sorted **largest first**, each going to the
    currently-smallest fold. Both halves are load-bearing: the shuffle is what
    keeps the draw a function of the design digest and what breaks ties among
    equal-sized clusters (the only place it can still matter once the sort is
    stable), while smallest-first assignment over the same clusters strands the
    large ones and gives a visibly worse split. `list.sort` is stable, so the
    shuffle survives inside each size.

    A `k` past the number of clusters leaves the surplus folds **empty** rather
    than dividing a cluster to fill them — an empty fold is a visibly useless
    split, a divided one is a leaky split that looks fine. `validate` refuses that
    `k` against the cluster count; this stays total for the case where it did not.

    `strata` is the same shape — unit key to stratum value — and is what makes a
    `fold` level's `stratify_by` change the split rather than only being checked
    (`reference.md` § Repeat kinds calls a fold "stratified" when it is declared).
    Each stratum is partitioned **on its own**, by the rule above, and the per-stratum
    folds are merged **index-wise**: fold `i` is every stratum's fold `i`. So each
    fold holds close to the roster's mix of the stratum, which is the whole point of
    declaring one, and no second balancer is introduced — one greedy objective (unit
    count) still runs, just once per stratum.

    **That composition is sound only while `stratum_varies_within_cluster` refuses
    the pair it refuses.** Balancing unit count and balancing stratum proportions are
    independent objectives, and two greedy passes over the same clusters would fight;
    what dissolves the conflict is that a cluster carries exactly one stratum value,
    so a cluster belongs to exactly one stratum and each per-stratum partition sees
    whole clusters. A later change that let a cluster straddle two strata would have
    to answer which stratum's partition owns it, and would silently divide it here.
    `reference.md` § Validation's *Fold strata survive clustering* row is the check;
    if it goes, this does.

    **With `strata`, fold sizes can differ by more than one.** When the things being
    dealt out inside a stratum are all the same size — every unclustered roster, each
    unit its own cluster of one — each stratum's fold list comes out non-increasing
    and fold 0 collects every stratum's ceiling: three strata of three units at
    `k = 2` give 6 and 3, not 5 and 4, so the spread is bounded by the number of
    strata. With clusters of unequal size no such bound holds, because the
    at-most-one-cluster floor above applies **per stratum** and the floors add: two
    strata of clusters 7+3 and 3+1+1 at `k = 2` give 10 and 5. Balancing the count
    *across* strata is what would divide a stratum's share unevenly, which is the
    thing being declared away, so this is the prescribed rule's consequence rather
    than a defect — stated here because it contradicts the at-most-one above, which
    holds for an unstratified split only.

    **`k` is checked against the whole roster's basis, not against each stratum's.**
    A `k` past some stratum's cluster count leaves that stratum contributing to fewer
    than `k` folds, so a fold can hold none of it while `validate` saw a `k` well
    inside `fold_basis` — a fold whose stratum mix is nothing like the roster's. The
    partition stays total and says so rather than dividing a cluster or dropping the
    stratification; `reference.md` § Validation bounds `k` by the roster's basis
    today, and a per-stratum bound is a check that does not exist yet.

    The mapping must be **total over the roster**, like `clusters`: a unit missing
    from it raises `KeyError` as a core defect rather than being given a stratum of
    its own. A unit carrying no value for the stratum attribute is possible after
    `validate` (a whole cluster carrying none agrees with itself), so how such a unit
    is rendered — a stratum of its own, or a refusal — is the caller's decision, made
    where the attribute is read.
    """
    units = list(roster)
    rng = random.Random(_seed_from(digest))
    if strata is None:
        return _assign_whole_clusters(units, k, rng, clusters)
    grouped: dict[str, list[Unit]] = {}
    for unit in units:
        grouped.setdefault(strata[unit.key], []).append(unit)
    per_stratum = [
        _assign_whole_clusters(members, k, rng, clusters) for members in grouped.values()
    ]
    # Index-wise, not sorted by size: sorting would re-pair the strata's pieces
    # against each other for no stated reason, and the fold a unit lands in is part
    # of this function's contract.
    return [[unit for folds in per_stratum for unit in folds[i]] for i in range(k)]


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

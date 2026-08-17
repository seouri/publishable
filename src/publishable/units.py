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
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from publishable.artifacts import ResolverIO
from publishable.config import Config
from publishable.errors import ContractError
from publishable.plugins import check_registration, declared_names, load_entry_point, scan_group

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
        Unit(key=row[key_col], paths=(), attributes={a: row[a] for a in attrs}) for row in rows
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
        p.relative_to(input_dir).as_posix() for p in input_dir.glob(pattern) if p.is_file()
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


RESOLVER_GROUP = "publishable.resolvers"


def _resolver_for(name: str) -> Callable[..., Any]:
    """The callable `data.units.from.resolver` names, or the refusal that answers instead.

    Three steps, three codes, in the order the information arrives:

    - **The name**, answered from package metadata alone (`scan_group`), so a name
      no installed distribution registers costs no import at all —
      `reference.md` § Creating a plugin makes that the whole argument for entry
      points. `E-RESOLVER-UNKNOWN`, naming every member of the group it did find,
      because the ordinary cause is a spelling.
    - **The object**, through `load_entry_point`, the one function in core that
      calls `EntryPoint.load()`. Every way a plugin's top level can fail arrives
      as `E-PLUGIN-LOAD`, including `SystemExit`.
    - **The declaration against the key** (`check_registration` over
      `declared_names`), `E-PLUGIN-DECORATOR`. Checked here rather than deferred
      to `run`: the object is already in hand, and reporting at `run` a fault
      `validate` had the evidence for is the shape this repo refuses.

    A collision between two distributions claiming this key is **not** decided
    here. `validate._check_plugin_collisions` reports it as `E-PLUGIN-COLLISION`
    for every config, from metadata, over the complete claim set in name order —
    the first claimant is used here rather than re-deciding the tie, since a
    verdict computed twice is a verdict that can disagree with itself.
    """
    found = scan_group(RESOLVER_GROUP)
    claimants = found.get(name)
    if not claimants:
        # `"none installed"` (the empty-`found` branch) is not exercised by any
        # fixture in this build: every test installs at least one distribution
        # under `publishable.resolvers`. Untested rather than unreachable.
        listed = ", ".join(found) if found else "none installed"
        raise ContractError(
            f"`data.units.from.resolver` names `{name}`, which no installed distribution "
            f"registers in the `{RESOLVER_GROUP}` entry-point group (registered: {listed})",
            code="E-RESOLVER-UNKNOWN",
        )
    ep = claimants[0]
    fn = load_entry_point(ep)
    check_registration(ep, declared_names(RESOLVER_GROUP, fn))
    return cast("Callable[..., Any]", fn)


def _from_resolver(
    decl: dict[str, Any],
    name: str,
    input_dir: Path,
    cfg: "Config | None",
    resolver_io: ResolverIO | None,
) -> tuple[list[Unit], frozenset[str]]:
    """The units a plugin's resolver yields, and the attribute names it yielded.

    The columns come back beside the roster for the reason `_from_table`'s do: they
    are the only honest reference set for `data.units.measurements.by` —
    `validate._check_measurements` checks `by` against them — and a resolver has
    no columns beyond the attributes it yields. The union over yielded units
    rather than the intersection, matching a table header's "this column exists"
    rather than "every row filled it in" — the same reading `collapse_measurements`
    takes when it treats a name only some rows carry as no disagreement.

    `Unit.attributes` on the returned roster carries only the declared
    `data.units.attributes` — projected exactly as `_from_table` projects a CSV
    row, which is what makes `cluster_by`, `weight_by`, `assign.<axis>.from`,
    `holdout.from` and a `fold`'s `stratify_by` indifferent to which form `from`
    took. An attribute a resolver yields and the config does not declare is
    dropped, exactly as an undeclared CSV column is.

    Yield order is preserved and nothing re-sorts it: `reference.md` § Where units
    come from makes resolver yield order the resolved order, `assign.method:
    blocked` reads that order as data, and `provenance.units_hash` covers the list
    in it.
    """
    if cfg is None:
        raise ContractError(
            f"`data.units.from.resolver` names `{name}`, and resolution was reached with no "
            'config to hand it — a resolver sees the same `cfg` a `scope: "run"` step does, '
            "so core's resolved state disagrees with itself here rather than the config being "
            "wrong",
            code="E-RUN-RESOLVER-UNCONFIGURED",
        )
    resolve = _resolver_for(name)
    io = resolver_io if resolver_io is not None else ResolverIO(input_dir)
    units: list[Unit] = []
    yielded: set[str] = set()
    try:
        for item in resolve(io, cfg):
            if not isinstance(item, Unit):
                raise ContractError(
                    f"resolver `{name}` yielded a {type(item).__name__} — a resolver yields "
                    "`Unit`s, which is what makes its roster a unit table with the columns a "
                    "CSV would have supplied",
                    code="E-RESOLVER-YIELD",
                )
            units.append(item)
            yielded.update(item.attributes)
    except ContractError as exc:
        if exc.code != "E-STEP-SWEPT-PARAM":
            raise
        # The mechanism is shared and the fault is not. `config.Node` raises the
        # step's identifier because that is what it raises for every reader of a
        # `SweptAway` marker; a reader holding it here would be sent to § Step
        # scope, which describes a different fault at a different time. Re-coded
        # rather than re-raised, on `discover_local`'s precedent for a coded
        # `ContractError` out of user code.
        raise ContractError(
            f"resolver `{name}` reads {exc}. The unit table is one table for the whole run, "
            "so conditions that resolved different units could not be paired and `n` would "
            "mean something different in each. Read a parameter the sweep leaves alone",
            code="E-RESOLVER-SWEPT-PARAM",
        ) from exc
    if not units:
        raise ContractError(
            f"resolver `{name}` yielded no units; a run measuring zero units has nothing to report",
            code="E-UNITS-EMPTY",
        )
    attrs = list(decl.get("attributes") or [])
    for attribute in attrs:
        if not isinstance(attribute, str):
            # An unhashable declared attribute (a `dict` or `list` entry) can
            # never equal a name a resolver yielded any more than it could equal
            # a CSV column name — `validate._check_units`'s own guard for the
            # table source (validate.py, "a non-string name can never equal a
            # CSV column name either") makes the identical call. Checked before
            # the set membership below, which hashes `attribute` and would raise
            # a bare `TypeError` out of `validate` for exactly this shape.
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which resolver `{name}` yields "
                "no unit carrying — a resolver has no columns beyond the attributes it yields, "
                "so the field a table would simply have carried has to be yielded",
                code="E-UNITS-ATTR-MISSING",
            )
        if attribute in RESERVED_FIELDS:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which is a field of `Unit` "
                f"itself; {', '.join(RESERVED_FIELDS)} cannot also be attributes",
                code="E-UNITS-ATTR-RESERVED",
            )
        if attribute not in yielded:
            raise ContractError(
                f"`data.units.attributes` names {attribute!r}, which resolver `{name}` yields "
                "no unit carrying — a resolver has no columns beyond the attributes it yields, "
                "so the field a table would simply have carried has to be yielded",
                code="E-UNITS-ATTR-MISSING",
            )
    # Projected onto the declared list exactly as `_from_table` projects a CSV
    # row, which is what makes everything downstream indifferent to which form
    # `from` took: `cluster_by`, `weight_by`, `assign.<axis>.from`, `holdout.from`
    # and a `fold`'s `stratify_by` all read `Unit.attributes` and were approved by
    # `validate` against `data.units.attributes` alone. An attribute the resolver
    # yields and the config does not declare is dropped, the way an undeclared
    # column is.
    units = [
        Unit(
            key=unit.key,
            paths=unit.paths,
            attributes={a: unit.attributes[a] for a in attrs if a in unit.attributes},
        )
        for unit in units
    ]
    return units, frozenset(yielded)


def resolve_units(
    units_decl: dict[str, Any],
    input_dir: Path,
    *,
    cfg: "Config | None" = None,
    resolver_io: ResolverIO | None = None,
) -> tuple[UnitList, dict[str, float] | None, frozenset[str]]:
    """Resolve the roster, preserving the order it was resolved in.

    Returns the roster, `technical_n` — `None` unless `data.units.measurements` is
    declared — and the source's own column names: a table's header, a glob's
    empty set, or a resolver's yielded attribute names. Both travel *beside* the
    roster rather than on it because `io.units` **is** a `UnitList` handed to
    steps, and `reference.md` § The unit list is three operations promises
    exactly iteration, `len`, and integer indexing, plus `.train`. A fourth
    operation would be a fourth thing every future backing has to provide.

    The columns are for `validate._check_measurements`, which checks
    `measurements.by` against the columns the source actually has. They are
    threaded from the one read `_from_table` already does rather than re-read
    there, so the two cannot come to disagree about what the table holds.

    `cfg` and `resolver_io` are defaulted keywords rather than required
    parameters — decision 6, ~60 existing call sites in `tests/` with no
    behavioural content to give them. `cfg` is what a `{resolver: ...}` source
    needs and every other source ignores; reaching a resolver source with
    `cfg=None` refuses under `E-RUN-RESOLVER-UNCONFIGURED` rather than crashing.
    `resolver_io` defaults to a fresh `ResolverIO(input_dir)`; only
    `cli.command_run` needs the object back afterwards, to read `read_paths`.
    """
    source = units_decl.get("from")
    if isinstance(source, str):
        units, columns = _from_table(units_decl, input_dir, source)
    elif isinstance(source, dict) and "glob" in source:
        units, columns = _from_glob(units_decl, str(source["glob"]), input_dir)
    elif isinstance(source, dict) and "resolver" in source:
        # `glob` is tested first, deliberately: `data.units.from` declaring both
        # keys is refused by `validate._check_from_source_exclusivity` as
        # `E-UNITS-SOURCE-AMBIGUOUS`, and keeping this order means the two
        # modules cannot come to read one declaration two ways in the window
        # before that check runs.
        units, columns = _from_resolver(
            units_decl, str(source["resolver"]), input_dir, cfg, resolver_io
        )
    else:
        raise ContractError(
            f"`data.units.from` is {source!r}; expected a table name, {{glob: ...}}, or "
            f"{{resolver: ...}}",
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
        # The two flat declarations whose column is a fact about the unit rather
        # than about the measurement, read straight off the declaration this
        # function already holds — no new plumbing, and no second place that could
        # come to disagree with `units_decl` about which column is the cluster. The
        # `isinstance` filter is load-bearing rather than defensive: a list-valued
        # `cluster_by` is `E-CONFIG-TYPE`'s finding, and using one as a mapping key
        # is a `TypeError` escaping `validate`, which never raises.
        # **A flat registry entry reaches only a flat, string-valued key of
        # `data.units`.** This indexes `units_decl` by the key itself, so on its
        # own it reaches `cluster_by` and `weight_by` and nothing nested —
        # `assign.<axis>.from` and `holdout.from` are the next two columns that
        # want this rule, and neither is a flat string: `assign` is a mapping of
        # axis blocks and `holdout` is a mapping with its own `from`. Task 11 adds
        # `_assign_constant_columns` below as `assign`'s accessor, so that one is
        # now reachable; **`holdout.from` reaches it through
        # `_holdout_constant_column`** — its shape is a single key under a
        # fixed mapping, not one-per-declared-axis, so it needed its own
        # accessor rather than this one's `axis` loop. Verified by probe, not
        # assumed: adding `"assign"` to `CONSTANT_COLUMN_RULES` alone changed
        # nothing, because this comprehension's `isinstance(..., str)` filter
        # drops a mapping before the registry is even consulted.
        #
        # **`assign`'s entries are built first, deliberately** — `constant`'s
        # iteration order is the order `collapse_measurements` checks
        # declarations in, and it stops at the first that raises, so whichever
        # comes first in this dict wins a unit that violates more than one at
        # once. `assign` is documented as the worst of the four (§ Allocation:
        # a mis-collapsed arm decides which condition a unit is measured in,
        # where cluster/weight/holdout only decide which side of a split it
        # lands on or what it stands for), so it has to be checked before the
        # flat pair or that severity ordering would be undermined by an
        # accident of dict-building order — the "precedence rule nothing in
        # the documents states" `CONSTANT_COLUMN_RULES` warns against, now
        # stated in both places rather than left implicit.
        constant = _assign_constant_columns(units_decl.get("assign"))
        # `holdout.from` next, between `assign` and the flat pair. `assign` is
        # documented as the worst of the family (§ Allocation: a mis-collapsed
        # arm decides which CONDITION a unit is measured in), so it stays
        # first. `holdout.from` and `cluster_by` say the same thing about the
        # damage — which side of a split the unit lands on — so the order
        # BETWEEN those two is fixed here deterministically rather than left to
        # an accident of dict-building, and is **not** a claim that one fault
        # is worse than the other. `weight_by` stays last, which is the
        # documented ordering.
        constant.update(_holdout_constant_column(units_decl.get("holdout")))
        # `holdout` is excluded here even though it is a `CONSTANT_COLUMN_RULES`
        # key: this comprehension's `isinstance(..., str)` filter would otherwise
        # admit a bare-string `data.units.holdout`, a shape `_check_holdout`
        # already refuses as `E-CONFIG-TYPE` and that `_holdout_constant_column`
        # above is deliberately silent on. `holdout.from` reaches this registry
        # only through that accessor, so a mis-typed scalar stays
        # `E-CONFIG-TYPE`'s finding alone rather than also raising
        # `E-DATA-HOLDOUT-VARIES` through a second, undocumented route.
        constant.update(
            {
                declaration: units_decl[declaration]
                for declaration in CONSTANT_COLUMN_RULES
                if declaration != "holdout"
                and isinstance(units_decl.get(declaration), str)
                and units_decl[declaration]
            }
        )
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


def _assign_constant_columns(assign_decl: Any) -> dict[str, str]:
    """`assign.<axis>.from`, resolved against its default, for every axis
    `data.units.assign` declares a mapping block for — `resolve_units`'s
    accessor for the one declaration `CONSTANT_COLUMN_RULES` cannot reach as a
    flat string.

    Resolution mirrors `validate._check_assign`'s own — `from` if it is a
    non-empty string, else the axis name when the key is entirely absent — but
    stays narrower on purpose: this function's only job is deciding which
    column, if any, this axis's constancy has to hold, not reporting a
    malformed declaration. A non-mapping axis block, an explicit `from: ""`,
    and a non-`str` `from` are three shapes `_check_assign` reports and this
    function is silent on, each because it resolves to no column to check:
    `E-DATA-ASSIGN-METHOD` (a stray value in place of a block) and
    `E-DATA-ASSIGN-UNKNOWN` (the empty-string and wrong-type halves) are
    `validate`'s findings to raise, not a `ContractError` from a run that
    resolution has no path to report through.

    **Gated on `method == "by_attribute"`, matching `_check_assign`'s own
    elif chain**, which reads `from` and `levels` only in that branch — they
    "mean nothing" under `random`/`blocked`, which draw an arm instead of
    reading one, and under an absent or out-of-enum method, refused as
    `E-DATA-ASSIGN-METHOD`. Without this gate, a `method: random`
    block whose axis-name default happens to match a column that varies within
    a unit's rows would raise `E-DATA-ASSIGN-VARIES` naming a `.from` path the
    declaration never wrote, over a column nothing under that method reads —
    the same validate-clean-then-crash gap this module's docstrings warn
    against elsewhere, in the opposite direction: a config no check approves
    yet, refused anyway by a rule that assumed a resolution `by_attribute`
    alone performs. **That gate went from redundant to load-bearing when the
    draw was built**: `random`/`blocked` were refused at `validate` before it,
    so no config carrying one could reach this function at all, and now every
    drawn design does. This is the only thing standing between such a design
    and an `E-DATA-ASSIGN-VARIES` over a column its declaration never named
    and its draw never reads.

    Keyed `assign.<axis>.from`, the literal dotted path a reader would look for
    in `data.units` — not `assign` alone — because `assign` is one declaration
    yielding as many columns as there are axes, and `collapse_measurements`'s
    error message names the column through this key. `CONSTANT_COLUMN_RULES`
    still holds one entry for it, under the bare word `assign`: the lookup in
    `collapse_measurements` strips back to the segment before the first `.`,
    so `cluster_by`/`weight_by` (no dot, no-op strip) and every
    `assign.<axis>.from` key resolve to their rule through the one mechanism.
    """
    if not isinstance(assign_decl, dict):
        return {}
    resolved: dict[str, str] = {}
    for axis, block in assign_decl.items():
        if not isinstance(block, dict) or not isinstance(axis, str):
            continue
        if block.get("method") != "by_attribute":
            continue
        declared_from = block.get("from")
        if declared_from is None:
            resolved_from: str | None = axis
        elif isinstance(declared_from, str) and declared_from:
            resolved_from = declared_from
        else:
            resolved_from = None
        if resolved_from:
            resolved[f"assign.{axis}.from"] = resolved_from
    return resolved


def _holdout_constant_column(holdout_decl: Any) -> dict[str, str]:
    """`holdout.from` when a `by_attribute` holdout declares one — at most one
    entry, keyed by the literal dotted path a reader would look for.

    `_assign_constant_columns`' sibling, one declaration over, and narrower for
    the reason that one is narrow: this function's only job is deciding which
    column, if any, a holdout's constancy has to hold — not reporting a
    malformed declaration. An absent block, a non-mapping block, a missing
    `from`, an empty `from` and a non-`str` `from` are shapes
    `validate._check_holdout` reports (`E-DATA-HOLDOUT-METHOD`,
    `E-DATA-HOLDOUT-FROM`) and this function is silent on, each because it
    resolves to no column to check: those are `validate`'s findings to raise,
    not a `ContractError` from a run that resolution has no path to report
    through.

    **Gated on `method == "by_attribute"`**, matching `_assign_constant_columns`'
    own gate and for its reason: `random` draws the split rather than reading
    one, so no column is read, and a `from` declared beside it means nothing —
    already refused as `E-DATA-HOLDOUT-NO-DRAW`. Without this gate a drawn
    split whose declaration carried a stray `from` naming a column that varies
    within a unit's rows would raise `E-DATA-HOLDOUT-VARIES` over a column its
    draw never reads, which is the validate-clean-then-crash gap in the
    opposite direction: a config no check approves, refused anyway by a rule
    that assumed a read `by_attribute` alone performs.

    **There is no axis-name default**, unlike `assign.<axis>.from`: a holdout
    has no axis name, which is why `validate` requires `from` outright under
    `by_attribute` rather than defaulting it.
    """
    if not isinstance(holdout_decl, dict):
        return {}
    if holdout_decl.get("method") != "by_attribute":
        return {}
    declared_from = holdout_decl.get("from")
    if isinstance(declared_from, str) and declared_from:
        return {"holdout.from": declared_from}
    return {}


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
    numeric_values = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)
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
    "assign": (
        "E-DATA-ASSIGN-VARIES",
        "An arm decides which condition the unit is measured in — not merely "
        "which side of a split it lands on, which is the worst a mis-collapsed "
        "cluster does, and not merely what size it stands for, which is the "
        "worst a mis-collapsed weight does. Collapsing disagreeing rows would "
        "leave that decision to the order the rows happen to be in. An arm is "
        "a fact about the unit, not about the measurement",
    ),
    "holdout": (
        "E-DATA-HOLDOUT-VARIES",
        "A holdout decides which side of a train/test split the unit lands on, "
        "so collapsing disagreeing rows would leave that decision to the order "
        "the rows happen to be in — a unit evaluated against a model it was "
        "fitted on, or held back from one it should have been evaluated by. "
        "Which side of a split a unit is on is a fact about the unit, not "
        "about the measurement",
    ),
}
"""The declarations whose column may not vary within a unit's measurement rows.

**Four codes, not one**, deliberately: `reference.md` § Clustered units,
§ Weighted samples and § Allocation each state the same constancy rule in
prose, for a different one of the first three columns; `holdout.from`'s own
instance of the rule is stated only in § Errors core raises
(`E-DATA-HOLDOUT-VARIES`'s row) rather than in § A fixed holdout split, which
carries no such paragraph.
Each of the first three says a different thing about what breaks — a
mis-collapsed weight mis-sizes what one unit stands for, a mis-collapsed
cluster decides which side of a split that unit lands on, and a mis-collapsed
arm decides which *condition* the unit is measured in, the worst of the three
because it changes what the run claims to have compared rather than how
confidently it says so. **`holdout` is the one exception**: it says the
*same* thing about the damage `cluster_by` does — which side of a split the
unit lands on — and still gets its own code, because one identifier for
either would send the reader naming the other to a section that does not
describe their input field at all.

Keyed by the *declaration* rather than by the column, so a config naming one
column under two declarations is checked once for each **declaration considered
on its own**: each is checked on its own and still raises its own code when it
is the only one declared — a config declaring only `cluster_by: arm` over rows
where `arm` varies raises `E-DATA-CLUSTER-VARIES`, and the same rows under only
`assign: {arm: {method: by_attribute}}` raise `E-DATA-ASSIGN-VARIES` — rather
than silently dropping one under a precedence rule nothing in the documents
states. **This is not a claim that one `resolve_units` call reports both at
once, and it is only ever tested one unit at a time**: `collapse_measurements`
raises the first `ContractError` its per-unit loop finds and stops, so a single
config naming the same varying column under both `cluster_by` and an axis's
`assign.<axis>.from` gets exactly one code from one call — and only a unit that
violates *both* declarations at once puts that choice to the test at all; a
roster where one unit varies only in `cluster_by`'s column and a different unit
varies only in `assign`'s still raises `E-DATA-CLUSTER-VARIES`, because that
unit is first in roster order and its own single violation is all `resolve_units`
ever sees before raising. For a unit that violates both, `constant`'s iteration
order decides: `assign`'s entries are built before the flat pair's (see
`resolve_units`), so `E-DATA-ASSIGN-VARIES` wins today, matching the severity
order this docstring states — the once-unstated "precedence rule" is now this
one, spelled out rather than left to whichever order a dict comprehension
happened to build. What "deliberately, nothing here builds mutual exclusion"
means is narrower than "reports both" and still true: neither check is skipped
*because* the other declaration also names the column — remove the
higher-priority declaration and the same config still raises the other's code,
which a real precedence *rule* (a check disabled outright by a sibling's
presence) would not do.

**`assign` is keyed by the bare declaration name, not by `assign.<axis>.from`**,
which is the design choice this registry had to make and the one the alternative
loses: `resolve_units` cannot expand this dict per axis ahead of time, because
the axes are declared in the config, not known when this module is loaded — so
either the registry carries the code and message directly inside the `constant`
mapping `resolve_units` builds (the code/message travel with each axis's entry,
built fresh per axis), or the registry stays keyed by declaration name and the
*lookup* strips a dotted key back to that name. The first would duplicate the
same `(code, message)` pair once per declared axis instead of once, and would
scatter this docstring's reasoning across every call site that builds a
`constant` mapping rather than leaving it in the one place a reader checking
"why this code" would look. So `_assign_constant_columns` below builds
`constant` entries keyed `assign.<axis>.from` — the literal dotted path, for the
error message — and `collapse_measurements`'s lookup strips back to the segment
before the first `.`, which is a no-op for `cluster_by`/`weight_by` and finds
`assign` for every axis alike. **`holdout.from` reaches this registry through
its own accessor**, `_holdout_constant_column` below — a single key under a
fixed mapping rather than one per declared axis, so it could not use
`_assign_constant_columns`'s `axis` loop, and it could not be a flat entry
either: `resolve_units`' comprehension filters on `isinstance(..., str)` and
drops a mapping before the registry is consulted. Its `constant` key is the
dotted `holdout.from`, for the message, and the lookup strips it back to the
bare `holdout` here, exactly as it strips `assign.<axis>.from` back to
`assign`.

**Every key in this dict must itself contain no `.`.** `collapse_measurements`'s
lookup strips a `constant` key back to the segment before its first `.` before
indexing this registry with it, so a future bare key spelled with a dot would
be unreachable by exactly the same stripping that makes `assign.<axis>.from`
reachable, and a `constant` key whose prefix names no registry entry raises a
bare `KeyError` — which, unlike a `ContractError`, is not caught by `validate`'s
`except ContractError` around `resolve_units` and would escape it.
"""


def collapse_measurements(
    units: list[Unit], by: str, collapse: Any, constant: Mapping[str, str] | None = None
) -> tuple[list[Unit], list[int]]:
    """Collapse rows sharing a `key` into one unit, in first-seen order.

    `constant` maps a declaration to the column it names, and those columns are
    refused where they vary within one unit's rows rather than being collapsed
    like any other attribute. A key is either a bare `CONSTANT_COLUMN_RULES` entry
    or a dotted path built by that entry's own accessor (`_assign_constant_columns`,
    `_holdout_constant_column`) for a declaration `CONSTANT_COLUMN_RULES` cannot
    reach as a flat string — see `CONSTANT_COLUMN_RULES`'s own docstring for which
    declaration takes which shape and why. The lookup below strips a dotted key
    back to the segment before its first `.` to find the rule, so one registry
    entry covers every dotted variant a declaration produces alike.
    **`validate` cannot host that check**:
    `resolve_units` collapses internally, so a validate-time check sees the
    post-collapse roster and the disagreeing values are already gone. This
    function groups the rows by key and is the one place holding them.

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
                # `declaration.partition(".")[0]` is a no-op for `cluster_by`/
                # `weight_by` — neither carries a `.` — and strips
                # `assign.<axis>.from` back to `assign`, the one entry
                # `CONSTANT_COLUMN_RULES` carries for every axis alike; see
                # that registry's docstring for why the dotted key is not
                # expanded into the registry itself.
                code, why = CONSTANT_COLUMN_RULES[declaration.partition(".")[0]]
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


def arms_of(roster: UnitList, column: str, levels: Sequence[str]) -> dict[str, list[Unit]]:
    """Which arm each unit belongs to, partitioned by declared level, in roster order.

    **The single authority** for arm membership, beside `clusters_of` and for the
    same reason: `validate` and the runner both have to ask "which units are in
    this arm" of the same declaration, and a second notion of it is the
    validate-clean-then-disagree gap in a new shape — here it would mean a
    `between` design `validate` approved whose conditions core cannot actually
    build, because the partition it draws at run time is not the one `validate`
    checked. `validate` calls this to turn a mismatch into
    `E-DATA-ASSIGN-LEVELS`; the subset view a `between` condition's roster is
    built from, and the per-arm `n` a report counts, both have to read the same
    partition rather than re-deriving arm membership from the roster on their
    own — which is the defect class this docstring is written to prevent a third
    instance of.

    `column` names a **declared attribute** — `assign.<axis>.from`, already
    resolved against its default by the caller — not a source column, the same
    side of the line `weight_by` and `cluster_by` fall on: an arm is read per
    unit when a `between` condition's roster is drawn, so it has to survive
    resolution as an attribute. `levels` is `sweep.groups`' declared list for
    that axis, in its own order.

    **Set equality, not subset tolerance, in either direction** —
    `reference.md` § Allocation states it twice: the `by_attribute` example
    annotates `from` as naming "a unit attribute whose values are exactly the
    declared levels", and `allocation: between` opens "each unit belongs to
    exactly one arm". So this raises `E-DATA-ASSIGN-LEVELS` for either
    violation, one code because a caller only needs to know the partition is
    unusable and the message is what says which:

    - a unit's value names none of `levels` — that unit would belong to no
      arm, and there is no fourth part of `n` for it;
    - a declared level no unit's value names — that arm's condition would
      resolve zero units.

    A unit carrying no value for `column` at all is folded into the first
    violation rather than raising a distinct fault — `clusters_of`'s convention
    for the same situation: it, too, names no declared level, for the same
    reason a value outside `levels` does not.

    Values are stringified before comparison, `clusters_of`'s reason: a table
    yields `str` for every column, and an arm id is a label rather than a
    quantity nothing downstream does arithmetic on.

    A caller may rely on every returned level's list being non-empty and on
    every unit in `roster` appearing in exactly one of them — the exact
    partition set equality promises once this returns without raising.
    """
    declared = list(levels)
    declared_set = set(declared)
    partition: dict[str, list[Unit]] = {level: [] for level in declared}
    unmatched: list[tuple[str, str | None]] = []
    for unit in roster:
        value = str(unit.attributes[column]) if column in unit.attributes else None
        if value is None or value not in declared_set:
            unmatched.append((unit.key, value))
            continue
        partition[value].append(unit)
    if unmatched:
        key, value = unmatched[0]
        holds = "carries no value for it" if value is None else f"holds {value!r}"
        raise ContractError(
            f"the arm attribute {column!r} does not resolve to the declared levels "
            f"({', '.join(declared)}) — unit {key!r} {holds}, naming none of them. "
            "Every unit belongs to exactly one arm, so a value naming none of the "
            f"declared levels leaves that unit in none of them "
            f"({len(unmatched)} of {len(roster)} units affected)",
            code="E-DATA-ASSIGN-LEVELS",
        )
    empty = [level for level in declared if not partition[level]]
    if empty:
        raise ContractError(
            f"the arm attribute {column!r} does not resolve to the declared levels "
            f"— no unit's value names {', '.join(empty)}. Every declared level "
            "needs at least one unit, or that arm's condition resolves zero of "
            "them",
            code="E-DATA-ASSIGN-LEVELS",
        )
    return partition


DRAWN_ASSIGN_METHODS = ("random", "blocked")
"""The `validate.ASSIGN_METHODS` values that draw an arm rather than read one
already assigned — **one tuple, defined here, read by `validate` alone now**.

`validate` imported it to report `E-DATA-ASSIGN-DRAWN`, the refusal of a
well-formed *value* this build could not yet realize. That refusal is retired,
and the tuple is not: it is now what `validate._check_assign` **dispatches** on
— which of a block's fields mean anything follows from whether the method draws
(`ratio`, `block_size`, `stratify_by`) or reads (`from`) — a permanent question
where the refusal was a temporary one. It lives here rather than in `validate`
because `units.py` depends on nothing there, and because a second literal
naming which methods draw would be pinned in agreement with this one by
nothing.

`assignment_for` below no longer reads it at all: task 8 realized `random`
(unclustered, then task 9 beside a declared `cluster_by`) and task 10 realized
`blocked` the same way, each in its own branch dispatched on `method` directly.
The generic fallback below them no longer distinguishes a member of this tuple
from any other unrecognized `method` string — every value that reaches it is,
by construction, one neither branch above claimed, so there is nothing left for
this tuple to pick a message for. It survives here as `validate`'s source of
truth for the dispatch above, which outlives the refusal it was minted for.

**It was never what made `assignment_for` fail closed**, and must not be
mistaken for that even in memory: `assignment_for` allows `by_attribute`,
`random`, and `blocked`, and refuses everything else, so a fourth drawing
method added to the enum and to nothing else raises rather than reading a
column, whether or not anyone remembers to add it here.
"""


@dataclass(frozen=True)
class ArmPlan:
    """One axis's **realized** membership: level → unit keys, in roster order.

    The shape a drawn allocation and a read one both fit, and the reason this
    type exists at all: `arms_of` reads an arm out of a *column*, and a drawn
    axis (`method: random`, `method: blocked`) has no column to read. A caller
    holding `(column, levels)` — `arm_members`' old input shape — cannot
    express a draw, so the draw would have had to happen somewhere else, and
    "somewhere else" is a second producer of arm membership: the
    validate-clean-then-disagree gap `arms_of`'s own docstring is written to
    prevent a third instance of. `assignment_for` below is the one producer,
    and this is what it produces.

    - `levels` is the axis's declared `sweep.groups` levels, in declared
      order, and every one of them is a key of `members`.
    - `members` maps each level to that arm's unit keys. **In roster order
      under `by_attribute`**; under a draw, in whatever order the draw
      realized — `artifacts.build_allocation_document` records the order it
      is given rather than re-sorting, because a `blocked` design reads that
      order as data.
    - `seed` is the seed the draw was realized with (`units.assign_seed_for`),
      and is `None` under `by_attribute` — a method that reads an arm a trial
      system already assigned rather than drawing one, so recording a seed
      would be a false record of a draw that never happened.
    - `strata` is the realized `assign.<axis>.stratify_by` — the attribute
      names the draw balanced each arm within, in declared order — and is
      empty under `by_attribute` for the reason above: `stratify_by` names
      how a draw was *balanced*, and with no draw there is nothing it
      describes. It is empty under a draw too whenever the declaration was
      empty, which is what `init` writes: an unstratified draw balances on
      nothing but the ratio, and `()` is the truthful record of that. A
      declared name that no resolved unit carries never reaches a plan at
      all — `assignment_for` raises rather than recording a balance it did
      not perform.

    `frozen=True` blocks rebinding an attribute; it does **not** deep-freeze
    `members`, whose values are tuples but whose mapping a determined caller
    can still mutate in place if it is handed a `dict`. Treat it as read-only
    — nothing in core writes through it — rather than as a guarantee this type
    enforces.
    """

    levels: tuple[str, ...]
    members: Mapping[str, tuple[str, ...]]
    seed: int | None
    strata: tuple[str, ...]


def _apportion(n: int, weights: Sequence[float]) -> list[int]:
    """`n` split across `weights`, largest-remainder (Hamilton) apportionment —
    `assignment_for`'s `random` path uses it to turn `assign.<axis>.ratio` into
    per-level sizes.

    Each entry's exact share (`n * weight / sum(weights)`) floors, and the
    remainder — `n` minus the sum of those floors — goes one at a time to the
    largest fractional part, ties broken by the entry's position in `weights`
    (so the first-declared level of an equal split wins any tie, deterministic
    rather than left to dict or set order). Every size is within one of its
    exact proportional share, which is the strongest claim a ratio that
    doesn't divide `n` supports — `partition_units`'s docstring makes the same
    argument for folds and refuses to claim the stronger, exact one.

    **A size of 0 is possible here and is the caller's to refuse.** A ratio
    skewed enough relative to `n` (a weight so small its floor is 0, with the
    remainder exhausted by larger fractions first — `{a: 1, b: 1000}` over 10
    units gives `[0, 10]`), or simply fewer units than levels, leaves an entry
    at 0. Nothing here manufactures a unit for a level the ratio didn't earn
    one for, and nothing here raises either: only `assignment_for` holds the
    axis name, the declared `ratio`, and the roster the message has to name,
    so the refusal lives there — as `E-DATA-ASSIGN-LEVELS`, the same code and
    the same words `arms_of` refuses a read arm no unit resolves to with.
    """
    total = sum(weights)
    quotas = [n * weight / total for weight in weights]
    floors = [int(quota) for quota in quotas]
    remainder = n - sum(floors)
    fractions = [quota - floor for quota, floor in zip(quotas, floors, strict=True)]
    order = sorted(range(len(weights)), key=lambda i: (-fractions[i], i))
    sizes = list(floors)
    for i in order[:remainder]:
        sizes[i] += 1
    return sizes


HOLDOUT_LEVELS = ("train", "test")
"""`data.units.holdout`'s two sides, in apportionment order — train first.

Fixed literals rather than "the two values the column happens to hold", because
a holdout declares no `levels` for core to read an order out of, and inferring
one from the data would make which side is *evaluated* depend on a lexical
accident of the input. `reference.md` § A fixed holdout split states the rule
and § Errors names the refusal, `E-DATA-HOLDOUT-VALUES`.

Order is load-bearing twice: it is the order `holdout_sizes` apportions in, so
`frac` is the SECOND weight, and it is the order `arms_of` is handed for a
`by_attribute` read.
"""


def holdout_sizes(n: int, frac: float) -> tuple[int, int]:
    """`(train, test)` — `n` apportioned across `[1 - frac, frac]`.

    **One arithmetic for the split, and two callers**: `validate._check_holdout`
    refuses a `frac` that apportions the test side zero units, and
    `holdout_for`'s unclustered draw cuts the shuffled roster at exactly these
    sizes. Two derivations of the same number would mean `validate` approving a
    `frac` whose realized test side the draw then sized differently — the
    validate-clean-then-disagree gap `arms_of`'s own docstring is written to
    prevent a third instance of.

    `_apportion`'s largest-remainder rule, which `assignment_for`'s `random`
    branch already uses for `assign.<axis>.ratio`: each side's exact share
    floors and the remainder goes to the larger fractional part. Every size is
    within one of its exact proportional share, which is the strongest claim a
    fraction that doesn't divide `n` supports.

    **A test size of 0 is possible and is the caller's to refuse.** Two units at
    `frac: 0.2` gives `(2, 0)`. Nothing here raises: `validate` holds the
    declared `frac` and the roster a message has to name, so the refusal lives
    there — `_apportion`'s own convention, one construction over.
    """
    train, test = _apportion(n, [1.0 - frac, frac])
    return train, test


def holdout_values_fault(roster: UnitList, column: str) -> str | None:
    """How `column` fails to resolve to exactly `train` and `test` over this
    roster — as a message — or `None` when it does not fail.

    **One authority, two reporting surfaces**, which is
    `stratum_varies_within_cluster`'s own arrangement: `validate._check_holdout`
    collects this as `E-DATA-HOLDOUT-VALUES` and `holdout_for` raises it under
    the same code, so the two cannot come to disagree about either the verdict
    or the wording. Two independent wrappings of one raise is exactly how two
    messages drift apart.

    The **verdict** is `arms_of`'s, unchanged: that function stays the authority
    for a column-read partition and promises set equality in both directions —
    no unit's value outside the pair, and neither literal left holding nothing.
    Only the **wording** is rebuilt here, because `arms_of`'s own message names
    an arm and an axis's declared levels and would send a holdout's reader to
    the wrong section.

    Returns a message rather than raising, so `validate` — contracted never to
    raise — can report it beside every other finding, and so `holdout_for` can
    raise it with the code that belongs to a holdout rather than to an arm.
    """
    try:
        arms_of(roster, column, HOLDOUT_LEVELS)
    except ContractError:
        seen = sorted(
            {
                "no value" if u.attributes[column] in (None, "") else str(u.attributes[column])
                for u in roster
                if column in u.attributes
            }
        )
        missing = [lit for lit in HOLDOUT_LEVELS if lit not in seen]
        return (
            f"the holdout column {column!r} has values {', '.join(seen) or 'none'} over "
            f"this roster — a `by_attribute` holdout needs exactly "
            f"`{HOLDOUT_LEVELS[0]}` and `{HOLDOUT_LEVELS[1]}`"
            + (f", and {', '.join(missing)} names no unit" if missing else "")
            + ". A holdout declares no levels for core to read an order out of, so the "
            "two names are fixed rather than inferred from the data"
        )
    return None


@dataclass(frozen=True)
class HoldoutPlan:
    """`data.units.holdout` **realized** — the two sides as unit keys, plus what
    it took to produce them.

    `ArmPlan`'s sibling and deliberately not the same type: an arm plan is
    `level -> keys` over a declared `levels` tuple, where a holdout's two sides
    are fixed and named, and squeezing one into the other would mean either a
    fabricated axis name or a `levels` field with one legal value.

    - `train` and `test` hold unit keys, never row numbers — a roster that
      gains a unit renumbers rows and would silently repoint every membership
      claim. Every key of the roster appears in exactly one of them.
    - Order is **roster order** under `by_attribute`, which `arms_of` promises,
      and the order the shuffle realized under `random` — recorded rather than
      re-sorted, `ArmPlan`'s own rule, because the record of a draw is the
      draw.
    - `seed` is the seed the draw was realized with, and is `None` under
      `by_attribute`: a method that reads a partition the data already holds
      rather than drawing one, so recording a seed would be a false record of a
      draw that never happened.
    - `strata` is the realized `stratify_by`, in declared order, and is empty
      under `by_attribute` for the reason above and empty under a draw that
      declared none.

    `frozen=True` blocks rebinding an attribute; the two tuples are immutable
    outright, so unlike `ArmPlan.members` there is nothing here a determined
    caller can mutate in place.
    """

    train: tuple[str, ...]
    test: tuple[str, ...]
    seed: int | None
    strata: tuple[str, ...]


HOLDOUT_METHODS_REALIZED = ("random", "by_attribute")
"""The `data.units.holdout.method` values `holdout_for` draws or reads at this
commit — named for its own fail-closed message, `assignment_for`'s allowlist
posture one seam over: a third method added to `validate.HOLDOUT_METHODS` and
to nothing else falls through to `holdout_for`'s final `NotImplementedError`
rather than silently partitioning. Declared here rather than imported from
`validate`, which imports `units` and not the reverse.
"""


def holdout_for(
    roster: UnitList,
    block: Mapping[str, Any] | None,
    *,
    seed: int,
    clusters: Mapping[str, str] | None = None,
) -> HoldoutPlan:
    """`data.units.holdout`, realized — **the single producer** of a
    `HoldoutPlan`.

    A **pure function of its arguments**, `assignment_for`'s reason one
    declaration over: `validate` has to ask "which units are in the test
    partition" of the same declaration `cli.command_run` asks it of — the
    `limits.min_clusters` warning is exactly that question — so the draw cannot
    live in the runner. Two callers, one answer, computed the same way from the
    same inputs.

    **`seed` is required and this function never derives one.** The seed
    argument exists so a caller that derives a seed some other way — from a
    run's identity, say — composes that derivation with this draw rather than
    handing the draw a policy to also get right: a function that both draws
    and derives is two independent things to get wrong inside one, and it
    would put the derivation out of reach of a test that wants to pin a draw
    against a known seed. The value is recorded on the plan under `random` and
    discarded under `by_attribute`, which draws nothing.

    Dispatches on `block["method"]`, `reference.md` § A fixed holdout split's
    own enum:

    - `by_attribute` reads the two sides out of a column, through `arms_of`
      **unchanged** — that function stays the authority for a column-read
      partition and this one does not re-derive it. The levels it is handed are
      `HOLDOUT_LEVELS`, the fixed `train`/`test` literals, so `arms_of`'s set
      equality in both directions is what refuses a third value, a value naming
      neither, and a literal naming no unit. The refusal goes through
      `holdout_values_fault`, which owns both the verdict and the wording, so
      this raise and `validate._check_holdout`'s collected finding are one
      answer rather than two wrappings of the same raise — `arms_of`'s own
      message names an arm and an axis's declared levels and would send a
      holdout's reader to the wrong section.
    - `random`, unclustered and unstratified, draws one: `holdout_sizes` — the
      same apportionment `validate` approved the `frac` against — then one
      `rng.shuffle` of the whole roster's keys, then two consecutive slices,
      train first. That is `assignment_for`'s `random` branch exactly, and
      deliberately so: one construction, described in one place.
    - **Every other value raises `NotImplementedError`** — an allowlist. Fail
      closed costs nothing, because `validate` already refuses an
      out-of-enum method (`E-DATA-HOLDOUT-METHOD`) before a run reaches here,
      and it is what keeps a *third* method added to `validate.HOLDOUT_METHODS`
      and to nothing else from validating clean and then silently partitioning.
      This includes an absent, non-mapping, or method-less `block` — unlike
      `assignment_for`, which falls such a block back to `by_attribute`, this
      function has no default method to fall back to, since an absent holdout
      declares no holdout at all rather than an unnamed one.

    **`clusters` and `stratify_by` compose, both inside the `random` draw.**
    A `stratify_by` splits the roster into `_stratum_groups` first, one
    generator carried across every stratum in roster order, `assignment_for`'s
    own convention: the seed determines the whole split together rather than
    each stratum in isolation. `clusters`, present or not, then decides how
    each stratum (or the whole roster, unstratified) is drawn — whole clusters
    through `_assign_whole_clusters_by_ratio` at weights `[1 - frac, frac]`, or
    the unclustered shuffle-and-slice above.

    **The two constructions are deliberately not one, and are not
    bit-identical.** The unclustered draw shuffles unit keys and cuts two
    consecutive slices; the clustered draw shuffles cluster names, sorts
    largest-first and deals each cluster to the bucket furthest below its own
    target share — the second interleaves by ratio where the first slices, and
    that is a difference in MEMBERSHIP, not only in mechanism. **Singleton
    clusters are not exempt from the SIZE disagreement either**: a sweep of
    every `n` in 2..39 against twelve `frac` values found 90 seeds where the
    unclustered and singleton-clustered draws realize different sizes,
    including cases where one refuses outright while the other does not
    (`n=2, frac=0.1`: unclustered raises `E-DATA-HOLDOUT-EMPTY`; clustered
    returns a 1/1 split). No size agreement is promised at any cluster size —
    `_assign_whole_clusters_by_ratio`'s own "no bound on that deviation is
    promised" already says so — so a fixture pinning equal sizes for both
    constructions is pinning that seed's coincidence, not a property; what a
    fixture comparing the two can rely on is that they draw different
    MEMBERSHIP, whatever sizes each realizes. `_assign_whole_clusters_by_ratio`
    takes a non-optional `Mapping`
    and indexes it, unlike `_assign_whole_clusters`, which is why this is two
    paths rather than one with a `clusters or singletons` default.

    **Both sides are refused empty**, under `E-DATA-HOLDOUT-EMPTY`, checked
    over the MERGED draw rather than per stratum — `assignment_for`'s rule for
    the identical composition: a side a small stratum apportioned nothing is
    fine while another stratum covered it, and only a side empty across the
    whole draw is refused. `validate._check_holdout` refuses a zero *test*
    side from the declaration and the roster size, and does not refuse a zero
    *train* side — 2 units at `frac: 0.9` apportions `(0, 2)`, which would fit
    a model on nothing. The draw holds the realized sizes and is the last
    place that can see them, which is `assignment_for`'s own posture for a
    zero-size arm — including a clustered draw's realized sizes, which a
    declared `frac` alone cannot predict.
    """
    block_map: Mapping[str, Any] = block if isinstance(block, Mapping) else {}
    method = block_map.get("method")
    strata = stratum_names(block_map.get("stratify_by"))
    if method == "by_attribute":
        column = block_map.get("from")
        if not isinstance(column, str) or not column:
            raise NotImplementedError(
                "`data.units.holdout.method: by_attribute` names no column to read the "
                "split out of; `validate` refuses this as `E-DATA-HOLDOUT-FROM`"
            )
        # `holdout_values_fault` computes the verdict AND the wording, so this
        # raise and `validate._check_holdout`'s collected finding are one
        # answer rather than two wrappings of `arms_of` that drift apart.
        fault = holdout_values_fault(roster, column)
        if fault is not None:
            raise ContractError(fault, code="E-DATA-HOLDOUT-VALUES")
        sides = arms_of(roster, column, HOLDOUT_LEVELS)
        return HoldoutPlan(
            train=tuple(u.key for u in sides[HOLDOUT_LEVELS[0]]),
            test=tuple(u.key for u in sides[HOLDOUT_LEVELS[1]]),
            seed=None,
            strata=(),
        )
    if method == "random":
        frac = block_map.get("frac")
        if (
            not isinstance(frac, (int, float))
            or isinstance(frac, bool)
            or not 0.0 < float(frac) < 1.0
        ):
            raise NotImplementedError(
                "`data.units.holdout.method: random` declares no usable `frac`; "
                "`validate` refuses this as `E-DATA-HOLDOUT-FRAC`"
            )
        weights = [1.0 - float(frac), float(frac)]
        rng = random.Random(seed)
        train_keys: list[str] = []
        test_keys: list[str] = []
        if strata:
            # One generator across every stratum, `assignment_for`'s own
            # convention: the strata are drawn in roster order from one carried
            # state, so the seed determines the whole split together rather
            # than each stratum in isolation. `_stratum_groups` is handed no
            # `resolved`: a holdout's `stratify_by` admits only a unit
            # attribute, never a `sweep.groups` axis (§ Validation,
            # *Stratification attribute exists*), and a holdout beside a group
            # axis is refused outright as `E-DATA-HOLDOUT-CELLS`.
            groups = _stratum_groups(list(roster), strata, "data.units.holdout.stratify_by")
            for stratum_units in groups.values():
                if clusters is not None:
                    # Whole clusters inside each stratum — sound only while
                    # `E-DATA-HOLDOUT-STRATIFY-VARIES` refuses a cluster
                    # carrying two stratum values, which would belong to two of
                    # these groups and be divided here. The identical argument
                    # `assignment_for` makes for the identical composition.
                    train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                        stratum_units, weights, rng, clusters
                    )
                    train_keys.extend(u.key for u in train_bucket)
                    test_keys.extend(u.key for u in test_bucket)
                else:
                    keys = [u.key for u in stratum_units]
                    rng.shuffle(keys)
                    cut, _rest = holdout_sizes(len(stratum_units), float(frac))
                    train_keys.extend(keys[:cut])
                    test_keys.extend(keys[cut:])
        elif clusters is not None:
            train_bucket, test_bucket = _assign_whole_clusters_by_ratio(
                list(roster), weights, rng, clusters
            )
            train_keys.extend(u.key for u in train_bucket)
            test_keys.extend(u.key for u in test_bucket)
        else:
            train_size, test_size = holdout_sizes(len(roster), float(frac))
            keys = [unit.key for unit in roster]
            rng.shuffle(keys)
            train_keys.extend(keys[:train_size])
            test_keys.extend(keys[train_size:])
        # Coverage over the MERGED draw, never per stratum — `assignment_for`'s
        # rule for the identical composition: a side a small stratum
        # apportioned nothing is fine while another stratum covered it, and
        # only a side empty across the whole draw leaves one half of the split
        # with no units. Also the one refusal the unclustered and clustered
        # paths share: with clusters larger than one, a cluster is a bigger
        # thing to move than a unit, which is why a clustered draw reaches an
        # empty side more easily rather than being exempt from the refusal —
        # a claim this docstring does not extend to singleton clusters, where
        # the two constructions' realized sizes can disagree in either
        # direction (see the paragraph above).
        if not train_keys or not test_keys:
            side = "train" if not train_keys else "test"
            raise ContractError(
                f"`data.units.holdout.frac: {frac}` over {len(roster)} resolved units "
                f"leaves the {side} side empty"
                + (f", drawn within {len(strata)} stratum declaration(s)" if strata else "")
                + (" over whole clusters" if clusters is not None else "")
                + ". Every split needs both sides — the training side has nothing to fit "
                "on, or the test side has nothing to report over; widen or narrow "
                "`frac`, stratify on fewer attributes, or resolve a larger roster",
                code="E-DATA-HOLDOUT-EMPTY",
            )
        return HoldoutPlan(train=tuple(train_keys), test=tuple(test_keys), seed=seed, strata=strata)
    raise NotImplementedError(
        f"`data.units.holdout.method: {method!r}` is not realized here — the methods "
        f"this build draws are {', '.join(HOLDOUT_METHODS_REALIZED)}. `validate` "
        "refuses an out-of-enum method as `E-DATA-HOLDOUT-METHOD` before a run reaches "
        "this, and an allowlist is what keeps a method added to that enum and to "
        "nothing else from validating clean and then partitioning on something core "
        "never drew"
    )


def auto_block_size(weights: Sequence[float]) -> int:
    """`block_size: "auto"`'s resolved value for `assign.<axis>.method: blocked` —
    `reference.md` § Allocation: twice `ratio`'s sum, rounded to a whole number of
    units.

    **The single producer of this value, imported by `validate._check_assign`
    rather than recomputed there** — the same reason `DRAWN_ASSIGN_METHODS` lives
    in this module and not in `validate`: two independent copies of one formula
    are pinned in agreement by nothing, and a run whose `validate` pass approved
    a `block_size` its own draw then computes differently is exactly the
    validate-clean-then-disagree gap this whole slice exists to close. Task 7's
    `ArmPlan`/`assignment_for` seam makes the identical argument for "which units
    are in this arm"; this is the same argument for one number inside that draw.

    `round`, not a bare `2 * sum(weights)`: a fractional `ratio` (any finite
    positive `float` is a "usable" share, `validate._usable_ratio_share`) makes
    the sum, and so twice the sum, a `float` too — `assignment_for`'s
    `range(0, len(keys), block_size)` requires an `int` step and raises a bare
    `TypeError` on one. `max(1, ...)` keeps the result a legal, positive step
    even for a sum under `0.5`, however implausible a config that draws one is.

    **Does not guarantee every level's per-block share is whole** — no finite
    `block_size` can, for shares that aren't commensurate rationals
    (`{a: 0.33, b: 0.33, c: 0.34}` is `reference.md`'s own example: this
    resolves to `2`, and none of the three levels' shares of `2` are whole).
    `validate._check_assign` runs the same whole-share check against this
    value that it runs against a declared one, so that case is refused before
    a run reaches `assignment_for` at all; a caller that bypasses `validate`
    and reaches the draw anyway gets `_apportion`'s ordinary largest-remainder
    tolerance, the same one an unclustered `random` draw already gets for a
    `ratio` that doesn't divide the roster evenly — up to and including a
    level starved in every block, which still raises `E-DATA-ASSIGN-LEVELS`
    rather than silently misallocating.
    """
    return max(1, round(2 * sum(weights)))


def stratum_names(stratify_by: Any) -> tuple[str, ...]:
    """A `stratify_by` declaration's names, normalized to a tuple — shared by
    `assign.<axis>.stratify_by` and `statistics.resample.stratify_by`, and
    written against neither in particular.

    **Presence and shape are read structurally**, `validate`'s own convention for
    this field and the one the refusal this replaces already used: a bare
    `stratify_by: site` names one stratum exactly as `[site]` does, so a draw
    written against `isinstance(x, list)` cannot silently ignore the bare form
    while `validate` reports it as non-empty. An absent, `None`, or empty
    declaration is `()`, which is what `init` writes and what sends a draw down
    its unstratified path.

    Entries are returned as declared, without a type test: a non-string entry
    names no unit attribute, which is the one thing `_stratum_groups` below
    checks, and folding it in there keeps one raise rather than two for the same
    fault. `validate` refuses it before a run reaches here, as
    `E-DATA-ASSIGN-STRATIFY-UNKNOWN`.

    **Public, and imported by `validate._check_assign` and
    `validate._check_resample` rather than re-read there** — `auto_block_size`'s
    own reason, one field over: `validate`'s *Allocation strata exist* and
    *Resample strata exist* rows each check the names this returns. `assign`'s
    own draw already balances on the names this returns; a resample draw is
    built (`stats.percentile_over_units`'s stratified branch) but, as of
    commit `2fdc957` (H4a task 12), still not wired to a config's declaration
    — `cli.command_run` did not yet resolve `statistics.resample` into a call
    here. Check `cli.command_run` directly for whether that wiring has since
    landed; whenever it does, it has to read the same declaration this way
    too, or two independent readings of one declaration would be pinned in
    agreement by nothing. A bare string read as one name
    here and as a sequence of characters there is exactly the
    validate-clean-then-disagree shape that costs.
    """
    if not stratify_by:
        return ()
    if isinstance(stratify_by, str):
        return (stratify_by,)
    if isinstance(stratify_by, (list, tuple)):
        return tuple(stratify_by)
    return (stratify_by,)


def _stratum_groups(
    units: list[Unit],
    names: Sequence[Any],
    declaration: str,
    resolved: Mapping[str, ArmPlan] | None = None,
) -> dict[tuple[str, ...], list[Unit]]:
    """The roster split into strata — one entry per distinct combination of the
    declared `stratify_by` values, each holding its units in roster order.

    Insertion order is roster order, `clusters_of`'s convention and for its
    reason: the draw walks these groups in turn from one seeded generator, so the
    order they come out in is part of what the seed determines. Deriving it a
    second way — sorting the keys, say — would make the same seed draw a
    different allocation for the same roster.

    Values are stringified, again `clusters_of`'s reason: a stratum is a label
    rather than a quantity, and a table yields `str` for every column while a
    hand-built roster need not. A unit carrying no value for one of the names is
    rendered `no value` and forms its own stratum with the other units that carry
    none — `stratum_varies_within_cluster`'s own rendering for the same absence,
    so the two agree about what a unit with no value is rather than one treating
    it as a stratum and the other as a fault.

    **A name may also be an earlier `sweep.groups` axis, and `resolved` is what
    reads it** — the mapping of the axes whose plans are *already drawn*, keyed
    by axis name, which is `reference.md` § Expansion modes' "axes resolve in
    declaration order, and `stratify_by` may name a group axis declared before
    it" realized rather than merely permitted. Such a stratum is that axis's
    **realized membership**: a unit's value is the level of `resolved[name]`
    whose members hold it, so `assign.arm.stratify_by: [sex]` balances `arm`
    *within each `sex` arm that was just drawn*. There is no column to read —
    a drawn axis leaves none — which is exactly why the earlier axis's plan has
    to arrive here, and why the sequencing is the feature rather than a check on
    one.

    **Precedence: a name the roster carries as an attribute is an attribute**,
    even when a `sweep.groups` axis shares the name, and `validate`'s *Allocation
    strata exist* row exempts a declared attribute in the same order. The two
    read the same declaration from opposite sides — this one from the resolved
    units, that one from `data.units.attributes` — so the one corner where they
    could disagree is a name declared as an attribute that no resolved unit
    carries: a roster already broken, which this function then reads as the axis
    if one is resolved and refuses below if none is.

    **Every other name raises `NotImplementedError`** — a stratum this build
    cannot read, which is a different thing from the per-unit absence above and
    must not be drawn as one "no value" stratum. Both declarations that reach it
    are refused by `validate` first, and the message names both because the
    raise cannot tell them apart from its arguments alone: a name nothing
    declares (`E-DATA-ASSIGN-STRATIFY-UNKNOWN`) and an axis declared *after*
    this one, so not yet drawn and not in `resolved`
    (`E-DATA-ASSIGN-STRATIFY-FORWARD`). It stays a bare `NotImplementedError`
    rather than a coded `ContractError` for that reason: a code here would have
    to name one of the two faults and would be wrong for the other, which is the
    same "one code answering to two § Validation rows" the two codes were split
    to avoid.

    **A caller whose `resolved` plan was built from a different roster** — a unit
    no level of it holds — renders as `no value`, the attribute path's own
    convention for the same absence. Unreachable through `assignment_for`'s two
    producers, which both partition the whole roster they are given.

    **`declaration` is the full dotted path of the declaration being served**,
    not an axis name: this function has more than one caller and the message it
    raises names the config path a reader has to go and fix. An axis name
    interpolated into a fixed `data.units.assign.<...>` template would print
    `data.units.assign.holdout.stratify_by` for a holdout — a path no config
    can hold. **The tail of the "every other name" raise is caller-aware too**:
    a holdout's `stratify_by` admits only a unit attribute — no already-drawn
    `sweep.groups` axis, since `E-DATA-HOLDOUT-CELLS` refuses a holdout beside
    a group axis outright — so a holdout reader is sent to
    `E-DATA-HOLDOUT-STRATIFY-UNKNOWN` and told nothing about a forward
    declaration or a `sweep.groups` path their declaration cannot take.
    """
    plans = resolved or {}
    sources: list[Mapping[str, str] | None] = []
    for name in names:
        if any(isinstance(name, str) and name in unit.attributes for unit in units):
            sources.append(None)  # read per unit, off the attribute
            continue
        if isinstance(name, str) and name in plans:
            plan = plans[name]
            sources.append({key: level for level, keys in plan.members.items() for key in keys})
            continue
        if declaration.startswith("data.units.holdout"):
            raise NotImplementedError(
                f"`{declaration}` names {name!r}, which no resolved unit carries "
                "as an attribute — a holdout's `stratify_by` admits only a unit "
                "attribute, never a `sweep.groups` axis (a holdout beside one is "
                "refused outright, as `E-DATA-HOLDOUT-CELLS`), so there is no "
                "forward-declared axis this could instead be naming. `validate` "
                "refuses this as `E-DATA-HOLDOUT-STRATIFY-UNKNOWN`"
            )
        raise NotImplementedError(
            f"`{declaration}` names {name!r}, which no resolved "
            "unit carries as an attribute and no already-drawn `sweep.groups` axis "
            "resolves — a stratum is read per unit when the draw is balanced. A stratum "
            "naming an axis declared AFTER this one names membership no draw has "
            "realized yet, and `validate` refuses it as "
            "`E-DATA-ASSIGN-STRATIFY-FORWARD`; a stratum naming nothing at all is "
            "refused as `E-DATA-ASSIGN-STRATIFY-UNKNOWN`"
        )

    def value(unit: Unit, name: Any, source: Mapping[str, str] | None) -> str:
        if source is not None:
            return source.get(unit.key, "no value")
        raw = unit.attributes.get(name)
        return "no value" if raw is None else str(raw)

    groups: dict[tuple[str, ...], list[Unit]] = {}
    for unit in units:
        key = tuple(value(unit, name, source) for name, source in zip(names, sources, strict=True))
        groups.setdefault(key, []).append(unit)
    return groups


def _blocked_draw(
    keys: list[str],
    levels: Sequence[str],
    weights: Sequence[float],
    block_size: int,
    rng: random.Random,
    drawn: dict[str, list[str]],
) -> None:
    """One list of unit keys cut into consecutive blocks of `block_size` and
    dealt into `drawn`, each block apportioned by `weights` and permuted with
    `rng`.

    Extracted so the stratified draw is the **same** block loop run once per
    stratum rather than a second implementation of blocking — the argument
    `_assign_whole_clusters` makes for folds, one level down. `rng` is passed in
    rather than seeded here for the same reason its own caller states: one
    generator's state carries from block to block, and now from stratum to
    stratum, so the seed determines every block's permutation together rather
    than each in isolation.

    Accumulates into `drawn` instead of returning a mapping, so the unstratified
    path (one call) and the stratified one (one call per stratum) merge
    identically, and the coverage check that follows reads one dict either way.
    """
    for start in range(0, len(keys), block_size):
        chunk = keys[start : start + block_size]
        counts = _apportion(len(chunk), weights)
        block_labels: list[str] = []
        for level, count in zip(levels, counts, strict=True):
            block_labels.extend([level] * count)
        rng.shuffle(block_labels)
        for key, label in zip(chunk, block_labels, strict=True):
            drawn[label].append(key)


def assignment_for(
    roster: UnitList,
    axis: str,
    block: Mapping[str, Any] | None,
    levels: Sequence[str],
    digest: str,
    clusters: Mapping[str, str] | None = None,
    resolved: Mapping[str, ArmPlan] | None = None,
) -> ArmPlan:
    """One axis's allocation, realized — **the single producer** of an `ArmPlan`,
    and the seam this whole slice turns on.

    A **pure function of its arguments**, deliberately: `validate` has to ask
    "which units are in this arm" of the same declaration `cli.command_run`
    asks it of (the cell and stratum checks), so the draw cannot live in the
    runner. Two callers, one answer, computed the same way from the same
    inputs — the property that makes a `between` design `validate` approved
    one core can actually build.

    Dispatches on `block["method"]`, `reference.md` § Allocation's own enum:

    - `by_attribute` (and an absent, non-mapping, or method-less block, which
      `validate._check_assign` falls back to the same way) reads the arm out
      of a column, through `arms_of` **unchanged** — that function stays the
      authority for a column-read partition and this one does not re-derive
      it. `from` is resolved here, once: the declared `from` when it is a
      non-empty string, else the axis name.
    - `random`, unstratified (no non-empty `stratify_by`), draws one — see
      below, whole clusters when `clusters` is given and individual units
      when it is `None`.
    - `blocked`, unstratified and unclustered (`clusters is None`), draws one
      too — see below. `blocked` beside a declared `cluster_by` raises
      `NotImplementedError` rather than realizing it: a block fills to an
      exact unit count and a cluster is indivisible, so no block size honours
      both, and `validate` refuses the combination outright as
      `E-DATA-ASSIGN-BLOCKED-CLUSTER` (task 11) — this build does not
      implement the combination at all rather than silently picking one rule
      over the other.
    - **Every other value raises `NotImplementedError`** — an allowlist, not a
      denylist of the methods that happen to draw today. Fail-closed costs
      nothing here, because `validate` already refuses an
      out-of-enum method outright (`E-DATA-ASSIGN-METHOD`) before `run` can
      reach this — and it is what keeps a *fifth* method, added to
      `validate.ASSIGN_METHODS` and to nothing else, from validating clean
      and then silently partitioning on a column. A denylist would have
      shipped exactly that regression, since the two literals naming which
      methods draw would have been pinned in agreement by nothing.

    An explicit hole, not a silent fallback to reading a column that need not
    exist: a drawn axis's units carry no arm attribute, so a fallback would
    either raise `E-DATA-ASSIGN-LEVELS` about a column nobody declared or,
    worse, partition on an unrelated one.

    `digest`, `clusters` and `resolved` are unread on the `by_attribute` path
    and are parameters anyway: `resolved` is how a stratum naming an earlier
    group axis reads that axis's realized membership (below), `digest` is what
    `random` draws its seed with
    (`assign_seed_for(block, axis, digest, roster)`, below), and `clusters`
    is what `random`'s clustered draw allocates whole clusters with instead
    of individual units — a caller that already has to hold both cannot then
    be told the signature changed under it.

    **`random`, unclustered (`clusters is None`), is realized here.**
    `assign.<axis>.ratio` (`{}` meaning equal allocation, `reference.md` §
    Allocation) is apportioned across `len(roster)` by `_apportion`, the
    whole roster is shuffled once with `random.Random(assign_seed_for(...))`,
    and the shuffled list is cut into consecutive slices sized by that
    apportionment, in `levels`' declared order — so `members[level]` holds
    that level's slice **in the order the shuffle realized**, exactly what
    `ArmPlan.members` promises for a draw. Every declared level is a key of
    `members`, and **every one of them is non-empty** — the `zip` below
    walks `levels` itself, so `set(members) == set(levels)` unconditionally,
    and an apportioned size of 0 raises `E-DATA-ASSIGN-LEVELS` rather than
    returning an empty tuple. A caller therefore gets from a draw exactly the
    partition `arms_of` promises for a read: both halves, coverage and
    non-emptiness. **The same fault deserves the same code**: `arms_of`
    refuses "a declared level no unit's value names — that arm's condition
    would resolve zero units", and an arm the ratio apportioned zero units to
    is that sentence, one line later. `reference.md` § Allocation states it
    method-agnostically ("An arm no unit resolves to is already refused, as
    `E-DATA-ASSIGN-LEVELS`"), in the sentence whose job is to contrast it
    with the thin-but-nonzero cell `limits.min_units_per_cell` does not yet
    warn about — a warning-shaped gap a hard refusal must not be routed into.

    **`random`, clustered (`clusters is not None`), goes through
    `_assign_whole_clusters_by_ratio` instead** — a sibling of the fold
    primitive `_assign_whole_clusters`, not a parameterization of it, because
    the two answer different questions: a fold deals whole clusters to the
    *least-loaded* of `k` **equal** buckets, where an unequal
    `assign.<axis>.ratio` needs the bucket **furthest below its own target
    share**, which is the same rule only when every share is equal.
    `reference.md` § Clustered units states the requirement this realizes:
    "core computed the partition, so core keeps it indivisible" — a cluster
    is drawn as a whole, so arms are balanced over clusters and no cluster
    straddles two arms. The realized sizes are **not** the exact `ratio`:
    a cluster is the smallest thing that can move, so one large cluster sets
    a floor no assignment can get under, the same argument `partition_units`
    makes for folds. An arm the draw allocates no whole cluster to is the
    same fault as the unclustered path's zero-size arm and raises the same
    code, `E-DATA-ASSIGN-LEVELS` — a coarser unit of movement makes it
    *easier* to reach, not exempt from the refusal.

    **A non-empty `assign.<axis>.stratify_by` is realized under both drawing
    methods**, whether or not `clusters` is given: the roster is split into
    strata by `_stratum_groups` — one group per distinct combination of the
    declared attributes' values, in roster order — and the method's own draw
    runs **inside each group** from one carried generator, so each arm gets
    its ratio's share of every stratum rather than only of the roster.
    Presence and shape are read structurally, `validate`'s own convention for
    this field: a bare `stratify_by: site` names one stratum exactly as
    `[site]` does, and the empty `stratify_by: []` that `init` writes leaves
    both draws on their unstratified paths unchanged, bit for bit. `strata`
    on the returned plan is the declaration realized, in declared order.

    **Arm sizes can therefore differ by more than one**, and the deviation is
    bounded by the number of strata rather than by one unit — `_apportion`
    runs once per stratum, its one-unit tolerance applies inside each, and the
    floors add. Three strata of five units at an equal two-arm ratio give 3/2
    in every stratum, so 9/6 overall where the unstratified draw of the same
    roster gives 8/7, and the surplus lands on the first-declared level every
    time, since that is how `_apportion` breaks a tie. `partition_units` states
    the identical consequence for stratified folds; it is the prescribed rule's
    arithmetic rather than a defect, and balancing the totals *across* strata is
    what would unbalance the thing `stratify_by` was declared to balance.

    **Coverage is checked over the merged draw, never per stratum** — the
    rule `blocked` already applies per block, one construction over: a level
    a small stratum apportioned no unit to is fine while another stratum
    covered it, and only a level empty across every stratum raises
    `E-DATA-ASSIGN-LEVELS`. So a stratified draw can no more return an empty
    arm than an unstratified one can.

    **A stratum may name an earlier `sweep.groups` axis, and `resolved` is
    the only way to read one** — the mapping of axis name to the plan
    *already drawn* for it, which `cli._resolved_group_axes` accumulates as
    it walks the declared axes in order. A drawn axis leaves no column, so
    balancing on it means balancing on its realized membership, and that
    membership can only come from the plan: `assign.arm.stratify_by: [sex]`
    puts each unit in the `sex` arm the earlier draw actually gave it and
    apportions `arm` inside each. **This is a sequencing requirement rather
    than a check** — `reference.md` § Expansion modes' "axes resolve in
    declaration order, and `stratify_by` may name a group axis declared
    before it" — and what makes the order load-bearing rather than
    incidental is that an axis whose stratum is not yet in `resolved` cannot
    be drawn at all: it raises here, where a caller that reordered the axes
    would otherwise have silently drawn a different allocation.

    **A stratum name that is neither carried by a resolved unit nor an
    already-drawn axis raises `NotImplementedError`** rather than being
    drawn as a single "no value" stratum — see `_stratum_groups`, which
    distinguishes that from a unit here or there carrying no value, names
    the two declarations that reach it (a later axis,
    `E-DATA-ASSIGN-STRATIFY-FORWARD`; a name nothing declares,
    `E-DATA-ASSIGN-STRATIFY-UNKNOWN`, both refused by `validate` first) and
    says why it carries neither code itself.

    **An axis-name stratum beside a declared `cluster_by` is refused where it
    would split a cluster, and the refusal is `validate`'s.** When the earlier
    axis *draws*, it allocated whole clusters, so its realized membership is
    constant within every cluster by construction and there is nothing to
    refuse. When the earlier axis is `by_attribute` with a `from` naming a
    column that is **not** constant within a cluster, it splits that cluster
    between its own arms — `arms_of` reads a column and respects nothing
    about clusters — and the two halves would land in different strata here,
    where `_assign_whole_clusters_by_ratio` would allocate each independently
    and the cluster would straddle both arms of this axis too. That is a
    measured outcome rather than a hypothetical, and it contradicts
    `reference.md` § Clustered units' "core computed the partition, so core
    keeps it indivisible", so `validate._check_assign` reads such a stratum
    through the column its axis reads (`_read_axis_column`) and reports
    `E-DATA-ASSIGN-STRATIFY-VARIES` — the same code, and the same row, an
    attribute stratum earns. It needs a `from` differing from the axis name to
    arise at all: with the default, the stratum resolves as a declared
    attribute on both sides and the attribute half of that check covers it.

    **`blocked` is realized here too, and is what reads the roster's order
    as data** (`reference.md` § Where units come from): the resolved roster
    is cut into consecutive chunks of `assign.<axis>.block_size` units —
    `"auto"` (or any declared value that isn't a plain `int`) resolving to
    twice `ratio`'s sum, `validate`'s own whole-multiple rule keeping an
    explicit value a multiple of that sum so every *whole* block fills each
    arm exactly. Each chunk, including a final one shorter than
    `block_size` when the roster doesn't divide evenly, is apportioned by
    the same `_apportion` `random` uses, turned into a label list (each
    level repeated its apportioned count of times) and shuffled *in place*
    with one `random.Random(assign_seed_for(...))` instance whose state
    carries from block to block — so the seed determines every block's
    permutation together, not each in isolation — then zipped onto the
    chunk's units in roster order. Reordering the roster therefore changes
    which units share a block and so changes the draw, where `random`'s
    single whole-roster shuffle does not carry any such structure for a
    reorder to disturb. Coverage and non-emptiness are checked the same way
    across the *whole* roster, not per block: a level with at least one
    unit in some block is fine even if another block apportioned it none,
    and only a level with zero units in *every* block raises
    `E-DATA-ASSIGN-LEVELS` — the same code and the same argument as
    `random`'s zero-size arm, one whole roster later. A declared
    `stratify_by` runs that same block loop once per stratum, `random`'s own
    composition above; whole clusters stay unrealized under `blocked`,
    refused for the reason given there.
    """
    # One narrowing of the block, read by every branch below: an absent or
    # non-mapping block declares nothing, which is what `{}` says here — and
    # what sends it down the `by_attribute` path, `validate._check_assign`'s
    # own fallback. Bound once so no branch repeats the `isinstance` test as a
    # guard that reads like a second condition on the method.
    block_map: Mapping[str, Any] = block if isinstance(block, Mapping) else {}
    method = block_map.get("method")
    # The declared strata, normalized once for both drawing branches: an empty
    # declaration is `()` and leaves each branch on the path it had before
    # stratification existed, bit for bit.
    strata = stratum_names(block_map.get("stratify_by"))
    if method == "random":
        ratio = block_map.get("ratio")
        weights = (
            [ratio[level] for level in levels]
            if isinstance(ratio, dict) and ratio
            else [1] * len(levels)
        )
        seed = assign_seed_for(block_map, axis, digest, roster)
        if strata:
            # One generator across every stratum, `blocked`'s own convention:
            # the strata are drawn in roster order from one carried state, so
            # the seed determines the whole allocation together rather than
            # each stratum in isolation.
            stratified_rng = random.Random(seed)
            stratified: dict[str, list[str]] = {level: [] for level in levels}
            groups = _stratum_groups(
                list(roster), strata, f"data.units.assign.{axis}.stratify_by", resolved
            )
            for stratum_units in groups.values():
                if clusters is not None:
                    # The same whole-cluster rule the unstratified clustered
                    # draw uses, run inside each stratum. Sound only while
                    # `stratum_varies_within_cluster` refuses the pair it
                    # refuses — a cluster carrying two stratum values would
                    # belong to two of these groups and be divided here —
                    # which is the argument `partition_units` makes for the
                    # identical composition over folds, and the reason
                    # `reference.md` § Validation's *Allocation strata survive
                    # clustering* row exists.
                    for level, bucket in zip(
                        levels,
                        _assign_whole_clusters_by_ratio(
                            stratum_units, weights, stratified_rng, clusters
                        ),
                        strict=True,
                    ):
                        stratified[level].extend(unit.key for unit in bucket)
                else:
                    stratum_keys = [unit.key for unit in stratum_units]
                    stratified_rng.shuffle(stratum_keys)
                    offset = 0
                    for level, size in zip(
                        levels, _apportion(len(stratum_units), weights), strict=True
                    ):
                        stratified[level].extend(stratum_keys[offset : offset + size])
                        offset += size
            # Coverage over the MERGED draw, not per stratum — `blocked`'s rule
            # for the same question one construction over: a level a small
            # stratum apportioned no unit to is fine while another stratum
            # covered it, and only a level empty across every stratum leaves an
            # arm resolving zero units. So an empty arm is refused here under
            # the same code and the same words either draw refuses one with,
            # and no plan this returns holds an empty level.
            empty = [level for level in levels if not stratified[level]]
            if empty:
                raise ContractError(
                    f"the drawn allocation for axis {axis!r} leaves no unit in "
                    f"{', '.join(empty)} — {len(roster)} units in {len(groups)} strata of "
                    f"{', '.join(str(name) for name in strata)}, apportioned within each "
                    "stratum by "
                    f"{dict(ratio) if isinstance(ratio, dict) and ratio else 'equal shares'}"
                    ", gives that level no unit in any stratum. Every declared level needs "
                    "at least one unit, or that arm's condition resolves zero of them; "
                    "widen the ratio, stratify on fewer attributes, or resolve a larger "
                    "roster",
                    code="E-DATA-ASSIGN-LEVELS",
                )
            return ArmPlan(
                levels=tuple(levels),
                members={level: tuple(keys_) for level, keys_ in stratified.items()},
                seed=seed,
                strata=strata,
            )
        if clusters is not None:
            rng = random.Random(seed)
            buckets = _assign_whole_clusters_by_ratio(list(roster), weights, rng, clusters)
            empty = [level for level, bucket in zip(levels, buckets, strict=True) if not bucket]
            if empty:
                cluster_total = len({clusters[unit.key] for unit in roster})
                raise ContractError(
                    f"the drawn allocation for axis {axis!r} leaves no unit in "
                    f"{', '.join(empty)} — {cluster_total} whole clusters apportioned by "
                    f"{dict(ratio) if isinstance(ratio, dict) and ratio else 'equal shares'} "
                    "gives that level no whole cluster. Every declared level needs at least "
                    "one unit, or that arm's condition resolves zero of them; widen the "
                    "ratio, resolve more clusters, or read an arm already assigned",
                    code="E-DATA-ASSIGN-LEVELS",
                )
            clustered_members: dict[str, tuple[str, ...]] = {
                level: tuple(unit.key for unit in bucket)
                for level, bucket in zip(levels, buckets, strict=True)
            }
            return ArmPlan(levels=tuple(levels), members=clustered_members, seed=seed, strata=())
        sizes = _apportion(len(roster), weights)
        empty = [level for level, size in zip(levels, sizes, strict=True) if size == 0]
        if empty:
            raise ContractError(
                f"the drawn allocation for axis {axis!r} leaves no unit in "
                f"{', '.join(empty)} — {len(roster)} units apportioned by "
                f"{dict(ratio) if isinstance(ratio, dict) and ratio else 'equal shares'} "
                "gives that level a share of zero. Every declared level needs at least "
                "one unit, or that arm's condition resolves zero of them; widen the ratio "
                "or resolve a larger roster",
                code="E-DATA-ASSIGN-LEVELS",
            )
        shuffled = [unit.key for unit in roster]
        random.Random(seed).shuffle(shuffled)
        members: dict[str, tuple[str, ...]] = {}
        start = 0
        for level, size in zip(levels, sizes, strict=True):
            members[level] = tuple(shuffled[start : start + size])
            start += size
        return ArmPlan(levels=tuple(levels), members=members, seed=seed, strata=())
    if method == "blocked":
        if clusters is not None:
            raise NotImplementedError(
                f"`data.units.assign.{axis}.method: blocked` beside a declared `cluster_by` "
                "is not realized here — a block fills to an exact unit count and a cluster "
                "is indivisible, so no block size honours both. `validate` refuses this "
                "combination outright, as `E-DATA-ASSIGN-BLOCKED-CLUSTER`; use `random` for "
                "a cluster-randomized design"
            )
        ratio = block_map.get("ratio")
        weights = (
            [ratio[level] for level in levels]
            if isinstance(ratio, dict) and ratio
            else [1] * len(levels)
        )
        declared_block_size = block_map.get("block_size", "auto")
        block_size = (
            declared_block_size
            if isinstance(declared_block_size, int) and not isinstance(declared_block_size, bool)
            # `auto_block_size`, not a second copy of its formula: `validate`
            # imports the same function so the value it approves and the value
            # this draw uses can never drift apart — see that function's own
            # docstring for why a `ratio` that makes it unable to give every
            # level a whole per-block share is refused there before a run
            # reaches here at all, and what this module does when a caller
            # bypasses `validate` and reaches it anyway.
            else auto_block_size(weights)
        )
        seed = assign_seed_for(block_map, axis, digest, roster)
        rng = random.Random(seed)
        drawn: dict[str, list[str]] = {level: [] for level in levels}
        if strata:
            # The same block loop, run once per stratum in roster order and
            # from the one carried generator — permuted blocks *within* each
            # stratum, which is what a stratified block design is. Cutting the
            # whole roster into blocks and balancing each block's strata
            # instead would be a different design and a second blocking rule.
            for stratum_units in _stratum_groups(
                list(roster), strata, f"data.units.assign.{axis}.stratify_by", resolved
            ).values():
                _blocked_draw(
                    [unit.key for unit in stratum_units],
                    levels,
                    weights,
                    block_size,
                    rng,
                    drawn,
                )
        else:
            _blocked_draw([unit.key for unit in roster], levels, weights, block_size, rng, drawn)
        empty = [level for level in levels if not drawn[level]]
        if empty:
            declaration = f"data.units.assign.{axis}.stratify_by"
            within = (
                f" within each of the "
                f"{len(_stratum_groups(list(roster), strata, declaration, resolved))} "
                f"strata of {', '.join(str(name) for name in strata)}"
                if strata
                else ""
            )
            raise ContractError(
                f"the drawn allocation for axis {axis!r} leaves no unit in "
                f"{', '.join(empty)} — {len(roster)} units, blocked in groups of "
                f"{block_size}{within} and apportioned within each block by "
                f"{dict(ratio) if isinstance(ratio, dict) and ratio else 'equal shares'}, "
                "gives that level no unit across every block. Every declared level needs at "
                "least one unit, or that arm's condition resolves zero of them; widen the "
                "ratio, shrink the block, or resolve a larger roster",
                code="E-DATA-ASSIGN-LEVELS",
            )
        blocked_members: dict[str, tuple[str, ...]] = {
            level: tuple(keys_) for level, keys_ in drawn.items()
        }
        return ArmPlan(levels=tuple(levels), members=blocked_members, seed=seed, strata=strata)
    if method is not None and method != "by_attribute":
        # `method in DRAWN_ASSIGN_METHODS` is not checked here: both of that tuple's
        # members (`random`, `blocked`) are handled in their own branches above, so
        # nothing reaches this point already knowing which method it is — everything
        # that does is a method this build has no branch for at all, `by_attribute`'s
        # allowlist failing closed rather than falling back to a column read.
        raise NotImplementedError(
            f"`data.units.assign.{axis}.method: {method!r}` is not a method this build can "
            "realize an allocation for; `by_attribute` is the one it reads a column for, and "
            "no other method may fall back to reading one (`validate` refuses an out-of-enum "
            "method as `E-DATA-ASSIGN-METHOD`)"
        )
    declared_from = block_map.get("from")
    column = declared_from if isinstance(declared_from, str) and declared_from else axis
    partition = arms_of(roster, column, levels)
    return ArmPlan(
        levels=tuple(levels),
        members={level: tuple(u.key for u in units) for level, units in partition.items()},
        seed=None,
        strata=(),
    )


def arm_members(
    axes: Mapping[str, ArmPlan],
    conditions: "Sequence[Any]",
) -> dict[int, frozenset[str]]:
    """Which units each resolved condition's own arm holds — the reduction the
    runner's subset view is built from, so a condition on a group axis is
    handed a real subset of the shared roster and not a second resolution of
    it.

    `axes` maps a group axis name to that axis's realized `ArmPlan`, one plan
    per declared axis, produced by `assignment_for` — **not** a roster and a
    column. This function takes no roster at all, and that absence is the
    point: with nothing to read membership *from*, no future edit here can
    quietly become the second producer of it. Its whole job is to intersect
    plans across the axes a condition selects.

    `conditions` is an iterable of objects carrying `.index`, `.values` and
    `.selectors` — `sweep.Condition`'s own shape, read structurally rather than
    imported, since `sweep.py` and `units.py` share no dependency edge today and
    a caller building a lightweight stand-in for a test loses nothing by it.
    `.selectors` names which of `.values`' paths are group cells; a condition
    selecting more than one axis gets the *intersection* of each axis's arm —
    § Validation's `sex × arm` cell — and a condition selecting none is absent
    from the returned mapping entirely, rather than mapped to the whole roster,
    since "no arm" and "every unit" are different claims and only the plan
    itself says which units a real arm holds.

    A caller passing a condition whose selected axis or level is not in `axes`
    — an inconsistency between the two arguments — raises a bare `KeyError`
    rather than falling back to the whole roster: `axes` is meant to cover
    every axis every condition selects, built from the same declarations that
    built the conditions, so a gap here is the caller's own bug to see rather
    than one this function should absorb by handing back units nothing
    verified.
    """
    result: dict[int, frozenset[str]] = {}
    for condition in conditions:
        if not condition.selectors:
            continue
        members: set[str] | None = None
        # `axes[axis]`, not `.get`, and `.members[level]`, not `.get`: `axes` is
        # meant to cover every axis every condition selects, so a selected axis
        # missing from it — or a level the plan didn't realize — is the two
        # arguments disagreeing, a caller bug this function must not paper over
        # by silently dropping the axis from the intersection (which would hand
        # back a *larger*, wrong arm) or the condition from the result (which
        # would hand its execution the whole roster, one level up).
        for axis in condition.selectors:
            level = condition.values[axis]
            keys = set(axes[axis].members[level])
            members = keys if members is None else members & keys
        result[condition.index] = frozenset(members or set())
    return result


def cluster_count_of(membership: Mapping[str, str], keys: Iterable[str]) -> int:
    """How many distinct clusters a given set of unit keys falls in.

    The counting expression, in one place. `cluster_count` below is the whole
    roster's answer and this is the same question asked of a SUBSET — the units a
    metric was actually computed over, which is what `n.clusters` reports
    (`runner._counts`, `stats.summarize_step`). Those callers have no roster to
    hand `cluster_count`: they hold a set of completed keys and the roster-wide
    membership mapping. Writing `len({m[k] for k in keys})` at each of them would
    be the second and third notion of "how many clusters is that", which is the
    thing `clusters_of` exists to prevent one of.

    Indexed rather than `.get`-ed, for the reason `runner._counts` states about
    weights: every key a caller passes came from the roster the membership was
    built from, so a missing one is a core defect and must drop out as a
    `KeyError` rather than being absorbed into a cluster of its own — which would
    quietly *raise* the count and narrow every interval computed from it.
    """
    return len({membership[key] for key in keys})


def cluster_count(roster: UnitList, cluster_by: str) -> int:
    """How many distinct clusters the roster holds.

    Derived from `clusters_of` rather than counted in its own walk: the count is
    what bounds `k` and what a cluster-robust interval's df is computed from, and a
    count that disagreed with the membership it is supposed to summarize would put
    a `k` past the number of groups the partitioner can actually produce.
    """
    membership = clusters_of(roster, cluster_by)
    return cluster_count_of(membership, membership)


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
    decides which declaration to name — **four callers today, under four codes**:
    `E-DATA-ASSIGN-STRATIFY-VARIES`, `E-REPL-FOLD-STRATIFY-VARIES`,
    `E-STATS-RESAMPLE-STRATIFY-VARIES` and `E-DATA-HOLDOUT-STRATIFY-VARIES`,
    answering to `reference.md` § Validation's *Allocation strata survive
    clustering*, *Fold strata survive clustering*, *Resample strata survive
    clustering* and *Holdout strata survive clustering*. That is why this returns
    a fault rather than raising one code: a code chosen here would be right for
    one caller and wrong for three.

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


def _assign_whole_clusters_by_ratio(
    units: list[Unit], weights: Sequence[float], rng: random.Random, clusters: Mapping[str, str]
) -> list[list[Unit]]:
    """One list of units into `len(weights)` arms, each cluster whole, sized as
    close to its own weight's target share as indivisible clusters allow.

    **A sibling of `_assign_whole_clusters`, not a parameterization of it** —
    spec decision 6, `reference.md` § Clustered units: "core computed the
    partition, so core keeps it indivisible." That function deals whole
    clusters to the *least-loaded* of `k` **equal** buckets; "least loaded"
    and "furthest below its own target share" agree only because every
    bucket's share there is identical. An unequal `assign.<axis>.ratio`
    breaks the agreement: a bucket entitled to three times another's share is
    still the one to prefer while it holds fewer than three times as many
    units, not merely while it holds fewer units outright. So the rule here
    is `counts[i] / weights[i]`, argmin, ties to the earlier-declared level —
    a strict generalization that collapses to `_assign_whole_clusters`'s rule
    when every weight is equal, but is a different comparison whenever they
    are not, which is why it is a second function rather than that one
    parameterized: changing the shared one to take weights risks a fold
    regression for an arm feature, a bad trade `_assign_whole_clusters`'s own
    bit-stability oracle exists to catch.

    Dealt in the same order as `_assign_whole_clusters`, for the same
    reasons: shuffled with `rng` to seed the tie between equal-sized
    clusters (the only place it can still matter once the sort is stable),
    then sorted largest-first so a big cluster is never stranded with only
    already-unbalanced buckets left to go to.

    Every realized size can differ from its exact target share (`n * weight
    / sum(weights)`): a cluster is the smallest thing that can move, so a
    bucket's share only ever changes in whole-cluster increments and nothing
    here divides one to correct an overshoot or an undershoot. **No bound on
    that deviation is promised** — `reference.md` § Clustered units makes
    the identical non-promise for folds ("What is not promised is a bound on
    how uneven the result may be"): one cluster larger than a bucket's whole
    target share makes an uneven split unavoidable, in whichever direction
    the greedy order happens to leave that bucket, and core reports the
    realized sizes rather than pretending otherwise.

    **A size of 0 is possible here and is the caller's to refuse**,
    `_apportion`'s own convention: only `assignment_for` holds the axis
    name, the declared `ratio`, and the roster a refusal's message has to
    name, so this stays total rather than raising — **including for a
    non-positive weight**, which `counts[i] / weights[i]` cannot be asked to
    divide by. Such a level is never the argmin while any other level still
    has a positive weight (`float("inf")` outranks every finite quotient),
    so it is dealt no cluster and correctly ends up a size-0 bucket for the
    caller to refuse, rather than a raised `ZeroDivisionError` for the
    caller never to see.
    """
    members: dict[str, list[Unit]] = {}
    for unit in units:
        members.setdefault(clusters[unit.key], []).append(unit)
    order = list(members)
    rng.shuffle(order)
    order.sort(key=lambda name: -len(members[name]))
    counts = [0.0] * len(weights)
    buckets: list[list[Unit]] = [[] for _ in weights]

    def priority(i: int) -> tuple[float, int]:
        # A non-positive weight has no target share to be "below" — `inf`
        # keeps it out of the argmin (and out of a `ZeroDivisionError`)
        # without raising, `_apportion`'s own convention of staying total
        # and leaving the refusal to `assignment_for`.
        share = counts[i] / weights[i] if weights[i] > 0 else float("inf")
        return (share, i)

    for name in order:
        i = min(range(len(weights)), key=priority)
        buckets[i].extend(members[name])
        counts[i] += len(members[name])
    return buckets


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

    **`k` is checked against the whole roster's basis, not against each stratum's,
    and a fold can therefore come out EMPTY — not merely short of one stratum.**
    Each stratum fills only as many folds as it has clusters, and the merge is
    index-wise, so when every stratum has fewer than `k` the high-index folds hold
    **nothing at all**. Six units as three plus three under `{k: all,
    stratify_by: label}` fills folds 0-2 and leaves 3-5 empty: six executions run,
    three of them over no units, `validate` silent because `fold_basis` is 6.
    `_fold_k` refuses that shape by its own route — "a fold with no units is a
    declaration error, not a small fold" — so this is core reaching by one path a
    state it refuses by another. Recorded rather than fixed: the per-stratum bound
    is a check that does not exist, and inventing one here would be a rule no
    document states. **A weaker earlier version of this paragraph said a fold could
    hold none of a *stratum*; that understated it.** The
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


def assign_seed_for(block: Mapping[str, Any], axis: str, digest: str, roster: UnitList) -> int:
    """The seed an `assign` axis draws its allocation with.

    `reference.md` § What `auto` derives from: an axis's `assign.seed` mixes
    "digest + the axis name + the resolved roster" — the digest and the axis
    name because a crossed design (`arm`, `sex`, ...) must not assign every
    axis identically, and `units_hash(roster)` because it covers the roster
    **in resolved order**: two runs that resolved the same units in a
    different sequence did not allocate the same trial (§ Where units come
    from).

    A pinned integer is returned literally, and — the load-bearing half,
    copied from `sweep.sample_seed_for`'s own docstring — **the digest is not
    consulted at all** on that path, only read out of `block`. "Pinning an
    integer is the deliberate act, and the one to take for anything you
    intend to cite," so a pinned assignment must survive a roster that grows,
    shrinks, or reorders, and `hashes.design_digest` strips `assign.<axis>.seed`
    per axis for the same reason: a pinned seed must not move the digest it
    would otherwise be mixed with.
    """
    seed = block.get("seed", "auto")
    if isinstance(seed, int) and not isinstance(seed, bool):
        return seed
    payload = f"{digest}|assign|{axis}|{units_hash(roster)}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def holdout_seed_for(block: Mapping[str, Any], digest: str, roster: UnitList) -> int:
    """The seed `data.units.holdout` draws its split with.

    `reference.md` § What `auto` derives from: a holdout's `seed` mixes "digest
    + the resolved roster" — the digest because the split is a property of the
    design, and `units_hash(roster)` because it covers the roster **in resolved
    order**, so two runs that resolved the same units in a different sequence
    did not draw the same trial (§ Where units come from).

    **Its own suffix, `|holdout`, and not `_seed_from`'s `|folds`.** A holdout
    is not a fold, and the two must not draw the same partition from the same
    digest. They are mutually exclusive declarations at this commit
    (`E-DATA-HOLDOUT-FOLD`), so nothing *observes* a collision — which is the
    argument FOR the suffix rather than against it: relying on a refusal
    elsewhere to keep two derivations apart is how they come to agree by
    accident the moment that refusal moves.

    **Not `assign_seed_for` either**, whose payload carries an axis name a
    holdout does not have. The construction is otherwise copied deliberately:
    the same digest, the same `units_hash`, the same four bytes read big-endian.
    That shape is shared with `assign_seed_for`, and **not** with every drawn
    partition: `_seed_from`'s fold payload carries no `units_hash` at all, and
    `sweep`'s sample seed differs again. Only the resemblance to
    `assign_seed_for` is claimed here.

    A pinned integer is returned literally, and — the load-bearing half, copied
    from `sweep.sample_seed_for`'s own docstring — **the digest is not consulted
    at all** on that path, only read out of `block`. "Pinning an integer is the
    deliberate act, and the one to take for anything you intend to cite," so a
    pinned split must survive a roster that grows, shrinks, or reorders, and
    `hashes.design_digest` strips `holdout.seed` for the same reason: a pinned
    seed must not move the digest it would otherwise be mixed with.

    `bool` is excluded from the pin: `isinstance(True, int)` is `True`, and
    `seed: true` is not a pin — `validate` refuses it as
    `E-DATA-HOLDOUT-SEED`, and honouring it as `1` would record a derived seed
    under a key the config wrote deliberately.
    """
    seed = block.get("seed", "auto")
    if isinstance(seed, int) and not isinstance(seed, bool):
        return seed
    payload = f"{digest}|holdout|{units_hash(roster)}".encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:4], "big")


def units_hash(units: UnitList) -> str:
    """Covers the list in resolved order — two runs that resolved the same units in a
    different sequence did not allocate the same trial."""
    payload = json.dumps(
        [{"key": u.key, "paths": list(u.paths), "attributes": dict(u.attributes)} for u in units],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def index_names(
    units_decl: dict[str, Any], roster: "UnitList | None", reads: tuple[str, ...] = ()
) -> set[str]:
    """The relative paths `input_manifest_policy: hash_index` hashes.

    `reference.md` § Three hashes: "the index and whatever it names". One
    expression over all three sources, because a per-source branch is how one of
    them comes to be left silently unhashed:

    - a **table** names one file and its units name no paths;
    - a **glob** names no file and each unit names the path it was built from;
    - a **resolver** names whatever it read (`ResolverIO.read_paths`) and its
      units name their own payloads — § Where units come from: "the paths the
      resolver read plus the paths its units name, so a unit whose payload the
      resolver never opened still gets that payload hashed".

    A roster that did not resolve still yields the source's own file: the index is
    named by the declaration, not by the roster, and a manifest built beside a
    failed resolution should not silently stop hashing it.
    """
    source = units_decl.get("from")
    named: set[str] = set(reads)
    if isinstance(source, str) and source:
        named.add(source)
    for unit in roster or ():
        named.update(unit.paths)
    return named

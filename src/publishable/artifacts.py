# src/publishable/artifacts.py
"""Scope-aware, atomic, append-only artifacts. docs/reference.md § Steps and artifacts."""

import csv
import hashlib
import io as _io
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from publishable.coercion import coerce_scalars
from publishable.errors import ArtifactError, ArtifactExistsError, ContractError
from publishable.sweep import condition_dir_name

if TYPE_CHECKING:
    from publishable.units import ArmPlan, HoldoutPlan, UnitList

SCOPE_ORDER = {"run": 0, "condition": 1, "repeat": 2, "summary": 3}


def write_atomic(path: Path, data: bytes) -> None:
    """Temp file plus rename, so a crash leaves nothing rather than a half-file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".partial-")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _encode_json(obj: Any) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode()


def _encode_yaml(obj: Any) -> bytes:
    return yaml.safe_dump(obj, sort_keys=False).encode()


def _encode_jsonl(rows: Any) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode()


def _encode_csv(rows: Any) -> bytes:
    rows = list(rows)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    buf = _io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


def _decode_json(data: bytes) -> Any:
    return json.loads(data.decode())


def _decode_yaml(data: bytes) -> Any:
    return yaml.safe_load(data.decode())


def _decode_jsonl(data: bytes) -> Any:
    return [json.loads(line) for line in data.decode().splitlines() if line]


def _decode_csv(data: bytes) -> Any:
    return list(csv.DictReader(_io.StringIO(data.decode())))


def _article(name: str) -> str:
    return "an" if name[0].lower() in "aeiou" else "a"


def _check_column_types(rows: list[dict[str, Any]], columns: list[str]) -> None:
    """Refuse a column mixing incompatible types, naming the column and a unit for each.

    int/float mixing within a column is the deliberate promotion pinned by
    `test_a_mixed_int_and_float_column_promotes_to_float_deliberately` and is not a
    conflict here. Anything else — bool/int, str/int, and so on — is the same
    contract `io.record`'s `values` is already checked against, so it raises the same
    `E-STEP-RETURN-TYPE` a step's return or a template's `aggregate` would.
    """
    for col in columns:
        groups: dict[type, tuple[type, Any]] = {}
        for i, row in enumerate(rows):
            if col not in row:
                continue
            value = row[col]
            if value is None:
                continue
            actual = type(value)
            normalized = float if actual in (int, float) else actual
            if normalized not in groups:
                groups[normalized] = (actual, row.get("unit", f"row {i}"))
        if len(groups) > 1:
            (type_a, unit_a), (type_b, unit_b) = list(groups.values())[:2]
            name_a, name_b = f"{type_a.__name__}", f"{type_b.__name__}"
            raise ContractError(
                f"column {col!r} recorded both {_article(name_a)} {name_a} "
                f"(unit {unit_a!r}) and {_article(name_b)} {name_b} (unit "
                f"{unit_b!r}); io.record's values, a step's return, and a "
                "template's aggregate take the same scalars under the same "
                "coercion, and this build cannot record a column mixing those types",
                code="E-STEP-RETURN-TYPE",
            )


def _encode_parquet(rows: Any) -> bytes:
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = list(rows)
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    _check_column_types(rows, columns)
    table = pa.table({c: [r.get(c) for r in rows] for c in columns})
    buf = _io.BytesIO()
    pq.write_table(table, buf)
    return buf.getvalue()


def _decode_parquet(data: bytes) -> Any:
    import pyarrow as pa
    import pyarrow.parquet as pq

    return pq.read_table(pa.BufferReader(data)).to_pylist()


WRITERS = {
    ".json": _encode_json,
    ".yaml": _encode_yaml,
    ".jsonl": _encode_jsonl,
    ".csv": _encode_csv,
    ".parquet": _encode_parquet,
}

READERS = {
    ".json": _decode_json,
    ".yaml": _decode_yaml,
    ".jsonl": _decode_jsonl,
    ".csv": _decode_csv,
    ".parquet": _decode_parquet,
}

CORE_SUFFIXES = frozenset(WRITERS)
"""The suffixes core itself writes, fixed at import.

Snapshotted rather than read live, because `plugins.register_writer` adds to
`WRITERS` and a shadow check reading the live table would start refusing one
plugin's suffix on behalf of another's. What a plugin may not claim is what
*core* writes, which is a property of this file and not of what is installed.
"""


def _suffix_for(name: str) -> str | None:
    """The longest registered suffix of the name's last component, lower-cased."""
    last = name.rsplit("/", 1)[-1].lower()
    best: str | None = None
    for suffix in WRITERS:
        if last.endswith(suffix) and (best is None or len(suffix) > len(best)):
            best = suffix
    return best


def build_allocation_document(
    group_axes: Mapping[str, "ArmPlan"], holdout: "HoldoutPlan | None" = None
) -> dict[str, Any] | None:
    """`allocation.json`'s payload — `reference.md` § `allocation.json` — who
    went where prints it in full: four top-level keys, `arms`/`seed`/`strata`
    keyed by axis name, `holdout` sharing the file because both are
    partitions of one roster drawn once.

    Returns `None` only when **neither** partition is declared — no arm
    assignment resolved *and* no holdout realized — matching § The other files
    a run writes' "present when either is declared": the caller writes nothing
    in that case rather than an empty file. A holdout-only run therefore still
    gets a document, with the axis-keyed blocks present and empty.

    **This function recomputes nothing — it is handed the plans and records
    them.** It used to take `(roster, (column, levels))` per axis and call
    `units.arms_of` a *second* time, after `cli.command_run` had already
    called it to narrow each condition's roster. Under `by_attribute` that
    second call is harmless, since reading the same column of the same
    roster twice gives the same partition. **Under a draw it is not**: a
    second draw is a second allocation, and "provably identical" is not
    something two calls can be made to promise — only not calling twice
    can. So the decision is *compute once and pass*:
    `cli._resolved_group_axes` realizes one `units.ArmPlan` per axis,
    `units.arm_members` narrows with those plans, and this function records
    those same plan objects. The partition the runner ran and the partition
    `allocation.json` claims are therefore the same object, not two answers
    that happen to agree. This function takes **no roster** for that reason:
    with nothing to read membership from, it cannot become a second producer
    of it.

    **`arms`** maps each axis to its plan's `members`, level → unit keys.
    Unit keys, never row numbers, because a roster that gains a unit
    renumbers rows and would silently repoint every membership claim. The
    order is the plan's own — roster order under `by_attribute`, which
    `units.arms_of` promises — and is recorded rather than re-sorted here,
    because a `blocked` design reads that order as data (once `blocked`
    itself is built).

    **`seed` and `strata` carry whatever the plans realized, per axis.** An
    axis appears under `seed` only when its plan has one, and under `strata`
    only when its plan's `strata` is non-empty — so a `random` or `blocked`
    axis appears under `seed`, and under `strata` too when it declared a
    non-empty `stratify_by`, while a `by_attribute` axis is **left out of
    both**. That omission is the record being truthful rather than a shape
    this build has not filled in yet: `units.assignment_for` realizes
    `seed=None`, `strata=()` for `by_attribute`, which reads an arm a trial
    system already assigned rather than drawing one, so recording a `seed`
    would be a false record of a draw that never happened — the same fault
    § Allocation names for a non-empty `ratio` under `by_attribute` — and
    `assign.stratify_by` names how a draw was *balanced*, which with no draw
    describes nothing. A drawn axis that declared no `stratify_by` is left
    out of `strata` for the same reason and not for a different one: `()` is
    the truthful record of a draw balanced on nothing but its ratio.
    Both keys stay present as mappings, empty or not — `seed`/`strata` are
    `{}` rather than omitted when no axis qualifies — because the shape is
    "keyed by axis name" whether or not any axis does, and an omitted key
    would read as "this document has no seed or strata block at all" rather
    than "no axis drew or stratified this run." `reference.md`
    § `allocation.json` prints a document of each shape.

    **`holdout` is the fourth key, and it is self-contained.** `train` and
    `test` hold unit keys, in the plan's own order — roster order under
    `by_attribute`, the shuffle's order under a draw — recorded rather than
    re-sorted, for the reason `arms` is. Its `seed` appears only when the split
    was DRAWN and its `strata` only when non-empty, `arms`' own rule one
    declaration over: a `by_attribute` holdout reads a partition the data
    already holds, so a seed would be a false record of a draw that never
    happened and a `stratify_by` would describe how a draw was balanced when
    none was. Both are omitted rather than written `null`, matching
    `manifest/input.json`'s "absent rather than null, so 'not hashed' can't be
    misread as 'hashed to nothing'".

    **Unlike the axis-keyed `seed` and `strata`, the holdout's own two live
    INSIDE its block.** Those two are keyed by axis name and a holdout has no
    axis name; hanging it off a fabricated key would invite a reader to index
    it as one, and `reference.md` § `allocation.json` prints the shape this
    produces.

    **This function still takes no roster**, and the holdout arrives realized
    for the same reason the arms do: `cli._resolved_holdout` draws it once, and
    a second draw here would be a second allocation.

    **This is the file `resume` must read rather than re-draw.**
    `reference.md` § Allocation and § Resuming both say `allocation.json` is
    "read rather than re-drawn" on resume — a fact about which units landed
    in which arm should not be re-computable to a different answer just
    because the run is being continued. **That rule has no reader in this
    build**: `OPERATION_COMMANDS = {"validate", "run"}` in `cli.py`, there is
    no `resume` command yet, so nothing here calls this function a second
    time against an existing `allocation.json`. This paragraph is the
    contract a future `resume` must honour — read the existing file rather
    than calling `build_allocation_document` again — not a description of
    behavior this build has or tests.

    **That gap stopped being harmless when the draw was built.** While
    `by_attribute` was the only method that executed, a `resume` that
    re-derived the allocation would have re-read the same column of the same
    roster and got the same partition, so the missing reader cost nothing. A
    drawn axis has no column: a second draw is a second allocation, and while
    `assign_seed_for` makes it *likely* to agree, "likely" is the wrong
    property for the record of which patient was in which arm.
    """
    # Gated on `group_axes` truthiness, which `cli._resolved_group_axes`'s own
    # docstring warns a caller against in general: an axis whose declared
    # `levels` aren't all `str` is silently dropped from `group_axes`, so
    # `bool(group_axes)` alone cannot tell "no axis was declared" from "an
    # axis was declared but shaped wrong." That silent-skip case cannot reach
    # here, though — not because of anything local to this function, but
    # because `cli.command_run` calls `units.arm_members` on the very same
    # `group_axes` earlier, before any run directory exists, and
    # `arm_members` raises `KeyError` the moment a condition selects an axis
    # or level missing from it (`units.arm_members`'s own docstring: "a
    # caller passing a condition whose selected axis or level is not in
    # `axes` ... raises a bare `KeyError`"). So a malformed axis never
    # reaches this call at all; this gate would need reconsidering only if a
    # future caller ever invoked `build_allocation_document` without that
    # upstream call already having succeeded. `holdout` carries no such shape
    # hazard: it reaches this function already realized by `cli._resolved_holdout`,
    # a single call with no per-condition narrowing beside it to compare against.
    if not group_axes and holdout is None:
        return None
    arms = {
        axis: {level: list(keys) for level, keys in plan.members.items()}
        for axis, plan in group_axes.items()
    }
    seed = {axis: plan.seed for axis, plan in group_axes.items() if plan.seed is not None}
    strata = {axis: list(plan.strata) for axis, plan in group_axes.items() if plan.strata}
    document: dict[str, Any] = {"seed": seed, "arms": arms}
    if holdout is not None:
        block: dict[str, Any] = {"train": list(holdout.train), "test": list(holdout.test)}
        if holdout.seed is not None:
            block["seed"] = holdout.seed
        if holdout.strata:
            block["strata"] = list(holdout.strata)
        document["holdout"] = block
    document["strata"] = strata
    return document


def allocation_hash(document: dict[str, Any]) -> str:
    """`provenance.allocation_hash` — a hash of the *document*, not of the file's
    bytes on disk, the same split `manifest.manifest_hash` makes for the input
    manifest: canonical JSON (`sort_keys=True`, compact separators) over the
    same dict `build_allocation_document` returned, which is **not** what
    `allocation.json` is written as (that call uses `indent=2` and the
    insertion order `build_allocation_document` builds, which § `allocation.json`
    prints, for a human reader). The two encodings
    hash to different digests for the same document. A reader reproducing
    this by hand must re-canonicalize `allocation.json`'s parsed content
    (`json.dumps(json.load(...), sort_keys=True, separators=(",", ":"))`)
    rather than hash the file's bytes directly.

    **Why this lives here rather than as a fourth entry in `hashes.py`.**
    `hashes.py` holds `code_hash`, `parameters_hash`, and `design_digest` —
    all three hash something the caller already has lying around (the repo
    tree, the config), not something this module built for them.
    `manifest_hash` sits in `manifest.py`, next to `build_manifest`, for the
    matching reason: it hashes the exact document its own module just
    constructed, so the construction and the hash of what it constructs stay
    one property of one artifact rather than two modules that have to agree
    on a shape from a distance. `allocation_hash` follows `manifest_hash`'s
    placement, not `hashes.py`'s: it hashes `build_allocation_document`'s
    own return value, and that function lives in `artifacts.py` because
    `allocation.json` is an artifact `cli.command_run` writes alongside the
    others this module already handles. H3d's `holdout` half landed the same
    way this reasoning predicted: task 17 gave `build_allocation_document` a
    fourth key for the drawn holdout's block rather than adding a separate
    `holdout_hash` in `hashes.py` — this function already hashes whatever
    `build_allocation_document` returns, so the holdout's block needed no
    hash of its own. The module boundary stays "hashes a document this file
    assembles," not "is a hash."
    """
    payload = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class StepIO:
    def __init__(
        self,
        *,
        step_dir: Path,
        input_dir: Path,
        run_dir: Path,
        units: "UnitList | None" = None,
        scope: str = "repeat",
        conditions: list[tuple[int, str | None]] | None = None,
        repeats: list[str] | None = None,
        step_scopes: dict[str, str] | None = None,
        condition_index: int | None = None,
        condition_label: str | None = None,
        repeat_label: str | None = None,
        measurements: dict[str, Any] | None = None,
    ) -> None:
        self.step_dir = step_dir
        self.input_dir = input_dir
        self.run_dir = run_dir
        self.resumed = False
        self._recorded_keys: set[str] = set()
        self._units = units
        self._rows: dict[str, dict[str, Any]] = {}
        self._skipped: dict[str, str] = {}
        # The `data.units.measurements` declaration itself, not a bool: task 5's
        # collapse needs the `by`/`collapse` rule this carries, and one field
        # carrying the declaration cannot disagree with itself the way a flag and
        # a rule could.
        self._measurements = measurements
        self._measurement_rows: dict[tuple[str, str], dict[str, Any]] = {}
        self._scope = scope
        self._conditions = conditions
        self._repeats = repeats
        self._step_scopes = step_scopes
        self._condition_index = condition_index
        self._condition_label = condition_label
        # This execution's own repeat label, not the run's list — `_repeats` holds
        # the latter and cannot say which one is running. `read_upstream` needs it
        # to resolve a `repeat`-scoped target to the directory that step actually
        # wrote, the same segment `read_condition` takes as an argument.
        self._repeat_label = repeat_label

    @property
    def units(self) -> "UnitList":
        if self._units is None:
            raise ContractError(
                "`io.units` has no roster here: either no `data.units` is declared, "
                "or a `fold` repeat is declared and this execution's scope (`run` or "
                "`condition`) is wider than where the fold exists — there is no fold "
                "yet at these scopes, only at `repeat`, which is where a step reading "
                "`io.units` belongs",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._units

    @property
    def recorded_keys(self) -> set[str]:
        return set(self._recorded_keys)

    @property
    def skipped(self) -> dict[str, str]:
        return dict(self._skipped)

    def _check_roster(self, unit_key: str) -> None:
        """The roster half of settling — the one check every arrival path needs,
        including the measurement path: a measurement of a unit this execution was
        never given is as wrong as a plain record of one, and `reference.md` §
        Errors core raises documents `E-STEP-UNIT-UNKNOWN` for `io.record` with no
        measurement exception.
        """
        if self._units is not None and unit_key not in {u.key for u in self._units}:
            raise ContractError(
                f"{unit_key!r} is not in this execution's roster",
                code="E-STEP-UNIT-UNKNOWN",
            )

    def _settle(self, unit_key: str) -> None:
        self._check_roster(unit_key)
        if unit_key in self._rows or unit_key in self._skipped:
            raise ContractError(
                f"{unit_key!r} was already recorded or skipped in this execution",
                code="E-STEP-UNIT-SETTLED",
            )

    def _check_unmeasured(self, unit_key: str) -> None:
        """The mirror half of the rule `record`'s measurement branch enforces:
        a unit may be measured many times, but never measured and also settled by
        another path — skipped, or plain-recorded — in either order.
        `record(measurement=...)` refuses a unit already in `self._skipped` or
        already in `self._rows`; this refuses the other order for both callers,
        `skip` and `record`'s plain branch, so no call order can produce a unit
        that carries both kinds of row.

        A skipped unit that also carried a measurement row would be counted
        `ineligible` and still produce a result once `finalize` collapses it,
        breaking `resolved == completed + ineligible + failed` (`reference.md` §
        The unit table is the inference base). A plain-recorded one would collide
        with the collapsed row `finalize` writes to the same `_rows` slot, so the
        declared `collapse` rule would apply or not depending on which call came
        first inside the step — the retry-versus-measurement ambiguity
        `measurement=` exists to remove, one layer down.
        """
        if any(key == unit_key for key, _ in self._measurement_rows):
            raise ContractError(
                f"{unit_key!r} already has a measurement recorded in this execution",
                code="E-STEP-UNIT-SETTLED",
            )

    def _declared_attributes(self) -> set[str]:
        if self._units is None or len(self._units) == 0:
            return set()
        return set(self._units[0].attributes)

    def record(self, unit_key: str, values: dict[str, Any], measurement: str | None = None) -> None:
        """Append one row, keyed by unit — or by `(unit, measurement)`.

        `measurement=` is the only thing separating a resumed retry from a second
        measurement of the same unit: without it a second row for the same unit is a
        retry to be deduplicated under first-write-wins, with it a measurement to
        be averaged, and nothing in the row itself says which
        (`reference.md` § What isn't a repeat).
        """
        if measurement is not None and not self._measurements:
            raise ContractError(
                "`io.record` was given `measurement=` while `data.units.measurements` "
                "is undeclared, so there is no rule to collapse the rows under. Declare "
                "it with a `by` and a `collapse`, or drop the argument — without a rule "
                "a second row for one unit is a resumed retry, not a measurement",
                code="E-STEP-MEASUREMENT-UNDECLARED",
            )
        if measurement is not None:
            key = (unit_key, measurement)
            if key in self._measurement_rows:
                return  # first write wins, so a resumed measurement is idempotent too
            self._check_roster(unit_key)
            # The rule: a unit may be measured many times, but never measured and
            # settled by another path — skipped, or plain-recorded — in either
            # order. A second measurement is not settling, because measurement
            # rows never land in `_rows`; membership in `_rows` means a *plain*
            # row, which is the mixture refused below.
            #
            # `io.skip` declares the unit ineligible, admitting no result by
            # design, and a later measurement re-entering it as a completed
            # result is exactly the accounting failure `ineligible` exists to
            # prevent (`reference.md` § The unit table is the inference base).
            # A plain row is refused for the reason `finalize` makes concrete:
            # the collapse writes its result to `_rows[unit_key]`, so a unit
            # holding both would have the declared `collapse` rule apply or not
            # depending on which call the step happened to make first. `skip`
            # and the plain branch call `_check_unmeasured` for the mirrors, so
            # every call order agrees.
            if unit_key in self._skipped:
                raise ContractError(
                    f"{unit_key!r} was already skipped in this execution",
                    code="E-STEP-UNIT-SETTLED",
                )
            if unit_key in self._rows:
                raise ContractError(
                    f"{unit_key!r} was already recorded without a measurement in this "
                    "execution: a unit arrives by one path or the other, never both",
                    code="E-STEP-UNIT-SETTLED",
                )
            if "unit" in values:
                raise ContractError(
                    "`unit` collides with the unit key column: a recorded column may "
                    "not be named `unit`",
                    code="E-STEP-KEY-COLLISION",
                )
            if "measurement" in values:
                raise ContractError(
                    "`measurement` collides with the measurement column: a recorded "
                    "column may not be named `measurement`",
                    code="E-STEP-KEY-COLLISION",
                )
            collision = self._declared_attributes() & values.keys()
            if collision:
                name = sorted(collision)[0]
                raise ContractError(
                    f"{name!r} collides with a declared unit attribute of the same "
                    "name: a recorded column may not shadow it",
                    code="E-STEP-KEY-COLLISION",
                )
            self._measurement_rows[key] = {
                "unit": unit_key,
                "measurement": measurement,
                **coerce_scalars(values, "io.record"),
            }
            return
        if unit_key in self._rows:
            return  # first write wins, matching io.append's idempotency
        self._settle(unit_key)
        # The mirror of the measurement branch's `_rows` check above: a measured
        # unit is not in `_rows`, so first-write-wins never catches this order.
        self._check_unmeasured(unit_key)
        if "unit" in values:
            raise ContractError(
                "`unit` collides with the unit key column: a recorded column may not "
                "be named `unit`",
                code="E-STEP-KEY-COLLISION",
            )
        collision = self._declared_attributes() & values.keys()
        if collision:
            name = sorted(collision)[0]
            raise ContractError(
                f"{name!r} collides with a declared unit attribute of the same name: "
                "a recorded column may not shadow it",
                code="E-STEP-KEY-COLLISION",
            )
        self._rows[unit_key] = {"unit": unit_key, **coerce_scalars(values, "io.record")}
        self._recorded_keys.add(unit_key)

    def skip(self, unit_key: str, reason: str) -> None:
        """Declare that this unit admits no result by design — `ineligible`, not `failed`.

        Refused for a unit that already carries a measurement row, the mirror of
        `record(measurement=...)` refusing an already-skipped unit: a unit may be
        measured many times, but never both measured and skipped, in either order.
        """
        self._settle(unit_key)
        self._check_unmeasured(unit_key)
        self._skipped[unit_key] = reason

    def rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows.values()]

    def measurement_rows(self) -> list[dict[str, Any]]:
        """The uncollapsed `(unit, measurement)` rows — task 5 collapses these."""
        return [dict(row) for row in self._measurement_rows.values()]

    def _collapse_measurements(self) -> None:
        """Fold this execution's measurement rows into one recorded row per unit.

        This is what makes a measured unit *exist* to the rest of core, not merely
        what tidies its table: `reference.md` § The unit table is the inference
        base counts `completed` as "how many distinct unit keys reached
        `io.record` in it — measurements of one unit collapse before they are
        counted", and the runner derives `failed` by subtracting `completed` and
        `ineligible` from `resolved`. A unit left only in `_measurement_rows`
        would therefore be silently counted as a failure.

        The result goes into `_rows`/`_recorded_keys` rather than a parallel
        table, so a collapsed unit flows through the path a plain recorded one
        already takes — including `finalize`'s declared-attribute merge, which a
        second table would have had to duplicate and could then disagree with.

        `rule_for`, `coerce_for_rule` and `apply_rule` are the same three calls
        `units.collapse_measurements` makes for the input path. Sharing them is
        what keeps the two paths from coming to disagree about what `mean` means
        over identical-looking rows; the signatures differ only because that path
        holds `Unit`s and this one holds rows.
        """
        from publishable.units import apply_rule, coerce_for_rule, rule_for

        if not self._measurement_rows:
            return
        collapse = (self._measurements or {}).get("collapse", "first")
        groups: dict[str, list[dict[str, Any]]] = {}
        # `_measurement_rows` is insertion-ordered, so each group's member list is
        # recording order — which is what makes `first` mean "earliest recorded",
        # the same property `collapse_measurements` rests on for resolution order.
        for (unit_key, _measurement), row in self._measurement_rows.items():
            groups.setdefault(unit_key, []).append(row)
        for unit_key, members in groups.items():
            names: list[str] = []
            for member in members:
                for name in member:
                    # `unit` and `measurement` are the row's structural columns,
                    # and the measurement axis is consumed by the collapse exactly
                    # as `by` is on the input path: it distinguished the rows and
                    # has no value once they are one unit.
                    if name not in ("unit", "measurement") and name not in names:
                        names.append(name)
            merged: dict[str, Any] = {"unit": unit_key}
            for name in names:
                rule = rule_for(name, collapse)
                # Rows need not agree on columns, so a column absent from a member
                # contributes no value rather than a `None` — which a numeric rule
                # would refuse outright.
                values = [m[name] for m in members if name in m]
                merged[name] = apply_rule(rule, coerce_for_rule(name, rule, values))
            self._rows[unit_key] = merged
            self._recorded_keys.add(unit_key)

    def finalize(self) -> None:
        """Write this execution's per-unit tables. Called by the runner when a step returns.

        Columns are the unit key, then every declared attribute, then the union of
        every key any row recorded — docs/reference.md § The per-unit tables. A
        failed unit has no row anywhere: `units.parquet` holds one row per completed
        (recorded) unit, `ineligible.jsonl` one line per skipped unit, and nothing is
        written for either table when there is nothing to put in it.

        `measurements.parquet` holds the uncollapsed `(unit, measurement)` rows and
        is written only when this execution's step actually passed `measurement=`
        — guarded on the rows, never on `self._measurements`, since a run whose
        input carries the replicates has that declaration in every execution and
        must produce no such file (`reference.md` § The per-unit tables: "present
        only when a step passed `measurement=`").
        """
        self._collapse_measurements()
        if self._rows:
            attribute_names: list[str] = []
            if self._units is not None:
                for unit in self._units:
                    for name in unit.attributes:
                        if name not in attribute_names:
                            attribute_names.append(name)
            by_key = {u.key: u for u in self._units} if self._units is not None else {}
            recorded: list[str] = []
            for row in self._rows.values():
                for key in row:
                    if key != "unit" and key not in recorded:
                        recorded.append(key)
            columns = ["unit", *attribute_names, *recorded]
            rows = []
            for key, row in self._rows.items():
                owner = by_key.get(key)
                merged: dict[str, Any] = {"unit": key}
                for name in attribute_names:
                    merged[name] = owner.attributes.get(name) if owner else None
                for name in recorded:
                    merged[name] = row.get(name)
                rows.append({c: merged.get(c) for c in columns})
            self.write("units.parquet", rows)
        if self._measurement_rows:
            self.write("measurements.parquet", list(self._measurement_rows.values()))
        for key, reason in self._skipped.items():
            self.append("ineligible.jsonl", {"unit": key, "reason": reason})

    def _resolve(self, name: str) -> Path:
        candidate = (self.step_dir / name).resolve()
        base = self.step_dir.resolve()
        if Path(name).is_absolute() or not str(candidate).startswith(str(base) + os.sep):
            raise ArtifactError(
                f"{name!r} resolves outside the step's directory", code="E-ARTIFACT-NAME"
            )
        return candidate

    def path(self, name: str) -> Path:
        target = self._resolve(name)
        if target.exists():
            raise ArtifactExistsError(f"{name} already exists", code="E-ARTIFACT-EXISTS")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def exists(self, name: str) -> bool:
        return self._resolve(name).exists()

    def write(self, name: str, obj: Any) -> Path:
        target = self.path(name)
        suffix = _suffix_for(name)
        if suffix is not None:
            data = WRITERS[suffix](obj)
        elif isinstance(obj, bytes):
            data = obj
        elif isinstance(obj, str):
            data = obj.encode()
        else:
            raise ArtifactError(
                f"{name} has no registered writer, so the object must be bytes or str, "
                f"not {type(obj).__name__}",
                code="E-ARTIFACT-UNWRITABLE",
            )
        write_atomic(target, data)
        return target

    def append(self, name: str, record: dict[str, Any]) -> None:
        if not name.lower().endswith(".jsonl"):
            raise ArtifactError(
                f"`io.append` writes one JSON object per line, so {name} must be .jsonl",
                code="E-ARTIFACT-APPEND",
            )
        target = self._resolve(name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_input(self, relpath: str) -> Any:
        return self._read(self.input_dir / relpath)

    def _summary_only(self, what: str) -> None:
        if self._scope != "summary":
            raise ContractError(
                f"`io.{what}` is available at `summary` scope only; this step is "
                f"`{self._scope}`-scoped, and a narrower step has no business reading "
                "across conditions",
                code="E-STEP-SCOPE-ONLY",
            )

    @property
    def conditions(self) -> list[tuple[int, str | None]]:
        self._summary_only("conditions")
        return list(self._conditions or [])

    @property
    def repeats(self) -> list[str]:
        self._summary_only("repeats")
        return list(self._repeats or [])

    def read_condition(
        self,
        condition: "int | tuple[int, str | None]",
        step: str,
        name: str,
        repeat: str | None = None,
    ) -> Any:
        """`condition` accepts either a bare index or the `(index, label)` element
        `io.conditions` yields, so the documented `for condition in io.conditions:
        io.read_condition(condition, ...)` pattern and a literal index both work.

        A resolved condition's label can itself be `None` — the no-`sweep` case,
        where there is no `conditions/` level to nest under — so membership is
        checked against the resolved *indices*, never by testing the label for
        `None`: that would make a legitimately unlabeled condition indistinguishable
        from an index this run never resolved.
        """
        self._summary_only("read_condition")
        index = condition[0] if isinstance(condition, tuple) else condition
        target = (self._step_scopes or {}).get(step)
        if target == "repeat" and repeat is None:
            raise ContractError(
                f"`{step}` is repeat-scoped, so `read_condition` needs a `repeat=` naming "
                "which repeat's copy to read",
                code="E-STEP-READ-REPEAT-REQUIRED",
            )
        by_index = dict(self._conditions or [])
        if index not in by_index:
            raise ContractError(
                f"condition {index} is not among this run's resolved conditions",
                code="E-STEP-READ-CONDITION-UNKNOWN",
            )
        label = by_index[index]
        base = (
            self.run_dir
            if label is None
            else (self.run_dir / "conditions" / condition_dir_name(index, label))
        )
        return self._read(self._nest_repeat(base, target, repeat) / step / name)

    def _nest_repeat(self, base: Path, target: str | None, repeat: str | None) -> Path:
        """The repeat-label segment a `repeat`-scoped target's directory carries.

        One rule, two callers: `read_condition` takes the repeat as an argument and
        `read_upstream` uses this execution's own. Writing it twice is how the two
        drift — which is exactly what had happened, `read_upstream` omitting the
        segment entirely and resolving to a path nothing writes.

        A degenerate repeat level collapses — `runner.step_dir_for` adds no segment
        when the run resolved one repeat — so the segment appears exactly when there
        is more than one, which is also why the omission was invisible until a
        design had a second seed.
        """
        if target == "repeat" and repeat and len(self._repeats or []) > 1:
            return base / repeat
        return base

    def read_upstream(self, step: str, name: str) -> Any:
        target = (self._step_scopes or {}).get(step)
        if target is not None and SCOPE_ORDER[target] > SCOPE_ORDER[self._scope]:
            raise ContractError(
                f"`{step}` is `{target}`-scoped and this step is `{self._scope}`-scoped; "
                "a wider step cannot read a narrower one, because at the time it runs "
                "those executions have not happened",
                code="E-STEP-READ-DIRECTION",
            )
        if self._scope == "summary" and target in ("condition", "repeat"):
            labeled_sweep = any(label is not None for _, label in (self._conditions or []))
            several_repeats = target == "repeat" and len(self._repeats or []) > 1
            if labeled_sweep or several_repeats:
                reason = (
                    "this run's sweep labels its conditions"
                    if labeled_sweep
                    else "this run resolved more than one repeat"
                )
                raise ContractError(
                    f"`{step}` is `{target}`-scoped and {reason}, so a `summary` step "
                    "sitting above all of them has no single condition `io.read_upstream` "
                    "could resolve to; name the condition explicitly with "
                    "`io.read_condition` instead",
                    code="E-STEP-READ-AMBIGUOUS",
                )
        if target == "run" or target is None:
            base = self.run_dir / "shared"
        elif target == "summary":
            base = self.run_dir / "summary"
        else:
            # A condition- or repeat-scoped target lives under the caller's own
            # condition: `read_upstream` reads WIDER steps (or, at equal scope, a
            # step earlier in the same execution), and the only condition wider
            # than this execution's is the one it is running in. A `repeat`-scoped
            # target then nests one level further, under this execution's own
            # repeat — the direction check permits a same-scope read, so this is
            # the ordinary "second repeat step reads the first's artifact" case.
            base = self.run_dir
            if self._condition_label is not None and self._condition_index is not None:
                base = (
                    base
                    / "conditions"
                    / condition_dir_name(self._condition_index, self._condition_label)
                )
            base = self._nest_repeat(base, target, self._repeat_label)
        return self._read(base / step / name)

    @staticmethod
    def _read(path: Path) -> Any:
        """Reads back what `write` wrote, through the inverse of the table it
        dispatched on.

        Two tables and one dispatch: `_suffix_for` decides from `WRITERS`, and
        the reader is then looked up in `READERS`. That is an inversion only
        while the two hold the same keys, which core's own five do and a plugin's
        pair need not — so a suffix `WRITERS` holds and `READERS` does not is a
        coded refusal rather than the bare `KeyError` it was, and § Steps and
        artifacts' promise that what a writer takes is what its reader gives
        back is stated where it can be enforced.

        The reverse is not handled, deliberately rather than by omission:
        `_suffix_for` is the single dispatch and it iterates `WRITERS` alone,
        so a suffix `READERS` holds and `WRITERS` does not is invisible to
        it — `suffix` comes back `None`, and this reads the file as raw bytes
        without ever consulting `READERS`. That suffix registered no writer
        in this process, so nothing here could have written the file `_read`
        is now looking at; a reader with no writer is not a broken pair the
        way the other direction is, so it is left as the ordinary
        no-suffix-known case rather than given its own refusal.

        A suffix *neither* table knows is not a fault at all: it is the raw-bytes
        case `write` already accepts.
        """
        suffix = _suffix_for(path.name)
        if suffix is None:
            return path.read_bytes()
        reader = READERS.get(suffix)
        if reader is None:
            raise ArtifactError(
                f"`{path.name}` claims the suffix `{suffix}`, which has a registered "
                "writer and no reader — a writer and its reader are registered as a "
                "pair, and core cannot invert one it was never given",
                code="E-ARTIFACT-UNREADABLE",
            )
        return reader(path.read_bytes())


class ResolverIO:
    """What a resolver receives: `read_input` and nothing else.

    `reference.md` § Where units come from — "The `io` a resolver receives is
    read-only: `io.read_input` and nothing else. There is no run directory yet at
    validate time and no step yet at run time, so there is nothing for it to write
    into." A `StepIO` with its directories defaulted would carry every write and
    every cross-scope read into a place where each either has no directory to act
    on or would let a resolver write into a run that has not started. Core cannot
    inspect the body of user Python, so the refusal is that the method does not
    exist rather than that it raises.

    Reads through `StepIO._read`, the one dispatch, so a plugin's registered
    reader serves a resolver exactly as it serves a step — two dispatches would be
    two answers to "what does this suffix mean".

    Records each relative path it was asked for, in the order it was asked, so
    `input_manifest_policy: hash_index` can name "the paths the resolver read"
    without a second walk that could disagree with what was actually opened.
    Duplicates are kept: this is a log of reads, and its one consumer builds a set
    from it.

    Two properties are left exactly as `StepIO.read_input` already has them, on
    purpose, rather than narrowed here: the path is appended to `read_paths`
    *before* `StepIO._read` runs, so a read that raises is still logged, and a
    `relpath` containing `../` is not rejected, so it can name a file outside
    `input_dir` — no containment check exists for either `IO` class. Task 31
    (`hash_index` naming what a resolver read) is where whether either matters
    gets decided; this class does not decide it.
    """

    __slots__ = ("input_dir", "_read_paths")

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir
        self._read_paths: list[str] = []

    def read_input(self, relpath: str) -> Any:
        self._read_paths.append(relpath)
        return StepIO._read(self.input_dir / relpath)

    @property
    def read_paths(self) -> tuple[str, ...]:
        return tuple(self._read_paths)

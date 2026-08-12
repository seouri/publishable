# src/publishable/artifacts.py
"""Scope-aware, atomic, append-only artifacts. docs/reference.md § Steps and artifacts."""

import csv
import io as _io
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from publishable.coercion import coerce_scalars
from publishable.errors import ArtifactError, ArtifactExistsError, ContractError
from publishable.sweep import condition_dir_name

if TYPE_CHECKING:
    from publishable.units import UnitList

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


def _suffix_for(name: str) -> str | None:
    """The longest registered suffix of the name's last component, lower-cased."""
    last = name.rsplit("/", 1)[-1].lower()
    best: str | None = None
    for suffix in WRITERS:
        if last.endswith(suffix) and (best is None or len(suffix) > len(best)):
            best = suffix
    return best


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
        """The other half of the rule `record`'s measurement branch already
        enforces one direction of: a unit may be measured many times, but never
        both measured and skipped, in either order. `record(measurement=...)`
        refuses a unit already in `self._skipped`; this refuses the mirror —
        `skip` on a unit already in `self._measurement_rows` — so the two call
        orders agree. A skipped unit that also carries a measurement row would
        be counted `ineligible` and produce a result once task 5 collapses it,
        breaking `resolved == completed + ineligible + failed`
        (`reference.md` § The unit table is the inference base).
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

    def record(
        self, unit_key: str, values: dict[str, Any], measurement: str | None = None
    ) -> None:
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
            # The rule: a unit may be measured many times, but never both measured
            # and skipped, in either order. `_settle`'s `_rows`-membership half must
            # not apply here — a second measurement of one unit is the whole point
            # of this path — but the `_skipped` half still must: `io.skip` declares
            # the unit ineligible, admitting no result by design, and a later
            # measurement re-entering it as a completed result is exactly the
            # accounting failure `ineligible` exists to prevent. `skip`'s
            # `_check_unmeasured` enforces the mirror, so the two call orders agree
            # (`reference.md` § The unit table is the inference base).
            if unit_key in self._skipped:
                raise ContractError(
                    f"{unit_key!r} was already skipped in this execution",
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

    def finalize(self) -> None:
        """Write this execution's per-unit tables. Called by the runner when a step returns.

        Columns are the unit key, then every declared attribute, then the union of
        every key any row recorded — docs/reference.md § The per-unit tables. A
        failed unit has no row anywhere: `units.parquet` holds one row per completed
        (recorded) unit, `ineligible.jsonl` one line per skipped unit, and nothing is
        written for either table when there is nothing to put in it.
        """
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
        base = self.run_dir if label is None else (
            self.run_dir / "conditions" / condition_dir_name(index, label)
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
                base = base / "conditions" / condition_dir_name(
                    self._condition_index, self._condition_label
                )
            base = self._nest_repeat(base, target, self._repeat_label)
        return self._read(base / step / name)

    @staticmethod
    def _read(path: Path) -> Any:
        """Inverts the same table `write` dispatches through — see `WRITERS`/`READERS`."""
        suffix = _suffix_for(path.name)
        if suffix is not None:
            return READERS[suffix](path.read_bytes())
        return path.read_bytes()

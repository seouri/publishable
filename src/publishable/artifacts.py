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
    ) -> None:
        self.step_dir = step_dir
        self.input_dir = input_dir
        self.run_dir = run_dir
        self.resumed = False
        self._recorded_keys: set[str] = set()
        self._units = units
        self._rows: dict[str, dict[str, Any]] = {}
        self._skipped: dict[str, str] = {}
        self._scope = scope
        self._conditions = conditions
        self._repeats = repeats
        self._step_scopes = step_scopes
        self._condition_index = condition_index
        self._condition_label = condition_label

    @property
    def units(self) -> "UnitList":
        if self._units is None:
            raise ContractError(
                "`io.units` needs a `data.units` declaration; none is present, and an "
                "empty list would let a step report results about nothing",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._units

    @property
    def recorded_keys(self) -> set[str]:
        return set(self._recorded_keys)

    @property
    def skipped(self) -> dict[str, str]:
        return dict(self._skipped)

    def _settle(self, unit_key: str) -> None:
        if self._units is not None and unit_key not in {u.key for u in self._units}:
            raise ContractError(
                f"{unit_key!r} is not in this execution's roster",
                code="E-STEP-UNIT-UNKNOWN",
            )
        if unit_key in self._rows or unit_key in self._skipped:
            raise ContractError(
                f"{unit_key!r} was already recorded or skipped in this execution",
                code="E-STEP-UNIT-SETTLED",
            )

    def _declared_attributes(self) -> set[str]:
        if self._units is None or len(self._units) == 0:
            return set()
        return set(self._units[0].attributes)

    def record(self, unit_key: str, values: dict[str, Any]) -> None:
        """Append one row to this step's per-unit table, keyed by unit."""
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
        self._rows[unit_key] = {"unit": unit_key, **values}
        self._recorded_keys.add(unit_key)

    def skip(self, unit_key: str, reason: str) -> None:
        """Declare that this unit admits no result by design — `ineligible`, not `failed`."""
        self._settle(unit_key)
        self._skipped[unit_key] = reason

    def rows(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self._rows.values()]

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
        collapsed = len(self._repeats or []) <= 1
        if target == "repeat" and repeat is not None and not collapsed:
            base = base / repeat
        return self._read(base / step / name)

    def read_upstream(self, step: str, name: str) -> Any:
        target = (self._step_scopes or {}).get(step)
        if target is not None and SCOPE_ORDER[target] > SCOPE_ORDER[self._scope]:
            raise ContractError(
                f"`{step}` is `{target}`-scoped and this step is `{self._scope}`-scoped; "
                "a wider step cannot read a narrower one, because at the time it runs "
                "those executions have not happened",
                code="E-STEP-READ-DIRECTION",
            )
        if (
            self._scope == "summary"
            and target in ("condition", "repeat")
            and any(label is not None for _, label in (self._conditions or []))
        ):
            raise ContractError(
                f"`{step}` is `{target}`-scoped and this run's sweep labels its "
                "conditions, so a `summary` step sitting above all of them has no "
                "single condition `io.read_upstream` could resolve to; name the "
                "condition explicitly with `io.read_condition` instead",
                code="E-STEP-READ-AMBIGUOUS",
            )
        if target == "run" or target is None:
            base = self.run_dir / "shared"
        elif target == "summary":
            base = self.run_dir / "summary"
        else:
            # A condition-scoped target lives under the caller's own condition:
            # `read_upstream` reads WIDER steps, and the only condition wider
            # than this execution's is the one it is running in.
            base = self.run_dir
            if self._condition_label is not None and self._condition_index is not None:
                base = base / "conditions" / condition_dir_name(
                    self._condition_index, self._condition_label
                )
        return self._read(base / step / name)

    @staticmethod
    def _read(path: Path) -> Any:
        """Inverts the same table `write` dispatches through — see `WRITERS`/`READERS`."""
        suffix = _suffix_for(path.name)
        if suffix is not None:
            return READERS[suffix](path.read_bytes())
        return path.read_bytes()

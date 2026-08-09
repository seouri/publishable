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

if TYPE_CHECKING:
    from publishable.units import UnitList


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


WRITERS = {
    ".json": _encode_json,
    ".yaml": _encode_yaml,
    ".jsonl": _encode_jsonl,
    ".csv": _encode_csv,
}

READERS = {
    ".json": _decode_json,
    ".yaml": _decode_yaml,
    ".jsonl": _decode_jsonl,
    ".csv": _decode_csv,
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
    ) -> None:
        self.step_dir = step_dir
        self.input_dir = input_dir
        self.run_dir = run_dir
        self.resumed = False
        self.recorded_keys: set[str] = set()
        self._units = units
        self._rows: dict[str, dict[str, Any]] = {}
        self.skipped: dict[str, str] = {}

    @property
    def units(self) -> "UnitList":
        if self._units is None:
            raise ContractError(
                "`io.units` needs a `data.units` declaration; none is present, and an "
                "empty list would let a step report results about nothing",
                code="E-STEP-UNITS-UNAVAILABLE",
            )
        return self._units

    def _settle(self, unit_key: str) -> None:
        if self._units is not None and unit_key not in {u.key for u in self._units}:
            raise ContractError(
                f"{unit_key!r} is not in this execution's roster",
                code="E-STEP-UNIT-UNKNOWN",
            )
        if unit_key in self._rows or unit_key in self.skipped:
            raise ContractError(
                f"{unit_key!r} was already recorded or skipped in this execution",
                code="E-STEP-UNIT-SETTLED",
            )

    def record(self, unit_key: str, values: dict[str, Any]) -> None:
        """Append one row to this step's per-unit table, keyed by unit."""
        if unit_key in self._rows:
            return  # first write wins, matching io.append's idempotency
        self._settle(unit_key)
        self._rows[unit_key] = {"unit": unit_key, **values}
        self.recorded_keys.add(unit_key)

    def skip(self, unit_key: str, reason: str) -> None:
        """Declare that this unit admits no result by design — `ineligible`, not `failed`."""
        self._settle(unit_key)
        self.skipped[unit_key] = reason

    def rows(self) -> list[dict[str, Any]]:
        return list(self._rows.values())

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

    def read_upstream(self, step: str, name: str) -> Any:
        return self._read(self.run_dir / "shared" / step / name)

    @staticmethod
    def _read(path: Path) -> Any:
        """Inverts the same table `write` dispatches through — see `WRITERS`/`READERS`."""
        suffix = _suffix_for(path.name)
        if suffix is not None:
            return READERS[suffix](path.read_bytes())
        return path.read_bytes()

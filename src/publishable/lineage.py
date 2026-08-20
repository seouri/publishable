"""Upstream run recording and chain verification (`reference.md` § Package layout).

This module holds `read_run_record`, the reader over a `run.yaml` this build wrote, and
(from later tasks in this slice) the locator resolution and containment machinery
`io.reuse_from` delegates to. It **may** import `run_record` — the assembler that writes
`run.yaml` — because a chain-verification reader is exactly what reads what an assembler
wrote. `artifacts.py` **may not** import this module: measured, `run_record` imports
`runner`, which imports `artifacts`, so `artifacts` importing `lineage` (which imports
`run_record`) would close a cycle: `artifacts → lineage → run_record → runner →
artifacts`. `run_record.py` itself is refused as the reader's home on the same grounds —
its own first line is "Assemble run.yaml. Assembles only — computes nothing" — and on
that identical cycle, since a reader living there would need no import of itself.
"""

from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError
from publishable.run_record import SCHEMA_VERSION


def read_run_record(path: Path) -> dict[str, Any]:
    """Read and parse a `run.yaml` at `path` (the run directory, not the file itself).

    Three refusals, each with a distinguishable fault and a distinct remedy — the shape
    H4d's `null_test` closed by splitting a single "return for many reasons" code:

    - No `run.yaml` at `path`: `E-UPSTREAM-RECORD-MISSING`. The run never finished, or
      `path` is not a run directory.
    - `run.yaml` present but unreadable — invalid YAML, not a mapping once parsed, or a
      mapping with no `run_id`: `E-UPSTREAM-RECORD-UNREADABLE`. The file was edited or
      truncated by hand.
    - A `schema_version` this build does not read: `E-UPSTREAM-RECORD-VERSION`. The
      remedy is pinning the `publishable` version that wrote it.

    `SCHEMA_VERSION` is imported from `run_record` rather than restated as a literal
    here, on the argument `artifacts.py`'s `_nest_repeat` already makes about a rule with
    two callers: writing it twice is how the two drift.

    A record whose `status` is `partial` or `failed` is **not** refused here. A partial
    run's completed step wrote a real artifact, and refusing the whole record on a
    sibling condition's failure would make that artifact unreadable for a reason that has
    nothing to do with it — the named step's own recorded status is a later task's check,
    not this one's.
    """
    run_yaml = path / "run.yaml"
    if not run_yaml.exists():
        raise ContractError(
            f"no run.yaml at {path} — the run never finished, or this is not a run directory",
            code="E-UPSTREAM-RECORD-MISSING",
        )
    try:
        doc = yaml.safe_load(run_yaml.read_text())
    except yaml.YAMLError as exc:
        raise ContractError(
            f"{run_yaml} is not valid YAML: {exc}",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        ) from exc
    if not isinstance(doc, dict):
        raise ContractError(
            f"{run_yaml} did not parse to a mapping — it was edited or truncated",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        )
    if "run_id" not in doc:
        raise ContractError(
            f"{run_yaml} has no `run_id` — it was edited or truncated",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        )
    version = doc.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ContractError(
            f"{run_yaml} declares schema_version {version!r}, which this build does "
            f"not read (it reads {SCHEMA_VERSION!r}) — pin the `publishable` version "
            "that wrote it",
            code="E-UPSTREAM-RECORD-VERSION",
        )
    return doc

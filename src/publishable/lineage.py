"""Upstream run recording and chain verification (`reference.md` § Package layout).

This module holds `read_run_record`, the reader over a `run.yaml` this build wrote, and
(from later tasks in this slice) the locator resolution and containment machinery
`io.reuse_from` delegates to. It **may** import `run_record` — the assembler that writes
`run.yaml` — because a chain-verification reader is exactly what reads what an assembler
wrote. `artifacts.py` **may not** import this module: measured, `run_record` imports
`runner`, which imports `artifacts`, so `artifacts` importing `lineage` (which imports
`run_record`) would close a cycle: `artifacts → lineage → run_record → runner →
artifacts`. `run_record.py` itself is refused as the reader's home on its own
docstring's grounds — its own first line is "Assemble run.yaml. Assembles only —
computes nothing."
"""

from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError
from publishable.provenance import resolves_inside_repo
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


def resolve_run(locator: str, *, output_dir: Path, repo_root: Path) -> tuple[Path, dict[str, Any]]:
    """Resolve a `reuse_from` locator to a run directory and its record.

    § Lineage between runs gives a locator two readings, told apart by
    `Path(locator).is_absolute()` and by nothing else — not a separator test, not
    whether the directory exists:

    - **A bare `run_id`** resolves under `output_dir`, this config's own. The
      locator is compared **as given** against the record's `run_id` — never a
      resolved basename — because `<output_dir>/latest` is a symlink to the real
      run directory's *name*, which happens to equal that directory's `run_id`; a
      resolved-basename comparison would agree on both sides and the relative form
      would quietly start accepting `latest`, which is not a `run_id`. A relative
      locator containing more than one path component is neither form — it would
      otherwise resolve under `output_dir` as if it were a `run_id`, and
      `provenance.upstream` would then record a value that is not one —
      `E-UPSTREAM-LOCATOR`. A resolved run whose record's `run_id` disagrees with
      the locator as given is `E-UPSTREAM-RUNID-MISMATCH`.
    - **An absolute path** names a run directory anywhere. Symlinks are resolved
      first, so `<output_dir>/latest` lands on the real directory; its `run_id` is
      then read back from the record there, never parsed from the path. Checked
      for repo containment against `repo_root` — the one `command_run` already
      computed by walking up from the config path it was given, never re-derived
      from the upstream path itself, which would answer a different question (does
      the upstream sit in *its own* repo) — `E-UPSTREAM-REPO-CONTAINED`.

    The two forms differ in exactly the way their arguments differ, one being an
    identity and the other a location: an absolute locator may name `latest`
    because a location can point at anything; a relative one may not, because
    `latest` is not a `run_id` and the record there says so. That asymmetry is a
    property, not an oversight.
    """
    path = Path(locator)
    if path.is_absolute():
        resolved = path.resolve()
        if resolves_inside_repo(resolved, repo_root):
            raise ContractError(
                f"upstream run {locator!r} resolves inside this repo ({repo_root}) — "
                "copy it outside the repo, or address it by run_id under output_dir",
                code="E-UPSTREAM-REPO-CONTAINED",
            )
        return resolved, read_run_record(resolved)
    if len(path.parts) > 1:
        raise ContractError(
            f"{locator!r} is neither a bare run_id nor an absolute path — a relative "
            "path with a separator would otherwise resolve under output_dir as if it "
            "were a run_id, and provenance.upstream would record a value that is not one",
            code="E-UPSTREAM-LOCATOR",
        )
    resolved = output_dir / locator
    record = read_run_record(resolved)
    if record.get("run_id") != locator:
        raise ContractError(
            f"{locator!r} does not name a run_id — the run directory at {resolved} "
            f"records run_id {record.get('run_id')!r}. `latest` is a path, not a "
            "run_id, and only the absolute form may follow a path",
            code="E-UPSTREAM-RUNID-MISMATCH",
        )
    return resolved, record

# src/publishable/reproduce.py
"""`reproduce`. docs/reference.md § Reproducing on another device.

**Ruling Y.** `reproduce` takes a path and nothing else, and it does not
resolve a target device: *"reproducing on another device"* names where the
user is, not an argument. There is no `--into`, no host, no user, no key and no
behaviour-changing environment variable — `reproduce` runs **on** the other
device against a record it is given. What remains is *which* path, and that is
what this module's first half answers.

**Nothing here writes to disk.** The destination derivation, the clone and the
environment restoration arrive with their own tasks; this module opens with
the reader so that a bad operand is refused before anything is created.

See `docs/superpowers/specs/2026-08-24-reproduce-design.md` § Decision 1 for
the five verdicts and the grounds each rests on.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.lineage import read_record_file


@dataclass(frozen=True)
class Record:
    """An accepted run record — the run-directory form or the bundle form.

    `path` is kept beside `doc` because the two accepted record forms differ in
    what sits *beside* the file, not in the file itself: `environment/uv.lock`
    is reachable next to a run directory's `run.yaml` and is a dangling
    reference from a bundle member (design § 0.6). A later step probes for it,
    and it needs the path this record was read from to do that.
    """

    doc: dict[str, Any]
    path: Path


@dataclass(frozen=True)
class ConfigOperand:
    """An accepted config file — § Reproducing's steps 4 onward.

    No `doc`: the config form re-reads the file through the same path `run`
    takes, rather than carrying a parse this module made for discrimination
    only. Carrying it would create a second source of truth for what the
    config says, which is the shape Decision 11 refuses for the byte copy.
    """

    path: Path


Operand = Record | ConfigOperand


def _refuse_operand(path: Path, c: Collector, what: str) -> None:
    """`E-REPRODUCE-OPERAND`, always naming what a usable operand would be.

    One helper rather than five call sites spelling the remedy five ways: the
    remedy is the same sentence in every branch — a run record file or a config
    file — and only `what` (the fault this operand has) differs.
    """
    c.error(
        "E-REPRODUCE-OPERAND",
        str(path),
        f"{what} — `reproduce` takes a run record file (a run directory's own "
        "`run.yaml`, or a bundle member such as `main.run.yaml`) or a config file",
    )


def classify_operand(path: Path, c: Collector) -> Operand | None:
    """One YAML parse, then three structural questions. Design Decision 1.

    **NOT by basename.** A bundle member is `main.run.yaml`, not `run.yaml`
    (measured: the bundle `study add` writes holds `study.yaml` and
    `main.run.yaml` and no directory), so `endswith("run.yaml")` is the
    reserved-name proxy this repo has already paid for at a `report_by`
    stratum — a name standing in for a structural fact. The structural facts
    are: a mapping holding `run_id` is a record; a mapping holding `runs` is a
    bundle root; a mapping holding `provenance` or `results` and no `run_id` is
    an **edited** record; a mapping holding `experiment_type` and none of the
    above is a config.

    **`runs` is the bundle root's key**, read out of `study.py` rather than
    guessed from § Building one's documented example: `study_new` writes
    `{"title", "authors", "runs"}` and `study_add` adds `runs[<name>] =
    {"file", "run_id"}` plus an optional `code` block. Neither `study` nor
    `members` appears anywhere in that module, and the member NAMES are
    `runs`'s keys.

    **Every refusal is appended to `c`, never raised.** `main`'s
    `except PublishableError` handler applies no redaction pass (measured by
    H9b), so a refusal raised out of here would reach a reader un-redacted;
    the caller owns a `Collector` carrying the credential values core read, and
    `render` is where redaction happens. `read_record_file`'s own three
    refusals are caught and re-reported through `c` **with their own codes
    intact** — H9c is that reader's fifth caller and mints no refusal of its
    own for the parse.

    Returns `None` exactly when something was appended to `c`.
    """
    if path.is_dir():
        # `resume` is the one command that takes a run DIRECTORY, and giving
        # `reproduce` the same operand for the opposite action is precisely
        # the confusion this refuses. The message supplies the one path
        # component the user is missing, which is what makes the refusal
        # cheap rather than obstructive.
        _refuse_operand(
            path,
            c,
            f"is a directory, not a file — `resume` takes a run directory and "
            f"`reproduce` takes the record inside one, so this is most likely "
            f"{path / 'run.yaml'}",
        )
        return None

    try:
        text = path.read_text()
        doc = yaml.safe_load(text)
    except (OSError, yaml.YAMLError) as exc:
        # `E-IO-FAILED`, joining `diff`'s and `resume`'s precedent rather than
        # minting a code of this slice's own: a path that cannot be read or
        # parsed is not a statement about `reproduce` at all. A missing path
        # reaches this branch too, and deliberately does not reach
        # `read_record_file`'s `E-UPSTREAM-RECORD-MISSING` — that code names a
        # run whose record is missing, and here we do not yet know the operand
        # was meant to be a record.
        c.error("E-IO-FAILED", str(path), f"could not be read as YAML: {exc}")
        return None

    if not isinstance(doc, dict):
        _refuse_operand(path, c, f"parsed to {type(doc).__name__}, not a mapping")
        return None

    if "runs" in doc:
        runs = doc.get("runs") or {}
        names = sorted(runs) if isinstance(runs, dict) else []
        # The members are LISTED, not counted. A count tells a reader how many
        # paths exist and none of what to type; the list is the remedy. And
        # `study new` writes `runs: {}`, so the empty bundle is its own
        # sentence rather than a list that reads as naming the first member.
        held = (
            "it holds " + ", ".join(f"`{name}.run.yaml`" for name in names)
            if names
            else "it holds no runs yet — add one with `study add`"
        )
        c.error(
            "E-REPRODUCE-BUNDLE",
            str(path),
            f"is a study bundle's own `study.yaml`, not a run record; {held}. "
            "Give `reproduce` the member you want",
        )
        return None

    if "run_id" in doc:
        try:
            return Record(read_record_file(path), path)
        except ContractError as exc:
            c.error(exc.code or "E-IO-FAILED", str(path), str(exc))
            return None

    if "provenance" in doc or "results" in doc:
        # An edited record, and it is refused rather than READ AS A CONFIG. A
        # record with its `run_id` removed has no `experiment_type` either, so
        # the fall-through would refuse it anyway — but it would refuse it as
        # "not a config", which sends the reader to the wrong file. The two
        # readings are genuinely different and this branch is what separates
        # them.
        _refuse_operand(
            path,
            c,
            "carries a run record's `provenance`/`results` but no `run_id`, so it is "
            "a record that was edited or truncated rather than a config",
        )
        return None

    if "experiment_type" in doc:
        return ConfigOperand(path)

    _refuse_operand(path, c, "is neither a run record nor a config")
    return None

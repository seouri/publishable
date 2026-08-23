"""Upstream run recording and chain verification (`reference.md` § Package layout).

This module holds `read_run_record`, the reader over a `run.yaml` this build wrote, and
the locator resolution and containment machinery `io.reuse_from` delegates to
(`resolve_run`, `resolve_step`, `UpstreamLedger`, `UpstreamResolver`). It **may** import
`run_record` — the assembler that writes `run.yaml` — because a chain-verification
reader is exactly what reads what an assembler wrote. `artifacts.py` **may not** import
this module: measured, `run_record` imports `runner`, which imports `artifacts`, so
`artifacts` importing `lineage` (which imports `run_record`) would close a cycle:
`artifacts → lineage → run_record → runner → artifacts`. `run_record.py` itself is
refused as the reader's home on its own docstring's grounds — its own first line is
"Assemble run.yaml. Assembles only — computes nothing."
"""

import json
from pathlib import Path
from typing import Any

import yaml

from publishable.errors import ContractError
from publishable.provenance import resolves_inside_repo
from publishable.run_record import SCHEMA_VERSION


def read_record_file(path: Path) -> dict[str, Any]:
    """Read and parse a run record at `path` — the record FILE itself, never a
    directory. `read_run_record` below is this function applied to a run
    directory's own `run.yaml`; this one exists separately because a bundle
    member is not `<dir>/run.yaml` — § Building one's bundle tree holds bare
    files, `main.run.yaml`, `sensitivity.run.yaml` — so a reader keyed to a
    directory cannot address one at all (measured at `ebf642a`,
    `docs/superpowers/plans/2026-08-21-report-study.md` § Corrections,
    correction 1). One refusal set, two entries, on `_nest_repeat`'s own
    "one rule, two callers" precedent — `report` and `study add` are the two
    new callers of this entry, `io.reuse_from` and `diff` the two existing
    callers of `read_run_record`'s.

    Three refusals, each with a distinguishable fault and a distinct remedy — the shape
    H4d's `null_test` closed by splitting a single "return for many reasons" code:

    - No record at `path`: `E-UPSTREAM-RECORD-MISSING`.
    - Present but unreadable — invalid YAML, not a mapping once parsed, or a
      mapping with no `run_id`: `E-UPSTREAM-RECORD-UNREADABLE`. The file was edited or
      truncated by hand. Invalid YAML and a document that parses clean to
      something other than a mapping (a list, say) are two different faults
      under the one code, and stay distinguishable by MESSAGE, not only by
      code — "not valid YAML" versus "did not parse to a mapping" — since a
      single assertion catching both would be the same defect as one code
      covering two faults (H8a's batch-1 review).
    - A `schema_version` this build does not read: `E-UPSTREAM-RECORD-VERSION`. The
      remedy is pinning the `publishable` version that wrote it.

    `SCHEMA_VERSION` is imported from `run_record` rather than restated as a literal
    here, on the argument `artifacts.py`'s `_nest_repeat` already makes about a rule with
    two callers: writing it twice is how the two drift.

    A record whose `status` is `partial` or `failed` is **not** refused here. A partial
    run's completed step wrote a real artifact, and refusing the whole record on a
    sibling condition's failure would make that artifact unreadable for a reason that has
    nothing to do with it — the named step's own recorded status is `resolve_step`'s
    check, not this one's.
    """
    if not path.exists():
        raise ContractError(
            f"no run record at {path} — the run never finished, or the path is wrong",
            code="E-UPSTREAM-RECORD-MISSING",
        )
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ContractError(
            f"{path} is not valid YAML: {exc}",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        ) from exc
    if not isinstance(doc, dict):
        raise ContractError(
            f"{path} did not parse to a mapping — it was edited or truncated",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        )
    if "run_id" not in doc:
        raise ContractError(
            f"{path} has no `run_id` — it was edited or truncated",
            code="E-UPSTREAM-RECORD-UNREADABLE",
        )
    version = doc.get("schema_version")
    if version != SCHEMA_VERSION:
        raise ContractError(
            f"{path} declares schema_version {version!r}, which this build does "
            f"not read (it reads {SCHEMA_VERSION!r}) — pin the `publishable` version "
            "that wrote it",
            code="E-UPSTREAM-RECORD-VERSION",
        )
    return doc


def read_run_record(path: Path) -> dict[str, Any]:
    """Read and parse the `run.yaml` inside the run directory `path` (the
    directory, not the file itself) — `read_record_file(path / "run.yaml")`,
    delegating rather than duplicating the parse-and-refuse body so the one
    refusal set stays defined once (see `read_record_file` above for the
    three codes and their remedies).
    """
    return read_record_file(path / "run.yaml")


def resolve_run(locator: str, *, output_dir: Path, repo_root: Path) -> tuple[Path, dict[str, Any]]:
    """Resolve a `reuse_from` locator to a run directory and its record.

    § Lineage between runs gives a locator two readings; Decision 1
    (`docs/superpowers/specs/2026-08-20-lineage-design.md`) tells them apart by
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

    **The repo-containment check runs on both forms.** `spec-defects.md`'s
    "`resolve_run`'s relative form skips the repo-containment check" (owner:
    H8a tasks 3 and 5) closes here: Decision 1's grounds for exempting the
    relative form — "`output_dir` was checked at `validate` and again by
    `run`" — hold for an ordinary subdirectory of `output_dir` and not for a
    **symlink** under it, and core writes one itself (`point_latest`'s
    `<output_dir>/latest`). A symlink under `output_dir` pointing into the
    git repo would otherwise read an in-repo run through the relative form
    with no check at all. So the relative form's path is resolved (symlinks
    followed) *before* the containment check, exactly as the absolute form's
    already is — one check, run on both branches, rather than two checks
    that could drift.
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
    resolved = (output_dir / locator).resolve()
    if resolves_inside_repo(resolved, repo_root):
        raise ContractError(
            f"upstream run {locator!r} resolves inside this repo ({repo_root}) — "
            "copy it outside the repo, or address it by run_id under output_dir",
            code="E-UPSTREAM-REPO-CONTAINED",
        )
    record = read_run_record(resolved)
    if record.get("run_id") != locator:
        detail = (
            "`latest` is a path, not a run_id, and only the absolute form may follow a path"
            if locator == "latest"
            else "the relative form addresses a run by its own run_id, never by "
            "another name it happens to sit under"
        )
        raise ContractError(
            f"{locator!r} does not name a run_id — the run directory at {resolved} "
            f"records run_id {record.get('run_id')!r}. {detail}",
            code="E-UPSTREAM-RUNID-MISMATCH",
        )
    return resolved, record


def resolve_step(record: dict[str, Any], run_dir: Path, step: str) -> Path:
    """Locate the directory an upstream `step` published to, from `record`'s own
    `execution` block — never from a condition or repeat selector, which
    `reuse_from` does not take.

    § `reuse_from` addresses an artifact argues there is no condition or repeat
    selector because one would couple a downstream config to an upstream run's
    layout, which a renumbering silently moves. The same argument decides where a
    read may land: the only two locations that carry no condition and no repeat
    coordinate are `shared/` (a `run`-scoped step) and `summary/` (a
    `summary`-scoped step) — so a step recorded under `execution.shared` resolves
    to `<run_dir>/shared/<step>/` and one under `execution.summary` to
    `<run_dir>/summary/<step>/`.

    A step recorded under `execution.conditions` — a `condition`- or
    `repeat`-scoped step — is refused, `E-UPSTREAM-STEP-SCOPED`, even in the one
    case where the ambiguity does not actually exist: an *unswept* run's
    condition- or repeat-scoped step writes directly under the run directory,
    never under `conditions/` (with a `<repeat>/` segment only when the run
    resolved more than one repeat — a single repeat collapses it), and so has an
    unambiguous location the blanket refusal deliberately declines to use. An
    upstream that is unswept today and gains a level tomorrow would relocate that
    artifact while every hash still matches, and a downstream read that worked
    before the level was added and reads a different cell after it is the exact
    failure the missing selector exists to prevent.

    A step present in neither `shared`, `summary` nor any condition's `steps` is
    `E-UPSTREAM-STEP-UNKNOWN`. A step that is addressable but whose recorded
    `status` is not `completed` is `E-UPSTREAM-STEP-INCOMPLETE` — a refusal
    rather than a read, because an artifact from an execution that did not finish
    is exactly what "lineage is recorded, not resolved" exists to stop being
    silently consumed.
    """
    execution = record.get("execution") or {}
    shared = execution.get("shared") or {}
    summary = execution.get("summary") or {}
    conditions = execution.get("conditions") or []

    if step in shared:
        entry = shared[step]
        base = run_dir / "shared" / step
    elif step in summary:
        entry = summary[step]
        base = run_dir / "summary" / step
    else:
        for cond in conditions:
            if step in (cond.get("steps") or {}):
                raise ContractError(
                    f"`{step}` is a condition- or repeat-scoped upstream step and has "
                    "no single location `reuse_from` can address without a condition "
                    "or repeat selector it does not take — republish it from a "
                    "`summary` step in the upstream run",
                    code="E-UPSTREAM-STEP-SCOPED",
                )
        raise ContractError(
            f"`{step}` is not a recorded step in this upstream run",
            code="E-UPSTREAM-STEP-UNKNOWN",
        )

    # Minor 6 (task-b2-review.md), ruled by task 5: a hand-edited record whose
    # `shared`/`summary` entry is not a mapping reaches `.get` here and raises
    # `AttributeError` rather than a diagnostic. Left as is, deliberately: this
    # is a fault in a hand-edited `run.yaml`, not in a config or a step, and
    # `read_run_record` (Decision 3) already draws the line at three narrow
    # refusals — `schema_version`, `run_id`, and parse/mapping validity —
    # rather than validating the whole document's shape. Minting a code here
    # would require widening that line with no config-reachable case to
    # justify it. `execute_plan`'s bare `except Exception` still contains it —
    # the execution is recorded `failed` and the plan still continues
    # (Decision 10) — so nothing here regresses "nothing in H8a stops or
    # alters a run" merely because the exception is uncoded.
    if entry.get("status") != "completed":
        raise ContractError(
            f"`{step}` in the upstream run did not complete (status: "
            f"{entry.get('status')!r}) — an artifact from an execution that did not "
            "finish is not read",
            code="E-UPSTREAM-STEP-INCOMPLETE",
        )
    return base


class UpstreamLedger:
    """The accumulating `provenance.upstream` entries for one run.

    Built once in `command_run` and shared across every execution's `StepIO`
    (Decision 2 / Decision 6) — one instance for the whole run, so it
    outlives every per-execution `StepIO` and survives an execution that
    later fails, rather than resetting between executions the way a
    `StepIO`-owned collection would.

    Task 6 owns the accumulation rule itself: `record` is called from
    `reuse_from` exactly once per call that *returns* — never from an
    `except` branch, and never for a call that raises before reaching it
    (Decision 6, step 1) — so a `reuse_from` that raises leaves the ledger
    untouched. The ledger is a run-level object built once in `command_run`
    and outlives every per-execution `StepIO`, so an entry survives an
    execution that later fails (Decision 6, step 2): nothing here is ever
    removed once added.

    Keyed by the RESOLVED `run_id`, never by the locator a step named — a
    read of the same upstream once by `run_id` and once by an absolute path
    is one entry with both names in `used` (Decision 6, step 4; see
    `UpstreamResolver`'s own cache, which is keyed by locator for a
    different reason and must not be confused with this one).
    """

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def record(self, *, step: str, name: str, record: dict[str, Any]) -> None:
        """Record that `step`'s `reuse_from` call read `name` from the
        upstream `record` (as returned by `resolve_run`/
        `UpstreamResolver.resolve`). Called from `reuse_from` only after its
        own read has returned — never on a raise (Decision 6, step 1).

        `code_hash` and `parameters_hash` are copied from `record` the first
        time this `run_id` is seen and never re-read afterward — this method
        only needs the two figures once per `run_id`, not once per call. The
        read itself is not this method's concern: whatever collapses N reads
        of one upstream into one `read_run_record` call is
        `UpstreamResolver._records`, keyed by locator (Decision 6, step 4's
        caching) — this ledger performs no I/O and two distinct locators
        naming the same run still reach `resolve()` twice, once each.
        """
        run_id = record["run_id"]
        entry = self._entries.setdefault(
            run_id,
            {
                "run_id": run_id,
                "code_hash": record.get("code_hash"),
                "parameters_hash": record.get("parameters_hash"),
                # A LIST, not a set: `entries()` sorts it before returning it
                # regardless, but a set's iteration order is Python's hash
                # order — randomized per process for `str` — which would
                # make the "delete the `sorted()`" mutation pass or fail by
                # chance rather than by construction. Deduplicated here, on
                # insertion, so insertion order stays a genuine fact about
                # this run's execution order for `entries()`'s docstring
                # (and Fixture O's test) to reason about.
                "used": [],
            },
        )
        used_key = f"{step}/{name}"
        if used_key not in entry["used"]:
            entry["used"].append(used_key)

    def entries(self) -> list[dict[str, Any]]:
        """The sorted list `command_run` reads into `provenance.upstream`
        (Decision 6, step 3; Decision 7). Entries are sorted by `run_id` and
        each entry's `used` is deduplicated and sorted lexicographically —
        never insertion order, which is *execution* order and which
        `order: randomized` moves between two runs of the same design, so a
        record stable across two identical runs cannot be built from it."""
        return [
            {
                "run_id": entry["run_id"],
                "code_hash": entry["code_hash"],
                "parameters_hash": entry["parameters_hash"],
                "used": sorted(entry["used"]),
            }
            for entry in sorted(self._entries.values(), key=lambda e: e["run_id"])
        ]


class UpstreamResolver:
    """Resolves a `reuse_from` locator to a run directory, its record, and a
    step's published directory within it — the one object `command_run`
    builds per run and injects into every execution's `StepIO` as a private
    keyword-only argument (Decision 2), so `output_dir` itself never reaches
    a step: a step can call the one method `io` documents and read no field
    of this object at all.

    `__init__` does no I/O and cannot raise. A resolver is constructed at run
    start for a config whose `output_dir` may hold no prior run at all —
    `allocate_run_dir` creates the directory later — so nothing about
    building one may depend on `output_dir` already existing.
    """

    def __init__(self, *, output_dir: Path, repo_root: Path, ledger: "UpstreamLedger") -> None:
        self.output_dir = output_dir
        self.repo_root = repo_root
        self.ledger = ledger
        # Keyed by the locator EXACTLY AS GIVEN, never by the run_id it
        # resolves to (task-b3-review.md Major 1 / Minor 3). Caching under
        # run_id broke two things at once: an absolute locator's run_id is
        # unknown until its record is read, so every absolute call re-read
        # `run.yaml` regardless of repetition (Major 1 — Decision 6's "one
        # answer per run" did not hold for that form, and a mid-run edit of
        # the upstream could make two identical absolute calls disagree);
        # and once ANY call populated the run_id key, a later RELATIVE call
        # naming that run_id hit the cache without ever running `resolve_run`
        # at all for it — so its own containment check (`resolves_inside_repo`)
        # never ran, and a run_id addressed only relatively was silently
        # answered from a directory an earlier ABSOLUTE call had resolved to,
        # which need not sit under this config's own `output_dir` (Minor 3).
        # Keying by the literal locator fixes both: the same locator asked
        # twice is one read and one answer, and two different locators naming
        # the same run are two independent queries, each checked on its own
        # terms.
        self._records: dict[str, tuple[Path, dict[str, Any]]] = {}

    def resolve(self, locator: str) -> tuple[Path, dict[str, Any]]:
        """Resolve `locator` to `(run_dir, record)`, reading `run.yaml` at
        most once per distinct LOCATOR — the same locator asked twice
        returns the same answer even if the upstream's record changes
        between the two calls (Decision 6: "an upstream edited mid-run
        cannot give two answers inside one record")."""
        cached = self._records.get(locator)
        if cached is not None:
            return cached
        run_dir, record = resolve_run(locator, output_dir=self.output_dir, repo_root=self.repo_root)
        self._records[locator] = (run_dir, record)
        return run_dir, record

    def locate_step(self, record: dict[str, Any], run_dir: Path, step: str) -> Path:
        """`resolve_step`, reached through the resolver rather than imported
        directly by `artifacts.py` — which cannot import this module at all
        (Decision 2's third ground: `artifacts → lineage → run_record →
        runner → artifacts` would close a cycle `TYPE_CHECKING` alone does
        not open back up)."""
        return resolve_step(record, run_dir, step)


# `executions.jsonl`'s ledger key: (step, condition index, repeat label), the
# triple `reference.md` § `executions.jsonl` calls one execution. `None` in
# either of the last two positions is a real value, not a missing one — a
# `run`- or `summary`-scoped execution has no condition and no repeat.
LedgerKey = tuple[str, "int | None", "str | None"]

_LEDGER_LINE_KEYS = ("step", "scope", "condition", "repeat", "status")


def read_execution_ledger(run_dir: Path) -> list[dict[str, Any]]:
    """Every line of `run_dir/executions.jsonl`, parsed, in the order the run
    wrote them. An absent ledger is `[]` — a run directory can exist with no
    ledger at all (a run-start probe raise leaves one), and that is *no
    executions*, not a fault.

    **The first reader of this file anywhere in `src/`** (H9b § Corrections
    against the code, correction 21, re-measured by task 6 before this
    function was written: `grep -rn "executions.jsonl" src/publishable/*.py`
    printed EIGHT lines and no reader — `apparatus.py:483` and `:485`
    (prose), `cli.py:2712` (a comment) and `cli.py:4257` (`_DRY_RUN_FIXED_
    FILES`' entry), and `runner.py` at four, of which one is the writer's
    path binding, one is task 5's own comment and two are prose. The two
    ledger-reading functions that do exist — `apparatus.replay_ledger` and
    `freeze._ledger_probe_names` — read `apparatus/probes.jsonl`, a different
    file. It lives here, in the
    module whose own docstring makes it the home of *"the reader over a
    `run.yaml` this build wrote"*, and for the same reason: `run_record`'s
    first line refuses the job ("Assembles only — computes nothing"), and
    `runner` is imported BY `run_record`, so a reader placed there could not
    be called from `run_record` at all. Two callers, one reader: `attempts`
    (this file's `attempt_counts`) and `resume`'s reconstitution.

    Read with plain `json.loads`, deliberately: `execute_plan` writes these
    lines with `json.dumps`' shipped `allow_nan=True`, so a non-finite value a
    step returned round-trips exactly through the same module (H9b design
    appendix A1). A strict reader would refuse a completed execution over a
    value `run.yaml` accepts.

    A line that is not a JSON object, or that lacks one of the five keys every
    line has carried since this file existed, is
    `E-RESUME-LEDGER-UNREADABLE` — the fault is a hand-edited or truncated
    ledger, and the alternative is a resumed run silently treating a mangled
    line as *this triple never ran*. `returned` and `recorded_columns` are
    **not** in that required set: they are H9b's own additions, so a ledger
    written by an earlier build parses here and is refused, if at all, by the
    reader that needs the missing key.
    """
    path = run_dir / "executions.jsonl"
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError as exc:
            raise ContractError(
                f"{path}: line {number} is not valid JSON ({exc})",
                code="E-RESUME-LEDGER-UNREADABLE",
            ) from exc
        if not isinstance(entry, dict):
            raise ContractError(
                f"{path}: line {number} parsed to {type(entry).__name__}, not an object",
                code="E-RESUME-LEDGER-UNREADABLE",
            )
        missing = [key for key in _LEDGER_LINE_KEYS if key not in entry]
        if missing:
            raise ContractError(
                f"{path}: line {number} is missing {', '.join(missing)}",
                code="E-RESUME-LEDGER-UNREADABLE",
            )
        records.append(entry)
    return records


def ledger_key(entry: dict[str, Any]) -> LedgerKey:
    """One ledger line's triple. The one place a line is turned into a key, so
    a counter and a reconstitution cannot key the same file two ways."""
    return (entry["step"], entry["condition"], entry["repeat"])


def attempt_counts(records: list[dict[str, Any]]) -> dict[LedgerKey, int]:
    """How many records each triple holds — `reference.md` § Resuming's own
    definition of `attempts`, computed from the log rather than stored in it.

    Every record counts, whatever its `status`: an attempt that failed is an
    attempt, and a triple that ran twice is the case this figure exists to
    report. Derived rather than written per line because a count stored in an
    append-only log would be a second source of truth for something the log
    already answers.
    """
    counts: dict[LedgerKey, int] = {}
    for entry in records:
        key = ledger_key(entry)
        counts[key] = counts.get(key, 0) + 1
    return counts

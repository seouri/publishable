# src/publishable/report.py
"""`BaseReport`, `Section`, and override discovery. docs/reference.md § A report
override renders one experiment's own figures, § The importable surface.

Nothing here dispatches: the real `report` command and the standard sections
arrive in later tasks. `render_with_override` is called by nothing outside
this module's own tests yet — task 8 wires it into the `report` command.
"""

import importlib
import sys
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from publishable.errors import ContractError
from publishable.stats import RESERVED_METRIC_NAMES

T = TypeVar("T")

# Decision 5's Conditions row, widened by § Corrections correction 8:
# `basis`, `correction` and `repeat_spread` are in the record and not in the
# design's own list — `repeat_spread` is `CLAUDE.md`'s designated home of
# repeat dispersion, so a Conditions section that dropped it would drop the
# only place a reader sees it. A `by` stratum entry carries no `repeat_spread`
# (measured), which is why this is read with `if field in entry` rather than
# a subscript that would raise `KeyError` on that entry.
_CONDITION_METRIC_FIELDS = ("value", "ci95", "method", "n", "basis", "correction", "repeat_spread")

# Decision 5's Deltas row, task 5 step 3: the fixed fields every `vs_baseline`
# or `results.contrasts` entry carries.
_DELTA_FIXED_FIELDS = (
    "delta",
    "method",
    "paired",
    "ci95",
    "ci95_corrected",
    "correction",
    "correction_level",
)
# Whichever of these an entry carries — never all of them, and `n_paired` is
# ABSENT rather than `null` on an unpaired entry (H4c's conditional write,
# `0` already meaning "pairing failed"), so key PRESENCE decides what prints,
# never a `None` test. `family_size`/`family` are in the record and not in
# Decision 5's own list (§ Corrections correction 9) — `family` is read
# generically as whatever mapping it holds, never by two literal keys,
# because a *hypothesis* family's shape (`{hypotheses: N}`) differs from a
# comparison family's (`{comparisons, metrics}`).
_DELTA_OPTIONAL_FIELDS = (
    "n_paired",
    "n_of",
    "n_against",
    "n_paired_clusters",
    "n_paired_effective",
    "weighted_by",
    "cohens_d",
    "cohens_ds",
    "p_value",
    "p_value_corrected",
    "family_size",
    "family",
)


def _present_fields(entry: Mapping[str, Any], names: "tuple[str, ...]") -> dict[str, Any]:
    """The named fields an entry actually carries, in the given order —
    never a subscript, since some fields are legitimately absent on some
    entries (a `by` stratum's `repeat_spread`, an unpaired delta's
    `n_paired`) and a `KeyError` there would be this module's own fail-open
    by a different route."""
    return {name: entry[name] for name in names if name in entry}


def _condition_metric_rows(condition: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One row per metric in one condition's `aggregated` block, plus one row
    per `by[attribute][level]` stratum metric when `statistics.report_by` was
    declared. `by` is a SIBLING of the metric names in `aggregated[step]`,
    never a metric itself — excluded via `stats.RESERVED_METRIC_NAMES`,
    never a literal `"by"` (Decision 5), so a second reserved name minted
    elsewhere is excluded here too without an edit.
    """
    rows: list[dict[str, Any]] = []
    identity = {
        "condition_index": condition.get("index"),
        "condition_label": condition.get("label"),
        "values": condition.get("values"),
        "is_baseline": condition.get("is_baseline"),
    }
    aggregated = condition.get("aggregated")
    if not isinstance(aggregated, Mapping):
        return rows
    for step, block in aggregated.items():
        if not isinstance(block, Mapping):
            continue
        for metric, entry in block.items():
            if metric in RESERVED_METRIC_NAMES or not isinstance(entry, Mapping):
                continue
            row = dict(identity)
            row.update({"step": step, "metric": metric, "by_attribute": None, "by_level": None})
            row.update(_present_fields(entry, _CONDITION_METRIC_FIELDS))
            rows.append(row)
        by = block.get("by")
        if not isinstance(by, Mapping):
            continue
        for attribute, levels in by.items():
            if not isinstance(levels, Mapping):
                continue
            for level, level_metrics in levels.items():
                if not isinstance(level_metrics, Mapping):
                    continue
                for metric, entry in level_metrics.items():
                    if metric in RESERVED_METRIC_NAMES or not isinstance(entry, Mapping):
                        continue
                    row = dict(identity)
                    row.update(
                        {
                            "step": step,
                            "metric": metric,
                            "by_attribute": attribute,
                            "by_level": level,
                        }
                    )
                    row.update(_present_fields(entry, _CONDITION_METRIC_FIELDS))
                    rows.append(row)
    return rows


@dataclass(frozen=True)
class Section:
    """One titled block of a report: `title` and `body`, where `body` is
    markdown text or a mapping core knows how to render as a table.

    Frozen is a property of the *type*, not a sentence about intent: a plain
    value class would let a subclass reach into a re-yielded standard
    section and rebind `title` or `body` before it renders, changing a
    number core computed on the way out — and a safety argument in a
    comment is a claim that needs a mutation to back it, not a promise. A
    frozen dataclass guarantees exactly one thing: a re-yielded standard
    section cannot be rebound. It does **not** deep-freeze a `body` that is
    a mapping — the mapping object itself stays as mutable as any other
    dict, and this class makes no claim beyond field assignment.
    """

    title: str
    body: "str | Mapping[str, Any]"


def conditions_section(run: Mapping[str, Any]) -> Section:
    """§ The four standard sections #1: `results.conditions[]` — identity,
    then every metric `aggregated[step]` carries, then its `by` strata when
    declared. A pure function of `run.yaml` alone — no standard section ever
    opens a file under the run directory (Decision 5)."""
    rows: list[dict[str, Any]] = []
    conditions = ((run.get("results") or {}).get("conditions")) or []
    for condition in conditions:
        if isinstance(condition, Mapping):
            rows.extend(_condition_metric_rows(condition))
    return Section(title="Conditions", body={"rows": rows})


def _delta_entry_row(
    *,
    comparison: "str | None",
    of: "str | None",
    against: "str | None",
    step: str,
    metric: str,
    entry: Mapping[str, Any],
) -> dict[str, Any]:
    row = {"comparison": comparison, "of": of, "against": against, "step": step, "metric": metric}
    row.update(_present_fields(entry, _DELTA_FIXED_FIELDS))
    row.update(_present_fields(entry, _DELTA_OPTIONAL_FIELDS))
    return row


def _vs_baseline_rows(condition: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    vs_baseline = condition.get("vs_baseline")
    if not isinstance(vs_baseline, Mapping):
        return rows
    for step, block in vs_baseline.items():
        if not isinstance(block, Mapping):
            continue
        for metric, entry in block.items():
            if metric in RESERVED_METRIC_NAMES or not isinstance(entry, Mapping):
                continue
            rows.append(
                _delta_entry_row(
                    comparison=None,
                    of=condition.get("label"),
                    against="baseline",
                    step=step,
                    metric=metric,
                    entry=entry,
                )
            )
    return rows


def _declared_contrast_rows(contrast: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    comparison = contrast.get("id")
    of = contrast.get("of")
    against = contrast.get("against")
    for step, block in contrast.items():
        if step in ("id", "of", "against") or not isinstance(block, Mapping):
            continue
        for metric, entry in block.items():
            if metric in RESERVED_METRIC_NAMES or not isinstance(entry, Mapping):
                continue
            rows.append(
                _delta_entry_row(
                    comparison=comparison,
                    of=of,
                    against=against,
                    step=step,
                    metric=metric,
                    entry=entry,
                )
            )
    return rows


def deltas_section(run: Mapping[str, Any]) -> Section:
    """§ The four standard sections #2: every condition's `vs_baseline` AS
    WELL AS top-level `results.contrasts` (Decision 5's own correction to
    § The two files' `run.yaml` example, which shows only `vs_baseline` and
    is the reading that produces the bug of silently omitting every
    declared contrast — this is the seam Fixture D exists for)."""
    rows: list[dict[str, Any]] = []
    results = run.get("results") or {}
    for condition in results.get("conditions") or []:
        if isinstance(condition, Mapping):
            rows.extend(_vs_baseline_rows(condition))
    for contrast in results.get("contrasts") or []:
        if isinstance(contrast, Mapping):
            rows.extend(_declared_contrast_rows(contrast))
    return Section(title="Deltas", body={"rows": rows})


class BaseReport:
    """A renderer override for one experiment. Subclass it, override
    `sections`, and compose the standard blocks with `yield from
    super().sections(run, io)` — see docs/reference.md § A report override.

    `format` has **no base default** here. `generate report` always writes
    the `format = "html" | "markdown"` line into the generated class, so a
    base default would be a value no generated class could ever be observed
    to take, and a class that declares none is refused at render rather than
    silently defaulted — the same reason `BaseTemplate.aggregate` has no
    base implementation returning `{}`.
    """

    def section(self, title: str, *, body: "str | Mapping[str, Any]") -> Section:
        """Construct a `Section`. Core's, so a subclass never has to import
        `Section` itself to build one — § A report override's worked block
        calls `self.section("Method agreement", body=...)` and nothing else.
        """
        return Section(title=title, body=body)

    def sections(self, run: Any, io: Any) -> Iterator[Section]:
        """A generator, yielding `Section` values. Core never materializes
        the list before rendering, so an override that yields a cheap
        section first and an expensive figure last prints the cheap one
        first.

        Yields two of the four standard sections so far — Conditions, then
        Deltas — in Decision 5's order; task 6 appends Hypothesis verdicts
        and Attrition after them. Every standard section is a pure function
        of `run` alone: `io` is accepted (an override's own `sections`
        passes it straight through to `yield from super().sections(run,
        io)`) but no standard section reads it, because Decision 5 rules
        that none of the four ever opens a file under the run directory —
        that is `ReportIO.read_condition`'s surface, for an override.
        """
        yield conditions_section(run)
        yield deltas_section(run)


def report_form(path: Path) -> str:
    """Decide whether `path` names a run record or a bundle, from its file
    NAME alone — `"run"` for `run.yaml`, `"bundle"` for `study.yaml`, and
    anything else (including a directory) refused with `E-REPORT-FORM`
    (docs/superpowers/specs/2026-08-21-report-study-design.md Decision 1).

    Not by parsing the document and looking for a discriminating key — a
    truncated `run.yaml` must still read as a run, never silently as a
    bundle — and not by `path.is_dir()` succeeding.

    `diff._form` is **not** reused here even though it looks like the same
    question: it answers "config or run record" over two operands of the
    *same* document family, while this answers "run record or bundle",
    over two *different* document families with two distinct renderers.
    Reusing a predicate that answers a different question is the proxy
    substitution `CLAUDE.md`'s "Answering a question with a proxy" is
    about. What *is* reused, in substance rather than by import, is
    `diff._record_dir`'s rule that a `run.yaml` path's run directory is
    its parent — the same fact, restated where `report` needs it
    (`path.parent` once the form is known to be `"run"`).

    A **directory** argument is refused rather than accepted, unlike
    `diff`'s run-record operand: `diff` accepts one because a run
    directory is one of two things a *run record* operand can be, while
    `report`'s two forms are two file names, and admitting a directory
    would make "which of the two did you mean" a question core answers by
    guessing.

    Nothing here checks whether `path` exists. A missing operand stays
    whatever the read that follows makes of it — `E-IO-FAILED` at exit `1`
    through `main`'s `OSError` handler, exactly as `diff`'s config operand
    does — never caught here.
    """
    if path.is_dir():
        raise ContractError(
            f"{path} is a directory — `report` takes a `run.yaml` or a "
            "`study.yaml` FILE, never a directory",
            code="E-REPORT-FORM",
        )
    if path.name == "run.yaml":
        return "run"
    if path.name == "study.yaml":
        return "bundle"
    raise ContractError(
        f"{path} is named {path.name!r}, neither `run.yaml` nor `study.yaml` — "
        "`report` takes one of those two file names and nothing else",
        code="E-REPORT-FORM",
    )


def _read_repo_root(run_dir: Path) -> Path:
    """`environment/repo_root.txt`, checked for shape, never walked up to.

    `report <run.yaml>` is handed a path inside `output_dir`, and
    `output_dir` may never resolve inside the git repo — the standing
    invariant, checked at generate, at validate, and by every command that
    executes. A walk-up from the argument therefore answers "is there a
    repo above `output_dir`", a different question, and on a correctly
    configured project `provenance.find_repo_root` **raises**
    `E-GIT-NO-REPO` rather than answering it (measured at `ebf642a`) — a
    mutation replacing this read with that walk-up would be caught by a
    crash rather than by a property, which is why it is not one of this
    module's four. The fact is `environment/repo_root.txt`, the run-start
    artifact H8b introduced for the identical problem in `freeze`.
    `provenance.git.repo_root` is not read here: it is the same value
    recorded at run end, `study add` redacts it out of a bundle member, and
    two sources for one fact is how the two drift.

    Missing, empty, or naming something that is not a directory is refused
    with the matching remedy (`E-REPORT-OVERRIDE-REPO`) rather than read as
    "no override" — a silent fail-open is exactly what this function
    exists to avoid.
    """
    repo_root_path = run_dir / "environment" / "repo_root.txt"
    if not repo_root_path.is_file():
        raise ContractError(
            f"no environment/repo_root.txt in {run_dir} — the run was "
            "started by a build before this artifact existed, or the "
            "directory was edited; a report override cannot be discovered",
            code="E-REPORT-OVERRIDE-REPO",
        )
    text = repo_root_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ContractError(
            f"{repo_root_path} is empty — the directory was edited; a "
            "report override cannot be discovered",
            code="E-REPORT-OVERRIDE-REPO",
        )
    repo_root = Path(text)
    if not repo_root.is_dir():
        raise ContractError(
            f"{repo_root_path} names `{text}`, which is not a directory — "
            "the directory was edited; a report override cannot be "
            "discovered",
            code="E-REPORT-OVERRIDE-REPO",
        )
    return repo_root


def _root_package(record: Mapping[str, Any]) -> str:
    """This run's own `config.entrypoint`'s root package — the direct
    question Decision 3 poses (docs/superpowers/specs/2026-08-21-report-
    study-design.md), and the only fact this function consults: not a
    directory scan of `src/`, not a module-name prefix, not a marker
    stamped on a class, not "does this file sit under this repo", and not
    definition order among two subclasses.

    A hand-edited record can hold an `entrypoint` that is absent, empty, or
    not a string, and a `None` reaching `.partition` would be a traceback
    rather than a diagnostic — so every shape but a well-formed
    `<module>:<attribute>` string is routed to a refusal with a remedy
    (`E-REPORT-OVERRIDE-ENTRYPOINT`), never to "no override", which would
    be this function's own fail-open.
    """
    config = record.get("config") if isinstance(record, Mapping) else None
    entrypoint = config.get("entrypoint") if isinstance(config, Mapping) else None
    if not isinstance(entrypoint, str) or not entrypoint:
        raise ContractError(
            f"this run's config.entrypoint is {entrypoint!r}, not a "
            "non-empty string — the record was edited by hand; a report "
            "override cannot be discovered",
            code="E-REPORT-OVERRIDE-ENTRYPOINT",
        )
    module_name, _, attr = entrypoint.partition(":")
    if not module_name or not attr:
        raise ContractError(
            f"this run's config.entrypoint {entrypoint!r} is not "
            "`<module>:<attribute>` — the record was edited by hand; a "
            "report override cannot be discovered",
            code="E-REPORT-OVERRIDE-ENTRYPOINT",
        )
    return module_name.split(".", 1)[0]


def render_with_override(
    run_dir: Path,
    record: Mapping[str, Any],
    render: Callable[["type[BaseReport] | None"], T],
) -> T:
    """Discover this run's own `BaseReport` override, if it declares one,
    and call `render` with the resolved subclass — or `None` when there is
    no override — entirely inside the `sys.path` window opened to import
    it (docs/superpowers/specs/2026-08-21-report-study-design.md
    Decision 3).

    **This does NOT call `base_experiment.load_experiment`.** Discovery
    needs `<root_pkg>.report`, not the entrypoint's own `<module>:
    <attribute>`, so it re-implements `load_experiment`'s window by
    calling the same two steps in the same order — purge `sys.modules` for
    the root package first (`load_experiment`'s own docstring: "two
    projects in one process can declare the same package name", and this
    repo's own suite runs many projects in one process off a scaffold
    whose package name is stable), then insert `<repo_root>/src` on
    `sys.path` — rather than importing and calling `load_experiment`
    itself. One consequence of re-implementing rather than calling: a
    corrupt or missing `entrypoint` here is this function's OWN refusal,
    `E-REPORT-OVERRIDE-ENTRYPOINT` (`_root_package` above), never
    `E-ENTRYPOINT-IMPORT`.

    The render happens before `sys.path` is popped, inside the same `try`
    whose `finally` pops it — never after — because a `sections` body that
    lazily imports a sibling module at render time would otherwise fail on
    an already-restored path: H7a's "state read at the wrong moment" in a
    new costume.

    Three refusals, and a fourth case that is not one:

    - no `<root_pkg>/report.py` at all → **no override**: `render(None)`,
      the ordinary case (`generate report` is opt-in).
    - `<root_pkg>.report` exists and raises on import →
      `E-REPORT-OVERRIDE-IMPORT`, distinguished from the case above by the
      import machinery's own answer — `ModuleNotFoundError.name` naming
      the exact module this call tried to import — never by catching
      every exception alike.
    - `<root_pkg>.report` defines no `BaseReport` subclass, or more than
      one → `E-REPORT-OVERRIDE-CLASS`. "More than one" is refused rather
      than resolved by definition order: order is exactly the proxy this
      function forbids, and a project has one report.
    """
    repo_root = _read_repo_root(run_dir)
    root_pkg = _root_package(record)
    module_name = f"{root_pkg}.report"
    src_entry = str(repo_root / "src")

    for cached in [
        name for name in sys.modules if name == root_pkg or name.startswith(root_pkg + ".")
    ]:
        del sys.modules[cached]
    sys.path.insert(0, src_entry)
    try:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                return render(None)
            raise ContractError(
                f"{module_name!r} could not be imported: {exc}",
                code="E-REPORT-OVERRIDE-IMPORT",
            ) from exc
        except Exception as exc:
            raise ContractError(
                f"{module_name!r} could not be imported: {exc}",
                code="E-REPORT-OVERRIDE-IMPORT",
            ) from exc

        subclasses = [
            obj
            for obj in vars(module).values()
            if isinstance(obj, type)
            and issubclass(obj, BaseReport)
            and obj is not BaseReport
            and obj.__module__ == module.__name__
        ]
        if len(subclasses) != 1:
            raise ContractError(
                f"{module_name!r} defines {len(subclasses)} `BaseReport` "
                "subclasses, not exactly one",
                code="E-REPORT-OVERRIDE-CLASS",
            )
        return render(subclasses[0])
    finally:
        # Removed by IDENTITY (the exact path string this call inserted),
        # never by POSITION (`sys.path.pop(0)`). `sections()` runs inside
        # this window by design, and an override reaching for a vendored
        # directory via `sys.path.insert(0, ...)` — an ordinary idiom — is
        # user code this window invites in; a positional pop would then
        # remove THAT entry and leak `src_entry` on every path, success or
        # refusal alike. `if` rather than an unguarded `remove` because a
        # refusal raised before the insert never reaches this `finally`
        # missing its own entry, but an override that removed our entry
        # itself (or cleared `sys.path` outright) must not turn our own
        # cleanup into a second, unhandled exception.
        if src_entry in sys.path:
            sys.path.remove(src_entry)

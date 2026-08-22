# src/publishable/report.py
"""`BaseReport`, `Section`, override discovery, and `command_report`.
docs/reference.md § A report override renders one experiment's own
figures, § The importable surface, § Operation commands' `report` row.
`cli._dispatch` imports `command_report` inside its own function body,
joining `OPERATION_COMMANDS`'s existing one-path arm — this module
imports nothing from `cli` at all. The bundle form (`report study.yaml`)
renders here too — `read_bundle`, `_bundle_cross_checks`, `render_bundle`
— entirely through this module's own coded refusals, never through
`cli._report_not_built`.
"""

import importlib
import sys
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

import yaml

from publishable.artifacts import ReportIO, derive_step_scopes_and_repeats
from publishable.diagnostics import EXIT_OK, EXIT_WRONG, Collector
from publishable.errors import ContractError, PublishableError
from publishable.lineage import read_record_file
from publishable.secrets import credential_values
from publishable.stats import RESERVED_METRIC_NAMES
from publishable.templates.registry import get_template
from publishable.validate import declared_credential_names_for

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


def _is_metric_entry(value: Any) -> bool:
    """A genuine metric entry, identified by what it CARRIES — `value`,
    always present in the measured record's own field inventory — never by
    the key it sits under. Major 3 (task-b4 review): Decision 5's own
    grounds for excluding `by` were "the record `report` reads can never
    hold a metric called `by`", which `cli.py`'s `W-STATS-STRATUM-SHADOWED`
    disproves in writing — a recorded column named `by` whose every value is
    a number keeps that value on the write side, as a real metric entry. A
    NON-numeric one can too — a mixed `by` column still keeps a full
    metric block, computed over its contributing units. The record can
    hold either shape under this key, and a structural test is what reads
    both.
    Filtering by the STRING
    `"by"` is the fifth instance on this project of answering a structural
    question with a name (a module-name prefix, a class marker, state read
    at the wrong moment, a one-spelling grep, `pop(0)`), so this asks the
    direct question instead: does this value look like a metric, not what
    is it called.
    """
    return isinstance(value, Mapping) and "value" in value


def _is_strata_block(value: Any) -> bool:
    """The `report_by` strata shape and nothing else: attribute → level →
    metric → entry, three `Mapping`s deep with a genuine metric entry
    (`_is_metric_entry`) at the bottom of every branch. Never identified by
    sitting under the key `"by"` — `cli.py` does not write this block at all
    when a recorded column of that name exists, numeric or not
    (`W-STATS-STRATUM-SHADOWED`: "no strata are reported for this step"), so
    the two shapes never actually collide under one key, but a structural
    test costs nothing to make correct in the collision's absence too.
    """
    if not isinstance(value, Mapping) or not value:
        return False
    for levels in value.values():
        if not isinstance(levels, Mapping) or not levels:
            return False
        for level_metrics in levels.values():
            if not isinstance(level_metrics, Mapping) or not level_metrics:
                return False
            for entry in level_metrics.values():
                if not _is_metric_entry(entry):
                    return False
    return True


def _condition_metric_rows(condition: Mapping[str, Any]) -> list[dict[str, Any]]:
    """One row per metric in one condition's `aggregated` block, plus one row
    per `by[attribute][level]` stratum metric when `statistics.report_by` was
    declared and no recorded column shadows it. Which of the two a given
    key's value is is decided STRUCTURALLY (`_is_metric_entry` /
    `_is_strata_block`), never by the key's name — see Major 3, task-b4
    review, and `docs/superpowers/spec-defects.md`'s "New reserved metric
    name: `by`" entry, whose own rule for the write side ("the column
    wins") this read side must agree with rather than silently override.
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
            if not _is_metric_entry(entry):
                continue
            row = dict(identity)
            row.update({"step": step, "metric": metric, "by_attribute": None, "by_level": None})
            row.update(_present_fields(entry, _CONDITION_METRIC_FIELDS))
            rows.append(row)
        for value in block.values():
            if not _is_strata_block(value):
                continue
            for attribute, levels in value.items():
                for level, level_metrics in levels.items():
                    for metric, entry in level_metrics.items():
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
    """`by` cannot reach this loop through an honest record: `cli.py`'s
    `_comparison_step_blocks` already drops it from every comparison's
    metric set unconditionally, on the write side, before a `vs_baseline`
    block is ever assembled — so the `RESERVED_METRIC_NAMES` guard below
    is DEFENSIVE rather than reachable (unlike the Conditions-side
    structural check `_is_metric_entry`/`_is_strata_block` replace, which
    guards a real collision). Kept anyway, on the precedent that a second,
    cheap check costs nothing when the first one's own guarantee ever
    moves — noted here in a comment rather than left to look pinned by a
    test that cannot reach it (m1, task-b4 review).
    """
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
    """Same defensive note as `_vs_baseline_rows` above: `_comparison_step_
    blocks` drops `by` from a declared contrast's metric set on the write
    side too, so the `RESERVED_METRIC_NAMES` guard below is unreachable
    from an honest record (m1, task-b4 review).

    The `{"id", "of", "against"}` blacklist separating this entry's own
    identity keys from its step keys is correct against `cli.py`'s
    `_compute_declared_contrasts` today — that function's own entry is
    exactly `{id, of, against}` plus a step -> metric mapping from
    `_comparison_step_blocks` (m2, task-b4 review) — but it is a literal
    set rather than a shared constant, unlike every other key decision
    this module makes. A future mapping-valued key added beside those
    three would render as a phantom step; a step genuinely named `id`,
    `of` or `against` would lose its rows. Neither is reachable from the
    schema this build validates against.
    """
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


# Decision 5's Hypothesis-verdicts row, plus § Corrections correction 9:
# `family_size`/`family` are in the record and not in the design's own list.
# `verdict_rests_on` is the field that distinguishes `computed` from
# `reported` — § The unit table is the inference base's rule that the one
# interval core stores without computing is an `Estimate` a `summary` step
# returned.
_HYPOTHESIS_FIELDS = (
    "id",
    "kind",
    "declared_in",
    "observed",
    "verdict_evaluated_on",
    "supported",
    "verdict_rests_on",
)
# Absent on an uncounted (`reported`) verdict — `hypotheses._is_counted`
# excludes it from the family, so there is no family to name. Read as a
# MAPPING generically, never by two literal keys: a hypothesis family's
# `family` is `{hypotheses: N}`, a different shape from a comparison
# family's `{comparisons, metrics}` — the same `_present_fields` helper the
# Deltas section already reads `family_size`/`family` through, on purpose,
# so the day the two sections share a table-building helper neither breaks
# on the other's shape.
_HYPOTHESIS_OPTIONAL_FIELDS = ("family_size", "family")


def hypotheses_section(run: Mapping[str, Any]) -> Section:
    """§ The four standard sections #3: `results.hypotheses[]`."""
    rows: list[dict[str, Any]] = []
    for verdict in (run.get("results") or {}).get("hypotheses") or []:
        if not isinstance(verdict, Mapping):
            continue
        row = _present_fields(verdict, _HYPOTHESIS_FIELDS)
        row.update(_present_fields(verdict, _HYPOTHESIS_OPTIONAL_FIELDS))
        rows.append(row)
    return Section(title="Hypothesis verdicts", body={"rows": rows})


def _metric_n_rows(run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Each metric's own `n: {resolved, completed, ineligible, failed}`,
    read through the identical `_condition_metric_rows` traversal the
    Conditions section uses (so a `by` stratum is excluded here on the same
    grounds, without a second exclusion to keep in step) and projected down
    to just the identifying columns and `n` — Attrition's own concern is
    what happened to units, not a metric's value or method."""
    rows: list[dict[str, Any]] = []
    for condition in (run.get("results") or {}).get("conditions") or []:
        if not isinstance(condition, Mapping):
            continue
        for row in _condition_metric_rows(condition):
            rows.append(
                {
                    "kind": "metric_n",
                    "condition_index": row["condition_index"],
                    "condition_label": row["condition_label"],
                    "step": row["step"],
                    "metric": row["metric"],
                    "by_attribute": row["by_attribute"],
                    "by_level": row["by_level"],
                    "n": row.get("n"),
                }
            )
    return rows


def _execution_rows(run: Mapping[str, Any]) -> list[dict[str, Any]]:
    """`execution`'s per-execution `status`, walked through all three of
    `shared`, `conditions[]` (with the repeat nesting) and `summary` —
    never only `conditions[]`, which is the mutation this function exists
    to be caught by whenever a run has a `summary` step (Fixture R does).
    A `conditions[].steps[step]` entry that itself carries `status` is a
    condition-scoped step; one that does not is a mapping of repeat labels
    to entries — the same discriminator `artifacts.derive_step_scopes_and_
    repeats` already uses over the same block (§ Corrections correction
    2), restated here rather than imported because that helper derives
    SCOPES for `ReportIO`, a different consumer of the same fact.
    """
    rows: list[dict[str, Any]] = []
    execution = run.get("execution")
    if not isinstance(execution, Mapping):
        return rows
    shared = execution.get("shared")
    if isinstance(shared, Mapping):
        for step, entry in shared.items():
            if isinstance(entry, Mapping):
                rows.append({"kind": "execution", "scope": "shared", "step": step, **entry})
    for condition in execution.get("conditions") or []:
        if not isinstance(condition, Mapping):
            continue
        index = condition.get("index")
        label = condition.get("label")
        steps = condition.get("steps")
        if not isinstance(steps, Mapping):
            continue
        for step, value in steps.items():
            if not isinstance(value, Mapping):
                continue
            if "status" in value:
                rows.append(
                    {
                        "kind": "execution",
                        "scope": "condition",
                        "condition_index": index,
                        "condition_label": label,
                        "step": step,
                        **value,
                    }
                )
            else:
                for repeat_label, entry in value.items():
                    if isinstance(entry, Mapping):
                        rows.append(
                            {
                                "kind": "execution",
                                "scope": "repeat",
                                "condition_index": index,
                                "condition_label": label,
                                "repeat": repeat_label,
                                "step": step,
                                **entry,
                            }
                        )
    summary = execution.get("summary")
    if isinstance(summary, Mapping):
        for step, entry in summary.items():
            if isinstance(entry, Mapping):
                rows.append({"kind": "execution", "scope": "summary", "step": step, **entry})
    return rows


def attrition_section(run: Mapping[str, Any]) -> Section:
    """§ The four standard sections #4: `provenance.units.n`; each metric's
    own `n`; every execution's `status` across `shared`, `conditions[]`
    (with its repeat nesting) and `summary`; the top-level `status`; and
    `provenance.input_manifest_changed` — measured to be a LIST, so this
    renders what it holds rather than coercing it to a boolean (task 6 step
    4's own mutation: `bool([])` is `False`, and a section that printed
    `false` for an empty list would be indistinguishable from one that
    printed `false` for a genuinely boolean field elsewhere).

    Does **not** claim `nondeterministic` — see the filing in
    `docs/superpowers/spec-defects.md`, "`nondeterministic` is documented
    as a `run.yaml` field and a thing `report` notes, and nothing writes
    it or reads it back" — because nothing in this build writes it onto an
    execution or a record,
    and a section printing `nondeterministic: false` for every execution
    would be reporting a default nothing measured.
    """
    rows: list[dict[str, Any]] = [{"kind": "status", "status": run.get("status")}]
    provenance = run.get("provenance")
    if isinstance(provenance, Mapping):
        units = provenance.get("units")
        if isinstance(units, Mapping):
            rows.append({"kind": "provenance_units", **units})
        if "input_manifest_changed" in provenance:
            rows.append(
                {"kind": "input_manifest_changed", "value": provenance["input_manifest_changed"]}
            )
    rows.extend(_metric_n_rows(run))
    rows.extend(_execution_rows(run))
    return Section(title="Attrition", body={"rows": rows})


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
        the list before rendering, so a later `Section`'s body is never
        constructed if an earlier one raises. **Sized down (whole-branch
        review, Minor 5): this does NOT mean an override's cheap section
        prints before its expensive one finishes** — `command_report`
        collects `render_with_override`'s full return into one `str`
        before printing it once, and both renderers join every section's
        text into one string before returning it, so nothing reaches
        stdout until every section — cheap and expensive alike — has been
        rendered. The lazy generator saves the LATER SECTION'S OWN
        construction when an earlier one refuses; it buys no streaming
        of output.

        Yields all four standard sections, in Decision 5's order:
        Conditions, Deltas, Hypothesis verdicts, Attrition. Every one is a
        pure function of `run` alone: `io` is accepted (an override's own
        `sections` passes it straight through to `yield from
        super().sections(run, io)`) but no standard section reads it,
        because Decision 5 rules that none of the four ever opens a file
        under the run directory — that is `ReportIO.read_condition`'s
        surface, for an override.
        """
        yield conditions_section(run)
        yield deltas_section(run)
        yield hypotheses_section(run)
        yield attrition_section(run)


# Decision 16: two renderers, one section stream. Both consume the SAME
# generator — a section's `body` is markdown text or a mapping core tables —
# and differ only in how they emit a heading, a table and a block. No third
# representation and no template language, so both call this one cell
# formatter rather than each inventing their own stringification.
_VALID_FORMATS = frozenset({"markdown", "html"})


def _format_cell(value: Any) -> str:
    """One value, as text — shared by both renderers so a formatting
    decision (how a `None`, a nested mapping, or a list renders) is made
    once rather than twice and risking drift between them."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Mapping):
        return "{" + ", ".join(f"{k}: {_format_cell(v)}" for k, v in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_format_cell(v) for v in value) + "]"
    return str(value)


def _table_columns(rows: "list[Mapping[str, Any]]") -> list[str]:
    """The union of every row's keys, in first-seen order — a section's
    rows are not required to share one key set (a `by` stratum row and a
    top-level metric row differ by exactly `repeat_spread`), so the column
    set is derived from what the rows actually carry rather than declared
    once and risking a silently dropped field."""
    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    return columns


def _as_rows(body: "str | Mapping[str, Any]") -> "list[Mapping[str, Any]] | None":
    """`body["rows"]` when `body` is one of the four standard sections'
    own shape; a one-row `{key, value}` table over an arbitrary mapping an
    override handed `self.section(..., body=...)`, so a renderer never has
    to special-case a shape this module did not itself construct; `None`
    for a `str` body, which is a block rather than a table.

    A `body` that is neither `str` nor a mapping — an override's own
    `self.section(..., body=...)` handed something else entirely, an
    `int` or a `list` say — is refused with `E-REPORT-BODY` rather than
    reaching `.get` and raising a bare `AttributeError` out of a renderer
    (batch 4 review, m10 — `report` runs user code, and this module
    already refuses a bad `format` with a coded diagnostic, so leaving
    exactly this shape to a traceback was the one asymmetry). **Scoped to
    exactly this fault**: a `sections()` that yields something other than
    a `Section` entirely — bypassing `self.section()` itself — fails on
    `.title`/`.body` before this function is ever reached, is a
    different fault, and no decision or brief assigns it a guard.
    """
    if isinstance(body, str):
        return None
    if not isinstance(body, Mapping):
        raise ContractError(
            f"a Section's body is {type(body).__name__}, not `str` or a "
            "mapping — an override's `self.section(..., body=...)` handed "
            "this module something it cannot render",
            code="E-REPORT-BODY",
        )
    rows = body.get("rows")
    if isinstance(rows, list):
        return rows
    return [{"key": k, "value": v} for k, v in body.items()]


def _render_markdown_section(section: Section) -> str:
    heading = f"## {section.title}\n"
    rows = _as_rows(section.body)
    if rows is None:
        return f"{heading}\n{section.body}\n"
    if not rows:
        return f"{heading}\n*(none)*\n"
    columns = _table_columns(rows)
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_format_cell(row.get(c)) for c in columns) + " |")
    return heading + "\n" + "\n".join(lines) + "\n"


def render_markdown(sections: Iterator[Section]) -> str:
    """The markdown emitter: `## ` for a heading, a pipe table for rows, the
    text verbatim for a `str` block."""
    return "\n".join(_render_markdown_section(section) for section in sections)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def _render_html_section(section: Section) -> str:
    heading = f"<h2>{_escape_html(section.title)}</h2>"
    rows = _as_rows(section.body)
    if rows is None:
        return heading + f"<pre>{_escape_html(str(section.body))}</pre>"
    if not rows:
        return heading + "<p><em>(none)</em></p>"
    columns = _table_columns(rows)
    head = "".join(f"<th>{_escape_html(c)}</th>" for c in columns)
    body_rows = "".join(
        "<tr>"
        + "".join(f"<td>{_escape_html(_format_cell(row.get(c)))}</td>" for c in columns)
        + "</tr>"
        for row in rows
    )
    return heading + f"<table><thead><tr>{head}</tr></thead><tbody>{body_rows}</tbody></table>"


def render_html(sections: Iterator[Section]) -> str:
    """The HTML emitter: self-contained and offline (Decision 16) — no
    external stylesheet, script or font, ever, because a bundle render is
    explicitly offline and an archived report degrading on a dead link is
    exactly what that promise forbids. An override that embeds a figure
    embeds it; this function never fetches anything to build the page
    around one.
    """
    body = "".join(_render_html_section(section) for section in sections)
    return f'<!doctype html><html><head><meta charset="utf-8"></head><body>{body}</body></html>'


def render_report(report_cls: "type[BaseReport] | None", run: Mapping[str, Any], io: Any) -> str:
    """Render `run` through `report_cls` (or, when `None` — no override
    declared — through `BaseReport` itself) and return the finished text.
    The one place `format` is read and the one place `E-REPORT-FORMAT` is
    raised.

    `report_cls is None` is the ordinary case (`generate report` is
    opt-in) and is not the class-declares-nothing refusal: there is no
    class here for "declared" and "omitted" to disagree about, so core
    renders its own four standard sections as markdown, unconditionally.
    A REAL class — the override subclass `render_with_override` resolved —
    that nonetheless declares no `format` (or a value other than
    `"markdown"`/`"html"`) is refused, because a class that exists and
    said nothing is exactly the case Decision 2 rules on: a base default
    would make that indistinguishable from a class that meant to say
    `"markdown"`.
    """
    fmt: Any
    if report_cls is None:
        report: BaseReport = BaseReport()
        fmt = "markdown"
    else:
        report = report_cls()
        fmt = getattr(report_cls, "format", None)
        if fmt not in _VALID_FORMATS:
            raise ContractError(
                f"{report_cls.__module__}.{report_cls.__qualname__} declares "
                f'`format` = {fmt!r}, not "markdown" or "html" — report cannot '
                "render it",
                code="E-REPORT-FORMAT",
            )
    sections = report.sections(run, io)
    if fmt == "html":
        return render_html(sections)
    return render_markdown(sections)


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
    whatever the read that follows makes of it, never caught here.
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


def _report_io_from_record(run_dir: Path, record: Mapping[str, Any]) -> ReportIO:
    """`ReportIO`, built from a run record alone — the identical
    construction `tests/test_report.py`'s own `_report_io_from_record`
    helper performs directly, now the production path `command_report`
    calls for every run-form render (Decision 4). Built unconditionally,
    whether or not the resolved override's `sections()` ever touches
    `io` — no standard section does (Decision 5) — the same posture
    § Corrections correction 13 rules for a bundle's construction one
    file over.
    """
    execution = record["execution"]
    step_scopes, repeats = derive_step_scopes_and_repeats(execution)
    conditions = [(c["index"], c["label"]) for c in record["results"]["conditions"]]
    return ReportIO(
        run_dir=run_dir,
        input_dir=Path(record["config"]["data"]["input_dir"]),
        conditions=conditions,
        repeats=repeats,
        step_scopes=step_scopes,
    )


# ---------------------------------------------------------------------------
# The bundle form: `report <study.yaml>` (Decisions 1, 7, 8; task 10).
#
# **No override discovery happens anywhere below.** Every function here
# builds `Section` values directly from a parsed `study.yaml` and its
# members' parsed records — never through `render_with_override`, which is
# the run form's own machinery for importing `<root_pkg>.report`. A bundle
# member carries no `environment/repo_root.txt` (§ Building one's tree is
# bare `<name>.run.yaml` files beside `study.yaml`, nothing else), so this
# module structurally cannot reach a sibling `report.py` from here — there
# is no call site that would even attempt to resolve one.
# ---------------------------------------------------------------------------


def _resolve_bundle_member(bundle_dir: Path, name: str, file_value: Any) -> Path:
    """`study.yaml`'s `runs.<name>.file`, resolved **relative to the bundle
    directory** and refused if it is absent, malformed, escapes the bundle,
    or names something not there — all `E-STUDY-UNREADABLE` (task 10's own
    brief, step 1): "a `runs` entry whose `file` is not in the bundle." A
    member that IS in the bundle but corrupt once read is a different,
    adjacent fault (`E-UPSTREAM-RECORD-*`, raised by `read_record_file`
    itself) — this function's only job is locating the file, never parsing
    it.

    Containment (`..`, an absolute path, a symlink leading outside) is
    checked the same way `artifacts.StepIO._contained` checks it for an
    artifact read — "every reference is resolved relative to the bundle
    directory and nothing resolves outside it" (task 10's brief, step 2) —
    restated here rather than imported, because that predicate is scoped to
    a run directory's own step layout and this is a different base entirely.
    """
    if not isinstance(file_value, str) or not file_value:
        raise ContractError(
            f"study.yaml's runs.{name!r}.file is {file_value!r}, not a non-empty string",
            code="E-STUDY-UNREADABLE",
        )
    base = bundle_dir.resolve()
    candidate = (bundle_dir / file_value).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise ContractError(
            f"study.yaml's runs.{name!r}.file ({file_value!r}) resolves "
            "outside the bundle directory — every reference in a bundle "
            "must resolve inside it",
            code="E-STUDY-UNREADABLE",
        ) from None
    if not candidate.is_file():
        raise ContractError(
            f"study.yaml names runs.{name!r}.file = {file_value!r}, which "
            "is not a file in the bundle",
            code="E-STUDY-UNREADABLE",
        )
    return candidate


def read_bundle(path: Path) -> tuple[dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    """Parse `study.yaml` at `path` and every member it names, in the order
    `runs` declares them. Returns `(bundle_doc, members)`, `members` a list
    of `(name, record)` pairs — a list rather than a dict because a bundle's
    own render walks it in declared order, and `dict` would silently keep
    that guarantee only as long as nobody re-sorted it.

    `E-STUDY-UNREADABLE`: `path` is absent, not valid YAML, does not parse
    to a mapping, or its `runs` key is not a mapping — the study.yaml-level
    faults task 10's brief step 1 names. A `runs` entry that is not itself a
    mapping is the identical fault one level down. Each member's `file` is
    resolved through `_resolve_bundle_member` (same code, an adjacent
    reason), then read through `read_record_file` (task 4) — whose OWN three
    refusals (`E-UPSTREAM-RECORD-MISSING/-UNREADABLE/-VERSION`) are left to
    propagate unwrapped, because a member that IS in the bundle and corrupt
    is a distinguishable fault from one that is not there at all.
    """
    if not path.exists():
        raise ContractError(f"no study.yaml at {path}", code="E-STUDY-UNREADABLE")
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ContractError(f"{path} is not valid YAML: {exc}", code="E-STUDY-UNREADABLE") from exc
    if not isinstance(doc, dict):
        raise ContractError(
            f"{path} did not parse to a mapping — it was edited or truncated",
            code="E-STUDY-UNREADABLE",
        )
    runs = doc.get("runs")
    if not isinstance(runs, Mapping):
        raise ContractError(
            f"{path}'s `runs` is {runs!r}, not a mapping",
            code="E-STUDY-UNREADABLE",
        )
    bundle_dir = path.parent
    members: list[tuple[str, dict[str, Any]]] = []
    for name, entry in runs.items():
        if not isinstance(entry, Mapping):
            raise ContractError(
                f"{path}'s runs.{name!r} is {entry!r}, not a mapping",
                code="E-STUDY-UNREADABLE",
            )
        member_path = _resolve_bundle_member(bundle_dir, str(name), entry.get("file"))
        members.append((str(name), read_record_file(member_path)))
    return doc, members


def _bundle_cross_checks(
    members: list[tuple[str, dict[str, Any]]],
) -> list[tuple[str, str]]:
    """Decision 8's two cross-checks, over bundled members already grouped
    by `provenance.git.commit`. **Compares recorded figures and computes
    neither** — never `hashes.code_hash`, never `apparatus.apparatus_hash`
    — because a second answer computed here could disagree with the one
    `diff` reports over the same field, "the one figure this project treats
    as authoritative" (`diff`'s own Decision 2).

    Two runs sharing a commit must share a `code_hash` (same commit, same
    two trees); when they do not, that is a real finding about the bundle,
    named `W-STUDY-CODE-HASH-MISMATCH`. The identical shape one column over
    for `provenance.apparatus.hash`, `W-STUDY-APPARATUS-MISMATCH`, with one
    difference task 10's brief step 4 states explicitly: a member whose
    `provenance.apparatus` is `null` is EXCLUDED from that comparison rather
    than counted a mismatch — "this experiment declares no probe" is not a
    deployment claim, and refusing on it would make every bundle of
    `generic` runs print a notice about a deployment nobody claimed.

    Returns `(code, message)` pairs. **The message states what was found
    and diagnoses no cause** — task 10's brief step 4: a dirty tree, an
    uncommitted `templates/**` edit, and another experiment's package
    moving inside the two hashed trees are three candidates among others,
    and naming one as fact would be the comment-claiming-a-guarantee habit
    one layer out.
    """
    by_commit: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for name, record in members:
        provenance = record.get("provenance")
        git = provenance.get("git") if isinstance(provenance, Mapping) else None
        commit = git.get("commit") if isinstance(git, Mapping) else None
        if isinstance(commit, str) and commit:
            by_commit.setdefault(commit, []).append((name, record))

    notices: list[tuple[str, str]] = []
    for commit, group in sorted(by_commit.items()):
        if len(group) < 2:
            continue

        # Minor 2 (whole-branch review): a record with NO `code_hash` at
        # all (missing or `None`) is excluded from this comparison, on
        # the identical grounds Decision 8 already gives for a `null`
        # apparatus — "this experiment declares no probe is not a
        # deployment claim" reads the same way as "this record carries
        # no code identity claim at all". Without the filter, the
        # missing figure's own `None` printed in the notice's own text,
        # which answered "not captured" as though it were a real,
        # disagreeing hash.
        code_hash_present = [
            (name, record.get("code_hash"))
            for name, record in group
            if record.get("code_hash") is not None
        ]
        code_hashes = {h for _, h in code_hash_present}
        if len(code_hash_present) > 1 and len(code_hashes) > 1:
            names = ", ".join(sorted(name for name, _ in code_hash_present))
            notices.append(
                (
                    "W-STUDY-CODE-HASH-MISMATCH",
                    f"runs {names} all record commit {commit} and their "
                    f"code_hash differs ({sorted(str(h) for h in code_hashes)})",
                )
            )

        # Minor 2's identical fix one column over: an apparatus block
        # present as a MAPPING but carrying no `hash` key at all is
        # excluded the same way a `null` apparatus already is — a block
        # with no hash to compare is not a deployment claim either.
        apparatus_present: list[tuple[str, Mapping[str, Any]]] = []
        for name, record in group:
            provenance = record.get("provenance")
            app = provenance.get("apparatus") if isinstance(provenance, Mapping) else None
            if isinstance(app, Mapping) and app.get("hash") is not None:
                apparatus_present.append((name, app))
        apparatus_hashes = {app.get("hash") for _, app in apparatus_present}
        if len(apparatus_present) > 1 and len(apparatus_hashes) > 1:
            names = ", ".join(sorted(name for name, _ in apparatus_present))
            notices.append(
                (
                    "W-STUDY-APPARATUS-MISMATCH",
                    f"runs {names} all record commit {commit} and their "
                    f"provenance.apparatus.hash differs "
                    f"({sorted(str(h) for h in apparatus_hashes)})",
                )
            )
    return notices


def _bundle_header_section(name: str, record: Mapping[str, Any]) -> Section:
    """One member's identity line — `run_id`, `status`, and a `draft` label
    when the record carries `draft: true`. Decision 7's asymmetry: a
    bundle FLAGS a draft member rather than refusing the whole render, "a
    bundle is a set, and refusing the whole render because one of five runs
    was a draft would throw away four legitimate renders." The flag lives
    here, in prose text a reader cannot miss, rather than as a fifth column
    threaded through every one of the four standard sections' tables.
    """
    lines = [f"run_id: {record.get('run_id')}", f"status: {record.get('status')}"]
    if record.get("draft") is True:
        lines.append(
            "**draft** — this run's code state is not reachable from any "
            "commit; it is included here but is not a citable result on "
            "its own"
        )
    return Section(title=name, body="\n".join(lines))


def _bundle_hypotheses_rows(
    members: list[tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Every member's `results.hypotheses[]`, tagged with the bundle's own
    name for that run — "collecting every declared hypothesis into one
    table" (`reference.md` § Building one), read through the identical
    field set `hypotheses_section` reads for a single run, so the two never
    drift about what a hypothesis entry carries.
    """
    rows: list[dict[str, Any]] = []
    for name, record in members:
        for verdict in (record.get("results") or {}).get("hypotheses") or []:
            if not isinstance(verdict, Mapping):
                continue
            row: dict[str, Any] = {"run": name}
            row.update(_present_fields(verdict, _HYPOTHESIS_FIELDS))
            row.update(_present_fields(verdict, _HYPOTHESIS_OPTIONAL_FIELDS))
            rows.append(row)
    return rows


def render_bundle(bundle_dir: Path, members: list[tuple[str, dict[str, Any]]]) -> str:
    """The bundle render: every member's identity line and its four
    standard sections, in declared order, plus one combined Hypotheses
    table over the whole bundle — "and nothing else" (task 10's brief step
    2). Always markdown: a bundle has no override to declare `format`
    (Decision 16's `report_cls is None` case, over every member alike), and
    HTML being self-contained and offline is a run-form override's own
    property, never a bundle's.

    Each member's four standard sections come from `BaseReport().sections`
    directly — **never** `render_with_override`, which is the run form's
    own discovery entry point and is not called anywhere in this function
    or by anything it calls. `ReportIO` is still constructed (§ Corrections,
    correction 13: "a bundle render still has to hand `sections` an `io`,
    and the design rules none... no override runs on a bundle and no
    standard section touches `io`, so the object is unreachable in that
    form"), over `bundle_dir` — a bundle holds bare record files, not run
    directories, so there is no other directory to build it from.

    Building a member's `ReportIO` over a malformed `execution`,
    `results.conditions`, or `config.data.input_dir` is the run form's own
    `E-REPORT-RECORD-INCOMPLETE` fault, reused here rather than reminted
    (Decision 15's "the row widens" precedent). **Whole-branch review,
    Major 5**: `KeyError`/`TypeError` is NOT the complete set — a shape
    like `execution: "x"` reaches `.get` on a `str` inside
    `derive_step_scopes_and_repeats` and raises `AttributeError`, which
    escaped both this guard and the run form's identical one until this
    fix. The tuple below is widened at both call sites; the § Errors row
    is corrected in the same commit to stop naming `execution` as covered
    when it was not.
    """
    sections: list[Section] = []
    for name, record in members:
        sections.append(_bundle_header_section(name, record))
        try:
            io = _report_io_from_record(bundle_dir, record)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
            raise ContractError(
                f"bundle member {name!r} parses and has a `run_id`, but is "
                f"missing or malformed at {exc!r} — `report` needs "
                "`execution`, `results.conditions` and "
                "`config.data.input_dir` to build the read-only artifact "
                "accessor the four standard sections read",
                code="E-REPORT-RECORD-INCOMPLETE",
            ) from exc
        sections.extend(BaseReport().sections(record, io))
    sections.append(Section(title="Hypotheses", body={"rows": _bundle_hypotheses_rows(members)}))
    return render_markdown(iter(sections))


def command_report(path: Path) -> int:
    """`report <run.yaml>`, end to end (docs/reference.md § Operation
    commands' `report` row; design Decisions 1, 6, 7; plan § Corrections
    correction 7). Dispatched from `cli._dispatch`'s `OPERATION_COMMANDS`
    arm, joining `validate`/`run`/`freeze`'s existing one-path enforcement
    rather than adding a second one.

    **Exit codes (Decision 6).** `1` for `report`'s OWN refusals — a
    malformed operand (`E-REPORT-FORM`), an unresolvable template
    (`E-TEMPLATE-LOAD`/`E-TEMPLATE-COLLISION`/`E-TEMPLATE-INSTALLED-
    UNSUPPORTED`/`E-TEMPLATE-UNKNOWN`, resolved the same way `freeze`
    resolves them), a corrupt, unreadable, or record `report` cannot use
    (the shipped `E-UPSTREAM-RECORD-*` family, or this function's own
    `E-REPORT-RECORD-INCOMPLETE`), a draft run (`E-REPORT-DRAFT`,
    Decision 7), the bundle form's own faults (`E-STUDY-UNREADABLE`, or the
    same `E-UPSTREAM-RECORD-*`/`E-REPORT-RECORD-INCOMPLETE` a run-form
    render can raise, one per corrupt or incomplete member), or an
    override fault reachable only on the run form (`E-REPORT-OVERRIDE-*`,
    `E-REPORT-FORMAT`, `E-REPORT-BODY`). `0` for every STATUS a record can
    hold once it renders — `completed`, `partial` and `failed` alike,
    because a read command's exit code reports whether it could read,
    never what it read: the record's own `status` and its failed
    executions are rendered by the Attrition section, not folded into
    this function's return value. `diff`'s Decision 4 rules the identical
    thing for the identical reason, and the two now agree in both
    directions. A bundle's two cross-check notices (`W-STUDY-CODE-HASH-
    MISMATCH`, `W-STUDY-APPARATUS-MISMATCH`) never change this function's
    exit code either, on the same warning-never-changes-exit-code
    precedent `W-APPARATUS-UNANSWERED` already sets. `2` is `main`'s own
    invocation-arity refusal, decided before this function is ever
    called — this function itself never returns `2`.

    **`report <study.yaml>` renders the real bundle (task 10).** Every
    member's four standard sections, in `study.yaml`'s own declared order,
    plus one combined Hypotheses table, and Decision 8's two cross-checks
    printed as notices before the render — never `cli._report_not_built`'s
    "command is not built" diagnostic at exit `2`, which would be a false
    claim about a command that is built, and never `E-REPORT-BUNDLE-
    UNSUPPORTED`, the interim-build-family code this task retires
    wholesale rather than narrows (`CLAUDE.md`'s "-UNSUPPORTED suffix" —
    the undocumented build family, absent from the registry once retired).
    **No override discovery happens on this path at all**: `render_bundle`
    calls `BaseReport().sections` directly for every member and never
    `render_with_override`, which stays the run form's own entry point.

    **Decision 7: a draft run (`config.yaml`'s `draft: true`, § Draft
    runs) is refused, not watermarked.** § Draft runs' own verb is
    "refuses" — a report that rendered a draft with a banner would be
    citable, which is the sentence the whole `draft`-versus-`--allow-
    dirty` argument rests on. Checked BEFORE the credential lookup and
    the override import below, on `freeze`'s own "cheap objection first"
    precedent: a draft is refused for reasons that cost nothing to check
    and have nothing to do with what an override might do. **This is a
    single RUN's refusal only** — `report <study.yaml>` FLAGS a draft
    member instead of refusing the whole bundle (§ Building one: "flag
    any draft runs"), because a bundle is a set and one draft member
    should not cost the other legitimate ones their render. That flagging
    arm is task 10's, over code that does not exist yet; this function
    owns only the single-run refusal.

    **User code runs here** (an override's import, and its `sections()`
    body), so every diagnostic THIS function prints for such a fault goes
    through a fresh `Collector` carrying `credentials` — never `main`'s
    own bare `except PublishableError` handler, which has no collector in
    scope at all (`spec-defects.md`'s filing). The set is populated by
    `freeze`'s own shipped recipe:
    `validate.declared_credential_names_for(doc, template)` over the
    record's embedded `config`, with `template` resolved through
    `templates.registry.get_template(name, repo_root)`, then
    `secrets.credential_values(names)`. **This command never calls
    `secrets.load_env`**: it executes nothing metered and needs no
    credential of its own, so the set it can redact is exactly what the
    process environment already held, for a declared name, when this
    process started — a value core never read cannot be redacted by
    name-matching, and this claims no more than that.

    `repo_root` for that resolution is read the same tolerant way
    `_read_repo_root` reads it for override discovery, EXCEPT that a
    missing or malformed `environment/repo_root.txt` here is not a
    refusal: credential resolution is best-effort safety, not a
    prerequisite for rendering a record that carries no override at all.
    Falling back to `None` costs exactly what `command_run`'s own
    identical fallback costs: a project-LOCAL template then resolves to
    `None` (`registry._merged` never runs `discover_local` without a
    repo root), so a local template's declared credential is silently
    excluded from this set. Stated rather than hidden, because a silently
    empty credential set is a redaction no-op — the leak shape this repo
    has shipped five times.

    `KeyboardInterrupt` is re-raised fresh and argument-less, `from None`
    — H7b Part B's resolver path's own precedent — so Ctrl-C still stops
    the command carrying no message a probe or an override could have
    constructed to smuggle a credential through Python's own printer.
    """
    try:
        form = report_form(path)
    except ContractError as exc:
        c = Collector()
        c.error(exc.code, str(path), str(exc))
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    if form == "bundle":
        # Task 10: the real bundle render. `read_bundle` and `render_bundle`
        # both raise only `ContractError` — `E-STUDY-UNREADABLE`, the
        # shipped `E-UPSTREAM-RECORD-*` family for a corrupt member, or
        # `E-REPORT-RECORD-INCOMPLETE` for one missing/malformed downstream
        # of a clean parse — so one `except` covers every bundle-side
        # refusal, exactly as the run form's own phases do below. No
        # `Collector.credentials` is populated here: the bundle form runs
        # no user code (no override discovery, ever, on this path) and
        # needs none to redact (§ Corrections, correction 7).
        bundle_dir = path.parent
        try:
            _bundle_doc, members = read_bundle(path)
            text = render_bundle(bundle_dir, members)
        except ContractError as exc:
            c = Collector()
            c.error(exc.code, str(path), str(exc))
            print(c.render(), file=sys.stderr)
            return EXIT_WRONG

        # Decision 8: two notices, never a refusal — exit stays `0`
        # regardless of what they find. Printed to STDERR, never stdout
        # (whole-branch review, Minor 6): stdout is the artifact for this
        # command — `publishable report study.yaml > report.md` is the
        # ordinary way to use it — so a diagnostic ahead of the render
        # would land inside the file a reader redirects to. `freeze`
        # already splits its own two warnings across stdout/stderr (one
        # of them stderr, "as shipped rather than as decided" — see
        # docs/reference.md § The apparatus core can only observe); this
        # command decides deliberately, and puts both notices on the
        # stream that keeps the redirected artifact clean.
        notices = _bundle_cross_checks(members)
        if notices:
            notice_c = Collector()
            for code, message in notices:
                notice_c.warn(code, str(path), message)
            print(notice_c.render(), file=sys.stderr)

        print(text)
        return EXIT_OK

    run_dir = path.parent
    try:
        record = read_record_file(path)
    except ContractError as exc:
        c = Collector()
        c.error(exc.code, str(path), str(exc))
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    # Decision 7: a refusal, not a watermark — checked before anything
    # else this function does that costs a credential lookup or an
    # import, on `freeze`'s own "cheap objection first" precedent. No
    # credentials are at stake in this message: nothing rendered, and the
    # record's own `draft` flag carries no secret.
    if record.get("draft") is True:
        c = Collector()
        c.error(
            "E-REPORT-DRAFT",
            str(path),
            "this run's record carries `draft: true` — its code state "
            "isn't reachable from any commit, so `report` refuses to "
            "render it as a final result; `publishable run` a committed "
            "tree, or read the record directly if you must",
        )
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    doc = record.get("config")
    doc = doc if isinstance(doc, Mapping) else {}
    name = doc.get("experiment_type", "")
    name = name if isinstance(name, str) else ""
    try:
        repo_root = _read_repo_root(run_dir)
    except ContractError:
        repo_root = None
    # Critical 1 (whole-branch review): `freeze.py`'s own recipe wraps this
    # EXACT call in a `try` and refuses through a redacting `Collector` —
    # copying its three calls without copying its containment left a
    # project-local template that raises on import (`E-TEMPLATE-LOAD`) or
    # collides with another claimant (`E-TEMPLATE-COLLISION`) free to
    # escape into `main`'s bare, un-redacting `except PublishableError`.
    # `command_run` gets away with an unguarded `get_template` only
    # because `validate_config` already made the identical call and
    # returned without error first — `command_report` validates nothing,
    # which is exactly why the shape is live here and nowhere else this
    # was swept. Mirrors `freeze._precheck`'s own `except BaseException`
    # arm verbatim, including its `partial_templates` recovery: a class
    # that raised AFTER `@register_template` still finished constructing
    # in memory, and `required_env` is readable off it even though the
    # module that defined it is refused wholesale.
    try:
        template = get_template(name, repo_root)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        code = exc.code if isinstance(exc, PublishableError) else "E-TEMPLATE-LOAD"
        partial = getattr(exc, "partial_templates", None) or []
        names: list[str] = []
        for cls in partial:
            names.extend(declared_credential_names_for(dict(doc), cls))
        c = Collector()
        c.credentials = credential_values(names)
        c.error(code, str(path), str(exc))
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG
    credentials = credential_values(declared_credential_names_for(dict(doc), template))

    # Major 2 (whole-branch review): a parseable-but-incomplete record
    # (a hand-truncated `run.yaml` missing `execution`, `results` or
    # `config`) gave a raw `KeyError` traceback out of a built command,
    # where `diff` over the identical file renders at exit 0. Refused
    # with a remedy instead, reusing the shipped `E-UPSTREAM-RECORD-*`
    # family Decision 15 already routes "a run record `report` cannot
    # read" through, rather than minting a fifth code for the same fault.
    try:
        io = _report_io_from_record(run_dir, record)
    except (KeyError, TypeError, AttributeError, ValueError, IndexError) as exc:
        # Whole-branch review, Major 5: `KeyError`/`TypeError` alone let
        # `execution: "x"` (a str, not a mapping) reach `.get` inside
        # `derive_step_scopes_and_repeats` and raise a bare `AttributeError`
        # traceback out of this built command — inherited by task 10's
        # bundle-side copy of this exact guard, and fixed at both sites in
        # the same commit that found it.
        c = Collector()
        c.credentials = credentials
        c.error(
            "E-REPORT-RECORD-INCOMPLETE",
            str(path),
            f"this record parses and has a `run_id`, but is missing or "
            f"malformed at {exc!r} — `report` needs `execution`, "
            "`results.conditions` and `config.data.input_dir` to build "
            "the read-only artifact accessor an override receives; the "
            "record was edited or truncated by hand",
        )
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    def _render(report_cls: "type[BaseReport] | None") -> str:
        return render_report(report_cls, record, io)

    try:
        text = render_with_override(run_dir, record, _render)
    except KeyboardInterrupt:
        raise KeyboardInterrupt from None
    except BaseException as exc:
        # `render_with_override` wraps every DISCOVERY fault (a bad
        # `entrypoint`, a raising import, the wrong number of `BaseReport`
        # subclasses, a missing `repo_root.txt`) in a `ContractError` with
        # its own code — but `test_sys_path_is_restored_after_render_raises`
        # pins that a RENDER-time raise (the resolved override's own
        # `sections()` body) propagates UNWRAPPED, on purpose, so that
        # test can assert `sys.path` is still restored around a raw
        # exception. That render-time raise is exactly the user-code fault
        # this function's own docstring commits to redacting, so it is
        # caught HERE instead — one level up, where `credentials` is
        # already in hand — rather than inside `render_with_override`,
        # which stays exactly as that pinned test requires. A `ContractError`
        # (`E-REPORT-FORMAT`, `E-REPORT-BODY`, or one of `render_with_
        # override`'s own OVERRIDE-* codes) keeps its own code; anything
        # else an override's `sections()` raised — a plain `RuntimeError`,
        # say — is `E-REPORT-OVERRIDE-RAISED`, on `freeze`'s own `except
        # BaseException as exc: code = exc.code if isinstance(exc,
        # PublishableError) else "..."` recipe.
        code = exc.code if isinstance(exc, PublishableError) else "E-REPORT-OVERRIDE-RAISED"
        c = Collector()
        c.credentials = credentials
        c.error(code, str(path), str(exc))
        print(c.render(), file=sys.stderr)
        return EXIT_WRONG

    print(text)
    return EXIT_OK

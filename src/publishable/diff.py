"""`diff`: compare two runs, or a run and a config, hash by hash.

docs/reference.md § How the three are computed, § The apparatus core can
only observe; docs/design-principles.md § Same code, different parameters;
README.md § The loop you'll actually live in. See
docs/superpowers/specs/2026-08-20-diff-freeze-design.md Decisions 1-6 and
docs/superpowers/plans/2026-08-20-diff-freeze.md tasks 7-11.

**This module is built in slices.** This task (H8b task 7-8) delivers
`covered_config`'s delta walk and the four rows that do not need H7d's
apparatus — `code_hash`, `input_manifest`, `uv.lock`, `parameters_hash` —
over a RUN-VS-RUN pair, plus form detection and the per-side header. The
`apparatus` row (task 9), a config side's `not comparable` rows and the
command's exit-code ruling (task 10), the upstream block and the CLI arm
(task 11) are later tasks' own diffs. `diff` does **not** dispatch through
`cli.main` until task 11 — every call here is direct, on `command_diff`.
"""

from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import EXIT_OK, EXIT_WRONG, Collector
from publishable.errors import ContractError
from publishable.hashes import covered_config
from publishable.lineage import read_run_record

# Task 9 is the only task permitted to insert `'apparatus'` here, in fourth
# position, before `'parameters_hash'` — Decision 1's row order, pinned by
# `tests/test_diff.py`'s row-order mutation (task 8 step 8). Every other row
# label is `reference.md`/`design-principles.md`/`README.md`'s own text, not
# a name this module invented.
ROW_LABELS = ["code_hash", "input_manifest", "uv.lock", "parameters_hash"]

_ABSENT = object()


def _form(path: Path) -> str:
    """A directory, or a file named `run.yaml`, is a run record. Any other
    file (existing or not) is a config. Decided from the path's SHAPE alone,
    never from whether something at it parses — that is content, and this
    step exists to forbid answering with it (Decision 5, part 2)."""
    if path.is_dir():
        return "run record"
    if path.name == "run.yaml":
        return "run record"
    return "config"


def _record_dir(path: Path) -> Path:
    """`read_run_record` is directory-keyed. A `run.yaml` path is dispatched
    by taking its parent; a directory is passed through."""
    return path.parent if path.name == "run.yaml" else path


def _read_config(path: Path) -> dict[str, Any]:
    """Read and parse a config side. A missing path is an unanticipated
    `OSError` and propagates uncaught — `validate`'s and `freeze`'s own
    shipped precedent for a path problem neither anticipated, which `main`'s
    generic handler turns into `E-IO-FAILED` at exit 1 once `diff` dispatches
    (task 11). A path that reads but does not parse to a mapping is
    `E-DIFF-CONFIG-UNREADABLE` — the one new code this module mints, new
    because `E-CONFIG-PARSE` is a `validate` finding at a config path and
    this is a command refusing one of its own two operands."""
    text = path.read_text()  # OSError propagates uncaught
    try:
        doc = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ContractError(
            f"{path} does not parse: {exc}", code="E-DIFF-CONFIG-UNREADABLE"
        ) from exc
    if not isinstance(doc, dict):
        raise ContractError(f"{path} did not parse to a mapping", code="E-DIFF-CONFIG-UNREADABLE")
    return doc


class _Side:
    """One operand, already loaded. `record` is the parsed `run.yaml` when
    `form == "run record"`; `config` is the parsed config when
    `form == "config"`. Exactly one of the two is set."""

    def __init__(
        self,
        path: Path,
        form: str,
        *,
        record: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.path = path
        self.form = form
        self.record = record
        self.config = config


def _load_side(path: Path) -> _Side:
    form = _form(path)
    if form == "run record":
        return _Side(path, form, record=read_run_record(_record_dir(path)))
    return _Side(path, form, config=_read_config(path))


def _header_line(letter: str, side: _Side) -> str:
    """The per-side header: form, identity, and — for a run record — its
    `status` plus the word `draft` when `draft: true`. A config side prints
    its form and the path AS GIVEN (never resolved), and no status word — a
    config has none, and inventing one would be a claim (§ Corrections,
    correction 9)."""
    if side.form == "run record":
        assert side.record is not None
        parts = [letter, side.form, str(side.record.get("run_id"))]
        status = side.record.get("status")
        if status is not None:
            parts.append(str(status))
        if side.record.get("draft") is True:
            parts.append("draft")
        return "  ".join(parts)
    return "  ".join([letter, side.form, str(side.path)])


def _diff_values(value_a: Any, value_b: Any, path: str) -> list[tuple[str, Any, Any]]:
    """Walk two config values in lockstep, descending into a `dict` present
    on EITHER side (empty or not), and returning every leaf where the two
    sides disagree as `(dotted path, value_a, value_b)`.

    **Replaces an earlier, per-side-independent flatten** (batch 5 review,
    Major 1): flattening each side on its own drops an empty `dict`
    entirely — nothing to loop over — so `covered_config({"sweep": {}})`
    and `covered_config({})` flattened identically while their hashes
    differed. Reachable from `init`'s own output: `materialize_config`
    writes `sweep: {}`, and its own inline comment calls that spelling
    equivalent to omitting the key, so deleting it between two runs printed
    `parameters_hash DIFFERS` with zero delta lines underneath.

    Walking BOTH sides together fixes this without the regression a
    simpler "treat every empty dict as a leaf" patch causes: when one
    side's dict at a path is empty and the OTHER side's is non-empty,
    recursing into the UNION of their keys still finds every real leaf
    underneath the populated side. Only when NEITHER side has a child at
    that path — both empty, or one absent and the other empty — does the
    path become a leaf itself, rendering e.g. `sweep  {} → (absent)`.

    A leaf is anything that is not a `dict` on either side — a `list`
    stays a leaf, never a subtree (Decision 3): splitting it by index
    would print one delta per moved position for a mere reordering."""
    a_dict = isinstance(value_a, dict)
    b_dict = isinstance(value_b, dict)
    if a_dict or b_dict:
        keys_a = value_a if a_dict else {}
        keys_b = value_b if b_dict else {}
        all_keys = set(keys_a) | set(keys_b)
        if not all_keys:
            return [] if value_a == value_b else [(path, value_a, value_b)]
        out: list[tuple[str, Any, Any]] = []
        for key in all_keys:
            child_path = f"{path}.{key}" if path else str(key)
            out.extend(_diff_values(keys_a.get(key, _ABSENT), keys_b.get(key, _ABSENT), child_path))
        return out
    return [] if value_a == value_b else [(path, value_a, value_b)]


def _render_leaf(value: Any) -> str:
    """A leaf's printed form, in the config's own YAML vocabulary — not
    Python's. `bool`/`None` render `true`/`false`/`null` (batch 5 review,
    Major 3): `str(True)` and `str(None)` print `True`/`None`, which a
    reader greps their own `config.yaml` for and does not find, since a
    generated config spells them `true`/`null`. `bool` is checked before
    the generic scalar branch because `isinstance(True, int)` is also
    `True` — not load-bearing here (there is no separate `int` branch) but
    the ordering that would matter if one were added. A `str` scalar keeps
    `str(value)` — no YAML quoting — so this is not a blanket `safe_dump`
    widening."""
    if value is _ABSENT:
        return "(absent)"
    if isinstance(value, (dict, list)):
        return yaml.safe_dump(value, default_flow_style=True, sort_keys=True).strip()
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def parameter_deltas(config_a: dict[str, Any], config_b: dict[str, Any]) -> list[str]:
    """The delta walk over `covered_config`'s return on both sides
    (Decision 3) — never a second, independently-built list, which is how
    the verdict above these lines and the lines themselves cannot disagree
    about coverage. Sorted by path, so two runs of `diff` over the same
    pair print identically.

    The value column aligns to the LONGEST changed path in this batch
    (batch 5 review, Minor 1) — `design-principles.md`'s own two-line
    example (`parameters.analysis.method` beside the longer
    `parameters.analysis.min_samples`) shows both values starting in the
    same column, which a fixed two-space separator does not reproduce. For
    a single-line batch this is exactly a two-space gap, so it changes
    nothing about a one-delta comparison — only a multi-line batch's
    columns move."""
    changed = _diff_values(covered_config(config_a), covered_config(config_b), "")
    if not changed:
        return []
    changed.sort(key=lambda item: item[0])
    width = max(len(path) for path, _, _ in changed) + 2
    return [
        f"  {path:<{width}}{_render_leaf(value_a)} → {_render_leaf(value_b)}"
        for path, value_a, value_b in changed
    ]


def _truncated(figure: str) -> str:
    """`sha256:` plus four hex characters plus `…` — the width all three
    worked outputs show."""
    prefix, _, digest = figure.partition(":")
    return f"{prefix}:{digest[:4]}…"


def _figure(row: str, doc: dict[str, Any]) -> Any:
    if row == "code_hash":
        return doc.get("code_hash")
    if row == "input_manifest":
        return (doc.get("provenance") or {}).get("input_manifest_hash")
    if row == "uv.lock":
        return ((doc.get("provenance") or {}).get("environment") or {}).get("uv_lock_hash")
    if row == "parameters_hash":
        return doc.get("parameters_hash")
    raise ValueError(row)  # pragma: no cover — ROW_LABELS is the only caller


_LABEL_WIDTH = 19  # measured against all three worked outputs' fenced `diff` examples
_VERDICT_WIDTH = 13  # "identical" (9) padded to the same examples' digest column


def _render_row(row: str, record_a: dict[str, Any], record_b: dict[str, Any]) -> list[str]:
    """One row's lines: the label, its verdict, and any detail lines.

    `not captured` fires when the figure is `null` on **either** side — the
    guard the H8a-scoping's own measurement demands: every scaffolded run
    records `uv_lock_hash: None`, so two such runs would otherwise print
    `uv.lock  identical  sha256:None…`, a match over a fact neither run
    holds. `parameters_hash`'s `DIFFERS` detail is task 7's parameter
    deltas; the other rows' `DIFFERS` detail is the two digests, because a
    bare `DIFFERS` gives a reader nothing to cite.

    The label and (for `identical`) the verdict are padded to
    `_LABEL_WIDTH`/`_VERDICT_WIDTH` — the widths all three worked outputs
    show (batch 5 review, Minor 1) — so a line copied out of a document
    matches a line this function prints.
    """
    figure_a = _figure(row, record_a)
    figure_b = _figure(row, record_b)
    if figure_a is None or figure_b is None:
        return [f"{row:<{_LABEL_WIDTH}}not captured"]
    if figure_a == figure_b:
        verdict = f"{'identical':<{_VERDICT_WIDTH}}{_truncated(figure_a)}"
        return [f"{row:<{_LABEL_WIDTH}}{verdict}"]
    if row == "parameters_hash":
        deltas = parameter_deltas(record_a["config"], record_b["config"])
        return [f"{row:<{_LABEL_WIDTH}}DIFFERS", *deltas]
    return [
        f"{row:<{_LABEL_WIDTH}}DIFFERS",
        f"  {_truncated(figure_a)} → {_truncated(figure_b)}",
    ]


def command_diff(a: Path, b: Path) -> int:
    """`diff a b`, end to end for the surface this task builds: form
    detection, the per-side header, and the four rows that need no
    apparatus, over a run-record pair. A config side's rows and the
    apparatus row are later tasks' (9, 10); this function's job is not to
    guess ahead of them.
    """
    # Both sides are loaded before either failure is reported (batch 5
    # review, Minor 4): loading them in two unconditional `try` blocks,
    # rather than returning on the first `ContractError`, is what lets a
    # caller with two bad paths learn about both in one run instead of
    # fixing one and re-running to discover the second. An `OSError` (a
    # missing path) is NOT caught here — it propagates uncaught either
    # way, on `validate`'s/`freeze`'s own precedent.
    c = Collector()
    side_a: _Side | None = None
    side_b: _Side | None = None
    try:
        side_a = _load_side(a)
    except ContractError as exc:
        c.error(exc.code, str(a), str(exc))
    try:
        side_b = _load_side(b)
    except ContractError as exc:
        c.error(exc.code, str(b), str(exc))
    if c.findings:
        print(c.render())
        return EXIT_WRONG
    assert side_a is not None and side_b is not None

    print(_header_line("A", side_a))
    print(_header_line("B", side_b))

    if side_a.form == "run record" and side_b.form == "run record":
        assert side_a.record is not None and side_b.record is not None
        for row in ROW_LABELS:
            for line in _render_row(row, side_a.record, side_b.record):
                print(line)

    return EXIT_OK

"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import re
from pathlib import Path
from typing import Any

import yaml

from publishable.base_experiment import load_experiment
from publishable.contrasts import resolve_contrasts, units_matching
from publishable.diagnostics import Collector
from publishable.envelope import check_envelope
from publishable.errors import ContractError
from publishable.manifest import POLICIES
from publishable.materialize import TEMPLATE_VERSION
from publishable.param import MISSING
from publishable.provenance import find_repo_root, resolves_inside_repo
from publishable.replication import resolve_repeats
from publishable.scope import step_name as _step_name
from publishable.strata import levels_for
from publishable.sweep import (
    SWEEP_MODES,
    _swept_paths,
    axis_modes_present,
    check_swept_value,
    expand,
    removal_value,
    render_value,
    sample_fault,
)
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template, template_names
from publishable.units import UnitList, resolve_units

REQUIRED_METADATA = ("description", "authors")

# The shape of every top-level block, checked once before any `_check_*` reads one —
# a property of the config format, not of whichever check happens to read a block
# first. `statistics`, `limits`, and `hypotheses` are included even though nothing
# reads them yet in this build, so the next reader inherits the guard rather than
# the crash a hand-edited config would otherwise produce.
_MAPPING_BLOCKS = (
    "metadata",
    "data",
    "parameters",
    "sweep",
    "replication",
    "statistics",
    "limits",
)
_LIST_BLOCKS = ("hypotheses",)
_STRING_BLOCKS = ("schema_version", "experiment_type", "template_version", "entrypoint", "plugin")

_KIND_LABEL = {
    "mapping": "a mapping",
    "list": "a list",
    "string": "a string",
    "integer": "an integer",
    "number": "a number",
    "string_or_integer": "a string or an integer",
}


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in (node or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, path))
        else:
            flat[path] = value
    return flat


def _check_shape(doc: dict[str, Any], c: Collector) -> bool:
    """Every top-level block's type, checked once before any later `_check_*` indexes
    into one. Returns whether the doc is shaped well enough to keep validating —
    `validate_config` returns early when it is not, the same pattern it already uses
    for an unparseable config and an unknown template: every later check indexes into
    these blocks, so continuing would cascade into confusing secondary errors about a
    config whose shape is already known wrong.

    An absent key is not a shape error — optional blocks stay optional, and required
    ones are already reported by their own check. A key present but `null` is treated
    the same as absent, matching the rest of this module (`doc.get("x") or {}`): a
    hand-edited `sweep: null` is not a declaration, and shouldn't become a new kind of
    error just because this check now runs first.
    """
    ok = True

    def _bad(key: str, value: Any, kind: str) -> None:
        nonlocal ok
        c.error(
            "E-CONFIG-SHAPE",
            key,
            f"is a {type(value).__name__} (`{value!r}`); expected {_KIND_LABEL[kind]}",
        )
        ok = False

    for block, kind, isa in (
        *((k, "mapping", dict) for k in _MAPPING_BLOCKS),
        *((k, "list", list) for k in _LIST_BLOCKS),
        *((k, "string", str) for k in _STRING_BLOCKS),
    ):
        value = doc.get(block)
        if value is not None and not isinstance(value, isa):
            _bad(block, value, kind)

    # Nested shapes a later check indexes into directly, folded into the same
    # `E-CONFIG-SHAPE` identifier rather than a second code for one condition. Each
    # container is checked before its items — a container of the wrong shape (a
    # mapping in place of a list, most plausibly a forgotten `-` on `repeats`) must
    # be caught here too, or the per-item loop below is simply skipped and the crash
    # just moves one level down, into whichever `_check_*` reads it next.
    data = doc.get("data")
    if isinstance(data, dict):
        units = data.get("units")
        if units is not None and not isinstance(units, dict):
            _bad("data.units", units, "mapping")
        elif isinstance(units, dict):
            attributes = units.get("attributes")
            if attributes is not None and not isinstance(attributes, list):
                _bad("data.units.attributes", attributes, "list")

    # `sweep`'s two implemented sub-blocks, and each grid axis's value list.
    # `_check_sweep` calls `grid.items()` and `sweep.expand` calls `dict(baseline)`
    # on whatever is here, so a list or a string in either place escaped `main`'s
    # `PublishableError`/`OSError` handler as a bare traceback. The per-axis `list`
    # check closes the quieter version of the same gap: a bare string axis
    # (`analysis.method: spearman`, brackets forgotten) is iterable, so it expanded
    # character by character into one condition per letter.
    sweep = doc.get("sweep")
    if isinstance(sweep, dict):
        baseline = sweep.get("baseline")
        if baseline is not None and not isinstance(baseline, dict):
            _bad("sweep.baseline", baseline, "mapping")
        grid = sweep.get("grid")
        if grid is not None and not isinstance(grid, dict):
            _bad("sweep.grid", grid, "mapping")
        elif isinstance(grid, dict):
            for path, values in grid.items():
                # Same crash as `paired`'s non-string-key guard below, reached
                # through `grid` instead: YAML permits a non-string mapping key
                # (`123: [...]` parses fine), but `_keys_for` feeds every swept
                # path into `.split(".")`, so a non-string `grid` key crashes
                # `AttributeError: 'int' object has no attribute 'split'` before
                # this guard existed. Pre-existing and outside the review's
                # original finding for `paired` — closed here rather than left
                # as the one axis-shaped mode without the guard its sibling has.
                if not isinstance(path, str):
                    _bad("sweep.grid", path, "string")
                    continue
                if values is not None and not isinstance(values, list):
                    _bad(f"sweep.grid.{path}", values, "list")

        # `paired` closes the same gap `grid` does, one level down: `_axes` now
        # reads it unconditionally (`dict(entry) for entry in paired`), so a
        # non-list `paired` or a non-mapping entry escaped as a bare `TypeError`/
        # `ValueError` from `expand`, past `_check_sweep`'s premise that it is the
        # check that reports an expansion crash. Two guards, same shape as
        # `grid`'s: the container, then each entry. Unlike a `grid` axis value —
        # which is used as-is and stays legal as `null` (a param-value question,
        # not a shape one) — every `paired` entry is fed straight into `dict()`,
        # so a `null` entry is itself the crash (`dict(None)` raises `TypeError`)
        # and is refused here rather than treated as absent.
        #
        # A third guard, same reasoning: `dict()` itself tolerates a non-string
        # key (`{123: 30}` parses fine off YAML), but `_swept_paths`/`_keys_for`
        # feed every `paired` key straight into `.split(".")` and an `endswith`
        # scan, both string-only, so `123.split(".")` is the crash — one level
        # further down than the entry-shape guard above, reached only once an
        # entry *is* a mapping. `envelope.py`'s `_check_unknown_keys` faces a
        # structurally similar non-string YAML key and chooses the other
        # route — coerce to `str` and report `E-CONFIG-KEY-UNKNOWN` — but that
        # works there because every leaf sits under a closed, known vocabulary
        # a coerced string can be compared against and reported as unmatched.
        # A `paired` key is an open dotted path into `parameters`, not a member
        # of any closed set `_check_shape` knows here (that resolution is
        # `_check_sweep`'s `E-SWEEP-PATH-UNKNOWN`, reached only for a *string*
        # key); coercing and continuing would just move today's crash one
        # frame deeper for no reporting benefit, so this stays a shape fault —
        # `E-CONFIG-SHAPE`, fatal, consistent with every other guard in this
        # function — rather than `envelope.py`'s coerce-and-report.
        paired = sweep.get("paired")
        if paired is not None and not isinstance(paired, list):
            _bad("sweep.paired", paired, "list")
        elif isinstance(paired, list):
            for i, entry in enumerate(paired):
                if not isinstance(entry, dict):
                    _bad(f"sweep.paired[{i}]", entry, "mapping")
                    continue
                for key in entry:
                    if not isinstance(key, str):
                        _bad(f"sweep.paired[{i}]", key, "string")

        # `ablate` gets the same walk `paired` gets, at every depth
        # `sweep.ablation_changes` reads — enumerated from the operations that
        # function performs, not from inputs someone imagined:
        #   `ablate.items()`                → the block must be a mapping
        #   `for path in remove`            → a list (a bare string iterates
        #                                     character by character into one
        #                                     condition per letter, the quiet
        #                                     failure `grid`'s axis guard closed)
        #   `{path: ...}` then `.split(".")` in `_keys_for` → a string path
        #                                     (a list entry is unhashable and
        #                                     raises at the dict literal; an int
        #                                     is hashable and raises later, in
        #                                     `_keys_for`)
        #   `for entry in override`         → a list, same reasoning
        #   `dict(entry)`                   → a mapping, exactly `paired`'s guard
        #   each override key               → a string, for `_keys_for` again
        # `from` is deliberately absent: `expand` reads `sweep.baseline`
        # directly and performs no operation on `from` at all, so there is no
        # type that makes it raise, and guarding it here would be guessing at
        # inputs rather than closing a crash. A `from` naming anything but
        # `baseline` is a value fault nothing yet reports — recorded in
        # `docs/superpowers/spec-defects.md`. `dict(baseline)` is now read by
        # ablate rows too; its guard is `sweep.baseline`'s above, unchanged.
        ablate = sweep.get("ablate")
        if ablate is not None and not isinstance(ablate, dict):
            _bad("sweep.ablate", ablate, "mapping")
        elif isinstance(ablate, dict):
            remove = ablate.get("remove")
            if remove is not None and not isinstance(remove, list):
                _bad("sweep.ablate.remove", remove, "list")
            elif isinstance(remove, list):
                for i, path in enumerate(remove):
                    if not isinstance(path, str):
                        _bad(f"sweep.ablate.remove[{i}]", path, "string")
            override = ablate.get("override")
            if override is not None and not isinstance(override, list):
                _bad("sweep.ablate.override", override, "list")
            elif isinstance(override, list):
                for i, entry in enumerate(override):
                    if not isinstance(entry, dict):
                        _bad(f"sweep.ablate.override[{i}]", entry, "mapping")
                        continue
                    for key in entry:
                        if not isinstance(key, str):
                            _bad(f"sweep.ablate.override[{i}]", key, "string")

        # `sample` gets the same treatment at every depth `_sample_cells` reads,
        # rather than one guard per input someone thought of: the container, then
        # `n`/`method`/`seed`, then the `ranges` mapping, then each range's path,
        # its single form key, and the two-element bound list the scaling
        # indexes into. Each of these is an operation on user data — a
        # comparison, a `dict` key, a `.split(".")`, a subscript — and each has a
        # YAML-expressible type that makes it raise, which is why the walk is
        # exhaustive over the *shapes* rather than over the examples. `bool` is
        # excluded from `n` deliberately (`n: true` is an `int` to Python and
        # nothing to a reader), and from a bound for the same reason.
        # `sweep.sample_fault` refuses this same family from the other end, so a
        # config reaching `expand` without passing here still gets a coded
        # error; the value-level residue it also names (a `method` outside the
        # enum, `n < 1`, an unknown form, inverted bounds) is `_check_sweep`'s
        # `E-SWEEP-SAMPLE-INVALID`, because those are legal shapes carrying
        # illegal values — the same division `grid` draws between its `list`
        # guard here and `E-SWEEP-AXIS-EMPTY` there.
        sample = sweep.get("sample")
        if sample is not None and not isinstance(sample, dict):
            _bad("sweep.sample", sample, "mapping")
        elif isinstance(sample, dict):
            n = sample.get("n")
            if n is not None and (isinstance(n, bool) or not isinstance(n, int)):
                _bad("sweep.sample.n", n, "integer")
            method = sample.get("method")
            if method is not None and not isinstance(method, str):
                _bad("sweep.sample.method", method, "string")
            seed = sample.get("seed")
            if seed is not None and not isinstance(seed, str | int):
                # Both types, because both are legal: `auto` and a pinned
                # integer (§ What `auto` derives from). Reporting "expected a
                # string" would send a user who wrote `seed: [1]` toward
                # quoting a number.
                _bad("sweep.sample.seed", seed, "string_or_integer")
            ranges = sample.get("ranges")
            if ranges is not None and not isinstance(ranges, dict):
                _bad("sweep.sample.ranges", ranges, "mapping")
            elif isinstance(ranges, dict):
                for path, spec in ranges.items():
                    if not isinstance(path, str):
                        _bad("sweep.sample.ranges", path, "string")
                        continue
                    if not isinstance(spec, dict):
                        _bad(f"sweep.sample.ranges.{path}", spec, "mapping")
                        continue
                    for form, bounds in spec.items():
                        if not isinstance(form, str):
                            _bad(f"sweep.sample.ranges.{path}", form, "string")
                            continue
                        where = f"sweep.sample.ranges.{path}.{form}"
                        if not isinstance(bounds, list):
                            _bad(where, bounds, "list")
                            continue
                        for bound in bounds:
                            if isinstance(bound, bool) or not isinstance(bound, int | float):
                                _bad(where, bound, "number")

    replication = doc.get("replication")
    if isinstance(replication, dict):
        repeats = replication.get("repeats")
        if repeats is not None and not isinstance(repeats, list):
            _bad("replication.repeats", repeats, "list")
        elif isinstance(repeats, list):
            for i, level in enumerate(repeats):
                if not isinstance(level, dict):
                    _bad(f"replication.repeats[{i}]", level, "mapping")

    # `statistics.contrasts` is read by two `_check_*` functions and by
    # `contrasts.resolve_contrasts`, so it belongs here rather than being guarded
    # three times. Verified against the pre-this-change code directly (not
    # assumed): a scalar here does not currently crash `validate` — `_check_sweep`
    # already contains `resolve_contrasts`'s `TypeError` in a `try/except`, and
    # `_check_contrasts` already has its own `isinstance(entries, list)` guard, so
    # the two together already report `E-STATS-CONTRAST-SHAPE` cleanly. What this
    # block buys instead is what every other entry in this pass buys: one refusal,
    # here, under the shared `E-CONFIG-SHAPE` identifier, so a future third reader
    # of this block inherits the guard rather than needing its own.
    statistics = doc.get("statistics")
    if isinstance(statistics, dict):
        contrasts = statistics.get("contrasts")
        if contrasts is not None and not isinstance(contrasts, list):
            _bad("statistics.contrasts", contrasts, "list")

        report_by = statistics.get("report_by")
        if report_by is not None and not isinstance(report_by, list):
            _bad("statistics.report_by", report_by, "list")

    # The leaf layer, in the same walk as the container layer above: shape and
    # type are one question asked at two depths, and two walks over one document
    # is how the two rules drift apart. Leaf faults are deliberately NOT fatal —
    # `ok` is untouched here. A wrong-typed `metadata.name` must not suppress a
    # `data.input_dir` finding, while a wrong-typed *container* must, because
    # every later check indexes into it.
    for code, field, message in check_envelope(doc):
        c.error(code, field, message)

    return ok


def load_document(config_path: Path, c: Collector | None = None) -> dict[str, Any] | None:
    """Parse the config and confirm it is a mapping — the two things every later check
    presumes. `c` is optional so a caller that only wants the entrypoint out of the file
    (`command_run`, so it can import once rather than twice) can parse without reporting:
    `validate_config` re-parses and reports, and one fault must produce one finding.
    """
    try:
        doc = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        if c is not None:
            c.error("E-CONFIG-PARSE", str(config_path), f"does not parse: {exc}")
        return None
    if not isinstance(doc, dict):
        if c is not None:
            c.error("E-CONFIG-PARSE", str(config_path), "does not parse as a mapping")
        return None
    return doc


def validate_config(
    config_path: Path, c: Collector, *, experiment: Any | None = None
) -> dict[str, Any] | None:
    """Validate one config. `experiment` is the already-imported entrypoint, when the
    caller has one — `command_run` passes what it loaded so a run imports user code once.
    When it is absent and the config names an entrypoint, `validate` imports it itself:
    `W-REPL-DETERMINISTIC` reads `nondeterministic` off the step classes, and warning at
    run time instead would spend exactly the compute the warning is about.
    """
    doc = load_document(config_path, c)
    if doc is None:
        return None

    if not _check_shape(doc, c):
        return None  # every later check indexes into a block already known malformed

    name = doc.get("experiment_type", "")
    template = get_template(name)
    if template is None:
        c.error(
            "E-TEMPLATE-UNKNOWN",
            "experiment_type",
            f"names `{name}`, which no installed template registers "
            f"(known: {', '.join(template_names())})",
        )
        return None  # every later check reads the spec

    entrypoint = doc.get("entrypoint")
    if experiment is None and isinstance(entrypoint, str) and entrypoint:
        try:
            repo_root: Path | None = find_repo_root(config_path)
        except ContractError:
            # No repo at all. That is `_check_data`'s finding to make (or not), and
            # there is no `src/` to import from, so the entrypoint check is skipped
            # rather than reported as an import failure it did not cause.
            repo_root = None
        try:
            if repo_root is not None:
                experiment = load_experiment(repo_root, entrypoint)
        except SystemExit as exc:
            # `SystemExit` is a `BaseException`, so the broad `except Exception` below
            # does not see it. A user package calling `sys.exit()` at module scope —
            # or building an `argparse` parser at import — would otherwise end the
            # process with the user's own exit code and no diagnostic at all, which
            # is the one outcome `validate` is contracted never to produce.
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                f"could not be imported: SystemExit: {exc.code}",
            )
        except Exception as exc:
            # Deliberately broad. Importing user code can fail every way user code
            # can fail — a syntax error, a missing dependency, a module-scope raise —
            # and `validate` reports rather than raises, so each of those is one
            # finding. Letting any of them propagate would turn a diagnosable config
            # into a traceback, which is the whole reason this import moved earlier.
            #
            # `load_experiment`'s own refusals already say which fault they are, so
            # their wording passes through: a value that is not `<module>:<attribute>`
            # was never imported at all, and framing it as an import failure sends the
            # reader hunting for a missing module rather than a malformed config line.
            own = isinstance(exc, ContractError) and exc.code == "E-ENTRYPOINT-IMPORT"
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                str(exc) if own else f"could not be imported: {type(exc).__name__}: {exc}",
            )

    _check_metadata(doc, config_path, template, c)
    _check_entrypoint(doc, c)
    _check_parameters(doc, template, c)
    _check_versions(doc, template, c)
    _check_data(doc, config_path, c)
    roster = _check_units(doc, c)
    _check_replication(
        doc,
        template,
        c,
        experiment=experiment,
        unit_count=len(roster) if roster is not None else None,
    )
    _check_unimplemented(doc, c)
    _check_sweep(doc, template, c, unit_count=len(roster) if roster is not None else None)
    _check_contrasts(doc, c, roster)
    _check_hypotheses(doc, c, experiment, template)
    _check_report_by(doc, c, roster)
    for message in template.validate(doc):
        c.error("E-TEMPLATE-RULE", "parameters", message)
    return doc


def _check_metadata(doc: dict[str, Any], config_path: Path, template: Any, c: Collector) -> None:
    metadata = doc.get("metadata") or {}
    for field in REQUIRED_METADATA:
        if not metadata.get(field):
            c.error("E-META-REQUIRED", f"metadata.{field}", "is empty, and is required")
    name = metadata.get("name", "")
    # `check_envelope` is what REPORTS a wrong-typed `name` (E-CONFIG-TYPE) — this
    # guard exists because this function may be reached without it having run: a
    # leaf fault is deliberately non-fatal to the pass, so `_check_metadata` still
    # executes on the still-malformed `doc`, and `re.match` requires a str/bytes-
    # like second argument. Without this, a list or int name raised `TypeError`
    # out of `validate` for the exact leaf fault this pass exists to turn into a
    # diagnostic instead.
    if name and isinstance(name, str) and not re.match(template.naming_pattern, name):
        c.error(
            "E-NAME-PATTERN",
            "metadata.name",
            f"is `{name}`, which does not match the template's naming_pattern "
            f"{template.naming_pattern}",
        )
    directory = config_path.parent.name
    if name and directory and name != directory:
        c.error(
            "E-NAME-DIR",
            "metadata.name",
            f"is `{name}` under `configs/{directory}/`; the two name one experiment",
        )


def _check_entrypoint(doc: dict[str, Any], c: Collector) -> None:
    entrypoint = doc.get("entrypoint")
    if not entrypoint or not isinstance(entrypoint, str):
        c.error(
            "E-ENTRYPOINT-REQUIRED",
            "entrypoint",
            "is empty, and is required — `run` cannot import a step without it",
        )


def _check_parameters(doc: dict[str, Any], template: Any, c: Collector) -> None:
    declared = _flatten(doc.get("parameters"), "")
    spec = template.parameter_spec
    for path, value in declared.items():
        param = spec.get(path)
        if param is None:
            import difflib

            near = difflib.get_close_matches(path, list(spec), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-PARAM-UNKNOWN",
                f"parameters.{path}",
                f"is not a parameter of this template{hint}",
            )
            continue
        problem = param.check(value)
        if problem:
            c.error("E-PARAM-VALUE", f"parameters.{path}", problem)
    for path, param in spec.items():
        if path not in declared and param.default is MISSING:
            c.error("E-PARAM-MISSING", f"parameters.{path}", "is required and absent")


def _check_versions(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The moved version, and which parameters this config leaves to a default.

    § Validation's "Template version moved" row reports both halves in one
    warning — the version, and `request.timeout` being unset. The second half is
    computed from `parameter_spec` alone and named only inside this warning, so
    it stays gated on the mismatch: a config whose `template_version` matches
    draws nothing here, and an omitted parameter with no default is
    `E-PARAM-MISSING`'s to report regardless of any version.

    The message states what is observable — a parameter the installed template
    defaults and this config does not set. Core cannot tell that apart from one
    the author deliberately left at its default, and asserting which it is would
    be a claim the declaration does not carry.
    """
    declared = doc.get("template_version")
    if not declared or declared == TEMPLATE_VERSION:
        return
    set_here = _flatten(doc.get("parameters"), "")
    unset = [
        path
        for path, param in template.parameter_spec.items()
        if path not in set_here and param.default is not MISSING
    ]
    detail = (
        f"; unset here and left to the installed template's default: {', '.join(unset)}"
        if unset
        else ""
    )
    c.warn(
        "W-TEMPLATE-VERSION",
        "template_version",
        f"is {declared} but the installed template reports {TEMPLATE_VERSION}{detail}",
    )


def _check_data(doc: dict[str, Any], config_path: Path, c: Collector) -> None:
    data = doc.get("data") or {}

    # Checked first and unconditionally: `input_manifest_policy` has nothing to do
    # with the repo, so it must not be gated behind the repo-existence check below —
    # a repo-less config still has to be one `manifest.build_manifest` can execute.
    policy = data.get("input_manifest_policy")
    if not policy:
        c.error(
            "E-DATA-POLICY",
            "data.input_manifest_policy",
            "is empty, and is required",
        )
    elif policy not in POLICIES:
        c.error(
            "E-DATA-POLICY",
            "data.input_manifest_policy",
            f"is `{policy}`, which is not one of {', '.join(POLICIES)}",
        )

    # `E-DATA-REQUIRED` and `E-DATA-UNREADABLE` have nothing to do with the repo
    # either — same reasoning as the policy check above — so they must not sit
    # behind the repo-existence early return below. Only `E-DATA-IN-REPO`
    # legitimately needs a repo root to compare against.
    resolvable: dict[str, Path] = {}
    for field in ("input_dir", "output_dir"):
        raw = data.get(field)
        if not raw:
            c.error("E-DATA-REQUIRED", f"data.{field}", "is empty, and is required")
            continue
        if not isinstance(raw, str):
            # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
            # exists because this function may be reached without it having run:
            # a leaf fault is deliberately non-fatal, so `_check_data` still runs
            # on a still-malformed `doc`, and `Path()` requires a str/PathLike.
            continue
        path = Path(raw).expanduser()
        if not path.is_absolute():
            c.error(
                "E-DATA-NOT-ABSOLUTE",
                f"data.{field}",
                f"is `{raw}`, which is not an absolute path — reference.md requires "
                "input_dir/output_dir to be absolute so the config means the same "
                "location regardless of the directory a command is run from",
            )
            continue
        resolvable[field] = path.resolve()

    input_dir = data.get("input_dir")
    # Same reasoning as the `isinstance` guard above: `check_envelope` reports a
    # wrong-typed `input_dir`, but this function may be reached without it having
    # run, and `Path()` requires a str/PathLike.
    if input_dir and isinstance(input_dir, str):
        path = Path(input_dir).expanduser()
        if not path.is_dir() or not any(path.iterdir()):
            c.error("E-DATA-UNREADABLE", "data.input_dir", f"{path} is unreadable or empty")

    try:
        repo_root = find_repo_root(config_path).resolve()
    except ContractError as exc:
        if exc.code == "E-GIT-NO-REPO":
            return  # not in a repo, so "inside the repo" doesn't arise
        raise
    for field, resolved in resolvable.items():
        if resolves_inside_repo(resolved, repo_root):
            c.error(
                "E-DATA-IN-REPO",
                f"data.{field}",
                f"resolves inside the git repository at {repo_root}",
            )


def _units_declaration(data: dict[str, Any], c: Collector) -> dict[str, Any] | None:
    """`data.units`, or `None` if there is no declaration or its shape is wrong.

    In the normal pipeline this shape is already guaranteed by `_check_shape`, which
    runs first in `validate_config` and stops the whole check before `_check_units` /
    `_check_unimplemented` are ever called. This guard exists for the two of them
    being exercised directly (as several `_check_*` functions already are in tests),
    so neither crashes on a non-mapping `data.units` reached on its own. Reported —
    under the same `E-CONFIG-SHAPE` identifier `_check_shape` uses, so a bad shape is
    never two different codes — only if that exact diagnostic is not already in
    `c.findings`, which is what keeps a direct call from double-reporting one
    `_check_shape` already caught.
    """
    units_decl = data.get("units")
    if not units_decl:
        return None
    if not isinstance(units_decl, dict):
        already_reported = any(
            f.code == "E-CONFIG-SHAPE" and f.path == "data.units" for f in c.findings
        )
        if not already_reported:
            c.error(
                "E-CONFIG-SHAPE",
                "data.units",
                f"is a {type(units_decl).__name__} (`{units_decl!r}`); expected a mapping "
                "with a `from` key, e.g. `{from: index.csv, key: patient_id}`",
            )
        return None
    return units_decl


def _check_units(doc: dict[str, Any], c: Collector) -> UnitList | None:
    """Resolve the roster so unit checks are real rather than deferred to run time.

    A `ContractError` from resolution becomes a diagnostic carrying the SAME
    identifier, so a user sees one code for one problem whether it surfaced here
    or during a run.

    Two things skip resolution outright rather than piling a second error onto a
    config `_check_data`/`_check_unimplemented` has already flagged:

    - `input_dir` missing, not absolute, or unreadable — `_check_data` already
      reported the real problem, and resolving would only add a confusing
      "file not found" on top of a directory that does not exist.
    - `data.units.from.resolver` — resolvers are plugin artifacts and already
      refused as `E-DATA-RESOLVER-UNSUPPORTED`; `resolve_units` cannot execute a
      resolver either, and without this skip it raises `E-UNITS-SOURCE-MISSING`
      for the same declaration, describing a resolver as a missing file.

    No other `-UNSUPPORTED` field is skipped on: `allocation`, `assign`,
    `cluster_by`, `weight_by`, `measurements`, and `holdout` are not read by
    `resolve_units` at all, so resolving against a real table or glob alongside
    one of those refusals adds a genuine, independent finding — a duplicate key
    in the roster is a real defect whether or not `holdout` is also declared —
    rather than noise about the same problem twice.

    Returns the resolved roster, or `None` when resolution did not happen or did
    not succeed — `_check_replication` uses its length to check a `fold` count
    against real units rather than resolving the roster a second time.
    """
    data = doc.get("data") or {}
    units_decl = _units_declaration(data, c)
    if units_decl is None:
        return None
    input_dir = data.get("input_dir")
    if not input_dir:
        return None  # E-DATA-REQUIRED already reported by _check_data
    if not isinstance(input_dir, str):
        # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
        # exists because this function may be reached without it having run: a
        # leaf fault is deliberately non-fatal, so `_check_units` still runs on
        # a still-malformed `doc`, and `Path()` requires a str/PathLike. This is
        # a second, independent `Path(input_dir)` call from the one `_check_data`
        # already guards — the two read the same leaf for two different purposes
        # (whether the directory is usable at all vs. whether a roster resolves
        # against it), so each needs its own guard.
        return None
    path = Path(input_dir).expanduser()
    if not path.is_absolute() or not path.is_dir() or not any(path.iterdir()):
        return None  # E-DATA-NOT-ABSOLUTE / E-DATA-UNREADABLE already reported by _check_data
    source = units_decl.get("from")
    if isinstance(source, dict) and "resolver" in source:
        return None  # E-DATA-RESOLVER-UNSUPPORTED already reported by _check_unimplemented
    key = units_decl.get("key")
    if key is not None and not isinstance(key, str):
        # `check_envelope` is what REPORTS this (E-CONFIG-TYPE) — this guard
        # exists because this function may be reached without it having run.
        # `_from_table` hashes `key` against a `set` of column names
        # (`key_col not in columns`), which raises `TypeError: unhashable type`
        # for a list or dict rather than the `ContractError` the `except` below
        # is built to catch — a plain wrong-but-hashable type (an int, a bool)
        # does not crash there, but skipping uniformly on any wrong type keeps
        # this guard matching what `check_envelope` already typed the leaf as,
        # rather than only covering the unhashable subset that happens to crash
        # today.
        return None
    # `LEAF_TYPES` types `data.units.attributes` itself a `list` — and it is one
    # here, so `check_envelope` reports nothing — but names no dotted path for a
    # list ELEMENT (the same reason `sweep.grid`'s axis values aren't in the
    # table either). So a non-string item is this function's own finding to
    # make, not a fault `check_envelope` already caught: unlike the `input_dir`
    # and `key` guards above, skipping here silently would be a real gap, not a
    # duplicate. `_from_table` (`units.py`) checks each name against
    # `RESERVED_FIELDS` (a tuple — tolerates an unhashable name) and then against
    # `columns` (a `set` — raises `TypeError: unhashable type` for a list or
    # dict). Reported under `E-UNITS-ATTR-MISSING`, the identifier `_from_table`
    # itself already raises for a *string* name the table doesn't have — a
    # non-string name can never equal a CSV column name either, so "the table
    # does not have it" is exactly as true, and this is one identifier for one
    # user-facing question ("is this a real column?") rather than a second code
    # for the type-shaped version of the same fault.
    attrs = units_decl.get("attributes")
    if isinstance(source, str) and isinstance(attrs, list):
        bad_attrs = [a for a in attrs if not isinstance(a, str)]
        if bad_attrs:
            for bad in bad_attrs:
                c.error(
                    "E-UNITS-ATTR-MISSING",
                    "data.units.attributes",
                    f"names {bad!r}, which {source} does not have",
                )
            return None
    try:
        return resolve_units(units_decl, path)
    except ContractError as exc:
        c.error(exc.code, "data.units", str(exc))
        return None


# Refusals that are properties of the DECLARATION, so `validate` reports them as
# findings. Anything else `resolve_repeats` raises is a genuine fault and still
# propagates — swallowing all of them is how a real error becomes a silent pass.
# This set is deliberately narrow: a future code `resolve_repeats` raises that is
# not added here propagates rather than being silently absorbed into a finding.
# `test_an_unresolved_repl_code_is_not_swallowed` pins that escape path.
REPL_DECLARATION_CODES = frozenset(
    {
        "E-REPL-FOLD-STRATIFY-UNSUPPORTED",
        "E-REPL-FOLD-K",
        "E-REPL-FOLD-K-TOO-LARGE",
        "E-REPL-LEVEL-DUPLICATE",
        "E-REPL-LEVEL-FIELD",
        "E-REPL-LEVEL-DEPTH",
        "E-REPL-LEVEL-BATCH-INNER",
        "E-REPL-KIND",
        "E-REPL-N",
        "E-REPL-SEED-COLLISION",
    }
)


def _declared_count(level: dict[str, Any]) -> Any:
    """The count key this level's kind actually takes, exactly as declared.

    `reference.md` § Repeat kinds gives each kind its own fields *and only these*:
    a `fold` takes `k` (and an optional `stratify_by`), a `seed` and a `batch`
    take `n`. Reading `n` first and falling back to `k` for every kind is what let
    `{kind: fold, k: 2, n: 5}` report a five-execution budget for a run that
    executes two folds — one declaration meaning two different things to two
    readers. `resolve_repeats` refuses that cross-talk outright
    (`E-REPL-LEVEL-FIELD`); this function is the arithmetic half of the same
    rule, so the number every check here derives is the number the run executes.
    """
    return level.get("k") if level.get("kind") == "fold" else level.get("n")


def _level_count(level: dict[str, Any], unit_count: int | None) -> int | None:
    """This level's count as a number, or `None` when there isn't one to have.

    `None` covers two cases the callers separate with `_declared_count`: nothing
    declared at all (which contributes 1×), and a count declared but unresolvable
    — `{kind: fold, k: all}` against a roster that did not resolve, or any other
    string `k`, which `resolve_repeats` reports by name. A resolvable `k: all` is
    the roster size, the same number `_fold_k` gives the run.
    """
    count = _declared_count(level)
    if count == "all" and level.get("kind") == "fold":
        return unit_count
    if isinstance(count, bool) or not isinstance(count, int | float):
        return None
    return int(count)


def _check_replication(
    doc: dict[str, Any],
    template: Any,
    c: Collector,
    *,
    experiment: Any | None = None,
    unit_count: int | None = None,
) -> None:
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    # A `fold` level partitions units into train/test splits; with no
    # `data.units` declared there is no roster to partition at all. Left
    # unchecked, `resolve_repeats` accepts a fixed `k` with `unit_count=None`
    # (only `k: all` needs a count, and that already reports `E-REPL-FOLD-K`) —
    # so a config with a fold and no units would validate clean and then, at
    # `run`, either crash (`fold_members_for` zips a fold's members against no
    # partitions) or, worse, complete: `k` roster-less repeats all executing
    # against nothing while `sweep.yaml`/`run.yaml` describe a k-fold
    # cross-validation that never happened. Caught here, at the declaration,
    # rather than guarded at `run` — a config that validates clean must not
    # then fail (see `docs/superpowers/spec-defects.md`).
    if any(level.get("kind") == "fold" for level in levels) and not (doc.get("data") or {}).get(
        "units"
    ):
        c.error(
            "E-REPL-FOLD-NO-UNITS",
            "replication.repeats",
            "a `fold` level partitions units, and `data.units` is not declared; "
            "there is nothing to partition",
        )
    total = 1
    any_invalid = False
    has_unresolved_fold = False
    for level in levels:
        count = _level_count(level, unit_count)
        if count is None and isinstance(_declared_count(level), str):
            # The count is declared as a word rather than a number and could not
            # be resolved — `{kind: fold, k: all}` with no roster, or any other
            # string `k`, which `resolve_repeats` reports by name as
            # `E-REPL-FOLD-K` below. The total from here on is not a fact: don't
            # fold a guess into it, and don't derive a floor warning from it.
            # Deliberately `str` rather than "not a number": a `n: yes` (a bool
            # under YAML) is the one repeat `resolve_repeats` will execute, so
            # treating it as unknown would suppress the budget check for the
            # whole config over a typo — the silent skip this pass exists to end.
            has_unresolved_fold = True
            continue
        if count is not None and int(count) < 1:
            c.error(
                "E-REPL-N",
                "replication.repeats",
                f"declares {count}, which executes nothing; the count must be at least 1",
            )
            any_invalid = True
            continue
        total *= 1 if count is None else int(count)
    if any_invalid:
        return  # a floor warning derived from an invalid design would be noise
    if not has_unresolved_fold and total < template.default_repeats:
        c.warn(
            "W-REPL-FLOOR",
            "replication.repeats",
            f"total of {total} is below this convention class's default of "
            f"{template.default_repeats}",
        )

    # `resolve_repeats` raises for refusals that are properties of the declaration
    # itself — fold, duplicate kinds, and depth past two levels among them. At run
    # time raising is right; here `validate` collects, so translate rather than let
    # it escape. The digest is a placeholder: seeds are irrelevant to a declaration
    # check, only the shape of `replication.repeats` is. `unit_count` is the roster
    # `_check_units` already resolved, threaded through rather than resolved again —
    # `k: all` and an oversized `k` can only be checked against a real count. When
    # the roster failed to resolve, `unit_count` is `None` and `k: all` reports
    # `E-REPL-FOLD-K`, which is honest: the fold count genuinely cannot be known,
    # and the roster's own finding is already reported beside it.
    try:
        resolve_repeats(doc, "validate", unit_count=unit_count)
    except ContractError as exc:
        if exc.code in REPL_DECLARATION_CODES:
            c.error(exc.code, "replication.repeats", str(exc))
        else:
            raise

    # A `batch` says *when*, not *what*: it re-executes the pipeline to capture the
    # apparatus drifting between blocks. If nothing in the pipeline declares itself
    # nondeterministic, there is no drift to capture. `experiment is not None` is
    # load-bearing — when the import failed, `E-ENTRYPOINT-IMPORT` is already
    # reported, and a second finding about a pipeline nobody could load is noise.
    kinds = {lv.get("kind") for lv in levels if isinstance(lv, dict)}
    if "batch" in kinds and experiment is not None:
        if not any(getattr(s, "nondeterministic", False) for s in experiment.steps):
            c.warn(
                "W-REPL-DETERMINISTIC",
                "replication.repeats",
                "declares a `batch` level, but no step sets `nondeterministic = True`; "
                "under a fully deterministic pipeline a batch recomputes the same answer "
                "each time, so its dispersion is a row of zeros bought with n× the compute",
            )

    order = (doc.get("replication") or {}).get("order")
    if order is not None and order not in ("as_declared", "randomized"):
        c.error(
            "E-REPL-ORDER",
            "replication.order",
            f"is `{order}`; the only orders are `as_declared` and `randomized`",
        )


def _check_unimplemented(doc: dict[str, Any], c: Collector) -> None:
    """Declared-but-unimplemented blocks, refused rather than silently ignored.

    This build expands `sweep.baseline`, `sweep.grid`, `sweep.paired`,
    `sweep.sample` and `sweep.ablate` only. Both declared orders are honored — `randomized`
    shuffles within each batch and `as_declared` leaves the plan's step-major
    layout alone. `sweep.paired` is no longer refused here: `_axes` composes it
    as a single axis whose cells set several paths at once, per § Expansion
    modes — `_check_shape` guards its container and entry shapes, and
    `_check_sweep` refuses a path it shares with another axis-shaped mode
    (`E-SWEEP-PATH-DUPLICATE`), the same way a bad `grid` shape or an
    unresolvable `grid` path already were. Neither is `sweep.sample`, which
    composes as one axis of `n` realized draws seeded from the design digest:
    `_check_shape` guards every shape `_sample_cells` reads and `_check_sweep`
    reports the value-level residue as `E-SWEEP-SAMPLE-INVALID`, its paths
    through the same `E-SWEEP-PATH-UNKNOWN` `grid` uses, and its bounds through
    the same `E-PARAM-VALUE` (§ Validation, "Sample ranges"). Neither is
    `sweep.ablate`, which `expand` applies after the product as the one mode that
    does not multiply: `_check_shape` guards every shape `ablation_changes`
    reads, and `_check_sweep` checks each `override` value against its own
    `Param` on the same `E-PARAM-VALUE`/`E-SWEEP-VALUE-UNNAMEABLE` pair a `grid`
    value gets. Its composition rules are checked there too, as of this slice —
    a `remove` on a parameter that can hold neither `false` nor `null`
    (`E-SWEEP-ABLATE-TARGET`), `ablate` without a `baseline`
    (`E-SWEEP-ABLATE-BASELINE-MISSING`), and `ablate` crossed with a parameter
    axis (`E-SWEEP-ABLATE-CROSSED`). The one § Validation row still open is
    "Ablation baseline isn't a group level", which needs a group axis to have a
    level for a baseline to fix. `.groups` is read by nothing yet. It resolves a unit roster, but
    several `data.units` sub-fields — allocation other than
    `within`, `assign`, `cluster_by`, `weight_by`, `measurements`, `holdout`,
    and a `resolver` source — are read by nothing yet either. Each of these
    would otherwise validate clean and then run something other than what the
    config describes — the same class of failure `resolve_repeats` already
    refuses for repeat levels: `E-REPL-FOLD-STRATIFY-UNSUPPORTED` for
    `fold.stratify_by`, `E-REPL-LEVEL-DUPLICATE` for two levels of the same
    kind, and `E-REPL-LEVEL-DEPTH` past two levels, and
    `E-REPL-LEVEL-BATCH-INNER` for a `batch` that is not the outermost level.
    `batch` and `fold` themselves are no longer refused — both are supported
    kinds. `statistics.resample` and `.null_test`, and a top-level `hypotheses`
    block, are refused the same way — a declared 2000-draw bootstrap or
    a pre-registered hypothesis that runs and reports success while honoring
    neither is the same silent-no-op class. `statistics.contrasts` is no longer in
    this family: `_check_contrasts` now resolves and checks each declared entry
    instead of refusing the block wholesale. Neither is `statistics.report_by`,
    which `_check_report_by` now checks for real instead of refusing wholesale.
    Neither is `statistics.correction`,
    which `cli.py` now applies: every comparison carries `ci95_corrected`,
    `correction_level`, `family_size`, and `family`, so what this module owes it
    is the value checks below (`E-STATS-CORRECTION-UNKNOWN`,
    `W-STATS-CORRECTION-INAPPLICABLE`) plus `W-STATS-FAMILY` on the one value that
    opts out — `none`, which corrects nothing and records `correction: null` to
    say so. Each remaining message says
    plainly that the block is honored in a later slice, so a user does not read this as
    their config being malformed.
    """
    sweep = doc.get("sweep") or {}
    for mode, code, why in (
        (
            "groups",
            "E-SWEEP-GROUPS-UNSUPPORTED",
            "is an axis over units rather than parameters, so it needs "
            "`data.units.allocation` and `data.units.assign`",
        ),
    ):
        if sweep.get(mode):
            c.error(
                code,
                f"sweep.{mode}",
                f"{why}, and is specified but not implemented in this build — this build "
                "expands `baseline`, `grid`, `paired`, `sample` and `ablate` only; `groups` "
                "will be "
                "honored in a later slice",
            )

    # A baseline that leaves some swept PATH unfixed. `reference.md`:1415-1422
    # states one rule with two cases: the baseline expands over whichever axes it
    # does not fix, giving one baseline condition per cell of the unfixed axes.
    # `expand` emits exactly one `00_baseline` row carrying only what the baseline
    # literally names, so the declared design is not the executed design — the
    # failure every other refusal in this function exists to prevent. Per-cell
    # expansion is a real feature; until it lands, refuse rather than diverge.
    # A baseline fixing every swept path (including the no-sweep-axis case) is
    # the supported row and is unaffected. `_swept_paths` is every axis-shaped
    # mode's paths, not `grid`'s alone — `paired` composes into this same product
    # now, and a baseline that fixes `grid` but leaves a `paired` axis free is the
    # identical declared-vs-executed mismatch this check exists to catch. An
    # *ablated* path is deliberately not in that set (see `sweep.ablated_paths`):
    # `ablate` is not an axis, there are no cells for a baseline to expand over,
    # and firing this refusal on an `override` path the baseline does not fix
    # would refuse a legal config with a message about cells that do not exist.
    #
    # This check is path-granular, not axis-granular: it asks "does every swept
    # path have some baseline value", not "does the baseline supply a whole cell
    # of a `paired` axis". A baseline naming only half of one `paired` entry's
    # paths passes this check pointing at the still-unfixed path, exactly as it
    # would for two independent `grid` axes — and a value that isn't any declared
    # `paired` cell (a mix-and-match the axis never produces) is not itself
    # caught here, since per-cell baseline expansion (which would need to resolve
    # a baseline against actual cells) is Task 6's feature, not this refusal's.
    baseline = sweep.get("baseline") or {}
    unfixed = [path for path in _swept_paths(sweep) if path not in baseline]
    if baseline and unfixed:
        c.error(
            "E-SWEEP-BASELINE-PARTIAL",
            "sweep.baseline",
            f"fixes no value for {', '.join(f'`{p}`' for p in unfixed)}, and a baseline "
            "that leaves an axis free expands to one baseline condition per cell of the "
            "unfixed axes — which is specified but not implemented in this build; this "
            "build emits a single `00_baseline` condition, so the design executed would "
            "not be the design declared. Per-cell baselines will be honored in a later "
            "slice; fix a value on every swept axis for now",
        )

    units = _units_declaration(doc.get("data") or {}, c) or {}
    source = units.get("from")
    if isinstance(source, dict) and "resolver" in source:
        c.error(
            "E-DATA-RESOLVER-UNSUPPORTED",
            "data.units.from.resolver",
            f"names `{source['resolver']}`, but resolvers are plugin artifacts and the "
            "plugin registry is not implemented in this build; resolvers will be honored "
            "in a later slice. Use a table or a glob for now",
        )
    if units.get("allocation") not in (None, "within"):
        c.error(
            "E-DATA-ALLOCATION-UNSUPPORTED",
            "data.units.allocation",
            f"`{units['allocation']}` allocation is specified but not implemented in this "
            "build — it needs a `sweep.groups` axis to say what the arms are, and group "
            "axes are not implemented either; both will be honored in a later slice. "
            "`within`, the default, is the supported value and is what a single-condition "
            "run means regardless",
        )
    for field, code in (
        ("assign", "E-DATA-ASSIGN-UNSUPPORTED"),
        ("cluster_by", "E-DATA-CLUSTER-UNSUPPORTED"),
        ("weight_by", "E-DATA-WEIGHT-UNSUPPORTED"),
        ("measurements", "E-DATA-MEASUREMENTS-UNSUPPORTED"),
        ("holdout", "E-DATA-HOLDOUT-UNSUPPORTED"),
    ):
        # `init` writes these as null; only a real declaration is refused.
        if units.get(field):
            c.error(
                code,
                f"data.units.{field}",
                "is specified but not implemented in this build — it is read by nothing "
                "here, and a declaration that changes no behavior is the failure this "
                "refusal exists to prevent; it will be honored in a later slice",
            )

    # `statistics.resample`/`.null_test` validate clean today and are read by
    # nothing — the same silent-no-op class as the fields above.
    # `statistics.contrasts`, `statistics.report_by` and the top-level
    # `hypotheses` block used to be in this list too; they are now checked for
    # real by `_check_contrasts`, `_check_report_by` and `_check_hypotheses`
    # instead of being refused wholesale — `cli.py` evaluates every declared
    # hypothesis and writes its verdict, so the declaration changes the record.
    # `statistics.correction` is not in it either, and no longer for a disclosure
    # reason: `cli.py` applies it, so a declared correction changes the record —
    # the correction checks further down this module check its *value* instead,
    # and warn only on `none`, which corrects nothing by request.
    # `materialize.py` writes only two of these keys into a generated config —
    # `statistics.correction` and a top-level `hypotheses: []` — so `resample`
    # and `null_test` are simply absent there; each check below fires on a real
    # declaration either way, never on a key's mere presence or on the empty
    # list `hypotheses` is generated as.
    statistics = doc.get("statistics") or {}
    for field, code, what in (
        (
            "resample",
            "E-STATS-RESAMPLE-UNSUPPORTED",
            "no resampling scheme runs",
        ),
        (
            "null_test",
            "E-STATS-NULLTEST-UNSUPPORTED",
            "no null distribution is computed",
        ),
    ):
        if statistics.get(field):
            c.error(
                code,
                f"statistics.{field}",
                f"is specified but not implemented in this build — {what}, and a "
                "declaration that changes no behavior is the failure this refusal "
                "exists to prevent; it will be honored in a later slice",
            )


def _repeat_total(doc: dict[str, Any], unit_count: int | None) -> int | None:
    """The product of every repeat level's count, permissively: an invalid level
    (`n < 1`) is already reported by `_check_replication` under its own identifier,
    so this treats it as absent rather than reporting the same defect twice under
    `W-EXEC-BUDGET`.

    `{kind: fold, k: all}` resolves against `unit_count` — the roster
    `_check_units` already resolved — because leave-one-out is the single design
    `W-EXEC-BUDGET` matters most for (`reference.md` § Sweeps and repeats), and
    it was the one design that could not produce the warning while this function
    read a string and gave up.

    Returns `None` only when a count declared as a *word* cannot be resolved: a
    `k: all` whose roster did not resolve, or a string `k` that is not `all`
    (reported by name as `E-REPL-FOLD-K`). Anything else unreadable — a `n: yes`,
    which YAML parses as a bool — executes 1× and is reported under its own
    identifier, so it contributes 1× here rather than suppressing the check for
    the whole config. Silently treating an unresolved level as
    contributing 1× would understate the total by the roster size — a wrong
    small number is worse than admitting the total is unknown, so the caller
    skips the check rather than trust a guess.
    """
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
    for level in levels:
        count = _level_count(level, unit_count)
        if count is None:
            # A string count that did not resolve is genuinely unknown; anything
            # else unreadable (a bool, a list) is reported under its own
            # identifier and executes 1×, so it must not suppress this check.
            if isinstance(_declared_count(level), str):
                return None
            continue
        if count >= 1:
            total *= count
    return total


def _check_sampled_values(
    sample: Any, spec: dict[str, Any], conditions: list[Any], c: Collector
) -> None:
    """Every value `sweep.sample` actually draws satisfies its own `Param`.

    **Checking the bounds is not checking the values, and only the values
    execute.** `uniform: [10, 200]` over `Param(int, ge=2)` has two perfectly
    legal integer bounds and draws `118.38516808291541`, which a step then reads
    where the template declares an `int`; `int_uniform: [10, 50]` over
    `Param(int, choices=[10, 50])` passes on both endpoints and draws `37`,
    which is neither choice. Both validate clean under a bounds-only check and
    then run a config § Validation's "Types" and "Choices" rows promise to
    refuse — the validates-clean-misbehaves-at-run class, one level up from the
    shape class `_check_shape` and `sample_fault` close.

    **The realized values are checked rather than the declaration's *form*,**
    deliberately. Refusing "a non-`int_uniform` range on an `int` parameter"
    would catch the first example and nothing else: it says nothing about
    `choices`, `pattern`, `ge`/`lt`, or a `log_uniform` range that dips under a
    `gt=0`, and the constraint vocabulary is closed but not small. What executes
    is the drawn value, so that is what `Param.check` is asked about — the same
    call `grid` values and `baseline` values already go through, on the same
    identifier (`E-PARAM-VALUE`), rather than a `sample`-shaped approximation of
    it.

    Its cost, stated rather than hidden: the finding names a value the user did
    not literally write. That is why the message quotes both the drawn value and
    the range that produced it. It is not flaky — the draw is deterministic
    given the config, so "this config draws an illegal value" is as stable a
    claim as any other check here, and re-running `validate` on an unedited
    config reports the same value. Only the *first* offending draw per path is
    reported: `n: 50` over a wrong-typed range is one mistake, not fifty.
    """
    if not sample or sample_fault(sample) is not None:
        return
    for path in sample["ranges"]:
        if path not in spec:
            continue  # already reported as `E-SWEEP-PATH-UNKNOWN`
        for condition in conditions:
            if path not in condition.values:
                continue
            value = condition.values[path]
            problem = spec[path].check(value)
            if problem is None:
                continue
            form = next(iter(sample["ranges"][path]))
            hint = ""
            if spec[path].type_ is int and form != "int_uniform":
                hint = " — `int_uniform` is the form that draws integers"
            c.error(
                "E-PARAM-VALUE",
                f"sweep.sample.ranges.{path}.{form}",
                f"draws `{render_value(value)}`, which {problem.lstrip()}{hint}",
            )
            break


def _check_sweep(
    doc: dict[str, Any], template: Any, c: Collector, *, unit_count: int | None = None
) -> None:
    """Checks that only become reachable once a sweep actually expands: an
    unrecognised mode, an axis with nothing in it, a swept path the template
    doesn't declare, a value the spec itself rejects, a value that can't render
    into a condition label, the execution budget, and the multiplicity family
    an enumerated sweep creates. `sweep.expand` is the single source of the
    condition count — re-deriving it here is exactly the drift Task 4 was
    told not to reintroduce.

    `E-SWEEP-EXPANDS-EMPTY` is a backstop beneath the per-axis checks above,
    not a replacement for them: it refuses on the *result* of `expand(doc)`
    being zero conditions, whatever shape of `sweep` produced that — an empty
    `grid` axis still gets the specific `E-SWEEP-AXIS-EMPTY` diagnosis (this
    check runs after, so it never displaces that one), but a declared `sweep`
    with no shape anyone enumerated here — `{grid: {}}`, or a hand-written
    block of falsy keys — is still caught, because it is checked mechanically
    against what would actually execute rather than against a list of shapes
    someone thought of. A run that would otherwise execute zero conditions
    while reporting `status: completed` is exactly the failure this project
    treats as worst: a record describing an experiment nobody performed.
    """
    import difflib

    sweep = doc.get("sweep") or {}
    # Not a literal set: `sweep.SWEEP_MODES` is `AXIS_MODES + NON_AXIS_MODES`,
    # and this check is the vocabulary's choke point — a mode absent from it is
    # refused here, so no config can use one. Reading the derived tuple is what
    # makes `E-SWEEP-ABLATE-CROSSED`'s "any axis-shaped mode" true of a mode
    # added later: it cannot become usable without being classified as an axis
    # or not. A literal here would let the two drift, with this check accepting
    # a mode `axis_modes_present` has never heard of.
    for key in sweep:
        if key not in SWEEP_MODES:
            near = difflib.get_close_matches(key, sorted(SWEEP_MODES), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-SWEEP-KEY-UNKNOWN",
                f"sweep.{key}",
                # The vocabulary comes from `SWEEP_MODES`, the same tuple the
                # check gates on. Naming the *implemented* modes here instead
                # made the message contradict its own emit site the moment the
                # two lists diverged: this branch accepts `groups` and the
                # sentence said `expand` does not understand it. A mode that is
                # recognized but not built is refused by its own
                # `-UNSUPPORTED` code, which is where that fact belongs.
                f"is not a sweep mode{hint} — the modes are "
                + ", ".join(f"`{mode}`" for mode in sorted(SWEEP_MODES))
                + ", so an unrecognised key would expand to zero conditions and the run "
                "would execute nothing while reporting success",
            )

    spec = template.parameter_spec

    def _path_resolves(path: str, where: str) -> bool:
        """`path` names a parameter this template declares. Shared by `grid` and
        `baseline` deliberately: both fix a value at a dotted `parameters` path,
        and two copies of this check is how the two drift apart."""
        if path in spec:
            return True
        near = difflib.get_close_matches(path, list(spec), n=1)
        hint = f" — did you mean `{near[0]}`?" if near else ""
        c.error("E-SWEEP-PATH-UNKNOWN", where, f"is not a parameter of this template{hint}")
        return False

    def _value_checks(path: str, value: Any, where: str, nameable: bool) -> None:
        """The value satisfies its own `Param`, and — for a value that will be
        rendered into a condition label — is nameable.

        `nameable` is False for a `baseline` entry: `sweep.label_for` returns the
        literal `baseline` for a baseline condition, so its fixed values are never
        rendered into a label, and refusing an unnameable one would reject a config
        that is legal (`reference.md`:1419 labels a per-cell baseline by the axes it
        leaves *free*, so this stays true when that expansion lands).
        """
        problem = spec[path].check(value)
        if problem:
            c.error("E-PARAM-VALUE", where, problem)
        if nameable:
            unnameable = check_swept_value(value)
            if unnameable:
                c.error("E-SWEEP-VALUE-UNNAMEABLE", where, unnameable)

    grid = sweep.get("grid") or {}
    for path, values in grid.items():
        if not values:
            c.error(
                "E-SWEEP-AXIS-EMPTY",
                f"sweep.grid.{path}",
                "declares no values, so the sweep expands to zero conditions and the run "
                "would execute nothing while reporting success",
            )
            continue
        if not _path_resolves(path, f"sweep.grid.{path}"):
            continue
        for i, value in enumerate(values):
            _value_checks(path, value, f"sweep.grid.{path}[{i}]", nameable=True)

    # `sweep.sample`, from three angles, in the order a reader would ask them.
    # First whether the declaration can be drawn from at all: `sample_fault` is
    # `sweep.py`'s own gate, shared rather than reimplemented so the check that
    # reports and the code that draws can never disagree about what is legal.
    # Then, only once it can, the two checks that need the template: each swept
    # path is a parameter it declares (`E-SWEEP-PATH-UNKNOWN`, the same check
    # `grid` gets), and each bound satisfies that parameter's own constraints —
    # which is § Validation's "Sample ranges" row exactly, whose example
    # ("upper bound 1.4 violates the parameter's `lt=1`") is `Param.check` on
    # the bound, and so reports `E-PARAM-VALUE` like every other illegal value
    # rather than a code of its own. A bound is checked `nameable=False`: it is
    # never rendered into a label — the *drawn* value is — and a drawn float
    # always renders inside `SWEPT_VALUE_PATTERN`.
    sample = sweep.get("sample")
    if sample:
        fault = sample_fault(sample)
        if fault is not None:
            c.error("E-SWEEP-SAMPLE-INVALID", "sweep.sample", fault)
        else:
            # Not `spec` — that name is this function's `template.parameter_spec`,
            # which `_path_resolves` and `_value_checks` both close over.
            for path, declared_range in sample["ranges"].items():
                if not _path_resolves(path, f"sweep.sample.ranges.{path}"):
                    continue
                form, bounds = next(iter(declared_range.items()))
                for i, bound in enumerate(bounds):
                    _value_checks(
                        path, bound, f"sweep.sample.ranges.{path}.{form}[{i}]", nameable=False
                    )

    # `grid` and `paired` writing the same path is not a shape fault — both are
    # well-formed on their own — but `expand`'s product applies each axis's cell
    # to `values` in declared order, so whichever mode is later in `_axes`
    # silently overwrites the other's value for that path on every combination.
    # Some combinations then collapse to byte-identical `values`: two different
    # `grid` settings paired with the same `paired` entry both resolve to that
    # entry's value, producing duplicate conditions `_condition_labels` cannot
    # see (it collects into a `set`). Filed as a spec gap in
    # `docs/superpowers/spec-defects.md` — § Expansion modes never states that a
    # path belongs to at most one axis-shaped mode — and refused here rather
    # than left to execute a design other than the one declared.
    #
    # Walked over every axis-shaped mode rather than the `grid`/`paired` pair it
    # started as: `sample` joins the same product, so a path it shares with
    # either would reopen exactly this hole through a third route — and a draw
    # overwritten by a `grid` cell is worse than the enumerated case, since the
    # drawn value is recorded in `sweep.yaml` as the condition's while the run
    # used another. The report names the *later* mode, which is the one whose
    # value wins, in `_axes` order (grid, then paired, then sample).
    named_by: dict[str, list[tuple[str, str]]] = {}

    def _names(mode: str, path: Any, where: str) -> None:
        if isinstance(path, str):
            named_by.setdefault(path, []).append((mode, where))

    for path in grid:
        _names("grid", path, f"sweep.grid.{path}")
    for i, entry in enumerate(sweep.get("paired") or []):
        if isinstance(entry, dict):
            for path in entry:
                _names("paired", path, f"sweep.paired[{i}]")
    if isinstance(sample, dict) and isinstance(sample.get("ranges"), dict):
        for path in sample["ranges"]:
            _names("sample", path, f"sweep.sample.ranges.{path}")

    for path in sorted(named_by):
        occurrences = named_by[path]
        modes = {mode for mode, _ in occurrences}
        if len(modes) < 2:
            continue  # one mode naming a path repeatedly is that mode's own business
        last_mode = occurrences[-1][0]
        earlier = ", ".join(
            f"`{where}`" for mode, where in occurrences if mode != last_mode
        )
        c.error(
            "E-SWEEP-PATH-DUPLICATE",
            f"sweep.{last_mode}.{path}",
            f"is also written by {earlier} — two axis-shaped modes "
            "writing the same path make `expand`'s product overwrite one mode's value "
            "with the other's on every combination, collapsing some conditions to "
            "duplicates the run would silently execute twice",
        )

    # `sweep.baseline` gets the same per-entry checks — one value, not a list.
    # `reference.md`:218 names this by example ("Baseline is a valid condition |
    # `sweep.baseline` sets `analysis.method: pearsonn`"). Unchecked, a misspelled
    # path was planted verbatim into condition `00`'s config by
    # `resolve_condition_cfg`'s `setdefault` walk, so `00_baseline` ran the base
    # config under a label claiming otherwise and the run reported success.
    baseline = sweep.get("baseline") or {}
    for path, value in baseline.items():
        if _path_resolves(path, f"sweep.baseline.{path}"):
            _value_checks(path, value, f"sweep.baseline.{path}", nameable=False)

    # `sweep.ablate.override`, through the same two checks, because an override
    # entry is structurally a `grid` value: a value the user wrote at a dotted
    # path, planted into a condition's config and rendered into its label. Left
    # unchecked, `override: [{analysis.method: pearsonn}]` executes a condition
    # whose config holds a value § Validation's "Choices" row promises to refuse,
    # and `nameable=True` because an override value — unlike a `baseline` one —
    # *is* what `label_for` renders, so a value carrying the axis separator would
    # produce a label that cannot be parsed back into axes.
    #
    # Gated on `_path_resolves` first, exactly as the `grid` and `sample` loops
    # are: `_value_checks` indexes `spec[path]` unguarded, so an unknown path
    # would raise `KeyError` inside a function contracted never to raise.
    #
    # A `remove` path takes the SAME path check, on the same identifier, for the
    # same reason `baseline` does: `expand` plants `false`/`null` at it through
    # `resolve_condition_cfg`'s `setdefault` walk, so a misspelling
    # (`remove: [analysis.methdo]`) creates a parameter this template never
    # declared and runs a condition whose label claims a change nothing made.
    # What `remove` then *produces* at a path that does resolve is
    # `E-SWEEP-ABLATE-TARGET`'s question, below.
    ablate = sweep.get("ablate")

    # § Expansion modes: `ablate` "reads the baseline rather than re-emitting
    # it", so without one there is nothing for a change to be one change away
    # *from* — "It therefore requires `sweep.baseline`, which `validate`
    # checks". `expand` is permissive here by design (it emits n conditions
    # each carrying only its own change), which is why the refusal lives here
    # rather than there. Truthiness, not presence: `init` writes `ablate: null`,
    # and a null `ablate` expands to nothing and is not a declared ablation.
    if ablate and not baseline:
        c.error(
            "E-SWEEP-ABLATE-BASELINE-MISSING",
            "sweep.ablate",
            "is declared but `sweep.baseline` is not — an ablation is one change away "
            "from the baseline, so there is nothing to ablate from; without one, each "
            "ablated condition carries only its own change and the run has no reference "
            "condition to compare against. Declare `sweep.baseline`",
        )

    # § Expansion modes: "the product of 'vary one thing at a time' with a
    # second parameter axis is no longer one thing at a time, and there is no
    # defensible reading of what it would mean". The modes come from
    # `sweep.AXIS_MODES` rather than a tuple written here — the rule names no
    # mode ("a second parameter axis"), and neither should its enforcement. A
    # mode added to `_axes` alone would still slip past this, which is why
    # `AXIS_MODES` is not the pin: `known` above reads `SWEEP_MODES`, derived
    # from `AXIS_MODES + NON_AXIS_MODES`, so a seventh mode is refused outright
    # (`E-SWEEP-KEY-UNKNOWN`) until someone classifies it — and classifying it
    # as an axis is what puts it here.
    # `groups` is deliberately absent from that set and is the row's stated
    # exception: it varies units rather than parameters, so every condition is
    # still exactly one parameter change from its own arm's baseline. (`groups`
    # is refused for its own reason today, `E-SWEEP-GROUPS-UNSUPPORTED`.)
    crossed_modes = axis_modes_present(sweep) if ablate else []
    if crossed_modes:
        c.error(
            "E-SWEEP-ABLATE-CROSSED",
            "sweep.ablate",
            f"cannot be combined with {', '.join(f'`sweep.{m}`' for m in crossed_modes)} — "
            "`ablate` varies one thing at a time and a parameter axis varies a second, "
            "so their product is no design with a defensible reading. Split the axis "
            "into its own run, or express the ablation as `paired` rows. Only "
            "`sweep.groups` composes with `ablate`, because it varies units rather than "
            "parameters",
        )

    if isinstance(ablate, dict):
        for i, path in enumerate(ablate.get("remove") or []):
            if not isinstance(path, str) or not _path_resolves(
                path, f"sweep.ablate.remove[{i}]"
            ):
                continue
            # § Validation, "Ablation targets": "`sweep.ablate.remove[0]` is
            # `analysis.min_samples` (int); `remove` needs a boolean or nullable
            # parameter — use `override`". Two branches, one identifier, because
            # they are one question asked of the two things that answer it —
            # the parameter, and the baseline `sweep.removal_value` reads.
            #
            # Branch 1 is the row's own words and is a fact about the parameter
            # alone, so it is ungated by the baseline: a `remove` on an `int`
            # with no `null` in its domain has nothing `remove` could set it to,
            # whatever the baseline says.
            #
            # Branch 2 exists because task 4 coupled the two readings (see
            # `docs/superpowers/spec-defects.md`, "Row 216 has two readings"):
            # `removal_value` picks `false` versus `null` from the *baseline's*
            # value, having no `parameter_spec` to ask, so a boolean the
            # baseline does not fix takes the nullable reading and plants `null`
            # at a non-nullable parameter — branch 1 passes it (it is a boolean)
            # and the run executes a value the "Types" row promises to refuse.
            # Checking what `removal_value` produces rather than what the config
            # declares is what closes that: the declaration is legal and the
            # product is not. It is `elif`, and gated on a declared baseline,
            # because `E-SWEEP-ABLATE-BASELINE-MISSING` owns the no-baseline
            # config whole — reporting every `remove` entry again there would
            # restate one fault n times.
            #
            # `remove` only, never `override`: an override states its own value,
            # so the baseline does not decide what it produces, and refusing an
            # override on a path the baseline leaves free would reject a legal
            # config (the same line `sweep.ablated_paths` draws for
            # `E-SWEEP-BASELINE-PARTIAL`).
            param = spec[path]
            where = f"sweep.ablate.remove[{i}]"
            if not (param.type_ is bool or param.nullable):
                c.error(
                    "E-SWEEP-ABLATE-TARGET",
                    where,
                    f"is `{path}`, which is neither a boolean nor nullable — `remove` "
                    "sets a boolean parameter to `false` and a nullable one to `null`, "
                    "and this parameter can hold neither; use `override` to state the "
                    "value the ablated condition should run instead",
                )
                continue
            problem = param.check(removal_value(baseline, path))
            if baseline and problem:
                c.error(
                    "E-SWEEP-ABLATE-TARGET",
                    where,
                    f"is `{path}`, which `sweep.baseline` fixes no *boolean* value for — "
                    "so `remove` reads the baseline, finds nothing it can turn off, and "
                    f"sets `null` rather than `false`, which {problem.lstrip()}. "
                    "Fix the parameter to `true` or `false` in `sweep.baseline`: an "
                    "ablation is one change away from the baseline, so the baseline has "
                    "to state what is being removed",
                )
        for i, entry in enumerate(ablate.get("override") or []):
            if not isinstance(entry, dict):
                continue  # `_check_shape` already refused it, fatally
            for path, value in entry.items():
                where = f"sweep.ablate.override[{i}].{path}"
                if _path_resolves(path, where):
                    _value_checks(path, value, where, nameable=True)

    # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
    # `validate` collects findings and never raises. A `sweep.grid` axis value
    # of `null` reaches here — past the per-axis `E-SWEEP-AXIS-EMPTY` check
    # above, which fires only on a value that is *present and falsy* and then
    # `continue`s past the rest of the per-axis body, and past `_check_shape`'s
    # per-axis `list` guard, which refuses only a *present, non-list* value —
    # and makes `itertools.product` raise `TypeError` inside `expand`.
    # `E-SWEEP-EXPANDS-EMPTY` below is deliberately skipped rather than fired
    # on the caught exception: that check means "this sweep is shaped well
    # enough to expand, and expanding it yields nothing," a different and more
    # specific claim than "this sweep could not be expanded at all," and
    # firing it here would misreport a crash as an empty grid.
    # `conditions = []` regardless, so every later use in this function (the
    # execution-budget arithmetic below) sees zero rather than reading a name
    # that was never assigned.
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    else:
        if sweep and not conditions:
            c.error(
                "E-SWEEP-EXPANDS-EMPTY",
                "sweep",
                "expands to zero conditions, so the run would execute nothing while "
                "reporting success — declare `baseline`, a non-empty `grid`, or remove "
                "`sweep` entirely",
            )
        _check_sampled_values(sample, spec, conditions, c)

    # `reference.md` § Validation, "Baseline leaves contrasts confounded": a
    # `sweep.baseline` that "fixes a value on every axis" leaves comparisons that
    # "differ on both and are reported `confounded: true`". `cli.py` computes
    # that fact per comparison at run time, after the compute is spent; the
    # declaration alone decides it, so it is warnable here.
    #
    # **The condition is the row's, and it is deliberately narrower than run
    # time.** Axes are compared over `sweep.grid`'s keys only, and only when the
    # baseline fixes every one of them — which is the row's own "fixes a value
    # on every axis", and is also the only baseline-plus-grid shape this build
    # admits at all (`_check_unimplemented`'s `E-SWEEP-BASELINE-PARTIAL` refuses
    # a baseline that leaves an axis free, since per-cell baseline expansion is
    # specified but not implemented). `cli._differing_axes` instead walks the
    # *union* of both sides' keys against a sentinel, so a baseline fixing an
    # axis the grid never sweeps adds a differing axis to every comparison and
    # can mark `confounded` where this warning stays silent. That direction is
    # the safe one — this never fires where a run would not mark the comparison
    # — and it is why the three lines below are not `cli._differing_axes` reused:
    # sharing the helper would import the wider semantics along with it.
    #
    # One finding, not one per condition: the fault is a single declaration, and
    # `sweep.baseline` is the line the reader edits.
    baseline_fixed = sweep.get("baseline") or {}
    swept_axes = list(grid)
    if swept_axes and baseline_fixed and all(axis in baseline_fixed for axis in swept_axes):
        crossed: list[tuple[Any, list[str]]] = []
        for cond in conditions:
            if cond.is_baseline:
                continue
            differing = [a for a in swept_axes if cond.values.get(a) != baseline_fixed.get(a)]
            if len(differing) > 1:
                crossed.append((cond, differing))
        if crossed:
            example, axes = crossed[0]
            c.warn(
                "W-SWEEP-BASELINE-CONFOUNDED",
                "sweep.baseline",
                f"fixes a value on every swept axis, so {len(crossed)} of "
                f"{len(conditions) - 1} baseline comparisons differ on more than one axis "
                f"and are reported `confounded: true` — `{example.label}` differs on "
                f"{', '.join(f'`{a}`' for a in axes)}, so its delta mixes those effects "
                "and no amount of correct pairing separates them",
            )

    repeat_total = _repeat_total(doc, unit_count)
    budget = (doc.get("limits") or {}).get("max_executions")
    # `repeat_total` is `None` only when a declared count cannot be resolved at
    # all — a `k: all` whose roster did not resolve, or a string `k` that is not
    # `all` — see `_repeat_total`. Skipping the check rather than computing
    # against a guessed 1× is deliberate: an unknown total must not be reported
    # as a small one. A `k: all` over a roster that DID resolve is a real number
    # here, and warns like any other count.
    # `check_envelope` is what REPORTS a wrong-typed `budget` (E-CONFIG-TYPE) —
    # this guard exists because this function may be reached without it having
    # run: a leaf fault is deliberately non-fatal, so `_check_sweep` still runs
    # on a still-malformed `doc`, and `executions > budget` below would raise
    # `TypeError` comparing an `int` to a `str`. `bool` is excluded explicitly,
    # matching `envelope._is_type`'s own bool-excluding rule for the same leaf
    # (`LEAF_TYPES` types `max_executions` as `int`, not `int | bool`): without
    # the exclusion, `isinstance(True, int)` is `True`, so a `max_executions:
    # true` would both get `E-CONFIG-TYPE` from the envelope AND run this check
    # against a `bool` budget, warning "exceeds True" — a message a wrong-typed
    # value should never be able to produce.
    if repeat_total is not None and isinstance(budget, int) and not isinstance(budget, bool):
        executions = len(conditions) * repeat_total
        if executions > budget:
            c.warn(
                "W-EXEC-BUDGET",
                "limits.max_executions",
                f"{len(conditions)} conditions × {repeat_total} repeats = {executions} "
                f"executions exceeds {budget}",
            )

    # The family is what `resolve_contrasts` will actually build — every
    # baseline comparison plus every declared contrast — not `len(conditions)`.
    # A grid-only sweep declares no baseline, so it publishes no comparison at
    # all, and telling its author they have a family of two was a false
    # positive rather than a backstop (`spec-defects.md`).
    correction = (doc.get("statistics") or {}).get("correction")
    known_corrections = {"none", "bonferroni", "holm", "fdr_bh"}
    # An out-of-enum *string* is the more likely mistake in practice — a typo
    # like `bonferonni` — and left unchecked it collects zero findings while
    # `corrected_for` downstream returns `ci95_corrected: null` with `thin:
    # false` and `correction: "bonferonni"` recorded on every member: a
    # correction named as applied while none was, and `thin: false`
    # suppresses the one signal that would otherwise flag it (`reference.md` §
    # Statistical reporting). Checking `isinstance` before the set membership
    # test is deliberate, not stylistic — `in` on a `set` raises `TypeError`
    # for an unhashable value (a `list` or `dict`), and `and` short-circuits
    # before that ever runs.
    if correction is not None and not (
        isinstance(correction, str) and correction in known_corrections
    ):
        shown = f"`{correction}`" if isinstance(correction, str) else type(correction).__name__
        c.error(
            "E-STATS-CORRECTION-UNKNOWN",
            "statistics.correction",
            f"is {shown}, not one of `none`, `bonferroni`, `holm` or `fdr_bh`",
        )
        correction = None
    # `resolve_contrasts` trusts its caller to have refused an unusable
    # `statistics.contrasts` block first (`contrasts.py`'s own comment leans on
    # this), and `_check_contrasts` is the check that does that — but it runs
    # *after* this one, so a malformed block (a scalar, a non-mapping entry, an
    # unresolvable or nested label) reaches this call first. `validate.py`
    # collects findings and never raises, so a block that cannot be resolved
    # yet counts as no resolvable family here; `_check_contrasts` reports the
    # shape or label fault under its own, more specific code.
    try:
        comparisons = len(resolve_contrasts(doc, conditions))
    except (TypeError, KeyError, AttributeError, ValueError):
        comparisons = 0
    if comparisons > 0 and (correction or "holm") == "none":
        c.warn(
            "W-STATS-FAMILY",
            "statistics.correction",
            f"{comparisons} comparisons per metric form a family, and "
            "`statistics.correction` is `none` — every interval reported is uncorrected, and "
            "each records `correction: null` to say so",
        )
    if comparisons > 0 and correction == "fdr_bh":
        c.warn(
            "W-STATS-CORRECTION-INAPPLICABLE",
            "statistics.correction",
            # The parenthetical this replaces asserted "`statistics.null_test` is
            # undeclared", which is false of a config that declares one — and such
            # a config reaches here, drawing `E-STATS-NULLTEST-UNSUPPORTED` and
            # this warning together. Removing a false assertion is independent of
            # the condition, which still fires on `fdr_bh` over a non-empty family
            # and is narrowed by whichever slice implements `null_test`.
            "`fdr_bh` adjusts p-values, and no comparison in this family can carry one in "
            "this build — every `ci95_corrected` will be null. Use `holm` or `bonferroni`, "
            "whose corrections are interval-shaped",
        )


def _check_contrasts(doc: dict[str, Any], c: Collector, roster: UnitList | None = None) -> None:
    """Each declared `statistics.contrasts` entry, checked for real now that the
    block is no longer refused wholesale (`_check_unimplemented` used to raise
    `E-STATS-CONTRASTS-UNSUPPORTED` for any non-empty declaration).

    `of` and `against` name conditions **by label** (`reference.md` § Contrasts),
    the same grammar `sweep.baseline`/`sweep.grid` resolve against, so a name that
    resolves to nothing would otherwise reach `contrasts.resolve_contrasts` and
    raise a bare `KeyError` at run time — the same silent-failure-deferred-to-a-
    crash class every other check in this module exists to move earlier.

    **Contrasts do not nest.** `reference.md` and `design-principles.md` both say
    a comparison between two contrasts — a dose-response ordering, a difference-
    in-differences, a nested mean over cells — is an *interaction*, not a
    contrast, and stays a `summary`-step `Estimate`. So a side naming another
    entry's `id` is refused under its own code, `E-STATS-CONTRAST-NESTED`, rather
    than the vaguer `E-STATS-CONTRAST-UNKNOWN` an unresolvable label gets — nesting
    is checked first for exactly that reason: an `id` that happens to also fail to
    resolve as a condition label must still be diagnosed as nesting, since that is
    the more specific and more actionable fault. A name that is simultaneously a
    real condition label and another entry's `id` resolves as the label instead —
    a legal contrast must not be refused as nesting just because some other entry
    happens to reuse its label as an `id`.

    **`within` names a unit attribute**, the same one `units_matching` (Task 2)
    reads with `.get`, which returns `None` for a typo exactly as it would for a
    stratum that is genuinely empty of units — the two are indistinguishable
    downstream. So this is checked here, at validate time, against the declared
    `data.units.attributes` list — analogous to the `report_by` unknown-attribute
    rule (`reference.md` § Reporting strata) — rather than left to look like a
    silently-empty stratum.

    **A `within` stratum too thin to disclose is warned about here too**
    (`reference.md` § Validation, "Contrast stratum is populated"), under the
    same `W-STATS-CONTRAST-THIN` the run emits — one code fired at two
    observation points, the way `report_by`'s roster-time and completed-time
    counts are two (`W-STATS-REPORTBY-THIN`/`W-STATS-STRATUM-THIN`). Which of
    those two shapes a future thinness check should take is not settled by
    anything in this function, so this comment does not argue it.

    The count here is over *resolved roster* units matching the stratum, which is
    all `validate` can see: pairing is a fact about which units both sides
    *completed*, and `cli.py`'s `allowed` set is `units_matching` over this same
    roster, so `n_paired` is bounded above by this number — the run-time check is
    what sees the attrition between them, which no declaration predicts.
    Only `roster` is optional in this function's signature: a caller with no
    resolved roster (`_check_contrasts` is called directly by tests) still gets
    every declaration-only check, and skips only the one that needs units.

    **The shape is checked here too, and it has to be.** `resolve_contrasts`
    reads `entry["of"]` and `entry.get("id")` off whatever the list holds, and
    its comment leans on this function having refused anything that would make
    those raise; before this block was un-refused, nothing could reach it at
    all. So a non-list `contrasts`, an entry that is not a mapping (a bare list
    of condition labels is the plausible slip), and a missing or non-string
    `id` are all `E-STATS-CONTRAST-SHAPE` rather than an `AttributeError` out
    of `run` or the literal string `'None'` published as a contrast's name,
    where two such entries would collide.

    **The two sides must be distinct** (`reference.md` § Validation, "Contrast
    has two distinct sides"), checked only once both resolve so the diagnostic
    for a typo stays the more specific `E-STATS-CONTRAST-UNKNOWN`. A condition
    compared with itself is a perfect null with a zero-width interval over
    every unit, published as a finding and occupying a slot in the correction
    family.
    """
    entries = ((doc.get("statistics") or {}).get("contrasts")) or []
    if not entries:
        return
    if not isinstance(entries, list):
        c.error(
            "E-STATS-CONTRAST-SHAPE",
            "statistics.contrasts",
            "is not a list of contrast entries; each entry is a mapping with `id`, `of` and "
            "`against`",
        )
        return

    # `isinstance(..., str)` before the value enters a `set`, for the reason the
    # `of`/`against` loop below states: building a `set` hashes every element, so
    # an `id` holding a mapping or a list (one bad indent under `id:`) raised
    # `TypeError` out of `validate_config` here, before a single finding was
    # collected. A non-string `id` is not a name a contrast can be published
    # under, so dropping it from `ids` routes it to the missing-or-not-a-string
    # branch below rather than minting an identifier.
    ids = {
        entry["id"]
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
    }
    # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
    # `validate` collects findings and never raises. `_check_sweep` calls this
    # same pure function on this same doc one statement earlier and is *also*
    # guarded now, so a sweep malformed enough to make `expand` raise (a
    # `null` grid axis value, past `_check_shape`'s per-axis `list` guard) no
    # longer crashes there first — meaning this guard is genuinely reachable
    # through `validate_config` too, not only from a caller that reaches
    # `_check_contrasts` directly. Kept regardless of that overlap, on the
    # same reasoning the `isinstance(entries, list)` guard just above was kept
    # once `_check_shape` started covering its shape first: two guards on the
    # same pure call is deliberate belt-and-braces, not redundancy to delete —
    # a caller that reaches `_check_contrasts` directly, skipping
    # `_check_sweep` entirely (`test_check_contrasts_guards_expand_when_called_directly`
    # does exactly this), still needs its own guard, and a future change that
    # reopens `_check_sweep`'s crash must not silently reopen this one too.
    # `conditions = []` rather than returning:
    # the shape and `id`-collision checks below don't need a resolved sweep at
    # all, and every `of`/`against` correctly reports `E-STATS-CONTRAST-UNKNOWN`
    # against an empty `labels` rather than the block going silently unchecked.
    try:
        conditions = expand(doc)
    except Exception:
        conditions = []
    labels = {cond.label for cond in conditions if cond.label is not None}
    # Same reasoning as `_check_report_by`'s `declared` set: a non-string item in
    # `data.units.attributes` is `_check_units`'s finding to make, not this
    # function's, but `set(...)` over the raw list would crash on it first.
    declared_attrs = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    seen_ids: set[str] = set()
    # The same guard `_check_report_by` puts on its own floor, for the same
    # reason: `check_envelope` is what REPORTS a wrong-typed `min_reported_n`
    # (`E-CONFIG-TYPE`), a leaf fault is deliberately non-fatal, so this function
    # still runs on a doc holding a `str` floor and `len(matched) < floor` would
    # raise `TypeError`. `bool` is excluded explicitly because `isinstance(True,
    # int)` is `True`, and a value the envelope already flagged must not also
    # drive a warning nobody can act on ("below limits.min_reported_n (True)").
    raw_floor = (doc.get("limits") or {}).get("min_reported_n")
    floor: float | None = (
        raw_floor
        if not isinstance(raw_floor, bool) and isinstance(raw_floor, (int, float))
        else None
    )

    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}]",
                f"is {type(entry).__name__}, not a mapping with `id`, `of` and `against` — a "
                "list of condition labels is not a list of contrasts",
            )
            continue
        # The second site that hashes `id`: `in seen_ids` raises for an
        # unhashable value exactly as the `ids` construction above did, so the
        # `isinstance` guard has to come first here too. A non-string `id` is
        # never a repeat of anything — it gets the shape error below instead.
        raw_id = entry.get("id")
        is_named = isinstance(raw_id, str) and raw_id
        if is_named and raw_id in seen_ids:
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}].id",
                f"repeats `{raw_id}`, which an earlier entry already uses; two "
                "contrasts under one name are indistinguishable in `results.contrasts` and "
                "in a hypothesis naming it",
            )
        elif is_named:
            seen_ids.add(entry["id"])
        if not is_named:
            c.error(
                "E-STATS-CONTRAST-SHAPE",
                f"statistics.contrasts[{i}].id",
                "is missing or not a string; `id` is how the contrast is named in "
                "`results.contrasts` and in a hypothesis, so two entries cannot share one",
            )
        for field in ("of", "against"):
            value = entry.get(field)
            where = f"statistics.contrasts[{i}].{field}"
            # `isinstance` before either membership test, the same guard
            # `E-STATS-CORRECTION-UNKNOWN` uses above: `in` on `ids`/`labels` (both
            # `set`s) raises `TypeError` for an unhashable `value` (a `list` or a
            # `dict`), and `and`/`not (... and ...)` short-circuits before that ever
            # runs. A non-string `of`/`against` is simply not a condition's label,
            # so it falls into the same `E-STATS-CONTRAST-UNKNOWN` branch a
            # resolvable-but-wrong string would.
            if isinstance(value, str) and value in ids and value not in labels:
                c.error(
                    "E-STATS-CONTRAST-NESTED",
                    where,
                    f"names `{value}`, which is another contrast's `id` — contrasts compare "
                    "conditions and do not nest. A comparison between two contrasts (a "
                    "dose-response ordering, a difference-in-differences, a nested mean over "
                    "cells) is an interaction, and stays a `summary`-step `Estimate` rather "
                    "than a declared contrast",
                )
            elif not (isinstance(value, str) and value in labels):
                c.error(
                    "E-STATS-CONTRAST-UNKNOWN",
                    where,
                    f"names `{value!r}`, which no condition's label matches",
                )
        of_value = entry.get("of")
        if isinstance(of_value, str) and of_value in labels and of_value == entry.get("against"):
            c.error(
                "E-STATS-CONTRAST-SAME-SIDES",
                f"statistics.contrasts[{i}]",
                f"sets `of` and `against` to the same condition (`{entry.get('of')}`); a "
                "contrast has two distinct sides. Comparing a condition with itself publishes "
                "a perfect null over every unit as a finding, and it joins the correction "
                "family, tightening every other interval in the run",
            )
        within = entry.get("within")
        if isinstance(within, dict):
            unknown = False
            for name in within:
                if name not in declared_attrs:
                    unknown = True
                    c.error(
                        "E-STATS-CONTRAST-WITHIN",
                        f"statistics.contrasts[{i}].within",
                        f"names `{name}`, which is not in `data.units.attributes`",
                    )
            # Skipped for a stratum already refused above, the way
            # `_check_report_by` skips a level of an attribute it just refused:
            # an unknown attribute matches no unit, so counting it would report
            # a thin stratum as well as an undeclared one for a single typo.
            if not unknown and within and roster is not None and floor is not None:
                matched = units_matching(roster, within) or set()
                if len(matched) < floor:
                    stratum = ", ".join(f"`{k}={v}`" for k, v in sorted(within.items()))
                    c.warn(
                        "W-STATS-CONTRAST-THIN",
                        f"statistics.contrasts[{i}].within",
                        f"selects {stratum}, which {len(matched)} of {len(roster)} units "
                        f"match, below limits.min_reported_n ({floor}). The run counts "
                        f"`n_paired` over the two sides' completed units, which attrition "
                        f"can only make smaller",
                    )


_DIRECTIONS = ("greater", "less")
_EVALUATE_ONS = ("observed", "ci95_lower", "ci95_upper")
_KINDS = ("confirmatory", "exploratory")


def _condition_labels(doc: dict[str, Any]) -> tuple[set[str], set[str]] | None:
    """Every declared condition label, and the baseline's own, or `None`.

    `None` means the sweep block is malformed badly enough that `expand` cannot
    read it — a scalar where an axis's value list belongs, a non-mapping
    `baseline`. `_check_sweep` is the check that reports those, and this module
    collects rather than raises, so an unexpandable sweep silently skips the
    label test instead of turning one bad indent into a traceback.
    """
    try:
        conditions = expand(doc)
    except Exception:
        return None
    labels = {cond.label for cond in conditions if cond.label is not None}
    baselines = {cond.label for cond in conditions if cond.label is not None and cond.is_baseline}
    return labels, baselines


def _check_hypotheses(
    doc: dict[str, Any], c: Collector, experiment: Any | None, template: Any
) -> None:
    """Each declared `hypotheses` entry, checked for real now that the block is
    non-empty and list-shaped (`_check_shape` already refused anything else).

    **`metric` names the quantity under test, and `compare` only ever says
    *where*.** `reference.md` § Pre-registration: "`metric` is required in every
    form, because `compare` says *where* and never *what*." A contrast or a
    condition comparison reports one value per step metric exactly as a summary
    step does, so a hypothesis that names only `compare` leaves the quantity
    unstated — `E-HYPOTHESIS-METRIC`. A `metric` naming a step this experiment's
    `steps` list does not declare is the same failure by a different route: the
    string looks like it names something, but nothing in the run will ever
    produce it, so it is refused under the same identifier rather than a third
    one — there being no experiment to check against (its import already failed,
    reported elsewhere as `E-ENTRYPOINT-IMPORT`) is not a hypothesis fault, so
    that case is silently skipped rather than double-reported.

    **`compare.to: baseline` needs a declared baseline — and so does a bare
    `compare.condition` with no `to` at all, because `hypotheses.resolve` reads
    `compare.condition` as a baseline comparison whether or not `to` spells it
    out.** `reference.md` § Validation, "Hypothesis needs baseline":
    `hypotheses[0].compare.to: baseline` but `sweep.baseline` is not declared.
    Nothing downstream guards this — `hypotheses.resolve` reads `vs_baseline`,
    which `cli` never populates without a declared baseline, so the hypothesis
    would silently resolve to no observation rather than being refused before a
    run starts. The same gap exists one form earlier: `compare: {condition: X}`
    with neither `to: baseline` nor a declared `sweep.baseline` used to fire
    neither this check (no `to` to read) nor `E-HYPOTHESIS-CONDITION` (the label
    can resolve just fine), so it validated clean while naming a condition and
    nothing to compare it against — `reference.md` § Pre-registration's ruling
    is to refuse that form rather than default the missing side to baseline, so
    `E-HYPOTHESIS-BASELINE`'s condition is widened to `to == "baseline"` *or*
    (`condition` present, `to` absent, and `contrast` absent too) — the last
    exclusion because `hypotheses.resolve` checks `"contrast" in compare` first
    and returns from that branch without ever reading `condition`, so a
    `{contrast: x, condition: y}` hypothesis resolves through the contrast and
    needs no baseline at all — rather than minting a second code for one fault
    that is the same fault under a different spelling.
    `E-HYPOTHESIS-BASELINE`.

    **`compare.to` has exactly one value, and it is `baseline`.**
    `reference.md` § Pre-registration writes `to: baseline` and core computes
    no other per-condition comparison — a claim against some *other* condition
    is a `statistics.contrasts` entry, named through `compare.contrast`. Left
    unchecked, `to: some_other_label` validates clean and
    `hypotheses.resolve` — which never reads the field — evaluates it against
    the baseline anyway, so the verdict answers a question the config did not
    ask and nothing in the record reveals the substitution.
    `E-HYPOTHESIS-COMPARE-TO`.

    **`compare.contrast` needs a real contrast.** `reference.md` § Validation,
    "Hypothesis names a real contrast": `hypotheses[1].compare.contrast` is
    `invariance`, which `statistics.contrasts` does not declare. The same
    unresolvable-label class `_check_contrasts` already refuses for `of` and
    `against` — a typo here would resolve to nothing in `hypotheses.resolve`
    and read back `block=None`, reported but never diagnosed as a typo.
    `E-HYPOTHESIS-CONTRAST`.

    **`evaluate_on` needs a bound that can exist.** `reference.md` §
    Validation, "Hypothesis bound exists": `evaluate_on` names a bound
    (`ci95_lower`/`ci95_upper`), but no metric this run computes could ever
    carry an interval — `data.units` undeclared *and* the template defines no
    `aggregate`, which together are the only way a `basis: units` metric with
    a `ci95` gets produced at all. `generic`, the only template this build
    registers, does not override `BaseTemplate.aggregate` — it inherits the
    `{}`-returning default — so the `aggregate`-half of this condition holds
    for every config naming it; `data.units` presence is what discriminates.

    **That two-condition test is `reference.md`'s own — "the config-level
    form" — and this check adds one more gate on top of it, not a divergence
    from it.** § What a hypothesis is tested against draws the line itself:
    "`validate` catches the config-level form of that, where nothing in the
    run could carry an interval; the per-metric form is settled when the step
    returns." The Validation row's own wording is "no metric this run
    *computes*" — and CLAUDE.md's own invariant is explicit that "the one
    interval core stores *without computing* is an `Estimate` returned by a
    `summary` step"; a `reported: true` `Estimate` a step supplies directly
    ("A hypothesis may name a summary metric") is therefore outside what that
    row is even about, not an exception carved into it. Core never inspects a
    step's body to know whether *this* summary step actually returns one, so
    the check below only fires when the metric's scope is affirmatively known
    and is not `"summary"` — unknown (no experiment, or a `metric` that
    doesn't parse) is treated the same as `"summary"`, conservatively, since
    the check can rule out neither. `E-HYPOTHESIS-BOUND`.

    **The same impossible-interval condition, without a bound requested, is a
    warning rather than a refusal — and shares the same scope gate, for the
    warning's own reason rather than the error's.** `reference.md` §
    Validation, "Hypothesis has an inference base": every metric will be
    `basis: repeats` — reportable (`evaluate_on: observed` still reads a
    value) but not testable against an interval. That premise is false for a
    `scope: "summary"` metric that turns out to be a reported `Estimate`: it
    is neither `basis: repeats` nor untestable — it is `reported`, carries its
    own interval, and is exactly what `evaluate_on: ci95_lower`/`ci95_upper`
    can test. (The error's hard-stop argument — `command_run` treats
    `E-HYPOTHESIS-BOUND` as `c.has_errors` and a warning never stops a run —
    does not transfer to the warning and is not why this one is gated; a
    warning it wrongly issued would cost nothing but a false alarm, so the
    gate here is justified only by the premise being false, the same way it
    is for the error.) `W-HYPOTHESIS-INFERENCE-BASE` fires exactly where
    `E-HYPOTHESIS-BOUND` does not, under that shared gate: same condition,
    `evaluate_on` absent or `observed` instead of a bound.

    **A hypothesis's form must match its metric's scope.** `reference.md` § What
    a hypothesis is tested against: a `scope: "summary"` metric "is one value
    per run, not a contrast between conditions" and takes no `compare`, while a
    `condition`- or `repeat`-scoped metric only exists per condition and "is the
    same mistake inverted" without one. Both directions are `E-HYPOTHESIS-FORM`.

    **`direction` and `evaluate_on` are closed vocabularies, refused here rather
    than reaching the evaluator at all.** The two fields are not symmetric in
    what happens if this check didn't exist. `hypotheses.py::verdict_for` already
    guards `direction`: `supported` is set only when `direction in ("greater",
    "less")`, so an out-of-vocabulary value (Task 4's review found `greatr`) gets
    `supported: None` rather than a wrong verdict — the refusal here is a second,
    earlier line of defence, so a mistyped `direction` never even reaches a real
    run, rather than being caught only after one. `evaluate_on` has no such
    guard: `_tested_number` reads `evaluate_on == "observed"` and, failing that,
    `evaluate_on == "ci95_lower"` — anything else, including a typo of either
    string, silently falls through to `ci95_upper` and both fields go on to
    build a genuinely different verdict, with nothing in the record to reveal
    that the value was never recognized. So `E-HYPOTHESIS-EVALUATE-ON` is closing
    a live, currently-unguarded misread; `E-HYPOTHESIS-DIRECTION` is moving an
    already-guarded one earlier. `direction` has no named enum anywhere in the
    four documents; `evaluate_on`'s is documented
    (`observed | ci95_lower | ci95_upper`) but no identifier existed for either.

    **`kind`, `direction` and `threshold` are required, not merely constrained.**
    `reference.md` § The one config file writes all three in every hypothesis and
    gives a default for none of them, and each has a different silent
    consequence when absent. `kind` is the worst: `hypotheses._is_counted` tests
    `== "confirmatory"`, so an omitted or mistyped `kind` leaves the correction
    family and the verdict is decided on the *raw* — tighter — bound, over-
    supporting a claim that the corrected level would have refused, with the
    record echoing the typo but no diagnostic anywhere. `direction` and
    `threshold` fail the other way, honestly but expensively: `verdict_for`
    returns `supported: None` and the run comes back with no verdict after the
    compute is spent. So `direction`'s check drops its `is not None` guard and
    `E-HYPOTHESIS-KIND` and `E-HYPOTHESIS-THRESHOLD` join it. `evaluate_on`
    stays optional, because `observed` is a documented default rather than an
    omission.

    **`compare.condition` is resolved against the declared labels**, the job
    `_check_contrasts` already does for `of`/`against` with the same `expand(doc)`
    machinery. A typo'd label validated clean and came back `observed: null,
    supported: null`; so did naming the baseline's own label, which
    `vs_baseline` has no entry for by construction. Both are
    `E-HYPOTHESIS-CONDITION`.
    """
    entries = doc.get("hypotheses")
    if not isinstance(entries, list) or not entries:
        return  # `_check_shape` already refused a bad shape; `[]` is not a declaration

    scopes_by_step: dict[str, str] = {}
    if experiment is not None:
        scopes_by_step = {_step_name(cls): cls.scope for cls in experiment.steps}

    has_baseline = bool((doc.get("sweep") or {}).get("baseline"))
    labels = _condition_labels(doc)
    contrast_entries = ((doc.get("statistics") or {}).get("contrasts")) or []
    contrast_ids = (
        {
            entry["id"]
            for entry in contrast_entries
            if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
        }
        if isinstance(contrast_entries, list)
        else set()
    )
    # The bound-exists error and the inference-base warning share one condition:
    # no metric this run computes could ever carry an interval, because that
    # needs a `basis: units` metric and the only source of one is a resolved
    # unit table run through a template's `aggregate`. `generic` — the only
    # template this build registers — inherits `BaseTemplate.aggregate`'s
    # `{}`-returning default rather than overriding it, so `data.units` is what
    # discriminates in practice; the `type(...) is not BaseTemplate.aggregate`
    # check is what would let a future template with a real `aggregate` clear
    # this condition without either check changing.
    no_interval_possible = (
        not bool((doc.get("data") or {}).get("units"))
        and type(template).aggregate is BaseTemplate.aggregate
    )

    for i, hyp in enumerate(entries):
        if not isinstance(hyp, dict):
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}]",
                f"is a {type(hyp).__name__}, not a mapping with `metric`, `direction` and "
                "`threshold`",
            )
            continue

        kind = hyp.get("kind")
        if kind not in _KINDS:
            c.error(
                "E-HYPOTHESIS-KIND",
                f"hypotheses[{i}].kind",
                f"is `{kind}`; the only kinds are `confirmatory` and `exploratory`, and "
                "there is no default — `hypotheses.evaluate` counts a hypothesis into the "
                "correction family only when `kind` is exactly `confirmatory`, so a typo or "
                "an omission drops a pre-registered claim out of its family and decides it "
                "on the raw, tighter bound instead of the corrected one",
            )

        direction = hyp.get("direction")
        if direction not in _DIRECTIONS:
            c.error(
                "E-HYPOTHESIS-DIRECTION",
                f"hypotheses[{i}].direction",
                f"is `{direction}`; the only directions are `greater` and `less`, and it is "
                "required — the evaluator refuses to guess by returning `supported: None` "
                "for anything else, so a mistyped or missing direction otherwise reaches a "
                "full run and comes back with no verdict rather than being refused before "
                "one starts",
            )

        threshold = hyp.get("threshold")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            c.error(
                "E-HYPOTHESIS-THRESHOLD",
                f"hypotheses[{i}].threshold",
                f"is `{threshold}`; a hypothesis is one quantity against one numeric "
                "threshold, and `verdict_for` compares against nothing else — a missing or "
                "non-numeric threshold yields `supported: null` after the whole run is "
                "spent, with nothing in the record saying why",
            )

        evaluate_on = hyp.get("evaluate_on")
        if evaluate_on is not None and evaluate_on not in _EVALUATE_ONS:
            c.error(
                "E-HYPOTHESIS-EVALUATE-ON",
                f"hypotheses[{i}].evaluate_on",
                f"is `{evaluate_on}`; the only values are `observed`, `ci95_lower` and "
                "`ci95_upper` — unlike `direction`, the evaluator has no guard for this one "
                "and silently reads anything else as `ci95_upper`, so a typo changes which "
                "bound the verdict is about rather than being caught anywhere",
            )

        compare = hyp.get("compare")
        if isinstance(compare, dict):
            if "to" in compare and compare.get("to") != "baseline":
                c.error(
                    "E-HYPOTHESIS-COMPARE-TO",
                    f"hypotheses[{i}].compare.to",
                    f"is `{compare.get('to')}`; the only value is `baseline` — core computes "
                    "no other per-condition comparison, and `hypotheses.resolve` reads the "
                    "baseline block whatever this says, so any other value names a "
                    "comparison that will never be made and is silently evaluated against "
                    "the baseline instead",
                )
            # `to: baseline` is the ordinary spelling, but `hypotheses.resolve`
            # reads `compare.condition` as a baseline comparison whether or not
            # `to` says so — so a bare `{condition: X}` implies the same
            # comparison `to: baseline` spells out, and needs the same declared
            # baseline. Without this second branch, that bare form fired neither
            # this check (no `to` to read) nor `E-HYPOTHESIS-CONDITION` (the
            # label can resolve just fine), and validated clean while naming a
            # condition and nothing to compare it against.
            #
            # Excludes `contrast in compare`: `resolve` checks `"contrast" in
            # compare` first and returns from that branch without ever reading
            # `condition` — so `{contrast: x, condition: y}` resolves through the
            # contrast, not the baseline, and needs no baseline at all. Without
            # this exclusion, a hypothesis that names both would be refused for a
            # comparison it was never going to make.
            implies_baseline = compare.get("to") == "baseline" or (
                "condition" in compare and "to" not in compare and "contrast" not in compare
            )
            missing_baseline = implies_baseline and not has_baseline
            if missing_baseline:
                if "to" in compare:
                    detail = "sets `to: baseline`, but `sweep.baseline` is not declared"
                else:
                    detail = (
                        "names `condition` with no `to` and no declared `sweep.baseline` — "
                        "a `compare` names both sides of the comparison, and `to: baseline` "
                        "is the ordinary spelling of the side this is missing"
                    )
                c.error(
                    "E-HYPOTHESIS-BASELINE",
                    f"hypotheses[{i}].compare",
                    f"{detail} — nothing populates a baseline comparison without one, so this "
                    "hypothesis would silently resolve to no observation rather than the "
                    "comparison it names",
                )
            # Gated on `missing_baseline` so one fault gets one code: with no
            # declared baseline there is no comparison for *any* label to name,
            # and `E-HYPOTHESIS-BASELINE` above already says so — reporting the
            # label as unknown too would be the double-report the dotless-metric
            # ordering fix exists to avoid.
            if "condition" in compare and not missing_baseline and labels is not None:
                declared_labels, baseline_labels = labels
                named = compare.get("condition")
                if not isinstance(named, str) or named not in declared_labels:
                    c.error(
                        "E-HYPOTHESIS-CONDITION",
                        f"hypotheses[{i}].compare.condition",
                        f"names `{named!r}`, which is not a condition this run's `sweep` "
                        "declares — `hypotheses.resolve` looks the label up and finds "
                        "nothing, so the verdict comes back `observed: null, supported: "
                        "null` after the whole run is spent, exactly the unresolvable-label "
                        "class `E-STATS-CONTRAST-UNKNOWN` refuses for a contrast's sides",
                    )
                elif named in baseline_labels:
                    c.error(
                        "E-HYPOTHESIS-CONDITION",
                        f"hypotheses[{i}].compare.condition",
                        f"names `{named}`, which is the baseline itself — `vs_baseline` holds "
                        "one entry per *other* condition, because a baseline has no "
                        "comparison against itself, so this resolves to no observation",
                    )
            if "contrast" in compare:
                contrast_id = compare.get("contrast")
                if not isinstance(contrast_id, str) or contrast_id not in contrast_ids:
                    c.error(
                        "E-HYPOTHESIS-CONTRAST",
                        f"hypotheses[{i}].compare.contrast",
                        f"names `{contrast_id!r}`, which `statistics.contrasts` does not declare",
                    )

        metric = hyp.get("metric")
        step, _, name = metric.partition(".") if isinstance(metric, str) else ("", "", "")
        metric_is_well_formed = isinstance(metric, str) and bool(metric) and bool(name)

        # A `scope: "summary"` metric can be a `reported: true` `Estimate` a step
        # supplies directly (`reference.md` § What a hypothesis is tested
        # against, "A hypothesis may name a summary metric") — its own real
        # `ci95`, with no unit table involved, and it is itself the answer to
        # `basis: repeats`'s "reportable but not testable": a reported `Estimate`
        # is neither `basis: repeats` nor untestable, so the warning's own
        # premise is false for one, and the error's "no metric ... could carry
        # an interval" is false for one too. Core never inspects a step's body
        # to know whether *this* summary step actually returns one, so both
        # checks below fire only when the metric's scope is affirmatively known
        # and is *not* `"summary"` — unknown (no experiment) is treated the same
        # as `"summary"`, conservatively. A `condition`- or `repeat`-scoped
        # metric has no such exception: its only possible interval is `basis:
        # units`, derived from `data.units` through a template's `aggregate`,
        # which `no_interval_possible` already covers in full.
        #
        # Gated on `metric_is_well_formed` too, and deliberately checked before
        # the malformed-metric refusal just below: a `metric` that doesn't parse
        # to `step.metric` names no scope to look up, and `step` alone (a
        # dotless value) can still collide with a real step name, which would
        # otherwise let this block read a real `scope` for a metric that is
        # about to be refused anyway — reporting the same entry under two
        # unrelated codes rather than the one `E-HYPOTHESIS-METRIC` fault it
        # actually has.
        if metric_is_well_formed:
            scope = scopes_by_step.get(step) if step else None
            if no_interval_possible and scope not in (None, "summary"):
                if evaluate_on in ("ci95_lower", "ci95_upper"):
                    c.error(
                        "E-HYPOTHESIS-BOUND",
                        f"hypotheses[{i}].evaluate_on",
                        f"names `{evaluate_on}`, but no metric this run computes could carry "
                        "an interval — `data.units` is undeclared and the template defines no "
                        "`aggregate`, so nothing produces a `ci95` to evaluate a bound against",
                    )
                else:
                    c.warn(
                        "W-HYPOTHESIS-INFERENCE-BASE",
                        f"hypotheses[{i}]",
                        "names a metric under a run where `data.units` is undeclared and the "
                        "template defines no `aggregate` — every metric will be `basis: "
                        "repeats`, reportable but not testable against an interval",
                    )

        if not metric_is_well_formed:
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}].metric",
                "is missing or not a `step.metric` string; `compare` says where a "
                "hypothesis is tested and never what, so a contrast or condition "
                "comparison alone leaves the quantity under test unnamed",
            )
            continue

        if experiment is None:
            continue  # the entrypoint didn't import; no step list to check the form against

        scope = scopes_by_step.get(step)
        if scope is None:
            c.error(
                "E-HYPOTHESIS-METRIC",
                f"hypotheses[{i}].metric",
                f"names step `{step}`, which the entrypoint's `steps` list does not declare",
            )
            continue

        has_compare = isinstance(hyp.get("compare"), dict)
        if scope == "summary" and has_compare:
            c.error(
                "E-HYPOTHESIS-FORM",
                f"hypotheses[{i}]",
                f'names `{metric}`, a `scope: "summary"` metric, and declares `compare` — '
                "a summary metric is one value per run, not a contrast between conditions",
            )
        elif scope != "summary" and not has_compare:
            c.error(
                "E-HYPOTHESIS-FORM",
                f"hypotheses[{i}]",
                f'names `{metric}`, a `scope: "{scope}"` metric, without declaring `compare` '
                "— that quantity only exists per condition, so the hypothesis must say which "
                "conditions it compares",
            )


def _check_report_by(doc: dict[str, Any], c: Collector, roster: UnitList | None) -> None:
    """Each `statistics.report_by` attribute, checked against the declared ones,
    then against the roster for a level too thin to disclose.

    `reference.md` § Reporting strata: "validate rejects a `report_by` attribute
    that isn't declared in `data.units.attributes`". The reason is the same one
    `E-STATS-CONTRAST-WITHIN` exists for: `strata.levels_for` reads the attribute
    with `.get`, which returns `None` for a typo exactly as it would for an
    attribute no unit carries, so the two are indistinguishable downstream — the
    record would hold no `by` block and never say why.

    A non-string entry is refused under the same code rather than reaching the
    set membership test below, where an unhashable one would raise out of a
    module whose contract is that it collects.

    The thinness warning that follows counts over *resolved* units, which is all
    `validate` can see; attrition between here and a run is `W-STATS-STRATUM-THIN`'s
    job at run time.
    """
    entries = ((doc.get("statistics") or {}).get("report_by")) or []
    if not isinstance(entries, list):
        return  # `_check_shape` already refused it, and returned early
    # A non-string item in `data.units.attributes` is `_check_units`'s own
    # finding to make (`E-UNITS-ATTR-MISSING`), not this function's — but
    # `set(...)` over the raw list would still crash on it before that finding
    # is ever reached (`TypeError: unhashable type` for a list or dict item).
    # Filtering to strings here just means a non-string item is treated as "not
    # declared", which is already true of it regardless.
    declared = {
        a
        for a in (((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
        if isinstance(a, str)
    }
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-REPORTBY-UNKNOWN",
                f"statistics.report_by[{i}]",
                f"names `{name}`, which is not in `data.units.attributes`",
            )

    floor = (doc.get("limits") or {}).get("min_reported_n")
    # `check_envelope` is what REPORTS a wrong-typed `floor` (E-CONFIG-TYPE) —
    # this guard exists because this function may be reached without it having
    # run: a leaf fault is deliberately non-fatal, so `_check_report_by` still
    # runs on a still-malformed `doc`, and `len(keys) < floor` below would raise
    # `TypeError` comparing an `int` to a `str`. `bool` is excluded explicitly,
    # the same rule as the budget guard above: `isinstance(True, (int, float))`
    # is `True` in Python, and a value already flagged wrong-typed by the
    # envelope must not also drive this check — whether or not the result
    # would be visibly wrong. (Here it happens not to be: every level in
    # `levels_for` holds at least one unit, so `len(keys) < floor` can never
    # hold for `floor` coerced to `0` or `1` either. The exclusion still
    # belongs here, on the same principle as the budget guard, rather than
    # relying on that being true forever.)
    if roster is None or isinstance(floor, bool) or not isinstance(floor, (int, float)):
        return
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            continue  # already refused above
        for level, keys in sorted(levels_for(roster, name).items()):
            if len(keys) < floor:
                c.warn(
                    "W-STATS-REPORTBY-THIN",
                    f"statistics.report_by[{i}]",
                    f"level `{level}` of `{name}` would hold {len(keys)} of "
                    f"{len(roster)} units, below limits.min_reported_n ({floor})",
                )

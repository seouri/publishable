"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import re
from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.manifest import POLICIES
from publishable.materialize import TEMPLATE_VERSION
from publishable.param import MISSING
from publishable.provenance import find_repo_root, resolves_inside_repo
from publishable.sweep import check_swept_value, expand
from publishable.templates.registry import get_template, template_names
from publishable.units import resolve_units

REQUIRED_METADATA = ("description", "authors")

# The shape of every top-level block, checked once before any `_check_*` reads one —
# a property of the config format, not of whichever check happens to read a block
# first. `statistics`, `limits`, and `hypotheses` are included even though nothing
# reads them yet in this build, so the next reader inherits the guard rather than
# the crash a hand-edited config would otherwise produce.
_MAPPING_BLOCKS = (
    "metadata", "data", "parameters", "sweep", "replication", "statistics", "limits",
)
_LIST_BLOCKS = ("hypotheses",)
_STRING_BLOCKS = ("schema_version", "experiment_type", "template_version", "entrypoint", "plugin")

_KIND_LABEL = {"mapping": "a mapping", "list": "a list", "string": "a string"}


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

    replication = doc.get("replication")
    if isinstance(replication, dict):
        repeats = replication.get("repeats")
        if repeats is not None and not isinstance(repeats, list):
            _bad("replication.repeats", repeats, "list")
        elif isinstance(repeats, list):
            for i, level in enumerate(repeats):
                if not isinstance(level, dict):
                    _bad(f"replication.repeats[{i}]", level, "mapping")

    return ok


def validate_config(config_path: Path, c: Collector) -> dict[str, Any] | None:
    try:
        doc = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        c.error("E-CONFIG-PARSE", str(config_path), f"does not parse: {exc}")
        return None
    if not isinstance(doc, dict):
        c.error("E-CONFIG-PARSE", str(config_path), "does not parse as a mapping")
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

    _check_metadata(doc, config_path, template, c)
    _check_entrypoint(doc, c)
    _check_parameters(doc, template, c)
    _check_versions(doc, c)
    _check_data(doc, config_path, c)
    _check_units(doc, c)
    _check_replication(doc, template, c)
    _check_unimplemented(doc, c)
    _check_sweep(doc, template, c)
    for message in template.validate(doc):
        c.error("E-TEMPLATE-RULE", "parameters", message)
    return doc


def _check_metadata(doc: dict[str, Any], config_path: Path, template: Any, c: Collector) -> None:
    metadata = doc.get("metadata") or {}
    for field in REQUIRED_METADATA:
        if not metadata.get(field):
            c.error("E-META-REQUIRED", f"metadata.{field}", "is empty, and is required")
    name = metadata.get("name", "")
    if name and not re.match(template.naming_pattern, name):
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


def _check_versions(doc: dict[str, Any], c: Collector) -> None:
    declared = doc.get("template_version")
    if declared and declared != TEMPLATE_VERSION:
        c.warn(
            "W-TEMPLATE-VERSION",
            "template_version",
            f"is {declared} but the installed template reports {TEMPLATE_VERSION}",
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
    if input_dir:
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


def _check_units(doc: dict[str, Any], c: Collector) -> None:
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
    """
    data = doc.get("data") or {}
    units_decl = _units_declaration(data, c)
    if units_decl is None:
        return
    input_dir = data.get("input_dir")
    if not input_dir:
        return  # E-DATA-REQUIRED already reported by _check_data
    path = Path(input_dir).expanduser()
    if not path.is_absolute() or not path.is_dir() or not any(path.iterdir()):
        return  # E-DATA-NOT-ABSOLUTE / E-DATA-UNREADABLE already reported by _check_data
    source = units_decl.get("from")
    if isinstance(source, dict) and "resolver" in source:
        return  # E-DATA-RESOLVER-UNSUPPORTED already reported by _check_unimplemented
    try:
        resolve_units(units_decl, path)
    except ContractError as exc:
        c.error(exc.code, "data.units", str(exc))


def _check_replication(doc: dict[str, Any], template: Any, c: Collector) -> None:
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
    any_invalid = False
    for level in levels:
        # `or` would read a declared 0 as "absent" and silently substitute 1,
        # which is the difference between warning about an empty design and not.
        count = level.get("n")
        if count is None:
            count = level.get("k")
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
    if total < template.default_repeats:
        c.warn(
            "W-REPL-FLOOR",
            "replication.repeats",
            f"total of {total} is below this convention class's default of "
            f"{template.default_repeats}",
        )


def _check_unimplemented(doc: dict[str, Any], c: Collector) -> None:
    """Declared-but-unimplemented blocks, refused rather than silently ignored.

    This build expands `sweep.baseline` and `sweep.grid` only, and executes
    repeats `as_declared` regardless of what is written here. `sweep.paired`,
    `.ablate`, `.sample`, and `.groups` are read by nothing yet. It resolves a
    unit roster, but several `data.units` sub-fields — allocation other than
    `within`, `assign`, `cluster_by`, `weight_by`, `measurements`, `holdout`,
    and a `resolver` source — are read by nothing yet either. Each of these
    would otherwise validate clean and then run something other than what the
    config describes — the exact failure `E-REPL-KIND-UNSUPPORTED` already
    refuses for `batch`/`fold`/nested repeat levels. Each message says plainly
    that the block is honored in a later slice, so a user does not read this as
    their config being malformed.
    """
    sweep = doc.get("sweep") or {}
    for mode, code, why in (
        ("paired", "E-SWEEP-PAIRED-UNSUPPORTED", "couples parameters into one axis"),
        (
            "ablate",
            "E-SWEEP-ABLATE-UNSUPPORTED",
            "emits 1 + n one-change conditions and reads the baseline rather than "
            "re-emitting it",
        ),
        (
            "sample",
            "E-SWEEP-SAMPLE-UNSUPPORTED",
            "draws continuous ranges and labels its conditions `NN_sample`",
        ),
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
                "expands `baseline` and `grid` only; the other modes will be honored in a "
                "later slice",
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

    order = (doc.get("replication") or {}).get("order")
    if order is not None and order != "as_declared":
        c.error(
            "E-REPL-ORDER-UNSUPPORTED",
            "replication.order",
            f"is `{order}`, which is specified but not implemented in this build — "
            "execution always proceeds as_declared regardless of what is declared here; "
            "`order` will be honored in a later slice",
        )


def _repeat_total(doc: dict[str, Any]) -> int:
    """The product of every repeat level's count, permissively: an invalid level
    (`n < 1`) is already reported by `_check_replication` under its own identifier,
    so this treats it as absent rather than reporting the same defect twice under
    `W-EXEC-BUDGET`.
    """
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
    for level in levels:
        count = level.get("n")
        if count is None:
            count = level.get("k")
        if isinstance(count, int) and count >= 1:
            total *= count
    return total


def _check_sweep(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """Checks that only become reachable once a sweep actually expands: an
    unrecognised mode, an axis with nothing in it, a swept path the template
    doesn't declare, a value the spec itself rejects, a value that can't render
    into a condition label, the execution budget, and the multiplicity family
    an enumerated sweep creates. `sweep.expand` is the single source of the
    condition count — re-deriving it here is exactly the drift Task 4 was
    told not to reintroduce.
    """
    import difflib

    sweep = doc.get("sweep") or {}
    known = {"baseline", "grid", "paired", "ablate", "sample", "groups"}
    for key in sweep:
        if key not in known:
            near = difflib.get_close_matches(key, sorted(known), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-SWEEP-KEY-UNKNOWN",
                f"sweep.{key}",
                f"is not a sweep mode{hint} — `expand` understands only `baseline` and "
                "`grid` in this build, so an unrecognised key would expand to zero "
                "conditions and the run would execute nothing while reporting success",
            )

    grid = sweep.get("grid") or {}
    spec = template.parameter_spec
    for path, values in grid.items():
        if not values:
            c.error(
                "E-SWEEP-AXIS-EMPTY",
                f"sweep.grid.{path}",
                "declares no values, so the sweep expands to zero conditions and the run "
                "would execute nothing while reporting success",
            )
            continue
        if path not in spec:
            near = difflib.get_close_matches(path, list(spec), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            c.error(
                "E-SWEEP-PATH-UNKNOWN",
                f"sweep.grid.{path}",
                f"is not a parameter of this template{hint}",
            )
            continue
        for i, value in enumerate(values):
            problem = spec[path].check(value)
            if problem:
                c.error("E-PARAM-VALUE", f"sweep.grid.{path}[{i}]", problem)
            unnameable = check_swept_value(value)
            if unnameable:
                c.error("E-SWEEP-VALUE-UNNAMEABLE", f"sweep.grid.{path}[{i}]", unnameable)

    conditions = expand(doc)
    executions = len(conditions) * _repeat_total(doc)
    budget = (doc.get("limits") or {}).get("max_executions")
    if isinstance(budget, int) and executions > budget:
        c.warn(
            "W-EXEC-BUDGET",
            "limits.max_executions",
            f"{len(conditions)} conditions × {_repeat_total(doc)} repeats = {executions} "
            f"executions exceeds {budget}",
        )

    if len(conditions) > 1:
        c.warn(
            "W-STATS-FAMILY",
            "statistics.correction",
            f"{len(conditions)} conditions form a family of {len(conditions) - 1} baseline "
            "comparisons per metric, and multiplicity correction is not implemented in this "
            "build — every interval reported is uncorrected, and each records "
            "`correction: null` to say so",
        )

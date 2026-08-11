"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import re
from pathlib import Path
from typing import Any

import yaml

from publishable.base_experiment import load_experiment
from publishable.contrasts import resolve_contrasts
from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.manifest import POLICIES
from publishable.materialize import TEMPLATE_VERSION
from publishable.param import MISSING
from publishable.provenance import find_repo_root, resolves_inside_repo
from publishable.replication import resolve_repeats
from publishable.scope import step_name as _step_name
from publishable.strata import levels_for
from publishable.sweep import check_swept_value, expand
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
                if values is not None and not isinstance(values, list):
                    _bad(f"sweep.grid.{path}", values, "list")

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
    _check_versions(doc, c)
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
    _check_contrasts(doc, c)
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
    path = Path(input_dir).expanduser()
    if not path.is_absolute() or not path.is_dir() or not any(path.iterdir()):
        return None  # E-DATA-NOT-ABSOLUTE / E-DATA-UNREADABLE already reported by _check_data
    source = units_decl.get("from")
    if isinstance(source, dict) and "resolver" in source:
        return None  # E-DATA-RESOLVER-UNSUPPORTED already reported by _check_unimplemented
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
    if any(level.get("kind") == "fold" for level in levels) and not (
        doc.get("data") or {}
    ).get("units"):
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

    This build expands `sweep.baseline` and `sweep.grid` only. Both declared
    orders are honored — `randomized` shuffles within each batch and
    `as_declared` leaves the plan's step-major layout alone. `sweep.paired`,
    `.ablate`, `.sample`, and `.groups` are read by nothing yet. It resolves a
    unit roster, but several `data.units` sub-fields — allocation other than
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
        ("paired", "E-SWEEP-PAIRED-UNSUPPORTED", "couples parameters into one axis"),
        (
            "ablate",
            "E-SWEEP-ABLATE-UNSUPPORTED",
            "emits 1 + n one-change conditions and reads the baseline rather than re-emitting it",
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

    # A baseline that fixes only *some* of the grid's axes. `reference.md`:1415-1422
    # states one rule with two cases: the baseline expands over whichever axes it
    # does not fix, giving one baseline condition per cell of the unfixed axes.
    # `expand` emits exactly one `00_baseline` row carrying only what the baseline
    # literally names, so the declared design is not the executed design — the
    # failure every other refusal in this function exists to prevent. Per-cell
    # expansion is a real feature; until it lands, refuse rather than diverge.
    # A baseline fixing every declared axis (including the no-grid case) is the
    # supported row and is unaffected.
    baseline = sweep.get("baseline") or {}
    grid = sweep.get("grid") or {}
    unfixed = [path for path in grid if path not in baseline]
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

    conditions = expand(doc)
    if sweep and not conditions:
        c.error(
            "E-SWEEP-EXPANDS-EMPTY",
            "sweep",
            "expands to zero conditions, so the run would execute nothing while "
            "reporting success — declare `baseline`, a non-empty `grid`, or remove "
            "`sweep` entirely",
        )

    repeat_total = _repeat_total(doc, unit_count)
    budget = (doc.get("limits") or {}).get("max_executions")
    # `repeat_total` is `None` only when a declared count cannot be resolved at
    # all — a `k: all` whose roster did not resolve, or a string `k` that is not
    # `all` — see `_repeat_total`. Skipping the check rather than computing
    # against a guessed 1× is deliberate: an unknown total must not be reported
    # as a small one. A `k: all` over a roster that DID resolve is a real number
    # here, and warns like any other count.
    if repeat_total is not None and isinstance(budget, int):
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
            "`fdr_bh` adjusts p-values, and no comparison in this family will carry one "
            "(`statistics.null_test` is undeclared, and a parameter-axis contrast cannot "
            "supply one) — every `ci95_corrected` will be null. Use `holm` or `bonferroni`, "
            "whose corrections are interval-shaped",
        )


def _check_contrasts(doc: dict[str, Any], c: Collector) -> None:
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
    conditions = expand(doc)
    labels = {cond.label for cond in conditions if cond.label is not None}
    declared_attrs = set(((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
    seen_ids: set[str] = set()

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
            for name in within:
                if name not in declared_attrs:
                    c.error(
                        "E-STATS-CONTRAST-WITHIN",
                        f"statistics.contrasts[{i}].within",
                        f"names `{name}`, which is not in `data.units.attributes`",
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
    baselines = {
        cond.label for cond in conditions if cond.label is not None and cond.is_baseline
    }
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

    **`compare.to: baseline` needs a declared baseline.** `reference.md` §
    Validation, "Hypothesis needs baseline": `hypotheses[0].compare.to:
    baseline` but `sweep.baseline` is not declared. Nothing downstream guards
    this — `hypotheses.resolve` reads `vs_baseline`, which `cli` never
    populates without a declared baseline, so the hypothesis would silently
    resolve to no observation rather than being refused before a run starts.
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
    contrast_ids = {
        entry["id"]
        for entry in contrast_entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
    } if isinstance(contrast_entries, list) else set()
    # The bound-exists error and the inference-base warning share one condition:
    # no metric this run computes could ever carry an interval, because that
    # needs a `basis: units` metric and the only source of one is a resolved
    # unit table run through a template's `aggregate`. `generic` — the only
    # template this build registers — inherits `BaseTemplate.aggregate`'s
    # `{}`-returning default rather than overriding it, so `data.units` is what
    # discriminates in practice; the `type(...) is not BaseTemplate.aggregate`
    # check is what would let a future template with a real `aggregate` clear
    # this condition without either check changing.
    no_interval_possible = not bool(
        (doc.get("data") or {}).get("units")
    ) and type(template).aggregate is BaseTemplate.aggregate

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
            missing_baseline = compare.get("to") == "baseline" and not has_baseline
            if missing_baseline:
                c.error(
                    "E-HYPOTHESIS-BASELINE",
                    f"hypotheses[{i}].compare",
                    "sets `to: baseline`, but `sweep.baseline` is not declared — nothing "
                    "populates a baseline comparison without one, so this hypothesis would "
                    "silently resolve to no observation rather than the comparison it names",
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
                        f"names `{contrast_id!r}`, which `statistics.contrasts` does not "
                        "declare",
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
                f"names `{metric}`, a `scope: \"summary\"` metric, and declares `compare` — "
                "a summary metric is one value per run, not a contrast between conditions",
            )
        elif scope != "summary" and not has_compare:
            c.error(
                "E-HYPOTHESIS-FORM",
                f"hypotheses[{i}]",
                f"names `{metric}`, a `scope: \"{scope}\"` metric, without declaring `compare` "
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
    declared = set(((doc.get("data") or {}).get("units") or {}).get("attributes") or [])
    for i, name in enumerate(entries):
        if not isinstance(name, str) or name not in declared:
            c.error(
                "E-STATS-REPORTBY-UNKNOWN",
                f"statistics.report_by[{i}]",
                f"names `{name}`, which is not in `data.units.attributes`",
            )

    floor = (doc.get("limits") or {}).get("min_reported_n")
    if roster is None or not isinstance(floor, (int, float)):
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

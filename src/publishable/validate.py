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
from publishable.templates.registry import get_template, template_names

# `sweep`'s six axis keys, per reference.md § The one config file. A key present
# but empty (`groups: []`, `ablate: null`) declares no axis and is not a sweep.
SWEEP_AXIS_KEYS = ("baseline", "grid", "paired", "ablate", "sample", "groups")

REQUIRED_METADATA = ("description", "authors")


def _flatten(node: Any, prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in (node or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten(value, path))
        else:
            flat[path] = value
    return flat


def validate_config(config_path: Path, c: Collector) -> dict[str, Any] | None:
    try:
        doc = yaml.safe_load(config_path.read_text())
    except yaml.YAMLError as exc:
        c.error("E-CONFIG-PARSE", str(config_path), f"does not parse: {exc}")
        return None
    if not isinstance(doc, dict):
        c.error("E-CONFIG-PARSE", str(config_path), "does not parse as a mapping")
        return None

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
    _check_replication(doc, template, c)
    _check_unimplemented(doc, c)
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

    This build hardcodes one condition and executes repeats `as_declared`
    regardless of what is written here. It now resolves a unit roster, but
    several `data.units` sub-fields — allocation other than `within`,
    `assign`, `cluster_by`, `weight_by`, `measurements`, `holdout`, and a
    `resolver` source — are read by nothing yet. Each of these would
    otherwise validate clean and then run something other than what the
    config describes — the exact failure `E-REPL-KIND-UNSUPPORTED` already
    refuses for `batch`/`fold`/nested repeat levels. Each message says plainly
    that the block is honored in a later slice, so a user does not read this as
    their config being malformed.
    """
    sweep = doc.get("sweep") or {}
    declared_axes = [key for key in SWEEP_AXIS_KEYS if sweep.get(key)]
    if declared_axes:
        c.error(
            "E-SWEEP-UNSUPPORTED",
            "sweep",
            f"declares {', '.join(declared_axes)}, which is specified but not implemented "
            "in this build — every run executes exactly one condition regardless of what "
            "is declared here; sweep execution will be honored in a later slice",
        )

    units = (doc.get("data") or {}).get("units") or {}
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

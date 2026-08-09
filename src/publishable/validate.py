"""The S1 check subset. Collects rather than stops. docs/reference.md § Validation."""

import re
from pathlib import Path
from typing import Any

import yaml

from publishable.diagnostics import Collector
from publishable.materialize import TEMPLATE_VERSION
from publishable.param import MISSING
from publishable.provenance import find_repo_root
from publishable.templates.registry import get_template, template_names

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
    _check_parameters(doc, template, c)
    _check_versions(doc, c)
    _check_data(doc, config_path, c)
    _check_replication(doc, template, c)
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
    try:
        repo_root = find_repo_root(config_path).resolve()
    except Exception:
        return
    for field in ("input_dir", "output_dir"):
        raw = data.get(field)
        if not raw:
            c.error("E-DATA-REQUIRED", f"data.{field}", "is empty, and is required")
            continue
        resolved = Path(raw).expanduser().resolve()
        if resolved == repo_root or repo_root in resolved.parents:
            c.error(
                "E-DATA-IN-REPO",
                f"data.{field}",
                f"resolves inside the git repository at {repo_root}",
            )
    input_dir = data.get("input_dir")
    if input_dir:
        path = Path(input_dir).expanduser()
        if not path.is_dir() or not any(path.iterdir()):
            c.error("E-DATA-UNREADABLE", "data.input_dir", f"{path} is unreadable or empty")


def _check_replication(doc: dict[str, Any], template: Any, c: Collector) -> None:
    levels = ((doc.get("replication") or {}).get("repeats")) or []
    total = 1
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
            return
        total *= 1 if count is None else int(count)
    if total < template.default_repeats:
        c.warn(
            "W-REPL-FLOOR",
            "replication.repeats",
            f"total of {total} is below this convention class's default of "
            f"{template.default_repeats}",
        )

"""The config envelope's leaf types. See docs/reference.md § The one config file.

Declarative rather than a hundred hand-written guards, for the same reason
`parameter_spec` is declarative: a table can be read against § The one config
file, and scattered `isinstance` calls cannot. The table stops at `parameters`,
where `parameter_spec` is the single source of truth — a second authority over
those keys is the defaults-file problem in another costume.

Pure: this module returns findings and never raises, and imports nothing from
`config`, `artifacts`, `runner`, `cli` or `validate`.
"""

import difflib
from typing import Any

# `bool` is deliberately absent from every numeric entry: it is a subclass of
# `int`, so listing `int` alone would accept `max_executions: true`, which is
# not a budget. `_is_type` special-cases it.
#
# The table stops at every key's own materialized or documented type in
# § The one config file — `data.units.measurements` and `.holdout` are always
# mappings there (`{by: read_id, collapse: mean}`, `{method: random, ...}`),
# never a bare scalar, so both are typed `dict`. The optional blocks that
# section documents but a materialized config omits — `sweep`'s modes,
# `statistics.contrasts` / `.resample` / `.null_test` / `.report_by`, and
# `data.units.assign` — are declared at their own key with the one outer type
# that section gives them; the dynamic child keys inside `grid`, `baseline`,
# and `assign` (a swept parameter path, an axis name) have no fixed dotted
# path a table entry could name, so they stay `_check_shape`'s job.
LEAF_TYPES: dict[str, type | tuple[type, ...]] = {
    "schema_version": str,
    "experiment_type": str,
    "template_version": str,
    "plugin": str,
    "entrypoint": str,
    "metadata.name": str,
    "metadata.description": str,
    "metadata.authors": list,
    "metadata.institution": str,
    "data.input_dir": str,
    "data.output_dir": str,
    "data.input_manifest_policy": str,
    "data.units.from": (str, dict),
    "data.units.key": str,
    "data.units.attributes": list,
    "data.units.allocation": str,
    "data.units.cluster_by": str,
    "data.units.weight_by": str,
    "data.units.measurements": dict,
    "data.units.holdout": dict,
    "data.units.assign": dict,
    "replication.repeats": list,
    "replication.order": str,
    "replication.rationale": str,
    "statistics.correction": str,
    "statistics.contrasts": list,
    "statistics.resample": dict,
    "statistics.null_test": dict,
    "statistics.report_by": list,
    "sweep.baseline": dict,
    "sweep.groups": list,
    "sweep.paired": list,
    "sweep.ablate": dict,
    "sweep.sample": dict,
    "sweep.grid": dict,
    "limits.max_executions": int,
    "limits.max_failed_fraction": float,
    "limits.max_ineligible_fraction": float,
    "limits.min_units_per_cell": int,
    "limits.min_clusters": int,
    "limits.min_reported_n": int,
    "hypotheses": list,
}

# Skipped by the closure below entirely — each has its own authority, and a
# second one reporting the same namespace is the defaults-file problem one
# level up. `parameters` is `parameter_spec`'s (`E-PARAM-UNKNOWN`, with its own
# difflib hint); `sweep`'s top-level modes are `_check_sweep`'s (`E-SWEEP-KEY-UNKNOWN`).
EXEMPT_SUBTREES = frozenset({"parameters", "sweep"})


def _known_containers() -> frozenset[str]:
    """Every dotted prefix a `LEAF_TYPES` path implies, e.g. `data.units.from`
    implies `data` and `data.units`. Derived rather than hand-listed, so it
    cannot drift from the one table that already has to stay accurate for the
    type check."""
    containers: set[str] = set()
    for path in LEAF_TYPES:
        parts = path.split(".")
        for i in range(1, len(parts)):
            containers.add(".".join(parts[:i]))
    return frozenset(containers)


_KNOWN_LEAVES = frozenset(LEAF_TYPES)
_KNOWN_CONTAINERS = _known_containers()
_KNOWN_OR_EXEMPT = _KNOWN_LEAVES | _KNOWN_CONTAINERS | EXEMPT_SUBTREES


def _immediate_children(prefix: str) -> list[str]:
    """The unqualified names one level under `prefix` that the closure
    recognizes — leaves, containers, and the two exempt subtrees — for the
    `difflib` hint. Top-level names use `prefix == ""`."""
    children: set[str] = set()
    for path in _KNOWN_OR_EXEMPT:
        if prefix:
            if path.startswith(prefix + "."):
                children.add(path[len(prefix) + 1 :].split(".", 1)[0])
        else:
            children.add(path.split(".", 1)[0])
    return sorted(children)


def _check_unknown_keys(
    node: Any, findings: list[tuple[str, str, str]], prefix: str = ""
) -> None:
    """Walk `node` reporting any key not implied by `LEAF_TYPES`, skipping the
    two exempt subtrees entirely and never descending into a known LEAF's
    value — a leaf's own children (`data.units.holdout`'s `method`, a `from`
    dict's `resolver`) have no fixed dotted path a table entry could name, so
    they are `_check_shape`'s job, exactly as the module docstring already
    says for `sweep.grid`'s axis values.
    """
    if not isinstance(node, dict):
        return
    for key, value in node.items():
        # A YAML mapping key need not be a string — `1: oops` and `true: oops`
        # parse to an `int`/`bool` key, and `load_document` only rejects an
        # *unhashable* key (a list or mapping key, `yaml.ConstructorError`,
        # a `YAMLError` subclass) before this ever runs; a hashable non-string
        # key reaches here untouched. Coerced once, up front, so every use
        # below — building `path`, the `difflib` call, which requires a
        # string and is where this crashed before this comment was added —
        # sees a string. No `LEAF_TYPES` path, container, or exempt name is
        # ever anything but a string, so a coerced non-string key can never
        # accidentally match one; it always falls through to the report
        # below, which is the right outcome: `1: oops` is certainly not a key
        # this schema declares, and reporting nothing for it would be exactly
        # the silent-typo gap this task exists to close.
        key_name = key if isinstance(key, str) else str(key)
        path = f"{prefix}.{key_name}" if prefix else key_name
        if path in EXEMPT_SUBTREES:
            continue
        if path in _KNOWN_LEAVES:
            continue
        if path in _KNOWN_CONTAINERS:
            _check_unknown_keys(value, findings, path)
            continue
        near = difflib.get_close_matches(key_name, _immediate_children(prefix), n=1)
        hint = f" — did you mean `{near[0]}`?" if near else ""
        findings.append(
            ("E-CONFIG-KEY-UNKNOWN", path, f"is not a key this schema declares{hint}")
        )


_LABEL = {str: "a string", int: "an integer", float: "a number", list: "a list", dict: "a mapping"}


def _label(expected: type | tuple[type, ...]) -> str:
    if isinstance(expected, tuple):
        return " or ".join(_LABEL[t] for t in expected)
    return _LABEL[expected]


def _is_type(value: Any, expected: type | tuple[type, ...]) -> bool:
    allowed = expected if isinstance(expected, tuple) else (expected,)
    # A `bool` satisfies only an explicit `bool` declaration. Python makes
    # `isinstance(True, int)` true, and a budget of `true` is not a budget.
    if isinstance(value, bool):
        return bool in allowed
    # An `int` satisfies a `float` declaration: `confidence: 1` is the number
    # one, not a type error, and YAML gives no way to write `1.0` as `1`.
    if isinstance(value, int) and float in allowed:
        return True
    return isinstance(value, allowed)


def check_envelope(doc: dict[str, Any]) -> list[tuple[str, str, str]]:
    """`(code, field, message)` per wrong-typed leaf, in table order, followed by
    `(code, field, message)` per unknown key, depth-first — closing the schema
    that § Validation claims is closed. `parameters` and `sweep` are excluded
    from the unknown-key closure; see `EXEMPT_SUBTREES`.

    An absent leaf is not a finding — a required key absent is its own check's
    report — and a `null` is treated as absent, matching `doc.get("x") or {}`
    everywhere else in `validate`.
    """
    findings: list[tuple[str, str, str]] = []
    for path, expected in LEAF_TYPES.items():
        node: Any = doc
        for part in path.split("."):
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(part)
        if node is None:
            continue
        if not _is_type(node, expected):
            findings.append(
                (
                    "E-CONFIG-TYPE",
                    path,
                    f"is a {type(node).__name__} (`{node!r}`); expected {_label(expected)}",
                )
            )
    _check_unknown_keys(doc, findings)
    return findings

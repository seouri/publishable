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
# never a bare scalar, so both are typed `dict`. `measurements` is typed a
# second time one level down, at `.by` and `.collapse`: its children have fixed
# names and the block is no longer refused wholesale, so leaving it whole would
# have made a `colapse` typo unreachable by any check the moment the block's
# wholesale refusal retired — a latent gap turning live. A path
# that is both a leaf and a container is typed by the loop below AND descended
# into by the closure, which is why the closure checks containers first.
# `holdout` stays whole for now: `E-DATA-HOLDOUT-UNSUPPORTED` still refuses the
# block, so its gap is latent, and H3d closes it. The optional blocks that
# section documents but a materialized config omits — `sweep`'s modes,
# `statistics.contrasts` / `.null_test` / `.report_by`, and `data.units.assign`
# — are declared at their own key with the one outer type that section gives
# them. `statistics.resample` is no longer among them: it is closed one level
# in, the same way `measurements` is — its three keys (`method`, `n`,
# `stratify_by`) are fixed, so leaving the block whole would make a typo among
# them unreachable by any check. Unlike `measurements`, `resample` is closed
# before its own wholesale refusal (`E-STATS-RESAMPLE-UNSUPPORTED`) retires,
# not after — see the comment at its `LEAF_TYPES` entry for why validating the
# shape has to precede honouring the values.
#
# The table stopping at a key is the end of the line for everything under it:
# the closure below never descends into a known leaf, and `_check_shape`
# checks a container's *shape* and never the names inside one, so a
# misspelled `resolverr` in a `data.units.from` mapping or `methodd` in
# `holdout` is reported by no check in this build. That is the documented
# cost of a whole leaf (`reference.md` § Validation names the blocks it
# applies to and the slice that closes each), not a claim that such a key
# could never be named: `holdout`'s children have fixed names. The keys that
# genuinely cannot be named are the dynamic ones inside `grid`, `baseline`,
# and `assign` — a swept parameter path, an axis name — which no fixed dotted
# path reaches; closing the nameable leaves here and not those would leave a
# partial closure reading like a total one. `assign` differs one level further
# in: the axis *name* is still unnameable, but each axis block's own keys are
# fixed — `{method, from, ratio, block_size, stratify_by, seed}`, § The one
# config file's full expansion of an `assign` entry — so `_check_assign_axis_keys`
# below closes that inner level on its own, the same way `measurements` is
# closed one level in rather than left whole.
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
    "data.units.measurements.by": str,
    # `str` or `dict`: one rule for every collapsed column, or a per-column map
    # (`{depth: mean, site: first}`). It stays a LEAF under either form — the
    # map's keys are column names, which no fixed dotted path reaches, exactly
    # like a `grid` axis's swept path.
    "data.units.measurements.collapse": (str, dict),
    "data.units.holdout": dict,
    "data.units.assign": dict,
    "replication.repeats": list,
    "replication.order": str,
    "replication.rationale": str,
    "statistics.correction": str,
    "statistics.contrasts": list,
    "statistics.resample": dict,
    # Closed one level in, the arrangement `data.units.measurements` above has
    # and for its reason: these three names are fixed. `E-STATS-RESAMPLE-UNSUPPORTED`
    # still refuses the block wholesale at this commit — unlike `holdout` above,
    # this is deliberately closed *before* that refusal retires, not after: the
    # slice that honours `resample` needs the shape checked before it can read
    # the values, so validate-before-honour means these three names go in now
    # rather than waiting for the wholesale refusal to lift. `assign`'s separate
    # `_check_assign_axis_keys` is not the precedent: it exists because an axis
    # NAME is user-chosen and no fixed dotted path reaches it. `stratify_by` is
    # `(str, list)` because `units.stratum_names` — the single authority the
    # draw balances on — reads a bare `stratify_by: site` as one name exactly as
    # `[site]` is; typing it `list` alone would make the envelope and the draw
    # disagree about the same declaration.
    "statistics.resample.method": str,
    "statistics.resample.n": int,
    "statistics.resample.stratify_by": (str, list),
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
    value unless the table also declares paths BENEATH it — a leaf's own
    children (`data.units.holdout`'s `method`, a `from` dict's `resolver`) are
    reached by no check in this build: not here, and not by `_check_shape`,
    which checks a container's shape and never the names inside one. See the
    module docstring for why a leaf is left whole rather than half-closed, and
    why `data.units.measurements` is not one of them.
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
        # Containers before leaves: `data.units.measurements` is both — typed a
        # mapping by the loop in `check_envelope`, and descended into here so a
        # typo among its fixed-name children is reported. Checking leaves first
        # would stop at it and leave that closure open. Every other path is one
        # or the other, so the order changes nothing for them.
        if path in _KNOWN_CONTAINERS:
            _check_unknown_keys(value, findings, path)
            continue
        if path in _KNOWN_LEAVES:
            continue
        near = difflib.get_close_matches(key_name, _immediate_children(prefix), n=1)
        hint = f" — did you mean `{near[0]}`?" if near else ""
        findings.append(
            ("E-CONFIG-KEY-UNKNOWN", path, f"is not a key this schema declares{hint}")
        )


ASSIGN_AXIS_KEYS = frozenset({"method", "from", "ratio", "block_size", "stratify_by", "seed"})
"""Every key an axis block under `data.units.assign` may itself carry — § The
one config file's full expansion of one `assign` entry. The axis *name* one
level up (`arm` in that expansion) is user-chosen and stays outside
`LEAF_TYPES` for the reason the module docstring gives; the block's own keys
are not user-chosen and are closed by `_check_assign_axis_keys` below."""


def _check_assign_axis_keys(doc: dict[str, Any], findings: list[tuple[str, str, str]]) -> None:
    """Close `data.units.assign`'s inner level: every axis block's own keys
    against `ASSIGN_AXIS_KEYS`. Separate from `_check_unknown_keys` because
    that closure never descends into a known LEAF's value — `data.units.assign`
    is one — and the axis names one level in are exactly the dynamic keys no
    fixed dotted path can name, so the generic mechanism cannot be pointed at
    them. A non-mapping axis block is left to whatever already reports it
    (`E-DATA-ASSIGN-METHOD`'s "the block naming no method that it is") rather
    than duplicated here.
    """
    node: Any = doc
    for part in ("data", "units", "assign"):
        if not isinstance(node, dict):
            return
        node = node.get(part)
    if not isinstance(node, dict):
        return
    for axis_name, axis_block in node.items():
        if not isinstance(axis_block, dict):
            continue
        axis_label = axis_name if isinstance(axis_name, str) else str(axis_name)
        for key in axis_block:
            key_name = key if isinstance(key, str) else str(key)
            if key_name in ASSIGN_AXIS_KEYS:
                continue
            near = difflib.get_close_matches(key_name, sorted(ASSIGN_AXIS_KEYS), n=1)
            hint = f" — did you mean `{near[0]}`?" if near else ""
            findings.append(
                (
                    "E-CONFIG-KEY-UNKNOWN",
                    f"data.units.assign.{axis_label}.{key_name}",
                    f"is not a key this schema declares{hint}",
                )
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
    _check_assign_axis_keys(doc, findings)
    return findings

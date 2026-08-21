"""`diff`: compare two runs, or a run and a config, hash by hash.

docs/reference.md § How the three are computed, § The apparatus core can
only observe; docs/design-principles.md § Same code, different parameters;
README.md § The loop you'll actually live in. See
docs/superpowers/specs/2026-08-20-diff-freeze-design.md Decisions 1-6 and
docs/superpowers/plans/2026-08-20-diff-freeze.md tasks 7-11.

**This module is built in slices.** This task (H8b task 7) delivers only
`covered_config`'s delta walk — the projection `hashes.parameters_hash` now
hashes, flattened to dotted leaf paths and compared. Form detection, the
per-side header, the four rows and `command_diff` itself are task 8's; the
`apparatus` row is task 9's; a config side's `not comparable` rows and the
command's exit-code ruling are task 10's; the upstream block and the CLI arm
are task 11's. `diff` does not dispatch through `cli.main` until task 11.
"""

from typing import Any

import yaml

from publishable.hashes import covered_config

_ABSENT = object()


def _flatten(config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Dotted leaf paths over `covered_config`'s projection. A leaf is
    anything that is not a `dict` — a list is a leaf, not a subtree, because
    a config list (`statistics.contrasts`, `metadata.authors`, a sweep grid's
    values) is one declaration and splitting it by index would print a delta
    per element for a mere reordering (Decision 3)."""
    out: dict[str, Any] = {}
    for key, value in config.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, prefix=f"{path}."))
        else:
            out[path] = value
    return out


def _render_leaf(value: Any) -> str:
    if value is _ABSENT:
        return "(absent)"
    if isinstance(value, (dict, list)):
        return yaml.safe_dump(value, default_flow_style=True, sort_keys=True).strip()
    return str(value)


def parameter_deltas(config_a: dict[str, Any], config_b: dict[str, Any]) -> list[str]:
    """The delta walk flattens `covered_config`'s return on both sides to
    dotted leaf paths (Decision 3) — never a second, independently-built
    list, which is how the verdict a row prints above these lines (task 8)
    and the lines themselves cannot disagree about coverage. Sorted by
    path, so two runs of `diff` over the same pair print identically."""
    flat_a = _flatten(covered_config(config_a))
    flat_b = _flatten(covered_config(config_b))
    lines = []
    for path in sorted(set(flat_a) | set(flat_b)):
        value_a = flat_a.get(path, _ABSENT)
        value_b = flat_b.get(path, _ABSENT)
        if value_a == value_b:
            continue
        lines.append(f"  {path}  {_render_leaf(value_a)} → {_render_leaf(value_b)}")
    return lines

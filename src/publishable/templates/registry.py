"""Name → template. S1 knows only core's own; a local template arrives here
once a repo root is given.

The merged mapping is built fresh on every call — never cached module-globally
— because two projects resolved in one process must never see each other's
`templates/`.

A local name core already registers is refused here rather than resolved by a
merge order: `reference.md` § Creating a plugin requires a shadow of a core
name to fail at load, naming both providers, because "a plugin that could
redefine `generic` could change what a config means without changing the
config". This is the merge, so it is the first place that holds both sides —
and `discovery.py` cannot hold them, `registry` importing it. The refusal is
of the repo rather than of one lookup: every name resolves through `_merged`,
so a `templates/` core cannot merge refuses a config naming some third
template too, and there is no order left for a merge to express.
"""

from pathlib import Path

from publishable.errors import ContractError
from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate
from publishable.templates.discovery import discover_local

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    if repo_root is None:
        return dict(_BUILTIN)
    local = discover_local(repo_root)
    for name in sorted(local):  # name order: import order may decide nothing here
        if name in _BUILTIN:
            core = _BUILTIN[name]
            raise ContractError(
                f"the project-local template `{local[name].provider}` claims the name "
                f"`{name}`, which core itself registers as "
                f"{core.__module__}.{core.__qualname__} — a local template that could "
                "redefine a core name could change what a config means without "
                "changing the config, which is what `parameters_hash` exists to make "
                "impossible. Rename yours.",
                code="E-TEMPLATE-COLLISION",
            )
    return {name: found.cls for name, found in local.items()} | _BUILTIN


def get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None:
    cls = _merged(repo_root).get(name)
    return cls() if cls else None


def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_merged(repo_root))

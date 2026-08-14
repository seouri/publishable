"""Name → template. S1 knows only core's own; a local template arrives here
once a repo root is given.

The merged mapping is built fresh on every call — never cached module-globally
— because two projects resolved in one process must never see each other's
`templates/`. Merge order is `{**locals, **_BUILTIN}`: core wins on a name
collision, so a local file that names itself `generic` cannot silently change
what a config naming `generic` means.

This is an interim behaviour, not the designed policy: `reference.md` §
Creating a plugin requires a collision or a shadow of a core name to fail at
load, naming both providers, and gives "resolved by name, never by load
order" as the *reason for refusing* the shadow — not as license to resolve it
silently. Task 7 replaces this merge order with that refusal.
"""

from pathlib import Path

from publishable.templates.base import BaseTemplate
from publishable.templates.builtin.generic import GenericTemplate
from publishable.templates.discovery import discover_local

_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}


def _merged(repo_root: Path | None) -> dict[str, type[BaseTemplate]]:
    if repo_root is None:
        return dict(_BUILTIN)
    return {**discover_local(repo_root), **_BUILTIN}


def get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None:
    cls = _merged(repo_root).get(name)
    return cls() if cls else None


def template_names(repo_root: Path | None = None) -> list[str]:
    return sorted(_merged(repo_root))

"""`register_template` and the pending-registration buffer it fills.

A local template's `@register_template` argument is the whole of its
registration — the decorator records `(name, cls)` and returns the class
unchanged, so `class X(BaseTemplate)` still resolves for every later
reference to `X`.

The pending list is module-level, but it is only a staging buffer: task 6's
requirement is that two projects in one process never see each other's
templates, so nothing here keeps a persistent name→class mapping. Discovery
drains this list into whatever scoped registry it builds per run.
"""

import importlib
import sys
from collections.abc import Callable
from pathlib import Path

from publishable.templates.base import BaseTemplate

_pending: list[tuple[str, type[BaseTemplate]]] = []


def register_template(
    name: str,
) -> Callable[[type[BaseTemplate]], type[BaseTemplate]]:
    """Record `(name, cls)` for the next `drain_pending()` and return `cls` unchanged."""

    def decorator(cls: type[BaseTemplate]) -> type[BaseTemplate]:
        _pending.append((name, cls))
        return cls

    return decorator


def drain_pending() -> list[tuple[str, type[BaseTemplate]]]:
    """Hand over the accumulated registrations and empty the buffer."""
    pending = list(_pending)
    _pending.clear()
    return pending


def discover_local(repo_root: Path) -> dict[str, type[BaseTemplate]]:
    """Import every `templates/*.py` under `repo_root` and return what it registered.

    Eager rather than lazy — every file is imported, not only the one a config
    names — because a collision between two local templates (task 7) can only
    be detected between files a config never mentions. Import order therefore
    never decides which template wins; both are found and the collision is
    named. See `reference.md` § Creating a plugin.

    Imports by path, following `base_experiment.load_experiment`'s shape: the
    module name is purged from `sys.modules` first and `templates/` is put on
    `sys.path` only for the duration of the import, inside a `try`/`finally`,
    for the same reason `load_experiment` gives — a cached module from another
    project would silently hand back the wrong file's registrations. `.gitkeep`,
    `__init__.py`, and any non-`.py` file are skipped; a file that raises on
    import is not caught here (task 8 owns that diagnostic), and any
    registrations it made before raising are left in the pending buffer for
    task 8 to reason about rather than silently discarded.

    Discards whatever the pending buffer already held before this call — the
    return value is what *these files* registered, not a leftover from an
    earlier `@register_template` in the same process.
    """
    templates_dir = repo_root / "templates"
    if not templates_dir.is_dir():
        return {}

    drain_pending()  # discard anything queued before this call — not ours to return
    found: dict[str, type[BaseTemplate]] = {}
    for path in sorted(templates_dir.glob("*.py")):
        if path.stem.startswith("__"):
            continue
        module_name = path.stem
        sys.modules.pop(module_name, None)
        sys.path.insert(0, str(templates_dir))
        try:
            importlib.import_module(module_name)
        finally:
            sys.path.remove(str(templates_dir))
            sys.modules.pop(module_name, None)
        for name, cls in drain_pending():
            found[name] = cls
    return found

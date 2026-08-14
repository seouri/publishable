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

import hashlib
import importlib.util
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


def _module_name(repo_root: Path, stem: str) -> str:
    """A synthetic module name that cannot alias across repos, or onto a real module.

    Keyed on the resolved repo root as well as the file stem: two projects in
    one process can both hold `templates/my_assay.py`, and a name derived from
    the stem alone makes them one `sys.modules` entry. The `_publishable_local_`
    prefix keeps the name out of every real module's namespace, which is what
    stops a `templates/json.py` from being bound as `json` and importing
    *itself* when its own top level says `import json` — the same hazard a
    `templates/io.py` would carry, since `publishable` imports `io`.
    """
    token = hashlib.sha256(str(repo_root).encode()).hexdigest()[:12]
    return f"_publishable_local_{token}_{stem}"


def _import_file(path: Path, module_name: str, templates_dir: Path) -> None:
    """Execute one `templates/*.py` under `module_name`, leaving `sys.modules` as found.

    `templates_dir` goes on the *end* of `sys.path` so a file may import a
    sibling helper, without that directory shadowing a stdlib or site-packages
    name for the duration.

    Only the entries this import touched are undone, and only those that
    resolve under `templates_dir` — plus any entry it *replaced*, wherever it
    lives, since that is the clobber path. Blanket-restoring every new entry
    would un-import whatever the template legitimately pulled in (numpy, say),
    trading a discovery bug for a re-initialisation bug in the rest of the
    process.
    """
    before = dict(sys.modules)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable for a .py file
        raise ImportError(f"no import machinery for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.append(str(templates_dir))
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(templates_dir))
        for key, was in list(sys.modules.items()):
            if key not in before:
                origin = getattr(sys.modules[key], "__file__", None)
                if key == module_name or (origin and _under(Path(origin), templates_dir)):
                    del sys.modules[key]
            elif was is not before[key]:
                sys.modules[key] = before[key]
        for key, was in before.items():
            if key not in sys.modules:
                sys.modules[key] = was


def _under(path: Path, directory: Path) -> bool:
    """Whether `path` is `directory` or sits inside it, both resolved first.

    Resolved because the two strings reach here by different routes — one from
    a module's `__file__`, one from the repo root a command was given — and on
    macOS a symlinked temporary directory makes them differ textually while
    naming one place.
    """
    here, root = path.resolve(), directory.resolve()
    return root == here or root in here.parents


def discover_local(repo_root: Path) -> dict[str, type[BaseTemplate]]:
    """Import every `templates/*.py` under `repo_root` and return what it registered.

    Eager rather than lazy — every file is imported, not only the one a config
    names — because a collision between two local templates (task 7) can only
    be detected between files a config never mentions. Import order therefore
    never decides which template wins; both are found and the collision is
    named. See `reference.md` § Creating a plugin.

    Imports by path, for the reason `base_experiment.load_experiment` gives —
    a cached module from another project would silently hand back the wrong
    file's registrations. Two things make that safe here: each file executes
    under a module name keyed on the repo root as well as its stem (see
    `_module_name`), so no two projects share an entry; and `sys.modules` is
    put back as it was found after each file (see `_import_file`), so a helper
    a template imports from its own `templates/` cannot be served to the next
    project from cache. `.gitkeep`,
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
        _import_file(path, _module_name(repo_root.resolve(), path.stem), templates_dir)
        for name, cls in drain_pending():
            found[name] = cls
    return found

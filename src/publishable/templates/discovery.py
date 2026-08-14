"""`register_template` and the pending-registration buffer it fills.

A local template's `@register_template` argument is the whole of its
registration — the decorator records `(name, cls)` and returns the class
unchanged, so `class X(BaseTemplate)` still resolves for every later
reference to `X`.

The pending list is module-level, but it is only a staging buffer: task 6's
requirement is that two projects in one process never see each other's
templates, so nothing here keeps a persistent name→class mapping. Discovery
drains this list into whatever scoped registry it builds per run, and a name
two registrations claim is refused there rather than by the decorator: the
buffer records what a file said, and only the drained set knows what the rest
of the repo said.
"""

import hashlib
import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from publishable.errors import ContractError
from publishable.templates.base import BaseTemplate


class LocalTemplate(NamedTuple):
    """One registration a `templates/*.py` made, and who made it.

    The provider string is built here rather than recovered later because it
    cannot be recovered later: the `sys.modules` restore in `_import_file`
    deletes the module object, and `inspect.getfile` on the surviving class
    then raises `TypeError`. It is also the *pair* `path::ClassName` rather
    than a path alone, because two classes in one file are as much a collision
    as two files are, and a message built from paths alone would print one path
    twice and name no second provider at all. Two decorators stacked on one
    class are the residue that pair cannot separate, and `discover_local` says
    so rather than printing the same provider twice.
    """

    cls: type[BaseTemplate]
    provider: str


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
    name for the duration, and `sys.path` is snapshotted and put back whole —
    the same shape as the `sys.modules` snapshot, and for the same reason.
    Neither an index captured before `exec_module` nor a `remove` of the string
    survives a template that mutates `sys.path` on its own top level, whether
    itself or through a library it imports: one deletes an unrelated entry and
    leaves `templates/` on the path permanently, which serves the *next* repo
    this repo's helpers — precisely the leak this function exists to close.

    Only the `sys.modules` entries this import touched are undone, and only those `_is_local`
    places under `templates_dir` — plus any entry it *replaced*, wherever it
    lives, since that is the clobber path. Blanket-restoring every new entry
    would un-import whatever the template legitimately pulled in (numpy, say),
    trading a discovery bug for a re-initialisation bug in the rest of the
    process.
    """
    before = dict(sys.modules)
    before_path = list(sys.path)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - unreachable for a .py file
        raise ImportError(f"no import machinery for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.append(str(templates_dir))
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = before_path
        for key, was in list(sys.modules.items()):
            if key not in before:
                if key == module_name or _is_local(sys.modules[key], templates_dir):
                    del sys.modules[key]
            elif was is not before[key]:
                sys.modules[key] = before[key]
        for key, was in before.items():
            if key not in sys.modules:
                sys.modules[key] = was


def _is_local(module: object, templates_dir: Path) -> bool:
    """Whether `module` was loaded out of the repo's own `templates/`.

    `__file__` alone is not enough. A helper directory with no `__init__.py` —
    the default shape, since nobody adds one on purpose — becomes a namespace
    package, and a namespace package has no `__file__` at all. Left in
    `sys.modules` it hands the next repo the previous repo's submodules, which
    is the exact leak this restore exists to close. `__path__` covers regular
    packages, namespace packages, and plain modules with one predicate.
    """
    origin = getattr(module, "__file__", None)
    if origin and _under(Path(origin), templates_dir):
        return True
    return any(_under(Path(entry), templates_dir) for entry in getattr(module, "__path__", ()))


def _under(path: Path, directory: Path) -> bool:
    """Whether `path` is `directory` or sits inside it, both resolved first.

    Resolved because the two strings reach here by different routes — one from
    a module's `__file__`, one from the repo root a command was given — and on
    macOS a symlinked temporary directory makes them differ textually while
    naming one place.
    """
    here, root = path.resolve(), directory.resolve()
    return root == here or root in here.parents


def discover_local(repo_root: Path) -> dict[str, LocalTemplate]:
    """Import every `templates/*.py` under `repo_root` and return what it registered.

    Eager rather than lazy — every file is imported, not only the one a config
    names — because a collision between two local templates can only be
    detected between files a config never mentions. Import order therefore
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

    Two local registrations of one name raise `ContractError` ·
    `E-TEMPLATE-COLLISION` naming every provider that claimed it. A local name
    core itself registers is the *other* refusal that code covers, and it is
    not made here: this function knows what a repo declares and not what core
    does, so the shadow is refused where the two are merged — see
    `registry._merged`.
    """
    templates_dir = repo_root / "templates"
    if not templates_dir.is_dir():
        return {}

    drain_pending()  # discard anything queued before this call — not ours to return
    found: dict[str, LocalTemplate] = {}
    claims: dict[str, list[str]] = {}
    for path in sorted(templates_dir.glob("*.py")):
        if path.stem.startswith("__"):
            continue
        _import_file(path, _module_name(repo_root.resolve(), path.stem), templates_dir)
        for name, cls in drain_pending():
            provider = f"{path}::{cls.__name__}"
            claims.setdefault(name, []).append(provider)
            found.setdefault(name, LocalTemplate(cls, provider))
    # Every file is imported before any collision is raised, and a colliding
    # name is reported in name order rather than in the order the files
    # happened to be read: the whole point of the refusal is that import order
    # is a property of a machine, so it may not decide which fault is reported
    # either.
    for name in sorted(claims):
        providers = claims[name]
        if len(providers) > 1:
            # Distinct providers, because stacked decorators on one class make
            # two claims a `path::ClassName` cannot tell apart: printing that
            # one string twice would name no second provider, which is the
            # thing the class suffix exists to prevent. Refused either way — a
            # name claimed twice is refused however it was claimed — but only
            # the honest half is said, and the remedy differs with it.
            distinct = list(dict.fromkeys(providers))
            if len(distinct) > 1:
                who, remedy = " and ".join(distinct), "Rename one."
            else:
                who, remedy = f"{distinct[0]}, twice by the same class", "Remove one."
            raise ContractError(
                f"the project-local template name `{name}` is claimed more than once: "
                f"{who} — install order and import order are the "
                "only tie-breaks available, and both are properties of a machine "
                f"rather than of a design. {remedy}",
                code="E-TEMPLATE-COLLISION",
            )
    return found

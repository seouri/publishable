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


_LOCAL_MARKER = "_publishable_local_template"


def is_local_template(cls: type[BaseTemplate]) -> bool:
    """Whether `cls` is one `discover_local` found **defined inside** a repo's
    own `templates/`, judged by a marker `_import_file` stamps directly onto
    the class, not by where the class merely happens to be *registered*.

    A registered class's `__module__` is not always the file that claimed its
    name: `_module_name`'s `_publishable_local_` prefix is only ever applied
    to the non-`__`-prefixed file `discover_local` imports directly, so a
    `BaseTemplate` subclass defined in a `__`-prefixed helper (`templates/
    __helper.py`) and merely imported and `@register_template`-ed from
    `templates/my_assay.py` carries the *helper's* real module name, not the
    synthetic one — a prefix check on `__module__` would call that class
    non-local. The marker fixes that, but a marker set on *every* registered
    class has the opposite fault: a `templates/my_assay.py` that imports and
    registers a class it does not own — core's own `GenericTemplate`, or an
    installed plugin's — would stamp that shared class permanently, for
    every repo resolved in the same process afterward. So the stamp is set
    only when the class's own defining module resolves under `templates_dir`
    (`_is_local`, the same predicate the `sys.modules` restore below already
    trusts) — checked by `_import_file` itself, while that module is still in
    `sys.modules` to look up, before its own restore deletes the only
    evidence of where a local class was defined. `GenericTemplate` and every
    other builtin are never stamped, so they read `False` by default, and the
    stamp is set fresh on every `discover_local` call (new class objects each
    import), so nothing carries over between repos in one process.

    The boundary that predicate draws: a `BaseTemplate` subclass **defined**
    under `src/**` and merely registered from a `templates/*.py` reads
    non-local, so `init` writes core's `template_version` for it and
    `_check_versions` compares it — the same treatment an installed plugin's
    template gets. Stated as what the predicate does, not as the right answer
    for that class; it fails closed, which is the direction the two earlier
    fail-opens make the safe one.
    """
    return bool(getattr(cls, _LOCAL_MARKER, False))


def _import_file(
    path: Path, module_name: str, templates_dir: Path
) -> list[tuple[str, type[BaseTemplate]]]:
    """Execute one `templates/*.py` under `module_name`, leaving `sys.modules` as found,
    and return what it registered.

    `templates_dir` goes on the *end* of `sys.path` so a file may import a
    sibling helper **at import time**, without that directory shadowing a
    stdlib or site-packages name for the duration, and `sys.path` is
    snapshotted and put back whole — the same shape as the `sys.modules`
    snapshot, and for the same reason. Only at import time: the restore runs
    before any method of the class this file registered is ever called, so a
    helper imported from inside `aggregate` rather than at module scope is not
    on the path when `aggregate` runs, and raises `ModuleNotFoundError` there
    with no diagnostic of core's around it.
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

    The pending buffer is drained **here**, and each registered class is
    stamped local (`is_local_template`) here too, rather than by the caller
    after this function returns — both for the same reason: the restore below
    deletes the local `sys.modules` entries this call added (the file's own
    module, and any `__`-prefixed helper it imported), and once deleted there
    is no way left to ask where a class came from — `LocalTemplate.provider`
    hits the identical wall, which is why it builds its string from `path`
    while it still has it rather than recovering it from the class afterward.
    Checked with `_is_local` against each registration's *own* defining
    module (`sys.modules.get(cls.__module__)`), not against `module` — the
    file that did the `@register_template` call and the module a class was
    *defined* in are the same object only when a template defines its class
    directly rather than importing one from a sibling helper or from outside
    `templates/` entirely.
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
        registered = drain_pending()
        for _, cls in registered:
            defining_module = sys.modules.get(cls.__module__)
            if defining_module is not None and _is_local(defining_module, templates_dir):
                setattr(cls, _LOCAL_MARKER, True)
        return registered
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
    never decides which template wins: every file is imported before any
    verdict is reached, so both claimants are found, and both are named —
    unless a file in the same directory failed to load, which preempts the
    collision verdict entirely (see the load-fault paragraph below). See
    `reference.md` § Creating a plugin.

    Imports by path, for the reason `base_experiment.load_experiment` gives —
    a cached module from another project would silently hand back the wrong
    file's registrations. Two things make that safe here: each file executes
    under a module name keyed on the repo root as well as its stem (see
    `_module_name`), so no two projects share an entry; and `sys.modules` is
    put back as it was found after each file (see `_import_file`), so a helper
    a template imports from its own `templates/` cannot be served to the next
    project from cache. `.gitkeep`, a dunder-stemmed file (`__init__.py`, or a
    helper a template means to import as a sibling rather than have discovered
    directly — the same `__`-prefix convention `__init__.py` already uses),
    and any non-`.py` file are skipped.

    A file that raises on import (including a bare `sys.exit()`, which is a
    `SystemExit` rather than an `Exception` and so needs its own `except`),
    imports cleanly but registers nothing, or registers something that is not
    a `BaseTemplate` subclass is a fault named `E-TEMPLATE-LOAD` — none of
    these stops the loop: every later file is still imported, so a genuinely
    well-formed template elsewhere in the same directory still resolves into
    the fault this function raises rather than being silently skipped.
    Reported for the first such file in sorted order once the whole directory
    has been walked, and **preempting** any collision rather than accompanying
    it: the raise below happens before the collision loop runs at all, so a
    directory holding both faults reports `E-TEMPLATE-LOAD` and no collision —
    the claims are collected and then not used. Deliberate, and the reason is
    that a collision verdict computed while a file failed to load would be
    computed over a partial set of claims: the file that didn't load might
    have been a third claimant. Any registration a raising file made *before*
    raising is drained and discarded rather than left for the next file's
    `drain_pending()` to inherit and misattribute.

    Discards whatever the pending buffer already held before this call — the
    return value is what *these files* registered, not a leftover from an
    earlier `@register_template` in the same process — and does so on every
    path out, including the one that finds no `templates/` at all and returns
    an empty mapping.

    Two local registrations of one name raise `ContractError` ·
    `E-TEMPLATE-COLLISION` naming every provider that claimed it. A local name
    core itself registers is the *other* refusal that code covers, and it is
    not made here: this function knows what a repo declares and not what core
    does, so the shadow is refused where the two are merged — see
    `registry._merged`.
    """
    # Before the `templates/` check, not after, so the promise above holds on
    # every path out of this function rather than only on the one that finds a
    # directory. A repo with no `templates/` is the case that inherits without
    # discarding, and something is there to inherit: `cli` imports the
    # experiment package before `validate_config` runs, so a module-scope
    # `@register_template` anywhere under `src/**` queues an entry with no
    # `templates/` in sight.
    drain_pending()  # discard anything queued before this call — not ours to return
    templates_dir = repo_root / "templates"
    if not templates_dir.is_dir():
        return {}

    found: dict[str, LocalTemplate] = {}
    claims: dict[str, list[str]] = {}
    load_faults: list[ContractError] = []
    for path in sorted(templates_dir.glob("*.py")):
        if path.stem.startswith("__"):
            continue
        try:
            registered = _import_file(
                path, _module_name(repo_root.resolve(), path.stem), templates_dir
            )
        except SystemExit as exc:
            # `SystemExit` is a `BaseException`, so the broad `except Exception` below
            # does not see it — the same hazard `validate_config`'s own entrypoint import
            # guards against, one import earlier: a `templates/*.py` calling `sys.exit()`
            # at module scope, or building an `argparse` parser at import, would otherwise
            # end the process with no diagnostic at all.
            drain_pending()  # discard a partial registration — not this path's to keep
            load_faults.append(
                ContractError(
                    f"the project-local template `{path}` called `sys.exit()` while "
                    f"importing and registers nothing usable: SystemExit: {exc.code}",
                    code="E-TEMPLATE-LOAD",
                )
            )
            continue
        except Exception as exc:
            # Deliberately broad and deliberately relabeling: a template's own top level
            # can itself raise a coded `ContractError` (an `E-PARAM-VALUE` from a
            # module-scope sanity check, say), and it is reported here as
            # `E-TEMPLATE-LOAD` rather than under its original code — the original
            # survives only inside `{exc!r}`. Undocumented as a design choice, but not
            # accidental: `E-TEMPLATE-LOAD` is what names *this* fault, "a file this
            # repo's `templates/` cannot use", and a coded exception from arbitrary user
            # code reaching this point is exactly as unusable as an uncoded one.
            drain_pending()  # discard a partial registration — not this path's to keep
            load_faults.append(
                ContractError(
                    f"the project-local template `{path}` raised while importing and "
                    f"registers nothing usable: {exc!r}",
                    code="E-TEMPLATE-LOAD",
                )
            )
            continue
        if not registered:
            load_faults.append(
                ContractError(
                    f"the project-local template `{path}` imported cleanly but called "
                    "`@register_template` on nothing — every file under `templates/` "
                    "that is not itself a template must be `__`-prefixed",
                    code="E-TEMPLATE-LOAD",
                )
            )
            continue
        bad = next(
            (
                (name, cls)
                for name, cls in registered
                if not (isinstance(cls, type) and issubclass(cls, BaseTemplate))
            ),
            None,
        )
        if bad is not None:
            name, cls = bad
            load_faults.append(
                ContractError(
                    f"the project-local template `{path}` registered `{name}` as "
                    f"{cls!r}, which is not a `BaseTemplate` subclass",
                    code="E-TEMPLATE-LOAD",
                )
            )
            continue
        for name, cls in registered:
            # Locality is already decided and stamped by `_import_file`, per
            # class rather than per file — see `is_local_template`. Not
            # redone here: a class this file merely imported and registered
            # (core's own `GenericTemplate`, say) must stay unstamped even
            # though it arrives in this same `registered` list.
            provider = f"{path}::{cls.__name__}"
            claims.setdefault(name, []).append(provider)
            found.setdefault(name, LocalTemplate(cls, provider))
    if load_faults:
        raise load_faults[0]
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

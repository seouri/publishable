"""Importing a project's own Python **from source**, every time.

Two `spec-defects.md` filings, one root cause, three call sites:
`templates/discovery.py`'s `_import_file`, `report.py`'s
`render_with_override` and `base_experiment.py`'s `load_experiment` all
re-import a file the user may have just edited, inside one long-lived
process. CPython's `SourceFileLoader` validates its `__pycache__/*.pyc`
against the source's `(mtime, size)`, and `mtime` is whole-second on the
filesystems this was measured against — so a same-size rewrite inside one
wall-clock second is served from the **previous** compile, silently, at exit
`0`.

**What the filing guessed, and what is actually true.** Both filings, and the
design that took option (a) from them, propose *"handing it a fresh
`importlib.machinery.SourceFileLoader(module_name, str(path))` explicitly."*
**Measured, that changes nothing**: `spec_from_file_location(name, "….py")`
already returns exactly that class, so the explicit form is the same object
by another route, and the filing's own recipe still answers `f_probe` under
it. Option (a)'s substance is *force recompilation*, and this is where that
lives: `get_code` is overridden to compile the bytes on disk, so the cache is
neither read nor written for these imports.

`sys.dont_write_bytecode` is rejected for the reason design Decision 10
gives — it is module-global and would change compilation for every concurrent
import in the process, which is *don't cache anything* standing in for
*don't serve a stale entry for this file*. This loader is per-load and
affects no other import.
"""

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import CodeType, ModuleType


class FreshSourceFileLoader(importlib.machinery.SourceFileLoader):
    """A `SourceFileLoader` that compiles the source on every load.

    `SourceLoader.get_code` is the method that consults
    `__pycache__/<stem>.<tag>.pyc` and writes it back; overriding it to go
    straight from `get_data` to `source_to_code` is what makes a second
    import of a rewritten file see the rewrite. Nothing else about the loader
    changes, so `__file__`, `__loader__`, `get_source` and tracebacks are
    what an ordinary source import gives.
    """

    def get_code(self, fullname: str) -> CodeType:
        source = self.get_data(self.path)
        code = self.source_to_code(source, self.path)
        assert isinstance(code, CodeType)
        return code


def fresh_spec(
    module_name: str, path: Path | str, submodule_search_locations: list[str] | None = None
) -> importlib.machinery.ModuleSpec:
    """A spec for one source file, loaded through `FreshSourceFileLoader`."""
    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
        loader=FreshSourceFileLoader(module_name, str(path)),
        submodule_search_locations=submodule_search_locations,
    )
    if spec is None:  # pragma: no cover - unreachable for a real .py path
        raise ImportError(f"no import machinery for {path}")
    return spec


def import_module_fresh(module_name: str) -> ModuleType:
    """`importlib.import_module(module_name)`, with every source file it
    resolves compiled from disk rather than from `__pycache__`.

    Each dotted part is resolved through `PathFinder` against its parent's
    `__path__` (against `sys.path` for the root), so the caller's existing
    `sys.path` window is what decides where the project is found — this
    function opens none of its own.

    **The failure shape is the import system's own, deliberately.** A part
    that cannot be found raises `ModuleNotFoundError` with `.name` set to
    that part, because both call sites discriminate on exactly that: a
    missing `<root_pkg>.report` is *no override* while a missing module some
    override merely imports is `E-REPORT-OVERRIDE-IMPORT`, and `PathFinder`
    answers a missing module with `None` rather than by raising.

    A part already in `sys.modules` is reused rather than re-executed —
    matching `import_module` — which is why both call sites purge the root
    package first and why this function does not do it for them: what to
    purge is the caller's question (`load_experiment`'s docstring: two
    projects in one process can declare the same package name).
    """
    parts = module_name.split(".")
    module: ModuleType | None = None
    for depth, part in enumerate(parts):
        name = ".".join(parts[: depth + 1])
        cached = sys.modules.get(name)
        if cached is not None:
            module = cached
            continue
        parent = module if depth else None
        search = list(getattr(parent, "__path__", [])) if parent is not None else None
        found = importlib.machinery.PathFinder.find_spec(name, search)
        if found is None:
            raise ModuleNotFoundError(f"No module named {name!r}", name=name)
        if isinstance(found.loader, importlib.machinery.SourceFileLoader) and found.origin:
            spec = fresh_spec(
                name,
                found.origin,
                list(found.submodule_search_locations)
                if found.submodule_search_locations is not None
                else None,
            )
        else:
            # A namespace package (no loader), an extension module, or
            # anything else the finder answers with: left exactly as found.
            # This function forces recompilation of *source*; it does not
            # take over importing.
            spec = found
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            if spec.loader is not None:
                spec.loader.exec_module(module)
        except BaseException:
            # A half-executed module must not be left behind for the next
            # import to find and reuse — `import_module` does not leave one.
            sys.modules.pop(name, None)
            raise
        if parent is not None:
            setattr(parent, part, module)
    assert module is not None
    return module

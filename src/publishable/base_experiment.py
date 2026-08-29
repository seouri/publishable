"""The ordered steps list, and nothing else — plus how core resolves one from a config.

`load_experiment` lives here rather than in `cli.py` because two callers now need it:
`run` imports the entrypoint to execute it, and `validate` imports it to read
`nondeterministic` off the step classes (`W-REPL-DETERMINISTIC`). `cli.py` already
imports `validate`, so putting the loader in either of them would make the other's
import a cycle; this module imports only `base_step` and `errors`, so both can reach
it. No new module means no divergence from `reference.md` § Package layout.
"""

import sys
import threading
from pathlib import Path

from publishable.base_step import BaseStep
from publishable.errors import ContractError
from publishable.sourceimport import import_module_fresh


class BaseExperiment:
    steps: list[type[BaseStep]] = []


# `load_experiment` mutates two pieces of process-global state — it deletes the
# project's root package out of `sys.modules`, and it opens a `sys.path` window
# — so two of them running at once corrupt each other's import. Measured rather
# than reasoned: two threads loading one project raised 43,697 times in 8
# seconds, in two shapes. One thread's purge lands between another's
# `exec_module` and CPython's `sys.modules.pop(spec.name)` in `_load_unlocked`,
# giving `KeyError: '<pkg>.steps.<step>'`; or `import_module_fresh` reuses a
# cached entry another thread is still executing, giving an `AttributeError` on
# the entrypoint attribute that the module does have.
#
# Core itself spawns no threads, so no command reaches this. The caller that
# does is `tests/test_cli.py`'s H9b arm G, which drives two `main(["resume",
# …])` calls in threads as a stand-in for the two PROCESSES a real takeover
# race is between — processes do not share `sys.modules`, which is why the
# hazard is the instrument's rather than the protocol's. It took CI red on
# 2026-08-29 and had never fired on a developer machine.
#
# `RLock`, not `Lock`: the window executes the project's own module-level code,
# and a project that imports a second entrypoint from it would otherwise
# deadlock against itself. It does not make the whole library thread-safe —
# nothing claims that — it makes this function's own global-state window
# atomic against another copy of itself.
_LOAD_LOCK = threading.RLock()


def load_experiment(repo_root: Path, entrypoint: str) -> BaseExperiment:
    """Import the entrypoint class from the project's own `src/` on `sys.path`.

    The entrypoint's root package is purged from `sys.modules` first: two projects
    in one process can declare the same package name (both scaffolds default to a
    layout like `cohort_pilot`), and a cached module would silently hand back the
    other project's steps instead of raising or re-importing the right one.
    """
    module_name, _, attr = entrypoint.partition(":")
    if not module_name or not attr:
        raise ContractError(
            f"entrypoint {entrypoint!r} is not `<module>:<attribute>`",
            code="E-ENTRYPOINT-IMPORT",
        )
    root_pkg = module_name.split(".", 1)[0]
    with _LOAD_LOCK:
        return _load_locked(module_name, attr, root_pkg, repo_root, entrypoint)


def _load_locked(
    module_name: str, attr: str, root_pkg: str, repo_root: Path, entrypoint: str
) -> BaseExperiment:
    """`load_experiment`'s body, run under `_LOAD_LOCK`. See its comment."""
    for cached in [m for m in sys.modules if m == root_pkg or m.startswith(root_pkg + ".")]:
        del sys.modules[cached]
    src_entry = str(repo_root / "src")
    sys.path.insert(0, src_entry)
    try:
        # `import_module_fresh`, not `importlib.import_module`, for the reason
        # `sourceimport` documents: the ordinary loader validates its
        # `__pycache__` entry against the source's `(mtime, size)`, so an
        # entrypoint or step file rewritten at the same size inside one
        # wall-clock second is silently served from the previous compile.
        # `ModuleNotFoundError` is an `ImportError`, so the `except` below is
        # unchanged.
        module = import_module_fresh(module_name)
        cls = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise ContractError(
            f"entrypoint {entrypoint!r} could not be imported: {exc}",
            code="E-ENTRYPOINT-IMPORT",
        ) from exc
    finally:
        # Removed by IDENTITY (the exact path string this call inserted),
        # never by POSITION (`sys.path.pop(0)`) — the whole-branch review's
        # Minor 10: the entrypoint's own module runs inside this window by
        # import, and a project vendoring a sibling directory via
        # `sys.path.insert(0, ...)` (an ordinary idiom) is user code this
        # window invites in; a positional pop would then remove THAT entry
        # and leak `src_entry` on every import, success or failure alike.
        # `report.py`'s `render_with_override` fixed the identical exposure
        # this way (batch 3 review) — this is the sibling site `CLAUDE.md`'s
        # "removing by position is a fifth [proxy]" rule was written about
        # and did not itself reach. `if` rather than an unguarded `remove`
        # for the same reason: an import that raised before the insert
        # never reaches here missing its own entry, but one that removed
        # our entry itself (or cleared `sys.path` outright) must not turn
        # our own cleanup into a second, unhandled exception.
        if src_entry in sys.path:
            sys.path.remove(src_entry)
    experiment: BaseExperiment = cls()
    return experiment

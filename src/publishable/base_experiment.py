"""The ordered steps list, and nothing else — plus how core resolves one from a config.

`load_experiment` lives here rather than in `cli.py` because two callers now need it:
`run` imports the entrypoint to execute it, and `validate` imports it to read
`nondeterministic` off the step classes (`W-REPL-DETERMINISTIC`). `cli.py` already
imports `validate`, so putting the loader in either of them would make the other's
import a cycle; this module imports only `base_step` and `errors`, so both can reach
it. No new module means no divergence from `reference.md` § Package layout.
"""

import importlib
import sys
from pathlib import Path

from publishable.base_step import BaseStep
from publishable.errors import ContractError


class BaseExperiment:
    steps: list[type[BaseStep]] = []


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
    for cached in [m for m in sys.modules if m == root_pkg or m.startswith(root_pkg + ".")]:
        del sys.modules[cached]
    sys.path.insert(0, str(repo_root / "src"))
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise ContractError(
            f"entrypoint {entrypoint!r} could not be imported: {exc}",
            code="E-ENTRYPOINT-IMPORT",
        ) from exc
    finally:
        sys.path.pop(0)
    experiment: BaseExperiment = cls()
    return experiment

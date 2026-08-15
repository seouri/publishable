# Task 2 report: eager path discovery

## Status: complete

Commit: `1621e7c` — feat: add discover_local for eager path discovery of templates/*.py

## What was built

`discover_local(repo_root: Path) -> dict[str, type[BaseTemplate]]` in
`src/publishable/templates/discovery.py`:

- Returns `{}` immediately if `repo_root/templates` is not a directory.
- Drains (and discards) whatever the pending buffer already held before the
  call, so a registration queued earlier in the same process cannot leak into
  the result.
- For each `templates/*.py` file, sorted for determinism, skipping any stem
  starting with `__` (catches `__init__.py`; `.gitkeep`/`notes.md` are already
  excluded by the `*.py` glob):
  - purges the module name from `sys.modules`,
  - puts `templates/` on `sys.path` for the duration of the import only,
    inside `try`/`finally` (mirrors `base_experiment.load_experiment`'s shape
    and its stated reason: a cached module from another project could
    silently hand back the wrong file's registrations),
  - imports it via `importlib.import_module(stem)`,
  - drains the pending buffer immediately after that one file and merges into
    `found`, which is what gives per-file attribution for tasks 7/8.

## Tests (`tests/test_templates.py`)

Added the three tests from the brief plus a fourth surfaced by review:

1. `test_discovery_imports_every_file_not_only_the_named_one` — two files,
   neither named by a config, both must register; also asserts the returned
   *values* are the actual classes (`__name__`, `issubclass`), not just the key
   set — an earlier draft only checked keys and would have passed with
   `{"alpha": None, "beta": None}`.
2. `test_discovery_ignores_non_python_and_dunder_files` — `.gitkeep`,
   `__init__.py`, `notes.md` alongside a real `real.py`. Per the advisor's
   review, `__init__.py` now carries a real `@register_template` of its own
   (`should_not_be_found`) rather than being empty — an empty `__init__.py`
   would make the dunder-skip branch untestable, since importing it registers
   nothing either way and the assertion would pass whether or not the skip
   existed. Verified this by mutation (below).
3. `test_discovery_with_no_templates_directory_is_empty_not_an_error`.
4. `test_discovery_leaves_no_stale_pending_registration_behind` — a
   registration made before `discover_local` is called must not leak into the
   result and must not still be sitting in the buffer afterward.

## Mutation testing (apply → run named test → confirm FAIL → delete
`__pycache__` → revert → confirm PASS, checked by rerunning tests, not `git
status`)

- **Import only the first file found** (`[:1]` on the sorted glob, simulating
  lazy/name-only discovery): `test_discovery_imports_every_file_not_only_the_named_one`
  FAILED (`['alpha'] == ['alpha', 'beta']`). Reverted, PASS.
- **Include `.gitkeep`** (`glob("*")` instead of `glob("*.py")`):
  `test_discovery_ignores_non_python_and_dunder_files` FAILED (`TypeError`
  trying to import `.gitkeep` as a relative import). Reverted, PASS.
- **Remove the dunder-skip branch** (drop `if path.stem.startswith("__"):
  continue`): `test_discovery_ignores_non_python_and_dunder_files` now FAILS
  (`['real_one', 'should_not_be_found']` vs `['real_one']`) — this is only
  observable because `__init__.py` carries a real registration; with an empty
  `__init__.py` this mutation would have been silent. Reverted, PASS.
- **Weaken the value merge** (`found[name] = BaseTemplate` instead of `cls`):
  `test_discovery_imports_every_file_not_only_the_named_one` FAILED
  (`'BaseTemplate' == 'Alpha'`). Reverted, PASS.
- **Drop the pre-loop `drain_pending()`**:
  `test_discovery_leaves_no_stale_pending_registration_behind` FAILED
  (`['alpha', 'stale'] == ['alpha']`). Reverted, PASS.

All reverts confirmed by rerunning the test suite after deleting
`__pycache__`, never by `git status`.

## Verification

- `uv run pytest` — 1642 passed, 2 xfailed.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — no issues found in 41 source files.
- `ruff format .` not run, per instructions.

## What this task does NOT do (by design, owned by later tasks)

- **Collision refusal** (task 7): if `alpha.py` and `beta.py` both registered
  `"same_name"`, `found["same_name"]` would just be silently overwritten by
  whichever file's drain ran last. Not handled here.
- **Load-failure diagnostics** (task 8): if a file raises on import, the
  exception propagates out of `discover_local` uncaught. The `try`/`finally`
  only restores `sys.path`/`sys.modules`; it does not catch or wrap the
  exception into a `PublishableError`/`ContractError`. Also worth noting for
  task 8: any registrations a failing file made *before* raising are left in
  the pending buffer rather than being discarded — they'll be there for
  whatever task 8 does next, not silently dropped, but also not returned by
  this call.
- **Per-repo isolation hardening** (task 6): `module_name = path.stem` means a
  local template file named e.g. `templates/json.py` would `sys.modules.pop
  ("json")` before and after import, evicting the real stdlib `json` module
  from the cache for the duration and beyond if another thread imports
  concurrently. This is a real footgun but squarely task 6's territory —
  the brief said not to over-engineer repo-safety here, and a namespaced
  module name (or `importlib.util.spec_from_file_location` with a unique
  name) is the natural fix task 6 should apply.

## Concerns

None that block this task. The two items above (module-name collision with
real packages; uncaught import exceptions) are exactly the two gaps the brief
told me to leave to tasks 6 and 8, and I've named them explicitly rather than
silently working around them, per its instruction not to over-engineer this
slice.

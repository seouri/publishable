# Task 1 report: `register_template`

## Status
DONE

## What was built

- `src/publishable/templates/discovery.py` (new): `register_template(name)` returns
  a decorator that appends `(name, cls)` to a module-level `_pending` list and
  returns `cls` unchanged; `drain_pending()` copies `_pending`, clears it, and
  returns the copy. No persistent name→class dict exists anywhere in this file —
  the mapping task 6 owns is deliberately absent here.
- `src/publishable/__init__.py`: imports and exports `register_template`, added
  to `__all__` in its alphabetical slot.
- `tests/test_templates.py`: added the test from the brief verbatim (as
  `test_register_template_returns_the_class_and_records_the_name`), appended
  after the existing tests in that file.

## TDD sequence followed

1. Added the test; ran it — failed on `ImportError: cannot import name
   'register_template' from 'publishable'` at the `from publishable import
   register_template` line, i.e. on the import, not an assertion, per Step 2.
2. Implemented `discovery.py` and the `__init__.py` export.
3. Full suite green: `uv run pytest` → 1638 passed, 2 xfailed;
   `uv run ruff check .` → All checks passed; `uv run mypy` → Success, no
   issues found in 41 source files.

## Mutation testing (both named in the brief)

**Mutation A — decorator returns the record, not the class.**
Changed `return cls` to `return (name, cls)` (with a `type: ignore` to keep
mypy from flagging the deliberately-wrong return during the mutation). Ran
the target test: failed with `AttributeError: 'tuple' object has no
attribute '__name__'` on the first assertion, as expected. Deleted
`__pycache__` under `src/`, reverted the edit, reran the test: passed. Revert
verified by behaviour (test outcome), not `git status`.

**Mutation B — `drain_pending` does not clear.**
Removed `_pending.clear()`. Ran the target test: failed on the final
assertion (`assert drain_pending() == []`) with the leftover `("my_assay",
MyAssay)` entry still present, as expected. Deleted `__pycache__`, reverted,
reran: passed. Revert verified by behaviour.

## Commit

`227936d` — feat: add register_template decorator and pending-registration buffer

## Concerns / brief defects

None found. The brief's requirements were unambiguous and directly
testable as written:

- The exact test given passes verbatim with no reinterpretation needed.
- "Module-level pending list, not a registry mapping" was satisfiable exactly
  as scoped — `discovery.py` contains no dict from name to class, only the
  list of tuples the test itself asserts against.
- Both named mutations produced the exact failures anticipated by the
  docstring rationale (decorator-returns-record breaks class references;
  non-draining breaks the "draining empties it" property), so the test is
  precise, not just passing by accident.

One judgment call, not a defect: mypy required an explicit return-type
annotation on `register_template` (`Callable[[type[BaseTemplate]],
type[BaseTemplate]]`), which the brief's minimal decorator sketch didn't
show. This is a straightforward consequence of `uv run mypy` being a stated
gate, not a conflict with the brief.

# Task 2 report: `units_matching`

Added `units_matching(roster, within) -> set[str] | None` to `src/publishable/contrasts.py`,
following the brief verbatim.

- `within=None` returns `None` (unrestricted contrast — nobody asked).
- `within={...}` returns the set of matching unit keys, conjunctively over all
  named levels, possibly empty (a real, reportable empty stratum — nobody
  matched). The two are never collapsed.
- Comparison is `str(attribute) == str(level)` in both directions, so an int
  level from YAML matches a string attribute read from a table.

Added the five test cases from the brief verbatim to `tests/test_contrasts.py`,
plus a local `_roster` helper matching the idiom used in `tests/test_units.py`
(`Unit(key=..., paths=(), attributes=...)`, wrapped in `UnitList`).

`contrasts.py` remains pure: the only new import is `publishable.units.UnitList`,
under `TYPE_CHECKING` only, so there is no runtime dependency added.

## Verification

- `uv run pytest -v`: 642 passed (637 pre-existing + 5 new).
- `uv run ruff check .`: All checks passed.
- `uv run mypy`: Success, no issues found in 35 source files.

## Commit

Committed as `Select the units a within stratum names`.

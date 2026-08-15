# Task 4 report: `paired_t_over_units` and `cohens_dz`

## Status
Done. Implemented verbatim from the brief.

## Changes
- `src/publishable/stats.py`: added `paired_t_over_units(diffs, confidence=0.95) -> Interval | None`
  (delegates to `t_over_units`, relabels `method="paired_t_over_units"`) and
  `cohens_dz(diffs) -> float | None` (mean / sample sd, ddof=1; `None` below two
  diffs or when sd == 0). Inserted just above `resample_seed`.
- `tests/test_stats.py`: added the six tests from the brief verbatim (imports
  extended with `cohens_dz`, `paired_t_over_units`), placed after
  `test_confidence_widens_the_interval`. Added `is not None` narrowing asserts
  before attribute access to satisfy mypy strict on `Interval | None`.

## Verification
- `uv run pytest -q` → 653 passed (647 pre-existing + 6 new).
- `uv run ruff check .` → All checks passed.
- `uv run mypy` → Success: no issues found in 35 source files.

## Hand-computed value
`cohens_dz([1.0, 2.0, 3.0, 4.0])` == 1.93649167 (mean 2.5 / sample sd 1.2909944)
held exactly as asserted — no discrepancy.

## Concerns
None. Commit `23c830a` on `s4b-contrasts`.

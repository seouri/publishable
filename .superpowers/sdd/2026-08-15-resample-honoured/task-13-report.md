# Task 13 report — resolve `statistics.resample` once and thread it

**Status:** done.
**Commit:** `220744b` — feat: resolve statistics.resample once in command_run and thread it.

**Tests:** `uv run pytest` → 1769 passed, 2 xfailed (baseline 1766 passed + 2 xfailed, +3 new tests
from this task); `uv run mypy` clean (42 source files); `uv run ruff check .` clean. Task 1's two
pins (`test_the_undeclared_resample_shape_is_pinned_absent_key`,
`test_the_undeclared_resample_shape_is_pinned_explicit_null`) still pass unmodified. Both named
mutations applied, confirmed FAIL, reverted in place, confirmed PASS:
1. `.get("resample", {"n": 500})` in place of `.get("resample") or {}` → failed the absent-key case
   of `test_an_undeclared_resample_still_draws_two_thousand` (and Task 1's absent-key pin) while
   passing the explicit-`null` case, exactly the asymmetry the brief predicted.
2. `"declared": n != 2000` in place of `"declared": bool(declared)` → failed
   `test_the_resample_block_is_resolved_once`.

## What changed

- Added `cli._resolved_resample(doc) -> dict[str, Any]` (placed immediately before `_entry_for`),
  returning `{"method", "n", "stratify_by", "declared"}`. Reads `(doc.get("statistics") or
  {}).get("resample") or {}`, falling back to `{}` again if the value isn't a dict. `n` defaults to
  `2000` unless the declared value is a non-bool `int`. `stratify_by` goes through
  `units.stratum_names` (imported into `cli.py`'s existing `from publishable.units import (...)`
  block). `declared` is `bool(declared)` — a `{"n": 2000}` declaration is still `declared: True`,
  independent of whether `n` differs from the default.
- Replaced the `derived_metric_draws = 2000` literal (originally around `cli.py:1507`, now
  `:1552` after this and prior edits) with `resample_spec = _resolved_resample(doc)` /
  `derived_metric_draws = resample_spec["n"]`. Left all six existing read sites of
  `derived_metric_draws` untouched (verified by `grep -n derived_metric_draws src/publishable/cli.py`
  before and after: now at `:1726`, `:1805`, `:1811`, `:2035`, `:2100`, `:2112`).
- Added three tests to `tests/test_cli.py`, verbatim from the brief:
  `test_a_declared_resample_n_changes_the_derived_draw_count`,
  `test_an_undeclared_resample_still_draws_two_thousand`,
  `test_the_resample_block_is_resolved_once`.

## The stratify_by gap (routed by the brief to Tasks 13-15)

Chose: **resolve and store `stratify_by` on `resample_spec`, thread nothing further with it in this
task.** `percentile_of_derived` takes no `strata` parameter (confirmed by reading
`src/publishable/stats.py:901-960`), and none of the six existing `derived_metric_draws` read sites
(all `summarize_step`/`_compute_vs_baseline`/`_compute_declared_contrasts` calls) pass a strata
argument today. So there is nothing in this task's diff that could claim a stratification was
honoured for a derived metric — the field is resolved and available on `resample_spec` for Task 14
to consume when it wires the column-metric percentile, but is not read by anything yet. This leaves
the gap open exactly where the brief found it, not narrower and not silently closed; nothing in the
record (no comment, no docstring) claims otherwise. `_resolved_resample`'s docstring says this
explicitly so Tasks 14-15 don't have to re-derive it.

## Concerns

- The brief's line numbers for the six `derived_metric_draws` read sites (`:1681, :1760, :1766,
  :1990, :2055, :2067`) were off by a consistent +6 from what was actually in the file at
  `a6407c0` (`:1687, :1766, :1772, :1996, :2061, :2073`) — line drift from commits between when the
  brief was written and this task, not a semantic disagreement. Verified by `grep` before touching
  anything; all six sites were exactly where expected content-wise, just six lines later.
- No other brief/code disagreement found. The resolver's shape, the `.get(...) or {}` requirement,
  the `declared`-vs-`n` split, and the mutation script all matched the code as found.

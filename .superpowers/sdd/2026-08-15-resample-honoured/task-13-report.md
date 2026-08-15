# Task 13 report — resolve `statistics.resample` once and thread it

**Status:** done, including a review-round fix pass.
**Commits:** `220744b` (initial), plus a follow-up addressing coordinator review (see below).

**Tests:** `uv run pytest` → 1770 passed, 2 xfailed; `uv run mypy` clean (42 source files);
`uv run ruff check .` clean. Task 1's two pins
(`test_the_undeclared_resample_shape_is_pinned_absent_key`,
`test_the_undeclared_resample_shape_is_pinned_explicit_null`) still pass unmodified. Mutations
applied, confirmed FAIL, reverted in place, confirmed PASS:
1. `.get("resample", {"n": 500})` in place of `.get("resample") or {}` → failed the absent-key case
   of `test_an_undeclared_resample_still_draws_two_thousand` (and Task 1's absent-key pin) while
   passing the explicit-`null` case, exactly the asymmetry the brief predicted.
2. `"declared": n != 2000` in place of `"declared": bool(declared)` → failed
   `test_the_resolver_fills_every_default_and_separates_declared_from_n`.
3. (review round) `"method": method or "bootstrap"` in place of the type-guarded form → failed the
   same test's non-`str`-`method` case.
4. (review round) a duplicated `_resolved_resample(doc)` call right after the real one → failed
   `test_the_resample_block_is_resolved_exactly_once`, confirming that test can actually detect
   double-resolution rather than only asserting shape.

## Review round (coordinator: 1 Important, 3 Minor, no Critical)

1. **Important — the threading-site comment overclaimed.** It said `statistics.resample` "is
   honored as of H4a" unqualified, and quoted § Statistical reporting's "resolved values ...
   recorded beside the interval" as met, when only `n` is read and threaded; `method`,
   `stratify_by`, and `declared` are resolved but unread, and no recording happens until task 17.
   Rewrote the comment at `cli.py` (just above `resample_spec = _resolved_resample(doc)`) to say
   plainly what's true now — `n` threaded to the six existing sites, `method`/`stratify_by`/
   `declared` resolved-but-unread, naming why each is unread (no second method exists yet; task 14
   wires stratified column resampling; task 14 gates the percentile switch on `declared`) — and that
   the "recorded beside the interval" requirement is task 17's, not met yet.
2. **Minor — `test_the_resample_block_is_resolved_once` didn't test once-ness.** It called the
   resolver directly and would pass unchanged under seven independent call sites. Renamed it to
   `test_the_resolver_fills_every_default_and_separates_declared_from_n` (shape-only, docstring says
   so explicitly) and added a real once-ness test,
   `test_the_resample_block_is_resolved_exactly_once`, which monkeypatches `cli._resolved_resample`
   with a call-counting wrapper around a full `run_a_project` and asserts exactly one call. Verified
   this new test fails when a second (redundant) call is inserted at the threading site (mutation 4
   above).
3. **Minor — the resolver's docstring forecast task 14 as a guarantee.** Reworded the `stratify_by`
   paragraph to state only what's true today (`percentile_of_derived` takes no `strata` param, so no
   construction could honor it yet) without naming which future task closes it.
4. **Minor — `method` had no type guard**, unlike `n` and the non-dict case. Added
   `method if isinstance(method, str) and method else "bootstrap"`, and a case in the renamed
   resolver test (`{"method": 123, "n": 10}` → `"method": "bootstrap"`), confirmed by mutation 3
   above.

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
  `test_the_resample_block_is_resolved_once` (later renamed and supplemented — see review round
  below).

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

# Task 15 report

Status: COMPLETE, per the amendment (both column and derived paths honour `strata`), all review
findings from the first round addressed.

Commits: `8c4bcbb` (feature), `6267120` (first report), `d715e08` (round-1 review: gate
`resample_strata` on `declared`, tighten a docstring), and this round's fixes (see below).

Tests: `uv run pytest` — 1787 passed + 2 xfailed baseline for the feature commit; +4 more after this
round's fixes (3 constant-pool-refusal tests, 1 clustered-wiring pin). `uv run ruff check .` and
`uv run mypy` clean throughout. Every new assertion and every mutation named below was applied,
confirmed FAIL, `__pycache__` cleared, reverted in place, confirmed PASS.

## Review round 2 — addressed

**Finding 1 (Important) — `percentile_of_derived` had no constant-pool refusal.** Fixed: added the
same content-based check its two siblings (`percentile_over_units`'s stratified branch,
`percentile_over_units_clustered`'s cluster-content branch) carry, applied to each stratum's own
recorded row — refuses (returns `(None, 0)`) when every key in a stratum carries the identical row,
a singleton stratum ("any near-unique attribute") being the trivial case. Pinned by three new tests:
`test_percentile_of_derived_refuses_the_singleton_stratum_case`,
`test_percentile_of_derived_refuses_a_multi_key_stratum_of_identical_rows_too`, and
`test_percentile_of_derived_does_not_over_refuse_one_constant_stratum_among_others` (the `all(...)`
gate, not `any(...)` — a single degenerate stratum among others that vary keeps its interval). All
three mutated (disabled the check) and confirmed FAIL before revert.

**Finding 2 (Important) — the clustered × stratified wiring at `summarize_step`'s own call site was
unpinned.** Added `test_summarize_step_threads_strata_into_the_clustered_column_call`: a banded
fixture paired into homogeneous two-unit clusters (10 `low`, 4 `mid`, 1 `high`), asserting the
stratified clustered interval is narrower than the unstratified one at the SAME clusters. Mutated
`summarize_step`'s own `percentile_over_units_clustered` call (`strata=column_strata` → `strata=None`)
and confirmed the new test fails; reverted.

**Minors — all five addressed:**
- Label-invariance for the derived path: added `test_percentile_of_derived_is_invariant_to_stratum_labels`,
  the derived-path counterpart of `test_a_stratified_draw_is_invariant_to_stratum_labels`. Mutated
  the ordering to sort pools BY LABEL (`[pools[label] for label in sorted(pools)]`) instead of by
  their own sorted contents; confirmed the test fails (a different rng draw sequence under the
  renamed labels moves the interval by a fraction of a unit) before reverting.
- The `percentile_of_derived` docstring claiming `.get`-like defaulting behaviour is corrected: it
  now states plainly that a key `strata` doesn't hold raises `KeyError`, not that it "silently draws
  as if unstratified."
- Sentinel collisions are now discussed in three places: a `cli.py` comment beside `resample_strata`'s
  `<absent>` construction, a new `docs/superpowers/spec-defects.md` entry, and the
  `E-STATS-RESAMPLE-STRATIFY-VARIES` "cannot disagree" claim in both `stats.py` (two copies) and
  `reference.md` (two rows) is narrowed to the single-uncomposed-name case it was actually built for,
  rather than left describing a guarantee `cli.py`'s composed, sentinel-bearing label no longer makes
  unconditionally.
- The retry `summarize_step` call (no `derived`, no `seed`) now carries a comment explaining why
  `strata` is left off — the same reason `resample_columns` already is: inert without a `seed`, and
  must stay off together with it if a future change ever threads one through that retry.
- The report's own `percentile_over_units_derived` (a method string that does not exist) is corrected
  to `percentile_over_units`, the actual method name `percentile_of_derived` returns.

**Adjudication 3 (report_by asymmetry) — filed, not fixed, per the coordinator's ruling.** Merged
into finding 1's entry in `spec-defects.md` (one heading, two parts: finding 1 CLOSED, the report_by
gap deferred beside it with a named owner — `H4 Statistics`, the same owner this file's existing
"report_by hardening" entry names). Reasoning recorded there: it discloses (different `method`
strings, different `resample_draws` presence) rather than hiding identically the way task 14's case
would have, it predates this task, and the real fix is a task (level-thin `min_honest_draws`,
per-level two-valued draws, tests) rather than a line.

## Original concerns (still true)

- The brief's own `test_a_unit_missing_a_stratum_attribute_joins_a_stratum_of_its_own` fixture (a
  blank CSV cell) does not exercise the `<absent>` sentinel: `csv.DictReader` reads a blank field as
  `""`, a real value, not `None`. Rewritten to a genuinely short CSV row (header
  `patient_id,arm,cohort`, a row omitting the trailing `cohort` field) so the attribute is really
  `None` for some units, which is what let the drop-mutation raise `KeyError` and fail the test as
  designed.

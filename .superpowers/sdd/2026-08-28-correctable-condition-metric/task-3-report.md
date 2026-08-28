# Task 3 report

Status: complete.

Functions changed: `percentile_over_units` and `percentile_over_units_clustered`
(`src/publishable/stats.py`, both surfaced by grepping `def percentile_over_units`
and confirming no other sibling shares the shape). Both now return `PairedResample`
instead of a bare `Interval | None`. `draws_used` on the success path is
`len(means)` (== requested `draws`, since neither path ever filters a draw —
docstring rewritten to say this explicitly rather than argue the old "stays
bare" decision). Every structural refusal returns `pool=[]`; `pool` on success
is the actual sorted `means` list `_percentile_ranks` indexed, not a rebuild.
No arithmetic, seed, draw count, or `interval_at` call changed.

Call sites: 1 production site (`summarize_step`, `stats.py:3208`), updated to
read `.interval` off the new `PairedResample`, with `Member` wiring left for
Task 4 per the brief. In `tests/test_stats.py`: grep `percentile_over_units(_clustered)?\(`
finds 85 call-expression occurrences; 38 required a `.interval` insertion
(attribute access, `is None`/`is not None`, or equality against a bare
`Interval`); the rest were object-to-object equality between two calls, which
stayed valid unchanged since `PairedResample` equality still holds. No other
file (`test_demo.py`, `test_validate.py`, `test_cli.py`) calls either function
directly — confirmed by grep; all three still pass.

One pre-existing test, `test_percentile_over_units_still_returns_a_bare_interval`,
pinned exactly the decision this task reverses; renamed to
`test_percentile_over_units_now_returns_a_pairedresample` and rewritten to state
why the decision changed, plus two new pool-fidelity tests (unclustered and
clustered) mirroring Task 2's.

Mutation evidence: for each of the two new pool-fidelity tests, replaced the
returned `pool` with a differently-seeded decoy of matching length/sortedness
(`sorted(random.Random(999999).random() for _ in range(len(means)))`). Both
went red (`interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)`
failed, e.g. `(0.21..., 0.85...) == (24.75, 33.98...)` and
`(0.21..., 0.85...) == (7.2, 14.27...)`). Reverted each by hand; `diff` against
a pre-mutation copy confirms byte-identical restoration; both tests green again.

Oracle: `test_task1_bit_stability_oracle_over_the_correction_machinery` stayed
green throughout, both before and after the mutation-and-revert cycle.

Full suite run before reporting: `tests/test_stats.py` (338 passed),
`tests/test_validate.py` (812 passed), `tests/test_demo.py` (background run,
completed 0 exit code), the oracle (passed). `ruff check .`, `ruff format --check .`,
`mypy` all clean.

Concern to flag: `docs/superpowers/spec-defects.md`'s "A column metric's
`resample_draws` records the requested `n`, not a survivor count" entry's
premise is now expiring — a survivor count is available for the first time via
`PairedResample.draws_used` — but `resample_draws` itself was left unchanged
(still records requested `draws`) per binding #5; owning the re-owner/closure
is Task 6's, not touched here.

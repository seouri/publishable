# Task 2 report — `percentile_of_derived` and `percentile_of_derived_clustered` return the pool

**Status:** done.

**Return shape chosen:** reused the existing `PairedResample` dataclass
(`interval: Interval | None`, `draws_used: int`, `pool: list[float]`) rather
than adding a third tuple element or a new dataclass. Its own docstring
already states the reason a tuple was rejected ("a positional `[2]` at a call
site says nothing about what it holds"), and its field shapes match exactly
what these two functions need — no new type introduced, one idiom for
"interval + count + pool" across the module instead of two.

**Call sites:** grepped `src/` and `tests/` for `\bpercentile_of_derived(_clustered)?\(` —
23 matches, 2 are the `def` lines, leaving 21 real call sites (1 production,
in `summarize_step` at `stats.py`, calling both; 20 in `tests/test_stats.py`).
Updated the summarize_step call site to unpack `.interval`/`.draws_used` from
the new `PairedResample` (pool discarded there — wiring it into
`correction.Member` is Task 4's job). Updated all 20 test call sites: most
tuple-unpacking assignments became `resampled = ...` + attribute access;
sites that already discarded the return entirely, or already bound the whole
result to one name (`a = percentile_of_derived(...)`), needed no change.
Confirmed by re-running the same grep: zero remaining `x, y = percentile_of_derived...` patterns.

**New tests:** `test_percentile_of_derived_carries_the_pool_it_read_its_interval_from`
and `test_percentile_of_derived_clustered_carries_the_pool_it_read_its_interval_from`
in `tests/test_stats.py`, mirroring the existing `paired_percentile_of_derived`
pool pin: assert `len(pool) == draws_used`, `pool == sorted(pool)`, and
`interval_at(pool, 0.95) == (interval.low, interval.high)` — the honest
read-off check, not a shape-only assertion.

**Mutation evidence:** replaced each function's final `pool=values` with a
pool drawn from an unrelated seed (999999 / 888888), same length, sorted.
Both new tests went red:
- unclustered: `interval_at(got.pool, 0.95) == (got.interval.low, got.interval.high)` failed, `(0.0316…, …) != (25.133…, 33.9)`
- clustered: same assertion failed, `(0.0352…, …) != (14.231…, …)`
Restored from a pre-mutation copy, then confirmed green by running the tests
again (3 passed each time) rather than trusting `git status`; final `diff`
against the saved copy showed no difference.

**Verification run:** `tests/test_stats.py` — 336 passed. Task 1 oracle
(`tests/test_cli.py::test_task1_bit_stability_oracle_over_the_correction_machinery`) —
1 passed, stayed green throughout (no numbers moved). `uv run ruff check .` —
all checks passed. `uv run ruff format --check .` — 101 files already
formatted. `uv run mypy` — success, 56 source files, no issues.

**Concerns:** none. No arithmetic, seed, draw count, or draw order changed —
verified by the oracle staying green and by `mypy`/tests passing unchanged
apart from the return-shape plumbing.

## Task 4 report — `summarize_step` carries the pool out

**Status:** done.

**Carrier chosen:** a `"pool"` key inside each metric block `summarize_step` returns,
beside `interval`/`resample_draws`, gated on the same condition (`resample_columns and
seed is not None` for a recorded column; "a resample was attempted" for a derived
metric). Reasoning: `step_summary`/`level_summary` is already the exact dict
`cli.py` writes into `aggregated`/`by_block`, so riding beside the metric it belongs
to needed no new return shape (a tuple return would have broken ~80 existing
`test_stats.py` call sites for no benefit) — it needed `cli.py` to *stop* passing
the dict through unmodified. `cli.py` pops `"pool"` off every block: once, right
after the try/retry `summarize_step` calls converge (covers both, since the retry's
recorded-column-only block carries the key under the same gate), stashed into a new
`pools_by_key[(cond.index, step_name)]` local (sibling of `collapsed_by_key` etc.,
for task 5 to build `Member`s from); and once for the `report_by` level call, popped
and discarded — no `Member` is built for a stratum (existing decision, `reference.md`
§ Reporting strata), so its pool has no consumer.

**Below-floor pool:** carried out, not dropped. Both a structural refusal
(`pool=[]`) and a below-honesty-floor return (`pool=sorted(values)`, `interval=None`)
now travel identically to a live pool — `stats.py` hands the evidence outward either
way and leaves it to the eventual `Member` construction (task 5) to decide what a
pool with no interval is worth, rather than silently losing that case here.

**No-pool-in-record test:** `tests/test_cli.py::test_a_resampled_runs_run_yaml_never_carries_a_pool`
walks a real `run.yaml` asserting no dict anywhere carries `"pool"`, paired with a
must-be-present check (`found_resample_draws`) so it isn't a vacuous absence. Verified
red: temporarily changed the pop to `.get` (leaving the key in place) → `AssertionError:
a pool reached run.yaml: {...}` with the full 500-draw list printed. Reverted, reran →
green (`1 passed`).

**Oracle:** `test_task1_bit_stability_oracle_over_the_correction_machinery` stayed
green before and after every change; never touched.

**Call-site sweep:** the four task-2/3 functions (`percentile_over_units`,
`percentile_over_units_clustered`, `percentile_of_derived`, `percentile_of_derived_clustered`)
are called from exactly 2 sites, both inside `stats.summarize_step` itself — `cli.py`
never calls them directly (it uses the unrelated `paired_percentile_of_derived` for
contrasts). Found 2, changed 0 arithmetic — only `.pool` captured alongside the
already-read `.interval`. `summarize_step` itself is called from exactly 3 sites in
`cli.py` (main try, retry, `report_by` level). Found 3, changed 3.

**Verification run:** new test + oracle green; `tests/test_stats.py` (338 passed);
targeted `test_cli.py -k "resample or report_by or stratum or weighted or clustered or
pool or oracle"` (251 passed); `uv run ruff check .` clean; `uv run ruff format --check .`
clean; `uv run mypy` clean (56 files). Full suite left to the controller per instructions.

**Concerns:** none. `pools_by_key` is populated but not yet read anywhere — expected,
since task 5 owns building `Member` from it.

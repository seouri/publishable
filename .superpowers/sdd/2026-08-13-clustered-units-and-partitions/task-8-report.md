# Task 8 report: `n` gains `clusters`

**Status:** complete. One commit, `ad55d40`. `uv run pytest` 1328 passed + 2 xfailed, 9 of them new
(no baseline figure claimed — I did not measure the pre-edit count, so subtracting is the arithmetic
the ledger has already caught once); `uv run ruff check .` and `uv run mypy` green. `ruff format .`
was not run.

## What was built

- `runner._counts` gains a `clusters` mapping (unit key → cluster id) and adds `n.clusters` when it is
  supplied. **The `_counts` builder H3a left behind does exist**, so all three of `attrition`'s return
  sites — no roster, no recording execution, the accumulating return — get the key from one
  conditional rather than three. `attrition` gains the matching keyword.
- `stats.summarize_step` gains `clusters` and recomputes `n.clusters` **per column**, over the units
  that carried that column. The derived branch inherits the condition-wide figure from `counts`,
  mirroring `effective` exactly.
- `cli.command_run` builds the mapping from `units.clusters_of` when `data.units.cluster_by` is a
  truthy string and a roster resolved, and passes it to all five downstream calls: `attrition`,
  `summarize_step`, the collision-retry `summarize_step`, and the per-stratum `attrition` /
  `summarize_step` pair. `clusters` does **not** join `beside_n`; no document shows a `clustered_by`
  sibling of `weighted_by`.
- Neither `clusters` nor `weights` carries a default on `_counts` now: a fifth return site added later
  must pass both or fail to type-check, which is the only guard against the "two of three sites"
  failure this builder was created for. No test can see that, so it is stated in the docstring.

**Those five calls are all of them.** `grep -n '"n":' src/publishable/*.py` finds four other `n` keys
and none is the four-part mapping: `provenance.units` (`{n, key}`), an `Estimate`'s own `n` in
`run_record`, `repeat_spread`'s per-level `n`, and a repeat level's declared `n` in `sweep.yaml`.
Contrast blocks record `n_paired`, not `n`, and are task 11's. So no `run.yaml` can carry `clusters` in
one block and silently omit it from a sibling.

## Which units `clusters` counts, and why

**The completed units, per column.** Justified from the documents rather than from `effective`'s
precedent: `reference.md` § Clustered units reports the cluster count "as the effective sample size
alongside the unit count", and § Statistical reporting gives `t_over_units_clustered` "df =
clusters − 1". The figure is therefore the df of an interval, and a df is over the units the interval
was computed from — which per column is that column's carriers. Over the resolved roster it would name
a df no interval used, and a reader comparing it against `completed` would be comparing two different
unit sets. It renders as an `int`: § Clustered units' own example is
`n: {resolved: 300, completed: 300, failed: 0, clusters: 10}`.

## One deviation from the brief's interface list

The brief named `units.cluster_count(roster, cluster_by)` and `units.clusters_of(...)`. Neither fits
the two `n` sites, which hold a set of completed keys and a roster-wide membership mapping and have no
roster to hand `cluster_count`. I added **`units.cluster_count_of(membership, keys)`** and refactored
`cluster_count` to go through it, so the codebase still holds exactly one `len({...})` over cluster
ids — one new expression instead of two inline ones at the sites. Membership still comes only from
`clusters_of`. The refactor is verified by behaviour: the full suite, including task 4/5/6's fold-basis,
`k`-bound and partition tests, is green.

## Tests (9 new)

| Test | What it decides |
|---|---|
| `test_runner.py::test_n_has_no_clusters_key_without_cluster_by` | **The regression.** The roster is the clustered one, `cluster_by` is not passed, `n` is exactly the four parts |
| `test_runner.py::test_n_gains_clusters_under_a_clustered_design` | Exact dict equality with `clusters: 2`, asserted against both 3 (resolved roster) and 4 (unit count); every part `isinstance(int)` |
| `test_runner.py::test_every_attrition_return_site_agrees_about_clusters` | All three return sites, with the mirrored no-mapping control at each |
| `test_runner.py::test_clusters_and_effective_are_independent_parts_of_n` | Each part arrives on its own declaration; 2 vs Kish's 3.0 so neither stands in for the other |
| `test_stats.py::test_clusters_is_recomputed_over_the_units_the_column_actually_has` | The ragged column: `pred`'s 2 against `other`'s 3, with `counts` carrying an impossible `clusters: 99` so an inheriting implementation cannot pass |
| `test_stats.py::test_an_unclustered_summary_grows_no_clusters_key` | The regression at the function, both metric shapes, with a value control |
| `test_stats.py::test_a_derived_metric_carries_the_condition_wide_cluster_count` | The derived branch takes the figure from `counts` |
| `test_cli.py::test_an_unclustered_run_grows_no_clusters_key` | **The regression end to end**, over the clustered-shaped roster with `site` declared as an ordinary attribute; needs no bypass |
| `test_cli.py::test_n_gains_clusters_under_a_clustered_design` | A real `run.yaml`: `n == {resolved: 15, completed: 15, ineligible: 0, failed: 0, clusters: 5}` on both metric shapes, plus a regex over every `n` block's **raw text** asserting no `\d+\.\d+` — so `resolved: 15.0` cannot ship. Deliberately unweighted, since `effective` is legitimately fractional |

Fixtures where the two numbers differ, as required: 5 units / 3 clusters / 2 completed clusters
(runner), 3 vs 4 carriers over 2 vs 3 clusters (stats), 15 units / 5 clusters (cli). No singleton-cluster
fixture is relied on anywhere.

**How I tested the `cli` path, and the bypass:** yes, I needed the same one task 5 recorded.
`E-DATA-CLUSTER-UNSUPPORTED` is still live, so the clustered end-to-end test calls task 5's existing
`_without_the_cluster_refusal(monkeypatch)` helper and reuses its `_UNEVEN_CLUSTERS` roster. Nothing
new was retired or bypassed; task 11 still owes retiring that helper.

## Mutation testing

Reverted between each, `__pycache__` deleted, and every revert verified by re-running the suite green
rather than by reading `git status`.

| Mutation | Result |
|---|---|
| `clusters` unconditional (`clusters or {}`) at both surfaces | 149 tests fail, including all three regression tests — the runner one, the stats one, and the `run.yaml` one |
| Count the resolved roster instead of the completed units | 3 runner tests fail (the exact-number ones) |
| Drop the per-column recompute, inherit from `counts` | the ragged stats test fails; nothing else does |

Note on the second: the `cli` positive test does **not** discriminate it — every unit there completes,
so the roster's clusters and the completed units' clusters are the same 5. The runner fixture is what
carries that half.

## Concerns

1. **`n.clusters` is a correct cluster count beside an interval that is not yet cluster-robust.**
   `stats.py` has no `t_over_units_clustered` and `percentile_of_derived` still draws rows, so
   § Clustered units' "as the effective sample size" half is document-ahead-of-code until task 9 wires
   the constructions. The brief scoped me to `counts`, so withholding the key was not the remedy — but
   this is the third declaration in this slice whose effect is delivered in halves across tasks, and
   task 12 should confirm § Mistakes core prevents' *Ignored clustering* row only after task 9.
2. **The cluster mapping is built in `cli` from a roster the run re-resolves**, so a unit carrying no
   value for `cluster_by` raises `E-DATA-CLUSTER-UNKNOWN` from `clusters_of` at that point, outside the
   `try` around `summarize_step`. For `run` the window is closed by `command_run` validating first (the
   same argument the weights comment makes); it re-opens for `draft`/`resume` in H9. This is also a
   second run-time raise site for that code, and task 2's report already recorded that
   `E-DATA-CLUSTER-UNKNOWN` has no § Errors *at run time* row yet — that debt is now larger, not
   smaller.
3. **No document edits were made or, I believe, owed.** § The three-part `n` and § Clustered units
   already state this behaviour, and § The one config file's `NOT BUILT` list correctly still names
   `.cluster_by` (task 12 retires it). Nothing about `cohort-pilot` moved — it declares no `cluster_by`,
   and its `n` blocks are the four parts they were.

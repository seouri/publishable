# Task 9 report: `t_over_units_clustered` — CR1

**Status:** complete. `uv run pytest` (1339 passed, 2 xfailed), `uv run ruff check .`, `uv run mypy` all green.
`ruff format .` was not run.

## What was built

`stats.t_over_units_clustered(values, keys, membership, confidence=0.95) -> Interval | None`.

The model core fits for a `basis: units` column is the mean, so the sandwich is the
intercept-only case: `X'X = n`, cluster score `S_g = Σ_{i∈g}(v_i − v̄)`, and

```
V_CR1 = [G/(G−1)] · Σ_g S_g² / n²      half = _t_critical(G − 1, confidence) · √V
```

with `G = units.cluster_count_of(membership, keys)` — the single counting expression, so
this df cannot disagree with the `n.clusters` printed beside it or with a fold's
partition. `_t_critical` is reused; the grouping reads `membership[key]` (indexed, not
`.get`-ed) and zips `strict=True`.

### The CR1 convention question, answered rather than picked

Two conventions exist: `G/(G−1)` (MacKinnon–White) and Stata's
`G/(G−1) · (n−1)/(n−k)`. **They coincide here**: `k`, the number of fitted parameters, is
1 for a mean, so the second factor is `(n−1)/(n−1) = 1`. There was nothing to choose
between, and the docstring says so.

### Floor

`None` below **two clusters** — CR1 with one cluster has df 0, so 300 cells from one
animal get a point and no interval, which is the honest answer for one draw. The
`len(values) < 2` guard sits in front of it so the two constructions refuse the same
degenerate inputs. Both are tested, and the two-cluster case (df 1, very wide) is the
control that must report.

## How the expectations were built (not from the code under test)

For **balanced** clusters of size `m`, `S_g = m(ȳ_g − ȳ)` and the whole thing reduces to
`s²(cluster means)/G` at df = G − 1 — i.e. exactly `t_over_units` over the G cluster
means. That reduction is textbook, so the headline test's expectation comes from the
already-trusted `t_over_units` over a 10-point fixture whose df is 9 by construction.
10 clusters × 3 units, with units at their cluster mean −1/+0/+1 so the 30 values spread
differently from the 10 means.

The balanced reduction hides two things — the sandwich is centred on the **unit** mean,
and unequal cluster sizes weight clusters unequally — both of which coincide with
"t over cluster means" when sizes are equal. So there is a second, **unbalanced**
fixture (sizes 1, 2, 3) computed by hand and cross-checked against a matrix-form
sandwich written separately in a scratch script: `[−0.94270, 6.27604]`, where the
cluster-mean construction would give `[−2.40353, 9.07020]`.

## Mutations (run separately, `__pycache__` cleared between, reverts verified by test)

| Mutation | Result |
|---|---|
| df from the unit count (`n − 1`, i.e. 29 not 9) | 3 tests fail — the df test (2.2065 vs 1.9949 half-width), the unbalanced hand-computed one, the scaling one |
| `G/(G−1)` finite-sample scaling dropped (CR0) | 4 tests fail, including the dedicated `test_the_finite_sample_scaling_is_in_the_variance` |

Both reverted; the full suite is green afterwards, verified by behaviour.

Under mutation 1 the df test fails at its first assertion, so its two explicit
standard-error assertions were additionally evaluated in isolation against the mutated
module — both fail there, i.e. neither is vacuous. (An earlier draft of that test divided
the standard error back out of the returned interval, which made the mutation assertion
true under every implementation; it now builds the standard error from the ten cluster
means. Recorded rather than quietly fixed, since it is a small instance of the failure
class this task exists to avoid.)

**Order of work:** the implementation was written before the tests, so the two mutation
runs above stand in for the red phase rather than a literal Step 1 → 4 sequence. The
expectations are independent of the module either way — a textbook reduction and a
hand computation cross-checked against a separately written matrix-form sandwich.

## Tests added (`tests/test_stats.py`)

`test_the_clustered_interval_takes_its_df_from_the_cluster_count`,
`..._is_the_cr1_sandwich_over_unbalanced_clusters`,
`test_the_finite_sample_scaling_is_in_the_variance`,
`test_correlated_units_widen_the_interval_against_the_unclustered_one` (secondary
property, with the unclustered interval as the control that must report),
`test_one_cluster_of_many_units_has_no_interval` + `test_two_clusters_still_report`,
`test_the_clustered_interval_needs_two_values`,
`test_one_unit_per_cluster_reproduces_the_unclustered_interval` (labelled as the
coinciding fixture that can see nothing else, which is why it is not the headline),
`test_a_unit_outside_the_membership_mapping_is_not_absorbed`,
`test_the_clustered_interval_honours_its_confidence`.

## Not done here, for task 11

- **Nothing is wired.** `summarize_step` still calls `t_over_units` /
  `weighted_t_over_units`; `clusters` there still only adds `n.clusters`. Every existing
  `t_over_units` result is unchanged, and the worked example (which declares no
  `cluster_by`) does not move.
- **What a caller must pass:** the column's own unit keys — `summarize_step` already
  holds them as `carried`'s first elements, aligned to `values` in one pass — plus the
  roster-wide `clusters` mapping it already receives, passed whole. No pre-resolved
  label vector, so alignment cannot drift.
- `E-DATA-CLUSTER-UNSUPPORTED` in `validate.py` is untouched (task 12).

## Concerns / gaps

1. **`weight_by` + `cluster_by` together has no construction in this module.**
   § Weighted samples says "`cluster_by` still decides the draw when both are declared,
   since a cluster is what's independent and a weight is what it represents" — that
   would be a weighted CR1 (weighted mean, weighted scores), which neither this task nor
   task 11's brief specifies. Task 11 hits it at `summarize_step`'s branch point and will
   have to either build it or refuse the combination.
2. **`_clustered` is a family, not one function.** § Statistical reporting says the
   paired and unpaired contrast forms each take a `_clustered` suffix
   (`paired_t_over_units_clustered`, `welch_…`, the percentile forms resampling whole
   clusters). Only the column form exists after this task; contrasts under a declared
   `cluster_by` remain unimplemented.

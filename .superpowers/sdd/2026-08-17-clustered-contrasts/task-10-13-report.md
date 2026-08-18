# Tasks 10–13 report — clusters threaded into contrasts

**Status: all four tasks complete, all gates clean, `E-DATA-CLUSTER-CONTRAST` still alive (task 14's).**

## Commits

| Task | SHA | Subject |
|---|---|---|
| 10 | `c51e049` | feat: a clustered column contrast takes the cluster-robust paired t |
| 11 | `6b9d8a7` | feat: every reachable contrast cell writes its own method string |
| 12 | `61d95bd` | feat: a clustered member's corrected bound is the clustered construction |
| 13 | `84db48f` | feat: a clustered contrast entry records n_paired_clusters |

## Test summary

Final full-suite run after task 13: **2196 passed, 1 skipped, 2 xfailed** (2179 baseline + 3 + 8 + 3 +
3 = 2196, matching each task's own predicted count). `ruff check`, `ruff format --check` (80 files),
and `mypy` clean after every task.

## Ruling for task 12: does `Member` carry clusters, and how

Yes. `Member` gained `clusters: tuple[str, ...] | None = None`, immediately after `weights`, treated as
**a modifier on `diffs`, not a third kind of evidence** — the identical grounds `weights` already
stands on, and `__post_init__`'s exactly-one-of-`pool`/`diffs` invariant is untouched: `clusters` is
checked in its own block, exactly parallel to the `weights` block, and never enters that rule. Three
checks, mirroring `weights` exactly: never beside `pool` (a clustered percentile pool is already drawn
from whole clusters, so a membership beside one would apply the correction twice); must be the same
length as `diffs` (a mismatched length is a misaligned vector — the failure class that produces a
plausible wrong number rather than an error); and never beside `weights` (the two declarations never
coexist — `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses a weighted-clustered comparison at `validate`, so a
member holding both would be `cli`'s own bookkeeping error). `_corrected_bounds` reads it first among
the three `diffs`-branch arms (`clusters` → `weights` → plain), which is a preference among
mutually-exclusive fields rather than a real tie-break, since `__post_init__` already guarantees at
most one of the two modifiers is present.

## Mutations run (all against the full, unfiltered suite; every revert re-run to confirm restoration)

**Task 10:**
1. Drop `clusters=clusters` → `clusters=None` at `_compute_vs_baseline`'s call site. **BLIND** (2182
   passed) — confirmed as predicted; this is the mutation task 14 must catch through `run`.
2. `if col_clusters is not None:` → `if col_clusters is None:` in the *t* branch. **FAILED** both
   named tests, plus 53 collateral failures suite-wide (every unclustered contrast now calls
   `paired_t_over_units_clustered(diffs, None)` and crashes) — confirmed, branches provably differ.
3. `[clusters[k] for k in col_keys]` → `[clusters[k] for k in sorted(clusters)]`. **BLIND** (2182
   passed) — confirmed as predicted; task 13's ragged fixture later caught this exact mutation.

**Task 11:**
1. `method=` first arm's condition inverted (`"paired_percentile_over_units" if clusters is not
   None...`). **FAILED** exactly the `(False, True, True)` parametrized cell plus
   `test_a_clustered_resampled_contrast_really_drew_clusters`; all 2188 other tests passed — confirmed,
   the table catches the fall-through at the cell.
2. `clusters=(...)` → `clusters=None` at the percentile-arm call. Parametrized test **PASSED**
   unchanged (method string is a separate argument); `test_a_clustered_resampled_contrast_really_drew_clusters`
   **FAILED** on the ci95-inequality assertion — confirmed exactly as predicted.
3. `{k: clusters[k] for k in col_keys}` → `clusters`. **BLIND** (2190 passed) — confirmed as predicted
   (`col_keys` is the whole roster in this fixture, and the construction re-filters by `keys` anyway).

**Task 12:**
1. `if member.clusters is not None:` → `if member.clusters is None:` in `_corrected_bounds`.
   **FAILED** the named test plus 56 collateral failures (every non-clustered member now hits
   `paired_t_over_units_clustered(diffs, None)`) — confirmed.
2. `clusters=(...)` → `clusters=None` at the `Member(...)` construction in `cli.py`. **FAILED** exactly
   `test_a_clustered_contrast_member_carries_its_membership_and_no_pool` on its first assertion,
   2192 others passed — confirmed.

**Task 13:**
1. `cluster_count_of(clusters, base_keys if is_derived else col_keys)` → `cluster_count_of(clusters,
   clusters.keys())`. **FAILED** exactly the ragged test (2 vs 3); the un-ragged clustered test still
   passed — confirmed, the dimension no un-ragged assertion could see.
2. → `len(set(clusters.values()))`. **FAILED** exactly the ragged test — confirmed, the single-counting-
   expression rule is load-bearing.
3. Re-ran task 10's mutation 3 (`sorted(clusters)` in place of `col_keys`). **FAILED** exactly the
   ragged test, on the `zip(..., strict=True)` length mismatch inside `paired_t_over_units_clustered`
   — confirmed as task 10 predicted it would be caught here.

Every mutation was reverted by editing the file back (never `git checkout --`) and every revert was
confirmed by re-running the full suite (2182 / 2190 / 2193 / 2196 as appropriate), not by `git status`.

## Brief/spec vs. code

No disagreement found between the four task briefs, the design spec (including its § Corrections), and
the code as it stood at the start of this session — batch 1 and batch 2 (tasks 1–9, already merged)
had already resolved the constructions (`paired_t_over_units_clustered`, the third `method` string on
`paired_percentile_of_derived`, `E-DATA-WEIGHT-CLUSTER-CONTRAST`, `cluster_count_of`) exactly as tasks
10–13 assumed. Every interface named in the briefs (`clusters_of`, `cluster_count_of`,
`paired_t_over_units_clustered`'s signature, `paired_percentile_of_derived`'s `clusters=`/`method=`
parameters, `command_run`'s local `clusters` variable) matched on inspection with no adjustment needed.
The one deliberate elaboration beyond the brief's literal text: task 11's brief left a placeholder
`ci95 == pytest.approx([0.0, 0.0])  # paste the run's` in its own draft test; I ran the fixture, captured
the real endpoints (`[1.0, 8.0]`), and pasted that instead of leaving a wrong literal in the suite.

## Concerns

None. `E-DATA-CLUSTER-CONTRAST` remains alive through all four tasks — every clustered test in this
batch calls `_comparison_step_blocks` directly, never through `validate`/`run`, per the binding
convention. No config is unblocked by this work (no sentence in this report or the commits claims
otherwise); the no-remaining-core-side-blocker count stays six and the executable count stays three,
unchanged by H4b-2's own framing.

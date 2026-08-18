# H4b-2 tasks 1, 4, 2, 3, 5 — report

## Status: all five complete, committed in order 1 → 4 → 2 → 3 → 5

## Commits

| Task | SHA | Message |
|---|---|---|
| 1 | `3174e5a` | docs: rule the weighted-clustered composition — mint the refusal, do not build the pair |
| 4 | `7a55876` | docs: E-DATA-CLUSTER-DERIVED is re-owned to H4c, and the fact H4b-2 rests on is pinned |
| 2 | `891518f` | docs: a clustered contrast records n_paired_clusters, and no clustered_by |
| 3 | `ee80d51` | docs: a contrast draw that cannot vary reports no interval |
| 5 | `7efece7` | test: pin the allocation-refusal dependency H4b-2's paired constructions rest on |

## Test summary

Baseline confirmed at start: **2159 passed, 1 skipped, 2 xfailed** (foreground, ~132s). Final suite
after all five tasks: **2163 passed, 1 skipped, 2 xfailed** (task 1 +0, task 4 +0, task 2 +1 = 2160,
task 3 +1 = 2161, task 5 +2 = 2163). `ruff check`, `ruff format --check` (80 files), and `mypy`
(45 source files) all clean after every task.

## The three rulings

**Task 1 — weight × cluster composition.** Ruled: **mint `E-DATA-WEIGHT-CLUSTER-CONTRAST`**, a
documented narrow refusal (§ Errors row + § Validation row), not a `-UNSUPPORTED` build-family code.
Do not build `weighted_paired_t_over_units_clustered` / `weighted_paired_percentile_over_units_clustered`.
Grounds: minting is the house move (H3a's `E-DATA-WEIGHT-CONTRAST`, H3b's `E-DATA-CLUSTER-DERIVED`
precedent); no config in the feasibility analysis declares `cluster_by`, so the composition unblocks
nothing measurable; a weighted-clustered *t*'s df comes from the cluster count, not Kish's effective
size, and the two coincide in any fixture not built to separate them. Identifier verified free at
this branch's HEAD (`grep -rn "E-DATA-WEIGHT-CLUSTER" README.md docs/design-principles.md
docs/experimental-designs.md docs/reference.md src/ tests/` → exit 1, no hits); the control sweep for
`E-DATA-CLUSTER-CONTRAST` over the identical file list returned 21 hits, proving the sweep shape can
fail. H4c inherits the composition itself. Built by task 8 (out of this batch's scope).

**Task 4 — `E-DATA-CLUSTER-DERIVED`'s fate.** Ruled: **re-word and re-own to H4c by name; do not
build the clustered derived draw.** The § Errors row's justification ("Temporary, alongside
`E-DATA-CLUSTER-CONTRAST`") dangles once task 14 retires that code, so it needs its own owner rather
than a dangling cross-reference. Measured rather than assumed: under `cluster_by` the whole `derived`
mapping is dropped before it reaches `aggregated`, so `_comparison_step_blocks`' derived branch is
unreachable in a clustered run — this is what makes decision 5's asymmetry hold (every clustered
contrast carries a `_clustered` `method`, so no clustered contrast entry ever needs to disclose
clustering by any other means). Mutation: flipped `summarize_step`'s guard from
`clusters is not None and seed is not None` to `clusters is not None and seed is None`; the existing
pin `test_a_clustered_derived_metric_is_refused_rather_than_drawn` **FAILED** against the full suite
(confirming it discriminates), reverted, confirmed PASS. One deviation from the brief noted below.

**Task 3 — degenerate-draw refusal for the paired percentile family.** Ruled: **build the refusal,
content-based rather than count-based, over the drawable item** (a key when unclustered, a whole
cluster once `clusters` is given) rather than over the stratum key. Documented in § Statistical
reporting: a contrast draw whose every stratum's drawable things carry the same pair of rows reports
`ci95: null` rather than a zero-width interval — same rule the three sibling percentile constructions
already apply, one level up. The live defect's amendment (in `spec-defects.md`, "a stratified paired
draw can publish a zero-width contrast interval") is **amended, not struck** — struck is task 16's
job once code lands at task 9; this task's amendment records that the rule is now specified and
names task 9 as the closer.

## Disagreements between the briefs/spec and the code, found while executing

1. **Task 4's mutation faults one assertion earlier than the brief predicted.** The brief said
   `test_a_clustered_derived_metric_is_refused_rather_than_drawn` must FAIL on
   `assert set(aggregated) == {"pred"}`. It actually failed two lines earlier, on
   `assert "total" not in aggregated` — same underlying cause (the mutant guard prevents the raise on
   every real clustered run, since `command_run` always derives a real `int` seed), stronger
   discrimination, but the brief's predicted failure line is wrong. Also: the mutation additionally
   failed three collateral tests not named in the brief —
   `test_a_contained_aggregate_fault_does_not_downgrade_a_declared_column_resample` and two in
   `tests/test_stats.py` (`test_a_clustered_derived_metric_is_refused_at_this_surface`,
   `test_a_clustered_derived_metric_that_would_not_be_drawn_is_not_refused[no-seed]`). All were
   reverted along with the guard; none required a code change since only the guard was touched.

2. **Task 2's committed prose overreaches on one clause.** § Contrasts now reads (verbatim from the
   brief): *"It is the count the interval's df was taken from, so a reader can check `clusters − 1`
   against the interval rather than take it on trust."* This is true only of the *t*-family
   construction (`paired_t_over_units_clustered`); `paired_percentile_over_units_clustered` is a
   resampling draw with no degrees of freedom at all. The sentence is general over the whole
   `n_paired_clusters` key, which both constructions carry. This is the `CLAUDE.md` § Misreadings
   "comment or docstring claiming a guarantee the code does not provide" shape. Followed the brief
   verbatim per instructions (exact values as given, order as given) rather than silently rewriting
   spec-authored prose mid-task; flagging here for the controller/task 13 or 15 to narrow the clause
   to the *t* form specifically.

## Operational note

A host disk-full condition (`ENOSPC` on `/`, root volume at 98% capacity) occurred mid-task-5, while
the validate.py mutation (inverted `if not group_axes: / continue` guard) was still applied and every
write tool — Bash, Edit, Write — failed to persist. The mutation was reverted the instant a tool call
succeeded again (confirmed by Read immediately before and after). The root cause was accumulated
pytest `tmp_path` artifacts under `/private/var/folders/.../T/pytest-of-joon` (1.3 GB from repeated
full-suite runs); cleared once and re-cleared after the mutation runs. Both task-5 mutations were
then redone from scratch against a verified-clean tree and verified against the full, unfiltered
suite in the foreground, per the slice's mutation discipline. No commit was made while the tree held
an unreverted mutation.

## `E-DATA-CLUSTER-CONTRAST` status

Confirmed alive and untouched by all five tasks — every new/amended test in tasks 3 and 5 asserts it
**alongside** the code it's paired with, never as a total set, per the slice's binding convention.
It retires only at task 14, which is out of this batch's scope.

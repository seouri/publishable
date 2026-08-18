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

## Fix round 1 (review at `ce77241`, `.superpowers/sdd/2026-08-17-clustered-contrasts/task-b1-review.md`)

Both Majors accepted as findings; the rulings underneath both survive. Both Minors that named a
concrete defect (3, 4) closed by documenting or repairing what they named; Minors 1–2, which named
the same test, closed together by deleting the non-discriminating one rather than differentiating it
— the review itself observed that task 15's narrow-rather-than-delete convention makes the surviving
pre-existing test the stronger pin regardless, so keeping both bought nothing.

**Major 1 — the df clause in `docs/reference.md` § Contrasts.** Deleted the sentence *"It is the
count the interval's df was taken from, so a reader can check `clusters − 1` against the interval
rather than take it on trust"* — per `CLAUDE.md`'s "prefer deleting a claim to rewriting it," since
the clause is general over `n_paired_clusters` and `paired_percentile_over_units_clustered` (a
resampling draw, no df) carries that same key. The two sentences on either side of it stand
unchanged and need nothing added. **Verified by:** grepping the four documents, `CLAUDE.md`, and the
feasibility analysis for the deleted phrase and for `"Every clustered contrast"` (Major 2) — no hits;
re-running `tests/test_cli.py::test_the_clustered_contrast_record_key_is_documented`, which checks the
section only for `n_paired_effective`/`n_paired_clusters`/absence of `clustered_by` and does not quote
the deleted clause — pass; full suite after the edit — 2163 passed (before Minor 1/2's deletion, see
below), gates clean.

**Major 2 — task 4's reachability grounds, and § Contrasts' universal quantifier.** Both narrowed,
neither retro-edited into looking like they were always true:

- `docs/superpowers/spec-defects.md`, task 4's entry: appended a `**CORRECTION, fix round 1**` block
  (did not edit the original ruling text) stating the actual disagreement — `_comparison_step_blocks`
  branches on `derived_by_key`, not on `aggregated`, and the two diverge in one reachable state (a
  clustered step whose derived key collides with a recorded column's name, surviving a
  `summarize_step` → `except ContractError` retry that never clears `derived_by_key` /
  `resample_fns_by_key`) — and states plainly that unreachability holds only through `validate`/`run`
  end-to-end and only while `E-DATA-CLUSTER-CONTRAST` stands, naming **task 14** as the owner that
  must re-check the corner when it retires that refusal.
- `docs/reference.md` § Contrasts: narrowed *"Every clustered contrast records a `method` carrying the
  `_clustered` suffix"* to *"A clustered contrast over a **recorded column** records..."*, and added a
  sentence naming the derived-key-collision corner as open and pointing to `spec-defects.md` rather
  than promising a resolution here.

**Verified by:** re-reading the three code sites the review's Major 2 cites
(`stats.summarize_step`'s raise-before-guard ordering, `cli.command_run`'s pre-call assignment of
`derived_by_key`/`resample_fns_by_key`, and the `except ContractError` retry's failure to clear them)
against the current source — all three still hold at this commit; grepping for the deleted universal
phrase (no hits); full suite after the edit — unaffected (doc-only change plus the spec-defects.md
correction), gates clean.

**Minor 1/2 — the near-duplicate test.** Deleted
`test_every_unpaired_comparison_shape_still_earns_the_allocation_refusal` from `tests/test_validate.py`
rather than renaming or differentiating it: it shared the fixture, the config, and (functionally) the
assertion with `test_a_contrast_beside_groups_and_cluster_by_draws_both_refusals` immediately above
it, and the review's own guard-inversion mutation already showed both failing together with no
daylight between them. Added a paragraph to the surviving test's docstring naming it as also serving
as H4b-2 task 5's behavioural tripwire, cross-referencing the two pre-existing tests
(`test_a_generated_cross_arm_comparison_is_refused_and_the_within_arm_one_is_not`,
`test_a_declared_contrast_across_arms_is_refused`) that cover the other unpaired shape (a *generated*
cross-arm comparison, no `cluster_by`) the deleted test's name had wrongly quantified over. Updated
`docs/superpowers/spec-defects.md` task 5's tripwire citation from the deleted test's name to the
surviving one. **Verified by:** re-running task 5's prescribed mutation
(`validate.py`'s allocation guard, `if not group_axes: continue` → `if group_axes: continue`) against
the full, unfiltered suite in the foreground — **86 failed** (one fewer than the review's 87, the
exact delta of the deleted duplicate), the surviving test named in it; reverted by editing the file
back, re-ran — clean. This is a net **-1** test versus the round-0 count: **2162 passed, 1 skipped, 2
xfailed** is the new expected number, not 2163.

**Minor 3 — the `inspect.getsource` pin's scope.** Added one line each to the test's own docstring
(`tests/test_cli.py::test_a_contrast_entrys_paired_flag_is_written_unconditionally_at_every_branch`)
and to task 5's `spec-defects.md` entry, stating plainly that the pin is scoped to one function's
source text and is defeated by extracting either `"paired": True` write into a helper. No behavior
changed; documentation only. **Verified by:** re-reading both edits render correctly; full suite
unaffected.

**Minor 4 — the orphaned weighted paragraph.** Task 2's insertion had put the `n_paired_clusters`
block between the weighted `arm_sensitivity` fence and the paragraph beginning *"Whatever core
weighted moves together..."* — which directly followed that fence before the insertion — so the
paragraph ended up stranded after the new clustered material, and the clustered section's own closing
line (*"the same obligation a weighted entry carries"*) forward-referenced a paragraph that now
appeared textually after it instead of before. Fixed by cutting the paragraph from where the
insertion had stranded it and pasting it back immediately after the weighted fence, ahead of the
`cluster_by` heading — restoring the pre-insertion order and turning the forward-reference back into a
backward one. **Verified by:** `grep -c "Whatever core weighted moves together" docs/reference.md` →
1 (confirms the move, not a duplication); re-running
`tests/test_cli.py::test_the_clustered_contrast_record_key_is_documented` and the mechanical pass
(anchors, duplicate headings, trailing whitespace/tabs, `×` usage) over `docs/reference.md` — clean.

**Full verification, all fixes applied:** `ruff check` clean, `ruff format --check` 80 files, `mypy`
45 source files clean, full unfiltered `pytest` in the foreground — **2162 passed, 1 skipped, 2
xfailed**. `git status --porcelain` empty after commit. No `ENOSPC` this round (3.0–3.7 GiB free
throughout); every mutation reverted by editing the file back and re-verified by re-running, never by
`git status` alone.

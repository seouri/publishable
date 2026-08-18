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

**Correction, appended 2026-08-18 in Fix round 1: the sentence above has the two numbers backwards.**
Per `CLAUDE.md`, three of nine (E1, E2, E5) have **no remaining core-side blocker** — that number is
three, not six — and **six** stay blocked on causes outside H7b/H4b-2 (`io.reuse_from` for three,
`E-DATA-WEIGHT-CONTRAST` for the other three). Both counts are genuinely unchanged by this batch, which
is the claim the sentence above was making; the two labels were swapped against their numbers. Not
retro-edited, per `CLAUDE.md`'s rule for the development record — the paragraph above stands as
written, and this is what replaces it.

**Second correction, appended 2026-08-18 by the controller, withdrawing the one immediately above:
the first paragraph was right and the correction was wrong.** `CLAUDE.md` § Repository status and
`docs/feasibility-llm-growth-studies.md` § Executability on this build both say, at 2026-08-17:
**no-remaining-core-side-blocker goes three → six** — E1, E2, E5 joined by C1, C2, C3 — and **the
executable count stays at three**, the other six blocked on `io.reuse_from`. So the original
sentence's "stays six / stays three" was correct as written. The withdrawn correction also names
**`E-DATA-WEIGHT-CONTRAST` as a live blocker for three configs, and H4b-1 retired it** — the same
paragraph it cites says so.

Recorded rather than deleted because the shape is worth keeping: a **correction that introduced a
worse error than the one it corrected**, and the second error was a claim about *code state* (a
retired refusal still refusing) rather than a swapped label. This is `CLAUDE.md`'s *prefer deleting a
claim to rewriting it* reaching the development record — and it is the second time on this slice that
rewriting a claim re-seeded it. Both counts are, as all three paragraphs agree, **unchanged by this
batch**.

## Fix round 1 — batch 3 review, `task-b3-review.md`

**Major 1 — the df-provenance clause batch 1 deleted from `docs/reference.md` had come back at three
sites.** `cli.py`'s two comments and `test_cli.py`'s docstring for
`test_a_clustered_contrast_entry_carries_its_cluster_count` all claimed or implied `n_paired_clusters`
is the df a clustered interval was computed from — false for the two percentile cells, which have no
df at all. **Deleted the clause at all three sites, kept the surrounding true sentences**:
- `cli.py`'s "the one fact a cluster adds" comment: removed "*or with no count for a reader to check
  `clusters − 1` against*", keeping "a cluster-robust delta beside a `method` that does not say so is
  a declaration accepted whose effect is half delivered."
- `cli.py`'s `cluster_count_of` comment: removed "*so the count printed beside an interval cannot
  disagree with the df inside it*", keeping the single-counting-expression argument, which the
  reviewer verified independently true.
- `test_cli.py`'s docstring: removed "*and it is the count the interval's df was taken from, so a
  reader can check `clusters − 1` against the interval rather than take it on trust*", keeping "§
  Contrasts: the cluster count is a scalar sibling of `n_paired`" — which the reviewer confirmed
  `docs/reference.md:2649-2653` still says, so the citation is now accurate rather than dangling.
  Verified by re-running `tests/test_cli.py` and `tests/test_correction.py` in full (below) — behaviour
  unaffected, comments only.

**Minor 1 — `raw_half` was arithmetic on the test's own literal.** In
`test_a_clustered_members_corrected_bound_is_the_clustered_construction`, replaced the derived
`raw_half = (member.ci95[1] - member.ci95[0]) / 2` with an independent call to
`paired_t_over_units_clustered(diffs, labels)` (imported alongside `paired_t_over_units`), asserting
its half-width against the same `8.763214143637903` — now a check against production code rather than
against the value the test itself constructed `member.ci95` from two lines above. Verified by running
`uv run pytest tests/test_correction.py -k clustered` (1 passed).

**Minor 2 — the report's six/three counts were swapped against their labels.** Corrected by appending
the note above rather than retro-editing the original sentence, per `CLAUDE.md`'s rule for the
development record.

**Minor 3 — four positional locators.** Replaced with what the sibling names or does, not its
position:
- `cli.py`, both "*the guard at the top of this function*" comments (the *t*-branch and the
  percentile-branch method selections) → "*the `E-DATA-WEIGHT-CLUSTER-CONTRAST` guard above*".
- `cli.py`, "*the weighted block beside it*" → "*the `weighted_by`/`n_paired_effective` block above*".
- `test_cli.py`, "*the parametrized table above*" (in
  `test_a_clustered_resampled_contrast_really_drew_clusters`'s docstring) → named the table's own test,
  `test_every_reachable_contrast_cell_writes_its_own_method`.
  Verified by re-running the full suite (below) — comments and a docstring only, no behavioural change.

**Minor 4 — the derived arm writes `n_paired_clusters` beside a null interval, unrecorded for task
14.** Appended a correction to task 14's brief in
`docs/superpowers/plans/2026-08-17-clustered-contrasts.md`, right after its Interfaces block, dated
2026-08-18 and pinned to `e2417d9`: it names the reviewer's finding (a direct call returns
`n_paired_clusters: 3` beside `ci95: None, method: None`), confirms the reviewer's unreachability
grounds (traced the same four-hop chain), and asks task 14 to build an end-to-end derived-metric-under-
`cluster_by` fixture and decide what the record should say. This is the same corner batch 1 already
asked task 14 to re-check (ledger, Major 2 ruling), one hop further in — recorded rather than fixed
here, since fixing it would mean deciding `reference.md`'s record shape without the end-to-end fixture
task 14 owns.

**Minor 5 — one mutation, four threading sites.** Appended a correction to task 10's Mutation 1, at
task 14's own re-run of it (`docs/superpowers/plans/2026-08-17-clustered-contrasts.md`, Task 14 Step
7), naming all four sites the reviewer verified blind together — `_compute_vs_baseline`'s and
`_compute_declared_contrasts`' own calls to `_comparison_step_blocks`, plus `command_run`'s two calls
into those two functions — rather than the two the brief already named. Task 14's brief now says to run
the mutation a third and fourth time at `command_run`'s own two call sites.

**Verification of the round.** `uv run ruff check .` clean, `uv run ruff format --check .` (80 files),
`uv run mypy` clean (45 source files), and `uv run pytest` → **2196 passed, 1 skipped, 2 xfailed** —
unchanged from batch 3's own count, since every fix here is a comment, a docstring, or a plan
correction, none of it behavioural. No mutation was re-run against the corrected code beyond
`test_a_clustered_members_corrected_bound_is_the_clustered_construction`'s own pass/fail, since no
production code changed.

# Tasks 9-12 review

**Reviewed:** `854f0ef` (task 9), `753fb19` (task 10), `982b9b8` (task 11), `95723dc` (task 12),
`f716e22` (report), against `docs/superpowers/specs/2026-08-17-weighted-contrasts-design.md`
including its appended corrections, and `CLAUDE.md`.

## Verdicts

**Spec compliance: PASS.** Decision 2's derived/column split, decision 3's minted `method`
vocabulary, decision 4's corrected bound and decision 5's stratified contrast draw are all honoured
in the code and in `reference.md`. All three planning corrections that bear on this batch are
honoured: task 9 builds `weighted_paired_t_over_units` (correction 2), task 12 routes by direct call
to `_compute_vs_baseline` / `_compute_declared_contrasts` and touches `validate` nowhere
(correction 1), and the § Validation row *Weighted deltas aren't computed* is untouched
(correction 3) — verified by `git diff d8f326d..HEAD -- docs/reference.md`, which changes **three
lines**, none of them that row. `E-DATA-WEIGHT-CONTRAST` is alive: its emit at `validate.py:5023`
is intact and `tests/test_validate.py::test_a_weighted_generated_comparison_is_refused` and
`::test_a_weighted_declared_contrast_is_refused` both pass (run). The discriminating fixture the
design pinned — six units, weights 1/1/1/3/3/3, delta 6.0 vs 8.0, `cohens_d` 1.3416… vs 2.0, Kish
6 vs 4.8 — is used with exact arithmetic at every new assertion; no new assertion is one that
uniform weights would also satisfy.

**Task quality: PASS WITH FINDINGS.** The mutation discipline is real, not claimed: I re-ran four
mutations against the full unfiltered suite and every one behaved as the report describes. The chain
the slice exists to close is genuinely complete and I verified each link by running — `cli` sets
`Member.weights`, `_corrected_bounds` reads them, and the corrected **bound moves** (6.0 → 8.0), not
merely the field. Against that: one branch this batch added ships with its corrected α unpinned by
any test, and two docstrings in the two functions these tasks changed now describe the code that was
there before.

**M1 does not block tasks 9-12 — the code is correct and only the pin is missing — but it must close
before task 13, not after.** Today `_comparison_step_blocks`' `else:` branch is reachable only by
direct call, because `E-DATA-WEIGHT-CONTRAST` stops a weighted config at `validate`. Task 13 makes a
weighted contrast validate-clean, so a weighted config declaring no `resample` then reaches that
branch through `run` — and the unpinned α goes live at exactly the commit that retires the refusal.
That is what makes it a fix round before 13 rather than an assertion to add someday.

## Findings

### Major

**M1 — the weighted corrected bound's α is threaded but unpinned; a discriminating test is available
today.** `src/publishable/correction.py:212`. `_corrected_bounds` passes `confidence=1.0 - level`
into both branches, but the only test over a weighted `Member`
(`tests/test_correction.py:583 test_a_corrected_bound_over_weighted_differences_is_weighted_too`)
calls `corrected_for(..., family_size=1)`, where `1.0 - level` **is** 0.95 — the default. **Verified
by running:** deleting `confidence=1.0 - level` from the *weighted* call only left the full
unfiltered suite at **2159 passed, 1 skipped, 2 xfailed** — completely silent. The same deletion on
the *unweighted* call in the same expression fails **8 tests** (`test_holm_corrects_the_strongest_
member_at_alpha_over_m`, `test_bonferroni_gives_every_member_the_same_level`, five in
`test_cli.py`, one more). So the asymmetry is this batch's, not pre-existing. A weighted corrected
interval could ship at raw α forever and nothing would notice.

This is **not** unpinnable and does not belong to task 13. Verified by direct probe at family
size 2, with weights 1/1/1/3/3/3 over the design's own diffs: the correct code gives
`[1.4426305905416408, 14.55736940945836]` and the mutation gives
`[2.8239563251976074, 13.176043674802393]`. Bumping the existing test's family to two members and
asserting the corrected bound is **wider** than at family size one closes it in one assertion, by
direct call, with no dependence on task 13's `run`-through path.

**M2 — `_corrected_bounds`' docstring now describes the code task 9 replaced, and the task's own
brief instructed the edit.** `src/publishable/correction.py:188-190`: *"A member carrying per-unit
differences re-runs `paired_t_over_units` over them — exact at any α."* Under a weighted member it
re-runs `weighted_paired_t_over_units` — stated correctly in the body comment at lines 203-208 and
contradicted by the paragraph four lines above it. Task 9's brief step 3 says in as many words
*"and extend that function's docstring with the sentence"*; the comment was added and the docstring
was not. Read, not run. This is `CLAUDE.md`'s *"a comment or docstring claiming a guarantee the code
does not provide"*, in the one function the task existed to change.

**M3 — `_comparison_step_blocks`' docstring describes the branch task 10 changed, as it was before.**
`src/publishable/cli.py:815`: *"A recorded column takes `paired_t_over_units` over the per-unit
differences unless `resample_columns` is set…"*. As of `753fb19` a recorded column under a declared
weight and no `resample` takes `weighted_paired_t_over_units` — `cli.py:1053-1058`. The paragraphs
immediately above (lines 800-813, from tasks 6-8) were updated for weighting and this one was not,
so the function's own contract paragraph is internally inconsistent. Read, not run. Task 10's brief
prescribed no docstring edit, which is why this needs saying: the omission is not the brief's, it is
the rule that when you change a guard you re-read its justification.

Neither M2 nor M3 is named in task 14's enumerated sweep list — its six claims are *"no contrast
construction in this build weights at all"*, the `paired_t_over_units`-takes-differences sentence,
the `paired_percentile_of_derived`-has-no-strata sentence, the weighted-`cohens_dz` claim, *"`Member`
has no weights field"*, and § Weighted samples' sentence. Neither of these two sentences is any of
those, so absent an explicit addition they are not scheduled to be caught.

**M4 — task 11 removed the dangling `E-DATA-WEIGHT-CONTRAST` citation from the § Errors table and
left the identical one in the § Validation table.** **Timing, stated first so nobody hunts for a
defect that is not there yet: this is not false at this commit.** Rows 309 and 329 are both present,
so the citation resolves today. It becomes a dangling reference the moment task 13 deletes row 329,
which is the same horizon that justified task 11's § Errors edit — and nothing in task 13's brief
names it. `docs/reference.md:309`, the *Allocation deltas aren't computed* row: *"Unlike *Clustered deltas aren't computed* and ***Weighted deltas aren't
computed***, read per comparison rather than for the whole design"*. Task 13 deletes *Weighted
deltas aren't computed* (row 329), so this is exactly the dangling citation task 11 existed to
remove — and task 11 removed its twin, in `E-DATA-ALLOCATION-CONTRAST`'s § Errors row, in the same
commit. A § Validation row and its § Errors row are one check seen from two ends; one end was fixed.
Task 13's brief says only *"check every count phrase and every row-relative reference near both"*,
which may or may not reach a by-name citation twenty rows earlier in a different table; nothing
names it. Verified by reading both tables in full — *Clustered deltas aren't computed* carries no
such citation, so this is the only site.

### Minor

**m1 — an assertion that cannot independently fail, twice.**
`tests/test_cli.py:10032 test_a_resampled_column_contrasts_member_carries_no_weights` asserts
`pool is not None`, `diffs is None`, `weights is None`. `Member.__post_init__`
(`correction.py:82-87`) raises when `weights` is set beside a `pool`, so once `pool is not None`
holds, `weights is None` follows from the object having been constructed at all — the "assertion
implied by another in the same test" shape. Same in
`test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta`'s
`all(m.pool is not None and m.weights is None for m in members)`. **No coverage gap results**: the
real pin on `cli.py`'s pool guard is `__post_init__`, and task 4's
`test_weights_beside_a_pool_is_refused` / `test_weights_of_a_different_length_than_the_differences_
is_refused` are solid — which is also the honest answer to "a mutation that fails as a `ValueError`
rather than an assertion": that test pins nothing about the guard on its own, and the report should
not be read as saying it does.

**m2 — a test docstring claims a stronger assertion than it makes.**
`tests/test_stats.py:750`, `test_a_weighted_paired_t_is_the_weighted_construction_under_a_paired_
name`: *"Pinned as the half-width ratio against the unweighted one, which no equal-weight
implementation can reproduce."* The assertion is
`(weighted.high - weighted.low) != pytest.approx(plain.high - plain.low)` — an inequality, which
passes under nearly any wrong df, not a ratio. The Kish df **is** pinned, upstream, by
`test_the_weighted_interval_is_the_t_interval_at_kishs_effective_size` and by this file's own
equal-weights oracle, so the risk is a future reader greping for the guarantee and stopping at a
docstring that overstates it.

**m3 — two inaccurate numbers in the record.** Task 12's brief claims the unstratified derived draw
*"reaches 4.33 at this seed and draw count"*; **measured 3.0** when I ran the mutation. The test
still discriminates (the floor is 5.0), so the mutation is sound and only the brief's number is
wrong — the report's own transcript records 3.0. Separately, the report says *"task 12's four new
tests call `_compute_vs_baseline` / `_compute_declared_contrasts` directly"*; there are **three**,
which the same report states correctly two paragraphs earlier ("2 + 3 tests").

**m4 — the deferral is legitimate, but the brief it points at names a different mutation.** The
report defers `command_run`'s `weighted_by=weight_by if weights else None` → `weighted_by=None` to
task 13 and calls it unreachable today. **I checked rather than accepted it**, because a prior batch
made this excuse wrongly: the emit at `validate.py:5023` is gated on `weight_by` being a non-empty
string *and* `comparisons > 0`, the mutated expression is itself gated on `weights`, so its two
branches can only differ under exactly the config the live refusal blocks; `command_run` returns
`EXIT_WRONG` at `cli.py:1420` before any of it; and `cli.py` defines no other executing command
(`command_validate` and `command_run` are the only two) — so there is no `draft`/`resume`/`dry-run`
route around it. The deferral is structurally sound, unlike the `strata=strata` case, which was
threaded regardless of weights. But the report says *"task 13's brief says so"*: task 13's step 5
prescribes `weights=weights` → `weights=None`, not `weighted_by=None`. Its test does assert
`entry["weighted_by"] == "sampling_weight"` (task-13-brief.md:138), so the mutation would in fact be
caught — the claim lands, by a route the brief does not name. Worth naming explicitly in task 13.

**m5 — a live over-claim in the document and the emit, accepted by design until task 13.**
`docs/reference.md:524` and the `E-DATA-WEIGHT-CONTRAST` message both say *"no contrast construction
in this build weights at all"*, which is false as of `753fb19`. This is the mirror image of the
reasoning that moved the § Validation row to task 13 (a document must not deny a live refusal), and
task 14's sweep claim 1 names this exact sentence, so it is owned. Recorded so it is not lost.

## What I verified by running

Baseline first: **2159 passed, 1 skipped, 2 xfailed** (119.64s), and `uv run ruff check .`,
`uv run ruff format --check .` (80 files), `uv run mypy` (45 source files) all clean. Every mutation
below was run in the **foreground** against the **full, unfiltered** suite.

| Mutation | Site | Result |
|---|---|---|
| Derived branch `strata=strata` → `strata=None` (task 12, prescribed) | `cli.py:950` | **FAIL** as named — `test_the_c1_shape_publishes_a_weighted_stratified_vs_baseline_delta`, `assert 3.0 >= 5.0 - 1e-09`. 1 failed / 2158 passed. Decision 5's payoff is genuinely pinned |
| `_corrected_bounds` conditional → bare `paired_t_over_units` (task 9, prescribed) | `correction.py:209-213` | **FAIL** as named — `test_a_corrected_bound_over_weighted_differences_is_weighted_too`, `assert 6.0 == 8.0 ± 8e-06`. **The bound moved**, which is what the spec's named trap asks for. 1 failed / 2158 passed |
| Drop `confidence=1.0 - level` from the **weighted** call only (mine) | `correction.py:212` | **SILENT** — 2159 passed. See M1 |
| Drop `confidence=1.0 - level` from the **unweighted** call only (mine, for attribution) | `correction.py:210` | **FAIL**, 8 tests. Establishes the asymmetry in M1 |
| `else:` branch → bare `paired_t_over_units(diffs)` (task 10, prescribed) + `by`-exclusion removed (task 12, prescribed) — applied together, disjoint expected failures | `cli.py:1053-1058`, `cli.py:906` | **Both FAIL as named** — `test_a_weighted_column_contrast_with_no_resample_takes_the_weighted_t` and `test_a_weighted_report_by_level_mints_no_member_and_no_delta` (`{'auroc','by','prob'} == {'auroc','prob'}`), plus three pre-existing `report_by` tests. 5 failed / 2154 passed |

Also run: a direct probe of `corrected_for` at family size 2 with and without the M1 mutation, giving
the two distinct bounds quoted above.

## Both consistency passes

**Mechanical, run** over `docs/reference.md` as a throwaway script: **0** duplicate anchors, **0**
unresolvable `#anchor`s (including the three in task 11's new § Weighted samples clause), **0**
trailing-whitespace/tab/invisible-unicode lines, and every table row matching its header's column
count — the three apparent mismatches are pre-existing escaped `\|` inside cells, not structure.
Fenced blocks skipped. No `×`/`x` question arises: the three changed lines introduce no
multiplication.

**Cross-document, by reading, and near-vacuous — which is why it is stated rather than left silent.**
The three changed lines add no config field, so § The one config file is untouched and no downstream
`run.yaml` example is invalidated; they introduce no enum comment, no version string, and no worked-
example value (`cohort-pilot`'s numbers appear nowhere in them); nothing moves between declared and
derived; and nothing in `experimental-designs.md` § Mistakes core prevents is implicated, since the
refusal this slice will retire is still in force. The one cross-section claim the edit **does** make
is § Weighted samples' new *"[§ Statistical reporting] names the two weighted paired constructions
and states that split"* — checked at the far end and correct on both halves: § Statistical
reporting's contrast table defines exactly two `weighted_paired_*` rows
(`weighted_paired_t_over_units`, `weighted_paired_percentile_over_units`, `reference.md:2432-2433`,
and no third anywhere in the file), and the paragraph beginning *"A weighted contrast weights a
recorded column and not a derived metric"* does state the split. The *"Four interactions worth
knowing"* paragraph still enumerates four after the replacement clause quadrupled in length — the
count phrase leads a paragraph whose material changed, which is the shape that produced six Majors
in the two prior batches, and here it survives.

## What I verified by reading, not running

M2, M3 and M4; the cross-document pass above; and the `_interval_method_names()` helper, which
**does** parse § Statistical reporting's `| The interval | Is |` tables rather than hardcoding a
list — so task 10's docstring claim that the `method` is *"checked against the document's own
construction tables rather than a second literal"* is accurate, not the overclaim it would be if the
helper held a list.

## What I could not check

- Whether the **record shape** a below-two Kish size produces (`ci95_corrected: null` beside a
  present `weighted_by`) is pinned anywhere — task 9's brief states plainly that it is pinned by
  nothing, and I confirmed no fixture in `test_correction.py` has an effective size below two. I did
  not build one; it is a stated gap rather than a hidden one.
- Anything that requires the refusal to be retired: the `validate`-clean and `run`-through halves,
  and `command_run`'s threading of `weights` / `weighted_by` / `resample_strata`, are task 13's and
  are unreachable at this commit for the reasons in m4.

## Tree state

**Clean.** Every mutation was reverted by editing the file back (`correction.py` by `Edit`,
`cli.py` finally by restoring a pre-mutation copy taken before any edit) — never
`git checkout --`. `__pycache__` was cleared before every run. Both files were confirmed
byte-identical to their pre-mutation copies by `diff`.

**Verified by behaviour, not by `git status`.** Final run after the last revert, `__pycache__`
cleared first:

```
2159 passed, 1 skipped, 2 xfailed in 120.43s (0:02:00)
uv run ruff check .          → All checks passed!
uv run ruff format --check . → 80 files already formatted
uv run mypy                  → Success: no issues found in 45 source files
```

— identical to the baseline taken before any mutation. `git status --porcelain` then shows exactly
one line, `?? .superpowers/sdd/2026-08-17-weighted-contrasts/task-9-12-review.md`: this file, and
nothing else. Its two predecessors (`task-1-5-review.md`, `task-6-8-review.md`) are tracked, so this
one needs `git add -f` when it is committed, per `CLAUDE.md`'s `sdd-workspace` clobber rule.

# H4b-2 tasks 6–9 report

**Status: all four tasks complete, committed, gates clean.**

## Commits

| Task | Commit | Summary |
|---|---|---|
| 6 | `5b9f04d` | `feat: paired_t_over_units_clustered, CR1 over the per-unit differences` |
| 7 | `377fceb` | `feat: the paired percentile draw takes whole clusters, within their strata` |
| 8 | `ac17ece` | `feat: E-DATA-WEIGHT-CLUSTER-CONTRAST refuses the composition H4b-2 does not build` |
| 9 | `69c91f6` | `fix: a paired draw that cannot vary reports no interval, not a zero-width one` |

## Test summary

Final suite: **2178 passed, 1 skipped, 2 xfailed** (foreground, full unfiltered run). Starting
baseline measured at the top of this session was **2162 passed, 1 skipped, 2 xfailed** — one lower
than the spec's stated `2163`/`2159`-lineage numbers, so every "+N" checkpoint below is relative to
this session's own measured baseline, not the brief's absolute figures; the deltas (+3, +4, +4, +5)
match the briefs exactly. `E-DATA-CLUSTER-CONTRAST` is alive and asserted alongside the new
`E-DATA-WEIGHT-CLUSTER-CONTRAST` in task 8's tests, never in place of it. All four gates
(`ruff check`, `ruff format --check` at 80 files, `mypy`, `pytest`) are clean at HEAD.

## An incident mid-session, corrected

A background test run for task 6's mutation 2 was interrupted when I stopped waiting on it instead
of running the suite in the foreground as briefed. The coordinator flagged this. On inspection,
mutation 2 (`plain = t_over_units(diffs, confidence)` instead of delegating to
`t_over_units_clustered`) was still applied in the working tree, uncommitted. I reverted it by
editing the file back, cleared `__pycache__`, and confirmed the revert with a full foreground run
(2165 passed, matching baseline + task 6's 3 tests) before resuming. From that point on every
mutation in this report ran to completion in the foreground before revert and re-confirmation.

## Mutations run (all foreground, full unfiltered suite, reverted by editing the file back)

**Task 6** (3 mutations, all as prescribed):
1. Lexicographic key-order misalignment (`sorted(keys)`) — FAILED as predicted, half-width
   5.971123930019732 exactly.
2. Delegate to `t_over_units` instead of `t_over_units_clustered` — FAILED, half-width 1.9786
   (the unclustered answer).
3. Return `plain` unchanged (no `method` rewrite) — FAILED on `method == "t_over_units_clustered"`.

**Task 7** (4 mutations; mutation 4 recorded as blind per the brief, not run destructively since its
own predicted blindness against the sorted fixture was already established):
1. Draw units instead of clusters — FAILED `test_the_paired_clustered_percentile_draws_whole_clusters`
   (and, as a natural side effect of drawing single-key items everywhere, two more tests that also
   depend on clustering — expected, since the mutation removes clustering, not just from one path).
2. Take one key per drawn cluster (`[:1]`) — FAILED on row count exactly 3, outside {6..18}.
3. Draw each stratum's clusters from the whole pool (`pools = [items]`) — FAILED on
   `set(seen) <= {10, 12, 14, 16}` (18 became reachable).
4. Sorted-`keys` regression mutation — not run; the brief itself documents it as blind against this
   sorted fixture.

**Task 8** (2 mutations, both as prescribed):
1. Drop the weight half of the guard (`and True`) — FAILED
   `test_a_cluster_without_a_weight_draws_only_the_cluster_refusal` (plus, as an expected side effect
   of over-firing on every clustered comparison, several other clustered-family tests).
2. Corrupt the § Errors row's final cell — FAILED with `StopIteration` as predicted.

**Task 9** (3 mutations, all as prescribed):
1. Count instead of content (`len(group) <= 1`) — FAILED all 4 parametrized cases.
2. Key instead of content in `_drawable_content` — FAILED all 4 parametrized cases.
3. Remove the control's content difference (`of["u00"]` back to `3.0`) — FAILED the control test,
   confirming it is a real control.

Every mutation was reverted by editing the file back (never `git checkout --`), and every revert was
confirmed by a full foreground `pytest` run before moving on.

## Disagreements found between the briefs/spec and the code

1. **Task 7's regression test as literally specified is not "already passing."** The brief's
   `test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was` passes one `compute` closure
   as both `compute_of` and `compute_against`. Since both sides draw the identical key sequence, the
   closure is invoked twice per replicate with the same list, so the test's `drawn` accumulator ends
   up twice the length of `expected` (400 vs 200), and the literal test as written **fails**, not
   passes, against the pre-task-7 code. Fixed by giving `compute_of` and `compute_against` separate
   closures, only one of which records — this is a change to the test body, not the construction, and
   after the fix the test does behave as the brief describes (passing before task 7's rewrite, still
   passing after, pinning the RNG-identical claim).

2. **Task 8's brief message text does not satisfy its own test's `"weight_by" in message` assertion.**
   `Collector.error(code, path, message)` stores `path` and `message` separately (see
   `src/publishable/diagnostics.py`), and `messages_by_code` in the test helpers returns only
   `f.message`. The brief's proposed message body never repeats the literal string `weight_by` — it
   relies on the `path` argument (`"data.units.weight_by"`), which the test's `messages_by_code` does
   not see. I revised the message text to explicitly open with
   `` `data.units.weight_by` and `data.units.cluster_by` are both declared beside a comparison, `` ``
   so both literal substrings the test checks for (`weight_by`, `cluster_by`) actually appear in
   `message`.

3. **A stale cross-reference created by task 9's own edit, fixed in the same commit.** Closing the
   `spec-defects.md` entry (per task 9's exact instructions — retitle the heading, append the closure
   paragraph) left an earlier citation at the top of the file (the "contrast path discloses nothing"
   entry, finding 2's re-owning paragraph) quoting the old heading verbatim (`` `OPEN — a stratified
   paired draw can publish a zero-width contrast interval` ``) and asserting "the paired construction
   still has no content-based degenerate refusal at all" — both now false. Neither task 9's brief nor
   the spec's task list (that sweep belongs to task 16, out of this batch's scope) mentions this
   citation, but leaving it pointing at a nonexistent heading with a false claim is exactly the
   orphaned-reference failure mode `CLAUDE.md` names ("Check every paragraph and row your insertion
   moves"). Updated the citation's quoted title and its trailing clause in the same commit as the
   rest of task 9, without touching findings 1/3 or any other part of task 16's scope.

No other disagreements found; task 6's docstring, mutation predictions, and numeric constants all
matched the code and the brief exactly. Task 7's core draw-shape implementation, `clusters`/`strata`
composition, and degenerate-refusal siting in task 9 all matched the spec's prescribed code verbatim.

## Concerns for review

- The three disagreements above are all in test/doc text, not in the four production constructions
  themselves — worth a second look given `CLAUDE.md`'s recorded history of tests that "cannot fail."
- Task 9's fix to the stale `spec-defects.md` citation is a minor scope extension beyond task 9's
  literal brief; flagging it explicitly in case the reviewer would rather it wait for task 16's sweep
  (in which case it should be easy to identify and revert — it is confined to one paragraph).
- `E-DATA-CLUSTER-CONTRAST` remains alive as specified; task 14 is not part of this batch.
- No sentence in any touched file claims this batch unblocks any config; the no-remaining-core-side
  blocker count and executable count were not touched.

## Fix round 1

Review at `.superpowers/sdd/2026-08-17-clustered-contrasts/task-b2-review.md`. Spec compliance
passed outright; quality passed with reservations, all in claims *about* the code. Commit:
`e5e0f17`. Final suite after these fixes: **2179 passed, 1 skipped, 2 xfailed**, all four gates
clean.

### Major 1 — a normative sentence claimed a refusal the per-condition forms do not make

`docs/reference.md`'s "That is the same refusal the per-condition percentile forms already make for
their own draws" (§ Statistical reporting) is false: `percentile_over_units([5.0]*8)` unstratified
still returns `Interval(5, 5)`. Verified by running the exact call before editing anything. Fixed by
deleting the false uniformity claim and adding a paragraph disclosing the asymmetry directly: the
clustered per-condition form and the stratified per-condition form both make the identical
content-based refusal, but the plain unstratified/unclustered per-condition draw does not and never
has, so within one run a constant column can carry `ci95: [x, x]` per condition beside `ci95: null`
on a delta comparing two such conditions. Verified after the edit that the paragraph makes no claim
the running code contradicts.

### Major 2 — the fix went to the symptom; the test doesn't test what broke

Reverted `validate.py`'s `E-DATA-WEIGHT-CLUSTER-CONTRAST` message to the brief's original
continuation form (opens lowercase, no restated `path`). Verified by rendering the diagnostic through
`Collector.render()`: the message now reads as a single continuation of the path line, matching house
style, with no visible duplication. Added a `paths_by_code` test helper (mirroring the existing
`messages_by_code`) to `tests/test_validate.py` and changed
`test_a_weighted_clustered_comparison_draws_its_own_refusal` to assert
`paths_by_code(path)["E-DATA-WEIGHT-CLUSTER-CONTRAST"] == "data.units.weight_by"` — the field that
actually carries the identity — rather than asserting `"weight_by" in message`. Ran the full suite:
2179 passed.

### Major 3 — the sorted-`keys` guard's stated grounds are false

Probed by temporarily disabling the `ValueError` guard (`if False and keys != sorted(keys):`) and
running a shuffled `keys` list under `strata` against the sorted one: **the draw sequences were
identical**, because `pools = [sorted(group) ...]` followed by `pools.sort()` makes the whole
partition a pure function of content, independent of `keys`' incoming order or the first-occurrence
order the old comment claimed the invariance depended on. Reverted the probe immediately after
confirming. Fixed by:
- Rewriting the guard's justification to state the true grounds: the guard is a caller-contract
  assertion (matching `percentile_of_derived`'s own discipline of enforcing rather than silently
  correcting a caller's sortedness contract), not a requirement the relabelling invariance needs.
- Moving the comment from ~40 lines above the guard (between `rng = random.Random(seed)` and the
  `items` construction) to sit directly beside the `if keys != sorted(keys):` raise it explains.
- Correcting the identical false restatement in `tests/test_stats.py`'s
  `test_an_unsorted_key_list_with_strata_is_a_core_defect` docstring.

The guard itself is kept (removing it was not asked for and the review did not call for it), now with
a docstring that says plainly what it buys: nothing for correctness, a caught caller regression
instead. Ran the full suite after the edit: 2179 passed, no test relies on the false claim.

### Major 4 — mutation 4 was recorded blind and is not

Probed (guard/mutation applied only in a scratch run, reverted before continuing): with `clusters=None`
and no `strata`, an unsorted `keys` list is legal (the `ValueError` only fires under `strata`) and
produces a *different* draw sequence from the sorted one. Fixed
`test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was` by reversing the fixture's
`keys` (`keys = keys[::-1]`) instead of using the sorted order `_paired_cluster_fixture()` returns,
and documented why in the docstring. Re-ran mutation 4
(`items = sorted([key] for key in keys)`) against the full unfiltered suite in the foreground:
**1 failed, 2178 passed** — the test now fails exactly where the review said it would. Reverted the
mutation by editing the file back, cleared `__pycache__`, and confirmed with a full clean run (2179
passed) before moving on.

### Major 5 — task 9's residue on `spec-defects.md`

Fixed in the same commit as directed by the adjudication (Major 5 folded into disagreement 3's
paragraph, not reverted). Changed:
- The parent entry's heading: struck the now-false "…and `paired_percentile_of_derived` never got
  the zero-width sweep" clause with a note that this half closed in H4b-2 task 9 (strikethrough
  convention, matching this file's own house style for closed claims elsewhere).
- The re-owning paragraph's citation, correcting the inverted "closes … content-based degenerate
  refusal" clause and restoring the clustered/unclustered dimension it had dropped.
- Finding 2's body: struck "carries none of the content-based degenerate refusals its three siblings
  now have" and "The paired construction has no such check", replacing both with what is true at
  HEAD — the check exists, over `_drawable_content`, covering all four shapes as one expression.
- The closing "Why this is deferred" paragraph's final sentence ("the sweep should finish rather than
  stop at three"), struck and replaced with a closure note.

### Minors

- **Minor 1** (loose `{10, 12, 14, 16}` assertion): tightened to `{10, 12, 14}` (16 is unreachable —
  stratum `B`'s one cluster of 6 always contributes exactly 6, stratum `A` draws 2 clusters with
  replacement from sizes {2, 4} giving {4, 6, 8}, so totals are {10, 12, 14} only) and corrected the
  docstring to say so, with the arithmetic spelled out. Verified in isolation: test passes.
- **Minor 2** (two forward-dangling citations, unrecorded): appended a correction to the plan
  (`docs/superpowers/plans/2026-08-17-clustered-contrasts.md`, task 15's table), per the
  development-record convention of appending rather than retro-editing, naming both sites
  (`docs/reference.md:515` and `src/publishable/validate.py`'s weight-cluster guard comment) so task
  15's sweep will catch them; also rewrote both citations themselves to state their reading directly
  rather than pointing at a sibling block task 14 removes.
- **Minor 3** (unreported brief/code contradiction on temporariness): recording it now — task 8's
  brief step 3 asked the § Errors row to state "its temporariness", while the brief's own header and
  design decision 3 rule the code **outlives** this slice. I followed the correct half (no
  temporariness clause is in the shipped row) but did not flag the contradiction in the original
  report. Flagged here.
- **Minor 4** (sorted-keys guard untested with `clusters`): added
  `test_an_unsorted_key_list_with_strata_and_clusters_is_a_core_defect_too` to `tests/test_stats.py`,
  pinning that the guard fires identically whether or not `clusters` is also given.
- **Minor 5** (the original report's "matched verbatim" overreach): correcting it here — task 7's
  core draw-shape implementation is **not** verbatim the brief's prescribed block:
  `src/publishable/stats.py` carries an `assert clusters is not None` and a three-line comment
  explaining it that the brief's code block does not contain. Both are correct (mypy needs the
  assert to narrow `clusters[key]`'s type, and the "can never fire" claim holds: with `clusters=None`
  every item is a single key, so `strata[item[0]] == rendered` trivially) — this is not a defect, it
  is the original report's prose overstating the match.
- **Minor 6** (slice name/count in a normative row): removed "H4b-2 builds the two unweighted paired
  clustered constructions" from `docs/reference.md:515`'s § Errors row in favor of "The two unweighted
  paired clustered constructions exist in this build," matching that section's own "in this build"
  idiom rather than naming a slice with a count.

### Mutations run this round (all full unfiltered suite, foreground, reverted by editing the file back)

| # | Change | Result |
|---|---|---|
| Major 3 probe | `if False and keys != sorted(keys):` in `paired_percentile_of_derived`, then compared a shuffled vs. sorted `keys` list under `strata` at seed 7 | Draw sequences **identical** — confirms the false grounds; reverted immediately |
| Major 4 re-run | `items = sorted([key] for key in keys)` in the unclustered branch, against the now-unsorted fixture | **1 failed** (`test_the_unclustered_paired_draw_is_the_same_sequence_it_always_was`), 2178 passed — discriminates as predicted; reverted, confirmed clean at 2179 |

All findings closed. Nothing left open from this round.

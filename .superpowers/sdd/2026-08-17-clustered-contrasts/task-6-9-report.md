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

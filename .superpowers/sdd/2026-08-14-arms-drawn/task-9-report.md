# Task 9 report: `random` over whole clusters

## Fold oracle, confirmed both sides

`test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` (`tests/test_units.py`)
passed **before** any change in this task and passed again **after**, unchanged
in body and unchanged in outcome — `_assign_whole_clusters` and `partition_units`
were not touched at all. The sibling requirement holds: nothing shared between
the fold primitive and the new draw primitive except `Unit`, `random.Random`,
and the shuffle-then-sort-descending dealing order they both apply to their own
selection rule.

## What was built

`units.assignment_for`'s `random` branch, when `clusters is not None`, now goes
through a new function, `units._assign_whole_clusters_by_ratio` — **a sibling
of `_assign_whole_clusters`, not a parameterization of it**, per the brief's
decision. `_assign_whole_clusters` deals whole clusters to the *least-loaded*
of `k` **equal** buckets; this one deals them to the bucket **furthest below
its own target share** — `min(counts[i] / weights[i], tie→earlier index)` —
which collapses to the same rule only when every weight is equal. Both shuffle
the cluster order with the axis's own seeded `rng` and then sort descending by
size, for the same reasons `_assign_whole_clusters`'s docstring gives.

An arm the draw allocates no whole cluster to raises `ContractError`
`E-DATA-ASSIGN-LEVELS` — the same code and the same "resolves zero of them"
reasoning `arms_of` and the unclustered `random` path already use, just over
cluster counts (`len({clusters[u.key] for u in roster})`) rather than unit
counts, in the message.

`assignment_for`'s docstring, `DRAWN_ASSIGN_METHODS`'s docstring, and
`ArmPlan`'s field docs were updated to stop describing `random` beside a
declared `cluster_by` as unbuilt/task-9-pending; `stratify_by`'s refusal
(task 12, unrelated) is now stated as applying regardless of whether
`clusters` is given, since that guard sits above the branch on `clusters`.

## The fixture, and why the numbers are what they are

`_five_clusters()` (`tests/test_units.py`) builds 12 units in 5 clusters of
4/3/2/2/1 via the existing `_clustered` helper, per the brief. Two of the
five sizes are equal (2, 2) and the rest are pairwise distinct, so a mutation
that dealt clusters out by the wrong rule, or split one, lands on a size
combination this fixture does not otherwise produce by chance.

**Important finding, recorded in the test docstring rather than silently
worked around**: the brief's stated reason for these sizes — "no subset sums
to exactly half" — does not hold for a 2-arm equal split: `{c0, c3}` (4+2)
and `{c1, c2, c4}` (3+2+1) both sum to 6, a legitimate whole-cluster 6/6
split. I did not change the sizes (`Do not tidy them`), and I did not
silently repeat the inaccurate rationale in the docstring — I said instead
what actually discriminates: a split-cluster mutation is caught by asserting
**per-cluster membership** (every cluster's units land in one arm), not by
size alone, precisely because a 6/6 split is legitimately reachable here and
a same-sized wrong-membership result would slip past a size-only check.
`test_a_clustered_random_draw_keeps_every_cluster_whole` asserts the
structural property directly, then pins the seed-5 realized split as a
secondary, concrete check.

`test_a_clustered_draw_approaches_an_unequal_ratio_as_closely_as_clusters_allow`
uses `ratio: {a: 1, b: 3}` over the same fixture. `_apportion(12, [1, 3]) ==
[3, 9]` (asserted inline as the unclustered contrast); the realized clustered
sizes are **4 and 8**, not 3 and 9 — `c0` (size 4, the largest cluster) is
dealt first under the largest-first rule and lands on `a` (both arms tied at
0 initially, tie breaks to the earlier-declared level), which already puts
`a` one past its target of 3, and no smaller cluster is available to pull it
back down without leaving it short instead. `partition_units`'s docstring
makes the identical argument for folds ("Sizes differ... as even as
indivisible clusters allow... one large cluster sets a floor") and the test
asserts the exact realized sizes rather than the weaker "close to 4:8"
claim.

A third test, `test_a_clustered_draw_the_ratio_apportions_no_whole_cluster_to_is_refused`,
checks the empty-arm refusal directly: one 5-unit cluster over two levels
leaves one arm no whole cluster to receive, and `assignment_for` raises
`E-DATA-ASSIGN-LEVELS` naming the starved level — the "resolves zero of
them" text `arms_of` and the unclustered path use.

One pre-existing test had a false premise once `random` beside `clusters`
stopped raising: `test_a_random_draw_refuses_a_declared_cluster_by` asserted
that very raise. Replaced with
`test_a_random_draw_with_clusters_still_refuses_a_declared_stratify_by`,
which asserts the surviving half of the old test's claim — `stratify_by`
declared alongside `clusters` still raises, via the `stratify_by` guard
(task 12), not a `cluster_by` guard that no longer exists.

## Mutation testing (`__pycache__` cleared between apply and revert; reverts confirmed by re-running the test, never by `git status`)

| Mutation | Test | Mutated | Reverted |
|---|---|---|---|
| Clustered `random` routed through `_assign_whole_clusters(list(roster), len(weights), rng, clusters)` unchanged, ignoring `weights` | `-k clustered_draw_approaches` | 1 failed (`6 == 4` — equal-bucket rule under an unequal ratio) | 1 passed |
| `_assign_whole_clusters_by_ratio` dealt cluster members **one unit at a time**, recomputing the argmin bucket per unit instead of per cluster (splits a cluster across arms) | `-k clustered_random_draw_keeps` | 1 failed (`cluster 'c3' split across arms: {'b', 'a'}`) | 1 passed |
| Fold oracle re-run after both mutations/reverts above | `-k unclustered_draw_is_unmoved` | not touched by either mutation | 1 passed throughout |

## Verification

`uv run pytest` — 1552 passed, 2 xfailed. `uv run ruff check .` — clean.
`uv run mypy` — clean (one `no-redef` on `members` in the two `random`
branches was fixed by naming the clustered branch's dict `clustered_members`
rather than reusing `members`). `ruff format` not run, per instructions.

## Concerns

**Can the clustered draw produce an empty arm? Yes, and it is refused.**
Unlike the unclustered path — where `_apportion` over enough units rarely
zeroes a level unless the ratio is deliberately skewed — a cluster is a
coarser unit of movement: with `k` levels and fewer than `k` clusters, or with
one cluster dominating the roster (the `{c0: 5}` fixture in the third test),
an entire level can receive no whole cluster at all even under an equal
ratio. This is refused with the same code and the same "resolves zero of
them" wording the unclustered path and `arms_of` already use, so the
contract a caller sees — "every declared level is non-empty, or the draw
raises" — is uniform across both paths. Nothing else in this task's scope
changes that story: `validate` still refuses `method: random` outright as
`E-DATA-ASSIGN-DRAWN` (unrelated to clustering), so this refusal is reachable
today only by calling `units.assignment_for` directly, the same reachability
gap task 8's report already recorded for the unclustered path.

I did not touch `docs/reference.md`. § Clustered units already states the
requirement this task realizes ("core computed the partition, so core keeps
it indivisible") in the future tense ("With `method: random` — refused as
`E-DATA-ASSIGN-DRAWN` in this build —"); that sentence is stale relative to
`units.py` now (as it already was after task 8 for the unclustered half), but
`validate` itself still refuses `random` outright, so no reader-facing
behavior contradicts the doc yet. Flagging rather than editing, since the
brief's file list is `units.py` and `tests/test_units.py` only, and the
doc-side resolution presumably belongs to whichever task retires
`E-DATA-ASSIGN-DRAWN`.

## Files touched

- `src/publishable/units.py` — new `_assign_whole_clusters_by_ratio`;
  `assignment_for`'s `random` branch gains a `clusters is not None` path
  before the existing unclustered one; docstring updates to `assignment_for`,
  `DRAWN_ASSIGN_METHODS`.
- `tests/test_units.py` — `_five_clusters` fixture helper, three new tests,
  one existing test rewritten to match the new (narrower) refusal surface.

---

# Review round 1 (commit `b158145`)

The reviewer reproduced both prescribed mutations independently, confirmed
`_assign_whole_clusters` byte-identical across the commit, and probed
whole-cluster integrity over 300 rosters with no cluster split and no unit
lost or duplicated. Three defects found, all the same class: a docstring
claiming a guarantee the code did not (yet) provide.

## 1. `ZeroDivisionError` on a non-positive `ratio` weight — fixed

`_assign_whole_clusters_by_ratio`'s `counts[i] / weights[i]` divided by an
individual weight, unlike `_apportion` (which only ever divides by
`sum(weights)`), so a weight of `0` crashed with a raw `ZeroDivisionError`
rather than staying total and leaving an eventual empty-arm refusal to
`assignment_for` — exactly what the docstring already claimed happened,
falsely. `validate` refuses a non-positive `ratio` value today
(`E-DATA-ASSIGN-RATIO`), independent of the method gate, so this was not
reachable through `run`; it is reachable by calling `assignment_for`
directly, the same reachability shape task 8's report already flagged for
the unclustered path.

**Fixed by guarding, not by narrowing the claim**, per the review's
instruction: a `priority(i)` helper returns `float("inf")` for any
`weights[i] <= 0` instead of dividing, so that level is never the argmin
while another level's weight stays positive, and ends up a size-0 bucket —
which `assignment_for` already refuses as `E-DATA-ASSIGN-LEVELS`, the same
code and "resolves zero of them" wording every other starved-level case in
this file uses. The docstring's total-and-defer claim is now true rather
than aspirational.

New test: `test_a_clustered_draws_zero_weight_level_refuses_rather_than_dividing_by_zero`
(`ratio: {a: 0, b: 1}` over the 5-cluster fixture) — asserts `ContractError`
`E-DATA-ASSIGN-LEVELS` naming `a`, not `ZeroDivisionError`.

**Mutation-proved** (`__pycache__` cleared between apply and revert, revert
confirmed by re-running the test): removing the `weights[i] > 0` guard
(`share = counts[i] / weights[i]` unconditionally) reproduces the exact
`ZeroDivisionError` the guard exists to prevent — 1 failed. Restoring the
guard: 1 passed.

## 2. `_five_clusters`'s false parenthetical — corrected

The reviewer's own earlier correction ("no subset sums to exactly half" was
false) extends to a clause I wrote in the same fixture's docstring: "a
mutation that... lands on a size combination this exact pair of fixtures
does not otherwise produce." False for the same reason — `{c0, c3}` (4+2)
and `{c1, c2, c4}` (3+2+1) are both legitimate whole-cluster combinations
summing to 6, so a split-cluster mutation reaching 6/6 proves nothing by
size alone. Rewrote the docstring to state this directly rather than delete
it silently: a split-cluster mutation *can* reach a size a correct draw also
reaches, which is precisely why the neighbouring test's assertion is
structural (per-cluster membership) rather than size-based. No code change;
`test_a_clustered_random_draw_keeps_every_cluster_whole`'s own assertions
were already correct and unchanged.

## 3. False deviation bound — corrected by removing the claim, not tightening it

`_assign_whole_clusters_by_ratio`'s docstring claimed the realized size
differs from its target share "by up to the size of the largest cluster
assigned to it" — false in the undershoot direction, per the reviewer's
counter-example (`{7,1,1,1}` over three equal-weight levels puts one bucket
at size 1 against a target of 3.33, a deviation of 2.33 while that bucket's
one assigned cluster is size 1).

I did not attempt a corrected, tighter, unproven bound. I replaced the claim
with the same non-promise `reference.md` § Clustered units already states
for folds under unequal cluster sizes ("What is not promised is a bound on
how uneven the result may be") — the honest, already-established position
in this codebase for exactly this situation, rather than inventing a new
guarantee under review pressure.

## Verification after all three fixes

`uv run pytest` — 1553 passed, 2 xfailed (one net new test). `uv run ruff
check .` — clean. `uv run mypy` — clean. `ruff format` not run.

**Fold oracle re-confirmed once more**, after these fixes:
`test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` — 1 passed.
None of the three fixes touch `_assign_whole_clusters` or `partition_units`.

## Minor item (report only, no code change)

The first pass of this report said "`ArmPlan`'s field docs were updated" —
the diff shows no such change was made, and reviewing it now, none was
needed: `ArmPlan.strata`'s docstring already described `random`'s
`strata=()` behavior correctly for both the clustered and unclustered case
without naming task 9 as pending. That sentence in the original report was
inaccurate about what the diff contained; correcting the record here rather
than editing history.

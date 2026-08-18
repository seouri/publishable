# SDD ledger — plan: docs/superpowers/plans/2026-08-17-clustered-contrasts.md

**Spec:** `docs/superpowers/specs/2026-08-17-clustered-contrasts-design.md`, plus its
**§ Corrections against the code** appended during planning. **Scoping:**
`docs/superpowers/H4b-2-SCOPING.md`, dated 2026-08-17 and pinned to `001ed9f` — **18 tasks against
the charter's 7**, the fifth consecutive re-scope to move up.

**Branch:** `h4b2-clustered-contrasts`, from `main` at `82310b9`.
**Baseline, measured in the foreground at `73c34d9`:** 2159 passed, 1 skipped, 2 xfailed; `ruff
check`, `ruff format --check` (80 files), `mypy` (45 source files) all clean.

**Execution order, from the plan:** 1 → 4 → 2 → 3 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 →
15 → 16 → 17 → 18. **It is not numeric**, and the two inversions are load-bearing, not cosmetic.

## What this slice is worth, stated before it starts

**Zero configs unblocked.** The feasibility analysis's only two `cluster_by` hits are both
`cluster_by: null`, verified by grep with a can-fail control. The no-remaining-core-side-blocker
count stays **six** and the executable count stays **three** — both unchanged from H4b-1, measured
2026-08-17 against `001ed9f`.

What it buys instead: a live defect closed (the zero-width stratified paired draw, filed *by* H4b-1
and owned by H4b-2 by name); a documented rule given code — § Statistical reporting's `_clustered`
suffix rule has **no construction behind it** today, and `grep` for one exits 1; two refusals
narrowed and one minted; and a **build-hedged sentence removed from the specification**, which is
its own defect shape here.

Recording this first because H4b-1's retirement commit rounded a refusal-count into an
execution-count and **failed both review verdicts** for it. The number does not move. Nothing in
this slice may say it does.

## Pre-flight conflict scan

### Shared files, by task, in execution order

| File | Tasks |
|---|---|
| `docs/superpowers/spec-defects.md` | 1, 4, 3, 5, 9, 16 |
| `docs/reference.md` | 2, 3, 8, 14, 15 |
| `tests/test_cli.py` | 2, 3, 5, 10, 11, 12, 13, 14, 17 |
| `src/publishable/cli.py` | 10, 11, 12, 13, 15 |
| `src/publishable/stats.py` | 6, 7, 9, 15 |
| `src/publishable/validate.py` | 8, 14, 15 |
| `tests/test_stats.py` | 6, 7, 9, 16 |
| `tests/test_validate.py` | 5, 8, 14 |
| `tests/test_correction.py` | 12 |
| `docs/feasibility-llm-growth-studies.md` | 18 |

No two tasks create the same file. Every shared file is a modify-after-modify, which the per-task
commit boundary and the sequential dispatch already serialize.

### Pairwise: what one produces against what the next consumes

| Pair | Produced → consumed | Found |
|---|---|---|
| 4 → 2 | `E-DATA-CLUSTER-DERIVED`'s fate → whether an **unsuffixed** `method` is reachable | **The reason the order inverts.** If the clustered derived draw gets built, an unsuffixed `method` becomes possible and task 2's "no `clustered_by` sibling needed" argument collapses. Ruling adopted from the spec: **4 before 2**, and task 2 must state which way 4 went |
| 6, 7 → 10, 11 | the two clustered constructions → the `method`-selection branch | A branch cannot select a construction that does not exist. Sequential order already satisfies it |
| 2 → 13 | `n_paired_clusters` documented → the key written | **A record key that code writes and no document names** is the pair `CLAUDE.md` says to grep for. H4b-1 had to mint a whole `method` vocabulary for this reason |
| 8 → 14 | `E-DATA-WEIGHT-CLUSTER-CONTRAST` minted → `E-DATA-CLUSTER-CONTRAST` retired | The weight × cluster combination must land somewhere **before** the refusal that currently catches it is deleted, or that combination falls through to an unclustered number silently |
| 3, 9 → 7 | the degenerate-draw refusal ruled and built → the paired percentile family | 3 rules and documents, 9 builds over all four draw shapes; 7 is the construction they constrain |
| 12 → 14 | `Member.clusters` and the corrected bound → the end-to-end run | H4b-1's exact shape: **a clustered raw interval beside an unclustered corrected one passes every existing test**. Its own decision 4, one axis over |
| 5 → 14 | the H4c gate asserted → the retirement | Both `_comparison_step_blocks` branches write `"paired": True` unconditionally, so two paired constructions suffice **only while `E-DATA-ALLOCATION-CONTRAST` stands**. If that gate lapses unnoticed, this slice's two constructions silently under-serve the unpaired case |
| all → 14 | every test asserting **alongside** `E-DATA-CLUSTER-CONTRAST` | Makes the retirement a one-line deletion per test. If a test resists, something was built wrong |

### Per-task self-agreement

Every task's own text was checked against the code it names rather than against the spec alone —
the plan author found **four disagreements** and appended them to the spec as § Corrections against
the code rather than editing its body. All four change a task's contents:

1. **`paired_percentile_over_units_clustered` is not a function.** `paired_percentile_over_units`
   is a `method=` argument on `paired_percentile_of_derived`, which already serves two spellings —
   so task 7 adds a `clusters` parameter and a third string, not a fourth construction.
2. **The "six-way `method`-selection branch" is two sites, not one** — the *t* arm's `method` comes
   from the construction it calls, the percentile arm's from a `method=` argument. Tasks 10 and 11
   wire them separately and assert all six cells **together**.
3. **The retirement's test surface is larger than the scoping's "six assertions"**, and two of its
   three `src/` comment attributions were wrong. One test locates the § Errors row with `next(...)`
   and would raise `StopIteration` on deletion — it is narrowed, never deleted.
4. **The obvious alignment mutation is blind by arithmetic**, confirmed numerically: reversing the
   label vector maps clusters onto a different partition with the *identical* multiset of residual
   sums (8.763214143637901 against 8.763214143637903). A lexicographic key-order mutation replaces
   it.

**Three further mutations are recorded in the plan as blind, each with the fixture that would catch
it**, rather than prescribed: the roster-order label mutation (task 10, caught by task 13's ragged
fixture), the wider-mapping narrowing (task 11, blind for two independent reasons), and the
sorted-`items` regression mutation (task 7, blind against a sorted `keys` list).

**Ruling: this is the right disposition, not a gap.** H4b-1's briefs shipped **five blind
mutations, one provably unbuildable**, and each cost a review round to discover. A mutation is a
claim; naming one unbuildable *in the plan* is the claim being checked before it is trusted.
**Cost if wrong:** a behaviour left unpinned that a nameable fixture could have pinned — which is
why each is recorded with that fixture rather than merely excused.

## Rulings taken before execution

**Ruling: dispatch in four batches on the spec's own seams, not one task at a time.** 1/4/2/3/5 are
the decisions and documents; 6/7/8/9 the constructions and refusals; 10/11/12/13 the threading and
the record; 14–18 the retirement and its residue. Each batch gets one implementer, one opus task
review, and a scoped re-review of the fixes. **Cost if wrong:** a defect crosses a batch boundary
and is caught by the whole-branch review instead of a task review — which is what the whole-branch
review is for, and which happened once on H4b-1 and was caught.

**Ruling: task 17's regression literals are captured at `82310b9`, before any behaviour changes.**
The plan says a pin whose values are captured afterwards is not one, and it is right: a literal
recorded after the change records the change, not the baseline. **Cost if wrong:** the regression
pin asserts the new behaviour against itself, which is the "assertion implied by another in the same
test" shape.

## Batch 1 — tasks 1, 4, 2, 3, 5 — the decisions and documents — complete, review dispatched

Commits `3174e5a` (1), `7a55876` (4), `891518f` (2), `ee80d51` (3), `7efece7` (5), report `ce77241`.
Suite 2159 → 2163 passed, 1 skipped, 2 xfailed; four gates clean. `E-DATA-CLUSTER-CONTRAST` alive.

**Ruling carried out of task 1:** mint **`E-DATA-WEIGHT-CLUSTER-CONTRAST`** as a documented narrow
refusal — both a § Errors and a § Validation row, not the `-UNSUPPORTED` build family — and do not
build the weighted-clustered pair. Identifier verified free by a sweep with a can-fail control.
**Cost if wrong:** H4c inherits a composition it must build rather than a refusal it may retire.

**Ruling carried out of task 4, and it went the way the ledger's pairwise scan needed:**
`E-DATA-CLUSTER-DERIVED` is **re-worded and re-owned to H4c by name** — not built — on the measured
grounds that **the derived branch is unreachable in a clustered run**. That reachability fact is what
makes task 2's "no `clustered_by` sibling needed" argument hold, so **two tasks rest on it** and the
reviewer was told to verify it by running rather than by reading. **Cost if wrong:** an unsuffixed
`method` becomes reachable and task 2's record-shape argument collapses with it.

**Ruling carried out of task 3:** the degenerate-draw refusal is **content-based over the drawable
item** (key or cluster), documented here and built at task 9. The live filing is **amended, not
struck** — a strike belongs at task 16, since `spec-defects.md` strikes a gap when it *closes*.

**Two implementer disagreements handed to the reviewer rather than accepted here.** Task 4's
mutation fails one assertion earlier than predicted and takes three uncited collateral tests with
it; and **task 2's committed df-clause overreaches beyond the *t* construction to the percentile
one** — a prose over-claim of the exact shape that produced ten Majors across H4b-1's four batches.

**Operational note, recorded because it nearly cost a silent corruption.** The host hit `ENOSPC`
mid-task-5 **while a `validate.py` mutation was still applied**, and every write tool failed. The
implementer did not proceed on an assumption: it confirmed by **reading** that the mutation was
still in place, reverted it the instant a tool call succeeded, and redid both task-5 mutations from
scratch against a verified-clean tree. No commit was made while the tree held an unreverted
mutation. Root cause was ~1.3GB of stale `pytest-of-joon` temp directories. **This is the failure
mode the revert-by-editing and verify-by-re-running rules exist for** — a `git checkout --` here, or
a `git status` check instead of a read, would have destroyed or misreported the state.

### Batch 1 — task review: both verdicts pass with findings; two Majors; fix round 1 dispatched

Review at `task-b1-review.md`. Every mutation the reviewer re-ran **discriminates**, including one
the brief asserted only from its description, and **both implementer disagreements are accurate** —
task 4's mutation reproduced exactly, one assertion earlier than predicted, with exactly the three
collateral tests it named.

**Major 2 is the proxy failure `CLAUDE.md` devotes a section to, and it falsifies the grounds of a
ruling this batch's order was built around.** Task 4 reasoned from `aggregated` and concluded about
a **predicate**: `_comparison_step_blocks` iterates `aggregated` but computes `is_derived` from
`derived_by_key`, and a name in **both** takes the derived branch. `summarize_step`'s
`E-STEP-KEY-COLLISION` raise precedes its cluster guard, `command_run` assigns the two maps before
the call, and the `except ContractError` retry never clears them. The reviewer **verified by
running**: a direct call with a shared name yields `method: 'paired_percentile_over_units'` —
**unsuffixed, the exact case task 2's argument says cannot exist** — carrying `ci95: [0.6, 0.6]`,
which is task 3's zero-width shape into the bargain.

**Ruling: the disposition stands, the grounds do not.** `E-DATA-CLUSTER-DERIVED` stays re-owned to
H4c and unbuilt — that was ruled on cost, not on reachability. What changes is the *argument*: the
filing's grounds and § Contrasts' "Every clustered contrast…" quantifier are both narrowed to what
is true, and the corner is recorded as unreachable end to end **only while `E-DATA-CLUSTER-CONTRAST`
stands** — which makes it a thing **task 14 must re-check when it retires that refusal**, stated
there rather than left to be rediscovered. **Cost if wrong:** task 14 ships a retirement that opens
an unsuffixed-`method` path nobody is watching.

**Major 1 is the df-clause the implementer flagged and deferred; the deferral is refused.** The
sentence generalizes a df provenance over both clustered constructions, and the percentile one is a
**resampling draw with no df**. It sits in the normative document every construction task reads, so
a false claim there propagates into the tasks that read it. Deleted rather than rewritten.

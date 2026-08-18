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

# Task 7 report — the stratified partition

**Status: complete.** Two commits on `h3b-clustered-units-and-partitions`: `21acabb` (`feat: a
declared fold stratification balances the split it was checked against`) and `58adf6a` (`docs: a
stratified split's size spread has two regimes, and its k bound is per-stratum` — a docstring
correction plus one more test, found in review; see the two § below). This report is in neither:
`.superpowers/sdd/` is gitignored.
`uv run pytest` 1319 passed + 2 xfailed (was 1310 + 2); `ruff check` and `mypy` green.
`ruff format` not run (and the repo is not format-clean today — `ruff format --diff` shows
pre-existing rewraps in `units.py` untouched by this task, so format is not a gate here).

No `*.md` edited, so no cross-document pass was owed. `cohort-pilot` declares neither `cluster_by`
nor a fold `stratify_by` and nothing about it moved.

## What landed in `src/publishable/units.py`

- **`_assign_whole_clusters(units, k, rng, clusters)`** — task 4's rule lifted verbatim into one
  function: group in the given order, shuffle cluster names with the passed RNG, stable-sort by
  descending size, assign each whole cluster to the currently-smallest fold by unit count. The whole
  roster reaches it once when nothing is stratified; each stratum's units reach it once when
  something is. **One rule, one place** — a separate stratified assignment would be a second answer
  to "which units land together", the near-miss class this slice keeps hitting.
- **`partition_units(roster, k, digest, clusters=None, strata=None)`** — with `strata`, units are
  grouped by stratum in roster order, each group partitioned by the rule above off the *same* RNG in
  that order, and the per-stratum folds merged **index-wise**: fold `i` is every stratum's fold `i`.
- **The `clusters is None` branch is gone, collapsed into the degenerate case**, and this is the one
  judgement worth reading twice. It is an identity, not an approximation: `random.shuffle` permutes
  by index and reads only `len`, so shuffling the one-name-per-unit list draws the same permutation
  as shuffling the units; the descending-size sort is stable over all-size-1 items, hence the
  identity; and least-loaded assignment of size-1 items is round-robin, which is `shuffled[i::k]`
  term for term, including within-fold order. Proved by probe before the edit (five (n, k) pairs
  byte-identical) and pinned by `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite`,
  which is untouched and green.
  - **Why collapse rather than keep two paths:** it is what makes the brief's step-5 wording true.
    With one shared rule, the *split-a-cluster* mutation fails **task 4's** no-split test as well as
    the new stratified one. Keeping a separate unclustered branch would have confined that mutation
    to stratified code, and step 5 would have been unsatisfiable as written.
  - The precondition it widens: the unclustered path now keys a dict by `unit.key`, so it assumes
    key uniqueness. `E-UNITS-KEY-DUPLICATE` guarantees that at resolution, and the docstring says so
    rather than leaving it implicit.
- **The docstring states the interaction the brief asked for**: unit-count balance and
  stratum-proportion balance are independent objectives that two greedy passes would fight over;
  what dissolves the conflict is that a cluster carries exactly one stratum value, **because
  `stratum_varies_within_cluster` refuses the pair otherwise** (`reference.md` § Validation, *Fold
  strata survive clustering*). It says in those words that a later slice removing that check breaks
  this composition silently.

## The contract change nobody had flagged: fold sizes can differ by more than one

Two regimes, and the first draft of this report got the second wrong:

- **Equal-sized things inside each stratum** (every unclustered roster; each unit a cluster of one):
  each stratum's fold list comes out non-increasing, so fold 0 collects **each** stratum's ceiling.
  Three strata of three units at `k = 2` gives **6 and 3**, not 5 and 4 — spread bounded by the
  number of strata. Pinned by `test_stratified_fold_sizes_can_differ_by_more_than_one`.
- **Unequal clusters: no bound at all.** Task 4's "as even as indivisible clusters allow" applies
  **per stratum**, and the floors add. `test_no_cluster_is_split_across_a_stratified_fold` is two
  strata at `k = 2` and lands **10 and 5**. Nor is a per-stratum vector necessarily non-increasing:
  clusters 3/2/2/2 at `k = 3` gives 3/4/2 — the same fact the sorted-merge mutation turns on.

Both are the prescribed rule's consequence, not defects: evening the totals out is exactly what
would divide a stratum's share unevenly. The docstring now states both regimes with both numbers,
against the at-most-one it claims for an unstratified split.

## A second gap the fixtures nearly hid: `k` is bounded globally, stratification makes it per-stratum

`validate` bounds `k` by `fold_basis` over the **whole roster**. Once each stratum is partitioned on
its own, a `k` inside that bound can exceed some *stratum's* cluster count — and then that stratum
reaches fewer than `k` folds and a fold holds **none** of it, while § Repeat kinds still calls the
fold stratified. Probed and pinned: 6 clusters (`A` 4, `B` 2) at `k = 3` validates cleanly and gives
`[{A:4,B:2}, {A:2,B:2}, {A:2}]` —
`test_a_k_past_a_single_stratum_leaves_a_fold_holding_none_of_it`. The partitioner stays total and
visibly short of a stratum rather than dividing a cluster, matching
`test_more_folds_than_clusters_leaves_folds_empty_rather_than_raising`'s stance. **Neither `validate`
nor `fold_basis` was changed** — see concern 7.

## The fixture check that decided the headline test

**The brief's own 8/4 fixture is coincidence-prone in the digest, not in the sizes.** Probed first:
at `k = 2` over 8 `label=0` + 4 `label=1`, the *unstratified* draw lands 4/2 in both folds under
digest `sha256:abc` **and** under `"d"` — the two digests every neighbouring test in the file uses.
Written against either, the proportion test would have passed against a partitioner that ignored
`strata` entirely. Under `sha256:0000` the unstratified draw is 3/3 and 5/1, so that is the digest
used, and the control pins those exact counts. Both facts are in the test docstrings.

## Tests (9 new in `tests/test_units.py`, all carrying `stratum`/`stratif` so `-k stratum` runs probe beside control)

| Test | Asserts (exact, never a direction) |
|---|---|
| `test_each_fold_gets_a_proportional_share_of_each_stratum` | sizes `[6, 6]`, and each fold `label=0` → 4, `label=1` → 2 |
| `test_an_unstratified_draw_of_the_same_stratum_fixture_is_lopsided` | the control that must report: same roster and digest, no `strata` → `[{0:3,1:3},{0:5,1:1}]` |
| `test_one_stratum_over_the_whole_roster_is_the_unstratified_draw` | 50 units, one stratum, `k = 5` → same units, same folds, same order as no `strata` |
| `test_no_cluster_is_split_across_a_stratified_fold` | clusters 7/3 in `A`, 3/1/1 in `B`, `k = 2` → no cluster spans two folds, 15 units land once each, composition `[{A:7,B:3},{A:3,B:2}]` |
| `test_the_clustered_stratified_split_pins_which_fold_each_cluster_lands_in` | `A` in 3/2/2/2, `B` in 5/1/1/1/1, `k = 3` → exact cluster membership per fold and `[{A:3,B:5},{A:4,B:2},{A:2,B:2}]` |
| `test_stratified_fold_sizes_can_differ_by_more_than_one` | 3 strata × 3 units, `k = 2` → `[6, 3]`, each fold 2/2/2 then 1/1/1 |
| `test_a_k_past_a_single_stratum_leaves_a_fold_holding_none_of_it` | `fold_basis` 6, `k = 3`, stratum `B` with 2 clusters → `[{A:4,B:2},{A:2,B:2},{A:2}]` |
| `test_the_same_digest_reproduces_the_same_stratified_split` | same digest twice → identical keys per fold |
| `test_a_unit_missing_from_the_stratum_mapping_is_a_core_defect` | `KeyError`, mirroring `clusters` — no `.get` default inventing a stratum |

Every clustered fixture is built so each cluster sits wholly inside one stratum, which is precisely
what task 6's check guarantees of a validated config — the fixture encodes the precondition instead
of assuming it.

## Mutations (four, separately; `__pycache__` deleted between each mutation and its revert; every revert verified by re-running the named tests, and the final state by `diff` against the pre-mutation copy plus the full suite — never `git status`)

| Mutation | Result |
|---|---|
| **Drop the stratification** — `if strata is None or True` | **FAIL**, 5 tests: the proportion test, the stratified no-split test, the composition pin, the size-spread test, and the missing-key test. The control (`…is_lopsided`) and the byte pin **passed** — they describe the unstratified draw, which the mutation restores |
| **Merge sorted by size** (descending, the mirror of task 4's own sort) instead of index-wise | **FAIL, exactly one test**: the composition pin. Nothing else could see it — see below |
| **Split a cluster while stratifying** — assign unit-by-unit inside the cluster loop | **FAIL**, 5 tests, including **task 4's** `test_no_cluster_is_split_across_folds` and the new `test_no_cluster_is_split_across_a_stratified_fold`. The unclustered byte pin still passed, as it must: round-robin over singletons is unchanged |
| **Stratify but ignore `clusters`** — pass `None` into the per-stratum assignment | **FAIL**, 2 tests: the stratified no-split test and the composition pin. Task 4's no-split test passed (it declares no `strata`), which is why the new one had to exist |

### The sorted-merge mutation: what can and cannot kill it, as a proof

The brief asked for a fixture where sorting unbalances the strata, **or** the reason it cannot fail.
Both halves have an answer, and the honest one is not "unbalances":

1. **Sorting cannot change any stratum's multiset of piece sizes** — it permutes that stratum's
   pieces among folds. So no assertion about how much of a stratum exists, anywhere, can see it.
2. **On every unclustered or equal-cluster fixture it is the identity.** The greedy emits a
   non-increasing size vector whenever all items within a stratum are the same size, so a descending
   sort is a no-op. That covers the brief's own 8/4 fixture: **no assertion of any kind could
   distinguish the mutation there.** Confirmed empirically — the proportion test passes under it.
3. **It becomes visible only when unequal clusters inside a stratum produce a non-monotone vector.**
   Computed rather than hand-reasoned: `A` in clusters 3/2/2/2 at `k = 3` gives **3/4/2**. Merged
   index-wise against `B`'s 5/2/2 the folds are `(A3,B5) (A4,B2) (A2,B2)`; sorted they are
   `(A4,B5) (A3,B2) (A2,B2)` — a genuinely different pairing, not a relabelling of folds.
4. **But sorted is not worse balanced there — it is marginally better.** `A`-fractions 4/9 and 3/5
   against index-wise's 3/8 and 4/6, on a roster whose mix is 1:1. So the test pins it on the
   **contract** ("which fold a unit lands in is a function of the digest", already task 4's stance)
   and its docstring says exactly that, rather than claiming an imbalance that is not there. Pinning
   it as a balance failure would have been one more check that cannot discriminate.

The brief's step 2 ("run the new test, confirm it fails") was discharged by mutation 1 rather than by
reverting the implementation: `if strata is None or True` *is* the pre-implementation partitioner,
and it fails the four new behavioural tests.

## Concerns / obligations for later slices

1. **Task 11 must build the `strata` mapping, and `clusters_of` is not it.** `partition_units` takes
   the mapping; nothing in `src/` builds one yet, and `cli.py:796` still calls
   `partition_units(roster, fold_level.n, digest)` with neither argument. `clusters_of(roster,
   stratify_by)` computes the right shape but raises **`E-DATA-CLUSTER-UNKNOWN`**, which would
   misname the block a reader has to edit; a `strata_of` was deliberately *not* added here, since
   the code it should raise belongs to whichever declaration the caller is serving
   (`fold.stratify_by` now, `holdout`/`assign` in H3c/H3d).
2. **The mapping must be total, and task 6's concern 4 is why that is not automatic.** A cluster
   whose units *all* carry no stratum value passes validation silently, so a validate-clean roster
   can hold units with no value for the stratum attribute. A builder that skips them will `KeyError`
   here. Whether such a unit gets a stratum of its own or a refusal is a decision to make where the
   attribute is read; the docstring says so and this report makes it task 11's obligation.
3. **Task 6's concern 2 is now half-closed.** § Repeat kinds' "`fold` | data partition — k-fold,
   **stratified**" row is backed by code as of this commit; the *declaration* stays refused by
   `E-REPL-FOLD-STRATIFY-UNSUPPORTED` until tasks 11 and 12. Nothing in the docs was touched — the
   NOT BUILT comments and the § Validation rows are still task 11's.
4. **No `-UNSUPPORTED` code was touched**, no `cli` wiring done, and `_fold_k` is unchanged.
5. **The at-most-one spread is now conditional**, per § above. Any later reader of
   `partition_units` (H3c's cells, H3d's uneven two-way split) inherits that: a cell-aware or
   holdout partition composed the same index-wise way will inherit both regimes, and H3d's
   *unequal* target sizes will need to be applied per stratum, not to the merged result.
6. **`validate` has no per-stratum `k` bound**, and the pinned behaviour above is what a config
   inside today's bound gets: a fold holding none of a stratum. Whoever owns the § Validation rows
   (task 11, then any slice adding `holdout.stratify_by`) should decide whether *Folds fit inside the
   clusters* wants a stratified sibling — "`k` fits inside the smallest stratum's cluster count" —
   because the current message would tell a reader their `k` fits when the split it produces is not
   stratified in any useful sense. Not changed here: this task owns the partitioner, not the checks.
7. **The brief was accurate.** Its one soft spot was the 8/4 fixture's digest, which it left to the
   implementer and which the probe in § above resolved; its instruction to consider that the sorted
   merge might be unkillable was right for the fixture it proposed, and only a clustered fixture
   with unequal cluster sizes makes it visible at all.

# Task 10 review — the stratified × clustered composition rule

Reviewed `4f62117..3af1e5a` (impl `97c911c`). Tree left clean at `3af1e5a`: **1748 passed + 2 xfailed**,
`uv run ruff check .` and `uv run mypy` clean. Only `progress.md` modified (the requester's).

**Spec compliance: ✅**
**Task quality: findings** — 3 Important, 3 Minor. Nothing wrong with the number the construction
produces; three dimensions of it are unpinned, one of them silently discarding `weight_by`.

---

## Confirmed first: the implementer's mutation finding is correct, both halves

- **The brief's width-ratio test is blind to `range(len(group))` → `range(1)`.** Reproduced: under that
  mutation `test_a_clustered_stratified_draw_takes_clusters_within_strata` **passes**. The stated cause
  is right — the fixture's percentile endpoints are single-cluster means, reachable identically whether
  a stratum draws one cluster or two, and the `plain` comparator degrades in the same direction.
- **The `_CountingRandom` spy genuinely catches it, and is not vacuous.** Under the mutation it fails
  `6000 == 12000`. It is insufficient alone (a draw that ignored strata entirely would also spend
  12000 calls) but the pair is jointly discriminating: mutating `stratum_pools = [ordered]` unconditionally
  fails the width test. Correctly diagnosed and correctly repaired.

## The statistics are right

- **Independent reference implementation matches to the digit.** I wrote a textbook stratified cluster
  bootstrap from the spec sentence (within each stratum *h* holding `n_h` clusters, draw `n_h` clusters
  with replacement; pool units; ratio-type mean), with its own canonical ordering and its own seed, at
  200 000 draws. Impl `[16.810666666666666, 30.274666666666667]`; reference **identical**. Sample mean
  23.54 sits inside it.
- **Composition verified directly, not inferred.** Instrumenting the real draw loop (via the weighted
  branch) over 500 replicates: **500/500 hold exactly 2 clusters from each of `low`, `mid`, `high`**;
  27 distinct cluster multisets = 3 per stratum cubed, as expected.
- **All three candidates are different numbers, and the theory direction is right.**
  clustered-stratified width **13.46** · clustered-only **57.30** · stratified-rows **0.26**. Stratifying
  narrows against clustered-only (between-stratum variance dominates ✓); clustering widens against
  stratified-rows (within-cluster correlation is total here ✓). Swapping for clustered-only fails the
  width test; swapping for row-level stratification fails the spy (30000 calls ≠ 12000).
- **Degenerate case is pinned in the correct direction** — `is None` for one-cluster-per-stratum,
  `is not None` for the two-cluster companion. No repeat of task 9's inverted zero-width pin. Guard
  mutated to `if False` → the degenerate test fails, as reported.
- **Task 1's regression pin holds; the change is purely additive.** 200 randomized fixtures (varying n,
  cluster counts, with and without weights) through both `3af1e5a` and `4f62117` versions of
  `percentile_over_units_clustered` with `strata=None`: **every interval digit-identical**. Deterministic
  across repeat calls, invariant to row order and to stratum relabelling.
- **`stats.py` gained no import.** Import block unchanged. (Note for the record: `stats.py` is *not*
  import-free of `units.py` today and was not before this task — it already imports
  `cluster_count_of, usable_weight`. Nothing new was added, which is what the constraint was protecting.)
- **Docs mechanical pass clean.** Three rows added (§ Validation, § Errors `validate` reports, § Errors
  core raises); each 2 columns matching its header, no trailing whitespace, tabs or invisible unicode,
  `#clustered-units` resolves. No count phrase near an insertion is invalidated — the nearest ("those six
  are core checking its own work", "Four interactions worth knowing") count things this diff does not
  touch. No row located by position.
- **`validate` half is real** — neutering `stratum_varies_within_cluster(...)` → `None` fails the negative
  test while the positive companion still passes.

---

## Important

**I-1. `weight_by` is silently discarded on the stratified clustered path, and no test can see it.**
The new `by_stratum` build re-sorts the `(value, weight)` pairs twice more before the draw — exactly the
re-pairing shape this function's own docstring warns about. Mutating the build to drop the weight:

```python
by_stratum.setdefault(cluster_stratum[cluster], []).append(sorted([(v, 1.0) for v, _ in pool]))
```

**the entire suite passes — 1748 passed + 2 xfailed.** The mutation is not a no-op: with a real weight
vector the interval moves from `[15.462, 24.972]` to `[16.811, 30.275]`, a ~40 % change in width and a
different point of support. No test added by this task passes `weights=`, and `weight_by` + `cluster_by` +
`stratify_by` are independently declarable, so the intersection is reachable. Add one weighted stratified
clustered test that would move if a weight were dropped or re-paired.

**I-2. The per-stratum cluster count — the load-bearing claim — survives being destroyed.**
Replacing `for _ in range(len(group))` with `for _ in range(len(stratum_pools[0]))` (every stratum draws
the *first* stratum's cluster count instead of its own) **passes all 1748 tests**. The docstring promises
"Each stratum contributes exactly as many CLUSTERS as it holds", and tasks 13–15 build on it. The fixture
holds 2/2/2 clusters per stratum, so the allocation across strata is invisible; the spy pins only the
total (12000). Corroborating evidence of the same fixture saturation: seeds 13 and 14 give the *identical*
interval on this fixture, so no seed-sensitivity assertion could discriminate either — which is the same
coarseness that made the brief's own mutation blind.

Do **not** fix this by reshuffling the fixture to 3/2/1 — `stratum_pools[0]` is whichever group sorts
first *by content*, so an unequal layout can still total 6 and stay blind. The order-independent fix is a
**per-stratum composition assertion**: capture each replicate's drawn pool and assert every replicate
holds each stratum's *own* cluster count. That is mutation-proof by construction, and it is the check I
ran by hand to verify the behaviour in the first place.

**I-3. A zero-width 95 % interval is reachable on the stratified clustered path.**
The new guard is count-based (`all(len(group) < 2 ...)`); its cited peer in `percentile_over_units` is
content-based (`all(len(set(group)) <= 1 ...)`). Content-identical clusters within every stratum therefore
report rather than refuse:

```
strata A: c0=[1.0], c1=[1.0];  B: c2=[0.0], c3=[0.0]   →  Interval(low=0.5, high=0.5)
```

which is exactly what § Statistical reporting calls not honest, and which the row-level sibling returns
`None` for. This is **inherited, not a regression** — the unstratified clustered path has the same hole at
`G = 2` with two identical clusters (verified: `Interval(1.0, 1.0)`) — but stratification makes it much
easier to reach, since any partition into content-identical groups triggers it, and a binary per-unit
metric over singleton clusters is the everyday case. One-line fix mirroring the sibling: test each group's
set of pool contents, not its length.

---

## Minor

**M-1. The docstring cites a peer strictly stronger than what it implements.** "the same … refusal
`G < 2` and every-stratum-identical both already give" — the count-based guard is a weaker test than
`every-stratum-identical` (see I-3). The sentence's own scoped claim ("when every stratum holds fewer than
two clusters, no draw can differ") is literally true, so this is a wording fix, not a false guarantee:
name the sibling it actually matches (`G < 2`) and drop the parity with the content-based one, or close
I-3 and keep the sentence.

**M-2. The positive rule lives only in a docstring.** The three doc rows state the *refusal*; nothing in
the four documents says what the interval **is** when both are legally declared — a cluster drawn within
its stratum, each stratum keeping its own cluster count. § Weighted samples' "Four interactions worth
knowing" spells out `cluster_by` × `weight_by` in exactly that positive form and is the natural home;
§ Clustered units' `resample` bullet is the other candidate. Tasks 13–15 wire this, so the behaviour a
legal declaration produces is currently specified in code only.

**M-3. `validate` and `stats` compare stratum values differently.** `units.stratum_varies_within_cluster`
compares `str(value)`; the run-time check compares raw values. A cluster carrying `1` and `"1"` passes
`validate` and raises `E-STATS-RESAMPLE-STRATIFY-VARIES` at run time. Narrow — CSV attributes arrive as
strings — but the two halves of a dual listing should agree on what "differs" means.

*(Not filed: the constancy check sitting after the `len(values) < 2` / `draws` / `groups < 2` early
returns, so a varying stratum on a degenerate input is silently `None` rather than refused. The brief
specified that insertion point and it matches `checked_weights`' placement.)*

---

## Method

Mutations applied where the behaviour lives, `__pycache__` cleared before every run, every revert an
in-place restore from a pre-mutation copy (never `git checkout`) and verified by re-running the affected
tests. Mutations run: `range(len(group))→range(1)`; `range(len(group))→range(len(stratum_pools[0]))`;
`stratum_pools=[ordered]` unconditionally; degenerate guard `→ if False`; weights dropped in the
`by_stratum` build; `stratum_varies_within_cluster(...) → None` in `validate`. Independent reference
implementation and the composition instrumentation were written from the spec sentence, not from the
implementation.

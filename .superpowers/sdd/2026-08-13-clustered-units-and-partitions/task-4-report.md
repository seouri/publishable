# Task 4 report: `partition_units` draws whole clusters

**Status:** complete. `uv run pytest` (1272 passed, 2 xfailed), `uv run ruff check .`, `uv run mypy` all green.
`ruff format .` was not run.

## What changed

`src/publishable/units.py` — `partition_units` gains `clusters: dict[str, str] | None = None`,
the mapping `clusters_of` returns. It is passed in, never re-derived: cluster membership stays
the single authority task 2 built.

- `clusters is None` → the existing three lines, untouched. Same shuffle, same `shuffled[i::k]`.
- otherwise → group the roster into clusters in roster order, shuffle the **cluster names** with
  the same digest-seeded RNG, `sort(key=-size)` (stable, so the shuffle survives within a size),
  then extend the currently-smallest fold with each whole cluster.

No caller changed. `cli.py` still calls the three-argument form and gets today's behaviour; wiring
`data.units.cluster_by` through to the fold step is a later task's. `_fold_k` untouched;
`E-DATA-CLUSTER-UNSUPPORTED` untouched.

### The docstring's promise, weakened only where it must be

The advisor's correction, and it is right: the brief says the "sizes differ by at most one" claim
becomes *as even as indivisible clusters allow*, but that weaker sentence is false-by-omission on
the unclustered path, where the stronger guarantee still holds and
`test_partition_sizes_differ_by_at_most_one` still pins it. The docstring now states both, each
against its own condition — at most one when `clusters is None`, as even as indivisible clusters
allow when it is not — rather than replacing a true claim with a vaguer one.

The assignment order is documented as contract, with both halves' reasons: the shuffle keeps the
draw a function of the design digest (§ What auto-derives from) and breaks ties among equal sizes;
largest-first is what gives 8/7 rather than 11/4 over the brief's fixture.

### `k` past the cluster count

Decided and stated in the docstring and pinned by
`test_more_folds_than_clusters_leaves_folds_empty_rather_than_raising`: the surplus folds come back
**empty**. The function stays total, and the alternative — dividing a cluster to fill a fold — is
the exact leak it exists to prevent. An empty fold is a visibly useless split; a divided cluster is
a leaky split that looks fine. Task 5 refuses that `k` at `validate`.

A unit key absent from `clusters` raises a bare `KeyError` by direct subscript, with a comment
saying why it is unreachable (`clusters_of` is total over its roster and raises
`E-DATA-CLUSTER-UNKNOWN` otherwise) and why `.get` would be worse — a default would invent a
singleton cluster, which is the silent form of the leak. No new `E-` code was minted; that
namespace belongs to other tasks in this slice.

## Tests added (`tests/test_units.py`, 5)

| Test | What makes its numbers discriminate |
|---|---|
| `test_the_unclustered_draw_is_unmoved_by_the_clustered_rewrite` | The literal 5 × 10 key lists captured from HEAD **before** the edit. The existing unclustered tests pin reproducibility and shape, both of which a rewritten unclustered path would still satisfy while allocating different units — this pins the draw itself |
| `test_no_cluster_is_split_across_folds` | The brief's 7/3/3/1/1 at `k = 2`. Uneven on purpose: equal-sized or singleton clusters make the two partitioners agree. Adds `len({keys}) == 15` beside `sum(...) == 15`, since the sum alone does not exclude a duplicate |
| `test_the_clustered_draw_follows_the_digest` | Six clusters of 3 at `k = 3`, where the sort is a no-op and only the shuffle decides. Asserts cluster→fold **membership**, not sizes — with equal clusters every fold holds 6 whatever the order, so a size assertion there could not fail |
| `test_the_same_digest_reproduces_the_same_clustered_split` | Reproducibility on the clustered path |
| `test_more_folds_than_clusters_leaves_folds_empty_rather_than_raising` | `[0, 0, 2, 2]` — pins the decision above rather than leaving it undefined |

Every unit landing in exactly one fold is asserted directly (the `resolved == completed +
ineligible + failed` analogue at this level); nothing about `n` moves for an unclustered run,
which is what the byte-identity test establishes.

## Mutations — applied, run, reverted, each verified by behaviour

`__pycache__` deleted before every run. Every cycle ran the **whole file**
(`uv run pytest tests/test_units.py`), never `-k`, so the unclustered controls — whose names
contain no "cluster" — reported on every one. That was task 2's near-miss.

| Mutation | Result |
|---|---|
| assign units rather than whole clusters | FAIL: "a cluster spans two folds" (3 tests) |
| balance cluster count rather than unit count | FAIL: `{4, 11} != {8, 7}` |
| drop the largest-first sort, keep the shuffle | FAIL: `{5, 10} != {8, 7}` |
| drop the shuffle, keep the sort | FAIL: `['C0','C3'],['C1','C4'],['C2','C5']` for both digests |

**On the sort mutation's trap.** The brief warns that for some shuffles the unsorted greedy
coincides with the sorted answer, making that mutation a check that could not fail. Before
implementing, a scratch script ran both variants over the fixture across many digests: under
`sha256:abc` — the brief's own digest — the shuffle draws the size-7 cluster **last**, which is the
case where the two diverge (10/5 against 8/7). So no extra seed had to be pinned; the reason is
written into the test's docstring so a future edit to that digest is visibly a change to what the
test can detect. Digests where the size-7 cluster draws first or second do coincide, and a test
written over one of those would have been the ninth non-discriminating check.

The revert after each mutation was confirmed by a green whole-file run, and the final file was
additionally `diff`'d against the pre-mutation copy — identical, so no mutation residue shipped.

## Document check (no divergence, nothing to record)

Weakening a guarantee in code obliges a check that no document still claims the stronger one.
Grepping the four documents for "at most one" / "differ by" returns nothing, and
`reference.md` § Clustered units already says core "balances units-per-fold as evenly as whole
clusters allow" — the weaker sentence the docstring now carries, word for word in intent. The same
bullet says `validate` "rejects a larger `k` rather than emitting empty partitions", which is
consistent with this function staying total and `validate` (task 5) being the refuser. No
`spec-defects.md` entry is owed.

The one thing no document states is the **assignment order** — shuffle, then largest-first to the
currently-smallest fold — which currently lives only in the docstring and in this slice's briefs.
The documents specify what auto-derives from the design digest, not the greedy rule, so this is
arguably by design; flagging it in case a later task wants the ordering named in § Clustered units
beside the realized sizes it says `sweep.yaml` records.

## Concerns

1. **The clustered path has no caller yet**, so nothing in an actual run is protected until the
   task that threads `cluster_by` from the config into `cli.py`'s fold step lands. Until then
   § Clustered units' promise holds in `units.py` and not end-to-end.
2. **A cluster larger than `n/k` silently unbalances the split** and there is no warning. With
   sizes 90/5/5 at `k = 2` the folds are 90 and 10, which is a legal partition by this function's
   contract and a nearly useless cross-validation. Whether `validate` should warn on a
   most-common-cluster fraction is not in this slice's briefs and may be worth one.
3. **The two paths diverge at `k = 0`**: unclustered returns `[]`, clustered raises `ValueError`
   from `min()` over an empty range. Unreachable — `_fold_k` refuses `k < 2`, and this task must
   not touch it — but "byte-identical unclustered path" is a claim about `clusters is None` only
   and does not extend to cross-path agreement at degenerate `k`.
4. **`min(range(k), ...)` breaks ties toward the lowest index**, which is deterministic given the
   shuffled order rather than randomized. That is deliberate — the randomness lives in the cluster
   order, one place rather than two — but it does mean fold 0 receives the first of any tie,
   including the first cluster of all.

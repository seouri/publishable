# Task 9 review — the stratified draw

**Spec compliance: ❌** (split, and the failing half is the one that prints a number). The draw itself
is exactly what `reference.md` § Weighted samples specifies and I verified it three independent ways.
The *return value* in the design-degenerate case contradicts § Statistical reporting — and is pinned by
an assertion, so a later task cannot fix it without deleting a test that claims to be correct.

**Task quality: findings** — 1 Critical-adjacent/Important spec finding, 2 Important test findings,
3 Minor.

---

## What I verified (do not re-do)

| Check | Result |
|---|---|
| Is it a stratified bootstrap? | **Yes.** Each pool contributes exactly `len(pool)` draws; `[1.0]*10+[5.0]*4`-style composition is exact by construction, and the pooled-swap mutation kills 3 named tests |
| Independent reference implementation | My own stratified bootstrap of the mean (separate RNG stream), banded 20/8/2 fixture: `(9.6842, 9.8900)` vs code `(9.6833, 9.8900)` |
| Analytic check | Stratified sd 0.0521 → normal-approx width **0.204**; code width **0.2067**. Pooled sd 4.485 → width **17.58**; code plain width **16.9**. Stratified is ~80× narrower, as theory requires with a 2-unit high band |
| Composition with `weights` | Correct. Weighted stratified code `(65.1334, 65.5177)` vs my independent weighted reference `(65.1339, 65.5177)`; weighted mean 65.325 |
| Determinism | Same seed/inputs → identical `Interval` across repeat calls; no second RNG source; `random.Random(seed)` still constructed at the same point |
| Regression boundary (task 1's pin) | **Byte-identical.** 300 randomized cases (n 2–40, weighted and unweighted, draws 80/200/2000, conf 0.90/0.95/0.99) against `stats.py` at `fbae604`: **0 mismatches**. Hoisting `checked_weights` above `rng =` changes nothing — it consumes no RNG and both early returns still precede it |
| Import hygiene | `stats.py` imports unchanged (`cluster_count_of, usable_weight` only). Nothing from `units.py` added |
| Tree state | `1741 passed, 2 xfailed`; `mypy` and `ruff check` clean; working tree matches `0866fa2` (only your `progress.md` edit, untouched) |

**Mutations I ran myself** (`__pycache__` cleared each time, reverted by in-place edit, file byte-compared
to a pre-mutation copy after every revert — never `git checkout`):

| # | Mutation | Result |
|---|---|---|
| A | Stratified path → pooled draw over the flattened pools | **FAILS** `preserves_each_stratum_size`, `weighted_draw_keeps_each_value_with_its_weight`, `more_strata_than_two_units_gives_a_zero_width_interval` |
| B | `range(1)` instead of `range(len(pool))` | **FAILS** `preserves_each_stratum_size` |
| C | Pools ordered by label | **FAILS** `is_invariant_to_stratum_labels` |
| D | Weight dropped at grouping (`(value, 1.0)`) | **FAILS** `weighted_draw_keeps_each_value_with_its_weight` |
| E | No sort at all (`ordered = list(pools.values())`) | **FAILS** `is_invariant_to_row_order` |
| F | Pools in **insertion** order (`[sorted(pool) for pool in pools.values()]`) | **SURVIVES — all 10 pass.** See Important 1 |

---

## Findings

### Important 1 — a zero-width `ci95` is produced, and a test pins it as correct

`percentile_over_units(..., strata=...)` returns `Interval(low=x, high=x)` whenever the strata leave the
resample no freedom, and `test_more_strata_than_two_units_gives_a_zero_width_interval` **asserts**
`got.low == got.high`. It is not confined to the all-singleton case I was asked about — internally
constant strata do it too, which is ordinary data:

```
percentile_over_units([1.0]*10 + [5.0]*4, seed=1, draws=2000, strata=["a"]*10+["b"]*4)
  -> Interval(low=2.142857…, high=2.142857…, method='percentile_over_units')
```

The sibling construction in the same module refuses precisely this. `percentile_over_units_clustered`'s
docstring derives its `G = 1` floor: "every replicate draws the same single cluster, so the resampled
distribution is a point mass, both ranks land on it and the interval has zero width — which § Statistical
reporting refuses in those terms: 'a zero-width 95 % interval is not [honest]', and 'reporting a point
with no interval is honest'". I confirmed it returns `None` at `G = 1`. `min_honest_draws`' own docstring
states the same rule a third time. Task 9 went the other way.

The counter-argument I considered and rejected: the pre-existing unstratified path also returns zero width
for all-identical values. That is **data**-caused. All-singleton (or internally constant) strata is
**design**-caused and zero-width *by construction regardless of the data* — which is exactly the
distinction the clustered docstring uses to justify a refusal. This is the whole ❌.

I checked `docs/superpowers/specs/2026-08-15-resample-honoured-design.md`: it says nothing about
degenerate strata. Decision 2 discusses degenerate *draws* only for `percentile_of_derived`. So this is a
task-9 invention, not a design decision being executed.

Route: mirror the clustered floor — return `None` when the drawn distribution is a point mass (equivalently
when every pool is internally constant), and invert the test. If you disagree, the disagreement is with
§ Statistical reporting and belongs in `docs/superpowers/spec-defects.md`, not in a passing assertion.

### Important 2 — the cross-pool ordering claim has no test that can fail

The docstring says the interval "depends on the multiset of (value, weight, stratum) triples and on nothing
else, not on row order and not on the labels." Mutation F — pools in **first-seen insertion** order, keeping
the within-pool sort — survives all ten tests. Cause: `test_a_stratified_draw_is_invariant_to_row_order`
rotates by 7, and `pairs[7:] + pairs[:7]` leaves first-seen order `low, mid, high`, identical to the
original; the label test renames in place, so first-seen order is unchanged there too. Neither test can see
cross-pool ordering that depends on row order. Mutation C catches only the *label*-ordered variant.

One-line fix, confirmed: rotate by 28 instead of 7 — `pairs[28:] + pairs[:28]` gives first-seen order
`high, low, mid`, and the real code is still invariant (I checked: intervals equal).

### Important 3 — two of the three added degenerate tests are non-crash tests, not property tests

`test_a_size_one_stratum_is_drawn_deterministically_every_time` and
`test_a_stratum_of_identical_values_contributes_no_variance_of_its_own` have docstrings naming properties
("contributes its one value to every replicate", "cannot widen the interval") and a single assertion,
`got.low < mean < got.high`, which any roughly centred bootstrap satisfies. Proof rather than argument:
**both passed under mutation A**, the pooled swap that discards stratification entirely. That is CLAUDE.md's
"a dimension no assertion can see." The report lists them as degenerate-shape coverage; they cover only
that the call does not raise. Make each assert the property it names — e.g. pin the singleton's fixed
contribution by comparing against the same fixture with that stratum's value changed, and assert the
identical-value stratum's presence does not change the interval width versus a construction where it does.

### Minor 1 — a comment states a number the code does not produce

`test_a_stratified_weighted_draw_keeps_each_value_with_its_weight`: "The weighted centre (≈ 39.5)". The
actual weighted mean is **65.325** and the interval is `[65.13, 65.52]`. Inherited verbatim from the brief.
The assertion `got.low > 20.0` still discriminates, but it is far looser than the comment implies — bracket
65.3 tightly instead, and fix the number. This is the repo's most-repeated defect class, in a docstring
tasks 13–15 will read.

### Minor 2 — the `E-STATS-RESAMPLE-*` route named in a test docstring does not exist and cannot

`test_more_strata_than_two_units…` says "which is why `E-STATS-RESAMPLE-*` validation (not this function) is
where a design that does this should be refused." The four rows that exist are `-METHOD`, `-N`,
`-STRATIFY-UNKNOWN`, `-UNITS`; none covers this, and none could — stratum *sizes* are roster-dependent and
unknown at validate. If Important 1 is fixed this line goes away with it; if it is not, it points a later
task at an unbuildable check.

### Minor 3 — two nits

- `pool` names a `list[float]` in the unstratified branch and a `list[tuple[float, float]]` in the
  stratified comprehension. Legal (comprehension scope) and mypy-clean, but the brief called the former
  `pool_flat` for this reason.
- `float(value)` coercion happens only on the stratified path. The docstring's "one-stratum case reproduce[s]
  the unstratified path digit for digit" holds for `float` input, not necessarily for `numpy.float32` or
  `Decimal`. Cosmetic today; state the contract or coerce in both.

---

## Boundary note for tasks 13–15

`percentile_of_derived` takes neither `weights` nor `strata`. If task 14 threads `strata` into
`percentile_over_units` only, one run with a declared `stratify_by` will stratify its **column** metrics and
silently not stratify its **derived** ones, with both reporting `method: percentile_over_units*`. Decide and
record that before the threading task, not after.

Nothing in this task implies `resample` is honoured end to end: `E-STATS-RESAMPLE-UNSUPPORTED` still fires,
no `cli` path reaches the new code, and every new test calls `stats` directly. Correct.

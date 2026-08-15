# Task 16b — controller additions

These are requirements, with the same force as the brief file they accompany.

## The identifier and the model

`E-DATA-ALLOCATION-CONTRAST`. Its two siblings are `E-DATA-WEIGHT-CONTRAST` and
`E-DATA-CLUSTER-CONTRAST`, both in `_check_sweep`, both refusing a **combination** rather than a
declaration, both carrying a § Validation registry row and neither counted among the `NOT BUILT`
declarations. **Read both, and read the long comment above the clustered one** — it is the model for
your message and it states the shape of the argument you owe: what construction would be needed, why
its absence would produce a number that looks right, and what the honest routes are.

## The guard reads the resolved family — and yours must read it *per comparison*

The two siblings fire on `comparisons > 0`, because a weight or a cluster affects every contrast alike.
**Yours does not**, and this is the one place where copying the siblings would be wrong.

`reference.md` § Allocation's pairing table settles it:

| The two conditions differ on | Share units? | Comparison |
|---|---|---|
| Parameter axes only, `allocation: between` | Yes — same arm, so same units | **Paired within that arm** |
| Any `groups` axis | No, by construction | **Unpaired** |

So in a `groups × grid` design, control-pearson vs. control-spearman is **paired and computable**, while
control-pearson vs. treatment-pearson is not. A guard on `comparisons > 0` would refuse the first along
with the second and make "each arm analyzed three ways" — the design § Group axes exists to show —
unexpressible. **Refuse a comparison whose two sides differ on a selector path**, and leave the rest.

`Condition.selectors` (task 3) is what tells you which of a condition's `values` are group cells, and
`contrasts.resolve_contrasts` is what produces the resolved family the siblings count. The test that
discriminates: a `groups × grid` config with a baseline must report the code **once per cross-arm
comparison and not for the within-arm ones** — assert the count and the message's named conditions, not
merely that the code appears.

## What the message must say

Following the clustered sibling's structure:

- the two conditions this contrast compares hold **disjoint sets of units**, which is what
  `allocation: between` means
- core has **no unpaired construction** — no `welch_t_over_units`, no `unpaired_percentile_over_units`;
  `paired_t_over_units` takes per-unit differences and there is no unpaired form at all — so the delta
  would be computed over an empty pairing and published as `null` beside a `paired: true` that is false
- the honest routes: an `Estimate` returned by a `summary` step, which core records as reported rather
  than recomputing, or the two arms run separately and joined in a `study`
- temporary, in the siblings' own words, **without naming an internal slice**

## The docstring this task exists to correct

`cli._vs_baseline_block` hard-codes `"paired": True` and justifies it by naming
`E-SWEEP-GROUPS-UNSUPPORTED` and `E-DATA-ALLOCATION-UNSUPPORTED` — the two codes task 17 removes one
task later. **Rewrite it to name yours.** If you leave it, task 17 lands and the file carries a
justification pointing at codes that no longer exist, which is the "comments claiming guarantees this
branch does not provide" failure this repo has a commit about.

Check whether the hard-coded `True` should stay hard-coded at all. Under your refusal every surviving
comparison is genuinely paired, so `True` becomes *true rather than merely unreachable* — say which of
those two it is in the docstring, because they are different claims and only one of them survives H4.

## The controls

Three, and the third is the one that must report:

1. `groups` axis, no baseline, no `statistics.contrasts` → **no comparison exists**, so nothing new
   fires. This is the config tasks 12 and 19 use; it must keep passing, and its finding set must be the
   exact one it has today.
2. `allocation: within` with a parameter axis and a baseline → a genuinely paired contrast, unaffected.
3. `groups × grid` with a baseline → the code fires for the cross-arm comparisons **and not** for the
   within-arm ones. Assert the exact count. Without this, a guard on `comparisons > 0` passes tests 1
   and 2 and silently forbids a documented design.

Every fixture states why its numbers discriminate. Mutate the baseline-generated path and the declared-
contrast path separately; each must die to its own branch.

## Ordering

**This task lands before task 17.** Task 17's addendum has been told to verify that it did, and to check
the `_vs_baseline_block` docstring as part of its own grep sweep.

## Verified interfaces — read off the code before this brief was written, not assumed

| Site | The fact |
|---|---|
| `cli._vs_baseline_block` | `"paired": True` is written literally in the returned block. The justification is verbatim: *"`paired` stays hard `True` here: the crossed-*group*-axis case `reference.md` shows with `paired: false` and `unpaired_*` needs a group axis or `allocation: between`, both refused (`E-SWEEP-GROUPS-UNSUPPORTED`, `E-DATA-ALLOCATION-UNSUPPORTED`), so it is unreachable in this build."* Both named codes are task 17's |
| `cli._differing_axes(of, against)` | **Already exists**, returns the axes two conditions disagree on in sweep declaration order, walking the **union** of both sides' keys against a sentinel. This is the helper your per-comparison guard needs — do not write a second one |
| `Condition.selectors` | `frozenset[str]`, task 3. Intersect it with `_differing_axes`' result and a non-empty intersection is a cross-arm comparison |
| `E-DATA-WEIGHT-CONTRAST` / `E-DATA-CLUSTER-CONTRAST` | Both in `_check_sweep`, both guarded on `comparisons > 0`, both with a `plural` variable and a long explanatory comment above. Yours is guarded differently — see above — and must say why in its own comment, since the next reader will compare the three |
| `stats.paired_keys(of, against, allowed)` | Returns the intersection; over disjoint arms it returns `[]`, and every construction downstream then returns `None`. That is the mechanism producing the silent empty comparison |
| No unpaired construction | `grep -rn 'unpaired_\|welch_' src/` returns exactly one hit, inside the `_vs_baseline_block` docstring quoted above. There is nothing to call |

`E-DATA-ALLOCATION-CONTRAST` sorts before `E-DATA-ALLOCATION-NO-ARMS` and `E-DATA-ALLOCATION-WITHIN-ARMS`
in § Errors `validate` reports. **Never write a phrase locating a row by position** — name what a sibling
row does — and when you insert, check every row your insertion **moved**.

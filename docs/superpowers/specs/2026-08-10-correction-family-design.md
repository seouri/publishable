# Correction family (S4c) design

**Goal:** every interval a run puts in front of a reader is corrected for the family it belongs
to, or says why it isn't. This closes S4: the worked example's `vs_baseline` block carries
`ci95_corrected`, `correction`, `correction_level`, `family_size` and `family`, and nothing
computes them today.

**Status of the sibling work:** S4c is the correction half only. `report_by`, the contents of the
table `aggregate` receives, and `min_reported_n` per stratum are S4d — see § Scope.

## Scope

| In | Out (S4d) |
|---|---|
| `statistics.correction`: `none` / `bonferroni` / `holm` / `fdr_bh` | `report_by` strata, retiring `E-STATS-REPORTBY-UNSUPPORTED` |
| `ci95_corrected`, `correction_level`, `family_size`, broken-out `family` | The `aggregate` table carrying declared attributes and non-numeric columns |
| `confounded: true` on a contrast crossing two axes | A repeat-collapse rule for string columns |
| `W-STATS-FAMILY` recounted from `resolve_contrasts` | `limits.min_reported_n` per stratum |
| `limits.max_ineligible_fraction`, read by nothing today | |
| `statistics.contrasts` added to `_check_shape`'s nested pass | |
| `percentile_over_units`'s missing honest-draw floor | |

The cut is deliberate: the correction family is arithmetic over comparisons that already exist,
while `report_by` first requires changing what every plugin's `aggregate` receives. Mixing a pure
computation with a change to a published interface is how a slice acquires two unrelated failure
modes.

## Architecture

**One new pure module, `src/publishable/correction.py`** — no filesystem, no runtime import of
`config`, `artifacts`, `runner` or `cli`, matching `contrasts.py` and `stats.py`.

```
@dataclass(frozen=True)
class Member:                      # one correctable interval, and where it came from
    where: str                     # condition index or contrast id, for the record
    condition_index: int           # `of`'s index — the tie-break key, which `where` cannot be
    step: str
    metric: str
    delta: float
    ci95: tuple[float, float]
    pool: list[float] | None       # sorted draws; None for an analytic interval
    diffs: list[float] | None      # per-unit differences; None for a derived metric

family_members(vs_baseline, contrasts) -> list[Member]
rank_family(members)                   -> list[Member]      # strongest first
corrected_for(member, method, alpha, family_size, rank) -> dict
```

`cli.py` collects members **after** both `vs_baseline` and `results.contrasts` are built, runs the
pass, and writes the fields back onto each entry. The family spans conditions, so this cannot
happen inside `_comparison_step_blocks`, which sees one comparison at a time.

**The corrected interval comes from the same evidence as the raw one.** For an analytic interval
that is the same per-unit differences at a different *t* quantile. For a percentile interval,
the construction returns its sorted draw pool and the corrected interval is a **second rank pair
read off that same pool** — so `corrected ⊇ raw` holds by
construction rather than by two RNG calls happening to agree. This is the S4b Critical's lesson
applied before the fact: a point estimate and its interval computed from different bases produced
an interval that could not contain its own estimate, and the fix was to make one call yield both.

**Only one construction needs this: `paired_percentile_of_derived`.** The family is comparisons ×
metrics, so a per-condition `aggregated` metric is not in it — the worked example's per-condition
`r` block carries `ci95` and `repeat_spread` and no `ci95_corrected`, and `reference.md` puts every
corrected block under `vs_baseline` or `contrasts`. So `percentile_of_derived` and
`percentile_over_units` keep their current shapes, and a contrast over a recorded *column* needs no
pool at all: `paired_t_over_units` already takes `confidence`, so its corrected interval is one
more call over the same stored per-unit differences.

`min_honest_draws` is then checked against the **corrected** level over the same pool size. A
family of 40 implies α/40, whose floor is 3201 draws against a 2000 default, so the corrected
interval is `null` with a warning rather than a number that is silently too narrow.

## What the pass computes

| | |
|---|---|
| **Family membership** | `basis: units` metrics carrying an interval, across `vs_baseline` **and** declared contrasts (`reference.md`: both put an interval in front of a reader). A reported `Estimate` is excluded — core never computed it and has no standing to correct it. A stratum is excluded — it describes rather than compares. A member whose `ci95` is `null` is not counted and consumes no rank |
| **`family_size`** | `comparisons × metrics`, with `family: {comparisons, metrics}` broken out so a reviewer can check the count instead of trusting it |
| **Rank** | `abs(delta) / (half the raw ci95 width)`, largest first. Ties break by condition index, then metric name in declaration order, so a rank is a function of the record rather than of an iteration order |
| **`holm`** (default) | `ci95_corrected` at α/(m−i+1) for rank *i*. The weakest member's corrected interval **equals** its raw one; that is Holm working, not a correction that failed |
| **`bonferroni`** | α/m for every member |
| **`fdr_bh`** | `ci95_corrected: null`, `correction_level: null`, no `p_value_corrected`, plus `W-STATS-CORRECTION-INAPPLICABLE`. No comparison in this build can carry a p-value: `statistics.null_test` is refused, and a parameter-axis contrast could never supply one anyway |
| **`none`** | The four fields absent. `W-STATS-FAMILY` keeps its identifier and flips to its documented condition — it warns for `correction: none` over a real family, counted from `resolve_contrasts`, rather than announcing "correction is not implemented" on every multi-condition run |
| **`confounded: true`** and **`differs_on`** | Set when the two conditions' `values` differ on more than one axis, together with `differs_on: [<axis>, <axis>]` naming them — `reference.md`:951-955 shows the pair, and the boolean alone would say a contrast is confounded without saying by what. Both are absent, not `false`/`[]`, when only one axis differs. `paired` stays hard `true`: group axes (`E-SWEEP-GROUPS-UNSUPPORTED`) and `allocation: between` (`E-DATA-ALLOCATION-UNSUPPORTED`) are both still refused, so the `paired: false` and `unpaired_*` method that example also shows are unreachable in this build |

### Two definitions that need stating rather than assuming

**`family_size` is a product, and the product can exceed the member count.** Where a metric is
recorded in one comparison and not another, `comparisons × metrics` is larger than the number of
members. That is the conservative direction — a larger family means a smaller α and a wider
corrected interval — and it is what the document's own arithmetic says. Holm's *m* is the
`family_size`, so ranks run 1..member-count against a possibly larger *m*, which again only
widens. Recorded here so a future reader does not "fix" it into the member count.

**α is `1 − confidence`, and confidence is not configurable.** Every interval core builds is a 95 %
one — `ci95` is in the field name — so α is 0.05 throughout and no config field sets it. The
corrected *level* varies by method and rank; the raw confidence does not. A future slice adding a
configurable confidence would have to rename the record field, which is the reason it stays fixed.

**Ranking needs a statistic every member has**, which a p-value is not: `null_test` supplies one
only where `shuffle` names an attribute, and a parameter-axis contrast never can. Hence the
point-estimate-over-half-width ratio, which is defined whether the interval was *t*-based or
percentile. Ranking on a p-value where one exists and on the ratio elsewhere would order the
family by two different statistics, which is not an ordering.

## New identifiers

Each needs a test that produces it, and a `docs/superpowers/spec-defects.md` entry where
`reference.md` states the rule but names no code — the pattern `E-STATS-CONTRAST-WITHIN` and
`E-STATS-CONTRAST-SAME-SIDES` already follow.

| Identifier | Fires when |
|---|---|
| `W-STATS-CORRECTION-INAPPLICABLE` | `fdr_bh` over a family where no comparison will carry a p-value. Documented as a warning at `reference.md` § Statistical reporting and § Validation; total over this build |
| `W-STATS-CORRECTED-THIN` | The draw pool cannot support the corrected level's honest-draw floor, so `ci95_corrected` is `null` while `correction` and `correction_level` still record what was asked for |
| `E-CONFIG-SHAPE` (reused) | `statistics.contrasts` is not a list, refused once in `_check_shape`'s nested pass instead of by each reader separately |

`W-STATS-FAMILY` is **not** retired and **not** renamed. Its condition changes to the documented
one. No test and no document quotes its message text, which was verified during the S4b review.

## Worked-example verification

Done before writing this spec, because a pinned number the implementation cannot reproduce is
worth finding now rather than in the acceptance test.

- **The worked example pins exactly one corrected block**, at `reference.md`:412-414 and again at
  :2003-2005: spearman's `r`, `ci95_corrected: [-0.007, 0.059]` — identical to its raw `ci95` —
  with `correction_level: 0.05`, `family_size: 2`, `family: {comparisons: 2, metrics: 1}`. Three
  conditions give 2 baseline comparisons, one metric gives `metrics: 1`, and spearman is rank 2 of
  2, so its level is α/(2−2+1) = α. **The implementation must reproduce corrected = raw here**,
  which is also the sharpest available test of Holm's weakest-member property.
- **Kendall's corrected interval is pinned nowhere.** It will be produced (rank 1 of 2, level
  α/2 = 0.025, so wider than its raw `[-0.213, -0.125]`), but no document states it, so there is
  no number to match.
- **The ranking ratio checks out against the pinned intervals.** Kendall: `0.169 / 0.044 = 3.84`.
  Spearman: `0.026 / 0.033 = 0.79`. Those are the two values `reference.md` cites, and they give
  the ranks above.
- **The two illustrative corrected intervals are normal-scaled widenings, and neither belongs to
  the worked example.** `reference.md`:1667 is a hypothetical six-condition family (the prose says
  so explicitly): half-width 0.044 → 0.066 at α/15, a ratio of 1.500 against
  z(0.99835)/z(0.975) = 1.5004. § Contrasts at :2083 is a different experiment: 0.0085 → 0.0115 at
  α/7, ratio 1.353 against a z-ratio of 1.371. **A percentile interval read off a draw pool
  approximates that scaling and will not equal it**, which is fine — no run this build produces is
  either of those families. Stated here because the numbers look like targets and are not.

### One document defect found, to fix before the code

`reference.md`:2084 reports `family_size: 7` with no `family:` breakout, while :414 and :2005 both
carry one and the prose at :1693 says the count "is reported broken out rather than as a single
integer, so the count is auditable instead of asserted." Add `family: {comparisons: 7, metrics: 1}`
to that entry — a single-metric family of 7 comparisons is consistent with the surrounding
`step03_screen` example. Per CLAUDE.md the document changes first, and the mechanical and
cross-document passes run on the edit.

## Testing

`correction.py` is pure, so most of the surface is unit-testable: membership, the ranking ratio and
its tie-break, Holm's per-rank levels, Bonferroni's flat level, `fdr_bh`'s nulls, the product
breakout, and the thin-pool refusal. `stats.py` gains the pool-return shape and the nesting
property for both constructions. Then end-to-end through `main(["run", ...])`, which is where S4b's
two Criticals both hid:

- a 3-condition Holm sweep asserting `family_size: 2`, `family: {comparisons: 2, metrics: 1}`, the
  weakest member's corrected interval **equal** to its raw one, and the stronger member's
  **strictly wider**
- a Bonferroni run, where every member shares one level
- an `fdr_bh` run asserting the nulls **and** the warning
- a two-axis grid asserting `confounded: true` **and** `differs_on` naming both axes, and a
  one-axis sweep asserting both fields are absent
- a family wide enough that the corrected level outruns the pool, asserting `ci95_corrected: null`
  beside a non-null `correction_level` and the warning

### Mutations each test must kill

Named here rather than discovered in review. Three tests shipped in S4b that passed against wrong
implementations; every one of them would have been caught by naming the mutation first.

| Mutation | Caught by |
|---|---|
| Rank by raw width instead of the ratio | the two-member ordering test |
| Drop `abs()` on `delta` | a negative-delta member ranking last |
| α instead of α/(m−i+1) | the rank-1 member's `correction_level` |
| Redraw the pool for the corrected interval | the nesting property |
| Count comparisons, not comparisons × metrics | a 2-comparison × 2-metric family |
| Count a stratum or a reported `Estimate` into the family | `family_size` on a run carrying one |
| Warn `W-STATS-FAMILY` on `holm` as well as `none` | the default-config run, which must be silent |

## Risks

Each has a live precedent in this repository, which is why it is listed.

- **A number and its interval computed from different evidence.** The S4b Critical. Here the
  analogue is a corrected interval from a different draw pool than the raw one, prevented
  structurally by returning the pool rather than by trusting two seeds to agree.
- **A silent no-op.** `correction: holm` must never validate clean and produce nothing. Every
  reachable value of `statistics.correction` ends in a computed field or a diagnostic, and the
  end-to-end tests assert the fields rather than the absence of a crash.
- **`validate` must collect, never raise.** A non-string `correction` needs an `isinstance` guard.
  This is the exact class of the R11 regression in S4b, where a new reader called `len()` on an
  unguarded config value ahead of the shape check.
- **A test that passes against the wrong implementation.** Hence the mutation table, and hence
  running each mutation rather than reasoning about it.

## Task sequence

Nine tasks, each landing green.

1. `stats.py`: the two percentile constructions return their sorted pool; a shared
   `interval_at(pool, confidence)` reading a rank pair off it.
2. `correction.py`: `Member` and `family_members`, including both exclusions.
3. `correction.py`: `rank_family`, with the tie-break.
4. `correction.py`: `corrected_for` per method, including the thin-pool `null`.
5. `validate.py`: the `W-STATS-FAMILY` recount from `resolve_contrasts`, the `fdr_bh` warning, and
   the `correction` shape guard.
6. `cli.py`: collect members across both record shapes, run the pass, write the fields back.
7. `confounded`, from the conditions' `values`.
8. The three carries: `max_ineligible_fraction`, `statistics.contrasts` in `_check_shape`,
   `percentile_over_units`'s floor.
9. The end-to-end acceptance test, including the worked example's pinned spearman block.

`reference.md`:2084's missing `family` breakout is fixed ahead of task 1, since the document leads.

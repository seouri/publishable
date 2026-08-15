"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import hashlib
import math
import random
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from scipy import stats as _scipy_stats

from publishable.errors import ContractError
from publishable.replication import LABEL_JOIN
from publishable.units import cluster_count_of, usable_weight

if TYPE_CHECKING:
    from publishable.replication import RepeatLevel
    from publishable.runner import ExecutionResult

#: Keys a step block holds that are not metrics, and so may not be metric names.
#: `by` carries the reporting strata (`reference.md` § Reporting strata): a
#: mapping of attribute to level to another metric block, sitting beside the
#: metric names in the same mapping. A derived metric of that name would be
#: overwritten by the strata — or, worse, would be differenced as a contrast
#: metric, since every consumer of a step block reads its keys as metric names.
RESERVED_METRIC_NAMES = frozenset({"by"})


@dataclass(frozen=True)
class Interval:
    low: float
    high: float
    method: str


@dataclass(frozen=True)
class PairedResample:
    """A paired percentile interval and the pool it was read from.

    The pool travels so a caller can build the *corrected* interval at a
    smaller α off the same draws (`interval_at`). It is deliberately not a
    third tuple element: a positional `[2]` at a call site says nothing about
    what it holds, and this value must never reach `run.yaml`.
    """

    interval: Interval | None
    draws_used: int
    pool: list[float]


def mean_of(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _t_critical(df: float, confidence: float) -> float:
    """The two-sided t critical value, for every t interval in this module.

    One expression rather than one per construction: two copies is how the
    weighted and unweighted intervals drift apart, and a drift in a critical
    value is invisible in every output that isn't compared against the other.
    `df` is a `float` because Kish's effective size is fractional — `t.ppf`
    accepts that, and rounding it would be a claim the sample doesn't support.
    """
    return float(_scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=df))


def t_over_units(values: Sequence[float], confidence: float = 0.95) -> Interval | None:
    """Student's t on the per-unit values, df = completed units − 1.

    Returns None below two values: df would be zero and there is no dispersion
    to describe. Reporting a point with no interval is honest; inventing one is not.
    """
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    sem = math.sqrt(variance) / math.sqrt(n)
    half = _t_critical(n - 1, confidence) * sem
    return Interval(low=mean - half, high=mean + half, method="t_over_units")


def checked_weights(weights: Sequence[Any]) -> list[float]:
    """Every weight as a number core can multiply by, or `ContractError`.

    The one gate for both weighted constructions in this module, reading
    `units.usable_weight` — the same single authority `validate` approves a
    `data.units.weight_by` config against. A fourth notion of a usable weight is
    the thing this arrangement exists to make impossible.

    It raises rather than dropping or substituting because the alternatives are
    each a wrong number with no error. Dropping the offending unit changes `n`
    silently; carrying it through gives `nan` for a `nan` weight and `0.0` for an
    all-negative one, and `effective: nan` in `run.yaml` is exactly the failure
    class the weight checks exist to prevent. `validate` reports the same
    condition under the same identifier, but only when it actually ran.

    **This code is dual-listed**, in `reference.md` § Validation's
    `### Errors validate reports` and in § Errors core raises — the arrangement
    `E-DATA-MEASUREMENTS-COLLAPSE-TYPE` already has, for the identical
    single-authority reason, and documented there as "Raised at run time too,
    under the same code". Both rows describe one condition because one predicate
    decides it; a reader who meets the code at either surface finds it.
    """
    usable = [usable_weight(w) for w in weights]
    if any(u is None for u in usable):
        offender = next(w for w, u in zip(weights, usable, strict=True) if u is None)
        raise ContractError(
            f"a weight of {offender!r} — a {type(offender).__name__} that is not a "
            "positive finite number — reached a weighted estimate. A weight is how much "
            "of the population a unit stands for, so zero, a negative, a non-number and "
            "a NaN are each a unit standing for nothing core could weight with",
            code="E-DATA-WEIGHT-INVALID",
        )
    return [u for u in usable if u is not None]


def kish_effective_n(weights: Sequence[Any]) -> float:
    """Kish's effective sample size: (Σw)² / Σw².

    Equals the count when the weights are equal, and falls as they spread — which
    is the whole reason it is here. `reference.md` § Weighted samples: weighting
    concentrates the estimate on fewer units, and an interval whose df ignored
    that would be narrower than the sample supports.

    **The gate is inside rather than at the call site**, and `weights` is
    annotated `Any` for the same reason `weighted_t_over_units`'s is: this is a
    public function that will be handed a roster's weight column, which
    `units._from_table` builds from `csv.DictReader` and which is therefore `str`
    for every unit. Ungated it answered `nan` for a `nan` weight, `0.0` for a
    negative one and a bare `TypeError` for a table-sourced one — three
    plausible-looking numbers and an uncoded traceback, for input it cannot
    handle. A caller that has to remember to pre-validate is a caller that
    eventually forgets, and this value lands in `run.yaml` as `n.effective`.

    The `Σw² == 0` guard survives the gate even though no gated weight is zero:
    it is what answers the empty sequence, which is a real call and not an error.
    """
    w = checked_weights(weights)
    total = sum(w)
    squares = sum(x * x for x in w)
    if squares == 0:
        return 0.0
    return (total * total) / squares


def _weighted_mean(checked: Sequence[float], values: Sequence[float]) -> float:
    """Σwv / Σw, over weights `checked_weights` has already gated.

    The single copy of the weighted mean in this module: `weighted_t_over_units`
    centres its variance on it, `weighted_mean_of` is what `summarize_step`
    reports, and `percentile_over_units` recomputes it on every draw. Three
    copies is how a point estimate and the interval around it come to disagree
    about what the estimate *is*, which no output shows.

    `strict=True` on the zip: a values/weights length mismatch is a misaligned
    weight vector, and the whole failure class this wiring guards against is one
    that produces a plausible number instead of an error.
    """
    return sum(w * v for w, v in zip(checked, values, strict=True)) / sum(checked)


def weighted_mean_of(values: Sequence[float], weights: Sequence[Any]) -> float | None:
    """The weighted mean, or `None` for an empty sequence — `mean_of`'s sibling.

    `reference.md` § Weighted samples: core "computes weighted means for
    `basis: units` column metrics". A weighted interval around an unweighted
    point estimate is the same half-delivered failure as an unweighted interval
    beside a `weighted_by` marker, one level down, and it survives any check that
    looks only at `ci95`.
    """
    if not values:
        return None
    return _weighted_mean(checked_weights(weights), values)


def weighted_t_over_units(
    values: Sequence[float], weights: Sequence[Any], confidence: float = 0.95
) -> Interval | None:
    """Student's t on the weighted per-unit values, df = Kish's effective n − 1.

    `reference.md` § Weighted samples: "the weighted mean and the weighted
    variance, with the degrees of freedom taken from Kish's effective sample size
    rather than the row count".

    Returns None below two values, matching `t_over_units`: df would be zero and
    there is no dispersion to describe. Reporting a point with no interval is
    honest; inventing one is not. The same refusal arrives by the weights when
    Kish's size falls below two — eight rows concentrated onto 1.8 effective units
    have no more dispersion for a df to describe than one row does.

    `weights` is annotated `Any` rather than `float` on purpose: a weight is a
    unit attribute, and `units._from_table` builds those from `csv.DictReader`,
    which yields `str` for every column whatever it holds. `units.usable_weight`
    is the gate — the same one `validate` approves the config against, so that a
    weight core accepts at validate time is exactly a weight core can multiply by
    here — and a `float` annotation would let a call site pass the real thing
    only by lying to the type checker.

    Two constructions here that a tidy-up would get wrong:

    - **The variance denominator is Σw − Σw²/Σw, not Σw.** That is what makes
      equal weights reproduce `t_over_units` exactly, digit for digit, rather
      than approximately: at w = 1 it is n − 1. Σw narrows the interval instead
      — in the direction § Weighted samples explicitly warns about — and makes
      the construction a different statistic wearing the same name.
    - **The whole thing is invariant to rescaling the weights**, which it must
      be: survey weights routinely sum to a population size rather than to the
      row count, and an interval that moved with that convention would be
      reporting the convention.
    """
    if len(values) < 2:
        return None
    w = checked_weights(weights)
    total = sum(w)
    squares = sum(x * x for x in w)
    mean = _weighted_mean(w, values)
    effective = kish_effective_n(w)
    if effective < 2:
        return None
    # The weights are in the variance as well as in the mean. Keeping them in only
    # the mean leaves the point estimate right and the interval wrong, which is
    # the failure that survives an eyeball.
    variance = sum(a * (v - mean) ** 2 for a, v in zip(w, values, strict=True)) / (
        total - squares / total
    )
    sem = math.sqrt(variance) / math.sqrt(effective)
    half = _t_critical(effective - 1, confidence) * sem
    return Interval(low=mean - half, high=mean + half, method="weighted_t_over_units")


def t_over_units_clustered(
    values: Sequence[float],
    keys: Sequence[str],
    membership: Mapping[str, str],
    confidence: float = 0.95,
) -> Interval | None:
    """Cluster-robust (CR1) *t* on the per-unit values, df = clusters − 1.

    `reference.md` § Statistical reporting: "Cluster-robust (CR1: the sandwich
    estimator with the standard finite-sample scaling), df = clusters − 1. The df
    is the part that bites — 10 animals give 9, not 299."

    **The df is the construction**, not a detail of it. A cluster-robust interval
    over positively correlated data comes out wider than `t_over_units` whatever
    df it uses, so widening is not evidence that the cluster count reached the
    critical value; only the number is.

    The model core fits here is the mean, so the sandwich is the intercept-only
    case: with `X'X = n` and a cluster's score `S_g = Σ_{i∈g}(v_i − v̄)`, the
    variance of the mean is `Σ_g S_g² / n²` before scaling. **The finite-sample
    scaling is the `G/(G−1)` factor**, and dropping it is not a rounding
    difference — it is the CR0 estimator wearing this one's name, biased downward
    by exactly the factor a small cluster count makes largest.

    Two conventions for CR1 exist in the literature — the `G/(G−1)` of
    MacKinnon–White, and Stata's `G/(G−1) · (n−1)/(n−k)` — and **they coincide
    here**: `k`, the number of fitted parameters, is 1 for a mean, so the second
    factor is `(n−1)/(n−1)`. There is nothing to choose between, which is why this
    function names neither in its `method` string.

    Returns `None` below two clusters, and for the same reason `t_over_units`
    returns `None` below two values: df would be zero. That floor is on the
    CLUSTER count, so 300 cells from one animal get a point and no interval —
    which is the honest answer, one animal being one draw. The `len(values) < 2`
    guard in front of it is `t_over_units`' own floor, kept so the two
    constructions refuse the same degenerate inputs.

    **The membership mapping is `units.clusters_of`'s**, passed whole rather than
    pre-resolved to a label vector, and the count comes from
    `units.cluster_count_of` — the single counting expression, so this df cannot
    disagree with the `n.clusters` printed beside it or with a fold's partition
    about what one cluster is. Indexed rather than `.get`-ed for the reason
    `cluster_count_of` states: a key the roster doesn't hold is a core defect, and
    absorbing it into a cluster of its own would raise `G` and narrow the interval.

    `strict=True` on the zip, for the reason `_weighted_mean` uses it: a
    keys/values length mismatch is a misaligned cluster vector, and it would
    produce a plausible number rather than an error.
    """
    n = len(values)
    if n < 2:
        return None
    groups = cluster_count_of(membership, keys)
    if groups < 2:
        return None
    mean = sum(values) / n
    # One residual sum per cluster: what makes this robust is that the residuals
    # are added up WITHIN a cluster before being squared, so correlated units
    # reinforce each other instead of counting as independent draws.
    scores: dict[str, float] = {}
    for key, value in zip(keys, values, strict=True):
        label = membership[key]
        scores[label] = scores.get(label, 0.0) + (value - mean)
    meat = sum(s * s for s in scores.values())
    variance = (groups / (groups - 1)) * meat / (n * n)
    half = _t_critical(groups - 1, confidence) * math.sqrt(variance)
    return Interval(low=mean - half, high=mean + half, method="t_over_units_clustered")


def weighted_t_over_units_clustered(
    values: Sequence[float],
    keys: Sequence[str],
    membership: Mapping[str, str],
    weights: Sequence[Any],
    confidence: float = 0.95,
) -> Interval | None:
    """Cluster-robust (CR1) *t* on the *weighted* per-unit mean, df = clusters − 1.

    The construction a run declaring both `data.units.weight_by` and
    `data.units.cluster_by` needs, and `reference.md` decides both halves of it in
    one sentence each rather than leaving them to be picked here. § Weighted
    samples: "`cluster_by` still decides the draw when both are declared, since a
    cluster is what's independent and a weight is what it represents" — so the
    **draw** is the cluster and the **estimate** is the weighted mean, the weight
    being what a unit stands for rather than what it is grouped with. § Statistical
    reporting gives the clustered form "df = clusters − 1" unqualified, and the df
    is a property of the draw, so it comes from the cluster count here too.

    **Kish's effective size appears nowhere in this interval**, and that is the
    part worth reading twice. `weighted_t_over_units` takes its df from Kish's
    size because there the draw *is* the unit and weighting concentrates the
    estimate on fewer of them; once the cluster is the draw, the thing being
    counted is clusters, and mixing the two would give an interval whose df came
    from neither. `n.effective` is still reported beside this interval — it is a
    fact about the weighting rather than about the construction — which is exactly
    the arrangement § Weighted samples describes for `effective` and `clusters`
    both joining `n`.

    The sandwich is `t_over_units_clustered`'s with the weights in the score:
    the estimating equation for a weighted mean is `Σ w_i (v_i − μ) = 0`, so a
    cluster's score is `S_g = Σ_{i∈g} w_i (v_i − v̄_w)`, the bread is `1/Σw`, and

        V_CR1 = [G/(G−1)] · Σ_g S_g² / (Σw)²

    **At `w ≡ 1` that is `t_over_units_clustered` digit for digit** — `Σw = n` and
    the score collapses to the residual sum — and it is a generalization rather
    than a second construction for exactly that reason. Unlike
    `weighted_t_over_units`, whose `Σw − Σw²/Σw` denominator is what buys it the
    same reduction, nothing has to be corrected for here: the scaling that makes
    CR1 CR1 is `G/(G−1)`, which counts clusters and knows nothing about weights.
    `test_the_weighted_sandwich_reduces_to_the_unweighted_one_at_equal_weights` is
    the oracle; if it ever fails, this formula is wrong rather than that test.

    Invariant to rescaling the weights, as `weighted_t_over_units` is and for the
    same reason: `S_g` scales with the weights and `(Σw)²` divides the square out,
    so a weight column summing to a population size gives the same interval as one
    summing to the row count.

    Floors are the clustered ones: `None` below two values (`t_over_units`' own,
    kept so every construction here refuses the same degenerate input) and `None`
    below two clusters, where df would be zero. There is deliberately no Kish
    floor, for the reason above — the effective size does not enter the df, so a
    weighting that concentrates 10 clusters onto few units still has 9 df, with the
    concentration showing up in the scores instead.

    `weights` is annotated `Any` and gated by `checked_weights`, the single
    authority `validate` approves a config against, for the reason
    `weighted_t_over_units` states: a weight is a unit attribute and
    `units._from_table` builds those from `csv.DictReader`, so every one of them
    arrives as `str`.
    """
    n = len(values)
    if n < 2:
        return None
    groups = cluster_count_of(membership, keys)
    if groups < 2:
        return None
    w = checked_weights(weights)
    total = sum(w)
    mean = _weighted_mean(w, values)
    # One weighted residual sum per cluster, added up WITHIN the cluster before
    # being squared — the same reason `t_over_units_clustered` gives, with each
    # residual carrying the weight of the unit that produced it.
    scores: dict[str, float] = {}
    for key, value, weight in zip(keys, values, w, strict=True):
        label = membership[key]
        scores[label] = scores.get(label, 0.0) + weight * (value - mean)
    meat = sum(s * s for s in scores.values())
    variance = (groups / (groups - 1)) * meat / (total * total)
    half = _t_critical(groups - 1, confidence) * math.sqrt(variance)
    return Interval(
        low=mean - half, high=mean + half, method="weighted_t_over_units_clustered"
    )


def paired_t_over_units(diffs: Sequence[float], confidence: float = 0.95) -> Interval | None:
    """Student's t on the per-unit differences, df = n_paired − 1.

    The contrast's interval is its own construction, never a difference of the
    two sides' intervals — differencing discards the covariance that pairing
    exists to exploit, which is why a paired interval is narrower than the two
    conditions' own (reference.md § How a metric becomes a number).
    """
    plain = t_over_units(diffs, confidence)
    if plain is None:
        return None
    return Interval(low=plain.low, high=plain.high, method="paired_t_over_units")


def cohens_dz(diffs: Sequence[float]) -> float | None:
    """The mean of the per-unit differences over their standard deviation.

    Reported only for a per-unit mean: a derived metric has no per-unit value to
    difference, which is why the worked example carries `cohens_d: null` for `r`.
    """
    if len(diffs) < 2:
        return None
    mean = sum(diffs) / len(diffs)
    variance = sum((d - mean) ** 2 for d in diffs) / (len(diffs) - 1)
    sd = math.sqrt(variance)
    return mean / sd if sd > 0 else None


def resample_seed(digest: str) -> int:
    """From the design digest, never `parameters_hash`.

    Editing an unrelated parameter must not redraw a resample — the same rule
    fold partitions and `order_seed` follow (reference.md § What auto-derives from).
    """
    return int.from_bytes(hashlib.sha256(f"{digest}|resample".encode()).digest()[:4], "big")


def _percentile_ranks(draws: int, confidence: float) -> tuple[int, int]:
    """The symmetric pair of ranks a percentile interval reads off a sorted pool.

    Factored out so every percentile construction in this module — over raw
    values or over recomputed draws — shares one copy: an asymmetry fixed in
    one and not the other is exactly the defect this arithmetic already had
    once (S4a task 4's off-by-one on the upper rank).
    """
    tail = (1.0 - confidence) / 2.0
    lo = max(0, int(tail * draws) - 1)
    # Symmetric with `lo` in rank, not `int((1.0 - tail) * draws)` bare: that form
    # overshoots the upper rank by one on every interval. Floored at `lo` because
    # the symmetric form alone gives -1 at draws=1.
    hi = max(lo, min(draws - 1, int((1.0 - tail) * draws) - 1))
    return lo, hi


def interval_at(pool: Sequence[float], confidence: float) -> tuple[float, float] | None:
    """The endpoints a sorted draw pool implies at `confidence`.

    Factored out so a corrected interval is a second rank pair off the *same*
    pool the raw interval was read from, rather than a fresh resample that
    happens to share a seed. That makes `corrected ⊇ raw` a property of the
    arithmetic instead of a property of two RNG calls agreeing — and a
    corrected interval narrower than its raw one is the kind of number a reader
    cannot detect is wrong.

    `None` below `min_honest_draws(confidence)`: a correction that pushes the
    level past what the pool can support has no honest interval to report, and
    the caller records `ci95_corrected: null` rather than a too-narrow number.
    """
    if len(pool) < min_honest_draws(confidence):
        return None
    lo, hi = _percentile_ranks(len(pool), confidence)
    return pool[lo], pool[hi]


def min_honest_draws(confidence: float = 0.95) -> int:
    """The fewest resample draws a percentile interval may be read off.

    `_percentile_ranks` floors the lower rank at 0, so below this count the
    interval's lower endpoint *is* the sample minimum while the upper endpoint
    keeps shrinking with n: low-biased and systematically too narrow, and at
    two surviving draws `lo == hi` and the "interval" has zero width. The
    threshold is the smallest n at which both ranks are interior — `int(tail *
    n) >= 2`, so `lo >= 1` and `hi <= n - 2` — which is 80 draws at 95 %
    confidence. Below it there is no honest interval to report, and reporting
    a point with no interval is what core does everywhere else it runs out of
    evidence (`t_over_units`, `percentile_over_units`).

    Derived from `confidence` rather than written as a literal so the two move
    together: a caller asking for 99 % needs 400.
    """
    tail = (1.0 - confidence) / 2.0
    return math.ceil(2.0 / tail)


def percentile_over_units(
    values: Sequence[float],
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    weights: Sequence[Any] | None = None,
    strata: Sequence[Any] | None = None,
) -> Interval | None:
    """A percentile interval over the units, by resampling with replacement.

    This is what gives a *column* metric a resampled `ci95` when `resample` is
    declared (`reference.md` § How a metric becomes a number): the mean is
    recomputed on each bootstrap draw. A derived metric — one `aggregate`
    computed, with no per-unit value of its own — needs `aggregate` itself
    recomputed on each draw instead, which is what `percentile_of_derived` does.

    With `weights`, the statistic recomputed on each draw is the *weighted* mean
    and the draw itself is unchanged — `reference.md` § Weighted samples: "A
    percentile interval draws units as usual and recomputes the weighted
    statistic on each draw, so the weights are in the estimate rather than in the
    drawing." Drawing units in proportion to their weights is a different
    estimator, not an equivalent implementation of this one: a unit standing for
    most of the population would then fill nearly every slot of every draw and
    the interval would collapse onto its value, when what the weights say is how
    much that unit *counts*, not how often it would be sampled again.

    Two things this path deliberately does not inherit from
    `weighted_t_over_units`. It applies no Kish floor — that construction refuses
    an effective size below two because Kish's size is where its *degrees of
    freedom* come from, and a percentile interval has none; its evidence is the
    spread of the draws, which a concentrated weighting widens rather than
    invalidates. And each value keeps its own weight through the sort: the pool
    is sorted for the row-order invariance the unweighted branch explains below,
    and sorting the two sequences separately would preserve that invariance while
    silently re-pairing them — a mistake equal weights cannot see.

    With `strata`, each draw preserves **each stratum's own size** and draws with
    replacement *within* it — `reference.md` § Weighted samples:
    "`resample.stratify_by` says what an independent draw is, resampling within
    each stratum so a bootstrap can't return a replicate whose stratum
    composition the design ruled out." The two ways to get this wrong both
    produce a plausible number: drawing `n` units and repairing the composition
    afterwards is the unstratified interval however carefully the counts are
    matched, and averaging the strata's own means gives every stratum equal say,
    which is a different estimator entirely (for 20/8/2 units in three bands it
    reports 37.2 where the sample mean is 9.8).

    `strata` is aligned positionally to `values`, the same contract `weights`
    has, and `strict=True` on the zip for the same reason: a length mismatch is
    a misaligned vector and would produce a number rather than an error.

    **Grouping happens before any sort and carries the pairs**, so each value
    keeps its stratum and its weight; the strata are then ordered by their own
    sorted contents rather than by label, which is what makes a relabelled
    stratum give the identical interval and what makes the one-stratum case
    reproduce the unstratified path digit for digit. Sorting values and stratum
    labels as separate sequences would preserve every invariance and silently
    re-pair them — the mistake equal-sized strata cannot see.

    Returns `None` rather than a zero-width interval when every stratum's own
    (value, weight) pairs are all identical — a singleton stratum is the
    special case of this, but a larger stratum whose rows all carry one
    repeated pair guarantees the same zero freedom. That is a structural
    guarantee, true whatever the repeated pair's value is, unlike a single
    constant stratum among others that still vary — which keeps its interval,
    the same way `percentile_over_units_clustered` reports a point rather than
    a zero-width interval at `G < 2`.

    **This returns a bare `Interval`, with no survivor count, and that is a
    decision rather than an omission.** `percentile_of_derived` returns
    `(Interval, int)` because a derived metric's `compute` can fail on a
    degenerate draw — `nan`, `None`, or a raise — so how many draws survived is
    a real fact about the interval. A column metric's draw statistic is a mean
    over a non-empty sample, which is always defined: the unweighted branch
    divides by `n >= 2`, the weighted branch's Σw is strictly positive because
    `checked_weights` refuses a zero, negative, non-finite or non-numeric weight
    before any draw is taken, and the stratified branch draws `len(pool) >= 1`
    rows from each non-empty pool. So a column's `resample_draws` — once a later
    slice wires `statistics.resample` for recorded columns into `summarize_step`
    (today's build still refuses a declared `resample` with
    `E-STATS-RESAMPLE-UNSUPPORTED`, and the recorded-column branch there carries
    no `resample_draws` key at all) — can safely be the REQUESTED `n` rather than
    a survivor count, and `percentile_over_units`'s return type need not change to
    carry one. The invariant is pinned by
    `test_a_column_resample_is_never_degenerate_across_adversarial_columns`
    rather than asserted here.
    """
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
    # One weight vector for every branch below, so a value and its weight are
    # paired once. `checked_weights` gates before any draw rather than producing
    # `draws` worth of `nan`, and it is the one authority `validate` and
    # `kish_effective_n` also read.
    carried = None if weights is None else checked_weights(weights)
    rng = random.Random(seed)
    if strata is not None:
        # Grouped BEFORE any sort, carrying (value, weight) pairs, then each
        # group sorted and the groups ordered by their own sorted contents —
        # so the interval depends on the multiset of (value, weight, stratum)
        # triples and on nothing else, not on row order and not on the labels.
        pools: dict[Any, list[tuple[float, float]]] = {}
        pairs_in = zip(
            values,
            strata,
            [1.0] * len(values) if carried is None else carried,
            strict=True,
        )
        for value, stratum, weight in pairs_in:
            pools.setdefault(stratum, []).append((value, weight))
        ordered = sorted(sorted(group) for group in pools.values())
        # If every stratum's own (value, weight) pairs are all identical, no
        # draw can ever come out different from any other: a singleton
        # stratum is the special case of this (one pair, trivially "all
        # identical"), but the same guarantee holds for a larger stratum whose
        # rows all happen to carry one repeated pair. That is a structural
        # guarantee — true for whatever the repeated pair's value is — and not
        # a data coincidence the way "one of several strata is constant while
        # the others vary" is: the latter still draws its variance from the
        # strata that aren't constant, and stays a reportable interval.
        # `percentile_over_units_clustered` refuses its own zero-freedom case
        # (`G < 2`) for the same reason `reference.md` § Statistical reporting
        # gives: "reporting a point with no interval is honest; a zero-width
        # 95 % interval is not."
        if all(len(set(group)) <= 1 for group in ordered):
            return None
        means_out: list[float] = []
        for _ in range(draws):
            # Each stratum contributes exactly as many rows as it holds: that
            # is the composition the design ruled the alternatives out of.
            drawn = [
                group[rng.randrange(len(group))]
                for group in ordered
                for _ in range(len(group))
            ]
            if carried is None:
                means_out.append(sum(v for v, _ in drawn) / len(drawn))
            else:
                means_out.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means = sorted(means_out)
    elif carried is not None:
        # `sorted` over the pairs, so a value and its weight travel together; the
        # gate is `checked_weights`, the one authority `validate` and
        # `kish_effective_n` also read, and it runs before any draw rather than
        # producing 2000 draws' worth of `nan`.
        pairs = sorted(zip(values, carried, strict=True))
        n = len(pairs)
        drawn_means = []
        for _ in range(draws):
            drawn = [pairs[rng.randrange(n)] for _ in range(n)]
            drawn_means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
        means = sorted(drawn_means)
    else:
        # Sorted, not just `list(values)`: with a fixed seed, `rng.randrange(n)`
        # draws the same sequence of *indices* regardless of input order, so
        # drawing from an unsorted pool would make the resample depend on row
        # order — the multiset of values must be all that matters.
        pool = sorted(values)
        n = len(pool)
        means = sorted(sum(pool[rng.randrange(n)] for _ in range(n)) / n for _ in range(draws))
    lo, hi = _percentile_ranks(draws, confidence)
    return Interval(low=means[lo], high=means[hi], method="percentile_over_units")


def percentile_over_units_clustered(
    values: Sequence[float],
    keys: Sequence[str],
    membership: Mapping[str, str],
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    weights: Sequence[Any] | None = None,
    strata: Sequence[Any] | None = None,
) -> Interval | None:
    """A percentile interval that resamples whole CLUSTERS, not rows.

    `reference.md` § Clustered units: "`resample` resamples clusters, not rows. A
    bootstrap that draws 300 cells with replacement from 10 animals produces
    resamples far more alike than a fresh sample of animals would be, so the
    percentile interval comes out too narrow… Core draws whole clusters with
    replacement, so a resampled table has a varying row count, and the interval's
    effective `n` is the cluster count." § Statistical reporting says the same
    thing for the contrast forms — "the percentile forms resample whole clusters"
    — and `experimental-designs.md` § Mistakes core prevents states the size of
    it: "300 cells from 10 animals give a 10-draw interval".

    **Each replicate draws `G` clusters with replacement and pools their units**,
    where `G` is the cluster count. That is the whole construction, and the two
    ways to get it wrong both produce a plausible number:

    - Drawing `n` units and repairing the groups afterwards is a 300-draw
      interval however carefully the groups are respected — the count of
      independent draws is what the document names, and it is `G`.
    - Averaging the drawn clusters' MEANS gives every cluster equal say. The
      document says "pools their units" and calls out the "varying row count"
      that follows, so a large cluster contributes more rows than a small one.
      The two coincide exactly when the clusters are the same size, which is why
      the fixtures here are deliberately unbalanced.

    `G` comes from `units.cluster_count_of` — task 8's single counting expression,
    so this cannot disagree with the `n.clusters` printed beside the interval or
    with a fold's partition about what one cluster is. The number of pools drawn
    from agrees with it *by construction* rather than by assertion: both are the
    distinct values `membership` takes over these same `keys`.

    **Each value keeps its cluster (and its weight) through the sort**, because
    the grouping happens before any sort and carries the pairs. The pool is sorted
    for the row-order invariance `percentile_over_units` explains — a fixed seed
    draws a fixed sequence of *indices*, so the multiset must be all that matters
    — and clusters are ordered by their own sorted contents rather than by label,
    which is what makes a relabelled roster give the identical interval and what
    makes the one-unit-per-cluster case reproduce `percentile_over_units` digit
    for digit. Sorting values and cluster labels as separate sequences would
    preserve the invariance and silently re-pair them; equal-sized clusters cannot
    see that, and neither can clusters whose value ranges don't interleave.

    **The floor is two clusters, and it is a derivation rather than an analogy to
    `t_over_units_clustered`'s df.** A percentile interval has no df. At `G = 1`
    every replicate draws the same single cluster, so the resampled distribution
    is a point mass, both ranks land on it and the interval has zero width —
    which § Statistical reporting refuses in those terms: "a zero-width 95 %
    interval is not [honest]", and "reporting a point with no interval is
    honest". The `len(values) < 2` guard in front of it is
    `percentile_over_units`' own floor, kept so the two constructions refuse the
    same degenerate inputs, and `draws < min_honest_draws(confidence)` is
    orthogonal to both — that one is about how many replicates the ranks are read
    off, not about how many things each replicate draws.

    **There is deliberately no higher threshold on `G` here.** A three-cluster
    resample reports, and the judgment that it is too few belongs to
    `limits.min_clusters` — `reference.md` § The one config file:
    "`validate` warns when `resample` would draw fewer than this". A second
    threshold in this module would be a competing authority for one judgment.

    With `weights`, the statistic recomputed on each draw is the weighted mean
    over the pooled units and the draw itself is unchanged. That is the
    composition of two sentences rather than a choice: § Weighted samples says a
    percentile interval "recomputes the weighted statistic on each draw, so the
    weights are in the estimate rather than in the drawing", unqualified by what
    the draw is, and then says "`cluster_by` still decides the draw when both are
    declared, since a cluster is what's independent and a weight is what it
    represents" — which moves the draw and says in its reason clause that the two
    live in different places. A cluster drawn twice contributes its units' weights
    twice, which is the only reading of "pools their units". `checked_weights`
    gates once before any grouping, for the reason the unclustered weighted branch
    states: a bad weight is refused before the draw rather than producing 2000
    draws' worth of `nan`.

    `strict=True` on the zip, for the reason `_weighted_mean` uses it: a
    keys/values length mismatch is a misaligned cluster vector, and it would
    produce a plausible number rather than an error.

    **With `strata`, a stratum must be constant within a cluster, and the draw
    is a cluster drawn within its stratum.** `stratify_by` says what an
    independent draw is; `cluster_by` says the draw IS a cluster — composed,
    `reference.md` § Clustered units already requires exactly this constancy
    for `fold`, `holdout` and `assign`, so this is the same rule taken again
    rather than a second one invented for `resample`. A cluster carrying two
    stratum values cannot be dealt to either, being indivisible, and is refused
    as `E-STATS-RESAMPLE-STRATIFY-VARIES` — `validate` reports the declaration
    form of the same fault from the roster, through
    `units.stratum_varies_within_cluster`. This is the run-time half of that
    dual listing, but **not by sharing one authority the way
    `E-DATA-WEIGHT-INVALID` does** — `stats.py` cannot import `units.py`, so
    this re-implements the equality over plain sequences instead of calling
    that function over a roster, and is normalized the identical way it is
    ("no value" for `None`, `str()` otherwise) so the two independent checks
    cannot disagree over a stratum read back as `1` in one place and `"1"` in
    the other. Each stratum then draws exactly as many clusters, with
    replacement, as it holds — preserving each stratum's own cluster count the
    way the unstratified draw preserves `G`.

    **The degenerate case is content, not count.** When every stratum's own
    clusters are pairwise identical (a singleton stratum trivially so),
    drawing any of a stratum's clusters with replacement reproduces the same
    pooled contribution on every replicate, so if this holds for every stratum
    the whole draw is invariant — the same "a zero-width 95% interval is not
    honest" refusal `percentile_over_units`'s own strata branch already gives
    for content-identical values, one level up over clusters rather than over
    values, and this returns `None` too. A COUNT floor alone (every stratum
    holding fewer than two clusters) is not sufficient: two clusters per
    stratum with identical content pass a count floor and are still
    degenerate, which is why this checks content and applies whether or not
    `strata` was given — the unstratified path had the identical hole at
    `G == 2`, since `groups < 2` alone answers a different question from
    whether the draw can vary.
    """
    if len(values) < 2:
        return None
    if draws < min_honest_draws(confidence):
        return None
    groups = cluster_count_of(membership, keys)
    if groups < 2:
        return None
    # Unit weights of 1.0 when none were declared, so the pairs have one shape;
    # the unweighted branch below still computes a plain mean, so this cannot move
    # an unweighted interval by a digit.
    carried = [1.0] * len(values) if weights is None else checked_weights(weights)
    # Grouped BEFORE any sort, indexed rather than `.get`-ed for the reason
    # `cluster_count_of` states: a key the roster doesn't hold is a core defect,
    # and a cluster of its own for it would raise `G`.
    pools: dict[str, list[tuple[float, float]]] = {}
    for value, key, weight in zip(values, keys, carried, strict=True):
        pools.setdefault(membership[key], []).append((float(value), weight))
    # A stratum must be CONSTANT within a cluster, and this is a composition of
    # two declarations rather than a third rule: `stratify_by` says what an
    # independent draw is, `cluster_by` says the draw IS a cluster, and a cluster
    # carrying two stratum values cannot be dealt to either, being indivisible.
    # § Clustered units already imposes exactly this on `fold`, `holdout` and
    # `assign`; `validate` reports the declaration form of the identical fault
    # through `units.stratum_varies_within_cluster`, and this is the run-time
    # half — but, unlike `E-DATA-WEIGHT-INVALID`'s single `usable_weight`
    # authority shared by both call sites, `stats.py` cannot import `units.py`
    # and so cannot call that function; this re-implements its equality over
    # plain sequences instead of a roster. Normalized the SAME WAY that
    # function is — "no value" for `None`, `str()` otherwise — so the two
    # independent checks cannot disagree over a stratum read as `1` in one
    # place and `"1"` in the other, which raw `!=` would have called a
    # violation.
    cluster_stratum: dict[str, str] = {}
    if strata is not None:
        for key, stratum in zip(keys, strata, strict=True):
            cluster = membership[key]
            rendered = "no value" if stratum is None else str(stratum)
            if cluster in cluster_stratum and cluster_stratum[cluster] != rendered:
                raise ContractError(
                    f"cluster {cluster!r} carries stratum values "
                    f"{cluster_stratum[cluster]!r} and {rendered!r}. A resample draws "
                    "whole clusters, so a cluster cannot be drawn within one stratum "
                    "while carrying two; stratify on an attribute that is constant "
                    "within a cluster, or drop `cluster_by` if the units really are "
                    "independent",
                    code="E-STATS-RESAMPLE-STRATIFY-VARIES",
                )
            cluster_stratum[cluster] = rendered
    ordered = sorted(sorted(pool) for pool in pools.values())
    rng = random.Random(seed)
    if strata is None:
        stratum_pools = [ordered]
    else:
        # Cluster pools grouped by the stratum their cluster carries, then each
        # group ordered by its own sorted contents — the same label-independence
        # the unstratified `ordered` gets, one level up.
        by_stratum: dict[str, list[list[tuple[float, float]]]] = {}
        for cluster, pool in pools.items():
            by_stratum.setdefault(cluster_stratum[cluster], []).append(sorted(pool))
        stratum_pools = [sorted(group) for group in by_stratum.values()]
        stratum_pools.sort()
    # Content-based, not count-based, and checked whether or not `strata` was
    # given: if every stratum's own clusters are pairwise IDENTICAL in content
    # (a stratum holding a single cluster is trivially so), drawing any of them
    # with replacement reproduces the same pooled contribution every time, so
    # no draw can ever come out different from any other — whatever count of
    # clusters that stratum holds. `percentile_over_units`'s own strata branch
    # refuses the analogous shape ("every stratum's own (value, weight) pairs
    # are all identical") for the identical reason, `reference.md` §
    # Statistical reporting: "a zero-width 95% interval is not honest" — this
    # is that same check one level up, over CLUSTERS rather than over values.
    # With no strata this is one group holding every cluster, so two
    # content-identical clusters at `G == 2` are refused here too, which
    # `groups < 2` alone does not catch — a count floor and a content check
    # answer different questions, and this construction had only asked the
    # first.
    if all(len({tuple(cluster) for cluster in group}) <= 1 for group in stratum_pools):
        return None
    means: list[float] = []
    for _ in range(draws):
        # Each stratum contributes exactly as many CLUSTERS as it holds — the
        # composition of "the draw is a cluster" with "each stratum keeps its
        # size". With no strata this is one group holding every cluster, which
        # is the unstratified draw digit for digit.
        drawn = [
            pair
            for group in stratum_pools
            for _ in range(len(group))
            for pair in group[rng.randrange(len(group))]
        ]
        if weights is None:
            means.append(sum(v for v, _ in drawn) / len(drawn))
        else:
            means.append(_weighted_mean([w for _, w in drawn], [v for v, _ in drawn]))
    means.sort()
    lo, hi = _percentile_ranks(draws, confidence)
    return Interval(
        low=means[lo], high=means[hi], method="percentile_over_units_clustered"
    )


def percentile_of_derived(
    collapsed: dict[str, dict[str, float]],
    compute: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
) -> tuple[Interval | None, int]:
    """A percentile interval for a derived metric, by recomputing it, and the
    number of draws it actually rests on.

    A derived metric has no per-unit value to resample directly — `aggregate`
    returned one number for the whole table, not one per unit — so this is
    the construction `reference.md` § How a metric becomes a number specifies:
    resampling requires recomputing the metric, "which core can do only for a
    metric it knows how to compute... a template `aggregate(units, cfg)`."
    `stats.py` stays pure by taking `compute` as a plain callable rather than
    importing anything: the caller (`cli.py`) closes over the template and
    `cfg`, and this function never does.

    Costs `draws` calls to `compute` — 2000 by default, matching
    `percentile_over_units` — so a caller wrapping an expensive `aggregate`
    should pass a smaller `draws`, and a test exercising this should too.

    Units are sorted by key before drawing, for the same row-order invariance
    `percentile_over_units` gets from sorting its own pool: a fixed seed draws
    a fixed sequence of *indices*, so an unsorted roster would make the
    interval depend on iteration order rather than on the multiset of units.
    Each draw's `UnitTable` is built with the *real* unit keys a bootstrap draw
    repeats, not a synthetic `0..n-1` re-key — `UnitTable` derives its `unit`
    column from the mapping key it was built from, so re-keying would make
    `units.unit` read as `n` distinct labels inside every draw even though a
    resample duplicates units by construction; a template that legitimately
    reads `unit` (a per-unit weight lookup keyed by it, say) would silently see
    the wrong roster. A plain dict can't hold the resulting duplicate keys, so
    the table is built from a row list instead, bypassing the dict-keyed
    constructor.

    A draw on which `compute` returns `None`, returns `nan`, or *raises* is
    dropped rather than counted. The three are the same situation from three
    different libraries: a resampled table with no variance makes `pearsonr`
    return `nan`, makes a hand-rolled ratio raise `ZeroDivisionError`, and a
    template author who checks for that case explicitly return `None` — which
    library `aggregate` happens to call is not a fact about whether the draw
    was degenerate, so it can't be what decides whether the draw counts. The
    one call this function does *not* make robust this way is the single
    unresampled call to `aggregate` that produces the reported `value` — that
    one is the metric's real definition for this table, so a failure there is
    a fault to surface, not a degenerate draw to skip, and is contained by the
    caller instead (`cli.py`, where the failure is disclosed rather than
    silently producing a table this function has no way to distinguish from
    "computed cleanly on the third try").

    Counting `None`/`nan`/raise as skipped can only shrink the surviving count
    relative to `draws`, so the percentile ranks are read off *that* count,
    and the second return value is that surviving count — **always**, even
    when the interval is `None`. That is what lets `summarize_step` tell "the
    resample was attempted and every draw was degenerate" (a surviving count
    of 0) apart from "resampling was never attempted at all" (no count
    to report), which otherwise reach `run.yaml` byte-identical: both would
    write `ci95: null` and nothing else. An interval quietly built from 200 of
    2000 requested draws would read identically to a clean one for the same
    reason, which is why the count is returned even on success. Below
    `min_honest_draws(confidence)` survivors — 80 at 95 % — there is no
    interval a percentile can honestly be read off (that function says why),
    so the interval is `None` while the count returned alongside it stays
    real. `cli.py` warns on any shortfall, a count below the floor and a count
    merely reduced being the same event at two magnitudes.
    """
    keys = sorted(collapsed)
    if len(keys) < 2:
        return None, 0
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        table = unit_table_from_rows([{"unit": key, **collapsed[key]} for key in drawn])
        try:
            value = compute(table)
        # Degenerate, not caught for the real call; see above. Also the
        # containment for a template returning a non-numeric metric:
        # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return
        # reaches `cli.py`'s resample closure, which floats whatever
        # `aggregate` returned — and `float("high")` raises `ValueError` on
        # every draw, caught here beside a degenerate `ZeroDivisionError`.
        # Narrowing this to a closed set that drops `ValueError` reopens that
        # path; see the pin in tests/test_stats.py.
        except Exception:
            continue
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        values.append(float(value))
    if len(values) < min_honest_draws(confidence):
        return None, len(values)
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return (
        Interval(low=values[lo], high=values[hi], method="percentile_over_units"),
        len(values),
    )


def paired_delta_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
) -> float | None:
    """The point estimate `paired_percentile_of_derived` builds an interval for.

    A derived metric has no per-unit value to difference, so its delta has to be
    `aggregate` evaluated on each side and subtracted — but over **the same
    units the interval is built from**, which is the intersection of both sides'
    completed units narrowed by the contrast's `within`, not each condition's
    own whole-sample table. `reference.md` § Contrasts: "a paired comparison
    exists only for units that completed in *both*. Differencing the two
    condition means instead would not be a paired comparison at all, however
    carefully `paired: true` was derived."

    It lives here, beside the interval it belongs to, because the two were
    computed in different modules once and drifted apart: the interval moved to
    the intersection and the point estimate stayed whole-sample, which produced
    a `ci95` that could not contain its own `delta`. A caller that can only get
    both from one call cannot reintroduce that.

    `None` — never a number — when there are no paired units or either side's
    `aggregate` declines to produce a value. `reference.md`: "A contrast whose
    intersection is empty is reported as such rather than as a delta of zero."
    """
    if not keys:
        return None
    table_of = unit_table_from_rows([{"unit": k, **of[k]} for k in keys])
    table_against = unit_table_from_rows([{"unit": k, **against[k]} for k in keys])
    try:
        a = compute_of(table_of)
        b = compute_against(table_against)
    # The same treatment the real call gets in `percentile_of_derived`. Also
    # the same containment for a template returning a non-numeric metric:
    # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return reaches
    # `cli.py`'s resample closure, which floats whatever `aggregate`
    # returned — and `float("high")` raises `ValueError`, caught here.
    # Narrowing this to a closed set that drops `ValueError` reopens that
    # path; see the pin in tests/test_stats.py.
    except Exception:
        return None
    if a is None or b is None:
        return None
    delta = float(a) - float(b)
    return None if math.isnan(delta) else delta


def paired_percentile_of_derived(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
) -> PairedResample:
    """Percentiles of the resampled difference, one draw applied to both sides.

    Drawing each side independently would resample the two conditions apart and
    destroy the pairing — the same error as differencing the two sides' own
    intervals. Both spellings produce a plausible interval; only this one is
    narrower, which is what `allocation: within` buys.

    Two computes, not one — a contrast can hold its two sides' `cfg` fixed on
    every axis except the one being compared, but `aggregate(units, cfg)` is
    still evaluated once per side with that side's own `cfg`. A single shared
    `compute` (as an earlier revision of this function took) is only correct
    when the two sides evaluate the same formula; the moment a swept axis
    changes which formula `aggregate` runs — analysis.method: pearson vs.
    spearman, the documented worked example's own case — a shared compute
    evaluates *one* side's formula against *both* sides' resampled draws. Where
    the two collapsed tables hold identical per-unit data (exactly the
    worked-example shape: `pred`/`truth` don't vary with `analysis.method`,
    only which correlation `aggregate` computes from them does), that shared
    evaluation cancels on every single draw — a `ci95` of zero width at zero,
    beside a nonzero point-estimate delta, the "plausible but wrong" case with
    nothing to raise. A caller that genuinely wants the same statistic on both
    sides passes the same callable twice; that's a normal call, not a special
    case this function has to detect.
    """
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    n = len(keys)
    values: list[float] = []
    for _ in range(draws):
        drawn = [keys[rng.randrange(n)] for _ in range(n)]
        table_a = unit_table_from_rows([{"unit": k, **of[k]} for k in drawn])
        table_b = unit_table_from_rows([{"unit": k, **against[k]} for k in drawn])
        try:
            a = compute_of(table_a)
            b = compute_against(table_b)
        # A degenerate draw, not a fault; see `percentile_of_derived`. Also the
        # same containment for a template returning a non-numeric metric:
        # `coerce_scalars` accepts a `str`, so a `{"m": "high"}` return reaches
        # `cli.py`'s resample closure, which floats whatever `aggregate`
        # returned — and `float("high")` raises `ValueError`, caught here.
        # Narrowing this to a closed set that drops `ValueError` reopens that
        # path; see the pin in tests/test_stats.py.
        except Exception:
            continue
        if a is None or b is None:
            continue
        diff = float(a) - float(b)
        if math.isnan(diff):
            continue
        values.append(diff)
    if len(values) < min_honest_draws(confidence):
        return PairedResample(interval=None, draws_used=len(values), pool=sorted(values))
    values.sort()
    lo, hi = _percentile_ranks(len(values), confidence)
    return PairedResample(
        interval=Interval(low=values[lo], high=values[hi], method="paired_percentile_over_units"),
        draws_used=len(values),
        pool=values,
    )


def _is_numeric(value: object) -> bool:
    """`bool` is a `int` subclass in Python but is never a quantity to average."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def handed_to(
    unit_key: str, labels: list[str], fold_members: dict[str, frozenset[str]] | None
) -> list[str]:
    """The repeat labels this unit was actually given.

    Without a fold, every repeat — the S2 rule, and the reason `fold_members=None`
    leaves every existing path on exactly the membership and values it had. With a
    fold, only the
    labels whose fold component holds this unit: `reference.md` § The per-unit
    tables is explicit that intersecting over *every* repeat "would report
    `completed: 0` for any design containing a fold, because no unit is ever in
    more than one of them."

    A composed label is split on `LABEL_JOIN`, so `fold02_seed17` is handed to a
    unit of `fold02` regardless of which level the fold was declared at. Fold
    member labels are single tokens (`fold01`, from `replication._seed_members`),
    which is what makes that split safe.
    """
    if fold_members is None:
        return list(labels)
    mine = {f for f, keys in fold_members.items() if unit_key in keys}
    return [lb for lb in labels if set(lb.split(LABEL_JOIN)) & mine]


def collapse_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, float]]:
    """Average each unit's numeric columns across the repeats that recorded it,
    within one condition.

    This is the collapse the inference base rests on: repeats are a variance
    component, not the inference base, so a unit's repeats are averaged into one
    row *before* any interval is computed over units.

    `condition_index` is required, not defaulted, on purpose: core aggregates
    within each condition and never pools across conditions, which would be
    meaningless (`reference.md` § Statistical reporting). Making the parameter
    required turns a caller that forgets it into a `TypeError` at the call site
    rather than a silently pooled mean in a `run.yaml` no reviewer could catch —
    S2 always has exactly one condition and always passes `0`, but the signature
    must not invite the mistake on the day a sweep adds a second one.

    Reads only `repeat`-scoped executions of `step_name` in this condition — a
    `condition`- or `run`-scoped step's rows, another step's rows, and another
    condition's rows never enter this table.

    Only a unit recorded in every repeat it was *handed* (within this condition)
    enters the table at all — the same intersection `runner.attrition` takes for
    `completed`, and for the same reason: a unit present in three of five seeds
    would otherwise enter the average on a different number of observations than
    its neighbours, which is a ragged table dressed as a rectangular one. A unit
    recorded in some of the repeats it was handed and not others is dropped here
    exactly as it is excluded from `completed` there, so the `n` reported beside
    this table's interval is never a lie about how many observations went into it.

    "Handed" is what `fold_members` narrows. Without a fold it is every repeat,
    which is the rule above unchanged. With one, `reference.md` § The per-unit
    tables is explicit that intersecting over *every* repeat "would report
    `completed: 0` for any design containing a fold, because no unit is ever in
    more than one of them" — so the intersection is taken over that unit's own
    fold's repeats instead. The average follows from the same set, which is what
    makes the collapse **inner-to-outer** (`reference.md` § How a metric becomes
    a number): under `fold` alone a unit has one handed label and its value
    passes through unchanged, so folds *concatenate* into the union of the
    partitions; under `fold × seed` the handed labels are that fold's seeds, so
    the seeds average within the fold before the folds are combined. Flattening
    all 30 executions of a 10 × 3 design would average numbers that are not
    exchangeable, and averaging across folds would divide each unit's single
    observation by one — both produce plausible values and neither raises, which
    is why this is stated at length.

    A non-numeric value (a string, or a bool — `bool` is an `int` subclass but
    never a quantity to average) is dropped from the column for that unit rather
    than averaged; a unit that recorded a column as a string in every repeat
    simply has no entry for that column in the collapsed table, which
    `summarize_step` then correctly omits rather than reporting a bogus mean.
    """
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        # Strict, for the same reason as `runner.attrition`: `or 0` would fold an
        # unexpected `None` into condition 0's table, which is the cross-condition
        # pooling the required `condition_index` parameter exists to make unwritable.
        and r.execution.condition_index == condition_index
    ]
    if not recording:
        return {}
    # Accumulated rather than built by comprehension: two executions sharing one
    # repeat label (a resumed leaf re-reported, say) must merge, not overwrite.
    # A dict comprehension would drop the earlier rows while `labels` still held
    # the label once per execution, counting the survivor twice in the mean —
    # a wrong average that looks entirely plausible.
    rows_by_label: dict[str, list[dict[str, Any]]] = {}
    recorded_by_label: dict[str, set[str]] = {}
    for r in recording:
        label = r.execution.repeat_label or ""
        rows_by_label.setdefault(label, []).extend(r.rows)
        recorded_by_label.setdefault(label, set()).update(r.recorded)
    labels = list(recorded_by_label)  # unique, in execution order

    candidates: set[str] = set()
    for keys in recorded_by_label.values():
        candidates |= keys

    gathered: dict[str, dict[str, list[float]]] = {}
    # `sorted`, and load-bearing rather than incidental: `summarize_step` derives a
    # metric's column order from this dict's values, so a ragged table's `run.yaml`
    # column order follows this loop. Encounter order varies with `order: randomized`
    # — the shuffle decides which execution is seen first — so sorting is what makes
    # that order a property of the roster instead of of the shuffle.
    for key in sorted(candidates):
        mine = handed_to(key, labels, fold_members)
        # The intersection, scoped to what this unit was handed. `not mine` drops
        # a unit no repeat was given — under a fold, one whose key is in no
        # partition — rather than letting `all()` over an empty set admit it.
        if not mine or any(key not in recorded_by_label[lb] for lb in mine):
            continue
        for lb in mine:
            for row in rows_by_label[lb]:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    if column == "unit" or not _is_numeric(value):
                        continue
                    gathered.setdefault(key, {}).setdefault(column, []).append(float(value))
    return {
        key: {col: sum(vals) / len(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }


def paired_keys(
    of: dict[str, dict[str, float]],
    against: dict[str, dict[str, float]],
    allowed: set[str] | None,
) -> list[str]:
    """The units both sides completed, narrowed by a `within` stratum if given.

    The intersection, not the union: a unit that completed in one condition and
    failed in the other has no difference to contribute, and counting it would
    put a number in `n_paired` that no per-unit difference backs.

    Sorted so a resample over these keys is row-order invariant, the same reason
    `percentile_over_units` sorts its pool.
    """
    keys = set(of) & set(against)
    if allowed is not None:
        keys &= allowed
    return sorted(keys)


def _is_anonymous_level(level: "RepeatLevel") -> bool:
    """The single-`seed`-level `resolve_repeats` synthesizes when no
    `replication` block is declared at all — never produced by a declared
    level, since every declared `seed`/`batch`/`fold` member gets a real,
    non-empty label from `_seed_members`. It's an implementation detail of
    how core represents "no repeats declared", not a design the user
    expressed, which is why `repeat_spread` gives it no entry while a
    *declared* `{kind: seed, n: 1}` still reports `{std: 0.0, n: 1, ...}`.
    """
    return level.kind == "seed" and level.n == 1 and level.members[0].label == ""


def repeat_spread(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    levels: "list[RepeatLevel]",
    column: str,
    keys: "Collection[str]",
) -> list[dict[str, Any]]:
    """How much each repeat level moved one metric's recorded values, one
    entry per level, outer to inner — `reference.md` § A `batch` says *when*,
    not *what*. `column` is the one recorded column this figure describes:
    pooling every numeric column of a row into one mean would average, say,
    `pred` and `truth` together and then report that blended number as the
    dispersion of each — dispersion is per metric, the same way the interval
    beside it is.

    A `fold` level contributes no entry on its own: each unit appears in
    exactly one fold, so there is nothing to average across (the same reason
    S3c's collapse concatenates across folds rather than averaging). Nested
    with another level (`fold x seed`), the honest per-level figure would
    need the metric recomputed over each fold's own slice — a materially
    heavier operation this passenger does not implement — so the whole
    result is omitted rather than reporting a differently-computed number
    under the same key; see `docs/superpowers/spec-defects.md`. The anonymous
    single-seed level (no `replication` block declared) is skipped the same
    way `fold` is, via `_is_anonymous_level`.

    Every other level gets a per-member mean of its recorded values for
    `column`, then the population standard deviation (divide by `n`, not
    `n - 1`) of those member means — population rather than sample so a
    single-member level falls out as exactly `0.0` with no special case,
    which is what a lone repeat's dispersion honestly is. `n` is the number
    of members that actually contributed a mean, not the level's declared
    count: a member with no matching rows for this column contributes
    nothing, and `std`/`n` must describe the same set of numbers.

    A member's rows are found by matching its label against the tokens of
    each execution's composed `repeat_label`, split on `LABEL_JOIN` — the
    same idiom `realize_order` uses to find a batch's rows inside
    `batch01_seed42`.

    `keys` is the unit set this figure is allowed to read: the keys of the
    collapsed table the `value` and `ci95` beside it rest on. Required rather
    than defaulted, so no call site can forget it. Reading *every* recorded
    row instead would compute the dispersion over a different population than
    the interval printed under the same metric key: a unit recorded in one
    repeat and lost in another is excluded from `collapse_repeats` by the same
    intersection that defines `completed`, but its lone value would still move
    one member's mean and none of the others, so ordinary single-unit
    attrition reads as a pipeline that is wildly unstable — or, under `batch`,
    as apparatus drift. That is the "ragged table dressed as a rectangular
    one" confound `collapse_repeats` refuses, and this filter is what keeps it
    from re-entering one field over.
    """
    admitted = set(keys)
    if len(levels) > 1 and any(lv.kind == "fold" for lv in levels):
        return []
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        and r.execution.condition_index == condition_index
    ]
    entries: list[dict[str, Any]] = []
    for level in levels:
        if level.kind == "fold" or _is_anonymous_level(level):
            continue
        member_means: list[float] = []
        for member in level.members:
            values = [
                float(row[column])
                for r in recording
                if member.label in (r.execution.repeat_label or "").split(LABEL_JOIN)
                for row in r.rows
                if row["unit"] in admitted and column in row and _is_numeric(row[column])
            ]
            if values:
                member_means.append(sum(values) / len(values))
        if not member_means:
            continue
        grand_mean = sum(member_means) / len(member_means)
        variance = sum((m - grand_mean) ** 2 for m in member_means) / len(member_means)
        entries.append({"std": math.sqrt(variance), "n": len(member_means), "kind": level.kind})
    return entries


def summarize_step(
    collapsed: dict[str, dict[str, float]],
    counts: dict[str, float],
    derived: dict[str, Any] | None = None,
    seed: int | None = None,
    resample: "dict[str, Callable[[UnitTable], float | None]] | None" = None,
    draws: int = 2000,
    beside_n: dict[str, Any] | None = None,
    weights: dict[str, Any] | None = None,
    clusters: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Per-column value, basis, `n`, and interval over the collapsed unit table.

    Every column here is `basis: units`: it was a recorded column, `n` counts
    units, and the interval is `t_over_units` over the per-unit values — or
    `None` below two units, since a single observation has no dispersion to
    describe and inventing an interval for it would not be honest.

    `n.completed` is per COLUMN, not the condition-wide figure `counts` carries:
    `StepIO.finalize()` deliberately writes the union of recorded keys with nulls
    for columns a unit didn't carry, so a column recorded only for a subset of
    completed units — eligible-positive units, say — is an ordinary ragged shape,
    not a bug. Reporting the condition-wide `completed` beside that column's
    interval would be a lie about how many observations went into it, which is
    exactly the guarantee this module's own docstring makes. `resolved`,
    `ineligible`, and `failed` stay condition-wide from `counts`: they describe the
    roster a condition drew from, not any one column, and every column in the
    table shares that one roster.

    A column is skipped entirely — not coerced, not defaulted — when any unit's
    value for it is not a real number (a string, or a `bool`, which is an `int`
    subclass but never a quantity to average). Averaging a bool would silently
    read as a proportion; this refuses that rather than doing it quietly.

    `derived` is what a template's `aggregate` returned for this step, name →
    scalar, already computed once over the whole table for the reported
    `value`. `resample` is the matching name → callable, each one recomputing
    that one derived key on a resampled `UnitTable` — typically
    `lambda units: template.aggregate(units, cfg).get(key)`, closed over in
    `cli.py` since that is where the template and `cfg` live; `stats.py` never
    imports either. `percentile_of_derived` is what actually resamples: a
    derived metric has no per-unit value to run `t_over_units` over
    (`aggregate` returned one number, not one per unit), and `reference.md` §
    How a metric becomes a number is explicit that resampling one "can do only
    for a metric it knows how to compute... a template `aggregate(units,
    cfg)`" — recomputing is the only construction, there is no proxy for it. A
    key absent from `resample` (or given no `seed`) gets `ci95: null` rather
    than an invented width: reporting a point with no interval is honest.
    Every derived metric is `basis: units`, `method: percentile_over_units`
    when it has one, `cohens_d: null` — Cohen's *d* differences a per-unit
    value, and a derived metric has none — and `resample_draws`: `null` when
    resampling was never attempted (no callable, or no `seed`), and otherwise
    the number of `draws` (passed through to `percentile_of_derived`, 2000 by
    default) that actually produced a value — `0` when every one was
    degenerate, matching `ci95: null` there too. `null` and `0` are different
    facts: one says nobody tried to resample this metric, the other says
    resampling was attempted and failed, and a caller (`cli.py`) that only
    checked `ci95: null` could not otherwise tell which happened.

    A derived key colliding with a recorded column — even one dropped above for
    being non-numeric — is refused with the same `E-STEP-KEY-COLLISION`
    `artifacts.py` raises for the sibling case: one name cannot hold both a
    column's mean and a derived value.

    `beside_n` is core-supplied context copied verbatim into every metric block —
    `technical_n` today. It is the second of two routes a count-shaped fact
    travels, and which one a new fact takes is decided by where `reference.md`
    shows it:

    - **A key that JOINS `n` travels in `counts`.** § What isn't a repeat says the
      three-part `n` is "joined by `clusters` … by `effective` … by `ineligible`",
      so those are parts of `n` and need no new carrier. `effective` arrives that
      way — `runner.attrition` puts it there under a declared `weight_by` — which
      is why `counts` is annotated `dict[str, float]` rather than `dict[str,
      int]`: Kish's effective size is fractional for any uneven weighting, and
      rounding it would name a size no interval was computed at.
    - **A key that sits BESIDE `n` travels here.** § What isn't a repeat shows
      `technical_n` as a sibling of `n` in the metric block, and § Weighted
      samples shows `weighted_by` in the same position.

    Copied into the derived branch as well as the recorded-column one, because
    the document's own example of a metric carrying `technical_n` is `r`, which
    `aggregate` derives. The computed keys are merged last and so always win: a
    caller cannot shadow `n`, `value`, or an interval with a key of this name.

    `weights` is unit key → that unit's `data.units.weight_by` value, over the
    whole roster, supplied only when the config declares one — the same mapping
    `runner.attrition` takes, from the same place (`cli.py`), passed as the
    roster holds it because `units.usable_weight` is the single authority that
    reads a weight and it lives inside `checked_weights`. It changes a RECORDED
    COLUMN's arithmetic in three places at once, all of which § Weighted samples
    requires together: the `value` becomes the weighted mean, the interval
    becomes `weighted_t_over_units`, and `n.effective` becomes Kish's size. A
    weighted interval beside an unweighted point estimate would be a declaration
    accepted whose effect is half delivered, and it survives every check that
    reads only `ci95`.

    **The weights are aligned to the units the column came from**, not to the
    table and not to the roster: the value and its unit key are taken in one
    pass, and the weight is looked up per key. A vector filtered differently
    weights the wrong unit and produces a plausible number rather than an error.
    Indexed rather than `.get`-ed, for the reason `runner._counts` states: every
    key in the collapsed table came from the roster the caller built `weights`
    from, so a default would quietly change the denominator instead of failing.

    **`effective` is recomputed per column**, for exactly the reason `completed`
    already is (above): a column recorded by a subset of the completed units is
    an ordinary ragged shape, and printing the condition-wide effective size
    beside it would name a size no interval was computed at — § Weighted samples
    calls `effective` the size the interval *was* computed at. A full column's
    figure is identical to `counts`'; a ragged one's is its own. It is set here
    rather than left to `counts` so a stale value cannot survive the filter.

    A DERIVED metric is not weighted here, and that is the same document's other
    half: core "computes weighted means for `basis: units` column metrics, hands
    the column to `aggregate` like any other attribute so a derived metric can
    weight itself". There is no per-unit vector to weight — `aggregate` returned
    one number for the whole table — and a weighted mean *of* that one number is
    the number itself. Which weighting a derived metric needs is a property of
    what it computes (a weighted correlation is not a weighted mean of anything),
    so the weight column reaches `aggregate` as a unit attribute and the template
    decides; `cli.py`'s `_attributed` is what puts it there. `weighted_by` and
    `effective` still travel beside a derived metric — the declaration is true of
    the run either way, and § Weighted samples' own example of both is `r`, a
    derived metric.

    `clusters` is unit key → that unit's `data.units.cluster_by` value, over the
    whole roster, supplied only when the config declares one — the same mapping
    `runner.attrition` takes, from the same place. It adds `n.clusters`, the number
    of distinct clusters the column's own units fall in, counted by
    `units.cluster_count_of` (the single counting expression, so this cannot
    disagree with `attrition`'s figure or with a fold's partition about what one
    cluster is), **and it decides the interval**: a RECORDED COLUMN's becomes
    `t_over_units_clustered`, or `weighted_t_over_units_clustered` when a weight is
    declared too, since § Weighted samples has `cluster_by` decide the draw when
    both are. § Clustered units calls the unclustered interval over clustered data
    "too narrow" and § Statistical reporting names the construction, so a
    `cluster_by` that only added a count would be a declaration accepted whose
    effect is not delivered — the same half-delivery the weights paragraph above
    describes, and it survives any check that reads only `n`.

    **The keys the clusters are looked up by are the column's own**, taken in the
    same pass as its values, for the reason the weights are: a differently filtered
    vector groups the wrong unit, and the result is a number rather than an error.

    A DERIVED metric's interval **cannot be clustered here, so the combination is
    refused** — `E-DATA-CLUSTER-DERIVED`, raised below. The clustered draw for a
    recomputed metric is a different construction from
    `percentile_over_units_clustered` — each replicate drawing `G` clusters with
    replacement and building a `UnitTable` from their pooled units, whose row count
    varies per draw — and it does not exist. `percentile_of_derived` draws units,
    so left to run it would report an interval "too narrow" in exactly the sense
    § Clustered units names, beside recorded columns whose intervals *are*
    cluster-robust and with nothing in the record saying which is which.

    **Why the refusal is here rather than in `validate`.** Whether a template
    derives a metric is not knowable before the run: `aggregate` is user code, core
    never inspects the body of user Python, and a template that overrides
    `aggregate` may still return `{}` for a given config — so "returns derived
    metrics" has no validate-time meaning. This is the first point at which core
    holds the answer, and it holds it as a fact rather than a guess. `cli.py`
    contains the raise the same way it contains a derived key collision: the whole
    `derived` mapping is dropped and re-summarized without it, the code is
    disclosed through `W-STATS-AGGREGATE-FAILED`, and the run keeps its record and
    its recorded columns. **Dropped, not published with `ci95: null`** — that state
    already means "no resample callable, or no seed", and reusing it would
    reintroduce the ambiguity `resample_draws`' `0`-versus-`null` distinction
    exists to remove. H4 Statistics lifts this with the clustered contrast family
    (`E-DATA-CLUSTER-CONTRAST`), which is the same missing construction one level
    over.

    **`clusters` is recomputed per column**, for exactly the reasons `completed`
    and `effective` already are: § Clustered units reports the cluster count "as
    the effective sample size alongside the unit count" and § Statistical
    reporting gives `t_over_units_clustered` "df = clusters − 1", so the figure is
    the df of *this column's* interval, and a ragged column drawn from a subset of
    the completed units sits in a subset of their clusters. Printing the
    condition-wide count beside it would name a df no interval used. A full
    column's figure is identical to `counts`'; a ragged one's is its own.

    A DERIVED metric takes the condition-wide figure from `counts` instead, as it
    does for `effective`: `aggregate` returned one number over the whole collapsed
    table, so there is no per-column carrier set to recompute over.
    """
    columns: list[str] = []
    for cols in collapsed.values():
        for name in cols:
            if name not in columns:
                columns.append(name)
    out: dict[str, dict[str, Any]] = {}
    for column in columns:
        # One pass over `(key, value)`, so the weights below cannot be filtered
        # or ordered differently from the values they weight.
        carried = [(key, cols[column]) for key, cols in collapsed.items() if column in cols]
        raw = [value for _, value in carried]
        if not raw or not all(_is_numeric(v) for v in raw):
            continue
        values = [float(v) for v in raw]
        # The column's own keys, taken from the same pass the values were: the
        # cluster of a unit is looked up by key, so a vector filtered or ordered
        # differently would group the wrong unit and produce a plausible number.
        column_keys = [key for key, _ in carried]
        n_block: dict[str, Any] = {**counts, "completed": len(values)}
        if clusters is not None:
            n_block["clusters"] = cluster_count_of(clusters, column_keys)
        interval: Interval | None
        value: float | None
        if weights is None:
            value = mean_of(values)
            interval = (
                t_over_units(values)
                if clusters is None
                else t_over_units_clustered(values, column_keys, clusters)
            )
        else:
            column_weights = [weights[key] for key, _ in carried]
            value = weighted_mean_of(values, column_weights)
            n_block["effective"] = kish_effective_n(column_weights)
            interval = (
                weighted_t_over_units(values, column_weights)
                if clusters is None
                else weighted_t_over_units_clustered(
                    values, column_keys, clusters, column_weights
                )
            )
        out[column] = {
            **(beside_n or {}),
            "value": value,
            "basis": "units",
            "n": n_block,
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
            # `W-STATS-FAMILY` warns the person; this null tells the record. The
            # generated config declares `statistics.correction: holm` by default,
            # so a metric that said nothing here could be misread as corrected —
            # multiplicity correction across conditions is not implemented yet.
            "correction": None,
        }
    if derived:
        # A derived key may not take a name the step block already spends on
        # something that is not a metric. Refused here, beside the recorded-column
        # collision and with the same identifier, because it is the same fault:
        # one name cannot hold both a metric and the block's strata. The recorded
        # -column half of this cannot be refused here — the caller's retry passes
        # the same `collapsed` and would re-raise uncontained — so `cli.py` warns
        # for that one instead.
        reserved = set(derived) & RESERVED_METRIC_NAMES
        if reserved:
            name = sorted(reserved)[0]
            raise ContractError(
                f"{name!r} is reserved for a step block's reporting strata and may "
                "not be a derived metric name",
                code="E-STEP-KEY-COLLISION",
            )
        collision = set(derived) & set(columns)
        if collision:
            name = sorted(collision)[0]
            raise ContractError(
                f"{name!r} collides with a recorded column of the same name: a "
                "derived key may not shadow a recorded column",
                code="E-STEP-KEY-COLLISION",
            )
        # The clustered derived draw, refused rather than drawn as if independent
        # (the docstring says why it lives here and not in `validate`). Gated on
        # what would actually be *drawn*, not on the declaration: with no callable
        # or no seed no interval is built at all, so a clustered run whose derived
        # metric was never going to be resampled publishes its point estimate as
        # it always did and there is no too-narrow interval to prevent. Raised
        # before a single derived key is written, so the caller drops the whole
        # mapping rather than a record carrying some of it.
        if clusters is not None and seed is not None:
            drawable = sorted(k for k in derived if (resample or {}).get(k) is not None)
            if drawable:
                raise ContractError(
                    f"{drawable[0]!r} is derived by the template's `aggregate`, and its "
                    "interval is a percentile over resampled units while "
                    "`data.units.cluster_by` declares that units are not independent. "
                    "Resampling whole clusters for a recomputed metric is a construction "
                    "this build does not have, and drawing units instead would report an "
                    "interval narrower than the design supports beside recorded columns "
                    "that are cluster-robust. The derived metrics are dropped for this "
                    "step; the recorded columns keep their clustered intervals. Report "
                    "the derived value as an `Estimate` from a `summary` step, which core "
                    "records as reported rather than recomputing, or drop `cluster_by` if "
                    "the units really are independent",
                    code="E-DATA-CLUSTER-DERIVED",
                )
        for key, value in derived.items():
            compute = (resample or {}).get(key)
            # `draws_used` is `None` only when resampling was never attempted
            # at all (no callable, or no `seed`) — attempted-and-failed
            # reports `0`, not `None`, which is the distinction Task 6's
            # review named: without it, "every draw raised" and "nobody
            # supplied a `resample` callable" write the same `run.yaml`.
            derived_interval: Interval | None
            draws_used: int | None
            if compute is not None and seed is not None:
                derived_interval, draws_used = percentile_of_derived(
                    collapsed, compute, seed, draws=draws
                )
            else:
                derived_interval, draws_used = None, None
            out[key] = {
                **(beside_n or {}),
                "value": value,
                "basis": "units",
                "n": {**counts, "completed": len(collapsed)},
                "ci95": (
                    [derived_interval.low, derived_interval.high] if derived_interval else None
                ),
                "method": derived_interval.method if derived_interval else None,
                "correction": None,
                "cohens_d": None,
                # How many of `draws` requested actually produced a value —
                # `None` when resampling wasn't attempted, `0` (or `1`) when
                # it was attempted and every draw was degenerate, and the real
                # survivor count on success. A degenerate-draw-heavy interval
                # built from 200 survivors would otherwise read identically to
                # a clean 2000-draw one (see `percentile_of_derived`).
                "resample_draws": draws_used,
            }
    return out


class UnitTable:
    """Row iteration, column access, `len`, `columns` — and nothing else.

    Deliberately not a `DataFrame`: one that also promised indexing, filtering
    and `.loc` would be one, and core could never change what backs it — a lazily
    materialized table, a view over a partition — without breaking every plugin.
    The same reasoning that keeps `io.units` to three operations.
    """

    def __init__(self, collapsed: dict[str, dict[str, float]]) -> None:
        self._rows = [{"unit": key, **values} for key, values in collapsed.items()]

    def __iter__(self) -> Iterator[dict[str, Any]]:
        return iter(self._rows)

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def columns(self) -> list[str]:
        # A property, not something `__getattr__` serves: `__getattr__` runs only
        # when normal attribute lookup fails, so a real property is the only way
        # a recorded column literally named `columns` can't shadow it — the same
        # shadowing question `cfg`'s no-methods rule answers.
        seen: dict[str, None] = {}
        for row in self._rows:
            for key in row:
                if key != "unit":
                    seen[key] = None
        return list(seen)

    def __getattr__(self, name: str) -> list[Any]:
        """That column, as a sequence in row order — one entry per row, `None`
        where the unit recorded nothing.

        Full length rather than "the units that recorded it", which is what
        `reference.md` § Templates requires: `units.truth` and `units.pred`
        "are the same shape whichever of the two supplied them", and § The
        per-unit tables says "a column absent from a row reads as `None`".
        Dropping missing rows *per column* — the earlier rule, right for a
        single-column mean and wrong for every multi-column read — makes two
        columns ragged in *different* rows come back mispaired, so
        `pearsonr(units.pred, units.truth)` (`reference.md`'s own example)
        would correlate one unit's prediction against another's truth and
        publish it with a resampled interval around it. Row alignment is the
        only property that makes the pairing correct by construction; a
        template summing a column that holds a `None` gets a loud `TypeError`,
        contained and disclosed as `W-STATS-AGGREGATE-FAILED`.

        The refusal is keyed on "this name appears in no row", not on
        `columns` membership: `columns` deliberately omits `unit`, which a
        template may legitimately read (`percentile_of_derived` keeps the real
        unit keys inside every draw precisely so it can).
        """
        if name.startswith("_"):
            raise AttributeError(name)
        if not any(name in row for row in self._rows):
            raise ContractError(
                f"{name!r} is not a column this table holds; it has "
                f"{', '.join(self.columns) or 'no columns'}",
                code="E-STEP-COLUMN-UNKNOWN",
            )
        return [row.get(name) for row in self._rows]


def unit_table_from_rows(rows: list[dict[str, Any]]) -> UnitTable:
    """Build a `UnitTable` from rows that may repeat a unit key.

    `UnitTable.__init__` takes a `dict[str, dict]`, which cannot hold two rows
    for the same key — the right shape for the one row per unit every other
    caller builds. A bootstrap draw repeats units by construction, so
    `percentile_of_derived` needs this instead: each row keeps its *real*
    `unit` value (duplicated, as the draw duplicated it), and this bypasses
    `__init__` rather than re-keying to something synthetic and unique, which
    is what made every draw's units look distinct to a template that reads
    `unit` before this function existed.

    Public rather than private because `cli.py` needs it for the same reason:
    merging a unit's declared attributes into the table a template's `aggregate`
    reads is a row-level operation (`columns` then names them for free), and the
    table it has to merge into is sometimes one of these draws.
    """
    table = UnitTable.__new__(UnitTable)
    table._rows = rows
    return table

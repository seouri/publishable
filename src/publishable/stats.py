"""Statistics over the per-unit table.

Pure by design: a collapsed table in, values and intervals out. No filesystem,
no config parsing, no git — a statistical claim is the last thing that should be
entangled with I/O, and purity is what lets this be tested exhaustively.

See docs/reference.md § Statistical reporting.
"""

import copy
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
    """A percentile interval and the pool it was read from.

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


def _sample_variance(values: Sequence[float], mean: float) -> float:
    """The unbiased sample variance, Σ(v − v̄)² / (n − 1).

    Extracted for the reason `_t_critical` gives for itself: one expression rather
    than one per construction, because two copies is how two intervals over the
    same data come to disagree about what the dispersion *is*, and a drift there is
    invisible in every output that isn't compared against the other.
    `welch_t_over_units` puts this in an interval and `cohens_ds` pools two of them
    into a standardizer, and § Statistical reporting's *d*s-pools-where-Welch-doesn't
    asymmetry is only readable if both rest on the same quantity.

    Takes the mean rather than recomputing it: every caller already holds one, and
    a variance centred on a different mean than the point estimate is the failure
    `_weighted_mean` exists to prevent one level over.

    Undefined below two values — every caller floors above that first, which is
    where the "no dispersion to describe" refusal belongs. `weighted_t_over_units`
    deliberately does NOT call this: its denominator is `Σw − Σw²/Σw`, a different
    quantity. `cohens_dz` also does not call this — its own expression over the
    difference vector is the same shape, left unwired as a scope choice this
    extraction did not make.
    """
    return sum((v - mean) ** 2 for v in values) / (len(values) - 1)


def t_over_units(values: Sequence[float], confidence: float = 0.95) -> Interval | None:
    """Student's t on the per-unit values, df = completed units − 1.

    Returns None below two values: df would be zero and there is no dispersion
    to describe. Reporting a point with no interval is honest; inventing one is not.
    """
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    variance = _sample_variance(values, mean)
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


def _cr1_variance(
    values: Sequence[float], keys: Sequence[str], membership: Mapping[str, str]
) -> tuple[float, int] | None:
    """The CR1 sandwich variance of the mean, and the cluster count its df reads.

    Three callers: `t_over_units_clustered` puts it in a per-condition interval,
    `paired_t_over_units_clustered` reaches it through that one, and
    `welch_t_over_units_clustered` combines two of them. A second sandwich among
    those three is how a paired interval and a per-condition one come to disagree
    about what cluster-robust means, which is the argument
    `paired_t_over_units_clustered`'s docstring already makes for delegating
    rather than hand-rolling — and a Welch form cannot delegate to
    `t_over_units_clustered` itself, because it needs the variance and the count
    and that function returns an `Interval`.

    The model core fits is the mean, so the sandwich is the intercept-only case:
    with `X'X = n` and a cluster's score `S_g = Σ_{i∈g}(v_i − v̄)`, the variance of
    the mean is `Σ_g S_g² / n²` before scaling. **The finite-sample scaling is the
    `G/(G−1)` factor**, and dropping it is not a rounding difference — it is the CR0
    estimator wearing this one's name, biased downward by exactly the factor a small
    cluster count makes largest. The two literature conventions for CR1 coincide
    here, since `k` is 1 for a mean.

    `None` below two values or below two clusters: the df every caller derives from
    the count would be zero, and each caller's own floor is that same refusal
    reported in its own terms. Returning the count rather than only the variance is
    what lets a Welch caller give each side `G_s − 1` df without recounting.

    The membership mapping is `units.clusters_of`'s, passed whole rather than
    pre-resolved, and the count comes from `units.cluster_count_of` — the single
    counting expression, so no df here can disagree with the `n.clusters` printed
    beside it. Indexed rather than `.get`-ed: a key the roster doesn't hold is a
    core defect, and absorbing it into a cluster of its own would raise `G` and
    narrow the interval. `strict=True` on the zip, because a keys/values length
    mismatch is a misaligned cluster vector and would produce a plausible number
    rather than an error.
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
    return (groups / (groups - 1)) * meat / (n * n), groups


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

    Returns `None` below two clusters, and for the same reason `t_over_units`
    returns `None` below two values: df would be zero. That floor is on the
    CLUSTER count, so 300 cells from one animal get a point and no interval —
    which is the honest answer, one animal being one draw. Both floors, and the
    sandwich itself, live in `_cr1_variance`; this function has no guard of its
    own to duplicate them with.
    """
    got = _cr1_variance(values, keys, membership)
    if got is None:
        return None
    variance, groups = got
    mean = sum(values) / len(values)
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
    return Interval(low=mean - half, high=mean + half, method="weighted_t_over_units_clustered")


def welch_t_over_units(
    of: Sequence[float], against: Sequence[float], confidence: float = 0.95
) -> Interval | None:
    """Welch's *t* on two independent condition means, df from Welch-Satterthwaite.

    `reference.md` § Statistical reporting: "The unpaired counterpart of the first:
    unequal variances are assumed rather than pooled, because two arms need be
    neither the same size nor the same spread." The contrast's interval is its own
    construction over the two sides, never a difference of the two sides' own
    intervals — `paired_t_over_units`' argument, unchanged by the sides being
    disjoint.

    **There is no pooling anywhere in this construction**, and that is the whole
    content of the row. Pooling the two variances gives a plausible number that is
    wrong in a direction unequal spreads decide, and at equal per-side sizes the
    pooled and Welch standard errors are algebraically IDENTICAL — so a fixture
    with equal arms cannot tell the two apart, and no test of this function may use
    one.

    **The df is the construction, not a detail of it.** Welch-Satterthwaite over
    the two per-side variances-of-the-mean is what makes the interval honest about
    two spreads; `n_of + n_against − 2` is the pooled reading this row refuses, and
    `min(n) − 1` throws a side's information away. `cohens_ds` pools where this
    deliberately doesn't, and § Statistical reporting states that asymmetry is not
    an inconsistency: an interval is an inference and gets the assumption-light
    construction, while *d* is a descriptive standardization whose conventional
    denominator *is* the pooled one.

    Returns `None` below two values on either side, matching `t_over_units`' floor
    read across two samples: df would be zero on that side and there is no
    dispersion to describe. Reporting a point with no interval is honest; inventing
    one is not. Returns `None` where BOTH sides are constant, because the combined
    variance is then exactly zero and the df is 0/0 — one side constant is not
    refused, since the other still has dispersion and the difference of two means
    still has a sampling distribution.

    Takes two value vectors and nothing else, for the reason
    `paired_t_over_units_clustered` takes a label vector: `correction.Member` will
    carry them as `UnpairedEvidence` (task 11, not yet built), and both callers
    hold two per-side vectors with no roster between them.
    """
    n_of, n_against = len(of), len(against)
    if n_of < 2 or n_against < 2:
        return None
    mean_of = sum(of) / n_of
    mean_against = sum(against) / n_against
    # The variance OF THE MEAN on each side, s²/n — what Welch adds rather than
    # pools, and what Welch-Satterthwaite's df is a function of.
    var_of = _sample_variance(of, mean_of) / n_of
    var_against = _sample_variance(against, mean_against) / n_against
    total = var_of + var_against
    if total <= 0.0:
        return None
    df = (
        total * total / (var_of * var_of / (n_of - 1) + var_against * var_against / (n_against - 1))
    )
    delta = mean_of - mean_against
    half = _t_critical(df, confidence) * math.sqrt(total)
    return Interval(low=delta - half, high=delta + half, method="welch_t_over_units")


def welch_t_over_units_clustered(
    of: Sequence[float],
    of_labels: Sequence[str],
    against: Sequence[float],
    against_labels: Sequence[str],
    confidence: float = 0.95,
) -> Interval | None:
    """Cluster-robust (CR1) Welch *t* on two independent condition means.

    `reference.md` § Statistical reporting's suffix rule: under a declared
    `cluster_by` each unweighted contrast construction "takes a `_clustered` suffix
    and reads the cluster as the draw", the *t* forms being cluster-robust (CR1)
    "over the differenced values when paired and over the arm-level ones when not"
    — this is the "when not" half. The design it is load-bearing for is
    § Clustered units' matched case-control: "The contrast stays unpaired, since no
    unit appears in both arms, but its interval is cluster-robust on the matched
    set — so the effective `n` is the number of sets rather than the number of
    subjects, which is the accounting a matched design needs."

    **The df is Welch-Satterthwaite over the two cluster-robust per-side variances,
    each side contributing `G_s` − 1**, which § Statistical reporting states since
    H4c and which code could not emit before it did. The substitution the suffix
    rule describes happens inside each side's own variance and its own df, and
    combining them is what the unclustered Welch form already does. Two readings
    are rejected rather than merely unused: `min(G_of, G_against) − 1` discards a
    side's information and contradicts "df = clusters − 1" on the side it discards,
    and `G_total − 2` is the **pooled** reading `welch_t_over_units` refuses by
    construction.

    **A cluster-robust interval that is merely wider is not evidence the cluster
    count reached the critical value.** Over positively correlated data it comes out
    wider whatever df it uses — `t_over_units_clustered` says so — so only the
    number is evidence, and a fixture whose two sides carry the same cluster count
    cannot see a construction reading one side's.

    `of_labels`/`against_labels` are one cluster label per value, in the same order,
    per side, rather than the `keys` + `membership` pairs the per-condition form
    takes: both callers hold two per-side vectors and nothing else, and
    `correction.UnpairedEvidence` will carry exactly that pair (task 11, not yet
    built). The positional keys synthesized below are a **bijection**, not a
    proxy — `_cr1_variance` uses a key only to look its label up and to count
    distinct labels — and the two sides get disjoint synthetic key spaces so
    neither side's count can read the other's.

    `None` below two values or below two clusters on **either** side, both inherited
    from `_cr1_variance`: that side's df would be zero. `None` also where both
    variances are zero, for the reason `welch_t_over_units` gives — the df is then
    0/0 — which a fixture with values constant within cluster but varying across
    clusters cannot reach.
    """
    of_keys = [f"of{i}" for i in range(len(of))]
    against_keys = [f"ag{i}" for i in range(len(against))]
    got_of = _cr1_variance(of, of_keys, dict(zip(of_keys, of_labels, strict=True)))
    got_against = _cr1_variance(
        against, against_keys, dict(zip(against_keys, against_labels, strict=True))
    )
    if got_of is None or got_against is None:
        return None
    var_of, groups_of = got_of
    var_against, groups_against = got_against
    total = var_of + var_against
    if total <= 0.0:
        return None
    # Welch-Satterthwaite with each side's df taken from its OWN cluster count —
    # the substitution the suffix rule makes, applied inside each side's variance
    # and its df rather than to the combination.
    df = (
        total
        * total
        / (var_of * var_of / (groups_of - 1) + var_against * var_against / (groups_against - 1))
    )
    delta = sum(of) / len(of) - sum(against) / len(against)
    half = _t_critical(df, confidence) * math.sqrt(total)
    return Interval(low=delta - half, high=delta + half, method="welch_t_over_units_clustered")


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


def weighted_paired_t_over_units(
    diffs: Sequence[float], weights: Sequence[Any], confidence: float = 0.95
) -> Interval | None:
    """Student's *t* on the *weighted* per-unit differences, df = Kish's effective n − 1.

    The contrast's interval is its own construction over the paired intersection,
    never a difference of the two sides' intervals — `paired_t_over_units`'
    argument, unchanged by the weighting.

    Delegates to `weighted_t_over_units` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units`. That is not tidiness: it is
    what makes the `Σw − Σw²/Σw` variance denominator, the Kish df, the exact
    reduction to the unweighted form at equal weights, and the invariance to
    rescaling the weights properties of ONE construction rather than of two that
    can drift apart. A hand-rolled variance here is how a paired interval and a
    per-condition one come to disagree about what a weighted interval is.

    `None` below two differences and `None` when Kish's effective size falls below
    two, both inherited: the record then carries `ci95: null` beside a present
    `weighted_by` and an `n_paired_effective` below 2 — the weighting happened, and
    there was no df to describe it with.
    """
    plain = weighted_t_over_units(diffs, weights, confidence)
    if plain is None:
        return None
    return Interval(low=plain.low, high=plain.high, method="weighted_paired_t_over_units")


def paired_t_over_units_clustered(
    diffs: Sequence[float], labels: Sequence[str], confidence: float = 0.95
) -> Interval | None:
    """Cluster-robust (CR1) *t* on the per-unit differences, df = clusters − 1.

    `reference.md` § Statistical reporting: under a declared `cluster_by` each
    unweighted contrast construction "takes a `_clustered` suffix and reads the
    cluster as the draw", the *t* forms being "cluster-robust (CR1) with df =
    clusters − 1, over the differenced values when paired". This is that form, and
    the contrast's interval stays its own construction over the paired
    intersection rather than a difference of the two sides' intervals —
    `paired_t_over_units`' argument, unchanged by the clustering.

    **The df is the construction**, not a detail of it: a cluster-robust interval
    over positively correlated differences comes out wider than
    `paired_t_over_units` whatever df it uses, so widening is not evidence the
    cluster count reached the critical value. Only the number is.

    Delegates to `t_over_units_clustered` and rewrites the `method`, exactly as
    `paired_t_over_units` delegates to `t_over_units` and
    `weighted_paired_t_over_units` to `weighted_t_over_units`. That is not
    tidiness: it is what makes the `G/(G−1)` scaling, the df, the two floors and
    the relabelling invariance properties of ONE construction rather than of two
    that can drift apart. A hand-rolled sandwich here is how a paired interval and
    a per-condition one come to disagree about what cluster-robust means.

    **`labels` is one cluster label per difference, in the same order**, rather
    than the `keys` + `membership` pair the per-condition form takes. Both callers
    hold a per-difference vector and nothing else: `correction.Member` carries
    `clusters` as a modifier on `diffs` for the same reason it carries `weights`
    that way, and a mapping plus a key list would be two fields on a frozen
    dataclass for one fact. The positional keys synthesized below are a
    **bijection**, not a proxy for the real unit keys: `t_over_units_clustered`
    uses a key for exactly one thing — looking its label up, and counting the
    distinct labels through `units.cluster_count_of` — so distinct synthetic keys
    carrying these labels are the same input to it, digit for digit. The real unit
    keys are unrecoverable here and are also unused.

    `strict=True` on the zip, for the reason `_weighted_mean` uses it: a
    diffs/labels length mismatch is a misaligned cluster vector, and it would
    produce a plausible number rather than an error.

    Floors are inherited whole: `None` below two differences, and `None` below two
    clusters, where df would be zero.
    """
    keys = [str(i) for i in range(len(diffs))]
    plain = t_over_units_clustered(diffs, keys, dict(zip(keys, labels, strict=True)), confidence)
    if plain is None:
        return None
    return Interval(low=plain.low, high=plain.high, method="paired_t_over_units_clustered")


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


def weighted_cohens_dz(diffs: Sequence[float], weights: Sequence[Any]) -> float | None:
    """The weighted mean of the per-unit differences over their weighted standard
    deviation.

    `reference.md` § Statistical reporting: "A weighted condition standardizes by
    the weighted standard deviation, on the same weights the mean used." So the
    same weights the delta was computed with, and no others — a *d* standardized by
    an unweighted dispersion is a ratio of two different samples' summaries.

    **The variance denominator is `Σw − Σw²/Σw`, not `Σw`**, the same choice
    `weighted_t_over_units` argues at length: at w ≡ 1 it is n − 1, so equal
    weights reproduce `cohens_dz` digit for digit and this is a generalization
    rather than a second statistic wearing the same name. `Σw` would shrink the
    denominator and inflate every *d*.

    Invariant to rescaling the weights, as every weighted construction here is:
    both the mean and the variance divide the scale out.

    `None` below two differences and `None` at zero dispersion, the two refusals
    `cohens_dz` carries, kept so the pair refuses the same inputs. `None` also
    for a non-positive denominator — reachable not by concentrating all the
    weight on one unit (`checked_weights` admits that; `Σw − Σw²/Σw` is still
    strictly positive for two or more strictly positive weights, algebraically)
    but by a **weight ratio wide enough that `Σw²/Σw` rounds to `Σw` in floating
    point** — `weighted_cohens_dz([1.0, 2.0], [1e17, 1.0])`'s `Σw² / Σw` computes
    to exactly `1e17`, indistinguishable from `Σw` at that magnitude, so the
    subtraction is exactly `0.0` rather than merely small. Reporting no *d* for
    an under-determined variance is the same honesty `t_over_units` already
    practises below two values; inventing one from a denominator that has
    rounded away is not.

    `weights` is annotated `Any` for the reason `weighted_t_over_units`' is: a
    weight is a unit attribute, `units._from_table` builds those from
    `csv.DictReader`, and `units.usable_weight` — reached through
    `checked_weights` — is the single gate `validate` approved the config against.
    """
    if len(diffs) < 2:
        return None
    w = checked_weights(weights)
    total = sum(w)
    denominator = total - sum(x * x for x in w) / total
    if denominator <= 0:
        return None
    mean = _weighted_mean(w, diffs)
    variance = sum(a * (d - mean) ** 2 for a, d in zip(w, diffs, strict=True)) / denominator
    sd = math.sqrt(variance)
    return mean / sd if sd > 0 else None


def cohens_ds(of: Sequence[float], against: Sequence[float]) -> float | None:
    """The difference of two condition means over the pooled within-condition sd.

    `reference.md` § Statistical reporting: "paired contrasts report *d*z … and
    unpaired ones report *d*s, over the pooled within-condition standard
    deviation. They are different quantities from the same data and the one that
    applies follows from `paired`, which is derived rather than declared."

    **The denominator pools where `welch_t_over_units`' deliberately does not**, and
    § Statistical reporting says in terms that this is not an inconsistency: an
    interval is an inference and gets the assumption-light construction, while *d*
    is a descriptive standardization whose conventional denominator *is* the pooled
    one, and a *d* against a Welch-style denominator is a number no reader could
    compare to another paper's. So this function does not read the interval beside
    it, and must not be tidied into doing so.

    Reported only for a per-unit mean, exactly as `cohens_dz` is: a derived metric
    has no per-unit value to difference, which is why the worked example carries
    `cohens_d: null` for `r`.

    `None` below two values on either side and `None` at zero dispersion, the two
    refusals `cohens_dz` carries, kept so the family refuses the same inputs.
    """
    if len(of) < 2 or len(against) < 2:
        return None
    mean_of = sum(of) / len(of)
    mean_against = sum(against) / len(against)
    pooled = (
        (len(of) - 1) * _sample_variance(of, mean_of)
        + (len(against) - 1) * _sample_variance(against, mean_against)
    ) / (len(of) + len(against) - 2)
    sd = math.sqrt(pooled)
    return (mean_of - mean_against) / sd if sd > 0 else None


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

    **`pool` must already be sorted ascending.** This function reads fixed
    ranks off it and does not sort — `correction.Member`'s own docstring states
    the precondition, and every construction in this module that returns a
    pool sorts it before returning. An unsorted pool would still return two
    values that look exactly like an interval, silently.
    """
    assert list(pool) == sorted(pool), (
        "interval_at reads fixed ranks off a sorted pool and does not sort; an "
        "unsorted pool gives two arbitrary positions"
    )
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


NULL_TEST_METHODS = ("permutation",)


def min_honest_permutations(level: float = 0.05) -> int:
    """The fewest relabellings a permutation p-value may be read off.

    A DIFFERENT quantity from `min_honest_draws`, and inheriting that one
    unexamined is the available shortcut and the wrong one: that floor is about a
    percentile interval's two ranks being interior, while a permutation p-value's
    resolution is `1/(n + 1)` — the smallest value it can take. The floor is the
    smallest `n` at which the p-value can fall STRICTLY below the level being
    tested: `1/(n + 1) < level` gives `n > 1/level − 1`, so `n >= floor(1/level)`
    — 20 at 95 % confidence, where `min_honest_draws` is 80.

    Derived from `level` rather than written as a literal, the way
    `min_honest_draws` is derived from `confidence`, so a family tested at a
    corrected level moves the floor with it.

    `floor` rather than a search over `n`: at `level = 0.05/7` the two disagree,
    a scan answering 139 because `1/140` and `0.05/7` differ by one ulp, where
    exact arithmetic answers 140. The non-strict reading `1/(n + 1) <= level`
    would be `ceil(1/level) - 1` and gives 19 at 95 %; `reference.md`
    § Statistical reporting states the strict inequality and the integer
    together so the two cannot drift.
    """
    return math.floor(1.0 / level)


def _label_delta(values: Sequence[float], labels: Sequence[str], of_level: str) -> float | None:
    """The statistic a permutation null is built for: the mean over the units
    labelled `of_level` minus the mean over the rest.

    One expression, called for the observed labelling and for every draw, so the
    `>=` comparison cannot be against a differently computed number. `reference.md`
    § What isn't a repeat requires the comparison be "against the value the actual
    run produced" — recomputed here rather than read off a record, so a delta that
    was rounded, weighted or narrowed elsewhere cannot silently shift the count by
    one at the identity draw.

    `None` for an empty arm, which is not a delta of zero: `reference.md`
    § Contrasts refuses that reading one construction over.

    `None` too when the delta itself is `nan` — `docs/superpowers/spec-defects.md`'s
    "a column resample is only ever defined given finite inputs" filing, claimed
    for this construction rather than re-declined a fourth time: an unguarded
    `nan` observed statistic makes every `>=` comparison `False`, which
    `permutation_over_units` would report as a small, real-looking p-value —
    `1/(n + 1)` — from a table nobody could compute a mean of, which is worse
    than the honest absence an empty arm already gets. Checked here rather
    than at each caller, since both the observed statistic and every draw's
    recomputation pass through this one function.
    """
    of = [v for v, label in zip(values, labels, strict=True) if label == of_level]
    against = [v for v, label in zip(values, labels, strict=True) if label != of_level]
    if not of or not against:
        return None
    delta = sum(of) / len(of) - sum(against) / len(against)
    return None if math.isnan(delta) else delta


def permutation_over_units(
    values: Sequence[float],
    labels: Sequence[str],
    of_level: str,
    seed: int,
    n: int = 5000,
    strata: Sequence[str] | None = None,
) -> float | None:
    """The permutation p-value for a label's effect, over rows.

    `reference.md` § What isn't a repeat: a `null_test` "relabels units and
    recomputes the metric", and "the permutation test compares the null it builds
    against the value the actual run produced". So each draw is one relabelling of
    `labels` — the multiset of labels is held fixed, which is what makes the arm
    sizes constant across draws and the null a null about the LABEL rather than
    about the design — and the statistic is recomputed from it.

    **The estimator is `(1 + #{T >= T_obs}) / (n + 1)`, and the +1 is not a
    rounding choice.** The observed labelling is itself one of the relabellings,
    so it is counted; `b/n` can return exactly `0.0`, and a permutation test can
    never legitimately report a probability of zero — it has only ever examined
    `n` of them. The `>=` is deliberate too: a draw that ties the observed
    statistic is evidence against the observed being extreme, so counting only
    strict exceedances would report a smaller p than the evidence supports.

    `None`, never a number, in three states, and each is an honest absence rather
    than a failure: an arm the observed labelling left empty (no statistic to
    test), fewer than two values (nothing to relabel), and a null whose every draw
    reproduces the observed statistic. The last is decision 8 and it follows
    `percentile_over_units_clustered`'s shipped rule that "the degenerate case is
    content, not count" — a p-value of 1.0 from a distribution that could not have
    been anything else is a number with no construction behind it. The record says
    so by carrying the resolved `null_test` echo beside the `null`, exactly as
    `ci95: null` beside a `resample` echo does.

    One seeded `random.Random`, drawn in call order, for the reason every draw in
    this module is: two identical runs must agree, and a generator taken from the
    global state would make the p-value depend on what ran before it.

    **With `strata`, the permutation is confined to each stratum's own
    positions.** `reference.md` § What isn't a repeat requires it for a
    group-axis contrast — "permuted within cells of every *other* group axis,
    so a cross isn't destroyed" — and it is the same shape
    `percentile_over_units` gives its own `strata`: what one draw may touch,
    not what the statistic is. With no `strata` the whole vector is one
    group covering every position, structurally the same domain the
    unstratified draw always had.

    **That structural sameness is not an RNG-identical one, unlike
    `_draw_pools`' own refactor.** Each draw now shuffles a fresh per-group
    copy and writes it back into `pool`, rather than shuffling `pool` in
    place — a valid uniform permutation either way, but a DIFFERENT sequence
    of `random.Random` calls: measured directly, fixture C at `seed=7, n=5000`
    gives `p = 0.48050` before this refactor and `p = 0.47351` after (also at
    seeds 2 and 3). Nothing user-visible moved, because `null_test` is
    unwired and every assertion this shape touches is range-based rather than
    a seed-pinned literal — but a future refactor of this walk is invisible
    to the suite for the identical reason, which is worth stating rather than
    leaving for the next reader to discover by the same review that found it
    here.
    """
    if len(values) < 2:
        return None
    observed = _label_delta(values, labels, of_level)
    if observed is None:
        return None
    rng = random.Random(seed)
    pool = list(labels)
    groups: list[list[int]] = []
    if strata is None:
        groups = [list(range(len(values)))]
    else:
        by_stratum: dict[str, list[int]] = {}
        for index, stratum in enumerate(strata):
            by_stratum.setdefault(stratum, []).append(index)
        groups = list(by_stratum.values())
    reached = 0
    varied = False
    for _ in range(n):
        for indices in groups:
            within = [labels[i] for i in indices]
            rng.shuffle(within)
            for index, label in zip(indices, within, strict=True):
                pool[index] = label
        drawn = _label_delta(values, pool, of_level)
        if drawn is None:
            continue
        if drawn != observed:
            varied = True
        if drawn >= observed:
            reached += 1
    if not varied:
        return None
    return (1 + reached) / (n + 1)


def permutation_over_units_clustered(
    values: Sequence[float],
    labels: Sequence[str],
    clusters: Sequence[str],
    of_level: str,
    seed: int,
    n: int = 5000,
    level: str = "within_cluster",
) -> float | None:
    """A permutation p-value that respects the clustering, at the level the
    roster implies.

    `reference.md` § Clustered units gives both rules and neither is a choice
    made here: "if `shuffle` names an attribute that varies *within* clusters,
    labels are permuted within each cluster independently — for matched
    case-control that's a case/control swap inside each matched set, which is
    the conditional test that design calls for. If the attribute is constant
    within a cluster, whole clusters are relabelled, which is the null for a
    cluster-randomized trial. Shuffling rows freely would destroy the structure
    the null is supposed to hold fixed, and the two designs need opposite
    treatments, so guessing is not an option."

    **`level` arrives as a parameter rather than being derived here**, because
    the derivation reads the roster and this module imports nothing:
    `units.null_test_level` is the single expression, and `validate` refuses
    the ambiguous roster before any caller reaches this. A caller passing a
    level it did not derive is passing a guess, which is what that refusal
    exists to prevent.

    **Within-cluster: each cluster's own label multiset is permuted inside
    it**, so every cluster keeps its arm counts and the null holds the
    matching fixed. **Whole-cluster: the clusters' labels are permuted among
    the clusters**, so a cluster's units move together and the arm sizes vary
    from draw to draw with the cluster sizes — which is the construction, not
    a defect of it. A whole-cluster draw that empties an arm has no statistic,
    and `_label_delta` reports that as `None`; where EVERY draw empties one,
    the p-value is `None` for decision 8's reason.

    The estimator, the `>=`, the +1 and the invariance rule are
    `permutation_over_units`' and are not restated in a second expression here
    — the two differ in what one draw is, which is exactly what `reference.md`
    says the cluster declaration changes.
    """
    if len(values) < 2:
        return None
    observed = _label_delta(values, labels, of_level)
    if observed is None:
        return None
    rng = random.Random(seed)
    positions: dict[str, list[int]] = {}
    for index, cluster in enumerate(clusters):
        positions.setdefault(cluster, []).append(index)
    drawn_labels = list(labels)
    # The cluster's own label, for the whole-cluster draw: constant within the
    # cluster by `units.null_test_level`'s own answer, so the first position's
    # label IS the cluster's. Read once rather than per draw, so a draw cannot
    # read a label a previous draw wrote.
    cluster_order = list(positions)
    cluster_labels = [labels[positions[c][0]] for c in cluster_order]
    reached = 0
    varied = False
    for _ in range(n):
        if level == "whole_cluster":
            rng.shuffle(cluster_labels)
            for cluster, label in zip(cluster_order, cluster_labels, strict=True):
                for index in positions[cluster]:
                    drawn_labels[index] = label
        else:
            for cluster in cluster_order:
                indices = positions[cluster]
                within = [labels[i] for i in indices]
                rng.shuffle(within)
                for index, label in zip(indices, within, strict=True):
                    drawn_labels[index] = label
        drawn = _label_delta(values, drawn_labels, of_level)
        if drawn is None:
            continue
        if drawn != observed:
            varied = True
        if drawn >= observed:
            reached += 1
    if not varied:
        return None
    return (1 + reached) / (n + 1)


def permutation_over_contrast(
    of: Sequence[float],
    against: Sequence[float],
    seed: int,
    n: int = 5000,
    of_clusters: Sequence[str] | None = None,
    against_clusters: Sequence[str] | None = None,
    level: str = "rows",
) -> float | None:
    """The permutation p-value for a cross-arm contrast.

    `reference.md` § What isn't a repeat: a `shuffle` naming a `groups` axis builds
    the null of "that axis's contrast, against a world where its membership carries
    no information — permuted within cells of every *other* group axis, so a cross
    isn't destroyed."

    **The arm label IS the side**, so this is not a second construction: the two
    per-side vectors are concatenated, the side membership becomes the label
    vector, and the draw is `permutation_over_units` — stratified by the other
    group axes' cells — or its clustered sibling wherever `data.units.cluster_by`
    is declared. Delegating rather than reimplementing is the rule
    `corrected_for`'s own docstring states for itself: two spellings of one
    construction drifting apart is a defect this codebase has already shipped.

    Takes two per-side value vectors rather than a difference vector, which is the
    evidence shape an unpaired comparison has — `correction.UnpairedEvidence` makes
    the same argument one module over: an unpaired contrast has no per-unit
    differences to store, because the two sides are disjoint sets of units.

    `level` is `units.null_test_level`'s answer, derived by the caller from the
    roster for the reason the clustered draw states.

    **No `strata` parameter, on purpose — whole-branch review Minor 4.** A prior
    version took `of_strata`/`against_strata` and stratified the unclustered
    branch by them, on the ground that `reference.md` requires a group-axis
    null to be "permuted within cells of every other group axis." No caller,
    production or test, ever supplied either: a declared contrast names its
    two conditions by label, and a condition is one cell of the full group
    cross, so every OTHER group axis is already constant on both sides of any
    comparison — the rule is satisfied structurally by which two conditions a
    contrast can even name, not by a stratified draw. Removed rather than left
    as dead surface a docstring implied delivered something it was never
    reachable to deliver.
    """
    values = list(of) + list(against)
    labels = ["of"] * len(of) + ["against"] * len(against)
    # A design declaring both a `cluster_by` and a second group axis takes the
    # clustered branch below and the strata are not composed with it: that
    # composition is a construction nothing in the four documents specifies,
    # no config in the feasibility analysis declares two group axes, and
    # inventing one would be a rule with no authority behind it.
    if of_clusters is not None and against_clusters is not None:
        return permutation_over_units_clustered(
            values,
            labels,
            list(of_clusters) + list(against_clusters),
            "of",
            seed,
            n=n,
            level=level,
        )
    return permutation_over_units(values, labels, "of", seed, n=n)


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
    reproduce the unstratified path digit for digit **when neither path is
    itself refused**. A one-stratum roster whose values are all identical is
    refused (`None`) by the constant-pair check below, while the unstratified
    path over that same roster returns a zero-width `Interval` rather than
    `None` — the two paths apply different refusal criteria to the identical
    degenerate input, so they diverge there rather than reproducing each other;
    that is not a contradiction of this paragraph, but it is a real exception to
    it and is pinned as such by
    `test_a_column_resample_refuses_the_constant_one_stratum_case_the_unstratified_path_does_not`.
    Sorting values and stratum labels as separate sequences would preserve every
    invariance and silently re-pair them — the mistake equal-sized strata cannot
    see.

    Returns `None` rather than a zero-width interval when every stratum's own
    (value, weight) pairs are all identical — a singleton stratum is the
    special case of this, but a larger stratum whose rows all carry one
    repeated pair guarantees the same zero freedom. That is a structural
    guarantee, true whatever the repeated pair's value is, unlike a single
    constant stratum among others that still vary — which keeps its interval,
    the same way `percentile_over_units_clustered` reports a point rather than
    a zero-width interval at `G < 2`.

    **This returns a bare `Interval`, with no survivor count, and that is a
    decision rather than an omission — conditional on finite inputs.**
    `percentile_of_derived` returns `(Interval, int)` because a derived metric's
    `compute` can fail on a degenerate draw — `nan`, `None`, or a raise — so how
    many draws survived is a real fact about the interval. A column metric's
    draw statistic is a mean over a non-empty sample of FINITE values with
    FINITE weights, which is always defined: the unweighted branch divides by
    `n >= 2`, the weighted branch's Σw is strictly positive because
    `checked_weights` refuses a zero, negative, non-finite or non-numeric weight
    before any draw is taken, and the stratified branch draws `len(pool) >= 1`
    rows from each non-empty pool. **The condition is load-bearing and does not
    hold unconditionally**: neither `values` nor a weight vector is checked for
    finiteness anywhere on this path — a `nan` or `inf` among `values`, or a
    weight vector whose checked-finite entries sum past `float`'s range (e.g.
    `[1e308] * 4`), each produce `Interval(nan, nan)` today, reachable by calling
    this function directly. That gap is real, pre-existing, and out of scope
    for this decision — recorded on its own in `docs/superpowers/spec-defects.md`
    rather than fixed here. Under the finiteness condition, though, a column's
    `resample_draws` — once a later slice wires `statistics.resample` for
    recorded columns into `summarize_step` (the wholesale refusal retired with
    H4a task 12, commit `2fdc957`; as of that commit `cli.command_run` did
    not yet resolve the block into a call here, so the recorded-column branch
    there still carried no `resample_draws` key at all — check
    `cli.command_run` directly for whether that has since changed) — can
    safely be the REQUESTED `n` rather than a survivor count, and
    `percentile_over_units`'s return type need not change to carry one: a
    non-finite draw statistic would not be caught by a survivor filter either,
    since nothing here treats `nan`/`inf` as a failed draw to exclude, so
    `(Interval, int)` would report `(Interval(nan, nan), n)` — the identical
    false claim with an extra field. The invariant is pinned, under that
    condition, by
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
                group[rng.randrange(len(group))] for group in ordered for _ in range(len(group))
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
    the other — **provided both are handed the same raw per-unit value**, which
    is the case this equality was built for: a single undeclared-composition
    `stratify_by` name, read straight off the roster. `cli.py`'s
    `resample_strata` (H4a task 15) hands this function something already
    transformed instead — a cross of every declared name joined by `|`, with a
    missing name rendered `<absent>` rather than passed through as `None` — so
    in production this function's own `stratum is None` branch is rarely if
    ever what actually distinguishes an absent unit; `cli.py`'s sentinel
    already has. The two normalizations no longer operate on one shared input,
    and neither is checked against a real attribute value that happens to
    collide with either sentinel string, or against two different attribute
    combinations that happen to join into the identical `|`-separated label —
    both are unaddressed here, and are gaps to record, not guarantees this
    docstring is making. Each stratum then draws exactly as many clusters, with
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
    # violation — provided both see the same raw value. `cli.py`'s
    # `resample_strata` (H4a task 15) pre-transforms what this function
    # actually receives (a `|`-joined cross, `<absent>` for a missing name),
    # so that provision no longer holds unconditionally in production; see the
    # docstring above for what is and is not covered.
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
    return Interval(low=means[lo], high=means[hi], method="percentile_over_units_clustered")


def percentile_of_derived(
    collapsed: dict[str, dict[str, Any]],
    compute: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
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

    **With `strata`, each draw preserves each stratum's own key count and draws
    keys with replacement within it** — the same discipline
    `percentile_over_units`'s stratified branch applies to *values*, applied
    here to *key* selection instead: a derived metric has no per-unit value of
    its own to stratify, so what stratifies is which units end up in the
    resampled table `compute` is handed. Pools are built by walking the
    already-sorted `keys`, so each pool's own contents come out sorted, and the
    pools are then ordered by their own sorted contents rather than by label —
    the same invariance `percentile_over_units` keeps for exactly the same
    reason: a relabelled stratum must draw the identical sequence of tables.
    `strata` is indexed by key, not `.get`-ed, the same discipline `weights`
    and `clusters` follow elsewhere in this module: `strata` must be total
    over `collapsed`'s keys, or the missing lookup raises `KeyError` rather
    than quietly defaulting the unit into some invented stratum — a caller
    whose roster and `strata` mapping have come to disagree about which units
    exist is a core defect, not a silent extra stratum. It need not be
    exactly `collapsed`'s key set — a caller resampling a subset of a larger
    roster (a `report_by` level, say) can pass the roster-wide mapping
    unfiltered, and any extra entry it carries is simply never looked up.

    **The degenerate case is refused here too, content-based, the same check
    `percentile_over_units`'s own strata branch and
    `percentile_over_units_clustered`'s cluster-content branch both carry, one
    level down over ROWS rather than over values or clusters.** If every key in
    a stratum carries the identical recorded row (a singleton stratum — "any
    near-unique attribute" — is the trivial case of this, and is exactly what
    a near-unique `stratify_by` produces), every draw of that stratum picks
    from an identical multiset of rows: the same units drawn every time, in
    whatever order, so `compute` — assuming it is itself deterministic, which
    every `aggregate` this module is handed is — returns the identical value on
    every draw. If this holds for every stratum, the interval has zero width,
    which § Statistical reporting refuses in those terms: "a zero-width 95 %
    interval is not [honest]; reporting a point with no interval is honest."
    Without this, a near-unique `stratify_by` would validate clean and publish
    `ci95: [x, x]` — indistinguishable from a genuine 2000-draw interval — right
    beside a recorded column's `ci95: null` for the identical degenerate
    design, the exact disagreement `percentile_over_units`'s own strata branch
    and `percentile_over_units_clustered`'s `G < 2` floor already refuse to
    let happen for their own constructions. Checked whether or not the
    resulting `compute` calls would agree in practice — this refuses on the
    STRUCTURE of the draw, not on running it and comparing outputs, since
    running it first would cost `draws` calls to `compute` for a refusal that
    is knowable from `collapsed` and `strata` alone.
    """
    keys = sorted(collapsed)
    if len(keys) < 2:
        return None, 0
    rng = random.Random(seed)
    n = len(keys)
    pools: dict[str, list[str]] | None = None
    if strata is not None:
        pools = {}
        for key in keys:
            pools.setdefault(strata[key], []).append(key)
    ordered_pools = None if pools is None else sorted(pools.values())
    if ordered_pools is not None and all(
        len({tuple(sorted(collapsed[key].items())) for key in group}) <= 1
        for group in ordered_pools
    ):
        # Content-based, over each stratum's own recorded ROW rather than a
        # count: a singleton stratum is the trivial case (one key, so one
        # possible row every draw), but a larger stratum whose members all
        # carry the identical recorded row is the same zero-freedom fact,
        # whatever its size. Refused before a single draw is taken, the same
        # way the two sibling constructions refuse their own degenerate case
        # — see the docstring's own paragraph for why this is checked on the
        # DRAW's structure and not by running `compute` and comparing outputs.
        return None, 0
    values: list[float] = []
    for _ in range(draws):
        if ordered_pools is not None:
            drawn = [
                group[rng.randrange(len(group))]
                for group in ordered_pools
                for _ in range(len(group))
            ]
        else:
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


def percentile_of_derived_clustered(
    collapsed: dict[str, dict[str, Any]],
    clusters: dict[str, str],
    compute: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
) -> tuple[Interval | None, int]:
    """A percentile interval for a derived metric, resampling whole clusters, and
    the number of draws it actually rests on.

    `reference.md` states the construction twice, and this docstring does not
    add a third wording: each replicate draws `G` clusters with replacement and
    rebuilds a unit table from their pooled units, so its row count varies per
    draw — `G` being `units.cluster_count_of`'s answer, so this cannot disagree
    with the `n.clusters` a caller prints beside the interval. `compute` is run
    on the pooled table exactly as `percentile_of_derived` runs it on its own
    resampled table; every other rule this function follows — the survivor
    discipline, the real-keys row-list construction, the uncontained unpermuted
    call — is `percentile_of_derived`'s, cited rather than restated.

    Built through `_draw_pools`, the one draw shape a percentile construction's
    other two callers already share, rather than a second notion of what a
    cluster draw is: with no `strata` this is one group holding every cluster
    (`G` clusters, drawn `G` times with replacement, pooling their units); with
    `strata` each stratum draws exactly as many clusters as it holds, the
    composition `_draw_pools` already enforces for its other two callers.

    The two ways to get this wrong both produce a plausible number: drawing `G`
    *units* and repairing the groups afterwards would be a resample whose
    independent draw count is really the row count, not the cluster count — a
    "too narrow" interval in exactly the sense `reference.md` § Clustered units
    names; averaging the drawn clusters' own means, rather than pooling their
    units, would give every cluster equal say regardless of size, where "pools
    their units" and the row count that varies with it says a large cluster
    contributes more rows than a small one.
    """
    keys = sorted(collapsed)
    if len(keys) < 2:
        return None, 0
    pools = _draw_pools(keys, strata, clusters)
    # The content-based refusal `percentile_over_units_clustered` makes
    # "whether or not `strata` is declared" (`reference.md` § Statistical
    # reporting), taken again here rather than left as a second undocumented
    # gap beside `percentile_of_derived`'s own unstratified one: if every
    # cluster within a stratum group carries the identical multiset of rows
    # (a stratum holding a single cluster is trivially so), drawing any of
    # them with replacement reproduces the same pooled table every time, so no
    # replicate can differ from any other and the interval would be `[x, x]`
    # — a zero-width 95 % interval `reference.md` refuses in those terms.
    # Content, not count: two identical-content clusters clear any count floor
    # and are still degenerate.
    if all(
        len(
            {tuple(sorted(tuple(sorted(collapsed[key].items())) for key in item)) for item in group}
        )
        <= 1
        for group in pools
    ):
        return None, 0
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(draws):
        drawn: list[str] = []
        for group in pools:
            for _ in range(len(group)):
                drawn.extend(group[rng.randrange(len(group))])
        table = unit_table_from_rows([{"unit": key, **collapsed[key]} for key in drawn])
        try:
            value = compute(table)
        # Degenerate, not caught for the real call; see `percentile_of_derived`.
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
        Interval(low=values[lo], high=values[hi], method="percentile_of_derived_clustered"),
        len(values),
    )


def permutation_of_derived(
    collapsed: dict[str, dict[str, Any]],
    labels: dict[str, str],
    compute: "Callable[[UnitTable, dict[str, str]], float | None]",
    seed: int,
    n: int = 5000,
) -> tuple[float | None, int]:
    """A permutation p-value for a metric a template derived, and the number of
    draws it rests on.

    A derived metric has no per-unit value to relabel directly — `aggregate`
    returned one number for the whole table — so this is `percentile_of_derived`'s
    situation one construction over: recompute the metric under each relabelling
    and count how many recomputations reach the observed value.

    **`compute` takes the table AND the relabelled label mapping, and that second
    argument is the whole difference from `percentile_of_derived`.** A one-argument
    closure of that function's shape cannot express a permutation here: `cli`
    re-applies each unit's declared attributes from the roster on every call
    (`_attributed`, which merges the roster's values OVER the row), so a
    relabelling written into the table's rows is erased before `aggregate` sees it
    and every draw reproduces the observed statistic. That is not a hypothetical —
    it is the shape the existing resample closure has, and it would report
    `p_value: 1.0` for every derived metric in every run. Handing the labels
    through instead makes the relabelling the closure's own input, which is the
    only place it cannot be overwritten.

    The table is rebuilt from a row list carrying the REAL unit keys, exactly as
    `percentile_of_derived` does and for its reason: a template that legitimately
    reads `unit` must see the roster it was drawn from. Unlike a bootstrap this
    draw repeats no unit, so the keys are unique — the row-list construction is
    kept anyway so the two functions hand `compute` the same shape of table.

    Units are sorted by key before the labels are permuted, for the row-order
    invariance `percentile_over_units` explains: a fixed seed permutes a fixed
    sequence of positions, so an unsorted roster would make the p-value depend on
    iteration order rather than on the multiset of units.

    A draw on which `compute` returns `None`, returns `nan`, or *raises* is dropped
    rather than counted — the three are the same situation from three different
    libraries, and which one `aggregate` happens to call is not a fact about
    whether the draw was degenerate. **The single unpermuted call that produces the
    observed statistic is not made robust that way**: it is the metric's real
    definition for this table, so a failure there is a fault to surface rather than
    a degenerate draw to skip, and `cli.py` contains it exactly as it contains the
    unresampled `aggregate` call — which is `percentile_of_derived`'s own rule,
    cited rather than restated in new words.

    The second return value is the surviving count **always**, even when the
    p-value is `None`, which is what lets a caller tell "the null was attempted and
    every draw was degenerate" from "no null was attempted at all" — two states
    that otherwise reach `run.yaml` byte-identical.
    """
    keys = sorted(collapsed)
    rows = [{"unit": key, **collapsed[key]} for key in keys]
    table = unit_table_from_rows(rows)
    # NOT wrapped in `try`, and the docstring above says why: a failure in the
    # metric's own definition for this table is a fault to surface, exactly as
    # `percentile_of_derived` leaves its single unresampled call uncontained.
    observed = compute(table, dict(labels))
    if observed is None or math.isnan(float(observed)):
        return None, 0
    rng = random.Random(seed)
    pool = [labels[key] for key in keys]
    reached = 0
    survivors = 0
    varied = False
    for _ in range(n):
        rng.shuffle(pool)
        drawn_labels = dict(zip(keys, pool, strict=True))
        try:
            drawn = compute(table, drawn_labels)
        except Exception:
            continue
        if drawn is None or math.isnan(float(drawn)):
            continue
        survivors += 1
        if float(drawn) != float(observed):
            varied = True
        if float(drawn) >= float(observed):
            reached += 1
    if not varied or survivors == 0:
        return None, survivors
    return (1 + reached) / (n + 1), survivors


def paired_delta_of_derived(
    of: dict[str, dict[str, Any]],
    against: dict[str, dict[str, Any]],
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


def _drawable_content(
    item: Sequence[str],
    of: Mapping[str, Mapping[str, float]],
    against: Mapping[str, Mapping[str, float]],
) -> tuple[tuple[tuple[tuple[str, float], ...], tuple[tuple[str, float], ...]], ...]:
    """What a drawable thing contributes to a draw, as a comparable value.

    The pair of rows each of its keys carries, sorted — so two things with the
    same rows in a different key order are the same contribution, which is what
    "the draw cannot vary" has to mean. The keys themselves are deliberately NOT
    in the value: a draw that replaces one key with another carrying identical
    rows produces an identical table, and a signature carrying the key would call
    that a difference.

    **This is the WHOLE row, not the column the compute closure reads**, and that
    makes the refusal narrower than its per-condition siblings, whose own draws
    carry one `(value, weight)` pair each. A collapsed table holding several
    recorded columns can differ on a column this contrast's closure never touches,
    and the refusal then does not fire though that metric's draw cannot vary. The
    filed defect is still closed — a near-unique `stratify_by` puts one drawable
    thing in each stratum, so the check holds however many columns the rows carry
    — but the general case is bounded by this and is not claimed.
    """
    return tuple(
        sorted(
            (tuple(sorted(of[key].items())), tuple(sorted(against[key].items()))) for key in item
        )
    )


def _draw_pools(
    keys: list[str],
    strata: dict[str, str] | None,
    clusters: dict[str, str] | None,
) -> list[list[list[str]]]:
    """One draw shape, for a percentile construction's callers.

    A list of stratum groups, each holding the DRAWABLE things that stratum
    owns, each of those a list of keys. A unit is the drawable thing by
    default; a whole cluster is, once `clusters` is given (`reference.md`
    § Clustered units: "`resample` resamples clusters, not rows"), which is
    the same move `percentile_over_units_clustered` makes one level up.
    Written as one shape rather than four branches because the
    clustered/unstratified and stratified/unclustered paths must not drift
    apart — and it is RNG-IDENTICAL to the two branches it replaces: with no
    clusters and no strata it is one group of `n` single-key items, so
    `randrange(n)` is called `n` times in the same order; with strata the
    group order and the per-group counts are today's, each key merely
    wrapped.

    Every caller trusts the `strata` × `clusters` composition rule, the
    relabelling invariance and the sorted-keys caller contract to be the same
    as every other's — a second copy of this function is how one caller comes
    to be fixed in one place and not the others. Not enumerated by name or
    count here on purpose: `CLAUDE.md`'s own rule against a call-site count
    near an insertion is what this docstring already violated once, when
    task 15a became a third caller and the "two callers" count went unswept.
    """
    if clusters is None:
        # `keys` order preserved rather than sorted — the unstratified draw
        # indexed `keys` directly, and sorting here would move an unsorted
        # caller's draw sequence.
        items = [[key] for key in keys]
    else:
        by_cluster: dict[str, list[str]] = {}
        for key in keys:
            # Indexed, not `.get`-ed, the discipline `t_over_units_clustered`
            # states: a key the roster doesn't hold is a core defect, and a
            # cluster of its own for it would raise the count the interval rests
            # on.
            by_cluster.setdefault(clusters[key], []).append(key)
        # Ordered by their own sorted contents rather than by label, so a
        # relabelled roster draws the identical sequence —
        # `percentile_over_units_clustered`'s own invariance, for the same
        # reason.
        items = sorted(sorted(group) for group in by_cluster.values())
    pools: list[list[list[str]]]
    if strata is None:
        pools = [items]
    else:
        # **`keys` must already be sorted ascending when `strata` is given.**
        # This is a caller-contract assertion, not a correctness requirement:
        # `pools = [sorted(group) for group in grouped.values()]` followed by
        # `pools.sort()` below makes the whole partition a pure function of
        # CONTENT, so the relabelling invariance holds regardless of the order
        # `keys` arrives in or the order strata are first encountered while
        # walking it — verified by running with this check disabled, a shuffled
        # `keys` list under `strata` draws the identical sequence a sorted one
        # does. What the check buys instead is the same discipline
        # `percentile_of_derived` keeps for itself (`sorted(collapsed)` rather
        # than trusting its caller): this function trusts `paired_keys`, which
        # returns its intersection sorted, so a caller that has stopped doing
        # that is a bookkeeping regression worth raising on rather than
        # correcting quietly and never being told about.
        if keys != sorted(keys):
            raise ValueError(
                "a percentile draw requires keys sorted ascending when strata "
                "is given, matching the contract this module's key functions "
                "already satisfy — not because the result would otherwise "
                "differ, but because a caller that has stopped supplying a "
                "sorted list is a regression worth raising on rather than "
                "correcting silently"
            )
        grouped: dict[str, list[list[str]]] = {}
        for item in items:
            rendered = strata[item[0]]
            for key in item:
                # A stratum must be CONSTANT within a drawable thing. With no
                # clusters an item is one key and this cannot fire; with
                # clusters it is the composition of two declarations rather than
                # a third rule, and it is the same fault
                # `percentile_over_units_clustered` raises under the same code —
                # § Errors carries one row per code covering every emit site.
                if strata[key] != rendered:
                    # Only reachable when `clusters` was given: with no clusters
                    # every item is a single key, and `strata[item[0]] == rendered`
                    # trivially, so this branch can never fire for `item`'s one key.
                    assert clusters is not None
                    raise ContractError(
                        f"cluster {clusters[key]!r} carries stratum values "
                        f"{rendered!r} and {strata[key]!r}. A resample draws "
                        "whole clusters, so a cluster cannot be drawn within one "
                        "stratum while carrying two; stratify on an attribute "
                        "that is constant within a cluster, or drop `cluster_by` "
                        "if the units really are independent",
                        code="E-STATS-RESAMPLE-STRATIFY-VARIES",
                    )
            grouped.setdefault(rendered, []).append(item)
        pools = [sorted(group) for group in grouped.values()]
        pools.sort()
    return pools


def paired_percentile_of_derived(
    of: dict[str, dict[str, Any]],
    against: dict[str, dict[str, Any]],
    keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
    method: str = "paired_percentile_over_units",
    clusters: dict[str, str] | None = None,
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

    `method` names the `Interval` the caller gets back, rather than this
    function deriving one from a `weights` parameter it deliberately does not
    take: this construction is shared by a derived contrast, which core does
    not weight (the weight column reaches `aggregate` as a unit attribute
    instead), and a recorded column's contrast, which it does — one
    construction, two possible `method` strings, and the arithmetic that picks
    between them lives in the caller's own resample closure, not here.

    `strata`, when given, resamples within each stratum rather than over the
    whole set of drawable things — the same `resample.stratify_by` honoured per
    condition by `percentile_over_units` and `percentile_of_derived`, honoured
    here for the first time. **The pairing survives the stratification**: one
    drawn key list still feeds both sides, so stratifying changes which keys are
    drawn and never that the two sides see the same ones — drawing each side's
    strata independently would resample the two conditions apart, the same
    failure the unstratified draw's docstring above already argues about.
    `strata` is indexed, not `.get`-ed, the discipline `percentile_of_derived`'s
    own `strata` branch already keeps: a caller whose roster and mapping have
    come to disagree about which units exist is a core defect, not a silent
    extra stratum. Pools are ordered by their own sorted contents rather than by
    label, so renaming a stratum draws the identical sequence of tables — the
    same relabelling invariance `percentile_over_units` and
    `percentile_of_derived` keep.

    `clusters`, when given, makes the drawable thing a whole cluster rather than
    a unit — `reference.md` § Clustered units: "`resample` resamples clusters,
    not rows", and § Statistical reporting: "the percentile forms resample
    whole clusters — jointly across both sides when paired". Each replicate
    draws `G` clusters with replacement and pools their units, so a larger
    cluster contributes more rows than a smaller one and a replicate's row
    count varies — the same construction `percentile_over_units_clustered`
    makes one level up, taken here over the paired draw instead. `clusters` and
    `strata` compose: a cluster is drawn within its own stratum, and a stratum
    must be constant within a cluster — a cluster carrying two stratum values
    is indivisible and cannot be dealt to either, refused as
    `E-STATS-RESAMPLE-STRATIFY-VARIES`, the same code
    `percentile_over_units_clustered` raises for the identical fault one level
    up (`reference.md` § Errors carries one row per code covering every emit
    site). Clusters are ordered by their own sorted contents rather than by
    label, the same relabelling invariance `percentile_over_units_clustered`
    keeps, so a relabelled roster draws the identical sequence.

    Returns `PairedResample(interval=None, draws_used=0, pool=[])` — the same
    shape the `len(keys) < 2` early return already builds — when every drawable
    thing within every stratum carries an identical pair of rows: the draw is
    then a constant, and the interval would otherwise be `[x, x]`, a zero-width
    95 % interval `reference.md` § Statistical reporting refuses in those terms.
    Content, not count: two clusters per stratum carrying identical rows clear
    any count floor and are still degenerate. See `_drawable_content` for what
    "identical" compares and what it deliberately does not.
    """
    if len(keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    pools = _draw_pools(keys, strata, clusters)
    # Content-based, not count-based, and applied whether or not `strata` or
    # `clusters` were given. If every drawable thing within a stratum carries the
    # same pair of rows (a stratum holding one of them trivially so), drawing any
    # of them with replacement reproduces the same table on every replicate, so no
    # draw can differ from any other whatever count that stratum holds — and the
    # interval would be `[x, x]`, which `reference.md` § Statistical reporting
    # refuses in those terms. This is `percentile_over_units`'s and
    # `percentile_over_units_clustered`'s own refusal, taken over the paired
    # form's two collapsed tables instead of one column. A count floor answers a
    # different question: two clusters per stratum with identical rows clear it
    # and are still degenerate.
    if all(len({_drawable_content(item, of, against) for item in group}) <= 1 for group in pools):
        return PairedResample(interval=None, draws_used=0, pool=[])
    values: list[float] = []
    for _ in range(draws):
        # Each stratum contributes exactly as many DRAWABLE THINGS as it holds,
        # and each contributes all of its keys — "pools their units", so a large
        # cluster contributes more rows than a small one and a replicate's row
        # count varies. ONE drawn key list feeds BOTH sides, under clusters and
        # strata exactly as without: drawing each side independently would
        # resample the two conditions apart and destroy the pairing.
        drawn = [
            key
            for group in pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
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
        interval=Interval(low=values[lo], high=values[hi], method=method),
        draws_used=len(values),
        pool=values,
    )


def _side_content(
    item: Sequence[str], rows: Mapping[str, Mapping[str, float]]
) -> tuple[tuple[tuple[str, float], ...], ...]:
    """What a drawable thing contributes to ONE side's draw, as a comparable value.

    `_drawable_content`'s single-sided counterpart: the row each of its keys
    carries, sorted, so two things with the same rows in a different key order are
    the same contribution. The keys are deliberately not in the value, for the
    reason that function gives — a draw that replaces one key with another carrying
    an identical row produces an identical table.

    Separate rather than a parameter on `_drawable_content`, because the unpaired
    draw's two sides hold DIFFERENT key sets and a signature taking both mappings
    could only be given one side's keys with the other's rows.
    """
    return tuple(sorted(tuple(sorted(rows[key].items())) for key in item))


def unpaired_percentile_of_sides(
    of: dict[str, dict[str, Any]],
    against: dict[str, dict[str, Any]],
    of_keys: list[str],
    against_keys: list[str],
    compute_of: "Callable[[UnitTable], float | None]",
    compute_against: "Callable[[UnitTable], float | None]",
    seed: int,
    draws: int = 2000,
    confidence: float = 0.95,
    strata: dict[str, str] | None = None,
    method: str = "unpaired_percentile_over_units",
    of_clusters: dict[str, str] | None = None,
    against_clusters: dict[str, str] | None = None,
) -> PairedResample:
    """Percentiles of the difference, resampling within each side independently.

    `reference.md` § Statistical reporting: "The percentiles of the difference,
    resampling within each side independently. The unpaired counterpart of the
    second."

    **This is a separate construction from `paired_percentile_of_derived` and not a
    `method` string over it.** That function draws ONE key list and applies it to
    both sides, and its docstring argues at length that drawing each side
    independently "would resample the two conditions apart and destroy the
    pairing" — which is exactly the arrangement this function's own definition
    requires, because the two sides here hold disjoint units and there is no
    pairing to destroy. Two spellings of two different constructions, not one
    construction serving two names.

    Two computes, not one, for `paired_percentile_of_derived`'s own reason: a
    contrast's two sides can hold their `cfg` fixed on every axis except the one
    being compared, and `aggregate(units, cfg)` is evaluated once per side with
    that side's own `cfg`.

    `method` names the `Interval` the caller gets back rather than being derived
    from a parameter here: one construction serves the plain and the `_clustered`
    spelling, and the arithmetic that picks between them lives in the caller.

    `strata` resamples within each stratum, per side. `of_clusters`/
    `against_clusters` make the drawable thing a whole cluster within its own side
    — `reference.md` § Statistical reporting: "the percentile forms resample whole
    clusters", the "jointly across both sides" qualifier being the paired case's.
    Two mappings rather than one, because the two sides' key sets are disjoint and
    a single mapping would be indexed with keys it does not hold. Both compose with
    `strata` through `_draw_pools`, which is where every one of those rules lives.

    **The degenerate refusal is per side and it is AND.** Where every drawable thing
    in every stratum of BOTH sides carries the same row, every replicate reproduces
    the same difference, both percentile ranks land on it, and the interval has zero
    width while looking exactly like a narrow one — which § Statistical reporting
    refuses in those terms. Where only one side cannot vary the difference still
    can, so there is a real interval to report and refusing it would be the same
    defect in the opposite direction. Content, not count: two clusters per stratum
    carrying identical rows clear any count floor and are still degenerate.

    `PairedResample(interval=None, draws_used=0, pool=[])` below two keys on either
    side, the floor every construction here shares. The pool is sorted on both
    return paths, because `interval_at` reads fixed ranks off it and does not sort.
    """
    if len(of_keys) < 2 or len(against_keys) < 2:
        return PairedResample(interval=None, draws_used=0, pool=[])
    rng = random.Random(seed)
    of_pools = _draw_pools(of_keys, strata, of_clusters)
    against_pools = _draw_pools(against_keys, strata, against_clusters)
    if all(len({_side_content(item, of) for item in group}) <= 1 for group in of_pools) and all(
        len({_side_content(item, against) for item in group}) <= 1 for group in against_pools
    ):
        return PairedResample(interval=None, draws_used=0, pool=[])
    values: list[float] = []
    for _ in range(draws):
        # TWO draws per replicate, `of` first and `against` second, each over its
        # own side's pools — which is what "resampling within each side
        # independently" means, and the one thing this construction does that
        # `paired_percentile_of_derived` refuses to do.
        drawn_of = [
            key
            for group in of_pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
        drawn_against = [
            key
            for group in against_pools
            for _ in range(len(group))
            for key in group[rng.randrange(len(group))]
        ]
        # Table construction is deliberately OUTSIDE the `try`, matching
        # `paired_percentile_of_derived`'s own placement: a key drawn for one
        # side that does not index that side's mapping is a caller-space bug —
        # the two sides' disjoint key spaces make that reachable in a way the
        # paired form's single shared key list cannot — and it must raise
        # rather than be silently absorbed into "degenerate draw, continue"
        # below. Only what `compute_of`/`compute_against` themselves do is
        # allowed to fail quietly.
        table_of = unit_table_from_rows([{"unit": k, **of[k]} for k in drawn_of])
        table_against = unit_table_from_rows([{"unit": k, **against[k]} for k in drawn_against])
        try:
            a = compute_of(table_of)
            b = compute_against(table_against)
        # A degenerate draw, not a fault; see `percentile_of_derived`. Also the same
        # containment for a template returning a non-numeric metric, which reaches
        # `cli.py`'s resample closure and raises `ValueError` from `float()`.
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
        interval=Interval(low=values[lo], high=values[hi], method=method),
        draws_used=len(values),
        pool=values,
    )


def _is_numeric(value: object) -> bool:
    """`bool` is a `int` subclass in Python but is never a quantity to average."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _across_repeats(values: list[Any]) -> Any:
    """One unit's values for one column, collapsed across the repeats it was handed.

    Three cases, and the third is the one that keeps a published number where it is.

    - Every value a real number: the mean, which is what this function has always
      done and the only case a purely numeric run reaches.
    - SOME values numbers: the mean of those, which is EXACTLY today's arithmetic —
      today's inner loop skipped the non-numeric ones and averaged the rest. Moving
      this to `None` would cost the whole column its metric block, for every unit,
      because `summarize_step` requires *all* carried values numeric (measured). That
      is a published column deleted, which no decision here argues for; the
      disagreement is disclosed instead, by `repeats_disagreeing`.
    - NO value a number: the value itself when the repeats agreed, `None` when they
      did not. `first` and `mode` are rules the user declared for `measurements` and
      never for repeats, and both are order-dependent here — `_gather_repeats`
      iterates in execution order, which `order: randomized` shuffles — so picking
      one would put the shuffle into a published column, the exact fault
      `sorted(candidates)` exists to keep out.

    `None` rather than omitting the key: omission would remove the column from
    `summarize_step`'s `columns` list when every unit disagreed, and `columns` is
    what the derived-key collision check reads — so omission reopens the silent
    coexistence defect through a second door. `_is_numeric(None)` is `False`, so a
    `None` cell keeps the column visible and unpublishable when every unit's cell
    for it is `None` — the case this was measured on. A column where SOME units
    carry a number and others carry `None` is a different case `summarize_step`'s
    own gate decides (Controller ruling 1): the column keeps a block computed over
    the units that carried a number.

    `reference.md` § What isn't a repeat's *"Attributes constant within a key
    collapse to that value with no rule needed"* is the rule reused here, and
    `units.apply_rule` is the sibling that implements it for `measurements`. It is
    deliberately NOT called: it takes a rule name, every name it accepts returns a
    value on disagreement, and there is no declared rule for repeats to pass it.
    """
    numeric = [float(v) for v in values if _is_numeric(v)]
    if numeric:
        return sum(numeric) / len(numeric)
    if _repeats_disagree(values):
        return None
    return values[0]


def _repeats_disagree(values: list[Any]) -> bool:
    """Whether a unit's repeats disagreed about a non-numeric column.

    Pairwise against the first value, on `(is-it-a-number, the value)` rather than on
    the value alone: `True == 1.0` in Python, so a column recorded as `True` in one
    repeat and `1.0` in another would read as constant and collapse to whichever
    arrived first — order-dependent, which is what this rule refuses. Compared
    pairwise rather than through a set, so nothing here depends on a recorded value
    being hashable.

    All-numeric columns are excluded: unequal numbers are what averaging is for, and
    reporting them as a disagreement would fire on every honest run.
    """
    if all(_is_numeric(v) for v in values):
        return False
    first = values[0]
    return any((_is_numeric(v), v) != (_is_numeric(first), first) for v in values)


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


def _gather_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None,
) -> dict[str, dict[str, list[Any]]]:
    """Every value each admitted unit recorded for each column, across the repeats
    it was handed — raw, uncoerced, in the order `sorted(candidates)` fixes.

    One walk, two readers: `collapse_repeats` turns it into one row per unit, and
    `repeats_disagreeing` asks it which columns disagreed. A second walk would be a
    second implementation of the membership rule, and the two would drift.

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
    is admitted at all — the same intersection `runner.attrition` takes for
    `completed`, and for the same reason: a unit present in three of five seeds
    would otherwise enter the average on a different number of observations than
    its neighbours, which is a ragged table dressed as a rectangular one. A unit
    recorded in some of the repeats it was handed and not others is dropped here
    exactly as it is excluded from `completed` there, so the `n` reported beside
    this table's interval is never a lie about how many observations went into it.

    "Handed" is what `fold_members` narrows. Without a fold it is every repeat.
    With one, `reference.md` § The per-unit tables is explicit that intersecting
    over *every* repeat "would report `completed: 0` for any design containing a
    fold, because no unit is ever in more than one of them" — so the intersection
    is taken over that unit's own fold's repeats instead.
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

    gathered: dict[str, dict[str, list[Any]]] = {}
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
        # The unit passed the membership gate, so it IS a unit. It gets a row even
        # when every value it recorded is non-numeric, and even when it recorded no
        # column at all — `io.record(key, {})` settles a unit and records nothing,
        # which is reachable (measured). `runner.attrition` already counts such a
        # unit `completed`; this was the one place in the program that did not.
        gathered.setdefault(key, {})
        for lb in mine:
            for row in rows_by_label[lb]:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    # `unit` is the key, not a measurement. `cli._attributed` is what
                    # puts the key column back for a bootstrap draw that duplicates
                    # units; it is never a column of `collapsed`.
                    if column == "unit":
                        continue
                    gathered[key].setdefault(column, []).append(value)
    return gathered


def collapse_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Collapse each admitted unit's repeats into one row, within one condition.

    This is the collapse the inference base rests on: repeats are a variance
    component, not the inference base, so a unit's repeats are averaged into one
    row *before* any interval is computed over units. `_gather_repeats` decides
    which units are admitted and carries every value, raw; `_across_repeats`
    decides what one unit's values for one column collapse to — see its own
    docstring for the three cases.

    "Handed" is what `fold_members` narrows, and the average follows from the
    same set, which is what makes the collapse **inner-to-outer**
    (`reference.md` § How a metric becomes a number): under `fold` alone a unit
    has one handed label and its value passes through unchanged, so folds
    *concatenate* into the union of the partitions; under `fold × seed` the
    handed labels are that fold's seeds, so the seeds average within the fold
    before the folds are combined. Flattening all 30 executions of a 10 × 3
    design would average numbers that are not exchangeable, and averaging across
    folds would divide each unit's single observation by one — both produce
    plausible values and neither raises, which is why this is stated at length.
    """
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    return {
        key: {col: _across_repeats(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }


def paired_keys(
    of: dict[str, dict[str, Any]],
    against: dict[str, dict[str, Any]],
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


def unpaired_keys(
    of: dict[str, dict[str, Any]],
    against: dict[str, dict[str, Any]],
    allowed: set[str] | None,
) -> tuple[list[str], list[str]]:
    """Each side's own completed units, narrowed by a `within` stratum if given.

    `paired_keys`' counterpart for a contrast whose two conditions differ on a
    declared `sweep.groups` axis: the two sides hold disjoint sets of units, so
    there is no intersection to take and no per-unit difference to contribute. What
    replaces the intersection is two sets, and what replaces the mean of a
    difference vector is a difference of two means.

    **This function does not decide whether a comparison is paired** —
    `contrasts.crossed_group_axes` does — and it deliberately does not subtract the
    two sides from each other. Two sides sharing a key is not what makes a
    comparison paired, the group axis is, and a set difference here would silently
    drop a unit from a roster whose arms overlap for a reason this function cannot
    see.

    Sorted, for the reason `paired_keys` sorts: a resample over these keys must be
    row-order invariant, and `unpaired_percentile_of_sides` asserts a sorted-keys
    caller contract when `strata` is given.

    `allowed` narrows **both** sides. A narrowing applied to one would compute a
    delta over a stratum on one side and a whole arm on the other, which is exactly
    the number no reader could detect is wrong.
    """
    of_keys = set(of)
    against_keys = set(against)
    if allowed is not None:
        of_keys &= allowed
        against_keys &= allowed
    return sorted(of_keys), sorted(against_keys)


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


def repeats_disagreeing(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, int]:
    """Column name -> how many admitted units disagreed about it across their repeats.

    Asks the ROWS, not the collapsed cell. A recorded `None` and a collapsed
    disagreement are the same cell (`coerce_scalars` leaves `None` alone, and
    `reference.md` § The per-unit tables makes an all-`None` column legal), so a
    scan of `collapsed` would answer this question with a proxy and give one answer
    to two different facts.

    The same four arguments `collapse_repeats` takes, over the same `_gather_repeats`
    walk, so membership has one implementation. Sorted keys, so the warning order is
    a property of the roster rather than of the shuffle — the reason
    `_gather_repeats` sorts.

    A column whose values are all numbers never appears here: unequal numbers are
    what averaging is for. A column that is numeric in some repeats and a string in
    others DOES appear, and its collapsed cell is still the mean of the numbers —
    the disclosure is the warning, not the loss of the column (`_across_repeats`
    says why).
    """
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    counts: dict[str, int] = {}
    for cols in gathered.values():
        for column, values in cols.items():
            if _repeats_disagree(values):
                counts[column] = counts.get(column, 0) + 1
    return {column: counts[column] for column in sorted(counts)}


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


def _beside_n_copy(beside_n: dict[str, Any] | None) -> dict[str, Any]:
    """`beside_n`, fresh for one metric block rather than the same object
    spread into every one.

    `beside_n` is built once per run (or once per condition) and reused across
    every metric block a call to `summarize_step` writes. Spreading the same
    dict-valued entry — `technical_n`, and now `resample` — into more than one
    block hands `yaml.safe_dump` the same object twice, and its default
    aliasing writes the first occurrence as `&id001 {...}` and every other as
    a bare `*id001` pointer. `hypotheses.py`'s `_observed_block` names the
    consequence exactly: "the number … is no longer readable where it is
    written" — a `run.yaml` a human opens must show the value at every block,
    not a pointer to the first one. A scalar-valued entry (`weighted_by`, a
    string) doesn't have this failure mode — a string is immutable and two
    equal strings dumping identically costs nothing to a reader either way —
    but copying every entry uniformly is simpler than deciding per key which
    ones need it, and cheap at this size.

    `copy.deepcopy`, not `dict(v)`: `resample`'s own `stratify_by` is a list
    nested one level inside the dict, and a shallow `dict(v)` copies the outer
    mapping while still pointing every copy's `stratify_by` at the one list
    object `cli.py` built once — which aliases exactly the same way, one level
    down, and a first attempt at this fix shipped that shallow version and
    caught the bug only by tracing the actual emitted `run.yaml` byte for byte,
    not by reasoning about the dict alone.
    """
    if not beside_n:
        return {}
    return {k: (copy.deepcopy(v) if isinstance(v, dict) else v) for k, v in beside_n.items()}


def summarize_step(
    collapsed: dict[str, dict[str, Any]],
    counts: dict[str, float],
    derived: dict[str, Any] | None = None,
    seed: int | None = None,
    resample: "dict[str, Callable[[UnitTable], float | None]] | None" = None,
    draws: int = 2000,
    beside_n: dict[str, Any] | None = None,
    weights: dict[str, Any] | None = None,
    clusters: dict[str, str] | None = None,
    resample_columns: bool = False,
    strata: dict[str, str] | None = None,
    null_test: dict[str, Any] | None = None,
    labels: dict[str, str] | None = None,
    null_fns: "dict[str, Callable[[UnitTable, dict[str, str]], float | None]] | None" = None,
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
    `technical_n`, `weighted_by`, and `resample` today (`_beside_n_copy`, not a
    bare spread, is what makes "copied" true rather than "shared": a dict-valued
    entry spread by reference into more than one block is one Python object
    dumped twice, and `yaml.safe_dump`'s aliasing turns every occurrence after
    the first into a pointer at the first). It is the second of two routes a
    count-shaped fact travels, and which one a new fact takes is decided by
    where `reference.md` shows it:

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

    A DERIVED metric's interval **is clustered by `percentile_of_derived_clustered`
    when `clusters` is given** — each replicate drawing `G` clusters with
    replacement and building a `UnitTable` from their pooled units, whose row
    count varies per draw, `G` being `units.cluster_count_of`'s answer over these
    same keys. Unclustered, `percentile_of_derived` draws units instead. Which
    one runs is decided beside the derived keys below.

    **`clusters` is recomputed per column**, for exactly the reasons `completed`
    and `effective` already are: § Clustered units reports the cluster count "as
    the effective sample size alongside the unit count" and § Statistical
    reporting gives `t_over_units_clustered` "df = clusters − 1", so the figure is
    the df of *this column's* interval, and a ragged column drawn from a subset of
    the completed units sits in a subset of their clusters. Printing the
    condition-wide count beside it would name a df no interval used. A full
    column's figure is identical to `counts`'; a ragged one's is its own.

    A DERIVED metric takes the condition-wide figure from `counts` for
    `effective`: `aggregate` returned one number over the whole collapsed
    table, so there is no per-column carrier set to recompute a WEIGHTED
    figure over — core never weights a derived metric itself (§ Weighted
    samples hands the weight column to `aggregate` as a unit attribute
    instead). `clusters` is different: a derived metric has no ragged
    per-column carrier either, but `percentile_of_derived_clustered`'s own
    `G` is the distinct values `clusters` takes over `collapsed`'s keys, so
    `n.clusters` is recomputed from those same keys below rather than passed
    through from `counts` unmodified — the fix for Major 3 of the batch-3
    review, which found the two could disagree whenever `collapsed` is a
    proper subset of the roster `counts` was computed over.

    `resample_columns` is the gate a RECORDED COLUMN's interval construction reads
    (H4a task 14). A column always has a `t_over_units` fallback available, so
    resampling it is a *choice* — unlike a derived metric, which has no fallback
    and is resampled whenever `resample`/`seed` let it be, whether or not
    `statistics.resample` was ever declared. `resample_columns=True` (only when
    `cli.py`'s `_resolved_resample(doc)["declared"]` is true) switches a column's
    interval from `t_over_units`/`weighted_t_over_units` (or their `_clustered`
    forms) to `percentile_over_units`/`percentile_over_units_clustered`, over the
    same `values`/`column_weights`/`column_keys`/`clusters` the unresampled branch
    already assembled — the `value` itself does not move, only the construction
    of the interval around it.

    `strata` is unit key → that unit's `statistics.resample.stratify_by` label,
    supplied only when the declaration carries one — built in `cli.py` the same
    way `weights` and `clusters` are, typically over the whole roster (though
    what this function requires is narrower: total over the collapsed table's
    keys, a roster-wide mapping being the common way a caller supplies that).
    **The keys the strata are looked up by are the column's own**, taken
    in the same pass as its values, for the identical reason the weights and
    clusters paragraphs above give: a vector filtered or ordered differently
    would stratify the wrong unit and produce a plausible number rather than an
    error. Indexed rather than `.get`-ed for the same reason those two are: every
    key in the collapsed table must have an entry in `strata`, so a default
    would quietly invent a stratum instead of failing. It
    reaches both interval constructions this function can produce, and the
    DERIVED metrics below the same call: `percentile_over_units`/
    `percentile_over_units_clustered` draw within each stratum for a recorded
    column, and `percentile_of_derived` draws unit keys within each stratum,
    preserving each stratum's key count, for a derived one — the same
    declaration honoured the same way on both paths, so one declared
    `stratify_by` cannot leave a stratified column beside an unstratified
    derived metric in the same table with nothing in the record to tell a
    reader which is which.

    `resample_draws` is **absent** from a column's block when `resample_columns`
    is `False` (or `seed` is `None`): no resample was attempted, and a `null`
    there would claim otherwise. When `resample_columns` is `True` it is present
    and **two-valued**, not the derived metric's three-valued `null`/`0`/*n*
    scheme: `null` when `interval is None` (fewer than two units, or too few
    draws for the confidence level — the same reasons `percentile_over_units`
    returns `None` at all) — there is no interval for a draw count to describe,
    so recording one would assert survivor evidence for a refused draw — and
    otherwise the *requested* `draws`, never a survivor count — **given finite
    recorded values and finite weights**. Under that condition a column's draw
    statistic (a mean, or a weighted mean, over a non-empty sample) is always
    defined once an interval exists at all, so unlike `percentile_of_derived`
    there is no per-draw failure to filter and no `0` bucket ("attempted,
    every draw individually degenerate") for a column to reach. **Nothing on
    this path checks that condition**: a `nan` among `values`, or a weight
    vector whose sum overflows, is not refused here and reaches `ci95` and
    `resample_draws: draws` exactly as a clean sample would — a known, unfixed
    gap filed in `docs/superpowers/spec-defects.md`, not a guarantee this
    docstring is making.

    `null_test`, `labels` and `null_fns` are a DERIVED metric's own p-value
    path, and they never reach a recorded column: decision 7 gives a column no
    null at all, because `mean(column)` over a condition's units is invariant
    under every relabelling — the null would be the observed value repeated
    `n` times and the p-value exactly 1.0, a number that reads as a finding
    and is an artifact of asking rather than a fact about the design.
    `null_test` is the resolved `{"method", "n", "shuffle", "level", ...}`
    dict; `labels` is the roster-wide `{unit key: label}` mapping the
    `shuffle` attribute takes; `null_fns` is `key → callable`, one per derived
    metric, built the same way `resample`'s closures are — `cli.py`'s
    `_make_null_fn`, a SECOND closure family rather than a keyword added to
    `_make_resample_fn`'s (§ Corrections, correction 1): that closure's
    `_attributed` merges the roster's declared attributes OVER each row, which
    erases a relabelling written into the table before `aggregate` ever sees
    it, so reusing it here would report `p_value: 1.0` for every derived
    metric in every run. Where a key has both a callable and `null_test`
    declared **and `clusters` is `None`**, `permutation_of_derived` runs and
    the metric block gains `p_value`, `null_draws`, and the `null_test` echo —
    uncorrected, per decision 5: the correction pass in `cli.py` merges
    `p_value_corrected` in afterward from the family this member belongs to,
    not from this call.

    **A declared `cluster_by` suppresses this write, and that is a gap this
    build has not closed rather than a design choice.** `permutation_of_derived`
    (task 12) draws one free relabelling over every unit — it takes no cluster
    argument, and no clustered counterpart exists in this build. § Clustered
    units requires the opposite treatment for a design declaring `cluster_by`,
    and measured directly against Fixture C's roster, the free draw lands on
    the spec's own "permutes across clusters (the wrong stratum)" row (≈0.48),
    not the within-cluster answer a declared `cluster_by` promises — so
    reporting it beside `null_test.level: "within_cluster"` would be a
    declaration accepted whose effect is not delivered, worse than the absent
    p-value this gate chooses instead.
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
        # The column's OWN keys, the same one-pass discipline `weights` and
        # `clusters` already follow and for the identical reason the docstring
        # gives for both: a vector filtered or ordered differently draws the
        # wrong composition and produces a plausible number rather than an
        # error. Indexed rather than `.get`-ed — every key in `column_keys`
        # came from the roster the caller built `strata` from, so a default
        # would quietly invent a stratum instead of failing.
        column_strata = None if strata is None else [strata[key] for key in column_keys]
        n_block: dict[str, Any] = {**counts, "completed": len(values)}
        if clusters is not None:
            n_block["clusters"] = cluster_count_of(clusters, column_keys)
        interval: Interval | None
        value: float | None
        column_weights: list[Any] | None = None
        if weights is None:
            value = mean_of(values)
        else:
            column_weights = [weights[key] for key, _ in carried]
            value = weighted_mean_of(values, column_weights)
            n_block["effective"] = kish_effective_n(column_weights)
        # A recorded column has a `t_over_units` fallback available, so
        # resampling it is a CHOICE and `statistics.resample` is what makes
        # it — the asymmetry with a derived metric, which has no fallback and
        # is resampled either way, below. The VALUE computed above is
        # unchanged in every branch: § Weighted samples puts the weights "in
        # the estimate rather than in the drawing", and § Clustered units
        # makes the cluster the draw while `n.clusters` (set above) still
        # reports the count. Only the interval's construction moves.
        if resample_columns and seed is not None:
            interval = (
                percentile_over_units(
                    values, seed, draws=draws, weights=column_weights, strata=column_strata
                )
                if clusters is None
                else percentile_over_units_clustered(
                    values,
                    column_keys,
                    clusters,
                    seed,
                    draws=draws,
                    weights=column_weights,
                    strata=column_strata,
                )
            )
        elif weights is None:
            interval = (
                t_over_units(values)
                if clusters is None
                else t_over_units_clustered(values, column_keys, clusters)
            )
        else:
            # `weights is not None` here (the `elif` above took the `None`
            # case), so `column_weights` was assigned in the first `if` block
            # above — mypy can't see that across the two separate
            # `if`-statements, hence the assert.
            assert column_weights is not None
            interval = (
                weighted_t_over_units(values, column_weights)
                if clusters is None
                else weighted_t_over_units_clustered(values, column_keys, clusters, column_weights)
            )
        out[column] = {
            **_beside_n_copy(beside_n),
            "value": value,
            "basis": "units",
            "n": n_block,
            "ci95": [interval.low, interval.high] if interval else None,
            "method": interval.method if interval else None,
            # Present only under a declared resample (`resample_columns` true
            # and a `seed` given), and then TWO-valued rather than a survivor
            # count: `null` when `interval is None` (too few units, or too
            # few draws for the confidence level) — there is no interval for
            # a draw count to describe, and recording one would assert
            # survivor evidence for a draw that never happened — otherwise
            # the REQUESTED `draws`, since a column's mean is always defined
            # once an interval exists at all and so has no per-draw failure
            # to survive-count the way a derived metric's recompute does.
            # ABSENT rather than `null` when no resample is declared at
            # all — `null` already means "declared, but the interval came
            # back empty", and reusing it for "never asked" would erase that
            # distinction (`docs/superpowers/spec-defects.md`).
            **(
                {"resample_draws": draws if interval else None}
                if resample_columns and seed is not None
                else {}
            ),
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
        # A derived metric has no per-column carrier set to recompute `clusters`
        # from — `aggregate` returned one number over the whole table, unlike a
        # recorded column's own ragged `column_keys` — but `percentile_of_derived_clustered`'s
        # own `G` (task 15a) is the distinct values `clusters` takes over
        # `collapsed`'s OWN keys, not `counts["clusters"]`'s condition-wide
        # figure, which can disagree with it whenever `collapsed` is a proper
        # subset of the roster `attrition` counted (a step recording for only
        # some completed units). Recomputed once here, over the same keys the
        # construction itself draws from, so `n.clusters` cannot print a
        # different `G` from the one the interval actually rests on.
        derived_clusters_n = cluster_count_of(clusters, collapsed) if clusters is not None else None
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
                derived_interval, draws_used = (
                    percentile_of_derived_clustered(
                        collapsed, clusters, compute, seed, draws=draws, strata=strata
                    )
                    if clusters is not None
                    else percentile_of_derived(collapsed, compute, seed, draws=draws, strata=strata)
                )
            else:
                derived_interval, draws_used = None, None
            derived_n = {**counts, "completed": len(collapsed)}
            if derived_clusters_n is not None:
                derived_n["clusters"] = derived_clusters_n
            out[key] = {
                **_beside_n_copy(beside_n),
                "value": value,
                "basis": "units",
                "n": derived_n,
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
            # Decision 7's other half: a DERIVED metric gets a p-value when a
            # `null_test` is declared and a closure exists for this key — the
            # closure is `null_fns`, never `resample`, for the reason the
            # docstring above gives. `label` and `n` come from the resolved
            # `null_test` dict; the level itself never reaches this function,
            # since it changed nothing about the DRAW `permutation_of_derived`
            # performs (unlike `permutation_over_units_clustered`, which reads
            # it to choose whole-cluster versus within-cluster relabelling) —
            # only the echo shows it, so a reader can see which relabelling a
            # `shuffle` naming a clustered attribute actually ran.
            null_fn = (null_fns or {}).get(key)
            # **Gated on `clusters is None`, which is a spec gap this build has
            # not closed rather than a stylistic choice.** `permutation_of_derived`
            # (task 12) does one free `rng.shuffle` over every unit's label —
            # it takes no cluster argument, and no clustered counterpart exists
            # in this build. Measured directly against fixture C's own roster:
            # a free relabelling gives ≈0.4845, the spec's own "permutes across
            # clusters (the wrong stratum)" row, not the within-cluster
            # `1/5001` a declared `cluster_by` promises. § Clustered units gives
            # the two designs OPPOSITE treatments, so publishing that number
            # beside `null_test.level: "within_cluster"` would be a declaration
            # accepted whose effect is not delivered — worse than reporting no
            # p-value at all, which is what this gate chooses instead. With it,
            # `null_test.get("level")` can only ever have resolved to `"rows"`
            # on a path that reaches this write, so the echo below cannot lie.
            if (
                null_test is not None
                and null_fn is not None
                and labels is not None
                and seed is not None
                and clusters is None
            ):
                p_value, null_draws = permutation_of_derived(
                    collapsed, labels, null_fn, seed, n=null_test.get("n", 5000)
                )
                out[key]["p_value"] = p_value
                out[key]["null_draws"] = null_draws
                out[key]["null_test"] = {
                    "method": null_test.get("method", "permutation"),
                    "n": null_test.get("n", 5000),
                    "shuffle": null_test.get("shuffle"),
                    "level": null_test.get("level") or "rows",
                }
    return out


class UnitTable:
    """Row iteration, column access, `len`, `columns` — and nothing else.

    Deliberately not a `DataFrame`: one that also promised indexing, filtering
    and `.loc` would be one, and core could never change what backs it — a lazily
    materialized table, a view over a partition — without breaking every plugin.
    The same reasoning that keeps `io.units` to three operations.
    """

    def __init__(self, collapsed: dict[str, dict[str, Any]]) -> None:
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

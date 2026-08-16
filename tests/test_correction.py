import pytest

from publishable.correction import (
    ALPHA,
    Member,
    corrected_fields,
    corrected_for,
    family_members,
    family_shape,
    rank_family,
)
from publishable.stats import paired_t_over_units


def _m(where="1", step="s", metric="r", delta=0.1, ci95=(0.0, 0.2), decl=0):
    return Member(
        where=where,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=None,
        diffs=(0.1, 0.2, 0.3),
        declaration_index=decl,
    )


def test_alpha_is_five_percent_and_not_configurable():
    """`ci95` is in every record field name, so the raw confidence is fixed and
    only the corrected level varies. A config field for it would have to rename
    the record field."""
    assert ALPHA == 0.05


def test_a_member_with_an_interval_rejects_both_pool_and_diffs():
    """Both set would let `_corrected_bounds` silently take the `diffs`
    branch and build a *t* interval as the corrected counterpart of a
    *percentile* raw one — wrong by construction, not by evidence."""
    with pytest.raises(ValueError, match="both"):
        Member(
            where="1",
            step="s",
            metric="r",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=(0.1, 0.2, 0.3),
            diffs=(0.1, 0.2, 0.3),
            declaration_index=0,
        )


def test_a_member_with_an_interval_rejects_neither_pool_nor_diffs():
    """Neither set would make `_corrected_bounds` return `None` for a reason
    that has nothing to do with the pool being too small, so `thin: True`
    would fire over a member that was never thin."""
    with pytest.raises(ValueError, match="neither"):
        Member(
            where="1",
            step="s",
            metric="r",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=None,
            declaration_index=0,
        )


def test_a_member_with_no_interval_is_not_in_the_family():
    """Counted-iff-corrected: a metric reported without an interval is not a
    comparison a reader can read as significant, so it neither takes a slot nor
    consumes a rank. `cli` passes `ci95=None` for it."""
    with_interval = _m(metric="r")
    without = Member(
        where="1",
        step="s",
        metric="n_units",
        delta=3.0,
        ci95=None,
        pool=None,
        diffs=None,
        declaration_index=1,
    )
    assert family_members([with_interval, without]) == [with_interval]


def test_the_family_is_comparisons_times_metrics():
    """`reference.md`: "The family is comparisons × metrics, not comparisons." A
    six-condition sweep is five comparisons, but three metrics per step means a
    reader is shown fifteen intervals."""
    members = [_m(where=str(c), metric=k) for c in (1, 2, 3, 4, 5) for k in ("r", "rmse", "auc")]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 5, "metrics": 3}
    assert size == 15


def test_the_worked_example_is_two_comparisons_and_one_metric():
    """`reference.md`'s worked example: 3 conditions give 2 baseline comparisons,
    one metric gives `metrics: 1`, so `family_size: 2`. This is the number the
    acceptance test asserts, pinned here at the arithmetic."""
    members = [_m(where="1", metric="r"), _m(where="2", metric="r")]
    size, shape = family_shape(family_members(members))
    assert size == 2
    assert shape == {"comparisons": 2, "metrics": 1}


def test_a_contrast_and_a_baseline_comparison_are_both_comparisons():
    """`reference.md`: "A 'comparison' is a baseline contrast or a declared one" —
    both put an interval in front of a reader. Counting only `vs_baseline`
    under-corrects by exactly the declared contrasts a config asked for."""
    members = [_m(where="1"), _m(where="sensitivity")]
    size, shape = family_shape(family_members(members))
    assert shape["comparisons"] == 2
    assert size == 2


def test_a_metric_absent_from_one_comparison_still_counts_as_a_metric():
    """The product can exceed the member count. That is the conservative
    direction — a larger family means a smaller α and a wider corrected
    interval — and `reference.md`'s own arithmetic is the product. Pinned so
    nobody "fixes" it into the member count."""
    members = [
        _m(where="1", metric="r"),
        _m(where="1", metric="rmse"),
        _m(where="2", metric="r"),
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 2, "metrics": 2}
    assert size == 4  # not 3


def test_the_same_metric_name_in_two_steps_counts_as_two_metrics():
    """`metrics` keys on `(step, metric)`, not `metric` alone. A simplification
    to `{m.metric for m in members}` would collapse `step01.r` and `step02.r`
    into one metric, undercounting the family — and a family counted too small
    gives an α that is too large and corrected intervals that are too narrow,
    which is the failure `reference.md` calls out as worse than not correcting
    at all."""
    members = [
        _m(where="1", step="step01", metric="r"),
        _m(where="1", step="step02", metric="r"),
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 1, "metrics": 2}
    assert size == 2


def test_the_family_ranks_by_estimate_over_half_width():
    """`reference.md`: the ranking statistic is "the point estimate over half the
    raw `ci95` width, largest first" — the one quantity every member has, since
    Holm's own p-value is unavailable here (a `null_test` supplies one only where
    `shuffle` names an attribute, which a parameter-axis contrast never is).

    These are the worked example's two members: kendall at 0.169 over a
    half-width of 0.044 is 3.84, spearman at 0.026 over 0.033 is 0.79. Ranking
    on the raw *width* instead would order them the other way, since kendall's
    interval is the wider of the two."""
    kendall = _m(where="2", metric="r", delta=-0.169, ci95=(-0.213, -0.125))
    spearman = _m(where="1", metric="r", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([spearman, kendall])] == ["2", "1"]


def test_the_ranking_statistic_uses_the_magnitude_not_the_signed_estimate():
    """Kendall's delta is negative and it is the *strongest* member. Ranking on
    the signed estimate puts every negative delta last regardless of its
    evidence, which would silently hand the smallest correction to the members
    that most need it."""
    strong_negative = _m(where="a", delta=-0.169, ci95=(-0.213, -0.125))
    weak_positive = _m(where="b", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([weak_positive, strong_negative])] == ["a", "b"]


def test_ties_break_by_declaration_index_not_where_or_metric_name():
    """`reference.md`: ties break by declaration order — the index `cli`
    assigned when it built the family — not by `where` or by metric name.
    These three carry identical evidence, and their `where`/`metric` would
    order them `(1, auc), (1, rmse), (2, auc)` were the tie-break keyed on
    those fields instead (sorted lexicographically); `declaration_index`
    orders them differently, and that is the order that must win, whichever
    order the members arrive in."""
    a = _m(where="2", metric="auc", delta=0.1, ci95=(0.0, 0.2), decl=2)
    b = _m(where="1", metric="rmse", delta=0.1, ci95=(0.0, 0.2), decl=0)
    c = _m(where="1", metric="auc", delta=0.1, ci95=(0.0, 0.2), decl=1)
    assert [(m.where, m.metric) for m in rank_family([a, b, c])] == [
        ("1", "rmse"),
        ("1", "auc"),
        ("2", "auc"),
    ]
    assert rank_family([a, b, c]) == rank_family([c, b, a])


def test_a_tie_breaks_by_declaration_order_not_by_metric_name() -> None:
    """Two members with identical evidence rank in the order cli built them.

    Named `zeta` first and `alpha` second on purpose: a lexicographic tie-break
    puts `alpha` first, and declaration order puts `zeta` first.
    """
    members = [
        Member(
            where="cond:1",
            step="step02",
            metric="zeta",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=0,
        ),
        Member(
            where="cond:1",
            step="step02",
            metric="alpha",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=1,
        ),
    ]
    assert [m.metric for m in rank_family(members)] == ["zeta", "alpha"]


def test_a_zero_width_interval_ranks_first_rather_than_dividing_by_zero():
    """A point-mass bootstrap is legitimate (S4b task 5 established it), so a
    half-width of exactly 0.0 is reachable and must not raise. Infinite evidence
    ranks first, which is also what the ratio's limit says."""
    point_mass = _m(where="a", delta=0.5, ci95=(0.5, 0.5))
    ordinary = _m(where="b", delta=0.169, ci95=(0.125, 0.213))
    assert [m.where for m in rank_family([ordinary, point_mass])] == ["a", "b"]


def _from_diffs(where, mean, spread, metric="r", decl=0):
    """A member whose `ci95` **is** the t interval over its own `diffs`.

    This matters: `corrected_fields` rebuilds a column metric's corrected
    interval by re-running `paired_t_over_units` over `diffs`, so a member whose
    `ci95` was hand-written to some other value would make "corrected at α equals
    raw" compare two unrelated numbers and fail against a correct
    implementation. Deriving both from one source keeps the assertion about
    Holm's level rather than about the fixture.
    """
    diffs = tuple(mean + spread * ((i % 5) - 2) for i in range(228))
    interval = paired_t_over_units(diffs)
    assert interval is not None
    return Member(
        where=where,
        step="step03_analyze",
        metric=metric,
        delta=sum(diffs) / len(diffs),
        ci95=(interval.low, interval.high),
        pool=None,
        diffs=diffs,
        declaration_index=decl,
    )


def _two_member_family():
    """Two members, the first carrying much the stronger evidence — the worked
    example's shape (kendall against spearman), with the same wide gap in the
    ranking ratio and intervals that are genuinely their own construction."""
    strong = _from_diffs("2", mean=-0.169, spread=0.02, decl=0)
    weak = _from_diffs("1", mean=0.026, spread=0.30, decl=1)
    return strong, weak


def test_corrected_for_takes_the_family_size_it_is_given():
    """The hypothesis family "counts the confirmatory hypotheses whose
    observations core computed, where a sweep's family counts comparisons ×
    metrics" — it "multiplies nothing". Only the size differs, so only the size
    is a parameter."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "bonferroni", 7, {"hypotheses": 7})
    for entry in got.values():
        assert entry["correction_level"] == pytest.approx(0.05 / 7)
        assert entry["family_size"] == 7
        assert entry["family"] == {"hypotheses": 7}


def test_corrected_fields_still_computes_the_sweep_shape():
    """The existing caller keeps its behaviour: it passes the product, not the
    member count, and its breakout still names comparisons and metrics.

    Non-square on purpose, following
    `test_the_level_divides_by_the_family_product_not_the_member_count`'s
    fixture shape: `rmse` is recorded in comparison "1" and absent from
    comparison "2", so 3 members span a family of 2 comparisons × 2 metrics =
    4. A caller that substituted `len(family)` (3) for the product would
    compute `family_size: 3` here and this test would catch it — a square
    fixture (comparisons == metrics == members) cannot, since the product and
    the member count coincide by construction."""
    members = [
        _from_diffs("1", mean=-0.169, spread=0.02, metric="r", decl=0),
        _from_diffs("1", mean=-0.150, spread=0.02, metric="rmse", decl=1),
        _from_diffs("2", mean=0.026, spread=0.30, metric="r", decl=2),
    ]
    got = corrected_fields(members, "bonferroni")
    assert len(got) == 3
    for entry in got.values():
        assert entry["family_size"] == 4
        assert entry["family"] == {"comparisons": 2, "metrics": 2}
        assert entry["correction_level"] == pytest.approx(0.05 / 4)


def test_holm_ranks_within_whatever_family_size_it_is_handed():
    """Holm's level is α/(m−i+1), so a larger m makes rank 1 tighter. Passing a
    size the members did not imply is exactly what the hypothesis family does."""
    strong, weak = _two_member_family()
    got = corrected_for([strong, weak], "holm", 5, {"hypotheses": 5})
    levels = sorted(e["correction_level"] for e in got.values())
    assert levels == [pytest.approx(0.05 / 5), pytest.approx(0.05 / 4)]


def test_holm_corrects_the_weakest_member_by_nothing():
    """`reference.md`: "the weakest comparison in a family is corrected by
    nothing — at rank m the level is α itself", which the worked example shows:
    spearman is rank 2 of 2, so `correction_level: 0.05` and its corrected
    interval *is* its raw one. That is Holm working, not a correction that
    failed, and it is the property that makes Holm more powerful than
    Bonferroni.

    Passed in as `[weak, strong]` — reversed from ranked order — so a
    `rank_family` call replaced by `enumerate` over the input as given cannot
    pass by accident; the correct implementation must actually re-rank."""
    strong, weak_member = _two_member_family()
    got = corrected_fields([weak_member, strong], "holm")
    weak = got[("1", "step03_analyze", "r")]
    assert weak["correction_level"] == pytest.approx(0.05)
    assert weak["ci95_corrected"] == pytest.approx(list(weak_member.ci95))


def test_holm_corrects_the_strongest_member_at_alpha_over_m():
    """Rank 1 of 2 gets α/(m−i+1) = α/2, so its corrected interval is strictly
    wider than its raw one on both sides. Using α for every member — the
    mutation that keeps the weakest member's test green — is caught here."""
    strong_member, weak_member = _two_member_family()
    got = corrected_fields([strong_member, weak_member], "holm")
    strong = got[("2", "step03_analyze", "r")]
    assert strong["correction_level"] == pytest.approx(0.025)
    low, high = strong["ci95_corrected"]
    assert low < strong_member.ci95[0]
    assert high > strong_member.ci95[1]


def test_bonferroni_gives_every_member_the_same_level():
    """α/m regardless of rank — the difference from Holm, and the reason Holm is
    uniformly more powerful."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "bonferroni")
    levels = {e["correction_level"] for e in got.values()}
    assert levels == {0.025}
    for member in (strong, weak):
        entry = got[(member.where, member.step, member.metric)]
        low, high = entry["ci95_corrected"]
        assert low < member.ci95[0] and high > member.ci95[1]
        assert entry["correction"] == "bonferroni"


def test_the_level_divides_by_the_family_product_not_the_member_count():
    """`family_size` is `comparisons × metrics`, and it is the *m* both Holm and
    Bonferroni divide α by — not `len(family)`, which on a non-square family is
    smaller. `rmse` is recorded in comparison "1" and absent from comparison
    "2", so 3 members span a family of 2 × 2 = 4: the level is 0.05/4, and
    correcting at 0.05/3 instead would publish every interval in the run
    narrower than the evidence supports, beside a `family_size: 4` saying the
    opposite. The design spec records the same warning in prose ("Recorded here
    so a future reader does not 'fix' it into the member count"); this is what
    stops them."""
    members = [
        _from_diffs("1", mean=-0.169, spread=0.02, metric="r", decl=0),
        _from_diffs("1", mean=-0.150, spread=0.02, metric="rmse", decl=1),
        _from_diffs("2", mean=0.026, spread=0.30, metric="r", decl=2),
    ]
    got = corrected_fields(members, "bonferroni")
    assert len(got) == 3
    for entry in got.values():
        assert entry["family_size"] == 4  # not 3
        assert entry["family"] == {"comparisons": 2, "metrics": 2}
        assert entry["correction_level"] == pytest.approx(0.05 / 4)  # not 0.05 / 3
        assert entry["correction_level"] != pytest.approx(0.05 / 3)


def test_fdr_bh_records_no_interval_and_no_level():
    """`reference.md`: Benjamini-Hochberg "has no interval that means anything of
    the kind — controlling a false discovery *rate* is a statement about a set,
    not a bound on any one comparison — so core reports the adjusted p-value and
    leaves `ci95_corrected` null". No p-value exists in this build, so there is
    no `p_value_corrected` either.

    `thin` must be `False` here even though `bounds` is always `None` under
    `fdr_bh` — there is no `level` to have been too tight for the pool, so
    reporting thin would blame the evidence for a method that never asked for
    an interval in the first place."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "fdr_bh")
    for entry in got.values():
        assert entry["ci95_corrected"] is None
        assert entry["correction_level"] is None
        assert entry["thin"] is False
        assert "p_value_corrected" not in entry


def test_none_produces_no_corrected_fields_at_all():
    """`reference.md`'s table: under `none`, `ci95_corrected` is *absent*. An
    explicit null would claim a correction was attempted."""
    strong, weak = _two_member_family()
    assert corrected_fields([strong, weak], "none") == {}


def test_every_member_carries_the_family_it_was_corrected_against():
    """`family` is "reported broken out rather than as a single integer, so the
    count is auditable instead of asserted"."""
    strong, weak = _two_member_family()
    got = corrected_fields([strong, weak], "holm")
    for entry in got.values():
        assert entry["family_size"] == 2
        assert entry["family"] == {"comparisons": 2, "metrics": 1}


def test_a_derived_member_is_corrected_off_its_own_pool():
    """A derived metric has no per-unit differences, so its corrected interval is
    a second rank pair off the stored draws. Nesting is structural: the same
    pool, read further into both tails.

    Two metrics on the same comparison so the family is size 2 and the level is
    genuinely below α — at family size 1 the level is α itself and
    `interval_at(pool, 0.95)` (the raw call) would be indistinguishable from the
    correct one."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    member = Member(
        where="1",
        step="s",
        metric="r",
        delta=1.0,
        ci95=(0.049, 1.949),
        pool=pool,
        diffs=None,
        declaration_index=0,
    )
    other = Member(
        where="1",
        step="s",
        metric="rmse",
        delta=1.0,
        ci95=(0.049, 1.949),
        pool=pool,
        diffs=None,
        declaration_index=1,
    )
    got = corrected_fields([member, other], "bonferroni")[("1", "s", "r")]
    low, high = got["ci95_corrected"]
    assert low < member.ci95[0] and high > member.ci95[1]


def test_a_pool_too_small_for_the_level_reports_no_interval_and_says_so():
    """A family of 40 implies α/40, whose honest-draw floor is 3201 against a
    2000-draw pool. `ci95_corrected` is null while `correction_level` still
    records what was asked for, and `thin` is what the caller turns into
    `W-STATS-CORRECTED-THIN` — a silent null here would read as "no correction
    applies" rather than "the evidence cannot support this level"."""
    pool = tuple(float(i) / 1000.0 for i in range(2000))
    members = [
        Member(
            where=str(c),
            step="s",
            metric=k,
            delta=1.0,
            ci95=(0.049, 1.949),
            pool=pool,
            diffs=None,
            declaration_index=i,
        )
        for i, (c, k) in enumerate((c, k) for c in range(20) for k in ("r", "rmse"))
    ]
    got = corrected_fields(members, "bonferroni")
    entry = got[("0", "s", "r")]
    assert entry["family_size"] == 40
    assert entry["correction_level"] == pytest.approx(0.05 / 40)
    assert entry["ci95_corrected"] is None
    assert entry["thin"] is True

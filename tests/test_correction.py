from publishable.correction import ALPHA, Member, family_members, family_shape, rank_family


def _m(where="1", step="s", metric="r", delta=0.1, ci95=(0.0, 0.2), index=1):
    return Member(
        where=where,
        condition_index=index,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=None,
        diffs=(0.1, 0.2, 0.3),
    )


def test_alpha_is_five_percent_and_not_configurable():
    """`ci95` is in every record field name, so the raw confidence is fixed and
    only the corrected level varies. A config field for it would have to rename
    the record field."""
    assert ALPHA == 0.05


def test_a_member_with_no_interval_is_not_in_the_family():
    """Counted-iff-corrected: a metric reported without an interval is not a
    comparison a reader can read as significant, so it neither takes a slot nor
    consumes a rank. `cli` passes `ci95=None` for it."""
    with_interval = _m(metric="r")
    without = Member(
        where="1", condition_index=1, step="s", metric="n_units", delta=3.0,
        ci95=None, pool=None, diffs=None,
    )
    assert family_members([with_interval, without]) == [with_interval]


def test_the_family_is_comparisons_times_metrics():
    """`reference.md`: "The family is comparisons × metrics, not comparisons." A
    six-condition sweep is five comparisons, but three metrics per step means a
    reader is shown fifteen intervals."""
    members = [
        _m(where=str(c), index=c, metric=k)
        for c in (1, 2, 3, 4, 5)
        for k in ("r", "rmse", "auc")
    ]
    size, shape = family_shape(family_members(members))
    assert shape == {"comparisons": 5, "metrics": 3}
    assert size == 15


def test_the_worked_example_is_two_comparisons_and_one_metric():
    """`reference.md`'s worked example: 3 conditions give 2 baseline comparisons,
    one metric gives `metrics: 1`, so `family_size: 2`. This is the number the
    acceptance test asserts, pinned here at the arithmetic."""
    members = [_m(where="1", index=1, metric="r"), _m(where="2", index=2, metric="r")]
    size, shape = family_shape(family_members(members))
    assert size == 2
    assert shape == {"comparisons": 2, "metrics": 1}


def test_a_contrast_and_a_baseline_comparison_are_both_comparisons():
    """`reference.md`: "A 'comparison' is a baseline contrast or a declared one" —
    both put an interval in front of a reader. Counting only `vs_baseline`
    under-corrects by exactly the declared contrasts a config asked for."""
    members = [_m(where="1", index=1), _m(where="sensitivity", index=1)]
    size, shape = family_shape(family_members(members))
    assert shape["comparisons"] == 2
    assert size == 2


def test_a_metric_absent_from_one_comparison_still_counts_as_a_metric():
    """The product can exceed the member count. That is the conservative
    direction — a larger family means a smaller α and a wider corrected
    interval — and `reference.md`'s own arithmetic is the product. Pinned so
    nobody "fixes" it into the member count."""
    members = [
        _m(where="1", index=1, metric="r"),
        _m(where="1", index=1, metric="rmse"),
        _m(where="2", index=2, metric="r"),
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
        _m(where="1", index=1, step="step01", metric="r"),
        _m(where="1", index=1, step="step02", metric="r"),
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
    kendall = _m(where="2", index=2, metric="r", delta=-0.169, ci95=(-0.213, -0.125))
    spearman = _m(where="1", index=1, metric="r", delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([spearman, kendall])] == ["2", "1"]


def test_the_ranking_statistic_uses_the_magnitude_not_the_signed_estimate():
    """Kendall's delta is negative and it is the *strongest* member. Ranking on
    the signed estimate puts every negative delta last regardless of its
    evidence, which would silently hand the smallest correction to the members
    that most need it."""
    strong_negative = _m(where="a", index=0, delta=-0.169, ci95=(-0.213, -0.125))
    weak_positive = _m(where="b", index=1, delta=0.026, ci95=(-0.007, 0.059))
    assert [m.where for m in rank_family([weak_positive, strong_negative])] == ["a", "b"]


def test_ties_break_by_condition_index_then_metric_name():
    """`reference.md`: "Ties break by condition index, then by metric name in
    declaration order, so a rank is a function of the record rather than of an
    iteration order." Two members with identical evidence must rank the same way
    whichever order they arrive in."""
    a = _m(where="2", index=2, metric="auc", delta=0.1, ci95=(0.0, 0.2))
    b = _m(where="1", index=1, metric="rmse", delta=0.1, ci95=(0.0, 0.2))
    c = _m(where="1", index=1, metric="auc", delta=0.1, ci95=(0.0, 0.2))
    assert [(m.condition_index, m.metric) for m in rank_family([a, b, c])] == [
        (1, "auc"),
        (1, "rmse"),
        (2, "auc"),
    ]
    assert rank_family([a, b, c]) == rank_family([c, b, a])


def test_a_zero_width_interval_ranks_first_rather_than_dividing_by_zero():
    """A point-mass bootstrap is legitimate (S4b task 5 established it), so a
    half-width of exactly 0.0 is reachable and must not raise. Infinite evidence
    ranks first, which is also what the ratio's limit says."""
    point_mass = _m(where="a", index=0, delta=0.5, ci95=(0.5, 0.5))
    ordinary = _m(where="b", index=1, delta=0.169, ci95=(0.125, 0.213))
    assert [m.where for m in rank_family([ordinary, point_mass])] == ["a", "b"]

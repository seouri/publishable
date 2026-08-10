from publishable.correction import ALPHA, Member, family_members, family_shape


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

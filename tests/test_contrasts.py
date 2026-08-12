import pytest

from publishable.contrasts import resolve_contrasts, units_matching
from publishable.sweep import Condition, expand
from publishable.units import Unit, UnitList


def _cond(i, label, baseline=False):
    return Condition(index=i, label=label, values={}, is_baseline=baseline)


def test_no_baseline_and_no_declared_contrasts_yields_nothing():
    conds = [_cond(0, "method=pearson"), _cond(1, "method=spearman")]
    assert resolve_contrasts({}, conds) == []


def test_each_non_baseline_condition_compares_against_the_baseline():
    conds = [
        _cond(0, "baseline", baseline=True),
        _cond(1, "method=spearman"),
        _cond(2, "method=kendall"),
    ]
    got = resolve_contrasts({}, conds)
    assert [(c.of, c.against) for c in got] == [(1, 0), (2, 0)]
    assert [c.id for c in got] == ["method=spearman", "method=kendall"]


def test_a_declared_contrast_resolves_labels_to_indices():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {
        "statistics": {
            "contrasts": [{"id": "sensitivity", "of": "shift=abnormal", "against": "shift=normal"}]
        }
    }
    got = resolve_contrasts(cfg, conds)
    assert [(c.id, c.of, c.against, c.within) for c in got] == [("sensitivity", 1, 0, None)]


def test_a_declared_contrast_carries_its_within_stratum():
    conds = [_cond(0, "shift=normal"), _cond(1, "shift=abnormal")]
    cfg = {
        "statistics": {
            "contrasts": [
                {
                    "id": "sens_f",
                    "of": "shift=abnormal",
                    "against": "shift=normal",
                    "within": {"sex": "f"},
                }
            ]
        }
    }
    assert resolve_contrasts(cfg, conds)[0].within == {"sex": "f"}


def test_declared_contrasts_come_after_the_baseline_ones():
    """Order is the record's order, and vs_baseline is the documented default."""
    conds = [_cond(0, "baseline", baseline=True), _cond(1, "method=spearman")]
    cfg = {
        "statistics": {
            "contrasts": [{"id": "extra", "of": "method=spearman", "against": "baseline"}]
        }
    }
    assert [c.id for c in resolve_contrasts(cfg, conds)] == ["method=spearman", "extra"]


def test_a_declared_entry_is_marked_declared_even_when_it_looks_generated():
    """The one case no identity test on `id`/`against` can get right: a declared
    entry whose `id` is its own `of` condition's label and whose `against` is
    the baseline is field-for-field identical to the generated comparison, so
    only `declared` separates them. Misfiling it puts it in `vs_baseline`,
    where it overwrites the genuine baseline block and never reaches
    `results.contrasts`."""
    conds = [_cond(0, "baseline", baseline=True), _cond(1, "method=spearman")]
    cfg = {
        "statistics": {
            "contrasts": [
                {
                    "id": "method=spearman",
                    "of": "method=spearman",
                    "against": "baseline",
                    "within": {"sex": "f"},
                }
            ]
        }
    }
    got = resolve_contrasts(cfg, conds)
    assert [(c.id, c.of, c.against, c.declared) for c in got] == [
        ("method=spearman", 1, 0, False),
        ("method=spearman", 1, 0, True),
    ]


def _roster(*specs):
    return UnitList([Unit(key=k, paths=(), attributes=a) for k, a in specs])


def test_no_within_means_no_restriction():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}))
    assert units_matching(r, None) is None


def test_a_single_level_selects_matching_units():
    r = _roster(("u1", {"sex": "f"}), ("u2", {"sex": "m"}), ("u3", {"sex": "f"}))
    assert units_matching(r, {"sex": "f"}) == {"u1", "u3"}


def test_multiple_levels_are_conjunctive():
    r = _roster(("u1", {"sex": "f", "site": "a"}), ("u2", {"sex": "f", "site": "b"}))
    assert units_matching(r, {"sex": "f", "site": "a"}) == {"u1"}


def test_an_empty_stratum_is_an_empty_set_not_none():
    """Empty means nobody matched; None means nobody asked. Downstream reports
    those differently, so they must not collapse."""
    r = _roster(("u1", {"sex": "f"}))
    assert units_matching(r, {"sex": "m"}) == set()


def test_values_compare_as_strings():
    """A config's YAML gives `1` as an int while an attribute read from a CSV is
    `"1"`; comparing them raw would silently match nothing."""
    r = _roster(("u1", {"cohort": "1"}))
    assert units_matching(r, {"cohort": 1}) == {"u1"}


@pytest.mark.xfail(
    strict=True,
    reason="Task 8 owns per-cell `vs_baseline` targeting. `resolve_contrasts` takes the "
    "FIRST baseline for every condition, so a per-cell expansion's other baselines "
    "become comparisons: 6 conditions / 2 baselines gives 5, not the 4 § Expansion "
    "modes states. `correction.family_shape` counts `len({m.where})`, so `family_size` "
    "and every corrected interval in the run rest on that number.",
)
def test_two_per_cell_baselines_are_four_comparisons_not_five():
    """§ Expansion modes, last line of the baseline table's section: "six conditions
    under two per-arm baselines are four comparisons in the correction family, not
    five."

    The tracked handle for the window H2 task 7 opened. Task 6 implemented per-cell
    baseline expansion and `E-SWEEP-BASELINE-PARTIAL` was the only thing keeping any
    config from reaching it; task 7 retired that refusal, which makes a
    multi-baseline run reachable while contrast targeting is still single-baseline.
    Nothing diagnoses the wrong family size, so this is `strict=True` rather than a
    note in a file: it fails loudly the moment task 8 lands and cannot be forgotten
    at merge.

    Built from `expand` rather than hand-written `Condition`s deliberately — the
    count under test is a property of the real expansion, and a hand-built list
    would let the two drift apart."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )
    assert [c.is_baseline for c in conditions] == [True, True, False, False, False, False]

    assert len(resolve_contrasts({}, conditions)) == 4


@pytest.mark.xfail(
    strict=True,
    reason="Same window as above: the first baseline is every condition's target, so "
    "the second baseline is compared against the first and enters the correction "
    "family as a member.",
)
def test_no_comparison_has_a_baseline_condition_as_its_subject():
    """§ Expansion modes: "Baseline conditions are references rather than comparisons,
    so they never count as one."

    The second half of the handle above, and the sharper of the two: the count being
    5 is a family-size error, but a *baseline* appearing as a comparison's `of` is a
    comparison of one reference against another — `sex=m__baseline` vs
    `sex=f__baseline` differs on `data.sex` alone and is exactly the confounded
    cross-cell contrast per-cell baselines exist to avoid."""
    conditions = expand(
        {
            "sweep": {
                "baseline": {"analysis.method": "pearson"},
                "grid": {
                    "analysis.method": ["pearson", "spearman"],
                    "data.sex": ["f", "m"],
                },
            }
        }
    )
    baselines = {c.index for c in conditions if c.is_baseline}

    subjects = [c.id for c in resolve_contrasts({}, conditions) if c.of in baselines]
    assert subjects == []

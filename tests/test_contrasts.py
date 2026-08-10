from publishable.contrasts import resolve_contrasts
from publishable.sweep import Condition


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

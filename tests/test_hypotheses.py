from publishable.hypotheses import Observation, resolve

_VS_BASELINE = {1: {"step03_analyze": {"r": {"delta": 0.026, "ci95": [-0.007, 0.059]}}}}
_CONTRASTS = [
    {"id": "sensitivity", "of": "01_a", "against": "00_b",
     "step03_screen": {"auroc": {"delta": 0.04, "ci95": [0.01, 0.07]}}}
]
_SUMMARY = {
    "step04_agreement": {
        "s_within": {"value": 0.9931, "reported": True, "ci95": [0.9931, 1.0],
                     "n": None, "method": "one-sided BCa"}
    }
}


def _resolve(hyp):
    return resolve(
        hyp,
        label_to_index={"method=spearman": 1},
        vs_baseline=_VS_BASELINE,
        contrasts=_CONTRASTS,
        summary=_SUMMARY,
    )


def test_a_condition_hypothesis_reads_that_conditions_vs_baseline_block():
    """`compare` says where; `metric` says what. The label resolves to a
    condition index because that is how `cli` addresses a Member."""
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.r",
        "compare": {"condition": "method=spearman", "to": "baseline"},
    })
    assert got == Observation(
        where="cond:1", step="step03_analyze", metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]}, rests_on="computed",
    )


def test_a_contrast_hypothesis_reads_that_contrast_entry():
    got = _resolve({
        "id": "s", "metric": "step03_screen.auroc", "compare": {"contrast": "sensitivity"},
    })
    assert got.where == "contrast:sensitivity"
    assert got.block == {"delta": 0.04, "ci95": [0.01, 0.07]}
    assert got.rests_on == "computed"


def test_a_summary_hypothesis_takes_no_compare_and_rests_on_reported():
    """`reference.md`: a summary metric "is one value per run rather than a
    contrast between conditions", so it takes no `compare` — and core did not
    derive it, which is the whole of what `verdict_rests_on` records."""
    got = _resolve({"id": "h2", "metric": "step04_agreement.s_within"})
    assert got.where is None
    assert got.rests_on == "reported"
    assert got.block["value"] == 0.9931


def test_an_unresolvable_metric_yields_no_block_rather_than_raising():
    """A hypothesis may name a metric no run produced — its step failed, or every
    unit was ineligible. The verdict records that rather than a boolean, and a
    pure resolver has no diagnostic to raise into."""
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.nosuch",
        "compare": {"condition": "method=spearman", "to": "baseline"},
    })
    assert got.block is None
    assert got.where == "cond:1"


def test_an_unknown_condition_label_yields_no_block():
    got = _resolve({
        "id": "h1", "metric": "step03_analyze.r",
        "compare": {"condition": "nosuch", "to": "baseline"},
    })
    assert got.block is None

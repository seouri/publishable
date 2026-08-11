from publishable.hypotheses import Observation, resolve, verdict_for

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


_H1 = {
    "id": "h1", "kind": "confirmatory", "metric": "step03_analyze.r",
    "compare": {"condition": "method=spearman", "to": "baseline"},
    "direction": "greater", "threshold": 0.02,
}


def _obs_h1():
    return Observation(
        where="cond:1", step="step03_analyze", metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]}, rests_on="computed",
    )


def test_the_worked_examples_h1_is_supported_on_the_observed_value():
    """`reference.md` § Pre-registration: "The observed delta of 0.026 clears the
    declared threshold of 0.02, so `h1` is supported on `observed`"."""
    got = verdict_for({**_H1, "evaluate_on": "observed"}, _obs_h1(), None)
    assert got["supported"] is True
    assert got["verdict_evaluated_on"] == "observed"
    assert got["verdict_rests_on"] == "computed"


def test_the_same_hypothesis_is_unsupported_on_the_lower_bound():
    """The other half of the same paragraph: "the same delta's interval over 228
    units, [−0.007, 0.059], does not exclude zero, so the same hypothesis written
    `evaluate_on: ci95_lower` would come back `supported: false`. Neither verdict
    is wrong; they answer different questions."

    An implementation ignoring `evaluate_on` passes the test above and fails this
    one, which is why the pair is the sharpest test in the slice."""
    got = verdict_for({**_H1, "evaluate_on": "ci95_lower"}, _obs_h1(), None)
    assert got["supported"] is False
    assert got["verdict_evaluated_on"] == "ci95_lower"


def test_direction_less_inverts_the_comparison():
    """An equivalence claim reads the upper bound: `reference.md` — "a mean
    absolute difference of 0.01 with an interval of [0.001, 0.30] passes
    `direction: less, threshold: 0.05` on the observed value and fails on the
    upper bound — and the second verdict is the correct one"."""
    obs = Observation(
        where="cond:1", step="s", metric="m",
        block={"delta": 0.01, "ci95": [0.001, 0.30]}, rests_on="computed",
    )
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "less", "threshold": 0.05}
    assert verdict_for({**hyp, "evaluate_on": "observed"}, obs, None)["supported"] is True
    assert verdict_for({**hyp, "evaluate_on": "ci95_upper"}, obs, None)["supported"] is False


def test_a_corrected_bound_is_what_a_bound_test_reads_when_one_is_supplied():
    """`reference.md`: a bound test "reads the corrected bound at the level *this*
    family implies". The raw interval would say supported; the corrected one does
    not, and the corrected one is the answer."""
    obs = Observation(
        where="cond:1", step="s", metric="m",
        block={"delta": 0.10, "ci95": [0.01, 0.19]}, rests_on="computed",
    )
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.0, "evaluate_on": "ci95_lower"}
    assert verdict_for(hyp, obs, None)["supported"] is True
    assert verdict_for(hyp, obs, (-0.02, 0.22))["supported"] is False


def test_a_summary_hypothesis_reads_its_value_and_rests_on_reported():
    obs = Observation(
        where=None, step="step04_agreement", metric="s_within",
        block={"value": 0.9931, "reported": True, "ci95": [0.9931, 1.0],
               "n": None, "method": "one-sided BCa"},
        rests_on="reported",
    )
    hyp = {"id": "h2", "metric": "step04_agreement.s_within",
           "direction": "greater", "threshold": 0.99, "evaluate_on": "observed"}
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is True
    assert got["verdict_rests_on"] == "reported"
    assert got["observed"]["method"] == "one-sided BCa"


def test_an_unresolvable_observation_is_supported_null_not_false():
    """A `false` would be indistinguishable from a claim that was tested and
    failed. `reference.md` covers no such case, so this is recorded in
    spec-defects rather than derived from it."""
    obs = Observation(where="cond:1", step="s", metric="m", block=None, rests_on="computed")
    got = verdict_for({"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
                       "direction": "greater", "threshold": 0.0,
                       "evaluate_on": "observed"}, obs, None)
    assert got["supported"] is None
    assert got["observed"] is None


def test_a_bound_test_on_a_metric_with_no_interval_is_supported_null():
    """Asking for a bound a metric does not have is unanswerable, not false."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.5, "ci95": None}, rests_on="computed")
    got = verdict_for({"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
                       "direction": "greater", "threshold": 0.0,
                       "evaluate_on": "ci95_lower"}, obs, None)
    assert got["supported"] is None

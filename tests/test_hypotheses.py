from publishable.correction import Member
from publishable.hypotheses import Observation, evaluate, resolve, verdict_for

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


def test_a_misspelled_direction_is_supported_null_not_a_wrong_verdict():
    """A `direction` outside `{greater, less}` — a typo such as `greatr` — must
    not silently invert the verdict. `direction` is never echoed into the
    record, so a wrong `supported` here would read as clean. `reference.md`
    documents no third value, so this is the same "no answer" as an
    unresolvable observation."""
    got = verdict_for({**_H1, "direction": "greatr", "evaluate_on": "observed"}, _obs_h1(), None)
    assert got["supported"] is None


def test_a_value_exactly_at_the_threshold_is_not_supported():
    """`reference.md` describes a supported hypothesis as one that "exceeds" or
    "clears" the threshold — a strict inequality. A value equal to the
    threshold has done neither, so `>`/`<` and not `>=`/`<=` is the reading
    pinned here."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.02, "ci95": [0.01, 0.03]}, rests_on="computed")
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.02, "evaluate_on": "observed"}
    assert verdict_for(hyp, obs, None)["supported"] is False


def test_a_sweep_ci95_corrected_is_not_relabelled_as_the_hypothesis_familys():
    """A `vs_baseline` entry already carries the sweep family's own
    `ci95_corrected`. Without a `bounds` from Task 5, `observed` must not show
    it — that would misattribute a different family's corrected interval to
    this hypothesis."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.5, "ci95": [0.1, 0.9], "ci95_corrected": [0.05, 0.95]},
                      rests_on="computed")
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.0, "evaluate_on": "observed"}
    got = verdict_for(hyp, obs, None)
    assert "ci95_corrected" not in got["observed"]


def test_observed_carries_exactly_the_named_block_keys():
    """`_observed_block` enumerates `delta`/`value`/`ci95`/`method` rather than
    copying the block, so a field the record entry carries for its own
    purposes — `n`, an unrelated note — does not leak into `observed`."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.5, "ci95": [0.1, 0.9], "n": 10, "note": "x"},
                      rests_on="computed")
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.0}
    got = verdict_for(hyp, obs, None)
    assert set(got["observed"]) == {"delta", "ci95"}


def test_omitting_evaluate_on_defaults_to_observed():
    """`reference.md`: "`direction` and `threshold` are compared to the observed
    value by default." Nothing must fail if that default silently changes."""
    obs = Observation(where="cond:1", step="s", metric="m",
                      block={"delta": 0.5, "ci95": [0.1, 0.9]}, rests_on="computed")
    hyp = {"id": "i", "metric": "s.m", "compare": {"contrast": "x"},
           "direction": "greater", "threshold": 0.0}
    got = verdict_for(hyp, obs, None)
    assert got["verdict_evaluated_on"] == "observed"
    assert got["supported"] is True


def _member(where, step, metric, delta, ci95):
    return Member(where=where, condition_index=1, step=step, metric=metric,
                  delta=delta, ci95=ci95, pool=None,
                  diffs=tuple(delta + 0.01 * ((i % 5) - 2) for i in range(60)))


def test_only_confirmatory_computed_hypotheses_are_counted():
    """`reference.md`: "Core's hypothesis family is the confirmatory hypotheses
    whose observations it computed, which keeps `family_size` predictable from
    the config." An exploratory one is evaluated and recorded, and counted by
    nothing."""
    hyps = [
        {"id": "a", "kind": "confirmatory", "metric": "s.m",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"},
        {"id": "b", "kind": "exploratory", "metric": "s.m",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"},
    ]
    got = evaluate(
        hyps, label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={}, members=[_member("contrast:x", "s", "m", 0.1, (0.01, 0.19))],
        method="holm", parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["a"]["family_size"] == 1
    assert by_id["a"]["family"] == {"hypotheses": 1}
    assert "family_size" not in by_id["b"]
    assert by_id["b"]["supported"] is not None   # still evaluated, just uncounted


def test_a_reported_estimate_hypothesis_is_evaluated_but_never_counted():
    """`reference.md`: its observation "is a reported `Estimate`, so core has
    nothing to correct — and therefore does not count it"."""
    got = evaluate(
        [{"id": "h2", "kind": "confirmatory", "metric": "step04.s",
          "direction": "greater", "threshold": 0.99, "evaluate_on": "observed"}],
        label_to_index={}, vs_baseline=None, contrasts=None,
        summary={"step04": {"s": {"value": 0.9931, "reported": True,
                                  "ci95": [0.9931, 1.0], "n": None, "method": "BCa"}}},
        members=[], method="holm", parameters_hash="sha256:1a2b",
    )
    assert got[0]["verdict_rests_on"] == "reported"
    assert got[0]["supported"] is True
    assert "family_size" not in got[0]


def test_every_verdict_carries_the_hash_that_declared_it():
    """`reference.md`: a hypothesis "carries the `parameters_hash` of the config
    that declared it. Add a hypothesis after seeing results and rerun, and the
    hash won't match the earlier run"."""
    got = evaluate(
        [{"id": "a", "kind": "confirmatory", "metric": "s.m", "compare": {"contrast": "x"},
          "direction": "greater", "threshold": 0.0, "evaluate_on": "observed"}],
        label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={}, members=[], method="none", parameters_hash="sha256:1a2b",
    )
    assert got[0]["declared_in"] == "parameters_hash sha256:1a2b"


def test_the_hypothesis_family_is_its_own_size_not_the_sweeps():
    """Two confirmatory computed hypotheses over a sweep whose own family is
    larger. The level must come from 2, not from the sweep's count — the two
    families are corrected separately, which is the whole reason `family_size`
    is on the verdict at all."""
    hyps = [
        {"id": f"h{i}", "kind": "confirmatory", "metric": f"s.m{i}",
         "compare": {"contrast": "x"}, "direction": "greater", "threshold": 0.0,
         "evaluate_on": "ci95_lower"}
        for i in (1, 2)
    ]
    got = evaluate(
        hyps, label_to_index={}, vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m1": {"delta": 0.10, "ci95": [0.01, 0.19]},
                                     "m2": {"delta": 0.20, "ci95": [0.11, 0.29]}}}],
        summary={},
        members=[_member("contrast:x", "s", "m1", 0.10, (0.01, 0.19)),
                 _member("contrast:x", "s", "m2", 0.20, (0.11, 0.29))],
        method="bonferroni", parameters_hash="sha256:1a2b",
    )
    assert {e["family_size"] for e in got} == {2}

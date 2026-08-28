from publishable.correction import Member
from publishable.hypotheses import Observation, evaluate, resolve, verdict_for

_VS_BASELINE = {1: {"step03_analyze": {"r": {"delta": 0.026, "ci95": [-0.007, 0.059]}}}}
# Two entries, not one, and both carrying the same step metric with different
# numbers: with a single entry, ignoring `compare.contrast` entirely (`if True`
# in place of the id test) passed the whole suite, and the consequence would be
# invisible in `run.yaml` — an `observed` block carries no identifier for which
# contrast it came from, so a verdict about `invariance` reported against
# `sensitivity`'s numbers reads as a real answer.
_CONTRASTS = [
    {
        "id": "sensitivity",
        "of": "01_a",
        "against": "00_b",
        "step03_screen": {"auroc": {"delta": 0.04, "ci95": [0.01, 0.07]}},
    },
    {
        "id": "invariance",
        "of": "02_c",
        "against": "00_b",
        "step03_screen": {"auroc": {"delta": -0.11, "ci95": [-0.19, -0.03]}},
    },
]
_SUMMARY = {
    "step04_agreement": {
        "s_within": {
            "value": 0.9931,
            "reported": True,
            "ci95": [0.9931, 1.0],
            "n": None,
            "method": "one-sided BCa",
        }
    }
}


_AGGREGATED = {
    0: {"step03_screen": {"auroc": {"value": 0.62, "ci95": [0.55, 0.69]}}},
    1: {"step03_analyze": {"r": {"value": 0.44, "ci95": [0.35, 0.53]}}},
}


def _resolve(hyp, aggregated=_AGGREGATED):
    return resolve(
        hyp,
        label_to_index={"method=spearman": 1},
        vs_baseline=_VS_BASELINE,
        contrasts=_CONTRASTS,
        summary=_SUMMARY,
        aggregated=aggregated,
    )


def test_a_condition_hypothesis_reads_that_conditions_vs_baseline_block():
    """`compare` says where; `metric` says what. The label resolves to a
    condition index because that is how `cli` addresses a Member."""
    got = _resolve(
        {
            "id": "h1",
            "metric": "step03_analyze.r",
            "compare": {"condition": "method=spearman", "to": "baseline"},
        }
    )
    assert got == Observation(
        where="cond:1",
        step="step03_analyze",
        metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]},
        rests_on="computed",
    )


def test_a_contrast_hypothesis_reads_that_contrast_entry():
    got = _resolve(
        {
            "id": "s",
            "metric": "step03_screen.auroc",
            "compare": {"contrast": "sensitivity"},
        }
    )
    assert got.where == "contrast:sensitivity"
    assert got.block == {"delta": 0.04, "ci95": [0.01, 0.07]}
    assert got.rests_on == "computed"


def test_a_contrast_hypothesis_reads_the_entry_it_names_not_the_first():
    """The id is resolved, not assumed. Both declared contrasts report the same
    step metric, so a resolver returning `contrasts[0]` regardless answers a
    hypothesis about `invariance` with `sensitivity`'s delta — and the record
    would not say so, because `observed` carries no contrast identifier."""
    got = _resolve(
        {
            "id": "inv",
            "metric": "step03_screen.auroc",
            "compare": {"contrast": "invariance"},
        }
    )
    assert got.where == "contrast:invariance"
    assert got.block == {"delta": -0.11, "ci95": [-0.19, -0.03]}


def test_a_plain_scalar_summary_return_is_no_block_rather_than_a_crash():
    """The Critical's second door, checked rather than assumed. A `summary` step
    returning a bare `{"adjusted": "high"}` — no `Estimate` — never reaches
    `_coerce_estimate`, and `_coerce_one` accepts a `str` scalar happily. It is
    `resolve`'s `isinstance(block, dict)` guard that closes it: `summary_values`
    leaves a non-`Estimate` return exactly as it came back, so the metric is a
    string where a block belongs, `block` is `None`, and the verdict is an
    honest `supported: null` rather than a `ValueError` in phase 8."""
    got = resolve(
        {"id": "h", "metric": "step04_agreement.bare"},
        label_to_index={},
        vs_baseline=None,
        contrasts=None,
        summary={"step04_agreement": {"bare": "high"}},
        aggregated=None,
    )
    assert got.block is None
    assert (
        verdict_for({"id": "h", "direction": "greater", "threshold": 0.02}, got, None)["supported"]
        is None
    )


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
    got = _resolve(
        {
            "id": "h1",
            "metric": "step03_analyze.nosuch",
            "compare": {"condition": "method=spearman", "to": "baseline"},
        }
    )
    assert got.block is None
    assert got.where == "cond:1"


def test_an_unknown_condition_label_yields_no_block():
    got = _resolve(
        {
            "id": "h1",
            "metric": "step03_analyze.r",
            "compare": {"condition": "nosuch", "to": "baseline"},
        }
    )
    assert got.block is None


_H1 = {
    "id": "h1",
    "kind": "confirmatory",
    "metric": "step03_analyze.r",
    "compare": {"condition": "method=spearman", "to": "baseline"},
    "direction": "greater",
    "threshold": 0.02,
}


def _obs_h1():
    return Observation(
        where="cond:1",
        step="step03_analyze",
        metric="r",
        block={"delta": 0.026, "ci95": [-0.007, 0.059]},
        rests_on="computed",
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
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.01, "ci95": [0.001, 0.30]},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "less",
        "threshold": 0.05,
    }
    assert verdict_for({**hyp, "evaluate_on": "observed"}, obs, None)["supported"] is True
    assert verdict_for({**hyp, "evaluate_on": "ci95_upper"}, obs, None)["supported"] is False


def test_a_corrected_bound_is_what_a_bound_test_reads_when_one_is_supplied():
    """`reference.md`: a bound test "reads the corrected bound at the level *this*
    family implies". The raw interval would say supported; the corrected one does
    not, and the corrected one is the answer."""
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.10, "ci95": [0.01, 0.19]},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "ci95_lower",
    }
    assert verdict_for(hyp, obs, None)["supported"] is True
    assert verdict_for(hyp, obs, (-0.02, 0.22))["supported"] is False


def test_a_summary_hypothesis_reads_its_value_and_rests_on_reported():
    obs = Observation(
        where=None,
        step="step04_agreement",
        metric="s_within",
        block={
            "value": 0.9931,
            "reported": True,
            "ci95": [0.9931, 1.0],
            "n": None,
            "method": "one-sided BCa",
        },
        rests_on="reported",
    )
    hyp = {
        "id": "h2",
        "metric": "step04_agreement.s_within",
        "direction": "greater",
        "threshold": 0.99,
        "evaluate_on": "observed",
    }
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is True
    assert got["verdict_rests_on"] == "reported"
    assert got["observed"]["method"] == "one-sided BCa"


def test_an_unresolvable_observation_is_supported_null_not_false():
    """A `false` would be indistinguishable from a claim that was tested and
    failed. `reference.md` covers no such case, so this is recorded in
    spec-defects rather than derived from it."""
    obs = Observation(where="cond:1", step="s", metric="m", block=None, rests_on="computed")
    got = verdict_for(
        {
            "id": "i",
            "metric": "s.m",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "observed",
        },
        obs,
        None,
    )
    assert got["supported"] is None
    assert got["observed"] is None


def test_a_bound_test_on_a_metric_with_no_interval_is_supported_null():
    """Asking for a bound a metric does not have is unanswerable, not false."""
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.5, "ci95": None},
        rests_on="computed",
    )
    got = verdict_for(
        {
            "id": "i",
            "metric": "s.m",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        },
        obs,
        None,
    )
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
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.02, "ci95": [0.01, 0.03]},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.02,
        "evaluate_on": "observed",
    }
    assert verdict_for(hyp, obs, None)["supported"] is False


def test_a_sweep_ci95_corrected_is_not_relabelled_as_the_hypothesis_familys():
    """A `vs_baseline` entry already carries the sweep family's own
    `ci95_corrected`. Without a `bounds` from Task 5, `observed` must not show
    it — that would misattribute a different family's corrected interval to
    this hypothesis."""
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.5, "ci95": [0.1, 0.9], "ci95_corrected": [0.05, 0.95]},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "observed",
    }
    got = verdict_for(hyp, obs, None)
    assert "ci95_corrected" not in got["observed"]


def test_observed_carries_exactly_the_named_block_keys():
    """`_observed_block` enumerates `delta`/`value`/`ci95`/`method` rather than
    copying the block, so a field the record entry carries for its own
    purposes — `n`, an unrelated note — does not leak into `observed`."""
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.5, "ci95": [0.1, 0.9], "n": 10, "note": "x"},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.0,
    }
    got = verdict_for(hyp, obs, None)
    assert set(got["observed"]) == {"delta", "ci95"}


def test_omitting_evaluate_on_defaults_to_observed():
    """`reference.md`: "`direction` and `threshold` are compared to the observed
    value by default." Nothing must fail if that default silently changes."""
    obs = Observation(
        where="cond:1",
        step="s",
        metric="m",
        block={"delta": 0.5, "ci95": [0.1, 0.9]},
        rests_on="computed",
    )
    hyp = {
        "id": "i",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.0,
    }
    got = verdict_for(hyp, obs, None)
    assert got["verdict_evaluated_on"] == "observed"
    assert got["supported"] is True


def _member(where, step, metric, delta, ci95, decl=0):
    return Member(
        where=where,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=None,
        diffs=tuple(delta + 0.01 * ((i % 5) - 2) for i in range(60)),
        declaration_index=decl,
    )


def test_only_confirmatory_computed_hypotheses_are_counted():
    """`reference.md`: "Core's hypothesis family is the confirmatory hypotheses
    whose observations it computed, which keeps `family_size` predictable from
    the config." An exploratory one is evaluated and recorded, and counted by
    nothing."""
    hyps = [
        {
            "id": "a",
            "kind": "confirmatory",
            "metric": "s.m",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        },
        {
            "id": "b",
            "kind": "exploratory",
            "metric": "s.m",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        },
    ]
    got = evaluate(
        hyps,
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={},
        aggregated=None,
        members=[_member("contrast:x", "s", "m", 0.1, (0.01, 0.19))],
        method="holm",
        parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["a"]["family_size"] == 1
    assert by_id["a"]["family"] == {"hypotheses": 1}
    assert "family_size" not in by_id["b"]
    assert by_id["b"]["supported"] is not None  # still evaluated, just uncounted


def test_a_reported_estimate_hypothesis_is_evaluated_but_never_counted():
    """`reference.md`: its observation "is a reported `Estimate`, so core has
    nothing to correct — and therefore does not count it"."""
    got = evaluate(
        [
            {
                "id": "h2",
                "kind": "confirmatory",
                "metric": "step04.s",
                "direction": "greater",
                "threshold": 0.99,
                "evaluate_on": "observed",
            }
        ],
        label_to_index={},
        vs_baseline=None,
        contrasts=None,
        summary={
            "step04": {
                "s": {
                    "value": 0.9931,
                    "reported": True,
                    "ci95": [0.9931, 1.0],
                    "n": None,
                    "method": "BCa",
                }
            }
        },
        aggregated=None,
        members=[],
        method="holm",
        parameters_hash="sha256:1a2b",
    )
    assert got[0]["verdict_rests_on"] == "reported"
    assert got[0]["supported"] is True
    assert "family_size" not in got[0]


def test_every_verdict_carries_the_hash_that_declared_it():
    """`reference.md`: a hypothesis "carries the `parameters_hash` of the config
    that declared it. Add a hypothesis after seeing results and rerun, and the
    hash won't match the earlier run"."""
    got = evaluate(
        [
            {
                "id": "a",
                "kind": "confirmatory",
                "metric": "s.m",
                "compare": {"contrast": "x"},
                "direction": "greater",
                "threshold": 0.0,
                "evaluate_on": "observed",
            }
        ],
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={},
        aggregated=None,
        members=[],
        method="none",
        parameters_hash="sha256:1a2b",
    )
    assert got[0]["declared_in"] == "parameters_hash sha256:1a2b"


def test_the_hypothesis_family_is_its_own_size_not_the_sweeps():
    """Two confirmatory computed hypotheses over a sweep whose own family is
    larger. The level must come from 2, not from the sweep's count — the two
    families are corrected separately, which is the whole reason `family_size`
    is on the verdict at all.

    `members` carries a *third* member, `m3`, that no hypothesis names — the
    shape `cli` actually hands `evaluate` in Task 8, where the sweep's full
    `Member` list is passed through unfiltered. `family_size` must come from
    the two counted hypotheses, not from `len(members) == 3`."""
    hyps = [
        {
            "id": f"h{i}",
            "kind": "confirmatory",
            "metric": f"s.m{i}",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        }
        for i in (1, 2)
    ]
    got = evaluate(
        hyps,
        label_to_index={},
        vs_baseline=None,
        contrasts=[
            {
                "id": "x",
                "s": {
                    "m1": {"delta": 0.10, "ci95": [0.01, 0.19]},
                    "m2": {"delta": 0.20, "ci95": [0.11, 0.29]},
                },
            }
        ],
        summary={},
        aggregated=None,
        members=[
            _member("contrast:x", "s", "m1", 0.10, (0.01, 0.19), decl=0),
            _member("contrast:x", "s", "m2", 0.20, (0.11, 0.29), decl=1),
            _member("contrast:x", "s", "m3", 0.30, (0.21, 0.39), decl=2),
        ],
        method="bonferroni",
        parameters_hash="sha256:1a2b",
    )
    assert {e["family_size"] for e in got} == {2}


def test_p_value_corrected_is_computed_at_the_hypothesis_familys_own_size():
    """Bonferroni's `p_value_corrected` is `min(1, p * m)`. `members` carries
    three p-only entries — the shape `cli` hands `evaluate`, its full sweep
    family unfiltered — but only two are named by a confirmatory hypothesis, so
    the hypothesis family's own `size` is 2. `0.05 * 2 = 0.1` is what the
    counted family gives; `0.05 * 3` (the sweep's own three-member count) would
    be 0.15. The two must differ for the fixture to tell them apart, and they
    do."""
    hyps = [
        {
            "id": f"h{i}",
            "kind": "confirmatory",
            "metric": f"s.m{i}",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "observed",
        }
        for i in (1, 2)
    ]

    def _p_member(metric, p_value, decl):
        return Member(
            where="contrast:x",
            step="s",
            metric=metric,
            delta=0.10,
            ci95=None,
            pool=None,
            diffs=None,
            declaration_index=decl,
            p_value=p_value,
        )

    got = evaluate(
        hyps,
        label_to_index={},
        vs_baseline=None,
        contrasts=[
            {
                "id": "x",
                "s": {
                    "m1": {"delta": 0.10, "p_value": 0.05},
                    "m2": {"delta": 0.10, "p_value": 0.05},
                },
            }
        ],
        summary={},
        aggregated=None,
        members=[
            _p_member("m1", 0.05, 0),
            _p_member("m2", 0.05, 1),
            _p_member("m3", 0.05, 2),
        ],
        method="bonferroni",
        parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["h1"]["family_size"] == 2
    assert by_id["h1"]["observed"]["p_value_corrected"] == 0.1
    assert by_id["h2"]["observed"]["p_value_corrected"] == 0.1


def test_an_unresolvable_confirmatory_hypothesis_is_not_counted():
    """A confirmatory hypothesis naming a metric no run produced (`m1` is
    correct; `nosuch` matches no member) rests on `computed` — its `compare`
    names a contrast — but has no `block`, so it must not inflate the family
    or tighten the resolvable hypothesis's corrected bound. It is still
    evaluated: `supported` reads `None` rather than being counted."""
    hyps = [
        {
            "id": "resolves",
            "kind": "confirmatory",
            "metric": "s.m1",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        },
        {
            "id": "missing",
            "kind": "confirmatory",
            "metric": "s.nosuch",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "ci95_lower",
        },
    ]
    got = evaluate(
        hyps,
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m1": {"delta": 0.10, "ci95": [0.01, 0.19]}}}],
        summary={},
        aggregated=None,
        members=[_member("contrast:x", "s", "m1", 0.10, (0.01, 0.19))],
        method="bonferroni",
        parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["resolves"]["family_size"] == 1
    assert "family_size" not in by_id["missing"]
    assert by_id["missing"]["supported"] is None


def test_a_counted_hypothesis_with_no_matching_member_still_gets_a_verdict():
    """`members` is the caller's own bookkeeping and may not carry an entry for
    every counted, computed hypothesis (a bookkeeping mismatch between how
    `cli` built `members` and what a hypothesis names). The hypothesis is still
    judged, on its raw bound rather than a corrected one it has no evidence to
    rebuild."""
    hyp = {
        "id": "orphan",
        "kind": "confirmatory",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "ci95_lower",
    }
    got = evaluate(
        [hyp],
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.10, "ci95": [0.01, 0.19]}}}],
        summary={},
        aggregated=None,
        members=[],
        method="bonferroni",
        parameters_hash="sha256:1a2b",
    )
    assert got[0]["family_size"] == 1
    assert got[0]["supported"] is True
    assert "ci95_corrected" not in (got[0]["observed"] or {})


def _thin_member(where, step, metric, delta, ci95):
    """A member whose corrected bound cannot be built: a 60-draw pool, where
    `stats.min_honest_draws(0.95)` is 80. Every level a correction asks for is
    at or below α, so `interval_at` returns `None` and `corrected_for` marks it
    `thin` — the real path is a family large enough that α/m outruns the 2000
    draws `cli` resamples with, which needs 26 hypotheses to reach and is
    covered end to end in `test_cli.py`."""
    return Member(
        where=where,
        step=step,
        metric=metric,
        delta=delta,
        ci95=ci95,
        pool=tuple(sorted(delta + 0.001 * i for i in range(60))),
        diffs=None,
        declaration_index=0,
    )


_THIN_CONTRASTS = [{"id": "x", "s": {"m": {"delta": 0.10, "ci95": [0.01, 0.19]}}}]


def _thin_verdict(evaluate_on, method="holm", threshold=0.0):
    hyp = {
        "id": "h",
        "kind": "confirmatory",
        "metric": "s.m",
        "compare": {"contrast": "x"},
        "direction": "greater",
        "threshold": threshold,
        "evaluate_on": evaluate_on,
    }
    return evaluate(
        [hyp],
        label_to_index={},
        vs_baseline=None,
        contrasts=_THIN_CONTRASTS,
        summary={},
        aggregated=None,
        members=[_thin_member("contrast:x", "s", "m", 0.10, (0.01, 0.19))],
        method=method,
        parameters_hash="sha256:1a2b",
    )[0]


def test_a_bound_the_correction_could_not_build_is_supported_null():
    """The error direction is what makes this a refusal rather than a fallback:
    the raw bound is the *tighter* of the two, so testing it answers a question
    nobody asked and answers it favourably. `reference.md` — "Correction reaches
    a verdict only through a bound" — makes the corrected bound the subject of
    the claim, so when it cannot be built there is no verdict, not a substitute
    one."""
    got = _thin_verdict("ci95_lower")
    assert got["family_size"] == 1
    assert got["verdict_evaluated_on"] == "ci95_lower"
    assert got["supported"] is None
    # Null, not absent: absent means no correction was attempted at all, which
    # is a different fact and the one `correction: none` records.
    assert "ci95_corrected" in got["observed"]
    assert got["observed"]["ci95_corrected"] is None
    # The raw interval stays on the record — the number exists, it is the
    # verdict at this level that does not.
    assert got["observed"]["ci95"] == [0.01, 0.19]


def test_an_unbuildable_bound_does_not_disturb_an_observed_verdict():
    """A point estimate has no α to adjust, so a thin family changes nothing
    about what `evaluate_on: observed` compares. `ci95_corrected: null` is still
    disclosed beside it, because the family was still corrected and still could
    not produce the interval."""
    got = _thin_verdict("observed")
    assert got["supported"] is True  # delta 0.10 > 0.0
    assert got["observed"]["ci95_corrected"] is None


def test_an_fdr_bh_family_gives_a_bound_hypothesis_no_verdict():
    """`fdr_bh` implies no per-comparison level at all (`correction._level_for`
    returns `None`), so there is no corrected bound to test — the same absence
    as a thin family, reached by a different route, and the same refusal to
    fall back to the raw bound. `reference.md` already warns that `fdr_bh` over
    a family carrying no p-value is the wrong tool; silently answering on the
    uncorrected bound would hide that rather than surface it."""
    got = _thin_verdict("ci95_upper", method="fdr_bh")
    assert got["supported"] is None
    assert got["observed"]["ci95_corrected"] is None


def test_no_correction_at_all_still_tests_the_raw_bound():
    """The third state, and the one that must not be swept up by the fix above:
    `correction: none` produces no family entry at all, which is a *request*
    that the raw bound be the one tested. `reference.md` makes `ci95_corrected`
    absent there rather than null, and the verdict is a real one."""
    got = _thin_verdict("ci95_lower", method="none")
    assert got["supported"] is True  # raw lower bound 0.01 > 0.0
    assert "ci95_corrected" not in got["observed"]


def test_a_counted_hypothesis_on_a_p_only_member_records_an_unavailable_corrected_bound():
    """The one thing decision 4's widening moves on the hypothesis side, sized
    honestly: `observed.ci95_corrected` goes from absent to `null`, which says the
    level was demanded and the bound could not be built. `supported` does not move
    — a bound test had no raw interval to read either — and `family_size` does not
    move, being `len(counted)`."""
    hyp = {
        "id": "h",
        "kind": "confirmatory",
        "metric": "s.m",
        "compare": {"contrast": "y"},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "observed",
    }
    p_only_member = Member(
        where="contrast:y",
        step="s",
        metric="m",
        delta=0.10,
        ci95=None,
        pool=None,
        diffs=None,
        declaration_index=0,
        p_value=0.05,
    )
    got = evaluate(
        [hyp],
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "y", "s": {"m": {"delta": 0.10}}}],
        summary={},
        aggregated=None,
        members=[p_only_member],
        method="holm",
        parameters_hash="sha256:1a2b",
    )[0]
    assert got["family_size"] == 1
    assert got["observed"]["ci95_corrected"] is None
    assert got["supported"] is True


# ---- `compare: {to: constant, value: N}` — Task 9 ----------------------------

_CONST_AGGREGATED = {
    0: {"step03_screen": {"auroc": {"value": 0.62, "ci95": [0.55, 0.69]}}},
    1: {"step03_screen": {"auroc": {"value": 0.58, "ci95": [0.50, 0.66]}}},
}


def _resolve_const(hyp, aggregated=_CONST_AGGREGATED):
    return resolve(
        hyp,
        label_to_index={"arm=b": 1},
        vs_baseline=None,
        contrasts=None,
        summary=None,
        aggregated=aggregated,
    )


def test_a_constant_hypothesis_with_one_condition_reads_its_sole_block():
    """No `condition` named, and the run declares exactly one condition — the
    only case where omitting `condition` resolves to something, on the same
    reasoning `E-HYPOTHESIS-BASELINE` gives for refusing a silent default
    elsewhere: with more than one condition, a bare `{to: constant}` has no way
    to say which one is meant."""
    got = _resolve_const(
        {"id": "h", "metric": "step03_screen.auroc", "compare": {"to": "constant", "value": 0.5}},
        aggregated={0: _CONST_AGGREGATED[0]},
    )
    assert got == Observation(
        where="const:0",
        step="step03_screen",
        metric="auroc",
        block={"value": 0.62, "ci95": [0.55, 0.69]},
        rests_on="computed",
    )


def test_a_constant_hypothesis_with_several_conditions_and_no_condition_named_has_no_block():
    """Ambiguous rather than guessed: `label_to_index` has two entries here, so
    a bare `{to: constant}` would otherwise have to pick one silently. It picks
    none, and the verdict reads `supported: null` rather than a number nobody
    can trace to a declared condition."""
    got = _resolve_const(
        {"id": "h", "metric": "step03_screen.auroc", "compare": {"to": "constant", "value": 0.5}}
    )
    assert got.block is None
    assert got.where is None
    assert got.rests_on == "computed"


def test_a_constant_hypothesis_can_still_name_its_condition():
    """`condition` travels with `to: constant` exactly as it does with `to:
    baseline` — resolved by the same `label_to_index`, just against `aggregated`
    rather than `vs_baseline`."""
    got = _resolve_const(
        {
            "id": "h",
            "metric": "step03_screen.auroc",
            "compare": {"condition": "arm=b", "to": "constant", "value": 0.5},
        }
    )
    assert got.where == "const:1"
    assert got.block == {"value": 0.58, "ci95": [0.50, 0.66]}
    assert got.rests_on == "computed"


def test_a_constant_hypothesis_where_clashes_with_no_vs_baseline_member():
    """`where` is prefixed `const:`, distinct from `cond:` — the same condition
    index can carry both a `vs_baseline` delta and a constant-referenced
    hypothesis on the metric's own value, and `evaluate`'s `by_key` must never
    confuse the two. A mutation that resolved this form to `cond:{index}`
    instead would pass every other test in this file and only show up here,
    against a family that also has a `cond:1` member for the same step/metric."""
    got = _resolve_const(
        {
            "id": "h",
            "metric": "step03_screen.auroc",
            "compare": {"condition": "arm=b", "to": "constant", "value": 0.5},
        }
    )
    assert got.where != "cond:1"
    assert got.where == "const:1"


def test_auroc_exceeds_chance_is_supported_true():
    """The design's own example: "AUROC exceeds chance" is `value: 0.5,
    threshold: 0.0, direction: greater` against an observed AUROC of 0.62 —
    0.62 - 0.5 = 0.12 > 0.0."""
    obs = Observation(
        where="const:0",
        step="step03_screen",
        metric="auroc",
        block={"value": 0.62, "ci95": [0.55, 0.69]},
        rests_on="computed",
    )
    hyp = {
        "id": "above_chance",
        "kind": "confirmatory",
        "metric": "step03_screen.auroc",
        "compare": {"to": "constant", "value": 0.5},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "observed",
    }
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is True
    assert got["verdict_rests_on"] == "computed"
    assert got["observed"]["value"] == 0.62  # the real value, not the shifted one


def test_auroc_below_chance_is_supported_false_same_constant():
    """Same constant, an observation on the other side of it — the pair proves
    `value` actually enters the arithmetic rather than being a documented,
    unread field: with `value` ignored, both this test and the one above would
    read the same raw threshold comparison and could not disagree."""
    obs = Observation(
        where="const:0",
        step="step03_screen",
        metric="auroc",
        block={"value": 0.44, "ci95": [0.37, 0.51]},
        rests_on="computed",
    )
    hyp = {
        "id": "above_chance",
        "kind": "confirmatory",
        "metric": "step03_screen.auroc",
        "compare": {"to": "constant", "value": 0.5},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "observed",
    }
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is False


def test_a_constant_hypothesis_on_ci95_lower_is_superiority():
    """`evaluate_on: ci95_lower` against a constant is the superiority form:
    the whole interval must clear the reference, not just the point estimate.
    0.55 - 0.5 = 0.05 > 0.0."""
    obs = Observation(
        where="const:0",
        step="step03_screen",
        metric="auroc",
        block={"value": 0.62, "ci95": [0.55, 0.69]},
        rests_on="computed",
    )
    hyp = {
        "id": "h",
        "metric": "step03_screen.auroc",
        "compare": {"to": "constant", "value": 0.5},
        "direction": "greater",
        "threshold": 0.0,
        "evaluate_on": "ci95_lower",
    }
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is True
    assert got["verdict_evaluated_on"] == "ci95_lower"


def test_a_constant_hypothesis_on_ci95_upper_is_non_inferiority():
    """`evaluate_on: ci95_upper` with `direction: less` is the non-inferiority
    form against a constant: 0.69 - 0.5 = 0.19, which is NOT less than the
    0.05 threshold, so this fails — the upper bound is too far from the
    reference for the equivalence claim, and `evaluate_on: observed` on the
    same block (0.62 - 0.5 = 0.12, also not less than 0.05) would agree, but
    the point is that this reads the bound `evaluate_on` names, not the point
    estimate."""
    obs = Observation(
        where="const:0",
        step="step03_screen",
        metric="auroc",
        block={"value": 0.62, "ci95": [0.55, 0.69]},
        rests_on="computed",
    )
    hyp = {
        "id": "h",
        "metric": "step03_screen.auroc",
        "compare": {"to": "constant", "value": 0.5},
        "direction": "less",
        "threshold": 0.05,
        "evaluate_on": "ci95_upper",
    }
    got = verdict_for(hyp, obs, None)
    assert got["supported"] is False
    assert got["verdict_evaluated_on"] == "ci95_upper"


def test_a_constant_hypothesis_joins_the_family_and_grows_its_size():
    """The whole gain per Decision 2: `verdict_rests_on: computed` and the
    entry carries `family_size`/`family`, exactly like a baseline or contrast
    hypothesis — unlike the `reported` route it replaces, which carries
    neither."""
    hyps = [
        {
            "id": "a",
            "kind": "confirmatory",
            "metric": "s.m",
            "compare": {"contrast": "x"},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "observed",
        },
        {
            "id": "b",
            "kind": "confirmatory",
            "metric": "step03_screen.auroc",
            "compare": {"to": "constant", "value": 0.5},
            "direction": "greater",
            "threshold": 0.0,
            "evaluate_on": "observed",
        },
    ]
    got = evaluate(
        hyps,
        label_to_index={},
        vs_baseline=None,
        contrasts=[{"id": "x", "s": {"m": {"delta": 0.1, "ci95": [0.01, 0.19]}}}],
        summary={},
        aggregated={0: {"step03_screen": {"auroc": {"value": 0.62, "ci95": [0.55, 0.69]}}}},
        members=[_member("contrast:x", "s", "m", 0.1, (0.01, 0.19))],
        method="holm",
        parameters_hash="sha256:1a2b",
    )
    by_id = {e["id"]: e for e in got}
    assert by_id["b"]["family_size"] == 2
    assert by_id["b"]["family"] == {"hypotheses": 2}
    assert by_id["b"]["verdict_rests_on"] == "computed"
    assert by_id["b"]["supported"] is True
    assert by_id["a"]["family_size"] == 2

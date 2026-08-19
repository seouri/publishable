"""H7d Part A: `Apparatus` and probe dispatch. See `docs/reference.md`
§ The apparatus core can only observe and § Creating a plugin.
"""

import pytest


def test_apparatus_is_importable_from_the_one_root_and_is_frozen():
    from publishable import Apparatus

    a = Apparatus(facts={"model_revision": "r1"})
    assert a.facts == {"model_revision": "r1"}
    with pytest.raises(Exception):  # noqa: B017 — frozen dataclass raises FrozenInstanceError
        a.facts = {}


def test_apparatus_accepts_a_shape_core_will_later_refuse():
    """The contract is enforced at core's boundary, not in `__init__` — a raise
    inside a probe's own body cannot be told from any other probe raise, and
    would be reported under a code whose row describes a different fault. This
    test is what stops a later task from "fixing" that by validating here."""
    from publishable import Apparatus

    assert Apparatus(facts={"nested": {"a": 1}}).facts["nested"] == {"a": 1}


def test_a_registered_probe_name_resolves_to_the_decorated_function(
    installed, registries, tmp_path
):
    """Positive control: without it, the two refusals below pass identically if
    nothing resolves at all."""
    import importlib
    import sys

    from publishable.apparatus import _probe_for

    site = installed(
        "dist-one", "1.0", {"publishable.probes": {"llm_deployment": "loadable_p24:probe"}}
    )
    (site / "loadable_p24.py").write_text(
        "from publishable import Apparatus, register_probe\n\n\n"
        '@register_probe("llm_deployment")\n'
        "def probe(cfg):\n    return Apparatus(facts={'model_revision': 'r1'})\n"
    )
    importlib.invalidate_caches()
    try:
        assert _probe_for("llm_deployment")(None).facts == {"model_revision": "r1"}
    finally:
        sys.modules.pop("loadable_p24", None)


def test_a_probe_name_no_distribution_registers_is_E_PROBE_UNKNOWN(installed, registries, tmp_path):
    """Answered from metadata alone: assert the message names the group's other
    registered member, which is what says the scan ran rather than an empty
    dict being consulted."""
    from publishable.apparatus import _probe_for
    from publishable.errors import ContractError

    installed("dist-one", "1.0", {"publishable.probes": {"llm_deployment": "no_one:probe"}})
    with pytest.raises(ContractError) as excinfo:
        _probe_for("llm_deploymemt")
    assert excinfo.value.code == "E-PROBE-UNKNOWN"
    assert "llm_deploymemt" in str(excinfo.value)
    assert "llm_deployment" in str(excinfo.value)


def test_a_probe_whose_module_declares_a_different_name_is_E_PLUGIN_DECORATOR(
    installed, registries, tmp_path
):
    """The entry-point key and the `@register_probe` argument disagree — the
    check that makes `validate`'s metadata answer and the registry agree."""
    import importlib
    import sys

    from publishable.apparatus import _probe_for
    from publishable.errors import ContractError

    site = installed(
        "dist-one", "1.0", {"publishable.probes": {"llm_deployment": "misnamed_p24:probe"}}
    )
    (site / "misnamed_p24.py").write_text(
        "from publishable import Apparatus, register_probe\n\n\n"
        '@register_probe("llm_screen")\n'
        "def probe(cfg):\n    return Apparatus(facts={})\n"
    )
    importlib.invalidate_caches()
    try:
        with pytest.raises(ContractError) as excinfo:
            _probe_for("llm_deployment")
    finally:
        sys.modules.pop("misnamed_p24", None)
    assert excinfo.value.code == "E-PLUGIN-DECORATOR"
    assert "llm_deployment" in str(excinfo.value)
    assert "llm_screen" in str(excinfo.value)


def test_a_decorator_only_registration_with_no_entry_point_is_still_E_PROBE_UNKNOWN(registries):
    """Decision 11's central claim, pinned: two sources of truth exist for "is
    this probe registered" — the entry-point metadata scan and the `PROBES`
    mapping `register_probe` fills at import — and reading `PROBES` alone
    would resolve a registration `validate` never saw, because `validate`
    only ever asks the metadata scan. The fixture: a name registered by
    decorator only, claimed by **no** installed distribution at all. Without
    this, a fail-open reading `PROBES` before the scan passes the whole suite
    silently, because no other test leaves `PROBES` populated under a name no
    entry point also claims."""
    from publishable import Apparatus, register_probe
    from publishable.apparatus import _probe_for
    from publishable.errors import ContractError

    @register_probe("decorator_only_probe")
    def probe(cfg):
        return Apparatus(facts={})

    with pytest.raises(ContractError) as excinfo:
        _probe_for("decorator_only_probe")
    assert excinfo.value.code == "E-PROBE-UNKNOWN"


def test_a_probe_that_raises_becomes_a_coded_refusal_carrying_its_message():
    """`E-APPARATUS-RAISED`, the sibling of `E-RESOLVER-RAISED`. The message is
    asserted to CARRY the probe's own text: the redaction that removes a
    credential from it happens at the call site, and a message emptied here
    would leave nothing for that redaction to be observed on."""
    from publishable.apparatus import observe_once
    from publishable.errors import ContractError

    def probe(cfg):
        raise RuntimeError("instrument offline at bay 3")

    with pytest.raises(ContractError) as excinfo:
        observe_once(probe, None, probe_name="llm_deployment")
    assert excinfo.value.code == "E-APPARATUS-RAISED"
    assert "instrument offline at bay 3" in str(excinfo.value)
    assert "llm_deployment" in str(excinfo.value)


def test_a_probe_calling_sys_exit_is_contained_too():
    """`SystemExit` is a `BaseException`; `except Exception` would let it end
    the command with no diagnostic at all."""
    from publishable.apparatus import observe_once
    from publishable.errors import ContractError

    def probe(cfg):
        raise SystemExit("bye")

    with pytest.raises(ContractError) as excinfo:
        observe_once(probe, None, probe_name="llm_deployment")
    assert excinfo.value.code == "E-APPARATUS-RAISED"


def test_a_keyboard_interrupt_is_re_raised_fresh_and_argument_less():
    """Ctrl-C still stops the command, and a `KeyboardInterrupt("secret")` a
    probe body constructed does not reach Python's printer with its message.
    Assert BOTH: that `KeyboardInterrupt` propagates, and that `str(exc) == ""`."""
    from publishable.apparatus import observe_once

    def probe(cfg):
        raise KeyboardInterrupt("secret-token-abc123")

    with pytest.raises(KeyboardInterrupt) as excinfo:
        observe_once(probe, None, probe_name="llm_deployment")
    assert str(excinfo.value) == ""


def test_every_declared_fact_that_came_back_is_kept_and_a_null_is_kept_as_null():
    """The first two states in one assertion, because a test asserting only the
    value state passes identically when `null` is dropped."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts

    returned = Apparatus(facts={"model_revision": "r1", "reagent_lot": None})
    checked = check_facts(
        returned, ["model_revision", "reagent_lot"], probe_name="p", credentials={}
    )
    assert checked == {"model_revision": "r1", "reagent_lot": None}


def test_a_declared_fact_the_probe_omitted_is_E_APPARATUS_FACT_MISSING():
    """The third state — the plugin and the template disagreeing about what this
    probe supplies. Assert the message names the missing KEY."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"model_revision": "r1"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, ["model_revision", "reagent_lot"], probe_name="p", credentials={})
    assert excinfo.value.code == "E-APPARATUS-FACT-MISSING"
    assert "reagent_lot" in str(excinfo.value)


def test_an_undeclared_fact_the_probe_returned_is_kept():
    """The fourth state, and the deliberate difference from a resolver's
    attribute projection. Paired with the assertion above that the declared ones
    survive, so it cannot pass on an implementation that keeps everything by
    doing nothing at all — assert the returned mapping's exact key set."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts

    returned = Apparatus(facts={"model_revision": "r1", "extra_diagnostic": "on"})
    checked = check_facts(returned, ["model_revision"], probe_name="p", credentials={})
    assert set(checked) == {"model_revision", "extra_diagnostic"}


def _apparatus_with_list_facts():
    from publishable import Apparatus

    return Apparatus(facts=["not", "a", "mapping"])


def _apparatus_with_non_str_key():
    from publishable import Apparatus

    return Apparatus(facts={7: "r1"})


@pytest.mark.parametrize(
    "make_returned",
    [
        lambda: {"model_revision": "r1"},
        _apparatus_with_list_facts,
        _apparatus_with_non_str_key,
    ],
    ids=["a-plain-dict", "facts-is-a-list", "facts-has-a-non-str-key"],
)
def test_a_probe_returning_something_that_is_not_an_apparatus_is_E_APPARATUS_RETURN(make_returned):
    """Parametrized over three shapes: a dict, an `Apparatus` whose `facts` is a
    list, and an `Apparatus` whose `facts` has a non-`str` key. Without this,
    each reaches `run` as an `AttributeError` or a `TypeError`."""
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    with pytest.raises(ContractError) as excinfo:
        check_facts(make_returned(), [], probe_name="p", credentials={})
    assert excinfo.value.code == "E-APPARATUS-RETURN"


def test_a_structural_fact_value_is_E_APPARATUS_FACT_TYPE_and_the_message_names_the_type():
    """Re-coded from `coerce_scalars`, not `E-STEP-RETURN-TYPE`: a reader holding
    that identifier is sent to § Steps and artifacts, which describes a different
    fault at a different time. Assert the code AND that the offending value's own
    text is absent from the message."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"model_revision": ["a-credential-shaped-value-9182736"]})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={})
    assert excinfo.value.code == "E-APPARATUS-FACT-TYPE"
    assert "a-credential-shaped-value-9182736" not in str(excinfo.value)
    assert "list" in str(excinfo.value)


def test_a_fact_equal_to_a_declared_credential_value_is_refused():
    """The value is `lab7`: short, lowercase, ordinary-looking, a whole word.
    That is the point — a random-looking value makes an exact-value check and a
    heuristic AGREE, so the mutation below would have two branches that cannot
    differ."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"operator_note": "lab7"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    assert excinfo.value.code == "E-APPARATUS-FACT-CREDENTIAL"


def test_the_refusal_names_the_variable_and_never_the_value():
    """A refusal that quoted the value would be the leak the check exists to
    prevent. Assert `lab7` is absent from the message and the variable's name is
    present."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"operator_note": "lab7"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    message = str(excinfo.value)
    assert "lab7" not in message
    assert "INSTRUMENT_API_TOKEN" in message


def test_a_value_core_never_read_is_not_matched():
    """The documented limit: a probe reading `os.environ` for a name nothing
    declared is outside what core saw. The control that keeps the check from
    being a string-similarity heuristic in disguise."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts

    returned = Apparatus(facts={"operator_note": "lab7"})
    checked = check_facts(returned, [], probe_name="p", credentials={})
    assert checked == {"operator_note": "lab7"}


def test_the_first_answered_observation_wins_and_a_never_answered_fact_stays_null():
    """Three observations of one fact — null, then a value, then a different
    value — and the recorded entry is the SECOND. A fixture with two
    observations could not tell "first answered" from "last seen"."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00_baseline", {"model_revision": None})
    obs.record("00_baseline", {"model_revision": "r1"})
    obs.record("00_baseline", {"model_revision": "r2"})
    obs.record("00_baseline", {"never_answers": None})
    doc = obs.facts_document()
    assert doc["00_baseline"]["model_revision"] == "r1"
    assert doc["00_baseline"]["never_answers"] is None


def test_a_partially_answered_fact_records_its_answer_and_still_counts_its_nulls():
    """The flaky case the null rule exists for, and the one `facts` alone cannot
    see: the recorded entry holds the value AND the pair's null count is 2. A
    build that derived the counts from `facts` would report 0."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00_baseline", {"reagent_lot": None})
    obs.record("00_baseline", {"reagent_lot": "lot-9"})
    obs.record("00_baseline", {"reagent_lot": None})
    doc = obs.facts_document()
    assert doc["00_baseline"]["reagent_lot"] == "lot-9"
    unobserved = obs.unobserved(["reagent_lot"])
    assert unobserved["reagent_lot"]["null_probes"] == 2
    assert unobserved["reagent_lot"]["total_probes"] == 3


def test_unobserved_counts_declared_facts_only_and_counts_every_probe():
    """The undeclared fact must have NO entry, asserted beside the declared
    ones' presence: an absence assertion alone passes if nothing was recorded.
    `unobserved` is the per-condition counts summed, asserted against a
    hand-computed total over the observations this test recorded."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00_baseline", {"model_revision": "r1", "undeclared_diag": "x"})
    obs.record("01_variant", {"model_revision": None, "undeclared_diag": "y"})
    unobserved = obs.unobserved(["model_revision"])
    assert set(unobserved) == {"model_revision"}
    assert unobserved["model_revision"] == {"null_probes": 1, "total_probes": 2}


def test_the_warning_is_one_finding_per_condition_and_fact_including_the_flaky_pair():
    """Two conditions × three declared facts over six observations, arranged as
    Fixture N: one never-answered pair, two partially answered pairs, and three
    pairs with no null at all. Exactly THREE findings, asserted as a count and as
    the exact set of (condition, fact) pairs — per-call emission would produce
    eight, and a warning derived from `facts` alone would produce one."""
    from publishable.apparatus import Observations
    from publishable.diagnostics import Collector

    obs = Observations()
    # 00_baseline: fact_a clean, fact_b flaky (1 null of 2), fact_c never answers
    obs.record("00_baseline", {"fact_a": "va", "fact_b": "vb", "fact_c": None})
    obs.record("00_baseline", {"fact_a": "va", "fact_b": None, "fact_c": None})
    # 01_variant: fact_a clean, fact_b clean, fact_c flaky (1 null of 2)
    obs.record("01_variant", {"fact_a": "va", "fact_b": "vb", "fact_c": "vc"})
    obs.record("01_variant", {"fact_a": "va", "fact_b": "vb", "fact_c": None})

    c = Collector()
    obs.warn_unanswered(c)
    findings = [f for f in c.findings if f.code == "W-APPARATUS-UNANSWERED"]
    assert len(findings) == 3
    pairs = set()
    for f in findings:
        if "00_baseline" in f.message and "fact_b" in f.message:
            pairs.add(("00_baseline", "fact_b"))
        elif "00_baseline" in f.message and "fact_c" in f.message:
            pairs.add(("00_baseline", "fact_c"))
        elif "01_variant" in f.message and "fact_c" in f.message:
            pairs.add(("01_variant", "fact_c"))
    assert pairs == {
        ("00_baseline", "fact_b"),
        ("00_baseline", "fact_c"),
        ("01_variant", "fact_c"),
    }

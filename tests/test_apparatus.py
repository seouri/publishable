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

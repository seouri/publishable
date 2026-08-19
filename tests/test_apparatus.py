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

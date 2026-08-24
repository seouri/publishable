"""H7d Part A: `Apparatus` and probe dispatch. See `docs/reference.md`
§ The apparatus core can only observe and § Creating a plugin.
"""

import math

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


def test_an_np_str_fact_value_resolves_instead_of_being_refused():
    """H5a task 10's retirement, pinned: before this task, `np.str_` had
    `__len__` and was refused by `coerce_scalars`' structural guard the same
    way `["a-credential-shaped-value-9182736"]` above still is, re-coded here
    to `E-APPARATUS-FACT-TYPE`. Now it coerces, so the fact resolves and its
    recorded value is exactly `str` — a refusal that stopped firing, stated
    as a retirement rather than left implicit."""
    import numpy as np

    from publishable import Apparatus
    from publishable.apparatus import check_facts

    returned = Apparatus(facts={"model_revision": np.str_("r1")})
    checked = check_facts(returned, ["model_revision"], probe_name="p", credentials={})
    assert checked == {"model_revision": "r1"}
    assert type(checked["model_revision"]) is str


def test_a_fact_equal_to_a_declared_credential_value_is_refused():
    """The value is `lab7`: short, lowercase, ordinary-looking, a whole word —
    chosen so an exact-value check catches it regardless of what it looks
    like, which is the property a pattern or entropy heuristic cannot be
    relied on for."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"operator_note": "lab7"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    assert excinfo.value.code == "E-APPARATUS-FACT-CREDENTIAL"


def test_a_fact_value_containing_a_declared_credential_value_is_refused():
    """Whole-branch review Major 2: `check_facts` matched only by EXACT
    equality, while `secrets.redact` — over the identical value set,
    `credential_values(declared_credential_names(...))` — matches by
    SUBSTRING. A probe returning an endpoint URL with the credential appended
    (`".../v1?key=" + token`) sailed through the exact-equality check and was
    published verbatim in `provenance.apparatus.facts` and every
    `apparatus/probes.jsonl` line — the two artifacts `reference.md` calls
    "publishable as-is". Match the way `redact` already matches: containment,
    not a third rule."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"endpoint": "https://api.example.com/v1?key=lab7"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    assert excinfo.value.code == "E-APPARATUS-FACT-CREDENTIAL"


def test_the_containment_refusal_also_names_the_variable_and_never_the_value():
    """The message for the substring case must uphold decision 6's own
    constraint exactly as the exact-equality case does: the fact KEY and the
    credential's NAME, never the value — the credential value `lab7` is
    absent even though it is only part of the offending fact value."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"endpoint": "https://api.example.com/v1?key=lab7"})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    message = str(excinfo.value)
    assert "lab7" not in message
    assert "INSTRUMENT_API_TOKEN" in message
    assert "endpoint" in message


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


def test_a_fact_value_with_elementwise_eq_is_E_APPARATUS_FACT_TYPE_even_beside_a_credential():
    """Major 2 (batch 2 review): `value == cred_value` used to run on the RAW
    value, before the scalar walk that would have refused it — so a NumPy
    array fact escaped as an uncoded `ValueError` ("the truth value of an
    array... is ambiguous"), but only when `credentials` was non-empty. With
    `credentials={}` the same fact was correctly `E-APPARATUS-FACT-TYPE`,
    which is what made the fault conditional on a declaration rather than on
    the fact's own shape. The `isinstance(value, str)` guard fixes this: a
    credential value is always a `str`, so nothing this check ever needs to
    catch is skipped."""
    import numpy as np

    from publishable import Apparatus
    from publishable.apparatus import check_facts
    from publishable.errors import ContractError

    returned = Apparatus(facts={"model_revision": np.array([1, 2])})
    with pytest.raises(ContractError) as excinfo:
        check_facts(returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"})
    assert excinfo.value.code == "E-APPARATUS-FACT-TYPE"


def test_a_credential_shaped_value_that_is_not_a_declared_credential_is_kept():
    """Major 3 (batch 2 review): the missing third cell. `credentials` is
    NON-EMPTY here, so the comparison loop actually runs, and the fact value
    is long, mixed-case-and-digit, credential-shaped text — exactly what a
    pattern or entropy heuristic would flag — but it is not equal to the one
    declared credential's value. Decision 6's own ground: "a pattern check …
    fails closed on a config value that happens to look random." Kept, not
    refused — the previous control (`credentials={}`) cannot exercise this,
    because its comparison loop never runs at all."""
    from publishable import Apparatus
    from publishable.apparatus import check_facts

    returned = Apparatus(facts={"model_revision": "gpt-5.5-2026-06-11x9f3a2b8c"})
    checked = check_facts(
        returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"}
    )
    assert checked == {"model_revision": "gpt-5.5-2026-06-11x9f3a2b8c"}


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
    """Two conditions × three declared facts over FOUR `record` calls (not the
    plan's Fixture N, which is a six-line `run`-level ledger owned by task 11
    — this is a direct-call fixture built for this batch): one never-answered
    pair, two partially answered pairs, and three pairs with no null at all.
    Exactly THREE findings, asserted as a count and as the exact set of
    (condition, fact) pairs — this fixture's four null observations mean a
    per-null-observation emission would produce four, not three, and a
    warning derived from `facts_document()` alone would produce one."""
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
    obs.warn_unanswered(c, ["fact_a", "fact_b", "fact_c"])
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


def test_an_undeclared_facts_null_warns_of_nothing_beside_a_declared_null_that_must():
    """Major 1 (batch 2 review): `warn_unanswered` fires only for a DECLARED
    fact that came back `null` — Decision 8's opening clause and Decision 4's
    fourth row. Both an undeclared and a declared fact come back `null` here,
    so the control is not an absence-only assertion: the declared pair's
    finding must be present at the same time the undeclared pair's is absent,
    which is what a build filtering nothing (the plan-brief signature with no
    `declared` parameter) cannot do."""
    from publishable.apparatus import Observations
    from publishable.diagnostics import Collector

    obs = Observations()
    obs.record("00_baseline", {"model_revision": None, "undeclared_diag": None})

    c = Collector()
    obs.warn_unanswered(c, ["model_revision"])
    findings = [f for f in c.findings if f.code == "W-APPARATUS-UNANSWERED"]
    assert len(findings) == 1
    assert "model_revision" in findings[0].message
    assert all("undeclared_diag" not in f.message for f in findings)


def test_a_ledger_line_carries_exactly_the_five_documented_keys(tmp_path):
    """Asserted as an exact key SET, in the shape `json.loads` gives back: a
    sixth key nobody documented is what this catches."""
    import json

    from publishable.apparatus import append_observation

    append_observation(
        tmp_path, phase="run_start", condition="00_baseline", probe="p", facts={"a": 1}
    )
    line = json.loads((tmp_path / "apparatus" / "probes.jsonl").read_text().splitlines()[0])
    assert set(line) == {"at", "phase", "condition", "probe", "facts"}


def test_a_null_fact_and_an_undeclared_fact_both_reach_the_ledger(tmp_path):
    """The ledger is every observation, nulls included — which is what makes a
    fact that only started answering halfway through visible as exactly that."""
    import json

    from publishable.apparatus import append_observation

    append_observation(
        tmp_path,
        phase="pre_execution",
        condition="00_baseline",
        probe="p",
        facts={"declared_fact": None, "undeclared_fact": "x"},
    )
    line = json.loads((tmp_path / "apparatus" / "probes.jsonl").read_text().splitlines()[0])
    assert line["facts"] == {"declared_fact": None, "undeclared_fact": "x"}


def test_a_second_append_adds_a_line_and_rewrites_nothing(tmp_path):
    """Append-only, asserted on the file's RAW text: both lines present, the
    first byte-identical to what the first call wrote."""
    from publishable.apparatus import append_observation

    append_observation(
        tmp_path, phase="run_start", condition="00_baseline", probe="p", facts={"a": 1}
    )
    ledger = tmp_path / "apparatus" / "probes.jsonl"
    first_line = ledger.read_text()
    append_observation(
        tmp_path, phase="pre_execution", condition="00_baseline", probe="p", facts={"a": 2}
    )
    raw = ledger.read_text()
    lines = raw.splitlines()
    assert len(lines) == 2
    assert raw.startswith(first_line)


def test_the_condition_key_is_the_nn_label_form_and_a_labelless_condition_is_nn():
    """`condition_dir_name`'s own spelling, imported rather than re-formatted, and
    the no-sweep case that `reference.md`'s example never shows. The labelled
    branch is checked against `condition_dir_name` itself, computed rather than
    a hard-coded literal — `condition_dir_name` is exactly `f"{index:02d}_{label}"`
    with no sanitisation, so no mutation of "call the import" vs "inline the same
    f-string" can ever be caught here; what this pins is the VALUE, not the
    import."""
    from publishable.apparatus import condition_key
    from publishable.sweep import condition_dir_name

    assert condition_key(0, "baseline") == condition_dir_name(0, "baseline")
    assert condition_key(0, "baseline") == "00_baseline"
    assert condition_key(0, None) == "00"


def test_observer_warn_unanswered_delegates_to_observations_with_declared_facts(tmp_path):
    """Fix round 1, Minor 7. `Observer.warn_unanswered` shipped with no caller
    and no test of its own — every existing test exercised
    `Observations.warn_unanswered` directly, which is a proxy for this
    method's one job: supplying `self.declared_facts` so a caller (task 11's
    wiring, its own step 2) does not have to carry it separately. `Observer`'s
    own call sites are all `command_run`'s (task 9's run-start round, task
    10's per-execution round); `warn_unanswered`'s call site is task 11's, not
    yet built — this test exercises the method directly rather than waiting
    on that wiring, the same way `check_facts` and `observe_once` were
    exercised directly before `Observer` existed to call them."""
    from collections import namedtuple

    from publishable.apparatus import Apparatus, Observer
    from publishable.diagnostics import Collector

    Condition = namedtuple("Condition", ["index", "label"])
    conditions = [Condition(0, "baseline")]

    def probe(cfg):
        return Apparatus(facts={"declared_fact": None, "undeclared_fact": "x"})

    observer = Observer(
        probe_name="p",
        probe=probe,
        declared_facts=["declared_fact"],
        conditions=conditions,
        cfgs={0: None},
        run_dir=tmp_path,
        credentials={},
    )
    observer.observe_round(phase="run_start", condition_index=None)

    c = Collector()
    observer.warn_unanswered(c)
    findings = [f for f in c.findings if f.code == "W-APPARATUS-UNANSWERED"]
    assert len(findings) == 1
    assert "declared_fact" in findings[0].message
    # The undeclared fact must never warn (Decision 8's fourth row) — proof
    # that `self.declared_facts`, not every observed fact, is what reached
    # `Observations.warn_unanswered` through this method.
    assert all("undeclared_fact" not in f.message for f in findings)


def test_changed_value_to_different_value_fails():
    """Reading 1 of Decision 1's five: a fact answered once and then answered
    a DIFFERENT value fails, returning the (fact, first, incoming) triple.
    `record` runs first so `_first_answered` is established before the
    comparison, mirroring `_observe_one`'s own order (Decision 3)."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"pinned": "r1"})
    assert obs.changed("00", {"pinned": "r1"}) is None
    obs.record("00", {"pinned": "r2"})
    assert obs.changed("00", {"pinned": "r2"}) == ("pinned", "r1", "r2")


def test_changed_null_to_value_passes_and_becomes_first_answered():
    """Reading 2: a fact silent on its first call and answered on its second
    does not fail, and the answered value becomes the pair's first answered —
    read back through `facts_document`, never a second mapping."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"appears": None})
    assert obs.changed("00", {"appears": None}) is None
    obs.record("00", {"appears": "A1"})
    assert obs.changed("00", {"appears": "A1"}) is None
    assert obs.facts_document()["00"]["appears"] == "A1"


def test_changed_value_to_null_passes_first_answered_stands():
    """Reading 3: a fact that answered once and then goes quiet does not
    fail, and the first answered value is unchanged by the null call."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"vanishes": "L1"})
    assert obs.changed("00", {"vanishes": "L1"}) is None
    obs.record("00", {"vanishes": None})
    assert obs.changed("00", {"vanishes": None}) is None
    assert obs.facts_document()["00"]["vanishes"] == "L1"


def test_changed_an_absent_key_is_not_compared():
    """Reading 4: a fact simply missing from a later call's mapping is never
    iterated by `changed`, so it can never appear in the returned triple —
    the only absence that reaches this method at all is an undeclared fact's,
    since a declared fact's absence is already `E-APPARATUS-FACT-MISSING`
    (Part A's, upstream of this method)."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"pinned": "r1", "sometimes": "S1"})
    assert obs.changed("00", {"pinned": "r1", "sometimes": "S1"}) is None
    # `sometimes` is absent from this call entirely.
    obs.record("00", {"pinned": "r1"})
    assert obs.changed("00", {"pinned": "r1"}) is None


def test_changed_value_null_different_value_fails_against_first_not_most_recent():
    """Reading 5, and the one that makes 'first answered' a different rule
    from 'most recent': a fact answers v1, goes quiet, then answers v2 — and
    FAILS, against v1, not against the intervening null. A two-observation
    fixture cannot separate this from reading 1 (design's own constraint), so
    this test chains three record/changed pairs in the order `_observe_one`
    uses. Under a most-recent comparison the middle call's null would make
    the third call's `null -> v2` transition read as reading 2 and PASS —
    which is exactly mutation (a)'s discriminator."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"flip": "v1"})
    assert obs.changed("00", {"flip": "v1"}) is None
    obs.record("00", {"flip": None})
    assert obs.changed("00", {"flip": None}) is None
    obs.record("00", {"flip": "v2"})
    assert obs.changed("00", {"flip": "v2"}) == ("flip", "v1", "v2")


def test_changed_is_scoped_per_condition_never_across():
    """The per-condition reading: two conditions record different values for
    the SAME fact name — a swept fact, Part A's own shipped shape — and each
    condition's first observation of its own value passes. `changed` must
    never compare condition A's incoming value against condition B's first
    answered one."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00_a", {"model_revision": "rev-a"})
    assert obs.changed("00_a", {"model_revision": "rev-a"}) is None
    obs.record("01_b", {"model_revision": "rev-b"})
    # The second condition's own FIRST observation — must not be compared
    # against "00_a"'s "rev-a", even though it differs.
    assert obs.changed("01_b", {"model_revision": "rev-b"}) is None


def test_check_changed_raises_E_APPARATUS_CHANGED_naming_both_values_and_the_condition():
    """Decision 2: the message names the condition key, the fact, and both
    values, joined by `→` (never `->`), and never either value's own Python
    variable name — the fact and condition and values are read from the
    exception, not transcribed from the call site. Paired with the control
    that must report: the same helper, called where nothing changed, returns
    silently rather than merely not-raising-for-this-fact — a control
    asserting only an absence would pass identically if `check_changed` did
    nothing at all, so this asserts the return value too."""
    from publishable.apparatus import Observations, check_changed
    from publishable.errors import ContractError

    obs = Observations()
    obs.record("00", {"pinned": "r1"})
    assert check_changed(obs, "00", {"pinned": "r1"}) is None

    obs.record("00", {"pinned": "r2"})
    with pytest.raises(ContractError) as excinfo:
        check_changed(obs, "00", {"pinned": "r2"})
    assert excinfo.value.code == "E-APPARATUS-CHANGED"
    message = str(excinfo.value)
    assert "r1 → r2" in message
    assert "->" not in message
    assert "pinned" in message
    assert "00" in message


def test_a_credential_carrying_value_cannot_reach_check_changed_because_check_facts_runs_first():
    """The ordering the message's safety rests on, asserted rather than
    assumed: `check_facts` runs before a value ever reaches
    `Observations.record`/`changed`, so a credential-carrying fact value
    never becomes a first-answered value or an incoming one. Calling the two
    in the chain's own order and watching `check_facts` raise ITS OWN code —
    never `E-APPARATUS-CHANGED` — is the control that must report: if the
    ordering were reversed, this test would see `check_changed` run first
    and either raise nothing (the credential became the first-answered
    value) or raise `E-APPARATUS-CHANGED` naming it, and it would silently
    pass through this test's `pytest.raises` if it named the wrong code."""
    from publishable import Apparatus
    from publishable.apparatus import Observations, check_changed, check_facts
    from publishable.errors import ContractError

    obs = Observations()
    obs.record("00", {"calibration_id": "CAL-2026-07-19"})

    returned = Apparatus(facts={"calibration_id": "lab7"})
    with pytest.raises(ContractError) as excinfo:
        checked = check_facts(
            returned, [], probe_name="p", credentials={"INSTRUMENT_API_TOKEN": "lab7"}
        )
        # check_changed is never reached if check_facts refuses first — this
        # line only runs if the ordering under test has already broken.
        check_changed(obs, "00", checked)
    assert excinfo.value.code == "E-APPARATUS-FACT-CREDENTIAL"


def test_stop_codes_holds_exactly_the_two_codes_execute_plan_breaks_on():
    """Plan correction 4: `E-APPARATUS-CHANGED` must NOT join
    `APPARATUS_CODES` — that frozenset is `command_run`'s containment filter
    for a probe CALL, and a changed fact never crosses it. `STOP_CODES` is
    the separate, both-members-pinned enumeration task 3 mints."""
    from publishable.apparatus import APPARATUS_CODES, STOP_CODES

    # GUARD-PIN ARM C, edited by H9c plan task 9 — its SOLE AUTHORIZED EDITOR.
    # One member added, none removed, nothing reordered, matching the design's
    # advance spec. The function's NAME still says "the two codes"; it is left
    # alone deliberately — batch 1's report cites this arm by that name, and a
    # rename would break the citation a reader follows. Disclosed in task 9's
    # report rather than corrected silently.
    assert STOP_CODES == {
        "E-APPARATUS-RAISED",
        "E-APPARATUS-CHANGED",
        "E-APPARATUS-UNEXPECTED",
    }
    assert "E-APPARATUS-CHANGED" not in APPARATUS_CODES
    assert "E-APPARATUS-RAISED" in APPARATUS_CODES
    # ADDED beside arm D's two shipped assertions above, never editing one
    # (H9c § 8, arm D: editor NONE; task 9 may add a sibling). Opposite
    # membership from `STOP_CODES` on purpose — plan correction 12: the loop
    # breaks on a `STOP_CODES` member before `command_run`'s containment filter
    # is reached, which is `E-APPARATUS-CHANGED`'s own documented reason.
    assert "E-APPARATUS-UNEXPECTED" not in APPARATUS_CODES


def test_changed_is_reflexivity_safe_for_a_constant_nan_fact():
    """Whole-branch review Major 1: `reference.md`'s `E-APPARATUS-FACT-TYPE`
    row admits `float` unqualified, so `coerce_scalars` legally passes a
    non-finite value through, and `float('nan') != float('nan')` is `True`
    in plain Python — a fact whose value is a constant `nan` would report a
    change against ITSELF on its own first observation once task 4 wires
    this into a run, tripping Decision 11's run-start guarantee. `changed`
    must treat a `nan`-vs-`nan` pair as unchanged; a `nan` compared against a
    genuinely different value must still fail."""
    from publishable.apparatus import Observations

    obs = Observations()
    obs.record("00", {"drift": float("nan")})
    # Same nan-valued fact, observed again — must NOT read as a change.
    assert obs.changed("00", {"drift": float("nan")}) is None
    obs.record("00", {"drift": 1.5})
    triple = obs.changed("00", {"drift": 1.5})
    assert triple is not None
    fact, first, incoming = triple
    assert fact == "drift"
    assert isinstance(first, float) and math.isnan(first)
    assert incoming == 1.5


# --- H7d Part B task 4: the ordering chain, and the two assertions only it
# can make ---------------------------------------------------------------


def test_the_ordering_chain_counts_the_moving_call_before_the_gate_fires(tmp_path):
    """Task 4 step 2. Fixture G1's own schedule, driven through `Observer`
    across four rounds — the raise on round 4 (`pinned: r1 -> r2`) must have
    already been counted in `unobserved.total_probes` for `pinned`, because
    `Observations.record` runs before the gate compares (Decision 3,
    `_observe_one`'s own order). Named in the plan's mutation table and in
    task 4 step 2 (not in § Corrections against the code, which this
    docstring previously mis-cited).

    **Batch 3 review, Major 2: this is a census assertion, not a
    discriminator, and this docstring previously overclaimed otherwise.**
    `_first_answered` never overwrites an answered pair, so no *value*
    assertion can tell record-before-gate from the reverse — true — but this
    *count* cannot either, on any fixture: `Observations.changed`'s own
    reflexivity-safety assert (`assert incoming is None` when `first is
    None`) fires on the first answering observation of ANY fact under a
    gate-before-record reordering, which is strictly earlier than any count
    this test reads. Verified by running: moving the gate above `record`
    makes this test fail with an `AssertionError` from `apparatus.py`, never
    with `total_probes == 3`. The record-before-gate ordering is not
    unguarded — that assert fires loudly the instant it is broken — but this
    test does not witness it; see
    `test_changed_asserts_when_called_without_record_first` for what that
    assert actually pins, and its own docstring for what it does and does
    not cover.

    A direct call rather than end to end: at this commit the raise still
    ends the command before `run.yaml` is written, so
    `provenance.apparatus.unobserved` does not exist to read — task 7
    re-asserts the same number end to end."""
    from collections import namedtuple

    from publishable.apparatus import Apparatus, Observer
    from publishable.errors import ContractError

    Condition = namedtuple("Condition", ["index", "label"])
    conditions = [Condition(0, None)]

    schedule = [
        {"pinned": "r1", "appears": None, "vanishes": "L1", "sometimes": "S1"},
        {"pinned": "r1", "appears": "A1", "vanishes": None},
        {"pinned": "r1", "appears": "A1", "vanishes": None},
        {"pinned": "r2", "appears": "A1", "vanishes": None},
    ]
    calls = {"n": 0}

    def probe(cfg):
        facts = dict(schedule[calls["n"]])
        calls["n"] += 1
        return Apparatus(facts=facts)

    observer = Observer(
        probe_name="p",
        probe=probe,
        declared_facts=["pinned", "appears", "vanishes"],
        conditions=conditions,
        cfgs={0: None},
        run_dir=tmp_path,
        credentials={},
    )

    phases = ["run_start", "pre_execution", "pre_execution", "pre_execution"]
    raised: ContractError | None = None
    for phase in phases:
        try:
            observer.observe_round(phase=phase, condition_index=None)
        except ContractError as exc:
            raised = exc
            break
    assert raised is not None
    assert raised.code == "E-APPARATUS-CHANGED"
    assert calls["n"] == 4, "the raise must not preempt the fourth call"
    assert observer.observations.unobserved(["pinned"])["pinned"]["total_probes"] == 4


def test_changed_asserts_when_called_without_record_first():
    """Batch 3 review, Major 2, action 2. Pins the claim
    `Observations.changed`'s own docstring makes and that nothing previously
    asserted: calling `changed()` for a pair whose non-`None` value has never
    gone through `record()` first trips the reflexivity-safety `assert`
    (`assert incoming is None` when `first is None`), because that assert's
    whole premise is that `record()` already ran for the same `facts` this
    call carries.

    **What this pins, and what it does not.** This witnesses that `changed`
    *requires* record-first — grep confirmed no test in this file asserted
    it before now. It does NOT witness that `Observer._observe_one`
    *satisfies* that requirement: add this test after a real reorder of
    `_observe_one` and it still passes unchanged, because it calls `changed`
    directly rather than through `_observe_one`. `_observe_one`'s own order
    is what `test_g1_ordering_chain_appends_before_the_gate_fires_end_to_end`
    (`tests/test_cli.py`) and
    `test_the_ordering_chain_records_before_it_gates` (below) exercise."""
    from publishable.apparatus import Observations

    obs = Observations()
    with pytest.raises(AssertionError):
        obs.changed("00", {"pinned": "r1"})


def test_the_ordering_chain_records_before_it_gates(tmp_path):
    """Batch 3 review, Major 2, action 3: the only legible witness of
    `_observe_one`'s actual call order, since every *value* assertion is
    equal under either ordering and every *count* assertion sits behind the
    reflexivity-safety assert that a reordering trips first (see the test
    above and the one two above). Wraps `Observations.record` and
    `check_changed` to log which ran first for the same call, rather than
    inferring order from a downstream count or value — the direct claim
    Decision 3 makes (`record` before the gate), witnessed directly."""
    from collections import namedtuple

    import publishable.apparatus as apparatus_mod
    from publishable.apparatus import Apparatus, Observer

    Condition = namedtuple("Condition", ["index", "label"])
    conditions = [Condition(0, None)]

    def probe(cfg):
        return Apparatus(facts={"pinned": "r1"})

    observer = Observer(
        probe_name="p",
        probe=probe,
        declared_facts=["pinned"],
        conditions=conditions,
        cfgs={0: None},
        run_dir=tmp_path,
        credentials={},
    )

    order: list[str] = []
    real_record = observer.observations.record
    real_check_changed = apparatus_mod.check_changed

    def spy_record(condition_key, facts):
        order.append("record")
        return real_record(condition_key, facts)

    def spy_check_changed(observations, condition_key_value, facts):
        order.append("check_changed")
        return real_check_changed(observations, condition_key_value, facts)

    observer.observations.record = spy_record  # type: ignore[method-assign]
    apparatus_mod.check_changed = spy_check_changed
    try:
        observer.observe_round(phase="run_start", condition_index=None)
    finally:
        apparatus_mod.check_changed = real_check_changed

    assert order == ["record", "check_changed"], order


# --- H8b task 1: `replay_ledger` — the baseline, replayed through the
# shipped `Observations` -------------------------------------------------


def _write_ledger(run_dir, lines):
    import json

    ledger_dir = run_dir / "apparatus"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    (ledger_dir / "probes.jsonl").write_text("\n".join(json.dumps(x) for x in lines) + "\n")


_H8B_T1_PROBE_MODULE = """\
from publishable import Apparatus, register_probe


@register_probe("h8b_t1_probe")
def probe(cfg):
    return Apparatus(facts={"model_revision": cfg.parameters.instrument.model})
"""

_H8B_T1_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("h8b_t1_assay")
class H8bT1Assay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    apparatus_probe = "h8b_t1_probe"
    apparatus_facts = ["model_revision"]
    parameter_spec = {
        "instrument.model": Param(str, default="m1", choices=["m1", "m2"]),
    }
"""


def test_replay_ledger_against_a_real_run_reproduces_provenance_apparatus_facts(
    installed, registries, tmp_path, capsys
):
    """Fixture P's shape, driven to completion: a synthetic installed
    distribution registering a probe, a project-local template declaring
    `apparatus_probe`/`apparatus_facts`, two swept conditions. The pin is
    that `replay_ledger`'s `facts_document()` reproduces
    `provenance.apparatus.facts` — both read back from the artifacts a real
    `run` wrote (`apparatus/probes.jsonl`, `run.yaml`), never asserted as a
    literal. This is the arm that pins that the reader reads what the
    writer wrote."""
    import yaml
    from tests.test_cli import run_a_project

    from publishable.apparatus import replay_ledger
    from publishable.diagnostics import EXIT_OK

    site = installed(
        "dist-h8b-t1", "1.0", {"publishable.probes": {"h8b_t1_probe": "h8b_t1_probe_mod:probe"}}
    )
    (site / "h8b_t1_probe_mod.py").write_text(_H8B_T1_PROBE_MODULE)

    doc = run_a_project(
        tmp_path,
        capsys=capsys,
        experiment_type="h8b_t1_assay",
        parameters={"instrument": {"model": "m1"}},
        sweep={"grid": {"instrument.model": ["m1", "m2"]}},
        _local_template=_H8B_T1_TEMPLATE,
        expect_exit=EXIT_OK,
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    observations = replay_ledger(doc["run_dir"])
    assert observations.facts_document() == run["provenance"]["apparatus"]["facts"]
    assert {v["model_revision"] for v in observations.facts_document().values()} == {"m1", "m2"}


def test_replay_ledger_two_conditions_scope_independently(tmp_path):
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "run_start",
                "condition": "00_a",
                "probe": "p",
                "facts": {"f": "x"},
            },
            {
                "at": "t",
                "phase": "run_start",
                "condition": "01_b",
                "probe": "p",
                "facts": {"f": "y"},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {"00_a": {"f": "x"}, "01_b": {"f": "y"}}


def test_replay_ledger_null_then_value_keeps_the_answer(tmp_path):
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "run_start",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": None},
            },
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": "v"},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {"00_x": {"f": "v"}}


def test_replay_ledger_value_then_null_keeps_the_answer(tmp_path):
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": "v"},
            },
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": None},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {"00_x": {"f": "v"}}


def test_replay_ledger_excludes_freeze_and_dry_run_lines_from_the_baseline(tmp_path):
    """Decision 9: only `run_start`/`pre_execution` lines feed the baseline.
    A well-formed `freeze` line and a well-formed `dry_run` line, each
    answering the fact a `run_start` line left `null`, must both be
    invisible to `facts_document()` — the fact stays `null`."""
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "run_start",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": None},
            },
            {
                "at": "t",
                "phase": "freeze",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": "from-freeze"},
            },
            {
                "at": "t",
                "phase": "dry_run",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": "from-dry-run"},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {"00_x": {"f": None}}


def test_replay_ledger_an_unrecognized_phase_is_skipped_not_refused(tmp_path):
    """The ledger is append-only; a phase this build has no name for must not
    make an old `freeze` unable to read a newer run's ledger."""
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "some_future_phase",
                "condition": "00_x",
                "probe": "p",
                "facts": {"f": "z"},
            }
        ],
    )
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {}


@pytest.mark.parametrize(
    "raw",
    [
        "not json at all {{{",
        # Batch 4 review, Minor 2: `[1, 2, 3]` is caught by the NEXT guard
        # (the missing-keys check: `"phase" not in [1, 2, 3]` is `True`)
        # regardless of whether the `isinstance(doc, Mapping)` guard exists
        # at all — deleting that guard left every arm here green. A JSON
        # array containing the three key STRINGS as elements is what the
        # missing-keys check cannot catch (`"phase" in doc` is `True` for a
        # list holding the string `"phase"`), so this fixture reaches
        # `doc["phase"]` next — a `TypeError` if the `Mapping` guard is
        # gone, `E-FREEZE-LEDGER-UNREADABLE` if it is there.
        '["phase", "condition", "facts"]',
        '{"phase": "run_start", "condition": "00_x"}',
    ],
    ids=["not-json", "not-a-mapping", "missing-facts"],
)
def test_replay_ledger_a_malformed_line_is_E_FREEZE_LEDGER_UNREADABLE(tmp_path, raw):
    from publishable.apparatus import replay_ledger
    from publishable.errors import ContractError

    ledger_dir = tmp_path / "apparatus"
    ledger_dir.mkdir()
    (ledger_dir / "probes.jsonl").write_text(raw + "\n")

    with pytest.raises(ContractError) as excinfo:
        replay_ledger(tmp_path)
    assert excinfo.value.code == "E-FREEZE-LEDGER-UNREADABLE"


def test_replay_ledger_with_no_ledger_file_returns_an_empty_observations(tmp_path):
    from publishable.apparatus import replay_ledger

    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {}


def test_replay_ledger_with_an_empty_ledger_file_returns_an_empty_observations(tmp_path):
    from publishable.apparatus import replay_ledger

    ledger_dir = tmp_path / "apparatus"
    ledger_dir.mkdir()
    (ledger_dir / "probes.jsonl").write_text("")
    observations = replay_ledger(tmp_path)
    assert observations.facts_document() == {}


def test_m8_fixture_a_second_freezes_own_answer_agrees_because_freeze_lines_are_excluded(
    tmp_path,
):
    """Decision 9's stated risk, pinned directly (Mutation M8's non-mutated
    half — see the task report for the mutated half, which needs editing
    `replay_ledger`'s filter and is exercised by hand rather than shipped).

    A `run_start` line leaves `pinned` `null`; a constructed `freeze` line
    (task 6 builds the real `freeze` command; this ledger is hand-written
    to stand in for one) answers it `"a"`. `replay_ledger` must exclude that
    line, so a SECOND freeze's own `record`-then-`changed` call — simulating
    what `freeze` does against the replayed baseline — sees no prior answer,
    adopts `"b"` as this pair's first-answered value via `record`, and then
    `changed` compares `"b"` against the value it just adopted: no
    contradiction. Were the `freeze` line admitted to the baseline instead,
    `record` would find the pair already answered `"a"` and never overwrite
    it, and `changed` would then report `"a"` vs `"b"` as a contradiction —
    two different exit codes downstream, not two different internal states."""
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "run_start",
                "condition": "00_x",
                "probe": "p",
                "facts": {"pinned": None},
            },
            {
                "at": "t",
                "phase": "freeze",
                "condition": "00_x",
                "probe": "p",
                "facts": {"pinned": "a"},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    observations.record("00_x", {"pinned": "b"})
    assert observations.changed("00_x", {"pinned": "b"}) is None


def test_m9_fixture_the_baseline_is_first_answered_not_most_recent(tmp_path):
    """Mutation M9's fixture: `pinned` goes `r1 → null → r2` across three
    `pre_execution` lines — the one transition that distinguishes *first
    answered* from *most recent*, since with only two values the first is
    also the last-but-one. Under the shipped rule the baseline is `r1`, so
    an incoming `r1` agrees. `replay_ledger` calling `Observations.record`
    per line (rather than assigning `_first_answered[pair]` unconditionally
    per line) is what this pins; see the task report for the mutated run."""
    from publishable.apparatus import replay_ledger

    _write_ledger(
        tmp_path,
        [
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"pinned": "r1"},
            },
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"pinned": None},
            },
            {
                "at": "t",
                "phase": "pre_execution",
                "condition": "00_x",
                "probe": "p",
                "facts": {"pinned": "r2"},
            },
        ],
    )
    observations = replay_ledger(tmp_path)
    observations.record("00_x", {"pinned": "r1"})
    assert observations.changed("00_x", {"pinned": "r1"}) is None


# --- H8b task 2: `PHASES`, the four constants, and the assert ------------


def test_phases_is_exactly_the_four_named_constants():
    from publishable.apparatus import (
        PHASE_DRY_RUN,
        PHASE_FREEZE,
        PHASE_PRE_EXECUTION,
        PHASE_RUN_START,
        PHASES,
    )

    assert PHASES == {PHASE_RUN_START, PHASE_PRE_EXECUTION, PHASE_DRY_RUN, PHASE_FREEZE}
    assert PHASES == {"run_start", "pre_execution", "dry_run", "freeze"}


def test_append_observation_accepts_each_of_the_four_named_phases(tmp_path):
    """Mutation M7's non-mutated arm: one call per name, each landing its own
    line carrying its own `phase`. **Iterates the four LITERAL spellings,
    never `PHASES` itself** (batch B2 review, Major 1: the first version of
    this test looped over `sorted(PHASES)`, so a removed name was never
    passed to `append_observation` at all — the expectation and the actual
    moved together, all four removals failed on one arithmetic assertion
    identically, and none through the guard being tested). Removing any one
    of the four literal spellings from `PHASES` now turns THAT SPELLING's
    own call into an `AssertionError`, fired at the removed name — run once
    per name removed, exercised by hand and reported in the task report
    rather than shipped as a mutated permanent test."""
    import json

    from publishable.apparatus import append_observation

    for phase in ("run_start", "pre_execution", "dry_run", "freeze"):
        append_observation(tmp_path, phase=phase, condition="00_x", probe="p", facts={})
    lines = [
        json.loads(line)
        for line in (tmp_path / "apparatus" / "probes.jsonl").read_text().splitlines()
    ]
    assert len(lines) == 4
    assert [line["phase"] for line in lines] == [
        "run_start",
        "pre_execution",
        "dry_run",
        "freeze",
    ]


def test_append_observation_refuses_a_fifth_spelling_before_writing_anything(tmp_path):
    """The re-measured claim this task closes: at this branch's own prior
    commit, this same call wrote `"BOGUS_FIFTH_SPELLING"` verbatim to
    `probes.jsonl` — the docstring's "closed vocabulary of four" was an
    unenforced claim. Now it raises `AssertionError` before the `mkdir`
    even runs, naming the offending value and all four legal names, and
    leaves no line on disk. Mutation M6's non-mutated arm: moving the
    assert below the write (exercised by hand, reported in the task
    report) would still raise but leave the bogus line behind — only the
    ledger's own content distinguishes the two placements."""
    from publishable.apparatus import append_observation

    with pytest.raises(AssertionError) as excinfo:
        append_observation(
            tmp_path, phase="BOGUS_FIFTH_SPELLING", condition="00_x", probe="p", facts={}
        )
    message = str(excinfo.value)
    assert "BOGUS_FIFTH_SPELLING" in message
    for name in ("run_start", "pre_execution", "dry_run", "freeze"):
        assert name in message
    assert not (tmp_path / "apparatus" / "probes.jsonl").exists()


def test_cli_and_runner_call_sites_pass_the_named_constants():
    """Enumerated by READING `cli.py` and `runner.py` for every place a
    `phase` string can originate (§ Answering a question with a proxy: a
    grep for one spelling is the fourth proxy and shipped a credential
    leak once already) and confirmed afterwards with a grep for `phase=`
    across `src/publishable/*.py`, in that order: exactly two core call
    sites pass a phase at all — `cli.command_run`'s run-start round and
    `runner.execute_plan`'s per-execution round — and both now read a
    constant rather than a literal, checked here by source inspection so a
    reversion of EITHER OF THESE TWO SITES back to a bare string fails
    this test rather than only failing silently under `python -O`.

    **This pin's own scope is an ENUMERATED list of function bodies**, not
    a module and not one function (batch B2 review, Minor 3; RETARGETED
    2026-08-23 by controller ruling after H9a task 2 moved the run-start
    round out of `command_run` into `_execute_prepared`). A hypothetical
    THIRD literal call site added elsewhere in `src/publishable/` would
    still not be caught here; the completeness claim ("there is no third
    site") rests on the reading-then-grep enumeration in the task report,
    not on this assertion alone.

    **Why an enumeration rather than the module's whole source.** Reading
    the module would keep passing when a call site moves — which is what
    just happened, and the second assertion below then passed VACUOUSLY,
    because a literal absent from `command_run` is absent from it whether
    the call site is there or not. An enumeration fails loudly when the
    site moves, which is the moment a human should re-aim the pin. The
    positive assertion is what makes the negative one non-vacuous: the
    constant must be present in the same text the literal must be absent
    from."""
    import inspect

    from publishable import cli as cli_mod
    from publishable import runner as runner_mod

    # The enumerated bodies the run-start round may legally live in. A move
    # to a function not on this list fails the positive assertion below.
    cli_source = "\n".join(
        inspect.getsource(fn)
        for fn in (
            cli_mod.command_run,
            cli_mod._prepare_run,
            cli_mod._execute_prepared,
        )
    )
    assert "phase=apparatus.PHASE_RUN_START" in cli_source
    assert 'phase="run_start"' not in cli_source

    runner_source = inspect.getsource(runner_mod.execute_plan)
    assert "phase=apparatus.PHASE_PRE_EXECUTION" in runner_source
    assert 'phase="pre_execution"' not in runner_source


# --- Fix round 1, Major 2: the surviving shape of `append_observation`'s
# assert firing, pinned by a real run rather than left only in a docstring


def test_the_run_start_fire_leaves_no_run_yaml_no_executions_and_no_lock(
    installed, registries, tmp_path, monkeypatch
):
    """The docstring's run-start half, re-measured for this fix round rather
    than carried a second time: `append_observation`'s assert is the
    function's FIRST statement, above the `mkdir`, so `apparatus/` cannot
    exist when it fires on the run-start round — the earlier docstring's
    claim that it did was carried from a differently-labelled measurement
    (batch B2 review, Major 2) and has since been deleted rather than
    rewritten. What is pinned here is only what was independently
    re-measured: the traceback is uncaught, `run.yaml` and
    `executions.jsonl` are both absent, and `lock` is gone."""
    from tests.test_cli import run_a_project

    import publishable.apparatus as apparatus_mod

    site = installed(
        "dist-fix1-a", "1.0", {"publishable.probes": {"h8b_t1_probe": "fix1a_probe_mod:probe"}}
    )
    (site / "fix1a_probe_mod.py").write_text(_H8B_T1_PROBE_MODULE)

    real_append = apparatus_mod.append_observation
    calls = {"n": 0}

    def patched(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise AssertionError("fix-round-1 probe: forced run-start fire")
        return real_append(*args, **kwargs)

    monkeypatch.setattr(apparatus_mod, "append_observation", patched)

    with pytest.raises(AssertionError, match="forced run-start fire"):
        run_a_project(
            tmp_path,
            experiment_type="h8b_t1_assay",
            parameters={"instrument": {"model": "m1"}},
            sweep={"grid": {"instrument.model": ["m1", "m2"]}},
            _local_template=_H8B_T1_TEMPLATE,
            expect_exit=1,
        )

    run_dirs = list((tmp_path / "results").glob("run_*"))
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert not (run_dir / "run.yaml").exists()
    assert not (run_dir / "executions.jsonl").exists()
    assert not (run_dir / "lock").exists()


def test_a_later_pre_execution_fire_leaves_one_paid_execution_and_no_run_yaml(
    installed, registries, tmp_path, monkeypatch
):
    """The docstring's later-`pre_execution`-fire half: one execution already
    paid for, `run.yaml` absent, `lock` gone — `CLAUDE.md`'s own phrase,
    measured rather than quoted. The fourth `append_observation` call (two
    run-start calls, then the first execution's `pre_execution` call) is
    where the fire lands under this template's two-condition sweep."""
    from tests.test_cli import run_a_project

    import publishable.apparatus as apparatus_mod

    site = installed(
        "dist-fix1-b", "1.0", {"publishable.probes": {"fix1b_probe": "fix1b_probe_mod:probe"}}
    )
    (site / "fix1b_probe_mod.py").write_text(
        _H8B_T1_PROBE_MODULE.replace("h8b_t1_probe", "fix1b_probe")
    )
    template = _H8B_T1_TEMPLATE.replace("h8b_t1_probe", "fix1b_probe").replace(
        "h8b_t1_assay", "fix1b_assay"
    )

    real_append = apparatus_mod.append_observation
    calls = {"n": 0}

    def patched(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 4:
            raise AssertionError("fix-round-1 probe: forced later pre_execution fire")
        return real_append(*args, **kwargs)

    monkeypatch.setattr(apparatus_mod, "append_observation", patched)

    with pytest.raises(AssertionError, match="forced later pre_execution fire"):
        run_a_project(
            tmp_path,
            experiment_type="fix1b_assay",
            parameters={"instrument": {"model": "m1"}},
            sweep={"grid": {"instrument.model": ["m1", "m2"]}},
            _local_template=template,
            expect_exit=1,
        )

    run_dirs = list((tmp_path / "results").glob("run_*"))
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert not (run_dir / "run.yaml").exists()
    assert not (run_dir / "lock").exists()
    executions = (run_dir / "executions.jsonl").read_text().splitlines()
    assert len(executions) == 1

# tests/test_validate.py
from pathlib import Path

import pytest
import yaml

from publishable.diagnostics import Collector
from publishable.validate import validate_config


def base_config(tmp_path: Path) -> dict:
    return {
        "schema_version": "1.0",
        "experiment_type": "generic",
        "template_version": "1.0.0",
        "plugin": None,
        "metadata": {"name": "cohort-pilot", "description": "a pilot", "authors": ["A"]},
        "entrypoint": "cohort_pilot.experiment:CohortPilotExperiment",
        "data": {
            "input_dir": str(tmp_path / "input"),
            "output_dir": str(tmp_path / "results"),
            "input_manifest_policy": "hash_all",
        },
        "parameters": {
            "analysis": {
                "method": "pearson",
                "min_samples": 30,
                "confidence": 0.95,
                "drop_missing": True,
            }
        },
        "replication": {"repeats": [{"kind": "seed", "n": 5}], "order": "as_declared"},
    }


@pytest.fixture
def write_config(git_repo: Path, tmp_path: Path):
    (tmp_path / "input").mkdir(exist_ok=True)
    (tmp_path / "input" / "index.csv").write_text("patient_id\np1\n")

    def _write(overrides: dict | None = None) -> Path:
        doc = base_config(tmp_path)
        for dotted, value in (overrides or {}).items():
            node = doc
            *heads, leaf = dotted.split(".")
            for h in heads:
                node = node[h]
            if value is _DELETE:
                del node[leaf]
            else:
                node[leaf] = value
        path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(doc))
        return path

    return _write


_DELETE = object()


def codes(path: Path) -> set[str]:
    c = Collector()
    validate_config(path, c)
    return {f.code for f in c.findings}


def messages_by_code(path: Path) -> dict[str, str]:
    c = Collector()
    validate_config(path, c)
    return {f.code: f.message for f in c.findings}


def test_a_valid_config_reports_nothing(write_config):
    assert codes(write_config()) == set()


def test_an_empty_description_is_required(write_config):
    assert "E-META-REQUIRED" in codes(write_config({"metadata.description": ""}))


def test_an_unknown_key_is_a_typo_by_construction(write_config):
    path = write_config()
    doc = yaml.safe_load(path.read_text())
    doc["parameters"]["analysis"]["min_sample"] = 30
    path.write_text(yaml.safe_dump(doc))
    assert "E-PARAM-UNKNOWN" in codes(path)


def test_values_are_checked_not_just_presence(write_config):
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.confidence": 1.4}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.method": "pearsonn"}))
    assert "E-PARAM-VALUE" in codes(write_config({"parameters.analysis.min_samples": "30"}))


def test_a_missing_parameter_is_reported():
    """`generic`'s parameters all carry defaults, so no config it accepts can be missing
    one — deleting `analysis.method` from the fixture just falls back to its default and
    reports nothing. Exercised directly against a stub template with a required
    parameter, the same pattern as the repeat-floor test below."""
    from publishable.param import Param
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_parameters

    class Benchmark(BaseTemplate):
        parameter_spec = {"analysis.method": Param(str)}

    c = Collector()
    _check_parameters({"parameters": {}}, Benchmark(), c)
    assert "E-PARAM-MISSING" in {f.code for f in c.findings}


def test_the_name_must_match_the_pattern_and_the_directory(write_config):
    assert "E-NAME-PATTERN" in codes(write_config({"metadata.name": "Cohort_Pilot"}))
    assert "E-NAME-DIR" in codes(write_config({"metadata.name": "cohort-pilot-v2"}))


def test_an_uninstalled_template_is_fatal(write_config):
    assert "E-TEMPLATE-UNKNOWN" in codes(write_config({"experiment_type": "llm_diagnostic"}))


def test_data_may_not_resolve_inside_the_repo(write_config, git_repo: Path):
    inside = str(git_repo / "results")
    assert "E-DATA-IN-REPO" in codes(write_config({"data.output_dir": inside}))


def test_an_unreadable_input_dir_is_reported(write_config, tmp_path: Path):
    assert "E-DATA-UNREADABLE" in codes(
        write_config({"data.input_dir": str(tmp_path / "absent")})
    )


def test_a_moved_template_version_warns_rather_than_failing(write_config):
    found = codes(write_config({"template_version": "0.9.0"}))
    assert "W-TEMPLATE-VERSION" in found


def test_a_repeat_count_below_one_executes_nothing_and_is_an_error(write_config):
    assert "E-REPL-N" in codes(write_config({"replication.repeats": [{"kind": "seed", "n": 0}]}))


def test_two_bad_repeat_levels_are_both_reported():
    """`_check_replication` collects rather than stopping, so a config with two invalid
    levels must not report only the first."""
    from publishable.templates.builtin.generic import GenericTemplate
    from publishable.validate import _check_replication

    doc = {
        "replication": {
            "repeats": [
                {"kind": "seed", "n": 0},
                {"kind": "fold", "n": -1},
            ]
        }
    }
    c = Collector()
    _check_replication(doc, GenericTemplate(), c)
    found = [f for f in c.findings if f.code == "E-REPL-N"]
    assert len(found) == 2
    # an invalid design must not also produce a floor warning on top of the errors
    assert not any(f.code == "W-REPL-FLOOR" for f in c.findings)


def test_an_unexpected_error_finding_the_repo_root_is_not_swallowed(write_config, monkeypatch):
    """`_check_data`'s repo-root lookup narrows its exception handling to the one case
    that legitimately means 'the inside-the-repo question does not arise' — anything
    else must propagate rather than presenting a safety check as a clean pass."""
    import publishable.validate as validate_mod

    def _boom(path):
        raise RuntimeError("disk fell off")

    monkeypatch.setattr(validate_mod, "find_repo_root", _boom)
    with pytest.raises(RuntimeError):
        validate_config(write_config(), Collector())


def test_a_contract_error_other_than_no_repo_is_not_swallowed(write_config, monkeypatch):
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _boom(path):
        raise ContractError("something else went wrong", code="E-SOMETHING-ELSE")

    monkeypatch.setattr(validate_mod, "find_repo_root", _boom)
    with pytest.raises(ContractError):
        validate_config(write_config(), Collector())


def test_the_genuine_no_repo_case_returns_quietly(write_config, monkeypatch):
    """The one case the narrowed handler is for: no repo at all is not a data-in-repo
    problem, so it must return without a spurious finding rather than propagating."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    assert codes(write_config()) == set()


def test_the_policy_check_still_runs_with_no_repo_at_all(write_config, monkeypatch):
    """`input_manifest_policy` has nothing to do with the repo, so it must not be
    gated behind the repo-existence early-return `_check_data` takes for the
    in-repo-only checks."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    codes_found = codes(write_config({"data.input_manifest_policy": "bogus"}))
    assert "E-DATA-POLICY" in codes_found


def test_a_config_that_does_not_parse_is_fatal(git_repo: Path):
    path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("metadata: [unbalanced\n")
    assert "E-CONFIG-PARSE" in codes(path)


def test_a_required_data_dir_left_empty_is_reported(write_config):
    c = Collector()
    validate_config(write_config({"data.output_dir": ""}), c)
    found = [f for f in c.findings if f.code == "E-DATA-REQUIRED"]
    assert len(found) == 1
    assert found[0].path == "data.output_dir"


def test_a_relative_input_dir_is_rejected(write_config):
    assert "E-DATA-NOT-ABSOLUTE" in codes(write_config({"data.input_dir": "./secret"}))


def test_a_relative_output_dir_is_rejected(write_config):
    assert "E-DATA-NOT-ABSOLUTE" in codes(write_config({"data.output_dir": "results"}))


def test_a_missing_data_dir_is_reported_even_outside_any_repo(write_config, monkeypatch):
    """The previous fix wave hoisted `E-DATA-IN-REPO`'s policy check above the
    repo-existence early return but left `E-DATA-REQUIRED` and `E-DATA-UNREADABLE`
    behind it under identical reasoning — neither has anything to do with the repo
    either, so a repo-less config missing `input_dir` must still be caught."""
    import publishable.validate as validate_mod
    from publishable.errors import ContractError

    def _no_repo(path):
        raise ContractError("no git repository found", code="E-GIT-NO-REPO")

    monkeypatch.setattr(validate_mod, "find_repo_root", _no_repo)
    found = codes(write_config({"data.input_dir": _DELETE}))
    assert "E-DATA-REQUIRED" in found


def _with_doc_change(write_config, change) -> Path:
    """Set a top-level key the base fixture does not declare at all — the dotted
    override helper needs the parent key to preexist, which `sweep` and
    `data.units` deliberately do not in the base fixture."""
    path = write_config()
    doc = yaml.safe_load(path.read_text())
    change(doc)
    path.write_text(yaml.safe_dump(doc))
    return path


def test_a_declared_sweep_axis_is_refused_not_silently_ignored(write_config):
    """S1 hardcodes one condition; a config declaring `sweep.grid` must not
    validate clean and then run one condition while `run.yaml` records the sweep
    verbatim, describing an experiment that never ran."""
    sweep = {"grid": {"analysis.method": ["pearson", "spearman"]}}
    path = _with_doc_change(write_config, lambda doc: doc.update(sweep=sweep))
    assert "E-SWEEP-UNSUPPORTED" in codes(path)


def test_an_empty_sweep_block_is_not_a_sweep(write_config):
    """An empty or all-null `sweep` (the shape a generated config ships with)
    declares no axis and must not trip the refusal meant for an actual sweep."""
    path = _with_doc_change(
        write_config,
        lambda doc: doc.update(
            sweep={
                "grid": None,
                "groups": [],
                "ablate": None,
                "baseline": None,
                "paired": [],
                "sample": None,
            }
        ),
    )
    assert "E-SWEEP-UNSUPPORTED" not in codes(path)


def test_a_non_default_replication_order_is_refused_not_silently_ignored(write_config):
    """`replication.order: randomized` currently validates clean and then executes
    `as_declared` anyway — the record would say randomized while the run wasn't."""
    found = codes(write_config({"replication.order": "randomized"}))
    assert "E-REPL-ORDER-UNSUPPORTED" in found


def test_a_config_without_unimplemented_blocks_still_validates_clean(write_config):
    """The base fixture declares no sweep axis, no `data.units`, and
    `replication.order: as_declared` — none of the new refusals should fire
    against it."""
    found = codes(write_config())
    assert "E-SWEEP-UNSUPPORTED" not in found
    assert "E-REPL-ORDER-UNSUPPORTED" not in found
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_a_plain_units_block_is_now_accepted(write_config):
    """The blanket refusal is retired: S2 resolves a roster."""
    found = codes(write_config({"data.units": {"from": "index.csv", "key": "patient_id"}}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("allocation", "between", "E-DATA-ALLOCATION-UNSUPPORTED"),
        ("assign", {"arm": {"method": "random"}}, "E-DATA-ASSIGN-UNSUPPORTED"),
        ("cluster_by", "site", "E-DATA-CLUSTER-UNSUPPORTED"),
        ("weight_by", "sampling_weight", "E-DATA-WEIGHT-UNSUPPORTED"),
        ("measurements", {"by": "read_id"}, "E-DATA-MEASUREMENTS-UNSUPPORTED"),
        ("holdout", {"method": "random", "frac": 0.2}, "E-DATA-HOLDOUT-UNSUPPORTED"),
    ],
)
def test_each_unimplemented_units_subfield_is_refused_on_its_own(write_config, field, value, code):
    units = {"from": "index.csv", "key": "patient_id", field: value}
    assert code in codes(write_config({"data.units": units}))


def test_allocation_within_is_accepted_because_it_is_a_no_op_here(write_config):
    units = {"from": "index.csv", "key": "patient_id", "allocation": "within"}
    assert "E-DATA-ALLOCATION-UNSUPPORTED" not in codes(write_config({"data.units": units}))


def test_a_resolver_source_is_refused_until_plugins_exist(write_config):
    units = {"from": {"resolver": "plate_wells"}, "key": "well"}
    assert "E-DATA-RESOLVER-UNSUPPORTED" in codes(write_config({"data.units": units}))


@pytest.mark.parametrize(
    "units",
    [
        {"from": {"resolver": "plate_wells"}, "key": "well"},
        {"from": "index.csv", "key": "patient_id", "allocation": "between"},
        {"from": "index.csv", "key": "patient_id", "assign": {"arm": {"method": "random"}}},
        {"from": "index.csv", "key": "patient_id", "cluster_by": "site"},
        {"from": "index.csv", "key": "patient_id", "weight_by": "sampling_weight"},
        {"from": "index.csv", "key": "patient_id", "measurements": {"by": "read_id"}},
        {"from": "index.csv", "key": "patient_id", "holdout": {"method": "random", "frac": 0.2}},
    ],
)
def test_every_unsupported_message_defers_rather_than_scolds(write_config, units):
    """The `-UNSUPPORTED` family exists so a refusal reads as 'not built yet', not as
    'your config is wrong'. Every message in this family must say so explicitly, or a
    user has no way to tell a refusal from a validation error."""
    found = messages_by_code(write_config({"data.units": units}))
    unsupported = {code: msg for code, msg in found.items() if code.endswith("-UNSUPPORTED")}
    assert unsupported, f"expected an -UNSUPPORTED finding for {units}"
    for code, message in unsupported.items():
        assert "later slice" in message, f"{code} message does not defer: {message!r}"


def test_a_null_subfield_is_not_a_declaration(write_config):
    """`init` writes these as null; null must not trip a refusal."""
    units = {
        "from": "index.csv",
        "key": "patient_id",
        "cluster_by": None,
        "weight_by": None,
        "measurements": None,
        "holdout": None,
    }
    found = codes(write_config({"data.units": units}))
    assert not [c for c in found if c.endswith("-UNSUPPORTED")]


def test_a_missing_entrypoint_is_reported(write_config):
    """A config `validate` blesses must be one `run` can actually execute — deleting
    `entrypoint` used to pass validation and then die inside `run` with a bare
    `KeyError`."""
    assert "E-ENTRYPOINT-REQUIRED" in codes(write_config({"entrypoint": _DELETE}))


def test_an_empty_entrypoint_is_reported(write_config):
    assert "E-ENTRYPOINT-REQUIRED" in codes(write_config({"entrypoint": ""}))


def test_a_missing_input_manifest_policy_is_reported(write_config):
    """Same gap, different field: deleting `data.input_manifest_policy` used to pass
    validation and then die inside `run` with a bare `KeyError`."""
    assert "E-DATA-POLICY" in codes(write_config({"data.input_manifest_policy": _DELETE}))


def test_an_unknown_input_manifest_policy_is_reported(write_config):
    """Setting it to a value outside `manifest.POLICIES` used to reach `manifest.py`
    and raise a bare `ValueError` that `main` does not catch."""
    assert "E-DATA-POLICY" in codes(write_config({"data.input_manifest_policy": "bogus"}))


def test_a_template_cross_field_rule_is_reported(write_config, monkeypatch):
    """`generic` has no cross-field rule of its own, so `E-TEMPLATE-RULE` is exercised
    through a stub template swapped in for the registry lookup `validate_config` makes."""
    import publishable.validate as validate_mod
    from publishable.templates.builtin.generic import GenericTemplate

    class RuleBreaker(GenericTemplate):
        def validate(self, config):
            return ["a cross-field rule was broken"]

    monkeypatch.setattr(validate_mod, "get_template", lambda name: RuleBreaker())
    assert "E-TEMPLATE-RULE" in codes(write_config())


def test_falling_below_the_repeat_floor_warns():
    """Exercised directly: `generic`'s floor is 1, so no legal count can breach it.

    Routing this through `validate_config` would need a template that does not
    exist yet, and asserting the warning against an illegal `n: 0` would be
    testing the error path while claiming to test the floor.
    """
    from publishable.templates.base import BaseTemplate
    from publishable.validate import _check_replication

    class Benchmark(BaseTemplate):
        default_repeats = 5

    c = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 3}]}}, Benchmark(), c)
    findings = [f for f in c.findings if f.code == "W-REPL-FLOOR"]
    assert len(findings) == 1
    assert "3" in findings[0].message and "5" in findings[0].message

    clean = Collector()
    _check_replication({"replication": {"repeats": [{"kind": "seed", "n": 5}]}}, Benchmark(), clean)
    assert clean.findings == []

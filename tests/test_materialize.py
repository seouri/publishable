import pytest
import yaml

from publishable.materialize import materialize_config
from publishable.param import Param
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template


class _OneParamTemplate(BaseTemplate):
    def __init__(self, default: str) -> None:
        self.parameter_spec = {"analysis.value": Param(str, default=default)}


def rendered() -> str:
    return materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir="/secure/data/cohort-2026",
        output_dir="/secure/results/cohort-pilot",
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )


def test_every_parameter_is_materialized_with_its_default():
    doc = yaml.safe_load(rendered())
    assert doc["parameters"]["analysis"] == {
        "method": "pearson",
        "min_samples": 30,
        "confidence": 0.95,
        "drop_missing": True,
    }


def test_the_four_identifying_fields_are_present():
    doc = yaml.safe_load(rendered())
    assert doc["schema_version"] == "1.0"
    assert doc["experiment_type"] == "generic"
    assert doc["template_version"] == "1.0.0"
    assert doc["plugin"] is None


def test_constraints_arrive_as_inline_comments():
    text = rendered()
    assert "# choices: pearson | spearman | kendall" in text
    assert "# integer >= 2" in text
    assert "# float in (0, 1)" in text


def test_limits_carry_the_documented_defaults():
    doc = yaml.safe_load(rendered())
    assert doc["limits"] == {
        "max_executions": 500,
        "max_failed_fraction": 0.2,
        "max_ineligible_fraction": 0.5,
        "min_units_per_cell": 20,
        "min_clusters": 10,
        "min_reported_n": 10,
    }


def test_s1_omits_the_units_block_because_resolution_is_s2():
    doc = yaml.safe_load(rendered())
    assert "units" not in doc["data"]
    assert doc["data"]["input_manifest_policy"] == "hash_all"


def test_replication_defaults_to_five_seed_repeats():
    doc = yaml.safe_load(rendered())
    assert doc["replication"]["repeats"] == [{"kind": "seed", "n": 5}]
    assert doc["replication"]["order"] == "as_declared"


def _rendered_with_default(default: str) -> str:
    return materialize_config(
        template=_OneParamTemplate(default),
        template_name="one-param",
        name="one-param-pilot",
        input_dir="/secure/data",
        output_dir="/secure/results",
        entrypoint="one_param.experiment:OneParamExperiment",
    )


def test_an_empty_string_default_round_trips_to_empty_string_not_null():
    doc = yaml.safe_load(_rendered_with_default(""))
    assert doc["parameters"]["analysis"]["value"] == ""


@pytest.mark.parametrize("default", ["yes", "null", "1.5"])
def test_yaml_lookalike_string_defaults_round_trip_as_strings(default: str):
    doc = yaml.safe_load(_rendered_with_default(default))
    value = doc["parameters"]["analysis"]["value"]
    assert value == default
    assert isinstance(value, str)


def test_a_default_containing_colon_space_still_parses_intact():
    doc = yaml.safe_load(_rendered_with_default("ratio: 1"))
    assert doc["parameters"]["analysis"]["value"] == "ratio: 1"


class _KeysTemplate(BaseTemplate):
    def __init__(self, *paths: str) -> None:
        self.parameter_spec = {path: Param(int, default=1) for path in paths}


def _rendered_with_keys(*paths: str) -> str:
    return materialize_config(
        template=_KeysTemplate(*paths),
        template_name="keys",
        name="keys-pilot",
        input_dir="/secure/data",
        output_dir="/secure/results",
        entrypoint="keys.experiment:KeysExperiment",
    )


def test_bool_and_null_lookalike_keys_round_trip_as_strings():
    doc = yaml.safe_load(_rendered_with_keys("t.yes", "t.null"))
    keys = list(doc["parameters"]["t"])
    assert set(keys) == {"yes", "null"}
    for key in keys:
        assert type(key) is str


def test_a_number_lookalike_key_round_trips_as_a_string():
    doc = yaml.safe_load(_rendered_with_keys("t.2024"))
    (key,) = doc["parameters"]["t"]
    assert key == "2024"
    assert type(key) is str


def test_generic_keys_that_need_no_quoting_still_emit_bare():
    text = rendered()
    assert "  analysis:" in text
    assert any(
        line.strip().startswith("method:") for line in text.splitlines()
    ), "method: must render bare, not \"method\":"


def test_a_non_two_segment_parameter_path_fails_loudly():
    class BadTemplate(BaseTemplate):
        parameter_spec = {"threshold": Param(int, default=1)}

    with pytest.raises(ValueError, match="threshold"):
        materialize_config(
            template=BadTemplate(),
            template_name="bad",
            name="bad-pilot",
            input_dir="/secure/data",
            output_dir="/secure/results",
            entrypoint="bad.experiment:BadExperiment",
        )

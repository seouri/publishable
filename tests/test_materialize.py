import pytest
import yaml

from publishable.materialize import materialize_config
from publishable.param import Param
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template


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

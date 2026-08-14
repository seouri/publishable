import copy
import re
from pathlib import Path

import pytest
import yaml

from publishable.diagnostics import Collector
from publishable.errors import ContractError
from publishable.materialize import materialize_config
from publishable.param import Param
from publishable.replication import resolve_repeats
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template
from publishable.validate import validate_config


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


def test_the_generated_config_declares_a_unit_roster():
    doc = yaml.safe_load(rendered())
    units = doc["data"]["units"]
    assert units["from"] == "index.csv"
    assert units["key"] == "patient_id"
    assert units["attributes"] == []
    assert units["allocation"] == "within"
    for optional in ("cluster_by", "weight_by", "measurements", "holdout"):
        assert units[optional] is None, f"{optional} must be null, not absent or declared"


def test_the_generated_units_block_carries_its_comments():
    text = rendered()
    assert '# index.csv | {glob: "*.dcm"}' in text
    assert "# within | between" in text


_MARKED_LATER_SLICE = re.compile(
    r"#\s*(?P<live>[\w.]+)\s*\(\s*(?P<later>[^:]+):\s*later slice\s*\)"
)

# Where a marked field lives in the parsed doc, and how to ask core whether a
# given value there is refused. `kind` is only refused at `resolve_repeats` (it
# is not read by `validate_config` at all), so it gets its own probe.
# `allocation` was here until task 17 retired `E-DATA-ALLOCATION-UNSUPPORTED`:
# `between` is built and runs end to end, so `init`'s comment no longer marks
# it, and this dict no longer carries a path for it.
_MARKED_FIELD_PATHS: dict[str, tuple[object, ...]] = {
    "kind": ("replication", "repeats", 0, "kind"),
}


def _refusal_codes(key: str, doc: dict, config_path: Path) -> list[str]:
    if key == "kind":
        try:
            resolve_repeats(doc, "digest")
        except ContractError as exc:
            return [exc.code]
        return []
    config_path.write_text(yaml.safe_dump(doc))
    c = Collector()
    validate_config(config_path, c)
    return [f.code for f in c.findings]


def test_no_enum_comment_names_a_value_validate_or_run_would_refuse(git_repo, tmp_path):
    """Every `(x: later slice)` marking must be honored by core, and the value

    `init` actually writes must never be one of the marked ones — a comment
    that lies in either direction sends a user into a refusal for nothing.
    """
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "index.csv").write_text("patient_id\np1\n")
    output_dir = tmp_path / "output"

    text = materialize_config(
        template=get_template("generic"),
        template_name="generic",
        name="cohort-pilot",
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        entrypoint="cohort_pilot.experiment:CohortPilotExperiment",
    )
    base_doc = yaml.safe_load(text)
    base_doc["metadata"]["description"] = "a pilot"
    base_doc["metadata"]["authors"] = ["A"]

    config_path = git_repo / "configs" / "cohort-pilot" / "config.yaml"
    config_path.parent.mkdir(parents=True)

    # The config `init` actually writes must validate and run clean.
    assert _refusal_codes("allocation", base_doc, config_path) == []
    assert _refusal_codes("kind", base_doc, config_path) == []
    assert _refusal_codes("order", base_doc, config_path) == []

    marked_keys_seen = set()
    for line in text.splitlines():
        m = _MARKED_LATER_SLICE.search(line)
        if not m:
            continue
        pre = line.split("#")[0]
        key_match = re.search(r"(\w+):\s*\S", pre)
        assert key_match, f"could not find a key on the marked line: {line!r}"
        key = key_match.group(1)
        assert key in _MARKED_FIELD_PATHS, (
            f"`{key}` marks a value as a later slice but has no path registered in "
            f"this test — add one to _MARKED_FIELD_PATHS"
        )
        marked_keys_seen.add(key)
        path = _MARKED_FIELD_PATHS[key]
        for value in (v.strip() for v in m["later"].split(",")):
            doc = copy.deepcopy(base_doc)
            node = doc
            for step in path[:-1]:
                node = node[step]
            node[path[-1]] = value
            codes = _refusal_codes(key, doc, config_path)
            assert codes, (
                f"comment marks `{key}={value}` as refused later, but core accepted "
                f"it silently — the marking is stale (or the value is supported now, "
                f"and the comment should say so instead of hiding it)"
            )

    assert marked_keys_seen == set(_MARKED_FIELD_PATHS), (
        "expected a `(...: later slice)` marking for each of "
        f"{sorted(_MARKED_FIELD_PATHS)}; saw {sorted(marked_keys_seen)}"
    )


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


def test_generic_method_value_emits_bare_matching_the_specification():
    text = rendered()
    assert "method: pearson" in text
    assert 'method: "pearson"' not in text


def test_generic_non_string_values_emit_bare():
    text = rendered()
    assert "min_samples: 30" in text
    assert "confidence: 0.95" in text
    assert "drop_missing: true" in text


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

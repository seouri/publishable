import pytest

from publishable import ContractError
from publishable.config import Config


def cfg() -> Config:
    return Config({
        "parameters": {"analysis": {"method": "pearson", "min_samples": 30}},
        "metadata": {"name": "cohort-pilot"},
        "sweep": {"grid": {"analysis.method": ["spearman"]}},
    })


def test_dot_access_walks_nested_mappings():
    assert cfg().parameters.analysis.method == "pearson"
    assert cfg().parameters.analysis.min_samples == 30


def test_a_path_the_config_does_not_hold_raises_with_the_nearest_key():
    with pytest.raises(ContractError) as e:
        _ = cfg().parameters.analysis.min_sample
    assert "parameters.analysis.min_sample" in str(e.value)
    assert "min_samples" in str(e.value)
    assert e.value.code == "E-STEP-PARAM-UNKNOWN"


def test_underscore_names_raise_attribute_error_so_protocols_keep_working():
    c = cfg()
    with pytest.raises(AttributeError):
        _ = c.parameters._ipython_canary
    assert not hasattr(c.parameters, "_repr_html_")


def test_a_node_has_no_methods_to_shadow_a_parameter_name():
    node = Config({"parameters": {"items": 3, "values": 4, "keys": 5}}).parameters
    assert node.items == 3
    assert node.values == 4
    assert node.keys == 5

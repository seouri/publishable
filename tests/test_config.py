import pytest

from publishable import ContractError
from publishable.config import Config


def cfg() -> Config:
    return Config(
        {
            "parameters": {"analysis": {"method": "pearson", "min_samples": 30}},
            "metadata": {"name": "cohort-pilot"},
            "sweep": {"grid": {"analysis.method": ["spearman"]}},
        }
    )


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


# Whole-project review 2026-08-26, Minor: `Node` had no `__setattr__` guard, so
# `a = cfg.analysis; a.method = 'x'` SUCCEEDED and `a.method` read back `'x'`
# while every fresh `cfg.analysis.method` returned the declared value. `Unit`
# refuses both a write and a delete with a reasoned `ContractError`; `Node` now
# does too, and `CLAUDE.md` calls this surface "immutable on purpose".
#
# The property these two tests pin is NOT "an attribute write raises" — that is
# what the raise line says. It is that a held handle and a fresh access cannot
# disagree, which is the defect: the second assertion in each test reads the
# declared value back through a fresh path, so a guard that raised while
# something else had already mutated the node would still fail here.


def test_a_config_node_refuses_a_write_the_way_a_unit_does():
    c = cfg()
    node = c.parameters.analysis
    with pytest.raises(ContractError) as e:
        node.method = "kendall"
    assert e.value.code == "E-CONFIG-IMMUTABLE"
    assert "'method'" in str(e.value)
    # The half that is the actual defect: nothing moved, on the handle or
    # through a fresh access.
    assert node.method == "pearson"
    assert c.parameters.analysis.method == "pearson"
    assert cfg().parameters.analysis.method == "pearson"


def test_a_config_node_refuses_a_delete_the_way_a_unit_does():
    """`Unit` refuses `__delattr__` as well as `__setattr__`, and a delete is
    the same disagreement in the other direction: a held handle would raise
    `E-STEP-PARAM-UNKNOWN` for a path every fresh access still resolves."""
    c = cfg()
    node = c.parameters.analysis
    with pytest.raises(ContractError) as e:
        del node.method
    assert e.value.code == "E-CONFIG-IMMUTABLE"
    assert "'method'" in str(e.value)
    assert node.method == "pearson"
    assert cfg().parameters.analysis.method == "pearson"


def test_the_root_config_refuses_a_write_too_and_raw_stays_read_only():
    """The root is a `Node` subclass, so the guard has to reach it — and `raw`
    is a property, which without an inherited `__setattr__` would have been
    writable through the class's own descriptor protocol failing open."""
    c = cfg()
    for name in ("parameters", "raw", "not_a_key"):
        with pytest.raises(ContractError) as e:
            setattr(c, name, object())
        assert e.value.code == "E-CONFIG-IMMUTABLE"
    assert c.raw["parameters"]["analysis"]["method"] == "pearson"

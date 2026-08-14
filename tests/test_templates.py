from publishable import BaseTemplate, Param
from publishable.stats import UnitTable
from publishable.templates.registry import get_template


def test_generic_is_registered_and_declares_its_conventions():
    t = get_template("generic")
    assert isinstance(t, BaseTemplate)
    assert t.field_convention == "generic"
    assert t.default_repeats == 1
    assert t.required_env == []
    assert t.apparatus_probe is None


def test_generic_declares_exactly_its_four_parameters():
    spec = get_template("generic").parameter_spec
    assert list(spec) == [
        "analysis.method",
        "analysis.min_samples",
        "analysis.confidence",
        "analysis.drop_missing",
    ]
    assert spec["analysis.method"].choices == ["pearson", "spearman", "kendall"]
    assert spec["analysis.min_samples"].ge == 2


def test_an_unknown_template_is_not_resolved():
    assert get_template("llm_diagnostic") is None


def test_validate_defaults_to_no_cross_field_rules():
    class Bare(BaseTemplate):
        parameter_spec: dict[str, Param] = {}

    assert Bare().validate(None) == []


def test_the_base_aggregate_returns_nothing():
    """`{}` is the right answer for a table a template doesn't recognize — core
    calls `aggregate` once per recording step, and a pipeline can have several."""
    assert BaseTemplate().aggregate(UnitTable({"u1": {"pred": 1.0}}), None) == {}


def test_a_subclass_can_derive_from_the_table():
    class T(BaseTemplate):
        def aggregate(self, units, cfg):
            return {"total": sum(units.pred)}

    assert T().aggregate(UnitTable({"u1": {"pred": 1.0}, "u2": {"pred": 2.0}}), None) == {
        "total": 3.0
    }


def test_register_template_returns_the_class_and_records_the_name():
    """§ Creating a plugin: a local template's `@register_template` argument
    "is therefore the whole of its registration". The decorator must return the
    class unchanged — a decorator that returned the registration record would
    break `class X(BaseTemplate)` for every later reference to X."""
    from publishable import register_template
    from publishable.templates.discovery import drain_pending

    @register_template("my_assay")
    class MyAssay(BaseTemplate):
        pass

    assert MyAssay.__name__ == "MyAssay"          # returned unchanged
    assert issubclass(MyAssay, BaseTemplate)
    assert drain_pending() == [("my_assay", MyAssay)]
    assert drain_pending() == []                  # draining empties it

from publishable import BaseTemplate, Param
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

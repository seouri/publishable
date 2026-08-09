import pytest

from publishable.param import Param


def test_omitting_default_is_what_makes_a_parameter_required():
    assert Param(str).required
    assert not Param(str, default="pearson").required


def test_default_none_requires_nullable():
    with pytest.raises(ValueError, match="nullable"):
        Param(str, default=None)
    assert Param(str, default=None, nullable=True).default is None


def test_check_enforces_type_choices_and_ranges():
    assert Param(int, default=30, ge=2).check("30") is not None
    assert Param(int, default=30, ge=2).check(1) is not None
    assert Param(int, default=30, ge=2).check(30) is None
    method = Param(str, default="pearson", choices=["pearson", "spearman", "kendall"])
    assert method.check("pearsonn") is not None
    assert method.check("kendall") is None
    assert Param(float, default=0.95, gt=0, lt=1).check(1.4) is not None


def test_bool_is_not_an_int():
    assert Param(int, default=1).check(True) is not None


def test_list_is_checked_element_by_element():
    p = Param(list, item_type=float, default=[0.01, 0.03])
    assert p.check([0.1, 0.2]) is None
    assert p.check([0.1, "x"]) is not None


def test_comments_render_the_constraint_that_claims_them():
    assert Param(str, default="a", choices=["a", "b"]).comment() == "choices: a | b"
    assert Param(int, default=30, ge=2).comment() == "integer >= 2"
    assert Param(float, default=0.95, gt=0, lt=1).comment() == "float in (0, 1)"
    assert Param(bool, default=True, help="Drop missing rows").comment() == "Drop missing rows"


def test_pattern_requires_a_str_type():
    with pytest.raises(ValueError, match="pattern") as exc_info:
        Param(int, default=5, pattern=r"\d+")
    assert "pattern" in str(exc_info.value)
    assert "int" in str(exc_info.value)


def test_pattern_still_works_on_str():
    p = Param(str, default="ok", pattern=r"^[a-z]+$")
    assert p.check("ok") is None
    result = p.check("OK")
    assert result is not None
    assert "match" in result


def test_bounds_require_int_or_float_type():
    with pytest.raises(ValueError, match="ge/gt/le/lt"):
        Param(str, default="a", ge=2)
    with pytest.raises(ValueError, match="ge/gt/le/lt"):
        Param(list, default=[], le=5)
    with pytest.raises(ValueError, match="ge/gt/le/lt"):
        Param(bool, default=True, gt=0)


@pytest.mark.parametrize("bad_value", [123, None, []])
def test_check_never_raises_on_a_mistyped_value(bad_value):
    for param in (
        Param(str, default="ok", pattern=r"^[a-z]+$"),
        Param(int, default=5, ge=0),
        Param(float, default=0.5, gt=0, lt=1),
        Param(list, item_type=float, default=[0.1]),
    ):
        result = param.check(bad_value)
        assert result is None or isinstance(result, str)

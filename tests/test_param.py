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

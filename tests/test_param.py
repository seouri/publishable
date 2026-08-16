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


def test_requires_env_is_stored_and_needs_choices():
    """The keyword `Param.__init__` rejects today. `choices` is required because a
    credential requirement is only checkable when the value set is closed —
    `reference.md` § A credential can belong to a parameter value."""
    p = Param(
        str,
        default="azure_openai",
        choices=["azure_openai", "openai", "ollama"],
        requires_env={
            "azure_openai": ["AZURE_OPENAI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "ollama": [],
        },
    )
    assert p.requires_env["openai"] == ["OPENAI_API_KEY"]
    assert p.requires_env["ollama"] == []  # `[]` is a claim, not an omission

    with pytest.raises(ValueError, match="choices"):
        Param(str, default="a", requires_env={"a": ["A_KEY"]})


def test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping():
    """`None` and `{}` are different claims — the first is "this parameter declares
    nothing", the second would be "every choice needs nothing", which is only
    legal for an empty `choices`. Tasks 10 and 11 gate on truthiness, so the
    distinction is load-bearing rather than cosmetic."""
    assert Param(str, default="a", choices=["a", "b"]).requires_env is None


def test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets():
    """Both directions, each with its own distinguishing fragment.

    `reference.md` § A credential can belong to a parameter value requires the
    message to name *both sets*; the direction clause is what makes the two
    branches separately pinnable, since both raise `ValueError` and both surface
    to a user as one `E-TEMPLATE-LOAD`.
    """
    with pytest.raises(ValueError) as short:
        Param(
            str,
            default="a",
            choices=["a", "b", "c"],
            requires_env={"a": ["A_KEY"], "b": []},
        )
    text = str(short.value)
    assert "choices are a, b, c" in text  # both sets named
    assert "requires_env names a, b" in text  # both sets named
    assert "no key for c" in text  # only the missing-key branch says this
    assert "naming no choice" not in text  # and only that branch

    with pytest.raises(ValueError) as extra:
        Param(
            str,
            default="a",
            choices=["a", "b"],
            requires_env={"a": ["A_KEY"], "b": [], "zz": ["Z_KEY"]},
        )
    text = str(extra.value)
    assert "choices are a, b" in text
    assert "requires_env names a, b, zz" in text
    assert "keys naming no choice: zz" in text  # only the unknown-key branch
    assert "no key for" not in text

    # Both directions at once, in one message: the fault a real edit makes when a
    # choice is renamed. Neither clause may swallow the other.
    with pytest.raises(ValueError) as both:
        Param(str, default="a", choices=["a", "b"], requires_env={"a": ["A_KEY"], "zz": []})
    text = str(both.value)
    assert "no key for b" in text
    assert "keys naming no choice: zz" in text


def test_a_total_requires_env_constructs_and_leaves_every_other_check_alone():
    """The honouring. Without it, ignoring `requires_env` entirely — storing it and
    checking nothing — passes every refusal test above."""
    p = Param(
        str, default=None, nullable=True, choices=["a", "b"], requires_env={"a": ["A_KEY"], "b": []}
    )
    assert p.check("a") is None
    assert p.check("zz") is not None
    assert p.check(None) is None

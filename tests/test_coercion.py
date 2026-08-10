import numpy as np
import pytest

from publishable.coercion import coerce_scalars
from publishable.errors import ContractError


def test_a_numpy_float_becomes_a_python_float():
    out = coerce_scalars({"r": np.float64(0.581)}, "io.record")
    assert out == {"r": 0.581}
    assert type(out["r"]) is float


def test_a_numpy_int_becomes_a_python_int():
    out = coerce_scalars({"n": np.int64(240)}, "io.record")
    assert out == {"n": 240}
    assert type(out["n"]) is int


def test_a_numpy_bool_becomes_a_python_bool():
    out = coerce_scalars({"ok": np.bool_(True)}, "io.record")
    assert type(out["ok"]) is bool


def test_plain_scalars_pass_through_unchanged():
    values = {"a": 1, "b": 2.5, "c": "x", "d": True, "e": None}
    assert coerce_scalars(values, "io.record") == values


def test_a_mapping_is_refused():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": {"nested": 1}}, "step03_analyze")
    assert exc.value.code == "E-STEP-RETURN-TYPE"
    assert "step03_analyze" in str(exc.value)


def test_a_list_is_refused():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": [1, 2]}, "io.record")
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_a_numpy_array_is_refused_not_coerced():
    """An array is structural even though its dtype is numeric — coercing it to a
    list would put a sequence in a cell that must hold one value."""
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": np.array([1.0, 2.0])}, "io.record")
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_the_message_names_the_key_and_the_type():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"weird": {"a": 1}}, "io.record")
    assert "weird" in str(exc.value) and "dict" in str(exc.value)

from decimal import Decimal
from enum import IntEnum
from fractions import Fraction

import numpy as np
import pytest

from publishable import Estimate
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


def test_a_decimal_becomes_a_python_float():
    out = coerce_scalars({"r": Decimal("1.5")}, "io.record")
    assert out == {"r": 1.5}
    assert type(out["r"]) is float


def test_a_fraction_becomes_a_python_float():
    out = coerce_scalars({"r": Fraction(3, 2)}, "io.record")
    assert out == {"r": 1.5}
    assert type(out["r"]) is float


def test_an_int_enum_becomes_its_python_int_value():
    class Status(IntEnum):
        OK = 1

    out = coerce_scalars({"status": Status.OK}, "io.record")
    assert out == {"status": 1}
    assert type(out["status"]) is int


class _FloatyButSized:
    """Implements `__float__` and `__len__` — the case the `__len__` refusal
    fallback exists to catch: a structural object that could be talked into
    serializing as a scalar must still be refused, not coerced."""

    def __float__(self) -> float:
        return 1.0

    def __len__(self) -> int:
        return 3


def test_a_sized_object_is_refused_even_if_it_implements_float():
    with pytest.raises(ContractError) as exc:
        coerce_scalars({"r": _FloatyButSized()}, "io.record")
    assert exc.value.code == "E-STEP-RETURN-TYPE"


def test_an_estimate_passes_through_at_summary_scope():
    est = Estimate(value=0.031, ci95=[0.008, 0.055], n=612, method="mixed model, REML")
    got = coerce_scalars({"delta": est}, "step03_site_model", scope="summary")
    assert got["delta"] == est


def test_an_estimate_is_refused_at_every_other_scope():
    """`reference.md` § `Estimate`: elsewhere it "would be a way to attach an
    interval to a per-execution return value, and `per_repeat` is *exactly what
    the step returned*" — an interval per repeat is either a claim about one
    execution or an accident."""
    est = Estimate(value=0.031)
    for scope in ("repeat", "condition", "run"):
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"delta": est}, "step03_analyze", scope=scope)
        assert excinfo.value.code == "E-STEP-ESTIMATE-SCOPE"


def test_io_record_refuses_an_estimate_without_claiming_summary_scope_helps():
    """`io.record` never passes a `scope` — it is reachable from a `summary`
    step, which is handed the full roster, so an author already at summary
    scope must not be told an Estimate is accepted at scope `summary` only.
    This call site never accepts an Estimate at all; the refusal is the same
    `E-STEP-RETURN-TYPE` any other structural value gets."""
    est = Estimate(value=0.031)
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"d": est}, "io.record")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"
    assert "summary" not in str(excinfo.value)


def test_template_aggregate_refuses_an_estimate_without_claiming_summary_scope_helps():
    """`reference.md` § "There is no `Estimate` exception here" for a
    template's `aggregate` — the call site never passes `scope`, and telling
    its author "accepted at scope `summary` only" would point at a door that
    does not exist for this surface."""
    est = Estimate(value=0.031)
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"r": est}, "template aggregate")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"
    assert "summary" not in str(excinfo.value)


def test_ci95_without_method_is_refused():
    """`reference.md`: "`method` is required whenever `ci95` is present. An
    interval nobody labelled is unreadable." The check is a declaration check,
    not a judgement about the statistics."""
    est = Estimate(value=0.031, ci95=[0.008, 0.055])
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"delta": est}, "step03_site_model", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-METHOD"


def test_a_bare_estimate_without_ci95_needs_no_method():
    got = coerce_scalars({"delta": Estimate(value=0.031)}, "s", scope="summary")
    assert got["delta"].method is None


def test_an_estimates_own_fields_are_coerced():
    """The half a narrower exemption would miss. `coerce_scalars` exists because
    an uncoerced NumPy scalar "reaches `yaml.safe_dump` and raises
    `RepresenterError` while writing `run.yaml` — a traceback rather than a
    diagnostic", and a mixed model hands back NumPy scalars more often than a
    derived metric does, not less. Passing the Estimate through untouched would
    reintroduce that defect one level of nesting down."""
    est = Estimate(
        value=np.float64(0.031),
        ci95=[np.float64(0.008), np.float64(0.055)],
        n=np.int64(612),
        method="mixed model, REML",
    )
    got = coerce_scalars({"delta": est}, "step03_site_model", scope="summary")["delta"]
    assert type(got.value) is float
    assert [type(v) for v in got.ci95] == [float, float]
    assert type(got.n) is int
    assert got.value == 0.031


def test_something_structural_inside_an_estimate_is_still_refused():
    """The exemption admits an `Estimate`, not everything inside one — this is
    the same field-coercion refusal any other structural value gets, not an
    interval-labelling refusal, so the code must be `E-STEP-RETURN-TYPE`."""
    est = Estimate(value=[0.031], method="m")  # type: ignore[arg-type]
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"delta": est}, "step03_site_model", scope="summary")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"


def test_a_bare_value_beside_an_estimate_is_untouched():
    """The documented example returns `converged: True` alongside. A bare value
    stays bare — it is not wrapped into the Estimate shape."""
    got = coerce_scalars(
        {"delta": Estimate(value=0.031), "converged": True}, "s", scope="summary"
    )
    assert got["converged"] is True

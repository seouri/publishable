from decimal import Decimal
from enum import Enum, IntEnum
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


def test_a_ci95_that_is_not_two_elements_is_refused():
    """S5b indexes this list to read a bound. A one-element interval would raise
    an IndexError mid-run, after every execution has been spent."""
    for bad in ([0.4], [0.1, 0.2, 0.3], []):
        est = Estimate(value=0.5, ci95=bad, method="one-sided BCa")
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"d": est}, "step04_agreement", scope="summary")
        assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_a_reversed_ci95_is_refused():
    """`evaluate_on: ci95_lower` reads element 0. Reversed, it reads the upper
    bound and returns a verdict that looks authoritative and tested the wrong
    number — mechanically detectable, and not a judgement about the statistics."""
    est = Estimate(value=0.5, ci95=[0.6, 0.4], method="one-sided BCa")
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"d": est}, "step04_agreement", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_a_non_numeric_ci95_bound_is_refused():
    """`[0.1, None]` is the reachable slip — a one-sided interval writing only the
    bound it has — and before this guard it reached `coerced_ci95[0] >
    coerced_ci95[1]` and raised a raw `TypeError` in place of a diagnostic, which
    is the whole reason this module exists. A string bound got further still: it
    passed coercion and `hypotheses._tested_number` called `float()` on it in
    phase 8, after every execution was spent."""
    for bad in ([0.1, None], [None, None], [0.1, "x"], ["a", "b"], [True, 0.9]):
        est = Estimate(value=0.5, ci95=bad, method="one-sided BCa")
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"d": est}, "step04_agreement", scope="summary")
        assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_a_non_numeric_estimate_value_is_refused():
    """The Critical this closes: a `summary` step returning `Estimate(value="high")`
    plus a hypothesis naming it raised `ValueError: could not convert string to
    float` in phase 8 — before `run.yaml` was written, and `main` catches only
    `PublishableError`/`OSError`, so a real run lost every completed execution's
    record to a traceback. `str` is a scalar `_coerce_one` accepts everywhere
    else, so the narrower rule is stated here, at the point of the mistake."""
    for bad in ("high", None, True):
        est = Estimate(value=bad, method="m")  # type: ignore[arg-type]
        with pytest.raises(ContractError) as excinfo:
            coerce_scalars({"adjusted": est}, "step04_agreement", scope="summary")
        assert excinfo.value.code == "E-STEP-ESTIMATE-VALUE"


def test_an_estimates_own_n_may_still_be_a_label():
    """`n` is deliberately outside the numeric rule: no verdict is read against
    it, and a step describing its own base ("612 pairs") is describing, not
    asserting. Pins the boundary so the omission reads as a decision."""
    est = Estimate(value=0.5, n="612 pairs", method="m")  # type: ignore[arg-type]
    got = coerce_scalars({"d": est}, "step04_agreement", scope="summary")["d"]
    assert got.n == "612 pairs"


def test_an_equal_pair_is_allowed():
    """A zero-width interval is legitimate — S4b established it for a point-mass
    bootstrap — so the check is `>`, not `>=`."""
    est = Estimate(value=0.5, ci95=[0.5, 0.5], method="point mass")
    got = coerce_scalars({"d": est}, "step04_agreement", scope="summary")["d"]
    assert got.ci95 == [0.5, 0.5]


def test_a_bare_value_beside_an_estimate_is_untouched():
    """The documented example returns `converged: True` alongside. A bare value
    stays bare — it is not wrapped into the Estimate shape."""
    got = coerce_scalars({"delta": Estimate(value=0.031), "converged": True}, "s", scope="summary")
    assert got["converged"] is True


# Fixture C — the coercion branch, `str` against `bytes` (Decision 7).


def test_a_numpy_str_coerces_to_exactly_str():
    """`np.str_` is a genuine `str` subclass, so it is already one of the four
    types `_SCALARS` accepts and the only thing wrong with it is that its type
    is not exactly `str` — the identical situation `np.float64` is in.
    `type(...) is str`, not `isinstance`, because `np.str_` passes
    `isinstance(..., str)` either way and that assertion would pass unmutated."""
    out = coerce_scalars({"r": np.str_("a")}, "io.record")
    assert type(out["r"]) is str
    assert out["r"] == "a"


def test_a_numpy_bytes_is_still_refused():
    """`bytes` is NOT in `_SCALARS`, so `np.bytes_` — a `bytes` subclass with
    `__len__`, same as `np.str_` — is left to the `__len__` guard rather than
    admitted, on the same ground plain `bytes` already is."""
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"r": np.bytes_(b"a")}, "io.record")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"


def test_plain_bytes_is_refused_with_the_same_code():
    """The Python spelling of the type `np.bytes_` shares — admitting the NumPy
    spelling of a type core refuses in its Python spelling would be the
    divergence this module's one rule exists to prevent."""
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"r": b"a"}, "io.record")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"


def test_a_str_enum_member_coerces_to_its_declared_value_not_its_repr():
    """`str(Color.RED)` is `'Color.RED'` under Python 3.11+ and would corrupt
    the value silently; `str.__str__(Color.RED)` is `'red'`, the literal the
    enum declares. This is why the branch calls `str.__str__` and not `str()`."""

    class Color(str, Enum):  # noqa: UP042 — StrEnum.__str__ returns the value, not "Color.RED"; this fixture needs the mixin's corrupting __str__
        RED = "red"

    out = coerce_scalars({"c": Color.RED}, "io.record")
    assert type(out["c"]) is str
    assert out["c"] == "red"


def test_a_numpy_array_of_floats_still_raises_the_positive_control():
    """Without this control, the arms above prove only that something was
    refused — not that the `__len__` guard still does the job it exists for.
    `np.array([1.0, 2.0])` has `__float__` and `__len__` both; it must still be
    refused, never coerced to its first element."""
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"r": np.array([1.0, 2.0])}, "io.record")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"


def test_an_estimate_value_that_is_a_str_subclass_now_raises_the_more_precise_code():
    """Before this task, a `str`-subclass `value` failed `_coerce_one`'s
    exact-type test, reached the `__len__` guard (a `str` subclass has
    `__len__`), and `_coerce_one` raised `E-STEP-RETURN-TYPE` directly, which
    `_coerce_estimate` propagated unchanged. Now the new branch coerces it to
    a plain `str` before the guard, and `_is_number` then refuses a `str` on
    its own narrower ground — so the code moves to the more precise
    `E-STEP-ESTIMATE-VALUE`. The shape refuses both before and after; only
    the code moves."""

    class Color(str, Enum):  # noqa: UP042 — StrEnum.__str__ returns the value, not "Color.RED"; this fixture needs the mixin's corrupting __str__
        RED = "red"

    est = Estimate(value=Color.RED, method="m")  # type: ignore[arg-type]
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"d": est}, "step04_agreement", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-VALUE"


def test_an_estimate_ci95_bound_that_is_a_str_subclass_now_raises_the_more_precise_code():
    """Same retirement, for a `ci95` bound: it coerces to `str` and then fails
    `_is_number`, raising `E-STEP-ESTIMATE-CI95` rather than
    `E-STEP-RETURN-TYPE`."""

    class Color(str, Enum):  # noqa: UP042 — StrEnum.__str__ returns the value, not "Color.RED"; this fixture needs the mixin's corrupting __str__
        RED = "red"

    est = Estimate(value=0.5, ci95=[Color.RED, 0.9], method="m")  # type: ignore[arg-type]
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"d": est}, "step04_agreement", scope="summary")
    assert excinfo.value.code == "E-STEP-ESTIMATE-CI95"


def test_an_estimates_n_retires_the_refusal_a_str_subclass_used_to_draw():
    """A THIRD retirement (review Minor 1), distinct from `value`/`ci95` moving
    to a more precise code: `n` is held to no numeric rule (`_is_number` is
    never applied to it), so a `str`-subclass `n` does not fail a narrower
    check afterward — it simply stops being refused. Before this task an
    `np.str_` `n` reached `_coerce_one`'s `__len__` guard and raised
    `E-STEP-RETURN-TYPE` directly; now it coerces and is kept, exactly as a
    plain `str` label already was."""
    est = Estimate(value=0.5, n=np.str_("612 pairs"), method="m")  # type: ignore[arg-type]
    got = coerce_scalars({"d": est}, "step04_agreement", scope="summary")["d"]
    assert type(got.n) is str
    assert got.n == "612 pairs"


def test_a_zero_dimensional_numpy_float_array_still_raises():
    """`np.array(1.0)` has `ndim == 0` and an `item()` like a true NumPy
    scalar — the shape closest to being mistaken for one. Measured:
    `hasattr(np.array(1.0), "__len__")` is `True` even though calling
    `len(...)` on it raises `TypeError`, because `ndarray` always carries the
    method regardless of shape — so this array reaches the `__len__` guard
    and is refused there, same as a sized array, never reaching the `item()`
    unwrap a true scalar would."""
    with pytest.raises(ContractError) as excinfo:
        coerce_scalars({"r": np.array(1.0)}, "io.record")
    assert excinfo.value.code == "E-STEP-RETURN-TYPE"

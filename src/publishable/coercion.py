"""The one scalar rule, shared by every surface that accepts values.

`docs/reference.md` § Steps and artifacts: `io.record`'s `values`, a step's
return, and a template's `aggregate` take the same scalars under the same
coercion — "a table core would reject what a return accepted would be a
divergence found on the first line anyone writes." What differs between the
three is only where the value lands.

The document is explicit about the mechanism: core coerces anything
implementing `__float__`, `__index__`, or `__bool__` to the Python scalar it
stands for, keeps that, and raises `ContractError` on everything else — a
list, a dict, an array, a `DataFrame`, a fitted model. The line is
deliberately at *what the value already is* rather than at what could be
talked into serializing — which is why `__len__` is the refusal test: a
NumPy array satisfies every one of those protocols too, but it also has
`__len__`, and the document forbids coercing it.
"""

from typing import Any

from publishable.errors import ContractError

_SCALARS = (bool, int, float, str)


def coerce_scalars(values: dict[str, Any], where: str) -> dict[str, Any]:
    """Return `values` with NumPy scalars coerced; raise on anything structural.

    A per-unit value a model hands back is a `numpy.float64` at least as often
    as a derived metric is, and uncoerced it reaches `yaml.safe_dump` and raises
    `RepresenterError` while writing `run.yaml` — a traceback rather than a
    diagnostic. Anything structural is refused instead of coerced: a list or a
    mapping in a cell that must hold one value is a mistake no reshaping fixes.
    """
    out: dict[str, Any] = {}
    for key, value in values.items():
        out[key] = _coerce_one(key, value, where)
    return out


def _coerce_one(key: str, value: Any, where: str) -> Any:
    # Exact-type scalars pass through untouched. `type(value) in _SCALARS` rather
    # than `isinstance` — `numpy.float64` is a genuine subclass of `float` in
    # CPython, so an isinstance check would let it pass through un-coerced and
    # `yaml.safe_dump` would still choke on it.
    if value is None or type(value) in _SCALARS:
        return value

    # Anything with `__len__` is structural, full stop — this must come before
    # the protocol checks below, because a NumPy array satisfies `__float__`,
    # `__index__`, and `__bool__` just as a scalar does, and coercing it would
    # silently collapse a sequence to one element.
    if hasattr(value, "__len__"):
        raise _refuse(key, value, where)

    # NumPy's own scalar unwrap, tried before the generic protocols below: it
    # must come first so `numpy.bool_` lands as `bool` rather than as the `int`
    # a `__index__` fallback would produce.
    item = getattr(value, "item", None)
    if item is not None and getattr(value, "ndim", None) == 0:
        unwrapped = item()
        if isinstance(unwrapped, _SCALARS):
            return unwrapped

    # The documented protocols: `__index__` before `__float__` so an integral
    # type (an `IntEnum`, a `Fraction` with denominator 1) stays an `int`
    # rather than becoming a `float`.
    if hasattr(value, "__index__"):
        return int(value)
    if hasattr(value, "__float__"):
        return float(value)
    if hasattr(value, "__bool__"):
        return bool(value)

    raise _refuse(key, value, where)


def _refuse(key: str, value: Any, where: str) -> ContractError:
    return ContractError(
        f"{where} gave {key!r} a {type(value).__name__}; values must be a scalar — "
        "a bool, int, float, str, or None, or something core can coerce to one",
        code="E-STEP-RETURN-TYPE",
    )

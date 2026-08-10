"""The one scalar rule, shared by every surface that accepts values.

`docs/reference.md` § Steps and artifacts: `io.record`'s `values`, a step's
return, and a template's `aggregate` take the same scalars under the same
coercion — "a table core would reject what a return accepted would be a
divergence found on the first line anyone writes." What differs between the
three is only where the value lands.
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
    # `type(value) in _SCALARS` rather than `isinstance` — `numpy.float64` is a
    # genuine subclass of `float` in CPython, so an isinstance check would let it
    # pass through un-coerced and `yaml.safe_dump` would still choke on it.
    if value is None or type(value) in _SCALARS:
        return value
    item = getattr(value, "item", None)
    # `.item()` is NumPy's own scalar unwrap, and `ndim == 0` is what separates a
    # scalar from an array — an array also has `.item()` and would otherwise
    # silently collapse to its first element.
    if item is not None and getattr(value, "ndim", None) == 0:
        unwrapped = item()
        if isinstance(unwrapped, _SCALARS):
            return unwrapped
    raise ContractError(
        f"{where} gave {key!r} a {type(value).__name__}; values must be a scalar — "
        "a bool, int, float, str, or None, or a NumPy scalar core coerces to one",
        code="E-STEP-RETURN-TYPE",
    )

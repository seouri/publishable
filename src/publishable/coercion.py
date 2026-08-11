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

There is exactly one documented exception: an `Estimate` returned at
`summary` scope. `CLAUDE.md`'s invariant states it precisely — a step's
`run` and a template's `aggregate` return a flat mapping of scalars, "with a
NumPy scalar coerced, anything structural a `ContractError`, and an
`Estimate` at `summary` scope the one exception." The exception admits the
type, not what it holds: its own fields go through the same coercion as
everything else — and two of them are then held to a *narrower* rule than a
scalar anywhere else here. `value` and each `ci95` bound must be a number,
because a hypothesis naming a reported `Estimate` compares exactly those to a
`threshold`; the `str` this module accepts happily in a recorded column is,
there, a verdict nobody can read.
"""

from typing import Any

from publishable.errors import ContractError
from publishable.estimate import Estimate

_SCALARS = (bool, int, float, str)


def coerce_scalars(
    values: dict[str, Any], where: str, *, scope: str | None = None
) -> dict[str, Any]:
    """Return `values` with NumPy scalars coerced; raise on anything structural.

    A per-unit value a model hands back is a `numpy.float64` at least as often
    as a derived metric is, and uncoerced it reaches `yaml.safe_dump` and raises
    `RepresenterError` while writing `run.yaml` — a traceback rather than a
    diagnostic. Anything structural is refused instead of coerced: a list or a
    mapping in a cell that must hold one value is a mistake no reshaping fixes.

    `scope` defaults to `None`, so `io.record` and a template's `aggregate` —
    the two call sites that never pass it — keep refusing an `Estimate` exactly
    as they refuse any other structural value.
    """
    out: dict[str, Any] = {}
    for key, value in values.items():
        if isinstance(value, Estimate):
            out[key] = _coerce_estimate(key, value, where, scope)
        else:
            out[key] = _coerce_one(key, value, where)
    return out


def _coerce_estimate(key: str, value: Estimate, where: str, scope: str | None) -> Estimate:
    """The one exception to "anything structural is a `ContractError`".

    `CLAUDE.md`'s invariant: a step's `run` and a template's `aggregate` return a
    flat mapping of scalars, "with a NumPy scalar coerced, anything structural a
    `ContractError`, and an `Estimate` at `summary` scope the one exception".
    That sentence is this function's whole justification, which is why the
    exception lives here rather than being special-cased in `runner.py`: one
    place decides what a step's return may contain.

    `value` and each `ci95` bound must be a number once coerced, which is
    stricter than `_coerce_one` alone: `str` is a scalar this module accepts
    everywhere else, and `None` is what a one-sided interval writes for the
    bound it does not have. Both are refused here rather than at the read site,
    because `hypotheses._tested_number` calls `float()` on whichever of them a
    hypothesis names, in phase 8 — after every execution is spent and before
    `run.yaml` is written, so an unguarded `ValueError` there costs the whole
    record. Refusing at the return keeps the cost at the one step that made the
    mistake and names it with an identifier.

    Not every refused shape crashed, and the two reasons are worth keeping
    apart. A `str` `value`, and a `str` or `None` `ci95` bound, are the ones
    that did. A `None` `value` never reached `float()` — `_tested_number` skips
    a point estimate that is `None` — and is refused on the narrower ground
    that `Estimate.value` is declared a number and a hypothesis naming one
    would get a verdict of `null` from a field the type says cannot be empty.
    `n` is not held to this rule at all: nothing evaluates a verdict against
    it, and a step that reports its own `n` as a label ("612 pairs") is
    describing, not asserting.

    The fields are coerced, not merely passed through. A mixed model hands back
    `numpy.float64` at least as often as a derived metric does, and an uncoerced
    one reaches `yaml.safe_dump` and raises `RepresenterError` while writing
    `run.yaml` — the traceback-instead-of-diagnostic this module exists to
    prevent, one level of nesting down.

    `scope is None` is not "some other scope" — it means the call site does not
    take a scope at all. `io.record` and a template's `aggregate` never pass
    one, and neither accepts an `Estimate` under any name for it: `io.record`'s
    `values`, and `aggregate`'s return, are the flat mapping of scalars this
    module exists to enforce, full stop. Telling that author "an Estimate is
    accepted at scope `summary` only" would name a door that, for `aggregate`,
    does not exist, and for `io.record` — reachable from a `summary` step,
    which is handed the full roster — describes the scope the caller is
    already at. So `scope is None` falls straight through to the same
    `E-STEP-RETURN-TYPE` refusal any other structural value gets; only a real,
    non-`summary` step scope gets the `E-STEP-ESTIMATE-SCOPE` message below.
    """
    if scope is None:
        raise _refuse(key, value, where)
    if scope != "summary":
        raise ContractError(
            f"{where} gave {key!r} an Estimate at scope {scope!r}; an Estimate is accepted "
            "at scope `summary` only, because elsewhere it would attach an interval to one "
            "execution's return value — `per_repeat` is exactly what the step returned, and "
            "an interval per repeat is either a claim about that one execution or an accident",
            code="E-STEP-ESTIMATE-SCOPE",
        )
    if value.ci95 is not None and not value.method:
        raise ContractError(
            f"{where} gave {key!r} a ci95 with no `method`; an interval nobody labelled is "
            "unreadable, and core can enforce that a label exists without having any opinion "
            "on whether it is the right method",
            code="E-STEP-ESTIMATE-METHOD",
        )
    coerced_ci95 = (
        None if value.ci95 is None else [_coerce_one(f"{key}.ci95", v, where) for v in value.ci95]
    )
    if coerced_ci95 is not None:
        if len(coerced_ci95) != 2:
            raise ContractError(
                f"{where} gave {key!r} a ci95 of {len(coerced_ci95)} elements; an interval is "
                "exactly two, lower then upper, because a hypothesis evaluating on "
                "`ci95_lower` or `ci95_upper` reads one of them by position",
                code="E-STEP-ESTIMATE-CI95",
            )
        for position, bound in zip(("lower", "upper"), coerced_ci95, strict=True):
            if not _is_number(bound):
                raise ContractError(
                    f"{where} gave {key!r} a ci95 whose {position} bound is "
                    f"{bound!r} ({type(bound).__name__}); an interval bound must be a number, "
                    "because `evaluate_on: ci95_lower`/`ci95_upper` compares it to a "
                    "`threshold` — a `None` from a one-sided interval, or a string, is a "
                    "bound no verdict can be read against",
                    code="E-STEP-ESTIMATE-CI95",
                )
        if coerced_ci95[0] > coerced_ci95[1]:
            raise ContractError(
                f"{where} gave {key!r} a ci95 whose lower bound {coerced_ci95[0]} exceeds its "
                f"upper bound {coerced_ci95[1]}; reversed, `evaluate_on: ci95_lower` would read "
                "the upper bound and report a verdict against the wrong number",
                code="E-STEP-ESTIMATE-CI95",
            )
    coerced_value = _coerce_one(f"{key}.value", value.value, where)
    if not _is_number(coerced_value):
        raise ContractError(
            f"{where} gave {key!r} a value of {coerced_value!r} "
            f"({type(coerced_value).__name__}); an Estimate's `value` must be a number, "
            "because a hypothesis naming a reported Estimate compares it to a `threshold` — "
            "a string or a `None` there is a point estimate no verdict can be read against",
            code="E-STEP-ESTIMATE-VALUE",
        )
    return Estimate(
        value=coerced_value,
        ci95=coerced_ci95,
        n=None if value.n is None else _coerce_one(f"{key}.n", value.n, where),
        method=value.method,
    )


def _is_number(value: Any) -> bool:
    """The same predicate `hypotheses.verdict_for` applies to a `threshold`.

    A `bool` is an `int` in Python and is excluded on purpose: `True` as a point
    estimate or an interval bound is a mistake that would otherwise compare
    against a threshold as `1` and produce a real-looking verdict. Written once
    here so the value core will judge and the value core accepts cannot drift
    apart.
    """
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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

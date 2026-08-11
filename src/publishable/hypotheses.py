"""Which number a declared hypothesis is about. Pure: results and config in,
one `Observation` out.

`docs/reference.md` § Pre-registration: the config "is written before the run
and hashed at run start. That's the mechanical property pre-registration asks
for, so core lets you use it: declare what you *expect*, not only what you'll
compute."
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Observation:
    """Where a hypothesis's number came from, and the record entry holding it.

    `where` addresses the `correction.Member` that built the entry — `cond:<index>`
    or `contrast:<id>`, the same strings `cli` uses — so a later bound test can
    rebuild the interval at the hypothesis family's own level. It is `None` for a
    summary metric, which core did not compute and therefore cannot re-derive.

    `block` is `None` when nothing matched: a hypothesis may name a metric no run
    produced, because its step failed or every unit in the comparison was
    ineligible. That is recorded, not raised — `reference.md` gives no
    diagnostic for it, and a verdict of `false` would be indistinguishable from
    a claim that was tested and failed.
    """

    where: str | None
    step: str
    metric: str
    block: dict[str, Any] | None
    rests_on: str


def resolve(
    hyp: dict[str, Any],
    *,
    label_to_index: dict[str, int],
    vs_baseline: dict[int, dict[str, dict[str, Any]]] | None,
    contrasts: list[dict[str, Any]] | None,
    summary: dict[str, dict[str, Any]] | None,
) -> Observation:
    """The one number this hypothesis is about, from one of three places.

    `reference.md` § What a hypothesis is tested against: "`metric` is required
    in every form, because `compare` says *where* and never *what*." A contrast
    reports one value per step metric exactly as a condition does, so `compare`
    alone would leave the quantity under test unnamed.

    A hypothesis names a condition by label — the same grammar
    `statistics.contrasts` uses — but `where` must carry the index, because that
    is the string `cli` gave the `correction.Member` it built for that
    condition. `label_to_index` is therefore the caller's job, not this
    module's: a pure resolver has no run to look the mapping up in.
    """
    step, _, metric = str(hyp.get("metric", "")).partition(".")
    compare = hyp.get("compare")

    if not isinstance(compare, dict):
        block = (summary or {}).get(step, {}).get(metric)
        return Observation(
            where=None,
            step=step,
            metric=metric,
            block=block if isinstance(block, dict) else None,
            rests_on="reported",
        )

    if "contrast" in compare:
        cid = str(compare["contrast"])
        found = None
        for entry in contrasts or []:
            if entry.get("id") == cid:
                step_block = entry.get(step)
                found = step_block.get(metric) if isinstance(step_block, dict) else None
                break
        return Observation(
            where=f"contrast:{cid}",
            step=step,
            metric=metric,
            block=found if isinstance(found, dict) else None,
            rests_on="computed",
        )

    index = label_to_index.get(str(compare.get("condition")))
    if index is None:
        return Observation(where=None, step=step, metric=metric, block=None, rests_on="computed")
    found = (vs_baseline or {}).get(index, {}).get(step, {}).get(metric)
    return Observation(
        where=f"cond:{index}",
        step=step,
        metric=metric,
        block=found if isinstance(found, dict) else None,
        rests_on="computed",
    )


_POINT_KEYS = ("delta", "value")


def _observed_block(obs: Observation, bounds: tuple[float, float] | None) -> dict[str, Any] | None:
    """What the record shows as `observed`, in the shape its source implies.

    `reference.md` shows two: `{delta, ci95, ci95_corrected}` for a comparison and
    `{value, ci95, method}` for a summary metric. Both are the entry's own fields,
    not a reshaping of them, so a reader can find the same numbers in the block
    the hypothesis names.
    """
    if obs.block is None:
        return None
    out: dict[str, Any] = {
        k: obs.block[k] for k in ("delta", "value", "ci95", "method") if k in obs.block
    }
    if bounds is not None:
        out["ci95_corrected"] = [bounds[0], bounds[1]]
    return out


def _tested_number(
    obs: Observation, evaluate_on: str, bounds: tuple[float, float] | None
) -> float | None:
    """The one number the verdict compares, or `None` when there isn't one.

    A bound test reads the corrected interval when this hypothesis is in a
    corrected family, and the raw one otherwise — `reference.md`: "Correction
    reaches a verdict only through a bound", and counted-iff-corrected decides
    whether there is a corrected bound at all.
    """
    if obs.block is None:
        return None
    if evaluate_on == "observed":
        for key in _POINT_KEYS:
            if key in obs.block and obs.block[key] is not None:
                return float(obs.block[key])
        return None
    interval = bounds if bounds is not None else obs.block.get("ci95")
    if not interval:
        return None
    return float(interval[0] if evaluate_on == "ci95_lower" else interval[1])


def verdict_for(
    hyp: dict[str, Any], obs: Observation, bounds: tuple[float, float] | None
) -> dict[str, Any]:
    """The verdict fields for one hypothesis.

    `verdict_evaluated_on` is spelled out rather than echoing the config's
    `evaluate_on` because `reference.md` says "a record field one letter from a
    config field is a typo waiting to be read as agreement" — a reader must see
    which question was asked without reconstructing it.

    `supported` is `None`, never `False`, when there is no number to compare: a
    `False` would be indistinguishable from a claim that was tested and failed.
    """
    evaluate_on = str(hyp.get("evaluate_on") or "observed")
    number = _tested_number(obs, evaluate_on, bounds)
    threshold = hyp.get("threshold")
    supported: bool | None = None
    if (
        number is not None
        and isinstance(threshold, (int, float))
        and not isinstance(threshold, bool)
    ):
        supported = number > threshold if hyp.get("direction") == "greater" else number < threshold
    return {
        "observed": _observed_block(obs, bounds),
        "verdict_evaluated_on": evaluate_on,
        "supported": supported,
        "verdict_rests_on": obs.rests_on,
    }

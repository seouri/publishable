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

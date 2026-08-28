"""Which number a declared hypothesis is about. Pure: results and config in,
one `Observation` out.

`docs/reference.md` § Pre-registration: the config "is written before the run
and hashed at run start. That's the mechanical property pre-registration asks
for, so core lets you use it: declare what you *expect*, not only what you'll
compute."
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from publishable.correction import corrected_for

if TYPE_CHECKING:
    from publishable.correction import Member


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
    aggregated: dict[int, dict[str, dict[str, Any]]] | None,
) -> Observation:
    """The one number this hypothesis is about, from one of four places.

    `reference.md` § What a hypothesis is tested against: "`metric` is required
    in every form, because `compare` says *where* and never *what*." A contrast
    reports one value per step metric exactly as a condition does, so `compare`
    alone would leave the quantity under test unnamed.

    A hypothesis names a condition by label — the same grammar
    `statistics.contrasts` uses — but `where` must carry the index, because that
    is the string `cli` gave the `correction.Member` it built for that
    condition. `label_to_index` is therefore the caller's job, not this
    module's: a pure resolver has no run to look the mapping up in.

    **`compare: {to: constant, value: N}` reads the metric's own per-condition
    block from `aggregated`, not a delta.** `condition` may still be given
    (validated the same way the baseline form's is) to pick which of several
    conditions is meant; absent, it resolves against the sole condition when
    the run declares exactly one, and to nothing otherwise — a silent default
    to "the first condition" would decide what a pre-registered hypothesis
    tested rather than what the config declared, the same reasoning
    `E-HYPOTHESIS-BASELINE` already rests on for the bare `{condition: X}`
    form. `where` is prefixed `const:`, distinct from `cond:` and `contrast:`,
    because the same condition can carry both a `vs_baseline` delta and a
    constant-referenced hypothesis on its own value, and the two must never
    collide in `by_key`.

    **`contrast` wins over everything else `compare` also names.** Checked
    first, ahead of both `to: constant` and the baseline/condition fallback:
    `{contrast: x, to: constant, value: 0.5}` and `{contrast: x, condition: y}`
    both resolve through the contrast, and every other key `compare` carries is
    read no further. One precedence rule for the whole field rather than one
    per pair of forms, and it is why the constant branch sits below this one
    rather than above it — the reverse order silently discarded a declared
    `contrast` and computed the verdict against the constant instead.
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

    # `contrast` wins whenever it is declared, over `to: constant` exactly as
    # it already did over `to: baseline`/bare `condition` (the precedent
    # `validate.py`'s own comment above the baseline-need exclusion states):
    # `{contrast: x, to: constant, value: 0.5, condition: y}` resolves through
    # the contrast, and `condition`/`value` are read no further, the same way
    # `{contrast: x, condition: y}` already resolves through the contrast and
    # needs no baseline at all. Checked FIRST, ahead of `to: constant`, is
    # what makes this true — the reverse order (constant-branch first) is a
    # real fault review caught: a declared contrast was silently discarded
    # and the verdict computed against the constant instead, with nothing in
    # `run.yaml` to say the contrast was never read.
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

    if compare.get("to") == "constant":
        if "condition" in compare:
            index = label_to_index.get(str(compare.get("condition")))
        else:
            agg = aggregated or {}
            index = next(iter(agg)) if len(agg) == 1 else None
        if index is None:
            return Observation(
                where=None, step=step, metric=metric, block=None, rests_on="computed"
            )
        found = (aggregated or {}).get(index, {}).get(step, {}).get(metric)
        return Observation(
            where=f"const:{index}",
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


def _observed_block(
    obs: Observation,
    bounds: tuple[float, float] | None,
    corrected_unavailable: bool = False,
    p_value_corrected: float | None = None,
) -> dict[str, Any] | None:
    """What the record shows as `observed`, in the shape its source implies.

    `reference.md` shows two: `{delta, ci95, ci95_corrected}` for a comparison and
    `{value, ci95, method}` for a summary metric. Both are the entry's own fields,
    not a reshaping of them, so a reader can find the same numbers in the block
    the hypothesis names.

    `ci95_corrected: null` when this hypothesis is in a corrected family whose
    bound could not be built — the same disclosure `W-STATS-CORRECTED-THIN`
    makes on the sweep side ("`ci95_corrected` is null rather than too narrow").
    Absent still means what it means everywhere else in this record: no
    correction was attempted at all.

    `p_value`, when the named block carries one, is copied the same way `ci95`
    is. `p_value_corrected` is *always* absent-not-null when there is none —
    `correction.corrected_for` never emits the key for a p-only-less member, so
    there is no "attempted and found nothing" state for it to report the way
    `ci95_corrected` has one; a `None` here always means "not passed."
    """
    if obs.block is None:
        return None
    # `list(...)`, not the entry's own list object. Sharing it makes
    # `yaml.safe_dump` anchor the interval where the comparison writes it
    # (`&id002`) and emit an alias (`*id002`) in the verdict, so the number a
    # hypothesis was decided on is no longer readable where it is written — in
    # the file this project describes as what a reviewer opens in ten years.
    # Copying also keeps a later in-place edit of either copy from silently
    # changing both.
    out: dict[str, Any] = {}
    for k in ("delta", "value", "ci95", "method", "p_value"):
        if k in obs.block:
            held = obs.block[k]
            out[k] = list(held) if isinstance(held, list) else held
    if bounds is not None:
        out["ci95_corrected"] = [bounds[0], bounds[1]]
    elif corrected_unavailable:
        out["ci95_corrected"] = None
    if p_value_corrected is not None:
        out["p_value_corrected"] = p_value_corrected
    return out


def _tested_number(
    obs: Observation,
    evaluate_on: str,
    bounds: tuple[float, float] | None,
    corrected_unavailable: bool = False,
) -> float | None:
    """The one number the verdict compares, or `None` when there isn't one.

    A bound test reads the corrected interval when this hypothesis is in a
    corrected family, and the raw one otherwise — `reference.md`: "Correction
    reaches a verdict only through a bound", and counted-iff-corrected decides
    whether there is a corrected bound at all.

    `corrected_unavailable` is the third case, and it is not the second: this
    hypothesis *is* in a corrected family, the level was demanded, and the bound
    at that level could not be built — a family too large for the resample's
    draws to support (`thin`), or an `fdr_bh` family, which implies no
    per-comparison level at all. Falling back to the raw interval there would
    answer a question nobody asked, on the *tighter* of the two bounds, so the
    error direction is over-support: a `supported: true` decided at α when the
    verdict was asked for at α/m. There is no number, so there is no verdict.

    `evaluate_on`'s three values — `observed`, `ci95_lower`, `ci95_upper` — are
    the whole vocabulary, and none of them is a p-value. No verdict this
    function computes rests on one, even for a counted hypothesis whose member
    carries `p_value`: `evaluate()` still writes `p_value_corrected` into the
    entry when it is there, at this family's own size, but that value is never
    read back into a comparison here.
    """
    if obs.block is None:
        return None
    if corrected_unavailable and evaluate_on != "observed":
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
    hyp: dict[str, Any],
    obs: Observation,
    bounds: tuple[float, float] | None,
    corrected_unavailable: bool = False,
    p_value_corrected: float | None = None,
) -> dict[str, Any]:
    """The verdict fields for one hypothesis.

    `verdict_evaluated_on` is spelled out rather than echoing the config's
    `evaluate_on` because `reference.md` says "a record field one letter from a
    config field is a typo waiting to be read as agreement" — a reader must see
    which question was asked without reconstructing it.

    `supported` is `None`, never `False`, when there is no number to compare: a
    `False` would be indistinguishable from a claim that was tested and failed.
    The same holds for `direction`: a value outside `{greater, less}` — most
    likely a typo — gets no verdict rather than one silently read against the
    wrong side, since a wrong `supported` is worse than an absent one and
    `direction` is never echoed into the record for a reader to catch it by eye.

    The comparison is strict (`>`, not `>=`): `reference.md` describes a
    supported hypothesis as one whose value "exceeds" or "clears" the
    threshold, and a value exactly at the threshold has done neither.

    A bound the correction could not build is the same honest absence, for the
    reason `_tested_number` gives: `supported: null` beside a
    `ci95_corrected: null` says the question was asked and could not be
    answered at the level asked for, where a raw-bound verdict would look
    answered and be over-supported. That choice over a warning is the project's
    own standard — a number that looks handled and is not is worse than an
    honest absence — and it is also the only one available to a pure function
    with no diagnostics channel: `run.yaml` has nowhere to carry a finding, so
    a warning printed to stdout would leave the record itself still claiming a
    verdict it cannot support.

    `p_value_corrected` never enters `number` or `supported`: `evaluate_on`
    names three bounds and none is a p-value, so it travels straight through to
    `_observed_block` for a reader to see, and never through the comparison
    this function decides.

    **`compare: {to: constant, value: N}` shifts `number` by the constant,
    once, after `_tested_number` returns** — `threshold` stays the decision
    boundary and `value` the reference, so "exceeds 0.5 by at least 0.02" is
    `value: 0.5, threshold: 0.02, direction: greater`, never `threshold: 0.52`
    with the constant folded in and lost from the record. `observed` itself
    is untouched: a reader sees the metric's real value and interval, and only
    the comparison this function makes is against the shifted number.
    """
    evaluate_on = str(hyp.get("evaluate_on") or "observed")
    number = _tested_number(obs, evaluate_on, bounds, corrected_unavailable)
    compare = hyp.get("compare")
    if number is not None and isinstance(compare, dict) and compare.get("to") == "constant":
        constant = compare.get("value")
        if isinstance(constant, (int, float)) and not isinstance(constant, bool):
            number = number - float(constant)
    threshold = hyp.get("threshold")
    direction = hyp.get("direction")
    supported: bool | None = None
    if (
        number is not None
        and isinstance(threshold, (int, float))
        and not isinstance(threshold, bool)
        and direction in ("greater", "less")
    ):
        supported = number > threshold if direction == "greater" else number < threshold
    return {
        "observed": _observed_block(obs, bounds, corrected_unavailable, p_value_corrected),
        "verdict_evaluated_on": evaluate_on,
        "supported": supported,
        "verdict_rests_on": obs.rests_on,
    }


def _is_counted(hyp: dict[str, Any], obs: Observation) -> bool:
    """`reference.md`: the family "counts the confirmatory hypotheses whose
    observations core computed".

    Two exclusions, and neither is a special case: an exploratory hypothesis is
    not a confirmatory one, and a reported `Estimate` is not core's number to
    correct. Counted-iff-corrected is the same rule the sweep family follows.
    """
    return (
        hyp.get("kind") == "confirmatory" and obs.rests_on == "computed" and obs.block is not None
    )


def evaluate(
    hyps: Sequence[dict[str, Any]],
    *,
    label_to_index: dict[str, int],
    vs_baseline: dict[int, dict[str, dict[str, Any]]] | None,
    contrasts: list[dict[str, Any]] | None,
    summary: dict[str, dict[str, Any]] | None,
    aggregated: dict[int, dict[str, dict[str, Any]]] | None,
    members: Sequence["Member"],
    method: str,
    parameters_hash: str,
) -> list[dict[str, Any]]:
    """Every declared hypothesis, resolved, corrected where it counts, judged.

    The corrected bound is rebuilt from the same evidence as the raw one, at this
    family's level — which is why `members` is a parameter: the record carries no
    draws, so a bound cannot be re-derived from it.

    `aggregated` is the same per-condition, per-step metric table `run.yaml`
    writes under `results.conditions[i].aggregated` — required, not defaulted,
    so a caller that forgets to thread it through a new call site fails loudly
    rather than silently resolving every `{to: constant}` hypothesis to no
    observation.
    """
    resolved = [
        (
            hyp,
            resolve(
                hyp,
                label_to_index=label_to_index,
                vs_baseline=vs_baseline,
                contrasts=contrasts,
                summary=summary,
                aggregated=aggregated,
            ),
        )
        for hyp in hyps
    ]
    counted = [(h, o) for h, o in resolved if _is_counted(h, o)]
    by_key = {(m.where, m.step, m.metric): m for m in members}
    counted_keys = [(o.where, o.step, o.metric) for _, o in counted if o.where is not None]
    family_members_ = [by_key[key] for key in counted_keys if key in by_key]
    size = len(counted)
    fields = corrected_for(family_members_, method, size, {"hypotheses": size}) if size else {}
    out: list[dict[str, Any]] = []
    for hyp, obs in resolved:
        entry: dict[str, Any] = {
            "id": hyp.get("id"),
            "kind": hyp.get("kind"),
            "declared_in": f"parameters_hash {parameters_hash}",
        }
        key = (obs.where, obs.step, obs.metric) if obs.where is not None else None
        corrected = fields.get(key) if key is not None and _is_counted(hyp, obs) else None
        bounds = None
        # Three states, not two. No entry at all means no correction was
        # attempted — `correction: none`, or a hypothesis outside the family —
        # and the raw interval is then the right one to test. An entry whose
        # `ci95_corrected` is `None` means the opposite: a level *was* demanded
        # and the interval at it could not be built, which `_tested_number`
        # refuses to paper over with the raw bound.
        corrected_unavailable = False
        p_value_corrected = None
        if corrected is not None:
            interval = corrected.get("ci95_corrected")
            if interval:
                bounds = (interval[0], interval[1])
            else:
                corrected_unavailable = True
            p_value_corrected = corrected.get("p_value_corrected")
        elif _is_counted(hyp, obs) and method != "none" and key not in by_key:
            # A counted hypothesis with no matching `Member` — today, only a
            # `compare: {to: constant}` observation, since core builds one for
            # every `vs_baseline`/contrast comparison but none for a constant
            # reference. Under a real correction method this hypothesis is
            # still IN the family (`family_size` counts it, per Decision 2's
            # whole point) but there is no evidence here to rebuild a bound
            # from at this family's level — the same honest gap
            # `W-STATS-CORRECTED-THIN` reports for a family too large for its
            # resample's draws, read through the same `corrected_unavailable`
            # path rather than a silent fall-back to the raw, uncorrected
            # bound. `method == "none"` is excluded: there no correction was
            # attempted for *anyone* in the family, which is the ordinary
            # absent-`ci95_corrected` case every other member gets too, not a
            # gap specific to this one.
            corrected_unavailable = True
        entry.update(verdict_for(hyp, obs, bounds, corrected_unavailable, p_value_corrected))
        if _is_counted(hyp, obs):
            entry["family_size"] = size
            entry["family"] = {"hypotheses": size}
        out.append(entry)
    return out

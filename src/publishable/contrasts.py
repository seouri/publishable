"""Which comparisons a config asks for. Pure: config and conditions in, list out.

`docs/reference.md` § Contrasts: `of` and `against` name conditions **by label**,
which is the selector property the condition-label grammar exists to provide — a
label has to be something a person can write down without seeing the directory.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from publishable.sweep import Condition
    from publishable.units import UnitList


@dataclass(frozen=True)
class Comparison:
    """One comparison of two conditions.

    `declared` records which of the two sources produced it: `False` for a
    condition-against-baseline comparison this module generates, `True` for a
    `statistics.contrasts` entry the config wrote down. The two land in
    different places in the record — `vs_baseline` inside a condition versus
    `results.contrasts` beside them — and the distinction cannot be
    reconstructed from the other fields: a declared entry may legitimately name
    the baseline as its `against` and carry an `id` equal to its `of`
    condition's own label, which is exactly a generated comparison's shape.
    """

    id: str
    of: int
    against: int
    within: dict[str, str] | None = None
    declared: bool = False


_MISSING = object()


def _free_axis_paths(baselines: list["Condition"]) -> list[str]:
    """The paths the baseline rows disagree on: the unfixed axes that actually vary.

    `docs/reference.md` § Expansion modes: "the baseline expands over whichever
    axes it doesn't fix", one baseline row per cell of those axes. This function
    recovers that cell's axes **from the conditions themselves**, which is what
    lets `baseline_for` target per cell without reading `sweep.baseline` and
    without reading a condition's index.

    The equivalence is a property of how `sweep.expand` builds a baseline row:
    it lays the *same* fixed mapping over every cell, fixed values last. So a
    path the baseline fixes holds one value across every baseline row and can
    never appear here, and a multi-path axis the baseline half-fixes counts as
    fixed in `_baseline_cells` and so contributes no cell path at all. What is
    left is exactly the unfixed axes — minus any whose single level makes it
    constant, which changes no answer, since matching on a constant path
    distinguishes nothing.

    Compared pairwise with `!=` against the first row rather than collected into
    a set: a condition's values are arbitrary YAML, and a list level is
    unhashable — `{...}` over it would raise `TypeError` from a function whose
    answer does not need hashing. `!=` needs nothing of a value at all, which is
    the point: this function takes `expand`'s output, and `expand` neither
    refuses a list level nor requires that `validate` ran, so resting the choice
    on `E-SWEEP-VALUE-UNNAMEABLE` having fired would be resting a pure
    function's defensiveness on a caller. (That refusal did not even cover a
    `paired` level until commit 884959a — the way such a justification goes
    stale, rather than a reason to restate it against today's coverage.)

    Order is the first row's key order, then any path a later row adds, so the
    comparison list this drives is stable rather than set-ordered.
    """
    if len(baselines) < 2:
        return []
    first = baselines[0]
    ordered: list[str] = list(first.values)
    for other in baselines[1:]:
        ordered += [k for k in other.values if k not in ordered]
    return [
        path
        for path in ordered
        if any(
            other.values.get(path, _MISSING) != first.values.get(path, _MISSING)
            for other in baselines[1:]
        )
    ]


def baseline_for(
    condition: "Condition", baselines: list["Condition"], free: list[str]
) -> "Condition | None":
    """The baseline of `condition`'s own cell, or None when its cell has none.

    § Expansion modes, second row: each `vs_baseline` targets "its own cell's
    baseline". A cell is a combination of the axes the baseline left free, so the
    condition's baseline is the baseline row agreeing with it on every free axis
    — `method=spearman__sex=f` against `sex=f__baseline`, whatever index either
    of them was assigned.

    **Matched on values, never on position.** Whether per-cell baselines belong
    at the head of each cell or in a leading block is an open document question
    (`docs/superpowers/spec-defects.md`, "Per-cell baseline numbering"), so any
    targeting built on condition indices would be built on numbering a later
    slice may change. This is invariant under either answer.

    `free` is empty for a single baseline, so every condition matches it and the
    answer is the one this function replaces: one reference for the whole run.

    Returns None rather than falling back to the first baseline when no cell
    matches. A fallback is precisely the cross-cell comparison per-cell
    baselines exist to avoid — `method=pearson__sex=m` against `sex=f__baseline`
    differs on two axes and mixes two effects. The shape is reachable:
    `expand` builds an `ablate` row beside a grid (the composition
    `E-SWEEP-ABLATE-CROSSED` refuses, so `run` never sees it) and that row
    carries only the baseline's fixed paths plus its one change, holding no
    value for a free axis at all.
    """
    for baseline in baselines:
        if all(
            condition.values.get(path, _MISSING) == baseline.values.get(path, _MISSING)
            for path in free
        ):
            return baseline
    return None


def resolve_contrasts(
    config: dict[str, Any], conditions: list["Condition"]
) -> list[Comparison]:
    """Every non-baseline condition against its own cell's baseline, then declared
    entries.

    A run with no baseline and no `statistics.contrasts` compares nothing, and
    the record carries no `vs_baseline` block at all — an empty one would claim
    a comparison was made and found nothing.

    **A baseline is never a comparison's subject.** § Expansion modes: "Baseline
    conditions are references rather than comparisons, so they never count as
    one: six conditions under two per-arm baselines are four comparisons in the
    correction family, not five." Every baseline row is skipped as an `of`, not
    just the one being targeted — comparing one reference against another is the
    cross-cell contrast per-cell baselines exist to avoid, and `family_size`
    counts comparisons, so admitting it corrects every interval in the run
    against a denominator one too large.

    The skip is scoped to this generated loop and deliberately not applied to
    the declared entries below: a `statistics.contrasts` entry may legitimately
    name a baseline as either side (see `Comparison.declared`), and a filter
    over the returned list would drop it.
    """
    by_label = {c.label: c.index for c in conditions if c.label is not None}
    out: list[Comparison] = []
    baselines = [c for c in conditions if c.is_baseline]
    free = _free_axis_paths(baselines)
    if baselines:
        for c in conditions:
            if c.is_baseline or c.label is None:
                continue
            against = baseline_for(c, baselines, free)
            if against is None:
                continue
            out.append(Comparison(id=c.label, of=c.index, against=against.index, declared=False))
    for entry in (config.get("statistics") or {}).get("contrasts") or []:
        # by_label[...] raises KeyError on an unresolvable label. That is
        # acceptable only because validate (Task 6) refuses an unresolvable
        # `of`/`against` at validate time, and `cli` always validates before
        # running — this function does not need to guard it itself.
        out.append(
            Comparison(
                id=str(entry.get("id")),
                of=by_label[entry["of"]],
                against=by_label[entry["against"]],
                within=entry.get("within"),
                declared=True,
            )
        )
    return out


def units_matching(roster: "UnitList", within: dict[str, str] | None) -> set[str] | None:
    """Unit keys matching every level in `within`, or `None` when unrestricted.

    `None` and `set()` are different answers: nobody asked, versus nobody
    matched. An empty stratum is a real finding — `limits.min_reported_n` exists
    to warn about small ones — so collapsing the two would hide it.

    Values compare as strings: a config's YAML gives `1` as an int while the same
    attribute read from a table is `"1"`, and comparing them raw matches nothing.
    """
    if within is None:
        return None
    return {
        unit.key
        for unit in roster
        if all(str(unit.attributes.get(k)) == str(v) for k, v in within.items())
    }

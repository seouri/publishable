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


def differing_axes(of: "Condition", against: "Condition") -> list[str]:
    """The axes two conditions disagree on, in the order the sweep declares them.

    `Condition.values` is built by `sweep.expand` from `grid.items()`, so
    iterating `of.values` first gives declaration order — which is what
    makes `differs_on` stable across runs rather than set-ordered. But the
    two sides' key sets are not guaranteed equal, and since
    `E-SWEEP-BASELINE-PARTIAL` was retired they can differ in *both*
    directions: a baseline may fix an axis the grid never sweeps (present in
    the baseline condition's `values`, absent from every grid condition's),
    and a grid axis need no longer be fixed in the baseline at all, which is
    what per-cell expansion made legal. Iterating only `of.values` would
    silently skip an axis of the first kind whenever it differs from that
    axis's own parameter default, so this walks the union of both sides' keys
    — required rather than merely defensive — comparing with `.get` against
    a sentinel (not `None`, which a real swept value could legitimately be)
    so a key present on one side and absent on the other always counts as
    differing rather than being skipped.

    Lives in this module rather than in `cli.py` or `validate.py` because both read
    it, and a module either of them already imports is what removes the cross-module
    private access and the local import either alternative would need — `cli`
    imports `publishable.validate` at module scope, so `validate` importing `cli`
    back is a true cycle, and `contrasts` sits below both.
    """
    ordered_keys = list(of.values) + [k for k in against.values if k not in of.values]
    return [
        k for k in ordered_keys if of.values.get(k, _MISSING) != against.values.get(k, _MISSING)
    ]


def crossed_group_axes(of: "Condition", against: "Condition") -> list[str]:
    """The declared group axes two conditions disagree on — empty iff they are paired.

    `reference.md` § Allocation's pairing table: two conditions differing only on
    parameter axes share their units and are paired unit by unit (or paired within
    that arm under `between`), while two differing on *any* `groups` axis hold
    disjoint sets of units by construction. So this list being empty **is** the
    pairing test, and it answers per comparison rather than per config — in a
    `groups × grid` design, control-pearson against control-spearman is paired and
    computable while control-pearson against treatment-pearson is not.

    **One expression, read wherever a comparison's pairing matters**, rather than a
    second spelling of the same rule at each site: two spellings of one rule
    drifting apart is a defect this codebase has already shipped, and here the
    drift would be a refusal at one site disagreeing with what another site
    records as paired.

    Returns the **list**, not a boolean: `validate`'s message names the axes and
    pluralizes on how many there are, and a boolean would force a second expression
    to recompute them.

    `Condition.selectors` is the authority on which of a condition's `values` paths
    select units rather than set a parameter — carried on the condition and set by
    `expand`, which is the only place that knows which mode produced a cell. Reading
    `values` alone would call every differing path a group axis. The **union** of
    both sides' selectors, because a path one side declares and the other does not
    still makes the two sides disjoint.

    Not gated on `allocation`: the axis being a declared `groups` axis is what makes
    the two sides disjoint, whatever `allocation` itself is declared as — a config
    missing that declaration entirely earns `E-DATA-ALLOCATION-WITHIN-ARMS`
    separately.
    """
    selecting = of.selectors | against.selectors
    return [k for k in differing_axes(of, against) if k in selecting]


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


def resolve_contrasts(config: dict[str, Any], conditions: list["Condition"]) -> list[Comparison]:
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

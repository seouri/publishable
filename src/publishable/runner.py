"""The execution loop. One execution at a time, in the recorded order."""

import copy
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from publishable.artifacts import StepIO
from publishable.coercion import coerce_scalars
from publishable.config import Config, SweptAway
from publishable.errors import ContractError
from publishable.replication import LABEL_JOIN, Repeat
from publishable.scope import Execution
from publishable.stats import handed_to, kish_effective_n
from publishable.sweep import Condition, condition_dir_name
from publishable.units import UnitList, cluster_count_of


@dataclass(frozen=True)
class ExecutionResult:
    execution: Execution
    status: str
    started_at: str
    wall_seconds: float
    returned: dict[str, Any]
    error: str | None
    recorded: frozenset[str] = frozenset()
    skipped: frozenset[str] = frozenset()
    rows: tuple[dict[str, Any], ...] = ()


def _counts(
    resolved: int,
    completed: "set[str]",
    ineligible: int,
    failed: int,
    weights: "dict[str, Any] | None",
    clusters: "dict[str, str] | None",
) -> dict[str, float]:
    """The one builder all three of `attrition`'s return sites go through.

    Three parallel dict literals is how `effective` reaches two of them and not
    the third — a design that weights reading as one that doesn't, at whichever
    site a given run happens to take. The shape is decided here instead.

    `effective` is Kish's size over the COMPLETED units' weights: those are the
    units a `basis: units` interval is computed from, so they are the ones whose
    concentration its degrees of freedom come from (`reference.md` § Weighted
    samples). It is `float` rather than `int` — an uneven weighting's effective
    size is not a whole number, and rounding it would report a size no interval
    was computed at. Present only when `weight_by` is declared, on the rule the
    three-part `n` states for every one of its parts: "each present only when it
    applies so a design that never skips reads as it always did".

    Sorted for reproducibility — Kish's ratio is order-independent in exact
    arithmetic but its two sums are not in floating point, and `completed` is a
    `set`. Indexed rather than `.get`-ed because every completed key comes from
    the roster the caller built `weights` from; a `.get(k, 0)` default would
    quietly change the denominator instead of failing.

    `clusters` is the same shape and arrives on the same rule: unit key → cluster
    id over the whole roster, supplied only when `data.units.cluster_by` is
    declared, and it adds `clusters` — the number of distinct clusters the
    COMPLETED units fall in. The completed ones for the reason `effective` is over
    them: `reference.md` § Clustered units reports the cluster count "as the
    effective sample size alongside the unit count" and § Statistical reporting
    gives `t_over_units_clustered` "df = clusters − 1", so this figure is the df of
    an interval, and a df is over the units the interval was computed from. Over
    the resolved roster instead it would name a df larger than any interval used,
    and a reader comparing it against `completed` would be comparing two different
    unit sets. It stays an `int`, unlike `effective`: a cluster count is a count of
    whole things, and § Clustered units' own example prints `clusters: 10`.

    **For a RECORDED column, this figure is not what `run.yaml` ends up printing.**
    `stats.summarize_step` recomputes `clusters` again, per column, from that
    column's own carrier keys ("`clusters` is recomputed per column" — that
    function's own docstring) — identical to this one for a full column, and
    correctly narrower for a ragged one — and that recompute is what reaches the
    record, overwriting this figure rather than reading it. This value survives
    unread here only for a DERIVED metric, where `summarize_step` has no
    per-column carrier set to recompute over and passes `**counts` through
    untouched.

    Listed ahead of `effective` because § The three-part `n` names the joiners in
    that order, and this dict's insertion order is what `run.yaml` renders.

    Neither mapping carries a default, deliberately: a fourth return site added
    later cannot forget one, because the call does not type-check without it. With
    a default, that site would produce a clustered (or weighted) design reading as
    a plain one — which is the exact failure this builder exists to prevent, and
    no test can see it until the site exists.
    """
    out: dict[str, float] = {
        "resolved": resolved,
        "completed": len(completed),
        "ineligible": ineligible,
        "failed": failed,
    }
    if clusters is not None:
        out["clusters"] = cluster_count_of(clusters, completed)
    if weights is not None:
        out["effective"] = kish_effective_n([weights[k] for k in sorted(completed)])
    return out


def attrition(
    results: list[ExecutionResult],
    roster: "UnitList | None",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
    weights: dict[str, Any] | None = None,
    clusters: dict[str, str] | None = None,
) -> dict[str, float]:
    """The four counts, scoped to one step within one condition. A failed unit has
    no row anywhere, so failure is derived.

    `step_name` is required, mirroring `stats.collapse_repeats`: without it this
    intersects `recorded`/`skipped` across every repeat-scoped execution of the
    condition, including an ordinary scalar-only step (a timing step, a logging
    step) that records no units at all. That step's empty `recorded` set would
    then intersect every OTHER step's into emptiness too, reclassifying every unit
    as `failed` and reporting a right-looking mean beside a wrong `n` — exactly the
    mismatch this parameter exists to make impossible.

    `condition_index` is required, not defaulted: core aggregates within each
    condition and never pools across conditions, and a caller that forgot to scope
    this would get a right-looking `n` computed over the wrong condition's
    executions — the same silent mismatch `collapse_repeats` refuses by requiring
    the same parameter. S2 always has exactly one condition and always passes `0`.

    `completed` and `ineligible` are computed per unit over the repeats
    `stats.handed_to` says that unit actually received — not, as with no fold,
    every repeat-scoped execution of this step. Without a fold every unit is
    handed to every repeat, so the two coincide and this is the same intersection
    as before: `completed` intersects because the collapse averages per unit, and
    a unit present in three of five seeds would otherwise enter that average on a
    different number of observations than its neighbours; `ineligible` intersects
    for the mirrored reason, since eligibility is a property of the design and a
    unit skipped in one repeat and completed (or simply unrecorded) in another did
    not get a consistent eligibility answer — that inconsistency is exactly the
    `failed` case, not a design exclusion. With a fold, intersecting across EVERY
    repeat-scoped execution would report `completed: 0` for any design containing
    one, because no unit is ever in more than one fold (`reference.md` § The
    per-unit tables); `handed_to` scopes the intersection to just the fold — and,
    under fold × seed, to every seed of that unit's own fold — so only a unit
    skipped or missing within its own group is `ineligible` or `failed`.

    `resolved` counts what was handed out across this condition, not the cohort:
    without a fold that is `roster` itself, since every execution receives it
    whole. `roster` is not always the whole shared roster — under a group axis
    (`reference.md` § Expansion modes) the caller has already narrowed it to
    this condition's own arm (`cli.py`'s `_cond_roster`, built from
    `units.arm_members`), the read-side counterpart of the narrowing
    `execute_plan` applies to what this condition's executions actually ran
    over. `attrition` does not re-derive that narrowing itself, and must not:
    it takes whichever `roster` the call site resolved, arm or whole, exactly
    once, the same single-authority reason `weights` and `clusters` arrive
    pre-resolved rather than rebuilt here. With a fold it is the union over
    every *declared* fold's members intersected with `roster` — which the
    partitions cover exactly, so it comes back to `roster` again, whether or
    not each fold's execution ran. That is the right answer at this scope: the
    counts a condition reports are against the cohort (or arm) the condition
    was run over, and a fold whose execution is missing leaves its units
    genuinely unsettled, so they land in `failed` rather than vanishing from
    the denominator. The smaller-than-roster figure is a fact about one
    *execution* — `reference.md` § Repeat kinds states it at that level, "`n:
    {resolved: 1, completed: 1}` per execution" under `k: all` — and this
    function is per-condition, so it is not the number to expect here. No
    per-execution `n` is written in this build: `run.yaml`'s `per_repeat` stays
    verbatim what each step returned (see `run_record.assemble_run_yaml`).

    `weights` is unit key → that unit's `data.units.weight_by` value, supplied
    only when the config declares one, and it is what adds `effective` to the
    returned mapping (`_counts` says what the figure is and why it is
    conditional). The values are passed through as the roster holds them —
    `str`, under a table source — because `stats.kish_effective_n` gates and
    parses its own input against `units.usable_weight`, the single authority
    `validate` approves a config's weights against. Coercing here would be a
    second notion of a usable weight, which is the thing this slice most
    carefully has only one of.

    That gating RAISES `ContractError` · `E-DATA-WEIGHT-INVALID` on a weight
    that is zero, negative, non-finite or non-numeric, and this call sits
    outside `cli.py`'s containment around `summarize_step`. For `run` the window
    is closed: `command_run` validates before it executes, against the same
    roster it then resolves, and `E-DATA-WEIGHT-INVALID` is one of the checks it
    runs — the same reasoning that closes `measurements`' validate/run window.
    It re-opens for any command that executes without validating first, which is
    `draft` and `resume` when they land (H9).

    `clusters` is unit key → that unit's `data.units.cluster_by` value, supplied
    the same way and from the same place, and it adds `clusters` to the returned
    mapping (`_counts` says over which units and why). It is built by
    `units.clusters_of`, the single authority for cluster membership, and counted
    by `units.cluster_count_of`, the single counting expression — a second `len(set(
    ...))` here is how a condition's cluster count and a fold's partition would
    come to disagree about what one cluster is.

    This is the per-step, per-condition breakdown `stats.summarize_step` attaches
    as a metric's `n`. It is deliberately not what guards `max_failed_fraction`:
    that threshold is run-level and a union across every recording step (see
    `_units_failed_anywhere` in `execute_plan`), not an intersection scoped to one.
    """
    if roster is None:
        return _counts(0, set(), 0, 0, weights, clusters)
    keys = {u.key for u in roster}
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        # Strict: `or 0` would map an unexpected `None` onto condition 0, which is
        # the pooling this function's required `condition_index` exists to prevent.
        # `build_plan` always gives a `repeat`-scoped execution a real index, so a
        # `None` here is a core defect and must drop out rather than be absorbed.
        and r.execution.condition_index == condition_index
    ]
    if not recording:
        return _counts(len(keys), set(), 0, len(keys), weights, clusters)
    # Accumulated per label, exactly as `stats.collapse_repeats` accumulates its
    # rows: two executions sharing one repeat label (a resumed leaf re-reported,
    # say) must merge, not overwrite. A dict comprehension kept only the last
    # while `labels` still held the duplicate, so the two readers of the same
    # executions disagreed about a unit — the collapsed table carrying a row for
    # a unit these counts called `failed`, which breaks the reconciliation
    # `resolved == completed + ineligible + failed`. `labels` comes off the
    # accumulator so it is unique and in execution order, the same list
    # `collapse_repeats` hands `handed_to`.
    recorded_by_label: dict[str, set[str]] = {}
    skipped_by_label: dict[str, set[str]] = {}
    for r in recording:
        label = r.execution.repeat_label or ""
        recorded_by_label.setdefault(label, set()).update(r.recorded)
        skipped_by_label.setdefault(label, set()).update(r.skipped)
    labels = list(recorded_by_label)
    if fold_members is None:
        handed = keys  # every unit, to every repeat — the no-fold rule
    else:
        handed = {k for s in fold_members.values() for k in s} & keys
    completed, ineligible = set(), set()
    for key in handed:
        mine = handed_to(key, labels, fold_members)
        if not mine:
            continue
        if all(key in recorded_by_label[lb] for lb in mine):
            completed.add(key)
        elif all(key in skipped_by_label[lb] for lb in mine):
            ineligible.add(key)
    return _counts(
        len(handed),
        completed,
        len(ineligible),
        len(handed) - len(completed) - len(ineligible),
        weights,
        clusters,
    )


def _arm_keys(
    condition_index: int,
    keys: set[str],
    arm_members: "dict[int, frozenset[str]] | None",
) -> set[str]:
    """The units a condition's execution was actually given, when the design
    declares group axes — the arm counterpart to `_handed_keys`'s fold narrowing,
    and the piece that makes the subset view real rather than merely avoided.

    Indexed, not `.get`-ed: `arm_members` is built once, from the same resolved
    conditions the plan itself was built from (`cli.command_run`), so a
    condition index missing from it is the plan and the resolved arms
    disagreeing — a core defect, not a condition with no arm. A `.get` default
    would silently hand that condition the whole roster, which is exactly the
    outcome two arms are declared to prevent, and is why this raises rather than
    falling back the way `_handed_keys` does for the fold case it mirrors.
    """
    if arm_members is None:
        return keys
    if condition_index not in arm_members:
        raise ContractError(
            f"condition {condition_index} has no arm among arm_members "
            f"({sorted(arm_members)!r}); the plan and the resolved arms disagree",
            code="E-RUN-ARM-UNRESOLVED",
        )
    return set(arm_members[condition_index]) & keys


def _handed_keys(
    repeat_label: str, keys: set[str], fold_members: dict[str, frozenset[str]] | None
) -> set[str]:
    """The units an execution with this repeat label was actually given.

    Subtracting from the whole roster instead is what made every fold run abort:
    the k−1 partitions this execution never saw are neither recorded nor skipped,
    and would each count as a failure.

    A label carrying no fold component while `fold_members` is not `None` is not
    a case to fall back on: `fold_members_for` returns `None` unless a `fold`
    level was declared, and `cross_levels` composes every leaf label from every
    declared level, so under a non-`None` `fold_members` every repeat label this
    function is ever called with by `execute_plan` carries a fold token by
    construction. Falling back to `keys` here would silently resurrect the exact
    bug this function exists to fix — the whole roster subtracted against a
    single execution's recorded units — so this is a core invariant violation,
    raised loud rather than defaulted quiet.
    """
    if fold_members is None:
        return keys
    parts = set(repeat_label.split(LABEL_JOIN))
    mine = [ks for f, ks in fold_members.items() if f in parts]
    if not mine:
        raise ContractError(
            f"repeat label {repeat_label!r} carries no fold component, but "
            f"fold_members ({sorted(fold_members)!r}) is not None; every label "
            "composed under a declared fold must include one of its members",
            code="E-RUN-FOLD-UNRESOLVED",
        )
    return set().union(*mine) & keys


def _units_failed_anywhere(
    results: list[ExecutionResult],
    roster: "UnitList",
    fold_members: dict[str, frozenset[str]] | None = None,
    arm_members: "dict[int, frozenset[str]] | None" = None,
) -> set[str]:
    """Units with no settled answer — neither recorded nor skipped — in at least
    one execution of a step that records units, across the whole run.

    A step "records units" if any of its repeat-scoped executions has produced at
    least one row so far — the same notion `cli.py`'s `recording_steps` uses to
    decide which steps enter `aggregated`, reused here rather than invented twice.
    That guard is what keeps an ordinary scalar-only repeat step (a timing step, a
    logging step) from ever failing the whole roster just because it records no
    units at all — only a step in the business of recording units can flunk one. A
    step whose every execution has crashed before producing a single row is never
    classified as recording and so cannot trip this guard either; its execution
    failures are still visible in `executions.jsonl` and the run's `status`, just
    not folded into unit attrition.

    This is deliberately NOT `attrition`, and deliberately not scoped to one
    condition: `reference.md` § "The failure fraction `run` enforces is against the
    run level" is explicit that the fraction is "units that failed in at least one
    execution, over `provenance.units.n`" — a union across every recording
    execution of every step, in every condition, over the whole resolved roster.
    `attrition`'s intersection is the right shape for one step's `n`; it is the
    wrong shape for this run-level union.

    What changes under a fold is the membership set each execution's recorded and
    skipped units are checked against: `_handed_keys` scopes it to the partition
    that execution was actually given, not the entire resolved roster — the other
    k−1 partitions were never handed to it and so cannot count as failures of it.
    `arm_members`, when a group axis is declared, narrows the same way for the
    same reason — a unit of the other arm was never handed to this condition's
    execution either, and counting it as failed would trip `max_failed_fraction`
    on an arm this run never touched. `_arm_keys` applies before `_handed_keys`,
    the same order `execute_plan`'s own narrowing uses, so a fold's complement is
    computed within the arm rather than across it.
    """
    keys = {u.key for u in roster}
    recording_steps = {
        r.execution.step_name for r in results if r.execution.scope == "repeat" and r.rows
    }
    failed: set[str] = set()
    for r in results:
        if r.execution.scope != "repeat" or r.execution.step_name not in recording_steps:
            continue
        scoped = keys
        if r.execution.condition_index is not None:
            scoped = _arm_keys(r.execution.condition_index, keys, arm_members)
        handed = _handed_keys(r.execution.repeat_label or "", scoped, fold_members)
        failed |= handed - (r.recorded | r.skipped)
    return failed


def step_dir_for(run_dir: Path, execution: Execution, collapse_repeats: bool) -> Path:
    """Depth follows scope; degenerate levels collapse."""
    if execution.scope == "run":
        return run_dir / "shared" / execution.step_name
    if execution.scope == "summary":
        return run_dir / "summary" / execution.step_name
    base = run_dir
    if execution.condition_label is not None and execution.condition_index is not None:
        base = base / "conditions" / condition_dir_name(
            execution.condition_index, execution.condition_label
        )
    if execution.scope == "repeat" and not collapse_repeats and execution.repeat_label:
        base = base / execution.repeat_label
    return base / execution.step_name


def resolve_condition_cfg(base: dict[str, Any], condition: Condition) -> Config:
    """Overlay this condition's swept *parameter* values onto the base config.

    A condition's `values` holds two kinds of dotted path, and only one of them
    names a leaf under `parameters`. A parameter path — from `grid`, `paired`,
    `sample`, `ablate`, or a parameter `baseline` — is overlaid: the walk creates
    intermediate mappings as needed and sets the leaf, so a `condition`- or
    `repeat`-scoped step reads exactly this condition's value without ever
    mentioning the sweep that produced it. A **selector** path — a group cell —
    is skipped, because `reference.md` § Expansion modes says "a group level is a
    *set of units*": `{arm: control}` names no parameter at all, and laying it
    over `parameters` would invent an `arm` no template's `parameter_spec`
    declares, which a step could then read as `cfg.parameters.arm`. That is the
    opposite of what a group axis claims — "same code, same parameters,
    different units" — and two conditions on a group axis are supposed to
    resolve to the *same* parameters.

    Takes the `Condition` rather than its `values` mapping so the two fields
    cannot arrive out of step: `expand` is the only place that knows which mode
    produced a cell, and a `values`-plus-`selectors` pair is something a caller
    can mismatch or forget. `Condition.selectors` is the answer, computed once.
    """
    doc = copy.deepcopy(base)
    for path, value in condition.values.items():
        if path in condition.selectors:
            continue
        node = doc.setdefault("parameters", {})
        *heads, leaf = path.split(".")
        for head in heads:
            node = node.setdefault(head, {})
        node[leaf] = value
    return Config(doc)


def resolve_wide_cfg(base: dict[str, Any], swept_paths: set[str]) -> Config:
    """A config for `run`/`summary` scope, with every swept path made unreadable.

    Those scopes have no single condition to draw a swept value from, so each
    leaf `sweep` varies is replaced by a `SweptAway` marker: `Node.__getattr__`
    raises `E-STEP-SWEPT-PARAM` the moment such a step reads it, rather than
    silently handing back a value that could only be wrong for every condition
    but one.

    Walks with `setdefault`, exactly as `resolve_condition_cfg` does, rather
    than `get` — a swept path whose parent is absent from `base` must still end
    up marked. Skipping it there (as an earlier version of this function did)
    fails in the unsafe direction: the value stays readable, and a `run`- or
    `summary`-scoped step would silently get a value that could only be wrong
    for every condition but one. Planting the marker instead means the worst
    case is a step getting `E-STEP-SWEPT-PARAM` for a path `validate` should
    have already rejected as unresolvable — a refusal either way, and the more
    accurate one, since the path *is* swept.
    """
    doc = copy.deepcopy(base)
    for path in swept_paths:
        node = doc.setdefault("parameters", {})
        *heads, leaf = path.split(".")
        for head in heads:
            node = node.setdefault(head, {})
        node[leaf] = SweptAway(f"parameters.{path}")
    return Config(doc)


def execute_plan(
    *,
    plan: list[Execution],
    run_dir: Path,
    input_dir: Path,
    cfgs: dict[int, Any],
    repeats: list[Repeat],
    digest: str,
    units: UnitList | None = None,
    max_failed_fraction: float | None = None,
    fold_members: dict[str, frozenset[str]] | None = None,
    arm_members: "dict[int, frozenset[str]] | None" = None,
    holdout_train: "UnitList | None" = None,
    measurements: dict[str, Any] | None = None,
) -> list[ExecutionResult]:
    """Run every execution in the plan, in order, one at a time.

    A failed execution never stops the run — the plan runs to its end, because
    abandoning it throws away every execution still pending and `resume` cannot
    un-abort a plan that was never attempted. `max_failed_fraction` is the one
    documented exception: unit failures only accumulate, so once the fraction of
    the roster that has failed in at least one execution crosses the threshold, no
    later execution can bring it back, and spending the remaining compute to
    confirm that is waste.

    `arm_members` is `units.arm_members`'s answer, one frozenset of keys per
    resolved condition that selects a group axis — `None` for a design that
    declares none. An arm is a **subset view of the one roster resolved for the
    whole run, never a re-resolution**: `Unit` is frozen and hashable by key
    exactly because one roster is shared across every condition, and narrowing to
    an arm here filters that same roster rather than reading the units a second
    time. Narrowed exactly when `execution.condition_index is not None` — a `run`-
    or `summary`-scoped execution belongs to no condition and so to no arm, and
    keeps the whole roster unconditionally, the same way a `fold` repeat already
    leaves those two scopes alone. The narrowing happens **before** the fold
    branch below reads `units`, not after: a `fold` repeat's `train` is built as
    "the roster minus what this execution was handed", and computing that
    complement across the *whole* roster rather than within the arm would leak
    the other arm's units into `.train` — the same class of leak
    `units.partition_units` exists to prevent for a cluster, one level up.

    `holdout_train` is `data.units.holdout`'s training roster, already resolved
    by the caller (`cli.command_run`'s single-authority narrowing) — this
    function derives nothing from it beyond wrapping it. Unlike a `fold`, a
    holdout's split is fixed for the whole run, so when `holdout_train` is given,
    `units` is the test partition and `io.units.train` is `holdout_train` at
    every scope — `run`, `condition`, `repeat` and `summary` alike, not only
    `repeat` the way a fold's `.train` is.
    """
    # Two evaluation splits is two answers to "which units is this metric
    # over?", which is exactly what `validate` refuses. No config can reach this
    # at this commit: `E-DATA-HOLDOUT-FOLD` (task 6) refuses a `holdout` beside a
    # declared `fold` level, and `E-DATA-HOLDOUT-CELLS` (task 8) refuses a
    # holdout beside the group axis `arm_members` comes from. So this asserts
    # something about core's own callers rather than about a config — and it is
    # an assertion rather than silent precedence because if either refusal ever
    # stops holding, a crash here is what makes that visible instead of a
    # partition chosen by whichever branch happened to be written first.
    assert holdout_train is None or fold_members is None, (
        "a holdout and a fold repeat both narrow the roster; `validate` refuses the "
        "pair as `E-DATA-HOLDOUT-FOLD`"
    )
    assert holdout_train is None or arm_members is None, (
        "a holdout beside a group axis is refused as `E-DATA-HOLDOUT-CELLS`"
    )
    collapse = len(repeats) <= 1
    seeds = {r.label: r.seed for r in repeats}
    ledger = run_dir / "executions.jsonl"
    results: list[ExecutionResult] = []

    # Derived once from the plan itself, not threaded in as extra parameters:
    # `io.conditions`/`io.repeats`/`io.read_condition` are a `summary`-scoped
    # step's read surface, and the plan already carries every condition and
    # repeat label the run resolved. A no-`sweep` run still has one resolved
    # condition — index 0, label `None` — and it belongs in this list: `None`
    # is what tells `read_condition` there is no `conditions/` level to nest
    # under, not "this index doesn't exist."
    #
    # Ascending by index, never by first appearance in the plan. Under
    # `order: randomized` a pipeline with zero condition-scope steps has its first
    # mention of each condition come from the shuffled repeat executions, so
    # first-appearance order would make `io.conditions` — a documented `summary`
    # read surface — depend on an RNG draw, and a summary step building a
    # comparison table from it would emit rows in a different order per design
    # digest. Nothing in `reference.md` warns that the list is unordered, so it
    # is ordered.
    by_index: dict[int, str | None] = {}
    for e in plan:
        if e.condition_index is not None and e.condition_index not in by_index:
            by_index[e.condition_index] = e.condition_label
    conditions_list: list[tuple[int, str | None]] = sorted(
        by_index.items(), key=lambda entry: entry[0]
    )
    repeats_list = [r.label for r in repeats]
    step_scopes = {e.step_name: e.scope for e in plan}

    for execution in plan:
        started = datetime.now(UTC)
        clock = time.monotonic()

        if execution.scope == "repeat":
            label = execution.repeat_label or ""
            if label not in seeds:
                raise ContractError(
                    f"{execution.step_name!r} has repeat label {label!r}, which has no "
                    f"seed among the resolved repeats {sorted(seeds)!r}",
                    code="E-RUN-SEED-MISSING",
                )
            seed = seeds[label]
        else:
            seed = 0

        step = execution.step_cls()
        step._bind(
            condition=execution.condition_index,
            repeat=execution.repeat_label or None,
            digest=digest,
            seed=seed,
        )
        # Arm narrowing first, before the fold branch below reads the roster: a
        # `run`- or `summary`-scoped execution has no condition and so no arm
        # (`execution.condition_index is None`) and keeps the whole roster,
        # exactly the units the outer `units` variable still names — narrowing
        # is a plain reassignment of the *local* `scoped_units`, so `units`
        # itself stays untouched for `attrition`/`_units_failed_anywhere` below,
        # the same reason the fold narrowing already left it alone.
        scoped_units = units
        if arm_members is not None and units is not None and execution.condition_index is not None:
            arm_keys = _arm_keys(execution.condition_index, {u.key for u in units}, arm_members)
            scoped_units = UnitList([u for u in units if u.key in arm_keys])
        # A fold repeat puts the units out of reach of the wider scopes: there is
        # no fold at "run" or "condition" scope, since folds are repeats and
        # repeats haven't happened yet, so a step fitting there would fit on units
        # later folds test on. By "summary" scope every fold has already run, so
        # there is nothing left to leak, and it keeps the whole roster like the
        # no-fold case — the arm-narrowed roster, when a group axis is declared,
        # since arm narrowing already ran above.
        if fold_members is None or scoped_units is None:
            # A `data.units.holdout` is fixed for the WHOLE run, so it narrows
            # at every scope — `run`, `condition`, `repeat` and `summary`
            # alike. That is the inverse of the fold branch below, which hands
            # `None` at `run`/`condition` because a fold hasn't happened yet
            # there — and deliberately: `reference.md` § Step scope says "a `holdout`
            # does not raise, because its split is fixed for the whole run",
            # and `experimental-designs.md` § Cross-validation says
            # "condition-scoped fitting is right for a fixed holdout and wrong
            # for cross-validation". A holdout that took the fold branch's
            # `run`/`condition` hole would hand `None` to exactly the step a
            # holdout exists to let fit.
            #
            # `units` is already the TEST partition when a holdout is declared
            # — `cli.command_run` narrowed it at the call site, `_cond_roster`'s
            # single-authority rule, which `attrition`'s own docstring restates
            # ("does not re-derive that narrowing itself, and must not"). This
            # function turns two rosters into one `UnitList`; it derives
            # neither.
            step_units = scoped_units
            if holdout_train is not None and scoped_units is not None:
                step_units = UnitList(list(scoped_units), train=holdout_train)
        elif execution.scope in ("run", "condition"):
            step_units = None  # no fold exists yet at these scopes
        elif execution.scope == "repeat":
            handed = _handed_keys(
                execution.repeat_label or "", {u.key for u in scoped_units}, fold_members
            )
            step_units = UnitList(
                [u for u in scoped_units if u.key in handed],
                train=UnitList([u for u in scoped_units if u.key not in handed]),
            )
        else:
            step_units = scoped_units  # "summary": every fold has already run
        io = StepIO(
            step_dir=step_dir_for(run_dir, execution, collapse),
            input_dir=input_dir,
            run_dir=run_dir,
            units=step_units,
            scope=execution.scope,
            conditions=conditions_list,
            repeats=repeats_list,
            step_scopes=step_scopes,
            condition_index=execution.condition_index,
            condition_label=execution.condition_label,
            repeat_label=execution.repeat_label,
            # `data.units.measurements` itself, threaded rather than re-read: it is
            # what tells `io.record` a `measurement=` has a rule to collapse under,
            # and what `finalize` collapses by. Without it a config that declares
            # measurements is honoured at the input path and refused at the step
            # path, which is the same declaration answering two different ways.
            measurements=measurements,
        )
        io.step_dir.mkdir(parents=True, exist_ok=True)
        recorded: frozenset[str] = frozenset()
        skipped: frozenset[str] = frozenset()
        rows: tuple[dict[str, Any], ...] = ()
        cfg_key = execution.condition_index if execution.condition_index is not None else -1
        if cfg_key not in cfgs:
            # Not a step failure — the plan and the resolved configs disagree,
            # which means core built an inconsistent plan. Continuing would
            # write a run record that looks partially fine while resting on a
            # bug, so this is deliberately not caught by the per-execution
            # `try` below: only a step's own failure is allowed to leave the
            # rest of the plan running.
            raise ContractError(
                f"no cfg was resolved for condition index {cfg_key!r}, needed by "
                f"{execution.step_name!r} at {execution.scope!r} scope; the plan and "
                "the resolved `cfgs` disagree",
                code="E-RUN-CFG-MISSING",
            )
        cfg = cfgs[cfg_key]
        try:
            returned = step.run(cfg, io)
            if returned is None:
                returned = {}
            elif not isinstance(returned, dict):
                raise ContractError(
                    f"{execution.step_name!r} returned {type(returned).__name__}; "
                    "a step's `run` must return a mapping or None",
                    code="E-STEP-RETURN-TYPE",
                )
            returned = coerce_scalars(returned, execution.step_name, scope=execution.scope)
            io.finalize()
            recorded = frozenset(io.recorded_keys)
            skipped = frozenset(io.skipped)
            rows = tuple(io.rows())
            status, error = "completed", None
        except Exception as exc:  # a failed execution never stops the run
            code = getattr(exc, "code", None)
            prefix = f"{code} " if code else ""
            returned, status, error = {}, "failed", f"{prefix}{type(exc).__name__}: {exc}"

        result = ExecutionResult(
            execution=execution,
            status=status,
            started_at=started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            wall_seconds=round(time.monotonic() - clock, 3),
            returned=returned,
            error=error,
            recorded=recorded,
            skipped=skipped,
            rows=rows,
        )
        results.append(result)
        with ledger.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "step": execution.step_name,
                        "scope": execution.scope,
                        "condition": execution.condition_index,
                        "repeat": execution.repeat_label,
                        "status": status,
                        "started_at": result.started_at,
                        "wall_seconds": result.wall_seconds,
                        "error": error,
                    }
                )
                + "\n"
            )

        if max_failed_fraction is not None and units is not None:
            resolved = len(units)
            failed = _units_failed_anywhere(results, units, fold_members, arm_members)
            if resolved and len(failed) / resolved > max_failed_fraction:
                break
    return results

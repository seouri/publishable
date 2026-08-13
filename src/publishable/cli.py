"""Dispatch. Operation commands take paths and nothing else.

See docs/reference.md § Exit codes and diagnostics, § Generators, § Scaffolding.
"""

import dataclasses
import importlib
import importlib.metadata
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from publishable.artifacts import allocation_hash, build_allocation_document
from publishable.base_experiment import BaseExperiment, load_experiment
from publishable.coercion import coerce_scalars
from publishable.config import Config
from publishable.contrasts import resolve_contrasts, units_matching
from publishable.correction import Member, corrected_fields
from publishable.diagnostics import (
    EXIT_FAILED,
    EXIT_INVOCATION,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
    Collector,
)
from publishable.errors import ContractError, PublishableError
from publishable.estimate import Estimate
from publishable.generators.experiment import generate_experiment
from publishable.generators.step import generate_step
from publishable.hashes import code_hash, design_digest, parameters_hash
from publishable.hypotheses import evaluate as evaluate_hypotheses
from publishable.manifest import build_manifest, manifest_hash, verify_manifest
from publishable.provenance import find_repo_root, git_provenance
from publishable.replication import (
    cross_levels,
    fold_members_for,
    order_seed_for,
    realize_order,
    resolve_repeats,
)
from publishable.run_identity import RunLock, allocate_run_dir, point_latest
from publishable.run_record import assemble_run_yaml, run_status, summary_values
from publishable.runner import (
    _arm_keys,
    attrition,
    execute_plan,
    resolve_condition_cfg,
    resolve_wide_cfg,
)
from publishable.scaffold import scaffold_project
from publishable.scope import Execution, build_plan
from publishable.stats import (
    UnitTable,
    cohens_dz,
    collapse_repeats,
    mean_of,
    min_honest_draws,
    paired_delta_of_derived,
    paired_keys,
    paired_percentile_of_derived,
    paired_t_over_units,
    repeat_spread,
    resample_seed,
    summarize_step,
    unit_table_from_rows,
)
from publishable.strata import levels_for
from publishable.sweep import (
    _swept_paths,
    ablated_paths,
    condition_dir_name,
    expand,
    sample_seed_for,
    selector_paths,
    sweep_document,
)
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template
from publishable.units import (
    Unit,
    UnitList,
    arm_members,
    clusters_of,
    fold_basis,
    partition_units,
    resolve_units,
    units_hash,
)
from publishable.uv_support import uv_lock_info
from publishable.validate import load_document, validate_config

if TYPE_CHECKING:
    from publishable.contrasts import Comparison
    from publishable.runner import ExecutionResult
    from publishable.sweep import Condition

OPERATION_COMMANDS = {"validate", "run"}


def _preloaded_experiment(config_path: Path) -> BaseExperiment | None:
    """Import the entrypoint before validating, so a run imports user code once.

    `validate_config` imports it too when handed nothing (it needs the step classes
    for `W-REPL-DETERMINISTIC`), and importing a project's package twice in one
    process is exactly what `load_experiment`'s `sys.modules` purge exists to make
    survivable — but paying for it on every run is pointless. Failures are swallowed
    here and reported by `validate_config` as `E-ENTRYPOINT-IMPORT`; a parse that
    fails is likewise the validator's finding to report, not this helper's.
    """
    doc = load_document(config_path)
    if doc is None:
        return None
    entrypoint = doc.get("entrypoint")
    if not isinstance(entrypoint, str) or not entrypoint:
        return None
    try:
        return load_experiment(find_repo_root(config_path), entrypoint)
    except Exception:  # reported by `validate_config`, which collects rather than raises
        return None


def _apply_execution_order(
    plan: list[Execution], execution_order: list[tuple[int, str]]
) -> list[Execution]:
    """Reorder `plan`'s repeat-scope executions to match `execution_order` exactly.

    Called only under `order: randomized` — see the call site. Under `as_declared`
    nothing was shuffled, so there is no realized order for the plan to match and
    `build_plan`'s step-major layout stands unchanged.

    `execution_order` is a fact about the run, not a rule to re-derive, so the plan
    actually executed must match it rather than merely being recorded beside it.
    `execution_order` orders `(condition, repeat label)` pairs — the grain
    `reference.md`'s example records — so each pair's own repeat-scope steps are
    kept together, in the order `experiment.steps` declares them, and the pairs
    themselves are laid out in `execution_order`'s sequence. `condition`-scope
    executions are left where `build_plan` put them (ahead of every repeat, one
    condition's steps before the next) since nothing in `execution_order` orders
    them.

    Raises `E-RUN-ORDER-MISMATCH` if a repeat-scope execution in `plan` has no
    home among `execution_order`'s pairs — the plan and the resolved order
    disagree, the same invariant class `execute_plan` raises `E-RUN-CFG-MISSING`
    for when the plan and the resolved `cfgs` disagree. Both are core bugs, not
    user mistakes: `declared_pairs` and `plan`'s repeat labels are built from the
    same `conditions`/`repeats` in `command_run`, so this should be unreachable —
    but a silently dropped pair here would run fewer executions than the plan
    declared while `sweep.yaml` recorded the fuller set, which is worse than
    recording nothing.
    """
    by_pair: dict[tuple[int, str], list[Execution]] = {}
    for e in plan:
        if e.scope == "repeat":
            by_pair.setdefault((e.condition_index or 0, e.repeat_label or ""), []).append(e)
    reordered_repeats = [e for pair in execution_order for e in by_pair.get(pair, [])]
    n_repeat = sum(1 for e in plan if e.scope == "repeat")
    if len(reordered_repeats) != n_repeat:
        raise ContractError(
            f"{n_repeat} repeat-scope executions are in the plan, but only "
            f"{len(reordered_repeats)} were found among execution_order's "
            f"{len(execution_order)} pairs; the plan and the resolved order disagree",
            code="E-RUN-ORDER-MISMATCH",
        )
    summary_executions = [e for e in plan if e.scope == "summary"]
    return (
        [e for e in plan if e.scope not in ("repeat", "summary")]
        + reordered_repeats
        + summary_executions
    )


def _baseline_comparisons(
    doc: dict[str, Any], conditions: "list[Condition]"
) -> "list[Comparison]":
    """The subset of `resolve_contrasts`'s list that belongs in `vs_baseline`.

    `resolve_contrasts` also returns declared `statistics.contrasts` entries —
    an arbitrary `of`/`against` pair under a custom `id` — and those are
    `results.contrasts` (`_declared_comparisons`, `_compute_declared_contrasts`),
    not this run's `vs_baseline`. Which source produced a comparison is read off
    `Comparison.declared` rather than reconstructed from `id`/`against`: a
    declared entry may name the baseline as its `against` and carry an `id`
    equal to its `of` condition's own label — `validate` permits both — and an
    identity test on those fields misfiles it here, where it silently replaces
    the genuine unrestricted baseline block and never reaches
    `results.contrasts` at all.
    """
    if not any(c.is_baseline for c in conditions):
        return []
    return [comp for comp in resolve_contrasts(doc, conditions) if not comp.declared]


def _declared_comparisons(doc: dict[str, Any], conditions: "list[Condition]") -> "list[Comparison]":
    """The complement of `_baseline_comparisons`: every `resolve_contrasts` entry
    that is *not* an auto-generated baseline comparison — i.e. a declared
    `statistics.contrasts` entry, headed for `results.contrasts` rather than
    `vs_baseline`. Reads the same `Comparison.declared` flag, inverted, kept as
    its own function so a caller never has to remember to negate the other one
    correctly.
    """
    return [comp for comp in resolve_contrasts(doc, conditions) if comp.declared]


_MISSING = object()


def _differing_axes(of: "Condition", against: "Condition") -> list[str]:
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
    """
    ordered_keys = list(of.values) + [k for k in against.values if k not in of.values]
    return [
        k for k in ordered_keys if of.values.get(k, _MISSING) != against.values.get(k, _MISSING)
    ]


def _wide_swept_paths(sweep_block: dict[str, Any]) -> set[str]:
    """Every `parameters` path a condition fixes, for `resolve_wide_cfg` to mark unreadable.

    Every path any condition fixes, not just the grid's axes. A path
    `sweep.baseline` fixes varies across conditions by definition — condition
    `00` uses the baseline's value and every other condition uses the base
    config's — so it is exactly as unreadable at `run`/`summary` scope as a
    grid axis is. Reading the grid alone left a baseline-only path resolving
    to the base value, which is a value no condition in the run used.

    `_swept_paths` rather than `grid` alone: every axis-shaped mode's paths vary
    across conditions, and `paired`'s and `sample`'s did not reach here when each
    became a real axis — a sampled path stayed readable at `run`/`summary` scope
    and resolved to the base config's value, which is exactly the "a value no
    condition in the run used" failure the baseline half of this union exists to
    prevent, reached through a mode added after it was written.
    `ablated_paths` is unioned in for the same reason and by the same rule,
    from the other side of the axis/non-axis split: an ablated path varies
    across conditions too. Most are already covered by the `baseline` term —
    a removed path is one the baseline fixes — but an `override` path the
    baseline leaves alone is not, and it is exactly the residue this union has
    now been widened for three times.

    **`selector_paths` is subtracted**, and it is the one term that narrows
    rather than widens. A `baseline` may fix a group level (§ Expansion modes:
    it "accepts group levels as well as parameter paths"), so `{arm: control}`
    reaches the `baseline` term above — but a group path names no parameter,
    so planting a `SweptAway` marker at `parameters.arm` would invent the same
    phantom parameter `resolve_condition_cfg` now refuses to invent, one scope
    over: a `run`- or `summary`-scoped step reading `cfg.parameters.arm` would
    get `E-STEP-SWEPT-PARAM` — "this is swept, you cannot read it here" — for a
    parameter that does not exist in any scope. Subtracting leaves the honest
    refusal, `E-STEP-PARAM-UNKNOWN` from `Node.__getattr__`.

    A function rather than the inline union it was, so the subtraction is
    testable: `groups` is refused by `validate` in this build
    (`E-SWEEP-GROUPS-UNSUPPORTED`), so no `run` can reach this line with a group
    axis declared, and an end-to-end test of it cannot exist yet.
    """
    selectors = set(selector_paths(sweep_block))
    return (
        set(_swept_paths(sweep_block))
        | set(ablated_paths(sweep_block))
        | set(sweep_block.get("baseline") or {})
    ) - selectors


def _resolved_group_axes(
    units_decl: dict[str, Any] | None, sweep_block: dict[str, Any]
) -> dict[str, tuple[str, list[str]]]:
    """Every `sweep.groups` axis resolved to `(assign.<axis>.from, declared levels)`
    — `units.arm_members`'s own input shape — read the same way
    `validate._check_assign`'s `by_attribute` branch resolves the pair: the
    declared `from` if it is a non-empty string, else the axis name itself.

    Skips an axis whose `levels` does not resolve to a non-empty list of
    strings, matching `_check_assign`'s own skip for that shape — `sweep.groups`'s
    own shape check is `validate`'s to report, or not report at all in this
    build, and inventing a second notion of "resolved" here would not change
    that. A malformed `assign` block (absent, non-mapping, or naming a method
    other than `by_attribute`) resolves the axis to its own name, the same
    default `_check_assign` falls back to before its own checks on the block
    would have already reported the malformation as a finding.

    **That skip is narrower than `sweep.selector_paths`'s own idea of "a group
    axis exists"**, and the caller must not gate on this function's own
    truthiness for that reason: `selector_paths` — the same function `expand`
    uses to decide which paths are group cells — accepts a `levels` list of any
    element type, so a config with e.g. `levels: [1, 2]` still expands into
    conditions carrying `Condition.selectors == {"that axis"}`, while this
    function silently omits the axis from its result. `command_run` gates
    calling `units.arm_members` on `selector_paths(sweep_block)`, not on this
    function's result, exactly so that disagreement surfaces as `arm_members`'s
    own `KeyError` — a caller bug to see — rather than as a silently
    empty `group_axes` that skips arm narrowing for every condition on that
    axis.

    Unreachable from `command_run` today: a declared `sweep.groups` axis draws
    `E-SWEEP-GROUPS-UNSUPPORTED` from `validate`, an error that stops `run`
    (`command_run`'s `if doc is None or c.has_errors: return EXIT_WRONG`) before
    this line is ever reached, until the slice that retires it (task 17) lands
    — the same "unreachable in this build" `_wide_swept_paths` above notes for
    the selector-path subtraction it depends on.
    """
    assign = (units_decl or {}).get("assign")
    blocks = assign if isinstance(assign, dict) else {}
    axes: dict[str, tuple[str, list[str]]] = {}
    for entry in sweep_block.get("groups") or []:
        if not isinstance(entry, dict):
            continue
        axis = entry.get("by")
        if not isinstance(axis, str) or not axis:
            continue
        levels = entry.get("levels")
        if not (
            isinstance(levels, list) and levels and all(isinstance(v, str) for v in levels)
        ):
            continue
        block = blocks.get(axis)
        # Gated on `method == "by_attribute"`, matching `_check_assign`'s own
        # elif chain and `units._assign_constant_columns`'s own gate for the
        # same reason: `from` "means nothing" under `random`/`blocked` or an
        # absent/out-of-enum method, each already refused at `validate` before
        # this line is ever reached (`E-DATA-ASSIGN-DRAWN`/`E-DATA-ASSIGN-METHOD`).
        declared_from = (
            block.get("from")
            if isinstance(block, dict) and block.get("method") == "by_attribute"
            else None
        )
        column = declared_from if isinstance(declared_from, str) and declared_from else axis
        axes[axis] = (column, levels)
    return axes


def _cond_roster(
    roster: "UnitList",
    cond_index: int,
    arm_members_map: "dict[int, frozenset[str]] | None",
) -> "UnitList":
    """The units condition `cond_index` counts against — its own arm's subset
    of the shared roster when a group axis selects one, and the whole roster
    (the same object, not a copy) otherwise.

    This is the read side of the same narrowing `execute_plan` already applies
    to the units a condition's steps EXECUTE against (`runner.py`'s own
    `scoped_units`): `attrition` and `statistics.report_by`'s per-level table
    both count units for a condition, and until this function existed they
    counted the whole roster while the run itself executed only the arm —
    `resolved: 12` reported beside 5 units the condition's own executions
    never touched, with the other arm's 7 silently landing in `failed`
    (`reference.md` § What isn't a repeat: "Under a group axis it doesn't
    reconcile, and shouldn't — each arm's interval is over that arm's units").

    Built on `runner._arm_keys`, not `units.arms_of` or a fresh comprehension
    over `roster`: `arm_members_map` is `units.arm_members`'s answer, already
    resolved once from the same conditions the plan itself was built from, and
    `_arm_keys` is the guard `execute_plan` already raises through
    (`E-RUN-ARM-UNRESOLVED`) for a condition index the resolved arms disagree
    with the plan about. A fourth derivation of arm membership here — reaching
    back into `units.arms_of` and re-reducing across axes per condition — is
    exactly the defect the single-authority pattern (`arms_of`, then
    `arm_members`, then this) exists to prevent a third instance of.
    """
    if arm_members_map is None:
        return roster
    keys = _arm_keys(cond_index, {u.key for u in roster}, arm_members_map)
    return UnitList([u for u in roster if u.key in keys])


def _cond_beside_n(
    beside_n: dict[str, Any], cond_roster: "UnitList", roster: "UnitList"
) -> dict[str, Any]:
    """`beside_n` with `technical_n` withheld when `cond_roster` is an arm
    rather than the whole roster.

    `technical_n` is `{min, max, median}` over the WHOLE roster's measurement
    counts (`command_run`'s own comment above where it is built) — the same
    reason `report_by`'s per-level `summarize_step` call passes
    `weighted_beside` rather than `beside_n`: copying a whole-roster figure
    onto a subset states a spread nobody computed over that subset. Under a
    group axis `cond_roster` IS such a subset, one level up from a
    `report_by` level, so the same withholding applies here rather than
    leaving a per-arm `n` sitting beside a figure describing units this
    condition's own table does not hold.

    `cond_roster is roster` (identity, not equality) is `_cond_roster`'s own
    signal that no group axis narrowed this condition — the same check that
    function documents for its no-narrowing return.
    """
    if cond_roster is roster:
        return beside_n
    return {k: v for k, v in beside_n.items() if k != "technical_n"}


def _report_by_levels(
    roster: "UnitList", attribute: str
) -> dict[str, tuple[set[str], "UnitList"]]:
    """Each level of `attribute` over `roster`, paired with the roster VIEW
    `attrition` must count that level against — `report_by`'s per-level loop,
    extracted so the narrowing is a function with one roster parameter rather
    than an inline block reading a name from the enclosing scope.

    Passing the whole roster here instead of a condition's own arm
    (`_cond_roster`'s answer) is the S4b-Critical-shaped defect one level up:
    the same comment at the call site below states it, "one key set decides
    BOTH the table and the counts — a number reported against a denominator
    computed over other units." Extracting this loop is what makes that
    defect representable as a unit test at all: the inline block it replaces
    lived inside `command_run`'s per-condition, per-step loop, which no test
    reaches with a real group axis declared — `validate` refuses one outright
    in this build (`E-SWEEP-GROUPS-UNSUPPORTED`).
    """
    out: dict[str, tuple[set[str], UnitList]] = {}
    for level, keys in sorted(levels_for(roster, attribute).items()):
        out[level] = (keys, UnitList([u for u in roster if u.key in keys]))
    return out


def _condition_counts(
    results: "list[ExecutionResult]",
    roster: "UnitList",
    step_name: str,
    cond_index: int,
    arm_members_map: "dict[int, frozenset[str]] | None",
    fold_members: dict[str, frozenset[str]] | None = None,
    weights: dict[str, Any] | None = None,
    clusters: dict[str, str] | None = None,
) -> dict[str, float]:
    """`attrition`'s counts for one condition, narrowed to that condition's own
    arm first — the exact composition `command_run`'s per-condition loop
    calls for a step's counts, and the ONLY thing it calls for them.

    Extracted (after review) because `_cond_roster` and `attrition` tested
    separately cannot tell "the fix is wired into `command_run`" apart from
    "the fix exists and is unused" — which is precisely the shape the bug
    this task fixes took: a narrowed roster computed and then not passed to
    `attrition`. Collapsing narrowing-then-counting into one call removes
    that seam at its root: there is no longer a place in `command_run` where
    a computed `cond_roster` sits beside a stale `attrition(..., roster,
    ...)` a few lines down.
    """
    return attrition(
        results,
        _cond_roster(roster, cond_index, arm_members_map),
        step_name,
        cond_index,
        fold_members=fold_members,
        weights=weights,
        clusters=clusters,
    )


def _condition_report_by_levels(
    roster: "UnitList",
    cond_index: int,
    arm_members_map: "dict[int, frozenset[str]] | None",
    attribute: str,
) -> dict[str, tuple[set[str], "UnitList"]]:
    """`_report_by_levels`, narrowed to one condition's own arm first — the
    exact composition `command_run`'s `report_by` block calls, for the same
    reason `_condition_counts` exists beside `attrition`."""
    return _report_by_levels(_cond_roster(roster, cond_index, arm_members_map), attribute)


def _condition_beside_n(
    beside_n: dict[str, Any],
    roster: "UnitList",
    cond_index: int,
    arm_members_map: "dict[int, frozenset[str]] | None",
) -> dict[str, Any]:
    """`_cond_beside_n`, narrowed to one condition's own arm first — the exact
    composition `command_run` calls to decide whether `technical_n` survives
    for this condition, for the same reason `_condition_counts` exists beside
    `attrition`."""
    return _cond_beside_n(beside_n, _cond_roster(roster, cond_index, arm_members_map), roster)


def _attributed(table: UnitTable, attributes: dict[str, dict[str, Any]]) -> UnitTable:
    """The same table, with each unit's declared attributes merged into its row.

    `data.units.attributes` declares what the roster carries; `reference.md` §
    Templates has `aggregate` reading the unit table, and a template that wants
    to stratify on a declared attribute has nowhere else to read it from — the
    collapsed table holds only *recorded* columns, because that is all a step's
    `io.record` puts there. So the roster is merged in here, at the one boundary
    where `aggregate` is called.

    Merged into the rows rather than into `collapsed` itself, and that is the
    load-bearing choice: `collapsed` is also what `summarize_step` summarizes
    column by column, what `repeat_spread` reads, and what a contrast
    differences. Two consequences, the first of them observable today and
    pinned by `test_a_declared_attribute_is_not_in_the_recorded_column_
    namespace`: an attribute in `collapsed` joins the **recorded-column
    namespace**, so a template returning a metric that merely shares an
    attribute's name collides with something no step ever recorded, and the
    containment around `summarize_step` costs it every metric it computed. And
    a *numeric* attribute (an age, a dose) would be published as a metric with
    its own `ci95` and its own seat in the correction family, and handed a
    repeat-dispersion figure for a value that cannot vary across repeats — not
    reachable while every roster attribute arrives from `csv.DictReader` as a
    string, and the reason not to depend on that staying true. Here an
    attribute reaches `aggregate` and nothing else.

    An attribute is carried through **unchanged**: it comes from the roster
    rather than from an execution, so unlike a recorded numeric column it has
    no repeats to average over. A recorded column of the same name is already
    refused upstream — `io.record` raises `ContractError` ·
    `E-STEP-KEY-COLLISION` — so this merge arbitrates no precedence; it merely
    must not be the thing that papers over that collision, which is why the
    attributes are applied last rather than first.

    `unit` is restored after the merge because nothing refuses an attribute
    *named* `unit` (`units.py` reserves `key`, `paths` and `attributes`, the
    fields of `Unit` itself), and the unit key column must survive: a bootstrap
    draw duplicates units on purpose, and `percentile_of_derived` keeps the real
    keys inside every draw precisely so a template reading `unit` sees the
    roster it was drawn from.

    Row-level, so the four operations the table promises are untouched and
    `columns` — derived from the rows — names the attributes for free.
    """
    # Empty exactly when the config declared no attributes (the caller builds
    # the mapping from the units that have any), so a project that declares
    # none pays nothing: no row list rebuilt on the unresampled call, and none
    # on any of the 2000 draws behind every derived metric's interval.
    if not attributes:
        return table
    rows = []
    for row in table:
        merged = {**row, **attributes.get(row["unit"], {})}
        merged["unit"] = row["unit"]
        rows.append(merged)
    return unit_table_from_rows(rows)


def _comparison_step_blocks(
    comp: "Comparison",
    *,
    roster: "UnitList",
    aggregated: dict[int, dict[str, dict[str, Any]]],
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, float]]],
    derived_by_key: dict[tuple[int, str], dict[str, Any] | None],
    resample_fns_by_key: dict[
        tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
    ],
    seed: int,
    draws: int,
    min_reported_n: float | int | None,
    findings: Collector,
    where: str,
    where_id: str,
    conditions_by_index: dict[int, "Condition"],
) -> tuple[dict[str, dict[str, Any]], list[Member]]:
    """One comparison's delta, per recording step and per metric already in
    `aggregated` — the computation `vs_baseline` and `results.contrasts` both
    rest on, factored out so the two record shapes don't duplicate it.

    A recorded column takes `paired_t_over_units` over the per-unit
    differences, with `cohens_d = cohens_dz(diffs)`. A derived metric — one
    `aggregate` computed, absent any per-unit value to difference — takes
    `paired_delta_of_derived` and `paired_percentile_of_derived` instead, both
    over `base_keys`: the point estimate is `aggregate` evaluated on each side
    over the *intersection*, never the difference of the two conditions' own
    whole-sample `aggregated` values, which under a `within` stratum or unequal
    completion is a number computed over units the interval beside it never
    saw. Each side gets its *own* resample closure
    (`compute_of`/`compute_against`): the two conditions' `cfg` can
    differ on exactly the axis the comparison exists to measure, so evaluating
    one side's closure against both sides' draws is wrong the moment that
    axis changes which formula `aggregate` runs — the documented worked
    example's `analysis.method` sweep does exactly this, and with `pred`/
    `truth` recorded identically across conditions there, a single shared
    closure cancels on every draw: a zero-width `ci95` at zero beside a
    nonzero point-estimate delta. `cohens_d` is `None` for a derived metric,
    for the reason the worked example carries `cohens_d: null` for `r`. Both
    constructions read `n_paired` off `stats.paired_keys` — the intersection
    of the two conditions' completed units, narrowed by `within` when the
    comparison declares one — and record `correction: null` as their default,
    which is what the record says under `correction: none`, since nothing is
    merged over it then.

    The second return value is the correction family's raw material: one
    `Member` per metric entry, carrying the evidence its interval was read from
    — the draw pool for a derived metric, the per-unit differences for a
    recorded column. It travels beside the block rather than inside it because
    a `run.yaml` carrying 2000 floats per metric is unreadable, and `io` never
    promised to serialize one. `where_id` is the caller's own addressing for
    this comparison (`cond:<index>` or `contrast:<id>`, see `_entry_for`), so
    the correction pass can find the entry again without knowing which of the
    two record shapes holds it.

    `W-STATS-CONTRAST-THIN` fires only for a comparison declaring a `within`,
    because that is the scope `reference.md` gives it three times over — §
    Contrasts ("`limits.min_reported_n` applies to a `within` contrast's
    `n_paired`, since a stratified paired comparison is where a small
    denominator is easiest to miss and most disclosive"), the § The one config
    file comment, and the § Validation row. `min_reported_n: 10` is in every
    generated config, so warning on every comparison would fire on any pilot
    under ten units for a comparison the document never scoped it to.

    `confounded`/`differs_on` mark, on each metric entry, a comparison whose
    two conditions disagree on more than one swept axis: the delta then mixes
    two effects and no amount of correct pairing separates them — the
    factorial main-effects problem core refuses to solve, so it is marked
    rather than reported as if it were clean. Both keys are absent, not
    `False`/`[]`, when only one axis differs. `paired` stays hard `True`
    here: the crossed-*group*-axis case `reference.md` shows with
    `paired: false` and `unpaired_*` needs a group axis or
    `allocation: between`, both refused (`E-SWEEP-GROUPS-UNSUPPORTED`,
    `E-DATA-ALLOCATION-UNSUPPORTED`), so it is unreachable in this build.
    """
    differs_on = _differing_axes(
        conditions_by_index[comp.of], conditions_by_index[comp.against]
    )
    confounded = len(differs_on) > 1
    allowed = units_matching(roster, comp.within)
    of_steps = {k[1] for k in collapsed_by_key if k[0] == comp.of}
    against_steps = {k[1] for k in collapsed_by_key if k[0] == comp.against}
    block: dict[str, dict[str, Any]] = {}
    members: list[Member] = []
    for step_name in sorted(of_steps & against_steps):
        of_collapsed = collapsed_by_key[(comp.of, step_name)]
        against_collapsed = collapsed_by_key[(comp.against, step_name)]
        base_keys = paired_keys(of_collapsed, against_collapsed, allowed)
        of_summary = aggregated.get(comp.of, {}).get(step_name, {})
        against_summary = aggregated.get(comp.against, {}).get(step_name, {})
        of_derived = derived_by_key.get((comp.of, step_name)) or {}
        against_derived = derived_by_key.get((comp.against, step_name)) or {}
        metric_block: dict[str, Any] = {}
        # `by` is the one key in a step block that is not a metric: it holds the
        # reporting strata (`reference.md` § Reporting strata), a mapping of
        # attribute to level to *another* metric block. Left in, it would be
        # differenced as though it were a metric — and, sorting before every
        # real name, would be the first entry of every contrast block.
        for metric_key in sorted((set(of_summary) & set(against_summary)) - {"by"}):
            is_derived = metric_key in of_derived or metric_key in against_derived
            if is_derived:
                compute_of = (resample_fns_by_key.get((comp.of, step_name)) or {}).get(
                    metric_key
                )
                compute_against = (resample_fns_by_key.get((comp.against, step_name)) or {}).get(
                    metric_key
                )
                n_paired = len(base_keys)
                interval = None
                delta = None
                # Reset per metric, beside the other two: assigned only inside
                # `n_paired >= 2` below, so a one-unit intersection would leave
                # the name unbound where the member is built (a `NameError` on
                # the first pass) or — worse, at function scope — hand a later
                # metric the *previous* metric's draw pool, which nothing
                # downstream could detect.
                resampled = None
                if compute_of is not None and compute_against is not None:
                    # Point estimate and interval from the same two calls over
                    # the same `base_keys`, so neither can drift onto a
                    # different unit set from the other.
                    delta = paired_delta_of_derived(
                        of_collapsed,
                        against_collapsed,
                        base_keys,
                        compute_of,
                        compute_against,
                    )
                    if n_paired >= 2:
                        resampled = paired_percentile_of_derived(
                            of_collapsed,
                            against_collapsed,
                            base_keys,
                            compute_of,
                            compute_against,
                            seed,
                            draws=draws,
                        )
                        interval = resampled.interval
                metric_block[metric_key] = {
                    "delta": delta,
                    "basis": "units",
                    "paired": True,
                    "method": interval.method if interval else None,
                    "n_paired": n_paired,
                    "ci95": [interval.low, interval.high] if interval else None,
                    "cohens_d": None,
                    "correction": None,
                }
            else:
                col_keys = [
                    k
                    for k in base_keys
                    if metric_key in of_collapsed[k] and metric_key in against_collapsed[k]
                ]
                diffs = [
                    of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
                    for k in col_keys
                ]
                interval = paired_t_over_units(diffs)
                n_paired = len(col_keys)
                metric_block[metric_key] = {
                    "delta": mean_of(diffs),
                    "basis": "units",
                    "paired": True,
                    "method": interval.method if interval else None,
                    "n_paired": n_paired,
                    "ci95": [interval.low, interval.high] if interval else None,
                    "cohens_d": cohens_dz(diffs),
                    "correction": None,
                }
            if confounded:
                # Marked, not merely reported: a delta mixing two axes is the
                # factorial main-effects problem, which core refuses to
                # separate. `differs_on` names them so a reader knows which.
                metric_block[metric_key]["confounded"] = True
                metric_block[metric_key]["differs_on"] = list(differs_on)
            # `Member` requires exactly one of `pool`/`diffs` wherever there is
            # an interval to correct: the draws a percentile interval was read
            # off, or the per-unit differences a *t* interval was computed
            # from. An entry with no `ci95` carries neither and is dropped by
            # `family_members` before either is read.
            members.append(
                Member(
                    where=where_id,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if is_derived and resampled else None,
                    diffs=None if is_derived else tuple(diffs),
                    # Placeholder: this function only sees one comparison, not
                    # the whole family. The caller that concatenates
                    # `vs_baseline_members` and `contrast_members` reassigns
                    # this to the position in that combined, ordered list —
                    # the only point where the full declaration order exists.
                    declaration_index=0,
                )
            )
            if comp.within is not None and min_reported_n is not None and n_paired < min_reported_n:
                findings.warn(
                    "W-STATS-CONTRAST-THIN",
                    "limits.min_reported_n",
                    f"{where}, step {step_name!r} metric {metric_key!r}: n_paired "
                    f"{n_paired} is below limits.min_reported_n ({min_reported_n})",
                )
        if metric_block:
            block[step_name] = metric_block
    return block, members


def _compute_vs_baseline(
    *,
    doc: dict[str, Any],
    conditions: "list[Condition]",
    roster: "UnitList | None",
    aggregated: dict[int, dict[str, dict[str, Any]]],
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, float]]],
    derived_by_key: dict[tuple[int, str], dict[str, Any] | None],
    resample_fns_by_key: dict[
        tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
    ],
    seed: int,
    draws: int,
    findings: Collector,
) -> tuple[dict[int, dict[str, dict[str, dict[str, Any]]]] | None, list[Member]]:
    """Every non-baseline condition's own delta against the baseline, per
    recording step and per metric already in `aggregated` — see
    `_comparison_step_blocks` for how one comparison's block is built.

    Returns `None`, not `{}`, when nothing survives: no baseline, no metric in
    common between a condition and the baseline, or (per
    `contrasts.resolve_contrasts`'s own docstring) no declared baseline at
    all. `assemble_run_yaml` omits the key entirely in that case rather than
    writing an empty block that would claim a comparison was made and found
    nothing.

    The members every comparison produced come back beside the block, for the
    correction family `command_run` builds over both record shapes at once.
    """
    if roster is None:
        return None, []
    comparisons = _baseline_comparisons(doc, conditions)
    if not comparisons:
        return None, []
    min_reported_n = (doc.get("limits") or {}).get("min_reported_n")
    conditions_by_index = {c.index: c for c in conditions}
    out: dict[int, dict[str, dict[str, dict[str, Any]]]] = {}
    members: list[Member] = []
    for comp in comparisons:
        block, block_members = _comparison_step_blocks(
            comp,
            roster=roster,
            aggregated=aggregated,
            collapsed_by_key=collapsed_by_key,
            derived_by_key=derived_by_key,
            resample_fns_by_key=resample_fns_by_key,
            seed=seed,
            draws=draws,
            min_reported_n=min_reported_n,
            findings=findings,
            where=f"condition {comp.of} ({comp.id!r}) vs baseline",
            where_id=f"cond:{comp.of}",
            conditions_by_index=conditions_by_index,
        )
        if block:
            out[comp.of] = block
            members.extend(block_members)
    return out or None, members


def _compute_declared_contrasts(
    *,
    doc: dict[str, Any],
    conditions: "list[Condition]",
    roster: "UnitList | None",
    aggregated: dict[int, dict[str, dict[str, Any]]],
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, float]]],
    derived_by_key: dict[tuple[int, str], dict[str, Any] | None],
    resample_fns_by_key: dict[
        tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
    ],
    seed: int,
    draws: int,
    findings: Collector,
) -> tuple[list[dict[str, Any]] | None, list[Member]]:
    """Every declared `statistics.contrasts` entry's delta, as `results.contrasts`
    — `reference.md` § Contrasts: claims that aren't condition-vs-baseline: "a
    contrast belongs to neither of its sides", so it lands beside the
    conditions rather than inside one, as a flat list rather than keyed by
    condition index the way `vs_baseline` is.

    `of`/`against` are recorded **with their index** even though the config
    names them by label alone — `sweep.condition_dir_name`'s `<nn>_<label>`
    form, the same the run's own `conditions/` directories use — because the
    record resolves what the config abbreviates.

    Returns `None`, not `[]`, when nothing was declared: this is the sibling
    no-op `docs/superpowers/spec-defects.md` used to carry (Task 6 retired
    `E-STATS-CONTRASTS-UNSUPPORTED`, so a declared contrast validated clean
    with nothing downstream to compute it) — closed here rather than in a
    later slice.

    The members every contrast produced come back beside the list, joining the
    `vs_baseline` ones in one family: `reference.md` counts every interval a
    reader is shown, and a declared contrast is one of them.
    """
    if roster is None:
        return None, []
    comparisons = _declared_comparisons(doc, conditions)
    if not comparisons:
        return None, []
    label_by_index = {c.index: c.label for c in conditions}
    min_reported_n = (doc.get("limits") or {}).get("min_reported_n")
    conditions_by_index = {c.index: c for c in conditions}
    out: list[dict[str, Any]] = []
    members: list[Member] = []
    for comp in comparisons:
        block, block_members = _comparison_step_blocks(
            comp,
            roster=roster,
            aggregated=aggregated,
            collapsed_by_key=collapsed_by_key,
            derived_by_key=derived_by_key,
            resample_fns_by_key=resample_fns_by_key,
            seed=seed,
            draws=draws,
            min_reported_n=min_reported_n,
            findings=findings,
            where=f"contrast {comp.id!r}",
            where_id=f"contrast:{comp.id}",
            conditions_by_index=conditions_by_index,
        )
        members.extend(block_members)
        entry: dict[str, Any] = {
            "id": comp.id,
            "of": condition_dir_name(comp.of, label_by_index.get(comp.of) or ""),
            "against": condition_dir_name(comp.against, label_by_index.get(comp.against) or ""),
        }
        entry.update(block)
        out.append(entry)
    return out or None, members


def _entry_for(
    vs_baseline: dict[int, dict[str, dict[str, dict[str, Any]]]] | None,
    contrasts: list[dict[str, Any]] | None,
    where_id: str,
    step: str,
    metric: str,
) -> dict[str, Any] | None:
    """The record entry a corrected field belongs on, in whichever shape holds it.

    `where_id` is `cond:<index>` for a `vs_baseline` block and `contrast:<id>`
    for a declared one — the same string `Member.where` carries, so the
    correction pass never has to know which of the two record shapes it is
    looking at.

    The prefixes are what make `where` collision-proof, and that is not
    cosmetic: `family_shape` counts comparisons as the number of distinct
    `where` values, so a declared contrast carrying `id: "1"` — which
    `validate` permits — would otherwise be the same comparison as condition 1.
    A family short by one comparison is a *larger* α and an interval narrower
    than the evidence supports, in the direction no reader can check.
    """
    kind, _, rest = where_id.partition(":")
    if kind == "cond" and vs_baseline is not None:
        block = vs_baseline.get(int(rest), {}).get(step, {})
        return block.get(metric)
    if kind == "contrast":
        for entry in contrasts or []:
            if entry.get("id") == rest:
                step_block = entry.get(step)
                if isinstance(step_block, dict) and metric in step_block:
                    found = step_block[metric]
                    return found if isinstance(found, dict) else None
    return None


def command_validate(config_path: Path) -> int:
    c = Collector()
    validate_config(config_path, c)
    if c.findings:
        print(config_path)
        print(c.render())
    else:
        print(f"  ✓ config valid · {config_path}")
    return c.exit_code()


def command_run(config_path: Path) -> int:
    c = Collector()
    experiment = _preloaded_experiment(config_path)
    # phases 1-2: resolve, walk up, load, validate
    doc = validate_config(config_path, c, experiment=experiment)
    if c.findings:
        print(config_path)
        print(c.render())
    if doc is None or c.has_errors:
        return EXIT_WRONG

    repo_root = find_repo_root(config_path)
    git = git_provenance(config_path, config_path)  # phase 3: clean src/**+templates/**
    if git.code_dirty:
        dirty_c = Collector()
        dirty_c.error(
            "E-CODE-DIRTY", "src/** or templates/**", "uncommitted changes; commit them first"
        )
        print(dirty_c.render())
        return EXIT_WRONG
    if experiment is None:  # phase 3: entrypoint imports
        # Unreachable in practice — a failed import is `E-ENTRYPOINT-IMPORT` and a
        # missing one `E-ENTRYPOINT-REQUIRED`, both errors that returned above. Kept
        # so `run` never proceeds on `None` if a future check stops being fatal.
        experiment = load_experiment(repo_root, doc["entrypoint"])

    digest = design_digest(doc)  # phase 5: pin hashes
    input_dir = Path(doc["data"]["input_dir"]).expanduser()
    output_dir = Path(doc["data"]["output_dir"]).expanduser()
    units_decl: dict[str, Any] | None = (doc.get("data") or {}).get("units")
    # phase 5: roster. `technical_n` — `{min, max, median}` over the measurement
    # counts rows sharing a key collapsed from — travels to every metric block as
    # `summarize_step`'s `beside_n`, which is the route for a fact `reference.md`
    # shows *beside* `n` rather than inside it (`stats.summarize_step` states the
    # two-route rule and which document sentence decides each). `provenance.units`
    # is documented as exactly `{n, key}`, so parking it there would invent a
    # `run.yaml` field no document describes.
    roster, technical_n, _columns = (
        resolve_units(units_decl, input_dir) if units_decl else (None, None, frozenset())
    )
    # Carried only when the input path actually merged rows. A run whose STEP does
    # the measuring (`io.record(..., measurement=)`) has one input row per unit, so
    # an ungated `technical_n` would report `{min: 1, max: 1, median: 1}` beside a
    # `measurements.parquet` holding three rows per unit — a false claim of no
    # replication, which is worse than the missing one. The step path's own counts
    # are not carried in this build; see `docs/superpowers/spec-defects.md`.
    beside_n: dict[str, Any] = {}
    if technical_n is not None and technical_n["max"] > 1:
        beside_n["technical_n"] = technical_n
    # `data.units.weight_by` names a unit attribute holding the inverse sampling
    # probability (`reference.md` § Weighted samples). Two facts reach the record
    # from it, by the two different routes `stats.summarize_step` describes:
    # `weighted_by` sits BESIDE `n`, exactly where the document's own example
    # prints it, and `effective` — Kish's size — JOINS `n`, so it travels in
    # `attrition`'s counts rather than here.
    #
    # The mapping itself travels to `summarize_step` as well, which is what makes
    # `weighted_by` a fact about the arithmetic rather than a marker beside an
    # unweighted number: every recorded column's `value` becomes the weighted
    # mean, its interval `weighted_t_over_units`, and its `n.effective` Kish's
    # size over that column's own units (`stats.summarize_step` says why all
    # three move together, and why `effective` is per column while `attrition`'s
    # is per condition). A derived metric is not weighted by core — the weight
    # column reaches `aggregate` as a unit attribute, through `_attributed`, so a
    # template weights whatever its own metric needs weighting by.
    #
    # Passed as the roster holds the values, `str` and all, for the same reason
    # `attrition` takes them that way: `stats.checked_weights` reads
    # `units.usable_weight`, the single authority `validate` approved the config
    # against, and a coercion here would be a second notion of a usable weight.
    weight_by = (units_decl or {}).get("weight_by")
    weights: dict[str, Any] | None = None
    weighted_beside: dict[str, Any] = {}
    if isinstance(weight_by, str) and weight_by and roster is not None:
        # `.get`, not `[...]`: `validate` guarantees `weight_by` names a declared
        # attribute and `_from_table` gives every unit every declared attribute,
        # so a missing one is a core defect — and `None` reaches
        # `kish_effective_n`, which refuses it as `E-DATA-WEIGHT-INVALID` under
        # the same single authority `validate` used. A comprehension that skipped
        # the unit instead would quietly shrink the denominator.
        weights = {u.key: u.attributes.get(weight_by) for u in roster}
        weighted_beside["weighted_by"] = weight_by
        beside_n["weighted_by"] = weight_by
    # Read straight from the declaration, not re-derived: `validate` guarantees a
    # truthy `cluster_by` is a declared attribute every unit carries (an empty or
    # wrongly-typed one is an error that returned above), so this is the same
    # string `units.clusters_of` was approved against.
    cluster_by = (units_decl or {}).get("cluster_by")
    # One fact reaches the record from it, and it JOINS `n`: `clusters`, the number
    # of distinct clusters the units a metric was computed over fall in
    # (`reference.md` § The three-part `n`, joined by `clusters` "whenever
    # `cluster_by` makes the cluster the inferential draw"; § Clustered units calls
    # it "the effective sample size alongside the unit count"). So it travels in
    # `attrition`'s counts, exactly where `effective` goes, rather than in
    # `beside_n` — the two routes `stats.summarize_step` describes, and nothing in
    # the documents shows a `clustered_by` sibling of `weighted_by`.
    #
    # The membership mapping itself goes to `summarize_step` as well, for the reason
    # `weights` does: a ragged column's clusters are its own, and only the call that
    # sees which units carried the column can count them.
    #
    # `units.clusters_of` is the single authority, the same one `validate`, the fold
    # basis and the partition read, so a unit carrying no value for the attribute
    # raises `E-DATA-CLUSTER-UNKNOWN` here rather than being invented a cluster of
    # its own.
    #
    # **That window is NOT fully closed, and saying it was is what this comment
    # used to do.** `command_run` does validate first against the same roster, but
    # `E-DATA-CLUSTER-UNKNOWN` is not among the checks `validate` runs for a
    # value-level absence — it is only ever raised, and `_check_cluster_by` tests
    # the declaration against `attributes`, not each unit's value. One shape slips
    # through: `cluster_by` naming `measurements.by` where **every unit has exactly
    # one measurement row**. The collapse drops that attribute, the constancy check
    # needs two rows to see a disagreement, so `validate` exits 0 and `run` raises
    # here. `stratify_by` has a declaration-time refusal for the same shape
    # (`E-REPL-FOLD-STRATIFY-UNKNOWN`); `cluster_by` has no counterpart yet, and
    # that asymmetry is the gap rather than this line.
    clusters: dict[str, str] | None = None
    if isinstance(cluster_by, str) and cluster_by and roster is not None:
        clusters = clusters_of(roster, cluster_by)
    # `fold_basis` is what turns `{kind: fold, k: all}` into a real count and what
    # `_fold_k` checks a declared `k` against — the resolved roster's units, or its
    # clusters when `data.units.cluster_by` declares the units are not independent
    # draws, since a cluster is indivisible and leave-one-out is then
    # leave-one-*cluster*-out (`reference.md` § Validation, *Folds fit inside the
    # clusters* and *Leave-one-out is affordable*). `units.fold_basis` is the one
    # derivation, the same `validate` bounded `k` with, applied here to the roster
    # `run` re-resolves fresh rather than trusted from the earlier pass.
    levels = resolve_repeats(
        doc,
        digest,
        fold_basis=fold_basis(roster, cluster_by) if roster is not None else None,
    )
    repeats = cross_levels(levels)
    labels = [r.label for r in repeats if r.label] or [""]
    fold_level = next((lv for lv in levels if lv.kind == "fold"), None)
    partitions: list[list[Unit]] | None = None
    if fold_level is not None:
        # A `fold` level with no roster to partition is refused by `validate`
        # (`E-REPL-FOLD-NO-UNITS`), which already returned above — so this is
        # unreachable with `roster is None`. Raised, not asserted, and not an
        # `or []` fallback: an `assert` disappears under `python -O`, which
        # `reference.md` § Errors names as precisely the wrong property for the
        # only guard on a condition nothing else detects. If the invariant is
        # ever wrong, every fold would otherwise run against nothing.
        if roster is None:
            raise ContractError(
                "a `fold` level is declared but no roster resolved; `validate` refuses "
                "that config (`E-REPL-FOLD-NO-UNITS`), so core's resolved state "
                "disagrees with itself about this fold",
                code="E-RUN-FOLD-UNRESOLVED",
            )
        # `clusters` and `strata` together, or neither. Both change WHICH units a
        # fold holds rather than how many folds there are, and each is unreachable
        # from the call that only passes a count:
        #
        # - Without `clusters` a clustered design gets the right fold count (the
        #   basis above) and the wrong membership — every fold trains on other
        #   units of the cluster it tests on, which `reference.md` § Clustered units
        #   calls "the difference between a valid evaluation and a leaky one" and
        #   `experimental-designs.md` § Mistakes core prevents requires to be
        #   structurally impossible. It is the whole point of declaring one, and no
        #   interval construction can repair a metric that was already leaked into.
        # - Without `strata` a declared `fold.stratify_by` is checked and then
        #   ignored, which § Repeat kinds contradicts by calling such a fold
        #   "stratified".
        #
        # Wiring one and not the other would ship half a guarantee that looks whole,
        # so they arrive at the same call.
        #
        # The stratum mapping is built here rather than by a `strata_of` beside
        # `clusters_of`, and the difference is deliberate: `clusters_of` raises
        # `E-DATA-CLUSTER-UNKNOWN`, a code naming the wrong declaration for a reader
        # whose config declares `fold.stratify_by`, and which code a missing value
        # belongs under is a property of the declaration being served — `holdout`
        # and `assign` will each read the same attribute under their own.
        #
        # Indexed, not `.get`-ed, and total over the roster because it has to be
        # (`units.partition_units` raises `KeyError` on a gap, by contract): every
        # unit carries every declared attribute, since `units._from_table` builds
        # `Unit.attributes` from `data.units.attributes` for every row and a `glob`
        # source refuses an `attributes` declaration outright. `validate` guarantees
        # the name is one of those attributes (`E-REPL-FOLD-STRATIFY-UNKNOWN`), so a
        # missing key is a core defect, exactly as it is for the weights. A unit
        # whose cell is blank is stratum `''` — a real stratum of its own, which is
        # what the source says it is; a sentinel string would instead merge those
        # units into whatever real stratum happened to be spelled the same way.
        #
        # One path rebuilds `Unit.attributes` after resolution and was the
        # exception: `units.collapse_measurements` drops the name equal to
        # `data.units.measurements.by`, so a config stratifying on the measurement
        # axis itself reached a bare `KeyError` here rather than a diagnostic. Task
        # 11 named it unreachable because `E-REPL-FOLD-STRATIFY-UNSUPPORTED` refused
        # every `stratify_by`; task 12 retired that code, which made it reachable
        # and turned the note into a defect. It is now refused from the declaration
        # by `_check_fold_stratify_by` under `E-REPL-FOLD-STRATIFY-UNKNOWN` — a
        # `measurements.by` does not survive resolution as an attribute, which is
        # that code's own meaning — so the subscript below cannot miss.
        #
        # Stringified for the reason `clusters_of` stringifies: a stratum is a label,
        # nothing downstream does arithmetic on it, and one type keeps a hand-built
        # roster and a table-sourced one giving the same split.
        strata: dict[str, str] | None = None
        if fold_level.stratify_by:
            strata = {u.key: str(u.attributes[fold_level.stratify_by]) for u in roster}
        partitions = partition_units(
            roster, fold_level.n, digest, clusters=clusters, strata=strata
        )
    fold_members = fold_members_for(levels, partitions) if partitions is not None else None

    conditions = expand(doc)
    sweep_block = doc.get("sweep") or {}
    swept_paths = _wide_swept_paths(sweep_block)
    # One frozenset of unit keys per condition that selects a group axis — `None`
    # for a design declaring none. Unreachable today (see `_resolved_group_axes`):
    # a declared `sweep.groups` axis returns `E-SWEEP-GROUPS-UNSUPPORTED`, which
    # stops `run` above before this line. Built anyway, rather than left for the
    # slice that retires that refusal, because `execute_plan`'s subset view is the
    # rest of this feature and a config that never reaches it is not evidence the
    # wiring is wrong — only that nothing yet asks for it end to end.
    #
    # Gated on `selector_paths(sweep_block)`, not on `group_axes` itself: `expand`
    # already used `selector_paths` to decide which paths are group cells, so
    # `conditions` below carries `Condition.selectors` naming every axis
    # `selector_paths` names — regardless of whether that axis's `levels` also
    # satisfy `_resolved_group_axes`'s stricter all-`str` requirement, the same
    # requirement `validate._check_assign`'s own `by_attribute` branch applies
    # before it ever calls `arms_of`. Gating on `group_axes` instead would let a
    # `sweep.groups` shape fault — no check for it exists yet, see
    # `_resolved_group_axes` — silently skip arm narrowing entirely: every
    # condition on the malformed axis would get the whole roster, which is
    # exactly the outcome two declared arms exist to make impossible. Gating on
    # `selector_paths` instead means `arm_members` is still called whenever
    # `expand` treated the config as having a group axis, so a resolution gap
    # surfaces as `arm_members`'s own `KeyError` — a caller-disagreement bug to
    # see, not a config to silently accept — rather than as a silently
    # unnarrowed run.
    group_axes = _resolved_group_axes(units_decl, sweep_block)
    arm_members_map = (
        arm_members(roster, group_axes, conditions)
        if selector_paths(sweep_block) and roster is not None
        else None
    )
    plan = build_plan(  # phase 4
        experiment,
        conditions=[(c.index, c.label) for c in conditions],
        repeat_labels=labels,
    )
    cfgs: dict[int, Config] = {
        # The whole `Condition`, not `dict(c.values)`: a group cell's path names
        # units rather than a parameter, and `c.selectors` is which — the answer
        # `expand` computed once, travelling with the values it qualifies.
        c.index: resolve_condition_cfg(doc, c)
        for c in conditions
    }
    cfgs[-1] = resolve_wide_cfg(doc, swept_paths)

    ch = code_hash(repo_root)
    ph = parameters_hash(doc)
    manifest = build_manifest(input_dir, doc["data"]["input_manifest_policy"])
    lock_path, lock_hash = uv_lock_info(repo_root)
    if lock_path is None:
        # A warning, not an error: it must not change the exit code. There are
        # legitimate reasons to proceed unpinned — including the bootstrapping case
        # this project is in right now, where a scaffolded project cannot resolve a
        # lockfile until `publishable` is published to an index (see
        # docs/superpowers/spec-defects.md).
        warn_c = Collector()
        warn_c.warn(
            "W-ENV-UNLOCKED",
            "environment",
            f"no uv.lock found at {repo_root}; the environment is not pinned, and "
            "`reproduce` will not be able to restore it",
        )
        print(warn_c.render())

    run_dir = allocate_run_dir(output_dir, ch, datetime.now(UTC))  # phase 6: first creation
    with RunLock(run_dir):
        (run_dir / "manifest").mkdir()
        (run_dir / "manifest" / "input.json").write_text(json.dumps(manifest, indent=2))
        (run_dir / "environment").mkdir()
        # `pyproject.toml` always exists (uv is mandatory) so it is always captured;
        # `uv.lock` is copied only when one was found.
        (run_dir / "environment" / "pyproject.toml").write_bytes(
            (repo_root / "pyproject.toml").read_bytes()
        )
        if lock_path is not None:
            (run_dir / "environment" / "uv.lock").write_bytes(lock_path.read_bytes())

        # `sweep.yaml` next to `manifest/input.json`, inside the lock, and *before*
        # the first execution: `docs/reference.md` § The other files a run writes
        # calls it "settled before the first execution and never touched again",
        # and `resume` reads it back rather than re-deriving it. Nothing in it
        # comes from `results` — every argument is settled by the time the plan
        # exists — so writing it after `execute_plan` bought nothing and left a
        # run that died inside the loop with no plan on disk at all.
        mode = ((doc.get("replication") or {}).get("order")) or "as_declared"
        order_seed = order_seed_for(digest) if mode == "randomized" else None
        declared_pairs = [(c.index, lf.label) for c in conditions for lf in repeats]
        execution_order = realize_order(declared_pairs, levels, mode, order_seed or 0)
        # Only when an order was actually realized. `realize_order` is the identity
        # under `as_declared`, but `_apply_execution_order` is not: it regroups
        # repeat executions pair-major, where `build_plan` lays them out step-major
        # (for each step, for each repeat). Applying it unconditionally silently
        # changed the execution order of every `as_declared` design with ≥2
        # repeat-scope steps and ≥2 repeats — a different `started_at` sequence and
        # a differently ordered `executions.jsonl` for a run that declared no
        # shuffle at all. Pair-major is the right grain once an order has been
        # realized, because `execution_order` records `(condition, repeat)` pairs
        # and the plan must match the record; under `as_declared` there is no
        # record to match and the plan's own layout stands.
        if mode == "randomized":
            plan = _apply_execution_order(plan, execution_order)

        (run_dir / "sweep.yaml").write_text(
            yaml.safe_dump(
                sweep_document(
                    conditions,
                    levels,
                    repeats,
                    digest,
                    mode,
                    execution_order,
                    order_seed,
                    partitions=partitions,
                    sample_seed=sample_seed_for(doc),
                ),
                sort_keys=False,
            )
        )

        # `allocation.json` — settled beside `sweep.yaml`, before the first
        # execution and never touched again, per § The other files a run
        # writes: both are partitions of one roster drawn once. `None` when
        # `group_axes` is empty — no arm assignment resolved for this run —
        # matching "present when either [an arm assignment or a holdout] is
        # declared"; `holdout` is never in this build's document at all
        # (`E-DATA-HOLDOUT-UNSUPPORTED` refuses every declaration of it).
        alloc_doc = build_allocation_document(roster, group_axes) if roster is not None else None
        alloc_hash: str | None = None
        if alloc_doc is not None:
            (run_dir / "allocation.json").write_text(json.dumps(alloc_doc, indent=2))
            alloc_hash = allocation_hash(alloc_doc)

        results = execute_plan(  # phase 7
            plan=plan,
            run_dir=run_dir,
            input_dir=input_dir,
            cfgs=cfgs,
            repeats=repeats,
            digest=digest,
            units=roster,
            max_failed_fraction=(doc.get("limits") or {}).get("max_failed_fraction"),
            fold_members=fold_members,
            arm_members=arm_members_map,
            measurements=(units_decl or {}).get("measurements"),
        )

        status = run_status(results)
        # No roster means nothing to aggregate over, so `aggregated` stays `None`
        # rather than an empty dict — `assemble_run_yaml` omits the key entirely in
        # that case, instead of every condition reporting a misleading empty
        # `aggregated: {}`.
        aggregated: dict[int, dict[str, dict[str, Any]]] | None = None
        # Same absent-not-empty rule as `aggregated`, for the same reason: a run
        # with no baseline and no declared contrast compares nothing, and
        # `_compute_vs_baseline` (below, only reached when `roster is not None`)
        # returns `None` rather than `{}` in that case.
        vs_baseline: dict[int, dict[str, dict[str, dict[str, Any]]]] | None = None
        # Same rule, same reason, for the declared side: no `statistics.contrasts`
        # entry means nothing to report, and `_compute_declared_contrasts` returns
        # `None` rather than `[]`.
        contrasts_out: list[dict[str, Any]] | None = None
        # The sweep family's raw material, declared out here for the same reason
        # `vs_baseline` and `contrasts_out` are: the hypothesis family is
        # rebuilt from these members, and `hypotheses.evaluate` runs whether or
        # not there is a roster — a `reported` hypothesis names a `summary`
        # step's `Estimate`, which is reachable with no `data.units` at all.
        comparison_members: list[Member] = []
        # Bound once and read twice — the sweep family below and the hypothesis
        # family after it are corrected by the *same* declared method, and two
        # spellings of one default is how they would come to disagree.
        correction_method = (doc.get("statistics") or {}).get("correction") or "holm"
        # Condition metadata `ExecutionResult` cannot carry: `Execution` holds
        # index and label but not `is_baseline` or the swept `values`, and
        # `reference.md` § The two files shows both on the condition entry.
        # `dict(...)` unwraps `Condition.values`'s `MappingProxyType`, which
        # `yaml.safe_dump` has no representer for.
        condition_meta = {
            c.index: {"label": c.label, "is_baseline": c.is_baseline, "values": dict(c.values)}
            for c in conditions
        }
        # Declared here rather than only under `if roster is not None:` below: a
        # `summary` step's `Estimate` is reachable whether or not `data.units` is
        # declared at all (`reference.md` § Units: undeclared `data.units` still
        # runs, it just leaves `io.units`/`io.units.train` unreachable), so the
        # warning this collector carries must not be coupled to a roster existing.
        aggregate_c = Collector()
        # An `Estimate` reaches here already valid (`coerce_scalars` refused a
        # `ci95` with no `method`, E-STEP-ESTIMATE-METHOD, and any non-`summary`
        # scope, E-STEP-ESTIMATE-SCOPE) — the one thing left unchecked is `n`.
        # `n` is optional (the run completes either way) but its absence beside
        # a real `ci95` is surfaced rather than passed in silence: an interval
        # with no stated denominator is exactly the disclosure risk
        # `limits.min_reported_n` exists to catch, and `study add` cannot check
        # what it cannot see. A bare `Estimate` with no `ci95` makes no interval
        # claim at all, so it is not warned about here.
        for r in results:
            if r.execution.scope != "summary":
                continue
            for key, value in (r.returned or {}).items():
                if isinstance(value, Estimate) and value.ci95 is not None and value.n is None:
                    aggregate_c.warn(
                        "W-STEP-ESTIMATE-N",
                        f"{r.execution.step_name}.{key}",
                        "reports a ci95 with no `n`; an interval with no stated "
                        "denominator is the disclosure risk `limits.min_reported_n` "
                        "exists to catch, and `study add` cannot check what it cannot see",
                    )
        if roster is not None:
            # `condition_index` is guarded per condition: core aggregates within
            # each condition and never pools across conditions — an unguarded
            # filter would let a same-named step from another condition mark this
            # one as having a recording step it never ran.
            template = get_template(doc.get("experiment_type", ""))
            resample_seed_value = resample_seed(digest)
            # The roster is resolved once per run and shared across every
            # condition, so this mapping is built once too — it is the same
            # attributes for every condition, every step and every draw
            # (`_attributed` says what it is for). The `if u.attributes` filter
            # is what makes it *empty* — rather than a unit-keyed mapping of
            # empty dicts, which is truthy — when the config declares no
            # `data.units.attributes`, so `_attributed`'s early return actually
            # fires and such a project never rebuilds a row list at all.
            unit_attributes = {u.key: dict(u.attributes) for u in roster if u.attributes}
            # `statistics.resample` isn't honored yet (`E-STATS-RESAMPLE-UNSUPPORTED`
            # refuses a declared one), so this is the one place the default
            # `reference.md` § How a metric becomes a number documents — bootstrap
            # at 2000 — is a real, passed value rather than `summarize_step`'s own
            # default taking effect unseen at every call site that forgets it.
            derived_metric_draws = 2000
            aggregate_where = f"{doc.get('experiment_type', '')}.aggregate"
            # `aggregate` is user code in exactly the sense `runner.py`'s own
            # step execution is — "a failed execution never stops the run" —
            # but this call sits outside that `try`, in phase 8, after every
            # execution already completed. Uncontained, a template whose
            # `aggregate` raises anything but `PublishableError`/`OSError`
            # would crash before `run.yaml` is ever written, discarding every
            # completed execution over one metric core couldn't compute.
            # Contained here the same way: the failure is disclosed (below)
            # and the run's other results — and `run.yaml` itself — survive.
            aggregated = {}
            # Kept beside `aggregated` so `vs_baseline` (below, once every
            # condition's own metrics are in) can recompute a paired interval
            # without re-running `collapse_repeats` or `aggregate` a second
            # time: the per-unit table, what `aggregate` returned by name, and
            # the resample closure `_make_resample_fn` built for it, one entry
            # per (condition, recording step) actually seen this run.
            collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, float]]] = {}
            derived_by_key: dict[tuple[int, str], dict[str, Any] | None] = {}
            resample_fns_by_key: dict[
                tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
            ] = {}
            for cond in conditions:
                recording_steps = {
                    r.execution.step_name
                    for r in results
                    if r.execution.scope == "repeat"
                    and r.execution.condition_index == cond.index
                    and r.rows
                }
                aggregated[cond.index] = {}
                # `_condition_beside_n` narrows to this condition's own arm
                # before deciding whether `technical_n` survives — the read
                # side of the same narrowing `execute_plan` already applies to
                # what this condition's executions were actually handed. Kept
                # as ONE call, not a `cond_roster` computed here and consumed
                # a few lines down: that two-step shape is exactly how the bug
                # this task fixes happened — a narrowed roster computed and
                # then not passed to `attrition`.
                cond_beside_n = _condition_beside_n(beside_n, roster, cond.index, arm_members_map)
                for step_name in sorted(recording_steps):
                    collapsed = collapse_repeats(
                        results, step_name, cond.index, fold_members=fold_members
                    )
                    counts = _condition_counts(
                        results,
                        roster,
                        step_name,
                        cond.index,
                        arm_members_map,
                        fold_members=fold_members,
                        weights=weights,
                        clusters=clusters,
                    )
                    max_ineligible = (doc.get("limits") or {}).get("max_ineligible_fraction")
                    if (
                        isinstance(max_ineligible, (int, float))
                        and not isinstance(max_ineligible, bool)
                        and counts["resolved"]
                        and counts["ineligible"] / counts["resolved"] > max_ineligible
                    ):
                        aggregate_c.warn(
                            "W-DATA-INELIGIBLE",
                            "limits.max_ineligible_fraction",
                            f"condition {cond.index}, step {step_name!r}: "
                            f"{counts['ineligible']} of {counts['resolved']} units are "
                            f"ineligible, above limits.max_ineligible_fraction "
                            f"({max_ineligible})",
                        )
                    derived = None
                    resample_fns: dict[str, Callable[[UnitTable], float | None]] | None = None
                    if template is not None:
                        cond_cfg = cfgs[cond.index]
                        # Once per recording step, on this condition's own resolved
                        # `cfg` — the same object a step in this condition receives —
                        # so one `aggregate` can compute a different metric under a
                        # different swept value (`reference.md` § Templates). This is
                        # the single unresampled call whose return is the reported
                        # `value`; `resample_fns` below is what recomputes it per
                        # bootstrap draw for the interval. Only *this* call is
                        # contained by a `try`: it is the metric's real definition
                        # for this table, so a failure here is a fault to disclose,
                        # not a degenerate draw — the per-draw calls inside
                        # `percentile_of_derived` are a different case, handled
                        # there (`stats.py`'s docstring says why).
                        try:
                            derived = coerce_scalars(
                                template.aggregate(
                                    _attributed(UnitTable(collapsed), unit_attributes),
                                    cond_cfg,
                                ),
                                where=aggregate_where,
                            )
                        except Exception as exc:
                            derived = None
                            code = getattr(exc, "code", None)
                            prefix = f"{code} " if code else ""
                            aggregate_c.warn(
                                "W-STATS-AGGREGATE-FAILED",
                                aggregate_where,
                                f"condition {cond.index} step {step_name!r}: "
                                f"{prefix}{type(exc).__name__}: {exc}",
                            )
                        if derived:
                            # A closure per key, not one shared call: `aggregate` may
                            # return several metrics, and `percentile_of_derived`
                            # resamples one key at a time (`reference.md` § How a
                            # metric becomes a number — resampling a derived metric
                            # means recomputing it, and this is `cli.py` supplying
                            # the callable `stats.py` stays pure by not importing).
                            # A nested `def`, not a lambda, so mypy has an explicit
                            # return type to check the `.get(key)` against, rather
                            # than trying (and failing) to infer one. Routed through
                            # `coerce_scalars` exactly like the call above — a bare
                            # `float(value)` on a structural return would `TypeError`
                            # straight into the failure this block exists to contain,
                            # rather than the honest `ContractError` a resampled
                            # draw can survive as "degenerate" in `stats.py`.
                            # `attrs` is passed in rather than closed over for the
                            # same reason `key`, `cfg` and `tmpl` are, and the
                            # closure re-attributes whatever table it is handed:
                            # `stats.py` rebuilds a table per bootstrap draw (and
                            # per side of a derived contrast) from rows it takes
                            # from `collapsed`, and it never sees the roster. So
                            # this is the one place that can put the attributes
                            # back — without it an attribute-reading `aggregate`
                            # computes its point estimate cleanly and then fails
                            # every single draw, reaching `run.yaml` with
                            # `resample_draws: 0` and no interval, and takes a
                            # derived contrast's *point estimate*
                            # (`paired_delta_of_derived`) down with it.
                            def _make_resample_fn(
                                key: str,
                                cfg: Config,
                                tmpl: BaseTemplate,
                                attrs: dict[str, dict[str, Any]],
                            ) -> Callable[[UnitTable], float | None]:
                                def resample_fn(units: UnitTable) -> float | None:
                                    value = coerce_scalars(
                                        tmpl.aggregate(_attributed(units, attrs), cfg),
                                        where=aggregate_where,
                                    ).get(key)
                                    return None if value is None else float(value)

                                return resample_fn

                            resample_fns = {
                                key: _make_resample_fn(key, cond_cfg, template, unit_attributes)
                                for key in derived
                            }
                    collapsed_by_key[(cond.index, step_name)] = collapsed
                    derived_by_key[(cond.index, step_name)] = derived
                    resample_fns_by_key[(cond.index, step_name)] = resample_fns
                    # The second door onto the same containment. `summarize_step`
                    # refuses a derived key that collides with a recorded column
                    # (`E-STEP-KEY-COLLISION`) — a real fault, and not weakened
                    # here — but the fault is in the same user-written
                    # `aggregate` the `try` above contains, one call later.
                    # Uncontained it exits before `run.yaml` is written,
                    # discarding every completed execution over one badly chosen
                    # name, while the sibling case (a structural return) merely
                    # warns. So it is disclosed the same way and costs the same
                    # thing: the whole `derived` mapping, exactly as a coercion
                    # failure does, never the recorded columns' own summaries —
                    # which is why the retry passes no `derived` rather than
                    # dropping the one colliding key.
                    try:
                        step_summary = summarize_step(
                            collapsed,
                            counts,
                            derived=derived,
                            seed=resample_seed_value,
                            resample=resample_fns,
                            draws=derived_metric_draws,
                            beside_n=cond_beside_n,
                            weights=weights,
                            clusters=clusters,
                        )
                    except ContractError as exc:
                        prefix = f"{exc.code} " if exc.code else ""
                        aggregate_c.warn(
                            "W-STATS-AGGREGATE-FAILED",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: "
                            f"{prefix}{type(exc).__name__}: {exc}",
                        )
                        # `weights` on the retry too: the collision costs the
                        # `derived` mapping and nothing else, so the recorded
                        # columns must come back with the same arithmetic they
                        # had on the first call. Silently downgrading them to
                        # unweighted numbers over a badly named derived key is
                        # this slice's own failure class, reached through the
                        # containment path. (A weight core cannot use cannot
                        # arrive here: `attrition` above gates the same mapping
                        # through `kish_effective_n`, outside any `try`.)
                        step_summary = summarize_step(
                            collapsed,
                            counts,
                            beside_n=cond_beside_n,
                            weights=weights,
                            clusters=clusters,
                        )
                        # What the parent block dropped, every stratum of it
                        # drops too. A level's table carries the same columns as
                        # the whole one, so the collision that raised above
                        # raises identically per level — uncontained, after the
                        # run has already spent every execution. Retrying each
                        # level with its own `try` would be worse than either:
                        # a level block carrying a derived metric its own parent
                        # does not have.
                        strata_derived: dict[str, Any] | None = None
                        strata_resample: (
                            dict[str, Callable[[UnitTable], float | None]] | None
                        ) = None
                    else:
                        strata_derived = derived
                        strata_resample = resample_fns
                    # `resample_draws: 0` (as opposed to `null`, meaning
                    # resampling was never attempted) is `summarize_step`'s
                    # signal that a callable was supplied and every single
                    # draw was degenerate — `nan`, `None`, or a raise, which
                    # `percentile_of_derived` treats alike. That is the same
                    # class of event `W-STATS-AGGREGATE-FAILED` already
                    # covers above (user code could not produce a number), so
                    # it reuses the identifier rather than minting a second
                    # one; the two cannot both fire for one metric, because a
                    # failure in the call above already left `derived` (and
                    # so this key) absent from `step_summary` entirely. The
                    # unit-identity fix makes this more likely, not less: a
                    # bootstrap draw duplicates units by construction, and a
                    # template whose `aggregate` assumes distinct ones will
                    # raise on every draw rather than some.
                    for metric_key, metric in step_summary.items():
                        used = metric.get("resample_draws")
                        if used == 0:
                            aggregate_c.warn(
                                "W-STATS-AGGREGATE-FAILED",
                                aggregate_where,
                                f"condition {cond.index} step {step_name!r} metric "
                                f"{metric_key!r}: every resample draw failed to "
                                "produce a value; reporting the point value with "
                                "no interval",
                            )
                        # A shrunken-but-nonzero count is a different event, so
                        # it gets a different identifier: `aggregate` did not
                        # fail — it produced numbers, just on fewer draws than
                        # were asked for, because some draws were degenerate.
                        # Below `min_honest_draws` the interval is `None` and
                        # this is the only notice of why; above it the interval
                        # exists but rests on less than it claims. One warning
                        # per metric, naming both counts, so a reader can weigh
                        # it without reading `resample_draws` out of `run.yaml`.
                        elif used is not None and used < derived_metric_draws:
                            floor = min_honest_draws()
                            aggregate_c.warn(
                                "W-STATS-RESAMPLE-THIN",
                                aggregate_where,
                                f"condition {cond.index} step {step_name!r} metric "
                                f"{metric_key!r}: {used} of {derived_metric_draws} "
                                "resample draws produced a value"
                                + (
                                    f"; below the {floor} an interval can honestly be "
                                    "read off, so none is reported"
                                    if used < floor
                                    else ""
                                ),
                            )
                    # One dispersion figure per repeat level, outer to inner
                    # (`reference.md` § A `batch` says *when*, not *what*), computed
                    # per RECORDED column — pooling `pred` and `truth` into one mean
                    # would report the blend as the dispersion of each. Only the
                    # columns `collapse_repeats` actually collapsed (and that
                    # survived `summarize_step`'s all-numeric check) get a figure;
                    # a derived (`aggregate`-computed) metric has no raw per-execution
                    # column to read a member's mean from without recomputing
                    # `aggregate` per member — the same heavier operation
                    # `repeat_spread` already declines for a nested `fold` — so it
                    # gets none (`docs/superpowers/spec-defects.md`). A length-one
                    # result is unwrapped to a bare mapping, matching
                    # `reference.md`'s single-level examples; a nested design's list
                    # of >1 entries is left as a list.
                    recorded_columns = {col for cols in collapsed.values() for col in cols}
                    for column in recorded_columns:
                        if column not in step_summary:
                            continue
                        spread = repeat_spread(
                            results,
                            step_name,
                            cond.index,
                            levels,
                            column,
                            # The units the metric beside it rests on, so the
                            # dispersion and the interval describe one
                            # population (`repeat_spread` says why).
                            keys=set(collapsed),
                        )
                        if spread:
                            step_summary[column]["repeat_spread"] = (
                                spread[0] if len(spread) == 1 else spread
                            )
                    aggregated[cond.index][step_name] = step_summary
                    # `reference.md` § Reporting strata: the same aggregation,
                    # repeated over the subsets each level of each named
                    # attribute picks out. Two attributes are two marginal
                    # splits, not their cross — the loop is over attributes,
                    # never nested — and no `Member` is built, because a
                    # stratum is a description rather than a comparison a
                    # reader acts on: joining the family would shrink α and
                    # silently widen every real comparison in the run.
                    # Built after the `repeat_spread` loop above deliberately,
                    # so a level block carries none: dispersion across repeats
                    # is the parent's figure, attached outside
                    # `summarize_step`, and a per-level one would need the
                    # column's per-member mean recomputed over the level's keys
                    # for a figure nothing documents.
                    report_by = (doc.get("statistics") or {}).get("report_by") or []
                    by_block: dict[str, dict[str, dict[str, Any]]] = {}
                    # `validate` refuses both a non-list `report_by` and a
                    # non-string entry, so neither guard below is reachable from
                    # a validated config. They stay because the cost of being
                    # wrong is asymmetric: a malformed value arriving here
                    # raises *after* the run has spent every one of its
                    # executions, the most expensive place in the program to
                    # fail.
                    for attribute in report_by if isinstance(report_by, list) else []:
                        if not isinstance(attribute, str):
                            continue
                        # Not `levels`: that name already holds this run's
                        # repeat levels, which `repeat_spread` above reads on
                        # every later pass of this loop.
                        levels_block: dict[str, dict[str, Any]] = {}
                        # `_condition_report_by_levels`, not `_report_by_levels`
                        # bare: under a group axis a level's key set must not
                        # reach past this condition's own arm into the other
                        # one — the same defect `_condition_counts` exists to
                        # fix for `attrition` above, one level in. Passing
                        # `roster` here directly (bypassing the arm narrowing)
                        # would let a level of `attribute` that happens to span
                        # both arms hand `attrition` units the other arm's
                        # executions never touched.
                        for level, (keys, level_roster) in _condition_report_by_levels(
                            roster, cond.index, arm_members_map, attribute
                        ).items():
                            # One key set decides BOTH the table and the counts.
                            # Taking the level's rows beside the condition's `n`
                            # is the S4b Critical's shape — a number reported
                            # against a denominator computed over other units.
                            level_collapsed = {
                                k: v for k, v in collapsed.items() if k in keys
                            }
                            level_counts = attrition(
                                results,
                                level_roster,
                                step_name,
                                cond.index,
                                fold_members=fold_members,
                                # Recomputed over the level's own units, which is
                                # what makes it carryable at all: `technical_n`
                                # below is withheld because it is a whole-roster
                                # figure that would have to be COPIED down, and
                                # Kish's size over this stratum is a different
                                # number this call computes from scratch — as is
                                # the number of clusters its own units fall in.
                                weights=weights,
                                clusters=clusters,
                            )
                            # Attrition happens during the run, so a level the
                            # roster-time `W-STATS-REPORTBY-THIN` counted as
                            # comfortable can complete on a handful — or on
                            # nothing at all. This check sits ahead of both
                            # gates below (the empty-level `continue` and the
                            # no-metric-produced check) on purpose: a level
                            # thinned to zero is the most disclosive case, and
                            # is exactly the one that gets no block. Warning
                            # only where a block is also emitted would mean the
                            # worst case never warns.
                            stratum_floor = (doc.get("limits") or {}).get("min_reported_n")
                            completed = level_counts.get("completed", 0)
                            if (
                                isinstance(stratum_floor, (int, float))
                                and not isinstance(stratum_floor, bool)
                                and completed < stratum_floor
                            ):
                                aggregate_c.warn(
                                    "W-STATS-STRATUM-THIN",
                                    "limits.min_reported_n",
                                    f"condition {cond.index}, step {step_name!r}: "
                                    f"level `{level}` of `{attribute}` completed "
                                    f"{completed} units, below limits.min_reported_n "
                                    f"({stratum_floor})",
                                )
                            # A level nothing completed gets no block at all —
                            # `W-STATS-STRATUM-THIN` above is what tells a
                            # reader the level exists and is empty, and a block
                            # whose metrics rest on no rows adds nothing to
                            # that. It also keeps `aggregate` from being called
                            # on an empty table, which raises for most
                            # templates and would fill the diagnostics with one
                            # failure per empty level.
                            if not level_collapsed:
                                continue
                            # A derived metric is NOT recomputed by
                            # `summarize_step` — it writes `value` straight
                            # through from the mapping and takes only the
                            # interval and `n.completed` from the table beside
                            # it. Handing a level the parent's `derived` would
                            # therefore publish the whole sample's point
                            # estimate against the level's own `n` and `ci95`:
                            # the S4b Critical's shape one layer in.
                            # `reference.md` § Reporting strata shows three
                            # different values (0.607 / 0.591 / 0.622) for this
                            # reason. So each level recomputes the metric over
                            # its own table, through the very closure the
                            # interval already resamples with — one definition
                            # of the metric, not two.
                            level_derived: dict[str, Any] | None = None
                            if strata_derived and strata_resample:
                                level_table = UnitTable(level_collapsed)
                                level_derived = {}
                                for key in strata_derived:
                                    compute = strata_resample.get(key)
                                    if compute is None:
                                        continue
                                    # User code, once per level. A raise here
                                    # costs this level's metric, never the run:
                                    # every execution is already spent, and the
                                    # whole-table call above is contained the
                                    # same way for the same reason. Also the
                                    # containment for a template returning a
                                    # non-numeric metric: `coerce_scalars`
                                    # accepts a `str`, so a `{"m": "high"}`
                                    # return reaches `compute` here — the same
                                    # resample closure — which floats
                                    # whatever `aggregate` returned, and
                                    # `float("high")` raises `ValueError`,
                                    # caught below. Narrowing this to a closed
                                    # set that drops `ValueError` reopens that
                                    # path; see the pin in tests/test_stats.py.
                                    try:
                                        level_value = compute(level_table)
                                    except Exception as exc:
                                        code = getattr(exc, "code", None)
                                        prefix = f"{code} " if code else ""
                                        aggregate_c.warn(
                                            "W-STATS-AGGREGATE-FAILED",
                                            aggregate_where,
                                            f"condition {cond.index} step "
                                            f"{step_name!r} metric {key!r}, "
                                            f"stratum {attribute}={level}: "
                                            f"{prefix}{type(exc).__name__}: {exc}",
                                        )
                                        continue
                                    # Omitted rather than carried over from the
                                    # parent: no value for this level is honest,
                                    # the parent's value here would not be.
                                    if level_value is not None:
                                        level_derived[key] = level_value
                            # The run's own resample seed, not one derived per
                            # level: a level resamples from its own key set,
                            # which is already what makes the draw its own.
                            #
                            # `weighted_beside`, not the parent's `beside_n`, and
                            # the difference is the whole rule: `technical_n` is
                            # `{min, max, median}` over the WHOLE roster, and a
                            # stratum's own units may have collapsed a different
                            # number of measurements each. Copying the parent's
                            # figure onto a subset would state a spread nobody
                            # computed over that subset, and `reference.md`
                            # § Reporting strata documents a level block as the
                            # aggregation repeated over the subset, not the
                            # parent's numbers re-shown — the same reason a level
                            # block carries no `repeat_spread`. `weighted_by`
                            # names the declaration rather than reporting a
                            # figure, and is as true of a stratum as of the whole
                            # roster, so withholding it would leave a block whose
                            # `n` carries `effective` with nothing saying why.
                            level_summary = summarize_step(
                                level_collapsed,
                                level_counts,
                                derived=level_derived or None,
                                seed=resample_seed_value,
                                resample=strata_resample,
                                draws=derived_metric_draws,
                                beside_n=weighted_beside,
                                # Same roster-wide mapping, filtered by the
                                # level's own table exactly as it is filtered by
                                # a ragged column's: a stratum's weighted mean
                                # and its Kish size are its own, which is the
                                # same reason `level_counts` is recomputed above
                                # rather than copied down, and the same reason the
                                # cluster mapping travels with it.
                                weights=weights,
                                clusters=clusters,
                            )
                            # At least one entry has to come from the level's own
                            # table. A block holding nothing but derived metrics
                            # over a table whose every column was non-numeric is
                            # the empty case again, wearing a value.
                            if set(level_summary) - set(level_derived or {}):
                                levels_block[level] = level_summary
                        if levels_block:
                            by_block[attribute] = levels_block
                    # `by` is reserved (`stats.RESERVED_METRIC_NAMES`). A derived
                    # metric of that name is refused in `summarize_step`; a
                    # RECORDED column of that name cannot be, because the retry
                    # that contains such a refusal passes the same `collapsed`
                    # and would re-raise uncontained, after the run has spent
                    # every execution. So it is handled here, and the column
                    # wins: it is a real measurement over the units, while the
                    # strata are a re-presentation of numbers already in the
                    # record.
                    #
                    # The disclosure follows the COLUMN, not the strata block:
                    # `_comparison_step_blocks` drops `by` from every
                    # comparison's metric set unconditionally, so a column of
                    # that name loses its `vs_baseline` delta and its seat in
                    # the correction family whether or not `report_by` was
                    # declared. Gating on `by_block` would leave the case where
                    # nothing was stratified — the case where the author has no
                    # other hint that the name is reserved — entirely silent.
                    # `aggregate_where`, not `statistics.report_by`: the fault
                    # is the recorded column, and there may be no `report_by`
                    # key in the file to point at.
                    if "by" in step_summary:
                        aggregate_c.warn(
                            "W-STATS-STRATUM-SHADOWED",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: 'by' is a "
                            "reserved metric name — it holds the key the reporting "
                            "strata are attached under — so the recorded column of "
                            "that name keeps its value but gets no contrast delta, "
                            "and no strata are reported for this step",
                        )
                    # Absent, not empty, the rule `vs_baseline` and `contrasts`
                    # already follow: a `by: {}` would claim a stratification
                    # was performed and found nothing.
                    elif by_block:
                        aggregated[cond.index][step_name]["by"] = by_block
            vs_baseline, vs_baseline_members = _compute_vs_baseline(
                doc=doc,
                conditions=conditions,
                roster=roster,
                aggregated=aggregated,
                collapsed_by_key=collapsed_by_key,
                derived_by_key=derived_by_key,
                resample_fns_by_key=resample_fns_by_key,
                seed=resample_seed_value,
                draws=derived_metric_draws,
                findings=aggregate_c,
            )
            contrasts_out, contrast_members = _compute_declared_contrasts(
                doc=doc,
                conditions=conditions,
                roster=roster,
                aggregated=aggregated,
                collapsed_by_key=collapsed_by_key,
                derived_by_key=derived_by_key,
                resample_fns_by_key=resample_fns_by_key,
                seed=resample_seed_value,
                draws=derived_metric_draws,
                findings=aggregate_c,
            )
            # Every interval a reader is shown is corrected against the family
            # it belongs to, and both record shapes are in the same family:
            # `reference.md` counts comparisons × metrics across the run, not
            # per block. Merged onto the entries in place, before
            # `assemble_run_yaml` reads them — the evidence each correction was
            # built from stays here, in the members, and never enters the
            # record. `corrected_fields` returns `{}` under `correction: none`,
            # which is why the field is *absent* there rather than null:
            # an explicit null would claim a correction was attempted.
            # Reassigned here, not where each `Member` is constructed: this is
            # the one point where the whole family — `vs_baseline` comparisons
            # then declared contrasts, each in config order — exists as a
            # single list, so it is the only place an index can be unique and
            # monotonic across all of it rather than restarted per comparison.
            comparison_members = [
                dataclasses.replace(m, declaration_index=i)
                for i, m in enumerate(vs_baseline_members + contrast_members)
            ]
            fields = corrected_fields(comparison_members, correction_method)
            for (where_id, step_name, metric_key), values in fields.items():
                entry = _entry_for(vs_baseline, contrasts_out, where_id, step_name, metric_key)
                if entry is None:
                    continue
                if values.pop("thin"):
                    aggregate_c.warn(
                        "W-STATS-CORRECTED-THIN",
                        "statistics.correction",
                        f"{where_id}, step {step_name!r} metric {metric_key!r}: "
                        f"{values['family_size']} comparisons imply a corrected level of "
                        f"{values['correction_level']:.5f}, which the resample's draws cannot "
                        "support — `ci95_corrected` is null rather than too narrow",
                    )
                entry.update(values)
        # Outside `if roster is not None:` on purpose, and for the same reason
        # `aggregate_c` is: a hypothesis naming a `summary` step's `Estimate`
        # is evaluable in a run with no `data.units` at all, where none of the
        # aggregate-phase code above runs. `vs_baseline`, `contrasts_out` and
        # `comparison_members` all carry their no-roster values there.
        #
        # The members, not the record, are what a corrected bound is rebuilt
        # from: `run.yaml` carries no draws, so an interval at *this* family's
        # level cannot be re-derived from what was already written. The
        # hypothesis family is corrected separately from the sweep's
        # (`reference.md` § Sweeps and repeats), which is why `evaluate` gets
        # the same members a second time rather than reading `ci95_corrected`
        # off the entries the pass above just merged into.
        #
        # `label_to_index` skips the unlabeled condition a sweepless plan
        # builds: a hypothesis names a condition by label, and `None` is not
        # one a config can write.
        hypothesis_verdicts = evaluate_hypotheses(
            doc.get("hypotheses") or [],
            label_to_index={c.label: c.index for c in conditions if c.label is not None},
            vs_baseline=vs_baseline,
            contrasts=contrasts_out,
            summary={
                r.execution.step_name: summary_values(r.returned)
                for r in results
                if r.execution.scope == "summary"
            },
            members=comparison_members,
            method=correction_method,
            parameters_hash=ph,
        )
        # Outside `if roster is not None:` on purpose: `aggregate_c` is created
        # above that block precisely so a `summary` step's `W-STEP-ESTIMATE-N`
        # still prints in a run with no roster at all, where none of the
        # aggregate-phase code above runs and adds nothing to it.
        if aggregate_c.findings:
            # Disclosed, not corrective: a metric that could not be computed
            # is not the same fact as a run that did not happen, so `status`
            # (set above from the executions themselves, all of which already
            # completed by the time `aggregate` runs) is deliberately left
            # alone — unlike `E-INPUT-CHANGED` below, which does set
            # `status = "failed"` for a different reason (the data a
            # completed run rested on is no longer what it read). This is
            # printed to stdout only: `run.yaml` has no diagnostics channel
            # to carry a finding that isn't a metric, an interval, or a
            # status.
            print(aggregate_c.render())
        changed_inputs = verify_manifest(input_dir, manifest)  # phase 8: re-verify
        if changed_inputs:
            status = "failed"
            drift_c = Collector()
            noun = "path" if len(changed_inputs) == 1 else "paths"
            drift_c.error(
                "E-INPUT-CHANGED",
                "data.input_dir",
                f"{len(changed_inputs)} {noun} changed since the manifest was built "
                f"at run start: {', '.join(changed_inputs)}",
            )
            print(drift_c.render())

        provenance: dict[str, Any] = {
            "git": {
                "repo_root": str(git.repo_root),
                "commit": git.commit,
                "branch": git.branch,
                "remote": git.remote,
                "code_dirty": git.code_dirty,
                "config_committed": git.config_committed,
            },
            "environment": {
                "manager": "uv",
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                "uv_lock": "environment/uv.lock" if lock_path is not None else None,
                "uv_lock_hash": lock_hash,
            },
            "apparatus": None,
            "input_manifest": "manifest/input.json",
            "input_manifest_hash": manifest_hash(manifest),
            "input_manifest_changed": changed_inputs,
            "publishable_version": importlib.metadata.version("publishable"),
            "plugin_versions": {},
            # A run over a roster whose identity is not pinned is a run whose `n`
            # means nothing later: `units` and `units_hash` are `None` together
            # exactly when there is no `data.units` declaration to pin.
            "units": (
                {"n": len(roster), "key": units_decl["key"]}
                if roster is not None and units_decl is not None
                else None
            ),
            "units_hash": units_hash(roster) if roster is not None else None,
            # "allocation.json" and its hash, when an arm assignment or a
            # holdout is declared — `None`/`None` together exactly when
            # `alloc_doc` was never written, the same pairing `units`/
            # `units_hash` already use above.
            "allocation": "allocation.json" if alloc_doc is not None else None,
            "allocation_hash": alloc_hash,
        }
        doc_out = assemble_run_yaml(  # phase 9: assemble and write
            run_id=run_dir.name,
            status=status,
            config=doc,
            code_hash=ch,
            parameters_hash=ph,
            provenance=provenance,
            results=results,
            repeats=repeats,
            aggregated=aggregated,
            condition_meta=condition_meta,
            vs_baseline=vs_baseline,
            contrasts=contrasts_out,
            hypotheses=hypothesis_verdicts,
        )
        (run_dir / "run.yaml").write_text(yaml.safe_dump(doc_out, sort_keys=False))
        # `with` block exit releases the lock.

    point_latest(output_dir, run_dir)
    print(f"run.yaml → {run_dir / 'run.yaml'}")
    return {"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)  # phase 10


def _dispatch(command: str, rest: list[str]) -> int:
    if command in OPERATION_COMMANDS:
        if len(rest) != 1 or rest[0].startswith("-"):
            print(f"`{command}` takes exactly one path and no flags", file=sys.stderr)
            return EXIT_INVOCATION
        path = Path(rest[0])
        return command_validate(path) if command == "validate" else command_run(path)
    if command == "new":
        if len(rest) != 1:
            return EXIT_INVOCATION
        scaffold_project(Path(rest[0]))
        return EXIT_OK
    if command in ("generate", "g", "init"):
        return _dispatch_generate(command, rest)
    print(f"unknown command `{command}`", file=sys.stderr)
    return EXIT_INVOCATION


def _dispatch_generate(command: str, rest: list[str]) -> int:
    opts: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(rest):
        if rest[i].startswith("--"):
            if i + 1 >= len(rest):
                return EXIT_INVOCATION
            opts[rest[i][2:]] = rest[i + 1]
            i += 2
        else:
            positional.append(rest[i])
            i += 1
    kind = "experiment" if command == "init" else (positional.pop(0) if positional else "")
    repo_root = find_repo_root(Path.cwd())
    if kind == "experiment":
        name = opts.get("name") or (positional[0] if positional else "")
        # Every option is checked before use: a missing one is a wrong invocation
        # (exit 2), never a KeyError traceback.
        missing = [f"--{o}" for o in ("template", "input-dir", "output-dir") if o not in opts]
        if not name or missing:
            print(
                "`generate experiment` needs a name plus " + ", ".join(missing or ["a name"]),
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        generate_experiment(
            repo_root=repo_root,
            name=name,
            template_name=opts["template"],
            input_dir=opts["input-dir"],
            output_dir=opts["output-dir"],
        )
        return EXIT_OK
    if kind == "step":
        if len(positional) != 2:
            return EXIT_INVOCATION
        generate_step(repo_root=repo_root, experiment=positional[0], step_name=positional[1])
        return EXIT_OK
    return EXIT_INVOCATION


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("usage: publishable <command> [args]", file=sys.stderr)
        return EXIT_INVOCATION
    command, rest = args[0], args[1:]
    try:
        return _dispatch(command, rest)
    except PublishableError as exc:
        print(f"  error   {exc.code:<20} {exc}", file=sys.stderr)
        return EXIT_WRONG
    except OSError as exc:
        # The single point where an environment failure becomes a diagnostic
        # instead of a bare traceback. Exit 1, not 5: the specification reserves
        # 5 for something outside the machine, and a local filesystem refusal
        # (permissions, a read-only mount, no space left) is not that.
        detail = exc.strerror or str(exc)
        io_c = Collector()
        io_c.error(
            "E-IO-FAILED",
            detail,
            "the filesystem refused this operation — check permissions, "
            "free space, and that the path exists",
        )
        print(io_c.render(), file=sys.stderr)
        return EXIT_WRONG

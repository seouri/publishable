"""Dispatch. Operation commands take paths and nothing else.

See docs/reference.md § Exit codes and diagnostics, § Generators, § Scaffolding.
"""

import dataclasses
import importlib
import importlib.metadata
import json
import os
import platform
import socket
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from publishable import apparatus
from publishable.artifacts import ResolverIO, allocation_hash, build_allocation_document
from publishable.base_experiment import BaseExperiment, load_experiment
from publishable.coercion import coerce_scalars
from publishable.config import Config
from publishable.contrasts import (
    crossed_group_axes,
    differing_axes,
    resolve_contrasts,
    units_matching,
)
from publishable.correction import Member, UnpairedEvidence, corrected_fields
from publishable.diagnostics import (
    EXIT_EXTERNAL,
    EXIT_FAILED,
    EXIT_INVOCATION,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
    Collector,
)
from publishable.errors import ContractError, PublishableError
from publishable.estimate import Estimate
from publishable.generators.experiment import generate_experiment, package_name
from publishable.generators.report import generate_report
from publishable.generators.step import generate_step
from publishable.generators.template import generate_template, is_usable_name
from publishable.hashes import code_hash_of, design_digest, hashed_files, parameters_hash
from publishable.hypotheses import evaluate as evaluate_hypotheses
from publishable.lineage import (
    UpstreamLedger,
    UpstreamResolver,
    attempt_counts,
    check_recorded_conditions,
    check_recorded_order,
    read_allocation,
    read_execution_ledger,
    read_sweep_plan,
)
from publishable.manifest import build_manifest, manifest_hash, verify_manifest
from publishable.plugin_scaffold import scaffold_plugin
from publishable.plugins import versions_for
from publishable.provenance import (
    GitInfo,
    find_repo_root,
    git_provenance,
    unignored_under_hashed_trees,
)
from publishable.replication import (
    Repeat,
    RepeatLevel,
    cross_levels,
    fold_members_for,
    order_seed_for,
    realize_order,
    resolve_repeats,
)
from publishable.run_identity import (
    IDENTITY_FILE,
    RunLock,
    allocate_run_dir,
    config_path_for,
    identity_document,
    point_latest,
    read_identity,
    read_repo_root,
    take_over_dead_lock,
)
from publishable.run_record import assemble_run_yaml, run_status, summary_values
from publishable.runner import (
    StopSignal,
    _arm_keys,
    _handed_keys,
    attrition,
    execute_plan,
    resolve_condition_cfg,
    resolve_wide_cfg,
    step_dir_for,
)
from publishable.scaffold import scaffold_project
from publishable.scope import Execution, build_plan
from publishable.secrets import credential_values, load_env, redact
from publishable.stats import (
    UnitTable,
    _is_numeric,
    cohens_ds,
    cohens_dz,
    collapse_repeats,
    kish_effective_n,
    mean_of,
    min_honest_draws,
    paired_delta_of_derived,
    paired_keys,
    paired_percentile_of_derived,
    paired_t_over_units,
    paired_t_over_units_clustered,
    permutation_over_contrast,
    repeat_spread,
    repeats_disagreeing,
    resample_seed,
    summarize_step,
    unit_table_from_rows,
    unpaired_keys,
    unpaired_percentile_of_sides,
    weighted_cohens_dz,
    weighted_mean_of,
    weighted_paired_t_over_units,
    welch_t_over_units,
    welch_t_over_units_clustered,
)
from publishable.strata import levels_for
from publishable.sweep import (
    condition_dir_name,
    expand,
    sample_seed_for,
    selector_paths,
    sweep_document,
    wide_swept_paths,
)
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template
from publishable.units import (
    RESOLVER_GROUP,
    ArmPlan,
    HoldoutPlan,
    Unit,
    UnitList,
    arm_members,
    assignment_for,
    cells_of,
    cluster_count_of,
    clusters_of,
    fold_basis,
    holdout_seed_for,
    holdout_within_cells,
    index_names,
    null_test_level,
    partition_units,  # noqa: F401 — see `partition_within_cells` below
    partition_within_cells,
    populated_cells,
    resolve_units,
    stratum_names,
    thinnest_cell,
    units_hash,
)
from publishable.uv_support import environment_manager, uv_lock_info
from publishable.validate import load_document, validate_config

if TYPE_CHECKING:
    from publishable.contrasts import Comparison
    from publishable.runner import ExecutionResult
    from publishable.sweep import Condition

OPERATION_COMMANDS = {
    "validate",
    "dry-run",
    "run",
    "draft",
    "resume",
    "reproduce",
    "freeze",
    "report",
}

# The specified-but-unbuilt surface, in one place. Every name here is a command
# `docs/reference.md` § CLI reference describes and this build does not execute;
# the value is the section of that document which specifies it. A name is removed
# from this mapping by the slice that builds it, and `tests/test_cli.py`'s
# `test_reference_cli_tables_match_what_the_cli_does` binds the two directions:
# the rows marked `NOT BUILT` there are exactly the keys here, and every unmarked
# row is a command this module really dispatches. Cited by section, never by line
# number — `docs/reference.md` moves under every edit above the citation.
# The commands `docs/reference.md` § Operation commands gives the argument
# *(none)*. They walk up from `Path.cwd()` — the exception `E-GIT-NO-REPO`'s own
# § Errors row already documents for the creation commands, reused rather than
# restated (Ruling FF) — and they take no flag either, `design-principles.md`
# § Everything is in the file admitting none anywhere.
ZERO_ARGUMENT_COMMANDS = {"docs", "list-templates"}

# EMPTY as of H9d, and deliberately kept rather than deleted: `demo`, `docs` and
# `list-templates` were its last three keys and all three dispatch now. The
# distinction it draws — *specified and unbuilt* against *unknown command* — is
# argued at length in `docs/reference.md` § Creation commands, and a future
# command specified before it is built would otherwise have to re-argue it.
# `_report_not_built` therefore has no reachable dispatch today; the companion
# `test_the_not_built_machinery_is_retained_with_no_row_marked` asserts BOTH that
# this mapping is empty and that the helper still formats the documented
# diagnostic, so the formatting half stays killable while the dispatch half has
# no input.
NOT_BUILT_COMMANDS: dict[str, str] = {}

# The same, for `generate`'s kinds: `docs/reference.md` § Generators names
# four and this build materializes all four (H8c task 15 built `report`,
# the last of them).
NOT_BUILT_GENERATORS: dict[str, str] = {}


def _report_not_built(what: str, section: str) -> int:
    """Print the diagnostic a specified-but-unbuilt name gets, and exit 2.

    Deliberately not `unknown command`: the two cases are different news. One says
    you typed something that was never specified; this one says the specification
    holds it and this build does not, which is a roadmap entry rather than a typo.
    Both exit 2 — the invocation is wrong either way, and a new exit code would be
    a change to `docs/reference.md` § Exit codes and diagnostics.
    """
    print(
        f"`publishable {what}` is specified but not built in this version — "
        f"see docs/reference.md § {section}",
        file=sys.stderr,
    )
    return EXIT_INVOCATION


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


def _baseline_comparisons(doc: dict[str, Any], conditions: "list[Condition]") -> "list[Comparison]":
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


def _flatten_parameters(node: Any, prefix: str = "") -> dict[str, Any]:
    """Mirrors `validate._flatten` for this one caller, rather than reaching
    across a module boundary for a name private to that module."""
    flat: dict[str, Any] = {}
    for key, value in (node or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_parameters(value, path))
        else:
            flat[path] = value
    return flat


def declared_credential_names(
    doc: dict[str, Any], template: Any, conditions: "list[Condition]"
) -> list[str]:
    """Every environment variable this config's declarations name.

    The same two collectors `validate` checks — the template's `required_env` and
    the `requires_env` of every value a resolved condition selects — read here for
    their *values* rather than for their presence. Deliberately the same set: core
    redacts exactly what it was told to look for, which is what makes the answer a
    fact rather than a guess.

    Takes the already-expanded `conditions` rather than expanding again, so the
    set core redacts is derived from the same condition list the run executes.

    A `None` template yields the empty list, which is the honest answer for a name
    that resolves to nothing — but it is also indistinguishable from a template
    declaring no credentials, so the caller's job is to pass a template that was
    resolved WITH `repo_root`.
    """
    raw_required = getattr(template, "required_env", None)
    # Same guard as `validate._check_required_env` and
    # `validate.declared_credential_names_for`: nothing reports a
    # `required_env` that is not a list, so it is ignored here alike rather
    # than iterated as characters.
    names: list[str] = list(raw_required) if isinstance(raw_required, list) else []
    spec = getattr(template, "parameter_spec", None) or {}
    declared = _flatten_parameters(doc.get("parameters"))
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path not in condition.selectors:
                resolved[path] = value
        for path, param in spec.items():
            mapping = getattr(param, "requires_env", None)
            if not mapping:
                continue
            value = resolved.get(path, param.default)
            try:
                names.extend(mapping.get(value) or [])
            except TypeError:
                continue
    return names


def _resolved_group_axes(
    units_decl: dict[str, Any] | None,
    sweep_block: dict[str, Any],
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None = None,
) -> dict[str, ArmPlan]:
    """Every `sweep.groups` axis **realized** — one `units.ArmPlan` per axis,
    `units.arm_members`'s own input shape and `artifacts.build_allocation_document`'s.

    This function resolves the *declaration* (which axes exist, and which
    levels each declares) and hands each axis to `units.assignment_for`,
    which is the single producer of a plan and which owns the resolution of
    `assign.<axis>.from` against its default — the declared `from` if it is a
    non-empty string, else the axis name itself. That resolution used to live
    here as well as there; two resolutions of one declaration is a smaller
    instance of the defect this slice closes, so there is now exactly one.

    **Axes are drawn in declaration order, and that order is a contract this
    function keeps rather than a property of how its dict happens to be
    built.** `reference.md` § Expansion modes: "axes resolve in declaration
    order, and `stratify_by` may name a group axis declared before it". Each
    axis is handed the plans of the axes already drawn, so an axis stratifying
    on an earlier one is balanced on that axis's **realized** membership —
    there is no column for a drawn axis to leave. What makes the ordering
    load-bearing rather than incidental is that the same argument is what
    fails: a refactor that reordered this loop (or built the result unordered
    and drew from it) would hand a stratifying axis a snapshot its stratum is
    not in, and `units.assignment_for` raises there rather than drawing a
    different allocation quietly. `validate` refuses the declaration that
    reaches that raise, as `E-DATA-ASSIGN-STRATIFY-FORWARD`.

    **One shape can still reach the raise through a clean `validate`**, and it
    is the same disagreement this function's `levels` skip already has with
    `sweep.selector_paths` (below): `validate` reads the axis order from
    `selector_paths`, which admits an axis whose `levels` this function skips,
    so an earlier axis this function did not realize is an earlier axis
    `validate` saw. Deliberately surfaced as a raise — `arm_members`'s own
    `KeyError` is the precedent, a caller bug to see rather than one to absorb
    by drawing an allocation nothing balanced.

    Realized **once per run**, and the result is what both `units.arm_members`
    and `artifacts.build_allocation_document` are handed — neither recomputes
    it. Under `by_attribute` a recomputation would agree; under a draw a second
    call is a second allocation, so the plan is computed once and passed.

    `roster` and `digest` are required rather than defaulted, `clusters` is
    not: `digest` is unread on the `by_attribute` path today and task 8
    threads it into `units.assign_seed_for`, so a defaulted one would become
    a draw silently seeded from the empty string with every test still green
    — exactly the class of silent-wrong-under-a-draw this seam exists to
    close, sitting in the signature the draw will arrive through.

    Returns `{}` when `roster is None`: an allocation is a partition of a
    resolved roster, and there is nothing to partition without one. That is
    the same gate `command_run` already applied before calling
    `units.arm_members`, kept here rather than moved, so a design with no
    `data.units` block still reaches `execute_plan` with no arm narrowing at
    all rather than raising.

    Skips an axis whose `levels` does not resolve to a non-empty list of
    strings, matching `_check_assign`'s own skip for that shape — `sweep.groups`'s
    own shape check is `validate`'s to report, or not report at all in this
    build, and inventing a second notion of "resolved" here would not change
    that. A malformed `assign` block (absent, non-mapping, or naming no
    method) reaches `assignment_for` as-is and takes its `by_attribute` path,
    the same default `_check_assign` falls back to before its own checks on
    the block would have already reported the malformation as a finding. A
    block naming any other method raises `NotImplementedError` from there —
    `assignment_for` allows `by_attribute` and refuses the rest rather than
    denying a list of drawing methods — which for `random` and `blocked` is
    the explicit hole tasks 8 and 10 filled — both now draw here, and the
    raise is left for a method no branch claims. Unreachable through
    `command_run`: `validate` refuses an out-of-enum method as
    `E-DATA-ASSIGN-METHOD`, and `blocked` beside a declared `cluster_by` —
    the one combination inside the enum that still raises — as
    `E-DATA-ASSIGN-BLOCKED-CLUSTER`, and returns first.

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

    Reachable from `command_run` now that task 17 retired
    `E-SWEEP-GROUPS-UNSUPPORTED`: `tests/test_cli.py`'s
    `test_a_group_axis_actually_narrows_end_to_end` and
    `test_allocation_json_is_written_with_exact_arm_keys_when_declared` reach
    this line for real, through a passing `command_run`, the same way
    `wide_swept_paths` (in `sweep.py`) is now reachable for the selector-path
    subtraction it depends on.
    """
    if roster is None:
        return {}
    assign = (units_decl or {}).get("assign")
    blocks = assign if isinstance(assign, dict) else {}
    axes: dict[str, ArmPlan] = {}
    for entry in sweep_block.get("groups") or []:
        if not isinstance(entry, dict):
            continue
        axis = entry.get("by")
        if not isinstance(axis, str) or not axis:
            continue
        levels = entry.get("levels")
        if not (isinstance(levels, list) and levels and all(isinstance(v, str) for v in levels)):
            continue
        block = blocks.get(axis)
        # The whole block, not a `from` this function resolved: `assignment_for`
        # dispatches on `method` and resolves `from` on the branch where `from`
        # means anything at all, which is where the gate this call site used to
        # apply now lives. `from` "means nothing" under `random`/`blocked` for
        # the reason `units._assign_constant_columns` states, and neither method
        # reads a column there — it raises.
        # `dict(axes)` — the axes drawn SO FAR, and the reason this loop's order
        # is a contract rather than an accident of construction. An axis whose
        # `stratify_by` names an earlier one is balanced on that axis's realized
        # membership, which exists only in its plan, so reordering the loop does
        # not silently draw a different allocation: the later axis is simply
        # absent from this snapshot and `assignment_for` raises. A copy rather
        # than the live dict, so the snapshot is what the axis was drawn against
        # and cannot be read as "every axis, eventually".
        axes[axis] = assignment_for(
            roster,
            axis,
            block if isinstance(block, dict) else None,
            levels,
            digest,
            clusters,
            dict(axes),
        )
    return axes


def _resolved_holdout(
    units_decl: dict[str, Any] | None,
    roster: "UnitList | None",
    digest: str,
    clusters: dict[str, str] | None,
    cells: "dict[tuple[tuple[str, str], ...], frozenset[str]] | None" = None,
) -> "HoldoutPlan | None":
    """`data.units.holdout`, realized **once per run** — or `None` when the
    design declares none.

    The one object handed to the runner's narrowing, to the denominators, and
    to `build_allocation_document`. `build_allocation_document`'s own docstring
    makes the argument for arms and it transfers verbatim: it used to be handed
    the roster and re-derive the partition, and *"under a draw that second
    derivation is a second draw, and 'provably identical' is not something two
    calls can be made to promise — only not calling twice can."* A `method:
    random` holdout is a draw, so the partition the run executes, the
    denominators it reports against, and the membership `allocation.json`
    claims are the same object rather than three answers that happen to agree.

    `None` for four shapes, and they are one shape: an absent `data.units`, an
    absent `holdout`, a `holdout: null`, and a `holdout: {}`. The last is
    `_check_holdout`'s own gate — an empty block declares nothing and
    partitions nothing — so the two readings of "is a holdout declared" agree
    rather than one drawing an unmethodded split the other validated as absent.
    `None` for a `roster` of `None` too: there is nothing to partition. That
    argument is defensive rather than reachable — `resolve_units` never returns
    `None`, so a `None` here means no `data.units` at all, which is a config
    that cannot carry a `holdout` to declare. It costs one line and keeps the
    helper total over its own signature.

    `clusters` is `cli.command_run`'s single cluster map, the same one the fold
    partition and the arm draw are handed — not re-derived here, `clusters_of`
    being the single authority.

    `cells` is the design's realized decomposition, and the split is drawn
    **inside each cell** through `units.holdout_within_cells` — the same single
    producer `validate._holdout_test_roster` calls, so the partition `validate`
    bounds `limits.min_clusters` against and the partition the run executes are
    one answer rather than two. `None` is a design with no group axis and takes
    that function's own one-cell reduction, which is the byte-identical
    whole-roster draw.

    **The decomposition arrives as `cells`, not as `group_axes`.**
    `_prepare_run` already holds `units.cells_of`'s answer in one local, and
    calling `cells_of` a second time here would be a second derivation of the
    decomposition — the thing that local exists to prevent, and the same
    argument `build_allocation_document`'s docstring makes for being handed the
    plans rather than the roster. The fold partition beside it is handed the
    same object.
    """
    if roster is None:
        return None
    block = (units_decl or {}).get("holdout")
    if not isinstance(block, dict) or not block:
        return None
    # `holdout_seed_for` over the WHOLE roster, computed once and handed to
    # every cell's draw — see `units.holdout_within_cells` for why the seed is
    # one per run rather than one per cell, and why a pinned integer survives a
    # roster that reorders.
    return holdout_within_cells(
        roster,
        block,
        seed=holdout_seed_for(block, digest, roster),
        cells=cells,
        clusters=clusters,
    )


def _evaluation_roster(
    roster: "UnitList | None", holdout: "HoldoutPlan | None"
) -> "UnitList | None":
    """The units every denominator counts against — the holdout's **test**
    partition when one is declared, and the same roster object otherwise.

    `reference.md` § A fixed holdout split: "`resolved` is the test partition
    — a 20 % holdout over 240 units reports `resolved: 48`, and the interval is
    over those 48. That's the honest denominator: the training units produced
    no result to generalize from."

    **Without this, every training unit lands in `failed`.** `runner.attrition`
    computes `handed = keys` over whatever roster it is given, and a training
    unit is handed out, records nothing, and is neither completed nor skipped —
    so a 0.2 holdout over 240 would report 192 failures and trip
    `max_failed_fraction` on a run in which nothing failed.

    **The same object, not a copy, when no holdout is declared.** There is
    nothing to copy: `roster` is unchanged, so returning it as-is is the
    correct answer, not a guard against a downstream identity check. (The
    identity `_cond_beside_n` tests is between `_cond_roster`'s return and the
    roster `_condition_beside_n` was given — both derived from that same
    single argument — so which object this function returns never reaches
    that decision.)

    Roster order is preserved: it is part of the roster's identity, and
    `_report_by_levels` walks it to build each level's table.

    **What this deliberately does NOT narrow**, and the list is the point
    rather than an omission:

    - `provenance.units.n` and `provenance.units_hash` stay whole-roster. They
      are the roster's identity, not a metric's denominator — which is what
      makes `240` there and `48` in a metric's `n` two true numbers rather than
      a contradiction.
    - The key-indexed maps `command_run` builds over the roster — the
      `weight_by` weights, `unit_attributes`, and `resample_strata` — are
      consumed BY KEY over units that completed, so a surplus training key is
      never looked up. Narrowing them would be a third answer to which roster
      is which for no observable difference.
    - `runner._counts`' Kish size and cluster count are computed over the
      COMPLETED units already (its own docstring: "a df is over the units the
      interval was computed from"), so they are holdout-safe by construction
      and need nothing here.
    """
    if roster is None or holdout is None:
        return roster
    test = set(holdout.test)
    return UnitList([u for u in roster if u.key in test])


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


def _report_by_levels(roster: "UnitList", attribute: str) -> dict[str, tuple[set[str], "UnitList"]]:
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
    lives inside `command_run`'s per-condition, per-step loop, and no
    end-to-end test in this build combines a group axis with a declared
    `statistics.report_by` — extraction is what makes the narrowing testable
    directly rather than only through such a run.
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
    repeat-dispersion figure for a value that cannot vary across repeats. Here
    an attribute reaches `aggregate` and nothing else.

    An attribute is carried through **unchanged**: it comes from the roster
    rather than from an execution, so unlike a recorded numeric column it has
    no repeats to average over. A recorded column of the same name is already
    refused upstream — `io.record` raises `ContractError` ·
    `E-STEP-KEY-COLLISION` — so this merge arbitrates no precedence; it merely
    must not be the thing that papers over that collision, which is why the
    attributes are applied last rather than first.

    `unit` is restored after the merge because the unit key column must survive:
    a bootstrap draw duplicates units on purpose, and `percentile_of_derived`
    keeps the real keys inside every draw precisely so a template reading `unit`
    sees the roster it was drawn from.

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


def _make_null_fn(
    key: str,
    cfg: Config,
    tmpl: BaseTemplate,
    attrs: dict[str, dict[str, Any]],
    shuffle: str,
    aggregate_where: str,
) -> "Callable[[UnitTable, dict[str, str]], float | None]":
    """The resample closure's counterpart (`_make_resample_fn`), taking the
    drawn labels as an argument — a SECOND closure family rather than a
    keyword added to that one (§ Corrections, correction 1).

    `_make_resample_fn`'s closure calls `_attributed(units, attrs)` on every
    draw, re-applying each unit's declared attributes from the roster — correct
    for a bootstrap, which never changes what a unit's attributes ARE, and
    fatal for a permutation: `_attributed` merges the roster's values OVER the
    row, so a relabelling written into the table would be erased before
    `aggregate` ever sees it, and every draw would reproduce the observed
    statistic — a `p_value` of 1.0 for every derived metric in every run. So
    the drawn label is merged over the roster's attributes here instead, which
    is the one place it cannot be overwritten.

    Module-level, not a nested `def` closed over `command_run`'s locals — the
    earlier shape, moved out so a test can build and call this closure
    directly as well as through a real `run` now that `E-STATS-NULLTEST-
    UNSUPPORTED` is retired (H4d tasks 25+26). `aggregate_where` therefore
    arrives as a parameter rather than a captured name.
    """

    def null_fn(units: UnitTable, labels: dict[str, str]) -> float | None:
        merged = {
            unit_key: {**attributes, shuffle: labels[unit_key]}
            for unit_key, attributes in attrs.items()
            if unit_key in labels
        }
        value = coerce_scalars(
            tmpl.aggregate(_attributed(units, merged), cfg), where=aggregate_where
        ).get(key)
        return None if value is None else float(value)

    return null_fn


def _comparison_step_blocks(
    comp: "Comparison",
    *,
    roster: "UnitList",
    aggregated: dict[int, dict[str, dict[str, Any]]],
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, Any]]],
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
    resample_columns: bool,
    weights: dict[str, Any] | None = None,
    strata: dict[str, str] | None = None,
    weighted_by: str | None = None,
    clusters: dict[str, str] | None = None,
    null_test: dict[str, Any] | None = None,
    resample_echo: dict[str, Any] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[Member]]:
    """One comparison's delta, per recording step and per metric already in
    `aggregated` — the computation `vs_baseline` and `results.contrasts` both
    rest on, factored out so the two record shapes don't duplicate it.

    `weights` is `command_run`'s roster-wide `{unit key: weight}` mapping, or
    `None` when `data.units.weight_by` is undeclared; `strata` its resolved
    `statistics.resample.stratify_by` mapping; and `clusters` its roster-wide
    `{unit key: cluster label}` mapping, or `None` when `data.units.cluster_by` is
    undeclared. All three are defaulted rather than required: the direct call
    sites in the test suite would otherwise take an edit with no behavioural
    content, and "no weight/cluster declared" and "this caller has not been taught
    about weights/clusters" are the same fact. `strata` reaches both percentile
    branches, because a declaration honoured for a derived metric and dropped for
    a recorded column would be the asymmetry § Weighted samples' pairing of
    `weight_by` with `resample.stratify_by` exists to rule out. `weights` and
    `clusters` never arrive together — refused above as
    `E-DATA-WEIGHT-CLUSTER-CONTRAST` — so every branch below is a choice among
    mutually exclusive declarations rather than a combination to compose.

    `null_test`, when given, is `_resolved_null_test`'s dict with `level`
    filled in by `command_run` (it needs the roster, which that function does
    not have). **Only the unpaired arm ever writes `p_value`/`null_test`**,
    gated on `not is_paired` and on the resolved `shuffle` naming a group axis
    these two conditions actually differ on: a paired comparison's two
    conditions share their units, so its null is a per-unit sign flip rather
    than a relabelling and `shuffle` cannot express it — § What isn't a repeat
    says so in those words. Both keys are **absent, not null**, everywhere
    else, the same shape `n_paired` follows: a fact about whether this
    comparison joins that p-value home, not about whether the permutation
    happened to run. Where it does write, `p_value` is written whether or not
    `interval` came back — the two per-side vectors it reads are built above
    regardless of whether the *t* or Welch construction resolved one — and
    `p_value_corrected` is never written here, because the correction pass
    merges it in afterward from the family it belongs to, not from this one
    comparison's own view of itself.

    `resample_echo`, when given, is `_resolved_resample`'s `{method, n,
    stratify_by}` dict, the same one `cli` merges into every `aggregated`
    metric block as `weighted_beside["resample"]`. It is written onto every
    metric entry here too — every arm, derived and column, paired and
    unpaired alike — because the fact it discloses ("this run's resample was
    declared, at this `n`") is true of the whole run and not of which
    construction a particular metric happened to route through
    (`spec-defects.md`'s "the contrast path discloses nothing about its
    resample", Finding 3). Absent, not null, when no `resample` is declared —
    the same rule the `aggregated` echo already follows.

    Under a declared weight, a recorded column's `delta` is the weighted mean of
    the differences and `cohens_d` is `weighted_cohens_dz(diffs, col_weights)` —
    `col_weights` being the intersection's own weights, in `col_keys` order, so
    the point estimate and the effect size can't disagree about which units were
    weighted. A resampled column's interval additionally gets `method =
    "weighted_paired_percentile_over_units"` in place of the unweighted spelling.
    The entry also carries `weighted_by` (the attribute name) and
    `n_paired_effective` (Kish's size over that same intersection) — § Contrasts
    requires all four to move together. A derived metric is never weighted by
    core (the weight column reaches `aggregate` as a unit attribute instead, so a
    template weights its own metric if it needs to), which is why its `method`
    and `cohens_d: None` stay the unweighted spellings under a declared weight —
    but `weighted_by` and `n_paired_effective` still travel beside it, the same
    arrangement a weighted condition gets from `summarize_step`.

    On the paired arm (`is_paired`), a recorded column takes
    `paired_t_over_units` over the per-unit differences —
    `weighted_paired_t_over_units` under a declared weight, or
    `paired_t_over_units_clustered` under a declared cluster (the two never
    coexist) — unless `resample_columns` is set **and the pairing has at least
    two units**, when it instead takes `paired_percentile_of_derived` over its
    own column mean (weighted inside the closure when a weight is declared, or
    drawing whole clusters under a declared one), the same construction a
    derived metric uses. A derived
    metric — one
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
    paired constructions read `n_paired` off `stats.paired_keys` — the
    intersection of the two conditions' completed units, narrowed by `within`
    when the comparison declares one — and record `correction: null` as their
    default, which is what the record says under `correction: none`, since
    nothing is merged over it then. The unpaired arm reads `stats.unpaired_keys`
    instead, has no intersection to report, and records `n_of`/`n_against` in
    `n_paired`'s place.

    The second return value is the correction family's raw material: one
    `Member` per metric entry, carrying the evidence its interval was read from
    — the draw pool for a derived metric, the per-unit differences for a
    recorded column **unless a `resample` is declared, when a column carries
    the draw pool too** (`resample_columns`, below). It travels beside the
    block rather than inside it because
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
    `False`/`[]`, when only one axis differs.

    `is_paired` — `not contrasts.crossed_group_axes(of, against)` — decides which
    arm each metric takes: the intersection and `n_paired` on one side, each
    side's own completed units (narrowed by `within`) and `n_of`/`n_against` on
    the other, where the point estimate is the difference of the two side means
    rather than a mean of differences. `E-DATA-ALLOCATION-CONTRAST` is retired:
    an unpaired comparison validates clean (except a weighted one, still refused
    as `E-DATA-WEIGHT-ALLOCATION-CONTRAST`) and the unpaired arm is reachable
    through a real `run`, not only by direct call.

    `paired` is derived per comparison, from `contrasts.crossed_group_axes` — the
    same expression `validate` refuses a weighted unpaired comparison on, so the
    two cannot disagree about which comparisons share their units. Two conditions
    differing on any declared `sweep.groups` axis hold disjoint sets of units
    whatever `allocation` itself is declared as, and an unpaired entry records
    `n_of`/`n_against` in place of an `n_paired` its intersection cannot supply.
    """
    # `E-DATA-WEIGHT-CLUSTER-CONTRAST` refuses this combination at `validate`, and
    # `cli` always validates before running — so both being set is core's own
    # bookkeeping error, not a config. Raised rather than resolved by precedence:
    # preferring one would publish a `method` naming a construction the other
    # declaration contradicts, and no reader of `run.yaml` could tell. `ValueError`
    # for the reason `Member.__post_init__` gives — nothing here came from outside
    # core.
    if weights is not None and clusters is not None:
        raise ValueError(
            "a weighted clustered comparison has no construction in this build; "
            "E-DATA-WEIGHT-CLUSTER-CONTRAST refuses the combination at validate"
        )
    differs_on = differing_axes(conditions_by_index[comp.of], conditions_by_index[comp.against])
    confounded = len(differs_on) > 1
    # Whether the two sides share their units, from the SAME expression `validate`
    # refuses on — `contrasts.crossed_group_axes`, whose docstring argues why it is
    # one function with two callers. Read once at function scope: a per-metric
    # re-derivation is how two entries in one block come to disagree about a fact
    # about their two conditions.
    group_axes = crossed_group_axes(conditions_by_index[comp.of], conditions_by_index[comp.against])
    is_paired = not group_axes
    # `E-DATA-WEIGHT-ALLOCATION-CONTRAST` refuses this combination at `validate`,
    # and `cli` always validates before running — so both being set is core's own
    # bookkeeping error, not a config. Raised rather than resolved by dropping the
    # weight: an unweighted cross-arm delta published beside a `weighted_by` marker
    # is a declaration accepted whose effect is not delivered, and no reader of
    # `run.yaml` could tell. `ValueError` for the reason the guard below gives.
    if weights is not None and not is_paired:
        raise ValueError(
            "a weighted unpaired comparison has no construction in this build; "
            "E-DATA-WEIGHT-ALLOCATION-CONTRAST refuses the combination at validate"
        )
    allowed = units_matching(roster, comp.within)
    of_steps = {k[1] for k in collapsed_by_key if k[0] == comp.of}
    against_steps = {k[1] for k in collapsed_by_key if k[0] == comp.against}
    block: dict[str, dict[str, Any]] = {}
    members: list[Member] = []
    for step_name in sorted(of_steps & against_steps):
        of_collapsed = collapsed_by_key[(comp.of, step_name)]
        against_collapsed = collapsed_by_key[(comp.against, step_name)]
        base_keys = paired_keys(of_collapsed, against_collapsed, allowed)
        of_side_keys, against_side_keys = unpaired_keys(of_collapsed, against_collapsed, allowed)
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
            # Bound here, before either branch, so the name is always defined —
            # the derived branch never assigns it, and relying on
            # `corrected_from_pool`'s short-circuit below to keep it out of reach
            # there would make an unrelated refactor of that expression silently
            # load-bearing.
            col_weights: list[Any] | None = None
            col_clusters: list[str] | None = None
            of_col: list[str] = of_side_keys
            against_col: list[str] = against_side_keys
            # Bound here too, beside `col_weights`/`col_clusters` above and for the
            # same reason: only the unpaired arm below assigns them, and relying on
            # `corrected_from_pool or is_paired`'s short-circuit to keep them out of
            # reach at the `Member` call would make an unrelated refactor of that
            # expression silently load-bearing.
            of_values: list[float] | None = None
            against_values: list[float] | None = None
            of_clusters: dict[str, str] | None = None
            against_clusters: dict[str, str] | None = None
            if is_derived:
                compute_of = (resample_fns_by_key.get((comp.of, step_name)) or {}).get(metric_key)
                compute_against = (resample_fns_by_key.get((comp.against, step_name)) or {}).get(
                    metric_key
                )
                interval = None
                delta = None
                # Reset per metric, beside the other two: assigned only inside
                # `len(base_keys) >= 2` below, so a one-unit intersection would
                # leave the name unbound where the member is built (a `NameError`
                # on the first pass) or — worse, at function scope — hand a later
                # metric the *previous* metric's draw pool, which nothing
                # downstream could detect.
                resampled = None
                # **One suppression condition remains: AN UNPAIRED COMPARISON.**
                # `unpaired_percentile_of_sides` serves a recorded column's own
                # closure; a recomputed metric would need `aggregate` evaluated on
                # each side's independently drawn table, which is a construction this
                # build does not have. Reached, this branch would compute
                # `paired_delta_of_derived` over an intersection that is empty by
                # construction and publish whatever `paired_percentile_of_derived`
                # returned over it.
                #
                # A declared cluster no longer suppresses this branch (H4d task
                # 15b, `E-DATA-CLUSTER-DERIVED` retired): `paired_percentile_of_derived`
                # already draws whole clusters when handed one — the same
                # construction the recorded-column arm below uses — so a derived
                # paired contrast under `cluster_by` computes rather than
                # publishing `null`.
                #
                # **The unpaired ground reads `is_paired`, never `not base_keys`.**
                # An empty intersection is a PROXY: it is also empty when two
                # genuinely paired conditions share no completed units, which is a
                # defect to report rather than a design to honour —
                # `test_a_derived_contrast_over_an_empty_stratum_reports_no_delta` is
                # that case, and it records `n_paired: 0` for exactly that reason.
                if compute_of is not None and compute_against is not None and is_paired:
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
                    if len(base_keys) >= 2:
                        # `base_col_clusters` is `None` unless a cluster is
                        # actually declared, in which case it carries every
                        # base key's membership — the same one-pass discipline
                        # `col_weights`/`col_clusters` follow above. The label and
                        # this argument are separately writable, so what keeps them
                        # agreeing is the collision test that asserts the clustered
                        # WIDTH rather than the label — arithmetic a unit-level draw
                        # cannot reproduce.
                        base_col_clusters = (
                            None if clusters is None else {k: clusters[k] for k in base_keys}
                        )
                        resampled = paired_percentile_of_derived(
                            of_collapsed,
                            against_collapsed,
                            base_keys,
                            compute_of,
                            compute_against,
                            seed,
                            draws=draws,
                            strata=strata,
                            method=(
                                "paired_percentile_over_units_clustered"
                                if base_col_clusters is not None
                                else "paired_percentile_over_units"
                            ),
                            clusters=base_col_clusters,
                        )
                        interval = resampled.interval
                # § Contrasts: `n_paired` is the intersection, and a PAIRED contrast has
                # to record it. An unpaired contrast's intersection is empty by
                # construction, so `n_paired: 0` would be arithmetically true and
                # descriptively false — and § Contrasts already spends `0` on a different
                # meaning, a pairing that failed, which is the whole reason this key is
                # absent here rather than zero. Absent, not null, the shape `weighted_by`
                # and `n_paired_effective` already use.
                metric_block[metric_key] = {
                    "delta": delta,
                    "basis": "units",
                    "paired": is_paired,
                    "method": interval.method if interval else None,
                    # `is_derived` is always True on this arm, so the count is
                    # `base_keys` unconditionally — `col_keys` belongs to the
                    # recorded-column arm below and referencing it here (even
                    # inside a ternary neither branch of which is ever taken)
                    # is a name pyflakes cannot prove bound on this path.
                    **(
                        {"n_paired": len(base_keys)}
                        if is_paired
                        else {"n_of": len(of_col), "n_against": len(against_col)}
                    ),
                    "ci95": [interval.low, interval.high] if interval else None,
                    "cohens_d": None,
                    "correction": None,
                }
            else:
                if is_paired:
                    col_keys = [
                        k
                        for k in base_keys
                        if metric_key in of_collapsed[k]
                        and metric_key in against_collapsed[k]
                        # The guard at the subtraction, not at another function's
                        # output. **Two cases, and only one of them is a future
                        # one.**
                        #
                        # LIVE, reachable from a validated config: a column
                        # NUMERIC for some units and `None` for others. Ruling 1
                        # publishes a perfectly good mean for such a column, so it
                        # legitimately becomes a `metric_key` on both sides — the
                        # convention below is INTACT — and the subtraction is then
                        # reached with `k` a unit both sides carry `None` for.
                        # Measured end to end: `TypeError` outside every `try`, run
                        # directory complete, every execution paid for, no
                        # `run.yaml`. That is the crash this guard closes; its pin
                        # is the ragged-`None` blast-radius test in
                        # `tests/test_cli.py`, which H5b task 6 shipped as a strict
                        # `xfail` naming this guard as its remover.
                        #
                        # FUTURE, the convention-breaks case: a column non-numeric
                        # for EVERY unit reaches no `metric_key` today, because
                        # `of_summary` is `aggregated`'s step block and the column
                        # loop publishes no block for it — a convention at another
                        # function's output, not a guard, and **a rule enforced
                        # only by another function's output is not a guard.**
                        #
                        # It SKIPS rather than raising: the two core-bookkeeping
                        # `ValueError`s above both sit before any interval is
                        # built, while a raise here loses the `run.yaml` this guard
                        # exists to protect. A unit dropped here is dropped exactly
                        # as a unit missing the column is dropped, and `n_paired`
                        # reports what remains — `0` already means *pairing
                        # failed*, so an all-dropped metric publishes
                        # `n_paired: 0` and `ci95: null`, a shape a reader can
                        # already read. **No new code is minted**, and not on the
                        # ground that this path is unreachable — the live case
                        # above is reachable. The disclosure is the narrowed
                        # `n_paired` itself, which is unconditional and always in
                        # the record. The condition-side `W-STATS-COLUMN-THIN`
                        # is NOT a standing second disclosure here: it fires only
                        # when the contributing count falls below
                        # `limits.min_reported_n` (Controller ruling 5), so a
                        # project declaring a floor of 1 — or no floor at all —
                        # gets none, and `n_paired` is then the only signal. That
                        # gap is the ruling's own named cost, not a reason to mint
                        # a second warning here for the contrast side.
                        and _is_numeric(of_collapsed[k][metric_key])
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
                    diffs = [
                        of_collapsed[k][metric_key] - against_collapsed[k][metric_key]
                        for k in col_keys
                    ]
                    n_paired = len(col_keys)
                    # The intersection's OWN weights, in `col_keys` order, so nothing
                    # downstream can weight a unit the difference beside it did not
                    # come from. `None` when no weight is declared, which is what
                    # keeps every unweighted construction on exactly the arithmetic it
                    # had.
                    col_weights = None if weights is None else [weights[k] for k in col_keys]
                    # The intersection's OWN cluster labels, in `col_keys` order, so
                    # nothing downstream groups a unit the difference beside it did not
                    # come from. Indexed, not `.get`-ed, the discipline
                    # `t_over_units_clustered` states: a key the roster doesn't hold is
                    # a core defect, and a cluster of its own for it would raise the
                    # group count and narrow the interval. The roster-wide mapping is
                    # safe to index — `col_keys` is a subset of it — and this is not
                    # the Kish seam, which had to be narrowed because it SUMS.
                    col_clusters = None if clusters is None else [clusters[k] for k in col_keys]
                    resampled = None
                    if resample_columns and n_paired >= 2:
                        # `col_keys`, NOT `base_keys`. The derived branch above uses
                        # `base_keys` because a derived metric has no column to be
                        # ragged about; a recorded column does.
                        # `paired_percentile_of_derived` builds its `UnitTable`s from
                        # whole rows, so `base_keys` here would feed `compute` rows
                        # missing this column — `UnitTable.__getattr__` pads with
                        # `None` and the mean below raises, which the construction
                        # catches as a degenerate draw and silently drops. A quarter
                        # of a roster missing the column nulls the interval; one unit
                        # missing leaves it looking fine, which is why this is a
                        # correctness rule and not a tidiness one.
                        #
                        # The same callable twice: both sides compute the mean of the
                        # same column, which is a normal call rather than the
                        # shared-closure cancellation `paired_percentile_of_derived`
                        # warns about — that one is about a SWEPT AXIS changing which
                        # formula `aggregate` runs, and a column mean is one formula.
                        #
                        # **The weights live in the CLOSURE, not in the
                        # construction.** `paired_percentile_of_derived` is shared
                        # with the derived branch, which core does not weight
                        # (§ Weighted samples hands that weight column to `aggregate`
                        # as a unit attribute), so a `weights` parameter there would
                        # weight the wrong half. The closure can reach them because
                        # the construction keeps the real unit key inside every draw:
                        # each row is `{"unit": k, **of[k]}`, and a bootstrap draw
                        # duplicates units on purpose, so the vector is built from the
                        # DRAWN keys rather than from the roster — a vector filtered
                        # or ordered differently weights the wrong unit, which is
                        # `summarize_step`'s own discipline one level over.
                        def _column_mean(
                            table: UnitTable,
                            _name: str = metric_key,
                            _weights: dict[str, Any] | None = weights,
                        ) -> float:
                            column: list[float] = getattr(table, _name)
                            if _weights is None:
                                return float(sum(column) / len(column))
                            drawn = [_weights[k] for k in table.unit]
                            got = weighted_mean_of([float(v) for v in column], drawn)
                            if got is None:
                                # An empty column — the identical input on which the
                                # unweighted branch above raises `ZeroDivisionError`,
                                # and which `paired_percentile_of_derived` catches as a
                                # degenerate draw either way. Raised rather than
                                # coerced to a number, so the two branches refuse the
                                # same input; a fabricated 0.0 here would enter the
                                # pool as a real draw.
                                raise ValueError("a weighted column contrast drew an empty table")
                            return got

                        resampled = paired_percentile_of_derived(
                            of_collapsed,
                            against_collapsed,
                            col_keys,
                            _column_mean,
                            _column_mean,
                            seed,
                            draws=draws,
                            strata=strata,
                            # One spelling per declaration, and the weighted-clustered
                            # cell is unreachable — the `E-DATA-WEIGHT-CLUSTER-CONTRAST`
                            # guard above refuses it before either branch runs. The
                            # construction is ONE function serving three `method`
                            # strings, so the string is the caller's to pass:
                            # `paired_percentile_of_derived` is shared with the derived
                            # branch, which core neither weights nor clusters.
                            method=(
                                "paired_percentile_over_units_clustered"
                                if clusters is not None
                                else "weighted_paired_percentile_over_units"
                                if weights is not None
                                else "paired_percentile_over_units"
                            ),
                            clusters=(
                                None if clusters is None else {k: clusters[k] for k in col_keys}
                            ),
                        )
                        interval = resampled.interval
                    else:
                        # The general case, off the resample path. One arm per
                        # declaration, and the weighted-clustered cell is unreachable —
                        # the `E-DATA-WEIGHT-CLUSTER-CONTRAST` guard above refuses it
                        # before either branch runs, so this is a three-way choice
                        # over two independent declarations rather than a four-cell
                        # one with a cell missing.
                        if col_clusters is not None:
                            interval = paired_t_over_units_clustered(diffs, col_clusters)
                        elif col_weights is not None:
                            interval = weighted_paired_t_over_units(diffs, col_weights)
                        else:
                            interval = paired_t_over_units(diffs)
                    metric_block[metric_key] = {
                        # The (weighted, when `col_weights` is not `None`) mean of
                        # the per-unit differences over `col_keys` — the same unit
                        # set the interval is drawn from, and identical to the
                        # difference of the two column means over that set, so the
                        # point estimate and the pool cannot drift onto different
                        # rosters.
                        "delta": (
                            mean_of(diffs)
                            if col_weights is None
                            else weighted_mean_of(diffs, col_weights)
                        ),
                        "basis": "units",
                        "paired": is_paired,
                        "method": interval.method if interval else None,
                        "n_paired": n_paired,
                        "ci95": [interval.low, interval.high] if interval else None,
                        # Cohen's dz survives the switch: it differences a PER-UNIT
                        # value, which a column has and a derived metric does not,
                        # and it is computed from the local `diffs` list rather than
                        # from anything the `Member` carries.
                        "cohens_d": (
                            cohens_dz(diffs)
                            if col_weights is None
                            else weighted_cohens_dz(diffs, col_weights)
                        ),
                        "correction": None,
                    }
                else:
                    of_col = [
                        k
                        for k in of_side_keys
                        if metric_key in of_collapsed[k]
                        and _is_numeric(of_collapsed[k][metric_key])
                    ]
                    against_col = [
                        k
                        for k in against_side_keys
                        if metric_key in against_collapsed[k]
                        and _is_numeric(against_collapsed[k][metric_key])
                    ]
                    of_values = [of_collapsed[k][metric_key] for k in of_col]
                    against_values = [against_collapsed[k][metric_key] for k in against_col]
                    resampled = None
                    of_clusters = None if clusters is None else {k: clusters[k] for k in of_col}
                    against_clusters = (
                        None if clusters is None else {k: clusters[k] for k in against_col}
                    )
                    if resample_columns and len(of_col) >= 2 and len(against_col) >= 2:
                        # The same closure the paired arm uses, and the same
                        # argument for reusing it: both sides compute the mean of
                        # the same column, which is one formula rather than the
                        # shared-closure cancellation a swept axis produces. No
                        # weight branch, because a weighted unpaired comparison
                        # raises above.
                        def _unpaired_column_mean(
                            table: UnitTable, _name: str = metric_key
                        ) -> float:
                            column: list[float] = getattr(table, _name)
                            return float(sum(column) / len(column))

                        resampled = unpaired_percentile_of_sides(
                            of_collapsed,
                            against_collapsed,
                            of_col,
                            against_col,
                            _unpaired_column_mean,
                            _unpaired_column_mean,
                            seed,
                            draws=draws,
                            strata=strata,
                            # One spelling per declaration. The construction is ONE
                            # function serving two `method` strings, so the string is
                            # the caller's to pass — the asymmetry with the *t* arm
                            # below, where each spelling is its own function.
                            # Both the label and the two `_clusters` arguments read
                            # `of_clusters is not None` — ONE fact deciding both,
                            # the same discipline the paired derived branch above
                            # takes for the identical reason.
                            method=(
                                "unpaired_percentile_over_units_clustered"
                                if of_clusters is not None
                                else "unpaired_percentile_over_units"
                            ),
                            of_clusters=of_clusters,
                            against_clusters=against_clusters,
                        )
                        interval = resampled.interval
                    elif of_clusters is not None and against_clusters is not None:
                        interval = welch_t_over_units_clustered(
                            of_values,
                            [of_clusters[k] for k in of_col],
                            against_values,
                            [against_clusters[k] for k in against_col],
                        )
                    else:
                        interval = welch_t_over_units(of_values, against_values)
                    of_mean = mean_of(of_values)
                    against_mean = mean_of(against_values)
                    metric_block[metric_key] = {
                        # The difference of the two sides' own means, over the units
                        # each side completed AND recorded this column for. Never a
                        # mean of differences: there are no per-unit differences, and
                        # `n_paired`'s intersection is empty by construction.
                        "delta": (
                            None
                            if of_mean is None or against_mean is None
                            else of_mean - against_mean
                        ),
                        "basis": "units",
                        "paired": is_paired,
                        "method": interval.method if interval else None,
                        "n_of": len(of_col),
                        "n_against": len(against_col),
                        "ci95": [interval.low, interval.high] if interval else None,
                        # *d*s over the pooled within-condition sd — § Statistical
                        # reporting: unpaired contrasts report *d*s and it pools
                        # where `welch_t_over_units` deliberately doesn't. Keyed on
                        # `is_paired`, not on which interval arm ran, the same way
                        # `cohens_dz` survives the resample switch above: computed
                        # from the local vectors rather than from anything the
                        # `Member` carries.
                        "cohens_d": cohens_ds(of_values, against_values),
                        "correction": None,
                    }
                    # Decision: only an unpaired comparison gets a p-value, and
                    # only when the resolved `shuffle` names an axis THESE TWO
                    # CONDITIONS actually differ on — `group_axes` above, the
                    # same expression that decided `is_paired`, so the two
                    # cannot disagree about which comparisons are unpaired. A
                    # paired comparison's two conditions share their units, so
                    # its null is a per-unit sign flip rather than a
                    # relabelling and `shuffle` cannot express it. Written
                    # whether or not `interval` came back — `of_values` and
                    # `against_values` are built above regardless — the same
                    # fact-not-construction rule `n_paired` follows.
                    if null_test is not None and null_test.get("shuffle") in group_axes:
                        p_value = permutation_over_contrast(
                            of_values,
                            against_values,
                            seed=seed,
                            n=null_test["n"],
                            of_clusters=(
                                [of_clusters[k] for k in of_col]
                                if of_clusters is not None
                                else None
                            ),
                            against_clusters=(
                                [against_clusters[k] for k in against_col]
                                if against_clusters is not None
                                else None
                            ),
                            level=null_test["level"] or "rows",
                        )
                        metric_block[metric_key]["p_value"] = p_value
                        # The echo carries the derived `level`, the one resolved
                        # value the config never writes — a reader who sees
                        # `within_cluster` beside a `null_test.shuffle` the
                        # config declared over an attribute alone would
                        # otherwise have no way to tell which relabelling ran.
                        metric_block[metric_key]["null_test"] = {
                            "method": null_test["method"],
                            "n": null_test["n"],
                            "shuffle": null_test["shuffle"],
                            "level": null_test["level"] or "rows",
                        }
            # The three facts a weight adds to a contrast entry, and they move
            # together with the delta and the interval: § Contrasts requires it,
            # and a weighted delta beside an unweighted effect size or an
            # `n_paired` with no effective size beside it is a declaration
            # accepted whose effect is half delivered. Absent — not null — when no
            # weight is declared, the same absent-not-null shape `weighted_by`
            # already has per condition.
            #
            # **Kish is over the PAIRED INTERSECTION**, not over the roster-wide
            # mapping `weights` holds: under a declared `holdout` the collapsed
            # table is the test partition alone, and the size reported beside an
            # interval has to be the size the interval was computed at. Summing
            # the mapping is the natural implementation and the wrong one.
            if weights is not None:
                metric_block[metric_key]["weighted_by"] = weighted_by
                metric_block[metric_key]["n_paired_effective"] = kish_effective_n(
                    [weights[k] for k in (base_keys if is_derived else col_keys)]
                )
            # The one fact a cluster adds to a contrast entry, and it moves with
            # the interval and the `method`: § Contrasts requires it, and a
            # cluster-robust delta beside a `method` that does not say so is a
            # declaration accepted whose effect is half delivered. Absent — not
            # null — when nothing is clustered, the same absent-not-null shape
            # `weighted_by` has.
            #
            # `cluster_count_of` is the SINGLE counting expression — the one
            # `attrition`'s `n.clusters` and `t_over_units_clustered`'s df both
            # read. `len(set(...))` here would be a second authority for one
            # number.
            #
            # Over the keys the difference was actually computed over, never the
            # roster-wide mapping: a ragged column's clusters are its own, and a
            # count over the roster would describe units the delta never saw.
            if clusters is not None:
                if is_paired:
                    # Written in the same `base_keys if is_derived else col_keys`
                    # shape the `weighted_by`/`n_paired_effective` block above uses,
                    # so the two never disagree about which key set a fact is
                    # computed over. A fact about the paired INTERSECTION, not about
                    # whether a construction ran — the same reason `n_paired` itself
                    # is written whether or not `method`/`delta`/`ci95` came back
                    # non-null (`docs/superpowers/spec-defects.md`'s H4b-2 task 4
                    # entry records the decision, for the derived-key-collision
                    # corner where this fires with every other field `None`).
                    metric_block[metric_key]["n_paired_clusters"] = cluster_count_of(
                        clusters, base_keys if is_derived else col_keys
                    )
                else:
                    # Per side once the sides are disjoint, and Welch's df reads
                    # both.
                    metric_block[metric_key]["n_clusters_of"] = cluster_count_of(clusters, of_col)
                    metric_block[metric_key]["n_clusters_against"] = cluster_count_of(
                        clusters, against_col
                    )
            if confounded:
                # Marked, not merely reported: a delta mixing two axes is the
                # factorial main-effects problem, which core refuses to
                # separate. `differs_on` names them so a reader knows which.
                metric_block[metric_key]["confounded"] = True
                metric_block[metric_key]["differs_on"] = list(differs_on)
            # Finding 3 (`spec-defects.md`): every `aggregated` metric block
            # carries the resolved `resample` echo when one is declared, and a
            # contrast entry carried none. Absent, not null, matching
            # `weighted_by`'s own rule — `resample_echo` is `None` exactly when
            # `statistics.resample` is undeclared.
            if resample_echo is not None:
                metric_block[metric_key]["resample"] = dict(resample_echo)
            # `Member` requires exactly one of `pool`/`diffs`/`sides` wherever
            # there is an interval to correct: the draws a percentile interval
            # was read off, the per-unit differences a *t* interval was computed
            # from, or the two independent per-side vectors a Welch interval was
            # computed from. A column contrast whose resample ran but produced
            # too few surviving draws for the confidence level still carries its
            # (too-short) `pool` alongside a `None` `ci95`, and
            # `Member.__post_init__` exempts that case rather than requiring
            # `pool`/`diffs` to be `None` too.
            #
            # **A column contrast under a declared `resample` carries the POOL
            # and sets `diffs=None`.** `_corrected_bounds` tests `diffs` FIRST
            # and only then falls through to `pool`, so leaving `diffs` set here
            # — the natural thing to do, since `cohens_dz` still needs them —
            # would give this row a `ci95` from a percentile and a
            # `ci95_corrected` from `paired_t_over_units`. Nothing raises and no
            # reader can tell. `cohens_dz` is computed above from the local list,
            # which is why the `Member` does not need it.
            corrected_from_pool = is_derived or resample_columns
            members.append(
                Member(
                    where=where_id,
                    step=step_name,
                    metric=metric_key,
                    delta=metric_block[metric_key]["delta"] or 0.0,
                    ci95=(interval.low, interval.high) if interval else None,
                    pool=tuple(resampled.pool) if corrected_from_pool and resampled else None,
                    diffs=(None if corrected_from_pool or not is_paired else tuple(diffs)),
                    # Only where `diffs` is: a pool is already drawn from weighted
                    # values, so weights beside one would be applied twice, and
                    # `Member.__post_init__` refuses that rather than letting it
                    # through. `corrected_from_pool` is the single decision, read
                    # once for both fields, so the two cannot disagree.
                    weights=(
                        None if corrected_from_pool or col_weights is None else tuple(col_weights)
                    ),
                    # `corrected_from_pool` is the single decision, read once for
                    # all three fields, so `pool`, `weights` and `clusters` cannot
                    # disagree about which evidence this member carries.
                    clusters=(
                        None if corrected_from_pool or col_clusters is None else tuple(col_clusters)
                    ),
                    # The single decision, read once for all four fields now:
                    # "the same decision, read once for all three fields, so
                    # `pool`, `weights` and `clusters` cannot disagree" extends to
                    # a fourth. An unpaired contrast never carries `diffs` (above)
                    # and never reaches here under `corrected_from_pool` — a
                    # resampled unpaired column carries the POOL instead, the same
                    # `corrected_from_pool` decision the paired arm reads.
                    sides=(
                        None
                        if corrected_from_pool or is_paired
                        else UnpairedEvidence(
                            of=tuple(of_values or ()),
                            against=tuple(against_values or ()),
                            clusters=(
                                None
                                if of_clusters is None or against_clusters is None
                                else (
                                    tuple(of_clusters[k] for k in of_col),
                                    tuple(against_clusters[k] for k in against_col),
                                )
                            ),
                        )
                    ),
                    # Placeholder: this function only sees one comparison, not
                    # the whole family. The caller that concatenates
                    # `vs_baseline_members` and `contrast_members` reassigns
                    # this to the position in that combined, ordered list —
                    # the only point where the full declaration order exists.
                    declaration_index=0,
                    # Absent on the block iff absent here: `.get` rather than a
                    # second condition, so this cannot disagree with the write
                    # above about which comparisons carry one.
                    p_value=metric_block[metric_key].get("p_value"),
                )
            )
            # § Validation keys this on the comparison's realized denominator, and an
            # unpaired comparison has two — so it fires where EITHER is below the
            # floor. § Contrasts grounds the row in "a stratified comparison is where
            # a small denominator is easiest to miss and most disclosive", and the
            # disclosive quantity is a thin denominator anywhere: a five-unit arm
            # against a five-hundred-unit one is exactly what the limit exists to
            # catch, and a rule reading one side or a total would pass it.
            #
            # Finding 1 (`spec-defects.md`, "the contrast path discloses nothing
            # about its resample"): a resample thin enough that
            # `paired_percentile_of_derived`/`unpaired_percentile_of_sides`
            # returned `interval=None` publishes `ci95: null` here with
            # nothing warning it came from a thin pool rather than a thin
            # `n_paired`/`n_of`/`n_against` — `W-STATS-RESAMPLE-THIN` is
            # emitted from exactly one site, the per-condition
            # `summarize_step` loop, and never reaches a comparison built
            # here. `resampled` is bound (to `None` or a `PairedResample`) on
            # every arm above, so this one check covers the derived and the
            # column-resample branches alike, carrying `where_id` — the
            # addressing `W-STATS-CONTRAST-THIN` below does not, since that
            # warning's own `"where"` argument is `limits.min_reported_n`.
            if resampled is not None and resampled.draws_used < draws:
                floor = min_honest_draws()
                findings.warn(
                    "W-STATS-CONTRAST-RESAMPLE-THIN",
                    where_id,
                    f"{where}, step {step_name!r} metric {metric_key!r}: "
                    f"{resampled.draws_used} of {draws} resample draws produced a "
                    "value"
                    + (
                        f"; below the {floor} an interval can honestly be read off, so ci95 is null"
                        if resampled.draws_used < floor
                        else ""
                    ),
                )
            # ONE finding per metric entry, naming every denominator below the floor.
            # The warning is about this entry's disclosure, and two findings for one
            # entry would double-count in any consumer that counts them.
            #
            # Scoped to a comparison declaring a `within`, because that is the scope
            # `reference.md` gives it three times over — § Contrasts, § The one config
            # file's comment, and the § Validation row. `min_reported_n: 10` is in
            # every generated config, so warning on every comparison would fire on
            # any pilot under ten units for a comparison the document never scoped it
            # to.
            if comp.within is not None and min_reported_n is not None:
                denominators = (
                    (("n_paired", len(base_keys) if is_derived else len(col_keys)),)
                    if is_paired
                    else (("n_of", len(of_col)), ("n_against", len(against_col)))
                )
                thin = [f"{name} {value}" for name, value in denominators if value < min_reported_n]
                if thin:
                    findings.warn(
                        "W-STATS-CONTRAST-THIN",
                        "limits.min_reported_n",
                        f"{where}, step {step_name!r} metric {metric_key!r}: "
                        f"{' and '.join(thin)} — below limits.min_reported_n "
                        f"({min_reported_n})",
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
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, Any]]],
    derived_by_key: dict[tuple[int, str], dict[str, Any] | None],
    resample_fns_by_key: dict[
        tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
    ],
    seed: int,
    draws: int,
    findings: Collector,
    resample_columns: bool,
    weights: dict[str, Any] | None = None,
    strata: dict[str, str] | None = None,
    weighted_by: str | None = None,
    clusters: dict[str, str] | None = None,
    resample_echo: dict[str, Any] | None = None,
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

    **No `null_test` parameter, deliberately** — decision 6: a group-axis
    p-value lands on a declared `statistics.contrasts` entry and never in
    `vs_baseline`. This is not a gate this function has to enforce: a baseline
    fixing a group level draws the permanent `E-SWEEP-BASELINE-GROUP`, so every
    comparison built here is within one group-axis cell and `is_paired` is
    always true for it — `_comparison_step_blocks` would write nothing even if
    handed a `null_test`. Omitted rather than threaded-and-unused, so a reader
    does not have to check that it is always `None` here.
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
            resample_columns=resample_columns,
            weights=weights,
            strata=strata,
            weighted_by=weighted_by,
            clusters=clusters,
            resample_echo=resample_echo,
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
    collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, Any]]],
    derived_by_key: dict[tuple[int, str], dict[str, Any] | None],
    resample_fns_by_key: dict[
        tuple[int, str], dict[str, Callable[[UnitTable], float | None]] | None
    ],
    seed: int,
    draws: int,
    findings: Collector,
    resample_columns: bool,
    weights: dict[str, Any] | None = None,
    strata: dict[str, str] | None = None,
    weighted_by: str | None = None,
    clusters: dict[str, str] | None = None,
    null_test: dict[str, Any] | None = None,
    resample_echo: dict[str, Any] | None = None,
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

    `null_test`, threaded through to `_comparison_step_blocks` unchanged, is
    decision 6's landing site: a declared contrast is the only place a
    group-axis p-value lands, so this is the one caller that carries it.
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
            resample_columns=resample_columns,
            weights=weights,
            strata=strata,
            weighted_by=weighted_by,
            clusters=clusters,
            null_test=null_test,
            resample_echo=resample_echo,
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


def _resolved_resample(doc: dict[str, Any]) -> dict[str, Any]:
    """`statistics.resample` with every default filled in, resolved once.

    `reference.md` § Statistical reporting: "A derived metric is resampled
    whether or not you declare `statistics.resample`" — declaring it "changes
    the method or the count rather than switching the behaviour on, and the
    resolved values are recorded in `run.yaml` beside the interval". So the
    defaults are real values here rather than `summarize_step`'s own defaults
    taking effect unseen at a call site that forgot them.

    **`declared` is separate from `n` on purpose.** A config asking for exactly
    2000 draws and a config asking for nothing both resolve to 2000, but only
    the first turns a RECORDED COLUMN into a percentile interval — a column has
    a t-interval available, so resampling it is a choice and `resample` is what
    makes it, while a derived metric has no such fallback. Reading `declared`
    off `n != 2000` would silently make that sentence false. `command_run` reads
    `declared` (H4a task 14) to gate `summarize_step`'s `resample_columns`.

    **`.get("resample") or {}`, never `.get("resample", …)`**: `materialize.py`
    writes no `resample` key at all and a hand-written config may write
    `resample: null`, and the two are different documents that must resolve to
    one answer.

    `stratify_by` goes through `units.stratum_names`, the same normalization the
    draw balances on and `validate._check_resample` checks names against, so a
    bare `stratify_by: site` is one name to all three. Resolved here and carried
    on the returned dict; `command_run` reads it to compose the roster-wide
    `resample_strata` mapping (H4a task 15) that reaches both
    `summarize_step`'s recorded-column branch and its derived-metric one —
    `percentile_over_units`/`percentile_over_units_clustered` and
    `percentile_of_derived` all take a `strata` parameter now, so one declared
    `stratify_by` moves both constructions the same way rather than leaving a
    stratified column beside an unstratified derived metric in the same table.
    """
    declared = ((doc.get("statistics") or {}).get("resample")) or {}
    if not isinstance(declared, dict):
        declared = {}
    n = declared.get("n")
    method = declared.get("method")
    return {
        "method": method if isinstance(method, str) and method else "bootstrap",
        "n": n if isinstance(n, int) and not isinstance(n, bool) else 2000,
        "stratify_by": stratum_names(declared.get("stratify_by")),
        "declared": bool(declared),
    }


def _resolved_null_test(doc: dict[str, Any]) -> dict[str, Any] | None:
    """`statistics.null_test` with every default filled in, resolved once —
    `_resolved_resample`'s shape, for the block this task gives a p-value home.

    `None` when nothing is declared, never a `declared: False` dict — every
    caller below gates on `null_test is not None`, so "no null test declared"
    and "this caller has not been taught about null tests" collapse to one
    check rather than two, and the returned dict itself carries no `declared`
    key: unlike `_resolved_resample`'s twin (which distinguishes an explicit
    `n: 2000` from an undeclared block that resolves to the same default),
    there is no shape here that resolves to a truthy dict and still needs to
    say "but nothing was actually declared" — a `None` return already says
    that.

    **`.get("null_test") or {}`, never `.get("null_test", …)`**: `materialize.py`
    writes no `null_test` key at all and a hand-written config may write
    `null_test: null`, and the two are different documents that must resolve
    to one answer.

    `level` is left `None` here on purpose — `units.null_test_level` needs the
    roster, which this function does not have, so `command_run` fills it in
    once the roster it resolves is in scope.
    """
    declared = ((doc.get("statistics") or {}).get("null_test")) or {}
    if not isinstance(declared, dict) or not declared:
        return None
    method = declared.get("method")
    n = declared.get("n")
    shuffle = declared.get("shuffle")
    return {
        "method": method if isinstance(method, str) and method else "permutation",
        "n": n if isinstance(n, int) and not isinstance(n, bool) else 5000,
        "shuffle": shuffle if isinstance(shuffle, str) and shuffle else None,
        "level": None,
    }


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


@dataclasses.dataclass(frozen=True)
class Prepared:
    """Everything phases 1-5 of `command_run` produce that phases 6-10 read.

    Thirty-SIX values when this docstring's measurement was taken, and
    thirty-SEVEN since H3c-3 task 4 (the paragraph below). The count is the
    argument FOR the seam: nothing in
    phases 6-10 can be re-entered without them, so a second entry either
    receives them or recomputes them, and recomputing is what `resume` (H9b)
    must not do.

    Measured rather than chosen, and the measurement is stated because two of
    the thirty-six are not like the others. An `ast` walk over `command_run`
    found **38** names assigned before the `allocate_run_dir` call and loaded
    after it; `u` and `r` are comprehension targets (comprehension-scoped, so
    they never touch the outer binding) and `warn_c` is re-bound in phase 9
    before its second read, which is the plan's § Corrections 13 and 17. That
    leaves the **35** the plan's task 2 section lists, in that order.

    `config_path` is the thirty-sixth, and the plan's list is short by exactly
    it: a Store-walk **cannot see a parameter** -- `config_path` is an `arg`
    node, never a `Name` in `Store` context -- and it is read after the seam at
    the one site H8b Decision 7 added,
    `(run_dir / "config.yaml").write_bytes(config_path.read_bytes())`. It was
    found by `ruff`'s `F821`, not by the walk and not by `mypy`, which is the
    plan's correction 20.

    `c` is the run's live `Collector` -- a channel, not a value, and it is
    named separately so a reader does not mistake it for state. It is carried
    because a second entry into phases 1-5 needs the diagnostic channel those
    phases rendered from. **No statement in phases 6-10 reads it at this
    commit** -- every post-seam `c` is a comprehension target, and phase 9's
    `warn_c`, `aggregate_c` and `drift_c` are each a fresh `Collector`, so
    `_execute_prepared` does not unpack it. Every other field is read in
    phases 6-10.

    **Thirty-SEVEN since H3c-3 task 4**, and the `ast` walk above is not
    re-run: it measured what `command_run` assigned before the seam and loaded
    after it, and that measurement stays what it was. `cells` is the
    thirty-seventh, ADDED by that task rather than found by the walk — the
    design's cell decomposition, realized once beside `group_axes` because
    `_resumed_allocation` and `_execute_prepared` both need it and a second
    derivation of a decomposition is a second producer of it. Its reader in
    phases 6-10 is `sweep.yaml`'s `partitions_within` (H3c-3 task 11), which
    is written exactly when this decomposition has a populated cell.

    Frozen on purpose: phases 6-10 must not write back into what phases 1-5
    pinned. That is the property `resume` will rest on. `plan` is the one name
    phases 6-10 re-bind (`_apply_execution_order` under `order: randomized`),
    which is why `_execute_prepared` unpacks to locals rather than reading
    attributes: a frozen field cannot be re-bound.
    """

    config_path: Path
    c: Collector
    doc: dict[str, Any]
    repo_root: Path
    git: GitInfo
    digest: str
    input_dir: Path
    output_dir: Path
    units_decl: dict[str, Any] | None
    # Quoted: `Condition` is a `TYPE_CHECKING`-only import (line ~147) and a
    # dataclass field annotation IS evaluated at runtime — this module has no
    # `from __future__ import annotations`. Caught by importing, not by `ruff`
    # or `mypy`, both of which passed clean with the bare name.
    conditions: "list[Condition]"
    run_template: BaseTemplate | None
    credentials: dict[str, str]
    roster: UnitList | None
    beside_n: dict[str, Any]
    weight_by: Any
    weights: dict[str, Any] | None
    weighted_beside: dict[str, Any]
    cluster_by: Any
    clusters: dict[str, str] | None
    levels: list[RepeatLevel]
    repeats: list[Repeat]
    partitions: list[list[Unit]] | None
    fold_members: dict[str, frozenset[str]] | None
    group_axes: dict[str, ArmPlan]
    holdout_plan: HoldoutPlan | None
    eval_roster: UnitList | None
    arm_members_map: dict[int, frozenset[str]] | None
    plan: list[Execution]
    cfgs: dict[int, Config]
    ch: str
    ph: str
    manifest: dict[str, Any]
    lock_path: Path | None
    lock_hash: str | None
    upstream_ledger: UpstreamLedger
    upstream_resolver: UpstreamResolver
    cells: dict[tuple[tuple[str, str], ...], frozenset[str]] | None


@dataclasses.dataclass(frozen=True)
class Resumed:
    """What a SECOND entry into phases 6-10 pins, beside `Prepared` (H9b
    Decision 14). `None` at `_execute_prepared` means `run` or `draft`, and
    every line there behaves as it does today.

    **Frozen for the reason `Prepared` is**, and it is the same reason stated
    once more rather than a convention followed: phases 6-10 must not write
    back into what the second entry decided, because everything here was read
    off the previous attempt's own artifacts and a phase that mutated one
    would be publishing a figure the previous run never recorded.
    `prior_results` is a TUPLE rather than a list for the same reason at one
    level down — a frozen dataclass holding a list still hands out a list
    anything can `append` to, and the aggregate phase iterates it.

    - `run_dir` — the existing run directory. Phase 6 uses it instead of
      calling `allocate_run_dir`, which is why no second run directory is
      created and why `E-RUN-ID-EXHAUSTED` is unreachable from `resume`.
    - `prior_results` — one `ExecutionResult` per triple with a `completed`
      record, reconstituted from the artifacts (Decision 4). The aggregate
      phase reads `rows`, `recorded`, `skipped` and `returned` off these and
      no file at all, so a `resume` that skipped a triple without
      reconstituting it would publish every interval over the re-executed
      triples only.
    - `attempts` — per-triple record counts off `executions.jsonl`
      (`lineage.attempt_counts`), straight into `assemble_run_yaml`.
    - `baseline` — the apparatus observations replayed from
      `apparatus/probes.jsonl`, so a fact that moved during the crash is
      gated against the ORIGINAL run's first-answered value rather than
      against this attempt's first probe. **EMPTY, not `None`, for a run
      that never probed** — `replay_ledger` returns an empty `Observations`
      for an absent ledger, which is exactly what an `Observer` builds for
      itself, so an absent baseline mints no refusal (Decision 11) and this
      path needs no branch for it. `None` stays legal at the type level for
      a caller with no ledger to offer, and is what every `Observer` outside
      a resume gets.
    - `recorded_manifest` — the manifest the first attempt wrote, so phase
      8's `verify_manifest` asks whether the inputs moved during THIS
      attempt and `run.yaml`'s `input_manifest_hash` stays the original
      figure (Decision 8).
    - `execution_order` — `sweep.yaml`'s RECORDED `(condition, repeat)`
      sequence, applied to the rebuilt plan instead of re-realizing the
      shuffle (Decision 9), and `None` when the recorded `order` is
      `as_declared`. `None` is the record's own answer rather than a missing
      one: `_apply_execution_order` regroups repeat executions pair-major
      where `build_plan` lays them out step-major, so applying it to a run
      that declared no shuffle would execute in an order the first attempt
      did NOT run in. Which of the two it is comes from the recorded `order`
      scalar rather than from the re-read config, because the file is what
      the first attempt actually did.
    """

    run_dir: Path
    prior_results: tuple["ExecutionResult", ...]
    attempts: dict[tuple[str, int | None, str | None], int]
    baseline: "apparatus.Observations | None"
    recorded_manifest: dict[str, Any]
    execution_order: tuple[tuple[int, str], ...] | None


def _reconstitute(
    plan: list[Execution],
    *,
    run_dir: Path,
    records: list[dict[str, Any]],
    collapse: bool,
) -> tuple["ExecutionResult", ...]:
    """One FULL `ExecutionResult` per plan triple that already has a
    `completed` record, in plan order (H9b Decision 4).

    **Why a full result and not a skip.** The aggregate phase reads
    `ExecutionResult.rows`, `.recorded`, `.skipped` and `.returned` off the
    in-memory list and **no file at all** — `recording_steps` is
    `{r.execution.step_name for r in results if … and r.rows}`,
    `collapse_repeats`/`repeats_disagreeing` walk `r.rows`/`r.recorded`
    through `_gather_repeats`, `attrition` walks `r.recorded`/`r.skipped`, and
    `per_repeat` is built from `r.returned`. So a `resume` that merely skipped
    a completed triple would publish every interval, every `n`, every delta
    and every hypothesis verdict **over the re-executed triples only** —
    plausible numbers, no diagnostic, `status: completed`. That is why this
    function exists and why guard-pin arm A is a whole-record equality rather
    than a set of per-key assertions.

    Sited in `cli` rather than in a module of its own: `reference.md`
    § Package layout has no `resume.py` (its "resume resolution" line names
    `run_identity.py`, which owns the run-ID and lock surface and reads no
    step artifact), and this function's only caller is `command_resume` two
    definitions below. A new module would be a § Package layout change
    carried by a code task rather than by the documents task.

    **The narrowing is by `recorded_columns`, never by subtracting declared
    attribute names.** `finalize` writes `unit`, then every declared
    attribute, then every recorded key — so the file holds columns this
    execution did not record, and they must not reach the unit table `stats`
    reads. Subtracting attributes by name would be a name standing in for a
    structural fact, and `finalize`'s own merge puts a RECORDED value under
    the shared column when the two names collide.

    **Row key order is the FILE's, not `recorded_columns`'.** That list is
    sorted; `io.rows()` preserves `{"unit": key, **values}` insertion order,
    and `units.parquet`'s columns preserve it too (`_finalize_columns` is
    first-seen order). `_gather_repeats` builds its column order from row
    iteration order and `summarize_step` derives a metric's column order from
    that, so narrowing by iterating the sorted list would move `run.yaml`'s
    column order with every value correct — the exact failure arm A names.
    Filtering the row's own items keeps the order the run had.

    Four refusals, each a distinguishable fault with its own remedy:

    - a completed line with no `returned`/`recorded_columns` key —
      `E-RESUME-LEDGER-UNREADABLE`: a ledger written by a build older than
      these two keys cannot be resumed, because the alternative is a
      `per_repeat` hole and a unit table narrowed to `unit` alone, which is
      the silent-wrong-numbers shape this whole decision is about;
    - a non-empty `recorded_columns` and no `units.parquet` —
      `E-RESUME-ROWS-MISSING`;
    - a `units.parquet` that will not decode, or whose columns do not cover
      that line's `recorded_columns` — `E-RESUME-ROWS-UNREADABLE`;
    - and an EMPTY `recorded_columns` with no `units.parquet` is **not** a
      refusal at all: `finalize` writes the table only `if self._rows`, so a
      scalar-only step legitimately writes none.
    """
    from publishable.artifacts import READERS
    from publishable.lineage import ledger_key
    from publishable.runner import ExecutionResult, step_dir_for

    completed: dict[tuple[str, int | None, str | None], dict[str, Any]] = {}
    for entry in records:
        if entry.get("status") == "completed":
            # Last completed record wins, which is the same answer as "the
            # only one": once a triple completes, `resume` filters it out of
            # every later plan, so a second completed record for one triple
            # is not reachable through this build.
            completed[ledger_key(entry)] = entry

    results: list[ExecutionResult] = []
    for execution in plan:
        key = (execution.step_name, execution.condition_index, execution.repeat_label)
        found = completed.get(key)
        if found is None:
            continue
        entry = found
        for name in ("returned", "recorded_columns"):
            if name not in entry:
                raise ContractError(
                    f"{run_dir / 'executions.jsonl'}: the completed record for "
                    f"{execution.step_name!r} (condition {execution.condition_index!r}, "
                    f"repeat {execution.repeat_label!r}) has no {name!r}; a run recorded "
                    "by a build older than this one cannot be resumed",
                    code="E-RESUME-LEDGER-UNREADABLE",
                )
        # `step_dir_for`, never a second path construction: it already owns
        # the degenerate-level collapse, and two constructions would be two
        # answers to which directory a triple wrote into.
        step_dir = step_dir_for(run_dir, execution, collapse)
        columns = list(entry["recorded_columns"])
        table = step_dir / "units.parquet"
        rows: tuple[dict[str, Any], ...] = ()
        if table.exists():
            try:
                decoded = READERS[".parquet"](table.read_bytes())
            except Exception as exc:
                raise ContractError(
                    f"{table} will not decode ({type(exc).__name__}: {exc})",
                    code="E-RESUME-ROWS-UNREADABLE",
                ) from exc
            present = set(decoded[0]) if decoded else set()
            uncovered = [name for name in columns if name not in present]
            if uncovered:
                raise ContractError(
                    f"{table} holds no column {', '.join(uncovered)}, which its "
                    "`executions.jsonl` record names as recorded",
                    code="E-RESUME-ROWS-UNREADABLE",
                )
            keep = {"unit", *columns}
            rows = tuple({k: v for k, v in row.items() if k in keep} for row in decoded)
        elif columns:
            raise ContractError(
                f"{table} is absent, and this execution's record names "
                f"{', '.join(columns)} as recorded",
                code="E-RESUME-ROWS-MISSING",
            )
        skipped: set[str] = set()
        ineligible = step_dir / "ineligible.jsonl"
        if ineligible.exists():
            # Through the same reader `io.write` dispatches to, so a line this
            # build wrote is read back by the code that wrote it.
            for line in READERS[".jsonl"](ineligible.read_bytes()):
                skipped.add(line["unit"])
        results.append(
            ExecutionResult(
                execution=execution,
                status=entry["status"],
                started_at=entry["started_at"],
                wall_seconds=entry["wall_seconds"],
                returned=entry["returned"],
                error=entry.get("error"),
                recorded=frozenset(row["unit"] for row in rows),
                skipped=frozenset(skipped),
                rows=rows,
            )
        )
    # A tuple, matching `Resumed.prior_results`: a list here would type-check
    # nowhere and behave identically at runtime, so `mypy` is the enforcer and
    # this assertion is the one thing a test can see.
    return tuple(results)


def _stale(detail: str) -> "ContractError":
    """One refusal, `E-RESUME-ALLOCATION-STALE`, for one remedy: the recorded
    allocation cannot be applied to what this tree resolves, so the run cannot
    be continued and a new one must be started. Every arm of the application
    below raises through here so the code and the remedy cannot drift
    apart."""
    return ContractError(
        f"allocation.json {detail}; the recorded allocation cannot be applied to this "
        "roster, so the run cannot be continued — start a new run",
        code="E-RESUME-ALLOCATION-STALE",
    )


def _fold_strata(
    fold_level: "RepeatLevel | None", roster: "UnitList | None"
) -> dict[str, str] | None:
    """A `fold` level's `stratify_by` as a `{unit key: stratum}` map, or `None`
    when the level declares none — `units.partition_within_cells`' `strata`
    argument.

    **One derivation, two callers**, and the second is the reason it is a
    function at all: `_prepare_run` builds this map before drawing the
    partitions, and `_resumed_allocation` re-draws them on the overridden cells
    and needs the same map. Two spellings would be two answers to what a
    stratum is, over one declaration.

    Indexed, not `.get`-ed, and total over the roster because it has to be —
    `units.partition_units` raises `KeyError` on a gap, by contract, and
    `validate` guarantees the name is a declared attribute
    (`E-REPL-FOLD-STRATIFY-UNKNOWN`), so a missing key is a core defect rather
    than something to soften here. Stringified for `clusters_of`'s reason: a
    stratum is a label, nothing downstream does arithmetic on it, and one type
    keeps a hand-built roster and a table-sourced one giving the same split.
    """
    if fold_level is None or roster is None or not fold_level.stratify_by:
        return None
    return {u.key: str(u.attributes[fold_level.stratify_by]) for u in roster}


def _resumed_allocation(prepared: "Prepared", document: dict[str, Any]) -> "Prepared":
    """`allocation.json` **read rather than re-drawn** (H9b Decision 10): the
    arm memberships and the holdout partition `_prepare_run` just resolved are
    replaced by the ones the first attempt recorded, through
    `dataclasses.replace` on the frozen `Prepared`.

    **This function overrides results; it moves no call.** What happens
    here is one step later and on the other side of the seam: the plans are
    rebuilt from the record and `arm_members` is called **again**, on the
    overridden axes, so that the per-condition mapping is a reduction of the
    membership the run actually used rather than of a second draw. Calling it
    again is what keeps `units.arm_members` the single authority for that
    reduction — re-deriving the mapping here by hand would make this function
    a second producer of arm membership, which is the fault its own docstring
    exists to prevent a third instance of.

    **Seed and strata come from the record too, not from the recomputed
    plans**, and that is what makes `provenance.allocation_hash` cover the
    file on disk: `_execute_prepared` computes it as
    `allocation_hash(build_allocation_document(group_axes, holdout_plan))`,
    and a resume never rewrites `allocation.json`, so anything here that
    differed from the record would publish a hash of a document no file
    holds. A pin asserts the round trip — the rebuilt document equals the
    recorded one — rather than trusting this paragraph.

    **What is checked, and every arm is `E-RESUME-ALLOCATION-STALE`.** The
    axis set, each axis's level set, and the holdout's presence must agree
    with what this tree resolved; and each recorded membership must be
    exactly the roster's keys, in both directions. Set equality rather than
    subset tolerance, `units.arms_of`'s own rule for the same reason
    (§ Allocation: "each unit belongs to exactly one arm"): a roster that
    *lost* a unit leaves the record naming a unit that no longer exists, and
    a roster that *gained* one leaves that unit in no arm at all — with no
    fourth part of `n` for it, and nothing in the record marking it.
    **Bounded by the methods that are realized**: union-equals-roster holds
    for `by_attribute` (`arms_of`'s set-equality rule) and for `random` (the
    shipped draw partitions the whole roster), which are the two
    `HOLDOUT_METHODS_REALIZED`-style pair this build has. A future method
    that partitioned only part of a roster would make this guard refuse a
    legitimate resume, and the fix would then be here rather than in the
    method.

    **Fold partitions ARE re-derived here** (H3c-3, Ruling KK). A partition is
    a function of the roster, the design digest **and the cell decomposition**;
    the decomposition is what this function overrides, one call above; so the
    partitions drawn from the fresh decomposition are stale the moment the
    override lands. They are re-derived through `units.partition_within_cells`
    — the **same single producer** `_prepare_run` calls, on the **overridden**
    axes — and never by hand here, which would make this function a second
    producer of fold membership, the fault its own docstring exists to prevent
    a third instance of. `partition_units` itself is still not called from this
    function.

    **The gate is "a fold level exists", never "an axis exists".** With no
    axis the producer takes its own one-cell reduction and returns the
    byte-identical partition, so gating on `group_axes` would be a branch whose
    no-axis arm is provably a no-op — one more thing to get wrong than a proof.
    `prepared.partitions is None` is a different question: it means the design
    declares no `fold` level at all, so there is no `k` to draw and nothing to
    replace. `fold_members` follows from the partitions through
    `replication.fold_members_for`, exactly as it does in `_prepare_run`.

    **`Prepared.cells` is deliberately left as `_prepare_run` derived it.** Its
    one reader below the override is `sweep.yaml`'s `partitions_within`, which
    projects the AXIS NAMES out of the first populated cell — and the guards
    above force the recorded axis set and each axis's level set to equal this
    tree's, so the stale object and a re-derived one give that projection the
    same answer. The decomposition the partitions are drawn inside is
    `cells_of(axes)`, computed here from the overridden plans.
    """
    from publishable.units import arm_members

    roster_keys = {u.key for u in prepared.roster} if prepared.roster is not None else set()
    recorded_arms = document.get("arms") or {}
    recorded_seeds = document.get("seed") or {}
    recorded_strata = document.get("strata") or {}
    if not isinstance(recorded_arms, dict):
        raise _stale("holds an `arms` block that is not a mapping of axis to arm")
    if set(recorded_arms) != set(prepared.group_axes):
        raise _stale(
            f"records the axes {sorted(recorded_arms)} while this config resolves "
            f"{sorted(prepared.group_axes)}"
        )
    axes: dict[str, ArmPlan] = {}
    for axis, plan in prepared.group_axes.items():
        members = recorded_arms[axis]
        if not isinstance(members, dict):
            raise _stale(f"records axis {axis!r} as {type(members).__name__}, not a mapping")
        if set(members) != set(plan.members):
            raise _stale(
                f"records axis {axis!r} with the levels {sorted(members)} while this "
                f"config resolves {sorted(plan.members)}"
            )
        recorded_keys = {key for keys in members.values() for key in keys}
        if recorded_keys != roster_keys:
            raise _stale(
                f"records axis {axis!r} over {len(recorded_keys)} unit(s) that are not "
                f"this roster's {len(roster_keys)}: "
                f"{sorted(recorded_keys ^ roster_keys)[:5]} disagree"
            )
        axes[axis] = dataclasses.replace(
            plan,
            members={level: tuple(keys) for level, keys in members.items()},
            seed=recorded_seeds.get(axis),
            strata=tuple(recorded_strata.get(axis) or ()),
        )

    recorded_holdout = document.get("holdout")
    holdout = prepared.holdout_plan
    if (recorded_holdout is None) != (holdout is None):
        raise _stale(
            "records a holdout this config does not declare"
            if holdout is None
            else "records no holdout while this config declares one"
        )
    if recorded_holdout is not None and holdout is not None:
        train = tuple(recorded_holdout.get("train") or ())
        test = tuple(recorded_holdout.get("test") or ())
        if set(train) | set(test) != roster_keys or len(train) + len(test) != len(roster_keys):
            raise _stale(
                f"records a holdout over {len(train)} + {len(test)} unit(s) that are not "
                f"a partition of this roster's {len(roster_keys)}"
            )
        holdout = dataclasses.replace(
            holdout,
            train=train,
            test=test,
            seed=recorded_holdout.get("seed"),
            strata=tuple(recorded_holdout.get("strata") or ()),
        )

    # The folds, re-drawn inside the RECORDED cells. See this function's own
    # docstring for why this is not gated on `axes` and why it goes through the
    # same producer `_prepare_run` calls rather than being computed here.
    partitions = prepared.partitions
    fold_members = prepared.fold_members
    if partitions is not None and prepared.roster is not None:
        partitions = partition_within_cells(
            prepared.roster,
            len(partitions),
            prepared.digest,
            cells_of(axes) if axes else {},
            clusters=prepared.clusters,
            strata=_fold_strata(
                next((lv for lv in prepared.levels if lv.kind == "fold"), None),
                prepared.roster,
            ),
        )
        fold_members = fold_members_for(prepared.levels, partitions)

    eval_roster = _evaluation_roster(prepared.roster, holdout)
    # `_prepare_run`'s own invariant, restated on this path because this path
    # has no counterpart of it: a narrowing that returned `None` for a real
    # roster would hand `execute_plan` no units at all.
    assert (eval_roster is None) == (prepared.roster is None)
    return dataclasses.replace(
        prepared,
        group_axes=axes,
        holdout_plan=holdout,
        partitions=partitions,
        fold_members=fold_members,
        eval_roster=eval_roster,
        # `None` stays `None`: whether a per-condition mapping exists at all
        # is `_prepare_run`'s decision (it gates on `selector_paths`), and a
        # resume overrides what that mapping HOLDS, never whether there is
        # one.
        arm_members_map=(
            None if prepared.arm_members_map is None else arm_members(axes, prepared.conditions)
        ),
    )


def _prepare_run(config_path: Path, *, allow_dirty: bool) -> "Prepared | int":
    """Phases 1-5 of a run, for every command that is a second entry into them.

    Returns `Prepared` or the exit code the run would have returned. **Every
    caller checks the union with `isinstance`, never truthiness** -- `EXIT_OK`
    is `0` and a truthiness test would mis-handle it. Phases 1-5 never return
    `EXIT_OK` today, which is exactly why that mutation is blind and why the
    rule is stated here rather than pinned: `mypy` is the enforcer, and task
    1's arm E pins the four codes end to end instead.

    `allow_dirty` is the one thing that varies between callers, and it varies
    the GATE, never its PATHSPEC. `run` passes `False`, `draft` and `dry-run`
    pass `True`. Widening what `E-CODE-DIRTY` covers is a separate, DECLINED
    decision (H6b Decision 12) that lives one line from this one.
    """
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
    # The second load site, and it is not redundant. Loading is a precondition of
    # *executing*, not a side effect of checking: `validate` loads because three
    # § Validation rows ask whether a variable is set, and `run` loads because a
    # step is about to read one. Idempotent and never overriding, so the second
    # call costs nothing. `reference.md` § Secrets & credentials.
    load_env(repo_root)
    git = git_provenance(config_path, config_path)  # phase 3: clean src/**+templates/**
    if git.code_dirty and not allow_dirty:
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

    # Moved above the roster: a resolver's own body is user code and the first
    # thing in this command that can raise carrying a credential it read, so the
    # values `redact` answers from must exist before that call is reached, not
    # after. `conditions` and `run_template` travel with `credentials` because
    # `declared_credential_names` needs both.
    conditions = expand(doc)
    # Resolved here rather than read off the later `get_template` call, which is
    # bound after `execute_plan` and inside a roster guard. `repo_root` is passed
    # because without it `registry._merged` never runs `discover_local`, and every
    # project-local template resolves to `None` — which would empty `credentials`
    # and silently turn the redaction below into a no-op for exactly the templates
    # this check is for. Cannot raise: `validate_config` already made the same
    # call and returned without error, or `command_run` returned above.
    run_template = get_template(doc.get("experiment_type", ""), repo_root)
    # Every credential core read for a DECLARED variable — the template's own
    # `required_env`, plus the union its parameters' `requires_env` resolves to.
    # Held for this command only and written nowhere; its single consumer is the
    # redaction in `execute_plan` and — since a resolver runs below — a fresh
    # collector wrapping the roster call.
    credentials = credential_values(declared_credential_names(doc, run_template, conditions))

    # phase 5: roster. `technical_n` — `{min, max, median}` over the measurement
    # counts rows sharing a key collapsed from — travels to every metric block as
    # `summarize_step`'s `beside_n`, which is the route for a fact `reference.md`
    # shows *beside* `n` rather than inside it (`stats.summarize_step` states the
    # two-route rule and which document sentence decides each). `provenance.units`
    # is documented as exactly `{n, key}`, so parking it there would invent a
    # `run.yaml` field no document describes.
    resolver_io = ResolverIO(input_dir)
    try:
        roster, technical_n, _columns = (
            resolve_units(
                units_decl,
                input_dir,
                cfg=resolve_wide_cfg(doc, wide_swept_paths(doc.get("sweep") or {})),
                resolver_io=resolver_io,
            )
            if units_decl
            else (None, None, frozenset())
        )
    except BaseException as exc:
        # `main`'s handler prints `{exc}` with no collector in scope, and a
        # non-`PublishableError` never reaches it at all — it ends the command in
        # a traceback. A resolver's message can carry a credential it read, so the
        # raise is turned into a diagnostic here, through a collector holding the
        # values `redact` answers from. A FRESH collector rather than `c`, which
        # has already been rendered and printed above: appending to it would
        # re-print every earlier finding and inflate the counts line.
        #
        # `except BaseException`, not `Exception`: a resolver body calling
        # `sys.exit()` — or raising `KeyboardInterrupt`/another `BaseException`
        # directly — must still have its message redacted before it reaches
        # stderr. `KeyboardInterrupt` is re-raised rather than turned into a
        # diagnostic, so Ctrl-C still stops the command the ordinary way — but
        # as a FRESH, argument-less `KeyboardInterrupt`, `from None`: a real
        # Ctrl-C already carries no message, and this is what stops a resolver
        # body that constructed one carrying a credential (`KeyboardInterrupt(
        # "...secret...")`) from reaching Python's own uncaught-exception
        # printer, which prints an exception's `str()` same as any other.
        # `from None` suppresses the chain — plain `raise` re-raises the
        # ORIGINAL object, message and all.
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        roster_c = Collector()
        roster_c.credentials = credentials
        roster_code = exc.code if isinstance(exc, PublishableError) else "E-RESOLVER-RAISED"
        roster_c.error(roster_code, "data.units", str(exc))
        print(roster_c.render(), file=sys.stderr)
        return EXIT_WRONG
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
    # `beside_n` — the two routes `stats.summarize_step` describes. There is no
    # `clustered_by` sibling of `weighted_by` on a CONTRAST entry either, and here
    # the reason is not silence but a second disclosure: a contrast's `method`
    # already carries the `_clustered` suffix, which discloses the clustering by
    # itself, so a name naming the same attribute again would be a second
    # disclosure of one fact. The count is a new fact no `method` string carries,
    # so it travels on its own as `n_paired_clusters`.
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
    # Hoisted above the fold region (H3c-3 task 4, discharging H9a Ruling S).
    # The fold is drawn INSIDE the cells (`reference.md` § Group axes), and a
    # cell is an intersection of realized arms, so the axes have to be realized
    # before the basis `k` is bounded against and before the partition is drawn
    # — not after. The move resolves nothing new: `expand(doc)` already sits
    # above this whole region and `clusters` two lines up. `sweep_block` travels
    # with them because both read it; `swept_paths` does not, and stays beside
    # its own reader.
    sweep_block = doc.get("sweep") or {}
    # One frozenset of unit keys per condition that selects a group axis — `None`
    # for a design declaring none. Reachable now that task 17 retired
    # `E-SWEEP-GROUPS-UNSUPPORTED`: `tests/test_cli.py`'s
    # `test_a_group_axis_actually_narrows_end_to_end` exercises `execute_plan`'s
    # subset view through a real `command_run`.
    #
    # Gated on `selector_paths(sweep_block)`, not on `group_axes` itself: `expand`
    # already used `selector_paths` to decide which paths are group cells, so
    # `conditions` below carries `Condition.selectors` naming every axis
    # `selector_paths` names — regardless of whether that axis's `levels` also
    # satisfy `_resolved_group_axes`'s stricter all-`str` requirement, the same
    # requirement `validate._check_assign`'s own `by_attribute` branch applies
    # before it ever calls `arms_of`. Gating on `group_axes` instead would let an
    # axis this function skips but `selector_paths`/`expand` still treat as one
    # silently skip arm narrowing entirely. `by: ""` is the live case:
    # `isinstance(by, str)` accepts it, so `selector_paths` names `""` an axis
    # and `expand` renders conditions under it (`Condition.selectors == {""}`,
    # labels `=a`/`=b`), but this function's own `not axis` check (an empty
    # string is falsy) skips it — every condition on that axis would then get
    # the whole roster, exactly the outcome two declared arms exist to make
    # impossible. Gating on `selector_paths` instead means `arm_members` is
    # still called whenever `expand` treated the config as having a group axis,
    # so a resolution gap surfaces as `arm_members`'s own `KeyError` — a
    # caller-disagreement bug to see, not a config to silently accept — rather
    # than as a silently unnarrowed run.
    group_axes = _resolved_group_axes(units_decl, sweep_block, roster, digest, clusters)
    arm_members_map = (
        arm_members(group_axes, conditions)
        if selector_paths(sweep_block) and roster is not None
        else None
    )
    # The design's cells, realized once from the axes just above — `None` for a
    # design with no group axis at all. **A design with no group axis is one
    # cell holding the whole roster**, and composing that is this caller's job
    # rather than `units.cells_of`'s: that function takes no roster (see its
    # docstring), so `cells_of({})` is one cell holding *nothing*. `None` here
    # IS that composition — every reader below falls back to the roster-wide
    # answer rather than looping over a cell that holds no units.
    cells = cells_of(group_axes) if group_axes else None

    # `fold_basis` is what turns `{kind: fold, k: all}` into a real count and what
    # `_fold_k` checks a declared `k` against — the resolved roster's units, or its
    # clusters when `data.units.cluster_by` declares the units are not independent
    # draws, since a cluster is indivisible and leave-one-out is then
    # leave-one-*cluster*-out (`reference.md` § Validation, *Folds fit inside the
    # clusters* and *Leave-one-out is affordable*). `units.fold_basis` is the one
    # derivation, the same `validate` bounded `k` with, applied here to the roster
    # `run` re-resolves fresh rather than trusted from the earlier pass.
    #
    # **Under a cell structure the basis is the SMALLEST CELL's**, resolved by
    # `units.thinnest_cell` from the `cells` just above — because the fold is
    # drawn inside each cell, so the cell that cannot carry `k` is what makes
    # the declaration unaffordable. `cells is None` means no cell structure and
    # takes the roster-wide answer, which is the identical predicate
    # `validate_config` applies to its own `basis` local: `validate` bounding
    # `k` against one number while this draws against another is the drift
    # `fold_basis`' single derivation exists to prevent. The third caller of
    # `fold_basis` — `validate._check_resample`'s `limits.min_clusters`
    # denominator — asks a different question and stays roster-wide (Ruling LL,
    # and Decision 4's three-site table in
    # `docs/superpowers/specs/2026-08-25-folds-inside-cells-design.md`).
    fold_level_basis: int | None = None
    # The cell that basis was counted over, travelling with it so a refused `k`
    # names the declaration a reader must change. `None` means *no cells
    # resolved*; see `replication._fold_k`.
    fold_level_cell: tuple[tuple[str, str], ...] | None = None
    if roster is not None:
        if cells is not None:
            fold_level_basis, fold_level_cell = thinnest_cell(roster, cluster_by, cells)
        else:
            fold_level_basis = fold_basis(roster, cluster_by)
    levels = resolve_repeats(
        doc,
        digest,
        fold_basis=fold_level_basis,
        fold_cell=fold_level_cell,
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
        # belongs under is a property of the declaration being served.
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
        strata = _fold_strata(fold_level, roster)
        # Drawn INSIDE each cell when the design has one, merged index-wise
        # (`units.partition_within_cells`), and reducing to the identical single
        # whole-roster call with the bare digest when it does not — `cells` is
        # `None` for a design with no group axis, and `{}` is the input that
        # reduction answers. `partition_units` is still what draws, from inside
        # that function, so the count and the digest a no-axis run makes are
        # unchanged.
        #
        # **`partition_units` stays imported above, unused, with a `noqa`.**
        # H3c-3's guard-pin arm D installs a counting wrapper at BOTH
        # `cli.partition_units` and `units.partition_units` and asserts on the
        # sum, precisely so it survives this reroute — and it has no authorized
        # editor in the slice, so removing the name here would break a pin that
        # may not be repaired. The import is the pin's surface rather than a
        # leftover, which is why it is annotated rather than deleted.
        partitions = partition_within_cells(
            roster,
            fold_level.n,
            digest,
            cells or {},
            clusters=clusters,
            strata=strata,
        )
    fold_members = fold_members_for(levels, partitions) if partitions is not None else None

    swept_paths = wide_swept_paths(sweep_block)
    # Realized here, once, and before anything reads it — the runner's
    # narrowing, the denominators and `allocation.json` are all handed this one
    # object. See `_resolved_holdout` for why not calling twice is the only
    # thing that can promise the run and the record agree.
    holdout_plan = _resolved_holdout(units_decl, roster, digest, clusters, cells)
    # One narrowing, six readers. `roster` itself stays whole below this line —
    # `provenance.units.n` and `units_hash` are the roster's identity rather
    # than a metric's denominator, and rebinding the name would narrow every
    # future call site silently, including theirs.
    eval_roster = _evaluation_roster(roster, holdout_plan)
    # Checked here, before `execute_plan` spends anything: `_evaluation_roster`
    # returns `None` only when its own `roster` argument is `None`, so this
    # invariant either holds for free or is worth knowing about before the
    # first execution runs, not after — a crash once executions are already
    # paid for loses the record along with the money (see `4b1aebf`).
    assert (eval_roster is None) == (roster is None)
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

    # Built HERE and called HERE, not at the dirty gate: `resolve_units` above
    # runs a plugin resolver — user code that may create or remove files under
    # `src/**` — so an exclude answer captured before it ran would answer
    # "what did git see before user code ran", which is not the question this
    # hash asks. State read at the wrong moment is a proxy (H7a's corollary).
    # One call, folded once: `hashed_files` walks the two trees and asks git a
    # single `check-ignore` question, and `code_hash_of` folds the list it
    # returns, so neither the walk nor the subprocess happens twice. Which
    # files that leaves is docs/reference.md § How the three are computed's
    # four-case rule, stated there and not restated here.
    def _include(candidates: list[str]) -> set[str]:
        return unignored_under_hashed_trees(repo_root, candidates)

    hashed = hashed_files(repo_root, _include)
    # E-CODE-EMPTY, ONE emit site (H6a task 8, Ruling D): a record whose
    # `code_hash` is `sha256:e3b0c442…` — the digest of nothing — proves
    # nothing, and would otherwise be published, cited, and bundled with no
    # diagnostic. Written as `if not hashed:`, testing the FILE LIST rather
    # than comparing against the empty digest — `ch == "sha256:e3b0c442…"`
    # answers "were there zero files?" with a digest comparison, a proxy a
    # mutation swapping one for the other would pass every fixture in this
    # slice on. `hashes.code_hash` itself still returns the empty digest for
    # an empty tree: two tests in tests/test_hashes.py use exactly that value
    # as a negative control, so the refusal belongs at this caller, not
    # inside the pure hashing module. Reachable two ways — no file at all
    # under either tree, or every file under them git-excluded — both named
    # in docs/reference.md § Errors core raises' `E-CODE-EMPTY` row. Sits
    # after unit resolution (a resolver's quota may already be spent) and
    # before `allocate_run_dir` below, so a refusal here leaves no run
    # directory behind.
    if not hashed:
        empty_c = Collector()
        empty_c.error(
            "E-CODE-EMPTY",
            "src/** or templates/**",
            "no file found under either tree once git's exclude rules are "
            "applied; the run would otherwise publish sha256:e3b0c442… — "
            "the digest of nothing — as its code_hash",
        )
        print(empty_c.render())
        return EXIT_WRONG
    ch = code_hash_of(hashed)
    ph = parameters_hash(doc)
    manifest = build_manifest(
        input_dir,
        doc["data"]["input_manifest_policy"],
        index_names(units_decl or {}, roster, resolver_io.read_paths),
    )
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

    # H8a Decision 2: one `UpstreamResolver` and one `UpstreamLedger` for the
    # whole run, built from this config's own `output_dir` and the
    # `repo_root` already walked up from the config path — never from
    # `run_dir`, which is a proxy answering "where does *this* run sit", not
    # "where do this experiment's runs live" (§ The mutations, the one
    # dropped mutation). Built here, BEFORE `allocate_run_dir` below creates
    # `output_dir`, because `__init__` does no I/O and cannot raise: a first
    # run against a config whose `output_dir` holds no prior run, and does
    # not exist yet at all, must not fail at construction. The ledger
    # outlives every per-execution `StepIO` `execute_plan` constructs, so a
    # read from an execution that later fails is not lost with it.
    upstream_ledger = UpstreamLedger()
    upstream_resolver = UpstreamResolver(
        output_dir=output_dir, repo_root=repo_root, ledger=upstream_ledger
    )

    return Prepared(
        config_path=config_path,
        c=c,
        doc=doc,
        repo_root=repo_root,
        git=git,
        digest=digest,
        input_dir=input_dir,
        output_dir=output_dir,
        units_decl=units_decl,
        conditions=conditions,
        run_template=run_template,
        credentials=credentials,
        roster=roster,
        beside_n=beside_n,
        weight_by=weight_by,
        weights=weights,
        weighted_beside=weighted_beside,
        cluster_by=cluster_by,
        clusters=clusters,
        levels=levels,
        repeats=repeats,
        partitions=partitions,
        fold_members=fold_members,
        group_axes=group_axes,
        holdout_plan=holdout_plan,
        eval_roster=eval_roster,
        arm_members_map=arm_members_map,
        cells=cells,
        plan=plan,
        cfgs=cfgs,
        ch=ch,
        ph=ph,
        manifest=manifest,
        lock_path=lock_path,
        lock_hash=lock_hash,
        upstream_ledger=upstream_ledger,
        upstream_resolver=upstream_resolver,
    )


def _recorded_config_path(config_path: Path, repo_root: Path) -> str:
    """`config_path` relative to `repo_root`, POSIX-separated, for
    `identity.json`.

    Relative and not absolute because a run directory may be read on a
    machine where the repository sits somewhere else, and POSIX-separated
    because the recorded name is a name rather than a local path.

    The fallback records the absolute path. It is a fallback and not a
    promise: `repo_root` is `find_repo_root(config_path)`'s answer, a WALK-UP
    from the config itself, so a config outside its own repo root is not a
    state this function can be handed by `_prepare_run`. An absolute recorded
    path is refused on read (`run_identity.config_path_for`), so a directory
    that somehow carried one refuses with `E-RESUME-NO-CONFIG` rather than
    resolving something unrelated.
    """
    resolved = config_path.resolve()
    try:
        return resolved.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _execute_prepared(prepared: Prepared, *, draft: bool, resumed: Resumed | None = None) -> int:
    """Phases 6-10 of a run: allocate the run directory, execute, record.

    Takes what `_prepare_run` pinned and nothing else, so that `run`, `draft`
    and (H9b) `resume` are three entries into ONE execution path rather than
    three copies of it.

    The names are read off `prepared` in one unpack block rather than as
    attribute accesses scattered through the body, which is what made the
    original move of this 1,495-line body out of `command_run` mechanically
    checkable. `c` is the one field not unpacked: no statement below reads it
    (see `Prepared`), and a local nothing reads is an `F841`.

    `draft` is accepted here and reaches `assemble_run_yaml` in task 3, which
    owns the `draft` command, its fixture Q and the mutation that catches the
    wiring. It is threaded now rather than added later so that `command_draft`
    is one call and not a second copy of this function.

    `resumed` is `None` for `run` and `draft`, and every line below behaves as
    it did before it existed (H9b Decision 14: one execution path, not a
    third copy of it). It is accepted at THIS signature and deliberately not
    threaded through the unpack block above (plan § Corrections against the
    code, correction 19): what reads it is the handful of phase-6 sites, the
    `execute_plan` call, and the run-start containment that publishes a record
    for a resume whose apparatus moved — and nothing else. The
    byte-identical-to-`command_run` claim this paragraph used to make is
    deleted rather than restated: it stopped being true when the `resumed`
    branches landed, and a weaker version of it would be a sentence nobody can
    check.
    """
    config_path = prepared.config_path
    doc = prepared.doc
    repo_root = prepared.repo_root
    git = prepared.git
    digest = prepared.digest
    input_dir = prepared.input_dir
    output_dir = prepared.output_dir
    units_decl = prepared.units_decl
    conditions = prepared.conditions
    run_template = prepared.run_template
    credentials = prepared.credentials
    roster = prepared.roster
    beside_n = prepared.beside_n
    weight_by = prepared.weight_by
    weights = prepared.weights
    weighted_beside = prepared.weighted_beside
    cluster_by = prepared.cluster_by
    clusters = prepared.clusters
    levels = prepared.levels
    repeats = prepared.repeats
    partitions = prepared.partitions
    fold_members = prepared.fold_members
    group_axes = prepared.group_axes
    holdout_plan = prepared.holdout_plan
    eval_roster = prepared.eval_roster
    arm_members_map = prepared.arm_members_map
    plan = prepared.plan
    cfgs = prepared.cfgs
    ch = prepared.ch
    ph = prepared.ph
    manifest = prepared.manifest
    lock_path = prepared.lock_path
    lock_hash = prepared.lock_hash
    upstream_ledger = prepared.upstream_ledger
    upstream_resolver = prepared.upstream_resolver
    cells = prepared.cells

    # phase 6: the run directory. `resume` re-enters an EXISTING one, which is
    # why `E-RUN-ID-EXHAUSTED` is unreachable from it — it allocates nothing.
    if resumed is not None:
        run_dir = resumed.run_dir
        # `manifest` is the RECORDED manifest from here down (Decision 8), so
        # phase 8's `verify_manifest` asks whether the inputs moved during
        # THIS attempt rather than comparing now against now, and
        # `run.yaml`'s `input_manifest_hash` is the first attempt's figure.
        manifest = resumed.recorded_manifest
    else:
        run_dir = allocate_run_dir(output_dir, ch, datetime.now(UTC))
    # The lock is taken here for BOTH entries, unchanged. `resume`'s takeover
    # of a dead holder's `lock` — Ruling W's exclusive token, the liveness
    # test, and the unlink — is plan task 14's and happens before
    # `_execute_prepared` is called at all; this acquisition is what task 14's
    # step 4 ends with, and it stays the only claim in the system.
    with RunLock(run_dir):
        # Every run-start artifact below is skipped on a resume: they were
        # written before the first execution and `docs/reference.md` § The
        # other files a run writes calls them "settled before the first
        # execution and never touched again". Rewriting one would replace a
        # record of what the first attempt did with a record of what this
        # attempt recomputed — and `identity.json` in particular is what
        # `resume` just compared itself against.
        if resumed is None:
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

            # `freeze` (H8b) needs the config as it was and the repo it came from — the
            # two facts a mid-run command cannot otherwise obtain or compute, since
            # `run.yaml` embeds the config only once, at the end. A byte copy, never a
            # re-dump: a re-dump would silently drop every comment `init` wrote.
            (run_dir / "config.yaml").write_bytes(config_path.read_bytes())
            (run_dir / "environment" / "repo_root.txt").write_text(f"{repo_root}\n")

            # `identity.json` — the three identity figures, the config's own path,
            # and whether this is a draft, made durable BEFORE anything executes,
            # because `resume` compares against them and a crashed run directory
            # holds no `run.yaml` to read them from (design Decision 1). Written
            # here rather than later for the same reason `config.yaml` and
            # `repo_root.txt` are: inside the lock, before `sweep.yaml`, settled
            # before the first execution and never touched again. Every figure is
            # `Prepared`'s own -- a second derivation would be a second answer.
            (run_dir / IDENTITY_FILE).write_text(
                json.dumps(
                    identity_document(
                        code_hash=ch,
                        parameters_hash=ph,
                        uv_lock_hash=lock_hash,
                        config_path_rel=_recorded_config_path(config_path, repo_root),
                        draft=draft,
                    ),
                    indent=2,
                )
            )

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
        #
        # On a RESUME the order comes from `sweep.yaml` and never from a
        # second realization (Decision 9, task 10): `resumed.execution_order`
        # is the recorded sequence when the recorded `order` was
        # `randomized`, and `None` when it was `as_declared` — the same
        # two-branch decision as above, taken from the record because the
        # record is what the first attempt actually ran. Re-realizing instead
        # agrees for an unedited file (`order_seed_for` is a pure function of
        # the design digest) and disagrees for exactly the case the reader
        # exists for: a recorded order this seed does not reproduce, which
        # under a `batch` level would open batch 4 while batch 3 still had
        # executions outstanding.
        if resumed is not None:
            if resumed.execution_order is not None:
                plan = _apply_execution_order(plan, list(resumed.execution_order))
        elif mode == "randomized":
            plan = _apply_execution_order(plan, execution_order)

        # Written by the FIRST attempt only, and read back by the branch above
        # rather than re-derived (Decision 9).
        if resumed is None:
            # `partitions_within` — the axes the folds were drawn inside, when
            # they were. The predicate is `units.populated_cells`', the same
            # list `partition_within_cells` loops over and reduces on, called
            # rather than re-spelled: a second spelling here is a record
            # claiming a draw that did not happen. The axis NAMES come from a
            # populated cell's own key, which is what was handed to the draw,
            # rather than from `group_axes` — every key carries the same axes
            # in the same order, `cells_of` building them from one product.
            populated = populated_cells(cells or {})
            partitions_within = [axis for axis, _ in populated[0][0]] if populated else None
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
                        partitions_within=partitions_within,
                        sample_seed=sample_seed_for(doc),
                    ),
                    sort_keys=False,
                )
            )

        # `allocation.json` — settled beside `sweep.yaml`, before the first
        # execution and never touched again, per § The other files a run
        # writes: both are partitions of one roster drawn once. `None` only
        # when NEITHER partition resolved — no arm assignment and no
        # `data.units.holdout` — matching "present when either is declared".
        # `holdout_plan` is `_resolved_holdout`'s single realization, the same
        # object the runner narrowed and the denominators counted against, so
        # the membership this file claims is the membership the run used rather
        # than a second draw that happens to agree.
        #
        # `group_axes` — the same object `arm_members` narrowed every
        # condition's roster with above, not a second resolution of the same
        # declaration. `build_allocation_document` used to be handed the roster
        # and re-derive the partition through `arms_of`; under a drawn method
        # that second derivation is a second draw, so the plans are realized
        # once (`_resolved_group_axes`) and recorded as realized. No roster
        # guard is needed here either: `_resolved_group_axes` already returns
        # `{}` when none resolved, and the empty mapping is what makes this
        # `None`.
        alloc_doc = build_allocation_document(group_axes, holdout_plan)
        alloc_hash: str | None = None
        if alloc_doc is not None:
            # The WRITE is the first attempt's; the hash is computed either
            # way, because `provenance.allocation_hash` is a figure this
            # attempt's record carries. On a resume the memberships this
            # document is rebuilt from were themselves READ from the file
            # (`_resumed_allocation`, Decision 10), so the document rebuilt
            # here equals the one on disk and the hash covers it — a
            # re-derivation would agree for a by-attribute axis and be a
            # second draw for a drawn one.
            if resumed is None:
                (run_dir / "allocation.json").write_text(json.dumps(alloc_doc, indent=2))
            alloc_hash = allocation_hash(alloc_doc)

        # `apparatus_probe` declared on the resolved template — the ordinary
        # case declares none, and `observer` stays `None` so every downstream
        # call site (`Observer.observe_round`'s run-start round, and
        # `execute_plan`'s per-execution round, task 10) is a no-op guarded on
        # that, not on a property of `Observer` itself.
        declared_probe = getattr(run_template, "apparatus_probe", None)
        observer: apparatus.Observer | None = None
        if isinstance(declared_probe, str) and declared_probe:
            # `apparatus._probe_for` is the same three-step dispatch a
            # resolver name goes through, and its middle step
            # (`load_entry_point`) imports a plugin's top level — user code —
            # exactly as `units._resolver_for` does for a resolver.
            # `validate._check_probe` answers only `E-PROBE-UNKNOWN` from
            # package metadata and never loads anything, so a load-time
            # failure (`E-PLUGIN-LOAD`, `E-PLUGIN-DECORATOR`) gets no verdict
            # from `validate` at all and can carry a credential the plugin's
            # own import-time body read — this wrapper is the roster
            # wrapper's own shape (`except BaseException`, `KeyboardInterrupt`
            # re-raised fresh and argument-less, a FRESH credential-bearing
            # `Collector`), for the identical reason.
            try:
                probe_fn = apparatus._probe_for(declared_probe)
            except BaseException as exc:
                if isinstance(exc, KeyboardInterrupt):
                    raise KeyboardInterrupt from None
                dispatch_c = Collector()
                dispatch_c.credentials = credentials
                dispatch_code = exc.code if isinstance(exc, PublishableError) else "E-PLUGIN-LOAD"
                dispatch_c.error(dispatch_code, "experiment_type", str(exc))
                print(dispatch_c.render(), file=sys.stderr)
                return EXIT_WRONG
            # H9c task 9 (Ruling BB): the recorded expectation, when the
            # CONFIG'S OWN DIRECTORY holds an `apparatus.expected.json` —
            # § Reproducing on another device's own location, which `reproduce`
            # writes and a reader may edit.
            #
            # **It is outside `src/**` and `templates/**`, so neither
            # `code_hash` nor the dirty gate sees it — and the ground is a
            # MEASUREMENT rather than the pathspec.** Measured on a real run:
            # an untracked `uv.lock` at a repo root left
            # `git status --porcelain` reading `?? uv.lock` while the run
            # exited `0`, because the gate reads
            # `git status --porcelain -- src templates`. Reasoning from the
            # pathspec alone would be answering with a proxy.
            #
            # Read only when a probe is declared: with no probe there is
            # nothing to compare, `observer` stays `None`, and a stray file is
            # inert exactly as it is today. `expectation_from`'s refusal is
            # contained here rather than raised, on the same shape and for the
            # same reason as `_probe_for`'s wrapper above — `main`'s
            # `PublishableError` handler applies no redaction pass.
            expected: apparatus.Observations | None = None
            expected_path = config_path.parent / "apparatus.expected.json"
            if expected_path.is_file():
                try:
                    expected = apparatus.expectation_from(expected_path)
                except ContractError as exc:
                    expectation_c = Collector()
                    expectation_c.credentials = credentials
                    expectation_c.error(exc.code or "E-IO-FAILED", str(expected_path), str(exc))
                    print(expectation_c.render(), file=sys.stderr)
                    return EXIT_WRONG
            observer = apparatus.Observer(
                probe_name=declared_probe,
                probe=probe_fn,
                declared_facts=list(getattr(run_template, "apparatus_facts", None) or []),
                conditions=conditions,
                cfgs=cfgs,
                run_dir=run_dir,
                credentials=credentials,
                # On a resume, the ORIGINAL run's first-answered facts
                # (Decision 11), replayed from `apparatus/probes.jsonl` by
                # `command_resume`. Without this the resumed run's own first
                # probe would become the baseline — retiring the apparatus
                # gate for the whole remainder of the run, which is the one
                # guard that stops a run being measured through two different
                # apparatus states. `None` for `run` and `draft`, which is
                # the keyword's shipped default and what `freeze` already
                # uses one branch over.
                observations=None if resumed is None else resumed.baseline,
                # A SECOND `Observations`, never merged into the run's own:
                # `record` bumps `_total_counts`/`_null_counts`, which feed
                # `provenance.apparatus.unobserved` and
                # `W-APPARATUS-UNANSWERED`, so seeding the run's own object
                # from a foreign record would make this record claim probe
                # calls it never made (H9c plan correction 11).
                expected=expected,
            )

        # Bound BEFORE the `try` below, not inside it: the run-start round can
        # raise, and the branch that then writes a record (H9b task 16) reads
        # both. Two assignments, neither of which can fail, moved for that
        # reason alone — `full_plan` is still `plan` as it stands before the
        # resumed filter narrows it, which is what `run_status`'s `planned=`
        # means on both entries.
        stop = StopSignal()
        full_plan = plan
        try:
            # The run-start round: one probe call per resolved condition,
            # before the first execution (Decision 2). `sweep.yaml` and
            # `allocation.json` are already on disk; `run.yaml` is not, so a
            # probe failure here leaves the same shape any other pre-`run.yaml`
            # failure already leaves — no `run.yaml`, everything before it.
            if observer is not None:
                observer.observe_round(phase=apparatus.PHASE_RUN_START, condition_index=None)
            # H7d Part B, Decision 3/Decision 5: one `StopSignal` per run,
            # shared by `execute_plan`'s apparatus gate and its
            # `max_failed_fraction` guard. `run_status` below reads
            # `stop.reason` rather than re-deriving why the plan came up
            # short.
            # The plan `run_status` is measured against is the WHOLE plan, on
            # both entries: `full_plan` below is what `planned=` gets, and
            # `plan` is what actually executes. On a resume the two differ by
            # exactly the triples that already completed, and the difference
            # is what `resumed.prior_results` puts back — so the bare
            # `assert len(results) >= planned` in `run_status` is satisfied
            # BY CONSTRUCTION rather than relaxed (Decision 6), and its
            # docstring's claim that a short list with no recorded stop
            # reason is a core defect stays true of `resume` too.
            if resumed is not None:
                already = {
                    (r.execution.step_name, r.execution.condition_index, r.execution.repeat_label)
                    for r in resumed.prior_results
                }
                plan = [
                    e
                    for e in plan
                    if (e.step_name, e.condition_index, e.repeat_label) not in already
                ]
            results = execute_plan(  # phase 7
                plan=plan,
                run_dir=run_dir,
                input_dir=input_dir,
                cfgs=cfgs,
                repeats=repeats,
                digest=digest,
                units=eval_roster,
                max_failed_fraction=(doc.get("limits") or {}).get("max_failed_fraction"),
                fold_members=fold_members,
                arm_members=arm_members_map,
                holdout_train=(
                    UnitList([u for u in roster if u.key in set(holdout_plan.train)])
                    if holdout_plan is not None and roster is not None
                    else None
                ),
                measurements=(units_decl or {}).get("measurements"),
                credentials=credentials,
                observer=observer,
                stop=stop,
                upstream=upstream_resolver,
            )
        except ContractError as exc:
            # The one containment site for a probe CALL's raise (a dispatch
            # failure is resolved, and redacted, by `apparatus._probe_for`'s
            # own `try/except` just before `observer` is built — that site
            # never reaches this `try` at all): `main`'s own `PublishableError`
            # handler prints `{exc}` with no collector in scope, so anything
            # reaching it is un-redacted. Filtered to
            # `apparatus.APPARATUS_CODES` UNION `apparatus.STOP_CODES` — every
            # other `ContractError` out of this block (`E-RUN-CFG-MISSING`,
            # `E-RUN-SEED-MISSING`) keeps escaping exactly as it does today;
            # this slice does not change how core's own inconsistencies are
            # reported.
            #
            # `E-APPARATUS-CHANGED` is deliberately not a member of
            # `APPARATUS_CODES` itself (plan correction 4: that frozenset is
            # `_probe_for`'s dispatch-time filter, and admitting an unpinned
            # member there is the thing this project has already been burned
            # by). `apparatus.STOP_CODES` is unioned in here too, and **H9b
            # task 13 made one of its members reachable**: this comment used
            # to say no path reaches this `try` carrying either, which was
            # true only while every run-start round started from an EMPTY
            # baseline. A RESUME starts from the previous attempt's replayed
            # baseline (H9b Decision 11), so its run-start round HAS a prior
            # observation to disagree with, and a fact that moved while the
            # run was down raises `E-APPARATUS-CHANGED` here. Measured, and
            # pinned by `test_h9b_a_resume_gates_against_the_original_runs_
            # first_answered_fact`. A mid-plan raise of either code still
            # `break`s inside `execute_plan` (H7d task 5/6) rather than
            # escaping, and `E-APPARATUS-RAISED` at run-start reaches this
            # branch through `APPARATUS_CODES` alone — so the union is now
            # load-bearing rather than cheap insurance: narrowing this filter
            # to `APPARATUS_CODES` fails that test (measured again at task 16,
            # full suite), because the raise escapes this containment — and
            # since task 16 that also loses the RECORD, not only the
            # redaction: the branch below writes `run.yaml` for a resume whose
            # apparatus moved, and it is inside this `except`.
            # The shipped comment's own "narrowing this filter leaves the
            # full suite unchanged" was true when it was written and is not
            # true now.
            if exc.code not in apparatus.APPARATUS_CODES and exc.code not in apparatus.STOP_CODES:
                raise
            # **H9b task 16: a resume whose apparatus MOVED while the run was
            # down publishes what the run already did.** Task 13 made this
            # state reachable and measured the cost: the raise above returned
            # an exit code with no `run.yaml`, and — because the fact stays
            # moved — every later `resume` returned the same, so every
            # completed execution stayed on disk, paid for and unpublishable.
            # *Every execution paid for, the record lost* is the most
            # expensive defect class in this repository's own habits list, and
            # a stop that discards work already done is worse than the change
            # it protects against.
            #
            # So this does not return: it records the stop on the shared
            # `StopSignal` — the same three fields `execute_plan`'s own
            # apparatus gate sets for a MID-PLAN move — and falls through with
            # NO new results, into the one path that prints the stop, folds
            # the reconstituted results back in, aggregates them and writes
            # `run.yaml`. H7d Part B's precedent decides the shape: a changed
            # fact fails the run **and the ledger keeps the moving observation
            # so a stop is legible from the artifacts** (`_observe_one`
            # appends before the gate, which is why the moved value is on disk
            # even here). The record then names that ledger through
            # `provenance.apparatus.ledger`, and `provenance.apparatus.facts`
            # carries the ORIGINAL run's first-answered values, because those
            # are the facts the results were measured through.
            #
            # **The exit code is 4, and it is neither of the two the brief
            # named.** § Exit codes gives `1` to *"a changed apparatus fact
            # caught before the first execution ran, which leaves nothing to
            # mark `failed` at all"* — a qualifying clause that is exactly
            # false here, since the prior attempt's executions are what there
            # is to mark. `5` is the class you retry and belongs to an
            # UNREACHABLE apparatus, not a moved fact. `4` is *"the run
            # stopped: `status: failed`. There is a record of what happened"*,
            # and its row already reads **`run`, `draft`, `resume` only**. The
            # code is not chosen here at all: `run_status` maps
            # `apparatus_changed` to `failed` and the final mapping maps
            # `failed` to `EXIT_FAILED`, which is the same answer H7d Part B
            # gives a mid-plan move that completed at least one execution.
            #
            # **The cost, stated rather than hidden**: `run.yaml` ends the
            # run, so `E-RESUME-RUN-ENDED` refuses every later `resume` of
            # this directory. That is correct for a MOVED fact and only for
            # one — the apparatus cannot move back, so no later resume could
            # ever pass the gate, and the choice is between a published
            # partial record and none. An UNREACHABLE apparatus is the
            # opposite case (bring it back and resume again), so it keeps
            # today's behaviour and is filed in `spec-defects.md` with that
            # terminality as the reason rather than folded in here.
            # **H9c task 9: `E-APPARATUS-UNEXPECTED` joins this branch, and the
            # ground is that the two sites must ALREADY agree.** `execute_plan`
            # maps every non-`E-APPARATUS-RAISED` `STOP_CODES` member to
            # `stop.reason = "apparatus_changed"` for a MID-PLAN raise, so a
            # resume whose apparatus contradicts `apparatus.expected.json`
            # mid-plan already publishes what the prior attempt did. Only the
            # RUN-START copy of the same question branched on the code by name,
            # and the asymmetry cost the whole record: measured, on a crash
            # leaving 2 completed executions on disk, a resume whose run-start
            # round answered a fact the expectation contradicts returned exit
            # `1` with NO `run.yaml`, and — the fact still contradicting — every
            # later resume returned the same. *Every execution paid for, the
            # record lost* is verbatim what H9b task 16 fixed here for the
            # sibling code, and this is the same defect reached through the code
            # added beside it.
            #
            # **No vocabulary is added and no code is minted.** `stop.reason`
            # stays the closed set of three `run_status` documents, and it is
            # `"apparatus_changed"` for exactly the reason `execute_plan`
            # already uses it for this code; the reader is told which fault
            # occurred by `stop.code`/`stop.message`, which carry
            # `E-APPARATUS-UNEXPECTED` verbatim into the printed diagnostic. The
            # exit code is `4` from `run_status`'s shipped fold, which is also
            # what design Decision 4 says it should be — *"`1` before the first
            # execution and `4` once there are results"* — so widening this is
            # what makes the code answer the design rather than a change to it.
            if (
                exc.code in ("E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED")
                and resumed is not None
                and resumed.prior_results
            ):
                stop.reason = "apparatus_changed"
                stop.code = exc.code
                stop.message = str(exc)
                # Nothing executed this attempt. The stop block below prints
                # the diagnostic — the same code and message, through the same
                # fresh credential-bearing `Collector` — so printing here too
                # would print it twice.
                results = []
            else:
                probe_c = Collector()
                # A FRESH collector: `c` was already rendered and printed above,
                # so appending to it would re-print every earlier finding and
                # inflate the counts line — the roster path's own shape.
                # `credentials` reused, never recomputed: a second derivation is a
                # second answer.
                probe_c.credentials = credentials
                probe_c.error(exc.code, "experiment_type", str(exc))
                print(probe_c.render(), file=sys.stderr)
                # H7d Part B task 8 (Decision 6): `E-APPARATUS-RAISED` — the
                # apparatus itself unreachable — is the one code in this
                # containment's filter that earns exit 5. The four Decision 9
                # contract refusals from `APPARATUS_CODES`
                # (`E-APPARATUS-FACT-TYPE`, `-FACT-MISSING`, `-FACT-CREDENTIAL`,
                # `-RETURN`) keep `EXIT_WRONG`. **A resume's run-start
                # `E-APPARATUS-CHANGED` no longer reaches this branch when the
                # prior attempt completed anything** — that is the record-write
                # branch above, at exit `4` — and it still reaches it when the
                # prior attempt completed nothing, where `1` is § Exit codes'
                # own answer: *a changed fact caught before the first execution
                # ran, which leaves nothing to mark `failed` at all*. An
                # UNREACHABLE apparatus on a resume also still returns here, at
                # `5`, deliberately: `run.yaml` would end the run, and that
                # fault is the one an operator can undo.
                if exc.code == "E-APPARATUS-RAISED":
                    return EXIT_EXTERNAL
                return EXIT_WRONG

        # H7d Part B task 7 (Decision 4, Decision 14): a stop is printed
        # here, before the aggregate phase, so the reason a run stopped is
        # on the operator's screen before any later phase that can itself
        # fail. Gated on the two apparatus reasons only — a
        # `max_failed_fraction` stop prints nothing, exactly as today
        # (Fixture T's arms assert the absence).
        #
        # A FRESH `Collector`: `c` was already rendered and printed above,
        # so appending to it would re-print every earlier finding and
        # inflate the counts line — the same reason the probe-dispatch and
        # run-start containment branches above each build their own.
        # `credentials` reused, never recomputed.
        if stop.reason in ("apparatus_unreachable", "apparatus_changed"):
            # `stop.code`/`stop.message` are set together with `stop.reason`
            # at every site that sets any of the three — `execute_plan`'s
            # apparatus gate, and (H9b task 16) the run-start containment
            # above, for a resume whose apparatus moved. The assert states
            # that contract rather than silently narrowing `str | None` to
            # `str`.
            assert stop.code is not None and stop.message is not None, (
                "a stop reason of one of the two apparatus kinds always sets "
                "`code` and `message` alongside it"
            )
            stop_c = Collector()
            stop_c.credentials = credentials
            stop_c.error(stop.code, "experiment_type", stop.message)
            print(stop_c.render(), file=sys.stderr)
            # Decision 4: with NO results, nothing was paid for, and the
            # command keeps Part A's shape — no `run.yaml`, `latest`
            # untouched. **"No results" now means neither this attempt's nor a
            # prior attempt's** (H9b task 16): on a resume the ground the
            # sentence rests on — nothing was paid for — is false whenever
            # `resumed.prior_results` is non-empty, and returning here is what
            # made a moved apparatus lose every completed execution's record.
            # For `run` and `draft` the condition is unchanged, `resumed` being
            # `None`. This must be sited before `assemble_run_yaml` AND
            # before `point_latest` (batch 4's Major 1): both, not one.
            # Decision 4's table gives zero-results TWO different exit
            # codes, not one: `moved` is `1` (the thing you asked about is
            # wrong), `unreachable` is `5` (the class you retry) — the same
            # split Decision 6 gives the `>= 1`-results rows. Branching on
            # `stop.reason` here is what task 8's review found missing
            # (Major 1): the run-start containment above and the final
            # mapping below are both off this path, since a zero-results
            # mid-plan stop returns right here.
            if not results and (resumed is None or not resumed.prior_results):
                if stop.reason == "apparatus_unreachable":
                    return EXIT_EXTERNAL
                return EXIT_WRONG

        attempts: dict[tuple[str, int | None, str | None], int] | None = None
        if resumed is not None:
            # `attempts` is the number of records a triple holds in
            # `executions.jsonl` (§ Resuming). `resumed.attempts` is that
            # count as of RE-ENTRY, so every triple this attempt executed
            # needs its own line added: `execute_plan` appends exactly one
            # line per `ExecutionResult`, in the same loop iteration that
            # builds it, unconditionally and whatever the status — including
            # the iteration a `max_failed_fraction` `break` ends, whose write
            # precedes the `break`. So this is one-for-one with what is on
            # disk rather than an estimate of it, and it is computed BEFORE
            # the prior results are prepended, since those triples wrote no
            # line this time.
            attempts = dict(resumed.attempts)
            for executed in results:
                # `attempt_key`, not `key`: this function's body binds `key`
                # twice further down at `str`, and reusing the name here is
                # what `mypy` caught rather than what a reader would.
                attempt_key = (
                    executed.execution.step_name,
                    executed.execution.condition_index,
                    executed.execution.repeat_label,
                )
                attempts[attempt_key] = attempts.get(attempt_key, 0) + 1
            # Prepended, never appended: the aggregate phase and
            # `_execution_block` both read this list in order, and the
            # reconstituted triples ran FIRST. A list rather than a tuple
            # because `results` is a `list` on every other path and this
            # line must not change what phases 8-10 receive.
            results = list(resumed.prior_results) + results
        status = run_status(results, planned=len(full_plan), stop=stop.reason)
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
        aggregate_c.credentials = credentials
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
        # A `run`- or `condition`-scoped step's return has nowhere to land, and
        # § Step scope says so — but core knows at the moment it discards one,
        # and said nothing. That silence is the defect this warning closes: the
        # refusal is a STATISTICAL guard ("a number with no denominator in the
        # record is the mistake this refusal exists to prevent"), and a
        # statistical guard that fires without saying so leaves an author
        # believing a value was recorded when the record is indistinguishable
        # from one where the step returned `{}`.
        #
        # **Non-empty only.** An empty mapping is the honest "nothing to
        # report" and is what a wide step that means it already returns, so
        # warning on it would fire on every correct pipeline in existence. The
        # distinction needs nothing from the author: a value they computed and
        # core dropped is exactly a non-empty return at these two scopes.
        #
        # Reported once per (step, scope) rather than once per execution: a
        # condition-scoped step returns once per condition, and nine identical
        # warnings for one mistake is the noise that teaches a reader to skip
        # the whole channel. The keys are unioned across those executions so
        # the message names everything dropped, not whatever the first one held.
        discarded: dict[tuple[str, str], list[str]] = {}
        for r in results:
            if r.execution.scope not in ("run", "condition") or not r.returned:
                continue
            seen = discarded.setdefault((r.execution.step_name, r.execution.scope), [])
            for key in r.returned:
                if key not in seen:
                    seen.append(key)
        for (step_name, scope), dropped_keys in discarded.items():
            aggregate_c.warn(
                "W-STEP-RETURN-DISCARDED",
                step_name,
                f"is `{scope}`-scoped and returned {', '.join(dropped_keys)}, which core "
                f"discards: a metric is keyed by unit or reported per repeat, and "
                f"`{scope}` scope has neither. Use `io.write` for what a wide step "
                f"produces, and let a narrower step record what it measures; return "
                f"`{{}}` if the value was not meant for the record",
            )
        if roster is not None:
            # Already checked once, before `execute_plan`, where a failure
            # would still cost nothing run. Restated here only for the type
            # checker, which cannot see across that earlier `assert`.
            assert eval_roster is not None
            # `condition_index` is guarded per condition: core aggregates within
            # each condition and never pools across conditions — an unguarded
            # filter would let a same-named step from another condition mark this
            # one as having a recording step it never ran.
            template = get_template(doc.get("experiment_type", ""), repo_root)
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
            # `statistics.resample` is resolved ONCE here (H4a task 13) rather
            # than at each read site, so the record and the arithmetic cannot
            # come to disagree by two sites resolving the same declaration
            # independently. `resample_spec["n"]` is threaded below to the six
            # existing `derived_metric_draws` sites, unchanged from before
            # task 13. `resample_spec["declared"]` gates `summarize_step`'s
            # `resample_columns` at the primary call below (H4a task 14): a
            # declared `resample` is what turns a recorded column's interval
            # from `t_over_units` into `percentile_over_units`, not `n` on its
            # own — a config asking for exactly 2000 draws and a config asking
            # for nothing both resolve to `n: 2000`. `method` stays unread
            # (`validate.RESAMPLE_METHODS` is `("bootstrap",)` only, so there
            # is nothing yet to choose between).
            resample_spec = _resolved_resample(doc)
            derived_metric_draws = resample_spec["n"]
            # `_resolved_null_test`'s counterpart to `resample_spec`, resolved
            # once here for the same reason. `level` is filled in here rather
            # than inside that function, because `units.null_test_level` needs
            # the roster and `_resolved_null_test` does not have one — this is
            # the one place both the declaration and the roster are in scope.
            null_test_spec = _resolved_null_test(doc)
            if null_test_spec is not None and null_test_spec["shuffle"] is not None:
                # `null_test_level`'s domain is a roster ATTRIBUTE, never a bare
                # `sweep.groups` axis name — passing an axis-only name would
                # fail open (every unit renders "no value", every cluster reads
                # constant). This call is safe without re-deriving that check:
                # `validate._check_null_test` already refuses an axis-only
                # `shuffle` beside a declared `cluster_by` (`E-STATS-NULLTEST-
                # LEVEL`), and `validate` gates every `run` this call executes
                # inside of. An axis-only name with no `cluster_by` is also
                # safe on its own — `null_test_level` returns `("rows", None)`
                # before reading any attribute when `cluster_by` is falsy.
                level, _ = null_test_level(eval_roster, cluster_by, null_test_spec["shuffle"])
                null_test_spec["level"] = level
            # The per-condition derived-metric home (task 20) is the OTHER
            # `shuffle` domain from the contrast-side one (task 19): that one
            # fires only when `shuffle` names a `sweep.groups` axis a
            # comparison crosses, and this one only when it names an ORDINARY
            # attribute — the two are mutually exclusive gates over the same
            # resolved declaration, never both at once for one `null_test`.
            group_axis_names = {
                g.get("by")
                for g in (doc.get("sweep") or {}).get("groups") or []
                if isinstance(g, dict)
            }
            derived_null_test = (
                null_test_spec
                if null_test_spec is not None
                and null_test_spec["shuffle"] is not None
                and null_test_spec["shuffle"] not in group_axis_names
                else None
            )
            # Roster-wide, the same `unit_attributes` shape below is built at,
            # so a unit's label survives even when this condition's `collapsed`
            # is a proper subset of the roster — `permutation_of_derived`
            # indexes every key in `collapsed` and a `KeyError` there would be
            # this mapping's fault, not that function's.
            null_labels = (
                {u.key: str(u.attributes.get(derived_null_test["shuffle"])) for u in eval_roster}
                if derived_null_test is not None
                else None
            )
            # The resolved block, beside the interval rather than joining `n` —
            # `summarize_step`'s own rule for which carrier a fact takes, and
            # `weighted_by` is the precedent: a key that names a declaration
            # rather than reporting a figure. § Statistical reporting requires
            # it be recorded "so the number is never the result of an
            # undocumented default".
            #
            # ABSENT when nothing was declared, not null: a null would claim a
            # resolution was performed. `stratify_by` is materialized as a list
            # even where the config wrote a bare string, because the record
            # resolves what the config abbreviates — the same rule `of`/`against`
            # follow in `results.contrasts`.
            #
            # `n` here is what was REQUESTED; `resample_draws` beside it is what
            # the interval rests on. Equal for a column by construction and
            # different for a derived metric whenever a draw was degenerate,
            # which is what `W-STATS-RESAMPLE-THIN` reports.
            resample_beside = (
                {
                    "resample": {
                        "method": resample_spec["method"],
                        "n": resample_spec["n"],
                        "stratify_by": list(resample_spec["stratify_by"]),
                    }
                }
                if resample_spec["declared"]
                else {}
            )
            # Merged into `weighted_beside` here, not left for the report_by
            # level call to add on its own: the declaration is true of the run
            # either way, the same argument already made for `weighted_by`
            # above — a stratum's own units were resampled under the same
            # declared `resample` as the whole roster.
            weighted_beside.update(resample_beside)
            # `_comparison_step_blocks`' own `resample_echo` parameter — the
            # same resolved dict, threaded a second route because a contrast
            # entry is built by `_comparison_step_blocks`, not by
            # `summarize_step`'s `beside_n` (`spec-defects.md`'s "the contrast
            # path discloses nothing about its resample", Finding 3). `None`,
            # not `{}`, when nothing is declared, so the callee's own
            # absent-not-null check reads a real absence rather than an empty
            # dict that happens to be falsy for the same reason.
            contrast_resample_echo = resample_beside.get("resample")
            # One stratum LABEL per unit, composed once for the run: several
            # declared names mean the stratum is their cross — `reference.md`
            # § Weighted samples' own `stratify_by: [dx_status, count_stratum]`
            # — so the composition happens here, where the attributes live, and
            # `stats.py` sees one label per unit and never learns how many
            # attributes made it. Named `resample_strata` rather than `strata`:
            # that name is already this function's own fold-partition mapping,
            # a different stratification for a different purpose, in scope a
            # few hundred lines above.
            #
            # A unit carrying no value for one of the names joins a stratum of
            # its own rather than being dropped. `strata.levels_for` drops such
            # a unit from every REPORTING level, because there is no honest
            # level for "we don't know" — but a DRAW cannot drop it: the draw is
            # over the completed table, and dropping would change `n` silently
            # beneath an interval that claimed the full count. The sentinel is
            # printable rather than a control character: nothing emits the
            # composed `|`-joined stratum LABEL into `run.yaml` (the attribute
            # NAMES that make it up are recorded instead, on `resample_beside`'s
            # `resample.stratify_by`, H4a task 17 — a different, coarser fact
            # than the per-unit label this sentinel guards), but a NUL byte in
            # a string PyYAML is later asked to emit raises, and a printable
            # one costs nothing to choose now.
            #
            # NOT ADDRESSED: `<absent>` and the `|` separator are both ordinary
            # printable text, not reserved characters, so a real attribute value
            # equal to `<absent>`, or two attribute combinations that happen to
            # join into the identical `|`-separated string (one name's value
            # containing `|`, say), collide with the sentinel or with each
            # other and are read back as the same stratum. Recorded as a known
            # gap (`docs/superpowers/spec-defects.md`) rather than fixed here —
            # an unambiguous encoding is a bigger change than this task's own.
            #
            # Gated on BOTH `declared` and `stratify_by`, not on `stratify_by`
            # alone: they cannot disagree today (`_resolved_resample` reads
            # `stratify_by` off the same `declared` dict `declared` itself is
            # `bool()`-ed from, so a non-empty `stratify_by` implies `declared`
            # is true), but writing both is what pins that agreement rather
            # than leaving a reader to re-derive it — the identical reason
            # `resample_columns` below reads `declared`, not `n`.
            resample_strata: dict[str, str] | None = None
            if resample_spec["declared"] and resample_spec["stratify_by"]:
                resample_strata = {
                    u.key: "|".join(
                        "<absent>"
                        if u.attributes.get(name) is None
                        else str(u.attributes.get(name))
                        for name in resample_spec["stratify_by"]
                    )
                    for u in roster
                }
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
            collapsed_by_key: dict[tuple[int, str], dict[str, dict[str, Any]]] = {}
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
                cond_beside_n = {
                    **_condition_beside_n(beside_n, eval_roster, cond.index, arm_members_map),
                    **resample_beside,
                }
                for step_name in sorted(recording_steps):
                    collapsed = collapse_repeats(
                        results, step_name, cond.index, fold_members=fold_members
                    )
                    for column, units_count in repeats_disagreeing(
                        results, step_name, cond.index, fold_members=fold_members
                    ).items():
                        aggregate_c.warn(
                            "W-STATS-REPEATS-DISAGREE",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: recorded column "
                            f"{column!r} disagrees across the repeats of "
                            f"{units_count} unit(s); "
                            "declare data.units.measurements.collapse if the within-unit "
                            "collapse is what you meant",
                        )
                    counts = _condition_counts(
                        results,
                        eval_roster,
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
                    null_fns: (
                        dict[str, Callable[[UnitTable, dict[str, str]], float | None]] | None
                    ) = None
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
                            if derived_null_test is not None:
                                null_fns = {
                                    key: _make_null_fn(
                                        key,
                                        cond_cfg,
                                        template,
                                        unit_attributes,
                                        derived_null_test["shuffle"],
                                        aggregate_where,
                                    )
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
                            resample_columns=resample_spec["declared"],
                            strata=resample_strata,
                            null_test=derived_null_test,
                            labels=null_labels,
                            null_fns=null_fns,
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
                        # `seed`, `draws`, `resample_columns` and `strata` on
                        # the retry for the same reason `weights` is on it, and
                        # the four travel together because the column branch
                        # reads all four (H4a whole-branch review, I1). Left
                        # off — as they were until that review — a declared
                        # `statistics.resample` was silently dropped from every
                        # recorded column here while `beside_n` went on
                        # carrying the `resample` echo, so one block claimed a
                        # declaration and omitted the `resample_draws` key that
                        # `reference.md` § Statistical reporting makes the mark
                        # of an UNDECLARED resample ("absent entirely — not
                        # `null` — when no `resample` is declared"). `draws` matters
                        # as much as the gate does: at its 2000 default a
                        # config declaring `n: 500` would resample the column
                        # at 2000 draws beside an echo saying 500.
                        #
                        # **THIS RETRY CAN RAISE, AND A RAISE HERE IS
                        # UNCONTAINED** — no `run.yaml`, no run directory, every
                        # execution spent. `stats.py`'s `E-STEP-KEY-COLLISION`
                        # comment names that as the reason the recorded-column
                        # half of that fault is warned about rather than raised.
                        # The `try` above wraps the FIRST call, so a fault from
                        # `summarize_step`'s COLUMN loop lands in this handler
                        # too, and the retry then replays that same loop over
                        # the same inputs and raises again. There is no
                        # "reaching here means the columns already succeeded":
                        # the handler cannot tell a column fault from a derived
                        # one.
                        #
                        # **So what holds the line is upstream gating, not this
                        # handler**, and each column-loop raise needs its own
                        # gate named:
                        #
                        # - `E-DATA-WEIGHT-INVALID` (`checked_weights`) —
                        #   `attrition` above puts the same mapping through
                        #   `kish_effective_n` outside any `try`, and `validate`
                        #   checks the column against `usable_weight`. Already
                        #   the situation before this change: `weights` was
                        #   always passed on the retry.
                        # - `E-STATS-RESAMPLE-STRATIFY-VARIES`
                        #   (`percentile_over_units_clustered`) — reachable here
                        #   ONLY because this call now passes `strata` and
                        #   `resample_columns`. Gated by `validate`'s own
                        #   `E-STATS-RESAMPLE-STRATIFY-VARIES` over the roster,
                        #   per declared name, which `command_run` returns
                        #   `EXIT_WRONG` on before any execution runs. Per-name
                        #   constancy within a cluster implies constancy of the
                        #   `|`-joined cross `resample_strata` builds, so the
                        #   composed label cannot violate where the per-name
                        #   check passed; the composition's own filed gap
                        #   (`<absent>`, `|`) can only MERGE two strata into
                        #   one, never split one into two.
                        #
                        # A future change adding a new raise to that loop — or
                        # widening this call again — must name its gate the
                        # same way, or wrap this call and fall back. The suite
                        # cannot see any of this: it is a property of what
                        # `validate` refuses, not of what this handler does.
                        step_summary = summarize_step(
                            collapsed,
                            counts,
                            seed=resample_seed_value,
                            draws=derived_metric_draws,
                            beside_n=cond_beside_n,
                            weights=weights,
                            clusters=clusters,
                            resample_columns=resample_spec["declared"],
                            strata=resample_strata,
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
                        strata_resample: dict[str, Callable[[UnitTable], float | None]] | None = (
                            None
                        )
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
                    #
                    # This loop now reads a RECORDED COLUMN's `resample_draws`
                    # too (H4a task 14, once `resample_spec["declared"]` gates
                    # `resample_columns` above) — before this task a column
                    # carried no such key and `used is None` skipped it
                    # silently. Neither branch below can fire for one:
                    # `used == 0` would name `aggregate_where` — `aggregate`,
                    # user code — as the source of a failure `aggregate` never
                    # touched, since a column's interval never calls it. A
                    # column's `resample_draws` is `null` (skipping both
                    # branches, same as before) whenever `ci95` is, and
                    # otherwise the *requested* `draws` exactly — never a
                    # lesser survivor count — because a column's mean is a
                    # statistic over a finite, non-empty sample and is always
                    # defined once an interval exists at all, unlike a
                    # template's recompute, which can fail draw by draw.
                    # `used == derived_metric_draws` (not `<`) is what that
                    # buys: the `elif` below can't fire either. See
                    # `docs/superpowers/spec-defects.md` for the one gap this
                    # rests on — non-finite recorded values or weights, which
                    # nothing here checks — filed rather than silently
                    # depended on.
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
                    # `W-STATS-COLUMN-THIN` (Controller ruling 5, 2026-08-22):
                    # one warning per (condition, step, recorded column) whose
                    # CONTRIBUTING count — `summarize_step`'s per-column
                    # `n.completed`, the number of units that carried a real
                    # number for it, not the condition-wide figure — falls below
                    # `limits.min_reported_n`. Ruling 1 asked for a warning
                    # naming the count on every partially-covered column; ruling
                    # 5 narrowed it to this floor, because a step that measures
                    # only what it can measure is ordinary and an unconditional
                    # warning would fire on runs with nothing wrong.
                    #
                    # `limits.min_reported_n` rather than a threshold of its own:
                    # `W-STATS-CONTRAST-THIN` (a realized `n_paired`/`n_of`) and
                    # `W-STATS-STRATUM-THIN` (a level's realized `completed`)
                    # already read this floor at `run` time against a realized
                    # denominator, and a second source of truth for one hazard is
                    # what that ruling refuses. The guard is theirs verbatim:
                    # `check_envelope` is what reports a wrong-typed floor, and a
                    # `True` would otherwise drive "below limits.min_reported_n
                    # (True)".
                    #
                    # Two scope decisions, both deliberate. A column that earned
                    # NO block is skipped: it has no contributing count to name,
                    # and `W-STATS-REPEATS-DISAGREE` (or nothing at all, for a
                    # column no unit ever recorded a number for) is what covers
                    # it. And a `report_by` LEVEL's columns are not checked here:
                    # `W-STATS-STRATUM-THIN` below already names a thin level
                    # against the same floor, and per-column-per-level would
                    # multiply one fact by the number of columns.
                    #
                    # Sited after both `summarize_step` calls have converged on
                    # `step_summary`, so the `except ContractError` retry above is
                    # covered by this one site — a diagnostic's unit of work is
                    # every place it reports, and one code gets one row.
                    column_floor = (doc.get("limits") or {}).get("min_reported_n")
                    if isinstance(column_floor, (int, float)) and not isinstance(
                        column_floor, bool
                    ):
                        for column in sorted(recorded_columns):
                            block = step_summary.get(column)
                            if block is None:
                                continue
                            contributing = (block.get("n") or {}).get("completed")
                            if not isinstance(contributing, (int, float)) or isinstance(
                                contributing, bool
                            ):
                                continue
                            if contributing < column_floor:
                                aggregate_c.warn(
                                    "W-STATS-COLUMN-THIN",
                                    "limits.min_reported_n",
                                    f"condition {cond.index}, step {step_name!r}: recorded "
                                    f"column {column!r} carries a number for "
                                    f"{int(contributing)} unit(s), below "
                                    f"limits.min_reported_n ({column_floor})",
                                )
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
                            eval_roster, cond.index, arm_members_map, attribute
                        ).items():
                            # One key set decides BOTH the table and the counts.
                            # Taking the level's rows beside the condition's `n`
                            # is the S4b Critical's shape — a number reported
                            # against a denominator computed over other units.
                            level_collapsed = {k: v for k, v in collapsed.items() if k in keys}
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
                                # cluster mapping travels with it. `strata` the
                                # same way: a level's own units carry the same
                                # stratum labels the whole roster does, and
                                # `summarize_step` filters the mapping down to
                                # this level's own keys exactly as it does for
                                # a ragged column.
                                weights=weights,
                                clusters=clusters,
                                strata=resample_strata,
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
                    #
                    # The question is *did any unit record a column called
                    # `by`?*, and `recorded_columns` — built above from
                    # `collapsed`, for the `repeat_spread` walk — is that
                    # question's own answer. `step_summary` was a PROXY for it:
                    # a NON-numeric `by` column never reaches `summarize_step`'s
                    # published keys, so it drew no warning while
                    # `units.parquet` carried the column and `run.yaml` carried
                    # a `by` strata block — the two-meanings-under-one-name case
                    # the reserved name exists to prevent. The move is only a
                    # widening: `by` in `step_summary` implies `by` in
                    # `recorded_columns`, because a DERIVED `by` is refused in
                    # `summarize_step` (`RESERVED_METRIC_NAMES`) and the
                    # containment retry above passes no `derived` at all, so the
                    # only route into `step_summary` is the column loop over
                    # this same `collapsed`.
                    if "by" in recorded_columns:
                        aggregate_c.warn(
                            "W-STATS-STRATUM-SHADOWED",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: 'by' is a "
                            "reserved metric name — it holds the key the reporting "
                            "strata are attached under — so the recorded column of "
                            "that name gets no contrast delta and no seat in the "
                            "correction family, and no strata are reported for this "
                            "step",
                        )
                    # Absent, not empty, the rule `vs_baseline` and `contrasts`
                    # already follow: a `by: {}` would claim a stratification
                    # was performed and found nothing.
                    elif by_block:
                        aggregated[cond.index][step_name]["by"] = by_block
            vs_baseline, vs_baseline_members = _compute_vs_baseline(
                doc=doc,
                conditions=conditions,
                roster=eval_roster,
                aggregated=aggregated,
                collapsed_by_key=collapsed_by_key,
                derived_by_key=derived_by_key,
                resample_fns_by_key=resample_fns_by_key,
                seed=resample_seed_value,
                draws=derived_metric_draws,
                findings=aggregate_c,
                resample_columns=resample_spec["declared"],
                weights=weights,
                strata=resample_strata,
                weighted_by=weight_by if weights else None,
                clusters=clusters,
                resample_echo=contrast_resample_echo,
            )
            contrasts_out, contrast_members = _compute_declared_contrasts(
                doc=doc,
                conditions=conditions,
                roster=eval_roster,
                aggregated=aggregated,
                collapsed_by_key=collapsed_by_key,
                derived_by_key=derived_by_key,
                resample_fns_by_key=resample_fns_by_key,
                seed=resample_seed_value,
                draws=derived_metric_draws,
                findings=aggregate_c,
                resample_columns=resample_spec["declared"],
                weights=weights,
                strata=resample_strata,
                weighted_by=weight_by if weights else None,
                clusters=clusters,
                null_test=null_test_spec,
                resample_echo=contrast_resample_echo,
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
            aggregated=aggregated,
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
            drift_c.credentials = credentials
            noun = "path" if len(changed_inputs) == 1 else "paths"
            drift_c.error(
                "E-INPUT-CHANGED",
                "data.input_dir",
                f"{len(changed_inputs)} {noun} changed since the manifest was built "
                f"at run start: {', '.join(changed_inputs)}",
            )
            print(drift_c.render())

        # Populated from the declaration this run actually resolved through, not
        # from the machine's installed set: a run's provenance is what it used.
        # Empty stays the honest record for a run with no plugin artifact.
        plugin_versions: dict[str, str] = {}
        _source = (units_decl or {}).get("from")
        if isinstance(_source, dict) and isinstance(_source.get("resolver"), str):
            plugin_versions = versions_for(RESOLVER_GROUP, _source["resolver"])

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
                # Measured, not asserted: `pyvenv.cfg`'s own `uv` key, `None`
                # when this environment was not created by uv. See
                # `uv_support.environment_manager` for why that file rather
                # than `shutil.which("uv")`, and why an absent uv warns about
                # nothing.
                "manager": environment_manager(),
                "python_version": ".".join(str(v) for v in sys.version_info[:3]),
                # NOT `platform.platform()`: measured, it reports the marketing
                # name and version (`macOS-26.5.2-arm64-arm-64bit-Mach-O`) rather
                # than the kernel `uname` names (`Darwin`, `25.5.0`), and its
                # component count differs per platform. The composed form yields
                # exactly three components everywhere, which is the shape
                # `reference.md` § The two files shows.
                "os": f"{platform.system()}-{platform.release()}-{platform.machine()}",
                # `socket.gethostname()` and not `platform.uname().node`, which
                # returns the same fact: `run_identity` already answers "what
                # machine is this" this way for the run lock, and two spellings of
                # one fact is how the two drift. Redacted by `study add`.
                "hostname": socket.gethostname(),
                "uv_lock": "environment/uv.lock" if lock_path is not None else None,
                "uv_lock_hash": lock_hash,
                # `cpu_count` alone. A GPU is not universal and core cannot probe
                # one without a dependency or a subprocess, so it is an apparatus
                # fact — `reference.md` § The apparatus core can only observe.
                # `None` is `os.cpu_count()`'s own documented answer for
                # indeterminable and is written through rather than substituted:
                # this format already spells never-captured as `null`.
                "hardware": {"cpu_count": os.cpu_count()},
            },
            "apparatus": observer.block() if observer is not None else None,
            "input_manifest": "manifest/input.json",
            "input_manifest_hash": manifest_hash(manifest),
            "input_manifest_changed": changed_inputs,
            "publishable_version": importlib.metadata.version("publishable"),
            "plugin_versions": plugin_versions,
            # A run over a roster whose identity is not pinned is a run whose `n`
            # means nothing later: `units` and `units_hash` are `None` together
            # exactly when there is no `data.units` declaration to pin.
            #
            # **Whole-roster, deliberately, and not the same number a metric's
            # `n` reports.** Under a `data.units.holdout` a metric's
            # `n.resolved` counts the TEST partition — 48 where this says 240
            # — and both are true: this is the identity of the roster the run
            # resolved, which is what `units_hash` pins, and what makes a
            # roster that resolved differently detectable when the run is
            # reproduced, where `n` is the denominator of an estimate.
            # Narrowing this would make the hash cover a subset the config
            # never described.
            "units": (
                {"n": len(roster), "key": units_decl["key"]}
                if roster is not None and units_decl is not None
                else None
            ),
            "units_hash": units_hash(roster) if roster is not None else None,
            # "allocation.json" and its hash, `None`/`None` together exactly
            # when `alloc_doc` was never written — which is now when NEITHER an
            # arm assignment nor a `data.units.holdout` resolved, the gate
            # `build_allocation_document` widened. The same pairing `units`/
            # `units_hash` already use above, and the same reason: a file named
            # in the record and absent from disk is worse than an honest
            # `None`.
            "allocation": "allocation.json" if alloc_doc is not None else None,
            "allocation_hash": alloc_hash,
            # Decision 7: always a list, `[]` when nothing was read — on
            # `input_manifest_changed`'s precedent, not `apparatus: null`'s.
            # `upstream` has no declaration anywhere for a `null` to mean
            # "declared and did not apply", so there is no third state to
            # write, and a `None` here would be a reader hazard for the
            # ordinary `for u in provenance["upstream"]`.
            "upstream": upstream_ledger.entries(),
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
            draft=draft,
            aggregated=aggregated,
            condition_meta=condition_meta,
            vs_baseline=vs_baseline,
            contrasts=contrasts_out,
            hypotheses=hypothesis_verdicts,
            # `None` on every other entry, which is what makes
            # `_execution_block` write the `1` it always wrote.
            attempts=attempts,
        )
        (run_dir / "run.yaml").write_text(yaml.safe_dump(doc_out, sort_keys=False))
        # `with` block exit releases the lock.

        # `W-APPARATUS-UNANSWERED`, once at run end: `run.yaml` has no
        # diagnostics channel of its own — the same reason `aggregate_c`'s
        # findings print to stdout rather than joining the document — so
        # this is a FRESH `Collector` (never `c`, already rendered and
        # printed) rendered to stdout. A warning never changes the exit code,
        # on `W-ENV-UNLOCKED`'s own precedent.
        if observer is not None:
            warn_c = Collector()
            warn_c.credentials = credentials
            observer.warn_unanswered(warn_c)
            if warn_c.findings:
                print(warn_c.render())

    point_latest(output_dir, run_dir)
    print(f"run.yaml → {run_dir / 'run.yaml'}")
    # Whole-project review M1: a run whose every execution raised printed
    # nothing but its warning block and the line above, and a shell swallows
    # the `4` — so the only signal was an exit code nobody sees. The cause is
    # already in the record (`results.conditions[].executions[].error`); this
    # names it on the way out and changes nothing else: not the exit code
    # below, not `status`, not a byte of `run.yaml`.
    #
    # A plain line on stderr, not a `Collector` finding. It is a summary of
    # what the record already says rather than a new fault, so it mints no
    # code and owes no § Errors row.
    #
    # Stderr on two grounds, and NOT on a third that does not hold. It holds
    # that stdout is reserved for what a command produces (`generators/
    # experiment.py` says exactly that of its own README notices), and that
    # this function already sends `stop_c` there while `draft` sends its
    # relaxation notice there — a message about why a run went sideways is
    # that class. It does NOT hold that stdout would have broken a pin: both
    # the byte-exact stdout arm and `test_demo.py`'s
    # `test_run_itself_prints_no_table_banner_or_progress_bar` cover a
    # COMPLETING run only, and this line never fires for one.
    #
    # Redacted with the same credential set every diagnostic on this path uses.
    if status != "completed":
        errored = [r for r in results if r.error]
        if errored:
            first = errored[0]
            where = first.execution.step_name
            if first.execution.condition_index is not None:
                where += f" · condition {first.execution.condition_index}"
            if first.execution.repeat_label is not None:
                where += f" · {first.execution.repeat_label}"
            print(
                f"run {status}: {len(errored)} of {len(results)} executions failed; "
                f"first error at {where}: {redact(first.error, credentials)}",
                file=sys.stderr,
            )
        else:
            # `status` can be non-`completed` with every execution clean —
            # `E-INPUT-CHANGED` sets `failed` after the fact, and an apparatus
            # stop sets its own. Saying "0 of 5 failed" there would name the
            # wrong fact, so this half names none and points at the record.
            print(
                f"run {status}: no execution recorded an error; see {run_dir / 'run.yaml'}",
                file=sys.stderr,
            )
    # H7d Part B task 8 (Decision 6): an unreachable apparatus wins over
    # whatever status it wrote — `5` is the class you retry, so it takes
    # precedence over `3`/`4` the same reason a dirty tree or a missing
    # credential would (§ Exit codes and diagnostics's own stated
    # precedence). Read from `stop.reason`, the reason the run stopped,
    # rather than re-derived from `status` — a build deriving it from
    # `status` cannot tell `partial` (a truncation guard) from `partial`
    # (an unreachable apparatus) apart, which is exactly why Fixture U's
    # exit and status assertions are pinned separately.
    if stop.reason == "apparatus_unreachable":
        return EXIT_EXTERNAL
    return {"completed": EXIT_OK, "partial": EXIT_PARTIAL}.get(status, EXIT_FAILED)  # phase 10


def command_run(config_path: Path) -> int:
    """`publishable run` -- phases 1-5, then phases 6-10, with the gate enforced.

    `allow_dirty=False` is `run`'s whole difference from `draft`: the pathspec
    `E-CODE-DIRTY` covers is `git_provenance`'s and is not this call's business
    (H6b Decision 12 declined widening it, and Ruling T keeps the two edits
    apart). `isinstance`, not truthiness -- `EXIT_OK` is `0`.

    **The signpost, and it is load-bearing for a reader.** Until H9a this
    function held all ten phases, so roughly forty-five comments, docstrings
    and `reference.md` rows across this repository attribute a behaviour to
    "`cli.command_run`" and mean "the `run` command". Every one of them is
    still reachable in one hop: **phases 1-5 are `_prepare_run`** (validate,
    the dirty gate, `E-CODE-EMPTY`, the roster, the repeat plan, the hashes,
    the manifest, the upstream ledger) and **phases 6-10 are
    `_execute_prepared`** (the run directory, the apparatus rounds,
    `execute_plan`, aggregation, the correction family, `run.yaml`, the exit
    code). Stated here rather than by rewriting those forty-five sites: a
    rewrite of each would have to decide which half it now names, and a
    pointer invents nothing (`CLAUDE.md` § Habits, *prefer deleting a claim to
    rewriting it*). H9a task 2's report files the sweep as correction 22.
    """
    prepared = _prepare_run(config_path, allow_dirty=False)
    if not isinstance(prepared, Prepared):
        return prepared
    return _execute_prepared(prepared, draft=False)


def command_draft(config_path: Path) -> int:
    """`publishable draft` -- `run` with the dirty-tree gate relaxed.

    `reference.md` § Draft runs: a provisional run whose code state is not
    reachable from any commit. The gate exists to protect a RECORD's identity
    claim; a draft's record says `draft: true` in its own top-level key, which
    is what every reader keys on (`report.py` twice, `diff.py` once -- grepped,
    all three read `record.get("draft")` and none reads `code_dirty`).

    `git.code_dirty` stays a MEASUREMENT: a draft of a clean tree records
    `false`, because `provenance.git_provenance` answers about the tree and
    forcing it would make a provenance figure lie about the one thing
    provenance is for. § Draft runs' conjunction is corrected in task 6.
    """
    prepared = _prepare_run(config_path, allow_dirty=True)
    if not isinstance(prepared, Prepared):
        return prepared
    if prepared.git.code_dirty:
        # A notice, not a warning and not a finding: it changes no exit code
        # and enters no record. stderr, because it is about the invocation
        # rather than part of what the run reports -- and because `run`'s
        # stdout is pinned (task 1, arm B) and this must not enter it.
        print(
            "notice  draft   src/** or templates/** is uncommitted; "
            "recording draft: true and git.code_dirty: true",
            file=sys.stderr,
        )
    return _execute_prepared(prepared, draft=True)


def command_resume(run_dir: Path) -> int:
    """`publishable resume <run_dir>` — a SECOND entry into phases 6-10 of a
    run that stopped without writing `run.yaml`.

    **This is the containment, and `_resume_prepared` below is the decision**
    (Decision 13): every refusal `resume` itself decides is printed through
    one FRESH credential-bearing `Collector` to stderr and returns
    `EXIT_WRONG`, and nothing `resume` decides reaches `main`'s
    `except PublishableError` handler, which prints `{exc}` with no collector
    in scope and therefore no redaction.

    **The shape is `_prepare_run`'s roster wrapper, copied WITH where it
    sits** — `except BaseException`, `KeyboardInterrupt` re-raised fresh and
    argument-less so a `KeyboardInterrupt("…secret…")` a resolver constructed
    never reaches Python's own printer, and a fresh `Collector` whose
    `credentials` is the set `_prepare_run` already resolved rather than a
    second derivation of it. This repository has shipped a credential leak
    twice by lifting such a recipe's CALLS and leaving its `try` behind
    (`CLAUDE.md` § Answering a question with a proxy, the fifth instance), so
    the sink below exists for one reason: the credential set is resolved
    INSIDE the body being contained, and the handler needs it.

    A non-`PublishableError` is re-raised unchanged: nothing this function
    decides is in that class — user code is contained by `_prepare_run`'s own
    wrapper, which returns an exit code rather than raising — so anything else
    escaping here is a defect in core, and a traceback is the right report for
    one.

    **A path that is not a directory is `E-IO-FAILED` at exit 1**, the shipped
    code § Exit codes already assigns to *"a `diff` operand path that doesn't
    exist"* — the same question and the same answer, reported through a
    `Collector` because that section says of this code *"it is not a
    `ContractError`"*.

    **Order, and it is the whole of what makes a refusal safe**: everything
    below happens before `_execute_prepared` is reached, so a refusal costs
    nothing and touches no artifact.

    1. `identity.json` — `E-RESUME-NO-IDENTITY`.
    2. a `run.yaml` present — `E-RESUME-RUN-ENDED`. That run ENDED, and its
       record is never modified.
    3. `environment/repo_root.txt` and the recorded `config_path`, contained
       under that root — `E-RESUME-NO-CONFIG`.
    4. `_prepare_run` on that config, with the dirty gate relaxed exactly
       when the record says `draft` (Decision 12: a resumed draft stays a
       draft, and `allow_dirty` and `draft` come from the SAME recorded flag
       — a resumed draft recording `draft: false` would be citable).
    5. the three hashes and the input manifest, recomputed by that call and
       compared against the recorded figures.
    6. the ledger, the reconstitution, the attempt counts.
    7. `sweep.yaml`'s recorded plan — `E-RESUME-PLAN-MISSING` when the file
       cannot be read as a plan, `E-RESUME-PLAN-MISMATCH` when its conditions
       disagree with the re-expanded ones over the four-tuple, and the
       recorded `execution_order` when the recorded mode was `randomized`
       (Decision 9).
    8. `allocation.json` — read rather than re-drawn, overriding the arm
       memberships and the holdout partition through `dataclasses.replace`;
       `E-RESUME-ALLOCATION-STALE` when the record cannot be applied to this
       roster (Decision 10).
    9. the apparatus baseline, replayed from `apparatus/probes.jsonl` under
       `E-RESUME-PROBES-UNREADABLE`; an absent or empty one is legitimate
       and mints no refusal (Decision 11).

    **This deviates from the plan's stated order in one place, deliberately.**
    The task section lists the hash comparison BEFORE `_prepare_run`. Doing it
    there would mean computing `code_hash`, `parameters_hash` and the lockfile
    digest here, a second derivation of three figures `Prepared` already holds
    — the *second answer to one question* fault this repository names. Design
    Decision 7's requirement is that the comparison refuse **before the lock
    is taken and before anything executes**, and it does: `_prepare_run` is
    phases 1-5, which allocate nothing, take no lock and execute no step. The
    visible cost is that a hash mismatch prints `validate`'s findings first,
    which is the same order `run` prints them in.

    10. the lock takeover (Ruling W, task 14): `take_over_dead_lock`'s
        exclusive `lock.takeover` token, the `os.kill(pid, 0)` liveness test
        against this host's `gethostname()`, and the unlink — sited last, so
        that only phase 6's entry separates it from
        `_execute_prepared`'s `with RunLock(run_dir)`, which is its step 4.
    """
    if not run_dir.is_dir():
        io_c = Collector()
        io_c.error(
            "E-IO-FAILED",
            str(run_dir),
            "is not a directory, so there is no run to continue — `resume` takes the "
            "run directory a stopped run left behind",
        )
        print(io_c.render(), file=sys.stderr)
        return EXIT_WRONG
    # The credential set `_prepare_run` resolves, handed back so the handler
    # below can redact with it. A list rather than a return value because the
    # body can raise BEFORE it has one — every refusal at steps 1-3 happens
    # before any config is read, and an empty set is the honest answer there:
    # nothing had been read that a message could carry.
    credentials: list[dict[str, str]] = []
    try:
        return _resume_prepared(run_dir, credentials)
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        if not isinstance(exc, PublishableError):
            raise
        resume_c = Collector()
        resume_c.credentials = credentials[-1] if credentials else {}
        resume_c.error(exc.code, str(run_dir), str(exc))
        print(resume_c.render(), file=sys.stderr)
        return EXIT_WRONG


def _resume_prepared(run_dir: Path, credentials: list[dict[str, str]]) -> int:
    """Everything `resume` decides, raising as it decides it.

    Split from `command_resume` so that the containment above is one `try`
    around the whole decision rather than one per refusal — fourteen codes
    are raised from five modules (`run_identity`, `lineage`, `sweep`,
    `apparatus`, and here), and a `Collector` call at each raise site would be
    fourteen places for the next one to be forgotten. `credentials` is the
    sink the handler redacts with; nothing else is passed and nothing is
    returned but an exit code.
    """
    identity = read_identity(run_dir)
    if (run_dir / "run.yaml").exists():
        raise ContractError(
            f"{run_dir / 'run.yaml'} exists, so this run ended; a run record is never "
            "modified. Start a new run instead.",
            code="E-RESUME-RUN-ENDED",
        )
    repo_root = read_repo_root(run_dir)
    config_path = config_path_for(run_dir, repo_root, identity)
    draft = bool(identity["draft"])
    prepared = _prepare_run(config_path, allow_dirty=draft)
    if not isinstance(prepared, Prepared):
        # `isinstance`, never truthiness: `EXIT_OK` is `0` (H9a's own rule,
        # repeated rather than re-derived — the swap is blind because phases
        # 1-5 never return `EXIT_OK`, and `mypy` is the enforcer).
        return prepared
    # Handed to the containment, never re-derived there: a second derivation
    # of a credential set is a second answer to one question.
    credentials.append(prepared.credentials)

    for recorded_key, recomputed, code in (
        ("code_hash", prepared.ch, "E-RESUME-CODE-MOVED"),
        ("parameters_hash", prepared.ph, "E-RESUME-PARAMS-MOVED"),
        ("uv_lock_hash", prepared.lock_hash, "E-RESUME-LOCKFILE-MOVED"),
    ):
        if identity[recorded_key] != recomputed:
            raise ContractError(
                f"{run_dir / IDENTITY_FILE} records {recorded_key} "
                f"{identity[recorded_key]!r}; this tree computes {recomputed!r}. The "
                "run cannot be continued under a different one — start a new run.",
                code=code,
            )

    recorded_manifest_path = run_dir / "manifest" / "input.json"
    try:
        recorded_manifest = json.loads(recorded_manifest_path.read_text())
    except (OSError, ValueError):
        raise ContractError(
            f"{recorded_manifest_path} is absent or unreadable, so what this run read "
            "cannot be compared against what is there now",
            code="E-RESUME-INPUT-MOVED",
        ) from None
    if manifest_hash(recorded_manifest) != manifest_hash(prepared.manifest):
        raise ContractError(
            f"the inputs under {prepared.input_dir} no longer hash to what "
            f"{recorded_manifest_path} recorded",
            code="E-RESUME-INPUT-MOVED",
        )

    # The recorded plan, cross-checked over the full four-tuple BEFORE
    # anything executes (Decision 9). Read here rather than inside
    # `_execute_prepared` for the reason every other comparison is here: a
    # refusal at this point has taken no lock and touched no artifact.
    recorded_plan = read_sweep_plan(run_dir)
    check_recorded_conditions(recorded_plan, prepared.conditions)
    if recorded_plan.order == "randomized":
        # The recorded ORDER, checked here for the same reason the conditions
        # are: it is applied to `prepared.plan` inside `_execute_prepared`,
        # after the lock, where a disagreement raises `E-RUN-ORDER-MISMATCH` —
        # a code documented as core's resolved state disagreeing with ITSELF,
        # which on a resume it is not: the order comes from a file somebody can
        # edit. Refused here, pre-lock, under `resume`'s own code (task 16).
        check_recorded_order(recorded_plan, prepared.plan)

    # `allocation.json` read rather than re-drawn (Decision 10). After the
    # plan cross-check and still before the lock: the override rests on the
    # roster and the conditions this tree resolved, and both have just been
    # checked against the record.
    recorded_allocation = read_allocation(run_dir)
    if recorded_allocation is not None:
        prepared = _resumed_allocation(prepared, recorded_allocation)

    records = read_execution_ledger(run_dir)
    resumed = Resumed(
        run_dir=run_dir,
        prior_results=_reconstitute(
            prepared.plan,
            run_dir=run_dir,
            records=records,
            collapse=len(prepared.repeats) <= 1,
        ),
        attempts=attempt_counts(records),
        # The ORIGINAL run's baseline, replayed through the shipped
        # `Observations.record` (Decision 11) under `resume`'s OWN code:
        # `replay_ledger` defaults to `freeze`'s, which would be a lie
        # about which command found the fault. An absent or empty ledger
        # comes back as an empty `Observations` and mints NO refusal —
        # `freeze`'s `E-FREEZE-LEDGER-MISSING` exists because probing
        # then would pin a fact the run never adopted, while a run that
        # crashed before its first probe is entitled to set one exactly
        # as the original run's first probe would have.
        baseline=apparatus.replay_ledger(run_dir, code="E-RESUME-PROBES-UNREADABLE"),
        recorded_manifest=recorded_manifest,
        # The RECORDED order, and `None` when the record says nothing was
        # shuffled — read off `sweep.yaml`'s own `order` scalar rather
        # than off the re-read config, because the file is what the first
        # attempt did (Decision 9).
        execution_order=(
            recorded_plan.execution_order if recorded_plan.order == "randomized" else None
        ),
    )
    # The takeover (Ruling W, Decision 2), sited LAST — after every
    # comparison, after `_prepare_run`, and after `Resumed` is built, which
    # is the last file this function reads. Steps 1-3 are
    # `take_over_dead_lock`; **step 4 is `_execute_prepared`'s own
    # `with RunLock(run_dir)`**, whose comment already says so, and that
    # `O_CREAT | O_EXCL` stays the only claim in the system.
    #
    # **Siting it here is what makes the window small enough to describe.**
    # The design's step order reads as though the takeover comes first, and
    # taken literally it would put the whole of `_prepare_run` — a plugin
    # import and a resolver, which is user code — between the unlink and the
    # claim. Nothing between this call and that `with` reads a file, runs
    # user code, or can block: one function call and phase 6's
    # `run_dir = resumed.run_dir`. The cost is that a directory whose holder
    # is ALIVE is refused after phases 1-5 rather than before them, which
    # spends validation on a refusal — and phases 1-5 execute no step,
    # allocate nothing and take no lock, so a refusal here still touches no
    # artifact, which is the property Decision 7 asks for.
    take_over_dead_lock(run_dir)
    return _execute_prepared(prepared, draft=draft, resumed=resumed)


# `run_.../` stands in for the run directory `dry-run` never allocates: every
# printed step directory is relative to it, and `allocate_run_dir` is what
# turns the placeholder into a name — a timestamp and a `code_hash` prefix
# that cannot exist before the directory is claimed. Named once here so the
# printed paths and the relativization cannot drift apart.
_DRY_RUN_PLACEHOLDER = "run_..."

# The eight a run always writes, plus three that each depend on a
# declaration. (This comment used to claim the entries were "in the order
# `_execute_prepared` writes them in", which was already false of the
# shipped tuple -- the code writes `manifest/input.json` first and
# `sweep.yaml` sixth, where the tuple lists them third and second. The
# clause is deleted rather than rewritten: `_dry_run_fixed_files` sorts what
# it prints, so no order here is load-bearing.) Every conditional is
# answered by the STRUCTURAL fact that decides it in `_execute_prepared` --
# `lock_path is not None`, `build_allocation_document(...) is not None`, and
# the same `isinstance(declared_probe, str) and declared_probe` guard the run
# uses -- rather than by a reserved name or a config key read a second time,
# which is the proxy substitution this repository keeps paying for.
_DRY_RUN_FIXED_FILES = (
    "config.yaml",
    "sweep.yaml",
    "manifest/input.json",
    "environment/pyproject.toml",
    "environment/repo_root.txt",
    "identity.json",
    "executions.jsonl",
    "run.yaml",
)


def _handed_counts(prepared: Prepared) -> list[int | None]:
    """How many units each planned execution would be handed -- `None` for one
    handed no unit list at all.

    A **restatement** of `runner.execute_plan`'s four-way `execution.scope`
    dispatch, not an extraction of it (design Decision 11): extracting it
    would be a second behaviour-preserving extraction on a shipped path, in
    phase 7, outside the phases this slice is chartered to move. What prevents
    the two from drifting is an **agreement pin** -- one fold fixture and one
    group-axis fixture in which the printed `unit-executions` must equal the
    summed `len(io.units)` a real `run` of the same config hands out -- rather
    than a shared helper a re-routed call site could defeat silently.

    The two narrowings themselves are NOT restated: `_arm_keys` and
    `_handed_keys` are already single-call-site extracted functions in
    `runner`, and they are what this calls. In `execute_plan`'s own order:

    1. arm narrowing first, when a group axis is declared **and** the
       execution has a condition index (a `run`- or `summary`-scoped
       execution has neither, and keeps the whole roster);
    2. then, under a declared **fold**, `run` and `condition` scope receive
       `None` -- no fold exists yet there -- `repeat` scope receives
       `_handed_keys`' partition of the arm-narrowed roster, and `summary`
       receives the whole arm-narrowed roster, every fold having run by then;
    3. under a declared **holdout**, every scope receives the test partition,
       which is `prepared.eval_roster` already: `_cond_roster`'s
       single-authority rule means the narrowing happened once, before the
       plan, and `execute_plan` only attaches `.train` -- which changes no
       length.

    **An execution handed `None` contributes zero**, and the caller says so in
    the printed output, because a fold's `run`- and condition-scoped steps see
    no units at all and a reader adding the number up by hand would be short.
    """
    roster = prepared.eval_roster
    counts: list[int | None] = []
    for execution in prepared.plan:
        scoped = roster
        if (
            prepared.arm_members_map is not None
            and roster is not None
            and execution.condition_index is not None
        ):
            arm_keys = _arm_keys(
                execution.condition_index, {u.key for u in roster}, prepared.arm_members_map
            )
            scoped = UnitList([u for u in roster if u.key in arm_keys])
        handed: UnitList | None
        if prepared.fold_members is None or scoped is None:
            handed = scoped
        elif execution.scope in ("run", "condition"):
            handed = None
        elif execution.scope == "repeat":
            keys = _handed_keys(
                execution.repeat_label or "", {u.key for u in scoped}, prepared.fold_members
            )
            handed = UnitList([u for u in scoped if u.key in keys])
        else:
            handed = scoped
        counts.append(None if handed is None else len(handed))
    return counts


def _dry_run_step_dirs(prepared: Prepared) -> list[str]:
    """Every step directory a run of this config would create, relative to the
    run directory, in plan order.

    One per planned (step, condition, repeat) triple, and the path scheme is
    **not re-derived**: `runner.step_dir_for` is called against a placeholder
    root and the answer relativized, so a change to the layout moves this
    output with it. `collapse` is `execute_plan`'s own
    `len(repeats) <= 1` -- a degenerate repeat level adds no directory
    component, and computing that here from anything else would be a second
    answer to one question.
    """
    root = Path(_DRY_RUN_PLACEHOLDER)
    collapse = len(prepared.repeats) <= 1
    # `dict.fromkeys`, not a `set`: plan order is what makes the list readable.
    # The de-duplication itself is defensive, not a case this plan can reach
    # today: `collapse` is `len(prepared.repeats) <= 1`, so whenever it is
    # true there is at most one repeat label per condition and no two
    # `build_plan` entries for one step in one condition can share a path.
    return list(
        dict.fromkeys(
            str(step_dir_for(root, execution, collapse).relative_to(root))
            for execution in prepared.plan
        )
    )


def _dry_run_fixed_files(prepared: Prepared) -> list[str]:
    """The run-directory-relative files a run writes whose names are fixed by
    core rather than by step code. See `_DRY_RUN_FIXED_FILES` for why each
    conditional is answered by a structural fact."""
    files = list(_DRY_RUN_FIXED_FILES)
    if prepared.lock_path is not None:
        files.append("environment/uv.lock")
    if build_allocation_document(prepared.group_axes, prepared.holdout_plan) is not None:
        files.append("allocation.json")
    declared_probe = getattr(prepared.run_template, "apparatus_probe", None)
    if isinstance(declared_probe, str) and declared_probe:
        files.append("apparatus/probes.jsonl")
    return sorted(files)


def _dry_run_probe(prepared: Prepared) -> int | None:
    """`dry-run`'s own apparatus round -- the exit code it must return, or
    `None` to carry on printing.

    **Decision 6: this is NOT phases 1-5.** The run-start round lives inside
    `with RunLock(run_dir)`, after `allocate_run_dir`, so "phases 1-5 plus the
    probe" is not a contiguous prefix and `dry-run` cannot obtain the probe by
    re-entering phases 1-5. It gets a round of its own, assembled from the
    shipped pure pieces -- `apparatus.observe_once` -> `apparatus.check_facts`
    -> `Observations.record` -> `Observations.warn_unanswered` -- once per
    resolved condition, each under **that condition's own cfg** from
    `prepared.cfgs`, never the wide `cfgs[-1]`, which is `Observer.observe_round`'s
    own rule for a `condition_index=None` round.

    **No `Observer` is constructed, and that is a rejection rather than an
    omission.** `Observer.__init__` requires `run_dir: Path` and
    `_observe_one` calls `append_observation` unconditionally, before
    recording and before the gate -- deliberately, so the moving observation
    is on disk before anything can stop the run. `dry-run` creates no run
    directory, so there is no ledger to append to. Defaulting `run_dir=None`
    and skipping the append inside `_observe_one` was considered and rejected:
    it is a fail-open shape on a class whose whole guarantee is that the
    append happens first, and a later caller that forgot the argument would
    lose the ledger silently. Calling the pieces directly changes
    `apparatus.py` not at all.

    **`check_changed` is not called, and the ground is read off the two
    functions rather than argued from the absence of a run.**
    `Observations.record` fills `_first_answered` from the facts it is handed;
    `changed` compares the *next* facts against that entry. With one round --
    one call per condition -- the value the gate would compare against **is
    the value it was just given**, so `changed` can only return `None`. Not
    "there is no baseline": there is one, and it is the observation itself.

    **`warn_unanswered` IS kept** (Decision 6): `W-APPARATUS-UNANSWERED`
    before a metered run is exactly the news § Before you spend it exists to
    deliver, and it costs one in-memory `Observations`. A fresh `Collector`
    rendered to stdout, never `prepared.c`, which phases 1-5 already rendered
    and printed -- appending to it would re-print every earlier finding and
    inflate the counts line. A warning never changes an exit code, on
    `W-ENV-UNLOCKED`'s precedent.

    **Decision 14: the containment travels with the calls.** Both `try`
    blocks below are `command_run`'s own -- `except BaseException` (a probe
    calling `sys.exit()` is covered; `except Exception` would end the command
    with no diagnostic at all), `KeyboardInterrupt` re-raised **fresh and
    argument-less** so a `KeyboardInterrupt("...secret...")` a probe body
    constructed never reaches Python's own printer, and a **fresh
    credential-bearing `Collector`** rendered to stderr, which is what
    redacts. `main`'s `PublishableError` handler prints `{exc}` with no
    collector in scope, so anything escaping here is un-redacted. This is
    verbatim the fault `CLAUDE.md` names as *copying a recipe's calls without
    its containment*: H8c's `report` lifted `freeze`'s credential wiring as
    calls and left the `try` behind, and a declared credential reached stderr
    in a case § Secrets promises to redact. The **return branches** are copied
    with the `try`, not only its shape: a dispatch failure is `EXIT_WRONG`,
    and at the call site `E-APPARATUS-RAISED` -- the apparatus itself
    unreachable -- is the one code that earns `EXIT_EXTERNAL`, exactly as
    `command_run`'s containment splits them.
    """
    declared_probe = getattr(prepared.run_template, "apparatus_probe", None)
    # `validate._check_probe` is what refuses a non-`str` declaration, and
    # `_prepare_run` has already run it -- this guard is the same shape the
    # run-start round uses, so a template declaring nothing costs nothing.
    if not (isinstance(declared_probe, str) and declared_probe):
        return None
    declared_facts = list(getattr(prepared.run_template, "apparatus_facts", None) or [])
    try:
        probe_fn = apparatus._probe_for(declared_probe)
    except BaseException as exc:
        # `_probe_for`'s middle step (`load_entry_point`) imports a plugin's
        # top level -- user code -- so a load-time failure can carry a
        # credential the plugin's own import-time body read.
        # `validate._check_probe` answers only `E-PROBE-UNKNOWN` from package
        # metadata and never loads anything, so this failure gets no verdict
        # from phases 1-5 at all.
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        dispatch_c = Collector()
        dispatch_c.credentials = prepared.credentials
        dispatch_code = exc.code if isinstance(exc, PublishableError) else "E-PLUGIN-LOAD"
        dispatch_c.error(dispatch_code, "experiment_type", str(exc))
        print(dispatch_c.render(), file=sys.stderr)
        return EXIT_WRONG

    observations = apparatus.Observations()
    try:
        for condition in prepared.conditions:
            returned = apparatus.observe_once(
                probe_fn, prepared.cfgs[condition.index], probe_name=declared_probe
            )
            facts = apparatus.check_facts(
                returned,
                declared_facts,
                probe_name=declared_probe,
                credentials=prepared.credentials,
            )
            observations.record(apparatus.condition_key(condition.index, condition.label), facts)
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise KeyboardInterrupt from None
        probe_c = Collector()
        probe_c.credentials = prepared.credentials
        code = exc.code if isinstance(exc, PublishableError) else "E-APPARATUS-RAISED"
        probe_c.error(code, "experiment_type", str(exc))
        print(probe_c.render(), file=sys.stderr)
        if code == "E-APPARATUS-RAISED":
            return EXIT_EXTERNAL
        return EXIT_WRONG

    warn_c = Collector()
    warn_c.credentials = prepared.credentials
    observations.warn_unanswered(warn_c, declared_facts)
    if warn_c.findings:
        print(warn_c.render())
    return None


def command_dry_run(config_path: Path) -> int:
    """`publishable dry-run` -- phases 1-5, printed, and nothing written.

    **Ruling R (design Decision 1): the promise narrows to what core can
    derive.** § Operation commands used to promise "every artifact path that
    *would* be written", which needs the `io.write` names inside step bodies --
    and `design-principles.md` § Greenfield only says core never inspects the
    body of user Python. A promise that can only be kept by breaking a stated
    non-promise is the **document** being wrong, so the document changed
    (task 9) and this prints step directories, the fixed files, and the
    unit-execution count. **The output says what it omits and why**: printing
    less without saying so would reproduce the defect in the one direction a
    reader cannot see.

    `allow_dirty=True` (Decision 8): the gate exists to protect a *record's*
    identity claim, and this writes no record -- there is no `code_hash` in
    this output at all, so there is no figure to mistake for one. That is a
    second USE of Ruling T's parameter, never a widening of what the gate
    covers.

    **Creates nothing** is scoped to `output_dir` (Decision 12): importing the
    entrypoint runs `discover_local`, which writes `__pycache__` under
    `src/**` and `templates/**` exactly as `validate` already does, and a
    bytecode cache is not an artifact of a run. No run directory is allocated,
    so no lock is taken either -- pointing this at a live run is as ordinary as
    reading the ledger.

    **The apparatus is probed, and nothing is appended** (Decisions 6, 7 and
    15): `_dry_run_probe` runs one round per resolved condition after the
    manifest and before any printing, so the cost ordering is validate ->
    manifest -> probe and a config that does not validate never reaches the
    probe. `PHASE_DRY_RUN` keeps its constant and gains no call site: the
    ledger lives inside a run directory this command never creates, so the
    phase name is reserved rather than written.

    **No comparison list is printed** (Decision 16): `contrasts.resolve_contrasts`
    is reached only from phase 8, which this never enters, so the standing
    unhashable-side precondition on H9 is discharged by construction. The
    `comparisons:` line reads `data.units.allocation` -- a declaration -- and
    resolves nothing.
    """
    prepared = _prepare_run(config_path, allow_dirty=True)
    if not isinstance(prepared, Prepared):
        return prepared

    # Decision 15's cost ordering, and the ordering IS the behaviour: validate
    # -> manifest (both inside `_prepare_run`) -> probe, stopping at the first
    # failure. A config that does not validate exits `1` with the probe never
    # called, so a cheap fault is never paid for at apparatus prices; only a
    # config that validates can reach `5`. That is what makes the two codes
    # mean "failed cheaply" versus "failed expensively", and it is why the
    # round is sited HERE rather than beside the printing below.
    probe_exit = _dry_run_probe(prepared)
    if probe_exit is not None:
        return probe_exit

    lines: list[str] = []
    modes = ["baseline"] if any(c.is_baseline for c in prepared.conditions) else []
    # `"baseline"` is itself a truthy key of `sweep` whenever the seed above
    # fires (`sweep.expand` only sets `is_baseline=True` from its own
    # `if baseline:` loop), so counting it again here double-prints it —
    # `(baseline + baseline + grid)`, invisible to the only prior assertion
    # on this line because that fixture was grid-only. Excluded rather than
    # re-deduplicated after the fact: the seed already carries it.
    modes += [k for k, v in (prepared.doc.get("sweep") or {}).items() if v and k != "baseline"]
    n_conditions = len(prepared.conditions)
    n_repeats = len(prepared.repeats)
    executions = len(prepared.plan)
    lines.append(
        f"sweep: {n_conditions} conditions"
        + (f" ({' + '.join(modes)})" if modes else "")
        + f" × {n_repeats} repeats = {executions} executions"
    )
    for condition in prepared.conditions:
        values = " ".join(f"{path}={value}" for path, value in condition.values.items())
        label = condition_dir_name(condition.index, condition.label or "")
        lines.append(f"  {label}" + (f"  {values}" if values else ""))
    lines.append(
        "repeats: "
        + " × ".join(
            f"{level.kind}(k={level.n})" if level.kind == "fold" else f"{level.kind}(n={level.n})"
            for level in prepared.levels
        )
    )
    lines.append(f"  seeds: {[r.seed for r in prepared.repeats]}  (auto, from design digest)")
    allocation = ((prepared.units_decl or {}).get("allocation")) or "within"
    lines.append(
        f"  comparisons: {'paired' if allocation == 'within' else 'unpaired'} "
        f"(allocation: {allocation})"
    )
    lines.append(
        "steps: "
        + " -> ".join(
            f"{name} ({scope})"
            for name, scope in dict.fromkeys((e.step_name, e.scope) for e in prepared.plan)
        )
    )
    resolved = 0 if prepared.roster is None else len(prepared.roster)
    correction = (prepared.doc.get("statistics") or {}).get("correction")
    lines.append(
        f"statistics: basis units (n={resolved} resolved); correction {correction}; "
        "derived metric names come from the template's aggregate() and are not "
        "knowable before the run"
    )

    counts = _handed_counts(prepared)
    unit_executions = sum(count for count in counts if count is not None)
    distinct = {count for count in counts if count is not None}
    if len(distinct) == 1 and None not in counts:
        detail = f"({executions} executions × {distinct.pop()} units handed to each)"
    else:
        detail = f"(over {executions} executions; the count handed varies by scope and partition)"
    lines.append(f"scale:  {unit_executions} unit-executions {detail}")
    if None in counts:
        lines.append(
            f"  {counts.count(None)} of those executions are handed no unit list at all — a "
            "fold's `run`- and condition-scoped steps see no units, and each contributes zero"
        )

    step_dirs = _dry_run_step_dirs(prepared)
    fixed_files = _dry_run_fixed_files(prepared)
    lines.append(
        f"would create {len(step_dirs)} step directories under "
        f"{prepared.output_dir / _DRY_RUN_PLACEHOLDER}/"
    )
    lines += [f"  {d}" for d in step_dirs]
    lines.append(f"and {len(fixed_files)} fixed files in that directory:")
    lines += [f"  {f}" for f in fixed_files]
    lines.append(
        f"the {prepared.output_dir / 'latest'} pointer is repointed too; it sits beside the "
        "run directory rather than inside it"
    )
    # Ruling R's own requirement, in the output rather than only in the
    # document: a narrowed promise that does not say what it dropped is worse
    # than the wrong one it replaces, because nothing marks it partial at the
    # point of reading.
    lines.append(
        "artifact files inside a step directory are NOT listed: their names are `io.write`"
    )
    lines.append(
        "  arguments in step code, which core never inspects, so they are declared nowhere"
    )
    lines.append("  in the config and cannot be known before the run")
    lines.append("creates nothing")
    print("\n".join(lines))
    return EXIT_OK


def command_list_templates() -> int:
    """`publishable list-templates` — every template name this build knows,
    with its provenance, its provider, and its full parameter spec where one is
    readable.

    **It takes no path** and walks up from `Path.cwd()`, which is the exception
    `E-GIT-NO-REPO`'s own § Errors row already documents for the creation
    commands, reused rather than restated (Ruling FF).

    **A missing repository is caught BY TYPE**, leaving `repo_root=None`
    exactly as `validate.validate_config` does, and the absence is **printed**:
    core's `generic` and every installed claim are answerable without a
    repository, and only `templates/**` discovery is skipped — so a shorter
    list with no explanation would be the *silently skipped* fault this repo
    already has a filing about.

    **It prints every CLAIM, and a parameter spec only where a class exists.**
    An installed claim's class is `None` by construction (correction 21): the
    entry-point scan reads package metadata and imports nothing, which is the
    invariant *"`validate` resolves a name without importing the package"*.
    Printing its spec would mean importing the package here, making this the
    one surface in the build that loads what every other one refuses to load —
    and resolving, for a listing, a name a config naming it is refused for. So
    it prints the provider and one line saying the spec is not readable, citing
    `E-TEMPLATE-INSTALLED-UNSUPPORTED` — a permanent refusal as this project
    ships, which is why that line names no slice.

    **Ruling FF rejects `H9-SCOPING.md` § 7.2's own preferred answer** —
    narrowing this to the installed set and never a project-local template.
    A project-local template is the case `docs/reference.md` § Templates says
    path discovery exists for, and the case `docs`' own `templates` region
    needs.

    **`E-TEMPLATE-COLLISION` is not caught**, and neither is `E-TEMPLATE-LOAD`:
    both reach `main`, which is the same answer `validate` gives. The command
    whose job is enumerating names is the wrong place to invent a tolerant
    enumeration — a name two providers claim has no listing that is not a lie
    about one of them.

    The renderer is `docs.template_details`, the one the `templates` region
    reads, rather than a second one: two renderings of one `parameter_spec` are
    two literals that drift.
    """
    from publishable.docs import template_details
    from publishable.templates.registry import _claims

    here = Path.cwd()
    notes: list[str] = []
    try:
        repo_root: Path | None = find_repo_root(here)
    except ContractError:
        # BY TYPE, testing no code, and the shape is `validate.validate_config`'s
        # own (Decision 4): `find_repo_root` raises exactly one code, and this
        # site wants the same answer — no repository, so no `templates/**` — for
        # any refusal that walk-up can produce. `docs` catches BY CODE instead,
        # and the difference is not stylistic: a README is that command's entire
        # input, so a walk-up it cannot complete is a refusal, while here it only
        # narrows the list. Two additions of two different kinds, which is why
        # `E-GIT-NO-REPO`'s § Errors row cannot be repaired by changing a digit.
        repo_root = None
        notes.append(
            f"no git repository was found from {here} upwards, so no project-local "
            "`templates/` was searched — the names below are core's own and any "
            "installed plugin's"
        )

    claims = _claims(repo_root)
    lines = list(notes)
    if notes:
        lines.append("")
    for name in sorted(claims):
        claim = claims[name]
        lines.append(f"### `{name}`")
        lines.append("")
        if claim.cls is not None:
            lines.append(f"{claim.provenance} · provider `{claim.provider}`")
            lines.append("")
        lines.extend(template_details(claim))
        lines.append("")
    print("\n".join(lines).rstrip("\n"))
    return EXIT_OK


def _dispatch(command: str, rest: list[str]) -> int:
    if command in OPERATION_COMMANDS:
        if len(rest) != 1 or rest[0].startswith("-"):
            print(f"`{command}` takes exactly one path and no flags", file=sys.stderr)
            return EXIT_INVOCATION
        # `freeze` and `report` join the existing one-path arm rather than
        # getting a second enforcer of the same rule (`_nest_repeat`'s own
        # docstring argues against two enforcers of one rule). Function-local
        # import: `freeze.py` imports `cli.declared_credential_names` at
        # module scope, so `cli.py` importing `freeze` there too would close
        # a cycle — this is the escape hatch, and it costs nothing since
        # `_dispatch` is called once per invocation, not once per import.
        # `report.py` imports nothing from `cli` at all (its bundle-form arm
        # is its own coded refusal), so `command_report` is function-local
        # here for symmetry with `command_freeze` rather than out of any
        # cycle of its own.
        from publishable.freeze import command_freeze
        from publishable.report import command_report
        from publishable.reproduce import command_reproduce

        handlers: dict[str, Callable[[Path], int]] = {
            "validate": command_validate,
            "dry-run": command_dry_run,
            "run": command_run,
            "draft": command_draft,
            # `resume` joins the existing one-path arm rather than getting a
            # second enforcer of the same rule, exactly as `draft`, `freeze`
            # and `report` did. `publishable resume new` dispatches into
            # `command_resume` with `new` as its path instead of printing the
            # unbuilt diagnostic, which is item 5 of the design's disclosure
            # and is pinned rather than merely disclosed. That outcome does
            # NOT rest on this function's branch order: hoisting the
            # `NOT_BUILT_COMMANDS` lookups above the built branches leaves the
            # full suite green (measured, H9b whole-branch review Minor 4),
            # and the order is filed as unpinned in
            # `docs/superpowers/spec-defects.md`.
            "resume": command_resume,
            # `reproduce` joins the same one-path arm for the same reason, and
            # its function-local import is `command_freeze`'s: `reproduce.py`
            # imports `validate.declared_credential_names_for` at module scope
            # and `cli.py` imports `validate` at module scope, so a module-scope
            # import here would put a third module on that chain for no gain.
            # `publishable reproduce new` dispatches into `command_reproduce`
            # with `new` as its path rather than printing the unbuilt
            # diagnostic — `new` is a single token, so the arity arm accepts it
            # and the two-token `NOT_BUILT_COMMANDS` lookup never happens. That
            # is item 5 of the design's disclosure, MEASURED through the real
            # console script and pinned below rather than predicted, and it does
            # NOT rest on this function's branch order (which is filed as
            # unpinned in `docs/superpowers/spec-defects.md`): the arms assert
            # the code and the identifier, never which branch answered.
            "reproduce": command_reproduce,
            "freeze": command_freeze,
            "report": command_report,
        }
        return handlers[command](Path(rest[0]))
    if command == "diff":
        # `diff` gets its OWN arm rather than joining `OPERATION_COMMANDS`'s:
        # that arm enforces exactly ONE path, and `diff` takes exactly TWO —
        # a second enforcer of a different arity rule, not a second enforcer
        # of the same one `freeze` joined above (H8b task 11, Decision 5
        # part 1). Same rejection of a leading `-`, same "no flags" rule
        # (`design-principles.md` § Everything is in the file): no
        # `--format`, no `--only`, no selector.
        if len(rest) != 2 or any(p.startswith("-") for p in rest):
            print("`diff` takes exactly two paths and no flags", file=sys.stderr)
            return EXIT_INVOCATION
        from publishable.diff import command_diff

        return command_diff(Path(rest[0]), Path(rest[1]))
    if command in ZERO_ARGUMENT_COMMANDS:
        # The arity rule these two carry is *takes nothing*, so ONE check
        # covers both halves `docs/reference.md` § Operation commands states —
        # no path, and no flag either, a flag being an argument. `diff`'s arm
        # argues why this is its own arm rather than a widening of the
        # one-path one: a different arity rule, not a second enforcer of the
        # same one.
        if rest:
            print(f"`{command}` takes no arguments and no flags", file=sys.stderr)
            return EXIT_INVOCATION
        # Function-local, `command_freeze`'s own reason: `docs.py` is imported
        # by both generators at module scope and `cli.py` imports them, so a
        # module-scope import here would put this module on that chain for no
        # gain — `_dispatch` runs once per invocation, not once per import.
        from publishable.docs import command_docs

        zero_argument: dict[str, Callable[[], int]] = {
            "docs": command_docs,
            "list-templates": command_list_templates,
        }
        return zero_argument[command]()
    if command == "demo":
        # A creation command, so it takes what is needed to bring something into
        # existence and nothing else: `docs/reference.md` § Creation commands
        # gives it *(none)* and `[--into DIR]`. `--into` is legal here and
        # refused by `reproduce` for a reason the two documents now state once:
        # `reproduce` derives its destination from the record, and `demo` has no
        # record to derive from.
        into: Path | None = None
        if rest:
            if len(rest) != 2 or rest[0] != "--into" or rest[1].startswith("-"):
                print("`demo` takes nothing, or `--into DIR`", file=sys.stderr)
                return EXIT_INVOCATION
            into = Path(rest[1])
        # Function-local, `command_freeze`'s own reason: `demo.py` imports
        # `scaffold` and `materialize` at module scope and runs the other
        # commands through this module's own `main`, so a module-scope import
        # here would close a cycle.
        from publishable.demo import command_demo

        return command_demo(into)
    if command == "new":
        if len(rest) != 1:
            return EXIT_INVOCATION
        root = scaffold_project(Path(rest[0]))
        # Whole-project review, Minor: `new` printed zero bytes at exit 0 — no
        # created path, no next step. Both lines are read off what
        # `scaffold_project` returned rather than composed from the argument,
        # and the second names the command `reference.md` § Scaffolding puts
        # next; nothing here claims a path this function did not write.
        print(f"project → {root}")
        print(
            f"next: cd {root} && uv run publishable generate experiment <name> "
            "--template generic --input-dir <dir> --output-dir <dir>"
        )
        return EXIT_OK
    if command in ("generate", "g", "init"):
        return _dispatch_generate(command, rest)
    if command == "plugin":
        if len(rest) != 2 or rest[0] != "new" or rest[1].startswith("-"):
            print("`plugin new` takes exactly one path", file=sys.stderr)
            return EXIT_INVOCATION
        scaffold_plugin(Path(rest[1]))
        return EXIT_OK
    if command == "study":
        return _dispatch_study(rest)
    # Everything built is handled above, so what reaches here is either specified
    # and unbuilt or not specified at all. The built branches come first on
    # purpose: a name that appeared in both places would keep working, and the
    # document-versus-code test is what would then report the mistake, rather than
    # a real command silently becoming a roadmap notice.
    two_token = f"{command} {rest[0]}" if rest else ""
    if two_token in NOT_BUILT_COMMANDS:
        return _report_not_built(two_token, NOT_BUILT_COMMANDS[two_token])
    if command in NOT_BUILT_COMMANDS:
        return _report_not_built(command, NOT_BUILT_COMMANDS[command])
    if any(n.startswith(f"{command} ") for n in NOT_BUILT_COMMANDS):
        # `publishable study` with no subcommand, or an unrecognized one. Every
        # subcommand of such a group is unbuilt today, so the group answer is the
        # same answer; § Creation commands is the table that holds all of them.
        return _report_not_built(command, "Creation commands")
    print(f"unknown command `{command}`", file=sys.stderr)
    return EXIT_INVOCATION


def _dispatch_study(rest: list[str]) -> int:
    """The `study` arm: both `new` (task 11) and `add` (task 13) are real
    now, so a missing or unrecognized subcommand is a usage error rather
    than the specified-but-unbuilt diagnostic it used to be —
    `_dispatch`'s `any(n.startswith("study "))` fallback matches nothing
    once neither name is left in `NOT_BUILT_COMMANDS`, and printing
    `unknown command` for a group `docs/reference.md` § Creation commands
    still specifies would be the one wrong word (§ Corrections,
    correction 4).
    """
    sub = rest[0] if rest else None
    if sub == "new":
        return _dispatch_study_new(rest[1:])
    if sub == "add":
        return _dispatch_study_add(rest[1:])
    print(
        "`publishable study` needs a subcommand: `new` or `add` — see "
        "docs/reference.md § Creation commands",
        file=sys.stderr,
    )
    return EXIT_INVOCATION


def _dispatch_study_new(rest: list[str]) -> int:
    """Parses `--title` explicitly and refuses BEFORE anything reaches
    disk: an unrecognized option or a missing/absent `--title` is
    `EXIT_INVOCATION`, never silently dropped the way `_dispatch_generate`
    drops one — a typo'd `--titel` would otherwise write a bundle carrying
    the wrong title, and `E-STUDY-EXISTS` then refuses to let anyone
    correct it.

    `test_reference_cli_tables_match_what_the_cli_does` DOES probe this
    arm from inside this very repository with two junk positionals and no
    `--title` (`main(["study", "new", "_probe_a", "_probe_b"])`), but — a
    docstring claim checked and found overreaching in fix round 1 — that
    test's own `built`-row branch asserts only that stderr carries neither
    `unknown command` nor `is specified but not built`; it checks no exit
    code and touches no disk. Removing the arity/`--title` check leaves it
    passing, because the invocation then falls through to
    `_refuse_if_in_repo` instead — `_probe_a` resolves inside THIS repo,
    so `E-STUDY-IN-REPO` fires and neither forbidden phrase appears
    either way. What actually pins this check is
    `tests/test_study.py`'s own direct `main(...)` calls, which assert the
    exit code and (separately) that nothing reached disk.
    """
    positional: list[str] = []
    title: str | None = None
    i = 0
    while i < len(rest):
        token = rest[i]
        if token.startswith("--"):
            if token != "--title":
                print(
                    f"`study new` does not recognize `{token}` — see "
                    "docs/reference.md § Creation commands",
                    file=sys.stderr,
                )
                return EXIT_INVOCATION
            if i + 1 >= len(rest):
                print("`study new` needs a value for `--title`", file=sys.stderr)
                return EXIT_INVOCATION
            title = rest[i + 1]
            i += 2
        else:
            positional.append(token)
            i += 1
    if len(positional) != 1 or title is None:
        print(
            '`study new` takes a bundle path and `--title "..."` — see '
            "docs/reference.md § Creation commands",
            file=sys.stderr,
        )
        return EXIT_INVOCATION
    from publishable.study import study_new

    study_new(Path(positional[0]), title)
    return EXIT_OK


def _dispatch_study_add(rest: list[str]) -> int:
    """`study add <bundle> <run.yaml> --as <name>`. Same discipline as
    `_dispatch_study_new`: an unrecognized option, a missing `--as`, or the
    wrong number of positionals refuses at `EXIT_INVOCATION` before
    `study_add` ever touches disk. `study_add`'s own `E-STUDY-NAME-EXISTS`
    and every other `ContractError` it raises propagate to `main`'s own
    `except PublishableError`, which prints and exits `1` — this function
    only prints the `W-STUDY-COMMIT-MISMATCH` notice `study_add` returns,
    the same `Collector`-rendered shape `report.py`'s bundle notices use.
    """
    positional: list[str] = []
    name: str | None = None
    i = 0
    while i < len(rest):
        token = rest[i]
        if token.startswith("--"):
            if token != "--as":
                print(
                    f"`study add` does not recognize `{token}` — see "
                    "docs/reference.md § Creation commands",
                    file=sys.stderr,
                )
                return EXIT_INVOCATION
            if i + 1 >= len(rest):
                print("`study add` needs a value for `--as`", file=sys.stderr)
                return EXIT_INVOCATION
            name = rest[i + 1]
            i += 2
        else:
            positional.append(token)
            i += 1
    if len(positional) != 2 or name is None:
        print(
            "`study add` takes a bundle path, a run.yaml path, and "
            "`--as <name>` — see docs/reference.md § Creation commands",
            file=sys.stderr,
        )
        return EXIT_INVOCATION

    from publishable.study import study_add

    notices = study_add(Path(positional[0]), Path(positional[1]), name)
    if notices:
        notice_c = Collector()
        for code, message in notices:
            notice_c.warn(code, positional[0], message)
        print(notice_c.render())
    return EXIT_OK


def _dispatch_generate(command: str, rest: list[str]) -> int:
    """Parse `--flag value` pairs into `opts` and leave everything else positional.

    Unrecognized options are silently accepted into `opts` and then silently
    dropped by whichever `kind` branch below does not read them — `--plugin`
    passed to `generate step` or `generate template`, or a misspelled
    `--plguin` anywhere, installs nothing and prints nothing. Each `kind`
    branch below validates its own required options by name (`missing` for
    `experiment`); it does not reject an option it was not asked for.
    """
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
        config_path = generate_experiment(
            repo_root=repo_root,
            name=name,
            template_name=opts["template"],
            input_dir=opts["input-dir"],
            output_dir=opts["output-dir"],
            plugin=opts.get("plugin"),
        )
        # Whole-project review, Minor: this printed zero bytes at exit 0 too.
        # `config_path` is what `generate_experiment` returned, and the step is
        # named from `config_path`'s own sibling tree rather than recomposed —
        # `is_file()` before printing, because a path a command claims to have
        # written is worth one stat.
        print(f"config → {config_path}")
        step = repo_root / "src" / package_name(name) / "steps" / "step01_summarize_units.py"
        if step.is_file():
            print(f"step   → {step}")
        print(f"next: uv run publishable validate {config_path}")
        return EXIT_OK
    if kind == "step":
        if len(positional) != 2:
            return EXIT_INVOCATION
        generate_step(repo_root=repo_root, experiment=positional[0], step_name=positional[1])
        return EXIT_OK
    if kind == "template":
        # Both checks are made before anything reaches disk, and the arity one
        # has a second reason to be: the CLI-table test probes every built
        # generator with two junk positionals, inside this repository, so a
        # generator that wrote first would scaffold a template into the working
        # tree that every later `discover_local` then reads.
        if len(positional) != 1:
            print(
                "`generate template` takes one template name — see docs/reference.md § Generators",
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        name = positional[0]
        if not is_usable_name(name):
            print(
                f"`{name}` cannot name a project-local template — `templates/{name}.py` "
                "must be an importable module name that discovery does not skip; "
                "see docs/reference.md § Generators",
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        generate_template(repo_root=repo_root, name=name)
        return EXIT_OK
    if kind == "report":
        if len(positional) != 1:
            print(
                "`generate report` takes one experiment name — see docs/reference.md § Generators",
                file=sys.stderr,
            )
            return EXIT_INVOCATION
        generate_report(repo_root=repo_root, experiment=positional[0], fmt=opts.get("format"))
        return EXIT_OK
    if kind in NOT_BUILT_GENERATORS:
        return _report_not_built(f"generate {kind}", NOT_BUILT_GENERATORS[kind])
    print(
        f"unknown generator `{kind}` — see docs/reference.md § Generators"
        if kind
        else "`generate` takes a generator name — see docs/reference.md § Generators",
        file=sys.stderr,
    )
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

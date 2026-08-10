"""Dispatch. Operation commands take paths and nothing else.

See docs/reference.md § Exit codes and diagnostics, § Generators, § Scaffolding.
"""

import importlib
import importlib.metadata
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from publishable.base_experiment import BaseExperiment, load_experiment
from publishable.coercion import coerce_scalars
from publishable.config import Config
from publishable.contrasts import resolve_contrasts, units_matching
from publishable.diagnostics import (
    EXIT_FAILED,
    EXIT_INVOCATION,
    EXIT_OK,
    EXIT_PARTIAL,
    EXIT_WRONG,
    Collector,
)
from publishable.errors import ContractError, PublishableError
from publishable.generators.experiment import generate_experiment
from publishable.generators.step import generate_step
from publishable.hashes import code_hash, design_digest, parameters_hash
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
from publishable.run_record import assemble_run_yaml, run_status
from publishable.runner import attrition, execute_plan, resolve_condition_cfg, resolve_wide_cfg
from publishable.scaffold import scaffold_project
from publishable.scope import Execution, build_plan
from publishable.stats import (
    UnitTable,
    cohens_dz,
    collapse_repeats,
    mean_of,
    min_honest_draws,
    paired_keys,
    paired_percentile_of_derived,
    paired_t_over_units,
    repeat_spread,
    resample_seed,
    summarize_step,
)
from publishable.sweep import expand, sweep_document
from publishable.templates.base import BaseTemplate
from publishable.templates.registry import get_template
from publishable.units import Unit, UnitList, partition_units, resolve_units, units_hash
from publishable.uv_support import uv_lock_info
from publishable.validate import load_document, validate_config

if TYPE_CHECKING:
    from publishable.contrasts import Comparison
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
    `results.contrasts`, not this run's `vs_baseline`; that block isn't built
    yet (`docs/superpowers/spec-defects.md` is where that gap belongs, not a
    silent misfile here). The auto-generated baseline comparisons this
    function keeps are exactly the ones `resolve_contrasts` built with
    `id=<condition's own label>` and `against=<the baseline's index>` — the
    same identity test, run again here rather than threaded through as a
    fourth field on `Comparison`, since only this one caller needs it.
    """
    baseline = next((c for c in conditions if c.is_baseline), None)
    if baseline is None:
        return []
    label_by_index = {c.index: c.label for c in conditions}
    return [
        comp
        for comp in resolve_contrasts(doc, conditions)
        if comp.against == baseline.index and comp.id == label_by_index.get(comp.of)
    ]


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
) -> dict[int, dict[str, dict[str, dict[str, Any]]]] | None:
    """Every non-baseline condition's own delta against the baseline, per
    recording step and per metric already in `aggregated`.

    A recorded column takes `paired_t_over_units` over the per-unit
    differences, with `cohens_d = cohens_dz(diffs)`. A derived metric — one
    `aggregate` computed, absent any per-unit value to difference — takes
    `paired_percentile_of_derived` instead, recomputing the metric on each
    resampled draw via the same closure `_make_resample_fn` built for the
    *reported* condition's own resampled `ci95`; `cohens_d` is `None` there,
    for the reason the worked example carries `cohens_d: null` for `r`. Both
    constructions read `n_paired` off `stats.paired_keys` — the intersection
    of the two conditions' completed units, narrowed by `within` when the
    comparison declares one — and record `correction: null`: the correction
    family, `ci95_corrected`, `correction_level`, and `family_size` are S4c's.

    Returns `None`, not `{}`, when nothing survives: no baseline, no metric in
    common between a condition and the baseline, or (per
    `contrasts.resolve_contrasts`'s own docstring) no declared baseline at
    all. `assemble_run_yaml` omits the key entirely in that case rather than
    writing an empty block that would claim a comparison was made and found
    nothing.
    """
    if roster is None:
        return None
    comparisons = _baseline_comparisons(doc, conditions)
    if not comparisons:
        return None
    min_reported_n = (doc.get("limits") or {}).get("min_reported_n")
    out: dict[int, dict[str, dict[str, dict[str, Any]]]] = {}
    for comp in comparisons:
        allowed = units_matching(roster, comp.within)
        of_steps = {k[1] for k in collapsed_by_key if k[0] == comp.of}
        against_steps = {k[1] for k in collapsed_by_key if k[0] == comp.against}
        block: dict[str, dict[str, Any]] = {}
        for step_name in sorted(of_steps & against_steps):
            of_collapsed = collapsed_by_key[(comp.of, step_name)]
            against_collapsed = collapsed_by_key[(comp.against, step_name)]
            base_keys = paired_keys(of_collapsed, against_collapsed, allowed)
            of_summary = aggregated.get(comp.of, {}).get(step_name, {})
            against_summary = aggregated.get(comp.against, {}).get(step_name, {})
            of_derived = derived_by_key.get((comp.of, step_name)) or {}
            against_derived = derived_by_key.get((comp.against, step_name)) or {}
            metric_block: dict[str, Any] = {}
            for metric_key in sorted(set(of_summary) & set(against_summary)):
                is_derived = metric_key in of_derived or metric_key in against_derived
                if is_derived:
                    compute = (resample_fns_by_key.get((comp.of, step_name)) or {}).get(
                        metric_key
                    ) or (resample_fns_by_key.get((comp.against, step_name)) or {}).get(
                        metric_key
                    )
                    n_paired = len(base_keys)
                    interval = None
                    if compute is not None and n_paired >= 2:
                        interval, _ = paired_percentile_of_derived(
                            of_collapsed, against_collapsed, base_keys, compute, seed, draws=draws
                        )
                    of_value = of_summary[metric_key].get("value")
                    against_value = against_summary[metric_key].get("value")
                    delta = (
                        float(of_value) - float(against_value)
                        if of_value is not None and against_value is not None
                        else None
                    )
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
                if min_reported_n is not None and n_paired < min_reported_n:
                    findings.warn(
                        "W-STATS-CONTRAST-THIN",
                        "limits.min_reported_n",
                        f"condition {comp.of} ({comp.id!r}) vs baseline, step "
                        f"{step_name!r} metric {metric_key!r}: n_paired {n_paired} is "
                        f"below limits.min_reported_n ({min_reported_n})",
                    )
            if metric_block:
                block[step_name] = metric_block
        if block:
            out[comp.of] = block
    return out or None


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
    roster = resolve_units(units_decl, input_dir) if units_decl else None  # phase 5: roster
    # `unit_count` is what turns `{kind: fold, k: all}` into a real count and
    # what `_fold_k` checks a declared `k` against — the same roster
    # `_check_units`/`_check_replication` resolved at `validate` time, threaded
    # through here rather than trusted blind, since `run` re-resolves it fresh.
    levels = resolve_repeats(doc, digest, unit_count=len(roster) if roster is not None else None)
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
        partitions = partition_units(roster, fold_level.n, digest)
    fold_members = fold_members_for(levels, partitions) if partitions is not None else None

    conditions = expand(doc)
    # Every path any condition fixes, not just the grid's axes. A path
    # `sweep.baseline` fixes varies across conditions by definition — condition
    # `00` uses the baseline's value and every other condition uses the base
    # config's — so it is exactly as unreadable at `run`/`summary` scope as a
    # grid axis is. Reading the grid alone left a baseline-only path resolving
    # to the base value, which is a value no condition in the run used.
    sweep_block = doc.get("sweep") or {}
    swept_paths = set(sweep_block.get("grid") or {}) | set(sweep_block.get("baseline") or {})
    plan = build_plan(  # phase 4
        experiment,
        conditions=[(c.index, c.label) for c in conditions],
        repeat_labels=labels,
    )
    cfgs: dict[int, Config] = {
        c.index: resolve_condition_cfg(doc, dict(c.values)) for c in conditions
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
                ),
                sort_keys=False,
            )
        )

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
        # Condition metadata `ExecutionResult` cannot carry: `Execution` holds
        # index and label but not `is_baseline` or the swept `values`, and
        # `reference.md` § The two files shows both on the condition entry.
        # `dict(...)` unwraps `Condition.values`'s `MappingProxyType`, which
        # `yaml.safe_dump` has no representer for.
        condition_meta = {
            c.index: {"label": c.label, "is_baseline": c.is_baseline, "values": dict(c.values)}
            for c in conditions
        }
        if roster is not None:
            # `condition_index` is guarded per condition: core aggregates within
            # each condition and never pools across conditions — an unguarded
            # filter would let a same-named step from another condition mark this
            # one as having a recording step it never ran.
            template = get_template(doc.get("experiment_type", ""))
            resample_seed_value = resample_seed(digest)
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
            aggregate_c = Collector()
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
                for step_name in sorted(recording_steps):
                    collapsed = collapse_repeats(
                        results, step_name, cond.index, fold_members=fold_members
                    )
                    counts = attrition(
                        results, roster, step_name, cond.index, fold_members=fold_members
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
                                template.aggregate(UnitTable(collapsed), cond_cfg),
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
                            def _make_resample_fn(
                                key: str, cfg: Config, tmpl: BaseTemplate
                            ) -> Callable[[UnitTable], float | None]:
                                def resample_fn(units: UnitTable) -> float | None:
                                    value = coerce_scalars(
                                        tmpl.aggregate(units, cfg), where=aggregate_where
                                    ).get(key)
                                    return None if value is None else float(value)

                                return resample_fn

                            resample_fns = {
                                key: _make_resample_fn(key, cond_cfg, template) for key in derived
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
                        )
                    except ContractError as exc:
                        prefix = f"{exc.code} " if exc.code else ""
                        aggregate_c.warn(
                            "W-STATS-AGGREGATE-FAILED",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: "
                            f"{prefix}{type(exc).__name__}: {exc}",
                        )
                        step_summary = summarize_step(collapsed, counts)
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
            vs_baseline = _compute_vs_baseline(
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

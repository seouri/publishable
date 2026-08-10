"""The execution loop. One execution at a time, in the recorded order."""

import copy
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from publishable.artifacts import StepIO
from publishable.config import Config, SweptAway
from publishable.errors import ContractError
from publishable.replication import LABEL_JOIN, Repeat
from publishable.scope import Execution
from publishable.stats import handed_to
from publishable.sweep import condition_dir_name
from publishable.units import UnitList


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


def attrition(
    results: list[ExecutionResult],
    roster: "UnitList | None",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, int]:
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
    without a fold that is the full roster, since every execution receives it
    whole. With a fold it is the union over every *declared* fold's members
    intersected with the roster — which the partitions cover exactly, so it is
    the full roster again, whether or not each fold's execution ran. That is the
    right answer at this scope: the counts a condition reports are against the
    cohort the condition was run over, and a fold whose execution is missing
    leaves its units genuinely unsettled, so they land in `failed` rather than
    vanishing from the denominator. The smaller-than-roster figure — what one
    execution was handed — is the per-execution `resolved` reported in
    `per_repeat`, which is the level `reference.md` § What isn't a repeat states
    that rule at.

    This is the per-step, per-condition breakdown `stats.summarize_step` attaches
    as a metric's `n`. It is deliberately not what guards `max_failed_fraction`:
    that threshold is run-level and a union across every recording step (see
    `_units_failed_anywhere` in `execute_plan`), not an intersection scoped to one.
    """
    if roster is None:
        return {"resolved": 0, "completed": 0, "ineligible": 0, "failed": 0}
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
        return {"resolved": len(keys), "completed": 0, "ineligible": 0, "failed": len(keys)}
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
    return {
        "resolved": len(handed),
        "completed": len(completed),
        "ineligible": len(ineligible),
        "failed": len(handed) - len(completed) - len(ineligible),
    }


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
    """
    keys = {u.key for u in roster}
    recording_steps = {
        r.execution.step_name for r in results if r.execution.scope == "repeat" and r.rows
    }
    failed: set[str] = set()
    for r in results:
        if r.execution.scope != "repeat" or r.execution.step_name not in recording_steps:
            continue
        handed = _handed_keys(r.execution.repeat_label or "", keys, fold_members)
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


def resolve_condition_cfg(base: dict[str, Any], values: dict[str, Any]) -> Config:
    """Overlay this condition's swept values onto the base config.

    Each dotted path in `values` names a leaf under `parameters`; the overlay
    walks (creating intermediate mappings as needed) to that leaf and sets it,
    so a `condition`- or `repeat`-scoped step reads exactly this condition's
    value without ever mentioning the sweep that produced it.
    """
    doc = copy.deepcopy(base)
    for path, value in values.items():
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
) -> list[ExecutionResult]:
    """Run every execution in the plan, in order, one at a time.

    A failed execution never stops the run — the plan runs to its end, because
    abandoning it throws away every execution still pending and `resume` cannot
    un-abort a plan that was never attempted. `max_failed_fraction` is the one
    documented exception: unit failures only accumulate, so once the fraction of
    the roster that has failed in at least one execution crosses the threshold, no
    later execution can bring it back, and spending the remaining compute to
    confirm that is waste.
    """
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
        # A fold repeat puts the units out of reach of the wider scopes: there is
        # no fold at "run" or "condition" scope, since folds are repeats and
        # repeats haven't happened yet, so a step fitting there would fit on units
        # later folds test on. By "summary" scope every fold has already run, so
        # there is nothing left to leak, and it keeps the whole roster like the
        # no-fold case. `units` (the full roster, from the outer scope) stays
        # untouched for `attrition`/`_units_failed_anywhere` below — only this
        # execution's own `step_units` narrows.
        if fold_members is None or units is None:
            step_units = units
        elif execution.scope in ("run", "condition"):
            step_units = None  # no fold exists yet at these scopes
        elif execution.scope == "repeat":
            handed = _handed_keys(
                execution.repeat_label or "", {u.key for u in units}, fold_members
            )
            step_units = UnitList(
                [u for u in units if u.key in handed],
                train=UnitList([u for u in units if u.key not in handed]),
            )
        else:
            step_units = units  # "summary": every fold has already run
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
            failed = _units_failed_anywhere(results, units, fold_members)
            if resolved and len(failed) / resolved > max_failed_fraction:
                break
    return results

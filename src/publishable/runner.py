"""The execution loop. One execution at a time, in the recorded order."""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from publishable.artifacts import StepIO
from publishable.errors import ContractError
from publishable.replication import Repeat
from publishable.scope import Execution
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

    Both `completed` and `ineligible` are the INTERSECTION across the repeat-scoped
    executions of this step, in this condition, a unit was handed to — not the
    union. `completed` intersects because the collapse averages per unit, and a
    unit present in three of five seeds would otherwise enter that average on a
    different number of observations than its neighbours. `ineligible` intersects
    for the mirrored reason: eligibility is a property of the design, so a unit
    skipped in one repeat and completed (or simply unrecorded) in another did not
    get a consistent eligibility answer, and that inconsistency is exactly the
    `failed` case, not a design exclusion. Only a unit skipped in EVERY recording
    execution of this step, in this condition — a consistent answer — is
    `ineligible`.

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
        and (r.execution.condition_index or 0) == condition_index
    ]
    if not recording:
        return {"resolved": len(keys), "completed": 0, "ineligible": 0, "failed": len(keys)}
    completed = set(keys)
    for r in recording:
        completed &= r.recorded
    ineligible = set(keys)
    for r in recording:
        ineligible &= r.skipped
    return {
        # `resolved` always equals `len(io.units)` for the execution
        # (reference.md § "resolved counts what the execution was handed, not the
        # cohort"). It equals the full roster here only because S2 has no `fold` or
        # group axis that would narrow `io.units` below it — every execution is
        # handed the whole roster, so the two coincide. The day a fold or group
        # axis lands, this must become the union of what the recording executions
        # were actually given, not `len(keys)` unconditionally.
        "resolved": len(keys),
        "completed": len(completed),
        "ineligible": len(ineligible),
        "failed": len(keys) - len(completed) - len(ineligible),
    }


def _units_failed_anywhere(results: list[ExecutionResult], roster: "UnitList") -> set[str]:
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
    """
    keys = {u.key for u in roster}
    recording_steps = {
        r.execution.step_name for r in results if r.execution.scope == "repeat" and r.rows
    }
    failed: set[str] = set()
    for r in results:
        if r.execution.scope != "repeat" or r.execution.step_name not in recording_steps:
            continue
        failed |= keys - (r.recorded | r.skipped)
    return failed


def step_dir_for(run_dir: Path, execution: Execution, collapse_repeats: bool) -> Path:
    """Depth follows scope; degenerate levels collapse."""
    if execution.scope == "run":
        return run_dir / "shared" / execution.step_name
    if execution.scope == "summary":
        return run_dir / "summary" / execution.step_name
    base = run_dir
    if execution.condition_label is not None:
        base = base / "conditions" / (
            f"{execution.condition_index:02d}_{execution.condition_label}"
        )
    if execution.scope == "repeat" and not collapse_repeats and execution.repeat_label:
        base = base / execution.repeat_label
    return base / execution.step_name


def execute_plan(
    *,
    plan: list[Execution],
    run_dir: Path,
    input_dir: Path,
    cfg: Any,
    repeats: list[Repeat],
    digest: str,
    units: UnitList | None = None,
    max_failed_fraction: float | None = None,
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
        io = StepIO(
            step_dir=step_dir_for(run_dir, execution, collapse),
            input_dir=input_dir,
            run_dir=run_dir,
            units=units,
        )
        io.step_dir.mkdir(parents=True, exist_ok=True)
        recorded: frozenset[str] = frozenset()
        skipped: frozenset[str] = frozenset()
        rows: tuple[dict[str, Any], ...] = ()
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
            failed = _units_failed_anywhere(results, units)
            if resolved and len(failed) / resolved > max_failed_fraction:
                break
    return results

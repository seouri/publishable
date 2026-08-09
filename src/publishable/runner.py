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


def attrition(results: list[ExecutionResult], roster: "UnitList | None") -> dict[str, int]:
    """The four counts. A failed unit has no row anywhere, so failure is derived.

    Both `completed` and `ineligible` are the INTERSECTION across the repeat-scoped
    executions a unit was handed to — not the union. `completed` intersects because
    the collapse averages per unit, and a unit present in three of five seeds would
    otherwise enter that average on a different number of observations than its
    neighbours. `ineligible` intersects for the mirrored reason: eligibility is a
    property of the design, so a unit skipped in one repeat and completed (or simply
    unrecorded) in another did not get a consistent eligibility answer, and that
    inconsistency is exactly the `failed` case, not a design exclusion. Only a unit
    skipped in EVERY recording execution — a consistent answer — is `ineligible`.
    """
    if roster is None:
        return {"resolved": 0, "completed": 0, "ineligible": 0, "failed": 0}
    keys = {u.key for u in roster}
    recording = [r for r in results if r.execution.scope == "repeat"]
    if not recording:
        return {"resolved": len(keys), "completed": 0, "ineligible": 0, "failed": len(keys)}
    completed = set(keys)
    for r in recording:
        completed &= r.recorded
    ineligible = set(keys)
    for r in recording:
        ineligible &= r.skipped
    return {
        "resolved": len(keys),
        "completed": len(completed),
        "ineligible": len(ineligible),
        "failed": len(keys) - len(completed) - len(ineligible),
    }


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
            counts = attrition(results, units)
            if counts["resolved"] and counts["failed"] / counts["resolved"] > max_failed_fraction:
                break
    return results

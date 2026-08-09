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


@dataclass(frozen=True)
class ExecutionResult:
    execution: Execution
    status: str
    started_at: str
    wall_seconds: float
    returned: dict[str, Any]
    error: str | None


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
) -> list[ExecutionResult]:
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
        )
        io.step_dir.mkdir(parents=True, exist_ok=True)
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
    return results

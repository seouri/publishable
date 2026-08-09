"""Assemble run.yaml. Assembles only — computes nothing.

See docs/reference.md § The two files.
"""

from typing import Any

from publishable.runner import ExecutionResult

SCHEMA_VERSION = "1.0"


def run_status(results: list[ExecutionResult]) -> str:
    if not results:
        return "failed"
    if all(r.status == "completed" for r in results):
        return "completed"
    if any(r.status == "completed" for r in results):
        return "partial"
    return "failed"


def _execution_block(results: list[ExecutionResult]) -> dict[str, Any]:
    shared: dict[str, Any] = {}
    summary: dict[str, Any] = {}
    conditions: dict[int, dict[str, Any]] = {}
    for r in results:
        entry = {
            "status": r.status,
            "started_at": r.started_at,
            "wall_seconds": r.wall_seconds,
            "attempts": 1,
        }
        if r.error:
            entry["error"] = r.error
        e = r.execution
        if e.scope == "run":
            shared[e.step_name] = entry
        elif e.scope == "summary":
            summary[e.step_name] = entry
        else:
            index = e.condition_index or 0
            cond = conditions.setdefault(index, {"index": index, "label": e.condition_label,
                                                 "steps": {}})
            if e.scope == "condition":
                cond["steps"][e.step_name] = entry
            else:
                cond["steps"].setdefault(e.step_name, {})[e.repeat_label or ""] = entry
    return {
        "shared": shared,
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }


def _results_block(results: list[ExecutionResult]) -> dict[str, Any]:
    conditions: dict[int, dict[str, Any]] = {}
    summary: dict[str, Any] = {}
    for r in results:
        e = r.execution
        if e.scope == "summary":
            summary[e.step_name] = r.returned
            continue
        if e.scope == "run":
            continue
        index = e.condition_index or 0
        cond = conditions.setdefault(
            index, {"index": index, "label": e.condition_label, "per_repeat": {}}
        )
        if e.scope == "repeat":
            cond["per_repeat"].setdefault(e.step_name, {})[e.repeat_label or ""] = r.returned
        else:
            cond.setdefault("per_condition", {})[e.step_name] = r.returned
    return {
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }


def assemble_run_yaml(
    *,
    run_id: str,
    status: str,
    config: dict[str, Any],
    code_hash: str,
    parameters_hash: str,
    provenance: dict[str, Any],
    results: list[ExecutionResult],
    draft: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": status,
        "draft": draft,
        "config": config,
        "parameters_hash": parameters_hash,
        "code_hash": code_hash,
        "provenance": provenance,
        "execution": _execution_block(results),
        "results": _results_block(results),
    }

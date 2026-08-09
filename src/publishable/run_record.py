"""Assemble run.yaml. Assembles only — computes nothing.

See docs/reference.md § The two files.
"""

from typing import Any

from publishable.replication import Repeat
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


def _results_block(
    results: list[ExecutionResult],
    aggregated: dict[int, dict[str, dict[str, Any]]] | None,
) -> dict[str, Any]:
    # A "run"-scoped step's return has nowhere to land here (§ The two files gives
    # `results` only `conditions` and `summary`), and the same is true of a
    # "condition"-scoped step's return — both are dropped rather than given an
    # undocumented home. See docs/superpowers/spec-defects.md.
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
            index, {"index": index, "label": e.condition_label, "values": {}, "per_repeat": {}}
        )
        if e.scope == "repeat":
            cond["per_repeat"].setdefault(e.step_name, {})[e.repeat_label or ""] = r.returned
        # e.scope == "condition": the return is dropped; the condition's entry still
        # exists (with `values` and an empty/partial `per_repeat`) so its identity is
        # on record even though its own return is not.
    # `aggregated` is computed separately from `per_repeat` and placed beside it,
    # never inside it: `per_repeat` stays verbatim what the step returned, and no
    # derived value — an averaged column, a `basis`, an interval — ever appears
    # there. Recording both side by side is deliberate so a disagreement between
    # what a repeat returned and what the collapsed table reports is visible
    # rather than reconciled behind the user's back. `n` is not duplicated here:
    # `summarize_step` already embeds it per metric under `aggregated`, and
    # `reference.md` § "Every threshold..." / the condition-entry example never
    # shows a plain `n` beside `per_repeat` — inventing one here would be a
    # schema key the docs don't have.
    #
    # `aggregated` is keyed by condition index, and each condition receives ONLY
    # its own slice — never the same mapping object handed to another condition.
    # Core aggregates within each condition and never pools across conditions
    # (`reference.md` § Statistical reporting); sharing one object across two
    # condition entries would be that pooling by aliasing, invisible until a
    # reader noticed two conditions reporting identical numbers (or PyYAML's
    # `&id001`/`*id001` anchors gave it away). A condition absent from
    # `aggregated` gets its own empty mapping, not another condition's.
    if aggregated is not None:
        for index, cond in conditions.items():
            cond["aggregated"] = aggregated[index] if index in aggregated else {}
    return {
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }


def _layout_block(results: list[ExecutionResult], repeats: list[Repeat]) -> dict[str, bool]:
    """Which degenerate levels survived collapse, per `reference.md` § How artifacts
    are organized: "No sweep means no `conditions/` level; a single repeat means no
    repeat level ... The active layout is recorded in `run.yaml` so tooling can rely
    on it."

    Shape: `{"conditions": bool, "repeats": bool}`. `"conditions"` is `True` when any
    execution carries a real condition label (i.e. `sweep` produced more than the
    single unlabeled condition `run`/`command_run` always builds the plan with).
    `"repeats"` is `True` when more than one repeat was resolved — the same
    threshold `runner.execute_plan` uses to decide whether a repeat directory
    (`seed42/`, `fold03_seed17/`, ...) is created at all. A tool that wants to build
    a path into `<run_dir>/` can read these two booleans instead of re-deriving
    `runner`'s collapse rule from `sweep.yaml` and the repeat count.
    """
    has_conditions = any(r.execution.condition_label is not None for r in results)
    has_repeats = len(repeats) > 1
    return {"conditions": has_conditions, "repeats": has_repeats}


def assemble_run_yaml(
    *,
    run_id: str,
    status: str,
    config: dict[str, Any],
    code_hash: str,
    parameters_hash: str,
    provenance: dict[str, Any],
    results: list[ExecutionResult],
    repeats: list[Repeat],
    draft: bool = False,
    aggregated: dict[int, dict[str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    # There is no `counts` parameter here: `summarize_step` already embeds the
    # per-unit counts as `n` inside each metric under `aggregated`, and the
    # condition entry's documented shape (`reference.md`'s worked example) has no
    # plain `n` sibling to `per_repeat`. A parameter this function would only
    # discard is worse than not having it.
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "status": status,
        "draft": draft,
        "config": config,
        "parameters_hash": parameters_hash,
        "code_hash": code_hash,
        "provenance": provenance,
        "layout": _layout_block(results, repeats),
        "execution": _execution_block(results),
        "results": _results_block(results, aggregated),
    }

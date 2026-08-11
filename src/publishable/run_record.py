"""Assemble run.yaml. Assembles only — computes nothing.

See docs/reference.md § The two files.
"""

from typing import Any

from publishable.estimate import Estimate
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


def _summary_values(returned: dict[str, Any]) -> dict[str, Any]:
    """A summary step's return, with each `Estimate` expanded and every other
    value left exactly as it came back.

    `reference.md` § `Estimate` shows both in one block: the expanded
    `site_adjusted_delta` beside a bare `converged: true`. Only a value carrying
    an interval makes an attribution claim, so only that one gets `reported`.
    """
    out: dict[str, Any] = {}
    for key, value in returned.items():
        if isinstance(value, Estimate):
            out[key] = {
                "value": value.value,
                "reported": True,
                "ci95": value.ci95,
                "n": value.n,
                "method": value.method,
            }
        else:
            out[key] = value
    return out


def _results_block(
    results: list[ExecutionResult],
    aggregated: dict[int, dict[str, dict[str, Any]]] | None,
    condition_meta: dict[int, dict[str, Any]] | None = None,
    vs_baseline: dict[int, dict[str, dict[str, dict[str, Any]]]] | None = None,
    contrasts: list[dict[str, Any]] | None = None,
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
            summary[e.step_name] = _summary_values(r.returned)
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
    # `vs_baseline` is attached only to a condition that actually has one — a
    # comparison belongs to the non-baseline side, so the baseline condition
    # itself never gets the key, and neither does one with no metric in common
    # with the baseline. Absent, not `{}`: an empty block would claim a
    # comparison was made and found nothing (`contrasts.resolve_contrasts`'s
    # own docstring, and the regression three prior slices have landed).
    if vs_baseline is not None:
        for index, block in vs_baseline.items():
            if block:
                conditions.setdefault(
                    index,
                    {"index": index, "label": None, "values": {}, "per_repeat": {}},
                )["vs_baseline"] = block
    # `condition_meta` is what an `Execution` cannot carry: it holds `index`,
    # `label`, and `repeat_label`, but not `is_baseline` and not the swept
    # `values` — those facts have to arrive alongside `aggregated` rather than
    # be inferred from executions. It also fills in a condition that has no
    # `condition`- or `repeat`-scoped execution in `results` at all (an empty
    # grid axis, say), so its identity is still on record.
    #
    # `values` is filled here rather than left `{}`: `reference.md` § The two
    # files and § Statistical reporting both show the swept values on the
    # condition entry, and `run.yaml` is the file a paper attaches — a reader
    # of it alone must be able to say what each condition varied without
    # opening `sweep.yaml`, which is the plan rather than the record.
    if condition_meta is not None:
        for index, meta in condition_meta.items():
            cond = conditions.setdefault(
                index, {"index": index, "label": meta.get("label"), "values": {}, "per_repeat": {}}
            )
            cond["label"] = meta.get("label", cond.get("label"))
            cond["is_baseline"] = meta.get("is_baseline", False)
            cond["values"] = dict(meta.get("values") or {})
        for cond in conditions.values():
            cond.setdefault("is_baseline", False)
    out: dict[str, Any] = {
        "conditions": [conditions[k] for k in sorted(conditions)],
        "summary": summary,
    }
    # `contrasts` is declared `statistics.contrasts` entries — a comparison that
    # belongs to neither of its two sides, so it sits beside `conditions` rather
    # than inside one (`reference.md` § Contrasts: claims that aren't
    # condition-vs-baseline). Absent, not `[]`, for the same reason every other
    # comparison block here is: no declared contrast means nothing to report.
    if contrasts:
        out["contrasts"] = contrasts
    return out


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
    condition_meta: dict[int, dict[str, Any]] | None = None,
    vs_baseline: dict[int, dict[str, dict[str, dict[str, Any]]]] | None = None,
    contrasts: list[dict[str, Any]] | None = None,
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
        "results": _results_block(results, aggregated, condition_meta, vs_baseline, contrasts),
    }

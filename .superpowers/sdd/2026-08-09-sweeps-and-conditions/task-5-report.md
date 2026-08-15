# Task 5 report: per-condition `cfg`, and the swept-parameter refusal

## What was done

- `src/publishable/config.py`: added `SweptAway` and made `Node.__getattr__` raise
  `ContractError(code="E-STEP-SWEPT-PARAM")` the moment it resolves one, so the
  refusal fires on the read itself rather than on a later attribute access.
- `src/publishable/runner.py`: added `resolve_condition_cfg(base, values) -> Config`
  (overlay a condition's swept values onto a deep-copied base) and
  `resolve_wide_cfg(base, swept_paths) -> Config` (replace swept leaves with
  `SweptAway` for `run`/`summary` scope). `execute_plan` now takes
  `cfgs: dict[int, Any]` instead of `cfg: Any`, and selects
  `cfgs[execution.condition_index if ... is not None else -1]` per execution.
- `src/publishable/cli.py`: updated its one call site to
  `cfgs={0: Config(doc), -1: Config(doc)}`.
- `tests/test_runner.py`: updated every existing `execute_plan` call site to the
  new `cfgs=` shape (two-condition fixtures now key both `0` and `1`, since
  those plans have no wide-scope executions and no `-1` need arise). Added:
  `test_each_condition_sees_its_own_parameter_value`,
  `test_a_condition_scoped_step_also_sees_its_own_value` (condition scope, not
  just repeat — a different `build_plan` branch and `step_dir_for` path),
  `test_a_run_scoped_step_cannot_read_a_swept_parameter`,
  `test_a_summary_scoped_step_cannot_read_a_swept_parameter`,
  `test_an_unswept_path_reads_normally_at_every_scope` (parametrized over all
  four scopes, not just `run`), and `test_per_condition_cfgs_are_not_the_same_object`
  (asserts the nested `analysis` dict is not shared between the two `Config`s,
  and that the shared `BASE_PARAMS` fixture is untouched afterward — a bare
  `cfg0 is not cfg1` would pass even with a shared nested dict).

## Verification

`uv run pytest -v` — 382 passed. `uv run ruff check .` — all checks passed.
`uv run mypy` — no issues found in 33 source files. Confirmed
`docs/reference.md` § "Mistakes core prevents" already lists
`E-STEP-SWEPT-PARAM` as a `ContractError` (read-time), consistent with this
implementation — no doc change needed. Confirmed `cli.py`'s `parameters_hash`,
`design_digest`, and `assemble_run_yaml` all take the original `doc` dict, never
a resolved `Config`, so a `SweptAway` marker can never reach `yaml.safe_dump`.

## Coordinator rulings, applied

**1. `resolve_wide_cfg`/`resolve_condition_cfg` asymmetry — resolved by making
`resolve_wide_cfg` symmetric, planting the marker.** Changed `resolve_wide_cfg`
to walk with `setdefault` exactly as `resolve_condition_cfg` does, so a swept
path whose parent is absent from `base` still gets the `SweptAway` marker
planted rather than silently skipped. Added
`test_resolve_wide_cfg_plants_the_marker_even_when_the_parent_is_absent`,
asserting the read raises `E-STEP-SWEPT-PARAM` even when `base` starts as
`{"parameters": {}}`. Docstring on `resolve_wide_cfg` now states why planting
is the safe direction: skipping leaves the value readable at `run`/`summary`
scope, which is precisely the failure `E-STEP-SWEPT-PARAM` exists to prevent.

**2. Missing `cfgs` key — kept fatal, made explicit.** `execute_plan` now
checks `cfg_key not in cfgs` before entering the per-execution `try`, and
raises `ContractError(code="E-RUN-CFG-MISSING")` naming the missing condition
index and the step/scope that needed it, rather than letting a bare `KeyError`
surface. This check deliberately stays outside the `try` — it is not a step
failure but core having built an inconsistent plan, so it must abort the whole
`execute_plan` call rather than being absorbed as one failed execution. Added
`test_execute_plan_raises_explicitly_when_a_cfg_is_missing`. Note:
`E-RUN-CFG-MISSING` isn't yet listed in `docs/reference.md`'s error registry,
but neither is the pre-existing `E-RUN-SEED-MISSING` this mirrors — consistent
with existing practice in this codebase, not a new gap introduced here.

**3. CLI wiring inert until Task 8 — acknowledged, no action taken.**
Coordinator confirmed Task 8 wires `sweep.expand` and `resolve_*_cfg` into
`cli.py` and carries the end-to-end acceptance test. Nothing changed here
beyond leaving the unit-level tests in place.

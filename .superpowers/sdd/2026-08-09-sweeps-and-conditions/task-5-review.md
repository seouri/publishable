# Task 5 review

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## Findings

None Critical or Important. Everything the brief specifies is present and correctly wired:

- `SweptAway` lives in `config.py`; `Node.__getattr__` checks `isinstance(value, SweptAway)` and raises `ContractError(code="E-STEP-SWEPT-PARAM")` *before* `_wrap`, so the raise fires on the read itself, under the identifier that was actually accessed — not a later attribute access on a returned sentinel (`src/publishable/config.py:91-98`).
- `resolve_wide_cfg` now walks with `setdefault` and plants the marker unconditionally, matching ruling 1 exactly; the new test (`tests/test_runner.py:510-519`) proves it for the case that mattered — parent absent from `base` — by asserting the read still raises `E-STEP-SWEPT-PARAM` rather than reading through. A `.get()`/`break` version (the pre-fix code) would make that test's `cfg.parameters.analysis.method` read raise `E-STEP-PARAM-UNKNOWN` or return normally instead of `E-STEP-SWEPT-PARAM` — the diff's `_ = cfg.parameters.analysis.method` under `pytest.raises` would fail on wrong code.
- The missing-`cfgs`-key check sits outside the per-execution `try` in `execute_plan` (`src/publishable/runner.py:222-236`), raising `ContractError(code="E-RUN-CFG-MISSING")` and propagating out of `execute_plan` rather than being recorded as one failed execution. `test_execute_plan_raises_explicitly_when_a_cfg_is_missing` (`tests/test_runner.py:522-550`) asserts `pytest.raises(ContractError)` around the whole call — if the check were inside the `try`, or a bare `KeyError` were left uncaught-but-swallowed, this test would either see a different exception type or see `results` returned instead of a raise.
- Aliasing: `resolve_condition_cfg`/`resolve_wide_cfg` both `copy.deepcopy(base)` before mutating. `test_per_condition_cfgs_are_not_the_same_object` (`tests/test_runner.py:495-507`) specifically asserts `cfg0.raw["parameters"]["analysis"] is not cfg1.raw["parameters"]["analysis"]` and that `BASE_PARAMS == before` afterward — a shallow-copy or in-place-mutate version (mutating `base` directly, or copying only the top dict) would fail this: either the nested dicts would be identical objects, or the shared fixture would show cross-condition contamination (e.g. both ending up `"spearman"`).
- `cfg` dot-access properties survive: no methods added to `Node`/`Config`; `AttributeError` on `_`-prefixed names and `ContractError`/`E-STEP-PARAM-UNKNOWN` on unknown paths are both untouched by the diff, only a new branch inserted between the "path exists" check and `_wrap`.
- `scope` continues to be read from the class (`Reads.scope = scope` set directly on the class in the parametrized test, per spec's "scope read from class before any instance exists").
- No leak path for `SweptAway` found: it is only ever placed at a dict leaf (never inside a list element, since `swept_paths` are dotted leaf paths under `parameters`, and `_wrap` only recurses into `dict`/`list` — a `SweptAway` at a leaf is caught by the `isinstance` check before `_wrap` ever sees it). `cli.py`'s `parameters_hash`, `design_digest`, and `assemble_run_yaml` all hash the original `doc`, never a resolved `Config`, so a marker can't reach a hash or the run record through this code path. This isn't exercised by a new automated test, but it's a static property of the code (grep-confirmed: `resolve_wide_cfg`'s only caller in this diff is the test file — S2's `cli.py` call site never builds a wide cfg with markers, since there's no sweep yet).
- CLI wiring (`cfgs={0: Config(doc), -1: Config(doc)}`) intentionally passes the same `doc` object to both `Config` instances rather than deep-copying — harmless today since `Node`/`Config` never mutate `_data`, and Task 8 (per the brief) is what actually exercises sweep + CLI together. Worth a note if Task 8's wiring instead calls `resolve_condition_cfg`/`resolve_wide_cfg` (which do deep-copy) rather than reusing this pattern, but not a defect in this task's scope.

## Minor / style notes (non-blocking)

- `E-RUN-CFG-MISSING` isn't yet in `docs/reference.md`'s error registry; the report flags this and correctly notes `E-RUN-SEED-MISSING` has the same pre-existing gap, so this isn't a new inconsistency introduced by this task.
- `resolve_condition_cfg` and `resolve_wide_cfg` both do `import copy` at module scope now (via the top-level `import copy` added to `runner.py`), consistent with the rest of the file's import style.

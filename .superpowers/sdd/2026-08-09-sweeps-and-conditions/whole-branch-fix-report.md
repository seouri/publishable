# Whole-branch fix report — S3a, `s3a-sweeps-and-conditions`

Against `whole-branch-review.md` at `b1d6c15`. All seven findings closed, plus the one
record-only item. 428 tests passing (414 pre-existing, unchanged, + 14 new), ruff clean,
mypy clean.

The six code findings had one cause and are fixed as one change: **a path fixed by
`sweep.baseline` was expanded into condition `00` and then treated everywhere else as if it
did not exist** — never validated, never marked swept, never recorded.

---

## 1. CRITICAL — `swept_paths` is grid keys only · `cli.py`

`swept_paths` now unions the baseline's keys with the grid's:

```python
sweep_block = doc.get("sweep") or {}
swept_paths = set(sweep_block.get("grid") or {}) | set(sweep_block.get("baseline") or {})
```

A path `sweep.baseline` fixes varies across conditions by definition — condition `00` uses the
baseline's value, every other condition the base config's — so `resolve_wide_cfg` now plants a
`SweptAway` marker for it and a `run`/`summary`-scoped step reading it gets
`E-STEP-SWEPT-PARAM` instead of a value no condition used.

**Test:** `test_a_run_scoped_step_reading_a_baseline_only_path_is_refused`
(`tests/test_acceptance.py`) — a real `run` on the reviewer's repro config (baseline fixes both
axes, grid fixes only `min_samples`), asserting `EXIT_PARTIAL` and `E-STEP-SWEPT-PARAM` in
`run.yaml`'s `execution.shared` entry. Verified to fail against the pre-fix line.

## 2. CRITICAL — `_check_sweep` iterates `grid` only · `validate.py`

The per-entry body of the grid loop is factored into two closures inside `_check_sweep` —
`_path_resolves` (`E-SWEEP-PATH-UNKNOWN`, with the `difflib` hint) and `_value_checks`
(`Param.check` → `E-PARAM-VALUE`, and `check_swept_value` → `E-SWEEP-VALUE-UNNAMEABLE`) — and
both `grid` and `baseline` call the same implementation. A baseline entry is a single value, not
a list, so it is checked once at path `sweep.baseline.<path>` rather than `[i]`-indexed.

**Deviation from the brief, taken deliberately:** the brief asked for all three checks on
baseline entries; the review's own fix note says nameability "does not apply, since a baseline's
label is the literal `baseline`". I followed the review. `sweep.label_for` returns `"baseline"`
when `is_baseline` is true, so a baseline's fixed values are never rendered into a label — and
that stays true under the per-cell expansion of item 4, which labels a per-cell baseline by the
axes it leaves *free* (`reference.md`:1419 row 2). Applying `check_swept_value` there would
refuse a constructible legal config: `baseline: {analysis.method: pearson, prompt.text: "a long
sentence"}` beside `grid: {analysis.method: [...]}` fixes every grid axis (so item 4 permits it)
and never renders `prompt.text` anywhere. `reference.md`:218's row — "Baseline is a valid
condition | `sweep.baseline` sets `analysis.method: pearsonn`" — is a *value* check, which is
implemented. `nameable` is an explicit parameter of `_value_checks` so the decision is visible
at both call sites rather than implied by omission.

**Tests:** `test_a_baseline_path_must_be_a_real_parameter`,
`test_a_baseline_value_must_satisfy_its_param`,
`test_a_baseline_value_is_not_subject_to_the_nameability_check` (`tests/test_validate.py`). The
last of those uses `baseline: {analysis.method: "pear son"}` beside a grid on the same axis: a
value `check_swept_value` actually refuses, fixing every grid axis so item 4 stays silent. It
asserts both halves on the one config — `E-PARAM-VALUE` fires, `E-SWEEP-VALUE-UNNAMEABLE` does
not — and was verified to fail when `nameable=True` is passed at the baseline call site.

## 3. IMPORTANT — a non-mapping `sweep.grid`/`sweep.baseline` escapes as a traceback · `validate.py`

`_check_shape` now descends into `sweep` beside `data.units` and `replication.repeats`:
`sweep.baseline` must be a mapping, `sweep.grid` must be a mapping, and each
`sweep.grid.<path>` must be a list. All three report `E-CONFIG-SHAPE`, and all three use the
`is not None and not isinstance(...)` form, so a key present but `null` stays "absent" —
matching `doc.get("x") or {}` everywhere else in the module. `validate` collects and reports;
it no longer raises out of `main` for any of these shapes.

The per-axis `list` check closes the quieter symptom in the same place: a bare string axis
(`grid: {analysis.method: spearman}`, brackets forgotten) is iterable, so it expanded character
by character into one condition per letter — clean, on any template with an unconstrained `str`
`Param`.

**Tests:** `test_a_list_grid_is_a_diagnostic_not_a_traceback`,
`test_a_list_baseline_is_a_diagnostic_not_a_traceback`,
`test_a_bare_string_axis_is_refused_rather_than_expanded_per_character`,
`test_a_null_grid_or_baseline_is_absent_not_malformed`.

## 4. IMPORTANT — the per-cell baseline: REFUSED, not implemented · `validate.py`

New identifier **`E-SWEEP-BASELINE-PARTIAL`**, emitted from `_check_unimplemented` at path
`sweep.baseline` when a truthy `baseline` leaves any declared `grid` axis unfixed. The message
names the free axes and is in the same register as the four `-UNSUPPORTED` messages beside it
("specified but not implemented in this build … will be honored in a later slice").

Grepped `docs/reference.md` for `E-SWEEP-BASELINE-PARTIAL`, `E-SWEEP-BASELINE`, and
`E-SWEEP-PARTIAL` before minting; the document names no `E-SWEEP-*` identifier at all, so there
is no registry collision.

The predicate is `baseline and [p for p in grid if p not in baseline]`, so the supported row is
untouched in all three of its shapes: a baseline fixing every axis (the slice's worked example),
a bare baseline with no grid, and `baseline: {}` beside a grid — which declares nothing, yields
no baseline condition, and is therefore not a partial baseline.

Recorded in `docs/superpowers/spec-defects.md` § New error identifier:
`E-SWEEP-BASELINE-PARTIAL`, naming `reference.md`:1415-1422 as the specified behavior this build
refuses, and saying to retire the identifier when per-cell expansion lands.

**Tests:** `test_a_baseline_that_leaves_a_grid_axis_free_is_refused` (asserts the code, the named
free axis, and the register of the message), plus the three negatives
`test_a_baseline_fixing_every_axis_is_supported`,
`test_a_bare_baseline_with_no_grid_is_supported`,
`test_an_empty_baseline_beside_a_grid_is_not_a_partial_baseline`.

## 5. IMPORTANT — `sweep.yaml` written after `execute_plan` · `cli.py`

A line move, unchanged: the `order`/`execution_order` derivation and the `write_text` now sit
immediately above `execute_plan`, still inside the `RunLock` and still written from `cli.py`
(the adjudicated exception to "`artifacts.py` is the only writer" — only the *when* changed).
Nothing in `sweep_document` derives from `results`.

**Test:** `test_sweep_yaml_is_written_before_the_first_execution`. The fatal is *injected*
(`monkeypatch` on `cli.execute_plan`) rather than induced, because neither `E-RUN-CFG-MISSING`
nor `E-RUN-SEED-MISSING` is reachable through `command_run` — `cfgs` is built from the same
`conditions` the plan is, so it is always complete. The ordering is what is under test, not the
specific fatal, and the test says so.

## 6. IMPORTANT — `results.conditions[i].values` is always `{}` · `cli.py`, `run_record.py`

`condition_meta` now carries `"values": dict(c.values)` alongside `label` and `is_baseline`, and
`_results_block`'s `condition_meta` loop copies it onto the condition entry. The `dict(...)`
unwraps `Condition.values`'s `MappingProxyType`, which `yaml.safe_dump` has no representer for
— the same reason `sweep_document` already does it. Setting it in that loop rather than at
either `setdefault` covers both construction paths, since the loop runs for every condition.

**Test:** `test_run_yaml_records_what_each_condition_varied` — a real run, asserting
`run.yaml`'s three `values` mappings and their `is_baseline` flags.

## 7. MINOR — `(condition_index or 0)` in the two anti-pooling functions

`runner.attrition` and `stats.collapse_repeats` now compare `r.execution.condition_index ==
condition_index` strictly, matching `cli.py`'s `recording_steps`. Dead today, but `or 0` inside
the two functions whose required `condition_index` exists to make pooling unwritable would have
silently attributed a stray `None` to condition 0. Both carry a comment saying so.

`run_record._execution_block` and `_results_block` keep their `e.condition_index or 0`: those
two *must* place a condition-less execution somewhere in the record, and dropping it would lose
it from `run.yaml` entirely. Different job, deliberately unchanged.

---

## Recorded, not fixed

`artifacts.StepIO.read_upstream` hard-codes `run_dir / "shared" / step / name`, so a
`repeat`-scoped step reading a `condition`-scoped one fails every execution although the
direction is legal. Pre-existing, newly advertised by S3a's `SCOPE_ORDER` direction check.
Entered in `docs/superpowers/spec-defects.md` § `io.read_upstream` can only reach `run`-scoped
steps — MARKED FOR THE NEXT SLICE, against `reference.md`:1083, with the note that the fix must
route through the same helper `runner.step_dir_for` uses rather than compose a second copy of
the layout.

## Constraints held

`sweep.py` and `stats.py` unchanged in their imports and still pure — no filesystem, no runtime
import of `config`/`artifacts`/`runner`/`cli`; `sweep.py` was not touched at all (every fix
landed in `validate.py`, `cli.py`, `run_record.py`, `runner.py`, `stats.py`). `artifacts.py`
untouched. No new dependency. ruff (line-length 100, `E,F,I,UP,B`) and mypy strict both clean.
Every new `E-`/`W-` identifier — one, `E-SWEEP-BASELINE-PARTIAL` — has a test that produces it.

## Verification

```
uv run pytest -q     428 passed
uv run ruff check .  All checks passed!
uv run mypy          Success: no issues found in 33 source files
```

Regressions the reviewer flagged, re-checked: `test_a_single_condition_run_is_unchanged` (no
`conditions/` level), `test_no_sweep_at_all_still_validates_clean`,
`test_a_normal_baseline_plus_grid_config_still_validates_clean`, and
`tests/test_runner.py`'s bare-baseline `conditions/00_baseline/seed17/analyze` assertion all
pass unmodified. No pre-existing test was edited.

Nothing was left open, and no item needed a design decision beyond the one recorded under
finding 2.

# Whole-branch review — S3a, `s3a-sweeps-and-conditions`

Range `152f0bf..b1d6c15` · 16 commits · 14 files · ~1650 insertions.
At HEAD: 414 passed, ruff clean, mypy clean. Verified independently; the working tree is clean
and every probe below was run and then deleted.

**Verdict: findings — not ready to merge.** Two Critical, four Important, one non-blocking
divergence, six parked minors (none blocking).

The slice's core mechanics are sound. Per-condition isolation is genuinely closed (§ Target 2),
`correction: null` holds on every metric-writing path (§ Target 3), the single-condition tree is
unchanged and the bare-baseline level is asserted (§ Target 4), and `sweep.py`/`stats.py` are
pure (§ Target 5). Every finding below is in one place: **`sweep.baseline` is expanded but never
validated, never treated as a swept path, and never recorded** — and one ordering bug in when
`sweep.yaml` is written.

---

## What was verified clean

### Target 2 — cross-condition pooling: closed, and closed on a *varied* fixture

The existing acceptance fixture has exactly one recording step in every condition — the same
shape that let the previous slice's Critical hide from two clean per-task reviews. So the fixture
shape was varied rather than the assertions: **two** repeat-scoped recording steps, one whose
skip count depends on the condition (`pearson`→0, `spearman`→4, `kendall`→9) and one whose skip
count is constant (10 of 40), over a 40-unit shared roster, 3 conditions × 5 seeds.

Observed in `run.yaml`:

| Condition | `step01.score` | `step01` n | `step02.other` | `step02` n |
|---|---|---|---|---|
| `00_baseline` | 1.0 | 40/40/0 | 7.0 | 40/30/10 |
| `01_method=spearman` | 2.0 | 40/36/4 | 7.0 | 40/30/10 |
| `02_method=kendall` | 3.0 | 40/31/9 | 7.0 | 40/30/10 |

(`resolved`/`completed`/`ineligible`.) Each step's attrition tracks *its own* skips within *its
own* condition; the condition-varying step does not contaminate the constant one, and no
condition's `n` leaks into another's. `runner.attrition` (runner.py:79-82) and
`stats.collapse_repeats` (stats.py:94-98) both filter on `condition_index`, `cli.py:205-210`
scopes `recording_steps` the same way, and `run_record._results_block` hands each condition its
own `aggregated` slice (run_record.py:103-105). `_units_failed_anywhere` (runner.py:106) is the
one deliberate cross-condition union, correctly documented as the run-level
`max_failed_fraction` denominator rather than an `n`.

### Target 3 — the record does not overclaim

`summarize_step` (stats.py:159-170) is the **only** path in `src/` that emits a metric mapping —
`grep -rn "basis" src/` returns it alone, and `aggregated` is written from nowhere else
(`cli.py:211`, `run_record.py:105`). So `correction: None` is unconditional on every metric, not
just the common one. `W-STATS-FAMILY` fires at `len(conditions) > 1` (validate.py:576) and was
observed in every multi-condition probe run.

### Target 4 — single-condition regression

`step_dir_for` gates the level on `condition_label is not None` (runner.py:148), not on a count.
No-sweep run: no `conditions/` directory (`test_a_single_condition_run_is_unchanged`). Bare
`sweep.baseline` with no grid: `tests/test_runner.py:100-111` asserts
`conditions/00_baseline/seed17/analyze` **exists** — the "declared, not N > 1" rule, correctly
pinned. `baseline: {}` alongside a grid yields no baseline condition and `is_baseline` nowhere
true, which is consistent with this repo's "present but empty is not a declaration" convention
elsewhere (`_check_shape`'s docstring, `sweep.get(mode)` truthiness) and is not a finding.

### Target 5 — module boundaries

`sweep.py` imports only `itertools`, `re`, `collections.abc`, `dataclasses`, `types`, `typing`,
plus `replication.Repeat` under `TYPE_CHECKING`. `stats.py` imports only stdlib, `scipy`, plus
`runner.ExecutionResult` under `TYPE_CHECKING`. Neither touches `Path` or the filesystem.
`artifacts.py` importing `sweep.condition_dir_name` at runtime is fine — the dependency runs
impure → pure. `sweep.yaml`'s write from `cli.py` is the adjudicated pre-existing exception and
is not re-reported (but see **H**, which is about *when*, not *where*).

---

## Findings

### CRITICAL 1 — a baseline-only swept path stays readable at `run`/`summary` scope
`src/publishable/cli.py:115`

`swept_paths = set((doc.get("sweep") or {}).get("grid") or {})` — the grid keys only.
`resolve_wide_cfg` therefore plants a `SweptAway` marker for grid paths and **not** for a path
`sweep.baseline` fixes. A baseline path is a value that varies across conditions by definition,
so a `run`- or `summary`-scoped step reading it gets exactly the value
`E-STEP-SWEPT-PARAM` exists to withhold.

Reproduced end to end, on a config that satisfies reference.md:1419 row 1 (the baseline fixes
every grid axis, so this is **not** a consequence of Important 2):

```yaml
parameters: {analysis: {method: kendall, min_samples: 30, ...}}
sweep:
  baseline: {analysis.method: pearson, analysis.min_samples: 10}
  grid:     {analysis.min_samples: [10, 20]}
```

A `run`-scoped step doing `return {"seen": cfg.parameters.analysis.method}` returns
`kendall` — a value **no condition in the run used** (condition 0 used `pearson`, conditions 1
and 2 used the base value only because nothing overrode it). Exit 0, `status: completed`, the
wrong value on the record. This is the design spec's own stated failure mode
(§ The central new mechanic: "silently wrong for every condition but one") reached through the
supported path.

**Fix:** one line — union the grid keys with the baseline keys:
`swept_paths = set(grid) | set(sweep.get("baseline") or {})`. It is independent of whatever is
decided for Important 2.

### CRITICAL 2 — `sweep.baseline` is not validated at all
`src/publishable/validate.py:528-554`

`_check_sweep` iterates `sweep.get("grid")` and nothing else. `sweep.baseline`'s dotted paths are
never checked against `template.parameter_spec`, and its values are never run through
`Param.check` or `check_swept_value`.

Reproduced: `sweep: {baseline: {analysis.methd: pearsonn}, grid: {analysis.method: [spearman,
kendall]}}` validates with **only** `W-STATS-FAMILY` — no `E-SWEEP-PATH-UNKNOWN`, no
`E-PARAM-VALUE`. `resolve_condition_cfg` (runner.py:166-171) then walks with `setdefault` and
creates `parameters.analysis.methd = "pearsonn"`, a key no step reads, while
`parameters.analysis.method` keeps the base value. Condition `00_baseline` executes the base
config under a label claiming otherwise, and the run reports success.

The document already requires this check by name: `docs/reference.md:218`, in the § Validation
table — **"Baseline is a valid condition | `sweep.baseline` sets `analysis.method: pearsonn`"**.
This is a code defect, not a document gap; `reference.md` is right.

**Fix:** factor the per-path/per-value body of the `grid` loop and run it over
`sweep.baseline`'s items too (path in `spec`, `spec[path].check(value)`; the nameability check
does not apply, since a baseline's label is the literal `baseline`).

### IMPORTANT 1 — a malformed `sweep.grid`/`sweep.baseline` crashes `validate` with a traceback
`src/publishable/validate.py:528`, `src/publishable/sweep.py:143`

`_check_shape` (validate.py:86-105) descends into `data.units`, `data.units.attributes`, and
`replication.repeats[*]` but not into `sweep`'s sub-keys. `_check_sweep` then calls
`grid.items()` and `expand` calls `dict(baseline)` on whatever is there.

- `sweep: {grid: [analysis.method]}` → `AttributeError: 'list' object has no attribute 'items'`
- `sweep: {baseline: [analysis.method], grid: {...}}` → `ValueError: dictionary update sequence
  element #0 has length 15; 2 is required`

`cli.main` catches only `PublishableError` and `OSError` (cli.py:351-368), so both escape as a
bare traceback rather than a diagnostic — the exact thing the `E-CONFIG-SHAPE` guard exists to
prevent. **This surface is new to this branch**: at `152f0bf`, `E-SWEEP-UNSUPPORTED` refused any
sweep block before `.items()` was ever reached (`git show 152f0bf:src/publishable/validate.py`,
line 398).

The same `isinstance` gap admits a second, quieter version: an axis written as a bare string
(`grid: {analysis.method: spearman}` — forgotten brackets) is iterated character by character
and expands to eight one-character conditions. Today the core `generic` template constrains
every parameter, so `E-PARAM-VALUE` fires eight times and blocks the run; a plugin template with
an unconstrained `str` `Param` would get the per-character expansion clean.

**Fix, one place:** add `sweep.baseline` (mapping), `sweep.grid` (mapping), and each
`sweep.grid.<path>` (list) to `_check_shape`'s nested section, beside `replication.repeats`.
Both symptoms close together.

### IMPORTANT 2 — a baseline that leaves a grid axis free is neither expanded per cell nor refused
`src/publishable/sweep.py:143-145`

`docs/reference.md:1415-1422` states one rule with two cases: *"the baseline expands over
whichever axes it doesn't fix"*, giving **one baseline condition per cell of the unfixed axes**.
`expand` unconditionally prepends exactly one `00_baseline` row carrying only the values the
baseline literally names.

Reproduced: `baseline: {analysis.method: pearson}`, `grid: {analysis.min_samples: [10, 20]}`
validates clean (only `W-STATS-FAMILY`) and expands to
`[(0, baseline, {method: pearson}), (1, min_samples=10, ...), (2, min_samples=20, ...)]` — one
baseline that doesn't fix `min_samples` at all, rather than the two per-cell baselines the
document specifies. The declared design is not the executed design, and nothing says so.

The design spec scoped S3a to "`sweep.baseline` prepended as condition `00`" — row 1 only — but
listed no refusal for row 2, so it fell through the "unimplemented must mean refused" rule that
governs this slice. Either implement the per-cell expansion or refuse a baseline that does not
fix every declared grid axis (`E-SWEEP-BASELINE-PARTIAL`, S3b to retire it). Refusing is the
smaller change and matches how the four unimplemented modes are handled.

### IMPORTANT 3 — `sweep.yaml` is written *after* the run, not before it
`src/publishable/cli.py:179` (relative to `execute_plan` at `cli.py:162`)

`docs/reference.md:486` is explicit: *"Written before the first execution, from the config and
the design digest"*, and § The other files a run writes calls it *"settled before the first
execution and never touched again"*, with `resume` reading it back rather than re-deriving it.
The call sits below `execute_plan`, so a run that dies inside the loop — `E-RUN-SEED-MISSING`
(runner.py:253) or `E-RUN-CFG-MISSING` (runner.py:291), both deliberately outside the
per-execution `try` and both propagating through the `RunLock` — leaves a run directory with
`executions.jsonl` and **no `sweep.yaml`**, which is the one input `resume` is specified to read.

Note the ledger's adjudicated item is that `sweep.yaml` is written *from `cli.py` rather than
`artifacts.py`*. That is about *where*; this is about *when*, and it is not covered.

**Fix:** move the write above `execute_plan`. Nothing in `sweep_document(conditions, repeats,
digest, order, execution_order)` derives from `results` — `execution_order` is built from `plan`
(cli.py:176-178), which exists at cli.py:116. It is a line move, unchanged.

### IMPORTANT 4 — `results.conditions[i].values` is always `{}` in `run.yaml`
`src/publishable/run_record.py:77` and `:115`, fed by `cli.py:194-196`

`condition_meta` carries `label` and `is_baseline` only, and both `setdefault` sites hard-code
`"values": {}`. Observed in every probe run: three conditions, three empty `values` mappings.

`docs/reference.md:393` and the § Statistical reporting example at `:1948-1950` both show
`values: {analysis.method: spearman}` on the condition entry. `run.yaml` is the file a paper
attaches; a reader of it alone cannot say what any condition actually varied, and must open
`sweep.yaml` — which the document positions as the *plan*, with `run.yaml` as the record.
(The label carries it informally, which is why this is Important rather than Critical.)

**Fix:** put `values` in `condition_meta` at cli.py:195 and copy it through in
`_results_block`, exactly as `is_baseline` already is.

### NON-BLOCKING — `io.read_upstream` can only reach `run`-scoped steps
`src/publishable/artifacts.py:416`

`docs/reference.md:1083`: *"a narrower step reads wider ones via `io.read_upstream(step, name)`
regardless of scope."* The implementation hard-codes `self.run_dir / "shared" / step / name`,
which is where only `run`-scoped steps write (runner.py:143). Reproduced: a `repeat`-scoped step
calling `io.read_upstream("step00_fit", "model.json")` on a `condition`-scoped step fails every
execution — exit 3, `status: partial`.

Pre-existing at `152f0bf`, and **not** caused by this branch. It is listed here because S3a is
what makes it load-bearing: the new `SCOPE_ORDER` direction check (artifacts.py:409) explicitly
permits `condition` → `repeat` reads, advertising a path that cannot resolve, and the
`conditions/` level is what a correct resolution now has to account for. The summary case is
covered by the new `io.read_condition`, so the live blast radius is repeat→condition only.

**Recommendation:** do not fix in this branch. Add an entry to
`docs/superpowers/spec-defects.md` naming reference.md:1083 and this path, so S3b picks it up
with the fold work that reshapes `step_dir_for` anyway.

---

## Triage of the parked minors

| Ledger entry | Call |
|---|---|
| `label_for`'s `keys.get()` fallback branch is dead | **Carry.** Defensive, cheap, and correct if `expand` ever calls it differently. |
| Refusal messages read as subjectless fragments | **Carry.** House-style sweep across all `-UNSUPPORTED` messages at once, including the pre-existing `cluster_by` one; piecemeal is worse. |
| No test declares two unimplemented sweep modes at once | **Carry.** The four branches at validate.py:397-424 are independent `if`s over a literal tuple; there is no interaction to exercise. |
| `_repeat_total` duplicates `_check_replication`'s n-falls-back-to-k shape | **Carry.** The two have genuinely different error semantics (one reports `E-REPL-N`, the other must stay permissive); sharing them would couple a warning to an error. |
| No dedicated test for the bare-baseline-only case | **Closed already.** `tests/test_runner.py:100-111` asserts `conditions/00_baseline/seed17/analyze` exists. |
| `sweep.yaml` written from `cli.py` rather than `artifacts.py` | **Carry** as adjudicated — but see Important 3, which is a different defect about ordering. |

One minor not in the ledger, worth folding into the Critical 1 fix:

- **`condition_index` normalization is inconsistent.** `runner.attrition:81` and
  `stats.collapse_repeats:97` compare `(r.execution.condition_index or 0) == condition_index`,
  while `cli.py:208`'s `recording_steps` uses a strict `==`. Dead today — `build_plan`
  (scope.py:63-68) always gives a `condition`/`repeat` execution a real `int`. But the `or 0`
  lives inside the two functions whose entire reason for taking a required `condition_index` is
  making pooling unwritable, and it would silently attribute a future `None` to condition 0.
  Prefer a strict `==` in all three, so an unexpected `None` raises or drops out rather than
  coercing into the baseline's bucket.

---

## Re-review

Range `b1d6c15..f3158e2` · 2 commits · 7 files · +375/−39, of which **zero** are deletions in
`tests/` — no pre-existing test was edited or removed. At `f3158e2`: 428 passed, ruff clean,
mypy clean (33 files), working tree clean and every probe below reverted.

**Verdict: ready to merge.** All seven findings closed, six of them killed by mutation. The
seventh is closed and correct but unpinnable by construction, which is stated rather than
papered over. No new Critical or Important finding.

### Mutation battery — each fix reverted in place, suite re-run, source restored

The interesting column is "test that died". A fix with no killer is a fix that would survive
being reverted.

| Reverted to the pre-fix behavior | Suite | Test that died |
|---|---|---|
| `swept_paths` back to grid keys only | 1 failed | `test_a_run_scoped_step_reading_a_baseline_only_path_is_refused` |
| `_check_sweep`'s baseline loop removed | 1 failed | `test_a_baseline_value_must_satisfy_its_param` |
| `_check_shape`'s `sweep` section removed | 1 failed | `test_a_list_grid_is_a_diagnostic_not_a_traceback` |
| `E-SWEEP-BASELINE-PARTIAL` predicate forced false | 1 failed | `test_a_baseline_that_leaves_a_grid_axis_free_is_refused` |
| `sweep.yaml` write moved back below `execute_plan` | 1 failed | `test_sweep_yaml_is_written_before_the_first_execution` |
| `condition_meta["values"]` back to `{}` | 1 failed | `test_run_yaml_records_what_each_condition_varied` |
| `nameable=True` at the baseline call site | 1 failed | `test_a_baseline_value_is_not_subject_to_the_nameability_check` |
| `(condition_index or 0)` restored in `runner.attrition` | **428 passed** | none |
| `(condition_index or 0)` restored in `stats.collapse_repeats` | **428 passed** | none |

### Per finding

**Critical 1 — closed.** `cli.py:117-118` unions both key sets. The acceptance test is a real
`run` on the repro config and asserts `EXIT_PARTIAL` + `E-STEP-SWEPT-PARAM`, so it exercises the
whole path rather than the expression.

**Critical 2 — closed.** `_path_resolves`/`_value_checks` are shared by both loops, so grid and
baseline cannot drift apart — which is the structural half of the fix and is worth as much as the
tests. `reference.md`:218's own example (`analysis.methd`, `pearsonn`) now produces
`E-SWEEP-PATH-UNKNOWN` and `E-PARAM-VALUE` respectively.

**Important 1 — closed, and closed at the right layer.** The guard is in `_check_shape`, which
`validate_config:139` early-returns on, so no later `_check_*` indexes into a block already known
malformed and `validate` still only *collects*. Verified the second entry point too:
`command_run` (`cli.py:90-95`) runs `validate_config` and returns `EXIT_WRONG` on errors before it
ever reaches `expand`, so `run` gets the diagnostic as well, not just `validate`. The `is not None
and not isinstance(...)` form keeps `sweep: {grid: null}` "absent", matching `doc.get(x) or {}`
everywhere else — pinned by `test_a_null_grid_or_baseline_is_absent_not_malformed`.

**Important 2 — closed as a refusal, and the supported row survives.** The predicate is
`baseline and [p for p in grid if p not in baseline]`, so all three legal shapes stay silent, each
with its own negative test: baseline fixing every axis (the slice's worked example), bare baseline
with no grid, and `baseline: {}` beside a grid. The end-to-end bare-baseline assertion at
`tests/test_runner.py:100-111` is unmodified and passing. Registry check re-run independently:
`grep -c "E-SWEEP" docs/reference.md` → **0**, so the new identifier collides with nothing, and
the mint is recorded in `docs/superpowers/spec-defects.md` § New error identifier:
`E-SWEEP-BASELINE-PARTIAL` naming `reference.md`:1415-1422 and the retirement condition. (That
file is untracked because `.gitignore:224` excludes `docs/superpowers/`; the entry exists on disk,
which is this repo's normal state for the ledgers, not an omission from the commit.)

**Important 3 — closed, and the test does pin the ordering despite the monkeypatch.** Reverting
the line move fails the test with `FileNotFoundError` on `sweep.yaml`, which is exactly the state
the finding described. The property under test is statement order inside `command_run`, and
injecting the fatal is the only way to reach it — `E-RUN-CFG-MISSING`/`E-RUN-SEED-MISSING` are
genuinely unreachable through `command_run`, since `cfgs` is built from the same `conditions` the
plan is. The test asserts the file's *content* (three labels, 15 execution-order entries), not
merely its existence, so it also catches a truncated or stub write. What it does not pin — out of
scope, and noted only so a later reader doesn't assume it — is that the write stays inside the
`RunLock`.

**Important 4 — closed.** `values` is set in `_results_block`'s `condition_meta` loop rather than
at either `setdefault`, so both construction paths are covered. `condition_meta=None` leaves
`values: {}`, but `command_run` (`cli.py:288`) is the only production caller and always passes it;
the `None` default exists for `tests/test_runner.py`'s direct `assemble_run_yaml` calls.
`dict(...)` unwrapping the `MappingProxyType` is required — `yaml.safe_dump` has no representer
for it — and the acceptance test is a real run reading `run.yaml` back, so a proxy leak would fail
there rather than in review.

**Minor (the `or 0`) — closed, unpinnable.** Both call sites are now strict `==`, and restoring
either `or 0` leaves all 428 tests green. That is the expected result, not a gap: `build_plan`
(`scope.py:63-68`) always gives a `condition`/`repeat` execution a real `int`, so the input the
`or 0` mishandled cannot be produced through any supported path, and pinning it would mean
hand-constructing an `Execution` core never emits. The change is still the right one — a strict
`==` makes a future `None` drop out instead of being absorbed into condition 0 — and both sites
carry a comment saying so. `run_record`'s two `e.condition_index or 0` are correctly left alone:
their job is placing a condition-less execution somewhere in the record, not filtering.

### The approved deviation — confirmed against the code, not the argument

`check_swept_value` is applied to grid values and not to baseline values. Verified end to end:

- `sweep.label_for` (`sweep.py:112-114`) returns the literal `"baseline"` on `is_baseline` before
  touching `values` at all, and `expand` (`sweep.py:145`) sets `is_baseline=True` unconditionally
  for the baseline row. A baseline's fixed values cannot reach a label.
- No other route. `grep` for `label_for` outside `sweep.py` returns nothing; `condition_dir_name`
  (the only other name-shaped consumer, used by `runner.py:153` and `artifacts.py:400`) takes
  `index` and `label`, never `values`. The two remaining consumers of `Condition.values` —
  `sweep_document` and the new `run.yaml` `values` — write YAML data, not identifiers.
- The pinning test is genuine, not vacuous. `SWEPT_VALUE_PATTERN` is anchored
  (`^[A-Za-z0-9._+-]+$`), and `check_swept_value("pear son")` returns a real refusal when called
  directly. Flipping `nameable=False` → `True` fails
  `test_a_baseline_value_is_not_subject_to_the_nameability_check`, so the test distinguishes the
  two settings rather than passing under both. It asserts all three halves on one config:
  `E-PARAM-VALUE` fires, `E-SWEEP-VALUE-UNNAMEABLE` does not, and `E-SWEEP-BASELINE-PARTIAL` does
  not (the baseline fixes the only grid axis, so item 4 cannot be what is keeping it quiet).

The deviation holds, and `nameable` being an explicit parameter at both call sites is the right
shape: when per-cell expansion lands, `reference.md`:1419 row 2 labels a per-cell baseline by the
axes it leaves *free*, so the fixed values stay unrendered and the flag stays `False`.

### Regression targets

| Target | Result |
|---|---|
| Single-condition / no-sweep tree unchanged | `test_a_single_condition_run_is_unchanged` asserts `not (run_dir / "conditions").exists()`, unmodified and passing |
| Bare `sweep.baseline`, no grid → one condition **with** the level | `tests/test_runner.py:100-111` still asserts `conditions/00_baseline/seed17/analyze`; `test_a_bare_baseline_with_no_grid_is_supported` adds the validate-side negative |
| `sweep.py` / `stats.py` pure | Re-checked imports directly: `sweep.py` is `itertools`, `re`, `collections.abc`, `dataclasses`, `types`, `typing` + `replication.Repeat` under `TYPE_CHECKING`; `stats.py` is `math`, `collections.abc`, `dataclasses`, `typing`, `scipy` + `runner.ExecutionResult` under `TYPE_CHECKING`. No `Path`, no `config`/`artifacts`/`runner`/`cli` at runtime. `sweep.py` was not touched by the wave at all |
| Every `E-`/`W-` identifier has a test producing it | 82 identifiers in `src/`; all but two appear in `tests/`. The two — `E-EXPERIMENT-UNKNOWN` (`generators/step.py:25`) and `E-RUN-ID-EXHAUSTED` (`run_identity.py:31`) — are pre-existing from S1/S2 (`21789da`, `dae3112`, both ancestors of `152f0bf`) and untouched here. Not this wave's debt; worth a line in a later slice's ledger. The one new identifier, `E-SWEEP-BASELINE-PARTIAL`, has a test that produces it and asserts its message |

One behavior change the union in Critical 1 introduces, recorded so it isn't later mistaken for a
regression: with a bare `sweep.baseline` and no grid, a `run`/`summary`-scoped step reading a
baseline-fixed path now gets `E-STEP-SWEPT-PARAM` where it previously got the base value. That is
the fix working — the run's single condition uses the baseline's value, so the base value is again
a value no condition used — not a new refusal of something legal.

### One document example the new refusal now rejects (non-blocking)

Swept every YAML `sweep.baseline` in the four documents and the feasibility analysis for a
baseline that fixes fewer paths than the `grid` beside it. Exactly one hit:
`docs/feasibility-llm-growth-studies.md`:469-475 — `baseline: {prompt.program_id:
neutral-baseline}` beside `grid: {prompt.program_id: [...], llm.model: [...]}`, whose own comment
says *"baseline expands over the unfixed `llm.model` axis: 3 baseline conditions (one per
deployment)"*. That is precisely `reference.md`:1419 row 2, and this build now refuses it with
`E-SWEEP-BASELINE-PARTIAL`.

Not a blocker and not a defect in the fix: a feasibility analysis is explicitly non-normative
(`CLAUDE.md` § Feasibility analyses), the refusal is the adjudicated choice over silently
executing a different design, and the divergence is on record with a retirement condition. It is
noted because it is the one place a reader following the documents will write a config this build
rejects — worth a sentence in the S3b brief that lands per-cell expansion, and the natural
acceptance case for it.

The four documents themselves are clean: `README.md`:176, `docs/experimental-designs.md`:48 and
:162, and every other feasibility example either fix every grid axis, declare no grid
(`ablate`/`null`), or are already refused by `E-SWEEP-UNSUPPORTED` for an unimplemented mode.

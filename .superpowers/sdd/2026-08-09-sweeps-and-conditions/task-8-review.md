# Task 8 review: wire the CLI, and the acceptance test

## Verdicts

- **Spec compliance:** ✅
- **Task quality:** approved

## What was checked

Read the brief, the report, and the diff (`review-82f16c0..104b018.diff`) in full;
cross-referenced against the full post-commit source (`git show 104b018:<path>`) for
`sweep.py`, `runner.py`, `artifacts.py` to verify claims the diff alone doesn't show —
per instructions, did not run the suite (405 passed / ruff clean / mypy clean already
confirmed) and made no changes.

## Is the wiring actually reachable from `main(["run", ...])`?

Yes, verified by tracing what happens if each new code path is deleted:

- **`sweep.expand(doc)` replacing `conditions=[(0, None)]`** — `cli.py:113-121` (new).
  If reverted, `plan` has one execution set and `cfgs` has only key `0`/`-1`; the new
  test `test_a_sweep_runs_every_condition_over_one_roster` asserts a `conditions/` dir
  with three labeled subdirs and 15 `executions.jsonl` lines — both would fail hard.
- **`resolve_condition_cfg`/`resolve_wide_cfg` replacing `Config(doc)` twice** —
  `runner.py` (`resolve_wide_cfg`) plants `SweptAway` markers read by `Node.__getattr__`
  → `E-STEP-SWEPT-PARAM`. `test_a_summary_step_reading_a_swept_parameter_is_refused_in_a_real_run`
  proves this fires from a real `run`, not a hand-built `cfgs`; reverting to
  `Config(doc)` would let the summary step read `"pearson"` silently and the run would
  finish `EXIT_OK`, not `EXIT_PARTIAL` — the assertion would fail.
- **`StepIO(scope=..., conditions=..., repeats=..., step_scopes=...)` in `runner.py`** —
  `artifacts.py`'s `io.conditions`/`io.repeats` default to `list(self._conditions or [])`,
  i.e. `[]` when the constructor args are omitted. `test_a_summary_step_reads_every_condition_in_a_real_run`
  iterates `io.conditions` and would see an empty list on the old wiring, producing
  `seen == {}` against an expected 3-entry dict — a real failure, not a tautology.
- **Per-condition `aggregated` loop replacing the single `0`-scoped block** — confirmed
  `attrition(results, roster, step_name, cond.index)` and
  `collapse_repeats(results, step_name, cond.index)` (`cli.py`) match the callee
  signatures `attrition(results, roster, step_name, condition_index)` and
  `collapse_repeats(results, step_name, condition_index)` in argument order and in
  varying value — this is the first slice where `condition_index` is not a constant
  `0` at these call sites, and it is not transposed.

All four are genuinely load-bearing; none of the new tests would pass against the
pre-commit (inert) `cli.py`/`runner.py`.

## The declaration-not-count rule

Verified directly in `sweep.py`'s `expand`: no `sweep` block → `Condition(index=0,
label=None, ...)`, and `runner.step_dir_for` only descends into `conditions/` when
`execution.condition_label is not None`. A bare `sweep.baseline` with no `grid` would
produce one `Condition` with `label="baseline"` (not `None`, since `is_baseline=True`
routes through `label_for`'s `is_baseline` branch before any grid axis exists) — so the
`conditions/` level would still appear for that single condition. This matches the
brief's stated rule (keyed on declaration, not `N > 1`). Not separately tested in this
diff (no bare-baseline-only case in `test_acceptance.py`), but the code path is
unambiguous and was already exercised by `sweep.py`'s own unit tests from an earlier
task; not a gap in this task specifically.

## Correctness details

- `stats.py`'s `summarize_step` sets `"correction": None` unconditionally on every
  emitted metric (`src/publishable/stats.py`, in the `out[column] = {...}` block) —
  not gated on any condition, so there's no path that skips it.
- `run_record.py`'s `_results_block` builds `aggregated[cond.index]` as a fresh dict
  comprehension per condition in `cli.py`; verified no shared mutable object crosses
  condition boundaries. The acceptance test's `assert blocks[0] is not blocks[1]` is a
  real check, backed by `resolve_condition_cfg`/`resolve_wide_cfg` each doing
  `copy.deepcopy(base)` — confirmed in `runner.py`.
- `condition_meta` correctly back-fills conditions absent from `results` (e.g. an empty
  grid axis) via `conditions.setdefault(...)` in `_results_block`, so identity survives
  even with zero executions — this is a real edge case the implementer's code handles
  even though no test in this diff exercises the zero-execution case (that's the
  already-known, separately-ticketed `sweep`-with-only-falsy-subkeys gap).

## Deviations from the brief (not defects)

- `sweep_document`'s call signature (5 args: `conditions, repeats, digest, order,
  execution_order`) differs from the brief's 4-arg sketch; the report explains this is
  because the pre-existing `sweep_document` (from an earlier task) separates the
  declared `order` mode from the realized `execution_order` sequence. Confirmed against
  `sweep.py`'s actual signature and docstring — consistent, not a shortcut.
- The acceptance test for `sweep.yaml`'s `repeats` field was written against actual
  behavior (`repeats` groups by kind → 1 entry with 5 seeds) rather than the brief's
  literal `len(sweep_doc["repeats"]) == 5`. This is the implementer correcting the
  brief's sketch to match already-shipped `sweep.py` behavior, and is disclosed with a
  comment in the test itself (`tests/test_acceptance.py`).

## Constraint check

`artifacts.py` is stated as the only module writing inside a run directory, but
`cli.py` writes `sweep.yaml` directly (as instructed by the brief's own pseudocode) —
this is consistent with pre-existing `cli.py` behavior (it already writes
`manifest/input.json`, `environment/*`, `run.yaml` directly) and is not a new violation
introduced by this task; the brief itself specifies the code this way. Noting for
completeness, not as a finding.

## Findings

None — Critical or Important. No transpositions, no aliasing, no dead wiring found.
The two "already known" items (empty falsy-subkey sweep, bare-baseline-only test gap)
are pre-existing/ticketed and correctly excluded from this task's scope per the
reviewer's brief.

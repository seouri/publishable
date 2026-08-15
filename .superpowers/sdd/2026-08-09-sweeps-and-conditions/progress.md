# SDD ledger — plan: docs/superpowers/plans/2026-08-09-sweeps-and-conditions.md

Branch: s3a-sweeps-and-conditions (in-place; docs/superpowers is gitignored so a worktree would not contain the plan)
Base: 152f0bffc9b4aa5718d7ee323d71d87f6a082002

Pre-flight scan: two plan defects found and ruled on before Task 1 —
  (a) Task 5's sentinel did not raise on the leaf read. cfg.parameters.analysis.method simply
      RETURNED the sentinel; the raise fired only on a further access, so the test's asserted
      E-STEP-SWEPT-PARAM would actually surface as E-STEP-RETURN-TYPE from the S2 shape gate.
      Ruled: the marker moves into config.py and Node.__getattr__ raises on it, so the refusal
      fires on the read. runner imports it; no cycle.
  (b) An empty grid axis expanded to zero conditions — a run executing nothing while reporting
      success. Ruled: refuse with E-SWEEP-AXIS-EMPTY at validate, mirroring S2's E-UNITS-EMPTY.
      expand() stays pure and still returns []; validate is what refuses.
Task 1: implemented (commit 919e128) — purity verified from a no-git dir; 3-axis ordering is
  exact nested-loop in declaration order; label is None only when no sweep is declared, which
  is what keeps the tree flat.
Task 1: fix round 1/5 dispatched — Important: Condition.values is a mutable dict inside a
  frozen dataclass, the same defect S2 fixed in Unit.attributes. Fixing NOW because Tasks 2-3
  begin building consumers on Condition, and S2's version of this fix had to be retrofitted
  after three tasks already depended on the type. Plus a docstring note that a baseline
  coinciding with a grid cell is deliberately not deduped.
Task 1: reviewer observation folded into the PLAN rather than this task — a sweep block whose
  only key is unrecognised (a typo like `gird`) expands to zero conditions with nothing to
  refuse it, since Task 3's refusals name only the four known modes. Task 4 now adds
  E-SWEEP-KEY-UNKNOWN, on the same argument as the unknown-parameter check.
Task 1: fix round 1/5 (Condition.values wrapped in MappingProxyType over a copy; docstring
  note on the deliberate baseline/grid-cell duplicate; commits 919e128..8548f03). Verified:
  immutable, passed-in dict copied, equality with a plain dict still holds (load-bearing for
  the unswept-run assertion), reads unchanged.
Task 1: complete (commits 152f0bf..8548f03, review clean)
Task 2: implemented at 1f63311 (label grammar: shortest-unique-suffix key, __ between axes, declaration order, render_value, SWEPT_VALUE_PATTERN). 349 tests.
Task 2: implementer escalated a SPEC conflict — reference.md sets the axis separator to `__` while the swept-value pattern `[A-Za-z0-9._+-]+` admits `_`, so a value of `a__b` yields `one=a__b__two=c`, which parses as three axes. Load-bearing because the label is a selector (compare.condition, contrast of/against).
Task 2: ruled — refuse a swept value whose rendering contains `__`; a single `_` stays legal. Ledger the conflict in spec-defects.md with both candidate resolutions. Fix round 1 dispatched.
Task 2: complete (8548f03..e2c9a21, spec ✅, quality approved).
Task 2: minor (deferred): sweep.py label_for's keys.get() fallback branch is dead given how expand() calls it — defensive, flagged for the whole-branch review.
Task 3: implementer a89358d0be8809e2a interrupted by session limit before commit; edits survived in the working tree (validate.py, test_validate.py), nothing committed. Resumed to verify and commit.
Task 3: implemented at 2b8d9e6 (E-SWEEP-UNSUPPORTED retired tree-wide; four mode refusals). 357 tests.
Task 3: verified by probe — baseline+grid validates clean, each of the four modes emits its own code, and the 50 refusal tests (incl. E-REPL-KIND/ORDER-UNSUPPORTED) still pass.
Task 3: minor (deferred): refusal messages render with the config path on a separate line, so several read as subjectless fragments (`couples parameters into one axis, and is...`, and the pre-existing `is specified but not...` for cluster_by). Pre-existing house style; worth one sweep across all of them rather than piecemeal — for the whole-branch review.
Task 3: noted — sweep's own key set is not checked for typos (a `gird:` key validates clean). Already owned by Task 4 as E-SWEEP-KEY-UNKNOWN.
Task 3: complete (2b8d9e6, spec ✅, quality approved). Reviewer confirmed expand() is genuinely wired into cli/run_record, so lifting the blanket refusal opened no silent no-op path.
Task 3: minor (deferred): no test declares two unimplemented modes at once (branches are independent, not exploitable).
Task 4: implemented at 66cf0da (E-SWEEP-AXIS-EMPTY, E-SWEEP-KEY-UNKNOWN, E-SWEEP-PATH-UNKNOWN, E-SWEEP-VALUE-UNNAMEABLE, W-EXEC-BUDGET, W-STATS-FAMILY; check_swept_value wired in). 371 tests.
Task 4: PLAN DEFECT (mine) — the brief's illustrative _check_sweep used elif between the spec-value check and the nameability check, making E-SWEEP-VALUE-UNNAMEABLE unreachable for its own test case. Implementer made them independent. Correct.
Task 4: confirmed W-EXEC-BUDGET is a WARNING per reference.md:147 and :2118 (`validate` warns above this many), not an error.
Task 4: complete (66cf0da, spec ✅, quality approved). Reviewer mutation-tested both boundaries (budget >/>=, family >1/>=1) — each flip breaks a real test.
Task 4: minor (informational): _repeat_total duplicates a few lines of _check_replication's n-falls-back-to-k shape; not shared, different error semantics.
Task 5: implemented at c37ff1b (per-condition cfg; SweptAway marker in config.py so Node.__getattr__ raises E-STEP-SWEPT-PARAM on the read itself; execute_plan cfg -> cfgs dict). 380 tests.
Task 5: fix round 1 — (a) resolve_wide_cfg made symmetric with setdefault so an absent parent still gets the marker planted; skipping it left the swept param READABLE at run/summary scope, the exact defect the code exists to prevent. (b) missing cfgs key stays fatal (core invariant, not a step failure) but raises explicitly instead of a bare KeyError.
Task 5: CARRY TO TASK 8 — the swept-param refusal is inert until cli.py wires sweep.expand + resolve_*_cfg. Task 8's acceptance test must prove E-STEP-SWEPT-PARAM fires through a real run, end to end.
Task 5: complete (c37ff1b..e66a88b, spec ✅, quality approved). Reviewer confirmed both rulings are implemented and each has a test that fails under the reverted behavior; no SweptAway leak into a hash, io.record, or the run record.
Task 5: ledgered — E-RUN-CFG-MISSING (and pre-existing E-RUN-SEED-MISSING) are raise-time codes absent from reference.md § Errors core raises. Added to spec-defects.md.
Task 5: CARRY TO TASK 8 — cli.py currently builds cfgs={0: Config(doc), -1: Config(doc)} sharing one doc object. Harmless today (Node never mutates _data) but must be checked against Task 8's real wiring.
Task 6: implemented at 4221ed0 (sweep_document; Repeat imported under TYPE_CHECKING so purity holds; float+bool YAML round-trip test). 385 tests.
Task 6: review spec ❌ — sweep_document's shape contradicts reference.md § sweep.yaml. Four divergences: repeats must group by kind with a resolved `seeds` list; `labels` is its own top-level key (composed outer-to-inner); `order` is the scalar mode (as_declared|randomized); `execution_order` is the realized sequence as {condition, repeat} mappings.
Task 6: PLAN DEFECT (mine) — the brief's shape disagreed with the normative document. Functionally load-bearing, not cosmetic: reference.md says resume READS sweep.yaml back rather than re-deriving it. Documents lead, so the code changes; nothing to amend in the spec. Fix round 1 dispatched.
Task 6: fix round 1 at eaffd0a — sweep_document now matches reference.md exactly (grouped repeats with resolved seeds, top-level labels, scalar order mode, execution_order as {condition, repeat} mappings, optional order_seed). Verified by rendering and round-tripping. 386 tests.
Task 7: implemented at 7374581..09882a7 (StepIO scope/conditions/repeats/step_scopes;
  io.conditions/io.repeats/io.read_condition summary-only via E-STEP-SCOPE-ONLY;
  E-STEP-READ-REPEAT-REQUIRED; read_upstream's E-STEP-READ-DIRECTION). Extracted
  sweep.condition_dir_name so read_condition and runner.step_dir_for share one
  `<nn>_<label>` format rather than a second hand-rolled string. 398 tests.
Task 7: minted E-STEP-READ-CONDITION-UNKNOWN beyond the brief — the brief's own
  read_condition pseudocode left an unresolved condition index formatting `None`
  into the path and failing opaquely inside _read's FileNotFoundError.
Task 7: SPEC CONFLICT flagged, not resolved — reference.md:1784/:1807/:2318's
  `for condition in io.conditions: io.read_condition(condition, ...)` only
  type-checks if io.conditions yields bare indices; the brief's test pins
  (int, str) tuples. Implemented per the brief's executable test. Ledgered in
  spec-defects.md with two candidate resolutions.
Task 7: CARRY TO TASK 8 — runner.py's StepIO(...) construction site still builds
  a scope-less StepIO (defaults: scope="repeat", conditions=None, repeats=None,
  step_scopes=None). io.conditions/io.read_condition/read_upstream's direction
  check are inert until Task 8 passes real values through from build_plan's
  Execution and sweep.expand's Condition list — same pattern as Task 5's carry.
  Task 8's brief as currently written does not show this wiring; check before
  closing S3a.
Task 7: complete (7374581..09882a7, 398 tests, ruff/mypy clean).
Task 6: complete (e66a88b..eaffd0a, all four findings resolved, no new findings).
Task 7: implemented at 7374581 + 09882a7 (io.conditions, io.repeats, io.read_condition, read_upstream direction check via SCOPE_ORDER; sweep.condition_dir_name extracted so runner.step_dir_for and read_condition share one path rule). 398 tests.
Task 7: DEFECT — io.conditions yields (index, label) tuples but read_condition looked the arg up as an int key, so reference.md's own documented loop (lines ~1784/1806/2318) raises E-STEP-READ-CONDITION-UNKNOWN at runtime. Ruled: accept int OR the (index,label) element, normalize once; test the documented pattern verbatim. Fix round 1 dispatched.
Task 7: approved the extra code E-STEP-READ-CONDITION-UNKNOWN (an unresolved index would otherwise fail opaquely in a path join).
Task 7: CARRY TO TASK 8 — runner.py's StepIO construction passes no scope/conditions/repeats/step_scopes, so the whole Task 7 surface is inert in a real run until Task 8 wires it.
Task 7: fix round 1 at 82f16c0 — read_condition accepts int | tuple[int,str], normalized once; test_read_condition_accepts_the_element_io_conditions_yields loops io.conditions verbatim. Both spellings pinned. 399 tests.
Task 7: review spec ✅, quality findings (2 Important) — (a) read_condition cannot distinguish an unresolved index from a resolved one whose label is None (the documented no-sweep case), so a valid index 0 gets E-STEP-READ-CONDITION-UNKNOWN; untested. (b) no test calls read_upstream from a summary-scoped caller, so a summary-ranking bug in the direction check (as opposed to the _summary_only guard) would go undetected.
Task 8: implemented at 104b018 (cli wires sweep.expand + resolve_*_cfg + sweep.yaml + per-condition aggregation; execute_plan derives conditions/repeats/step_scopes into StepIO; stats emits correction: null). 405 tests. Both carry-forwards proven through real main(["run"]) calls.
Task 8: DEFECT found by me — `sweep: {grid: {}}` passes validate and expands to ZERO conditions; the per-axis E-SWEEP-AXIS-EMPTY loop never runs when there are no axes. Run executes nothing and reports success — the exact silence class. Ruled: refuse on the expansion RESULT (zero conditions), not by enumerating shapes.
Task 7: fix round 2 at cb1a5aa (read_condition distinguishes membership from a null label; summary-caller read_upstream tests added).
Task 8: complete (104b018, spec ✅, quality approved). Reviewer traced all four wirings to 'would reverting break the new tests' — yes in every case. attrition/collapse_repeats arg order correct and cond.index genuinely varies 0/1/2.
Task 8: minor (deferred): no dedicated test for the bare-baseline-only case (one condition WITH the conditions/ level); sweep.yaml is written from cli.py rather than artifacts.py, matching pre-existing cli behavior, not a new violation.
ZERO-CONDITION FIX: complete at b1d6c15. E-SWEEP-EXPANDS-EMPTY refuses on the expansion RESULT (`if sweep and not conditions`), beneath the per-axis checks so E-SWEEP-AXIS-EMPTY keeps its specific diagnosis. Verified: {grid:{}} refused, empty axis still specific, no-sweep still 1 condition. Bare-baseline conditions/-level layout test added. 414 tests.
WHOLE-BRANCH REVIEW: findings — 2 Critical, 4 Important, all clustered on sweep.baseline being expanded but never validated, treated as swept, or recorded. Verified clean: cross-condition pooling (on a VARIED fixture: two recording steps, condition-dependent skips), correction: null, single-condition and bare-baseline trees, sweep.py/stats.py purity.
WHOLE-BRANCH FIX WAVE: complete at 8e208bf + f3158e2. 428 tests. (1) swept_paths unions baseline keys; (2) baseline entries get path+Param checks; (3) _check_shape descends into sweep; (4) partial baseline REFUSED as E-SWEEP-BASELINE-PARTIAL rather than implementing per-cell expansion (reference.md:1415-1422), following the four-mode precedent; (5) sweep.yaml written before execute_plan; (6) run.yaml condition values populated; (7) (condition_index or 0) made strict in the two anti-pooling functions.
WHOLE-BRANCH: approved deviation — check_swept_value is NOT applied to baseline values, since label_for returns the literal 'baseline' so a baseline's fixed values never reach a label. Applying it would refuse legal configs. Pinned by test_a_baseline_value_is_not_subject_to_the_nameability_check.
WHOLE-BRANCH: recorded not fixed — artifacts.py read_upstream hard-codes shared/, so a repeat step reading a condition-scoped step fails. Pre-existing, newly advertised by the S3a direction check. spec-defects.md entry against reference.md:1083, for S3b.
RE-REVIEW: ready to merge. All 7 findings closed; 6 of 7 killed by mutation testing. The approved nameability deviation holds (label_for returns the literal on is_baseline; no other path routes a baseline value into a name) and its test is not vacuous. Regression targets clean; purity intact; no test deleted or edited.
RE-REVIEW notes: (a) docs/feasibility-llm-growth-studies.md:469 shows a per-cell baseline the new refusal now rejects — non-normative, recorded, a natural S3b acceptance case. (b) E-EXPERIMENT-UNKNOWN (generators/step.py:25) and E-RUN-ID-EXHAUSTED (run_identity.py:31) have no test naming them — pre-existing S1/S2 gaps in the coverage bar, not this slice.

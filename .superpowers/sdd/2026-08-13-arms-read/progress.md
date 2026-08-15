# SDD ledger — plan: docs/superpowers/plans/2026-08-13-arms-read.md
Plan: docs/superpowers/plans/2026-08-13-arms-read.md (20 tasks).
Branch h3c1-arms-read, base cb96c7d (main, H3b merged).

Pre-flight (controller): one fix — task 3's test asserted `c.selects`, an interface I INVENTED rather
  than read. Now labelled as the implementer's choice, with Condition's real shape (index, label,
  values, is_baseline; __post_init__ wraps values in a MappingProxyType) stated instead. What is
  non-negotiable is that the answer lives ON THE CONDITION rather than being re-derived per reader.

Task 1: commit f9eecb7. Documents only; 1391 passed + 2 xfailed, unchanged; NOT BUILT count still
  seven. FIVE edits, not four — the fifth reported rather than slipped in.
  THE SHARPEST FINDING, controller-verified: *Baseline leaves contrasts confounded* used `arm: control`
  as its own example, but its implemented twin W-SWEEP-BASELINE-CONFOUNDED reads `swept_axes =
  list(grid)` — grid's axes ALONE. So the row's example described A WARNING THAT NEVER FIRES. The old
  "2 of 3" was also arithmetically wrong. Rewritten to a grid-only example whose count was verified BY
  RUNNING expand (5 conditions, 4 contrasts, 2 differing on both), with the grid values named in the
  row so the number is auditable.
  BRIEF SUB-QUESTION HAD A DEFECTIVE PREMISE: I asked whether REQUIRED-when-`between` needs its own
  row. It needs none — *Allocation needs arms* and *Every axis is assigned* cover it between them
  (absent assign, assign: {}, and between-with-no-axes all land in one of the two). Said so in the row.
  The new *Arm is constant within a unit* row deliberately does NOT reuse the weight sibling's "a value
  no row declared" consequence: an arm column is a string, `mean` is rejected, so first/mode always
  pick a value some row declared. The arm-specific harm is that the FILE'S ORDER decides WHICH
  CONDITION the unit is measured in — which is what discriminates it from cluster (which side of a
  split) and weight (how much it counts).
  FIFTH EDIT: W-SWEEP-BASELINE-CONFOUNDED's "the other two are silence" was a COUNT that groups makes
  wrong — the same trap H2's commit e91cf0d fixed. Dropped. Its closing claim that per-cell expansion
  is "only a free grid axis" is also false once groups is real, per § Expansion modes; reworded, and
  the resulting group-axis silence labelled DELIBERATE rather than left as an unowned gap.
Task 1: DIGEST VERDICT — the DOCUMENT is right, the code changes in task 16. Reasoning worth keeping:
  design_digest canonicalises data.units wholesale, so a pinned assign.seed is inside the digest —
  which would make pinning ONE axis's seed move every fold boundary, repeat seed, sample draw and
  OTHER axis's allocation. That is exactly the confounding § What auto derives from exists to refuse.
  One-line fix, deferred to task 16 as the brief required.
Task 1: TWO CONCERNS ROUTED — holdout.seed is the same digest defect one field over, latent while
  holdout is NOT BUILT, and H3d owes the exclusion or a reason; and *Leave-one-out is affordable* is a
  THIRD row this slice pressures that my brief did not name (under `between`, folds are drawn within
  each cell, so k: all is the cell's count not the roster's — example stays true, rule unstated, left
  alone). Task 20 should check it.
Task 2: commit 4e19d5c. 1391 passed + 2 xfailed, unchanged — behaviour-preserving by design.
  Controller-verified: PRODUCT_MODES (grid, paired, sample, groups) uplus NON_PRODUCT_MODES (baseline,
  ablate) is a real partition and SWEEP_MODES derives from it; PARAMETER_AXIS_MODES is the predicate
  subset; the residual is exactly {groups}; and `groups` still expands to ZERO conditions, which is
  task 5's boundary, pinned explicitly.
  THREE BRIEF DEFECTS, MINE, and the first is the sharpest kind:
  (a) THE TEST I PRESCRIBED WAS ITSELF A CHECK THAT COULD NOT FAIL. `groups` was ALREADY in
  NON_AXIS_MODES, so `ablate x groups` was already permitted and the discriminating assertion could
  not have failed before the change — and the discriminator ALREADY EXISTS as
  test_validate.py::test_ablate_composes_with_a_group_axis. I wrote a brief warning against adding an
  eleventh could-not-fail check whose own prescribed test was one. The implementer refused to
  manufacture a red test and said so.
  (b) THE NAMED SPLIT IS NOT A PARTITION. PARAMETER_AXIS_MODES is a SUBSET of PRODUCT_MODES, so
  SWEEP_MODES cannot derive from those two — a third name is forced. The partition is
  PRODUCT_MODES uplus NON_PRODUCT_MODES; PARAMETER_AXIS_MODES is a predicate over the first.
  (c) MUTATION 2 AS SPECIFIED IS DEGENERATE — a literal SWEEP_MODES with the same six contents fails
  nothing (verified: 1391 passed), and my fallback test would also pass under it. The contentful
  version is a literal SWEEP_MODES PLUS a seventh mode in PRODUCT_MODES only: 1 failure. Mutation 1
  (groups into PARAMETER_AXIS_MODES) killed 2 tests including the real discriminator.
Task 2: STANDING RISK the implementer named, worth carrying to task 20 — the subset relation is a NEW
  hole the derivation cannot close. A future product mode forgotten in PARAMETER_AXIS_MODES silently
  becomes one `ablate` may cross, and the only guard is the literal residual assert
  PRODUCT_MODES - PARAMETER_AXIS_MODES == {"groups"}. H2's derivation closed the
  is-it-a-known-mode hole; it cannot close this one.
Task 3: commit b8499e9. 1393 passed + 2 xfailed (was 1391). Condition.selectors: frozenset[str], after
  is_baseline, coerced in __post_init__ the way values is wrapped. SELECTOR_MODES derived as
  PRODUCT_MODES minus PARAMETER_AXIS_MODES rather than a second literal. selector_paths(sweep) is the
  counterpart to _swept_paths, total over malformed input on validate's expand-inside-a-try premise.
  Controller-verified with a control: baseline rows carry selectors={arm} and values
  [analysis.method, arm]; product rows carry selectors={} — and a GRID axis literally NAMED `arm`
  marks nothing, so the discriminator is the mode and not the name.
  BRIEF DEFECT #11, MINE: my test config used the MAPPING form {"groups": {"arm": [...]}}. § Expansion
  modes refuses it outright — "`groups` is a LIST, always ... there is no mapping shorthand" — and
  tests/test_sweep.py already used the list form. Asserting a config shape rather than reading one,
  the same cluster as every other defective brief in this project.
  TESTED END TO END DESPITE groups NOT EXPANDING YET, which I had said might be impossible: a baseline
  may fix a group level TODAY (§ Expansion modes — a baseline "accepts group levels as well as
  parameter paths"), so groups + grid + baseline:{arm: control} yields baseline rows carrying `arm` and
  product rows carrying none — PROBE AND CONTROL IN ONE expand CALL, with exact lists asserted.
  MUTATION RUN IN BOTH DIRECTIONS, which is the discipline: marking nothing fails the named test, AND
  marking every path also fails it — with the grid-only control separately confirmed to report {arm}
  under that second mutation, so the control is proven non-vacuous rather than assumed.
Task 3: TWO DELIBERATE GAPS, named — group paths are not unioned into `swept` (label ordering is task
  5's), and `selectors` is NOT recorded in sweep.yaml, because that payload matches § "sweep.yaml —
  the resolved plan" exactly and a new key needs a document change outside this task. Task 4 decides
  whether a reader of run.yaml can tell an arm from a parameter; if it should, the document moves first.
Task 4: commit 493eb8d. 1396 passed + 2 xfailed (was 1393). Controller-verified: a condition carrying
  a selector resolves to parameters WITHOUT `arm`, and the no-selector control resolves identically.
  THE LEAK IS CLOSED.
  MY BRIEF WAS WRONG THREE WAYS, all found by the implementer:
  (a) ONLY ONE OF THE SEVEN READERS HAD TO CHANGE — resolve_condition_cfg, which now takes the
  Condition rather than a bare values mapping, so the marking cannot arrive out of step. The other six
  are correct AS-IS, each verified by what the site actually consumes: the two records carry the cell
  verbatim because § Expansion modes prescribes exactly that; label_for must render it; contrasts'
  free-axis matching correctly treats a group axis AS an axis (verified by running _free_axis_paths and
  baseline_for); and validate's two sites read sample.ranges and list(grid), neither of which a group
  path enters. My brief assumed all seven needed teaching.
  (b) THE parameters_hash PREMISE IS FALSE AND UNSATISFIABLE. parameters_hash covers the WHOLE config,
  so sweep.groups is inside it — "unchanged by adding a group axis" cannot hold. And cli hashes the
  BASE doc, never the per-condition configs, so the phantom parameter never reached parameters_hash at
  all. The real harm is a step reading cfg.parameters.arm. The headline test asserts the satisfiable
  form instead: two ARMS OF ONE DESIGN resolve to the same parameters_hash.
  (c) AN EIGHTH SITE I MISSED, same leak by another path — cli's wide-config union planted a
  SweptAway marker at parameters.arm (reachable because a baseline may fix a group level). Fixed, and
  extracted as _wide_swept_paths so the subtraction is testable.
  TWO MUTATIONS, NOT SIX, and the reason is right: only two sites changed, so inventing four against
  unchanged code would be four checks that cannot fail. Each killed exactly its named test.
Task 4: RULED, no document change — run.yaml embeds the config, so sweep.groups[].by recovers the
  arm-vs-parameter distinction without a new key. The implementer checked the thing that could have
  overturned it: `resume` is not built and Condition is constructed ONLY inside expand, so nothing
  rebuilds conditions without selectors.
Task 4: TWO LATENT validate GAPS ROUTED TO TASK 5, both the same missing question from opposite sides —
  _path_resolves will reject sweep.baseline: {arm: control} as E-SWEEP-PATH-UNKNOWN despite
  § Expansion modes permitting it; and groups: [{by: arm}] alongside grid: {arm: [...]} would make the
  grid axis silently unplantable at every scope, refused by nothing.
Task 5: commits 2535200, 379cc18. 1407 passed + 2 xfailed (was 1396). Ten new tests, seven mutations
  each killing its own named test. Controller-verified: groups alone gives arm=control/arm=treatment;
  groups x grid gives 4; ablate x groups gives (1+n) per level; the no-groups control is unchanged.
  Group axes HEAD _axes, per § How artifacts are organized's axis order, which also makes the last
  parameter axis vary fastest.
  MY PLAN WAS WRONG ABOUT ablate x groups — I scoped it as TEST-ONLY in task 19. It needed
  IMPLEMENTATION: each ablation repeats over each cell with the bare product rows suppressed. Without
  that, expanding groups would have shipped a six-condition set OF THE WRONG SHAPE that a test-only
  task could not have fixed.
  A FOURTH GAP, WORSE THAN THE TWO I ROUTED, and this slice would have opened it: the document says
  TWICE that validate rejects a baseline fixing a group level under `ablate`, and IT WAS NEVER
  IMPLEMENTED. The baseline fixes the axis, so it expands over nothing and EVERY OTHER LEVEL IS
  EXECUTED BY NO CONDITION while the run reports success — verified by running expand. Worse, the
  gap-1 fix REMOVED the accidental E-SWEEP-PATH-UNKNOWN that had been covering it by accident. Now
  refused as E-SWEEP-ABLATE-BASELINE-GROUP, a new identifier with a new § Errors validate reports row.
  The two routed gaps are closed: the baseline skip is gated on DECLARED AXIS NAMES (which also closes
  task 3's open concern), and groups+grid naming one path is refused under E-SWEEP-PATH-DUPLICATE with
  its row rewritten to state the real harm. Task 19 step 2 becomes "pin the refusal"; the adjacent case
  (`by` naming a declared-but-unswept parameter) is routed there rather than decided.
  NEW EXPOSURE FROM THE CHANGE, closed: group levels were unchecked by check_swept_value.
Task 5: NOT TAKEN, deliberately — § How artifacts are organized's Index row still shows 00/03
  interleaved baselines that expand does not produce. spec-defects.md owns it and says the deliverable
  is a DOCUMENT decision; the recommendation (narrow the row to the single-axis case) is in the report
  for task 18/20. Also: `groups` has no _check_shape guard, latent until task 17 retires the wholesale
  refusal — task 17 owes it.
Task 6: commit 0a69863. 1408 passed + 2 xfailed (was 1407). NO CODE CHANGE AND NO DOC CHANGE — none was
  owed, and the implementer verified that BEFORE touching anything rather than manufacturing one.
  The budget was not made wrong by this slice: _check_sweep computes len(expand(doc)) x repeat_total,
  and task 5 put group axes into _axes, so the budget inherited the fix. Probed: groups(2) x grid(3) x
  5 seeds against max_executions 20 already reports "6 conditions x 5 repeats = 30 executions exceeds
  20". Task 1 had already rewritten the row. Both halves of my brief's premise were already satisfied.
  What it added is the one thing missing: a test pinning the behaviour, which nothing else did (task 5
  tests expand directly). Reached BESIDE E-SWEEP-GROUPS-UNSUPPORTED with the exact error set asserted,
  so no refusal was retired to test it.
  A CONTROL THAT MUST REPORT, and the reason is worth keeping: "a silence-only control cannot tell
  'the group factor is counted' from 'the check is dead'". The second control asserts its own exact
  message rather than an absence.
Task 6: THE FOLD QUESTION MEASURED, and it is H3c-3's — task 5's expansion did change it. A 60-unit
  roster with a 2-level group axis and k: all now computes 2 conditions x 60 repeats = 120, where the
  no-group control gives 60. Under allocation: within (the only one built) 120 is CORRECT. Under
  `between`, once built, folds are drawn within each cell so the truth is 60 and the budget would
  OVERCOUNT BY EXACTLY THE LEVEL COUNT — latent, because _repeat_total never sees allocation and
  `between` is still refused.
Task 6: task 5's missing _check_shape guard for `groups` touches this path too — a malformed block
  silently budgets the parameter-only product. Task 17 inherits it, now from two directions.
Tasks 7+8: commit e288653, dispatched together as one coherent piece (both are validate checks over
  the assign block). 1427 passed + 2 xfailed (was 1408). FIRST NON-DEFECTIVE BRIEFS OF THE SLICE.
  validate._check_assign implements three previously unimplemented rows: *Allocation needs arms*
  (E-DATA-ALLOCATION-NO-ARMS), *Every axis is assigned* (E-DATA-ASSIGN-MISSING, one finding per
  unassigned axis), *Assignment names a method* (E-DATA-ASSIGN-METHOD). Task 1's ruling followed —
  REQUIRED-when-between gets NO third code, because the first two rows cover absent assign, assign: {},
  {arm: null} and between-with-no-axes, each with a test.
  A MUTATION THAT KILLED NOTHING, AND THE FIX — the presence and enum branches share one identifier,
  so deleting the presence branch let None fall through to the enum branch reporting the same code. The
  test now asserts the MESSAGE, which is what makes the branches separately mutation-testable. All four
  mutations then killed exactly their own named tests. That is the could-not-fail class caught by the
  implementer inside its own task rather than at review.
Tasks 7+8: A GAP NO TASK OWNED, now assigned to task 12 — `groups` + `allocation: within`. § Validation
  carries *Arms need allocation* and it is UNIMPLEMENTED (verified: no emit site). Once task 17 retires
  the two refusals, that config VALIDATES CLEAN AND HANDS EVERY CONDITION THE WHOLE ROSTER — exactly
  "two identical measurements reported as two arms", which task 20 step 6 must show is structurally
  impossible and which is why H2 deferred groups to H3 at all. `between` is not the only route to the
  bar; `within` is the route that defeats it. Task 12 now owns both halves, because closing one without
  the other looks complete from inside itself.
Tasks 7+8: two routed — E-DATA-ALLOCATION-UNSUPPORTED's message says group axes "are not implemented
  either", which task 5 falsified (task 17 owns the message); and the registry table has one
  pre-existing sort violation, E-SWEEP-ABLATE-BASELINE-GROUP after E-SWEEP-ABLATE-CROSSED, left alone
  for task 20 step 3.
Task 9: complete. Commits 56cc440 (impl), dec6242 (fix round 1), 07ee0a0 (controller's own fix).
  1427 passed + 2 xfailed — unchanged, honestly: the old 3-way parametrize over ASSIGN_METHODS became
  1 control + a 2-way parametrize, so three cases became three cases.
  E-DATA-ASSIGN-DRAWN refuses `random`/`blocked` BY VALUE while honouring the block. NOT the
  `-UNSUPPORTED` suffix: that is the broad build family, undocumented in reference.md and retired
  wholesale; this is the narrow family (E-DATA-WEIGHT-CONTRAST, E-DATA-CLUSTER-DERIVED), which is
  documented and gets registry rows. Sits in the same elif chain as E-DATA-ASSIGN-METHOD, so the two
  are mutually exclusive BY CONSTRUCTION (DRAWN_ASSIGN_METHODS ⊂ ASSIGN_METHODS), not by input order —
  the reviewer verified that structurally rather than reading it.
  Reviewer reproduced all three mutations independently: widening to include by_attribute kills only
  the control, narrowing to ("random",) kills only [blocked], ("blocked",) only [random].
Task 9: THE ROW-POSITION DEFECT, THREE TIMES IN ONE TASK. The insertion turned E-DATA-ASSIGN-METHOD's
  "unlike the two rows above" into a flat contradiction with its new neighbour (review finding); the
  FIX for that then wrote "E-DATA-ASSIGN-MISSING above" into two rows when MISSING sorts BELOW both
  (re-review finding); the controller fixed that by naming what the sibling rows DO instead of where
  they sit. Rule now in tasks 10 and 11's briefs: never write a phrase locating a row relative to a
  position. Audited the other five positional phrases in reference.md — all correct, left alone.
Task 9: the implementer went out of the brief's scope to caveat experimental-designs.md's `random`
  examples and was RIGHT to; the review then caught that the argument applied to four uncaveated
  passages in reference.md itself (§ Group axes ×3, § The resolved list order, § Clustered units).
  Pointer sentences, not rewrites — swapping an example to by_attribute illustrates a different design.
RULING (controller, from the documents, not delegated): THE LEVELS CHECK IS SET EQUALITY IN BOTH
  DIRECTIONS. § Allocation says `from` names "a unit attribute whose values are exactly the declared
  levels" and that under `between` "each unit belongs to exactly one arm". So a value naming no declared
  level is refused (that unit would belong to no arm, and `n` has no fourth part for it) and a declared
  level no unit holds is refused (that arm's condition resolves zero units). Settled at task 10 rather
  than left to a docstring because tasks 12 and 13 both depend on the answer — § Validation's
  *Attribute assignment resolves* row reads settled and is NOT (its example is disjoint, a fault under
  either reading), so task 10 amends the row too.
RULING (controller): TASK 10 PRODUCES `units.arms_of`, the single authority for the arm partition, read
  by both validate and the runner — the fifth instance of the pattern behind usable_weight,
  is_measurement_numeric, clusters_of, fold_basis. Tasks 12 and 13 CONSUME it; neither re-derives arm
  membership from the roster. This is defect class #2 (a defect living in a combination no task owns)
  headed off before dispatch rather than at whole-branch review.
Task 10: complete. Commits bb978ab (impl), e455a1e (fix round 1, all 9 findings), 6c2df18 (controller).
  1442 passed + 2 xfailed (was 1427). `units.arms_of` is the FIFTH single-authority accessor, beside
  clusters_of / usable_weight / fold_basis / is_measurement_numeric — read by validate now and by tasks
  12 and 13 later, so a config that validates cannot crash the runner. E-DATA-ASSIGN-UNKNOWN (name half,
  `from` defaulting to the axis name) and E-DATA-ASSIGN-LEVELS (set equality, both directions, one code).
Task 10: A HOLE THE IMPLEMENTER FOUND IN MY BRIEF, AND THE BRIEF WAS WRONG. I wrote that
  _check_weight_by's reasoning for silently skipping a non-`str` declaration "applies here unchanged".
  It does not: weight_by and cluster_by are envelope.py LEAF_TYPES leaves, so their silent skip defers
  to a real E-CONFIG-TYPE backstop; `assign.<axis>.from` is a DYNAMIC AXIS KEY that no fixed dotted path
  can type, so the same skip reports NOTHING ANYWHERE. `from: 3` yielded zero findings — a config shape
  validate was silent about, the inverse of what this slice hunts. Closed in-task by folding it into
  E-DATA-ASSIGN-UNKNOWN, the same absorption E-DATA-ASSIGN-METHOD already performs for a non-mapping
  block, for the identical untypeable-dynamic-key reason. The implementer documented it and deferred;
  the reviewer and I both said close it. Twelfth defective brief of the thirty-odd this project has run.
Task 10: THE ROW-POSITION DEFECT, TWICE MORE — this time in rows the diff DID NOT TOUCH. Inserting
  E-DATA-ASSIGN-LEVELS between -DRAWN and -METHOD falsified both neighbours' "immediately above/below"
  claims, which were not in the `+` lines at all. The rule as now written in every brief: never locate a
  row by position, and check every row a diff touched OR MOVED. Four instances in two tasks.
Task 10: also caught — arms_of's return value was asserted NOWHERE (grep -rn arms_of tests/ was empty);
  it was reached only through _check_assign, which discards the partition. Five direct tests added, each
  mutation-sensitive by construction: roster order over a fixture NOT in key order, stringification over
  int attributes against string levels. Tasks 12 and 13 consume exactly those promises.
PROCESS FIX: addenda now go in `task-N-addendum.md`, a SEPARATE file. `scripts/task-brief` regenerates
  `task-N-brief.md` from the plan and silently overwrote two of my addenda; I rewrote one from context
  and would have lost it outright after a compaction. Dispatches name both paths.
RULING (controller, with advisor concurrence): `groups` + `fold` IS NOT REFUSED. The composition is
  well-defined — narrow to the arm first, then partition, so each unit is in exactly one fold and the
  cross-validation happens within the arm. What is missing is only the BOUND on `k`: a small arm can
  yield an empty fold. The spec's out-of-scope table already assigns H3c-3 "`k` bounded per cell, and the
  empty-fold-per-arm case", which is a bound and not a construction, so a refusal here would narrow what
  the slice ships on account of a gap the design already routed. Task 18 records the gap; task 12 builds
  and tests the composition.
RULING (controller): the arm-narrowing predicate is `execution.condition_index is not None`, NOT a scope
  allowlist. Verified in scope.py's plan builder: `run` and `summary` executions are appended with
  condition_index=None, `condition` and `repeat` carry an index. A run-scope step runs once for the run
  and a summary-scope step once after every condition — neither belongs to an arm, and the worked
  example's step04_compare_methods IS summary scope, so an implementation narrowing at all four scopes
  is reachable and passes every test the plan's task 12 specifies. Test pair required: summary and run
  scope each receive 12, not 7 or 5.
RULING (controller): the arm narrowing must happen BEFORE runner.py's fold branch reads `units`. That
  branch builds `train=UnitList([u for u in units if u.key not in handed])`; narrowing afterwards leaves
  the OTHER ARM'S UNITS IN `train` — a training set leaking across arms, the same class as the cluster
  leak partition_units exists to prevent, and invisible to any size assertion on io.units. Required
  assertion: `.train` contains no unit of the other arm.
Task 11: complete. Commits b21f42c (impl), cbd4420 (fix round 1, all 6 findings). 1452 passed + 2 xfailed
  (was 1442). E-DATA-ASSIGN-VARIES joins CONSTANT_COLUMN_RULES, dual-listed in both reference.md tables.
  Registry shape settled: ONE "assign" entry plus a stripping lookup (declaration.partition(".")[0]),
  because the alternative — one registry entry per axis — is unimplementable: the registry is a
  module-level dict and axes are config-declared. Constraint now stated in the docstring: a registry key
  must contain no `.`, or the lookup raises KeyError, which validate's `except ContractError` would not
  catch — an escape from a module contracted never to raise.
Task 11: MY ADDENDUM WAS WRONG, AND ON THE LOAD-BEARING POINT. I wrote that one column named as both the
  arm attribute and cluster_by "SHOULD draw both codes", citing CONSTANT_COLUMN_RULES' own docstring.
  collapse_measurements RAISES ON THE FIRST VIOLATION AND STOPS, so one call reports exactly one code —
  and the reviewer established the pre-existing cluster_by+weight_by pair has ALWAYS behaved that way,
  so the docstring promising otherwise was already false before this task. Thirteenth defective brief.
  The docstring is now honest AND the reference.md row that repeated the same overclaim was caught by
  the review — the implementer had removed it from the docstring and left it in the normative document
  on the same commit.
Task 11: A PRECEDENCE NOBODY DECLARED, FAVOURING THE LEAST SEVERE CODE. `constant` was built flat-first,
  so E-DATA-CLUSTER-VARIES beat the code this slice's own prose calls the worst of the three. Fixed by
  building the assign entries first — resolution order now matches the asserted severity order — and the
  precedence is stated in both the docstring and the table row, which is exactly what
  CONSTANT_COLUMN_RULES set out to avoid ("a precedence rule nothing in the documents states"). The
  reviewer reverted the ordering by hand and confirmed the new test dies to it.
Task 11: the implementer added a `method: by_attribute` gate ON ITS OWN INITIATIVE and was right —
  `from`/`levels` mean nothing under random/blocked, so an ungated read would refuse a declaration the
  method does not use. It then claimed § Validation's *Arm is constant within a unit* row "needed no
  edit"; the review probed `assign: {arm: {}}` over varying rows, got nothing, and the row was falsified
  by the gate. Three documentation surfaces now open with "Under `method: by_attribute`,".
Controller audit at task 12 (read-only, for the whole-branch review):
  - `Condition.values` readers now number NINE, matching spec decision 2: cli.resolve_condition_cfg call
    site, cli's run.yaml conditions block, sweep_document, sweep.label_for, contrasts' free-axis match,
    validate's swept-value check (two lines, one reader), validate's confounded check,
    runner.resolve_condition_cfg's body, and units.arm_members — the ninth, added by task 12.
  - The seven spec decisions all map to tasks: 1→9, 2→3/4, 3→12, 4→15/18, 5→18, 6→16, 7→17. None dropped.
  - § Validation checks table measures 108 checks, not the 95 the plan and three scoping docs assert.
  - Seven NOT BUILT markers, exactly the seven the plan names; none in any other tracked markdown; the
    count is stated nowhere in prose, so task 17 changes markers only.
  - Five positional phrases survive across tracked markdown, all correct as of task 12; TWO ARE COUNTS,
    and one of those had already gone stale within this slice — E-RUN-ARM-UNRESOLVED turned "those five
    are core checking its own work" into six, and task 12's implementer updated it in the same commit.
PRE-FLIGHT AUDIT of tasks 13-20, run read-only while task 12's fix round was in flight. THIRTEEN defects
  found before dispatch, in briefs I wrote. This is the first time the audit ran ahead of the tasks
  rather than behind them, and it paid for itself on the first finding.
RULING (user): TASK 16b — A CONTRAST WHOSE TWO SIDES SHARE NO UNITS IS REFUSED. cli._vs_baseline_block
  hard-codes "paired": True and its own docstring says the unpaired case is "unreachable in this build"
  because E-SWEEP-GROUPS-UNSUPPORTED and E-DATA-ALLOCATION-UNSUPPORTED refuse it — THE EXACT TWO CODES
  TASK 17 REMOVES. No welch_/unpaired_ construction exists anywhere in src/. Probed: a groups axis with
  a baseline yields 2 comparisons over disjoint arms, paired_keys returns [], and every statistic
  returns None — so after task 17 a two-arm run would write {"delta": null, "paired": true,
  "n_paired": 0, "ci95": null} PER METRIC, SILENTLY, falsifying experimental-designs.md § Mistakes core
  prevents' "Paired analysis of an unpaired design" in the same slice that makes the design legal. The
  user chose refuse-not-build. New task 16b inserted BEFORE task 17 — a refusal minted after the
  retirement is a refusal that shipped too late — and it also owns fixing the docstring that motivated
  it. Owned by no task in the plan; H3c-SCOPING flagged it as a decision the plan must state and the
  plan stated neither way.
RULING (user): TASK 18 STEP 2b — write the § Mistakes core prevents row. Task 20 step 6's exit criterion
  names "two identical measurements reported as two arms" as a row in that section. THE ROW DOES NOT
  EXIST IN ANY TRACKED DOCUMENT; the phrase lives only in the gitignored scoping file. The exit
  criterion for the whole slice could not have been signed off as written.
Audit findings folded into the addenda as explicit corrections that override what I wrote:
  - t13: my "arms' resolved sum to the roster" is ARITHMETICALLY IMPLIED by pinning 7 and 5, and my own
    independence test would have certified it as independent. Replaced with coverage (union equals the
    roster's keys, intersection empty). The dominant defect class, prescribed by the brief written to
    prevent it.
  - t13: report_by has the same whole-roster defect one level down — levels_for(roster, attribute) spans
    both arms — in the very code I held up as the pattern to follow, whose own comment states the
    invariant it breaks. Owned by no task; task 13 owns it now.
  - t13: technical_n is whole-roster and would sit beside a per-arm n; the report_by branch already
    litigated this one level down and WITHHELD it. t13: consume arm_members, not arms_of — my headline
    instruction would have forced a fourth derivation.
  - t15: provenance.py BUILDS NO HASHES AT ALL (86 lines of git helpers); "the same canonicalisation"
    names no single existing thing; and the `allocation: null` line I quoted is in § The two files'
    run.yaml provenance block, not § The one config file — my pointer could have put an `allocation` key
    into the config schema.
  - t17: there is no "three refusals in the five-field loop" — the loop has TWO entries, allocation is a
    standalone if, and groups is emitted from a different function. Three sites. Files list also omits
    sweep.py and cli.py, where three unreachability claims are falsified by the retirement. And
    sweep.groups still has no _check_shape guard, routed to task 17 twice by the ledger and absent from
    its brief.
  - t19: E-SWEEP-GROUPS-PARAMETER MUST NOT BE MINTED — task 5 already closed it as E-SWEEP-PATH-DUPLICATE
    with a published row. My ruling was stated first and in bold and was wrong. Step 3's fixture also
    cannot carry a baseline: E-DATA-CLUSTER-CONTRAST refuses it outright.
  - t20: my "the NOT BUILT count is not stated in prose" was wrong — § The one config file states it
    spelled out AND enumerates all seven, and it predates this branch. The three-phrases-counting-a-table
    failure arriving inside my own audit instructions.
  - t16: the validate-exposure hazard is AttributeError on a non-mapping assign, not TypeError, which the
    existing handler does not catch. Verified clean: no test pins a digest literal.
  - t14 and t18 clean. t12's own Critical was the same class the audit exists to catch, found one task
    too late.
RULING (controller, on task 16b's shape): the identifier is E-DATA-ALLOCATION-CONTRAST, and ITS GUARD IS
  PER COMPARISON, NOT `comparisons > 0`. Its two siblings (E-DATA-WEIGHT-CONTRAST, E-DATA-CLUSTER-
  CONTRAST) fire on the whole resolved family because a weight or a cluster affects every contrast
  alike. An arm does not. § Allocation's pairing table settles it: two conditions differing on parameter
  axes only under `between` are PAIRED WITHIN THAT ARM and perfectly computable; only a pair differing
  on a groups axis is unpaired. So a `comparisons > 0` guard would refuse control-pearson vs
  control-spearman along with control-pearson vs treatment-pearson, and make "each arm analyzed three
  ways" — the design § Group axes exists to show — unexpressible. Copying the siblings is the wrong move
  here, and it is the move an implementer reading the siblings would make. Required test: a groups × grid
  config with a baseline reports the code once per CROSS-ARM comparison and not for the within-arm ones,
  asserted by count.
Task 12: complete. Commits 923c1a5 (impl), 26c7847 (fix round 1, both Criticals + four lesser).
  1465 passed + 2 xfailed (was 1452). THE ACCEPTANCE BAR IS MET: two arms get different rosters, an arm
  is a subset view of the one roster, narrowing happens before the fold branch so `.train` cannot hold
  the other arm's units, and *Arms need allocation* is implemented as E-DATA-ALLOCATION-WITHIN-ARMS.
Task 12: THE BRIEF'S HEADLINE ASSERTION WAS DECORATIVE, AND THE IMPLEMENTER PROVED IT. The plan required
  "`units_hash` over the full roster is unchanged — assert it" as the proof that an arm is a view rather
  than a re-resolution. It is not proof: a re-resolution with equal keys and attributes HASHES
  IDENTICALLY. The re-resolution mutation kills only the object-identity assertion the implementer added
  (`any(u is r for r in roster)`); the units_hash assertion never fires. Reviewer reproduced it.
Task 12: A CRITICAL THAT DEFEATED THE ACCEPTANCE BAR FROM INSIDE THE TASK THAT SET IT. Two derivations of
  "which group axes exist" disagreed: sweep.selector_paths accepts a `levels` list of ANY element type,
  cli._resolved_group_axes required str. With `levels: [1, 2]`, _check_assign reported nothing, expand
  produced 2 conditions both with selectors={'arm'}, _resolved_group_axes returned {}, the gate
  `if group_axes and roster is not None` left arm_members_map None — and BOTH CONDITIONS GOT ALL 12
  UNITS. Exactly "two identical measurements reported as two arms". No later task added a string-levels
  check and task 17 retires the refusal masking it, so it would have gone live inside this slice.
  Fixed by keying the gate off selector_paths — what expand itself agrees on — so a resolution gap
  RAISES instead of silently skipping. Second manifestation (one string axis beside one non-string)
  raises too; re-review confirmed both live, and confirmed the common no-group-axes path is unchanged.
Task 12: units.arm_members' docstring claimed a guarantee the code did not provide — a missing LEVEL
  raised, a missing AXIS was silently filtered by `if axis in partitions` and the condition vanished
  from the result. Same class as commit 4f1818a. Now indexes directly; both raise paths confirmed live.
Task 13: implementation 30c099d, fix round f44b569. 1475 passed + 2 xfailed (was 1465).
  attrition, report_by's strata and beside_n all narrow to the arm; _condition_counts /
  _condition_report_by_levels / _condition_beside_n extracted so each is directly mutation-tested.
Task 13: THE BRIEF'S OWN STEP 5 MUTATION PASSED GREEN AT THE REAL CALL SITES. Reverting all three
  call sites in command_run to whole-roster behaviour killed NOTHING in the suite; the implementer had
  mutated the extracted helper's BODY, a proxy for the fix rather than the fix, and had disclosed the
  gap for report_by only — not for the main attrition call site, which is what the task is about. After
  extracting one level further the literal mutation STILL passes: command_run's inline aggregation loop
  is unreachable end to end while E-SWEEP-GROUPS-UNSUPPORTED stands, and no task-12-style bypass exists
  for it (task 12 could call execute_plan directly with a hand-built arm_members map; there is no
  equivalent entry point here). Disclosed rather than papered over, which is the right outcome.
ROUTED: task 19 gains a step 6 — the end-to-end counting test task 13 could not write. Task 17 removes
  the refusal, and task 19 runs after it, so the route exists by then: a real between/by_attribute config
  that validates clean, run through command_run, asserting per-condition n in the written run.yaml, and
  THEN the mutation task 13 could not run. It is the only test in the slice that proves the counting fix
  is wired in rather than merely present.
Task 13: COMPLETE. Commits 30c099d (impl), f44b569 (fix round 1), 87131e7 (fix round 2).
  1476 passed + 2 xfailed (was 1465). attrition, report_by's strata and beside_n all narrow to the arm;
  _condition_counts / _condition_report_by_levels / _condition_beside_n extracted so the composed
  narrow-then-act call is the only thing command_run's loop calls — no variable that can be computed and
  silently unused.
Task 13: FINDING 1 CLOSED, NOT MITIGATED, AND THE IMPOSSIBILITY CLAIM WAS WRONG. The implementer
  reported command_run "structurally untestable end to end" while E-SWEEP-GROUPS-UNSUPPORTED stands. The
  re-reviewer disproved it by building the route: command_run gates on validate_config's has_errors, and
  the ONLY thing between a real groups config and the narrowing body is validate._check_unimplemented, a
  single isolated module-level function. Monkeypatching just that one function — the same style
  test_cli.py already uses for STARTER_STEP and GenericTemplate.aggregate — runs a real
  groups + between + by_attribute config through main(["run", ...]) to EXIT_OK with _check_assign's real
  arm-resolution doing genuine work. test_a_group_axis_actually_narrows_end_to_end now pins it, over an
  8/3 split (11 total) so every number in play is mutually distinguishable — the reviewer's 6/6 probe was
  symmetric and could not tell the arms apart by size. The Step 5 mutation against the REAL call sites
  now fails decisively (resolved: 11 instead of 8, failed: 3 bleeding from the other arm).
  The implementer's misses were both honest and both instructive: it searched for a route that avoided
  touching validate ENTIRELY, and never considered patching one function inside it. It corrected its own
  report rather than deleting the wrong conclusion.
  The test's docstring records that the monkeypatch becomes unnecessary once task 17 retires the refusal.
Task 14: implementation b15ef37, fix round in flight. 1481 passed + 2 xfailed (was 1476). allocation.json
  written from the assignment: `arms` keyed axis → level → UNIT KEYS in arms_of's resolved roster order;
  `seed` and `strata` empty because under by_attribute NOTHING WAS DRAWN and a seed would record a draw
  that did not happen; `holdout` OMITTED, following manifest/input.json's "absent rather than null"
  precedent, with the key's absence asserted in two tests so an H3d implementer cannot silently
  contradict it.
Task 14: STRONGEST QUALITY VERDICT OF THE SLICE — the reviewer could not make any probe pass vacuously,
  and every mutation it invented was caught: forcing a seed and a "holdout": None into the document,
  sorting each level's keys, nulling provenance.allocation_hash, and removing the `if not group_axes`
  gate (which proved the ABSENT test exercises the group_axes gate rather than the roster-is-None
  branch). Fixture 4/9/13 is distinct from the suite's 7/5/12 and 8/3/11 and from their sums.
Task 14: absorbed most of TASK 15 — allocation_hash and the provenance wiring — and the absorption was
  judged sound. Task 15 RESCOPED to the four items that remain: the swap-two-units hash assertion in its
  discriminating form (reassigning ONE unit also changes the input table, so a hash covering the roster
  would move for the wrong reason and the test would prove nothing); verifying the bytes-vs-canonical
  docstring fix; stating that § Resuming's "read rather than re-drawn" rule HAS NO READER, since
  OPERATION_COMMANDS = {"validate", "run"}; and a stated reason why allocation_hash lives in artifacts.py
  rather than as a fourth entry in hashes.py.
Task 14: two findings in its own fix round — a docstring claiming the hash covers "exactly the bytes
  written" when it covers the CANONICAL form (measurably different: sha256:2e77fae5… vs sha256:887307da…,
  and the canonical form reorders the keys), and reference.md never stating what a by_attribute axis
  writes into seed/strata, so the omit rule lived only in a docstring and two tests with H3d editing the
  same file and nothing normative to follow.
Task 14: COMPLETE. Commits b15ef37 (impl), f7a02db (fix round 1, all three). 1481 passed + 2 xfailed.
  Re-review verified the corrected docstring empirically — the two digests really do differ and the
  canonical form really does reorder the keys — and confirmed the new reference.md sentence matches what
  the code does ("the axis is left out of both seed and strata") rather than the different and tidier
  claim it might have made (an empty per-axis entry). Zero code lines changed in the fix.
Task 15: COMPLETE, NO FINDINGS — the first clean pass of the slice. Commit b4858e7. 1482 passed +
  2 xfailed. Rescoped to four items after task 14 absorbed the mechanism; all four verified.
  The swap test is genuinely discriminating: the reviewer mutated allocation_hash to hash the sorted set
  of ALL unit keys (roster-shaped, ignoring which arm) and confirmed the test FAILS — and further
  confirmed that under that mutation the pre-swap and post-swap documents hash IDENTICALLY, which is
  exactly the "covers the roster rather than the assignment" defect the swap form exists to catch. A
  reassignment test could not have caught it.
  THE BRUTE-FORCE WAS HONEST, and worth recording because it looks like the opposite. My addendum quoted
  two digests without naming which pair produced them; the implementer brute-forced all control ×
  treatment pairs to find the pair reproducing the reviewer's independently measured values, rather than
  inventing new ones. The search was over WHICH INPUT to use, not over the algorithm or the assertion —
  the code under test was untouched — so the expected digests are real reproducible outputs, not values
  fitted to make an assertion pass. The reviewer checked this specifically.
  Item 3 is a statement, not a test, as required. The sentence task 18 quotes: `allocation.json`'s "read
  rather than re-drawn on resume" rule has no reader in this build — OPERATION_COMMANDS = {"validate",
  "run"} contains no `resume` command, so nothing calls build_allocation_document a second time against
  an existing file, and no test exercises this path.
  Item 4: allocation_hash lives in artifacts.py because it follows manifest_hash's pattern — hashing what
  its own module built — rather than hashes.py's, where every entry hashes something the caller already
  has. A real distinguishing argument, verified against both modules.
Task 16: COMPLETE, NO FINDINGS. Commit a6a15d3. 1486 passed + 2 xfailed. assign.<axis>.seed is now
  excluded from design_digest PER AXIS, so pinning a seed no longer moves the digest that seed is itself
  mixed with — the self-referential derivation § What `auto` derives from already ruled against.
  The surgical property is genuinely tested: the reviewer widened the carve-out to drop the whole assign
  subtree and exactly one test failed, the one written for that purpose. "Excluded assign.seed" and
  "excluded assign" are therefore distinguishable, which is what the addendum's four extra cases bought.
  The implementer sidestepped the addendum's own corrected hazard (AttributeError on a non-mapping
  assign, which sweep.py's `except TypeError` would not catch) by guarding with isinstance throughout
  rather than catching anything — so no sweep.py change was needed at all. Verified: design_digest does
  not raise on a non-mapping assign, a non-mapping axis block, or seed: None.
  No doc edit needed — task 1 had already amended § What `auto` derives from, so the document led and the
  code followed, which is the order CLAUDE.md requires.
Task 16b: COMPLETE. Commits ca814a3 (impl), 6c7dcea (fix round 1, all five). 1490 passed + 2 xfailed.
  E-DATA-ALLOCATION-CONTRAST refuses a contrast whose two conditions differ on a groups axis, PER
  COMPARISON — the reviewer probed a real groups × grid config twice, before and after a three-file
  refactor, and confirmed the refusal fires on exactly the two cross-arm comparisons and names neither
  within-arm one. A comparisons > 0 guard copied from the siblings would have made "each arm analyzed
  three ways" unexpressible.
Task 16b: MY BRIEF NAMED A FUNCTION THAT DOES NOT EXIST — `_vs_baseline_block`; the hard-coded
  "paired": True lives in `_comparison_step_blocks`. Fourteenth defective brief. The implementer treated
  it as a naming slip rather than a wrong premise and fixed the real site.
Task 16b: TWO PRE-EXISTING TESTS ALREADY CONTAINED CONFIGS THAT TRIGGER THE NEW REFUSAL — a baseline
  fixing a group axis to one arm. The implementer updated their expected sets rather than calling it a
  regression, which is the change most likely to hide a defect; the reviewer checked each by dumping the
  resolved comparisons and both are genuinely correct, not weakened.
Task 16b: THE REVIEWER CORRECTED MY ADDENDUM. I claimed controls (a) and (b) would both fail under
  widening. Measured: (b) and (c) die to a family-level (comparisons > 0) widening; (a) dies only to a
  declaration-level one, having no comparisons for a family guard to reach. The three cover both
  widenings, but not for the reason I gave.
Task 16b: a Critical the brief did not ask for and CLAUDE.md's cross-document pass did — the code had a
  row in § Errors `validate` reports but NONE in § Validation's check table, whose intro says it "states
  each check by the mistake it catches". Both siblings and E-DATA-ASSIGN-DRAWN have one. Now
  *Allocation deltas aren't computed*, in the allocation cluster.
  Also fixed: the paired: True docstring had no EXPIRY — it said which claim it is but not that retiring
  this very code falsifies it, the same displaced staleness the task existed to fix, one slice later.
  And `differing_axes` moved from cli.py to contrasts.py, ending a layering violation where validate
  function-locally imported a cross-module private from a layer above it.
Task 17: implementation f71b1d4, fix round in flight. 1488 passed + 2 xfailed (1490 before — the
  refusal tests went with the refusals). THE THREE RETIREMENTS ARE DONE: E-SWEEP-GROUPS-UNSUPPORTED,
  E-DATA-ALLOCATION-UNSUPPORTED, E-DATA-ASSIGN-UNSUPPORTED. NOT BUILT seven → four; the sentence, the
  spelled word and the enumeration all changed, and the four surviving markers were counted independently.
Task 17: THE CHECK-OFF EARNED ITS KEEP — a live, previously undocumented defect the retirement would
  have made real. `groups: [{by: arm, levels: [a,b]}, {by: arm, levels: [c,d]}]` produced four conditions
  labelled ['arm=c','arm=d','arm=c','arm=d']: THE FIRST AXIS'S LEVELS ENTIRELY ERASED, and two label
  pairs byte-identical, so two condition directories would collide. Fourth instance in this project of
  "a retirement makes a latent defect live", and the first found empirically rather than by reading.
  Closed by reusing E-SWEEP-PATH-DUPLICATE, judged right on three tests: § Validation's *Axis names are
  distinct* pre-dates the task and that table has no code column, so reuse contradicts nothing; the
  registry row was extended in bold and already carried two distinct faults, so a third sibling is the
  established shape of that row rather than a conflation; and the emitted `where` matches the adjacent
  group-axis emit. It survives deletion of the whole by_names accumulation, a stronger mutation than the
  implementer ran. Worth knowing: this is the one genuinely new behavioural change inside the
  irreversible task, and it went in unreviewed until the task review caught up with it.
Task 17: also minted E-DATA-ALLOCATION-METHOD, backing the out-of-enum `allocation` claim that
  E-DATA-ALLOCATION-UNSUPPORTED's blanket refusal used to carry — pre-specified by task 12's reviewer,
  code name and all, in spec-defects.md. That is the routing working: a gap named at task 12, closed at
  the task that made it live.
Task 17: THE METHODOLOGICAL LESSON. The implementer ran a CONCEPT-level sweep on the documents — which
  is how it caught W-STATS-REPORTBY-THIN, outside my addendum's code-name grep — but only a code-NAME
  sweep on src/. All three required-before-merge items are things a code-name grep cannot see:
  materialize.py shipping `allocation: within # within (between: later slice)` INTO EVERY SCAFFOLDED
  CONFIG with a test locking the string in; two § Validation rows asserting min_units_per_cell warnings
  that have no code anywhere, now reachable; and a comment this task WROTE whose `levels: []` example is
  unreachable (that config expands to zero conditions and E-SWEEP-EXPANDS-EMPTY refuses it).
RULING (controller): min_units_per_cell — HEDGE THE DOCUMENT, DO NOT IMPLEMENT THE WARNING. It was never
  implemented for `within` designs either, so task 17 makes a pre-existing gap REACHABLE rather than
  creating one, and a new W- code is scope creep into the limits family. But spec-defects.md is
  gitignored and invisible to every reader of the normative document, so recording there is not enough.
  § Validation already has the convention and these two rows do not use it: *Assignment method isn't
  drawn* and *Allocation deltas aren't computed* both say "specified, not built in this build".
Task 17: A GREP THAT FAILED SILENTLY, LIVE, DURING THE REVIEW — the reviewer's own first sweep reported
  zero hits for reference.md because it piped through `grep -v superpowers`, and the one true hit is a
  line containing the string `docs/superpowers/spec-defects.md`. Precisely the failure step 6's
  positive-control requirement exists to catch, hit by the person checking for it.
Task 17: COMPLETE. Commits f71b1d4 (retirement), b7af7a5 (fix round 1, all three required + all three
  recommended). 1488 passed + 2 xfailed. All three required items verified by probe, not by reading:
  - init's scaffolded comment is now `within | between`, and test_materialize.py's marker dict updated
  - min_units_per_cell hedged in three places to match the sibling "specified, not built in this build"
    rows; the NOT BUILT count correctly left alone, since that marks DECLARATIONS and this is a WARNING
  - the false `levels: []` comment replaced with `by: ""`, and the reviewer probed the replacement:
    selector_paths returns [''] (isinstance(by, str) is true for ""), expand produces two real
    conditions labelled =a/=b with selectors == frozenset({''}), _resolved_group_axes skips it because
    "" is falsy, and validate does NOT refuse it. The substituted example is true where the original
    was vacuous.
ROUTED to task 18: the min_units_per_cell hedge is TRUTHFUL BUT UNDER-SPECIFIC. It is a bare "specified,
  not built" tag where its two sibling hedges explain their mechanism. The controller had already probed
  the distinction it needs to draw: units.arms_of refuses a declared level NO UNIT HOLDS, so an EMPTY arm
  is already caught by E-DATA-ASSIGN-LEVELS; the genuinely uncovered case is a ONE-UNIT ARM, which
  validates clean and produces a basis: units interval over n = 1. Task 18's addendum already carries
  this with the instruction to say the failure rather than the abstraction.
Task 18: implementation 1bd48e5, fix round in flight. Documentation only. Spec ✅ — every added sentence
  RECORDS A GAP rather than legislating a rule, which was the direction CLAUDE.md gives and the failure
  mode this task existed to avoid.
Task 18: THE EXIT ROW EXISTS NOW, AND IT SURVIVED ITS HARDEST TEST. *Two identical measurements reported
  as two arms* is in experimental-designs.md § Mistakes core prevents, resting on
  E-DATA-ALLOCATION-WITHIN-ARMS (primary), E-DATA-ALLOCATION-NO-ARMS and E-DATA-ALLOCATION-CONTRAST. The
  reviewer hunted for a remaining route and FOUND NONE — including the one it went looking for, a group
  axis declared with NO ROSTER so both arms would be repeat-basis and identical: closed by the chain
  E-DATA-ALLOCATION-NO-ARMS → E-DATA-ASSIGN-MISSING → -METHOD → -UNKNOWN, since with no data.units the
  attributes list is empty. You cannot declare a group axis without a roster.
  The implementer dropped a citation of `units.arms_of` from the row because no sibling row in either
  Mistakes table names an internal Python symbol — judged right. validate.py's own docstring
  independently phrases the mistake the same way, so the row is faithful to what was built.
Task 18: MY ADDENDUM OVERCLAIMED A PROBE, AND THE REVIEW CAUGHT IT. I wrote that a one-unit arm
  "produces a basis: units interval over n = 1" and presented it as probed, when only the arms_of and
  min_units_per_cell halves were. Every interval construction in stats.py RETURNS None BELOW TWO VALUES,
  and summarize_step's docstring says why: "there is no dispersion to describe and inventing an interval
  for it would not be honest". A one-unit arm gets a point estimate with ci95: null — core behaving
  correctly. The recognisable failure is a TWO-UNIT ARM: validates clean, real interval from two
  observations, nothing warns. Fifteenth defective brief, and the first where I mislabelled reasoning as
  measurement.
Task 18: the implementer found ONE ITEM NOT IN THE STATE MY ADDENDUM CLAIMED — the W-STATS-REPORTBY-THIN
  table row still said "this build cannot yet construct" while the prose beside it had been updated
  post-task-17 to "Reachable now." Fixed the row to match. That is the check-the-claimed-state
  instruction working.
Task 18: COMPLETE. Commits 1bd48e5 (records), 0844f9b (fix round 1, all six). Documentation only;
  1488 passed + 2 xfailed unchanged. Four gaps recorded durably in reference.md/experimental-designs.md
  rather than in the gitignored spec-defects.md; four more verified already recorded by tasks 13/14/17.
  The one-unit/two-unit correction is verified against stats.py at both boundaries: t_over_units returns
  None at n < 2, and computes a real Interval at n == 2 (df = 1, finite t_critical). So the sentence now
  says a single-unit arm is NOT the uncovered case — core already declines to interval it — and a
  two-unit arm is: passes validate clean, reports a real basis: units interval, nothing warns.
Task 19: implementation a90d6ab, fix round in flight. 1495 passed + 2 xfailed (was 1488). Spec ✅.
Task 19: STEP 6 CLOSES THE HOLE TASK 13 DISCLOSED AND COULD NOT CLOSE. The reviewer ran the mutation
  independently at all four sites — each of command_run's three narrowing call sites individually and
  all three together — and the new end-to-end test FAILS every time. The per-arm counting fix is pinned
  where it matters, not merely present. That was the single test the slice hinged on, and it only became
  writable once task 17 retired E-SWEEP-GROUPS-UNSUPPORTED, which is the whole reason step 6 was routed
  to task 19 rather than left as task 13's disclosed gap.
Task 19: STEP 2 FOUND A REAL GAP. E-SWEEP-PATH-DUPLICATE compared a groups axis's `by` only against
  SWEPT paths (grid/paired/sample), missing a `by` naming a path the template declares as a parameter
  but nothing sweeps. Confirmed by restoring the previous validate.py: the new test fails with the code
  absent, and the harm assertions pass on the old code, so the harm predates the fix. Extended rather
  than minted, per the addendum's ruling — judged not a conflation, because both halves are ONE fault (a
  `by` naming a parameter path, so expand marks it a selector and the label claims a value nothing
  plants); the swept half merely strands another axis, a wider consequence rather than a different fault.
ROUTED to task 20: the expand INDEX ORDER divergence. spec-defects.md § Per-cell baseline numbering
  records it but argues the interleaved rule is ill-defined ONCE A SECOND AXIS EXISTS, and EXPLICITLY
  EXEMPTS the single-group-axis case — which is exactly the case § Expansion modes prints. So the code
  diverges from the document precisely where the recorded excuse does not apply, and the record does not
  cover it. The entry names "the groups slice" as owner with a document decision as its deliverable;
  task 19's reviewer grepped this slice's plan, its design spec and H3c-SCOPING and found no mention, so
  whether that means this slice is unresolved. Task 19 deletes the one assertion pinning the current
  order so nothing entrenches an answer before task 20 picks one.
Task 19: FIX ROUND 2 — THE FIFTH COULD-NOT-FAIL CHECK OF THE SLICE, and a clean instance of the class.
  The new end-to-end groups × cluster_by test passed; the reviewer mutated runner._counts to count
  clusters over the WHOLE ROSTER instead of the arm's completed units — the exact bug the test was
  written to guard — AND IT STILL PASSED. The fixture made every site span both arms, so the arm-scoped
  and roster-scoped counts are both 3 on each side: the correct answer coincides with the buggy one and
  no assertion on those numbers can separate them. The docstring claimed the test proved per-arm
  counting; it proved the combination runs.
  Required fix: one site with units in only one arm, so that arm's count differs from the roster's —
  while KEEPING a cluster that spans both arms, since § Clustered units says that is not merely legal
  under by_attribute but universal in matched case-control. The fixture must show both shapes and still
  discriminate, which is the arm/cluster partitions-must-cross rule in its sharpest form.
  Second time in this slice the mutation had to be run at a level the test never reached (the first was
  task 13's call sites). The lesson both times: RUN THE MUTATION BEFORE BELIEVING THE TEST, and run it
  where the behaviour lives rather than where the test looks.
Task 19: COMPLETE. Commits a90d6ab, a6edefd, bb99bec, 82152d9. 1496 passed + 2 xfailed. Three fix rounds.
Task 19: THE ARCHITECTURAL FINDING, VERIFIED WITH ONE CORRECTION. runner._counts' clusters figure NEVER
  REACHES A run.yaml: stats.summarize_step recomputes a recorded column's cluster count from that
  column's own carrier keys, overwriting attrition's. Proven by mutation — mutating runner._counts fails
  only three direct-attrition tests and NO end-to-end test. The fixture fix alone therefore could not
  make the reviewer's mutation fail, and the test was retargeted to the site that actually produces the
  observed number.
  THE REASON GIVEN WAS WRONG, in the direction that stops a reader checking: the derived path is NOT
  "refused unconditionally under cluster_by". stats.py's gate also requires a seed and a non-empty
  drawable set, and the derived block is a LIVE CONSUMER passing attrition's figure straight through. It
  closes only because command_run always supplies both — a fourth call site omitting either would
  silently publish the other figure.
  DISPOSITION (controller): LEAVE AND RECORD. A correct computation whose consumer is temporarily
  refused, not dead code. Deleting it would break _counts' no-default discipline (its own docstring:
  a fourth return site added later cannot forget a key), E-DATA-CLUSTER-DERIVED is marked Temporary in
  two places with H4 named as the lifter, and reference.md's promise that `n` carries a cluster count is
  delivered today by the per-column recompute — identical to attrition's for a full column, correctly
  narrower for a ragged one. No doc/code divergence, so no spec-defects entry and no new code.
  Final fixture: control {A,A,B,B,C,C,C} = 3 clusters, treatment {A,B,B,D,D} = 3, roster {A,B,C,D} = 4.
  A and B span both arms (the by_attribute legality § Clustered units requires stay represented); C is
  control-only and D treatment-only, and those are what make 3 distinguishable from 4.
Task 20: implementation 3059ed1 + c6ef6e1, FIX ROUND IN FLIGHT ON A CRITICAL. 1497 passed + 2 xfailed.
Task 20: THE EXIT CRITERION FAILED, AND THE FAILURE IS THE NAMED MISTAKE ITSELF. A duplicate level on a
  groups axis — `levels: [control, treatment, control]`, a plausible typo — produces three conditions
  where 00_arm=control and 02_arm=control are BYTE-IDENTICAL AT EVERY FILE, units.parquet and
  ineligible.jsonl sha256s matching across all five seed repeats. validate exits 0 with "✓ config valid"
  and no warning; sweep.yaml records index 0 and index 2 with the same label and the same values. That is
  experimental-designs.md § Mistakes core prevents' *Two identical measurements reported as two arms*
  verbatim. The row's three codes all guard the within/no-axis route; NOTHING guards duplicate levels
  inside one axis, E-SWEEP-PATH-DUPLICATE is across entries' `by` rather than within one entry's levels,
  and arms_of's set equality holds because {control} == {control}. Fix: mint E-SWEEP-LEVEL-DUPLICATE.
Task 20: THE METHODOLOGY LESSON, WHICH MATTERS MORE THAN THE BUG. Task 20 ran 19 adversary shapes, 13 of
  them nobody had named, each driven to a real run.yaml — careful work, and the reviewer confirmed it.
  But ALL 19 RAN AGAINST A SINGLE 8/3 ROSTER, so every set-equality refusal in the table was
  ROSTER-INCIDENTAL rather than structural: its case D is the same config as the reviewer's probe and
  refused only because that roster carried 3 treatment units naming no declared level. The set was
  enumerated over CONFIG SHAPE while the exit criterion is a property of ROSTER CONTENT. Sixth
  could-not-fail instance of the slice, and the first at the level of a whole adversary suite rather
  than a single check.
Task 20: also found — `by: "arm."` reaches the exact outcome the new blank-`by` refusal exists to
  prevent, because label_for uses path.rsplit('.', 1)[-1], so it renders an empty axis name: labels
  ['=control', '=treatment'], directories 00_=control, exit 0, nothing reported. The refusal's own
  registry row justifies itself by naming directories "nothing else in this project would produce" —
  and this produces precisely that, while passing by.strip().
Task 20: the index-order divergence was recorded ONLY in the gitignored spec-defects.md — the precise
  failure task 18 existed to prevent, arriving in the task that ran the consistency passes. Durable note
  now required in reference.md at both printed sites. The disposition (do not renumber; it changes
  condition directory names and sweep.yaml indices) is right and stands.
Task 20 verified, both directions: 137 source codes, 122 registry codes, 0 registry-not-in-source, 15
  source-not-in-registry (4 -UNSUPPORTED + 11 pre-existing command-level, all already recorded). The
  § Validation checks table is 101 CHECKS — not the 95 three scoping documents say, nor the 108 my
  addendum measured (that count included both tables and the header). NO TRACKED *.md STATES A COUNT,
  verified with digit and spelled-number greps, so nothing is stale in the four documents.
Task 20: THE EXIT CRITERION HOLDS. The reviewer re-ran the Critical end to end on its own harness,
  reproduced the pre-fix failure under its OWN mutation (byte-identical directories, matching digests on
  both the mixed and all-control rosters), and confirmed every duplicate-level route is refused at
  validate with run creating no run directory. It then hunted for the next one WITH THE ROSTER VARIED —
  whitespace-variant levels (refused structurally by E-SWEEP-VALUE-UNNAMEABLE, so they never reach the
  duplicate check), case-differing levels (correctly two distinct arms; arms_of does no case folding), a
  duplicate in a second axis while the first is clean, and a duplicate crossed with ablate — and found
  nothing. `dry-run`, `draft` and `resume` are not commands in this build, so run and validate are the
  whole executing surface and both refuse: that is what makes it structural rather than run-only.
  E-SWEEP-LEVEL-DUPLICATE, mutation-proven three ways including a control that is NOT vacuous (hoisting
  `seen` out of the per-entry loop fails the two-axes-sharing-a-level test).
Task 20: THE IMPLEMENTER'S OWN ACCOUNT OF THE MISS, WHICH IS THE MOST VALUABLE LINE IN THE SLICE —
  "Case D was the same Critical, and I reported it 'refused.' On my one mixed roster it drew
  E-DATA-ASSIGN-LEVELS — a code about the DATA. On an all-one-arm roster it runs green with two
  byte-identical condition directories. I recorded the right outcome for the wrong reason and called the
  sweep complete." The rule in its learned form: enumerating over config SHAPE does not test a property
  of roster CONTENT, and A REFUSAL THAT HAPPENS TO FIRE HAS TO BE ATTRIBUTED BEFORE IT CAN BE COUNTED.
  Re-run classification, independently confirmed: C, D, N roster-incidental; the other 16 structural.
  Sharpening the reviewer added: H, Q and R keep a structural refusal on all three rosters but pick up
  an extra E-DATA-ASSIGN-LEVELS on the non-mixed ones — THE CODE SET MOVES EVEN WHERE THE VERDICT DOES
  NOT, so comparing verdicts alone would have hidden the attribution problem.
Task 20: the wrong positional phrase was introduced BY THE COMMIT THAT RAN THE POSITIONAL AUDIT. The
  implementer named this itself. Strongest evidence in the slice that the defect class is structural
  rather than a matter of care — the person checking for it wrote one while checking.
Task 20: COMPLETE. Commits 3059ed1, c6ef6e1, 87b3ff7, 438ef92. 1501 passed + 2 xfailed.
  The false consequence corrected in all three places that carried it. The implementer named the class
  itself: "my own step 4 defect class one level up — a justification true of the instance and false of
  the general claim." The crossed case (groups × grid with a duplicated grid value) is now PINNED AS
  UNREFUSED in the suite, so the recorded gap is visible and a later slice closing it has exactly one
  assertion to change.
  The blank-name class closed as a CLASS: inverted to an allowlist over sweep.NAMEABLE_CHAR, which
  SWEPT_VALUE_PATTERN is now built from — one alphabet, two strictnesses (a swept VALUE must be made
  entirely of it; a group axis's rendered NAME must contain at least one). Reuses the rule § How
  artifacts are organized already states rather than inventing a second. The test first asserts
  `.strip()` would NOT have caught each invisible, so it discriminates the allowlist from the denylist
  rather than merely re-passing — three mutations in both directions.
ALL TWENTY-ONE TASKS COMPLETE (1-20 plus 16b). 1501 passed + 2 xfailed, ruff and mypy clean.
  Branch h3c1-arms-read, 31 commits over cb96c7d. Ready for whole-branch review.
WHOLE-BRANCH REVIEW: ONE CRITICAL, and it is the acceptance bar defeated by the documented feature.
  A groups axis plus a `baseline` fixing one of its levels renders that arm TWICE: _baseline_cells and
  _axes both emit it, so `00_baseline` and `01_arm=control` come out BYTE-IDENTICAL at every artifact
  across all five seed repeats, validate reporting ZERO findings and run exiting 0. At >= 2 levels it is
  masked by E-DATA-ALLOCATION-CONTRAST — a refusal reference.md calls TEMPORARY, promising it lifts with
  the unpaired estimator family — and at ONE level nothing masks it. Not a corner: § Group axes
  documents `baseline: {arm: control}` as the way to designate the control arm, and arms_of's set
  equality forbids omitting a level from the roster, so EVERY control-arm baseline renders twice.
  E-SWEEP-ABLATE-BASELINE-GROUP already refuses this exact shape under `ablate` for the WEAKER reason
  (a level executed by NO condition); the plain product case — a level executed TWICE — was unrefused.
RULING (user): REFUSE IT — ARMS ARE PEERS. Extend the existing refusal from the ablate case to the plain
  product case: a baseline may never fix a group level. Consistent with the rule already enforced and
  with § Expansion modes' own words ("the arms are peers"). § Group axes' "designate the control arm"
  passage is rewritten and that job routes to statistics.contrasts, which already expresses a named
  comparison. Rejected: suppressing the duplicate cell (changes expansion semantics late, and every
  condition-count and label assertion on the branch would need re-verifying) and refusing only where it
  duplicates (an unreachable exception nobody could state).
WHOLE-BRANCH CRITICAL: CLOSED. Commits cd8d972, 7d324fc (implementer), plus the controller's message fix.
  E-SWEEP-BASELINE-GROUP minted as an EXCLUSIVELY-GUARDED SIBLING of E-SWEEP-ABLATE-BASELINE-GROUP
  rather than widening it — and the verifier confirmed the distinction is real by enumerating `expand`
  rather than reading the comment: under `ablate` over group axes the crossed branch SUPPRESSES the
  product rows, so the level is NOT duplicated and the other levels execute nowhere; without `ablate`
  the level IS duplicated. One widened code would have been false about one of the two shapes.
  Verified closed by reproduction at 438ef92 (zero findings, exit 0, byte-identical directories) and
  refusal at HEAD on both the one-level and two-level shapes, with NO RUN DIRECTORY CREATED either time.
  No cross-arm route to two identical rosters survives: a repeated level (E-SWEEP-LEVEL-DUPLICATE), two
  axes sharing a `by` (E-SWEEP-PATH-DUPLICATE) and a baseline fixing a level (E-SWEEP-BASELINE-GROUP)
  are the three, all refused; 16 sweep blocks plus a green `between` matrix enumerated with no unrefused
  pair in DIFFERENT arms holding equal (values, selectors).
  § Group axes rewritten: the arms are peers, and the named comparison routes to statistics.contrasts —
  WITH THE BUILD RESTRICTION ATTACHED, so the document does not promise something E-DATA-ALLOCATION-
  CONTRAST refuses.
  THE EIGHTH INSTANCE OF THE CLASS, AND THE CONTROLLER FIXED IT: E-SWEEP-BASELINE-GROUP's message
  asserted the level "is rendered twice" unconditionally, but the guard is keyed on the PATH and never
  on the value — a baseline fixing a group path to a value naming NO declared level is refused by the
  same rule and duplicates nothing. The code comment admitted the exception; the user-visible string did
  not, and a test pinned the unconditional wording. Message now states both shapes.
  Four parameter-axis routes to identical conditions remain, all pre-existing in that form and all
  recorded: baseline fixing a grid value (reports LITERALLY NOTHING), a baseline equal to a default, a
  repeated `paired` row, and a repeated `grid` value. The verifier confirmed § Mistakes core prevents
  does NOT overclaim — its row is about two identical measurements reported as two ARMS, and crossing
  these with a group axis puts the duplicated pair INSIDE one arm.

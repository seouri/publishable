# SDD ledger — plan: docs/superpowers/plans/2026-08-14-arms-drawn.md

Branch h3c2-arms-drawn, forked from main at 39c6667 (the H3c-1 merge).
USER DIRECTIVE: execute to merge and push without check-ins. Any decision that would otherwise be
an AskUserQuestion is taken by the controller as the option it would have recommended, and RECORDED
HERE with its grounds so the user can audit every one of them afterwards.
Spec: docs/superpowers/specs/2026-08-14-arms-drawn-design.md
Scoping: docs/superpowers/H3c-2-SCOPING.md
Decisions already settled by the user before execution: (1) `blocked` beside a declared cluster_by is
REFUSED; (2) limits.min_units_per_cell stays unowned and hedged.
Controller decision at plan time: block_size: auto under ratio: {} is TWICE THE LEVEL COUNT, because
{} is equal allocation so the implied sum is the level count.
PLAN SELF-REVIEW CAUGHT ONE: task 4's test named E-CONFIG-UNKNOWN; the real code is
E-CONFIG-KEY-UNKNOWN (envelope.py). Fixed before dispatch.

Task 1: DONE (recon; no tracked files changed, so no commit). 1502 passed + 2 xfailed.
  Controller verified the inventory independently rather than dispatching a reviewer for an empty
  diff — DECISION RECORDED: a task whose deliverable is a report and which changes no tracked file
  gets a controller spot-check of its load-bearing claims instead of a task reviewer. Confirmed by my
  own sweep: 9 sites in reference.md + 1 in experimental-designs.md name the code string, with a
  present-control (E-DATA-ASSIGN-LEVELS, 2 hits) and an absent-control (0 hits) both behaving.
  Six source/test files also name it: units.py, validate.py, cli.py, artifacts.py, test_cli.py,
  test_validate.py.
Task 1 finding — MY BRIEF UNDERCOUNTED. "Ten independent prose sites" counts only the code STRING.
  Two further sentences describe the same fact without naming it (reference.md § Expansion modes and
  experimental-designs.md § Crossed group axes, both "carries the same refusal ... as the single-axis
  example above"). Task 14 works from TWELVE doc sites plus the six source files, not ten.
Task 1 finding — the `ratio`-under-by_attribute gap is CONFIRMED LIVE, not a not-built refusal.
  reference.md § Allocation asserts "under `method: by_attribute` a `ratio` describes a draw that
  didn't happen, so `validate` rejects a non-empty one"; `ratio` appears ZERO times in validate.py.
  by_attribute is the method that executes today, so this is a live divergence. Task 5 owns it.
Task 1 finding — routed to tasks 5/10/12/13: *Ratio names levels* and *Allocation strata exist* read
  as METHOD-INDEPENDENT from their own wording, but only apply under random/blocked; the surrounding
  prose carries that gating. Implementers must gate rather than re-derive it from the row alone.

Tasks 2+3: commits 704111c, 98086c5, 77ee13a, 6923b07 (the last two the implementer's own advisor pass).
  Spec ✅. Doc-only; 1502 passed + 2 xfailed throughout. Reviewer verified ruling 2's arithmetic, the
  registry sort across all 91 codes, and — by grepping the phrasing that could carry the old reading
  WITHOUT the word `blocked` — that no third stale cluster claim survives.
CONTROLLER RULING A (would have been a user question; user directed me to decide): REFUSE
  `stratify_by` UNDER `by_attribute`, the way `ratio` is refused. § Manifest already calls it "the same
  fault" as the ratio case and § Allocation refuses the ratio; the document was declaring two things the
  same fault and refusing only one, and the new row made that WORSE by stating non-coverage explicitly —
  a harder claim than the ambiguity it replaced. Same fault, same treatment. Task 5 owns both halves.
  This also RATIFIES the implementer's method gate on *Allocation strata exist*, which neither brief
  asked for: gating the row to the drawing methods is right GIVEN by_attribute gets its own refusal, and
  was wrong only while that refusal was missing.
CONTROLLER RULING B: DROP "earlier-resolved" from E-DATA-ASSIGN-STRATIFY-UNKNOWN's registry row. As
  written it covered a fault belonging to a DIFFERENT § Validation row — `assign.sex.stratify_by: [arm]`
  with arm declared after sex is verbatim *Stratification is forward-only*'s example, which task 13
  implements with its own test. One code answering to two rows breaks § Validation's own promise that
  "a row here and a code there are the same check seen from the two ends". Existence is this code's
  fault; ORDER is task 13's, and TASK 13 MINTS E-DATA-ASSIGN-STRATIFY-FORWARD (that row has no code at
  all today — pre-existing, confirmed at the fork point and in the scoping).
Routed to task 11: it owes TWO rows for E-DATA-ASSIGN-BLOCKED-CLUSTER — registry AND § Validation.
Controller decision: the three forward references (a code named in prose before its row) stay UNMARKED.
  Tasks 10-14 land before any mechanical pass, and a marker someone must remember to remove is worse
  than a forward reference.

Task 4: commit 1b5d909, fix round in flight. 1503 passed + 2 xfailed. Spec ✅.
  `data.units.assign`'s per-axis blocks are closed to {method, from, ratio, block_size, stratify_by,
  seed} — the gap the PREVIOUS SLICE was assigned and did not ship, and which would have made all four
  of this slice's new keys silently ignorable. Closed one level down, because the axis keys are
  user-chosen names no fixed dotted path can reach; that is why it needed its own function rather than
  the generic LEAF_TYPES closure. Same code and same message format as the generic emitter — verified
  no divergence in the message text.
Task 4: the implementer accidentally ran `git checkout --` on its own uncommitted implementation and
  redid it from scratch, re-verifying before reporting. Recorded because the RECOVERY was right: no
  unverified state was ever reported as done, and the reviewer confirmed the committed result is
  coherent rather than a partial reconstruction.
Task 4: two Importants in the fix round — the new test covered only 2 of the 6 keys (the other four
  rested on incidental hits from unrelated tests, or nothing), and E-CONFIG-KEY-UNKNOWN's registry row
  described only the generic emitter when there are now two.
Task 4: COMPLETE. Commits 1b5d909, 0051c29. 1509 passed + 2 xfailed. All six keys parametrized and
  mutation-proved INDEPENDENTLY — each removed from ASSIGN_AXIS_KEYS in turn, only that key's case
  failing. E-CONFIG-KEY-UNKNOWN's row now names both emitters.

Task 5: commit e54736f, fix round in flight. 1516 passed + 2 xfailed. Spec ✅.
  Closes the LIVE divergence: reference.md § Allocation asserted a non-empty `ratio` under by_attribute
  is rejected and nothing read the key at all. E-DATA-ASSIGN-RATIO (*Ratio names levels*, gated to the
  drawn methods) and E-DATA-ASSIGN-NO-DRAW (the by_attribute whole-field refusal, covering BOTH `ratio`
  and `stratify_by` per ruling A).
IMPLEMENTER DECISION UPHELD: one shared code for the two by_attribute faults rather than two. § Allocation
  and § Manifest both call them "the same fault" verbatim; they fire on the identical condition for the
  identical reason with the identical remedy and differ only by path, which the findings carry;
  E-DATA-ASSIGN-LEVELS is in-function precedent for one code over two directions; and a -STRATIFY split
  would collide with E-DATA-ASSIGN-STRATIFY-UNKNOWN, a different fault task 12 owns. The reviewer
  confirmed a reader loses nothing, and that the gating is mutually exclusive BY CONSTRUCTION — the two
  checks sit in different arms of one if/elif chain over the same method value.
Task 5 Critical: A MUTATION SURVIVED THE WHOLE SUITE. Replacing set equality with "every declared level
  has an entry" left 1516 green, because the undeclared-level fixture `{control: 1, f: 2}` is
  SIMULTANEOUSLY partial and extra-keyed and never isolates the direction its name claims. The registry
  row promises set equality in BOTH directions and no test held the code to half of it. Same class as
  every could-not-fail defect this project has hit: a fixture where two faults coincide.
CONTROLLER RULING: absorb WRONG-TYPED `ratio`/`stratify_by` values under E-DATA-ASSIGN-NO-DRAW. Under
  by_attribute, `stratify_by: site` (a bare string, a routine YAML slip) and `ratio: 3` reported NOTHING
  — the row said they were "left to whatever else might catch it" and the reviewer established nothing
  does: envelope types only the assign block itself, task 4's closure checks key NAMES not types, and
  assign.<axis>.stratify_by is read nowhere else. Three in-file precedents absorb the wrong-typed case
  for exactly this reason. § Allocation says "rejects a non-empty one" and a bare string is non-empty.
Routed to task 10: `ratio` VALUES are unchecked (`{control: 0, treatment: 1}` passes). Not a divergence —
  nothing promises otherwise — but *Block size fills the arms* sums those values.
Task 5: COMPLETE. Commits e54736f, 50b6f61. 1519 passed + 2 xfailed. The surviving mutation now dies; wrong-typed values absorbed under E-DATA-ASSIGN-NO-DRAW.
Task 6: COMPLETE, NO FINDINGS. Commit 6718f4c. 1523 passed + 2 xfailed. `units.assign_seed_for(block,
  axis, digest, roster) -> int`, in units.py because it hashes what that module already builds
  (units_hash) and only CONSUMES design_digest — putting it in hashes.py would invert that module's
  dependency direction.
  The reviewer proved the pinned path never touches the digest BY CONSTRUCTION rather than by reading:
  it passed a PoisonDigest whose __str__ and __format__ raise, and got 42 back cleanly over two
  different rosters. It also isolated the reorder control by patching units_hash to sort before hashing
  and confirming the roster test fails at the reorder assertion specifically — so that half is
  load-bearing rather than decorative. Bools correctly fall through to the derived path, matching
  sample_seed_for's guard verbatim. Returns [0, 2^32) via sha256 digest bytes, deterministic across
  platforms unlike builtin hash().

Task 7: commits 60c65d4, 2542b7f; fix round in flight. 1530 passed + 2 xfailed. Spec ✅, quality high.
  THE SEAM: units.ArmPlan (frozen; levels, members, seed, strata) and units.assignment_for(...) as the
  ONE producer, pure and callable from validate and cli.command_run alike. by_attribute → arms_of
  unchanged; random/blocked → NotImplementedError until tasks 8 and 10, an explicit hole rather than a
  silent fallback to reading a column that need not exist.
  DECISION: COMPUTE ONCE AND PASS. One plan per axis realized in _resolved_group_axes; the same objects
  narrow the runner and are recorded in allocation.json. allocation.json is byte-identical, so the two
  pinned allocation_hash digests are unchanged — empirical proof the output did not move.
  IMPLEMENTER DEVIATION UPHELD: it dropped `roster` from arm_members and build_allocation_document
  entirely, beyond the brief's letter. Right, and better: with no roster in scope a second producer is
  not EXPRESSIBLE in either consumer without a signature change a reviewer would see. Structural rather
  than conventional.
  IMPLEMENTER'S VACUITY ARGUMENT UPHELD, AND MEASURED: the brief's literal mutation (a fresh-but-equal
  plan via dataclasses.replace) leaves 377 tests passing — genuinely vacuous, because an equal copy is
  by construction indistinguishable and the only way to make an UNEQUAL one is to recompute, which the
  call-count mutation catches. Its substitute (perturb the plan given to only one consumer) fails two
  tests and is the mutation that actually pins the property.
  The NotImplementedError hazard the implementer flagged is now PROVABLY unreachable rather than
  unlikely: validate never calls assignment_for, command_run gates on has_errors with no try/except
  between there and the call site, and _check_assign's block loop sits OUTSIDE the allocation gate, so
  any dict block naming random/blocked draws E-DATA-ASSIGN-DRAWN regardless of allocation, sweep.groups
  or roster resolution.
CONTROLLER RULING: make the method guard FAIL-CLOSED and single-sourced. Two sources of truth existed
  (validate.DRAWN_ASSIGN_METHODS and a literal inside assignment_for), pinned in agreement by nothing,
  and assignment_for was a DENYLIST — so a fourth method added to validate's enum alone would pass
  validation and then SILENTLY PARTITION ON A COLUMN, precisely the fallback the guard exists to
  prevent. The tuple moves to units.py (the dependency edge already runs that way, and validate's use is
  temporary while the draw's is permanent) and the dispatch inverts to an allowlist.
Routed to tasks 12/13: validate._check_assign still calls arms_of directly; when it starts resolving
  plans it must call assignment_for or the second producer reappears. Carry with it a latent asymmetry —
  _declared_levels returns the FIRST sweep.groups entry matching `by`, _resolved_group_axes keeps the
  LAST. Unreachable today (E-SWEEP-PATH-DUPLICATE), but it is the second place a level list could differ.
Routed to the draw tasks: build_allocation_document iterates plan.members, not plan.levels, so nothing
  checks realized membership covers the declared levels. arms_of guarantees it under by_attribute; a
  draw will not get it free.
Task 7: COMPLETE. Commits 60c65d4, 2542b7f, fce663b. 1531 passed + 2 xfailed. The guard is now
  single-sourced (DRAWN_ASSIGN_METHODS lives in units.py, validate imports it, and the drawn-method test
  is parametrized over the constant itself so the two sides cannot drift) and FAIL-CLOSED (allowlist:
  by_attribute/absent/non-mapping/method-less read a column, EVERYTHING ELSE RAISES).
  The old docstring had EXPLICITLY PROMISED "any other `method` string takes the by_attribute path" —
  the fail-open defect written down as if intended. Mutation: adding "adaptive" to ASSIGN_METHODS with
  the denylist restored made the fourth method silently partition on a column (DID NOT RAISE); with the
  allowlist and the extended enum still in place it raises.

Task 8: commit 067d046, fix round in flight on TWO CRITICALS. 1534 passed + 2 xfailed.
  First task that actually draws. The draw itself is correct: the reviewer verified the partition
  property over ~200 (n, ratio) configurations, and confirmed seeding is sound — local random.Random,
  no module global, identical across processes and under PYTHONHASHSEED 0/1/42/77/12345.
Task 8 Critical 1: THE DRAW CAN PRODUCE AN EMPTY ARM, and the citation used to justify it says the
  opposite. n=10 at {a: 1, b: 1000} gives {'a': 0, 'b': 10}. reference.md § Allocation says "An arm no
  unit resolves to is already refused, as E-DATA-ASSIGN-LEVELS" — in the sentence whose job is to
  CONTRAST that already-refused case with min_units_per_cell's thin-but-nonzero gap — and arms_of
  enforces it. The implementer routed a HARD REFUSAL into a gap about THIN cells that proposes a
  WARNING. CONTROLLER RULING: raise on a zero-size level in the drawn path, mirroring arms_of. A drawn
  empty arm is the same fault as a read empty arm.
Task 8 Critical 2: A MUTATION SURVIVED ALL 1534 — THE SECOND TIME IN THIS SLICE. Replacing
  largest-remainder-with-declared-order-tie-break by "remainder to the last entries in reverse order"
  leaves the suite green, because the 13-unit fixture agrees with the mutant BY COINCIDENCE (b is last).
  Everything _apportion's docstring argues — Hamilton, largest fractional part, ties by declared order —
  was unenforced. Both survivals in this slice had the same cause: a fixture whose numbers agree with
  the bug by accident.
CONTROLLER RULING: implement the stratify_by refusal in task 8, not task 14. assignment_for already
  raises for `clusters is not None` four lines above with exactly the "do not silently ignore a declared
  field" argument; a non-empty stratify_by under random is the same shape in the same function. A defer
  makes correctness depend on a future task remembering.
CONTROLLER RULING: close the whole `ratio` VALUE family under the existing E-DATA-ASSIGN-RATIO rather
  than minting. The worst member was missing from the implementer's report: `ratio: 3` under `random`
  VALIDATES CLEAN AND SILENTLY DRAWS EQUAL ALLOCATION, because both validate and units gate on
  `isinstance(ratio, dict) and ratio` so a scalar falls through to [1] * len(levels) with no exception.
  Siblings: {a: 0, b: 0} → ZeroDivisionError, {a: -1, b: 2} → silently a: 0.
Task 8: COMPLETE. Commits 067d046 (draw), 228e2d6 (controller's WIP commit on a dead agent's behalf —
  implementation only, no tests), 1a951d9 (fresh implementer: both Criticals + all Importants).
  1549 passed + 2 xfailed. AN AGENT DIED MID-FIX from an API 522. Recovery: the tree was green and the
  partial work coherent, so I committed it with an honest WIP message saying tests were owed, and
  dispatched a FRESH implementer for the remainder rather than losing or silently keeping it.
  Critical 1 closed by REUSING E-DATA-ASSIGN-LEVELS rather than minting — same fault and same words as
  arms_of, and § Allocation's "an arm no unit resolves to is already refused" is method-agnostic, so
  reuse leaves both documents true with ZERO doc edits. Verified independently: {a:1,b:1000} over 10
  units raises, {a:1,b:1} draws 5/5.
  Critical 2 closed with _apportion(10,[1,1,1]) == [4,3,3] and (10,[3,3,1]) == [4,4,2] — the second
  putting the largest fraction on the SMALLEST weight, which kills every weight-magnitude heuristic.
  (10,[1,2,4]) deliberately excluded because it coincides with the reverse-order mutant. Verified both.
  THE FRESH IMPLEMENTER FOUND A BUG THE WIP SHIPPED, by mutation: `.inf` passed the positivity check
  (inf > 0 is True) and made 10*inf/inf a nan, so int(nan) blew up. Found because deleting isfinite
  initially SURVIVED — the mutation caught a real hole rather than confirming a known one. 8 mutations
  in all, every one killed.
Routed to task 14: when E-DATA-ASSIGN-DRAWN retires, {a:1,b:1000} over a 10-unit roster VALIDATES CLEAN
  and raises at the draw — a validate-clean-then-disagree gap. The closing check is roster-dependent, so
  it belongs beside E-DATA-ASSIGN-LEVELS's roster-resolved check, not in the declaration-only ratio family.
Routed (pre-existing, do not fix casually): arms_of's run-time E-DATA-ASSIGN-LEVELS is absent from
  § Errors core raises, and that section's closing paragraph locates a row BY POSITION ("That last row"),
  so inserting one breaks it. The defect class again, sitting in the fix for the defect class.

Task 9: commit d21a118, fix round in flight. 1552 passed + 2 xfailed. Spec ✅, quality high.
  A `random` draw keeps whole clusters on one side, via a SIBLING of _assign_whole_clusters rather than
  a parameterization. The reviewer confirmed that function is BYTE-IDENTICAL across the commit, so the
  fold bit-stability oracle could not have moved — and probed whole-cluster integrity over 300 rosters
  (276 draws, 24 correctly-refused empty arms) with no cluster straddling two arms and no unit lost.
  The clustered path CAN produce an empty arm more easily than the unclustered one, because a cluster is
  a coarser unit of movement, and it refuses with the same E-DATA-ASSIGN-LEVELS and the same wording.
MY FIXTURE RATIONALE WAS FALSE AND THE IMPLEMENTER CAUGHT IT. I wrote that 4/3/2/2/1 was chosen so "no
  subset sums to exactly half"; it has FOUR such subsets — (4,2) twice and (3,2,1) twice. It corrected
  the docstring to the property that actually discriminates rather than keeping my words. Verified.
Task 9 fix round: THREE OVERREACHING DOCSTRINGS, the class this project hits most — and one of them
  commits the fault while describing the fix for another.
  (a) _assign_whole_clusters_by_ratio divides counts[i]/weights[i] unguarded, so ratio 0 crashes with a
      raw ZeroDivisionError, while its docstring claims it follows _apportion's total-and-defer
      convention. _apportion divides by SUM(weights) and never an individual weight. Ruling: GUARD IT so
      the claim becomes true, rather than narrowing the claim — total-and-defer is the right convention.
  (b) the fixture helper claims a split-cluster mutation "lands on a size combination this pair does not
      otherwise produce"; it lands on 6/6, EXACTLY what a legitimate whole-cluster draw produces. The
      neighbouring docstring says the opposite, correctly, which is why its assertions are structural.
  (c) the deviation bound was false in the undershoot direction: three equal levels over clusters
      {7,1,1,1} put a bucket at size 1, deviation 2.33 from target 3.33, while its only assigned cluster
      is size 1. The bound is the largest cluster in the ROSTER, not the largest assigned to that bucket.
Task 9: COMPLETE. Commits d21a118, b158145. 1553 passed + 2 xfailed. All three overreaching docstrings fixed; the zero-weight guard makes the starved level a size-0 bucket refused by the existing E-DATA-ASSIGN-LEVELS path rather than crashing, and the deviation bound now cites reference.md's existing non-promise for folds rather than an unproven tighter one.

Task 10: commit 0aef863, fix round in flight. 1563 passed + 2 xfailed. `blocked`, block_size: auto, the
  whole-multiple rule, and E-DATA-ASSIGN-BLOCK-SIZE (minted by the implementer, name/sort/rows verified).
TWO BRIEF DEFECTS, BOTH MINE, BOTH UPHELD — and one is worse than the implementer said:
  (a) "random does not read order" was my control's whole premise. At a pinned seed, random and blocked
      are BOTH pure functions of position → arm: 200 permutations leave the arm-by-position vector
      bit-identical for both, and both are invariant under exactly 42 of the 91 pairwise swaps. They are
      EQUALLY order-sensitive mechanically; only the map differs. So the order test does not test its
      named property — it passes for any two distinct maps. The real demonstration is the per-block
      balance test: local balance in every consecutive window is the property only blocked has.
      reference.md is NOT defective — it is true in the design sense and its next sentence concedes
      general order-sensitivity. The false mechanism claim was mine alone.
  (b) "appending re-blocks, boundaries move relative to every earlier unit" is imprecise for an append:
      verified over five appends at a pinned seed, only the trailing-partial-block unit ever changes,
      because every whole block shuffles a label list of identical length so the RNG stream is
      bit-identical through it. My phrasing is true for insertion IN THE MIDDLE.
Task 10: FOURTH AND FIFTH SURVIVING MUTATIONS OF THE PROJECT. (i) Replacing the block_size resolution
  with `2 * ratio_sum` — ignoring an explicit block_size entirely and always drawing at auto — passes
  ALL 1563 tests. The validate tests cover the REFUSAL of bad explicit values; nothing covered the draw
  HONOURING a good one, and that is the task's headline parameter. (ii) Inserting a PER-BLOCK empty-level
  refusal passes all 665 units/validate tests, while the docstring commits explicitly to the opposite —
  the 14-unit two-level equal-ratio fixture can never reach the whole-roster check.
CONTROLLER RULING: tighten the whole-multiple rule to PER-LEVEL shares. ratio {a: 0.5, b: 0.5} with
  block_size 1 passes validate (1 is a whole multiple of 1.0), then every block apportions [1, 0] and the
  run dies at E-DATA-ASSIGN-LEVELS — a wrong-fault code, and the validate-clean-then-fail class this
  slice keeps closing. § Allocation's purpose clause is "so every block fills each arm exactly", and the
  rule that delivers it is each level's per-block share being whole, not the sum being divisible.
Task 10: COMPLETE. Commits 0aef863, 7bb0e7d, 6e2fe28 (controller's docstring fix). 1571 passed.
  Both surviving mutations now die to their own named tests, verified independently. The whole-multiple
  rule is per-level shares; integer ratios that used to pass still pass ({1,1}/4, {1,2}/6, {}/auto all
  accepted end to end through write_config → validate), and {a:0.5,b:0.5}/block_size 1 is now refused AT
  VALIDATE rather than dying at the draw with a wrong-fault code. CLI seam restored.
  The controller fixed two docstrings the fix's own later passes had falsified — one still said `auto`
  "is not checked against the whole-multiple rule at all" (a claim that commit's third pass reversed),
  the other credited the 2 × ratio_sum formula to assign_seed_for, the SEED function, rather than
  auto_block_size. Stale rationale inside the fix for stale rationale.
Task 11: COMPLETE. Commit 98fe62d. 1574 passed + 2 xfailed. Controller-probed: blocked+cluster_by draws E-DATA-ASSIGN-BLOCKED-CLUSTER, random+cluster_by stays legal, blocked-without-cluster_by stays legal. Both owed rows landed; the two forward references from tasks 2-3 needed no edit. validate refuses before run, matching the NotImplementedError units.assignment_for already raises for the same case — no gap between layers.

Task 12: commits ef46038, 986370f; fix round in flight. 1594 passed + 2 xfailed. Spec ✅.
  Stratified drawing under BOTH random and blocked. The implementer found blocked had the same
  validate-clean-then-crash shape task 8 had left for random — both § Validation's row and the
  STRATIFY-UNKNOWN row gate on "random or blocked", so a well-formed stratum under blocked validated
  clean and then crashed. Minted E-DATA-ASSIGN-STRATIFY-VARIES for the constancy refusal, which
  genuinely had no code. validate now calls assignment_for rather than arms_of — one producer — and the
  reviewer verified the digest it passes is PROVABLY UNREAD on that path.
  The reviewer confirmed unstratified and clustered-unstratified draws are BYTE-IDENTICAL to the
  pre-change implementation across methods × n ∈ {7,12,20,31} × seeds × ratios.
Task 12: THE SIXTH SURVIVING MUTATION, AND THE BEST DIAGNOSIS YET. Deleting the stratified shuffle, and
  replacing Random(seed) with Random(0), each leave all 1594 tests passing. The reason generalizes past
  "the fixture doesn't discriminate": PER-STRATUM ARM COUNTS ARE FORCED BY _apportion, SO NO COUNT
  ASSERTION CAN EVER DETECT AN RNG MUTATION IN THE STRATIFIED PATH. Every stratified test asserts counts
  only; the clustered one asserts cluster-wholeness and per-site counts, both structurally forced. The
  implementer's ten mutations sampled the structural class exclusively and could not have found it.
  Control proving it is specific to the new branch: deleting rng.shuffle(block_labels) in _blocked_draw
  fails six tests. Fix: pin members at a seed and assert a different seed differs, both paths.
  The second mutation is the worse one — the seed is ignored while ArmPlan.seed still RECORDS it, a
  false record of the draw, which is the exact fault ArmPlan's own docstring argues against for strata.
Task 12: seventh positional-phrase instance in the project, in a row this task wrote ("one row up" where
  it is two, with E-DATA-ASSIGN-RATIO between).
Task 12: COMPLETE. Commits ef46038, 986370f, a600358. 1594 passed + 2 xfailed. Both RNG mutations now die to a membership pin at seed 11 vs 12, covering the clustered path too since it draws from the same generator.

Task 13: commits d4aa70a, 28f011e; fix round in flight. 1602 passed + 2 xfailed. Spec ✅.
  Forward-only stratification. THE DRAW ORDER IS NOW A CONTRACT, and exactly one thing pins it — THE
  RAISE: each axis is drawn against a snapshot of the plans drawn BEFORE it, so an axis whose stratum is
  not in that snapshot cannot be drawn at all. Verified: reversing the loop fails the contract test.
  What does NOT pin it, and no test claims it does: assign_seed_for keys on the axis NAME, not position,
  so two non-stratifying axes draw BIT-IDENTICAL plans in either order — reordering is observable only
  through a stratifying axis.
  The implementer hit the same `git checkout` trap task 4 did and reconstructed; the reviewer proved the
  reconstruction complete a stronger way than claimed — pre-change vs HEAD assignment_for output is
  BYTE-IDENTICAL across n × method × seed × ratio × strata × clustered, 66 KB of pinned JSON, cmp-clean.
Task 13: SEVENTH AND EIGHTH SURVIVING MUTATIONS.
  (7) `blocked`'s forward-only stratification is threaded but NEVER EXERCISED — reverting only that
      branch's two call sites leaves all 1602 passing. The reason generalizes: the parametrized test
      loops ("random","blocked") but asserts a RAISE for both, so it passes whether or not blocked can
      read a plan at all. A PARAMETRIZED TEST THAT ASSERTS A FAILURE FOR BOTH ARMS PROVES NOTHING ABOUT
      EITHER ARM'S SUCCESS PATH. Every successful axis-name draw in the suite is `random`. The worse of
      the two call sites is inside the E-DATA-ASSIGN-LEVELS message construction, so the mutation makes
      the diagnostic path raise while FORMATTING AN ERROR.
  (8) the `axis not in axes` guard is untested and removing it crashes validate: assign.ghost.stratify_by
      with ghost not a groups axis raises an uncaught ValueError OUT OF VALIDATE — a traceback where a
      diagnostic belongs, in a module contracted never to raise. Documented in the registry row and an
      eight-line comment; unasserted.
Task 13 finding, MEASURED not argued, routed to task 14's addendum by the controller: an axis-name
  stratum never reaches E-DATA-ASSIGN-STRATIFY-VARIES, whose loop appends only declared-ATTRIBUTE strata.
  So with cluster_by declared, an earlier by_attribute axis whose `from` VARIES WITHIN A CLUSTER splits
  that cluster between its own arms, the halves land in different strata, and A CLUSTER STRADDLES BOTH
  ARMS — 30 of 30 seeds on the reviewer's fixture, 17 of 30 on the implementer's. Contradicts
  § Clustered units' "core keeps it indivisible". Needs `from` ≠ axis name, and is unreachable while
  E-DATA-ASSIGN-DRAWN stands — which is exactly what task 14 removes.
CONTROLLER RULING: do NOT record it in spec-defects.md (gitignored, does not survive the merge). Task 14
  decides: extend the constancy check to axis-name strata, or record it in reference.md beside
  § Clustered units' indivisibility claim, where a reader meets it at the promise.
Task 13: COMPLETE. Commits d4aa70a, 28f011e, e9e7746. 1605 passed + 2 xfailed. Both surviving mutations now die, and the two blocked tests ISOLATE the two call sites — reverting only the message-construction site fails the second alone.
Task 14: COMPLETE. Commits d2799d5, c3e61cc. 1614 passed + 2 xfailed. E-DATA-ASSIGN-DRAWN is retired
  across all twelve doc sites and six source/test files; DRAWN_ASSIGN_METHODS and its elif SURVIVE as
  the drawn/read dispatch (the brief's "remove the elif" predates tasks 8-13 filling that branch).
  Step 1 needed NO code change — build_allocation_document already emitted per-axis seed/strata — so
  the mixed-document test was mutation-tested in both directions to give it teeth.
BOTH routed defects CLOSED, each by broadening an existing code rather than minting one:
  (1) ratio-starves-an-arm -> new § Validation row *Every arm draws units*, E-DATA-ASSIGN-LEVELS,
      realized by calling assignment_for and discarding the plan. GATED to the unstratified,
      unclustered draw (validate has no digest; the clustered draw's empty arm is seed-dependent),
      and the residue is written into the registry row AND into § Errors core raises, which had no
      run-time E-DATA-ASSIGN-LEVELS row at all. "That last row" rewritten to name the row by code.
  (2) cluster straddle -> E-DATA-ASSIGN-STRATIFY-VARIES broadened to read an axis-name stratum
      through the column its axis reads (_read_axis_column). Zero draws. NOT spec-defects.md.
MUTATION THAT SURVIVED (sixth dimension-blindness of the project): the "an earlier axis that DRAWS
  needs no check" control passed with the method guard deleted, because its fixture declared no
  `from` — so the mutated helper defaulted to the axis name, found no attribute, and returned None
  anyway. THE TEST WAS PROVING THE ABSENCE OF A COLUMN, NOT THE METHOD. Fixed by declaring a `from`
  the drawn method ignores. Ask what your control is actually holding fixed.
STILL OPEN, deliberately: a clustered or axis-stratified draw that starves an arm validates clean and
  raises at the draw (documented in the row, pinned by a test); `resume` still does not exist and its
  "read rather than re-drawn" rule stopped being harmless the moment arms are drawn.

Task 14: commits d2799d5, c3e61cc, 9579dba; fix round in flight. 1615 passed + 2 xfailed. Spec ✅.
  E-DATA-ASSIGN-DRAWN RETIRED across all twelve doc sites and every source/test surface. DRAWN_ASSIGN_
  METHODS and its elif SURVIVE — the brief's "remove the elif" predates tasks 8-13 filling that branch;
  only the c.error went, and the tuple's reason is now DISPATCH rather than refusal. Step 1 needed no
  code change: build_allocation_document already emitted per-axis seed/strata, so the deliverable was the
  docstring, a mixed-document test mutated in BOTH directions (since no code moved, that is what gives it
  teeth), and an end-to-end run test proving a random config reaches a run directory at all.
  BOTH ROUTED DEFECTS CLOSED, each by broadening an existing code rather than minting: the starving ratio
  as a new § Validation row *Every arm draws units*, realized by calling assignment_for and DISCARDING
  the plan (so no second producer); the cluster straddle by extending E-DATA-ASSIGN-STRATIFY-VARIES to
  read an axis-name stratum through the column its axis reads, with zero draws.
  The reviewer probed SEVEN shapes end to end. The two that matter — a clustered draw and an
  attribute-stratified draw that starve an arm — produce a DIAGNOSTIC and EXIT_WRONG with no run
  directory, not a traceback.
Task 14 fix round: (1) the documented residue is THREE classes stated as TWO — an attribute-stratified
  starving draw also validates clean and raises at the draw, and it is refused at ALL 50 SEEDS, i.e.
  SEED-INDEPENDENT, so the gate's own stated justification ("only where realized sizes do not depend on
  the seed") does not cover its own exclusion. Two normative sentences under-count by one class.
  (2) NINTH SURVIVING MUTATION: `if drawn_levels is not None:` → `if True:` survives all 963 tests of the
  four relevant files, and the mutant crashes INSIDE VALIDATE with a TypeError on an empty `levels` — a
  traceback in a module contracted never to raise.
MY ADDENDUM WAS WRONG AGAIN: I claimed "two allocation_hash digests pinned as literals". There are none —
  no 64-hex literal exists in tests/ or docs/, and both tests recompute. The invariant that mattered
  (a by_attribute-only document is unmoved) does hold and is pinned by a different test.

Task 14: COMPLETE. Commits d2799d5, c3e61cc, 9579dba, 5c97686. 1616 passed. The residue is now stated as
  THREE draws excluded for TWO different reasons (the digest covers only the clustered case; both
  stratified kinds are excluded for reasons of their own), corrected at five sites. The optional
  widening was DECLINED with a reason worth keeping: admitting attribute strata means either swallowing
  a NotImplementedError or COPYING _stratum_groups' precedence rule into validate — a second copy of the
  rule the single-producer seam exists to prevent.
WHOLE-BRANCH REVIEW: MERGE, no Criticals. Verified independently: assignment_for is still the single
  authority (arms_of has exactly one caller in the whole tree, inside it); drawn allocations are
  reproducible across processes and PYTHONHASHSEED over 8 shapes × 3 seed settings, and every shape
  produces different membership per seed, so no path records a seed it ignores; the eleven codes agree
  in both directions; and the acceptance property survived 19 varied-ROSTER probes (attribute missing,
  a stratum of one, a cluster 11/12 of the roster, levels outnumbering units, a forward plan built from
  a different roster).
  TENTH SURVIVING MUTATION, found by the whole-branch review: passing `clusters=None` into
  _resolved_group_axes left all 1616 passing, while the real path keeps clusters whole and the mutant
  SPLITS ALL FOUR across both arms. That argument is the load-bearing wiring for two normative claims,
  and the only end-to-end groups × cluster_by test used by_attribute, where clusters is unread.
  Controller verified the fix: the mutation now fails exactly the new test and reverts clean.
  Also closed: two stale claims the retirement falsified (a gate justification asserting the refusal
  this branch retired, and a docstring citing the § Validation row the retirement deleted), and
  E-DATA-ASSIGN-SEED minted for a wrongly-typed pin — "1234", 1.5 and true each silently fell through to
  the auto derivation, so allocation.json recorded a DERIVED seed as if it were the pin, with no backstop
  anywhere and the sibling field (sweep.sample.seed) refused.
ALL 14 TASKS COMPLETE. 1632 passed + 2 xfailed, ruff and mypy clean. 33 commits over 39c6667.

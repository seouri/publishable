# SDD ledger — plan: docs/superpowers/plans/2026-08-12-sweep-expansion-modes.md

Branch: h2-sweeps (from main @ ad6cf3d). Suite baseline: 955 passing.
9 tasks. groups STAYS REFUSED — E-SWEEP-GROUPS-UNSUPPORTED must still fire at the end.
Task 1: complete (commits ad6cf3d..ddeee8f, review clean). 956 tests. expand() is now a two-phase
  product: _axes builds one entry per axis-shaped mode, expand takes the product. label_for lost
  its `grid` param for a `swept` path list (one caller, contained). No existing test edited.
  Reviewer compared expand() output between main and HEAD in a throwaway worktree: byte-identical
  for grid ordering, the baseline-coincides-with-a-grid-cell no-dedup case, and the no-sweep case.
Task 2: commit 268f37c (960 tests). paired added as ONE axis; E-SWEEP-PAIRED-UNSUPPORTED retired;
  NOT BUILT marker removed and the count corrected Fourteen -> Thirteen (reviewer counted the 13
  remaining markers independently).
Task 2: implementer caught a regression its own change caused — paired becoming a real axis
  reopened E-SWEEP-BASELINE-PARTIAL's declared-vs-executed hole, which was grid-only. Reviewer
  confirmed the regression is real, the widening correct, and deferring it to task 6/7 would have
  been WRONG (four tasks of silent divergence). The mis-scoped half was the DOC: reference.md's row
  still describes the pre-widening refusal.
Task 2: review spec ❌ — CRITICAL: `paired: ["notadict"]` validates clean and crashes run with a
  bare ValueError, reopening for paired the exact hole ad6cf3d closed for grid/baseline one commit
  earlier. _check_shape guards grid and baseline and stops there, because paired was refused when
  it was written; _axes now reads it unconditionally.
Task 2: IMPORTANT — grid and paired naming the same path produce byte-identical duplicate
  conditions, silently. _swept_paths dedups, _axes does not. validate reports nothing; the run
  executes a condition twice and the correction family counts double. _condition_labels returns a
  SET, so duplicate labels are structurally invisible to every check built on it. Underspecified in
  § Expansion modes -> spec-defects entry AND a refusal.
Task 2: fix round 1 (commit 54cdac7, 966 tests) — shape guard for paired, E-SWEEP-PATH-DUPLICATE
  minted with its row, the E-SWEEP-BASELINE-PARTIAL row widened, three Minors closed. Re-reviewer
  verified the duplicate refusal's row is a STRUCTURAL fact (grid axes always precede the paired
  axis in _axes, so paired's cell always wins a shared path) and that it stays silent for the two
  normal cases.
Task 2: fix round 2 dispatched — the guard closed the reported INPUT, not the CLASS. A paired entry
  with a non-string key ({123: 30}) is a well-formed dict, passes isinstance(entry, dict), validates
  clean, and raises AttributeError from _keys_for's path.split(". "). Same validated-clean-crashes-run
  failure via a different shape. Pointed at H1's envelope.py precedent, which resolved the same
  question the OTHER way (str()-coerce and report rather than skip) so the choice is deliberate.
Task 2: fix round 2 (commit 1c5ed66, 968 tests) — non-string paired keys refused as E-CONFIG-SHAPE
  (fatal), NOT envelope.py's coerce-and-report route. Reviewer upheld the choice with the better
  argument: envelope.py coerces because its keys sit under a CLOSED vocabulary a coerced string can
  be compared against, and its check is non-fatal by design; _check_shape's is a shape guard and
  fatal like every other guard there. Same rule, two different questions.
  Reviewer enumerated every operation on paired-derived data across five functions and confirmed
  isinstance(key, str) is an exhaustive gate. Class CLOSED for paired.
Task 2: fix round 3 dispatched — two residuals the enumeration surfaced:
  (a) the IDENTICAL crash is live via sweep.grid (a non-string grid key raises AttributeError from
      _keys_for). Pre-existing, but closed-for-paired/open-for-grid is the worst of the two states.
  (b) the paired value-checking gap lives ONLY in the gitignored task report, which is deleted at
      merge — the sibling E-SWEEP-PATH-DUPLICATE gap IS in spec-defects.md. Same lost-finding
      failure H1 had to correct once already.
Task 2: fix round 3/5 (2 addressed; commit 2d30836, 970 tests). sweep.grid's identical non-string-key
  crash closed with the same guard (reviewer confirmed no pre-existing guard, and that the two guards
  are one rule — the control-flow difference follows from nesting, not drift). The paired
  value-checking gap moved into spec-defects.md with three verified repros.
Task 2: complete (commits ddeee8f..2d30836, review clean). 970 tests, ruff and mypy green.
Task 2: FOR THE FINAL REVIEW — the paired value-checking gap names owner H2, which the reviewer
  judged "sound in principle but not actionable in plan": H2 is the right house, but H2's charter
  does not list per-entry paired checking and no task 3-9 claims it. The entry itself says it needs
  a future H2 task or a charter revision. Softer than the circular routing this project has hit,
  but worth triaging at the end rather than assuming a later task picks it up.
Task 3: commit 2e0e270 + follow-ups (1016 tests). `sample` added as ONE axis of n realized draws;
  E-SWEEP-SAMPLE-UNSUPPORTED retired; NOT BUILT marker removed and the count corrected Thirteen ->
  Twelve. All three methods implemented (scipy qmc Sobol/LatinHypercube, stdlib random). One code
  minted: E-SWEEP-SAMPLE-INVALID (registry row + a § Validation row "Sample is drawable"); every
  TYPE fault is E-CONFIG-SHAPE in _check_shape, fatal, matching grid/paired. sweep.yaml gains
  `sample_seed` (the values were already conditions[].values — no second copy).
Task 3: FOUR things later tasks need to know.
  (a) A PINNED INTEGER SEED IS LEGAL. § What `auto` derives from says "pinning an integer is the
      deliberate act" and names sweep.sample.seed explicitly. My first implementation refused
      anything but `auto` and contradicted the document. sample_seed_for returns a pinned int
      literally and does not compute the digest at all on that path.
  (b) E-SWEEP-PATH-DUPLICATE WIDENED to all three axis-shaped modes (was grid ∩ paired). Leaving it
      would have reopened task 2's fix through a third route, and worse: sweep.yaml records the
      DRAWN value as the condition's while the run used the grid cell's. Registry row follows.
  (c) A REAL CODE BUG FOUND AND FIXED, live on main for `paired` since task 2: command_run built
      the run/summary-scope unreadable-path set from `grid | baseline` only, so a paired or sampled
      path stayed READABLE at those scopes and resolved to the base config's value. Now
      `_swept_paths(sweep) | baseline`. spec-defects entry + end-to-end test.
  (d) baseline + sample now hits E-SWEEP-BASELINE-PARTIAL unless the baseline pins every sampled
      path (sample paths joined _swept_paths). Same widening task 2 made for paired, retires with
      TASK D's per-cell expansion. Test added so task D sees it named.
Task 3: digest-constancy question (the brief's note) — VERDICT: intended, no spec-defect entry.
  Measured on main: two unrelated configs with no data.units/sweep.groups already resolve the SAME
  repeat seeds ([1862657564, 169278302, 780543318] both), so `sample` inherits a documented
  property (§ What `auto` derives from) rather than introducing one. The documented lever for a
  distinct draw is pinning an integer, which (a) implements.
Task 3: NEW SPEC-DEFECT — § Expansion modes says the sample seed is "derived from the design
  digest"; § What `auto` derives from's table says the draws mix "digest + n, method, ranges". I
  implemented the first (per the brief). They differ on ONE observable: under random/sobol, raising
  n EXTENDS the condition list rather than redrawing it — which the same table explicitly prefers
  one row up for a seed level. Recorded, not silently resolved.
Task 3: sobol n — drawn EXACTLY at a non-power-of-two n, scipy's UserWarning suppressed around that
  one call. n is the condition count: billed against limits.max_executions, printed by dry-run,
  recorded as the design. Rounding would execute a different experiment than the one declared.
Task 3: mutation pass caught two silent-no-op gaps the first test set missed — qmc.Sobol(
  scramble=False) (the engine ignores its seed; the discriminating test is now parametrized over
  all three methods) and crossing the sample axis per path instead of composing it as one cell
  (n**d conditions; the multiplication test now declares two sampled paths). 8 of 10 mutants died
  on the first try.
Task 3: E-SWEEP-GROUPS-UNSUPPORTED confirmed still firing. § Validation's "not raised for a
  sample-only sweep, whose draws aren't a family" exception is now REACHABLE and verified: it holds
  structurally, since resolve_contrasts needs a DECLARED baseline and a sample-only sweep has none.
Task 3: commits 2e0e270, cabdc5a, 2907ebb (1016 tests, +46). sample implemented with all three
  methods via scipy.stats.qmc (lazy import, purity held); E-SWEEP-SAMPLE-UNSUPPORTED retired;
  E-SWEEP-SAMPLE-INVALID minted with a row.
Task 3: found and fixed a REAL BUG live on main that task 2 introduced — command_run built the
  run/summary-scope unreadable-path set from grid|baseline only, so a paired or sampled path
  silently resolved to the base config's value at those scopes. Reviewer confirmed the bug, the fix
  (_swept_paths|baseline) as exactly right rather than over-broad, and landing it here as correct.
Task 3: digest-constancy verdict REPRODUCED by the reviewer — same digest, same three repeat seeds,
  on untouched main. sample inherits a documented property; no defect entry owed.
Task 3: review spec ❌ — CRITICAL, and it is task 2's failure one level up. The SHAPE class is
  closed (24 adversarial inputs, all coded, none a bare exception). The VALUE class is not:
  _value_checks runs on the sample's BOUNDS only and never on the DRAWN values, so
  {analysis.min_samples: {uniform: [10, 200]}} against Param(int, ge=2) validates clean and runs at
  118.385. Reviewer's diagnosis: "the enumeration was over operations on the declaration, not over
  what the declaration produces."
Task 3: IMPORTANT — E-SWEEP-SAMPLE-INVALID's registry row still lists "a seed other than auto" as a
  cause while the code deliberately accepts a pinned integer. Three other places were widened; this
  row was not.
Task 3: review round 1 (spec ❌ 1C/1I/2m) addressed — commits c7faf37, c48464a. 1019 tests.
  CRITICAL was the same failure one level up: the shape class was closed, the VALUE class was not.
  `sample` checked its BOUNDS only, so {uniform: [10, 200]} over Param(int) validated clean and drew
  118.385… into a step reading an int, and Param(int, choices=[10,50]) with int_uniform: [10,50]
  drew 37. Route chosen: check the REALIZED draws (validate._check_sampled_values, after expand,
  through the same Param.check/E-PARAM-VALUE grid values use) rather than refusing a non-int_uniform
  form on an int param — the form rule catches the type case and nothing else (not choices, pattern,
  ge/lt, or log_uniform under a gt=0), and the drawn value is what actually executes. First
  offending draw per path only. Mutation M11 kills it.
  LESSON FOR TASKS 4-9: an enumeration over operations on the DECLARATION is not an enumeration over
  what the declaration PRODUCES. ablate and per-cell baselines both produce values the same way.
  IMPORTANT: reference.md's E-SWEEP-SAMPLE-INVALID row still said "a seed other than auto" after the
  pinned-integer deviation — same drift class as the rows I did widen. Fixed, plus the drawn-value
  case added to the § Validation "Sample ranges" row.
  MINOR: the digest-TypeError conversion is defensive only — cli computes design_digest(doc) at
  phase 5 BEFORE expand, so a YAML date under data.units crashes `run` with a BARE TRACEBACK today,
  for ANY config, sample or not. Pre-existing, owned by H3 Units, now a spec-defects entry. Triage
  it at the end of the branch alongside the paired per-entry gap.
  MINOR: _check_shape's seed message said "expected a string" when an int is legal too.
  PROCEDURAL: I applied a mutant to an UNCOMMITTED fix and `git checkout --` reverted the fix with
  it. Commit before mutating.
Task 3: fix round 1/5 (4 addressed; commits c7faf37, c48464a; 1019 tests). Took the REALIZED-VALUE
  route over the declaration-form rule, correctly: the form rule catches the type case only, not
  choices/pattern/ge/lt or log_uniform dipping under gt=0. Checks every drawn value for every
  sampled path through the same Param.check/E-PARAM-VALUE grid uses, first offending draw per path.
  Reviewer confirmed method-independence empirically for random, sobol and latin_hypercube, and
  produced a closure table: every Param constraint is checked on the draw, structurally implied by
  the monotone bound check, or vacuous for range forms. Value class CLOSED.
Task 3: complete (commits 2d30836..c48464a, review clean). 1019 tests, ruff and mypy green.
Task 3: FOR H3 — a genuine PRE-EXISTING bug found: cli computes design_digest(doc) at phase 5
  BEFORE expand, so a bare YAML date under data.units crashes `run` with an uncaught TypeError for
  ANY config, sample or not. Filed in spec-defects.md as H3 Units' to own.
Task 3: minor (deferred): the composed message duplicates the value ("draws X, which is X, expected
  integer") since Param.check already opens with "is ...". Cosmetic.
Task 3: minor (deferred): with baseline+sample, an illegal BASELINE value is attributed to the
  sample range and the per-path break suppresses genuine drawn violations on that path. Wrong
  attribution on an already-refused config; refuses nothing new.
Task 3: PROCESS — the implementer applied a mutant to an UNCOMMITTED fix and `git checkout --`
  reverted the fix with it. Caught and restored; the Critical was committed before re-running.
  Mutate only against a committed tree.
Task 4: commits e2f85e7, 9e07dd4 (1042 tests). ablate applied after the product, not as an axis;
  E-SWEEP-ABLATE-UNSUPPORTED retired; ablated_paths() kept OUT of _swept_paths (which feeds
  E-SWEEP-BASELINE-PARTIAL's which-axis question, meaningless for a non-axis) and unioned in at the
  two sites needing the whole set. Reviewer verified there is no third such site.
Task 4: DISCLOSED WINDOW, judged right to ship — retiring the blanket refusal removed the only
  enforcement of two normative rules (ablate requires a baseline; ablate x a parameter mode is
  rejected). Both reproduced: no baseline -> 1 condition silently; ablate x grid -> 4 conditions.
  Task 5 owns rows 217/218. Keeping a narrowed unbuilt-block code alive would mint wrong semantics
  under the wrong identifier for task 5 to delete again.
Task 4: review spec ❌ — IMPORTANT: `remove` paths get no path-resolution check while `override`
  paths do. remove: [analysis.methdo] validates clean and plants null at an undeclared path.
  Introduced by this commit, no new identifier needed, two lines in the loop already written.
Task 4: IMPORTANT — the window had no MECHANICAL handle; both durable records are gitignored, and
  this slice already lost a finding that way (task 2's paired gap). Fix: two xfail(strict=True)
  tests in tracked tests/, so task 5's reviewer confirms closure by watching them flip green.
Task 4: FOR TASK 5 — the plan's gloss of row 216 ("paths the baseline fixes") differs from
  reference.md's actual row ("remove needs a boolean or nullable parameter — use override"). Task 4
  COUPLED them: ablation_changes picks false vs null from baseline.get(path), so a remove path the
  baseline does not fix silently takes the null reading. Task 5 must implement both readings.
Task 5 PREP — controller read the three rows directly; the plan's gloss is WRONG and reference.md
  leads. Verbatim:
   - Ablation targets: "`sweep.ablate.remove[0]` is `analysis.min_samples` (int); `remove` needs a
     boolean or nullable parameter — use `override`"  [a TYPE check against Param, NOT the plan's
     "paths the baseline fixes"]
   - Ablation needs a baseline: "`sweep.ablate` is declared but `sweep.baseline` is not — there is
     nothing to ablate from"
   - Ablation doesn't compose with a parameter axis: "cannot be combined with `grid`, `paired`, or
     `sample`", with `groups` the stated exception (moot — groups stays refused).
  Rows 219 (baseline isn't a group level) and 257 (axis names distinct) both need groups: stay H3.
  Note task 3 already widened the "Sample ranges" row to cover the drawn-value case.
Task 4: fix round 1/5 (4 addressed; commit b93a559; 1043 passed + 2 xfailed). remove paths now go
  through _path_resolves -> E-SWEEP-PATH-UNKNOWN at sweep.ablate.remove[i] (index included), the
  same path check override gets; what remove PRODUCES stays row 216's, correctly deferred.
Task 4: complete (commits c48464a..b93a559, review clean).
Task 4: THE XFAIL CAVEAT FOR TASK 5'S REVIEWER — the two handles assert only that SOME error is
  reported, because task 5 has not minted an identifier yet. The re-reviewer reproduced the
  strictness mutation (stub refusal -> XPASS(strict) FAIL; strict=False -> silent xpass) so the
  mechanism works. But there was a REAL near-miss: on the first draft of the composition test,
  E-SWEEP-BASELINE-PARTIAL fired for an UNRELATED reason and the loose assertion passed — caught
  only because strict xfail forced a human to look at the XPASS. So: FLIPPING GREEN IS NOT
  SUFFICIENT EVIDENCE OF CLOSURE. Task 5's reviewer must inspect WHICH code fired.
Task 5: commit e0ee322 (1054 passed, 0 xfailed — the window is CLOSED). Three identifiers minted
  with rows: E-SWEEP-ABLATE-TARGET (row 216, BOTH readings under one code), -BASELINE-MISSING
  (217), -CROSSED (218, refused against a shared AXIS_MODES rather than a hardcoded list).
Task 5: reviewer verified the window closed FOR THE RIGHT REASON — listed EVERY finding for both
  window configs, not just whether one existed: each reports exactly its own code and nothing else,
  and E-SWEEP-BASELINE-PARTIAL appears nowhere. The task-4 near-miss is genuinely closed.
Task 5: row-216 one-identifier decision upheld with a better discriminator than mine — not
  condition count but whether the READER CAN ACT: distinct messages, both branches disclosed in the
  row, mutations killing independently. Branch 2 catches what branch 1 provably cannot.
Task 5: review IMPORTANT — AXIS_MODES's future-proofing is CLAIMED IN COMMITTED PROSE AND NOT
  PROVIDED. Reviewer ran the experiment rather than reading the test: added a `ladder` axis mode to
  _axes and to `known`, left AXIS_MODES alone -> the pinning test PASSED and `ablate x ladder`
  validated with ZERO findings. Three committed claims overstate it (sweep.py docstring, validate.py
  comment, the registry row). Fix: pin against `known` (a real choke point — a new mode MUST be
  added there or E-SWEEP-KEY-UNKNOWN refuses every config using it), not against _axes.
Task 5: fix round 1/5 (3 addressed; commits 1cabc11, 00c53de, 94e50a3; 1055 passed, 0 xfailed).
  The pin went FURTHER than instructed and is better: SWEEP_MODES = AXIS_MODES + NON_AXIS_MODES,
  with E-SWEEP-KEY-UNKNOWN gating on SWEEP_MODES and the local `known` literal deleted — so
  classifying a new mode is the only way to make it usable at all. Re-reviewer reproduced the
  ladder experiment BOTH ways: _axes-only is now refused (was silent); AXIS_MODES-only is caught by
  -CROSSED when composed and by the pre-existing -EXPANDS-EMPTY backstop when bare.
  M11 residual (nothing pins THAT the check reads SWEEP_MODES) judged sufficient as a disclosure —
  no behavioural test can catch "rewritten to a different but currently-equivalent set".
  Also fixed unasked: E-SWEEP-KEY-UNKNOWN's message named five modes while the check accepted six.
Task 5: complete (commits b93a559..94e50a3, review clean). 1055 tests.
Task 6 PREP — controller VERIFIED (not assumed) that the worked example is out of reach: with
  baseline {analysis.method: pearson, analysis.min_samples: 30} and grid {analysis.method:
  [spearman, kendall]}, expand gives exactly 3 conditions as CLAUDE.md pins, and `unfixed` is
  EMPTY — so cohort-pilot sits in § Expansion modes' FIRST row and per-cell expansion cannot move
  its labels 00_baseline / 01_method=spearman / 02_method=kendall.
Task 6: commit 0857a37 (1061 passed). Per-cell baseline expansion works: a baseline fixing SOME
  axes gives one per cell of the unfixed ones, labelled <cell>__baseline matching the document's
  00_cohort=derivation__baseline shape; is_baseline true on EVERY baseline; the first row unchanged.
  condition_dir_name byte-identical. Controller verified both rows and the worked example (3
  conditions, labels unchanged). No tests failed because the refusal lives in validate while this
  change is in sweep.py — reviewer confirmed that reasoning by probe rather than assuming it.
Task 6: review — the two-row table is ✅ but § How artifacts are organized's INDEX ROW is violated
  and unrecorded: it says per-cell baselines "land at the head of each cell … rather than putting
  both baselines first", and the implementation emits them as a leading block. Not Critical (no
  config reaches it while E-SWEEP-BASELINE-PARTIAL gates every multi-baseline config — the reviewer
  verified that gate across six shapes), but it is the numbering TASK 8 builds on.
Task 6: TWO GENUINE DOCUMENT DEFECTS found by implementing the spec, both routed to a spec-defects
  entry rather than fixed:
   (a) The interleaved rule is ILL-DEFINED, not merely unimplemented — for grid x grid with the free
       axis not outermost, the free axis varies fastest so its rows are not contiguous and "head of
       each cell" has no referent. An argument the DOCUMENT should change.
   (b) § Expansion modes row 2's own example is CIRCULAR: "sex=f__arm=treatment compares against
       sex=f__arm=control" with "arm and sex left free" — if arm is free the baseline expands over
       it too, so the stated target does not exist. The RULE is unambiguous; the EXAMPLE is defective.
Task 6: minor (deferred) — a baseline fixing NO swept path duplicates the whole run (8 conditions
  for a 4-cell design); gated today. And the label body now mixes key=value with a bare `baseline`;
  nothing in src/ parses a label body (reviewer checked recursively), so a residual for a future parser.
Task 6: fix round 1/5 (no commit — docs/superpowers/ is gitignored; controller verified the entry
  directly). The entry quotes the Index row verbatim, proves the ill-definedness (with the free axis
  not outermost, sex=f lands at 02 and 04, interleaved, so "head of each cell" has no referent, and
  it names test_the_last_declared_axis_varies_fastest as the pin for why), explains the
  ablate x groups illustration is consistent ONLY because one axis makes cells contiguous, and owns
  it to the `groups` slice as a DOCUMENT decision.
  CONSTRAINT IT HANDS TASK 8: resolve a condition's baseline by MATCHING UNFIXED-AXIS VALUES, not by
  positional numbering — invariant under either resolution of the Index-row question.
Task 6: complete (commits 94e50a3..0857a37, review clean). 1061 tests.
Task 7: commit eba1804 (1062 tests). E-SWEEP-BASELINE-PARTIAL retired — the placeholder whose own
  message conceded the design was "specified but not implemented in this build". Error table 65->64.
  Three gated shapes routed, none refused; the reviewer ACCEPTED that argument in full, calling
  reason 1 decisive (refusing would be code diverging from reference.md in the very commit that
  stopped code diverging from it). Firing condition of W-SWEEP-BASELINE-CONFOUNDED untouched.
Task 7: review spec ❌, TWO CRITICALS.
  (1) The rewritten row/comment/MESSAGE all assert "every comparison then differs in exactly one
      place" — FALSE on the shape the row recommends: method=spearman__sex=m vs sex=f__baseline
      differs on both axes, confounded True. The document was changed to describe code that does not
      exist, which is the direction CLAUDE.md forbids — while §4 invoked "the document changes
      first" to justify not refusing three shapes. The comment also contradicts itself on one screen.
  (2) The task 6 -> task 8 window has NO TRACKED HANDLE. contrasts.py targets the FIRST baseline for
      every condition and admits the others as comparisons: 6 conditions / 2 baselines -> 5
      comparisons where the spec says 4, one member a baseline, one differing on nothing.
      family_shape counts len({m.where}), so family_size is 5 x metrics and EVERY interval is
      corrected against the wrong denominator with no diagnostic. Task 6 named this and named the
      blocker; task 7 removed the blocker. In the same commit it pinned all three shapes IT found
      with tracked tests, three times, and left this one to a gitignored note.
      Handle refined: xfail(strict=True) on `len(resolve_contrasts(...)) == 4` — pins the spec's own
      arithmetic, better than task 4's error-presence form because this defect is a wrong NUMBER.
Task 7: fix round 1/5 (commits b61c054, c208c58; 1062 passed + 2 xfailed). False clause corrected at
  all three layers; §4 and §7.6 corrections landed, with §4's substantive half moved into TRACKED
  code. Two xfail(strict=True) handles in tests/test_contrasts.py pin the spec's own arithmetic
  (len(resolve_contrasts(...)) == 4; no comparison subject is a baseline). Re-reviewer added
  `and not c.is_baseline` to contrasts.py itself and confirmed both flip to FAILED [XPASS(strict)].
Task 7: fix round 2 dispatched — one residual: the message's lead clause still promises "the design
  that avoids this is a baseline fixing only the axis you are measuring", and taking that advice
  does NOT remove the confounded: true verdict in this build. The caveat retracted the mechanism,
  not the outcome. Ruling: make the message FACT-ONLY — the project only puts build-state language
  in a message when the build gap IS the finding (fold.stratify_by, the resolver refusals, the
  -UNSUPPORTED family); no precedent for another subsystem's build state on a config-fault message.
Task 7: RULED — no temporary W- for the window. The two strict xfails plus task 8's imminence
  suffice; a new identifier would land on the enumerated warnings surface and be deleted next task.
*** MERGE GATE I OWN: this branch must NOT reach main while those two xfails are still xfailing.
    A main carrying task 7 without task 8 ships 5-comparison correction families with no diagnostic.
Task 7: fix round 2/5 (commit d53b702). The message is now BYTE-IDENTICAL to its pre-task-7 text
  (controller verified against eba1804^, not by eye), so task 7's net change to
  W-SWEEP-BASELINE-CONFOUNDED is the § Warnings row plus the emit-site comment. The comment records
  WHY the message carries no remedy — telling a reader to free an axis would promise an outcome this
  build does not deliver — and that re-adding it is task 8's once targeting makes it true.
  It also corrected the ledger's task-8 checklist, which had told task 8 to delete a caveat that no
  longer exists.
Task 7: complete (commits 0857a37..d53b702, review clean). 1062 passed + 2 xfailed.
Task 8: complete (commit 632018b, spec compliance ✅, quality approved with three Minor findings).
  1069 passed + 0 xfailed (was 1062 + 2 xfailed) — the merge gate this branch carried is lifted.
  Per-cell vs_baseline targeting: contrasts.baseline_for matches on the FREE axes, derived by
  _free_axis_paths from the paths the baseline rows themselves disagree on — not from
  set(sweep["baseline"]), which both xfail tests (calling resolve_contrasts({}, ...)) measurably
  reduce to 2 comparisons. So the targeting reads no condition index and is invariant under either
  resolution of the open § How artifacts are organized Index-row question.
  Reviewer probed 12 designs (one baseline; three free axes / 8 baselines / 16 comparisons; a
  repeated free level; two baselines coincidentally agreeing on a free axis; ragged paired key sets;
  an unhashable level; sample as the free axis; ablate beside a grid) — nothing mis-targeted, nothing
  raised. Structural argument: expand lays `fixed` over every cell last, so a fixed path is constant
  across baseline rows and can never enter `free`; free == [] iff all baseline rows are
  value-identical; two distinct cells must differ somewhere, and that path lands in `free`.
  Handles flipped for the right reason, verified by two mutations the reviewer applied itself:
  match on fixed axes instead of free -> 6 failed, count collapses to 2; against = baselines[0] ->
  the count test fails on the PAIRS assertion with len == 4 still satisfied. That second one is
  exactly the confound a previous window nearly flipped green on, and the strengthened assertion
  catches it.
Task 8: minor (deferred): no test pins a MOVED corrected bound. The report's "no bound moved" is
  arithmetically forced under Holm — removing the rank-1 member takes rank i to i-1 with m'=m-1, and
  ALPHA/((m-1)-(i-1)+1) == ALPHA/(m-i+1). Under `statistics.correction: bonferroni`, _level_for
  returns ALPHA/family_size for every member, so 5 -> 4 moves every bound. Same design, one
  assertion. Mechanism IS pinned (family, family_size, four Holm levels asserted end to end).
Task 8: minor (deferred): the re-added W-SWEEP-BASELINE-CONFOUNDED remedy is true only when an axis
  is FULLY freed. Half-fixing a multi-path `paired` axis makes _baseline_cells treat it as fixed, so
  per-cell expansion happens on the other axis while comparisons still differ on the paired paths and
  stay confounded. Not falsified — half-fixing is not freeing — and c208c58 already records the
  shape; a sentence beside the remedy would stop a later window re-opening task 7's question.
Task 8: minor (deferred, accepted as-is): baseline_for -> None silently drops the comparison.
  Reachable only through ablate x grid, which E-SWEEP-ABLATE-CROSSED refuses. The alternative —
  falling back to baselines[0] — is the cross-cell contrast per-cell baselines exist to remove, so
  dropping is the right answer of the two available. Pinned at expand level, argued in the docstring,
  W- deferred to whenever a legal design reaches it.
Task 8: the declined row-softening was correctly declined, on verified evidence. § Warnings core
  reports' row stands: the guard is "fixes every swept axis", so a baseline fixing two of three
  leaves it False while both cells moving the fixed axes are still marked confounded.
Task 8: PROCESS FINDING, mechanism now known. The task's disclosed "mutation revert appeared not to
  take effect with git status clean" is real and explained: CPython validates a .pyc against the
  source mtime truncated to SECONDS plus size. A same-size edit made inside the same wall-clock
  second as the cached compile is invisible — and once the mutant .pyc is cached, a same-size
  same-second revert stays invisible PERMANENTLY, not transiently, curable only by deleting
  __pycache__. Reviewer reproduced this. Every reported number was independently re-produced from a
  verified-clean tree with __pycache__ cleared. Standing rule for all later slices: verify a mutation
  revert by BEHAVIOUR, never by `git status`.
Task 9: complete (commit 24cb017 — tests only; the four documents and CLAUDE.md came back CLEAN from
  both passes, so no docs: commit and no empty commit). 1069 passed + 2 xfailed, ruff and mypy green
  on the final tree.
Task 9: EXIT CRITERION MET. E-SWEEP-GROUPS-UNSUPPORTED still fires and no groups axis expands —
  checked behaviourally (validate on a groups config; _axes == [] and expand == []), with both
  self-tests firing. Note for the groups slice: AXIS_MODES membership does NOT drive _axes (moving
  groups into it changes no expansion), so _axes is the thing to guard, not the tuple. No worked
  example figure moved (proven with a real temporary commit — a working-tree edit is invisible to a
  two-dot diff, which is how that check silently passes). Registry integrity holds both ways: 64 E-
  and 18 W- rows unmoved, every documented code still emitted, and the emitted-but-undocumented
  residual equals the base set MINUS EXACTLY the three retired -UNSUPPORTED codes. Mechanical pass
  clean over 669 relative links; the three named slugger false positives needed no exemption.
Task 9: TWO MAJOR DIVERGENCES FOUND, both created by the slice's own sequencing, both recorded in
  spec-defects.md with the documents left untouched (in both, the document is right).
  Causal chain: task 3 verified reference.md's two "a sample draw is not a comparison" claims and
  recorded that they held STRUCTURALLY because resolve_contrasts needs a declared baseline and
  E-SWEEP-BASELINE-PARTIAL refused baseline + sample. TASK 6 RETIRED THAT REFUSAL. The verdict was
  correct when made and false three commits later, and nothing re-derived it.
  (1) A sampled condition joins the correction family. grid × sample gives 6 vs_baseline comparisons
      where § Sweeps and repeats gives 2; validate also raises W-STATS-FAMILY for a sample-only
      sweep, which § Validation exempts. TWO code sites — validate's
      len(resolve_contrasts(...)) and cli's vs_baseline_members + contrast_members (no mode filter) —
      named separately because a fix at one leaves the other live. The "report says so" half of the
      claim is dormant: no report command exists.
  (2) Sampled labels are confidence=0.8615282253183009, where § How artifacts are organized specifies
      01_sample/02_sample. Not a one-line label_for change: the documented rule makes every draw's
      label BODY the literal `sample` while a selector names the body, and _condition_labels is a
      SET — so it is a ruling about selector identity for a later slice.
  Both carry an xfail(strict=True) handle in tracked tests (test_sweep.py, test_contrasts.py) because
  spec-defects.md is gitignored and task 2 already flagged the lost-finding-at-merge failure.
Task 9: TRIAGE of task 2's end-of-slice request — the paired value-checking gap is STILL OPEN at
  HEAD, verified: sweep.paired: [{analysis.min_sample: 30}] (a typo), [{analysis.method: pearsonn}]
  (outside choices) and [{analysis.method: "a long sentence"}] (unnameable) all validate with ZERO
  findings. _check_sweep runs _path_resolves/_value_checks over grid, sample ranges and ablate
  override; paired gets only the shape guards and E-SWEEP-PATH-DUPLICATE. Owner is still H2 with no
  task claiming it, exactly as task 2 said — it needs a charter revision or a new task, and task 9
  is not the place to mint three checks without a brief. Not fixed here; flagged for the final review.
Task 9: passes clean, two Major doc-vs-code divergences found, both created by this slice's own
  sequencing (task 3 verified two "a sample draw is not a comparison" claims held STRUCTURALLY
  because resolve_contrasts needs a declared baseline and E-SWEEP-BASELINE-PARTIAL refused
  baseline + sample; task 6 retired that refusal and nothing re-derived the verdict). Commit 24cb017
  pinned both with tracked xfail(strict=True) tests, since docs/superpowers/ is gitignored and a
  finding recorded only there does not survive the merge.
Task 9: fix round 1 dispatched. CONTROLLER RULING on finding 1 — do NOT implement the family
  semantics here; refuse the combination instead.
  Why the full fix cannot land in H2: § Sweeps and repeats expects 2 comparisons for grid × sample,
  which means the three draws COLLAPSE into one comparison — not that sampled conditions are skipped
  as subjects. Skipping them gives 0, not 2. Implementing "skip sample" as a filter would ship a
  second wrong number under a test asserting the first. A comparison's identity over a sampled axis
  is the correction family's semantics, which the spine assigns to H4.
  Why the xfail alone is not enough: it protects the next developer, not the user whose run silently
  corrects every interval against a denominator of 6 instead of 2 — and H2 CREATED that reachability.
  This is the same harm the task-7 -> task-8 merge gate was held for, with `sample` substituted for
  `baseline`.
  So: a narrow validate-time refusal of sweep.baseline together with sweep.sample, in the existing
  -UNSUPPORTED idiom, restoring exactly the protection task 6 removed — and making task 3's verdict
  true again FOR ITS STATED REASON rather than true by accident.
  Blast radius measured before writing it (probe, controller): sample alone = 3 conditions / 0
  generated comparisons, LEGAL and stays legal; sample + baseline = 3 generated; grid × sample +
  baseline = 6 generated where the doc gives 2; grid + baseline without sample = 2, untouched;
  sample alone + a declared statistics.contrasts entry = 0 generated / 1 declared, LEFT LEGAL because
  declared entries are user-named, do not inflate the generated family, and the document lets one
  name either side. A refusal wider than the harm would strand `sample` for designs that are fine.
  Consequence to expect, not to read as drift: the new code needs a registry row, moving § Validation's
  ### Errors validate reports table from 64 E- rows to 65.
Task 9: registry check, the direction `comm -23` cannot catch (controller, self-tested against a code
  that does exist): all four retired codes — E-SWEEP-BASELINE-PARTIAL, E-SWEEP-ABLATE-UNSUPPORTED,
  E-SWEEP-PAIRED-UNSUPPORTED, E-SWEEP-SAMPLE-UNSUPPORTED — are absent from both docs/*.md and src/.
  A surviving row for a retired code is the mirror of an undocumented code and that grep misses it.
Task 9: finding 2 (sampled labels render the drawn value where § How artifacts are organized specifies
  01_sample) NOT bundled into the fix — no correction-family consequence, and implementing it is a
  ruling about label bodies and selectors. The strict xfail is its disposition.
Task 9: the sweep.paired per-entry value-checking gap remains OPEN and unowned within H2 — a typo'd
  path, an out-of-choices value, and an unnameable value all validate with zero findings. Deliberately
  not fixed in the exit task; minting three checks without a brief is out of scope. Route it.
Task 9 fix round 1: commit 012472d (separate from 24cb017). E-SWEEP-SAMPLE-BASELINE minted —
  validate refuses sweep.baseline declared beside sweep.sample, in _check_unimplemented (where the
  retired E-SWEEP-BASELINE-PARTIAL lived), in the same specified-but-not-implemented idiom. This
  restores the protection task 6 removed when it retired E-SWEEP-BASELINE-PARTIAL, over exactly the
  reachable harm: sample with NO baseline stays legal (no comparison is generated without a declared
  baseline), a declared statistics.contrasts entry stays legal (members are named, not generated),
  and baseline + grid is untouched. Three mutants killed (refusal deleted; widened to any sample;
  narrowed to never) with __pycache__ cleared between every mutation and revert.
Task 9 fix round 1: THE FAMILY SEMANTICS ARE DELIBERATELY NOT IMPLEMENTED and belong to whoever owns
  the correction family. The document's expected count for grid × sample is 2, so the draws COLLAPSE
  into the grid's comparisons; skipping sampled conditions as subjects gives 0 — a second wrong
  number under the same assertion. The xfail(strict=True) in test_contrasts.py pins 2 at
  expand/resolve_contrasts level and its reason now names the refusal as today's protection and the
  family slice as the owner of removing both together. Same treatment in the spec-defects entry.
Task 9 fix round 1: REGISTRY COUNT MOVED 64 -> 65 BY THIS FIX, NOT BY DRIFT. reference.md
  § Errors validate reports gains the E-SWEEP-SAMPLE-BASELINE row (alphabetical position, before
  E-SWEEP-SAMPLE-INVALID); § Validation gains "Sample draws aren't compared to a baseline". W- rows
  still 18. Both comm directions re-run clean, mechanical pass 0 problems, worked example unmoved.
Task 9 fix round 1: ONE DEVIATION, FLAGGED. The code is named E-SWEEP-SAMPLE-BASELINE, not
  ...-UNSUPPORTED, because § The one config file says the -UNSUPPORTED family "is deliberately absent
  from the validate-time registry" — an -UNSUPPORTED code with a registry row would contradict it.
  The precedent the ruling itself cites resolves this: E-SWEEP-BASELINE-PARTIAL was not named
  -UNSUPPORTED, did carry a registry row, and did use the message idiom. The "Eleven declarations
  ... NOT BUILT" count is unchanged: this refuses a COMBINATION, not a declaration, exactly as
  E-SWEEP-ABLATE-CROSSED does. Suite 1072 passed + 2 xfailed, ruff and mypy green on 012472d.
Task 9: fix round 1 landed (commit 012472d), scoped re-review says FINDING CLOSED, three Minor
  findings, none blocking. E-SWEEP-SAMPLE-BASELINE refuses sweep.baseline beside sweep.sample, in
  _check_unimplemented — the same function the retired E-SWEEP-BASELINE-PARTIAL lived in.
  The re-review verified the load-bearing link the report only asserted: command_run gates on
  c.has_errors (any level == "error", no code whitelist) and returns EXIT_WRONG before the roster, the
  hashes, or any execution — and command_validate/command_run are the only commands in this build. So
  the second inflating site the finding named (cli's unfiltered vs_baseline_members + contrast_members)
  is UNREACHABLE for the refused shape, not merely unvisited.
  Scoping confirmed tight by probe: baseline leaving the sampled path free -> 6 comparisons, refused;
  baseline FIXING the sampled path -> 3 comparisons, refused (a shape E-SWEEP-BASELINE-PARTIAL would
  have missed); baseline: {} or null + sample -> 0 comparisons, correctly NOT refused; paired +
  baseline -> 2 comparisons, correctly not refused because the document counts paired; grid + baseline
  untouched. Three mutants killed with __pycache__ cleared between every mutation and revert, and the
  widen-the-refusal direction is pinned by a PRE-EXISTING test
  (test_a_sample_only_sweep_is_not_a_correction_family), not only by the new ones.
  Naming deviation, flagged rather than taken silently and upheld on precedent: the code is
  E-SWEEP-SAMPLE-BASELINE, not -UNSUPPORTED, because § The one config file says the -UNSUPPORTED family
  is deliberately ABSENT from the validate-time registry — so an -UNSUPPORTED code carrying the
  required registry row would contradict it. E-SWEEP-BASELINE-PARTIAL and E-SWEEP-ABLATE-CROSSED are
  both precedents: a combination refusal, a registry row, the "specified but not built" message idiom.
  The "Eleven declarations ... NOT BUILT" count is correctly unmoved — this refuses a combination, not
  a declaration.
  Only ONE of the two xfail reason lines needed rewriting, and the re-review was right to say so: the
  test_sweep.py label marker must NOT gain a "no config reaches it" clause, because a sample-only sweep
  validates clean and still produces confidence=0.8615282253183009. That defect IS live. My fix-round
  instruction said "both reason lines" and held for one.
Task 9: two of the three Minors closed by the controller in 82dff37 rather than deferred, both being
  one-clause fixes in a class this slice already treated as real (d53b702 fixed a message stating an
  impossible remedy):
  - the registry row and the message both said "every draw becomes a comparison"; under grid × sample
    it is every combination of a draw with the other axes' levels, six of nine conditions.
  - the row omitted the truthiness qualifier its sibling three rows above spells out. baseline: {} is
    correctly not refused — it fixes nothing, produces no baseline row, generates no comparison — but
    a reader could not tell that from the row.
  - the message said "drop the `baseline` here", IMPOSSIBLE for the ablate + sample + baseline config
    it also fires on, since ablate requires a baseline: dropping it trades this error for
    E-SWEEP-ABLATE-BASELINE-MISSING. Now "declare only one of the two".
Task 9: Minor 3 NOT fixed — a report-accuracy sentence in a gitignored file. The substance is worth
  carrying forward: the emitted-vs-documented `comm -23` check now reports E-SWEEP-BASELINE-PARTIAL
  again, because the new refusal's comment CITES it and the grep does not skip comments. Benign
  (a historical citation, not an emit site) and the same tolerated-resident class as the existing
  E-STATS-CONTRASTS-UNSUPPORTED docstring resident. Do not "fix" it by deleting the citation.
Task 9: complete (commits 24cb017, 012472d, 82dff37). Consistency passes clean over all four documents
  and CLAUDE.md; 669 links checked; W- rows still 18; E- rows 64 -> 65 by the fix, not drift.
  EXIT CRITERION MET: E-SWEEP-GROUPS-UNSUPPORTED still fires and no groups axis expands; no
  worked-example figure moved (proven with a real temporary commit, since a working-tree edit is
  invisible to a two-dot diff — which is how that check silently passes); registry integrity holds in
  both directions; pytest/ruff/mypy green.

## Whole-branch review

Verdict: BLOCK, cleared. One Critical, one Important, four Minors.
CRITICAL — sweep.paired received NONE of the four value-level checks its three siblings get. _check_sweep
  already ran _path_resolves + _value_checks over grid, baseline, sample.ranges and ablate.override;
  paired was the sole omission of four, and task 2 created the reachability by promoting paired from
  refused to executable without bringing the checks along. Five shapes validated with zero findings:
  a typo'd path, an out-of-choices value, a wrong type, a slashed value, and a list level.
  Failure scenario: the one-character typo `analysis.methdo` validates clean, runner's setdefault walk
  CREATES that key, analysis.method keeps the config's own value in every condition, and each condition
  still gets a distinct parameters_hash — so the run executes one experiment twice and records it as a
  two-arm sweep. That is the outcome § Mistakes core prevents lists under "A typo'd parameter silently
  using a default". The slashed value is CLAUDE.md's own named trap landing unsanitized in a path
  segment: 00_method=../../evil resolves out of the condition directory.
  Why it blocked rather than shipping as the routed follow-up I had been carrying: it is the branch's
  OWN task-9 ruling applied consistently ("the xfail alone is not enough: it protects the next
  developer, not the user, and H2 created that reachability"), the harm is larger, and unlike the two
  smaller gaps it had no handle at all. A second module already reasoned from the missing check.
  Fixed in 884959a: a loop over sweep.paired calling the same two helpers with nameable=True. No new
  identifiers. Both registry rows widened in the same commit — document-and-code-together, the allowed
  direction, and it resolved an EXISTING internal inconsistency: § How artifacts are organized already
  stated unscoped that validate rejects an unnameable swept value, so the two documents had disagreed
  with each other since task 2 and the code followed the narrower one.
  Controller verification through the suite's own write_config/codes fixtures: all five refused, a
  legal paired axis clean, and a grid control reporting — my FIRST probe harness bailed at
  E-TEMPLATE-UNKNOWN before the sweep checks ran and reported empty for everything, including the
  control. A check that could not fail, caught by the control. Keep controls in every probe.
IMPORTANT — W-SWEEP-BASELINE-CONFOUNDED's row stated a mechanism false for a half-fixed multi-path
  paired axis. Documentation-only fix (39477bf); the guard is behaviourally unchanged, verified by
  stripping comments from the source diff. Task 8's reviewer had already declined a softening of this
  row on evidence, and widening the guard is a behaviour change outside the fix's remit.
IMPORTANT (found by the scoped re-review, in 39477bf itself) — the fix introduced the very defect class
  it was removing, in the same row: "every comparison against it ... is reported confounded: true" is a
  false universal. confounded is len(differs_on) > 1, so a paired level whose value on the FIXED path
  equals the baseline's differs on one path only and is reported clean. Reproduced by the controller:
  the same half-fixed axis yields confounded False for one comparison and True for the other. Fixed in
  334cd83, in both the row and the emit-site comment. Worth remembering: this class survived a task
  review, a whole-branch review, and the commit written to remove it.
MINORS closed in 334cd83, all the same class: E-SWEEP-PATH-UNKNOWN's row called its six modes "every
  mode that fixes a value at a dotted path" when sample.ranges declares bounds and ablate.remove plants
  a removal (the load-bearing half — all six reach a condition through the setdefault walk — is true and
  now says so); E-SWEEP-VALUE-UNNAMEABLE's row called its three modes "every value label_for renders"
  then exempted a sample.ranges bound two clauses later (coverage was never wrong, the appositive was);
  _baseline_cells' docstring said validate "says nothing" about a half-fixed baseline, stale since
  012472d for sample; and a test docstring cited contrasts._cell_paths, a name that has never existed.
DURABILITY MARKER added: two comments now ARGUE from E-SWEEP-SAMPLE-BASELINE rather than mentioning it,
  and that refusal is documented to retire with the correction-family slice. The refusal's own comment
  now names both sites so whoever retires it can find what goes stale with it.
MINORS accepted, may ship: duplicate condition labels (reproduced at base ad6cf3d in a throwaway
  worktree — PRE-EXISTING, not branch-created; the branch adds two more routes to the same class);
  paired: 7 raising TypeError from the _names walk (raises identically at 82dff37, pre-existing);
  E-STATS/ablate residual value shapes (pre-disclosed, no document claims they are refused).
Ledger Minor CORRECTED by the review: task 6's "baseline fixing no swept path is gated today" is STALE
  — the gate was E-SWEEP-BASELINE-PARTIAL, retired at task 7. Verified live: baseline fixing an unswept
  path over a 4-cell grid validates clean and gives 8 conditions. The design may still ship — per-cell
  targeting keeps the family at 4 comparisons, so the harm is 2x compute, and a reference-arm design is
  legitimate — but the record said "gated" and it is not.
Cross-task seams, all five answered: no OTHER verdict rests on a retired refusal (the two survivors
  were both from E-SWEEP-PAIRED-UNSUPPORTED and are fixed); condition_dir_name is still the single
  builder and per-cell baselines cannot collide; the correction family is clean, proven by a could-fail
  mutation (deleting the is_baseline skip gives 6 comparisons with a baseline as a subject);
  § Mistakes core prevents was re-opened ONLY by the paired gap, now closed; sample's determinism holds
  and sweep.py stayed pure (scipy is a lazy import inside _sample_cells).
FINAL: 1079 passed + 2 xfailed, ruff and mypy green, at 334cd83.

# SDD ledger — plan: docs/superpowers/plans/2026-08-15-fixed-holdout.md

Slice H3d — a fixed holdout split. Branch `h3d-fixed-holdout`, forked from `78bb794` (main, post
H7a + H4a + the spec-defects audit). Baseline at fork: 1801 passed + 2 xfailed; ruff and mypy clean.
Spec: docs/superpowers/specs/2026-08-15-fixed-holdout-design.md (6 decisions + 6 appended corrections)
Measurement: docs/superpowers/H3d-SCOPING-2.md (2026-08-15, pinned to 78bb794) — REPLACES
  H3d-SCOPING.md, which was pinned to cb96c7d, FOUR SLICES BACK.
Execution: subagent-driven, WITHOUT standing merge authorization — STOP AND ASK before merge/push.

## Pre-flight scan

| Tasks | Shared | Finding |
|---|---|---|
| 2 -> 5,6,7,8,9 | the thirteen new `E-DATA-HOLDOUT-*` codes | Task 2 mints, 5-9 emit. Sequential. Task 2 also mints E-DATA-HOLDOUT-VARIES, which the scoping prescribed an entry for WITHOUT NAMING — controller-verified absent from src/ and reference.md |
| 5 -> 6,7 | `validate._check_holdout` | Task 5 CREATES it; 6 and 7 extend the same function. Same shape as H4a's _check_resample, which five tasks extended and whose COMMENTS carried five false claims read as instructions. Every dispatch must say the function already exists |
| 8, 16 | `validate.py`, separate check sites | Independent of _check_holdout. No conflict |
| 10,11,12 | `units.holdout_for` / seed | 10 builds unclustered, 11 clustered+strata, 12 the seed — and PER THE PLANNING CORRECTION `seed` is a REQUIRED KWARG holdout_for never derives, so 10/11 carry no forward reference to 12 |
| 13,15,17 | `cli.command_run` | 13 realizes once; 15 narrows six denominators; 17 writes allocation.json. Sequential |
| 1 -> 13,15,17,18 | `tests/test_cli.py` | Task 1's pin is the acceptance criterion for the wiring tasks, exactly as H4a's was |
| 2,4,8 | `spec-defects.md` | Three independent appends |
| 2 x 19 | `reference.md` NOT BUILT marker | CHECKED AND CLEAN: task 19 owns the marker and the count sentence; task 2's section contains ZERO "NOT BUILT" references. This is the H4a task-2/task-12 conflict I had to rule on there, and the plan avoided it unprompted |

Self-consistency per task: checked each task's tests against the code it specifies and the files it
creates against the files later tasks touch. **No conflict found requiring a ruling** — unusual, and
attributable to the plan author having been given H4a's fourteen brief defects as explicit rules.

Two plan properties worth recording because they are H4a lessons applied without being asked:
  - the "alongside, not instead of" rule appears FOUR times — every Part A test asserts its new
    finding beside E-DATA-HOLDOUT-UNSUPPORTED, so task 18's retirement is a one-line deletion
    rather than a rewrite of eight tasks' tests;
  - task 19's prose sweep carries a MUTATION PROVING THE SWEEP CAN FAIL (reintroduce a known
    sentence, confirm the grep returns it). Three H4a sweeps stopped one file short and none was
    mutation-tested.

## Task log

Task 1: implemented, commit 889de01 (tests only). 1803 passed + 2 xfailed (baseline 1801 + 2); ruff and
  mypy clean. Both required mutations (runner.execute_plan's no-fold branch, attrition's no-fold branch)
  confirmed FAIL then reverted in place with git diff empty afterward.
  THREE BRIEF DEFECTS, AND ONE WOULD HAVE MADE THE PIN VACUOUS:
  (1) executions.jsonl records carry NO `n` field at all — the brief's "n.resolved in executions.jsonl"
  corresponds to nothing this build writes; the real denominator lives only in run.yaml's aggregated
  block via _condition_counts.
  (2) THE VACUITY: the default one-step scaffold's aggregated block is EMPTY —
  {"step01_summarize_units": {}} — because it records a bool column stats.summarize_step drops outright.
  The brief's `assert aggregated` guard WOULD HAVE PASSED WHILE THE PIN'S INNER LOOP NEVER RAN. Fixed
  with aggregate_returns="mean_pred". This is the "control asserting only an absence" class wearing a
  new coat: the guard was truthy, the iteration was empty.
  (3) a single always-failing step yields run status "failed", not "partial", since run_status requires
  at least one completed execution; fixed by adding an always-completing second step.
  BASE for task 2 is 889de01.
Task 1 review: spec ✅, quality 1 CRITICAL + 2 Important + 1 Minor. All three brief defects verified
  independently, including the vacuity — the reviewer dumped the fixture and confirmed
  aggregated == {"step01_summarize_units": {}}, so `assert aggregated` passes while the loop iterates
  ZERO times.
  CRITICAL — THREE OF THE SIX NARROWING SITES MOVE WITH THE WHOLE SUITE GREEN. Mutating
  _condition_beside_n, _compute_vs_baseline(roster=) and the units_hash call each to
  UnitList(list(roster)[:3]) leaves 1803 passed / 2 xfailed. NO TEST IN THIS REPO CAN SEE THEM CHANGE.
  Two are exactly what the spec singles out (units_hash "must stay whole-roster"; _condition_beside_n is
  the filed technical_n gap). Unreachable for a FIXTURE reason, not a code reason — no measurements, no
  vs_baseline with `within`. Ruled: CLOSE THEM IN TASK 1. The plan routes end-to-end coverage to task 18,
  which lands AFTER the narrowing and therefore cannot be a baseline for it.
  IMPORTANT — THE PIN COVERS 1 OF 6. The units=roster -> execute_plan site is EXECUTED by the fixture and
  still missed: under mutation `value` 4.5 -> 1.0, `completed` 10 -> 3, `failed` 0 -> 7, BOTH ci95s move,
  and the run still exits EXIT_OK because _units_failed_anywhere is scoped to the same narrowed list so
  max_failed_fraction: 0.2 never fires on 7/10 — AND BOTH TESTS PASS, because the pin asserts
  n["resolved"] alone. Same shape as the previous slice's pin, which is why this one was promoted to
  first.
  IMPORTANT: units_hash pinned as a SHAPE (startswith("sha256:")) on one of the two values task 15 must
  not touch. A shape assertion survives any change to the thing it names. Ruled: recompute and compare,
  not a literal digest.
CARRY FORWARD (task 1 Minor, shapes tasks 14-17): executions.jsonl carries NO `n` field, so ALL OF TASK
  15'S DENOMINATORS ARE run.yaml-SIDE. Any test of a narrowing that looks for it in the ledger is
  looking in the wrong artifact.
Task 1: COMPLETE (commits 889de01, 33eafac). 1803 passed + 2 xfailed; ruff and mypy clean; src/ diff
  empty throughout, diffed byte-identical against a pre-round backup. Note the fix round was re-dispatched
  after the first agent died to a session limit having made no change — tree verified clean before resuming.
  THE FIX ROUND OVERTURNED BOTH THE REVIEWER'S DIAGNOSIS AND MY RULING, AND IT IS RIGHT —
  CONTROLLER-VERIFIED. The reviewer called _condition_beside_n and _compute_vs_baseline(roster=)
  FIXTURE GAPS and I ruled "close them in task 1". They are STRUCTURALLY DEAD PARAMETERS:
    - _condition_beside_n's narrowing is invariant under BOTH branches of _cond_roster — the identity
      check holds or fails independent of roster size;
    - _compute_vs_baseline's `roster` only feeds units_matching(roster, comp.within), and comp.within is
      PROVABLY None for every comparison reachable there. Verified myself: Comparison.within defaults to
      None (contrasts.py:33) and _baseline_comparisons constructs
      Comparison(id=…, of=…, against=…, declared=False) at :195 WITHOUT EVER SETTING within, so
      units_matching returns None unconditionally. The reviewer's proposed remedy — "a vs_baseline
      comparison with `within`" — DESCRIBES A CONFIG THIS CODE CANNOT PRODUCE.
  GENERALIZES, AND IT IS NEW: A SITE NO TEST CAN SEE IS NOT ALWAYS A FIXTURE GAP. It can be a DEAD
  PARAMETER, and no fixture can make a dead parameter observable — chasing one produces either a test
  that cannot fail or a config that cannot exist. Before ruling "extend the fixture", ask whether the
  argument reaches anything. The right remedy is to record the pinning obligation AGAINST THE TASK THAT
  MAKES THE PARAMETER LIVE.
CARRY FORWARD — TASK 14 AND TASK 15 EACH OWE A PIN: task 14 for _condition_beside_n and task 15 for
  _compute_vs_baseline(roster=), each becoming live under its own narrowing. Recorded as an obligation
  on those tasks, NOT as closed and NOT as an unowned deferral.
  Also closed in this round: the pin now asserts the FULL `n` dict plus value/ci95 rather than
  n["resolved"] alone (mutating execute_plan's units=roster now fails on completed 10->3, failed 0->7);
  and units_hash is RECOMPUTED AND COMPARED rather than asserted as startswith("sha256:").
  The fix round also independently re-verified the reviewer's two "caught by the whole suite" claims
  rather than trusting them — _condition_report_by_levels (11 named tests fail) and
  _compute_declared_contrasts (3 fail, including n_paired 20->1).
Task 2: implemented, commits 3b5e942 + d3ee12c. 1803 passed + 2 xfailed; ruff and mypy clean. Thirteen
  codes registered (twelve in § Errors validate reports, E-DATA-HOLDOUT-VARIES in § Errors core raises
  beside its VARIES siblings), both § Validation rows, the resample x holdout sentence, and THE
  INFERENCE-BASE RULING: the test partition counts as `n`, training units count NOWHERE, and
  provenance.units.n / units_hash stay whole-roster. technical_n filed not fixed. NOT BUILT marker
  correctly left to task 19.
CONTROLLER-VERIFIED CONTRADICTION, RAISED BY THE IMPLEMENTER AND RULED BACK TO IT: task 2's own
  reference.md text says a roster-wide split beside a cell structure is "REFUSED, NOT DRAWN" and that
  drawing within each cell "IS NOT BUILT", while experimental-designs.md:123 still says, present tense
  and unqualified, that "folds and holdouts are drawn WITHIN each cell". TWO NORMATIVE DOCUMENTS GIVING
  OPPOSITE ANSWERS TO ONE QUESTION. Ruled: task 2 closes it minimally NOW rather than leaving it to task
  8, six tasks away — CLAUDE.md says both consistency passes run BEFORE AN EDIT IS FINISHED, so the
  cross-document pass is the editing task's obligation, not a later task's. Task 8 keeps the fuller
  treatment.
  GENERALIZES: the rule that made task 2 right to LEAVE the NOT BUILT marker is the same rule that makes
  it wrong to leave this — NEVER SHIP A DOCUMENT STATE THAT IS FALSE, IN EITHER DIRECTION. It applied the
  principle in one direction and not the other.
PLAN DEFECT RECORDED: the plan attributes the reference.md cell-paragraph rewrite to TASK 8, but it
  actually fell to task 2. Task 8's implementer would otherwise assume the reconciliation already
  happened and check nothing. Task 8's dispatch must carry the current wording.
Task 2: COMPLETE (commits 3b5e942, d3ee12c, efba1e7, 641b63c, ecaa7dc). 1803 passed + 2 xfailed; ruff,
  mypy and the mechanical pass clean after each fix commit. CONTROLLER-VERIFIED: the "drawn within each
  cell" claim is now DEAD across all four documents.
  THE SWEEP LESSON DEMONSTRATED ITSELF. I pointed at ONE contradiction, in experimental-designs.md. The
  implementer's second pass found THREE MORE INSTANCES OF THE IDENTICAL CLAIM INSIDE reference.md — the
  file it had just finished editing: § Validation's "Folds fit inside the cells" row, § Cross-validation's
  opening ("Under allocation: between, folds are drawn within each cell"), and § Repeat kinds' fold row.
  Its own rewrite of § A fixed holdout split changed the underlying rule and left three siblings
  asserting the old one. THIS IS "SWEEP FOR THE CLAIM, NOT THE FILE" PROVING ITSELF INSIDE A SINGLE
  FILE — the boundary that traps people is not only the file, it is the SECTION they were editing.
  The superseded § Validation row was left in place rather than deleted, because H3c-3-SCOPING.md cites
  it BY NAME — correct call: a scoping is dated evidence and its citations must keep resolving.
PLAN DEFECT CORRECTED, AND MY LEDGER LINE WAS WRONG: the misattribution is in TASK 20's brief ("task 8
  already rewrote the one paragraph that did"), NOT task 8's. Task 8's brief correctly names task 2 and
  correctly flags two of the four spots as its own to finish. My previous entry said task 8; that is
  struck. TASK 20's dispatch is the one that must carry the current wording.
Task 3: implemented, commits 93372ce + 0c1f9b1. 1820 passed + 2 xfailed (baseline 1803 + 17 new); ruff
  and mypy clean. The measurements/resample precedent held — five LEAF_TYPES entries, NO closed key set.
  THIRD IMPLEMENTER, THIRD SET OF BRIEF DEFECTS, AND ONE IS "A MUTATION IS A CLAIM TOO" IN MY OWN BRIEF:
  (1) my `frac` comment claimed a false guarantee about (int, float) vs float — _is_type ALREADY promotes
  int->float, so the tuple is behaviourally redundant; it kept the tuple per the interface and reworded
  the comment.
  (2) MY SECOND MUTATION INSTRUCTION DOES NOT FALSIFY THE TEST. Deleting only the `method` line leaves
  four other holdout.* entries, which keep `holdout` A KNOWN CONTAINER — so the closure test still
  passes. It used a corrected mutation (delete all five) that does fail. This is the third
  non-discriminating mutation in two slices, and the second one I wrote.
  (3) A THIRD instance of the "holdout stays whole" claim beyond the two my brief named — inside
  _check_unknown_keys's OWN DOCSTRING in the same file. Task 2 hit the identical pattern one task ago:
  the false claim is never only where you noticed it.
  It also added a test BEYOND the brief's file scope, pinning end-to-end through validate_config that the
  new envelope finding and E-DATA-HOLDOUT-UNSUPPORTED fire TOGETHER — the brief's own tests exercised
  check_envelope directly, which would not have caught a wiring break.
Task 3 review dispatched. BASE ecaa7dc, HEAD 0c1f9b1.
Task 3 review: spec ✅, quality approved with findings — 1 Important, 3 Minor. Nothing blocks 4-7.
  Mechanism verified BY BEHAVIOUR: non-mapping holdout gives exactly one E-CONFIG-TYPE with no
  traceback; {} and null both silent, matching the documented null-is-absent rule and both sibling
  blocks; typos report at the exact path with the difflib hint; stratify_by takes bare string AND list;
  EVERY new assertion has a killing mutation. The five closed keys are exactly the set § Errors gives a
  code each, so no legal config is refused.
  ALL THREE BRIEF DEFECTS CONFIRMED, and the implementer's generalization on the blind mutation is the
  keeper: "DELETE ONE CHILD OF N>1" CAN NEVER FALSIFY A _known_containers DERIVATION, because the
  siblings keep the container known. That is the SHAPE of my error, not just the instance.
  Its out-of-scope end-to-end test is confirmed genuinely discriminating — dropping E-CONFIG-KEY-UNKNOWN
  at the validate.py wiring left ALL 32 envelope tests green and failed that one test alone.
  IMPORTANT — A FALSE CLAIM INTRODUCED INSIDE THE COMMIT THAT FIXED A FALSE CLAIM. The rewritten `frac`
  comment cites limits.max_failed_fraction's entry as precedent for (int, float); THAT ENTRY IS A BARE
  float. Same pattern H4a hit ("three overreaching claims inside a single commit that was itself fixing
  overreaching claims"), now seen in a second slice.
  MINOR WORTH GENERALIZING: the "alongside not instead of" rule was adopted to make task 18's retirement
  cheap, but this task's test NAME and docstring embed the wholesale refusal — so retirement is deletion
  PLUS rename PLUS docstring rewrite, not one line. A REFUSAL NAMED IN A TEST'S IDENTIFIER DEFEATS THE
  RULE EVEN WHEN THE ASSERTION IS RIGHT. Later tasks: name tests for the behaviour, not for the refusal
  that happens to co-occur.
CARRY TO TASK 19: reference.md:456 now states the opposite of the code, and plan item (e) as drafted
  replaces only the TRAILING PARENTHETICAL, leaving the earlier clause ("a typo inside
  data.units.holdout ... is reached by no check at all") false. THE WHOLE ROW needs rewriting.
Task 3: COMPLETE (commits 93372ce, 0c1f9b1, cdf7295). 1820 passed + 2 xfailed; ruff and mypy clean. The
  false citation is gone — the comment now states plainly that the tuple documents what _is_type already
  does for a bare float, dropping the comparison rather than repairing it. All four findings closed;
  comment-only, so no new mutation round was owed and it said so rather than inventing one.
  BASE for task 4 is cdf7295.
Task 4: dispatched — design_digest excludes holdout.seed, and the open half of its spec-defects entry.
Task 4: implemented, commit TBD. 1823 passed + 2 xfailed (baseline 1820 + 3 new); ruff and mypy clean.
  `_units_excluding_assign_seed` renamed `_units_excluding_drawn_seeds`, now dropping `holdout.seed`
  alongside each `assign.<axis>.seed`; sweep for the old name returned nothing except the two
  narrative mentions in spec-defects.md that explain the rename by name (expected, per brief step 3's
  own replacement text). spec-defects.md's open half struck and closed; its CLOSED half (task 16's
  paragraph) also named the old function and was updated too, since the brief said every hit moves.
  reference.md § What `auto` derives from already carried both the prose and the table row naming
  `holdout.seed` and `E-DATA-HOLDOUT-SEED` (verified, not assumed) — no doc change owed there.
  TWO ISSUES SURFACED AND BOTH FIXED BEFORE COMMIT, NOT AFTER:
  (1) Step 4's literal command `uv run ruff format .` (not `--check`) rewrote 67 files, including
  fenced Python inside README.md — reverted everything outside the three task files via
  `git checkout --`, confirmed `ruff format --check` baseline back to 67 (was silently 66 for one
  cycle). Future briefs should say `--check` in step 4.
  (2) The brief's step-5 second mutation (`out = {**out, "holdout": None}` gated on
  `isinstance(holdout, dict) and "seed" in holdout`) cannot discriminate `base` from `widened` in
  `test_a_pinned_holdout_seed_does_not_move_the_design_digest` — NEITHER has a `seed` key, so that
  branch never fires for either config, and the mutation instead fails on the EARLIER
  `design_digest(base) == design_digest(pinned)` assertion (because `pinned` alone gets nulled).
  A MUTATION WHOSE TWO BRANCHES CANNOT DIFFER, per CLAUDE.md's own catalogue. Substituted the
  unguarded form `if isinstance(holdout, dict): out = {**out, "holdout": None}` (no `"seed" in
  holdout` guard), which fails on the intended `design_digest(base) != design_digest(widened)`
  assertion instead — that is the mutation that actually proves the positive companion. Both
  mutations run, confirmed FAIL, reverted in place, diffed byte-identical against a pre-round backup,
  confirmed PASS.
  See task-4-report.md for the commit sha.
Task 4: controller verification of the collateral revert. `git diff --stat cdf7295..HEAD` is exactly five
  files — progress.md, task-4-report.md, spec-defects.md, hashes.py, test_hashes.py. README.md is
  untouched (the only `docs/` entry is spec-defects.md), and `ruff format --check` reports 67 would-be
  reformats against 267 already formatted, which is the pre-task baseline. The hashes.py diff was read in
  full: 46 added lines, all of them the rename, the `holdout` branch, and rewritten docstrings — no
  reformatting hunk survived.
  Ruling: my brief's Step 4 said `uv run ruff format .` where every prior task said `--check`. That is a
  MUTATING command issued as a verification step, and it rewrote 67 files repo-wide including fenced
  Python inside a normative document. Cost if the implementer had not caught it: a formatting commit
  spanning the whole repo buried inside a one-function task, and README prose silently altered. Every
  remaining brief in this plan is to be read for `ruff format` without `--check` before dispatch.
  Ruling: this is the THIRD blind mutation I have authored across H4a and H3d — H4a task 10's
  `range(len(group)) -> range(1)`, H3d task 3's "delete the `method` line", and now H3d task 4's Step 5
  second mutation. All three share one shape: I proposed a mutation without checking that the fixture
  actually reaches the mutated branch. Cost if uncaught: a test recorded as mutation-proven that never
  ran the mutation. Remaining briefs get their mutations checked against the fixture they name, not
  against the code alone.
Task 4: reviewed (opus). Spec compliance PASS; task quality FAIL with one Critical, one Important, five
  Minor. Critical verified by me before dispatching the fix: `reference.md` § What `auto` derives from
  still opened "every field except `assign.seed` itself" while a later paragraph in the SAME section
  already said `holdout.seed` is excluded too — the code was fixed and the normative sentence it mirrors
  was not. In this repo the documents lead, so a false document state is the blocking defect, not the
  code.
Task 4: fix round 1 (fresh agent — the implementer's id did not survive compaction; a precise brief
  substitutes, and the diff is small enough that it did). Commit fe7fd01. `reference.md`'s parenthetical
  now states the RULE — "every field except a drawn partition's own seed" — with the two names as
  illustration, so a later slice adding a third drawn partition does not silently falsify it. Sweep for
  the old phrasing over the four documents, CLAUDE.md, `src/` and `tests/` returns zero; the quotations
  in `spec-defects.md` and `H3c-SCOPING.md` were correctly left standing as dated evidence.
  Three docstring/comment claims narrowed: "redraws nothing" -> "redraws nothing else" (pinning
  `holdout.seed` does redraw the holdout), and the `moved` fixture's comment now describes the one block
  it actually edits. Report correction appended, not retro-edited.
  Ruling: the reviewer's Important finding is FALSIFIED in its premise, and I ran the mutation myself to
  settle it. Inserting `if not isinstance(assign, dict): return units` before the holdout branch fails
  TWO tests, not zero — `test_a_pinned_holdout_seed_does_not_move_the_design_digest` was already
  discriminating, because its fixture omits `assign` entirely and so takes the same early return. The
  reviewer reported "all 17 green"; that did not reproduce. The added test stands anyway: it pins a
  non-mapping `assign` where the pre-existing one pins an ABSENT `assign`, which are different shapes
  through `.get`, and it is the more explicit of the two. Cost if wrong: one redundant test.
  Ruling: the `ruff format --check` count moving 67 -> 68 is NOT a regression. Measured at `5ff2448` in a
  scratch worktree: 67, with `tests/test_hashes.py` and `docs/reference.md` ALREADY among them. The 68th
  is the reviewer's own untracked `task-4-review.md` — ruff's check counts markdown in this repo, which
  is also why the brief's `ruff format .` accident rewrote fenced Python inside README. Both the fix
  agent's and the reviewer's numbers were right; they measured trees differing by one untracked file.
Task 4: complete. 1824 passed + 2 xfailed; ruff check and mypy clean. BASE for task 5 is fe7fd01.
Ruling (plan-wide, made before task 5 dispatched): all 19 verification steps in
  `plans/2026-08-15-fixed-holdout.md` said `uv run ruff format .` and none said `--check`. That is a
  MUTATING command standing in a verification step, and it is what rewrote 67 files including fenced
  Python inside README.md during task 4. Rewritten in place to `--check`, all 19, because a plan is a
  live instruction set that re-fires on every remaining brief — not dated evidence, which is corrected by
  appending. Cost if wrong: a plan diff that does not match the plan as originally written, recorded
  here.
  Noted for the slice review, not acted on: `CLAUDE.md`'s command table lists Format as
  `uv run ruff format .`, and running it rewrites 67 files including prose documents, because ruff's
  formatter reaches fenced Python inside markdown here. The documented command damages the four
  documents. Out of scope for H3d; belongs to whoever next edits that table.
Task 5: dispatched — `_check_holdout` declaration half A, wired into `validate_config`. Before dispatch I
  checked all three of the brief's prescribed mutations against the fixtures they name, per the ruling
  after task 4. All three discriminate: (a) the `frac: 0` and `frac: 1` rows exist in the parametrized
  list; (b) passing `{}` for `units_decl` kills the third assertion of
  `test_an_empty_or_null_holdout_validates_clean`, which is the positive companion; (c) dropping the
  `not holdout` gate moves only that test's FIRST assertion, since `holdout: null` is not a dict either
  way. This is the check I committed to after authoring three blind mutations, and it is now paying for
  itself.
Task 5: implemented at 5e3d965. 1846 passed + 2 xfailed.
Task 5: reviewed (opus). Spec compliance PASS; task quality FAIL with six Important and four Minor.
  The load-bearing one is F3, and it is this repo's dominant defect class again: ELEVEN `c.error` sites
  and not one test reading a message. The reviewer mutated `if method is None:` to `if False:` and
  `elif not isinstance(method, str):` to `elif False:` and each left 24 of 24 tests GREEN, because two
  branches share a code and the tests only asserted the code. `messages_by_code` was already in the same
  file.
  F2 I verified myself before dispatching, because it edits a normative document: `frac` and `from` are
  both typed in `envelope.py`'s `LEAF_TYPES`, so a wrong type earns `E-CONFIG-TYPE` from `check_envelope`
  and never reaches `_check_holdout` — the § Errors rows claiming those codes cover wrong types were
  overclaiming. A third row enumerated two NO-DRAW emit sites where the code has three. § Errors carries
  one row per code covering every emit site, so the rows were what changed, not the code.
Task 5: fix round 1. Commit 638639e. All ten findings closed.
  Ruling: F5 was closed by changing BEHAVIOUR rather than the claim — `stratify_by: []` under
  `by_attribute` is now exempt. I verified the convention it now mirrors: `validate.py:2803` reads
  `is not None and != []`, byte-for-byte the test `assign` already makes at `validate.py:2435`, and
  § Errors' `E-DATA-ASSIGN-NO-DRAW` row says "non-empty". Aligning with the documented sibling beats
  narrowing a message to describe an inconsistency. Cost if wrong: an empty `stratify_by` under a
  holdout is silently accepted where a reader might expect a refusal — which is exactly what assign
  already does.
  Ruling: F9's `doc` parameter is a genuine forward reference, not dead weight — task 6's
  `E-DATA-HOLDOUT-FOLD` reads `doc.get("replication")`. Confirmed against the plan. This is the same
  distinction task 1's fix round settled in the other direction, where two sites the reviewer called
  fixture gaps were dead parameters. The two cases differ by whether a LATER TASK fills the parameter,
  and that is the question to ask each time.
  I re-ran F3's first mutation myself rather than take the fix on report: `if method is None:` ->
  `if False:` now FAILS `test_a_malformed_holdout_declaration_is_refused[block0-...-is not declared]`,
  where the same mutation left 24 of 24 green before the fix. Reverted by editing the file back,
  confirmed byte-identical to HEAD and 25 passed.
Task 5: complete. 1847 passed + 2 xfailed; ruff check and mypy clean; `ruff format --check` down to 68
  (67 tracked baseline + one untracked record file). BASE for task 6 is 638639e.
Task 6: dispatched — `stratify_by` existence and the `holdout` x `fold` mutual exclusion. Pre-checked both
  brief mutations; the brief's own text rejects its first candidate as non-discriminating and prescribes a
  replacement, and the fold fixture declares `[{kind: fold, k: 5}]` with no `batch` level, so retargeting
  the exclusion to `"batch"` makes it never fire.
Task 6: implemented at bbd4a29 / b5d1ae6. 1857 passed + 2 xfailed.
  MY PRE-CHECK WAS ITSELF INSUFFICIENT AND THE IMPLEMENTER CAUGHT IT. I confirmed the mutation's target
  test EXISTED and never read its ASSERTIONS. The test asserted only a finding COUNT of 1, and the
  mutation produces count 1 too — via the wrong branch, with a different message. The implementer ran it,
  saw PASS, strengthened the test to read the message, and re-proved it.
  Ruling: the discipline adopted after task 4 was "check the mutation against the fixture it names". That
  is now amended to "check the mutation against the ASSERTIONS the fixture makes" — a fixture's existence
  says nothing about whether its assertions can see the difference the mutation makes. This is the same
  defect as CLAUDE.md's "a dimension no assertion can see", arriving from the mutation's side rather than
  the test's. Cost of the weaker form: a mutation recorded as proof that proves nothing, which is what
  three of my four blind mutations were.
Task 6: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important and four Minor.
  F1 is the class again: `if not isinstance(name, str) or not name:` -> `if False:` left the FULL SUITE at
  1857 passed, because all four rows assert only the code and `7`/`[3]` fall through to the undeclared-name
  branch under the same code at the same path. The `not name` clause had no fixture at all.
  Ruling on F2, where the review's remedy was incomplete and I overrode it. The review found § Errors
  self-contradicting — the `-NO-DRAW` row says an empty `stratify_by: []` is not refused, while `[]` in
  fact earns `-STRATIFY-UNKNOWN` — and proposed fixing that one row. I probed the code instead. There is
  NO behavioural contradiction: `[]` is refused exactly once, under the accurate code. The empty refusal
  is CORRECT and stays, because `materialize.py` writes `holdout: null` and `init` never materializes a
  holdout block, so refusing `[]` breaks no `init` output. That is also why holdout may differ from
  `assign` here despite task 5 aligning the two on the `!= []` exemption — for `assign`, `init` DOES write
  `stratify_by: []`, so the exemption there is forced. The asymmetry is principled.
  The defect was purely the CLAIM, and it was false at TWO sites, not the one the review named: the
  § Errors row, and the NO-DRAW branch's own message saying `[]` is "what `init` writes and changes no
  behavior" — both halves false for holdout. Sweep for the claim, not the file it was noticed in.
  Cost if wrong: a `stratify_by: []` under a holdout is refused where a user might have meant it as an
  explicit "no strata"; `init` never writes that shape, so nobody arrives at it by accident.
Task 6: fix round 1. Commit 062253f. All five actionable findings closed; F6 left alone as instructed —
  `units.stratum_names`'s docstring names two call sites and has six, which is pre-existing and belongs to
  the roster-half task. CARRIED TO TASK 7, along with the design's own note that
  `stratum_varies_within_cluster`'s docstring claims two rows and has three callers, becoming four there.
  Verified myself that `ruff format --check` rising 68 -> 70 is not a regression: measured 68 at 8f7270b
  in a scratch worktree with `validate.py` ALREADY among them, and the two added files are this task's own
  review and report records.
Task 6: complete. 1859 passed + 2 xfailed; ruff check and mypy clean. BASE for task 7 is 062253f.
Task 7: dispatched — the roster half: `E-DATA-HOLDOUT-VALUES`, `-STRATIFY-VARIES`, `-EMPTY`, plus
  `units.holdout_sizes` and `units.holdout_values_fault`. Pre-checked all three brief mutations against
  the ASSERTIONS their fixtures make, per task 6's amended discipline. All three discriminate. I briefly
  believed mutation (a)'s arithmetic was wrong — `_apportion(4, [0.2, 0.8])` is `[1, 3]`, not the `(0, 4)`
  the brief claims — and was about to dispatch a correction. The brief was right and I was wrong: I had
  taken `frac: 0.2` from the mutation's `-k` filter instead of reading the fixture, which declares
  `frac: 0.1`. At 0.1 the numbers are exactly as written, `[4, 0]` against `[0, 4]` and `[36, 4]` against
  `[4, 36]`. Recorded because the near-miss is the lesson: the amended discipline says read the
  assertions, and reading half of them is how you manufacture a false correction.
Task 7: implemented at 880750c. 1869 passed + 2 xfailed. `stratum_varies_within_cluster`'s docstring
  corrected from two call sites to four, as the design assigned. `stratum_names`'s stale docstring left
  again, correctly — this task adds no call site, so the deferral stands rather than being absorbed.
Task 7: reviewed (opus). Spec compliance PASS; task quality FAIL with one Critical and three Important.
  Critical: the same defect for the FOURTH consecutive task in this one function — three new error sites
  and no test reading any message. Inverting `missing` to `if lit in seen` left 67 holdout tests green.
  Both the task 5 and task 6 reviews prescribed the `fragment` + `messages_by_code` remedy, and it was
  applied at none of the three new sites. That the remedy exists in the same file and was still not
  reached for is the finding worth carrying: a defect closed in one task is not closed in the next unless
  the next task's brief says so. **Every remaining brief in this slice must name it.**
  RULING — AND THE INSTRUCTION THAT WAS WRONG WAS MINE. I told every implementer in this slice to assert
  each finding ALONGSIDE `E-DATA-HOLDOUT-UNSUPPORTED`, so the assertion survives task 17 as a one-line
  deletion. That part stands. But three of this task's controls went further and claimed that companion
  gave POSITIVE ATTRIBUTION — "without it this passes identically if `_check_holdout` never ran". False:
  `-UNSUPPORTED` is emitted by `_check_unimplemented`, a different function entirely. With
  `_check_holdout` returning immediately, all four controls passed. This is CLAUDE.md's "a control
  asserting only absences" wearing a companion assertion as a disguise, and the disguise is what I
  supplied. Closed by giving each control a `seed: "bogus"` earning `E-DATA-HOLDOUT-SEED`, a code only
  `_check_holdout` emits. I verified this myself rather than take it on report: inserting `return` as
  `_check_holdout`'s first statement now FAILS all three, where all three passed before. Reverted by
  editing back, byte-identical to HEAD, 3 passed.
  It matters past today: at task 17 the `-UNSUPPORTED` lines get deleted, and any control resting on them
  would silently become absence-only. **Task 17's brief must re-verify every control it touches.**
Task 7: fix round 1. Commit 00114d3. All nine findings closed; two Do-Not-Fix items held —
  `stratum_names`'s docstring, and the typo'd-`from` diagnostic gap routed to spec-defects.md.
  Ruling: the five added lines sitting in `ruff format` would-reformat hunks are NOT to be formatted.
  `validate.py` and `tests/test_validate.py` were already unformatted at 880750c, so formatting either
  wholesale would bury a one-function task's diff inside an unrelated repo-wide rewrite — the exact
  accident this slice already had once. The claim was corrected in the report instead. Cost if wrong:
  five lines that a future repo-wide format will touch anyway.
Task 7: complete. 1872 passed + 2 xfailed; ruff check and mypy clean. BASE for task 8 is 00114d3.
Between tasks 7 and 8 — four corrections made at SOURCE rather than carried as reminders.
  Ruling 1: the message-pinning defect is now a GLOBAL CONSTRAINT of the plan, not a line in the next
  brief. Evidence that the per-brief remedy fails: task 7's brief DID name it, verbatim, and the
  implementer still shipped three code-only assertion sites. Four consecutive tasks, three separate
  briefs naming it. Same move as the `ruff format` fix — put it where every task inherits it. The
  constraint also records that `E-DATA-HOLDOUT-UNSUPPORTED` is not positive attribution, so no later task
  repeats the mistake I made.
  Ruling 2: task 8's own test code is patched in the plan, not left to a reminder. Its `where` is a
  two-branch ternary and BOTH branches emit `E-DATA-HOLDOUT-CELLS` at the same path, while the two tests
  exercising them asserted only the code — collapsing the ternary would have passed both. Added the
  message assertions, a fourth mutation that collapses the ternary, and corrected the control's docstring
  claim that `-UNSUPPORTED` proves the check ran. Step 5's count phrase moved three -> four.
  Ruling 3: `reference.md`'s `E-CONFIG-UNKNOWN` row was FALSE TODAY and had been for four tasks. It said
  "a typo inside `data.units.holdout` ... is reached by no check at all" and justified it as latent
  because the whole block is refused — but task 3 closed the envelope for all five holdout leaves, so
  `check_envelope` reaches such a typo now. Task 5's own test docstring asserted the opposite. Fixed here
  rather than deferred to the sweep task, because a normative document that is false is not a sweep item.
  `envelope.py`'s own docstring was checked and is correct — task 3 rewrote it properly; only the
  document lagged. This is also the record of that row's identity by CONTENT rather than by the line
  number it was carried as, which is the repo's own convention and which an insertion would have broken.
  Ruling 4: two deferrals were living only in review prose and are now FILED — the typo'd-`from` values
  fault with no attribute-existence hint, and `units.stratum_names`'s docstring naming two call sites
  against seven. CLAUDE.md's own lesson is that a ledger line saying "filed" is not a filing, and both
  would have been exactly that. Each names its owner as a SLICE and says to re-owner it rather than let
  it point at a closed one. A third item, § *How a metric becomes a number*, was checked and is genuinely
  filed already.
  Ruling 5: the per-task format reconciliation is retired. The invariant that matters is narrower than the
  repo-wide count — no file a task touched became newly unformatted — and
  `uv run ruff format --check $(git diff --name-only BASE..HEAD -- '*.py')` answers it in one call, with
  no scratch worktree and no untracked-markdown noise. Four rounds were spent reconciling 67 -> 70 for a
  number that was never the question.
Task 8: dispatched — the shared cells refusal, `_check_evaluation_split_cells`, two codes from one site,
  H3c-3 named as owner of its retirement. First task dispatched under the new Global Constraints.
Task 8: implemented at fa6accc / 44e232c, DONE_WITH_CONCERNS with three disclosed. Confirmed the LIVE
  defect by hand before closing it, as the brief required: the fold-beside-cells fixture validated with
  `found == set()` — no error at all — on the shipped build. That is the defect H3c-3 would otherwise have
  carried, and seeing it is what stops a refusal being written against a fault that was never there.
  Task 2's document work was already in place, so two of the brief's three document steps were phantom
  edits. The implementer reported that rather than writing them twice, which is what the owed-context note
  existed to buy.
Task 8: reviewed (opus). Spec compliance PASS; **task quality PASS** — the first of this slice. The
  reviewer's words: "the four-task pattern of unfailable tests does not recur." Moving the message-pinning
  rule from the next brief into the plan's Global Constraints, and patching task 8's test code at source,
  is what changed; three briefs naming it had not.
  All three disclosed concerns adjudicated and none upheld. The one worth recording: `if units.get(
  "holdout"):` is a bare truthiness gate where `_check_holdout` uses `isinstance(..., dict) and holdout`,
  so a bare-string holdout beside cells earns `-CELLS` while `_check_holdout` stays silent. Ruled
  acceptable — the divergence is confined to truthy non-mappings, which is exactly `E-CONFIG-TYPE`'s
  territory; `_check_unimplemented` already uses the identical gate on the same key; and § Errors' row
  says "is declared beside", which is true of a string.
Task 8: fix round 1. Commit aff6ca5. One Important closed — the `and groups` emptiness half of the `cells`
  predicate was unpinned, and dropping it left the whole suite green while a config with
  `sweep.groups: []` and a holdout would have earned a spurious refusal that all three document sites
  contradict. Also fixed a doubled verb in the `E-REPL-FOLD-CELLS` message, which the shared `reason`
  string had forced, by factoring the tail into a `consequence` and giving each code its own verb.
  Ruling: the review found the function's three `isinstance` guards unreachable from `validate_config` —
  `E-CONFIG-SHAPE` returns first, proven with a `raise RuntimeError` probe. They stay, untested and
  uncommented. Recording it here so it is not re-derived: an unreachable guard is not a testable one, and
  a comment asserting it is reachable would be this repo's most recurring defect in its purest form.
Task 8: complete. 1879 passed + 2 xfailed; ruff check and mypy clean. BASE for task 9 is aff6ca5.
Task 9: dispatched — `holdout.from`'s constant-column accessor, its `CONSTANT_COLUMN_RULES` entry, and its
  place in the severity ordering.
Task 9: implemented at bf27897 / 08351ff. 1891 passed + 2 xfailed.
  MY FIFTH BLIND MUTATION, and the pre-check that was supposed to catch it did not. The brief's mutation
  (b) claimed moving the `constant.update` ordering would fail a named test. The implementer ran it: the
  named test PASSED and so did all 175 tests in the file — zero effect. The test builds its `constant`
  dict BY HAND and never calls `resolve_units`, so it only ever proved `collapse_measurements` stops at
  the first key of whatever dict it is handed. CLAUDE.md's "a seam named in the brief and instantiated by
  no fixture", exactly.
  Ruling: the discipline is amended a second time. After task 6 it became "check the mutation against the
  ASSERTIONS the fixture makes". That was still not enough here, because I read the BRIEF'S ARGUMENT about
  the test — which was articulate, cited the right fixture, and was wrong — instead of the test body. The
  rule is now: **read the test body, and where the brief argues for discrimination in prose rather than
  arithmetic, run the mutation before dispatching.** Prose confidence is not evidence. Cost of the weaker
  form: a mutation recorded as proof that proves nothing, which is what five of my mutations across two
  slices have now been.
  The implementer closed the gap itself with `test_resolve_units_checks_holdout_after_assign_and_before_
  cluster`, which calls `resolve_units` directly, and the reviewer independently re-ran the mutation and
  confirmed the replacement discriminates where the original did not.
Task 9: reviewed (opus). Spec compliance PASS; task quality FAIL with four Important and four Minor.
  The substantive one: adding `"holdout"` to `CONSTANT_COLUMN_RULES` opened a SECOND route into the
  registry that the accessor was built to be the only one for — `resolve_units`' flat comprehension
  admits a string-valued `data.units.holdout` and emits `E-DATA-HOLDOUT-VARIES` at a path with no
  `.from`, bypassing the accessor's `by_attribute` gate. Covered by no § Errors row, pinned by no test,
  and falsifying two sentences written in this same task.
  Ruling: close the route, do not document it. A second route that bypasses the gate makes the gate
  decorative, and both sentences describing the design were already written as though one route exists.
  The alternative — keeping the route and correcting the sentences — would have preserved a behaviour
  nobody designed. Cost if wrong: a string-valued holdout now reaches `validate`'s refusals rather than
  resolution's, which is where a malformed declaration belongs anyway.
Task 9: fix round 1. Commit c799d2f. All eight closed, plus the report correction. The route is closed and
  pinned; `E-DATA-HOLDOUT-VARIES` is dual-listed like its three siblings; two stale enumerations were
  replaced by pointers rather than by corrected counts, which is the form that does not go stale again;
  and the test whose NAME claimed an ordering guarantee it never tested was renamed to the property it
  actually pins.
Task 9: complete. 1892 passed + 2 xfailed; ruff check and mypy clean. BASE for task 10 is c799d2f.
Task 10: dispatched — `units.holdout_for` construction 1: the unclustered draw and the column read. First
  task in the slice that draws anything. Pre-checked all three mutations by READING THE TEST BODIES, per
  the discipline amended twice; all three discriminate, and the brief rejects its own candidate for (c)
  as a no-op with the correct reason (the function indexes `arms_of`'s mapping by level, not by position).
Task 10: implemented at a6c6945 / 30a9338. 1902 passed + 2 xfailed.
  Real disagreement found: the brief's test helper `_roster(n, **attrs_by_index)` would have SHADOWED an
  existing module-level `_roster(n)` in `tests/test_units.py` used by a dozen tests, three of which pin
  zero-padded key literals. Appending it verbatim would have silently rebound the name and broken them.
  Renamed to `_holdout_roster`. This is the plan authoring a name collision, not the implementer missing
  one — worth carrying: a brief that appends test helpers to an existing file must be read against that
  file's existing names.
Task 10: reviewed (opus). BOTH verdicts FAIL, but the behaviour is correct and independently confirmed —
  a testing-and-claims round rather than a rewrite.
  The affirmative result is the one worth recording: the reviewer did not trust the pinned membership
  literals and re-derived the construction, finding `holdout_for` and `assignment_for`'s `random` branch
  return BYTE-IDENTICAL membership for the same seed and weights — same `_apportion`, same single
  whole-roster shuffle, same consecutive slices, both refusing the zero-size case before shuffling.
  **No bit-stability reconciliation is owed to task 11**, which the spec listed as a trap.
  Ruling on finding 3, where I made the code follow the claim rather than the reverse. The docstring said
  in bold that both sides are refused empty; the guard checked TYPE only, so `frac: -0.5` returned a plan
  with an empty test side and `frac: 2.0` one with an empty train side. `holdout_for` is public and a
  later task wires it from `cli.command_run`, so a silent degenerate partition is worse than a refusal,
  and the function already raises for the zero-size case. The guard was widened to the open interval,
  deliberately duplicating a rule `validate` also enforces — `validate` refuses the config, this refuses
  the call. Cost if wrong: one range test in two places, which is the cheap direction.
  Carried to task 11, from the reviewer: the empty-side refusal reads `holdout_sizes`' DECLARED sizes,
  which a clustered draw's REALIZED sizes are not, so task 11 must restate that refusal per branch. The
  seam is otherwise sound — task 11's only undo is swapping the `strata=()` literal and deleting the
  up-front raise.
Task 10: fix round 1. Commit f48cd68. All eight closed. Two of the three vacuous assertions were the exact
  shape the Global Constraint targets and had slipped past it: `assert empty_side in str(exc.value)`
  matched whichever side was passed, because the message's invariant tail names BOTH sides — so inverting
  the side-naming line left the full suite green. A message assertion is not automatically a
  discriminating one, and that is a new entry for the catalogue.
Task 10: complete. 1913 passed + 2 xfailed; ruff check and mypy clean. BASE for task 11 is f48cd68.
Task 11: dispatched — construction 2: whole clusters, `stratify_by`, their composition, and the relation
  between the constructions. Pre-checked all three mutations by reading the test bodies; all three
  discriminate, and the stratified test correctly pins MEMBERSHIP as well as counts because the
  per-stratum counts are forced by the apportionment and no count assertion can see a generator change.
Task 11: implemented at 9d5e75c. 1917 passed + 2 xfailed. Four disagreements reported, two of which reach
  back into task 10's tests: one task-10 assertion rewritten, and one task-10 test DELETED.
Task 11: reviewed (opus). Both verdicts FAIL. The reviewer's attribution is the finding I am carrying
  forward: "the implementer followed the brief faithfully and all three of its mutations discriminate;
  the gap is that the brief's mutation set never touched the composition or any message path."
  Ruling: my pre-dispatch check has been asking the wrong question. I verify that each prescribed
  mutation DISCRIMINATES; I have not been asking what the mutation set FAILS TO COVER. A brief can
  prescribe three sound mutations and still leave its own headline deliverable unpinned — here Step 3(a)'s
  new declaration path was pinned by nothing, and corrupting it back to the exact bug that step exists to
  fix left all 1917 tests green. **The check is now: for each of the task's stated deliverables, which
  mutation kills it? A deliverable no mutation reaches is unpinned however good the mutations are.**
  Both flagged cross-task items adjudicated. The deletion of task 10's
  `test_a_clustered_or_stratified_holdout_raises_not_realized` was CORRECT — it asserted the
  `NotImplementedError` this task retires — but its coverage was not replaced, and that is the half worth
  remembering: a justified deletion still owes a replacement. The rewritten empty-side fragment was
  checked for the vacuity task 10 had already hit once, and is clean: inverting the side-naming line
  fails both parametrizations.
  The sharpest finding: a BOLDED docstring guarantee that with one cluster per unit the two constructions
  agree on sizes. The reviewer swept n x frac and found 90 disagreements, including `n=2, frac=0.1` where
  the unclustered draw REFUSES and the clustered one returns 1/1 — a legality disagreement, not a rounding
  one. The claim was contradicted by another sentence in its own docstring and by
  `_assign_whole_clusters_by_ratio`'s "no bound is promised". A test was pinning that coincidence as
  `len(...) == 4`.
Task 11: fix round 1. Commit fb78340. All six closed. The false size-agreement claim was replaced with the
  verified negative — no size agreement is promised at any cluster size — and the assertion pinning the
  coincidence was dropped rather than weakened, keeping the membership INEQUALITY as the real check.
  `_stratum_groups`' message now branches on the declaration so a holdout reader is no longer sent to two
  `E-DATA-ASSIGN-*` codes and a `sweep.groups` path their declaration cannot take.
Task 11: complete. 1919 passed + 2 xfailed; ruff check and mypy clean. BASE for task 12 is fb78340.
Task 12: dispatched — `units.holdout_seed_for`, the derivation and its own digest suffix. FIRST TASK
  DISPATCHED UNDER THE AMENDED CHECK from task 11: I asked not only whether each prescribed mutation
  discriminates, but which of the task's deliverables NO mutation reaches. The brief prescribed two; two
  of the five tests were reached by neither. I added three — ignore the pin, drop the roster from the
  payload, and one the implementer was told to name itself for the fold-distinctness test — and told it
  to report rather than invent if no single-line mutation reached the last.
Task 12: implemented at 605f63c. 1924 passed + 2 xfailed. The implementer returned an honest NEGATIVE on
  mutation (e): no single-line mutation isolates the fold-distinctness test from the roster-mixing test,
  because any edit that collides `holdout_seed_for` with `_seed_from` necessarily also drops the roster
  term. It reported the coupling rather than claiming a clean proof, which is the behaviour the "name it
  yourself, and report if none exists" framing was for.
Task 12: reviewed (opus). **BOTH VERDICTS PASS** — the second of the slice, and the reviewer ran three
  mutations beyond the five. It independently confirmed the negative finding by constructing the narrower
  variant and watching the suite stay green, and ruled it a property of `_seed_from`'s roster-free payload
  rather than a weakness the implementer chose.
  Verified for the record: the pin gate is character-identical to `validate._check_holdout`'s
  `E-DATA-HOLDOUT-SEED` predicate across eight shapes; the digest consumed is the one task 4 strips
  `holdout.seed` from, so the derivation is not self-referential; the payload is distinct from all seven
  other digest-derived seeds in `src/`.
  One Important, closed by me directly rather than by a fix round — a single false docstring sentence,
  "one derivation shape for every drawn partition in the config". False: `_seed_from`'s fold payload is
  `f"{digest}|folds"` and carries no `units_hash` at all, which I confirmed by reading it. My first
  replacement asserted a REASON for the difference that I had not verified — that a partition reading the
  resolved roster mixes it in and one deriving boundaries without it does not — which is the same defect
  I was fixing, since a fold's boundaries do partition resolved units. Replaced with the checked fact
  alone and an explicit statement that only the resemblance to `assign_seed_for` is claimed. Gates green
  after: 1924 passed, ruff and mypy clean.
  Two Minors carried without action: the payload literal is pinned by no golden value, which matches
  every sibling and is the house standard; and the implementer used `git checkout --` on the clobbered
  `.gitignore`, which was safe here but is the move CLAUDE.md names by hand.
Task 12: complete. 1924 passed + 2 xfailed. BASE for task 13 is the commit below.
  For task 13's reviewer, from task 12's: `holdout_seed_for` has no production caller yet — task 13
  composes it — so confirm the digest it is passed is `design_digest(doc)` and not a neighbour.
Task 13: dispatched — `cli._resolved_holdout`, composing the seed derivation and the draw once in
  `command_run`. Pre-check found the brief's two mutations sound but reaching only one of three tests, so
  I added two: ignore the pin, and delete the `roster is None` guard — the second with an explicit
  instruction to report WHICH WAY it failed, since a guard deletion can fail a test by crashing rather
  than by the assertion seeing a wrong value.
  Also settled before dispatch that the two deliverables no test in this diff can reach — realized ONCE,
  and passed the run's own digest — are deferred BY DESIGN, not missing. The spec records tasks 13-17 as
  untestable end to end while the wholesale refusal stands, and task 18's brief already carries five
  enumerated end-to-end pins, one per wiring task. I verified task 13's pin is written there before
  dispatching rather than trusting the spec's promise of it.
Task 13: implemented at 6c328a6. 1927 passed + 2 xfailed. Both added mutations behaved as asked, and the
  implementer reported the distinction I asked for: (d) fails via a `TypeError` from `units_hash`
  iterating a `None` roster, not via the final assertion.
Task 13: reviewed (opus). **BOTH VERDICTS PASS** — the third of the slice, and the run of passes since
  the Global Constraints landed is now three of the last four.
  Task 12's open question is settled: `digest = design_digest(doc)` is the ONLY assignment in `cli.py`,
  and every occurrence between it and the holdout call is a pass, so no rebinding and no shadow.
  The siting question — the one deliverable NO test in this slice can catch, because a realization inside
  a condition loop would draw the same partition each time and be behaviourally invisible — was settled by
  READING, which is the only instrument available: the call sits at `command_run`'s own body indent, with
  no `for` or `while` at that level anywhere in the surrounding 500 lines.
  The gate agreement was checked at the stake that matters. `_resolved_holdout` matches `_check_holdout`'s
  gate character-for-character; the bare-truthiness sites disagree only on a truthy NON-DICT holdout,
  which cannot reach a run because `envelope.py` types the key as `dict`. So no shape is drawn-on by one
  gate and validated-as-absent by the other. That is a stronger answer than task 8's equivalent, and it
  needed to be, because this gate decides whether a split is drawn at all.
  One Important carried forward as an OBLIGATION rather than a fix: the docstring says present-tense that
  the runner's narrowing, the denominators and `allocation.json` "are all handed this one object", and at
  this commit `holdout_plan` has exactly one occurrence in `src/` — its own assignment. It is verbatim
  from the brief, the horizon is named in the code by `# noqa: F841 -- consumed starting task 14`, and it
  is true by task 17. **Task 17's reviewer must confirm all three named consumers exist.**
  One Minor closed by me directly: the `roster is None` guard claimed `_check_units` "has already reported
  why", describing a shape that cannot occur — `resolve_units` never returns `None`, so a `None` there
  means no `data.units` at all and no such diagnostic was emitted. Rewritten to say the argument is
  defensive rather than reachable, which is what it is. Gates green after.
  Ruling on the new format drift (M3): NOT fixed, consistent with the same ruling at task 7. The task's
  new lines sit in `ruff format --diff` hunks, but `tests/test_cli.py` already carried drift, so
  formatting it would bury a small wiring diff in an unrelated whole-file rewrite. The accumulation is
  real and is now an item for the WHOLE-BRANCH REVIEW, where the repo's broken format baseline can be
  decided once for the slice instead of argued per task.
Task 13: complete. 1927 passed + 2 xfailed; ruff check and mypy clean. BASE for task 14 is the commit below.
Task 14: dispatched — the runner narrowing: `io.units` is the test partition, `io.units.train` the training
  one, at EVERY scope. Pre-check added two mutations to the brief's three: one for the holdout-beside-fold
  seam (which no config can reach, so a direct-call test is its only instrument and it needed a mutation
  or the seam was only NAMED), and one the implementer was asked to name itself for the control.
Task 14: implemented at 8b3602a. 1933 passed + 2 xfailed. The implementer's own mutation (e) found the
  precise defect shape the design warns about: dropping `fold_members is None or` from the outer guard
  routes into the fold branch and yields `train=UnitList([])` — an EMPTY LIST where the contract requires a
  RAISE. Two mypy-driven conjuncts were added beyond the brief and both were flagged.
Task 14: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important and four Minor.
  The reviewer's answers to the four checks are the record worth keeping. (1) No fold regression: the
  holdout narrowing sits inside the FIRST branch, whose condition is scope-independent, while the
  `run`/`condition` -> `None` hole is a sibling `elif` reachable only when `fold_members is not None`,
  which the new assertion makes mutually exclusive with a holdout. (2) Both mypy conjuncts are benign and
  neither can silently skip the narrowing — the concern I raised was that a guard added for a type checker
  can convert a crash into a skipped narrowing, which is worse than the crash; it cannot here, because the
  only state it admits leaves no roster to execute over and `io.units` raises. (3) The control DOES
  distinguish raise-from-empty rather than merely asserting a failure. (4) My worry about mutation (d)
  failing for the wrong reason was MISPLACED, and the reviewer said so plainly: `pytest.raises(
  AssertionError)` passes only on an `AssertionError`, so a silent-precedence implementation fails the
  test whether it returns normally or raises a `ContractError`. Recorded because a controller's worry is a
  claim too, and this one did not survive checking.
Task 14: fix round 1. Commit f194d29. Both Importants were shapes CLAUDE.md names by hand: an assertion
  deletable with the whole suite green — the very guard that makes a holdout beside a cell structure a core
  defect rather than a silent precedence — and a test whose NAME claimed four scopes while exercising one.
  Both `pytest.raises` sites now carry `match=`, so each is pinned to its OWN assertion rather than to any
  `AssertionError` the call might raise, which was the residue of my misplaced worry being half right.
Task 14: complete. 1937 passed + 2 xfailed; ruff check and mypy clean. BASE for task 15 is the commit below.
Task 15: dispatched — the denominators, six sites narrowed and three deliberately not. The scoping names
  this the task most likely to ship wrong, and the brief under-specified it in exactly that direction:
  six sites, three deliberately-untouched, and only TWO tests. I checked what they reach — only
  `_condition_counts` was pinned — and then checked task 18's five end-to-end pins, which cover
  `n.resolved` and `max_failed_fraction` only. **Four of the six sites would have been unpinned even after
  task 18.** The dispatch required a per-site answer: a test that fails when that site alone is reverted,
  or a written statement that it is unpinnable naming which task-18 pin closes it. It also required the
  "surplus keys are inert" claim about the three key-indexed sites to be CHECKED rather than restated,
  because that is a claim like any other.
Task 15: implemented at fa85b26. 1942 passed + 2 xfailed. The per-site requirement paid for itself: three
  sites pinned with a mutation each, ONE genuinely unpinnable and deferred, and **two proven STRUCTURALLY
  INERT by construction** — `_condition_beside_n`, whose answer is a function of `arm_members_map is None`
  alone because it passes its own roster argument as both the input and the identity reference, and
  `_compute_vs_baseline`, because `resolve_contrasts` builds every auto-generated `Comparison` without
  `within`, so `units_matching(_, None)` is `None` whatever roster it holds. That second reason
  corroborates something I had verified independently before this slice began.
Task 15: reviewed (opus). Spec compliance PASS — exactly six sites and no seventh, verified by grepping
  every remaining `roster` in `command_run`; `provenance.units.n` and `units_hash` correctly whole-roster.
  Task quality FAIL with two Important and three Minor, and nothing shipping a wrong number.
  Both inertness claims CONFIRMED by construction, including running `_compute_vs_baseline` over a doc
  carrying a declared `within` — the arm that could have broken it. The reviewer declined a new
  spec-defects entry for site 5 on the grounds that the dependency runs in the SAFE direction: if `within`
  ever becomes settable, `eval_roster` is already the correct argument, so there is no failure mode to
  file. I accept that; a deferral needs a failure mode, not just a coupling.
  The finding worth carrying past this slice: **this task made a FILED remediation false.**
  `spec-defects.md`'s OPEN `technical_n` entry said the fix was cheap because `_cond_beside_n` "already
  takes the un-narrowed roster as its third argument and decides by identity" — and task 15 changed that
  argument to `eval_roster`. A filed gap is not inert: it makes claims about the code, and those claims
  go stale exactly like a docstring's. Nothing in this repo's process was checking them. That belongs in
  the whole-branch review.
  Also closed: a false docstring guarantee duplicated across `cli.py` and its test, disproved by running
  the brief's OWN mutation over the full suite; a test that passed with `_compute_vs_baseline` returning
  `None, []`; and an `assert` sited AFTER `execute_plan`, which is the shape that once cost this repo
  every execution in a run with the record lost — moved before the call.
Task 15: complete. 1942 passed + 2 xfailed; ruff check and mypy clean. BASE for task 16 is 2545dda.
Task 16: dispatched — `W-STATS-RESAMPLE-CLUSTERS` against the test partition. This is the one task in the
  slice that fixes a defect the SCOPING found rather than building new surface: the check read `fold_basis`
  over the whole roster while the draw ran over the test partition, under-warning by ~1/frac and failing in
  the direction of NOT FIRING, which is the worse direction because nobody sees a missing warning.
  Pre-check added a third mutation: the brief's two reach the two positive tests, and the CONTROL — the one
  asserting the stratum-constancy check must NOT narrow — was reached by neither, so the boundary was only
  named. The dispatch asked for an honest negative if narrowing changed nothing observable.
Task 16: implemented at 30f18b2 / cfd5672. 1945 passed + 2 xfailed. Measured under-warning: 50 clusters,
  `min_clusters: 20`, `frac: 0.2` — the old check read 50 and stayed silent, the new one reads ~10 and
  fires. Roughly 5x, matching the estimate.
  The implementer returned the honest negative on mutation (c) AND investigated why: the control's fixture
  varied on EVERY cluster, not only training-side ones as its docstring claimed. It fixed the docstring
  rather than the fixture — correct on the evidence it had, and I flagged to the reviewer that a
  discriminating fixture looked constructible.
Task 16: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important and four Minor.
  The reviewer did not argue the boundary question — it BUILT the fixture. At `seed: 1234` the test
  partition is exactly `{a2, a6, a12, a13}` and `a0` lands training-side, and the label column does not
  participate in the draw, so varying only `a0` is deterministic rather than lucky. That fixture passes on
  HEAD and fails under the narrowing mutation, while the shipped control passes under it.
  Ruling: the honest negative was the right call on the evidence available and is superseded by a
  CONSTRUCTION, not by an argument. That distinction is the one worth keeping — "no mutation reaches this"
  and "no mutation can reach this" are different claims, and only the second justifies leaving a boundary
  unpinned. The reviewer was asked for exactly that disjunction and answered it with evidence.
  Second Important: the warning still read "puts this ROSTER in 10 clusters" while the 10 counted a test
  partition of a 50-cluster roster. The count could not regress invisibly, since the printed value is the
  compared variable — but the noun was wrong and nothing pinned it. Now conditional, and pinned by an
  assertion that checks "roster" is ABSENT from the holdout-case message, which is the discriminating form
  rather than the vacuous one this slice hit at task 10.
Task 16: fix round 1. Commit 579e524. All five closed. `_holdout_test_roster`'s "**Never raises**" narrowed
  to a claim tied to its actual `except` tuple; § Errors' row now records the fallback to the whole roster
  when a declared draw cannot be performed, which the row had stated unconditionally.
Task 16: complete. 1945 passed + 2 xfailed; ruff check and mypy clean. BASE for task 17 is 579e524.
Task 17: dispatched — `allocation.json` gains its fourth key. Carried task 13's OBLIGATION explicitly:
  its `_resolved_holdout` docstring claims present-tense that three consumers "are all handed this one
  object", and that claim was false when written and becomes true only here. Pre-check added a fourth
  mutation for the middle arm of a three-way distinction — drawn+stratified, drawn+unstratified, read —
  which the brief's three did not reach.
Task 17: implemented at 5eaaddb. 1950 passed + 2 xfailed.
  Real disagreement, and the right resolution: the brief's literal code produces key order
  `seed, arms, strata, holdout`, while `reference.md` § `allocation.json`'s printed example — settled by
  task 2 — orders them `seed, arms, holdout, strata`. The implementer followed the DOCUMENT and verified
  the output matches key-for-key. That is the repo's rule working as intended, from the direction that
  matters: the plan argues from the spec, and where they disagree the document leads.
Task 17: reviewed (opus). Spec compliance PASS; task quality FAIL with two Important, both one-paragraph
  docstring fixes, plus two Minor.
  Task 13's obligation is DISCHARGED and independently verified: all three consumers read the single
  `holdout_plan`, with no second derivation anywhere. The runner's is a key-projection into a `UnitList`
  rather than the plan object, which the reviewer checked is a projection and not a second draw.
  On the key order: confirmed the document's example, and confirmed the order is PURELY COSMETIC because
  `allocation_hash` canonicalizes with `sort_keys=True`. Recording that because it changes what the
  disagreement cost — following the brief would have produced a reader-facing mismatch with a printed
  example, not a hash divergence.
  Both Importants closed by me directly rather than by a fix round. `build_allocation_document`'s
  docstring still said it returns `None` when `group_axes` is empty — false as of this commit, and it
  CITED the very sentence that falsifies it, three paragraphs above the guard this task widened.
  `allocation_hash`'s docstring enumerated the written insertion order as `seed, arms, strata`; rather
  than correct the count to four, I replaced the enumeration with a pointer to what builds it and what
  § `allocation.json` prints — the form that does not go stale again, and the same move tasks 9 and 10
  made for two other enumerations in this slice. Gates green after: artifacts tests pass, ruff and mypy
  clean.
  Minor carried, not fixed: dropping `holdout_plan` from the `build_allocation_document` call leaves all
  1950 tests green. That is OWNED — task 18's fifth end-to-end pin names it verbatim, and no config can
  reach `command_run` today.
Task 17: complete. 1950 passed + 2 xfailed. BASE for task 18 is the commit below.
Task 18: dispatched — retire `E-DATA-HOLDOUT-UNSUPPORTED`, and the five end-to-end pins. The slice's pivot.
  I counted the assertions to be removed before dispatching — 28 in `tests/test_validate.py` — and made the
  central requirement not the deletion but the RE-VERIFICATION after it. Every task from 5 onward asserted
  its finding alongside a code emitted by `_check_unimplemented`, a DIFFERENT function, so the companion
  was never positive attribution for anything. Delete it and any test left asserting only absences becomes
  a test that passes identically if nothing ran.
Task 18: implemented at 30376a1 / 7b0cd14. 1953 passed + 2 xfailed. **FOUR TESTS HAD GONE VACUOUS AND WERE
  REWRITTEN.** That is the whole return on the "assert alongside" discipline: the deletions were one-line
  as designed, and the four that needed more were found by looking rather than by the suite, which stayed
  green throughout.
  Two strong disagreements. `executions.jsonl` carries no `n` key at all, so the brief's pin was written
  against a field that does not exist. And the brief's `_ALWAYS_FAILING_STEP` — a bare `raise` — CANNOT
  TRIP `max_failed_fraction` at any denominator, because `_units_failed_anywhere` counts only recording
  steps and a step that never produces a row never records. The brief's own pin for task 15's second
  property could not have fired. Replaced with a step that discriminates narrowed from un-narrowed.
Task 18: reviewed (opus). Spec compliance PASS — retirement complete, only `E-DATA-RESOLVER-UNSUPPORTED`
  and `E-STATS-NULLTEST-UNSUPPORTED` survive, all five repeat kinds still rejected by probe. Task quality
  FAIL with five commentary/pin defects.
  The reviewer re-verified the re-verification rather than trusting it, killing `_check_holdout` and
  watching 37 tests fail, and confirmed every non-rewritten sample rests on `E-DATA-HOLDOUT-SEED` — a code
  only that function emits. The four rewrites are genuine.
  Two pins were pinning nothing. Pin 1's seed clause asserted the DECLARED `4321`, so replacing the digest
  with a constant left all 1953 tests green; it now uses a config with no declared seed and recomputes
  `holdout_seed_for` from the run's own recorded digest, and the mutation drives it. And the regression
  assertion sat on `holdout: null` — a shape the retired refusal NEVER FIRED ON, so it could not have
  failed even before the retirement.
  Ruling on I1/M1, which is the lesson of this task: the implementer's sweep was scoped to the STRING
  `E-DATA-HOLDOUT-UNSUPPORTED` rather than to the CLAIM, so a docstring citing the deleted
  `_check_unimplemented` loop survived at two sites. CLAUDE.md's rule is sweep for the claim, not the file;
  this is the same failure one level in — sweep for the claim, not the SYMBOL. Re-sweeping for the claim
  found a third instance in `reference.md` that the string sweep could never have reached.
Task 18: fix round 1. Commit b034923. All eight closed. The one worth naming: the task-14 pin read
  `next(rglob("split.json"))` — 1 of 5 files — and now asserts all five are IDENTICAL. That is the first
  behavioural instrument this slice has had for task 13's "realized once", which was otherwise invisible
  because a realization inside a per-condition loop draws the same partition each time. Reading the call
  site had been the only instrument for six tasks.
Task 18: complete. 1954 passed + 2 xfailed; ruff check and mypy clean. BASE for task 19 is b034923.

# SDD ledger — plan: docs/superpowers/plans/2026-08-15-resample-honoured.md

Slice H4a — `statistics.resample` honoured. Branch `h4a-resample-honoured`, forked from `eaf3605`
(main, post-H7a). Baseline at fork: 1689 passed + 2 xfailed; ruff check and mypy clean.
Spec: docs/superpowers/specs/2026-08-15-resample-honoured-design.md
Measurement: docs/superpowers/H4a-SCOPING.md (dated 2026-08-15 against eaf3605)
Execution mode: subagent-driven. User chose the variant WITHOUT standing merge/push authorization —
  STOP AND ASK before merging to main or pushing.

## Pre-flight scan

Shared-surface pairs (one row per shared file or interface):

| Tasks | Shared | Finding |
|---|---|---|
| 4 -> 5,6,7,8,10 | `validate._check_resample` | Task 4 CREATES it and fixes its call site; 5/6/7 extend the same function; 8 and 10 add sibling checks. Signature is named in task 4's Produces (`_check_resample(doc, roster, c) -> None`). Sequential, no conflict — but every later brief must state the function already exists so none re-creates it |
| 2,4,5,6,7,8,10,12,17 | `docs/reference.md` | Nine tasks insert rows into § Errors / § Validation. Each insertion MOVES rows. Global Constraints carry the count-phrase rule; no brief locates a row by position (checked) |
| 8,9,10,11,14,15 | `src/publishable/stats.py` | 8 and 11 are docstring-only; 9 builds the stratified path; 10 extends it to clusters; 14/15 wire `summarize_step`. Sequential |
| 13,14,15,16,17 | `src/publishable/cli.py` | 13 creates `_resolved_resample` and `resample_spec`; 14-17 consume it. Named in 13's Produces |
| 1 -> 15,16 | `tests/test_cli.py` `_CONDITION_SCALED_STEP` | Task 1 introduces the condition-scaled starter step and a `_starter_step` parameter; 15 and 16 reuse it. Named in task 1's own text. **This is the fixture that makes 16's assertions able to fail at all** |
| 6,11,19 | `docs/superpowers/spec-defects.md` | Three separate appends, no shared entry. Note the file is GITIGNORED, so anything recorded only there does not survive the merge — 6 and 11 both also write to a tracked file |
| 3 -> 4 | `envelope.LEAF_TYPES` | 3 adds the three leaf entries; 4's checks assume them. Named in 4's Consumes |

Self-consistency, per task: checked each task's tests against the code it specifies and the files it
creates against the files later tasks touch. **One conflict found**, ruled below. Tasks 1-19 otherwise
agree with themselves.

Ruling (pre-flight, tasks 2 x 12): TASK 2 MUST KEEP THE `NOT BUILT;` MARKER; TASK 12 REMOVES IT.
  As written, task 2 step 3(b) says "delete `NOT BUILT;` from this line only" while task 12 is the task
  that actually retires `E-STATS-RESAMPLE-UNSUPPORTED`. That opens a TEN-TASK WINDOW (2 through 11) in
  which `reference.md` § The one config file states `statistics.resample` is built while `validate`
  still refuses every config that declares it — a false build fact in a normative document, which is
  the exact class H7a spent a whole slice removing and which `CLAUDE.md`'s feasibility procedure step
  10 exists to prevent.
  The distinction that resolves it: the ENUM TABLE task 2 mints is a SPEC claim, legitimately present
  tense, and lands in task 2 as planned. The `NOT BUILT` marker is a BUILD FACT and is still true until
  task 12. So task 2 writes `resample: null   # NOT BUILT; bootstrap` — marker preserved, enum comment
  in the `# a | b | c` form CLAUDE.md requires — and task 12 drops `NOT BUILT; ` leaving `# bootstrap`.
  Task 12's own step 3(b) already says "Task 2 already removed `NOT BUILT;`"; that sentence is now
  wrong and task 12's brief must be corrected when it is dispatched.
  Cost if wrong: one clause moves between two tasks in the same slice.

## Task log

Task 1: implemented, commit 0f62ba0 (tests only, +154 lines). 1691 passed + 2 xfailed (baseline 1689);
  ruff and mypy clean. Implementer ran both required mutations — the literal 2000 -> 500, and
  t_over_units -> percentile_over_units in summarize_step — and reports both new tests failing on the
  predicted assertion, reverted in place. No disagreement found between brief and code.
  BASE for task 2 is 0f62ba0.
Task 1 review dispatched (opus). Asked it to go BEYOND the report and name what a plausible task-13 bug
  would NOT catch — specifically whether the two tests genuinely distinguish the absent-key document
  from the explicit-null one, which is the whole reason they are two tests rather than one parametrized
  case. Also asked whether the pin protects CLAUDE.md § The worked example's NUMBERS or only their
  SHAPE — the file says those intervals were checked numerically and must not be narrowed back.
Task 1 review: spec ✅, quality FINDINGS — 2 Important. Structural half CONFIRMED GOOD: the reviewer
  simulated the .get("resample", DEFAULT) hazard IN BOTH DIRECTIONS and the two-document split genuinely
  catches it (absent-key fails, explicit-null passes; the mirror bug `"resample" in stats` fails the
  other). That split was the task's whole point and it works.
  IMPORTANT 1 — THE FIXTURE'S NUMBERS AGREED WITH THE BUG. Scales {pearson: 1.0, spearman: 2.0} make the
  per-unit difference IDENTICAL TO THE BASELINE COLUMN'S VALUE, so four distinct quantities are all 19.5
  and the contrast ci95 is byte-identical to the column's. Two mutations passed green: dropping the
  subtraction from the delta computation entirely, and shifting the derived seed by +1 (ci95 moves
  [16.025,23.025] -> [15.825,22.925]). The pin asserted `ci95 is not None` and nothing numeric anywhere.
  THE REVIEWER CHECKED ALL FOUR REMEDIATION COMBINATIONS, which is what makes this finding usable rather
  than merely correct: scale-fix ALONE stays green (cohens_dz is scale-invariant); delta-assertion ALONE
  at scale 2.0 stays green (both deltas 19.5); only scale 1.0/3.0 PLUS a numeric delta assertion bites
  (39.0 correct vs 19.5 buggy). Tasks 15 and 16 INHERIT this fixture.
  IMPORTANT 2 — correction levels order-blind: `sorted(...) == [0.025, 0.05]` pins that both levels occur
  and never which member gets which, which is precisely the Holm ranking swap this slice could cause.
CALIBRATION RECORDED: the implementer reported "Concerns: None" on the grounds that the brief named
  exactly two load-bearing mutations. Running the brief's mutations is NECESSARY, NOT SUFFICIENT — the
  question a pin must answer is "what would slip past this?", which a brief cannot enumerate in advance.
  The report also claimed no assertion was "a tautology against a degenerate fixture" while the whole
  fixture was degenerate in exactly that way. Fix round told this as process, not blame.
Ruling: the reviewer's observation that CLAUDE.md § The worked example's INTERVALS are unowned by any
  task is NOT a gap this slice must close. Nothing in the suite computes r = 0.581 — those numbers are
  documentation of a synthetic 228-unit table, not values any test derives, so no code change can
  "narrow them back". They can only be narrowed by someone EDITING THE DOCS, which is the cross-document
  consistency pass's job rather than a test's. Recorded so the whole-branch review does not re-open it.
Task 1: COMPLETE (commits 0f62ba0, a80e50d). 1691 passed + 2 xfailed; ruff and mypy clean.
  CONTROLLER-VERIFIED the decisive fix independently: dropping the subtraction from the delta
  computation in cli.py now FAILS BOTH PINS (it passed green before the fix); reverted in place and
  both pass again. Scale moved {pearson:1, spearman:2, kendall:3} -> {1, 3, 5} so the paired delta
  (39.0) no longer collides with the baseline column's own value (19.5), and presence-only checks
  became numeric pytest.approx assertions on value/delta/ci95. Correction levels now pinned PER MEMBER
  rather than sorted. Two Minors taken, one skipped with reasoning (degenerate repeat_spread, flagged
  forward to tasks 15/16 which inherit the fixture). The implementer retracted its own earlier
  "Concerns: None" overclaim in the report.
  BASE for task 2 is a80e50d.
Task 2: dispatched, carrying the pre-flight ruling — KEEP `NOT BUILT;` on the resample line.
Task 2: COMPLETE (commit d5a3a19). 1691 passed + 2 xfailed; ruff, mypy and the mechanical pass all
  controller-verified clean (0 whitespace/tab/column issues over reference.md). The NOT BUILT ruling
  landed as instructed: `# NOT BUILT; bootstrap` plus the expansion line, so the enum comment satisfies
  CLAUDE.md's rule while the build fact stays true until task 12.
  THE IMPLEMENTER CAUGHT A FALSE GUARANTEE IN MY OWN BRIEF. My dispatch said the closed enum "makes
  `method: bootstap` a diagnostic (E-STATS-RESAMPLE-METHOD, minted in task 4) rather than a shrug" —
  and it correctly refused to write that into reference.md, because that code does not exist until task
  4 and the sentence would have claimed a guarantee the build does not provide. It rewrote to "a
  refusal the schema can name", which is true of a closed vocabulary today. GENERALIZES: a brief's
  RATIONALE is written from the finished slice's point of view, and prose lifted from it into a
  normative document inherits a future tense the document cannot carry.
  Implementer flagged two follow-ups task 12 now owns: drop `NOT BUILT; ` from the resample line, AND
  add the E-STATS-RESAMPLE-METHOD reference to the new paragraph once task 4 registers it. The second
  is new — my pre-flight ruling named only the first.
Ruling: NO SEPARATE REVIEWER SEAT FOR TASK 2; folded into the whole-branch review, same as H7a's
  tasks 12/13. Grounds: the diff is one table, one paragraph and one comment line, docs-only, and I read
  every line and ran the mechanical pass myself. A fresh reviewer's marginal value here is near zero
  against a full seat. NOT a precedent for any task touching src/.
Task 3: implemented, commit 3c8c941 (+61/-3, envelope.py and test_envelope.py). 1694 passed + 2 xfailed
  (baseline 1691 + 3 new); ruff and mypy clean. The corrected precedent held: three LEAF_TYPES entries
  alone, NO closed key set, with data.units.measurements as the model — the implementer verified the
  container-before-leaf ordering in _check_unknown_keys EMPIRICALLY before relying on it, which is what
  the brief asked and what the earlier spec draft (`assign.<axis>` style, plus a closed key set) would
  have got wrong. `stratify_by` typed `(str, list)` so a bare `stratify_by: site` and a list are both
  legal, matching units.stratum_names, the single authority the draw balances on.
  BASE for task 4 is 3c8c941.
Task 3 review dispatched (opus — a 23-line src diff, but it is THE SCHEMA GATE FOR TASKS 4-8 and the
  dual leaf-and-container role of `statistics.resample` is subtle and precedented only by
  `measurements`; a wrong mechanism here is inherited by five later tasks). Asked it to verify the dual
  role BY BEHAVIOUR — that a non-dict resample is still type-refused, that `resample: null` and an
  ABSENT key both stay clean (task 1's pin rests on those being different documents that resolve alike),
  and that a wrong-typed stratify_by is still caught somewhere rather than passed silently to task 5.
Task 3 review: spec ✅, quality FINDINGS — 2 Important, 2 Minor. Mechanism confirmed BY BEHAVIOUR
  (non-dict resample still one E-CONFIG-TYPE; typo yields E-CONFIG-KEY-UNKNOWN with the hint;
  `resample: null` and absent both clean; bare-string stratify_by accepted, `stratify_by: 3` caught),
  and the reviewer re-ran the mutations rather than trusting the report.
  IMPORTANT 1 IS THE HIGHEST-VALUE FINDING OF THE SLICE SO FAR: A DOCSTRING THAT INSTRUCTS THE NEXT
  TASK TO BUILD A CRASH. test_the_three_resample_leaves_are_typed's docstring claimed the E-CONFIG-TYPE
  backstop "lets `_check_resample` read each value without its own isinstance ladder". False —
  validate.py:449-456 makes leaf type faults DELIBERATELY NON-FATAL, so validation continues and task
  4's check would run against `n: "many"`, where `n >= 80` raises TypeError and takes out the whole
  validate call. The house pattern is the OPPOSITE: quiet isinstance/continue guards at four sites, each
  carrying that reason in its own comment. Task 4's implementer reads this docstring and would have
  taken it literally.
  GENERALIZES, and it is new: THE "COMMENT CLAIMING A GUARANTEE THE CODE DOES NOT PROVIDE" CLASS HAS A
  WORSE VARIANT — a comment that claims a guarantee AND IS READ AS AN INSTRUCTION BY A LATER TASK. The
  damage is not a misleading reader; it is a defect built on purpose, downstream, by someone doing what
  they were told. Docstrings on a schema gate are interface documentation for the tasks that consume it.
  IMPORTANT 2: the new block comment says "the block is no longer refused wholesale" — not true until
  task 12 — and it CONTRADICTS the `holdout` clause a few lines above ("stays whole for now… gap is
  latent"), so a reader cannot reconcile the two. Same class as the task 2 NOT BUILT ruling: prose
  written from the finished slice's point of view, landing in a file that is read mid-slice. The true
  justification is validate-before-honour and it stays true both before and after task 12.
Task 3: COMPLETE (commits 3c8c941, d9bed97). 1694 passed + 2 xfailed; ruff and mypy clean. Both
  Importants and both Minors closed; the difflib hint is now actually asserted rather than merely
  claimed. BASE for task 4 is d9bed97.
Task 4: dispatched, CARRYING THE ISINSTANCE-GUARD REQUIREMENT task 3's review surfaced — leaf type
  faults are non-fatal, so _check_resample must guard every value it reads or `n >= 80` raises
  TypeError on `n: "many"` and takes out the whole validate call.
Task 4: implemented, commits 60e7aab + 28c257e. 1702 passed + 2 xfailed (baseline 1694 + 8 new); ruff
  and mypy clean. The isinstance-guard requirement landed, and the implementer found the brief's own
  `method` check double-reported a wrong-typed value under BOTH E-CONFIG-TYPE and
  E-STATS-RESAMPLE-METHOD — inconsistent with the `n` branch's own stated reasoning two lines below it.
  It also rewrote two docstring sentences the brief supplied that claimed resample is "honored" (false
  until task 12) and that the function only "reads values" (false once guards were added). Third task
  running, third false-guarantee caught before commit.
CARRY FORWARD TO TASKS 5 AND 8 — CONTROLLER-VERIFIED. The brief's `_RESAMPLE_UNITS` fixture is
  `{"from": "index.csv", "key": "patient_id", "attributes": ["cohort"]}`, but the test harness writes
  index.csv as `patient_id\np1\n` — ONE COLUMN, no `cohort`. So roster resolution FAILS and `roster` is
  None in every test using that fixture. Harmless for task 4, whose checks read declarations only.
  FATAL FOR TASKS 5 AND 8, whose checks need a resolved roster: every test would take the
  `roster is None` early path, the check would never fire, and the test would pass by asserting the
  absence of a finding THAT COULD NEVER HAVE APPEARED. A check that cannot fail, pre-installed in the
  plan. Both dispatches must fix the fixture — add the column to index.csv or drop the attribute — and
  must PROVE the roster resolved rather than assuming it.
Task 4 review: spec ✅, quality FINDINGS — 1 Important, 5 Minor. Both halves of the implementer's
  mid-flight correction independently confirmed (the double-report was real; the original test WAS
  vacuous, proved from git show). Floor verified on both sides — 80 accepted, 79 refused, and the
  `n <= floor` off-by-one fails a test. Guards complete. Cross-document sweep clean: no example anywhere
  declares n below 80, so no dated build claim is contradicted.
Ruling: I CORRECTED SPEC DECISION 5 MYSELF — the false rationale was mine, not the implementer's.
  I wrote that _check_resample sits after _check_sweep because "its strata check needs the resolved
  roster and declared attributes; its `n` bound needs the resolved comparison family, which
  _check_sweep computes." BOTH HALVES ARE FALSE. `roster` comes from _check_units and is already handed
  to _check_fold_stratify_by THREE CALLS EARLIER, so roster availability does not discriminate this
  position at all; and _check_sweep RETURNS None and stores nothing on `doc`, so the comparison family
  is NEVER HANDED OVER — task 6 must recompute it locally, which is position-independent. The placement
  is right; only the reason was wrong. Spec row rewritten to say what the position actually buys
  (grouping with the other statistics.* checks, sensible finding order) and to state the recomputation
  requirement explicitly.
  THIS IS THE SECOND TIME IN FOUR TASKS THAT A JUSTIFICATION READ BY DOWNSTREAM TASKS WAS FALSE, and
  both times the damage was the same: an interface comment that four later tasks read as instruction.
  Task 3's told the next task to omit a guard; this one tells task 6 the family is in hand. TASK 6'S
  DISPATCH MUST CARRY: recompute the comparison family locally, it is not passed to you.
Task 4: COMPLETE (commits 60e7aab, 28c257e, 5a61576). 1704 passed + 2 xfailed; ruff and mypy clean.
  All six review items closed. BASE for task 5 is 5a61576.
  WORTH RECORDING — THE POSITIVE-COMPANION TRAP HAS A SECOND LAYER. The implementer's first attempt at
  fixing the absence-only floor test paired it with `assert "E-STATS-RESAMPLE-UNSUPPORTED" in found`,
  copying the two wrong-type tests in the same block. THAT PAIRING WAS ITSELF VACUOUS: that code fires
  from _check_unimplemented, INDEPENDENTLY of _check_resample, so the "positive companion" would still
  pass with the whole call site deleted. It caught this by TESTING the fix rather than assuming it, and
  paired the n:80 acceptance with the n:79 refusal instead — a companion that exercises the SAME
  function. GENERALIZES: a positive companion must be produced BY THE CODE UNDER TEST; a finding that
  merely co-occurs proves only that validation ran at all.
Task 5: implemented, commit 1253763. 1710 passed + 2 xfailed (baseline 1704 + 6 new); ruff and mypy
  clean. E-STATS-RESAMPLE-STRATIFY-UNKNOWN minted and registered; the fixture fixed and a new
  _resample_stratum_table helper added for tests that need a genuinely resolved roster.
MY DISPATCH'S STATED MECHANISM WAS WRONG AND THE IMPLEMENTER CORRECTED IT — CONTROLLER-VERIFIED.
  I wrote that with `roster is None` the check "takes the early-return path, never fires, and every test
  passes by asserting the absence of a finding that could never have appeared". FALSE:
  _check_resample takes `roster` as a parameter but NEVER READS IT (grep-confirmed), and is called
  unconditionally — task 5's check compares against `data.units.attributes`, a DECLARATION, not the
  roster. The fixture fix was still necessary, but for two different reasons the implementer states
  correctly: a stray E-UNITS-ATTR-MISSING on every resample config, and a trap left armed for tasks 6-8.
  GENERALIZES: I inherited "needs the resolved roster" from the scoping and the spec and repeated it
  three times without checking which check actually reads it. THE ROSTER CONSUMER IN THIS SLICE IS TASK
  8 (min_clusters), NOT TASK 5 — task 8's dispatch must carry that, and it is the task where a
  roster-is-None fixture WOULD be fatal.
  Second disagreement, also real: the brief's suggested error message listed the declared-attribute set
  while its own test asserted `"cohort" not in named` — the brief contradicted itself. Resolved by
  dropping the clause, matching _check_report_by's shorter shape.
Task 5 review: spec ✅, quality FINDINGS — 3 Important, 5 Minor. Reviewer independently CLEARED several
  things in the implementer's favour: the fixture change weakens no task-3/4 test (all 11 uses assert
  code membership only) and STRICTLY HELPS TASK 8, since _from_table previously raised and left
  roster=None for every one of them; matching _check_report_by rather than _check_assign was right.
  IMPORTANT 1 — THE TASK'S DEFINING GUARANTEE IS A CHECK THAT CANNOT FAIL, in its purest form. Swapping
  `declared` from the data.units.attributes DECLARATION to the roster's REALIZED attribute keys leaves
  all six new tests AND the whole suite green. Every stratify fixture makes the declared set and the CSV
  columns IDENTICAL, so no assertion can tell the two readings apart — while the brief and the § Errors
  row both promise "data.units.attributes, NOT the source's columns". The code is right (probed: an
  undeclared-but-real column IS refused); only the pin is missing. Fix requires a fixture where the two
  sets genuinely DIFFER. This is the same shape as task 1's (a fixture in which correct and buggy
  produce the same observable) and the third instance in five tasks.
  IMPORTANT 2: _resample_stratum_table's docstring ships THE MECHANISM THE IMPLEMENTER ITSELF REFUTED —
  the roster story I got wrong, restated in the helper that tasks 6-8 inherit. Also omits that it writes
  ONE unit row, insufficient for task 8's cluster counts.
  IMPORTANT 3: a comment attributes E-DATA-ASSIGN-STRATIFY-UNKNOWN to units._stratum_groups, which
  raises a bare NotImplementedError — its docstring exists partly to explain why it is NOT coded.
  Inherited from the brief.
Ruling on Minor 1: RESTORE the candidate list and FIX THE TEST, not the message. Both closest siblings
  enumerate the declared set, and a `cohot` typo currently gets no candidates. The brief's test was the
  wrong half — it asserted a declared attribute is ABSENT from the message, which enumerating violates.
Task 5: COMPLETE (commits 1253763, 92ad457). 1711 passed + 2 xfailed; ruff and mypy clean. All 3
  Importants and all 5 Minors closed. BASE for task 6 is 92ad457.
  THE IMPLEMENTER CORRECTED THE REVIEWER, AND WAS RIGHT. The reviewer's Important 1 proposed proving the
  declared-vs-realized distinction by swapping `declared` to the roster's Unit.attributes. That swap is a
  MATHEMATICAL NO-OP — units._from_table builds Unit.attributes from exactly data.units.attributes' own
  list, so the two readings are identical whenever the roster resolves, and no fixture could ever
  distinguish them. The real risk is reading THE SOURCE'S RAW COLUMNS. It built the discriminating
  fixture (a CSV carrying an extra real-but-undeclared column) and proved it by temporarily rewiring
  `declared` to the CSV header. GENERALIZES: a reviewer's proposed mutation can itself be
  non-discriminating — before trusting "this mutation would prove X", check the two branches can
  actually differ.
Task 6: dispatched. Carries (a) RECOMPUTE THE COMPARISON FAMILY LOCALLY — _check_sweep returns None and
  hands nothing over, per the corrected spec decision 5; (b) _resample_stratum_table writes ONE unit row.
Task 6: implemented, commit 5c744bd. 1717 passed + 2 xfailed (baseline 1711 + 6 new); ruff and mypy
  clean. W-STATS-RESAMPLE-FAMILY added; the family re-derived LOCALLY via expand(doc)/resolve_contrasts
  behind the same try/except three sibling checks use — the corrected mechanism, never assumed handed
  down. Sixth implementer, sixth real disagreement found: the brief attributed `interval_at` to
  correction.interval_at when it lives in stats.py and is only CALLED from correction.py.
CONTROLLER CONCERN TO RESOLVE AT REVIEW — THE RESIDUE MAY BE RECORDED NOWHERE. Task 6 filed the
  un-buildable comparisons x metrics bound in docs/superpowers/spec-defects.md, which is GITIGNORED.
  CLAUDE.md's own words: "a decision recorded only there is recorded nowhere." The residue is a real
  spec gap a reader of the four documents should be able to find — a config with many metrics can still
  null every ci95_corrected with only the run-time W-STATS-CORRECTED-THIN to show for it. I asked the
  implementer to say if it belonged somewhere durable and it did not raise it. Ruling deferred to the
  review, which is asked to assess it.
Task 6 review: spec ✅, quality APPROVED WITH FINDINGS — 2 Important, 5 Minor. The correctness property
  was PROVED, not assumed: min_honest_draws is monotone and metrics >= 1, so ALPHA/comparisons >=
  ALPHA/m and the shipped bound is provably <= the real requirement, equality at one metric. Reviewer
  ran two mutations of its own beyond the brief's.
  IMPORTANT 1: the comment names THREE precedents for the expand(doc) guard; there are TWO —
  _check_hypotheses never calls expand, it goes via _condition_labels whose guard returns None, a
  different shape. Inherited verbatim from my brief, in a comment I myself designated as interface
  documentation for tasks 7-8. THIRD wrong instruction this slice has put in that exact position.
  IMPORTANT 2: reference.md's "Six things deliberately absent from that table" still says a corrected
  interval's draw floor is reported only once a run has executions — the new § Validation row is now its
  VALIDATE-TIME COUNTERPART, and the reporting-stratum half of the same sentence already carries the
  "distinct from the row above" clause for exactly this reason.
RESIDUE RULING — I ADOPTED THE REVIEWER'S ANSWER OVER MY OWN QUESTION. I asked whether the residue
  needed moving out of the gitignored spec-defects.md. Better answer: MOVE NOTHING, BUT WRITE THE RULE
  THAT IS MISSING. The DECISION already has a durable home — the new warnings row admits the lower bound
  and why. What is absent from all four documents is the ACTIONABLE, PRESENT-TENSE SIZING RULE: a
  corrected interval at α/m needs min_honest_draws(1 − α/m) ≈ 80m draws off the same pool, so size
  resample.n against comparisons × metrics rather than against the 80-draw floor. Home: § Statistical
  reporting beside the correction-level table — NOT beside W-STATS-CORRECTED-THIN, because a sizing rule
  found only in a warnings table is found AFTER THE RUN IS SPENT. Legitimate to write now: it is a spec
  claim in the present tense, independent of the refusal still standing until task 12.
  Reviewer also found the residue OMITS A SECOND FAMILY — hypotheses.py corrects the same pools at α/H
  and is not safely boundable either, since the declared hypothesis count is an upper bound.
Task 6: COMPLETE (commits 5c744bd, 8a973f1). 1719 passed + 2 xfailed. Both Importants and all 5 Minors
  closed. The reviewer's residue ruling was adopted: the SIZING RULE (size resample.n against
  comparisons × metrics, ~80m draws) now lives in § Statistical reporting beside the correction-level
  table. The fix also made an ABSENT `n` check against cli.py's real 2000-draw default rather than being
  silently skipped — a gap neither the brief nor I had seen.
INFRASTRUCTURE, at the user's direction (commits 6c529c7, 4547bed): THE DEVELOPMENT RECORD IS NOW
  TRACKED IN GIT. 217 files / 66.6k lines — docs/superpowers/{specs,plans,*-SCOPING.md,spec-defects.md}
  and .superpowers/sdd/*/{progress.md,task-N-report.md,task-N-review.md}. Still ignored: task briefs
  (extracted from the plan by scripts/task-brief) and every .diff (regenerable from the two commits in
  its filename).
  CLAUDE.md gained § The development record and lost the two claims tracking made false — "docs/
  superpowers/ is gitignored and a decision recorded only there is recorded nowhere" and "slice ledgers
  ... are gitignored". THOSE SENTENCES WERE THE REASON CLAUDE.md KEPT DUPLICATING RULINGS; it can cite
  now. Also pinned: the consistency passes govern the four documents, CLAUDE.md and the feasibility
  analyses ONLY — a spec records what was decided when written and a scoping what was measured on its
  date, so corrections are APPENDED, never retro-edited. spec-defects.md is the exception, a live list.
  Consequence for sweeps: `*.md` no longer means the four documents, so a sweep must NAME them.
Task 7: dispatched. BASE 4547bed.

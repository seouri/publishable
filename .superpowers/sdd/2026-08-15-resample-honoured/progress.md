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
Task 7: implemented, commits d280f86 + 01b2b97 (report, now a tracked artifact). 1721 passed + 2
  xfailed; ruff and mypy clean. E-STATS-RESAMPLE-UNITS minted.
  THE JUDGMENT CALL I LEFT OPEN WAS DECIDED WELL AND PROVED BY MUTATION. I told it a config can declare
  data.units and still fail to resolve a roster — different faults, different remedies — and required a
  deliberate choice plus a test distinguishing them. It gated on the DECLARATION (`units_declared`),
  not on `roster is None`, and proved the distinction by mutating one into the other: the
  unresolvable-roster test then FAILED with a double fault (because _check_units already reports that
  case) while the no-roster test still passed. That is the right seam — a missing declaration is this
  check's fault; an unresolvable source is _check_units'.
  First task in this slice where the implementer found NO disagreement with its brief.
Task 7 review: spec ✅, quality APPROVED WITH FINDINGS — 2 Important, 3 Minor. THE JUDGMENT CALL WAS
  VERIFIED CORRECT AT EVERY SHAPE: absent / null / {} all fire; a non-mapping data.units dies upstream as
  fatal E-CONFIG-SHAPE so the .get walk cannot raise; all three declared-but-unresolvable shapes get
  actionable E-UNITS-* findings from _check_units, so silence there is right. Tests confirmed NOT
  vacuous on the old refusal — deleting the call site fails the acceptance test.
  IMPORTANT 1 — THE MISCITED PRECEDENT IS MINE, AND IT TRAVELLED THREE HOPS. My spec's trap table said
  "_check_replication's fold-without-basis shape is the precedent", pointing at E-REPL-FOLD-K. The real
  twin is E-REPL-FOLD-NO-UNITS, twelve lines away: SAME `not (doc.get("data") or {}).get("units")`
  expression, likewise silent for an unresolvable roster. E-REPL-FOLD-K is the different k:all fault.
  Spec -> brief -> shipped comment. FIXED IN THE SPEC so the next brief cannot regenerate it. The twin
  also STRENGTHENS the implementer's judgment call from a novel decision into house pattern.
  IMPORTANT 2 — and the twin DOES NOT RETURN. The comment claimed the checks below the gate "each
  presuppose a roster"; false, `roster` is an unused parameter across the whole function and the
  method/n checks are roster-independent. Measured consequence: `{method: bootstap, n: 50}` with no
  data.units reports ONLY the new code, silently swallowing E-STATS-RESAMPLE-METHOD and -N. A user fixes
  one fault and meets two more. RULED: drop the return, follow the twin, surface all three in one pass.
  GENERALIZES: a false comment can have a BEHAVIOURAL consequence, not just a documentary one — this one
  justified a `return` that suppressed two real findings. When a comment explains why control flow
  stops, check the explanation before trusting the stop.
Out of scope, recorded for its owner: null_test has NO equivalent no-units check, so whichever slice
  retires E-STATS-NULLTEST-UNSUPPORTED (H4d) inherits exactly this hole.
Task 7: COMPLETE (commits d280f86, 01b2b97, cf9f022). 1722 passed + 2 xfailed; ruff and mypy clean.
  The `return` is gone — all three faults now surface in one pass — the precedent citation is corrected
  to E-REPL-FOLD-NO-UNITS, and the null_test equivalent gap is recorded for H4d in spec-defects.md.
  Two existing assertions were tightened from an absence and a broad prefix to exact code sets.
  BASE for task 8 is cf9f022.
Task 8: dispatched. IT IS THE FIRST REAL ROSTER CONSUMER in this slice — limits.min_clusters needs the
  cluster count — so it must NOT reuse task 5's _resample_stratum_table, which writes ONE unit row.
Task 8: implemented, commits 21214d8 + f75078b. 1726 passed + 2 xfailed (baseline 1722 + 4 new); ruff
  and mypy clean. W-STATS-RESAMPLE-CLUSTERS emitted; cluster count derived via units.fold_basis, the
  same derivation _check_replication/_check_sweep share; E-DATA-CLUSTER-UNKNOWN from an unreadable
  cluster attribute caught and treated as unresolved rather than re-reported. The
  statistics.min_clusters -> limits.min_clusters miscitation in stats.py is fixed.
  SEVENTH OF EIGHT IMPLEMENTERS FOUND A BRIEF DEFECT, and this one would not have compiled: the brief's
  test code used dotted overrides (`"limits.min_clusters": 10`) against tests/test_validate.py's
  write_config fixture, WHICH ONLY ASSIGNS THE FINAL LEAF OF A DOTTED PATH and never creates missing
  intermediates — and base_config() declares no top-level "limits" key at all. The literal brief code
  raises KeyError inside the fixture BEFORE the check under test runs. Every other limits override in
  that same file already uses the nested form, so it used `{"limits": {"min_clusters": 10}}`. Same floor
  values, different override syntax, shared fixture untouched.
Task 8 review dispatched. BASE cf9f022, HEAD f75078b.
Task 8 review: spec ✅, quality APPROVED WITH FINDINGS — 3 Important, 5 Minor, NO BEHAVIOURAL DEFECT
  SHIPPED. Everything the dispatch flagged as most-likely-wrong came back RIGHT and verified by
  behaviour: fixtures resolve a real roster (12 units / 4 clusters, not the vacuous-roster trap); the
  count is NOT a proxy — fold_basis -> cluster_count -> clusters_of is the same authority cli.py hands
  percentile_over_units_clustered; a 12-cluster roster at floor 10 is silent, so the cluster count is
  genuinely what moves.
  IMPORTANT 1 — AN UNTESTED GUARD HIDES A REAL CRASH. Three of four guard clauses can be deleted with
  the suite still green. `roster is not None` is load-bearing: missing input file + cluster_by +
  resample sends a TypeError out of units.py, so VALIDATE RAISES WHERE IT IS CONTRACTED TO COLLECT —
  the one outcome validate must never produce. Dropping the cluster_by half yields the nonsense
  "`cluster_by: None` puts this roster in 1 clusters".
  IMPORTANT 2 — FIFTH FALSE CLAIM IN _check_resample'S COMMENTS. "`roster` is unused by every check
  below" is now false (task 8's check reads it) and its enumeration omits the new check. THIS IS THE
  SAME COMMENT THAT IN TASK 7 JUSTIFIED A RETURN SWALLOWING TWO FINDINGS. Ruled: replace the blanket
  property with a per-check statement, since a blanket claim invites the next task to falsify it again.
  IMPORTANT 3 — A FALSE COMMENT PROPAGATING BY COPY-PASTE. The new `except ContractError` comment says
  the fault is "already reported beside this"; measured false (cluster_by naming measurements.by fires
  the branch and NOTHING reports E-DATA-CLUSTER-UNKNOWN). The wording was copied from a sibling handler
  CARRYING THE SAME FALSEHOOD. Ruled: FIX BOTH, against my usual refusal to widen scope — the
  propagation mechanism is copy-paste and the sibling is one line, so leaving it guarantees a third copy.
  Minor worth carrying: the min_clusters miscitation SURVIVES at tests/test_stats.py:2206 — the
  implementer's sweep covered src/ and docs/ only. The "filter the file list" rule is necessary but not
  sufficient; the SCOPE of the file list is the other half.
Task 8: COMPLETE (commits 21214d8, f75078b, fbae604). 1732 passed + 2 xfailed; ruff and mypy clean.
  All 3 Importants and all 5 Minors closed. The roster-guard mutation REPRODUCED A REAL TypeError,
  confirming it guards an actual crash rather than a wrong message. Both copy-paste-propagated
  except-ContractError comments rewritten. Miscitation finally dead in tests/ too.
  SCHEMA AND VALIDATION (tasks 2-8) ARE COMPLETE. _check_resample now carries six checks.
  BASE for task 9 is fbae604.
Task 9: dispatched — the STRATIFIED DRAW. First construction task of the slice; stats.py has been
  byte-identical to cb96c7d until now.
Task 9: implemented, commits f69055a + 0866fa2. 1741 passed + 2 xfailed (baseline 1732 + 9 new — the
  brief's 6 plus 3 the implementer added for degenerate shapes: size-1 stratum, all-identical-value
  stratum, more strata than groupable units). ruff and mypy clean. Both required mutations (draw-count,
  pool-ordering) failed the named test and were reverted in place. Degenerate-shape decisions recorded
  for tasks 14/15: a misaligned strata/values length RAISES ValueError; size-1, identical-value and
  all-singleton strata all work without error.
  Second task with NO brief/code disagreement (after seven of eight that had one).
Task 9 review dispatched. HIGHEST-STAKES REVIEW OF THE SLICE — the first task to touch stats.py, and the
  first whose output is a NUMBER THAT GOES IN A PAPER rather than a refusal.
Task 9 review: spec ❌ (FIRST OF THE SLICE), quality FINDINGS — 3 Important. The ❌ is narrow and the
  statistics around it are RIGHT, VERIFIED INDEPENDENTLY: the reviewer built its own reference
  implementation and the draw matched to ~5e-4, matched the analytic normal approximation (width 0.2067
  vs 0.204), and came out ~80x narrower than pooled — what theory requires when between-stratum variance
  is large. Weights compose against an independent weighted reference. Regression boundary byte-identical
  over 300 RANDOMIZED CASES against fbae604.
  IMPORTANT 1 / THE ❌ — A ZERO-WIDTH ci95 PRODUCED AND PINNED AS CORRECT. strata=["a"]*10+["b"]*4 over
  internally constant strata returns Interval(2.142857, 2.142857). The sibling
  percentile_over_units_clustered REFUSES EXACTLY THIS at one cluster, quoting § Statistical reporting:
  "Reporting a point with no interval is honest; a zero-width 95 % interval is not." This case is WORSE
  than the sibling's because it is STRUCTURAL, not data-caused — the design guarantees it whatever the
  values. And a test the implementer added asserts it is correct: A TEST PINNING WRONG BEHAVIOUR, which
  is harder to find later than no test at all. RULED: follow the sibling, return None, invert the test.
  Two answers to one question inside one module is the drift this project refuses everywhere.
  IMPORTANT 2 — a mutation SURVIVES ALL TEN TESTS: pooling in insertion order rather than sorted-contents
  order. The rotation-by-7 fixture leaves first-seen stratum order unchanged. Fix is the fixture, not the
  assertions: rotate by 28 (reviewer verified the real code stays invariant under it).
  IMPORTANT 3 — the two degenerate tests assert only low < mean < high and BOTH PASS under the
  pooled-swap mutation. They test non-crash, not the property their docstrings name.
SLICE-LEVEL GAP FOUND, ROUTED TO TASKS 13-15: percentile_of_derived TAKES NO `strata`. Once the wiring
  lands, a declared stratify_by would stratify COLUMN metrics and silently NOT derived ones IN THE SAME
  RUN — two intervals in one table computed under different designs, invisible until someone compares
  them. Tasks 13/14/15 dispatches must carry this; it may be additional construction rather than wiring.
Task 9: COMPLETE (commits f69055a, 0866fa2, 79ae219, 4f62117). 1742 passed + 2 xfailed; ruff and mypy
  clean. All 3 Importants closed. percentile_over_units now returns None when every stratum's own
  (value, weight) pairs are identical — mirroring percentile_over_units_clustered's refusal at G < 2 —
  and the test that pinned the zero-width interval as correct was inverted. The rotation-by-28 fixture
  now kills the insertion-order mutation that had survived all ten tests, and both degenerate tests
  assert the stratified interval is under half the pooled width rather than merely not crashing.
  BASE for task 10 is 4f62117.
Task 10: dispatched — the stratified x clustered composition rule, stated then implemented. Carries the
  routed percentile_of_derived gap as context, though its owner is tasks 13-15.
Task 10: implemented, commits 97c911c + 3af1e5a. 1748 passed + 2 xfailed (baseline 1742 + 6 new); ruff
  and mypy clean. percentile_over_units_clustered gained `strata`, enforcing decision 3 — a stratum must
  be constant within a cluster, the draw is a cluster drawn within its stratum — raising
  E-STATS-RESAMPLE-STRATIFY-VARIES on violation and returning None when every stratum holds fewer than
  two clusters, mirroring the existing groups<2 and all-strata-constant refusals. validate gained the
  roster-side check via units.stratum_varies_within_cluster.
  THE BRIEF'S OWN MUTATION INSTRUCTION WAS NON-DISCRIMINATING, AND THE IMPLEMENTER PROVED IT. My
  specified width-ratio test does NOT fail under the `range(len(group)) -> range(1)` mutation on that
  fixture, because the interval's extremes are single-cluster values reachable identically whether a
  stratum draws 1 or its own cluster count. It built a call-count spy (_CountingRandom) that does catch
  it. This is the SECOND time in the slice a proposed mutation could not discriminate (the first was a
  reviewer's in task 5) — the rule now has both halves: a MUTATION, like a fixture, must be checked for
  whether its two branches can actually differ.
  SYSTEMATIC PLAN DEFECT, SECOND OCCURRENCE: the brief again used dotted overrides
  (`"limits.min_clusters": 2`) against write_config, which only assigns the final leaf and never creates
  intermediates, and base_config has no top-level "limits" — KeyError before the check runs. Task 8 hit
  the identical defect. EVERY REMAINING TASK TOUCHING `limits` MUST BE TOLD to use the nested form.
Task 10 review dispatched. BASE 4f62117, HEAD 3af1e5a.
Task 10 review: spec ✅, quality FINDINGS — 3 Important, 3 Minor. STATISTICS VERIFIED INDEPENDENTLY AND
  EXACTLY: the reviewer wrote its own reference implementation from the spec sentence — own ordering,
  own seed, 200k draws — and reproduced the interval TO THE DIGIT. Instrumenting the real draw loop,
  500/500 replicates hold exactly two clusters per stratum across 27 distinct multisets. All three
  candidate answers distinguishable (13.46 clustered-stratified / 57.30 clustered-only / 0.26
  stratified-rows), both theory directions correct, task 1's pin digit-identical over 200 randomized
  fixtures. Both halves of the implementer's mutation diagnosis confirmed, and the spy proved
  NON-VACUOUS JOINTLY with the width test.
  IMPORTANT 1: weights untested on the stratified-clustered path — dropping the weight passes all 1748
  tests and moves the interval [15.462,24.972] -> [16.811,30.275]. weight_by + cluster_by + stratify_by
  are independently declarable, so an ordinary config reaches it.
  IMPORTANT 2: every stratum drawing the FIRST stratum's cluster count passes all 1748 tests — the
  fixture is 2/2/2 and the spy pins only the TOTAL. THE FIX IS NOT A FIXTURE RESHUFFLE: stratum_pools[0]
  sorts by content, so even 3/2/1 totals 6 and stays invisible. Requires a PER-STRATUM COMPOSITION
  assertion. Generalizes: when a spy counts an aggregate, an allocation among the parts is exactly what
  it cannot see.
  IMPORTANT 3: a zero-width interval is reachable — content-identical clusters in every stratum give
  Interval(0.5, 0.5) where the row-level sibling returns None. TASK 9'S ❌ IN A NEW PLACE. Inherited (the
  unstratified path has it at G=2) but stratification makes it EVERYDAY-REACHABLE WITH BINARY METRICS.
  Ruled: fix the stratified path to match the sibling; fix the pre-existing case too IF one line away,
  but STOP AND REPORT rather than moving any behaviour an existing test pins.
  Minor worth carrying: validate compares str(value) while stats compares RAW values, so the
  dual-listed error disagrees on 1 vs "1" — two enforcement points for one rule giving different answers.
Task 10: COMPLETE (commits 97c911c, 3af1e5a, 2348477, c5de085). 1752 passed + 2 xfailed; ruff and mypy
  clean. All 3 Importants and all 3 Minors closed.
  ON IMPORTANT 3 IT DID EXACTLY WHAT THE RULING ASKED: checked FIRST whether any existing test pinned
  the wrong zero-width behaviour, found none, and therefore fixed BOTH the stratified and the
  pre-existing unstratified path — replacing the count-based degenerate check (len(group) < 2) with a
  CONTENT-based one. Had a test pinned it, the ruling required stopping instead.
  The total-count spy became a SEQUENCE-RECORDING spy over a 1/2/3 fixture, which catches both the
  original range(1) mutation and the every-stratum-draws-the-first-count mutation the total-only test
  could not see. The str()/"no value" normalization went VALIDATE's way, since
  units.stratum_varies_within_cluster is the established shared authority elsewhere.
  CONSTRUCTIONS (tasks 9-10) COMPLETE. stats.py now carries the stratified draw and the clustered x
  stratified composition, both verified against independent reference implementations.
  BASE for task 11 is c5de085.
Task 11: dispatched — resample_draws for a column metric. A VERIFY-AND-PIN task: decision 2 rests on the
  invariant that a column draw is never degenerate, and this task is where that invariant is proved
  rather than assumed.
Task 11: implemented, commit d5f6b6b. 1762 passed + 2 xfailed (baseline 1752 + 10 new); ruff and mypy
  clean. THE INVARIANT DECISION 2 RESTS ON IS VERIFIED, NOT ASSUMED: no reachable degenerate column draw
  in the unweighted, weighted or stratified branches, gated respectively by n >= 2, checked_weights /
  usable_weight's finite-positive guard, and non-empty stratum pools by construction. PROVED BY MUTATION
  rather than argued — relaxing usable_weight's guard from <= 0 to < 0 (admitting a zero weight) makes
  the 0/0.0 weight-refusal parameters FAIL WITH ZeroDivisionError, so the pin rests on that guard rather
  than on luck.
  EIGHTH BRIEF DEFECT, AND IT IS THE FALSE-TENSE CLASS AGAIN. My brief's docstring text claimed, PRESENT
  TENSE, that summarize_step already records resample_draws for column metrics as "the requested n". It
  does not — summarize_step's recorded-column branch carries NO resample_draws key at all; that wiring
  is task 12/14's, and E-STATS-RESAMPLE-UNSUPPORTED still refuses a declared resample end to end.
  Writing the sentence verbatim would have shipped a docstring claiming a guarantee the code does not
  provide. It reworded to state the invariant CONDITIONALLY for whenever the wiring lands, and recorded
  the distinction in spec-defects.md. The spec decision itself is unaffected — only the tense was wrong.
  RUNNING COUNT: this is the fourth time in the slice that prose written from the FINISHED slice's point
  of view landed in a brief and would have shipped as a present-tense claim. The pattern is now
  well-established enough to belong in CLAUDE.md at merge.
Task 11 review dispatched. BASE c5de085, HEAD d5f6b6b.
Task 11 review: spec ❌, quality 1 CRITICAL, 3 Important, 2 Minor. THE TASK WORKED — its job was to test
  an invariant, and the invariant turned out FALSE.
  CRITICAL — "a column draw is always defined" IS FALSE. Non-finite column values are reachable END TO
  END: coerce_scalars accepts nan/inf, summarize_step's _is_numeric never checks finiteness, and the
  column branch passes them through — TODAY, ALREADY PRODUCING ci95: [NaN, NaN]. Once 12/14 wires the
  column path the record would claim resample_draws: 2000 where the DERIVED SIBLING ON THE SAME DATA
  SAYS 0. A second instance needs no user nan at all: usable_weight gates each weight finite-positive
  but Σw CAN OVERFLOW — weights=[1e308]*4 gives Interval(nan, nan).
  AND (Interval, int) IS NOT THE REMEDY — percentile_over_units has no survivor filter, so the tuple
  returns (Interval(nan,nan), 2000): the same false claim with more ceremony. DECISION 2'S CONCLUSION
  SURVIVES; ITS PROOF DOES NOT. Ruled: name the finiteness CONDITION in docstring and defect entry, and
  FILE THE NON-FINITE-COLUMN GAP SEPARATELY with its own owner — it is pre-existing, bigger than this
  task, and produces a wrong published number today.
  THE ❌ TRIGGER: the defect entry cites reference.md § Statistical reporting for a two-provenance split
  THAT SECTION DOES NOT STATE (it says the field is "recorded beside every derived metric" and never
  mentions columns). The ruling CONTRADICTS the document rather than resting on it, and in this project
  the document changes first.
  IMPORTANT: the None question is now demonstrably incoherent — a column refused by 9/10's rule writes
  resample_draws: 2000 beside ci95: null, a positive evidence count for a REFUSED interval, while the
  draws<min_honest_draws path reads correctly. reference.md's three-way scheme (null / 0 / survivors)
  PREDATES REFUSALS and may need a fourth case rather than being forced.
  MINOR THAT EXPLAINS THE WHOLE FAILURE: the adversarial set varied CONFIG SHAPE, not VALUE DOMAIN. ONE
  nan CASE WOULD HAVE CAUGHT THE CRITICAL IMMEDIATELY (low <= high is False for nan). That is CLAUDE.md's
  own named trap — "Varying config shape when the property is about roster content" — in new clothes,
  and it is why the invariant survived ten tests.
Task 11: COMPLETE (commits d5f6b6b, 30e8d03). 1765 passed + 2 xfailed; ruff and mypy clean. Critical,
  all 3 Importants and both Minors closed. The non-finite gap is FILED SEPARATELY owned by task 12/14,
  with two tests pinning current behaviour EXPLICITLY AS A KNOWN UNFIXED GAP rather than as correctness —
  the right shape, given task 9 shipped a test pinning wrong behaviour as correct.
  RULED BY THE IMPLEMENTER AND ACCEPTED: resample_draws is `null` whenever ci95 is `null` (all three
  refusal reasons), otherwise the requested n. That makes the COLUMN field genuinely TWO-VALUED against
  the derived metric's THREE-valued scheme — an asymmetry it named explicitly as owed content for
  reference.md rather than smuggling in.
OWED TO reference.md, ROUTED TO TASK 14 (the column percentile wiring, which is where the behaviour
  lands): § Statistical reporting currently says resample_draws is "recorded beside every derived
  metric" and never mentions columns. It owes (a) the column provenance, and (b) the two-valued vs
  three-valued asymmetry above.
Task 12: dispatched — THE RETIREMENT. Carries four items recorded earlier: drop `NOT BUILT; ` leaving
  `# bootstrap`; add the E-STATS-RESAMPLE-METHOD reference to § Statistical reporting now that task 4
  registered it; "Four declarations are not yet built" -> "Three"; and RE-DATE the feasibility doc's
  § Executability rather than editing it in place. BASE 30e8d03.
Task 12: implemented, commits 2fdc957 + 9fa2366 + ef8880f. 1767 passed + 2 xfailed; ruff and mypy clean.
  E-STATS-RESAMPLE-UNSUPPORTED IS RETIRED. Both required mutations confirmed (re-adding the resample
  tuple; deleting the whole loop, which must fail the null_test control).
  NINTH AND TENTH BRIEF DEFECTS, BOTH FALSE-TENSE: (1) my step 3(b) said "Task 2 already removed
  `NOT BUILT;`" — false, task 2 DELIBERATELY KEPT it per my own pre-flight ruling, and the brief's own
  top-matter item 1 said so; the brief contradicted itself. (2) step 3(a)'s prescribed docstring claimed
  cli.command_run ALREADY threads a declared resample into every interval construction — false at this
  commit; cli.py still hardcodes derived_metric_draws = 2000 and that wiring is tasks 13-14. It called
  advisor() before writing anything and wrote the true statement instead.
  IT ALSO REPAIRED FOUR PRE-EXISTING TESTS THAT USED THE RETIRED CODE AS THEIR POSITIVE COMPANION —
  exactly the weakening I asked it to look for. They now use a second, independent _check_resample
  finding. One now-contradicted test deleted. It also fixed a vacuity risk in the brief's OWN acceptance
  test (cwd-relative rglob path, no non-empty guard).
  CAREFUL SEQUENCING WORTH KEEPING: it split into two commits so the feasibility doc's re-dated table
  is measured against a tree where the refusal is ACTUALLY GONE, rather than against the brief-specified
  parent sha which still carries it.
Task 12 review dispatched. BASE 30e8d03, HEAD ef8880f.
Task 12 review: spec ✅, quality 1 Important + 3 Minor. Retirement clean and wholesale; both brief
  defects confirmed; the two-commit split confirmed correct reasoning.
  THE OPEN WINDOW IS SILENT, NOT WRONG — the question I most wanted settled. statistics.resample is read
  at exactly ONE place in src/, nothing echoes the declared values, and resample_draws plus the emitted
  method strings report WHAT ACTUALLY HAPPENED. So a declared n: 5000 sits beside resample_draws: 2000
  in run.yaml: DETECTABLE, not hidden. That is the right state for a two-task window.
  IMPORTANT — A FALSE BEHAVIOUR CLAIM INTRODUCED INTO THE RE-DATED SECTION, which is the worst place for
  one because the section is dated and reads as measured. It said the plugin registry "gates every one of
  them before any other check runs". validate COLLECTS — probed, a config declaring a resolver + holdout
  + faulty resample reports ALL FOUR codes together. Told to re-read the whole section against the same
  standard: anything phrased as what HAPPENS must be OBSERVED, not inferred from the code's shape.
  MINOR WORTH THE NAME: the two repaired n-side tests use `method: "bootstap"` as companion, which is
  checked UPSTREAM of the n leaf — a return after the n check leaves both green while the docstrings
  claim otherwise. The implementer was repairing exactly this failure mode in four other tests and then
  reproduced it in its own.
Task 12: COMPLETE (commits 2fdc957, 9fa2366, ef8880f, 462de50, a6407c0). 1766 passed + 2 xfailed; ruff
  and mypy clean. The false "gates every one of them" claim is reworded after PROBING validate directly;
  the upstream companion replaced with a downstream stratify_by one and mutation-confirmed; the
  duplicate null_test control dropped after re-verifying the pre-existing one still catches the
  whole-loop mutation alone; and five perishable comments ANCHORED TO COMMIT 2fdc957 with readers
  pointed at cli.command_run/derived_metric_draws to check current state directly rather than trust
  prose that goes stale at tasks 13-14. BASE for task 13 is a6407c0.
Task 13: dispatched — THE LIVE REGRESSION HAZARD. Replacing the literal derived_metric_draws = 2000 with
  a resolved value is exactly where an undeclared config could silently acquire a different draw count,
  and task 1's two-document pin exists for this task and no other.
Task 13: implemented, commits 220744b + 8b34b19. 1769 passed + 2 xfailed (+3 new); ruff and mypy clean.
  TASK 1'S PIN IS STILL GREEN — the acceptance criterion this whole slice's first task existed to
  provide, eighteen tasks later. Both required mutations applied/failed/reverted.
  The stratify_by-for-derived gap was handled by STORING IT UNUSED on resample_spec for task 14 to
  consume — the gap stays open but NOTHING IN THE RECORD IMPLIES IT IS CLOSED, which was the constraint.
  First task in a while with no substantive brief/code disagreement (only six lines of line-number drift).
Task 13 review dispatched. BASE a6407c0, HEAD 8b34b19. THE REGRESSION-HAZARD REVIEW.
Task 13 review: spec ✅, quality 1 Important + 3 Minor, no Critical. THE DANGEROUS PART CAME OUT RIGHT
  AND WAS VERIFIED, NOT ASSUMED. .get("resample", …) fails the ABSENT-KEY pin while the explicit-null pin
  passes — the two-document distinction intact, which is the whole reason task 1 wrote two tests.
  Deriving `declared` from n != 2000 fails specifically at the {"n": 2000} assertion. A mutation the
  implementer did NOT run — resolver call left in, derived_metric_draws hardcoded — fails the declared-n
  test, so the resolved value really reaches all six sites.
  DECISIVE: TASK 1'S PIN STILL REACHES THE CHANGED CODE. It pins the derived ci95 NUMERICALLY and it fell
  to the first mutation. A green pin is not evidence on its own — a pin can survive by no longer reaching
  what it guarded — and this one was checked for exactly that.
  The stratify_by decision met its constraint UNDER TEST: with stratify_by declared, run.yaml carries
  only the verbatim config echo plus percentile_over_units / resample_draws. Nothing implies a stratified
  derived draw.
  IMPORTANT: the new threading comment sits at the ONE LINE three other files point readers to, and it
  (a) says "statistics.resample is honored as of H4a" unqualified when ONLY `n` is honored, (b) quotes
  § Statistical reporting's "resolved values are recorded beside the interval" AS A REQUIREMENT THIS
  COMMIT MEETS when it does not (that is task 17), and (c) REPLACED A COMMENT THAT WAS SCRUPULOUS ABOUT
  NAMING ITS OWN OPEN GAP — undoing task 12's anchoring discipline at the site that most needs it.
  MINOR RAISED IN PRIORITY BECAUSE TASKS 14-17 WORSEN IT: test_the_resample_block_is_resolved_once does
  NOT distinguish "resolved once" from "read seven times" — it calls the resolver directly and would pass
  if seven sites resolved independently. ONCE-NESS IS GUARDED BY NOTHING IN THE SUITE, immediately before
  four tasks add read sites. The false docstring text was verbatim from MY brief.
Task 13: COMPLETE (commits 220744b, 8b34b19, ce2f2db). 1770 passed + 2 xfailed; ruff and mypy clean.
  All four findings closed. THE ONCE-NESS TEST IS NOW REAL — a call-counting monkeypatch around a full
  run_a_project, confirmed to fail when a redundant resolver call is inserted. That guarantee now holds
  for tasks 14-17, which are the tasks that add read sites. The threading comment states only what is
  true at this commit and names task 17 for the recorded-values requirement.
  BASE for task 14 is ce2f2db.
Task 14: dispatched — THE PAYLOAD. Where a declared resample finally changes a recorded column's
  interval, and where the partly-honoured window opened by task 12 CLOSES. Carries the two reference.md
  amendments owed from task 11 and the percentile_of_derived strata gap routed from tasks 9/13.
Task 14: implemented, commit (this task). 1776 passed + 2 xfailed (baseline 1770 + 6 new); ruff and
  mypy clean. All three required mutations (dropped `weights=` in the unclustered percentile call,
  emitting `resample_draws` unconditionally, and gating `resample_columns` on anything but
  `resample_spec["declared"]`) applied, confirmed FAIL against a named test, `__pycache__` cleared,
  reverted in place, confirmed PASS. Task 1's acceptance pin caught the gate mutation directly.
  BRIEF/CODE DISAGREEMENT FOUND (as flagged): the brief's own Step 1 test asserted
  `resample_draws == 2000` for a one-unit column under a declared resample — a refused (`ci95: null`)
  interval. The spec-defects.md ruling this brief itself cites says the field must be `null` whenever
  `ci95` is, for exactly this reason ("recording the requested `n` there would assert survivor
  evidence for a refused interval"). Implemented per the ruling, not the brief's literal snippet;
  the test was rewritten and renamed
  (`test_a_column_below_two_units_reports_a_null_draw_count_under_resample`) to assert `None`, and a
  new spec-defects.md entry ("A column's resample_draws under a refused interval is null, not the
  requested n") records which test was wrong and why. Caught before implementing via `advisor()`,
  which cross-checked the brief's test against spec-defects.md's own text before any code was written.
  STRATA DECISION: shipped WITHOUT threading `stratify_by` into either the column or the derived path.
  Threading it into the column path alone (the only one cheap enough for this task, since
  `percentile_over_units`/`_clustered` already accept `strata`) would have put two intervals in one
  table under different designs with `method` reading identically either way — worse than today's
  status quo, where both paths agree by both ignoring it. A new spec-defects.md entry
  ("statistics.resample.stratify_by is checked by validate and honoured by nothing") records the gap
  and names what closing it needs: `percentile_of_derived` gaining a `strata` parameter first (a real
  construction — the derived draw has no per-unit value to stratify directly), with the column wiring
  landing alongside it rather than ahead of it. `cli.py`'s stale "task 14 wires stratified column
  resampling" / "declared is unread until task 14" comments (written by tasks 12-13) were rewritten to
  state what this commit actually does.
  `reference.md` § Statistical reporting gained the column-provenance paragraph task 11 named as owed:
  absent when undeclared, `null` when declared but `ci95` is, otherwise the requested `n` — two-valued
  against the derived metric's three-valued scheme, named as a real asymmetry rather than smoothed over.
  The retry `summarize_step` call (post derived-key-collision) deliberately does NOT receive
  `resample_columns`, so a column's construction cannot depend on whether its sibling derived metrics
  happened to collide — commented at the call site.
  The `cli.py` warning loop now reads `resample_draws` off recorded columns too; commented (not a
  runtime assert) why `used == 0` and `used < derived_metric_draws` cannot fire for one, resting on
  Task 11's verified invariant and this task's `null`-or-`n` correction of it.
  BASE for task 15 is this commit.
Task 14: implemented, commits b156b1b + 556d13d. 1776 passed + 2 xfailed (+6 new); ruff and mypy clean.
  All three required mutations applied/failed/reverted, and TASK 1'S PIN CAUGHT THE GATE MUTATION
  DIRECTLY — the acceptance criterion doing its job on the payload task.
  ELEVENTH BRIEF DEFECT, AND THE BRIEF CONTRADICTED THE RULING IT ITSELF CITED: my Step 1 test snippet
  pinned resample_draws == 2000 for a column whose interval is REFUSED (ci95: null, one unit), while the
  spec-defects ruling the same brief cites says the field must be null in that case — a draw count beside
  a refused interval asserts survivor evidence that does not exist. It FOLLOWED THE RULING, NOT THE
  SNIPPET, rewrote the test, and filed an entry recording which test was wrong.
  STRATA DECISION, AND IT IS THE RIGHT ONE: shipped WITHOUT threading stratify_by into either path.
  Wiring the column path alone was the cheap option (the construction exists there) but would have
  produced TWO INTERVALS IN ONE TABLE UNDER DIFFERENT DESIGNS with nothing in the record to tell them
  apart — WORSE than today, where both paths agree by both ignoring it. GENERALIZES: "both wrong the same
  way" is a better interim state than "one right, one wrong, indistinguishable". Filed naming what
  actually closes it: a `strata` parameter on percentile_of_derived — a real construction — with the
  column wiring landing alongside it.
  reference.md § Statistical reporting got the owed column-provenance paragraph.
Task 14 review dispatched. BASE ce2f2db, HEAD 556d13d.
Task 14 review: spec ✅, quality 4 Important + 4 Minor, no Critical.
  CONFIRMED GOOD: task 1's pin bites AND STILL REACHES the changed code (4 tests fail under the
  unconditional-emit mutation); the null-under-refused-interval guard is pinned; the weighted unclustered
  draw is pinned by an EXACT ci95 match — the implementer was right to replace my bracketing assertion,
  which would not have caught it; the summary-Estimate risk is genuinely NOT live (summary_values ->
  evaluate_hypotheses is disjoint from summarize_step).
  IMPORTANT 1 — THE `declared` GATE, WHICH I NAMED AS SEAM NUMBER ONE, IS UNDISCRIMINATED. Mutating it to
  `n != 2000` leaves the FULL SUITE GREEN, because no test declares resample with exactly n: 2000 — the
  only config separating the two readings. The report's "task 1's pin caught the gate mutation" is true
  of the PRESENCE mutation, not this one. Fix is one test. GENERALIZES: naming a seam in a brief does not
  make it tested; the discriminating CONFIG has to exist.
  IMPORTANT 2: clustered AND weighted — the fourth required combination — ships unpinned.
  IMPORTANT 3: the new reference.md paragraph over-claims ("finite throughout ... always defined", no
  hedge) where the ruling says "conditional on finite inputs" — AND TASK 14 IS WHAT MAKES THE
  COUNTEREXAMPLE REACHABLE FROM A REAL RUN: a column with one nan now records ci95: [nan, nan] beside
  resample_draws: 2000. The defect entry assigned finiteness to "task 12/14"; task 14 neither did it nor
  recorded declining it.
MERGE GATE RECORDED (Important 4): the stratify_by judgment was RIGHT but the option set INCOMPLETE — a
  RUN-TIME WARNING was never weighed, and it is neither a divergent construction nor a doc change. The
  gap is WORSE after this commit: a declared resample now VISIBLY MOVES the interval while the
  stratify_by beside it silently does nothing, and six of seven feasibility declarations carry one.
  RULED: add a W-STATS-RESAMPLE-STRATIFY-UNHONOURED-shaped run-time warning in task 14's own code, since
  that is where the declaration is read and not honoured. H4A MUST NOT MERGE WITHOUT A USER-VISIBLE
  ROUTE — the whole-branch review is to check this.
Task 14 review: spec ✅, quality 4 Important + 4 Minor, no Critical. Confirmed good first: task 1's
  pin bites AND still reaches the changed code (four tests fail under the unconditional-emit
  mutation), the null-under-refused-interval guard is pinned, the weighted unclustered draw is
  pinned by an EXACT ci95 match (the bracketing assertion it replaced would not have caught the
  mutation), the brief/ruling contradiction was resolved correctly, and the summary-Estimate risk is
  genuinely not live (summary_values -> evaluate_hypotheses is disjoint from summarize_step).
  IMPORTANT 1 — the `declared` GATE ITSELF WAS UNDISCRIMINATED: mutating it to `n != 2000` left the
  full suite green, since no test declared `resample` with exactly the UNDECLARED-default `n: 2000`.
  Fixed with one test (`test_declaring_n_2000_still_gates_a_column_on_declared_not_on_n`), confirmed
  to fail under exactly that mutation.
  IMPORTANT 2 — clustered AND weighted (the fourth required combination) shipped unpinned: dropping
  `weights=` from the clustered percentile call left the suite green. Fixed with an exact-match pin
  (`test_a_clustered_and_weighted_column_pins_both_together_under_resample`), confirmed to fail.
  IMPORTANT 3 — the reference.md paragraph over-claimed "finite throughout ... always defined" with
  no hedge, while the ruling it derives from is explicit "conditional on finite inputs" — and task
  14's own wiring is what makes the counterexample reachable from a real run (a column with one nan
  now records ci95: [nan, nan] beside resample_draws: 2000). Hedged both reference.md's paragraph and
  stats.py's docstring to match the ruling; the "task 12/14" assignment in the earlier spec-defects
  entry was left declined-and-named rather than silently unaddressed (the entry already named
  task 12/14 as the owner and this task explicitly declines, consistent with the earlier finiteness
  entry's own "not attempted here").
  IMPORTANT 4 (MERGE GATE) — the stratify_by option set (thread / refuse / ship-the-asymmetry) OMITTED
  a run-time warning, the cheap disclosed-gap route this project uses everywhere else. Ruled: add
  `W-STATS-RESAMPLE-STRATIFY-UNHONOURED`, fired once per run when `resample` is declared with a
  non-empty `stratify_by`, registered in reference.md § Warnings core reports, with a positive and a
  negative test, both confirmed to fail under the relevant mutation. spec-defects.md's stratify_by
  entry amended to record the disclosure without closing the underlying gap.
  MINORS: the retry-call comment overclaimed a live behavior change (the retry passes no `seed`
  either, so `resample_columns` there is inert today, not merely unused-by-choice) — reworded to
  state the true, narrower reason it stays off. Three positional locators in the new reference.md
  paragraph and spec-defects.md entries ("the paragraph above", "two entries above", "the option set
  above") renamed to what they refer to. Two of the three null-interval reasons were unexercised for
  a column (too-few-draws-for-confidence was untested; the third, per-stratum constant-pair, is
  unreachable for a column today since no strata are threaded) — added
  `test_a_column_below_the_honest_draw_floor_also_reports_a_null_draw_count`.
Task 14: COMPLETE, all review findings addressed. 1781 passed + 2 xfailed (baseline 1770 + 11 new
  across both rounds); ruff and mypy clean. Every new assertion mutated, confirmed to FAIL, reverted
  in place. BASE for task 15 is this commit.
Task 14: COMPLETE (commits b156b1b, 556d13d, d61c640, a6fe234). 1781 passed + 2 xfailed; ruff and mypy
  clean. All 4 Importants and all Minors closed. The undiscriminated gate now has its discriminating
  config (resample: {n: 2000} declared explicitly, same value as the undeclared default); clustered+
  weighted pinned by exact ci95; the finiteness claim hedged in BOTH reference.md and the stats.py
  docstring with the unchecked-ness disclosed; and W-STATS-RESAMPLE-STRATIFY-UNHONOURED added, fired once
  per run, registered in § Warnings core reports, with positive and negative tests both
  mutation-confirmed. MERGE GATE CLOSED.
RULING — TASK 15 IS AMENDED, BECAUSE ITS PLAN TEXT PREDATES TASK 14'S DECISION AND CONTRADICTS IT.
  As written, task 15 threads strata into the COLUMN path only (summarize_step -> percentile_over_units/
  _clustered). THAT IS EXACTLY THE ASYMMETRY TASK 14 DECLINED TO CREATE — two intervals in one table
  computed under different designs, with nothing in the record to tell them apart. Executing task 15
  verbatim would undo a decision this slice made deliberately two tasks ago.
  Three options weighed. (a) Thread column-only anyway: contradicts task 14, reintroduces the asymmetry.
  (b) Grow task 15 to include a `strata` parameter on percentile_of_derived, so BOTH paths honour the
  declaration. (c) Defer, and ship H4a with stratify_by disclosed-but-not-honoured.
  CHOSEN: (b). Grounds — SIX OF SEVEN non-null resample declarations in the feasibility analysis carry a
  stratify_by, so (c) leaves the slice's headline deliverable partial for the common case; and the
  construction is CONTAINED, being the same draw discipline percentile_over_units already implements,
  applied to KEY selection rather than value selection. The slice is called "resample honoured" and (b)
  is what makes that name true.
  CONSEQUENCE TASK 15 MUST HANDLE: W-STATS-RESAMPLE-STRATIFY-UNHONOURED, which task 14 added one task
  ago, IS RETIRED BY TASK 15 — the gap it discloses closes. That is the correct sequence rather than
  waste: disclosure was right for the state task 14 shipped, and retiring it is right for the state task
  15 ships. Task 15 must remove the warning, its registry row and its tests, or the record will warn
  about a gap that no longer exists.
  COST IF WRONG: task 15 grows from wiring to wiring-plus-one-construction and may need splitting. The
  dispatch tells the implementer to report rather than push through if the derived construction turns
  out large.
Task 15: implemented per the amendment, commits 8c4bcbb + 6267120 + d715e08. 1787 passed + 2 xfailed
  (+6 net); ruff and mypy clean. BOTH PATHS NOW HONOUR strata: percentile_of_derived gained a real
  construction (draws KEYS with replacement within each stratum, preserving stratum size), summarize_step
  threads strata into both branches, and cli composes resample_strata ONCE from the roster gated on
  `declared and stratify_by`. W-STATS-RESAMPLE-STRATIFY-UNHONOURED IS RETIRED — emit site, warnings row
  and both tests — and the spec-defects entry marked CLOSED. The amendment's judgment held: the derived
  construction was contained, as predicted, and the implementer did not need the escape hatch.
NEW ASYMMETRY FOUND BY THE IMPLEMENTER, ONE LAYER IN — RAISED FOR THE MERGE GATE, NOT FILED AS ROUTINE:
  the report_by level call site still does not pass `resample_columns`, so under a declared resample a
  LEVEL'S RECORDED COLUMN STAYS UNRESAMPLED while its derived metrics are now stratified. That is the
  same class task 14 declined to create — two intervals under different designs in one table — one layer
  down, and it PREDATES this task and sits outside its scoped call sites. Within a single run this means
  top-level column = percentile while level column = t_over_units. The task 15 review is asked to assess
  whether this is a merge blocker or a legitimate deferral.
  Also flagged for future fixtures: a blank CSV cell yields "" and NOT None, so testing the
  missing-attribute sentinel needs a genuinely SHORT CSV ROW rather than a blank field.
Task 15 review dispatched. BASE a6fe234, HEAD d715e08.
Task 15 review: spec ✅, quality approved with findings — 2 Important, 5 Minor, no Critical.
  STATISTICS VERIFIED INDEPENDENTLY AND EXACT: replicates preserve per-stratum KEY counts (one distinct
  composition {low:20, mid:8, high:2} over 50 replicates); an independent reference draw reproduces
  Interval(290.45, 296.55) TO THE DIGIT against a pooled (82.8, 602.2) and an equal-weighted-stratum-
  means answer of 1111.6. Both paths move together in one run, confirmed at stats level, CLI level, and
  on a crossed report_by/stratify_by run. Warning retirement complete on every surface. Task 1's pin
  green AND reaching the new branch.
  IMPORTANT 1 — THE ZERO-WIDTH FAULT, THIRD OCCURRENCE. percentile_of_derived has no constant-pool
  refusal, so singleton strata (any near-unique attribute, validates clean) put a column ci95: null
  beside a derived ci95: [50.4875, 50.4875] with resample_draws: 2000, in one table, no warning. Task 9
  shipped this (the slice's first ❌), task 10 shipped it on the clustered path, and BOTH SIBLINGS NOW
  REFUSE IT. A third construction that does not is three answers to one question inside one module.
  IMPORTANT 2 — the clustered x stratified WIRING is invisible: replacing strata=column_strata with None
  in the clustered call leaves ALL 1787 TESTS PASSING. Same shape as task 14's undiscriminated gate — a
  seam named in the design and instantiated by no fixture. That is now TWICE in this slice.
ADJUDICATED — report_by ASYMMETRY: DEFER, and the argument is worth keeping. It is NOT task 14's class
  in the load-bearing respect: a level's column and its derived metric carry DIFFERENT method strings and
  differ on resample_draws presence, so run.yaml DISCLOSES the difference — where task 14's case would
  have been two identical method strings with nothing to separate them. THE TEST FOR THIS CLASS IS NOT
  "do two intervals differ in design" BUT "can a reader TELL". It also predates the slice, and the fix is
  a task (level-thin min_honest_draws, per-level two-valued draws, tests), not a line. Filed with a named
  owner. Raising it for the merge gate rather than filing it as routine was the right call.
Task 15: COMPLETE (commits 8c4bcbb, 6267120, d715e08, c1286bb). 1792 passed + 2 xfailed; ruff and mypy
  clean. Both Importants and all 5 Minors closed. percentile_of_derived now refuses a constant-pool draw
  the same content-based way both siblings do — THE ZERO-WIDTH FAULT IS NOW CLOSED ON ALL THREE
  CONSTRUCTIONS. The clustered x stratified wiring has an end-to-end pin at summarize_step's own call
  site. The report_by asymmetry is filed with a named owner (H4's report_by hardening), merged into the
  same spec-defects entry. BASE for task 16 is c1286bb.
Task 16: dispatched — THE DANGEROUS ONE. The spec names it "the one place H4a can produce a wrong number
  with a green suite", and both of its traps were found by measurement rather than reading.
Task 16: implemented, commit b06079c. 1795 passed + 2 xfailed (+3 new); ruff and mypy clean. Both named
  mutations confirmed FAIL then reverted — forgetting the Member (the genuinely silent path) and
  col_keys -> base_keys. Performance MEASURED rather than assumed: 0.18s per column-comparison at n=240 /
  2000 draws, so the cheap direct index-vector construction was not needed.
  TWELFTH BRIEF DEFECT, AND IT IS THE FIXTURE-AGREES-WITH-THE-BUG CLASS IN MY OWN BRIEF. My test
  recomputed the expected t-bound assuming _CONDITION_SCALED_STEP scales pearson/spearman as 1.0/2.0 —
  but the fixture that ACTUALLY EXISTS, built by task 1 and revised during ITS review, scales 1.0/3.0.
  Copying my line verbatim made the "not the t-interval" assertion PASS UNDER BOTH CORRECT AND MUTATED
  CODE. It used the correct diff (2.0 * float(i)) and verified the mutation now genuinely fails.
  GENERALIZES: task 1's review CHANGED that scale precisely to break a numeric coincidence, and my brief
  for task 16 was written against the pre-review value. A BRIEF WRITTEN BEFORE A REVIEW LANDS CAN CARRY
  NUMBERS THE REVIEW DELIBERATELY MOVED — and the failure mode is silent, because the stale number still
  produces a passing test.
Task 16 review dispatched. BASE c1286bb, HEAD b06079c. HIGHEST-RISK TASK OF THE SLICE.
Task 16 review: spec ✅, quality approved with findings — 1 Important, 6 Minor. BOTH TRAPS VERIFIED BY
  MUTATION *AND ATTRIBUTED*: the col_keys -> base_keys mutation fails the ragged test BECAUSE OF THE
  RAGGED UNITS (sometimes -> ci95: None, n_paired: 30 against always -> [16.025, 23.025], n_paired: 40),
  not incidentally. The vacuous-test fix confirmed genuine — with the brief's [float(i)] the assertion
  passes under BOTH codes; with [2.0*float(i)] the mutation reproduces t_bound exactly. The `declared`
  seam IS tested here, so this is NOT a third instance of the untested-seam pattern.
  IMPORTANT — MY SWEEP SCOPE WAS WRONG AGAIN, SECOND TIME THIS SLICE. _comparison_step_blocks's own
  docstring still says the Member carries "the per-unit differences for a recorded column" — THE EXACT
  SENTENCE THIS TASK FALSIFIES, IN THE FUNCTION IT CHANGED. My brief's sweep fixed the identical sentence
  in correction.py and STOPPED ONE FILE SHORT. Task 8's sweep covered src/ and docs/ but not tests/.
  GENERALIZES: when a change falsifies a sentence, the sweep must be for THE CLAIM, not for the file the
  claim was first noticed in.
  Minor worth keeping (M3): the flagship test recomputes Holm's rank-1 level instead of reading
  entry["correction_level"] from run.yaml — and the two family members are EXACTLY TIED on the ranking
  statistic (kendall's pool is element-wise 2x spearman's at the same seed, so the same index draws), so
  spearman's rank-1 position is a TIE-BREAK. Loud rather than silent if it broke, but the same
  assumption-derived class as the defect fixed one line above.
  M4: perf conclusion right, number understated — 1 column 0.19s, TEN columns 0.32s, so a 10x5 family is
  ~16s not ~9s. Still far under threshold; keeping the construction was correct.
  M6/M7 FILED with owner H4 contrast-side hardening: a declared resample can silently null a column
  contrast's interval (W-STATS-RESAMPLE-THIN fires only from the per-condition path), and
  paired_percentile_of_derived never got the zero-width sweep its three siblings have.

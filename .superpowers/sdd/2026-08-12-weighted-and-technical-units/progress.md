# SDD ledger — plan: docs/superpowers/plans/2026-08-12-weighted-and-technical-units.md
Plan: docs/superpowers/plans/2026-08-12-weighted-and-technical-units.md (12 tasks).
Branch h3a-weighted-and-technical-units, base 410dd9a (main, H2 merged).

Pre-flight scan (controller, before task 1): ONE conflict found in the plan and fixed rather than
  batched to the user, being my own authoring defect with no genuine choice in it — task 10's prose
  forbade a test-only hook on the production signature while its own code block used one
  (`_record_draws`). Rewritten so the draw is observable through the OUTPUT: 20 units at 1.0 plus one
  at 100.0 carrying almost all the weight, drawn unweighted, reaches down to low == 1.0 in some draws;
  a draw-weighted implementation could never produce that low bound. Also recorded there that
  percentile_over_units currently SORTS its pool (with a comment about multiset-not-row-order), so a
  weighted version must keep each value with its own weight or it silently pairs values with the
  wrong weights — which the equal-weights test cannot see.

Task 1: commit 193957b, DONE_WITH_CONCERNS, fix round 1 dispatched.
  Three concerns from the implementer, all correct, all mine:
  - THE BRIEF'S OWN STEP 3 CODE CRASHED ON ITS OWN STEP 1 TEST. collapse="mean" applied blanket-wise
    to a constant string column hits sum(["A","A"]). The implementer found the governing sentence
    rather than patching around it: "Attributes constant within a key collapse to that value with no
    rule needed", reference.md § What isn't a repeat. Put in _apply and ordered AFTER the rule-name
    validation so a bogus rule still raises over a single-member group — both correct, and _apply is
    the better home than the loop because task 5 calls it directly with already-grouped values.
  - The brief's mutation #1 (first branch, values[0] -> values[-1]) DOES NOT KILL against the
    verbatim test, because both `site` values are "A" — index choice is unobservable there whatever
    the implementation. A mutation my own plan specified against a test that could not detect it.
    Implementer added a per-column-map test with differing values and confirmed the kill there.
  - Mutation #2 (recomputing counts in a second walk) does not change behaviour today, exactly as the
    brief predicted. Reported honestly rather than manufactured — the correct outcome.
Task 1: CRITICAL found by the controller while verifying the constant-column claim, and it is a
  defect in my plan that task 2 would have inherited. COLLAPSE_RULES = ("mean","first","mode") is
  WRONG. reference.md § What isn't a repeat: "`collapse` is `mean`, `median`, or `sum` for numeric
  columns and `first` or `mode` for the rest". FIVE rules in two groups. As written, collapse: median
  — which the document offers — raises E-UNITS-COLLAPSE-RULE as unknown. Fixed in the plan
  (COLLAPSE_RULES plus a NUMERIC_COLLAPSE_RULES exported for task 2's row-243 check, so the check and
  the collapse cannot hold two different ideas of what `mean` may be applied to) and dispatched as
  task 1 fix round 1.
  Two documented guarantees ride on the same sentence and each got a test in the fix round: `first`
  means the earliest row in RESOLUTION ORDER (true only because collapse_measurements appends within
  a group in iteration order — a property someone could reorder away), and `mode` breaks ties "by
  whichever tied value appeared first", which currently rests on an undocumented CPython property of
  Counter.most_common preserving insertion order among equal counts.
Task 1: E-UNITS-COLLAPSE-RULE needs a registry row and it is NOT the validate-time table's.
  _apply raises it, so it is raise-time: § Errors core raises, which scopes itself to "exactly the
  run-time surface, where there is a step to raise into". H2 nearly mis-scoped a code this way; the
  two tables' own scoping sentences are what settle it.
Task 1: noted for the reviewer, not a defect — the step-1 test uses collapse="mean" over a constant
  string column, which is a config shape task 2's row-243 check will REFUSE. Fine for a unit test of
  a function that must stay total, but the docstring has to say so or a later reader takes the test
  as evidence the config is legal.
Task 1: fix round 1 landed (a8f59c9) — five rules, NUMERIC_COLLAPSE_RULES exported, median/sum
  implemented, mode tie-break pinned, E-UNITS-COLLAPSE-RULE row added. 1083 passed + 2 xfailed.
  Controller verified behaviourally from a clean tree with __pycache__ cleared: all five rules, the
  tie-break, the constant-column rule, and the ContractError code.
Task 1: REVIEW returned spec ❌ with one Critical, one Important, one Minor. Fix round 2 dispatched.
  CRITICAL — the constant-column shortcut silently corrupts `sum`. _apply("sum",[5,5]) -> 5, not 10;
  [1000,1000] -> 1000. A no-op for mean/median/first/mode (all idempotent on constant input) and
  wrong only for sum, and DATA-DEPENDENT: two reads both at depth 10 give 10 while 10 and 11 give 21.
  No test covered a constant numeric column under any rule.
  RULING: the shortcut is not wrong to exist — it is what makes _apply("mean",["A","A"]) return "A"
  instead of crashing, which was round 1's whole finding. Its real job is narrower than "all values
  equal": it lets a NUMERIC RULE SUCCEED OVER VALUES IT CANNOT OPERATE ON, which is what the document
  means by "attributes constant within a key collapse to that value with no rule needed" — `site`
  needs no rule because no rule is meaningful for it. When a numeric rule meets genuinely numeric
  values the user asked for an aggregation and must get one. So the shortcut is gated on
  `not (rule in NUMERIC_COLLAPSE_RULES and values are numeric)`, with an explicit bool check because
  isinstance(True, int) is True and summing booleans is a different intent.
  Routed to spec-defects.md rather than a document edit: the document states the constant rule and
  states sum's membership in the numeric group but never states their INTERACTION, which is why this
  was reachable.
  IMPORTANT — I was WRONG to tell the implementer E-UNITS-COLLAPSE-RULE was raise-time only. validate
  CALLS resolve_units inside `try: ... except ContractError as exc: c.error(exc.code, ...)`, so the
  code genuinely surfaces as a validate-time finding once task 3 wires the collapse in. The reviewer
  found the exact precedent: E-REPL-SEED-COLLISION is DUAL-LISTED in both § Errors validate reports
  and § Errors core raises, for the same reason — repeat-level resolution runs at both times, as unit
  resolution does. Row added to both; validate-time count 65 -> 66.
  MINOR — the ordering claim (rule-name validation before the constant shortcut, so a bogus rule still
  raises over a single-member group) was asserted in a comment and provided by nothing: the reviewer
  swapped the order and all 43 tests still passed. The dominant defect class. Now pinned by
  _apply("bogus", ["A"]) raising even though the single value is trivially constant.
Task 1: HANDOFF TO TASK 3, recorded now so it is not rediscovered. resolve_units builds attributes
  through csv.DictReader, so a table-sourced numeric column arrives as `str`. Once the collapse is
  wired in, sum(["10","20"]) raises a bare TypeError — and validate catches only ContractError, so it
  PROPAGATES OUT OF VALIDATE, violating the hard invariant that validate collects findings and never
  raises. Task 1's Unit-constructing tests cannot reach it. Task 3's brief must carry this.
Task 1: two brief claims the review IMPROVED on rather than merely confirming — `first`'s
  resolution-order guarantee is correctly documented as units.py's own responsibility, and `mode`'s
  tie-break rests on two DOCUMENTED guarantees stacked (max() returns the first-encountered element on
  ties; dict insertion order is language-spec since 3.7), not the undocumented CPython property my
  brief warned about. Better grounded than the brief claimed.
Task 1: fix round 2 landed (d1d2026) — sum gate, dual-listed row, ordering test. Scoped re-review:
  ALL THREE FINDINGS CLOSED, task 1 completable. Verified independently by the re-reviewer with its
  own mutations (gate removal -> 5 != 10; shortcut moved above the rule check -> DID NOT RAISE).
  Registry count confirmed 65 -> 66 by counting both revisions, and E-REPL-SEED-COLLISION confirmed
  genuinely dual-listed (validate-time and raise-time) — the precedent holds.
  ONE NEW MINOR, same class as the one it followed: the gate's `bool` exclusion was CLAIMED in a
  comment and provided by nothing — including bool as numeric left all 45 tests passing. Closed by the
  controller in 05ac1ba rather than a third fix round (one line, and the comment "reads as verified
  when it isn't"). Mutation-verified: dropping the exclusion fails that test and nothing else.
  Controller note on method: my first sed revert of that mutation SILENTLY DID NOT MATCH — and
  behaviour caught it, exactly as the standing rule predicts. `git status` would have shown a dirty
  tree either way; only running the test revealed the revert had not taken. Second confirmation that
  reverts are verified by behaviour.
Task 1: KNOWN AND ACCEPTED, not fixed — sum([True,True]) is True while sum([True,False]) is 1, a type
  asymmetry. `sum` over a boolean column is incoherent whichever branch it takes; refusing it belongs
  to task 2's collapse-rule/column-type check. Recorded in the test's own docstring so it is not
  rediscovered as a bug.
Task 1: STRUCTURAL ISSUE raised by the re-reviewer, not task 1's to solve, worth carrying. CLAUDE.md
  says to record a spec gap in docs/superpowers/spec-defects.md — but that whole tree is gitignored
  and has never been tracked, so "record the gap" is satisfied only TRANSIENTLY: the record does not
  survive a merge or a fresh clone. This slice's entry documents a genuine ambiguity between two
  normative sentences in reference.md (the constant-collapse rule vs sum's numeric membership), which
  is exactly the class the cross-document pass exists to catch. Options are a tracked home or a
  clarifying sentence in reference.md § What isn't a repeat. Route it; do not silently rely on the
  gitignored file.
Task 1: complete (commits 193957b, a8f59c9, d1d2026, 05ac1ba). 1086 passed + 2 xfailed.
Task 2: commit 41de16c + cc6fb3f (mine). Review: spec ✅, task quality APPROVED with findings, none
  blocking task 2. 1099 passed + 2 xfailed. Validate-time registry 66 -> 68 as predicted.
  THE CSV RULING held up. resolve_units builds attributes through csv.DictReader, so a table-sourced
  numeric column arrives as "10", not 10. Written naively the check would have refused collapse: mean
  over every CSV-sourced numeric column — most real configs. Implementer accepted a numeric-LOOKING
  string and refused a non-numeric one; the reviewer confirmed the alternative would be unusable.
  Constant-string ruling also held: a constant `site` column survives `mean` at run time via task 1's
  shortcut, and validate refuses it anyway, per the document ("the alternative is a silently dropped
  column or a meaningless number"). Pinned by a test whose name says it refuses a shape the runtime
  survives. Falls out of the design rather than a carve-out.
  DEAD-CHECK CONFOUND EXPLICITLY KILLED: E-DATA-MEASUREMENTS-UNSUPPORTED is still live, so every test
  here could in principle have passed off the refusal. The reviewer neutered _check_measurements with
  an early return and confirmed TEN positive tests fail — none was passing off -UNSUPPORTED.
Task 2: CONTROLLER FIX cc6fb3f — task 2 duplicated units._rule_for's per-column fallback inline
  rather than importing it, because the helper was private. That is decision 4's drift, and there was
  no precedent for a cross-module private import (the one apparent case imports a PUBLIC name and
  aliases it locally). Made rule_for public; both callers now route through it.
  Mutation-verified as genuinely shared: changing the fallback from `first` to `mean` in units.py now
  fails a test in test_units.py AND one in test_validate.py; before, only the first.
  MY DRIFT CLAIM WAS TRUE AS TEXT BUT NOT DEMONSTRABLE AS BEHAVIOUR — the reviewer checked. Every
  reachable path validates all collapse values against COLLAPSE_RULES and returns before the
  per-column loop, so a non-string rule value never reaches rule_for and str() cannot change a verdict
  on today's inputs. The refactor stands on single-source grounds; "could validate against one reading
  and run under the other" is LATENT, not live. Recorded because overclaiming a justification is the
  same class as the defects this slice keeps finding.
Task 2: MY OWN PROCESS DEFECT — cc6fb3f renamed _rule_for and skipped CLAUDE.md's rule to grep every
  markdown after removing or renaming a string. Task 5's own plan instructions still said _rule_for.
  Fixed, and task 5's text now also points at the numeric predicate so it does not write a third copy.
Task 2: fix round 1 dispatched — (a) move the numeric predicate into units.py beside _apply as the
  single authority both the check and the collapse read, so task 3's coercion cannot become a second
  one; (b) route an OMITTED collapse to E-DATA-MEASUREMENTS-INVALID, because it currently emits
  E-UNITS-COLLAPSE-RULE whose row says "NAMES a rule that is none of ..." and an omission names
  nothing — which matters more than usual since that code is dual-listed; (c) row 411 says "declared
  and is not a mapping", which as worded refuses init's own `measurements: null` output while the code
  correctly skips None.
Task 2: DEFERRED MINORS (deliberately not widened into the task, recorded so they are not
  rediscovered):
  - collapse: {typo_column: mean} and {7: "mean"} validate clean and do nothing, in tension with the
    rationale used to refuse measurements: {} ("a declaration that changes no behavior is the failure
    this refusal exists to prevent").
  - float()'s grammar accepts "nan", "inf", "1_000", " 10 ", "+5" and unicode digits. Doc and code
    agree so it is a slice decision — but `mean` over a "nan" column yields a silently meaningless
    number, which is exactly what row 243's own rationale objects to.
  - A malformed `by` cascades into a second -COLLAPSE-TYPE finding. Noise, not misdirection, since the
    root cause reports first.
Task 2: CROSS-TASK RISK, now written into the plan rather than living only in a report — task 3 must
  reuse the numeric predicate, not write its own. _apply('mean', ['10','10']) returns the STRING '10'
  today (the constant shortcut fires because the values are not isinstance numeric), so coercion has
  to happen before _apply sees the values; and any coercion must accept exactly float()'s grammar or
  the validate-time and run-time answers part again.
Task 3 PRE-EMPTIVE PLAN FIX (controller, while task 2's fix round ran). My plan told task 3 to store
  technical_n on UnitList "exposed as a read-only property". That WOULD HAVE VIOLATED A DOCUMENTED
  INVARIANT: reference.md § The unit list is three operations and CLAUDE.md both say io.units supports
  EXACTLY three operations — iterate, len, index — plus .train, and UnitList's own docstring says
  "Deliberately not a list. A sequence that also promised slicing, membership and .index would just be
  a list, and core could never change what backs it without breaking every step." io.units IS a
  UnitList handed to steps, so a public technical_n property widens a deliberately narrow surface —
  and a private one with a module-level accessor is the same thing wearing a disguise.
  Fixed: resolve_units now returns a TUPLE (UnitList, technical_n | None). The collapse produces two
  things and the caller that needs both asks for both. Exactly two call sites — validate.py inside its
  except ContractError wrapper, which discards the second element, and cli.py's phase-5 roster
  resolution, which carries it to the record.
  Added a test to the plan that pins the invariant directly rather than trusting the shape:
  `assert not hasattr(roster, "technical_n")`.
  Also verified for task 3: `statistics` is already imported in units.py (task 1 added it for median),
  so the median computation needs no new import.
Task 6 PRE-EMPTIVE PLAN FIX (controller). My plan told task 6 to "edit the whole-leaf passage that
  calls the envelope gap 'latent rather than live'". THAT PASSAGE IS ABOUT `holdout`, NOT
  `measurements` — reference.md's E-CONFIG-KEY-UNKNOWN row says "`holdout` is not among them only
  because the whole block is refused today as E-DATA-HOLDOUT-UNSUPPORTED, which makes its gap latent
  rather than live". holdout stays refused until H3d. Task 6 would have edited a passage about a
  neighbouring block believing it was about its own — the document-defect class this project keeps
  shipping, and the one task 7 of H2 committed at three layers.
  The real enumeration is the closed-schema paragraph naming FOUR whole-leaf blocks the claim excepts:
  a hypotheses entry, a statistics.contrasts entry, a replication.repeats entry of kind seed or fold
  (batch is closed), and the mapping form of data.units.from. `measurements` is NOT among them — it is
  typed as a bare dict in envelope.py but excluded from the list because the block is refused.
  So task 6 has exactly two honest outcomes and step 3 decides which: fully type .by and .collapse, in
  which case measurements never becomes a whole-leaf block and NEITHER passage needs an edit (pin it
  by showing {by: read_id, colapse: mean} now reports E-CONFIG-KEY-UNKNOWN); or fail to, in which case
  measurements becomes a FIFTH live whole-leaf block and must be added to that enumeration with its
  closing slice named. Leaving it typed `dict` while retiring the refusal is the one forbidden outcome
  — that turns a latent gap live without recording it anywhere.
Task 2: fix round 1 landed (e863830). Scoped re-review: ALL THREE FINDINGS CLOSED, NO NEW FINDINGS,
  task 2 complete. 1100 passed + 2 xfailed.
  THE JUDGEMENT CALL, upheld and worth keeping: the implementer deliberately did NOT rewire _apply's
  constant-column shortcut to read the newly shared predicate, arguing that doing so converts today's
  silent-wrong-value into an unhandled bare TypeError — worse, not better — and that the real fix is
  coercion upstream, which is task 3's. Verified by controller and re-reviewer independently:
      is_measurement_numeric("10")  -> True       validate accepts a CSV-sourced numeric column
      _apply("mean", ["10","10"])   -> '10'       constant shortcut fires; returns a STRING
      _apply("mean", ["10","20"])   -> TypeError  bare, no E- code
  The re-reviewer's verdict on whether one shared predicate with two deliberately different uses is a
  single authority or a single NAME over two behaviours: "the opposite of 'one name over two
  behaviors' — it draws the boundary in the open rather than papering over it", because the docstring
  states prominently that _apply's shortcut does NOT read the predicate, and gives the reason. The
  single-authority claim is scoped to validate's check and a FUTURE coercion step, not to the
  pre-existing narrower isinstance gate.
  Predicate move verified verdict-preserving by byte-comparing the removed private copy against the
  new public one and re-exercising bool, "", " 10 ", "nan", "10", "north", 10, 10.5, None, [], {}.
Task 2: complete (commits 41de16c, cc6fb3f, e863830).
Task 3 PLAN ADDITION (controller) — the contract task 3 must honour or the slice ships a config that
  validates and then crashes. Task 3 must coerce numeric-looking strings BEFORE _apply sees them,
  gated on is_measurement_numeric so the two answers cannot part. Two things to TEST, not merely
  implement: a CSV-sourced roster with collapse: mean over a numeric column must collapse to a NUMBER
  (not raise, not return a string); and no path may let a non-ContractError escape resolve_units,
  because validate wraps that call in `except ContractError` only — a bare TypeError would escape
  validate itself and break the hard invariant that it collects findings and never raises. Task 5
  calls _apply directly and inherits the same obligation, though io.record coerces its values, so it
  must CHECK whether that already settles it rather than assuming either way.
Task 3: commit 901276d. Review: spec ✅, APPROVED with findings. 1121 passed + 2 xfailed.
  Controller verified independently: a CSV roster with collapse {depth: mean} over "10"/"20" yields
  ONE unit with depth == 15.0, a real float; technical_n == {min:1,max:2,median:1.5}; and
  hasattr(roster,"technical_n") is False — the three-operations invariant held. Adversarially, mixed
  ["10","north"] and an empty string both raise ContractError E-DATA-MEASUREMENTS-COLLAPSE-TYPE,
  ["nan","10"] gives nan, a single-member group gives 10.0 — nothing escapes as a non-ContractError.
  Through the suite's own fixtures, four malformed measurements shapes all report
  E-DATA-MEASUREMENTS-INVALID without raising, and a valid block does not.
  MY THIRD could-not-fail PROBE: my first attempt to verify "validate never raises" built a config by
  hand and bailed at E-TEMPLATE-UNKNOWN before the measurements checks ran, reporting NOTHING for
  every shape including the control. Only the suite's write_config/codes fixtures reach these checks.
  Standing lesson, now three for three: every probe needs a control that MUST report.
  BRIEF DEFECT, MINE, CONFIRMED: the brief's str(measurements["by"]) raises KeyError on
  {collapse: mean} and AttributeError on measurements: "yes" — and validate._check_units resolves the
  roster BEFORE _check_measurements runs, so those escape validate itself, breaking the hard
  invariant. Fixed by _measurement_axis raising the same E-DATA-MEASUREMENTS-INVALID the shape check
  reports. The reviewer swept 17 measurements shapes x 3 tables = 51 combinations: every one produced
  findings, none raised. The fix is general, not case-by-case.
  Ordering proven load-bearing by the reviewer's own mutation: moving the collapse after the
  uniqueness loop fails test_duplicate_keys_collapse_when_measurements_is_declared plus five others.
  Coercion boundary probed for the gap and none found: coerce_for_rule is gated on
  `rule not in NUMERIC_COLLAPSE_RULES` then on all(is_measurement_numeric(v)), so first/mode over
  "007"/"008" preserve the string; a by column that is numeric is excluded from names and never
  coerced; grammar follows float()'s exactly, so predicate and conversion cannot part.
Task 3: IMPORTANT closed by the controller in 6a6ecb0 rather than routed — is_measurement_numeric's
  docstring was FALSIFIED BY TASK 3'S OWN COMMIT, ~40 lines above the coercion it disclaimed: "which
  today is never coerced" and "neither is reachable today" were both false on landing, and the
  reviewer proved reachability before task 6 by showing COLLAPSE-TYPE reported alongside the
  still-firing -UNSUPPORTED. No scheduled task rewrites units.py, so routing it to task 6 with the
  reference.md rows would have left a live falsehood in shipped code. The two facts it recorded as
  advice for a future implementer are now invariants of how the code is arranged, and stay as such.
Task 3: IMPORTANT routed to task 6 as a HARD PRECONDITION, ranked by the reviewer above the registry
  rows because it is a wrong-answer path rather than a missing diagnostic. measurements.by is never
  checked against the declared attributes. Verified by the controller:
      measurements: {by: nonexistent, collapse: {depth: mean}}
      -> units [('p1', 15.0), ('p2', 35.0)], technical_n {'min':2,'max':2,'median':2.0}
  A typo'd `by` silently averages rows nothing declared to be measurements of one unit and reports a
  technical_n claiming the collapse was intentional. E-DATA-MEASUREMENTS-UNSUPPORTED masks it today;
  retiring that refusal makes it reachable. validate already refuses an unknown attribute elsewhere
  (E-UNITS-ATTR-MISSING) and data.units.attributes is the declared set.
Task 3: technical_n gap — computed and carried NOWHERE. The implementer's deferral reasoning was
  checked by the reviewer and is a REAL document constraint, not a convenient one: reference.md shows
  technical_n inside the METRIC block beside n/repeat_spread/ci95, not in provenance.units, which is
  documented as exactly {n, key} — so parking it there would invent an undocumented run.yaml field.
  Folded into TASK 6, on the grounds that retiring the refusal declares the declaration honoured and a
  feature that collapses replicates without reporting how many is half-delivered. Reviewer agreed task
  6 is the right acceptance gate but added a SEQUENCING CONSTRAINT I had missed: the shape decision
  (how a sibling-of-n travels through counts/summarize_step) is what task 9 was scoped to make, so
  task 6 must either make that decision and have task 9 follow it, or agree the route with task 9
  first — otherwise two tasks invent two routes for one problem. Written into the plan.
Task 3: three stale reference.md bits routed to task 6 (which rewrites those sections): both new
  measurements rows sit only in § Errors validate reports and lack the dual-listing clause
  E-UNITS-COLLAPSE-RULE carries, with no § Errors core raises counterpart; AND COLLAPSE-TYPE's row
  calls is_measurement_numeric "the single authority this check and a FUTURE run-time coercion both
  read", which a row edit that only added the dual-listing clause would have left false.
Task 3: MINOR deferred — collapse: null draws both E-DATA-MEASUREMENTS-INVALID and
  E-UNITS-COLLAPSE-RULE (two findings, one fault), same class as the double-INVALID already recorded.
  Fold into whichever task deduplicates in _check_units.
Task 3: complete (commits 901276d, 6a6ecb0).
Task 4: commit ab6fb2e. Review: spec ❌, two Important, one Minor. Fix round 1 dispatched.
  1127 passed + 2 xfailed. Controller verified the good behaviour first, each probe with a control:
  under a declaring StepIO two measurements of one unit keep both rows and a repeated (unit,
  measurement) is first-write-wins (the later 99 rejected); the plain no-measurement path is untouched
  and still first-write-wins; an undeclared StepIO raises E-STEP-MEASUREMENT-UNDECLARED.
  IMPORTANT 1 — the measurement path bypasses _settle ENTIRELY. Reproduced with controls:
      skip("p1") then record("p1",...,measurement="r1")  -> NO RAISE, row stored, p1 still skipped
        control: skip then plain record                  -> E-STEP-UNIT-SETTLED   (correct)
      record("nonexistent",...,measurement="r1")         -> NO RAISE, unit not in the roster
  _settle does two checks and the measurement path needs one and a half: E-STEP-UNIT-UNKNOWN (roster
  membership) must ALWAYS fire — a measurement of a unit the execution was never given is as wrong as
  a plain record of one. E-STEP-UNIT-SETTLED must fire for an already-SKIPPED unit and must NOT fire
  for an already-MEASURED one: today the check is `unit_key in self._rows or unit_key in
  self._skipped`, and _rows-membership cannot block a second measurement because that is the whole
  feature — but io.skip declares a unit INELIGIBLE, admitting no result by design, and a later
  measurement re-entering it as a completed result is exactly the accounting failure `ineligible`
  exists to prevent. Once task 5 collapses the rows it breaks the reconciliation
  resolved == completed + ineligible + failed.
  IMPORTANT 2 — the measurement path never calls _declared_attributes(), so a measurement row can
  shadow a declared unit attribute where a plain record correctly raises E-STEP-KEY-COLLISION.
  Reproduced with a control. Bites hardest at collapse time, when task 5 folds measurement columns
  into the unit row and two `site`s meet.
  MINOR 3 — the report states `measurement` "must be a plain str" as a decision, but measurement=5 is
  silently accepted and keyed unchanged. Mirrors unit_key's existing laxness so not a regression, but
  claimed-not-provided again. Either enforce it or restate it honestly.
  UPHELD, no change: reserving `measurement` as a structural column name is NOT an invented rule —
  reference.md names measurements.parquet's columns as exactly (unit, measurement), so the report
  undersold its own textual support. And E-STEP-MEASUREMENT-UNDECLARED belongs in § Errors core raises
  with NO dual listing, unlike E-UNITS-COLLAPSE-RULE: validate never constructs a StepIO or calls
  .record, so no validate-time path can reach it. (Task 3 got the mirror of this wrong; here it is
  right.)
  Mutation discipline was thin — one mutation for three changed behaviours. The reviewer mutated the
  other two and both were caught by tests the implementer had written, so coverage was adequate even
  though the demonstrated discipline was not.
Task 5 PLAN ADDITION (controller): runner.py never passes `measurements` to StepIO — verified, its
  single StepIO(...) construction has no such argument — so in a REAL RUN io.record(..., measurement=)
  raises E-STEP-MEASUREMENT-UNDECLARED even when the config declares measurements. The declaration is
  honoured at the input path and refused at the step path. Task 5's first obligation, and it must be
  pinned by a test running a REAL STEP: a directly-constructed StepIO cannot catch it, which is
  exactly how it was missed.
Task 4: fix round 1 landed (a3d8aa2) — _settle decomposed into _check_roster + the settled check; the
  measurement branch calls _check_roster unconditionally then checks only _skipped, so a second
  measurement of an unskipped unit is still allowed; declared-attribute collision check shared.
  1131 passed. Controller verified all four with controls, including the DISCRIMINATING case a naive
  _settle call would have broken (second measurement must NOT raise -> 2 rows).
Task 4: SCOPED RE-REVIEW: finding 1 only HALF closed, and the missing half is MY instruction's fault —
  I named the skip -> measure direction and not its mirror. Fix round 2 dispatched.
      record("p1",{"score":1},measurement="r1"); skip("p1","reason")  -> NO RAISE
      skipped {'p1':'reason'}, measurement_rows 1 — the unit is BOTH ineligible AND measured
      control (the fixed direction): skip then measure -> E-STEP-UNIT-SETTLED   (correct)
  skip() still calls _settle, which checks _rows and _skipped and NEVER _measurement_rows. Same
  accounting failure, reached from the other call order: a unit in both stores breaks
  resolved == completed + ineligible + failed the moment task 5 collapses the rows, being counted
  ineligible while also producing a result.
  Also asked for the full rule to be stated in ONE sentence covering both orderings, in the code, so
  the next reader need not derive it from two guards in different methods: a unit may be measured many
  times, but never both measured and skipped, in either order.
Task 4: ROUTED TO TASK 5 (not a defect, out of finding 1's scope, but task 5 meets it) — plain-record
  and measurement can be MIXED for one unit in either order, leaving it in both _rows and
  measurement_rows():
      record("p1",{"score":1}); record("p1",{"score":2},measurement="r1")  -> NO RAISE, both stores
  Explained by the stated rule (_rows-membership must not block a measurement), but task 5 folds
  measurement rows into unit rows and a unit with both is an ambiguity someone must resolve. Asked the
  implementer to say which it believes is right — refuse the mixture, or define which wins — with a
  document sentence if one settles it, WITHOUT implementing it, so I can route the reasoning.
Task 4: finding 2 and 3 dispositions ACCEPTED — the attribute-collision check is correctly shared, and
  restating the `str` claim as conventional-but-unenforced (consistent with unit_key's existing
  laxness) rather than inventing a coercion was the right call.
Task 5 PLAN ADDITION (controller, verified with a control while task 4's round 2 ran) — THE CENTRAL
  OBLIGATION, which the plan did not state and which is a wrong NUMBER rather than an error:
      io.record("p1",{"score":10},measurement="r1")   # measured only
      io.record("p2",{"score":20})                    # plain, the control
      io.recorded_keys -> ['p2']                      # p1 is ABSENT
  recorded_keys is populated only by the plain branch, and finalize writes units.parquet only
  `if self._rows:` while measurement rows live in a separate store. So a unit that is ONLY measured is
  counted neither completed nor ineligible, which by runner's subtraction makes it FAILED.
  reference.md § The unit table is the inference base states the accounting directly: "completed is
  how many distinct unit keys reached io.record in it — measurements of one unit collapse before they
  are counted".
  So the collapse is not merely about producing a nice table: IT IS WHAT MAKES A MEASURED UNIT EXIST
  to the rest of core. Task 5 must collapse _measurement_rows into _rows and _recorded_keys BEFORE
  finalize's existing units.parquet block, so collapsed units flow through the path that already works
  rather than a parallel one — and must pin the RECONCILIATION, not just the file: a run whose step
  only measures reports completed == distinct units measured, failed zero, and
  resolved == completed + ineligible + failed.
  This is the third distinct way this slice has been able to break that reconciliation (skip->measure,
  measure->skip, and now measured-but-never-counted). Worth noting the pattern for H3b/H3c: every new
  path into the unit table needs checking against n's four parts, not just against its own output.
Task 4: fix round 2 landed (f080564). skip() now calls _check_unmeasured, raising E-STEP-UNIT-SETTLED
  if the unit already has a measurement row — symmetric to record(measurement=) refusing an
  already-skipped unit. Both sites state the unified rule: "a unit may be measured many times, but
  never both measured and skipped, in either order."
  Controller verified all four with controls: measure->skip SETTLED; skip->measure SETTLED; a second
  measurement does NOT raise; skipping an UNMEASURED unit does NOT raise.
Task 4: complete (commits ab6fb2e, a3d8aa2, f080564). 1133 passed + 2 xfailed.
Task 4 -> TASK 5 HANDOFF, with the implementer's recommendation: plain record() and
  record(measurement=) on the same unit still leaves it in both stores with no raise. Its
  recommendation is to REFUSE THE MIXTURE rather than define a winner, because no document sentence
  settles it and a silent winner would apply or skip the declared collapse rule depending on ARRIVAL
  ORDER — which is the retry-versus-measurement ambiguity the measurement= argument exists to remove,
  reappearing one layer down. Task 5 decides; read the report first.
Task 5: commits eef7ff7, a76f0e7, a06bed4. Review: spec ✅, APPROVED, 1 Important + 4 Minor.
  1148 passed + 2 xfailed. Controller verified with controls: a measured-only unit now appears in
  recorded_keys; units.parquet written; measurements.parquet written when a step measured and NOT when
  none did.
  THE SHARPEST PLAN DEFECT OF THE SLICE, found by the implementer: the brief's prescribed mean ->
  median mutation COULD NOT FAIL, because mean and median of [10, 20] are both 15.0. Worse, NO
  existing input-path test distinguished mean from median either — every case was two symmetric
  values. So the slice's central single-source claim (decision 4: one place decides what `mean` means)
  was untested on both paths simultaneously. Fixed with 10/20/60 plus a new input-path test.
  The reviewer verified this with ONE mutation over 576 tests: exactly two failed, the new input-path
  test and the new step-path test, and the step-path one failed from a mutation made ONLY in
  units.apply_rule — which is decision 4's single-source claim PROVIDED rather than stated. None of
  the other 574 failed, which independently confirms nothing pre-existing discriminated the two rules.
  N RECONCILIATION VERIFIED END TO END through execute_plan + attrition, the acceptance test for this
  whole slice: measures+plain+skip+untouched over 2 repeats -> 4 = 2 + 1 + 1; measures 1 of 3 ->
  3 = 1 + 0 + 2; input-path measured roster -> all completed. No unit counted in two parts. All three
  ways this slice previously broke the identity are closed.
  Obligation 3 RULED: refuse the mixture, both orders, on a stronger reason than task 4's — the
  collapse assigns self._rows[unit_key], so refusing is what makes that assignment collision-free,
  and a "winner" would make the declared collapse rule apply or not depending on call order INSIDE
  the step. Reviewer confirmed nothing legitimate is lost: a unit-level covariate alongside
  measurements is still buildable via a `first` rule or a declared data.units attribute.
  Coercion NOT settled by coerce_scalars — it guarantees a scalar, not a number — so coerce_for_rule
  is called on this path too, pinned with "10"/"20" -> 15.0.
  _apply renamed to apply_rule (it now has an out-of-module caller).
Task 5: IMPORTANT closed by the controller — the PLAN FILE still carried 15 `_apply` occurrences, of
  which the current-code descriptions would mislead task 6's implementer, who reads it for cross-task
  context. The reviewer's distinction is worth keeping: dated-plans-as-records is correct for
  CLAUDE.md's mechanical pass, whose enumeration is the four documents + CLAUDE.md + feasibility
  analyses — but it does NOT cover a sentence telling a LATER task where current code lives. Renamed
  throughout. Second time this slice that renaming a symbol left stale instructions behind; both mine.
Task 5: MINOR closed by the controller in 2f8f65f — the two new RUNNER tests recorded 1.0/3.0, whose
  mean and median are both 2.0, inheriting the exact blindness task 5 had just fixed one layer down.
  Now 1, 3, 8 (mean 4.0, median 3.0). Mutation-verified in both directions: the mean -> median
  mutation did NOT fail them before this commit and does now.
Task 5: MINORS accepted, not fixed — parquet type widening in a mixed step (an encoder consequence
  asserted as intended); the bool asymmetry under `sum` (inherited from apply_rule's documented
  constant shortcut and pinned by an existing test, so nobody should "fix" it here); and core now
  being able to raise AFTER a step's run returned successfully, which is pre-existing semantics for a
  failed execution but is why the missing § Errors core raises row matters — the user sees a code with
  no lookup.
Task 5: TASK 6 AMENDMENT written into the plan — step 2b named only resolve_units as the raise
  surface, and `finalize` is now a SECOND one: a step recording a non-numeric value under a numeric
  rule raises E-DATA-MEASUREMENTS-COLLAPSE-TYPE at collapse time. The row task 6 writes must cover
  both paths or it ships incomplete.
Task 5: ⚠️ CARRY FORWARD — execute_plan's measurements threading is test-covered, not type-enforced.
  One call site exists today (cli.py), so no mutation can see a draft/resume caller that does not
  exist yet. Re-opens the moment a second executing command lands (H9 owns draft/resume).
Task 5: complete (commits eef7ff7, a76f0e7, a06bed4, 2f8f65f).
Task 6: commits ed48f75, 7cbc161. Review: spec ❌, ONE CRITICAL. Fix round 1 dispatched.
  1158 passed + 2 xfailed. Controller verified with controls: a valid measurements block reports
  nothing (retirement real); a typo INSIDE the block (`colapse`) reports E-CONFIG-KEY-UNKNOWN (envelope
  children typed); the no-block control reports nothing; E-DATA-MEASUREMENTS-UNSUPPORTED gone from src
  and all four documents; prose count reads "Ten declarations above"; summarize_step gained beside_n
  merged into BOTH the recorded and derived loops. Precondition mutation-discriminating: neutering it
  fails its target test while both controls keep passing.
  CRITICAL, AND IT IS MY BRIEF'S DEFECT — I prescribed `attributes` as the reference set for the `by`
  check and the implementer built what I asked for. The check refuses the exact YAML TWO NORMATIVE
  DOCUMENTS PRINT. Three independent confirmations, checked by the controller:
    - reference.md § What isn't a repeat's fence is from/key/measurements only — NO `attributes` key at
      all. experimental-designs.md § Technical and biological replication carries the same fence.
    - design-principles.md, the TIEBREAKER, lists key, attributes, cluster_by, measurements.by,
      holdout.from, assign.from, stratify_by as PARALLEL field-namers. `by` names an input column in
      its own right; it is not a member of `attributes`.
    - E-UNITS-ATTR-MISSING's own registry row already states the doc-faithful predicate: "names a value
      THE SOURCE TABLE has no column for".
  So the retirement's headline claim — "data.units.measurements is a declaration core honors" — is
  false for the documents' own example, at the very commit that makes it. The wrong-answer class this
  task existed to close, inverted.
  FIX: narrow the predicate to the SOURCE TABLE's columns. Still closes the original path (a typo'd
  `by` names no column) and accepts by: read_id with no attributes declared. The max > 1 GATE SURVIVES
  — the reviewer probed it hard: elif precedence correct, the validate/run window closed because
  command_run validates against the same table it resolves, and the step-path exemption right because
  _collapse_measurements never reads `by`. Only the reference set changes.
  Explicitly REFUSED the other available fix (updating the two fences): design-principles.md settles
  the semantics against it, and changing two documents to match a check is the inverted direction.
Task 6: IMPORTANT — a load-bearing sentence added to reference.md claiming the § The one config file
  fence is what `init` writes is false and self-contradicting (the same paragraph says the section is
  "a wider thing than the literal output of init"), and materialize.py writes different text. It was
  the justification for not expanding the block.
Task 6: THE BRIEF'S PREMISE ON THE REGISTRY ROWS WAS WRONG AND THE IMPLEMENTER CORRECTED IT — I wrote
  that both resolve_units and finalize raise both codes. In fact -INVALID is raised ONLY from
  units._measurement_axis on the input path, while finalize reaches only E-UNITS-COLLAPSE-RULE and
  -COLLAPSE-TYPE. Its rows say what the code does rather than what the brief claimed. Task 9's author
  must not inherit the false premise.
Task 6: three brief defects confirmed by the reviewer, all mine. (i) The brief's step-1 test was
  INERT — write_config's CSV is `patient_id\np1\n`, one column and one row, so the roster fails to
  resolve and the assertion passes without reaching the honoured path. CONTAINED: every earlier
  measurement test that declares attributes writes its own CSV (all checked), and the earlier
  absence-assertions on the default CSV are -UNSUPPORTED-family checks that run before resolution.
  (ii) materialize.py never carried NOT BUILT for ANY block, so that clause was a no-op.
  (iii) The step-5 grep scope was wrong; CLAUDE.md scopes the mechanical grep to the four documents,
  itself, and feasibility analyses, so docs/superpowers/* is correctly outside it.
Task 6: SPLIT-SEAM GATE — the reviewer's answer to "is the measurements half mergeable" is NO until
  the Critical is resolved, and I agree. Everything else is complete and well-evidenced.
Task 6/7 SUBTLETY the controller established while the fix ran — WHAT `by` ACTUALLY DOES, which the
  plan never stated and which settles both the Critical's fix direction and task 7's shape.
  collapse_measurements groups by unit.key and never reads `by`'s VALUE — it uses `by` only to EXCLUDE
  that column from the merged attributes. Consequences, measured:
    - The documents' own fence (from/key/measurements, NO attributes key) "works": 3 rows collapse to
      1 unit, technical_n {min:1, max:3, median:2}. But the units carry NO ATTRIBUTES AT ALL, so
      nothing is averaged — the collapse merely deduplicates. Useless, not wrong.
    - CONTROL with attributes ["read_id","depth"]: depth becomes 30.0, the mean of 10/20/60.
    - So the genuine wrong-answer path is `by: nonexistent` WITH attributes declared: the real
      measurement column survives into the merge and gets collapsed under whatever rule applies.
  This confirms the source-table predicate is both necessary and sufficient: it catches the typo that
  causes the harm, and admits the documented fence, which `attributes` membership would not.
Task 7 NOTE — the weight_by/measurements.by ASYMMETRY IS REAL, do not "fix" task 7 to match task 6.
  reference.md row 292 says weight_by "names `sampling_weight`, which is not a UNIT ATTRIBUTE", and
  the config comment calls it "a unit attribute holding the inverse sampling probability". The
  semantics differ for a reason: weight_by must be readable PER UNIT at analysis time, so it has to
  survive resolution as an attribute; measurements.by is CONSUMED at collapse time and removed from
  the merged unit, so it need not survive at all. Task 7's check against `attributes` is therefore
  correct and is NOT the same defect the task 6 Critical was.
Task 6: fix round 1 landed (3978870). Scoped re-review: ALL FOUR FINDINGS CLOSED, task 6 complete,
  and SPLIT-SEAM VERDICT: YES — the measurements half is merge-ready on its own. 1160 passed.
  The Critical is fixed doc-faithfully: the predicate is the SOURCE TABLE's columns, threaded out of
  the single read _from_table already does (_from_table/_from_glob now return (units, columns);
  resolve_units returns a THREE-tuple). Nothing re-reads the header, so the check's column set and the
  resolution's cannot disagree. Controller verified with a control: the documents' own fence shape
  (by: read_id, NO attributes key) -> []; a typo'd by with attributes declared -> E-UNITS-ATTR-MISSING;
  the valid declared form -> []. Reviewer's mutation pins the FIX ITSELF: reverting the predicate to
  attributes fails test_the_documents_own_fence_shape_is_accepted.
  The max > 1 gate survived intact and both older mutations still discriminate against the moved code.
  Glob case probed on seven adversarial patterns: zero duplicate keys, so the empty column set is
  unreachable by the gate — no false refusal of the Critical's class. Caveat: that rests on pathlib
  dedup behaviour and is asserted in a comment without a pinning test.
  The design-principles.md citation was checked for fabrication (this project has had one) and is
  CORRECT — the paragraph exists and lists the parallel namers as claimed.
Task 6: FOURTH could-not-fail probe by the controller — my first verification wrote reads.csv to the
  wrong directory, so all three cases reported identically (E-DATA-POLICY, E-DATA-REQUIRED) with no
  measurement codes at all, including the case that had to fail. The CONTROL caught it, again. Four
  for four this slice; the harness bails before the checks run and every input looks the same.
Task 6: three of five new Minors closed by the controller in the follow-up commit:
  - Two code comments cited "design-principles.md § The shape your input must have is derived", which
    is a BOLDED PARAGRAPH inside ## Core vs. plugin, not a heading — so the citation resolved to
    nothing, against CLAUDE.md's own cite-by-section rule. Both now name the heading, and both had
    dropped null_test.shuffle from the enumeration while reading as complete.
  - The replacement sentence "a run declares it only when its input carries technical replicates" was
    made load-bearing by the fix and is false in the direction that matters: a step supplies
    measurements through io.record(..., measurement=) with ONE input row per unit, and core refuses
    that call without the declaration — which is the premise the max > 1 gate rests on. Stating the
    input as the only source contradicts the gate's own reason. Both sources now named.
  - The plan's stale two-tuple resolve_units signature (mine) updated to the three-tuple.
Task 6: TWO MINORS ROUTED, not fixed — `by` naming the KEY column passes the header-level check
  (design-principles.md says core enforces the projection "down to values rather than headers"; the
  closing predicate would be "does `by` vary within a key's rows"), and a stale test name in the task
  report. Neither produces a wrong number.
Task 6: complete (commits ed48f75, 7cbc161, 3978870, plus the controller follow-up).
MEASUREMENTS HALF COMPLETE. Reviewer's end-to-end verdict: validate (shape, by, source-column check
  with its gate, collapse rule against the resolved roster's own values, envelope children typed);
  both arrival paths; technical_n carried to run.yaml beside each metric's n when max > 1;
  measurements.parquet written only when a step measured, pinned both ways; and the n reconciliation
  pinned by test_attrition_reconciles_for_a_step_that_only_measures. No half-delivered piece, no known
  wrong-answer path. The two open items are in spec-defects.md rather than silent, and neither
  produces a wrong number.

=== WEIGHT_BY HALF ===
Task 7: commit f510ff9 (+ controller follow-up). Review: spec ✅, APPROVED, 1 Important + 3 Minor.
  1176 passed + 2 xfailed. Controller verified all three checks with controls in one run: weight_by
  naming an undeclared attribute -> E-DATA-WEIGHT-UNKNOWN; a column holding 0 and -2 ->
  E-DATA-WEIGHT-INVALID; a valid weight -> only the still-live -UNSUPPORTED; an undeclared
  sampling_weight -> W-DATA-WEIGHT-UNDECLARED; a FLAT sampling_weight -> nothing; an age-only roster ->
  nothing. Both negative controls for the warning fire correctly.
  TWO MORE BRIEF DEFECTS, MINE, both confirmed by the reviewer directly rather than inferred:
  (i) the brief's isinstance(value, (int, float)) numeric test is wrong because _from_table builds
  attributes from csv.DictReader, so EVERY table-sourced value is a str. It would have reported
  E-DATA-WEIGHT-INVALID against the exact YAML § Weighted samples prints, AND — worse — the identical
  test inside the warning loop would have `continue`d on every column, making W-DATA-WEIGHT-UNDECLARED
  A CHECK THAT COULD NOT FIRE, whose negative test passes vacuously. The same CSV-string trap task 2
  hit; my plan code repeated it one half later.
  (ii) the brief routed a wrongly-typed weight_by into the "is empty" message, duplicating
  E-CONFIG-TYPE.
  THE NAME HEURISTIC — kept, and the reviewer's justification is better than the implementer's and
  worth carrying: CLAUDE.md's core-vs-plugin test asks whether a CAPABILITY would be identical across
  domains; this gates ONLY A WARNING — it refuses no config, changes no computed value, and alters
  nothing in the record but what core says it was unsure of. Domain leakage matters where it changes
  what core computes or refuses, and it does neither. The document-leads process was followed
  correctly (prose moved first, states the test, concedes it is the weakest part, names the exact
  failure mode). And the alternative is real but out of scope: it is name-test-or-no-warning, because
  positive-varying-numeric has no structural discriminator — age, dose and latency are shape-identical
  to a weight — and dropping the warning means deleting a pre-existing § Validation row.
  ASYMMETRY VERIFIED, not assumed, with primary evidence the reviewer re-checked: _from_table builds
  attributes={a: row[a] for a in attrs} from decl["attributes"], so an undeclared CSV column does not
  survive resolution. There are exactly two sources and no third path can supply an attribute. The
  glob consequence is truthful in both directions: a glob + weight_by -> E-DATA-WEIGHT-UNKNOWN naming
  that the source declares none; the same config WITH the attribute declared -> E-UNITS-ATTR-MISSING
  from _from_glob and no weight finding.
Task 7: two Minors closed by the controller — the W- row said "its name contains `weight`" while the
  code lowercases first (SamplingWeight warns and the row denied it), and the prose called this "the
  same warning as the undeclared-cluster one", true of the REASON and misleading about the MEANS. A
  cluster is structurally distinctive (few distinct values, many units each) so that warning needs no
  guess about a column's name; a weight has no such shape. Saying so is what stops the next reader
  re-litigating the name test.
Task 7: IMPORTANT left open deliberately — no spec-defects.md entry recording that a stated principle
  (core-vs-plugin) was traded against for the name test. The reviewer's ruling makes the trade
  defensible, but CLAUDE.md's document-leads rule has two halves and only one was done. Note that
  spec-defects.md is gitignored, so this record does not survive a merge either way — the durable form
  is the § Weighted samples prose, which now carries the reasoning.
Task 7: MINOR routed into TASK 8's plan — _usable_weight (positive, finite, numeric via
  is_measurement_numeric) is PRIVATE to validate.py, and it is the predicate validate approves a
  config against. If the weighted mean is built on a different notion of a usable weight, the slice
  re-opens the validate-clean-then-crash gap tasks 2 and 3 closed. Task 8 must PROMOTE it beside
  is_measurement_numeric in units.py and have both readers share it, mutation-tested so that changing
  the predicate fails a test in BOTH test_validate.py and test_stats.py.
Task 7: complete (commits f510ff9, plus the controller follow-up).
Task 8: commit 35d1ef8. Review: spec ✅ (with one deviation to record), APPROVED, 1 Important +
  4 Minor. 1194 passed + 2 xfailed. Fix round 1 dispatched.
  THE SLICE'S MOST CONSEQUENTIAL BRIEF DEFECT, MINE, AND STATISTICAL RATHER THAN PROCEDURAL: my
  variance denominator was `/sum(w)`, the POPULATION form, against a t_over_units that uses n-1. At
  equal weights it gives (1.2440, 4.7560) where the unweighted is (1.0368, 4.9632) — NARROWER than the
  sample supports, which is the precise failure § Weighted samples exists to prevent, and it fails the
  brief's own boundary test. The implementer caught it before writing and replaced it with
  `sum(w) - sum(w^2)/sum(w)`.
  The reviewer confirmed the replacement is right FOR THE RIGHT REASON, not merely for the boundary:
  it is the reliability/probability-weight unbiased form (gsl_stats_wvariance, Stata's aweight), which
  is exactly the inverse-probability semantics § Weighted samples declares. All three claimed
  properties verified — reduces to n-1 at equal weights (matching t_over_units digit for digit),
  invariant to rescaling (checked analytically and empirically at x10^6), and errs wide ANALYTICALLY
  rather than by sampling. The Hájek/linearization sandwich alternative was rejected ON THE BOUNDARY
  rather than on width: at equal weights it gives SE 0.6325 against the unweighted 0.7071, so it
  cannot reproduce t_over_units, which the document and the brief both mandate.
  MY HEADLINE TEST COULD NOT KILL ITS OWN MUTATION — the fifth could-not-fail check in this slice and
  the most pointed, since the whole point of task 8 was that one assertion. With df mutated to
  len(values)-1 the weighted width is 22.94 against an unweighted 4.10, so "wider than unweighted"
  passes. Verified by the controller independently. The replacement is non-circular: weights [1,1,1,3]
  make Kish EXACTLY 3 (36/12, no float slack), so the expectation comes from the already-trusted
  t_over_units over three literal points whose df=2 is baked in independently of the code under test.
  The reviewer applied three mutations — df alone, sem alone, and BOTH — and all three fail it, so an
  implementation that never computes Kish at all is pinned.
  Two further brief defects: the headline test's own weights returned None (Kish 1.791, under the
  brief's own effective < 2 guard), and the files list omitted units.py/validate.py which the brief's
  own text mandates.
  SHARED PREDICATE PROVIDED, NOT STATED: _usable_weight promoted to units.usable_weight, and TWO
  different mutations (is_measurement_numeric -> isinstance; dropping the finiteness check) each fail
  tests in BOTH test_stats.py and test_validate.py.
  _t_critical extracted with both call sites changed in one commit, and verified behaviour-preserving
  by 500 random t_over_units + 500 paired_t_over_units calls against the pre-commit module: zero
  differences, with a deliberately-mismatched control that reported 1. No third critical-value
  construction survives.
Task 8: IMPORTANT, worse than disclosed, fix dispatched — kish_effective_n silently returns garbage.
  Controller-reproduced with a working control (equal weights -> 4.0):
      negative [-1,1] -> 0.0     silent
      nan  [nan,1]    -> nan     silent, and this is what would reach run.yaml
      inf  [inf,1]    -> nan     silent
      zeros [0,0]     -> 0.0     silent
      str  ["1","3"]  -> TypeError, no .code
  It is a PUBLIC function in a pure module returning a plausible-looking number for input it cannot
  handle, and task 9 wires it onto the roster's weight column, which is `str` under _from_table. An
  `effective: nan` in run.yaml is a wrong number with no error. RULED: gate inside kish_effective_n
  using units.usable_weight, not in task 9 — the function is public, the guarantee belongs to it, and
  a caller that must remember to pre-validate eventually forgets.
Task 8: RULED, no change — stats raising E-DATA-WEIGHT-INVALID is NOT a code-family violation. The
  reviewer found the precedent: E-DATA-MEASUREMENTS-COLLAPSE-TYPE is documented as "Raised at run time
  too, under the same code" and carries rows in BOTH tables, for the identical single-authority
  reason. The owed registry row lands with the wiring in task 9 or 11.
Task 8: PLAN CORRECTED — the Global Constraint "stats.py is pure" said "imports only errors and
  replication", which stopped being true when stats gained publishable.units for the shared predicate.
  Still acyclic (units imports only publishable.errors) and still pure in the sense that matters — no
  filesystem, no config/artifacts/cli — but the stale phrasing is now explicitly retired.
Task 8: fix round 1 landed (0278926). Scoped re-review: ALL THREE CLOSED, NO NEW FINDINGS, task 8
  complete. 1203 passed + 2 xfailed. The gate lives inside kish_effective_n via a shared
  checked_weights that weighted_t_over_units also calls — ONE gate rather than two, units.usable_weight
  still the single authority, E-DATA-WEIGHT-INVALID the single identifier.
  Controller verified on the settled tree with a control: equal weights -> 4.0; negative, nan, inf,
  all-zero and non-numeric str all raise E-DATA-WEIGHT-INVALID; and the case task 9 actually hits,
  kish(["1","1","1","3"]) -> 3.0, still WORKS rather than raising. Boundary still exact, empty
  sequence still 0.0.
  Single authority re-proven AFTER the refactor moved the gate: mutating usable_weight fails 4 tests
  in test_stats.py and 3 in test_validate.py.
  No regression smuggled into the guard: the reviewer re-probed the equal-weights boundary, the uneven
  headline case, the exact-Kish-3 df case (bit-for-bit) and rescaling invariance at x100.
  The `Any` annotation was checked for being a typing hole and is not one — mypy still reports
  arg-type errors for a non-Sequence argument; widening the ELEMENT type does not weaken container
  checking.
Task 8: CONTROLLER PROCESS ERROR, worth keeping. I probed the working tree and cleared __pycache__
  WHILE THE IMPLEMENTER WAS STILL EDITING, then reported "7 failed" as a fact about the commit. It was
  an artifact of my own timing: git status showed `M src/publishable/stats.py` in the same output and
  I read past it. A clean status immediately after a commit tells you nothing if the agent's next edit
  is thirty seconds away — the check is git status PLUS file mtimes. Same defect class as the five
  could-not-fail probes: a measurement reported as a fact about the code when it was a fact about the
  harness. Do not probe or clear __pycache__ under an active implementer.
Task 8: complete (commits 35d1ef8, 0278926).
Task 9 CARRIES: (a) task 6's route — a key that JOINS n travels in summarize_step's `counts`, a key
  that sits BESIDE n travels in `beside_n`; `effective` joins n so it is counts work, and
  `weighted_by` sits beside it. (b) counts is typed dict[str, int] and MUST BE WIDENED for Kish's
  fractional size. (c) The owed registry row: E-DATA-WEIGHT-INVALID is registry-listed validate-only
  but stats raises it at run time; the precedent for dual-listing is E-DATA-MEASUREMENTS-COLLAPSE-TYPE
  ("Raised at run time too, under the same code", rows in both tables). Due with the wiring.
  (d) kish_effective_n now accepts CSV-shaped numeric strings, so no pre-coercion is needed — but it
  RAISES on a bad weight, and validate only guarantees usability when it actually ran.
Task 9: commits 2836af1, 2cdd197. DONE_WITH_CONCERNS — one BLOCKING hand-off. 1208 passed + 3 xfailed
  (was 1203 + 2). runner.attrition gains `weights` and routes all three return sites through one
  _counts builder that adds `effective` (Kish over the COMPLETED units' weights) only when weighting is
  declared; summarize_step's counts widened dict[str,int] -> dict[str,float]; weighted_by rides
  beside_n, exactly the route task 6 decided. reference.md gained the owed E-DATA-WEIGHT-INVALID
  run-time row with the dual-listing clause, mirroring E-DATA-MEASUREMENTS-COLLAPSE-TYPE.
  run_record.py needed no change — the brief's file list was wrong; it copies `aggregated` verbatim.
  Three mutations, each killed by a named test asserting EXACT numbers (36/12 = 3.0 vs 256/112 vs 4.0)
  rather than directions: unconditional effective, resolved-instead-of-completed, unconditional
  weighted_by.
Task 9: THE BLOCKING FINDING, and a genuine gap in MY PLAN rather than in the task — NOTHING CALLS
  weighted_t_over_units. Controller-confirmed: the only mentions outside stats.py are COMMENTS
  (cli.py:726, units.py:426). So a weighted run records weighted_by and n.effective beside an
  UNWEIGHTED mean and interval — the exact risk this slice's spec names first, "a declaration accepted
  whose effect is not delivered". Latent only because E-DATA-WEIGHT-UNSUPPORTED refuses every config
  declaring weight_by; TASK 11 RETIRES THAT REFUSAL, which turns it live. Same shape as task 6's
  precondition: retiring a refusal makes a latent defect live.
  The plan had no task owning the wiring — task 10 was scoped to the percentile path only, task 11 to
  the retirement. TASK 10 WIDENED to own it, since it already owns "the weighted statistic reaches the
  estimate", which keeps task 11's retirement clean.
  The site is summarize_step's recorded-column loop: BOTH `interval = t_over_units(values)` and
  `"value": mean_of(values)` must become weighted — § Weighted samples says the construction uses the
  weighted MEAN and the weighted variance, so wiring only the interval leaves the point estimate
  unweighted and would pass any test checking only the interval.
  Two things task 10 must test rather than assume: the weight vector must be filtered and ordered the
  same way `raw` is (a misalignment silently weights the wrong unit and produces a plausible number),
  and a DERIVED metric has no per-unit vector to weight, so what happens to it must be read out of the
  documents rather than chosen.
  Task 9 left an xfail(strict=True) end-to-end pin that will XPASS-FAIL the suite the moment task 11
  retires the refusal — a deliberate forcing function so this cannot be forgotten. That is why the
  suite is now at 3 xfailed.
Task 9: BRIEF DEFECT — the weighted assertions cannot live in test_cli.py today, because every
  run.yaml test goes through command_run, which validates first and the refusal is still live.
  Positive tests are in test_runner.py/test_stats.py; test_cli.py carries the negative regression plus
  the xfail pin.
Task 9: review spec ✅, APPROVED, 2 Important + 2 Minor, all closed by the controller.
  Conditionality PASS across all three attrition return sites, now routed through one _counts builder.
  Semantics confirmed right in the first place: effective is Kish over the COMPLETED units, matching
  § Weighted samples' own printed shape (completed: 228 against effective: 191.4, "df came from 191
  rather than 228").
  Weight alignment PROBED WITH EXACT VALUES rather than a direction: a roster of 5 weighted 1/1/2/4/8
  with p0-p2 completed, p3 skipped, p4 failed gives effective == 2.6667 == 16/6, against 2.9091 with
  the skipped unit and 2.9767 with everything — three DISTINCT numbers, so a misalignment could not
  have passed. report_by strata each recompute their own (4/2 = 2.0 and 16/10 = 1.6 against a parent
  3.0).
  counts widened to dict[str,float] without the four existing parts becoming floats — the reviewer
  read the run.yaml TEXT from a real unweighted run (resolved: 10, no .0 anywhere), since the cli-side
  isinstance check cannot see it (10 == 10.0).
  IMPORTANT 1 — THE FORCING FUNCTION DID NOT FORCE THE RIGHT THING. The strict xfail asserted
  weighted_by, n.effective and n.completed and NOTHING about `value`. Its fixture is pred = 0/1/2/3
  under weights 1/1/1/3, so unweighted mean 1.5 and weighted mean 2.0 — the test would XPASS the
  instant the refusal retires WHETHER OR NOT the estimator was ever wired. Identical defect to task 8's
  headline test, reappearing inside the guard against it. Closed: the pin now asserts
  aggregated["pred"]["value"] == 2.0, on `pred` (a recorded column core weights) and deliberately not
  `total` (derived, handed to aggregate to weight itself — a decision task 10 owns).
  IMPORTANT 2 — checked_weights' docstring still said "§ Errors core raises OWES this code a row" and
  that same commit ADDED the row. The grep-after-a-string-changes pass, missed in the code->doc
  direction. Third time in this slice a doc/comment was falsified by its own or an adjacent commit.
  MINOR closed — the cli ⚠️ comment now also names what the wiring must settle: summarize_step
  recomputes `completed` PER COLUMN while `effective` is computed once per condition, so a ragged
  column prints a small `completed` beside an `effective` from a larger set, and the two numbers a
  reader is invited to compare would not describe the same units.
  MINOR recorded, not a defect — _counts indexes weights[k] and would raise a bare KeyError for a key
  absent from the dict, unreachable from cli.py since it builds over the whole roster; and an unusable
  weight on a unit that never completes is silently tolerated at run time, which is right, but means
  the run-time gate is per-completed-unit rather than roster-wide as the registry row's wording could
  suggest.
Task 9: complete (commits 2836af1, 2cdd197, plus the controller follow-up). 1208 passed + 3 xfailed.
Task 10: commit dcf1ebc (+ controller follow-up 11fb33c). Review: spec ✅, APPROVED, 2 Minor.
  1219 passed + 3 xfailed. Controller verified with a control over pred = 0/1/2/3 under weights
  1/1/1/3: unweighted value 1.5 / ci95 [-0.554, 3.554] / method t_over_units / NO effective key;
  weighted value 2.0 / ci95 [-1.513, 5.513] / method weighted_t_over_units / effective 3.0. Both the
  mean AND the interval are weighted, and `method` records which construction ran.
  WHAT THE REVIEWER DID THAT IS WORTH COPYING: it noticed the implementer's four alignment mutations
  ALL CHANGED THE VECTOR'S LENGTH, which zip(strict=True) turns into ValueError — so they proved the
  strict zip, not the key mapping. It then applied a SAME-LENGTH WRONG-KEY mutation, which is the one
  that produces a plausible number, and three named tests caught it. Ragged-column probe gave three
  distinct values (2.0 / 4/3 / 0.8) so a misalignment could not have passed.
  effective is now recomputed PER COLUMN, settling the caveat task 9 recorded. Citation checked and
  verbatim: § The three-part n says "by `effective` whenever weight_by makes Kish's size THE ONE THE
  INTERVAL WAS COMPUTED AT". Consequence verified exactly: pred -> completed 3, effective 25/11 over
  its three carriers' weights; other -> completed 4, effective 36/12 = 3.0. Same units, both columns.
  DERIVED-METRIC RULING confirmed against the documents rather than accepted: § Weighted samples has
  core compute weighted means for basis: units COLUMN metrics and hand the column to aggregate "like
  any other attribute so a derived metric can weight itself". Structurally sound because
  E-DATA-WEIGHT-UNKNOWN requires weight_by to name a DECLARED attribute and _attributed merges declared
  attributes into the rows aggregate receives, so the weight column always arrives.
  Percentile: sorted(zip(values, weights, strict=True)) sorts TUPLES so pairs travel together; the
  separate-sort mutation fails exactly one named test, draw-weighting fails three. No Kish floor,
  correctly — a percentile interval has no df and the floor would null the fixture.
  BIT-IDENTICAL verified independently by loading 1a011c6:stats.py via importlib alongside HEAD, with
  the trap named: Interval is a dataclass so cross-module == is always False on class identity, so the
  comparison must be by fields. Identical across seeds 1/7/12345/2026/2/99, draws 1000/2000,
  confidence 0.9, and both None boundaries.
  Wiring completeness: exactly three summarize_step call sites outside stats.py, all in cli.py, all
  passing weights. None reachable by a test until the refusal retires — but task 9's strict xfail pins
  pred.value == 2.0 and would catch a dropped main site the moment it does.
Task 10: MINOR closed in 11fb33c, and MY FRAMING OF IT WAS WRONG, corrected here — I called it a
  seventh could-not-fail check. It was narrower: counts carried effective = 3.0, the value attrition
  really computes, and `other`'s recomputed size is ALSO 3.0, so both of ITS assertions held against a
  setdefault-shaped implementation. `pred` caught that mutation on its own, so the test could always
  fail; two of its four assertions just could not. counts now carries an impossible 99.0.
Task 10: MINOR accepted, no change and no spec change — a derived metric carries weighted_by and the
  condition-wide effective while percentile_of_derived is unweighted, so `effective` names a size its
  interval was not computed at. NOT a defect: § Weighted samples' own worked example is `r`, a DERIVED
  metric shown with weighted_by and effective: 191.4, and task 9's xfail pins total's effective == 3.0.
  A tested, document-sanctioned decision.
Task 10: complete (commits dcf1ebc, 11fb33c).
USER RULING on the contrast gap: NARROW REFUSAL, DEFERRED TO H4. weight_by becomes legal except in
  combination with a contrast (sweep.baseline or statistics.contrasts), on H2's E-SWEEP-SAMPLE-BASELINE
  precedent — H2 retired E-SWEEP-BASELINE-PARTIAL and minted a narrow code for the combination it had
  just made reachable but could not yet compute. Task 11 owns it; the spine is amended so H4 owns
  lifting it alongside the paired estimator family (paired_t_over_units, paired_delta_of_derived,
  paired_percentile_of_derived) it already owns.
Task 11: commits b36b1b6, 3c2e6d6 (+ controller follow-up 2db57a6). Review: spec ✅, APPROVED, one
  Important + one Minor. 1226 passed + 2 xfailed — DOWN from 3, because the forcing function fired.
  THE DEVIATION FROM MY BRIEF IS AN IMPROVEMENT, and the reviewer tested it hard. My brief said refuse
  weight_by + sweep.baseline. The implementer MEASURED the blast radius first and found a bare
  baseline expands to one is_baseline row which resolve_contrasts skips as an `of` — zero comparisons,
  no wrong delta. So the guard reads the RESOLVED FAMILY (comparisons > 0) rather than the
  declaration, which is both narrower AND wider in the right places: it also catches a declared
  statistics.contrasts over a sweep with no baseline, which a declaration-shaped guard would miss.
  Controller-verified with a control: weight_by alone -> clean; + BARE baseline -> clean; + baseline
  AND grid -> E-DATA-WEIGHT-CONTRAST; no-weight + baseline and grid -> clean.
  Reviewer probed nine shapes each with an unweighted control — per-cell baseline, ablate, paired,
  sample, a `within` selecting nothing, report_by, grid-with-no-baseline, contrasts-with-no-sweep, and
  an empty weight_by. NO under-firing and NO over-firing found. The widening mutation
  (comparisons > 0 -> >= 0) kills exactly three tests including the axis-free-baseline and report_by
  edges, so the narrowness is PINNED rather than incidental.
  Harm confirmed real: paired_t_over_units, paired_delta_of_derived and paired_percentile_of_derived
  take no weights parameter at all, so every refused config would have published an unweighted delta
  beside weighted per-condition values.
  FORCING FUNCTION FIRED HONESTLY — git diff over the test shows the hunk removes the xfail decorator
  and NOTHING ELSE; the body including `assert pred.value == 2.0` is byte-identical to the
  strengthened version. It passes unmarked. No expectation moved.
  Both previously-untestable call sites now pinned by end-to-end runs with exact numbers, each
  mutation-verified: dropping weights from the collision-retry summarize_step kills exactly one named
  test (2.0 vs 1.5), from the report_by one exactly another (stratum 0.75/1.6 vs 0.5/2).
  MY REGISTRY INSTRUCTION WAS HALF WRONG and the implementer corrected it: the codeless § Validation
  CHECKS table also carries sibling rows for E-SWEEP-SAMPLE-BASELINE and E-SWEEP-ABLATE-CROSSED —
  invisible to an identifier grep — so the new refusal needed a row there too, not only in the
  registry.
Task 11: IMPORTANT closed by the controller in 2db57a6 — the clause the implementer had JUST rewritten
  to fix a different staleness was still false, in the same class: it promised `.cluster_by` and
  `.holdout` would "inherit the same treatment" (sub-key closure) while asserting one sentence later
  that `.weight_by` needed none of it because a string naming an attribute has no sub-keys. envelope.py
  types data.units.cluster_by as `str`, IDENTICALLY to weight_by; measurements/holdout/assign are the
  dicts. So the edit drew the right distinction and put one of the two string leaves on the wrong side
  of it. `.holdout` and `.assign` are the two that genuinely inherit it.
Task 11: MINOR recorded, no change — the justification for the checks-table sibling row overreached:
  E-SWEEP-SAMPLE-BASELINE is a build-state refusal but E-SWEEP-ABLATE-CROSSED is a PERMANENT design
  refusal, so only the first is the true precedent. The shipped row and its phrasing are correct.
Task 11: complete (commits b36b1b6, 3c2e6d6, 2db57a6). WEIGHT_BY HALF COMPLETE — reviewer's verdict:
  mergeable. E-DATA-WEIGHT-UNSUPPORTED gone from src and all four documents (self-tested); NOT BUILT
  count reads Nine; envelope's weight_by leaf verified `str` so no whole-leaf closure was owed.
Task 12: commit 313bc97. PASS — H3a's exit criterion is met. 1226 passed + 2 xfailed.
  Two defects found and fixed: five TEST DOCSTRINGS cited § Validation rows by the stale numbers the
  brief warned about (243/291/292x2/293), now citing the stable TITLE; and envelope.py still named
  E-DATA-MEASUREMENTS-UNSUPPORTED in an explanatory comment, rewritten so the retirement check stays
  clean on future slices. The tests/ mentions are retirement GUARDS and were deliberately kept.
  Controller re-verified independently with controls: both retirements clean in src and all four
  documents while a live code (E-DATA-HOLDOUT-UNSUPPORTED) reports; NOT BUILT reads Nine;
  partition_units byte-identical by AST BODY COMPARE while resolve_units reports DIFFERENT (the
  single diff hit was a context line, not a change).
  Implementer's proofs: md-direction control printed five rows for two live codes; the worked example
  was proven unmoved by a REAL TEMPORARY COMMIT mutating 0.581 -> 0.582, which the probe caught before
  reset --hard; the four H3a rows each have a check, the implied identifier, and a validate-path test
  with a discriminating negative twin.
Task 12: BRIEF DEFECT #14, MINE — step 3's registry counts were wrong. § Errors validate reports goes
  65 -> 71, not 69: six rows added, three of them dual-registry, and neither counting convention
  yields 69. Warnings 18 -> 19 was right. No document states a count so nothing needed fixing, but the
  number must not be copied forward.
Task 12: THE IMPLEMENTER'S OWN MECHANICAL SCRIPT INITIALLY REPORTED NOTHING FOR EVERY INPUT — a
  hard-coded root read the pristine repo regardless of the path handed to it. Caught by its seeded
  defect control. That is the eighth instance in this slice of a check that could not fail, and the
  fifth caught by a control rather than by luck.
Task 12: MY "known false positive" ANCHOR LIST WAS ITSELF STALE — correcting the script's slugger
  turned all three (secrets--credentials, naming-conventions--repeat-defaults, the executions.jsonl
  heading) into genuine passes, and the final run was made with the suppression list EMPTIED. A
  suppression list is a place stale claims hide; it should be re-derived, not inherited.
Task 12: THREE ITEMS FLAGGED, all pre-existing on main and out of scope — eight codes are emitted and
  documented nowhere (E-CODE-DIRTY, E-GIT-NO-REPO, E-RUN-LOCKED among them); validate.py cites the
  gitignored spec-defects.md, a citation that outlives the file; and condition-text verification of
  the new registry rows was owned by tasks 2-11 rather than this pass, stated explicitly so it is not
  assumed covered.
Task 12: complete. ALL 12 TASKS DONE.

## Whole-branch review
Verdict: APPROVE WITH FINDINGS. One Important + four Minor. 33 commits, 14 files, +4061/-101.
F1 IMPORTANT — A DEFECT THAT EXISTS ONLY IN THE COMBINATION OF THE TWO HALVES, which is exactly what a
  whole-branch review is for and what "the halves share nothing" hid. With both measurements and
  weight_by declared, the weight column is collapsed like any other attribute, so validate reads
  POST-collapse values and units.usable_weight — the single authority — never sees what the config
  declared. Controller-reproduced:
      collapse {w: sum}, p1's rows carrying 1 and 99 -> p1's weight becomes 100.0, a number no row
        declared. Validates clean, exit 0, and p1 stands for 100 units of population.
      collapse {w: first}, p2's rows carrying 3 and -5 -> rows as 3,-5 ACCEPTED; rows as -5,3 REFUSED.
        Same data, permuted, opposite verdict.
  Why no task saw it: task 6 closed the measurements half, task 7 opened the weight half, and no task
  owned the combination. E-DATA-WEIGHT-UNSUPPORTED masked it until task 11.
  USER RULING: document the rule, route the check. § Weighted samples' "Three interactions worth
  knowing" is now FOUR, stating that a weight must not vary within a unit's measurement rows, with
  both failure shapes named. Stated in reference.md rather than spec-defects.md deliberately — that
  tree is gitignored and the record would not survive the merge, which is the same reasoning that made
  F3 worth fixing.
  Structurally the SAME finding task 6 already routed ("`by` naming the key column; the closing
  predicate would be 'does `by` vary within a key's rows'") applied to weight_by's column instead.
F3 MINOR closed — E-DATA-WEIGHT-CONTRAST's owner claim lived only in the gitignored spine amendment.
  Its reference.md row now names the three paired estimators that have to take weights, so the durable
  half says what has to change even though it cannot name a slice.
F2 MINOR closed — the plan's "two independent halves that share nothing" is inaccurate twice over:
  usable_weight reads is_measurement_numeric (deliberate, one-way), and the halves share the F1 failure
  mode. Corrected in the plan's Architecture line.
F4/F5 MINOR, accepted, no change — weighted_by on a DERIVED metric records a claim about what a
  template did, which core cannot verify; the shipped `generic` template derives nothing, so no shipped
  path is affected, and § Weighted samples' own example (`r`) sanctions the shape. The ragged-column
  break of the n identity is on main (stats.summarize_step's {**counts, "completed": len(values)}),
  pre-existing and not the branch's.
Reviewer's independent verifications worth keeping: the n identity holds in the combination no single
  task tested — measure + plain record + skip + untouched, under weight_by AND measurements AND
  report_by, at top level and per stratum; a 336-combination validate-never-raises fuzz with zero
  raises, PROVEN able to fail by a seeded KeyError/TypeError defect; partition_units AST-identical to
  main; and the undocumented-code count went 21 on main -> 19 at HEAD, so the branch made that better
  rather than worse.
ALL LEDGER DEFERRALS TRIAGED MAY-SHIP. The one structural note: docs/superpowers/ is untracked, so
  every "recorded in spec-defects.md" disposition in this ledger is transient — which is why F1's rule
  and F3's owner both went into reference.md instead.

# SDD ledger — plan: docs/superpowers/plans/2026-08-09-units-and-inference-base.md

Branch: s2-units-and-inference-base (in-place; docs/superpowers is gitignored so a worktree would not contain the plan)
Base: 36f9a0d9e5c968b9a61c206cba395a5ba1aaf76a

Pre-flight scan (before Task 1): two plan defects found and fixed, both would have failed
  at runtime rather than being caught by review —
  (a) a test used `io.repeat`; `repeat` is on the STEP (self.repeat), not on io
  (b) test_collapse_averages_a_unit_across_repeats called _two_repeat_results(), which the
      plan never defined. Replaced with a concrete _result() helper plus a second test that
      collapse ignores other steps and non-repeat scopes.
Task 1: complete (commits 36f9a0d..42a9c24, review clean, no fix round)
  numpy/scipy/pyarrow added; stats.py verified pure (imports from a dir with no repo/config).
  Controller checked t against four published values (df=1,4,9,29) — all exact.
  Reviewer mutation-tested z-for-t: 3 of 8 tests failed incl. the wider-than-normal property
  test, confirming it is not circular. Interval bounds are Python floats, not numpy scalars.
Task 2: implemented (commit d8a79fd) DONE_WITH_CONCERNS — implementer escalated that a glob
  matching zero files returns an empty UnitList silently. Controller found the table path has
  the same hole masked: an empty table refuses, but via the key-column check, so the user is
  told "index.csv does not have patient_id (columns: )" and goes hunting for a typo.
  Ruled: refuse an empty roster from either source, E-UNITS-EMPTY. The reason that decides it
  is downstream and invisible from units.py — a later task's attrition check guards on
  `if counts["resolved"]`, so a zero-unit roster does not just produce empty results, it
  silently disables the max_failed_fraction guard too.
Task 2: fix round 1/5 (E-UNITS-EMPTY from either source; commits d8a79fd..f5642eb) — verified
  it discriminates: empty table -> E-UNITS-EMPTY, misspelled key with rows -> KEY-MISSING.
Task 2: fix round 2/5 dispatched — reviewer found the four-operation contract is NOT enforced.
  MY test checked hasattr for named methods, so it passed green while slicing returned a plain
  list and `in`/`reversed()` worked via protocol fallback. Plan test corrected to exercise the
  operators.
  Ruled FIX: __getitem__ rejects a slice (E-STEP-UNITS-CONTRACT) — slicing returns a FOREIGN
    TYPE, which is the actual leak; a step that slices then writes list-shaped code.
  Ruled FIX: Unit.attributes wrapped in MappingProxyType — one roster is shared across every
    condition, so in-place mutation would change what a later condition measures while
    units_hash, computed once, still described the old roster.
  Ruled NO: `in` and `reversed()` stay. Both DERIVE from the three promised operations, so no
    backing that honours the contract can fail to provide them; blocking them would mean adding
    methods to a class whose point is having none. Distinction ledgered.
Task 2: fix round 2/5 (3 addressed; commits f5642eb..40c3313). Reviewer confirmed the new
  slice test fails if the check is removed, the dict copy is genuine, and the empty/key-missing
  discrimination did not regress. bool excluded from the integer check — good catch by the
  implementer, since bool is an int in Python and units[True] would silently mean units[1].
Task 2: complete (commits 42a9c24..40c3313, review clean)
Task 3: implemented (commit a49854d) — all seven refusals verified by the controller firing
  individually; reviewer verified they also fire in COMBINATION (validate collects, not stops).
  Retired code grep-clean. allocation:within and null sub-fields accepted.
  Implementer caught a self-contradiction in MY brief: its test asserted the literal string
  "E-DATA-UNITS-UNSUPPORTED" not in found, which would itself violate the grep-clean
  requirement the same task imposed. Swapped to a generic endswith check — upheld on review.
Task 3: fix round 1/5 dispatched — Important: E-DATA-ALLOCATION-UNSUPPORTED's message reads
  as "your config is wrong, use within" rather than "not built yet". Six of seven carry the
  deferral clause; this one didn't. The distinction is the point of the -UNSUPPORTED family:
  the identifier tells a tool what happened, the message tells a person whether to change
  their config or wait.

*** BLOCKING CONDITION FOR DECLARING S2 COMPLETE (raised by the Task 3 reviewer) ***
  resolve_units is not yet called from command_run/execute_plan. A config with a supported
  data.units block now validates clean, runs, exits 0, and the roster is never touched. This
  is NOT a Task 3 defect — its brief scoped validate.py only — and nothing lies yet, because
  run_record has no units fields to be wrong. Tasks 6-10 wire it. S2 must not be called done
  until the acceptance test proves the roster reaches the runner.
Task 3: fix round 1/5 (deferral clause added; commits a49854d..a2a06e0). Controller verified
  all NINE reachable -UNSUPPORTED codes carry it, including the two inherited from S1.
Task 3: minor (deferred): the new deferral test parametrises over the seven data.units configs
  rather than discovering -UNSUPPORTED codes generically, so a code added elsewhere later would
  not be caught. Documented by the implementer; acceptable, worth revisiting if the family grows.
Task 3: complete (commits 40c3313..a2a06e0, review clean)
Task 4: implemented (commit 520df7c) — resolution wired into validate with byte-identical
  codes. Implementer's answer to the open ordering question upheld on review: skip resolution
  ONLY for a resolver source (else resolve_units mislabels it E-UNITS-SOURCE-MISSING,
  duplicating E-DATA-RESOLVER-UNSUPPORTED); do NOT skip for the other six, since resolve_units
  never reads them and a key defect alongside them is independent. Controller verified all
  four ordering cases.
Task 4: fix round 1/5 dispatched — CRITICAL: a non-mapping `data.units` (e.g. a string) raises
  an uncaught AttributeError out of validate_config, breaking the collect-don't-stop rule that
  is the module's whole reason for existing. Reviewer found the identical latent bug in
  _check_unimplemented. Asked for both guards plus a SURVEY of whether the pattern is endemic
  across the other user-editable blocks — with instructions to report rather than sweep if it
  is widespread, since a whole-envelope shape pass deserves its own task and reviewer.
Task 4: fix round 1/5 (E-DATA-UNITS-SHAPE on both named sites; commits 520df7c..e029f84)
  Part-3 survey came back ENDEMIC and the implementer correctly stopped rather than sweeping.
  Controller confirmed independently: data, metadata, parameters, sweep, replication, and a
  repeats list item all crash with AttributeError. limits and hypotheses survive only because
  validate does not read them yet — latent, not safe.
Task 4: fix round 2/5 dispatched — one _check_shape(doc, c) running FIRST, not six scattered
  guards. Rationale: block shape is a property of the config FORMAT, not of whichever check
  reads it first, so six guards would be six places to forget the seventh and the next block
  added would arrive unguarded by default. Covers statistics/limits/hypotheses too, which
  nothing reads yet, so the next reader inherits a guard instead of a crash. Returns early on
  a shape error, following the existing precedent for an unparseable config and an unknown
  template. Pre-existing hole from S1, not an S2 regression — fixed here because the fix is
  one function and the alternative is leaving a traceback where a diagnostic is promised.
Task 4: fix round 2/5 (_check_shape landed, E-DATA-UNITS-SHAPE folded into E-CONFIG-SHAPE;
  commits e029f84..ac33ae2). Verified: 10 shape violations all reported, valid config clean,
  absent optional blocks clean, exactly one finding per condition, no cascade.
Task 4: fix round 3/5 dispatched — the SAME bug one level up, found by the re-reviewer:
  _check_shape validated the ITEMS of replication.repeats but never `repeats` itself, so a
  non-list sailed through and crashed _check_replication. Reproduced all three shapes.
  Worth a third round because the triggering input is the single most likely YAML mistake in
  the file — forgetting the list dash under `repeats:` yields a mapping. Also asked for a
  survey of the same items-but-not-the-container gap in hypotheses, data.units.attributes and
  sweep axis values, since this is the second time the pattern hid one level below where I looked.
Task 4: fix round 3/5 (repeats-as-container + data.units.attributes-as-container; commits
  ac33ae2..c163e8a). Verified all 6 shapes report E-CONFIG-SHAPE, attributes:[] stays clean.
Task 4: PARKED after round 3 — the re-review found a FOURTH layer, a genuinely different class:
  scalar leaf types (input_dir as a list, metadata.name as a list, n as "many", units.key as a
  list, attributes items as lists). Five repros, all escaping as exceptions.
  RULING: stop. Container shapes were one table and one loop; leaf types need per-field type
  knowledge for the whole envelope, i.e. a config schema — its own design with its own
  questions, and parameter_spec already does that job for `parameters`. Adding it as round 4
  of a units task is the partial-sweep-that-looks-complete failure I warned against in round 1.
  Not load-bearing for S2: pre-existing from S1, and no S2 task depends on it. Recorded in
  spec-defects.md with all five repros so the next task starts from evidence, not rediscovery.
Task 4: complete (commits a2a06e0..c163e8a, 3 fix rounds, 1 parked with ruling)
[session limit hit during Task 5's review; reviewers only read, so nothing was lost — tree
 unchanged at a6fe803, 285 tests passing, review package still on disk. Re-dispatched.]
Task 5: implemented (commit a6fe803) — controller verified the real journey: new → generate
  → validate exits 0 clean, and the reviewer took it further through `run` (also exit 0).
  This was the task's whole hazard: a generator whose output its own validator rejects.
Task 5: MY review brief carried a false premise — I asserted `attributes: null` would be a
  shape error. It is not: _check_shape treats null as absent by documented design and units.py
  coerces `null or []`. The reviewer said so plainly instead of manufacturing a finding.
Task 5: fix round 1/5 dispatched — Minor, but inconsistent WITHIN one diff: the new
  `allocation` comment advertises `between`, which E-DATA-ALLOCATION-UNSUPPORTED refuses,
  while the `from` comment two lines above correctly dropped `{resolver: ...}` for the same
  reason. Same pattern in the pre-existing `kind` and `order` comments. Ruled: mark rather
  than hide — "within  (between: later slice)" — because hiding says the value does not
  exist while marking says it exists and is not ready, which is what the refusal messages
  themselves now say.
Task 5: fix round 1/5 (enum comments marked, not hidden; commits a6fe803..9b9cfa7). Test is
  the generic form: extracts every "(x: later slice)" marking and drives the value through
  validate_config or resolve_repeats to confirm it IS refused and the live default is not —
  so the next drift is caught automatically rather than by pinned strings. Implementer
  correctly declined to mark `from`: {glob:...} is not refused, only {resolver:...} is.
Task 5: complete (commits c163e8a..9b9cfa7, review clean)
Task 6: implemented (commit f15a091) — all three rules verified by controller: io.units raises
  without a roster, second record discarded (first write wins), record/skip in either order
  raises E-STEP-UNIT-SETTLED, unknown key raises E-STEP-UNIT-UNKNOWN. Implementer correctly
  flagged that runner.py does not pass units= yet (Task 8/10's job, already tracked).
Task 6: fix round 1/5 dispatched:
  IMPORTANT a recorded column named `unit` silently overwrote the roster key — the row disowned
    its own identity with no error. Refusing rather than reordering the merge, because
    {**values, "unit": key} would make the row correct while still silently dropping the user's
    column: same disease, nicer symptom. Using the SPEC'S OWN identifier E-STEP-KEY-COLLISION
    (reference.md § Errors core raises) rather than inventing one — and extending it to the
    other half of that sentence, a recorded column colliding with a declared unit ATTRIBUTE,
    which io can detect at record time since it holds the roster.
  IMPORTANT recorded_keys and skipped were live handles to internal state, not the read-only
    accessors the brief claimed. Attrition reads both in a later task, so a step mutating them
    would corrupt the four counts and the corruption would look like data.
Task 6: fix round 1/5 (E-STEP-KEY-COLLISION for both the unit-key and declared-attribute
  cases, using the SPEC'S existing identifier rather than a tenth new one; recorded_keys and
  skipped now return copies; commits f15a091..930b3bb)
Task 6: fix round 2/5 dispatched — the re-review found rows() is a SHALLOW copy, so mutating a
  row dict inside the returned list corrupts internals. The existing test only appended to the
  list, which is why it passed. Matters because rows() feeds units.parquet and collapse_repeats
  in the next two tasks: a step mutating a returned row would change what lands in the
  inference base, and it would look like data rather than an error. One-line fix; explicitly
  NOT deep-copying, since values are scalars by contract.
Task 6: fix round 2/5 (rows() now deep-enough copies each row dict; io.units confirmed already
  safe — UnitList exposes no mutating handle and Unit.attributes is a MappingProxyType on a
  frozen dataclass; commits 930b3bb..e2906ae)
Task 6: complete (commits 9b9cfa7..e2906ae, review clean)
Task 7: implemented (commit 686598d) — controller verified the column contract exactly: key,
  then roster attributes, then the UNION of recorded keys with nulls for absent; failed units
  absent from both files; no files written when nothing was recorded; WRITERS/READERS paired
  with .parquet in both.
  Implementer corrected two of MY errors: the brief's _decode_parquet sketch took a path where
  every other reader takes bytes (would have broken the invert-the-same-table property), and
  two brief test fixtures had step_dir lacking "shared" — the identical mistake I made in my
  own probe.
Task 7: escalation RULED NOT A DEFECT — a column recorded as int in one row and float in
  another comes back all-float. Rejecting at record() would refuse legitimate data (a metric
  whole for some units, fractional for others is ordinary), numeric promotion is what any
  columnar format does, and collapse floats everything before any interval is computed, so no
  reported number changes. What matters is the part that already works: bool/int and str/int
  clashes RAISE rather than coercing. Asked for tests pinning all three so the behaviour is a
  decision rather than an accident, plus a ledger note for the slice that reads the table back.
Task 7: fix round 1/5 (pinning tests + ledger note; commits 686598d..cca47ce)
Task 7: fix round 2/5 dispatched — the pinning work exposed that the type clash raises a raw
  pyarrow.lib.ArrowInvalid: no stable E- identifier to grep or cite, no column name, no unit
  key, and it names pyarrow, which a step author has no relationship with. That text lands
  verbatim in run.yaml's error field — the file a reviewer opens in ten years. Wrapping as
  ContractError naming the column, the clashing types and an example unit each.
  Using E-STEP-RETURN-TYPE, which already exists: reference.md § Steps and artifacts says one
  rule across three surfaces — io.record's values, a step's return, and aggregate — so no new
  identifier. Int/float promotion must still NOT raise.
Task 7: fix round 2/5 (raw pyarrow.ArrowInvalid wrapped as ContractError E-STEP-RETURN-TYPE
  naming the column, both types and an example unit each; commits cca47ce..680754b)
Task 7: minor (DEFERRED, not fixed): finalize() called twice raises ArtifactExistsError when
  rows exist but SILENTLY DUPLICATES every line of ineligible.jsonl when only skips occurred —
  two failure modes for one misuse. Unreachable today (the runner calls it once) and Task 8
  counts from the in-memory skipped set rather than the file, so nothing downstream reads the
  duplicates. Deliberately ledgered rather than fixed: it is a Minor by the reviewer's own
  grading, I have already spent two rounds on this task, and minors belong in final-review
  triage. A one-line _finalized flag is the fix if the final review promotes it.
Task 7: complete (commits e2906ae..680754b, review clean, 1 minor deferred)
Task 8: implemented (commit fa5d261) — attrition + the one named early stop.
Task 8: fix round 1/5 dispatched — implementer's escalation, verified: S1's
  E-STEP-NAME-COLLISION guard catches two DISTINCT classes deriving one name but misses the
  SAME class listed twice, which is the likelier copy-paste error. Two executions then share a
  step directory and, worse, one run-record key — the second silently overwrites the first in
  per_repeat. Directly load-bearing for Tasks 9 and 10, which key the collapsed table and the
  aggregated metrics by step_name. Extending the existing guard, same identifier, no new code;
  messages distinguished because the remedies differ (rename one vs delete a duplicated line).
  Also asked for the workaround (distinctly-named subclasses in the Task 8 tests) to be either
  reverted or kept with a stated reason, so the next reader knows it was deliberate.
Task 8: fix round 1/5 (E-STEP-NAME-COLLISION extended to the same class listed twice;
  commits fa5d261..850dc14). Workaround kept deliberately with inline comments — the fixed
  guard now REFUSES [Bad, Bad], so distinctly-named subclasses are required, not a dodge.
Task 8: fix round 2/5 dispatched — CRITICAL from MY brief's pseudocode: `ineligible` was a
  UNION across repeats where reference.md:1580 requires an intersection ("A unit ineligible in
  some and completed in others is counted as FAILED, not ineligible"). Reproduced: a unit
  skipped in s1 and completed in s2 came back ineligible with failed=0.
  Why Critical rather than cosmetic: max_failed_fraction guards `failed` and deliberately does
  NOT guard `ineligible`, because a design exclusion is not dropout. Mis-filing the unit hides
  it from the one threshold that would have caught it — and a step with non-deterministic
  eligibility, the exact bug this rule exists to surface, would sail past. Plan corrected.
Task 8: fix round 2/5 (ineligible is now an intersection; commits 850dc14..02612d2).
  Re-reviewer proved the fix load-bearing by reverting to the union and watching the two new
  tests fail, and verified the CONSEQUENCE not just the count: 10-unit roster with 4
  inconsistently skipped — union gives failed=0 so the run never stops under any threshold,
  intersection gives failed=4 so max_failed_fraction=0.2 stops it. That is the hidden-failure
  scenario that made this Critical.
  Second opinion sought and given on the open ruling (skipped in one repeat, unrecorded in
  another = failed): agreed, with a better articulation than mine — a skip is an AFFIRMATIVE
  act, an absent skip is an absence of information, and reading it as ineligible would let a
  step's omission silently manufacture a design exclusion.
Task 8: complete (commits 680754b..02612d2, review clean)
Task 9: implemented (commit 62236c4) — three items raised, all good:
  (1) self-fixed before commit: collapse averaged a unit over whatever subset recorded it, so
      the reported n.completed (intersection) could describe a different set than the mean was
      computed over. Now intersects too. Accepted.
  (2) FIX: collapse_repeats pools across conditions — reproduced, 1.0 and 100.0 collapse to
      50.5. reference.md § Statistical reporting forbids it outright. Unreachable in S2 (one
      condition) and pinned by a test named "known_limitation", but that reads to the next
      person as a decision and S3 adds sweeps. Ruled: add a REQUIRED condition_index so the
      bug becomes unwritable — a forgetful caller gets a TypeError, not a wrong number.
  (3) FIX: assemble_run_yaml accepts `counts` then `del counts`. The reasoning for not writing
      it is right, so the conclusion is the parameter should not exist. A parameter accepted
      and discarded is worse than either alternative. Removed against my own brief; plan
      corrected for both.
Task 9: fix round 1/5 (required condition_index on collapse_repeats; dead `counts` param
  removed against my own brief; commits 62236c4..463c679). Verified: omitting condition_index
  is a TypeError, conditions no longer pool, interval arithmetic hand-checked exactly.
Task 9: fix round 2/5 dispatched — the MIRROR IMAGE of the fix I just ordered. _results_block
  assigns ONE `aggregated` object to every condition, so with two conditions the record shows
  condition 1 reporting condition 0's numbers; PyYAML emits &id001/*id001 anchors exposing the
  aliasing. I made pooling unwritable in collapse_repeats and left it writable one file over.
  Fixing both: aggregated keyed by condition index (NOT deep-copied — identical-but-separate
  wrong numbers would be worse than obviously-shared ones), and attrition gains a required
  condition_index too, since summarize_step embeds its n as the denominator a reader trusts
  most and a right mean over a wrong n is the same silent mismatch.
  NOTE: both signatures change, so Task 10's dispatch must be written against the NEW ones.
Task 9: fix round 2/5 (aggregated keyed by condition index; attrition gains required
  condition_index; commits 463c679..4ba0190). Verified: no YAML aliasing anchors, both
  signatures require the index.
Task 9: complete (commits 02612d2..4ba0190, review clean)
Task 10: implemented (commit d914893). Controller ran the real 240-unit journey end to end:
  resolved 240 / completed 226 / ineligible 2 / failed 12, reconciling; basis units with
  t_over_units; interval recomputed INDEPENDENTLY from the units.parquet files and matched to
  1e-12; provenance.units and units_hash present; declared attribute carried into the table;
  n_units sits in per_repeat with no interval near it.
  *** The Task 3 blocking condition is DISCHARGED: the roster now reaches the runner. ***
  Implementer fixed a real doc/code drift (the generated starter step never touched io.units,
  contradicting both normative docs — S1's recorded deviation, now closed) and self-caught a
  scaffold leaked into this repo via a stray cd. Controller verified: never committed, history
  clean, tree holds only src/publishable.
Task 10: complete (commits 4ba0190..d914893)
== WHOLE-BRANCH REVIEW (25 commits, opus) ==
Central claim verified numerically by the reviewer with its own fixture: reported ci95 matched
  an independent recomputation to 1e-13, and no path can produce a ci95 for a step-returned
  scalar. That refusal is intact.
CRITICAL found: attrition intersected across EVERY repeat-scoped step, not the recording one.
  An ordinary scalar-only second step (timing, logging) collapsed 8/1/1 to 0/0/10. Three
  consequences: right mean beside wrong n; units skipped everywhere reclassified from
  ineligible to failed, hiding them behind the guard that deliberately does not watch
  ineligible; and max_failed_fraction then SILENTLY TRUNCATING the plan — 6 of 10 executions,
  status completed, exit 0, nothing in the record saying so.
  Why every prior review missed it: every attrition/stats/acceptance fixture had exactly ONE
  repeat-scoped recording step. Structurally unable to see it. The regression test now has two.
Fix wave (single dispatch, commit 152f0bf): all four findings. Re-review reverted the fix and
  watched the new test fail; verified the truncation consequence separately; assessed and
  upheld the guard's run-level-union judgement call against reference.md:1606, including the
  crash-exclusion case (never yields a false completed, since run_status is already failed).
Deferrals upheld by the reviewer: leaf-type validate crashes (pre-existing, needs a config
  schema) and the finalize() double-call (unreachable). Neither blocks.
MERGED: main fast-forwarded 36f9a0d..152f0bf, 334 tests green on the merged result,
  ruff/mypy clean, docs pass clean, branch deleted, pushed to origin.

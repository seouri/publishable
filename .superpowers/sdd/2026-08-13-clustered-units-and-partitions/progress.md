# SDD ledger — plan: docs/superpowers/plans/2026-08-13-clustered-units-and-partitions.md
Plan: docs/superpowers/plans/2026-08-13-clustered-units-and-partitions.md (12 tasks).
Branch h3b-clustered-units-and-partitions, base fc98a09 (main, H3a merged).

Pre-flight (controller): ONE under-specification in my own plan, fixed before dispatch. Task 4
  asserted folds of {8,7} from cluster sizes 7/3/3/1/1 at k=2, but that holds only under LARGEST-FIRST
  greedy assignment — smallest-first gives {11,4}. Measured all three orderings. The rule is now
  explicit: shuffle the clusters with the digest-seeded RNG, THEN assign largest first to the
  currently-smallest fold. Both halves are load-bearing and each got its own mutation — dropping the
  sort (find a seed where greedy diverges and pin it, or the mutation cannot fail) and dropping the
  shuffle (needs a test that two digests give different assignments, or the seeding rule is claimed
  and not provided).
Task 1: commits 2c80d49, 6a3c3a9. Documents only; 1226 passed + 2 xfailed, unchanged.
  Three edits verified present by the controller: the owed *Cluster attribute exists* row, the
  W-DATA-CLUSTER-UNDECLARED row, and the "a cluster must not vary within a unit's measurement rows"
  rule. The identifier is correctly NOT emitted anywhere in src yet.
  THE TRIGGER CARRIES NO NUMBER, and the implementer's reason is right: a ratio is a tunable, and
  CLAUDE.md puts every threshold in `limits` — anchoring it would mean a new limits key, which is code
  task 1 could not write. So it is predicate-only like W-DATA-WEIGHT-UNDECLARED. Verified silent on
  cohort-pilot's own [label, age, sex] and firing on § Validation's own `site` example. The four
  predicates are the implementer's construction, so the ROW is what changes if one proves
  unimplementable.
  The first commit CREATED A DRIFT the second fixed: two existing summaries (§ Clustered units,
  § Weighted samples) described the trigger as "few distinct values, many units each", which fires on
  `sex` literally. Both now point at the row as the single statement of the trigger.
Task 1: REPORT INACCURACY, no action — it says the NOT BUILT count is "unchanged at 11". The prose
  reads "Nine declarations above are not yet built", verified by the controller, and the count is
  indeed unchanged. The 11 looks like a miscount of backtick spans (it counts `NOT BUILT` itself and
  splits compound items). Document state right, report number wrong.
Task 1: TWO PLAN GAPS THE IMPLEMENTER FOUND, both fixed by the controller:
  (a) NO TASK OWNED W-DATA-CLUSTER-UNDECLARED's EMIT SITE. The File Structure table named it under
  validate.py but no step did, so the slice would have shipped a documented warning nothing raises,
  surfacing only at task 12. Now task 2 step 6, with the worked example's own [label, age, sex] as the
  negative control that decides whether the trigger is usable at all.
  (b) § Mistakes core prevents carries FOUR cluster rows, not one, and CLAUDE.md requires each to be
  STRUCTURALLY IMPOSSIBLE. Task 12 now checks them one at a time with owners: Ignored clustering
  (tasks 8, 9, 2); A cluster split across train and test (tasks 4 AND 3 — the partition closes the
  fold route, the constancy check closes the INPUT-FILE route, and closing one half looks complete
  from inside that task); Resampling clustered rows as if independent (task 9, live via the
  unconditional derived draw even though statistics.resample stays refused); A permutation that
  shuffles away the matching (H4, still refused — confirm rather than assume).
Task 1: H3b-SCOPING CONTRADICTS ITSELF on where the clustered-contrast refusal lands (its task-1 line
  vs its task-12 line). The implementer followed the brief — task 11, matching the H3a precedent — and
  did not add it. That is the right call; the plan is the authority, not the scoping.
Task 2: commits df3a4f2, 46c994f. 1248 passed + 2 xfailed (was 1226). clusters_of/cluster_count in
  units.py; _check_cluster_by in validate.py; W-DATA-CLUSTER-UNDECLARED's emit site; one new § Errors
  row; 21 tests.
  CONTROLLER-VERIFIED, the test that decides usability: over a 20-unit table, cohort-pilot's own
  attributes [label, age, sex] draw NOTHING — including `sex`, two values over 20 units, which the
  loose phrase "few distinct values, many units each" would have caught — while adding `site`
  (5 values, 4 units each) fires W-DATA-CLUSTER-UNDECLARED. A warning that fired on the project's own
  worked example is one every user learns to ignore.
Task 2: TWO BRIEF DEFECTS, MINE.
  (a) Step 3 said to raise "the code the *Cluster attribute exists* row implies" — NO SUCH CODE EXISTS.
  § Validation is a two-column table carrying no codes, and task 1 added no § Errors entry. The
  implementer minted E-DATA-CLUSTER-UNKNOWN with its § Errors row and explicitly REJECTED reusing
  E-UNITS-ATTR-MISSING, which § Errors frames as the SOURCE-COLUMN code — the same asymmetry H3a's
  task 6 shipped a Critical on, read correctly this time.
  (b) The brief's "two deliverables" undercounts: H3b-SCOPING assigns the glob cross-check to task 2
  as well, and task 1's report says task 2 discharges that row. Built, or a published check would have
  had no implementation.
Task 2: verified rather than assumed that cluster_by names a DECLARED ATTRIBUTE (reference set is
  data.units.attributes), from three sources — task 1's row wording, design-principles.md § Core vs.
  plugin, and § Clustered units' YAML declaring animal_id in both places. That is also what makes it
  readable per unit at all. The opposite reading is what H3a's task 6 shipped a Critical on.
Task 2: NEAR-MISS WORTH KEEPING — `pytest -k cluster` reported all-green because the negative
  control's name contains no "cluster". A -k selection is itself a check that can fail to run the case
  that matters. Run the file, not the selection, when a control is what you are trusting.
Task 2: OWED, routed — E-DATA-CLUSTER-UNKNOWN has no § Errors AT RUN TIME row yet. Honest today
  (nothing in a run calls clusters_of); whichever task wires it, 4 or 11, owes that row.
Task 2: the exclusion list (groups axis / assign.from / stratify_by / null_test.shuffle) is mostly
  unreachable while those blocks stay refused. Implemented and tested anyway, since the row states it.
Task 3: commits e63dc01, 8ed0135. 1267 passed + 2 xfailed (was 1248). The constancy check lives in
  collapse_measurements — the one place holding PRE-collapse values, since resolve_units collapses
  internally and any validate-time check sees the post-collapse roster.
  Controller-verified with controls: a varying cluster -> E-DATA-CLUSTER-VARIES; agreeing rows -> ok;
  a varying weight -> E-DATA-WEIGHT-VARIES; agreeing rows -> ok; neither declared -> ok.
  H3A'S OPEN GAP IS CLOSED by the same machinery. § Weighted samples carried "a weight must not vary
  within a unit's measurement rows" as documented-but-unchecked since H3a's whole-branch review;
  wiring only the cluster caller would have shipped a capability and an identical known bug side by
  side.
Task 3: BRIEF DEFECT #3, MINE — I specified `constant: tuple[str, ...]`, which CANNOT CARRY TWO CODES:
  a bare column name does not say whether it is the cluster or the weight, so the parameter
  contradicted the brief's own "two codes, not one". The implementer used a Mapping keyed by
  DECLARATION ({"cluster_by": "site"}) and adjusted the tests.
Task 3: THE IMPLEMENTER CAUGHT A DOCUMENT CLASS I DID NOT ASK FOR — two reference.md prose passages
  became COUNTERFACTUAL the moment the check landed. § Weighted samples' "become a single weight of
  100 under `sum`" and § Clustered units' "collapses to S1, chosen by the first fallback" both
  described the UNCHECKED outcome, which is now refused. Rewritten to conditional + refusal. That is
  the document-describes-code-that-no-longer-exists class, and CLAUDE.md's Prevented mistakes rule
  requires it.
Task 3: SCOPE NOTE, correct as recorded — artifacts._collapse_measurements (the step-recorded path)
  has no equivalent check, deliberately: it merges RECORDED columns, never declared attributes. If a
  later slice lets a step record over a declared attribute, this check does not cover it.
Task 3: MINOR, accepted — the raise reports the first offending unit and ends resolution, so several
  faults report one at a time. Matches E-UNITS-KEY-DUPLICATE; E-DATA-WEIGHT-INVALID reports the whole
  roster, so the two differ.
Task 3: review spec ✅, APPROVED, 1 Important + 2 Minor. Totality pinned by 17 direct probes each with
  a control; the leak confirmed closed on BOTH surfaces (validate via _check_units' except
  ContractError, run via main's except PublishableError -> EXIT_WRONG); both halves pinned separately
  by mutation (unwiring weight_by kills the weight tests and NOTHING cluster-specific).
  § Mistakes core prevents' "A cluster split across train and test" is now structurally impossible VIA
  THE INPUT-FILE ROUTE. Task 4 owns the partition route; the row is correctly left alone until then.
Task 3: IMPORTANT closed by the controller — CONSTANT_COLUMN_RULES reads as an extension point its
  wiring cannot reach. The comprehension indexes units_decl by the key itself, so it reaches only flat
  string-valued keys. The reviewer PROBED it: adding "holdout" to the registry with
  holdout: {method: by_attribute, from: split} over rows carrying split train/test RESOLVED CLEANLY —
  no error, no failing test, just an absent check; and "holdout.from" no-ops identically. H3c's
  assign.<axis>.from and H3d's holdout.from are the next two that will want this rule, so the
  constraint is now stated at the comprehension where someone adding a row will read it.
Task 3: MINORS accepted — a stale commit hash in the report (amend slip; content matches), and an
  "alphabetical position" claim that is true of the code-sorted § Errors tables but loose for
  § Validation, which orders by sibling adjacency instead. The reviewer confirmed zero out-of-order
  pairs across all 74 rows of the validate-report table.
Task 3: the reviewer strengthened the artifacts._collapse_measurements exemption's REASON — not merely
  that artifacts never mentions cluster_by, but that declared attributes are attached AFTER the
  collapse, per unit, from the roster, so there is no pre-collapse per-measurement declared value for
  a constancy check to have an opinion about.
Task 3: complete (commits e63dc01, 8ed0135, plus the controller follow-up).
Task 4: commit 6c58f55. 1272 passed + 2 xfailed. THE SLICE'S LOAD-BEARING TASK.
  partition_units(roster, k, digest, clusters=None): group in roster order -> rng.shuffle(names) ->
  stable sort by -size -> each whole cluster to the currently-smallest fold by unit count.
  Controller-verified: fold sizes {7,8}, NO cluster split, every unit exactly once, and a different
  digest gives a different assignment (so the seeding rule is provided, not claimed).
  FIRST CLEAN BRIEF OF THE SLICE — "no brief defect found", after three consecutive defective ones.
  THE TRAP FIRED IN MY OWN VERIFICATION: the clustered and unclustered paths give the SAME FOLD SIZES
  {7,8} on this fixture, so a size comparison discriminates nothing. The implementer had already
  pinned the unclustered path by LITERAL KEY LISTS captured from HEAD before the edit, which is the
  right discriminator. Sizes coinciding while membership differs is exactly the class this slice was
  warned about.
  Both trap-mutations handled as asked rather than assumed: the drop-the-sort mutation genuinely
  diverges under the brief's own digest ({5,10} vs {8,7}), ESTABLISHED BY A SCRATCH SEARCH over both
  variants and written into the test docstring; and the drop-the-shuffle mutation is caught by a
  separate equal-cluster fixture (six clusters of 3 at k=3) asserting cluster->fold MEMBERSHIP, since
  sizes there are invariant by construction and could not have caught it.
  The docstring keeps BOTH promises conditionally — at most one when clusters is None, "as even as
  indivisible clusters allow" when clustered — rather than replacing a still-true strong claim with
  the weak one.
Task 4: CONCERNS RECORDED — (1) nothing wires cluster_by into cli's fold step yet, so the guarantee is
  not end-to-end until that lands; (2) a cluster larger than n/k silently unbalances the split with no
  warning (90/5/5 at k=2 -> 90/10), possibly worth a validate warning and in no brief; (3) k=0 diverges
  between paths, unreachable since _fold_k refuses k < 2.
  Doc check: no document claims the at-most-one balance, and § Clustered units already says "as evenly
  as whole clusters allow", so nothing is owed — BUT the assignment order is stated nowhere in the four
  documents, only in the docstring. Worth a document sentence in task 12 if the order is a promise.
Task 5: commits 0261be0, 96f6f45. 1290 passed + 2 xfailed (was 1272). units.fold_basis(roster,
  cluster_by) is the single derivation — cluster count when clustered, unit count otherwise — and
  resolve_repeats' unit_count kwarg is renamed fold_basis. E-REPL-FOLD-K-TOO-LARGE reused, so no
  REPL_DECLARATION_CODES escape risk. _fold_k's body order untouched, so task 6's ordering flip stays
  pinned.
  BRIEF DEFECT, MINE: THREE ARRIVAL PATHS, NOT TWO. I named validate's and cli's calls to
  resolve_repeats; the BUDGET half (Leave-one-out is affordable) reaches the number through
  _check_sweep -> _repeat_total -> _level_count and never through _fold_k at all. Exactly the class
  H3a shipped when it changed two of three n-building sites. Four mutations run, one per path.
  Brief step 6 was already discharged by task 1 — the row already carried the clustered wording. What
  actually needed editing were two § Errors rows: E-REPL-FOLD-K-TOO-LARGE said "resolved unit count",
  and E-REPL-FOLD-K said `all` fails only with no roster, now false since the roster can resolve while
  its clusters cannot.
Task 5 + Task 4 INDEPENDENTLY FOUND THE SAME PLAN GAP, now fixed: cli.py's fold step calls
  partition_units(roster, fold_level.n, digest) with NO clusters argument. So a clustered run gets the
  right fold COUNT (task 5 wired that) and the WRONG MEMBERSHIP — task 4's rewrite is never reached,
  and every fold still trains on other units of the cluster it tests on. The slice's load-bearing
  guarantee was unwired and MY PLAN ASSIGNED IT TO NO TASK. Task 10 widened to own it, with the
  requirement to pin it over a REAL RUN rather than at the function, and to assert MEMBERSHIP not
  sizes — the coincidence that caught my own probe on task 4.
Task 5: CONCERNS RECORDED — (1) the cli path is unreachable end-to-end while E-DATA-CLUSTER-UNSUPPORTED
  lives, so its test monkeypatches that one finding away; task 11 must retire the bypass and still owes
  the § Errors AT RUN TIME row for E-DATA-CLUSTER-UNKNOWN; (2) § Repeat kinds' "cluster-respecting when
  cluster_by is declared" is document-ahead-of-code until task 10 lands the wiring — task 12 checks it;
  (3) k: all over a single cluster reports E-REPL-FOLD-K naming k: 1 for a config that wrote `all`,
  pinned by test.
Task 6: commits 7f13c3e, 8b98056. 1310 passed + 2 xfailed (was 1290). Clean brief — no defect found.
  units.stratum_varies_within_cluster (membership from clusters_of only) and
  validate._check_fold_stratify_by reporting E-REPL-FOLD-STRATIFY-UNKNOWN and -VARIES. Neither joins
  REPL_DECLARATION_CODES, correctly — neither is raised from replication.py.
  THE ORDERING PINS ARE STRONGER THAN I ASKED FOR: they assert the current code AND THE ABSENCE of the
  flip code (E-REPL-FOLD-K for k: 1, E-REPL-FOLD-K-TOO-LARGE for k: 99 over a resolvable 15-unit
  roster), so task 12's retirement will show up as a diff rather than as a surprise.
  The survives-clustering check lives in validate.py, not _fold_k, because it needs roster + cluster
  membership + stratum values together and _fold_k sees only a level and a count. Judgement recorded.
  The *Stratification attribute exists* row is ONE-THIRD discharged — fold only — and the codes are
  fold-prefixed so H3c (assign.*) and H3d (holdout.) cannot mistake it as done.
  Mutations disjoint in BOTH directions: 3 existence tests fail with the clustering ones passing, and
  4 clustering tests fail with the existence ones passing.
  A unit carrying no stratum value counts as a variation (rendered "no value") — a judgement no
  § Validation row states, pinned both ways by test. Worth a document sentence if it is a promise.

PLAN RESTRUCTURED (controller, after task 6): the SECOND gap of the same shape in this slice.
  fold.stratify_by is now VALIDATED but partition_units takes no stratum, so a declared stratification
  HAS NO EFFECT ON THE SPLIT. § Repeat kinds calls folds "stratified" when it is declared, so this is
  a declaration accepted whose effect is not delivered — and task 12 retiring
  E-REPL-FOLD-STRATIFY-UNSUPPORTED would make it live. Task 4's heading said "and honouring a
  stratification" and NO STEP OWNED IT; task 6's implementer found it and said so.
  USER RULING: add a dedicated task rather than fold it into the wiring task or refuse the feature.
  Tasks 7-12 renumbered to 8-13 (highest-first, headings and prose cross-references), and the new
  TASK 7 is the stratified partition. Brief extraction re-verified for 7, 8 and 13 after renumbering.
  The composition is not a second balancer: because task 6 GUARANTEES a cluster carries exactly one
  stratum value, a cluster belongs to exactly one stratum — so the rule is partition WITHIN each
  stratum using task 4's existing rule, then merge the per-stratum folds index-wise. Unclustered is
  the degenerate case (each unit its own cluster of one), and clusters=None must stay byte-identical.
  Task 7 also owes a docstring sentence saying the composition is sound ONLY WHILE task 6's check
  exists — a later slice removing it would silently break this.
  Task 11's partition wiring widened to pass BOTH clusters and strata: "both arguments or neither;
  wiring one and not the other ships half a guarantee that looks whole."
Task 7: commits 21acabb, 58adf6a. 1319 passed + 2 xfailed (was 1310). Controller-verified with the
  control: stratified gives 4/2 in BOTH folds; the plain draw gives 3/3 and 5/1 — they differ, so the
  test discriminates.
  MY FIXTURE WAS COINCIDENCE-PRONE IN THE DIGEST, and the implementer found it: under sha256:abc (and
  "d") the UNSTRATIFIED draw already lands 4/2 in both folds, so my prescribed fixture could not see
  the rule at all. sha256:0000 used instead. That is the coinciding-fixture trap arriving through the
  seed rather than through the sizes — a dimension I had not thought to warn about.
  THE SORTED-MERGE MUTATION IS UNKILLABLE BY A BALANCE ASSERTION, and the implementer said so rather
  than manufacturing a failure: sorting permutes a stratum's pieces without changing its size multiset,
  and is the IDENTITY on every equal-size fixture including mine. It only shows up with unequal
  clusters, where it is in fact marginally CLOSER to the roster mix. Pinned on the contract (exact
  per-fold cluster membership) with the reason recorded. Exactly the honest outcome the brief asked
  for.
  clusters is None was COLLAPSED INTO THE DEGENERATE CASE (each unit a cluster of one), proved
  byte-identical by probe and by task 4's byte pin — which is also what makes the split-a-cluster
  mutation fail TASK 4's no-split test, as the brief required.
  Tests all named with stratum/stratif so `-k stratum` runs each probe beside its control — task 2's
  near-miss applied as a habit.
Task 7: TWO GAPS FOUND AND PINNED AS BEHAVIOUR RATHER THAN FIXED, both routed to task 11/13:
  (a) stratified fold sizes have NO SPREAD BOUND once clusters are unequal (10/5 at k=2 in one
  fixture) — the size promise task 4 weakened weakens further under stratification;
  (b) validate bounds k only by the WHOLE ROSTER's fold_basis, so a clean k can leave a fold holding
  NONE of a stratum, which defeats stratification silently. A possible new § Validation row.
Task 7: HANDOFF — task 11 must build the strata mapping and MUST NOT reuse clusters_of for it, which
  raises E-DATA-CLUSTER-UNKNOWN and would misname the block. The mapping must be total.
Task 8: commit ad55d40. 1328 passed + 2 xfailed (was 1319). Controller-verified with the control:
  clustered n reports clusters: 2 over 6 units (the two numbers DIFFER, so the fixture discriminates);
  the unclustered control has NO clusters key at all; every part renders as int.
  ONE CHANGE, NOT THREE — H3a's runner._counts builder exists, so all three n-building sites gained
  clusters from one conditional. That is H3a's own fix paying off: it shipped a bug by changing two of
  three sites and then routed them through one builder.
  WHAT `clusters` COUNTS, justified from the documents rather than by analogy: the COMPLETED units,
  recomputed PER COLUMN. § Clustered units calls it "the number of clusters as the effective sample
  size alongside the unit count" and § Statistical reporting gives t_over_units_clustered "df =
  clusters - 1" — the figure is an interval's df, and a df is over the units that interval was computed
  from. The derived branch inherits the condition-wide figure, mirroring effective.
  INTEGERS CONFIRMED IN THE RUN.YAML TEXT by regex over every n block asserting no \d+\.\d+ — the right
  check, since an isinstance assertion cannot see it (10 == 10.0). H3a's reviewer had to read the text
  for the same reason after counts widened to dict[str, float].
  DEVIATION, justified: added units.cluster_count_of(membership, keys) and refactored cluster_count
  through it, because neither named interface fits a SUBSET count (no roster to hand cluster_count) and
  one new expression beats two inline len({...})s. Verified by behaviour against tasks 4/5/6's tests.
  Mutations: unconditional clusters -> 149 failures including all three regression tests; counting the
  resolved roster instead of completed -> 3 runner tests; dropping the per-column recompute -> exactly
  the ragged stats test. Noted honestly that the cli positive test does NOT discriminate the
  wrong-unit-set mutation (all units complete there) — the 5-unit/3-cluster/2-completed fixture carries
  that half.
Task 8: TRANSIENT STATE, acceptable mid-slice, must be checked at the end — n.clusters now prints
  beside intervals that are NOT yet cluster-robust (stats has no t_over_units_clustered and
  percentile_of_derived still draws rows), so § Clustered units' "effective sample size" half is
  document-ahead-of-code until task 9. TASK 13 MUST CHECK THE *Ignored clustering* ROW ONLY AFTER
  TASK 9, not before.
Task 8: DEBT GROWING — clusters_of is now a SECOND run-time raise site for E-DATA-CLUSTER-UNKNOWN,
  which still has no § Errors AT RUN TIME row. Task 2 recorded it; the debt is larger now. Task 12 owes
  it alongside retiring task 5's monkeypatch bypass.
Task 9: commits 50c796a, c9e03a5. 1339 passed + 2 xfailed (was 1328).
  t_over_units_clustered(values, keys, membership, confidence=0.95): intercept-only CR1 sandwich,
  V = [G/(G-1)] * sum_g S_g^2 / n^2, df = cluster_count_of(membership, keys) - 1, reusing _t_critical.
  Returns None below two clusters (df 0), with a two-cluster control that must report.
  Controller-verified independently: over 30 units in 10 clusters of 3 the interval matches
  t_over_units over the ten CLUSTER MEANS — df 9 BY CONSTRUCTION, from an already-trusted function —
  to 1e-9, while the unclustered control gives 11.21-17.79 against 8.00-21.00. The fixture
  discriminates by a wide margin, and the expectation is not a tautology.
  THE TWO CR1 CONVENTIONS COINCIDE HERE and the implementer said so rather than picking silently:
  G/(G-1) and Stata's G/(G-1)*(n-1)/(n-k) are identical because k = 1 for a mean. That is the kind of
  thing that otherwise becomes an unexamined choice buried in a formula.
  Expectations built two ways: balanced clusters provably reduce to t_over_units over cluster means,
  plus an UNBALANCED hand-computed fixture (sizes 1, 2, 3) that the cluster-mean shortcut fails on both
  centre and width, CROSS-CHECKED AGAINST A SEPARATELY WRITTEN MATRIX-FORM SANDWICH. Cross-checking
  against an independently written implementation is how a statistical test avoids being a tautology.
  Mutations: df from the unit count -> 3 tests fail; dropping the G/(G-1) scaling -> 4 tests fail.
Task 9: COMBINATION GAP FOUND BEFORE TASK 11 HITS IT — weight_by + cluster_by together has NO
  construction. § Weighted samples says the cluster decides the draw when both are declared, which
  means a WEIGHTED CR1. Task 11 reaches that branch point at summarize_step and must build it or refuse
  it by name. This is the class H3a shipped (measurements collapsing a weight column); finding it one
  task early is the difference.
Task 9: the _clustered FAMILY is still incomplete by design — the paired/unpaired contrast and
  percentile forms § Statistical reporting names do not exist. Only the column form was in scope.
  Task 10 owns the percentile draw; task 12 owns refusing the contrast family, on the
  E-DATA-WEIGHT-CONTRAST precedent.
Task 10: commits 17ef816, ee8b1fd. 1354 passed + 2 xfailed (was 1339). The clustered percentile draw:
  each replicate selects G clusters with replacement and pools their units. Headline asserts BOTH
  endpoints exactly as pooled means of two named cluster multisets AND as members of the 35-multiset
  achievable set. Mutations: draw units -> 3 fail; separate-sort re-pairing -> 5; average cluster means
  -> 4.
  The floor is two clusters, DERIVED rather than borrowed from task 9's df: at G=1 every replicate is
  the same pool so the width is zero, which § Statistical reporting refuses in those words. A percentile
  has no df, so task 9's floor could not simply transfer — the implementer said so rather than
  assuming.
  weight_by + cluster_by implemented as the composition of two documented sentences (draw by cluster,
  weighted mean over pooled units). Unlike task 9's case the underspecification there was the DF, and a
  percentile has none — so the composition is determined rather than invented.
Task 10: BRIEF DEFECT #4, MINE, AND THE MOST CONSEQUENTIAL — I CONFLATED TWO FUNCTIONS. My brief's
  motivation (derived_metric_draws = 2000 runs unconditionally) attaches to percentile_of_derived;
  its deliverable was percentile_over_units. Verified by the controller: percentile_over_units has
  ZERO callers outside stats.py and is reached only via summarize_step under statistics.resample,
  which E-STATS-RESAMPLE-UNSUPPORTED still refuses; percentile_of_derived has one caller, in cli, and
  runs unconditionally. So task 10 built the right construction for the GATED path while the LIVE path's
  clustered form does not exist.
  Exposure measured before deciding: the shipped GenericTemplate does not override aggregate, so only a
  USER-WRITTEN template that derives a metric reaches it. Narrow but real.
  USER RULING: refuse the combination at task 12 rather than growing percentile_of_derived_clustered
  here. Task 12 now carries TWO refusals — the clustered contrast family and the clustered derived
  draw — both on the E-DATA-WEIGHT-CONTRAST precedent, with H4 lifting both.
  Task 12 must also answer a question the refusal raises: what does "returns derived metrics" MEAN at
  validate time, when aggregate is user code core never inspects? If it cannot be known before the run,
  the refusal has to live somewhere else, and the brief says to say so rather than guess.
Task 10: percentile_over_units_clustered names something § Statistical reporting's method table has no
  row for — the _clustered suffix rule is stated only under the CONTRAST table. Recorded in
  spec-defects.md with a proposed row; task 13 should land it.
Task 11: commits c43e02b, 42df52d, cefaba3. 1377 passed + 2 xfailed (was 1354; +23). THE WIRING TASK —
  everything the slice built was unreachable until this landed.
  cli now passes BOTH clusters and strata to partition_units. The strata mapping is built at the call
  site rather than via clusters_of (which would raise E-DATA-CLUSTER-UNKNOWN and misname the block —
  task 7's trap, avoided), indexed against the totality _from_table guarantees, with fold.stratify_by
  carried on RepeatLevel so resolve_repeats stays the single reader of the declaration.
  All three summarize_step call sites already passed clusters from task 8, so the interval wiring is
  one four-way branch inside stats.summarize_step. Six separate mutations, each failing a named test;
  reverts verified by diff against pristine copies PLUS the full suite.
  THE DECISION THE BRIEF ASKED FOR: weight_by + cluster_by is BUILT, not refused —
  weighted_t_over_units_clustered, draw and df from the CLUSTER (§ Weighted samples + § Statistical
  reporting), with Kish's size nowhere in the df but still reported as n.effective. It reduces to
  t_over_units_clustered digit for digit at equal weights, and the expectations came from EXACT-RATIONAL
  ARITHMETIC OUTSIDE THE MODULE. The reasoning for building rather than refusing: refusing would cost
  every basis: units interval in a run declaring a documented pair.
Task 11: BRIEF INACCURACY #5, MINE — item 3 was a VERIFIED NO-OP. percentile_over_units_clustered has
  no summarize_step site to wire, because percentile_over_units has no caller in src/ at all. I asked
  for wiring that does not exist to be wired.
Task 11: CORRECTED A FACTUAL ERROR IN MY TASK 13 TABLE, now fixed in the plan — I attributed
  *Resampling clustered rows as if independent* to task 10. That row is NOT closed by task 10: its
  construction serves the statistics.resample path, which H4 still refuses and which has no caller. The
  LIVE path is percentile_of_derived, still unit-level, so the row closes only by TASK 12'S REFUSAL.
  Task 13 must check the refusal, not the function.
Task 11: TWO BYPASSES NOW EXIST BY TWO MECHANISMS — _without_the_cluster_refusal (the validate finding,
  task 5) and _without_the_stratify_refusal (_fold_k's raise, new). Task 12 retires exactly two, and
  the count is recorded here so neither is forgotten.
Task 11: EXOTIC HOLE, named in the code, left for task 12 — collapse_measurements drops the attribute
  named by measurements.by, so stratifying ON the measurement axis would reach a bare KeyError.
  Unreachable today; task 12 decides whether it earns a coded refusal.
Task 12: RECOVERY SITUATION. The first dispatch was interrupted; its work was left UNCOMMITTED with no
  commit and no report, ~710 lines across six files. Controller preserved it as a patch, inventoried it
  against the brief, established it was ON-PLAN (both refusals minted, both -UNSUPPORTED codes removed
  from live paths, both test bypasses gone), and dispatched a fresh agent to COMPLETE rather than redo
  it. The two failing tests at that moment were task 6's ordering pins — the DESIGNED consequence my
  brief predicted ("if they do not change, something is wrong"), not breakage.
Task 12: complete. Commits 870301f, 23ac64e, 65cd97a, 5cd65e4. 1391 passed + 2 xfailed (was 1377).
  Controller-verified with a control: E-DATA-CLUSTER-UNSUPPORTED clean in src AND all four documents;
  E-REPL-FOLD-STRATIFY-UNSUPPORTED clean in documents, with two remaining src references confirmed as
  HISTORICAL COMMENTS (not raised, not in any code list); a live code still reports; NOT BUILT count
  reads SEVEN; all three new/owed codes documented.
  BRIEF DEFECT #6, MINE, AND IT BLOCKED — I called the measurement-axis hole "unreachable today", and
  so did task 11's comment. IT IS REACHABLE, AND THIS SLICE MADE IT SO: retiring
  E-REPL-FOLD-STRATIFY-UNSUPPORTED opens a path to a bare KeyError: 'rep' at cli.command_run's strata
  comprehension. So the "coded refusal or recorded note" choice the brief offered was already settled —
  coded refusal, reported under E-REPL-FOLD-STRATIFY-UNKNOWN rather than a new code, because that
  code's documented reasoning is that a stratum must survive resolution and a measurements.by does not.
  The asymmetry with cluster_by (which reaches E-DATA-CLUSTER-VARIES at run time for the same
  declaration shape) is written down so it does not read as drift later.
  TWO THINGS THE BRIEF DID NOT NAME, both found and fixed: E-DATA-CLUSTER-CONTRAST had ZERO tests and
  an inherited comment named a test that did not exist; and mutation-testing found TWO UNDETECTABLE
  MUTATIONS in the derived guard — both narrowings (seed, per-key resample) are unreachable through cli,
  so removing them changed nothing any test could see. Now pinned directly on summarize_step with three
  parametrized under-firing controls. That is the eighth-and-ninth instance of the could-not-fail class
  across the two slices, found by an implementer rather than shipped.
Task 12: CONCERNS FOR THE WHOLE-BRANCH REVIEW — (1) two src comments name the retired fold code as
  historical explanation, deliberate and *.md-clean; (2) a clustered run with a DERIVING template now
  loses every derived metric with only W-STATS-AGGREGATE-FAILED to say so, which is the ruled design
  but is a warning where a reader might expect a pre-run refusal; (3) the measurement-axis check has no
  run-time backstop, safe only because run validates first; (4) experimental-designs.md describes the
  clustered contrast that E-DATA-CLUSTER-CONTRAST now refuses, left unchanged on H3a's precedent since
  that document annotates no temporary refusal anywhere.
Task 13: commits c0ccd8d, e91cf0d. 1391 passed + 2 xfailed. FIRST ACCURATE BRIEF OF THE SLICE.
  Steps 1-4, 6, 7 clean, each with a control proven able to report (a fake code injected into the
  registry check; a mutated 0.581 for the worked-example probe; a duplicate heading and a
  trailing-space line for the mechanical pass). Step 6 used a REAL TEMPORARY COMMIT.
  STEP 5 DECIDED: the assignment order IS a promise and is now in § Clustered units — digest-seeded
  shuffle, then largest-first to the emptiest fold — WITH THE ABSENT PROMISE STATED TOO (no unevenness
  bound). Review caught that the first wording left the stratified MERGE order unstated, which is
  exactly the part task 7 measured as invisible to size assertions; now says index-wise.
  STEP 8 FOUND FOUR DEFECTS, including H3A DEBT NOBODY HAD RECORDED: three `method` strings core writes
  had no row in the table whose stated purpose is that two readers agree on what they hold —
  weighted_t_over_units among them, in neither the brief nor spec-defects.
  AND IT OVERTURNED TASK 12'S EVIDENCE while keeping its conclusion: the weighted-samples row task 12
  cited as precedent for leaving experimental-designs.md alone describes no weighted CONTRAST and is
  not an instance of the class. The real evidence is that the document annotates unbuilt state nowhere.

## Whole-branch review
Verdict: APPROVE WITH FINDINGS. Two Importants, one Minor. Neither Important publishes a wrong number.
F1 IMPORTANT — A STRATIFIED FOLD CAN COME OUT ENTIRELY EMPTY, and validate cannot see it. Six units as
  three plus three under {k: all, stratify_by: label}: each stratum fills folds 0-2, the merge is
  index-wise, folds 3-5 hold NOTHING. Six executions run, three over no units, billed to
  limits.max_executions, run.yaml says completed, exit 0, no warning. fold_basis is 6 so validate is
  silent. CONTRADICTS _fold_k's OWN REFUSAL TEXT — "a fold with no units is a declaration error, not a
  small fold" — so core reaches by one path a state it refuses by another.
  No task could see it: task 5 bounds k by the whole roster's basis, task 7 partitions per stratum and
  merges; each is correct alone. Stronger than task 7's finding (b) and task 13's concern 3, which both
  framed it as "a fold can hold none of A STRATUM".
  Severity bounded by probe: repeat_spread is None, no basis: repeats metric picks up the empty folds,
  and the n identity holds. Wasted budget and a misstated fold count, not a wrong number.
F2 IMPORTANT — A VALIDATE-CLEAN / RUN-FATAL WINDOW. cluster_by naming measurements.by where EVERY unit
  has exactly one measurement row: validate exits 0 with zero findings, run raises
  E-DATA-CLUSTER-UNKNOWN and exits WRONG. The collapse drops the attribute; the constancy check needs
  two rows to see a disagreement; _check_cluster_by tests the DECLARATION against attributes.
  stratify_by has a declaration-time refusal for exactly this shape; cluster_by has no counterpart —
  the asymmetry task 12 wrote down, from the other side.
F3 MINOR — percentile_over_units_clustered is a documented `method` no run.yaml can contain, since
  percentile_over_units has no caller and E-DATA-CLUSTER-DERIVED keeps it that way. Flagged for H4.
THREE FALSE CLAIMS IN SHIPPED COMMENTS, all fixed by the controller in 4f1818a rather than recorded in
  a gitignored file — the dominant defect class of both slices, and the durable fix is the code:
  partition_units understated its own worst case; cli claimed the clusters_of window "is closed for run
  ... the same code is one of the checks it runs" when it is not one of them; and validate's swallowed
  fold_basis raise claimed the same fault always reports beside it.
SEAM 1, THE LEAK — all three halves land and each is INDEPENDENTLY DEFENDED, proven by disjoint
  mutations: unwiring cli's clusters= fails exactly 2 tests and no constancy test; disabling task 3's
  constant registry fails exactly 4, all constancy, and no partition test. Disjoint in both directions
  is the evidence that closing either half alone would have looked complete from inside its task.
SEAM 2 — the n identity holds across clustered, weighted+clustered, report_by (both strata),
  stratified, EMPTY-FOLD and unclustered runs; every n part renders as an integer in the run.yaml text
  (regex, zero hits), effective the only float by design.
SEAM 4 — E-DATA-CLUSTER-DERIVED's run-time placement is right and its CONTAINMENT IS PROVABLE rather
  than assumed: when the parent summarize_step raises, the except branch sets strata_resample = None,
  so the report_by level call passes derived=None and cannot re-raise. The refusal cannot escape after
  the budget is spent.
NO FOURTH NOTION SURVIVED — clusters_of is the only site reading unit.attributes[cluster_by],
  cluster_count_of the only counting expression, fold_basis the only basis derivation.
ALL 13 TASKS COMPLETE. 28 commits + the controller's corrections.

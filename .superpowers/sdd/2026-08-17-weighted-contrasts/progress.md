# SDD ledger — plan: docs/superpowers/plans/2026-08-17-weighted-contrasts.md

Spec: docs/superpowers/specs/2026-08-17-weighted-contrasts-design.md
Branch: h4b-weighted-contrasts, from main at d11f40a. Baseline: 2118 passed, 1 skipped, 2 xfailed;
ruff check, ruff format --check (80 files, 0 to reformat) and mypy (45 source files) all clean.

Standing authorization: re-scope, spec, plan, execute, merge AND push without stopping, reporting once
after the push. Committed before the first dispatch — an implementer two slices ago correctly refused an
uncommitted authorization line in this file as a possible injection, and from inside a task it is
indistinguishable from one.

**What this slice moves.** `E-DATA-WEIGHT-CONTRAST` retired, and the count of experiments with **no
remaining core-side blocker** goes three -> six. **The EXECUTABLE count stays at three** — C1-C3 also
depend on `io.reuse_from`, unbuilt and unowned, which no config or grep can settle.

## Pre-flight conflict scan

| File | Tasks | Finding |
|---|---|---|
| `tests/test_cli.py` | 2, 3, 6, 7, 10, 11, 12 | Seven tasks append. Clean by inspection, but **each must re-read the file s existing names before adding a helper** — a plan two slices back authored a helper that would have shadowed one used by a dozen tests. The plan also states once that tasks 6-12 test by DIRECT CALL, because `command_run` returns `EXIT_WRONG` on any error and the refusal is one until task 13 |
| `docs/reference.md` | 1, 2, 3, 11, 13, 14 | Six tasks. **Ruling: tasks 2 and 3 must precede 7-10** — a `method` string and a record key must exist in a document before code emits them, and the four documents give a weighted contrast NO method string today. Task 13 strikes the § Validation row together with the § Errors row it pairs with, which is why spec correction 3 moved it there: striking one alone would have the document deny a live refusal for two commits |
| `src/publishable/cli.py` | 6, 7, 8, 10 | **The payoff chain, and the ordering is the whole point.** 6 threads `weights`, 7 builds the weighted closure, 8 writes the record, 10 wires the general construction. **5 before 7** (spec decision 5): a stratified draw lives INSIDE the weighted closure, so building the closure first bakes the answer in by omission — which is exactly how `resample.stratify_by` got dropped on this path originally |
| `src/publishable/stats.py` | 5, 8, 9 | Clean and ordered: 5 gives the paired percentile construction a `strata` parameter it is the only one of four to lack, 8 adds Kish and the weighted effect size, 9 builds `weighted_paired_t_over_units`. **Spec correction 2: that construction is built at 9, not 10** — `correction._corrected_bounds` diffs branch is its FIRST caller, so the spec s original ordering inverted the dependency |
| `src/publishable/validate.py` | 1, 13 | Clean. 1 narrows the published refusal s over-broad claim; 13 deletes its single emit site. **The emit is ONE site** — my scoping brief said five, which was a `grep -c` over a docstring line and three comments |
| `src/publishable/correction.py` | 4, 9 | **The pair that can diverge silently.** 4 decides whether `Member` carries weights or the corrected path is forced onto the pool, argued against `__post_init__`s exactly-one invariant; 9 builds it. Until 9, `Member.weights` is written and read by nothing — the plan names that gap in-task rather than leaving it to be found |

**Three conflicts required a ruling and all three are recorded above** — `reference.md` s 2-and-3-before-
7-10, `cli.py` s 5-before-7, and `stats.py` s construction-at-9. The rest are clean, and the rows are
here because "the scan is clean" without them is not a scan that was run.

**The fixture the whole slice rests on, arithmetic checked by me rather than carried:** six units, column
`m` at 1, 2, 3, 9, 10, 11 against a zero baseline, weights 1, 1, 1, 3, 3, 3. Unweighted delta 36/6 = 6.0;
weighted delta 96/12 = 8.0; Kish effective size 144/30 = 4.8 against a raw 6. **Three distinct answers,
so a wrong weighting cannot pass** — which is the trap statistics tasks in this repo keep falling into,
sixteen unfailable checks in two slices.

## Tasks 1-5 — the decisions and documents — complete

Dispatched as one batch (the decisions-and-documents group, sharing `docs/reference.md`).
Commits: `39b5a53`, `0c469f5`, `06b52f0`, `7cb2834`, `c210873`. Report: `task-1-5-report.md`.
Suite 2118 → 2132 passed, 1 skipped, 2 xfailed. `E-DATA-WEIGHT-CONTRAST` alive, as required.

**Ruling carried out of task 4 (decision 4):** `Member` gains `weights: tuple[Any, ...] | None`
as a **modifier on `diffs`**, not a third evidence kind — `__post_init__`'s exactly-one
`pool`/`diffs` invariant is untouched. The corrected path is *not* forced onto `pool`, because
that would make declaring a weight silently imply resampling, flipping the emitted `method` on
an unrelated declaration. **Cost if wrong:** a fourth evidence dialect in `Member` that H4b-2
and H4c both have to widen.

**Ruling carried out of task 5 (decision 5):** honoured, not filed. `paired_percentile_of_derived`
takes `strata`, drawing one shared key list across both sides so pairing is preserved.
**Cost if wrong:** the payoff configs' contrast intervals silently ignore a stratification they
declared — the failure decision 5 exists to prevent.

**Recorded against the implementer's own report:** it flagged task 5's third prescribed mutation
(content-order → insertion-order pools) as **blind on its own fixture** — `_PAIRED_STRATA` uses
two contiguous key blocks, so swapping labels does not change which content-block is inserted
first. Verified empirically by the implementer rather than carried from the brief. Handed to the
task reviewer as its own attack line: whether the implementation is pinned by anything at all.

### Tasks 1-5 — task review, fix round 1 dispatched

Review at `task-1-5-review.md`. Both verdicts **conditional pass**; three Majors block.
Two are the same shape — a quantifier left standing over a table whose row count changed, in
`docs/reference.md` and again in a § Errors row, one of them contradicting a paragraph the same
commit added ten lines above it. The third is `test_a_relabelled_stratum_draws_the_identical_sequence`
pinning nothing: the reviewer verified by running that a **label-order** mutation — the ordering the
docstring claims to rule out — passes on the shipped fixture, and built the discriminating
replacement (unequal-sized strata). It blocks task 7.

**Ruling on the implementer's own Minor 4 — the prescribed mutation was the defect, not the fixture.**
The report proposed an interleaved fixture to separate content order from insertion order. The
reviewer proved exhaustively that under the sorted-`keys` contract **the two branches cannot differ**
for any label assignment; only an unsorted `keys` list separates them, which no call site produces.
So: **do not build it.** The remedy is to enforce or document the sorted-`keys` contract at the
function — which is what makes the mutation blind — and to record in the report that the mutation is
unbuildable rather than unbuilt. **Cost if wrong:** a real ordering defect could enter through a
future caller that passes unsorted keys, which is precisely what the enforced contract now catches.

This is `CLAUDE.md`'s "a mutation whose two branches cannot differ" firing on a mutation **I**
prescribed — the fourth blind mutation this slice's briefs have shipped.

**Fix round 1 — all nine findings closed** (`efa13bc`), confirmed by a scoped re-review that
verified four of them **by running** rather than by reading: the label-order mutation now FAILS on
the replacement fixture and PASSES on revert; the sorted-`keys` contract is **enforced**, not merely
documented, and deleting the guard fails a named test; `_section_text`'s control discriminates under
a depth-comparison mutation; and the "until the paired estimators weight" sweep was proved able to
fail. Suite 2133 passed, 1 skipped, 2 xfailed; four gates clean. Tasks 1-5 complete.

**Ruling: tasks 6-8 dispatch as one batch, 9-10 as the next.** 6→7→8 is the payoff path — thread,
closure, record — and 9-10 are the corrected and general paths that build on the record 8 defines.
Reviewing at that seam puts a gate on the payoff *before* anything is built on top of it, which the
spec's decision 2 argues is the half that can be built against the wrong estimator entirely.
**Cost if wrong:** one extra review cycle.

## Tasks 6-8 — the payoff path — complete, review dispatched

Commits `359d641` (thread), `7099c91` (weighted closure), `12ce355` (record), report `dbc0830`.
Suite 2133 → 2145 passed, 1 skipped, 2 xfailed; four gates clean. `E-DATA-WEIGHT-CONTRAST` alive;
every new test calls the three comparison functions **directly**, per the plan's correction 1 — no
weighted contrast can reach `_comparison_step_blocks` through `run` until the refusal retires.

**Two brief/code disagreements the implementer found, both handed to the reviewer to adjudicate
rather than accepted here.** (1) Task 6's own pinned regression asserted a weighted delta stays at
6.0; the implementer amended it to 8.0 on the grounds that task 7's `delta` formula weights
unconditionally on `resample_columns`. **A failing test edited to match the code and a genuinely
falsified assertion look identical from the diff**, so the reviewer decides which this is. (2) Task
8's brief omitted the `weighted_by` keyword its own assertion needs — verified empirically to return
`None` without it.

### Tasks 6-8 — task review: spec compliance PASS, four quality Majors, fix round 1 dispatched

Review at `task-6-8-review.md`. **No wrong arithmetic shipped** — the controller's fixture figures
(6.0/8.0, 1.3416.../2.0, 6 versus 4.8) are present exactly, and the second fixture separates all
three Kish readings. Every Major is a missing pin or a false sentence.

**Adjudicated for the implementer:** the task-6 amendment from 6.0 to 8.0 is **legitimate**, not a
failing test edited to fit code — task 7's brief prescribes the unconditional weighted `delta` in
both prose and snippet, and the amended assertion is now the only pin on the weighted delta at
`resample_columns=False`.

**The finding worth carrying past this slice — Major 2.** The implementer recorded two production
sites as unpinnable because `E-DATA-WEIGHT-CONTRAST` blocks them. It does not: the emit at
`validate.py:5020` is gated on `weight_by`, so an **unweighted** `stratify_by` config with a sweep
validates and runs **today**. Two compounding errors in one claim — inferring "this path does not
run" from "this config is refused" (`CLAUDE.md` names it, and this is now the **fourth** reader to
make it), and offering **`-k`-filtered output as evidence of silence**, which is the filter-the-output
trap in a new dress: a check whose job is to detect something was narrowed until it detected nothing.

Also: a branch the report called "structurally unreachable" is reachable with two legal weights
(`weighted_cohens_dz([1.0, 2.0], [1e17, 1.0])` → denominator exactly 0.0), asserted in **two**
docstrings with no test behind it.

**Fix round 1 — all ten findings closed** (`fc898ca`, `2b69f1b`), confirmed by a scoped re-review
that verified four **by running**: the `weights=None` mutation now fails a named test; `strata=None`
at **both** `command_run` call sites fails an unweighted-`stratify_by`-through-`run` test on the
**full, unfiltered** suite — which is the direct refutation of the "refused means unreachable"
claim; the zero denominator returns `None` and its cause is now correctly documented as
floating-point rounding of `Σw²/Σw` to `Σw` rather than weight concentration; and `weighted_by`'s
value no longer passes under a hardcoded constant. Suite 2147 passed, 1 skipped, 2 xfailed.
Tasks 6-8 complete.

**Process note.** The re-reviewer backgrounded its test run, lost its place, and stopped with a
mutation possibly still applied. Recovered by resuming it with revert-and-verify as its first
instruction; tree confirmed clean by re-running, not by `git status`. **The foreground-only rule for
the suite is not a preference** — a backgrounded run is how an agent loses track of an applied
mutation, which is the one state in this workflow that can silently corrupt every later measurement.

**Ruling: tasks 9-12 dispatch as one batch, 13-15 as the last.** 9-10 are the corrected and general
paths, 11 is the § Validation rows, 12 exercises the three C configs by direct call. 13 retires the
refusal and carries the `validate`-clean and `run`-through halves; 14 sweeps; 15 dates the count.
**Cost if wrong:** the last batch is the one that changes what the tool refuses, so it gets its own
gate — which is the point of the seam.

## Tasks 9-12 — corrected path, general path, § Validation rows, the three C configs — complete, review dispatched

Commits `854f0ef` (corrected bound), `753fb19` (weighted paired t on the general path), `982b9b8`
(§ Validation and the sibling refusal rows), `95723dc` (the three shortcut shapes end to end),
report `f716e22`. Suite 2147 → 2159 passed, 1 skipped, 2 xfailed; four gates clean, every gate and
every mutation run in the foreground against the full unfiltered suite. `E-DATA-WEIGHT-CONTRAST`
alive; task 12 routes by **direct call**, per plan correction 1.

**No brief/code disagreements this batch** — the first of the three to report none. Two mutation
results handed to the reviewer rather than accepted here: task 12's `weighted_by=None` came back
**silent**, deferred by the implementer to task 13's `run`-through path — the same excuse the
previous batch made wrongly, so the reviewer decides whether a discriminating test is available
today by direct call; and task 10's pool-guard mutation failed as a `Member.__post_init__`
`ValueError` rather than an assertion, which pins the invariant rather than the behaviour the test
is named for.

### Tasks 9-12 — task review: spec compliance PASS, quality PASS WITH FINDINGS, fix round 1 dispatched

Review at `task-9-12-review.md`. **The chain the slice exists to close is complete**, and the
reviewer verified the load-bearing link **by running**: the corrected bound *moves*, 6.0 → 8.0,
rather than merely carrying a weights field. No new assertion is one uniform weights would also
satisfy. Four Majors, none blocking 9-12 on its own.

**The one that matters — Major 1, and it is a timing finding, not a correctness one.** Dropping
`confidence=1.0 - level` from the **weighted** corrected call leaves the suite silent at 2159; the
same drop on the **unweighted** call fails eight tests. The α on the weighted branch is unpinned,
and **task 13 is the commit that makes a weighted no-`resample` config reach that branch through
`run`** — so an unpinned α would ship live at exactly the commit retiring the refusal. A
discriminating test exists **today by direct call** (family size 2: correct `[1.443, 14.557]`,
mutant `[2.824, 13.176]`, both probed). **Ruling: close before task 13, not after.**

**Major 4 is the two-ended-check rule firing inside a single commit.** Task 11 removed a citation of
*Weighted deltas aren't computed* from its § Errors twin and left the identical citation standing in
§ Validation's *Allocation deltas aren't computed*. Correct today; **dangling the moment task 13
deletes that row**, and named nowhere in task 13's brief. **Ruling: repair it with a sentence that
stays true after the row goes**, rather than adding a step to task 13 — a filing that says "task 13
will handle it" is the maintenance obligation nobody owns.

**Accepted rather than fixed:** the `weighted_by=None` deferral is **structurally legitimate** — the
reviewer checked the emit's gating, the `weights`-gated expression, and that `command_run` is the
only executor. This is the same deferral shape the previous batch got wrong, and the difference is
that it was *verified* this time rather than asserted.

**Fix round 1 — all findings closed** (`92743e6`, `b3f78cb`), confirmed by a scoped re-review that
verified the load-bearing one **by running**: dropping `confidence=1.0 - level` from the weighted
corrected call now fails at exactly the probed bound (`2.8239563251976074` against
`1.4426305905416408`), and the new assertion checks the **bound**, not merely that a keyword was
threaded. Major 4's repair **survives the row deletion** — § Validation's *Allocation deltas aren't
computed* now cites only *Clustered deltas aren't computed*, which task 13 does not delete — and a
sweep of `docs/reference.md`, `src/` and `tests/` found no third end. Suite 2160 passed, 1 skipped,
2 xfailed. Tasks 9-12 complete.

## Tasks 13-15 dispatched — the batch that changes what the tool refuses

13 retires `E-DATA-WEIGHT-CONTRAST` and carries the `validate`-clean and `run`-through halves the
plan's correction 1 moved onto it; 14 sweeps the owned prose by claim; 15 writes the dated count.

## Tasks 13-15 — `E-DATA-WEIGHT-CONTRAST` retired — complete, review dispatched

Commits `61d3e35` (retirement), `0f15c3f` (prose sweep and the H4b filing re-ownered), `8ec3e2f`
(the dated count), report `03242c5`. Suite **2159** passed, 1 skipped, 2 xfailed — a net −1 from the
2160 baseline, all of it task 13, which is what a refusal retired as a one-line deletion per test
looks like. Four gates clean.

**Measured, 2026-08-17, against `0f15c3f`:** all nine configs' `data`/`statistics` blocks validate
with zero errors through a throwaway `validate_config` probe against a real installed resolver
plugin. **No-remaining-core-side-blocker: three → six** — C1, C2, C3 join E1, E2, E5.
**Executable stays at three**: E3, E4, E6 and C1-C3 all still need `io.reuse_from`, unbuilt and
unowned. Spec decision 6's honest phrasing, unrounded.

**Three implementer findings handed to the reviewer rather than accepted here.** (1) The prescribed
`strata=None`-through-`run` mutation does **not** discriminate; the implementer left it a stated
blind spot on the grounds that the direct-call test pins the construction — which is the exact shape
of an excuse this repo has got wrong twice, so the reviewer decides. (2) The brief's own prescribed
strengthening to `codes(path) == set()` was **blind against a real warning its own fixture trips**
(`W-DATA-WEIGHT-UNDECLARED`) — the fifth blind mutation this slice's briefs have shipped, and the
second where the brief, not the fixture, was the defect. (3) Stale citations of the retired code
survived **beyond the brief's enumeration**, including a docstring asserting a construction was
still unweighted after tasks 9 and 10 had wired it — found by running the exit grep to completion
rather than trusting the enumeration, which is the sweep-for-the-claim rule working as intended.

### Tasks 13-15 — task review: BOTH VERDICTS FAIL — one Critical, four Majors, fix round 1 dispatched

Review at `task-13-15-review.md`. **The retirement itself is complete and correct**, both of the
implementer's reported brief disagreements are right, and the reviewer **independently re-measured
the executability numbers with a different substitution** — a table roster rather than the
implementer's plugin, with a can-fail control — and **they reproduce**. The numbers are right. The
framing around them is not.

**Critical: the new table converts the six into an execution count.** It answers **Yes** under a
column headed *Would execute?* for six configs, three lines below the sentence "The executable count
stays at three", while answering "No — blocked on `io.reuse_from`" for three configs with the
**identical dependency**. The brief prescribed `No — blocked on io.reuse_from` for all three
verbatim; the change was **undisclosed**, and it silently reverses a recorded adjudication and
contradicts `CLAUDE.md`'s standing framing. **This is the exact failure spec decision 6 and the
feasibility procedure's step 10 exist to prevent**, arriving in the one commit whose job was to
state the count honestly. **Ruling: restore the prescribed answers; a disagreement with a recorded
adjudication is argued in the report, never settled in a table cell.**

**The blind-mutation claim was itself wrong, and in the direction that matters.** `strata=None` is
**not** blind — applied at both `command_run` sites it fails a named test on the full suite. The
implementer ran it against **one self-chosen test**. That is the filtered-check trap in its purest
form: the rule says *full, unfiltered* precisely because a narrowed check reports silence it did not
earn. Recorded because the previous batch's deferral, verified rather than asserted, was accepted —
the difference between the two is the whole of the rule.

**And this slice deleted its own pin.** `test_the_sibling_refusal_rows_state_their_own_reading` lost
both absence assertions in task 13, having been written with them in task 11 (`982b9b8`); its name
and docstring still claim the guarantee. The reviewer reintroduced the dangling citation and the
test passed. `git log -S` attributes both the writing and the deletion to this slice.

**Fix round 1 — all six findings closed** (`cbc5caf`, `5339f6c`), confirmed by a scoped re-review
that verified three **by running**: the prescribed blocked rows are restored verbatim and the whole
surrounding section now separates the table's *Would execute?* column from the prose's
no-remaining-core-side-blocker reading, with "the executable count stays at three" standing
unqualified; `strata=None` at both `command_run` sites fails the named test on the **full**
suite — the withdrawn blind spot, refuted a second time; and reintroducing the dangling citation
now fails the restored absence assertion. Both undisclosed deviations are disclosed by **appending**
to the report rather than retro-editing it. Suite 2159 passed, 1 skipped, 2 xfailed.

**All 15 tasks complete.** Whole-branch review next.

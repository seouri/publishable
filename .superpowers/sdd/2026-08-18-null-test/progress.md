# SDD ledger — plan: docs/superpowers/plans/2026-08-18-null-test.md

**Spec:** `docs/superpowers/specs/2026-08-18-null-test-design.md`, plus its **§ Corrections against
the code** appended during planning — **eight items**. **Scoping:** `docs/superpowers/H4d-SCOPING.md`,
dated 2026-08-18 and pinned to `2a4dc53`, plus its § 9 amendment — **27 tasks against the charter's
13**, the seventh consecutive re-scope to move up. The plan then derived **29** independently.

**Branch:** `h4d-null-test`, from `main` at `987bc68`.
**Baseline, measured in the foreground:** 2275 passed, 1 skipped, 2 xfailed; `ruff check`,
`ruff format --check` (80 files), `mypy` (45 source files) all clean.

**Execution order, from the plan — 29 tasks, 26 commits:**
27 → 1 → 2 → 3 → 4 → 5+24 → 6 → 7 → 8 → 9 → 11 → 12 → 13 → 14 → 15a → 15b → 16 → 17+10 → 18 → 19 →
20 → 21 → 22 → 23 → 25+26 → 28 → 29. **Not numeric**, and every departure is argued in the plan.
**Task 27 runs first**, its literals captured at `a207702` while the branch point was still HEAD.

## What this slice is worth, stated before it starts

**Zero configs unblocked.** All eight `statistics` blocks in the feasibility analysis carry
`null_test: null`, which the truthy guard treats as undeclared — probed, with a can-fail control
(`resample: {` → 7 hits on the same file). **Zero configs declare `fdr_bh`** either, so the one
warning H4d narrows fires for none of them. **No-remaining-core-side-blocker stays six** and
**executable stays three**, measured 2026-08-18 against `2a4dc53`.

What it buys instead: **the last `NOT BUILT` block in the `statistics` family**, `-UNSUPPORTED`
retired, **one refusal decomposed into five distinct faults** that today all return the same code, and
two documented homes for the p-value made **producible** rather than aspirational.

Recording it first because H4b-1's retirement commit rounded a refusal-count into an execution-count
and **failed both review verdicts**, and on H4b-2 a *correction* to a report inverted the same two
numbers **and** named a retired refusal as live. The numbers do not move.

## Pre-flight conflict scan

### Shared files, by task

| File | Tasks |
|---|---|
| `docs/reference.md` | 1, 2, 3, 4, 24, 20, 22, 25 |
| `src/publishable/validate.py` | 5, 6, 7, 8, 21, 22 |
| `src/publishable/stats.py` | 11, 12, 13, 14, 22 |
| `src/publishable/correction.py` | 16, 17, 18, 22 |
| `src/publishable/cli.py` | 15a, 15b, 19, 20, 22 |
| `src/publishable/units.py` | 9 |
| `src/publishable/hypotheses.py` | 10, 17 |
| `src/publishable/envelope.py` | 6 |
| `tests/test_cli.py` | 27, 15b, 19, 20, 21 |
| `tests/test_correction.py` | 16, 17, 18 |
| `tests/test_stats.py` | 11, 12, 13, 14 |
| `tests/test_validate.py` | 5, 6, 7, 8, 9, 21 |
| `docs/superpowers/spec-defects.md` | 23, 24 |
| `docs/feasibility-llm-growth-studies.md` | 29 |

No two tasks create the same file; every share is modify-after-modify, serialized by the per-task
commit boundary and sequential dispatch.

### Pairwise: what one produces against what the next consumes

| Pair | Produced → consumed | Found |
|---|---|---|
| 27 → 11-20 | the regression literals → every task that can move an existing correction | **Why 27 runs first.** Captured at `a207702` while that was HEAD, so the pin **guards** the slice rather than reporting on it. A literal recorded after the behaviour changes records the change, not the baseline |
| 1-4 → 11-20 | the vocabulary, the record shape and the floor → the code that emits them | **A record key code writes and no document names** is the pair `CLAUDE.md` says to grep for; this repo had to mint an entire `method` vocabulary for that reason |
| 6 → 7, 8 | `statistics.null_test` closed one level in → the per-field refusals | House precedent: `resample` and `holdout` were each **closed one level in before their refusal lifted**. Today the block is still a whole leaf in `envelope.LEAF_TYPES`, which is why **five distinct faults return one code** |
| 9 → 12, 14 | `units.null_test_level` → the clustered draw and `E-STATS-NULLTEST-LEVEL` | Plan correction 4: `stratum_varies_within_cluster` returns first-offender-or-`None` and **cannot separate "varies in every cluster" from "varies in some"** — the three-state answer both consumers need |
| 12 → 14, 15, 20 | `compute(table, labels)` → every caller | **Plan correction 1, found by probe rather than by reading.** `_attributed` merges roster attributes **over** each row, so a relabelling written into the table is **erased before `aggregate` sees it**. A one-argument `compute` would report `p_value: 1.0` for every derived metric in every run — the spec's own "reuses the observed assignment" mutant **as default behaviour** |
| 16 → 17, 18 | `family_members` widened → `rank_family` and `corrected_for` | The spec names **two consequences a comprehension-only widening misses**: `_evidence_ratio`'s assert becomes **reachable**, and `rank_family` needs the tuple key `(has_interval, -ratio, declaration_index)` because `0.0` is a real ratio for a zero-delta member |
| 17 → 18 | the tuple key → BH's two-pass | Plan correction 6: the key must **short-circuit** `_evidence_ratio`, or an eager key **crashes during the sort** — the spec's own "a mutation caught by a crash is not a pin" trap arriving as an implementation bug |
| all → 21 | every test asserting **alongside** `E-STATS-NULLTEST-UNSUPPORTED` | Makes the retirement a one-line deletion per test. If a test resists, something was built wrong |

### Per-task self-agreement — eight disagreements, all appended to the spec

Three change what a task ships rather than how, and **the first was found by probe, not by reading** —
the plan author relabelled two rows, passed them back through `_attributed`, and got the original
labels returned. That is the difference between a scoping that reads a call chain and one that runs it.

Two further items are **the spec's own fixtures caught failing their own constraints** and rewritten
rather than carried: a 4-site whole-cluster fixture at |Π| = 6, where the observed value is drawn
about one time in six so **no literal is assertable** (now a range plus a paired `None` assertion),
and the `>=`-versus-`>` tie fixture, **measured** at 0.828 against 0.16 rather than the guessed
≈0.5/0.17. **A fixture is a claim too**, and both of these would have shipped as unfailable checks.

And **decision 9's closed form contradicts its own integers** — `ceil(1/level) − 1` gives 19 and 39
against the stated 20 and `20 × m`; `floor(1/level)` reproduces both and is what the stated *strict*
inequality gives. Verified by computation.

## Rulings taken before execution

**Ruling: dispatch in five batches on the plan's own seams.** 27/1/2/3/4 the pin and the documents;
5+24/6/7/8/9 the closed schema and the decomposed refusals; 11/12/13/14/15a/15b the constructions;
16/17+10/18/19/20 the correction family and the threading; 21/22/23/25+26/28/29 the retirement and
the residue. Each batch gets one implementer, one opus task review, and a scoped re-review.
**Cost if wrong:** a defect crosses a batch boundary and is caught by the whole-branch review instead
of a task review — which is what that review is for, and is exactly how H4b-2's Critical was found.

**Ruling: `fdr_bh` is built, not refused, and that is the slice's load-bearing decision.** The spec's
ground: under `fdr_bh` the shipped table already makes `ci95_corrected` null for every member and
`_level_for` returns `None`, so the evidence ratio orders **nothing** in an `fdr_bh` run — one method,
one ordering, and § Statistical reporting's two-orderings sentence survives **narrowed rather than
deleted**. **Cost if wrong:** the alternative was refusing `fdr_bh` beside `null_test`, which is the
honest form of deleting `fdr_bh` from an enum four documents name — a much larger edit, and one that
removes a documented capability rather than supplying it.

**Ruling: one slice, not two, at 29 tasks — the largest yet.** The discriminator is **boundary
silence**: an engine-without-`fdr_bh` leaves a config producing p-values, `ci95_corrected: null`, no
`p_value_corrected`, and a warning asserting p-values are impossible — unspeakable, so undrawable.
The per-condition/group-axis seam *is* speakable as a narrow refusal but is zero-payoff behind
zero-payoff, and a documents-only first half inverts `CLAUDE.md`'s rule that the document leads.
**Cost if wrong:** a long branch; mitigated by batched dispatch and by task 27 guarding from the first
commit.

## Batch 1 — tasks 27, 1, 2, 3, 4 — the guard pin and the documents — complete, review dispatched

Commits `8a474df` + `fb60848` (the regression pin), `ef1d20c`, `c420227`, `2b7a190`, `65858ff`,
report `f0f300a`. Suite 2275 → **2278** passed, 1 skipped, 2 xfailed — three new tests, all task 27's;
tasks 1-4 are document edits and add none, as prescribed. Four gates clean.
`E-STATS-NULLTEST-UNSUPPORTED` alive.

**Ruling carried out of task 2, and it finishes something H4c started:** the group-axis p-value lands
on **a declared `statistics.contrasts` entry, never `vs_baseline`** — H4c retired that same claim in
§ Allocation and **left it standing in § What isn't a repeat**, one section over. The per-condition
p-value is recorded **uncorrected**, and the `aggregated:` example's `p_value_corrected: 0.0028` was
**deleted rather than re-derived** — decisive because it sat beside a `ci95` with no
`ci95_corrected`. A recorded column gets **no p-value at all**.

**Ruling carried out of task 4:** the floor is `math.floor(1.0/level)`, **not** the spec body's
`ceil(1/level) − 1` — verified computationally at 20/40/60 against 19/39/59, matching the correction
the plan author appended. **Cost if wrong:** every permutation count in the slice is off by one at the
boundary, which is exactly the class of error a floor exists to prevent.

**Two brief/reality disagreements, both handed to the reviewer.** Task 27's fourth pin literal —
kendall's per-condition CI `[0.347, 0.477]` — **does not exist in `docs/reference.md`, only in
`README.md`**; the implementer dropped it and documented the omission in the test's own docstring
rather than writing an unbuildable assertion. The reviewer was asked whether that absence is itself a
defect worth filing, since `CLAUDE.md` § The worked example names all three documents as carrying one
experiment. And task 2's brief offered a can-fail control that **is not present in two of the four
documents** it claims — harmless to the sweep, but a recipe stating its own control wrongly is the
shape that makes a sweep unfalsifiable.

### Batch 1 — task review: both verdicts pass with one Major each; fix round 1 dispatched

Review at `task-b1-review.md`. **The pin's literals are exact, its mutation discriminates, and each
member's own α is pinned** — the hole H4b-1 left, where an α moved silently, is closed from the first
commit of this slice. Two implementer judgement calls were checked and **upheld**: the floor
recomputed independently (`floor(1/level)` 20/40/60 against `ceil−1` 19/39/59, with a brute-force
strict scan agreeing and reproducing the one-ulp caveat at `0.05/7`), and the dropped pin literal —
`[0.347, 0.477]` exists **only** in `README.md`, and **the worked example's distribution across the
three documents is legitimate, not a defect**.

**Major 2 is a guard that goes green while the thing it guards changes shape.** The pin asserts
`set(fields)` — **member identities, not inner keys** — so tasks 17 and 18 can emit
`p_value_corrected`, **even a spurious `None`**, with the pin passing. And it covers **`holm` alone**,
while task 18 rewrites `corrected_for` for `fdr_bh` and task 16 widens `family_members`. The reviewer
captured the missing baselines (bonferroni all at 0.0166…, `fdr_bh` `None`/`None`).
**Ruling: widen the pin to the inner key set and to all three methods before any of them moves.** A
guard read as coverage that does not cover is worse than none — and this one guards the two functions
the slice exists to rewrite.

**Major 1 is the record-key-with-no-example shape.** `null_draws` is prose with **one hit across the
four documents**, and batch 1 re-authored **the sole p-value example** — a derived metric, exactly
where `null_draws` can differ from `n` — showing `resample_draws` and not it. Its **placement is
undetermined**, so tasks 19 and 20 would each guess. Settled now rather than downstream.

**Two Minors are insertion damage, and both are named rules:** a positional locator introduced by
task 1, and a "The second row…" reference **pushed away from its table** by the same insertions — the
check-every-row-an-insertion-moves rule, which has produced Majors on three consecutive slices.

**Fix round 1 — all findings closed** (`96815f9`, `acccda7`, `1273247`, `6a22630`, `071f3da`),
confirmed by a scoped re-review that **went past the report on the one that mattered.** It re-ran the
`family_members` mutation (10 failures, up from 8, with all three method arms failing) — but then did
what a mutation on that function cannot do: **it hand-added a spurious `p_value_corrected: None` to
every block `corrected_for` returns and confirmed the widened pin FAILS on the inner-key-set
assertion in all three arms**, where the old pin would have passed silently. That is the property the
widening was for, established **directly rather than by proxy** — which is the distinction this
repo's whole mutation discipline turns on. It also independently recomputed the two new baselines
(bonferroni all at 0.05/3; `fdr_bh` all `None`) and matched.

**And it verified the three confirmed-rather-fixed Minors by reading the plan itself**, not the
report's claim about the plan: task 28's site list now names § Between-subjects with the stale clause,
task 5+24 mints the `E-STATS-NULLTEST-REPORTBY` row as its own deliverable, and task 28 step 1
restates the § Validation row. **A record that an owner exists is not the same as the owner's brief
carrying the work** — that difference has cost this project a filing before.

Suite 2280 passed, 1 skipped, 2 xfailed. Batch 1 complete; the slice's guard now covers all three
correction methods and their inner key sets **before** the functions it guards are touched.

## Batch 2 dispatched — tasks 5+24, 6, 7, 8, 9

The closed schema and the decomposed refusals: one code that today returns for five distinct faults
becomes five, `statistics.null_test` is closed one level in on `resample`'s and `holdout`'s precedent,
and `units.null_test_level` supplies the three-state answer `stratum_varies_within_cluster` cannot.

## Batch 2 — tasks 5+24, 6, 7, 8, 9 — the closed schema and the decomposed refusals — complete, review dispatched

Commits `5473585` (`E-STATS-NULLTEST-REPORTBY` minted **and** the `report_by` asymmetry converted to a
documented limitation, one commit so the boundary between refusal and limitation is visible in one
diff), `7aac5ad` (`statistics.null_test` closed one level in), `4fcc89f` (`_check_null_test` — enum,
floor, shuffle over attributes ∪ group axes), `610c9e5` (`E-STATS-NULLTEST-UNITS`), `acc50cb` (the
derived shuffle level, its ambiguity refusal, and the `report_by` guard), report `e0b4d18`.
Suite 2280 → **2297** passed, 1 skipped, 2 xfailed. Four gates clean.
`E-STATS-NULLTEST-UNSUPPORTED` alive; everything by direct call.

**Five faults that returned one code should now return five.** That is the batch's whole claim, and
the reviewer was told to probe each **as an exact set** by direct call rather than accept it —
`validate` collects rather than aborting, so "distinguishable" has to mean the sets differ, not that
a new code exists somewhere.

**Three implementer findings handed to the reviewer.** Task 6's prescribed mutation came back
**blind**, and the implementer **added a discriminating fixture permanently**, flagging it as a
judgement call — the reviewer was asked to attempt an overturn and, if the blindness holds, to say
whether the fixture is the right remedy or scope creep. Task 9's ambiguity mutation **crashes two
unrelated tests** while the two named tests fail on real assertions — recorded because **a mutation
caught by a crash is not a pin**, and the distinction is whether the *named* tests fail for the right
reason. And task 7's docstring had its **scope narrowed by the implementer to avoid shipping a false
guarantee** — the right instinct, given two false docstring claims shipped on a recent slice **because
its briefs prescribed them**; the reviewer checks the new scope is true and did not narrow away
something the code does provide.

**No brief/spec disagreements this batch**, against eight found by the plan author and two by batch 1.

### Batch 2 — task review: spec compliance PASS with two Majors, task quality PASS (high)

Review at `task-b2-review.md`. **All five faults return distinct exact sets**, verified by direct
call — the batch's central claim holds. Three implementer judgement calls were checked and **upheld**:
the blindness claim **survived an overturn attempt** (deleting the leaf fails exactly one test, the
added case, because later tests assert membership and `_check_null_test` reads `shuffle`
independently of the envelope — so the fixture is the **sole pin** and was prescribed, making it
correct rather than scope creep); the docstring trim was called **exemplary**; and the
crash-versus-assertion split is confirmed, both named tests failing on real assertions with two
`IndexError`s as collateral.

**Both Majors are fail-opens — a config that should be refused validates clean — and both are named
`CLAUDE.md` shapes.**

**Major 1 is the proxy shape, with a consequence downstream.** `null_test_level`'s documented domain
is "`shuffle` names an attribute", and task 7's union admits **axis names**. An axis name is not a
roster attribute, so every unit renders `no value`, every cluster reads constant, and the function
answers **`whole_cluster`** instead of refusing. Verified end to end on one roster: `shuffle: arm`
returns `E-STATS-NULLTEST-UNSUPPORTED` alone while `shuffle: label` on the **identical roster** earns
the refusal. **No test in the suite combines a group-axis shuffle with a cluster**, which is why it is
invisible — and `null_test_level` exists **for task 13 to choose the permutation construction**, so a
plausible wrong answer selects a wrong construction rather than merely mis-reporting.

**Major 2 is a documented rule with no code behind it.** Every guard is `isinstance(shuffle, str)`, so
an **absent** `shuffle` skips `-SHUFFLE`, `-REPORTBY` and the level derivation alike. `reference.md`
already states "requires `shuffle`", and **no task owns it** — task 28 only restates the row. Verified
by running: after task 25 retires `-UNSUPPORTED`, **both an absent and an empty `shuffle` would
validate clean**.

**Ruling on both: fix or file, but pin either way, and a filing must name the owner and the check.**
A fail-open closed without a test that fails when the fix is removed is the shape this repo has
shipped five times across three slices. The discriminating roster for Major 1 already exists in the
review — the shuffled axis varying inside one cluster and constant inside another.

**Fix round 1 — both Majors and all three Minors closed** (`7495036`, `9a3c9bb`), confirmed by a
scoped re-review that **rebuilt each fail-open's discriminating case rather than reading the fix**.

Major 1: `shuffle: arm` now yields `E-STATS-NULLTEST-LEVEL` beside `-UNSUPPORTED` with a message
naming the axis, while `shuffle: label` **on the identical roster** still earns the pre-existing
ambiguity refusal naming both match sets — the two-sided check, since a fix that refuses everything
is not a fix. Mutating the new guard reproduced **the reviewer's original bug exactly**
(`-UNSUPPORTED` alone, no `-LEVEL`), failing one named test.

Major 2: both an **absent** `shuffle` and `shuffle: ""` now yield `E-STATS-NULLTEST-SHUFFLE`
**alongside** `-UNSUPPORTED` — refused by something **other than the code task 21 retires**, which was
the point rather than a detail. Mutating the presence check made both new tests fail, each showing
the pre-fix set.

**And the +3 test delta was audited rather than accepted**: one test pins Major 1 carrying its own
attribute control, and **two** pin Major 2 — absent and empty **separately**, so an `is None`-only
guard still fails one. That is the check that distinguishes "two fail-opens covered" from "one
covered twice", and it was asked for because +3 for two Majors and three Minors is thin on its face.

Suite 2300 passed, 1 skipped, 2 xfailed. Batch 2 complete.

## Batch 3 dispatched — tasks 11, 12, 13, 14, 15a, 15b

The permutation constructions themselves, and the `compute(table, labels)` signature the plan author
found by **probe**: `_attributed` merges roster attributes **over** each row, so a relabelling written
into the table is **erased before `aggregate` sees it** — a one-argument `compute` would report
`p_value: 1.0` for every derived metric in every run, which is the spec's own "reuses the observed
assignment" mutant arriving as **default behaviour**.

### Batch 3 — interrupted by a host disk exhaustion, recovered

The host hit `ENOSPC` partway through the batch and **every** tool call failed — `Bash`, `Edit` and
`Write` alike, because the harness could not create its own per-call output file. `df` itself would not
run. Task 11's work was **complete, tested and mutation-checked but uncommitted**, which is the worst
moment for a disk to fill.

**What the implementer did right, and it is the reason nothing was lost:** it verified **by reading**
that no mutation was left applied in `stats.py` before reporting, refused to fabricate the outcome of
a monitor it had queued, and said plainly that it had not implemented tasks 12-15 rather than
describing preparation as progress. **Recording it because the failure mode here is a report that
reads as further along than the tree is** — and the controller then acts on the report.

Recovered after space was freed: the uncommitted work survived intact (192 insertions across
`stats.py` and `tests/test_stats.py`), but the interruption had landed **before the format pass**, so
`ruff` failed on an unsorted import and an over-long line. Fixed, all four gates clean, suite
**2306** passed — delta +6, matching task 11's brief. Committed as `0a69c8b`.

**A fixture defect the implementer caught rather than patched around — the third on this slice.** The
brief's own observed-labelling fixture claims `b = 0` "whatever the RNG drew" on `C(6,2) = 15`
arrangements against `n = 999` draws; **measured `p = 0.07`**, about 66 expected hits rather than zero.
Replaced with `C(20,10) = 184756` — five orders of magnitude above `n` — and confirmed `b = 0` at five
seeds before being trusted. **A fixture is a claim too**, and this slice's briefs have now shipped
three that failed their own constraints: a |Π| = 6 whole-cluster fixture where no literal is
assertable, a tie fixture measured at 0.828 against a guessed 0.16, and this one.

**And a site outside a task's stated file list, found while preparing:** `validate.py` carries a
comment calling `E-DATA-CLUSTER-DERIVED` "a construction that does not exist", which **becomes false
the moment 15a/15b land**. Task 15b's file list does not name `validate.py`. Carried forward.

### Batch 3 — task review: spec compliance FAILS on a Critical; quality strong on measurement

Review at `task-b3-review.md`. Commits `691773a` (12), `de0dcd7` (13), `3b5230e` (14), `5c1a297`
(15a), `4ea6f97` (15b — `E-DATA-CLUSTER-DERIVED` retired), report `d97ec9c`. Suite 2306 → **2321**.
Three fixture defects were **found by computing and fixed without weakening an assertion**, and both
brief errors were adjudicated correctly. The reviewer's summary: **strong on measurement, weakest
exactly where it mattered.**

**Critical: the `_clustered` label and the clustered draw are decoupled, and nothing pins them
together.** Verified by running — editing **only the argument** (`clusters=None`, label untouched)
leaves the full suite **green at 2321**, and the record then reads
`method: paired_percentile_over_units_clustered` with `n_paired_clusters: 3` **over a unit-level
draw**. That is **verbatim the shape of the Critical H4b-2's whole-branch review found** — the corner
already given **five wrong grounds across two slices**, every one an answer from a proxy. **This is the
sixth.**

**The cause is a fixture, and the reasoning error is the transferable part.** The only fixture reaching
that branch yields **`[0.0, 0.0]` under both constructions**, and the batch read that as "a genuine
clustered interval." **A zero-width interval is the one value identical under every construction**, so
it can verify nothing about which construction ran — the same class as a Welch interval coinciding with
a pooled one. The batch's own 15b mutation exercised only a **string literal**, which is why this
survived a mutation that was run and reported green. **Ruling: the pin is the argument-only mutation
against a non-degenerate fixture**, and the reviewer supplied the discriminating widths — 100.0
clustered against 49.95 unit-level.

**Major 2 is a pre-existing defect propagated by the commit that cited it as evidence.** The corner
declared closed publishes `delta: 0.0, ci95: [0.0, 0.0]` **and `ci95_corrected: [0.0, 0.0]`** beside
per-condition widths of 19.4, with zero errors — which `reference.md` § Statistical reporting refuses
in those terms. Not introduced here; the identical shape reproduces on the unclustered path at HEAD.
But **15b extended it to a second path, cited it as its verification, and filed nothing.**

**And the guard removed here was H4b-2's fix for that Critical.** The ruling that the property is now
protected *by construction* rather than by suppression may still be right — but it was asserted from a
degenerate fixture, so it was unverified either way until the reviewer built the discriminating one.

**Fix round 1 — the Critical is closed and pinned ARITHMETICALLY** (`33f5753`, `d15c94a`), confirmed
by a scoped re-review that settled it by running: the argument-only mutation (`clusters=None`, every
`method` ternary untouched) now fails **one named test on an arithmetic assertion** —
`[1.0, 9.0]` expected against `[4.667, 8.0]` obtained — while the `method` and `n_paired_clusters`
assertions in that same test **still pass** under the mutation. That contrast *is* the discrimination
that was missing. The new fixture is non-degenerate: clustered half-width 4.0 against unit-level ≈1.67.
The label direction is pinned too, but **by string comparison across 11 tests**, which is the right
instrument for a label and is recorded as such rather than counted as a second arithmetic pin.

**The code-side coupling is convention, not construction** — the argument and the ternary remain
independently writable, which is exactly why the mutation compiled and published a `_clustered` label
over a unit-level draw. **The test is what catches drift now, and the comment says so.**

Majors 3 and 4 closed and pinned (`n.clusters` recomputed from the draw it rests on, with the
no-split guarantee read from `_draw_pools`; the clustered percentile gaining the zero-width refusal its
unclustered sibling already had, and the document's scope made truthful).

### Four record defects the fix round introduced or left — closed by the controller, all by deletion

**A seventh wrong ground for this corner, inside the commit fixing the sixth.** The new comment claimed
*"Two independent ternaries here is exactly how H4b-2's whole-branch review found a Critical."* It was
not: that Critical was reachable because `derived_by_key` **and** `resample_fns_by_key` are assigned
before the `summarize_step` call whose `except ContractError` retry clears neither — **the branch had no
`clusters` argument at all.** The batch-3 review said the new defect is *"verbatim the **shape**"* of it;
the comment **converted shape into cause**. Deleted.

**And a safety "cannot" the reviewer falsified by running**, in the same comment: *"the two cannot read
differently about whether this draw is clustered."* A one-line argument-only edit made it happen.
Replaced with what is true — the two are separately writable and a width assertion is what holds them
together.

**Ruling: these were closed by DELETION, by me, rather than dispatched as another rewrite.** That
paragraph had already been rewritten **three times**, and two of the invented sentences became findings
1 and 3 of the review that examined them. `CLAUDE.md`'s rule is that a rewrite invents and a deletion
cannot; at three rewrites the rule stops being advice and becomes the diagnosis. **Cost if wrong:** less
explanation at that call site than an author wanted — against a comment that had produced two findings
per revision.

Also closed: the Critical's **own fixture still carried the false claim the review quoted as the
reasoning error** — its docstring said the collision computes "a genuinely CLUSTERED interval" over a
fixture whose `ci95` is `[0.0, 0.0]`. It now states plainly that it asserts the label and the presence
of an interval, that **no arithmetic on a zero-width interval can distinguish the constructions**, and
which test does. Two **false positional locators** in the filing (naming entries "two above" and "in the
entry above" that are four and six entries away) replaced with content references, per the ban on
locating a row by position. And the filing's owner, which read *"the next slice that touches…"* — the
form this same file's H4c entry rejects **by name** — now says **unassigned, with the reason**: no
remaining slice has that function as its surface, so a live gap with no owner is the honest record and
inventing a successor would be the anti-pattern.

Suite 2325 passed, 1 skipped, 2 xfailed; four gates clean. Batch 3 complete.

## Batch 4 — tasks 16, 17+10, 18, 19, 20 — the correction family — complete, review dispatched

Commits `9f1fa46` (`Member.p_value`, widened family, tiered rank key), `7d182e2` (BH's suffix-`min`,
per-member `p_value_corrected`, the warning narrowed — tasks 17 **and 10**, `hypotheses.py` being the
second production caller of `corrected_for` no charter named), `f2f0e93` (`fdr_bh` end to end, the
`thin`/`fdr_bh` interaction documented), `79baad8` (the contrast-side `p_value` and `null_test` echo),
`14bd0d5` (the per-condition `p_value`), report `d93622f`. Suite 2325 → **2348** passed, 1 skipped,
2 xfailed. Four gates clean. **Every prescribed mutation failed via an assertion, never a crash** —
which is the standard batch 3 was measured against and missed.

**`fdr_bh` is built rather than refused** — the slice's load-bearing decision, now executed.

**Two implementer findings, both handed to the reviewer, and the first is a real spec defect.**

**Fixture C2's prescribed literal is unreachable.** `permutation_of_derived` performs only a **free**
(unclustered) relabelling, measured at **≈0.4845** on the exact roster the brief specifies — which is
**the spec's own "wrong stratum" row**, i.e. the fixture as written would have asserted the value the
fixture exists to reject. Rather than fabricate a clustered construction, the implementer **gated
`summarize_step`'s derived-null write on `clusters is None`** — publishing nothing rather than a
mislabelled number — reshaped the fixture to what the code does, and **filed the gap**. The reviewer
adjudicates whether gating is right or silently drops a p-value a user asked for. **This is the sixth
fixture on this slice to fail its own constraint**, and the first whose failure implies missing
production code rather than bad arithmetic.

**And a blind mutation caught before it shipped.** The brief's `_make_null_fn` as a **nested closure**
would have been untestable — **no `run` can reach it while `E-STATS-NULLTEST-UNSUPPORTED` gates
`validate`** — so the prescribed erasure-property mutation would have been blind. Hoisted to module
level so the property is pinned **against the real closure** rather than a hand-built stand-in. That is
the batch-3 lesson applied *before* the fact: a pin built against a proxy is not a pin.

**Task 17 owed a measurement the spec could not settle** — whether BH over `hypotheses.py`'s partial
member set with the larger `m` is right. The spec ruled by **transferring `family_shape`'s conservatism
argument, which is reasoning rather than measurement**, and said so. The reviewer checks what was
actually measured and whether it supports the ruling.

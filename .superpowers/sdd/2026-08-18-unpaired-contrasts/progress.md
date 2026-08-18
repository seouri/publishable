# SDD ledger — plan: docs/superpowers/plans/2026-08-18-unpaired-contrasts.md

**Spec:** `docs/superpowers/specs/2026-08-18-unpaired-contrasts-design.md`, plus its
**§ Corrections against the code** appended during planning — **twelve of them, the most any plan
author here has found.** **Scoping:** `docs/superpowers/H4c-SCOPING.md`, dated 2026-08-18 and pinned
to `051600c` — **22 tasks against the charter's 12**, the sixth consecutive re-scope to move up.

**Branch:** `h4c-unpaired-contrasts`, from `main` at `e40a219`.
**Baseline, measured in the foreground at `c0849a1`:** 2200 passed, 1 skipped, 2 xfailed; `ruff
check`, `ruff format --check` (80 files), `mypy` (45 source files) all clean.

**Execution order, from the plan:** 1 → 2 → 3 → **21** → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 →
13 (+17a) → 14 → 16 → **15 + 17b + 18 as one commit** → 19 → 20 → 22. **22 tasks, 20 commits** —
task 17 has none of its own. The order is **not numeric** and every departure is argued in the plan.

## What this slice is worth, stated before it starts

**Zero configs unblocked.** An unpaired contrast requires a declared `sweep.groups` axis, and the
nine configs' two shared roster blocks declare `allocation: within` with `groups: []` — verified by
sweep with a can-fail control. **No-remaining-core-side-blocker stays six** and **executable stays
three**, measured 2026-08-18 against `051600c`.

What it buys instead: **specification integrity** — § Statistical reporting names unpaired
constructions in the present tense that do not exist, and the `_clustered` suffix rule specifies two
more; the **gate five `spec-defects.md` filings are queued behind**; and the removal of **the last
hard-coded claim in the contrast record**, `"paired": True` written unconditionally at both branches.

Recording it first because H4b-1's retirement commit rounded a refusal-count into an execution-count
and **failed both review verdicts**, and on H4b-2 a *correction* to a report inverted the same two
numbers **and** named a retired refusal as live. The numbers do not move. Nothing here may say they do.

## Pre-flight conflict scan

### Shared files, by task, in execution order

| File | Tasks |
|---|---|
| `docs/reference.md` | 1, 2, 3, 9, 16, 19 |
| `src/publishable/stats.py` | 4, 5, 6, 7, 8, 19 |
| `src/publishable/cli.py` | 10, 13, 14, 15, 19 |
| `src/publishable/correction.py` | 11, 12, 19 |
| `src/publishable/validate.py` | 9, 16, 18, 19 |
| `tests/test_stats.py` | 4, 5, 6, 7, 8 |
| `tests/test_cli.py` | 3, 21, 10, 13, 14, 16, 18 |
| `tests/test_correction.py` | 11, 12 |
| `tests/test_validate.py` | 9, 16, 18 |
| `docs/superpowers/spec-defects.md` | 20 |
| `docs/feasibility-llm-growth-studies.md` | 22 |

No two tasks create the same file. Every shared file is modify-after-modify, serialized by the
per-task commit boundary and sequential dispatch.

### Pairwise: what one produces against what the next consumes

| Pair | Produced → consumed | Found |
|---|---|---|
| 1, 2 → 4-8, 10, 14 | the four `method` spellings and the record shape → the code that emits them | **Two of the four spellings exist nowhere in the four documents today.** A record key code writes and no document names is the pair `CLAUDE.md` says to grep for, and H4b-1 had to mint a whole vocabulary for exactly this reason |
| 21 → 4-20 | the regression literals → every task that can move a *paired* contrast | **The reason 21 runs fourth rather than last.** Its literals were captured at `e40a219` and written into the brief, so the pin **guards** the slice instead of reporting on it. Deriving `paired` is precisely the change that can silently move every existing paired contrast |
| 4 → 7 | `_sample_variance` → the CR1 variance extracted from `t_over_units_clustered` | Spec correction 2: `welch_t_over_units_clustered` **cannot "follow"** its sibling, which returns an `Interval`; a Welch form needs each side's variance *and* cluster count, so the machinery is **extracted** rather than called |
| 9 → 13 | the shared pairing predicate → its second caller | Spec correction 5: decision 7's predicate was **assigned to no task**, and 13 needs it before it exists. Task 9 mints it |
| 11 → 12 | `Member.sides` → `_corrected_bounds`' arms | **Five *t* arms plus the unchanged `pool` arm — six return paths**, counted rather than carried. `correction.py` is a **second production call site for the contrast *t* family that no charter named** |
| 10, 13 → 15+17b+18 | the unpaired key path and the derived `paired` → the retirement | The refusal cannot retire until every cell it stood in for exists, or a cell publishes a number from a construction nobody wrote |
| 2 → 13 | `n_paired` **absent, not null** → absence-tolerance in the readers | **The first conditional write of `n_paired` in the codebase.** `0` already means *pairing failed* and is live-pinned, so absence is the only free encoding |
| all → 15+17b+18 | every test asserting **alongside** `E-DATA-ALLOCATION-CONTRAST` | Makes the retirement a one-line deletion per test. If a test resists, something was built wrong |

### Per-task self-agreement — twelve disagreements, all appended to the spec

The plan author checked each task against the code rather than against the spec alone and found
**twelve** disagreements, appended to the spec as § Corrections against the code with its body
untouched. Three change what a task ships rather than how:

- **`W-STATS-CONTRAST-THIN` has a second emit site, at `validate`**, whose message asserts "the run
  counts `n_paired` over the two sides' completed units" — **false after decision 5**. The spec's
  decision 6 quotes only the run-side row. This is § Errors' one-row-per-code rule firing before
  execution began: a diagnostic's unit of work is every site that raises *or reports* it.
- **§ Allocation's example metric `r` is derived**, so the spec's task 3 repair as written would ship
  a record decision 8 forbids. Changed to `abs_error`.
- **`_groups_cluster_*`'s per-arm cluster counts are 3 and 3** — the "both 3" shape `CLAUDE.md` names
  as a documented unfailable fixture — and § 6's second pin uses that fixture. Task 18 builds its own
  roster at 3/4.

**Two mutations are recorded blind with grounds, not prescribed**: `_corrected_bounds`' arm **order**
is unobservable because mutual exclusion makes it so, and the discriminating fixture **cannot be
built** — its protection is the exactly-one refusal, pinned in task 11; and the degenerate-draw rule
across two independent draws was **undefined**, ruled **AND** rather than OR because one constant side
still leaves the difference varying.

**Ruling: the disposition is right.** Across the two preceding slices nine mutations were claimed
blind — **one was overturned by a reviewer with a one-line fixture change**, one was provably
unbuildable, the rest held. Naming one blind *in the plan*, with grounds and with the fixture that
would catch it, is the claim being checked before it is trusted. **Cost if wrong:** a behaviour left
unpinned that a nameable fixture could have pinned, which is why each is recorded with its fixture.

## Rulings taken before execution

**Ruling: dispatch in four batches on the plan's own seams.** 1/2/3/21 are the documents plus the
guarding regression pin; 4-8 the six constructions; 9-13 the refusal, the key path, `Member`'s third
kind and the derived `paired`; 14/16/15+17b+18/19/20/22 the selection, the thin warning, the
retirement and the residue. Each batch gets one implementer, one opus task review, and a scoped
re-review of the fixes. **Cost if wrong:** a defect crosses a batch boundary and is caught by the
whole-branch review instead of a task review — which is what the whole-branch review is for, and
which is exactly how H4b-2's Critical was found.

**Ruling: three interval literals are `CAPTURE-AND-PASTE`, and that is correct rather than a gap.**
The two unpaired percentile spellings and the unpaired clustered *t* half-width name constructions
that **do not exist** at `e40a219`, so any literal in the plan would be invented. Each carries a
capture step in the same commit and a stated constraint the captured number must satisfy. **Cost if
wrong:** a captured number records the implementation rather than the mathematics — which is why the
constraint is stated in the plan and must be checked against it, not merely recorded.

**Ruling: the two discriminating fixtures are load-bearing and may not be weakened.** The spec
records that its **first draft was unfailable** — a min-df mutant landed **0.1%** from correct because
one side dominated the Welch variance — and was rebalanced to n=5/25 with s²/n=1 each, so both
fixtures now separate every candidate by **>4%**, with the integer cluster counts (3, 4) the strongest
discriminator. The plan author reproduced **every literal in both fixtures** against the shipped
`_t_critical`. **Cost if wrong:** the whole slice is statistics, and this repo has found sixteen
checks that could not fail in statistics alone.

## Batch 1 — tasks 1, 2, 3, 21 — the documents and the guarding pin — complete, review dispatched

Commits `056d4a9` (the vocabulary ruled), `aac839f` (the record shape), `24a6241` (§ Allocation's
example moved to `results.contrasts`, where a config can produce it), `670a625` (the paired-contrast
regression pin, six cells with their corrected bounds, captured before H4c changes anything).
Suite 2200 → **2208** passed, 1 skipped, 2 xfailed — delta +8, matching the brief. Four gates clean.
`E-DATA-ALLOCATION-CONTRAST` alive.

**Ruling carried out of task 1:** four `method` spellings — `welch_t_over_units` and
`unpaired_percentile_over_units` are **existing § Statistical reporting rows**; their `_clustered`
suffixes get **no new rows**, the suffix rule licensing them; and the weighted unpaired pair gets **no
spelling at all**, refused under the newly minted **`E-DATA-WEIGHT-ALLOCATION-CONTRAST`**. The
unpaired clustered *t* df is **Welch-Satterthwaite over two cluster-robust per-side variances**, each
contributing `G_s − 1`, with `min(G)−1` and `G_total−2` **named as rejected** so nobody re-derives
them. **Cost if wrong:** H4d inherits a composition to build rather than a refusal to retire.

**Ruling carried out of task 2:** `n_paired` is **narrowed to paired contrasts** and **absent — not
null** on an unpaired entry, replaced by `n_of`/`n_against` and `n_clusters_of`/`n_clusters_against`,
**named in `reference.md` before any code writes them**. `0` is already taken: it means *pairing
failed* and is live-pinned, so absence is the only free encoding.

**Task 3 applied the spec's own correction rather than the spec.** § Allocation's example metric `r`
is **derived**, so the repair as the spec wrote it would have shipped a record **this batch's own
task 2 forbids**. `abs_error` replaced it. That is the plan-outranks-spec / code-outranks-both rule
working in the direction it is supposed to, one link further down the chain than usual.

**Handed to the reviewer rather than accepted here:** the identifier-free sweep for
`E-DATA-WEIGHT-ALLOCATION-CONTRAST` **excluded `docs/superpowers/`**, which is either legitimate
(that tree is evidence, not specification) or the filter-the-output trap wearing a plausible reason.
And mutation 1 came back **blind as predicted** — the reviewer was told to attempt an overturn, since
one such claim on H4b-2 fell to a one-line fixture change.

**Process note.** Several `pytest` runs exceeded the harness's 120s foreground timeout and were
**auto-backgrounded by the tool**, not by choice. Each was allowed to finish before any further edit
and no mutation was left applied across a transition. Recording it because the foreground rule exists
to prevent losing track of an applied mutation, and an *involuntary* backgrounding is the same hazard
arriving without the decision — the mitigation that worked was reading state before editing, not
avoiding the transition.

### Batch 1 — task review: spec compliance FAIL, task quality HIGH, three Majors, fix round 1 dispatched

Review at `task-b1-review.md`. All three Majors are **documents-only**, one to three lines each, no
code. Two results are worth carrying as positives, because a guard slice is judged on exactly them.

**The blindness claim could not be overturned, and the true reason is stronger than the one given.**
`Member.__post_init__` raises on both-set and `family_members` drops `ci95=None` members first, so
**no legitimate fixture can discriminate `_corrected_bounds`' arm order** — structural, not
fixture-dependent. The pre-flight ruling said naming a mutation blind in the plan is the claim being
checked before it is trusted; this is the check passing and improving the grounds.

**And task 21's pin closes the hole H4b-1 left.** It covers the corrected bound at its own α **and its
own df** — verified independently, each *t* cell's corrected/raw ratio matching `t(df, 0.975)/t(df,
0.95)` at its own df: 1.17815 at df 11, 1.44221 at df 2, 1.18293 at Kish 9.8, three distinct values
against the shipped `_t_critical`. On H4b-1 that α was silently unpinned and only a reviewer's own
mutation caught it; here the pin was built to cover it before anything moved.

**Major 1 is the quantifier shape again, and inside the same commit that fixed its siblings.** The
`_clustered` suffix sentence still specifies the unpaired clustered *t* as "over the arm-level ones
when not", which **is** the `min(G)−1` reading task 1 named as rejected (35.65 and 26.37 against the
correct 34.15). The rejected readings are named as rejected **only in `spec-defects.md`, the
development record** — so the normative document still carries the wrong rule while the evidence file
carries the right one. That inversion is worse than either error alone.

**Major 2 is an orphaned obligation the reviewer had to read the plan to find.** Decision 6 said the
row *and* the sentence are narrowed in task 2; the sentence was, the row was not, and **task 16's
Files list excludes `docs/reference.md`**, so nothing downstream picks it up. § Contrasts and
§ Validation now disagree.

**Major 3 is a justification contradicting its own content.** The `r` → `abs_error` swap made the
metric a **recorded column** and left both fields the old metric decided: `unpaired_percentile_over_units`
needs a declared `resample` the worked example does not have, and `cohens_d` is owed and absent —
while **task 2's own block four commits earlier invents `cohens_d: 0.31`**. The block whose repair was
justified as "where a config can produce it" **still shows a record no config can produce**.

**Also asked, and recorded because it is unresolved rather than closed:** the reviewer could not
establish whether any harness-backgrounded run had a mutation live across the transition. The
implementer was told to answer from its own record and, if it cannot tell, to **say so and re-run** —
an unverifiable measurement is not a clean one.

**Fix round 1 — all seven findings closed** (`0066830`, `6c7bdf5`), confirmed by a scoped re-review.
Major 1's fix is the right shape: the two clauses are now **grammatically parallel, each carrying its
own df**, so the correct rule — Welch-Satterthwaite over two cluster-robust per-side variances, each
side contributing `G_s − 1` — is stated **normatively in that sentence**, not merely removed from it.
The reviewer swept the four documents individually, read for paraphrases rather than grepping for a
spelling, and found no survivor. Suite 2208 passed, 1 skipped, 2 xfailed. Batch 1 complete.

**Ruling on the backgrounded-run question, which the prior reviewer could not settle.** The
implementer's reconstruction is **corroboration, not proof**: mutation 3's failure list lacking
mutation 2's signature tests falsifies one specific overlap, and nothing retrospective can prove no
window ever left a mutation applied unobserved. **The re-reviewer replaced the inference with a
measurement** — a full foreground suite against the **committed HEAD**, the artifact that actually
ships, clean before and after, at exactly the pre-mutation baseline. Any leaked mutation would appear
as extra failures there. **Ruling: the process claim stays labelled corroborated rather than proven,
and the shipped state is verified directly.** That is the right disposition — it answers the question
that matters without asserting the one that cannot be answered. **Cost if wrong:** none for this
branch; the general lesson is that when a process claim is unverifiable, verify the artifact instead.

**A finding neither task owns, filed rather than passed over.** Checking Major 3's re-derived
`cohens_d` against the block's own numbers, the re-reviewer found the value is **not** formula-exact —
and that the same naive back-calculation disagrees by a similar margin with the **pre-existing,
untouched** blocks' stated values. So § Contrasts' illustrative record blocks carry **invented
precision** as a house convention. That is a different thing from the `cohort-pilot` worked example,
whose intervals `CLAUDE.md` records as checked numerically and forbids narrowing. It is worth a filing:
a reader cannot tell which numbers in these documents are derived and which are illustrative, and this
slice has now had two tasks re-derive a field from a block that was never derived in the first place.

## Batch 2 — tasks 4-8 — the six unpaired constructions — complete, review dispatched

Commits `900e22b` (`welch_t_over_units`, `_sample_variance` extracted), `1bb70b7` (`cohens_ds`),
`620f698` (`unpaired_percentile_of_sides`, `_draw_pools` extracted), `ecd535a`
(`welch_t_over_units_clustered`, `_cr1_variance` extracted), `14587e0` (the `_clustered` percentile
spelling), report `72e3e67`. Suite 2208 → **2227** passed, 1 skipped, 2 xfailed — deltas
+4/+3/+5/+4/+3, each matching its brief. Four gates clean. `E-DATA-ALLOCATION-CONTRAST` alive; every
new construction tested **by direct call**.

**§ Statistical reporting's unpaired constructions now exist.** They had been specified in the present
tense since the section was written.

**Five implementer findings, all handed to the reviewer.** Two are brief defects that could not have
worked: task 6's `pytest.raises(..., match="E-STATS-RESAMPLE-STRATIFY-VARIES")` **cannot pass** —
`ContractError`'s message never contains its code, only `.code` does — and `getattr(table, "m")` fails
`ruff check`. Both fixed to the idioms the file already uses.

**Two mutation findings the reviewer must adjudicate, and they are different in kind.** Task 6's
mutation 2 is claimed **genuinely blind on fixture A**, verified by direct call: with no strata or
clusters `_draw_pools` gives one group per side sized exactly to that side, so concatenate-then-split
reconstructs the draw bit-for-bit. The reviewer was told that **if a fixture with strata or clusters
would discriminate, the mutation is not blind — it is mis-fixtured**, which is a different verdict with
a different remedy. Task 7's mutation 4 is reported **ambiguous**: read literally it does not reproduce
the brief's target, and hitting `9.647234756296374` required *also* treating each unit as its own
cluster. **Ruling deferred to the reviewer**, because a mutation that reaches the target only by
changing a second thing is either the mutation the brief meant or **a mutation whose two branches
cannot differ wearing the costume of one that can** — and the second is the shape this slice's
pre-flight ruling exists to catch.

**Four extractions in five tasks** — `_sample_variance`, `_draw_pools`, `_cr1_variance`, plus
`PairedResample` reused with the word "paired" deleted from its docstring. Extractions are where
`CLAUDE.md`'s traps concentrate: a mutation applied to the extracted body rather than the call site,
and a monkeypatch left aimed at a name the code no longer calls. The reviewer was pointed at both.

### Batch 2 — task review: spec compliance PASS, quality PASS WITH RESERVATIONS, three Majors

Review at `task-b2-review.md`. **No behavioural defect — the reviewer could not provoke a wrong
number**, and it verified that the hard way: every fixture literal recomputed in a script importing
`scipy` directly and **never importing `publishable`**. Fixture A's SE √2, df 96/7,
`3.039125537798091` and all four mutants; fixture B's per-side variances at G = 3/4, SE
`8.286504224543332`, df `2.0950313633473936`, half-width **`34.14810237373095`**. **No test passes
under either rejected clustered reading.** All three Majors are in prose and in the mutation record.

**Both mutation questions answered, and they went opposite ways — which is why they were sent
together.** Task 7's mutation 4: the **implementer's reading is right**, the literal reading also
fails (`17.34…` against `34.15`), so both branches discriminate and it is **not** the cannot-differ
trap — a **brief defect**. Task 6's mutation 2: **the blindness claim is overturned**, and the reason
is the one worth carrying — **it was true when it was measured and false at HEAD**, because task 8
added the clustered tests that see it. **Mis-fixtured, not blind.** A blindness claim, like a build
fact, has an expiry: it is measured against a suite, and the suite moves.

The reviewer also answered the discriminating-fixture question directly: **a clustered fixture
discriminates** (variable-length per-side draws defeat a split at `len(of_keys)`); **strata alone do
not** (per-side totals stay 5 and 25, so the split reconstructs both draws bit-for-bit).

**Major 1 is a brief that prescribed a false claim, shipped verbatim.** `_sample_variance` is
documented as "the one copy in this module" while `cohens_dz` computes the identical expression —
verified **bit-identical** by running — and their denominators are documented as "different
quantities" when only the input vector differs. **A brief prescribing a false claim does not make it
true.**

**Major 3 is the oracle's docstring over-claiming.** Task 6's mutation 4 names two tests that do not
fail; the extraction oracle's only draw-reading assertion is **clustered**, so it cannot see the
unclustered half of the body it was extracted from. Task 4's equivalent mutation was run as a control
and **is** sound, so this is an instance rather than a pattern.

**Filed rather than fixed inside a fix round:** the two tests that catch mutation 2 fail via an
**uncaught `KeyError` at `stats.py:1865`**, because `unit_table_from_rows` sits **outside** the `try`.
A test that fails by crashing pins something different from one that fails by assertion. The
implementer was told to say whether the placement is deliberate and to **file it rather than fix it
silently** — a robustness change smuggled into a prose fix round is how scope escapes review.

**And a brief mislabelling, corrected here so it does not propagate:** `26.371…` is **`G_against−1`**,
not `G_total−2`; `G_total−2` is `21.301…`.

**Fix round 1 — all eight findings closed** (`cf301e8`), confirmed by a scoped re-review that treated
the two **behavioural** items as suspects rather than as claims, and settled both **by running**.

**The removed guard was genuinely unreachable, not merely unfalsifiable** — and the distinction was
the point of asking. `_cr1_variance` performs the identical `len(values) < 2` check **first**, and
every path to the post-guard code is gated behind `got is not None`. Probed with `[]`, `[5.0]` and a
valid two-element case. **Ruling upheld:** a code change inside a prose fix round is allowed only when
it is verified behaviour-preserving, and this one was.

**And the safety argument in the new comment was made to happen, both halves.** The paired form does
place `unit_table_from_rows` outside its `try` the same way — read. And moving it **inside** produces
exactly the failure the comment warns of: **no `KeyError` at all**, a valid non-`None` interval with
the correct `method`, failing only on a row-count-variance assertion with `seen_of` collapsed to
`{9}` — **plausible and silently wrong** rather than a crash. That is `CLAUDE.md`'s "if a comment says
this cannot happen, make it happen" answered in the affirmative for once, and it is why the placement
was documented rather than filed.

The withdrawal was a **pure append** — `--numstat` shows 154 insertions, **0 deletions**, with the
original wrong claim left standing under a `WITHDRAWN` note. Checked with `--numstat` specifically
because on the previous slice an "append" deleted a line and orphaned a sentence head.

Suite 2227 passed, 1 skipped, 2 xfailed. Batch 2 complete.

## Batch 3 dispatched — tasks 9, 10, 11, 12, 13(+17a)

The refusal for the composition H4c will not build, the unpaired key path and its per-side record
keys, `Member`'s **third evidence kind**, `_corrected_bounds`' unpaired arms, and the derived `paired`
that removes the last hard-coded claim in the contrast record.

## Batch 3 — tasks 9-13(+17a) — the wiring — complete, review dispatched

Commits `9218516` (task 9), `730551c` (the unpaired key path and per-side keys), `3900661`
(`Member`'s third evidence kind), `f39b40b` (`_corrected_bounds`' two Welch arms), `4c91108`
(`paired` derived at all three sites, the source-text pin replaced by a behavioural one), report
`908d273`. Suite 2235 → **2252** passed, 1 skipped, 2 xfailed. Four gates clean.
`E-DATA-ALLOCATION-CONTRAST` alive; everything by **direct call**.

**The last hard-coded claim in the contrast record is gone** — `paired` is derived.

**An intervention, recorded because it is the failure mode the rules exist for.** The first batch-3
implementer stalled three times constructing waits on its own test runs, and **left a mutation
applied**: `crossed_group_axes`' body reduced to bare `differing_axes(of, against)` — **exactly the
defect its own docstring warns against**, since reading `values` alone calls every differing path a
group axis. I established the state myself (suite green at 2235, nothing committed), **reverted by
editing the file back** to the intersection form `cli.py`'s own comment specifies, verified by
re-running, and committed task 9. A fresh implementer took 10-13.

**Ruling: the successor's first job was to determine whether that mutation discriminates**, because a
pin that a live mutation passes is worthless and I could not tell from a green suite whether the
mutation had ever been measured. It came back at **90 failures** — strongly discriminating. **Cost if
wrong:** none realized; the check cost one suite run and removed the only doubt about a commit made
under recovery rather than under review.

**Five brief/code disagreements**, two forcing real deviations (an `UnboundLocalError` in a
`min_reported_n` placeholder; a `ruff` F821 false-reachability flag in a ternary), one a stale
hardcoded test count, and **two where a mutation's predicted magnitude or its named discriminating
test did not match what was measured** — the implementer says the qualitative "this mutation is
caught" claim held both times. The reviewer was asked the sharper question: **whether a wrong
predicted magnitude means the mutation is hitting something other than what the brief thought.**

### Batch 3 — task review: spec compliance PASS, quality PASS WITH FINDINGS, two Majors

Review at `task-b3-review.md`. **The code is correct** — the reviewer's own summary — and it
established that by running rather than reading: every illegal `Member` combination built in-process
and confirmed to raise, so `sides` is a genuine third **kind**; all six `_corrected_bounds` return
paths reachable and **bit-equal to a direct call of the construction each names**; the unpaired
corrected bound **moves** with α (3.03913 → 3.55785); and **batch 1's six-cell guard pin still
discriminates at its own α and df** under a paired-clustered-to-unclustered mutation.

**Both Majors are stated guarantees that are false, and both were prescribed by the briefs.**

**Major 1 is the test-name-claims-the-guarantee row, caught by running.** `test_the_five_t_arms_…`
claims each arm is asserted "by the construction its `method` names" and that it catches an unpaired
clustered member taking the plain Welch arm. Task 12's mutation 1 leaves it **green** — 1 failure out
of 2251, and not this test. The body asserts non-`None` plus distinctness, which catches
**collisions**, not collision-free fall-through. Its `sides` fixtures are also **3-vs-3**, the equal
per-side geometry **the spec's own constraint 1 forbids**, and the shape under which a Welch interval
coincides with a pooled one.

**Major 2 is a mutation caught by a crash rather than by an assertion.** The clustered `sides` arm's
**centre** is unpinned: mutation 4 fails through a `zip()` `ValueError` arising from fixture B's
9-vs-12 asymmetry. **Change the fixture geometry and the mutation goes silent.** One line fixes it.
**Ruling: the qualitative "this mutation is caught" claim is not sufficient here**, against the
implementer's disagreement 5 — what caught it was fixture arithmetic, not the property under test.
The brief's own reasoning ("tuples DO move, so it discriminates") is wrong. On the implementer's
disagreement 4 the opposite ruling holds: the brief's magnitude is an arithmetic slip, the mutation
fails on the intended assertion, and qualitative **is** enough. **The two look identical in a report
and differ entirely in what they license.**

**And task 9's mutation is now 126 failures, not 90** — the earlier figure was measured **before
tasks 10-13 gave the predicate its second caller**. This is the blindness-expiry rule running in the
opposite direction: a mutation's blast radius is measured against a suite, and the suite moves under
it. Both directions have now been observed on this slice.

**A caller enumeration was re-introduced in `crossed_group_axes`' docstring, one function away from
the one task 13 deleted in the same batch.** Recorded because deleting a forbidden pattern and adding
another instance of it in the same file is the pattern worth naming, not the instance.

**Fix round 1 — all seven findings closed** (`2b2674c`, `87ce22a`), confirmed by a scoped re-review
that verified both Majors **by running**: mutation 1 now fails **2** tests including
`test_the_five_t_arms_…` on `sides_clustered` (`-10.007…` against `-23.859…`), and the fixtures are
now genuinely unequal per side (4-vs-3 and 3-vs-4) rather than the forbidden equal-size geometry. The
centre assertion is load-bearing: under a sign-flip the **centre** assertions fail while the
half-width ones pass.

**A second leftover mutation was found applied in the working tree at review start** — the `sides`
branch of `_corrected_bounds` collapsed to always call `welch_t_over_units`, left over from the
stalled run. The reviewer **reverted it by editing the file back**, confirmed a zero diff against
`HEAD`, and only then began. **That is twice on this batch that a stalled agent left a live
mutation**, and both times it was caught by *reading the tree state first* rather than by trusting a
green suite — the green suite is exactly what a leftover mutation can still produce.

**And the fix report's own mutation tally was wrong**, caught by re-running rather than reading: the
sign-flip fails **2** tests, not 1. The second is a **batch-2 test, untouched by this batch**, which
independently asserts the same centre via a direct call. The substantive claim holds and the count
does not — which is the same shape as task 9's 90-versus-126: **a mutation's blast radius is a
measurement against a suite, and reporting it from memory of an earlier run is reporting a stale
number.** Three instances on this slice now.

Suite 2252 passed, 1 skipped, 2 xfailed. Batch 3 complete.

## Batch 4 dispatched — tasks 14, 16, 15+17b+18, 19, 20, 22

The `method` and `cohens_d` selection across the reachable cells; the thin warning at both emit
sites; **the retirement of `E-DATA-ALLOCATION-CONTRAST`** with the derived suppression guard and the
converted pin as one commit; the surviving-citation sweep; the five inherited filings; and the dated
re-measurement.

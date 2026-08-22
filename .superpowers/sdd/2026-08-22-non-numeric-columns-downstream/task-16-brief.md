## Task 16: the § Executability entry — row 4 re-derived, `1 → 0 → 1`

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: one appended section in a non-normative analysis.** H5a design Decision 11 ruled that this
re-derivation *"must be appended regardless of which slice does it"*; the entry dated 2026-08-22 against
`71f3c6e` **left row 4 at `1` and substituted a paragraph**, so this task is **correcting a published
figure** and therefore **appends and says what it replaces** — it never edits the earlier entry.

**Files:** `docs/feasibility-llm-growth-studies.md`

- [ ] **Step 1: append one entry, dated to this slice's merge and pinned to its commit**, in the shape
      § Executability on this build already uses: *"Measured on 2026-08-22 against commit `<sha>`"*, every
      refusal named by its code.

- [ ] **Step 2: repeat the four-row table with rows 1, 2 and 3 CHARACTER FOR CHARACTER.**
      8 of 8 validating clean; 0 blocked on `io.reuse_from`; **7** meeting the
      `report_by`-under-`resample` gap. **Row 3 is not this slice's and is not folded in.** **No fifth
      number is minted.** Copy the rows from the immediately preceding entry rather than retyping them,
      and **diff your copy against it**.

- [ ] **Step 3: row 4 goes `1 → 0 → 1`, with the re-derivation in the entry's own prose.** The predicate
      is *"free of every core-side dependency this analysis can name."* The named dependency is **a
      non-numeric recorded column vanishing between the write and `aggregate`**; it meets **all nine**
      configs, since all nine record through one request step whose payload carries `valid` (a bool),
      `invalid_reason` and `finish_reason` (strings); so row 4 **reads `0` today** and **`1`** once this
      slice lands. **Say plainly that the published figure was `1` and what it is replaced by.**

- [ ] **Step 4: the pre-emption question, decided, and named as decided.** E5's step records `"truth":
      unit.consensus_label` while the E-family declares `truth` as an attribute, so E5's own `io.record`
      would raise `E-STEP-KEY-COLLISION`. **That does NOT pre-empt the core-side dependency**: it is a
      defect in the analysis' own shown plugin code, fixable by renaming one key with no change to core,
      and the row's predicate names core-side dependencies only. Letting it pre-empt would answer *would
      this config as literally written run?* under a heading that asks about core, and would pin row 4 at
      `0` until the analysis is edited — the *carried phrase answering no consistent question* failure the
      two corrections in that section were written about.
      **So the entry names both, separately**: row 4 moves on the core-side dependency, and the `truth`
      collision is named as an **analysis-side obligation that changes no core-side count** — the same
      treatment the H8a entry gave E3's `summary`-step obligation. **State what was established and what
      was not:** the payload and the attribute list were quoted from the analysis; **the plugin was never
      run, because it does not exist.**

- [ ] **Step 5: repeat the two things the corrections require, in the entry's own words.** Do not quote a
      single figure for this analysis' executability, and **name the dependency**.

- [ ] **Step 6: the mechanical pass in full on this file** — it is exempt from the cross-document pass and
      **not** from this one. Links, `#anchor`s, table rows against the header's column count, whitespace,
      `×` for multiplication, hyphens in anchors. **Skip fenced blocks.**

- [ ] **Step 7.** No mutation; **named blind.** Its replacement is the B5 review's character-for-character
      check of rows 1–3 and its reading of row 4's argument.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 16: § Executability —
      row 4 re-derived 1 → 0 → 1, rows 1-3 unchanged`.

---

## Corrections against the code

**Appended by this plan's author and extended by no task.** Each was measured at `ee8085e`. The rule is
`CLAUDE.md`'s: *the plan argues from the spec, and the code outranks both; where they disagree the code
wins and the document changes first.* **Six of six implementers on one recent slice found a real
disagreement, so finding one is expected, not exceptional** — and **do not report a count of zero.** Every
claim below names what was run.

**1. "No test records a non-numeric `by` column" is false, and the design says it was grepped.** The
design's § What this pass found that the scoping did not, item 5, states: *"`tests/test_cli.py`'s
`_RECORDS_A_BY_COLUMN_STEP` records `{"pred": float(i), "by": float(i) * 2.0}` — the numeric arm — and
the only other `"by":` hits in the suite are `sweep.groups` entries. Grepped, not assumed."*
Run: `grep -rn '"by": ' tests/*.py`. **`tests/test_artifacts.py` holds two hits the claim misses** —
`io.record("p1", {"by": "north", "score": 10}, measurement="r1")` and its `r2` sibling, in
`test_a_measured_by_column_survives_the_collapse_into_units_parquet`, which records a **non-numeric `by`
column** deliberately and explains in its own docstring why the value must be a string.
**What the task must do instead:** task 9 narrows the claim to **`tests/test_cli.py`** — where it is
true, and where Fixture F's end-to-end arm therefore exists nowhere today — and names that artifacts test
as a **must-stay-green control** that never reaches `collapse_repeats`. **The general shape:** the design
grepped one file pattern and reported a claim about "the suite". *Sweep for the claim, not for the file the
claim was first noticed in.*

**2. Decision 7's unpaired narrowing must go in `of_col`/`against_col`, not in
`of_values`/`against_values`.** The design says *"the unpaired arm's `of_values`/`against_values` gain the
same narrowing in the same comprehension that builds them."* Read at `cli._comparison_step_blocks`:
`n_of` is `len(of_col)`, `n_against` is `len(against_col)`, and `of_clusters`/`against_clusters` are built
by keying off `of_col`/`against_col`. Narrowing only the value vectors would publish a count and group a
cluster set the difference did not come from. **What the task must do instead:** task 7 step 3 puts the
filter in `of_col`/`against_col`, and task 7's **third mutation** pins the difference by moving it back —
without that mutation this correction is prose, and *prose in a corrections section prevents nothing.*
The paired arm's `col_keys` is where the design put it and is correct, for the same reason: `diffs`,
`col_weights`, `col_clusters` and `n_paired` all derive from it. **And the unpaired arm has a fourth
consumer the design's reading would also break:** `permutation_over_contrast`'s `of_clusters`/
`against_clusters` are built as `[of_clusters[k] for k in of_col]`, so a value vector narrowed while
`of_col` was not would permute a cluster list of the wrong length beside it.

**3. The disagreement function needs no "plus the unit keys" parameter, because the walk is shared.**
The design specifies *"a new pure function in `stats.py` beside `repeat_spread`, taking the same four
arguments the collapse takes plus the unit keys."* The extra parameter exists to avoid re-deriving
membership — but re-deriving it is the real hazard, not the parameter. **What the task must do instead:**
task 4 step 1 extracts `_gather_repeats` once and both `collapse_repeats` and `repeats_disagreeing` read
it, so membership has **one implementation** and the signatures match exactly. A second walk would be a
second implementation of the membership rule, and the two would drift.

**4. `cli.py` does not import `_is_numeric`.** `grep -n '_is_numeric' src/publishable/*.py` → four lines,
**all in `stats.py`**. Decision 7's filter is written as if the predicate were in scope. **What the task
must do instead:** task 7 step 1 adds it to `cli.py`'s `from publishable.stats import (…)` block; the
precedent for a private cross-module import is `_arm_keys` from `runner`, already in that file.

**5. Decision 2 does not name the MIXED column, and the naive reading destroys a published metric
block.** The design gives two cases — constant and disagreeing — for a *non-numeric* column, and says
nothing about a column that is numeric in one repeat and non-numeric in another. It is reachable: each
repeat writes its own `units.parquet`, so H5a's within-file cross-row type rule does not bind across
repeats. Today such a column is **averaged over the numeric subset** (the inner loop skips the others).
**Measured, and this is what decides it:** `summarize_step` over a column with **one** `None` cell and
five floats publishes **no metric block for that column at all** (probe `p3`; the gate is
`all(_is_numeric(v) for v in raw)` over the whole column). So *mixed → `None`* would delete a **published**
column for **every** unit — a record-visible change nobody argued for — while for a genuinely non-numeric
column `None` costs nothing, there being no block. **What the task must do instead:** task 4's
`_across_repeats` returns the mean of the numeric values whenever there is at least one, so the mixed
path's published number is **exactly today's**; the disclosure is `W-STATS-REPEATS-DISAGREE`, and task 5's
**Fixture L** pins the value, the block's survival and the warning together, with an all-numeric second
arm as the can-fail control. **Flagged for the controller as a decision the design left open**, with the
rejected reading and its measured cost stated so the choice is checkable rather than inherited.

**6. `cli.py` passes `keys=set(collapsed)` to `repeat_spread`, which widens — and the obvious fixture
cannot see whether the inner gate held.** The second gate is `_repeat_spread_entries`' own
`_is_numeric(row[column])` filter. A fixture whose repeats record identical scores reports `std: 0.0`
**whether the gate held or not** — a dimension no assertion can see. Measured on a discriminating fixture
(two repeats 2.0 apart, four units carrying `score`, two carrying only a bool; probe `p5`):
`{'std': 1.0, 'n': 2, 'kind': 'seed'}` under the narrow keys and **identical** under the wide ones.
**What the task must do instead:** task 4 step 10 ships that fixture as **Fixture M**, so the claim is
pinned rather than inferred from a `0.0` that agrees with the bug.

**7. `resample_draws: 1998` is Fixture A's number at `seed=7, draws=2000`, not a constant.** The design's
§ The behaviour change table gives it as the `mean_score.resample_draws` literal. Reproduced exactly by
direct call — **and the same fixture shape run end to end at a run-derived seed gave `1999`.** Both are
correct; the count is the number of non-degenerate draws and depends on the seed. **What the task must do
instead:** task 1 arm B captures `1998` from its own `seed=7` call and arm E captures `1999` from its own
run, each labelled with the seed it came from, and **neither literal is reused across arms.**

**8. "§ Templates" names two sections in `reference.md`.** `## Templates: where parameters are defined`
(anchor `#templates-where-parameters-are-defined`) carries the four-operation contract, the `aggregate`
paragraph and the sentence Decision 10 edits; `## Templates` further down is the `my_assay` parameter
table. **What the task must do instead:** task 2 locates the paragraph by grepping for
`Columns are whatever the step` — one hit — rather than by the heading, and cites the long anchor.

**9. The scoping's two-condition Holm half REPRODUCES at `ee8085e`, and it moves two keys its paragraph
does not name.** Re-measured as the controller required, by running the console path with the H5b shape
installed on `publishable.cli` — **not copied.** All three cited literals hold: `n_paired` 4 → 6; the
`correction_level` swap (`mean_score` 0.025 → 0.05, `score` 0.05 → 0.025); and `score.ci95_corrected`
`[-0.10000000000000014, -0.09999999999999998]` → `[-0.10000000000000017, -0.09999999999999995]`.
**Additionally moved and unnamed in the design:** the derived contrast's own `ci95` **and**
`ci95_corrected`, `[-0.10000000000000009, -0.09999999999999998]` →
`[-0.10000000000000053, -0.09999999999999964]`, and both conditions' `aggregated…mean_score.ci95`.
**Unmoved, and load-bearing:** `vs_baseline…score.n_paired` stays `4`, `score.ci95` is identical, and
`n_rows.correction_level` stays `0.016666666666666666`. **What the task must do instead:** task 1 captures
this as **arm E**, a separate arm with its own key list, rather than folding it into arm B's seven.
*Merging two fixtures' moving sets into one count is the carried-summary failure this analysis' own
corrections were written about.*

**10. § The behaviour change's `n_rows` "today" value is `4.0`, and the design's own table says so — but
the reason is worth stating because it is not the one an implementer will assume.** `n_rows` is the row
count of the table `aggregate` receives, and today that table has **four** rows for a six-unit condition:
`collapse_repeats` returns `{}` only when **every** unit's every value is non-numeric, and drops **only
the units that carry no number** otherwise. Verified by direct call: the bool-only roster returns `{}`;
Fixture A's roster returns four units. **What the task must do instead:** task 4's Fixture A must have
**both** kinds of unit — some with a number, some without — because a bool-only roster cannot distinguish
*carriage* from *admission*, which is precisely what mutation (ii) tests.

**11. "Exactly two tests move" is dated to `5ee3a0c` AND to a shape this plan does not ship.** The scoping
measured it by installing a probe that carried values and admitted units — **with no across-repeats rule
and no mixed-column rule.** This plan's task 5 adds `None` cells and Fixture L's mixed rule. **This plan
did not re-run the suite under the shipped shape** and does not guess a number. **What the task must do
instead:** task 4 step 11 runs the whole suite and **reports the moved tests by name**, treating any third
as a finding; the scoping's figure stays attributed to its own shape and commit.

**12. `test_collapse_drops_a_bool_column_rather_than_averaging_it` does not pin what its name says.** It
asserts `"flag" not in collapsed.get("p0", {})`, and `p0` is **not in `collapsed` at all** today — the
collapse returns `{}` for that input, measured. So the test's name and docstring describe a **column**
drop while its subject is a **unit** drop, and `.get("p0", {})` is what hides the difference. **What the
task must do instead:** task 5's replacement asserts the key's **presence** and the value's being `None`
— two assertions — and names the old test in its docstring so a reader grepping for it lands there.
*A test whose name claims the guarantee* is one of this repo's recorded shapes, and this is an instance
nobody had filed.

**13. The measurements interaction is now OBSERVED, discharging the design's own request.** § What could
not be measured says *"A `measurements.parquet` written by a real run, so the interaction between Decision
2's repeat-level rule and a declared `data.units.measurements` collapse is reasoned … The plan should
build one."* Built: a real run declaring `{by: read_id, collapse: first}` whose step records
`{"score", "valid", "tag"}` per measurement. `measurements.parquet` holds both rows with both `tag`
values; `units.parquet` holds `tag: 'a'`; the collapsed table's `tag` is `'a'`; **no**
`W-STATS-REPEATS-DISAGREE` fires. **The two levels do not interact:** the declared collapse runs *inside*
each execution, so the repeat rule sees a constant. **And only `first`/`mode` can reach it** — a numeric
declared rule refuses a non-numeric value at `coerce_for_rule` first, which
`tests/test_artifacts.py::test_a_numeric_rule_coerces_a_recorded_string_before_applying` already pins.
**What the task must do instead:** task 5 step 6 pins all four observations rather than reasoning about
them.

**14. `repeats_disagreeing` must not join `publishable`'s importable surface.** § The importable surface
is an enumerated list and `stats.py` is implementation detail; `repeat_spread`, the sibling this function
is modelled on, is absent from `src/publishable/__init__.py`. Stated because a new **public** name in
`stats.py` invites the assumption. **What the task must do instead:** task 5 step 1 greps
`__init__.py` for `repeat_spread`, confirms the precedent, and exports nothing.

**15. Two `report.py` docstrings assert guarantees `cli.py` does not currently give, and this slice moves
both.** `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` returns **two** lines, and the second
is a docstring rather than an emit site. Read at `ee8085e`: `_is_strata_block` says *"`cli.py` does not
write this block at all when a recorded column of that name exists"* — **false for a non-numeric `by`
column today**, since the gate reads `step_summary` and such a column never reaches it, which is the
scoping's own measurement; and `_is_metric_entry` says a recorded `by` column *"keeps its value … as a
real metric entry"* — true for a numeric one and false for a non-numeric one, which keeps no metric block.
**What the task must do instead:** task 9 gains step 3b — narrow or delete both clauses, **changing no
code in `report.py`**, whose structural predicates are the sibling that already got this right. *A comment
or docstring claiming a guarantee the code does not provide* is this repo's most-recorded habit, and
**this instance is one the design did not name.**

**16. `statistics.null_test` widens by the same mechanism, and NOBODY enumerated it.** Neither the design
nor the scoping names `p_value` among the moving keys. `permutation_of_derived(collapsed, labels, compute,
seed, n=…)` takes the whole `collapsed` and rebuilds each draw's table from **whole rows**, exactly as
`percentile_of_derived` does — so admitting units widens the null distribution too. Measured on Fixture
A's two tables at `seed=7, n=500` with a label-reading `null_fn` (probe `p6`): `mean_score.p_value`
**`0.846307385229541` → `0.812375249500998`**, `null_draws` `500` in both. **The asymmetry is the same one
Decision 6 already documents for `n_paired`**, and both halves were established: a **recorded column**
gets no `p_value` from `summarize_step` at all (the write lives in the derived branch only), and a
**contrast's** p-value comes from `permutation_over_contrast` over `of_values`/`against_values` in the
unpaired recorded-column arm, which task 7 narrows — so it does not widen. **The contrast half was read
rather than run**, and is named as such. **What the task must do instead:** task 1 gains **arm F** with
those literals and task 15's `CLAUDE.md` list gains an eighth moving-key class. **No row of the four-row
table moves**: all eight `statistics` blocks in the feasibility analysis carry `null_test: null`, which the
truthy guard treats as undeclared — **say so explicitly, so a new moving key is not read as an
executability change.** *An enumeration that omits a class is the carried-summary failure in miniature*,
and this plan asserted one.

---

## Live overrulings — restated here because a ruling that overrules a brief has to reach the brief

A plan correction was once overruled when the plan landed, the overruling was recorded in the slice
ledger, and the plan was left carrying the old text — so the brief extracted from that plan still said
*delete*, and the task deleted. **The ledger reaches the controller and the reviewers; it reaches no
implementer.** These are in the plan itself, above and here.

1. **Fixtures E and H are task 4's, not tasks 10's and 11's.** The design's § What each change makes
   reachable overrules the scoping's task list: both go live at task 4 with no further code, and their
   pins would otherwise sit two batches later where the collapse batch's green suite is no evidence about
   either. Tasks 10 and 11 keep their **document and record** halves. **Task 10 and task 11's briefs must
   not re-add the pins**, and task 11 must not re-run task 4's mutation.
2. **The design's appended controller ruling post-dates its body and wins.** Its body's cost-if-wrong
   says *"no `diff` row points at the change"*; the ruling corrects that to *"the row that points at it is
   the one a reader is least likely to read"* — `uv.lock` is the carrier. **Any task quoting the
   cost-if-wrong must quote the corrected form**, and task 15 files the residual against H9.
3. **Nothing is minted to make the change more visible.** A fourth hash, a core-version record key, or a
   `diff` row of its own are each **refused by the controller**, not merely unbuilt. No task proposes one.
4. **`STARTER_STEP` is not changed** (Decision 12), and the scaffold's `aggregated: {step: {}}` is
   unchanged before and after. Task 4's Fixture B asserts that, and no task "fixes" the scaffold.
5. **`summarize_step` ships no code change** (Decision 4). A task that finds itself editing its body has
   found a disagreement and must report it rather than proceed.
6. **The mixed-column rule is § Corrections 5's, not the design's two-case reading.** Task 4's
   `_across_repeats` and task 5's Fixture L are the shipped form; a brief reading Decision 2 literally
   would return `None` for a mixed column and delete a published metric block.

---

## What could not be measured

- **The nine configs' real behaviour**, because neither `growth_screen` nor `publishable-llm` exists to
  install. Task 16's row-4 re-derivation rests on the payload and the attribute list quoted from the
  analysis, and **says so in the entry.**
- **The suite under the shipped shape** (§ Corrections 11). Routed to task 4 step 11 as a step, not
  guessed at here.
- **Whether any project in the wild reads `aggregated` for a column this slice newly admits.** Unknowable,
  which is why the disclosure is stated rather than a mitigation claimed.
- **Whether a run in which the SAME column is numeric for some units and non-numeric for others across
  the same repeat** (rather than across repeats) behaves as § Corrections 5 predicts end to end. The
  direct-call radius was measured (`p3`); the end-to-end shape is Fixture L's second responsibility and is
  task 5's to observe, not this plan's to assert.

---

## What the design leaves undecidable, for the controller

1. **The mixed column across repeats.** § Corrections 5 prescribes a rule and states the measured cost of
   the alternative. It is a **decision the design does not contain**, and it is record-visible in one
   direction: under the design's literal two-case reading a published metric block disappears. **If the
   controller prefers `None`, task 4's docstring, task 5's Fixture L and `CLAUDE.md`'s stoppage list all
   change, and a fifth newly-stopping thing joins the four.**
2. **Whether arm E belongs in the guard pin at all.** The design gives the pin four arms and puts the
   correction-family measurement only in prose. This plan makes it a fifth arm with a sole editor. The
   alternative — leaving it in prose — is what left the loose "byte-identical for a numeric-only run"
   framing alive long enough for the scoping to have to falsify it.
3. **The `where` on `W-STATS-REPEATS-DISAGREE`.** `aggregate_where` follows the sibling row in the same
   loop and is honest about neither the step nor the remedy; `data.units.measurements` names the remedy
   and may not exist in the file. Task 5 takes the sibling's answer with the sibling's reason. A
   controller who wants a step-shaped `where` is minting a second convention for one class of fault, and
   that is the trade.

---

## Plan self-review

- **Every claim about the code was measured at `ee8085e`**, by reading the file or **running** the
  behaviour, and `git diff --stat 5ee3a0c ee8085e -- src tests` is empty — so the scoping's baseline is
  reusable while its claims are re-checked. **Sixteen corrections**, seven of which reshape a task:
  correction 2 (task 7's unpaired filter moves and gains a mutation), correction 3 (task 4 extracts a
  shared walk), correction 5 (task 4's collapse rule and task 5's Fixture L), correction 6 (task 4 gains
  Fixture M) correction 9 (task 1 gains arm E), correction 15 (task 9 gains step 3b) and correction 16 (task 1 gains arm F and the moving-key enumeration gains an eighth class).
- **The required re-measurement was performed, not copied.** The scoping's Holm half reproduces and moves
  two keys its paragraph does not name. **It was not a non-reproduction, so no finding is owed there** —
  but the two extra keys are one.
- **Both design-flagged items are discharged:** the Holm half re-measured (correction 9), and the
  `measurements.parquet` interaction **observed** rather than reasoned (correction 13).
- **Every task states its surface, its mutations with two branches that can differ, what it must not
  touch, and its § Errors/§ Warnings work as one row per code covering every emit site.** Five mutations
  are named **blind in advance** — the annotation sweep, four docstring/comment edits, and the document
  tasks — and **each owes a named replacement.** One is named **REJECTED rather than blind** (task 5's
  fourth), because it is not blind and calling it so would be wrong.
- **Three pin arms have no authorized editor** (A, C, D) and three have exactly one each (B, E and F,
  all task 4). Arm A's rule and its fixture's framing are stated as **two labelled sentences**, because the
  loose version is what the scoping falsified.
- **The four collisions that stay where they are** — H3c-3's `fold_members`, the
  `report_by`-under-`resample` gap, `repeat_spread`'s `std: 0.0`, and the degenerate-stratum warning's
  stale owner — are named in the Global Constraints, and `fold_members` is **pinned** (Fixture K) rather
  than only named.
- **Batch 2 gets a real-command review; every batch gets a review, including the last.**
- **The four-row table is repeated with rows 1-3 unchanged, no fifth number appears, and row 4's
  re-derivation is appended as a correction to a published figure** rather than edited into it.
- **No count phrase, positional row locator, call-site enumeration or line-number citation appears above**
  except where a count is the thing being pinned (the gate literals, the 20 annotation sites, the moving
  keys) or the thing being corrected.

---

## Controller rulings, 2026-08-22 — appended AFTER this plan was written, and they bind every task below

**These are here because a ruling that overrules a brief has to reach the brief.** The ledger reaches the
controller and the reviewers; it reaches no implementer. A brief extracted from this plan carries these
paragraphs, so **no task may act on the superseded reading above.**

### Ruling 1 — the mixed column: mean over the values that exist, and the `n` must be the contributing count

**The question the plan leaves open** (its correction 5): a column that is numeric for some units and
`None` for others. The plan measured that *mixed → `None`* deletes the whole column's published block for
every unit, and proposed the mean of the numeric values with a warning.

**Ruling: the mean over the units that recorded a value, and `n` reports the number that contributed —
not `completed`.** Grounds, measured rather than reasoned:

- **A mixed *type* column cannot reach this question at all.** `_check_column_types(rows, ["v"])` refuses
  `float` beside `str` (*"column 'v' recorded both a float (unit 'row 0') and a str (unit 'row 1')"*) and
  `bool` beside `float`, while `int` beside `float` is accepted and promotes. So the only mixed column that
  survives H5a's write side is **numeric beside `None`**, which is exactly the case this ruling is about —
  and `None` is a legal recorded value (`coerce_scalars({"valid": None})` returns it), which this design
  established.
- **Dropping the column because one unit recorded `None` IS the defect this slice exists to end.** A
  silent drop that costs every unit its block because one cell is absent is the same fault at a different
  granularity, and choosing it here would mean shipping the defect's own shape as the fix.
- **`n` counting contributors rather than `completed` is what makes the interval true.** *Units are the
  inference base* and every interval core reports is computed from the per-unit table; an interval over
  five values published beside `n.completed: 240` is a lie about its own precision, and it is the kind of
  lie no later reader can detect from the record. The four-way `n` (`resolved`/`completed`/`ineligible`/
  `failed`) is not widened — this is a per-metric contributing count, reported where the metric is.

**Amendment to this ruling, same day, from batch 1's review — the reachable case, named.** Batch 1
shipped an all-or-nothing read sentence that this ruling rejects, and repairing it turned up the
distinction the ruling should have drawn in the first place. **There are three mixtures, not one:**

| The column holds | What reaches `aggregated` | Why |
|---|---|---|
| Non-numeric for **every** unit (a `str` column, a `bool` column) | **No metric block**, and the column still reaches `aggregate`'s table | There is no mean of strings. This is H5b's main case and the all-or-nothing wording is **correct here** |
| A number for some units, `None` for others | **A block computed over the units that carried a number**, with the contributing count reported and a warning naming it | This ruling's case. `None` is a legal recorded value, and a `None` cell means *this unit has no value for this metric* — which is the partial-coverage case the rest of the system already handles by counting the unit out |
| `str` **beside** a number | **Cannot occur.** `_check_column_types` refuses it at `finalize` — measured: *"column 'v' recorded both a float (unit 'row 0') and a str (unit 'row 1')"* | So a read rule for it describes an unreachable state, and a document that states one invites a later reader to build against it |

**The all-or-nothing sentence is therefore not wholly wrong — it is right about the first row and wrong
about the second**, which is why it read as plausible and passed its own task. The repair keeps its first
clause and replaces the second.

**Cost if wrong:** a metric whose coverage is a twentieth of the roster publishes an interval that reads
like every other metric's, distinguished only by a number a reader has to notice. **That is why the warning
is not optional and must name the count**, and why a task may not downgrade it to a silent computation.
The alternative — refusing the run outright — is rejected because a partially-recorded metric is ordinary
(a step that measures only what it can measure is exactly what `io.skip` exists beside), and a refusal
would make `None` unusable as the legal value H5a made it.

### Ruling 2 — `W-STATS-REPEATS-DISAGREE`'s `where` follows its sibling in the same loop

Use `aggregate_where`, the sibling row in the same loop, **and do not name `data.units.measurements` in
the `where`**. Grounds: *the sibling that already got it right is the first place to look*, and the
remedy-naming alternative points at a config field that **may not exist in the file being validated** —
a `where` that names an absent path is a diagnostic pointing at nothing. Name the remedy in the message
if it helps; the `where` locates the fault.

### Ruling 3 — the correction-family measurement stays IN the pin, not in prose

The plan asks whether the Holm/`fdr_bh` half of the moving-key measurement belongs in the guard pin at
all. **It does.** Grounds: this slice's predecessor produced **three miscounts in three consecutive
batches**, every one in a number carried as prose and framed as *read rather than estimated*. A
correction-family effect is the single least intuitive thing this slice moves — a column with **no
non-numeric value anywhere** gets a different `ci95_corrected` because admitting a unit flipped a rank —
and prose is exactly the medium those three miscounts travelled in. Arms E and F stand as captured.

### Ruling 4 — the `scripts/` finding is real, and it is not this slice's to fix

The plan is right that `scripts/` does not exist in this repo, so `CLAUDE.md`'s claims that briefs are
extracted by `scripts/task-brief` and that `scripts/sdd-workspace` rewrites `.superpowers/sdd/.gitignore`
are **documented rules with no code behind them** — the misreading `CLAUDE.md` itself names. Both scripts
live in the installed `superpowers` plugin, not in this repository, and the `.gitignore` clobber is a real
observed behaviour with a wrong path attached. **The controller fixes `CLAUDE.md` directly; no task here
touches it for this reason**, and no task may cite `scripts/` as a repo path.

---

## Controller rulings, second set — 2026-08-22, from batch 2's review

**Ruling 5 — Ruling 1's "warning naming the count" becomes `W-STATS-COLUMN-THIN`, checked against
`limits.min_reported_n` at `run` time.** Batch 2 shipped Ruling 1's contributing count and not its
warning, and the review is right that code and both document passages then diverge from the ruling
together. **The ruling is amended rather than enforced as written**, on grounds the ruling itself did not
have:

- **Its own justification is now satisfied by the count.** Ruling 1 argued the warning was *not optional*
  because *"an interval over five values published beside a `completed` of two hundred is a precision
  claim no later reader can catch."* Measured at HEAD, `run.yaml` publishes `n.completed: 3` for a column
  three of six units carry — **so the record no longer makes that claim**, and the warning's job shrinks
  from *preventing a lie* to *telling the person who never opens `run.yaml`*.
- **An unconditional warning is the wrong shape for an ordinary event.** A step that measures only what it
  can measure and records `None` otherwise is normal; warning on every such column would fire on runs with
  nothing wrong, which is how a warning becomes noise a reader learns to skip.
- **`limits.min_reported_n` is already this floor, and three shipped rows use it exactly this way** —
  `W-STATS-CONTRAST-THIN` at `run` against a realized denominator, `W-STATS-STRATUM-THIN` at `run` against
  what completed, and `W-STEP-ESTIMATE-N` citing it as *"the disclosure risk `limits.min_reported_n` exists
  to catch."* **The sibling that already got it right is the first place to look**, and a second threshold
  for the same hazard would be a second source of truth.

So: **one warning per (condition, step, column) whose contributing count is below `limits.min_reported_n`,
naming the column and the count.** Cost if wrong: a project declaring a floor of 1 gets no warning for a
column one unit carries — and the honest `n` is then the only signal, which is the state batch 2 already
shipped, so the downside is bounded by what exists today.

**Ruling 6 — the § Warnings row's granularity must match the loop.** *"Once per (condition, step)"* is
false of the code: the emit site iterates columns and a two-disagreeing-column step prints two. **Fix the
row, not the loop** — per column is the useful granularity, and the row is the thing that was wrong.

**Ruling 7 — delete the false premise, do not rewrite it.** `W-STATS-REPEATS-DISAGREE`'s message says a
mixed numeric/string column *"is not a number"* and that *"those units carry no value for it"* while the
record publishes a value for them; `reference.md`'s § Warnings row states the same premise normatively;
and `repeats_disagreeing`'s own docstring contradicts both. **Delete the clauses that make the false
claim.** *A rewrite invents; a deletion cannot* — and the same applies to `_across_repeats`'s ground
*"because `summarize_step` requires all carried values numeric"*, which task 6's own gate change
falsified and which its own docstring contradicts three paragraphs later.

**Ruling 8 — the two unpinned changes get pins, and the ninth moving-key class gets an arm.** The empty-
record admission (`n_rows` 4.0 → 6.0) and `_repeats_disagree`'s `(is-numeric, value)` tuple are both live
behaviour with **no test that fails when they are removed** — that is the *five slices weakening a pin
quietly* shape arriving as *never pinned at all*. And the `report_by` stratum path is a **ninth** moving-key
class the enumeration omits, carrying a **third** distinct `resample_draws` literal; it needs an arm, even
though `level_collapsed` is a projection with no separate code path. **A key that moves and appears in no
arm is precisely what the guard pin exists to catch.**

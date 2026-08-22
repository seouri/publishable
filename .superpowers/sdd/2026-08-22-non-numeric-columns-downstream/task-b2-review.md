# H5b batch 2 review — tasks 4, 5, 6

Reviewed at `ab6b65b` on branch `h5b-non-numeric-downstream`, 2026-08-22. **This was a real-command
review**: every behavioural claim below was established through the **installed console script**
(`uv run --project <repo> publishable run …`) against projects scaffolded by `publishable new` +
`generate experiment`, with `run.yaml` read key by key — not through `main([...])` in-process, and not
by reading. Where a claim is established by reading, it says so.

**Verdicts: task 4 PASS · task 5 FAIL · task 6 FAIL.**

Gates, all re-run: `uv run pytest` → **2911 passed, 1 skipped, 3 xfailed** (matches the report's claim
and the +16/+1 delta off the 2895/1/2 baseline). `ruff check .` clean, `ruff format --check .` 93 files
unchanged, `mypy` 52 source files clean. Every mutation below was reverted **by editing back** and the
revert verified by **re-running**; `git status --porcelain` is empty and the final full-suite run above
was taken after the last revert.

---

## Item 1 — Ruling 1's three mixtures, each through a real `run`. All three behave as ruled.

**Does `run.yaml` publish the contributing count? YES.** No Critical on item 1.

| Mixture | Probe | `run.yaml` |
|---|---|---|
| Non-numeric for **every** unit | 6 units, step records `{"flag": True, "score": float(i)}`; project-local template's `aggregate` returns `n_flag`/`n_rows`/`n_cols` | `flag` earns **no metric block**; `n_flag: 6.0`, `n_rows: 6.0`, **`n_cols: 2.0`** — the column reaches `aggregate`'s table |
| A number for some units, `None` for others | 6 units, 3 record `{"score": float(i)}`, 3 record `{"score": None}` | `score.value: 1.0`, **`n: {resolved: 6, completed: 3, …}`** — the **contributing** count, beside a condition-wide `resolved: 6` |
| `str` beside a number | 6 units, 3 record `4.0`-family floats, 3 record `"n/a"` | **Cannot occur.** Exit 4, `status: failed`, every execution `E-STEP-RETURN-TYPE ContractError: units.parquet: column 'score' recorded both a float (unit 'p1') and a str (unit 'p4')` — the ruling's own quoted message |

`n_block = {**counts, "completed": len(values)}` (`stats.py`, the column loop) is the one place, and
`len(values)` is post-filter, so the count follows the numeric subset for free.

---

## Item 2 — task 6's out-of-brief code change. Adjudicated: regression real, fix correct, disclosure adequate.

Task 6's brief says *"`summarize_step` ships NO code change."* It shipped one. **The regression is
real, and I built it three ways on one project** (6 units, 3 recording `score`, 3 recording `None`),
through the console script:

| Code | `aggregated.step01_summarize_units` |
|---|---|
| `668cb05` (pre-batch) | `score`, `n.completed: 3` |
| task 4 + 5 only (task 6's gate change reverted in place) | **`{}`** — the whole column silently gone |
| `252774b` (HEAD) | `score`, `n.completed: 3` |

So task 4 introduced a published-column deletion and task 6 closed it, restoring the pre-batch answer
and generalising it. That is the correct call under CLAUDE.md (*"a fix that carries its own
justification is not thereby verified"* cuts the other way here — the fix was measured), and the
**deviation is disclosed at length in both the commit message and the report**, named as beyond the
brief, with the ruling cited. **Credit rather than a finding for the widening itself.** The findings
against task 6 are M3 and M4 below, which are about what the fix did *not* carry.

---

## Item 3 — the `TypeError` task 6 makes reachable. Reproduced; damage exactly as disclosed; the pin is a real pin.

Same project shape, two conditions (`baseline: pearson` / `grid: [spearman]`), through the console
script: **raw traceback, exit 1**, at `cli.py:1168`
(`of_collapsed[k][metric_key] - against_collapsed[k][metric_key]`),
`TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'`.
Damage confirmed: **run directory complete** (`conditions/`, `config.yaml`, `environment`,
`executions.jsonl`, `manifest`, `sweep.yaml`), **all 10 executions paid for** (10 ledger lines, both
conditions × 5 seeds), **no `run.yaml`**. Not even a redacted diagnostic — the traceback escapes
`main`.

The disclosure device holds, and **fails for the right reason now**:
`pytest --runxfail` on `test_ruling_1s_blast_radius_a_contrast_over_a_ragged_none_column_crashes`
fails **at `cli.py:1168` with that same `TypeError`**, not at a validate refusal or a fixture error.
And it fails **loudly when the behaviour moves**: with task 6's gate reverted, the test reported
`FAILED … [XPASS(strict)]`. Asserting exit 0 + `run.yaml` exists rather than `pytest.raises(TypeError)`
is the right choice; a `raises` pin would have pinned the bug as intended.

---

## Item 4 — the moving keys. One class moved that is in neither list. See **M7**.

Measured by running **one identical project against `668cb05` and HEAD** (`git worktree add /tmp/pubold
668cb05`) and diffing the two `run.yaml` files leaf by leaf: 12 units (8 with `score`+`flag`, 4 with
`flag` only), two conditions, project-local template returning `n_flag`/`n_rows`/`mean_score`,
`correction: holm`, `report_by: [cohort]`, `null_test: {permutation, n: 200, shuffle: arm}`.

Covered by arm B / arm E: derived `value`, `ci95`, `n.completed`, `resample_draws`; recorded
`mean_score.ci95`/`n.completed`; `vs_baseline.*.n_paired` (8 → 12 on three metrics).
`score` (the recorded column) did **not** move, correctly — its numeric subset is unchanged.
`correction_level`/`ci95_corrected` did not move in this run (every delta is 0.0 here); arm E is where
that is measured, and arm E passes.

**Not covered: the `report_by` stratum path.** See M7.

**The eighth class (`statistics.null_test`'s `p_value`) — verified by READING, not behaviour.** My
end-to-end probe was **non-discriminating**: my template's `aggregate` ignores the relabelling, so
`permutation_of_derived`'s "not varied" rule wrote `p_value: null` in both runs. Arm F
(`test_a_derived_metrics_permutation_p_value_widens_but_a_recorded_columns_never_gets_one`) plus plan
correction 16's direct-call measurement are the evidence, and both are batch 1's, unedited here.

---

## Item 5 — existing tests whose expectation moved. Exactly three, and the report names all three.

Measured rather than argued: `git archive 668cb05 tests | tar -x`, ran the **pre-batch test tree
against HEAD's `src/`** → **3 failed, 2892 passed, 1 skipped, 2 xfailed**. The three:
`test_a_bool_only_column_widens_exactly_seven_moving_keys` (arm B), 
`test_the_correction_family_measurement_arm_e_no_editor_except_task_4` (arm E), 
`test_collapse_drops_a_bool_column_rather_than_averaging_it`. **No fourth** — plan correction 11's
"a third would be a finding" is discharged. Fixture K (`test_two_units_per_fold_under_fold_times_seed_keeps_every_unit`)
**passed** in that run, confirming the report's claim that it was extended additively, not rewritten.

Each argument checked against the old assertion:
- **Arms B and E** are flip-arms with task 4 named in their own docstrings as sole authorized editor.
  Correct move. Arm B's `today`/`after` pairs are now redundant (the two tables are identical
  post-task-4), which its docstring says outright; the discriminating assertion is `narrow == wide`
  and it survives mutation (see Item 6). Not a weakening.
- **`test_collapse_drops_a_bool_column_rather_than_averaging_it`** → replaced by
  `test_a_disagreeing_bool_column_collapses_to_none_not_dropped`. **The replacement distinguishes the
  two readings correction 12 named** (Item 8): it indexes `collapsed["p0"]` rather than `.get("p0", {})`,
  so a unit drop is a `KeyError` and a column drop fails `assert "flag" in collapsed["p0"]` — two
  assertions, and the value assertion `is None` is separate. The old test's name is in the new
  docstring, so a grep lands there. Correct move.
- **`summarize_step`'s docstring** — task 6 edited the paragraph its brief said to leave alone. Correct
  and correctly disclosed: the gate change made that paragraph false, and CLAUDE.md forbids shipping a
  known-false docstring. (The same discipline was **not** applied to the caller — M4.)

---

## Item 6 — mutations. Every claimed mutation re-run against the named test's body. Failure counts read, not accepted.

| Claim | Re-run result |
|---|---|
| T4 (i) restore `or not _is_numeric(value)` in `_gather_repeats` | **4 failures**, not the 1 the report names: `test_a_disagreeing_bool_column_collapses_to_none_not_dropped`, `test_a_bool_only_column_widens_exactly_seven_moving_keys`, both Fixture E arms. Minor m3 |
| T5 (i) carry `values[0]` instead of `None` | 2 failures — Fixture C's `is None` **and** Fixture E arm 2. As claimed plus one |
| T5 (ii) answer from the collapsed cell (`value is None`) | Fixture D **arm 1** FAILS (gains a warning) + Fixture L. Exactly the proxy the design rejects |
| T5 (iii) delete the warn call site | Fixture C's real-run assertion FAILS on stdout, message absent. As claimed |
| T5 (iv) drop the all-numeric early return — reported as run, not blind | **1 failed, 2910 passed** — `test_fixture_l_arm_2_both_repeats_numeric_draws_no_warning`, `{'score': 1} != {}`. Exactly as reported |
| T4 (iii) `cli.py`'s second empty-level gate → `if True:` | Fixture H FAILS, `'b'` back in `by`. As claimed |
| T6 (1) project non-numeric out at `summarize_step`'s **input** | Fixture I FAILS, `ci95 == [0.0, 0.0]` against `value == 6.0` — a point estimate outside its own interval. As claimed |
| T6 (2) restore the all-or-nothing gate | `test_ruling_1_…keeps_a_block` FAILS `KeyError: 'score'`, **and** the blast-radius pin flips to `XPASS(strict)`. As claimed, plus the pin proving itself |

**Two mutations I built myself, both leaving the suite green — M5 and M6.**

---

## Item 7 — `W-STATS-REPEATS-DISAGREE`. One emit site, one row; Ruling 2 satisfied; the row is wrong twice.

Re-derived by grep over the whole tree (filtering the **file list**, never the output):
`grep -rln "W-STATS-REPEATS-DISAGREE"` → `src/publishable/cli.py` (**one** site, line 2882),
`docs/reference.md` (**one** row, line 393), plus tests and the development record. One row per code. ✓

**Ruling 2 satisfied**, verified by behaviour: the emitted `where` is **`generic.aggregate`** —
`aggregate_where`, the sibling row in the same loop — and `data.units.measurements` appears only in the
message, which the ruling explicitly permits. ✓

The row itself carries **two reachable falsehoods** — M1 and M2.

---

## Item 9 — fixture literals recomputed, not read.

- **Fixture M** (`repeat_spread` under widened `keys`): two seeds recording `score` 1.0 and 3.0 over
  four units → per-seed means 1.0 and 3.0 → asserted `{"std": 1.0, "n": 2}`. Recomputed: population
  std of [1.0, 3.0] is `sqrt(((1-2)²+(3-2)²)/2) = 1.0`; the **sample** std would be `1.414`. So the
  literal is the code's own convention and **`std: 0.0` cannot hide the bug** — the repeats genuinely
  differ, which is the trap correction 6 named. ✓
- **`resample_draws` seed-dependence**: arm B asserts `1998` at its own `seed=7`, labelled with that
  seed in the docstring, and reuses it nowhere. My real run produced a **third** value (`1997`) at a
  run-derived seed, confirming it is not a constant. ✓ (See M7 and m2.)
- **Fixture A has both kinds of unit** (`u0`–`u3` with `score`+`valid`, `u4`–`u5` with `valid` only),
  so `n_rows` can tell carriage from admission — and T4 mutation (ii) is what tests it. ✓

---

## Item 11 — every claim the report makes about other tests, rows or code, grepped.

All of these hold: `repeat_spread` absent from `src/publishable/__init__.py` (0 hits, and
`repeats_disagreeing` is 0 too — nothing exported, correction 14 satisfied);
`assert "W-STATS-STRATUM-SHADOWED" in doc["stdout"]` twice in `tests/test_cli.py` (6920, 6949);
`test_a_numeric_rule_coerces_a_recorded_string_before_applying` at `tests/test_artifacts.py:783`;
`grep -rn 'dict\[str, dict\[str, float\]\]' src/publishable/` → **0**;
the contrast loop is `sorted((set(of_summary) & set(against_summary)) - {"by"})` at `cli.py:1038`;
`reference.md:997` and `:2570` do state row 2's rule. **One thing the report's grep did not notice
about those two passages: neither states a warning** — which is M3's second half.
`docs/superpowers/spec-defects.md` grepped: no existing entry covers M3 or M6; the H5b-owned entry at
line 8437 is the one this slice closes and is task 15's to strike.

---

# Findings

## Critical — none.

## M1 (Major, task 5) — the shipped warning message asserts two things that are false of the very case Fixture L ships, and so does the normative § Warnings row

Established by behaviour, console script, 4 units, module-level counter recording `{"score": 4.0}` on
odd repeats and `{"score": "n/a"}` on even ones (legal: `_check_column_types` is per-file, so each
repeat's parquet is homogeneous — unlike Item 1's third mixture, which is within one file):

```
  warning W-STATS-REPEATS-DISAGREE generic.aggregate
          condition 0 step 'step01_summarize_units': recorded column 'score' is not a number and
          disagrees across the repeats of 4 unit(s), so those units carry no value for it; …
```
`run.yaml` for the same run: **`score.value = 4.0`, `n.completed = 4`.**

So the message says *"is not a number"* of a column that is a number in three of five repeats, and
*"those units carry no value for it"* of four units that carry `4.0` and publish it. `reference.md:393`
states the same false premise normatively — *"so that unit's cell in the collapsed table is `None`
rather than a value"* — while the cell is `4.0`. **`repeats_disagreeing`'s own docstring, in the same
commit, says the opposite**: *"its collapsed cell is still the mean of the numbers — the disclosure is
the warning, not the loss of the column."* Both cannot hold.

`test_fixture_l_a_mixed_numeric_string_column_keeps_its_mean_and_warns` is the fixture that *proves*
the message false and it asserts only the code and the column name, never the sentence — so the false
clause is **unpinned as well as false**.

## M2 (Major, task 5) — the same § Warnings row's frequency claim is false

`reference.md:393` ends *"Reported at `run` time, once per (condition, step)."* The emit site loops
over `repeats_disagreeing(...).items()`, i.e. **once per (condition, step, column)**. Behaviour, 4
units, one step whose repeats disagree on **two** columns (`flag` and `tag`):
`publishable run … | grep -c "W-STATS-REPEATS-DISAGREE"` → **2**, both for condition 0 / one step.
A § Warnings row narrower than its code is this repo's most-recorded documentation fault. Same root as
M1, same owner — the row was minted in batch 1's task 3, but task 5 is the task that built the emit
site and owed the row a re-read.

## M3 (Major, task 6) — Ruling 1's row 2 shipped its count and not its warning, and the divergence is not framed as the ruling gap it is

Ruling 1's amendment, row 2: *"A block computed over the units that carried a number, **with the
contributing count reported and a warning naming it**."* Its cost-if-wrong: *"**That is why the warning
is not optional and must name the count**, and why a task may not downgrade it to a silent
computation."*

Behaviour, console script, the directly-recorded-`None` project (Item 1, mixture 2): `run.yaml`
publishes `score` at `n.completed: 3` against `resolved: 6`, and **stdout carries no diagnostic at all
beyond `W-ENV-UNLOCKED`.** A silent computation, which the ruling forbids by name. On the other path
(a repeat disagreement) `W-STATS-REPEATS-DISAGREE` does fire, but it names the *disagreeing* count, not
the contributing one — the complement, and defensible; the directly-recorded path is the undefended
half.

**This is not a code-versus-document inconsistency a task can close by editing one side.**
`reference.md:997` and `:2570` both state row 2 with the count and **no warning**, so code and document
agree and both diverge from the binding ruling. It needs the controller: either the ruling's warning
half is built (a per-metric coverage warning, which no shipped code has) or the ruling is amended and
the amendment recorded. The report's *"A filing candidate, not a code mint"* section does disclose the
silence and argues from the pre-existing ragged-column precedent, but **never quotes the ruling
sentence it contradicts** — so the disclosure reads as a judgement call about a new hazard rather than
as a deviation from a binding instruction.

## M4 (Major, task 6) — `_across_repeats`'s stated ground is falsified by task 6's own gate change, and contradicted three paragraphs later in the same docstring

`_across_repeats`, second bullet, unchanged by task 6:

> *SOME values numbers: the mean of those … Moving this to `None` would cost the whole column its
> metric block, for every unit, **because `summarize_step` requires *all* carried values numeric
> (measured)**.*

Task 6 removed exactly that requirement. And the same docstring's fourth paragraph — also unchanged —
already says the opposite: *"A column where SOME units carry a number and others carry `None` is a
different case `summarize_step`'s own gate decides (Controller ruling 1): the column keeps a block
computed over the units that carried a number."* Two properties, both asserted, one false.

Task 6 rewrote `summarize_step`'s own docstring for exactly this reason and did not sweep its caller,
700 lines up in the same file. *When you change a guard, re-read its justification* — and *sweep for
the claim, not for the file the claim was first noticed in.* **Prefer deleting the clause to rewriting
it**: the fourth paragraph already carries the true statement.

## M5 (Major, task 4) — `_repeats_disagree`'s tuple comparison is unpinned, and its stated consequence is false

Mutation I built (not in the report): replace
`any((_is_numeric(v), v) != (_is_numeric(first), first) for v in values)` with `any(v != first …)`.
**Full suite: 2911 passed, 1 skipped, 3 xfailed — bit-identical to the unmutated run.** No fixture
records a column as `True` in one repeat and `1.0` in another, and the property is reachable (each
repeat writes its own `units.parquet`, so H5a's within-file type rule does not bind across repeats).

The docstring's stated consequence is also false. It claims such a column *"would read as constant and
**collapse to whichever arrived first — order-dependent**, which is what this rule refuses."* Measured:
`_across_repeats([True, 1.0])` → `1.0` and `_across_repeats([1.0, True])` → `1.0`, because the numeric
branch precedes the disagreement branch in the very function that calls this one. The real consequence
of losing the tuple is **a missing warning**, not an order-dependent published value. *A safety
argument in a comment is a claim, and needs a mutation like any other.* The text came verbatim from
task 4's brief — *brief-supplied prose is where zero hides* — and the batch reported grep discipline on
five other claims and not on this one.

## M6 (Major, task 4) — the empty-record admission is a published behaviour change, unpinned and unenumerated

The comment task 4 added at the admission gate asserts: *"It gets a row even when … it recorded no
column at all — `io.record(key, {})` settles a unit and records nothing, **which is reachable
(measured)**."*

**Reachable: confirmed by behaviour**, console script, one project, 6 units, 4 recording
`{"score": float(i)}` and 2 recording `{}`, project-local template returning `n_rows`:

| Code | `n_rows.value` | `n_rows.n.completed` |
|---|---|---|
| `668cb05` | **4.0** | **4** |
| HEAD | **6.0** | **6** |

**Unpinned: confirmed by mutation.** Adding `if cols` to `collapse_repeats`'s return comprehension —
dropping every unit that carried no column — leaves **2911 passed, 1 skipped, 3 xfailed**, the full
suite unchanged. *A seam named in the brief and instantiated by no fixture*, and the trigger appears in
neither the report's moving-key table nor any pin arm.

## M7 (Major, task 4) — the moving-key enumeration omits the `report_by` stratum path, including a third distinct `resample_draws` literal

From the `668cb05`-vs-HEAD `run.yaml` diff on one project declaring `report_by: [cohort]`, per level and
per condition:

```
by.cohort.a.n_flag.value          0.0  -> 6.0
by.cohort.a.n_flag.ci95      [0.0,0.0] -> [6.0,6.0]
by.cohort.a.n_flag.n.completed      4  -> 6
by.cohort.a.n_rows.value          4.0  -> 6.0
by.cohort.a.mean_score.ci95[0]    2.0  -> 1.5
by.cohort.a.mean_score.n.completed  4  -> 6
by.cohort.a.mean_score.resample_draws 2000 -> 1997
```
`by.cohort.b.*` moves the same way, in both conditions. **`resample_draws: 1997` is a third measured
draw literal**, beside arm B's `1998` (`seed=7`) and plan correction 7's `1999`.

**No arm pins a moved value inside `by`.** Fixture H is the only fixture that exercises `by` and it
pins only *unmoved* literals (`by_grp["a"]["score"]["value"] == 10.0`, `n_rows["value"] == 2.0` — both
identical before and after, since level `a`'s two units were always admitted). Arm E declares no
`report_by`.

**Bounded honestly:** `level_collapsed = {k: v for k, v in collapsed.items() if k in keys}`
(`cli.py:3297`) is a projection of `collapsed`, so **no independent code path is unguarded** — the
values move mechanically. The Major rests on the enumeration, not the guard: the report's table calls
itself *"Every key whose published value moved"*, task 15's `CLAUDE.md` moving-key list is written from
it, and *an enumeration that omits a class is the carried-summary failure in miniature* — the fault
this slice's own § Corrections 16 was written about.

## m1 (Minor, task 6) — Ruling 1's row 2 has no end-to-end pin

The report says the real run was *"confirmed via direct probe during development … not committed as a
separate test — covered in spirit by the direct-call tests."* The two direct-call tests are good, but
the shipped behaviour change is a figure in `run.yaml`, and no test reads it there. Low risk
(`n_block` is one line, one place), so Minor. **I verified it end-to-end myself** — Item 1, mixture 2.

## m2 (Minor, not batch 2's) — arm E asserts no `resample_draws`

Plan correction 7 prescribed *"arm E captures `1999` from its own run, each literal labelled with the
seed it came from."* Arm E asserts no `resample_draws` at all (`grep -n "1999" tests/` → nothing).
Batch 1's task 1, already merged and reviewed; noted here because M7 turned up a **third** value for
the same key and the missing arm-E literal is why nobody had two to compare.

## m3 (Minor, task 4) — mutation (i)'s disclosure under-reports its blast radius

Reported as failing "Fixture A's `narrow == wide` assertion and Fixture B's `n_present`". Re-run:
**4 test failures**, including both Fixture E arms and the Fixture C replacement. An undisclosed side
effect rather than a weakness — the same shape batch 1's review found in mutation (iv) — but *read the
failure count* is this slice's own standing instruction.

---

# Verdicts, and the discriminator

**Shipped behaviour or shipped normative text wrong → FAIL. Behaviour right but unpinned or
mis-justified → PASS with a Major.**

- **Task 4 — PASS.** The collapse is correct, the split into `_gather_repeats`/`_across_repeats`/
  `_repeats_disagree` is the one-implementation shape correction 3 asked for, every claimed mutation
  reproduces, the annotation sweep is complete (0 hits), exactly three existing tests move and all
  three are named, and Fixtures A/B/E/H/K/M all discriminate. Three Majors (M5, M6, M7) and one Minor
  (m3), all of them unpinned-or-mis-justified rather than wrong behaviour.
- **Task 5 — FAIL.** The mechanism is right — the disclosure is answered from the **rows**, not from
  the collapsed cell, and mutation (ii) proves it — but the batch shipped a **warning message that is
  false of the case its own Fixture L ships** (M1) and left a **normative § Warnings row false twice
  over** (M1, M2), one of which its own new docstring contradicts.
- **Task 6 — FAIL.** The gate fix is correct, load-bearing, and disclosed the way an out-of-brief
  change should be — that part is a credit. But it ships **a docstring ground its own change falsified
  and its own later paragraph contradicts** (M4), and it implemented **half of Ruling 1's row 2**
  without framing the missing half as a binding-ruling gap the controller has to rule on (M3).

**For the controller.** M3 is the one that cannot be fixed inside a task: code and both `reference.md`
passages agree with each other and all three diverge from Ruling 1's *"the warning is not optional."*
Either the warning half gets built and owned, or the ruling gets amended in writing. M1/M2/M4 are
straight text corrections with the true statements already available in the same files — prefer
deleting the false clauses to rewriting them. M5/M6 want one fixture each. M7 wants the enumeration
extended before task 15 consumes it, and the `1997`/`1998`/`1999` triple recorded as evidence that
`resample_draws` is per-seed rather than a constant.

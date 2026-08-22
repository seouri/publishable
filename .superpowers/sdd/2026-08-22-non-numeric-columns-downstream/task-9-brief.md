## Task 9: the `by` arbitration answers from the recorded-column set, and `_attributed`'s two falsified grounds are deleted

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a real `run`.** Design Decision 9.

Today `cli.py` tests `if "by" in step_summary`, so a **non-numeric** `by` column draws no
`W-STATS-STRATUM-SHADOWED` and the strata are published under the same name the column holds in
`units.parquet` — measured by the scoping both ways, with the numeric case as its can-fail control. After
task 6 the non-numeric column still never reaches `step_summary`, so the gate must move.

**Files:**
- Source: `src/publishable/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: move the gate to the recorded-column set — the set this loop ALREADY computes.**
      `recorded_columns = {col for cols in collapsed.values() for col in cols}` is built a few statements
      earlier in the same loop body, for the `repeat_spread` walk. **Reuse it; do not recompute it.**
      *Before writing a walk, a guard or a containment, grep for one that already exists.* The gate
      becomes `if "by" in recorded_columns:` and the `elif by_block:` branch below it is unchanged.
      **This is the direct question** — *did any unit record a column called `by`?* — rather than a proxy
      for it. It is **not** the *reserved NAME standing in for a structural fact* fault: there the question
      was *is this entry a stratum?* and the answer was a name; here the question **is** whether a name was
      recorded.
      **Verify the widening is only a widening:** `by` in `step_summary` implies `by` in
      `recorded_columns`, because a **derived** `by` is refused in `summarize_step` and the containment
      retry passes no `derived` at all. **Read both branches and report that reading** rather than
      asserting it.

- [ ] **Step 2: both arms warn and both suppress the strata.** § Steps and artifacts already states it
      without qualification — *"no strata are reported for the step at all"* — and a run whose
      `units.parquet` holds a `by` column while its `run.yaml` holds a `by` strata block is the
      two-meanings-under-one-name case the reserved name exists to prevent. The `if`/`elif` shape already
      delivers both, so **this is a one-expression change**; say so rather than restructuring the branch.

- [ ] **Step 3: reword the `W-STATS-STRATUM-SHADOWED` row in § Warnings core reports — ONE row, ONE emit
      site, two conditions.** The row reads *"A step records a metric named `by` … so that column keeps
      its recorded value but is reported with no contrast delta"*. A non-numeric `by` column keeps **no**
      `aggregated` entry to keep, so the row must cover a column with a metric block and one without.
      **Locate the row by its code, never by position.** Then check § Steps and artifacts' reserved-`by`
      paragraph against the reworded row and against the code, and report all three readings.
      **No other row moves, and the emit site is ONE — but the grep returns TWO lines.**
      `grep -rn 'W-STATS-STRATUM-SHADOWED' src/publishable/*.py` → `cli.py`'s `warn` call **and a
      docstring in `report.py`**. Run it and report both. *§ Errors and § Warnings carry one row per code,
      not per emit site, so a diagnostic's unit of work is every site that raises or reports it* — that
      was the whole-branch Major on two sub-slices and shipped twice inside a third, and **the second hit
      here is not an emit site but IS a claim this slice changes** (§ Corrections 15).

- [ ] **Step 3b: re-read `report.py`'s two structural predicates, because this task moves what they
      claim.** `_is_strata_block`'s docstring says *"`cli.py` does not write this block at all when a
      recorded column of that name exists"* — **false today for a NON-numeric `by` column**, which is
      exactly what the scoping measured, and **true after step 1.** `_is_metric_entry`'s docstring says a
      recorded `by` column *"keeps its value … as a real metric entry"* — true for the numeric case and
      **false for the non-numeric one**, which keeps no metric block at all after task 6.
      **Correct both by narrowing the claim to the case it holds for, or by deleting the clause**
      (*prefer deleting a claim to rewriting it*), and **change no code in `report.py`**: both predicates
      are structural and both stay. **When you change code a comment describes, re-read the comment** —
      and this is the sibling that already got the structural test right, so nothing here is a defect
      except the sentences.

- [ ] **Step 4: DELETE `_attributed`'s two falsified grounds.** Its docstring argues `unit` is restored
      *"because nothing refuses an attribute named `unit`"* — H5a's `units.RESERVED_COLUMNS` now does, at
      `validate` and at roster resolution — and argues a numeric attribute's publication is *"not
      reachable while every roster attribute arrives from `csv.DictReader` as a string"*, which H5a's
      `coerce_scalars` at `resolve_units` makes weaker than it reads: a resolver may yield a float and it
      stays a float. **Both grounds go. Delete, do not rewrite.**
      **The true reasons stay:** the unit key column must survive a bootstrap draw that duplicates units,
      and an attribute is merged into **rows** and never into `collapsed`, which is why it can never be
      published as a metric. **Grep `RESERVED_COLUMNS` in `src/publishable/units.py` and quote the
      constant** before writing that the first ground is false — *before repeating any claim a brief makes
      about the code, grep for it.*

- [ ] **Step 5: Fixture F — a non-numeric `by` column, with the numeric arm as its can-fail control.**
      A step recording `{"pred": float(i), "by": f"lvl{i % 2}"}` with `report_by` declared. Assert
      `W-STATS-STRATUM-SHADOWED` fires **on stdout**, `"by" not in aggregated[step]` (a non-numeric column
      has no metric block to keep), and **no strata block**.
      **The controls, and there are two:**
      (a) the two **existing** tests over `_RECORDS_A_BY_COLUMN_STEP`, which records `float(i) * 2.0` and
      asserts `aggregated[step]["by"]["value"] == 39.0` — task 1's pin arm C, **zero lines changed**, and
      the B3 review reports the `git diff` line count over both bodies.
      (b) `tests/test_artifacts.py::test_a_measured_by_column_survives_the_collapse_into_units_parquet`,
      which records `{"by": "north", …}` — **a non-numeric `by` column at the artifact layer**, which
      never reaches `collapse_repeats` and must stay green. **The design says "no test in the suite records
      a non-numeric `by`"; that is false, and this is the test (§ Corrections 1).** The true claim is
      narrower: no test in **`tests/test_cli.py`** does, so Fixture F's end-to-end arm exists nowhere
      today. **Grep `'"by": ' tests/*.py` yourself and report the hit list** rather than repeating either
      claim.

- [ ] **Step 6: the mutations — two.**
      (i) Point the gate back at `step_summary`. **Fixture F's warning assertion AND its no-strata
      assertion must FAIL.** *Why the branches differ:* measured by the scoping both ways — the
      non-numeric column never reaches `step_summary`, so the mutant is silent.
      (ii) Widen the gate to suppress a **numeric** `by` column's metric block (drop the column from
      `step_summary` instead of only the strata). **Pin arm C must FAIL** — the two existing tests assert
      `aggregated[step]["by"]["value"] == 39.0`. *Why the branches differ:* the numeric arm keeps its
      metric block, and a widened guard removes it.
      **Named blind in advance, with its replacement:** the `_attributed` docstring deletion. A docstring
      has no behaviour; its replacement is the B3 review's *were the two grounds deleted rather than
      rewritten?* check, run against `git diff` rather than against the report.

- [ ] **Step 7: run** the four commands. **Delta:** Fixture F. **Commit:** `H5b task 9: the by
      arbitration answers from the recorded columns, and _attributed loses two false grounds`.

---


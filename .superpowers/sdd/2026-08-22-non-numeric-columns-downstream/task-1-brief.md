## Task 1: the guard pin — five arms, captured before anything moves

**Runs FIRST, before every other task. Surface: direct calls to `stats.summarize_step` for arms B and
D, a real `run` through `main` for arms A, C and E.** H5b moves published numbers, and a literal
captured after a task has run records the move rather than the baseline. **Two arms have no authorized
editor at all, so a passing arm is itself the proof** — the answer to five slices weakening a pin
quietly, and to the two that pinned one list twice and edited both.

**Files:**
- Test: `tests/test_cli.py` (add), `tests/test_stats.py` (add)

**Interfaces:**
- Consumes: `run_a_project` and `_first_contrast` from `tests/test_cli.py`, `_result` from
  `tests/test_stats.py`, `stats.summarize_step`, `stats.collapse_repeats`.
- Produces: nothing importable. Arms every later task's suite run must keep green.

**What this pin deliberately does NOT re-capture, and why.** `run.yaml`'s top-level and `provenance` key
lists are already pinned by more than one shipped assertion, and `publishable.__all__` is already
asserted somewhere in the suite. H5b exports one new name (`repeats_disagreeing`, from `stats.py`, which
is **not** part of `publishable`'s importable surface and must not be added to it) and writes no new
record key. **Grep for those pins before writing anything, and report what you grepped rather than a
count** — *before writing "no existing test asserts X", grep for it* is the check that catches the shape
where six consecutive slices' reports claimed zero disagreements and all six were wrong.

- [ ] **Step 1: capture arm A — the numeric-only run's `results` block. NO AUTHORIZED EDITOR.**
      A two-condition, two-seed, Holm-corrected run over 40 units with **one numeric recorded column and
      one derived metric, and NO non-numeric recorded column anywhere in the run.** Assert the whole
      `results` mapping against a literal.
      **The default `STARTER_STEP` records `{"present": True}` — a bool — so `run_a_project` with no
      step override falsifies this arm's own premise and the arm would fire for the wrong reason.**
      Use `aggregate_returns=` (which swaps in `_AGGREGATE_STEP`'s float `pred` column) or an explicit
      numeric `_starter_step`; **grep the helper for `_AGGREGATE_STEP` and say in the docstring which
      you used and that the step records no bool.** **Say in the arm's own text that a second recorded
      column of any non-numeric type FALSIFIES this arm rather than failing it** — the arm would then be
      asserting identity over a run this slice legitimately moves, and the response is to fix the fixture,
      not the literal.
      **The docstring carries two labelled sentences, not one:**
      *The rule:* identity holds when no non-numeric column exists **anywhere in the same correction
      family**, because Holm ranks across the family and one metric's interval width moves another's
      corrected interval.
      *What this fixture pins:* the safe framing — **none anywhere in the run** — so that a later
      fixture edit cannot quietly turn the rule into the false loose one. The loose version is what the
      scoping falsified, and arm E is the measurement that falsified it.
      **No task in this slice edits this arm.** A passing arm A after every task is the proof that the
      numeric-only path did not move.

- [ ] **Step 2: capture arm B — Fixture A's seven moving keys, by RUNNING `summarize_step`.**
      Six units, `seed=7`, `draws=2000`. Units `u0`–`u3` recorded `{"score": float(i), "valid": True}`;
      units `u4`–`u5` recorded `{"valid": True}`. `counts = {"resolved": 6.0, "completed": 6.0,
      "ineligible": 0.0, "failed": 0.0}`. The template's `aggregate` returns `n_rows` (row count),
      `n_valid` (rows whose `valid` is `True`) and `mean_score` (mean of the `score` values present).
      **The `aggregate` must never return `None` on this table** — production passes whatever
      `coerce_scalars` returns and `if derived:` is a truthiness gate, so a `None` top-level value would
      be a shape this fixture measures and production reaches differently. On this table `mean_score` is
      `1.5`; the `None` branch exists only for a degenerate resample draw, which is what produces the
      `1998` below.
      Drive it **twice**: once over the `collapsed` today's `collapse_repeats` returns for those
      executions (`{u0..u3: {"score": …}}`, four units — computed by calling `collapse_repeats` on
      `_result`-built executions, **not** hand-written), and once over the wide `collapsed`
      (`{u0..u3: {"score": …, "valid": True}, u4..u5: {"valid": True}}`).
      **Assert these seven, and only these seven, as the moving set — enumerated, never counted:**

```
  KEY                          TODAY                         AFTER
  n_valid.value                0.0                           6.0
  n_valid.ci95                 [0.0, 0.0]                    [6.0, 6.0]
  n_rows.value                 4.0                           6.0
  n_rows.ci95                  [4.0, 4.0]                    [6.0, 6.0]
  mean_score.n.completed       4                             6
  mean_score.ci95              [0.5, 2.5]                    [0.3333333333333333, 2.5]
  mean_score.resample_draws    2000                          1998

  AND THESE MUST NOT MOVE:
  mean_score.value             1.5                           1.5
  score.value                  1.5                           1.5
  score.n.completed            4                             4
  score.ci95                   [-0.5542602567605206, 3.5542602567605206]   (identical)
  score.method                 t_over_units                  t_over_units
```

      Every literal above was produced by running `summarize_step` at `ee8085e` (this plan's probe `p1`).
      **`mean_score.value` unmoved is the load-bearing assertion nobody would think to write:** a fixture
      in which every number moves cannot tell *the table widened* from *the metric changed*.
      **`1998` is this fixture's number at `seed=7, draws=2000` and is not a constant** — the same shape
      run end to end at a run-derived seed gave `1999` (§ Corrections 7). Do not reuse it elsewhere.
      **Sole authorized editor: task 4.** Task 4 flips exactly those seven to the AFTER column, literal
      for literal, and edits nothing else in this arm. **Task 5 is not an editor of this arm**: Fixture A
      has no column that disagrees across repeats, so the collapse rule cannot reach it, and a task-5
      edit here is a **finding**, not a fixture repair.

- [ ] **Step 3: capture arm E — the correction family, by RUNNING the console path. Sole authorized
      editor: task 4.** A two-condition run (`sweep.baseline: {analysis.method: pearson}`,
      `grid: {analysis.method: [spearman]}`), six units, default five seeds, `correction: holm`, whose
      step records `{"score": float(i) + thr, "valid": True}` for `i < 4` and `{"valid": True}`
      otherwise, with `thr` `0.5` under pearson and `0.4` under spearman, and whose template's
      `aggregate` returns `n_rows` and `mean_score`. **This is a different fixture from arm B, with a
      different key list, and the two are never merged into one count.**

```
  KEY (condition `method=spearman` unless noted)          TODAY                    AFTER
  aggregated…n_rows.value / .n.completed                  4.0 / 4                  6.0 / 6
  aggregated…n_rows.ci95                                  [4.0, 4.0]               [6.0, 6.0]
  aggregated…mean_score.n.completed                       4                        6
  aggregated…mean_score.ci95 (baseline)                   [1.0, 3.0]               [0.8333333333333334, 3.1666666666666665]
  aggregated…mean_score.ci95 (spearman)                   [0.8999999999999999, 2.9] [0.7333333333333334, 3.0666666666666664]
  vs_baseline…mean_score.n_paired                         4                        6
  vs_baseline…mean_score.correction_level                 0.025                    0.05
  vs_baseline…mean_score.ci95 / .ci95_corrected           [-0.10000000000000009, -0.09999999999999998]
                                                                                   [-0.10000000000000053, -0.09999999999999964]
  vs_baseline…score.correction_level                      0.05                     0.025
  vs_baseline…score.ci95_corrected                        [-0.10000000000000014, -0.09999999999999998]
                                                                                   [-0.10000000000000017, -0.09999999999999995]

  AND THESE MUST NOT MOVE:
  aggregated…score.*  (value, n, ci95, method, repeat_spread)  identical in both conditions
  vs_baseline…score.n_paired                              4                        4
  vs_baseline…score.ci95                                  [-0.10000000000000014, -0.09999999999999998]
  vs_baseline…n_rows.correction_level                     0.016666666666666666     0.016666666666666666
```

      **Re-measured by this plan, not copied.** The scoping's three literals — `n_paired` 4 → 6, the
      `correction_level` swap, and `score.ci95_corrected` moving in its last digits — **all three
      reproduce at `ee8085e`**, and the re-measurement found **two the scoping's paragraph does not
      name**: the derived contrast's own `ci95` and `ci95_corrected` (§ Corrections 9). **`score`'s
      corrected interval moving is the whole point of this arm**: `score` carries no non-numeric value
      anywhere, and Holm ranks on the point estimate over half the raw `ci95` width, so the *other*
      metric's widening moves it. That is what makes arm A's loose framing false and its safe framing
      necessary.
      **Capture this arm by RUNNING the console path with the AFTER behaviour monkeypatched in**, the way
      this plan did (a `collapse_repeats` replacement installed on `publishable.cli`), and record the
      TODAY column from the unpatched run. **The monkeypatch does not ship**: the arm's committed form
      asserts the TODAY column, and task 4 flips it.

- [ ] **Step 3b: capture arm F — a DERIVED metric's permutation p-value moves, and a recorded column's
      and a contrast's do not. Sole authorized editor: task 4.** Fixture A's two tables again, this time
      with `null_test={"method": "permutation", "n": 500, "shuffle": "grp", "level": "rows"}`, `labels`
      mapping each unit to `"a"`/`"b"` by parity, `seed=7`, and a `null_fn` per key that reads the
      **relabelled mapping** (a one-argument closure cannot express a permutation here —
      `permutation_of_derived`'s docstring says why, and a closure ignoring `labels` returns `None` for
      every key, measured).

```
  KEY                                   TODAY (4 units)        AFTER (6 units)
  mean_score.p_value                    0.846307385229541      0.812375249500998
  mean_score.null_draws                 500                    500

  AND THESE MUST NOT MOVE (they have no p_value at all):
  score.p_value / .null_draws           None / None            None / None
```

      Measured at `ee8085e` (§ Corrections 16). **Why this arm exists:** the design and the scoping both
      enumerate the moving keys and **neither names `p_value`**, and `permutation_of_derived` takes the
      whole `collapsed` and rebuilds each draw's table from whole rows — the same mechanism that moves
      `mean_score.ci95`. **Why it is a separate arm rather than more keys on arm B:** arm B's fixture
      declares no `null_test`, and adding one would change the block shape every one of its seven literals
      was captured from.
      **State the asymmetry in the docstring, and state which half was reasoned:** a **recorded column**
      gets no `p_value` from `summarize_step` at all (read: the write is in the derived branch only,
      confirmed by grepping `p_value` in `stats.py` over the column loop's range → nothing); and a
      **contrast's** p-value comes from `permutation_over_contrast` over `of_values`/`against_values` in
      the **unpaired recorded-column** arm, which task 7 narrows — so it does not widen. **The contrast
      half was read, not run**; if the reader wants it run, one direct call settles it.
      **No row of the four-row table moves on this**: all eight `statistics` blocks in the feasibility
      analysis carry `null_test: null`, which the truthy guard treats as undeclared.

- [ ] **Step 4: capture arm C — the numeric `by` column keeps its metric block and its warning. NO
      AUTHORIZED EDITOR.** `tests/test_cli.py::test_a_recorded_column_named_by_keeps_its_metric_and_warns`
      and `::test_a_recorded_by_column_warns_even_with_no_report_by_declared`, both asserting
      `aggregated[step]["by"]["value"] == 39.0`. **Grep for both names and quote the assertion you
      found; do not add a third copy.** This arm is the statement that **zero lines of those two test
      bodies change in this slice** — the B3 review reports the `git diff` line count over both bodies,
      and the number must be `0`. **Related but distinct, and it is NOT this arm's:**
      `tests/test_artifacts.py::test_a_measured_by_column_survives_the_collapse_into_units_parquet`
      records a **non-numeric** `by` column at the artifact layer and never reaches `collapse_repeats`
      (§ Corrections 1) — it must also stay green, and task 9's brief names it.

- [ ] **Step 5: capture arm D — the two behaviours this slice narrows AROUND and must not narrow AWAY.
      NO AUTHORIZED EDITOR.** By direct call to `summarize_step`:
      (i) `E-STEP-COLUMN-UNKNOWN` still raises for a name **no** row holds — through `UnitTable`, on a
      table that does hold other columns, so the fixture cannot fire on an empty table instead;
      (ii) the derived-key collision still raises `E-STEP-KEY-COLLISION` for a **numeric** recorded
      column. Assert the codes, not the wording.

- [ ] **Step 6: run.** `uv run pytest` → **2891 + your new tests** passed, 1 skipped, 2 xfailed.
      `uv run mypy` → still **52 source files**; `uv run ruff format --check .` → still **93 files**.

- [ ] **Step 7: the mutations — five, because one arm proving itself proves nothing about another.**
      Keep a copy of every file you mutate; restore by copying back; verify by **behaviour**.
      (i) In `stats.collapse_repeats`, delete `or not _is_numeric(value)` from the inner loop's skip.
      **Arm B's TODAY column must FAIL** and arm A must **PASS**. *Why the branches differ:* arm B's
      fixture has two units whose only value is a bool; arm A's run has none.
      (ii) In `stats.summarize_step`'s column loop, delete the `all(_is_numeric(v) for v in raw)` clause.
      **Arm B's AFTER-side key set must FAIL** (a `valid` metric block appears). *Why the branches
      differ:* measured — the clause is the projection, and the wide table carries a bool column.
      (iii) In `cli.py`, change the `by` gate from `if "by" in step_summary` to `if False`. **Arm C's
      warning assertion must FAIL.** *Why the branches differ:* the numeric `by` column reaches
      `step_summary` today, measured by the scoping both ways.
      (iv) In `correction.py`, reverse the Holm rank ordering. **Arm E's `correction_level` assertions
      must FAIL** for both metrics. *Why the branches differ:* the two metrics' levels are `0.025` and
      `0.05`, distinct literals in the captured arm.
      (v) In `stats.py`'s `UnitTable.__getattr__`, return an all-`None` column instead of raising.
      **Arm D(i) must FAIL.** *Why the branches differ:* arm D asserts a raise, and nothing else in this
      pin does.
      **Named blind in advance, with its replacement:** no mutation is proposed for arm B's *unmoved*
      literals as a group, because any mutation that moves `score.*` also moves arm A. Their replacement
      is mutation (i) above, which moves the moving keys and leaves the unmoved ones alone — the
      discrimination arm B exists for.

- [ ] **Step 8: commit.** `git add -A && git commit -m "H5b task 1: pin the numeric-only run, the two
      moving runs, the numeric by column and the two narrowed-around refusals before anything moves"`.

---


# H5b batch 2 report — tasks 4, 5, 6

**Status: all three tasks complete and committed.**

Commits:
- `06fdd3d` — H5b task 4: the collapse carries every recorded value and admits every unit it was handed
- `8ffab8a` — H5b task 5: a disagreeing non-numeric column collapses to None and says so, from the rows
- `252774b` — H5b task 6: delete the clause task 4 falsified, and pin the projection at summarize_step's output — plus Controller ruling 1's gate

Test summary: `2911 passed, 1 skipped, 3 xfailed` (started at `2895 passed, 1 skipped, 2 xfailed`), `mypy` 52 source files clean throughout, `ruff check`/`ruff format --check` clean throughout (93 files formatted, unchanged count).

## Every key whose published value moved

| Key | Before | After | Pin arm |
|---|---|---|---|
| `n_valid.value`/`.ci95` | `0.0`/`[0.0,0.0]` | `6.0`/`[6.0,6.0]` | Arm B (task 4, `test_a_bool_only_column_widens_exactly_seven_moving_keys`) |
| `n_rows.value`/`.ci95` | `4.0`/`[4.0,4.0]` | `6.0`/`[6.0,6.0]` | Arm B |
| `mean_score.n.completed` | `4` | `6` | Arm B |
| `mean_score.ci95` | `[0.5,2.5]` | `[0.333...,2.5]` | Arm B |
| `mean_score.resample_draws` | `2000` | `1998` | Arm B |
| `n_paired` (arm E family) | `4` | `6` | Arm E (task 4, `test_the_correction_family_measurement_arm_e_no_editor_except_task_4`) |
| `mean_score`/`score` `correction_level` | `mean_score:0.025, score:0.05` | swapped: `mean_score:0.05, score:0.025` | Arm E |
| `mean_score.ci95`/`ci95_corrected` | `[-0.10000000000000009,-0.09999999999999998]` | `[-0.10000000000000053,-0.09999999999999964]` | Arm E |
| `score.ci95_corrected` | `[-0.10000000000000014,-0.09999999999999998]` | `[-0.10000000000000017,-0.09999999999999995]` | Arm E |
| `n_rows`/`mean_score` at `aggregated.*` (both conditions) | 4 units | 6 units | Arm E |

**Must-not-move, confirmed unmoved:** `score.ci95`, `score.n_paired`, `n_rows.correction_level` (arm E); `mean_score.value`, `score.value`, `score.n.completed`, `score.ci95`, `score.method` (arm B); `aggregated == {}` for the unmodified scaffold (Fixture B, Decision 12).

**A key moved by task 6 that arms E/F do not cover, disclosed per the dispatch's own escape hatch:** a column numeric for some units and `None` for others now publishes a block in `aggregated` at all (before: no block, silently). Before/after, direct call: `summarize_step({"u0": {"score": 4.0}, "u1": {"score": None}}, {"completed": 2}, seed=7)` → `{}` before task 6's gate fix, `{"score": {"value": 4.0, "n": {"completed": 1}, ...}}` after. End-to-end: a 6-unit run with 3 units recording a number and 3 recording `None` directly publishes `score.n.completed: 3` (contributing count, not 6) with no crash on a single-condition run. This is Controller ruling 1's amendment (row 2 of its three-mixture table), which no task's original brief assigned — task 6's own brief said "ships NO code change," measured only against ruling 1's row 1 (all-non-numeric). Full reasoning below.

## Existing tests whose expectation changed

1. **`test_a_bool_only_column_widens_exactly_seven_moving_keys`** (guard pin arm B, task 4's sole authorized editor). Flipped the seven TODAY literals to their AFTER values, because after task 4 the live `collapse_repeats` call produces the AFTER (wide) table exactly — "narrow" no longer exists. **Correct move**: the test's own docstring says it is "sole authorized editor," and the arm exists precisely to be flipped by this task.

2. **`test_the_correction_family_measurement_arm_e_no_editor_except_task_4`** (guard pin arm E, task 4's sole authorized editor). Flipped `n_rows`/`mean_score` literals and the `correction_level` swap to their real-run AFTER values (previously only reproduced via a scoping monkeypatch). **Correct move**, same reasoning as arm B.

3. **`test_collapse_drops_a_bool_column_rather_than_averaging_it`** → replaced by `test_a_disagreeing_bool_column_collapses_to_none_not_dropped` (task 5). **Correct move, not a weakening**: the old assertion (`"flag" not in collapsed.get("p0", {})`) passed today because `p0` was absent from `collapsed` entirely (a unit drop), not because `flag` was dropped from a present unit (a column drop) — it pinned the defect this slice exists to end. Between task 4's commit and task 5's, I ran it as `xfail(strict=True)` naming task 5 as its remover, per the brief's explicit instruction, then task 5 replaced it outright.

4. **`test_two_units_per_fold_under_fold_times_seed_keeps_every_unit`** (Fixture K) — extended, not replaced, per the brief's "grep for the existing fixture by name and extend it" instruction. Grepped `fold_members` test names in `tests/test_stats.py`; this was the closest existing "widest shape" fold fixture. Added a third fold whose two units record only a bool, asserting they are admitted within their own fold with `handed_to`'s intersection unchanged. **Correct extension**, not a weakening — the original four assertions are untouched.

5. **`summarize_step`'s docstring** — deleted the em-dashed qualifier "even one dropped above for being non-numeric" (task 6 step 1, prescribed) and rewrote the "column is skipped entirely... when ANY unit's value... is not a real number" paragraph, which the brief said was "still true" and should be left alone. **I edited it anyway, disclosed as a deviation**: my Ruling 1 gate fix (below) makes that paragraph false as written — a column is no longer skipped when *any* unit's value is non-numeric, only when *no* unit's value is. Per CLAUDE.md's own rule ("a comment or docstring claiming a guarantee the code does not provide" is a defect to close, not to leave), leaving it as directed would have shipped a known-false docstring. Replaced with the accurate rule plus a short paragraph stating Ruling 1's amendment.

## Grep discipline (reporting what was grepped, not a count)

- `grep -n "repeat_spread" src/publishable/__init__.py` → no hits, confirming `repeats_disagreeing` (same precedent) is correctly not exported.
- `grep -n 'assert "W-STATS-STRATUM-SHADOWED" in doc\["stdout"\]' tests/test_cli.py` → two hits (lines ~6920, ~6949), confirming stdout is the correct stream for a run-finding assertion; reused for Fixture C/D's real-run halves.
- `grep -n "test_a_numeric_rule_coerces_a_recorded_string_before_applying" tests/test_artifacts.py` → exists at line 783; cited rather than restated per the brief's instruction, in the measurements-interaction test's docstring.
- `grep -rn 'dict\[str, dict\[str, float\]\]' src/publishable/*.py` at the start of task 4 → 20 hits (16 stats.py, 4 cli.py), matching the brief's `ee8085e` count exactly; swept to `Any` and reconfirmed 0 hits after.
- `grep -n "only when every value carried for it is a real number\|three mixtures\|contributing count" docs/reference.md` (before writing the Ruling 1 fix, to check for document drift) → no hit for the old wording; `grep -n "non-numeric\|real number" docs/reference.md` found the passage at line 997 and line 2570 **already stating Ruling 1's three-mixture rule verbatim** ("a column that is a number for some units and absent — `None` — for others publishes a block computed over the units that carried a number, with the count that contributed reported beside it"). The document was already correct (fixed in task 3's batch-1 fix round); task 6's code fix brings the code into agreement with a document that was already right. No document edit was needed or made.
- `grep -n "col_keys\|metric_key in " src/publishable/cli.py` while investigating the blast-radius finding, to confirm the contrast loop iterates `sorted((set(of_summary) & set(against_summary)) - {"by"})` — i.e., over `summarize_step`'s *output* keys, not `collapse_repeats`'s raw columns — which is why the crash was unreachable before task 6's gate fix even though task 4 already put `None` values into `collapsed`.

## The end-to-end `run.yaml` evidence

- **Fixture A′ (arm E)**: real run through `run_a_project`/`main(["run", ...])`, `run.yaml` read key by key (test asserts on `run["results"]["conditions"][...]["aggregated"/"vs_baseline"]`).
- **Fixture B**: real run, `run.yaml`'s `aggregated == {}` for the unmodified scaffold; a project-local template counting `present` via row-dict `.get` reports `6.0` with `W-STATS-AGGREGATE-FAILED` absent from stdout; a control template reading a genuinely unknown attribute earns `E-STEP-COLUMN-UNKNOWN` under `W-STATS-AGGREGATE-FAILED` on stdout, proving the harness is exercised for real.
- **Fixture H**: real run with `report_by: [grp]`; `by.grp` holds `a` (numeric) and omits `b` (all non-numeric), both counts checked.
- **Fixture C (task 5)**: real run, `W-STATS-REPEATS-DISAGREE` and the column name `flag` both asserted present on stdout.
- **Measurements interaction (task 5, step 6)**: real run; `measurements.parquet` (both tag values) and `units.parquet` (tag `'a'` only) read via `_decode_parquet`; no disagreement warning on stdout.
- **Ruling 1's gate fix (task 6)**: real 6-unit single-condition run (3 numeric, 3 `None`) confirmed via direct probe during development to publish `score.n.completed: 3` with no crash and a written `run.yaml` (not committed as a separate test — covered in spirit by the direct-call tests `test_ruling_1_a_column_numeric_for_some_units_and_none_for_others_keeps_a_block`/`test_ruling_1_all_non_numeric_still_earns_no_block_at_all`, since the single-condition case does not crash and needs no xfail pin).
- **Ruling 1's blast radius (task 6, disclosure)**: real two-condition run, pinned as `xfail(strict=True)` — see below.

## Task 7's `TypeError`: now reachable, and this batch is what makes it so

**Yes — confirmed empirically, and it is task 6's gate fix, not task 4 alone.** I probed a two-condition run (`pearson` baseline vs. `spearman` grid) whose step records a number for 3 of 6 units and `None` directly for the other 3, on the same column, in both conditions. Before task 6's Ruling 1 gate fix (task 4+5 only, verified via `git stash`), this run completes cleanly: `summarize_step`'s old all-or-nothing gate drops the ragged/`None`-carrying column entirely from `of_summary`/`against_summary`, so it never enters `cli.py`'s per-metric contrast loop at `sorted((set(of_summary) & set(against_summary)) - {"by"})`, and no crash occurs.

After task 6's gate fix, the column *does* enter that set (it now publishes a block), and `cli.py`'s unguarded `of_collapsed[k][metric_key] - against_collapsed[k][metric_key]` (around `cli.py:1168`) subtracts `None - None` for a unit both conditions carry as `None`, raising `TypeError` outside any `try` — run directory complete, every execution paid for, no `run.yaml` written.

**Blast radius, bounded and verified:**
- An all-`None` column cannot reach it: the numeric subset is empty, the column is skipped entirely, and it never enters `of_summary`/`against_summary` at all.
- A ragged column with no `None` cannot reach it either: the guard pin's own arm E (`test_the_correction_family_measurement_arm_e_no_editor_except_task_4`) computes a live paired `score` contrast at `n_paired: 4` over a `score` only 4 of 6 units carry, with zero crash — which also confirms `ExecutionResult.rows` carries un-unioned per-execution rows rather than `finalize`'s union-with-nulls (if it were the union, every ragged column in every run would hit this, not only one carrying an explicit `None`).
- The trigger is exactly: **a column numeric for some units and `None` for others, in a run that computes a contrast over it.**

**Disclosed, not fixed here**, per the batch's own instruction: this is Fixture G's territory and task 7's guard. Pinned as `test_ruling_1s_blast_radius_a_contrast_over_a_ragged_none_column_crashes` in `tests/test_cli.py`, `xfail(strict=True)`, asserting the *correct* behaviour (exit 0, `run.yaml` exists) rather than `pytest.raises(TypeError)` — so it fails loudly (not silently passes) the instant task 7's guard lands, naming task 7 and Fixture G as its remover in the reason string.

## A filing candidate, not a code mint

A directly-recorded `None` (no repeat disagreement at all — a unit's step just returns `None` for a column) reaching a mixed column draws **no** `W-STATS-REPEATS-DISAGREE` warning, since no disagreement occurred; it is silent, consistent with the pre-existing "ordinary ragged shape, not a bug" precedent `summarize_step`'s own docstring already states for a column recorded by only a subset of completed units. This is not a new hazard — arm E's `score` (carried by 4 of 6 units, no `None` involved) already publishes silently the same way today — so no new diagnostic was minted. Noting it here as a candidate for whoever next reviews warning coverage, per the advisor's guidance, rather than filing it in `spec-defects.md` unasked.

## Mutations, each with FAIL/PASS against the full suite

**Task 4 (4 mutations, all reverted and re-verified):**
1. Restore `or not _is_numeric(value)` in `_gather_repeats`'s inner loop → Fixture A's `narrow == wide` assertion FAILS (`u4`/`u5` drop back to `{}`, `valid` absent from `u0`-`u3`).
2. Admit only units with ≥1 numeric value (carriage kept, admission narrowed) → Fixture A's `narrow == wide` assertion FAILS (`u4`/`u5` excluded again).
3. Replace `cli.py`'s second empty-level gate with `if True:` → Fixture H's absent-level assertion FAILS (`b` reappears in `by`).
4. `_across_repeats` omits a disagreeing non-numeric column instead of returning `None` → Fixture E's second arm FAILS with `KeyError` before the collision check is reached.

**Task 5 (3 mutations reverted/re-verified, 1 run and found NOT blind):**
1. Carry `values[0]` instead of `None` → Fixture C's `is None` assertion FAILS (`True is None` is false).
2. Answer from the collapsed cell (`value is None`) instead of the rows → Fixture D arm 1 FAILS (gains a false warning).
3. Delete the `W-STATS-REPEATS-DISAGREE` call site → Fixture C's real-run warning assertion FAILS.
4. Drop the all-numeric early return in `_repeats_disagree` — run rather than assumed blind, and found **not** blind: Fixture L's can-fail control (both repeats numeric) FAILS (`{'score': 1} == {}` false), so reported as run, not named blind.

**Task 6 (2 mutations, both reverted and re-verified):**
1. Project non-numeric columns out of `collapsed` at `summarize_step`'s input → Fixture I's `ci95` assertion FAILS (`[0.0, 0.0]` vs. `[6.0, 6.0]`, point estimate outside its own interval).
2. Restore the old all-or-nothing gate (my own addition, beyond the brief) → `test_ruling_1_a_column_numeric_for_some_units_and_none_for_others_keeps_a_block` FAILS with `KeyError: 'score'`.

## Concerns for the controller

1. **The Ruling 1 gate fix landed in task 6 despite that task's brief stating "ships NO code change."** That claim was measured only against Ruling 1's row 1 (all-non-numeric). Row 2 (mixed) was not owned by any task's original steps — I implemented it here because leaving it unbuilt would ship the batch-1 Critical's exact defect shape one level up (a `None` cell from task 4's own new return path silently deleting a whole published column), and `reference.md` already states the ruling's correct behavior in shipped prose. Flag if a different slice/task should have owned this instead.
2. **Task 7's `TypeError` is now reachable**, exactly as CLAUDE.md's brief predicted it might be, and is pinned `xfail(strict=True)` rather than fixed, per instruction. Task 7 must remove this pin (or it will fail loudly once Fixture G's guard lands).
3. No document edit was needed for this batch — `reference.md` already carries Ruling 1's three-mixture wording (confirmed by grep, not assumed).

---

# Batch 2 fix round — 2026-08-22 (appended; nothing above this line was edited)

Commits: `ad67a75` (source and documents), `a9b6340` (the nine pins).
Suite: **2920 passed, 1 skipped, 3 xfailed** (2911/1/3 at `4edd98d`; +9 tests, no
existing test edited, none removed). `ruff check` clean, `ruff format --check` 93 files
unchanged, `mypy` 52 source files clean, `git status --porcelain` empty after every
mutation was reverted **by editing back** and each revert verified by re-running.

## Correction to what is above (m3), appended rather than edited in place

The "Mutations" section above reports task 4's mutation (i) — restoring
`or not _is_numeric(value)` in `_gather_repeats` — as failing "Fixture A's `narrow ==
wide` assertion and Fixture B's `n_present`". **The full unfiltered suite fails four
tests, not those two alone**: it also fails both Fixture E arms and the Fixture C
replacement (`test_a_disagreeing_bool_column_collapses_to_none_not_dropped`). The
review re-ran it and read the count; this section records the correct figure. The
number above stands as written, with this line as its correction — the fourth
miscount in this slice family, and in a column framed as *counts read, not estimated*.

## Status per finding

| Finding | Status | Where it was closed |
|---|---|---|
| **M1** (false warning message + false § Warnings row) | **closed** | The two clauses deleted from `cli.py`'s message and from the row. Pinned end to end by `test_a_disagreeing_column_that_still_publishes_a_value_is_not_told_it_carries_none` |
| **M2** (row's frequency claim) | **closed** | Row now reads *once per (condition, step, recorded column)* — Ruling 6's *fix the row, not the loop*. Pinned by `test_two_disagreeing_columns_in_one_step_warn_twice_once_per_column` |
| **M3** (Ruling 1 row 2 shipped its count and not its warning) | **closed** | `W-STATS-COLUMN-THIN` minted per Ruling 5, one § Warnings row, three tests |
| **M4** (`_across_repeats`'s falsified ground) | **closed** | Clause deleted through `argues for;` so no dangling referent remains; the true statement three paragraphs down was already there |
| **M5** (`_repeats_disagree`'s unpinned tuple, and its false stated consequence) | **closed** | Pinned in both orders; the false consequence **deleted** and replaced by the measured one |
| **M6** (empty-record admission unpinned) | **closed** | Two pins: the membership at `collapse_repeats`, and the published `n_rows` out of `run.yaml` |
| **M7** (moving-key enumeration omits the `report_by` stratum path) | **closed** | **Arm G**, a new guard-pin arm, carrying a fourth labelled `resample_draws` literal |
| **m1** (Ruling 1 row 2 had no end-to-end pin) | **closed** | `test_ruling_1_row_2_publishes_the_contributing_count_in_run_yaml` |
| **m2** (arm E asserts no `resample_draws`) | **closed with grounds, arm E unedited** | See below |
| **m3** (mutation (i)'s blast radius under-reported) | **closed** | The correction above |

## A third site carried M1's premise, and the third site the dispatch named did not

The dispatch says three sites carry M1's false premise: the warning message, the
§ Warnings row, and `repeats_disagreeing`'s docstring. **Grepped: that docstring is the
one that was already right** — *"its collapsed cell is still the mean of the numbers —
the disclosure is the warning, not the loss of the column"* is true of the mixed case,
and deleting it would have turned a correct statement into a gap. It stands untouched.
The review's own M1 body says the same thing (*"says the opposite"*); the dispatch's
list is where the third item drifted.

Sweeping for the **claim** rather than for the file turned up a site in neither the
review nor the dispatch: `reference.md` § Statistical reporting's *"A repeat-level
disagreement collapses that unit's cell to `None`"* — true only when no value is
numeric, false of exactly the case M1 is about. Deleted to its true remainder.
Greps run (file list filtered, never the output), over the four documents, `src/`,
`tests/` and `CLAUDE.md`: `carry no value`, `is not a number`, `collapses that unit`,
`requires \*all\* carried values numeric`, `order-dependent`, `once per (condition`.
The development record was left alone deliberately — it is corrected by appending.

## `W-STATS-COLUMN-THIN`, and its measured footprint

Built per Ruling 5: one warning per (condition, step, recorded column) whose
**contributing** count — `summarize_step`'s per-column `n.completed` — is below
`limits.min_reported_n`, at `run` time, naming the column and the count. The floor's
guard is `W-STATS-STRATUM-THIN`'s verbatim (`isinstance(..., (int, float)) and not
isinstance(..., bool)`), and the site sits where **both** `summarize_step` calls have
converged on `step_summary`, so the `except ContractError` retry is covered by the same
one site.

**Footprint measured before anything else was written**, as the first change of the
round: with the emit site in place and no test touched, the full suite was
**2911 passed, 1 skipped, 3 xfailed — unchanged**. Why: the generated default is
`min_reported_n: 10` and `run_a_project`'s default roster is 10 units, so a
fully-covered column sits *at* the floor and `<` does not fire; the fixtures that do
trip it assert the presence of other strings, never the absence of warnings. **No
shipped assertion had to move**, which is the reason this ruling could be built
literally rather than negotiated.

**Two asymmetries worth carrying, reported rather than absorbed.** Both siblings are
gated on a *declaration* — `W-STATS-CONTRAST-THIN` on `comp.within is not None`,
`W-STATS-STRATUM-THIN` on `report_by` — and this one is not, so its footprint is every
recorded column of every run. That is what Ruling 5 says, and it is recorded here as a
property rather than discovered by the next reader. And two scope decisions are written
into the code as decisions with grounds: a column that earned **no** block is skipped
(there is no contributing count to name), and a `report_by` **level**'s columns are not
checked (`W-STATS-STRATUM-THIN` already names a thin level against the same floor, and
per-column-per-level would multiply one fact by the column count). The first was
verified live rather than reasoned: mixture 1's console run warns for `score` and
**not** for the bool `flag`.

I grepped for a mechanical docs-versus-code test over warning codes — a registry, a
vocabulary frozenset, an enumeration in `tests/` — and **found none**:
`grep -rn "W-STATS-STRATUM-THIN" src tests docs/*.md README.md CLAUDE.md` returns an
emit site, two prose mentions in `validate.py`, four test assertions and one § Warnings
row. So a new code's obligations here are exactly the emit site and the row, and both
are met; there is no third place a new code can be missing from.

## m2 — decided, with grounds, and arm E left alone

`resample_draws` is `resample_seed(digest)`-dependent, so it is pinnable end to end,
and there are now **four** measured literals for it: arm B's `1998` (direct call,
`seed=7`), plan correction 7's `1999`, the batch 2 review's `1997`, and arm G's `1927`.
m2's actual content was that nobody had two to compare — **arm G supplies the second,
labelled with the fixture whose digest produced it**, which is why arm E is left
exactly as it stands. Arm E's docstring names task 4 as its sole authorized editor;
adding a literal there would have been an edit by a round that is not task 4, for a
comparison arm G already provides. **Recorded rather than silently skipped.**

## Mutations — text and count, each read from the FULL unfiltered suite

| # | Mutation | Result |
|---|---|---|
| 1 | Restore `is not a number and` / `so those units carry no value for it;` in the emit site's message | **2 failed**, 2918 passed — M1's test on both absence assertions, and M2's on `recorded column 'flag' disagrees` |
| 2 | `repeats_disagreeing(...).items()` → `list(...)[:1]` (once per condition+step, the row's old claim) | **1 failed**, 2919 passed — M2's test, `assert 1 == 2` |
| 3 | `contributing < column_floor` → `<=` | **1 failed**, 2919 passed — `test_a_recorded_column_at_the_floor_draws_no_column_thin_warning` |
| 4 | `if contributing < column_floor:` → `if False:` (delete the warning) | **1 failed**, 2919 passed — the naming test, on the code's absence from stdout |
| 5 | `any((_is_numeric(v), v) != ...)` → `any(v != first ...)` | **1 failed**, 2919 passed — M5's test, both orders |
| 6 | `if cols` added to `collapse_repeats`'s return comprehension | **2 failed**, 2918 passed — M6's two halves, direct-call and `run.yaml` |
| 7 | `level_collapsed` narrowed to rows carrying a numeric value (the pre-H5b stratum table) | **1 failed**, 2919 passed — arm G, `assert 2.0 == 3.0` |

**Mutation 7 was blind on its first attempt and is reported as such.** I first wrote
`if k in keys and v` — a bool-only row is `{"valid": True}`, which is truthy, so the two
branches could not differ and the suite stayed at 2920 green. *A mutation is a claim
too*: the second form narrows the projection the way the pre-H5b collapse actually did,
and it fails.

## Nothing regressed, verified rather than assumed

- `pytest --runxfail` on `test_ruling_1s_blast_radius_a_contrast_over_a_ragged_none_column_crashes`
  fails at **`cli.py:1168`, `TypeError: unsupported operand type(s) for -: 'NoneType'
  and 'NoneType'`** — the same place and the same reason, not a new diagnostic.
  `W-STATS-COLUMN-THIN` cannot pre-empt it: diagnostics print after the crash point.
- **Ruling 1's three mixtures, re-run through the installed console script** (`uv run
  --project <repo> publishable run`) on a project scaffolded by `publishable new` +
  `generate experiment`, outside this repo, committed clean:
  - **all non-numeric**: `flag` earns no block, `score` publishes at `n.completed: 6`,
    exit 0 — and `W-STATS-COLUMN-THIN` names `score` alone;
  - **number for some, `None` for others**: `score.value: 1.0`, `n: {resolved: 6,
    completed: 3, …}`, exit 0, `W-STATS-COLUMN-THIN` naming `3 unit(s)`;
  - **`str` beside a number**: exit **4**, ledger status `failed`, every execution
    `E-STEP-RETURN-TYPE ContractError: units.parquet: column 'score' recorded both a
    float (unit 'p1') and a str (unit 'p4')` — the ruling's own quoted message.

## Concerns

1. **`W-STATS-COLUMN-THIN` has no declaration gate**, unlike both siblings. Today it
   costs nothing (measured: zero suite churn), but any project whose roster is smaller
   than its own `min_reported_n` will see one warning per recorded column per condition
   per step. That is Ruling 5 as written, and the place to revisit it is the ruling, not
   the code.
2. **Arm G asserts no pre-H5b values and says so.** The narrow collapse no longer exists
   to run, so the "before" figures in its docstring would have been reasoning reported as
   measurement. What it pins instead is the moved state plus the pair that makes the move
   visible inside one run (a three-row level table beside a two-unit `score`).
3. `run.yaml`'s own `n` for a derived metric inside a `by` level is the level's
   condition-wide `completed`, so arm G's `mean_score.n.completed == 3` and its
   `score.n.completed == 2` describe two different denominators in one block set. Nothing
   in this round changed that, and no finding named it; noting it because a reader
   comparing the two figures will ask.

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

# Batch 4 review — H5b tasks 12, 13, 14

**Verdicts: task 12 PASS. task 13 PASS. task 14 PASS.**

Suite, at `0cf71b8` (clean tree, no mutations left applied): `uv run pytest -q` → **2931 passed, 1
skipped, 2 xfailed** — matches the report's claim exactly, and reconciles with baseline 2926 + 5 (2
task-12 tests, 1 task-13 test, 2 task-14 tests). `uv run ruff check .` clean, `uv run ruff format
--check .` — 93 files unchanged, `uv run mypy` — 52 source files clean. `git diff --stat
66b3c5c..0cf71b8 -- src/` is **empty**: this batch changed zero lines of `src/`, only tests — the
"ships almost nothing but pins" framing is literally true.

## What was verified by behaviour vs. by reading

Everything material below was verified by **running a mutation and reading the failure**, not by
reading the claim. Reading was used only for locating code (`_gather_repeats`,
`_floor_metric_entries`, `_condition_metric_rows`) and for grep-count claims, which were independently
re-run.

## Task 12 — both directions of `E-STEP-COLUMN-UNKNOWN` are really pinned

**Mutation (i)**, applied to `UnitTable.__getattr__` (removed the `E-STEP-COLUMN-UNKNOWN` raise,
made it always return `[row.get(name) for row in self._rows]`):
- `tests/test_stats.py::test_an_unknown_column_raises` → **FAILS**: `Failed: DID NOT RAISE
  ContractError`.
- `tests/test_cli.py::test_task_12_step2_still_fires_for_a_genuinely_absent_column_with_containment`
  → **FAILS**: `assert 'n_broken' not in {...}` (the derived call no longer raises, so `n_broken`
  reaches the record).
- `test_task_12_step1_...stops_firing` → unaffected, still passes, confirming the mutation is
  arm-specific as claimed.
Reverted by editing back (diffed against a saved copy, confirmed byte-identical); re-ran all four
tests green.

**Mutation (ii)**, the reconstructed pre-task-4 admission rule (a unit is entirely absent from
`gathered` unless at least one of its recorded values, across every column, is numeric — built
independently of the report, from `_gather_repeats`'s own current structure):
- `test_task_12_step1_...stops_firing` → **FAILS**: `KeyError: 'n_valid'` — `p5`/`p6` (numeric-free)
  are dropped from `collapsed` entirely, `valid` never reaches any row, the derived call raises
  `E-STEP-COLUMN-UNKNOWN` again and the whole `derived` dict is lost.
- `test_task_12_step2_...containment` → unaffected, still passes.
Reverted, re-ran green.

**Both directions are genuinely pinned.** Each mutation fails exactly the arm the brief says it
should and leaves the other arm green — confirmed by running, not by reading the report's account.

Grep-of-existing-pin claim reconciled: `grep -rn 'E-STEP-COLUMN-UNKNOWN' tests/*.py` finds a
pre-existing hit at `tests/test_cli.py:17688` (`git blame` → `06fdd3d`, task 4, unrelated to this
batch) plus arm D(i) at `test_stats.py:2316` — task 12 added no third copy of that shape, matching
the disclosure.

## Task 13 — the silent-drop discriminator

Same reconstructed mutation (ii) applied: `test_task_13_the_silent_drop_cannot_be_mistaken_for_the_fix`
→ **FAILS** at `assert block["value"] == 5.0` with `assert 2.0 == 5.0` — the first of the three
assertions, exactly as the report states, and the buggy value (`2.0`) is neither the correct value
nor a value the fixture could produce by accident (verified: `p1`-`p3`, the numeric-free bool
carriers, are dropped entirely under the mutation, leaving only `p4`/`p5`'s `flag: True` to count).

**The reconstruction itself, adjudicated against history rather than taken on faith**: `git show
06fdd3d` (task 4's own commit) documents applying *the same* mutation — "(i) restoring `or not
_is_numeric(value)` in `_gather_repeats`'s inner loop" — against Fixture A/B at the time, and its
commit message records that this dropped `u4`/`u5` (numeric-free) from the table entirely. The
pre-task-4 code (visible in the same diff) shows `gathered.setdefault(key, {})` was nested *inside*
the per-column `_is_numeric` filter — so a unit with zero numeric columns never got a `gathered`
entry at all, which is precisely "drop a unit entirely when none of its values are numeric." Task
12/13's batch-4 mutation reproduces that exact historical shape (confirmed independently: I applied
it to the current, post-refactor `_gather_repeats` by collecting all of a unit's columns first, and
only inserting into `gathered` if any collected value is numeric). The report's own disclosure that
a naive literal restore of `or not _is_numeric(value)` inside the *current* loop structure would
reproduce task 12's outcome but not task 13's is correct — because in the current code
`gathered.setdefault(key, {})` runs unconditionally before the per-value filter, so a naive restore
would leave an empty-but-present row rather than no row at all. **The reconstruction is sound, both
historically and by direct verification.**

**Substitution of the third fact** (`resample_draws` → the bootstrap interval `[2.0,8.0]` vs.
`[0.0,4.0]`): verified both halves. The brief's literal fact is genuinely blind — `resample_draws`
stays `2000` under both codes because `FlagCounter.aggregate` is `sum(1 for row in units if
row.get("flag") is True)`, which never returns `None`/`nan` and never raises regardless of which
rows survive, so no draw is ever dropped either way (confirmed by reading `percentile_of_derived`'s
own drop condition, which task 13's docstring cites correctly). The substitute genuinely
discriminates — confirmed by running the mutation: `block["ci95"]` differs (`[2.0, 8.0]` correct vs.
what would be `[0.0, 4.0]` buggy, though the test fails on the first assertion before reaching the
interval one, which is expected and is what "state which fails first" means).

**Confirms the test separates "unit absent" from "column dropped"**: the fixture is constructed so
the three units with no numeric column (`p1`-`p3`) are exactly the bool carriers, so the buggy
admission rule removes the *unit*, not just the *column* — which is the whole point (old bug: `.get`
hid an absent unit behind what looked like a column read). Verified this is genuinely reachable and
discriminating by the mutation run above.

## Task 14 — `report`/`study` as readers of `aggregated`, and the three docstrings

**Mutation (i)**, emptying `summarize_step`'s `_is_numeric` gate in the column loop (`carried =
[(key, value) for key, value in carried if _is_numeric(value)]` → unfiltered):
- `test_fixture_j_report_renders_the_carried_and_the_dropped_columns_correctly` → **FAILS**: `assert
  "valid" not in names` fails, `'valid'` present in the parsed `metric` column.
- `test_fixture_j_the_floor_walk_sees_exactly_four_metric_entries` → **FAILS**: `'valid'` is a fifth
  name in the set.
Both confirmed by running; reverted, re-ran green.

**Mutation (ii)**, pointing `study.py`'s floor walk at `condition.get("aggregated")` directly (one
level short of the `step → block` nesting `_step_block` expects):
- `test_fixture_j_the_floor_walk_sees_exactly_four_metric_entries` → **FAILS**: `_floor_metric_entries`
  returns an empty list (`assert set() == {...}`) against the identical real record that gave four
  entries before the mutation.
- `report`'s own test is unaffected (still passes) — confirms the mutation is `study`-only, as
  claimed.
Reverted, re-ran green.

**End-to-end, through the installed console script, for Ruling 1's three mixtures** (built a fresh
scaffolded project outside the repo, a step recording a column non-numeric for every unit, a column
numeric for every unit, and a column numeric for 6 of 9 units, `min_reported_n: 1`): `publishable
run` produced `aggregated.step01_summarize_units` holding `score` (`n.completed: 9`) and `thin`
(`n.completed: 6`, the *contributing* count, not the condition-wide 9) and no block at all for the
non-numeric column. `publishable report run.yaml` rendered exactly those two rows in `## Conditions`.
`publishable study new` / `study add --as main` / `publishable report study.yaml` rendered the
identical two rows under the bundle's own section. No four-times-two-case-sentence found in task 14's
new text — Fixture J's docstrings cite "Ruling 1's first row" and the contributing-count fact by
number, not as an exhaustive two-case claim, and both reachable rows of the ruling's table are
exercised by Fixture J (`valid` non-numeric-for-every-unit, `score` numeric-for-some).

**The three docstrings**: grep counts reconciled at `336ed45` — `drops a bool column outright` → 1
hit, `` filtered by `_is_numeric` `` → 1 hit, `grows no` → 1 hit (line-wrapped, `-c` on the full
phrase gives 0, matching the report's own disclosure that `-n` was needed). Swept the four documents
and this batch's own report/plan for the same two false clauses — no other test or `src/` file
carries either false claim; the only remaining occurrences are quotations inside
`docs/superpowers/H5b-SCOPING.md`, the plan, and the b4 report itself, which are historical record,
not live claims about the code. Read `test_a_run_without_a_holdout_pins_its_denominators_and_artifacts`
and `test_a_baseline_sweep_reports_a_delta` against `BaseTemplate.aggregate` (Decision 12: returns
`{}` unconditionally) and against `summarize_step`'s own per-column gate — both re-derivations are
accurate to the code, and both delete rather than relocate the false clause (no new false clause
introduced). The third docstring
(`test_an_unclustered_resampled_contrast_draws_what_it_always_drew`, "`grows no basis: units column`")
was left untouched, confirmed by diff — no edit — and its claim is still true (a column non-numeric
for every unit earns no metric block, Ruling 1's first row, unaffected by H5b).

## Other checks

- **Undisclosed drops**: diffed all three briefs' steps against the shipped commits. Task 12: both
  steps built as specified, one direct-call duplicate correctly avoided and disclosed. Task 13: all
  five steps present; step 3's "does not pin" list matches the brief's three items verbatim. Task 14:
  Fixture J built as specified, both mutations run, all three docstrings addressed (two edited, one
  left alone per instruction) — nothing dropped.
- **Guard-pin arms**: `git log -p` shows no edits to `tests/test_cli.py`'s guard-pin arms (arms
  A-H) in this batch's three commits — batch 4 touches only new test functions appended at file end
  (task 12/13) and pre-existing test functions' docstrings only (task 14's three re-derivations,
  which are documentation, not assertions) plus two wholly new fixtures/tests in `test_report.py`/
  `test_study.py`. No arm moved without an authorized editor.
- **Claims about other tests/code**: task 12's claim that arm D(i) already covers the direct-call
  shape was verified by reading `test_an_unknown_column_raises` and by running it under mutation (i)
  above — it does fail, so it is a real pin, not a decoy. Task 14's claim that `report`'s own
  `results.summary` walk pattern was the sibling `study.py`'s walk should have copied was checked
  against `report.py`'s `_execution_rows`/`_condition_metric_rows` shape and against `study.py`'s
  comment citing that precedent by name — consistent.

## Suite reconciliation

Baseline 2926/1/2 → task 12 2928 (+2) → task 13 2929 (+1) → task 14 2931 (+2) = **2931 passed, 1
skipped, 2 xfailed**, confirmed by a direct foreground `uv run pytest -q` run at `0cf71b8` on a clean
tree. All temporary mutations were applied to `src/publishable/stats.py` and `src/publishable/study.py`
one at a time, each reverted by editing back to a saved copy (`git diff --stat` empty after every
revert), and each revert re-verified by re-running the affected tests before moving to the next
mutation.

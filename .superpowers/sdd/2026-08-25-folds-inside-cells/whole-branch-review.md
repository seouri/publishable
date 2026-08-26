# H3c-3 — whole-branch review

Branch `h3c3-folds-inside-cells` at `ff53cf4`, against `main` at `dfc6b7d`.
Written incrementally; each section is appended as its check completes.

**VERDICT: IN PROGRESS** (see the end of this file for the final line).

---

## Check 1 — the bit-stability oracle: **HOLDS**

Measured, not read. A `main` worktree was created at
`…/scratchpad/wbr_h3c3/main` (commit `dfc6b7d`) and one probe script
(`…/scratchpad/wbr_h3c3/oracle.py`) was run under **both** trees' own
`uv run python`, writing a sorted JSON of every case.

**336 cases**, covering every no-cell input the two producers take:

- fold: rosters of 7 / 12 / 40 / 240 units × digests `3d8a1f`, `deadbeefcafe`,
  `0` × `k` ∈ {2,3,5} × `clusters` present/absent × `strata` present/absent.
  HEAD calls `partition_within_cells(roster, k, digest, {}, …)` **and**
  `partition_within_cells(…, None or {}, …)` and asserts the two agree; `main`
  calls `partition_units(roster, k, digest, …)`.
- holdout: the same rosters × `frac` ∈ {0.1,0.2,0.25,0.5} × `method` ∈
  {`random`, `by_attribute`, `stratified`} × two seeds × clusters
  present/absent. HEAD calls `holdout_within_cells(…, cells=None, …)` **and**
  `cells={}` and asserts the two agree; `main` calls `holdout_for`.
  Both sides record `train`, `test`, `seed` and `strata`, and a raise is
  recorded as its `type: message` so a refusal that moved would show as a
  difference too.

Result: `diff head.json mainout.json` → **byte-identical**, both for the
partitions' key lists in order and for the holdout plans' four fields.

**The oracle was proven able to fail.** With `partition_within_cells`'
reduction mutated to `digest + "x"` and `holdout_within_cells`' reduction to
`seed + 1` — the two lines the reduction rests on — the same comparison
produced **13021 differing lines**. Both mutations were reverted by editing
back and the comparison re-run: byte-identical again.

## Check 10 — gates

| Gate | Result |
|---|---|
| `uv run pytest` | **3416 passed, 1 skipped, 2 xfailed** in 383s |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 101 files already formatted |
| `uv run mypy` | Success: no issues found in 56 source files |

Run in the foreground, whole suite, after clearing `pytest-of-joon` and every
`__pycache__`. `main`'s 3338 → **+78** collected-and-passing, 1 skipped and
2 xfailed unchanged. Delta accounted for below (Check 10a).

### Check 10a — the delta against `main`'s 3338, accounted for

`pytest --collect-only` under both trees, ids sorted and `comm`-ed:
`main` collects **3341**, HEAD collects **3419** (= 3416 passed + 1 skipped +
2 xfailed, so nothing is silently deselected).

**9 ids removed, 87 added**, 3341 − 9 + 87 = 3419.

The 9 removals are each accounted for and none is a lost guarantee:

- 8 are the refusal tests of the two codes this slice retires —
  `test_a_fold_beside_a_cell_structure_is_refused`,
  `test_a_holdout_beside_a_cell_structure_is_refused`,
  `test_both_split_kinds_beside_a_cell_structure_report_both_codes`,
  `test_a_group_axis_alone_triggers_the_refusal_without_between`,
  `test_allocation_between_alone_triggers_the_refusal_without_a_group_axis`,
  `test_an_empty_group_axis_alone_does_not_trigger_the_refusal`,
  `test_an_evaluation_split_without_a_cell_structure_is_not_refused`
  (all `test_validate.py`) and
  `test_a_holdout_beside_a_cell_structure_is_core_defect_not_a_silent_choice`
  (`test_runner.py`). A retired refusal's tests going with it is the point.
- 1 is the `docs/experimental-designs.md` parameter of H9d guard-pin arm C,
  retired by the controller ruling in `ff53cf4`.

The 87 additions land in 8 files; no test file lost a test other than the 9.


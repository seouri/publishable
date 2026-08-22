## Task 5: the disagreement is disclosed from the ROWS, never from the collapsed cell

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: a direct call and a real `run`.** Design Decisions 2 and 3.

**The obvious design is wrong and was measured wrong.** A first draft said *a `None` value can only be
produced by the disagreement rule, so `cli.py` can warn by scanning `collapsed`.* Measured:
`coerce_scalars({"valid": None}, where=…)` returns `{'valid': None}` unchanged, and § The per-unit tables
states that a recorded cell may hold `None` and that a column of all `None` round-trips. **A recorded
`None` and a collapsed disagreement are the same cell**, so warning from the cell answers the question
with a proxy — the fault § Answering a question with a proxy records six times.

**Files:**
- Source: `src/publishable/stats.py`, `src/publishable/cli.py`
- Test: `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: the pure function, in `stats.py` beside `repeat_spread`.** `repeat_spread` is the sibling
      that already got it right: a separate pure function over `results`, called from `cli.py` beside the
      collapse, for a per-column across-repeats fact, with the warning living at the call site.
      **`stats.py` imports no findings channel and must not gain one.**

```python
def repeats_disagreeing(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, int]:
    """Column name → how many admitted units disagreed about it across their repeats.

    Asks the ROWS, not the collapsed cell. A recorded `None` and a collapsed
    disagreement are the same cell (`coerce_scalars` leaves `None` alone, and
    `reference.md` § The per-unit tables makes an all-`None` column legal), so a
    scan of `collapsed` would answer this question with a proxy and give one answer
    to two different facts.

    The same four arguments `collapse_repeats` takes, over the same `_gather_repeats`
    walk, so membership has one implementation. Sorted keys, so the warning order is
    a property of the roster rather than of the shuffle — the reason
    `_gather_repeats` sorts.

    A column whose values are all numbers never appears here: unequal numbers are
    what averaging is for. A column that is numeric in some repeats and a string in
    others DOES appear, and its collapsed cell is still the mean of the numbers —
    the disclosure is the warning, not the loss of the column (`_across_repeats`
    says why).
    """
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    counts: dict[str, int] = {}
    for cols in gathered.values():
        for column, values in cols.items():
            if _repeats_disagree(values):
                counts[column] = counts.get(column, 0) + 1
    return {column: counts[column] for column in sorted(counts)}
```

      **Not exported from `publishable`.** § The importable surface is an enumerated list and this is not
      on it; `stats.py` is implementation detail. **Grep `src/publishable/__init__.py` for `repeat_spread`
      and confirm it is absent** — that is the precedent, and report the grep.

- [ ] **Step 2: the one call site, in `cli.py`'s aggregation phase.** Immediately after
      `collapsed = collapse_repeats(...)`, before `counts`:

```python
                    for column, units_count in repeats_disagreeing(
                        results, step_name, cond.index, fold_members=fold_members
                    ).items():
                        aggregate_c.warn(
                            "W-STATS-REPEATS-DISAGREE",
                            aggregate_where,
                            f"condition {cond.index} step {step_name!r}: recorded column "
                            f"{column!r} is not a number and disagrees across the repeats of "
                            f"{units_count} unit(s), so those units carry no value for it; "
                            "declare data.units.measurements.collapse if the within-unit "
                            "collapse is what you meant",
                        )
```

      **`aggregate_where`, and the reason is the sibling row's own.** The fault is the recorded column,
      not `aggregate`, and `W-STATS-STRATUM-SHADOWED` — the other recorded-column finding in this same
      loop — already uses `aggregate_where` with that stated. `data.units.measurements` was considered
      and rejected as the `where` for exactly the reason the `by` row gives for not pointing at
      `statistics.report_by`: **there may be no such key in the file to point at.** Inventing a second
      convention for one class of fault is the two-sources-of-truth move.
      **Add `repeats_disagreeing` to `cli.py`'s `from publishable.stats import (…)` block**, in the
      block's existing alphabetical order.

- [ ] **Step 3: replace `test_collapse_drops_a_bool_column_rather_than_averaging_it` with Fixture C.**
      One unit, two repeats, recording `{"flag": True}` and `{"flag": False}`. Assert
      `collapsed["p0"]["flag"] is None` — **the key present and the value `None`, two assertions, not
      one** — and, through a real run, that `W-STATS-REPEATS-DISAGREE` names `flag` **on stdout**.
      `values[0]` is `True`, so a mutant carrying the first value gives `True`, which `is None` separates.
      **This is a CORRECT move, not a weakening, and the replacement says so in its own docstring**: the
      old assertion (`"flag" not in collapsed.get("p0", {})`) pinned the behaviour that **is** the defect,
      and it passed today because `p0` was not in `collapsed` at all — so its name described a column
      drop while its subject was a unit drop. **Keep the old test's name discoverable**: the new test's
      docstring names it, so a reader grepping for it lands here.

- [ ] **Step 4: Fixture D — the control Decision 3 rests on, and its harder second arm.**
      *Arm 1:* two repeats **both** recording `{"valid": None}`. Assert the cell is `None` **and that
      `W-STATS-REPEATS-DISAGREE` does not fire** — asserted on the run's **stdout**, not on stderr and
      not on an exit code. **The stream was measured, not assumed:** every shipped assertion on a run
      finding reads stdout (`tests/test_cli.py` carries two `assert "W-STATS-STRATUM-SHADOWED" in
      doc["stdout"]` lines and `tests/test_report.py` a third — **grep for them and quote one**). An
      absence asserted on stderr would pass whether the warning fired or not, which would make exactly
      this fixture unable to fail.
      *Arm 2, and it is the one Decision 3 is actually about:* one repeat recording `{"valid": None}` and
      another recording `{"valid": True}` — a genuine disagreement whose collapsed cell is `None`,
      **bit-identical to arm 1's**. Assert the cell is `None` and that the warning **does** fire. The two
      arms differ **only in the rows**, never in the collapsed value, so a rule answering from the cell
      gives one answer to both and must fail one of them.

- [ ] **Step 5: Fixture L — the mixed column (§ Corrections 5).** One unit, two repeats, recording
      `{"score": 4.0}` and `{"score": "n/a"}`. Assert **three** things: the cell is `4.0` (today's
      arithmetic, **unmoved** — the numeric subset's mean); the column **keeps** its metric block in
      `aggregated` through a real run; and `W-STATS-REPEATS-DISAGREE` names `score`.
      **This is the fixture that separates the prescribed rule from the plausible wrong one.** Under
      *mixed → `None`* the cell is `None`, and measured at `ee8085e` **one `None` cell costs the whole
      column its metric block for every unit** (probe `p3`) — a published column silently deleted, which
      no decision argues for. Under the prescribed rule the value is unmoved and the disclosure is the
      warning. **A second arm as the can-fail control:** the same column with **both** repeats numeric
      (`4.0` and `6.0`) collapses to `5.0` and draws **no** warning, asserted on stdout.

- [ ] **Step 6: the measurements interaction, OBSERVED rather than reasoned.** The design's § What could
      not be measured says a `measurements.parquet` from a real run was never inspected and *"the plan
      should build one."* **This plan built it** (§ Corrections 13) and the finding is that the two levels
      **do not interact**. Pin it: a run declaring `data.units.measurements: {by: read_id, collapse:
      first}` whose step records `{"score": …, "valid": True, "tag": "a"|"b"}` per measurement. Assert
      `measurements.parquet` holds both measurement rows with both `tag` values; `units.parquet` holds
      `tag: 'a'` (the declared collapse's answer); the collapsed table's `tag` is `'a'`; and **no**
      `W-STATS-REPEATS-DISAGREE` fires — the declared collapse ran **inside** each execution, so the
      repeat rule saw a constant. All four literals were observed at `ee8085e`. **State in the docstring
      why a numeric declared rule cannot reach this path**: `_collapse_measurements` calls `rule_for` then
      `coerce_for_rule`, which refuses a non-numeric value under a numeric rule before the repeat rule is
      reached — so only `first` and `mode` get here. **Grep
      `tests/test_artifacts.py::test_a_numeric_rule_coerces_a_recorded_string_before_applying` and cite
      it** rather than restating the mechanism.

- [ ] **Step 7: the mutations — three.**
      (i) Carry `values[0]` instead of `None` for a disagreeing non-numeric column. **Fixture C's
      `is None` must FAIL.** *Why the branches differ:* `values[0]` is `True` there, by construction.
      (ii) Make `repeats_disagreeing` answer from the collapsed cell (`value is None`) rather than from
      the rows. **Fixture D must FAIL** — arm 1 gains a warning it must not have. *Why the branches
      differ:* a recorded `None` is indistinguishable from a disagreement at the cell, which is the whole
      ground for Decision 3, and the two arms are bit-identical in `collapsed`.
      (iii) Delete the `W-STATS-REPEATS-DISAGREE` call site. **Fixture C's warning assertion must FAIL**,
      on **stdout**, with the column name in it. *Why the branches differ:* the message names `flag`, and
      nothing else in that run's output does — **checked against the run's other diagnostics rather than
      assumed**, which is the check `assert "draft" in out` failing on `draft_run` exists to force.
      **A fourth is named REJECTED rather than blind:** dropping the `all numeric → False` early return
      in `_repeats_disagree` would make every unequal numeric column "disagree" — caught by Fixture L's
      second arm and by arm A's `results` snapshot, which carries a numeric column with real variance.
      Run it; it is not blind, and naming it as such would be wrong.

- [ ] **Step 8: run** the four commands. **Delta:** Fixtures C, D, L and the measurements pin added; **one
      test replaced** (`test_collapse_drops_a_bool_column_rather_than_averaging_it`), named in the report.
      **Commit:** `H5b task 5: a disagreeing non-numeric column collapses to None and says so, from the
      rows`.

**What this task must NOT touch.** Pin arms A, B, C, D, E — **arm B in particular**: Fixture A has no
column that disagrees across repeats, so this task cannot reach it, and an edit here is a finding.
`repeat_spread`'s body (its `std: 0.0` filing is unassigned and stays). `units.apply_rule`,
`units.rule_for`, `units.coerce_for_rule` — cited, never called, never refactored.

---


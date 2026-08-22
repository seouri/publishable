## Task 4: the collapse carries every recorded value and admits every unit it was handed

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**THE BEHAVIOUR CHANGE. Surface: a direct call and a real `run`, both.** Design Decisions 1, 5 and 6.
This task also **carries Fixtures E, H and K and the pins the scoping put in tasks 10 and 11** — a live
overruling from the design's § What each change makes reachable, restated here because *a ruling that
overrules a brief has to reach the brief.*

**Files:**
- Source: `src/publishable/stats.py`, `src/publishable/cli.py` (annotations only)
- Test: `tests/test_stats.py`, `tests/test_cli.py`

- [ ] **Step 1: extract the repeat walk once, so it has one implementation and two readers.** In
      `stats.py`, lift `collapse_repeats`' gathering into a module-private helper and leave
      `collapse_repeats` as its reader. **This is what lets task 5's `repeats_disagreeing` ask the rows
      the same question without a second walk that can drift** — and it is why the design's *"plus the
      unit keys"* parameter is unnecessary (§ Corrections 3).

```python
def _gather_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None,
) -> dict[str, dict[str, list[Any]]]:
    """Every value each admitted unit recorded for each column, across the repeats
    it was handed — raw, uncoerced, in the order `sorted(candidates)` fixes.

    One walk, two readers: `collapse_repeats` turns it into one row per unit, and
    `repeats_disagreeing` asks it which columns disagreed. A second walk would be a
    second implementation of the membership rule, and the two would drift.
    """
    recording = [
        r
        for r in results
        if r.execution.step_name == step_name
        and r.execution.scope == "repeat"
        and r.execution.condition_index == condition_index
    ]
    if not recording:
        return {}
    rows_by_label: dict[str, list[dict[str, Any]]] = {}
    recorded_by_label: dict[str, set[str]] = {}
    for r in recording:
        label = r.execution.repeat_label or ""
        rows_by_label.setdefault(label, []).extend(r.rows)
        recorded_by_label.setdefault(label, set()).update(r.recorded)
    labels = list(recorded_by_label)
    candidates: set[str] = set()
    for keys in recorded_by_label.values():
        candidates |= keys

    gathered: dict[str, dict[str, list[Any]]] = {}
    for key in sorted(candidates):
        mine = handed_to(key, labels, fold_members)
        if not mine or any(key not in recorded_by_label[lb] for lb in mine):
            continue
        # The unit passed the membership gate, so it IS a unit. It gets a row even
        # when every value it recorded is non-numeric, and even when it recorded no
        # column at all — `io.record(key, {})` settles a unit and records nothing,
        # which is reachable (measured). `runner.attrition` already counts such a
        # unit `completed`; this was the one place in the program that did not.
        gathered.setdefault(key, {})
        for lb in mine:
            for row in rows_by_label[lb]:
                if row["unit"] != key:
                    continue
                for column, value in row.items():
                    # `unit` is the key, not a measurement. `cli._attributed` is what
                    # puts the key column back for a bootstrap draw that duplicates
                    # units; it is never a column of `collapsed`.
                    if column == "unit":
                        continue
                    gathered[key].setdefault(column, []).append(value)
    return gathered
```

      **Preserve every comment the original loop carried**, in particular the two whose reasons are still
      true: `sorted(candidates)` is load-bearing because `summarize_step` derives a metric's column order
      from this dict and `order: randomized` decides encounter order; and the accumulation rather than a
      comprehension is what makes two executions sharing one repeat label merge rather than overwrite.
      **Delete nothing you cannot argue is false.**

- [ ] **Step 2: `collapse_repeats` reads the walk and averages what it can.**

```python
def collapse_repeats(
    results: "list[ExecutionResult]",
    step_name: str,
    condition_index: int,
    fold_members: dict[str, frozenset[str]] | None = None,
) -> dict[str, dict[str, Any]]:
    gathered = _gather_repeats(results, step_name, condition_index, fold_members)
    return {
        key: {col: _across_repeats(vals) for col, vals in cols.items()}
        for key, cols in gathered.items()
    }
```

      and the rule itself, in `stats.py` beside `_is_numeric`:

```python
def _across_repeats(values: list[Any]) -> Any:
    """One unit's values for one column, collapsed across the repeats it was handed.

    Three cases, and the third is the one that keeps a published number where it is.

    - Every value a real number: the mean, which is what this function has always
      done and the only case a purely numeric run reaches.
    - SOME values numbers: the mean of those, which is EXACTLY today's arithmetic —
      today's inner loop skipped the non-numeric ones and averaged the rest. Moving
      this to `None` would cost the whole column its metric block, for every unit,
      because `summarize_step` requires *all* carried values numeric (measured). That
      is a published column deleted, which no decision here argues for; the
      disagreement is disclosed instead, by `repeats_disagreeing`.
    - NO value a number: the value itself when the repeats agreed, `None` when they
      did not. `first` and `mode` are rules the user declared for `measurements` and
      never for repeats, and both are order-dependent here — `_gather_repeats`
      iterates in execution order, which `order: randomized` shuffles — so picking
      one would put the shuffle into a published column, the exact fault
      `sorted(candidates)` exists to keep out.

    `None` rather than omitting the key: omission would remove the column from
    `summarize_step`'s `columns` list when every unit disagreed, and `columns` is
    what the derived-key collision check reads — so omission reopens the silent
    coexistence defect through a second door. `_is_numeric(None)` is `False`, so a
    `None` cell keeps the column visible and unpublishable. Measured: the collision
    fires for a column whose every cell is `None`.

    `reference.md` § What isn't a repeat's *"Attributes constant within a key
    collapse to that value with no rule needed"* is the rule reused here, and
    `units.apply_rule` is the sibling that implements it for `measurements`. It is
    deliberately NOT called: it takes a rule name, every name it accepts returns a
    value on disagreement, and there is no declared rule for repeats to pass it.
    """
    numeric = [float(v) for v in values if _is_numeric(v)]
    if numeric:
        return sum(numeric) / len(numeric)
    if _repeats_disagree(values):
        return None
    return values[0]


def _repeats_disagree(values: list[Any]) -> bool:
    """Whether a unit's repeats disagreed about a non-numeric column.

    Pairwise against the first value, on `(is-it-a-number, the value)` rather than on
    the value alone: `True == 1.0` in Python, so a column recorded as `True` in one
    repeat and `1.0` in another would read as constant and collapse to whichever
    arrived first — order-dependent, which is what this rule refuses. Compared
    pairwise rather than through a set, so nothing here depends on a recorded value
    being hashable.

    All-numeric columns are excluded: unequal numbers are what averaging is for, and
    reporting them as a disagreement would fire on every honest run.
    """
    if all(_is_numeric(v) for v in values):
        return False
    first = values[0]
    return any((_is_numeric(v), v) != (_is_numeric(first), first) for v in values)
```

      **`_repeats_disagree` is a `stats.py` private and task 5's public `repeats_disagreeing` is what
      reads it.** Writing the predicate here rather than in `units.py` is deliberate: a shared helper
      would couple the measurements rule to the repeats rule, and a future edit to one would silently
      move the other.

- [ ] **Step 3: sweep the 20 annotation sites.** `grep -rn 'dict\[str, dict\[str, float\]\]'
      src/publishable/*.py | wc -l` → **20** at `ee8085e` (16 `stats.py`, 4 `cli.py`), re-run and report
      it. Each becomes `dict[str, dict[str, Any]]`. **Filter the file list, never the output.** The
      widened type is `Any` and **not** a `Scalar` union, because every arithmetic consumer re-narrows at
      runtime through `_is_numeric`, which mypy cannot see: a union would trade twenty annotations for a
      dozen `cast`s asserting the same runtime fact twice. `uv run mypy` is this step's check — **an
      annotation change has no observable behaviour, so a mutation for it is one whose two branches
      cannot differ, and it is named blind here rather than invented** (its replacement is task 7's
      mutation, which pins the runtime narrowing the annotation stopped expressing).

- [ ] **Step 4: Fixture A, and the arm B flip.** Drive `summarize_step` over a `collapsed` produced by
      calling the **new** `collapse_repeats` on `_result`-built executions (`recorded` = **unit keys**),
      and assert the AFTER column of task 1's arm B — the seven moved literals **and** the five that must
      not move. **Then edit arm B in `tests/`, flipping exactly those seven and nothing else.** You are
      that arm's **sole authorized editor**. Arms A, C, D and E: **do not touch** (arm E is yours in
      step 5). If arm A fails, stop — a numeric-only run moved and that is a defect, not a pin to edit.

- [ ] **Step 5: the arm E flip, through a real command.** Run the console script on arm E's project and
      read `run.yaml` **key by key** against arm E's AFTER column. Flip arm E's literals. **`score`'s
      `ci95` and `n_paired` must not move and `score.ci95_corrected` must**; if the corrected interval
      does not move, that is a **finding** — the correction family did not see the widening — and it is
      reported rather than smoothed.

- [ ] **Step 6: Fixture B — the scaffold's own run, end to end.** With `STARTER_STEP` unmodified and six
      units: `aggregated.step01_summarize_units == {}` **before and after** (Decision 12 — `generic`
      inherits `BaseTemplate.aggregate` returning `{}`, so the scaffold's symptom does not move), and,
      with a project-local template whose `aggregate` returns
      `{"n_present": float(len([r for r in units if r.get("present")]))}`, the value is **`6.0`** and no
      `W-STATS-AGGREGATE-FAILED` appears **on stdout** — the stream every shipped assertion on a run
      finding reads. Today the same project publishes `0.0` at exit 0.
      **The control that can fail:** a template reading `units.absent_column` still earns
      `E-STEP-COLUMN-UNKNOWN` under `W-STATS-AGGREGATE-FAILED`. **Without it this fixture asserts only
      absences and would pass identically if nothing ran.**

- [ ] **Step 7: Fixture E — the collision, driven from the collapse's own output.** `collapse_repeats`
      over executions recording `{"score": float(i), "r": True}`, its return fed to
      `summarize_step(…, derived={"r": 1.0})`, asserting `E-STEP-KEY-COLLISION`. **This is the pin, not
      the rewrite** — task 10 owns the shipped test's fixture replacement and the § Errors assertion.
      **Second arm, and it is the one that pins Decision 2's `None` choice:** a colliding column that
      **disagrees** across repeats, so its cell is `None` and the collision must still fire. Measured at
      `ee8085e`: it does.
      **Plus the end-to-end arm:** a real run whose template returns a colliding key publishes no `r`
      metric, warns, and **writes its `run.yaml`** — the containment is already right and is not touched.

- [ ] **Step 8: Fixture H — the stratum's empty level.** A run with `report_by` on an attribute one of
      whose levels contains **only** units whose every recorded value is non-numeric, and a template
      returning one derived metric. Assert that level is **absent** from the `by` block while the other
      level is **present**. **The presence half is what stops this from being an absence-only control.**

- [ ] **Step 9: Fixture K — the fold path.** Re-assert the existing `fold_members` collapse fixture over
      a roster where one fold's units record only a bool: each such unit is admitted **within its own
      fold**, and `handed_to`'s intersection is unchanged. **Grep for the existing fixture by name and
      extend it rather than writing a second one**; report what you grepped. The claim is that this task
      changed what the function **returns** and nothing about how it **intersects** — H3c-3's contact
      point, pinned rather than named.

- [ ] **Step 10: Fixture M — `repeat_spread` under the widened `keys`.** `cli.py` passes
      `keys=set(collapsed)`, which goes 4 → 6 in Fixture A's shape while the column's own `n` stays 4.
      **The gate that holds is `_repeat_spread_entries`' own `_is_numeric(row[column])` filter, and a
      fixture whose repeats record identical scores cannot see whether it held** — `std: 0.0` agrees
      with the bug. So: two repeats recording `score` **2.0 apart**, four units carrying it, two units
      carrying only a bool. Measured at `ee8085e` (this plan's probe `p5`): `{'std': 1.0, 'n': 2, 'kind':
      'seed'}` under the narrow keys and **identical** under the wide ones. Assert both.

- [ ] **Step 11: run the whole suite and REPORT THE MOVED TESTS BY NAME.** The scoping measured *"exactly
      two tests move"* under a shape that carried values and admitted units but had **no across-repeats
      rule and no mixed-column rule** — that figure is dated to `5ee3a0c` and to that shape, and it is
      **not** a prediction about this branch (§ Corrections 11). Expect
      `tests/test_stats.py::test_collapse_drops_a_bool_column_rather_than_averaging_it` (task 5 owns its
      replacement) and
      `::test_a_derived_key_colliding_with_a_dropped_non_numeric_column_is_refused` (task 10 owns its
      fixture). **Any third is a finding**: name it, say whether it pins the defect or a real guarantee,
      and do not edit a test whose guarantee is real without saying so in the report.
      **Do not "fix" `test_collapse_drops_a_bool_column_rather_than_averaging_it` here** — it asserts
      `"flag" not in collapsed.get("p0", {})` and passes today because `p0` is not in `collapsed` **at
      all** (§ Corrections 12), so it is a pin of the unit drop wearing the name of a column drop. Task 5
      replaces it, and this task's suite run may leave it failing between the two commits **only if that
      is stated in the report** — otherwise mark it `xfail` with task 5 named as its remover.

- [ ] **Step 12: the mutations — four, each with the assertion that catches it and two branches that can
      differ.**
      (i) Restore `or not _is_numeric(value)` in `_gather_repeats`' inner loop. **Fixture A's
      `n_valid.value` (`6.0` vs `0.0`) and Fixture B's `n_present` (`6.0` vs `0.0`) must FAIL.** *Why
      the branches differ:* measured — that exact input yields `{}` for a bool-only roster and drops two
      units in Fixture A's.
      (ii) Admit only units with at least one **numeric** value (keep the carriage, drop the admission):
      `if not gathered.get(key): gathered.pop(key, None)`-shaped, or `gathered.setdefault` moved back
      inside the value loop. **Fixture A's `n_rows.value` (`6.0` vs `4.0`) and
      `mean_score.n.completed` must FAIL.** *Why the branches differ:* the two rules differ **exactly**
      on units `u4`/`u5`, which carry a value and no number — the case a single-arm fixture would miss,
      and the reason Fixture A has both kinds of unit.
      (iii) Replace `cli.py`'s second empty-level gate (`if set(level_summary) - set(level_derived or
      {}):`) with `if True:`. **Fixture H's absent-level assertion must FAIL.** *Why the branches
      differ:* measured at `5ee3a0c` — this mutation leaves the **whole suite** green today, and it stops
      being blind at this task. **That is the point of pinning it here rather than in batch 3.**
      (iv) In Fixture E's second arm, make `_across_repeats` omit the key instead of returning `None` for
      a disagreeing non-numeric column. **The collision assertion must FAIL** — omission removes the
      column from `columns`, so the check stops seeing it. *Why the branches differ:* measured — the
      collision fires for an all-`None` column and cannot fire for an absent one.
      **Named blind in advance, with replacements:** the annotation sweep (step 3), replaced by task 7's
      mutation; and the docstring/comment edits in steps 1–2, replaced by the B2 review reading each
      comment against the code it sits on. *If a comment says this cannot happen, make it happen.*

- [ ] **Step 13: run** the four commands. **Delta:** Fixtures A, B, E, H, K, M added; `mypy` still 52
      source files; `ruff format --check` still 93. **Commit:** `H5b task 4: the collapse carries every
      recorded value and admits every unit it was handed`.

**What this task must NOT touch.** `summarize_step`'s body (task 6 deletes one docstring clause and
nothing else); `cli.py`'s contrast arms (task 7); `cli.py`'s `by` gate (task 9); `STARTER_STEP`
(Decision 12 refuses it); `paired_keys` and `unpaired_keys` (Decision 6 rules that a unit with no
numeric column **does** enter the intersection, and the per-column arms already narrow — no code
change); pin arms A, C and D (**no authorized editor**).

---


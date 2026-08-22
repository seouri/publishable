# Batch 6 — tasks 7, 8 — the recorded-side guards, a control review

Commits: `44399fd` (task 7 — `io.record`'s plain branch refuses `measurement`),
`3b58442` (task 8 — `finalize`'s `columns` list deduped, residual stated).

Suite: **2875 → 2879** (2875 passed, 1 skipped, 2 xfailed baseline → 2879 passed, 1
skipped, 2 xfailed). Delta is +4 tests: task 7 adds Fixture M's three arms, task 8 adds
Fixture D. `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all
clean on both commits.

## Task 7 — the plain branch now refuses `measurement`; the `measurement=` branch unchanged

`StepIO.record`'s plain branch (no `measurement=`) gained the mirror of the
`measurement=` branch's own guard:

```python
if "measurement" in values:
    raise ContractError(
        "`measurement` collides with the measurement column: a recorded "
        "column may not be named `measurement`",
        code="E-STEP-KEY-COLLISION",
    )
```

placed after the existing `unit` guard, before the declared-attribute collision check,
unconditional (not gated on `data.units.measurements` being declared — the comment
states why: gating would make one line of step code legal or illegal depending on a
config block elsewhere).

**Fixture M, three arms** (`tests/test_artifacts.py`):
- Arm 1 — `test_fixture_m_plain_record_refuses_a_measurement_column`: plain
  `io.record("p0", {"measurement": "HIJACK"})` → `E-STEP-KEY-COLLISION`. New behaviour.
- Arm 2 — `test_fixture_m_measurement_branch_still_refuses_the_same_key`: the same key
  through `measurement=` → the same code. **Was already passing before this task**;
  kept unedited so the test asserts the symmetry, not just the new branch in isolation.
- Arm 3 (control) — `test_fixture_m_a_plural_measurements_column_still_writes`: a plain
  record naming `measurements` (plural) still writes and round-trips through
  `units.parquet`.

**Mutation, run and reverted.** Replaced the plain branch's guard with
`if any("measurement" in k for k in values):` (a substring test over the keys).
Ran `uv run pytest tests/test_artifacts.py -k "fixture_m"`: arms 1 and 2 still PASS,
**arm 3 FAILS** — `measurements` (plural) now raises `E-STEP-KEY-COLLISION` because the
substring test matches it too. A property-preserving arm would need a guard that only
ever matches the exact string `measurement`; the mutant's two branches differ from the
original precisely on the plural control, which is why arm 3 exists at all. Reverted by
editing the line back (not `git checkout`), re-ran the same `-k` selection to confirm
the revert (2 passed → back to 3 passed), then re-ran the full suite (below) to confirm
no other test moved.

**§ Errors:** `reference.md`'s existing `E-STEP-KEY-COLLISION` row (§ Errors core
raises) already names "a recorded column named `unit`, or one named `measurement`"
without tying either to which branch raises it — it was already true of the plain
branch's new site with no change needed, since it was already true of the
`measurement=` branch's pre-existing site. No row required widening.

## Task 8 — what the dedupe fixes, and what it leaves open

`finalize`'s inline `columns = ["unit", *attribute_names, *recorded]` became a call to
a new module-level helper, `_finalize_columns(attribute_names, recorded)`, which builds
the same three-part list but deduped by name, first-seen order preserved. The
docstring states, in the words the plan's correction 5 requires: **the dedupe fixes the
LIST, not the VALUE.** `finalize`'s attribute-merge loop still overwrites
`merged["unit"]` with a `Unit`'s own `unit`-named attribute value when one is present,
so a directly constructed `Unit` (reachable because `Unit` is on § The importable
surface, and task 5's `E-UNITS-ATTR-COLUMN` refusal only closes this for a *config*,
not for a direct caller) still publishes the attribute's value in the unit-key column —
the docstring says this and routes it by name (task 12's residual filing) rather than
building a guard, per the brief.

**Fixture D** (`test_fixture_d_finalize_columns_is_deduped_by_name`): I chose the
**module-level-helper** route rather than a parquet-column-order assertion, because I
measured that the file cannot distinguish the two: `finalize`'s per-row dict
comprehension already collapses a duplicate key (a Python dict cannot hold `"unit"`
twice), so the written parquet's column order is byte-for-byte identical whether or not
the list itself is deduped — an assertion on the file passes before and after either
way, which is exactly what correction 5 and the brief warn against. The fixture instead
monkeypatches `artifacts._finalize_columns` with a spy that delegates to the real
function and records both its call arguments and its return value, then drives it
through a real `io.finalize()` call (a `UnitList` built directly with a `Unit`
carrying an attribute named `unit`). It asserts two things: the helper was called
exactly once with `attribute_names == ["unit", "site"]`, `recorded == ["score"]` (the
call-site half), and the returned list is `["unit", "site", "score"]` — `"unit"` exactly
once (the list half). I ran both possible regressions as mutations, not just the one
the brief names, because either alone risks being a mutation applied to a proxy:
- **Mutation, helper body:** replaced the helper's dedupe with a bare
  `return ["unit", *attribute_names, *recorded]`. Ran
  `uv run pytest tests/test_artifacts.py -k fixture_d`: **FAILS** —
  `columns.count("unit") == 1` sees `2`, list is
  `['unit', 'unit', 'site', 'score']`. This is the mutation the brief prescribes
  ("delete the dedupe"). Reverted by editing back; re-ran to confirm PASS.
- **Mutation, call site:** reverted `finalize`'s own line to the old inline
  `columns = ["unit", *attribute_names, *recorded]`, bypassing the helper entirely
  while leaving the helper's dedupe intact. Ran the same selection: **FAILS** —
  `len(calls) == 1` sees `0`, because the spy is never invoked. This is the
  "mutation applied to a proxy" case the brief calls out by name: a test that only
  exercised `_finalize_columns` directly (never through `finalize`) would have missed
  this branch entirely. Reverted by editing back; re-ran to confirm PASS.

A property-preserving arm for the first mutation is any implementation of the helper
that still returns a list with no repeated name; for the second, any call site that
still routes through `_finalize_columns` (or an equivalent dedupe) rather than
reassembling the raw concatenation inline.

**Task 13's arm A and arm B stay green** — task 8 moves no byte, confirmed by
re-running `tests/test_cli.py::test_h5a_arm_a_a_real_runs_units_parquet_column_order_values_and_types`
and `tests/test_artifacts.py::test_h5a_arm_b1_the_csv_golden_bytes_never_move_in_this_slice` /
`test_h5a_arm_b2_the_parquet_golden_sha256_is_a_tripwire` after task 8's commit: all
three pass.

**The `by` column still survives both `record` branches**, confirmed by re-running
`test_a_plain_recorded_by_column_survives_into_units_parquet` and
`test_a_measured_by_column_survives_the_collapse_into_units_parquet` after both tasks:
both pass. Neither task's guard touches `by` — task 7's new guard checks only the
literal string `"measurement"`, and `RESERVED_COLUMNS` (the constant Decision 3/
correction 1 restrict to one reader) is not consulted by either task.

## Brief clauses dropped

None. Both briefs' steps were followed as written; task 8's Fixture D took the
helper-extraction option the brief offered as an alternative to a file-based
assertion (the brief let me choose), and the report states why the file-based option
was measured to be unusable here.

## Full suite, both commits landed

`uv run pytest -q` → **2879 passed, 1 skipped, 2 xfailed** (186s), up from the batch's
starting 2875/1/2 by the expected +4 (three Fixture M arms, one Fixture D test).
`uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` all clean.

## Concerns

None found — no disagreement between either brief and the shipped code, and every
prescribed and self-added mutation behaved as predicted (FAIL under the mutant, PASS
after revert, confirmed by re-running rather than by reading `git status`). The one
residual this batch deliberately leaves open — `finalize`'s attribute merge overwriting
`merged["unit"]` for a directly constructed `Unit` — is task 12's to file; task 8's
docstring names it and does not close it, per the brief's explicit instruction not to
build a fifth stoppage.

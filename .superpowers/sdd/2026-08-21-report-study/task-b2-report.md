# Tasks 1 and 2 (batch 2): `BaseReport`/`Section`, and `ReportIO` — report

Branch `h8c-report-study`. Commits `6b0bd04` (H8c task 1) and `56e6dc1` (H8c task 2), both mine.
Run in the foreground throughout, per the batch's own instruction — no monitor, no background
wait, no stall.

## Task 1: `BaseReport` and a frozen `Section`

`src/publishable/report.py` (new): `Section` — a frozen dataclass, `title: str` and
`body: str | Mapping[str, Any]` — and `BaseReport`, with `section(self, title, *, body)`
constructing one and `sections(self, run, io)` a generator yielding nothing (`yield from ()`).
`format` has no class attribute at all — checked directly (`not hasattr`, `"format" not in
vars(...)`), not merely undeclared by omission. `publishable/__init__.py` imports and exports
`BaseReport` in sorted position. `tests/test_report.py` (new, 8 tests): frozen-ness (assignment to
either field raises `dataclasses.FrozenInstanceError`), a mapping `body` is accepted and NOT
deep-frozen (mutating the dict after construction is visible through `section.body`, exactly what
the docstring claims and no more), `self.section` construction, `sections` is a real generator
that yields nothing from the base, `yield from super().sections(...)` composition (an override's
own sections still arrive, in order, alongside the base's), an override that omits `yield from`
gets none of the standard sections, and the no-`format`-attribute check.

**Docs:** `docs/reference.md` § The importable surface — `BaseReport` row's `Status` cell flips
`not yet built` → `built`. § What you define — `BaseReport` row's `Core's` cell gains `self.section`
and `__init__` (correction 15). `docs/superpowers/spec-defects.md` — the entry *"~~The importable
surface names five things `publishable/__init__.py` does not export~~"* is now struck to `— CLOSED`
(previously `— MOSTLY CLOSED; only BaseReport remains`), with an appended closure paragraph dated
2026-08-21 rather than any rewrite of the existing body — the entry's history stays exactly as
written.

### Arm B's diff, and its demonstration

The whole edit to `tests/test_cli.py`:

```diff
@@ test_h8c_arm_b_publishable_all_is_a_full_sorted_list @@
         "ArtifactExistsError",
         "BaseExperiment",
+        "BaseReport",
         "BaseStep",
         "BaseTemplate",
         "ContractError",
@@
     ]
     assert list(publishable.__all__) == sorted(publishable.__all__)
-    assert "BaseReport" not in publishable.__all__
```

One name appended in sorted position (`BaseExperiment` < `BaseReport` < `BaseStep` alphabetically:
`E` < `R` < `S` at that character), and the now-false absence assertion deleted. Nothing else in
the test changed — confirmed by `git diff tests/test_cli.py`, reproduced above verbatim. The test
passes: `uv run pytest -q tests/test_cli.py::test_h8c_arm_b_publishable_all_is_a_full_sorted_list`
→ 1 passed.

### Mutation M14 — run, and what was carried forward

`Section`'s `@dataclass(frozen=True)` → `@dataclass(frozen=False)`. Ran
`tests/test_report.py` at file scope first: **1 failed** —
`test_section_is_frozen_and_carries_title_and_body` (`DID NOT RAISE FrozenInstanceError`), 7
passed — none of the other 7 tests move, since none of them depends on frozen-ness. Reverted by
editing the file back (`sed` restoring `frozen=True`); `diff` against a pre-mutation copy showed
**byte-identical**, and a re-run of `tests/test_report.py` returned to 8 passed.

The render-level arm — an override reaching into a *standard* section's mapping `body` and
mutating a number before yielding it, failing loudly under `frozen=True` and rendering the
mutated figure without it — could not be written here: no standard section with a mapping body
exists until task 5 builds one. Per the brief's own instruction, that arm is carried forward by
name to task 5's brief rather than silently dropped from the chain (the H8a/H8b routing failure
this batch was warned about). What was pinned here instead is the frozen-ness assertion in
isolation, above.

## Task 2: `ReportIO`, and the traversal it shares with `StepIO`

`src/publishable/artifacts.py`: extracted two module-level functions ahead of `class StepIO`:

- `_nest_repeat_segment(base, target, repeat, repeats)` — the repeat-label segment rule, byte-for-
  byte what `StepIO._nest_repeat`'s body used to be, now taking `repeats` as a parameter instead
  of reading `self._repeats`.
- `_resolve_condition_step_dir(*, run_dir, conditions, step_scopes, repeats, condition, step,
  repeat)` — the read half of `read_condition`'s traversal (after its `_summary_only` gate),
  calling `_nest_repeat_segment`.
- `derive_step_scopes_and_repeats(execution)` — the derivation § Corrections correction 2 says
  `lineage.resolve_step` does NOT perform: three-way split on `execution["shared"]` → `"run"`,
  `execution["summary"]` → `"summary"`, a `conditions[].steps[step]` entry holding `"status"`
  directly → `"condition"`, one whose value is a mapping of repeat labels → `"repeat"` (collecting
  those labels, first-seen order, deduped across conditions).

`StepIO.read_condition` and `StepIO._nest_repeat` were rewritten to call these — the method bodies
are now thin wrappers, not copies. `StepIO` does not subclass `ReportIO` and `ReportIO` does not
subclass `StepIO`.

`ReportIO` (new class, between `StepIO` and `ResolverIO`): constructor takes `run_dir`, `input_dir`,
`conditions`, `repeats`, `step_scopes` — already-derived, exactly as `StepIO`'s constructor takes
them for a `summary` step; `ReportIO` does no record-reading itself. **What it exposes:**
`conditions` and `repeats` as plain properties (no `_summary_only` gate — a report has no scope to
be narrower than); `read_condition(condition, step, name, repeat=None)`, same signature, same
refusals (`E-STEP-READ-REPEAT-REQUIRED`, `E-STEP-READ-CONDITION-UNKNOWN`), same containment check
(`E-ARTIFACT-NAME`) as `StepIO`'s; `read_input(relpath)`. **What it deliberately does not expose:**
`write`, `record`, `append`, `skip`, `finalize` — asserted absent by name
(`test_report_io_has_no_write_half`), paired with the members above actually working, per the
brief's "control asserting only absences run backwards" instruction.

`tests/test_artifacts.py` (+13 tests): three direct tests of `derive_step_scopes_and_repeats`
against hand-built `execution` dicts (the four-way split; the measured one-repeat case where the
entry still nests a label while the eventual directory collapses; label dedup across two
conditions sharing a repeat-scoped step); ten `ReportIO` tests mirroring `StepIO`'s existing
`read_condition` coverage one-for-one (null-label condition, the `io.conditions`-element pattern,
a named repeat among several, the one-repeat collapse, the repeat-required refusal, the unresolved-
index refusal, name-containment refusal, `read_input`, and the withheld-half absence check).

`tests/test_report.py` (+1 test): `test_report_io_resolves_the_same_artifacts_at_three_repeats_and_at_one`
— a real project (a condition-scoped `step02_fit` writing `model.json`, the generated repeat-scoped
starter writing `units.parquet`), run twice (3 repeats, 1 repeat), with `ReportIO` built from
nothing but the finished `run.yaml` (`derive_step_scopes_and_repeats` over `execution`,
`conditions` from `results.conditions`, `input_dir` from `config.data.input_dir`, `run_dir` the
directory's own path) and queried directly from the test — never through a step — reading the
same values at both repeat counts.

### The load-bearing mutation (M16)

`_nest_repeat_segment`: `if target == "repeat" and repeat and len(repeats) > 1:` →
`if target == "repeat" and repeat:` (dropped the `> 1` guard). Ran `tests/test_artifacts.py
tests/test_report.py` at file scope: **4 failed**, 139 passed —
`test_read_condition_collapses_the_repeat_directory_when_the_run_has_only_one` (`StepIO`,
pre-existing, direct-call), `test_h8c_arm_c_read_condition_resolves_at_three_repeats_and_at_one`
(task 17's guard pin, arm C — `StepIO` via a real `summary` step), `test_report_io_read_condition_
collapses_the_repeat_directory_at_one_repeat` (`ReportIO`, direct-call, mine), and
`test_report_io_resolves_the_same_artifacts_at_three_repeats_and_at_one` (`ReportIO`, real-run,
mine) — all four failing at the one-repeat case only, with the same shape (a read resolving to
`.../seed1/step/name` when the real directory never nested that segment). That is one `StepIO`
test and one `ReportIO` test failing at minimum (in fact two of each), which is the whole of
Decision 4's anti-drift claim: the mutation could not fail only the report side, so the extraction
shares rather than copies. Reverted by editing the line back; `diff` against a pre-mutation copy
of the file showed **byte-identical**. Re-ran `tests/test_artifacts.py tests/test_report.py`:
143 passed. Confirmed task 17's arm C passed in isolation both before mutating and after
reverting.

## Gates, confirmed by running

- After task 1: `uv run mypy` → 50 source files. `uv run ruff format .` → 1 file reformatted, 89
  unchanged (→ 90 formatted). `uv run ruff check .` → all checks passed. `uv run pytest` →
  2651 passed, 1 skipped, 2 xfailed (baseline 2643 + 8 new).
- After task 2: `uv run mypy` → 50 (unchanged — no new source file, only `artifacts.py` grew).
  `uv run ruff format --check .` → 90 (unchanged). `uv run ruff check .` → all checks passed.
  `uv run pytest` → 2665 passed, 1 skipped, 2 xfailed (2651 + 14 new: 3 derivation tests + 10
  `ReportIO` direct tests in `test_artifacts.py`, 1 real-run `ReportIO` test in `test_report.py`).
  Full suite re-confirmed clean and at 2665/1/2 after the M16 mutation was reverted.

## What was grepped, and its scope

`grep -n "ReportIO" src/ tests/ docs/` before starting task 2, scoped to confirm nothing under
`src/`/`tests/` referenced the name yet (docs/superpowers's design and plan documents were the
only hits, as expected — no code or test pre-existed to build against). `grep -n "@staticmethod"
src/publishable/artifacts.py` to confirm `StepIO._read`/`StepIO._contained` are stateless
staticmethods before having `ReportIO` call them directly (not through inheritance) — both are.

## Concerns

- `ReportIO`'s `read_condition`/`read_input` reach `StepIO._read`/`StepIO._contained` by name
  (`StepIO._read(...)`), not through a shared module-level function — those two are already
  stateless `@staticmethod`s with no `StepIO`-instance dependency, so this is reuse of an existing
  extraction rather than a new coupling, but it does mean `ReportIO` still names `StepIO` in its
  own module. Flagging it since the brief's language ("does not subclass") is about inheritance
  specifically and this is not that, but a future reviewer may want those two promoted to
  module-level functions for full symmetry.
- Task 1's M14 render-level arm is carried to task 5 by name (see above) — not a gap I own, but
  worth the next reader confirming it actually lands there rather than dropping a third time.

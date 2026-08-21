# Batch 5 (tasks 8-9): `report <run.yaml>` end to end, and the draft refusal

Branch `h8c-report-study`. Ran `uv run pytest` directly, in the foreground, every time — no
monitor, no background wait. Order 8 → 9, each committed separately.

## Status

Both tasks landed. Suite: baseline **2738 passed, 1 skipped, 2 xfailed** → **2745** after task 8 →
**2746** after task 9. mypy **50** throughout (no new source files — task 8's brief carries no gate
delta, unlike tasks 1/11/15). `ruff check .` and `ruff format --check .` clean after both commits.

## Commit SHAs

- `65207c1` — H8c task 8: report <run.yaml> end to end, exit 0 on partial, and its CLI arm
- `f54c3e7` — H8c task 9: report refuses a draft run, and a bundle flags one

## Test summary

2738/1/2 → 2746/1/2, all clean gates. Task 8 added 7 tests (non-mapping `body`, the `completed`
arm through `main`, Fixture P, a `failed`-status fixture, the bundle-form interim-diagnostic route,
`E-REPORT-FORM` through `main`, and the credential redaction positive control). Task 9 added 1
(Fixture T, the draft refusal).

## What each task did

**Task 8.** `report` joined `OPERATION_COMMANDS` (`{"validate", "run", "freeze", "report"}`), left
`NOT_BUILT_COMMANDS`, and § Operation commands' `report` row flipped to `built` — one commit, per
correction 5. `command_report(path)` lives in `src/publishable/report.py` (not `cli.py`, matching
`freeze`'s split): it decides the form via `report_form`, routes a bundle path to
`cli._report_not_built("report", "Building one")` (task 10's row, not built by this function —
see "Bundle-form routing" below), and otherwise reads the record, resolves credentials through
`freeze`'s own recipe (`validate.declared_credential_names_for` + `templates.registry.get_template`
+ `secrets.credential_values`, no `load_env`), builds a `ReportIO` from the record, and renders
through `render_with_override`. Every diagnostic this function itself prints goes through a fresh
`Collector` carrying `credentials`. `main`'s own bare `except PublishableError` handler is never
reached by anything this function raises internally — a new finding, below, forced widening the
catch from `ContractError` to `BaseException` for exactly one case. A new guard,
`E-REPORT-BODY`, replaces an `AttributeError` `_as_rows` raised on a non-`str`/non-`Mapping`
`Section.body` (batch 4 review, m10, routed to task 8 as unowned).

**Task 9.** `E-REPORT-DRAFT`: `record.get("draft") is True` is checked first, before the credential
lookup, on `freeze`'s "cheap objection first" precedent, and refuses with nothing rendered. Fixture
T hand-edits a real completed run's own `run.yaml` (measured: `run` writes `draft: false`, asserted
in the fixture itself) to `draft: true`, with the test's own docstring stating why. The bundle-flag
arm is **not built here** — carried to task 10 by name, per the brief's own instruction (see below).

## A finding task 8's own scope forced, not named by any brief

`render_with_override`'s pinned test, `test_sys_path_is_restored_after_render_raises`, requires that
a RENDER-time raise (the resolved override's `sections()` body itself, as opposed to an
IMPORT-time fault) propagate **unwrapped** out of that function — only import faults become
`ContractError`s inside it. That is correct and untouched. But it means `command_report`'s own
`except ContractError` around the render call would NOT catch a plain exception an override's
`sections()` raises (a bare `RuntimeError`, say) — and `main()` catches only `PublishableError` and
`OSError`, so such an exception would reach neither collector and print as a raw, un-redacted
traceback. This is exactly the leak class correction 7 exists to close, so `command_report` widens
its own catch (only its own, not `render_with_override`'s) to `except BaseException as exc`, on
`freeze`'s own `code = exc.code if isinstance(exc, PublishableError) else "..."` recipe, minting
`E-REPORT-OVERRIDE-RAISED` for the non-`PublishableError` case. This is a decision the design and
plan brief did not name; it is now in `command_report`'s own docstring and in a new § Errors row.

## Bundle-form routing (my own decision, stated so task 10 knows what it replaces)

Task 8's arm is: `command_report` calls `report_form(path)`; on `"bundle"` it does a
function-local `from publishable.cli import _report_not_built` and returns
`_report_not_built("report", "Building one")`. Two things this route depends on:

- **Import direction.** `report.py` imports `cli._report_not_built` at MODULE scope (same shape
  `freeze.py` already uses for `cli.declared_credential_names`); `cli.py` imports `command_report`
  FUNCTION-locally inside `_dispatch`, exactly where it already imports `command_freeze`. Verified
  this closes no cycle by grep: nothing in `cli.py`'s own module-level imports names `report`.
- **Why not `NotImplementedError`.** From this commit onward `report` is out of `NOT_BUILT_COMMANDS`
  entirely, so an unhandled branch would be a real command's uncaught traceback — the exact fault
  class this project keeps filing. `_report_not_built` is the same interim `study add` takes per
  correction 5, until task 10 replaces this one branch.
- Pinned by `test_report_of_a_bundle_path_routes_to_the_interim_not_built_diagnostic`. **Task 10:
  this branch is yours to delete and replace.**

## The grep for `OPERATION_COMMANDS`'s literal value (task 8 step 1)

Ran, scope stated:

- `grep -rn '"validate", "run", "freeze"'` over `src/publishable/*.py` and `tests/*.py`: no hits
  outside `cli.py`'s own definition line.
- `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
  each grepped individually for the literal set and for `OPERATION_COMMANDS`: no hits. (One
  unrelated hit in `design-principles.md`'s lifecycle-commands table — a different list, not a
  quote of the set — noted and not touched.)
- **Conclusion: no external site quotes this literal**, unlike H8b's `freeze` join, which found two
  (`artifacts.build_allocation_document`'s docstring, `reference.md` § Resuming) — both already
  written in a form that doesn't re-quote the set, so nothing needed re-editing this time.
- **Does anything READ `OPERATION_COMMANDS` beyond `_dispatch`'s arity check?** `grep -rn
  "OPERATION_COMMANDS" src/publishable/*.py tests/*.py` → exactly the definition, the one `if
  command in OPERATION_COMMANDS:` line, and one comment. No second reader; adding `report` is a
  dispatch change only, not a behavior change needing its own pin.

## Decision 6, all three statuses, each verified through the real command (`main(["report", ...])`)

- **`completed`** — `test_report_of_a_completed_run_through_main_renders_all_four_sections`, over
  Fixture R (no override). Exit `0`, all four section headings present in stdout.
- **`partial`** — Fixture P: a real run with a second, always-failing `repeat`-scope step beside the
  scaffolded one, so some executions complete and some fail. Exit `0`; the failed execution's own
  condition label (`"analysis.method=spearman"` or `pearson`, read back from the record, asserted
  non-empty) and its own repeat label both appear in stdout, plus the literal words `partial` and
  `failed`.
- **`failed`** — a run whose ONLY step always raises (no `extra_steps`, so nothing else completes):
  measured via `run_a_project`'s own precedent
  (`test_io_units_train_raises_without_a_fold_or_holdout`'s docstring: no completed execution
  anywhere → `run_status` returns `"failed"`, not `"partial"`). Exit `0`; `failed` and the
  Attrition heading both appear in stdout.

All three go through `main(["report", str(run_dir / "run.yaml")])`, never `command_report` directly,
per the task's own instruction.

## Credential wiring, confirmed with its positive control

Built a project-local template (`CredReportAssay`, `required_env = ["PUBLISHABLE_TEST_REPORT_CRED"]`)
so `get_template` resolving through the run's own `repo_root` is what populates a genuinely
non-empty `credentials` mapping — not a hand-built one. A `report.py` override's `sections()` raises
a plain `RuntimeError` (not a `ContractError`) carrying the credential's VALUE in its message.

- **Ordinary run:** exit `1`; stderr and stdout both lack the sentinel value; stderr carries
  `E-REPORT-OVERRIDE-RAISED` and `<redacted:PUBLISHABLE_TEST_REPORT_CRED>`.
- **Positive control (mutation applied and reverted):** in `command_report`, changed

  ```python
  c.error(code, str(path), str(exc))
  print(c.render(), file=sys.stderr)
  ```

  to

  ```python
  c.error(code, str(path), str(exc))
  print(f"  error   {code:<20} {exc}", file=sys.stderr)  # REDACTION MUTATION
  ```

  Reran the one test: **FAILED** — the sentinel `sekrit-report-h8c-task8-9f3a` appeared verbatim in
  stderr (`assert 'sekrit-...' not in '  error   E...task8-9f3a\n'`). Reverted by restoring the
  saved copy of `report.py` (never `git checkout --`); diffed against the saved copy — identical;
  reran — 1 passed. Confirms the assertion can fail and that the collector, not the exception's own
  `str()`, is what's doing the redaction.

## Mutations, run and reverted, against the full suite each time

**M5** — `return EXIT_PARTIAL if record.get("status") == "partial" else EXIT_OK` in place of the
final `return EXIT_OK`. *Property-preserving arm:* the `completed`/`failed` branches are untouched,
so a mutant that changed behavior for every status alike (e.g. always returning `EXIT_PARTIAL`)
would be a different, cruder mutation; this one specifically targets the `partial` case Fixture P
exists to catch. Ran `pytest tests/test_report.py -k "fixture_p or fixture_f"`: Fixture P
**FAILED** (`assert 3 == 0`), Fixture F stayed green (its status is `"failed"`, untouched by this
mutant) — showing the mutation's effect is scoped exactly where intended. Reverted by restoring the
saved copy; diffed identical; reran — both pass.

**The redaction mutation** — covered above, under credential wiring.

**M6** — replaced the `E-REPORT-DRAFT` refusal block with `print("*** DRAFT — not a final result
***")` and no `return`, so execution falls through to the ordinary render path. *Property-preserving
arm:* Fixture R's non-draft render is untouched (the `if record.get("draft") is True:` guard still
gates the banner the same way it gated the refusal), so a mutant that also broke the non-draft path
would be conflating two different properties; this one isolates "does a draft render instead of
refusing." Ran `pytest tests/test_report.py -k fixture_t`: **FAILED** (`assert 0 == 1` — banner
render exits `0` and prints something, where the pinned test requires exit `1` and empty stdout).
Reverted by restoring the saved copy; diffed identical; reran full `test_report.py` — 84 passed.

## Carry-forward, said explicitly

Per task 9 step 3: the bundle's flag-not-refuse arm (a bundle holding Fixture T's draft record,
asserting exit `0` with the run flagged rather than the whole render refused) is **not built in this
batch** — it cannot be, since no bundle render exists yet. It is task 10's, per the brief's own
routing, and this report names it so the carry is explicit rather than implicit in a brief task 10
might not re-derive on its own.

## Concerns for the next reader

- `command_report`'s `except BaseException` (widened from `ContractError`, see "A finding" above)
  will also catch `SystemExit`/`GeneratorExit` from an override's `sections()`, matching `freeze`'s
  own precedent for its probe call — not narrowed further, on the same grounds `freeze` already
  argues.
- The `repo_root` read for credential resolution is deliberately LENIENT (`_read_repo_root`'s
  `ContractError` is swallowed to `None`) where override discovery's read is strict. This means a
  hand-edited or missing `environment/repo_root.txt` silently drops project-local credential
  resolution rather than refusing — stated in `command_report`'s own docstring as a named cost, not
  hidden.
- No task 10 code exists; the bundle-form route in `_dispatch`/`command_report` is a placeholder by
  design and is meant to be deleted, not extended, by whoever builds it.

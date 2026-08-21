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

## Fix round 1

Review: `.superpowers/sdd/2026-08-21-report-study/task-b5-review.md`. Both verdicts FAIL — one
Critical, three Majors, six Minors. All addressed below, in the order the dispatch listed them.

### Critical 1 — `get_template`/`declared_credential_names_for` outside every `try`

**What changed.** In `command_report`, the `template = get_template(name, repo_root)` call is now
wrapped exactly the way `freeze._precheck`'s own template-resolution step is: `try` / `except
KeyboardInterrupt: raise KeyboardInterrupt from None` / `except BaseException as exc`, computing
`code = exc.code if isinstance(exc, PublishableError) else "E-TEMPLATE-LOAD"`, recovering credential
names off `exc.partial_templates` (a class that raised AFTER `@register_template` still finished
constructing, so `required_env` is readable off it even though its module is refused wholesale), and
refusing through a fresh, redacting `Collector` at `EXIT_WRONG`. This closes the gap the review
named precisely: the calls were copied from `freeze`'s recipe without its containment.

**Verified by running, with the positive control the review itself used.** Added
`test_critical_1_a_template_raising_after_registration_is_still_redacted`: a project-local template
declares `required_env`, then the SAME module raises after `@register_template`, carrying the
credential's real value (via `os.environ[...]`, not a decoy string — my first draft used a decoy and
the test passed for the wrong reason; caught by checking the failure message before trusting it,
fixed to embed the real env value). Ordinary (fixed) code: exit 1, sentinel absent from both
streams, `<redacted:PUBLISHABLE_TEST_REPORT_CRED>` and `E-TEMPLATE-LOAD` present in stderr.

**Mutation, reverted.** Removed the `try`/`except` around `get_template`, leaving the two calls
bare (`# M-CRITICAL1 MUTATION: containment removed, calls left bare`). Ran
`pytest tests/test_report.py -k critical_1`: **FAILED** — `assert 'sekrit-report-h8c-task8-9f3a' not
in "...carrying sekrit-report-h8c-task8-9f3a')\n"` — the sentinel reached stderr verbatim, exactly
the leak the review demonstrated. *Property-preserving arm:* every OTHER refusal path in
`command_report` (form, record read, draft) is untouched by this mutation and stays green; only the
template-resolution path loses its redaction, which is the property under test. Reverted by
restoring the saved pre-mutation copy of `report.py`; diffed byte-identical; reran — 1 passed.

### Major 1 — the bundle arm's false "not built" claim at a forbidden exit code

**What changed.** The bundle-form branch of `command_report` no longer calls
`cli._report_not_built`. It is now `report`'s own coded refusal: `E-REPORT-BUNDLE-UNSUPPORTED` at
`EXIT_WRONG` (1), naming the FORM ("the bundle form of `report`... is not yet built... `report
<run.yaml>` is") rather than falsely claiming the whole command is unbuilt, at an exit code (2)
Decision 6 reserves for an invocation fault decided before this function is ever called. The
now-false module docstring claim ("this module imports `cli._report_not_built` at module scope") is
deleted rather than rewritten — the import is gone entirely, not merely relocated — and
`cli.py`'s own comment at the `_dispatch` arm is corrected to describe `freeze`'s real module-scope
import and `report`'s real absence of one (Minor 1, folded in here since it's the same lines).
A new § Errors row for `E-REPORT-BUNDLE-UNSUPPORTED` lands in this fix-round commit, alphabetically
between `E-REPORT-BODY` and `E-REPORT-DRAFT`.

**The old, now-false pinning test was deleted, not left broken or "fixed" to match the old
behavior**: `test_report_of_a_bundle_path_routes_to_the_interim_not_built_diagnostic` asserted
exactly the defect (exit 2, "is specified but not built"). Replaced by
`test_major_1_report_of_a_bundle_path_is_report_s_own_refusal_not_a_false_claim`, asserting exit 1,
`E-REPORT-BUNDLE-UNSUPPORTED` present, and the false sentence absent.

**Mutation, reverted.** Restored the old `cli._report_not_built("report", "Building one")` call in
place of the new refusal (`# M-MAJOR1 MUTATION: restore the pre-fix false-claim route`). Ran
`pytest tests/test_report.py -k major_1`: **FAILED** — `assert 2 == 1`. *Property-preserving arm:*
every other refusal in the function returns 1 unconditionally; this mutation touches only the
bundle branch, so a mutant that also broke, say, `E-REPORT-FORM`'s exit code would be conflating two
different properties — this one isolates exactly Major 1's claim. Reverted; diffed identical; reran
full `test_report.py` — 91 passed.

### Major 2 — a parseable-but-incomplete record tracebacks instead of refusing

**What changed.** `_report_io_from_record(run_dir, record)`'s call site in `command_report` is now
wrapped in `try: ... except (KeyError, TypeError) as exc:`, refusing with a NEW code,
`E-REPORT-RECORD-INCOMPLETE`, through the credential-carrying `Collector` already in scope. This is
a new code rather than a widened `E-UPSTREAM-RECORD-*` row deliberately: the shipped family is
`read_record_file`'s OWN three checks (existence, parseability, schema version), and this fault is
downstream of a record that already passed all three — reusing that family's code for a
DIFFERENT fault is the exact "row narrower than its code" shape `CLAUDE.md` names as this project's
repeat whole-branch Major. § Errors row added in this commit, alphabetically after
`E-REPORT-OVERRIDE-REPO` and before `E-RESOLVER-UNKNOWN`.

**Verified by running, parametrized over all three keys the review's own table named**:
`test_major_2_a_record_missing_a_needed_key_is_refused_not_a_traceback[execution|results|config]`,
each dropping one top-level key from a real run's record and asserting exit 1, the new code present,
and no `Traceback` text in stderr.

**Mutation, reverted.** Removed the `try`/`except`, leaving the bare call (`# M-MAJOR2 MUTATION:
guard removed`). Ran `pytest tests/test_report.py -k major_2`: **all three parametrized arms
FAILED**, each with an uncaught `KeyError` traceback through `main` → `_dispatch` →
`command_report` → `_report_io_from_record`, exactly the fault class the review named. *Property-
preserving arm:* the three arms (dropping `execution`, `results`, `config` respectively) fail at
different lines inside `_report_io_from_record` for different reasons — this is why the fixture is
parametrized rather than testing one drop: each key's absence is an independently distinguishable
crash site, and a single-key test could not have shown the guard covers all three. Reverted;
diffed identical; reran — 3 passed.

### Major 3 — the fresh-`KeyboardInterrupt` guard was pinned by nothing

**What changed:** nothing in the shipped code — the guard (`except KeyboardInterrupt: raise
KeyboardInterrupt from None`) was already correct, per the review's own finding. What changed is the
test suite: added `test_major_3_keyboard_interrupt_from_an_override_propagates_with_no_message`, on
`tests/test_cli.py`'s own shipped precedent for the identical shape at a resolver
(`test_a_resolvers_keyboard_interrupt_at_run_propagates_with_no_message`) — `pytest.raises
(KeyboardInterrupt)` around `main([...])`, asserting `excinfo.value.args == ()` and `str(excinfo.
value) == ""` for an override whose `sections()` raises `KeyboardInterrupt("ctrl-c carrying
<sentinel>")`.

**Mutation, reverted.** Changed `raise KeyboardInterrupt from None` to a bare `raise` (`#
M-MAJOR3 MUTATION: bare raise, not a fresh argument-less one`). Ran `pytest tests/test_report.py -k
major_3`: **FAILED** — `assert ('ctrl-c carrying sekrit-h8c-b5-fix-round-1',) == ()` — the
constructed message survived the re-raise. *Property-preserving arm:* the sibling `except
BaseException` arm one line below (for every non-`KeyboardInterrupt` fault) is untouched, so a
mutant that also broke THAT arm's redaction would be a different, cruder mutation; this one isolates
exactly the `KeyboardInterrupt`-carries-no-message property. Reverted; diffed identical; reran full
`test_report.py` — 91 passed. This closes the exact gap `CLAUDE.md` names ("five times in three
slices a correct fix shipped unpinned").

### Minor 1 — two docstrings claim a module-scope `cli` import that doesn't exist

Folded into Major 1's fix: the report.py module docstring's false claim is deleted (not rewritten —
"prefer deleting a claim to rewriting it"), and `cli.py`'s `_dispatch` comment is corrected to
describe `freeze`'s real module-scope import of `cli.declared_credential_names` and `report.py`'s
real absence of any import from `cli` (now that the bundle arm no longer calls into `cli` at all).

### Minor 2 — `E-REPORT-BODY` pinned only at the renderer, against the brief

**What changed:** added `test_minor_2_e_report_body_is_reachable_through_main`, an override yielding
`self.section("Bad body", body=42)`, asserting `main(["report", ...])` gives exit 1 and
`E-REPORT-BODY` in stderr — the command-level route the task's own brief required and the shipped
suite never exercised.

### Minor 3 — a positional row locator in the `E-REPORT-OVERRIDE-RAISED` § Errors row

**What changed:** `docs/reference.md`'s row no longer says "every other `E-REPORT-OVERRIDE-*` row
**above**" (false since the table is alphabetical and `E-REPORT-OVERRIDE-REPO` sits below it). It
now names what the sibling rows DO ("the discovery faults, finding and importing the class") instead
of where they sit.

### Minor 4 — no test renders a successful override through the command

**What changed:** added `test_minor_4_a_successful_html_override_renders_through_main` — an override
declaring `format = "html"` and composing with `yield from super().sections(run, io)` plus one extra
section, asserted through `main(["report", ...])` at exit 0, self-contained HTML, both the standard
and the added section's text present.

### Minor 5 — Decision 2's "prints the cheap one first" is not delivered

**What changed:** `BaseReport.sections`'s own docstring is sized down — it now says only what the
lazy generator actually buys (a later section's construction is skipped when an earlier one raises),
and states explicitly that `command_report` buffers the full render into one `str` before printing
once, so nothing streams. The DESIGN doc's Decision 2 is dated, tracked development record and is
not retro-edited; a new `spec-defects.md` entry ("Decision 2's 'prints the cheap one first' is not
delivered at the real command") records the gap instead, unowned, since fixing it would be a real
streaming behavior change to a shipped command — out of a review fix-round's scope.

### Minor 6 — a credential rendered into a report body reaches stdout

**What changed:** one sentence added to `docs/reference.md` § Secrets & credentials' limit
paragraph, naming a report override's `Section.body` alongside a step's `io.record` as a second
surface the redaction promise does not cover — closing exactly the gap the review named ("the limit
sentence does not name a rendered report"). No code changed; the review's own judgement (this is
spec-consistent, not a defect) stands.

### Gates and full suite after all of the above

`ruff check .` clean; `ruff format --check .` 90 files; `mypy` 50 source files, no issues. Full
suite, foreground, stale temp dirs cleared first: **2753 passed, 1 skipped, 2 xfailed** (2746 → 2753,
+7 net: 8 new tests in the fix round minus the 1 deleted stale bundle test).

### What I did not close

Nothing from the review is left open. The one thing explicitly NOT fixed in code is Minor 5's
underlying behavior (output still buffers rather than streaming) — filed rather than built, for the
reason stated above: it is a real behavior change to a shipped command, not a wording defect, and no
task in this slice owns it.

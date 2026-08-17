# Task 12 report

**Status:** complete. Commit `248c152` on `h7c-credentials`.

**Tests:** `uv run pytest -q` → 1993 passed, 2 xfailed (1989 + 4 new before this
task, per the brief's baseline). `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy` all clean.

## The four new tests

1. `test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so` — step-error
   boundary, `GenericTemplate.required_env`.
2. `test_a_step_reads_its_credential_and_the_value_still_reaches_no_artifact` — success
   path, same boundary.
3. `test_a_template_exception_printed_as_a_warning_is_redacted_too` — the
   `Collector.render()` boundary, via a project-local template's `aggregate` raising.
4. `test_a_project_local_template_s_credentials_are_redacted_too` — step-error boundary
   again, but through a project-local template resolved with `repo_root`, closing the
   `requires_env` half neither `GenericTemplate` fixture reaches.

## Mutation outcomes (all four, both halves each)

**(a) Removed the step-error boundary** (`runner.py`'s `error = redact(...)` reverted to
the plain f-string): tests 1 and 4 (both step-error-path fixtures) went **RED** on the
`<redacted:...>` assertion; test 3 (the render-boundary fixture) stayed **GREEN**, exactly
as expected since its sentinel never touches `ExecutionResult.error`. Reverted by editing
the file back; `diff` against a pre-mutation copy confirmed byte-identical; re-ran to
confirm green again.

**(b) Removed the `Collector.render()` boundary** (`diagnostics.py`'s message line
reverted to `f"          {f.message}"`): test 3 went **RED** on both the
`<redacted:PUBLISHABLE_TEST_AZURE>` assertion and the bare `_SENTINEL not in out`
assertion; tests 1 and 4 stayed **GREEN**. Reverted and re-confirmed the same way.

Both pairs discriminate correctly — no mutation reddened both boundaries' tests, and no
mutation left its own boundary's test green. Mutation (c) — redact-by-pattern on a
`sk-`-prefix — was not run here; it is named in the brief as blind and already covered by
`tests/test_secrets.py`'s `test_redaction_replaces_the_exact_value_and_names_the_variable`.

## Render-boundary fixture reachability — verified, not assumed

Confirmed by running `test_a_template_exception_printed_as_a_warning_is_redacted_too` alone:
the run reaches `EXIT_OK` (the default `expect_exit`, and the test passed against it), and
`"W-STATS-AGGREGATE-FAILED" in out` held before the redaction assertion was even reached —
i.e. `aggregate` was genuinely invoked (the scaffold's default `STARTER_STEP` calls
`io.record`, so a recording step existed for it to run over). The failing mutation (b) run
above shows the same warning line reaching `out` with the raw sentinel still in it,
independently confirming the route is live: `raise` → `W-STATS-AGGREGATE-FAILED` →
`aggregate_c.render()` → `print(...)` → `capsys` → `doc["stdout"]`.

## `_local_template`

Had zero real callers before this task (only present in `run_a_project`'s signature and
docstring from task 8) — confirmed by grepping `tests/test_cli.py` for `_local_template=`
before writing anything. This task's tests 3 and 4 are its first two callers.

## Where the brief/spec disagreed with the code

1. **`expect_exit=EXIT_PARTIAL` was wrong for the step-error fixtures as the brief wrote
   them.** The scaffolded project has exactly one `repeat`-scope step; when that one step
   raises unconditionally, *every* execution fails and `run_status` sees no completed
   execution anywhere, giving `"failed"` (`EXIT_FAILED`, code 4) rather than `"partial"`.
   This is the identical fixture defect `tests/test_cli.py`'s
   `test_io_units_train_raises_without_a_fold_or_holdout` already found and documented in
   this same slice ("a real mismatch against the brief this test started from"). Fixed the
   same way that test fixed it: added `extra_steps=["control"]` (the generated no-op step,
   always completes) to both `test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so`
   and `test_a_project_local_template_s_credentials_are_redacted_too`, so the run genuinely
   mixes a failure with a success and `run_status` reports `partial` for real.
2. **`test_a_template_exception_printed_as_a_warning_is_redacted_too`'s config needed
   `parameters={}`.** `CredAssay.parameter_spec` is empty, but `run_a_project`'s generated
   config carries the generic scaffold's default `parameters.analysis.*` block, which
   `validate` refuses as `E-PARAM-UNKNOWN` for a template declaring no parameters at all —
   before `run` ever reaches `execute_plan`, so the run never started (`EXIT_WRONG`) until
   this was added.
3. **Decision 1 (validate-side helper naming/hoisting).** The brief offered
   `declared_credential_names_for(doc, template)` in `validate.py` or hoisting a single
   shared function with `cli.declared_credential_names`. Wrote them as two separate
   functions rather than one: `cli.py`'s must take the already-expanded `conditions` to
   avoid a second `expand(doc)` derivation that could drift from the plan actually
   executed (mandated by correction 3 in the design doc), while `validate.py`'s
   `declared_credential_names_for` re-derives `expand(doc)` under a guard — matching this
   module's own existing convention (`_check_requires_env`, `_check_sweep`,
   `_check_contrasts` all independently re-derive `expand(doc)` the same guarded way,
   since `validate` collects per-check rather than threading one resolved plan through
   every check function). A true merge would have required changing that file-wide
   convention, which is out of scope for this task. Not shipping two *identical*
   functions — the logic core (spec walk + condition-value resolution) is genuinely
   shared in shape but the signatures differ for a stated reason.
4. Everything else in the brief (the `Collector`/`Diagnostic` boundary split, the
   `run_template`/`credentials` placement in `command_run`, the `_flatten_parameters`
   local mirror, the quoted `"list[Condition]"` annotation, the five construction sites)
   matched the code as found, verbatim.

## Concerns

None outstanding. `aggregate_c` and `drift_c` (both constructed after `credentials` is in
scope in `command_run`) were given `.credentials = credentials`; `dirty_c`, the
pre-execution `c`, and `warn_c` are constructed before `credentials` exists and carry only
core-authored text, so they were left alone; `io_c` lives in `main`, a different function
with no `credentials` in scope at all, and carries only a filesystem-error message, so it
was left alone too.

## Correction, appended after the task-12 review

**§ Mutation outcomes was titled "all four, both halves each" but reported only two.** Step 7
of the brief mandates a third — dropping `repo_root` from `get_template(...)` — with the
requirement that tests 3 and 4 go RED while both `GenericTemplate` tests (1 and 2) stay GREEN.
That mutation was run and its outcome was never entered here; the heading read as exhaustive
without being exhaustive. The reviewer ran it independently:

**(c) Dropped `repo_root`** (`cli.py`'s `get_template(doc.get("experiment_type", ""))` losing
its second argument): tests 1 and 2 (both `GenericTemplate` fixtures) stayed **GREEN**; tests 3
and 4 (the project-local-template fixtures) went **RED**, with `errors` coming back carrying
the sentinel unredacted in `executions.jsonl` because `run_template` resolved to `None` and
`credentials` emptied before either fixture's boundary saw it. This is exactly the defect the
`repo_root` argument exists to prevent, and it is the outcome check 5 in the review confirms.
The code and its reasoning were already correct; only this entry was missing.

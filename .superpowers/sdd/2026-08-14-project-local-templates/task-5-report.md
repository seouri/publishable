# Task 5 report — wire the other two `get_template` call sites

## Status: complete

## Commit

`e5d727b` — Wire repo_root through generate_experiment and command_run's aggregate lookup

## Changes

- `src/publishable/cli.py` § `command_run`'s `aggregate` block: `get_template(doc.get("experiment_type", ""))` → `get_template(doc.get("experiment_type", ""), repo_root)` (`repo_root` already bound earlier in the same function).
- `src/publishable/generators/experiment.py` § `generate_experiment`: `get_template(template_name)` → `get_template(template_name, repo_root)` (`repo_root` already a parameter).
- Confirmed by grep (`grep -rn "get_template(\|template_names(" src/publishable/`) that these are the only two remaining call sites — `validate.py:503` was task 4's, and `validate.py:509`'s `template_names()` is task 14's message-list, untouched.
- `tests/test_cli.py`: three new tests, all end-to-end through `main`/`generate_experiment`, none of them mocking `get_template` itself:
  - `test_generate_experiment_resolves_a_project_local_template` — calls `generate_experiment()` directly with `template_name="my_assay"` against a project holding `templates/my_assay.py`; asserts the config materializes with `experiment_type: my_assay` and, since `MyAssay(BaseTemplate)` carries an empty `parameter_spec`, `parameters` comes back `None` — pinning that `my_assay` itself resolved rather than merely that some template answered to the name. Control: `template_name="nope"` still raises `ContractError` with `E-TEMPLATE-UNKNOWN`.
  - `test_generate_experiment_cli_resolves_a_project_local_template` — the literal probe from the brief, through `main(["generate", "experiment", ..., "--template", "my_assay", ...])` with `monkeypatch.chdir(root)`, exercising `_dispatch_generate`'s `find_repo_root(Path.cwd())` too (not required by the brief, added because it was cheap and closes the literal-probe gap — see concerns). Control: `--template nope` returns `EXIT_WRONG`.
  - `test_command_run_aggregate_resolves_a_project_local_template` — a full `run` through a project whose config names `experiment_type: my_assay`, where `MyAssay(BaseTemplate).aggregate` is a real override on disk; asserts the metric it computes (`n_units_seen`) lands in `run.yaml`. Uses `_AGGREGATE_STEP` (records a `pred` float column) rather than the scaffold's default step, which records a bare `True` — the resampled `aggregate` treated a `KeyError` on that field as a degenerate `0.0` rather than raising, which is how the first draft of this test passed with the wrong number instead of failing loudly.

## Mutation testing (step 5)

Each site mutated to pass `None` in turn, tests run, `__pycache__` deleted, site reverted, tests re-run — verified by rerunning pytest, not `git status`.

- `generators/experiment.py`'s `get_template(template_name, None)`: both `test_generate_experiment_resolves_a_project_local_template` and `test_generate_experiment_cli_resolves_a_project_local_template` failed (`E-TEMPLATE-UNKNOWN` where `EXIT_OK`/no-raise was expected); `test_command_run_aggregate_resolves_a_project_local_template` still passed, since it calls `generate_experiment(template_name="generic")`, which resolves from `_BUILTIN` regardless of root. Reverted, all three pass.
- `cli.py`'s `get_template(..., None)`: only `test_command_run_aggregate_resolves_a_project_local_template` failed (`KeyError: 'n_units_seen'` — the built-in `BaseTemplate.aggregate` ran instead of `MyAssay`'s); the two generate-side tests were unaffected, since neither reaches `command_run`. Reverted, all three pass.

This also stands as the red-before-green evidence step 2 asked for: the `None` mutation at each site *is* the pre-fix code (the old calls were `get_template(name)` / `get_template(template_name)`, and the signature's second parameter defaults to `None`), so each new test was observed failing against the actual prior behavior before the fix, not just against a hand-mutated stand-in.

## Verification

`uv run pytest` — 1653 passed, 2 xfailed. `uv run ruff check .` — all checks passed. `uv run mypy` — no issues, 41 source files.

## Concerns

- Advisor review caught two real issues before commit, both fixed: (1) the aggregate-block fixture template originally imported `publishable.templates.builtin.generic.GenericTemplate`, violating the one-import-root invariant for user-written template code — replaced with a `BaseTemplate` subclass plus `doc["parameters"] = {}` to avoid `E-PARAM-UNKNOWN`; (2) the first draft's identity assertion (`doc["experiment_type"] == "my_assay"`) couldn't distinguish "this template resolved" from "some template resolved under this name" — added the `parameters is None` check, which only holds for `MyAssay`'s empty spec, not `generic`'s.
- The brief's Step 1 names two tests; I wrote three, adding the CLI-dispatch-level one (`main(["generate", "experiment", ...])` rather than calling `generate_experiment()` directly) so the literal probe in the brief — `publishable generate experiment --template my_assay` — is exercised as typed, including `_dispatch_generate`'s own `find_repo_root(Path.cwd())`. This wiring was already correct and untouched by this task; the extra test doesn't change the diff's substance, only its coverage.
- No requirement in the brief was wrong or unsatisfiable. The one soft spot: the brief's phrase "each must fail its own test" undersells what's checkable for free — since the three tests exercise three different call paths, the mutation matrix (mutate site A, run all three tests) also shows the sites are *independent*, not just individually sensed, and I recorded that cross-check in this report rather than leaving it implicit.

## Coordinator review round 2 — two fixes applied, commit `33e4ce1`

The coordinator's review confirmed the spec and wiring (separate-sensing by mutation, and the stop-checking control by patching `get_template` to fall back to `GenericTemplate`), and confirmed no hidden fourth aggregate path — `draft`, `resume`, and `dry-run` all route through `command_run`. It found two real gaps, both fixed:

1. **The identity assertion in `test_generate_experiment_resolves_a_project_local_template` was a proxy, not a pin.** `doc["parameters"] is None` only proved "this is not `generic`" — any other empty-`parameter_spec` template resolving in `MyAssay`'s place (including a stand-in with the same shape, exactly the class of defect task 3's review found: a merge mutation that left all 16 tests in a file passing because identity was pinned nowhere) would have passed the same assertion. Fixed by giving `MyAssay` a distinctive `parameter_spec` — `{"assay.tag": Param(str, default="my-assay-fingerprint")}` — and asserting the materialized `doc["parameters"] == {"assay": {"tag": "my-assay-fingerprint"}}` exactly.

   **Mutation-proved the strengthened assertion**: changed the fixture's `Param` default in place to `"a-different-fingerprint"` (a different non-empty spec, simulating a wrong-but-similarly-shaped template resolving instead), ran `test_generate_experiment_resolves_a_project_local_template` — it failed on the dict-equality assertion as expected. Reverted the string, deleted `__pycache__`, reran — passed. This is the evidence that the assertion now pins template identity rather than merely "non-empty."

2. **The CLI-level control checked only `EXIT_WRONG`, not the code.** `test_generate_experiment_cli_resolves_a_project_local_template`'s `--template nope` control would have passed on any unrelated `EXIT_WRONG` refusal. Added a `capsys` fixture and `assert "E-TEMPLATE-UNKNOWN" in capsys.readouterr().err` after the `--template nope` call, matching the code-level assertion its sibling test (`test_generate_experiment_resolves_a_project_local_template`, via `excinfo.value.code`) already made.

Re-ran the full suite after both fixes: `uv run pytest` — 1653 passed, 2 xfailed; `uv run ruff check .` — all checks passed; `uv run mypy` — no issues, 41 source files. Committed as `33e4ce1`.

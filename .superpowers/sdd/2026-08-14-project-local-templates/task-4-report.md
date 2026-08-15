# Task 4 report: hoist `find_repo_root` above the template check

## Status: complete

## Commits

- `15ee377` — "Hoist find_repo_root above the template check in validate_config"
- `b75a485` — "Give the no-repo hoist test its own sensor, not a shared one"
  (follow-up from coordinator review, see § Post-review correction below)

## What changed

`src/publishable/validate.py` § `validate_config`:

- Moved the `try: find_repo_root(config_path) except ContractError: repo_root = None`
  pattern up, from the entrypoint-import block to immediately after
  `name = doc.get("experiment_type", "")`, before `get_template` is called.
- `get_template(name)` → `get_template(name, repo_root)`, so a local
  `templates/*.py` in the resolved repo is discoverable.
- The entrypoint-import block below no longer computes `repo_root` a second
  time — it reuses the value computed above and keeps its own
  `if repo_root is not None: experiment = load_experiment(...)` guard
  unchanged.
- `template_names()` in the `E-TEMPLATE-UNKNOWN` message is untouched (that's
  task 14's).

`tests/test_validate.py`:

- Fixed the routed finding from task 3's review: `get_template`'s monkeypatch
  stub in `test_a_template_cross_field_rule_is_reported` was a one-argument
  `lambda name: RuleBreaker()`; changed to
  `lambda name, repo_root=None: RuleBreaker()` so it doesn't raise `TypeError`
  now that `validate_config` always passes `repo_root`.
- Added three tests, placed next to the existing
  `test_an_uninstalled_template_is_fatal`:
  - `test_an_unknown_template_still_reports_exactly_one_finding` — asserts
    `codes(...) == {"E-TEMPLATE-UNKNOWN"}` (exact set, not membership).
  - `test_a_local_template_validates_through_the_real_path` — writes a real
    `templates/my_assay.py` into `git_repo`, points `experiment_type` at it,
    asserts `E-TEMPLATE-UNKNOWN` is absent; control asserts an unregistered
    name still draws it.
  - `test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves`
    — monkeypatches `find_repo_root` to raise `ContractError(code="E-GIT-NO-REPO")`
    (matching the file's existing no-repo test style) and asserts
    `codes(write_config()) == set()`: the hoist must swallow the exception
    silently and `generic` must still resolve.

## Verification

- `uv run pytest` — 1650 passed, 2 xfailed.
- `uv run ruff check .` — all checks passed.
- `uv run mypy` — no issues found in 41 source files.
- Mutation 1 (let `find_repo_root`'s `ContractError` propagate, i.e. delete
  the `try`/`except`): confirmed FAIL on
  `test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves`
  (uncaught `ContractError` from `find_repo_root`). Deleted `__pycache__`,
  reverted, confirmed PASS by re-running the test.
- Mutation 2 (report a finding on a missing repo instead of swallowing it,
  i.e. add `c.error(...)` inside the `except ContractError` branch):
  confirmed FAIL on the same test (`{'E-MUTATION-TEST'} == set()` mismatch).
  Deleted `__pycache__`, reverted, confirmed PASS with a full `uv run pytest`.
- Both reverts verified by behavior (test outcomes), not by `git status`.

## Test summary

13/13 template- and no-repo-related tests pass in isolation; full suite
1650 passed, 2 xfailed; both named mutations killed the target test and were
reverted cleanly.

## Concerns

None regarding the early-return order: `E-TEMPLATE-UNKNOWN` still fires
exactly once and returns immediately after, and the no-repo path adds no
finding ahead of it — both are now covered by exact-set assertions rather
than membership checks, per the brief's emphasis that membership cannot see
an added finding.

## Post-review correction

The coordinator's review caught that my original framing of the "duplicate
test" concern was wrong, not just cosmetically but factually. I had written
that the new `test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves`
and the pre-existing `test_the_genuine_no_repo_case_returns_quietly` were
"defense-in-depth" guarding different call sites. That's false: both
monkeypatched `validate_mod.find_repo_root`, the single module-level name
every call site in `validate.py` reads from — patching it patches the hoisted
call *and* `_check_data`'s call identically. There is no input on which they
diverge, so the second test contributed exactly zero incremental mutation
coverage over the first, dressed up as if it did.

Rather than deleting the new test, I narrowed its seam so it actually
isolates the hoisted call: the stub now raises `ContractError` only on the
*first* `find_repo_root` invocation (the hoist always runs first) and
delegates every subsequent call to the real implementation, so
`_check_data`'s own lookup hits the genuine repo `write_config` writes into
rather than the stub.

I verified the isolation is real, not just newly-worded, with two additional
mutation trials beyond the original two (all reverted after, `__pycache__`
deleted each time, confirmed by rerunning tests rather than by `git status`):

- Reproduced both of the brief's original two mutations against *only* the
  narrowed test in isolation (not the whole suite) — both still FAIL on it,
  confirming it didn't lose the coverage the brief asked for.
- A **new** mutation inside `_check_data`'s own `except ContractError`
  branch (`if exc.code == "E-GIT-NO-REPO": <add a c.error here>; return`):
  `test_the_genuine_no_repo_case_returns_quietly` FAILS (it still forces
  every call to raise, including `_check_data`'s), while the narrowed
  `test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves`
  PASSES — because its second call reaches the real `find_repo_root`, finds
  the real repo, and never enters that branch at all. This is the proof the
  two tests now exercise different call sites: a mutation local to
  `_check_data` is invisible to the hoist test, and (from the original two
  mutations) a mutation local to the hoist is invisible to
  `test_the_genuine_no_repo_case_returns_quietly` only in the sense that it
  no longer needs to be caught there — it already was, correctly, before.

The report's earlier "defense-in-depth" claim is withdrawn; the corrected
claim is narrower and mutation-verified: the two tests now cover two
distinct call sites of `find_repo_root`, each falsifiable independently of
the other.

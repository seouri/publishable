# Tasks 16–20 — report

## Status

All five tasks complete. Gates clean: `uv run ruff check .`, `uv run ruff format --check .`,
`uv run mypy` all pass. Final suite: `uv run pytest` → **2054 passed, 1 skipped (slow), 2 xfailed**
(baseline was 2040 passed + 2 xfailed; net +14 = task 16 +4, task 17 +4, task 18 +3, task 19 +3,
task 20 +0).

## Commits

| Task | SHA | Message |
|---|---|---|
| 16 | `baa8337` | feat: the decorator-vs-key comparison, and the consequence that validate cannot see it |
| 17 | `e695384` | feat: plugin import-failure containment, SystemExit included, draining the pending buffer |
| 18 | `3fbaf13` | feat: --plugin runs uv add and writes the plugin field — and reverts task 6's markings |
| 19 | `060789c` | feat: data.units.from is closed one level in, and a mapping naming two sources is refused |
| 20 | `aa37916` | docs: a metadata-only collision carries no class, and the residual is filed as accepted |

## Test summary

- Task 16: `check_registration`/`declared_names` — 4 new tests, all pass. 3 prescribed mutations run;
  each FAILed the test it was supposed to fail, each reverted, suite reconfirmed green.
- Task 17: `load_entry_point` — 4 new tests, all pass. Whole suite run twice in a row in one command
  (`pytest -q && pytest -q`) — both 2048 passed, no leak into `test_templates.py`'s discovery tests.
  3 prescribed mutations run and reverted; mutation (b) (`SystemExit` propagating) confirmed by
  reading pytest's own exit behavior rather than an assertion, as the brief specified.
- Task 18: `--plugin`/`uv_add`/`plugin_requirement` — 3 new tests (1 materialize, 2 CLI), all pass.
  Slow test written as `pytest.skip` (no `git+https://` dependency this project already carries to
  install offline; real network access would be needed). `pytest -q -m "not slow"` → 2051 passed,
  1 deselected; with slow included → 2051 passed, 1 skipped. 3 prescribed mutations run and reverted,
  each failing exactly the assertion the brief named — mutation (c) confirmed the materialize test
  does *not* catch it and the CLI test does, as predicted.
- Task 19: envelope closure + mutual exclusion — 3 new tests (2 envelope, 1 validate), all pass.
  `test_envelope.py` run in full first (34 passed, no regression from the closure). 3 prescribed
  mutations run and reverted, each failing the assertion the brief named.
- Task 20: decision 3 residual — step 1's test was written, then run against the real un-redacted
  message (patching `publishable.diagnostics.redact` to a no-op) per the brief's own instruction, and
  the sentinel credential **never appeared** in the `E-TEMPLATE-COLLISION` message — it names
  providers (`<path>::<ClassName>`, a dotted module path), never a declaration. Per the brief's
  explicit fallback, the test was **deleted** and replaced with a comment recording that no test in
  this slice reaches `partial_templates`' payload at all. Net test count for task 20 is **+0**, as
  the brief allowed. The one prescribed mutation (emptying the payload) was still applied and the
  whole suite run against it: no test failed, confirming the residual is real and unpinned — reverted
  afterward. The "mutation that does not exist" (`claims.values()` → `local.values()`) was correctly
  not written, per the brief.

## Task 18's `Status` row

**True.** `docs/reference.md`'s `generate` row, the `experiment` generator row, and § Plugins'
opening sentence all lost their `NOT BUILT`/"parses and is dropped" markings task 6 added, and
`--plugin` now really runs `uv add` before anything reaches disk (verified by
`test_generate_experiment_installs_the_plugin_before_it_scaffolds` and
`test_a_failed_plugin_install_scaffolds_nothing`, both exercising `main` end to end, not
`generate_experiment` directly). `_dispatch_generate` passes `plugin=opts.get("plugin")` through, so
recognition of `--plugin` is now real rather than the "accepts and silently drops any unknown flag"
behavior the task-6 review flagged.

## Task 20's residual

Filed at `docs/superpowers/spec-defects.md` as **`## OPEN — a plugin-side collision carries no class,
so its finding cannot be redacted — Owner: none; accepted`**. States: an installed claim carries no
class because the entry-point scan is metadata-only by decision 3, so `required_env`/`parameter_spec`
are never available to redact a plugin-side collision's credentials; the repair (`.load()`) would
destroy the exact invariant entry points exist for; the exposure is bounded because a collision
message interpolates providers, never a declaration; and it closes together with (not independently
of) the sibling residual `## OPEN — an installed template's name resolves but its class is never
loaded`.

## Where a brief or the spec disagreed with the code

- **Task 20, step 1.** The brief anticipated this outcome explicitly ("that outcome is acceptable and
  expected") and it is what happened: the collision message never carries a credential, so the
  discriminating test was vacuous and was deleted rather than shipped. Not a disagreement so much as
  the brief's own conditional branch firing.
- **Task 19, `write_config` fixture.** The brief's test bodies write `{"data.units.from": {...}}` as
  an override key. `write_config`'s dotted-path walker requires every intermediate segment to already
  exist in `base_config`, and `base_config`'s `data` dict has no `units` key — only `{"data.units":
  {...}}` (one level up) works, the pattern every other test in the file already uses. Rewrote both
  new `test_validate.py` cases to override `"data.units"` as a whole mapping (adding `"key":
  "patient_id"` alongside `from`, matching the established pattern) rather than `"data.units.from"`
  directly. No behavior change — cosmetic to the fixture's own contract.
- Everything else matched the briefs' prescribed text and mutation outcomes exactly, including the
  three "checked against the body" claims in tasks 16, 17, and 19 — each mutation's predicted
  pass/fail outcome was verified rather than assumed.

## Notes on the four invariants

- No path added anywhere calls `.load()` except `load_entry_point` itself (task 17's sole purpose,
  documented as the module's one importing function) — `scan_group`/`check_registration` remain
  metadata-only, confirmed by re-running their existing no-import assertions unchanged.
- `E-DATA-RESOLVER-UNSUPPORTED` still fires on every resolver-only and both-keys config in task 19's
  tests, asserted alongside `E-UNITS-SOURCE-AMBIGUOUS` rather than instead of it (mutation (c) pins
  this discipline directly).
- No change touched `command_run`'s credential computation or `_check_units`'s `except ContractError`
  guard — Part B's options are untouched.
- `validate_config` still collects; `_check_units_source` is a `c.error(...)` call, not a raise, and
  runs before `_check_units` without altering its control flow.

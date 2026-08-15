# Task 10 report: `template_version` and `plugin` under a local template

## Status

Done. Commits `6b62b95`, `f4c1366`, `e99e50f` on branch `h7a-local-templates`.

## What changed

- `src/publishable/templates/discovery.py`: added `is_local_template(cls)`, a
  predicate beside `_module_name` that reads the `_publishable_local_` prefix
  off `cls.__module__` — the one place that already knows the naming scheme,
  so nothing re-imports `templates/**` a second time to answer "is this
  local?".
- `src/publishable/materialize.py`: `materialize_config` now checks
  `is_local_template(type(template))`. For a local template it emits no
  `template_version` key at all, and drops the header comment's
  `` v{TEMPLATE_VERSION}`` clause (trap (c) from the brief — the header was a
  third, unnamed instance of the same false claim). `plugin: null` is
  unchanged for every template — decision 2 needed no code, only a test.
- `src/publishable/validate.py`: `_check_versions` now returns immediately
  when `is_local_template(type(template))`, before reading `declared` at all
  — so the skip holds regardless of what a config's `template_version` says,
  not only when it's absent.
- `docs/reference.md`: amended § Three hashes and the `W-TEMPLATE-VERSION`
  row in § Errors `validate` reports to say local templates get no
  `template_version` line and no version comparison, and that `plugin` stays
  `null` for the same reason it does everywhere else.
- Tests added: `tests/test_materialize.py::test_a_local_template_carries_no_core_template_version`,
  `tests/test_validate.py::test_a_local_templates_declared_version_draws_no_warning`.
  Both write a real `templates/*.py` file and resolve it through
  `get_template`/`write_config` rather than faking a template class, per the
  established pattern in `test_templates.py`. The validate test declares
  `template_version: "0.9.0"` (differing from core's `TEMPLATE_VERSION`)
  under the local template, per ruling 1 — the falsy-declared shape can never
  fail against the pre-existing early return, so it proves nothing.

## Test summary

`uv run pytest -q` → 1678 passed, 2 xfailed (baseline 1676 + 2 new tests).
`uv run ruff check .` clean on all files. `uv run mypy` clean (42 source
files, no issues).

Mutation testing performed and reverted by editing files back in place
(never `git checkout`), confirmed identical to a pre-edit backup via `diff`
afterward:
- `_check_versions`: forcing unconditional `return` (suppress for every
  template) failed the `generic` control; reverting to the pre-task
  falsy-only check (`if not declared or declared == TEMPLATE_VERSION: return`
  with no locality check) failed the local half — the exact two shapes
  ruling 1 asked for.
- `materialize_config`: forcing `local = True` unconditionally failed the
  `generic` control (missing `template_version`); forcing `local = False`
  unconditionally failed the local half (`template_version` present when it
  shouldn't be).

## Concerns

- `uv run ruff format --check .` reports 42 files needing reformatting,
  including all four files this task touched — confirmed via `git stash` to
  be **identical at baseline commit `92a34d3`**, i.e. pre-existing
  environment/formatter drift unrelated to this task, not something
  introduced here. I did not run a repo-wide `ruff format .` write, since
  that would reformat ~40 files this task never touched; `ruff check`
  (lint) and `mypy` are both clean. Flagging this rather than silently
  either fixing it (out of scope) or hiding it.
- No other callers of `materialize_config` exist beyond
  `generators/experiment.py`, which already threads the resolved template
  instance through — no signature changes were needed there.

## Amendment after code review (commit `f4c1366`)

The coordinator overrode the reviewer's suggested remedy for finding 1 below
and specified the fix directly; items 2 and 3 were accepted as the reviewer
raised them.

**1 — `is_local_template` fail-open on a helper-defined class, fixed by a
stamp instead of a docstring narrowing.** The predicate read the
`_publishable_local_` prefix off `cls.__module__`, but `_module_name` only
ever synthesizes that prefix for the non-`__`-prefixed file `discover_local`
imports directly. A `BaseTemplate` subclass *defined* in `templates/
__helper.py` and merely imported and `@register_template`-ed from
`templates/my_assay.py` keeps the helper's real module name (`__helper`),
so the old predicate called it non-local — core's `template_version` would
be written and compared against it, the exact false claim this task exists
to remove. Fixed per the coordinator's chosen remedy: `discover_local` now
`setattr`s a marker (`_LOCAL_MARKER = "_publishable_local_template"`) on
every class it accepts, at the one site (`for name, cls in registered:`)
that already knows the answer regardless of where the class was defined.
`is_local_template` now reads `getattr(cls, _LOCAL_MARKER, False)`.
`GenericTemplate` is never stamped, so builtins still read `False`; the
stamp is set fresh on every `discover_local` call against fresh class
objects, so nothing carries over between repos in one process. No
`get_template` signature change was needed. The docstring on
`is_local_template` was rewritten to describe what the code now checks.

  Added `tests/test_materialize.py::test_a_template_class_defined_in_a_dunder_helper_is_still_local`,
  which defines `MyAssay` in `templates/__helper.py` and registers it from
  `templates/my_assay.py`, then asserts the rendered config carries no
  `template_version`. Confirmed it FAILS against the reverted (module-prefix)
  predicate, and separately FAILS (along with the pre-existing local test)
  when the `setattr` stamping line is removed — both reverted in place, `diff`
  confirmed identical to pre-edit.

**2 — the field count near § The one config file.** "The four identifying
fields above `metadata`" is now qualified: "three for a config generated
against a project-local template, which `init` writes with no
`template_version` at all." One clause, no other count phrase nearby needed
touching (the later "All four are inside `parameters_hash`" describes the
hashing rule over the full-expansion schema, not a per-config count, so it
stands).

**3 — an integration test for the `init`-shaped case.** Added
`tests/test_validate.py::test_a_generated_local_config_validates_with_no_version_finding`:
materializes a local-template config via `materialize_config` (not a
hand-declared `template_version`), writes it to `git_repo/configs/
cohort-pilot/config.yaml`, runs it through `validate_config`, and asserts
the finding set is exactly `{"E-META-REQUIRED"}` (the placeholder
`metadata.description`/`metadata.authors` gaps every `init`-written config
leaves) with no `W-TEMPLATE-VERSION` and no other `*VERSION*` code. Mutated
by forcing `materialize.py`'s `local = False`: the test's own
`assert "template_version" not in yaml.safe_load(text)` failed, confirming
it is load-bearing. Reverted in place, `diff` confirmed identical.

**Verification after the amendment:** `uv run pytest -q` → 1680 passed, 2
xfailed (1678 + 2 new tests). `uv run ruff check .` and `uv run mypy` both
clean. Committed as `f4c1366` on top of `6b62b95`, per "your call" — kept as
a separate commit rather than amending, so the review trail stays visible.

## Second amendment: the marker leaked onto a class the repo doesn't own (commit `e99e50f`)

The coordinator reproduced a narrower fail-open in `f4c1366`'s own fix:
`setattr(cls, _LOCAL_MARKER, True)` in `discover_local`'s registration loop
ran over **every** class in `registered`, including one a `templates/*.py`
merely imported and registered without defining — core's own
`GenericTemplate`, or later an installed plugin's. Reproduced exactly as
given, against `f4c1366`, before touching anything:

```
before: generic is_local = False
AFTER : generic is_local = True
```

A repo whose `templates/my_assay.py` does
`register_template("sneaky")(GenericTemplate)` flips
`is_local_template(GenericTemplate)` permanently for the rest of the
process, since `GenericTemplate` is a shared class object, not a fresh one
per `discover_local` call — every later repo's `generic` would then skip
`W-TEMPLATE-VERSION` too. This is the same defect class as finding 1 in the
prior round (a fact recorded on an object that outlives the thing that
recorded it), one level down.

**Why the coordinator's literal instruction ("look up
`sys.modules.get(cls.__module__)` ... in `discover_local`, after
`_import_file` returns") does not work as stated, and what I did instead.**
I probed this before implementing: `_import_file`'s own `finally` deletes
the local `sys.modules` entries it added (the file's own module under its
synthetic name, and any `__`-prefixed helper the file imported) *before it
returns* — that is the whole point of "leaving `sys.modules` as found" the
existing docstring already claims. So by the time `discover_local`'s
registration loop runs (strictly after `_import_file` returns), doing
`sys.modules.get(cls.__module__)` finds **nothing** for a genuinely local
class either — both the direct-definition case and the helper case — and
finds the **real, still-cached module** for an external class like
`GenericTemplate`'s (`publishable.templates.builtin.generic`, never
purged because it isn't under `templates_dir`). Checking at that point
would invert the answer, not just fail to distinguish it: confirmed with a
throwaway probe script before writing any fix.

So I moved the check to the one place it can still see the evidence:
inside `_import_file` itself, immediately after `exec_module` succeeds and
*before* its own `finally` purges `sys.modules`. `_import_file` now drains
the pending buffer itself, stamps each registration whose *own* defining
module (`sys.modules.get(cls.__module__)`, looked up while it's still
present) passes the existing `_is_local` predicate, and returns the
`(name, cls)` pairs to `discover_local` — already correctly marked.
`discover_local`'s own registration loop no longer stamps at all; a comment
there says why not. This reuses `_is_local` exactly as instructed ("you
already have the predicate... do not write a second answer") — the
restructuring is only about *when* it runs, not a new answer to the
question.

Verified both shapes together:
- The **helper case** (`templates/__helper.py` defining `MyAssay`,
  registered from `templates/my_assay.py`) still stamps `True` —
  `tests/test_materialize.py::test_a_template_class_defined_in_a_dunder_helper_is_still_local`
  still passes.
- The **leak case** no longer fires —
  `tests/test_templates.py::test_registering_a_class_a_repo_does_not_own_does_not_mark_it_local`
  (new) passes against the fix and confirmed to **fail** against `f4c1366`
  (ran it with only `discovery.py` stashed back to that commit, via `git
  stash push -- src/publishable/templates/discovery.py`, then popped).
- Mutated the fix itself: replaced the `_is_local` guard with `if True:`
  (stamp unconditionally, i.e. `f4c1366`'s shape restructured) — the leak
  test fails, the helper test still passes (since unconditional stamping
  happens to still mark the helper case local too — the leak test is what
  actually distinguishes the two). Reverted in place, `diff` against a
  pre-mutation backup confirmed identical.

I took the coordinator's "minimal change" option for the open judgment
call: a class a repo registers without owning is silently left unstamped
(treated as non-local, gets the ordinary `template_version` check) rather
than refused as a new `E-TEMPLATE-LOAD` shape — no new refusal surface, no
document change needed for it.

**Verification:** `uv run pytest -q` → 1681 passed, 2 xfailed (1680 + 1 new
test). `uv run ruff check .` and `uv run mypy` both clean. Committed as
`e99e50f`.

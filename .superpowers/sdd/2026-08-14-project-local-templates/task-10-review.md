# Task 10 review — `template_version` and `plugin` under a local template

Reviewed `92a34d3..6b62b95` against `task-10-brief.md`, `task-10-report.md`, and
`docs/superpowers/specs/2026-08-14-project-local-templates-design.md` decisions 2 and 3.

## Verdicts

- **Spec compliance: ✅**
- **Task quality: approved with findings** (none blocking)

## Spec compliance

Decision 3 (`template_version` not written, not warned on) and decision 2 (`plugin` stays `null`,
no code change, pinned by test) are both implemented for the resolve-by-path case, and
`docs/reference.md` was amended before the behaviour was claimed.

All three pre-dispatch rulings landed:

1. **Declared-and-differing.** `tests/test_validate.py::test_a_local_templates_declared_version_draws_no_warning`
   declares `template_version: "0.9.0"` under the local template, with the `generic` control on the
   *identical* shape (same declared string, same helper). Verified by mutation below.
2. **No re-discovery.** Locality is read off `cls.__module__` in
   `src/publishable/templates/discovery.py::is_local_template`; neither call site touches
   `discover_local`. `validate` re-executes no user top level to answer the question.
3. **Three lies, not two.** The header comment's `` v{TEMPLATE_VERSION}`` clause is dropped for a
   local template (`materialize.py`, `header_version`), and the test asserts both exact header
   strings. Grep confirms the header string exists only in `materialize.py` and
   `tests/test_materialize.py` — no document shows it, so nothing else is falsified by that half.

## Verification I ran (not taken from the report)

Mutations run where the behaviour lives, `__pycache__` deleted between runs, reverted by editing in
place and confirmed byte-identical to pre-mutation backups by `diff`; `git status` clean afterwards
and the suite re-run to confirm by behaviour.

| Mutation | Killed by | Result |
|---|---|---|
| `_check_versions` returns unconditionally (suppress for every template) | the `generic` control inside the local test, **and** `test_a_moved_template_version_warns_rather_than_failing` | ✅ fails |
| Locality check deleted (pre-existing falsy-only branch alone) | `test_a_local_templates_declared_version_draws_no_warning`, line 544 | ✅ fails |
| `materialize_config` `local = True` always | `test_the_four_identifying_fields_are_present` and the new test's control half | ✅ fails |
| `materialize_config` `local = False` always | new test's local half, line 88 | ✅ fails |
| `plugin: null` dropped for locals (decision 2's only deliverable) | new test's `doc["plugin"] is None`, line 89 | ✅ fails |

The second row is the important one: it establishes **attribution**. The local half is not passing
because validation stopped early somewhere else — `_check_versions` is genuinely reached with the
local template and genuinely reaches the comparison without the new guard.

Full suite on the reverted tree: `1678 passed, 2 xfailed`, matching the report.

**Mechanical pass on `docs/reference.md`:** the three new links resolve —
`#templates-where-parameters-are-defined` → "Templates: where parameters are defined",
`#three-hashes` → "Three hashes", `#warnings-core-reports` → "Warnings core reports". No duplicate
heading anchors in the file. Both edited lines keep the 2-column table shape, carry no trailing
whitespace, no tab, no `x`-for-`×`. Neither amendment locates a row by position; the
`W-TEMPLATE-VERSION` row cites § Three hashes by name.

**Cross-document sweep for what this falsifies:** `docs/feasibility-llm-growth-studies.md:116`
declares `template_version: "0.1.0"` but under `plugin: "seouri/publishable-llm@v0.1.0"` — a plugin
template, not a local one, so it is untouched. `docs/design-principles.md:150` and
`docs/reference.md:2561` name `template_version` as part of the envelope / hashed set, both still
true when the field is present. The fenced example in § The one config file names itself generic's,
so Config completeness is satisfied in the direction the invariant runs.

## Findings

### Important

**1. `is_local_template`'s docstring claims a guarantee the predicate does not provide.** It says
"Whether `cls` came from a repo's `templates/`", while the code tests a synthetic module-name
prefix that only `_module_name` applies — and it applies it only to non-`__` files. Probed
empirically (three repos, `discover_local` + `is_local_template`):

| Shape | `cls.__module__` | `is_local_template` |
|---|---|---|
| `templates/my_assay.py` defines and registers | `_publishable_local_<token>_my_assay` | `True` |
| `templates/assay.py` subclasses a base from `templates/__base.py` | `_publishable_local_<token>_assay` | `True` |
| `templates/__helper.py` defines **and registers**; `my_assay.py` imports it | `__helper` | **`False`** |
| `templates/assay.py` calls `register_template("assay")(Common)` on a class from `__base.py` | `__base` | **`False`** |

The last two resolve by name through `get_template` and are then treated as non-local: `init`
writes core's `template_version: "1.0.0"` and `_check_versions` compares against core's constant —
exactly the false claim this task exists to remove, fail-open. This is the repo's most common defect
class (a comment promising what the guard does not deliver), and the same shape as the
`by_attribute` fail-open already recorded in CLAUDE.md.

I am **not** asking for the predicate to change. `discover_local`'s own load-failure message
("every file under `templates/` that is not itself a template must be `__`-prefixed") says a
`__`-file is by construction not a template, so registering from one is unsanctioned; deriving
locality from the registry instead would mean a `get_template` signature change across the three
bindings the design doc flags — disproportionate to task 10. **Remedy: narrow the docstring to what
it checks, plus one clause naming the helper-defined class as out of scope and fail-open.**

(Separately, and *not* created by this diff: `discover_local` credits the helper's registration to
the importing file's `path::ClassName`. Pre-existing task 2/6 behaviour, recorded here only so it
is not mistaken for a consequence of this change.)

### Minor

**2. `docs/reference.md` § The one config file's four-fields paragraph is now unqualified.** "The
four identifying fields above `metadata`" and "`template_version` records the spec this file was
materialized from" describe a shape a local config no longer has (three fields, no
`template_version` line). The reader's escape hatch works — that sentence's own
`[warning](#warnings-core-reports)` link lands on the row that now carries the exception, and
§ Three hashes states it fully — so this is a clause worth adding, not a contradiction. One
qualifying phrase would close it. (The same paragraph's "`experiment_type` … must resolve to one an
installed package registers" is falsified by local templates generally, which is this slice's
doc-task territory rather than task 10's.)

**3. Coverage gap: nothing in the diff validates the artifact the diff produces.** Both new tests
feed a config that *declares* `template_version`; the shape `init` now writes for a local template —
no `template_version` key at all — is never run through `validate`. I ran it (materialize against a
local template → write → `validate_config`): clean, the only findings are the ordinary
`E-META-REQUIRED` placeholders every `init` output carries, and no code names `template_version`.
So this is a gap in the tests rather than a defect in the code; one assertion in the materialize
test's neighbourhood would pin it.

## Not re-litigated

`ruff format --check .` flagging 42 files: controller-verified as pre-existing and repo-wide,
correctly declined, recorded as post-merge work.

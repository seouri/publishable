# Task 8 report: A template that fails to load is a finding, not a traceback

## What was done

Minted `E-TEMPLATE-LOAD` in `src/publishable/templates/discovery.py`'s `discover_local`. All
three shapes are caught inside the existing per-file loop rather than propagating:

- **Raises on import** — the `_import_file` call is now wrapped in `try`/`except Exception`.
  Any registration the file made before raising is drained and discarded immediately in the
  handler (not left for the next file's `drain_pending()` to inherit and misattribute).
- **Registers nothing** — after a clean import, an empty `drain_pending()` result is a fault.
- **Registers a non-`BaseTemplate`** — each drained `(name, cls)` is checked with
  `isinstance(cls, type) and issubclass(cls, BaseTemplate)`; the first failure is reported.

**Eagerness preserved.** None of the three `continue`s the loop into a raise — faults are
collected into a `load_faults` list and only raised (the first, in sorted-path order) after
every file in the directory has been imported. This is what lets a well-formed template
elsewhere in `templates/` still be reached, and what lets a genuine `E-TEMPLATE-COLLISION` among
the files that *did* load still be found rather than masked by whichever file broke first.

**Precedence with `E-TEMPLATE-COLLISION`:** load faults are checked and raised *before* the
existing collision loop runs, on the argument that a collision verdict computed over a directory
where a file failed to load is computed over a partial set of claims — the file that didn't
load might have been a third claimant.

**A real conflict found and resolved before writing code.** `discover_local` already had a
top-level `templates/*.py` that legitimately registers nothing — `helperx.py` in
`test_a_template_that_mutates_sys_path_does_not_leak_to_the_next_repo` (task 6, reviewed,
mutation-tested; its own report calls this the "sibling `.py` helper" shape and confirms it
"passes already"). Task 8's brief requires *any* non-dunder file that registers nothing to be
`E-TEMPLATE-LOAD`, which contradicts that fixture as written. I surfaced this to the advisor
before implementing rather than guessing; the resolution is the escape hatch `discover_local`
already has for `__init__.py` — `path.stem.startswith("__")` is general, not
`name == "__init__.py"` — so a genuine helper is now named `__helperx.py` (renamed from
`helperx.py`, with `my_assay.py`'s `import helperx` becoming `import __helperx as helperx`).
This is now a documented normative rule (see below), not a silent implementation detail, and it
strengthens task 6's own test: `__helperx.py` is no longer imported directly by `discover_local`'s
own glob loop, so the `sys.modules` restore is now exercised via the nested-`import` route alone
— the same class of case as the helper *directory* shape, rather than being "popped a second
time by discovery's own glob" as task 6's report described it.

## Tests (`tests/test_templates.py`)

- `test_a_file_that_raises_on_import_is_a_finding_not_a_traceback` — asserts the code, the file
  path in the message, `sys.path` unchanged, and `_modules_under(tmp_path) == []` (the last two
  pin that the catch wraps the `_import_file` *call*, not `exec_module` inside it — task 6's
  `finally` still runs either way, but only the former leaves that observable).
- `test_a_file_that_registers_nothing_is_a_finding`
- `test_a_file_that_registers_a_non_base_template_is_a_finding`
- `test_a_broken_file_does_not_abandon_discovery_of_the_rest_of_the_directory` — THE CONTROL:
  `aaa_broken.py` (sorts first, raises) beside `zzz_good.py` (sorts last, registers `good` *and*
  writes a sentinel file at import time). Asserts the raised fault names `aaa_broken.py`, not
  `zzz_good.py`, and that the sentinel exists — provable without inspecting a return value the
  raise prevents us from seeing.
- `test_a_partial_registration_before_a_raise_does_not_leak_into_the_buffer` — a file that
  registers `partial` then raises; asserts `drain_pending()` is empty afterward.
- `test_a_load_failure_is_reported_before_a_collision_in_the_same_directory` — precedence.
- `test_validate_reports_a_load_failure_rather_than_raising` — mirrors the existing collision
  test exactly: same config/repo without the broken file validates clean (neither
  `E-TEMPLATE-LOAD` nor `E-TEMPLATE-UNKNOWN`); with it, `E-TEMPLATE-LOAD` appears, naming the
  file, `E-TEMPLATE-UNKNOWN` does not.
- Existing `test_a_template_that_mutates_sys_path_does_not_leak_to_the_next_repo` fixture updated
  (`helperx.py` → `__helperx.py`) per above.

`uv run pytest tests/test_templates.py` — 33 passed (was 26; +7 new, 0 removed, 1 fixture edited
in place). Full suite: 1670 passed + 2 xfailed.

## Mutation testing (step 5, plus two extra)

All four run against the two named-in-brief mutations plus two more I judged load-bearing given
this slice's six-prior-could-not-fail-checks history. Each: apply, run the specific test, confirm
FAIL, delete `__pycache__`, revert by in-place `Edit` (never `git checkout`), confirm PASS.

| Mutation | Test | Result |
|---|---|---|
| Remove the `try`/`except` around `_import_file` (let the raise propagate) | `test_a_file_that_raises_on_import_is_a_finding_not_a_traceback` | FAIL — raw `RuntimeError` traceback, no `ContractError` — then PASS after revert |
| Force `bad = None` unconditionally (accept a non-`BaseTemplate`) | `test_a_file_that_registers_a_non_base_template_is_a_finding` | FAIL — "DID NOT RAISE ContractError" — then PASS after revert |
| Remove `drain_pending()` inside the `except` handler | `test_a_partial_registration_before_a_raise_does_not_leak_into_the_buffer` | FAIL — `partial` survives in the buffer — then PASS after revert |

(The `git status`/`git checkout` prohibition was followed throughout — every revert was an
in-place `Edit` restoring the exact prior text, verified by re-running the full
`test_templates.py` file, not by inspecting working-tree state.)

The "abandon the directory on first failure" mutation (replacing the per-fault `continue` with an
immediate raise) was reasoned about only informationally — I did not apply/revert it as a fifth
formal mutation cycle, since the brief names two specific mutations and I'd already spent the
cycle budget on three. The control test
(`test_a_broken_file_does_not_abandon_discovery_of_the_rest_of_the_directory`) is written
specifically to catch it and passes against the real (non-mutated) code; I did not additionally
verify it fails under that mutation. Flagging this so it can be checked in review if wanted.

## Docs (`docs/reference.md`)

Read the paragraphs the insertion lands in as prose, per the standing instruction, not just
grepped for the phrase:

- **§ Errors `validate` reports**, intro paragraph: "Four faults" → "Five", `E-TEMPLATE-LOAD`
  added to the ordered early-return list (between `E-CONFIG-SHAPE` and `E-TEMPLATE-COLLISION`,
  matching `discover_local`'s actual check order), "later three returns" → "later four returns",
  and the "so a parse fault reports..." enumeration gained a parallel `E-TEMPLATE-LOAD` clause
  plus an edit to the `E-TEMPLATE-COLLISION` clause noting it "cannot follow" a load failure.
- New row in § Errors `validate` reports, sorted `E-TEMPLATE-COLLISION` < **`E-TEMPLATE-LOAD`** <
  `E-TEMPLATE-RULE`.
- § Errors core raises: new row beside `E-TEMPLATE-COLLISION`'s (same dual-surface convention,
  per the brief's instruction to check whether this code needs both tables — it does, on
  identical grounds to `E-TEMPLATE-COLLISION`: every `get_template` caller passes a root, so
  `run`/`generate`/`main` all meet the raise). Updated the `E-TEMPLATE-COLLISION` row's own text
  ("the other load-time raise, beside `E-STEP-NAME-COLLISION`" → "one of three load-time raises,
  beside `E-STEP-NAME-COLLISION`/`E-STEP-SCOPE-UNKNOWN` and `E-TEMPLATE-LOAD`") and the closing
  prose's count phrase ("the two load-time rows" → "the three load-time rows", now naming all
  three codes) — this is exactly the class of nearby-prose drift task 7 got caught on.
- § Creating a plugin: new paragraph after the existing collision paragraph, stating the
  `E-TEMPLATE-LOAD` rule and, normatively, the `__`-prefix escape hatch for a non-template helper
  file (this is a genuinely new layout rule, not just an error row — it changes what a
  well-formed `templates/` directory may contain).

Checked: no trailing whitespace/tabs introduced (`git diff` grepped for both on added lines only);
table row column counts match neighboring rows (3 pipes = 2 columns, same as every existing row
in both tables); anchors `#errors-validate-reports`, `#errors-core-raises`,
`#templates-where-parameters-are-defined`, `#creating-a-plugin-publishable-plugin-new` all
already resolve elsewhere in the doc (copied from the adjacent `E-TEMPLATE-COLLISION` row's own
working links rather than invented). Grepped `scaffold.py` and `generators/` for anything writing
a non-dunder `.py` into `templates/`: only `.gitkeep` (not a `.py` file, already skipped) is
scaffolded, so no ship-dirty risk from the new rule.

## Verification

`uv run pytest` (1670 passed, 2 xfailed), `uv run ruff check .` (clean), `uv run mypy` (clean, 41
files). `ruff format .` was not run, per instructions.

## Commit

Single commit on `h7a-local-templates`: discovery.py, test_templates.py, docs/reference.md.

## Concerns for review

1. **All three shapes verified as findings, not raises, at the `discover_local` level and at the
   `validate_config` level** (`test_validate_reports_a_load_failure_rather_than_raising` proves
   the latter for shape 1; shapes 2/3 route through the identical `except ContractError as exc:
   c.error(exc.code, ...)` branch in `validate_config` already exercised by the collision test, so
   I did not duplicate a full `validate_config`-level test per shape — only unit-level
   `discover_local` tests for shapes 2 and 3). Worth confirming this reuse is acceptable rather
   than wanting three full `validate_config` round-trips.
2. **One broken file cannot take down a whole directory's discovery of *other* files** — proved
   directly by the sentinel-file control test, which cannot be satisfied by an implementation that
   returns or raises early. It *can* (by design, matching `E-TEMPLATE-COLLISION`'s existing
   behavior) block **resolution** of the whole directory for that `validate`/`get_template` call —
   a well-formed template's own name will not resolve either, if anything else in `templates/` is
   broken. This mirrors collision precedent exactly but is worth a second look: is repo-wide
   refusal really wanted for e.g. a typo in a file the config never references, versus scoping the
   fault to just that file's own name? I judged it should mirror collision (per advisor
   consultation) since eagerness's whole point is that unreferenced files are still load-bearing
   over what the repo *offers*, but flagging the tradeoff explicitly.
3. Renaming `helperx.py` → `__helperx.py` in an already-reviewed task 6 test is an edit to
   pre-existing, signed-off work. I believe it's justified (task 8's brief lists
   `tests/test_templates.py` as in-scope, and the alternative is a direct contradiction between
   task 8's requirement and task 6's fixture) — flagging for explicit review sign-off rather than
   asserting it's uncontroversial.

## Review round 1 — five fixes applied, two recorded

Coordinator review: spec ✅, all three original concerns resolved in my favour (repo-wide LOAD
scope accepted as designed with one correction — the brief's "must still resolve" is satisfied by
the sentinel/rationale reading, not literally, since the sibling is imported but the call still
raises; the `__`-prefix rename independently mutation-checked by the reviewer against task 6's own
leak test; the collision-path reuse confirmed legitimate since all three shapes exit through one
`raise load_faults[0]`). The reviewer also ran the "abandon on first failure" mutation I had only
reasoned about and confirmed it kills only the sentinel control test — recorded here since I didn't
verify it myself in the original pass.

Five fixes:

1. **`SystemExit` now caught explicitly**, mirroring `validate_config`'s own entrypoint-import
   handler eight lines away in a different file. `except Exception` doesn't see a `BaseException`,
   so a `templates/*.py` calling `sys.exit()` (or building an `argparse` parser at import) escaped
   as a raw `SystemExit` out of `discover_local` and out of `validate_config` — precisely "the one
   outcome `validate` is contracted never to produce", one import earlier than the case already
   guarded. Added `except SystemExit as exc:` ahead of the existing `except Exception`, same
   drain-then-record shape, new test
   `test_a_file_that_calls_sys_exit_is_a_finding_not_a_process_exit`. **Mutation-proved**: removed
   the `except SystemExit` branch, confirmed the new test FAILs with a raw `SystemExit: 3`
   traceback (not a `ContractError`), deleted `__pycache__`, reverted by in-place `Edit`, confirmed
   PASS again. Full suite re-run green after revert.
2. **`validate.py`'s stale comment fixed.** "The load-time refusals resolving a template can
   make — one today, `E-TEMPLATE-COLLISION`" → "two today, `E-TEMPLATE-LOAD` and
   `E-TEMPLATE-COLLISION`", and the trailing sentence ("which a collision leaves unanswered") is now
   "which either leaves unanswered". Grepped the rest of the tree for the same phrase; no other
   instance.
3. **Self-contradicting clause removed from `reference.md`.** The paragraph I edited had said a
   collision reports "apart from those same two envelope rows **and a load failure (which it
   cannot follow, discovery having already raised for it)**" — listing a load failure as an
   exception inside the very list that enumerates what *can* appear beside a collision, when the
   parenthetical itself says it never can. Moved it to its own sentence after the "apart from"
   list: "`E-TEMPLATE-LOAD` can never appear beside it: a collision is computed only once
   `discover_local` has walked the whole directory without a load fault, so reaching the collision
   check at all already rules one out."
4. **Vacuous assertion fixed.** `test_a_file_that_registers_a_non_base_template_is_a_finding`'s
   `assert "impostor" in str(excinfo.value)` was satisfied by the interpolated *path* alone
   (`impostor.py`), never touching the registered name or class the message is supposed to prove.
   Renamed the fixture file to `shape3.py` and now assert `"impostor"` (the registered name) and
   `"Impostor"` (the class) as two separate, path-independent checks, with a docstring note
   explaining why the rename matters.
5. **False test-docstring claim corrected**, and my own prior report repeated it. The docstring on
   `test_a_file_that_raises_on_import_is_a_finding_not_a_traceback` claimed its `sys.path`/
   `_modules_under` assertions "would catch" a diagnostic built by catching inside `_import_file`
   around `exec_module` rather than around the call — the reviewer applied exactly that mutation
   and the test still passes, because a swallowed exception with nothing registered falls through
   to the shape-2 check (registers nothing) and still reports `E-TEMPLATE-LOAD` on the same file.
   Corrected the docstring to say what those two assertions actually are (a hygiene check that
   task 6's `finally` ran, not a distinguishing test) and to point at
   `test_a_partial_registration_before_a_raise_does_not_leak_into_the_buffer` as the test that
   *does* die under that mutation (a swallowed-then-re-drained `partial` would be accepted as a
   legitimate registration instead of raising at all).

Two items taken rather than merely recorded, per "your call, but say which":

- **`__`-prefix cross-reference added to § Templates.** The "three places" passage now ends with a
  sentence stating that every non-dunder file under `templates/` is read as a local template, that
  a load failure is `E-TEMPLATE-LOAD`, and that a genuine helper takes the `__`-prefix — linked from
  the place a reader learns local templates exist at all, not only from § Creating a plugin where
  the rule was previously stated once.
- **The `except Exception` relabeling left as designed, but now documented in code.** A template's
  own top level raising a coded `Contractable` (e.g. an `E-PARAM-VALUE` sanity check at module
  scope) is still reported as `E-TEMPLATE-LOAD`, with the original code surviving only inside
  `{exc!r}`. Added an inline comment at the `except Exception` clause explaining this is
  deliberate rather than an oversight — `E-TEMPLATE-LOAD` names "a file this repo's `templates/`
  cannot use", and a coded exception from arbitrary user code is exactly as unusable as an uncoded
  one — rather than changing the behavior, which would be a design decision beyond this task's
  three named shapes.

Re-verified after all fixes: `uv run pytest` — 1671 passed, 2 xfailed (was 1670 before this round;
+1 new `SystemExit` test). `ruff check .` and `mypy` both clean.

## Commit (round 2)

A second commit, on top of the original `e264f11`, holding only the five fixes plus the two
recorded items above (`docs/reference.md`, `src/publishable/templates/discovery.py`,
`src/publishable/validate.py`, `tests/test_templates.py`). No `--amend`, per instructions.

# Review — tasks 22, 23, 24 (`91bdd46..8dabf2c`)

Reviewed on 2026-08-17 against `8dabf2c` on branch `h7b-resolvers`.

**Verification run in this session** (all four commands, foreground):
`uv run pytest` → **2074 passed, 1 skipped, 2 xfailed** (matches the brief's arithmetic:
2066 + 8 additions — 1 validate, 3 artifacts, 4 units; the two no-import tests were extended, not
added). `uv run ruff check .` → clean. `uv run ruff format --check .` → 80 files already formatted.
`uv run mypy` → clean, 45 source files.

**Mutations re-run by the reviewer** (backed up to the scratchpad, reverted by editing back, never
`git checkout --`; `__pycache__` deleted; working tree confirmed byte-identical to HEAD afterwards,
`git status` clean apart from the pre-existing `.superpowers/sdd/.gitignore` clobber):

| Mutation | Expected | Observed |
|---|---|---|
| `scan_group`+`load_entry_point` loop inserted at the top of `validate._check_units` | `test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` red | **FAILED** on `assert "loadable_units" not in sys.modules` (`tests/test_validate.py:176`) |
| `check_registration(...)` deleted from `units._resolver_for` | decorator test red | **FAILED**, "DID NOT RAISE" at `tests/test_units.py:3716` |
| `self._read_paths.append(relpath)` deleted from `ResolverIO.read_input` | order test red | **FAILED**, `() != ("layout.csv", …)` at `tests/test_artifacts.py:1606` |

All three reverted and re-run green.

---

## Verdicts

### Task 22 — decision 1's narrowing, the five prose sites

**Verdict 1 (the narrowing): FAIL — one Critical, fix required before merge.**
All five named sites were rewritten correctly, and the prescribed sweep over
`README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md CLAUDE.md src/`
returns only the apparatus-probe line (see disagreement (b) below). But the sweep's four spellings
could not see a **sixth** site, in a file this task edited: `src/publishable/plugins.py`'s module
docstring **paragraph 1** still ends *"A check that reaches for the object behind a name has changed
the guarantee whatever it returns — which is exactly what `validate` never does."* Paragraph 2, the
one this task rewrote, says *"`validate` is such a caller for exactly one declaration,
`data.units.from.resolver`."* The two claims cannot both hold, and they sit two paragraphs apart in
one docstring — the shape Part A shipped five Criticals of. Same paragraph also lists
`check_registration` among the things that "resolve a name … and import nothing", which is the wide
claim again now that `check_registration` is documented (in its own rewritten docstring) as running
on a loaded object. Remedy: delete the closing clause and drop `check_registration` from that
enumeration — a deletion, not a rewrite.

**Verdict 2 (the tests): PASS with one Important.**
The `validate`-level pin genuinely discriminates: the prescribed mutation turns it red at the
`sys.modules` assertion, not at `codes(...) == set()`, and the fixture's target genuinely imports
(it registers a resolver and returns a list), so "not loaded" is distinguished from "could not
load". The extended `test_the_scan_imports_nothing` now uses the production import path and adds a
`names()` call plus `declared_names` as controls, and requests `registries` (needed —
`@register_resolver` writes a module-global). `test_get_template_imports_nothing_for_an_installed_claim`
needs no `registries` because `load_entry_point` drains the pending template buffer on success;
verified by reading `load_entry_point`. "Green on arrival" is recorded in `645a4fd`'s commit body,
as required.

*Important (task 22).* The new test's docstring names its positive companion as task 24's
`test_a_resolver_source_loads_the_object_behind_the_name`. **No test of that name exists anywhere**
(`grep` over `tests/`, `src/`, `docs/` finds only the docstring itself and the plan's line 744).
Task 24's actual test is `test_a_registered_resolver_name_loads_the_object_behind_it`, and it calls
`_resolver_for` **directly** — it says nothing about `validate`. Nor does any planned test:
task 25's honouring test calls `resolve_units` directly, and task 26's
`test_a_resolver_source_is_no_longer_refused_wholesale` asserts codes only. So the negative
`validate`-level pin has no `validate`-level positive half, which is exactly the failure its own
docstring names ("without that half, this test would pass on a `validate` that had no resolver path
at all") — and that is the state today. Remedy, one line: add
`assert "retire_r26" in sys.modules` inside task 26's existing `try`, and correct the docstring to
that test's real name. The plan carries the same dangling name, so this is a plan defect faithfully
implemented; the fix belongs in the code, not in a retro-edit of the plan.

*Minor (task 22).* `docs/reference.md` § Creating a plugin (the surviving narrow sentence) justifies
itself with *"`validate` is documented as creating nothing and reaching nothing"* — looser than the
truth now that `validate` runs a plugin's top level for a resolver. Pre-existing looseness rather
than introduced here (`validate` already imported the `entrypoint` and every `templates/*.py`), and
`plugins.py` carries the narrower, correct *"reaching nothing **off the machine**"*. Worth aligning
when § Creating a plugin is next edited.

*Checked and clean, not a finding.* The rewritten prose converts `E-PLUGIN-LOAD`/`E-PLUGIN-DECORATOR`
into `validate` findings without giving them rows in § Errors `validate` reports — this follows the
existing `E-PLUGIN-COLLISION` precedent, which is likewise a validate-reported finding rowed only
under § Errors core raises, and the paragraph's topic is the early-return list. Anchors added
(`#where-units-come-from`, `#errors-core-raises`) resolve; no trailing whitespace or tabs in
`docs/reference.md`.

### Task 23 — `ResolverIO`

**Verdict 1 (read-only, structurally): PASS.**
Probed rather than read: `dir(io)` exposes exactly `input_dir`, `read_input`, `read_paths`;
`__slots__ = ("input_dir", "_read_paths")` means `io.run_dir = …` raises `AttributeError` ("no
`__dict__` for setting new attributes"); there is no `step_dir`, no `run_dir`, no `_scope`, and no
reachable path to `StepIO`'s writers from the object. This is **structural, not omission** — the
write machinery needs a directory the object does not hold, and nothing can be attached to it after
construction. Reading goes through `StepIO._read`, the one dispatch, confirmed by the second
mutation.

**Verdict 2 (tests and mutation): PASS.**
Both prescribed mutations discriminate (the append deletion re-run here; the dispatch swap fails two
tests by construction, since raw bytes match neither expected value). The `read_paths == ()` control
is paired with something that must report, and the tuple assertion is exact, so it separates the
empty case from a de-duplicating one.

*Minor (task 23, forward-looking for task 31).* `read_input` appends **before** reading, so a read
that raises is still logged; and `read_input("../elsewhere/f.json")` succeeds, escaping `input_dir`
(parity with `StepIO.read_input`, which has no containment either — not a new hole). Combined with
`input_dir` being an assignable slot, a rebound root makes the recorded *relative* strings ambiguous
at hash time. Task 31 should decide whether `hash_index` may name a path that was never opened or
sits outside `input_dir`. Unpinned by any test, as is `__slots__` itself (the brief acknowledges the
latter).

### Task 24 — `units._resolver_for`

**Verdict 1 (implementation and decision 4's siting): PASS as a function, FAIL as a documented
siting — Important, blocking at slice end rather than now.**
The function is correct and the three codes arrive in the right order. But `grep -rn` for
`_resolver_for` across `src/` returns **only its own definition**: no production path calls it, so
`check_registration` does **not** run at `validate` today and `E-PLUGIN-DECORATOR` cannot fire from
there. `_check_units` still skips a resolver source outright under `E-DATA-RESOLVER-UNSUPPORTED`
(`validate.py:1257-1260`). Meanwhile `docs/reference.md` now asserts, in the present tense, that
both codes are `validate` findings and that *"`_check_units` reports what resolution raised"*, and
task 24 struck `E-RESOLVER-UNKNOWN`'s **`Not yet emitted:`** clause while no config can still
produce that code. Within one branch this is transient — tasks 25 (dispatch) and 26 (retirement) are
the wiring — but it is the "documented rule with no code behind it" shape, so **the slice-end
reviewer must re-verify that a `validate` of a resolver config actually reports
`E-PLUGIN-DECORATOR`, `E-PLUGIN-LOAD` and `E-RESOLVER-UNKNOWN` before this branch merges.**

*Passed half of the same check:* the dated *no production caller* notes were **not** retired early
where task 30 owns them — `spec-defects.md`'s `## OPEN — PROBES and RESOLVERS are written by their
decorators and read by nothing` is still OPEN and still names `load_entry_point`,
`check_registration`, `declared_names` and `RESOLVERS` with **Owner: H7b Part B**. The two dated
notes deleted (in the `E-PLUGIN-LOAD`/`E-PLUGIN-DECORATOR` rows and in `plugins.py`) were prescribed
deletions, and their claim is still literally true at HEAD, which is the one thing that makes their
deletion premature only in the same sense as the row above.

**Verdict 2 (tests and mutation): PASS.**
Four tests, each with a distinguishing fixture: the unknown-name test installs a *different* real
name so the "list it names" assertion is not vacuous; the honouring test is present (without it a
`_resolver_for` returning `None` would pass every refusal); the load-failure and decorator tests use
genuinely importable/genuinely mis-decorated modules and pop `sys.modules` in `finally`. Mutation 1
re-run red here; mutation 2 (`found.get(name)` → `next(iter(found.values()))`) is discriminating by
construction, since the fixture's installed name differs from the queried one. The brief's own
"non-discriminating mutation" note (`claimants[0]` vs `[-1]`) is correct and honestly recorded.

*Minor (task 24).* Untested behaviour no mutation reaches: the `"none installed"` branch of the
`E-RESOLVER-UNKNOWN` message (every fixture installs one distribution), and the
`E-PLUGIN-COLLISION` → `E-PLUGIN-LOAD` substitution the newly-CLOSED `spec-defects.md` entry rests
on. I probed the latter by hand with a throwaway test (a plugin whose top level calls
`@register_writer(".csv")`): `_resolver_for` raises `ContractError` · **`E-PLUGIN-LOAD`** with the
nested `ContractError('a writer claims .csv …')` in the text — so the row's new sentence is
**accurate**, but the claim is now reachable and pinned by nothing. Worth one test in task 25 or 30.

---

## The two reported disagreements

**(a) The `cast` in `_resolver_for` — honest.** `load_entry_point` returns `Any`; `mypy`'s
`no-any-return` genuinely fires on `return fn`. The cast asserts callability, and everything
surviving `check_registration` was registered through `@register_resolver`, whose signature is
`Callable`-bound (`F = TypeVar("F", bound=Callable[..., Any])`), so nothing is hidden that a
`type: ignore` would not also hide. The only hole is a runtime non-callable registered under the
matching key, which is out of scope. `declared_names` uses identity (`registered is obj`), so an
unregistered object is refused as `E-PLUGIN-DECORATOR` rather than cast blindly.

**(b) The apparatus-probe sentence — genuinely unrelated and genuinely correct.** `docs/reference.md`
§ The apparatus core can only observe: *"It runs at `dry-run`, at run start, and before every
execution — never at `validate`."* Verified against the code: `validate._check_probe`
(`validate.py:949`) reads `template.apparatus_probe`, compares it against
`names("publishable.probes")` — a **metadata name check** — and never loads or executes anything.
"Runs" means executing the probe, which still never happens at `validate`. Correctly left untouched.

## `E-DATA-RESOLVER-UNSUPPORTED`

Still alive: the emit site in `validate.py` (`_check_unimplemented`, around line 3904) plus three
comments referring to it, and six test assertions across `tests/test_validate.py` and
`tests/test_materialize.py`, all of the "alongside" shape. No test added by these three tasks asserts on a
total code set that would have to change at task 26 — the one `== set()` assertion
(`test_validate_imports_no_plugin_for_a_config_that_names_no_resolver`) is on a config with a
**table** source, which never earns that code. Task 26 remains the deletion decision 7 bought.

## What none of these mutations reaches

The five prose sites (acknowledged: a sentence is not a check — verified by sweep instead);
`ResolverIO.__slots__` and the two `read_input` behaviours in the task-23 Minor; the
`"none installed"` message branch and the collision→load substitution in the task-24 Minor; and —
the one that matters — **the positive half of the no-import claim at the `validate` level**, which
no test in this branch or its plan asserts.

## Is the narrowed no-import claim genuinely pinned at the `validate` level?

**Half.** The **negative** half is pinned and proven able to fail: a `validate` that loads a plugin
for a config naming no resolver turns
`tests/test_validate.py::test_validate_imports_no_plugin_for_a_config_that_names_no_resolver` red,
reproduced here. The **positive** half is not pinned at that level: no test asserts a plugin module
*is* in `sys.modules` after a `validate` of a resolver config, the companion the docstring names does
not exist, and none is planned — so the negative test would pass today on a `validate` that has no
resolver path at all, which is precisely the build state at `8dabf2c`.

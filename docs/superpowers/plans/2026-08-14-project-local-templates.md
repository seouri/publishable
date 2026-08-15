# H7a Project-local Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a template written into `templates/` in a project's own repo is **found**, so `experiment_type: my_assay` resolves with no package installed — the third of the three homes `reference.md` § Templates already specifies, and the only one with nothing behind it.

**Architecture:** `get_template` and `template_names` gain an **optional repo root** and build their mapping **per call**, merging core's builtins with whatever `templates/*.py` registers. Discovery is **eager** — every file in the directory is imported, because a collision must be caught whether or not the config names either file. The decorator drains into a **transient** collection, never a module-level dict, so two projects in one process cannot cross-contaminate.

**Tech Stack:** Python 3.12+, `uv`, pytest, ruff, mypy. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-14-project-local-templates-design.md`
**Measurement:** `docs/superpowers/H7a-SCOPING.md`

## Global Constraints

Every task's requirements implicitly include this section.

- **The documents lead the code.** Where code cannot follow, **the document changes first**; where the code is wrong, record the gap rather than editing a document to describe code that does not exist. **Not in `docs/superpowers/spec-defects.md`** — it is gitignored and does not survive a merge.
- **`validate` collects findings and never raises.** User code failing on import must be a **finding**, not a traceback.
- **Importing is not inspecting.** Core still never reads the body of user Python. This slice widens a documented promise (`validate` importing files no config references) and **owes the sentence that says so**.
- **Assert exact numbers and strings, not directions**, and **every probe needs a control that must report.** Sixteen checks across the two H3c slices could not fail, every one caught by a mutation and none by reading. **Run the mutation before believing the test, and run it where the behaviour lives.**
- The shapes that have survived a full suite in this project, so you can ask whether your own tests are one of them: a fixture whose numbers agree with the bug; a dimension no assertion can see; an assertion implied by another in the same test; a control asserting only absences; **a parametrized test asserting a failure for both arms**, which proves nothing about either arm's success path; **testing the refusal but never the honouring**.
- **Mutation testing is never reasoned about.** Apply, run the named test, confirm FAIL, revert, confirm PASS. **Delete `__pycache__` between mutation and revert**; **verify reverts by behaviour, never `git status`**.
- **Never write a phrase locating a table row by position.** Seven instances in this project, wrong twice, once in a row no diff touched. Name what a sibling row *does*; when you insert or remove a row, check every row it **moved** and every count phrase near it.
- **Never filter the output of a sweep whose job is to find a string** — filter the file list.
- `uv run pytest`, `uv run ruff check .`, `uv run mypy` green. **Do not run `ruff format .`** — repo-wide, pre-existing, out of scope.
- Cite by section, never line number; `×` not `x`; **hyphen never an en dash** in anything becoming a filename or anchor.
- **The worked example `cohort-pilot` may not move**: 240/228/12; r = 0.581 / 0.607 / 0.412; delta 0.026, ci95 [−0.007, 0.059]; kendall −0.169, [−0.213, −0.125]; `repeat_spread` std 0.014; hashes `8e21`/`1a2b`/`3d8a`/`6b1f`; README's demo `2f5c8d0`.

---

## Verified interfaces — read from the code before any task was written

| Site | Fact |
|---|---|
| `templates/registry.py` | **15 lines total.** `_BUILTIN: dict[str, type[BaseTemplate]] = {"generic": GenericTemplate}`; `get_template(name: str) -> BaseTemplate \| None` returns `cls()`; `template_names() -> list[str]` returns `sorted(_BUILTIN)` |
| `BaseTemplate` members | `naming_pattern`, `field_convention`, `default_repeats`, `required_env`, `apparatus_probe`, `apparatus_facts`, `parameter_spec`, `validate`, `aggregate`. **Five are live** — `parameter_spec`, `validate`, `aggregate`, `naming_pattern`, `default_repeats`. The other four are read by nothing |
| `get_template` call sites | `validate.py` (the template check), `cli.py` (the `aggregate` block), `generators/experiment.py`. **`template_names()` is called inside the `E-TEMPLATE-UNKNOWN` message** |
| Test bindings that break on a signature change | `tests/test_templates.py` ×3 (including `get_template("llm_diagnostic") is None`, which asserts the closed set **by name**), `tests/test_materialize.py` ×2, and `tests/test_validate.py`'s `monkeypatch.setattr(validate_mod, "get_template", lambda name: RuleBreaker())` — **a one-argument lambda** |
| `provenance.find_repo_root(start: Path) -> Path` | raises `ContractError` when there is no repo |
| `base_experiment.load_experiment` | **The precedent for path import and for the purge**: it deletes the root package from `sys.modules` because "two projects in one process can declare the same package name … and a cached module would silently hand back the other project's steps", then inserts `repo_root / "src"` on `sys.path` inside a `try`/`finally` |
| Already built, do not touch | `hashes.HASHED_TREES = ("src", "templates")` and the `E-CODE-DIRTY` gate over both trees. This slice makes them load-bearing; it does not build them |

**New identifiers this plan introduces:** `E-TEMPLATE-COLLISION`, `E-TEMPLATE-LOAD`, and `src/publishable/templates/discovery.py`.

---

## Task 1: `register_template`, and the decorator that is the whole registration

**Files:** Create `src/publishable/templates/discovery.py`; Modify `src/publishable/__init__.py`; Test `tests/test_templates.py`

**Produces:** `register_template(name: str)` — a decorator returning the class unchanged, recording `(name, cls)` into a module-level *pending* list that discovery drains. Exported from `publishable` and in `__all__`.

- [ ] **Step 1: Write the failing test**

```python
def test_register_template_returns_the_class_and_records_the_name():
    """§ Creating a plugin: a local template's `@register_template` argument
    "is therefore the whole of its registration". The decorator must return the
    class unchanged — a decorator that returned the registration record would
    break `class X(BaseTemplate)` for every later reference to X."""
    from publishable import register_template
    from publishable.templates.discovery import drain_pending

    @register_template("my_assay")
    class MyAssay(BaseTemplate):
        pass

    assert MyAssay.__name__ == "MyAssay"          # returned unchanged
    assert issubclass(MyAssay, BaseTemplate)
    assert drain_pending() == [("my_assay", MyAssay)]
    assert drain_pending() == []                  # draining empties it
```

- [ ] **Step 2: Run it and confirm it fails** on the import, not on an assertion.
- [ ] **Step 3: Implement** the decorator and `drain_pending()`. The pending list is module-level; **the registry mapping is not** — that is task 6's property and this task must not pre-empt it by keeping a persistent name→class dict.
- [ ] **Step 4: Export** from `publishable/__init__.py` and add to `__all__`.
- [ ] **Step 5: Mutate** — make the decorator return the record rather than the class; the first assertion must fail. Then make `drain_pending` not clear; the last assertion must fail.
- [ ] **Step 6: Commit.**

---

## Task 2: Eager path discovery

**Files:** Modify `src/publishable/templates/discovery.py`; Test `tests/test_templates.py`

**Consumes:** `register_template`, `drain_pending` (task 1).
**Produces:** `discover_local(repo_root: Path) -> dict[str, type[BaseTemplate]]` — imports **every** `templates/*.py` under the root and returns what they registered.

**Eager, and the reason is in the documents.** § Creating a plugin: a collision fails "at load, naming both providers", because *"install order and import order are the only tie-breaks available, and both are properties of a machine rather than of a design."* **Lazy discovery makes import order decide which template you get.** So every file is imported, not only the one the config names.

- [ ] **Step 1: Write the failing tests**

```python
def test_discovery_imports_every_file_not_only_the_named_one(tmp_path):
    """Two files, and the config names neither. Both must register, or a
    collision between them could not be detected — which is the whole reason
    discovery is eager rather than lazy."""
    # write templates/alpha.py and templates/beta.py, each registering one name
    found = discover_local(tmp_path)
    assert sorted(found) == ["alpha", "beta"]

def test_discovery_ignores_non_python_and_dunder_files(tmp_path):
    """The scaffold puts `.gitkeep` in `templates/`. THE CONTROL: a real
    template beside it must still be found, so a discovery that returned {}
    for everything fails here rather than passing both assertions."""
    # .gitkeep, __init__.py, notes.md, and one real template
    found = discover_local(tmp_path)
    assert sorted(found) == ["real_one"]

def test_discovery_with_no_templates_directory_is_empty_not_an_error(tmp_path):
    assert discover_local(tmp_path) == {}
```

- [ ] **Step 2–4:** Fail, implement, pass. Import by path, following `load_experiment`'s shape — `try`/`finally`, and drain after each file.
- [ ] **Step 5: Mutate** — import only the file matching a requested name (the eager test fails); include `.gitkeep` (the second fails). **Note the second test's control**: it must find `real_one`, so an implementation returning `{}` fails rather than passing the "ignores junk" half.
- [ ] **Step 6: Commit.**

---

## Task 3: The registry takes an optional repo root and merges per call

**Files:** Modify `src/publishable/templates/registry.py`; Test `tests/test_templates.py`, `tests/test_materialize.py`, `tests/test_validate.py`

**Consumes:** `discover_local` (task 2).
**Produces:** `get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None` and `template_names(repo_root: Path | None = None) -> list[str]`.

**Three test bindings break, and a partial change fails collection rather than a test** — which reads as a broken suite rather than a failing assertion. Update all of them in this task: `tests/test_templates.py` ×3, `tests/test_materialize.py` ×2, and `tests/test_validate.py`'s `lambda name: RuleBreaker()`, which takes **one** argument.

**`tests/test_templates.py`'s `get_template("llm_diagnostic") is None` asserts the closed set by name.** Decide whether it still means anything and say so — with a repo root it is no longer a statement about the world.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_local_template_resolves_by_name(tmp_path):
    """The headline. THE CONTROL: `generic` still resolves from the same call,
    so a change that replaced builtins with locals fails here."""
    # tmp_path/templates/my_assay.py registers "my_assay"
    assert get_template("my_assay", tmp_path) is not None
    assert get_template("generic", tmp_path) is not None

def test_without_a_repo_root_only_builtins_resolve(tmp_path):
    """No root → local discovery is skipped, `generic` still resolves. This is
    the behaviour task 4's hoist depends on."""
    assert get_template("my_assay") is None
    assert get_template("generic") is not None

def test_template_names_includes_locals_and_stays_sorted(tmp_path):
    assert template_names(tmp_path) == ["generic", "my_assay"]
    assert template_names() == ["generic"]
```

- [ ] **Step 2–4:** Fail, implement, pass. Merge builtins with locals **per call** — build no persistent dict.
- [ ] **Step 5: Mutate** — return locals only (the `generic` control fails); cache the merged mapping module-globally (task 6's test will catch it, but note it here).
- [ ] **Step 6: Commit.**

---

## Task 4: Hoist `find_repo_root` above the template check, silently

**Files:** Modify `src/publishable/validate.py`; Test `tests/test_validate.py`

**The ordering constraint § Errors pins:** `E-TEMPLATE-UNKNOWN` fires "exactly once, since that check returns immediately after", with none of the other rows. **A hoisted `find_repo_root` that reported a missing repo would put a new finding ahead of a documented one.** The existing `try: … except ContractError: repo_root = None` below is the pattern to reuse.

- [ ] **Step 1: Write the failing tests**

```python
def test_a_local_template_validates_through_the_real_path(tmp_path):
    """End to end: a config naming a local template no longer draws
    E-TEMPLATE-UNKNOWN. THE CONTROL: a config naming a template that exists
    nowhere still draws it, so a check that stopped reporting entirely fails."""

def test_no_repo_means_local_discovery_is_skipped_and_generic_still_resolves(tmp_path):
    """A config outside any repo. `find_repo_root` raises; the hoist must
    swallow it. Assert the exact finding set — an added finding here would
    break the documented early-return order."""

def test_an_unknown_template_still_reports_exactly_one_finding(tmp_path):
    """§ Errors: the check "returns immediately after", so none of the other
    rows appear. Assert the exact set, not that the code is present."""
```

- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — let `find_repo_root`'s `ContractError` propagate (the no-repo test fails); report a finding on a missing repo (the exact-set assertions fail).
- [ ] **Step 6: Commit.**

---

## Task 5: Wire the other two call sites

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/experiment.py`; Test `tests/test_cli.py`

Both already have a repo root in scope — `cli.command_run` binds `repo_root = find_repo_root(config_path)` in the same function, and `generate_experiment` takes it as a parameter.

**`generate experiment --template my_assay` failing with `E-TEMPLATE-UNKNOWN` is the first probe in the scoping.** It must stop failing.

- [ ] **Step 1: Write the failing tests** — `generate experiment --template my_assay` succeeds in a project holding that local template, with the control that `--template nope` still fails; and `command_run`'s `aggregate` block resolves a local template's `aggregate`.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — pass `None` as the root at each site in turn; each must fail its own test.
- [ ] **Step 6: Commit.**

---

## Task 6: Process hygiene — per-repo registration, non-aliasing module names

**Files:** Modify `src/publishable/templates/discovery.py`; Test `tests/test_templates.py`

**Trap (b), and the reason is written down already.** `load_experiment` purges the root package from `sys.modules` because "two projects in one process can declare the same package name … and a cached module would silently hand back the other project's steps". Two repos can both hold `templates/my_assay.py`.

- [ ] **Step 1: Write the failing test**

```python
def test_two_repos_in_one_process_do_not_cross_contaminate(tmp_path):
    """Both repos hold `templates/my_assay.py`, registering the same name but
    different classes. Resolving from repo A then repo B must give B's class.
    A module-global registry, or a `sys.modules` cache keyed on a name both
    repos share, hands back A's — silently, which is why this is a test and
    not a comment."""
    a = get_template("my_assay", repo_a)
    b = get_template("my_assay", repo_b)
    assert type(a).__doc__ == "A's"
    assert type(b).__doc__ == "B's"      # the assertion that fails on a cache
```

- [ ] **Step 2–4:** Fail, implement, pass. Give each path-imported module a name that cannot alias across repos, and purge it as `load_experiment` does.
- [ ] **Step 5: Mutate** — key the synthetic module name on the file stem alone; the test must fail. **This is the mutation that matters: a naive implementation passes every other test in this plan.**
- [ ] **Step 6: Commit.**

---

## Task 7: Collision and shadow are refused, naming both providers

**Files:** Modify `src/publishable/templates/discovery.py`, `docs/reference.md`; Test `tests/test_templates.py`

**Mint `E-TEMPLATE-COLLISION`.** § Creating a plugin: two local files claiming one name, and a local claiming `generic`, "fail at load, naming both providers". **Both providers must appear in the message** — that is what the rule promises and what makes it actionable.

**Scope, per the spec's decision 5:** local × local and local-shadows-`generic` only. Local shadowing an *installed plugin* is H7b's — no plugin can exist until entry points do.

- [ ] **Step 1: Write the failing tests** — two files claiming one name; a file claiming `generic`; **and the control**, two files claiming *different* names, which must resolve cleanly. Assert both provider paths appear in the message.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — report only the first provider (the naming assertions fail); allow the shadow (its test fails). Neither may kill the control.
- [ ] **Step 6: Registry row** in § Errors `validate` reports, in sort order, checking every row it moves. Commit.

---

## Task 8: A template that fails to load is a finding, not a traceback

**Files:** Modify `src/publishable/templates/discovery.py`, `docs/reference.md`; Test `tests/test_templates.py`

**Mint `E-TEMPLATE-LOAD`.** Three shapes: a file that **raises on import**, one that **registers nothing**, one that **registers a non-`BaseTemplate`**. `validate` collects and never raises, so each must surface as a finding naming the file.

- [ ] **Step 1: Write the failing tests** — one per shape, **plus the control**: a well-formed template beside a broken one must still resolve, so a discovery that abandoned the directory on the first failure fails here.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — let the `ImportError` propagate (the raise test fails with a traceback rather than a finding); accept a non-`BaseTemplate` (its test fails).
- [ ] **Step 6: Registry row**, sorted, rows-moved checked. Commit.

---

## Task 9: `generate template`

**Files:** Modify `src/publishable/cli.py`, `src/publishable/generators/` (a new module beside `experiment.py`); Test `tests/test_cli.py`

Writes `templates/<name>.py` holding a `BaseTemplate` subclass with `parameter_spec` and `@register_template`.

**The stub emits only the five live members** — `parameter_spec`, `validate`, `aggregate`, `naming_pattern`, `default_repeats`. **Not** `field_convention`, `required_env`, `apparatus_probe` or `apparatus_facts`: nothing reads them, and a stub that emits them teaches a user to set fields with no effect.

**Greenfield refusal:** an existing `templates/<name>.py` is refused, never overwritten.

**The README half is deferred** — spec decision 4. § Generators promises the parameter table "is added to the README", but the scaffolded README has no region for one and `generate_experiment` never touches the README at all. Task 15 records the gap; do not invent a region.

- [ ] **Step 1: Write the failing tests** — the file is written and its name resolves through `get_template(name, repo_root)` (**round-trip, not just file existence**); an existing file is refused with the file unchanged; the stub contains none of the four dead members.
- [ ] **Step 2–4:** Fail, implement, pass, and route it in `_dispatch_generate`.
- [ ] **Step 5: Mutate** — overwrite instead of refusing (the refusal test fails); emit `apparatus_probe` in the stub (the dead-members test fails).
- [ ] **Step 6: Commit.**

---

## Task 10: `template_version` and `plugin` under a local template

**Files:** Modify `src/publishable/materialize.py`, `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_materialize.py`, `tests/test_validate.py`

**Trap (c), and the single best reason this slice is not three lines.** Today `materialize_config` writes `template_version` from **core's own module constant** and `_check_versions` compares a config against it. For a local template that string certifies nothing — § Three hashes says so: *"`template_version` isn't the answer for a local template — it's a string its author remembers to bump."*

**Spec decisions 2 and 3:** `plugin` stays **`null`** — it names a *distributable source* and a local template has none, so **no code change**, only the test that pins it. `template_version` is **not written and not warned on** for a local template.

- [ ] **Step 1: Write the failing tests** — a config generated against a local template carries no core `template_version`, and `_check_versions` emits no `W-TEMPLATE-VERSION` for it; **the control**, a `generic` config, still gets both, so a change that suppressed the warning globally fails.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — suppress the warning for every template (the `generic` control fails); write core's constant for locals (the first test fails).
- [ ] **Step 6:** Amend § Three hashes / § Errors' `W-TEMPLATE-VERSION` row so the document says what the code does. Commit.

---

## Task 11: The `generate template` row goes `built`

**Files:** Modify `docs/reference.md`, `src/publishable/cli.py`; Test — the existing CLI-table tests

**Atomic, or the suite fails.** § Generators' `template` row, the inline `` `template` (NOT BUILT) `` spelling in § Operation commands' `generate` row, and `cli.NOT_BUILT_GENERATORS` are bound in **both directions** by `test_reference_cli_tables_are_parsed_at_all` and `test_reference_cli_tables_match_what_the_cli_does`. Change all three in one commit.

- [ ] **Step 1:** Run the two binding tests first and record that they pass — they are your oracle.
- [ ] **Step 2–3:** Make all three edits; confirm green.
- [ ] **Step 4: Mutate** — change the doc and not the constant; a binding test must fail. That is the check proving they are still bound.
- [ ] **Step 5: Commit.**

---

## Task 12: Split the four-`register_*` row in § The importable surface

**Files:** Modify `docs/reference.md`

`register_template` · `register_resolver` · `register_probe` · `register_writer` share **one row** marked `not yet built`, under a paragraph saying "Importing one raises `ImportError` today". Only the first is built now.

**That table's `Status` is its third column, so the CLI test does not parse it** — an unsplit row would silently claim three unbuilt exports are built, with nothing to catch it.

- [ ] **Step 1:** Split the row so only `register_template` reads built; correct the `ImportError` sentence, which is now false for one of the four.
- [ ] **Step 2:** Check every row the split **moved**, and any count phrase near the table.
- [ ] **Step 3: Commit.**

---

## Task 13: § Package layout gains the discovery module

**Files:** Modify `docs/reference.md`

The tree is normative and "modules marked `— not yet built` are specified and unbuilt". Add `discovery.py` beside `templates/{base.py,registry.py,builtin/generic.py}`.

- [ ] **Step 1:** Add it, unmarked, since it is built.
- [ ] **Step 2: Commit.** (If task 2 put discovery inside `registry.py` instead, say so in the report and skip — do not invent a file the code does not have.)

---

## Task 14: `E-TEMPLATE-UNKNOWN` stops being about installation

**Files:** Modify `src/publishable/validate.py`, `docs/reference.md`; Test `tests/test_validate.py`

Today the message reads *"names `my_assay`, which no installed template registers (known: generic)"* and its § Errors row says *"names a template no installed package registers"*. **Both stop being true the moment a template installed nowhere can resolve.** And "(known: …)" is `template_names()`, which must now include local names.

- [ ] **Step 1: Write the failing test** — in a project holding local templates, an unknown name's message lists them among the known, and says nothing about installation. Assert the **exact message**.
- [ ] **Step 2–4:** Fail, implement, pass.
- [ ] **Step 5: Mutate** — call `template_names()` without the root; the known-list assertion fails.
- [ ] **Step 6:** Update the § Errors row to match. Commit.

---

## Task 15: The promise this slice widens, and the gap it declines to fix

**Files:** Modify `docs/reference.md`

- [ ] **Step 1: Write the sentence § Creating a plugin owes.** It justifies entry points by saying `validate` resolves a name *"without importing a line of that package"*, "which matters because importing a module runs its top level and `validate` is documented as creating nothing and reaching nothing." For a local template that cannot hold: the decorator argument **is** the registration, and the collision rule makes discovery **eager**, so `validate` imports every file in `templates/` — including ones no config references. Say it beside the argument it qualifies. Say also that this is not a greenfield breach — importing is not inspecting, and it is the same line `validate` already crosses for `entrypoint` — but that it widens that exception from one module to a directory.
- [ ] **Step 2: Record the README gap** where a reader meets it, **not** in `spec-defects.md` (gitignored, does not survive a merge). **Re-anchored — do not grep for the old wording.** Task 9 already changed § Generators' `template` row: the promise that the parameter table "is added to the README" now reads *"Adding its parameter table to the README is NOT BUILT"*, so **the `template` half is marked and must not be re-marked**. What remains is the gap itself: § The generated README specifies **no region** for a parameter table, and `generate_experiment` does not touch the README at all — a pre-existing defect plus a genuinely under-specified spot, deferred to whoever owns `docs`. Record it once, where a reader of § The generated README meets it.
- [ ] **Step 2b: Two items routed here from task 9's review.** (i) The `experiment` row's *"adds a row to the README's managed experiments table"* is the same false build fact as the row above it; task 9 marked it, so **verify only** that both rows now read consistently and that no third row in that table still claims an unbuilt README effect. (ii) `BaseTemplate.required_env` is **dead** (spec measurement: declarable, read nowhere), yet § The generated README specifies that `generate experiment` *"merges any new `required_env` into the credentials table"* — a specified reader of an unbuilt member. Same defect shape as the parameter table, same paragraph; record it in the same place rather than minting a second note.
- [ ] **Step 2c: Generalize § Exit codes' `E-STEP-EXISTS` clause.** `E-TEMPLATE-EXISTS` (minted in task 9) joins a family — `E-STEP-EXISTS` and its siblings — whose behaviour § Exit codes states for one member only, by name. This is now the fourth undocumented member. Widen that clause to name the family and its shared exit behaviour rather than adding a fourth row; the greenfield refusal is one rule, not four.
- [ ] **Step 3: One sentence on `__pycache__`.** Discovery writes `templates/__pycache__/`; a scaffolded project ignores it, so neither the dirty gate nor `code_hash` is disturbed — **probed**. A hand-made repo whose `.gitignore` lacks it would go dirty on `validate` and fail `run`.
- [ ] **Step 4:** Mechanical pass over everything edited. Commit.

---

## Sequencing

1 → 15 in order. Tasks 1–3 build the mechanism bottom-up and **task 3 is where the suite briefly cannot collect** unless all six bindings move together. Task 4 is the ordering constraint; 5 makes it reachable from the two other call sites. **Task 6 is the one whose absence passes every other test in this plan** — a naive implementation is correct until a second repo appears in the same process. Tasks 7–8 are the refusals, 9–10 the generator and the version question, 11–15 the documents, with 11 atomic against its binding tests.

## Where this slice will be attacked

**The acceptance property:** a `templates/<name>.py` in a project's own repo resolves by name through `validate`, `run` and `generate`, with core's builtins still resolving beside it; two files claiming one name are refused naming both; a broken file is a finding rather than a traceback; and two repos in one process never see each other's templates.

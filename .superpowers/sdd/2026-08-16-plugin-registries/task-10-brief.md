## Task 10: `BaseTemplate.version`, and `W-TEMPLATE-VERSION` against it

**Files:** Modify `src/publishable/templates/base.py`, `src/publishable/templates/builtin/generic.py`,
`src/publishable/validate.py`, `src/publishable/materialize.py`,
`src/publishable/generators/template.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_templates.py`.

**Interfaces:**
- Consumes: `BaseTemplate`'s class attributes, which today are `naming_pattern`, `field_convention`,
  `default_repeats`, `required_env`, `apparatus_probe`, `apparatus_facts`, `parameter_spec`, plus
  the methods `validate` and `aggregate`; `materialize.TEMPLATE_VERSION`, the module constant
  `"1.0.0"`; `validate._check_versions(doc, template, c)`, whose warning message reads
  `f"is {declared} but the installed template reports {TEMPLATE_VERSION}{detail}"`;
  `materialize.materialize_config`, which writes `template_version: "{TEMPLATE_VERSION}"` for a
  non-local template and omits the line for a local one.
- Produces: `BaseTemplate.version: str | None = None`; `GenericTemplate.version = TEMPLATE_VERSION`;
  `_check_versions` comparing against **the template's own** reported version; `materialize` writing
  **the template's own** version.

**Row 212's first half, and what actually closes it.** `spec-defects.md`'s Row 212 says
`_check_versions` compares the declared `template_version` against a module constant rather than
against the installed template's own reported version, and that closing it means `BaseTemplate`
declaring a `version` attribute — a four-document change. That is exactly this task. What it does
**not** do is make the third provenance reachable there: task 9 states that no installed claim
carries a class in Part A, so `_check_versions` still sees only core's own template and this repo's.
The gap the attribute closes is the **false guarantee in the message** — "the installed template
reports" is a claim about a template core did not write — and the hard-coded comparison. Both are
real and both are fixed here; the reachability is not, and the `spec-defects.md` amendment says so
rather than striking the row outright.

**Two counts in comments that go stale here, and `CLAUDE.md` forbids both.**
`generators/template.py`'s comment says the stub emits "five members … and none of `BaseTemplate`'s
other four", and that `reference.md` § Templates "shows all nine". Adding `version` moves both.
**Rewrite them to state what each set *is*** rather than to increment a number — that is the rule,
and re-incrementing is how this repo has gone wrong before.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_templates.py`:

```python
def test_a_template_reports_its_own_version_and_the_base_declares_none():
    """`None` and a string are different claims: the first is "this template
    tracks no version", which is every template that does not set one, and the
    second is what `template_version` in a config is compared against."""
    assert BaseTemplate.version is None
    assert get_template("generic").version == TEMPLATE_VERSION


def test_the_version_warning_names_what_the_template_reports_not_a_core_constant(
    tmp_path: Path, git_repo: Path
):
    """The false guarantee Row 212 names, closed by comparing against the class.

    A local template declaring a version of its own is still skipped — that is
    `_check_versions`' first line and § Three hashes' rule — so the observable
    change is that the comparison reads the class rather than a module constant,
    and the fixture that shows it is a subclass whose `version` differs from
    core's.
    """
    from publishable.diagnostics import Collector
    from publishable.validate import _check_versions

    class Versioned(BaseTemplate):
        version = "9.9.9"
        parameter_spec = {}

    c = Collector()
    _check_versions({"template_version": "1.0.0"}, Versioned(), c)
    message = next(f.message for f in c.findings if f.code == "W-TEMPLATE-VERSION")
    assert "9.9.9" in message
    assert TEMPLATE_VERSION not in message

    # THE CONTROL, produced by the code under test: a config declaring the
    # version the template reports draws nothing at all.
    quiet = Collector()
    _check_versions({"template_version": "9.9.9"}, Versioned(), quiet)
    assert [f.code for f in quiet.findings] == []
```

      `tests/test_templates.py` imports `BaseTemplate` already; add
      `from publishable.materialize import TEMPLATE_VERSION`.

- [ ] **Step 2: Run and see it fail.** `AttributeError: type object 'BaseTemplate' has no attribute
      'version'`.

- [ ] **Step 3: Implement.** In `src/publishable/templates/base.py`, add beside the other class
      attributes:

```python
    version: str | None = None
```

      with a docstring-adjacent comment stating what it is rather than counting the attributes
      around it:

```python
    # What this template reports as its own spec version, which a config's
    # `template_version` is compared against. `None` for a template that tracks
    # no version — the base's answer, and the right one for a project-local file,
    # whose version is a string its author remembers to bump rather than a fact
    # core can check.
```

      In `src/publishable/templates/builtin/generic.py`, add
      `from publishable.materialize import TEMPLATE_VERSION` and `version = TEMPLATE_VERSION`.
      **Check the import direction before writing it:** `materialize` imports
      `publishable.param`, `publishable.templates.base` and `publishable.templates.discovery`, and
      imports neither `registry` nor `builtin.generic`, so `generic → materialize → discovery →
      base` introduces no cycle. Confirm by running `uv run python -c "import publishable"` and then
      the suite; a cycle shows as an `ImportError` at collection, not later.

      In `src/publishable/validate.py`, replace `_check_versions`' comparison and message:

```python
    if is_local_template(type(template)):
        return
    reported = type(template).version
    declared = doc.get("template_version")
    if reported is None or not declared or declared == reported:
        return
```

      and the warning's message:

```python
        f"is {declared} but the template reports {reported}{detail}",
```

      Then amend the docstring paragraph that reads "`TEMPLATE_VERSION` is core's own constant —
      comparing a config's declared string against it is meaningless for a template core did not
      write" so it states the current rule:

```python
    A local template is skipped regardless of what `template_version` declares,
    and so is any template reporting no version of its own. What a config's
    declared string is compared against is the template's own `version`, read
    off the class: a module constant would be core's answer for a template core
    did not write, which `docs/reference.md` § Three hashes rejects — a
    `template_version` "isn't the answer for a local template — it's a string
    its author remembers to bump."
```

      In `src/publishable/materialize.py`, replace the two `TEMPLATE_VERSION` interpolations so the
      generated header and field carry what the template reports:

```python
    local = is_local_template(type(template))
    reported = None if local else type(template).version
    header_version = "" if reported is None else f" v{reported}"
```

      and `*([] if reported is None else [f'template_version: "{reported}"']),`. **`TEMPLATE_VERSION`
      stays defined in `materialize.py`** — `generic.py` reads it and `validate.py` no longer does;
      remove `validate.py`'s now-unused import and let `ruff` confirm it.

- [ ] **Step 4: Rewrite the two stale counts.** In `src/publishable/generators/template.py`, replace
      "The stub emits five members — `parameter_spec`, `validate`, `aggregate`, `naming_pattern`,
      `default_repeats` — and none of `BaseTemplate`'s other four" with a statement of what each set
      is:

```python
# The stub emits `parameter_spec`, `validate`, `aggregate`, `naming_pattern` and
# `default_repeats`, and none of the rest. `required_env` has a reader
# (`validate` checks it), but a stub declaring `[]` would only ever satisfy that
# check trivially and would still teach its reader to set a field this generated
# file has no other use for. `version` is omitted for a sharper reason: a
# project-local template is never version-checked at all, so a version in this
# file would be a string nothing reads. `field_convention`, `apparatus_probe`
# and `apparatus_facts` are declared on the base class and read by nothing in
# this build. `docs/reference.md` § Templates: where parameters are defined
# shows the whole set, because that example is core's own `generic` rather than
# a file you are about to edit.
```

      Note the last sentence drops "all nine" for "the whole set" — the rule is to state what a set
      *is*, and a count in a comment is what went stale. **Task 13 edits this same comment again**
      when `apparatus_probe` gains a reader; do not pre-empt it.

- [ ] **Step 5: Document it.** In § Templates' fenced class example, add `version = "1.0.0"` after
      `default_repeats = 1`, and in § The importable surface's "What you define, and what is core's"
      table, the `BaseTemplate` row's **Defaulted** column reads "`validate(self, config)` returns
      `[]`" — extend it to "`validate(self, config)` returns `[]`, `version` is `None`". In
      § Validation's *Template version moved* row, the example failure reads "`template_version` is
      `1.0.0` but installed `generic` reports `1.2.0`" — leave it; it was already stated against the
      template rather than a constant and is now true.

- [ ] **Step 6: Amend Row 212 rather than striking it.** Append to that section in
      `docs/superpowers/spec-defects.md`:

```markdown
**AMENDED 2026-08-16 (H7b Part A task 10): the comparison is fixed; the reachability is not.**
`BaseTemplate.version` now exists, `GenericTemplate` reports it, `_check_versions` compares a
config's `template_version` against `type(template).version`, and `materialize` writes what the
template reports. The false guarantee this row named — a warning saying "the installed template
reports" while comparing against core's own module constant — is gone.

What remains, and it is why this row is amended rather than struck: **no installed template's class
is ever held in this build**, so the comparison still only ever runs against core's own template and
a project-local one is still skipped. `Claim.cls` is `None` for an installed claim by decision 3 of
`2026-08-16-plugin-registries-design.md`. This row's own words — "It becomes observable when a
plugin ships a template with a version of its own" — are still the condition, and it is now filed
separately as `## OPEN — an installed template's name resolves but its class is never loaded`,
**owner unassigned**. Strike this row when that one is closed, not before.
```

- [ ] **Step 7: Run and see it pass**, then the whole suite. `tests/test_materialize.py`'s
      `test_the_four_identifying_fields_are_present` and
      `test_a_local_template_carries_no_core_template_version` are the regression controls and must
      pass **unchanged**: `generic.version` equals `TEMPLATE_VERSION`, so the generated config is
      byte-identical. Confirm that by running those two by name and reading the result. Expected
      total: predecessor's count **+ 2**.

- [ ] **Step 8: Mutate — two.**

  **(a) Compare against the constant again.** In `_check_versions`, change `reported =
  type(template).version` to `reported = TEMPLATE_VERSION` (re-adding the import).
  `test_the_version_warning_names_what_the_template_reports_not_a_core_constant` must FAIL on
  `assert "9.9.9" in message` — the mutant compares `"1.0.0"` against `"1.0.0"` and returns early,
  so the `next(...)` raises `StopIteration` before the assertion. **Checked against the body:** the
  fixture's `Versioned.version` is deliberately `"9.9.9"` while its config declares `"1.0.0"`, which
  is what makes the two branches produce different results; a fixture whose version happened to
  equal `TEMPLATE_VERSION` would have been blind. Read the failure and confirm it is
  `StopIteration`, not an `AssertionError` — if it is an `AssertionError` the early return was
  transcribed wrong.

  **(b) Drop the `reported is None` guard.** Remove `reported is None or` from the early return.
  Nothing in the suite goes red, **and that is the finding**: no template in the tree reports `None`
  while also being non-local, so the guard is unreachable today. **Do not keep this mutation and do
  not manufacture a fixture for it** — a `BaseTemplate` subclass with no version, registered in a
  repo's `templates/`, is local and skipped one line earlier. State in the task report that the
  guard is defensive and unpinned, and that the task that populates `Claim.cls` for an installed
  claim is what first reaches it.

  Revert (a) by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** `materialize`'s use of
      `type(template).version` **is not independently pinned**: `generic.version` equals
      `TEMPLATE_VERSION`, so writing either produces the same file and every materialize test passes
      under both. A fixture that separated them would have to be a non-local template reporting a
      different version, which is the unreachable case named in mutation (b). Stated rather than
      papered over; **nothing in this slice closes it.** § Templates' `version = "1.0.0"` line and
      the § The importable surface cell are prose and unpinned, as every document row in this slice
      is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: a template reports its own version, and W-TEMPLATE-VERSION compares against it`

---


## Task 9: `required_env` checked at `validate` — the first reader of a shipped-unread attribute

**Files:** Modify `src/publishable/validate.py`, `tests/test_validate.py`, `CLAUDE.md`.

**Interfaces:**
- Consumes: `BaseTemplate.required_env: list[str] = []` at `src/publishable/templates/base.py`,
  re-declared at `src/publishable/templates/builtin/generic.py`; `missing_env` from task 7;
  `Collector.error(code: str, path: str, message: str) -> None`.
- Produces: `_check_required_env(template: Any, c: Collector) -> None` in `validate.py`, called from
  `validate_config`, emitting `E-CRED-MISSING`.

**This is a defect closure, not a neutral addition.** `CLAUDE.md` § Reading the documents names
`BaseTemplate.required_env` **by hand** as its canonical instance of "an unbuilt reader of a
**shipped** surface". This slice is the first reader, so the example stops being true and the row
needs a surviving one. **Use `field_convention`** — verified unread at `478c1f3`:
`grep -rn "field_convention\|apparatus_facts" src/publishable/` returns only the two declarations
(`templates/base.py`, `templates/builtin/generic.py`) and a comment in `generators/template.py`
saying the `generate template` stub omits them. `apparatus_facts` is equally unread but **H7d owns
it**, and `apparatus_probe` is **H7b task 13's**; `field_convention` is unowned, which is what makes
it the right survivor.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`:

```python
_REQUIRED_ENV_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    required_env = ["PUBLISHABLE_TEST_TOKEN", "PUBLISHABLE_TEST_OTHER"]
    parameter_spec = {}
"""


def test_an_unset_required_env_variable_is_reported_with_its_name(
    git_repo: Path, write_config, monkeypatch
):
    """The first reader of `BaseTemplate.required_env`.

    `delenv` on both names is what makes this a test of the check rather than of
    the machine: `os.environ` is inherited from the test runner, and without it
    this passes on a laptop where nothing was ever set — including on a build
    where the check does not exist.
    """
    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.delenv("PUBLISHABLE_TEST_OTHER", raising=False)
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "cred_assay.py").write_text(_REQUIRED_ENV_TEMPLATE)

    c = Collector()
    validate_config(write_config({"experiment_type": "cred_assay", "parameters": {}}), c)
    found = [f for f in c.findings if f.code == "E-CRED-MISSING"]

    # One finding per unset variable, in declared order — a template needing two
    # keys names both rather than one at a time. Asserted as a fragment per
    # finding rather than by splitting the message on backticks: the message
    # already carries a backticked template name, so an index-based split pins
    # the message's backtick COUNT and breaks on any reworded clause.
    assert len(found) == 2, [f.message for f in found]
    assert "`PUBLISHABLE_TEST_TOKEN`" in found[0].message
    assert "`PUBLISHABLE_TEST_OTHER`" in found[1].message
    assert {f.path for f in found} == {"experiment_type"}
    # The message names the template, which is the only thing this code CAN name
    # — the fragment that distinguishes it from `E-CRED-PARAM-MISSING`, whose
    # message names a parameter, a value and a condition and never a template.
    assert "template `cred_assay`" in found[0].message
    assert "condition" not in found[0].message


def test_a_satisfied_required_env_validates_clean(git_repo: Path, write_config, monkeypatch):
    """The honouring, and the control the negative test needs. Without it, a check
    that reported unconditionally would pass every assertion above."""
    monkeypatch.setenv("PUBLISHABLE_TEST_TOKEN", "x")
    monkeypatch.setenv("PUBLISHABLE_TEST_OTHER", "y")
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "cred_assay.py").write_text(_REQUIRED_ENV_TEMPLATE)

    assert codes(write_config({"experiment_type": "cred_assay", "parameters": {}})) == set()


def test_a_required_env_variable_may_be_supplied_by_dot_env(
    git_repo: Path, write_config, monkeypatch
):
    """The two halves wired together: task 8's load makes `.env` a legal place to
    put the value, which is the whole point of the mechanism."""
    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.delenv("PUBLISHABLE_TEST_OTHER", raising=False)
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "cred_assay.py").write_text(_REQUIRED_ENV_TEMPLATE)
    (git_repo / ".env").write_text(
        "PUBLISHABLE_TEST_TOKEN=a\nPUBLISHABLE_TEST_OTHER=b\n"
    )

    assert codes(write_config({"experiment_type": "cred_assay", "parameters": {}})) == set()


def test_a_template_declaring_no_required_env_reports_nothing(write_config, monkeypatch):
    """`generic` declares `required_env = []`. A check that reported for an empty
    list would break every existing config in the suite — asserted here anyway,
    so the reason a green suite is green is stated rather than assumed."""
    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    assert "E-CRED-MISSING" not in codes(write_config())
```

- [ ] **Step 2: Run and see them fail.** The first fails with an empty `found` list; the two clean
      ones already pass, which is expected and is exactly why they are not sufficient on their own.

- [ ] **Step 3: Implement.** In `validate.py`, add `missing_env` to the `publishable.secrets` import
      line from task 8, and define:

```python
def _check_required_env(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The template-level credential set — `reference.md` § Secrets & credentials.

    Read from the class, so it needs no roster and no expansion: a `required_env`
    list says what an experiment *type* always needs, which is the wrong shape
    exactly when the credential follows a choice, and that case is
    `_check_requires_env`'s.

    Reported at `experiment_type`, the field that decided which template's list
    applies. The value is never printed — the message names the variable and
    where to put a value, which is the whole of what is safe to say and the whole
    of what a reader needs.
    """
    names = getattr(template, "required_env", None)
    if not isinstance(names, list):
        return  # a template declaring something else is not this check's fault to report
    name = doc.get("experiment_type", "")
    for variable in missing_env(str(n) for n in names):
        c.error(
            "E-CRED-MISSING",
            "experiment_type",
            f"template `{name}` requires `{variable}`, which has no value in the "
            "environment or in `.env` — the config records the NAME, so put the value "
            "in `.env` at the repository root",
        )
```

Call it from `validate_config`, immediately before `_check_parameters(doc, template, c)` so the
credential findings sit beside the other template-derived ones:

```python
    _check_required_env(doc, template, c)
```

- [ ] **Step 4: Run and see it pass.** New tests, then the full suite.

- [ ] **Step 5: Replace `CLAUDE.md`'s worked example.** In § Misreadings this repo has made more
      than once → *Reading the documents*, the row currently reads:

```
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect: `BaseTemplate.required_env` is declarable today on a class that ships, and nothing reads it |
```

Replace the example with the survivor:

```
| Reading an unbuilt reader as a defect | An unbuilt reader of an **unbuilt** surface is specification — present tense is correct, and § Package layout's `— not yet built` carries it. An unbuilt reader of a **shipped** surface is a defect: `BaseTemplate.field_convention` is declarable today on a class that ships, and nothing reads it. (`required_env` was this row's example until H7c gave it a reader at `validate`; `apparatus_probe` and `apparatus_facts` are the other two, and each is owned — H7b and H7d respectively — where `field_convention` is not) |
```

**Verify the survivor before writing it**: re-run
`grep -rn "field_convention" src/publishable/` and confirm the only hits are the two declarations
and the `generators/template.py` comment. Shipping a *new* false example in the file that warns
about false examples is the worst available outcome.

- [ ] **Step 6: Mutate — two.**

  **(a) Delete the `c.error` call.**
  `test_an_unset_required_env_variable_is_reported_with_its_name` must FAIL on its list comparison
  (`[] != [...]`). **Checked against the test body:** it filters `c.findings` for the code and
  asserts a two-element list, so an absent finding is directly observable.

  **(b) Report the whole list rather than the missing ones.** Change
  `for variable in missing_env(...)` to `for variable in (str(n) for n in names)`.
  `test_a_satisfied_required_env_validates_clean` must FAIL — `codes(...)` would hold
  `E-CRED-MISSING`. **This is the mutation that proves the check reads the environment at all**;
  mutation (a) does not, because a check that always reported would also satisfy (a)'s test. Without
  a control that sets the variables, this mutation would be undetectable — which is why that test
  exists and why it is named here.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches.** The `isinstance(names, list)` guard is
      defensive and **unpinned**: no fixture in this slice declares a non-list `required_env`, and a
      template that did would be a plugin-authoring fault this slice is not scoped to diagnose. Left
      in and named. Also unpinned: **the finding's position in `validate_config`'s call order** —
      nothing asserts that `E-CRED-MISSING` appears before or after any other code, deliberately,
      because § Errors documents an ordering only for the five early returns.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: required_env gets its first reader at validate, and CLAUDE.md's example moves to field_convention`

---


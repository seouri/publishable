## Task 9: Template provenance becomes three-valued

**Files:** Modify `src/publishable/templates/registry.py`, `src/publishable/templates/discovery.py`,
`src/publishable/validate.py`, `src/publishable/materialize.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_templates.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry.Claim` and `registry._claims` (task 8); `discovery.is_local_template(cls:
  type[BaseTemplate]) -> bool`, which reads a marker `_import_file` stamps and whose two callers are
  `validate._check_versions` (`is_local_template(type(template))`) and `materialize.materialize_config`
  (`local = is_local_template(type(template))`).
- Produces:
  - `Claim.provenance: str` — `"core"`, `"local"` or `"installed"`, decided at the merge where all
    three sources are in hand.
  - `registry.template_provenance(name: str, repo_root: Path | None) -> str | None` — the direct
    question, answered from `_claims` rather than from a marker on a class.
  - `validate` reporting `E-TEMPLATE-INSTALLED-UNSUPPORTED` for a name whose only claim is installed.
  - `is_local_template` **kept and unchanged**, still stamping and still read — see the ruling below.

**The ruling on `is_local_template`, and it is narrower than "replace the predicate".** The
re-scoping's § 10 says the direct question is asked at the merge, and it is: `Claim.provenance` is
decided there, from the source a claim came from, with no proxy. But its two readers take a **class**
and not a name, and in Part A no installed claim ever carries a class — decision 3 forbids the load.
So **`installed` is unreachable at both class-taking readers in this slice**, and rewriting them to
consult a three-valued predicate would thread a value no fixture can produce, which is precisely the
"seam named in the brief and instantiated by no fixture" shape that passed 1700+ tests in an earlier
slice. `is_local_template` therefore stays exactly as it is, keeps both callers, and keeps its
docstring's stated boundary. What is three-valued is the **claim**, and it is observable at three
places that do not take a class: `template_provenance`, the collision message's provider spellings
(task 8), and the new refusal below.

**The refusal this task mints, and why it is the `-UNSUPPORTED` family.** After task 8 an installed
template name is *known* and unresolvable. Reporting `E-TEMPLATE-UNKNOWN` for it would be false —
the message says "no template … registers" and one does. Reporting nothing would let
`validate_config` fall through to `template is None` and return with a wrong finding. So:
`E-TEMPLATE-INSTALLED-UNSUPPORTED`, the undocumented build family — **no § Errors row, and it must
not gain one** — retired wholesale by whichever slice loads an installed template. **That slice is
not Part B**, whose nine tasks are the resolver half; this task files the residual with its owner
stated as unassigned, which is the honest form.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_templates.py`:

```python
def test_provenance_is_decided_at_the_merge_for_each_of_the_three_sources(installed, tmp_path):
    """The direct question, asked where all three sources are in hand.

    All three values in one arrangement, because a fixture with two could not
    tell a three-valued answer from a boolean one renamed.
    """
    templates = tmp_path / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(CLAIMS_MY_ASSAY)
    installed("dist-one", "1.0", {"publishable.templates": {"vendor_assay": "no_one:T"}})

    assert template_provenance("generic", tmp_path) == "core"
    assert template_provenance("my_assay", tmp_path) == "local"
    assert template_provenance("vendor_assay", tmp_path) == "installed"
    assert template_provenance("nothing_claims_this", tmp_path) is None
```

      and to `tests/test_validate.py`:

```python
def test_an_installed_only_template_name_is_known_and_refused(installed, write_config):
    """Known, and not resolved: core answers the name from metadata and does not
    import the distribution to get a class. So the finding is neither
    `E-TEMPLATE-UNKNOWN` — which would be false — nor silence.
    """
    installed("dist-one", "1.0", {"publishable.templates": {"vendor_assay": "no_one:T"}})

    found = messages_by_code(write_config({"experiment_type": "vendor_assay"}))
    assert "E-TEMPLATE-UNKNOWN" not in found
    message = found["E-TEMPLATE-INSTALLED-UNSUPPORTED"]
    assert "vendor_assay" in message
    assert "dist-one 1.0" in message

    # THE CONTROL: a name nothing claims is still `E-TEMPLATE-UNKNOWN`, so the
    # refusal above is about the installed claim rather than about any
    # unresolved name.
    assert "E-TEMPLATE-UNKNOWN" in codes(write_config({"experiment_type": "nothing_claims_this"}))
```

- [ ] **Step 2: Run and see them fail.** `ImportError` on `template_provenance`, and
      `KeyError: 'E-TEMPLATE-INSTALLED-UNSUPPORTED'`.

- [ ] **Step 3: Implement.** In `registry.py`, add `provenance: str` to `Claim` — **first field**,
      so the collision message's `claim.provider` reads stay unambiguous only if you update every
      construction; construct with keywords rather than positionally to make that impossible to get
      wrong:

```python
class Claim(NamedTuple):
    provenance: str
    provider: str
    cls: type[BaseTemplate] | None
```

      Construct core's as `Claim(provenance="core", provider=…, cls=core)`, an entry point's as
      `Claim(provenance="installed", provider=provider_of(ep), cls=None)`, and a local one as
      `Claim(provenance="local", provider=found.provider, cls=found.cls)`. Then add:

```python
def template_provenance(name: str, repo_root: Path | None = None) -> str | None:
    """Where the template `name` resolves from — `core`, `local`, `installed` — or
    `None` if nothing claims it.

    Asked at the merge, which is the one place holding all three sources, and
    answered from which source a claim came from rather than from anything
    observable on a class afterward. `discovery.is_local_template` answers a
    narrower question about a class that is already in hand, and keeps its two
    callers: nothing in this build ever holds an installed template's class, so a
    class-taking predicate has no third value to return.
    """
    claim = _claims(repo_root).get(name)
    return claim.provenance if claim is not None else None
```

      In `validate.py`, inside `validate_config`, replace the `if template is None:` block with:

```python
    if template is None:
        # One merge, for the reason `resolve_template`'s docstring already gives:
        # `_claims` runs local discovery, which imports every `templates/*.py`
        # and executes every user top level. Asking `template_provenance` and
        # then `_claims` would do that twice more in a command that has already
        # done it once.
        claim = _claims(repo_root).get(name)
        if claim is not None and claim.provenance == "installed":
            c.error(
                "E-TEMPLATE-INSTALLED-UNSUPPORTED",
                "experiment_type",
                f"names `{name}`, which {claim.provider} registers as a "
                "`publishable.templates` entry point — but core resolves an installed "
                "template's name without importing its package, and loading one is not "
                "implemented in this build; installed templates will be honored in a "
                "later slice. Use a project-local `templates/` file or a core template "
                "for now",
            )
        else:
            c.error(
                "E-TEMPLATE-UNKNOWN",
                "experiment_type",
                unknown_template_message(name, known),
            )
        return None  # every later check reads the spec
```

      importing `_claims` from `publishable.templates.registry`. `template_provenance` is the public
      answer for a caller that has only a name; `validate_config` needs the provider string too, so
      it takes the claim itself and reads both off one merge. **Both branches return `None`** — the reason the existing branch does ("every later check reads the
      spec") is unchanged, and `validate` collecting rather than aborting does not mean a check with
      no template can run.

- [ ] **Step 4: Do not touch `materialize.py`'s or `_check_versions`' `is_local_template` call.**
      Read both and confirm you left them alone. Task 10 changes what `_check_versions` *compares*,
      not how it decides to skip.

- [ ] **Step 5: Document it — and do NOT change any count phrase in § The one config file.** The
      sentence reading "**Two** declarations above are not yet built" counts *config declarations
      marked `NOT BUILT` in the fenced example*, and an `experiment_type` naming an installed
      template is not one. Read that rule first, then edit. In the identifying-fields paragraph — the
      same sentence task 5 edited — the clause now reads "…or this project's own `templates/`
      registers;". Extend it:

```
…or this project's own `templates/` registers — an installed one is answered from package metadata, so a name no distribution declares is refused without importing anything, and a name one *does* declare is [not yet loadable in this build](#the-one-config-file);
```

      and add `E-TEMPLATE-INSTALLED-UNSUPPORTED` to the sentence in the same section that names the
      `-UNSUPPORTED` family, which reads "**Two declarations above are not yet built, and each is
      marked `NOT BUILT` where it appears**". Do **not** change its count — that sentence counts
      *config declarations* marked `NOT BUILT` in the fenced example, and an installed template name
      is not one of them. Instead append to that sentence's own paragraph:

```
A third refusal in the same family is not a declaration at all and so is marked nowhere above: an `experiment_type` naming a template an installed distribution registers is refused, because core resolves such a name from package metadata and this build does not load what the name points at. It carries `E-TEMPLATE-INSTALLED-UNSUPPORTED` and, like every `-UNSUPPORTED` code, [no row in the registry below](#errors-validate-reports).
```

- [ ] **Step 6: File the residual.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — an installed template's name resolves but its class is never loaded — **Owner: unassigned**

H7b Part A task 8 makes an installed distribution's `publishable.templates` entry point a claim in
the merge, so its name is known, collisions against it are decided, and `template_names` lists it.
Task 9 refuses a config naming one, as `E-TEMPLATE-INSTALLED-UNSUPPORTED` — the `-UNSUPPORTED` build
family, no § Errors row.

The refusal exists because decision 3 of `2026-08-16-plugin-registries-design.md` states the
entry-point invariant of **resolution** and not merely of the negative answer: "`validate` resolves a
name *without importing a line*". Loading the one entry point a config names would answer a narrower
reading of the same sentence and is the natural next step, but it is a decision, not an oversight,
and it is not H7b Part B's — Part B is the resolver half and its nine tasks do not touch template
loading.

**What retiring it needs:** `Claim.cls` populated for an installed claim; `is_local_template`'s two
class-taking callers (`validate._check_versions`, `materialize.materialize_config`) reading
`Claim.provenance` instead, since `installed` becomes reachable at both for the first time; and
`provenance.plugin_versions` recording which distribution supplied it. **Owner: unassigned.**
```

      Use `git add -f` per `CLAUDE.md`.

- [ ] **Step 7: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 2**.
      Every pre-existing `E-TEMPLATE-UNKNOWN` test must still pass — run
      `uv run pytest -q -k "unknown"` and read the list.

- [ ] **Step 8: Mutate — two.**

  **(a) Collapse the branch.** In `validate_config`, delete the `if provenance == "installed":` arm
  so every unresolved name reports `E-TEMPLATE-UNKNOWN`.
  `test_an_installed_only_template_name_is_known_and_refused` must FAIL on its first assertion
  (`"E-TEMPLATE-UNKNOWN" not in found`). **Checked against the body:** the test asserts both the
  absence of the wrong code and the presence of the right one, so the mutant fails on the first and
  would fail on the second too; and its control asserts the *other* direction with a name nothing
  claims, so a mutant that always reported the new code would fail there instead.

  **(b) Answer provenance from a class rather than from the merge.** Change `template_provenance` to
  `return "local" if name in discover_local(repo_root or Path(".")) else "core"`.
  `test_provenance_is_decided_at_the_merge_for_each_of_the_three_sources` must FAIL on its
  `"installed"` assertion. **Checked against the body:** the fixture declares all three sources in
  one arrangement, so the mutant's two-valued answer differs from the expected one for
  `vendor_assay`. A two-source fixture could not discriminate — that is why the test builds all
  three.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches, stated plainly.** **`installed` is unreachable
      at `validate._check_versions` and at `materialize.materialize_config`** — both take a class,
      and no installed claim carries one in this slice. No test here pins their behaviour under a
      third value because no fixture can produce one, and inventing a fake class to feed them would
      pin a path core never takes. **Nothing in Part A or Part B closes this**; the `spec-defects.md`
      entry filed in step 6 is where it lives, owner unassigned. **`Claim.provenance` for the `core`
      value is pinned only by `template_provenance("generic", …)`**, which is enough — no other
      source can produce it.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: template provenance is three-valued at the merge, and an installed name is known but unloaded`

      Note for step 1: `tests/test_templates.py` must import `template_provenance` alongside its
      existing `from publishable.templates.registry import get_template, template_names`.

---


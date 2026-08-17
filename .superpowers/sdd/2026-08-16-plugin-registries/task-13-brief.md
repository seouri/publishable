## Task 13: `register_probe`, and the check that reads it

**Files:** Modify `src/publishable/plugins.py`, `src/publishable/__init__.py`,
`src/publishable/validate.py`, `src/publishable/generators/template.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_plugins.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `plugins.PROBES` and the decorator shape from task 12; `plugins.names(group)` from task
  7; `BaseTemplate.apparatus_probe: str | None`, declared on the base class and **read by nothing**
  at this commit; `validate_config`'s check sequence, which calls `_check_required_env` and
  `_check_requires_env` from the resolved template before setting `c.credentials`.
- Produces: `plugins.register_probe`, exported; `validate._check_probe(template, c) -> None`
  emitting `E-PROBE-UNKNOWN`; § Validation's *Probe is installed* row backed by a real emit site.

**Why the export and the reader ship together, and it is the trap this task is named in.**
`register_probe` exported bare would be the **fourth** declarable-and-unread surface beside
`field_convention`, `apparatus_probe` and `apparatus_facts` — and the first *exported* one.
`CLAUDE.md` names the distinction precisely: an unbuilt reader of an **unbuilt** surface is
specification, and an unbuilt reader of a **shipped** surface is a defect. So the § Validation
*Probe is installed* row is what consumes it, and that means `validate` reading
`BaseTemplate.apparatus_probe` for the first time. Not defensible as a bare export, and this task
does not attempt it.

**What it is still not.** `Apparatus`, probe execution, the ledger, per-condition facts and the
change gate are **H7d**. This ships registration and the is-it-registered answer, and only because
that row consumes it.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_plugins.py`:

```python
def test_register_probe_records_the_name_and_returns_the_function(registries):
    from publishable.plugins import PROBES, register_probe

    @register_probe("assay_instrument")
    def probe(cfg):
        return {"model": "x"}

    assert PROBES["assay_instrument"] is probe
    assert probe(None) == {"model": "x"}


def test_a_probe_is_importable_from_the_one_root():
    import publishable

    assert "register_probe" in publishable.__all__
```

      and a template fixture plus two tests to `tests/test_validate.py`:

```python
_PROBING_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("probing")
class Probing(BaseTemplate):
    apparatus_probe = "assay_instrument"
    parameter_spec = {}
"""


def test_a_declared_probe_no_distribution_registers_is_reported(git_repo, write_config):
    """The first reader `BaseTemplate.apparatus_probe` has ever had.

    Answered from metadata, so an absent name costs no import — which is also why
    this reports rather than raising: nothing was loaded to fail.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "probing.py").write_text(_PROBING_TEMPLATE)

    found = messages_by_code(write_config({"experiment_type": "probing", "parameters": {}}))
    message = found["E-PROBE-UNKNOWN"]
    assert "assay_instrument" in message
    assert "publishable.probes" in message


def test_an_installed_probe_satisfies_the_check_and_a_template_declaring_none_draws_nothing(
    installed, git_repo, write_config
):
    """THE HONOURING, and the control in one test.

    Without the first half, a `_check_probe` that reported unconditionally passes
    the refusal test above. Without the second, one that reported for every
    template — including `generic`, which declares no probe — would too.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "probing.py").write_text(_PROBING_TEMPLATE)
    installed("dist-one", "1.0", {"publishable.probes": {"assay_instrument": "no_one:probe"}})

    assert "E-PROBE-UNKNOWN" not in codes(
        write_config({"experiment_type": "probing", "parameters": {}})
    )
    assert "E-PROBE-UNKNOWN" not in codes(write_config())  # `generic` declares none
```

- [ ] **Step 2: Run and see them fail.** The plugins tests on `ImportError`, the validate tests on
      `KeyError: 'E-PROBE-UNKNOWN'`. **The honouring test fails on its first assertion only if the
      check exists**; before the implementation it passes vacuously, which is expected — a control
      proves nothing until its sibling passes, and this one is written to go red under the
      mutations in step 6 rather than here.

- [ ] **Step 3: Implement.** In `plugins.py`, beside `register_resolver`:

```python
def register_probe(name: str) -> Callable[[F], F]:
    """Record `name -> fn` for this process and return `fn` unchanged. See
    `register_resolver` for why the mapping is module-global and why the object
    comes back untouched."""

    def decorator(fn: F) -> F:
        PROBES[name] = fn
        return fn

    return decorator
```

      Export it from `publishable/__init__.py` and add `"register_probe"` to `__all__` in sorted
      position — read the list rather than assuming where that is.

      In `validate.py`:

```python
def _check_probe(name: str, template: Any, c: Collector) -> None:
    """The resolved template's `apparatus_probe` against the installed probes.

    Read from package metadata, so a name no distribution declares is refused
    without importing one — the same guarantee every other plugin name is
    answered under. Reported at `experiment_type` because the declaration is the
    template's rather than the config's: a reader who cannot install the plugin
    changes which template the experiment uses, and `experiment_type` is where
    that decision is written.

    Takes the registered name rather than recovering it from the class, which
    cannot be done: a class knows what it was decorated with only until the
    pending buffer is drained, and `validate_config` is holding the name anyway.

    A template declaring no probe is the ordinary case and draws nothing —
    `reference.md` § The apparatus core can only observe: an experiment whose
    measurements never leave the machine declares nothing and records
    `apparatus: null`.
    """
    declared = getattr(template, "apparatus_probe", None)
    if not isinstance(declared, str) or not declared:
        return
    known = names("publishable.probes")
    if declared in known:
        return
    listed = ", ".join(known) if known else "none installed"
    c.error(
        "E-PROBE-UNKNOWN",
        "experiment_type",
        f"resolves template `{name}`, which declares `apparatus_probe: {declared}` — "
        "a name no installed distribution registers in the `publishable.probes` "
        f"entry-point group (registered: {listed})",
    )
```

      Call it as `_check_probe(name, template, c)` from `validate_config`, immediately after `_check_requires_env`, which is the nearest
      check that also reads a declaration off the resolved template rather than off the config —
      name that neighbour in the commit message. **Placing it before the `c.credentials` line is
      deliberate and load-bearing:** a finding appended before that line is still redacted at
      `render`, because redaction happens at render and `Diagnostic` is a frozen record, and moving
      the check after it would look identical while quietly depending on ordering. Do **not** move
      the `c.credentials` line to accommodate it — Global Constraints forbids that outright.

- [ ] **Step 4: Falsify the comment `generators/template.py` carries.** Task 10 rewrote that comment
      and left "`field_convention`, `apparatus_probe` and `apparatus_facts` are declared on the base
      class and read by nothing in this build." That is now false. **Sweep for the claim, not for
      the file** — `grep -rn "read by nothing\|apparatus_probe" src/ docs/reference.md docs/superpowers/spec-defects.md`
      and read every hit — then correct each:

```python
# `field_convention` and `apparatus_facts` are declared on the base class and
# read by nothing in this build; `apparatus_probe` is read (`validate` checks it
# against the installed probes) but a stub declaring `None` would only ever
# satisfy that check trivially.
```

- [ ] **Step 5: Amend the `spec-defects.md` entry that names the family.** That file carries
      `## OPEN — BaseTemplate.field_convention is declarable and read by nothing`. Read it: if it
      names `apparatus_probe` as a sibling, append an amendment saying `apparatus_probe` gained a
      reader in H7b Part A task 13 and the family is now `field_convention` and `apparatus_facts`.
      **Do not restate the whole entry** and do not retro-edit its original text — a correction is
      appended in the development record.

- [ ] **Step 6: Also amend `CLAUDE.md`'s worked example if it still points here.** `CLAUDE.md`
      § Misreadings' *unbuilt reader of a shipped surface* row cites a member of this family. Read
      it; if it names `apparatus_probe`, move it to `field_convention`, which is still unread. If it
      already names `field_convention`, leave it and say so in the report. **This is the one file
      outside the four documents that a task may edit here**, and only because the re-scoping's § 9b
      names the obligation.

- [ ] **Step 7: Run and see them pass**, then the whole suite. Expected: predecessor's count **+ 4**.

- [ ] **Step 8: Mutate — three.**

  **(a) Delete the check's call site.** Remove `_check_probe(...)` from `validate_config`.
  `test_a_declared_probe_no_distribution_registers_is_reported` must FAIL with
  `KeyError: 'E-PROBE-UNKNOWN'`. **Checked against the body:** the test indexes `messages_by_code`
  by that code, so a missing finding is a `KeyError` rather than a silent pass. This is the mutation
  that proves the export has a reader at all, which is the whole reason this task exists.

  **(b) Report regardless of the installed set.** Change `if declared in known: return` to
  `if False: return`. `test_an_installed_probe_satisfies_the_check_and_a_template_declaring_none_draws_nothing`
  must FAIL on its **first** assertion. **Checked against the body:** the fixture installs a
  distribution declaring exactly that probe name, so the two branches genuinely differ; without the
  installed distribution the test could not tell this mutant from correct code, which is why it
  takes the `installed` fixture.

  **(c) Report for a template declaring no probe.** Change the guard to
  `if declared is None: declared = "?"` — i.e. drop the early return. The same test must FAIL on its
  **second** assertion, where `generic` declares nothing. **Checked against the body:** the second
  assertion runs `write_config()` with no override, so the resolved template is `generic`, whose
  `apparatus_probe` is `None`. This is the mutation the second half of that test exists for, and the
  reason both halves live in one test rather than two.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 9: Which deliverable no mutation reaches.** **`PROBES` has no production reader** —
      `_check_probe` reads the *metadata* scan, not the decorator's mapping, because answering from
      metadata is the guarantee and the decorator's mapping is only populated once a plugin has been
      imported. **H7d closes it**, where a probe is actually executed. So `register_probe` is
      exported with a reader for the *name* and none for the *object*, which is a narrower claim
      than "it ships with its reader" and is the true one — say so in the task report. The
      `E-PROBE-UNKNOWN` message's *path* (`experiment_type`) is unpinned, as every finding path in
      this slice is.

- [ ] **Step 10: Verify and commit.** All four commands.
      `feat: register_probe, and the Probe-is-installed check that reads apparatus_probe`

---


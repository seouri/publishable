## Task 20: Decision 3 — `PartialLoadError` semantics for the entry-point half, and its residual

**Files:** Modify `src/publishable/templates/registry.py`, `docs/reference.md`,
`docs/superpowers/spec-defects.md`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `registry._claims`' `PartialLoadError(..., partial_templates=[claim.cls for these in
  claims.values() for claim in these if claim.cls is not None])`, written by task 8;
  `discovery.PartialLoadError`, whose docstring says it "carries every class this discovery pass got
  far enough to construct"; `validate_config`'s `except ContractError` guard, which reads
  `getattr(exc, "partial_templates", None)` and sets `c.credentials` from what those classes
  declare; `secrets.redact(text, values)`, which replaces a value by exact match.
- Produces: the payload expression named as the concept it is, in a comment; § Secrets & credentials
  extended with the second case redaction does not cover; a `spec-defects.md` entry for the residual.

**The residual, stated exactly.** H7c gave `discovery`/`registry` a `PartialLoadError` whose payload
is the classes a discovery pass constructed, so a credential a *refused* file declared can still be
redacted out of the refusal's own message. Task 8 added a third claim source to the merge that
raises it. **The entry-point half structurally cannot carry a class**: the scan is metadata-only, by
decision 3, so a plugin-side collision holds no `parameter_spec` and no `required_env` to read, and
its finding cannot be redacted the way a local one's is. That is a **documented residual, not a
defect to fix** — the natural repair is calling `.load()`, which destroys the exact invariant the
mechanism exists for, and the temptation will arrive dressed as "we need the class to redact its
credentials."

**What task 8 already got right, and what is left.** Task 8's expression reads `claims.values()`
rather than `local.values()`, so it already names "every class this pass constructed" rather than
"every local class" — the proxy the re-scoping's § 10 flags is gone. What is left is that **nothing
distinguishes the two**: no installed claim carries a class in Part A, so the two expressions are
behaviourally identical and **no mutation reaches the difference.** This task says that in the code,
in the document, and in the defects file, rather than adding a test that cannot fail.

- [ ] **Step 1: Write the test that *is* available.** Append to `tests/test_validate.py`:

```python
_CREDENTIALED_TEMPLATE = """\
from publishable import BaseTemplate, register_template


@register_template("generic")
class Shadower(BaseTemplate):
    required_env = ["SHADOW_KEY"]
    parameter_spec = {}
"""


def test_a_collision_redacts_what_a_local_claimant_declared_and_cannot_redact_an_installed_one(
    installed, git_repo, write_config, monkeypatch
):
    """Both halves of decision 3 in one test, because the second is only legible
    beside the first.

    A local claimant's class is in hand at the merge, so its declared credential
    is redacted out of the collision's own message. An installed claimant is a
    name and a distribution — the scan never imported it — so nothing of what it
    declares is available to match against, and that is the mechanism rather than
    a gap.
    """
    monkeypatch.setenv("SHADOW_KEY", "SENTINEL-sk-abc123")
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "mine.py").write_text(_CREDENTIALED_TEMPLATE)

    c = Collector()
    validate_config(write_config(), c)
    rendered = c.render()

    assert "E-TEMPLATE-COLLISION" in rendered
    # The local claimant's declaration reached `c.credentials`, which is the
    # whole of what `partial_templates` is for. Asserted on the RENDERED text,
    # since redaction happens at render.
    assert "SENTINEL-sk-abc123" not in rendered
    assert "<redacted:SHADOW_KEY>" in rendered or "SHADOW_KEY" in rendered
```

      **Read `_CREDENTIALED_TEMPLATE` against the message before believing this test**: the value is
      only redacted if it appears in the message at all, and a collision message names providers
      rather than credentials. If the sentinel never appears in the un-redacted message, the
      `not in` assertion is vacuous — **so first run the test with `redact` disabled** (patch
      `publishable.diagnostics.redact` to return its first argument, by full module attribute path)
      and confirm the sentinel **is** present. If it is not, the collision message does not carry a
      credential, and this test cannot discriminate: **delete it, and record in the task report that
      no test in this slice reaches the payload at all.** That outcome is acceptable and expected;
      what is not acceptable is shipping the assertion without checking.

- [ ] **Step 2: Name the concept in the code.** In `registry._claims`, above the
      `partial_templates=` expression:

```python
                # Every class this merge constructed, whether or not it ends up
                # usable — the same set `discover_local` accumulates, so a caller
                # that never gets a resolved template can still ask an abandoned
                # class what credentials it declares. An installed claim
                # contributes nothing here and structurally cannot: its claim is
                # read from package metadata and no module was imported, so there
                # is no class to ask. That is the cost of the guarantee rather
                # than a gap in this expression — see § Secrets & credentials.
```

      **Do not enumerate which sources contribute** — that is a call-site enumeration in a comment,
      which this repo has had go stale twice.

- [ ] **Step 3: Document the second uncovered case.** § Secrets & credentials' paragraph beginning
      "A template's own file failing to load or colliding with another is covered too" ends with
      "The one case that isn't: a raise from *inside* a class body, before its own
      `@register_template` line is ever reached, leaves no class behind to ask, and a value that
      reaches only that text is not matched." **Replace "The one case that isn't" with an
      enumeration of two**, since there are now two and the sentence's own construction counts:

```
Two cases aren't. A raise from *inside* a class body, before its own `@register_template` line is ever reached, leaves no class behind to ask. And a collision involving a template an **installed distribution** registers carries no class either, for a sharper reason: such a claim is read from [package metadata](#creating-a-plugin-publishable-plugin-new) and no module was imported, which is the guarantee that makes `validate` cheap and safe — so there is nothing to ask what it declares, and reaching for the class to find out would trade that guarantee for a redaction. In both, a value that reaches only that text is not matched.
```

- [ ] **Step 4: File the residual.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — a plugin-side collision carries no class, so its finding cannot be redacted — **Owner: none; accepted**

H7c's `PartialLoadError` carries the classes a discovery pass constructed, so a credential a refused
`templates/*.py` declared is redacted out of the refusal's own message. H7b Part A task 8 adds
installed distributions as a third claim source to that merge, and an installed claim carries **no
class**: the scan is metadata-only by decision 3 of
`2026-08-16-plugin-registries-design.md`, so nothing was imported and there is no `required_env` or
`parameter_spec` to read.

**Filed as accepted rather than as work.** The repair is to call `EntryPoint.load()`, which destroys
the invariant the entry-point mechanism exists for — that `validate` resolves a name without
importing a line — and § Creating a plugin justifies the whole design by that promise. A named
residual beats a silently weaker guarantee. Recorded here so the next reader meets the argument
rather than the temptation, which will arrive dressed as "we need the class to redact its
credentials."

**Bound on the exposure.** A collision message names providers — a distribution and a version, a
path and a class name — and interpolates no declaration, so the text at risk is an exception's
rather than a credential's by construction. What is unmatched is a credential value appearing in a
message core built from an installed claimant's own data, and no such message exists today.

**Struck when** an installed template's class is held at the merge, which is
`## OPEN — an installed template's name resolves but its class is never loaded`, owner unassigned.
The two close together or not at all.
```

- [ ] **Step 5: Run.** `uv run pytest` — the whole suite. Expected: predecessor's count **+ 1**, or
      **+ 0** if step 1's test proved vacuous and was deleted. Report which.

- [ ] **Step 6: Mutate — one, and its scope is narrow.**

  **(a) Empty the payload.** Change `partial_templates=[...]` to `partial_templates=[]`. If step 1's
  test survived, it must FAIL on `assert "SENTINEL-sk-abc123" not in rendered` — the local
  claimant's declaration no longer reaches `c.credentials`, so the value is printed whole.
  **Checked against the test body:** the assertion is over rendered text and the value is set in the
  environment by `monkeypatch.setenv`, so `credential_values` returns it and redaction has something
  to match — that chain is what makes the two branches differ, and it is exactly what step 1 tells
  you to verify before believing the test.

  **The mutation that does NOT exist, stated so nobody proposes it.** Changing
  `claims.values()` to `local.values()` — the proxy this task is about — **cannot fail any test in
  this suite**, because no installed claim carries a class, so the two expressions produce the same
  list for every fixture that can be built in Part A. It is a mathematical no-op here. Do not write
  a test for it, and do not claim one covers it.

  Revert by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 7: Which deliverable no mutation reaches.** **The whole of decision 3's residual.** No
      mutation distinguishes a payload that names every constructed class from one that names every
      local class, and none can until an installed claim carries a class. **Nothing in Part A or
      Part B closes it**; the `spec-defects.md` entry filed in step 4 is where it lives, and it is
      filed as accepted rather than as work. The § Secrets & credentials sentence is prose and
      unpinned, as every document sentence in this slice is.

- [ ] **Step 8: Final sweep for this slice.** Before committing, run the identifier sweep by **file
      list** over the four documents and `src/`, and read every hit:
      `grep -rnE "E-(RESOLVER|PROBE|PLUGIN|READER|UNITS-SOURCE-AMBIGUOUS|TEMPLATE-INSTALLED)[A-Z-]*" docs/reference.md docs/design-principles.md docs/experimental-designs.md README.md src/`.
      Every code minted by this slice must appear where its task put it and nowhere else, and
      `E-TEMPLATE-INSTALLED-UNSUPPORTED` must have **no § Errors row** — that is the `-UNSUPPORTED`
      family's rule and this is the last chance to catch a row someone added. Can-fail control on the
      identical file list: `grep -oE "E-TEMPLATE[A-Z-]*" docs/reference.md | sort -u`.

- [ ] **Step 9: Verify and commit.** All four commands.
      `docs: a metadata-only collision carries no class, and the residual is filed as accepted`

---

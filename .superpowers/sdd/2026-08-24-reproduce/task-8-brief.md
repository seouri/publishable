## Task 8

**Step 6, narrowed: `.env` and `required_env`.** Design Decision 12.

`.env.example` is **tracked** (correction 15), so the clone holds it: write `.env` from it **only when
`.env` does not exist**, never overwrite one, and say which happened. Safe by correction 16 —
`missing_env` treats an empty value as missing. When `.env.example` is absent, say that instead.

**`required_env` is listed only for a template this interpreter can construct** — core's `generic`, or a
project-local `templates/**` discovered by path **in the checkout**. Correction 8 is why: `get_template`
returns `None` for an installed template, and a plugin is installed into the **clone's** environment by
`uv sync`, not into this one. For a plugin-provided template the transcript **names the template and its
plugin and defers to the `validate` line it already prints** — `validate` in the prepared checkout
already reads `required_env` (H7c gave it that reader) in the interpreter where the plugin exists. **This
is a document narrowing and § Reproducing on another device's step 6 must say so** (task 13 owns the
prose; you own the measurement it rests on and must hand it over explicitly).

**Resolving a project-local template imports user code. The containment is copied WHERE IT SITS, not
what it calls.** `report`'s shipped credential leak came from lifting `freeze`'s calls without the `try`
they sit inside, and the sibling that already got it right is `report.render_with_override` — **read it
before writing this**. Two rules, both `CLAUDE.md` § Misreadings entries with this repo's scars on them:

- the whole resolution sits inside the credential-bearing `try`, so a template raising at import becomes
  a redacted diagnostic rather than reaching `main`'s un-redacted printer (correction 21);
- the `sys.path` entry is removed **by identity**, never `pop(0)` — user code runs inside that window by
  design, and an override doing its own `sys.path.insert(0, …)` makes a positional pop remove the wrong
  entry. The restoration is pinned **on the failure path**.

**Fixture R**, plus its `pop(0)` arm whose project-local template does its own `sys.path.insert(0, …)` at
import. **The credential is declared through `Param(requires_env=)` and set in the environment**, so the
redaction has a real value to match — an undeclared one passes vacuously. The positive control is the one
that caught the original: `validate` over the identical project printing `<redacted:…>`.

**Mutations:** copy the calls without the enclosing `try` (Fixture R — one path prints the credential
verbatim, the other `<redacted:…>`); remove the `sys.path` entry with `pop(0)` (the inserting-template
arm; **without that template the two are indistinguishable**, which is the fixture the shipped defect
lacked).

**Verify through the real console script.** A credential leak is invisible to a direct call that never
reaches `main` — *a probe proves the moment; a test proves tomorrow*, and both are required here.

**Must not touch:** `secrets.py`, `report.py`, `templates/discovery.py`, `templates/registry.py`.

---


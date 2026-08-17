# H7c — scoped re-review of the whole-branch review's fix round

**Reviewed:** branch `h7c-credentials` at `7130cc0`, against the fix commit `65ee854` and the
whole-branch review's six findings. **Scope: only whether those findings closed, and whether
closing them introduced anything new.** The whole-branch review was not repeated.

**Gates, re-run at HEAD after every mutation was reverted (by editing the file back, never
`git checkout --`, verified by behaviour):** `uv run pytest` → **1997 passed, 2 xfailed**.
`ruff check .` → clean. `mypy` → clean, 43 source files.

**Verdict: NOT READY TO MERGE.** The security property holds end to end (§ Leak probe) and
finding 3's fix is correct on the discriminating shape. What blocks is that **finding 4 did not
close — the false claim it named was propagated from one site to two** — and that the fix round
introduced **one new Important defect of exactly the family this slice keeps hitting** — a
silent behaviour change in the `.env` load path, under a docstring asserting the behaviour is
preserved and citing the very property it breaks (N1) — plus four Minor ones. All are cheap; none
needs a redesign.

---

## Finding-by-finding

| # | Was | Now |
|---|---|---|
| 3 | declared credential to stdout via `E-TEMPLATE-LOAD` early return | **CLOSED** — reproduced both ways, mechanism attacked, one new Minor (N6) |
| 2 | `reference.md` "never anything secret in it" | **CLOSED** at that sentence; introduced N2 and N3 |
| 1 | three comments carrying a falsified count | **CLOSED** at the three named sites; a fourth stale count survives in a file the *same commit* edited (N4), and one replacement over-claims (N5) |
| 4 | guard naming an owner that does not exist | **NOT CLOSED — regressed.** See below |
| 5 | `PYTHON_DOTENV_DISABLED` filing's false dichotomy | Fixed and struck correctly, but the fix changes `override=False` semantics (N1) |
| 6 | dict-valued-parameter filing's wrong reason | **CLOSED** |

### 3 — CLOSED. Reproduced, and the mechanism holds.

**Reproduction, single-file discriminating shape, through `main(["validate", …])`** — one
project-local `templates/plate_assay.py` declaring `required_env = ["PLATE_READER_HOST"]` and
raising *after* its own `@register_template`, value supplied only from `.env`:

```
error   E-TEMPLATE-LOAD      experiment_type
        … raised while importing and registers nothing usable:
        RuntimeError('startup failed host=<redacted:PLATE_READER_HOST> loose=zqx-undeclared-5150')
```

**Proved it was leaking before**, by deleting the five new lines in `validate_config`'s
`except ContractError` branch: same run prints `host=zqx-marmalade-7781` verbatim, and
`tests/test_cli.py::test_a_declared_credential_reaches_no_diagnostic_when_its_own_template_fails_to_load`
goes red. Restored by editing the lines back; the test is green again. The shipped test is real.

**Mechanism, attacked six ways.** Shapes probed independently through `validate`:

| Shape | Result |
|---|---|
| Sibling declares, later file raises (`a_plate.py` / `z_broken.py`) | redacted |
| Sibling declares **after** the raising file alphabetically (`a_broken.py` / `z_plate.py`) | redacted — the loop `continue`s and keeps importing, so declaration order is not load order |
| Raise from **inside the class body**, before its own decorator | **leaks** — the documented residual |
| `@register_template` applied to a non-`BaseTemplate` | reported, no declared credential involved |
| Local template shadowing `generic` (`E-TEMPLATE-COLLISION` from `registry._merged`) | redacted set carried; the message interpolates no user exception text, so this path is defensive rather than load-bearing |
| Partial class with malformed `parameter_spec` | **`validate` raises** — see N6 |

- **Escape risk of `PartialLoadError`:** it subclasses `ContractError`, `code`/`str(exc)` are
  unchanged (`errors.py` gives `ContractError` no custom `__str__`, so
  `PartialLoadError(str(fault), code=fault.code, …)` round-trips the message exactly). Every
  `except ContractError` in `src/` was read: none reconstructs the exception
  (`raise ContractError(str(exc), …)` or `type(exc)(…)`), so none can silently drop
  `partial_templates`. `cli.py:2094` only formats. The non-standard `__init__` breaks pickling —
  but `ContractError` already requires `code=` as a keyword, so that is pre-existing, not new.
- **Executing anything further:** `BaseTemplate` has no metaclass, so reading a class attribute
  off a class whose body already ran runs nothing. The exception is N6.
- **Sweep of `discovery.py`/`registry.py` raise sites by *what they interpolate*, not by name:**
  every raise carrying user-supplied text (`{exc!r}`, `{exc.code}`, `{cls!r}`, a path) is now a
  `PartialLoadError`. The `if not registered:` branch and `ImportError` at `discovery.py:190`
  interpolate only a path.
- **The other early returns, verified independently rather than taken from the fix author's
  report.** `load_document` → `E-CONFIG-PARSE` interpolates a `yaml.YAMLError`, not user-code
  exception text, and runs *before* `load_env`, so `credential_values` would be empty on two
  independent grounds; `_check_shape`'s findings interpolate no exception; the
  `E-TEMPLATE-UNKNOWN` branch calls `unknown_template_message`, which interpolates a name and a
  known-name list. None embeds a raising file's exception text. Confirmed.
- **The residual statement is accurate and, for *declared* credentials, complete.**
  `reference.md`'s *"a raise from inside a class body, before its own `@register_template` line is
  ever reached, leaves no class behind to ask"* — reproduced, it leaks. The adjacent shape (a
  module-level raise *before* the class statement) also leaves no class, but it also leaves the
  variable declared by nothing, so it falls under the already-stated **declared** limit rather
  than being a second unnamed residual. The sentence's scope is right.

### 4 — NOT CLOSED. The false owner was propagated, not removed.

The review's finding was that `_check_required_env`'s guard *"names an owner that does not
exist"*. The fix made the guard identical at all three sites — correct — but then wrote **two new
comments asserting the same non-existent owner**, and they now contradict the third:

- `cli.py:342` and `validate.py:901`, both new: *"Same guard `validate._check_required_env`
  **reports against** — a template declaring something other than a list **is that check's finding
  to make**, not this collector's shape to guess at."*
- `validate.py:797`, also new, same commit: *"**Nothing reports** a `required_env` that is not a
  list — **this repo has no check for it anywhere** — so a template declaring one this way is a
  silent author mistake rather than a diagnosed one."*

Both cannot be true. `_check_required_env` `return`s silently; it makes no finding. **The
charitable parse does not rescue it:** "the same guard that `_check_required_env` reports *against*"
could be read as "the guard that gates whether that check reports at all", which is true — but the
next clause, *"a template declaring something other than a list is that check's finding to make"*,
asserts an owner outright, and there is none. That clause is the whole of what the review's finding
4 was about. The comment
the review asked to be corrected was corrected, and its false claim was copied to two fresh sites
in the same commit. `CLAUDE.md` § Habits that cost real work, first bullet — and this is now the
second round in which the same sentence has been shipped.

**Fix:** delete "reports against … is that check's finding to make" at both collectors; the true
statement is the one already written at `validate.py:797` — nothing anywhere reports it, and the
guard is identical at three sites so a malformed `required_env` is ignored alike rather than
iterated as characters in one place. Verified as before: `grep -rn "required_env"
src/publishable/` still returns no reporter.

### 1 — CLOSED at the three named sites; a fourth survives (N4), one replacement over-claims (N5).

The three replacements are true, and no new number was introduced at any of them.
`runner.py`'s wording correctly declines the review's suggested sentence: `main`'s stderr
catch-all is not a diagnostic, so *"the other places are diagnostics"* would have been false — the
shipped sentence scopes to *"every other place core interpolates an exception **into a
diagnostic**"*, which is true. Swept `src/`, `tests/` and the four documents for surviving
redaction-site counts (sweep proved able to fail: the same grep against a known-present string
hits). Counts under `docs/superpowers/` were left alone — those are dated records.

### 2 — CLOSED at `reference.md:3485`.

The three paragraphs now compose in sequence: the narrowed guarantee ("core never writes a
**declared** credential's value into a record of its own"), the redaction paragraph, the limit
paragraph, and the new load-fault paragraph. The undeclared negative control in § Leak probe is
exactly the case the limit describes, and it is no longer contradicted. The section's own
pre-existing *"the two constructions above"* is still accurate after the fix — the fix populated
the credential set earlier, it did not add a third boundary. Two new defects were introduced in
the same edit: N2 and N3.

### 5 — Fixed and struck correctly, with one new defect (N1).

- **Strike is in place, not deleted** — the whole entry is `~~`-wrapped with a `**STRUCK
  2026-08-16 (H7c whole-branch review, finding 5): FIXED, not merely re-reasoned.**` paragraph
  beneath, matching `spec-defects.md`'s established convention. Nothing elsewhere links to it
  (`grep` for `PYTHON_DOTENV_DISABLED` outside that file hits only `secrets.py`'s new docstring
  and the new test).
- **Bool contract intact.** `bool(values)` matches `load_dotenv`'s own return (`True` iff the
  parsed mapping is non-empty), so comment-only/empty → `False`, all-already-set → `True`, exactly
  as the docstring says.
- **Bare `KEY` treated as missing, not empty.** Verified: `dotenv_values` yields `None`, the loop
  skips it, `os.environ` is untouched, `missing_env` reports it. Pinned by the shipped test.
- **`override=False` for directly-assigned values: preserved.** A shell value still wins.
- **`override=False` for *interpolated* values: NOT preserved.** See N1 — this is the real defect.

### 6 — CLOSED.

The correction is in place, and it says the true thing: the refusal is `E-PARAM-UNKNOWN` on the
nested leaf, the `choices` check never sees the parent path at all, and the surviving defect is a
misleading message on an already-refused config. Both the body and the `**Severity:**` line were
corrected, so the entry carries no surviving copy of the false reason — the "sweep for the claim,
not the file" trap was avoided here.

---

## New defects introduced by the fix round

### N1. Important — the `load_env` rewrite silently changes `override=False` semantics for interpolated values, and the docstring claims it doesn't. **Blocks.**

`dotenv_values` constructs its parser with `override=True` internally; `load_dotenv(override=False)`
does not. That flag decides **where a `${VAR}` reference resolves from**, not only what gets
written. Probed, both through `secrets.load_env` and directly:

`.env`:
```
ACCOUNT=prod
API_URL=https://${ACCOUNT}.example.com/key
```
with `ACCOUNT=staging` exported in the shell:

| | `ACCOUNT` | `API_URL` |
|---|---|---|
| Old (`load_dotenv(override=False)`) | `staging` | `https://staging.example.com/key` |
| New (`dotenv_values` + `setdefault`) | `staging` | **`https://prod.example.com/key`** |

The new docstring says *"`setdefault` **is** exactly `override=False`"* and *"keeping
`override=False` semantics … intact"*, and justifies the direction with *"a stale `.env` cannot
silently redirect a run to the wrong account."* **That is precisely the property this change
breaks** — a stale `.env` now wins inside an interpolation even when the shell sets the variable
it interpolates. `reference.md` § Secrets & credentials's *"The load never overrides a variable
already exported"* is likewise now true only of directly-assigned values.

This is a comment claiming a guarantee the code does not provide, in the security-relevant load
path, introduced by a commit whose own subject line is about closing false claims.

**The flag is what gates it**, confirmed by reading the installed package rather than inferred:
`dotenv/main.py`'s `resolve_variables(values, override)` builds the interpolation environment as
`new_values` then `os.environ` when `override` is false, and the reverse when it is true —
`dotenv_values` passes `override=True` unconditionally, `load_dotenv` passes it through.

**Fix:** either resolve interpolation the old way — `dotenv.main.DotEnv(path, stream=None,
verbose=False, interpolate=True, override=False).dict()`, which takes the flag `dotenv_values`
hardcodes (and, like `dotenv_values`, never consults `PYTHON_DOTENV_DISABLED`) — or keep `dotenv_values` and state the changed semantics in both the docstring and
`reference.md` rather than claiming they are unchanged. Either way the current claim must go. A
test pinning it needs a `${VAR}` fixture; none exists (the two new tests exercise
`PYTHON_DOTENV_DISABLED` and the bare-`KEY` skip, neither of which touches interpolation).

### N2. Minor — a new `reference.md` sentence uses "does not exist" where the paragraph's own convention is `[NOT BUILT]`, and collapses the contrast in the sentence after it.

`docs/reference.md:3279`, added by the fix: *"The merge still has nothing to read from, though —
**the credentials region itself does not exist** for `generate experiment` to merge into, which is
filed separately in the development record."*

This is *not* a contradiction of the fenced § The generated README block above it — that block is
specification, and marking parts of specified content `[NOT BUILT]` in the prose beneath is this
paragraph's established way of showing specified-but-unemitted content. The defect is narrower:
the sentence says "does not exist" where the same paragraph says `[NOT BUILT](#generators)` two
clauses earlier, and that vocabulary makes an undated build claim read as a spec claim.

What it costs is the next sentence, whose job is to **contrast**: *"A parameter table's gap is
**different in kind** — the scaffolded README shown above declares no managed region for one at
all."* Under the new sentence's phrasing both gaps read as "the region isn't there", so the
contrast collapses. `CLAUDE.md` § Citing a sentence whose job is to contrast.

**Fix:** say the credentials region is specified and its **emission** is NOT BUILT. That restores
the contrast — the parameter table has no region *in the specification*, the credentials one does
and is not emitted yet — and keeps the paragraph in one vocabulary.

### N3. Minor — a new positional reference, in a slice that has an OPEN filing for exactly that.

`reference.md:3485`, added by the fix: *"see **the limit below** for what it does not cover."*
`CLAUDE.md` bans locating anything by position, and this slice's own `spec-defects.md` carries an
OPEN entry for a pre-existing positional reference elsewhere in this file. The target has a
nameable lead-in — *"The limit of that, stated rather than discovered"* — so it is nameable.

### N4. Minor — a stale count survived in a file the fix commit itself edited.

`src/publishable/generators/template.py:7`: *"The stub emits the **five members anything reads** —
`parameter_spec`, `validate`, `aggregate`, `naming_pattern`, `default_repeats`."* The same comment,
rewritten by the same commit, then says *"`required_env` **now has a reader** (`validate` checks
it)."* Six members are read; the phrase claims five are all there are. Finding 1's shape,
reintroduced in the act of closing finding 1 — and missed because the sweep ran over the three
sites the review named rather than over the claim. (`"none of BaseTemplate's other four"` is still
correct: four members go un-emitted.)

**Fix:** *"the five members this stub emits — … — and none of `BaseTemplate`'s other four"*, which
drops the exhaustiveness claim without minting a new number.

### N5. Minor — `diagnostics.py`'s replacement over-claims coverage.

*"every one of those constructions reaches a reader through a `Collector`, whatever their number,
and **a site added later is covered without a second edit here**."* The first half is true and is
the property worth stating. The second is not: `Collector.render` redacts only what
`c.credentials` holds, and the whole-branch review enumerated three collectors — `warn_c`,
`dirty_c`, `io_c` — that are never given it. A future diagnostic carrying exception text in one of
those is *rendered* through the chokepoint and *not* redacted. The honest property is "every
diagnostic's text passes through one method", not "every later site is covered."

### N6. Minor — `validate` now raises on a path that previously reported cleanly.

A project-local template declaring `parameter_spec = "not-a-dict"` and raising after its own
`@register_template`: before the fix, `validate` reported `E-TEMPLATE-LOAD` and exited 1. After
it, `declared_credential_names_for` is called on the partial class and dies —
`AttributeError: 'str' object has no attribute 'items'` at `validate.py:909`, an uncaught
traceback. Verified as a regression by deleting the five new lines and re-running the same fixture
(clean report returns).

The same crash **pre-exists** on the resolved path (`_check_requires_env`, `validate.py:840`), so
this is a pre-existing fragility newly reachable rather than a new one — but it is newly reachable
on the one path that is *by definition* about a malformed file, and `validate_config`'s own new
comment cites *"`validate` is contracted never to raise"* four lines above the call that breaks it.

**Fix:** guard `spec` with `isinstance(spec, dict)` at **both** readers —
`declared_credential_names_for` (`validate.py:908`) *and* `_check_requires_env`
(`validate.py:839`) — the same way `required_env` is now guarded at three sites. Guarding only the
new reader closes the new reachability and leaves the pre-existing resolved-path crash raising.

---

## Leak probe — end to end, written independently and re-run at HEAD

Full `run` of a project-local template `plate_assay`, credential names deliberately unlike
secrets, values distinctive but not secret-shaped, **declared both ways** so the `required_env`
path and the per-value `requires_env` path each carry a value:

- `required_env = ["PLATE_READER_HOST"]`; `reader.vendor` a two-choice `Param` with
  `requires_env={"acme": ["PLATE_READER_TOKEN"], "bex": []}`, config selecting `acme`.
- `.env`: `PLATE_READER_HOST=zqx-marmalade-7781`, `PLATE_READER_TOKEN=zqx-jam-2211`,
  `SIDECAR_NOTE=zqx-undeclared-5150` — the last **declared nowhere**, the negative control.
- The step raised `RuntimeError("vendor call failed host=… token=… loose=…")` with all three
  verbatim. Exit 4.

Sweep over the **file list** (`rglob`, filtered by path; the search output is never filtered),
34 → 28 files:

| Value | Files hit |
|---|---|
| `PLATE_READER_HOST` (declared) | 1 — `.env` only |
| `PLATE_READER_TOKEN` (declared, per-value) | 1 — `.env` only |
| `SIDECAR_NOTE` (undeclared control) | 3 — `.env`, `run.yaml`, `executions.jsonl` |
| `publishable` (**sweep-can-fail control**) | 13 |

`run.yaml` and `executions.jsonl` both carry `<redacted:` markers and the surrounding text intact.
`allocation.json` is absent for this fixture, which is why the sweep globs rather than naming
files. stdout and stderr: zero hits for either declared value. Something that must report fired —
the run failed and the error text was written — so the sweep is not vacuous.

**The security property holds end to end.** The undeclared value is not redacted, which is the
documented limit behaving as documented rather than a gap.

---

## Note, not a finding

`.superpowers/sdd/.gitignore` is **clobbered to a bare `*` in the working tree right now**
(uncommitted, present before this review began) — the documented `scripts/sdd-workspace` behaviour.
Restore its committed content, and commit this file with `git add -f`.

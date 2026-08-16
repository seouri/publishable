# Task 10 review — the `requires_env` union over the conditions the sweep resolves

Reviewed `9e62b9e..2852ea0` on branch `h7c-credentials`. Baseline re-measured before and after every
mutation: `uv run pytest` → **1982 passed, 2 xfailed**; `ruff check` clean; `ruff format --check` →
76 files already formatted; `mypy` → 43 files, no issues. Every mutation below was applied by
editing, reverted by copying back a pre-mutation copy of `src/publishable/validate.py` saved before
the first edit, `__pycache__` deleted between runs, and the revert verified by `diff -q` against
that copy plus a re-run — never `git checkout --`. Probe tests were appended to
`tests/test_validate.py` and the file restored byte-identically afterwards (`git status` clean apart
from the `.superpowers/sdd/.gitignore` clobber noted at the end, which I restored from `HEAD`).

**Verdicts: spec compliance ✅ — task quality ❌.**

---

## What I verified as correct

- **The three readings are genuinely separated by the fixture** — verified myself, not taken from the
  report.
  - **A (shipped)** reports `{OPENAI_TEST_KEY}` alone: the shipped code passes
    `test_the_union_is_over_the_conditions_the_sweep_resolves`, which asserts `len(found) == 1` and
    `"OLLAMA_TEST_KEY" not in message`.
  - **B (union over all `choices`)**: replacing the per-condition resolution with
    `for value in param.requires_env:` fails **three** tests — the reading-A test, the honouring test
    (`codes(...) == set()` gains `E-CRED-PARAM-MISSING`), and the default-fallback test, whose
    message became ``is `ollama` in the base parameters, which requires `OLLAMA_TEST_KEY` `` —
    confirming both the membership difference **and** the mis-attribution the report describes.
  - **C (the written value only)**: deleting the `condition.values` overlay leaves `found == []` and
    fails the reading-A test with `assert 0 == 1`.
  - Mutation (c), dropping the `param.default` fallback, fails
    `test_an_undeclared_parameter_falls_back_to_the_template_s_default` with
    `KeyError: 'E-CRED-PARAM-MISSING'`, as predicted.
- **The condition label is derived, not assumed.** `expand({'sweep': {'grid': {'llm.provider':
  ['azure_openai','openai']}}})` prints `['provider=azure_openai', 'provider=openai']`, so the
  literal `condition \`provider=openai\`` in the test is the one the code actually renders.
- **The message names the three facts and no credential value.** Finding `path` is
  `parameters.llm.provider` (asserted); the message names the resolved value and the condition label.
  Leak probe run in the shape that **can** fail (the trivial shape cannot: a variable with a value is
  never reported): `AZURE_TEST_KEY="sk-sentinel-9x"` **set**, `OPENAI_TEST_KEY` unset, sweep
  selecting both, then `Collector.render()` — the sentinel appears nowhere in the rendered output,
  which carries only `OPENAI_TEST_KEY`'s name, the parameter's resolved value, and the label.
- **Environment hygiene.** `_union_project` `delenv`s all three names before `setenv`ing the chosen
  ones, so the answer is a property of the check and not of the machine; `monkeypatch` is used in
  both directions; the negative tests are paired with a control that sets the keys and asserts
  `codes(...) == set()`. No second autouse fixture is added.
- **Two cited claims check out.** `_condition_labels` really does wrap `expand(doc)` in
  `except Exception: return None`, so the guard's citation is accurate; and `requires_env` totality
  over `choices` is enforced in `src/publishable/param.py` (both `absent` and `extra` are rejected),
  so the docstring's "total over `choices`" is true.
- Semantics match `docs/reference.md` § Errors' `E-CRED-PARAM-MISSING` row clause by clause: union
  over the conditions `expand` resolves, reported at the parameter's own dotted path, naming the
  value and the condition, one finding per variable, a value with no key requiring nothing. **Spec
  compliance ✅.**

---

## Findings

### Important 1 — the attribution the § Errors row makes normative is unpinned, and a docstring claims the assertion that would pin it

`reference.md` § Errors states *"A variable required by two conditions is reported once, **attributed
to the first that selected it**"*. Nothing tests the attribution. Mutation:
`first_seen.setdefault(variable, (path, value, condition.label))` →
`first_seen[variable] = (path, value, condition.label)` (last-seen). **All 693 tests in
`tests/test_validate.py` pass.** `first_seen` is keyed on the variable, so `len(found) == 1` still
holds, and `test_a_variable_two_conditions_need_is_reported_once` asserts only
`"OPENAI_TEST_KEY" in found[0].message` — both conditions that select `openai` produce the same
variable and the same value, so only the **label** differs and no assertion reads it.

That test's docstring says *"Attributed to the first condition that selected it, which is why the
assertion below names `openai` and not the later duplicate"* — the name-claims-the-guarantee shape
`CLAUDE.md` lists, and the second half is simply false: no assertion below names a condition. In the
single-condition test the attribution is right by accident (only one condition selects `openai`),
which is exactly the "right by accident on a two-condition fixture" hole the brief warned about.

Fix: one assertion, with the literal derived rather than assumed — I ran `expand` on that fixture and
the first condition selecting `openai` is `provider=openai__retries=1`; the shipped code emits
``condition `provider=openai__retries=1` `` and the last-seen mutant emits `…__retries=2`. Add
`assert "condition \`provider=openai__retries=1\`" in found[0].message`.

A second consequence, which is the honest answer to *"say what none of the three mutations reaches"*:
**that test pins nothing of its own today.** Its stated job — once-per-variable dedup across two
conditions — is enforced **twice**, by `first_seen` being a dict keyed on the variable *and* by
`missing_env`'s own `seen` set (`src/publishable/secrets.py`), so even replacing the dict with a list
of tuples would still emit once. Its only reachable failure is under mutation (a), which the
reading-A test already catches. The label assertion above is what converts it from structural to
discriminating.

**Verified by:** the setdefault→assignment mutation plus a probe test printing the shipped message.
`grep -rln "E-CRED-PARAM-MISSING" tests/` returns `tests/test_validate.py` alone, so the
file-scoped mutation run (693 tests) is whole-suite coverage for this claim.

### Important 2 — the `except TypeError` guard is reachable and merely untested, not unpinnable, and the report's justification answers the wrong question

The report (and the brief) call the guard unpinned on the grounds that *"no fixture declares a
`list`-typed parameter with `requires_env`"*. That is the wrong question: what reaches `.get(value)`
is the value's type **at resolution time**, and `_check_requires_env` is called **before**
`_check_parameters`, so no type or `choices` check has run yet. A config writing
`parameters: {llm: {provider: ["azure_openai", "openai"]}}` against the task's own `cred_assay`
template resolves a `list` and reaches the lookup. With the guard deleted, that config gives
`TypeError: unhashable type: 'list'` out of `validate.py` — a traceback instead of the
`E-PARAM-VALUE` finding `validate` should collect. With the guard present it reports exactly
`{E-PARAM-VALUE}`.

So the guard is load-bearing and must **stay** (my judgment on the reviewer's question: keep it, do
not delete it). It is nonetheless unpinned: with the guard removed the **full suite** is green
(1986 passed, 2 xfailed, one probe deselected). One test — the list-valued config above asserting
`codes(...) == {"E-PARAM-VALUE"}` — closes it.

**Verified by:** deleting the guard, running the probe config (traceback), and running the whole
suite (green).

The same root cause — running before `_check_parameters` — has a second, non-crashing route worth
folding into the same fix rather than filing separately: `parameters: {llm: {provider: {a: 1}}}`
makes `_flatten` emit `llm.provider.a`, so `llm.provider` is absent from `resolved` and the check
falls back to the **default** and reports ``is `azure_openai` in the base parameters, which requires
`AZURE_TEST_KEY` `` for a config that declares no such value (alongside `E-PARAM-UNKNOWN`).
Cosmetic — the config is refused either way — but the message asserts a resolution that did not
happen.

### Important 3 — the `condition.selectors` skip *is* pinnable; "structurally unreachable" is wrong

The report accepts the skip as unpinned because the group-axis fixture is refused with
`E-SWEEP-PATH-DUPLICATE`. I confirmed the refusal (the predicate at
`src/publishable/validate.py` compares `selector_paths(sweep)` against `template.parameter_spec`, so
any group axis colliding with a declared parameter is always refused) — but the conclusion does not
follow, because **`validate` collects rather than aborting**, so the skip still executes on that
config and the finding set differs:

- shipped: `{E-DATA-ALLOCATION-WITHIN-ARMS, E-SWEEP-PATH-DUPLICATE}`;
- with `if path in condition.selectors: continue` deleted: additionally
  ``E-CRED-PARAM-MISSING: is `ollama` in condition `provider=ollama`, which requires
  `OLLAMA_TEST_KEY` ``.

The implementer ran the prescribed fixture and stopped at "validate refuses it" rather than comparing
finding sets — the probe answered a correlated question ("does the config validate?") instead of the
direct one ("does deleting the skip change what is reported?"). Note also that the spec's own
planning correction 4 records this mutation as "blind because a group axis's name is not a
`parameter_spec` path", which the run above falsifies: the collision only has to exist in
`parameter_spec`, and there it does. Route: the fixture belongs in task 11 (`groups`) or here; either
way, the record should say *pinnable, unpinned* rather than *unreachable* — and that correction
reaches the spec, whose planning correction 4 records this same mutation as blind.

**Verified by:** deleting the skip and running the group-axis probe under both versions.

### Minor 4 — the finding-order comment has nothing behind it

The comment *"insertion order is condition order then declared-parameter order — a deterministic
finding order without sorting away the attribution"* is untested: every shipped reporting test
asserts `len(found) == 1`, so two findings are never produced. Declared and sorted order **do**
differ in a constructible fixture — grid `["openai", "azure_openai"]` with both keys unset emits
`OPENAI_TEST_KEY` then `AZURE_TEST_KEY`, where sorted would be the reverse (note `["azure_openai",
"openai"]` would not distinguish them). Mutating to `sorted(missing_env(first_seen))` leaves the full
suite green (1986 passed, 2 xfailed). Minor rather than Important only because § Errors makes no
order claim for this code, unlike `E-CRED-MISSING`'s row.

**Verified by:** the `sorted(...)` mutation over the full suite, plus a probe emitting two findings.

### Minor 5 — a docstring sentence that contradicts the sentence before it and invents an owner

`_check_requires_env`'s docstring: *"`sweep.ablate.remove` sets a nullable parameter to `null`, which
is a legal resolved value and not a choice. **Reporting it here would be a second report of a fault
`_check_sweep` already owns.**"* If the value is legal there is no fault for `_check_sweep` to own,
and `reference.md`'s row stops correctly at *"which is not a choice"*. The behaviour is right; the
justification is a claim the code does not support — the dominant defect shape of this slice. Delete
the last sentence.

**Verified by:** reading `sweep.removal_value` (a nullable target resolving to `null` is what the
mode is defined to produce) and comparing against `docs/reference.md` § Errors' own wording.

### Minor 6 — a stale count in a docstring

`test_a_template_declaring_no_requires_env_reports_nothing`: *"which is why the other 1957 tests are
unaffected"*. The suite was 1977 before this task and is 1982 after. Phrase it without the number.

---

## Not findings, recorded so the next reader does not re-derive them

- `test_a_template_declaring_no_requires_env_reports_nothing` is a pure-absence control with no
  distinguishing mutation (`if not wanted: return` and an empty-`wanted` loop are the same no-op).
  That is a property of the check, not a hole.
- The report's account of the brief's Step 7 shape error (`{"llm.provider": [...]}` vs.
  `[{by, levels}]`) is correct; `sweep.groups` is a list of blocks.
- `.superpowers/sdd/.gitignore` was found clobbered to a bare `*` during this review and restored
  from `HEAD` (`git show HEAD:… > …`), per `CLAUDE.md`.

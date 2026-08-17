# Task 3 review: `Param(requires_env=)` — the constructor argument

**Reviewed:** `e3ac3a4..ceff925` (`fbab1e8` is the code commit) on branch `h7c-credentials`.

**Verdicts**

1. **Spec compliance — ✅**
2. **Task quality — ❌** — **no shipped behaviour is wrong**; the constructor argument, both refusals,
   the message, the storage and the `E-TEMPLATE-LOAD` route are correct and each is pinned by a
   mutation I ran. The ❌ is two false prose claims: one in a test docstring, one in the tracked
   report. Both are cheap to fix and neither touches `src/`.

**Note for whoever commits this file:** `.superpowers/sdd/.gitignore` was found clobbered to a bare
`*` (the `scripts/sdd-workspace` failure `CLAUDE.md` names by hand). I restored its content from
`HEAD`; `git check-ignore` now reports this review as not ignored. Use `git add -f` anyway.

**Baseline reproduced before attributing any red:** `uv run pytest -q` → **1962 passed, 2 xfailed**;
`uv run ruff check .` clean; `uv run ruff format --check .` → 74 already formatted; `uv run mypy` →
42 source files, no issues. Re-run after every mutation was reverted: identical. All mutations were
reverted by restoring a pre-mutation copy and verified by `diff` **and** by re-running the suite —
never by `git status`. `__pycache__` cleared between each.

---

## Findings

### Important — the docstring of `test_a_total_requires_env_constructs_and_leaves_every_other_check_alone` claims a guarantee the code does not provide

`tests/test_param.py`:

> *"The honouring. Without it, ignoring `requires_env` entirely — storing it and checking nothing —
> passes every refusal test above."*

**Falsified by mutation.** I removed the whole `if requires_env is not None:` block from
`src/publishable/param.py` (lines 56–74) while leaving `self.requires_env = requires_env` in place —
which is exactly "storing it and checking nothing". Result:

```
FAILED tests/test_param.py::test_requires_env_is_stored_and_needs_choices
FAILED tests/test_param.py::test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets
2 failed, 14 passed
```

Both refusal tests above it go red, and `test_a_total_requires_env_constructs_and_leaves_every_other_check_alone`
itself stays **green**. The sentence is false in both halves. The task's own report is the second
witness: its mutation (a) is the same deletion and reports the refusal test red.

**Provenance, which is why it reads plausibly:** the sentence is transplanted from the slice spec's
§ *What the scoping overturned* — *"Without it, ignoring `requires_env` entirely passes the suite"* —
where it is a claim about the **environment check** (tasks 9–11), and true there. Moved onto
`Param.__init__` it is false.

**Not a reason to delete the test.** The test does pin something no other test reaches, which I
confirmed: injecting a `requires_env` leak into `check()` —

```python
if self.requires_env is not None:
    return "declares a credential requirement"
```

— turns **only** this test red: `uv run pytest tests/test_param.py tests/test_validate.py -q -k
requires_env` (no `-x`, so all five matching tests ran) gives `1 failed, 4 passed`, with the E2E
`test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` measured and **green**. That is
the closed-constraint-vocabulary invariant, and this test is its guard. **The docstring is what needs
correcting, not the test**: it should say it pins that a total mapping constructs without a false
refusal and that `requires_env` does not participate in `check()`.

### Important — the report's mutation-(c) reasoning overclaims, and "Where the brief/spec disagreed with the code: None found" is inaccurate

The report writes that the `TypeError: 'NoneType' object is not iterable` **"confirms the guard is
correctly ordered before the comprehensions."** It does not. A `TypeError` there proves only that the
comprehensions ran — i.e. that the guard is **absent**, which the mutation made true by construction.
Ordering in the unmutated code is established by reading `param.py:56–63`, not by that run.

The brief's own diagnostic rule is the thing that was wrong: *"check that the failure you see is
`DID NOT RAISE`, not a `TypeError`; if it is a `TypeError` the guard order was transcribed wrong."*
`DID NOT RAISE` is unreachable for that mutation under any correct transcription — deleting a `raise`
that guards an iteration over `None` can only crash. The implementer observed the right thing and
should have recorded it as a **brief defect**; instead the report reinterpreted it as confirmation and
then declared no brief/spec disagreements found. That declaration is what a later reader trusts.

**The underlying guard is nevertheless adequately pinned** — I ran the two mutations the brief did not,
and both are caught *by the assertion* rather than by a crash:

| Mutation | Result |
|---|---|
| Guard message `"requires_env requires choices: …"` → `"requires_env requires a closed value set: …"` | `test_requires_env_is_stored_and_needs_choices` FAILED — `Regex pattern did not match. Expected regex: 'choices'` |
| Guard `raise ValueError` → `raise TypeError` | `test_requires_env_is_stored_and_needs_choices` FAILED — `TypeError` propagated out of `pytest.raises(ValueError, …)` |

So mutation (c) is blunt, not blind. The finding is the report's claim, not the code.

### Minor — the `E-CRED-*` absence assertions cannot fail today

`grep -rn "E-CRED" src/` returns **nothing**; the two identifiers exist only as `docs/reference.md`
§ Errors rows (task 1). So `assert "E-CRED-MISSING" not in found` / `assert "E-CRED-PARAM-MISSING" not
in found` in `tests/test_validate.py` are `CLAUDE.md`'s *control asserting only absences* — they pass
identically if nothing emitted anything. They are acceptable as a forward guard for tasks 9–11 and are
paired with real positive assertions in the same test, but the report's claim that the fault is
verified "not under a credential code" is verified by nothing yet. Do not count it as evidence.

### Minor — house citation style in the new module docstring

`src/publishable/param.py`'s new paragraph cites *"§ A credential can belong to a parameter value"*
with no file, where the line above it correctly writes `docs/reference.md § Templates`. The
convention is to cite by file § section. Brief-verbatim, so a nit.

---

## What I verified, and how

### 1. The invariant — `requires_env` sits outside the closed constraint vocabulary — ✅

Read `src/publishable/param.py` end to end. `requires_env` appears **only** in the signature (line 40),
the construction-time block (56–74), and the store (83). It appears nowhere in `check()` (90–116),
`_check_list()` (118–127), `_is_type()` (129–137), or `comment()` (139–152) — confirmed by
`grep -n "requires_env" src/publishable/param.py`. Task 4's rendering is not pre-empted. Positively
guarded by the leak mutation above, which only `test_a_total_requires_env_constructs_…` catches.

The amended module docstring's *why* is checkable against the code beside it — it says `requires_env`
constrains the environment a value may be used in, not the value, and the code beside it applies the
mapping to nothing during `check()`. It matches `docs/reference.md` § A credential can belong to a
parameter value's closing paragraph clause for clause. Not merely asserted.

### 2. Totality in both directions, each pinned separately — ✅ (re-run, plus the mirror the brief omitted)

Line numbers of the three `pytest.raises` blocks in the test: **117** (missing-key), **130**
(unknown-key), **145** (both at once).

| Mutation | Observed |
|---|---|
| `if absent or extra:` → `if absent:` (brief's (b)) | **Only** the second block red: `tests/test_param.py:130: Failed: DID NOT RAISE ValueError`. The first block passed (execution reached 130). `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` stayed **green** — its fixture is missing-key only. `1 failed, 16 passed` |
| `if absent or extra:` → `if extra:` (**the mirror; not in the brief**) | **Only** the first block red: `tests/test_param.py:117: Failed: DID NOT RAISE ValueError`, and the E2E test red at `tests/test_validate.py:12266: KeyError: 'E-TEMPLATE-LOAD'`. `2 failed, 15 passed` |

Both directions go red independently. The branches are genuinely isolated — the fixtures separate them,
they are not co-satisfied.

### 3. The message assertions discriminate — ✅

The template is an invariant head plus an appended `detail`:

```
"requires_env must be total over choices: choices are {choices}; requires_env names {keys}{detail}"
detail: "; no key for {absent}"  and/or  "; keys naming no choice: {extra}"
```

- `"no key for …"` is producible **only** by the `absent` branch; `"keys naming no choice: …"` **only**
  by the `extra` branch. Neither fragment occurs in the invariant head, so neither negative assertion
  (`"naming no choice" not in text`, `"no key for" not in text`) is vacuous the way the last slice's was.
- Empirically: under `if absent:` the unknown-key fixture raises nothing at all, and under `if extra:`
  the missing-key fixture raises nothing at all — the messages cannot be produced by the wrong branch.
- The `choices are …` / `requires_env names …` fragments come from the invariant head and are
  non-discriminating between branches by design; they are the *"names both sets"* requirement
  `reference.md` states, and each fixture asserts a different literal for them.
- The third block (line 145) is the one that proves neither clause swallows the other — both fragments
  present in one message.

### 4. Mutation (c) — judgment

**The implementer's observation is right, the brief's rule is wrong, and the implementer's inference
overclaims.** See the Important finding above. The `TypeError` is unavoidable for that mutation, so
(c) as written is a test going red via a crash rather than via an assertion — weaker than claimed. I
ran two replacement mutations (message text, exception type) that are caught by
`pytest.raises(ValueError, match="choices")` itself; both go red. The guard is therefore adequately
pinned in type and in message, and the deficiency is in the report's reasoning, not in the code or
the test.

### 5. The end-to-end claim, both halves — ✅, and the control is real

Ran `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` directly: passes. The
fault lands as `E-TEMPLATE-LOAD` carrying `ValueError(` (the `{exc!r}` interpolation at
`src/publishable/templates/discovery.py:317–333`), naming `cred_assay.py`, `no key for openai, ollama`
and `choices are azure_openai, openai, ollama`. No `E-CRED-*` code is reported — trivially so, since
no such string exists in `src/` (see the Minor finding). Decision 2 holds: **no new identifier is
minted**; `grep -rn "E-CRED" src/` is empty and the diff adds no code to `errors`/`diagnostics`.

**The control is not vacuous — probed, not reasoned.** I rewrote the `.replace()` so the second write
re-emits the **same partial mapping**:

```
E   AssertionError: assert 'E-TEMPLATE-LOAD' not in {'E-TEMPLATE-LOAD'}
tests/test_validate.py:12281: AssertionError
```

The second `write_config` genuinely re-imports the file (no `sys.modules` short-circuit), and the
disappearance of `E-TEMPLATE-LOAD` in the real control is caused by the mapping becoming total, not by
caching and not by the fault being re-labelled `E-TEMPLATE-COLLISION`. Reverted; test green.

### 6. Task 2's forward reference — ✅, confirmed independently of the report

Read the two ends directly rather than taking the report's word:

- `src/publishable/validate.py:523` — the comment asserting that *"a `requires_env` mapping that is not
  total over `choices`"* is a `Param`-construction fault and the first of `E-TEMPLATE-LOAD`'s three
  shapes, *"raises while importing"*.
- `src/publishable/templates/discovery.py:317–333` — `except Exception as exc:` → `ContractError(…,
  code="E-TEMPLATE-LOAD")` with `{exc!r}`.
- `src/publishable/param.py:56–74` now raises `ValueError` on exactly that fault.

The chain closes. The comment was true of nothing at `e3ac3a4` and is true now.

### 7. Test-helper collisions and fixture files — ✅

- `_joined` — the only definition in `src/` and `tests/` (`grep -rn "_joined"`), no shadow.
- `_CRED_TOTALITY_TEMPLATE` — the only definition, matches the brief's free-name claim.
- No duplicate `def test_` names across `tests/test_param.py` and `tests/test_validate.py`
  (`grep -h "^def test_" … | sort | uniq -d` → empty).
- `templates/cred_assay.py` is written under the `git_repo` fixture (`tests/conftest.py:45`, rooted at
  `tmp_path / "repo"`), so nothing is written into the working tree. `git status --porcelain` after
  the full suite shows only the pre-existing `.superpowers/sdd/.gitignore` modification.

### (a) For every test added, the mutation that makes it fail

| Test | Single-line mutation | Verified |
|---|---|---|
| `test_requires_env_is_stored_and_needs_choices` | delete `self.requires_env = requires_env` → `AttributeError` | **run**, red |
| " (its second half) | guard message: drop the word `choices` → regex miss | **run**, red |
| " (its second half) | guard `ValueError` → `TypeError` | **run**, red |
| `test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping` | delete `self.requires_env = requires_env` (or store `requires_env or {}`) | **run**, red on the delete |
| `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets` | `if absent or extra:` → `if absent:` / → `if extra:` / delete the block | **all three run**, each red on the predicted block |
| `test_a_total_requires_env_constructs_and_leaves_every_other_check_alone` | early `return` in `check()` when `self.requires_env is not None` | **run**, red — and uniquely so |
| `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` | delete the totality block (`KeyError`); or make the control's second write partial (control assertion) | **both run**, red |

**What none of the brief's three mutations reached, now covered:** `self.requires_env` being *stored*
is pinned — deleting the assignment fails two tests with `AttributeError` (blunt, but it cannot pass).
The report's Step 7 said this was pinned "not by a dedicated mutation here"; it is now run and holds.
The `requires_env`-must-not-enter-`check()` half of the invariant is pinned by the leak mutation, which
no mutation in the brief or report reached. `_joined`'s output order remains unpinned — I agree with
the report that this is correct to leave: the order belongs to `choices`, and a fixture separating them
would pin `list` iteration order rather than behaviour.

### (b) Sentences added, checked one by one

- **Module docstring amendment** (`param.py:5–9`) — accurate; the code beside it applies `requires_env`
  to no value. Minor citation-style nit only.
- **Guard message** *"a credential requirement is only checkable over a closed set of values"* —
  matches `reference.md`'s stated reason verbatim in substance.
- **Totality message** — every clause it emits is emitted only under the condition it names.
- **`test_requires_env_is_stored_and_needs_choices` docstring** — accurate.
- **`test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping` docstring** — the
  `None` vs `{}` distinction is real (`self.requires_env = requires_env`, no coercion); the
  "tasks 10 and 11 gate on truthiness" clause is a forward claim about unbuilt code, acceptable as
  motivation but unverifiable today.
- **`test_requires_env_must_be_total_over_choices_…` docstring** — accurate, and the "separately
  pinnable" claim is now empirically true in both directions.
- **`test_a_total_requires_env_constructs_…` docstring** — **false**; see the Important finding.
- **`test_a_requires_env_totality_fault_surfaces_…` docstring** — accurate, including the `{exc!r}`
  claim, verified at `discovery.py:317–333`.
- **`# THE CONTROL, and it is what makes the assertion above about the totality check rather than
  about local discovery`** — a strong claim, and it survives the probe. Correct.
- **Report §"Where the brief/spec disagreed with the code: None found"** — **inaccurate**; see the
  Important finding.

---

## Required before this is done

1. Rewrite `test_a_total_requires_env_constructs_and_leaves_every_other_check_alone`'s docstring to
   state what the test actually pins — a total mapping constructs without a false refusal, and
   `requires_env` does not reach `check()` — and drop the "passes every refusal test above" claim.
2. Amend `task-3-report.md`: record the brief's mutation-(c) diagnostic rule as a **brief defect**
   (`DID NOT RAISE` is unreachable there), replace "confirms the guard is correctly ordered" with the
   two message/type mutations that do pin it, and correct "None found" in
   §*Where the brief/spec disagreed with the code*.

Neither changes any shipped behaviour, so the H7b prerequisite itself is sound: the constructor
argument, its two refusals, its message, its storage and its `E-TEMPLATE-LOAD` route are all correct
and all pinned by a mutation I ran.

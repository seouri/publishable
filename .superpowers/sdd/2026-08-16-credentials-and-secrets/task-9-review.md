# Task 9 review: `required_env` checked at `validate`

Reviewed `931f2dd..36a7778` on branch `h7c-credentials`.

## Gates, re-run rather than trusted

| Command | Result |
|---|---|
| `uv run pytest` | 1977 passed, 2 xfailed — matches the brief's expectation |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 76 files already formatted |
| `uv run mypy` | Success, 43 source files |

Working tree left clean (`git status --porcelain` shows only the pre-existing
`.superpowers/sdd/.gitignore` clobber, which `scripts/task-brief` re-created when this review's
brief was extracted). Every mutation below was reverted by restoring a byte copy taken before the
edit, never by `git checkout --` on a source file; `__pycache__` deleted before each re-run; each
revert verified by re-running the targeted tests, and finally the full suite.

---

## The eight checks the brief asked for

### 1. The `CLAUDE.md` example replacement — ✅ verified independently

`grep -rn "field_convention" src/ tests/ docs/ README.md CLAUDE.md` (quoted patterns; the
implementer's `--include` form would have silently no-matched under zsh). In `src/` the only hits
are the two declarations (`templates/base.py:13`, `templates/builtin/generic.py:7`) and the
`generators/template.py:9` comment. **No reader.**

Two hits the implementer's `src/`-only grep did not see, and neither is a reader:

- `tests/test_templates.py:18` — `assert t.field_convention == "generic"`, an assertion on the
  declared default. This is the same shape as `assert t.required_env == []`, which coexisted with
  the row while it named `required_env`, so the precedent holds and the standard is applied
  consistently.
- `tests/test_cli.py:668` — asserts the `generate template` stub does *not* emit the name.

**The row's count phrase checks out.** "The other two" requires that the unread set really is
`{field_convention, apparatus_probe, apparatus_facts}`: `naming_pattern` is read at
`validate.py:702`, `default_repeats` at `validate.py:3385`, `parameter_spec`/`validate`/`aggregate`
throughout. So the row's arithmetic is right.

**The ownership claim is sourced, contrary to my first reading of the design doc.** The design
(`…-credentials-and-secrets-design.md` § What the charter got wrong) says only "H7b takes
`apparatus_probe`, so pick from the other two" — it does not name H7d. But
`docs/superpowers/H7c-SCOPING.md:502` does, explicitly: *"`Apparatus`, probe execution,
`apparatus_probe`/`apparatus_facts` — the two remaining unread `BaseTemplate` members after task 9 |
**H7d** (and H7b task 13 for `apparatus_probe`'s registration answer)"*, and `:503` records
`field_convention` as *"Unowned. Worth a `spec-defects.md` line in task 14"* — which plan task 14
step 4 does file. So the parenthetical is not a "ledger line saying filed is not a filing": it has a
scoping behind it and a filing scheduled. Verified rather than assumed.

**The surrounding rule was not weakened.** The row's normative first half — unbuilt reader of an
unbuilt surface is specification, of a shipped surface is a defect — is byte-identical; only the
example moved, and the parenthetical adds provenance rather than hedging. The `apparatus_*` members
were correctly avoided.

### 2. The position claim — ✅ verified, by re-running the mutation that makes it true

Moved `load_env(repo_root)` from before `resolve_template` to immediately after the
`_check_required_env(doc, template, c)` call. `test_a_required_env_variable_may_be_supplied_by_dot_env`
went red: `AssertionError: assert {'E-CRED-MISSING'} == set()`. Reverted from a byte copy;
`__pycache__` cleared; the five `.env`/`required_env` tests re-run green. The reworded comment's
pinned half is therefore genuinely pinned, not merely weaker.

I also checked the comment's other clause — *"before the first check that reads the environment"* —
against the code rather than the report: `grep -n "os.environ\|getenv\|environ" src/publishable/validate.py`
returns only the two lines this task added plus the message text. No core check between `load_env`
and `_check_required_env` reads the environment. That half is true. See finding **I1** for the
clause that is not.

### 3. `E-CRED-MISSING`'s § Errors row versus the emit site — ✅ every clause honoured

`docs/reference.md:470`, read against `validate.py:738-753`:

| Row clause | Emit site |
|---|---|
| "checked from the class alone, before any condition is expanded" | `getattr(template, "required_env")`; called before `_check_parameters` and long before `expand` |
| "reported at `experiment_type`" | Literal `"experiment_type"`; asserted by `{f.path for f in found} == {"experiment_type"}` |
| "one finding per unset variable" | One `c.error` per `missing_env` element; `assert len(found) == 2` |
| "in the order the list declares them" | `secrets.missing_env` appends in iteration order — see below |
| "Core loads `.env` … before this check runs and never overrides" | Pinned by the mutation in check 2 |
| "The **value** is never printed" | See check 4 |
| "Distinct from `E-CRED-PARAM-MISSING` in what it can name" | `assert "template \`cred_assay\`" in …` and `assert "condition" not in …` |

**The order guarantee's fixture can see it — the hole task 7 nearly shipped is closed here.**
Declared order is `[PUBLISHABLE_TEST_TOKEN, PUBLISHABLE_TEST_OTHER]`; sorted order is
`[OTHER, TOKEN]`. The two differ, so `found[0]`/`found[1]` distinguish them. I proved it rather than
reasoning it: wrapping the loop in `reversed(...)` — which for this two-element fixture *is* sorted
order — turned `test_an_unset_required_env_variable_is_reported_with_its_name` red on
`assert "\`PUBLISHABLE_TEST_TOKEN\`" in found[0].message`. Reverted and re-run green. (Worth
recording that the ordering behaviour lives in `secrets.missing_env`, one module away from the test
that pins it here.)

### 4. The value is never printed — ✅ true, and **structurally so**, which is the honest form

Probed directly with a temporary test (a template declaring `["PUBLISHABLE_TEST_SET",
"PUBLISHABLE_TEST_UNSET"]`, `setenv` the first to `sk-distinctive-abc123`, `delenv` the second),
asserting against `Collector.render()` — the formatted output, not just `f.message`. One finding,
naming only the unset variable; the distinctive value appears nowhere:

```
  error   E-CRED-MISSING       experiment_type
          template `leak_assay` requires `PUBLISHABLE_TEST_UNSET`, which has no value in the
          environment or in `.env` — the config records the NAME, so put the value in `.env` at
          the repository root
```

The temporary test was removed and `tests/test_validate.py` confirmed byte-identical to the commit.

**But this property cannot fail at this emit site**, and that is worth stating rather than crediting
to task 9: `_check_required_env` never obtains a value at all — `missing_env` returns names and
discards values, and the emit site closes over `variable` and `name` only. The check is safe by
construction, not by a filter. The slice's actual leak property — a value that core *did* read
reaching a record — is task 12's, and that is where a mutation can bite.

### 5. Environment-test hygiene — ✅

- The autouse `_restore_environ` in `tests/conftest.py` is untouched by this commit (it landed at
  `4c79417`, task 7's review). **No second fixture was added** — the diff adds only a module-level
  string constant and four `def test_…` functions.
- `monkeypatch` is used in **both** directions: `delenv` in tests 1, 3 and 4;
  `setenv` in test 2.
- The negative test (1) has its control: test 2 sets both variables and expects silence, and I
  confirmed by mutation that the control is the *only* thing that can catch an unconditional
  reporter (see (a) below).

One weak shape, deliberate and named by the brief: `test_a_template_declaring_no_required_env_reports_nothing`
asserts only an absence and has no control of its own — it would pass on a build with no check. Its
value is documentary (it states why the pre-existing suite stays green), and tests 1–2 carry the
real load, so this is acceptable rather than a defect.

### 6. The forward reference in the docstring — reads as present-tense, not forward-looking

*"…and that case is `_check_requires_env`'s"* is accurate (task 10 builds it) but carries no
build-state marker, so it is indistinguishable from a stale reference to something deleted. Minor;
see **m2** for the reasoning and the one-word repair.

### 7. The edit accident — ✅ verified, the diff is purely additive

`git diff 931f2dd..36a7778 -- tests/test_validate.py | grep '^-'` returns exactly one line, the
`--- a/tests/test_validate.py` header. No deletion, no relocation. The displaced
`assert os.environ.get("PUBLISHABLE_TEST_TOKEN") is None` sits in its original test in the shipped
tree, as the diff's context lines show.

### (a) Which mutation reaches which test

| Test | The single-line mutation that fails it |
|---|---|
| `test_an_unset_required_env_variable_is_reported_with_its_name` | Delete/`pass` the `c.error` call (run by implementer, red); `reversed(missing_env(...))` (**run by me**, red); `"experiment_type"` → `"parameters"` (**run by me**, red on the `{f.path}` assertion) |
| `test_a_satisfied_required_env_validates_clean` | `missing_env(...)` → `(str(n) for n in names)` (run by implementer, red) — the only one that proves the check reads the environment |
| `test_a_required_env_variable_may_be_supplied_by_dot_env` | Move `load_env` past `_check_required_env` (**run by me**, red) |
| `test_a_template_declaring_no_required_env_reports_nothing` | None that the other three do not already reach |

**What the implementer's two mutations do not reach**, and I ran the two that matter: the **declared
order** of the findings, and the **`experiment_type` path literal**. Both are load-bearing § Errors
clauses and both are now confirmed observable. Still unreached by any mutation, and correctly named
in the report: the `isinstance(names, list)` guard, and `_check_required_env`'s position in
`validate_config`'s call order relative to the other checks.

---

## Findings

### Important

**I1 — The comment's safety clause over-claims: `resolve_template` executes arbitrary user
top-level code, so it *can* read an environment variable.** (`src/publishable/validate.py:511-516`)

The new comment justifies the weaker pinned position with:

> That is weaker than "before `resolve_template`": nothing here depends on the stronger position,
> since **`resolve_template` reads no environment variable**, and no test distinguishes the two
> placements.

`resolve_template` performs project-local discovery — it **imports every `templates/*.py` in the
repository**, and a user module's top level is arbitrary Python that may read `os.environ`. That is
not hypothetical for this slice specifically: a template whose module scope reads a credential name
is exactly the case where `.env` must already be loaded. The clause is a claim about a function's
behaviour that is falsified by what the function executes, and it is the *entire* argument that the
stronger position is unnecessary.

The code is currently correct — `load_env` **is** before `resolve_template`. The harm is that the
comment invites a future reader to move it, and CLAUDE.md's rule is explicit: *"A safety argument in
a comment is a claim, and needs a mutation like any other… If a comment says this cannot happen,
make it happen."* Verified by reading `resolve_template`'s discovery path and by CLAUDE.md
§ Answering a question with a proxy, which documents that H7a's local-template discovery imports
user files.

*Suggested repair:* say what is true — that **core's own** `resolve_template` reads no environment
variable, while the `templates/*.py` it imports may, which is why the load stays ahead of it even
though no test yet distinguishes the two placements. One clause, and it turns a false justification
into the real reason the code is where it is.

### Minor

**m1 — Note, out of this review's scope:** `tests/__pycache__/*.pyc` is tracked on this branch —
begun at `4c79417`, 31 files added at `931f2dd`, despite root `.gitignore:2` — and task 9's commit
updates one such blob. Pre-existing, **not task 9's**; recorded only so it is not read as new.

**m2 — `_check_required_env`'s docstring forward-references `_check_requires_env` in the present
tense, with no build-state marker.** (`src/publishable/validate.py`, docstring: *"…and that case is
`_check_requires_env`'s."*) Task 10 builds it; the design's § Task decomposition item 10 confirms
that, so the reference is accurate. But this repo's own distinction is carried by **tense and
marker**: a documented-but-unbuilt surface is specification *when it is marked* (§ Package layout's
`— not yet built`), and an unmarked present-tense sentence about an absent function is
indistinguishable from a stale reference to something deleted. A reader who greps
`_check_requires_env` today finds nothing and cannot tell which. One word fixes it — *"that case
will be `_check_requires_env`'s (task 10)"* or a `— not yet built` marker. Text carried verbatim
from the brief, so the brief is where it originated; the implementer flagged it and judged it fine,
and I agree it is accurate but disagree that it is adequately marked.

**m3 — Two claims elsewhere in the tree were falsified by this commit; both are task 13's, and one
is in a normative document.** Not task 9's to fix, recorded so the hand-off is explicit:

- `src/publishable/generators/template.py:9` — *"`field_convention`, `required_env`,
  `apparatus_probe` and `apparatus_facts` are declared on the base class and **read by nothing in
  this build**"*. False as of this commit. Plan task 13 Step 2 names this file explicitly and says
  to re-read it, so it is covered.
- `docs/reference.md:3279` — *"`BaseTemplate.required_env` is declarable but **read nowhere in
  `src/`**"*. False as of this commit, in one of the four normative documents. **This is the
  hand-off risk:** task 13's expected-disposition table entry for that site (§ The generated README
  — the `credentials` region) says only *"Do not build it. Task 14 files it,"* which is about the
  managed region, not this clause — a reader working the table rather than Step 1's "read **every**
  hit" instruction could pass right over it. Flagging so task 13 does not.

---

## Verdicts

1. **Spec compliance — ✅.** Every clause of `E-CRED-MISSING`'s § Errors row is honoured by the emit
   site, verified clause by clause and, for the three that a mutation can reach (order, path,
   `.env`-before-check), verified by running the mutation.
2. **Task quality — ❌**, on **I1** alone. Everything else is clean: gates green, diff purely
   additive, no second environment fixture, both `monkeypatch` directions used, the control present
   and proved necessary, the survivor grep re-verified beyond the implementer's `src/`-only scope
   with the count phrase and the ownership claim both sourced, and two mutations run that the
   implementer's set did not reach. **I1** is one clause and a one-line repair, but it is a safety
   argument newly written by this task that the function's own documented behaviour falsifies, and
   it is the sole justification a future reader would act on when deciding where `load_env` may sit.

# H7c — credentials and secrets — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** a template declares the environment variables it needs, `validate` reports a missing one
before anything executes, and a credential value never reaches a record. `Param(requires_env=)`
becomes constructible and renders into the `choices` comment, `BaseTemplate.required_env` gets its
first reader, `secrets.py` loads `.env` at two sites, and a failing step's exception text is
redacted by exact value at the point it is built.

**Architecture:** `param.py` gains one keyword-only argument, `requires_env`, which requires
`choices` and must be total over them in both directions — enforced in `Param.__init__` as a
`ValueError`, the shipped route `default=None`-without-`nullable` already takes, which surfaces to a
user as `E-TEMPLATE-LOAD` with the `ValueError`'s `repr` interpolated by
`templates/discovery.py`. `Param.comment()` renders each choice's requirement against *every*
choice. A new `src/publishable/secrets.py` wraps `python-dotenv`: `load_env(repo_root)` is
idempotent and never overrides an exported variable, `missing_env(names)` answers which declared
names have no value, `credential_values(names)` returns the values core read, and
`redact(text, values)` replaces each of those values by exact match with a marker naming its
variable. `validate_config` calls `load_env` once, right after it resolves `repo_root`, and gains
two collectors: `_check_required_env` (template-level, `E-CRED-MISSING`) and `_check_requires_env`
(the union over the conditions `expand` resolves, `E-CRED-PARAM-MISSING`). `cli.command_run` calls
`load_env` again — loading is a precondition of executing, not a side effect of checking — and
collects the values behind those same two declarations. Those values then reach the **two
serialization boundaries** at which core turns an exception into text a reader sees:
`runner.execute_plan`, which builds a failed execution's `error` string for `executions.jsonl` and
`run.yaml`, and `Collector.render()`, the one method every diagnostic passes through on its way to
stdout or stderr — which covers the four *other* places core interpolates a template's or a user
package's exception. Two boundaries rather than five construction sites, so a sixth construction
inherits the redaction instead of forgetting it.

**Spec:** docs/superpowers/specs/2026-08-16-credentials-and-secrets-design.md

**Task count: 14**, exactly the spec's decomposition and the scoping's § 8, in its order and its
grain. No task was split, merged, or moved.

**Sequencing.** Task 1 before everything: it mints the two identifiers every later message uses.
**Task 3 is H7b's prerequisite** — `H7b-SCOPING.md`'s task 27 and any H7b Part B test that imports
the feasibility analysis's `llm_screen` plugin cannot run until `Param.__init__` accepts
`requires_env`, and **nothing else in this slice gates task 3**. If this combined run is
interrupted, task 3 is the task that must have landed. The seam if H7c itself runs long is **6/7**:
tasks 1–6 change no behaviour beyond `Param`'s constructor and its rendered comment, need no new
dependency, and already contain task 3. Tasks 7–11 read the environment; 12–14 prove it, sweep the
owned prose, and file.

---

## Global Constraints

Every task inherits all of these. They are copied verbatim rather than cross-referenced because an
implementer sees only its own task brief.

**Commands.** Tests `uv run pytest`. Lint `uv run ruff check .`. Format `uv run ruff format .`.
Types `uv run mypy`. All four must pass before a commit.

**Verify format with `uv run ruff format --check .`, never the bare form.** A previous brief in
this repo wrote `uv run ruff format .` where it meant `--check` and rewrote 67 files. **Measured at
`478c1f3`, before this slice starts: `74 files already formatted, 0 to reformat`.** The repo is
format-clean and a task that leaves new drift is incomplete. `pyproject.toml`'s
`[tool.ruff.format] exclude = ["*.md"]` now fences the four documents' fenced Python, so the
historical 67-file blowup is partly contained — do not carry that number forward as if it were
current.

**Baseline.** `uv run pytest -q` at `478c1f3` (HEAD when this plan was written, a docs-only commit
above the scoping's pin `d86290c`) is **1957 passed, 2 xfailed**, 116 s. Re-measured for this plan
rather than carried from the scoping. A task that leaves the count below its own additions has
broken something.

**Identifiers this slice mints.** Two, both new: `grep -rn "E-CRED" src docs README.md` returns
nothing at `478c1f3` — run it once before task 1 to confirm the family is still free.

| Code | Fault | Minted in task |
|---|---|---|
| `E-CRED-MISSING` | A variable in the resolved template's `required_env` has no value in the environment or in `.env` | 1 (row), 9 (check) |
| `E-CRED-PARAM-MISSING` | A variable a resolved condition's parameter *value* requires through `Param(requires_env=)` has no value | 1 (row), 10 (check) |

**This slice mints no `-UNSUPPORTED` code and retires none.** There is no refusal in this family to
retire: the three § Validation rows have existed since H1 with nothing behind them. A narrow refusal
of a combination is documented and carries rows; this family has only missing checks. Do not read
the `-UNSUPPORTED` family in on the way past.

**The `requires_env` totality check mints nothing.** It is a `ValueError` from `Param.__init__`,
which surfaces as `E-TEMPLATE-LOAD` — the first of that code's three enumerated shapes, "raises
while importing" — and `reference.md` § Errors `validate` reports already enumerates it. No new code
and **no new § Errors row is owed**. Do not mint a third identifier.

**Every new error site is pinned by its MESSAGE, not only its code.** Use the `fragment` +
`messages_by_code(path)[code]` pattern already in `tests/test_validate.py` (both helpers are defined
at the top of that file: `codes(path)` returns the set of every finding's code,
`messages_by_code(path)` returns `{code: message}`). Where two branches emit one code, their
messages must be *distinguishable* and each pinned separately. **A message assertion is not
automatically a discriminating one** — one in the last slice was vacuous because the message's
invariant tail contained the asserted fragment either way. Assert a fragment only one branch can
produce, and before believing any test, name the single-line mutation that makes it fail.

**`os.environ` is inherited from the test runner.** A test asserting "the variable is unset, so
`validate` reports" passes on a machine where nothing was ever set — **and would pass if the check
did not exist** — while the positive test fails mysteriously on a developer machine that happens to
have it. **Every environment test uses `monkeypatch.setenv` / `monkeypatch.delenv`**, and every
negative test needs a control that sets the variable and expects silence.

**`load_dotenv` writes straight into `os.environ` and nothing cleans it up.** A test that causes a
`.env` to load leaks its variables into every test that runs after it. **Before triggering any load,
call `monkeypatch.delenv(NAME, raising=False)` for every name the `.env` holds**: `monkeypatch`
records the pre-state and, since the name was absent, deletes it again at teardown. This is not
optional and it is not covered by the rule above — `setenv` alone does not protect against a name
the file introduces.

**The two `.env` load sites are in different modules.** `publishable.validate` and
`publishable.cli` each call `load_env`, so a `monkeypatch` aimed at one while asserting the other's
behaviour is not obviously wrong on inspection. **Every task that patches a load site names its
target as a full module attribute path** — `publishable.validate.load_env` or
`publishable.cli.load_env` — in the task text and in the test's own comment.

**Mutation discipline, every task.** Apply the named mutation to the file it names. Run the named
test. Confirm it **FAILS**. Then `find . -name __pycache__ -type d -exec rm -rf {} +`. Then revert
**by editing the file back in place** — **never `git checkout -- <file>`**, which destroys
uncommitted work and has been mistaken for a revert twice in this repo. Confirm the test **PASSES**
again, and verify the revert by *behaviour*, never by `git status`.

**A mutation is a claim too.** Before writing or believing "this mutation must fail test X", read
the *body* of test X and check the two branches can actually produce different results. A plan in
this repo once claimed a `constant.update` reordering would fail a named test whose fixture built
its dict by hand and never called the function at all. Where this plan concludes a mutation cannot
discriminate, it says so and prescribes a different one; do the same for any mutation you add.

**Test-design rules this repo enforces.**

- A control that asserts only an absence passes identically if nothing ran. Every such assertion
  needs a positive companion **produced by the code under test**, in the same test.
- Size a fixture so each candidate wrong answer produces a **different** observable. **Two elements
  only ever distinguish two answers** — decision 6 is a fixture sized by counting the readings first.
- **Never filter the output of a sweep whose job is to find a string — filter the file list.** A
  reviewer checking this exact rule lost a true hit to `grep -v superpowers`.
- **Test the honouring, not only the refusal.** This slice's charter is three-quarters refusals. A
  correctly declared `requires_env` over a satisfied environment must validate **clean**, and the
  union must be computed over the right condition set — without that, ignoring `requires_env`
  entirely passes the suite.
- **Read a target test file's existing module-level names before naming a helper.** A brief in this
  repo prescribed `_roster(n, **attrs)` that would have shadowed an existing `_roster(n)` used by a
  dozen tests. The names already taken in the files this slice touches are listed in each task.

**Documentation rules.** `×` not `x` for multiplication, including inside fenced blocks. Hyphen,
never an en dash, in anything that becomes a filename or an anchor. **Cite by section**
(`reference.md` § "Secrets & credentials"), never by line number, in any prose a task writes.
**Do not locate anything by position** — "three lines below" was wrong by twelve here, and locating
a table row by position has been wrong twice. Name what a sibling row *does*. **Do not enumerate
call sites in a docstring** — two in this repo went stale that way and one is an open
`spec-defects.md` gap. After any `*.md` edit run the mechanical pass: every relative link and
`#anchor` resolves, no two headings in a file share an anchor, every table row matches its header's
column count and none is empty, no trailing whitespace, tab, or invisible unicode — skipping fenced
code blocks in all of them. Any inline `# a | b | c` enum comment must list every value its table
defines.

**The four normative documents LEAD; `src/` follows.** `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`. Where they and the code disagree, **the
document changes first** and the gap is recorded in `docs/superpowers/spec-defects.md`. The
cross-document pass governs those four **only** — never the development record under
`docs/superpowers/`, where a correction is appended rather than retro-edited. `spec-defects.md` is
the one exception: a closed gap is struck there rather than left to mislead.

**`reference.md` § Errors `validate` reports carries one row per code covering every emit site**,
not one row per site. `E-TEMPLATE-UNKNOWN` cost a slice a round by being scoped to one of its two
emit sites.

**This slice exports nothing.** `requires_env` is a `Param` keyword and `required_env` a class
attribute, so `reference.md` § The importable surface's enumerated list does not move. Task 6 says
so in the document; no task adds a name to `publishable/__init__.py`.

**Two shared edits with H7b — assigned here, once.** H7b task 2 also touches § Errors' early-return
ordering prose and `validate.py`'s "two today" comment: **H7c task 2 owns both.** H7b task 4 splits
the § The importable surface `register_*` row while **H7c task 6** owns the "exports nothing"
statement in that same section. Do not do either twice.

---

## Task 1: The two identifiers — § Validation ↔ § Errors, with decision 1's grounds

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: nothing.
- Produces: the § Errors `validate` reports rows for `E-CRED-MISSING` and `E-CRED-PARAM-MISSING`,
  which tasks 9 and 10 emit and pin, and the sentence that records `E-TEMPLATE-LOAD` as the
  `requires_env` totality check's identifier.

**Why two codes and not one.** Decision 1 of the spec, settled: they are one mechanism with two
collectors, but a § Errors row carries *one message*, and these two messages cannot be shared. One
names a template; the other must name a parameter, a value, and the condition that selected it. The
`E-TEMPLATE-UNKNOWN` precedent — two emit surfaces under one row — turns on those two surfaces
sharing a message, which is exactly what fails here. One row enumerating both is the shape the
one-row-per-code rule exists to avoid. Write that argument into the rows rather than leaving the
next reader to re-derive it.

**Where the identifiers go.** § Validation's table is two columns, `Check | Example failure`, and
**no row in it names a code** — verified by grepping the table's own row range for
`errors-validate-reports` and finding zero hits. So the identifiers are minted in § Errors `validate`
reports (`| Reported when | Code |`) and nowhere else, and the `requires_env`-totality statement
goes into the **prose** of § A credential can belong to a parameter value, in the sentence that
already reads "`validate` rejects a mapping with a missing or unknown key when the template loads,
naming both sets." **Task 5 is told not to touch that sentence**; it is this task's.

- [ ] **Step 1: Read before writing.** Read § Validation's three credential rows (*Credentials
      present*, *Credentials a swept value needs*, *`requires_env` covers its choices*) and confirm
      each still reads as measured — none carries a code today. Read § Errors `validate` reports'
      table header and the rows immediately around where the new ones will sit. Confirm
      `grep -rn "E-CRED" src docs README.md` is empty.

- [ ] **Step 2: Add two rows to § Errors `validate` reports.** Place them adjacent to each other.
      Locate the insertion point by naming the row you put them after — do **not** describe it by
      position — and after inserting, re-check every count phrase near them and every row the
      insertion moved.

```
| The resolved template declares a [`required_env`](#secrets--credentials) variable that has no value in the environment or in `.env`. A template-level list says what an experiment *type* always needs, so this is checked from the class alone, before any condition is expanded, and reported at `experiment_type` — the field that decided which template's list applies. One finding per unset variable, in the order the list declares them, so a template needing three keys names all three rather than one at a time. Core loads `.env` from the repository root before this check runs and never overrides a variable already exported, so a value set in the shell satisfies it. The **value** is never printed: the message names the variable and says where to put a value, which is the whole of what a reader needs and the whole of what is safe to say. Distinct from the row below in what it can name — that one has a parameter, a value, and a condition, and this one has only the template | `E-CRED-MISSING` |
| A parameter *value* the sweep actually resolves declares a credential through [`requires_env`](#a-credential-can-belong-to-a-parameter-value) that has no value in the environment or in `.env`. Checked as the **union over the conditions [`expand`](#expansion-modes) resolves**, which is the entire reason a value-level requirement exists rather than a template-level list: a config that selects Azure and OpenAI is silent about Ollama's key, and one that selects none of them is silent about all three. Reported at the parameter's own dotted path, and the message names the parameter, the value, and the condition that selected it — the three facts a reader needs to decide whether to supply the key or drop the condition, and the reason this is a second code rather than a second emit site of the row above, whose message can name none of them. A variable required by two conditions is reported once, attributed to the first that selected it, since one missing value is one thing to fix. A value with no key in the mapping requires nothing: `requires_env` is total over `choices`, and [`sweep.ablate.remove`](#expansion-modes) resolves a nullable parameter to `null`, which is not a choice | `E-CRED-PARAM-MISSING` |
```

- [ ] **Step 3: Record that the totality check mints nothing.** In § A credential can belong to a
      parameter value, extend the existing sentence so it reads:

```
`validate` rejects a mapping with a missing or unknown key when the template loads, naming both sets — as [`E-TEMPLATE-LOAD`](#errors-validate-reports), which is that code's "raises while importing" shape and mints no identifier of its own, exactly as a `Param` declaring `default=None` without `nullable=True` already does.
```

- [ ] **Step 4: Mechanical pass.** Every relative link and `#anchor` in the edited region resolves
      (`#secrets--credentials`, `#a-credential-can-belong-to-a-parameter-value`,
      `#errors-validate-reports`, `#expansion-modes` — check each against a heading that exists), no
      duplicate anchors, every new row has exactly two cells, no trailing whitespace, no tab, no
      invisible unicode, no en dash where a hyphen belongs. Skip fenced code blocks.

- [ ] **Step 5: Cross-document pass.** The four documents only. Nothing here changes the worked
      example, a config field, an enum comment, or a version. Confirm by grepping the other three
      documents for `E-CRED` (must be empty — these codes are named in `reference.md` alone at this
      commit) and for `requires_env` (`design-principles.md` and `experimental-designs.md` each hold
      one mention, neither of which names a code; leave both alone — they are task 13's).

- [ ] **Step 6: Mutation.** This task is document-only and **no mutation reaches it**, which is
      stated rather than papered over. There is no code to mutate and no test to redden: at this
      commit both codes are strings in a table. **Task 9 closes `E-CRED-MISSING` and task 10 closes
      `E-CRED-PARAM-MISSING`** — each pins its row's message by fragment, and a wrong code in a row
      is caught there. The verification available *here* is the mechanical pass plus a re-read: the
      two rows must state conditions no other row in the table states.

- [ ] **Step 7: Commit.** `docs: mint E-CRED-MISSING and E-CRED-PARAM-MISSING, with decision 1's grounds`

---

## Task 2: § Errors' load-refusal prose and its count phrase

**Files:** Modify `docs/reference.md`, `src/publishable/validate.py`. No test change.

**Interfaces:**
- Consumes: `reference.md` § Errors `validate` reports' early-return paragraph, which begins "Five
  faults return `validate_config` early, in this order"; `validate.py`'s comment inside
  `validate_config`'s `except ContractError` guard, which reads "The load-time refusals resolving a
  template can make — two today, `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION`."
- Produces: both phrases correct once a `Param` construction fault is a reachable
  `E-TEMPLATE-LOAD` shape. **Neither number changes.**

**The finding this task exists to record, and it is a negative one.** The scoping probed a `Param`
fault end to end against a real scaffolded project: a `templates/badnull.py` declaring
`Param(str, default=None)` produced

```
error   E-TEMPLATE-LOAD      experiment_type
        the project-local template `…/templates/badnull.py` raised while importing and
        registers nothing usable: ValueError('default=None requires nullable=True')
```

collapsing a three-error report to one. `requires_env`'s three faults take that identical route. So
**"Five faults" stays five and "two today" stays two**: both phrases count *codes*, and this slice
adds a *shape* to a code that already enumerates "raises while importing" as one of three. The edit
is to make that distinction explicit so the next reader does not increment a number that should not
move.

- [ ] **Step 1: Read both sites and confirm the counts.** In `validate.py`, read the `except
      ContractError` guard inside `validate_config` and confirm exactly two codes can arrive there:
      `resolve_template` is the only call inside the `try`, and `E-TEMPLATE-LOAD` /
      `E-TEMPLATE-COLLISION` are the only codes `templates/discovery.py` and
      `templates/registry.py` raise from it. In `reference.md`, read the early-return paragraph and
      count its enumerated faults: `E-CONFIG-PARSE`, container-shaped `E-CONFIG-SHAPE`,
      `E-TEMPLATE-LOAD`, `E-TEMPLATE-COLLISION`, `E-TEMPLATE-UNKNOWN` — five.

- [ ] **Step 2: Amend `validate.py`'s comment.** Replace the phrase "two today" so it counts what it
      means:

```python
        # The load-time refusals resolving a template can make — two codes,
        # `E-TEMPLATE-LOAD` and `E-TEMPLATE-COLLISION`. Two *codes*, not two
        # faults: `E-TEMPLATE-LOAD` covers three shapes of its own (see its
        # § Errors row), and a `Param` whose construction raises — `default=None`
        # without `nullable=True`, or a `requires_env` mapping that is not total
        # over `choices` — is the first of them, "raises while importing". Adding
        # such a fault adds no code and does not move this count. Reported under
        # the code the raise carries rather than a code chosen here, so the two
        # surfaces stay one fault, and reported at all because `validate` is
        # contracted never to raise. Nothing later can run: which template a name
        # means is exactly what either leaves unanswered.
```

- [ ] **Step 3: Amend `reference.md`'s early-return paragraph.** Keep "Five faults" and add one
      sentence immediately after the enumeration of the five, before the paragraph's existing "Each
      returns because…" clause:

```
That is five *codes*. `E-TEMPLATE-LOAD` covers three shapes — a file that raises while importing, one that imports cleanly and registers nothing, one that registers a non-`BaseTemplate` — and a `Param` whose construction raises is the first of them, so a bad `default=None` or a [`requires_env`](#a-credential-can-belong-to-a-parameter-value) mapping that is not total over `choices` adds a fault to this list without adding a row to the table below or a sixth to this count.
```

- [ ] **Step 4: Run the mechanical pass** over the edited paragraph, and confirm the four other
      places `E-TEMPLATE-LOAD`'s three shapes are enumerated (two § Errors tables' rows,
      § Templates' "Every non-dunder-stemmed file under `templates/` is a template" paragraph, and
      `templates/discovery.py`'s `discover_local` docstring) still read correctly — **grep for
      `E-TEMPLATE-LOAD` across `docs/reference.md` and `src/publishable/` and read each hit**, since
      an enumerating row owes a prose edit when a case is added and this task's finding is that none
      is owed. Record in the commit message that all four were re-read and none needed changing.

- [ ] **Step 5: Verify.** `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`,
      `uv run mypy`. A comment change alone must leave 1957 passed, 2 xfailed.

- [ ] **Step 6: Mutation — and this task has none that can fail.** Stated explicitly, per the rule
      that a task must name the deliverables no mutation reaches: **both count phrases are
      unpinnable.** Nothing in the suite reads `validate.py`'s comment text or `reference.md`'s
      "Five faults" sentence, so changing "two" to "three" or "Five" to "Six" leaves all 1957 tests
      green. Do **not** invent a test that greps the document for a number — that would pin a count
      phrase to a literal and make every future insertion a two-file edit, which is the
      maintenance-obligation failure `CLAUDE.md` names under "Rewriting a sentence when a table row
      was the thing that was wrong." The verification here is the re-read in step 1: enumerate the
      codes that can reach `validate_config`'s `except` clause from the source, and the enumerated
      faults in the paragraph, and confirm both match what the prose says. **No later task closes
      this**; it is accepted as a document-only claim verified by reading.

- [ ] **Step 7: Commit.** `docs: the load-refusal count phrases count codes, not fault shapes`

---

## Task 3: `Param(requires_env=)` — the constructor argument · **the H7b prerequisite**

**Files:** Modify `src/publishable/param.py`, `tests/test_param.py`.

**Interfaces:**
- Consumes: `Param.__init__(self, type_: type, *, default: Any = MISSING, choices: list[Any] | None
  = None, ge, gt, le, lt, pattern, item_type, min_items, max_items, nullable: bool = False,
  help: str | None = None) -> None` — twelve keyword-only arguments today, at
  `src/publishable/param.py`, read from that file.
- Produces: a thirteenth, `requires_env: dict[Any, list[str]] | None = None`, stored as
  `self.requires_env`; a `ValueError` naming both sets when it is not total over `choices`; a
  `ValueError` when `choices` is absent. **Task 4 consumes `self.requires_env`; tasks 10 and 11
  consume it through `template.parameter_spec`.**

**Why this is the prerequisite.** The feasibility analysis's `llm_screen` template declares
`Param(..., requires_env=…)` at module scope. `Param.__init__` rejects that keyword today
(`TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`, probed by the
scoping), so the plugin H7b's registry would resolve **cannot be written** until this lands. Nothing
else in H7c gates this task.

**Names already at module level in `src/publishable/param.py`:** `MISSING`, `_TYPE_NAMES`, `Param`.
`_joined` is free. **Names already at module level in `tests/test_param.py`:** the ten `test_*`
functions and nothing else — no helpers, no constants. Any helper you add is new.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_param.py`:

```python
def test_requires_env_is_stored_and_needs_choices():
    """The keyword `Param.__init__` rejects today. `choices` is required because a
    credential requirement is only checkable when the value set is closed —
    `reference.md` § A credential can belong to a parameter value."""
    p = Param(
        str,
        default="azure_openai",
        choices=["azure_openai", "openai", "ollama"],
        requires_env={
            "azure_openai": ["AZURE_OPENAI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "ollama": [],
        },
    )
    assert p.requires_env["openai"] == ["OPENAI_API_KEY"]
    assert p.requires_env["ollama"] == []  # `[]` is a claim, not an omission

    with pytest.raises(ValueError, match="choices"):
        Param(str, default="a", requires_env={"a": ["A_KEY"]})


def test_a_param_without_requires_env_reports_none_rather_than_an_empty_mapping():
    """`None` and `{}` are different claims — the first is "this parameter declares
    nothing", the second would be "every choice needs nothing", which is only
    legal for an empty `choices`. Tasks 10 and 11 gate on truthiness, so the
    distinction is load-bearing rather than cosmetic."""
    assert Param(str, default="a", choices=["a", "b"]).requires_env is None


def test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets():
    """Both directions, each with its own distinguishing fragment.

    `reference.md` § A credential can belong to a parameter value requires the
    message to name *both sets*; the direction clause is what makes the two
    branches separately pinnable, since both raise `ValueError` and both surface
    to a user as one `E-TEMPLATE-LOAD`.
    """
    with pytest.raises(ValueError) as short:
        Param(
            str,
            default="a",
            choices=["a", "b", "c"],
            requires_env={"a": ["A_KEY"], "b": []},
        )
    text = str(short.value)
    assert "choices are a, b, c" in text          # both sets named
    assert "requires_env names a, b" in text      # both sets named
    assert "no key for c" in text                 # only the missing-key branch says this
    assert "naming no choice" not in text         # and only that branch

    with pytest.raises(ValueError) as extra:
        Param(
            str,
            default="a",
            choices=["a", "b"],
            requires_env={"a": ["A_KEY"], "b": [], "zz": ["Z_KEY"]},
        )
    text = str(extra.value)
    assert "choices are a, b" in text
    assert "requires_env names a, b, zz" in text
    assert "keys naming no choice: zz" in text    # only the unknown-key branch
    assert "no key for" not in text

    # Both directions at once, in one message: the fault a real edit makes when a
    # choice is renamed. Neither clause may swallow the other.
    with pytest.raises(ValueError) as both:
        Param(str, default="a", choices=["a", "b"], requires_env={"a": ["A_KEY"], "zz": []})
    text = str(both.value)
    assert "no key for b" in text
    assert "keys naming no choice: zz" in text


def test_a_total_requires_env_constructs_and_leaves_every_other_check_alone():
    """The honouring. Without it, ignoring `requires_env` entirely — storing it and
    checking nothing — passes every refusal test above."""
    p = Param(str, default=None, nullable=True, choices=["a", "b"],
              requires_env={"a": ["A_KEY"], "b": []})
    assert p.check("a") is None
    assert p.check("zz") is not None
    assert p.check(None) is None
```

- [ ] **Step 2: Run and see it fail.** `uv run pytest tests/test_param.py -q`. Every new test must
      fail with `TypeError: Param.__init__() got an unexpected keyword argument 'requires_env'`.
      A failure of any other shape means the argument already exists and this brief is stale.

- [ ] **Step 3: Implement.** In `src/publishable/param.py`:

Amend the module docstring, whose "closed on purpose" claim becomes false the moment this lands
(`H7c-SCOPING.md` § 9 names it):

```python
"""One parameter's type, default, constraints and help text.

The constraint vocabulary is closed on purpose: docs/reference.md § Templates.

`requires_env` is the one keyword here that is **not** a constraint and is
deliberately absent from that closed table: it constrains the *environment* a
value may be used in, not the value. § A credential can belong to a parameter
value states the boundary and the reason — the provider is something you decide,
so it is a `Param`, and what that decision requires travels with it.
"""
```

Add the helper beneath `_TYPE_NAMES`:

```python
def _joined(values: list[Any]) -> str:
    return ", ".join(str(v) for v in values)
```

Add the argument to `__init__`'s signature, after `nullable` and before `help`:

```python
        nullable: bool = False,
        requires_env: dict[Any, list[str]] | None = None,
        help: str | None = None,
```

Add the checks after the existing `ge/gt/le/lt` guard and before the attribute assignments, so a
`requires_env` fault is raised alongside the other construction faults rather than after a partly
built object exists:

```python
        if requires_env is not None:
            if choices is None:
                raise ValueError("requires_env requires choices: a credential requirement is "
                                 "only checkable over a closed set of values")
            absent = [c for c in choices if c not in requires_env]
            extra = [k for k in requires_env if k not in choices]
            if absent or extra:
                detail = ""
                if absent:
                    detail += f"; no key for {_joined(absent)}"
                if extra:
                    detail += f"; keys naming no choice: {_joined(extra)}"
                raise ValueError(
                    "requires_env must be total over choices: "
                    f"choices are {_joined(choices)}; "
                    f"requires_env names {_joined(list(requires_env))}{detail}"
                )
```

Store it beside `nullable`:

```python
        self.nullable = nullable
        self.requires_env = requires_env
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_param.py -q`, then the whole suite:
      **1957 + 4 new tests passed, 2 xfailed.** `uv run mypy` must be clean — `dict[Any, list[str]]`
      matches how `choices: list[Any]` is already typed, so a non-`str` choice stays legal.

- [ ] **Step 5: End-to-end confirmation that a fault is `E-TEMPLATE-LOAD`.** Append to
      `tests/test_validate.py` — its module-level names are `base_config`, `write_config`,
      `write_config_nondet`, `write_config_broken`, `write_config_exits`, `_DELETE`, `codes`,
      `messages_by_code`, `_validate_with`, `_error_codes`, plus the `_*_EXPERIMENT` source
      constants. `_CRED_TOTALITY_TEMPLATE` is free:

```python
_CRED_TOTALITY_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai", "ollama"],
            requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"]},
        )
    }
"""


def test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding(
    git_repo: Path, write_config
):
    """The route, probed end to end rather than reasoned from the phrasing:
    `Param.__init__` raises `ValueError`, `discover_local` catches it and
    interpolates `{exc!r}` into an `E-TEMPLATE-LOAD` message. No new identifier.

    `!r` is why the fragments below are quoted the way they are — the message
    carries `ValueError('...')`, not the bare text.
    """
    templates = git_repo / "templates"
    templates.mkdir()
    (templates / "cred_assay.py").write_text(_CRED_TOTALITY_TEMPLATE)

    found = messages_by_code(write_config({"experiment_type": "cred_assay", "parameters": {}}))
    assert "E-CRED-MISSING" not in found        # a load fault is not a credential finding
    assert "E-CRED-PARAM-MISSING" not in found
    message = found["E-TEMPLATE-LOAD"]
    assert "cred_assay.py" in message
    assert "ValueError(" in message             # the repr, per `{exc!r}`
    assert "no key for openai, ollama" in message
    assert "choices are azure_openai, openai, ollama" in message

    # THE CONTROL, and it is what makes the assertion above about the totality
    # check rather than about local discovery: the same template with a total
    # mapping loads, and `E-TEMPLATE-LOAD` disappears.
    (templates / "cred_assay.py").write_text(
        _CRED_TOTALITY_TEMPLATE.replace(
            'requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"]},',
            'requires_env={"azure_openai": ["AZURE_OPENAI_API_KEY"],\n'
            '                          "openai": ["OPENAI_API_KEY"],\n'
            '                          "ollama": []},',
        )
    )
    assert "E-TEMPLATE-LOAD" not in codes(
        write_config({"experiment_type": "cred_assay", "parameters": {}})
    )
```

Run it. It must pass with the implementation from step 3 already in place.

- [ ] **Step 6: Mutate — three, each with the test that must go red.**

  **(a) Delete the totality check.** Remove the `if absent or extra:` block from
  `param.py`. `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets` must
  FAIL at its first `pytest.raises` (no exception raised), and
  `test_a_requires_env_totality_fault_surfaces_as_a_template_load_finding` must FAIL on its
  `found["E-TEMPLATE-LOAD"]` lookup with a `KeyError`. **Checked against the test bodies:** both
  call `Param(...)` with a deliberately partial mapping and both observe the raise, so both
  discriminate.

  **(b) Drop the `extra` half.** Change `if absent or extra:` to `if absent:`. Only the
  **second** `pytest.raises` block in
  `test_requires_env_must_be_total_over_choices_and_the_message_names_both_sets` goes red — the
  unknown-key fixture has `choices=["a","b"]` fully keyed plus `"zz"`, so `absent` is empty and
  nothing raises. The first block still passes. **This is the mutation that proves the two branches
  are separately pinned**, which the code-only mutation (a) does not.

  **(c) Drop the `choices` requirement.** Remove the `if choices is None:` raise. The second half of
  `test_requires_env_is_stored_and_needs_choices` must FAIL — `Param(str, default="a",
  requires_env={"a": ["A_KEY"]})` would construct, and `pytest.raises(ValueError, match="choices")`
  reports `DID NOT RAISE`. Note that this mutation would *also* make `absent`/`extra` compute
  against `None` and raise `TypeError`, which is why the guard is a raise and not a silent skip —
  check that the failure you see is `DID NOT RAISE`, not a `TypeError`; if it is a `TypeError` the
  guard order in step 3 was transcribed wrong.

  After each: `find . -name __pycache__ -type d -exec rm -rf {} +`, edit the file back by hand,
  re-run, confirm green. **Never `git checkout --`.**

- [ ] **Step 7: Which deliverable no mutation reaches.** `self.requires_env` being *stored* is
      pinned only by `test_requires_env_is_stored_and_needs_choices`'s two reads, which is enough —
      dropping the assignment gives `AttributeError`. **`_joined`'s output order** is not
      independently pinned: it follows `choices`'s declared order and the fixtures happen to declare
      them sorted. Deliberate and left — the order is `choices`'s, not this function's, and a
      fixture that separated them would be pinning `list` iteration order. Say so in the task
      report rather than adding an assertion.

- [ ] **Step 8: Verify and commit.** All four commands. `feat: Param(requires_env=) — the
      constructor argument, total over choices` — and note in the message that **this is the H7b
      prerequisite**.

---

## Task 4: `Param.comment()` renders the requirement against every choice

**Files:** Modify `src/publishable/param.py`, `tests/test_param.py`.

**Interfaces:**
- Consumes: `Param.comment(self) -> str`, and `self.requires_env` from task 3.
- Produces: a `choices` comment carrying each value's variables, exactly as `reference.md`
  § A credential can belong to a parameter value renders it:
  `choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama`.

**Against every choice, not the written one**, because nothing ever writes back into a config and a
comment describing the *current* value would be wrong the first time the file was edited. That is
the property every other inline comment already has.

**The blast radius, measured.** `grep -rn "choices:" tests/ docs/reference.md src/publishable/` at
`478c1f3` returns six sites: `tests/test_param.py` (the `comment()` unit assertion),
`tests/test_materialize.py` (`# choices: pearson | spearman | kendall` in a generated config),
`reference.md`'s worked-example config line, its § Templates constraint table row, its
§ A credential can belong to a parameter value example, and its § Secrets-adjacent parameter table.
**`generic` declares no `requires_env`, so both test sites must be byte-identical after this task** —
that is the regression control, and it already exists.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_param.py`:

```python
def test_a_choices_comment_carries_each_value_s_credential_against_every_choice():
    """`reference.md` § A credential can belong to a parameter value shows this
    exact string. Every choice is annotated, not the default — a comment about
    the current value would be wrong the first time the config was edited.

    Three choices, not two, and the annotated ones are NOT contiguous with the
    default: with two, "annotate every choice" and "annotate the written one"
    both produce a one-annotation string for some arrangement.
    """
    p = Param(
        str,
        default="azure_openai",
        choices=["azure_openai", "openai", "ollama"],
        requires_env={
            "azure_openai": ["AZURE_OPENAI_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "ollama": [],
        },
    )
    assert p.comment() == (
        "choices: azure_openai (needs AZURE_OPENAI_API_KEY) | "
        "openai (needs OPENAI_API_KEY) | ollama"
    )


def test_a_value_needing_two_variables_names_both_in_its_own_parenthesis():
    p = Param(
        str,
        default="a",
        choices=["a", "b"],
        requires_env={"a": ["A_ONE", "A_TWO"], "b": []},
    )
    assert p.comment() == "choices: a (needs A_ONE, A_TWO) | b"
```

And leave `test_comments_render_the_constraint_that_claims_them` **untouched** — its
`Param(str, default="a", choices=["a", "b"]).comment() == "choices: a | b"` is the regression
control for a parameter with no `requires_env`, and it must still pass unchanged.

- [ ] **Step 2: Run and see it fail.** Both new tests fail on the missing `(needs …)` suffix.

- [ ] **Step 3: Implement.** In `param.py`, replace `comment()`'s first branch and add one helper
      method beneath `comment()`:

```python
    def comment(self) -> str:
        """The inline comment `init` renders. One constraint claims it, else `help`.

        A `choices` comment additionally carries each value's `requires_env`
        variables. Those are not a constraint — see this module's docstring —
        and they are rendered against *every* choice rather than the written
        one, because nothing ever writes back into a config and a comment about
        the current value would be wrong the first time the file was edited.
        """
        if self.choices is not None:
            return "choices: " + " | ".join(self._choice_label(c) for c in self.choices)
```

(the rest of the body is unchanged), and:

```python
    def _choice_label(self, choice: Any) -> str:
        needs = (self.requires_env or {}).get(choice) or []
        if not needs:
            return str(choice)
        return f"{choice} (needs {', '.join(needs)})"
```

- [ ] **Step 4: Run and see it pass.** `uv run pytest tests/test_param.py tests/test_materialize.py -q`
      first — `test_materialize.py`'s `# choices: pearson | spearman | kendall` is the generated-file
      regression and must be untouched — then the whole suite.

- [ ] **Step 5: Mutate — two.**

  **(a) Render the written value's annotation everywhere.** Change the join to
  `self._choice_label(self.default) for c in self.choices`.
  `test_a_choices_comment_carries_each_value_s_credential_against_every_choice` must FAIL: it would
  produce `choices: azure_openai (needs AZURE_OPENAI_API_KEY) | azure_openai (needs
  AZURE_OPENAI_API_KEY) | azure_openai (needs AZURE_OPENAI_API_KEY)`. **Checked against the test
  body:** the assertion is an exact string equality over a three-choice fixture whose annotations
  differ, so it discriminates. Note that `test_comments_render_the_constraint_that_claims_them` also
  goes red under this mutation (`choices: a | a`), which is fine — the mutation must fail *at least*
  the named test.

  **(b) Drop the empty-list distinction.** Change `if not needs:` to `if needs is None:`. Then
  `ollama`, whose value is `[]`, renders as `ollama (needs )`. The first new test must FAIL.
  **This is the mutation that pins `[]` as "needs nothing" rather than as a missing key**, which
  mutation (a) does not reach.

  Revert each by editing the file back; delete `__pycache__`; re-run; confirm green.

- [ ] **Step 6: Which deliverable no mutation reaches.** The **generated config's** rendering — the
      path from `comment()` through `materialize.py` into a real `config.yaml` — is exercised only
      for `generic`, which declares no `requires_env`, so `tests/test_materialize.py` proves the
      *absence* case and nothing proves the presence case end to end at this commit. That is
      accepted here: no template in the tree declares `requires_env`, and inventing a local one
      purely to render a comment would test `materialize.py`'s existing loop rather than this task.
      **Task 10's fixture is the first local template that declares one**; if its config is
      generated rather than hand-written it closes this incidentally — do not force it.

- [ ] **Step 7: Verify and commit.** All four commands.
      `feat: a choices comment carries each value's requires_env, against every choice`

---

## Task 5: § Templates' constraint table stays closed, and `reference.md`'s present-tense claim

**Files:** Modify `docs/reference.md`. No `src/` change, no test change.

**Interfaces:**
- Consumes: § Templates' constraint table (header `| Constraint | Applies to | Renders as |`, six
  rows: `choices`, the four bounds, `pattern`, the list trio, `nullable`, `help`), and the sentence
  in the same section reading "`Param` carries type, default, constraints, help text, and any
  credential a chosen value requires".
- Produces: both correct once task 3 and task 4 land. **`requires_env` does not enter the table.**

**Two things are true at once and the paragraph currently obscures it.** The "`Param` carries …
any credential a chosen value requires" sentence sits **inside the paragraph that introduces the
closed table**, in the present tense, about an argument `Param.__init__` rejected until task 3 — it
was **false today** when the scoping measured it (`H7c-SCOPING.md` § 9) and becomes true with task
3. Meanwhile `requires_env` must stay *out* of the table, a rule that is normative in two files
(`CLAUDE.md` § Invariants a change must not quietly break, and § A credential can belong to a
parameter value's closing paragraph). This task keeps the two apart.

**Do not touch** the sentence "`validate` rejects a mapping with a missing or unknown key when the
template loads, naming both sets" — task 1 owns it and has already extended it.

- [ ] **Step 1: Read the section.** Read § Templates from the `aggregate` discussion through the end
      of § A credential can belong to a parameter value. Confirm the constraint table has six rows
      and that `requires_env` appears in none of them.

- [ ] **Step 2: Separate the sentence from the table.** Rewrite the "`Param` carries …" sentence so
      the credential clause is marked as the non-constraint it is, and so the table's closure
      sentence immediately after is not read as covering it:

```
`Param` carries type, default, constraints, and help text — so `init` renders the file with accurate inline comments, and `validate` enforces exactly what was documented. Adding a parameter in one place makes it appear in newly-initialized configs and become enforceable at once. It carries one thing that is **not** a constraint and so is not in the table below: [the credential a chosen value requires](#a-credential-can-belong-to-a-parameter-value), which constrains the environment a value may be used in rather than the value.
```

- [ ] **Step 3: Leave the table alone, and say why in the section that already argues it.** The
      closing paragraph of § A credential can belong to a parameter value already reads "This is not
      a constraint, so it isn't in the closed vocabulary above". Confirm it still resolves — the
      word "above" there refers to the constraint table **in a different subsection**, so check the
      table is still the nearest preceding one and, if it is not, name what the table *does* rather
      than where it sits. Do not locate it by position.

- [ ] **Step 4: Re-run the enum-comment cross-document rule.** § A credential can belong to a
      parameter value's rendered example is

```yaml
    # choices: azure_openai (needs AZURE_OPENAI_API_KEY) | openai (needs OPENAI_API_KEY) | ollama
```

Confirm it lists **every** value the `Param` above it declares (three), that the string is
**byte-identical** to what task 4's `comment()` now produces for that declaration, and that the
`choices` row of the constraint table (`# choices: a \| b \| c`) still shows the *unannotated* form,
which is what a parameter with no `requires_env` renders. Both forms are correct and neither is a
fix for the other.

- [ ] **Step 5: Config completeness.** § The one config file's fenced example is the config schema
      for template `generic` at full expansion. `generic` declares no `requires_env`, so **no config
      field is added by this slice** and that example does not move. Confirm by reading its
      `analysis.method` line — it must still read `# choices: pearson | spearman | kendall`.

- [ ] **Step 6: Mechanical pass** over § Templates and § A credential can belong to a parameter
      value: links, anchors, table column counts, whitespace, `×` for multiplication, hyphen not en
      dash. Skip fenced blocks.

- [ ] **Step 7: Mutation.** Document-only; **no mutation reaches it**, stated rather than
      manufactured. The property this task defends — `requires_env` is not in the closed table — is
      a *document* rule, and the code half that would betray it does not exist: `param.py` has no
      table. The nearest testable consequence is task 4's rendering, already pinned. The
      verification here is the step-4 comparison: render
      `Param(str, default="azure_openai", choices=["azure_openai","openai","ollama"],
      requires_env={...}).comment()` in a throwaway `uv run python -c` and diff it against the
      document's line, character for character. **Do that; do not eyeball it.**

- [ ] **Step 8: Commit.** `docs: requires_env stays out of the closed constraint table, and § Templates' present-tense claim is reconciled`

---

## Task 6: § Package layout, § The importable surface, and decision 8

**Files:** Modify `docs/reference.md`. No `src/` change, no test change. **Depends on task 7 for
truth** — see the ordering note.

**Interfaces:**
- Consumes: § Package layout's `secrets.py` line, which reads
  `│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance) — not yet built`;
  § The importable surface's enumerated table and its "A row marked `not yet built` is a promise"
  paragraph.
- Produces: `secrets.py` without its `— not yet built` marker, and an explicit statement that this
  slice exports nothing.

**Ordering note the implementer must respect.** § Package layout's marker means "specified and
unbuilt", so retiring it is a **build claim**. Do the § The importable surface half now; **do the
`secrets.py` marker retirement as the last step of task 7**, in task 7's commit, so the document
never claims a module that is not there. This task's step 2 is therefore explicitly deferred, and
task 7 step 8 executes it. Recorded here rather than in task 7 alone so a reader of either task
finds it.

- [ ] **Step 1: State that this slice exports nothing.** In § The importable surface, after the
      paragraph beginning "**A row marked `not yet built` is a promise, not an export.**", add:

```
**Not everything core adds is a name on this table, and the credential mechanism is the example.** `required_env` is an attribute of a class you already subclass and [`requires_env`](#a-credential-can-belong-to-a-parameter-value) is a keyword of a construct you already import, so declaring either adds no import line to your template. A mechanism reaching you through a class you subclass and a keyword you pass is the shape to expect: this table enumerates what you *import*, and it moves only when there is a new name to import.
```

- [ ] **Step 2: DEFERRED to task 7 step 8.** Retiring `secrets.py`'s `— not yet built` marker in
      § Package layout. Do not do it here; the module does not exist yet at this commit.

- [ ] **Step 3: Check the `Status` column.** § The importable surface's table has a `Status` column
      whose values this slice does not move: `Param` is already `built`, `BaseTemplate` is already
      `built`. Confirm neither row needs a change, and confirm the sentence "Importing one raises
      `ImportError` today" is still derived from that column rather than from an enumeration of
      names — `CLAUDE.md` records that replacing it with an enumeration would convert a
      self-maintaining statement into a maintenance obligation nobody owns.

- [ ] **Step 4: Mechanical pass** over the edited paragraphs: links and anchors resolve
      (`#a-credential-can-belong-to-a-parameter-value`), no duplicate anchors introduced, no trailing
      whitespace, no tab, no invisible unicode.

- [ ] **Step 5: Mutation.** Document-only; **no mutation reaches it.** The claim "this slice exports
      nothing" is verified by a grep, not a test: `git diff 478c1f3 -- src/publishable/__init__.py`
      must be empty at the end of this slice. **Run that at task 14** and record the result there;
      note the obligation in this task's commit message.

- [ ] **Step 6: Commit.** `docs: the importable surface does not move — a subclass attribute and a Param keyword are not exports`

---

## Task 7: `secrets.py` and the `python-dotenv` dependency

**Files:** Create `src/publishable/secrets.py`, `tests/test_secrets.py`. Modify `pyproject.toml`,
`uv.lock`, `docs/reference.md` (§ Package layout's marker, deferred from task 6).

**Interfaces:**
- Consumes: `dotenv.load_dotenv(dotenv_path=None, stream=None, verbose=False, override=False,
  interpolate=True, encoding="utf-8") -> bool` — read from `python-dotenv` 1.2.1's `dotenv/main.py`,
  which ships `py.typed`, so **no `mypy` override is expected**. If `uv run mypy` reports a missing
  stub anyway, add `[[tool.mypy.overrides]] module = "dotenv.*"` with
  `ignore_missing_imports = true` in this task and say so in the report — that contingency is named
  here so it is not discovered.
- Produces, all consumed by tasks 8–12:
  - `load_env(repo_root: Path | None) -> bool`
  - `missing_env(names: Iterable[str]) -> list[str]`
  - `credential_values(names: Iterable[str]) -> dict[str, str]`
  - `redact(text: str | None, values: Mapping[str, str]) -> str | None`

**`python-dotenv` is the first runtime dependency this project has added since scaffolding.**
`pyproject.toml` declares `pyyaml`, `numpy`, `scipy`, `pyarrow` today. `code_hash` covers `src/**`
and `templates/**` only, so this disturbs no recorded hash — but it does move `uv.lock`. Version
1.2.1 is already in the local `uv` cache, so `uv add` resolves offline.

- [ ] **Step 1: Add the dependency.** `uv add python-dotenv`. Confirm `pyproject.toml`'s
      `dependencies` now lists it and `uv.lock` moved. Then confirm the import works:
      `uv run python -c "import dotenv; print(dotenv.__version__)"`.

- [ ] **Step 2: Write the failing tests.** Create `tests/test_secrets.py` — a new file, so no
      existing module-level name can be shadowed:

```python
from pathlib import Path

import pytest

from publishable.secrets import credential_values, load_env, missing_env, redact

_NAME = "PUBLISHABLE_TEST_TOKEN"
_OTHER = "PUBLISHABLE_TEST_OTHER"


def test_a_shell_value_wins_over_the_file(tmp_path: Path, monkeypatch):
    """`override=False` is the safety property, not a default that happened to be
    there: a stale `.env` must never silently redirect a run to another account.
    Flipping it is a one-word change, so it is pinned by a test rather than by a
    comment."""
    monkeypatch.setenv(_NAME, "from-the-shell")
    (tmp_path / ".env").write_text(f"{_NAME}=from-the-file\n")

    assert load_env(tmp_path) is True          # the file WAS read — a positive companion
    assert credential_values([_NAME]) == {_NAME: "from-the-shell"}


def test_an_unset_variable_takes_the_file_s_value_and_the_load_is_idempotent(
    tmp_path: Path, monkeypatch
):
    """The honouring half. `delenv` first, because `load_dotenv` writes straight
    into `os.environ` and monkeypatch is the only thing that puts it back."""
    monkeypatch.delenv(_NAME, raising=False)
    (tmp_path / ".env").write_text(f"{_NAME}=from-the-file\n")

    assert load_env(tmp_path) is True
    assert credential_values([_NAME]) == {_NAME: "from-the-file"}
    assert load_env(tmp_path) is True          # twice, same answer
    assert credential_values([_NAME]) == {_NAME: "from-the-file"}


def test_no_repo_and_no_file_are_both_quiet(tmp_path: Path, monkeypatch):
    monkeypatch.delenv(_NAME, raising=False)
    assert load_env(None) is False
    assert load_env(tmp_path) is False         # a real directory holding no `.env`
    assert credential_values([_NAME]) == {}


def test_missing_env_answers_in_declared_order_and_dedupes(monkeypatch):
    monkeypatch.setenv(_NAME, "set")
    monkeypatch.delenv(_OTHER, raising=False)
    monkeypatch.delenv("PUBLISHABLE_TEST_THIRD", raising=False)
    assert missing_env([_OTHER, _NAME, "PUBLISHABLE_TEST_THIRD", _OTHER]) == [
        _OTHER,
        "PUBLISHABLE_TEST_THIRD",
    ]
    # THE CONTROL: with everything set, the answer is empty — so a function that
    # returned its whole argument would fail here rather than only above.
    monkeypatch.setenv(_OTHER, "set")
    monkeypatch.setenv("PUBLISHABLE_TEST_THIRD", "set")
    assert missing_env([_OTHER, _NAME, "PUBLISHABLE_TEST_THIRD"]) == []


def test_an_empty_string_counts_as_unset():
    """A variable exported as the empty string is a name someone wrote down and
    never filled in, which is the fault this family exists to catch — not a
    credential whose value happens to be empty."""
    import os

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv(_NAME, "")
        assert missing_env([_NAME]) == [_NAME]
        assert credential_values([_NAME]) == {}
    assert _NAME not in os.environ  # the context restored it


def test_redaction_replaces_the_exact_value_and_names_the_variable():
    text = "RuntimeError: POST https://api/v1?key=sk-abc123 failed"
    assert redact(text, {"OPENAI_API_KEY": "sk-abc123"}) == (
        "RuntimeError: POST https://api/v1?key=<redacted:OPENAI_API_KEY> failed"
    )
    # By exact value, never by pattern: a string that merely LOOKS like a
    # credential is untouched, because core did not read it out of the
    # environment. This is the fail-closed direction of decision 4.
    assert redact("RuntimeError: token sk-zzzzzz rejected", {"OPENAI_API_KEY": "sk-abc123"}) == (
        "RuntimeError: token sk-zzzzzz rejected"
    )
    assert redact(None, {"OPENAI_API_KEY": "sk-abc123"}) is None
    assert redact("nothing to do", {}) == "nothing to do"


def test_a_value_that_contains_another_value_is_redacted_whole():
    """Longest first. With `SHORT` applied before `LONG`, the longer value is left
    half-exposed as `<redacted:SHORT>def` — a leak that reads as a redaction.
    Two credentials where one value is a prefix of the other is the only fixture
    that can tell the two orders apart."""
    values = {"SHORT": "abc", "LONG": "abcdef"}
    assert redact("saw abcdef here", values) == "saw <redacted:LONG> here"
    assert redact("saw abc here", values) == "saw <redacted:SHORT> here"
```

- [ ] **Step 3: Run and see it fail.** `uv run pytest tests/test_secrets.py -q` —
      `ModuleNotFoundError: No module named 'publishable.secrets'`.

- [ ] **Step 4: Implement.** Create `src/publishable/secrets.py`:

```python
"""`.env` loading and the credential values core read.

docs/reference.md § Secrets & credentials. A config holds an environment
variable's NAME; the value lives in `.env`, which every scaffold gitignores.

**Never touches provenance**, and the claim is structural rather than careful:
nothing in this module imports `publishable.provenance` or writes into the
document it builds, and `provenance.environment` is assembled from `os`,
`hostname`, `hardware` and `uv.lock` alone. The one surface on which a value
could reach a record is a failing step's exception text, which `redact` below
exists for.
"""

import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from dotenv import load_dotenv

ENV_FILENAME = ".env"


def load_env(repo_root: Path | None) -> bool:
    """Load `<repo_root>/.env` into `os.environ`. Returns whether a file was read.

    **Never overrides.** `override=False` means a variable already exported in the
    shell wins over the file, which is the direction that fails safe: a stale
    `.env` cannot silently redirect a run to the wrong account, and a machine that
    supplies its credentials through a secret manager needs no file at all.

    Idempotent, because it is called twice on a `run` — once by `validate` and
    once before any step executes — and a second load with `override=False` can
    only re-set what is already set.

    A `None` root (no git repository) and a directory holding no `.env` are both
    quiet: a project whose credentials are exported rather than filed is ordinary,
    and this function has no way to tell it from one that forgot. Whether a
    *declared* variable is missing is `missing_env`'s question, asked by
    `validate` against what a template declares.
    """
    if repo_root is None:
        return False
    path = repo_root / ENV_FILENAME
    if not path.is_file():
        return False
    return load_dotenv(path, override=False)


def missing_env(names: Iterable[str]) -> list[str]:
    """Declared names with no value, in declared order, each named once.

    An empty string counts as missing: a name exported with no value is one
    somebody wrote down and did not fill in, which is the fault this family
    exists to catch.
    """
    seen: set[str] = set()
    out: list[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        if not os.environ.get(name):
            out.append(name)
    return out


def credential_values(names: Iterable[str]) -> dict[str, str]:
    """The values core read for the declared names — `{name: value}`, unset omitted.

    This is the knowledge `redact` answers from, and the whole of decision 4: core
    can say *is this the value I read out of the environment* rather than *does
    this look like a secret*. A pattern check fails open on a credential named
    `instrument_pw` and fails closed on a config value that happens to look
    random.

    Held only for the length of one command, and never written anywhere: the
    mapping is built where a run starts and reaches exactly one consumer.
    """
    found: dict[str, str] = {}
    for name in names:
        value = os.environ.get(name)
        if value:
            found[name] = value
    return found


def redact(text: str | None, values: Mapping[str, str]) -> str | None:
    """Replace each credential value in `text` with a marker naming its variable.

    Longest value first, so a credential whose value is a prefix of another's
    cannot leave the longer one half-exposed as `<redacted:SHORT>def` — which
    would read as a redaction while being a leak.

    Says a redaction happened rather than scrubbing silently: the record exists to
    be debugged from, and `<redacted:OPENAI_API_KEY>` tells a reader both what was
    removed and which variable to look at, without telling them the value.
    """
    if not text or not values:
        return text
    for name, value in sorted(values.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        if value:
            text = text.replace(value, f"<redacted:{name}>")
    return text
```

- [ ] **Step 5: Run and see it pass.** `uv run pytest tests/test_secrets.py -q`, then the full suite:
      **1957 + task 3's 5 + task 4's 2 + these 7 = 1971 passed, 2 xfailed** (adjust for what actually
      landed; the point is that nothing existing broke). `uv run mypy` must be clean.

- [ ] **Step 6: Mutate — three.**

  **(a) `override=False` → `override=True`.** `test_a_shell_value_wins_over_the_file` must FAIL:
  `credential_values` would return `from-the-file`. **Checked against the test body:** it sets the
  shell value with `monkeypatch.setenv` *before* writing a different value into the file, and
  asserts on the resolved value, so the two branches genuinely differ.

  **(b) Drop the longest-first sort.** Change `sorted(values.items(), key=...)` to
  `values.items()`. `test_a_value_that_contains_another_value_is_redacted_whole` must FAIL — insertion
  order puts `SHORT` first, so `"saw abcdef here"` becomes `"saw <redacted:SHORT>def here"`.
  **Checked:** the fixture is a dict literal with `SHORT` written first, so the mutant's order is
  deterministic and different. Without that fixture this mutation would be blind, which is why the
  test exists.

  **(c) Treat an empty string as set.** Change `if not os.environ.get(name):` to
  `if os.environ.get(name) is None:` in `missing_env`. `test_an_empty_string_counts_as_unset` must
  FAIL.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches — say it plainly.** The docstring's **"never
      touches provenance"** claim is a safety claim, and `CLAUDE.md` is explicit that a safety
      argument in a comment needs a mutation like any other. **No mutation in this task reaches it**,
      because at this commit nothing calls `secrets.py` at all: there is no run for a value to leak
      into. **Task 12 closes it** — its sweep covers `run.yaml`, which embeds the whole `provenance`
      block, and its mutation (deleting the redaction call) makes that sweep go red. Do not
      substitute a source-text assertion (`"provenance" not in inspect.getsource(...)`) here; that
      is a proxy for the fact, which is exactly the move `CLAUDE.md` § Answering a question with a
      proxy records as twice-burned.

- [ ] **Step 8: Execute task 6's deferred step.** In `docs/reference.md` § Package layout, retire
      `secrets.py`'s marker so the line reads:

```
│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance)
```

Then confirm the surrounding paragraph ("**Modules marked `— not yet built` are specified and
unbuilt.**") still describes a non-empty set — `apparatus.py`, `reproduce.py`, `report.py` remain —
and run the mechanical pass over the fenced tree block (it is a code fence, so the anchor and table
checks do not apply; check alignment and whitespace only).

- [ ] **Step 9: Verify and commit.** All four commands.
      `feat: secrets.py — .env loading, the values core read, and redaction by exact value`

---

## Task 8: The two load sites, and the reconciled single-site sentence

**Files:** Modify `src/publishable/validate.py`, `src/publishable/cli.py`, `docs/reference.md`,
`tests/test_validate.py`, `tests/test_cli.py`.

**Interfaces:**
- Consumes: `load_env(repo_root: Path | None) -> bool` from task 7;
  `validate_config(config_path: Path, c: Collector, *, experiment: Any | None = None) ->
  dict[str, Any] | None`, whose body resolves `repo_root: Path | None` inside a
  `try/except ContractError` before it resolves the template; `cli.command_run(config_path: Path) ->
  int`, which calls `validate_config` and then `repo_root = find_repo_root(config_path)`.
- Produces: `.env` loaded at both sites. **The patch targets tasks 8 and 12 name are
  `publishable.validate.load_env` and `publishable.cli.load_env`** — two different module
  attributes, and a patch on one does not affect the other.

**Why two sites and not one, written down so nobody deletes the second.** `command_run` calls
`validate_config`, so by the time `run` reaches `execute_plan` the environment is already loaded and
the `cli.py` call looks like dead code. It is not: **loading is a precondition of executing, not a
side effect of checking.** A future `run` that skips `validate` — or any executing command that
reaches the runner by another path — must still have the environment. Task 7 made the load
idempotent and non-overriding precisely so the second call costs nothing. Step 4's test is what
stops the deletion.

**`draft` and `resume` are in `cli.NOT_BUILT_COMMANDS`** (together with `dry-run`, `demo`, `diff`,
`docs`, `freeze`, `list-templates`, `plugin new`, `report`, `reproduce`, `study add`, `study new`).
The scoping's § 8 task 8 says the load site is "`run`/`draft`/`resume`"; the buildable set is
**`command_run` alone**. Handle it the way the scoping handled `dry-run`: build the one executing
site, write the document's sentence as what the *specification* says, and record that `draft` and
`resume` inherit the load when they are built. **Do not stub a `command_draft`.**

- [ ] **Step 1: Write the failing tests.**

Append to `tests/test_validate.py`:

```python
def test_validate_loads_dot_env_from_the_repository_root(git_repo: Path, write_config, monkeypatch):
    """`validate` reads `.env`. Not a breach of its promise — `reference.md`
    § Validation promises it "creates nothing and reaches nothing **off the
    machine**", and a file in the repository root is on-machine.

    `delenv` first: `load_dotenv` writes straight into `os.environ` and only
    monkeypatch puts it back.
    """
    import os

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    (git_repo / ".env").write_text("PUBLISHABLE_TEST_TOKEN=from-the-file\n")

    path = write_config()
    assert codes(path) == set()                      # the config itself is clean
    assert os.environ.get("PUBLISHABLE_TEST_TOKEN") == "from-the-file"

    # THE CONTROL: with no `.env`, the same validate leaves the name unset — so
    # this test fails on a build that never loads rather than passing on a
    # machine that happened to export it.
    (git_repo / ".env").unlink()
    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    assert codes(write_config()) == set()
    assert os.environ.get("PUBLISHABLE_TEST_TOKEN") is None
```

Append to `tests/test_cli.py` — its module-level names are `Ran`, `run_a_project`,
`_AGGREGATE_STEP`, `_TRAIN_TOUCHING_STEP` and the `test_*` functions; `_ENV_READING_STEP` is free:

```python
_ENV_READING_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        # Reads the environment directly, which is how `reference.md` § Secrets &
        # credentials says a step gets a credential: core hands it none.
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        for unit in io.units:
            io.record(unit.key, {{"present": True}})
        return {{"token_len": len(token)}}
"""


def test_run_loads_dot_env_itself_rather_than_relying_on_validate(tmp_path, monkeypatch):
    """The second load site earns its existence. `publishable.validate.load_env` is
    patched to a no-op — NOT `publishable.cli.load_env`, which is a different
    module attribute and the one under test — so if `command_run` did not load
    for itself, the step's `os.environ[...]` would raise `KeyError` and the
    execution would land `failed`.

    `expect_exit=EXIT_OK` is the assertion: a `KeyError` in the one step makes the
    run `partial`, which is `EXIT_PARTIAL`.
    """
    import publishable.validate as validate_mod

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(validate_mod, "load_env", lambda repo_root: False)

    doc = run_a_project(
        tmp_path, units=4, _starter_step=_ENV_READING_STEP, _env_file="PUBLISHABLE_TEST_TOKEN=abcdefgh\n"
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    per_repeat = run["results"]["conditions"][0]
    # Something that must REPORT, not an absence: the step got the real value and
    # returned its length. 8 is `len("abcdefgh")`, derived from the fixture above.
    assert json.dumps(per_repeat).count('"token_len": 8') >= 1
```

**`run_a_project` needs two new keywords, `_env_file` and `_local_template`**, since it scaffolds
the project itself and nothing outside it can write into `root` before `main(["run", ...])` runs.
Add both in this task — `_env_file` is used here, `_local_template` by **task 12 step 7**, and they
are added together because they are one edit to one signature:

```python
    _env_file: str | None = None,
    _local_template: str | None = None,
```

and, immediately after `assert main(["new", str(root)]) == EXIT_OK` and before the
`pytest.MonkeyPatch.context()` block:

```python
    if _env_file is not None:
        # The scaffold's own `.gitignore` opens with `.env`, so this never reaches
        # the commit below and never makes `src/**`+`templates/**` dirty.
        (root / ".env").write_text(_env_file)
    if _local_template is not None:
        # The opposite property, and it is why this is written HERE rather than
        # after the config is generated: `code_hash` covers `templates/**`, so this
        # file must exist before the `git add .` below or `run` refuses the tree as
        # dirty. Written as `templates/cred_assay.py`, the one name every caller
        # that passes this registers.
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / "cred_assay.py").write_text(_local_template)
```

Extend the docstring with one paragraph per keyword, in the same register as its neighbours.
**Do not enumerate their call sites there** — two docstrings in this repo went stale that way and
one is an open `spec-defects.md` gap.

- [ ] **Step 2: Run and see them fail.** The `validate` test fails on
      `os.environ.get(...) == "from-the-file"` (nothing loads). The `cli` test fails with the
      execution having failed on `KeyError` — read the run's `error` field to confirm that is the
      reason, rather than assuming it.

- [ ] **Step 3: Implement.**

In `src/publishable/validate.py`, add to the import block (alphabetical among the
`from publishable.…` imports):

```python
from publishable.secrets import load_env
```

and, inside `validate_config`, immediately after the `try/except ContractError` that resolves
`repo_root` and before the template is resolved:

```python
    # `.env`, once, before any check that asks whether a variable is set.
    # `reference.md` § Validation promises `validate` "creates nothing and
    # reaches nothing off the machine"; a file in the repository root is
    # on-machine, so this is inside that promise rather than an exception to it.
    # Never overrides an exported variable — see `secrets.load_env`.
    load_env(repo_root)
```

In `src/publishable/cli.py`, add `from publishable.secrets import load_env` to the import block and,
in `command_run`, immediately after `repo_root = find_repo_root(config_path)`:

```python
    # The second load site, and it is not redundant. Loading is a precondition of
    # *executing*, not a side effect of checking: `validate` loads because three
    # § Validation rows ask whether a variable is set, and `run` loads because a
    # step is about to read one. Idempotent and never overriding, so the second
    # call costs nothing. `reference.md` § Secrets & credentials.
    load_env(repo_root)
```

- [ ] **Step 4: Run and see them pass.** Both new tests, then the full suite.

- [ ] **Step 5: Reconcile the document.** In `reference.md` § Secrets & credentials, replace "Core
      loads `.env` via `python-dotenv` before any step runs, never reads it into provenance, and
      gitignores it in every scaffold." with:

```
**Core loads `.env` via `python-dotenv` at two moments**, never reads it into provenance, and gitignores it in every scaffold. [`validate`](#validation) loads it because three of its checks ask whether a variable is *set*, and every command that executes loads it again before any step runs, because a step is about to read one — loading is a precondition of executing rather than a side effect of checking. The load never overrides a variable already exported, so a machine supplying its credentials through a secret manager needs no file at all, and a stale `.env` cannot silently redirect a run. **This is not an exception to [`validate`'s promise](#validation)**, which is that it creates nothing and reaches nothing *off the machine*: a file in the repository root is on-machine. In this build the executing site is `run`; [`draft`, `resume` and `dry-run`](#cli-reference) inherit it when each is built.
```

Check that `#validation` and `#cli-reference` both resolve to real headings before committing.

- [ ] **Step 6: Mutate — two.**

  **(a) Delete the `load_env(repo_root)` call in `cli.command_run`.**
  `test_run_loads_dot_env_itself_rather_than_relying_on_validate` must FAIL. **Checked against the
  test body:** it patches `publishable.validate.load_env` to a no-op, so with `cli`'s call gone
  nothing loads, the step raises `KeyError`, the run becomes `partial`, and `run_a_project`'s
  `assert main(...) == expect_exit` fails against the default `EXIT_OK` before the `token_len`
  assertion is even reached. Every `validate` test stays green — which is the point: this mutation
  is the one that proves the second site is load-bearing, and no test written before this task could
  have caught it.

  **(b) Delete the `load_env(repo_root)` call in `validate_config`.**
  `test_validate_loads_dot_env_from_the_repository_root` must FAIL on its
  `os.environ.get(...) == "from-the-file"` assertion. The `cli` test stays green (it patched that
  site away anyway), so the two mutations discriminate the two sites *separately*, which a single
  end-to-end test could not.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches.** The clause "never overrides" is pinned in
      `tests/test_secrets.py` (task 7's mutation (a)) but **not through either wired site** — no test
      here writes a `.env` whose value differs from an exported one and then runs. Accepted:
      `load_env` is the single implementation both sites call, and duplicating the override test at
      each call site would pin the call rather than the behaviour. Named here so it is not
      rediscovered.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: load .env at both sites — validate, and before any step runs`

---

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

## Task 10: The `requires_env` union over the conditions the sweep resolves

**Files:** Modify `src/publishable/validate.py`, `tests/test_validate.py`.

**Interfaces:**
- Consumes: `expand(config: dict[str, Any]) -> list[Condition]` from `publishable.sweep`, already
  imported in `validate.py`; `Condition(index: int, label: str | None, values: Mapping[str, Any],
  is_baseline: bool, selectors: frozenset[str])` — read from `src/publishable/sweep.py`;
  `_flatten(node: Any, prefix: str = "") -> dict[str, Any]` and `MISSING`, both already in
  `validate.py`; `Param.requires_env` from task 3; `missing_env` from task 7.
- Produces: `_check_requires_env(doc: dict[str, Any], template: Any, c: Collector) -> None`,
  emitting `E-CRED-PARAM-MISSING`.

**How a condition's value is resolved, and why not through `runner.resolve_condition_cfg`.**
`resolve_condition_cfg` deep-copies the whole document and returns a `Config`; this check needs one
dotted path's value, for each of a handful of paths, once per condition. The overlay is the same
three lines it performs — declared parameters, then each of `condition.values` whose path is **not**
in `condition.selectors` — computed locally against `_flatten`, which `_check_parameters` already
uses for exactly this. `validate.py` does not import `runner` today and this task does not make it.
**The selector skip is `resolve_condition_cfg`'s own rule and its reason is quoted at that function:
a group cell names no parameter at all**, so laying `{arm: control}` over `parameters` would invent
an `arm` no `parameter_spec` declares.

**Decision 6's fixture, sized by counting the readings first.** There are **three** candidate
readings of "what does this config require", and two choices cannot separate them:

| Reading | What it answers on the fixture below |
|---|---|
| **A — the union over the conditions the sweep resolves** (the specified one) | `OPENAI_API_KEY` alone |
| **B — the union over all `choices`** | `OPENAI_API_KEY` **and** `OLLAMA_HOST_KEY` |
| **C — the requirement of the value written in `parameters`** | nothing |

The fixture: three choices; `requires_env` giving a **non-empty** requirement to all three;
`sweep.grid` selecting two of them; the Azure key **set**, the OpenAI key **unset**, and the third
choice's key **unset and never selected**. Note the deviation from `reference.md`'s own example,
which gives `ollama` an empty `[]`: copying that collapses A and B, because an unselected choice
requiring nothing produces the same answer either way. **The third choice must require something.**

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`:

```python
_UNION_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai", "ollama"],
            requires_env={
                "azure_openai": ["AZURE_TEST_KEY"],
                "openai": ["OPENAI_TEST_KEY"],
                "ollama": ["OLLAMA_TEST_KEY"],
            },
        ),
        "llm.retries": Param(int, default=2, ge=0),
    }
"""

_UNION_NAMES = ("AZURE_TEST_KEY", "OPENAI_TEST_KEY", "OLLAMA_TEST_KEY")


def _union_project(git_repo: Path, monkeypatch, *, set_names: tuple[str, ...]) -> None:
    """The decision-6 fixture: three choices, a sweep selecting two, a third whose
    variable is deliberately unset and whose requirement is deliberately NON-empty.

    `reference.md`'s own example gives `ollama` an empty `[]`; copying it here
    would collapse "union over resolved conditions" into "union over all
    choices", since an unselected choice requiring nothing answers the same
    either way.

    Every one of the three names is `delenv`-ed first and only `set_names` is
    exported, so the answer is a property of the check rather than of the machine
    the suite runs on.
    """
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    for name in set_names:
        monkeypatch.setenv(name, "value")
    templates = git_repo / "templates"
    templates.mkdir(exist_ok=True)
    (templates / "cred_assay.py").write_text(_UNION_TEMPLATE)


def test_the_union_is_over_the_conditions_the_sweep_resolves(
    git_repo: Path, write_config, monkeypatch
):
    """Reading A. B would additionally report `OLLAMA_TEST_KEY`; C would report
    nothing, `azure_openai` being the written value and its key set."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {"grid": {"llm.provider": ["azure_openai", "openai"]}},
        }
    )

    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-CRED-PARAM-MISSING"]

    assert len(found) == 1, [f.message for f in found]
    message = found[0].message
    assert found[0].path == "parameters.llm.provider"
    assert "OPENAI_TEST_KEY" in message          # reading A's answer …
    assert "OLLAMA_TEST_KEY" not in message      # … and not reading B's
    # The three facts this code's message must name and the other one cannot:
    # the parameter (via `path` above), the value, and the condition.
    assert "`openai`" in message
    assert "condition `provider=openai`" in message


def test_the_union_says_nothing_when_every_selected_value_s_key_is_set(
    git_repo: Path, write_config, monkeypatch
):
    """The honouring. The unselected `ollama`'s key stays unset throughout — so a
    check that reported over all `choices` fails here while passing the test
    above."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY", "OPENAI_TEST_KEY"))
    assert codes(
        write_config(
            {
                "experiment_type": "cred_assay",
                "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
                "sweep": {"grid": {"llm.provider": ["azure_openai", "openai"]}},
            }
        )
    ) == set()


def test_an_undeclared_parameter_falls_back_to_the_template_s_default(
    git_repo: Path, write_config, monkeypatch
):
    """A config that omits the parameter still resolves to a value — the
    template's default — and that value's credential is still required."""
    _union_project(git_repo, monkeypatch, set_names=())
    path = write_config({"experiment_type": "cred_assay", "parameters": {}})
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "AZURE_TEST_KEY" in message
    assert "the base parameters" in message      # no sweep, so no condition label


def test_a_variable_two_conditions_need_is_reported_once(
    git_repo: Path, write_config, monkeypatch
):
    """One missing value is one thing to fix. Attributed to the first condition
    that selected it, which is why the assertion below names `openai` and not the
    later duplicate."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "grid": {
                    "llm.provider": ["openai", "azure_openai"],
                    "llm.retries": [1, 2],
                }
            },
        }
    )
    c = Collector()
    validate_config(path, c)
    found = [f for f in c.findings if f.code == "E-CRED-PARAM-MISSING"]
    assert len(found) == 1, [f.message for f in found]
    assert "OPENAI_TEST_KEY" in found[0].message


def test_a_template_declaring_no_requires_env_reports_nothing(write_config, monkeypatch):
    """`generic`'s four parameters declare none, which is why the other 1957 tests
    are unaffected. Asserted rather than assumed."""
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    assert "E-CRED-PARAM-MISSING" not in codes(write_config())
```

- [ ] **Step 2: Run and see them fail.** The three reporting tests fail on an empty `found`
      / `KeyError`; the two clean ones pass already.

- [ ] **Step 3: Implement.** In `validate.py`:

```python
def _check_requires_env(doc: dict[str, Any], template: Any, c: Collector) -> None:
    """The union over the conditions the sweep actually resolves.

    That union is the entire reason a value carries its own credential
    requirement instead of a template carrying a static list: a config selecting
    Azure and OpenAI must say nothing about Ollama's key, and one selecting none
    of them must say nothing about any. `reference.md` § A credential can belong
    to a parameter value.

    A condition's value is resolved the way `runner.resolve_condition_cfg`
    resolves it — declared parameters, then each of `condition.values` whose path
    is not a **selector**, a group cell naming no parameter at all — computed
    locally rather than by importing the runner, since this needs one path's
    value rather than a whole `Config`.

    A resolved value with no key in the mapping requires nothing. `requires_env`
    is total over `choices`, so that case is exactly the values `choices` does
    not hold: `sweep.ablate.remove` sets a nullable parameter to `null`, which is
    a legal resolved value and not a choice. Reporting it here would be a second
    report of a fault `_check_sweep` already owns.

    One finding per variable, attributed to the first condition that selected it:
    one missing value is one thing to fix, whatever selected it.
    """
    spec = getattr(template, "parameter_spec", None) or {}
    wanted = {path: p for path, p in spec.items() if getattr(p, "requires_env", None)}
    if not wanted:
        return
    try:
        conditions = expand(doc)
    except Exception:
        # Guarded the same way `_condition_labels` guards its own `expand(doc)`:
        # an unexpandable sweep is `_check_sweep`'s to report, and this module
        # collects rather than raises.
        return
    declared = _flatten(doc.get("parameters"), "")
    # `dict`, so insertion order is condition order then declared-parameter
    # order — a deterministic finding order without sorting away the attribution.
    first_seen: dict[str, tuple[str, Any, str | None]] = {}
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path in condition.selectors:
                continue
            resolved[path] = value
        for path, param in wanted.items():
            if path in resolved:
                value = resolved[path]
            elif param.default is not MISSING:
                value = param.default
            else:
                continue  # required and absent — `E-PARAM-MISSING`'s finding, not this one
            try:
                needs = param.requires_env.get(value)
            except TypeError:
                continue  # an unhashable resolved value cannot key the mapping
            for variable in needs or []:
                first_seen.setdefault(variable, (path, value, condition.label))
    for variable in missing_env(first_seen):
        path, value, label = first_seen[variable]
        where = f"condition `{label}`" if label else "the base parameters"
        c.error(
            "E-CRED-PARAM-MISSING",
            f"parameters.{path}",
            f"is `{value}` in {where}, which requires `{variable}` — no value in the "
            "environment or in `.env`",
        )
```

Call it from `validate_config`, immediately after `_check_required_env(doc, template, c)`.

- [ ] **Step 4: Run and see them pass.** New tests, then the full suite.

- [ ] **Step 5: Confirm the condition label the message prints.** The assertion
      `"condition \`provider=openai\`"` is **derived, not assumed**: run
      `uv run python -c "from publishable.sweep import expand; print([c.label for c in expand({'sweep': {'grid': {'llm.provider': ['azure_openai','openai']}}})])"`
      and write the literal it prints into the test. If `sweep.label_for` renders it differently,
      **the printed value wins** — `CLAUDE.md`: derive expected values from the fixture, never from
      an assumption about it.

- [ ] **Step 6: Mutate — three.**

  **(a) Union over all `choices` instead of resolved conditions.** Replace the per-condition loop
  body's value resolution with `for value in param.requires_env:` (iterating the mapping's keys).
  `test_the_union_is_over_the_conditions_the_sweep_resolves` must FAIL on
  `"OLLAMA_TEST_KEY" not in message` — actually on `len(found) == 1`, which becomes 2.
  **Checked against the test body:** the fixture gives `ollama` a non-empty requirement and leaves
  its key unset, so readings A and B genuinely differ. **This is the mutation decision 6 sizes the
  fixture for**, and with `reference.md`'s two-annotated-choices example it would have been blind.

  **(b) Only the written value.** Delete the per-condition overlay so `resolved` is `declared`
  alone. `test_the_union_is_over_the_conditions_the_sweep_resolves` must FAIL — reading C reports
  nothing, and `len(found) == 1` becomes 0.

  **(c) Drop the default fallback.** Change `elif param.default is not MISSING:` to
  `else: continue`. `test_an_undeclared_parameter_falls_back_to_the_template_s_default` must FAIL
  with `KeyError: 'E-CRED-PARAM-MISSING'`.

  Revert each by editing back; delete `__pycache__`; re-run.

- [ ] **Step 7: Which deliverable no mutation reaches, and one honest attempt.** The
      **`condition.selectors` skip** is not reachable by any mutation the fixtures above support:
      `wanted` is keyed on `parameter_spec` paths, and a group axis's path names no parameter, so
      deleting the skip changes nothing observable. **Attempt one fixture before accepting this** —
      a `sweep.groups` axis named exactly `llm.provider`, i.e.
      `{"sweep": {"groups": {"llm.provider": ["ollama"]}}}` — and see whether `validate` accepts the
      config. If it does, the skip is pinned (without it the union would read `ollama`'s
      requirement; with it, the base value's) and the fixture belongs in **task 11**, which owns
      the `groups` mode. **If `validate` refuses the config for an unrelated reason, record the
      code it refused with and accept the skip as unpinned**, on the grounds that it mirrors
      `resolve_condition_cfg`'s own documented rule rather than inventing one. Say which of the two
      happened in the task report; do not leave it undetermined.

  Also unpinned: the `except TypeError` guard around `.get(value)`. No fixture here declares a
  `list`-typed parameter with `requires_env`, and `Param` does not forbid it. Named and left.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: the requires_env union over the conditions the sweep resolves`

---

## Task 11: The expansion modes the union must cover

**Files:** Modify `tests/test_validate.py`. Modify `src/publishable/validate.py` **only if a mode
turns out to be wrong** — this task's first job is to find out.

**Interfaces:**
- Consumes: `_check_requires_env` from task 10; `_UNION_TEMPLATE`, `_UNION_NAMES` and
  `_union_project` from task 10's additions to `tests/test_validate.py`;
  `sweep.NON_PRODUCT_MODES = ("baseline", "ablate")` and
  `sweep.removal_value(baseline: Mapping[str, Any], path: str) -> Any`, which returns `False` for a
  path the baseline fixes to a bool and `None` otherwise — read from `src/publishable/sweep.py`.
- Produces: no new interface. Four fixtures, one per mode the scoping's § 5 finding 3 names, plus
  the `ablate.remove` case the charter has no task for.

**Why these four and not the grid alone.** `NON_PRODUCT_MODES` means a `baseline` is a **resolved
condition**, not a description of one — so a baseline fixing `llm.provider` contributes its
credential to the union. `paired` couples two paths in one cell. `groups` contributes a **selector**
and therefore no parameter value at all, so a groups-only sweep's union is the base value's
requirement — a case that reads as a gap and is the correct answer. And `ablate.remove` against a
nullable parameter with `choices` resolves to `null`, which is a **legal resolved value with no key
in the mapping**: the union must skip it silently rather than treat it as an unknown key.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_validate.py`. Note the second
      template constant — `_UNION_TEMPLATE`'s `llm.provider` is not nullable, and `ablate.remove`
      needs a nullable target:

```python
_ABLATABLE_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            nullable=True,
            choices=["azure_openai", "openai", "ollama"],
            requires_env={
                "azure_openai": ["AZURE_TEST_KEY"],
                "openai": ["OPENAI_TEST_KEY"],
                "ollama": ["OLLAMA_TEST_KEY"],
            },
        ),
        "llm.retries": Param(int, default=2, ge=0),
    }
"""


def test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union(
    git_repo: Path, write_config, monkeypatch
):
    """`sweep.NON_PRODUCT_MODES` is `("baseline", "ablate")` — a baseline is not a
    description of a condition, it IS one, so the value it fixes is resolved and
    its credential is required. No fixture for this existed anywhere in the
    evidence base."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "baseline": {"llm.provider": "openai"},
                "grid": {"llm.retries": [1, 2]},
            },
        }
    )
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "OPENAI_TEST_KEY" in message
    assert "OLLAMA_TEST_KEY" not in message


def test_a_paired_cell_resolves_both_of_its_paths(git_repo: Path, write_config, monkeypatch):
    """A `paired` entry couples two paths into one cell — the shape the
    feasibility analysis describes in prose for its Ollama case and shows in no
    YAML (`sweep.paired` is `[]` in both configs that have the key)."""
    _union_project(git_repo, monkeypatch, set_names=("AZURE_TEST_KEY",))
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "paired": [
                    {"llm.provider": "azure_openai", "llm.retries": 1},
                    {"llm.provider": "ollama", "llm.retries": 4},
                ]
            },
        }
    )
    message = messages_by_code(path)["E-CRED-PARAM-MISSING"]
    assert "OLLAMA_TEST_KEY" in message
    # Azure's key IS set, so the union reports one variable and not two — the
    # positive companion that keeps this from being an absence-only control.
    assert "AZURE_TEST_KEY" not in message


def test_a_groups_axis_contributes_no_parameter_value(
    git_repo: Path, tmp_path: Path, write_config, monkeypatch
):
    """A group level is a *set of units*, so it names no parameter and the union
    over a groups-only sweep is the base value's requirement — which is the
    correct answer rather than a gap.

    The roster is rewritten first: the `write_config` fixture writes
    `patient_id\\np1\\n` and nothing else, so `attributes: ["cohort"]` over that
    file earns `E-UNITS-ATTR-MISSING` and this test would pass for the wrong
    reason. `tmp_path / "input" / "index.csv"` is the file that fixture writes.
    """
    _union_project(git_repo, monkeypatch, set_names=())
    (tmp_path / "input" / "index.csv").write_text(
        "patient_id,cohort\np1,derivation\np2,derivation\np3,validation\np4,validation\n"
    )
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {"groups": {"cohort": ["derivation", "validation"]}},
            "data.units": {
                "from": "index.csv",
                "key": "patient_id",
                "attributes": ["cohort"],
            },
        }
    )
    found = [
        f for f in _findings_of(path) if f.code == "E-CRED-PARAM-MISSING"
    ]
    assert len(found) == 1, [f.message for f in found]
    assert "AZURE_TEST_KEY" in found[0].message   # the base value's, in both cells
    assert "OPENAI_TEST_KEY" not in found[0].message


def test_ablate_remove_resolves_a_value_with_no_key_and_requires_nothing(
    git_repo: Path, write_config, monkeypatch
):
    """`sweep.removal_value` sets a nullable parameter to `null`. `requires_env` is
    total over `choices`, and `null` is not a choice — so the ablated condition
    requires nothing, silently. Reporting it would be a second report of a fault
    `_check_sweep` owns.

    The control is on the same document: the BASELINE condition still resolves
    `openai` and still reports, so this test cannot pass by the check never
    running.
    """
    for name in _UNION_NAMES:
        monkeypatch.delenv(name, raising=False)
    templates = git_repo / "templates"
    templates.mkdir(exist_ok=True)
    (templates / "cred_assay.py").write_text(_ABLATABLE_TEMPLATE)
    path = write_config(
        {
            "experiment_type": "cred_assay",
            "parameters": {"llm": {"provider": "azure_openai", "retries": 2}},
            "sweep": {
                "baseline": {"llm.provider": "openai"},
                "ablate": [{"remove": ["llm.provider"]}],
            },
        }
    )
    found = [f for f in _findings_of(path) if f.code == "E-CRED-PARAM-MISSING"]
    assert len(found) == 1, [f.message for f in found]
    assert "OPENAI_TEST_KEY" in found[0].message   # the baseline's, and only it
```

and one helper — **`_findings_of` is a new name; `tests/test_validate.py`'s module level already
holds `base_config`, `write_config`, `write_config_nondet`, `write_config_broken`,
`write_config_exits`, `_DELETE`, `codes`, `messages_by_code`, `_validate_with`, `_error_codes` and
the `_*_TEMPLATE`/`_*_EXPERIMENT` constants, none of which is `_findings_of`**:

```python
def _findings_of(path: Path) -> list:
    """Every finding, not just its code or its message — the shape a test needs
    when it must count findings of one code rather than test membership."""
    c = Collector()
    validate_config(path, c)
    return list(c.findings)
```

- [ ] **Step 2: Run each test and record what it does.** **Expect some of these to pass
      immediately** — task 10's implementation is written to handle all four — and treat that as the
      measurement this task exists to take, not as a reason to skip it. For any that **fails**,
      diagnose before changing anything: `sweep.expand`'s output for that document is the ground
      truth. Run
      `uv run python -c "from publishable.sweep import expand; import yaml; print(expand(yaml.safe_load(open('<path>').read())))"`
      and read the `Condition` list. Only then change `validate.py`, and record the change in the
      task report as a real disagreement found.

- [ ] **Step 3: Check each config actually validates for the reason you think.** Every one of these
      documents can earn unrelated findings — a `groups` axis needs `data.units.attributes`, an
      `ablate` needs a `baseline`, a `paired` entry's values must be nameable. **Print
      `codes(path)` for each fixture once and read the whole set** before believing any assertion
      about `E-CRED-PARAM-MISSING`. `CLAUDE.md`: a refusal that happens to fire must be
      attributed before it is counted. If a fixture earns an unrelated error, fix the fixture — do
      not weaken the assertion.

- [ ] **Step 4: Mutate — one, chosen because the obvious one is blind.**

  **The obvious mutation is deleting the `if path in condition.selectors: continue` guard, and it
  cannot discriminate** — `wanted` is keyed on `parameter_spec` paths and a group axis's name is
  not one, so the mutant behaves identically on every fixture above. Do not use it. (Task 10 step 7
  prescribes the one experiment that could change this answer; if it succeeded, use that fixture
  here instead and say so.)

  **Use instead: resolve only the first condition.** Change `for condition in conditions:` to
  `for condition in conditions[:1]:`. **`test_a_baseline_is_a_resolved_condition_whose_credential_joins_the_union`
  must FAIL**? Check first: `expand` emits the baseline's rows **first**, so a baseline fixture's
  requiring condition *is* condition 0 and this mutation would be blind on it.
  **`test_a_paired_cell_resolves_both_of_its_paths` is the one that must FAIL** — its two `paired`
  entries are conditions 0 and 1, and the requiring one (`ollama`) is **second**, so truncating to
  the first leaves `OLLAMA_TEST_KEY` unreported and the `messages_by_code(path)[...]` lookup raises
  `KeyError`. **Name that test in the brief and verify the ordering by printing
  `[c.values for c in expand(doc)]` before trusting it.**

  A second, on the same principle: **replace `first_seen.setdefault` with `first_seen[…] = …`**.
  `test_a_variable_two_conditions_need_is_reported_once` (task 10's) must still pass — it counts
  findings, not attributions — but the *attribution* changes, so add the assertion that pins it if
  it is not already pinned: in the paired fixture, assert the message names `` `ollama` `` rather
  than a later condition's value. If no fixture can distinguish first-wins from last-wins, **say so
  and drop this second mutation** rather than defending it.

  Revert by editing back; delete `__pycache__`; re-run.

- [ ] **Step 5: Which deliverable no mutation reaches.** The **`ablate.remove` silence** is proved
      by a test whose positive companion is the baseline's own finding on the same document, so it
      is not an absence-only control — but **no mutation makes it go red**, because the behaviour is
      "does nothing" and every plausible mutant that reports would break the count assertion, which
      is the mutation. State it as covered-by-count rather than covered-by-mutation, and if
      `.get(value)` on an absent key ever stops returning `None`, the count assertion is what
      catches it.

- [ ] **Step 6: Verify and commit.** All four commands.
      `test: the union over baseline, paired, groups, and ablate.remove`

---

## Task 12: The no-leak test, the redaction, and decision 4a's boundary

**Files:** Modify `src/publishable/diagnostics.py`, `src/publishable/runner.py`,
`src/publishable/cli.py`, `src/publishable/validate.py`, `tests/test_cli.py`, `docs/reference.md`.

**Interfaces:**
- Consumes: `redact(text: str | None, values: Mapping[str, str]) -> str | None` and
  `credential_values(names: Iterable[str]) -> dict[str, str]` from task 7;
  `runner.execute_plan(*, plan, run_dir, input_dir, cfgs, repeats, digest, units=None,
  max_failed_fraction=None, fold_members=None, arm_members=None, holdout_train=None,
  measurements=None) -> list[ExecutionResult]` — read from `src/publishable/runner.py`;
  `ExecutionResult.error: str | None`; `Collector` — a `@dataclass` in
  `src/publishable/diagnostics.py` whose only field is `findings: list[Diagnostic]`, with
  `error`/`warn`/`has_errors`/`exit_code`/`render` and **no other state**.
- Produces: `execute_plan(..., credentials: dict[str, str] | None = None)`; a redacted step `error`
  string; `Collector.credentials: dict[str, str]` and a `render()` that redacts every message
  through it.

**Where the redaction goes — spec correction 1, and it supersedes an earlier reading of decision 3.**
Decision 3 says "redact by exact value at the two record-writing sites". An earlier draft of this
task located those sites by `grep -rn "\.error\b" src/publishable/*.py`, concluded there was **one**
exception-text construction, and was **wrong**: that grep finds assignments to an `.error`
*attribute*, not constructions of exception text. The correct measurement is

```
$ grep -rn 'type(exc).__name__' src/publishable/*.py
runner.py:688     the step-error text
cli.py:1937       W-STATS-AGGREGATE-FAILED — a template's `aggregate` raised
cli.py:2022       W-STATS-AGGREGATE-FAILED — the resample retry raised
cli.py:2369       W-STATS-AGGREGATE-FAILED — a `report_by` stratum's compute raised
validate.py:566   E-ENTRYPOINT-IMPORT — the user package raised at import
```

**Five constructions, not one.** The four beyond `runner.py` carry a *template's* or a *user
package's* exception, and none of them reaches `run.yaml` — `run_record.py` has no diagnostics
channel, and `cli.py`'s own comment at the `aggregate_c` print says so. **But this task's leak sweep
covers stdout and stderr**, so all four are leaks by this slice's own definition.

**The ruling: redact at the two serialization boundaries, not at any construction site.**

| Boundary | Covers |
|---|---|
| `Collector.render()` in `src/publishable/diagnostics.py` — the one method every diagnostic's text passes through on its way to stdout or stderr, called from **seven** sites in `cli.py` | `cli.py:1937`, `cli.py:2022`, `cli.py:2369`, `validate.py:566`, and every diagnostic minted after them |
| The step-error path in `runner.execute_plan` | `runner.py:688`, and through it both `executions.jsonl` and `run.yaml` |

Two edits cover all five and cannot diverge as a sixth construction is added; five edits at
construction are five places for the next one to be forgotten. Same argument that put
`holdout_values_fault` behind one authority in H3d.

**Read `diagnostics.py` before writing the edit — `render()` is on `Collector`, not on
`Diagnostic`.** `Diagnostic` is a frozen four-field dataclass (`level`, `code`, `path`, `message`)
with no methods at all; `Collector` holds `findings` and does the rendering. Redacting per-`Diagnostic`
would need the values at construction, which is exactly what this ruling avoids.

**Decision 4a is a document-only deliverable and it belongs here**, not between tasks 8 and 12:
core redacts only values it read for a **declared** variable, and a step that reaches
`os.environ` for a name no `required_env` or `requires_env` declares holds a value core never saw
and cannot match. Saying so is the difference between a guarantee and an overreaching claim in the
one document whose job is to prevent them.

**The scoping's stated mutation is not one.** It says "the mutation: a step that raises with the
sentinel in its exception text". That is the **fixture** — changing the test's own step source
cannot fail the unmutated test, because it *is* the test. Writing it as the mutation would ship the
fifth blind mutation in three slices, in the slice whose stated purpose is replacing a test that
cannot fail. The mutation is **deleting the redaction call**.

- [ ] **Step 1: Write the failing tests.** Append to `tests/test_cli.py`. `_LEAKY_STEP` and
      `_SENTINEL` are free names in that module:

```python
_SENTINEL = "sk-h7c-sentinel-9f3a1c"

_LEAKY_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        # A client library interpolating a key into a URL in its error message is
        # ordinary, and this is the one surface on which that value can reach a
        # record: `runner` writes a failed execution's exception text into both
        # `executions.jsonl` and `run.yaml`.
        raise RuntimeError("POST https://api.example/v1?key=" + token + " returned 401")
"""

_SECRET_USING_STEP = """\
# src/{pkg}/steps/step01_summarize_units.py — generated, and runnable as-is
import os

from publishable import BaseStep


class Step(BaseStep):
    scope = "repeat"

    def run(self, cfg, io):
        token = os.environ["PUBLISHABLE_TEST_TOKEN"]
        for unit in io.units:
            io.record(unit.key, {{"present": True}})
        return {{"token_len": len(token)}}
"""


def _files_under(results_dir):
    """Every file a run wrote, as a list of paths — the FILE LIST is what gets
    filtered, never the sweep's output. Filtering the output of a search for a
    string is how this repo lost a true hit once already.

    Globbed rather than enumerated: `allocation.json` exists only under an
    assignment or a holdout, and a fixture that declares neither would make a
    named-file assertion vacuous or wrong.
    """
    return [p for p in sorted(results_dir.rglob("*")) if p.is_file()]


def test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so(
    tmp_path, monkeypatch, capsys
):
    """The one accident this slice must survive: a step whose exception text
    carries the value core read.

    Three assertions, and the first is the one that makes the other two mean
    something — a sweep for absence passes identically if nothing ran.
    """
    import publishable.generators.experiment as experiment_gen

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _LEAKY_STEP)
    monkeypatch.setattr(
        "publishable.templates.builtin.generic.GenericTemplate.required_env",
        ["PUBLISHABLE_TEST_TOKEN"],
    )

    doc = run_a_project(
        tmp_path,
        units=4,
        _env_file=f"PUBLISHABLE_TEST_TOKEN={_SENTINEL}\n",
        expect_exit=EXIT_PARTIAL,
        capsys=capsys,
    )
    run_dir = doc["run_dir"]
    run = yaml.safe_load((run_dir / "run.yaml").read_text())

    # 1. SOMETHING THAT MUST REPORT. The execution failed, its error was recorded,
    #    and the redaction announced itself by naming the variable.
    ledger = [
        json.loads(line)
        for line in (run_dir / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = [e["error"] for e in ledger if e["error"]]
    assert errors, "no execution failed — the sweep below would be vacuous"
    assert all("<redacted:PUBLISHABLE_TEST_TOKEN>" in e for e in errors), errors
    # The surrounding text SURVIVES: scrubbing the whole message destroys the
    # debugging the record exists for.
    assert all("RuntimeError" in e and "returned 401" in e for e in errors), errors

    # 2. The same, as `run.yaml` arranges it — a second surface, not a rephrasing
    #    of the first.
    recorded = json.dumps(run)
    assert "<redacted:PUBLISHABLE_TEST_TOKEN>" in recorded

    # 3. The sweep. The FILE LIST is filtered, never the output.
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
    # stdout/stderr, captured by the helper because `capsys` was passed.
    assert _SENTINEL not in (doc["stdout"] or "")
    assert _SENTINEL not in (doc["stderr"] or "")


def test_a_step_reads_its_credential_and_the_value_still_reaches_no_artifact(
    tmp_path, monkeypatch, capsys
):
    """The success path, with something that must report: the step got the real
    value and returned its length. Without this, the sweep above proves only that
    a *failed* run leaks nothing."""
    import publishable.generators.experiment as experiment_gen

    monkeypatch.delenv("PUBLISHABLE_TEST_TOKEN", raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _SECRET_USING_STEP)
    monkeypatch.setattr(
        "publishable.templates.builtin.generic.GenericTemplate.required_env",
        ["PUBLISHABLE_TEST_TOKEN"],
    )

    doc = run_a_project(
        tmp_path, units=4, _env_file=f"PUBLISHABLE_TEST_TOKEN={_SENTINEL}\n", capsys=capsys
    )
    run = yaml.safe_load((doc["run_dir"] / "run.yaml").read_text())
    # Pin ONE spelling, derived from the document rather than guessed: print
    # `run["results"]` once for this fixture, find where `token_len` lands, and
    # write that access path here. An `or` between two candidate spellings passes
    # if either happens to hold and proves nothing about which.
    assert json.dumps(run).count(f'"token_len": {len(_SENTINEL)}') >= 1, run["results"]
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
    assert _SENTINEL not in (doc["stdout"] or "")
    assert _SENTINEL not in (doc["stderr"] or "")
```

**Three fixture facts to check before running, not after.** (i) `run_a_project`'s docstring says a
step whose `run` raises is *contained* — that execution lands `status: "failed"`, the rest of the
plan runs, `run_status` turns it into `partial` and so `EXIT_PARTIAL`; that is why the first test
passes `expect_exit=EXIT_PARTIAL` and the second does not. (ii) `_env_file` is task 8's addition to
`run_a_project`. (iii) **Do not assert on `allocation.json`** — it exists only under an assignment
or a holdout and this fixture declares neither. `_files_under` globs, which is the correct way to
say "every artifact".

- [ ] **Step 2: Run and see them fail.** The first fails on
      `"<redacted:PUBLISHABLE_TEST_TOKEN>" in e` and again on the sweep, with the sentinel present
      in `executions.jsonl` and `run.yaml`. The second should already pass **only if task 8 landed**
      — if it fails on `KeyError: 'PUBLISHABLE_TEST_TOKEN'`, the run-side load is missing.

- [ ] **Step 3a: Implement the `Collector.render()` boundary.** In
      `src/publishable/diagnostics.py` — which today imports only `dataclasses`, so
      `from publishable.secrets import redact` is acyclic (`secrets.py` imports `os`, `pathlib` and
      `dotenv` and nothing from this package). Add a field to `Collector` and redact in `render()`:

```python
@dataclass
class Collector:
    """`validate` collects rather than stops, so findings are appended, never raised."""

    findings: list[Diagnostic] = field(default_factory=list)
    credentials: dict[str, str] = field(default_factory=dict)
    """The credential values core read for a DECLARED variable, if any were.

    Set by whoever knows them — `validate_config`, which resolves the same two
    declarations it checks, and `command_run` for the collectors it builds after
    it. Redaction happens at `render`, the one place a finding's text becomes
    output, rather than at each of the five sites that build an exception string:
    a diagnostic carrying a template's or a user package's exception is minted in
    four places and a sixth is one commit away. `Diagnostic` stays a plain frozen
    record so a message is never rewritten before the collector that owns it
    decides to print.

    Empty is the default and the honest one: a collector nobody gave values to
    redacts nothing, because there is nothing it was told to look for.
    """
```

and, in `render()`, replace the message line:

```python
        for f in self.findings:
            lines.append(f"  {f.level:<7} {f.code:<20} {f.path}")
            # `or f.message` narrows `str | None` to `str` for the type checker;
            # `redact` returns its argument unchanged when there is nothing to do.
            lines.append(f"          {redact(f.message, self.credentials) or f.message}")
```

Then wire the two owners:

- In `validate.py`'s `validate_config`, immediately after `_check_requires_env(doc, template, c)`
  (task 10's call), set `c.credentials = credential_values(declared_credential_names_for(doc,
  template))` — **or**, if that would duplicate the collector task 12 step 3b writes into `cli.py`,
  hoist a single shared helper. **Decide by reading**: if `cli.declared_credential_names` and the
  validate-side collector would be the same function, put it in one module and import it, and say
  in the commit message which. Do not ship two.
- In `cli.py`'s `command_run`, after `credentials` is built (step 3b), set
  `aggregate_c.credentials = credentials` where `aggregate_c = Collector()` is constructed, and do
  the same for any other `Collector` built **after** that point whose `render()` can carry a
  user-supplied exception. **Enumerate them by reading**, not from this brief:
  `grep -n "\.render()" src/publishable/*.py` returns seven sites; decide for each whether its
  collector's messages are core-authored (a dirty tree, a manifest drift) or can carry foreign text.
  Setting it on all of them is harmless and is the safer default.

- [ ] **Step 3b: Implement the step-error boundary.** In `src/publishable/runner.py`:

Add `from publishable.secrets import redact` to the import block, add the parameter to
`execute_plan`'s keyword-only signature after `measurements`:

```python
    credentials: dict[str, str] | None = None,
```

document it in `execute_plan`'s docstring in the same register as its neighbours:

```
    `credentials` is `{variable: value}` for every credential core read for a
    *declared* variable — `required_env` and the `requires_env` union. A failed
    execution's exception text is the one surface on which such a value can enter
    a record, so each is replaced there by a marker naming its variable. By exact
    value, never by pattern: core knows what it read, and a pattern check fails
    open on a credential named `instrument_pw` and fails closed on a config value
    that happens to look random. A value a step read from `os.environ` for a name
    nothing declared is outside what core saw and is not matched — see
    `docs/reference.md` § Secrets & credentials.
```

and redact inside `except Exception`, where the step-error text is built:

```python
        except Exception as exc:  # a failed execution never stops the run
            code = getattr(exc, "code", None)
            prefix = f"{code} " if code else ""
            # Redacted where this string is BUILT rather than at each writer:
            # both records — `run.yaml` through `run_record` and
            # `executions.jsonl` below — read from it, so one edit covers both
            # and they cannot diverge. The *other* four places core interpolates
            # an exception are diagnostics, and `Collector.render` covers all of
            # them at once (`docs/reference.md` § Secrets & credentials).
            returned, status = {}, "failed"
            error = redact(f"{prefix}{type(exc).__name__}: {exc}", credentials or {})
```

In `src/publishable/cli.py`'s `command_run`, build the mapping and pass it. **Read these three facts
about that function before writing a line** — the first is a name that does not exist where you would
reach for it, and reaching for it wrongly disables this task's headline deliverable for exactly the
templates it exists to serve:

1. **There is no `template` local in scope before `execute_plan`.** `command_run` binds `template`
   exactly once, at its `get_template(doc.get("experiment_type", ""), repo_root)` call **inside the
   `if roster is not None:` block that runs *after* `execute_plan`**. You must resolve the template
   yourself, earlier.
2. **`get_template(name: str, repo_root: Path | None = None) -> BaseTemplate | None` resolves a
   project-local `templates/*.py` only when `repo_root` is passed** — it goes through
   `registry._merged(repo_root)`, which calls `discover_local`. **Calling it without `repo_root`
   returns `None` for every local template**, `declared_credential_names` then returns `[]`,
   `credentials` is empty, and `redact` becomes a silent no-op for the case this slice exists for.
   Pass `repo_root`. It is already a local by then.
3. **`conditions = expand(doc)` is already a local**, bound before `execute_plan`. Take it as an
   argument rather than expanding a second time — a second `expand` is a second derivation that can
   drift from the one the run actually executes.

Add, immediately after the existing `conditions = expand(doc)` line and before `execute_plan(`:

```python
    # Resolved here rather than read off the later `get_template` call, which is
    # bound after `execute_plan` and inside a roster guard. `repo_root` is passed
    # because without it `registry._merged` never runs `discover_local`, and every
    # project-local template resolves to `None` — which would empty `credentials`
    # and silently turn the redaction below into a no-op for exactly the templates
    # this check is for. Cannot raise: `validate_config` already made the same
    # call and returned without error, or `command_run` returned above.
    run_template = get_template(doc.get("experiment_type", ""), repo_root)
    # Every credential core read for a DECLARED variable — the template's own
    # `required_env`, plus the union its parameters' `requires_env` resolves to.
    # Held for this command only and written nowhere; its single consumer is the
    # redaction in `execute_plan`.
    credentials = credential_values(declared_credential_names(doc, run_template, conditions))
```

Named `run_template`, not `template`, so it cannot be confused with — or accidentally merged into —
the later binding, which this task leaves alone. That later call re-runs local discovery a second
time; the redundancy is pre-existing (`validate_config` already discovered once) and consolidating it
is **out of scope here**.

Add the collector beside `_wide_swept_paths` in `cli.py`:

```python
def declared_credential_names(
    doc: dict[str, Any], template: Any, conditions: "list[Condition]"
) -> list[str]:
    """Every environment variable this config's declarations name.

    The same two collectors `validate` checks — the template's `required_env` and
    the `requires_env` of every value a resolved condition selects — read here for
    their *values* rather than for their presence. Deliberately the same set: core
    redacts exactly what it was told to look for, which is what makes the answer a
    fact rather than a guess.

    Takes the already-expanded `conditions` rather than expanding again, so the
    set core redacts is derived from the same condition list the run executes.

    A `None` template yields the empty list, which is the honest answer for a name
    that resolves to nothing — but it is also indistinguishable from a template
    declaring no credentials, so the caller's job is to pass a template that was
    resolved WITH `repo_root`.
    """
    names: list[str] = list(getattr(template, "required_env", None) or [])
    spec = getattr(template, "parameter_spec", None) or {}
    declared = _flatten_parameters(doc.get("parameters"))
    for condition in conditions:
        resolved = dict(declared)
        for path, value in condition.values.items():
            if path not in condition.selectors:
                resolved[path] = value
        for path, param in spec.items():
            mapping = getattr(param, "requires_env", None)
            if not mapping:
                continue
            value = resolved.get(path, param.default)
            try:
                names.extend(mapping.get(value) or [])
            except TypeError:
                continue
    return names
```

**`_flatten_parameters` does not exist in `cli.py`** — confirm with
`grep -n "_flatten" src/publishable/cli.py` before naming it. Do **not** import `validate._flatten`,
which is private to that module; write the four-line flatten locally and say in its docstring that it
mirrors `validate._flatten` for one caller rather than reaching across a module boundary for a
private name.

**`Condition` is already imported into `cli.py` under `TYPE_CHECKING`** — `if TYPE_CHECKING:` holds
`from publishable.sweep import Condition` beside `Comparison` and `ExecutionResult`, and
`_baseline_comparisons` and `_declared_comparisons` both annotate it as the quoted
`"list[Condition]"`. **Quote the annotation the same way; do not add a runtime import.** `expand` is
already in `cli.py`'s `from publishable.sweep import (...)` block and `get_template` is already
imported from `publishable.templates.registry`. **Confirm all three before writing, and add only
`credential_values`/`redact` — which are genuinely missing.**

Finally pass it at the call: add `credentials=credentials,` to the `execute_plan(` keyword list.

- [ ] **Step 4: Run and see them pass.** Both new tests, then the full suite.

- [ ] **Step 4b: The `Collector.render()` boundary needs its own fixture — the step-error path does
      not reach it.** Both tests in step 1 go through `runner.py`'s construction. If step 3a were
      reverted wholesale they would stay green, and the second boundary would be pinned by
      **nothing** — the shape that shipped a headline deliverable unpinned last slice.

      **Reachability, verified rather than assumed.** `cli.py:1937` sits in the per-condition,
      per-recording-step loop that calls `template.aggregate(...)`; the template comes from the
      `get_template(..., repo_root)` call, so a **project-local** template's `aggregate` is the one
      invoked. `tests/test_cli.py` already has three tests asserting `"W-STATS-AGGREGATE-FAILED" in
      doc["stdout"]` (one of them patches `GenericTemplate.aggregate` to return a value whose
      resample fails), so the construction, the collector, the `print(aggregate_c.render())`, and
      `capsys` reaching `doc["stdout"]` are all live today. An `aggregate` that **raises** lands on
      `cli.py:1937` directly. Confirm this by running the test and reading the captured stdout
      before trusting the assertion.

      This test reuses task 12 step 7's `_local_template` keyword and the same project shape, so
      write it **after** step 7's helper lands or write step 7 first — the two are one fixture family
      and the order between them is free.

```python
_AGGREGATE_LEAKING_TEMPLATE = """\
import os

from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_AZURE"]
    parameter_spec = {}

    def aggregate(self, units, cfg):
        # A template's own exception reaches stdout through
        # `W-STATS-AGGREGATE-FAILED`, never through `run.yaml` — `run_record`
        # has no diagnostics channel. So this is a leak the step-error path
        # cannot see and the render boundary must catch.
        raise RuntimeError("upstream rejected key " + os.environ["PUBLISHABLE_TEST_AZURE"])
"""


def test_a_template_exception_printed_as_a_warning_is_redacted_too(tmp_path, monkeypatch, capsys):
    """The second serialization boundary, `Collector.render()`.

    `aggregate` raising is one of five places core builds a
    `f"...{type(exc).__name__}: {exc}"` string, and four of them are diagnostics
    rather than records. This one reaches stdout and nothing else, so the step
    tests above are blind to it — reverting `diagnostics.py` alone leaves all of
    them green and this one red, which is the whole reason it exists.
    """
    monkeypatch.delenv("PUBLISHABLE_TEST_AZURE", raising=False)

    doc = run_a_project(
        tmp_path,
        units=4,
        experiment_type="cred_assay",
        _local_template=_AGGREGATE_LEAKING_TEMPLATE,
        _env_file=f"PUBLISHABLE_TEST_AZURE={_SENTINEL}\n",
        capsys=capsys,
    )
    out = doc["stdout"] or ""
    # SOMETHING THAT MUST REPORT: the warning fired, and it announced the
    # redaction by naming the variable. Without the first assertion the two
    # below pass identically on a build where `aggregate` was never called.
    assert "W-STATS-AGGREGATE-FAILED" in out, out
    assert "<redacted:PUBLISHABLE_TEST_AZURE>" in out, out
    # The surrounding text survives — the warning is still diagnosable.
    assert "upstream rejected key" in out, out
    # And the value is nowhere: stdout, stderr, and every artifact.
    assert _SENTINEL not in out
    assert _SENTINEL not in (doc["stderr"] or "")
    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
```

      **Check before believing it:** the run must reach `EXIT_OK` (an `aggregate` that raises is
      contained — `cli.py`'s own comment says the warning is emitted "alone", without setting
      `status = "failed"`), and the scaffolded step must actually record a column, or `aggregate` is
      never called for any step and the first assertion fails. `run_a_project`'s default
      `STARTER_STEP` calls `io.record`, so it does — confirm by reading the captured stdout.

- [ ] **Step 5: Document decision 3 and decision 4a.** In `reference.md` § Secrets & credentials,
      after the sentence about `report` and `diff` being safe to send as-is, add:

```
**An exception's text can carry a value by accident, and it is refused rather than tolerated.** A client library that interpolates a key into a URL in its error message is ordinary, and core turns an exception into text a reader sees in two places: a failed execution's `error`, written into both `run.yaml` and `executions.jsonl`, and a [diagnostic](#exit-codes-and-diagnostics) printed to stdout or stderr — which is how a template's `aggregate` failure and an entrypoint that raises at import reach you. Core replaces each credential value it read with `<redacted:VARIABLE_NAME>` at both, and leaves the rest of the message intact, because the record exists to be debugged from — and it says a redaction happened rather than scrubbing silently, so a reader knows both what was removed and which variable to look at. The match is by **exact value, never by pattern**: core knows what it read out of the environment, so it answers the direct question instead of guessing from a name ending `_KEY` or from how random a string looks.

**The limit of that, stated rather than discovered.** Core redacts only values it read for a **declared** variable — one named in a template's `required_env`, or in the `requires_env` of a value a condition resolves. `io` hands a step no credential, so a step that reaches `os.environ` for a name no declaration mentions holds a value core never saw and cannot match. Declare it, and it is covered; don't, and the redaction is not a guarantee the code can provide.
```

Then run the mechanical pass over § Secrets & credentials.

- [ ] **Step 6: Mutate — one per boundary, plus one named as blind.** The pair is the point: each
      mutation must redden **its own** boundary's tests and leave the other boundary's **green**.
      Two boundaries that both went red under one mutation would mean one of them is doing nothing.

  **(a) Remove the step-error boundary.** In `runner.py`, change the `error = redact(...)` line back
  to `error = f"{prefix}{type(exc).__name__}: {exc}"`.
  `test_a_credential_value_reaches_no_artifact_and_the_redaction_says_so` must FAIL — on the
  `"<redacted:…>" in e` assertion first, and again on the file sweep — and so must step 7's
  `test_a_project_local_template_s_credentials_are_redacted_too`. **Checked against the test bodies:**
  each fixture's step raises with the sentinel in its message and passes
  `expect_exit=EXIT_PARTIAL`, which guarantees the run reaches the ledger, so the two branches
  genuinely differ. **Step 4b's `test_a_template_exception_printed_as_a_warning_is_redacted_too`
  must stay GREEN** — its sentinel never touches `ExecutionResult.error` at all. Confirm both halves.

  **(b) Remove the `Collector.render()` boundary — the retargeted 12b.** In `diagnostics.py`, change
  `render()`'s message line back to `lines.append(f"          {f.message}")`, leaving the
  `credentials` field in place so the mutation is one line.
  **`test_a_template_exception_printed_as_a_warning_is_redacted_too` must FAIL**, on
  `"<redacted:PUBLISHABLE_TEST_AZURE>" in out` and again on `_SENTINEL not in out`.
  **Checked against that test's body:** its sentinel reaches output *only* through
  `W-STATS-AGGREGATE-FAILED` → `aggregate_c.render()` → `print(...)` → `capsys` → `doc["stdout"]`,
  and the test asserts on `doc["stdout"]`, so the mutated and unmutated branches produce different
  strings. **Both step-1 tests and step 7's must stay GREEN** — `runner.py` still redacts, and their
  assertions are over `executions.jsonl`, `run.yaml` and the artifact sweep.

  This replaces an earlier mutation ("move the redaction into `run_record._execution_block`") which
  rested on the false premise that there was one construction site. Its *intent* — proving the test
  can see a boundary that was skipped — is what (b) now does, against a boundary that genuinely
  exists.

  **(c) Redact by pattern instead of by value.** Change `redact`'s loop to replace any
  `sk-`-prefixed token. Every test above would still pass — both sentinels start with `sk-`.
  **This mutation is BLIND and is named here so nobody proposes it as a check.** The pattern reading
  is refused in `tests/test_secrets.py`'s
  `test_redaction_replaces_the_exact_value_and_names_the_variable`, whose `sk-zzzzzz`-untouched
  assertion is the fixture that can tell by-value from by-pattern. **The property is covered there
  and needs nothing here.**

  Revert each by editing the file back in place; delete `__pycache__`; re-run; confirm green.
  **Never `git checkout --`.**

- [ ] **Step 7: The third test — a credential that arrives through a project-local template.**
      **Not optional, and not an accepted gap.** Both tests above patch `GenericTemplate`, a *core*
      template, which `get_template` resolves whether or not `repo_root` is passed. So both stay
      green under the exact wiring defect step 3 warns about: a `get_template` call missing its
      `repo_root` empties `credentials` for every project-local template and turns `redact` into a
      no-op, while every mutation above still discriminates. That is the shape this repo has shipped
      twice — a headline deliverable wired through a lookup that works for the fixture and fails open
      for the real case. The fixture must come the way a real one does.

      This also closes `declared_credential_names`'s **`requires_env` half**, which the two tests
      above do not reach at all.

      **`run_a_project` needs a second keyword, `_local_template`, and it lands in task 8 beside
      `_env_file`** — a `templates/` file must exist before `git add .` runs, or `run` refuses the
      tree as dirty (`E-CODE-DIRTY` covers `src/**` and `templates/**`). Add to task 8's signature:

```python
    _local_template: str | None = None,
```

and, in the same place `_env_file` is written (after `main(["new", str(root)])`):

```python
    if _local_template is not None:
        # Written before the commit below, because `code_hash` covers
        # `templates/**` and `run` refuses a dirty tree.
        (root / "templates").mkdir(exist_ok=True)
        (root / "templates" / "cred_assay.py").write_text(_local_template)
```

The config must then name it: pass `experiment_type="cred_assay"` through `**overrides`, which
`run_a_project` already merges onto the generated `config.yaml` as top-level keys.

Then the test:

```python
_LOCAL_CRED_TEMPLATE = """\
from publishable import BaseTemplate, Param, register_template


@register_template("cred_assay")
class CredAssay(BaseTemplate):
    naming_pattern = r"^[a-z0-9]+(-[a-z0-9]+)*$"
    required_env = ["PUBLISHABLE_TEST_TOKEN"]
    parameter_spec = {
        "llm.provider": Param(
            str,
            default="azure_openai",
            choices=["azure_openai", "openai"],
            requires_env={
                "azure_openai": ["PUBLISHABLE_TEST_AZURE"],
                "openai": ["PUBLISHABLE_TEST_OPENAI"],
            },
        )
    }
"""


def test_a_project_local_template_s_credentials_are_redacted_too(tmp_path, monkeypatch, capsys):
    """The case `get_template` answers wrongly when `repo_root` is not passed.

    Both tests above patch `GenericTemplate`, which resolves either way — so
    neither can see a `declared_credential_names` that got `None` back and
    returned `[]`. This one can: nothing here is a core template, and the value
    that must be redacted is the one `requires_env` names.
    """
    import publishable.generators.experiment as experiment_gen

    for name in ("PUBLISHABLE_TEST_TOKEN", "PUBLISHABLE_TEST_AZURE", "PUBLISHABLE_TEST_OPENAI"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(experiment_gen, "STARTER_STEP", _LEAKY_AZURE_STEP)

    doc = run_a_project(
        tmp_path,
        units=4,
        experiment_type="cred_assay",
        parameters={"llm": {"provider": "azure_openai"}},
        _local_template=_LOCAL_CRED_TEMPLATE,
        _env_file=(
            "PUBLISHABLE_TEST_TOKEN=irrelevant\n"
            f"PUBLISHABLE_TEST_AZURE={_SENTINEL}\n"
        ),
        expect_exit=EXIT_PARTIAL,
        capsys=capsys,
    )
    ledger = [
        json.loads(line)
        for line in (doc["run_dir"] / "executions.jsonl").read_text().splitlines()
        if line.strip()
    ]
    errors = [e["error"] for e in ledger if e["error"]]
    assert errors, "no execution failed — the sweep below would be vacuous"
    assert all("<redacted:PUBLISHABLE_TEST_AZURE>" in e for e in errors), errors

    swept = _files_under(doc["results_dir"])
    assert swept, "no artifacts were written — the sweep would be vacuous"
    for path in swept:
        assert _SENTINEL not in path.read_bytes().decode("utf-8", "replace"), path
```

with `_LEAKY_AZURE_STEP` a copy of `_LEAKY_STEP` reading `PUBLISHABLE_TEST_AZURE` instead. **Check
the config actually validates before believing the run**: a local template's `naming_pattern` must
accept `cohort-pilot` (declared above), and `run_a_project`'s generated config will carry a
`template_version` — confirm whether `_check_versions` skips it for a local template (it does, per
`is_local_template`) rather than assuming. If any unrelated finding appears, fix the fixture, not
the assertion.

**Mutation for this test, and it is the one that matters:** drop `repo_root` from step 3's
`get_template(doc.get("experiment_type", ""), repo_root)` call. This test must FAIL — the template
resolves to `None`, `credentials` is empty, the sentinel reaches `executions.jsonl` — while the two
`GenericTemplate` tests above stay **green**. Verify both halves of that; the green half is what
proves this test was needed.

**What remains unreached even so:** decision **4a's prose** is document-only by construction — it
describes what core *cannot* do, and there is no code to mutate. Named and accepted.

- [ ] **Step 8: Verify and commit.** All four commands.
      `feat: redact credential values at the two serialization boundaries, and state the limit`

---

## Task 13: The owned prose sweep — named files

**Files:** Modify whichever of `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md` the sweep turns up. Possibly
`src/publishable/**` and `tests/**`.

**Interfaces:** none. This task reads and repairs.

**Name the files; `*.md` no longer means the four documents.** The development record under
`docs/superpowers/` is tracked, so a glob sweeps specs, plans, scopings and ledgers — which must
**not** be retro-edited. Every sweep below names its files explicitly.

**Prove each sweep can fail.** Before trusting a sweep that returns nothing, run it against a string
known to be present in the same file list (`publishable` works everywhere; `requires_env` works in
`reference.md` and `experimental-designs.md`) and confirm it hits. **Filter the file list, never the
output** — a reviewer checking this exact rule lost a true hit to `grep -v superpowers`, because the
matching line contained that path.

The four documents, as a reusable list:

```
README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```

- [ ] **Step 1: Sweep the four documents for every claim this slice moved.**

```
grep -n "required_env\|requires_env\|python-dotenv\|dotenv\|\.env\|credential\|secret" \
  README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md
```

Read **every** hit. The ones the scoping measured and their expected disposition:

| Site | Expected after this slice |
|---|---|
| `README.md` — the "your data, and your credentials" line in the four-step pitch | Unchanged. `reproduce` is unbuilt and this slice does not touch it |
| `README.md` — "Neither data nor credentials travel" | Unchanged, and still true |
| `README.md` — the tree line `└── .env  # credentials, never committed` | Unchanged; `scaffold.py` writes it |
| `design-principles.md` — "your data and your credentials, neither of which core transmits" | Unchanged |
| `design-principles.md` — "**Secrets are the one thing never captured.**" | **Re-read against task 12.** Still true, and now *enforced* rather than held by absence. Decide whether it earns a clause pointing at the redaction; if it does not, say so |
| `design-principles.md` — the plugin-boundary row naming "the secrets mechanism (`required_env` / `requires_env` + dotenv loading)" | Unchanged, and now describes something that exists |
| `design-principles.md` — "**Not credential transfer.**" | Unchanged. Still a stated non-promise |
| `experimental-designs.md` — "**Credentials in a shared config**" | Unchanged |
| `experimental-designs.md` — "**A credential missing for one arm of a sweep**" | **Re-read against task 10.** It already describes the union correctly; confirm its link anchor still resolves |
| `reference.md` § Secrets & credentials — "`validate` confirms each is set … without printing or logging it" | **Was aspirational; is now true.** Confirm it reads as a statement of what happens, and that "the second only for the conditions a sweep actually resolves" matches task 10's behaviour exactly |
| `reference.md` § Templates — "`Param` carries … any credential a chosen value requires" | Task 5's |
| `reference.md` § Package layout — `secrets.py` | Task 7 step 8's |
| `reference.md` § The generated README — the `credentials` region | **Do not build it.** Task 14 files it |
| `reference.md` § Reproducing — step 6's `.env.example` copy and `required_env` listing | Unchanged; `reproduce` is unbuilt. Task 14 files it |
| `reference.md` § Metering — `dry-run` "needs … real credentials" | Unchanged; `dry-run` is unbuilt. Task 14 files it |

- [ ] **Step 2: Sweep `src/` and `tests/` separately, and do not stop one file short.**
      `CLAUDE.md` records three sweeps in one slice that each stopped one file short — one covered
      `src/` and `docs/` but not `tests/`.

```
grep -rn "required_env\|requires_env\|dotenv\|\.env\b" src/publishable/
grep -rn "required_env\|requires_env\|dotenv" tests/
```

Read each hit. `src/publishable/generators/template.py`'s comment says the `generate template` stub
omits `required_env` deliberately — **re-read it now that the attribute has a reader** and decide
whether it still says something true. `tests/test_templates.py`'s assertion
`assert t.required_env == []` is fine and should stay.

- [ ] **Step 3: Sweep for the false guarantees `H7c-SCOPING.md` § 9 named**, one at a time, and
      confirm each is now either true or amended:

```
grep -n "constraint vocabulary is closed" src/publishable/param.py
grep -n "One constraint claims it" src/publishable/param.py
grep -n "never touches provenance" docs/reference.md src/publishable/secrets.py
```

Each must have been amended by task 3, 4 or 7. If any was missed, fix it here and say which task
should have.

- [ ] **Step 4: Sweep for `<redacted:` and `E-CRED-`** across the four documents plus `src/` plus
      `tests/`, and confirm every appearance is one this slice put there and that the marker string
      is spelled identically everywhere.

- [ ] **Step 5: Mechanical pass** over every document this task edited: links, anchors, table
      column counts, whitespace, tabs, invisible unicode, `×` for multiplication, hyphen not en
      dash. Skip fenced code blocks.

- [ ] **Step 6: Cross-document pass.** The four documents only. Check the classes that actually
      drift: the worked example (`cohort-pilot` — untouched by this slice, confirm), config
      completeness (no field added, confirm § The one config file's fenced example is unchanged),
      enum comments (task 5 step 4's check), schema fields in prose, declared-vs-derived, versions
      (`CITATION.cff` unchanged — this slice bumps nothing), prevented mistakes.

- [ ] **Step 7: Mutation — the sweeps themselves.** For each `grep` above, run it once against a
      string **known to be present** in the same file list and confirm it hits:

```
grep -n "publishable" README.md docs/design-principles.md docs/experimental-designs.md docs/reference.md | head -3
grep -rn "BaseTemplate" src/publishable/ | head -3
grep -rn "def test_" tests/ | head -3
```

A sweep that cannot hit is a sweep that proves nothing. **Record the three confirmations in the task
report.**

- [ ] **Step 8: Verify and commit.** All four commands.
      `docs: the owned prose sweep for the credential family, over named files`

---

## Task 14: `spec-defects.md` filings, and decision 7's routing correction

**Files:** Modify `docs/superpowers/spec-defects.md`.

**Interfaces:** none.

**A ledger line saying "filed" is not a filing.** `CLAUDE.md` records a gap registered "against
\<owner\>" that existed only in a ledger and never in the defects file. Every entry below goes into
`spec-defects.md` itself, with a heading, the measurement, and a named owner. And **re-owner a
deferral when the slice that filed it finishes**: an entry naming its owner as "whichever slice does
X" points at a closed slice once X lands.

**This family has zero entries today** — `grep -n "required_env\|requires_env\|secret\|credential\|\.env"`
over `spec-defects.md` returns five hits, all `provenance.environment` or `.env.example`-in-a-scaffold
prose, and `grep -n "H7c"` returns nothing. Re-run both before writing, since six slices have landed
since the scoping.

- [ ] **Step 1: Re-measure before filing.** Run both greps above. For each entry below, confirm the
      gap is still open by checking the code, not by trusting this brief.

- [ ] **Step 2: File the README `credentials` region, with the routing correction.** Append to
      `docs/superpowers/spec-defects.md`:

```markdown
## OPEN — the generated README's `credentials` region does not exist, so nothing can merge into it

`reference.md` § The generated README shows a scaffolded README carrying a
`<!-- publishable:begin credentials -->` region with a *"(none yet — added as experiments declare
them)"* placeholder row, and a `cp .env.example .env` setup line above it. **Neither is emitted.**
Measured at `d86290c` and re-confirmed for this filing: a freshly scaffolded `README.md` grepped for
`publishable:begin` returns `overview` and `experiments` and nothing else, and `scaffold.py`'s
`README` constant holds no credentials block and no `cp` line. The control — the same grep for the
two regions that do exist — hits both.

Three consequences, in the order they bite. `reference.md` § Generators already marks *"merging any
new `required_env` into the credentials table"* **NOT BUILT** and says in the same paragraph that
`required_env` "compounds that gap rather than merely sharing it" — that half of the sentence is
now stale, since H7c gave the attribute a reader at `validate`; what remains unbuilt is the merge,
not the reader. `publishable docs`, which § The generated README says regenerates every managed
region, is in `cli.NOT_BUILT_COMMANDS`. And a merge built against an absent region would have
nothing to merge into, which is why H7c refused the charter item rather than absorbing it.

**Routing, and it corrects `H7b-SCOPING.md` § 11.** That document routes "the README managed
regions — `credentials`, a parameter-table region, `generate experiment`'s merge" wholesale to
**`docs`**. It is right about the merge and wrong about the region: the *static* `credentials`
region and the `cp .env.example .env` line are written by **`new`**, i.e. `scaffold.py`'s `README`
constant, and `docs` has nothing to populate until they exist.

**Owner:** whichever slice next edits `new`'s README emission owns the region and the setup line;
`docs`'s slice owns regenerating it; `generate experiment`'s merge follows both. Not H7c, and not
H7b.
```

- [ ] **Step 3: File the two unbuilt readers of `required_env`, each with its owning slice.**

```markdown
## OPEN — two specified readers of `required_env` belong to unbuilt commands

H7c made `BaseTemplate.required_env` readable and gave it its first reader, at `validate`. Two more
readers are specified and cannot be built here, because each belongs to a command in
`cli.NOT_BUILT_COMMANDS`. Filed so neither is folded into a slice that has no business with it.

| Specified | Owner |
|---|---|
| `reference.md` § Reproducing on another device, step 6 — `reproduce` *"copies `.env.example` and lists the `required_env` variables that need values"*, and the consequence stated beneath it | **`reproduce`'s slice** |
| `reference.md` § Metering — `dry-run` *"needs what a run needs minus the compute … which means real credentials"* | **`dry-run`'s slice**, which inherits H7c's load site and its two checks without change |

H7c owes only that the attribute is readable, which it now is.
```

- [ ] **Step 4: File `field_convention`, the remaining unread member.**

```markdown
## OPEN — `BaseTemplate.field_convention` is declarable and read by nothing

Measured at `478c1f3`: `grep -rn "field_convention" src/publishable/` returns two declarations
(`templates/base.py`, `templates/builtin/generic.py`) and one comment in `generators/template.py`
saying the `generate template` stub omits it. Nothing reads it. `reference.md` § Naming conventions
& repeat defaults specifies what it means — a naming pattern and a repeat floor per convention
class — and `naming_pattern` and `default_repeats` are both read while the class that groups them
is not.

This is `CLAUDE.md`'s *unbuilt reader of a shipped surface*, and it is now that row's worked
example: H7c retired `required_env` from that role by giving it a reader, and of the three
remaining members `apparatus_probe` is **H7b task 13's** and `apparatus_facts` is **H7d's**, which
leaves this one unowned.

**Owner:** unassigned. Whichever slice next touches § Naming conventions & repeat defaults should
either give it a reader or state in `reference.md` that it is declarative only.
```

- [ ] **Step 5: File `io.reuse_from`.** The spec names it as "unbuilt and unowned by any H7
      sub-slice, which is a gap this slice files rather than closes". **Check first** whether an
      entry already exists — `grep -n "reuse_from" docs/superpowers/spec-defects.md` — and if one
      does, do not file a second; instead check whether its owner still exists and re-owner it if it
      names a closed slice. If none exists, file one naming the `reference.md` section that
      specifies it and marking the owner unassigned.

- [ ] **Step 6: Re-owner anything pointing at "the secrets slice".**

```
grep -n "secrets slice\|H7c\|the credentials slice" docs/superpowers/spec-defects.md
```

Any entry whose owner is "whichever slice does credentials" now points at a **closed** slice. Rewrite
each to name what is actually left and who holds it, or strike it if H7c closed it. **This is the
step that stops an entry reading as live work nobody holds.**

- [ ] **Step 7: Discharge task 6's deferred obligation.** Run
      `git diff 478c1f3 -- src/publishable/__init__.py` and confirm it is **empty** — decision 8's
      claim that this slice exports nothing. Record the result in the commit message.

- [ ] **Step 8: Mechanical pass** over `spec-defects.md`: table column counts, no empty rows, no
      trailing whitespace, no tab, no invisible unicode, hyphen not en dash in anything that becomes
      an anchor, and **no two headings producing the same anchor** — this file is long and heading
      collisions are its most likely mechanical fault. Note that the cross-document pass does
      **not** apply here; `spec-defects.md` is development record, and the one place where a closed
      gap is struck rather than left to mislead.

- [ ] **Step 9: Mutation.** Document-only; **no mutation reaches it**, as with tasks 1, 2, 5 and 6.
      The verification is step 1's re-measurement and step 6's grep. **Do not file an entry you did
      not re-measure**, and say in the task report which measurements were re-run and what each
      returned.

- [ ] **Step 10: Verify and commit.** All four commands (nothing here should move a test, so the
      suite must land exactly where task 12 left it).
      `docs: spec-defects filings for the credential family, with H7b-SCOPING § 11's routing corrected`

---

## Self-review

### Spec coverage — the eight decisions

| Decision | Task |
|---|---|
| 1 — two codes, not one | **1** (the two § Errors rows and the grounds), honoured by **9** and **10** emitting them separately |
| 2 — the totality check is `E-TEMPLATE-LOAD` and owes no row | **3** (the `ValueError` and its end-to-end confirmation), **2** (the count phrases that must not move) |
| 3 — redact by exact value, and say a redaction happened | **12**, at the **two serialization boundaries** per the spec's correction 1: `runner.execute_plan`'s step-error path and `Collector.render()`. `grep -rn 'type(exc).__name__' src/publishable/*.py` returns **five** constructions, four of which are diagnostics rather than records and reach the sweep through stdout |
| 4 — detect by exact value, never by pattern | **7** (`redact`'s implementation and its by-value test), **12** (the blind pattern mutation named as blind) |
| 4a — core redacts only what it read for a declared variable | **12** step 5, marked document-only |
| 5 — two load sites, and the reconciled sentence | **8**, with `draft`/`resume` recorded as unbuilt rather than stubbed |
| 6 — three choices, a sweep selecting two, a third deliberately unset | **10**, with the three readings tabulated and the deviation from `reference.md`'s `[]` example argued |
| 7 — the README region is filed, not built | **14** step 2, including the correction against `H7b-SCOPING.md` § 11 |
| 8 — this slice exports nothing | **6** (the document statement), **14** step 7 (the `git diff` that discharges it) |

### Scoping coverage — the 14

Tasks 1–14 of this plan are the scoping's § 8 tasks 1–14, in its order and its grain. None was
split, merged, or moved. Task 6's `secrets.py` marker retirement is *executed* in task 7's commit
because a build claim must not precede the build; the ownership stays with task 6 and both tasks say
so.

### Placeholder scan

No step says "similar to Task N" or "as above". Every code block is literal. Every type, function and
attribute a later task references is defined in an earlier one: `Param.requires_env` (3) → `comment()`
(4) → the union (10, 11) → `declared_credential_names` (12); `load_env`/`missing_env`/
`credential_values`/`redact` (7) → the load sites (8) → `_check_required_env` (9) →
`_check_requires_env` (10) → `execute_plan(credentials=)` (12); `run_a_project`'s `_env_file` and
`_local_template` (both added in 8) → used by 8 and 12 respectively;
`_UNION_TEMPLATE`/`_UNION_NAMES`/`_union_project` (10) → used by 11; `_findings_of` (11) is defined
where it is first used; `_SENTINEL` and `_files_under` (12) are defined before the three tests that
use them, and `_LEAKY_AZURE_STEP` is defined in 12 step 7 as a copy of `_LEAKY_STEP` from 12 step 1.
`declared_credential_names(doc, template, conditions)` (12) takes three arguments at its definition
and its one call site.

### Type consistency

`requires_env: dict[Any, list[str]] | None` (task 3) is read as `param.requires_env.get(value)` in
tasks 10 and 12, both guarded by `except TypeError` for an unhashable resolved value.
`credentials: dict[str, str] | None` (task 12) matches `credential_values`'s return (task 7).
`redact(text: str | None, values: Mapping[str, str]) -> str | None` (task 7) is called with
`credentials or {}`, so the `Mapping` is never `None`. `missing_env(names: Iterable[str])` is called
with a generator in task 9 and with a `dict` in task 10 — both are `Iterable[str]`.

### Names checked against their target files before use

`param.py`: `_joined` free (module holds `MISSING`, `_TYPE_NAMES`, `Param`); `_choice_label` is a new
method. `tests/test_param.py`: no module-level helpers exist; every new name is new.
`tests/test_validate.py`: `_CRED_TOTALITY_TEMPLATE`, `_REQUIRED_ENV_TEMPLATE`, `_UNION_TEMPLATE`,
`_ABLATABLE_TEMPLATE`, `_UNION_NAMES`, `_union_project`, `_findings_of` — none collides with
`base_config`, `write_config`, `write_config_nondet`, `write_config_broken`, `write_config_exits`,
`_DELETE`, `codes`, `messages_by_code`, `_validate_with`, `_error_codes`.
`tests/test_cli.py`: `_ENV_READING_STEP`, `_LEAKY_STEP`, `_LEAKY_AZURE_STEP`, `_SECRET_USING_STEP`,
`_LOCAL_CRED_TEMPLATE`, `_AGGREGATE_LEAKING_TEMPLATE`, `_SENTINEL`, `_files_under` — none collides
with `Ran`, `run_a_project`, `_AGGREGATE_STEP`, `_TRAIN_TOUCHING_STEP`. `diagnostics.py`:
`Collector.credentials` is a new field on a dataclass whose only field today is `findings`, so no
existing `Collector()` construction changes. `cli.py`: `declared_credential_names`,
`_flatten_parameters` and the `run_template` local are all to be confirmed absent by grep in task 12
step 3 — `template` is deliberately **not** reused, because `command_run` already binds that name
after `execute_plan`. `tests/test_secrets.py` is a new file.

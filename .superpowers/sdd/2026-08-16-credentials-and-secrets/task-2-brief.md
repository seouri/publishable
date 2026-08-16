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


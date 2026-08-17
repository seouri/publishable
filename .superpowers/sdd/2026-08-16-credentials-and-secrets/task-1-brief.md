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


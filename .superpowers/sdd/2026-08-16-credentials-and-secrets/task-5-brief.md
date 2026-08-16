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


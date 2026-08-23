## Task 10: Ruling B written into the documents — two false sentences DELETED

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: documents only, plus one docstring under `src/` that quotes one of them.**

**Files:** `docs/reference.md`, `src/publishable/hashes.py` (the `covered_config` docstring only).

**The ruling.** `parameters_hash` is **not** normalized. The charter's second clause —
*"`parameters_hash` normalization against `parameter_spec`"* — is **rejected**, not narrowed. Three
grounds, each independently sufficient, and none of them is re-derived by this task:

1. **`parameter_spec` cannot reach the gap.** Of the nine omissions the scoping measured moving the hash,
   **eight are core-schema keys**, and core-schema defaults exist **nowhere as data** —
   `materialize.materialize_config` emits them as literal text lines, and only the `parameters` block is
   generated from `parameter_spec`. Normalizing "against `parameter_spec`" reaches **one** of nine.
2. **Reaching the other eight needs a structure the invariants forbid by name** — *"there is deliberately
   no separate defaults file"*, stated normatively in § There is no separate defaults file.
3. **Normalizing the `parameters` half would be actively wrong.** An omitted `parameter_spec` default
   validates clean and then the step that reads it dies with `E-STEP-PARAM-UNKNOWN`, every execution
   `failed`. Normalizing would hand **one identity claim to a config that runs and a config that
   cannot** — the opposite of what an identity claim is for.

- [ ] **Step 1: DELETE the normalization sentence.** In § How the three are computed, the clause
      *"Values are normalized to what `init` would have materialized before hashing — an omitted
      `cluster_by` and an explicit `cluster_by: null` are the same declaration, and a config that omits a
      defaulted key hashes identically to one that spells it out"* is **deleted**, not softened.
      **Prefer deleting a claim to rewriting it**: a rewrite invents, a deletion cannot. A round that
      closed a false-owner comment by *propagating* the claim to two more sites is the precedent for why.
- [ ] **Step 2: DELETE its justification, which is false against the shipped command.** The following
      sentence argues *"Without that rule, a hand-trimmed config and the file `init` wrote would disagree
      about parameters that are equal, and `diff` would report a difference with nothing to print."*
      `diff` prints exactly the right thing —

      ```
      parameters_hash    DIFFERS
        data.units.cluster_by  null → (absent)
      ```

      — so the justification is false, and it goes with the claim.
- [ ] **Step 3: leave the subtractive rule standing and add ONE honest sentence.** § How the three are
      computed already states the rule two paragraphs later — *"everything in the config except
      `metadata` and `data.input_dir`/`data.output_dir`"* — and it is correct. What replaces the deleted
      pair is one sentence naming the consequence honestly: **a hand-trimmed config and the file `init`
      wrote are two declarations, they hash differently, and `diff` names the key that differs.** Do not
      write a second statement of the coverage rule; the table beneath it already carries that.
- [ ] **Step 4: re-point `covered_config`'s docstring.** It currently says the normalization sentence *"is
      not implemented here — see `docs/superpowers/spec-defects.md` … an OPEN gap owned by H6"*, and it
      **quotes the sentence being deleted**. Once task 12 strikes that entry, this docstring points at a
      struck entry. Replace that paragraph with the **ruling**: `parameters_hash` hashes the config as
      written, by decision, and § How the three are computed is where the rule and its consequence are
      stated. **Delete the quotation rather than updating it.**
- [ ] **Step 5: sweep for the deleted sentences' OTHER homes, and the sweep must be able to fail.**
      Sweep **named files**: the four documents (`README.md`, `docs/design-principles.md`,
      `docs/experimental-designs.md`, `docs/reference.md`), `CLAUDE.md`,
      `docs/feasibility-llm-growth-studies.md`, `docs/superpowers/spec-defects.md`, and every file under
      `src/` and `tests/`. **The sweep must be newline-insensitive** — normalize whitespace across the
      whole file before matching, because a `grep -F` cannot match a phrase that wraps, and that is how
      two of one false sentence's five homes hid on the preceding slice. **Never filter the output of a
      sweep whose job is to find a string** — filter the file list. Prove each sweep can fail by running
      it against a string known to be present. **`covered_config`'s docstring is a known second home**
      and is closed by step 4; find the rest before committing, and **report what you swept, not a
      count**.
- [ ] **Step 6: mechanical pass** on every `reference.md` edit, as task 1's step 6 specifies.

**Delta:** 0 tests.

**What this task must NOT touch.** `hashes.covered_config`'s **body** or `parameters_hash`'s behaviour —
**Ruling B means the code does not change.** A task that finds itself editing either has found a
disagreement and must report it rather than proceed. `diff`'s config-side recomputation. The
`spec-defects.md` entries themselves — striking them is **task 12's**, and this task's docstring edit is
what makes the strike safe.

**Guard-pin arms this task may edit: NONE.**

---


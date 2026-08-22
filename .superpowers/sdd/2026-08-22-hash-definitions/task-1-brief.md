## Task 1: Ruling A written into the documents, and the four-case table

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is how the previous
> slice shipped a Critical, and this pointer is the fix. **Ruling F (the exclude chain) changes the
> command every hashing task runs.**

**Surface: documents only.** No code, no test.

**Files:** `docs/reference.md`.

**The ruling.** § How the three are computed wins. `code_hash` becomes aware of git's exclude rules, and
§ Templates' *"an ignore file has no bearing on"* clause narrows to the **dirty gate**, which is the
question that sentence is actually about. The grounds are the design's Decision 1 and are not re-argued
here: the defect is that the dirty gate consults git and the hash does not, so one mechanism says
*nothing changed* while the other says *the code moved*, and the warning that fires downstream
(`W-STUDY-CODE-HASH-MISMATCH`) names three candidate causes, **none of which is this one**.

**§ Corrections 1 binds this task and reshapes what it writes.** `git check-ignore` answers from **git's
whole exclude chain**, measured in a scratchpad repo: the root `.gitignore`, a **per-directory**
`.gitignore` (`src/sub/.gitignore` holding `perdir.py`), **`.git/info/exclude`**, and the user's
**`core.excludesFile`** — a single call reported all three of `src/pkg/globignored.py`,
`src/pkg/infoexcluded.py` and `src/sub/perdir.py` as ignored. **A table row that says "`.gitignore`"
while the code means "any of git's four exclude sources" is a row narrower than its code**, which is the
shape that was the whole-branch Major on two of H8's sub-slices.

- [ ] **Step 1: add the four-case table to § How the three are computed, and enumerate the rule ONCE.**
      The design's Decision 3 is explicit that a four-case rule invites a two-case sentence at every site
      that mentions it — H5b shipped one in five files. So the table lives in exactly one place and every
      other site **links to its anchor**.

| A file under `src/**` or `templates/**` is | Hashed? |
|---|---|
| in the fixed skip set (`__pycache__`, `.git`, `.ruff_cache`, `.mypy_cache`, `.pytest_cache` as a path component; suffix `.pyc`/`.pyo`) | **no**, whatever git says — including when it is tracked |
| tracked | **yes**, even when it matches an exclude pattern |
| untracked and not excluded | **yes** |
| excluded by any of git's exclude sources — the repo's `.gitignore` files at any depth, `.git/info/exclude`, and the user's `core.excludesFile` | **no** |

- [ ] **Step 2: amend the sentence that states the rule.** § How the three are computed says `code_hash`
      is *"taken from the working tree and skipping whatever `.gitignore` skips."* It stays taken from
      the working tree; what it skips is stated by the table and the sentence links to it. **Do not
      write a second prose statement of the four cases beside the table.**
- [ ] **Step 3: disclose the machine-dependence, in § How the three are computed, beside the table.**
      Because the chain includes a **user-level** excludes file, an untracked file under the two trees
      can be excluded on one machine and not on another. The section's own opening argues *"A hash that
      two machines compute differently is not an identity claim."* The honest statement, which is the one
      to write: **the dirty gate already has exactly this property today** — `git status --porcelain --
      src templates` consults the same chain — so this ruling **extends an existing behaviour to the
      hash** rather than inventing one, and the two mechanisms agreeing is the whole point of Decision 1.
      A file whose hashing status you need to be machine-independent is a file you **commit**. **This
      paragraph is a disclosure, not a reopening of Decision 2**; no task may propose a flag that
      narrows the chain.
- [ ] **Step 4: narrow § Templates' clause to the dirty gate.** Both clauses live in one paragraph of
      § Templates: where parameters are defined — the one that says `code_hash` *"skips `__pycache__`
      directories and compiled `.pyc`/`.pyo` files unconditionally … so no ignore file could have done
      that for it"* and, later, that a hand-assembled repo's *"`code_hash` is unchanged, that being the
      mechanism an ignore file has no bearing on."* The first is **true and stays** — it is the fixed
      skip set, applied first — and gains a link to the table. The second is **narrowed to the dirty
      gate**, which is what that sentence is about. **Do not touch its *"goes dirty at `validate`"*
      clause**: it describes behaviour that does not exist and it is **H6b task 18's**, named here so its
      survival is not read as this task's omission.
- [ ] **Step 5: link, do not restate, at every other site that mentions the rule.** § Three hashes' table
      row for `code_hash`; § Warnings core reports' `W-STUDY-CODE-HASH-MISMATCH` row, which gains **one
      link and nothing else** — its three candidate causes stay three, because Decision 1 makes the
      fourth cause *disappear* rather than need naming.
- [ ] **Step 6: mechanical pass on every edit.** Every relative link and `#anchor` resolves; no two
      headings produce the same anchor; the new table's rows match its header's column count; no trailing
      whitespace, tab or invisible unicode; `×` not `x`; hyphens, never en dashes, in anything that
      becomes an anchor. Skip fenced blocks.

**What this task must NOT touch.** Any code. Any test. `E-CODE-DIRTY`'s absent § Errors row (H6b task
17). § How the three are computed's **normalization** sentence and its false `diff` justification — those
are **task 10's**, and two tasks editing one paragraph in one batch is how a sweep stops one file short.

**Guard-pin arms this task may edit: NONE.** The pin is captured by task 2 in the same batch; if this
task lands first, arm capture happens after it and the arms are unaffected because this task changes no
behaviour.

---


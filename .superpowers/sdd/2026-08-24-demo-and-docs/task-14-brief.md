## Task 14

> **AMENDED 2026-08-25 by the controller, from batch 4's concern 5.** **`E-GIT-NO-REPO`'s enumeration is TEN paths — two uncaught, four by code, four by type — re-derived by READING, and the design's own phrase ("three uncaught-or-by-code additions") does not parse against the code.** That row has now been widened and then undercounted in **three consecutive slices**: six → seven, seven → eight, eight → ten. **State the breakdown, not the total**, and confirm by grep after enumerating by reading — the reverse order is the substitution `CLAUDE.md` § Answering a question with a proxy is about, and it is what produced all three undercounts. **Also yours**: five `E-DOCS-*` § Errors rows that exist in no document, a § Package layout row for `src/publishable/sourceimport.py`, `E-DOCS-REGION-UNKNOWN`'s wording covering **both** its senses, and § Operation commands' rows for `list-templates` and `docs` (wording is in batch 4's report).

**Binding corrections: 1, 2, 3, 5, 8, 9, 10, 11, 12, 16, 19, 20, 21, 24, 29. You are named on NO
guard-pin arm.** You edit `reference.md` in eight sections and that is expected — **no arm hashes it**
(design § 8.2). **Arm A's `REFERENCE` parametrization must stay green**: it holds every `reference.md`
line carrying a worked-example literal, so if it fires you have moved a `cohort-pilot` number.

**The four documents, `CLAUDE.md`, `spec-defects.md`, both consistency passes, and § Executability.**

Document edits:
- § Operation commands: `docs` and `list-templates` lose `NOT BUILT`; `list-templates`' *Does* cell is
  narrowed to task 8's reported wording (correction 21).
- § Creation commands: `demo` loses `NOT BUILT`.
- § What `demo` walks you through: `.demo-progress` *"listed in the generated `.gitignore`"* becomes
  *"listed in the demo repository's `.gitignore`, which `demo` appends"* (correction 16, Decision 9);
  the stop-1 cell names the project-local template; stop 5's cell says the summary is `demo`'s
  (correction 6); the design document's stale *"the `conditions` and `replication` blocks"* is **not**
  followed — build from `reference.md`'s `sweep`, and **do not retro-edit the design**.
- § Using them in step code and § Randomness: `self.rng` is a **`random.Random`** (corrections 3, 4;
  Decision 13). `CLAUDE.md` § Invariants' own sentence is type-agnostic and needs no edit.
- § Package layout: `docs.py` loses `— not yet built`; **rows for `demo.py` and `list_templates.py` are
  added**; `readme_templates/`' row is now true (correction 19). `examples/generic/` **stays and is
  filed** (correction 20) — do not delete a documented directory to make a tree pass.
- § The generated README: brought to what task 3 writes, including the `templates` region it declared
  nowhere.
- § Generators: `generate experiment`'s two `NOT BUILT` halves and `generate template`'s one are gone.
- **§ Errors: five new rows, one per `E-DOCS-*` code** (`-REGION-UNBALANCED`, `-REGION-DUPLICATE`,
  `-REGION-UNKNOWN`, `-NO-REGIONS`, `-NO-README`). **One row per code covering EVERY emit site**, and
  **placed by each table's own scope sentence** — `docs` **raises** these, so read which of the two
  tables that is rather than assuming, and read the sentence rather than the cells. This is the exact
  shape that has produced a whole-branch Major on five sub-slices; it is named here rather than left to
  fall between you and task 13.
- `CLAUDE.md` § Invariants: the creation-command enumeration gains **`demo`**, with the clause Decision
  11 owes — *`reproduce` derives its destination from the record; `demo` has no record to derive from*
  — so the two documented answers about `--into` are one rule, not two.

`spec-defects.md`:
- **Strike** the two bytecode entries (task 9). **Re-read each entry's own claims against the code you
  changed** before striking — a filing's claims go stale like any comment.
- **Re-own** *`diff`'s `uv.lock` row prints two digests…* from H9d to **`unassigned`, with the
  reason**, quoting the 2026-08-24 re-owning and answering it: *"the only remaining slice with a CLI
  rendering surface"* is a **schedule argument wearing a surface argument's clothes** — `diff` is H8b's
  command, and none of `demo`, `docs`, `list-templates` renders a `diff` row or resolves a dependency
  graph.
- **File six new entries**, design § 5's list, each `Owner: unassigned, with the reason` stating that
  no remaining slice (H3c-3's remaining 14 being folds inside cells) has the surface. **Never
  *"whichever slice next touches X"*** — this file rejects that form by name.

**§ Executability on this build:** one dated entry, *"Measured on 2026-08-24 against commit `<sha>`"*,
deriving all four rows per design § 7. **The table block is extracted programmatically and `diff`-ed to
empty** against the H9c entry's copy, by the two independent methods the H8a/H9a/H9b/H9c entries
describe. **No fifth number. It unblocks ZERO configs.** Its cells still name **H8a** — updating them is
exactly how a repeated table stops being repeated.

**Both consistency passes.** The mechanical one over the four documents **named individually**, never
`*.md` — the development record is tracked and `*.md` no longer means what it used to — and **never
filter a sweep's output; filter the file list**, proving each sweep can fail against a string known to
be present. The cross-document one, especially: **the shared worked example** (arm A and arm C's NONE
half are your evidence that it did not move), **config completeness**, **enum comments**, **schema
fields in prose**, and **versions**.

**This is the batch with the most findings historically.** *A documents-and-codes task looks like the
safest one to skip and is the one whose output no later batch reads*, so nothing else will find its
errors.

---

## Controller ruling GG, 2026-08-24 — binding on every task that touches `base_step.py`, `demo`'s generated step, or § Randomness

**`self.rng` becomes a `numpy.random.Generator`.** The grounds are in the design's appended ruling; the
short form is that the documents say so twice, § Randomness's whole argument is written for it, **zero
tests mention `self.rng`**, numpy is already a hard dependency, and a step calling `self.rng.normal(...)`
— which the documents invite — **fails at exit 3 today**.

**This is a behaviour change to a shipped surface. It needs:**
- **a disclosure section**, naming what breaks (`randint`, `gauss`, `choice`'s signature) and what does not
  (`shuffle`, `random`, `uniform`);
- **a pin on the type itself**, since nothing has ever pinned it — and *a surface with no test is how this
  divergence survived a shipped release*;
- **`demo`'s generated step drawing from `self.rng`**, so the walkthrough exercises what it documents;
- **the two `reference.md` statements checked against the new code rather than assumed correct** — they
  were the authority for this ruling, so if either is wrong in some other detail, that is a finding.

**Whichever task owns `base_step.py` owns all four.** If no task does, the batch that discovers it says so
and stops rather than folding it in silently.

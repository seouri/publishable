## Task 1

**The guard pin, captured before anything else moves.** Build the seven arms of the design's § 8 exactly
as that table specifies, including the two re-authorizations, and prove **every** arm able to fail by a
mutation in **production** code.

**You are the only task in batch 1, and no later task may capture a pin.** Arms whose post-edit state the
design writes in advance (**B**, **C**) are captured **at their pre-edit state** here; you do not make
those edits.

Arms, and what to build versus cite:

- **A** — *cite, do not re-capture.* H9a arms A and B and H9b arm A already hold a completed `run`'s
  `run.yaml` leaf by leaf, its tree path by path, and its stdout. Name them by test function in your
  report. **Re-capturing would recreate H8a's *same list pinned twice*, which a later task then edited
  in both places.** Editor: **NONE**.
- **B** — the existing `assert ("reproduce", "NOT BUILT") in tables["Command"]`. **Do not edit it.**
  Record in your report that its sole authorized editor is **plan task 11** and that the post-edit state
  is `("reproduce", "built")` **plus** a new `assert ("list-templates", "NOT BUILT") in tables["Command"]`
  line (correction 20).
- **C** — `apparatus.STOP_CODES`'s set-equality assertion. **Do not edit it.** Sole authorized editor:
  **plan task 9**; post-edit set
  `{"E-APPARATUS-RAISED", "E-APPARATUS-CHANGED", "E-APPARATUS-UNEXPECTED"}`.
- **D** — the two shipped `APPARATUS_CODES` membership assertions. Editor **NONE**. Record that task 9
  may **add** a sibling assertion beside them and that adding one is not editing one.
- **E** — **build this one.** A whole-tree `{path → sha256}` map of (i) the run directory, (ii) the
  operand's own tree and (iii) the source repository, captured before and after a `reproduce`
  invocation, asserting ADDED/REMOVED/CHANGED all empty over each. Today `reproduce` is `NOT BUILT`, so
  capture it against the `NOT BUILT` invocation and **state in the docstring that task 11 makes it
  meaningful and that it must keep passing then** — that is the arm's whole job. Editor **NONE**.
  **Established by snapshotting, never by reading for absent `mkdir` calls** — H9a's `dry-run` arm is the
  precedent and *if a comment says nothing is created, make it create something* is the rule.
- **F** — **build this one if it does not exist; grep first.** The shipped assertion on
  `W-ENV-UNLOCKED`'s message containing *"`reproduce` will not be able to restore it"* is in
  `tests/test_cli.py`. If it exists, **cite it**; if the phrase is asserted only as a substring of a
  longer literal, add an arm that asserts *that clause* on its own. Editor **NONE** — Decision 5 affirms
  the warning, and this arm is what stops a later slice promoting it quietly.
- **G** — *cite, do not re-capture*, and list each cited test by name.

**Mutations required, each full-suite:** delete the write of `config.yaml` from `_execute_prepared`
(arm A's cited arms); remove `reproduce` from `NOT_BUILT_COMMANDS` (arm B); delete `E-APPARATUS-RAISED`
from `STOP_CODES` (arm C); add `E-APPARATUS-CHANGED` to `APPARATUS_CODES` (arm D); make the `NOT BUILT`
path `mkdir` one directory under the operand's parent (arm E); change `W-ENV-UNLOCKED`'s message text
(arm F).

**Must not touch:** `src/` except to mutate and revert; any test file's existing assertions; the four
documents. **Never `git checkout -- <file>` to revert a mutation** — keep a copy and verify the revert by
**behaviour**, not by `git status`.

---


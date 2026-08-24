## Task 17

> **AMENDED 2026-08-23 by the controller, after batches 1-2's review found the escalation lived only in a
> report.** The document work for the new fixed file is **wider than the one tree line this section
> names**, and the following are this task's, each measured on the branch: the `dry-run` transcript's
> fixed-file count (it reads `and 8 fixed files` and is **wrong on the branch today**), **both**
> `<run_dir>/` trees, the two § `config.yaml` and `environment/repo_root.txt` sentences including the
> *"the pair … exactly the two facts"* clause, and the table of contents. **Sweep for the count and the
> list rather than for the file they were first noticed in**, filter the FILE LIST not the output, prove
> the sweep can fail, and **attribute every hit** — a recent sweep found a true hit and its triage
> discarded it.

**Pointer: every ruling's document half lands here. Read Rulings V, W and X, and § Is this additive?**

The documents, and the § Checking consistency mechanical pass is task 18's.

- **§ The other files a run writes** — `identity.json` joins the *"settled before the first execution
  and never touched again"* list, with its own subsection saying what it holds and, explicitly, that
  `input_manifest_hash` is **absent because `manifest/input.json` is itself the operand**. Extend
  § `config.yaml` and `environment/repo_root.txt`'s own sentence rather than writing a second one:
  its *"exactly the two facts a mid-run command cannot otherwise obtain and cannot compute"* becomes
  three artifacts and names which figure each supplies.
- **§ Resuming** — the three comparisons now have operands; `E-RESUME-NO-IDENTITY` for a directory
  without them; the takeover and its liveness rule; the residual `lock.takeover`; the draft paragraph
  kept and made true rather than rewritten.
- **§ `executions.jsonl`** — the example line becomes the ten keys, `attempt` and `n` **deleted**, and
  the *"the two never disagree"* claim now has the durability behind it. Say so.
- **§ One execution at a time** — `lock` records three keys and the third is now written; the liveness
  rule; the sentence *"a lock left behind by a killed process is reported rather than assumed dead"*
  must be **narrowed rather than deleted**, because it stays true of `run` and `draft` and of every
  case the liveness test cannot answer.
- **§ What status means** — `resume`'s `partial` folds the previous attempt's failures; `attempts` is
  a ledger count.
- **§ CLI reference** — the `resume` row's `Status` is task 15's; its `Does` cell gains the takeover.
- **§ Exit codes** — `3`, `4` and `5` gain their first `resume` reader; **no code is minted**; `1`'s
  row already anticipates *"a `resume` whose hashes moved."*
- **`spec-defects.md`** — amend the five-codes filing to three with the reason; amend the
  `resolve_contrasts` precondition (H9c still bound — **amend, do not strike**); **strike** the
  run-start `parameters_hash` entry, which Decision 15 closes; **re-read** the `command_run`-prose
  entry rather than re-deriving its count, and **delete** rather than rewrite any `command_run` claim
  this slice makes false; record the H9-SCOPING § 4.5 falsification and the H9b/H9d disagreement about
  the bytecode-cache fix.
- **`CLAUDE.md`** — one H9b paragraph in the running record, stating the four-row table unmoved and
  **zero configs unblocked**, and the disclosure's six items with item 3 named as the under-read one.
- **§ Executability on this build** — one dated entry, the four-row table **repeated character for
  character**, **no fifth number**.

**Two traps this task has hit before.** *When you insert or remove a row, check every row it moved —
and every sentence whose antecedent it displaced.* H9a's Major 1 was an insertion into a § Warnings
row that displaced the following sentence's antecedent, making the row deny the very thing its
decision exists to establish. And *locating a table row by position* has been wrong twice: name what a
sibling row does.

**Must not touch:** the worked example's numbers; `run.yaml`'s key order; any arm.

**Report:** every sweep you ran, with **every hit attributed individually** — a recent sweep found a
true hit and its *triage* discarded it. Sweep for the **claim**, not for the file the claim was first
noticed in: `src/`, `tests/`, the four documents named individually, `CLAUDE.md`, and the feasibility
analysis.

---


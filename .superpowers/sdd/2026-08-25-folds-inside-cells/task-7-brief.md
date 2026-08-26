## Task 7

> **AMENDED 2026-08-25 by the controller, from batch A's concern 4.** **Mutation MU-3's refusal half is
> YOURS** — batch A declared it in advance and named it in the shipped test's docstring, because the code
> it mutates did not exist yet. *Reporting a mutation blind is necessary and not sufficient; it owes a
> replacement*, and the replacement is due here.

**Corrections that bind this task: C12.**

**Give `E-REPL-FOLD-K-TOO-LARGE` its cell clause at ALL THREE emit sites**, and rewrite its **one**
§ Errors `validate` reports row to cover them. The three: `validate.py`'s `c.error`, and
`replication._fold_k`'s two raises (units and clusters). Each message, when the basis came from cells,
names the cell — its `(axis, level)` pairs — and, under `cluster_by`, that cell's cluster count.

`_fold_k` sees a declaration and a count and never a roster, so the **cell label** arrives as an
optional argument beside `fold_basis`, defaulting to `None`, and every existing caller is unchanged.
**State in the docstring that a `None` label is "no cells resolved", not "cells resolved and
unnamed"** — a helper that ignores an argument hides what its callers stopped testing.

**Mutation MU-7:** reach the clause at only two of three sites — three tests, one per site (a fixed
`k` through `validate`, a `k: all` through `resolve_repeats`, a direct `_fold_k` call), each
asserting the **message names the cell**, not just the code.

**One asymmetry to answer rather than leave.** `E-DATA-HOLDOUT-EMPTY` has rows in **both** § Errors
tables (task 14) while this code has one, in the validate table, though `_fold_k` raises it twice.
Task 5's swallowing `try` is what could change that: if `validate`'s cell draw returns `None` while
`_prepare_run`'s succeeds, a config validates clean and then meets the raise, and § Errors core
raises would owe this code a row — **checked against THAT table's scope sentence, not the validate
one.** Answer it from the code (both draws call the same function at the same `design_digest(doc)`
over the same roster, so a fault in one is a fault in the other), and either say so or file the path.

**Report must state:** the grep it ran (`grep -rn "E-REPL-FOLD-K-TOO-LARGE" src/`), its hit count,
and every hit attributed. **Report what you grepped, not a count without a noun.**

**Must not touch:** the row for any other code; `_fold_k`'s existing two messages' unclustered text.

---

# Batch C — the fold half


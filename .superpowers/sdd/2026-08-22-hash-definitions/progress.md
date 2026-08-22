# H6a — the two hash definitions — the ledger

Branch `h6a-hash-definitions`, off `main` at the H5b merge. **13 tasks in six batches, every batch
reviewed.** The slice changes **what two identity functions compute for unchanged inputs**, which is a
harder exposure than H5b's: `aggregated`'s numbers were wrong on the record's own terms, whereas a hash
that moves is not wrong — it is *differently defined*, and no reader can see the redefinition from a
record. `schema_version` is deliberately **not** bumped (bumping makes `lineage.read_record_file` refuse
every record on disk), so **`uv.lock` is the carrier and the disclosure obligation is heavier, not
lighter.**

Five controller rulings arrived with the design (A–E) and four more with the plan (F–I).

## Batch 1 — tasks 1, 2, 7, 10 — the rulings, the documents, and the pin

Commits `c863e3e` (§ How the three are computed), `ad59bdd` (**the guard pin**), `76efc72` (the
disclosure and arm N), `13ae83c` (Ruling B written, the normalization claim deleted), `6db2942`,
`419ca29` (in-batch fix round), review `db32e13`. Suite 2931 → **2939**. **All four PASS, two Minors, no
Major.**

**Ruling F held and was measured rather than read.** Every `check-ignore` invocation runs as
`GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null git -c core.excludesFile= check-ignore -z
--stdin`, and both the batch and the reviewer built a throwaway repo with a global exclude beside a
committed `.gitignore` to confirm **only the committed rule answers**, with `.git/info/exclude` surviving
as the one disclosed residue. **The ruling overrode the brief in two places and the commit said so** —
the table row drops `core.excludesFile`, and the *machine-dependence is fine, the dirty gate has it too*
paragraph was **not written**. That paragraph would have been the defect: a gate answers *may this run
proceed here*, which is local by nature; a hash answers *is this the same code*, which is not.

**The plan's own base tree could not be run, and the batch found it rather than working around it.**
`templates/t.py` holding `b = 2` is **discovered as a project-local template**, registers nothing, and
`validate`/`run` refuse with `E-TEMPLATE-LOAD` — so arms A and B each carry **two** trees, the plan's for
the direct call and a runnable one for the `run_id` half. The consequence is a live overruling: **arm B's
moving set is four literals, not two**, and it is written into arm B's own docstring, which is the only
place a later task's implementer will see it.

**Two fixture premises were checked by running before any literal was pinned.**
`input_manifest_hash` covers `st_mtime_ns`, so arm C **fixes the roster's mtime** rather than recomputing
the figure; and `allocation_hash` would have been `null` on the implied project, so arm C's project
declares a `between`/`by_attribute` axis to make the figure real. **A fixture built on a false premise is
a fixture whose numbers agree with the bug**, and both of these would have been.

**Four of seven arms have no authorized editor — A, C, D and N — and every arm was proven able to fail.**
The reviewer mutated `hashes.py`'s fold separator (A, B, C, D fail; E correctly unaffected) and `diff.py`'s
row comparison two ways, and reproduced the **asymmetry** the in-batch fix round documents: inverting
fails both of arm N's tests, while forcing `True` fails only the DIFFERS half and leaves the control
passing. **Arm N is the seventh arm and holds the claim a later slice will most want to soften** — that a
`diff` across this boundary prints `code_hash DIFFERS` for identical code.

**One literal was wrong before it was pinned and the fixture caught it** — `parameters_hash` drifted with
a config's `rationale` text. That is the evidence the fixture discriminates, and it is worth more than any
assertion about it.

**Both Minors are about owners and names, and one is the rule stated exactly.** `hashes.py`'s `code_hash`
docstring still says it reads the working tree *"not from git"* — true today, **false after task 5** — and
the report routed it to *"task 3 or 5"*. **An owner that is a disjunction is not an owner**: task 3 changes
only the signature, task 5 wires the predicate, so it is **task 5's**.

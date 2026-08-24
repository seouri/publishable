## Task 4

**Ruling Z, and `code_hash` in the checkout.**

> **RULING Z (binding, restated here):** a hash that differs must say **which input moved**, never guess
> **why**. The scoping measured that this step would report an H6a-boundary difference as *"a rewritten or
> force-pushed history"* — a cause invented from a symptom. H6a's Ruling C already pays for it: `uv.lock`
> is the carrier and a core upgrade moves `code_hash` for identical code. **Every verdict must be
> derivable from what was compared; if two causes cannot be told apart, say so.** **No marker may be
> minted** — H6a Ruling C, and the scoping's § 12 names it.

Recompute with **exactly** `command_run`'s predicate, in the pair form so the file list is available
(correction 19):

```python
pairs = hashes.hashed_files(dest, lambda cands: unignored_under_hashed_trees(dest, cands))
computed = hashes.code_hash_of(pairs)
```

Equal → one line, with the file count. Different → `E-REPRODUCE-CODE-HASH` at exit `1`, **the checkout
kept**, and the output carries: the recorded digest, the computed digest, the file count, the file list,
the checkout path, and **this closed enumeration of causes it cannot separate** —

- the code at that commit really is different: a rewritten or force-pushed history;
- the record predates H6a's redefinition of which files are hashed, which **no key in `run.yaml` can
  date** (`schema_version` was deliberately not bumped, and a scaffolded project's `uv_lock_hash` is
  `null`, so the carrier may be absent);
- this machine's git materialized the tree differently — `core.autocrlf`, which the clone neutralizes,
  or a tracked `.gitattributes`, which it may not.

**Naming a closed candidate set is not a verdict; picking one is.** The output must not contain a
sentence asserting a single cause.

**`draft: true` declines rather than fails** (Decision 10): print *"this record is a draft: its code was
not committed, so `code_hash` is not verified"* and continue — the posture § Reproducing already takes for
the config form, which *"cannot verify a `code_hash` and says so, rather than reporting a match it never
made."* **This is the one cause `reproduce` names, and it is named because the record names it.**

**Fixtures C, D**, plus a `draft` arm on Fixture B. **Fixture C's literal is computed by calling
`code_hash_of` in the test, never hard-coded** — a commit SHA and everything derived from it cannot be a
stable literal, and H9a's self-caught defect was an arm compared against its own read-back.

**Mutations:** compare with `include=None` instead of the git-aware predicate — caught by a **Fixture C
arm carrying a git-ignored file under `src/`**, where the two predicates give `0cc6ddd` and `bdf2ce9`;
**without that ignored file the two agree and the mutation is blind**, which is exactly how a fixture
whose numbers agree with the bug happens. Report the single-cause phrase (Fixture D asserts the
enumeration is present **and** that a single-cause sentence is **absent** — an assertion on the code alone
passes under both wordings). Refuse a draft instead of declining (the draft arm: one path exits `1` before
the closing transcript, the other reaches it at `0`).

**Must not touch:** `hashes.py`, `provenance.py`, `run_record.py`, `reference.md`.

---


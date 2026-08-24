## Task 15

**The four documents, `CLAUDE.md`, § Executability, and both consistency passes.**

`reference.md`:
- § **Reproducing on another device** — step 2's *"can't collide"* narrowed (correction 13): the
  destination is derived so you do not name it, and a second `reproduce` of the same run **refuses**
  rather than overwriting. Step 3's *"catching a rewritten or force-pushed history"* replaced by Ruling
  Z's shape: the difference, the input, and the candidate causes it cannot separate. Step 4 gains the
  lockfile ranking. Step 5 gains the `parameters_hash` self-check and the comment-loss disclosure. Step 6
  **narrowed** to what Decision 12 builds, and it must say what it defers and to which command.
- § **CLI reference** — `reproduce`'s row from `NOT BUILT` to `built`, and its `Does` cell rewritten to
  what the command does.
- § **Errors core raises** — **twelve rows, one per code, each covering every site that raises *or*
  reports it.** § Errors carries one row per code and not per emit site: `E-TEMPLATE-UNKNOWN` had two
  sites and a task scoped by one helper's call site missed the second.
- § **Exit codes and diagnostics** — `5`'s *"a clone or `uv sync` that failed"* gains its first reader,
  and say so the way `3`/`4`'s `resume` sentence does.
- § **The apparatus core can only observe** — `E-APPARATUS-UNEXPECTED` beside the gate, on the gate's own
  terms, and **the third reading of one comparison named explicitly**: the gate tolerates `null → value`,
  `diff` flags it, and the expectation file sides with the **gate**. H8b ruled the first two are two
  questions rather than one contradiction; this is the third, stated so nobody folds it into either.

`design-principles.md` § Design goals — the *"not optional"* footnote (task 6 wrote the decision; you
write the sentence if task 6 did not, and **grep to find out which** rather than assuming).

`CLAUDE.md` — the H9c entry in the same shape as its siblings: what merged, what it retires (**nothing**),
what it unblocks (**zero configs**), the disclosure, and the four-or-five things worth carrying. **State
the behaviour change to `run` and the exit `2` → `1` change at `reproduce new`.** A wrong disclosure is
worse than no disclosure.

§ **Executability on this build** — one dated entry, and **derive the verdict rather than carrying it**:
`reproduce` does not run at `validate` and is not invoked from a step; none of the nine configs is a run
record or declares a `study`, so none is an operand it accepts; **none declares an `apparatus_probe`**, so
`E-APPARATUS-UNEXPECTED` is unreachable for all nine. **The four-row table is repeated character for
character**, by the two independent extraction methods the H8a and H9a entries describe, `diff`-ed to
empty, and its cells still name **H8a** — updating them is exactly how a repeated table stops being
repeated. **No fifth number.** Quote the table or name the dependency; never a single figure.

**Both consistency passes**, and the traps that have actually bitten:
- **Never filter the output of a sweep whose job is to find a string** — filter the file list. A reviewer
  checking this exact rule lost a true hit to `grep -v superpowers`. Prove each sweep can fail by running
  it against a string known to be present.
- **The development record is tracked**, so a sweep over the four documents must **name them
  individually**; `*.md` no longer means what it used to.
- **When you insert or remove a table row, check every row it moved and every sentence whose antecedent it
  displaced** — H9a's Major 1 was an insertion that made a § Warnings row contradict itself three clauses
  later.
- **Locate a row by what a sibling row *does*, never by position.** Seven instances, wrong twice.
- **`ruff format` does not touch `*.md`.** Two agents on two slices blamed it and both reverted files on
  that reading; measured both times as byte-identical. If bytes move, find the cause rather than
  restoring on a story.
- The **cross-document** pass governs the four documents only; a feasibility analysis is exempt from it
  and subject to the mechanical pass in full. **Neither pass governs the development record** — correct a
  spec or a scoping by **appending**, never by editing.

**Must not touch:** `spec-defects.md` (task 14), any guard-pin arm, `src/`.

---

## Corrections 26–29, appended 2026-08-24 before dispatch — two mechanisms, one fixture recipe, one count

The design's own [§ Appendix](../specs/2026-08-24-reproduce-design.md) carries these with their full
measurements. They are repeated here because **a correction that reaches only the design reaches no
implementer**, and each names the task section it amends.

26. **Fixture D was not constructible, and a rewritten history is caught at the CHECKOUT rather than by
    the hash — amends tasks 3 and 4.** A commit SHA is a hash over its own tree, so a different tree
    cannot live at the same SHA; measured, an amend produced a new SHA (`fcc45b7…` → `ff45afe…`) and left
    the original's tree untouched, so the recorded SHA still checks out to the recorded bytes and the
    comparison **passes**. **Task 4's Fixture D becomes two arms**: **D1**, the record's `code_hash` set
    to the pre-H6a figure computed in the test by `hashes.code_hash(root, None)` over a tree holding a
    git-ignored file under `src/` (`bdf2ce9` against `0cc6ddd`); and **D2**, a `code_hash` edited to an
    arbitrary digest. **Task 3 gains a thirteenth code**, `E-REPRODUCE-COMMIT-UNREACHABLE` at exit
    **`5`**, for a recorded commit the remote no longer holds — measured: after an amend,
    `git clone --no-local` of a bare intermediate does not carry the old object and
    `git checkout --detach <recorded-sha>` fails `fatal: unable to read tree`. Its message names the
    recorded commit and says the remote does not hold it.
    **And a fixture trap you must design around:** `git clone` of a **local path** hardlinks the whole
    object database, **unreachable objects included**, so Fixture A's local-path remote **cannot
    reproduce that state** — the checkout succeeded in the measurement. The recipe needs a bare
    intermediate cloned with **`--no-local`**. A fixture built the obvious way passes while testing the
    opposite state. **`reproduce` itself passes no `--no-local`**: that would break the legitimate
    local-remote case and slow every clone. The flag belongs to the fixture.
27. **Task 9's mechanism is `record(incoming)` THEN `changed(incoming)` on the seeded object, and the
    design's *"asked only for `changed`"* is false of the shipped class.** `Observations.changed`'s
    `assert` rests on a caller contract its own docstring states — *"`record` runs before `changed` for
    the same `facts`"* — which holds for a run's own object and **not** for one seeded from a foreign
    record. Measured on a seeded object, `changed` **alone** raises `AssertionError` for three cases: an
    extra incoming fact, a condition the expectation does not carry, and — **the one that matters** —
    **`null → value`**, which § Reproducing on another device requires to **pass** and calls *"more
    evidence rather than less"*. With `record(incoming)` first, **which is what `Observer` itself does**,
    all eight measured cases are right and there is still no new comparison function. **Task 9's mutation
    list gains a sibling: drop the `record` call and keep the `changed` call**, caught by Fixture P arm 2,
    which becomes the arm separating an `AssertionError` from a pass. Fixture Q's `total_probes` claim is
    unchanged — the seeded object's counts are its own and reach no record.
28. **Task 5's "reachable beside the operand" is a filesystem probe, and the docstring must say so.** The
    test is `(<operand>.parent / "environment" / "uv.lock").is_file()` — a probe for a file, not a
    structural fact about the operand. Correct for both measured forms, and **stated because a bundle
    placed inside a run directory would take the run-directory branch**. What makes it safe is the digest
    check: `E-REPRODUCE-LOCKFILE-EDITED` fires when the copy's sha256 does not match the record's
    `uv_lock_hash`, so a foreign copy is refused rather than used. **Write the reason, not just the
    probe** — that is the difference between a proxy and a guarded one.
29. **The count is thirteen, and it carries its noun — amends task 15.** Twelve `E-REPRODUCE-*` codes and
    one `E-APPARATUS-*` code: **thirteen codes, thirteen § Errors rows**, one row per code covering every
    site that raises *or* reports it. Anywhere this plan or the design says *twelve*, read **thirteen**.
    The § Executability verdict does not move and **no fifth number** is minted: a count of refusals says
    nothing about whether any of the nine configs can reach one, and none can. **Still no exit code is
    minted** — `5` gains a second reader here rather than a first, since the lockfile task already reads
    it for `uv sync`.

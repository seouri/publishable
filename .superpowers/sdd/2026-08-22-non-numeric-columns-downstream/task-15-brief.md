## Task 15: the records

> **BINDING CONTROLLER RULINGS — read them before this task's steps.** They are appended at the end of
> this plan under *Controller rulings, 2026-08-22*, they **post-date every task section including this
> one**, and where they disagree with the steps below **they win**. `task-brief` extracts one `## Task N`
> section and nothing else, so an appended ruling reaches no brief on its own — that is exactly how batch
> 1 shipped a Critical, and this pointer is the fix. **Ruling 1 (the mixed column) is the one most likely
> to change what you build.**

**Surface: records and documents. Runs against the finished branch.** `spec-defects.md` is a live list, so
a closed gap is **struck** rather than deleted; every other tracked record is **appended to, never
retro-edited**.

**Files:** `docs/superpowers/spec-defects.md`,
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md`, `CLAUDE.md`

- [ ] **Step 1: strike three entries, each against the code.**
      - *a unit whose only recorded column is non-numeric is silently dropped* (Owner: H5b) — **struck**,
        naming **which of its four options was taken** (carry with the column, and admit the unit) and
        why the other three were rejected, and answering **the fourth question it did not ask**: such a
        unit **does** enter `paired_keys`, `n_paired` and the resample pool (Decision 6, documented by
        task 8).
      - *the `aggregate` table omits declared unit attributes and non-numeric columns* (RE-OWNED to H5b) —
        its **non-numeric half struck**; the attributes half was already closed by H5a and is not
        re-struck.
      - *the second empty-level gate in `cli`'s stratum loop is unpinned* — **already struck by task 11.**
        **Confirm it, do not strike it twice.** *A ledger line saying "filed" is not a filing*, and its
        converse holds too: an entry struck twice reads as two gaps.

- [ ] **Step 2: three things that were filed NOWHERE, each recorded in the right form.**
      - **The mixed `str`/`float` question**, which H5a's design says is *"Filed, not built, owner H5b"*
        while `spec-defects.md` has no such entry: **discharged by Decision 11 in `reference.md`** (task 3),
        and the write-side residual **filed unassigned with a reason** (task 3, step 5). **Confirm task 3's
        entry exists; do not write a second one.** Record in your report that *a design line saying
        "Filed" is not a filing* — **second instance in one slice pair**, the first being H5a's own `.csv`
        null question.
      - **A derived key colliding with a non-numeric recorded column is not refused** — recorded by task 10
        as *found and closed in the same slice*. Confirm.
      - **A non-numeric recorded `by` column draws no `W-STATS-STRATUM-SHADOWED`** — **closed by task 9**,
        recorded the same way, here.

- [ ] **Step 3: FILE AGAINST H9 — `diff`'s `uv.lock` detail lines do not name the moved package.** The
      controller's ruling: this slice's change is carried by `provenance.environment.uv_lock_hash`, which
      `diff` reads, so it is **not** true that no row points at it — the true and smaller claim is that
      **the row that points at it is the one a reader is least likely to read**. If the ruling is wrong, the
      symptom is a user who diffs two runs, sees `uv.lock DIFFERS` beside changed numbers, and **cannot
      tell whether the lockfile move caused the change.** File it with **Owner: H9**, and the reason:
      `reproduce` is what reads the environment back, so H9 is the slice with that surface. **Verify both
      halves before filing** — `cli.py` writes `provenance.environment.uv_lock_hash` and `diff.py`'s
      `ROW_LABELS` holds a `uv.lock` row reading exactly that key; grep both and report them.
      **Nothing is minted here to make the change more visible, and that is a decision rather than an
      omission**: a fourth hash, a core-version record key, or a `diff` row of its own would each add a
      second source of truth for something `uv.lock` already answers.

- [ ] **Step 4: append a correction to the spine's 2026-08-22 amendment. DO NOT EDIT IT.** Its
      § The hardening slices row sizes H5b at **"(10)"** and this slice is **16**; and its
      behaviour-change sentence has already been corrected once the same day. The append records the count
      **and** that the exposure is what the design's § The behaviour change enumerates — seven keys in
      one fixture, a correction family in another, four things that newly stop or newly warn — rather than
      a phrase. *A spec records what was decided when it was written; append the correction and say what it
      replaces.*

- [ ] **Step 5: `CLAUDE.md` — the slice entry and the order line.** A new entry in the shape of the
      existing ones, and it **must carry the disclosure the controller ruled stands**: the seven moving
      keys with computed before/after literals, and the **four** things that newly stop or newly warn —
      the collision, the `by` suppression, an `aggregate` that assumes every row carries its numeric
      column and may now raise (contained as `W-STATS-AGGREGATE-FAILED`), and **a purely numeric derived
      metric newly drawing `W-STATS-RESAMPLE-THIN`** because admitting units creates degenerate draws
      (`2000 → 1998` on Fixture A, `2000 → 1999` on the two-condition run — an existing code at an
      existing site seeing a wider input, so **no § Warnings row moves**). Add the eighth moving-key
      class — **a derived metric's `p_value` and, through the family, its `p_value_corrected`**
      (§ Corrections 16) — and say that **one warning is MINTED**, `W-STATS-REPEATS-DISAGREE`, which is a
      new thing that fires rather than a stoppage, so the entry does not read as if nothing new appears.
      Say that `uv.lock` is the
      carrier and that being *able* to derive the change from a lockfile hash is not being told.
      **The order line:** H5b removed from *remaining*; **H6, H9 and H3c-3's remaining 14** stated as what
      is left. **Grep `CLAUDE.md` for every occurrence of "H5b" and reconcile each**, reporting the list —
      the order line is not the only one.

- [ ] **Step 6: both consistency passes, in full, over the FOUR DOCUMENTS BY NAME.**
      `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, plus
      `CLAUDE.md` and the feasibility analysis for the removal sweep. **Every sweep names its files, never
      filters its output, and each must be PROVEN ABLE TO FAIL** by running it against a string known to
      be present — *a reviewer checking this exact rule lost a true hit to `grep -v superpowers`.*
      Mechanical: links, `#anchor`s, duplicate anchors, table column counts, trailing whitespace, tabs,
      invisible unicode, `×` not `x`, hyphens not en dashes — **skipping fenced blocks.**
      Cross-document: the shared worked example — **this slice changes no worked-example number, and the
      way to show it is `git diff` over `README.md`, `docs/design-principles.md` and `docs/reference.md`
      for the worked example's interval and hash literals, expecting ZERO hits.** (No pin arm in this
      slice covers those files; H5a's did, and citing it here would be a claim about the wrong branch.)
      Then: config completeness; enum comments; schema fields in prose; declared vs. derived; versions; prevented
      mistakes. **The feasibility analysis is exempt from the cross-document pass and subject to the
      mechanical pass in full.**
      **Neither pass touches the development record** — a spec and a scoping record what was decided and
      measured on their dates. `spec-defects.md` is the one exception.

- [ ] **Step 7.** No mutation. **Named blind, with its replacement:** the B5 review, which checks every
      struck entry against the code and every "filed" against the file. **Prove each sweep can fail and
      paste the proof** — that is this task's substitute for a mutation.

- [ ] **Step 8: run** the four commands (no test delta) and **commit**: `H5b task 15: strikes, filings,
      the H9 filing, the spine correction, CLAUDE.md, and both consistency passes`.

---


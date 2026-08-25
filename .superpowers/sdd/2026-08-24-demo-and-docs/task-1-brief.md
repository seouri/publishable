## Task 1

**Binding corrections: 25, 26, 27, 28, 29.**

**The guard pin, captured before anything else moves.** Build the seven arms of the design's § 8 exactly
as that table specifies, and prove **every** arm able to fail by a mutation in **production** code or in
a document. **You are the only task in batch 1, and no later task may capture a pin.**

- **Arm A** — *cite, do not re-capture.* `test_h5a_arm_d_the_worked_examples_own_numbers_as_raw_text`'s
  `DESIGN_PRINCIPLES` and `REFERENCE` parametrizations already hold `cohort-pilot`'s numbers as raw
  text. **Re-capturing recreates H8a's *same list pinned twice*.** Editor **NONE**. Name the test by
  function in your report.
- **Arm B** — the `[README]` parametrization of the same test. **Do not edit it.** Record that its sole
  authorized editor is **task 12** and that its post-edit state is the **procedure** in design § 8.1 —
  **not a literal tuple**. Copy that procedure verbatim into your report.
- **Arm C** — **build this.** A whole-file `sha256` of `docs/design-principles.md` and
  `docs/experimental-designs.md`, asserted as two literals. Editor **NONE** — both must be
  byte-identical at merge, and a red arm is a finding rather than a hash to refresh. **`README.md` and
  `docs/reference.md` are deliberately NOT in this arm**, and design § 8.2 says why: task 12 must edit
  README twice and task 14 must edit `reference.md` in eight sections, so a whole-file digest over
  either would report only *an edit happened*. What needs protecting in those two is pinned by
  **content** — arms A, B and E — not by a digest.
- **Arm D** — **build this.** A `{relative path → sha256}` map of a `publishable new` project's whole
  tree **except `README.md`**, built by running `scaffold_project` into `tmp_path`. Editor **NONE**.
  Its job is Decision 16: after the constants move into `readme_templates/`, every other scaffolded
  byte must be identical.
- **Arm E** — *cite, do not re-capture.* `tests/test_diff.py`'s H8c arm D. Editor **NONE**.
- **Arm F** — **build this.** `assert set(NOT_BUILT_COMMANDS) == {"demo", "docs", "list-templates"}`,
  plus a citation (not a copy) of the shipped `("list-templates", "NOT BUILT")` row assertion. Sole
  authorized editor **task 13**; post-edit state is design § 8's row F.
- **Arm G** — *cite, do not re-capture*, per correction 29. Editor **NONE**.

**Mutations required, each full-suite:** change one digit of a `cohort-pilot` interval in
`docs/reference.md` (arm A) and in `README.md` (arm B); append a blank line to
`docs/design-principles.md` and to `docs/experimental-designs.md` (arm C, both halves); change one byte of `scaffold.CITATION` (arm D); add a
fourth key to `NOT_BUILT_COMMANDS` (arm F).

**Must not touch:** `src/` except to mutate and revert; any existing test assertion; the four documents
except to mutate and revert. **Never `git checkout -- <file>` to revert** — keep a copy and verify the
revert by **behaviour**, not by `git status`.

---


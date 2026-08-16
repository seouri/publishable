## Task 12: Split the four-`register_*` row in § The importable surface

**Files:** Modify `docs/reference.md`

`register_template` · `register_resolver` · `register_probe` · `register_writer` share **one row** marked `not yet built`, under a paragraph saying "Importing one raises `ImportError` today". Only the first is built now.

**That table's `Status` is its third column, so the CLI test does not parse it** — an unsplit row would silently claim three unbuilt exports are built, with nothing to catch it.

- [ ] **Step 1:** Split the row so only `register_template` reads built; correct the `ImportError` sentence, which is now false for one of the four.
- [ ] **Step 2:** Check every row the split **moved**, and any count phrase near the table.
- [ ] **Step 3: Commit.**

---


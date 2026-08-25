## Task 3

**Binding corrections: 16, 17, 19, 20. This is the slice's only behaviour change to a shipped command,
and it is its own batch.**

Two moves, in this order.

**(a) `readme_templates/` receives the scaffolds.** Move `README`, `CITATION`, `MIT` and `GITIGNORE`
out of `scaffold.py`'s module globals into files under `src/publishable/readme_templates/`, read at
scaffold time. `scaffold.py` keeps the `.format(name=…)` calls and every refusal. Add the package data
declaration `pyproject.toml` needs, and **verify by installing into a fresh venv that the files ship**
— a template that is not packaged is a scaffold that raises on someone else's machine.

**(b) `scaffold.README` becomes what § The generated README specifies:** the `credentials` region with
its two-column table, `## Experiments` moved **inside** the `experiments` region with its
`Name | Template | Run` table, the `cp .env.example .env    # then fill in the values below` line, the
`## Reproducing a published result` section, and a **`templates` region** (correction 17's fifth drift
— the document declares one nowhere and § Templates needs one).

**`scaffold.GITIGNORE` does not change.** Decision 9: `.demo-progress` is appended by `demo` to the
demo repository's own `.gitignore`, not added to every `publishable new` project. **The documented
sentence is what moves**, and task 14 moves it. Adding it here is the *widening a behaviour change to
make a document self-consistent* fault.

**Guard-pin arm D is yours to keep passing, not to edit.** Its editor is **NONE**. It hashes every
scaffolded file **except `README.md`**, so move (a) must produce byte-identical output for all four
others; if arm D goes red, move (a) is wrong, not the arm.

**Mutation:** change one byte of the `credentials` region body and confirm a test fails that names the
region rather than the whole file.

**Must not touch:** `docs.py`, `cli.py`, the four documents, guard-pin arms.

---


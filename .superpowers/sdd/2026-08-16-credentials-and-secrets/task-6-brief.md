## Task 6: § Package layout, § The importable surface, and decision 8

**Files:** Modify `docs/reference.md`. No `src/` change, no test change. **Depends on task 7 for
truth** — see the ordering note.

**Interfaces:**
- Consumes: § Package layout's `secrets.py` line, which reads
  `│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance) — not yet built`;
  § The importable surface's enumerated table and its "A row marked `not yet built` is a promise"
  paragraph.
- Produces: `secrets.py` without its `— not yet built` marker, and an explicit statement that this
  slice exports nothing.

**Ordering note the implementer must respect.** § Package layout's marker means "specified and
unbuilt", so retiring it is a **build claim**. Do the § The importable surface half now; **do the
`secrets.py` marker retirement as the last step of task 7**, in task 7's commit, so the document
never claims a module that is not there. This task's step 2 is therefore explicitly deferred, and
task 7 step 8 executes it. Recorded here rather than in task 7 alone so a reader of either task
finds it.

- [ ] **Step 1: State that this slice exports nothing.** In § The importable surface, after the
      paragraph beginning "**A row marked `not yet built` is a promise, not an export.**", add:

```
**Not everything core adds is a name on this table, and the credential mechanism is the example.** `required_env` is an attribute of a class you already subclass and [`requires_env`](#a-credential-can-belong-to-a-parameter-value) is a keyword of a construct you already import, so declaring either adds no import line to your template. A mechanism reaching you through a class you subclass and a keyword you pass is the shape to expect: this table enumerates what you *import*, and it moves only when there is a new name to import.
```

- [ ] **Step 2: DEFERRED to task 7 step 8.** Retiring `secrets.py`'s `— not yet built` marker in
      § Package layout. Do not do it here; the module does not exist yet at this commit.

- [ ] **Step 3: Check the `Status` column.** § The importable surface's table has a `Status` column
      whose values this slice does not move: `Param` is already `built`, `BaseTemplate` is already
      `built`. Confirm neither row needs a change, and confirm the sentence "Importing one raises
      `ImportError` today" is still derived from that column rather than from an enumeration of
      names — `CLAUDE.md` records that replacing it with an enumeration would convert a
      self-maintaining statement into a maintenance obligation nobody owns.

- [ ] **Step 4: Mechanical pass** over the edited paragraphs: links and anchors resolve
      (`#a-credential-can-belong-to-a-parameter-value`), no duplicate anchors introduced, no trailing
      whitespace, no tab, no invisible unicode.

- [ ] **Step 5: Mutation.** Document-only; **no mutation reaches it.** The claim "this slice exports
      nothing" is verified by a grep, not a test: `git diff 478c1f3 -- src/publishable/__init__.py`
      must be empty at the end of this slice. **Run that at task 14** and record the result there;
      note the obligation in this task's commit message.

- [ ] **Step 6: Commit.** `docs: the importable surface does not move — a subclass attribute and a Param keyword are not exports`

---


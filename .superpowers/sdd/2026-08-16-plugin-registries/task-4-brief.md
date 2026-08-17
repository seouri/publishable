## Task 4: § Package layout + § The importable surface — a home for the shared scan

**Files:** Modify `docs/reference.md`. No `src/` change, no test change. **Its § Package layout
marker is retired inside task 7's commit** — see the ordering note.

**Interfaces:**
- Consumes: § Package layout's fenced tree, whose lines are `│   ├── <file> # <description>` and
  whose entries marked `— not yet built` are specified-and-unbuilt; the paragraph beneath it
  beginning "**Modules marked `— not yet built` are specified and unbuilt.**"
- Produces: a `plugins.py` line in that tree, marked `— not yet built` at this commit; and the
  statement in § The importable surface that the scan is core's own and reaches a user through no
  import.

**Ordering note the implementer must respect, and it is copied from H7c's tasks 6/7 because it is
the same shape.** § Package layout's marker means "specified and unbuilt", so retiring it is a
**build claim**. Add the line **with** its marker here; **retire the marker as the last step of task
7, in task 7's own commit**, so the document never claims a module that is not there. This task's
step 3 is therefore explicitly deferred and task 7 executes it. Recorded in both tasks so a reader
of either finds it.

- [ ] **Step 1: Read the tree and pick the insertion point by neighbour, not by position.** The
      entry for `param.py` reads `│   ├── param.py # Param: type, default, constraints, help`, and
      `envelope.py` follows it. `plugins.py` belongs beside the modules that answer "what is
      installed", not beside the config machinery — put it immediately after the `manifest.py` line,
      which is the nearest entry that is also about what the machine supplies rather than what the
      config declares. Name that neighbour in your commit message.

- [ ] **Step 2: Add the line.** Keep the column alignment of its neighbours exactly — the tree is a
      fenced block and `ruff format` does not touch it, so misalignment survives to the reader:

```
│   ├── plugins.py             # entry-point metadata scan; the resolver/probe/writer/reader registries — not yet built
```

      Note what the comment does **not** say: it does not enumerate the groups' names and it does
      not say "five". A count in a comment goes stale; what the set *is* is "the registries that are
      not templates'", and the templates' own registry stays in `templates/{base,registry,discovery}`
      where the tree already puts it.

- [ ] **Step 3: DEFERRED to task 7's last step.** Retiring `plugins.py`'s `— not yet built` marker.
      Do not do it here; the module does not exist at this commit.

- [ ] **Step 4: State that the scan is not an import.** In § The importable surface, after the
      paragraph beginning "**Not everything core adds is a name on this table, and the credential
      mechanism is the example.**", add:

```
**The five plugin registries move this table; the machinery behind them does not.** `@register_resolver` and its siblings are names you import and decorate with, so each has a row. What resolves those names — a scan of installed package metadata, run by core before your code exists — reaches you through no import at all, and the module holding it is [core's own source](#package-layout) rather than a name on this list. That is the same boundary `cfg` and `io` sit on: constructed by core, handed to you, never imported.
```

- [ ] **Step 5: Mechanical pass** over both edited regions: anchors resolve (`#package-layout`), the
      fenced tree's box-drawing characters are `│`, `├──` and `└──` as its neighbours use, no
      trailing whitespace, no tab, no invisible unicode. Skip fenced blocks for the table/heading
      checks but **do** check the tree line's trailing whitespace by hand, since it lives inside a
      fence and the whitespace rule is unconditional in this repo.

- [ ] **Step 6: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**.

- [ ] **Step 7: Mutation — none reaches this task, and one later task partly closes it.** § Package
      layout is read by no test. The `— not yet built` markers in it are not bound to `src/`'s
      contents by anything. **Task 7 closes the half that matters**: it creates `src/publishable/plugins.py`
      and retires this line's marker in the same commit, so a marker retired against a module that
      does not exist would be caught by task 7's own import in its test file. The paragraph added in
      step 4 is unpinnable and stays that way; **nothing closes it.** Stated, not papered over.

- [ ] **Step 8: Commit.** `docs: plugins.py gets a home in the tree, marked unbuilt until task 7`

---


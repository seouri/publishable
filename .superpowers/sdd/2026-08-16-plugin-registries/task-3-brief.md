## Task 3: Decision 2's fifth group — `publishable.readers`, settled and filed

**Files:** Modify `docs/reference.md`, `docs/superpowers/spec-defects.md`. No `src/` change, no test
change.

**Interfaces:**
- Consumes: § Creating a plugin's `[project.entry-points."publishable.writers"]` TOML block and the
  paragraph beginning **"Four registries, one mechanism"**, whose closing clause reads "it takes the
  object and returns `bytes`, and its reader inverts it"; § The importable surface's row whose
  `Name` cell is `register_resolver · register_probe · register_writer`.
- Produces: a fifth entry-point group `publishable.readers` and a fifth decorator `register_reader`,
  documented; and a `spec-defects.md` entry recording that the gap existed and is now closed by
  specification, with the code owed by tasks 14 and 15.

**The ruling and its grounds, from decision 2.** `io.write` dispatches on the longest registered
suffix and `StepIO._read` **inverts the same table** — its own docstring says so. The asymmetry is
what produces a bare `KeyError` for a third-party writer today, proved by mutation in the
re-scoping's § 5(a). `CLAUDE.md`'s invariant that *each core writer takes exactly what its reader
gives back* presumes a reader exists for every writer; a "stated convention" that a writer's entry
point resolves its own inverse would leave that invariant true of core and false of plugins. So:
**mint the fifth group.** Four registries become five, and § Creating a plugin's "Four registries,
one mechanism" heading sentence moves with it.

- [ ] **Step 1: Read before writing.** Read § Creating a plugin's four TOML entry-point blocks and
      the "Four registries, one mechanism" paragraph in full. Read § Steps and artifacts' sentence
      about `io.write`'s dispatch. Confirm the gap is still unfiled:
      `grep -n "publishable.readers" docs/superpowers/spec-defects.md` → exit 1, with
      `grep -n "register_resolver" docs/superpowers/spec-defects.md` → six hits as the can-fail
      control on the identical file.

- [ ] **Step 2: Add the fifth TOML block** to § Creating a plugin's `pyproject.toml` example,
      immediately after the `publishable.writers` block:

```toml
[project.entry-points."publishable.readers"]
".fastq.gz" = "publishable_my_assay.writers.fastq:read"
```

- [ ] **Step 3: Rewrite the "Four registries" paragraph's opening.** Replace **"Four registries, one
      mechanism.** Templates, [resolvers](#where-units-come-from),
      [probes](#the-apparatus-core-can-only-observe), and [writers](#steps-and-artifacts) are each an
      entry-point group and a `@register_*` decorator" with:

```
**Five registries, one mechanism.** Templates, [resolvers](#where-units-come-from), [probes](#the-apparatus-core-can-only-observe), [writers and readers](#steps-and-artifacts) are each an entry-point group and a `@register_*` decorator
```

      and replace the paragraph's closing clause "it takes the object and returns `bytes`, and its
      reader inverts it" with:

```
it takes the object and returns `bytes`, and its reader inverts it — which is a fifth group rather than a convention, because [`io.write` dispatches on the writer table and `io.read_upstream` indexes the reader table](#steps-and-artifacts), so a suffix present in one and absent from the other is a promise core cannot keep. A writer registered without its reader is refused at load for that reason, the same breath in which a suffix core already writes is.
```

- [ ] **Step 4: Split § The importable surface's `not yet built` row into two.** The existing row's
      `Name` cell reads `register_resolver · register_probe · register_writer`. Replace that one row
      with two, keeping the `Kind`, `Status` and `Is` columns' shape:

```
| `register_resolver` · `register_probe` | decorator | not yet built | Two more of the five plugin registries — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
| `register_writer` · `register_reader` | decorator | not yet built | The registries an artifact suffix is claimed through, in the pair `io.write` and `io.read_upstream` require — see [Creating a plugin](#creating-a-plugin-publishable-plugin-new) |
```

      **Splitting the row is what keeps the sentence "Importing one raises `ImportError` today"
      true**, because that sentence derives its claim from the `Status` column rather than from an
      enumeration of names. Do not replace it with a list. Tasks 12, 13, 14 and 15 each move a
      `Status` cell as their name lands; this task moves none.

- [ ] **Step 5: Update the paragraph immediately under § The importable surface's fenced import
      example** if it says "four" anywhere, and re-read the sentence "One of the four plugin
      registries" in `register_template`'s own row — it must become "One of the five plugin
      registries". Sweep the four documents by name for `four plugin registries` and
      `Four registries`, read each hit, and fix every one. Can-fail control: the same sweep for
      `plugin registries` must return strictly more hits.

- [ ] **Step 6: File it.** Append to `docs/superpowers/spec-defects.md`:

```markdown
## STRUCK 2026-08-16 — `publishable.readers` had no entry-point group, so a third-party writer had no reader

**Was:** § Creating a plugin declared four entry-point groups and said of a writer "its reader
inverts it", with no mechanism for supplying one. `artifacts.WRITERS` and `artifacts.READERS` are
two module dicts, `io.write` dispatches through `_suffix_for`, which iterates `WRITERS` alone, and
`StepIO._read` indexes `READERS` — so a suffix registered as a writer and not as a reader gives
`io.read_upstream` a bare `KeyError` rather than a coded `ArtifactError`. Proved by mutation
(`H7b-SCOPING-2.md` § 5a): adding one key to `WRITERS` alone reproduced it, and deleting the key
restored the read. Filed here for the first time — `H7c` task 14 filed four entries in this family
and none of them was this one.

**Closed by specification** in H7b Part A task 3: a fifth group `publishable.readers` and a fifth
decorator `register_reader`, with `register_writer` refusing a suffix that has no reader. The code
is owed by tasks 14 and 15 of the same slice; this entry is struck when task 15 lands, not before.
```

      Note the entry is written as STRUCK-on-landing rather than OPEN: it is closed in the document
      by this task and in the code by task 15. **Task 15's last step re-reads this entry and
      confirms the strike is honest.** Use `git add -f` when committing, per `CLAUDE.md`.

- [ ] **Step 7: Mechanical pass** over § Creating a plugin and § The importable surface: anchors
      resolve, the two new table rows have exactly four cells each, TOML fence closes, no trailing
      whitespace, no tab, no invisible unicode. `spec-defects.md` is development record — the
      cross-document pass does not govern it, the mechanical one does.

- [ ] **Step 8: Verify.** `uv run pytest` → **1999 passed, 2 xfailed**. The § The importable surface
      table is read by no test at this commit; confirm that by running `uv run pytest tests/test_cli.py -q`
      and observing it green, since that file is the one that parses `reference.md` tables and it
      parses the **CLI** tables, not this one.

- [ ] **Step 9: Mutation — none reaches this task.** Every deliverable is a document sentence or a
      defects entry. The `Status` cells stay `not yet built`, so nothing changed behaviour and no
      test can go red. **Task 15 closes it**: it builds `register_reader`, enforces the symmetry, and
      its own test pins the refusal's message. Stated rather than manufactured.

- [ ] **Step 10: Commit.** `docs: mint the publishable.readers group, and file the gap it closes`

---


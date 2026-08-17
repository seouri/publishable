## Task 31: `hash_index` — the table case and the resolver case together

**Files:** Modify `src/publishable/manifest.py`, `src/publishable/units.py`,
`src/publishable/cli.py`, `docs/superpowers/spec-defects.md`, `tests/test_manifest.py`,
`tests/test_cli.py`.

**Interfaces:**
- Consumes: `manifest.build_manifest(input_dir: Path, policy: str, index_names: set[str] | None = None) -> dict[str, Any]`,
  whose `hash_it` is `policy == "hash_all" or (policy == "hash_index" and rel in (index_names or set()))`
  — read in `src/publishable/manifest.py`; `cli.py`'s single call site,
  `build_manifest(input_dir, doc["data"]["input_manifest_policy"])`, which passes **two** arguments;
  `Unit.paths: tuple[str, ...]`; `ResolverIO.read_paths` from task 23.
- Produces: `units.index_names(units_decl: dict, roster: UnitList | None, reads: tuple[str, ...] = ()) -> set[str]`;
  `cli.py` threading it; a `spec-defects.md` filing for the pre-existing table-case defect, struck
  CLOSED in the same entry.

**This is broken for the table case too, and the resolver half cannot be built without closing it.**
Measured at `53090e9` and re-confirmable: `index_names` has zero callers in `src/` and no mention in
`tests/`; under `hash_index` **every** `sha256` comes back `None`, for a table source as much as a
resolver's. Three `reference.md` passages promise otherwise — § Three hashes' table
(*"Content hashes for the files `data.units.from` resolves — the index and whatever it names"*),
§ What `run.yaml` records (*"Under `hash_index` the `sha256` key is present for the files
`data.units.from` resolves and absent for the rest"*), and § Where units come from. It is
**unfiled**: `grep -n "hash_index" docs/superpowers/spec-defects.md` → nothing. File it and close it
in the same entry, since this is the task that cannot proceed without closing it.

**Three sources, one expression.** `_from_table` sets `paths=()` and the source names one file;
`_from_glob` sets `paths=(rel,)` and the source names none; a resolver names whatever it read and
its units name their own paths. So *the source's own file, where the source names one, plus every
path its units name* covers all three, and **no case is left silently empty** — which is the failure
mode of shipping table + resolver and leaving glob at `sha256: None`.

**The trap this task is specifically exposed to.** Under `hash_index` the `sha256` **key is present
and its value is `None`**. An assertion on `"sha256" in entry` passes on a completely broken policy —
§ What `run.yaml` records anticipates exactly this (*"Absent rather than null, so 'not hashed' can't
be misread as 'hashed to nothing'"*) and the code does the thing the document says it must not.
**Assert the value**, and include a file the source does *not* name whose `sha256` is `None`, or the
test passes on a policy behaving like `hash_all`.

- [ ] **Step 1: Write the failing test.** Append to `tests/test_manifest.py`:

```python
def test_hash_index_hashes_the_named_files_and_nothing_else(tmp_path):
    """The VALUE, not the key. Under `hash_index` the `sha256` key is present and
    `None` today, so `"sha256" in entry` passes on a completely broken policy —
    which is how this went unnoticed since the policy shipped. The unnamed file is
    the control that separates `hash_index` from `hash_all`."""
    (tmp_path / "index.csv").write_text("patient_id\np1\n")
    (tmp_path / "scan.bin").write_bytes(b"\x00\x01")
    (tmp_path / "unnamed.txt").write_text("not named by anything\n")

    manifest = build_manifest(tmp_path, "hash_index", {"index.csv", "scan.bin"})
    files = manifest["files"]

    assert files["index.csv"]["sha256"] is not None
    assert files["scan.bin"]["sha256"] is not None
    assert files["unnamed.txt"]["sha256"] is None
    assert files["index.csv"]["sha256"] == build_manifest(tmp_path, "hash_all")["files"][
        "index.csv"
    ]["sha256"]
```

      and in `tests/test_units.py`:

```python
def test_index_names_covers_every_source_shape(tmp_path):
    """One expression, three sources: the source's own file where it names one,
    plus every path its units name. A table names its index and no paths; a glob
    names no index and one path per unit; a resolver names what it read and
    whatever its units carry. Asserted together, because shipping two of the three
    is how the glob case would be left at `sha256: None` silently."""
    from publishable.units import UnitList, Unit, index_names

    table = UnitList([Unit(key="p1"), Unit(key="p2")])
    globbed = UnitList([Unit(key="a.dcm", paths=("a.dcm",)), Unit(key="b.dcm", paths=("b.dcm",))])
    resolved = UnitList([Unit(key="a1", paths=("reads/a1.fq",))])

    assert index_names({"from": "index.csv"}, table) == {"index.csv"}
    assert index_names({"from": {"glob": "*.dcm"}}, globbed) == {"a.dcm", "b.dcm"}
    assert index_names({"from": {"resolver": "plate_wells"}}, resolved, ("layout.csv",)) == {
        "layout.csv",
        "reads/a1.fq",
    }
    assert index_names({"from": "index.csv"}, None) == {"index.csv"}  # no roster, still the index
```

- [ ] **Step 2: Run and see it fail.** The manifest test fails on
      `files["index.csv"]["sha256"] is not None` today **only if** the third argument is dropped —
      so run it first *with* the argument to confirm `build_manifest` already honours a set it is
      given (it does; the defect is that nothing gives it one), then the `units` test fails with
      `ImportError: cannot import name 'index_names'`. Record both outcomes: the fix is the wiring,
      not the manifest's arithmetic.

- [ ] **Step 3: Implement.** In `src/publishable/units.py`:

```python
def index_names(
    units_decl: dict[str, Any], roster: UnitList | None, reads: tuple[str, ...] = ()
) -> set[str]:
    """The relative paths `input_manifest_policy: hash_index` hashes.

    `reference.md` § Three hashes: "the index and whatever it names". One
    expression over all three sources, because a per-source branch is how one of
    them comes to be left silently unhashed:

    - a **table** names one file and its units name no paths;
    - a **glob** names no file and each unit names the path it was built from;
    - a **resolver** names whatever it read (`ResolverIO.read_paths`) and its
      units name their own payloads — § Where units come from: "the paths the
      resolver read plus the paths its units name, so a unit whose payload the
      resolver never opened still gets that payload hashed".

    A roster that did not resolve still yields the source's own file: the index is
    named by the declaration, not by the roster, and a manifest built beside a
    failed resolution should not silently stop hashing it.
    """
    source = units_decl.get("from")
    named: set[str] = set(reads)
    if isinstance(source, str) and source:
        named.add(source)
    for unit in roster or ():
        named.update(unit.paths)
    return named
```

      In `src/publishable/cli.py`, thread it at the one `build_manifest` call site, which sits
      **downstream** of the roster in `command_run` — so nothing moves:

```python
    manifest = build_manifest(
        input_dir,
        doc["data"]["input_manifest_policy"],
        index_names(units_decl or {}, roster, resolver_io.read_paths),
    )
```

      In `src/publishable/manifest.py`, `build_manifest`'s docstring says *"Relative paths plus
      size, mtime, and — at the policy's depth — content hash"*, which was false for `hash_index`
      because nothing supplied `index_names`. It is true now; leave it, and add one sentence naming
      `units.index_names` as what supplies the set, so a future reader can find the answer to "which
      files does the index name".

      In `docs/superpowers/spec-defects.md`, add an entry — filed and struck CLOSED in one, with the
      measurement that found it and the commit it was measured against — recording that
      `hash_index` hashed nothing at all for **every** source until this task, that
      `build_manifest`'s `index_names` had no caller, and that `hash_index` appeared in no test.

- [ ] **Step 4: Run and see it pass.** `uv run pytest` → **2090 + 2 = 2092 passed**, 1 skipped,
      2 xfailed. Then the other three commands.

- [ ] **Step 5: Mutate.** In `src/publishable/cli.py`, drop the third argument from the
      `build_manifest` call — restoring the state this task found.
      `tests/test_cli.py`'s end-to-end `hash_index` assertion (add one beside the
      `plugin_versions` test if the file has none: run a `hash_index` config and assert the index's
      `sha256` is not `None` and an unnamed file's is) must **FAIL**. **Checked:**
      `tests/test_manifest.py`'s test passes the set directly and would **not** catch this — it
      pins the arithmetic, not the wiring, and the wiring is the defect. That is why the mutation is
      named at the call site and the test that catches it is the end-to-end one.

      Second mutation, in `units.index_names`: delete the `for unit in roster or ():` loop.
      `tests/test_units.py::test_index_names_covers_every_source_shape` must **FAIL** on the glob
      case, which has no source file and would come back empty. **Checked against the test body:**
      the glob assertion is exactly the case where the source names nothing, so it cannot be
      satisfied by the `source` term alone.

- [ ] **Step 6: Commit.** `manifest: hash_index actually hashes the index — for every source`

---


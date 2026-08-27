# W1 scoping — a plugin's writer and reader are registered and never loaded

Read-only measurement against `docs-plugin-tutorial` at `00ad727`, on 2026-08-27. Every
identifier, call-site count and file position below was grepped or probed against that tree,
never remembered. Spec claims and build facts are labelled separately throughout.

**Why `W1` and not `H10a`.** The H-series is the charter `CLAUDE.md` records as complete —
H1 through H9 and every sub-slice merged, the last on 2026-08-25. Numbering this `H10`
would imply a charter row that does not exist. It is a new slice, chartered by
[`spec-defects.md`](spec-defects.md)'s entry *a plugin's writer or reader never dispatches
unless user code imports its module*, filed and measured on 2026-08-27.

**Verdict: 9 tasks.** The gap itself is two functions and roughly forty lines. Six of the
nine are the consequences: one shipped ruling whose stated premise the fix falsifies, two
§ Errors rows that enumerate their emit surfaces and would become narrower than their code,
a normative dispatch sentence that goes false, a process-level cache that must be resettable
because the suite's own fixture restores the tables it caches over, and a surface the filing
did not name at all — `io.read_input`, which means **input files**, not only artifacts.

**Baseline at `3427713`** (this branch's other commit; `00ad727` is documentation only):
`uv run pytest -q` → **3448 passed, 1 skipped, 2 xfailed**, 364 s.

---

## 0. Executive summary — the four things that change what this slice is

1. **The filing proposed the wrong fix.** It said *"loading the group once at `command_run`'s
   start is the plausible closure."* `plugins.load_entry_point`'s own docstring says it is
   *"what a command calls once it has resolved a name and **actually needs the object**"*, and
   everything else in that module *"answers from package metadata, which is the guarantee
   § Creating a plugin justifies the whole mechanism by."* Eager loading contradicts the
   contract of the function it would call. The shape that matches is lazy suffix resolution —
   `units._resolver_for`'s and `apparatus._probe_for`'s shape, on a suffix rather than a name.
2. **`reference.md` is already written for the lazy shape**, which makes this a wiring gap
   rather than a design change. § Errors core raises, `E-PLUGIN-COLLISION`'s row: *"A writer
   or reader claiming a core suffix from inside a plugin's top level raises this at decoration
   time, which is inside the import `E-PLUGIN-LOAD` contains — so a load reports the
   containing code."* A decoration-time raise inside a contained import is reachable **only**
   if something loads that group. Nothing does.
3. **`io.read_input` is in scope and the filing missed it.** `_read` has **seven** call sites,
   three of them `read_input`. So a reader resolved from metadata would newly apply to files
   under `input_dir`, not only to artifacts a step wrote — a wider blast radius than the
   filing's `io.write` framing, and the reason task 4 exists.
4. **One shipped ruling's premise is falsified by the fix, and the ruling should survive
   anyway.** `_read`'s docstring justifies leaving reader-without-writer as raw bytes with
   *"that suffix registered no writer in this process, so nothing here could have written the
   file `_read` is now looking at."* Under `io.reuse_from` that premise is already thin — the
   file came from a *prior* run — and under metadata resolution it is gone. The ruling
   (dispatch is decided from the writer side alone) is still right, on a different ground.
   **Append the correction; do not retro-fit the argument.**

---

## 1. What exists — measured

| Fact | Where | Measured |
|---|---|---|
| `_suffix_for` is the single dispatch, iterating `WRITERS` | `artifacts.py:235` | 2 call sites in `src/`: `write` at `:984`, `_read` at `:1258` |
| `WRITERS` / `READERS` are filled **only** by a decorator running | `plugins.py:172`, `:197` | assignment appears nowhere else |
| Nothing loads the `publishable.writers` or `publishable.readers` groups | — | `load_entry_point` has exactly **two** call sites in `src/`: `units.py:352` (resolver), `apparatus.py:93` (probe) |
| `GROUPS`'s own docstring says *"Every entry-point group core **reads**"* | `plugins.py:43-50` | false of two of its five members |
| `_registry_for`'s `publishable.writers` / `publishable.readers` arms are unreachable | `plugins.py:203-217` | its only reader is `declared_names`, called at `units.py:353` and `apparatus.py:94` with the resolver and probe groups |
| `_read` reaches input files, not only artifacts | `artifacts.py` | 7 call sites: `:1025`, `:1072`, `:1128`, `:1169`, `:1357`, `:1360`, `:1404` — three of them `read_input` |
| `scan_group` is uncached and walks all installed metadata | `plugins.py:66-78` | no `lru_cache`, no `cache`, nothing memoized anywhere in the module |
| A real installed-distribution fixture already exists | `tests/conftest.py:87-127` | `installed(dist_name, version, groups)` writes a `.dist-info` with `entry_points.txt`, then `syspath_prepend` + `invalidate_caches()` |
| The suite restores the two tables around any test that fills them | `tests/conftest.py:133-158` | `registries` snapshots `RESOLVERS`, `PROBES`, `WRITERS`, `READERS` — and would **not** clear a new metadata cache |

**Reproduced end to end at `937591f`** (unchanged at `00ad727`): a plugin registering
`.plate_assay` in both groups, installed with `uv add --editable`, its **resolver from the
same distribution dispatching in the same run**, and a step calling
`io.write("readings.plate_assay", {"n": 6})`:

```
run failed: 10 of 10 executions failed; first error at step01_summarize_units · condition 0 · seed96: E-ARTIFACT-UNWRITABLE ArtifactError: readings.plate_assay has no registered writer, so the object must be bytes or str, not dict
```

exit `4`, `run.yaml` written. Adding `import publishable_plate_assay.writers.artifact` to the
step makes the same run write the artifact in all ten step directories.

---

## 2. The fix, stated as the change rather than as an intention

`_suffix_for` decides over `WRITERS`'s keys. It must decide over **core suffixes ∪ already
registered ∪ the `publishable.writers` entry-point keys**, where the third set comes from
`scan_group` — metadata only, no import — and only the winning key is then passed to
`load_entry_point`. `READERS` gains the same lazy lookup at `_read`, and **only as a lookup**:
the writer side stays the sole dispatch, which is what keeps § 4's ruling intact.

Four helpers already exist and this slice writes no new mechanism:
`scan_group` (keys from metadata), `load_entry_point` (the one importer, containing
`SystemExit` and every other top-level failure as `E-PLUGIN-LOAD`), `declared_names` +
`check_registration` (the decorator argument against the key, `E-PLUGIN-DECORATOR`), and
`scan_group`'s per-key claim **list**, which is how two distributions claiming one suffix
becomes `E-PLUGIN-COLLISION` over the complete set in name order rather than a race.

**What the user-visible change is, in one sentence:** a step writing a mapping to a suffix an
installed plugin claims goes from failing every execution to succeeding. That is a behaviour
change to shipped commands, in the additive direction, and § 6 lists the two places it is not.

---

## 3. The cache is a task, not an implementation detail

`_suffix_for` runs on **every** `io.write` and every `_read`. `scan_group` walks every
`sys.path` entry's metadata. Memoizing the writer group's keys per process is required for
this not to be a per-write directory scan — and the memo has three constraints, each measured:

- **`tests/conftest.py`'s `registries` fixture restores `WRITERS`/`READERS` and would not
  clear a new cache**, so a test that installs a distribution leaks its suffix into every
  later test. The fixture must clear it, and that is an edit to shared test machinery.
- **`importlib.metadata`'s path cache is keyed on a directory and its mtime** — stated in the
  `installed` fixture's own docstring, which is why two distributions means two calls and two
  directories. A core-side cache sits *above* that one and must not be assumed to see a
  distribution installed after the first scan.
- **A miss must be cheap and a hit must not import.** The memo holds *keys*, not loaded
  functions; the loaded function still lands in `WRITERS` through the decorator, so the second
  write of a suffix is a plain dict hit.

---

## 4. The ruling whose premise the fix falsifies

`artifacts.py:1233-1257`, `_read`'s docstring, and `reference.md` § Creating a plugin's closing
clause both rest on the same sentence: *"nothing in this process ever wrote that suffix, so
there is no broken pair to refuse."*

That premise is **already** weaker than it reads — `io.reuse_from` and `io.read_upstream` read
a *prior run's* artifact, and `io.read_input` reads a file no run wrote at all — and under
metadata resolution it is simply false: a suffix can be claimed by an installed distribution
this process never loaded.

**The ruling should survive, on a ground that measures true.** Dispatch is decided from the
writer side because the writer table is what `io.write` used to choose the encoding; a reader
with no writer is not a broken pair but an unclaimed extension, and reading such a file as
bytes is the same answer as for a suffix neither table knows. Two shipped tests pin exactly
this and **must still pass unchanged**:

- `tests/test_artifacts.py::test_a_reader_with_no_writer_is_never_dispatched_to` — registers a
  reader directly into `READERS` and asserts the file reads back as raw bytes with the reader
  **not consulted** (`read_calls == []`).
- `tests/test_artifacts.py::test_a_resolver_io_reads_through_the_same_table_a_step_does` — a
  registered pair serves `ResolverIO.read_input` too, *"one dispatch, not two"*.

A fix that scans the **readers** group for dispatch candidates breaks the first. Scanning only
the writers group keeps both. That is the whole of the design constraint here, and it is why
this is task 3 rather than a note.

---

## 5. Decomposition — 9 tasks

### Part A — dispatch · 3

1. **Memoized writer-suffix candidates from metadata.** A `plugins`-level helper returning the
   `publishable.writers` keys, cached per process, with an explicit reset; `conftest.registries`
   clears it. Pin: two distributions claiming one suffix reports both in name order, and a
   suffix no distribution claims costs no import (assert `load_entry_point` is not called).
2. **`_suffix_for` decides over the union, and loads exactly the winner.** Longest-suffix
   comparison unchanged, so `.fastq.gz` still beats `.gz` — the two existing pins at
   `tests/test_plugins.py:259` and `:268` must pass untouched. `load_entry_point` +
   `check_registration` on the winner only.
3. **`_read` looks up the reader lazily, and the writer side stays the sole dispatch.** The two
   tests in § 4 pass unchanged; a plugin pair resolved from metadata decodes through the
   registered reader.

### Part B — the surfaces the filing did not name · 2

4. **`io.read_input` under a plugin suffix.** Three of `_read`'s seven call sites are
   `read_input`, so a claimed extension under `input_dir` now decodes. Decide and pin whether
   that is wanted for **`ResolverIO`** specifically, where the existing test says one dispatch
   serves both — the honest answer is yes, and it needs saying rather than inheriting.
5. **Failure inside an execution.** A plugin whose top level raises now does so at the first
   write, inside a step, inside a metered execution. Pin the containment: `E-PLUGIN-LOAD`
   surfaces as that execution's failure with a `run.yaml`, not as a bare traceback, and
   `KeyboardInterrupt` still stops the command.

### Part C — the documents, which is where the debt is · 4

6. **`_read`'s docstring ruling, corrected by appending** (§ 4). The existing argument stays as
   written; the new ground is appended beneath it, and the false premise is struck rather than
   rewritten. *A rewrite invents; a deletion cannot.*
7. **Two § Errors rows widen.** `E-PLUGIN-DECORATOR` (`reference.md:1252`) and `E-PLUGIN-LOAD`
   (`:1253`) each **enumerate** their emit surfaces — *"a resolver source's dispatch, at
   `validate` as well as at `run`, and an apparatus probe's dispatch … `run`, `draft`,
   `dry-run` and `freeze`"* — and neither names a writer or a reader. § Errors carries one row
   per code covering **every** emit site, so a slice adding an emit surface owes this sweep
   whether or not it mints a code. This one mints none.
8. **One normative dispatch sentence goes false.** `reference.md:1344`: *"only against suffixes
   something actually registered."* After this slice, an installed claim is a candidate before
   anything registers. The § Creating a plugin paragraph at `:4147` carries the same claim twice
   — the registration-versus-read asymmetry, and the *"nothing in this process ever wrote that
   suffix"* clause — and `:1196`'s `E-ARTIFACT-UNREADABLE` row states it a fourth time.
   **Sweep for the claim, not for the file**, and sweep newline-insensitively: this phrase wraps.
9. **The tutorial and the filing.** `docs/tutorial-writing-a-plugin.md` § 7 teaches the import
   workaround, its refusals table routes `E-ARTIFACT-UNWRITABLE` to it, and the § Gaps entry
   describes it — all three move together, and the heading's pinned commit moves with them.
   `spec-defects.md`'s entry is struck with the reader named. `GROUPS`'s docstring stops being
   false of two of its members in the same edit.

---

## 6. What is NOT in this slice

- **Eager loading at `command_run`'s start.** Argued out in § 0.1 rather than deferred: it
  imports plugin code for runs that never write the suffix. Its one real advantage is
  disclosed instead — with lazy resolution a plugin's top level runs inside a *timed* execution,
  so a plugin doing slow I/O at import pays for it inside the measurement. If that becomes a
  problem the remedy is to move the **scan** to run start and leave the import lazy, which task
  1's helper makes a one-line change.
- **A `READERS`-only claim becoming dispatchable.** Refused, with § 4's two pins as the reason.
- **`validate`-time checking of a writer claim.** Core never inspects the body of user Python,
  so it cannot know which suffixes a step will write. There is nothing for `validate` to check
  and no warning it could honestly emit.
- **The other three open entries** in `spec-defects.md` — `template.validate` receiving a dict,
  the plugin scaffold's five tree discrepancies, and the `uv.lock`/example-config half of that
  entry. None shares a surface with this one.

---

## 7. Traps specific to this slice

| Trap | Why it applies here |
|---|---|
| A mutation whose two branches cannot differ | Deleting the metadata scan is invisible unless a fixture **installs** a distribution whose suffix nothing registers. Every dispatch test that registers through the decorator passes with the scan gone — which is how this defect shipped in the first place |
| A count where the property needs membership | "The writer was called" passes if *any* writer was called. Assert the bytes the plugin's writer produced, which are distinguishable from core's for every core format |
| A decoy whose sort position agrees with the bug | Longest-suffix means a `.gz`/`.fastq.gz` pair is the discriminating fixture, and both must be *entry-point* claims — one registered and one claimed reproduces neither ordering |
| A test whose reader normalises the defect away | A plugin writer's output is bytes; assert on `read_bytes()`, not through `_read`, or the reader under test undoes the writer under test |
| Proving an arm cannot move offered as proof the line is pinned | Task 8's four doc sites are the kind nothing fails on. The pin is the document-versus-code test pair, and it must be shown to fail with one sentence reverted |

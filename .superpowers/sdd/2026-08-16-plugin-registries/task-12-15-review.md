# Tasks 12–15 review — `register_resolver`, `register_probe`, `register_writer`, `register_reader`

Reviewed `5aad355..e3a1d96` (four commits) against the four briefs, the task report, and
`docs/superpowers/specs/2026-08-16-plugin-registries-design.md` with its appended corrections.

**Baseline re-verified, not taken from the report.** `uv run pytest` → **2034 passed, 2 xfailed**
(113s). `uv run ruff check .` → all checks passed. `uv run ruff format --check .` → 78 files already
formatted. `uv run mypy` → success, 44 source files. Every mutation below was reverted by copying a
pre-mutation backup back over the file, `__pycache__` deleted, and green re-confirmed by running the
tests — never by `git status`, never by `git checkout --` on a source file. `git status` at the end
of the review shows only the untracked `task-12-15-report.md` (see § Out of scope, item 3).

---

## Verdicts

### Task 12 — `register_resolver`

**T12-A · Important · `register_resolver`'s docstring names a function that does not exist.**
The shipped docstring reads *"…so this records what the source says and `check_registration` is what
compares the two."* `grep -rn "check_registration" src/ tests/ docs/reference.md` returns **one hit:
that sentence.** `check_registration` is task 16's — the decorator-vs-key check at load, unbuilt at
this commit — and the sentence states in the present tense that a comparison happens which nothing
performs. This is the coordinator's item (b), the shape this slice has already shipped two Criticals
of, and it is worse than a stale comment: it names a symbol a reader will grep for and not find,
which is how "assuming a documented rule has code behind it" starts. It came from the brief verbatim,
which is not a defence — six of six implementers on the previous slice were expected to find a
brief-vs-code disagreement. **Fix:** say the comparison is what task 16 will add, or drop the clause.

**T12-B · Important · The `registries` fixture is a check that cannot fail.**
The fixture is *correct* by reading — it snapshots all four mappings this slice touches, restores by
`clear()` + `update()` so a **deleted** key is restored as well as a **set** one, and it is not
autouse (`grep -n autouse tests/conftest.py` shows exactly one, the pre-existing environ restore, so
its docstring's claim is true). But **nothing pins it**. I replaced the entire restore loop with
`_ = saved`, cleared `__pycache__`, and ran the whole suite: **2034 passed, 2 xfailed** — identical
to the unmutated run. Task 14's brief step 5 prescribed the alone-vs-together comparison as the
discriminator; I ran `uv run pytest tests/test_plugins.py tests/test_artifacts.py -q` (118 passed),
so that comparison does not discriminate either. The reason is that no test asserts core dispatch
behaviour *after* a test that leaks a suffix, and `.fastq`/`.fastq.gz`/`.gz` collide with nothing
core writes. This is the deliverable of task 12 that no mutation reaches, and the report does not say
so. **Fix (cheap):** one test that registers `.gz` and then asserts, in a *later*-collected test,
that `artifacts.WRITERS` holds exactly `CORE_SUFFIXES` — or accept it and record the gap explicitly.

**Not a finding — the report's mutation-(a) deviation stands.** `@register_resolver("plate_wells")`
rebinds `resolve` to the decorator's return value before either assertion runs, so a `return None`
mutant fails on `RESOLVERS["plate_wells"] is resolve`, one line earlier than the brief predicted. It
still fails, and for the docstring's stated reason. The residue worth naming: given
`RESOLVERS[name] = fn`, the second assertion (`resolve(None, None) == [...]`) is **implied** by the
first — the CLAUDE.md "assertion implied by another in the same test" shape — so the test has one
effective assertion, not two. Harmless here because the first is the discriminating one.

### Task 13 — `register_probe` and `validate._check_probe`

**T13-A · Critical · `reference.md` § The importable surface still marks `register_probe`
`not yet built`, and the paragraph below it now states a falsehood.**
Line 943: `` | `register_probe` | decorator | not yet built | … ``. Line 950: *"**A row marked
`not yet built` is a promise, not an export.** Importing one raises `ImportError` today."*
`uv run python -c "import publishable; print(publishable.register_probe)"` prints a function, and
`"register_probe" in publishable.__all__` is `True`. `git show 98eb381 --stat` confirms task 13's
commit touched **no** `docs/reference.md` — task 12 split the two-name row and correctly left
`register_probe` unbuilt at that commit, and task 13 never flipped it. This is exactly the shape
`CLAUDE.md` names: a sentence that **derives** its claim from the `Status` column, so the row is the
thing that is wrong and the row is what must move. It is Critical because the sentence is normative
prose in one of the four documents, and it is false about a name a plugin author would be told not to
import. **Fix:** move the cell to `built`; nothing else in that paragraph needs touching.

**And the test that would have caught the reverse does not look.**
`test_a_probe_is_importable_from_the_one_root` asserts only `"register_probe" in publishable.__all__`
— its resolver sibling additionally asserts `publishable.register_resolver is not None`, and the
probe one dropped that line. So the single-line mutation of removing `register_probe` from
`__init__.py`'s `from publishable.plugins import …` leaves `__all__` untouched and the test green: I
ran it, **2 passed**, and `uv run ruff check .` also passed (F822 is not in this project's rule set,
so lint does not stand in for the assertion either). A test whose *name* claims importability and
whose body imports nothing — `CLAUDE.md`'s "a test whose name claims the guarantee". Reverted and
re-run green. **Fix:** one line, `assert publishable.register_probe is not None`.

**T13-B · Important · `PROBES` is a fifth shipped-but-unread surface and it is unfiled — and so is
`RESOLVERS`, the same family with a different owner.**
See § The `PROBES` judgment below for the reasoning. The check `_check_probe` reads
`BaseTemplate.apparatus_probe` against the `publishable.probes` **metadata** scan — verified by
mutation, twice — so `apparatus_probe` genuinely gained its first reader and the `spec-defects.md`
amendment and the `generators/template.py` comment correction are both accurate. But the *registry*
`PROBES` is written by the decorator and read by nothing; `grep -rn "PROBES" src/` returns only
`plugins.py`. The brief's step 9 and the report state this honestly — which is the right call on the
scope question — but neither is a filing, and `grep -n "RESOLVERS\|PROBES" docs/superpowers/spec-defects.md` returns
**nothing**. `CLAUDE.md` § Habits: *"A ledger line saying 'filed' is not a filing."* `RESOLVERS`
(task 12) is the identical shape — written by its decorator, read by nothing, reader named as **Part
B task 23** in its own brief, equally unfiled. **Fix:** one `spec-defects.md` entry naming both, with
two owners — `PROBES` → **H7d** (probe execution), `RESOLVERS` → **H7b Part B task 23**.

**Mutations re-run, not taken on report.** (a) removing the `_check_probe(name, template, c)` call
site → `KeyError: 'E-PROBE-UNKNOWN'` in
`test_a_declared_probe_no_distribution_registers_is_reported` (the honouring test passes vacuously,
as the brief predicts). (b) `if declared in known:` → `if False:` →
`test_an_installed_probe_satisfies_...` fails on its **first** assertion, with the `installed`
fixture's distribution present — so the two branches genuinely differ and the mutation is not blind.
Both reverted and re-run green. The `E-PROBE-UNKNOWN` row **does** exist in § Errors `validate`
reports (`docs/reference.md:536`), so no row is owed there.

### Task 14 — `register_writer` into `artifacts.WRITERS`

**T14-A · Minor · The compound-suffix assertion cannot distinguish "longest wins" from
"first-registered wins".** `test_a_third_party_suffix_reaches_io_write_s_dispatch` registers
`.fastq.gz` **then** `.gz` and asserts `_suffix_for("sample.fastq.gz") == ".fastq.gz"`, with the
comment *"The longest registered suffix still wins."* I mutated `_suffix_for`'s body from
`(best is None or len(suffix) > len(best))` to `best is None` — i.e. first matching key in insertion
order wins, not longest — and `tests/test_plugins.py tests/test_artifacts.py` stayed **green (118
passed)**, because `.fastq.gz` was inserted first and is therefore also the first match. This is
`CLAUDE.md`'s *"a fixture with too few elements to distinguish the candidate orderings"* — the fixture
rules out "last wins" and nothing else. `_suffix_for` is pre-existing code, which is why this is
Minor rather than Important; the *comment* claiming the guarantee is task 14's. **Fix:** register
`.gz` first and `.fastq.gz` second, or assert both orderings.

**T14-B · Minor · Nothing drives a plugin suffix through the public write path.** The test's own
docstring says *"Registration is only real if `io.write` finds it, so the assertion is over the
dispatch rather than over the dict"* — but the assertion is over `artifacts._suffix_for`, a private
helper, and over `WRITERS[...] is write_fastq`. `StepIO.write` — which is what `io.write` actually
is, and which calls `WRITERS[suffix](obj)` and then writes the returned bytes — is never invoked with
a plugin suffix anywhere in the suite. Task 15's round-trip test likewise calls
`artifacts.WRITERS[".fastq"](...)` by hand rather than `io.write`. So "reaches `io.write`'s dispatch"
is proven one call frame short of `io.write`. **Fix:** one `StepIO.write` round trip over a plugin
suffix.

**The two mechanisms are distinct, and mutation (b) does discriminate — both re-verified.** Task 14's
refusal fires in `register_writer`'s decorator (`ContractError` · `E-PLUGIN-COLLISION`, registration
time); task 15's fires in `StepIO._read` (`ArtifactError` · `E-ARTIFACT-UNREADABLE`, read time). Two
types, two codes, two call sites, two messages, and no comment merges them — `register_writer`'s
docstring names the metadata half as the *other* arm, `_read`'s names neither, and `reference.md`
§ Creating a plugin (line 3432) spells out *"a different mechanism, a different time, and a different
code"*. The corrected sentence held. I re-ran mutation (b) (`if suffix in CORE_SUFFIXES:` →
`if suffix in WRITERS:`): with the appended second-registration assertion in place,
`test_a_suffix_core_does_not_write_is_accepted` fails on the second `@register_writer(".fastq")`
raising `ContractError`. The added assertion genuinely sizes the fixture for the mutation; the
report's account of it is accurate. Mutation (a) (private `_PLUGIN_WRITERS` table) also re-run: three
tests red.

### Task 15 — `register_reader` and the coded read-time refusal

**T15-A · Important · The reverse asymmetry is neither handled nor stated, while two texts read as
if it were.** Probed live: with `@register_reader(".fastq")` registered and **no** writer,
`_suffix_for("a.fastq")` returns `None` and `StepIO._read` returns `b'raw'` — the file silently reads
back as raw bytes and the registered reader is never reached, with no diagnostic. That may well be
the right behaviour, but the choice is nowhere stated, and two shipped sentences read as symmetric
claims over it: `_read`'s new docstring says the tables are *"an inversion only while the two hold
the same keys … so **the gap** is a coded refusal"* (there are two gaps; one is), and
`reference.md:1002` / `:3432` repeat *"an inversion only while the two hold the same keys"* while
only the writer-side key set is checked. This is the (b) shape — a docstring claiming a guarantee
broader than the code's — in a slice that has already shipped two Criticals of it. **Fix:** one
clause in `_read`'s docstring and in the § Errors row saying a reader with no writer is never
dispatched to and reads as bytes, deliberately, because `_suffix_for` is the single dispatch.

**T15-B · Minor · The `spec-defects.md` correction is right in substance, thin in form, and the
false clause was deleted rather than struck.** Three checks, as asked:
1. **Heading convention — partially.** The report's premise is correct: no `STRUCK` heading exists
   anywhere in the file, so the brief pointed at a heading that was never written, and renaming was
   the right instinct. But `## CLOSED 2026-08-17 — …` is a form the file does not otherwise use.
   `grep -n "^## .*CLOSED"` shows nine closed entries in three shapes — a suffix on the original
   heading (`… — CLOSED`, `— CLOSED by H7c`, five of them), `## CONFIRMED CLOSED (…)`, and
   `## CLOSED HERE:`. The prefix family exists, so this is not wrong, but the report's
   *"following the file's own existing convention"* overstates it: the exact form is new.
2. **The claim is now true.** The entry previously said `register_writer` would refuse *"a suffix
   that has no reader"* — registration-time — which is the reading this slice's first Critical
   corrected. It now says the refusal fires at the read, names `E-ARTIFACT-UNREADABLE`, and
   distinguishes task 14's core-suffix check under the same code. Both statements match the shipped
   code, verified against `_read` and `register_writer`.
3. **It describes what task 15 built** — yes, including the "not at registration, since a plugin may
   register the reader later in the same module" reason, which is the design's own.
   **The residue:** the false clause was *removed*, not struck-and-appended. `spec-defects.md` is the
   one file `CLAUDE.md` exempts from append-only correction, so this is defensible — but the
   evidence that task 3's specification claimed the wrong mechanism now survives only in
   `task-1-6-review.md`. Strike-through would have cost nothing.
   **Also minor, and here rather than as a verdict:** `register_reader`'s refusal is decided from
   `CORE_SUFFIXES = frozenset(WRITERS)` while its message says *"which core itself **reads**"* — an
   answer by proxy. Inert today (the two core tables hold identical keys) and arguably unavoidable
   since `_suffix_for` iterates `WRITERS` alone, but it is a `WRITERS` fact answering a `READERS`
   question.

**Mutations re-run.** (a) restoring `return READERS[suffix](path.read_bytes())` →
`test_a_suffix_with_a_writer_and_no_reader_is_a_coded_refusal` fails with `KeyError: '.fastq'`, the
original defect reproduced. Reverted, green. The symmetry deliverable itself is **confirmed by probe,
not by report**: a third-party writer registered without a reader now raises `ArtifactError` ·
`E-ARTIFACT-UNREADABLE`, and a suffix neither table knows still returns raw bytes. One caveat carried
into T14-B's family: both tests call the private `StepIO._read` directly, so the refusal is never
shown reaching a caller through `io.read_upstream`.

---

## The `PROBES` judgment

**Yes — `PROBES` is a fifth shipped-but-unread surface, and the answer is a filing, not a reader.**

`_check_probe` reads `BaseTemplate.apparatus_probe` against `plugins.names("publishable.probes")`,
which is the entry-point **metadata** scan. That is a reader for the **name**, and the report says so
in exactly those words. It is *not* a reader for the **registry**: `PROBES` is populated only when a
plugin module is imported, and importing one is precisely what `scan_group` must never do. So
"something reads the attribute" and "something reads the registry" are two different facts here, and
only the first is true.

The right resolution is a **filing with an owner**, not a reader. Building a reader for `PROBES`
means executing a probe, which is `Apparatus`, per-condition facts, the ledger and the change gate —
all H7d, explicitly out of scope in the design's § Out of scope. Shipping half of H7d to satisfy a
symmetry rule would be worse than recording the gap. But the filing must exist in
`docs/superpowers/spec-defects.md`, and today it does not: the brief's step 9 and the task report are
the development record, and `CLAUDE.md` is explicit that a ledger line is not a filing. `RESOLVERS`
is the same shape with a different owner (H7b Part B task 23) and is equally unfiled — one entry
naming both, with the two owners, closes T12-A and T13-B together.

Note that this makes the shipped-and-unread family **larger**, not smaller, than the
`spec-defects.md` amendment task 13 wrote: that amendment correctly narrows the *`BaseTemplate`
attribute* family to `field_convention` and `apparatus_facts`, but two module-level registries joined
the wider family in the same four commits.

---

## Checks that came back clean

- **The no-import invariant holds.** `scan_group` is unchanged in this range and still never
  `.load()`s. `_check_probe` reaches the metadata through `names()` → `scan_group()` and touches no
  class behind a name — the place the coordinator flagged as most likely to reach for the object, and
  it does not. The positive assertions are intact and unweakened: `git diff 5aad355..e3a1d96 -- tests/`
  is **pure insertion** (255 lines added, 0 deleted), so `tests/test_plugins.py`'s
  `assert "loadable_probe" not in sys.modules` (two sites) and `tests/test_templates.py`'s
  `"loadable_tpl" not in sys.modules` (four sites) are untouched.
- **No import cycle, and none latent.** `plugins.py` now imports `publishable.artifacts`;
  `artifacts.py` imports `coercion`, `errors`, `sweep`, none of which reaches back to `plugins`
  (grepped). `import publishable` succeeds and pulls in no heavyweight dependency — `pyarrow` stays
  behind function-local imports.
- **`E-DATA-RESOLVER-UNSUPPORTED` stays alive and is asserted alongside, never over a total code
  set.** Its emit site (`validate.py:3882`) is untouched by this range; the four assertions in
  `tests/test_validate.py` and `tests/test_materialize.py` are all `"E-DATA-RESOLVER-UNSUPPORTED" in
  codes(...)` / `in found`. Nothing here approaches Part B's retirement of it.
- **Registry isolation, on the correctness axis.** All four mappings these tasks add are snapshotted
  and restored in both directions; the template registry is correctly *not* in the fixture, since
  none of these four touches it. The two `_PROBING_TEMPLATE` validate tests register `probing`
  through a project-local `templates/` file in a `git_repo` tmpdir, i.e. through
  `templates/registry.py`'s per-call merge, so they leak no process-global name. The gap is
  T12-B — that none of this is pinned — not the fixture's content.
- **The `E-ARTIFACT-UNREADABLE` § Errors row** exists, sits beside the `E-ARTIFACT-UNWRITABLE` row,
  and states the neither-table case correctly.
- **`_check_probe`'s placement** is before the `c.credentials` line as the brief required, so its
  finding is still redacted at `render`; the `c.credentials` line was not moved.

## Out of scope, but worth the coordinator's eye

1. **`docs/reference.md:535`** — the `E-PLUGIN-COLLISION` row in § Errors `validate` reports still
   ends *"**Not yet emitted:** no task has landed the check this build makes over installed
   distributions."* `validate._check_plugin_collisions` iterates `GROUPS` and emits that code, and
   `validate_config` calls it unconditionally at line 638. The sentence entered at `24a56ff` (the
   tasks 1–6 review closure), so it belongs to the tasks 8–11 family rather than to these four — but
   it is live and false today.
2. **`.superpowers/sdd/.gitignore` was clobbered to a bare `*`** at some point in this range. I
   restored it from `HEAD` (the file is tracked, so nothing uncommitted was at risk).
3. **`task-12-15-report.md` is untracked** — it was created while the `.gitignore` was clobbered.
   Commit it with `git add -f`, along with this review.

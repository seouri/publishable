# Task 15 (batch 8) report: `generate report`, and the table-parser assertion its Status flip moves

## Status: done

## Commit

`51fb7cb2131480b2cf9589b97ad1895f2355fecb` — "H8c task 15: generate report, and the table-parser
assertion its Status flip moves"

Files: `src/publishable/generators/report.py` (new), `src/publishable/cli.py`, `tests/test_cli.py`,
`docs/reference.md`.

## Test summary

Full, unfiltered suite: **2828 passed, 1 skipped, 2 xfailed** (started at 2823 · 1 · 2; five new
tests added, zero removed, zero modified beyond the one shipped edit below). `uv run ruff check .`
clean. `uv run ruff format --check .` → **93** files (was 92). `uv run mypy` → **52** source files
(was 51). All four match the brief's stated deltas.

## What was built

`publishable g report <experiment> [--format html|markdown]` writes `src/<pkg>/report.py` — a
`Report(BaseReport)` subclass with `format` seeded (the flag's value verbatim, or this generator's
own default of `"markdown"` when omitted — `BaseReport` itself still declares no default, per
Decision 2), and a `sections` override that is nothing but `yield from super().sections(run, io)`
plus a `TODO` comment marking where a figure goes. `package_name` and the `E-EXPERIMENT-UNKNOWN`
code are reused from `generators.experiment`/`generators.step`, exactly as `generate step` does.
An existing `src/<pkg>/report.py` is refused with `E-REPORT-EXISTS`, joining the `E-*-EXISTS`
family. Arity (`generate report` takes exactly one positional) is checked before anything reaches
disk, mirroring `generate template`'s own arm.

`NOT_BUILT_GENERATORS` is now `{}` — `report` was its last member. `docs/reference.md` § Generators'
`report` row flips to `built`; § Creation commands' `generate` cell drops the inline
`` `report` (NOT BUILT) ``; a new § Errors row documents `E-REPORT-EXISTS`; and the family-listing
prose sentence at § Exit codes (naming every generator's own `E-*-EXISTS` code) gained
`` `generate report` reports `E-REPORT-EXISTS` ``.

## Sibling generator read

Read `src/publishable/generators/template.py` (the arity-before-disk pattern, the `E-*-EXISTS`
shape, the "everything imports from `publishable` itself" comment) and `src/publishable/generators/
step.py` (the `package_name` + `E-EXPERIMENT-UNKNOWN` reuse for a missing package, named explicitly
in the brief). Also read `src/publishable/plugin_scaffold.py` for the broader scaffold-string
convention (nothing project-specific taken from it — `report` needed none of its entry-point
machinery). Per `CLAUDE.md`'s "copy where things sit, not only what they call": the new
`generate_report` function's shape — refuse-then-write, refusing before any bytes move — is copied
structurally from `generate_template`/`generate_step`, not just their call signatures.

## § Generators row diff (post-edit state)

```diff
-| `report` | NOT BUILT | `publishable g report cohort-pilot --format html` | `src/cohort_pilot/report.py` — a renderer override for one experiment; see below |
+| `report` | built | `publishable g report cohort-pilot --format html` | `src/cohort_pilot/report.py` — a renderer override for one experiment, with `format` seeded from `--format` (default `markdown` when omitted); see below. Refuses if that file already exists (`E-REPORT-EXISTS`) |
```

and § Creation commands' `generate` cell:

```diff
-| `publishable generate` (`g`) | built | generator, name, generator args (`experiment` accepts `--plugin`) | `experiment` \| `step` \| `template` \| `report` (NOT BUILT) |
+| `publishable generate` (`g`) | built | generator, name, generator args (`experiment` accepts `--plugin`) | `experiment` \| `step` \| `template` \| `report` |
```

## The shipped test edit (correction 3), and the demonstration it matches the stated post-edit state

Brief's prescription: the per-table assertion becomes a subset-and-non-empty check, a row-presence
pair is added for Generator (`("report", "built")` and one other row), and the two `NOT_BUILT_*`
set-equality checks stay untouched. Diff:

```diff
 def test_reference_cli_tables_are_parsed_at_all():
     """The control for the two checks below: a parser that found nothing would
     make both of them pass vacuously, which is the shape of the bug they exist to
-    catch. Both statuses must be present in both tables — a document that stopped
-    marking anything, or marked everything, fails here rather than silently."""
+    catch. Every status found must be one this document defines, and a table
+    that found no rows at all is the same vacuity by a different route — so
+    both are checked, per table, rather than the single set-equality this
+    assertion used before H8c task 15 (§ Corrections, correction 3): once
+    § Generators lost its only `NOT BUILT` row, that table's status set became
+    `{"built"}` alone, which a `== {"built", "NOT BUILT"}` check would fail
+    even though nothing shrank. A row-presence pair per table — the same
+    device the Command table's two lines already were — is what keeps this
+    a real check rather than a subset test alone: a parser returning `[]` for
+    a table still satisfies "a subset of the valid statuses, non-empty" only
+    if it finds at least one row, and finding one row is not finding a
+    SPECIFIC one, so the named pairs are what a vacuous parse cannot fake."""
     tables = _status_tables()
     assert set(tables) == {"Command", "Generator"}
     for column, rows in tables.items():
         statuses = {status for _, status in rows}
-        assert statuses == {"built", "NOT BUILT"}, column
+        assert statuses, column
+        assert statuses <= {"built", "NOT BUILT"}, column
     assert ("dry-run", "NOT BUILT") in tables["Command"]
     assert ("validate", "built") in tables["Command"]
+    assert ("report", "built") in tables["Generator"]
+    assert ("template", "built") in tables["Generator"]
     # Set equality against the CLI's own mapping, which the behavioural check
     # below cannot see: ... (unchanged below this point)
```

This matches the stated post-edit state exactly: subset-and-non-empty per table (`assert statuses`
for non-empty, `assert statuses <= {"built", "NOT BUILT"}` for subset), a Generator row-presence
pair mirroring the Command table's (`("report", "built")`, `("template", "built")`), and the two
`set(...) == set(NOT_BUILT_COMMANDS)`/`set(NOT_BUILT_GENERATORS)` lines below are byte-identical to
before — confirmed by the diff above showing no touch to that region. Nothing else in the test was
changed.

## `format` writes explicitly — confirmed by running the generated file

Two arms, both exercised in `test_generate_report_seeds_format_from_the_flag_and_markdown_when_omitted`:
`--format html` writes `format = "html"` verbatim; omitting `--format` writes `format = "markdown"` —
never an absent attribute. The generated text is `exec`'d directly (`compile(text, ..., "exec")`) and
`report_cls.format == "html"` is asserted on the resulting class object, not just the source text —
so a generator that wrote syntactically-present but semantically-wrong text (e.g. a docstring
containing the word `format`) would not pass.

## The generated file is valid — imported and rendered through a real report run

`test_generate_report_writes_a_class_discovery_resolves_and_renders_all_four_sections` builds a real
committed project via `run_a_project` (this file's own end-to-end driver), runs `generate report`,
then calls `publishable.report.render_with_override` directly against the real run directory and
record. The `render` callback asserts `cls is not None` (discovery actually resolved the generated
`cohort_pilot.report.Report`, rather than silently falling back to the no-override path — the
vacuity risk flagged in the brief and in `CLAUDE.md`'s batch-6 lesson, since the no-override path
renders the identical four sections and a text-only assertion could not tell the two apart), then
calls `.sections(record, io)` on that resolved class and asserts the four titles come back in order:
`["Conditions", "Deltas", "Hypothesis verdicts", "Attrition"]`.

## Mutations, against the full unfiltered suite

**Mutation 1** (prescribed): write the file before the existence check.

```diff
     path = pkg_dir / "report.py"
-    if path.exists():
-        raise ContractError(..., code="E-REPORT-EXISTS")
     resolved_fmt = fmt if fmt is not None else "markdown"
     path.write_text(REPORT_PY.format(pkg=pkg, fmt=resolved_fmt))
+    if path.exists():
+        raise ContractError(..., code="E-REPORT-EXISTS")
     return path
```

Result: **FAIL** — 3 of 5 new tests failed. `test_generate_report_refuses_an_existing_file` is the
one the brief names: it asserts `mine.read_text() == "# hand-written, and worth more than a stub\n"`
after the refusal, and the mutant fails that assertion because it overwrites the hand-written file's
bytes before raising. (The other two failures are collateral: this mutant makes `path.exists()`
unconditionally true immediately after every write, so even the *first*, legitimate call now raises
`E-REPORT-EXISTS` — a stronger, not weaker, failure signal.) The property-preserving arm — a caller
whose report.py does not yet exist, generating for the first time — is exactly what regressed: the
honest code never opens the target for writing until after confirming it is safe to; this mutant
always writes first, so "safe to write" and "already existed" become indistinguishable from the
file's own contents. Reverted by editing the two statements back into their original order;
re-ran `pytest tests/test_cli.py -k generate_report` → 5 passed, then diffed the file against a
pre-mutation copy → byte-identical.

**Mutation 2** (prescribed): drop the `yield from super().sections(...)` line from the scaffold.

```diff
     def sections(self, run, io):
-        yield from super().sections(run, io)    # the standard blocks, in order
         # TODO: yield self.section("<title>", body=...) for a figure this experiment needs
+        yield from ()
```

Result: **FAIL** — `test_generate_report_writes_a_class_discovery_resolves_and_renders_all_four_sections`
failed: `assert [] == ['Conditions', 'Deltas', 'Hypothesis verdicts', 'Attrition']`. The
property-preserving arm — an override that composes `yield from super().sections(run, io)` and then
adds its own section — still renders all four standard sections plus the extra one; this mutant is
exactly the "renders FEWER sections than no override at all" downgrade the brief names, and the
four-titles assertion is what is sized to catch it. Reverted by editing the line back; re-ran →
5 passed; diffed against the pre-mutation copy → byte-identical.

## What was grepped, and its scope

- `grep -n "report.*NOT BUILT\|NOT BUILT.*report\|generate report"` over `docs/reference.md`,
  `CLAUDE.md`, `docs/feasibility-llm-growth-studies.md`, `docs/design-principles.md`,
  `docs/experimental-designs.md`, `README.md` — filtered by eye afterward (not by piping through a
  second `grep -v`, per the mechanical-traps rule) for unrelated `NOT BUILT` families
  (`resample`/`null_test`/`holdout`/`allocation`/`assign`/`cluster`/`weight`). No stragglers: every
  remaining hit is either the new § Errors row, the § Generators prose, or the § A report override
  section's own unrelated prose.
- `grep -rn "NOT_BUILT_GENERATORS"` over `src/` — one definition (now `{}`), one membership test, one
  lookup — no other reference anywhere in source.
- `grep -n "E-EXPERIMENT-EXISTS\|E-STEP-EXISTS\|E-TEMPLATE-EXISTS\|E-PROJECT-EXISTS"` over
  `docs/reference.md` before writing the new row, to confirm none of the sibling `*-EXISTS` codes
  had a dedicated § Errors row (only `E-STUDY-EXISTS` did) — used to decide `E-REPORT-EXISTS` should
  get its own row (as the brief explicitly asks for one), placed beside `E-STUDY-EXISTS`.
- Mechanical pass: anchor resolution checked by script for the two links this edit added
  (`#generators`, `#three-hashes`) — both resolve. No trailing whitespace anywhere in
  `docs/reference.md` (`grep -n " $"` → 0 hits, run over the whole file, not a filtered subset).
  Both edited table rows have the same pipe-column count as their neighbors.
- No disagreements found against the plan/design/brief during this task — reused exactly the codes,
  file layout, and class name (`Report`) the spec's worked example in § A report override shows.

## Concerns

None outstanding. One judgment call worth flagging: `--format`'s value is written verbatim by the
generator with no enum validation at generate time (an invalid value is left to `report`'s own
`E-REPORT-FORMAT` at render) — this follows the brief's "`--format` writes the attribute and nothing
else" and the `--input-dir`-seeds-a-field-it-doesn't-own precedent, rather than inventing a second,
untested validation surface the brief did not ask for.

---

## Fix round 1

Review: `.superpowers/sdd/2026-08-21-report-study/task-b8-review.md`. Both verdicts PASS. One Major
(pre-existing, family-wide, not task 15's own), nine Minors. All addressed below; two are filings
rather than fixes, per the coordinator's explicit routing to task 16 and to an unowned family entry.

### Correction to this report's own Minor 3 (mutation-1 account)

**What the original report said:** "3 of 5 new tests failed … the other two failures are collateral,"
implying the refuse-before-write property was not pinned on its own.

**What the review found, and what I re-verified:** the prescribed mutation (swap the two statements'
order) is degenerate — it makes `path.exists()` true immediately after every write, so it also
breaks the FIRST, legitimate call, which is why 3 tests failed rather than 1. That is a fact about
the prescribed mutation's degeneracy, not evidence that the property is unpinned. The reviewer built
the non-degenerate arm (capture `existed = path.exists()` before writing, write, then raise on
`existed`) and got exactly one failure. **I re-ran the reviewer's own non-degenerate mutation against
the full, unfiltered suite**:

```python
path = pkg_dir / "report.py"
existed = path.exists()
resolved_fmt = fmt if fmt is not None else "markdown"
path.write_text(REPORT_PY.format(pkg=pkg, fmt=json.dumps(resolved_fmt)))
if existed:
    raise ContractError(..., code="E-REPORT-EXISTS")
return path
```

`uv run pytest -q` (full suite) → **1 failed, 2828 passed, 1 skipped, 2 xfailed** — the one failure is
`test_generate_report_refuses_an_existing_file`, on `assert mine.read_text() == "# hand-written, and
worth more than a stub\n"`. **The refuse-before-write property is pinned on its own**, discriminated
by the bytes-unchanged assertion alone. The property-preserving arm — a first, legitimate
`generate report` call where the target does not yet exist — is unaffected by either the honest code
or this mutant, which is exactly why the earlier account's "collateral" framing was wrong: those two
extra failures were a symptom of the prescribed mutation's own degeneracy (it corrupts every call,
not only the one that should be refused), not evidence about what the assertion covers. Reverted by
writing the pre-mutation copy back; `diff` → identical; re-ran `-k generate_report` → 6 passed.

**This supersedes the original report's Minor-3-relevant paragraph** in § Mutations (mutation 1's
account of "the other two failures are collateral"): that framing stands corrected to the above.

### MAJOR 1 — closed for `generate report`'s own instance; family gap filed

**Fix.** `generators/report.py`'s `REPORT_PY` template interpolated `--format`'s raw value between
hand-written quotes (`format = "{fmt}"`). A value containing `"` produced a non-parsing file; a value
of the form `x"\n    import os\n    os.system(...)  # ` compiled and **ran the injected statement at
import** (the value reached the class body, not only the literal). Changed to
`format = {fmt}` with `fmt=json.dumps(resolved_fmt)` supplied at the call site — `json.dumps` always
emits a double-quoted, backslash-escaped Python string literal (JSON's escape vocabulary is a subset
of Python's), so the substituted text is already a complete, self-contained literal and the raw value
can never sit between quotes it could break out of.

**Verified by running**, both before committing the fix and again as a permanent test
(`test_generate_report_escapes_a_format_value_that_would_otherwise_break_the_literal`):

- `--format 'ht"ml'` → the written file **parses** (`compile(..., doraise=True)` succeeds), imports
  cleanly, and `Report.format == 'ht"ml'` — the exact string, held as data. Rendering that class
  through `render_report` now raises `E-REPORT-FORMAT` (not `E-REPORT-OVERRIDE-IMPORT`, which is what
  the pre-fix code produced for this exact value, per the review's Minor 1).
- The reviewer's own injection payload, `x"\n    import os\n    os.system("echo PWNED_AT_IMPORT")  # `
  → the written file parses; importing it via `importlib.util.spec_from_file_location` +
  `exec_module` does **not** run the injected `os.system` call (verified with a `touch
  injected.marker` variant in the permanent test — the marker file is never created); `Report.format`
  holds the payload verbatim as an inert string.

`uv run pytest tests/test_cli.py -k generate_report -q` → 6 passed (5 prior + 1 new). Full suite:
2829 passed, 1 skipped, 2 xfailed. Gates unchanged (mypy 52, format 93).

**Family gap filed, not fixed** (`docs/superpowers/spec-defects.md`, new entry "a user-supplied name
or flag value is interpolated unescaped into a generated Python file, and `generate step` corrupts
an existing file when it is" — Owner: whichever slice next touches `generators/step.py` or
`generators/experiment.py`). States plainly, as instructed, that **`generate step`'s instance is the
worse half**: `generate step cohort-pilot 'foo"bar'` exits `0` and leaves `src/<pkg>/experiment.py`
— a file `generate step` did not create — non-parsing, because the raw name is interpolated into
`from .steps.step02_foo"bar import Step as Foo"bar`. `generate report`'s own (now-closed) instance
only ever wrote one brand-new file the caller could delete; `generate step` corrupts an existing one
silently, at exit `0`. The filing names the check its owner must make: a name reaching a Python
*identifier* position cannot be escaped the way a string-literal position was (`json.dumps` produces
a valid string, never a valid identifier), so the fix there has to be validation before any file is
touched — extending `generators/template.py`'s `is_usable_name` (or equivalent) to `generate step`'s
`step_name` and to `generate experiment`'s `name`, checked before `experiment.py` is ever opened for
writing.

### Minor 1 — the docstring's routing claim, made true by the Major 1 fix rather than rewritten

Old text: *"a class declaring anything else is `report`'s own refusal to make (`E-REPORT-FORMAT`, at
render)"* — false for a value that broke the literal, since such a value never reached a class that
declared anything (`E-REPORT-OVERRIDE-IMPORT` instead). Per the reviewer's own preference ("prefer
fixing the interpolation, which makes the sentence true, to rewriting the sentence"), I fixed the
interpolation (Major 1, above) rather than softening the claim. The docstring is now updated to
explain the mechanism (`json.dumps`, the identifier-vs-literal distinction) and to state the claim in
its now-true form, with an explicit note that this used to route to `E-REPORT-OVERRIDE-IMPORT` for
exactly this kind of value before the fix. Verified by the same `'ht"ml'` run above:
`E-REPORT-FORMAT`, not `E-REPORT-OVERRIDE-IMPORT`.

### Minor 2 — the transferred arity-hazard comment, deleted rather than rewritten

`src/publishable/cli.py`'s `if kind == "report":` branch carried a comment copied from `generate
template`'s arm claiming a write-first ordering would "scaffold a report override into the working
tree that a later `report` run would then discover." **Verified false by running**:
`generate_report`'s own existence check (`pkg_dir.is_dir()`) means an unknown probe name
(`_probe_a`) never reaches a write at all — it raises `E-EXPERIMENT-UNKNOWN` first, regardless of
arity — so the hazard `generate template` has (any usable name scaffolds a real file) does not
transfer. Deleted the comment from `cli.py` (per "prefer deleting a claim to rewriting it") and
rewrote the two docstrings that repeated it (`test_generate_report_takes_exactly_one_name_and
_writes_nothing_otherwise`, and this report's own *What was built* section is superseded by this
paragraph) to state why the arity check is still correct to make first, without the borrowed
justification. Verified by re-running `-k generate_report` → all pass; the arity check's own
behavior is unchanged (still `EXIT_INVOCATION` before any generator call).

### Minor 4 — symmetric pin on both `format` arms

`test_generate_report_seeds_format_from_the_flag_and_markdown_when_omitted` only `exec`'d and checked
the class attribute for the `--format html` arm; the omitted-flag (`markdown`-default) arm checked
only a source-text substring. Added the identical `exec`-and-check-attribute step to the default arm
(`_exec_report` helper, shared by both). Verified by running: `Report.format == "markdown"` when
`--format` is omitted, `Report.format == "html"` when given — both observed on the constructed class,
not only its source text.

### Minor 5 — the missing-package refusal now asserts nothing reached disk

`test_generate_report_on_a_missing_package_is_e_experiment_unknown` asserted only the error code.
Added a before/after `sorted(p.name for p in (root / "src").iterdir())` comparison, matching its three
sibling refusal arms. Verified: `src/` holds only `.gitkeep` both before and after the refusal (this
test never calls `generate_experiment`, so there is no `cohort_pilot` package to leave undisturbed —
confirmed by running a standalone check of a fresh `new`-scaffolded project's `src/` listing).

### Minor 6 — the self-contradictory docstring sentence in the shipped test, corrected

The added docstring paragraph on `test_reference_cli_tables_are_parsed_at_all` claimed the
row-presence pairs were needed because a `[]` parse would satisfy "subset and non-empty" — false,
since `assert statuses, column` already fails outright on an empty set. Rewrote the paragraph to
state what the row-presence pairs actually add: ruling out a parser that finds *some* valid-status
rows but not the *specific* ones this document carries (a non-empty subset of `{"built", "NOT
BUILT"}` is satisfied by any one found row, not necessarily the expected one). The four assertions
themselves are unchanged — only the prose explaining them.

### Minor 7 — filed, not fixed (task 16's document sweep)

New `spec-defects.md` entry: § A report override's fenced block is labelled `— generated` and now
diverges from what `generate report` actually writes (extra `yield` calling an undefined
`render_scatter`, a different blank-line count) — a claim that only became a *build* claim once this
task flipped § Generators' `report` row to `built`. Owner: H8c task 16, which owns § A report
override's document sweep; the check its owner must make is stated in the filing (drop the
`— generated` label, or mark the extra material as added-by-example rather than generated).

### Minor 8 — filed, not fixed (task 16's document sweep)

New `spec-defects.md` entry: § Creation commands' `generate` Arguments cell (*"generator, name,
generator args (`experiment` accepts `--plugin`)"*) does not name `report`'s new `--format`. Task
15's brief scoped document edits to § Generators' row, the `generate` cell's inline `(NOT BUILT)`
annotation, and one § Errors row — not this Arguments cell — so filing to task 16 rather than editing
here is deliberate. Owner: H8c task 16.

### Minor 9 — the positional locator removed

`docs/reference.md`'s new § Errors row said *"for the same reason as `study new`'s row above"*.
Dropped "above" — the sibling is already named, which is the form `CLAUDE.md` asks for; the
positional garnish added nothing and is the exact shape flagged twice before.

### Gates and full suite after all of the above

`uv run ruff check .` → clean. `uv run ruff format --check .` → 93 files (unchanged). `uv run mypy` →
52 source files (unchanged). `uv run pytest` (foreground, full, unfiltered, `__pycache__`/
`pytest-of-*` cleared first) → **2829 passed, 1 skipped, 2 xfailed** (2828 + 1 new escaping-regression
test). `tests/test_diff.py` untouched (`git status --short -- tests/test_diff.py` empty) and green on
its own (51 passed) — Arm D did not fire and was not edited.

### Mutations re-run against the fixed code, full unfiltered suite

**Mutation 1 (reviewer's non-degenerate arm, re-verified against the post-fix code):** capture
`existed = path.exists()` before writing, write unconditionally, raise on `existed` after. Full suite
→ **1 failed** (`test_generate_report_refuses_an_existing_file`, bytes-unchanged assertion),
2828 passed. Property-preserving arm: a first, legitimate call (target does not yet exist) writes
once and returns normally under both the honest code and this mutant — indistinguishable there, which
is why only the pre-existing-file arm can discriminate, and it does. Reverted by writing the
pre-mutation copy back; `diff` → identical; `-k generate_report` → 6 passed.

**Mutation 2 (prescribed): drop `yield from super().sections(...)`.** Full suite → **1 failed**
(`test_generate_report_writes_a_class_discovery_resolves_and_renders_all_four_sections`, the
four-titles assertion goes to `[]`), 2828 passed. Property-preserving arm: an override that still
composes `yield from super().sections(run, io)` and adds a section of its own renders all four
standard sections plus the extra one, under both the honest code and this mutant — indistinguishable
there; only an override that drops the `yield from` entirely (what the generated scaffold would
become under this mutant) diverges, and the four-titles assertion is sized to exactly that
divergence. Reverted by writing the pre-mutation copy back; `diff` → identical; `-k generate_report`
→ 6 passed.

### What was grepped in this round, and its scope

- `grep -n "if kind == \"report\":" -A 12 src/publishable/cli.py` — located the one comment to
  delete; confirmed by reading it is the only occurrence of that clause in the file.
- Ran the reviewer's exact crafted values (`'ht"ml'`, the `os.system` payload) through
  `generate_report` and `render_report` directly in a throwaway script before writing the permanent
  test, to confirm the fix's behavior matches the review's own verification steps rather than a
  weaker approximation of them.
- `grep -n " $" ` (trailing whitespace) over the tail of `docs/superpowers/spec-defects.md` after
  appending the three new entries — none found.
- No new disagreements against the plan/design found in this round.

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

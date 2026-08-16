# Task 13 + 14 report

**Status:** both tasks complete, committed separately.

**Commits:**
- Task 13: `24e3a57` — docs: the owned prose sweep for the credential family, over named files
- Task 14: `dd08bb6` — docs: spec-defects filings for the credential family, with H7b-SCOPING § 11's routing corrected

**Tests:** 1994 passed, 2 xfailed — unchanged across both commits (matches task 12's baseline). `ruff check .`, `ruff format --check .` (76 files, 0 to reformat), and `mypy` all clean after each commit.

## Task 13 — sweep findings beyond the brief's table

The brief's disposition table named one `reference.md` site as "about the managed README region,
not this clause" and explicitly warned that a sweep trusting the table would read past the real
issue. The sweep found **two** sites the table did not name, both flagged correctly by that
warning:

1. `docs/reference.md` § The generated README — "`BaseTemplate.required_env` is declarable but
   read nowhere in `src/`" — false since task 9; `validate` reads it at `validate.py:776` and
   `cli.py:344`. Corrected to say the reader exists and only the merge is still missing.
2. `src/publishable/generators/template.py`'s comment claiming `required_env` is "read by nothing
   in this build" — same correction, plus a sentence explaining why the stub still omits the
   field (a stub value would satisfy `validate` trivially without teaching anything).

Also fixed a smaller staleness found in the same sweep: `validate.py`'s `_check_required_env`
docstring said `_check_requires_env` was "the next task in this slice" to add — stale since task
10 landed; now points at the sibling function directly rather than at a task number.

`design-principles.md`'s "Secrets are the one thing never captured" line was re-read against task
12 per the brief's instruction and given one added clause: it held by absence alone before this
slice (core read no environment variable at all), and is now backed by redaction at the two
serialization boundaries rather than by nothing ever reading `os.environ`.

Sweep mutation proof (step 7): all three confirmed to hit — `"publishable"` in the four documents,
`"BaseTemplate"` in `src/publishable/`, `"def test_"` in `tests/`.

Also restored `.superpowers/sdd/.gitignore`, found clobbered to a bare `*` before this task
started (per `CLAUDE.md`'s documented recovery — not something either task caused).

## Task 14 — re-measurements and filings

Re-ran both greps from the brief before writing anything: the credential-family grep over
`spec-defects.md` returned the same five pre-existing, unrelated hits (all `provenance.environment`
or `.env.example`-in-scaffold prose); the `H7c` grep returned zero, confirming no prior filing
existed for this family.

**Filed, all independently re-verified against the code (not the brief) on 2026-08-16:**

1. The README `credentials` region — reconfirmed absent from `scaffold.py`'s `README` constant
   (only `overview`/`experiments` regions exist), `docs` reconfirmed in `cli.NOT_BUILT_COMMANDS`.
   Carries the `H7b-SCOPING.md` § 11 routing correction.
2. Two unbuilt readers of `required_env` (`reproduce` step 6, `dry-run`) — both commands
   reconfirmed present in `cli.NOT_BUILT_COMMANDS`.
3. `BaseTemplate.field_convention` — reconfirmed two declarations, one stub comment, zero readers
   via grep; named as the surviving `CLAUDE.md` worked example now that `required_env` has a
   reader.
4. `io.reuse_from` — reconfirmed no prior `spec-defects.md` entry (grep hit nothing), filed fresh
   with unassigned owner.
5. **`PYTHON_DOTENV_DISABLED`** — confirmed by reading the installed `python-dotenv` package's
   `main.py` directly: it checks the variable and disables loading when truthy. Filed as a
   dependency property, not a fix, since removing or countering it would be its own behavior
   change.
6. **Dict-valued parameter → stale template-default credential report** — confirmed by reading
   `cli._flatten_parameters` and `cli.declared_credential_names`'s fallback
   (`resolved.get(path, param.default)`), and the identical shape in
   `validate._check_requires_env`. Filed as cosmetic (the `choices` constraint refuses the config
   regardless).
7. **`main`'s bare stderr handler** — confirmed the `except PublishableError as exc: print(f"...
   {exc}", ...)` handler is un-redacted by construction, and that the one demonstrated path into
   it (`template.validate(doc)` raising unguarded) was already closed by commit `cd72c3a` earlier
   in this slice. Filed as structural, with the reasoning for not fixing it (no config context in
   `main` to redact against).
8. **`min_items`/`max_items` not rendered** — confirmed by reading `Param.comment()`'s `list`
   branch: it returns only `f"list of {_TYPE_NAMES[self.item_type]}"`, never mentioning either
   bound, against `reference.md`'s documented `# list of float, 2 to 5 items` example.
9. **Positional reference "the table above"** — confirmed still present, unchanged by this slice,
   pre-existing and untouched by any H7c task.

All nine judged worth filing; none dropped. Re-owner sweep (step 6) found nothing pointing at "the
secrets slice"/"H7c"/"the credentials slice" to rewrite — there was no prior entry to re-owner.
Task 6's deferred obligation (step 7) discharged: `git diff 478c1f3 -- src/publishable/__init__.py`
is empty, confirming decision 8's "this slice exports nothing."

Mechanical pass on `spec-defects.md`: no heading-anchor collisions (checked programmatically
against all 165 `##` headings), no trailing whitespace or tabs in the new content, no en-dashes,
new tables both hold a consistent 2-column shape.

## Disagreements between the briefs/spec and the documents as they stand

None found. Both briefs' factual claims (site locations, commit pins, `NOT_BUILT_COMMANDS`
membership, the two disposition-table gaps task 13's brief flagged by name) checked out against
the current code and docs without needing correction to the brief or the spec itself.

## Concerns

None outstanding. Both commits are document-only; the test suite, lint, format, and type-check
gates are unchanged from task 12's baseline (1994 passed, 2 xfailed) across both commits.

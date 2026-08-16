# Tasks 5 & 6 — report

**Status:** both complete, both committed separately.

**Commits:**
- Task 5: `8e3a911` — `docs: requires_env stays out of the closed constraint table, and § Templates' present-tense claim is reconciled`
- Task 6: `f298aca` — `docs: the importable surface does not move — a subclass attribute and a Param keyword are not exports`

**Tests:** `uv run pytest` — 1964 passed, 2 xfailed (unchanged), `uv run ruff check .` clean, `uv run ruff format --check .` — 74 files already formatted, `uv run mypy` — no issues, all re-run after each commit.

## Disagreements found between the briefs/spec and the documents as they stand

- **Task 5 step 3's positional claim was correct as a diagnosis but the fix needed care.** The brief was right that "above" in "isn't in the closed vocabulary above" (§ A credential can belong to a parameter value) no longer points at the constraint table by position: a second table (the "Three states" `Declaration | Means | init writes` table, § Templates) sits between the constraint table and this sentence, so the nearest preceding table is the wrong one. Fixed per the brief's own instruction — named what the table *does* rather than where it sits, via an explicit link: `isn't in [the constraint table](#templates-where-parameters-are-defined)`.
- **Task 6's step 5 obligation is carried forward as instructed** — `git diff 478c1f3 -- src/publishable/__init__.py` was run now as a sanity check and is empty, consistent with decision 8, but the brief's own instruction is that task 14 is the authoritative place to record this, so I noted the obligation in the commit message rather than declaring it settled here.
- No other disagreement found: task 5's step 4 byte-identical claim was verified directly (`Param(...).comment()` run via `uv run python -c`, output matches the document's line character for character), and task 6's step 1 paragraph text and step 3's Status-column check both matched the document/code as read — no rewrite of the brief's prescribed language was needed beyond what the brief itself specified.

**No changes made to code, tests, or `secrets.py`'s `— not yet built` marker** (correctly deferred to task 7 per the ordering note).

## Correction (review, 2026-08-16)

Task 5 repaired one positional table reference and **introduced another in the same commit** — the new
§ Templates sentence ended "is not in **the table below**". The brief is what disagreed with itself:
its step 2 prescribes that text and its step 3 forbids the practice, and the disagreement went
unflagged. Now `[the constraint table](#templates-where-parameters-are-defined)`, mirroring the site
task 5 repaired.

Also narrowing this report's account of that repair: it says "the nearest preceding table is the wrong
one". The replaced phrase was "the closed vocabulary above", which named its referent **uniquely** —
so the reference was *fragile*, not wrong. The edit stands; the justification was stronger than the
facts.

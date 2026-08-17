# Tasks 5 & 6 — review

Reviewed `363cf31..2742188` (commits `8e3a911`, `f298aca`, `2742188`) on branch `h7c-credentials`.
Diff touches `docs/reference.md` (+6/−2 lines, two paragraphs and one sentence) and adds
`task-5-6-report.md`. Nothing else.

## Verdicts

| Task | Spec compliance | Task quality |
|---|---|---|
| 5 — `requires_env` stays out of the closed table; present-tense claim reconciled | **Pass** | **Pass with one Important finding** |
| 6 — § The importable surface records that this slice exports nothing | **Pass** | **Pass** |

## What was verified, and how

**1. The invariant task 5 guards — held.** The constraint table (`docs/reference.md` § Templates,
header `| Constraint | Applies to | Renders as |`) is byte-unchanged in the diff and still carries
exactly six rows: `choices`, the four bounds, `pattern`, the list trio, `nullable`, `help`. No
`requires_env` row. Grepped `requires_env` across the four documents and the feasibility analysis
(`README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`,
`docs/feasibility-llm-growth-studies.md`): every occurrence describes it as a credential
requirement or an explicit non-constraint; none calls it a constraint. The *reason* given ("it
constrains the environment a value may be used in rather than the value") is true against the code:
`Param.check()` in `src/publishable/param.py` reads `nullable`, `type_`, `choices`, the four bounds,
`pattern`, `item_type`, `min_items`, `max_items` — and never `self.requires_env`. The only
constructor-time checking of `requires_env` is a *declaration* check (needs `choices`, must be total
over them), which is not value checking. `Param.comment()` reads it only for rendering.

**2. Decision 8, task 6's claim — holds, and stays true through task 14.** `git diff 478c1f3 --
src/publishable/__init__.py` is empty; `__all__` in `src/publishable/__init__.py` is the eleven
pre-existing names. Forward check over the plan's tasks 7–14 code blocks: every `from publishable
import` line in them names only already-exported symbols (`BaseStep`, `BaseTemplate`, `Param`,
`register_template`); no task edits `__all__` or `__init__.py`; `secrets.py`'s `load_env` /
`missing_env` appear only as core-internal call sites (validate and the executing commands), never
as user-facing imports. Plan line 167 states this directly and task 14 step 7 carries the
discharging `git diff`. The paragraph's own claims are about `required_env` (a `BaseTemplate` class
attribute — confirmed at `src/publishable/templates/base.py:15` and
`src/publishable/templates/builtin/generic.py:9`) and `requires_env` (a `Param` keyword — confirmed
at `src/publishable/param.py:40`), both durable. **No later task falsifies this paragraph.**

**3. The deferred marker — not retired.** `docs/reference.md:3611` still reads
`│   ├── secrets.py             # dotenv loading, required_env checks (never touches provenance) — not yet built`,
and the diff does not touch § Package layout at all. Correct per the brief's ordering note; task 7
step 8 still owns it.

**4. The positional reference — fixed correctly, diagnosis slightly overstated.** Both halves
checked. *Second half (the fix):* the replacement reads `isn't in [the constraint
table](#templates-where-parameters-are-defined)` — names the table by what it *does*, and the anchor
is a heading, so it survives any further table insertion. *First half (was it wrong?):* partially.
The "Three states" table (`| Declaration | Means | init writes |`) does now sit between the
constraint table and the sentence, so "above" was fragile by position — but the original phrase was
"the closed vocabulary above", and "the closed vocabulary" names its referent uniquely inside that
section (only one thing there is called a closed vocabulary). So the reference was *fragile*, not
*wrong*; the report's "the nearest preceding table is the wrong one" overstates it. The edit is
still an improvement. Minor, and it lands on the report rather than the document.

**5. Every sentence added.** Three prose changes, each checked against something readable:
- "`Param` carries type, default, constraints, and help text" — matches `param.py`'s constructor and
  its module docstring.
- "the credential a chosen value requires … constrains the environment a value may be used in rather
  than the value" — matches `check()` not reading it (finding 1).
- "`required_env` is an attribute of a class you already subclass and `requires_env` is a keyword of
  a construct you already import, so declaring either adds no import line" — both confirmed at the
  source lines cited in finding 2.
- Task 5 step 4's byte-identity claim re-verified independently, not eyeballed: `uv run python -c`
  rendering `Param(str, default="azure_openai", choices=[...], requires_env={...}).comment()`
  prefixed with `# ` compares `True` against the document's YAML line, character for character. The
  constraint table's `choices` row still shows the unannotated `# choices: a \| b \| c`.
- No "still true" gloss appears in the document text. The one in the *report* is finding 4.

**6. Consistency passes — clean.** Mechanical over `docs/reference.md`, fenced blocks skipped: no
duplicate heading anchors; every `](#…)` target resolves (0 unresolved); no trailing whitespace, no
tabs, no NBSP/ZWSP/BOM/en-dash; every table row matches its header's column count once escaped `\|`
is discounted (the three apparent mismatches at lines 572, 1590, 3106 are all escaped pipes inside
cells), no empty rows. The two anchors this diff introduces were additionally checked **by hand**
against existing uses rather than trusted to a slugger:
`#a-credential-can-belong-to-a-parameter-value` is already used at `reference.md` 436, 471, 3485 and
`experimental-designs.md:382`; `#templates-where-parameters-are-defined` is already used in the
`BaseTemplate` and `Param` rows of the importable-surface table. Cross-document: **config
completeness** — `generic` declares no `requires_env`, no config field added, and § The one config
file's `analysis.method` line still reads `# choices: pearson | spearman | kendall` (matching
`README.md:172`); **enum comments** — the credential example's comment lists all three declared
choices; **declared-vs-derived** — nothing in the diff makes a derived value settable or vice versa.

**7. Scope — clean.** `git diff --stat 363cf31..HEAD` touches no `src/` and no `tests/`. `uv run
pytest` → **1964 passed, 2 xfailed** (unchanged). `uv run ruff check .` → all checks passed. `uv run
ruff format --check .` → 74 files already formatted. `uv run mypy` → no issues in 42 source files.

## Findings

### Important — task 5

**F1. The fix removed one positional table reference and the same commit introduced another.** The
new § Templates sentence ends "…and so is not in **the table below**". That is exactly the
locate-a-table-by-position habit `CLAUDE.md` records as its most-repeated (at least seven instances,
wrong twice), and it is fragile in exactly the way the sentence 60 lines down just had to be
repaired: § Templates holds two tables, and the constraint table is only "below" until something is
inserted between. It is correct today — the next table after the sentence is the constraint table at
line 1588 — so this is a latent defect, not a live error.

Two things make it reportable rather than excusable. First, **the brief contradicts itself**: step 2
prescribes that literal sentence while step 3 says "Do not locate it by position." The implementer
applied step 3's rule at the site step 3 named and copied step 2's text verbatim at the other,
without flagging the disagreement — and finding a disagreement is the expected outcome here, not the
exceptional one. Second, the same commit demonstrates the fix. Recommend mirroring the site already
repaired: "…and so is not in [the constraint table](#templates-where-parameters-are-defined)".

*Verified by:* reading `docs/reference.md` lines 1584–1596 and 1644, confirming two tables sit in
§ Templates between the sentence and the section end, and comparing against task 5 step 3's own
instruction in the brief.

### Minor — task 5

**F2. The report overstates the diagnosis it is proudest of.** "The nearest preceding table is the
wrong one" is true of *position*; but the phrase being replaced was "the closed vocabulary above",
which named its referent uniquely. The reference was fragile, not wrong. The edit is still right.
Recorded so the next reader of this ledger does not carry "the document pointed at the wrong table"
forward as a fact.

*Verified by:* reading the pre-image at `git show 363cf31:docs/reference.md` around § A credential
can belong to a parameter value against the section's heading structure.

**F3 (pre-existing, out of scope for both tasks — recommend a filing, not an edit).** The constraint
table's list row documents `Renders as` = `# list of float, 2 to 5 items`, but
`Param.comment()` returns only `list of float` — `min_items`/`max_items` are read by `_check_list`
and by nothing that renders. This is `CLAUDE.md`'s "assuming a documented rule has code behind it"
shape, inside the very table task 5 was guarding, and it is **not** in
`docs/superpowers/spec-defects.md`. Neither task's mandate reaches the row and scope forbids `src/`,
so this belongs in `spec-defects.md` (task 14 owns the filings) rather than in this diff.

*Verified by:* `uv run python -c` rendering
`Param(list, item_type=float, min_items=2, max_items=5, default=[1.0, 2.0]).comment()` → `list of
float`; grep of `min_items`/`max_items` across `src/` showing only constructor, storage and
`_check_list` sites.

### Minor — task 6

**F4. A one-line tension with the paragraph above it.** The new paragraph ends "this table
enumerates what you *import*", while the table deliberately carries `not yet built` rows that cannot
be imported today. The immediately preceding paragraph already disposes of this ("a promise, not an
export"), so no change is needed — noted only so a later editor does not read the two as
contradictory and "fix" one.

*Verified by:* reading `docs/reference.md` § The importable surface, the two adjacent paragraphs.

### Minor — neither task (housekeeping)

**F5. `.superpowers/sdd/.gitignore` had been clobbered to a bare `*`** by `scripts/sdd-workspace`,
as `CLAUDE.md` warns. Restored to its committed content during this review (`git show
HEAD:.superpowers/sdd/.gitignore`), which is the only file this review modified. Consequence to act
on: **this review file is new in that directory and needs `git add -f` to be tracked**, as does any
other record created while the clobber was live.

*Verified by:* `git diff .superpowers/sdd/.gitignore` before and after.

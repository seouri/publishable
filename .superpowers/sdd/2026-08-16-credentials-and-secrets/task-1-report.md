# Task 1 report — the two identifiers

**Status:** DONE
**Commit:** `5f416c1fbf89f184a56d90a4f07d9a37f8de0f28` — "docs: mint E-CRED-MISSING and E-CRED-PARAM-MISSING, with decision 1's grounds"
**Tests:** `uv run pytest` — 1957 passed, 2 xfailed (unchanged, as required for a document-only task). `ruff check` and `ruff format --check` clean (74 files formatted, 0 to reformat). `mypy` — no issues, 42 source files.

## What was done

Edited `docs/reference.md` only, exactly per brief:

1. Inserted the two rows verbatim (brief's exact text, unedited) into § "Errors `validate` reports"'
   `| Reported when | Code |` table, placed immediately after the `E-CONFIG-TYPE` row and before
   `E-DATA-ALLOCATION-CONTRAST` — the table is in strict alphabetical order by code
   (`E-CONFIG-* ... E-CRED-* ... E-DATA-*`), so that is the only slot consistent with the table's
   own ordering; I named it by the neighboring rows' content rather than by position.
2. Extended the existing sentence in § "A credential can belong to a parameter value" to record
   that the `requires_env`-totality check is `E-TEMPLATE-LOAD` and mints nothing of its own,
   exactly the text the brief specified.

## Verification performed

- **Re-read against what will emit each row (tasks 9/10/step 3):** `E-CRED-MISSING`'s row says
  "checked from the class alone, before any condition is expanded, and reported at
  `experiment_type`" — consistent with a template-level `required_env` list read off the resolved
  class. `E-CRED-PARAM-MISSING`'s row says "checked as the union over the conditions `expand`
  resolves" and "reported at the parameter's own dotted path" — consistent with a per-condition
  union over `Param(requires_env=)`. The two rows state genuinely different firing conditions (one
  needs only the template; the other needs a parameter, a value, and a selecting condition), so
  they cannot collapse into the `E-TEMPLATE-UNKNOWN` one-row-two-surfaces shape — the distinction
  decision 1 asks for is visible in the rows themselves, not just asserted.
- **§ Validation's three credential rows** (*Credentials present*, *Credentials a swept value
  needs*, *`requires_env` covers its choices*) — confirmed none carries a code, unchanged.
- **`grep -rn "E-CRED" src docs README.md`** — empty before the edit (step 1), and after the edit
  matches only `docs/reference.md` (the two new rows) — confirmed empty across `src/`, the other
  three documents, and `README.md`.
- **`requires_env` in `design-principles.md` / `experimental-designs.md`** — one mention each,
  neither naming a code, left untouched (task 13's).
- **Anchors resolve:** `#secrets--credentials` → `## Secrets & credentials`; verified this heading's
  slug empirically against the brief's own claimed slug (GitHub's slugger drops `&`, collapsing the
  two spaces around it into a double hyphen). `#a-credential-can-belong-to-a-parameter-value` →
  `### A credential can belong to a parameter value`. `#errors-validate-reports` → `### Errors
  \`validate\` reports` (backticks stripped by the slugger). `#expansion-modes` → `### Expansion
  modes`. All four headings exist via direct grep, no duplicates.
- **Mechanical pass:** each new row is exactly two `|`-delimited cells (verified pipe count: 6
  pipes across the 2 new lines = 3 each, correct for a 2-column row); no trailing whitespace, no
  tab, no en dash (only em dashes, which are house style) introduced. No count phrase near the
  insertion point references position ("five faults return... early," "every other row in this
  table fires only once all five have passed") needed updating — neither new code is among the
  five early-return faults, so both statements remain true unchanged.
- **`.superpowers/sdd/.gitignore` clobber:** `scripts/sdd-workspace`/`task-brief` had rewritten it
  to a bare `*` during this session (per the standing `CLAUDE.md` warning). Restored it from `HEAD`
  before committing; it is not part of this commit since it matched `HEAD` exactly afterward.

## Disagreements found between brief/spec and the documents as they stand

None. The brief's insertion point, exact row text, and the step-3 sentence all checked out against
the current `docs/reference.md` with no adjustment needed — the alphabetical-ordering placement was
the only judgment call, and it was unambiguous once verified against the surrounding rows' actual
order rather than assumed.

## Concerns

None. This task is document-only as the brief states; no `src/` or test change was in scope, and
none was made. Test count is unchanged at 1957 passed + 2 xfailed.

## Correction (task 1 review, 2026-08-16), replacing this report's stated placement justification

The report says the two rows were placed by the table's strict alphabetical ordering. **The table is
not strictly alphabetical** — the reviewer extracted all 119 codes and found seven out of order. The
*placement* is still correct, because the local `E-CONFIG-*` → `E-CRED-*` → `E-DATA-*` run is
alphabetical and that is the run the rows join. Only the reason given was wrong, and a wrong reason
for a right answer is what sends the next reader looking for an ordering that is not there.

Two further corrections, both to text the plan supplied rather than to the implementer's execution:

- `E-CRED-PARAM-MISSING`'s row claimed *the message* names the parameter. It does not — task 10's
  message names the value, the condition and the variable, and the parameter arrives in the finding's
  `path` field, which `Collector.render()` prints on its own line. Reworded to say the finding carries
  the parameter and the message names the value and the condition. Decision 1's grounds are untouched:
  they rest on the two messages being unshareable, which value-and-condition alone already establishes.
- Both rows located their sibling by position ("the row above" / "the row below") — the habit
  `CLAUDE.md` bans and which the brief itself invoked one step earlier for the insertion point. Both
  now name the sibling code.

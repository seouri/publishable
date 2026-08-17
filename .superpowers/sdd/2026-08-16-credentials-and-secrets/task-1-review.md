# Task 1 review — the two identifiers

**Reviewed:** `5f416c1` against `d75e6ba` (`docs/reference.md`, +3 −1).
**Commands run:** `uv run pytest` → **1957 passed, 2 xfailed** (unmoved). `uv run ruff check .` →
all checks passed. `uv run ruff format --check .` → 74 already formatted, 0 to reformat.
`uv run mypy` → no issues, 42 source files.

## Verdicts

1. **Spec compliance — ✅.** The two rows are the brief's text verbatim, in § Errors `validate`
   reports' `| Reported when | Code |` table, adjacent, in the alphabetically correct slot; the
   step-3 sentence is the brief's text verbatim in § A credential can belong to a parameter value.
   Decision 2 is honoured — no third code, no third row. Decision 1's grounds are legible in the
   rows. Nothing outside `reference.md` changed.
2. **Task quality — ❌.** Three findings: one Important claim disagreement between row 2 and the
   check task 10 will build (originating in the brief's supplied text, not in the implementer's
   execution), one Important convention violation the brief itself warned about one step earlier,
   and one Important false justification in the task report. The mechanical pass is clean.

---

## Findings

### Important 1 — row 2 says the *message* names the parameter; task 10's message does not

`docs/reference.md:466`: "Reported at the parameter's own dotted path, **and the message names the
parameter, the value, and the condition that selected it**".

**Verified three ways.**
- `docs/superpowers/plans/2026-08-16-credentials-and-secrets.md:1839-1844` — the emitted message is
  `f"is \`{value}\` in {where}, which requires \`{variable}\` — no value in the environment or in
  \`.env\`"`. The parameter appears only in the `path` argument, `f"parameters.{path}"`.
- `src/publishable/diagnostics.py:40-44` — `Collector.render()` prints `path` on one line and
  `message` on the next. They are two fields; the message string is what task 10 pins by fragment.
- The plan's own test comment at line 1702-1703 concedes it: *"The three facts this code's message
  must name and the other one cannot: the parameter (**via `path` above**), the value, and the
  condition."*

**Why it matters rather than being a nit.** This clause is the visible half of decision 1's grounds
— the reason two codes exist. Left as written, task 10 must either ship a message that contradicts
its own § Errors row, or pad the message with a parameter name the path already carries. Decision 1
survives untouched on *value* and *condition* alone (row 1's message can name neither), so the fix
costs nothing: "Reported at the parameter's own dotted path, and the message names the value and
the condition that selected it — with the path, the three facts a reader needs …".

**Not a finding, checked and closed:** "the parameter's own dotted path" describing the emitted
`parameters.llm.provider` is the repo's existing convention, not a discrepancy —
`src/publishable/validate.py:728,731` emit `E-PARAM-VALUE`/`E-PARAM-MISSING` at
`f"parameters.{path}"` identically. Do not reopen this.

**Also not a finding:** § Validation's row at `docs/reference.md:265` names parameter, value and
condition in one string. That column is *Example failure*, not a message format, and needs no
change when row 2 is corrected.

### Important 2 — both new rows locate their sibling **by position**

`docs/reference.md:465`: "Distinct from **the row below** in what it can name".
`docs/reference.md:466`: "a second emit site of **the row above**, whose message can name none of
them."

**Verified** by `grep -n "row above\|row below\|next row\|following row\|preceding row\|two rows"
docs/reference.md` — 465 and 466 are the only two hits inside this table that do not name their
sibling by code (476's "`E-DATA-ASSIGN-RATIO`'s row below" names it, and is unaffected by the
insertion).

`CLAUDE.md` § Habits that cost real work: *"Locating a table row by position … at least seven
instances, wrong twice … Name what a sibling row does."* The brief applies the identical rule one
step earlier — step 2: *"Locate the insertion point by naming the row you put them after — do **not**
describe it by position."* Both clauses are true today, so this is fragility rather than falsehood;
but see Important 3 — the table is **not** strictly alphabetical, so "these two will always be
adjacent" is not a property the table guarantees. A future `E-CRED-PAIR-*` between them falsifies
both clauses at once. Fix is two clause rewrites naming the sibling code.

### Important 3 — the report's placement justification ("strict alphabetical order") is false

`task-1-report.md` line 12-14 claims "the table is in strict alphabetical order by code … so that
is the only slot consistent with the table's own ordering."

**Verified** by extracting every code from the table (header `docs/reference.md:459`, 119 rows,
lines 461–579) and comparing consecutive pairs. **Seven rows are out of alphabetical order**, all in
the holdout/fold region: `E-DATA-HOLDOUT-FRAC` after `-METHOD` (485), `-FOLD` after
`-STRATIFY-UNKNOWN` (490), `-VALUES` after `-VARIES` (492), `-STRATIFY-VARIES` (493), `-EMPTY`
(494), `-CELLS` (495), and `E-DATA-CLUSTER-CONTRAST` after `E-REPL-FOLD-CELLS` (497).

**The placement is nonetheless correct** — the local run `E-CONFIG-KEY-UNKNOWN … E-CONFIG-TYPE →
E-CRED-* → E-DATA-ALLOCATION-*` is alphabetical, and it is also the topical slot. Only the *stated
reason* is wrong. Recorded because this repo grades claim accuracy and a report is read as evidence
by the next slice.

### Minor 1 — "before any condition is expanded" is true at this commit and pinned by nothing

`docs/reference.md:465`. **Verified true** by reading `src/publishable/validate.py:485-573`:
`load_env(repo_root)` (task 8) → template resolution → `_check_required_env` immediately before
`_check_parameters` (line 571); the only `expand(doc)` calls are in `_check_sweep`,
`_condition_labels` and task 10's own check, all later. It reads as explanatory (the check needs no
expansion) rather than as an ordering guarantee, and task 9 step 7 explicitly declines to pin
finding order. Left as a note, not a required change.

### Minor 2 — the development record is not tracked for this task

`git status --short` shows `.superpowers/sdd/.gitignore` clobbered to a bare `*` **right now**, and
`git ls-files .superpowers/sdd/2026-08-16-credentials-and-secrets/` returns `progress.md` only —
`task-1-report.md` is untracked. The report says the file was restored before committing; it has
been clobbered again since (`scripts/task-brief`). Restore `.gitignore` from `HEAD` and `git add -f`
the report and this review, per `CLAUDE.md` § The development record.

---

## What was checked and found clean

- **Row 1 against task 9** (plan lines 1394-1589). Every clause verified against the code that task
  will write: `required_env` read off the class via `getattr` (1522); path `"experiment_type"`
  (1529); one `c.error` per variable from `missing_env`, which answers *in declared order and
  dedupes* (task 7 test, plan 1745-… / 955-…); the message names the template and the variable and
  says to put the value in `.env` at the repository root, and **never the value** (1530-1532);
  `.env` loaded from the repository root before the check, `override=False` so a shell value wins
  (task 7 step 2 test `test_a_shell_value_wins_over_the_file`, task 8 step 3).
- **Row 2 against task 10** (plan lines 1592-1895), other than Important 1. Union over
  `expand(doc)`'s conditions (1806-1835); `first_seen.setdefault` gives "reported once, attributed
  to the first condition that selected it" (1835); `requires_env.get(value)` returning `None` for a
  value with no key, with the `ablate.remove` → `null` reasoning quoted in the docstring
  (1792-1797). `reference.md:1607` independently confirms `sweep.ablate.remove` sets a nullable
  parameter to `null`.
- **Decision 2, verified in the code rather than from the spec.** `src/publishable/param.py:34-35`
  raises a bare `ValueError` for `default=None` without `nullable=True`, inside `Param.__init__`, so
  it fires while a `templates/*.py` class body executes at import.
  `src/publishable/templates/discovery.py:316-334` catches that with a deliberately broad
  `except Exception` and re-raises `ContractError(code="E-TEMPLATE-LOAD", …"raised while importing
  and registers nothing usable")`; `validate.py:517-522` reports it under the code the raise
  carries. Corroborated by an existing test — `tests/test_templates.py:808-811`, a module-scope
  raise asserted as `E-TEMPLATE-LOAD`. The added sentence is true, and no third code was minted
  (`grep -rn "E-CRED" docs/ README.md src/` excluding the development record returns exactly the two
  new rows).
- **One row per code, no second emit site later.** `grep -n "E-CRED"` over the whole plan: task 9 is
  the sole `c.error("E-CRED-MISSING", …)` site and task 10 the sole `c.error("E-CRED-PARAM-MISSING",
  …)` site. Every other hit is a test assertion or prose. Neither code will need a second row.
- **Count phrases.** "Five faults return `validate_config` early" (`reference.md:428`) is unaffected
  — neither new code is an early-return fault. "Every other row in this table fires only once all
  five have passed" (432) stays **true** of both: each is checked after template resolution
  succeeded. `validate.py:519`'s "two today" comment (task 2's) is untouched and still true. No
  prose anywhere counts the table's rows, so the row count moving 117 → 119 falsifies nothing.
- **No positional reference falsified by the insertion.** The only in-table positional phrase below
  the insertion, `reference.md:476` ("`E-DATA-ASSIGN-RATIO`'s row below"), names its target by code
  and its target is still below it.
- **Mechanical pass on `docs/reference.md`, fences skipped.** Zero trailing-whitespace, tab or
  invisible-unicode lines. Zero duplicate heading anchors. All four new anchors resolve to real
  headings — `#secrets--credentials` → `## Secrets & credentials` (GitHub drops `&`, leaving the
  double hyphen), `#a-credential-can-belong-to-a-parameter-value`, `#errors-validate-reports`,
  `#expansion-modes`. Table column counts: the only three mismatches in the file (lines 567, 1583,
  3100) are pipes inside inline code, and **all three sit outside both diff hunks** (465–466 and
  1626) — pre-existing, untouched. Both new rows are exactly two cells. No en dash where a hyphen
  belongs.
- **Scope.** No `-UNSUPPORTED` code, no "Temporary:" framing, no retired refusal in either new row.
- **Cross-document.** `E-CRED` appears in `reference.md` alone; `requires_env`'s single mention in
  each of `design-principles.md` and `experimental-designs.md` is untouched (task 13's). No worked
  example value, config field, enum comment or version number moved.

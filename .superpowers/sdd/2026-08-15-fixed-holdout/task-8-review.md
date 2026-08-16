# Task 8 review — the shared cells refusal (`_check_evaluation_split_cells`)

Reviewed `review-6e87092..44e232c.diff` (commits `fa6accc`, `44e232c`) against `task-8-brief.md`,
`task-8-report.md`, `CLAUDE.md`, and `task-7-review.md`.

Working tree restored after every mutation by editing the file back — **no `git checkout --` on any
source file** — with a backup in the scratchpad, `__pycache__` deleted, and each revert verified by
**re-running** (`diff` against the backup reports IDENTICAL; the six new tests pass; `git status`
clean only as a secondary check). Measured myself at `44e232c`: `uv run pytest` → **1878 passed, 2
xfailed**; `uv run ruff check .` clean; `uv run mypy` clean (42 source files).

Also restored `.superpowers/sdd/.gitignore`, found clobbered to a bare `*` again.

## Verdicts

1. **Spec compliance: ✅** — `_check_evaluation_split_cells` is the brief's Step 3(a) verbatim,
   wired immediately after `_check_holdout` with the brief's comment; the six tests are Step 1
   verbatim; the `spec-defects.md` entry is Step 3(d) with one accurate correction. Steps 3(b) and
   3(c) were genuine phantom edits — task 2 had already written both passages, and I verified that
   independently (concern 3 below).
2. **Task quality: ✅** — with one Important finding. The refusal is correct, the code is attributed
   by mutation to this site alone, and the documents already carry it. What is missing is a single
   test row: the `and groups` **emptiness** half of the `cells` predicate is load-bearing —
   the documents specify it in three places as "a *non-empty* `sweep.groups`" — and nothing in 1878
   tests proves the code honours it. That is one row, not a class of defect, and it is the only
   thing between this task and a clean bill; the four consecutive tasks' pattern of dead checks does
   **not** recur here.

---

## Adjudication of the three disclosed concerns

### Concern 1 — the co-reported `E-DATA-ALLOCATION-*` codes: **does not weaken attribution. No finding.**

CLAUDE.md's rule is that a refusal which happens to fire must be attributed before it is counted.
It is attributed here, three ways:

- **Verified by mutation.** Inserted `return  # MUTATION` as the first statement of
  `_check_evaluation_split_cells`. All **five** trigger tests failed
  (`..._a_fold_beside...`, `..._a_holdout_beside...`, `..._both_split_kinds...`,
  `..._allocation_between_alone...`, `..._a_group_axis_alone...`); only the control passed.
  Reverted in place, re-ran, 6 passed.
- **Verified by grep.** `E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` each have exactly one
  occurrence in `src/publishable/` (both in this new function). No other site can produce them.
- No assertion in any of the six tests rests on `E-DATA-ALLOCATION-NO-ARMS` or
  `E-DATA-ALLOCATION-WITHIN-ARMS`; they are merely present in the finding set. They are also the
  *expected* consequence of the two single-spelling fixtures — a `between` with no arms axis, and a
  group axis with `within` — so their presence confirms the fixture is the shape the test claims.

### Concern 2 — `if units.get("holdout"):` versus `_check_holdout`'s `isinstance(...) and`: **reachable, and acceptable. No change owed.**

**Verified by probe** (throwaway test, since deleted): `holdout: "random"` beside
`allocation: between` yields `['E-CONFIG-TYPE', 'E-DATA-HOLDOUT-CELLS',
'E-DATA-HOLDOUT-UNSUPPORTED']` — so validation does continue past `E-CONFIG-TYPE` and the
divergence is real, not hypothetical. It is nonetheless acceptable:

- The divergence is confined to **truthy non-mappings**. On `{}`, `null`, and an absent key the two
  gates agree, and a truthy non-mapping is exactly what `E-CONFIG-TYPE` owns and the reader must fix
  first regardless.
- **Shipped precedent on the same key:** `_check_unimplemented` already uses a bare
  `if units.get(field):` and already stacks `E-DATA-HOLDOUT-UNSUPPORTED` on that same malformed
  value. Matching it is consistency, not divergence.
- `reference.md` § Errors' `E-DATA-HOLDOUT-CELLS` row says "`data.units.holdout` **is declared**
  beside …", which is true of a bare string. No document is contradicted.

This is unlike task 7's `E-DATA-HOLDOUT-EMPTY` case, where the stacked finding was a *second
substantive verdict about the same value* computed from a value already refused. Here the second
finding is about a **different declaration pair**, and it is correct on its own terms.

### Concern 3 — "task 2 already wrote the prose and both § Errors rows": **true, verified independently. One report inaccuracy (Minor finding 3).**

Read against every emit site this diff creates:

- § Errors carries **one row per code**, and each covers **both** cell spellings and both emit
  paths: the `E-DATA-HOLDOUT-CELLS` row and the `E-REPL-FOLD-CELLS` row each say "declared beside
  `data.units.allocation: between` or a non-empty `sweep.groups`", and the fold row names the
  identical check site. Nothing this diff emits is undocumented, and nothing documented lacks a site.
- § Validation carries *One split, not one cell each* for the combination, and *Folds fit inside the
  cells* is already marked superseded by it — so the two rows do not give two answers.
- `reference.md` § A fixed holdout split's fourth interaction and § Cross-validation's
  "Under `allocation: between`, a roster-wide fold is refused rather than drawn within each cell"
  both state the refusal. `experimental-designs.md`'s "Every cell is a condition" paragraph states
  it too.
- The reworded spec-defects sentence — the documents "both now name the refusal this entry documents
  and record drawing the split **within** each cell as the design that would lift it" — is
  **accurate** against both files as they stand. The brief's original sentence ("both prescribe
  drawing the split within each cell") would have been false. The rewording is right.
- Sweep of my own, by claim: `grep -rn "per cell\|within a cell\|inside the cell\|each cell"` over
  the four documents returns nothing that asserts a within-cell draw this build performs.

---

## Findings

### 1. Important — the `and groups` emptiness half of the `cells` predicate is unpinned, and it refuses an otherwise-valid config when broken

`cells = allocation == "between" or bool(isinstance(groups, list) and groups)`. The brief's
mutations (a) and (b) pin the two **disjuncts** against each other. Nothing pins the **emptiness**
guard inside the second disjunct — no test in the repo declares `sweep.groups: []`.

**Verified by mutation.** Changed the line to
`cells = allocation == "between" or bool(isinstance(groups, list))`:

- `uv run pytest` → **1884 passed, 2 xfailed** (1878 + 6 probes of mine). Whole suite green.
- Probe on the shape that separates the readings — a holdout, `attributes: [arm]`, no `allocation`,
  `sweep: {groups: [], grid: {analysis.method: [pearson, spearman]}}`:
  - at `44e232c`: `['E-DATA-HOLDOUT-UNSUPPORTED']` — correct, no cells refusal;
  - mutated: `['E-DATA-HOLDOUT-CELLS', 'E-DATA-HOLDOUT-UNSUPPORTED']` — an otherwise-valid config
    refused for a cell structure it does not declare.

Reverted in place; `diff` against the scratchpad backup IDENTICAL; the six tests re-run and pass.

This is not a stylistic gap: **all three document sites specify the emptiness restriction** —
§ Validation's *One split, not one cell each*, and both § Errors rows, each say "a **non-empty**
`sweep.groups`". The code honours a rule the documents state and the suite cannot see. This is the
repo's own recurring shape — "a dimension no assertion can see" — arriving one clause deeper than
the brief's mutations reached.

**Remedy: one row.** A holdout beside `sweep: {groups: [], grid: …}` asserting
`"E-DATA-HOLDOUT-CELLS" not in codes(path)`. Add the `grid` (or accept `E-SWEEP-EXPANDS-EMPTY`
alongside): `groups: []` with no other axis expands to nothing and earns its own refusal, which
would make the control roster-incidental in exactly the way CLAUDE.md warns about.

### 2. Minor (note, not actionable) — the three `isinstance` guards are unreachable from `validate_config`

`isinstance(groups, list)`, `isinstance(repeats, list)` and `isinstance(level, dict)` are defensive
against a malformed config that **cannot arrive** at this function.

**Verified by probe + mutation.** Deleting `isinstance(level, dict) and` from the `any(...)` left
`uv run pytest` at 1884 passed with **no crash** on a `repeats: ["fold"]` config. I then replaced the
function's first statement with `raise RuntimeError("REACHED")`: the three malformed-shape probes —
`repeats: {…}` (not a list), `repeats: ["fold"]` (level not a mapping), `sweep.groups: "arm"` (not a
list) — **did not raise**, because each earns `E-CONFIG-SHAPE` and `validate_config` returns before
this check. (The bare-string `holdout` probe *did* raise: `E-CONFIG-TYPE` does not stop validation,
`E-CONFIG-SHAPE` does.) So `validate` cannot crash here, no test can pin the guards, and no finding
is owed — recorded so it is not re-derived, as task 7's finding 12 did for its own untestable branch.
Reverted; re-verified by re-running.

### 3. Minor — the report overstates what `experimental-designs.md` says

The report writes that `experimental-designs.md`'s "Every cell is a condition" paragraph "already
states the refusal (`E-REPL-FOLD-CELLS`, `E-DATA-HOLDOUT-CELLS`)". **Verified by grep**:
`grep -n "HOLDOUT-CELLS\|REPL-FOLD-CELLS" docs/experimental-designs.md` returns **nothing**. The
paragraph states the refusal in prose and links `reference.md` § A fixed holdout split; it names
neither code. Nothing is wrong with the document — codes belong in `reference.md` § Errors, and the
cross-reference is the house pattern — but the report's parenthetical claims a check it did not
make, and the next reader consulting that file for the codes will not find them.

### 4. Minor — Step 4's `ruff format --check` is unreported, and this task's lines are among the would-reformat hunks

The report claims `ruff check` and `mypy` clean (both confirmed by me) but never mentions
`ruff format --check`, which Step 4 explicitly requires. **Verified by running it**:
`uv run ruff format --check src/publishable/validate.py tests/test_validate.py` → "2 files would be
reformatted", and `--diff` shows the hunks include this task's own additions — `_cells`'s
`"allocation": "between", "assign": {…},` line and four of the six new tests' call sites. Same
disposition as task 7's finding 10: the repo is broadly not format-clean, so this is not a gate
failure, but the step was skipped rather than run and judged.

### 5. Minor — `E-REPL-FOLD-CELLS`'s message doubles its verb

The shared `reason` string starts "is declared beside …", so the fold branch renders:

> replication.repeats **declares** a `fold` level, which **is declared** beside
> `data.units.allocation: between`, which divides the roster into cells. …

**Verified by probe** (message printed via `messages_by_code`). Cosmetic, and the price of the one
shared string that makes the two messages provably the same reason — worth a clause reword
(`f"declares a \`fold\` level, {reason_body}"`) only if this function is touched again.

### 6. Note, no finding — docstring and comment honesty holds throughout

Checked every claim in the new docstring and the wiring comment:

- "Knowable from the declarations alone — no roster, no resolution — so this takes neither" — the
  signature is `(doc, units, c)`; the body reads `units.get("allocation")`, `doc["sweep"]["groups"]`,
  `units.get("holdout")`, `doc["replication"]["repeats"]` and nothing else. **True.**
- The four precedent codes — `E-DATA-WEIGHT-CONTRAST`, `E-DATA-CLUSTER-CONTRAST`,
  `E-DATA-ALLOCATION-CONTRAST`, `E-DATA-ASSIGN-BLOCKED-CLUSTER` — each have exactly one emit site in
  `src/publishable/` (**verified by grep**), and each refuses a combination while honouring both
  declarations. **True.**
- "`E-DATA-HOLDOUT-CELLS` and `E-REPL-FOLD-CELLS` send a reader to the declaration they actually
  wrote" — paths are `data.units.holdout` and `replication.repeats`. **True.**
- "A second check *site* is what this deliberately does not have" — one site, confirmed by the
  single-occurrence grep in concern 1. **True.**
- The `fold` half was live: **re-verified myself** — the fold-only cells config now reports exactly
  `['E-REPL-FOLD-CELLS']`, and the implementer's pre-implementation run reported the empty set.
- `test_both_split_kinds_…`'s "`E-DATA-HOLDOUT-FOLD` rides along" — **verified by probe**: that
  config's codes are `['E-DATA-HOLDOUT-CELLS', 'E-DATA-HOLDOUT-FOLD', 'E-DATA-HOLDOUT-UNSUPPORTED',
  'E-REPL-FOLD-CELLS']`. **True.**
- `_cells`'s "15 units, 12 in arm `a` and 3 in arm `b`" — `'b' if i >= 12 for i in range(15)` gives
  3 and 12. **True.**
- The control's docstring is the honest one this repo has been asking for: it says outright that
  `E-DATA-HOLDOUT-UNSUPPORTED` is **not** positive attribution and that a control over a check which
  correctly reports nothing cannot prove itself. That is exactly the correction task 7's finding 3
  demanded, applied before the review rather than after. Its "differ from it only in the cell
  structure" is loose — the control also omits `assign` — but `assign` is *entailed* by
  `allocation: between` (§ Validation, *Allocation needs arms*), so the claim holds in substance.
- "task 18's retirement" — **verified against the plan**: Task 18 is "Retire
  `E-DATA-HOLDOUT-UNSUPPORTED`, and the five end-to-end pins". Correct (task 7's review said 17 and
  was wrong on that detail).

### 7. Note, no finding — the spec-defects entry

Present, appended, headed `## OPEN — an evaluation split cannot be drawn within a cell`. It names
**H3c-3** — a slice, not a person and not "whichever slice does X" — and adds the re-ownership
instruction CLAUDE.md asks for. Its description matches what the code refuses: both split kinds,
both cell spellings, one site, two codes. The `OPEN` heading beside "now closed as a refusal rather
than as a capability" is coherent rather than contradictory: the *capability* gap is open, the
*silently-wrong* defect is closed.

---

## Mutation ledger

| Mutation | File | Result |
|---|---|---|
| `cells = … or bool(isinstance(groups, list))` (drop `and groups`) | `validate.py` | whole suite green (1884 passed); probe config gains a spurious `E-DATA-HOLDOUT-CELLS` → **finding 1** |
| drop `isinstance(level, dict) and` from the `any(...)` | `validate.py` | 1884 passed, no crash → **finding 2** |
| `raise RuntimeError("REACHED")` as first statement | `validate.py` | three malformed-shape probes never entered the function → **finding 2** |
| `return  # MUTATION` as first statement | `validate.py` | all 5 trigger tests failed, control passed → **attribution confirmed, concern 1 closed** |

Every mutation reverted by editing the file back and verified by `diff` against a scratchpad backup
plus a re-run of the six tests. Final state: `diff` IDENTICAL, `ruff check` clean, `mypy` clean,
`git status` clean.

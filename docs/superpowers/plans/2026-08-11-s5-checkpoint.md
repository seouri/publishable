# S5 Checkpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** resolve `docs/superpowers/spec-defects.md` into the four documents, so the reference implementation and its specification describe the same tool.

**Architecture:** Sixteen tasks across nine slices, drawn by **which document section is edited** rather than by which ledger entry closes. Tasks 3–9 touch only `docs/`; tasks 10–14 touch only `src/` and `tests/`; tasks 1–2 and 15–16 are controller and verification work. The two groups are independent, so a `docs/` task and a `src/` task can never conflict.

**Tech Stack:** Python 3.12, `uv`, pytest, ruff, mypy. Markdown for the four documents.

## Global Constraints

- **The four documents are `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`.** Nothing else is normative. `docs/feasibility-llm-growth-studies.md` is exempt from the cross-document pass and subject to the mechanical pass in full.
- **No pinned worked-example figure changes anywhere in this plan.** `CLAUDE.md` § The worked example pins every number; the delta `0.026`, the interval `[−0.007, 0.059]`, the threshold `0.02`, `r = 0.581` / `0.607` / `0.412`, `240`/`228`/`12`, `repeat_spread` std `0.014`, and the hash prefixes `8e21` / `1a2b` / `3d8a` / `6b1f` / `2f5c8d0`. "Those intervals were checked numerically … and must not be narrowed back."
- **The `-UNSUPPORTED` policy is restated, not re-litigated.** A `-UNSUPPORTED` code stays out of the four documents and retires with the slice that implements its feature. 14 live codes are covered. Do not add rows for them.
- **`×`, not `x`, for multiplication**, including inside fenced blocks.
- **Hyphen, never an en dash, in anything that becomes a filename or an anchor.**
- **Cite another file by section** — `reference.md` § "Package layout" — never by line number.
- **Prose style is declarative and reason-giving:** state the rule, then why it exists. Tables carry the dense material.
- **`docs/superpowers/` is gitignored.** Nothing under it appears in any commit or any diff. A task whose only output is a file there produces an empty `git diff` — that is expected, not a failure.
- **Every `E-`/`W-` identifier that `src/` emits must have a test producing it.** Adding a document row does not create that obligation; it already exists.
- Commands: tests `uv run pytest`, lint `uv run ruff check .`, format `uv run ruff format .`, types `uv run mypy`.

---

## File Structure

**Documents modified (tasks 3–9):**

| File | Sections this plan touches |
|---|---|
| `docs/reference.md` | § Errors core raises, § Validation, § The importable surface, § Package layout, § Statistical reporting, § How artifacts are organized, § Steps and artifacts, § Pre-registration, § `Estimate`, § The two files, § Exit codes and diagnostics, § The one config file |

`README.md`, `docs/design-principles.md` and `docs/experimental-designs.md` are read by task 16's cross-document pass but are not expected to change. If a task finds a contradiction in one of them, that is a finding for task 16, not a silent edit.

**Code modified (tasks 10–14):**

| File | Responsibility | Change |
|---|---|---|
| `src/publishable/correction.py` | Correction families, ranking, corrected bounds | `Member` gains a declaration index; `rank_family`'s tie-break uses it |
| `src/publishable/validate.py` | Collects findings, never raises | An `except SystemExit` arm beside the entrypoint import |
| `src/publishable/units.py` | `Unit`, roster resolution | `Unit.__setattr__` and a read-only attribute mapping raising `E-UNIT-IMMUTABLE` |
| `src/publishable/cli.py` | Assembles `UnitTable` for `aggregate` | Threads declared unit attributes into the table |
| `src/publishable/stats.py` | Pure statistics | No change; task 14 only pins existing behaviour with a test |

**Controller artifacts (tasks 1, 2, 15, 16), all gitignored:**

- `docs/superpowers/spec-defects.md` — amended in place by tasks 1 and 2
- `docs/superpowers/CHECKPOINT-AGENDA.md` — read-only input, produced by the audit

---

## Task 1: Amend the eleven stale ledger claims

**Files:**
- Modify: `docs/superpowers/spec-defects.md`
- Read: `docs/superpowers/CHECKPOINT-AGENDA.md` § Staleness findings

**Interfaces:**
- Consumes: nothing
- Produces: a ledger whose headings can be trusted by tasks 2–16. Every later task reads this file.

**This task produces no commit.** `docs/superpowers/` is gitignored. Do not attempt to `git add` its contents; verify by re-reading the file.

**Why amend in place rather than file new entries:** five of these eleven were already closed by a later entry that never touched the earlier heading. Filing a twelfth entry is what created the staleness. Each amendment goes **at the stale entry's own heading**, as an indented `**AMENDED 2026-08-11:**` line immediately under it, naming the closing entry's line number *and* the module and function that closes it — the line number goes stale, the function name does not.

- [ ] **Step 1: Amend the five heading-level stale entries**

At each heading in `docs/superpowers/spec-defects.md`, insert directly beneath it:

```markdown
**AMENDED 2026-08-11 (S5 checkpoint audit):** FALSE at HEAD. <text below>
```

| Heading at line | Amendment text |
|---|---|
| 715 `read_upstream can only reach run-scoped steps` | Fixed in S3b task 7, recorded at entry line 901. `artifacts.py`'s `read_upstream` resolves per target scope — `run`/unknown to `run_dir/shared`, `summary` to `run_dir/summary`, otherwise the caller's own condition directory via `condition_dir_name`, then `_nest_repeat`. The hard-coded `shared/` path this entry describes is gone. **The "MARKED FOR THE NEXT SLICE" marker is withdrawn.** |
| 1557 `percentile_over_units is unguarded` | The floor landed; `stats.py`'s `percentile_over_units` returns `None` below two values and below `min_honest_draws(confidence)` draws. Closed by entry line 1779. The entry's *second* claim — "nothing in production calls it" — is **still true**, because `statistics.resample` is refused by `E-STATS-RESAMPLE-UNSUPPORTED`. |
| 1637 `max_ineligible_fraction moves from S4b to S4c` | It is read: `cli.py` reads `limits.max_ineligible_fraction` and warns `W-DATA-INELIGIBLE`. Closed by entry line 1752. The entry's other two claims **survive**: `min_clusters` and `min_units_per_cell` appear nowhere in `src/` and remain unread behind refused features. |
| 1646 `W-STATS-FAMILY counts a baseline comparison per condition even with no baseline` | `validate.py`'s `_check_statistics` computes the family as `len(resolve_contrasts(doc, conditions))`, not `len(conditions) - 1`, and fires only for `correction: none` over a non-empty family. Closed by entry line 1678. |
| 1664 `statistics.contrasts is absent from _check_shape's nested pass` | `validate.py`'s `_check_shape` now carries a `statistics` branch refusing a non-list `contrasts` **and** a non-list `report_by` as `E-CONFIG-SHAPE`. Closed by entry line 1794. **The residue moves to entry 1794**, which is headed `RESOLVED` and is therefore invisible to a reader scanning headings: `contrasts.resolve_contrasts` itself is still unguarded against an unhashable side. |

- [ ] **Step 2: Amend the two understated entries**

| Heading at line | Amendment text |
|---|---|
| 150 `runner.py is missing from § Package layout` | **Understates the divergence by 6×.** `docs/reference.md` § Package layout omits six shipped modules, not one: `runner.py`, `coercion.py`, `contrasts.py`, `correction.py`, `estimate.py`, `strata.py`. It also omits `templates/registry.py`. Its closing sentence "No other module built in S1 diverges from the layout table" is true only of S1. Owned by task 5 of this plan. |
| 2054 `The importable surface names five things __init__.py does not export` | **Miscounted, and one claim is false.** `__all__` holds nine names; the § The importable surface table names **seven** that are absent — `Unit`, `Apparatus`, `BaseReport`, `register_template`, `register_resolver`, `register_probe`, `register_writer`. The parenthetical "`register_template` is the only one of the four core actually ships today" is **false**: `grep -rn "def register_" src/publishable/` returns nothing. The template registry is `get_template`/`template_names` in `templates/registry.py`; there is no `register_template` decorator. **Zero** of the four registries exist. The reverse direction is clean — nothing is exported that the table does not name. |

- [ ] **Step 3: Amend the four now-false record entries**

| Heading at line | Amendment text |
|---|---|
| 279 `E-RUN-SEED-MISSING`, `E-STEP-RETURN-TYPE` | Now in the registry. `E-RUN-SEED-MISSING`, `E-RUN-CFG-MISSING`, `E-RUN-ORDER-MISMATCH`, `E-REPL-ORDER-UNRESOLVED` and `E-RUN-FOLD-UNRESOLVED` are all in `reference.md` § Errors core raises' last row. Closed at entry lines 927 and 1094. |
| 598 `E-RUN-CFG-MISSING belongs in the registry` | Now in the registry — same last row of § Errors core raises. Closed at entry line 927. |
| 1206 `E-STEP-COLUMN-UNKNOWN` "not yet done in this pass" | Landed. The row is in `reference.md` § Errors core raises; recorded at entry line 1515. |
| 2472 `A non-numeric aggregate return may reach float() uncontained` | **Not reachable**, but the containment is incidental. The closure routes through `coerce_scalars`, which accepts `str`, so this entry's suspicion that a `str` is refused upstream is wrong. Every call site sits inside an `except Exception` whose docstring justifies it **only** as degenerate-draw handling — `percentile_of_derived`, `paired_delta_of_derived`, `paired_percentile_of_derived` in `stats.py`, and the strata path in `cli.py`. A template returning `{"m": "high"}` yields `ci95: null`, `W-STATS-AGGREGATE-FAILED`, and a `str` in the metric's `value`. **No test pins this**, so a plausible future narrowing of those handlers reopens the path with nothing failing. Pinned by task 14 of this plan. |

- [ ] **Step 4: Reassign the orphaned slice name**

At the S4d residue entry (line 2009), under the row deferring a test to **S4e**, insert:

```markdown
**AMENDED 2026-08-11 (S5 checkpoint audit):** `S4e` names a slice
`docs/superpowers/specs/2026-08-08-implementation-spine-design.md` § The slices does not define —
it runs S1–S5 and then "hardening slices". This deferral has no owner. Reassigned by task 16 of
`docs/superpowers/plans/2026-08-11-s5-checkpoint.md`.
```

- [ ] **Step 5: File the finding the ledger never recorded**

Append a new entry at the end of `docs/superpowers/spec-defects.md`:

```markdown
## `E-UNIT-IMMUTABLE` is documented and implemented nowhere

Found by the S5 checkpoint audit, 2026-08-11 — not by any slice.

`docs/reference.md` names it twice: in § Errors core raises ("a write through a frozen `Unit`"),
and in § The unit list is three operations, and the units in it are frozen, which spends a
paragraph on why — the roster is resolved once per run and shared across every condition, so
`unit.attributes["scored"] = True` would edit what the next condition sees, and core cannot inspect
a step's body to catch it. The document states the object refuses instead, "raising `ContractError`
· `E-UNIT-IMMUTABLE` at the write".

`grep -rn E-UNIT-IMMUTABLE src/ tests/` returns nothing. `units.py`'s `Unit` is
`@dataclass(frozen=True, eq=False)`, so `unit.key = "x"` raises `dataclasses.FrozenInstanceError` —
no `.code`, and not a `PublishableError`, so `main()` does not catch it and the user gets a bare
traceback. `attributes` is a `MappingProxyType`, so the document's own example
`unit.attributes["scored"] = True` raises `TypeError`, also uncoded.

**Decision (C1 decision 2, settled by the user 2026-08-11): implement the coded refusal.** A
documented identifier that nothing raises is the class this repo says must not exist. Owned by
task 12 of `docs/superpowers/plans/2026-08-11-s5-checkpoint.md`.
```

- [ ] **Step 6: Verify**

Run:

```bash
grep -c "AMENDED 2026-08-11" docs/superpowers/spec-defects.md
grep -c "^## " docs/superpowers/spec-defects.md
```

Expected: **12** amendments (5 + 2 + 4 + 1 orphan reassignment), and **99** `##` entries (98 plus the new `E-UNIT-IMMUTABLE` entry).

There is no commit for this task.

---

## Task 2: The decisions record

**Files:**
- Modify: `docs/superpowers/spec-defects.md` (append one entry)
- Read: `docs/superpowers/specs/2026-08-11-s5-checkpoint-design.md` § C1, `docs/design-principles.md`

**Interfaces:**
- Consumes: task 1's amended ledger
- Produces: nine settled decisions, each naming its transcribing task. Tasks 3–9 and 12 read this entry and transcribe it; **none of them re-decides.**

**This task produces no commit** — same reason as task 1.

**A decision left open is a task 3–9 blocked mid-flight.** The deliverable is checked for nine answers before task 3 starts.

- [ ] **Step 1: Append the decisions entry**

Append to `docs/superpowers/spec-defects.md`:

```markdown
## S5 checkpoint decisions record

Nine decisions gating the transcription tasks of
`docs/superpowers/plans/2026-08-11-s5-checkpoint.md`. `design-principles.md` is the tiebreaker.
Decisions 2 and 3 were settled by the user on 2026-08-11.

| # | Decision | Ruling | Grounds | Transcribed by |
|---|---|---|---|---|
| 1 | Where the 13 unnamed `W-` codes live | § Validation gains a diagnostics table, shaped like § Errors core raises' | A warning is a diagnostic carrying an identifier a user greps. A separate registry file has no precedent in the four documents, and § Exit codes and diagnostics already promises that a command prints the identifier beside the message — the table it points at must exist | Task 4 |
| 2 | `E-UNIT-IMMUTABLE` | Implement the coded refusal | **Settled by the user.** A documented identifier nothing raises is the class this repo says must not exist | Task 12 |
| 3 | "the complete parameter set" | Narrow the phrase | **Settled by the user.** The code route changes what `init` writes, which is `parameter_spec`-driven — the single-source-of-truth invariant. Three of the four missing `statistics` blocks are still refused features | Task 6 |
| 4 | `supported: null` | § Pre-registration states three verdict states and both routes to the third | A `false` there is indistinguishable from a claim tested and failed — the same confusion `verdict_evaluated_on` exists to prevent one level up. The two routes are an observation core cannot resolve, and a bound test against an absent interval | Task 8 |
| 5 | Unbuilt names in § The importable surface | Keep them, marked unbuilt | The table is the enumerated normative surface, and `reference.md` calls it "the promise". Deleting the four `register_*` rows would delete the plugin contract four hardening slices build against | Task 5 |
| 6 | Reserved metric names | § Steps and artifacts states the reserved set, currently `{by}` | `statistics.report_by` spends `by` as a column name. A user learns this today only by collision, and § Steps and artifacts is where the flat-mapping return contract already lives | Task 6 |
| 7 | A `run`- or `condition`-scoped step's return | State that it is not recorded | A wide scope has no unit and no repeat to key a value by, so there is nowhere for it to land. Inventing a `results` block would add a record with no denominator — the failure mode the "per-request measurements in a side report" trap already names | Task 6 |
| 8 | `Config.raw` | § The importable surface states that the root node carries one accessor and nested nodes carry none | A top-level config key named `raw` is shadowed today. That is a real narrowing of "dot-access with no methods at all", and an invariant with an undocumented exception is worse than one with a documented one | Task 5 |
| 9 | Finding order | Amend the sentence, not the code | § Exit codes promises config-position order; `validate` collects by check. Ordering by document position needs position tracking threaded through every check — a hardening change with its own tests, not a checkpoint one | Task 6 |
```

- [ ] **Step 2: Verify nine answers are present**

Run:

```bash
awk '/^## S5 checkpoint decisions record/,0' docs/superpowers/spec-defects.md | grep -c "^| [0-9]"
```

Expected: **9**. Every row's "Ruling" cell must be non-empty and must not contain "TBD", "decide", or "open".

There is no commit for this task.

---

## Task 3: § Errors core raises — the raise-time `ContractError` rows

**Files:**
- Modify: `docs/reference.md` § Errors core raises
- Read: `src/publishable/replication.py`, `scope.py`, `artifacts.py`, `units.py`, `coercion.py`, `generators/step.py`

**Interfaces:**
- Consumes: task 2's decisions record (none of the nine bear on this task, but read it so you do not re-decide anything)
- Produces: a § Errors core raises table that names every raise-time `ContractError` the run-time surface can produce. Task 4 adds the warnings table beneath it; task 16 checks both.

**The table's own framing decides membership, and it excludes one of the twelve.** § Errors core raises says it "covers exactly the run-time surface, where there is a step to raise into", and that every row but the last is "something your declarations or your step code asked for". `E-STEP-EXISTS` is raised by `src/publishable/generators/step.py` when `generate step` would overwrite a file — a creation command refusing, with no step to raise into. **It does not belong in this table.** It belongs in § Exit codes and diagnostics, which task 6 owns. Do not add a row for it here.

That leaves eleven rows for this table.

- [ ] **Step 1: Read each raise site and record its actual condition**

For each identifier, read the `raise ContractError(...)` and the surrounding branch. Write the condition down before writing the row. **A row stating the wrong condition is worse than a missing row** — a missing row is a known gap, a wrong row is a false promise.

```bash
for c in E-REPL-SEED-COLLISION E-STEP-NAME-COLLISION E-STEP-SCOPE-UNKNOWN \
         E-STEP-SCOPE-ONLY E-STEP-UNIT-UNKNOWN E-STEP-UNIT-SETTLED \
         E-STEP-UNITS-CONTRACT E-STEP-READ-CONDITION-UNKNOWN \
         E-STEP-READ-REPEAT-REQUIRED E-STEP-ESTIMATE-CI95 E-STEP-ESTIMATE-VALUE; do
  echo "=== $c"; grep -rn -B12 "\"$c\"" src/publishable/ | grep -v __pycache__
done
```

- [ ] **Step 2: Add the rows**

Insert into § Errors core raises' table, grouped by the module they come from, above the final self-check row (the one carrying `E-RUN-SEED-MISSING`). Each row follows the table's existing shape — a prose "Raised by" cell with anchor links, and a `Type · code` cell. Use these, adjusting the wording only if step 1 shows the condition differs:

```markdown
| A [repeat level](#repeat-kinds) whose derived seeds or whose rendered labels are not distinct across its repeats | `ContractError` · `E-REPL-SEED-COLLISION` |
| Two [steps](#steps-and-artifacts) in one experiment sharing a name, or one whose `scope` is not one of the four | `ContractError` · `E-STEP-NAME-COLLISION`, `E-STEP-SCOPE-UNKNOWN` |
| [`io.record`](#the-unit-table-is-the-inference-base) naming a unit the roster does not hold, or naming one this execution has already recorded or skipped | `ContractError` · `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED` |
| An [`io` accessor](#step-scope) reached from a scope that does not have it | `ContractError` · `E-STEP-SCOPE-ONLY` |
| Indexing [`io.units`](#the-unit-list-is-three-operations-and-the-units-in-it-are-frozen) outside the roster's range | `ContractError` · `E-STEP-UNITS-CONTRACT` |
| [`io.read_condition`](#steps-that-need-every-condition) naming a condition index the sweep did not expand, or omitting a repeat where the run resolved more than one | `ContractError` · `E-STEP-READ-CONDITION-UNKNOWN`, `E-STEP-READ-REPEAT-REQUIRED` |
| An [`Estimate`](#estimate-carries-your-interval-without-core-claiming-it) whose `ci95` is not two numbers in ascending order, or whose `value` is not a number | `ContractError` · `E-STEP-ESTIMATE-CI95`, `E-STEP-ESTIMATE-VALUE` |
```

The `E-STEP-ESTIMATE-*` row sits beside the existing `E-STEP-ESTIMATE-SCOPE`, `E-STEP-ESTIMATE-METHOD` row.

- [ ] **Step 3: Verify every anchor resolves**

Every `#anchor` used above must match a heading in `docs/reference.md`. Run:

```bash
python3 - <<'PY'
import re, sys
text = open('docs/reference.md').read()
body = re.sub(r'```.*?```', '', text, flags=re.S)          # skip fenced blocks
heads = {re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-')
         for h in re.findall(r'^#{2,6} (.+)$', body, re.M)}
bad = sorted({a for a in re.findall(r'\]\(#([a-z0-9-]+)\)', body) if a not in heads})
print("UNRESOLVED:", bad or "none")
sys.exit(1 if bad else 0)
PY
```

Expected: `UNRESOLVED: none`, exit 0.

- [ ] **Step 4: Verify the row/column counts and the identifier coverage**

```bash
python3 - <<'PY'
import re
text = open('docs/reference.md').read()
body = re.sub(r'```.*?```', '', text, flags=re.S)
for i, line in enumerate(body.splitlines(), 1):
    if line.strip().startswith('|') and line.strip().endswith('|'):
        pass  # column-count check runs in task 15 over the whole file
named = set(re.findall(r'E-[A-Z0-9-]+', text))
want = {"E-REPL-SEED-COLLISION","E-STEP-NAME-COLLISION","E-STEP-SCOPE-UNKNOWN",
        "E-STEP-SCOPE-ONLY","E-STEP-UNIT-UNKNOWN","E-STEP-UNIT-SETTLED",
        "E-STEP-UNITS-CONTRACT","E-STEP-READ-CONDITION-UNKNOWN",
        "E-STEP-READ-REPEAT-REQUIRED","E-STEP-ESTIMATE-CI95","E-STEP-ESTIMATE-VALUE"}
print("MISSING:", sorted(want - named) or "none")
print("E-STEP-EXISTS present (should be False here):", "E-STEP-EXISTS" in named)
PY
```

Expected: `MISSING: none`. `E-STEP-EXISTS` may be `True` only if task 6 has already run.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "docs: name eleven raise-time ContractErrors in the errors registry"
```

---

## Task 4: § Validation — the diagnostics table for the thirteen unnamed warnings

**Files:**
- Modify: `docs/reference.md` § Validation
- Read: `src/publishable/diagnostics.py`, `src/publishable/validate.py`, `src/publishable/cli.py`

**Interfaces:**
- Consumes: task 2's decision 1 — the warnings live in a diagnostics table in § Validation, shaped like § Errors core raises'
- Produces: a table naming all 18 `W-` codes `src/` emits. Task 6 splits § Validation's *existing* table's validate-time/run-time blur; **that is a different table** — do not do task 6's work here.

**These thirteen are unnamed today.** Verified by `comm` against the four documents:

`W-DATA-INELIGIBLE`, `W-ENV-UNLOCKED`, `W-EXEC-BUDGET`, `W-HYPOTHESIS-INFERENCE-BASE`, `W-REPL-FLOOR`, `W-STATS-CONTRAST-THIN`, `W-STATS-CORRECTED-THIN`, `W-STATS-CORRECTION-INAPPLICABLE`, `W-STATS-REPORTBY-THIN`, `W-STATS-STRATUM-SHADOWED`, `W-STATS-STRATUM-THIN`, `W-STEP-ESTIMATE-N`, `W-TEMPLATE-VERSION`.

- [ ] **Step 1: Confirm the set against `HEAD` before writing rows**

```bash
comm -23 <(grep -roh "W-[A-Z0-9-]*" src/ | grep -v __pycache__ | sort -u) \
         <(grep -oh "W-[A-Z0-9-]*" docs/*.md README.md | sort -u)
```

Expected: exactly the thirteen above. If the set differs, the code moved since this plan was written — write rows for what the command prints, and note the difference in your report.

- [ ] **Step 2: Read each emit site and record its actual condition**

```bash
for c in W-DATA-INELIGIBLE W-ENV-UNLOCKED W-EXEC-BUDGET W-HYPOTHESIS-INFERENCE-BASE \
         W-REPL-FLOOR W-STATS-CONTRAST-THIN W-STATS-CORRECTED-THIN \
         W-STATS-CORRECTION-INAPPLICABLE W-STATS-REPORTBY-THIN W-STATS-STRATUM-SHADOWED \
         W-STATS-STRATUM-THIN W-STEP-ESTIMATE-N W-TEMPLATE-VERSION; do
  echo "=== $c"; grep -rn -B8 "\"$c\"" src/publishable/ | grep -v __pycache__
done
```

Write each row's condition from the code, not from the identifier's name. **The identifier's name is a label, not a specification** — `W-STATS-CORRECTED-THIN` fires when the draw pool cannot meet the floor the *corrected* level demands, which is not what "thin" alone conveys.

- [ ] **Step 3: Add the table**

Add to `docs/reference.md` § Validation, after its existing content, a subsection:

```markdown
### Warnings core reports

A warning is a [diagnostic](#exit-codes-and-diagnostics), not an exception: nothing raises one and
nothing catches one. It carries a stable `W-` identifier for the same reason an error carries an
`E-` one — a message gets clearer over time, and something pinned to the wording breaks when it
does. A warning never changes an exit code; it changes what the record says core was unsure of.

Each row states the condition, not the wording.

| Reported when | Code |
|---|---|
| … one row per identifier, condition written from the emit site … | `W-…` |
```

Fill every row from step 2. Group them by prefix — `W-DATA-`, `W-ENV-`, `W-EXEC-`, `W-HYPOTHESIS-`, `W-REPL-`, `W-STATS-`, `W-STEP-`, `W-TEMPLATE-` — and include the five already-named codes so the table is the complete set rather than a supplement. Move their prose mentions to point at it rather than duplicating the condition.

**`W-ENV-UNLOCKED` gets a row and a note.** It fires on every scaffolded run until `publishable` is published to an index a lockfile can resolve. That is bootstrapping, not a defect — say so in the row, so a reader hitting it on their first run knows it is expected.

- [ ] **Step 4: Verify every `W-` code is now named**

```bash
comm -23 <(grep -roh "W-[A-Z0-9-]*" src/ | grep -v __pycache__ | sort -u) \
         <(grep -oh "W-[A-Z0-9-]*" docs/*.md README.md | sort -u)
```

Expected: **no output.**

Then re-run task 3's anchor checker. Expected: `UNRESOLVED: none`.

- [ ] **Step 5: Commit**

```bash
git add docs/reference.md
git commit -m "docs: add the warning registry, naming all eighteen W- diagnostics"
```

---

## Task 5: § Package layout and § The importable surface

**Files:**
- Modify: `docs/reference.md` § Package layout, § The importable surface
- Read: `src/publishable/__init__.py`, `ls src/publishable/`

**Interfaces:**
- Consumes: task 2's decisions 5 (unbuilt names stay, marked) and 8 (the root accessor)
- Produces: two tables reconciled with `src/`. Task 16's cross-document pass re-checks both.

- [ ] **Step 1: Add the six built modules to the tree**

`docs/reference.md` § Package layout's fenced tree omits six shipped modules and one shipped subpackage file. Insert them in the tree's existing alphabetical-by-role ordering, each with a `#` comment in the style of its neighbours:

```
│   ├── runner.py              # one execution: constructs the step, runs it, records what came back
│   ├── coercion.py            # a step's return to a flat mapping of scalars; the Estimate exemption
│   ├── contrasts.py           # vs_baseline and declared statistics.contrasts, resolved to comparisons
│   ├── correction.py          # correction families: ranking, holm/bonferroni levels, corrected bounds
│   ├── estimate.py            # Estimate: an interval a summary step computed itself
│   ├── strata.py              # statistics.report_by: stratum levels off the roster
```

and under `templates/`:

```
│   └── templates/{base.py,registry.py,builtin/generic.py}
```

- [ ] **Step 2: Mark the unbuilt modules rather than deleting them**

The tree lists eight modules that do not exist: `plugin_scaffold.py`, `docs.py`, `lineage.py`, `study.py`, `apparatus.py`, `secrets.py`, `reproduce.py`, `report.py`. **Keep them** — they are specified features and the tree is a specification. Add one sentence beneath the fence:

```markdown
**Modules marked `— not yet built` are specified and unbuilt.** The tree is a map of what core's
source will hold, and a module removed from it because today's `src/` lacks it would have to be
re-argued when its slice lands. What is built is what `src/publishable/` contains.
```

and append `— not yet built` to each of the eight comments.

- [ ] **Step 3: Reconcile § The importable surface with `__all__`**

`__all__` holds exactly nine names: `ArtifactError`, `ArtifactExistsError`, `BaseExperiment`, `BaseStep`, `BaseTemplate`, `ContractError`, `Estimate`, `Param`, `PublishableError`.

The table names seven that are absent. Handle them in two groups:

**`Unit` is built and gets exported.** Add it to `__all__` and to the import in `src/publishable/__init__.py`. A step receives `Unit`s from `io.units` and a resolver yields them, so a plugin author needs the type — and the table's own example line is `from publishable import BaseStep, Estimate, Unit, register_resolver`.

**The other six are unbuilt and get marked.** `Apparatus`, `BaseReport`, and the four `register_*` decorators. Add a `Status` column to the table, `built` or `not yet built`, and set the six.

Add beneath the table:

```markdown
**A row marked `not yet built` is a promise, not an export.** Importing one raises `ImportError`
today. The rows stay because this table is the enumerated surface every plugin is written against,
and a contract that appears only once its implementation lands is a contract nobody could have
designed to.
```

- [ ] **Step 4: State the root accessor (decision 8)**

`Config` is documented as dot-access with no methods at all, so that no parameter name can be shadowed. `Config.raw` is an exception: a top-level config key named `raw` is shadowed by it. Add to § The importable surface, beside the `cfg`-and-`io` paragraph:

```markdown
**The root config node carries exactly one accessor, `raw`; every nested node carries none.** That
is a real exception to "no methods at all" and it costs one name: a top-level key named `raw` is
unreachable through dot-access. It is at the root only, because the root is the one node core hands
to something other than a step — `validate` and a template's `validate(config)` both need the
underlying mapping — and a nested node has no such caller. A parameter named `raw` inside a block
is reachable exactly as any other is.
```

- [ ] **Step 5: Add the failing test for the `Unit` export, then export it**

Add to `tests/test_errors.py` (which already pins the import root's shape):

```python
def test_unit_is_importable_from_the_root() -> None:
    import publishable

    assert "Unit" in publishable.__all__
    from publishable import Unit

    assert Unit(key="u1").key == "u1"
```

Run: `uv run pytest tests/test_errors.py::test_unit_is_importable_from_the_root -v`
Expected: **FAIL** — `AssertionError` on `__all__`.

Then add `Unit` to the import and `__all__` in `src/publishable/__init__.py` and re-run.
Expected: **PASS**.

- [ ] **Step 6: Verify the table and `__all__` agree**

```bash
python3 - <<'PY'
import re
import publishable
text = open('docs/reference.md').read()
sec = text.split('## The importable surface')[1].split('\n## ')[0]
named = set(re.findall(r'`([A-Za-z_][A-Za-z0-9_]*)`', sec.split('|---|')[1].split('\n\n')[0]))
exported = set(publishable.__all__)
print("named but unexported:", sorted(named - exported))
print("exported but unnamed:", sorted(exported - named))
PY
```

Expected: `named but unexported` is exactly the six unbuilt names; `exported but unnamed` is empty.

- [ ] **Step 7: Full suite, lint, types, commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add docs/reference.md src/publishable/__init__.py tests/test_errors.py
git commit -m "docs: reconcile the package layout and importable surface with src/"
```

---

## Task 6: § Validation, § Steps and artifacts, § Exit codes, § The one config file

**Files:**
- Modify: `docs/reference.md` § Validation, § Steps and artifacts, § Exit codes and diagnostics, § The one config file

**Interfaces:**
- Consumes: task 2's decisions 3 (narrow the phrase), 6 (reserved metric names), 7 (a wide step's return), 9 (finding order)
- Produces: nothing later tasks read. Task 16 re-checks.

Six prose changes. Each is one to three sentences; none adds a table.

- [ ] **Step 1: Split § Validation's validate-time/run-time blur**

§ Validation's table lists two warnings as validate-time checks that core actually reports at run time — `W-STATS-STRATUM-THIN` and its sibling, both of which need a resolved roster and completed executions. Move them out of the validate-time table into a short paragraph beneath it:

```markdown
**Two of these are reported at run time, not at `validate`.** A stratum's thinness and a corrected
interval's draw floor are both properties of the units that actually completed, which `validate`
has not seen — it resolves the roster to count it, not to know which units a condition will skip.
They appear in [the warning registry](#warnings-core-reports) and in `run.yaml`, never in
`validate`'s output.
```

Confirm which two by reading their emit sites before writing: `grep -rn "W-STATS-STRATUM-THIN\|W-STATS-CORRECTED-THIN" src/publishable/`. If the emit site is in `validate.py`, the row stays.

- [ ] **Step 2: State the reserved metric names (decision 6)**

Add to § Steps and artifacts, beside the flat-mapping return contract:

```markdown
**One metric name is reserved: `by`.** [`statistics.report_by`](#statistical-reporting) spends it —
a stratified block keys its rows by `by`, so a step returning a metric of that name would produce a
record with two meanings for one column. Returning it raises
[`ContractError` · `E-STEP-KEY-COLLISION`](#errors-core-raises). The set is stated here rather than
left to be discovered by collision, and it is a set of one today; anything added to it is a
breaking change to what a step may return.
```

Before writing, confirm the raise: `grep -rn '"by"' src/publishable/coercion.py src/publishable/artifacts.py`. If core does not currently refuse it, say so in your report — the document must not promise a refusal that does not exist, and the row becomes task 14's problem instead.

- [ ] **Step 3: State that a wide step's return is not recorded (decision 7)**

Add to § Steps and artifacts:

```markdown
**A `run`- or `condition`-scoped step's return value is not recorded.** Core still requires it to be
a flat mapping of scalars — the contract is the same at every scope — but there is nowhere for the
values to land: a metric is keyed by unit or reported per repeat, and a wide scope has neither. Use
[`io.write`](#steps-and-artifacts) for what a wide step produces, and let a narrower step record
what it measures. A number with no denominator in the record is the mistake this refusal exists to
prevent, and it is the same one [a usage report makes](#the-unit-table-is-the-inference-base).
```

- [ ] **Step 4: Amend the finding-order sentence (decision 9)**

§ Exit codes and diagnostics promises findings ordered by config position. `validate` collects by check. Amend the sentence to describe what core does:

```markdown
Findings are grouped by the check that produced them, not by where in the config the offending
value sits. A config with three mistakes in one block reports them together, which is the grouping
a reader fixing that block wants; a strict document order would interleave unrelated checks.
```

- [ ] **Step 5: Add `E-IO-FAILED` and `E-STEP-EXISTS` to § Exit codes and diagnostics**

Neither belongs in § Errors core raises: `E-IO-FAILED` is a local `OSError` a command reports rather than a step raises, and `E-STEP-EXISTS` is `generate step` refusing to overwrite a file. Both are diagnostics. Add:

```markdown
A local filesystem failure — an unwritable `output_dir`, a full disk — is reported as
`E-IO-FAILED` and exits `1`. It is not a `ContractError`: nothing in your declarations asked for
it, and no `except` in a step improves it. A creation command refusing to overwrite an existing
file reports `E-STEP-EXISTS` and exits `1` for the same reason — [creation commands take
arguments](#creation-commands), and refusing is how one stays safe to re-run.
```

- [ ] **Step 6: Narrow "the complete parameter set" (decision 3)**

§ The one config file calls what `init` writes "the complete parameter set". `materialize.py` emits none of `statistics.contrasts`, `statistics.resample`, `statistics.null_test`, or `statistics.report_by`. Narrow the phrase:

```markdown
`init` materializes **every parameter the template declares**, each with its default and its
inline comment. Blocks belonging to a feature core does not yet execute are absent from what it
writes — `statistics.contrasts`, `.resample`, `.null_test` and `.report_by` are declared in this
document and added by hand until their slices land. What `init` writes is complete with respect to
[`parameter_spec`](#templates-where-parameters-are-defined), which is the only source of truth
there is one of.
```

Then grep every other occurrence of the old phrasing and fix each:

```bash
grep -rn "complete parameter set" README.md docs/*.md
```

- [ ] **Step 7: Verify and commit**

Re-run task 3's anchor checker. Expected: `UNRESOLVED: none`.

```bash
grep -rn "complete parameter set" README.md docs/*.md   # expect: none, or only the narrowed phrasing
uv run pytest
git add docs/reference.md README.md
git commit -m "docs: settle four checkpoint decisions in validation, steps and exit codes"
```

---

## Task 7: § Statistical reporting and § How artifacts are organized

**Files:**
- Modify: `docs/reference.md` § Statistical reporting, § How artifacts are organized, § Steps that need every condition, § The one config file

**Interfaces:**
- Consumes: nothing from tasks 3–6
- Produces: nothing later tasks read. Task 16 re-checks.

Four prose changes, none of them a decision — each states behaviour the code already has and the document does not.

- [ ] **Step 1: No interval below two units**

§ Statistical reporting must say what `stats.py` does: a metric resolving to fewer than two units carries `ci95: null`, and so does one whose draw pool cannot meet the honest-draw floor for its confidence level.

```markdown
**An interval needs two units, and enough draws to place its bounds.** A metric whose completed
units number fewer than two reports `ci95: null` — there is no dispersion to estimate from one
observation, and a zero-width interval around it would read as certainty. A percentile construction
additionally reports `ci95: null` when `statistics.resample_draws` is below the floor its
confidence level needs, because a bound read off too few draws is a bound placed by the draw count
rather than by the data. `n` still reports the units, and `value` still reports the point estimate:
what is missing is the interval, not the metric.
```

Confirm the floor's name and behaviour first: `grep -n "min_honest_draws" -A12 src/publishable/stats.py`.

- [ ] **Step 2: `__` is not admissible in a swept value**

§ How artifacts are organized states the swept-value pattern as `[A-Za-z0-9._+-]+`, which admits `__` — while `__` is the label separator, so `sweep.py` refuses it. Add:

```markdown
A swept value renders as `[A-Za-z0-9._+-]+` and additionally may not contain `__`, which is the
separator between one `key=value` component and the next. A value carrying it would produce a
directory name that parses back into a different set of components than the one it was built from,
and a label that cannot be read back is not a label.
```

- [ ] **Step 3: `io.conditions` yields `(index, label)`**

Add to § Steps that need every condition, beside `io.read_condition`:

```markdown
`io.conditions` yields `(index, label)` pairs, not bare labels — `read_condition` addresses a
condition by its index, and the label is what you put in a figure. An unswept run yields one pair
whose label is `None`, because there is no `key=value` body to render.
```

Confirm against `grep -n "def conditions" -A15 src/publishable/artifacts.py` before writing.

- [ ] **Step 4: `default_repeats` is a floor**

§ The one config file (or wherever the naming table sits — `grep -n "default_repeats" docs/reference.md`) presents `default_repeats` as a materialized value; S1 implements it as a floor. Rename the column to **Repeat floor** and add:

```markdown
This is a floor, not a value `init` writes. A template declaring a repeat floor above what a
config asks for makes `validate` warn ([`W-REPL-FLOOR`](#warnings-core-reports)); it never edits
the config. What executes is what the config says, and what the floor buys is that a design running
below it says so in its record.
```

- [ ] **Step 5: Verify and commit**

Re-run task 3's anchor checker. Expected: `UNRESOLVED: none`.

```bash
uv run pytest
git add docs/reference.md
git commit -m "docs: state the interval floors, the label separator, and the repeat floor"
```

---

## Task 8: § Pre-registration and § `Estimate`

**Files:**
- Modify: `docs/reference.md` § Pre-registration, § What a hypothesis is tested against, § `Estimate`
- Read: `src/publishable/hypotheses.py`, `src/publishable/estimate.py`, `src/publishable/coercion.py`

**Interfaces:**
- Consumes: task 2's decision 4 (three verdict states, both routes)
- Produces: nothing later tasks read. Task 16's worked-example check reads this section closely.

**This section is worked-example territory.** `CLAUDE.md` pins `h1`'s two divergent verdicts, the delta `0.026`, the paired interval `[−0.007, 0.059]`, and the threshold `0.02`. **This task adds a key to an example block and adds prose; it changes no figure.** Do not "fix" the fact that `h1` is supported on `observed` while its interval spans zero — that divergence is the point of `verdict_evaluated_on` and `CLAUDE.md` names it as a consequence to preserve.

- [ ] **Step 1: State the three verdict states and both routes (decision 4)**

Add to § Pre-registration:

```markdown
**`supported` has three states, and the third is not a failure.** `true` and `false` mean the
comparison was made and came out one way or the other. `null` means core could not make it, and it
appears by exactly two routes: the observation does not resolve — the step that would have produced
the metric failed, or every unit on one side of a comparison was ineligible — or the verdict asks
for a bound (`evaluate_on: ci95_lower` or `ci95_upper`) against a metric whose interval is `null`.
The `observed` block still records what was found, so a reader can see which route it was.

A `false` in either of those places would be indistinguishable from a claim that was tested and did
not hold, which is the confusion [`verdict_evaluated_on`](#what-a-hypothesis-is-tested-against)
exists to prevent one level up. A hypothesis core could not evaluate is not a hypothesis core
refuted.
```

- [ ] **Step 2: Show a `null` verdict in the `run.yaml` example**

§ Pre-registration's `run.yaml` example shows one verdict. Add a second beneath it, using a *new* hypothesis id that does not exist elsewhere in the documents — `h3` — so no pinned figure moves:

```yaml
  - id: h3
    kind: exploratory
    declared_in: parameters_hash sha256:1a2b...
    observed:
      delta: null
      ci95: null
      method: paired_percentile_over_units
    supported: null
    verdict_evaluated_on: ci95_lower
    verdict_rests_on: computed
```

Then grep the four documents for `h3` to confirm it is new: `grep -rn "\bh3\b" README.md docs/*.md`.

- [ ] **Step 3: Add `method` to the `observed` example**

The `observed` block core writes carries four keys — `delta`, `ci95`, `ci95_corrected`, `method` — and § Pre-registration's example shows three. Add `method` to the existing example, reading the name core actually records for the worked example's contrast:

```bash
grep -rn "paired_percentile_over_units" docs/reference.md src/publishable/
```

The worked example's delta is a paired percentile construction, so the value is
`paired_percentile_over_units`. Adding a key is not a figure change.

- [ ] **Step 4: State § `Estimate`'s six rules**

§ `Estimate` states four rules and should state six. Add:

```markdown
- `ci95` is exactly two numbers, in ascending order — refused as
  [`E-STEP-ESTIMATE-CI95`](#errors-core-raises). A bound read off a one-element or reversed pair
  would be the wrong bound, silently, and `evaluate_on: ci95_lower` indexes it.
- `value` is a number — refused as [`E-STEP-ESTIMATE-VALUE`](#errors-core-raises). An `Estimate` is
  the one interval core stores without computing, so the only thing it can check is the shape.
```

Confirm both against `src/publishable/coercion.py` before writing.

- [ ] **Step 5: State the required `hypotheses` fields**

§ Pre-registration names the fields in prose; the config block should say which are required. Add a short table listing `id`, `kind`, `metric`, `step`, `direction`, `threshold`, `evaluate_on`, `compare`, marking each required or optional, and stating that `compare` is absent exactly when the metric is a summary-step `Estimate`. Read `src/publishable/validate.py`'s hypothesis checks for the actual requirement set before writing:

```bash
grep -n "E-HYPOTHESIS" -B6 src/publishable/validate.py
```

- [ ] **Step 6: Verify no pinned figure moved**

```bash
git diff docs/reference.md | grep "^-" | grep -E "0\.026|0\.02|0\.581|0\.607|0\.412|−0\.007|0\.059|0\.014|228|240|\b12\b|8e21|1a2b|3d8a|6b1f"
```

Expected: **no output.** Any hit is a removed pinned figure and must be restored.

Re-run task 3's anchor checker. Expected: `UNRESOLVED: none`.

- [ ] **Step 7: Commit**

```bash
uv run pytest
git add docs/reference.md
git commit -m "docs: state the three verdict states and Estimate's six rules"
```

---

## Task 9: § The two files

**Files:**
- Modify: `docs/reference.md` § The two files
- Read: `src/publishable/run_record.py`, `src/publishable/cli.py`

**Interfaces:**
- Consumes: nothing from tasks 3–8
- Produces: nothing later tasks read.

- [ ] **Step 1: Add `layout` and `provenance.input_manifest_changed` to the `run.yaml` example**

Both are written by core and appear in no example. Read what core writes first:

```bash
grep -n "\"layout\"\|input_manifest_changed" src/publishable/run_record.py src/publishable/cli.py
```

Add both to § The two files' `run.yaml` example, with the values the worked example's run would carry, and one sentence each: `layout` records which artifact-tree levels were present, since degenerate levels collapse and a reader needs to know whether a missing `conditions/` meant an unswept run or a failure; `input_manifest_changed` records whether the input manifest differed from the upstream run's, which is what makes a re-run's inputs checkable.

- [ ] **Step 2: State `per_repeat`'s shape when nothing repeats**

```markdown
A run with no repeat level still writes `per_repeat`, keyed by the empty string — the one repeat
has no label because there is no repeat axis to render one from. The block is present rather than
omitted so that a reader parsing `per_repeat` does not need two code paths, and the empty key is
what says "this run had one execution per condition" rather than "this run recorded nothing".
```

Confirm against `grep -n "per_repeat" -A10 src/publishable/run_record.py`.

- [ ] **Step 3: State a single repeat's dispersion**

Entry 525 answered this for `basis: units`; the repeats case is open.

```markdown
`repeat_spread` is absent when the run resolved one repeat. A standard deviation over one value is
zero, and reporting zero would read as agreement between repeats that were never run — the same
mistake a zero-width `ci95` over one unit would make.
```

Confirm the code omits rather than writes zero: `grep -n "repeat_spread" -B4 -A10 src/publishable/cli.py`. If core writes `0.0` today, the document must say so instead, and the divergence becomes a task 16 finding.

- [ ] **Step 4: Verify and commit**

Re-run task 3's anchor checker. Expected: `UNRESOLVED: none`.

```bash
uv run pytest
git add docs/reference.md
git commit -m "docs: document layout, input_manifest_changed, and the degenerate repeat cases"
```

---

## Task 10: `rank_family` ranks by declaration order

**Files:**
- Modify: `src/publishable/correction.py`
- Modify: `src/publishable/cli.py` (wherever `Member`s are constructed)
- Test: `tests/test_correction.py`

**Interfaces:**
- Consumes: nothing from tasks 3–9
- Produces: `Member` gains a field `declaration_index: int`. Any construction site must pass it. `rank_family(members: Sequence[Member]) -> list[Member]` keeps its signature.

`correction.py`'s `rank_family` currently sorts by `(-_evidence_ratio(m), m.condition_index, m.metric)` — lexicographic by metric name, which `reference.md` calls declaration order. `where` is omitted from the key entirely, so two members of different comparisons with the same condition index and metric are ordered arbitrarily.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_correction.py`:

```python
def test_a_tie_breaks_by_declaration_order_not_by_metric_name() -> None:
    """Two members with identical evidence rank in the order cli built them.

    Named `zeta` first and `alpha` second on purpose: a lexicographic tie-break
    puts `alpha` first, and declaration order puts `zeta` first.
    """
    members = [
        Member(
            where="cond:1",
            condition_index=1,
            step="step02",
            metric="zeta",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=0,
        ),
        Member(
            where="cond:1",
            condition_index=1,
            step="step02",
            metric="alpha",
            delta=0.1,
            ci95=(0.0, 0.2),
            pool=None,
            diffs=(0.1, 0.1),
            declaration_index=1,
        ),
    ]
    assert [m.metric for m in rank_family(members)] == ["zeta", "alpha"]
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_correction.py::test_a_tie_breaks_by_declaration_order_not_by_metric_name -v`
Expected: **FAIL** — `TypeError: Member.__init__() got an unexpected keyword argument 'declaration_index'`.

- [ ] **Step 3: Add the field and change the key**

In `src/publishable/correction.py`, add to `Member`:

```python
    declaration_index: int
```

and change `rank_family`'s key and docstring:

```python
def rank_family(members: Sequence[Member]) -> list[Member]:
    """Strongest first, so a member's rank is its index + 1.

    Ties break by declaration order — the index `cli` assigned when it built the
    family, which follows the config's own ordering of comparisons and metrics.
    `reference.md` requires that: a rank decides a correction level, and a level
    that moved with iteration order would make two identical runs disagree. The
    earlier key broke ties by metric *name*, which is a different ordering that
    happened to be stable, and which reorders a family when a metric is renamed.
    """
    return sorted(
        members,
        key=lambda m: (-_evidence_ratio(m), m.declaration_index),
    )
```

`condition_index` and `metric` leave the key: `declaration_index` is unique per member, so nothing after it can ever be reached.

- [ ] **Step 4: Assign the index at every construction site**

Find them: `grep -rn "Member(" src/publishable/ tests/ | grep -v __pycache__`. In `cli.py`, assign `declaration_index=i` from the enumeration that builds the list, so the index follows the order comparisons and metrics are iterated — which is config order. Update every test fixture that constructs a `Member`.

- [ ] **Step 5: Run the test and the suite**

Run: `uv run pytest tests/test_correction.py::test_a_tie_breaks_by_declaration_order_not_by_metric_name -v`
Expected: **PASS**.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green.

- [ ] **Step 6: Mutation-test the tie-break**

Apply the mutation, run the named test, confirm it fails, revert, confirm `git status --porcelain` is empty. **Run it — do not reason about it.**

| Mutation | Test that must fail |
|---|---|
| Restore the key to `(-_evidence_ratio(m), m.condition_index, m.metric)` | `test_a_tie_breaks_by_declaration_order_not_by_metric_name` |
| Change the key to `(-_evidence_ratio(m), -m.declaration_index)` | the same test |

- [ ] **Step 7: Commit**

```bash
git add src/publishable/correction.py src/publishable/cli.py tests/test_correction.py
git commit -m "fix: rank a correction family's ties by declaration order"
```

---

## Task 11: `validate` catches `SystemExit`

**Files:**
- Modify: `src/publishable/validate.py` (the `except Exception` around `load_experiment`)
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: nothing
- Produces: nothing later tasks read.

A user package calling `sys.exit()` at module scope — or anything that does, such as an `argparse` parser built at import time — raises `SystemExit`, which does not inherit from `Exception`. It escapes `validate`'s deliberately-broad catch, and the process exits with the user's chosen code and no diagnostic. `validate`'s hard contract is that it collects findings and never raises.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_validate.py`, following the file's existing pattern for writing a user package into a temporary repo:

```python
def test_an_entrypoint_that_exits_at_module_scope_is_reported_not_propagated(
    tmp_path: Path,
) -> None:
    """`sys.exit()` at import is a SystemExit, which is not an Exception.

    Without an explicit arm it escapes `validate`'s catch and takes the process
    with it — the user's exit code, and no diagnostic naming the entrypoint.
    """
    project = _scaffolded_project(tmp_path)          # existing helper
    (project / "src" / "cohort_pilot" / "__init__.py").write_text(
        "import sys\nsys.exit(3)\n"
    )

    findings = validate_config(project / "configs" / "cohort-pilot" / "config.yaml")

    codes = [f.code for f in findings]
    assert "E-ENTRYPOINT-IMPORT" in codes
    message = next(f.message for f in findings if f.code == "E-ENTRYPOINT-IMPORT")
    assert "SystemExit" in message
```

Read `tests/test_validate.py` for the actual helper names and the `Finding` attribute names before writing — `_scaffolded_project`, `.code` and `.message` are the shapes this plan expects and the file is authoritative.

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_validate.py::test_an_entrypoint_that_exits_at_module_scope_is_reported_not_propagated -v`
Expected: **FAIL** — the test process exits with code 3, or pytest reports `SystemExit: 3`.

- [ ] **Step 3: Add the arm**

In `src/publishable/validate.py`, beside the existing `except Exception as exc:` around `load_experiment`, add **above** it:

```python
        except SystemExit as exc:
            # `SystemExit` is a `BaseException`, so the broad `except Exception` below
            # does not see it. A user package calling `sys.exit()` at module scope —
            # or building an `argparse` parser at import — would otherwise end the
            # process with the user's own exit code and no diagnostic at all, which
            # is the one outcome `validate` is contracted never to produce.
            c.error(
                "E-ENTRYPOINT-IMPORT",
                "entrypoint",
                f"could not be imported: SystemExit: {exc.code}",
            )
```

- [ ] **Step 4: Run the test and the suite**

Run: `uv run pytest tests/test_validate.py::test_an_entrypoint_that_exits_at_module_scope_is_reported_not_propagated -v`
Expected: **PASS**.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green.

- [ ] **Step 5: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Delete the `except SystemExit` arm | the new test |
| Place the arm **below** `except Exception` | Python raises `SyntaxError`-adjacent unreachable-handler behaviour or the test fails — record which |
| Change the code to `"E-ENTRYPOINT-IMPORT-EXIT"` | the new test |

Run each, revert each, confirm `git status --porcelain` is empty after every revert.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/validate.py tests/test_validate.py
git commit -m "fix: report a SystemExit from an entrypoint import instead of propagating it"
```

---

## Task 12: `Unit` refuses a write with `E-UNIT-IMMUTABLE`

**Files:**
- Modify: `src/publishable/units.py`
- Test: `tests/test_units.py`

**Interfaces:**
- Consumes: task 2's decision 2 (implement the coded refusal)
- Produces: `Unit.__setattr__` and `Unit.__delattr__` raise `ContractError` with code `E-UNIT-IMMUTABLE`. `unit.attributes` is a mapping whose `__setitem__`, `__delitem__`, `pop`, `clear` and `update` do the same.

**Both halves are documented, and `MappingProxyType` covers neither with a code.** `reference.md` § The unit list is three operations names `unit.attributes["scored"] = True` as *the* example, and `MappingProxyType` raises a bare `TypeError` for it. `@dataclass(frozen=True)` raises a bare `FrozenInstanceError` for `unit.key = "x"`. Neither is a `PublishableError`, so `main()` catches neither.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_units.py`:

```python
def test_writing_a_unit_field_raises_the_documented_code() -> None:
    unit = Unit(key="u1")

    with pytest.raises(ContractError) as exc:
        unit.key = "u2"  # type: ignore[misc]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_writing_through_a_units_attributes_raises_the_documented_code() -> None:
    """`reference.md` names this exact expression: a roster is shared across
    conditions, so this write would change what the next condition measures."""
    unit = Unit(key="u1", attributes={"site": "A"})

    with pytest.raises(ContractError) as exc:
        unit.attributes["scored"] = True  # type: ignore[index]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_deleting_a_units_attribute_raises_the_documented_code() -> None:
    unit = Unit(key="u1", attributes={"site": "A"})

    with pytest.raises(ContractError) as exc:
        del unit.attributes["site"]  # type: ignore[misc]

    assert exc.value.code == "E-UNIT-IMMUTABLE"


def test_a_unit_still_reads_normally() -> None:
    unit = Unit(key="u1", paths=("a.csv",), attributes={"site": "A"})

    assert unit.key == "u1"
    assert unit.paths == ("a.csv",)
    assert unit.attributes["site"] == "A"
    assert unit.site == "A"
    assert len(unit.attributes) == 1
    assert dict(unit.attributes) == {"site": "A"}
    assert {unit} == {Unit(key="u1")}          # hashable by key
```

- [ ] **Step 2: Run them and watch them fail**

Run: `uv run pytest tests/test_units.py -k immutable -v`
Expected: **FAIL** on the first three — `FrozenInstanceError` and `TypeError` are raised, not `ContractError`.

- [ ] **Step 3: Add the refusing mapping**

In `src/publishable/units.py`, above `Unit`:

```python
class _FrozenAttributes(Mapping[str, Any]):
    """A read-only mapping that refuses a write with the documented code.

    `MappingProxyType` refuses too, but with a bare `TypeError` that carries no
    `.code` and is not a `PublishableError` — so `main` does not catch it and the
    user gets a traceback where every other refusal is a diagnostic. The document
    names `unit.attributes["scored"] = True` as the example, so this is the
    expression that has to produce `E-UNIT-IMMUTABLE`.
    """

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]) -> None:
        object.__setattr__(self, "_data", dict(data))

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return repr(self._data)

    def _refuse(self, *_args: Any, **_kwargs: Any) -> Any:
        raise ContractError(
            "a unit's attributes are read-only: the roster is resolved once per run "
            "and shared across every condition, so writing here would change what "
            "the next condition measures",
            code="E-UNIT-IMMUTABLE",
        )

    __setitem__ = _refuse
    __delitem__ = _refuse
    pop = _refuse
    popitem = _refuse
    clear = _refuse
    update = _refuse
    setdefault = _refuse
```

- [ ] **Step 4: Refuse field writes on `Unit`**

In `Unit`, replace the `MappingProxyType` line in `__post_init__` and add the two dunders:

```python
    def __post_init__(self) -> None:
        # `object.__setattr__` rather than `self.attributes = …`, because the
        # refusal below is already in place by the time this runs.
        object.__setattr__(self, "attributes", _FrozenAttributes(self.attributes))

    def __setattr__(self, name: str, value: Any) -> None:
        raise ContractError(
            f"a unit is immutable: cannot set {name!r}. The roster is resolved once "
            "per run and shared across every condition",
            code="E-UNIT-IMMUTABLE",
        )

    def __delattr__(self, name: str) -> None:
        raise ContractError(
            f"a unit is immutable: cannot delete {name!r}. The roster is resolved "
            "once per run and shared across every condition",
            code="E-UNIT-IMMUTABLE",
        )
```

Keep `@dataclass(frozen=True, eq=False)` — `frozen=True` is what makes the generated `__init__` use `object.__setattr__`, and removing it would break construction. Add `Iterator` to the `collections.abc` import if it is not already there; `MappingProxyType` may become unused — remove the `from types import MappingProxyType` line if so, or ruff will flag it.

- [ ] **Step 5: Run the tests and the suite**

Run: `uv run pytest tests/test_units.py -v`
Expected: **PASS**, all four.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green. If `mypy` objects to assigning `_refuse` to the dunder names, add a targeted `# type: ignore[assignment]` on each — not a blanket ignore on the class.

- [ ] **Step 6: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Restore `MappingProxyType` in `__post_init__` | `test_writing_through_a_units_attributes_raises_the_documented_code` |
| Delete `Unit.__setattr__` | `test_writing_a_unit_field_raises_the_documented_code` |
| Change the code string to `"E-UNIT-FROZEN"` | all three refusal tests |
| Make `_FrozenAttributes.__init__` store the mapping without copying it (`object.__setattr__(self, "_data", data)`) | none of the above — **add a test for it**: build a `dict`, construct a `Unit` from it, mutate the original `dict`, and assert `unit.attributes` did not change |

Run each, revert each, confirm `git status --porcelain` is empty after every revert. The fourth mutation is the one that will not be caught by the tests as written — that is why it is listed, and the test it demands is part of this task.

- [ ] **Step 7: Commit**

```bash
git add src/publishable/units.py tests/test_units.py
git commit -m "fix: raise the documented E-UNIT-IMMUTABLE on a write through a Unit"
```

---

## Task 13: `aggregate`'s table carries declared unit attributes

**Files:**
- Modify: `src/publishable/cli.py` (`UnitTable` construction)
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: task 12's `Unit` (attributes are read through the same three operations)
- Produces: the table `aggregate` receives exposes declared unit attributes as columns, alongside the recorded ones.

**This entry named S4c as its owner. S4c, S4d, S5a and S5b all merged without it.** `reference.md` § Templates says a template's `aggregate` reads the unit table; `data.units` declares attributes; today `grep -n attributes src/publishable/stats.py` returns nothing and only recorded columns reach the table.

**A string column needs a collapse rule.** A recorded numeric column collapses across a unit's repeats by mean; a declared attribute does not vary across repeats at all, because it comes from the roster rather than from an execution. So the rule is: **a declared attribute is carried through unchanged, and it is a collision (`E-STEP-KEY-COLLISION`) for a recorded column to share its name** — which core already refuses, per § Errors core raises' existing row.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_cli.py`, following the file's existing end-to-end run helpers:

```python
def test_a_templates_aggregate_sees_declared_unit_attributes() -> None:
    """`data.units` declares `site`; a template reading `row["site"]` must find it.

    The roster carries it, no step records it, and today it never reaches the
    table — so a template that stratifies on a declared attribute cannot.
    """
    # ... build a project whose index.csv carries a `site` column,
    #     whose config declares `data.units.attributes: [site]`,
    #     and whose template's `aggregate` returns
    #     {"n_site_a": sum(1 for row in units if row["site"] == "A")}
    result = _run(project)

    metrics = result["conditions"][0]["metrics"]
    assert metrics["n_site_a"]["value"] == 2
```

Read `tests/test_cli.py` for the existing project-building helpers and reuse them; do not write a new harness. The comment block above must become real code before this task is done — it is a sketch of the fixture, not a placeholder in the finished test.

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_cli.py::test_a_templates_aggregate_sees_declared_unit_attributes -v`
Expected: **FAIL** — a `ContractError` · `E-STEP-COLUMN-UNKNOWN` surfacing as `W-STATS-AGGREGATE-FAILED`, or a `KeyError` on `"site"`.

- [ ] **Step 3: Thread the roster into the table**

In `cli.py`, where `UnitTable` is constructed, pass the resolved roster and merge each unit's declared attributes into its row, recorded columns taking no precedence — a collision is already refused upstream as `E-STEP-KEY-COLLISION`. Keep the table's four operations exactly as they are: row iteration, column access, `len`, `columns`. `columns` must now include the declared attribute names.

- [ ] **Step 4: Run the test and the suite**

Run: `uv run pytest tests/test_cli.py::test_a_templates_aggregate_sees_declared_unit_attributes -v`
Expected: **PASS**.

Run: `uv run pytest && uv run ruff check . && uv run mypy`
Expected: all green.

- [ ] **Step 5: Mutation-test**

| Mutation | Test that must fail |
|---|---|
| Stop merging attributes into the row (revert step 3's merge) | the new test |
| Merge the attributes but omit them from `columns` | **add a test asserting `"site" in units.columns`** — the one above passes without it |
| Let a recorded column silently win a name collision | the existing `E-STEP-KEY-COLLISION` test in `tests/test_artifacts.py` — confirm it still fails on this mutation; if it does not, that refusal is untested and this task adds a test for it |

Run each, revert each, confirm `git status --porcelain` is empty after every revert.

- [ ] **Step 6: Commit**

```bash
git add src/publishable/cli.py tests/test_cli.py
git commit -m "fix: carry declared unit attributes into the table aggregate receives"
```

---

## Task 14: Pin the non-numeric `aggregate` containment

**Files:**
- Test: `tests/test_stats.py` and `tests/test_cli.py`
- Modify: `src/publishable/stats.py` docstrings only — no behaviour change
- Modify: `src/publishable/validate.py` (`_check_contrasts`)

**Interfaces:**
- Consumes: nothing from tasks 10–13
- Produces: nothing later tasks read.

**Two unrelated small debts, folded together because each is a test plus a comment.**

**Debt A — the `float()` containment is real but incidental.** A template returning `{"m": "high"}` yields `ci95: null`, `W-STATS-AGGREGATE-FAILED`, and a `str` in the metric's `value`. That works only because every call site of the aggregate closure sits inside an `except Exception` whose docstring justifies it *solely* as degenerate-bootstrap-draw handling. No test pins the `str` case — `tests/test_stats.py`'s existing test pins a compute that *raises*. A future narrowing of those handlers to `except (ValueError, ZeroDivisionError)` reopens the path with nothing failing.

**Debt B — two narrow holes in `_check_contrasts`.** `validate.py`'s `_check_contrasts` calls `expand` unguarded, and `compare: {condition: X}` with no `to` and no `sweep.baseline` fires neither the baseline check nor the contrast check.

- [ ] **Step 1: Write the failing test for the containment**

Add to `tests/test_stats.py`:

```python
def test_a_derived_metric_returning_a_string_is_contained_not_raised() -> None:
    """A template returning a non-numeric metric yields a null interval, not a crash.

    The containment is real but incidental: it comes from the `except Exception`
    that exists for degenerate draws. This test is what makes narrowing that
    handler fail loudly instead of silently reopening the path.
    """
    result = percentile_of_derived(
        keys=("u1", "u2", "u3"),
        compute=lambda _rows: "high",
        draws=2000,
        confidence=0.95,
        rng=np.random.default_rng(0),
    )

    assert result is None
```

Read `tests/test_stats.py` for `percentile_of_derived`'s real signature and the file's existing fixture style before writing — the argument names above must match the function.

- [ ] **Step 2: Run it**

Run: `uv run pytest tests/test_stats.py::test_a_derived_metric_returning_a_string_is_contained_not_raised -v`
Expected: **PASS** — the behaviour already holds. This test is a pin, not a fix. Confirm it is a real pin in step 3.

- [ ] **Step 3: Prove the pin bites**

Narrow the handler in `stats.py`'s `percentile_of_derived` from `except Exception` to `except (ValueError, ZeroDivisionError)`. Run the test. Expected: **FAIL** with `TypeError`. Revert, confirm `git status --porcelain` is empty.

**If it does not fail, the test is not pinning anything** — find where the `str` is actually contained and pin that instead.

- [ ] **Step 4: Amend the docstrings so the next reader knows what the handler holds**

In each of `stats.py`'s three handlers (`percentile_of_derived`, `paired_delta_of_derived`, `paired_percentile_of_derived`) and `cli.py`'s strata path, extend the existing comment:

```python
            # Also the containment for a template returning a non-numeric metric:
            # `coerce_scalars` accepts `str`, so a `{"m": "high"}` return reaches
            # here and becomes `ci95: null` plus `W-STATS-AGGREGATE-FAILED` rather
            # than a traceback. Narrowing this to specific exception types reopens
            # that path — see the pin in tests/test_stats.py.
```

- [ ] **Step 5: Close debt B's first hole**

Guard `_check_contrasts`' call to `expand` the same way its neighbours are guarded, so a malformed sweep reaching it produces a finding rather than a raise. Read the neighbouring checks for the established pattern; `validate` collects and never raises.

Write the failing test first, in `tests/test_validate.py`: a config whose `sweep` is malformed *and* whose `statistics.contrasts` is present, asserting `validate_config` returns findings rather than raising.

- [ ] **Step 6: Record debt B's second hole as a decision, not a fix**

`compare: {condition: X}` with no `to` and no `sweep.baseline` fires neither check. Rather than widening a check speculatively, append to `docs/superpowers/spec-defects.md` under the entry at line 2370:

```markdown
**AMENDED 2026-08-11 (task 14 of the S5 checkpoint plan):** The first hole is closed —
`_check_contrasts` now guards its `expand` call. The second stands by decision: a `compare` naming
a condition with no `to` and no `sweep.baseline` is a form no documented rule covers, and inventing
a refusal here would be core deciding a question `reference.md` § Pre-registration has not asked.
Routed to the hardening slice that specifies `compare`'s full grammar.
```

- [ ] **Step 7: Run the suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add src/publishable/stats.py src/publishable/cli.py src/publishable/validate.py \
        tests/test_stats.py tests/test_validate.py
git commit -m "test: pin the non-numeric aggregate containment; guard _check_contrasts' expand"
```

---

## Task 15: The mechanical consistency pass

**Files:**
- Read: `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`, `docs/reference.md`, `CLAUDE.md`, `docs/feasibility-llm-growth-studies.md`
- Modify: whichever of them the pass finds defects in

**Interfaces:**
- Consumes: every document edit from tasks 3–9
- Produces: a clean mechanical pass. Task 16's cross-document pass assumes it.

`CLAUDE.md` § Checking consistency: write these as throwaway checks, not as tooling the repo keeps. **Skip fenced code blocks in every check** — the docs contain markdown inside markdown, and a `##` or `|` there is content.

- [ ] **Step 1: Anchors and links**

```bash
python3 - <<'PY'
import re, pathlib, sys
files = ["README.md","CLAUDE.md","docs/design-principles.md","docs/experimental-designs.md",
         "docs/reference.md","docs/feasibility-llm-growth-studies.md"]
def slug(h):
    return re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-')
heads = {}
for f in files:
    body = re.sub(r'```.*?```', '', pathlib.Path(f).read_text(), flags=re.S)
    hs = [slug(h) for h in re.findall(r'^#{1,6} (.+)$', body, re.M)]
    dupes = {h for h in hs if hs.count(h) > 1}
    if dupes: print(f"DUPLICATE ANCHORS in {f}: {sorted(dupes)}")
    heads[f] = set(hs)
bad = []
for f in files:
    body = re.sub(r'```.*?```', '', pathlib.Path(f).read_text(), flags=re.S)
    for target, anchor in re.findall(r'\]\(([^)#]*)#([a-z0-9-]+)\)', body):
        dest = f if not target else str((pathlib.Path(f).parent / target).resolve().relative_to(pathlib.Path.cwd()))
        if dest not in heads: bad.append((f, target, "no such file"))
        elif anchor not in heads[dest]: bad.append((f, f"{target}#{anchor}", "no such anchor"))
    for target in re.findall(r'\]\(([^)#:]+\.md)\)', body):
        if not (pathlib.Path(f).parent / target).exists(): bad.append((f, target, "no such file"))
print("BROKEN:", bad or "none")
sys.exit(1 if bad else 0)
PY
```

Expected: no duplicates, `BROKEN: none`, exit 0.

- [ ] **Step 2: Tables**

```bash
python3 - <<'PY'
import re, pathlib
for f in ["README.md","CLAUDE.md","docs/design-principles.md","docs/experimental-designs.md",
          "docs/reference.md","docs/feasibility-llm-growth-studies.md"]:
    text = pathlib.Path(f).read_text()
    fenced = {n for m in re.finditer(r'```.*?```', text, re.S)
              for n in range(text[:m.start()].count('\n')+1, text[:m.end()].count('\n')+2)}
    width = None
    for n, line in enumerate(text.splitlines(), 1):
        if n in fenced: continue
        s = line.strip()
        if s.startswith('|') and s.endswith('|'):
            cols = len(s.split('|')) - 2
            if re.fullmatch(r'\|[\s:-]+\|', s.replace('|', '|', 1)) or set(s) <= set('|-: '):
                width = cols; continue
            if width is None: width = cols
            elif cols != width: print(f"{f}:{n}: {cols} cols, expected {width}")
            if not s.strip('| ').strip(): print(f"{f}:{n}: empty row")
        else:
            width = None
PY
```

Expected: no output.

- [ ] **Step 3: Whitespace, tabs, invisible unicode, `x` for `×`, en dashes in anchors**

```bash
grep -rn " $" README.md CLAUDE.md docs/*.md                      # trailing whitespace
grep -rnP "\t" README.md CLAUDE.md docs/*.md                     # tabs
grep -rnP "[\x{200b}\x{00a0}\x{feff}\x{2060}]" README.md CLAUDE.md docs/*.md   # invisibles
grep -rnE "[0-9] x [0-9]" README.md CLAUDE.md docs/*.md          # x for ×
grep -rnE "^#{1,6} .*–" README.md CLAUDE.md docs/*.md            # en dash in a heading
```

Expected: no output from any of the five. An en dash in a heading is the one that silently breaks anchors — GitHub's slugger strips it entirely.

- [ ] **Step 4: Grep for strings this checkpoint removed or renamed**

```bash
grep -rn "complete parameter set" README.md CLAUDE.md docs/*.md
grep -rn "default_repeats" README.md CLAUDE.md docs/*.md
grep -rn "register_template" README.md CLAUDE.md docs/*.md
```

Each hit must be consistent with what tasks 5–6 wrote. `register_template` should now appear only in § The importable surface, marked not yet built.

- [ ] **Step 5: Fix every defect found, re-run all four checks, commit**

```bash
uv run pytest
git add -A README.md CLAUDE.md docs/
git commit -m "docs: mechanical consistency pass over the four documents"
```

If steps 1–4 all produced no output and no file changed, there is nothing to commit — say so in the report rather than creating an empty commit.

---

## Task 16: The cross-document pass, and route every residual

**Files:**
- Read: all four documents, `docs/superpowers/spec-defects.md`, `docs/superpowers/CHECKPOINT-AGENDA.md`, `docs/superpowers/specs/2026-08-08-implementation-spine-design.md`
- Modify: whichever documents the pass finds defects in; `docs/superpowers/spec-defects.md`

**Interfaces:**
- Consumes: tasks 1–15
- Produces: the checkpoint's exit criterion.

**No tooling substitutes for this pass.** `CLAUDE.md` names seven drift classes; check each against what tasks 3–9 changed.

- [ ] **Step 1: The shared worked example**

README, `design-principles.md` and `reference.md` describe one experiment: `cohort-pilot`, package `cohort_pilot`, template `generic`, steps `step01_load_cohort` (run) → `step02_fit_model` (condition) → `step03_analyze` (repeat) → `step04_compare_methods` (summary). Confirm every figure `CLAUDE.md` pins still reads as it does there:

```bash
git diff main --stat -- README.md docs/
git diff main -- README.md docs/ | grep "^-" | \
  grep -E "0\.026|0\.02|0\.581|0\.607|0\.412|0\.488|0\.661|0\.517|0\.683|0\.347|0\.477|−0\.007|0\.059|−0\.169|−0\.213|−0\.125|0\.014|228|240|8e21|1a2b|3d8a|6b1f|2f5c8d0"
```

Expected: **no output** from the second command. Any hit is a pinned figure this checkpoint removed and must be restored.

Also confirm the deliberate divergences survived: README uses `~/data`/`~/results` where `reference.md` uses `/secure/...`, and README's `demo` walkthrough carries its own code hash prefix `2f5c8d0` under a separate `correlation_pilot` experiment.

- [ ] **Step 2: Config completeness**

Every config field documented anywhere in `reference.md` must appear in § The one config file. Task 6 narrowed that section's self-description; confirm the field list itself is still complete:

```bash
python3 - <<'PY'
import re, pathlib
text = pathlib.Path('docs/reference.md').read_text()
one = text.split('## The one config file')[1].split('\n## ')[0]
mentioned = set(re.findall(r'`((?:data|statistics|replication|sweep|limits|analysis|metadata)\.[a-z_.]+)`', text))
missing = sorted(m for m in mentioned if m.split('.')[-1] not in one)
print("documented elsewhere but absent from § The one config file:", missing or "none")
PY
```

Triage each hit: a refused feature's field is expected to be documented and absent from what `init` writes, which task 6's narrowed phrasing now permits. A field belonging to a built feature is a real gap.

- [ ] **Step 3: The other five classes**

| Class | Check |
|---|---|
| Enum comments | Every inline `# a \| b \| c` lists every value its table defines. Task 4's warning table and task 8's verdict states both add values — grep for enum comments naming `supported` or a diagnostic level |
| Schema fields in prose | Every field named in prose exists in the `config.yaml` or `run.yaml` example. Task 9 added `layout` and `input_manifest_changed` to the example; confirm the prose names them too |
| Declared vs. derived | Nothing shows a derived value as a settable input. Task 7's `default_repeats` change is exactly this class — confirm no other passage now shows it as settable |
| Versions | Version numbers in examples agree with `CITATION.cff` and README's v0.x notice: `grep -n version CITATION.cff; grep -rn "v0\.[0-9]" README.md docs/*.md` |
| Prevented mistakes | Everything in `experimental-designs.md` § Mistakes core prevents is structurally impossible in the schema, not merely discouraged. Nothing in tasks 3–9 should have weakened one — confirm |

- [ ] **Step 4: Route every open residual to a named slice**

This is the response to the audit's sharpest finding: three deferrals named an owner by *description* — "the slice that next touches `correction.py`", "whichever slice next touches `validate`'s import path" — each was satisfied repeatedly, and none was honoured.

Walk every entry in `docs/superpowers/spec-defects.md` still owing something. For each, the deferral must name a slice `docs/superpowers/specs/2026-08-08-implementation-spine-design.md` defines, or a new one filed as a spine amendment. Rewrite any that does not.

Known cases:

| Residual | Route |
|---|---|
| The S4d residue row naming **S4e** | The spine defines no S4e. Assign it to the hardening slice that lands non-numeric recorded columns, and name that slice in the spine |
| `resolve_contrasts`'s unhashable-side guard (entry 1794) | The hardening slice that builds a caller reaching it without validating first — a `dry-run`-style path. Name that slice |
| `validate` crashing on wrong scalar leaf types (entry 462) | Its own hardening slice, as the entry argues. File the spine amendment |
| The two `repeat_spread` figures declined (entry 1326) | The hardening slice that threads a per-slice `aggregate` recompute through `cli.py` |
| `code_hash`'s `.gitignore` awareness, `parameters_hash` normalization (89 / 99) | The hardening slice for hashes |
| The missing-`uv.lock` question (191) | The `reproduce` slice |
| `E-SWEEP-BASELINE-PARTIAL` (683) | The slice that lands per-cell baseline expansion |
| The seven `E-DATA-*-UNSUPPORTED` and the other `-UNSUPPORTED` families (373) | Each retires with its own feature's slice — the existing policy, restated per entry |
| `W-ENV-UNLOCKED` (208) | Bootstrapping, not a defect: retires on the first release. Say so and close it |
| The S4c and S4d residue tables (1874 / 2009) | Row-by-row: each row either routes to a named slice or closes |

- [ ] **Step 5: Write the checkpoint's closing entry**

Append to `docs/superpowers/spec-defects.md`:

```markdown
## S5 checkpoint complete

Both `CLAUDE.md` consistency passes ran over the four documents on 2026-08-11. Every entry above
either closes, records work done, or names a slice the spine defines. No entry defers to a
description of a slice.

Open at close: <N> entries, each routed. The largest classes are the `-UNSUPPORTED` families, which
retire with their own features, and the hardening debts on hashes, `validate`'s type envelope, and
`repeat_spread`.
```

Fill `<N>` from the actual count.

- [ ] **Step 6: Verify no deferral names a description**

```bash
grep -rn "next slice\|a later slice\|a future slice\|whichever slice\|the slice that next" \
     docs/superpowers/spec-defects.md
```

Expected: hits only inside `**AMENDED**` blocks quoting the old wording. Any live deferral phrased this way must be rewritten.

- [ ] **Step 7: Full suite and commit**

```bash
uv run pytest && uv run ruff check . && uv run mypy
git add -A README.md CLAUDE.md docs/
git commit -m "docs: cross-document consistency pass closing the S5 checkpoint"
```

---

## Sequencing

Task 1 → task 2 → {tasks 3, 4, 5, 6, 7, 8, 9} → task 15 → task 16, with tasks 10–14 anywhere before task 15.

Tasks 3–9 own disjoint sections and are therefore independent, but they are **sequenced rather than parallel**: they land in the same file, and a merge conflict in `reference.md` costs more than the serialization saves. Task 4 depends on task 3 only for the anchor it links to (`#warnings-core-reports` is created by task 4, and task 7 links to it), so 3 before 4 before 7.

Tasks 1, 2 and any step writing only to `docs/superpowers/` produce **no commit** — that directory is gitignored, and an empty `git diff` for those tasks is the expected outcome, not a failure to report.

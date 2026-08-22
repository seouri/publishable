# H5a batch 3 (tasks 3–4) — review

Reviewed at `11dd8b3`, branch `h5a-artifacts-write-side`. Commits under review: `a2b6b51` (task 3),
`8822dc9` (task 4), `45aa4fc` (report). The batch touched `docs/reference.md`,
`docs/experimental-designs.md`, the plan (controller's appended correction) and the report — **no
`src/` or `tests/` file at all**, confirmed by `git diff 5c78bef..HEAD --name-only`.

## Verdicts

- **Spec compliance: PASS**, with **two Majors to close before this branch merges.** Both tasks did
  what Decisions 4/5/8, the two controller rulings and corrections 8/10 prescribe; the format binding
  is honoured; the mint lands in exactly the three sections the design names. What fails is emit-site
  fidelity in the one row the batch was isolated to get right: one shipped emit site is still
  uncovered, and two enumerated sites travel as a warning with no annotation saying so.
- **Task quality: PASS.** The implementer enumerated by reading before grepping, verified the
  untouched count phrase by re-deriving it, refused to silently pick a side on the plan's
  `.csv`/`.parquet` ambiguity, and named two concerns instead of claiming zero — a disclosure that
  produced a controller correction to the plan (`11dd8b3`). Both named concerns check out. The two
  Majors below are both the *same* failure the brief warned about, in the two places a brief could
  not warn: a clause traced to a neighbouring statement rather than to a raise site, and a brief's own
  claim about the code repeated without re-deriving it.

## Gates — all run, in the foreground

| Gate | Result |
|---|---|
| `uv run ruff check .` | `All checks passed!` |
| `uv run ruff format --check .` | `93 files already formatted` |
| `uv run mypy` | `Success: no issues found in 52 source files` |
| `uv run pytest` | **2845 passed, 1 skipped, 2 xfailed** (184s) — the expected count |

`__pycache__` cleared before the run; no `pytest-of-*` dirs existed. Tree left clean
(`git status` → `nothing to commit, working tree clean`), verified after a temporary probe test was
created, run and removed.

---

## Findings

**The principle these are graded against, established first.** § Errors core raises enumerates **every
emit site of a code and annotates how each one travels** — it is not a table of uncontained raises
only. Two shipped rows in that same table prove it: `reference.md:1120` reads *"all three are also
[reported by `validate`](#errors-validate-reports) under the same codes, reaching it through the
resolution it performs"*, and `:1118`'s sibling `E-DATA-MEASUREMENTS-*` clauses distinguish the surface
`validate` cannot reach from the ones it can. So a contained site **belongs** in the row, and the
defect is an unannotated one, never the site's presence. Both Majors below are graded on that one
reading.

### Major 1 — `docs/reference.md:1116`: `E-STEP-KEY-COLLISION`'s clause list omits a shipped emit site (`stats.py:3115`)

I enumerated the code's sites by reading `artifacts.py` and `stats.py`, then confirmed with
`grep -rn "E-STEP-KEY-COLLISION" src/`. There are **seven** raise sites covering **five** distinct
faults:

| Site | Fault | Named by the row? |
|---|---|---|
| `artifacts.py:649`, `:681` | a recorded column named `unit` (both `record` branches) | yes (added by task 3) |
| `artifacts.py:655` | a recorded column named `measurement` (`measurement=` branch only) | yes (added by task 3) |
| `artifacts.py:663`, `:689` | a recorded column shadowing a declared attribute | yes (pre-existing) |
| `stats.py:3123` | a derived key against a recorded column | yes (pre-existing) |
| **`stats.py:3115`** | **a derived key taking a reserved metric name (`by`)** | **no** |

The omission is load-bearing rather than cosmetic, because § Steps and artifacts links **into** this
row for exactly that fault: `reference.md:1242` reads *"A template's `aggregate` returning a derived
metric called `by` collides outright and raises `ContractError` ·
[`E-STEP-KEY-COLLISION`](#errors-core-raises)"*. A reader follows that anchor and finds a row whose
enumeration does not contain their fault. `RESERVED_METRIC_NAMES = frozenset({"by"})`
(`src/publishable/stats.py:34`) confirms the site is live.

The report discloses the choice and grounds it on "the brief's specific list of what to add" — and the
brief's list is where the gap comes from: it asserts the row *"names **neither** the `unit` nor the
`measurement` column collision"*, an incomplete claim about the code that the implementer's own
enumeration had already superseded. **Repeating a brief's claim about the code after your own
enumeration contradicts it is the documented failure mode**; the enumeration was done correctly and
then not acted on. Task 3's stated purpose — *one row per code covering EVERY emit site* — is not met
while one of five faults is unnamed.

### Major 2 — `docs/reference.md:1116`: two of the row's enumerated sites travel as a **warning**, and the row does not say so — contradicting `:386`

The widened row now positively enumerates *"a template's `aggregate` return"* under § **Errors core
raises**, and keeps the pre-existing *"a derived key against a recorded column"*. **Neither ever
reaches a user as a raised error.** Both are contained and re-reported as `W-STATS-AGGREGATE-FAILED`
with the `E-` code interpolated into the warning's text.

**Verified by running.** A temporary probe test (created, run, deleted; tree re-verified clean)
monkeypatched `GenericTemplate.aggregate` to return `{"total": [1, 2]}` and ran a real project through
`run_a_project`:

```
STATUS completed
HAS_WARN True     # W-STATS-AGGREGATE-FAILED on stdout
HAS_CODE True     # "E-STEP-RETURN-TYPE" appears inside the warning's message
```

**Verified by reading**, four independent confirmations:

- `src/publishable/cli.py:2922-2937` — the one unresampled `template.aggregate` call sits inside
  `try: … except Exception:` and converts the fault into `aggregate_c.warn("W-STATS-AGGREGATE-FAILED", …)`
  with the code as a message prefix. The other three `.aggregate(` sites (`cli.py:813`, `:2975`, and
  `stats.py`'s per-draw closures) are contained too — `stats.py`'s `except Exception` handlers treat a
  failed draw as degenerate.
- `src/publishable/cli.py:3014-3037` — the `summarize_step` call is wrapped in `except ContractError`
  for the same reason, and its own comment says it: *"while the sibling case (a structural return)
  merely warns."*
- `docs/reference.md:386` — § Warnings core reports **already owns both**: *"A template's `aggregate`
  produced no usable value … it raised, a returned key collided with one a step already recorded …
  Reported at `run` time."* Two normative rows, one asserting a raise and one a report, for one fault.
- `tests/test_cli.py:2709` and `:2738` — both cases are pinned as `status: completed` + a warning.

**Ownership, re-derived rather than charged by position.** The `aggregate` claim was *reachable* before
task 3 touched the row: the pre-edit row linked to `#steps-and-artifacts`, and `:1240` there reads
*"One rule, all three surfaces — `io.record`'s `values`, a step's return, and a template's
`aggregate`"*. So the tension between § Errors core raises and § Warnings core reports is
**pre-existing**; what task 3 did was turn a claim reachable through a link into an explicit clause in
the raise table, which is what makes it legible — and what makes leaving it unannotated this task's to
close. It is Major-grade because two normative rows now disagree in the four documents, not because a
clause was invented.

**Remedy.** Keep the sites and annotate the travel, on `:1120`'s own precedent — one clause saying the
`aggregate` and derived-key halves are **reported at `run` as
[`W-STATS-AGGREGATE-FAILED`](#warnings-core-reports) rather than raised**, and that the code appears
inside that warning's message. One annotation closes both halves. Do **not** narrow the containment to
make the table true: `cli.py:3062`'s comment states in capitals why the containment exists.

### Minor 3 — `docs/reference.md:1116`: "once coerced" is a further undisclosed forward-looking clause, and it makes the row narrower than shipped code

The clause reads *"a written `.parquet` row set whose rows disagree on a column's type **once
coerced**"*. Coercion inside `_encode_parquet` is task 9's; at HEAD `_check_column_types` runs over
raw types. Measured:

```
_encode_parquet([{'v': np.float64(1.5)}, {'v': 1.5}])
→ E-STEP-RETURN-TYPE  "column 'v' recorded both a float64 … and a float …"
```

Once coerced these two do **not** disagree, so for any non-`finalize` `.parquet` write the row is
narrower than the code it describes today — the same *row narrower than its code* shape that was two
of H8c's whole-branch Majors. It is correct post-task-9 and is inside Decision 8's scope, and task 12
step 4 ("`E-STEP-RETURN-TYPE`'s row against the finished code") owns the re-read. What is missing is
disclosure: the report's concerns section enumerates the `.csv`-cell clause as *the* unbuilt clause on
this row and does not name this one.

### Minor 4 — `docs/reference.md:1116`: the em-dash list reads exhaustive and omits a step's return **values**

The clause *"a step's `run` returning anything but a mapping or `None`"* names the shape check at
`runner.py:783` only. The very next line, `runner.py:785`, passes that same return through
`coerce_scalars`, so `return {"v": [1, 2]}` from a step is a shipped `E-STEP-RETURN-TYPE`
(`coercion.py:226`) that no item in the list names — while the sibling items are phrased as surfaces
(*"`io.record`'s values"*, *"a template's `aggregate` return"*) rather than as faults. The umbrella
phrase "A returned value core can't record" covers it, so this is a Minor: *"a step's `run`
return"* in place of the current wording covers both faults at that surface.

### Minor 5 — `docs/reference.md:1116` states as permanent spec what its sibling row hedged as "today"

The row asserts *"since a `.csv` write never unifies a column's type across rows"*, with no hedge, in
a table that has no `Status` column. Task 1's sentence about the same fact (`reference.md:998`) reads
*"does not unify a column's types across rows **at all today**"*, and correction 8 explicitly routes
the two formats agreeing as *"a disclosed behaviour change for another slice"*. Measured at HEAD:
`_encode_csv([{'v':'a'},{'v':1}])` → `b'v\na\n1\n'`. Two rows on one branch, two tenses for one
measurement; align them.

### Minor 6 — four new passages assert a refusal that does not exist at HEAD, and one of them engages a `CLAUDE.md` cross-document invariant that task 12's sweep list does not name

`reference.md:272` (§ Validation), `:629` (§ Errors `validate` reports), `:1244` (§ Steps and
artifacts — *"`validate` **now** refuses the declaration … and a `run` stops at the same gate"*, and
*"used to replace"* in the past tense) and `experimental-designs.md:384` all describe task 5's code.
Measured at HEAD by direct call:

```
resolve_units({'key':'pid','from':'t.csv','attributes':['unit']}, …)   → resolves, no refusal
finalize's merge over that roster                                     → {'unit': 'HIJACK', 'v': 1.0}
```

The mint-before-code order is Decision 4's, so this is sanctioned — but two things about it are worth
holding. First, the report's sentence *"No row claims a raise site that does not exist"* is true only
under a narrow reading of "raise site"; three of these four passages describe a **refusal** that does
not fire, and the disclosure is a half-sentence rather than the explicit hand-off task 3 wrote for its
own two unbuilt clauses. Second, `experimental-designs.md` § Mistakes core prevents is governed by
`CLAUDE.md`'s cross-document rule that *anything in it must be structurally impossible in the schema,
not merely discouraged* — false at HEAD — and **task 12's step-4 sweep list names three `reference.md`
sections and not `experimental-designs.md`.** Add the fourth home to that list, or the one passage
carrying an invariant has no named re-reader.

---

## What I verified about the report's own claims

The report names two concerns rather than claiming zero. **Both are true**, and the ambiguity it
flagged has since been ruled on by the controller (`11dd8b3` appends the binding to the plan).

**Concern 2 — the format binding — measured at HEAD, all three arms:**

| Claim | Measured |
|---|---|
| `.csv` refuses a structural / `bytes` cell | **not built** — `_encode_csv([{'v':[1,2],'b':b'x'}])` → `b'v,b\n"[1, 2]",b\'x\'\n'` (the corruption case) |
| `.parquet` accepts both, byte-faithfully | **true** — `_decode_parquet(_encode_parquet([{'v':[1,2],'b':b'x'}]))` → `[{'v': [1, 2], 'b': b'x'}]` |
| cross-row unification for `.csv` is not built | **true** — `.csv` writes `b'v\na\n1\n'`; `.parquet` raises `E-STEP-RETURN-TYPE` |

So the shipped rows honour the binding: the cell clause is bound to `.csv` alone and no `.parquet`
refusal for a structural cell was documented. The implementer's reading was correct and the plan text
it contradicted was the superseded one.

**Concern 1 — the two unbuilt clauses — confirmed unbuilt:** `_encode_csv`/`_encode_parquet` handed a
non-mapping row raise a bare `AttributeError` (`'list' object has no attribute 'keys'` / `'get'`), not
`E-ARTIFACT-UNWRITABLE`. **Task 9 can be held to both**: its plan step 9 is *"re-read the § Errors
rows task 3 wrote"*, and task 12 step 4 re-checks the row against the finished code. See Minor 3 for
the clause the concerns section missed.

**Named greps re-run, with their scope:**

| The report's claim | My result |
|---|---|
| `grep -rn 'E-STEP-RETURN-TYPE' src/` → three raise sites, no fourth | **confirmed** — `runner.py:783`, `coercion.py:226`, `artifacts.py:118`; the two other hits are docstrings. Scope `src/` is the right scope for a raise-site count |
| `grep -rn 'E-ARTIFACT-NAME' src/` → exactly four `_contained(…)` call sites | **confirmed** — `artifacts.py:819`, `:908`, `:964`, `:1193`; hits at `:1035`, `:1037`, `:1178` are prose. The untouched count phrase *"Four emit sites for the escape alone"* holds, and `reuse_from` raises `E-UPSTREAM-NAME` rather than inflating it |
| `E-ARTIFACT-UNWRITABLE` → exactly one raise | **confirmed** — `artifacts.py:844` only |
| `"set of one"` → one hit in the four documents, unedited | **confirmed** — `reference.md:1242` only; `RESERVED_METRIC_NAMES = frozenset({"by"})` so the sentence stays true |
| house style "at line 314/319's own rows" | **confirmed** — both § Validation rows carry a parenthetical `E-` code, so `:272`'s two parentheticals match a real convention |
| `_encode_csv` has no `_check_column_types` call | **confirmed** — one caller, `artifacts.py:132`, inside `_encode_parquet` |
| `E-UNITS-ATTR-RESERVED` is not in § Errors core raises | **confirmed** — zero `E-UNITS-ATTR*` hits between `:1088` and `:1248`; the new row is at `:629`, inside § Errors `validate` reports (`:409`–`:803`) |
| correction 10 — one emit path | **confirmed by reading `cli.py`** — `command_run` calls `validate_config` at `:1953`, returns `EXIT_WRONG` at `:1958`, and reaches `resolve_units` only at `:2017`. The row's "before its own `resolve_units` call" is exact |
| the `E-APPARATUS-FACT-TYPE` cross-reference | **confirmed** — `reference.md:1131` does state *"sharing a mechanism without sharing the fault: `coerce_scalars` is the one scalar walk both use"*. No false claim about a neighbouring row |

## Attack 7 — the guard pin

**None fired and none was edited.** `git diff 5c78bef..HEAD --name-only` returns four files, none in
`tests/` or `src/`, so arm D, arm E1 (`.parquet`, no authorized editor) and arm E2 (`.csv`, task 9's)
are byte-unchanged. Arm D reads `reference.md` as raw text and both tasks edited that file — it stayed
green in the full-suite run above, which is the interesting half: the insertions at `:272`, `:629`,
`:1244` carry no worked-example literal.

## Attack 6 — both consistency passes

**Mechanical, over `README.md`, `docs/design-principles.md`, `docs/experimental-designs.md`,
`docs/reference.md` named explicitly (never `*.md`), fences skipped:** zero broken relative links,
zero unresolved `#anchor`s, zero duplicate heading anchors, zero trailing whitespace, zero tabs, zero
invisible unicode. Three table-column-count reports are `\|`-escaped pipes inside inline code
(`reference.md:621`, `:1729`, `:3573`), all pre-existing and all outside this diff.

**Each sweep proven able to fail**, on a scratch copy with four faults injected: a duplicate
`## Errors core raises` heading → `DUP ANCHOR`; `[bad](#no-such-anchor-xyz)` → `BAD ANCHOR`; a
trailing-space line → `TRAILWS`; a tab line → `TAB`. All four reported.

**Locators and count phrases near every insertion:**

- `:272` and `:1116`/`:1102` are in-place edits — no row moved.
- `:629` inserts a row into § Errors `validate` reports. The only "row above" locator in that
  neighbourhood is `:407` (`W-ENV-UNLOCKED`), which sits in the warnings table **above** the
  insertion; `:630`'s *"the same reuse `E-REPL-SEED-COLLISION` above illustrates"* still points above
  (`:569`). The new row's own "`E-UNITS-ATTR-RESERVED` row above" is correct (`:628`) and identifies
  by code, not position.
- `:346`'s *"Six things deliberately absent from that table"* enumerates six absentees, none of them
  this refusal — the § Validation edit **adds** to the table, so the count is unaffected. Its
  *"'Reporting stratum is populated' row above"* and *"the batch row above"* both still resolve, since
  `:272` moved nothing.
- `:1244` inserts a paragraph four lines below `:1240`'s *"One rule, **all three** surfaces"* — the
  one count phrase the branch will falsify. **It is already owned**: plan `:1208` assigns it to task 9
  with *"drop the count"*, and plan `:782` forbids the neighbouring task from touching it. Correctly
  handled; noting it as a positive rather than a finding.
- `experimental-designs.md:384` is appended at the end of the Bookkeeping table — no row moved, and
  that table carries no count phrase.

**Cross-document, over the four documents only:** `README.md` and `design-principles.md` mention
neither `E-UNITS-ATTR-*` nor a reserved-name set, so nothing needed mirroring. No config field, no
enum value, no version, no worked-example number touched (arm D is the mechanical proof of the last).
`E-UNITS-ATTR-COLUMN`'s four homes are exactly the three `reference.md` sections plus
`experimental-designs.md` — matching plan `:1421`'s expectation, with the caveat in Minor 6.

## What I could not check

- **Whether tasks 5 and 9 actually land the behaviour these rows promise.** Nothing mechanical forces
  it: there is **no docs↔code `E-` registry test** in `tests/` (searched for one; the suite would be
  red if it existed, since `E-UNITS-ATTR-COLUMN` has no raise site). The only guards are prose —
  task 9 step 9, task 12 step 4 — which is why Minor 6 asks for `experimental-designs.md` to be added
  to that list.
- **The `spec-defects.md` contradiction is live and I left it.** The `finalize` `unit`-shadow filing
  (`docs/superpowers/spec-defects.md:3278`) still reads *"Pre-existing, live, and reachable from a
  config that validates clean"* — true of the code, now contradicted by four passages saying the
  declaration is refused. Task 12 owns striking it; correction 11 has the right diagnosis of its wrong
  prediction. Not a batch-3 finding, recorded so it is not discovered late.
- **Whether `.csv`'s eventual refusal is the right call for a real project.** Unmeasurable, and the
  plan's § What could not be measured already says so.

# The S5 checkpoint design

**Goal:** resolve `docs/superpowers/spec-defects.md` into the four documents, so that the
reference implementation and its specification describe the same tool.

**Why now:** the spine document defines the checkpoint as what follows S5 — "every entry in the
spec-defect ledger is resolved into the four documents, and both consistency passes from
`CLAUDE.md` run once over the result." S5b merged on 2026-08-10 and the reference implementation is
complete. Hardening slices follow the checkpoint, not the other way round: each of them retires
`-UNSUPPORTED` codes and adds document rows, and doing that against a specification already known
to be wrong compounds the divergence.

## What the audit found

All 98 `##` entries were read and every factual claim about code was checked against `HEAD`. The
file is **less open than its headings suggest and more stale than it admits**: 31 entries are pure
records of a minted identifier, 20 are answered, 6 are historical duplicates, and 41 still owe
something — of which the large majority owe one document line, not a code decision. The findings
are in `docs/superpowers/CHECKPOINT-AGENDA.md`; this spec does not restate them, it slices them.

Three facts drive the decomposition:

- **The largest owed change is not an entry at all.** 105 of the 130 identifiers `src/` emits
  appear in none of the four documents.
- **Eleven claims are stale**, five of them at heading level. A checkpoint that triages by scanning
  headings will act wrongly on `read_upstream can only reach run-scoped steps — MARKED FOR THE NEXT
  SLICE`, which was fixed in S3b.
- **"Assigned to slice N" has silently failed three times.** `rank_family`, `aggregate`'s table
  attributes, and the `SystemExit` arm each named an owner; each owner merged without the work.
  That is why this checkpoint routes residuals to *named* slices with a recorded owner, and why
  C8 exists.

## The discriminator: sections, not entries

Slices are drawn by **which document section gets edited**, not by which ledger entry closes.

Every edit to the four documents triggers both `CLAUDE.md` consistency passes. Entry-per-slice
would run the mechanical pass thirty-plus times over the same anchors and would have several
slices re-anchoring the same heading — the exact churn the cross-document pass exists to catch.
Section-per-slice makes each slice's blast radius a contiguous piece of one file, and makes the
final pass meaningful because it runs once over a settled tree.

One consequence to accept rather than tidy: a single ledger entry can be split across slices when
it owes both a code change and a document line. Entry 2311 (§ `Estimate` should state six rules)
owes two prose lines to C5 and two identifier rows to C2. The ledger entry closes when both land,
which is C8's job to check.

## The slices

| Slice | Owns | Kind |
|---|---|---|
| **C0** | Ledger hygiene — amend the 11 stale claims | Controller |
| **C1** | The nine adjudications that gate transcription | Design |
| **C2** | § Errors core raises, and the warning registry | Documents |
| **C3** | § Package layout, § The importable surface | Documents |
| **C4** | § Validation, § Statistical reporting, § How artifacts are organized | Documents |
| **C5** | § Pre-registration, § `Estimate` | Documents |
| **C6** | § The two files | Documents |
| **C7** | The code debts | `src/` |
| **C8** | Both consistency passes; route every residual to a named slice | Verification |

C7 touches no document and C2–C6 touch no code, so C7 may run at any point. C1 blocks C2 through
C6. C0 blocks everything, because every later slice reads the ledger.

### C0 — Ledger hygiene

**Not a dispatched task.** `docs/superpowers/` is gitignored, so `scripts/review-package` would
hand a reviewer an empty diff. C0 is controller work done inline, and its output is the amended
ledger.

Each of the eleven stale claims gets an amendment **at its own heading**, not a new entry lower in
the file. A new entry is what created the staleness: five of these were closed by a later entry
that never touched the earlier heading. The amendment names the closing entry's line and the code
that closes it.

| Entry | Amendment |
|---|---|
| 715 | Fixed in S3b; `artifacts.py:460-478` resolves per target scope. Drop the marker |
| 1557 | Floor landed, `stats.py:183-186`. Second claim ("nothing calls it") still true |
| 1637 | Read at `cli.py:869`. Its `min_clusters`/`min_units_per_cell` claims survive |
| 1646 | Fixed at `validate.py:992` |
| 1664 | Present in `_check_shape`'s nested pass; residue moves to entry 1794 |
| 150 | Six modules, not one: `runner`, `coercion`, `contrasts`, `correction`, `estimate`, `strata` |
| 2054 | Seven names, not five; and **zero** of the four registries exist — `register_template` is not a decorator, the registry is `get_template`/`template_names` |
| 279, 598 | Now in § Errors core raises' last row |
| 1206 | Landed; the row is in `reference.md` |
| 2472 | Not reachable, but contained only by `except Exception` blocks documented as degenerate-draw handling, and no test pins it |
| 2016 | Names **S4e**, a slice the spine does not define. Reassigned by C8 |

C0 also files the one finding the ledger never recorded: **`E-UNIT-IMMUTABLE` is documented in
`reference.md` and implemented nowhere.**

### C1 — The adjudications

Nine decisions gate the transcription slices. C1's deliverable is a decisions record appended to
the ledger, each decision naming the slice that transcribes it. `design-principles.md` is the
tiebreaker for all of them; two were already settled by the user and are recorded here as settled.

| # | Decision | Recommendation and grounds | Transcribes in |
|---|---|---|---|
| 1 | Where 13 unnamed `W-` codes live | **§ Validation gains a diagnostics table**, beside § Errors core raises' shape. A warning is a diagnostic with an identifier a user greps; a separate registry file has no precedent in the four documents | C2 |
| 2 | `E-UNIT-IMMUTABLE` | **Settled: implement the coded refusal.** A documented identifier nothing raises is the class this repo says must not exist | C7 |
| 3 | "the complete parameter set" | **Settled: narrow the phrase.** The code route changes what `init` writes, which is `parameter_spec`-driven — the single-source-of-truth invariant | C4 |
| 4 | `supported: null` | **§ Pre-registration states three verdict states** and both routes producing the third (an unresolvable observation; an absent interval). A `false` there is indistinguishable from a tested-and-failed claim | C5 |
| 5 | Unbuilt names in § The importable surface | **Keep them, marked unbuilt.** The table is the enumerated normative surface; deleting `register_*` would delete the plugin contract four hardening slices build against | C3 |
| 6 | Reserved metric names | **§ Steps and artifacts states the reserved set**, currently `{by}`. `report_by` spends it, and a user learns this today only by collision | C4 |
| 7 | A `run`- or `condition`-scoped step's return | **State that it is not recorded**, rather than inventing a `results` block. Wide scopes have no unit or repeat to key a value by | C4 |
| 8 | `Config.raw` | **State that the root node carries one accessor and nested nodes carry none.** A top-level key named `raw` is shadowed; that is a real narrowing of "no methods at all" and belongs in the document | C3 |
| 9 | Finding order | **Amend the sentence**, not the code. § Exit codes promises config-position order; `validate` collects by check. Ordering findings by document position needs position tracking through every check — a hardening change, not a checkpoint one | C4 |

A decision C1 reverses is fine; a decision C1 leaves open is not, because it becomes a transcription
slice blocked mid-flight.

### C2 — § Errors core raises, and the warning registry

The largest slice, and near-pure transcription once C1 lands.

**Verified before slicing:** all 12 raise-time `ContractError`s below are in `src/` and in none of
the four documents. `src/` emits 18 distinct `W-` codes; the documents name 5.

- **12 error rows** — `E-REPL-SEED-COLLISION`, `E-STEP-NAME-COLLISION`, `E-STEP-EXISTS`,
  `E-STEP-SCOPE-UNKNOWN`, `E-STEP-SCOPE-ONLY`, `E-STEP-UNIT-UNKNOWN`, `E-STEP-UNIT-SETTLED`,
  `E-STEP-UNITS-CONTRACT`, `E-STEP-READ-CONDITION-UNKNOWN`, `E-STEP-READ-REPEAT-REQUIRED`,
  `E-STEP-ESTIMATE-CI95`, `E-STEP-ESTIMATE-VALUE`. Each belongs in that table by the table's own
  framing.
- **13 warning rows** into C1's chosen home.
- **The named orphans** — `E-IO-FAILED` (with § Exit codes stating that a local `OSError` exits
  `1`), `E-SWEEP-EXPANDS-EMPTY`, `E-STATS-CONTRAST-WITHIN`, `E-STATS-REPORTBY-UNKNOWN`, the
  `E-REPL-LEVEL-*` family, and the `E-HYPOTHESIS-*` family.

**The `-UNSUPPORTED` policy is restated, not re-litigated.** Ledger entries 1416 and 1515 make it
policy that a `-UNSUPPORTED` code stays out of the documents and retires with the slice that
implements its feature — a document must not name an error for a feature it specifies as working.
14 live codes are covered. Without this restated in the slice's brief, a reviewer flags 14 missing
rows.

### C3 — The structural tables

- **§ Package layout** adds the six built modules the tree omits. The eleven listed-but-unbuilt
  modules stay: they are specified features, and the table is a specification.
- **§ The importable surface** reconciles with `__all__`, which holds exactly nine names. Seven
  named names are unexported: `Unit`, `Apparatus`, `BaseReport`, and the four `register_*`
  decorators. `Unit` is built and gets exported — a step receives one and a plugin author needs the
  type. The other six are marked unbuilt per C1 decision 5.
- **§ The importable surface** states C1 decision 8, the root accessor.

The reverse direction is clean: nothing is exported that the table does not name.

### C4 — § Validation, § Statistical reporting, § How artifacts are organized

Nine prose changes, four of them C1 decisions.

| Change | Entry |
|---|---|
| § Validation's table lists two run-time warnings as validate-time checks — split the rows | 1968 |
| The reserved metric name set (C1 decision 6) | 1928 |
| A wide step's return is not recorded (C1 decision 7) | 227 / 246 |
| Finding order — amend the sentence (C1 decision 9) | 325 |
| No interval below two units | 525 |
| `__` is not admissible in a swept value; only `sweep.py` refuses it today | 558 |
| `io.conditions` yields `(index, label)` | 624 |
| `default_repeats` is a repeat **floor**, not a materialized value | 12 |
| "the complete parameter set" narrows (C1 decision 3) | 29 |

### C5 — § Pre-registration and § `Estimate`

- Three verdict states and both routes to the third (C1 decision 4).
- The `observed` block carries `method`; the example shows three keys and should show four.
- § `Estimate` states four rules and should state six — the `ci95` element type and a numeric
  `value`. The two identifiers go to C2; the two prose lines are here.
- The required `hypotheses` fields, and the two § Validation rows entry 2370 names.

**No worked-example number changes.** § Pre-registration is worked-example territory, and
`CLAUDE.md` pins `h1`'s divergent verdicts, the delta 0.026, the interval [−0.007, 0.059], and the
threshold 0.02 — including "must not be narrowed back." C5 adds a key to an example block and adds
prose; it changes no figure. This is stated here so a reviewer does not flag the untouched numbers.

### C6 — § The two files

- `run.yaml` gains `layout` and `provenance.input_manifest_changed`, neither of which appears in
  any example.
- `per_repeat`'s shape when nothing repeats — the `""` key.
- A single repeat's dispersion. Entry 525 answered this for `basis: units`; the repeats case is
  open.

### C7 — The code debts

Five, plus C1 decision 2. This is the only slice touching `src/`, and every change needs a test
that fails against the current implementation.

| Debt | The change |
|---|---|
| `rank_family` tie-breaks lexicographically where `reference.md` says declaration order | Thread a declaration index onto `Member`; `correction.py:129`'s key becomes `(-ratio, declaration_index)`. `where` is currently omitted from the key entirely |
| `SystemExit` at module scope escapes `validate`'s `except Exception` | An `except SystemExit` arm beside `validate.py:219`, reporting `E-ENTRYPOINT-IMPORT`. A user-chosen exit code with no diagnostic is the current behaviour |
| The table `aggregate` receives omits declared unit attributes | Thread the roster into `cli.py`'s `UnitTable`. Needs a collapse rule for strings — a non-numeric attribute collapses only if constant across the unit's repeats |
| A non-numeric `aggregate` return reaching `float()` | Not reachable, but contained only incidentally by `except Exception` blocks whose docstrings justify them as degenerate-draw handling. Pin it with a test: a template returning `{"m": "high"}` yields `ci95: null`, `W-STATS-AGGREGATE-FAILED`, and a `str` value |
| `E-UNIT-IMMUTABLE` (C1 decision 2) | `Unit.__setattr__` raises `ContractError` with the documented code, after `__init__`. `units.py:24` is `@dataclass(frozen=True, eq=False)` today, so the raise is a bare `FrozenInstanceError` that `main()` does not catch |
| Two narrow holes in `_check_contrasts` | Widen the `expand` guard; decide `compare: {condition: X}` with no `to` and no baseline, which fires neither check |

`contrasts.resolve_contrasts`'s unhashable-side guard (entry 1794) is **not** in C7. It is safe
while every path validates first, and the caller that reopens it — a `dry-run`-style path — does
not exist. C8 routes it to the slice that builds one.

### C8 — The consistency passes and the routing

Two deliverables.

**Both `CLAUDE.md` passes over the four documents.** The mechanical pass — every relative link and
`#anchor` resolves, no duplicate anchors, table rows match their headers, no trailing whitespace or
tabs or invisible unicode, `×` not `x`, hyphens not en dashes in anything that becomes an anchor,
fenced blocks skipped throughout. Then the cross-document pass, whose seven classes are the ones
that actually drift; the shared worked example and config completeness are the two C2–C6 most
plausibly disturbed.

**Every residual routes to a named slice with an owner.** The ledger's failure mode is a deferral
whose owner is a description rather than a name: "the slice that next touches `correction.py`",
"whichever slice next touches `validate`'s import path". Both were satisfied repeatedly and neither
was honoured. C8 rewrites every open deferral to name a slice the spine defines, and files a spine
amendment for any that has no home — starting with the S4d residue row that names **S4e**, which
does not exist.

Legitimately deferred, and named as such: the seven `E-DATA-*-UNSUPPORTED` refusals and the other
`-UNSUPPORTED` families (each retires with its feature's slice), `E-SWEEP-BASELINE-PARTIAL`
(per-cell expansion), the missing-`uv.lock` question (`reproduce`), `code_hash`'s `.gitignore`
awareness and `parameters_hash` normalization (hardening), the two declined `repeat_spread` figures,
and `W-ENV-UNLOCKED`, which is bootstrapping rather than a defect and retires on the first release.

## What this checkpoint is not

- **Not a re-audit.** The classification and the eleven staleness findings are inputs. C0 records
  them; no slice re-derives them.
- **Not a hardening slice.** No refused feature is implemented, no `-UNSUPPORTED` code retires, and
  no CLI command is added. C7 is five bounded fixes to code that already ships.
- **Not a worked-example revision.** No pinned figure changes anywhere.

## Risks

- **A document row that describes code wrongly.** C2 transcribes 25+ identifiers; a row stating the
  wrong condition is worse than a missing row, because a missing row is a known gap and a wrong row
  is a false promise. Every C2 row cites the raising line, and the reviewer checks the row against
  it rather than against the ledger.
- **C1 leaving a decision open.** Nine decisions, six transcription slices; a decision deferred
  blocks a slice mid-flight. C1's deliverable is checked for nine answers before C2 dispatches.
- **The consistency passes running over a moving tree.** C8 runs once, last. A C7 fix landing after
  C8 is fine — it touches no document — but a late document edit means C8 re-runs.
- **The ledger amendments drifting from the code again.** C0's amendments cite line numbers, which
  go stale. Each cites the module and the function alongside, which do not.

## Task sequencing

C0 → C1 → {C2, C3, C4, C5, C6} → C8, with C7 anywhere before C8. The transcription slices are
mutually independent by construction — each owns disjoint sections — but they are sequenced rather
than parallel, because they land in the same files and a merge conflict in `reference.md` costs
more than the serialization saves.

# H9b — `resume` — whole-branch review

**Verdict: HOLD.** Four Majors, none behaviour-affecting, all of them record, document or
test-hygiene defects — and two of them are the exact faults this repository names by hand and this
branch's own earlier review already raised in another form. The precedent is explicit (H7d Part A: *"a
whole-branch review held the merge on two Majors, both closed the same day"*). The code is sound:
`resume` works end to end, the takeover is correct under contention, and a crash-and-resume produces
the record an uninterrupted run would.

Branch `h9b-resume` at `6ddd882`, 38 commits ahead of `main` (`f2e545d`). Reviewed as batch reviewer
for tasks 10–18 and as the whole-branch gate; the task-level verdicts and every mutation table are in
[`task-b4-review.md`](task-b4-review.md).

## Gates

| Gate | Result |
|---|---|
| `uv run pytest` | **3132 passed, 1 skipped, 2 xfailed** (259 s) |
| `uv run pytest` on a `main` worktree | **3019 passed, 1 skipped, 2 xfailed** |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 93 files already formatted |
| `uv run mypy` | no issues in 52 source files |

**The whole delta accounted for, not just batch 4's.** Collected counts: `main` **3022**, HEAD
**3135**, `+113`, and every one attributed by file — `test_cli.py` +49, `test_run_identity.py` +49,
`test_lineage.py` +10, `test_run_record.py` +3, `test_freeze.py` +2 = 113. **Zero test functions
removed** (`git diff main...HEAD -- tests/ | grep "^-" | grep -c "def test_"` → 0). `3135 = 3132 + 1
skipped + 2 xfailed`; `3022 = 3019 + 1 + 2`. The xfail count is 2 on both sides because batch 1 added
two strict xfails (arms A and G) and batch 4 converted both — so the 4 → 2 movement the batch-4 report
describes reconciles against `main`'s standing 2.

Every mutation in this review was applied by editing, reverted by editing back, and the reverts were
verified **by re-running**: the closing full suite returned exactly `3132 passed, 1 skipped, 2
xfailed` with `git status` clean.

## The gate questions

### `run`'s artifacts, diffed against `main` on one real config

A scaffolded project outside the repository (`publishable new` → `init myexp --template generic`,
2 conditions × 2 seed repeats over 4 units), run once with `main`'s `src/` and once with HEAD's,
through `cli.main`.

| Comparison | Result |
|---|---|
| run directory, path by path | **exactly one new file: `identity.json`** |
| `run.yaml`, leaf by leaf | **98 leaves each, key order identical, 0 value differences** outside the two my own fixture introduced (`config.data.output_dir`, `provenance.git.commit`) |
| `executions.jsonl`, key by key, line by line | 4 lines each; **`added = ['recorded_columns','returned']`, `removed = []`**, the eight pre-existing keys in unchanged order, **no value difference** on any line outside `started_at`/`wall_seconds` |
| stdout | **byte-identical** |
| stderr | **byte-identical** |
| exit code | 0 on both |
| `dry-run` | **`and 7 fixed files` → `and 8 fixed files`** (this project has no `uv.lock`; the document's transcript says 9 and that figure is derived — the shipped tuple is 8 entries plus `environment/uv.lock` when a lockfile exists, and the transcript lists all nine by name) |

**Every difference is one the slice disclosed** — items 1, 2, 3 and 4, plus `lock`'s third key, which
is disclosed in § Is this additive?'s *"what does not move"* paragraph (*"`RunLock.__enter__`'s claim
is byte-unchanged apart from the third key it writes into its own JSON payload"*) and does not appear
in a finished run directory because the lock is removed. **There is no fifth undisclosed thing.**
This is also the behavioural verification of guard-pin arm F, which cites H9a arms A and B rather than
re-capturing them.

### Does a crash-and-resume produce the record an uninterrupted run would?

**Yes — leaf for leaf, and including `attempts`.** Same project, a repeat step that `os._exit(137)`s
on its third execution keyed off a counter file outside `input_dir`, everything through the
**installed console script**:

- `publishable run` (control) → exit 0.
- `publishable run` with the crash → exit **137**, a directory holding `config.yaml`,
  `environment/{pyproject.toml,repo_root.txt}`, `executions.jsonl`, `identity.json`,
  `manifest/input.json`, `sweep.yaml`, **`lock`** (three keys, a real reaped pid on this host), two
  `units.parquet`, **no `run.yaml`**.
- `publishable resume <dir>` → exit **0**, the takeover removed the stale lock, all four triples
  present, `run.yaml` written, `lock` and `lock.takeover` both gone.

`run.yaml` against the control: **98 leaves each, key order identical, 0 value differences** after
normalizing timestamps, run ids, hostnames, hashes and the git commit; `code_hash`,
`parameters_hash`, `input_manifest_hash` and `uv_lock_hash` **equal without normalization**; 4 ledger
lines each.

**One clause the answer needs, so it does not overclaim.** This crash left the interrupted triple
**no ledger line**, so `attempts` came back `1` on both sides and the normalization never bit.
`attempts` becomes `2` only for a triple that was actually re-executed — a contained failure — which
is disclosure item 4, is on arm A's normalization list by design, and is pinned by
`test_h9b_a_contained_failure_then_a_resume_records_two_attempts` (killed by mutation E4 below). So:
identical including `attempts` for a crash that wrote no line; identical modulo `attempts` for one
that did, by disclosure.

### Cross-batch interactions — every earlier guard mutated, every one still alive

The chain is `identity.json` (batch 2) → the ledger's two keys (batch 3) → reconstitution (batch 4) →
the baseline replay (batch 6) → the lock and the record write (batch 8). Each earlier guard mutated
independently; **none is dead and none is carrying a claim a later batch falsified**, with one
exception, which is Major 2.

| # | Guard mutated | Result |
|---|---|---|
| N1 | `take_over_dead_lock` → bare `return` | **FULL: 21 failed**, 3111 passed — 19 unit tests, arm G, **and arm A** |
| E1 | `_reconstitute` → `return ()` | 21 failed (scoped) |
| E2 | the `identity.json` write neutered | 29 failed (scoped) — including arm B and both `freeze` arms |
| E3 | `recorded_columns` always `[]` | 9 failed (scoped) |
| E4 | `attempt_counts` → `{}` | 4 failed (scoped) |
| E5 | `baseline=Observations()` — the replay dropped | 2 failed (scoped) |

**One mutation-blindness prediction of the reports reproduces and is worth carrying**: M6, the
`_dispatch` hoist, is blind on a **full unfiltered** run. The report derived that rather than guessing
it, and reported it rather than banking the silence — which is the right handling; the residue is
Minor 4 in the task review.

### The filings

Three new OPEN entries, one STRUCK, one NOT-A-DEFECT record; every owner a fact with a reason.

| Entry | Reproduced |
|---|---|
| OPEN — `repo_root.txt` has a **third** reader repeating the same refusal triple | Yes: `freeze.py:176`, `report.py:774`, `run_identity.py:330`. Owner *"unassigned, no remaining slice owns `freeze` and `report` together"* — a fact |
| OPEN — `io.record`'s collision check reads only the first unit's attributes | By reading; owner names H5 as closed |
| OPEN — a resume stopped by an **unreachable** apparatus writes no record | Yes: `E-APPARATUS-RAISED` still returns `EXIT_EXTERNAL` before `assemble_run_yaml` (`cli.py:3421`). The terminality argument is argued, not asserted, and I do not disagree with it |
| STRUCK — the run-start `parameters_hash` gap | Genuinely closed: `E-FREEZE-CONFIG-EDITED`, pinned, and M11 kills the pin. **Struck, not deleted** |
| NOT A DEFECT — `H9-SCOPING.md` § 4.5's `aggregated`-survives claim | Recorded rather than retro-edited, correctly |

**The one filing that is missing is Major 3** — `freeze._assert_refused`'s code-blind helper, which
lives only in the batch-4 report's *Concerns* section.

### The development record was not retro-edited

`git diff main...HEAD` over `docs/superpowers/specs/`, `docs/superpowers/plans/`,
`docs/superpowers/H9-SCOPING.md` and `.superpowers/` produces **zero deletion lines**. Every
correction is appended: the design carries three (arms B/D's editor; task 16's record-loss amendment;
batch 4's item-by-item disclosure check), the plan carries corrections 21–22 and four task amendments,
and two batch reports carry appended corrections. `spec-defects.md` is the sole file with deletions
(6), all of them the struck entry and the amended count chain — which is what that file's exception is
for.

### The feasibility analysis

`+55` lines, **one deletion line** (a section-list bullet). The four-row table extracted rather than
retyped: programmatically, nine of the ten `| Figure | Count | Visible to` blocks in the file are
**byte-identical at 785 characters** (the tenth is the pre-H8a shape), the H9b entry's among them — so
its cells still name **H8a**, correctly. **No fifth number.** § Executability's movement re-derived by
me, row by row: row 1 — `resume` is called from no `validate` path and from no step, so `validate`'s
answer is unchanged; row 2 — `_prepare_run` is the same call, the upstream ledger untouched; row 3 —
the gap is a construction inside `summarize_step`, which the branch does not touch and which a
resumed run reaches through the identical function; row 4 — none of the nine declares an
`apparatus_probe`, a `study`, a `fold` or a group axis, so none can reach the replay, the takeover or
the allocation reader. **Zero configs unblocked, four rows unmoved. Confirmed.** Its one wrong figure
is Major 4.

## Findings, one line each — all four routed

| Sev | Finding | Route |
|---|---|---|
| **Major 1** | `E-RESUME-LEDGER-UNREADABLE` has **four** emit sites (`lineage.py:478/483/489`, **`cli.py:2262`**) while `docs/reference.md:658` says *"Three faults, one code"* and denies the fourth by name (*"`returned` and `recorded_columns` are **not** in the required set: a ledger written by an earlier build reads clean here"*) — the very amendment item task 16 was told to close, answered with a count carried from the brief | Widen the row; **delete** the *"reads clean here"* clause; append a correction to the batch-4 report, whose *"item (a), closed"* is what a later reader trusts |
| **Major 2** | `cli.py:4880–4890` — `command_resume`'s own docstring asserts *"Decision 13 is NOT implemented here"*, *"`resume` is not dispatched"*, *"the containment does not exist yet"* and *"Task 16 owns building it"*, all four false at HEAD, eighteen lines above the containment itself, and contradicted by the same docstring's closing sentence | **Delete** the paragraph; reconcile the closing sentence, which still calls `command_resume` its own only caller |
| **Major 3** | `tests/test_freeze.py:115`'s `_assert_refused` never reads the `code` it is handed — **21** call sites assert *that* a refusal happened and its exit code, not *which*; renaming `E-FREEZE-RUN-ENDED` → `E-FREEZE-BOGUS-MUTATION` leaves `tests/test_freeze.py` at **42 passed**, and that code has exactly one test reference. H8b's (`60f5d61`), untouched by this branch, and filed **nowhere** — it lives in a Concerns section, which is the fault this branch's own batch 3–4 review already raised as a Major | **File** it in `spec-defects.md` with the reproduction, the count of 21, and an owner that is a fact |
| **Major 4** | `docs/feasibility-llm-growth-studies.md:2154` says H9b mints *"thirteen `E-RESUME-*` codes … every one of the fourteen"*; the emit sites give **fourteen** `E-RESUME-*` codes and **fifteen** rows, and design Decision 17's own table contradicts its own prose — a carried count landing in the one section the procedure requires dated and re-derived | Correct the sentence to fourteen/fifteen; append a correction to Decision 17 citing its own table |
| Minor 1 | `run_identity.py:69`'s *"A lock left by a killed process is reported, never assumed dead"* was **not** narrowed when task 17 narrowed the identical `docs/reference.md:894` sentence to *"for `run` and `draft`, and for every case a liveness test cannot answer"* — and `RunLock` is step 4 of the takeover | Narrow the message |
| Minor 2 | `tests/test_cli.py:23761` (*"`resume` is not dispatched until plan task 15 … arm A's resume half stays `xfail`"*) and `:24677` (*"task 14's takeover does not exist yet"*) are false at HEAD | Delete the stale clauses |
| Minor 3 | the appended design correction fixing arms B/D's editor asserts *"arm C → task 6 … correct"*; the plan gives arm C to **task 5**, and `d4e0afd` (task 5) is where it was edited — the same fault one row over, inside the correction written to fix it | Append |
| Minor 4 | M6 is blind on a full run, so `_dispatch`'s *"Safe only because of this function's branch ORDER"* is constrained by nothing at HEAD; disclosed by the report, filed nowhere | File it |
| Minor 5 | `E-RESUME-ALLOCATION-STALE`'s row names six fault phrases against nine shapes; `cli.py:2404`'s per-axis *"not a mapping"* is not distinctly named | Widen or accept explicitly |
| Minor 6 | report accuracy: concern 2's *"the end-to-end pin is arm G"* omits arm A (the takeover no-op fails it), and concern 3's *"ten shipped gate tests"* is 21 | Append to the batch-4 report |

## What this branch got right, stated so the HOLD is not read as a verdict on the work

The race criterion correction is the most valuable thing in the batch and it reproduces: **a
token-less control without a stagger violates nothing** (0 of 60 in my own harness), so the design's
own probe was measuring something else, and the report found that by building the control rather than
by reading it. The exit-4 argument is not a preference but a consequence — `_STOP_REASON_TO_STATUS`
and phase 10's fold have **no branch on `resumed`**, so the resume path and H7d Part B's mid-plan path
are the same two lines. The takeover's siting is argued in the code, measured in the window it
creates, and the residual is written down rather than argued away. Arm R was honoured by **not
colliding with it** — the `identity.json` example elides its digests and returns `{}`, which is what
the worked example's repeat-scope step actually returns. And two mutations were reported as blind with
their derivations rather than banked as silence.

**Close the four Majors and this merges.** None requires code that changes behaviour: three are
deletions or widenings of prose, and one is a filing.

---

# Fix round, 2026-08-24 — every finding closed, and one of them was hiding a coverage loss

Run against this review and [`task-b4-review.md`](task-b4-review.md) at `bd2b4de`. Commits
`b19f1e1` (Majors 1–2, Minors 1, 2, 4, 5), `4efa280` (Major 3 and the filings), the commit carrying this section
(Major 4, Minor 3, Minor 6 and this section).

**Gates:** `uv run ruff check .` all checks passed; `ruff format .` 93 files unchanged; `mypy` no
issues in 52 source files; **`uv run pytest` → 3132 passed, 1 skipped, 2 xfailed** — **identical to
this review's own baseline**, zero tests added or removed, which is the whole no-regression claim
stated as a number.

**Why no behavioural re-verification was run, and why that is the stronger answer.** The entire
`src/` diff of this round is *two docstring deletions, one comment, and one message string* —
`git diff main...HEAD` over `src/` for this round shows no executable line changed at all, so the
crash-and-resume round trip, the 60×5 lock race and the exit-4 apparatus stop are reached by
byte-identical code. The one production string is `RunLock`'s `E-RUN-LOCKED` message, and **no test
asserts its wording**: `grep -rn 'E-RUN-LOCKED' tests/` → 11 hits, every one on the identifier;
`grep -rn 'assumed dead\|is held' tests/` → three hits, all unrelated prose (`test_run_identity.py`'s
barrier comment, `test_stats.py`, `test_coercion.py`). Arm G asserts *exactly one `E-RUN-LOCKED`*, the
code and not the sentence.

## The four Majors

| # | Status | What closed it |
|---|---|---|
| 1 | **CLOSED** | The row names **four** faults, re-derived by `grep -rn 'code="E-RESUME-LEDGER-UNREADABLE"' src/publishable/` (three in `lineage.py`, one in `cli.py`'s `_reconstitute`), and the *"reads clean here"* clause is gone. The five-key required set is now scoped to the ledger reader with the reconstitution check named beside it, which is the review's own second option |
| 2 | **CLOSED** | The paragraph is **deleted**, not rewritten — the docstring's opening two paragraphs already state Decision 13 correctly, so nothing was lost and nothing was invented. The self-referential closing sentence went with it; `_resume_prepared`'s own docstring carries that fact where it is true |
| 3 | **CLOSED**, and it was hiding a real coverage loss | The helper reads the code off stderr. **Twenty** arms were blind, not 21 — see below. Filed in `spec-defects.md` with the reproduction, and its second half (the credential test) filed OPEN rather than repaired |
| 4 | **CLOSED** | A dated correction appended to § Executability, one to design Decision 17, one to plan correction 23. **Fourteen `E-RESUME-*` codes, fifteen codes minted, fifteen rows** — each figure carrying its noun |

### Major 1 — what was checked besides the row

The table's **scope sentence** admits these rows unchanged (*"these are the codes a **command**
reports, and a code raised at load can be in both"*), so no placement moves. `lineage.py`'s docstring
and `tests/test_lineage.py:957`'s *"Three faults, one code"* are **correct and deliberately untouched**
— both are scoped to `read_execution_ledger`, which really does have three. Removed-string sweep for
*"Three faults, one code"* and *"reads clean here"* over the four documents, `CLAUDE.md`, the
feasibility analysis, `src/`, `tests/`, `docs/superpowers/` and `.superpowers/`, **every hit
attributed**: the only live-prose hit is that test docstring; every other is a development-record file
quoting the defect, which is not retro-edited. The fourth emit site was **already pinned**
(`tests/test_cli.py`'s stale-build arm asserts the code and the message) — the row was the only thing
wrong, which is why nothing behavioural moved.

### Major 3 — the count is 20, and four of them were testing the wrong gate

**The review's 21 is a miscount of the same number**, and it is the fault three of the four Majors
are about: `grep -c "_assert_refused(result" tests/test_freeze.py` returns 21 because the definition
line's first parameter is `result`. There are **20 call sites in 20 distinct test functions**
(enumerated by walking the file's `def` boundaries, each one carrying `capsys` already).

The discriminating pair, both arms scoped to `tests/test_freeze.py`, `freeze._refuse` mutated to emit
a constant `"E-BOGUS-MUTATION"` — the single funnel, confirmed by reading all 20 call sites (lines
137–448, every refusal in `_precheck` returns through it; `command_freeze`'s two other `c.error` sites
are on a path `_assert_refused` never sees):

| Helper | Result |
|---|---|
| shipped, code-blind | **5 failed, 37 passed** — not one of the twenty arms |
| reading stderr | **25 failed, 17 passed** — all twenty, plus the same five |

FULL unfiltered run under that mutation with the fix in place: **25 failed, 3107 passed, 1 skipped,
2 xfailed**. Both mutations reverted by copying the saved file back and verified **by re-running**
(42 passed in that file; 3132 overall at the end).

**And this is the finding rather than a fixture repair.** Four of the twenty had been passing a code
the code never printed — since **this branch** minted `E-FREEZE-CONFIG-EDITED`. Gate (c2) sits before
template resolution (e) and the plan cross-check (h), and `covered_config` covers everything but
`metadata` and the two host paths, so **any** edit to the run directory's `config.yaml` copy moves
`parameters_hash` and stops at (c2): `test_gate_e_unknown_template_reuses_the_shipped_code`,
`test_gate_e_installed_only_template_reuses_the_shipped_code` and both
`test_gate_h_*_is_plan_mismatch` were exercising (c2), so `E-TEMPLATE-UNKNOWN`,
`E-TEMPLATE-INSTALLED-UNSUPPORTED` and `E-FREEZE-PLAN-MISMATCH` had **no coverage at all** and nothing
could say so. `_edit_config_yaml` now re-records `identity.json`'s `parameters_hash` beside the edit —
the state each of those fixtures means, a copy the run really started under with the fault somewhere
later — and (c2) keeps its own coverage in the two tests that edit `config.yaml` directly and leave
`identity.json` alone, one of which already asserts `E-FREEZE-PLAN-MISMATCH` is **not** what fires.
**No test was added**: the ordering assertion the four were accidentally making already exists there.

Two tests that read stderr themselves now take the helper's return value rather than a second, drained
`readouterr` — the one shape the fix broke, and it broke loudly.

### Major 4 — both counts derived, no fifth number

- `grep -rho 'E-RESUME-[A-Z-]*' src/publishable/*.py | sort -u | wc -l` → **14**. Eleven are a literal
  `code="E-RESUME-…"`; three (`-CODE-MOVED`, `-PARAMS-MOVED`, `-LOCKFILE-MOVED`) are raised through a
  loop variable over a three-tuple list — **the under-count a keyword-form grep produces, and the
  likeliest origin of "thirteen"**.
- `E-FREEZE-CONFIG-EDITED` is new on this branch (`git show main:src/publishable/freeze.py` → zero
  occurrences): **15 codes minted**.
- **15 rows**, 14 `E-RESUME-*` plus that one, in § Errors `validate` reports.

Appended in three places, never retro-edited: the feasibility analysis' § Executability (dated
2026-08-24, against `bd2b4de`), design Decision 17 (**its own table is the evidence** — it listed
fourteen all along), and the plan as correction 23. **The entry's other count sentence is right and is
named as such** so the correction does not create the next reader's contradiction: *"refuses fourteen
named ways"* is the `E-RESUME-*` family alone, and `resume` is the command it describes. **No row of
the four-row table moves and no fifth number is minted.**

## The six Minors

| # | Status | What closed it |
|---|---|---|
| 1 | **CLOSED** | `RunLock`'s message carries § One execution at a time's own qualification. No test asserts the wording (greps above) |
| 2 | **CLOSED** | Both stale clauses deleted. The sweep `grep -rn "not dispatched\|does not exist yet\|owns building it" src/ tests/` now returns **five** hits, every one attributed: `units.py`, `validate.py` (genuine unbuilt surfaces) and **`report.py` + `test_report.py` ×2, which are FALSE at HEAD** — H8c's, filed OPEN, deliberately not fixed on this branch |
| 3 | **CLOSED** | Appended to the design: **arm C's editor is plan task 5**, not task 6 — the plan's § Task 5 holds the sole-editor sentence and `git log -S '"recorded_columns",'` returns `d4e0afd` *"H9b task 5"*. Arm E → task 15 **is** correct (plan § Task 15), which is how the half-right claim survived |
| 4 | **CLOSED** | The *"Safe only because of this function's branch ORDER"* claim is **deleted** and the gap **filed** with an owner that is a fact. The replacement states the measurement (M6 blind on a full run) and points at the filing rather than re-deriving `NOT_BUILT_COMMANDS`' contents, which would go stale the moment someone adds a two-token unbuilt name — which is what the filing is for |
| 5 | **CLOSED by widening** | The row now names all **nine** shapes; the per-axis *"records axis X as T, not a mapping"* arm and the holdout-partition arm were the two it did not |
| 6 | **CLOSED** | One appended block on the batch-4 report covering three items: item (a) was **not** closed (Major 1), the takeover has **two** end-to-end pins (arm A as well as arm G — a bare `return` in `take_over_dead_lock` fails 21 tests including arm A), and *"ten shipped gate tests"* is **20**, with the review's 21 named as the same miscount. The arm A/G omission is also corrected in `_h9b_resume`'s own docstring, where the same sentence lived — *sweep for the claim, not for the file it was first noticed in* |

## Both `*.md` passes, re-run

**Mechanical**, my own script over `README.md`, `docs/design-principles.md`,
`docs/experimental-designs.md`, `docs/reference.md`, `docs/feasibility-llm-growth-studies.md` and
`CLAUDE.md`, fenced blocks skipped, inline code and escaped `\|` masked before any table arithmetic:
**0 problems.** Every check proven able to fail by appending to **every** file in the list:

| Probe | Problems reported |
|---|---|
| `## The documents` (duplicate anchor) | 1 (only `CLAUDE.md` holds that heading — it fired where it could) |
| a line ending in a space | 6 |
| a tab-indented line | 6 |
| `a 3 x 5 grid` | 6 |
| `## An en–dash heading` | 6 |
| `[nope](docs/no-such-file-xyz.md)` | 6 |
| `[nope](#no-such-anchor-xyz)` | 6 |
| a 3-cell row under a 2-cell header | 6 |
| `\|  \|  \|` under a 2-cell header | 6 |

Two of those probes reported **0** on the first attempt and both were the *checker's* fault, not the
documents': a bare row appended at EOF became its own header, and `|  |  |` matched the
separator-row pattern. Fixed, re-probed, and recorded here because *a mutation whose two branches
cannot differ is a claim too* — a green mechanical pass over a checker with two dead arms is worth
nothing.

**Cross-document.** `README.md`, `docs/design-principles.md` and `docs/experimental-designs.md` are
untouched by this round. The `reference.md` diff is **exactly two table rows**, both prose-only: no
config field, no code, no enum comment, no `run.yaml` key, nothing declared-versus-derived. The worked
example's literals were re-counted after the edit and are unchanged — `[0.488, 0.661]`,
`[0.517, 0.683]`, `[0.347, 0.477]`, `[−0.007, 0.059]`, `[−0.213, −0.125]`, `8e21`, `1a2b`, `3d8a`,
`6b1f`, `2f5c8d0` all present at their previous counts. § The one config file does not move.

## The one thing left open, said plainly

**Nothing from this review is open.** Three things are **filed** rather than fixed, each with an owner
that is a fact and a reason, and none of them is a finding of this review:

1. `test_gate_e_a_load_fault_..._carries_credentials` promises a redaction no assertion makes — H8b's,
   and pinning it needs a mutation in a closed slice's production surface on the commit before a merge.
2. `_dispatch`'s branch order is unpinned (Minor 4's residue, which is what the Minor asked for).
3. Two H8c comments denying that a shipped bundle render exists.

**Not a count of zero disagreements**: every claim this round repeats was grepped, and two of the
briefs' own figures did not survive it — the review's *"21 call sites"* is 20, and its *"fourteen
codes and fifteen rows"* needed the nouns attached before either figure meant anything. Both are named
above with the derivation rather than quietly corrected.

# H8c — whole-branch review — `report`, `study`, `BaseReport`

Reviewed at `c10aa44` (branch `h8c-report-study`, 17 tasks, nine batches), against
`docs/superpowers/specs/2026-08-21-report-study-design.md` (21 decisions),
`docs/superpowers/plans/2026-08-21-report-study.md` § Corrections against the code (17),
`.superpowers/sdd/2026-08-21-report-study/progress.md`, the nine batch reports and reviews, and
`CLAUDE.md`. Worktree held alone; tree left clean.

## Verdict

**MERGE.**

No Critical and no Major. **Ten Minors**, none of which changes what any command does for a
correctly-formed input; four are document/record hygiene, and the two most interesting (9 and 10) are
pre-existing platform/sibling issues this branch's own work made visible. The slice's load-bearing
negatives — no override discovery on a bundle, no hash recomputed, nothing written outside a bundle, no
run altered, **and no § Errors row narrower than its code** — hold under direct probing, not under
reading.

The recurring whole-branch Major of the two preceding sub-slices (*a § Errors row narrower than its
code*) I looked for hardest and **did not find**: I enumerated every raise reachable from `ReportIO`'s
two read members, including through the shared helpers, and every row covers every site (§ 6 below).

## Gates, all re-run by me in the foreground with caches cleared

| Gate | Result |
|---|---|
| `uv run ruff check .` | clean |
| `uv run ruff format --check .` | **93 files** already formatted |
| `uv run mypy` | **52 source files**, no issues |
| `uv run pytest` | **2833 passed, 1 skipped, 2 xfailed** (186s) |

All four match the brief's literals exactly. Re-run a second time after deleting my probe file:
identical.

---

## What I verified by running

### 1. `report` and `study` end to end through `main([...])`

Built my own fixtures (a scaffolded project through `run_a_project`, plus a project-local
`required_env` template for the credential arms) and drove every form through `main`:

| Invocation | Result |
|---|---|
| `report <run.yaml>`, `completed` | exit `0`, four sections in order: Conditions, Deltas, Hypothesis verdicts, Attrition |
| `report <run.yaml>`, `status: failed` | exit **`0`**, `\| status \| failed \|` in the Attrition table |
| `report <run.yaml>`, `status: partial` | exit **`0`** (Decision 6) |
| `report <run.yaml>`, `draft: true` | exit `1`, `E-REPORT-DRAFT`, **nothing rendered** (Decision 7) |
| `report <run directory>` | exit `1`, `E-REPORT-FORM` |
| `report <run_dir>/sweep.yaml` | exit `1`, `E-REPORT-FORM` |
| `report <run.yaml> --format html` | exit **`2`**, "`report` takes exactly one path and no flags" |
| `report <study.yaml>`, two members, one a draft | exit `0`; per-member header, four sections each, one combined `## Hypotheses`; the draft member carries the `**draft** — …` line, and the word `draft` occurs **exactly once** in the whole render (so the assertion is not satisfied by neighbouring output — the batch-6 trap) |
| `report <missing>/study.yaml` | exit `1`, `E-STUDY-UNREADABLE` |
| `study new` inside a git repo | exit `1`, `E-STUDY-IN-REPO`, **directory not created** |
| `study new` outside, then again | `{title, authors: [], runs: {}}`; second call exit `1`, `E-STUDY-EXISTS`, **title unchanged** |
| `study add --as main` | exit `0`; four fields carry `<redacted by study add>`; `code_hash`, `parameters_hash` and `input_manifest_hash` all survive |
| `study add --as main` twice | exit `1`, `E-STUDY-NAME-EXISTS`, **bundle directory listing byte-for-byte unchanged** |
| `generate report <exp>` (no flag) | exit `0`, `format = "markdown"` |
| `generate report <exp>` again | exit `1`, `E-REPORT-EXISTS` |
| `generate report <exp> --format html` | exit `0`, `format = "html"`; the subsequent `report` emits `<!doctype html>…`, **no `http` anywhere in the output** (self-contained, Decision 16) |
| a code-hash disagreement inside one commit | exit `0` with `W-STUDY-CODE-HASH-MISMATCH` — a notice, never a refusal |

Decision 2's and Decision 3's refusals, none of which any earlier probe of mine had run:

| Override | Result |
|---|---|
| declares no `format` | exit `1`, `E-REPORT-FORMAT`, **nothing rendered** |
| `format = 'pdf'` | exit `1`, `E-REPORT-FORMAT` |
| `self.section('X', body=42)` | exit `1`, `E-REPORT-BODY` |
| **two** `BaseReport` subclasses | exit `1`, `E-REPORT-OVERRIDE-CLASS` (refused, not resolved by definition order) |
| raises on import | exit `1`, `E-REPORT-OVERRIDE-IMPORT` |
| no `report.py` at all | exit **`0`**, four standard sections — the ordinary case, not a refusal |

`W-STUDY-COMMIT-MISMATCH`, which I had only read: two runs from two repos, `alpha` added first, then
`beta` — exit `0` and the notice fires, naming both commits and the run; and the **control**, re-adding
the same differing run `--as main`, does **not** fire it, because that add writes `code.commit` instead
of comparing against it.

`render_bundle`'s docstring claims the widened exception tuple landed *"at both call sites"* — a safety
claim in a comment, so I made it happen. `execution: "x"` (a `str`, the shape that used to reach `.get`
and raise a bare `AttributeError`) on the **run form** and on a **bundle member**: both give
`E-REPORT-RECORD-INCOMPLETE` at exit `1`, no traceback. The comment is true.

The `min_reported_n` prompt, exercised over a record with a real `basis: units` metric and a floor
of 1000 (a floor the default scaffold cannot trip, because its `aggregate` returns `{}` — my first
attempt was underpowered and I re-ran it with `aggregate_returns`):

- **no TTY** → exit `1`, `E-STUDY-CONFIRM-REQUIRED`, offending metrics printed first, **bundle
  listing unchanged and `runs` still `{}`**;
- **quit** → exit `0`, `Quit — nothing was added to the bundle.`, **listing unchanged, `runs` still `{}`**;
- **proceed** → exit `0`, the record written and `runs.main` added.

**Nothing reaches disk on any refusal path I exercised.** For a successful `report` of a run whose
override imports, I snapshotted every file under `output_dir` as `(relpath, size, mtime_ns)` before
and after: **unchanged**. The only thing that appears in the repo is `src/<pkg>/__pycache__`, which
the scaffolded `.gitignore` already lists (`scaffold.py:13`), so it cannot dirty `src/**` for a
later `run`.

### 2. The credential story

Same project, same declared credential (`required_env` on a project-local template), same sentinel
value, five surfaces:

| Surface | Result |
|---|---|
| override's `sections()` **raise** | `<redacted:PUBLISHABLE_WB_CRED>` — **redacted** (this is the positive control: it proves `command_report`'s collector is genuinely populated, not empty by luck) |
| project-local **template raising at import** | redacted (batch 5's Critical stays closed — re-verified through the console path) |
| credential rendered **into a `Section` body** | printed verbatim, exit `0`, on stdout — and **`docs/reference.md` § Secrets & credentials says so in its own words**: *"an override that renders a declared credential into a body prints it verbatim, at exit `0`, on stdout"*. Documented, not graded |
| `generate report --format <credential>` | no leak on any stream |
| a **corrupt `run.yaml`** whose offending YAML line carries the value | **leaks** — see Minor 1 |

### 3. The guard pin's whole life

Verified with `git log -L` per arm, not per file:

| Arm | Commits touching its region | Expected |
|---|---|---|
| A (`test_cli.py`, both tests) | `52612ed` only | untouched ✓ |
| B (`test_cli.py`, `__all__`) | `52612ed`, **`6b0bd04` (task 1)** | exactly the one authorized edit ✓ |
| C (`test_artifacts.py`) | `52612ed` only ✓ (`56e6dc1`'s single deletion in that file is one `import` line, checked) |
| D (`test_diff.py`, three tests) | **`52612ed` only** — `c794029` (task 16) touched the file with **129 insertions and 0 deletions**, none inside arm D's region ✓ |

Arm B's post-edit state matches what task 17 stated in advance: `"BaseReport"` inserted in sorted
position and the `not in` negative deleted, nothing else reordered.

**Arm D provably fires.** I mutated `README.md`'s `code_hash … sha256:8e21…` to `sha256:9f99…` and
`design-principles.md`'s `parameters.analysis.min_samples  30 → 50` to `30 → 51`; both arm-D tests
**failed**. Reverted by editing the values back (never `git checkout --`), diffed against copies
taken before the mutation — **byte-identical** — and re-ran: 3 passed. So the claim that no hash
prefix, run ID, delta line, row label, row order or separator moved is verified, not trusted.

`README.md` and `docs/design-principles.md` between them carry **exactly four added lines** on this
whole branch — the two header lines each. `docs/experimental-designs.md` is untouched. The shared
worked example is intact.

### 4. § Executability's figures, re-measured

I transplanted **E1**'s and **E2**'s `data`/`statistics` blocks (under the analysis's own table-roster
substitution) onto a scaffolded config over a 240-row synthetic roster and ran `validate_config`:

| Config | Codes reported |
|---|---|
| E1 | `W-DATA-CLUSTER-UNDECLARED` — **zero errors** |
| E2 | `W-DATA-CLUSTER-UNDECLARED` — **zero errors** |
| E1 with `holdout.frac → 0` (**can-fail control**) | the same **plus `E-DATA-HOLDOUT-FRAC`** |

No `E-REPORT-*` and no `E-STUDY-*` code appears on either. The entry's table is **8 of 8 · 0 · 7 · 1**
with no fifth number, and I confirmed by `md5` over the extracted six lines that the H8a, H8b and
H8c tables are **byte-identical** — so "character for character" is now true (b9 Minor 5 closed).
The pin `ae71d2a` is the last commit touching `src/`, dated 2026-08-21, matching the entry's date;
everything after it is docs and tests only (verified by `git diff --stat ae71d2a..HEAD -- src/ tests/`).

### 5. The documents

- **§ Package layout matches `src/publishable/` in both directions.** Set-diff over the tree block's
  `*.py` entries against `ls src/publishable/*.py`: nothing in `src/` missing from the tree, and the
  only two tree entries absent from `src/` are `docs.py` and `reproduce.py` — precisely the two rows
  still carrying `— not yet built`. `generators/` and `templates/` contents also match.
- **Mechanical pass, written fresh** (links, `#anchor` resolution, duplicate anchors, table column
  counts, empty rows, trailing whitespace, tabs, invisible unicode; fences skipped): **clean** over the
  four documents. Three apparent table-width hits are escaped `\|` inside cells — false positives of my
  splitter, checked by reading each line. **Proved the sweep can fail**: appended a bogus heading, a
  broken `#anchor`, a broken relative link, a 3-cell row under a 2-cell header and a trailing-space line
  to `reference.md` — all five were reported — then restored the file and confirmed byte-identity
  against a pre-mutation copy.
- **The three removed spans are gone**, greppd over the four documents plus `CLAUDE.md` and the
  feasibility analysis: "leaves open for whichever slice builds", "not a checked fact", and
  "read-only accessor a `summary` step gets". Filtered the *file list*, never the output.
- § The importable surface carries `BaseReport | subclass | built` and the `Core's` cell names
  `self.section` and `__init__` (correction 15); § Package layout's `artifacts.py` gloss now
  enumerates `ReportIO` (correction 15's second half).

### 6. Every `E-`/`W-` code's row against every emit site

Enumerated by **reading** `report.py`, `study.py`, `generators/report.py` and `lineage.py`, then
confirmed by grep. Nineteen new codes (the design's Decision 15 names twelve; correction 17 adds two;
five more — `E-REPORT-BODY`, `-OVERRIDE-ENTRYPOINT`, `-OVERRIDE-RAISED`, `-OVERRIDE-REPO`,
`-RECORD-INCOMPLETE` — were minted in fix rounds and are legitimate under *the code outranks both*).
Every one has a § Errors row, and **every row's "fires when" text covers every site**:

- `E-REPORT-OVERRIDE-REPO` — 3 sites (missing / empty / not a directory); row names all three.
- `E-REPORT-OVERRIDE-ENTRYPOINT` — 2 sites; row names both.
- `E-STUDY-UNREADABLE` — 12 sites across `study.py` (4) and `report.py` (8, of which 3 are
  `_resolve_bundle_member`'s); the row enumerates the bundle-document faults, the per-entry fault, the
  three `file` faults, and names both callers.
- `E-REPORT-RECORD-INCOMPLETE` — 2 sites (run form and bundle member); the row's last sentence names
  the bundle member explicitly.
- `E-UPSTREAM-RECORD-*` — the § Errors core raises row now names **four** callers and the message no
  longer says "this is not a run directory" (correction 1 landed).
- `E-TEMPLATE-LOAD`/`-COLLISION` — rows are stated as dual-surface over *"every command resolving a
  template"*, so `report`'s new site needs no enumeration.
- b9's own Majors 2 and 3 (`E-STEP-READ-CONDITION-UNKNOWN`/`-REPEAT-REQUIRED` naming one of two
  callers; `E-EXPERIMENT-UNKNOWN` asserting "one raise") are both **closed at HEAD** — re-read.

**And the audit b9 started, finished.** b9 caught two rows going stale because `artifacts.py` gained a
second caller, and widened a third (`E-ARTIFACT-NAME`) — but nobody enumerated the whole set, and *a row
narrower than its code* was the whole-branch Major on both preceding sub-slices. So I enumerated every
`raise` reachable from `ReportIO.read_condition` and `ReportIO.read_input`, **including through the
shared helpers**, by reading `artifacts.py`:

| Reachable from `ReportIO` | Via | Row's disposition |
|---|---|---|
| `E-STEP-READ-REPEAT-REQUIRED`, `E-STEP-READ-CONDITION-UNKNOWN` | `_resolve_condition_step_dir` | **widened** — the row names the shared function and both callers ✓ |
| `E-ARTIFACT-NAME` | `StepIO._contained` | **widened** — the row names *"a report override's own `io.read_condition`"* and says *"Four emit sites for the escape alone"*; I counted `code="E-ARTIFACT-NAME"` in `artifacts.py`: **exactly four** (a write in `_resolve`, `StepIO.read_condition`, `read_upstream`, `ReportIO.read_condition`) ✓ |
| `E-ARTIFACT-UNREADABLE` | `StepIO._read` | **not narrower.** Its fires-when clause is surface-agnostic — *"Reading a name whose suffix has a registered writer and no reader"* — and the `io.read_upstream` mention sits inside the explanation of the *pair* mechanism, not in a scoping of when it fires. Also checked against `main`: the row text is byte-identical there, and `_read` already had five callers before this branch, so nothing about it went stale here |
| `E-STEP-READ-DIRECTION`, `E-STEP-READ-AMBIGUOUS` | — | **unreachable**: both are raised in `read_upstream`, which `ReportIO` does not have |

**No row is narrower than its code.** That is the one shape I was most looking for, and it is not here.

**The symmetry question batch 2 routed to "a later reviewer", answered.** `ReportIO` calls
`StepIO._read` and `StepIO._contained` by class, while the module extracted
`_resolve_condition_step_dir` and `_nest_repeat_segment` to module level for the same sharing. **No
change needed**: the drift argument the extraction was for is satisfied by there being exactly one
definition either way, and moving two stateless `@staticmethod`s would be churn against a shipped
module. Recorded so it does not read as missed — and so a later reader does not "fix" one half of the
asymmetry and leave the other.

### 7. `CLAUDE.md` § Invariants

- **Operation commands take paths and nothing else** — `report --format html` exits `2` at the
  arity guard, verified by running. `study new|add` are creation commands and take `--title`/`--as`.
- **One import root** — `BaseReport` is in `publishable.__all__` in sorted position, and in
  § The importable surface's enumerated list.
- **Three hashes, apparatus not a fourth** — `grep` at HEAD (re-run after the three fix rounds that
  post-date batch 6's claim): `report.py` imports neither `hashes` nor `apparatus`; the only
  `apparatus_hash` occurrences are the local variable `apparatus_hashes` holding **recorded** strings.
  `report` computes neither hash.
- **Core never inspects the body of user Python** — no `ast`, no `inspect`, no `getsource` in
  `report.py`, `study.py` or `generators/report.py`.
- **Greenfield only** — no `adopt`; `generate report`, `study new` and `study add` all refuse rather
  than overwrite, each verified by running.

### 8. The filings

Four filings on this branch, each stating the check its owner must make and each giving a reason for
`unassigned` rather than leaving the field blank. Both filings this branch closed are **struck** with a
`CLOSED by H8c task 16` note, and **no OPEN filing names H8c or H8 as owner** (grepped). None is stale
on arrival: I re-checked the `basis: "repeats"` filing's amendment against `study.py`'s corrected
`results.summary` walk and the `nondeterministic` filing's absence claim against a real record.

---

## Findings

Nothing Critical. Nothing Major.

### Minor 1 — a credential inside a corrupt run record is echoed unredacted by `report` and `study add`
**`src/publishable/lineage.py:71`** (`f"{path} is not valid YAML: {exc}"`), reported through
**`src/publishable/report.py:1376`** and **`src/publishable/cli.py`**'s `study add` path.

**Verified by running**, in the credentialed project, with the override-raise arm as a positive
control in the same test: a `run.yaml` rewritten to `run_id: x\nbad: [unclosed <SENTINEL>` makes
PyYAML's `MarkedYAMLError` embed the offending source line, and `command_report` prints it through a
`Collector()` constructed **with no `credentials`** — the sentinel reaches stderr verbatim at exit `1`,
while the override-raise arm over the identical project prints `<redacted:…>`. `study add` over the
same file leaks identically.

`docs/reference.md` § Secrets & credentials promises redaction of *"a diagnostic printed to stdout or
stderr"*, and this is one. It is **Minor, not Major**, for three measured reasons: (a) the same probe
against **`diff`** — untouched by this branch, shipped on `main` — leaks identically, so the class is
pre-existing rather than introduced here; (b) `command_report`'s own docstring is honest, scoping its
redaction commitment to *user-code* faults; and (c) the ordering is structurally forced — the credential
set is derived from the record's embedded config, so it cannot exist before the record parses.

**What I'd ask for:** name `report` and `study add` in the existing `spec-defects.md` entry
*"`main`'s last-resort stderr handler prints an exception un-redacted, by construction"* (`:6325`), or
file a sibling — that entry today covers `main`'s handler, and this leak is from a command's own
collector, so a reader following it finds nothing about this path.

### Minor 2 — `report_form`'s docstring names an exit path the code does not produce
**`src/publishable/report.py:726-729`**: *"A missing operand stays whatever the read that follows makes
of it — `E-IO-FAILED` at exit `1` through `main`'s `OSError` handler, exactly as `diff`'s config operand
does."*

**Verified by running**: `report <nonexistent>/run.yaml` → `E-UPSTREAM-RECORD-MISSING`;
`report <nonexistent>/study.yaml` → `E-STUDY-UNREADABLE`. `E-IO-FAILED` is produced on neither form,
because both readers check existence themselves before any `open`. This is the *comment claiming a
guarantee the code does not provide* habit; the remedy is deletion of the `E-IO-FAILED` clause (the
sentence's first half is true and self-maintaining), not a rewrite.

### Minor 3 — `E-STUDY-IN-REPO`'s § Errors row names the wrong object for the walk-up
**`docs/reference.md:581`**: *"Implemented as the walk-up `provenance.find_repo_root` performed over
`input_dir`/`output_dir` **succeeding**."*

**Verified by reading** `src/publishable/study.py:42-64`: the walk-up is performed over the **bundle
path**, not over `input_dir`/`output_dir`. The design's own wording is *"the same walk-up
`input_dir`/`output_dir` already use"* — the row lost the comparison and turned it into a false claim
about which path is walked, in a normative row. One-word fix.

### Minor 4 — `CLAUDE.md`'s proxy tally and this branch's own ledger disagree on what the sixth proxy is
**`CLAUDE.md` § Answering a question with a proxy** numbers: prefix (1), class marker (2), state read
at the wrong moment (3), one-spelling grep (4), *"Removing by position is a **fifth**"*, *"Copying a
recipe's calls without its containment is a **sixth**"*.

**`.superpowers/sdd/2026-08-21-report-study/progress.md`** (batch 4) states: *"The tally of that move on
this project is now: a module-name prefix, a class marker, state read at the wrong moment, a one-spelling
grep, `pop(0)`, and **a reserved name**. Six."*

So the **reserved-name** instance — batch 4's Major, *"exclude by structure, not by name"*, the one whose
fix produced `_is_metric_entry`/`_is_strata_block` — has **no numbered entry in `CLAUDE.md`'s proxy
list at all**, and the ordinal it holds in the ledger is used there for a different instance. It survives
only as a clause inside the *"sibling that already got it right"* bullet. Either the tally is seven and
one entry is missing, or the two tracked records need reconciling; a section whose value is a running
count cannot have two answers. (I am not proposing a retro-edit of the ledger — `CLAUDE.md` is the live
document here.)

Also, in that same section, the three new/renumbered paragraphs read **sixth, fifth, fourth** in file
order, which makes the count harder to follow than the numbering intends.

### Minor 5 — the ledger stops at batch 7
`.superpowers/sdd/2026-08-21-report-study/progress.md` has entries through *"Batches 6 and 7"* and
**none for batch 8 (task 15, `generate report`) or batch 9 (task 16, the documents)** — the two batches
whose isolation the ledger itself argues for at length (*"B9 is the documents batch, alone and reviewed
— explicitly because H8b dispatched no review for its documents task and three of its four whole-branch
Majors lived in that commit"*).

**Nothing is lost**: I read both reviews and verified each finding closed at HEAD (b8's Major 1 escaped
`--format` through `json.dumps` and filed the family-wide generator name-guard gap; b9's four Majors and
three Minors are all closed, checked one by one above). But the record that exists to explain *why*
something is the way it is is missing its last two batches, including the batch that produced the
`E-GIT-NO-REPO` filing and the executability-pin correction.

### Minor 6 — a bundle's cross-check notices go to stdout, ahead of the artifact
**`src/publishable/report.py:1364-1369`** prints the `Collector`-rendered notices with a bare `print`,
then **`:1371`** prints the render.

**Verified by running**: with a hand-edited `code_hash` disagreement inside one commit, the first line of
stdout is `  warning W-STUDY-CODE-HASH-MISMATCH …`, followed by `## alpha`. So
`publishable report study.yaml > report.md` yields a markdown file whose first three lines are diagnostic
text. For `validate` the findings *are* the deliverable; for `report`, stdout **is** the artifact a paper
cites. No document rules the stream for `report`, and `reference.md` § `freeze` already records its own
two-stream split as *"as shipped rather than as decided"* — so this is a gap in the documents as much as
a choice in the code. Worth a sentence either way, since a reader will redirect this command.

### Minor 7 — the bundle render's heading levels are flat, so a member boundary reads like a section
**`src/publishable/report.py:1188`** (`render_bundle`) and **`:602-603`** (`_render_markdown_section`,
which emits `## ` for every section).

**Verified by running** a two-member bundle: the headings are `## alpha`, `## Conditions`, `## Deltas`,
`## Hypothesis verdicts`, `## Attrition`, `## beta`, `## Conditions`, …, `## Hypotheses` — a member's
name and its own sections are siblings at the same level, so nothing in the rendered artifact marks
where one run's block ends and the next begins. Decision 16 does not rule heading depth, and `Section`
carries no level, so this is a consequence rather than a violation — but the bundle render is the one
place where two levels genuinely exist.

### Minor 8 — `study add` does not check the in-repo rule that `study new` enforces
**`src/publishable/study.py:390`** (`study_add`) never calls `_refuse_if_in_repo`; only `study_new`
(`:80`) does.

**Verified by reading**, and consistent with the documents: Decision 9 scopes the rule to `study new`
and `E-STUDY-IN-REPO`'s row says *"`study new`'s bundle path"*, so this is **not** a spec violation and
I am not asking for a behaviour change on this branch. But § Why not in the repo's three arguments are
described as structural, and the structure has one hole: a bundle created outside a repo and later
enclosed by one (`git init` a directory above it, or a move) takes `study add` writes inside the repo
with no objection. Worth a filing so the next reader does not rediscover it as a defect.

### Minor 9 — a same-size rewrite of an override is silently not picked up, and the render is the previous one at exit `0`
**`src/publishable/report.py:882-885`** (`render_with_override`'s `sys.modules` purge).

This is the observation I first logged as unattributed; I re-ran the original sequence verbatim and then
isolated it. **Verified by running**: render an override whose section body is `MARKER_AAA`, then rewrite
the same file with `MARKER_BBB` — **byte-identical in length**, within the same second — and render again.
The second render prints **`MARKER_AAA`**, at exit `0`, with no diagnostic. A rewrite that changes the
file's *length* (`MARKER_CCCCCCCC`) is picked up correctly, which is what identifies the cause: CPython
invalidates a `.pyc` on **source mtime (one-second resolution) plus source size**, so purging
`sys.modules` — which `render_with_override` does correctly, root package **and** every `root_pkg.*` —
does not reach the bytecode cache.

**Not H8c's invention and not a Major**: `base_experiment.load_experiment` has the identical exposure for
`validate`/`run`, and neither site calls `importlib.invalidate_caches()` or sets
`sys.dont_write_bytecode` (grepped: neither name appears anywhere in `src/`). But `report` is the command
a user will iterate an override with, and this is the "wrong answer that looked like an artifact" shape
the rest of the module works hard to avoid — worth a filing rather than silence.

### Minor 10 — `pop(0)` is still live at `base_experiment.load_experiment`, one file from where this branch fixed it and named the rule
**`src/publishable/base_experiment.py:50`**: `sys.path.pop(0)`.

Batch 3's review closed exactly this in `render_with_override` (now `sys.path.remove(src_entry)`), and
`CLAUDE.md` gained *"Removing by position is a fifth [proxy]"* on this branch — **and the sibling site
whose behaviour was cited in the buggy version's own defence still does it.** That is *sweep for the
claim, not for the file the claim was first noticed in*, one slice later.

**Verified by running, as a discriminating pair in one process:**

| Site | After the command | Verdict |
|---|---|---|
| `load_experiment` (through `validate`, with the project's `experiment.py` doing `sys.path.insert(0, …)` at import — the ordinary vendoring idiom) | the **project's own `src` is left on `sys.path`** and the vendored entry was removed instead | the inversion, live |
| `render_with_override` (through `report`, same idiom in `report.py`) | the vendored entry survives and **our `src` entry is gone** | correct |

**Minor, not Major**: `base_experiment.py` is outside H8c's charter, the exposure is narrower there (only
an import runs inside that window, not a whole render), and within one CLI invocation the process exits.
It bites a long-lived process handling two projects — which is this repo's own test suite. Worth a filing
naming the site, since `CLAUDE.md` now carries the rule without the sweep having reached it.

---

## What I could not check

- **A bundle assembled on another machine.** Every fixture builds locally; device-independence is
  pinned by relative references and by the render opening no path outside the bundle, exactly as both
  the design and the plan say. I did not move a bundle between machines.
- **A genuine `draft` run.** `publishable draft` is `NOT BUILT` (H9's). Every draft arm I ran — the
  run-form refusal and the bundle-form flag — used a record with the shipped `draft` key flipped by hand,
  which is what the design rules.
- **A `basis: "repeats"` metric.** Nothing in this build writes one; I confirmed the five `"basis"` emit
  sites all write `"units"` and did not exercise that prompt branch against anything `run` produced.
- **Whether the HTML render is correct HTML to a browser.** I asserted it is self-contained (no `http`
  anywhere in the output) and that it opens `<!doctype html>`; I did not render it.
Nothing else. The one observation I originally could not attribute was chased to ground rather than
deferred — see Minor 9.

## Tree state

**Clean.** My probe file (`tests/test_zzz_wb_probe.py`) is deleted; the three documents I mutated for the
arm-D can-fail control were restored by editing the values back and verified **byte-identical** against
copies taken before the mutation; `__pycache__` and `pytest-of-*` cleared. `git status --porcelain` is
empty apart from this review file, and all four gates were re-run green after cleanup.
`.superpowers/sdd/.gitignore` is **not** clobbered.

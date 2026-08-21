# H8b — `diff` and `freeze` — whole-branch review

**Branch:** `h8b-diff-freeze` at `e3e480e`. **Base:** `main` at `64a831f`. 14 tasks, seven batches.
Reviewed 2026-08-21. Every claim below is labelled **verified by running** or **read**.

## Verdict

**DO NOT MERGE as-is. Hold on four Majors** — one behavioural (a bare traceback out of `diff`, a
command this branch marked `built`) and three documentation/record. Merge once they are closed.

**No Critical.** Every *other* behavioural property I could test holds. Gates, verified by running at HEAD
with a clean tree, `__pycache__` and `.pytest_cache` cleared first:

| Gate | Result |
|---|---|
| `uv run pytest` | **2631 passed, 1 skipped, 2 xfailed** — the expected figure exactly |
| `uv run ruff check .` | All checks passed |
| `uv run ruff format --check .` | 88 files already formatted |
| `uv run mypy` | Success, 49 source files |

Re-run after every mutation was reverted: **identical**. Tree clean; both scratch test files removed,
the `main` worktree removed and pruned. `git status --porcelain` is empty and `git diff HEAD` is empty.

---

## Findings

### Major 1 — a config operand carrying a non-JSON-serializable scalar tracebacks out of `diff`, after printing four rows

**`src/publishable/diff.py:427`** → `hashes.py:87` → `hashes.py:57`. **Verified by running through the
real console script**, not a direct call:

```
$ printf 'experiment_type: generic\nexpires: 2026-01-01\nparameters: {}\n' > d.yaml
$ uv run publishable diff d.yaml d.yaml   →  EXIT=1
stdout: A  config  d.yaml
        B  config  d.yaml
        code_hash          not comparable  …
        input_manifest     not comparable  …
        uv.lock            not comparable  …
        apparatus          not comparable  …
stderr: TypeError: Object of type date is not JSON serializable   (bare traceback)
```

Unquoted `2026-01-01` is a `datetime.date` under `yaml.safe_load` with no quoting mistake in sight.
`_read_config` checks mapping-ness and nothing else; `_parameters_hash_for` → `parameters_hash` →
`_canonical` → `json.dumps` has no guard; and `main` catches `PublishableError`/`OSError` only. The
user gets **four rows of a comparison and then a Python traceback** — worse than a clean refusal,
because the partial output reads as a rendered answer.

**Why no per-batch review could see it.** No batch owned the question *what may a config operand
contain*: batch 5 built `covered_config`/`_canonical`, batch 8 built `_read_config`/`_form`, batch 10
built `_parameters_hash_for`. Each is correct in isolation. Note the asymmetry that hides it further —
`parameter_deltas` renders a `date` perfectly well through YAML flow style, so **the delta walk
survives and only the hash dies**, which is why the one function feeding two readers does not
surface it.

**Severity, bounded honestly.** I tried to reach it from a config that validates clean and could not:
a bare date in `data.units.holdout.seed` earns `E-CONFIG-TYPE`/`E-DATA-HOLDOUT-SEED`, in
`parameters.analysis.method` earns `E-PARAM-VALUE`, and in `metadata` is excluded from
`covered_config` altogether (verified by running, with a clean-validating baseline as the control:
`BASELINE errors: []`). So it needs a config `validate` would refuse — but **`diff` validates
nothing, by design**, and § Operation commands documents it as taking *"two config or run paths"*
with no such precondition. The sibling case already has a code: a config that does not parse to a
mapping is `E-DIFF-CONFIG-UNREADABLE`, a diagnostic. This is that family's missing third shape.

**And the existing filing does not cover it.** `docs/superpowers/spec-defects.md:4176` describes the
same `TypeError` class in the sibling function — *"`design_digest` over a non-JSON-serializable
`data.units` crashes `run` with a bare traceback"*, **owner H3 Units** — and names neither
`parameters_hash`, nor the whole-config projection `covered_config` covers (a date in `limits`,
`statistics` or an unknown top-level key reaches it, not just `data.units`), nor `diff`. Task 12's
brief step 7 required *"re-read every entry whose code this slice changed"*, and `covered_config` is
extracted from exactly that family; the entry carries no amendment.

**The cheap close** is a guard where `diff` computes the hash, raising `E-DIFF-CONFIG-UNREADABLE`
(same operand, same remedy: the file is not a config this build can hash) — or, if the guard belongs
at the hash, an amendment to entry 4176 naming `parameters_hash` and `diff` so the next reader is not
told this is `run`-only and H3's.

### Major 2 — `E-APPARATUS-RAISED`'s § Errors row is narrower than its code, and `freeze` is a third emit surface

**`docs/reference.md:1092`** (§ Errors core raises).

The row reads: *"a probe is user code, **called at run start and before every execution**, never at
`validate`"*, then *"Raised in `apparatus.observe_once`, and **one of two outcomes** follows depending
on when it happens"* — enumerating a run-start raise (exit `5`, no `run.yaml`) and a mid-plan raise
(`status: partial`, exit `5`). There is now a third surface and a third outcome: `freeze`.

**Verified by running.** `main(["freeze", <mid-run dir>])` against a project-local template whose
installed probe raises → `E-APPARATUS-RAISED` on stderr, **exit 5**, no ledger line appended, no
`run.yaml` at stake at all. `src/publishable/freeze.py:507-524` catches the raise and returns
`EXIT_EXTERNAL` for exactly this code.

This is the branch's own Decision 10, which explicitly *reuses* the code and says
*"`EXIT_EXTERNAL` gains its **second** reader"* — so the row was owed an emit-site amendment.
Task 12 amended four rows (`E-TEMPLATE-UNKNOWN`, `E-UPSTREAM-RECORD-*`, `E-APPARATUS-CHANGED`,
`E-IO-FAILED`) and not this one. It is the exact shape the brief named: **a § Errors row written from
an earlier decision's wording that nobody re-read**, in the last task, for a code minted four batches
earlier.

**Checked and NOT a finding, for contrast** (read): `E-APPARATUS-RETURN`, `-FACT-CREDENTIAL`,
`-FACT-TYPE`, `-FACT-MISSING` all say *"Raised in `apparatus.check_facts`"* with no surface
enumeration, so they cover `freeze` self-maintainingly; `E-TEMPLATE-COLLISION` and `E-TEMPLATE-LOAD`
say *"every command that resolves a template meets it at load"*, likewise. `E-TEMPLATE-UNKNOWN`
enumerates *"Three surfaces"* and got the edit — and three is right (grep: `freeze.py:232`,
`validate.py:595`, `generators/experiment.py:120`).

### Major 3 — a shipped docstring asserts a filing that does not exist

**`src/publishable/apparatus.py:461-464`**, the `PHASES` docstring: *"`PHASE_DRY_RUN` is named here and
called by NOTHING at this commit … Where one should **is filed to H9** rather than answered here."*

That is not a wording nit, and the proof it is not is fifty lines down in the same file:
`replay_ledger`'s own docstring (`apparatus.py:545`) says *"nothing appends one yet (**§ Refusals
routes that gap to H9**)"* — routing to the design document, which is **accurate**. Two docstrings
about the same gap, one of which claims a filing and one of which correctly claims only a routing.
CLAUDE.md's own row: *"A ledger line saying 'filed' is not a filing."* The cheapest close is deleting
four words there, per *prefer deleting a claim to rewriting it*.

Corroborating it, the same claim appears in two more places:
- `docs/superpowers/specs/2026-08-20-diff-freeze-design.md` § Refusals: *"**H9**, filed."* — where
  every neighbouring row's *"filed"* does have a `spec-defects.md` entry (H4's `report_by` gap,
  H7d Part B's truncation), so the word means the same thing there.
- `docs/superpowers/plans/2026-08-20-diff-freeze.md` § What could not be measured: *"the contradiction
  is **filed to H9** by task 12"* — a promise task 12's brief step 7 never carried, so no step
  discharged it.

**Verified by grep.** `docs/superpowers/spec-defects.md` has **no** entry for it — no hit for
`PHASE_DRY_RUN`, and the only `dry_run`/`dry-run` hits are unrelated (lines 2296, 3896, 4564, 6130,
6136). Task 12's brief step 7 names two filings to make and this is not one of them; the promise lived
only in the plan's § What could not be measured, which no step discharged. `git diff main...HEAD --
docs/superpowers/spec-defects.md` shows **additions only** (one deletion, and it is a `---` rule), so
nothing was struck — the entry was never written.

**Verified by grep**: `PHASE_DRY_RUN` ships defined at `apparatus.py:446`, is a member of `PHASES`, and
is passed by no call site in `src/`. That is the `EXIT_EXTERNAL`/`field_convention` shape CLAUDE.md's
unbuilt-reader row tracks, now with **no owner recorded anywhere** — and nobody will look for it,
because three documents say it is filed.

### Major 4 — `W-APPARATUS-UNANSWERED`'s § Warnings row describes a surface `freeze` is not, and `freeze` emits it

**`docs/reference.md:377`** (§ Warnings core reports). The row reads *"printed to stdout through a
`Collector` **at run end**, read off the accumulated per-(condition, fact) counts rather than emitted
per call: **under every execution probed**, a single flaky fact would otherwise print the same line
once per probe that missed it."* Every clause is about `run`.

**Verified by running.** A template declaring `apparatus_facts: [calibration_id]` whose probe returns
`{"calibration_id": None}`, frozen through `main(["freeze", d])`: exit `0` and
`W-APPARATUS-UNANSWERED` printed — at freeze end, over that invocation's two probe calls, not at run
end. Emit site `src/publishable/freeze.py:543-546` (`observer.warn_unanswered`).

Decision 10's own verdict table lists this warning as one of `freeze`'s five outcomes, so the row was
owed the amendment for the same reason `E-APPARATUS-CHANGED`'s was — and `E-APPARATUS-CHANGED`'s got
one (*"**A second surface**: `freeze` meets the identical raise…"*, reference.md:1097). Same class as
Major 2, one table over.

---

### Minor 1 — a stale code count in shipped code, wrong when it was written

`src/publishable/freeze.py:478-484`: *"a dispatch fault here … is neither one of the **seven**
`E-FREEZE-*` codes nor a member of `apparatus.APPARATUS_CODES` … rather than inventing an **eighth**
code."*

**Verified by grep over `src/`**: **eight** `E-FREEZE-*` codes ship — `RUN-ENDED`, `NO-CONFIG`,
`NO-APPARATUS`, `LEDGER-MISSING`, `LEDGER-UNREADABLE`, `PROBE-MISMATCH`, `PLAN-MISSING`,
`PLAN-MISMATCH` — plus one `E-DIFF-*` and one `W-FREEZE-*`. `git log -S'E-FREEZE-LEDGER-UNREADABLE'`
puts that code in `freeze.py` at `60f5d61` (task 4); `git blame` dates the comment to `6258b26`
(task 6). So it was already false when written, and no per-task review caught it. The design's own
"seven … plus one warning" is *correct as of its date* and is not retro-edited, so that is not a
finding; this comment is.

### Minor 2 — one count phrase, two normative homes, and it omits the form that prints five rows

`docs/reference.md:3551` (§ Operation commands, the `diff` row) and `CLAUDE.md:213` (the H8b entry)
both read: *"five over a run-vs-run pair with a declared apparatus (four when both sides' apparatus is
`null`)"*. The "four" clause carries no scope word.

**Verified by running.** `main(["diff", <config>, <run_dir>])` and `main(["diff", <config>, <config>])`
each print **five** rows — four `not comparable` plus `parameters_hash` — because plan correction 10
ruled Decision 5 beats Decision 2's omission rule for a config side. `reference.md` self-corrects four
lines later (*"a config side cannot supply four of its five rows"*); **CLAUDE.md's copy does not**, and
CLAUDE.md is what the next session reads first.

### Minor 3 — two warnings from one command, on two streams, neither decided

**Verified by running.** `W-APPARATUS-UNANSWERED` goes to **stdout** (`freeze.py:545`);
`W-FREEZE-LOCK-MOVED` goes to **stderr** (`freeze.py:452`, and
`test_w_freeze_lock_moved_fires_when_the_captured_copy_and_the_repo_disagree` asserts
`capsys.readouterr().err`). Same command, same phase, two streams. No document states either. The
shipped tests pin each to its current stream, so the split is now **pinned without having been
decided** — which is how it will outlive anyone's memory of it. (`E-DIFF-CONFIG-UNREADABLE` and
`E-UPSTREAM-RECORD-*` likewise render to stdout from `diff.py:557` while `E-IO-FAILED` reaches stderr
through `main`; `cli.py` already has both conventions, so I am not calling that half a defect.)

### Minor 4 — a deferral whose owner line names a task that has finished

`docs/superpowers/spec-defects.md:7534`: *"**Owner: H9 (option a); H8b task 12 may instead take the
narrower option (b)**"*. Task 12 has landed and did not take option (b) — **read**: the entry carries
no amendment. Per CLAUDE.md, *"re-owner a deferral when the slice that filed it finishes, or it reads
as live work nobody holds."*

### Minor 5 — `repo_root.txt`'s content is read but its shape is not checked

`E-FREEZE-NO-CONFIG`'s § Errors row (reference.md:618) covers `repo_root.txt` *"missing or empty"*.
**Verified by running**: a `repo_root.txt` naming a **nonexistent path**, and one naming a **plain
file**, both reach exit `1` with `E-TEMPLATE-UNKNOWN` — a coded diagnostic, no traceback, but the
remedy it prints (the template name is registered by nothing) is wrong for the fault (the run
directory was hand-edited), which is the class `E-FREEZE-PLAN-MISMATCH` exists to name. Not a crash;
a misrouted remedy on a gate the branch built.

### Minor 6 — the three worked `diff` outputs show no per-side header

`README.md:270`, `docs/design-principles.md:118`, `docs/reference.md:3143`. Decision 6 makes `diff`
always print two header lines (`A  run record  <run_id>  completed`) — **verified by running** — and no
fenced output shows them or marks an elision. The design's consistency sweep deliberately scoped this
check to *"their verdict words and their `sha256:` truncation"*, so it was scoped out rather than
missed; naming it because a fenced block with no `…` reads as literal.

### Minor 7 — the slice record stops at batch 5, and batch 7 was never reviewed

`.superpowers/sdd/2026-08-20-diff-freeze/progress.md` has entries through **Batch 5** and none for
batch 6 or batch 7, so batch 6's four Majors / twelve Minors and the two controller commits after it
(`cad8940`, `e3e480e`) have no ledger record. And there is **no `task-b7-review.md`** — task 12's
commit `639d0f7`, which wrote the ten new § Errors rows, the two § Package layout rows, the
§ Executability entry and the CLAUDE.md entry, went toward merge with a report and no review. All
three Majors above are in that commit's surface. Not retro-writing the ledger — I did not watch those
batches — but the gap is the finding.

---

## What I verified by running, and found sound

### 1. `freeze` and `diff` end to end through `main([...])`

An independent harness (19 tests, my own fixtures, not the branch's), all passing:

**`freeze`, all three verdicts and what each leaves on disk.**
- **Exit 0**: two `phase: "freeze"` lines appended (one per condition), and `lock`, `sweep.yaml`,
  `executions.jsonl` **byte-identical** afterwards; no `run.yaml` created. The lock-untouched
  assertion is what would catch M10.
- **Exit 1** on a moved fact: `E-APPARATUS-CHANGED` with the condition key and **both** values, and
  the moving observation **on disk** (ledger +1) so the stop is legible from the artifacts.
- **Exit 5** on an unreachable apparatus: `E-APPARATUS-RAISED`, and **no** ledger line.
- A run **holding `run.yaml`** is refused `E-FREEZE-RUN-ENDED`, exit 1, `run.yaml` byte-identical, no
  ledger line — M11's discriminator.
- No lock taken, no status touched, in every arm.

**`diff`, all five rows, both locator forms, exit codes.**
- Two directories and two `run.yaml` paths produce **byte-identical output** (`out2 == out`), and a
  `latest` symlink directory works — Decision 5 part 2's whole point.
- `not captured` on `uv.lock` for a scaffolded pair (M1's branch is entered by the default fixture);
  `identical` with `sha256:` + 4 hex + `…`; `DIFFERS` with delta lines; **exit 0 with a `DIFFERS` row
  present** — M5's discriminator.
- Config side: `not comparable` **exactly four times**, for config-vs-run **and** config-vs-config,
  with `parameters_hash` computed either way.
- **Exit 1 only when it could not render**: missing path → `E-IO-FAILED`; a config parsing to a list →
  `E-DIFF-CONFIG-UNREADABLE`; a `schema_version: 999` record → `E-UPSTREAM-RECORD-VERSION`.
- The apparatus row's **three shapes**: `DIFFERS` with **two** condition-qualified detail lines for a
  two-condition sweep, each carrying its own old and new value (M3's discriminator, no collapsing);
  `identical  sha256:xxxx…`; and one-sided → `DIFFERS` with `B recorded no apparatus`.
- `diff` writes **nothing** into a run directory (full byte snapshot before/after).

**Both commands take paths and nothing else** (CLAUDE.md § Invariants). Exit **2** for `diff` with one
path, three paths, `--json`, or none; for `freeze` with two paths, `--force`, or none.

### 2. `covered_config`'s two readers, and digest stability against `main`

- **Digest stability, measured rather than trusted**: `parameters_hash` computed at `main` and at HEAD
  over 11 branch-covering configs — including `{}`, `{"sweep": {}}`, `{"data": {"input_dir": "/x"}}`
  (the shape the batch-5 ledger says manufactured an empty dict), and a full config — **zero
  mismatches**. Can-fail control: perturbing `limits.max_failed_fraction` moves the digest; a
  `metadata`-only edit does not. Re-measured **at HEAD**, after the batch-5 fix round restructured the
  flattener, not carried from that batch.
- **A narrowing moves both readers**: narrowing `covered_config` to `config["parameters"]` fails
  **3 tests in `test_hashes.py` and 6 in `test_diff.py`** — hash side and delta side, together.
  Reverted by editing back; revert verified by `diff` against a pre-mutation copy (**identical**) and
  by re-running both files green (68 passed). Never `git checkout --`.

### 3. Decision 9's exclusion, end to end

`freeze` run **three times** against one mid-run directory, each through `main`: the run answered
`CAL-1`; freeze #1 answered `CAL-2` → exit 1; freeze #2 answered `CAL-3` → exit 1 **against `CAL-1`**,
with `CAL-2` **absent from the diagnostic**; freeze #3 restored `CAL-1` → **exit 0** despite two
`phase: "freeze"` lines sitting in the ledger. `freeze` does not pin itself. That is M8 and M9's
property demonstrated on the shipped code, not read off the docstring.

### 4. `run`'s two new artifacts are additive

Full artifact-tree comparison, `main` in a throwaway worktree versus HEAD, same project, same
`units=8`, both inventories dumped to JSON and diffed:

- **File lists differ by exactly two entries**: `config.yaml` and `environment/repo_root.txt`.
- **Equal**: `run.yaml`'s top-level key list, its `provenance` key list, `status`, `draft`,
  `parameters_hash`, `layout`, `results` keys, `execution` (minus timestamps), `provenance.environment`
  keys, `apparatus`, `upstream`, `units_hash`, `allocation_hash`, and parsed `sweep.yaml`.
- The only other differences are `started_at`/`wall_seconds` and `input_manifest_hash` — and I
  confirmed `input_manifest_hash` is **non-deterministic across two runs at HEAD itself**, so it is
  fixture noise, not a moved hash. No verdict, status, exit code, hash or `provenance` key moved.

### 5. The credential story, with a positive control

- A probe reading a `requires_env`-declared credential and **raising with its value in the message**,
  through `main(["freeze", d])`: exit **5**, `E-APPARATUS-RAISED` present (the positive half), the
  sentinel **absent from stderr, stdout, and every file under the whole results tree**.
- A probe **returning** a fact containing the credential (`https://x/?key=<token>`, substring not
  equality — H7d Part A's Major): exit **1**, `E-APPARATUS-FACT-CREDENTIAL`, sentinel absent from both
  streams and every artifact.
- **Positive control**: setting `c.credentials = []` in `freeze.py`'s `observe_round` handler makes the
  credential appear verbatim on stderr (`probe 'wbr_cprobe' raised RuntimeError: apparatus refused for
  token s3kr3t-…`). Reverted by editing back; `diff` against the pre-mutation copy identical, harness
  re-run green. So the redaction is doing the work, not the test.

### 6. The guard pin's whole life

Audited by history, not by reading. `git log -L` over each arm's line range in `tests/test_cli.py`
and `tests/test_hashes.py`:

| Arm | Commits touching it | Authorized? |
|---|---|---|
| A (run-dir root) | `152688f` create, `bf56ed3` fix round, **`6335c1d` task 3** | Yes — one entry added (`config.yaml`, alphabetical), nothing reordered |
| B (`environment/`) | same three | Yes — one entry added (`repo_root.txt`) |
| C (record key lists) | `152688f` only | Untouched |
| D (five figures) | `152688f` only | Untouched |
| E (`sweep.yaml` plan) | `152688f`, `bf56ed3` | Untouched by any task |
| F (embedded config) | `152688f`, `bf56ed3`, `6335c1d` — **but the task-3 hunk is the Fixture C block appended *after* arm F's end**, not an edit to arm F. Verified by reading `git show 6335c1d -- tests/test_cli.py` in full: three hunks, arm A +1 line, arm B +1 line, and the new fixture | Yes |
| G (`parameters_hash` agrees) | `152688f`, `bf56ed3`, **`986f10a` task 7** — one import name added and one new test appended; no existing assertion changed | Yes |

`ROW_LABELS`: created in task 8 (`ed615e4`), its **definition line** changed by task 9 (`8bb90c2`)
only; `11cdadd`, `bdaccaa`, `4afe0dc` touch *references*, not the constant. Authorized.

**Each arm still discriminates — verified by mutation**, not asserted:
- Swapping the two new writes for stray files in the run root and `environment/` fails **A, B and
  Fixture C** simultaneously (missing *and* stray, both arms, one mutation).
- Renaming `sweep.yaml`'s `is_baseline` key fails **E** alone.
- Adding a `provenance` key and nulling `units_hash` fails **C** alone.
- `"manager": "uv"` → `"uvx"` fails **D** alone.
- Reversing `ROW_LABELS`' first two entries fails the row-order pin **and both document-agreement
  tests** — and the row-order pin asserts hard-coded literals, so it does not test itself.
- **G** fails under the `covered_config` narrowing above.
Every mutation reverted by editing back; `cli.py`, `sweep.py`, `hashes.py`, `diff.py`, `freeze.py` each
diffed against a pre-mutation copy afterwards (**identical**), and the full suite re-run green at the
end.

### 7. CLAUDE.md § Invariants

- **Operation commands take paths and nothing else** — verified by running (item 1).
- **Three hashes split** — verified: `code_hash` untouched, `parameters_hash` digest-stable against
  `main`, `input_manifest` separate; `diff` prints the apparatus as a **row**, not a fourth hash, and
  `design_digest` is not printed at all.
- **`input_dir`/`output_dir` never inside the repo** — neither command executes and neither performs a
  containment check; Decision 15 refuses it **with grounds** (read), and nothing this branch adds
  creates a write path into the repo.
- **Core never inspects the body of user Python** — `freeze` imports `templates/*.py` (what `validate`
  already does) and calls the declared probe; no body is read.
- **Greenfield only** — no `adopt`, nothing near it.

### 8. The documents

- **Every new code has a § Errors row**: all eight `E-FREEZE-*` (reference.md:617-624), the one
  `E-DIFF-*` (625) and `W-FREEZE-LOCK-MOVED` (402) — ten rows for ten codes, checked against the grep
  of `src/`. Reused codes: `E-TEMPLATE-UNKNOWN` amended to name `freeze` (607, and *"Three surfaces"*
  is correct); `E-UPSTREAM-RECORD-*` rewritten to name `diff`'s operand (1072); `E-APPARATUS-CHANGED`
  gained `freeze` as a second surface (1097); `E-IO-FAILED` gained the `diff` operand path (3606);
  `E-TEMPLATE-COLLISION`/`-LOAD` need no edit (self-maintaining wording).
  **The two gaps are Majors 2 and 4.**
- **And the reverse direction — every shape a row *names* has an emit site.** Checked for the two rows
  most at risk, both written in task 12 for codes minted in earlier batches:
  `E-FREEZE-LEDGER-UNREADABLE`'s row names six shapes (not JSON, not an object, missing `phase`,
  missing `condition`, missing `facts`, wrong-type `facts`/`condition`) and `apparatus.py:572-613` has
  a raise for **every one**; `E-FREEZE-PLAN-MISSING`'s row names three (absent, unparseable, no
  `conditions` list) and `freeze.py:260/271/279` has three. No row describes a check that does not
  exist.
- § Package layout has rows for `diff.py` and `freeze.py` (4063-4064). § Exit codes' `1` row no longer
  claims `diff` — verified by grep across the four documents that the old clause survives nowhere.
- **Both `Status` cells flipped to `built`** and `NOT_BUILT_COMMANDS` holds neither key — verified by
  running: `len(NOT_BUILT_COMMANDS) == 10`.
- **The `Does` cell's "five rows" was fixed** — see Minor 2 for what is left of it. No other count
  phrase about `diff`'s rows survives: § Package layout's *"the five rows"* is correct, and
  *"a config side cannot supply four of its five rows"* is correct.
- **The shared worked example is untouched.** `git diff main...HEAD` over the four documents shows the
  *only* change to the worked figures is ASCII `...` → `…` in three fenced outputs — the design's own
  sweep item. `8e21`/`1a2b`/`3d8a`/`6b1f`, 0.581/0.607/0.412, 228/240, `cohort-pilot` all unchanged.
  `README.md` is unchanged apart from that. The apparatus fenced example gained its condition keys as
  Decision 2 requires, using `01_method=spearman` — which is the worked example's **own** condition
  label, already used elsewhere in `reference.md` (`conditions/01_method=spearman/…` on `main`), so
  that is consistent rather than invented.
- **Mechanical pass on the four documents: 0 problems** — duplicate anchors, local and cross-file
  anchor resolution (GitHub's slugger, including the `--` from a stripped `&` and retained `_`),
  missing linked files, table column counts, trailing whitespace, tabs, invisible unicode, all with
  fenced blocks skipped. **The sweep was proven able to fail**: injecting a dead anchor, a missing
  file, a 3-cell row under a 2-cell header, a trailing space, a tab and a duplicate heading into
  `reference.md` produced **6 problems**, one per class; reverted by copying the backup back, verified
  byte-identical and re-run to 0.
- `spec-defects.md`: **additions only** (verified — a single `-` line in the diff, and it is a rule).
  The three filings the plan forbade striking are all intact and OPEN — `parameters_hash`
  normalization (H6, line 170), `UpstreamLedger.record`'s `None` hash (H9, line 3311),
  `max_failed_fraction`'s truncation (unassigned, line 7363). The one closure is an **appended
  `AMENDED … CLOSED`** note on the `diff`-versus-gate divergence, whose remedy (one sentence in
  § The apparatus core can only observe) I confirmed landed at reference.md:3155. The
  `parameters`-edit filing the plan promised (H9) exists at line 7649.

### 9. The § Executability figures

- The four-row table is **repeated character for character** from the H8a entry — verified by
  extracting both tables programmatically and comparing: 6 lines each, `a == b` **True**. `8 of 8` ·
  `0` · `7` · `1`. **No fifth number** anywhere in the entry, and no "N configs now execute".
- **Date matches its commit**: `cad8940` is `2026-08-21 01:40:19 -0400`. It is `639d0f7`'s parent —
  the correct thing to measure against for a doc commit.
- **The ten not-built commands are exactly right** — verified by running:
  `sorted(NOT_BUILT_COMMANDS)` is `['demo','docs','draft','dry-run','list-templates','report',
  'reproduce','resume','study add','study new']`, set-equal to the entry's list. So item 10(a)'s
  worry does not land: the sentence is an enumeration that matches the constant, not an uncounted
  count phrase.
- **I re-measured two configs myself, with can-fail controls.** E1's and C1's `data.units` and
  `statistics` blocks, transplanted verbatim from the analysis onto a scaffolded `generic` config over
  a 240-row synthetic roster, through `validate_config` — the method every prior entry uses:

  | Config | errors | warnings |
  |---|---|---|
  | E1 | **0** | `W-DATA-CLUSTER-UNDECLARED` (a fixture artifact, as the 2026-08-16 entry already says) |
  | C1 | **0** | same |
  | E1 control (`holdout.frac: 0`) | 1 — `E-DATA-HOLDOUT-FRAC` | same |
  | C1 control (`resample.method: nonsense`) | 1 — `E-STATS-RESAMPLE-METHOD` | same |

  Both clean arms discriminate. And **verified by running**: `GenericTemplate().apparatus_probe` is
  `None` with `apparatus_facts == []`, so the entry's claim that `freeze` against any of the nine
  would report `E-FREEZE-NO-APPARATUS` before a probe ran is correct.

### 10. The three things flagged for a second look

**(a) The ten-command enumeration** — not a count-phrase defect. See above: set-equal to the
constant, verified by running.

**(b) The two additions taken under "if it fits naturally"** — both check out. The `reference.md`
sentence closing the diff-vs-gate ruling is at 3155, directly beside the fenced example, and the
filing's closure is an **appended amendment**, not a strike. Its grounds are stated in the entry
(task 12 was already editing that section for the ellipsis fix). Neither addition moves behaviour and
neither closes someone else's gap.

**(c) The restored `CLAUDE.md` clause is correct, and nothing else in that row moved.** This is worth
spelling out because the *reasoning* recorded for the overruling could have been wrong and was not.
The clause on `main` at `64a831f` reads *"`EXIT_EXTERNAL` **was** the same fault outside
`BaseTemplate` **until** H7d Part B task 8 gave it its reader"* — **past tense**, exactly as the
overruling quoted it, and consistent with the sentence naming `field_convention` as the sole remaining
example. So plan correction 4's diagnosis (*"already false", present tense, "read by nothing"*) was
itself false, the controller's overruling was right, and task 12's deletion was wrong. `e3e480e`
restores it as a **one-line change to that row and nothing else** — verified by reading the full
commit diff: the restored line is `main`'s line plus one appended justification clause (*"and that
clause is kept deliberately: it is the row's own evidence that it retires entries as readers land"*).
That is a restoration *with its reason*, which is what the commit says it is; not a byte-exact revert,
and correctly so.

### 11. Cross-batch interactions — where the last three slices' Majors lived

Probed specifically, all sound (verified by running unless noted):

- **Task 2's `assert phase in PHASES` versus tasks 1 and 6.** No literal phase string survives
  outside `apparatus.py`'s four constant definitions — grep over `src/` for `"run_start"`,
  `"pre_execution"`, `phase="`: zero hits elsewhere. All four core call sites
  (`cli.py:2467`, `runner.py:641`, `freeze.py:95`, `freeze.py:508`) pass constants. The assert cannot
  be reached by typo, and `replay_ledger` **skips** an unknown phase rather than refusing it, so this
  build can still replay a newer run's ledger.
- **Task 3's `config.yaml` versus task 8's `_form`.** The new artifact is a file not named `run.yaml`,
  so `diff <run_dir>/config.yaml <source config>` reads it as a **config** — and prints
  `parameters_hash  identical` with four `not comparable`. Useful and correct, not an accident.
- **A mid-run directory handed to `diff`.** Exit 1, `E-UPSTREAM-RECORD-MISSING`. No traceback, no
  half-rendered comparison.
- **Task 9's apparatus row versus task 10's `not comparable` rule** (plan correction 10): a config
  side against a run whose `apparatus` is `null` prints `not comparable`, not silence — Decision 5
  wins, as ruled.
- **Task 11's upstream block versus task 10's config side**: `_upstream_entries` returns `[]` for a
  non-run side, so no block prints and no `None` dereference is reachable.
- **Gate ordering in `_precheck`**: `replay_ledger` (i) validates every line before
  `_ledger_probe_names` (j) re-reads it unguarded, and an absent ledger short-circuits at (i) via
  `E-FREEZE-LEDGER-MISSING`, so (j)'s bare `json.loads` is unreachable with a malformed file. Read,
  and consistent with the docstring's own claim.
- **Fixture F3 was not downgraded.** `tests/test_freeze.py:962` is a genuine second process
  (`subprocess.Popen` running `main(['run', …])`, blocking inside a step, with a sentinel/release
  handshake and 20-second deadlines), asserting the `lock` is genuinely held and that `freeze` still
  exits 0 and appends two lines. Read. (It calls `command_freeze` directly rather than
  `main(["freeze", …])`; the `main` path is covered by many other tests, so this is a note, not a
  finding.)

---

## What I could not check

- **A torn ledger line under real concurrency.** `_ledger_probe_names` (`freeze.py:92-96`) re-reads
  `probes.jsonl` and `json.loads`es each line with no guard, in the window after `replay_ledger`
  validated it — and a live run may append in that window. I could not construct a partially-written
  append (small appends are effectively atomic on a local filesystem), so I am **naming this rather
  than claiming it**. The related exposure is a false `E-FREEZE-LEDGER-UNREADABLE` from
  `replay_ledger` itself, whose message says *"the file was edited or truncated by hand"* — a wrong
  remedy for the command's own concurrent use case. Not demonstrated.
- **Whether `resume` (H9) reads the two new artifacts compatibly.** The reader does not exist. This is
  the design's own named limit and I add nothing to it.
- **Whether a real project's `diff` output is legible at width.** A 12-condition sweep prints 12 lines
  per moved fact under Decision 2's no-collapse rule and no document shows that shape. The design says
  so about itself; I did not build one.
- **The design's own stale "seven `E-FREEZE-*`" count.** Correct on its date, and specs are not
  retro-edited, so I did not treat it as a finding — only its echo in shipped code (Minor 1).
- **Batches 6 and 7's own conduct.** I did not watch them and the ledger does not record them
  (Minor 7); I checked their *output* against the code instead.

## Recommendation

Close Majors 1–4, then merge.

1. **Major 1 is the only one that touches behaviour** and is the one to decide rather than patch: a
   guard at `diff`'s hash call raising `E-DIFF-CONFIG-UNREADABLE`, or an amendment to
   `spec-defects.md:4176` naming `parameters_hash` and `diff` so the gap is not left reading as
   `run`-only and H3's. Either way the four already-printed rows argue for the guard.
2. **Majors 2 and 4** are two emit-site amendments in `docs/reference.md` — one § Errors row, one
   § Warnings row — for codes the branch's own Decision 10 lists as reused.
3. **Major 3** is four words deleted from `apparatus.py`'s `PHASES` docstring, plus either a
   `spec-defects.md` entry or the same deletion in the design's and plan's *"filed"* claims.

The Minors are cheap and should ride along, particularly Minor 2 (the CLAUDE.md count phrase, since
that file is read first) and Minor 1 (a wrong count in shipped code).

**Tree is clean.**

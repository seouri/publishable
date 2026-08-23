# H9b batch 1+2 — tasks 1, 2, 3 and 4

**Written 2026-08-23** on branch `h9b-resume`, from `main` at `f2e545d`. Every figure below was
read off a run of the command it describes; nothing is carried from the plan or the design without
re-checking, and where the code disagreed with them the disagreement is named rather than smoothed.

## Task 4's normalization list — WRITTEN BEFORE THE COMPARISON WAS RUN

Recorded here first, and this section is timestamped by the commit that carries it. A normalization
decided after seeing a diff is a normalization chosen to hide it.

**Two sides.** A `main` worktree and the branch worktree, each with its own venv and its own
`uv pip install -e`, and a positive control asserting each side's `publishable.__file__` resolves
inside its own worktree — so a comparison that accidentally ran one build twice is caught rather
than reported as agreement.

**`run.yaml`, leaf by leaf, in order.** Normalized: any leaf whose own key is `at`, `started_at`,
`wall_seconds`, `run_id`, or `hostname`; `provenance.git.commit` (a fresh commit's SHA is
committer-timestamp-sensitive); and any string leaf containing either side's own base directory
(`config.data.input_dir`, `output_dir`, `provenance.git.repo_root`). **The three hashes are NOT
normalized**: the two projects are byte-identical apart from those paths, and `code_hash` covers
`src/**`+`templates/**` while `parameters_hash` and `input_manifest_hash` cover content, so all
three must be EQUAL across sides. A difference in any is a finding, not noise.

**The run-directory tree, path by path, by kind, size and sha256.** The expected difference, named
in advance: **`identity.json` exists on the branch side and not on `main`'s — one added file, and
nothing else added, removed or moved.** Every file whose bytes legitimately carry a path or a
timestamp is expected to differ in size/sha256 and is enumerated in advance: `config.yaml` and
`environment/repo_root.txt` and `manifest/input.json` (absolute paths), `run.yaml` and
`executions.jsonl` (timestamps and durations), `units.parquet` (a container whose bytes are not a
promise). Anything else differing is a finding.

**`sweep.yaml`** — compared as parsed documents, leaf by leaf, with no normalization at all: it
holds no path, no timestamp and no hash.

**`executions.jsonl`** — key by key per line, and the ordered `(step, condition, repeat, status)`
tuples. Values of `started_at`/`wall_seconds` normalized; every other value compared.

**stdout, stderr, exit code** — line by line, with each side's own absolute paths normalized.

**`dry-run`'s transcript, line by line.** Two expected differences, named in advance: the header
`and 7 fixed files in that directory:` becomes `and 8 …`, and one new line, `  identity.json`,
appears in the fixed-file list. Every other line must match after path normalization.

---

## Status

| Task | What landed | Commit |
|---|---|---|
| 1 | The guard pin: arms A and G built, arms B, C, D and E re-authorized, arms F and H cited | `811feee` |
| 2 | `IDENTITY_FILE`, `identity_document`, `read_identity`, `read_repo_root`, `config_path_for` | `ff942ef` |
| 3 | `run`/`draft` write `<run_dir>/identity.json` inside the lock; `_DRY_RUN_FIXED_FILES` gains it; arms B and D edited | `c7bbd64` |
| 4 | The normalization list (committed first), then the two-sided real-command comparison — findings below | `f70f63f`, this commit |

**Gates, on the final tree:** `ruff check` clean, `ruff format --check` clean (93 files), `mypy` clean
(52 files), `uv run pytest` **3053 passed, 1 skipped, 4 xfailed**. Baseline was 3019 / 1 / 2, so the
delta is **+34 passed and +2 xfailed** — the two `xfail`s are arm A's resume half and arm G's race;
the 34 are 3 live tests in batch 1, 28 in task 2 (`test_run_identity.py` went 8 → 36, most of them
parametrized arms), and 3 in task 3. No existing test's expectation moved except guard-pin arms B and
D, both authorized (below).

## Task 1 — every arm, its editor, and its mutation

Every count below is the number of tests that failed in a **FULL, UNFILTERED** `uv run pytest`, read
off that run's own summary line.

| Arm | Built or cited | Authorized editor | Mutation (production code) | Full-suite result |
|---|---|---|---|---|
| **A**, live half — `test_h9b_arm_a_the_straight_through_golden` | Built: the straight-through run's whole `run.yaml`, 185 normalized leaves, captured by running | **NONE** | `run_record.py`: `cond["is_baseline"] = not meta.get(...)` | **9 failed, 3013 passed** — this arm among them (also H9a arm A, two `test_acceptance` tests, four `test_report` tests, one `test_cli` H5b test) |
| **A**, fixture-state half — `test_h9b_arm_a_the_crash_fixture_is_really_crashed` | Built | **NONE** | `run_identity.RunLock.__enter__`: `"pid": os.getppid()` | **2 failed, 3020 passed** — this arm and arm G's live half |
| **A**, resume half — `test_h9b_arm_a_crash_and_resume_equals_straight_through` | Built, `xfail(strict=True)` naming task 9 | **NONE** | **Named blind in advance** — see below | — |
| **G**, live half — `test_h9b_arm_g_the_dead_holder_fixture` | Built | **NONE** | same `os.getppid()` mutation | **2 failed, 3020 passed** (same run) |
| **G**, race half — `test_h9b_arm_g_the_takeovers_mutual_exclusion` | Built, `xfail(strict=True)` naming task 14 | **NONE** | **Named blind in advance** | — |
| **B** — `test_h8b_arm_a_the_run_directorys_root` | Shipped, **re-authorized** | H9b's `identity.json` write-site task = **plan task 3** (see the discrepancy below) | edited by task 3; the mutation that proves it can fail is task 3's M6 | **4 failed, 3049 passed** under M6 |
| **C** — `test_h9a_arm_d_the_executions_jsonl_line_key_set` | Shipped, **re-authorized from NONE** | **H9b task 6**, by controller ruling in design Decision 5 | not this task's to move | — |
| **D** — the `and 7 fixed files` literal | Shipped, **re-authorized** | plan task 3 | task 3's M6 | **4 failed, 3049 passed**: arm D itself (`test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript`) plus the three `_h9a_fixture_u` arms, which are the *second*, set-to-set assertion |
| **E** — `("resume", "NOT BUILT")` | Shipped, **re-authorized** | **H9b task 15** | not this task's to move | — |
| **F** | **Cited, not re-captured**: `test_h9a_arm_a_a_completed_runs_whole_run_yaml_leaf_by_leaf` (a completed run's whole `run.yaml`) and `test_h9a_arm_b_runs_full_stdout_line_by_line` (`run`'s full stdout) — what Decision 14's behaviour-preservation claim is measured against | NONE | — | — |
| **H** | **Cited, not re-captured**: `test_h8b_arm_b_environments_contents` (`environment/`'s contents — `identity.json` is not under it), `test_h8a_arm_a_a_clean_run_top_level_shape_status_and_exit` and `test_h8a_arm_b_the_provenance_key_list_and_upstream_empty` (`run.yaml`'s and `provenance`'s key lists), `test_h8c_arm_a_the_records_field_level_shape` (the record's field-level shape), `test_h8b_arm_e_sweep_yamls_recorded_plan_shape` (`sweep.yaml`'s key list), H9a arms C and E (the four exit codes, the four early exits) | NONE | — | — |

Both reverts were performed by **editing back** and verified by **behaviour**: after reverting the
`is_baseline` mutation the tests it caught passed again in the *next* full run (the one carrying the
`os.getppid()` mutation, whose only failures were the two fixture-state arms), and after reverting
that one the suite returned to 3053 / 1 / 4. `diff` against a pre-mutation copy also showed both files
byte-identical. No `git checkout -- <file>` was used anywhere.

**A property-PRESERVING arm, per mutation.** `is_baseline`: writing `bool(meta.get("is_baseline",
False))` instead — same value, different expression, and every arm stays green, which is what
distinguishes "this line is pinned" from "this file is pinned". `os.getppid()`: writing
`int(os.getpid())`. M5 (position): writing the same statement one line earlier, above
`environment/repo_root.txt`'s — still inside the lock, so the probe pin stays green while the
design's stated order is what moved (which is why the report says which single line the write is,
rather than resting on the pin alone). M6: reordering the tuple's existing entries without adding or
removing one — `_dry_run_fixed_files` sorts, so arm D's count and the set comparison both hold.

### The two mutations named BLIND in advance, and what is owed instead

`xfail(strict=True)` absorbs every failure reason, so **"mutate production code and watch the arm
fail" is trivially satisfied for arms A-resume and G-race and therefore proves nothing about them.**
Named here rather than discovered later. What is owed in their place, and was built:

1. **The fixture-state halves** (`..._the_crash_fixture_is_really_crashed`,
   `..._the_dead_holder_fixture`), which are live, assert positive presences rather than absences, and
   both fail under a real production mutation (counts above). A crash fixture that silently never
   crashed — a subprocess that could not import `publishable`, a counter file at the wrong path — is
   exactly what would otherwise be read as *correctly failing until task 9*.
2. **A probe of the current answer, not a pin of it**: `publishable resume <crashed run dir>` through
   the real console script today prints ``  `publishable resume` is specified but not built in this
   version — see docs/reference.md § Resuming`` and **exits 2**. So both `xfail`s currently fail on
   the unbuilt diagnostic and not on something else. Deliberately NOT asserted in a test: that
   expectation is task 15's to move, and pinning it here would force an unauthorized edit.

### The five-process race probe is cited, not used as the pin

Design § 0's three protocol probes (rename-as-mutex falsified on trial 0 with four winners of four;
scan-then-claim falsified on trial 0 with two winners; token-first holding 60 trials × 5 processes with
zero violations, and producing two winners by trial 22 with the token deleted) are the **discovery
instrument**. Arm G is the pin, and it is deterministic: two threads, a `threading.Barrier` released
inside the liveness syscall between the verdict's evidence and the lock's replacement. **Stated
exactly rather than generously, in the arm's own docstring**: under the shipped protocol only one
thread ever reaches that syscall, so the barrier times out and is INERT; it bites under the mutation
that deletes the token. The barrier does not make the shipped path deterministic — it makes the
mutation's interleaving deterministic. The arm also asserts the hook fired at all, because a
monkeypatch aimed at a name the code no longer calls is silently inert.

### The two re-authorizations, stated as re-authorizations

- **Arm C is a NONE arm being re-aimed.** `test_h9a_arm_d_the_executions_jsonl_line_key_set` carried
  *SOLE AUTHORIZED EDITOR: NONE* at HEAD. It now reads *SOLE AUTHORIZED EDITOR: H9b task 6, by
  controller ruling recorded in the H9b design's Decision 5*. **The authority is the design, not this
  task**: § The guard pin's row says of this arm *"SOLE AUTHORIZED EDITOR: NONE at HEAD, and Decision
  5 re-authorizes it"*, and writes the post-edit set in advance, which this docstring now copies
  verbatim. **No assertion here was changed by this task** — the ledger line's key set is still the
  shipped eight, and task 6 is what makes it ten.
- **Arm B was aimed at a closed slice's task.** Its clause read *"task 3 is that task"*, meaning
  **H8b's** task 3, and its post-edit paragraph still prescribed the `'config.yaml'` append H8b had
  already applied. Both are replaced.

### FINDING — the arm B / arm D editor number is a stale parenthetical, and I did not stop on it

The design's § The guard pin gives arms B and D to *"the `identity.json` task only (**plan task
4**)"*, and the task 1 brief says to write *SOLE AUTHORIZED EDITOR: H9b task 4*. **Plan task 4 is the
real-command review, whose own brief says "Must not touch: anything."** Meanwhile **plan task 3 — the
`identity.json` write site — says in its own text "You are the SOLE AUTHORIZED EDITOR of guard-pin
arms B and D (task 1 re-aimed them at you)"** and prescribes the diff shape. Under the number, batch 2
is uncompletable: the only task authorized to move the two assertions may touch nothing.

What settles it as a slip rather than a ruling: **the two sibling parentheticals in the same table are
correct** — arm C's "(plan task 6)" is the ledger task and arm E's "(plan task 15)" is the dispatch
task. So the **descriptive** half governs, and the clauses I wrote name it descriptively *and* give
the plan number, with the discrepancy stated in the docstring itself so no later reader has to
re-derive it. This is unlike H9a task 2's red branch, which was a genuinely missing authority; here
three sibling facts in the same document falsify one number.

### FINDING — fixture B's prescribed name collision is unreachable, measured

Design § Fixtures as claims, fixture B, requires *"one recorded key deliberately colliding with [a
declared attribute's] name, so the attribute subtraction is exercised against the case that breaks a
by-name rule"*, and plan § Corrections 6 states the underlying fact from `artifacts.finalize`'s merge
loop. **Through `io.record` it cannot happen.** The first capture of arm A's fixture recorded a
`cohort` column beside `data.units.attributes: [cohort]` and produced **eight `failed` executions**,
every one carrying `E-STEP-KEY-COLLISION ContractError: 'cohort' collides with a declared unit
attribute of the same name: a recorded column may not shadow it`. Grepped afterwards, not before:
`artifacts.py` raises that code at six sites and `docs/reference.md` § The per-unit tables and
§ Validation both document the refusal. So correction 6's *reading* of the merge loop is right about
the loop and wrong about reachability from a step — the loop's collision branch is reachable only from
a path that is not `io.record`'s declared-attribute case. Arm A therefore carries the declared
attribute undisturbed, and **the task whose reader subtracts attribute columns (task 8) must not plan
its by-name-versus-structural mutation around a fixture it cannot build.**

## Task 2 — the artifact and its readers

`IDENTITY_FILE`, `identity_document` (five keys, one order, `input_manifest_hash` deliberately
absent), `read_identity` (`E-RESUME-NO-IDENTITY` for absent / unparseable / not an object / missing
any of the five), `read_repo_root` and `config_path_for` (`E-RESUME-NO-CONFIG`). All in
`run_identity.py`, beside the lock; `cli.py`, `provenance.py` and `freeze.py` untouched by this task.

**Mutations, full suite:**

| Mutation | Full-suite result | Caught by |
|---|---|---|
| Drop the containment check (`if False:`) | **2 failed, 3048 passed** | `test_a_recorded_path_escaping_the_repo_root_is_refused` (the positive control, `../../secret/config.yaml`) and `test_an_absolute_recorded_path_is_refused_even_inside_the_repo` |
| Accept a document missing `draft` (drop it from `_IDENTITY_KEYS`) | **1 failed, 3049 passed** | `test_a_document_missing_any_one_key_is_refused[draft]` |

A property-preserving arm for the first: spelling the containment test as
`candidate.relative_to(resolved_root)` inside a `try` — the other shipped spelling of the same rule —
leaves every test green.

### The containment guard I REUSED rather than wrote

`artifacts.StepIO._contained` is the rule: `candidate = (base / name).resolve()`, refuse when
`Path(name).is_absolute()` or `str(candidate)` does not start with `str(base.resolve()) + os.sep`.
`config_path_for` uses **that predicate, restated for a `ContractError` caller** — the same move
`report.py`'s study-member resolver already made, and its docstring says why restating beats calling:
`_contained` raises `ArtifactError` and is scoped to a step's directory layout, and this raises
`ContractError` · `E-RESUME-NO-CONFIG` against a repo root. **Copied where it sits, not only what it
calls**: the check runs at the moment the recorded value is turned into a path and before anything
opens it, which is where H8a put it for `reuse_from`. The docstring states in as many words that
**this is not a boundary** — a step can `open()` anything regardless — because the H8a entry's whole
point is that a guard's rule may be narrower than the gap it closes.

Both directions are pinned: three honouring arms (a root-level config, a nested one with forward
separators, a hyphenated component) and six refusals (`..` escape with the escaped file really
existing, an absolute path pointing *inside* the repo, a non-string/empty/`None` value, a contained
path naming nothing, a contained path naming a directory).

### A brief ambiguity resolved, and how

The brief gives `config_path_for(run_dir, repo_root, document)` **and** assigns it the
`repo_root.txt` refusals — but a function handed `repo_root` cannot be the thing that reads
`repo_root.txt`. Resolved by splitting the read into `read_repo_root(run_dir)`, which carries the three
`repo_root.txt` refusals under the same code, and keeping `config_path_for`'s prescribed arity for the
containment half. The reason is the repo's own: a caller re-entering a run needs that root for itself,
and a second read inside the resolver would be a **second answer** to a question already answered.

### `identity.json`'s round trip through a strict reader

`json.dumps` emits bare `NaN`/`Infinity` and `coerce_scalars` passes non-finite floats through (plan
correction 22), so *"serializable by invariant"* is not available as a ground and the round trip is
**performed**. Pinned twice, and both readers **can fail**, proven on a value they must reject:

- unit level (`test_the_document_round_trips_through_a_reader_that_can_fail`,
  `test_a_written_document_reads_back_key_for_key`): `json.loads(text, parse_constant=reject)` returns
  the document key for key and in order.
- end to end (`test_h9b_identity_json_records_the_runs_own_figures`): the same strict reader over the
  **file a real `run` wrote**.
- and again in task 4's comparison, against the console script's own output: the branch side's
  `identity.json` parses under the strict reader as
  `{"code_hash": "sha256:436cab24…", "parameters_hash": "sha256:fff9b0cb…", "uv_lock_hash": null,
  "config_path": "configs/cohort-pilot/config.yaml", "draft": false}`, with `code_hash`,
  `parameters_hash` and `uv_lock_hash` **equal to that run's own `run.yaml`** and `config_path`
  resolving to the config file the command was given.

## Task 3 — the write site

**The single line, named as the brief requires:** the write is one statement beginning
`(run_dir / IDENTITY_FILE).write_text(` at the top of the phase-6 block, placed **immediately after**
`(run_dir / "environment" / "repo_root.txt").write_text(f"{repo_root}\n")` and before `sweep.yaml`'s
`mode = …`. Task 9 can guard it without moving it.

**Nothing is computed a second time and no local was added.** `config_path`, `repo_root`, `ch`, `ph`
and `lock_hash` are already unpacked at the top of `_execute_prepared`, and `draft` is its parameter —
so **§ Corrections 19's 36-field unpack block is byte-identical**, shown by the commit's diff, which
touches only the import, one new module-level helper above `_execute_prepared`, the write itself, and
the fixed-file tuple with its own comment. `git_provenance` is unchanged and `provenance.py` is
untouched (`git diff src/publishable/provenance.py` is empty).

**The `relative_to` fallback branch: no test reaches it, and it is not unreachable.** `repo_root` is
`find_repo_root(config_path)`'s answer — a walk-up **from the config itself** — so a `Prepared` whose
`config_path` lies outside its own `repo_root` is not a state `_prepare_run` produces. I did not find
a fixture that reaches the branch and I did not write a comment claiming it cannot be reached; the
helper's docstring says it is a fallback rather than a promise, and says what happens if a directory
somehow carries an absolute path (`config_path_for` refuses it, `E-RESUME-NO-CONFIG`).

**The two arm edits, exactly:** arm B gains one list entry (`"identity.json"`, after
`"executions.jsonl"`, keeping the sort) and arm D's literal goes `7` → `8`. Nothing reordered,
nothing else in `tests/test_cli.py` edited. I read *"you may edit nothing else in `tests/test_cli.py`"*
as forbidding edits to other tests, not as forbidding the new tests the same brief's mutation clause
requires ("pin it by asserting the file exists at the moment the apparatus run-start probe is
called") — three new tests were appended, editing nothing.

**Mutations, full suite:**

| Mutation | Full-suite result | Caught by |
|---|---|---|
| Write `identity.json` **outside** the lock (the same statement moved below the `with` block, above `point_latest`) | **1 failed, 3052 passed** | `test_h9b_identity_json_exists_while_the_lock_is_held` only |
| Omit `"identity.json"` from `_DRY_RUN_FIXED_FILES` | **4 failed, 3049 passed** | **two different assertions, as the brief requires both be reported**: arm D's count literal (`test_h9a_dry_run_dispatches_end_to_end_and_prints_the_transcript`) and the set-to-set comparison against a real run's tree (`_h9a_fixture_u`'s three arms: `..._the_two_lists_match_a_real_runs_tree`, `..._the_conditional_fixed_files_uv_lock_and_allocation`, `..._the_conditional_fixed_file_apparatus_probes_jsonl`) |

**Checked in advance, and confirmed by that first mutation: arm B CANNOT see the write's position.**
It lists the root of a *completed* run directory, where the file is present either way — and under the
mutation arm B stayed green while only the new pin failed. So the position is pinned the way the brief
prescribes, through the apparatus run-start probe, which core calls inside the same `with RunLock`
block: the probe snapshots the run directory's own root and the test asserts `identity.json` **and**
`lock` are there while `run.yaml` is not. Positive presences, not absences.

## Task 4 — the two-sided real-command review

Two `git worktree`s, two venvs, `uv pip install -e` in each. **Positive control:**
`main-wt/.venv/bin/python -c "import publishable; print(publishable.__file__)"` prints
`…/t4/main-wt/src/publishable/__init__.py` and the branch side prints `…/t4/branch-wt/src/…` — two
builds, not one run twice. One config per side, identical apart from its own absolute paths, each
scaffolded and committed through the **real console script** (`publishable new`, `generate
experiment`, `dry-run`, `run`), everything outside this repository. Green tests are not the evidence;
this is.

| Comparison | Result |
|---|---|
| `run.yaml`, leaf by leaf, in order | 94 leaves each, **one difference**: `provenance.input_manifest_hash` — attributed and closed below |
| Run-directory tree, path by path, by kind | **`identity.json` on the branch side only.** No other path added, removed or moved |
| Shared paths' size + sha256 | Five differ, every one on the pre-declared list: `config.yaml`, `environment/repo_root.txt`, `manifest/input.json` (absolute paths / mtime), `run.yaml`, `executions.jsonl` (timestamps and durations). No sixth |
| `sweep.yaml` | **IDENTICAL**, leaf by leaf, with no normalization |
| `executions.jsonl` | 5 lines each; **key sets identical line for line**; the ordered `(step, condition, repeat, status, error)` tuples identical |
| `run` stdout / stderr / exit code | **IDENTICAL** after path normalization; exit `0` both sides |
| `dry-run` transcript, line by line | **Exactly the two differences named in advance**: `and 7 fixed files in that directory:` → `and 8 …`, and one new line `  identity.json` in the fixed-file list, in write order. Nothing else, on either stream; exit `0` both sides |

**The one `run.yaml` difference, attributed by measurement rather than by argument.** The manifest
records each input file's `mtime` alongside its size and sha256, and my fixture wrote the two sides'
`index.csv` at different moments — the two `manifest/input.json` documents differ in **`mtime` only**
(size 173 and sha256 `16ce84f9…` identical on both sides). Confirmed by re-running: `cp -p` main's
`index.csv` over the branch side's, re-run the branch project, and its `input_manifest_hash` is
`sha256:65d60091f90565b4c84d184667d28010f88f7618c8000e41597049f4f0cd341f` — **byte-equal to main's**.
So the branch changes no hash. (This also shows why Decision 1 is right to leave
`input_manifest_hash` out of `identity.json`: the figure is mtime-sensitive, and
`manifest/input.json` is the operand `resume` compares.)

**No unattributed difference remains**, so nothing is filed from this comparison.

## Counts and lists that had to move — the grep, and every hit attributed

Filtered the **file list**, never the output.

`grep -rn "iterdir()" tests/*.py` → 13 hits: `test_artifacts.py` ×2 (a step directory and `tmp_path`,
neither a run root), `test_acceptance.py` ×2 (`conditions/` and a condition's repeat dirs),
`test_cli.py` 835/853 and 1080/1085 (a `templates/` and a `src/` listing), 14863 (`results_dir`, one
level **up** from a run directory), 16419 (**guard-pin arm B — edited**), 16452 (`environment/`'s
contents, guard-pin H8b arm B: `identity.json` is not under `environment/`), plus the two docstring
mentions in arm B's own prose.

`grep -rn "rglob" tests/*.py` → 24 hits, none needing an edit: `units.parquet`/`measurements.parquet`/
`split.json` locators; `_h9a_snapshot` and the `dry-run` *creates nothing* before/after snapshots
(self-maintaining — one build, two moments); `_h9a_fixture_u`'s `real_files`/`real_dirs` partition
(**self-maintaining by construction, and the second assertion that catches M6**); `test_freeze.py`'s
`_snapshot` (before/after of one build); `test_study.py`'s `_snapshot` (a bundle, not a run
directory); `test_validate.py` ×2 (`src/**/*.py`).

`grep -rn "fixed file" tests/` → 4 hits: `_H9A_DRY_RUN_FIXED_HEADER`, one prose line inside
`_h9a_fixture_u`, **arm D's literal (edited, 7 → 8)**, and one unrelated `test_materialize.py` line
about a dunder-prefixed file.

`grep -rn "and 7 fixed\|and 8 fixed" <the four documents> <feasibility> tests/ src/` → 2 hits:
arm D's literal (mine) and **`docs/reference.md`'s worked `dry-run` transcript, which already reads
`and 8 fixed files` and lists eight names** (that example declares a lockfile, so its count is
`_DRY_RUN_FIXED_FILES` **plus** `environment/uv.lock`). **It must become `9` with `identity.json` in
the list** — filed below for the documents task; no `*.md` was touched here.

In `src/`: `_DRY_RUN_FIXED_FILES`'s own comment said *"The seven a run always writes"* and now says
*"The eight"*. That is the count phrase nearest the tuple, and the only one in `src/` — 
`grep -rn "seven" src/publishable/cli.py` returns nothing else about this tuple.

**No test parses `reference.md`'s `dry-run` transcript**, grepped rather than assumed: the three
`"would create"` hits in `tests/` are all assertions on the **command's** output
(`_h9a_parse_dry_run` and one literal), and the document-parsing tests read `## `/`| ` tables, not
that fenced block. This is also why the count in `reference.md` did not fail the suite when the code's
count moved.

### For the documents task (17/18) — not touched here, and each is a real edit

- `docs/reference.md` § Artifact layout's fenced tree, and the second `<run_dir>/` tree in
  § Steps and artifacts: **neither lists `identity.json`**. Note the second tree also omits
  `config.yaml` and `environment/repo_root.txt`, so it is behind H8b as well as behind this slice.
- `docs/reference.md`'s `dry-run` worked transcript: `and 8 fixed files` → `9`, plus the new list line.
- § The other files a run writes' lead sentence — *"`sweep.yaml`, `allocation.json`, `config.yaml` and
  `environment/repo_root.txt` are settled before the first execution and never touched again"* —
  `identity.json` belongs in that list, and design Decision 1 says so in as many words.
- § `config.yaml` and `environment/repo_root.txt`: *"Together the pair holds exactly the two facts a
  mid-run command cannot otherwise obtain and cannot compute"* is now **three artifacts, not a pair**,
  and the sentence *"`code_hash` at run start is not recoverable from a tree that has since moved"* is
  exactly what `identity.json` changes. Decision 1's grounds name this passage; it cannot be left as
  it stands.
- The table-of-contents line for § The other files a run writes names the files it covers.

## Claims about other tests, other rows or other code — what I grepped

Reported as greps rather than as a count, and **no claim of zero disagreements is made** (two
disagreements are filed above: the arm B/D editor number, and fixture B's unreachable collision).

- *"`identity.json` is a free name"* (plan correction 7) — re-grepped at HEAD before writing:
  `grep -rn "identity.json" src/ docs/ tests/` returned no hit naming the artifact. Every hit for
  the bare word `identit*` was prose about a roster's or a run's identity, or `run_identity`'s own
  module name; enumerated when I ran it, and none was this file.
- *"no arm can see the write's position"* — not asserted from reading: measured by mutation M5, where
  arm B stayed green.
- *"no existing assertion holds `reference.md`'s `dry-run` count"* — grepped (above), and
  corroborated by M6, where the doc's `8` was untouched while the code's list changed.
- *"`lock` holds two keys"* (plan correction 9) — confirmed on a real crashed directory:
  `{"host": "macbookair.lan", "pid": 68754}`. Arm G's live half therefore asserts a **subset**, not an
  equality, precisely so task 14's `started_at` addition does not force an edit to an arm whose editor
  is NONE.
- *"a crashed run leaves no `latest`"* (plan correction 10) — measured, with a wrinkle worth carrying:
  in a project that has ALSO completed a run, `latest` exists and points at the **completed** one. Arm
  A's fixture-state half asserts that (the pointer resolves to the straight-through run's name, not
  the crashed one) rather than asserting an absence, because an absence would also pass for a fixture
  whose first run never happened.

## Concerns for the controller

1. **The arm B / arm D editor number needs a ruling on the record**, even though batch 2 is complete:
   the design's § The guard pin still says "plan task 4" and a later reader (or the whole-branch gate)
   will hit the same contradiction. The design is a dated record and should be corrected by
   **appending**, not by editing the table.
2. **Task 8's mutation plan rests on a fixture that cannot be built** (fixture B's recorded/attribute
   name collision, refused by `E-STEP-KEY-COLLISION`). Its brief should say what separates the
   by-name and structural readings **without** a colliding recorded key, or say the mutation is blind
   and what replaces it.
3. **The documents list above is longer than "one file added"** — in particular § `config.yaml` and
   `environment/repo_root.txt`'s *"the pair … exactly the two facts"* sentence and the second
   `<run_dir>/` tree, which is behind H8b too. Worth naming in task 17's brief so it is not scoped to
   the artifact-layout tree alone.
